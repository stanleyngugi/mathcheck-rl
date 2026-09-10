"""Redaction-safe checks used during the post-benchmark Git cutover."""
from __future__ import annotations

from enum import Enum
import re
from urllib.parse import urlsplit


class RemoteCredentialStatus(str, Enum):
    CLEAN = "clean_credential_free"
    EMBEDDED = "embedded_credentials"
    UNSUPPORTED = "unsupported_or_missing"


_SCP_REMOTE_RE = re.compile(
    r"(?P<user>[A-Za-z0-9_.-]+)@(?P<host>[A-Za-z0-9.-]+):(?P<path>[^\s]+)"
)


def classify_remote_url(remote_url: object) -> RemoteCredentialStatus:
    """Classify a remote without returning or logging any part of its value."""
    if not isinstance(remote_url, str) or not remote_url.strip():
        return RemoteCredentialStatus.UNSUPPORTED
    value = remote_url.strip()
    if _SCP_REMOTE_RE.fullmatch(value):
        return RemoteCredentialStatus.CLEAN
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError:
        return RemoteCredentialStatus.UNSUPPORTED
    if parsed.scheme in {"http", "https"}:
        if not parsed.hostname:
            return RemoteCredentialStatus.UNSUPPORTED
        if parsed.username is not None or parsed.password is not None:
            return RemoteCredentialStatus.EMBEDDED
        return RemoteCredentialStatus.CLEAN
    if parsed.scheme in {"ssh", "git", "git+ssh"}:
        if not parsed.hostname:
            return RemoteCredentialStatus.UNSUPPORTED
        if parsed.password is not None:
            return RemoteCredentialStatus.EMBEDDED
        return RemoteCredentialStatus.CLEAN
    return RemoteCredentialStatus.UNSUPPORTED
