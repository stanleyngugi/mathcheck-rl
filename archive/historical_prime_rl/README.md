# Historical Prime-RL experiments

This directory preserves the August 2026 single-GPU Prime-RL experiment for
provenance. It is not a supported installation or launch surface for MathCheck
RL, and its commands contain historical absolute paths and assumptions that
must not be applied to a current machine without a fresh review.

The archive contains:

- `scripts/`: 161 incremental pod setup, debugging, and launch scripts;
- `configs/`: three historical GRPO configurations;
- `patches/`: logs plus modified full-file Prime-RL snapshots;
- `docs/`: the old agent handoff, pod runbook, curriculum, and operations course.

Historical references such as `scripts/pod_*.sh`, `configs/grpo_*.toml`, and
`patches/prime-rl/*.py` are relative to the old repository root. Their preserved
locations now have the prefix `archive/historical_prime_rl/`. They have not been
rewritten because doing so would make the record look like a current recipe.

No archived file is imported by the Python packages or included by setuptools.
See the repository root `THIRD_PARTY_NOTICES.md` before reusing upstream-derived
files.
