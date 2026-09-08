# Bounded verifier/native correction ledger

Prepared from `VERIFICATION_RL_AGENT_HANDOFF.md`. “Done” means the listed bounded
condition is implemented and regression-tested; it is not a claim that every
possible defect is eliminated.

| ID | Severity | Reproduced defect | Bounded correction | Done condition | Status |
|---|---|---|---|---|---|
| F1 | high | A function correct only below the fixed cutoff earned reward despite “any n” wording | State the exact finite range and widen hidden boundary ranges | Prompts and docs call the contract finite; cutoff control is no longer misreported as universal | done |
| F2 | high | Default train/eval had repeated prompts and four overlaps | Parameterize low-cardinality families, deduplicate, and exclude train digests from eval | Default 40/10 split has unique disjoint mathematical digests | done |
| F3 | critical | Indented `abbrev` bypassed the defs-only scan | Scan declaration tokens independent of indentation; reject non-`def`, qualified names, and unterminated comments | Original bypass and related controls reject before Lean | done |
| F4 | critical | Native runner used a temp directory but no OS sandbox | Require shared `lean-isolated` and remove host/retired fallback | Missing or non-wrapper configuration fails closed | done |
| F5 | high | v1 reward and metric could compile the same rollout twice | Exact-input async single-flight cache | Concurrent same-key requests invoke the verifier once; changed keys do not reuse | done |
| F6 | high | Version/dependency/import contracts were broad or silent | Require Lean 4.23.0 exactly; declare verifier/framework dependencies; expose v0-only fallback explicitly | Fresh wheel/environment smoke passes or fails with a clear unsupported surface | done |
| F7 | high | Failure stages conflated math and infrastructure | Add explicit status and digest-bound evidence | Timeout/backend failure cannot become `mathematical_rejection` or reward | done |
| F8 | medium | Batch evaluation overwrote output and hid retry accounting | Exclusive output, explicit attempts, fsync, manifest/trial/terminal records | Existing files are refused and terminal accounting is durable | done |
| F9 | medium | README/roadmap/config claims contradicted preserved evidence | Rewrite active docs around the two contracts and bounded milestone status | Current docs no longer claim universality, automatic sandboxing, or demonstrated learning | done |
| F10 | critical | Native Git remote contains an exposed embedded credential | Revoke/rotate with owner, then use a clean URL and credential manager/SSH | Provider confirms revocation and local remote no longer embeds a secret | owner action required |

Deferred outside this bounded implementation: arbitrary prose formalization,
production multi-tenant isolation/cgroups, new GPU training, checkpoint recovery,
and publication. None is needed to interpret the completed local contracts.
