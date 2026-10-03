"""Closeout cannot turn source tests or an unavailable compiler into native success."""
import importlib.util
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]/"scripts"
sys.path.insert(0, str(SCRIPTS))
try:
    import closeout_gate
    import wheel_smoke
finally:
    sys.path.pop(0)


def checks(source="passed", native="passed"):
    return {**{name: {"status": source} for name in closeout_gate.SOURCE_CHECKS},
            **{name: {"status": native} for name in closeout_gate.NATIVE_CHECKS}}


def test_source_delivery_can_finish_without_learning_but_not_claim_native_success():
    result = closeout_gate.completion_state(checks(native="blocked"))
    assert result["source_delivery_complete"]
    assert result["exit_code"] == 2 and not result["release_ready"]
    assert not result["native_validation_complete"] and not result["rl_learning_results_required"]


def test_complete_native_gate_is_a_finite_success_without_a_training_run():
    result = closeout_gate.completion_state(checks())
    assert result["exit_code"] == 0 and result["release_ready"]
    assert result["status"] == "validated_delivery_complete"


def test_native_failure_is_not_a_blocked_or_successful_release():
    result = closeout_gate.completion_state(checks(native="failed"))
    assert result["exit_code"] == 1 and result["status"] == "failed"
    assert result["source_delivery_complete"] and not result["release_ready"]


def test_missing_source_checks_do_not_satisfy_completion():
    assert closeout_gate.completion_state({})["exit_code"] == 1


def test_installed_native_smoke_covers_leastness_and_complete_pairs(monkeypatch):
    import asyncio
    from types import SimpleNamespace
    calls = []
    async def fixture(completion, answer, state):
        index = len(calls)
        calls.append((completion, answer))
        status = "checked_success" if index % 2 == 0 else "mathematical_rejection"
        state["nv_spec_verdict"] = SimpleNamespace(status=status, checker_invocations=1, reason=None)
        return float(index % 2 == 0)
    monkeypatch.setattr(wheel_smoke.mathcheck_rl, "specification_pass", fixture)
    controls = asyncio.run(wheel_smoke._verify_controls())
    assert len(calls) == 6
    assert {row["control"] for row in controls} == {"count_correct", "count_wrong", "minimum_least",
                                                   "minimum_nonleast", "pairs_complete", "pairs_incomplete"}


def test_installed_native_smoke_rejects_operational_zero_rewards(monkeypatch):
    import asyncio
    from types import SimpleNamespace
    async def broken(completion, answer, state):
        state["nv_spec_verdict"] = SimpleNamespace(status="operational_error", checker_invocations=1, reason="broken")
        return 0.
    monkeypatch.setattr(wheel_smoke.mathcheck_rl, "specification_pass", broken)
    with pytest.raises(AssertionError, match="operational_error"):
        asyncio.run(wheel_smoke._verify_controls())
