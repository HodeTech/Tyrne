# T-054 — Cascade the ADR ledger renumbering across phase files

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** In Review
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none (phase-level precondition: [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) `Accepted`, see the [task index](README.md))
- **Informs:** [T-056](T-056-docs-consistency-automation.md), [T-074](T-074-phase-c-readiness-sweep.md)
- **ADRs required:** [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md) (Accepted 2026-10-12; reviewed execution and corpus policy)

---

> **Approved contract reconciliation (2026-10-12).** The maintainer approved the [preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and ADR package. The criteria below are the executable contract; dated opening observations remain historical. This preparation records no task delivery. Each implementation step includes verification and two fresh independent review rounds under [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); new task states stop at `In Review`.

## User story

As the author of a future ADR, I want the phase ledgers to assign each planned ADR a stable purpose identity and allocate its number only when filed, so that "which number do I use" never needs a cascade-renumbering pass.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). Each phase file carries a ledger of *planned* ADRs with *tentative* numbers ("final numbers are assigned when the ADR is actually written"). Two problems exist. First, the plan item at `phase-b2.md` (snapshot line 226) records that Phase C's 2026-06-01 renumbering (ADR-0040…0044) was never cascaded: Phase C and Phase D both claim ADR-0042, 0043 and 0044 (`phase-c.md` ledger vs `phase-d.md` ledger). Second, the real ADR-0040 is now the Phase B.2 governance ADR, so *every* placeholder from 0040 upward is off by at least one. This is the third time the same cascade is needed (Blockers D4-001/D4-002 of the 2026-05-22 master review, the 2026-06-01 shift, now 0040).

Current ledger inventory (verify before editing): Phase C 5 rows (0040–0044), D 5 ADR rows plus one `_(none)_` row (0042–0046), E 6 (0047–0052), F 5 (0053–0057), G 5 (0058–0062), H 3 (0063–0065), I 3 (0066–0068); about 110 lines (143 occurrences) mentioning `ADR-004x…006x` across `phase-b2.md`, `phase-c.md`…`phase-i.md` (counted 2026-10-11; recount before editing).

## Acceptance criteria

- [x] Record the maintainer-approved ADR-0043 stable-identity decision; do not execute another numeric cascade.
- [x] Migrate all 32 numbered C–I ledger definitions to unique milestone-plus-purpose identifiers (for example ADR-C1-secondary-core-start and the distinct ADR-F2-i2c-service / ADR-F2-spi-service). No live ledger definition retains a tentative numeric allocation.
- [x] Resolve every live prose/cross-phase reference by meaning to the unique definition and link its ledger location; never perform a global numeric replacement. Real filed references, especially ADR-0040, remain numeric.
- [x] Add dated per-ledger notes explaining removal of tentative numbers, actual allocation at filing and historical aliases. Preserve reserved 0034, explicitly unallocated object-lifecycle/G1.5/J decisions and dated old numeric evidence without treating aliases as current allocations.
- [x] Align phase-b2.md and the ADR index Numbering gaps note with the workflow. Verify the already-filed ADR-0040 Acceptance-time rider covers both numbering and the limited Track B.2-2 execution extension; do not rewrite its original body.
- [x] Record a reproducible source-bound check showing exactly 32 unique definitions, resolved live references and no tentative numeric ledger definitions. Count repeated references separately from definitions.

## Out of scope

- Writing any of the planned ADRs.
- ADR-0034 (kernel-image section permissions): it is a reserved slot below 0040 and is not renumbered.
- The object-lifecycle ADR slot named in `phase-c.md` carry-forwards (it has no number yet).
- Folding Phase C review items into the milestones — [T-074](T-074-phase-c-readiness-sweep.md).

## Approach

Use Accepted ADR-0043's stable milestone-plus-purpose workflow.
Read every ledger row and cross-reference by meaning, including the two F2 decisions and ambiguous C/D old numbers.
Replace only live planned definitions/references, add navigable ledger anchors and retain dated historical aliases, filed numeric citations and unallocated planning.
Verify all 32 definitions and their references, the ADR-0040 rider and the numbering note; record the reproducible output.

## Definition of done

- [x] Every relative link in each touched file resolves.
- [x] `git diff --stat` is limited to `docs/roadmap/phases/*.md`, `docs/decisions/README.md`, this task file and `docs/roadmap/current.md`.
- [x] The duplicate check output is pasted into the review history.
- [x] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) (scope `roadmap`).
- [x] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

**Step-scoped evidence allowance.** In addition to the named content files, the step may update this task, `docs/roadmap/current.md`, the B.2 task/track indexes, governing decision references, source-bound reports/raw evidence, canonical review artifacts and their indexes where necessary. Verify this allowance against the step commit range, not the full stacked branch. Record a demonstrated existing-scope reason for any further file.

## Design notes

- **Resolved 2026-10-12:** ADR-0043 selects stable purpose identities; the former numeric alternative is not executable. The opening numeric inventory is retained as dated provenance.
- The ledger convention "Numbers are tentative" is already stated in every ledger; the problem is that readers (and review documents) still quote the numbers as if they were reserved.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-12 | Codex (AI agent), maintainer-approved reconciliation | Old: either numeric cascade or slugs, including a no-old-number-string check. Approved replacement: all 32 semantic purpose definitions/references, separate historical aliases/filed numbers/unallocated decisions and verification of the already-filed Acceptance-time rider. See [approved preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); preparation only, status unchanged. |
| 2026-10-13 | Codex (AI agent), implementation author | Step 9 kickoff after Step 8 both-round canonical boundary at `f8c9b7f34a28d0974cbc9e03f1ef8355dc2df4f3`. [Preflight](../../reports/2026-10-13-t054-identity-preflight.md) records full semantic planning review, all 32 source definitions, explicit reference resolution and the additional write-adr procedural reason before mutation. Accepted ADR-0043 selects stable purposes, no numeric cascade/new ADR/phase opening. Status In Progress; criteria unchecked pending implementation and both fresh paired rounds. |
| 2026-10-13 | Codex (AI agent), implementation author | [Implementation/evidence](../../reports/2026-10-13-t054-planned-adr-identity-migration.md): duplicate/source comparison `32 unique definitions; C5 D5 E6 F5 G5 H3 I3; 71 semantic reference source lines; 74 linked occurrences; 42 filed ADRs and 42 index record rows unchanged; errors 0`. All original purposes/milestones/complete notes preserved; numeric historical snapshots/filed citations remain distinct. In Progress/unchecked until both fresh paired review rounds and canonical publication. |
| 2026-10-13 | Codex (AI agent), confirmed R1 correction | Primary R1-C01 and security T054-R1-S01 independently identify one unique Low: Phase I's new workflow note referred to nonexistent local acceptance criteria. Full-source validation confirmed it; removed only that fragment and retained no-status/no-authorization wording, with no new milestone criteria. [Separate corrected-source check](../../reports/2026-10-13-t054-verification-evidence/r1-correction-verification.json) preserves original snapshots; 32/71/74/42/42 and zero errors. In Progress; actual peer cross-reading/fix verification and fresh R2 pending. |
| 2026-10-13 | Codex coordinator; four distinct independent reviewers | [Both fresh code/security rounds](../../reviews/code-reviews/2026-10-13-t054-planned-adr-identities.md) Approve cumulative `f8c9b7f..a93926b`. One unique R1 Low (R1-C01 / T054-R1-S01) fixed in a93926b and independently verified; zero new R2 or unresolved findings. Actual immutable peer initials and R1 finals fully cross-read; full final reports retained, source/capture hashes and separate publication checks recorded. All 11 criteria checked; In Review, no date_done or maintainer approval. T-047 starts next. |
