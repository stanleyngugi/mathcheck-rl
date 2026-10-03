# Local procedural trainer

The optional trainer performs real causal-language-model parameter updates.
It has not produced an M5 learning result. Native execution and frozen launch
inputs remain prerequisites; the website is managed separately by its owner.

## Install and freeze

Use a clean Linux environment with working user namespaces, bubblewrap and
Lean 4.23.0. Install the Engine and RL candidate source commits, the locked
release dependencies, and `requirements-training.lock`. A CPU-only PyTorch
installation can use its official CPU wheel index:

```sh
python -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install transformers==4.57.6
python -m pytest tests/test_grpo.py tests/test_local_pilot.py -q
```

Supply an actual local model/tokenizer bundle with safetensors weights. No
checkpoint is downloaded implicitly and remote model code is disabled. The
trainer loads full float32 weights, keeps a frozen initial reference, disables
dropout, and uses AdamW with zero weight decay. It supports CPU and CUDA; the
local smoke used CPU only. Full tuning retains two model copies and optimizer
state, so choose a model that fits the worker's memory and the time budget.

Serialize `dataclasses.asdict(LocalTrainingConfig(...))` as the training config.
Its digest is `canonical_json_sha256(config_object)`. The default settings are
seed 20261003, learning rate 1e-5, KL coefficient 0.01, clipping epsilon 0.2,
gradient norm cap 1, group size 3 and completion limit 256 tokens. The completion
limit must accommodate the intended certificate lengths and model context;
freeze any change before sampling. Temperature and top-p are both fixed at 1,
top-k is disabled, and checkpoint-specific generation processors are not
inherited. This keeps sampling consistent with the policy log probabilities.

Use `checkpoint_digest(Path(checkpoint))` to bind the complete model/tokenizer
bundle, then create a `PilotTrainingPlan` with that hash, the config hash, and
the exact RL source commit. Freeze `provider=local-transformers`, the actual
model identity, `trainer_runtime_version` in the exact form
`torch==<installed-version>;transformers==<installed-version>`, and
`currency_conversion_source=local-unbilled-no-currency-conversion`.
The CPU wheel reports `torch==2.8.0+cpu`. Local provider spend is zero; worker
compute cost is outside that provider-spend field and should be reported
separately. This driver has no hosted-provider or quota integration.

Run `scripts/prepare_m5_manifest.py --help` to supply these values, the release
gate manifest, source commits and genuine benchmark-completion reference. It
rejects `UNSET`; do not manufacture completion or release evidence.

## Execute

After the full release gate passes, keep the four wheels and its manifest.
Set `LKV_SANDBOX_TOOLCHAIN` to the separately owned read-only toolchain and run:

```sh
python scripts/run_m5_local.py \
  --manifest /path/to/frozen-pilot.json \
  --release-manifest /path/to/release-manifest.json \
  --training-config /path/to/training-config.json \
  --checkpoint /path/to/initial-checkpoint \
  --wheel-dir /path/to/gated-wheels \
  --verifier-root /path/to/mathcheck-engine \
  --lean-bin /path/to/venv/bin/lean-isolated \
  --output /path/to/new-run-directory
```

The command checks clean source commits, imported package locations, dependency
versions, checkpoint/config/release identities, actual wheel bytes, Lean binary
identity and six native positive/negative controls before loading the model.
It rebuilds the manifest to reject changes to split commitments, budgets or
analysis rules. It never silently substitutes a Python reward checker.

The objective uses population-standardized binary rewards, a clipped policy
ratio, the `exp(log_ref-log_policy) - (log_ref-log_policy) - 1` KL estimator,
and the original per-sequence token normalization. It scores through the first
EOS and ignores subsequent padding. Old and reference probabilities are
detached. One group receives at most one update; zero-variance groups are
recorded and skipped without resampling or shaping. If all groups are
degenerate or weights do not change, the run stops before a learning comparison.

The run follows 40 initial primary completions, 40 initial confirmatory
completions, 40 training groups of three, final checkpoint save, 40 final primary
completions and, only after the primary gate passes, 40 final confirmatory
completions. Paired evaluations reuse frozen sampling seeds. The final checkpoint
is selected by training completion, never by evaluation performance.

## Records and limits

The exclusive output directory contains a durable JSONL journal, a final
safetensors checkpoint, `primary-analysis.json`, and a separate confirmatory
baseline journal created with mode 0600. Evaluation verdicts are excluded from
the policy update interface. A durable analysis digest is written before the
coordinator opens baseline confirmatory scores. This is process-local score
separation, not independent-custodian blinding; document that access-control
mechanism before launch or use an independent evaluator for stronger blinding.
Public specifications are already visible.

Completion slots are reserved before generation, including failures. There are
no automatic retries. Checker operational errors are recorded with zero reward
and stop the experiment before the next update. The CLI installs a Linux alarm
for the 60-minute experiment limit; phase checks also prevent further dispatch
or updates after expiry. Native library calls may delay delivery of Python
signals, so use a supervisor with a hard termination deadline when a strict
wall-clock cap is required. Interrupted work can leave an incomplete checkpoint;
checkpoint recovery and resumed trials are unsupported.

Reports include overall/family pass rates, paired transitions, invalid-input and
operational-error rates. Failure, timeout or missed primary criteria is recorded
without a learning-success claim. Forty tasks per split support an exploratory
pilot, not a general reasoning conclusion.

## Current evidence

The tensor controls and a tiny randomly initialized GPT-2 fixture
exercise actual gradients, optimizer steps, frozen-reference integrity and a
checkpoint round trip. Orchestration controls use explicit test doubles to
exercise the 280-call schedule, stop conditions and evaluation separation.
Neither supplies policy-performance evidence. No pretrained-policy M5 run has
started. See [CURRENT_VALIDATION.md](CURRENT_VALIDATION.md).
