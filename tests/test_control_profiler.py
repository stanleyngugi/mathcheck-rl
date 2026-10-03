"""Profiler records distinguish reference-only QA from native evidence."""
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_reference_only_profile_preserves_complete_controls(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("control_profiler", ROOT / "scripts/profile_specification_checks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output = tmp_path / "controls.jsonl"
    monkeypatch.setattr(sys, "argv", ["profile", "--reference-only", "--per-family", "1", "--output", str(output)])
    assert module.main() == 0
    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert records[0]["record_type"] == "manifest"
    assert records[-1]["native_evidence_complete"] is False
    assert records[-1]["native_median_ms"] is None
    controls = records[1:-1]
    assert any(r["control"] == "feasible_nonminimal" and not r["reference_accepted"] for r in controls)
    assert any(r["control"] == "incomplete" and not r["reference_accepted"] for r in controls)
    assert all("native" not in r for r in controls)
    import pytest
    with pytest.raises(FileExistsError):
        module.main()
