"""Project a pinned official GSM8K source into question-only formalizer input.

The extraction process reads upstream records containing solutions. It writes
only questions and provenance; no formalizer/solver receives solution fields.
Selection is fixed by indices, never by correctness or solution contents.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--split", choices=("train", "test"), required=True)
    parser.add_argument("--indices", required=True, help="Comma-separated zero-based indices")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.revision):
        parser.error("revision must be a full Git commit")
    indices = [int(i) for i in args.indices.split(",")]
    if len(set(indices)) != len(indices) or any(i < 0 for i in indices):
        parser.error("indices must be unique and nonnegative")
    url = f"https://raw.githubusercontent.com/openai/grade-school-math/{args.revision}/grade_school_math/data/{args.split}.jsonl"
    data = urllib.request.urlopen(url, timeout=30).read()
    digest = hashlib.sha256(data).hexdigest()
    lines = data.splitlines()
    rows = []
    for index in indices:
        question = json.loads(lines[index])["question"]
        rows.append({"dataset": "openai/gsm8k", "revision": args.revision,
                     "source_split": args.split, "source_index": index,
                     "source_id": f"GSM8K:{args.split}:{index}", "question": question,
                     "question_sha256": hashlib.sha256(question.encode()).hexdigest(),
                     "source_file_sha256": digest})
    with args.output.open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"Exported {len(rows)} question-only rows; source SHA-256 {digest}")


if __name__ == "__main__":
    main()
