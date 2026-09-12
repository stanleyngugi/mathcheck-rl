# MathCheck RL

**Answer-key-free bounded-math tasks and Lean-checked rewards for RL.**

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
counts, and bounded minima. Pair certificates must enumerate the entire
satisfying relation in the declared rectangle, not merely valid witnesses.

The legacy sequence environment is useful for executable-program RL, but it is
finite observation testing. It does not prove a function correct for every
natural number, even when the prose describes a universal rule.

## Result model

Verdicts distinguish:

- `checked_success`: the encoded checker accepted;
- `mathematical_rejection`: a well-formed candidate failed the encoded check;
- `invalid_input`: extraction, language, or compilation was malformed;
- `unsupported_task`: outside the declared task contract;
- `operational_error`: timeout, missing/mismatched toolchain, or backend failure.

Operational failures deny reward but are not reported as mathematical
counterexamples. Verdicts bind SHA-256 digests of the exact specification and
artifact/submission.

## Isolation and toolchain

Untrusted Lean programs require the shared Linux `lean-isolated` wrapper and
Lean 4.23.0 exactly. There is no fallback to a discovered host Lean executable,
retired checkout, or sibling solver environment.

```bash
python -m pip install -e ../lean-kernel-verifier -e '.[dev]'
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

The blog-ready project narrative is in
[`TECHNICAL_ARTICLE.md`](TECHNICAL_ARTICLE.md). It explains the answer-key-free
contract, trust boundary, evaluation discipline, and deliberately bounded claims.

The current public GitHub release is
[`v0.2.1`](https://github.com/stanleyngugi/mathcheck-rl/releases/tag/v0.2.1).
The primary environment is public on Prime Hub as
[`stanley-ngugi/mathcheck-rl`](https://app.primeintellect.ai/dashboard/environments/stanley-ngugi/mathcheck-rl)
version `0.1.1`. Exact local and Hub hashes, consumer-install evidence, and the
hosted-execution boundary are recorded in
[`docs/RELEASE_EVIDENCE_0.2.1.md`](docs/RELEASE_EVIDENCE_0.2.1.md).

Start with [`examples/specification_quickstart.py`](examples/specification_quickstart.py)
for a fixed task that demonstrates both a checked answer and a checked rejection.
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

The separately authorized M5 pilot has an offline preregistration gate in
`scripts/prepare_m5_manifest.py`. It binds the exact release manifest and Git
commits, reproduces all 200 frozen task specifications and their commitments,
enforces pairwise split disjointness, and rejects unset runtime fields. It does
not contact a provider or start training.

After the active benchmark finishes and credential rotation is coordinated,
`scripts/check_remote_credentials.py` provides a read-only origin check whose
output never includes the remote URL.
