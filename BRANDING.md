# Naming and compatibility

## Public name

The project is **MathCheck RL**: reinforcement-learning task and reward layers
for bounded mathematical specifications checked with Lean. The intended future
GitHub repository slug is `mathcheck-rl`.

This name makes the relationship to **MathCheck Engine** visible without using
`native_decide` as the product name. `native_decide` remains an implementation
detail and part of the trusted-computing-base disclosure, not a claim of broad
automated theorem proving.

## Stable 0.x compatibility names

The following identifiers remain unchanged through the 0.x line:

- PyPI/distribution name: `native-verify`
- Python import: `native_verify`
- environment IDs: `native-verify-spec` and `native-verify-seq`
- configuration prefix: `NATIVE_VERIFY_`

The dependency distribution remains `lean-kernel-verifier` even though its
public project name is MathCheck Engine. A future 1.0 migration may add aliases
and deprecations, but must not silently invalidate saved manifests.

## Scope boundary

MathCheck RL contains the reusable environments, tests, and release gates. The
separate experimental math solver, its provider credentials, quota database,
benchmark journals, and claims about model improvement are not part of this
project or its release narrative.
