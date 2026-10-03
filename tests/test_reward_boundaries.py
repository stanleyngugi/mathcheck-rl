import asyncio
import json
from types import SimpleNamespace

import pytest

import mathcheck_rl
import native_verify_seq
from lean_kernel_verifier.specification import ProblemSpec
from native_verify.async_cache import AsyncSingleFlight
from native_verify.specification_tasks import SpecificationTask, verify_specification_submission
from native_verify.types import Verdict


def test_deep_json_is_invalid_input_without_starting_a_checker():
    task = SpecificationTask("nested", "evaluate", "bounded", "", ProblemSpec("evaluate", "3"))
    response = '```json\n{"answer":' + '[' * 2000 + '3' + ']' * 2000 + '}\n```'
    verdict = verify_specification_submission(response, task)
    assert verdict.status == "invalid_input"
    assert verdict.checker_invocations == 0


def test_json_decoder_recursion_limit_is_a_structured_rejection(monkeypatch):
    # Python versions differ in decoder depth limits. Exercise the error path
    # directly as well as the real nested input above.
    def too_deep(*args, **kwargs):
        raise RecursionError("decoder depth exceeded")

    monkeypatch.setattr(json, "loads", too_deep)
    task = SpecificationTask("nested", "evaluate", "bounded", "", ProblemSpec("evaluate", "3"))
    verdict = verify_specification_submission('```json\n{"answer":3}\n```', task)
    assert verdict.status == "invalid_input"
    assert verdict.checker_invocations == 0
    assert "nested too deeply" in verdict.reason


def test_verdict_diagnostics_cannot_mutate_shared_cached_result():
    lines = ["first"]
    verdict = Verdict(False, "internal", None, diagnostics=lines)
    lines.append("second")
    assert verdict.diagnostics == ("first",)


@pytest.mark.parametrize("returncode", [124, 125, -9, 2])
def test_older_engine_wrapper_exit_is_still_operational_in_reward(monkeypatch, returncode):
    import native_verify.specification_tasks as submission
    from lean_kernel_verifier.runner.checker_runner import CheckerRunResult

    spec = ProblemSpec("evaluate", "3")
    task = SpecificationTask("exit", "evaluate", "bounded", "", spec)
    monkeypatch.setattr(submission, "locate_lean", lambda *args, **kwargs: SimpleNamespace(executable="wrapper"))
    checker = CheckerRunResult(False, returncode, "", "wrapper failed", 1, False)
    # An older Engine can report mathematical rejection despite these exits.
    monkeypatch.setattr(submission, "verify_answer", lambda *args: SimpleNamespace(
        checker=checker, status="mathematical_rejection", verified=False,
        scope="encoded_specification_only", specification_digest=spec.digest,
    ))
    verdict = verify_specification_submission('```json\n{"answer":3}\n```', task)
    assert verdict.status == "operational_error"
    assert verdict.stage == "internal"
    assert not verdict.accepted


def test_singleflight_survives_all_consumers_cancelling_and_reuses_completion():
    async def scenario():
        cache = AsyncSingleFlight(max_completed=2)
        started, release = asyncio.Event(), asyncio.Event()
        calls = 0

        async def factory():
            nonlocal calls
            calls += 1
            started.set()
            await release.wait()
            return "checked"

        consumer = asyncio.create_task(cache.get("same", factory))
        await started.wait()
        consumer.cancel()
        with pytest.raises(asyncio.CancelledError):
            await consumer
        # A new consumer must join the check that is still running.
        joined = asyncio.create_task(cache.get("same", factory))
        await asyncio.sleep(0)
        joined.cancel()
        with pytest.raises(asyncio.CancelledError):
            await joined
        release.set()
        # Drain work and its completion callback with no surviving consumer.
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert await cache.get("same", factory) == "checked"
        assert calls == 1

    asyncio.run(scenario())


def test_singleflight_completed_cache_is_loop_local_and_lru_bounded():
    cache = AsyncSingleFlight(max_completed=2)
    calls = []

    async def value(key):
        async def factory():
            calls.append(key)
            return key
        return await cache.get(key, factory)

    async def scenario():
        for key in ("a", "b", "a", "c", "a", "b"):
            assert await value(key) == key

    asyncio.run(scenario())
    assert calls == ["a", "b", "c", "b"]
    asyncio.run(value("a"))
    assert calls == ["a", "b", "c", "b", "a"]


@pytest.mark.parametrize("module,verifier,task_key,verdict_key", [
    (mathcheck_rl, "verify_specification_submission", "nv_spec_verdict_task", "nv_spec_verdict"),
    (native_verify_seq, "verify", "nv_verdict_task", "nv_verdict"),
])
def test_v0_cancelled_initiator_does_not_duplicate_running_check(
    monkeypatch, module, verifier, task_key, verdict_key,
):
    verdict = Verdict(True, "verified", None, status="checked_success")
    calls = []

    async def scenario():
        started, release = asyncio.Event(), asyncio.Event()

        async def fake_to_thread(fn, *args, **kwargs):
            calls.append(fn)
            started.set()
            await release.wait()
            return verdict

        monkeypatch.setattr(module.asyncio, "to_thread", fake_to_thread)
        if module is mathcheck_rl:
            completion = [{"content": '```json\n{"answer":3}\n```'}]
            answer = json.dumps({"specification": {"kind": "evaluate", "expression": "3"}})
        else:
            completion = [{"content": "```lean\ndef f (n : Nat) : Nat := n\n```"}]
            answer = json.dumps({"train": [0], "holdout": [1]})
        state = {}
        initiator = asyncio.create_task(module._get_verdict(completion, answer, state))
        await started.wait()
        work = state[task_key]
        initiator.cancel()
        with pytest.raises(asyncio.CancelledError):
            await initiator
        assert state[task_key] is work
        follower = asyncio.create_task(module._get_verdict(completion, answer, state))
        await asyncio.sleep(0)
        release.set()
        assert await follower is verdict
        assert state[verdict_key] is verdict
        assert task_key not in state
        assert len(calls) == 1

    asyncio.run(scenario())


@pytest.mark.parametrize("module", [mathcheck_rl, native_verify_seq])
def test_v1_retries_operational_errors_and_keys_effective_runtime(monkeypatch, module):
    monkeypatch.setattr(module, "_V1_VERDICTS", AsyncSingleFlight())
    monkeypatch.delenv("NATIVE_VERIFY_LEAN", raising=False)
    monkeypatch.setenv("LEAN_BIN", "/wrapper/a")
    monkeypatch.setenv("LKV_SANDBOX_TOOLCHAIN", "leanprover/lean4:v4.23.0")
    calls = []

    def verify(*args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return Verdict(False, "internal", "unavailable", status="operational_error")
        return Verdict(True, "verified", None, status="checked_success")

    if module is mathcheck_rl:
        monkeypatch.setattr(module, "verify_specification_submission", verify)
        task = module.NativeSpecificationTask(module.NativeSpecificationTaskData(
            name="spec", specification={"kind": "evaluate", "expression": "3"},
        ))
        response = '```json\n{"answer":3}\n```'
    else:
        monkeypatch.setattr(module, "verify", verify)
        task = module.NativeVerifyTask(module.NativeVerifyTaskData(
            name="seq", train_values=[0], holdout_values=[1],
        ))
        response = "```lean\ndef f (n : Nat) : Nat := n\n```"

    async def scenario():
        trace = SimpleNamespace(last_reply=response)
        assert (await task._run(trace)).status == "operational_error"
        assert (await task._run(trace)).accepted
        assert (await task._run(trace)).accepted
        assert len(calls) == 2
        monkeypatch.setenv("LEAN_BIN", "/wrapper/b")
        await task._run(trace)
        assert len(calls) == 3
        assert calls[-1]["lean_bin"] == "/wrapper/b"
        monkeypatch.setenv("LKV_SANDBOX_TOOLCHAIN", "different-toolchain")
        await task._run(trace)
        assert len(calls) == 4

    asyncio.run(scenario())


def test_v1_framework_scoring_records_metadata_with_one_check(monkeypatch):
    from verifiers.v1.configs.agent import AgentConfig
    from verifiers.v1.graph import MessageNode
    from verifiers.v1.trace import AgentInfo, Trace, TraceTask
    from verifiers.v1.types import AssistantMessage

    monkeypatch.setattr(mathcheck_rl, "_V1_VERDICTS", AsyncSingleFlight())
    calls = []
    verdict = Verdict(
        True, "verified", None, diagnostics=["check complete"], duration_ms=25,
        status="checked_success", backend="oneshot_cli", scope="encoded_specification_only",
        specification_digest="spec-digest", artifact_digest="artifact-digest", checker_invocations=1,
    )

    def verify(*args, **kwargs):
        calls.append(args)
        return verdict

    monkeypatch.setattr(mathcheck_rl, "verify_specification_submission", verify)
    task = mathcheck_rl.NativeSpecificationTask(mathcheck_rl.NativeSpecificationTaskData(
        name="spec", specification={"kind": "evaluate", "expression": "3"},
    ))
    trace = Trace(
        task=TraceTask(type=type(task).__name__, data=task.data),
        agent=AgentInfo(config=AgentConfig()),
        nodes=[MessageNode(message=AssistantMessage(content='```json\n{"answer":3}\n```'), sampled=True)],
    )
    asyncio.run(task.score(trace, runtime=object()))
    assert trace.reward == 1.0
    assert trace.rewards["nv_verify_seconds"].score == 0.025
    assert trace.info["nv_status"] == "checked_success"
    assert trace.info["nv_artifact_digest"] == "artifact-digest"
    assert trace.info["nv_scope"] == "encoded_specification_only"
    assert trace.info["nv_duration_ms"] == 25
    assert trace.info["nv_checker_invocations"] == 1
    assert trace.info["nv_diagnostics"] == ["check complete"]
    assert len(calls) == 1
