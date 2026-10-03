# MathCheck RL

**Formal verification of bounded mathematical submissions, used as answer-key-free RL rewards.**

The repository and public project name are **MathCheck RL**. The Python
distribution, imports, and environment IDs remain `native-verify`,
`native_verify`, and `native-verify-*` in the 0.x series for compatibility.
See [BRANDING.md](BRANDING.md) for the naming policy.

RL task and reward layers for bounded computational verification. The shared
`lean-kernel-verifier` package owns trusted source generation, Lean execution,
isolation, and checker evidence. This repository owns tasks, prompts, candidate
formats, split policy, reward caching, and framework adapters.

Two contracts are intentionally separate:

| Environment | Model submission | What acceptance establishes |
|---|---|---|
| `mathcheck-rl` | Integer candidate or complete pair certificate in JSON | The candidate satisfies the complete encoded bounded specification, without a stored expected answer |
| `native-verify-seq` | Restricted pure Lean definitions | The function agrees with all environment-held observations in the declared finite index range |

The specification environment is the answer-key-free path. The environment
freezes an arithmetic predicate/objective before generation; the model cannot
submit or weaken it. Scalar tasks cover exact evaluation, bounded sums, bounded
counts, and bounded minima. Submitted scalar answers must be nonnegative
integers smaller than `10**1000`; integer expressions may have negative
intermediate values. Negative final answers and a minimum's “no solution”
result have no submission representation in this version. Pair certificates
must enumerate the entire satisfying relation in the declared rectangle,
not merely valid witnesses.

The legacy sequence environment is useful for executable-program RL, but it is
finite observation testing. It does not prove a function correct for every
natural number, even when the prose describes a universal rule.

## Start with a complete check

Install the two source projects and configure the isolated Lean runtime as shown
below, then run:

```bash
python examples/specification_quickstart.py --lean-bin "$NATIVE_VERIFY_LEAN"
```

The walkthrough checks a count, a minimum with a feasible-but-nonminimal
control, and complete versus incomplete pair certificates. It exits nonzero
if any expected control outcome fails. No model or provider account is needed.

The formal claim concerns the encoded contract. The specification author,
Python-to-Lean expression translation, generated template, and native compiler
remain trusted. The solving model supplies data; trusted code constructs and
discharges the Lean obligation. See the [article](TECHNICAL_ARTICLE.md) for the
comparison with Python checking and proof-synthesis RL.

## Result model

Verdicts distinguish:

- `checked_success`: the encoded checker accepted;
- `mathematical_rejection`: a complete recognized native diagnostic reports a false encoded check;
- `invalid_input`: extraction, language, or compilation was malformed;
- `unsupported_task`: outside the declared task contract;
- `operational_error`: timeout, missing/mismatched toolchain, or backend failure.

Operational failures deny reward but are not reported as mathematical
counterexamples. Verdicts bind SHA-256 digests of the exact specification and
artifact/submission.
Exit 1 alone is inconclusive: unrecognized, truncated or mixed checker errors
remain operational. The legacy sequence adapter also requires an explicit
negative decision before labeling a train/holdout mismatch.

## Isolation and toolchain

Untrusted Lean programs require the shared Linux `lean-isolated` wrapper and
Lean 4.23.0 exactly. There is no fallback to a discovered host Lean executable,
retired checkout, or sibling solver environment.

```bash
python -m pip install -e ../mathcheck-engine -e '.[dev]'
export NATIVE_VERIFY_LEAN=/absolute/path/to/venv/bin/lean-isolated
export LKV_SANDBOX_TOOLCHAIN=/absolute/path/to/lean-4.23.0-linux
python -m pytest tests -q
```

Run from Linux or inside WSL. The isolation wrapper fails closed if bubblewrap,
namespaces, resource limits, or the pinned toolchain are unavailable.

## Layout

```text
src/native_verify/
  specification_tasks.py  # answer-key-free tasks and reward path
  tasks.py                 # legacy finite-observation sequence tasks
  sanitizer.py             # restricted lexical program-language boundary
  runner.py                # shared isolated runner integration
  async_cache.py           # exact-input single-flight verdict cache
environments/
  mathcheck_rl/            # public v0/v1 answer-key-free environment
  native_verify_seq/       # v0/v1 finite-observation adapter
```

Train/evaluation generators remove duplicate specifications and enforce digest
disjointness. This is evidence of split separation for the encoded tasks, not a
claim that procedural generation eliminates all semantic contamination.

See `docs/DEFECT_LEDGER.md` for the bounded correction ledger and
`docs/RUN_RESULTS.md` for historical training evidence. No learning improvement
is inferred from the historical smoke launch alone.

The current repository article,
[Grading Mathematical Answers Without Precomputed Answer Keys](TECHNICAL_ARTICLE.md),
walks through leastness and completeness, explains the answer-key-free contract
and its trust boundary, and separates current validation from historical
release evidence. Website publication is managed separately.

The current public GitHub release is
[`v0.2.1`](https://github.com/stanleyngugi/mathcheck-rl/releases/tag/v0.2.1).
The primary environment is public on Prime Hub as
[`stanley-ngugi/mathcheck-rl`](https://app.primeintellect.ai/dashboard/environments/stanley-ngugi/mathcheck-rl)
version `0.1.1`. Exact local and Hub hashes, consumer-install evidence, and the
hosted-execution boundary are recorded in
[`docs/RELEASE_EVIDENCE_0.2.1.md`](docs/RELEASE_EVIDENCE_0.2.1.md).

Legacy Prime-RL operational experiments are retained under
[`archive/historical_prime_rl/`](archive/historical_prime_rl/) for provenance;
they are not the supported public interface.

## Release-candidate gate

Install `requirements-release.lock` into a dedicated build environment, then run
`scripts/release_gate.py` with the verifier worktree, a separately owned
read-only Lean 4.23.0 distribution, its expected binary SHA-256, and an absent or
empty output directory. The gate verifies the locked build tools and Lean hash,
builds all four versioned wheels with a fixed source-date epoch, installs them in
a disposable environment, runs `pip check`, and performs the answer-key-free
real-Lean smoke outside both source trees.

The versioned M5 pilot amendment has an offline preregistration gate in
`scripts/prepare_m5_manifest.py`. It binds the exact release manifest and Git
commits, reproduces all 120 frozen task specifications and their commitments,
enforces pairwise split disjointness, and rejects unset runtime fields. It does
not contact a provider or start training.

After the active benchmark finishes and credential rotation is coordinated,
`scripts/check_remote_credentials.py` provides a read-only origin check whose
output never includes the remote URL.

## Audit finish line and optional experiments

[FINISH_LINE.md](docs/FINISH_LINE.md) fixes the delivery scope and completion
criteria. Source delivery covers explicit contracts, corrected source behavior,
honest writing, installed packages and the disclosed question-only demonstration.
Validated delivery adds the current native gate. **RL training results are
optional and are not a project-completion requirement.**

Run `scripts/closeout_gate.py --help` for the finite closeout command. It builds
and installs all four wheels, runs source suites and installed-package checks,
and executes the native checklist when a healthy toolchain is supplied.
Its report distinguishes source completion, failed checks and blocked native
validation. [CURRENT_VALIDATION.md](docs/CURRENT_VALIDATION.md) records evidence.

The [GSM8K demonstration](docs/GSM8K_DEMONSTRATION.md) admits three development
contracts and one known public-test example, with two explicit exclusions.
[The semantic audit](docs/GSM8K_SPEC_AUDIT.md) records their interpretation and
same-context review limits. This is a small interface demonstration, not a
whole-dataset or held-out performance claim.

The [procedural M5 pilot](docs/M5_PILOT_PROTOCOL.md) and
[local GRPO driver](docs/LOCAL_TRAINING.md) are available for a separately
requested experiment. Their implementation and tiny checkpoint smoke do not
make training mandatory. Broader contracts and automatic formalization are
future projects outside this audit.

Distribution commands and historical evidence live in
[REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md). Candidate versions are Engine
0.3.3, RL core/sequence 0.2.2 and Hub 0.1.2. Public releases remain unchanged
until the native gate passes. The **Native release candidate gate** workflow
runs manually or when the Hub's dependency metadata changes on `main`. It
checks the immutable Engine dependency and runs the finite checking and packaging
gates without policy training or automatic publication.
