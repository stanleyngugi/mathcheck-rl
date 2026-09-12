# Credential and remote cutover gate

Status: **deferred until the active benchmark has finished**.

New API/provider credentials must live outside the repository in an operating
system credential manager or a local environment file. The repository ignores
`.env`, `.env.*`, `*.env`, common private-key extensions, and local
`secrets/`/`credentials/` directories; a sanitized `.env.example` may be
committed. Ignore rules are preventive only: they do not remove an already
tracked secret, revoke an exposed token, or apply to a credential embedded in
the repository-local `.git/config` remote URL.

The native repository's configured origin was reported to contain an embedded
credential. No command in this work inspected, printed, changed, or exercised
that remote. Revoking it while another benchmark may depend on it could disrupt
the active run.

After the benchmark owner confirms completion:

1. Revoke the exposed credential at its provider. Treat any replacement as a
   new secret; do not place it in a URL, command transcript, journal, or commit.
2. Replace the local origin with a credential-free HTTPS URL or an SSH URL.
   Authentication should come from the platform credential manager or SSH agent.
3. Validate programmatically that the configured URL contains no user-info
   component, without printing the old or new credential-bearing value. After
   replacing the URL, run
   `python scripts/check_remote_credentials.py --repository <repository>`.
   Exit 0 means a credential-free HTTPS/SSH remote, exit 2 means embedded
   credentials remain, and exit 3 means the remote is missing or unsupported.
4. Search committed content and release artifacts for the credential fingerprint
   using a redacted detector. Do not echo matching secret text.
5. Confirm the provider reports the old credential revoked before any push.
6. Push only the reviewed release-candidate commits, after the original active
   benchmark checkout is no longer in use.

This gate is intentionally an owner-coordinated cutover, not an automated action
inside the current isolated implementation task.
