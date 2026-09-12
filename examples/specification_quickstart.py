"""MathCheck RL quickstart: one answer-key-free task, two candidate outcomes."""
from __future__ import annotations

import argparse
import json

from lean_kernel_verifier.specification import ProblemSpec
from native_verify.specification_tasks import SpecificationTask, verify_specification_submission


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lean-bin", required=True, help="Path to lean-isolated")
    args = parser.parse_args()

    specification = ProblemSpec("count", "x%3 == 0", 1, 20)
    task = SpecificationTask(
        task_id="quickstart_count",
        family="bounded_count",
        difficulty="bounded",
        prompt="Count multiples of three in the half-open interval [1, 20).",
        specification=specification,
    )
    accepted = verify_specification_submission(
        '```json\n{"answer": 6}\n```', task, lean_bin=args.lean_bin
    )
    rejected = verify_specification_submission(
        '```json\n{"answer": 7}\n```', task, lean_bin=args.lean_bin
    )
    print(json.dumps({
        "project": "MathCheck RL",
        "task_id": task.task_id,
        "specification_digest": task.specification_digest,
        "candidate_6": accepted.status,
        "candidate_7": rejected.status,
    }, indent=2))
    return 0 if accepted.accepted and rejected.status == "mathematical_rejection" else 1


if __name__ == "__main__":
    raise SystemExit(main())
