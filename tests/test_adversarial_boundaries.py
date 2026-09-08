import asyncio
import hashlib
import json

import pytest

import native_verify_spec
from lean_kernel_verifier.certificates import PairCountSpec
from lean_kernel_verifier.specification import ProblemSpec
from native_verify.async_cache import AsyncSingleFlight
from native_verify.sanitizer import sanitize_model_code
from native_verify.specification_tasks import (
    SpecificationTask,
    generate_disjoint_specification_splits,
    generate_specification_tasks,
    parse_specification_submission,
    specification_to_dict,
)


def _fenced_body(body: str) -> str:
    return "```json\n" + body + "\n```"


@pytest.mark.parametrize("declaration", [
    "  abbrev escape : Nat := 1",
    "  axiom escape : False",
    "  private def escape : Nat := 1",
    "  noncomputable def escape : Nat := 1",
    "  namespace Escape",
    "  protected def escape : Nat := 1",
    "  theorem escape : True := by trivial",
    "  unsafe def escape : Nat := 1",
    "  variable (escape : Nat)",
])
def test_indented_declaration_bypasses_fail_closed(declaration):
    artifact = "def f (n : Nat) : Nat := n\n" + declaration
    result = sanitize_model_code(artifact)
    assert not result.accepted


@pytest.mark.parametrize("submission", [
    _fenced_body('{"answer": 3, "answer": 4}'),
    _fenced_body('{"answer": 3} trailing'),
    _fenced_body('{"answer": 3.0}'),
    "prefix\n" + _fenced_body('{"answer": 3}'),
    _fenced_body('{"answer": 3}') + "\n" + _fenced_body('{"answer": 3}'),
    _fenced_body('{"answer": 3}') + (" " * 100_001),
])
def test_scalar_submission_ambiguities_are_rejected(submission):
    specification = ProblemSpec("count", "x%3 == 0", 1, 10)
    with pytest.raises(ValueError):
        parse_specification_submission(submission, specification)


@pytest.mark.parametrize("payload", [
    {"answer": 1, "pairs": [[0]]},
    {"answer": 1, "pairs": [[0, 1], [0, 1]]},
    {"answer": 1, "pairs": [[1, 0], [0, 1]]},
    {"answer": True, "pairs": [[0, 1]]},
    {"answer": 1, "pairs": [[-1, 1]]},
])
def test_pair_certificate_shape_and_canonicalization_fail_closed(payload):
    specification = PairCountSpec("x < y", 0, 3, 0, 3)
    with pytest.raises(ValueError):
        parse_specification_submission(
            _fenced_body(json.dumps(payload)), specification
        )


def test_singleflight_does_not_cache_failures():
    async def scenario():
        cache = AsyncSingleFlight(max_completed=2)
        calls = 0

        async def fail():
            nonlocal calls
            calls += 1
            await asyncio.sleep(0)
            raise RuntimeError("expected failure")

        results = await asyncio.gather(
            cache.get("same", fail), cache.get("same", fail),
            return_exceptions=True,
        )
        assert all(isinstance(result, RuntimeError) for result in results)
        with pytest.raises(RuntimeError):
            await cache.get("same", fail)
        assert calls == 2

    asyncio.run(scenario())


def test_multiple_seed_splits_remain_digest_disjoint():
    for seed in range(10):
        training, evaluation = generate_disjoint_specification_splits(
            train_per_family=10,
            eval_per_family=10,
            train_seed=seed,
            eval_seed=10_000 + seed,
        )
        training_digests = {task.specification_digest for task in training}
        evaluation_digests = {task.specification_digest for task in evaluation}
        assert len(training_digests) == 40
        assert len(evaluation_digests) == 40
        assert training_digests.isdisjoint(evaluation_digests)


def test_preregistered_m5_splits_are_frozen_and_pairwise_disjoint():
    expected = {
        (10, 20260909): "96c8f1139a37f1acd9fec83f6e61a54b60f2b02fc4fed79a2150ad52a3df90bc",
        (20, 20270909): "34148fde00892e68abac3997856ba49f9a003e8ac5547e95820af3555cdd1249",
        (20, 20280909): "e0a208362d56742c1703be5d5ac02dd30d38db757e9d2da24c1246d5fb7a9a28",
    }
    digest_sets = []
    for (per_family, seed), commitment in expected.items():
        tasks = generate_specification_tasks(per_family=per_family, seed=seed)
        payload = [{
            "task_id": task.task_id,
            "family": task.family,
            "specification": specification_to_dict(task.specification),
            "specification_digest": task.specification_digest,
        } for task in tasks]
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        assert hashlib.sha256(canonical.encode()).hexdigest() == commitment
        digest_sets.append({task.specification_digest for task in tasks})
    assert all(
        digest_sets[left].isdisjoint(digest_sets[right])
        for left, right in ((0, 1), (0, 2), (1, 2))
    )


def test_operational_verdict_cannot_earn_framework_reward(monkeypatch):
    task = SpecificationTask(
        "t", "bounded_count", "bounded", "prompt",
        ProblemSpec("count", "x%3 == 0", 1, 10),
    )
    environment = native_verify_spec.load_environment(
        families="bounded_count", num_per_family=1, eval_num_per_family=1
    )
    row = environment.dataset[0]

    class OperationalVerdict:
        accepted = False
        stage = "internal"
        reason = "checker_backend_error"
        duration_ms = 0
        status = "operational_error"

    monkeypatch.setattr(
        native_verify_spec,
        "verify_specification_submission",
        lambda *args, **kwargs: OperationalVerdict(),
    )

    async def score():
        state = {}
        reward = await native_verify_spec.specification_pass(
            [{"role": "assistant", "content": _fenced_body('{"answer": 3}')}],
            row["answer"],
            state,
        )
        assert reward == 0.0
        assert state["nv_spec_verdict"].status == "operational_error"

    asyncio.run(score())
