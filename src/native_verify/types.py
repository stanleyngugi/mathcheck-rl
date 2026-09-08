from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


VerdictStatus = Literal[
    "checked_success",
    "mathematical_rejection",
    "invalid_input",
    "unsupported_task",
    "operational_error",
]


@dataclass(slots=True)
class SanitizeResult:
    accepted: bool
    model_code: str = ""
    reason: str | None = None
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Verdict:
    accepted: bool
    stage: str
    reason: str | None
    diagnostics: list[str] = field(default_factory=list)
    duration_ms: int = 0
    backend: str = ""
    status: VerdictStatus = "invalid_input"
    scope: str = "finite_observation"
    specification_digest: str = ""
    artifact_digest: str = ""
    checker_invocations: int = 0
