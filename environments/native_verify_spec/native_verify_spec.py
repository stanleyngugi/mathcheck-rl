"""Answer-key-free bounded specification/certificate RL environment."""
import asyncio
import hashlib
import json

import verifiers as vf
from datasets import Dataset

from native_verify.async_cache import AsyncSingleFlight
from native_verify.specification_tasks import (
    SpecificationTask,
    generate_disjoint_specification_splits,
    generate_specification_tasks,
    specification_from_dict,
    specification_to_dict,
    verify_specification_submission,
)

SYSTEM_PROMPT = (
    "Solve the bounded mathematical task. Submit only the requested fenced JSON "
    "candidate or complete certificate. The environment owns and freezes the "
    "specification; do not emit a replacement specification or a Lean proof."
)

STAGE_RANK = {
    "parse": 0.0,
    "internal": 0.0,
    "timeout": 0.0,
    "specification_check": 1.0,
    "verified": 2.0,
}

_V1_VERDICTS = AsyncSingleFlight(max_completed=2048)


def _build_split(tasks) -> Dataset:
    rows = []
    for task in tasks:
        rows.append({
            "prompt": [{"role": "user", "content": task.prompt}],
            # The framework calls this column answer, but it contains only the
            # frozen checker specification and never an expected candidate.
            "answer": json.dumps({"specification": specification_to_dict(task.specification)}),
            "info": json.dumps({
                "task_id": task.task_id,
                "family": task.family,
                "difficulty": task.difficulty,
                "scope": "encoded_specification_only",
                "specification_digest": task.specification_digest,
                "contains_expected_answer": False,
            }),
        })
    return Dataset.from_list(rows)


def _completion_text(completion) -> str:
    if not completion:
        return ""
    last = completion[-1]
    return (last.get("content") or "") if isinstance(last, dict) else str(last)


async def _get_verdict(completion, answer, state):
    if "nv_spec_verdict" in state:
        return state["nv_spec_verdict"]
    if "nv_spec_verdict_task" in state:
        return await asyncio.shield(state["nv_spec_verdict_task"])
    payload = json.loads(answer)
    specification = specification_from_dict(payload["specification"])
    task = SpecificationTask(
        task_id="framework-row",
        family=specification.kind,
        difficulty="bounded",
        prompt="",
        specification=specification,
    )
    response_text = _completion_text(completion)
    running = asyncio.create_task(asyncio.to_thread(
        verify_specification_submission, response_text, task,
    ))
    state["nv_spec_verdict_task"] = running
    try:
        verdict = await asyncio.shield(running)
    finally:
        state.pop("nv_spec_verdict_task", None)
    state["nv_spec_verdict"] = verdict
    return verdict


async def specification_pass(completion, answer, state) -> float:
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
    num_per_family: int = 4,
    seed: int = 0,
    eval_num_per_family: int = 2,
    eval_seed: int = 1000,
) -> vf.Environment:
    family_list = None if families == "all" else [item.strip() for item in families.split(",")]
    training, evaluation = generate_disjoint_specification_splits(
        families=family_list,
        train_per_family=num_per_family,
        eval_per_family=eval_num_per_family,
        train_seed=seed,
        eval_seed=eval_seed,
    )
    rubric = vf.Rubric(funcs=[specification_pass], weights=[1.0])
    rubric.add_metric(stage_rank)
    rubric.add_metric(verify_seconds)
    return vf.SingleTurnEnv(
        dataset=_build_split(training),
        eval_dataset=_build_split(evaluation),
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

    class NativeSpecificationTaskData(TaskData):
        specification: dict

    class NativeSpecificationTaskConfig(TaskConfig):
        lean_bin: str | None = None
        verify_timeout: float = 120.0

    class NativeSpecificationTask(Task[NativeSpecificationTaskData, State, NativeSpecificationTaskConfig]):
        NEEDS_CONTAINER = False

        async def _run(self, trace: Trace):
            specification = specification_from_dict(self.data.specification)
            task = SpecificationTask(
                task_id=self.data.name,
                family=specification.kind,
                difficulty="bounded",
                prompt="",
                specification=specification,
            )
            payload = json.dumps({
                "response": trace.last_reply,
                "specification": self.data.specification,
                "lean_bin": self.config.lean_bin,
                "timeout": self.config.verify_timeout,
            }, sort_keys=True, separators=(",", ":"))
            key = hashlib.sha256(payload.encode()).hexdigest()

            async def run_once():
                return await asyncio.to_thread(
                    verify_specification_submission,
                    trace.last_reply,
                    task,
                    lean_bin=self.config.lean_bin,
                    timeout_seconds=self.config.verify_timeout,
                )
            return await _V1_VERDICTS.get(key, run_once)

        @reward(weight=1.0)
        async def nv_specification_pass(self, trace: Trace, runtime: Runtime) -> float:
            verdict = await self._run(trace)
            trace.info["nv_status"] = verdict.status
            trace.info["nv_stage"] = verdict.stage
            trace.info["nv_reason"] = verdict.reason
            trace.info["nv_specification_digest"] = verdict.specification_digest
            return 1.0 if verdict.accepted else 0.0

        @reward(weight=0.0)
        async def nv_stage_rank(self, trace: Trace, runtime: Runtime) -> float:
            return float(STAGE_RANK.get((await self._run(trace)).stage, 0.0))

    class NativeSpecificationTasksetConfig(TasksetConfig):
        families: str = "all"
        num_per_family: int = 4
        seed: int = 0
        task: NativeSpecificationTaskConfig = NativeSpecificationTaskConfig()

    class NativeSpecificationTaskset(Taskset[NativeSpecificationTask, NativeSpecificationTasksetConfig]):
        def load(self):
            family_list = (
                None if self.config.families == "all"
                else [item.strip() for item in self.config.families.split(",")]
            )
            tasks = generate_specification_tasks(
                families=family_list,
                per_family=self.config.num_per_family,
                seed=self.config.seed,
            )
            for index, generated in enumerate(tasks):
                yield NativeSpecificationTask(
                    NativeSpecificationTaskData(
                        idx=index,
                        name=generated.task_id,
                        prompt=generated.prompt,
                        specification=specification_to_dict(generated.specification),
                        resources=TaskResources(cpu=2, memory=2),
                    ),
                    self.config.task,
                )

    __all__ = [
        "NativeSpecificationTask",
        "NativeSpecificationTaskConfig",
        "NativeSpecificationTaskset",
        "NativeSpecificationTasksetConfig",
        "load_environment",
    ]
except ImportError:
    # v0 remains usable when an installed verifiers release has no v1 surface.
    __all__ = ["load_environment"]
