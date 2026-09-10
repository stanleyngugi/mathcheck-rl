# Bounded milestone status

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

`native-verify-spec` derives prompts and trusted checkers from one frozen bounded
specification. Runtime reward does not store or compare an expected answer.
Positive/wrong/minimality/completeness controls execute through real Lean.

## M4 — evaluation and packaging

Generators enforce unique, digest-disjoint train/evaluation specifications.
Packages declare the shared verifier and tested framework version. Batch records
use exclusive creation, durable manifest/trial/terminal JSONL records, explicit
retry budgets, and input/source digests. All four wheels install together in a
fresh environment and pass the artifact smoke recorded in
`docs/BOUNDED_MILESTONE_VALIDATION.md`.

## M5 — separately authorized experiment

Prepared but not started. `docs/M5_PILOT_PROTOCOL.md` freezes recommended splits,
hard call/cost/time limits, retry policy, stopping rules, and equal pre/post
evaluation. Execution remains gated on the active benchmark finishing,
credential cutover, reviewed merges, and filling the exact provider/model fields.
The offline manifest builder and redaction-safe remote check are implemented and
tested; they prepare those transitions but do not authorize or perform them.
