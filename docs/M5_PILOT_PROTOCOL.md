# M5 pilot pre-registration

Status: **prepared, not authorized to execute while the other benchmark is active**.

## Preconditions

All conditions must be recorded before the first provider call:

- the active benchmark has finished and its owner confirms quota is available;
- credential cutover in `SECURITY_CUTOVER.md` is complete;
- reviewed verifier and native commits are merged without unrelated changes;
- versioned wheels pass `scripts/release_gate.py` against a separately owned,
  read-only Lean 4.23.0 toolchain with the expected binary digest;
- exact provider, model ID/revision, trainer version, and sampling parameters are
  filled into this document and committed;
- no evaluation candidate or checker result is fed into training.

After those facts and the runtime choices are known, create the preregistration
with `scripts/prepare_m5_manifest.py`. The command is offline and writes its
output with exclusive-create semantics. It rejects `UNSET` runtime fields,
non-full commit IDs, a mismatched release-manifest digest, altered split
commitments, duplicate/overlapping specifications, or a missing benchmark
completion reference. Creating this manifest does not authorize or launch M5.

## Frozen task protocol

- Primary environment: `mathcheck-rl`; the legacy sequence environment is
  diagnostic only.
- Families: bounded count, sum, minimum, and complete pair count.
- Training split: 10 tasks per family, seed `20260909` (40 total).
- Evaluation split: 20 tasks per family, seed `20270909` (80 total).
- A second confirmatory split uses seed `20280909` and is opened only after the
  primary analysis is final.
- Ordered canonical split commitments are:
  - training: `96c8f1139a37f1acd9fec83f6e61a54b60f2b02fc4fed79a2150ad52a3df90bc`;
  - primary evaluation: `34148fde00892e68abac3997856ba49f9a003e8ac5547e95820af3555cdd1249`;
  - confirmatory: `e0a208362d56742c1703be5d5ac02dd30d38db757e9d2da24c1246d5fb7a9a28`.
- All 200 specifications are unique within their split and the three sets are
  pairwise digest-disjoint. The run manifest must include the ordered members
  and reproduce these commitments before any call.
- Pre- and post-training evaluation use the same 80 tasks, one rollout each,
  identical decoding settings, and no retries.
- Training may use at most three attempts per task; every attempt is retained in
  durable trial and terminal records.

## Hard resource limits

- Maximum provider calls: 300 total, including pre/post evaluation and failures.
- Maximum provider spend: USD 20 equivalent.
- Maximum wall-clock duration: 60 minutes.
- Stop immediately at the first reached limit; do not borrow quota from another
  benchmark or silently retry infrastructure failures.

## Success and stopping rules

The pilot is promising only if all of the following hold:

- post-training primary pass rate improves by at least 10 percentage points;
- improvement is not explained solely by repeated or overlapping specifications;
- invalid-input rate does not rise by more than 5 percentage points;
- operational-error rate is at most 1%; any operational error remains zero reward
  and is reported separately from mathematical rejection;
- the unopened confirmatory split shows improvement in the same direction.

Stop without scaling if any integrity check fails, if the hard budget is reached,
or if the primary threshold is missed. A successful pilot authorizes analysis,
not production deployment or a larger training run.

## Fields that must be frozen before execution

- Provider: `UNSET`
- Exact model ID/revision: `UNSET`
- Trainer/runtime version: `UNSET`
- Temperature/top-p/token limit: `UNSET`
- Currency conversion source, if needed: `UNSET`
- Reviewed merge commits: `UNSET`
- Wheel and Lean hashes: `UNSET`
- Benchmark completion reference: `UNSET`
