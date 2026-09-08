import pytest

from native_verify import locate_lean, verify
from native_verify.runner import classify_failure

HONEST_FIB = """def fib : Nat -> Nat
  | 0 => 0
  | 1 => 1
  | n + 2 => fib (n + 1) + fib n

def f (n : Nat) : Nat := fib n"""

HARDCODED_TABLE = """def f (n : Nat) : Nat :=
  match n with
  | 0 => 0
  | 1 => 1
  | 2 => 1
  | 3 => 2
  | 4 => 3
  | 5 => 5
  | 6 => 8
  | 7 => 13
  | 8 => 21
  | 9 => 34
  | 10 => 55
  | 11 => 89
  | _ => 0"""

TRAIN = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
HOLDOUT = [144, 233, 377, 610]

MARKERS = {"model_start": 3, "verify_train": 10, "verify_holdout": 14}


def test_classify_holdout_error():
    output = "checker.lean:15:31: error: unsolved goals"
    assert classify_failure(output, MARKERS) == ("holdout_check", "holdout_mismatch")


def test_classify_train_error():
    output = "checker.lean:11:3: error: unsolved goals"
    assert classify_failure(output, MARKERS) == ("train_check", "train_mismatch")


def test_classify_model_compile_error():
    output = "checker.lean:5:12: error: unknown identifier"
    assert classify_failure(output, MARKERS) == ("compile", "model_or_template_error")


def test_classify_unknown_failure():
    assert classify_failure("some fatal crash", MARKERS) == ("compile", "unknown_failure")


LEAN = locate_lean()
requires_lean = pytest.mark.skipif(LEAN is None, reason="no Lean backend available")


@requires_lean
def test_sanitize_rejection_does_not_touch_lean():
    verdict = verify("def f (n : Nat) : Nat := sorry", TRAIN, HOLDOUT)
    assert not verdict.accepted
    assert verdict.stage == "sanitize"
    assert verdict.backend == "none"
    assert verdict.status == "invalid_input"
    assert verdict.checker_invocations == 0


@requires_lean
def test_honest_fib_accepted():
    verdict = verify(HONEST_FIB, TRAIN, HOLDOUT)
    assert verdict.accepted, (verdict.stage, verdict.reason, verdict.diagnostics)
    assert verdict.stage == "verified"
    assert verdict.status == "checked_success"
    assert len(verdict.specification_digest) == 64
    assert len(verdict.artifact_digest) == 64


@requires_lean
def test_hardcoded_table_fails_holdout():
    verdict = verify(HARDCODED_TABLE, TRAIN, HOLDOUT)
    assert not verdict.accepted
    assert verdict.stage == "holdout_check"
    assert verdict.reason == "holdout_mismatch"
    assert verdict.status == "mathematical_rejection"


def test_explicit_backend_failure_does_not_fall_through(monkeypatch):
    monkeypatch.setenv("LEAN_BIN", "/some/other/lean-isolated")
    assert locate_lean("/definitely/missing/lean-isolated") is None


def test_host_lean_is_not_an_accepted_backend(monkeypatch):
    monkeypatch.delenv("NATIVE_VERIFY_LEAN", raising=False)
    monkeypatch.setenv("LEAN_BIN", "lean")
    assert locate_lean() is None


def test_missing_isolation_wrapper_is_operational_failure():
    verdict = verify(
        HONEST_FIB,
        TRAIN,
        HOLDOUT,
        lean_bin="/definitely/missing/lean-isolated",
    )
    assert not verdict.accepted
    assert verdict.stage == "internal"
    assert verdict.status == "operational_error"
    assert verdict.reason == "checker_backend_error"


@requires_lean
def test_wrong_formula_fails_train_or_holdout():
    artifact = "def f (n : Nat) : Nat := n + 1"
    verdict = verify(artifact, TRAIN, HOLDOUT)
    assert not verdict.accepted
    assert verdict.stage in {"train_check", "holdout_check"}
