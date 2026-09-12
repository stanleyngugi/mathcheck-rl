# Configuration policy

The old TOML experiment inputs moved to
`archive/historical_prime_rl/configs/`. They are preserved evidence, not current
safe launch recipes, and must not be silently rewritten to make a new run look
like the old one.

In particular, they point `NATIVE_VERIFY_LEAN` at a direct Lean executable.
Current native verification requires the shared `lean-isolated` wrapper plus an
explicit `LKV_SANDBOX_TOOLCHAIN` path and Lean 4.23.0 exactly. Any future run must
create a new configuration with frozen source/task digests, budget, retry and
stopping policies, rather than editing these historical files in place.

The smoke and 120-step files also contain different vLLM settings. Do not infer
which values produced a historical result without the corresponding preserved
run record.
