# T-055 verification evidence — 2026-10-13

These checks execute the implementation working tree based on e8104e3, before its commit. Metadata records the exact base HEAD, dirty state, two rustdoc-file hashes, command argv/cwd/UTC intervals/exits, installed Rust/Cargo identities and raw stream SHA-256/bytes. No QEMU/Miri/coverage run is newly claimed. Runtime tokens are separately compared unchanged; these required host checks verify comment/lint/documentation compatibility, not a new runtime feature.

- [metadata.json](metadata.json)
- [index-baseline.json](index-baseline.json): exact source headers and initial index differences for all 42 records.
- [fmt.stdout.log](fmt.stdout.log)
- [fmt.stderr.log](fmt.stderr.log)
- [host-clippy.stdout.log](host-clippy.stdout.log)
- [host-clippy.stderr.log](host-clippy.stderr.log)
- [host-test.stdout.log](host-test.stdout.log)
- [host-test.stderr.log](host-test.stderr.log)

Raw streams are retained without normalization, including intentionally empty captures. See the [reconciliation report](../2026-10-13-t055-adr-correction-reconciliation.md) and [preflight scope](../2026-10-13-t055-adr-correction-preflight.md). The original snapshot precedes both fresh implementation-review rounds; later checkpoints are recorded separately below.

- [static-verification.json](static-verification.json): preservation/index/raw-hash checks at the implementation snapshot.
- [navigation.json](navigation.json): bounded existing-parser diagnostic, distinct from the future stdlib T-056 implementation.

- [r1-correction-verification.json](r1-correction-verification.json): post-fix checks, original-capture binding and separate corrected source hashes; immutable initial evidence is preserved.

**Later canonical boundary:** both fresh rounds complete, T-055 In Review. [Code](../../reviews/code-reviews/2026-10-13-t055-adr-corrections.md) and [security](../../reviews/security-reviews/2026-10-13-t055-adr-corrections.md) preserve all actual reports. Original captures/snapshots remain immutable and separate from later publication checks; no additional runtime execution is implied.

- [publication-verification.json](publication-verification.json): separate canonical retention/scope/lifecycle/preservation and bounded navigation checks; original snapshots are unchanged.
