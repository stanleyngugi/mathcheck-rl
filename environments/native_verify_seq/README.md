# native-verify-seq

Legacy finite-observation executable-program tasks for Prime Intellect
`verifiers`. The model submits restricted pure Lean definitions. Reward is 1
only when the function agrees with every environment-held value in the exact
finite range stated in the prompt.

This contract does not establish correctness for arbitrary `n`. Hidden suffixes
and wider boundary ranges make hard-coded prefix solutions less useful, but they
remain finite tests. Use `native-verify-spec` when answer-key-free complete
bounded checking is required.

Train and evaluation rows are deduplicated and disjoint by a digest over family,
parameters, and all checked values. The framework `answer` column holds the
environment-owned finite arrays and is never rendered into the prompt.

The v0 rubric exposes binary `lean_pass` plus zero-weight stage and timing
metrics. The v1 task uses an exact-input bounded single-flight cache, so reward
and metrics share one immutable verdict. Timeout or backend failure yields zero
reward with `operational_error`; it is not called a mathematical mismatch.

Execution requires Linux/WSL, the shared `lean-isolated` executable configured
through `NATIVE_VERIFY_LEAN` or `LEAN_BIN`, and `LKV_SANDBOX_TOOLCHAIN` pointing
to Lean 4.23.0. Missing isolation fails closed; host Lean discovery is disabled.
