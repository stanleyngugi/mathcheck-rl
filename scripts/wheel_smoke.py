"""Smoke installed release wheels without importing either source tree."""
from __future__ import annotations

import asyncio
import importlib.metadata as metadata
import inspect
import json
from pathlib import Path

import native_verify
import native_verify_seq
import native_verify_spec
from lean_kernel_verifier.specification import ProblemSpec


EXPECTED_VERSIONS = {
    "lean-kernel-verifier": "0.3.1",
    "native-verify": "0.2.0",
    "native-verify-seq": "0.2.0",
    "native-verify-spec": "0.1.0",
    "verifiers": "0.3.0",
    "datasets": "4.8.5",
}


def _completion(answer: int):
    fence = chr(96) * 3
    return [{
        "role": "assistant",
        "content": fence + "json\n" + json.dumps({"answer": answer}) + "\n" + fence,
    }]


async def _verify_pair(row: dict) -> tuple[str, str]:
    payload = json.loads(row["answer"])
    assert set(payload) == {"specification"}
    specification = ProblemSpec.from_dict(payload["specification"])
    correct = next(
        x for x in range(specification.start, specification.stop)
        if eval(specification.expression, {"__builtins__": {}}, {"x": x})
    )
    accepted_state: dict = {}
    rejected_state: dict = {}
    accepted = await native_verify_spec.specification_pass(
        _completion(correct), row["answer"], accepted_state
    )
    rejected = await native_verify_spec.specification_pass(
        _completion(correct + 1), row["answer"], rejected_state
    )
    assert (accepted, rejected) == (1.0, 0.0)
    statuses = (
        accepted_state["nv_spec_verdict"].status,
        rejected_state["nv_spec_verdict"].status,
    )
    assert statuses == ("checked_success", "mathematical_rejection")
    return statuses


def main() -> int:
    versions = {name: metadata.version(name) for name in EXPECTED_VERSIONS}
    assert versions == EXPECTED_VERSIONS
    for module in (native_verify, native_verify_seq, native_verify_spec):
        module_path = Path(inspect.getfile(module)).resolve()
        assert "site-packages" in module_path.parts, module_path

    sequence = native_verify_seq.load_environment(
        num_per_family=1, eval_num_per_family=1
    )
    specification = native_verify_spec.load_environment(
        families="bounded_minimum",
        num_per_family=1,
        eval_num_per_family=1,
        seed=17,
        eval_seed=1017,
    )
    row = specification.dataset[0]
    info = json.loads(row["info"])
    assert info["contains_expected_answer"] is False
    assert "answer" not in json.loads(row["answer"])["specification"]
    statuses = asyncio.run(_verify_pair(row))
    print(json.dumps({
        "versions": versions,
        "sequence_rows": [len(sequence.dataset), len(sequence.eval_dataset)],
        "specification_rows": [
            len(specification.dataset), len(specification.eval_dataset)
        ],
        "statuses": statuses,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
