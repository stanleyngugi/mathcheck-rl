# Delivery status and optional roadmap

The finite audit criteria are in [FINISH_LINE.md](docs/FINISH_LINE.md).
Source delivery is complete; current native validation remains blocked by
execution capabilities. **RL training results are optional and are not an
issue or completion requirement.** M5 and broader contracts are future work.

## M0 — isolated reproducible state

Implemented in a dedicated worktree and virtual environment. Baseline evidence:
68 verifier tests plus 38 subtests, and 44 native tests, all with actual Lean
4.23.0. The active solver benchmark checkout, environment, quota state, and
journals were not modified. Credential rotation remains an owner action; see the
defect ledger without exposing the credential.

## M1 — shared checking contracts

The existing answer-key-free scalar and complete-pair APIs remain compatible.
Results now explicitly distinguish checked success, mathematical rejection, and
operational failure. The shared runner optionally enforces an exact Lean version.

## M2 — hardened finite-program path

The sequence runner uses the shared one-shot runner and `lean-isolated`, requires
Lean 4.23.0, and has no implicit host/retired-checkout fallback. The model-code
boundary rejects indented non-`def` declarations, qualified definitions,
unterminated comments, and non-string inputs. Verdicts bind exact inputs. v0 and
v1 scoring reuse one verdict; v1 uses an exact-input single-flight cache.

## M3 — answer-key-free task type

`mathcheck-rl` derives prompts and trusted checkers from one frozen bounded
specification. Runtime reward does not store or compare an expected answer.
Positive/wrong/minimality/completeness controls execute through real Lean.

## M4 — evaluation and packaging

Generators enforce unique, digest-disjoint train/evaluation specifications.
Packages declare the shared verifier and tested framework version. Batch records
use exclusive creation, durable manifest/trial/terminal JSONL records, explicit
retry budgets, and input/source digests. All four wheels install together in a
fresh environment and pass the artifact smoke recorded in
`docs/BOUNDED_MILESTONE_VALIDATION.md`.

The public release is MathCheck RL `v0.2.1`. Its primary Verifiers v1
environment is also public on Prime Hub as `stanley-ngugi/mathcheck-rl` version
`0.1.1`. A fresh consumer installation resolved the immutable Engine 0.3.2 and
RL 0.2.1 commits and passed local subprocess setup validation. Prime-hosted
model execution is not claimed: the attempted authenticated inference path
stopped before a rollout because the account had insufficient balance, and no
solver quota was borrowed.

## M5 — optional procedural learning experiment

Protocol v2 supersedes the infeasible v1 allocation without changing its
300-call / USD 20 / 60-minute limits. It uses 40 training, 40 primary and
40 confirmatory tasks; paired evaluation consumes 160 calls and training
uses at most 120. The offline builder verifies the allocation and requires
a frozen GRPO training plan and checkpoint identity. The optional local Transformers/GRPO driver and actual-gradient/checkpoint
smoke are implemented. Execution of the learning pilot is not started.
Exact model/trainer identities, native wheel gates and benchmark-completion
evidence remain required; see `docs/M5_PILOT_PROTOCOL.md`.

## M6 — bounded answer-blind dataset demonstration

An offline GSM8K import path accepts question-only inputs and explicitly
reviewed specifications. The delivered demonstration has three development
contracts, one public-test example and two exclusions; its review is same-context
and disclosed in `docs/GSM8K_SPEC_AUDIT.md`. It binds source provenance and split roles, rejects
reference-answer fields, and records unsupported questions as exclusions.
No automatic faithful formalizer, full-dataset coverage, training result or
native dataset verification is claimed. See `docs/GSM8K_DEMONSTRATION.md`.
