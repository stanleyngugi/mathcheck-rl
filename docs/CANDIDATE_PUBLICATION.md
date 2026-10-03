# Candidate validation and publication

This is the remaining release sequence for the audited candidates. GitHub
source updates and Prime Hub publication are separate operations. The public
Hub still shows **0.1.1**, with the historical Engine/core pins, as observed on
2026-10-03. Candidate **0.1.2** is ready in source but must not be published
before D6 passes.

## Current execution blocker

The latest native workflow retry (attempt 2 of
[run 37130137846](https://github.com/stanleyngugi/mathcheck-rl/actions/runs/37130137846))
started zero steps. GitHub's run summary explicitly reports an account billing
lock. Resolving that account condition is outside the test suite. Alternatively,
run the same gate on an existing supported Linux host.

The available assistant worker has no `/proc`; bubblewrap's capability probe
fails before isolation starts. Installing Python packages or weakening the
isolation requirement cannot satisfy D6. The latest observations are retained in
[evidence/native-closeout-retry-20261003.json](evidence/native-closeout-retry-20261003.json).

## Run the native gate

Use the current Engine and RL sources on supported Linux, Python 3.12, and
`requirements-release.lock`. Install both projects in that validation environment.
Provide a standalone Lean **4.23.0 exactly**, a compatible bubblewrap installation,
and the independently owned read-only toolchain required by the wrapper.
Follow [FINISH_LINE.md](FINISH_LINE.md) and the existing native workflow setup.

Run from the RL repository:

```sh
python scripts/closeout_gate.py \\
  --verifier-root ../mathcheck-engine \\
  --toolchain /absolute/path/to/read-only-lean-4.23.0-linux \\
  --toolchain-sha256 cbf5fd536e142ef1beaccf33f788fd8a7f3f29fb214e75c11319a8d8677b4b2b \\
  --output artifacts/native-closeout
```

The output directory must be new. Exit **0**, `native_validation_complete=true`
and `release_ready=true` are required. Keep the report, all logs, native controls
and four wheel identities together. A source-only exit 2 is not release approval.
No model inference or training is necessary.

## Publish the Hub candidate

After D6 passes, authenticate the current Prime CLI with the account that owns
`stanley-ngugi/mathcheck-rl`. Do not place API keys in repository files or logs.
Publish from the environment package directory:

```sh
cd environments/mathcheck_rl
prime env push
prime env info stanley-ngugi/mathcheck-rl
```

Its declared version is **0.1.2**. Do not use automatic version bumping or replace
the earlier 0.1.1 artifact. The candidate wheel must retain these dependencies:

- Engine: `dce2fc88cee1e98ed3136ac89a4b40eba0d1ada7`
- RL core: `d7158c411f0e00122f86bbd56949839b86284923`

The package already declares Verifiers 0.3.0 and supports the v1 taskset interface.
Verify that the Hub lists it as v1, shows 0.1.2 and retains the expected pins.
Prime's [publication documentation](https://docs.primeintellect.ai/tutorials-environments/create)
describes versioned uploads and wheel-embedded direct dependencies. A GitHub push
alone does not perform this upload.

## Verify the published installation

In a new consumer environment, outside both source trees:

```sh
prime env install stanley-ngugi/mathcheck-rl@0.1.2
python -m pip check
```

Inspect installed distribution versions, direct-URL commit identities and
packaged source hashes. Configure the same healthy isolated Lean runtime and
repeat known-valid and known-invalid native checks through the installed
framework path. Preserve the actual Hub wheel hash separately from local build
hashes if Prime rebuilt it. Hub visibility alone does not demonstrate hosted
Lean execution or learning results.

Record the publication identity and fresh consumer evidence in
`CURRENT_VALIDATION.md`. If publishing the GitHub distributions, release Engine
0.3.3 and RL core/sequence 0.2.2 with the validated wheels, manifests and evidence;
do not reuse the historical release's native evidence for these versions.
Then stop: additional contracts, dataset expansion and policy training are outside
this delivery.
