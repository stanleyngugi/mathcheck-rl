# Native closeout evidence

The unchanged joint closeout gate passed on 2026-10-05 under hardware-accelerated
QEMU WHPX. `closeout.json` is the gate's unmodified report. The adjacent stage
logs and JSONL controls are the complete output set (excluding disposable
consumer virtual environments and pytest temporary files). The manifest records
the reproducible, locked four-wheel build hashes. `environment.json` records
the host accelerator, guest setup, exact source commits, toolchain provenance,
test results and the sole optional training-module skip, also detailed in
`optional-training-skip.json`.

The four candidate wheels are present in `native-release/` and repeated in
`wheels/`; the gate independently rebuilt them and verified identical hashes.
The duplicate wheel files are kept with this local evidence directory for
release upload convenience; the evidence commit publishes the report, logs,
environment record and manifest. GitHub release assets carry the validated
distribution wheels.
