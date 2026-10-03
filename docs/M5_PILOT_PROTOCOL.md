# M5 procedural pilot: protocol v2

Status: **amended offline, not started**. Identifier:
`native-verify-m5-bounded-spec-v2`.

## Amendment and scope

[V1](archive/M5_PILOT_PROTOCOL_V1.md) allocated 40 training, 80 primary and
80 confirmatory tasks under a 300-call cap. Paired baseline/final measurements
on both evaluation splits alone need 320 calls. It also left the training
procedure unspecified. V2 supersedes that plan before execution. There are no
pilot results to select or preserve.

V2 retains the 300-call, USD 20, 60-minute and zero-automatic-retry limits.
It retains the training split, families and all three seeds. It reduces both
evaluation splits to ten tasks per family and requires a frozen GRPO procedure.
The resulting 280 planned model rollouts leave 20 calls of headroom, not an
extra tuning or retry budget. Hosted trainer billing, if applicable, counts
against the spend limit too. A provider that cannot expose and bound rollout
and training costs is ineligible for this pilot.

## Splits and allocation

The primary environment is `mathcheck-rl`. The legacy sequence adapter is not
used to make the primary learning claim. Count, sum, minimum and complete
pair-count families receive equal representation.

| Split | Per family | Total | Seed | Role |
| --- | --- | --- | --- | --- |
| Training | 10 | 40 | 20260909 | Policy updates only |
| Primary | 10 | 40 | 20270909 | Paired initial/final evaluation |
| Confirmatory | 10 | 40 | 20280909 | Paired evaluation; results sealed until primary analysis final |

Ordered canonical commitments (verified by the offline builder):

- Training: `96c8f1139a37f1acd9fec83f6e61a54b60f2b02fc4fed79a2150ad52a3df90bc`
- Primary: `8984a2fb724f4d58e204a7644bc5de89cfd200ff24caa4019de182dad1740880`
- Confirmatory: `1fbd92a0bfc26bf857a4649dfa7c6e6c54bc63bab3ae64eb8b184be99bfb8120`

All 120 specifications are unique and pairwise digest-disjoint across splits.
Exact separation does not establish semantic novelty or absence from pretraining.
No evaluation prompts, candidates or verdicts enter training or checkpoint selection.

| Stage | Maximum calls |
| --- | --- |
| Initial primary evaluation | 40 |
| Initial confirmatory evaluation | 40 |
| Training: 40 groups of 3 | 120 |
| Final primary evaluation | 40 |
| Final confirmatory evaluation, if primary criteria pass | 40 |
| Total planned | 280 |

The confirmatory baseline is sampled from the frozen initial policy **before
training**, using a separate evaluator. Its results remain unread by the trainer
and primary analyst until the primary analysis is committed. The final policy
is sampled on that split only after primary criteria pass. The specifications
are public; sealing describes result handling and must be enforced operationally,
not assumed from a string in the manifest. Record the independent custodian or
access-control mechanism before launch.

## Policy update procedure

Use actual GRPO parameter updates, not repeated attempts with an unchanged API
model. Freeze the initial checkpoint, trainer source commit, full trainer config
and their SHA-256 identities. A hosted API is usable only if it provides the
required training and checkpoint provenance.

One seeded family-balanced pass visits each of the 40 training specifications
once. Each group samples three completions from the current policy. All three
receive the binary complete-specification reward. One optimizer step per group
uses the pinned trainer's GRPO objective, within-group advantages and KL
regularization against the frozen initial policy. There are at most 40 optimizer
steps. For a zero-variance reward group, record all rollouts and skip the
zero-advantage update; do not invent shaping rewards or resample the group.

Freeze learning rate, KL coefficient, optimizer settings, clipping, precision,
LoRA/full-tuning choice, sampling and random seeds in the full trainer config.
The builder binds its digest; it does not certify the contents or supply a
trainer implementation. Resolve the model and trainer first, inspect the pinned
implementation, and verify a local update/weight-change smoke before allocating
provider quota. Initial and final checkpoint identities must appear in records.
The final checkpoint is the only selected policy; evaluation cannot select it.

Use one completion per evaluation task, with identical decoding settings for
initial and final policies. No tools, feedback-driven retries, or answer labels
are added to evaluation. The initial checkpoint is the baseline. Python/Lean
control sweeps test the grading instrument separately; they are not policy baselines.

## Preconditions and frozen identities

Before the first billed call, record:

- completion of the other benchmark and available quota;
- credential cutover, following `SECURITY_CUTOVER.md`;
- reviewed exact Engine and RL commits on `main`, with no unrelated changes;
- versioned wheels passing `scripts/release_gate.py` using a separately owned,
  read-only Lean 4.23.0 distribution and expected binary digest;
- provider, immutable model/checkpoint identity, trainer source/config identity,
  sampling, prices and worst-case cost bound;
- the confirmatory result custodian and local update/weight-change smoke.

The current owner-dependent fields are **UNSET**. No model or price is invented
in this amendment. `scripts/prepare_m5_manifest.py --training-plan ...` rejects
unset runtime identities, invalid training-plan values, altered commitments,
overlap, mismatched release evidence and an infeasible allocation. It produces
an offline preregistration, not a launch authorization or a running trainer.

## Measurement and stopping

Preserve a durable manifest, every rollout (including errors), checker evidence,
policy/checkpoint identity, optimizer-step count, tokens, cost, latency and
terminal reason. Count every dispatched rollout and failed provider request.
Stop at the first call, USD 20 or 60-minute limit; automatic retries are zero.
Do not borrow another benchmark's quota. A run stopped at a limit is incomplete,
not a failed or successful learning result.

Report per-family and overall pass rate, paired wrong-to-right/right-to-wrong
transitions, invalid-input rate and operational-error rate for both policies.
Operational failure remains zero reward; report it separately and do not delete
it from the primary denominator. A sensitivity view conditional on healthy
checking may be labeled separately. With only 40 tasks per split, estimates
are noisy; thresholds are exploratory go/no-go rules, not a powered general
reasoning claim.

The pilot is promising only if primary gain is at least 10 percentage points,
invalid-input rate increases by no more than 5 points, operational-error rate
is at most 1%, and the paired confirmatory gain is strictly positive. If an
integrity check fails or primary criteria are missed, stop without scaling.
Commit the primary analysis before opening confirmatory results. Any subsequent
protocol change receives a new version before new calls. A successful pilot
supports analysis; it does not establish broad mathematical transfer.
