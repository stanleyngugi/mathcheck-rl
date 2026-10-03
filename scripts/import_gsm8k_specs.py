"""Freeze a reviewed question-only GSM8K slice. No provider or Lean calls."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from native_verify.dataset_import import build_import_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--role", choices=("training", "development", "held_out_test", "evaluation_demonstration"), required=True)
    parser.add_argument("--exclude-manifest", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    questions = [json.loads(line) for line in args.questions.read_text().splitlines() if line.strip()]
    decisions = json.loads(args.reviews.read_text())
    excluded_questions, excluded_specs = set(), set()
    for path in args.exclude_manifest:
        manifest = json.loads(path.read_text())
        for row in manifest["tasks"] + manifest["exclusions"]:
            excluded_questions.add(row["question_sha256"])
            if "specification_digest" in row:
                excluded_specs.add(row["specification_digest"])
    manifest = build_import_manifest(questions, decisions, role=args.role,
                 excluded_question_digests=excluded_questions,
                 excluded_specification_digests=excluded_specs)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(f'Frozen {len(manifest["tasks"])} tasks and {len(manifest["exclusions"])} exclusions; {manifest["manifest_sha256"]}')


if __name__ == "__main__":
    main()
