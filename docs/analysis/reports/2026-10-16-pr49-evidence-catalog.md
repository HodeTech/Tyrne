# Recover PR #49 review evidence

Readers of historical review/task records can recover exact raw evidence and original source from the verified immutable archive. Canonical Markdown reports remain in Git; their findings, verdicts, measurements, procedural limits and original execution SHA identities are preserved.

## Archive and source identities

The [evidence-only release](https://github.com/HodeTech/Tyrne/releases/tag/evidence-pr-49-2026-10-16) is immutable, prerelease and not latest. Its tag anchors clean main `c16997e`; GitHub's automatic source ZIP/tar describes that main anchor. Use the attached **pre-rewrite-development.bundle** for original development. No Tyrne product version or maintainer-key signature is asserted.

Original executed PR tip: `97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4`. Governance-inclusive archive tip: `6c84f0d51820f858b31789ad51ecb612ed74e186`. Trial filtered tip: `32bdc16e4f19a654fda19abc202d3b4ad496d406`. The [compact machine catalog](2026-10-16-pr49-evidence-catalog.json) pins every asset ID, size and SHA-256 and all 151 commit mappings. An all-zero new hash denotes the one removed evidence-only commit. Later maintenance commits are not rewritten by this map.

Historical SHA literals remain original execution identities. A mapped commit is not a claim that a historical test ran on the mapped hash. Restore the bundle and use `git show <original-sha>:<path>` for original evidence, including reports whose live navigation was migrated. The [recovery guide](../../guides/review-evidence.md) provides tested commands and contributor synchronization guidance.

## Verified assets

All nine assets were downloaded without repository credentials after publication, digest checked, and used to recover the complete old source plus all 804 payloads (134,293,614 bytes). The recovered bundle passes full Git integrity checks. This does not promise GitHub hidden-ref/cache erasure.

| Asset | Bytes | SHA-256 |
|---|---:|---|
| [SHA256SUMS](https://github.com/HodeTech/Tyrne/releases/download/evidence-pr-49-2026-10-16/SHA256SUMS) | 678 | `516025119ccb184a22b8c64719d20e4f522b60daafb6178393b921c5384e5b93` |
| [candidate-files.json](https://github.com/HodeTech/Tyrne/releases/download/evidence-pr-49-2026-10-16/candidate-files.json) | 201510 | `84b694430893470c42558f24f74e396a2eb3eb185dc26b4ccc3a6e417118eb19` |
| [commit-map.txt](https://github.com/HodeTech/Tyrne/releases/download/evidence-pr-49-2026-10-16/commit-map.txt) | 12427 | `8a768c3f5158efc8a7cb6cf8a2d9d95eb92237574cdb151b3fcac226a977888e` |
| [manifest.json](https://github.com/HodeTech/Tyrne/releases/download/evidence-pr-49-2026-10-16/manifest.json) | 1447 | `e16420553ed7ec8b5f6903eb81a84a7945ed818a5c650607fb86ea3ca7cb6320` |
| [payloads.tar.gz](https://github.com/HodeTech/Tyrne/releases/download/evidence-pr-49-2026-10-16/payloads.tar.gz) | 66475418 | `032b586ec81c38d37d45f5076c628707a3b35484da4388499f1d9896c44e3117` |
| [pre-rewrite-development.bundle](https://github.com/HodeTech/Tyrne/releases/download/evidence-pr-49-2026-10-16/pre-rewrite-development.bundle) | 63861764 | `4a1bd4f426eddb9301062a5a8f136311983ef7a1cf342f1535d4133ca6e7c73c` |
| [provenance.tar.gz](https://github.com/HodeTech/Tyrne/releases/download/evidence-pr-49-2026-10-16/provenance.tar.gz) | 716265 | `eeea6dd85889480d9a6841784c58afa0ec2073267f4d0f811bceaebb0b0f1587` |
| [recovery.txt](https://github.com/HodeTech/Tyrne/releases/download/evidence-pr-49-2026-10-16/recovery.txt) | 3408 | `1ad0ebdf695b669ed1271c9143d261278982e0a709e1e03ad373d5c957ae0b98` |
| [trial-validation.json](https://github.com/HodeTech/Tyrne/releases/download/evidence-pr-49-2026-10-16/trial-validation.json) | 1169 | `bad883f58ef929cfa5d60398c678d91fd0d09638da6e68a4f20a6cbace01d92a` |

## Find an archived member

Each migrated link title gives its full original repository member path. The [full per-file manifest](https://github.com/HodeTech/Tyrne/releases/download/evidence-pr-49-2026-10-16/candidate-files.json) contains all paths, sizes and SHA-256 values. Download payloads.tar.gz and inspect that member with the recovery guide. Older revisions remain in the Git bundle.

<a id="dataset-2026-10-13-t045-architecture-evidence"></a>

### 2026-10-13-t045-architecture-evidence

7 archived files, 13260 bytes. Use the link title's exact member path and the full manifest; the archive preserves every original byte.

<a id="dataset-2026-10-13-t047-verification-evidence"></a>

### 2026-10-13-t047-verification-evidence

7 archived files, 39314 bytes. Use the link title's exact member path and the full manifest; the archive preserves every original byte.

<a id="dataset-2026-10-13-t049-review-evidence"></a>

### 2026-10-13-t049-review-evidence

7 archived files, 763979 bytes. Use the link title's exact member path and the full manifest; the archive preserves every original byte.

<a id="dataset-2026-10-13-t050-entry-document-evidence"></a>

### 2026-10-13-t050-entry-document-evidence

17 archived files, 23487 bytes. Use the link title's exact member path and the full manifest; the archive preserves every original byte.

<a id="dataset-2026-10-13-t052-t053-verification-evidence"></a>

### 2026-10-13-t052-t053-verification-evidence

8 archived files, 111524 bytes. Use the link title's exact member path and the full manifest; the archive preserves every original byte.

<a id="dataset-2026-10-13-t054-verification-evidence"></a>

### 2026-10-13-t054-verification-evidence

11 archived files, 165130 bytes. Use the link title's exact member path and the full manifest; the archive preserves every original byte.

<a id="dataset-2026-10-13-t055-verification-evidence"></a>

### 2026-10-13-t055-verification-evidence

12 archived files, 59971 bytes. Use the link title's exact member path and the full manifest; the archive preserves every original byte.

<a id="dataset-2026-10-13-t056-parser-evidence"></a>

### 2026-10-13-t056-parser-evidence

473 archived files, 21792904 bytes. Use the link title's exact member path and the full manifest; the archive preserves every original byte.

<a id="dataset-2026-10-15-phase-b2-track2-final-evidence"></a>

### 2026-10-15-phase-b2-track2-final-evidence

19 archived files, 2152075 bytes. Use the link title's exact member path and the full manifest; the archive preserves every original byte.

<a id="dataset-2026-10-15-t056-integration-evidence"></a>

### 2026-10-15-t056-integration-evidence

243 archived files, 109171970 bytes. Use the link title's exact member path and the full manifest; the archive preserves every original byte.

## Generation and policy

Generated by the archived `migrate-citations.py` plus the [reproducible correction](2026-10-16-pr49-evidence-migration.md); both original and corrected script digests are bound in the machine catalog. It used the production Markdown reader, changed 348 recognized destinations in 46 documents, added exact member titles and dated notices, and verified exact reversal to each original document. No historical SHA or verdict text was replaced. [ADR-0044](../../decisions/0044-review-evidence-retention.md) governs storage; [ADR-0043](../../decisions/0043-documentation-corpus-consistency.md) retains corpus/attribution authority.
