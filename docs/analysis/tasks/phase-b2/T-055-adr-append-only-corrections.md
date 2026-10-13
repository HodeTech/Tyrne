# T-055 — Apply append-only corrections to Accepted ADRs

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** In Review
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-056](T-056-docs-consistency-automation.md)
- **ADRs required:** [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md) (Accepted 2026-10-12; reviewed execution and corpus policy)

---

> **Approved contract reconciliation (2026-10-12).** The maintainer approved the [preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and ADR package. The criteria below are the executable contract; dated opening observations remain historical. This preparation records no task delivery. Each implementation step includes verification and two fresh independent review rounds under [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); new task states stop at `In Review`.

## User story

As a reader opening an Accepted ADR, I want stale or unsubstantiated statements to carry a visible, dated pointer to their correction, so that I do not act on a superseded fact while the historical text stays intact.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). ADRs are append-only (see [`docs/decisions/README.md`](../../../decisions/README.md) and [`supersede-adr`](../../../../.agents/skills/supersede-adr/SKILL.md)); corrections are made with banners, revision notes or appended sections, never by rewriting the original reasoning. Track B.2-2 of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) lists five places where the project's forward-pointer mechanism was missed: ADR-0008's "safety-relevant" aliasing rationale has no evidence behind it (and is duplicated into `hal/src/cpu.rs`), ADR-0033 does not point at its own post-Accept correction, ADR-0011 still says QEMU `virt` is GICv3, ADR-0012's "EL drop" open question was never marked resolved, and ADR-0018 is the only early ADR without a pros-and-cons section. The renumbering of planned ADR numbers in phase ledgers is [T-054](T-054-adr-ledger-renumbering-cascade.md), not this task.

## Acceptance criteria

- [x] **ADR-0008** (§Revision notes, 2026-05-22 entry, line 158 at opening) gets an append-only follow-up note, and the duplicated rationale in `hal/src/cpu.rs` (doc comment on `IrqGuard`, lines 99-104) is changed to match — comment only. Retract the unverified "vtable references that alias unrelated data in `.rodata`" explanation with a dated append-only note, preserving the historical QEMU failure observation and the defensible "avoid fat-pointer vtable dispatch on the critical-section path" rationale. Match the IrqGuard comment to that correction and record its source provenance; the maintainer already selected this retraction in the approved plan.
- [x] **ADR-0033** has a top-of-file blockquote (in the style of ADR-0022 lines 7-11) stating that the shipped `KBASE` is `0xFFFF_FFFF_4008_0000` (not `0xFFFF_FFFF_8008_0000`) and that a single offset (`KERNEL_HIGH_HALF_OFFSET`) replaces the two-offset model described in the body, linking to the 2026-05-30 correction in its §Revision notes (line 188 at opening). The body is untouched.
- [x] **ADR-0011** has a one-line correction banner at the top in the same wording pattern as the banners on ADR-0004, ADR-0006 and ADR-0012 (their line 7): QEMU `virt` is GICv2 in v1, not GICv3; the trait surface is version-agnostic and unaffected. The banner text lives in `docs/decisions/0011-irq-controller-trait.md`, so its link to the correcting ADR is the sibling target `[ADR-0036](0036-qemu-virt-gicv2-no-iommu-v1.md)` (for navigation from this task: [ADR-0036](../../../decisions/0036-qemu-virt-gicv2-no-iommu-v1.md)).
- [x] **ADR-0012** §Open questions (line 148 at opening): the "EL drop" bullet is struck through and followed by `*Resolved 2026-04-27 by [ADR-0024](0024-el-drop-policy.md) (EL drop to EL1 policy).*` — a sibling link, because the text lives in `docs/decisions/0012-boot-flow-qemu-virt.md` (for navigation from this task: [ADR-0024](../../../decisions/0024-el-drop-policy.md)) — mirroring the existing "Boot-time MMU activation" treatment on the same list.
- [x] **ADR-0018** gains an appended `## Pros and cons of the options` section that restates the tradeoffs of the six options in §Considered options (lines 33-49), placed after the existing sections and before or after §References consistently with the template; no existing text changes.
- [x] For every touched ADR, `git diff` shows only additions, with one exception: the strikethrough markup wrapping the existing ADR-0012 sentence. No status line changes in the five corrected ADRs. Reconcile canonical ADR index membership and title/status/date against actual headers; report every anomaly and disposition instead of requiring "no anomalies". Report title/filename-slug differences (including 0040–0043) separately from index/header mismatches; do not rename filed records. Handle Deferred, prose-extended dates, partial supersession and reserved 0034 from existing evidence without inventing metadata. Align the sync-adr-index procedure vocabulary/reporting with those existing forms without concealing anomalies.
- [x] Each new banner or note carries the date it is applied and a link to the document that supplies the correction.

## Out of scope

- Re-sequencing tentative ADR numbers in phase ledgers — [T-054](T-054-adr-ledger-renumbering-cascade.md).
- Superseding any ADR or changing a decision; these are corrections to labels and rationale only.
- ADR-0034 (still an unwritten reserved slot).

## Approach

Copy the established banner shapes rather than inventing new ones: ADR-0022 lines 5-11 for a multi-paragraph "partially superseded" pointer, ADR-0004/0006/0012 line 7 for one-line corrections, and the struck-through "Resolved" bullet already present in ADR-0012 §Open questions. For ADR-0008, apply the approved append-only retraction of the generalized aliasing explanation; preserve the recorded QEMU observation and direct-dispatch rationale without claiming retained compiler/Miri/disassembly proof. Apply the same wording change to the `IrqGuard` doc comment so the code and the ADR do not diverge again.

## Definition of done

- [x] Every relative link in each touched file resolves.
- [x] `cargo fmt --all -- --check` and `cargo host-clippy` clean (the `hal/src/cpu.rs` doc-comment change must not trigger a lint); `cargo host-test` unchanged.
- [x] `git diff --stat` is limited to the five ADRs, `hal/src/cpu.rs`, `docs/decisions/README.md`, `.agents/skills/sync-adr-index/SKILL.md`, the explicit anomaly/disposition report and associated reviews/indexes, this task file and `docs/roadmap/current.md`.
- [x] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) (scope `adr`; a separate commit for the `hal/src/cpu.rs` comment is acceptable).
- [x] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

**Step-scoped evidence allowance.** In addition to the named content files, the step may update this task, `docs/roadmap/current.md`, the B.2 task/track indexes, governing decision references, source-bound reports/raw evidence, canonical review artifacts and their indexes where necessary. Verify this allowance against the step commit range, not the full stacked branch. Record a demonstrated existing-scope reason for any further file.

## Design notes

- **Location re-verification (2026-10-11, HEAD `400dec0`):** ADR-0008:158 (Revision notes entry) and `hal/src/cpu.rs:99-104` match; ADR-0033 body lines 67, 105-112 still show `KBASE = 0xFFFF_FFFF_8008_0000` and the correction sits at line 188; ADR-0011 line 11 says "GIC v3 (QEMU `virt`)"; ADR-0012 §Open questions still lists "EL drop" unstruck; ADR-0018 has headings Context, Decision drivers, Considered options (Badge scheme, `reply_recv` fastpath), Decision outcome, Consequences, References and no pros-and-cons section.
- **Resolved 2026-10-12:** retract the unverified generalized .rodata aliasing explanation, retaining the recorded QEMU observation and defensible direct-dispatch rationale; append ADR-0018 tradeoffs without changing existing sections. Report source/index/slug anomalies separately under ADR-0043.
- The original five-item scope touches source only through the ADR-0008 comment. The dated step allowance additionally records timer rustdoc; both are comment-only and need no new audit entry.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-12 | Codex (AI agent), maintainer-approved reconciliation | Old: index needs no edit / no anomalies and DoD excludes index/sync skill. Approved replacement: source/header/index reconciliation with explicit anomaly/disposition report, title-slug differences including 0040–0043 and existing Deferred/date/partial/reserved forms; index/sync skill/reports allowed while five ADR corrections stay append-only with only the stated strikethrough exception. See [approved preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); preparation only, status unchanged. |
| 2026-10-12 | Codex (AI agent), Step 0 round-1 correction | R1-GOV-01 confirmed: replaced the residual evidence-or-retraction AC/Approach alternative with the already-approved retraction. Historical observation/direct-dispatch rationale and append-only limits remain explicit; no new decision or delivery. |
| 2026-10-13 | Codex (AI agent), Step 7 kickoff | Starts after T-050 canonical boundary 69afa33 and both fresh rounds. [Full preflight/scoped plan](../../reports/2026-10-13-t055-adr-correction-preflight.md) records all five approved corrections, exact metadata/index anomalies and four demonstrated additional surfaces before edits: ADR-0010/timer.rs existing ceiling-contract clarification, supersede-adr existing append-only/template repair and P7 compatibility anchor preserving ADR-0015. No new decision/ADR/runtime change; status In Progress, delivery/checks/review rounds pending. |
| 2026-10-13 | Codex (AI agent), Step 7 implementation | Applied five approved ADR corrections plus pre-recorded ADR-0010/timer rustdoc and supersession/P7 compatibility repairs; historical bodies/metadata preserved with only approved EL-drop wrapper exception. Exact 42-row index synchronization fixes 14 title/one Date mismatches and separately reports 35 retained title/slug differences and supported historical forms. [Reconciliation/evidence](../../reports/2026-10-13-t055-adr-correction-reconciliation.md): fmt, host-clippy, host-test exit 0; 366 passed, two ignored; source comments only and raw hashes checked. Both fresh code/security rounds pending; In Progress, boxes unchecked. |
| 2026-10-13 | Codex (AI agent), Step 7 R1 scope clarification before fix | Independent code/security assessments converged on one Low stale timer-helper citation. Separately, root confirmed Low C-ROOT-01: propose-standard-change still permits in-place Accepted ADR amendments contrary to ADR-0025 Rule 2. [Dated extra-file reason](../../reports/2026-10-13-t055-adr-correction-preflight.md#round-1-additional-file-reason--recorded-before-correction) adds this fifth procedure file before mutation under the existing allowance. Correct factual rider/Proposed draft wording while preserving approval for substantive new decisions; no new ADR or policy. Independent initial reports remain intact; fixes and both rounds are still pending. |
| 2026-10-13 | Codex (AI agent), Step 7 R1 correction | Fixed the one independently corroborated timer rustdoc issue and root-origin C-ROOT-01 after recording the additional-file reason. Existing decision/approval boundaries and executable source unchanged. Post-fix fmt/host-clippy, preservation/index/raw-hash and bounded navigation checks pass; original test capture stays bound to f256a610 and default raw blank-EOF diagnostic is retained. [Separate correction evidence](../../reports/2026-10-13-t055-verification-evidence/r1-correction-verification.json); bounded R1 verification and fresh R2 pending. |
| 2026-10-13 | Codex (AI agent), Step 7 canonical boundary | Both fresh code/security rounds Approve corrected cumulative e8104e3..23391c7; two unique Low R1 findings verified fixed, zero new R2 or unresolved findings. [Code](../../reviews/code-reviews/2026-10-13-t055-adr-corrections.md) and [security](../../reviews/security-reviews/2026-10-13-t055-adr-corrections.md) retain all four actual reports, checklist/read provenance and limits. All seven AC/five DoD checked against source/evidence and scoped allowance; original raw captures unchanged, canonical diagnostics separate. In Review without date_done or maintainer approval; Step 8/T-052/T-053 starts next. |
