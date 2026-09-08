from __future__ import annotations

import os
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from lean_kernel_verifier.runner.checker_runner import CheckerRunConfig, LeanCheckerRunner
from lean_kernel_verifier.sanitizer.sanitizer import SanitizerConfig

from .sanitizer import sanitize_model_code
from .template import build_checker_source
from .types import Verdict

ERROR_LINE_RE = re.compile(r":(\d+):\d+:\s*error")
PINNED_LEAN_VERSION = (4, 23, 0)


@dataclass(slots=True)
class LeanBackend:
    mode: str
    executable: str


def locate_lean(explicit: str | None = None, *, probe: bool = True) -> LeanBackend | None:
    """Resolve only an explicitly configured shared isolation wrapper.

    A broken explicit backend never falls through to a host Lean installation.
    Native verification is supported from Linux/WSL processes, where the shared
    ``lean-isolated`` entry point can be executed directly.
    """
    configured = explicit
    if configured is None:
        configured = os.getenv("NATIVE_VERIFY_LEAN") or os.getenv("LEAN_BIN")
    if not configured:
        return None
    candidate = _explicit_backend(configured)
    if candidate.mode != "direct" or Path(candidate.executable).name != "lean-isolated":
        return None
    return candidate if not probe or _probe(candidate) else None


def _is_windows() -> bool:
    return sys.platform == "win32"


def _explicit_backend(path: str) -> LeanBackend:
    if _is_windows() and path.startswith("/"):
        return LeanBackend(mode="wsl", executable=path)
    return LeanBackend(mode="direct", executable=path)


def verify(
    model_code: str,
    train_values: Sequence[int],
    holdout_values: Sequence[int],
    *,
    lean_bin: str | None = None,
    timeout_seconds: float = 60.0,
) -> Verdict:
    start = time.perf_counter()

    def elapsed_ms() -> int:
        return int((time.perf_counter() - start) * 1000)

    sanitized = sanitize_model_code(model_code)
    if not sanitized.accepted:
        return Verdict(
            accepted=False,
            stage="sanitize",
            reason=sanitized.reason,
            diagnostics=sanitized.errors[:10],
            duration_ms=elapsed_ms(),
            backend="none",
            status="invalid_input",
            artifact_digest=_digest_text(model_code) if isinstance(model_code, str) else "",
        )

    try:
        source, markers = build_checker_source(sanitized.model_code, train_values, holdout_values)
    except ValueError as exc:
        return Verdict(
            accepted=False,
            stage="internal",
            reason=f"template_error:{exc}",
            duration_ms=elapsed_ms(),
            backend="none",
            status="invalid_input",
            artifact_digest=_digest_text(sanitized.model_code),
        )

    specification_digest = _finite_specification_digest(train_values, holdout_values)
    artifact_digest = _digest_text(sanitized.model_code)

    backend = locate_lean(lean_bin, probe=False)
    if backend is None:
        return Verdict(
            accepted=False,
            stage="internal",
            reason="lean_not_found",
            duration_ms=elapsed_ms(),
            backend="none",
            status="operational_error",
            specification_digest=specification_digest,
            artifact_digest=artifact_digest,
        )
    runner = LeanCheckerRunner(CheckerRunConfig(
        lean_executable=backend.executable,
        timeout_seconds=max(1, int(timeout_seconds)),
        min_lean_version=PINNED_LEAN_VERSION,
        required_lean_version=PINNED_LEAN_VERSION,
        execution_mode="oneshot_cli",
    ))
    try:
        checked = runner.run_source(
            source,
            SanitizerConfig(profile="A", enforce_template_contract=False),
        )
    finally:
        runner.close()

    output = checked.stdout + "\n" + checked.stderr
    invocations = 1 if checked.returncode is None and not checked.timed_out else 2
    if checked.timed_out:
        return Verdict(
            accepted=False, stage="timeout", reason="checker_timeout",
            duration_ms=elapsed_ms(), backend=checked.backend_mode,
            status="operational_error", specification_digest=specification_digest,
            artifact_digest=artifact_digest, checker_invocations=invocations,
        )
    if checked.backend_error or checked.returncode in (124, 125) or checked.returncode is None:
        diagnostics = [line.strip() for line in output.splitlines() if line.strip()][-10:]
        return Verdict(
            accepted=False, stage="internal", reason="checker_backend_error",
            diagnostics=diagnostics, duration_ms=elapsed_ms(), backend=checked.backend_mode,
            status="operational_error", specification_digest=specification_digest,
            artifact_digest=artifact_digest, checker_invocations=invocations,
        )
    error_lines = [line.strip() for line in output.splitlines() if ": error" in line]
    if checked.success and not error_lines:
        return Verdict(
            accepted=True,
            stage="verified",
            reason=None,
            duration_ms=elapsed_ms(),
            backend=checked.backend_mode,
            status="checked_success",
            specification_digest=specification_digest,
            artifact_digest=artifact_digest,
            checker_invocations=invocations,
        )
    stage, reason = classify_failure(output, markers)
    diagnostics = error_lines[:10] or [line.strip() for line in output.splitlines() if line.strip()][-5:]
    return Verdict(
        accepted=False,
        stage=stage,
        reason=reason,
        diagnostics=diagnostics,
        duration_ms=elapsed_ms(),
        backend=checked.backend_mode,
        status="mathematical_rejection" if stage in {"train_check", "holdout_check"} else "invalid_input",
        specification_digest=specification_digest,
        artifact_digest=artifact_digest,
        checker_invocations=invocations,
    )


def classify_failure(output: str, markers: dict[str, int]) -> tuple[str, str]:
    match = ERROR_LINE_RE.search(output)
    if match is None:
        return "compile", "unknown_failure"
    line_no = int(match.group(1))
    if line_no >= markers["verify_holdout"]:
        return "holdout_check", "holdout_mismatch"
    if line_no >= markers["verify_train"]:
        return "train_check", "train_mismatch"
    return "compile", "model_or_template_error"


def _probe(backend: LeanBackend) -> bool:
    runner = LeanCheckerRunner(CheckerRunConfig(
        lean_executable=backend.executable,
        min_lean_version=PINNED_LEAN_VERSION,
        required_lean_version=PINNED_LEAN_VERSION,
    ))
    try:
        return runner._ensure_lean_compatible() is None
    finally:
        runner.close()


def _digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _finite_specification_digest(
    train_values: Sequence[int], holdout_values: Sequence[int]
) -> str:
    payload = {
        "contract": "finite_observation_v1",
        "train": list(train_values),
        "holdout": list(holdout_values),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _to_wsl_path(path: Path | str) -> str:
    if isinstance(path, str) and path.startswith("/"):
        return path
    resolved = Path(path).resolve()
    drive = resolved.drive.rstrip(":").lower()
    rest = str(resolved)[len(resolved.drive):].replace("\\", "/")
    return f"/mnt/{drive}{rest}"
