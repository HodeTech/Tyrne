# T-055 verification evidence — 2026-10-13

These checks execute the implementation working tree based on e8104e3, before its commit. Metadata records the exact base HEAD, dirty state, two rustdoc-file hashes, command argv/cwd/UTC intervals/exits, installed Rust/Cargo identities and raw stream SHA-256/bytes. No QEMU/Miri/coverage run is newly claimed. Runtime tokens are separately compared unchanged; these required host checks verify comment/lint/documentation compatibility, not a new runtime feature.

- [metadata.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t055-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t055-verification-evidence/metadata.json")
- [index-baseline.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t055-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t055-verification-evidence/index-baseline.json"): exact source headers and initial index differences for all 42 records.
- [fmt.stdout.log](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t055-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t055-verification-evidence/fmt.stdout.log")
- [fmt.stderr.log](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t055-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t055-verification-evidence/fmt.stderr.log")
- [host-clippy.stdout.log](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t055-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t055-verification-evidence/host-clippy.stdout.log")
- [host-clippy.stderr.log](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t055-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t055-verification-evidence/host-clippy.stderr.log")
- [host-test.stdout.log](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t055-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t055-verification-evidence/host-test.stdout.log")
- [host-test.stderr.log](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t055-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t055-verification-evidence/host-test.stderr.log")

Raw streams are retained without normalization, including intentionally empty captures. See the [reconciliation report](../2026-10-13-t055-adr-correction-reconciliation.md) and [preflight scope](../2026-10-13-t055-adr-correction-preflight.md). The original snapshot precedes both fresh implementation-review rounds; later checkpoints are recorded separately below.

- [static-verification.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t055-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t055-verification-evidence/static-verification.json"): preservation/index/raw-hash checks at the implementation snapshot.
- [navigation.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t055-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t055-verification-evidence/navigation.json"): bounded existing-parser diagnostic, distinct from the future stdlib T-056 implementation.

- [r1-correction-verification.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t055-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t055-verification-evidence/r1-correction-verification.json"): post-fix checks, original-capture binding and separate corrected source hashes; immutable initial evidence is preserved.

**Later canonical boundary:** both fresh rounds complete, T-055 In Review. [Code](../../reviews/code-reviews/2026-10-13-t055-adr-corrections.md) and [security](../../reviews/security-reviews/2026-10-13-t055-adr-corrections.md) preserve all actual reports. Original captures/snapshots remain immutable and separate from later publication checks; no additional runtime execution is implied.

- [publication-verification.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t055-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t055-verification-evidence/publication-verification.json"): separate canonical retention/scope/lifecycle/preservation and bounded navigation checks; original snapshots are unchanged.

> **Evidence migration (2026-10-16).** Raw evidence links now open the [immutable archive catalog](../2026-10-16-pr49-evidence-catalog.md). Each link title retains its exact archived member path. Original verdicts, measurements, limitations and execution SHA identities remain historical; the archive bundle restores their original source.
