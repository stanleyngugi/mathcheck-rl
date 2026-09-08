import json
import os

import pytest

from lean_kernel_verifier.certificates import PairCountSpec
from lean_kernel_verifier.specification import ProblemSpec
from native_verify.specification_tasks import (
    SpecificationTask,
    generate_disjoint_specification_splits,
    generate_specification_tasks,
    parse_specification_submission,
    verify_specification_submission,
)


def fenced(payload):
    return "```json\n" + json.dumps(payload) + "\n```"


def test_tasks_store_specifications_not_expected_answers():
    tasks = generate_specification_tasks(per_family=2, seed=7)
    assert tasks
    assert all(not hasattr(task, "answer") for task in tasks)
    assert all("answer" not in task.__dataclass_fields__ for task in tasks)
    assert all(task.specification_digest not in task.prompt for task in tasks)


def test_disjoint_splits_bind_mathematical_specifications():
    train, evaluation = generate_disjoint_specification_splits(
        train_per_family=4, eval_per_family=2, train_seed=0, eval_seed=1000
    )
    train_digests = {task.specification_digest for task in train}
    eval_digests = {task.specification_digest for task in evaluation}
    assert len(train_digests) == len(train)
    assert len(eval_digests) == len(evaluation)
    assert train_digests.isdisjoint(eval_digests)


def test_candidate_cannot_replace_environment_specification():
    spec = ProblemSpec("count", "x%3 == 0", 1, 10)
    task = SpecificationTask("t", "bounded_count", "bounded", "prompt", spec)
    assert parse_specification_submission(fenced({"answer": 3}), spec) == 3
    with pytest.raises(ValueError):
        parse_specification_submission(
            fenced({"answer": 3, "specification": {"kind": "evaluate", "expression": "3"}}),
            spec,
        )
    verdict = verify_specification_submission(fenced({"answer": True}), task)
    assert verdict.status == "invalid_input"
    assert verdict.checker_invocations == 0
    assert verify_specification_submission(fenced({"answer": -1}), task).status == "invalid_input"


def test_pair_parser_requires_complete_certificate_shape():
    spec = PairCountSpec("x < y", 0, 3, 0, 3)
    candidate = parse_specification_submission(
        fenced({"answer": 3, "pairs": [[0, 1], [0, 2], [1, 2]]}), spec
    )
    assert candidate.answer == 3
    with pytest.raises(ValueError):
        parse_specification_submission(fenced({"answer": 3}), spec)


def test_missing_isolation_wrapper_is_operational_failure():
    spec = ProblemSpec("count", "x%3 == 0", 1, 10)
    task = SpecificationTask("t", "bounded_count", "bounded", "prompt", spec)
    verdict = verify_specification_submission(
        fenced({"answer": 3}),
        task,
        lean_bin="/definitely/missing/lean-isolated",
    )
    assert not verdict.accepted
    assert verdict.stage == "internal"
    assert verdict.status == "operational_error"
    assert verdict.reason == "checker_backend_error"


requires_lean = pytest.mark.skipif(not os.environ.get("LEAN_BIN"), reason="isolated Lean required")


@requires_lean
def test_live_scalar_positive_wrong_and_nonminimal_controls():
    cases = (
        (ProblemSpec("count", "x%3 == 0", 1, 10), 3, 4),
        (ProblemSpec("sum", "x*x", 1, 5), 30, 31),
        (ProblemSpec("minimum", "x%7 == 3 and x%5 == 2", 0, 100), 17, 52),
    )
    for index, (spec, correct, wrong) in enumerate(cases):
        task = SpecificationTask(str(index), spec.kind, "bounded", "prompt", spec)
        accepted = verify_specification_submission(fenced({"answer": correct}), task)
        rejected = verify_specification_submission(fenced({"answer": wrong}), task)
        assert accepted.accepted and accepted.status == "checked_success", accepted
        assert not rejected.accepted and rejected.status == "mathematical_rejection", rejected
        assert accepted.specification_digest == rejected.specification_digest == spec.digest


@requires_lean
def test_live_pair_completeness_control():
    spec = PairCountSpec("x < y and x+y == 4", 0, 5, 0, 5)
    task = SpecificationTask("pairs", "bounded_pair_count", "bounded", "prompt", spec)
    complete = verify_specification_submission(
        fenced({"answer": 2, "pairs": [[0, 4], [1, 3]]}), task
    )
    incomplete = verify_specification_submission(
        fenced({"answer": 1, "pairs": [[0, 4]]}), task
    )
    assert complete.accepted and complete.status == "checked_success", complete
    assert not incomplete.accepted and incomplete.status == "mathematical_rejection", incomplete
