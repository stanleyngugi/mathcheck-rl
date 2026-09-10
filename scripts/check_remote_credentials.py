"""Check origin for embedded credentials without printing the URL."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

from native_verify.security import RemoteCredentialStatus, classify_remote_url


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only, redaction-safe origin credential check"
    )
    parser.add_argument("--repository", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=args.repository.resolve(),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        print("origin credential check: unsupported_or_missing")
        return 3
    status = classify_remote_url(result.stdout)
    print(f"origin credential check: {status.value}")
    if status is RemoteCredentialStatus.CLEAN:
        return 0
    if status is RemoteCredentialStatus.EMBEDDED:
        return 2
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
