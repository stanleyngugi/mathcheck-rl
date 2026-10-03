"""Independent semantic controls, plus optional real Lean differential coverage."""
import os

import pytest
from lean_kernel_verifier.certificates import PairCertificate, PairCountSpec
from lean_kernel_verifier.specification import ProblemSpec
from native_verify.reference_checks import reference_accepts, reference_result
from native_verify.specification_tasks import SpecificationTask, verify_specification_submission


@pytest.mark.parametrize("spec, expected", [
    (ProblemSpec("evaluate", "(-7)//3+10"), 7),
    (ProblemSpec("evaluate", "(-7)%3"), 2),
    (ProblemSpec("evaluate", "2**4-3*2"), 10),
    (ProblemSpec("count", "not (x%2 == 0) and 1 <= x < 5", 0, 8), 2),
    (ProblemSpec("sum", "x-4", 0, 3), -9),
    (ProblemSpec("count", "x == 0", 0, 0), 0),
    (ProblemSpec("minimum", "x%3 == 2 and x%5 == 1", 0, 30), 11),
])
def test_python_semantics(spec, expected):
    assert reference_result(spec) == expected


def test_feasibility_is_insufficient_and_no_solution_is_not_a_candidate():
    spec = ProblemSpec("minimum", "x%3 == 2 and x%5 == 1", 0, 30)
    assert reference_accepts(spec, 11)
    assert not reference_accepts(spec, 26)
    assert not reference_accepts(spec, True)
    assert not reference_accepts(ProblemSpec("minimum", "x > 10", 0, 5), 0)


def test_complete_relation_and_empty_relation():
    spec = PairCountSpec("x < y and x+y == 4", 0, 5, 0, 5)
    assert reference_result(spec) == PairCertificate(((0, 4), (1, 3)), 2)
    assert not reference_accepts(spec, PairCertificate(((0, 4),), 1))
    assert reference_accepts(PairCountSpec("x < y", 0, 0, 0, 0), PairCertificate((), 0))


@pytest.mark.skipif(not os.environ.get("NATIVE_VERIFY_LEAN"), reason="requires isolated Lean 4.23.0")
@pytest.mark.parametrize("spec, candidates", [
    (ProblemSpec("evaluate", "(-7)//3+10"), (7, 8)),
    (ProblemSpec("evaluate", "(-7)%3"), (2, 3)),
    (ProblemSpec("minimum", "x%3 == 2 and x%5 == 1", 0, 30), (11, 26, 41)),
])
def test_live_differential_controls(spec, candidates):
    task = SpecificationTask("differential", spec.kind, "control", "control", spec)
    for candidate in candidates:
        result = verify_specification_submission(f'```json\n{{"answer": {candidate}}}\n```', task)
        assert result.status in {"checked_success", "mathematical_rejection"}
        assert result.accepted == reference_accepts(spec, candidate)
