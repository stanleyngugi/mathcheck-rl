"""Durable local M5 execution; evaluation verdicts never enter policy updates."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
import json
import os
from pathlib import Path
import random
import time

from .grpo import LocalTrainingConfig
from .pilot_manifest import (PilotInputs, PilotRuntime, PilotTrainingPlan,
                             build_pilot_manifest, canonical_json_sha256)
from .specification_tasks import generate_specification_tasks


class PilotStopped(RuntimeError):
    pass


def validate_manifest(manifest, release_manifest, config: LocalTrainingConfig):
    """Rebuild all commitments, caps and analysis rules, rather than trust JSON."""
    plan = PilotTrainingPlan(**{key: manifest["training_plan"][key]
                              for key in PilotTrainingPlan.__dataclass_fields__})
    expected = build_pilot_manifest(PilotRuntime(**manifest["runtime"]),
                                   PilotInputs(**manifest["inputs"]), release_manifest,
                                   training_plan=plan)
    if manifest != expected:
        raise ValueError("manifest differs from the frozen protocol")
    runtime = manifest["runtime"]
    if runtime["provider"] != "local-transformers":
        raise ValueError("this driver only supports unbilled local Transformers execution")
    if runtime["currency_conversion_source"] != "local-unbilled-no-currency-conversion":
        raise ValueError("local execution must explicitly freeze zero provider spend")
    if (runtime["temperature"], runtime["top_p"], runtime["token_limit"]) != (
            config.temperature, config.top_p, config.max_new_tokens):
        raise ValueError("sampling configuration does not match preregistration")
    if plan.trainer_configuration_sha256 != canonical_json_sha256(asdict(config)):
        raise ValueError("training configuration digest changed")
    if (plan.learning_rate, plan.kl_coefficient) != (config.learning_rate, config.kl_coefficient):
        raise ValueError("training objective does not match preregistration")


def paired_analysis(before, after):
    if set(before) != set(after) or not before:
        raise ValueError("paired evaluation must contain the same nonempty task set")
    n = len(before)
    def rate(rows, status):
        return 100 * sum(row["status"] == status for row in rows.values()) / n
    report = {
        "task_count": n,
        "before_pass_percentage": rate(before, "checked_success"),
        "after_pass_percentage": rate(after, "checked_success"),
        "gain_percentage_points": rate(after, "checked_success") - rate(before, "checked_success"),
        "invalid_input_increase_percentage_points": rate(after, "invalid_input") - rate(before, "invalid_input"),
        "operational_error_percentage": 100 * sum(row["status"] == "operational_error"
                   for rows in (before, after) for row in rows.values()) / (2*n),
        "wrong_to_right": sum(before[key]["status"] != "checked_success" and
                              after[key]["status"] == "checked_success" for key in before),
        "right_to_wrong": sum(before[key]["status"] == "checked_success" and
                              after[key]["status"] != "checked_success" for key in before),
        "before_status_counts": dict(Counter(row["status"] for row in before.values())),
        "after_status_counts": dict(Counter(row["status"] for row in after.values())),
    }
    families = sorted({row["family"] for row in before.values()})
    if len(families) > 1:
        report["families"] = {family: paired_analysis(
            {key: row for key, row in before.items() if row["family"] == family},
            {key: row for key, row in after.items() if row["family"] == family}) for family in families}
    return report


class LocalPilot:
    """Coordinator injected with a policy and specification verifier for testing.

    Production callers must run native preflight before constructing the policy.
    Test doubles establish orchestration behavior, never mathematical evidence.
    Confirmatory baselines are withheld from updates and the primary report;
    process-local sealing does not provide independent-custodian blinding.
    """

    def __init__(self, manifest, release_manifest, config, policy, verify, output: Path,
                 *, clock=time.monotonic):
        validate_manifest(manifest, release_manifest, config)
        if policy.initial_checkpoint_digest != manifest["training_plan"]["initial_checkpoint_sha256"]:
            raise ValueError("initial checkpoint digest changed")
        self.manifest, self.config, self.policy, self.verify = manifest, config, policy, verify
        self.output, self.clock = output, clock
        self.calls = 0
        self.started = clock()
        self.tasks = {name: generate_specification_tasks(
            manifest["families"], row["per_family"], row["seed"])
            for name, row in manifest["splits"].items()}

    @staticmethod
    def _write(stream, row):
        stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())

    def _check_time(self):
        if self.clock() - self.started >= self.manifest["budgets"]["maximum_wall_clock_minutes"]*60:
            raise PilotStopped("wall_clock_budget_exhausted")

    def _rollout(self, stream, phase, task, count, seed):
        self._check_time()
        if self.calls + count > self.manifest["budgets"]["maximum_provider_calls"]:
            raise PilotStopped("call_budget_exhausted")
        first = self.calls
        self.calls += count  # Reserve every completion before generation; never retry.
        self._write(stream, {"record_type": "attempt_started", "phase": phase,
            "task_id": task.task_id, "completion_ids": list(range(first, self.calls)),
            "sampling_seed": seed, "specification_digest": task.specification_digest})
        self.policy.set_sampling_seed(seed)
        generation_started = self.clock()
        try:
            batch = self.policy.sample(task.prompt, count)
            if len(batch.texts) != count:
                raise ValueError("policy returned an unexpected number of completions")
        except Exception as exc:
            self._write(stream, {"record_type": "generation_error", "phase": phase,
                "task_id": task.task_id, "completion_ids": list(range(first, self.calls)),
                "error": type(exc).__name__ + ": " + str(exc)})
            if isinstance(exc, PilotStopped):
                raise
            raise PilotStopped("generation_failed") from exc
        generation_seconds = self.clock() - generation_started
        rows = []
        for index, text in enumerate(batch.texts):
            try:
                verdict = self.verify(text, task)
                if verdict.specification_digest != task.specification_digest:
                    raise ValueError("verdict does not bind the frozen specification")
                if verdict.status not in {"checked_success", "mathematical_rejection", "invalid_input", "operational_error"}:
                    raise ValueError("unknown checker status")
                if verdict.accepted != (verdict.status == "checked_success"):
                    raise ValueError("inconsistent checker acceptance")
                row = {"record_type": "trial", "phase": phase, "completion_id": first+index,
                    "task_id": task.task_id, "family": task.family, "response": text,
                    "status": verdict.status, "reward": float(verdict.accepted),
                    "verdict": asdict(verdict), "provider_spend_usd": 0,
                    "group_generation_seconds": generation_seconds,
                    "prompt_tokens": getattr(batch, "prompt_length", None),
                    "completion_tokens": int(batch.completion_mask[index].sum().item())
                       if getattr(batch, "completion_mask", None) is not None else None}
            except Exception as exc:
                row = {"record_type": "trial", "phase": phase, "completion_id": first+index,
                    "task_id": task.task_id, "family": task.family, "response": text,
                    "status": "operational_error", "reward": 0.,
                    "error": type(exc).__name__ + ": " + str(exc)}
                self._write(stream, row)
                if isinstance(exc, PilotStopped):
                    raise
                rows.append(row)
                continue
            self._write(stream, row)
            rows.append(row)
        if any(row["status"] == "operational_error" for row in rows):
            raise PilotStopped("checker_operational_failure")
        self._check_time()
        return batch, rows

    def _evaluate(self, stream, phase, tasks, seed_base):
        rows = {}
        for index, task in enumerate(tasks):
            _, trial = self._rollout(stream, phase, task, 1, seed_base + index)
            rows[task.task_id] = trial[0]
        return rows

    def run(self):
        self.output.mkdir(parents=True, exist_ok=False)
        with (self.output / "records.jsonl").open("x", encoding="utf-8") as stream:
            self._write(stream, {"record_type": "manifest", "manifest": self.manifest,
                "manifest_sha256": canonical_json_sha256(self.manifest),
                "initial_checkpoint_sha256": self.policy.initial_checkpoint_digest,
                "initial_state_sha256": getattr(self.policy, "initial_state_digest", None),
                "confirmatory_custody": "separate_0600_journal_update_interface_excludes_evaluation"})
            try:
                result = self._execute(stream)
            except Exception as exc:
                self._write(stream, {"record_type": "terminal", "status": "stopped",
                    "reason": str(exc), "completion_calls": self.calls, "provider_spend_usd": 0,
                    "elapsed_seconds": self.clock()-self.started})
                raise
            self._write(stream, {"record_type": "terminal", **result,
                "completion_calls": self.calls, "provider_spend_usd": 0,
                "elapsed_seconds": self.clock()-self.started})
        return result

    def _execute(self, stream):
        pre = self._evaluate(stream, "primary_pre", self.tasks["primary_evaluation"], self.config.seed+1000)
        # Separate permission-restricted journal: do not expose baseline scores
        # in the training journal or any policy update input.
        sealed = self.output / "confirmatory-baseline.jsonl"
        fd = os.open(sealed, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as confirm_stream:
            self._evaluate(confirm_stream, "confirmatory_pre", self.tasks["confirmatory"], self.config.seed+2000)
        rng = random.Random(self.config.seed)
        buckets = {family: [t for t in self.tasks["training"] if t.family == family]
                   for family in self.manifest["families"]}
        for bucket in buckets.values():
            rng.shuffle(bucket)
        order = [bucket[index] for index in range(10) for bucket in buckets.values()]
        for index, task in enumerate(order):
            batch, rows = self._rollout(stream, "training", task, 3, self.config.seed+3000+index)
            self._check_time()
            update = self.policy.update(batch, [row["reward"] for row in rows])
            self._write(stream, {"record_type": "update", "task_id": task.task_id, **update})
        self._check_time()
        checkpoint = self.policy.save(self.output / "final-checkpoint")
        self._write(stream, {"record_type": "checkpoint", **checkpoint})
        if not 0 < checkpoint["optimizer_steps"] <= 40 or not checkpoint["policy_changed"]:
            raise PilotStopped("no_policy_update_no_learning_comparison")
        post = self._evaluate(stream, "primary_post", self.tasks["primary_evaluation"], self.config.seed+1000)
        primary = paired_analysis(pre, post)
        rules = self.manifest["analysis"]
        passed = (primary["gain_percentage_points"] >= rules["primary_minimum_gain_percentage_points"]
            and primary["invalid_input_increase_percentage_points"] <= rules["maximum_invalid_input_increase_percentage_points"]
            and primary["operational_error_percentage"] <= rules["maximum_operational_error_percentage"])
        report = {"primary": primary, "primary_gate_passed": passed,
                  "final_checkpoint": checkpoint}
        with (self.output / "primary-analysis.json").open("x", encoding="utf-8") as analysis:
            json.dump(report, analysis, sort_keys=True, indent=2, allow_nan=False)
            analysis.write("\n"); analysis.flush(); os.fsync(analysis.fileno())
        # Durable commitment precedes opening confirmatory baseline scores.
        self._write(stream, {"record_type": "primary_analysis_final",
            "analysis_sha256": canonical_json_sha256(report), "primary_gate_passed": passed})
        if not passed:
            return {"status": "primary_gate_failed", "primary": primary}
        baseline = {row["task_id"]: row for row in
                    (json.loads(line) for line in sealed.read_text(encoding="utf-8").splitlines())
                    if row["record_type"] == "trial"}
        after = self._evaluate(stream, "confirmatory_post", self.tasks["confirmatory"], self.config.seed+2000)
        confirmatory = paired_analysis(baseline, after)
        return {"status": "complete", "primary": primary, "confirmatory": confirmatory,
                "confirmatory_gain_positive": confirmatory["gain_percentage_points"] > 0}
