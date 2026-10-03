# Dataset roles and contract eligibility

A dataset split is an upstream convention; its role in our experiment must also
be frozen. Training changes policy weights, development changes design choices,
and held-out evaluation measures the chosen policy/design. Feedback from an
upstream test split can make it development data in our study. Public tests may
also have appeared in model pretraining.

| Dataset | Public splits | Appropriate role here | Present contract limits |
| --- | --- | --- | --- |
| [GSM8K](https://github.com/openai/grade-school-math) | 7,473 train; 1,319 test | Train plus dev carved from train; official test reserved | Reviewed integer arithmetic subset; not full coverage |
| [MATH](https://arxiv.org/abs/2103.03874) | 7,500 train; 5,000 test | Later training and separately frozen evaluation | Many symbolic, geometric and proof questions unsupported |
| [MATH-500](https://huggingface.co/datasets/HuggingFaceH4/MATH-500) | 500 test | Evaluation subset, not independent of MATH test | Same limitations; prevent parent/subset overlap |
| [DeepMath-103K](https://huggingface.co/datasets/zwhe99/DeepMath-103K) | 103,022 train | Future large training source; create dev separately | Advanced questions mostly need richer contracts |
| [NuminaMath 1.5](https://huggingface.co/datasets/AI-MO/NuminaMath-1.5) | 896,215 train | Future training source with source-overlap audit | Mixed question types; select by faithfully representable contract |
| [GSM-Symbolic](https://huggingface.co/datasets/apple/GSM-Symbolic) | Test variants of source templates | Stress evaluation; group by original/template ID | Template variants are correlated; check terms before reuse |
| [Omni-MATH](https://huggingface.co/datasets/KbsdJames/Omni-MATH) | 4,428 test | Later difficult evaluation | Olympiad mathematics largely outside current DSL |
| [miniF2F](https://github.com/openai/miniF2F) | 244 validation; 244 test | Proof-synthesis evaluation with a pinned compatible Lean port | Target statements/proof outputs are a different interface |
| [LeanDojo benchmark](https://leandojo.org/) | Formal-library training/evaluation splits | Future proof-synthesis research | Library premise separation is not word-problem answer checking |

Keep split conventions explicit. OpenAI's PRM800K uses a nonstandard MATH
12,000/500 partition; combining it with the original MATH 7,500/5,000 convention
can contaminate evaluation. Numina sources can overlap GSM8K/MATH, so upstream
train labels alone do not establish independence from our chosen tests.

Current priorities remain the procedural instrument and pilot first, the small
[GSM8K demonstration](GSM8K_DEMONSTRATION.md) last, then any broader import.
No dataset supplies faithful checker specifications merely because it supplies
questions and solutions. Construct specs from questions, disclose review and
label access, freeze accepted contracts, and count unsupported items separately.
