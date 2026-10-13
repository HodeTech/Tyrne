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

Raw streams are retained without normalization, including intentionally empty captures. See the [reconciliation report](../2026-10-13-t055-adr-correction-reconciliation.md) and [preflight scope](../2026-10-13-t055-adr-correction-preflight.md). Both fresh implementation-review rounds remain pending.

- [static-verification.json](static-verification.json): preservation/index/raw-hash checks at the implementation snapshot.
- [navigation.json](navigation.json): bounded existing-parser diagnostic, distinct from the future stdlib T-056 implementation.
