# T-055 — existing-document review and scoped plan

- Source: clean development `523615603f87f6f11f2030db4d6d974c38330f0d` on 2026-10-13; T-050 fresh R2 pending. No T-055 repository implementation has begun.
- This is coordinator preparation, not either fresh implementation review or maintainer approval. Existing AGENTS prerequisites, Accepted ADR-0025/0043 and the approved task/plan apply.
- Full executable T-055 contract reread. Rechecked ADR-0008 revision/IrqGuard comment, ADR-0011 Context, ADR-0012 Open questions, full ADR-0018, ADR-0033 top/canonical correction, full ADR index/sync skill and provenance commits. The five approved corrections choose no new decision or status.

## Index baseline

Read-only header/index extraction retained in `/tmp/tyrne-b22-t055-baseline-index.json` (its source74f8e837 has identical ADR/index bytes to this preparation source). 42 numbered files/42 rows; 14 literal title mismatches (8 descriptive differences and 6 backtick-only differences), one Date mismatch (0023 prose-extended source Date versus index ISO prefix), 35 normalized full-title/filename-slug differences. No filename/status difference in the actual indexed rows. Do not mistake row/header agreement after synchronization for removal of title/slug differences. Reserved0034, Deferred0023, partial0022 supersession and 0041→0042 are existing evidence, not new vocabulary decisions.

Rebuild exact source-title/status/date rows; retain the complete authoritative prose-extended Date, report all initial differences and noncanonical forms, do not invent dates or rename records. Sync skill's valid-status/date/supersession vocabulary must distinguish whole supersession from partial-axis riders and ordinary correction pointers. Whole supersession target must exist and be Accepted; partial-axis historical status is not a reason to erase the standing typed-error decision. ADR README Format may describe the existing observed forms under ADR-0043, without changing metadata semantics.

## Existing timer discrepancy — bounded existing-contract correction

HAL timer rustdoc52–53 and ADR-0010 Decision outcome78 describe nearest-multiple deadlines, conflicting with the existing reaches-or-exceeds contract and current ceiling implementation. Read full ADR-0010 and relevant timer helpers. `resolution_ns_for_freq`145–160 computes nearest integer period/min1ns; `ns_to_ticks`207–220 uses saturating ceiling. These are distinct calculations. `git show d820a88d902e77ccf33b30ebe9c7be03a9c25cea` and `5c9cf069c2f5fa3be77c048d865ae89c4055ba11`, together with T-012 review history112, explicitly record the accepted floor→ceiling fix and the non-divisor3Hz/333333334ns→2ticks regression. d820a88 is an ancestor of merged-mainc16997e. No fresh runtime policy or function change is needed.

Recommended T-055 allowance: an append-only dated factual clarification in existing ADR-0010, plus comment-only Timer::resolution_ns wording. Preserve old body/Date/Status. Explain approximate reported resolution separately from the already-shipped deadline conversion; do not promise representability beyond saturating counter bounds. Source provenance and named owner are existing T-012/T-055. This adds two demonstrated existing-scope files; record that reason before implementation and verify comment-only source/append-only ADR deltas.

## Additional real navigation/procedure drift — do not suppress in gate

Read-only coarse tracked-corpus diagnostic `/tmp/tyrne-b22-readonly-corpus-scan.py` (existing third-party Markdown tool, NOT shipping T-056 parser/grammar) at source5236156 scans359MD,5938local targets/601fragments. Six candidates independently inspected: two rendered template destinations in supersede-adr skill (NNNN-slug.md, MMMM-new-slug.md), and four old P7 fragments in Accepted ADR-0015. Source heading is `P7 — No proprietary binary blobs in the kernel`; old destinations use `p7--no-proprietary-blobs`. No claim of complete Markdown grammar or shipped gate coverage.

Recommended T-055 allowance: render supersession examples as tagged markdown code fences (template syntax is quoted data); fix its existing minor-amendment instruction to append-only rider wording supplied by Accepted ADR-0025 rather than an in-place rewrite. Add invisible legacy id `p7--no-proprietary-blobs` immediately before the matching P7 standard heading, preserving all four Accepted ADR-0015 historical links/body bytes and current heading. This is navigation/authority reconciliation, not a standard rule change/new ADR or historical exception. Add the two demonstrated existing-scope files and explicit provenance to T-055 report/history at kickoff. Do not change these files during T-050 R2.

## Approved correction constraints

- IrqGuard: preserve 4fe547cf47beb54a51ad09f8a5705d2f30841a29's recorded QEMU failure and concrete-dispatch choice; retract generalized rodata/vtable aliasing cause as unverified. No retained compiler/Miri/disassembly proof, no broad trait-object-unsoundness claim. Comment and rider agree.
- ADR-0033: dated top pointer to existing 2026-05-30 single-offset/KBASE correction; unchanged body.
- ADR-0011: dated GICv2/no trait-surface-change pointer to ADR-0036; unchanged body.
- ADR-0012: exact original EL-drop sentence preserved inside strikethrough; resolved2026-04-27 link to ADR-0024; separately date pointer application2026-10-13 so resolution date is not claimed as application date.
- ADR-0018: append dated pros/cons of all six historical options, with links to original considered-options/decision sections. Avoid amplifying decision-time badge emulation/API-compatibility claims as current guarantees; present historical tradeoffs and retain current source-defined boundary. No option/outcome changes.
- Verify every touched ADR has additions only, except stated ADR-0012 strikethrough; no status/date/body rewrites. Root sole writer; fmt/host-clippy/host-test required; runtime source otherwise byte-identical except the two documented rustdoc corrections. Two fresh complementary rounds, separate security pass because rationale describes unsafe/scheduler boundary. New T-055 stops In Review.

## Step 7 kickoff — 2026-10-13

T-050 completed both fresh code/security rounds and canonical publication at 69afa33f67ea9dd7e97c127841222d2edc5c9f00 before this task starts. Its reviewed source was 946f45f; these are distinct checkpoints. The preparation snapshot above remains historical; this kickoff records execution authority and planned extra surfaces before modifying them. [T-055](../tasks/phase-b2/T-055-adr-append-only-corrections.md), [approved plan](2026-10-12-phase-b2-track2-preflight-and-plan.md), [ADR-0025](../../decisions/0025-adr-governance-amendments.md) and [ADR-0043](../../decisions/0043-documentation-corpus-consistency.md) supply the settled contract. No new decision or ADR is needed.

The five original ADR corrections, CPU rustdoc, exact source-metadata index reconstruction, procedure alignment and explicit anomaly report are the named scope. Four further files have demonstrated existing-scope reasons under the approved step allowance:

| File | Evidence and bounded correction |
|------|---------------------------------|
| [ADR-0010](../../decisions/0010-timer-trait.md) | Existing reaches-or-exceeds contract and merged T-012 ceiling fix conflict with old nearest-multiple prose; append dated source-backed clarification, preserving original body/status/date. |
| [Timer rustdoc](../../../hal/src/timer.rs) | Same stale nearest-deadline wording; comment-only correction distinguishes approximate reported resolution from ceiling conversion and saturation. No function/signature/behavior change. |
| [supersede-adr skill](../../../.agents/skills/supersede-adr/SKILL.md) | Rendered dummy destinations are broken, and edit-in-place minor-amendment instructions conflict with Accepted ADR-0025 Rule 2; quote templates as data and apply the existing append-only discipline. No new supersession rule. |
| [architectural principles](../../standards/architectural-principles.md) | Four preserved ADR-0015 citations use the retired P7 fragment; add one invisible compatibility anchor at the exact current P7 heading, without changing rule text or ADR-0015 bytes. |

Apply the approved corrections and index/report together, then run append-only/source-token/metadata/navigation checks plus required fmt/host-clippy/host-test. Commit implementation before fresh R1 code/security contexts. Verify/fix/commit every confirmed finding, then use different fresh R2 contexts for the corrected cumulative range; bounded fix verification closes R2. Publish all actual reports/indexes and stop task state at In Review, then automatically start Step 8. No task delivery or test execution claimed at kickoff.

## Round 1 additional-file reason — recorded before correction

After the independent assessments of frozen implementation f256a610, the coordinator confirmed Low C-ROOT-01 in [propose-standard-change](../../../.agents/skills/propose-standard-change/SKILL.md): its amendment path still instructs rewriting an Accepted ADR in place, contradicting [ADR-0025 Rule 2](../../decisions/0025-adr-governance-amendments.md#rule-2--riders-are-not-failures-their-frequency-is-a-signal). This fifth additional file has the same demonstrated existing-scope procedure drift as the already-recorded supersede-adr correction. Record this reason before editing the skill; align it with dated append-only factual riders, editable Proposed drafts and the existing new-decision/supersession approval gates. No new rule, ADR or decision is proposed. Both reviewers assess this coordinator-origin finding after their independent checkpoints; fresh R2 reviews the cumulative correction. The independently found timer helper citation is a completion of the already-recorded timer rustdoc surface, not another additional file.
