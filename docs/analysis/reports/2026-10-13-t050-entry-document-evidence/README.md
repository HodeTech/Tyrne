# T-050 retained build and QEMU evidence — 2026-10-13

All six commands executed an isolated tracked-source export of clean `development` at `75de2ba90e151bae33e14d2db4a8278837e7775d`, before entry-document edits. The export initially contained neither target/ nor hello.bin; machine toolchains/Cargo caches were reused. It is a generated-artifact-free source check, not a new-machine installation or network reproducibility test. No Git branch/worktree was created or switched.

Metadata records exact argv, cwd, UTC intervals, process exits, tool identities, seven relevant unset environment overrides, stream SHA-256/bytes and each profile’s raw-QEMU/ELF/raw-image identities. Raw output is unnormalized; empty stdout captures are intentional. QEMU is timeout-terminated after successful completion because Task A spins. No compiled binary, target directory or source tar is retained here; the source archive digest is metadata.

- [debug-kernel.stderr.log](debug-kernel.stderr.log)
- [debug-kernel.stdout.log](debug-kernel.stdout.log)
- [debug-smoke.stderr.log](debug-smoke.stderr.log)
- [debug-smoke.stdout.log](debug-smoke.stdout.log)
- [debug-userland.stderr.log](debug-userland.stderr.log)
- [debug-userland.stdout.log](debug-userland.stdout.log)
- [debug.qemu.log](debug.qemu.log)
- [glossary.json](glossary.json)
- [verification.json](verification.json): coordinator working-tree contract/navigation checks, distinct from executed-source runtime metadata.
- [metadata.json](metadata.json)
- [release-kernel.stderr.log](release-kernel.stderr.log)
- [release-kernel.stdout.log](release-kernel.stdout.log)
- [release-smoke.stderr.log](release-smoke.stderr.log)
- [release-smoke.stdout.log](release-smoke.stdout.log)
- [release-userland.stderr.log](release-userland.stderr.log)
- [release-userland.stdout.log](release-userland.stdout.log)
- [release.qemu.log](release.qemu.log)

The glossary ledger separately records 50 → 54 headwords, four additions, all stable IDs, the two pure-ordering moves/grouping exception and 27 source-corrected existing definitions. It is document metadata, not runtime evidence. See the [verification report](../2026-10-13-t050-entry-document-verification.md) and [preflight source map](../2026-10-13-t050-entry-document-preflight.md). Both fresh implementation-review rounds remain pending.

**Later review boundary (2026-10-13):** the pending snapshot above is superseded by both completed fresh rounds; T-050 is In Review. [Canonical code](../../reviews/code-reviews/2026-10-13-t050-entry-document-refresh.md) and [security](../../reviews/security-reviews/2026-10-13-t050-entry-document-refresh.md) preserve actual delivered outcomes. Raw captures/metadata/glossary.json/verification.json remain unchanged; no later runtime execution is implied.
