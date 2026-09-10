import pytest

from native_verify.security import RemoteCredentialStatus, classify_remote_url


@pytest.mark.parametrize(
    "remote",
    [
        "https://github.com/example/project.git",
        "ssh://git@github.com/example/project.git",
        "git+ssh://git@github.com/example/project.git",
        "git@github.com:example/project.git",
    ],
)
def test_credential_free_remote_is_clean(remote):
    assert classify_remote_url(remote) is RemoteCredentialStatus.CLEAN


@pytest.mark.parametrize(
    "remote",
    [
        "https://token@github.com/example/project.git",
        "https://user:secret@github.com/example/project.git",
        "ssh://git:secret@github.com/example/project.git",
    ],
)
def test_embedded_remote_credential_is_rejected(remote):
    assert classify_remote_url(remote) is RemoteCredentialStatus.EMBEDDED


@pytest.mark.parametrize(
    "remote",
    [
        None,
        "",
        "../project",
        "C:/project",
        "file:///tmp/project",
        "https://",
        "https://github.com:invalid/project.git",
    ],
)
def test_missing_or_unsupported_remote_fails_closed(remote):
    assert classify_remote_url(remote) is RemoteCredentialStatus.UNSUPPORTED


def test_classifier_result_never_contains_input():
    secret = "never-echo-this-value"
    status = classify_remote_url(f"https://user:{secret}@example.com/project.git")
    assert secret not in status.value
