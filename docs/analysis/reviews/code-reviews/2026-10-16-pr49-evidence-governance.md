# Code review 2026-10-16 — PR49 evidence governance and recovery

Both fresh complementary rounds are complete for the governance/recovery unit. One unique Medium release-scope clarification was fixed and independently verified; no unresolved finding remains. This record preserves all six original reports below, including initial Request changes verdicts and actual reading/verification limits.

- **Change:** `97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4..94fd86c8328ff6951aa61b06444d17f8ccefe25d`.
- **Reviewer:** Codex coordinator and four separately instantiated independent reviewers identified in the preserved reports.
- **Risk class:** Ordinary governance/documentation, with separate archive/ref integrity passes.
- **Security-review cross-reference:** N/A for kernel security triggers; no runtime/unsafe/cryptographic primitive change. Operational publication trust boundaries were explicitly reviewed.

## Correctness

All 804 payloads, manifest membership, original-tree bytes, tar/recovered-clone hashes and complete-history bundle integrity are independently verified. Original source/run identities and pending implementation gates remain explicit. Exact remote/main boundaries are distinguished from the pre-existing local main ref.

## Style

MADR sections, real task dependencies, English prose and separate Proposal/Acceptance are preserved. No prior Accepted ADR body was rewritten. ADR index headers/status/date join correctly. The descriptive ADR-0044 title extends its filename slug; this literal slug/title difference is reported separately from the green index/header join, as required by sync-adr-index.

## Test coverage

Navigation161/metadata124 suites pass on Python3.9/3.13; all-family corpus at the corrected source is401 Markdown files/7215 targets/925 fragments/zero findings. The individual reports distinguish independent execution from inspected historical logs. No new Rust/QEMU execution is claimed. Archive download/restoration, filtering/equivalence, footprint fixtures and final hosted source remain future gates.

## Documentation

GR1-C01 and INT-R1-01 describe the same Medium ambiguity, initially raised by the coordinator and independently assessed by both R1 reviewers. Fix94fd86c defines evidence-only archival hosting, preserves product release signing/gates and grounds the minimal post-Acceptance release-standard scope pointer in T-056 before publication. Both R1 reviewers verified the committed correction. Different fresh R2 CODE and integrity reviewers report zero findings. Original findings/verdicts and source identities below are not retroactively replaced.

## Integration

Only governance documents and existing-task maintenance criteria changed. Main/protection, unrelated refs, checker behavior and required context identities remain unchanged. The independently verified original bundle precedes the later governance-inclusive archival freeze. No payload removal, immutable publication, history rewrite or merge is claimed by this unit.

## Verdict

**Approve — governance/recovery unit only.** Both required rounds and the deliberate end-to-end ADR reread are complete; zero unresolved findings. Separate ADR Acceptance precedes dependent standards/archival implementation. Later migration/prevention units and maintainer merge remain separate.

## Preserved original reports

The following fenced snapshots preserve the complete report bytes, apart from the surrounding fences. Their source identities remain historical after the approved rewrite; the later archive catalog supplies recovery and commit mapping.

### governance-r1-code.md

SHA-256: `333fac915f5bb8af8b4ce5103c2c157f812fac9f99633aad4930bbdba799d13a`.

````````markdown
# Code review 2026-10-16 — PR #49 cleanup governance/recovery, round 1

Independent five-role review of the committed governance/recovery unit. This report is external to Git at the maintainer's direction; it does not approve merging PR #49 or delivering later migration units.

- **Change:** development, `97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4..38e14663e981753d4c3027539403182a477b534d` (five files, two commits, 208 additions).
- **Source reviewed:** full tip `38e14663e981753d4c3027539403182a477b534d`; original historical source `97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4`; advertised main/PR base `c16997e003fbd1726d1205734380394781c52002`.
- **Reviewer:** Codex, independent code role; all five master-plan roles executed sequentially. No peer report read before this initial freeze. The coordinator separately raised the release-scope question, which I assessed against release.md myself; I do not claim to have independently originated that question.
- **Risk class:** Ordinary documentation under the kernel security-review trigger list; elevated evidence-retention/ref-publication process consequences. The requested complementary integrity review remains a separate pass.
- **Read scope:** AGENTS.md, CLAUDE.md, current roadmap; perform-code-review/conduct-review skills and code master plan; MADR template/write-adr skill; affected task contracts; relevant ADR-0025/0040/0043; documentation, code-review, commit, testing, security-review, release and architectural-principles standards. All five changed documents and the external approved draft/plan were compared. External candidate/dependency inventories, recovery proof, saved refs/PR/CI/protection metadata and both job inventories were inspected. Payload bytes were hashed, not semantically reviewed; embedded archives/source exports were not manually re-reviewed.

## Correctness

- The filed ADR preserves the approved draft's archive, 804-path boundary, separate footprint guard, exact development lease/rollback, immutable publication, source-identity honesty and no-merge limits. Changes concern filing/date/approval state, repository-relative citations and review sequencing, not a different storage choice.
- ADR-0044 remains Proposed, the index joins its exact title/status/date inside the existing table, all MADR sections exist, and dependencies point at real existing T-049/T-056/T-047 slots. No prior Accepted ADR body changes. ADR-0043's whole-corpus checking, offline/no-Git checker contract and historical evidence authority remain explicit.
- Independent `git diff --numstat` and object-tree recount reproduce 1,008 files, +956,905/-3,003; 804 candidates/+927,770 lines/134,293,614 bytes; projected 204 files/+29,135/-3,003; retained tree 10,697,725 bytes/reports 478,307 bytes/largest retained blob 576,155 bytes. Historical changed-path enumeration across all 145 unmerged commits finds no extra candidate path. Re-reading the recovered original corpus reproduces 348 links/46 documents and 1,830 SHA mentions/131 documents/129 original identities.
- Local recovery claims reproduce: bundle is complete and passes `git bundle verify`; the existing independently recovered clone is clean at original97 and passes full `git fsck`. Every one of 804 tar members and recovered-clone files matches manifest size/SHA-256; no extraction or source-tree copying was performed. Both asset byte counts/digests match the committed checkpoint: bundle 63,841,865 bytes / `a622d9e31929132c547d7b1a32a56aba31523338e81762c4004d64c8a6f5d0f9`; tar 66,475,418 bytes / `032b586ec81c38d37d45f5076c628707a3b35484da4388499f1d9896c44e3117`.
- Original-only local backup is correctly distinguished from the future post-governance pre-rewrite bundle and verified public archive. No pending operation is represented as already delivered.

## Style

Clean for this scope. English, existing Markdown/MADR conventions and conventional commit subjects/ADR trailers are retained. No new runtime API, unsafe region, dependency or diagram needs review.

## Test coverage

- Current whole-corpus check: Python 3.9.6, eight families, 401 Markdown files / 7,212 local targets / 925 fragments / zero findings. `git diff --check` passes.
- Independently executed existing navigation 161-test and metadata 124-test suites: pass on Python 3.9.6 and Python 3.13. This source does not change executable checking behavior; additional fixtures or Rust/QEMU builds are unnecessary for this unit.
- Both retained CI-log ZIPs pass ZIP integrity checking (114 entries each). Saved run inventories show all seven jobs successful in both original runs; saved check data supplies all six required app-15368 success contexts at original97. These are historical captures, not new hosted execution on source38 or rewritten source.
- The release download/immutability gate, trial rewrite mapping/equivalence, footprint rejection fixtures, final remote lease publication and final-source hosted checks are later-unit obligations, not missing tests for this Proposed filing.

## Documentation

**GR1-C01 — Medium, blocking before Acceptance: reconcile the evidence-release profile with the release standard.** At `docs/decisions/0044-review-evidence-retention.md:36` (also cleanup plan's durable-delivery section), the new policy creates a GitHub evidence prerelease at an existing clean-main anchor, with archived source/payload assets. `docs/standards/release.md:114` says tags and release artifacts are signed; its first product release also brings version/changelog/key-publication gates, and its anti-pattern list rejects unsigned tags/artifacts. The ADR does not reference this standard or explicitly distinguish archival hosting from a Tyrne version release. The labels evidence/prerelease/not-latest alone do not settle whether those broad requirements apply. Before immutable publication, an executor would have to invent a policy exception or expand this cleanup into a first product-release workflow.

**Required correction:** define the narrow evidence-only hosting profile in the Proposed ADR/plan before Accept, linking release.md. State that this archive declares no Tyrne version, bootable product, supported-target/ABI guarantee or first product release; preserve the product-release gates and signing policy. Explicitly reconcile the archive's approved immutability/digest/restoration provenance contract with release.md instead of silently waiving its requirements. Ground the minimal matching standard cross-reference as Accepted-ADR followup before archive publication. This finding does not request a new kernel release or relaxation of product-release requirements.

## Integration

- T-049/T-056 gain bounded unchecked maintenance criteria while original completed criteria remain historical; task count and In Review ceiling remain intact. Actual maintenance state/current.md updates are explicitly required by the execution plan as that work starts; this Proposed-only unit does not falsely mark maintenance complete.
- No checker, CI job/context/app binding, protection setting, production source, other ref or source payload is changed by these two commits. The source-identity and lossless archive contracts agree with ADR-0043. Review/publication and no-merge boundaries remain explicit.
- GR1-C01 is the only confirmed cross-standard blocker. Local main is pre-existing stale `400dec041a65fea163d4cbefb671f355aaf416ca`, whereas the saved advertised main/PR base is c16997e; this review does not claim to have synchronized or changed either. Future ref freezes must distinguish local refs from advertised refs.

## Verdict

**Request changes** — one Medium blocker, GR1-C01, limited to release-policy scope clarity before ADR Acceptance. No other confirmed scoped finding.

Verification limits: no live API refresh, publication, settings change, force push, new clone/extraction, rewrite, GC, source mutation, kernel execution or merge was performed. Saved API data is historical; the 63.50 MiB original packed-store measurement was not recreated after governance commits. This review validates the frozen governance/recovery unit and measured archive content, not every historical verdict or embedded evidence stream. Acceptance requires the correction's committed-source verification and the required fresh second complementary round; this report is not Acceptance or merge authorization.
````````

### governance-r1-integrity.md

SHA-256: `453d82cb9b28fa8861b6df12a205797165d1e2265ec5fe512a18e233c26437dd`.

````````markdown
# Code review 2026-10-16 — PR49 cleanup governance/recovery R1 integrity

Independent complementary review of archive recovery, provenance and operational boundaries. The initial independent pass was completed without reading the peer review. A subsequent parent-requested check of release-standard scope produced finding INT-R1-01 below; no peer review was consulted. It is an external review input for the canonical consolidated record, as requested; it does not change repository state.

- **Change:** `97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4..38e14663e981753d4c3027539403182a477b534d` (five Markdown files, 208 additions).
- **Source SHA:** `38e14663e981753d4c3027539403182a477b534d`.
- **Reviewer:** Codex independent agent `cleanup_governance_r1_integrity`, covering all five roles sequentially.
- **Risk class:** Ordinary documentation change, with explicit Git/ref/archive trust-boundary assessment.
- **Security-review cross-reference:** N/A for the formal kernel security-review trigger: no runtime, unsafe, dependency, cryptographic primitive or kernel authorization change.
- **Basis:** AGENTS/CLAUDE; current roadmap; review skills/master plan; code-review, security-review, documentation and release standards; ADR-0025/0043; Proposed ADR-0044; approved cleanup plan; T-049/T-056 maintenance clauses; actual candidate inventory, bundle, payload archive, recovered clone and captured CI/ref metadata. This is a bounded complementary review, not a new full-kernel or all-ADR correctness audit.

## Correctness

No blocking finding. Independent checks established:

- The candidate manifest contains exactly 804 unique paths. Its membership equals all newly added non-Markdown report paths between clean main `c16997e003fbd1726d1205734380394781c52002` and original development `97dbcd1`; all non-Markdown report paths touched over those 145 commits are the same set. There is no extra historical-only candidate path.
- Every original Git blob, existing recovered-clone file and tar member independently matches the manifest size and SHA-256: 804/804, totaling 134,293,614 bytes. The tar has exactly 804 ordinary file members with no duplicate/extra member. No archive extraction or archived script execution was needed.
- Recomputed bundle size/hash: 63,841,865 bytes, `a622d9e31929132c547d7b1a32a56aba31523338e81762c4004d64c8a6f5d0f9`. Recomputed payload archive size/hash: 66,475,418 bytes, `032b586ec81c38d37d45f5076c628707a3b35484da4388499f1d9896c44e3117`. Both match the committed recovery checkpoint.
- `git bundle verify` confirms complete history and the original development ref. The recovered clone is clean at the original full SHA, has no alternates, and passes `git fsck --full --no-reflogs`. This reviewer verified the existing recovered clone; the review did not create a second clone or claim a new clone operation.

The original-tip recovery asset is correctly distinguished from the required later post-governance bundle. The latter, its map and public release remain pending; the proposal does not falsely claim they already exist.

## Style

No blocking finding. The added policy and maintenance text use English Markdown and explicit identities. No proprietary payload, runtime code, dependency or diagram is introduced. Proposed status and separate Acceptance are visible in both the ADR and approval plan. The review does not raise cosmetic spacing preferences as safety defects.

## Test coverage

The byte-level and Git integrity checks above independently substantiate the local recovery claim rather than trusting `recovery-proof.json` alone. The archived PR snapshot binds PR49 to development original97 and main c16997e. Captured push run 38801339254 and PR run 38801349720 both identify original97 and contain seven successful jobs. Both downloaded log ZIPs pass CRC validation; each contains 114 entries. Captured checks include the six required app-15368 contexts at original97, each successful.

These are historical proof inspections, not reruns of CI and not proof of any future rewritten head. No Rust/QEMU rebuild is warranted by this five-file governance-only delta. Future post-governance bundle recovery, downloaded public-asset restoration, immutable-release confirmation, commit-map/source-equivalence checks, footprint tests and final hosted CI remain required execution gates. This review does not certify those pending gates.

## Documentation

**INT-R1-01 — Medium, blocking before Acceptance: define evidence-hosting scope relative to the release standard.** `docs/standards/release.md` defines product version/changelog/kernel gates, but its Signing section says “Tags and release artifacts are signed with the maintainer's long-term key” and its anti-patterns reject unsigned tags or artifacts without an explicit scope exception. ADR-0044's Decision outcome authorizes a GitHub evidence release with SHA-256 and immutability, yet does not state its relationship to that standard. Product-focused surrounding text suggests the intended distinction, but leaves a concrete ambiguity about whether archival publication silently waives existing release/signature requirements.

Before Acceptance, explicitly define this approved evidence-only hosting category in ADR-0044: prerelease/not-latest, clean-main evidence tag, immutable digest-verified evidence and tested recovery; no kernel product version, changelog/support milestone, or maintainer-key signature assertion. Preserve the product release gates. Ground a minimal subsequent release.md scope pointer in the existing maintenance ownership, after Acceptance. This is clarification of the already approved archival operation, not a request to invent a signature, cut a product release, or broaden authorization. The parent requested this focused scope check after the independent pass; this reviewer then read the standard and confirmed the wording directly.

Otherwise, The policy preserves canonical Markdown verdicts, original measurements and SHA execution identities, while giving their old source a self-contained recovery route. It explicitly prevents substituting rewritten SHA values for historical executions. The source bundle is independent of the later catalog, avoiding a self-referential digest requirement.

The public evidence tag is anchored to clean main rather than old development; automatic GitHub source archives and the authoritative attached original-source bundle are distinguished. ADR-0043 is preserved, not silently narrowed. ADR-0025 forward references resolve to existing T-049/T-056/T-047 ownership; proposal and Acceptance are separate, with deliberate reread and two rounds still required. Task additions are unchecked maintenance criteria, not retroactive claims that the original work was incomplete or newly Done.

## Integration

No blocking finding. A fresh read-only `git ls-remote --heads --tags origin` returned exactly the 17 frozen advertised refs, with no changed or added identity. The reviewed working branch remains development, clean at source38e1466. Main's tree contains none of the 804 candidates. All 16 non-development advertised refs were checked for reachable candidate-path objects; none carries them. One older documentation branch shares five original-range commits, but those commits carry no migrated candidate payload; changing that unrelated ref is unnecessary.

The operational order requires verified local recovery, accepted governance, isolated bounded trial filtering, complete durable public publication and restoration, then actual local adoption and citation repair, then one explicit development-only lease publication. The archive tag is the explicitly authorized clean-main evidence tag; unrelated refs and main/protection stay outside the rewrite. The emergency rollback is restricted to development with an exact lease on the observed replacement tip. Immutable publication failure or drift stops the operation. No remote backup ref, blanket force push, destructive source-repository GC, or claim of GitHub cache erasure is authorized.

The separate footprint guard retains check-docs.py's offline/no-Git contract and existing app-bound check identities. No implementation/CI setting change is part of this reviewed unit. Local archive recovery is not mistaken for independent public durability: the independent copy and hosted archive gates must still be satisfied before removal/ref replacement.

## Verdict

**Request changes** for this bounded governance/recovery source: close INT-R1-01 before Acceptance. All archive-byte recovery, provenance and ref-boundary checks passed; no additional finding was identified. This is one complementary R1 input; it does not replace the different fresh R2, the separate Acceptance commit, later archive/migration/prevention reviews, or maintainer approval/merge. No repository edit, ref mutation, remote publication, peer-review read or new source/archive dump was performed.
````````

### governance-r1-code-fix.md

SHA-256: `7efbcab74ea411612d89f07edac1733f36456c521aabf92f102fc59be5788fd7`.

````````markdown
# Code review fix verification 2026-10-16 — governance round 1

Independent verification of GR1-C01 on committed source; this note supplements and preserves the frozen initial five-role report and its original Request changes verdict.

- **Initial source:** `38e14663e981753d4c3027539403182a477b534d`.
- **Fix source:** `94fd86c8328ff6951aa61b06444d17f8ccefe25d`.
- **Bounded delta:** three Markdown documents, 11 additions / two deletions; actual committed diff read in full.
- **Reviewer:** Codex, original independent code reviewer. No peer report read for this verification.
- **Initial report SHA-256 rechecked unchanged:** `333fac915f5bb8af8b4ce5103c2c157f812fac9f99633aad4930bbdba799d13a`.

## GR1-C01 disposition

**Closed.** ADR-0044 now links release.md and explicitly defines archival evidence-only hosting, without a kernel/product version, boot image, support/ABI guarantee, changelog milestone or first product-release assertion. It states the actual integrity/provenance contract: immutable bytes, SHA-256 digests, original source identities and tested independent recovery, with no maintainer-key signature assertion. Product release gates and signing remain mandatory for product releases.

The cleanup plan repeats that boundary. Both ADR dependency-chain item 2 and the new unchecked T-056 maintenance criterion require the matching release-standard scope pointer after Acceptance and before archive publication. The standard is therefore reconciled through an existing grounded task before the archive is published; no product-release policy is silently waived by the correction. The minimal retention guidance remains within the approved maintenance followup.

The plan additionally distinguishes advertised main from the pre-existing unchanged local main, resolving the initial report's non-blocking operational observation without authorizing another ref change.

## Verification and remaining obligations

`git diff --check` passes for source38..source94. New correction references resolve in the committed tree. ADR-0044 and its existing index row both remain Proposed with matching date/title; no premature Acceptance is introduced. No new confirmed finding in the bounded correction.

**Fix-verification verdict: Approve; GR1-C01 closed, zero unresolved code findings for this first-round unit.** This is committed-fix verification, not a second fresh review round. The different fresh complementary second round and deliberate reread remain required before separate Acceptance. The actual release-standard pointer, archive publication/recovery gate, history rewrite, footprint implementation and final hosted checks remain future implementation obligations.

Limits: no broad test rerun was needed for this prose-only correction; the initial recovery/count/corpus/fixture evidence remains attributed to its original reviewed source. No repository edit, new archive/source copy, settings change, publication, rewrite or merge was performed. Initial report bytes and verdict are unchanged.
````````

### governance-r1-integrity-fix.md

SHA-256: `2e839f744b7ee0b50f6124d7b0e4f4c32757ca98efa4f6550c71e0606eaf896c`.

````````markdown
# Committed-fix verification — PR49 governance R1 integrity

INT-R1-01 is closed on the committed fix. This bounded follow-up preserves the initial review and its historical Request changes verdict.

- **Reviewer:** Codex independent agent `cleanup_governance_r1_integrity`.
- **Source SHA:** `94fd86c8328ff6951aa61b06444d17f8ccefe25d`.
- **Delta:** `38e14663e981753d4c3027539403182a477b534d..94fd86c8328ff6951aa61b06444d17f8ccefe25d`; one direct-child commit, three Markdown files, 11 additions / 2 deletions.
- **Original report:** `governance-r1-integrity.md`, SHA-256 `453d82cb9b28fa8861b6df12a205797165d1e2265ec5fe512a18e233c26437dd`; both report bytes and adjacent checksum were independently confirmed unchanged.
- **Risk:** Governance/documentation only; formal kernel security-review trigger remains N/A.

## Verification

**INT-R1-01 — Closed.** ADR-0044 line 38 explicitly defines evidence-only hosting, separates it from a product-version release and identifies the actual integrity/provenance contract: immutable hosted bytes, published SHA-256 digests, original source identities and tested independent recovery. It makes no kernel version, bootable image, target/ABI guarantee, changelog milestone, first-product-release or maintainer-key signature assertion. Product release gates and signing requirements explicitly remain mandatory.

The preceding retained paragraph still requires draft preparation, complete download verification, prerelease/not-latest labeling, the clean-main tag anchor, independent local archive and stop-on-failure behavior. The clarification therefore does not weaken the archival contract.

T-056 line 70 provides an unchecked, concrete maintenance criterion to add the release-standard scope pointer after ADR Acceptance and before archive publication. ADR dependency-chain ownership and the plan agree. The standard itself has not been prematurely changed, and the ADR remains Proposed. Minimal retention guidance remains bounded to approved maintenance.

The plan now distinguishes advertised main/PR base from the existing local main ref. Read-only ref inspection confirms local main is `400dec041a65fea163d4cbefb671f355aaf416ca`, while origin/main is `c16997e003fbd1726d1205734380394781c52002`. This avoids treating the local ref as the approved remote base; this follow-up does not independently assert its earlier historical value.

`git diff --check` passes for the exact committed delta. No peer report was consulted, no broad test or archive verification was repeated, and no repository/ref/remote mutation was performed.

## Verdict and remaining gates

**Approve the committed correction; INT-R1-01 closed.** Zero unresolved findings from this integrity R1 remain. This verifies a fix, not a different fresh R2. Fresh complementary R2, separate ADR Acceptance, the actual release-standard pointer before publication, durable archive/restoration, history-migration validation and final hosted gates remain pending under the approved plan. The initial report and its original verdict are unchanged.
````````

### governance-r2-code.md

SHA-256: `bb3d1873df8e7b0c3aeff811cc278ca8b7bf2951a2cfbb7ef356c8a391e934d0`.

````````markdown
# Code review 2026-10-16 — PR 49 evidence-retention governance, Round 2

- **Change:** `97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4..94fd86c8328ff6951aa61b06444d17f8ccefe25d`; five Markdown files, 217 additions, no deletions.
- **Reviewer:** Codex independent fresh R2 CODE reviewer, acting in all five master-plan roles sequentially.
- **Risk class:** Ordinary documentation change at this range; planned archival integrity and remote-ref operations warrant the separately assigned complementary review. This report is not that review.
- **Security/complementary cross-reference:** sibling `governance-r2-integrity.md` is expected from the independent complementary reviewer; not read or relied upon before this initial freeze.
- **Boundary:** Governance/recovery unit only. ADR-0044 remains Proposed. Acceptance, immutable hosting, rewrite, citation migration, footprint implementation, final hosted validation and maintainer merge remain pending.

## Correctness

No blocking finding. The full five-file delta matches the approved option B: exact 804-path relocation, original-history preservation, clean-main evidence tag, immutable draft-first hosting, isolated bounded rewrite, exact development-only lease and scoped emergency rollback. The plan gates removal/local adoption on verified durable publication, and remote replacement on the completed candidate. Failures and lease drift stop progress. Main, unrelated existing refs, branch protection, canonical findings and original execution identities remain protected.

The frozen original bundle and payload archive match the plan's exact sizes and SHA-256 values. I independently checked all 804 tar members and all 804 recovered-checkout payloads against the manifest, including exact tar membership, regular-file type and size. Manifest membership and sizes also match every non-Markdown report path in the original Git tree. The original range contains 145 commits. The recovery checkout identifies original `97dbcd1`; `git bundle verify` confirms complete history and the expected development ref.

The plan deliberately freezes the later governance-inclusive bundle before creating its catalog, avoiding self-reference. It preserves the distinction between original executed identities, mapped rewritten commits and subsequently authored maintenance commits. The release-standard clarification preserves product-release requirements while making this proposed evidence-only profile explicit; implementation must add its grounded standard pointer after Acceptance and before publication.

## Style

No blocking finding. The new ADR uses the project decision structure, documents alternatives and consequences, and records an explicit dependency chain. English Markdown and relative local references are appropriate. The three governance commits use conventional documentation subjects and relevant ADR trailers. `git diff --check` passes.

No Rust, unsafe region, dependency, public API, Result/error boundary, capability semantics or kernel fault-containment path changes in the reviewed range; those runtime checklist items are not applicable. No runtime build or QEMU rerun is claimed.

## Test coverage

Actual independent checks on clean reviewed HEAD:

- Bundle verification succeeds with complete history.
- Both archive asset hashes/sizes match the committed recovery table.
- Exact 804-entry manifest/tar membership, all tar payload hashes, all recovered payload hashes and original tree sizes pass; total payload bytes are 134,293,614.
- `python3 tools/check-docs.py` exits 0: all eight families, 401 Markdown files, 7,215 local targets, 925 fragments, zero findings.
- Exact-range whitespace check exits 0; HEAD remains `94fd86c`, worktree clean.

The archived four fixture outputs and summary report 161 navigation and 124 metadata tests passing on Python 3.9 and 3.13. I inspected their success summaries; I did not rerun the unchanged suites or attribute those archived runs to a newly executed R2 suite. New footprint fixtures, downloaded-asset recovery, mapped-tree equivalence and hosted final-tip checks are explicit later gates, not missing delivery claims at this proposal stage.

A first ad hoc asset-check attempt used unavailable Python 3.9 `hashlib.file_digest` and stopped before asset checks; the corrected streaming-hash run completed the checks above. Earlier default-yield corpus invocations did not retain final output; a completed captured invocation supplies the explicit result above. No failed attempt is counted as a pass.

## Documentation

No blocking finding. ADR-0044 and its index both say Proposed. T-049 and T-056 add unchecked, separately dated maintenance criteria while preserving historical checked criteria and In Review state. Their scopes name archival/citation ownership and the narrow standards/skills/footprint/migration followup. No new task or Done promotion is asserted. ADR-0025 forward references are grounded in existing task files, and ADR-0043 attribution and full-corpus checking remain operative.

The plan explains the main tag versus attached development bundle, original SHA preservation, compact versus full manifests, immutable publication failure behavior, final-source CI and retention/recovery limits. The future-release-only immutability statement agrees with [GitHub's primary documentation](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes), accessed during this review. I make no claim that immutability is currently enabled or that public archive restoration has occurred.

## Integration

No blocking finding. The delta changes only five Markdown files. Current checker, six app-bound required contexts, CI permissions, Rust source and dependencies are unchanged. Saved original PR/API evidence identifies an open development-to-main PR at the recorded original head/main anchor; the two saved CI runs succeed and the saved checks contain successful app-15368 entries for the six protected contexts. These are inspected historical captures, not a fresh remote readback.

Retaining the no-Git documentation checker while assigning footprint checking to a separate existing-job command avoids changing ADR-0043's contract. The trial/map, governance-inclusive bundle, source-equivalence checks, clean clone and explicit lease/rollback gates address the migration's integration hazards at the proper later checkpoints.

## Source and reading limits

Read AGENTS.md and CLAUDE.md fully; current roadmap state; both applicable review skills and the five-role master plan; the full changed ADR, plan and five-file diff; ADR-0025 and ADR-0043 governance; affected task contracts/maintenance additions; code-review, documentation, commit and release standards and relevant security/testing guidance. I used the delegated change description before source review and read the saved original PR body later for historical context. Not every unrelated ADR/standard or lengthy unchanged task review-history row was re-read; broad command output had truncation, so no complete-repository reading claim is made.

No prior review artifact or peer R2 content was opened before this freeze. The proposed source itself discloses the R1 release-standard finding; that disclosure is not an independent discovery. Recovery/API summaries and bounded local checks were inspected; the original large evidence corpus, CI log ZIP contents and every historical source tree were not independently re-audited. No clone was newly created; recovery hashes were checked in the existing recovered checkout. No remote settings, refs, publication, repository files or commits were changed. This external report location overrides the ordinary in-repository filing/index procedure under the explicit task instruction.

## Verdict

**Approve — governance/recovery scope only.** All five role passes have no blocking or non-blocking finding requiring a change. This is the frozen independent initial R2 CODE report, not ADR Acceptance, paired-review closure, migration approval evidence, product-release approval or authorization to merge. Complete the separate complementary round and deliberate Acceptance boundary before dependent implementation; preserve the stated publication and final-source gates.
````````

### governance-r2-integrity.md

SHA-256: `23558338d4e0947a575a72426fccabe9433f58c41862d010444f63378ea17dfc`.

````````markdown
# Code review 2026-10-16 — PR49 cleanup governance/recovery R2 integrity

Fresh independent complementary review of archive bytes, provenance, recovery and ref boundaries. All five roles were executed sequentially. No peer R2 report was read before this report was frozen. This external report is an input to the consolidated review; it does not modify the repository or authorize merge.

- **Change:** `97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4..94fd86c8328ff6951aa61b06444d17f8ccefe25d` (five Markdown files, 217 additions).
- **Source SHA:** `94fd86c8328ff6951aa61b06444d17f8ccefe25d`.
- **Reviewer:** Codex independent agent `cleanup_governance_r2_integrity`.
- **Risk class:** Ordinary governance/documentation; archive and Git-ref operational boundaries examined explicitly.
- **Security-review cross-reference:** N/A for the formal kernel trigger: no runtime, unsafe, dependency, cryptographic primitive or kernel authorization change.
- **Basis:** AGENTS/CLAUDE, current roadmap, applicable review skills/master plan, relevant documentation/release/infrastructure/review standards, ADR-0025/0043, Proposed ADR-0044, approved cleanup plan, T-049/T-056 maintenance clauses, actual retained archive/recovery/API evidence. This is a bounded governance review, not a full kernel or all-ADR correctness audit.

## Correctness

**Clean; zero findings.** Independent verification reproduced the claimed baseline rather than relying on the analysis script or recovery-proof JSON:

| Verification | Actual result |
|---|---|
| Original main-to-development diff | 1,008 files, +956,905 / -3,003 |
| Candidate inventory membership | Exactly 804 unique non-Markdown report paths; equals the diff candidates |
| Candidate historical membership | Same set across all 145 unmerged commits; no extra historical-only candidate path |
| Original Git blobs / existing recovered files / streamed tar members | 804/804 sizes and SHA-256 values match in each source |
| Candidate current-tree bytes / additions | 134,293,614 / 927,770 |
| Retained tree / reports bytes | 10,697,725 / 478,307 |
| Largest retained blob | 576,155 bytes, the T-056 parser security review |
| Recomputed dependency inventory | Exact match: 348 links in 46 documents; 1,830 original-SHA mentions in 131 documents, identifying 129 original commits |

The projection to 204 files and 29,135 additions is correctly described as pre-policy/pre-citation, not a final publication promise. The working delivery budget remains an execution gate.

Recomputed asset digests match the committed recovery checkpoint:

- `original-development.bundle`: 63,841,865 bytes; SHA-256 `a622d9e31929132c547d7b1a32a56aba31523338e81762c4004d64c8a6f5d0f9`.
- `payloads.tar.gz`: 66,475,418 bytes; SHA-256 `032b586ec81c38d37d45f5076c628707a3b35484da4388499f1d9896c44e3117`.

`git bundle verify` reports complete history and the original development ref. The existing independent recovered repository is at full original97, has no object alternates, uses the external bundle as origin and passes `git fsck --full --no-reflogs`. The tar was read as a stream, with exactly the expected 804 ordinary files and no duplicate or extra file; no extraction, new clone or archived script execution was performed. This independently verifies the existing recovery, without claiming to have created it.

## Style

**Clean; zero findings.** English Markdown, explicit full source identities, Proposed status and a separate Acceptance boundary are present. No runtime code, dependency, proprietary blob or diagram is added. Cosmetic spacing is not raised as a blocker. Canonical historical Markdown and task delivery evidence remain intact; maintenance criteria are additional unchecked work, not retroactive test or Done assertions.

## Test coverage

**Clean for this governance unit; execution validation remains pending.** Ran the full eight-family documentation command at source94fd86c: 401 Markdown files, 7,215 local targets, 925 fragments, zero findings. Exact-range `git diff --check` passes. Independent byte/hash, original-tree, historical-path, dependency-inventory and Git-recovery checks above cover the consequential current claims.

Inspected retained fixture logs: 161 checker and 124 metadata tests passed on each of Python 3.9 and 3.13. These retained logs are not independently source-SHA-attested by their text and are not presented as newly executed at94fd86c. Checker/fixture implementation is unchanged by this five-Markdown-file range; identical full fixture suites and Rust/QEMU suites were not rerun.

Captured original push/PR run metadata identifies original97 and success for runs38801339254 and38801349720. Captured check metadata has the seven successful job names, including all six required app15368 contexts, at original97. This inspection is historical evidence, not a CI rerun or proof for rewritten history.

The post-governance bundle, public download restoration, immutable-publication verification, original-to-new map and every mapped noncandidate-tree comparison, footprint fixtures/rejection probes, clean remote clone and final hosted source gates remain mandatory later checks. None is claimed delivered by this proposal.

## Documentation

**Clean; zero findings.** The R1 release-scope ambiguity is independently resolved by ADR-0044 line38, the plan's evidence-only paragraph and T-056 line70. They define archival hosting with immutable bytes, published digests, original provenance and tested recovery, while expressly preserving product release gates/signing and making no maintainer-key signature claim. T-056 grounds the minimal release-standard pointer after Acceptance and before publication; release.md has not been changed prematurely.

The proposal distinguishes the clean evidence-tag source archive from the attached authoritative original development bundle. It freezes the later post-governance bundle before the in-Git catalog to avoid self-reference. Original historical SHA literals, verdicts, severities, measurements and procedural limitations survive; dated citation notices and a recovery/map route explain changed navigation without claiming historical runs on new hashes. ADR-0043's full-corpus and attribution rules remain intact. ADR-0025 forward references resolve to actual T-049/T-056/T-047 ownership; careful reread and separate Acceptance are still required.

## Integration

**Clean; zero findings.** Fresh read-only remote inspection exactly matches the saved 17 advertised refs. There are no advertised tags. Clean mainc16997e contains no candidate payload, and all 16 non-development advertised refs have zero reachable candidate-path objects. The pre-existing local main400dec041a65fea163d4cbefb671f355aaf416ca is distinct from the approved advertised mainc16997e003fbd1726d1205734380394781c52002; this review did not modify either or newly establish its earlier historical value.

Fresh API reads confirm main protection is byte-structurally equal to the saved JSON, no releases exist, and release immutability remains disabled. The proposed future setting change and clean-main evidence tag are explicitly authorized archival steps; no archive durability is claimed today. [GitHub's primary documentation](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes) confirms repository immutability applies to future releases. The draft/upload/download/restore/publish/immutable-verify order and stop-on-failure condition are therefore material gates before actual local adoption/removal and remote replacement.

The approved rewrite is confined to enumerated paths in clean-main..frozen-development, tested in isolation; it keeps meaningful ordering and records empty-commit handling. Actual development replacement waits for archive verification and citation reconciliation, then uses an explicit lease expecting original97. A lease mismatch stops. Emergency rollback is development-only with a lease on the observed new tip. Main, unrelated existing refs and protection remain outside authority. No remote backup tag retaining original97, blanket push, source-repository pruning/GC or promise of hidden GitHub-object erasure appears in the plan.

The subsequent footprint command has explicit per-blob/report-aggregate/catalog limits, meaningful fixtures, exact-path reviewed exceptions and existing-lint-job wiring. It preserves check-docs.py's no-Git/offline contract, existing required app-bound contexts and CI permissions. T-049/T-056 ownership, later review units, task status transitions and maintainer SECURITY wording/merge boundaries are explicit.

## Verdict

**Approve this bounded governance/recovery R2 source.** Zero Critical, High, Medium or Low findings; zero unresolved blockers. The R1 clarification is substantiated independently. This verdict supports the separate ADR Acceptance after the other complementary R2 and deliberate reread; it does not certify pending archive publication, rewrite, prevention tooling, final CI, task Done promotion or PR merge.

No repository edit, source/ref mutation, new source dump, archive extraction, publication or peer R2 read was performed. Only this external report and adjacent SHA-256 file were written.
````````
