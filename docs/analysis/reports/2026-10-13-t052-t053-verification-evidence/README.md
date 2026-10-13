# T-052 / T-053 verification evidence — 2026-10-13

Original snapshots were captured during content implementation before canonical review publication. They remain immutable; metadata records their source and scope. No new Cargo/QEMU/Miri/coverage/hosted or reproducibility run is claimed.

- [scope-baseline.json](scope-baseline.json): 470 historical subjects/75 captured scope strings at Step 8 baseline; combined strings are data, not an allowlist.
- [downstream-baseline.txt](downstream-baseline.txt): all 141 broad baseline lines, not a defect count.
- [downstream-after-content.txt](downstream-after-content.txt): exact 73-line post-edit search output.
- [downstream-search-method.json](downstream-search-method.json): source, argv and provenance for both searches; patterns intentionally differ.
- [initial-static-verification.json](initial-static-verification.json): 19-path pre-report snapshot, 15 unchanged source digests, lints/tests/fences/task counts/policy checks.
- [initial-navigation-verification.json](initial-navigation-verification.json): bounded existing third-party parser diagnostic at the 367-file snapshot, not future T-056 grammar proof.
- [retained-report-manifest.json](retained-report-manifest.json): exact final report byte counts/SHA-256, retained once verbatim in canonical reports.
- [publication-verification.json](publication-verification.json): separate later coordinator scope/retention/lifecycle/navigation checks.

[Reconciliation](../2026-10-13-t052-t053-standards-reconciliation.md), [preflight](../2026-10-13-t052-t053-standards-preflight.md), [code](../../reviews/code-reviews/2026-10-13-t052-t053-standards-reconciliation.md) and [security](../../reviews/security-reviews/2026-10-13-t052-t053-standards-reconciliation.md) preserve initial verdicts and actual later cross-read chronology. Both tasks stop In Review without date_done. Original evidence does not become an execution of later publication content.
