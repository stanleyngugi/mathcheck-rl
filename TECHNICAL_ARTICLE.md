# MathCheck RL: rewards without a hidden answer key

## Abstract

Many mathematical reinforcement-learning environments compare a model's final
text with a stored answer. MathCheck RL takes a different, deliberately bounded
route: the environment freezes a machine-readable integer specification before
generation, accepts only a candidate answer or a complete finite certificate,
and asks MathCheck Engine to construct and run the corresponding Lean check.

This is not “RL for all mathematics.” The current contract covers exact integer
evaluation, finite sums, finite counts, bounded minima, and complete relations of
bounded pairs. That limited surface is the point: acceptance has a precise
meaning, infrastructure failure is not mislabeled as mathematical failure, and
the model cannot rewrite the checker specification in its response.

## The answer-key-free contract

Each task contains an environment-owned `ProblemSpec` or `PairCountSpec`. A model
sees a prompt derived from that specification and submits one fenced JSON object.
For scalar tasks the object contains an integer. For pair tasks it contains both
a count and the entire sorted, duplicate-free satisfying relation inside the
stated rectangle.

The reward path never reads an expected-answer field. It parses the candidate,
binds it to the frozen specification digest, and sends trusted generated Lean to
MathCheck Engine. A successful scalar check establishes that the candidate equals
the computation encoded by the bounded specification. A successful pair check
establishes equality with the complete bounded relation, rather than merely
confirming that a few submitted witnesses are valid.

That distinction matters for training. A weak witness checker can reward a model
for listing one convenient example. A complete-certificate checker requires the
whole finite object, and therefore exposes omissions as rejections.

## Results that preserve meaning

The environment reports five statuses:

- `checked_success`: Lean accepted the encoded candidate;
- `mathematical_rejection`: a well-formed candidate failed the encoded check;
- `invalid_input`: the submission or generated program was malformed;
- `unsupported_task`: the request was outside the declared contract;
- `operational_error`: the checker timed out or its backend was unavailable.

Operational errors receive no reward, but they are not presented as
counterexamples. Each verdict also records the exact specification and submission
digests, scope, backend, duration, and checker invocation count. The resulting
logs are useful for both reward accounting and post-run audits.

## Isolation and trust

Untrusted model-written Lean is used only by the legacy finite-sequence
environment. It must run through MathCheck Engine's opt-in Linux `lean-isolated`
wrapper with Lean 4.23.0. The wrapper uses bubblewrap namespaces, read-only
toolchain mounts, a private scratch directory, and process resource limits, and
it fails closed if those controls cannot be established.

The answer-key-free specification environment is narrower still: model output is
data, not Lean source. Trusted templates generate the check. Even here,
`native_decide` means the Lean compiler and native runtime join the trusted
computing base. The system certifies the encoded bounded specification, not the
faithfulness of a natural-language translation and not an unbounded theorem.

## Evaluation discipline

Task generation is deterministic from a seed, removes duplicate specification
digests, and enforces digest-disjoint train and evaluation splits. This prevents
literal task reuse. It does not prove semantic novelty, eliminate all
contamination, or demonstrate that a policy learned a transferable strategy.

The repository retains one historical Prime-RL smoke run because it establishes
that rollout, verification, reward delivery, updates, weight synchronization, and
checkpointing once completed end to end. It does not establish learning
improvement. The old pod scripts, configurations, patches, and operational notes
are archived separately so they cannot be mistaken for the supported interface.

## What is ready, and what comes next

Version 0.2 provides the answer-key-free and finite-sequence adapters, exact-input
single-flight caching, disjoint task generation, fail-closed checker integration,
unit and real-Lean tests, reproducible wheel gates, and an offline preregistration
gate for a future pilot. The pilot is intentionally separate from this release:
provider credentials, quotas, stopping rules, and empirical learning claims need
their own authorization and evidence.

The next verification families are preserved in MathCheck Engine's future
contracts document: bounded divisibility certificates, permutation and subset
certificates, polynomial identities, and coordinate-geometry identities. They
should be added one explicit contract at a time, each with adversarial tests and
an honest statement of what acceptance establishes.

MathCheck RL is therefore best understood as a reusable experimental instrument:
small enough to audit, strict enough to reject incomplete bounded claims, and
clear about the distance between a checked computation and a general proof.
