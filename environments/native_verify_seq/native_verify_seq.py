import asyncio
import hashlib
import json

import verifiers as vf
from datasets import Dataset

from native_verify import verify
from native_verify.canonical import canonicalize_unicode
from native_verify.extract import extract_artifact
from native_verify.tasks import FAMILIES, generate_tasks
from native_verify.tasks import generate_disjoint_task_splits
from native_verify.async_cache import AsyncSingleFlight

SYSTEM_PROMPT = (
    "You are an expert Lean 4 programmer. You will receive a sequence problem. "
    "Respond with exactly one ```lean code block containing the definition "
    "`def f (n : Nat) : Nat` computing the sequence, plus optional helper "
    "definitions. Constraints: pure computational definitions only. No imports, "
    "no attributes (@[...]), no theorems, no `sorry`, no `partial`, no `unsafe`. "
    "Use structural recursion or explicit fuel loops for recursion. "
    "ASCII only: write `->` for function arrows, never the Unicode arrow character. "
    "Define f either as `def f (n : Nat) : Nat := ...` or as `def f : Nat -> Nat` "
    "with match patterns. The reward contract is finite observation agreement on "
    "the exact checked range stated in each prompt; it is not a universal theorem."
)

STAGE_RANK = {
    "extract": 0.0,
    "sanitize": 0.0,
    "compile": 1.0,
    "train_check": 2.0,
    "holdout_check": 3.0,
    "timeout": 0.0,
    "internal": 0.0,
    "verified": 4.0,
}


class _ExtractFailure:
    def __init__(self, reason: str):
        self.accepted = False
        self.stage = "extract"
        self.reason = reason
        self.duration_ms = 0
        self.status = "invalid_input"


_V1_VERDICTS = AsyncSingleFlight(max_completed=2048)


def _build_split(tasks) -> Dataset:
    rows = []
    for task in tasks:
        rows.append(
            {
                "prompt": [{"role": "user", "content": task.prompt}],
                "answer": json.dumps(
                    {
                        "train": task.train_values,
                        "holdout": task.holdout_values,
                    }
                ),
                "info": json.dumps(
                    {
                        "task_id": task.task_id,
                        "family": task.family,
                        "difficulty": task.difficulty,
                        "scope": "finite_observation",
                        "specification_digest": task.metadata["specification_digest"],
                    }
                ),
            }
        )
    return Dataset.from_list(rows)


async def _get_verdict(completion, answer, state):
    if "nv_verdict" in state:
        return state["nv_verdict"]
    if "nv_verdict_task" in state:
        return await asyncio.shield(state["nv_verdict_task"])
    response_text = ""
    if completion:
        last = completion[-1]
        response_text = last.get("content") or "" if isinstance(last, dict) else str(last)
    artifact = extract_artifact(response_text)
    async def run_once():
        if artifact is None:
            return _ExtractFailure("no_lean_fence")
        if len(artifact) > 10000:
            return _ExtractFailure("artifact_too_large")
        case_data = json.loads(answer)
        return await asyncio.to_thread(
            verify, canonicalize_unicode(artifact), case_data["train"],
            case_data["holdout"], timeout_seconds=90.0,
        )
    task = asyncio.create_task(run_once())
    state["nv_verdict_task"] = task
    try:
        verdict = await asyncio.shield(task)
    finally:
        state.pop("nv_verdict_task", None)
    state["nv_verdict"] = verdict
    return verdict


async def lean_pass(completion, answer, state) -> float:
    verdict = await _get_verdict(completion, answer, state)
    return 1.0 if verdict.accepted else 0.0


async def stage_rank(completion, answer, state) -> float:
    verdict = await _get_verdict(completion, answer, state)
    return STAGE_RANK.get(verdict.stage, 0.0)


async def verify_seconds(completion, answer, state) -> float:
    verdict = await _get_verdict(completion, answer, state)
    return verdict.duration_ms / 1000.0


def load_environment(
    families: str = "all",
    num_per_family: int = 8,
    seed: int = 0,
    eval_num_per_family: int = 2,
    eval_seed: int = 1000,
) -> vf.Environment:
    family_list = None if families == "all" else [f.strip() for f in families.split(",")]
    unknown = set(family_list or []) - set(FAMILIES)
    if unknown:
        raise ValueError(f"unknown families: {sorted(unknown)}")

    training, evaluation = generate_disjoint_task_splits(
        family_list,
        train_per_family=num_per_family,
        eval_per_family=eval_num_per_family,
        train_seed=seed,
        eval_seed=eval_seed,
    )
    dataset = _build_split(training)
    eval_dataset = _build_split(evaluation)

    rubric = vf.Rubric(funcs=[lean_pass], weights=[1.0])
    rubric.add_metric(stage_rank)
    rubric.add_metric(verify_seconds)

    return vf.SingleTurnEnv(
        dataset=dataset,
        eval_dataset=eval_dataset,
        system_prompt=SYSTEM_PROMPT,
        rubric=rubric,
    )


try:
    from verifiers.v1.configs.task import TaskConfig
    from verifiers.v1.configs.taskset import TasksetConfig
    from verifiers.v1.runtimes import Runtime
    from verifiers.v1.state import State
    from verifiers.v1.task import Task, TaskData, TaskResources
    from verifiers.v1.taskset import Taskset
    from verifiers.v1.trace import Trace
    from verifiers.v1.utils.decorators import reward

    class NativeVerifyTaskData(TaskData):
        train_values: list[int]
        holdout_values: list[int]

    class NativeVerifyTaskConfig(TaskConfig):
        lean_bin: str | None = None
        verify_timeout: float = 90.0

    class NativeVerifyTask(Task[NativeVerifyTaskData, State, NativeVerifyTaskConfig]):
        NEEDS_CONTAINER = False

        async def _run(self, trace: Trace):
            artifact = extract_artifact(trace.last_reply)
            if artifact is None:
                return _ExtractFailure("no_lean_fence")
            if len(artifact) > 10000:
                return _ExtractFailure("artifact_too_large")
            canonical = canonicalize_unicode(artifact)
            payload = json.dumps({
                "artifact": canonical,
                "train": self.data.train_values,
                "holdout": self.data.holdout_values,
                "lean_bin": self.config.lean_bin,
                "timeout": self.config.verify_timeout,
            }, sort_keys=True, separators=(",", ":"))
            key = hashlib.sha256(payload.encode()).hexdigest()

            async def run_once():
                return await asyncio.to_thread(
                    verify, canonical, self.data.train_values, self.data.holdout_values,
                    lean_bin=self.config.lean_bin,
                    timeout_seconds=self.config.verify_timeout,
                )

            return await _V1_VERDICTS.get(key, run_once)

        @reward(weight=1.0)
        async def nv_lean_pass(self, trace: Trace, runtime: Runtime) -> float:
            verdict = await self._run(trace)
            trace.info["nv_stage"] = verdict.stage
            trace.info["nv_reason"] = verdict.reason
            trace.info["nv_status"] = verdict.status
            return 1.0 if verdict.accepted else 0.0

        @reward(weight=0.0)
        async def nv_stage_rank(self, trace: Trace, runtime: Runtime) -> float:
            verdict = await self._run(trace)
            return float(STAGE_RANK.get(verdict.stage, 0.0))

    class NativeVerifyTasksetConfig(TasksetConfig):
        families: str = "all"
        num_per_family: int = 8
        seed: int = 0
        task: NativeVerifyTaskConfig = NativeVerifyTaskConfig()

    class NativeVerifyTaskset(Taskset[NativeVerifyTask, NativeVerifyTasksetConfig]):
        def load(self):
            family_list = (
                None
                if self.config.families == "all"
                else [f.strip() for f in self.config.families.split(",")]
            )
            tasks = generate_tasks(
                families=family_list,
                per_family=self.config.num_per_family,
                seed=self.config.seed,
            )
            for index, generated in enumerate(tasks):
                yield NativeVerifyTask(
                    NativeVerifyTaskData(
                        idx=index,
                        name=generated.task_id,
                        prompt=generated.prompt,
                        train_values=generated.train_values,
                        holdout_values=generated.holdout_values,
                        resources=TaskResources(cpu=2, memory=2),
                    ),
                    self.config.task,
                )

    __all__ = [
        "NativeVerifyTask",
        "NativeVerifyTaskConfig",
        "NativeVerifyTaskset",
        "NativeVerifyTasksetConfig",
        "load_environment",
    ]
except ImportError as exc:
    V1_IMPORT_ERROR = str(exc)
    __all__ = ["load_environment"]
