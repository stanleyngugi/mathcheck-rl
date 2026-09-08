"""Build and smoke versioned wheels against an independently owned Lean copy."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv


EXPECTED_WHEELS = {
    "lean_kernel_verifier-0.3.1-py3-none-any.whl",
    "native_verify-0.2.0-py3-none-any.whl",
    "native_verify_seq-0.2.0-py3-none-any.whl",
    "native_verify_spec-0.1.0-py3-none-any.whl",
}
LOCKED_RELEASE_TOOLS = {
    "build": "1.6.0",
    "datasets": "4.8.5",
    "hatchling": "1.32.0",
    "pytest": "9.1.1",
    "setuptools": "84.0.0",
    "verifiers": "0.3.0",
    "wheel": "0.48.0",
}
SOURCE_DATE_EPOCH = "1704067200"


def _run(command: list[str], *, cwd: Path | None = None, env: dict | None = None) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True, timeout=900)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verifier-root", type=Path, required=True)
    parser.add_argument("--toolchain", type=Path, required=True)
    parser.add_argument("--toolchain-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    if not sys.platform.startswith("linux"):
        raise SystemExit("release gate requires Linux or WSL")
    args = _parse_args()
    actual_tools = {
        name: metadata.version(name) for name in LOCKED_RELEASE_TOOLS
    }
    if actual_tools != LOCKED_RELEASE_TOOLS:
        raise SystemExit(
            "release tools do not match requirements-release.lock: "
            + json.dumps(actual_tools, sort_keys=True)
        )
    native_root = Path(__file__).resolve().parents[1]
    verifier_root = args.verifier_root.resolve()
    toolchain = args.toolchain.resolve()
    lean = toolchain / "bin" / "lean"
    if not lean.is_file():
        raise SystemExit("toolchain has no bin/lean")
    if toolchain.stat().st_mode & 0o222 or lean.stat().st_mode & 0o222:
        raise SystemExit("release toolchain root and Lean binary must be read-only")
    if _sha256(lean) != args.toolchain_sha256.lower():
        raise SystemExit("Lean binary digest mismatch")
    version = subprocess.run(
        [str(lean), "--version"], check=True, capture_output=True, text=True, timeout=30
    ).stdout
    if "Lean (version 4.23.0," not in version:
        raise SystemExit("release gate requires Lean 4.23.0 exactly")

    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit("output directory must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    package_roots = (
        verifier_root,
        native_root,
        native_root / "environments" / "native_verify_seq",
        native_root / "environments" / "native_verify_spec",
    )
    build_env = os.environ.copy()
    build_env["SOURCE_DATE_EPOCH"] = SOURCE_DATE_EPOCH
    for package_root in package_roots:
        _run([
            sys.executable, "-m", "build", "--wheel", "--no-isolation",
            "--outdir", str(output),
        ], cwd=package_root, env=build_env)
    wheels = sorted(output.glob("*.whl"))
    if {wheel.name for wheel in wheels} != EXPECTED_WHEELS:
        raise SystemExit("built wheel set or versions do not match the release contract")

    with tempfile.TemporaryDirectory(prefix="native-verify-release-") as temporary:
        environment_root = Path(temporary) / "venv"
        venv.EnvBuilder(with_pip=True).create(environment_root)
        python = environment_root / "bin" / "python"
        _run([
            str(python), "-m", "pip", "install", "--disable-pip-version-check",
            *map(str, wheels),
        ])
        _run([str(python), "-m", "pip", "check"])
        smoke_env = os.environ.copy()
        smoke_env["NATIVE_VERIFY_LEAN"] = str(environment_root / "bin" / "lean-isolated")
        smoke_env["LKV_SANDBOX_TOOLCHAIN"] = str(toolchain)
        _run(
            [str(python), str(native_root / "scripts" / "wheel_smoke.py")],
            cwd=Path(temporary),
            env=smoke_env,
        )

    manifest = {
        "schema_version": 1,
        "lean_version": "4.23.0",
        "lean_binary_sha256": args.toolchain_sha256.lower(),
        "release_tools": actual_tools,
        "source_date_epoch": SOURCE_DATE_EPOCH,
        "wheels": {wheel.name: _sha256(wheel) for wheel in wheels},
    }
    manifest_path = output / "release-manifest.json"
    with manifest_path.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
