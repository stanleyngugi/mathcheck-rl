"""native-verify: execution-as-verification harness for RL training."""

from .runner import LeanBackend, locate_lean, verify
from .sanitizer import SanitizeResult, sanitize_model_code
from .template import build_checker_source
from .types import Verdict
from .specification_tasks import (
    SPECIFICATION_FAMILIES,
    SpecificationTask,
    generate_disjoint_specification_splits,
    generate_specification_tasks,
    parse_specification_submission,
    verify_specification_submission,
)

__version__ = "0.2.1"

__all__ = [
    "LeanBackend",
    "SanitizeResult",
    "Verdict",
    "SPECIFICATION_FAMILIES",
    "SpecificationTask",
    "build_checker_source",
    "locate_lean",
    "sanitize_model_code",
    "verify",
    "generate_disjoint_specification_splits",
    "generate_specification_tasks",
    "parse_specification_submission",
    "verify_specification_submission",
    "__version__",
]
