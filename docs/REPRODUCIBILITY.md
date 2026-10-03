# Reproducibility and historical distribution evidence

The following records describe the published RL 0.2.1 / Hub 0.1.1 artifacts.
They do not validate later source changes on `main`. Run the release gate again
before publishing updated wheels. Current source development starts with the
root README.

## What the historical training run actually showed

A preserved August 2026 run used the sequence baseline with a
Qwen2.5-1.5B-Instruct model, LoRA, GRPO, and a single colocated RTX 2000 Ada.
Twenty-four trainer steps completed. Rollouts reached Lean, binary rewards
reached the trainer, policy updates and weight synchronization occurred, and a
checkpoint was written.

That is useful operational evidence: the broad loop once executed end to end.
It is not evidence that training improved mathematical performance. The run was
short, family difficulty was imbalanced, reward varied sharply with batch
composition, some preserved logs contain empty or cancelled work, and no
controlled pre/post evaluation establishes a gain. The active documentation
retains that distinction, while old pod scripts and patches live in an archive
so they cannot be mistaken for the current interface.

This article makes no RL improvement claim. The separate solver project and its
long-running benchmark are also outside this result.



## How MathCheck RL fits Verifiers v1

The Hub module supports the current Verifiers v1 taskset interface while
retaining a compatibility loader for earlier workflows.

In v1, task data contains the prompt, an identifier, resource hints, and the
frozen specification. Task configuration contains the isolated Lean launcher
and verification timeout. A `Task` owns reward functions and writes diagnostic
fields into trace metadata. A `Taskset` deterministically yields the configured
families and number of tasks.

The main reward decorator has weight 1.0. The stage-rank decorator has weight
0.0. Task resources currently request two CPU units and 2 GB of memory. The task
declares `NEEDS_CONTAINER = False` because it invokes the separately configured
isolation wrapper in the environment process; that is an execution detail, not
a statement that untrusted checking needs no sandbox.

The compatibility `load_environment` path builds training and evaluation
datasets and a single-turn rubric. Both interfaces ultimately call the same
`verify_specification_submission` function and preserve the same candidate
contract.



## Publishing on Prime Hub

The primary environment is public at
<https://app.primeintellect.ai/dashboard/environments/stanley-ngugi/mathcheck-rl>.
Version 0.1.1 is classified as Verifiers v1. The recommended installation path
is the Prime CLI:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install -U prime
prime login
prime env install stanley-ngugi/mathcheck-rl@0.1.1
```

The Hub wheel declares Verifiers 0.3.0, Datasets 3–4, and immutable PEP 508 Git
dependencies on the exact public Engine and RL core commits. This is important
because ordinary wheel metadata must carry direct URL requirements;
`[tool.uv.sources]` would not travel with the built artifact.

Prime's installer reads those requirements and passes the immutable URLs to the
package manager. A raw `uv pip install` against only the extra index may reject
transitive URL dependencies under uv's security rules, so the documented and
tested route is `prime env install`.

The Prime CLI built and uploaded
`mathcheck_rl-0.1.1-py3-none-any.whl` with SHA-256
`ed6e997980a3c532c0282f80a99513fe8c9e976a54fa9b2577bcc17b90df754d`.
The independently reproducible local fixed-epoch build has a different byte
hash because the Prime publication build did not use the repository release
gate's fixed source-date epoch. Both facts are recorded instead of pretending
the artifacts are byte-identical.



## What has been validated

The 0.2.1 source suite passed 113 tests, with two platform-specific tests
intentionally skipped in that run. The tests cover, among other things:

- correct, adjacent-wrong, nonminimal, and incomplete-certificate controls;
- strict fenced JSON, duplicate keys, malformed pairs, bounds, and pseudo-integer
  rejection;
- multiple deterministic seeds and digest-disjoint splits;
- missing-isolation and checker-failure classification;
- exact-input concurrent cache reuse and cancellation behavior;
- v0 compatibility and v1 taskset adapters;
- durable batch-record and offline pilot-manifest behavior;
- package metadata and exact dependency versions.

The complete release gate ran twice from clean temporary environments. Both
runs produced byte-identical local wheels, passed dependency checks, imported
from installed packages rather than source trees, loaded both environment
adapters, confirmed the primary task row stored no expected candidate, and used
isolated Lean to accept a known-correct result and reject a known-wrong result.

A separate consumer environment then installed the exact public Hub version.
It resolved MathCheck Engine 0.3.2 from commit
`742edec6bdb4f7057780fc54e98fb284b76eedcf`, RL core 0.2.1 from commit
`d4912c30564e99a3200f77ca7e94a8a3ebe184c7`, MathCheck RL 0.1.1, and
Verifiers 0.3.0. The module imported from the new environment's
`site-packages`. Verifiers' local setup validator then loaded one Hub task under
the subprocess runtime and recorded one valid result with no errors or timeouts.

Hub distribution and hosted execution are related but different claims. An
authenticated Prime inference attempt stopped before any rollout because the
account had insufficient balance. No hosted model result or hosted Lean check
was produced. The project therefore does not claim a demonstrated Prime-hosted
rollout or one-click hosted training.

The current native reward requires Linux, `lean-isolated`, a standalone Lean
4.23.0 distribution, bubblewrap, and compatible namespace support. A future
hosted demonstration needs a runtime image or substrate with those capabilities,
then one known-valid and one known-invalid end-to-end check. We chose to state
that boundary rather than borrow quota from an unrelated active benchmark.



## Reproducing the local environment path

MathCheck RL 0.2.1 and Hub 0.1.1 support Python 3.11 through 3.13. Install the
published environment with the Prime CLI, then configure the native checker:

```bash
prime env install stanley-ngugi/mathcheck-rl@0.1.1

export NATIVE_VERIFY_LEAN=/absolute/path/to/venv/bin/lean-isolated
export LKV_SANDBOX_TOOLCHAIN=/absolute/path/to/lean-4.23.0-linux

lean-isolated --version
```

A local, no-model v1 setup check is:

```bash
validate mathcheck-rl \
  --only-setup True \
  --runtime.type subprocess \
  --num-tasks 1 \
  --rich False
```

For source development and the complete test suite:

```bash
git clone https://github.com/stanleyngugi/mathcheck-engine.git
git clone https://github.com/stanleyngugi/mathcheck-rl.git

cd mathcheck-engine
git checkout v0.3.2

cd ../mathcheck-rl
git checkout v0.2.1
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e ../mathcheck-engine -e '.[dev]'

export NATIVE_VERIFY_LEAN="$PWD/.venv/bin/lean-isolated"
export LKV_SANDBOX_TOOLCHAIN=/absolute/path/to/lean-4.23.0-linux
python -m pytest tests -q
```

The release manifest and exact wheel hashes are published with the GitHub
release. A missing Lean configuration may cause live tests to skip; such a run
must not be reported as full native verification evidence.

The frozen release and Hub evidence—including the exact consumer-install
resolution and hosted boundary—is collected in
[`docs/RELEASE_EVIDENCE_0.2.1.md`](docs/RELEASE_EVIDENCE_0.2.1.md). The public
GitHub release is at
<https://github.com/stanleyngugi/mathcheck-rl/releases/tag/v0.2.1>.

