# native-verify-spec

This is the answer-key-free environment. Each prompt and checker are derived
from one environment-owned bounded specification. The model submits only an
integer candidate or a complete pair certificate in JSON; it does not submit a
Lean proof or a replacement specification.

Successful scalar verdicts establish the exact encoded evaluation, sum, count,
or bounded minimum. Successful pair verdicts establish equality with the entire
satisfying relation in the declared rectangle and the claimed cardinality. The
scope is the encoded bounded specification, not arbitrary prose.

The framework column named `answer` contains the frozen specification because
that is the metadata channel offered by the v0 API. It contains no expected
candidate. Train/evaluation splits are disjoint by specification digest.

Execution requires the shared Linux `lean-isolated` wrapper configured through
`NATIVE_VERIFY_LEAN` or `LEAN_BIN`, with `LKV_SANDBOX_TOOLCHAIN` pointing to a
standalone Lean 4.23.0 distribution. Missing isolation fails closed.
