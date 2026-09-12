from __future__ import annotations

from pathlib import Path
import tomllib

import native_verify


ROOT = Path(__file__).resolve().parents[1]


def _project(relative: str = "pyproject.toml") -> dict:
    with (ROOT / relative).open("rb") as stream:
        return tomllib.load(stream)["project"]


def test_root_package_python_and_engine_contract() -> None:
    project = _project()
    assert project["version"] == native_verify.__version__ == "0.2.1"
    assert project["requires-python"] == ">=3.11,<3.14"
    assert "lean-kernel-verifier>=0.3.2,<0.4" in project["dependencies"]
    assert "Programming Language :: Python :: 3.10" not in project["classifiers"]
    assert "Programming Language :: Python :: 3.13" in project["classifiers"]


def test_environment_packages_share_supported_python_range() -> None:
    sequence = _project("environments/native_verify_seq/pyproject.toml")
    hub = _project("environments/mathcheck_rl/pyproject.toml")
    assert sequence["version"] == "0.2.1"
    assert hub["version"] == "0.1.1"
    assert sequence["requires-python"] == hub["requires-python"] == ">=3.11,<3.14"
    assert any(
        dependency.endswith("mathcheck-engine.git@742edec6bdb4f7057780fc54e98fb284b76eedcf")
        for dependency in hub["dependencies"]
    )
    assert any(
        dependency.endswith("mathcheck-rl.git@d4912c30564e99a3200f77ca7e94a8a3ebe184c7")
        for dependency in hub["dependencies"]
    )
