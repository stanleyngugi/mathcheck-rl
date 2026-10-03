"""Smoke installed release wheels without importing either source tree."""
from __future__ import annotations

import asyncio
import argparse
import importlib.metadata as metadata
import inspect
import json
from pathlib import Path

import native_verify
import native_verify_seq
import mathcheck_rl
import lean_kernel_verifier
from lean_kernel_verifier.certificates import PairCountSpec
from lean_kernel_verifier.specification import ProblemSpec
from native_verify.specification_tasks import specification_to_dict


EXPECTED_VERSIONS = {
    "lean-kernel-verifier": "0.3.3",
    "native-verify": "0.2.2",
    "native-verify-seq": "0.2.2",
    "mathcheck-rl": "0.1.2",
    "verifiers": "0.3.0",
    "datasets": "4.8.5",
}


def _completion(payload):
    fence = chr(96) * 3
    return [{
        "role": "assistant",
        "content": fence + "json\n" + json.dumps(payload) + "\n" + fence,
    }]


async def _verify_controls():
    # Known control data is artifact QA, never a training/reference-answer row.
    cases = [
        ("count_correct", ProblemSpec("count", "x%3 == 0", 1, 20), {"answer": 6}, "checked_success"),
        ("count_wrong", ProblemSpec("count", "x%3 == 0", 1, 20), {"answer": 7}, "mathematical_rejection"),
        ("minimum_least", ProblemSpec("minimum", "x%3 == 2 and x%5 == 1", 0, 30), {"answer": 11}, "checked_success"),
        ("minimum_nonleast", ProblemSpec("minimum", "x%3 == 2 and x%5 == 1", 0, 30), {"answer": 26}, "mathematical_rejection"),
        ("pairs_complete", PairCountSpec("x < y and x+y == 4", 0, 5, 0, 5), {"answer": 2, "pairs": [[0, 4], [1, 3]]}, "checked_success"),
        ("pairs_incomplete", PairCountSpec("x < y and x+y == 4", 0, 5, 0, 5), {"answer": 1, "pairs": [[0, 4]]}, "mathematical_rejection"),
    ]
    controls = []
    for name, specification, candidate, expected in cases:
        state = {}
        reward = await mathcheck_rl.specification_pass(_completion(candidate),
            json.dumps({"specification": specification_to_dict(specification)}), state)
        verdict = state["nv_spec_verdict"]
        assert verdict.status == expected, (name, expected, verdict.status, verdict.reason)
        assert reward == float(expected == "checked_success")
        assert verdict.checker_invocations == 1
        controls.append({"control": name, "status": verdict.status, "reward": reward})
    return controls


async def _invalid_input_control(row):
    state = {}
    reward = await mathcheck_rl.specification_pass(
        [{"role": "assistant", "content": "invalid JSON submission"}], row["answer"], state)
    verdict = state["nv_spec_verdict"]
    assert reward == 0 and verdict.status == "invalid_input" and verdict.checker_invocations == 0
    return {"status": verdict.status, "reward": reward, "checker_invocations": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structural-only", action="store_true",
                        help="Explicit installed-package checks without native acceptance evidence")
    args = parser.parse_args()
    versions = {name: metadata.version(name) for name in EXPECTED_VERSIONS}
    assert versions == EXPECTED_VERSIONS
    for module in (lean_kernel_verifier, native_verify, native_verify_seq, mathcheck_rl):
        module_path = Path(inspect.getfile(module)).resolve()
        assert "site-packages" in module_path.parts, module_path

    sequence = native_verify_seq.load_environment(
        num_per_family=1, eval_num_per_family=1
    )
    specification = mathcheck_rl.load_environment(
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
    invalid_input = asyncio.run(_invalid_input_control(row))
    controls = [] if args.structural_only else asyncio.run(_verify_controls())
    print(json.dumps({
        "versions": versions,
        "sequence_rows": [len(sequence.dataset), len(sequence.eval_dataset)],
        "specification_rows": [
            len(specification.dataset), len(specification.eval_dataset)
        ],
        "invalid_input": invalid_input,
        "controls": controls,
        "native_evidence_complete": not args.structural_only,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
