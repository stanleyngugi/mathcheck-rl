# Bounded milestone validation

Validation was performed on 2026-09-08 in the isolated worktrees under
`_agent_worktrees/bounded-verifier-native-20260908`. The active solver checkout,
its Python environment, its Lean wrapper/toolchain, quota state, and journals
were not modified. The archived Lean 4.23.0 toolchain was referenced read-only
through each isolated environment's own `lean-isolated` entry point.

## Baseline

- `lean-kernel-verifier`: 68 tests and 38 subtests passed with real Lean.
- `native-verify`: 44 tests passed with real Lean.

## Corrected source validation

- `lean-kernel-verifier`: 70 tests and 42 subtests passed in 52.75 seconds.
- `native-verify`: 63 tests passed in 125.50 seconds, including explicit
  operational-failure controls for both checking paths.
- Both suites had zero skips and used Lean 4.23.0.
- The legacy no-provider environment smoke accepted the honest program and
  rejected `sorry` and missing-fence controls.
- The answer-key-free environment smoke accepted the correct bounded candidate,
  rejected the wrong candidate, and reported `checked_success` versus
  `mathematical_rejection`.

The native pytest configuration now limits discovery to `tests/`. This prevents
an unrestricted test invocation from collecting historical provider scripts,
including a script that attempts to read a local API-key file.

## Built-artifact validation

The following wheels were built into the isolated `wheelhouse` and installed
together into a fresh `/tmp/nv-wheel-smoke-20260908` virtual environment:

| Wheel | SHA-256 |
|---|---|
| `lean_kernel_verifier-0.3.0-py3-none-any.whl` | `8668D98B774C28D757DB1328F5B03A1196419D7EA4D4A05D6C353D3D4FC63FC1` |
| `native_verify-0.1.0-py3-none-any.whl` | `17ABA5C7183A34C26A1B84A2AEA848E29633351EB260F64729F589126A235046` |
| `native_verify_seq-0.2.0-py3-none-any.whl` | `2948D27A69F2331098839331B47CF512A871D7CD7772AA50B3FA385966CB9DB4` |
| `native_verify_spec-0.1.0-py3-none-any.whl` | `325CE4B9735D8CD5D3A50D9CA322C929566AD998BC04C173D9B2F650FD2E6057` |

The smoke ran from `/tmp`, without source-tree path injection. It imported the
four distributions with `verifiers==0.3.0` and `datasets==4.8.5`, loaded both
environment adapters, confirmed that the specification row contains no expected
answer, and exercised a real Lean accepted/rejected pair.

## Deliberate boundary

M5 was not started. No provider call, paid training run, publication step,
remote push, credential change, or benchmark-state mutation was performed.
