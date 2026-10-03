"""No-provider control and latency sweep of the current bounded contracts."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lean_kernel_verifier.certificates import PairCertificate, PairCountSpec
from lean_kernel_verifier.specification import ProblemSpec
from native_verify.reference_checks import reference_accepts, reference_result
from native_verify.specification_tasks import (
    SpecificationTask, generate_specification_tasks, specification_to_dict,
    verify_specification_submission,
)


def control_tasks(seed: int, per_family: int):
    tasks = generate_specification_tasks(per_family=per_family, seed=seed)
    for name, spec in (
        ("negative_floor", ProblemSpec("evaluate", "(-7)//3 + 10")),
        ("negative_modulo", ProblemSpec("evaluate", "(-7)%3")),
        ("minimum_leastness", ProblemSpec("minimum", "x%3 == 2 and x%5 == 1", 0, 30)),
        ("empty_count", ProblemSpec("count", "x == 0", 0, 0)),
        ("pair_completeness", PairCountSpec("x < y and x+y == 4", 0, 5, 0, 5)),
    ):
        tasks.append(SpecificationTask(name, spec.kind, "control", name, spec))
    return tasks


def controls(spec):
    correct = reference_result(spec)
    yield "correct", correct
    if isinstance(correct, PairCertificate):
        if correct.pairs:
            missing = correct.pairs[:-1]
            yield "incomplete", PairCertificate(missing, len(missing))
        else:
            yield "wrong_count", PairCertificate((), 1)
    else:
        yield "adjacent_wrong", correct + 1
        if spec.kind == "minimum":
            for candidate in range(correct + 1, spec.stop):
                narrowed = ProblemSpec("minimum", spec.expression, candidate, spec.stop)
                try:
                    if reference_result(narrowed) == candidate:
                        yield "feasible_nonminimal", candidate
                        break
                except ValueError:
                    break


def response(candidate):
    payload = {"answer": candidate.answer, "pairs": candidate.pairs} if isinstance(
        candidate, PairCertificate) else {"answer": candidate}
    return "```json\n" + json.dumps(payload) + "\n```"


def _write(stream, record):
    stream.write(json.dumps(record, sort_keys=True) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lean-bin")
    parser.add_argument("--import-manifest", type=Path, help="Use a frozen reviewed dataset slice instead of procedural tasks")
    parser.add_argument("--reference-only", action="store_true")
    parser.add_argument("--seed", type=int, default=20261003)
    parser.add_argument("--per-family", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    if not args.reference_only and not args.lean_bin:
        parser.error("--lean-bin is required unless --reference-only is explicit")
    if args.import_manifest:
        from native_verify.dataset_import import task_from_import_record, text_sha256
        imported = json.loads(args.import_manifest.read_text(encoding="utf-8"))
        commitment = imported.pop("manifest_sha256")
        if text_sha256(json.dumps(imported, sort_keys=True, separators=(",", ":"))) != commitment:
            raise ValueError("import manifest digest changed")
        tasks = [task_from_import_record(row) for row in imported["tasks"]]
        if not tasks:
            raise ValueError("import manifest contains no supported tasks")
    else:
        tasks = control_tasks(args.seed, args.per_family)
    native_ms, reference_ms, statuses = [], [], {}
    disagreements = operational = 0
    with args.output.open("x", encoding="utf-8") as stream:
        _write(stream, {
            "record_type": "manifest", "schema": "mathcheck-controls-v1",
            "reference_only": args.reference_only, "seed": args.seed,
            "per_family": args.per_family, "lean_bin": args.lean_bin,
            "import_manifest_sha256": commitment if args.import_manifest else None,
            "toolchain": os.environ.get("LKV_SANDBOX_TOOLCHAIN"),
            "specification_digests": [t.specification_digest for t in tasks],
            "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (Path(__file__).resolve(), ROOT / "src/native_verify/reference_checks.py")},
        })
        for task in tasks:
            for label, candidate in controls(task.specification):
                started = time.perf_counter()
                expected = reference_accepts(task.specification, candidate)
                elapsed = (time.perf_counter() - started) * 1000
                reference_ms.append(elapsed)
                row = {"record_type": "control", "task_id": task.task_id,
                       "family": task.family, "control": label,
                       "specification": specification_to_dict(task.specification),
                       "specification_digest": task.specification_digest,
                       "response": response(candidate), "reference_accepted": expected,
                       "reference_ms": elapsed}
                if not args.reference_only:
                    verdict = verify_specification_submission(row["response"], task,
                              lean_bin=args.lean_bin, timeout_seconds=args.timeout)
                    row["native"] = asdict(verdict)
                    statuses[verdict.status] = statuses.get(verdict.status, 0) + 1
                    native_ms.append(verdict.duration_ms)
                    if verdict.status == "operational_error":
                        operational += 1
                    elif verdict.accepted != expected:
                        disagreements += 1
                _write(stream, row)
        summary = {"record_type": "terminal", "reference_only": args.reference_only,
                   "control_count": len(reference_ms), "native_statuses": statuses,
                   "disagreements": disagreements, "operational_errors": operational,
                   "reference_median_ms": statistics.median(reference_ms),
                   "native_median_ms": statistics.median(native_ms) if native_ms else None,
                   "native_evidence_complete": not args.reference_only and not operational}
        _write(stream, summary)
    print(json.dumps(summary, indent=2))
    return 1 if disagreements or operational else 0


if __name__ == "__main__":
    raise SystemExit(main())
