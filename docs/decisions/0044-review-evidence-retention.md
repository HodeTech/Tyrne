# 0044 — Review evidence retention and delivery

- **Status:** Accepted
- **Date:** 2026-10-16
- **Deciders:** @cemililik

## Context

PR #49 at 97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4 has 956,905 additions and 3,003 deletions across 1,008 files. Non-Markdown report payloads account for 804 files, 927,770 additions and 134,293,614 current-tree bytes. They include intermediate results, complete source exports and encoded reviewer scratch archives, including copies of earlier archives. The current evidence delivery makes the implementation unnecessarily difficult to review and retain in Git.

ADR-0043 requires truthful, attributable historical evidence and complete checking of the public Markdown corpus. It does not require every execution stream or temporary source export to reside in the source repository. Historical review verdicts, severities, failed-before observations, procedural limitations and actual source identities must survive this migration. GitHub Actions retention is time-limited and cannot be the sole durable archive.

The maintainer approved the external proposal and bounded migration plan on 2026-10-16. This initial filing remains Proposed pending deliberate reread and both fresh independent review rounds; Acceptance is a separate commit. The approved plan is [PR #49 evidence cleanup](../analysis/reports/2026-10-16-pr49-evidence-cleanup.md).

## Decision drivers

- Keep production source, regression fixtures and readable decision/review records reviewable in Git.
- Preserve every migrated byte and the original source history before removing payloads.
- Keep source identities honest when commit hashes change.
- Limit the migration to this unmerged development sequence; preserve main and every unrelated ref.
- Prevent recurrence without adding a required status context or broadening CI permissions.

## Considered options

1. Keep payloads in Git and only change rendering or formatting.
2. Move payloads to a durable archive and add a normal cleanup commit; keep development history.
3. Move payloads to a durable archive and additionally remove only those payload paths from the unmerged development history.
4. Adopt Git LFS for payloads and migrate the corresponding history.

## Decision outcome

Maintainer-approved choice: **option 3**, pending the separate Acceptance commit before implementation.

Keep the six checker/fixture files, runtime source, CI behavior, filed ADRs, all canonical Markdown review/analysis records, and a compact evidence catalog in Git. Move the exact 804 enumerated non-Markdown report paths to a durable, digest-verified archive. Preserve both their final bytes and all previous source/evidence revisions using a self-contained Git bundle of the pre-rewrite development tip, including original `97dbcd1` and approved governance commits. Create the later in-Git catalog after that bundle freezes so its hash is not self-referential. This is storage relocation, not evidence destruction or a new test result.

Use a GitHub evidence release plus an independent local archive outside the Git working tree. Enable repository release immutability before publishing, subject to this explicit approval. Build the release as a draft, upload all assets, verify a complete download, then publish and verify immutability. Tag the already-clean main anchor c16997e003fbd1726d1205734380394781c52002; never tag the bloated development tip. Label the release as evidence, prerelease and not latest. Its manifest identifies the original development source independently of its clean tag anchor. If durable publication, immutability or recovery verification fails, do not delete payloads or rewrite refs.

This is an evidence-only hosting profile under [the release standard](../standards/release.md), not a Tyrne product-version release. It declares no kernel version, bootable image, supported-target/ABI guarantee, changelog milestone or first product release. Its integrity/provenance contract is immutable hosted bytes, published SHA-256 digests, explicit original source identities and tested independent recovery; it makes no maintainer-key signature assertion. Product-version release gates and signing requirements remain mandatory for product releases. T-056 adds the narrow matching release-standard scope pointer after Acceptance and before archive publication.

The catalog records schema version, archive URL, asset IDs, SHA-256/size, original source/run identities, logical paths, recovery instructions and the original-to-rewritten commit map. The full per-file catalog is an archive asset; the in-Git catalog stays at most 128 KiB. Existing historical SHA literals remain original execution identities; do not mechanically replace them with new hashes or claim that the new commit was historically executed. Supply a dated migration notice and explicit source-recovery mapping. Original Markdown snapshots are in the bundle; live citation-target edits are dated and do not change findings, verdicts, measurements or reading limits. Append-only performance narratives stay intact; use adjacent migration pointers where appropriate.

Introduce a separate offline repository-footprint check in the existing lint job. Do not change check-docs.py's no-Git/offline contract. Proposed hard limits are: 1 MiB per tracked blob, 512 KiB in total for non-Markdown content under docs/analysis/reports/, and 128 KiB for the evidence catalog. Bulk source snapshots and encoded scratch archives belong in the artifact archive. Any future exception must be exact-path, reasoned and reviewed; no whole-directory bypass. Existing eight-family docs checks, job names, six required app-15368 contexts and branch protection remain intact. No administrative credential is added to CI; archive publishing is an explicitly authorized maintainer operation.

After the decision is Accepted, prepare a trial rewrite and its commit map in isolation, archive and verify that frozen original history, and only then apply the rewrite locally. New maintenance implementation/review commits are made after the local rewrite and are not rewritten again. Publish no intermediate broken citation state.

For this one migration, filter only the enumerated payload paths from `c16997e..the-frozen-development-tip` in an isolated copy. Keep meaningful commit ordering and produce a commit map; pure evidence-only commits may become empty. Do not rewrite main or unrelated branches/tags. Recheck exact source/ref identities before a single development-only force-with-lease publication. A lease mismatch stops publication. No standing future force-push authorization is created. GitHub hidden PR refs/caches may retain old objects; server-side physical erasure is not promised.

### Simulation

Not applicable — this ADR settles a process/storage policy, not a kernel state machine. Migration checkpoints and rollback gates are specified in the implementation plan.

### Dependency chain

1. Existing [T-049](../analysis/tasks/phase-b2/T-049-review-indices-sync.md): approved maintenance followup owns historical evidence/citation reconciliation and verified lossless archive/recovery.
2. Existing [T-056](../analysis/tasks/phase-b2/T-056-docs-consistency-automation.md): approved maintenance followup owns the separate footprint check, existing required-job wiring, narrow development-history migration and validation, including minimal retention guidance and the evidence-only release-standard scope pointer before publication. Its followup criteria must be recorded before implementation; reopen In Progress only during actual work, then return In Review.
3. Existing [T-047](../analysis/tasks/phase-b2/T-047-roadmap-state-and-phase-index-sync.md): maintain correct current-state pointers, task census and final PR evidence. No new phase task count or T-038 implementation is introduced.
4. Accepted ADR-0043 remains the whole-corpus and reviewed-execution authority. This ADR adds storage delivery constraints without superseding its navigation or evidence-attribution rules. Proposal and Acceptance remain separate commits under ADR-0025; standards/CI changes follow actual Acceptance and maintainer approval.

## Consequences

### Positive

- Initial projection falls to 204 changed files and 29,135 additions before migration edits and policy tooling.
- The original source and all 804 payloads remain recoverable by their original identities.
- Default published branch history no longer carries those payload paths; future excess is caught in CI.

### Negative

- History rewriting changes descendant commit identities. Mitigation: verified original bundle, source-equivalence checks, explicit commit map and fresh final-tip CI.
- Force publication and collaborator reconciliation require care. Mitigation: clean-tree checks, exact-tip lease, no other ref changes and no merge of old development ancestry back into the rewritten line.
- Durable storage relies on a hosted release and an independent offline copy. Mitigation: digest verification, immutable asset verification and tested restoration before removal.
- A one-time pinned maintenance tool may be needed outside project dependencies. Verify its primary-source version/checksum before use; do not add it to runtime or default CI dependencies.

### Neutral

- GitHub backend object retention and immediate repository-size accounting are outside this migration's guarantees.
- All twelve B.2-2 tasks stop In Review; maintainer SECURITY wording review and PR merge remain separate.
- Original approval/review/execution assertions remain historical; migration does not backdate new validation.

## Pros and cons of the options

### Option 1

- Pro: source hashes and history stay unchanged.
- Con: retains the observed review/storage cost; formatting changes do not remove payload bytes.

### Option 2

- Pro: small PR diff with no force push; squash merge can keep old unmerged commits out of main ancestry.
- Con: default clones still fetch old development history while it remains a published branch; it does not achieve the branch-history cleanup goal.

### Option 3

- Pro: addresses both visible PR size and published development ancestry, preserving meaningful changes and a full original archive.
- Con: needs explicit one-time history approval, commit-map reconciliation and complete post-rewrite validation.

### Option 4

- Pro: purpose-built out-of-line object storage.
- Con: adds contributor/tooling/storage obligations and still requires handling existing Git history. A source-delivery dependency is unnecessary for archived review streams.

## References

- [ADR-0025 — ADR governance amendments](0025-adr-governance-amendments.md)
- [ADR-0043 — Documentation corpus consistency](0043-documentation-corpus-consistency.md)
- [Git bundle documentation](https://git-scm.com/docs/git-bundle)
- [git-filter-repo primary documentation](https://github.com/newren/git-filter-repo/blob/main/Documentation/git-filter-repo.txt)
- [GitHub immutable releases](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes)
- [GitHub Actions retention](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)
