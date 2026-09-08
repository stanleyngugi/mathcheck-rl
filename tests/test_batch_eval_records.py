import argparse
import json

from scripts import batch_eval


def test_batch_eval_records_are_exclusive_and_terminal(monkeypatch, tmp_path):
    monkeypatch.setenv("TEST_NATIVE_KEY", "not-a-real-key")
    calls = []

    def fake_chat(*args):
        calls.append(args)
        return "no fenced artifact", None, 1

    monkeypatch.setattr(batch_eval, "chat_completion", fake_chat)
    output = tmp_path / "record.jsonl"
    args = argparse.Namespace(
        api_key_env="TEST_NATIVE_KEY",
        families="linear",
        per_family=1,
        seed=0,
        out=str(output),
        base_url="https://invalid.example",
        model="fixture-model",
        temperature=0.0,
        max_tokens=32,
        verify_timeout=5.0,
        max_attempts=1,
        save_artifacts=False,
    )
    assert batch_eval.run_eval(args) == 0
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert [row["record_type"] for row in rows] == ["manifest", "trial", "terminal"]
    assert rows[0]["config"]["max_attempts"] == 1
    assert rows[1]["api_attempts"] == 1
    assert rows[-1]["status"] == "complete"
    assert rows[-1]["dispatches"] == rows[-1]["completed_trials"] == 1
    assert len(calls) == 1

    assert batch_eval.run_eval(args) == 2
    assert len(calls) == 1
