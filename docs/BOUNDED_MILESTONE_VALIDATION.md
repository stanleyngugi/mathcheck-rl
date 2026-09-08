# Bounded milestone validation

Validation was performed on 2026-09-08 and 2026-09-09 in the isolated worktrees under
`_agent_worktrees/bounded-verifier-native-20260908`. The active solver checkout,
its Python environment, its Lean wrapper/toolchain, quota state, and journals
were not modified. Initial validation referenced the archived Lean 4.23.0
toolchain read-only. Final release validation used a separate read-only copy at
`/tmp/nv-agent-lean-4.23.0-20260909` with Lean binary SHA-256
`cbf5fd536e142ef1beaccf33f788fd8a7f3f29fb214e75c11319a8d8677b4b2b`.

## Baseline

- `lean-kernel-verifier`: 68 tests and 38 subtests passed with real Lean.
- `native-verify`: 44 tests passed with real Lean.

## Corrected source validation

- `lean-kernel-verifier`: 70 tests and 42 subtests passed in 39.82 seconds.
- `native-verify`: 87 tests passed in 67.29 seconds, including explicit
  operational-failure and adversarial controls for both checking paths.
- Both suites had zero skips and used Lean 4.23.0.
- The legacy no-provider environment smoke accepted the honest program and
  rejected `sorry` and missing-fence controls.
- The answer-key-free environment smoke accepted the correct bounded candidate,
  rejected the wrong candidate, and reported `checked_success` versus
  `mathematical_rejection`.

The native pytest configuration now limits discovery to `tests/`. This prevents
an unrestricted test invocation from collecting historical provider scripts,
including a script that attempts to read a local API-key file.

The adversarial pass found and fixed one additional indented `private def`
sanitizer bypass. The expanded controls cover declaration modifiers, ambiguous
or duplicate-key JSON, malformed pair certificates, cache failure reuse, ten
independent split seeds, and zero reward for operational failures.

## Initial built-artifact validation

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

## Versioned release-candidate gate

`scripts/release_gate.py` validated the locked release tools, private read-only
Lean copy, exact Lean hash/version, package dependency closure, source-external
imports, and a real answer-key-free accepted/rejected pair. Release-candidate
versions are verifier `0.3.1`, native core `0.2.0`, sequence environment `0.2.0`,
and specification environment `0.1.0`. The generated manifest is stored beside
the candidate wheels in `release-candidate-20260909-repro`.

| Release-candidate wheel | SHA-256 |
|---|---|
| `lean_kernel_verifier-0.3.1-py3-none-any.whl` | `2ac1fea4e6e160e293b1e3a4787dc3f7aba9ca6978898834cb41112c529027e7` |
| `native_verify-0.2.0-py3-none-any.whl` | `6a544c5fb3d8c311856127c61129fd52a35644a4c003629fc04ea5bd5ba70095` |
| `native_verify_seq-0.2.0-py3-none-any.whl` | `98a8f835137ce5aa6dfc0139cf1e4f0f0e5486bd211046e27a867180d339122d` |
| `native_verify_spec-0.1.0-py3-none-any.whl` | `b520ee5881819934b06f722cbcf67996d3c02e22130e3b61dc3cf7b16e0c7b93` |

A second independent build with the same locked inputs and source-date epoch
produced byte-identical SHA-256 values for all four wheels.

## Deliberate boundary

M5 was not started. No provider call, paid training run, publication step,
remote push, credential change, or benchmark-state mutation was performed.
