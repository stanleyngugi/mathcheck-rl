"""MathCheck RL quickstart: one answer-key-free task, two candidate outcomes."""
from __future__ import annotations

import argparse
import json

from lean_kernel_verifier.specification import ProblemSpec
from lean_kernel_verifier.certificates import PairCountSpec
from native_verify.specification_tasks import SpecificationTask, verify_specification_submission


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lean-bin", required=True, help="Path to lean-isolated")
    args = parser.parse_args()

    cases = [
        ("count", ProblemSpec("count", "x%3 == 0", 1, 20),
         [("correct", {"answer": 6}, "checked_success"),
          ("adjacent_wrong", {"answer": 7}, "mathematical_rejection")]),
        ("minimum", ProblemSpec("minimum", "x%3 == 2 and x%5 == 1", 0, 30),
         [("least", {"answer": 11}, "checked_success"),
          ("feasible_nonminimal", {"answer": 26}, "mathematical_rejection")]),
        ("pairs", PairCountSpec("x < y and x+y == 4", 0, 5, 0, 5),
         [("complete", {"answer": 2, "pairs": [[0, 4], [1, 3]]}, "checked_success"),
          ("incomplete", {"answer": 1, "pairs": [[0, 4]]}, "mathematical_rejection")]),
    ]
    records = []
    passed = True
    for name, specification, controls in cases:
        task = SpecificationTask(name, name, "bounded", name, specification)
        for label, payload, expected in controls:
            verdict = verify_specification_submission(
                "```json\n" + json.dumps(payload) + "\n```", task, lean_bin=args.lean_bin
            )
            passed = passed and verdict.status == expected
            records.append({"task": name, "control": label, "expected": expected,
                            "status": verdict.status, "reason": verdict.reason,
                            "specification_digest": task.specification_digest})
    print(json.dumps({"project": "MathCheck RL", "controls": records}, indent=2))
    return 0 if passed else 1



if __name__ == "__main__":
    raise SystemExit(main())
