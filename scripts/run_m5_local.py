"""Run the frozen pilot with a local checkpoint and a healthy isolated checker."""
from __future__ import annotations

import argparse
import functools
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

from native_verify.grpo import LocalTrainingConfig, TransformersPolicy, checkpoint_digest
from native_verify.local_pilot import LocalPilot, PilotStopped, validate_manifest
from native_verify.specification_tasks import verify_specification_submission


def checked_source(root, commit, module_file):
    root = root.resolve(strict=True)
    if root not in Path(module_file).resolve().parents:
        raise ValueError("imported package is outside its frozen checkout")
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root, text=True)
    if actual != commit or dirty:
        raise ValueError("source checkout is dirty or differs from the frozen commit")
    subprocess.run(["git", "ls-files", "--error-unmatch", str(Path(module_file).resolve().relative_to(root))],
                   cwd=root, check=True, capture_output=True)


def preflight(release, wheel_dir, lean_bin):
    from packaging.utils import parse_wheel_filename
    from lean_kernel_verifier.specification import ProblemSpec
    from lean_kernel_verifier.certificates import PairCountSpec
    from native_verify.specification_tasks import SpecificationTask
    toolchain = Path(os.environ.get("LKV_SANDBOX_TOOLCHAIN", "")).resolve()
    lean = toolchain / "bin/lean"
    if not lean.is_file() or toolchain.stat().st_mode & 0o222 or lean.stat().st_mode & 0o222:
        raise ValueError("a separately installed read-only Lean toolchain is required")
    if hashlib.sha256(lean.read_bytes()).hexdigest() != release["lean_binary_sha256"]:
        raise ValueError("Lean binary differs from the release gate")
    version = subprocess.run([str(lean), "--version"], check=True, capture_output=True, text=True, timeout=30).stdout
    if "Lean (version 4.23.0," not in version:
        raise ValueError("Lean 4.23.0 is required")
    # The reward launcher must be the installed isolated entry point.
    launcher = Path(lean_bin).resolve(strict=True)
    if launcher.name != "lean-isolated" or "lean_kernel_verifier.isolation" not in launcher.read_text():
        raise ValueError("use the installed lean-isolated entry point")
    distributions = set()
    for name, digest in release["wheels"].items():
        if Path(name).name != name:
            raise ValueError("release wheel name is not a basename")
        if hashlib.sha256((wheel_dir/name).read_bytes()).hexdigest() != digest:
            raise ValueError("wheel differs from release manifest: " + name)
        distribution, version, _, _ = parse_wheel_filename(name)
        distributions.add(distribution)
        if metadata.version(distribution) != str(version):
            raise ValueError("installed package version differs from gated wheel: " + name)
    if distributions != {"lean-kernel-verifier", "native-verify", "native-verify-seq", "mathcheck-rl"}:
        raise ValueError("release manifest does not bind the four MathCheck distributions")
    cases = [
        (ProblemSpec("count", "x%3 == 0", 1, 20), {"answer": 6}, "checked_success"),
        (ProblemSpec("count", "x%3 == 0", 1, 20), {"answer": 7}, "mathematical_rejection"),
        (ProblemSpec("minimum", "x%3 == 2 and x%5 == 1", 0, 30), {"answer": 11}, "checked_success"),
        (ProblemSpec("minimum", "x%3 == 2 and x%5 == 1", 0, 30), {"answer": 26}, "mathematical_rejection"),
        (PairCountSpec("x < y and x+y == 4", 0, 5, 0, 5), {"answer": 2, "pairs": [[0,4], [1,3]]}, "checked_success"),
        (PairCountSpec("x < y and x+y == 4", 0, 5, 0, 5), {"answer": 1, "pairs": [[0,4]]}, "mathematical_rejection"),
    ]
    for index, (spec, payload, expected) in enumerate(cases):
        verdict = verify_specification_submission("```json\n" + json.dumps(payload) + "\n```",
            SpecificationTask(f"preflight-{index}", "control", "control", "control", spec),
            lean_bin=str(launcher))
        if verdict.status != expected:
            raise ValueError(f"native preflight {index} failed: {verdict.status}: {verdict.reason}")
    return str(launcher)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "release-manifest", "training-config", "checkpoint", "wheel-dir", "verifier-root", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--lean-bin", required=True)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        parser.error("local pilot requires Linux with working bubblewrap")
    config = LocalTrainingConfig(**json.loads(args.training_config.read_text()))
    manifest = json.loads(args.manifest.read_text())
    release = json.loads(args.release_manifest.read_text())
    validate_manifest(manifest, release, config)
    if args.output.exists():
        raise ValueError("output directory must not already exist")
    import native_verify
    import lean_kernel_verifier
    native_root = Path(__file__).resolve().parents[1]
    checked_source(native_root, manifest["inputs"]["native_commit"], native_verify.__file__)
    checked_source(args.verifier_root, manifest["inputs"]["verifier_commit"], lean_kernel_verifier.__file__)
    if manifest["training_plan"]["trainer_source_commit"] != manifest["inputs"]["native_commit"]:
        raise ValueError("trainer source must match this frozen RL checkout")
    runtime = ";".join(f"{name}=={metadata.version(name)}" for name in ("torch", "transformers"))
    if runtime != manifest["runtime"]["trainer_runtime_version"]:
        raise ValueError("actual training dependency versions differ from preregistration")
    if checkpoint_digest(args.checkpoint) != manifest["training_plan"]["initial_checkpoint_sha256"]:
        raise ValueError("initial checkpoint changed")
    launcher = preflight(release, args.wheel_dir.resolve(strict=True), args.lean_bin)
    print("native preflight passed; starting the frozen local pilot", flush=True)
    def deadline(signum, frame):
        raise PilotStopped("wall_clock_budget_exhausted")
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, manifest["budgets"]["maximum_wall_clock_minutes"]*60)
    try:
        policy = TransformersPolicy(args.checkpoint, config)
        runner = LocalPilot(manifest, release, config, policy,
                            functools.partial(verify_specification_submission, lean_bin=launcher), args.output)
        result = runner.run()
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "complete" else 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, PilotStopped, subprocess.SubprocessError, OSError) as exc:
        print(f"local pilot stopped: {exc}", file=sys.stderr)
        raise SystemExit(1)
