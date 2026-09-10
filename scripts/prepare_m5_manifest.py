"""Create an exclusive, offline M5 preregistration manifest."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from native_verify.pilot_manifest import (
    PilotInputs,
    PilotRuntime,
    build_pilot_manifest,
    canonical_json_sha256,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare M5 inputs without making provider calls"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--release-manifest", type=Path, required=True)
    parser.add_argument("--native-commit", required=True)
    parser.add_argument("--verifier-commit", required=True)
    parser.add_argument("--benchmark-completion-reference", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--model-id-revision", required=True)
    parser.add_argument("--trainer-runtime-version", required=True)
    parser.add_argument("--temperature", type=float, required=True)
    parser.add_argument("--top-p", type=float, required=True)
    parser.add_argument("--token-limit", type=int, required=True)
    parser.add_argument("--currency-conversion-source", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    release_path = args.release_manifest.resolve()
    with release_path.open("r", encoding="utf-8") as stream:
        release_manifest = json.load(stream)
    runtime = PilotRuntime(
        provider=args.provider,
        model_id_revision=args.model_id_revision,
        trainer_runtime_version=args.trainer_runtime_version,
        temperature=args.temperature,
        top_p=args.top_p,
        token_limit=args.token_limit,
        currency_conversion_source=args.currency_conversion_source,
    )
    inputs = PilotInputs(
        native_commit=args.native_commit,
        verifier_commit=args.verifier_commit,
        release_manifest_canonical_sha256=canonical_json_sha256(release_manifest),
        benchmark_completion_reference=args.benchmark_completion_reference,
    )
    manifest = build_pilot_manifest(runtime, inputs, release_manifest)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(f"created M5 preregistration: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
