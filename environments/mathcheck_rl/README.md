# MathCheck RL

MathCheck RL is an answer-key-free reinforcement-learning and evaluation
environment for bounded integer mathematics. It generates each prompt and its
trusted checker from one frozen bounded specification. A model submits an
integer candidate or a complete pair certificate in fenced JSON; it does not
submit a Lean proof or replace the specification.

Reward is binary. A reward of `1` means the submission satisfied the complete
encoded bounded specification. Scalar tasks establish the exact bounded
evaluation, sum, count, or minimum. Pair-certificate tasks establish equality
with the entire satisfying relation in the declared rectangle and the claimed
cardinality. The claim is limited to the encoded bounds; this environment does
not claim to prove arbitrary mathematical prose or facts outside those bounds.

The environment does not store an expected candidate. In the compatibility
API, the framework column named `answer` carries only the frozen checker
specification and is never rendered into the model prompt. Train and evaluation
tasks are generated deterministically and are disjoint by specification digest.

## Task configuration

- `families`: `all` or a comma-separated subset of supported bounded families.
- `num_per_family`: number of generated training tasks per family.
- `seed`: deterministic training-generation seed.
- `eval_num_per_family`: compatibility-API evaluation tasks per family.
- `eval_seed`: deterministic compatibility-API evaluation seed.
- `task.verify_timeout`: Verifiers v1 native-check timeout in seconds.
- `task.lean_bin`: optional explicit path to the isolated Lean launcher.

## Submission format

The prompt states the exact JSON schema. A scalar task uses a fenced object such
as:

```json
{"answer": 17}
```

Pair tasks require the complete bounded relation and its cardinality in the
schema shown by that task. Extra prose, replacement specifications, malformed
JSON, incomplete relations, duplicates, and out-of-bounds pairs are rejected.

## Reward and metrics

- `nv_specification_pass`: reward `1.0` only for an accepted complete result;
  otherwise `0.0`.
- `nv_stage_rank`: zero-weight diagnostic metric for checker progress.
- Verification status, stage, reason, and specification digest are recorded in
  trace metadata.

Timeouts and backend failures fail closed with zero reward and an operational
status. They are not reported as mathematical counterexamples.

## Runtime requirements

Execution requires Linux, MathCheck Engine's `lean-isolated` launcher, and a
standalone Lean 4.23.0 distribution. Configure:

```bash
export NATIVE_VERIFY_LEAN=/absolute/path/to/lean-isolated
export LKV_SANDBOX_TOOLCHAIN=/absolute/path/to/lean-4.23.0-linux
```

The launcher requires bubblewrap and a kernel that permits its isolation mode.
Missing isolation fails closed; MathCheck RL does not fall back to executing
untrusted model code with an arbitrary host Lean installation.

## Source and scope

- MathCheck RL: https://github.com/stanleyngugi/mathcheck-rl
- MathCheck Engine: https://github.com/stanleyngugi/mathcheck-engine

The older finite-observation sequence adapter remains in the repository as a
legacy experimental baseline. It is not the contract published by this Hub
environment.
