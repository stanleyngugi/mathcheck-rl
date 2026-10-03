# Source audit validation — 2026-10-03

This record concerns the audited source revision and its direct-to-main changes.
It is separate from the immutable public RL 0.2.1 / Hub 0.1.1 release evidence.
No replacement release or Hub version was published in this audit.

## Changes and local results

- Engine classifies wrapper exits 124/125, signals, unexpected exit codes and
  process launch errors as operational failures. The RL adapter also guards
  that boundary with older compatible Engine installations.
- Verdict diagnostics are immutable. Shared verification survives consumer
  cancellation, cleans up completed work, isolates event loops and does not
  retain operational failures in its completed cache. Runtime identity enters
  the v1 cache key. Primary traces preserve checker evidence and timing.
- The article is reorganized around a bounded minimum, with precise claims
  about answer-key-free rewards, generated proofs, native trust and spec fidelity.
  Operational history is moved into `REPRODUCIBILITY.md`.
- Pilot v2 binds a feasible 280-call plan, paired confirmatory baseline and
  actual GRPO update procedure. It preserves v1 as a superseded planning record.
- Question-only GSM8K import is implemented with split roles, provenance,
  explicit review and exclusions. Four development contracts and one known
  public test demonstration are frozen; independent fidelity review remains open.

Python 3.12.14, real Verifiers 0.3.0 and Datasets 4.8.5:

| Check | Result |
| --- | --- |
| RL source suite | 149 passed, 14 skipped |
| Engine source suite | 63 passed, 10 skipped, 38 subtests passed |
| Procedural Python-only control profile | 29 controls; native evidence false |
| GSM8K Python-only controls | 8 development and 2 demonstration controls; native evidence false |
| Wheel builds | All four source wheels built with fixed source-date epoch |
| Installed wheel smoke | Imported all four packages outside source trees; real v1 invalid-input scoring preserved zero reward, metadata and zero checker invocations |
| Diff hygiene | `git diff --check` passed |
| Website render | Both articles match source hashes; headings/anchors, links, metadata and XML feeds checked |

Wheel builds used build 1.6.0, hatchling 1.32.0, setuptools 84.0.0 and wheel
0.48.0. The installed smoke used `--no-deps` with an existing dependency target;
it is not a fresh dependency-resolution or native release-gate claim. Artifact
versions are unchanged because these are unpublished source builds. Published
Hub dependencies still point to their previous immutable release commits.

## Runtime limits and remaining gates

Lean is not installed in this workspace. A direct bubblewrap capability probe
failed with `Can't read /proc/sys/kernel/overflowuid: No such file or directory`.
There was no fallback to unisolated reward execution. The skipped tests include
live native/platform integrations; they must be run on a supported Linux worker
with separately installed Lean 4.23.0 before claiming current native validation.

Earlier GitHub Actions jobs were prevented from starting by an account billing
lock. Fixing source CI configuration cannot resolve that account condition.
The Engine workflow now exports `LEAN_BIN` in the same step as pytest; previously
writing only to `GITHUB_ENV` did not expose it to that step's test process.

Remaining work that requires unavailable runtime or owner-dependent facts:

1. Run both complete native suites, the six-control quickstart and the Python/Lean
   profiler on a working isolated runtime. Exit-1 infrastructure classification
   remains a documented limit.
2. Bump candidate artifact versions and update immutable package pins, then run
   the full locked release gate and consumer installation before publication.
   Do not overwrite existing release assets with these source wheels.
3. Freeze actual pilot model/checkpoint, trainer/config, pricing, quota and
   benchmark-completion evidence; verify a real policy update before launch.
   No provider calls, training, credential changes or other benchmark changes
   were made in this audit.
4. Independently review the GSM8K interpretations, then run native controls.
   No full-dataset coverage, independent review or learning-gain claim is made.

These are execution gates, not completed results. The checked-in protocol and
commands make the remaining work concrete without inventing their inputs.
