import asyncio
import json
from types import SimpleNamespace

import native_verify_seq
import native_verify_spec


def test_v0_sequence_metrics_share_one_inflight_verdict(monkeypatch):
    calls = []

    def fake_verify(*args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(
            accepted=True, stage="verified", reason=None, duration_ms=25,
            status="checked_success",
        )

    monkeypatch.setattr(native_verify_seq, "verify", fake_verify)

    async def scenario():
        completion = [{"role": "assistant", "content": "```lean\ndef f (n : Nat) : Nat := n\n```"}]
        answer = json.dumps({"train": [0], "holdout": [1]})
        state = {}
        scores = await asyncio.gather(
            native_verify_seq.lean_pass(completion, answer, state),
            native_verify_seq.stage_rank(completion, answer, state),
            native_verify_seq.verify_seconds(completion, answer, state),
        )
        assert scores == [1.0, 4.0, 0.025]
        assert state["nv_verdict"].status == "checked_success"

    asyncio.run(scenario())
    assert len(calls) == 1


def test_environment_rows_bind_disjoint_specs_without_candidate_answers():
    seq = native_verify_seq.load_environment(
        families="linear", num_per_family=2, eval_num_per_family=1,
        seed=1, eval_seed=1001,
    )
    seq_train = {json.loads(row["info"])["specification_digest"] for row in seq.dataset}
    seq_eval = {json.loads(row["info"])["specification_digest"] for row in seq.eval_dataset}
    assert seq_train.isdisjoint(seq_eval)

    spec = native_verify_spec.load_environment(
        families="bounded_count", num_per_family=2, eval_num_per_family=1,
        seed=1, eval_seed=1001,
    )
    for row in list(spec.dataset) + list(spec.eval_dataset):
        metadata = json.loads(row["info"])
        checker_input = json.loads(row["answer"])
        assert metadata["contains_expected_answer"] is False
        assert set(checker_input) == {"specification"}
        assert "answer" not in checker_input["specification"]
