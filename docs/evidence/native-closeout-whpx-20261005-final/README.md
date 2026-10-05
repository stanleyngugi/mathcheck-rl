# Native closeout evidence

The unchanged joint closeout gate passed on 2026-10-05 under hardware-accelerated
QEMU WHPX. `closeout.json` is the gate's unmodified report. The adjacent stage
logs and JSONL controls are the complete output set (excluding disposable
consumer virtual environments and pytest temporary files). The manifest records
the reproducible, locked four-wheel build hashes. `environment.json` records
the host accelerator, guest setup, exact source commits, toolchain provenance,
test results and the sole optional training-module skip, also detailed in
`optional-training-skip.json`.
`prime-consumer-whpx.json` retains the successful fresh consumer installation,
`pip check`, installed identity/hash record and native Lean control output for
the independently fetched Prime 0.1.2 wheel.

The gate independently rebuilt all four candidate wheels and verified
identical hashes. The release manifest records those identities; GitHub release
assets carry the validated distribution wheels. The repository evidence commit
preserves the report, logs, environment record, manifest and consumer checks
without duplicating the release binaries.
