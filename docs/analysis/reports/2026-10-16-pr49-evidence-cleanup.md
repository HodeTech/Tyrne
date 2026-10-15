# PR #49 evidence cleanup — approval package

Maintainer approved option B and the attached ADR policy on 2026-10-16. This record preserves the measured 2026-10-15 baseline and execution gates. Implementation and publication are recorded incrementally below; approval alone does not claim delivery.

## Frozen analysis basis

- Repository: HodeTech/Tyrne, public; PR49 development → main.
- Main: c16997e003fbd1726d1205734380394781c52002.
- Development: 97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4; clean and equal to origin/development.
- PR: 1,008 changed files, +956,905 / -3,003.
- Candidate migration: exactly804 non-Markdown report files introduced in this PR,134,293,614 current-tree bytes,+927,770 lines. No extra historical-only non-Markdown report path was found in the145-commit range.
- Projection after that migration alone:204 changed files,+29,135/-3,003. Policy, catalogs, citation edits and cleanup reviews will add their own small diff. Working delivery budget: fewer than250 changed files and40,000 additions; report actual counts before publication instead of treating this projection as a guarantee.
- Remaining complete tracked tree before new policy changes:10,697,725 bytes. Reports subtree:478,307 bytes. Largest retained blob:576,155 bytes.
- Existing packed Git object store:63.50MiB. This is compressed history, not the134MB current payload size.
- Dependency analysis:348 recognized local links from46 Markdown documents point to the804 candidates.131 Markdown documents contain1,830 occurrences of129 distinct original unmerged commit identities. Preserve original identities with provenance/recovery mapping; do not replace all1,830 literals with rewritten hashes.
- Repository API: squash/rebase/merge methods enabled; development unprotected; no releases; release immutability disabled. Actions retention90days; smoke/performance workflow artifacts explicitly14days. No retention/branch protection change is proposed except explicit release immutability below.

The exact804-file path/size/SHA256 inventory is the external per-file candidate inventory. the external dependency inventory contains the actual link and source-identity occurrences. Neither file is committed; they are analysis inputs for the approval package.

## Alternatives

A. Durable archive + normal deletion commit. Removes bulk from the PR's final diff without a force push. Squash merging a clean final tree can keep the old unmerged commits out of main ancestry, but development remains a published ref carrying the bulk, so ordinary full clones still receive that ancestry.

B. Durable archive + narrow rewrite of unmerged development history — recommended. Removes bulk from both the PR diff and advertised development ancestry. Original history survives in an external, verified bundle; meaningful commit ordering is retained, with empty evidence-only commits handled explicitly. Requires one-time development-only force-with-lease authorization and collaborator synchronization.

C. Git LFS migration. Adds contributor/storage tooling obligations and still needs old Git-history handling. It is unnecessary for archival review streams and is not recommended here.

GitHub PR refs/caches may retain previous objects even after optionB. Server-side physical erasure or immediate repository-size-accounting reduction is not promised. The measurable acceptance criterion is clean advertised branch/tag ancestry and a fresh ordinary clone, not inaccessible GitHub internal storage.

## Proposed durable delivery and policy

Keep all canonical Markdown reports/reviews, original findings/verdicts/severities/measurements, all six checker/test files, source comments, CI behavior and compact archive metadata in Git. Move the804 payloads byte-for-byte. The full archive includes raw originals, intermediate stages, previous source exports, decoder scripts and existing encoded bundles; do not discard unique evidence merely because it is redundant for everyday review.

Create a dedicated GitHub evidence release, draft first, prerelease and not latest, plus a verified independent local copy outside the repository. Suggested tag: evidence-pr-49-2026-10-16, pointing only to already-clean main c16997e. Its automatic source archive is that main anchor; the attached Git bundle is the authoritative old development source. Do not tag the bloated original tip.

The evidence-only release is archival hosting under [ADR-0044](../../decisions/0044-review-evidence-retention.md), with no product version, image, ABI/support claim, first product release or maintainer-key signature assertion. Its contract is immutable bytes, digests, historical provenance and verified restoration. Product release gates/signing remain mandatory; a minimal [release-standard](../../standards/release.md) scope pointer follows Acceptance and precedes publication.

Enable repository release immutability before publication. This applies to future releases; there are currently none. Upload all assets before publication, verify download digests and restoration, publish, then verify immutable status and tag anchor. Any unavailable immutable publication or failed restoration stops removal/ref replacement; do not fall back silently to expiring Actions artifacts.

Proposed in-Git limits:1MiB per tracked blob;512KiB aggregate non-Markdown content under docs/analysis/reports/;128KiB archive catalog. Add a separate footprint command/test in the existing lint job, leaving check-docs.py's offline/no-Git contract and all six required app15368 context identities intact. One-time maintenance tooling outside project dependencies may be needed: git-filter-repo is currently not installed. Pin and verify its primary-source version/digest before isolated use.

The complete proposed decision is [ADR-0044](../../decisions/0044-review-evidence-retention.md). It is filed Proposed with this plan; a separate Acceptance commit follows both fresh review rounds. Execution will record approved maintenance criteria under existingT049/T056, and preserve ADR0043. The package adds no phase task, does not implementT038 and does not promote tasks toDone.

## Ordered approved execution

1. **Freeze and create tested local recovery.** Recheck clean worktree, exact local/remote development tip, advertised main and all advertised refs. Record the unchanged pre-existing local main separately; it is not the remote PR base. Stop on drift. Create a self-contained original development bundle and payload manifests outside the working tree; verify bundle integrity, clone/recover original source and all804 payloads, and hash-check every recovered file. Save PR metadata and original final CI/API/log proof before retention expiry. No new backup branch/tag in the source remote.

2. **File and settle the approved decision.** Commit the proposed ADR separately from Acceptance, complete the deliberate reread and required review discipline, then record approved followup criteria forT049/T056 and operative roadmap state. Material proposal changes return for approval. No standard/guard implementation precedes the accepted decision.

3. **Prepare the archive and trial rewrite without replacing published refs.** Freeze the post-governance tipA. Create a self-contained pre-rewrite bundle ofA, which includes original97 and the approved governance commits. This bundle is independent of the later in-Git catalog, avoiding self-referential hashes. In an isolated copy using the same development name, filter only the enumerated804 paths in main-base..A; never rewrite main or unrelated refs. Generate the original-to-proposed commit map, compare every noncandidate path at mapped trees, inspect empty-commit handling and confirm the main anchor unchanged. Package the bundle, original payload snapshot, full external per-file manifest, map, provenance and recovery instructions.

4. **Publish and verify the durable archive.** Create the draft evidence release at the clean main anchor, upload the complete assets, download all assets to a distinct location, verify hashes and restore old source/individual evidence from the downloaded copy. Publish only once complete, confirm immutable assets/tag and retain a second local copy outside Git. Do not replace actual development refs or remove payloads before this gate succeeds.

5. **Apply the bounded rewrite locally and reconcile citations.** Only after verified archival, adopt the trial-filtered development tip locally; do not switch to another branch. Immediately repair the348 citations/46 documents to the archive catalog/verified external destinations, preserving old text in the archive and dating migration notices. Preserve historical SHA literals and provide their recovery/map context. Add compact catalog and restore instructions. No broken intermediate local state is pushed. New maintenance commits/reviews occur after the rewrite, so their source hashes will not themselves be rewritten later.

6. **Prevent recurrence and review the new work.** Add the separate footprint check, meaningful small temporary-fixture negative/positive tests, existing-lint-job wiring, minimal standards/skill guidance and correct current-state updates. Verify all804 archived/recovered bytes, retained source/fixture blobs against original97, original historical assertions and all new citations. Run the existing161/124 fixture suites and whole docs corpus on both supported local runtimes, the new guard tests/negative probes, appropriate syntax checks and diff checks. Each implementation step follows commit → fresh complementaryR1 → validated fixes/commit → different freshR2 → validated fixes/commit. Review records/essential summaries stay within the approved budget; scratch exports go outside Git.

7. **Validate the final candidate before remote replacement.** Confirm no migrated payload path remains reachable through the proposed development ancestry; inspect retained blob size limits, compact catalog, full file membership, source equivalence,145-original-commit provenance and unchanged main/other refs. Use clean isolated clones/copies for recovery and object inventory; do not expire reflogs, prune backups or run aggressive GC in the maintainer's working repository. Freeze new tipF.

8. **Publish exactly development with a lease, then verify final hosted gates.** Recheck that origin/development is still the approved original97. Publish F using an explicit refs/heads/development lease expecting97; no mirror/blanket force push and no main/other-ref change. A lease mismatch stops. Verify PR49 remains development→main, updated diff/budget, all seven hosted jobs and six exact app-bound required contexts, new footprint rejection controls, unchanged protection and a fresh ordinary remote clone. Record actual final source/results in PR49; tasks return InReview. Maintainer SECURITY wording review and merge remain separate.

## Recovery and approval boundary

Before publication, restore from the verified original/pre-rewrite bundle if a local ref/tree operation fails. The remote remains original97 until step8. After publication, ordinary fix commits are preferred for a CI defect; a necessary emergency rollback to original97 is restricted to development and an exact lease on the observed new tip. The proposed authorization includes that narrowly scoped rollback, not arbitrary future force pushes. Keep the verified archive/backups until the maintainer confirms the resulting PR and recovery path.

Approval of optionB includes the attached ADR policy,804-file relocation/citation migration, dedicated public evidence release and immutable-release setting, one-time bounded development rewrite/lease publication and scoped rollback, separate footprint guard, and the original two-round review discipline. It excludes mergingPR49, changing main/protection/other refs, deleting canonical verdicts, claiming historical tests ran on rewritten hashes, accessing private notes, or starting later phase work.

## Primary references

- Git bundle: https://git-scm.com/docs/git-bundle
- git-filter-repo: https://github.com/newren/git-filter-repo/blob/main/Documentation/git-filter-repo.txt
- GitHub release immutability: https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes
- Managing release assets: https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository
- Actions retention: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository
- GitHub old-ref/cache limits: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository

## Execution checkpoints

### Recovery baseline — 2026-10-16

At original `97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4`, the clean development worktree and open PR #49 match the frozen source. A self-contained bundle was verified and independently cloned; all 804 payloads were SHA-256 checked both from the tar archive and recovered clone. The protected main definition and original hosted proof are retained outside Git.

| Asset | Bytes | SHA-256 |
|---|---:|---|
| Original development bundle | 63841865 | `a622d9e31929132c547d7b1a32a56aba31523338e81762c4004d64c8a6f5d0f9` |
| Payload archive | 66475418 | `032b586ec81c38d37d45f5076c628707a3b35484da4388499f1d9896c44e3117` |

Local recovery is verified; durable public publication, history migration, footprint guard, hosted final-tip checks and maintainer review remain pending. Implementation review units are governance/recovery (steps 1–2), archive/migration/citations (steps 3–5), and prevention/final validation (steps 6–8). Each unit has its own committed source, two different fresh complementary rounds, validated correction commits and explicit disposition before the next unit. Publication is gated by completed local reviews.

### Governance R1 correction — 2026-10-16

Both independent first-round reviewers requested one Medium clarification (GR1-C01 / INT-R1-01): define evidence hosting relative to the product-release signing/gates standard. The Proposed ADR and plan now define the approved evidence-only profile and ground its post-Acceptance standard pointer in T-056. No signature, product release or broadened remote-ref authorization is claimed. Independent committed-fix verification and a different fresh second round remain required before Acceptance.

### Governance/recovery review boundary — 2026-10-16

[Both fresh complementary rounds](../reviews/code-reviews/2026-10-16-pr49-evidence-governance.md) close the single Medium release-scope group at94fd86c; all six complete initial/fix reports and digests are preserved. Deliberate end-to-end reread confirms actual task dependencies, costs and ADR-0043 compatibility. Separate Acceptance and dependent implementation follow; no public archive, migration or new hosted result is yet claimed.

### Decision Acceptance — 2026-10-16

ADR-0044 is Accepted in a separate commit after the actual reread and both fresh complementary review rounds. The maintainer approved this policy and bounded execution in chat. This records decision authority only; the archive/migration/prevention delivery gates remain pending.

### Archival execution starts — 2026-10-16

T-049/T-056 are In Progress for approved maintenance; the task index, delimited live state and track pointer agree. The narrow release-standard scope pointer follows actual Acceptance and precedes publication. The next frozen pre-rewrite source includes these governance/status changes; no payload removal or remote development replacement has occurred.

### Durable archive and local migration — 2026-10-16

The [actual migration record](2026-10-16-pr49-evidence-migration.md) binds immutable publication, both downloaded recovery checks,150 mapped-tree comparisons, exact local-only adoption and348/46 reversible citation repair. The original generator failure and complete reproducible correction are explicit. Remote development remains original97; both migration rounds, footprint implementation and final hosted publication remain pending.

### Migration R1 correction — 2026-10-16

Fresh CODE R1 reported Low MRC1-01: current/phase pointers still described actual completed archival/local migration as pending. Complementary integrity R1 independently approved archive/map/citation integrity. Live pointers now separate completed immutable publication/local migration from review/prevention/remote lease/hosted gates; guide status avoids a stale per-round claim. The initial byte-reversal proof remains bound to migration commit86484e6; this later status-only correction is explicit. Original reports/verdicts remain unchanged.

An ordinary full Git-transport clone of86484e6 with local object-store copying disabled has no candidate paths in any fetched ref, passes full Git integrity, and uses a5.93MiB pack (original measured pack63.50MiB). Full docs output is identical on Python3.9/3.13:405 files/7285 targets/1273 fragments/zero findings. This is a local source-clone result; final ordinary remote clone and hosted source remain pending.

### Archive/citation unit closes — 2026-10-16

[All six complete reports](../reviews/code-reviews/2026-10-16-pr49-evidence-migration.md) preserve both fresh complementary rounds and Low MRC1-01 fix verification at3a17c3d. No unresolved finding. T-049 maintenance criteria are checked and it returns In Review; T-056 remains In Progress. The separate footprint guard/CI/review/final lease/hosted/remote-clone gates are next. No extra rewrite or merge is performed by this closure.

### Prevention/final-validation preflight — 2026-10-16

The approved limits will cover indexed blobs and every complete HEAD-history snapshot, so adding an oversized artifact and deleting it in a later commit cannot evade delivery checks. Report aggregate is512KiB per snapshot; each Markdown/JSON evidence-catalog pair totals at most128KiB; each tracked blob at most1MiB. Gitlinks store only an external commit identity and are not parent-repository blobs. The separate Git/stdlib command reads objects, ignores untracked/worktree-only content and refuses shallow/promisor inputs instead of silently reducing history or lazily fetching. The existing lint checkout gains full history; no required context/app identity, runtime dependency, admin credential or check-docs contract changes.

Meaningful temporary Git fixtures will cover inclusive boundaries, aggregate/pair limits, commit-then-delete history, staging versus worktree, symlinks/Gitlinks, invalid roots/unmerged index and incomplete history, deterministic JSON/default root behavior and offline failure. No alternate project branch or committed negative probe. Documentation/standards/common review skill receive minimal Accepted ADR-0044 guidance. Both fresh prevention review rounds, final exact-lease publication, all hosted gates and ordinary remote clone remain required.


### Prevention implementation validation — 2026-10-16

At preflight HEAD803ff08 with the staged prevention change, both Python3.9.6 and3.13.14 pass the existing161 navigation/reader and124 metadata methods. The separate footprint suite passes21 real temporary-Git methods on each runtime. Author self-review reproduced a legacy info/grafts false green: an oversized committed-then-deleted artifact became hidden. Its new isolated regression first failed (exit0 instead of2), then passes after explicit graft-file rejection; original replacement-object suppression remains independently tested. This is new author verification, not a claim about historical execution or a substitute for either fresh review round.

The guard streams one complete tree at a time, caches unique blob sizes, reads indexed objects and rejects incomplete/alternate ancestry views. Existing lint checkout gains full history and two failing footprint steps; credentials remain unpersisted and permissions/job identities unchanged. Minimal Accepted ADR-0044 guidance is wired into documentation/infrastructure standards, the CI guide and common review skill. No production Rust, unsafe, dependency, parser or branch-protection change. Both fresh prevention rounds and final candidate/remote lease/hosted/ordinary remote-clone gates remain required; T-056 stays In Progress.


### Prevention R1 correction — 2026-10-16

Both fresh independent initials at2d83602 requested the same Low group (PRC1-01/PIR1-01): Python3.9 Path.resolve raises RuntimeError for a symlink-loop root, escaping the documented invalid-input JSON/exit2 boundary. Coordinator independently reproduced3.9 exit1/traceback and3.13 exit2, then added a real public-CLI regression which failed before the repair. The narrow root-resolution boundary now converts that exception to InputError; both runtimes pass all22 footprint methods. Existing policy findings retain exit1 and no storage limit or ancestry check is weakened. Actual same-context committed-fix verification/peer reconciliation, a different fresh full second round and final publication/hosted/clone gates remain pending. Initial verdicts and original failed-before observations remain preserved.


### Prevention R2 correction — 2026-10-16

Different fresh CODE R2 initially approvedfb9e4b9 with zero findings; fresh integrity R2 independently requested one Medium PIR2-01. A checksum-valid inconsistent commit-graph cache truncates cached HEAD parents, hiding an oversized committed-then-deleted ancestor. Coordinator independently reproduced both-runtime exit0 (one cached commit versus three raw commits), with Git's cache verifier reporting inconsistency. The first scratch mutation needed owner-write permission on the disposable cache; no project cache was touched. New public-CLI regression fails againstfb9e4b9 on both runtimes before the fix.

The Git read wrapper now explicitly sets core.commitGraph=false, so ancestry/tree metadata comes from actual commit objects. The regression constructs the documented Git cache format with a valid checksum and inconsistent parents, without altering stored commits; source attribution must still identify the original oversized commit. This does not claim normal tracked PR content can install a cache on clean CI, or introduce an object-authenticity guarantee. [Git configuration](https://git-scm.com/docs/git-config) and [cache format](https://git-scm.com/docs/gitformat-commit-graph) ground the narrow remedy/fixture. Both supported local runtimes pass all23 footprint methods after the repair. Actual same-R2 committed-fix verification and post-freeze peer reconciliation remain required; the initial Approve/Request changes are preserved, and final lease/hosted/clone gates remain pending.
