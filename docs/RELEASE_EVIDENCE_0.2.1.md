# MathCheck RL 0.2.1 and Hub 0.1.1 release evidence

## Public identities

- Repository: <https://github.com/stanleyngugi/mathcheck-rl>
- Git release: <https://github.com/stanleyngugi/mathcheck-rl/releases/tag/v0.2.1>
- Release commit: `10e3f9e54dc50635514e5aada6ed556d3da346e8`
- Core dependency commit embedded in the Hub wheel:
  `d4912c30564e99a3200f77ca7e94a8a3ebe184c7`
- Prime Hub environment:
  <https://app.primeintellect.ai/dashboard/environments/stanley-ngugi/mathcheck-rl>
- Prime Hub owner and slug: `stanley-ngugi/mathcheck-rl`
- Prime Hub version: `0.1.1`, public, Verifiers v1

The project is MathCheck RL. `native-verify` and `native_verify` are the
historical 0.x Python distribution and import names. The primary Hub package is
`mathcheck-rl`. The older finite-observation `native_verify_seq` adapter is a
historical experimental baseline inside the repository, not a third product.

## Tests and release gate

- Full source suite: 113 passed, 2 intentionally skipped
- Tested Python: 3.12.3
- Declared Python range: `>=3.11,<3.14`
- Tested Lean: 4.23.0
- Lean executable SHA-256: `cbf5fd536e142ef1beaccf33f788fd8a7f3f29fb214e75c11319a8d8677b4b2b`
- Release-manifest SHA-256: `b58de70188f2ff2a454197f212415b7d58a7b440ca20006641ba16e264eada1b`

The clean release gate ran twice and produced byte-identical wheels:

| Distribution | Version | SHA-256 |
| --- | --- | --- |
| `lean-kernel-verifier` | 0.3.2 | `61f5d485d59b77270df4134c0dd332afe9fbd7b7596baa85400341b85259bd4d` |
| `native-verify` | 0.2.1 | `2e27070f72192c2803effea5637bef0d7dac12220b109489099b78b6a56e80f3` |
| `native-verify-seq` | 0.2.1 | `b84efc91878f35d3e704cffdcdd486e31feb9f6094bbc507697580cb5ef4f165` |
| `mathcheck-rl` local reproducible build | 0.1.1 | `d497ff87c0fc1c0af183a395769b13366ad426653eaf872884aca2e8292b6383` |

The release smoke installed all four wheels outside the source trees, passed
`pip check`, asserted every distribution version, confirmed that primary task
rows contain a specification but no expected candidate, and ran a real Lean
accepted/rejected pair with statuses `checked_success` and
`mathematical_rejection`.

## Hub consumer validation

The Prime CLI built the publication wheel without the release gate's fixed
source-date epoch, so its byte hash is different from the reproducible local
build even though it packages the same versioned source:

- Hub wheel: `mathcheck_rl-0.1.1-py3-none-any.whl`
- Hub wheel SHA-256: `ed6e997980a3c532c0282f80a99513fe8c9e976a54fa9b2577bcc17b90df754d`
- Public simple index:
  <https://hub.primeintellect.ai/stanley-ngugi/simple/mathcheck-rl/>

A new Python 3.12 environment first installed Prime CLI 0.6.34, then ran:

```bash
prime env install stanley-ngugi/mathcheck-rl@0.1.1
```

The official installer extracted the wheel's PEP 508 requirements and resolved:

- MathCheck Engine 0.3.2 from commit `742edec6bdb4f7057780fc54e98fb284b76eedcf`;
- MathCheck RL core 0.2.1 from commit `d4912c30564e99a3200f77ca7e94a8a3ebe184c7`;
- `mathcheck-rl` 0.1.1;
- Verifiers 0.3.0.

The installed module imported from that fresh environment's `site-packages`.
Local Verifiers v1 setup validation then recorded one valid task, zero invalid,
zero error, zero timeout, and a valid rate of 1.0 using the subprocess runtime.

## Hosted-execution boundary

An authenticated Prime evaluation command was attempted only after the Hub
consumer checks. It stopped before any rollout with an explicit insufficient
balance response. No model result, hosted Lean check, or training step was
produced, and no active solver quota, environment, result, or journal was used.

The supported claim is therefore: MathCheck RL is publicly distributed,
installable through Prime Hub, loadable as Verifiers v1, locally setup-valid,
and locally executable with the declared isolated Lean runtime. The project
does not yet claim a demonstrated Prime-hosted rollout or one-click hosted
training. Hosted execution still requires a suitable Linux runtime containing
Lean 4.23.0, bubblewrap, and compatible namespace support, followed by an
actual successful capability probe.
