"""Fixture-only orchestration checks: no native evidence or learning claims."""
from dataclasses import asdict
import json
from types import SimpleNamespace

import pytest

from native_verify.grpo import LocalTrainingConfig
from native_verify.local_pilot import LocalPilot, PilotStopped
from native_verify.pilot_manifest import (PilotInputs, PilotRuntime, PilotTrainingPlan,
                                         build_pilot_manifest, canonical_json_sha256)
from native_verify.types import Verdict


def inputs():
    config = LocalTrainingConfig()
    release = {"schema_version": 1, "lean_version": "4.23.0", "lean_binary_sha256": "a"*64,
               "wheels": {f"fixture-{i}.whl": "b"*64 for i in range(4)}}
    runtime = PilotRuntime("local-transformers", "fixture@revision", "fixture-runtime", 1., 1., 256,
                           "local-unbilled-no-currency-conversion")
    plan = PilotTrainingPlan("GRPO", 3, 1, 40, 1e-5, .01, "c"*64,
                             canonical_json_sha256(asdict(config)), "d"*40)
    frozen = PilotInputs("e"*40, "f"*40, canonical_json_sha256(release), "fixture-only-attestation")
    return build_pilot_manifest(runtime, frozen, release, training_plan=plan), release, config


class FixturePolicy:
    initial_checkpoint_digest = "c"*64
    def __init__(self, *, degenerate=False, gains=True):
        self.groups = []; self.updated = False; self.degenerate = degenerate; self.gains = gains
    def set_sampling_seed(self, seed):
        self.seed = seed
    def sample(self, prompt, count):
        if count == 3:
            return SimpleNamespace(texts=["wrong"]*3 if self.degenerate else ["right", "wrong", "wrong"], prompt=prompt)
        return SimpleNamespace(texts=["right" if self.updated and self.gains else "wrong"], prompt=prompt)
    def update(self, batch, rewards):
        assert rewards == ([0., 0., 0.] if self.degenerate else [1., 0., 0.])
        self.groups.append(batch.prompt)
        self.updated = not self.degenerate
        return {"optimizer_step": self.updated}
    def save(self, directory):
        directory.mkdir()
        return {"checkpoint_sha256": "a"*64, "state_sha256": "b"*64,
                "optimizer_steps": 0 if self.degenerate else len(self.groups),
                "policy_changed": self.updated}


def fixture_verify(text, task):
    passed = text == "right"
    return Verdict(passed, "verified", None, status="checked_success" if passed else "mathematical_rejection",
                   specification_digest=task.specification_digest)


def pilot(tmp_path, policy=None, verify=fixture_verify, **kwargs):
    manifest, release, config = inputs()
    return LocalPilot(manifest, release, config, policy or FixturePolicy(), verify, tmp_path/"run", **kwargs)


def test_paired_flow_uses_280_calls_and_only_training_for_updates(tmp_path):
    runner = pilot(tmp_path)
    result = runner.run()
    assert runner.calls == 280
    assert result["status"] == "complete" and result["confirmatory_gain_positive"]
    assert result["primary"]["wrong_to_right"] == 40
    assert len(set(runner.policy.groups)) == 40
    assert set(runner.policy.groups) == {task.prompt for task in runner.tasks["training"]}
    records = [json.loads(line) for line in (tmp_path/"run/records.jsonl").read_text().splitlines()]
    assert not any(row.get("phase") == "confirmatory_pre" for row in records)
    finalized = next(i for i, row in enumerate(records) if row["record_type"] == "primary_analysis_final")
    confirm = next(i for i, row in enumerate(records) if row.get("phase") == "confirmatory_post")
    assert finalized < confirm
    assert (tmp_path/"run/confirmatory-baseline.jsonl").stat().st_mode & 0o777 == 0o600
    assert len([row for row in records if row["record_type"] == "trial"]) == 240
    assert runner.manifest["training_plan"]["maximum_optimizer_steps"] == 40
    with pytest.raises(FileExistsError):
        pilot(tmp_path).run()


def test_primary_failure_does_not_open_or_sample_final_confirmation(tmp_path):
    runner = pilot(tmp_path, FixturePolicy(gains=False))
    result = runner.run()
    assert runner.calls == 240 and result["status"] == "primary_gate_failed"
    assert not any(json.loads(line).get("phase") == "confirmatory_post"
                   for line in (tmp_path/"run/records.jsonl").read_text().splitlines())


def test_degenerate_training_stops_without_learning_comparison(tmp_path):
    runner = pilot(tmp_path, FixturePolicy(degenerate=True))
    with pytest.raises(PilotStopped, match="no_policy_update"):
        runner.run()
    assert runner.calls == 200
    assert not any(json.loads(line).get("phase") == "primary_post"
                   for line in (tmp_path/"run/records.jsonl").read_text().splitlines())


def test_operational_error_is_recorded_and_aborts_before_update(tmp_path):
    def broken(text, task):
        return Verdict(False, "internal", "broken", status="operational_error",
                       specification_digest=task.specification_digest)
    runner = pilot(tmp_path, verify=broken)
    with pytest.raises(PilotStopped, match="checker_operational_failure"):
        runner.run()
    assert runner.calls == 1 and not runner.policy.groups
    rows = [json.loads(line) for line in (tmp_path/"run/records.jsonl").read_text().splitlines()]
    assert rows[-2]["reward"] == 0 and rows[-1]["status"] == "stopped"


def test_generation_failure_counts_attempt_and_is_not_retried(tmp_path):
    class Broken(FixturePolicy):
        def sample(self, prompt, count):
            raise RuntimeError("fixture generation error")
    runner = pilot(tmp_path, Broken())
    with pytest.raises(PilotStopped, match="generation_failed"):
        runner.run()
    assert runner.calls == 1
    assert "generation_error" in (tmp_path/"run/records.jsonl").read_text()


def test_elapsed_budget_stops_before_dispatch(tmp_path):
    times = iter([0, 3600, 3600])
    runner = pilot(tmp_path, clock=lambda: next(times))
    with pytest.raises(PilotStopped, match="wall_clock_budget"):
        runner.run()
    assert runner.calls == 0


def test_changed_manifest_cannot_relax_caps_or_thresholds(tmp_path):
    manifest, release, config = inputs()
    manifest["budgets"]["maximum_provider_calls"] = 1000
    with pytest.raises(ValueError, match="frozen protocol"):
        LocalPilot(manifest, release, config, FixturePolicy(), fixture_verify, tmp_path/"run")


def test_mismatched_verdict_binding_aborts(tmp_path):
    def swapped(text, task):
        return Verdict(True, "verified", None, status="checked_success", specification_digest="0"*64)
    with pytest.raises(PilotStopped, match="checker_operational_failure"):
        pilot(tmp_path, verify=swapped).run()
