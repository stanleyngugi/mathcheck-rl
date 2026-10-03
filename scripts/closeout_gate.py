"""Finite audit closeout: source delivery, installed artifacts and native evidence.

Exit 0: source and native gates passed. Exit 1: a required check failed.
Exit 2: source delivery passed, native validation is explicitly blocked/unrequested.
No policy training, inference, publishing or account changes are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import venv

from release_gate import EXPECTED_WHEELS, SOURCE_DATE_EPOCH


SOURCE_CHECKS = ("engine_source_tests", "rl_source_tests", "candidate_wheels",
                 "consumer_install", "consumer_dependencies", "installed_structural_smoke")
NATIVE_CHECKS = ("quickstart", "engine_live_tests", "rl_live_tests", "procedural_controls",
                 "gsm8k_development_controls", "gsm8k_demo_controls", "native_release_gate")


def completion_state(checks):
    source_complete = all(checks.get(name, {}).get("status") == "passed" for name in SOURCE_CHECKS)
    native_complete = all(checks.get(name, {}).get("status") == "passed" for name in NATIVE_CHECKS)
    failed = any(row.get("status") == "failed" for row in checks.values())
    status = "failed" if failed else "validated_delivery_complete" if source_complete and native_complete else (
        "source_delivery_complete_native_blocked" if source_complete else "incomplete")
    return {"status": status, "source_delivery_complete": source_complete,
            "native_validation_complete": native_complete,
            "release_ready": source_complete and native_complete and not failed,
            "rl_learning_results_required": False,
            "exit_code": 1 if failed or not source_complete else 0 if native_complete else 2}


class Closeout:
    def __init__(self, output: Path):
        self.output = output.resolve()
        self.output.mkdir(parents=True, exist_ok=False)
        (self.output/"tmp").mkdir()
        self.checks = {}
        self.started = time.monotonic()

    def run(self, name, command, *, cwd=None, env=None, timeout=900):
        started = time.monotonic()
        log = self.output/(name+".log")
        environment = dict(os.environ if env is None else env)
        environment["TMPDIR"] = str(self.output/"tmp")
        with log.open("x", encoding="utf-8") as stream:
            try:
                result = subprocess.run(command, cwd=cwd or self.output, env=environment,
                    stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
                code = result.returncode
            except (OSError, subprocess.TimeoutExpired) as exc:
                stream.write(type(exc).__name__ + ": " + str(exc)+"\n")
                code = -1
        self.checks[name] = {"status": "passed" if code == 0 else "failed",
            "returncode": code, "log": log.name, "seconds": round(time.monotonic()-started, 3)}
        print(f"{name}: {self.checks[name]['status']}", flush=True)
        return code == 0

    def finish(self, *, details=None):
        state = completion_state(self.checks)
        report = {"schema": "mathcheck-audit-closeout-v1", **state,
            "checks": self.checks, "details": details or {},
            "elapsed_seconds": round(time.monotonic()-self.started, 3),
            "optional_work": ["pretrained_policy_training", "learning_gain_measurement",
                              "automatic_formalization", "broader_dataset_coverage"]}
        with (self.output/"closeout.json").open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
        print(json.dumps(state, sort_keys=True))
        return state["exit_code"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verifier-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--toolchain", type=Path)
    parser.add_argument("--toolchain-sha256")
    args = parser.parse_args()
    if bool(args.toolchain) != bool(args.toolchain_sha256):
        parser.error("provide --toolchain and --toolchain-sha256 together")
    root = Path(__file__).resolve().parents[1]
    engine = args.verifier_root.resolve(strict=True)
    gate = Closeout(args.output)
    source_env = os.environ.copy()
    for key in ("LEAN_BIN", "NATIVE_VERIFY_LEAN", "LKV_SANDBOX_TOOLCHAIN"):
        source_env.pop(key, None)
    details = {"native_integrations_disabled_for_source_phase": True,
               "source_date_epoch": SOURCE_DATE_EPOCH,
               "source_file_sha256": {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (Path(__file__).resolve(), root/"scripts/wheel_smoke.py")}}
    for name, directory in (("engine_source_tests", engine), ("rl_source_tests", root)):
        if not gate.run(name, [sys.executable, "-m", "pytest", "tests", "-q",
                              "--basetemp", str(gate.output/(name+"-tmp"))], cwd=directory, env=source_env):
            return gate.finish(details=details)
    wheels = gate.output/"wheels"
    build_env = dict(source_env, SOURCE_DATE_EPOCH=SOURCE_DATE_EPOCH)
    for index, directory in enumerate((engine, root, root/"environments/native_verify_seq", root/"environments/mathcheck_rl")):
        if not gate.run(f"wheel_build_{index}", [sys.executable, "-m", "build", "--wheel", "--no-isolation",
                         "--outdir", str(wheels)], cwd=directory, env=build_env):
            return gate.finish(details=details)
    actual_wheels = sorted(wheels.glob("*.whl"))
    gate.checks["candidate_wheels"] = {"status": "passed" if {p.name for p in actual_wheels} == EXPECTED_WHEELS else "failed",
                                       "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in actual_wheels}}
    if gate.checks["candidate_wheels"]["status"] != "passed":
        return gate.finish(details=details)
    consumer = gate.output/"consumer"
    venv.EnvBuilder(with_pip=True).create(consumer)
    python = str(consumer/"bin/python")
    hub = next(p for p in actual_wheels if p.name.startswith("mathcheck_rl-"))
    dependencies = [p for p in actual_wheels if p != hub]
    if not gate.run("consumer_install", [python, "-m", "pip", "install", "--disable-pip-version-check",
                "-r", str(root/"requirements-release.lock"), *map(str, dependencies)], env=source_env):
        return gate.finish(details=details)
    if not gate.run("consumer_hub_install", [python, "-m", "pip", "install", "--disable-pip-version-check",
                                           "--no-deps", str(hub)], env=source_env):
        return gate.finish(details=details)
    if not gate.run("consumer_dependencies", [python, "-m", "pip", "check"], env=source_env):
        return gate.finish(details=details)
    if not gate.run("installed_structural_smoke", [python, str(root/"scripts/wheel_smoke.py"),
                                                   "--structural-only"], env=source_env):
        return gate.finish(details=details)
    if not args.toolchain:
        for name in NATIVE_CHECKS:
            gate.checks[name] = {"status": "blocked", "reason": "explicit_native_toolchain_not_supplied"}
        return gate.finish(details=details)
    toolchain = args.toolchain.resolve(strict=True)
    lean = toolchain/"bin/lean"
    if not lean.is_file() or hashlib.sha256(lean.read_bytes()).hexdigest() != args.toolchain_sha256.lower():
        gate.checks["native_toolchain_identity"] = {"status": "failed", "reason": "missing_lean_or_binary_digest_mismatch"}
        return gate.finish(details=details)
    if toolchain.stat().st_mode & 0o222 or lean.stat().st_mode & 0o222:
        gate.checks["native_toolchain_identity"] = {"status": "failed", "reason": "toolchain_root_and_binary_must_be_read_only"}
        return gate.finish(details=details)
    native_env = dict(source_env, LKV_SANDBOX_TOOLCHAIN=str(toolchain), LEAN_BIN=str(lean),
                      NATIVE_VERIFY_LEAN=str(consumer/"bin/lean-isolated"))
    if not gate.run("lean_startup", [str(lean), "--version"], env=native_env, timeout=30):
        gate.checks["lean_startup"]["status"] = "blocked"
        for name in NATIVE_CHECKS:
            gate.checks[name] = {"status": "blocked", "reason": "stock_lean_startup_failed"}
        return gate.finish(details=details)
    if not gate.run("quickstart", [python, str(root/"examples/specification_quickstart.py"),
                                  "--lean-bin", native_env["NATIVE_VERIFY_LEAN"]], env=native_env):
        try:
            controls = json.loads((gate.output/"quickstart.log").read_text())["controls"]
            operational = len(controls) == 6 and all(row["status"] == "operational_error" for row in controls)
        except (KeyError, ValueError):
            operational = False
        if operational:
            gate.checks["quickstart"]["status"] = "blocked"
        for name in NATIVE_CHECKS[1:]:
            gate.checks[name] = {"status": "blocked", "reason": "native_quickstart_not_passed"}
        return gate.finish(details=details)
    commands = [("engine_live_tests", [sys.executable, "-m", "pytest", "tests", "-q"], engine),
                ("rl_live_tests", [sys.executable, "-m", "pytest", "tests", "-q"], root)]
    for name, imported in (("procedural_controls", None), ("gsm8k_development_controls", "development_manifest.json"),
                           ("gsm8k_demo_controls", "evaluation_demo_manifest.json")):
        command = [python, str(root/"scripts/profile_specification_checks.py"), "--lean-bin", native_env["NATIVE_VERIFY_LEAN"],
                   "--output", str(gate.output/(name+".jsonl"))]
        if imported:
            command += ["--import-manifest", str(root/"examples/gsm8k"/imported)]
        commands.append((name, command, gate.output))
    commands.append(("native_release_gate", [sys.executable, str(root/"scripts/release_gate.py"),
        "--verifier-root", str(engine), "--toolchain", str(toolchain), "--toolchain-sha256", args.toolchain_sha256,
        "--output", str(gate.output/"native-release")], root))
    for name, command, cwd in commands:
        if not gate.run(name, command, cwd=cwd, env=native_env):
            return gate.finish(details=details)
    return gate.finish(details=details)


if __name__ == "__main__":
    raise SystemExit(main())
