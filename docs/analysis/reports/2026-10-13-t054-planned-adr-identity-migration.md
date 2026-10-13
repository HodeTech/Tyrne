# T-054 — stable planned ADR identities

- **Date:** 2026-10-13
- **Author:** Codex (AI agent), implementation coordinator
- **Clean step base:** f8c9b7f34a28d0974cbc9e03f1ef8355dc2df4f3, development.
- **Pre-content kickoff:** f8c7e1f70e93e9cea4fef67c2b2077769bc9996d.
- **Authority:** [approved plan](2026-10-12-phase-b2-track2-preflight-and-plan.md), Accepted [ADR-0043](../../decisions/0043-documentation-corpus-consistency.md), [T-054](../tasks/phase-b2/T-054-adr-ledger-renumbering-cascade.md).
- **Delivery state:** In Review after [both fresh paired rounds](../reviews/code-reviews/2026-10-13-t054-planned-adr-identities.md); one unique R1 Low fixed and verified, zero new R2 or unresolved findings. No task Done, planned ADR filing/acceptance or Phase C/D opening claimed.

## Reviewed migration

All 32 numbered C–I ledger rows now define stable milestone-plus-purpose identities with explicit navigable anchors: C:5, D:5, E:6, F:5, G:5, H:3, I:3. I2C and SPI remain two separate F2 decisions. Each row retains its exact original purpose, milestone and complete old note, prefixed by a dated historical alias. D4's implementation-only row, unallocated object-lifecycle/G1.5/J planning and reserved 0034 are preserved.

The coordinator resolved 71 live reference source lines individually by meaning, resulting in 74 linked occurrences. These are references, not extra definitions. The [actual migration ledger](2026-10-13-t054-verification-evidence/live-reference-migration.json) preserves original source lines and actual replacements. This includes C's old 0040 versus filed governance 0040, C/D's ambiguous 0042–0044, D's historical SGI/IPI quotation versus GIC-400, F's cross-phase crypto/memory references and G's verification-tool/measurement references. No global numeric substitution was used.

Each ledger explains allocation at filing, preservation of the purpose as a historical alias and linkage of its existing row to the filed record. Where the phase already has acceptance criteria, they refer to the future filed record's Accepted state; planning identities convey no ADR status or implementation authorization. Phase I remains a sketch without newly invented criteria. Original dated C/D gate snapshots and E's 2026-05-22 cascade quote remain intact, with dated clarifications superseding only the allocation guidance. C's old tentative-number paragraph and B.2's opening remediation are retained as explicitly historical evidence. Runtime/backlog work and whole-phase gates remain outstanding.

Phase B.2's executable action, acceptance language and consistency-check description now match stable identities. The ADR-index Numbering gaps/creation guidance and conditional write-adr procedure preserve the identity during filing. The [preflight](2026-10-13-t054-identity-preflight.md) records the demonstrated additional skill-file reason before its edit. Filed ADR bodies, filenames, statuses and all 42 index record rows are unchanged. The existing ADR-0040 rider is verified to cover both rule 7's numbering clarification and rule 4's limited B.2-2 execution extension; it was not edited.

## Source-bound verification

The retained [bounded verification script](2026-10-13-t054-verification-evidence/verify-migration.py) reads the recorded clean Git base and current worktree. It verifies baseline hashes/rows, all definitions, complete historical notes, original/replacement reference lines, destinations and separate occurrence counts. It also checks classified residual historical numeric references, dated snapshots, reserved/unallocated planning, all 42 filed records/index rows and the existing rider. This diagnostic is specific to T-054; it does not implement T-056's parser, prove architectural correctness or verify Rust soundness.

~~~text
definitions: 32 unique
distribution: C=5 D=5 E=6 F=5 G=5 H=3 I=3
semantic reference source lines: 71
linked reference occurrences: 74
filed ADRs unchanged: 42
filed ADR-index rows unchanged: 42
errors: 0
~~~

See [implementation snapshot](2026-10-13-t054-verification-evidence/implementation-verification.json) and [evidence instructions](2026-10-13-t054-verification-evidence/README.md). The initial snapshot is taken against kickoff HEAD plus the actual content worktree; later review/fix commits are recorded separately without rewriting that initial result. The actual [navigation snapshot](2026-10-13-t054-verification-evidence/implementation-navigation.json) reports 374 visible Markdown files, 6,395 local targets, 743 fragments and zero candidates. Navigation uses the existing third-party diagnostic, with its grammar limitations stated separately from the source comparison. No runtime, build/configuration, Cargo dependency, CI or unsafe audit entry changes; no new QEMU/Miri/hosted CI result is claimed for this documentation migration.

## Implementation review boundary (historical checkpoint before R1)

Implementation and evidence are committed before R1. R1 primary code/complementary security and different fresh R2 reviewers inspect the actual frozen commit range. Their initial source checks precede any peer report or verdict exchange; full actual reports, confirmed findings/fixes and paired cross-reading chronology will be published in the canonical artifacts. No provisional future review verdict is asserted here. Criteria stay unchecked until both rounds and final publication checks finish; then T-054 stops at In Review pending maintainer PR review/merge.

## R1 confirmed correction

Both independent initial reports identified the same Low accuracy defect (primary R1-C01 / complementary T054-R1-S01): Phase I's copied workflow note referred to nonexistent acceptance criteria above. The coordinator read both full reports, verified the complete Phase I sketch and removed only that sentence fragment, retaining the explicit no-status/no-authorization boundary. No new Phase I criterion or future decision was introduced. Initial implementation/baseline/navigation snapshots remain byte-unchanged. A separate [R1 correction comparison](2026-10-13-t054-verification-evidence/r1-correction-verification.json) records the actual corrected worktree and fresh hashes. Both initial source checks preceded peer exchange; actual cross-reading and correction verification follow the correction commit. The unique finding count is one, not two; final R1 verdicts and R2 remain pending at this correction boundary.

## Final both-round and publication boundary

All four distinct final reviewers Approve corrected source through `a93926b3836e5e661495ed53356f1ded04dc216d`. The [code artifact](../reviews/code-reviews/2026-10-13-t054-planned-adr-identities.md) and [security artifact](../reviews/security-reviews/2026-10-13-t054-planned-adr-identities.md) retain full actual reports and actual cross-reading chronology. Original initial reports remain prefixes of their final reports; the one shared Low is counted once. R1 report-metadata QA remains separate from source findings. The [publication manifest](2026-10-13-t054-verification-evidence/publication-manifest.json) binds all final report bytes, original captures, ten reviewed content surfaces and the separate final source/navigation checks. Publication is coordinator bookkeeping, not another independent round. All eleven criteria are checked and T-054 is In Review without date_done; T-047 follows automatically. No external publication or stronger runtime/CI/maintainer certification is claimed.
