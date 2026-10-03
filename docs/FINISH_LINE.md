# Audit delivery and finite completion criteria

Scope frozen on 2026-10-03 following the owner's instruction: **RL training
results are optional and are not a defect or a condition of project completion.**

This delivery is the bounded specification-checking prototype, its adapters,
technical writing, reproducible packages and a small question-only dataset
demonstration. Work is pushed directly to `main`. Website publication is handled
by the owner and is outside this repository closeout.

## Required delivery checks

| ID | Requirement | Done when |
| --- | --- | --- |
| D1 | Declared checking contracts | Scalar evaluation/count/sum/minimum, complete bounded pair certificates and legacy finite observations have explicit inputs, scope, trust and failure meanings |
| D2 | Source correctness | Both source suites pass; no known reproduced parser, reward, cache or cancellation regression remains; live skips are recorded separately |
| D3 | Honest writing | The article explains answer-key-free checking, the Python comparison, native compiler trust and prose fidelity; it makes no learning, universal-proof or automatic-formalization claim |
| D4 | Reproducible installed artifacts | Four candidate wheels build and install together, dependency checking passes, imports come from installed packages and the real framework preserves invalid-input zero reward |
| D5 | Bounded dataset demonstration | Three supported GSM8K development contracts, one known public-test example and two explicit exclusions are bound to question provenance; same-context review and lack of independent evaluation are disclosed |
| D6 | Current native evidence | Healthy Lean 4.23.0 executes both live suites, six positive/negative controls, procedural/dataset differential controls and the installed-wheel native gate with no acceptance mismatch or operational error |

**Source delivery is complete when D1–D5 pass. Validated delivery is complete
when D1–D6 pass.** New release/Hub publication is eligible only after D6 passes.
This distinguishes completed source work from an unavailable execution gate;
neither an unavailable compiler nor skipped integrations can count as D6.

The present source delivery passes D1–D5. D6 is the single remaining validation
gate: this VM execution surface lacks `/proc`, so stock Lean startup and
bubblewrap fail. Earlier GitHub jobs were blocked by account billing; latest
candidate jobs started no steps. Package installation alone cannot fix those
runtime/account conditions. Native evidence for the earlier public release
does not substitute for checking this candidate.

## One closeout command

In a dedicated environment with the Engine/RL sources and
`requirements-release.lock` installed:

```sh
python scripts/closeout_gate.py \
  --verifier-root ../mathcheck-engine \
  --output artifacts/closeout-20261003 \
  --toolchain /absolute/path/to/read-only-lean-4.23.0-linux \
  --toolchain-sha256 cbf5fd536e142ef1beaccf33f788fd8a7f3f29fb214e75c11319a8d8677b4b2b
```

The output directory must be new. The command runs source suites, builds four
wheels, resolves dependencies in a fresh consumer environment and checks
installed artifacts. If native startup works, it runs the finite D6 checklist
and full release gate. If not, it writes an explicit blocked result. It does
not start model inference, training, publish artifacts or change accounts.

| Exit | Meaning |
| --- | --- |
| 0 | Source and current native validation complete; release eligible |
| 1 | A required check failed; fix the reported defect before closing |
| 2 | Source delivery complete; native validation blocked or not requested |

`closeout.json` binds wheel hashes, check statuses, logs and execution-script
hashes. Logs retain test skips and failures. Omitting both toolchain arguments
permits a source-only check and always yields exit 2 when source checks pass.
That mode is explicitly not the native release gate.

The Engine integration follow-up binds the Hub to immutable Engine and RL core
commits and preserves its fresh source/artifact report in
`docs/evidence/engine-integration-20261003/closeout.json`. The native candidate
workflow also runs when the Hub's `pyproject.toml` changes on `main`. Its Linux
result, not the trigger or source-only report, must satisfy D6.

## Work outside this finish line

The existing optional GRPO driver and protocol remain available, but a model
choice, pretrained checkpoint, training run, measured learning gain, GPU run,
transfer benchmark or statistical study is **not required** for this delivery.
Automatic LLM formalization, rational/real/geometry contracts, broader dataset
coverage and independent dataset research evaluation are separate projects.
They begin only when explicitly requested; this audit will not keep expanding
to include them.

Independent fidelity review remains necessary before making an independent
dataset-evaluation claim. The four disclosed demonstration tasks make no such
claim, so external review does not keep their bounded demonstration open.
The same-context semantic audit is recorded in `GSM8K_SPEC_AUDIT.md`.

An exposed credential's revocation/cutover is unconfirmed owner-controlled
account work. Local remotes are clean, no secret is in delivered artifacts, and
no credential/quota changes are made by this gate. That item stays visibly
unconfirmed rather than turning into recurring implementation work.

After D6 passes and requested distribution updates are published, stop. A
future bug report can reopen a specific defect; new capabilities and experiments
require a new scope.
