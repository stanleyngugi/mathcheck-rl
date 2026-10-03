# Answer-blind GSM8K demonstration

Status: **offline import implemented; independent fidelity review, native
verification and policy evaluation not completed**. This extension was prepared
last, after the current contract, documentation and procedural pilot amendment.
It does not replace that pilot or demonstrate learning improvement.

## What is included

`examples/gsm8k/` binds official source revision
`3101c7d5072418e28b9008a6636bde82a006892c`. The exporter selects source indices
before inspecting question text and projects records into question-only input.
The extraction process necessarily reads upstream records containing solutions;
those fields are discarded before formalization. They were not supplied to the
assistant during this construction and are absent from every imported artifact.
This is a process/provenance statement, not proof that a model's pretraining
never contained these public questions or answers.

The five first official training questions are a **development** slice.
Four have arithmetic contracts. One is explicitly excluded because converting
“a year” into exactly 52 weeks adds a convention not stated in the question.
The first official test question is an **evaluation demonstration**, not a fresh
held-out performance measurement: it was already discussed in the audit.
No source solution or expected candidate is stored in either task manifest.

| Source item | Frozen interpretation | Role |
| --- | --- | --- |
| train:0 | April sales plus half as many May sales: `48+48//2` | Development |
| train:1 | Hourly pay times minutes / minutes per hour: `(12*50)//60` | Development |
| train:2 | Wallet shortfall after savings and both gifts: `100-100//2-15-2*15` | Development |
| train:3 | Half the unread pages after two reading sessions: `(120-12-2*12)//2` | Development |
| train:4 | Year-to-weeks convention unstated | Excluded |
| test:0 | Revenue from eggs left after consumption: `(16-3-4)*2` | Evaluation demonstration |

Division uses the existing integer DSL. The reviewed divisions above are exact
for these instances. An expression requiring rounding, a rational answer or
unstated unit conversion must be excluded or assigned a richer contract;
integer floor division must not silently change the mathematical question.

Codex constructed and reviewed these interpretations from question-only text.
The manifests disclose that this was the **same assistant context**. There is
no independent human/model review claim. Before a research run, obtain separate
review of quantities, units, operation order, domains and the objective, then
freeze a new manifest with that provenance. Future automatic formalizers should
be separated from the solving policy and blind to labels and candidate rollouts.

## Import and control commands

After installing both source projects:

```bash
python scripts/import_gsm8k_specs.py \
  --questions examples/gsm8k/development_questions.jsonl \
  --reviews examples/gsm8k/development_reviews.json \
  --role development --output development-import.json

python scripts/import_gsm8k_specs.py \
  --questions examples/gsm8k/evaluation_demo_questions.jsonl \
  --reviews examples/gsm8k/evaluation_demo_reviews.json \
  --role evaluation_demonstration \
  --exclude-manifest development-import.json --output evaluation-demo-import.json

python scripts/profile_specification_checks.py \
  --import-manifest development-import.json \
  --lean-bin "$NATIVE_VERIFY_LEAN" --output development-native-controls.jsonl
```

Outputs use exclusive creation. `--reference-only` runs Python controls without
claiming native evidence. Control candidates are computed for QA after the spec
is frozen; they are not source answer keys and are not fed to a policy. A
healthy native run must accept correct candidates and reject adjacent wrong
ones. Timing or correctness comparisons require completed native checking.

To reproduce question export, use `scripts/export_gsm8k_questions.py` with the
recorded full revision, split and source indices. Its source-file SHA-256 covers
the upstream JSONL file, and each question has a separate exact-text digest.
The importer rejects source answer/solution fields, missing reviews, mutated
questions, duplicate or excluded specs, mixed source revisions, incompatible
roles and bare answer constants masquerading as arithmetic specifications.
Review attestations remain trusted: these checks do not prove prose fidelity.

`task_from_import_record` supplies a frozen `SpecificationTask` to the same
`verify_specification_submission` function used by the procedural environment.
The default Hub taskset still generates procedural families. Dataset training
integration is a subsequent step, not an implemented hosted trainer feature.

## Training, development and held-out use

[Official GSM8K](https://github.com/openai/grade-school-math) has 7,473 training
and 1,319 test examples; it provides no separate development split. Reserve a
question-disjoint subset of official training for development. Keep official
test evaluation-only, including formalization feedback and parameter selection.
The importer rejects assigning official test questions to training. For a
held-out study, pass every training/development manifest as an exclusion when
constructing the evaluation manifest; inspect semantic overlap as well as exact
digests. Public test availability still leaves pretraining contamination open.

Eligibility is itself a measurement. Record every selected question as either a
reviewed supported contract or an explicit exclusion. Report coverage and
fidelity review separately from solver pass rate. An unsupported formalization
is not a wrong solver answer. Four successes in this deliberately small
arithmetic slice would not establish whole-dataset coverage or broad reasoning.
Source answer labels, if later consulted for QA, must be disclosed as a later
validation stage and must never be used to manufacture the reward specification.
