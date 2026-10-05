# Local closeout handoff — 2026-10-04

The later Engine
[guest preflight follow-up](https://github.com/stanleyngugi/mathcheck-engine/blob/af26078be4a316f29be8b10cdc17d30ea1651cab/validation/2026-10-04-linux-attempt/VM_PREFLIGHT_FOLLOWUP.md)
records a successful official Ubuntu image download, guest boot, stock Lean
4.23.0 startup, and unprivileged bubblewrap namespace probe. These observations
are transcribed from execution tool results. The transient worker was replaced
before a full gate or guest-file export; D6 and all candidate publication gates
remain unfinished. They are not native mathematical acceptance/rejection evidence.

Prime's secure method-choice prompt worked, but Google returned 502 / connection
refused before loading its credential form. Owner authentication is unconfirmed.
The [local-agent prompt](LOCAL_CLOSEOUT_PROMPT.md) covers persistent Linux
execution, user-entered local authentication, complete native validation,
GitHub/Prime publication and independent installed-consumer verification.

GitHub releases were rechecked on 2026-10-04: Engine 0.3.2 and RL 0.2.1 remain
the latest published releases in their respective repositories. No Engine
0.3.3 or RL 0.2.2 release was present. The earlier public Prime observation
below has not been refreshed during this authentication handoff.
These updates change documentation only. The existing immutable Engine/core
pins still match the current runtime files and package metadata.

---

# Initial execution-route follow-up — 2026-10-04

The [fresh Engine evidence](https://github.com/stanleyngugi/mathcheck-engine/blob/b28424dc1587d8a6ef83d0a83965277d725ec69e/validation/2026-10-04-linux-attempt/README.md)
reproduces 85 source passes and 40 subtests, byte-identical candidate wheels,
and fresh installed-wheel controls. All ten required Engine live entries were
attempted with the official hashed Lean 4.23.0 distribution, but no native gate
cleared: the worker lacks `/proc`, stock Lean cannot locate its application,
and bubblewrap fails. These are operational limitations, not native rejection
evidence. No runtime or package metadata changed; immutable candidate pins stay
unchanged.

A [subsequent QEMU attempt](https://github.com/stanleyngugi/mathcheck-engine/blob/b28424dc1587d8a6ef83d0a83965277d725ec69e/validation/2026-10-04-linux-attempt/VM_ATTEMPT.md)
successfully initializes a paused TCG process. Its Ubuntu guest image could not
be downloaded, so no guest boot or joint native pass is claimed. The latest
Engine Actions run also has zero steps and no runner. The
[publication guide](CANDIDATE_PUBLICATION.md) now gives a documented Windows
Quicksand/QEMU route without WSL and corrects doubled shell continuation slashes
in the existing closeout command. Shell syntax, actual closeout-command argv,
and the guest-preflight Python syntax were checked; that guest snippet is not
reported as executed.

Prime CLI 0.9.2 is installed in a separate worker environment. Public Hub reads
work after adding its proxy dependency. A fresh public `pyproject.toml` inspection
confirms latest is **0.1.1**, pinned to Engine `742edec6bdb4f7057780fc54e98fb284b76eedcf`
and core `d4912c30564e99a3200f77ca7e94a8a3ebe184c7`; requesting **0.1.2** returns
HTTP 404. [Actual CLI records](evidence/remaining-execution-20261004/prime-public-status.json)
and [documentation checks](evidence/remaining-execution-20261004/documentation-checks.json)
are retained. No Prime API key is configured, and the browser shows Sign In.
No upload or release publication was attempted. D6 and authenticated owner
publication access remain required; no training or expanded mathematics is needed.

---

# Candidate source validation and audit closeout — 2026-10-03

**Source delivery is complete. Current native validation remains blocked.
RL training results are optional and are not a completion requirement.**
The finite criteria and one-command gate are in [FINISH_LINE.md](FINISH_LINE.md).
The latest follow-up records **178 RL tests and 85 Engine tests plus 40 subtests**.
Its [source/artifact closeout report](evidence/engine-integration-20261003/closeout.json)
passes with native validation blocked. The earlier tables below preserve the
previous checkpoint; the final section records the updated immutable pins.

The audited work is pushed directly to `main`. Candidate versions are Engine
**0.3.3**, RL core/sequence **0.2.2**, and Hub **0.1.2**. No replacement release
or Hub version has been published. Existing public 0.3.2 / 0.2.1 / 0.1.1
assets and their historical evidence remain unchanged.

## Implementation

- Engine and RL preserve the operational-failure boundary for wrapper exits,
  signals, timeouts and process launch errors. Shared verification survives
  consumer cancellation, isolates event loops and does not cache operational
  failures. Immutable verdict diagnostics and primary trace metadata retain
  checker status, digests, invocations and timing.
- The article is framed around grading frozen mathematical specifications
  without precomputed candidate keys. It distinguishes Python computation,
  Lean native verification, proof synthesis and prose-to-specification fidelity.
- Pilot v2 has a feasible 280-completion allocation. The optional local
  Transformers driver now samples actual policy completions, applies binary
  GRPO updates, preserves a frozen reference, saves checkpoints and performs
  paired evaluation. Config/checkpoint/source/release identities are checked.
  Evaluation verdicts never enter optimizer updates. Zero-variance groups are
  skipped; operational errors abort; primary analysis is finalized before
  confirmatory scores are opened. See [LOCAL_TRAINING.md](LOCAL_TRAINING.md).
- GSM8K question-only import now freezes three development specifications and
  one known public-test demonstration, with two explicit exclusions. The final
  semantic audit found an unstated friends-to-clips quantity correspondence in
  train:0 and removed its earlier contract. Same-context review is disclosed in
  [GSM8K_SPEC_AUDIT.md](GSM8K_SPEC_AUDIT.md); no independent evaluation is claimed.
- A manual **Native release candidate gate** workflow prepares a supported
  Linux worker, runs both complete suites, procedural/dataset native controls
  and the locked four-wheel gate, then retains artifacts without publishing.

## Passing checks

Fresh Python 3.12.14 dependency resolution, Verifiers 0.3.0, Datasets 4.8.5,
PyTorch 2.8.0+cpu and Transformers 4.57.6:

| Check | Result |
| --- | --- |
| RL complete source suite with optional training dependencies | 173 passed, 14 live/platform skips |
| Engine source suite | 63 passed, 10 live/platform skips, 38 subtests passed |
| Optional gradient/checkpoint/orchestration controls | 18 passed; included in the RL total above; not a mandatory training-result gate |
| Finite closeout status/artifact regressions | 6 passed; included in the RL total above |
| Real Transformers update | Tiny random GPT-2 weights change, frozen reference stays unchanged, final safetensors checkpoint reloads with identical tensor digest |
| Candidate wheel builds | Engine 0.3.3, RL core/sequence 0.2.2 and Hub 0.1.2 build with fixed source-date epoch |
| Fresh consumer installation | Dependencies resolved in a new venv; candidate wheels install; `pip check` passes, including optional training dependencies |
| Independent Git-resolved Hub installation | New venv resolves Engine/core from the candidate Git pins; exact commits and packaged Python source bytes match; `pip check` and environment smoke pass |
| Installed artifact smoke outside source trees | All four imports, real v1 environment construction, invalid-input zero reward and zero checker invocations pass |
| Hygiene | Python compilation, workflow syntax/path checks and `git diff --check` pass |

The orchestration tests use explicitly labeled fixtures. They validate the
280-call schedule and stop conditions, not learning. The GPT-2 smoke validates
actual gradients and checkpoint mechanics, not mathematical improvement.
Consumer dependencies are recorded in
[evidence/candidate-consumer-packages-20261003.txt](evidence/candidate-consumer-packages-20261003.txt).
The Hub wheel is installed with `--no-deps` after the exact locally built
Engine/core/sequence wheels have been resolved and installed, matching the
release gate's artifact installation strategy. A second fresh environment independently resolves the immutable Git
dependencies without those local dependency wheels. Exact installed commit IDs
and packaged Python bytes are verified in
[evidence/git-consumer-20261003.json](evidence/git-consumer-20261003.json).
Candidate wheel hashes are recorded in
[evidence/candidate-wheels-20261003.json](evidence/candidate-wheels-20261003.json);
that earlier build record is historical and is not a successful release-gate
manifest. Current wheel hashes are in the latest closeout report.

## Native attempts: blocked, not passed

Lean 4.23.0 is installed from the official Linux release. The verified archive
SHA-256 is `ecd028d6f642b61b451c8687aeeb24dd53789fbfdcb7d4adb8f5cf60eb2022ba`;
the installed binary SHA-256 is
`cbf5fd536e142ef1beaccf33f788fd8a7f3f29fb214e75c11319a8d8677b4b2b`.
Even with the stock shared-library paths configured, `lean --version` exits 1
with `error: failed to locate application`. Lean's Linux application-path
lookup needs `/proc/<pid>/exe`; this workspace does not provide it. Bubblewrap
also fails because `/proc/sys/kernel/overflowuid` is absent. Mathlib is not
required for the present bounded checkers and cannot repair these OS limits.

| Attempt | Observed result |
| --- | --- |
| Six-control quickstart | All 6 operational errors |
| Procedural Python/Lean profile | All 29 native attempts operational errors |
| Earlier GSM8K four-contract development controls | All 8 native attempts operational errors; source slice superseded by the final semantic audit |
| GSM8K public-test demonstration | Both native attempts operational errors |
| Full release gate | Stops at stock `lean --version`, before its build/install/native smoke |

[evidence/native-attempt-20261003.json](evidence/native-attempt-20261003.json)
records these attempts with `native_evidence_complete=false`. Zero recorded
mathematical disagreements in an all-operational-error run supplies no agreement
evidence. No unisolated reward fallback or weakened gate was introduced.
Earlier Actions runs were prevented from starting by a GitHub billing lock;
source workflow changes cannot resolve that account condition. The recorded
candidate CI jobs also fail with zero steps started:
[Engine](https://github.com/stanleyngugi/mathcheck-engine/actions/runs/37114767685)
and [RL](https://github.com/stanleyngugi/mathcheck-rl/actions/runs/37115380434).
Their current failure reason was not exposed by the available job metadata;
no native CI pass is claimed.

## Finite remaining gate and optional work

The single remaining required validation gate is D6: execute the closeout
command on supported Linux and pass its native checklist and installed-wheel
release gate. Then publish requested candidate distributions. The latest run
passes source suites, wheel builds, fresh dependency resolution and installed
structural smoke, then records stock Lean startup as blocked with exit 2.
It makes no native acceptance claim.

The following do not keep this delivery open: choosing a pretrained model,
freezing an experimental configuration, obtaining benchmark-completion evidence,
launching a procedural learning pilot, measuring gains, automatic formalization
or expanding dataset coverage. They belong to a separately requested experiment.
The optional driver/protocol remain implemented and have their smoke evidence.

The bounded GSM8K demonstration is complete as a disclosed same-context manual
interpretation. Its current development slice has six Python-only candidate
controls, with no native claim. Independent fidelity review remains required
before a future independent dataset-evaluation claim, not before closing this
small demonstration. Earlier records remain historical and are not relabeled.

Credential revocation/cutover remains unconfirmed owner-controlled account work;
no secret, quota or benchmark changes are made by the closeout command. At this
earlier checkpoint, website publication remained with the owner; the follow-up
below records the article synchronization.

At this earlier checkpoint, design limits included unidentified infrastructure
failures returning exit 1, trusted expression translation, process-local rather than independent
confirmatory custody, and production isolation beyond per-process limits.
At that checkpoint, the website was left for the owner to update separately.

## Engine integration follow-up — 2026-10-03

This section supersedes the source counts and dependency identities above for
current candidate source. Earlier records remain historical.

Engine is pinned to `dce2fc88cee1e98ed3136ac89a4b40eba0d1ada7`. The Hub's RL core dependency is
`d7158c411f0e00122f86bbd56949839b86284923`; its Python source is the same core built in this gate.
Candidate versions remain Engine 0.3.3, RL core/sequence 0.2.2 and Hub 0.1.2.
No release or Hub publication occurred.

| Fresh check | Result |
| --- | --- |
| Engine source suite | 85 passed, 10 live/platform skips, 40 subtests passed |
| RL source suite, including installed optional trainer dependencies | 178 passed, 14 live/platform skips |
| Four candidate wheels | Built with the fixed source-date epoch; hashes recorded |
| Wheel Python source | All packaged Python files match their current source |
| Immutable source identities | All 23 Engine and 16 RL core Python files match the pinned Git blobs |
| Fresh consumer installation | Four wheels install; `pip check` passes |
| Installed framework smoke | v1 environment construction and invalid-input zero reward pass outside source trees |
| Current local native gate | Blocked: this worker lacks `/proc`; stock Lean is not on PATH and bubblewrap fails its capability probe |

The unmodified closeout report and its logs are in
[evidence/engine-integration-20261003/closeout.json](evidence/engine-integration-20261003/closeout.json).
Its exit is **2**, with source delivery complete, native validation incomplete
and release readiness false. No native toolchain was supplied to that source/artifact
run; the separately recorded platform probe explains why this worker cannot
provide D6. Wheel/source comparisons and the platform probe are retained beside
that report. Installed wheels were used in the consumer gate; this follow-up does
not claim a new remote Git-resolved consumer installation.

The remaining exit-1 ambiguity is now handled conservatively: mathematical
rejection requires complete recognized Lean native false-decision diagnostics.
Unknown, truncated or mixed output is operational. The classifier scans lines
without nested multiline regex backtracking. Engine's JSON CLI now rejects
repeated keys at every object depth, matching the RL candidate parser's policy.
Structured and legacy RL paths preserve the revised negative-decision boundary.
Specification serialization, arithmetic semantics and result fields did not change.

Ordinary RL CI now checks out its immutable Engine dependency. The existing
**Native release candidate gate** also runs when Hub dependency metadata changes
on `main`, as well as manually. That Linux workflow runs D6 without publishing
or training. Its outcome must be inspected independently; a scheduled job is not
a successful gate. Training, autoformalization and broader mathematics remain
outside the required delivery.

The dependency update triggered the current Linux native workflow, but
[run 37130137846](https://github.com/stanleyngugi/mathcheck-rl/actions/runs/37130137846)
concluded failure with **zero steps and no assigned runner**. The associated RL
CI run and current Engine CI run also concluded failure with zero steps. The
inspected job metadata does not expose the reason; the historical billing lock
is not assumed to explain these new runs. The compact
[Actions observation](evidence/engine-integration-20261003/github-actions.json)
records those outcomes. None is a native test pass or a failed mathematical control.

Both website articles were synchronized verbatim from the audited repository
sources in [website commit 05a9960](https://github.com/stanleyngugi/website-1/commit/05a9960aa63d64352c0803d949e34f41619e8691).
The site renderer now supports display formulas through native MathML, with
scrollable formula regions on narrow screens. Source hashes, links, anchors
and deterministic rendering were checked before the website commit.


## Native retry and Hub publication boundary — 2026-10-03

The requested native retry was executed as attempt **2** of
[run 37130137846](https://github.com/stanleyngugi/mathcheck-rl/actions/runs/37130137846).
It again completed with zero steps and no assigned runner. The signed-in GitHub
run summary now provides the reason: **the account is locked due to a billing
issue**. This confirms the current retry's cause; the earlier metadata-only
observations remain historical. The billing/account condition was not changed.

The current worker still has no `/proc`, no Lean executable on PATH and a failing
bubblewrap probe. No current native acceptance was established. Prime Hub was
also inspected directly: latest is **0.1.1**, still pinned to Engine
`742edec6bdb4f7057780fc54e98fb284b76eedcf` and core
`d4912c30564e99a3200f77ca7e94a8a3ebe184c7`. The browser was not signed in to Prime,
and this worker had no configured `PRIME_API_KEY`.

The [retry observation](evidence/native-closeout-retry-20261003.json) retains these
facts. [CANDIDATE_PUBLICATION.md](CANDIDATE_PUBLICATION.md) specifies the finite
native gate, Hub 0.1.2 upload and independent installed-version checks. No new
release or Hub upload occurred: D6 remains required before publication.

## Title continuity and final native gate attempt — 2026-10-03

The article is now **Grading Mathematical Answers Without Answer Keys**. Its
Markdown path and published `/posts/mathcheck-rl.html` URL are unchanged.
[Website commit 2fc858f](https://github.com/stanleyngugi/website-1/commit/2fc858f18d66552ad308217d45bf97e105e3087a)
updates the page, homepage, RSS title and citation, and shows the former title
for readers following previously submitted resumes. Publication dates and the
RSS permalink are preserved. Source identity, generated metadata, anchors,
local links and deterministic rendering pass. Upstream website merging and
deployment remain with the owner.

The unchanged native closeout gate now also triggers when its own workflow
configuration changes. The title/workflow commit
`15c33b19470fad151a9f3039d616550cac448d8f` triggered
[run 37149622162](https://github.com/stanleyngugi/mathcheck-rl/actions/runs/37149622162).
The initial attempt and one explicit retry both concluded failure with **zero
steps executed, runner ID 0 and no assigned runner**. No tests, mathematical
controls or artifact gate ran. The inspected metadata does not expose the
failure reason; no current billing cause is inferred.

The local capability probe again finds bubblewrap 0.9.0 unable to read
`/proc/sys/kernel/overflowuid`; stock Lean is not on PATH. This is a platform
probe, not a new Lean installation or native test result. No fallback,
isolation bypass, account change or weakened reward was introduced.

[evidence/native-gate-retry-20261003.json](evidence/native-gate-retry-20261003.json)
records both Actions attempts and the local probe. **D6 remains blocked;
source delivery is complete and release readiness remains false.** The finite
remaining action is runner availability followed by one passing execution of
the existing native closeout gate. Training and broader features remain
outside the completion criteria.

## Local closeout and publication hold — 2026-10-05

The user-owned Windows machine has no WSL distribution, SSH Linux target, or
hardware virtualization available. A persistent Ubuntu 24.04 guest was booted
with Quicksand/QEMU TCG. It runs Python 3.12.3, genuine read-only Lean 4.23.0
(binary SHA-256 `cbf5fd536e142ef1beaccf33f788fd8a7f3f29fb214e75c11319a8d8677b4b2b`),
and bubblewrap 0.9.0; the unprivileged namespace probe passes.

The unchanged joint closeout attempt built all four candidate wheels, passed
both source suites, clean consumer installation and `pip check`, installed
structural smoke, Lean startup and quickstart. The Engine live suite exceeded
the gate's fixed 900-second subprocess limit under TCG (`returncode=-1`,
900.218 seconds). The gate correctly reports `native_validation_complete=false`
and `release_ready=false`; later RL live, control and release checks did not
run. A separate verbose diagnostic run completed the full Engine suite with
real Lean: **96 passed, 52 subtests passed in 1,488.11 seconds**. This confirms
the suite can complete in the guest but still exceeds the unchanged gate's
900-second stage limit; it is not a substitute for a passing joint gate. Its
[summary](evidence/native-engine-diagnostic-20261005-tcg.json) and
[full log](evidence/native-engine-diagnostic-20261005-tcg.txt) are preserved.
A focused actual-Lean regression test for the reproduced warning-prefixed
negative-diagnostic case passes, but does not substitute for the joint gate.
No required skip is counted as a pass.

The machine has no configured existing Linux host. The local closeout prompt
forbids purchasing cloud compute without explicit authorization, so neither a
billable runner nor a publication was started. The exact gate report, candidate
wheel hashes and source script identities are preserved in
[`evidence/native-closeout-20261005-local.json`](evidence/native-closeout-20261005-local.json).
The fix is at Engine commit `fa2f04ce4a1d114f08444944dbf0898515611980`; Hub
candidate 0.1.2 pins that Engine commit and RL core
`d7158c411f0e00122f86bbd56949839b86284923`. The GitHub releases and Prime Hub
upload remain withheld until a qualifying native gate exits 0.

## Final native closeout — 2026-10-05

The unchanged joint gate subsequently passed on the persistent Ubuntu 24.04.4
guest under QEMU WHPX (`-accel whpx,kernel-irqchip=off`), using Python 3.12.3,
unprivileged user `mathcheck` (UID 1002), bubblewrap 0.9.0, and stock read-only
Lean 4.23.0. The official Lean archive and installed binary hashes, verified
VM package provenance, exact source commits, gate report, locked wheel manifest
and complete stage logs are retained in
[`evidence/native-closeout-whpx-20261005-final/`](evidence/native-closeout-whpx-20261005-final/).

The gate exited 0 in 801.238 seconds with
`native_validation_complete=true` and `release_ready=true`. Engine live tests
passed (**96 tests and 52 subtests in 424.30 seconds**). RL live tests passed
(**182 passed**); pytest skipped only optional `tests/test_grpo.py` because its
training-only PyTorch dependency was absent. Required native skips: **0**.
All source checks, quickstart controls, dataset/procedural differentials,
consumer installs, `pip check`, four wheel builds and native release gate passed.
The second locked wheel build matched all four hashes in the retained manifest.

The validated source revisions are Engine
`2556e1fec67aabb8823fed10d170df7f42ebf574` and RL
`62c988f428f35c484b1d851ffb5b5fcb130eb619`. Hub 0.1.2 retains immutable
Engine/core pins `fa2f04ce4a1d114f08444944dbf0898515611980` and
`d7158c411f0e00122f86bbd56949839b86284923`; later commits contain evidence and
documentation only. This passing WHPX result supersedes the earlier TCG timeout
and failed WHPX boot diagnostics. GitHub releases and Prime Hub publication
were completed after the gate passed. Release identities and fresh installed-
consumer checks are recorded below.

## Publication and installed-consumer closeout — 2026-10-05

The validated GitHub releases are live: [Engine 0.3.3](https://github.com/stanleyngugi/mathcheck-engine/releases/tag/v0.3.3)
is tagged at validated source `2556e1fec67aabb8823fed10d170df7f42ebf574`, and
[RL 0.2.2](https://github.com/stanleyngugi/mathcheck-rl/releases/tag/v0.2.2)
at `62c988f428f35c484b1d851ffb5b5fcb130eb619`. The published Engine, RL core,
RL sequence and Hub candidate GitHub assets were downloaded independently; all
four wheel SHA-256 values match the native gate manifest.

Prime Hub now lists public `stanley-ngugi/mathcheck-rl` version **0.1.2** as
runtime v1. Prime CLI authenticated as owner `stanley-ngugi` with environment
read/write scope and successfully published the candidate without a version
bump. Prime reports version ID `w139dmpyx1jcvdqb5pnra23n` and content hash
`d5fe188d6874826ed9f6c8eb6b3f82069bc1c99a387d021c69cbca14da345295`. The
Prime-built wheel SHA-256 is
`e6f4c3074cbfd5436ba225448023134455d12fa69533a8c8ec35a01b4a0ed231`. Prime's
packaged `mathcheck_rl.py` has SHA-256
`08a069e6272d031a70d2f83a88bffcf05f06b5cd6eb090ab852734bcef129cd3`; after
normalizing CRLF to LF, its content hash matches the locally gated wheel's
`92ab8c94599a662c91791756d470ea9ca6b3652c59e3cd35bf1c61924d66c737`. Its
metadata retains Engine pin `fa2f04ce4a1d114f08444944dbf0898515611980`,
RL core pin `d7158c411f0e00122f86bbd56949839b86284923`, and Verifiers 0.3.0.

Two clean consumer environments independently installed Prime 0.1.2. A new
Windows Python 3.11 environment installed it through `prime env install` and
passed `pip check`; installed direct-URL metadata resolved both immutable Git
pins, and installed module bytes match the published wheel. A separate fresh
Ubuntu 24.04.4/Python 3.12.3 environment installed the exact Prime-downloaded
wheel and Git-pinned dependencies, passed `pip check`, and ran the installed
framework's full six-control Lean smoke under the same isolated Lean 4.23.0
runtime. All valid, invalid and nonminimal cases returned their expected
mathematical statuses; invalid input made zero checker invocations. The installed
Engine/core module SHA-256 values match the pinned Git trees. Full identities,
asset hashes, versions, and smoke results are in
[`evidence/native-closeout-whpx-20261005-final/publication.json`](evidence/native-closeout-whpx-20261005-final/publication.json).
The raw successful Linux consumer result is retained in
[`evidence/native-closeout-whpx-20261005-final/prime-consumer-whpx.json`](evidence/native-closeout-whpx-20261005-final/prime-consumer-whpx.json).

Native validation, GitHub publication, Prime Hub publication, independent asset
hash checks, fresh package installation and installed-consumer native checks are
complete. The sole source-suite skip remains the optional PyTorch training
module; no required native check was skipped.
