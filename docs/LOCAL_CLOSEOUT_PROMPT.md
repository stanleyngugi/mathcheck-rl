# Local agent prompt: validate and publish the existing candidates

Finish the MathCheck closeout on my local machine. Do the engineering work
yourself, including provisioning a persistent Linux guest if necessary. I will
enter account credentials in my own browser or a supported CLI login flow.
Do not ask me to paste passwords, authentication codes or API keys into chat.

Repositories:

- https://github.com/stanleyngugi/mathcheck-engine
- https://github.com/stanleyngugi/mathcheck-rl

## 1. Pull and preserve current work

Locate existing checkouts, inspect their status and remotes, fetch current
`main`, and fast-forward clean checkouts. Clone missing repositories as sibling
directories. Preserve uncommitted work and other agents' commits; use a separate
checkout if necessary. Do not reset or force-push. Read `AGENTS.md` if present.

Read Engine `CURRENT_VALIDATION.md`, `README.md`, `CAPABILITIES.md`, package
metadata, tests and CI. Read RL `docs/CURRENT_VALIDATION.md`, `docs/FINISH_LINE.md`,
`docs/CANDIDATE_PUBLICATION.md`, `requirements-release.lock`, the Hub package
metadata, `scripts/closeout_gate.py`, `scripts/release_gate.py`,
`scripts/wheel_smoke.py` and `.github/workflows/release-candidate.yml`.
Inspect changes since these immutable dependency commits:

- Engine: `dce2fc88cee1e98ed3136ac89a4b40eba0d1ada7`.
- RL core: `d7158c411f0e00122f86bbd56949839b86284923`.

Later documentation/evidence commits do not by themselves require repinning.
If implementation or package metadata differs, bind the Hub to the appropriate
immutable implementation commits before rebuilding and joint validation.

## 2. Keep the scope finite

Complete validation, necessary narrow fixes, evidence, releases and Prime Hub
publication. The candidates are Engine 0.3.3; RL core/sequence 0.2.2; Hub 0.1.2.
Verify their actual current publication status before creating anything.
Do not reopen blogs, add features or mathematical contracts, expand datasets,
or run model inference/training. Training results are not a completion gate.
Push authorized fixes and evidence directly to GitHub; do not create more PRs.

Preserve the completed diagnostic classifier, nested duplicate-key rejection,
shared sweep classifier, parser/reward/cache fixes and documented trust boundary.
Recheck them; do not rewrite them without a reproduced defect.

## 3. Provision genuine Linux execution

Use supported Linux with real `/proc`, working bubblewrap/prlimit and namespaces,
Python 3.12, and stock Lean **4.23.0 exactly**. Run validation as an unprivileged
user with a separately owned, read-only standalone Lean distribution.
Do not disable isolation, patch the compiler, or count required skips as passes.
The current bounded checkers do not require Mathlib.

If this host is Windows, WSL can remain removed. Use a persistent Linux VM.
The documented Microsoft Quicksand/QEMU route supports Windows without WSL;
prefer hardware acceleration if available, with TCG as a software fallback.
Install from official sources, verify the real platform image and record its
digest. The small PyPI image stub is not a bootable image. Read the later Engine
`validation/2026-10-04-linux-attempt/VM_PREFLIGHT_FOLLOWUP.md`: Ubuntu boot, real
Lean startup and an unprivileged bubblewrap probe were observed, but the full
gate was not completed. Retain the local VM and export evidence progressively.

GitHub Actions previously started zero steps because of an account billing lock.
Do not rely on an unchanged locked runner or stop because Windows lacks Linux
namespaces. Provision the Linux guest locally. If elevated OS setup requires
me, ask for that specific step and continue other work. Do not purchase cloud
compute or change billing/security settings without explicit authorization.

## 4. Run the unchanged source/artifact/native gate

Inside Linux, create a dedicated validation environment. Install
`requirements-release.lock`, then both source projects without re-resolving
dependencies. Follow the repository's ownership/setup instructions.
Run from the RL checkout, using a new output directory:

```sh
python scripts/closeout_gate.py \
  --verifier-root ../mathcheck-engine \
  --toolchain /absolute/path/to/read-only-lean-4.23.0-linux \
  --toolchain-sha256 cbf5fd536e142ef1beaccf33f788fd8a7f3f29fb214e75c11319a8d8677b4b2b \
  --output artifacts/native-closeout-local
```

That digest is the recorded official Linux x86_64 Lean binary. Independently
verify it and the archive provenance; use the genuine distribution's verified
digest if validating another supported architecture, recording the difference.
The recorded Linux x86_64 archive digest is
`ecd028d6f642b61b451c8687aeeb24dd53789fbfdcb7d4adb8f5cf60eb2022ba`.

Require exit 0, `native_validation_complete=true`, `release_ready=true`, both
full live suites and no required native skips. Review logs, not only summary
booleans. The gate covers six quickstart controls, procedural and dataset
differentials, four wheels, fresh installed consumers and the native release
smoke. Confirm valid/invalid evaluation, count, sum, minimum (including feasible
but nonminimal candidate 52), complete/incomplete pair certificates, exact
mathematical rejection versus operational failure, timeout behavior, nested
duplicate JSON rejection, and filesystem/environment/network isolation through
the installed CLI. Historical/source-only results are not current native proof.

If a defect appears, fix it narrowly, update immutable pins if necessary,
and rerun affected checks plus the complete final gate. Keep actual timeouts;
do not relax them merely to obtain a pass under slow emulation.
Build twice with the locked tools and `SOURCE_DATE_EPOCH=1704067200`; compare
the four wheel hashes. Preserve manifests, logs, skips, source SHAs, toolchain
provenance, hashes and fresh consumer `pip check`. Supplemental sdists are not
an established required release asset; do not expand the closeout around them.

## 5. Authenticate locally and publish only validated artifacts

Use existing authorized GitHub/Prime credentials. For Prime, inspect the current
CLI's supported login flow and open my ordinary local browser for Google sign-in
so I can type myself. The assistant cloud browser returned Google 502; do not
reuse it. A browser session is not automatically CLI authentication. Complete
the documented browser/device callback and verify CLI owner access to
`stanley-ngugi/mathcheck-rl`. If a new API key is required, explain its permissions
and let me create/store it using the service's normal secure flow. Never print,
commit or place credentials in guest images, artifacts or logs. Do not publish
under a new or wrong Google/Prime account.

Only after the native gate passes, follow the established GitHub release pattern:
Engine `v0.3.3` gets its validated wheel; RL `v0.2.2` gets its validated core,
sequence and Hub wheels. Attach the manifests and current validation evidence,
with tags bound to exact source commits. Check for existing releases first;
do not overwrite published versions or move tags. The historical process uses
GitHub wheels/manifests; no required PyPI step was established. Check current
repository instructions before assuming a registry upload is needed.

From `environments/mathcheck_rl`, push Hub **0.1.2** with the current Prime CLI,
without automatic version bumping. Verify visibility, v1 runtime, version and
immutable Engine/core dependencies. Never publish based on a GitHub push alone.

## 6. Verify the published consumer, record, and stop

Install `stanley-ngugi/mathcheck-rl@0.1.2` from Prime into a fresh environment
outside both source trees. Run `pip check`; inspect installed versions,
`direct_url.json` commit identities and packaged source hashes. Repeat known
valid and invalid checks through the installed Verifiers framework using the
same healthy isolated Lean toolchain. Record the actual Prime-built wheel hash
if it differs from the locally built wheel. Download GitHub assets and compare
their hashes too. Hub visibility alone does not prove native execution.

Commit and push concise final evidence in the repositories' current validation
documents. Report final source commits, native pass/fail counts and any remaining
skips, artifact hashes, GitHub release links, Prime 0.1.2 identity, installed
consumer results and pin changes. Preserve access blockers precisely if any
remain; do not claim publication or completion without checking the result.

**Done means the final native gate passes, validated distributions are published,
Prime 0.1.2 is independently installed and checked, and evidence is pushed. Then
stop. No training, blog rewrite or further feature work is required.**
