# Candidate source validation — 2026-10-03

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
- GSM8K question-only import freezes four development specifications and one
  known public-test demonstration with explicit provenance and exclusions.
  Same-context review is not independent fidelity review.
- A manual **Native release candidate gate** workflow prepares a supported
  Linux worker, runs both complete suites, procedural/dataset native controls
  and the locked four-wheel gate, then retains artifacts without publishing.

## Passing checks

Fresh Python 3.12.14 dependency resolution, Verifiers 0.3.0, Datasets 4.8.5,
PyTorch 2.8.0+cpu and Transformers 4.57.6:

| Check | Result |
| --- | --- |
| RL complete source suite with optional training dependencies | 167 passed, 14 live/platform skips |
| Engine source suite | 63 passed, 10 live/platform skips, 38 subtests passed |
| Standalone gradient/checkpoint/orchestration controls | 18 passed; included in the RL total above |
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
that record is explicitly not a successful release-gate manifest.

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
| GSM8K development controls | All 8 native attempts operational errors |
| GSM8K public-test demonstration | Both native attempts operational errors |
| Full release gate | Stops at stock `lean --version`, before its build/install/native smoke |

[evidence/native-attempt-20261003.json](evidence/native-attempt-20261003.json)
records these attempts with `native_evidence_complete=false`. Zero recorded
mathematical disagreements in an all-operational-error run supplies no agreement
evidence. No unisolated reward fallback or weakened gate was introduced.
Earlier Actions runs were prevented from starting by a GitHub billing lock;
source workflow changes cannot resolve that account condition. The most recent
candidate CI jobs also fail with zero steps started:
[Engine](https://github.com/stanleyngugi/mathcheck-engine/actions/runs/37114767685)
and [RL](https://github.com/stanleyngugi/mathcheck-rl/actions/runs/37115380434).
Their current failure reason was not exposed by the available job metadata;
no native CI pass is claimed.

## Remaining execution gates

1. Run complete live suites, quickstart, profiler and full release gate on
   supported Linux. The independent Git consumer installation passes already;
   publish candidate releases/Hub only after the native artifact gate passes.
2. Freeze an actual pretrained model/checkpoint and exact config/runtime,
   genuine benchmark-completion evidence and the confirmatory access mechanism.
   Launch the procedural pilot only after native gates pass. No real M5 run,
   provider inference, quota borrowing or credential changes occurred here.
   Credential revocation/cutover remains unconfirmed owner-dependent work.
3. Obtain independent fidelity review of the GSM8K interpretations and run
   their native controls before using that extension for evaluation or training.

Remaining design limits include unidentified infrastructure failures returning
exit 1, trusted expression translation, process-local rather than independent
confirmatory custody, and production isolation beyond per-process limits.
The website is left for the owner to update separately.
