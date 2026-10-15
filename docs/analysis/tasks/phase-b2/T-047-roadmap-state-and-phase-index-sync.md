# T-047 — Synchronise roadmap live state and phase index

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** In Review
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none (phase-level precondition: [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) `Accepted`, see the [task index](README.md))
- **Informs:** [T-074](T-074-phase-c-readiness-sweep.md), [T-056](T-056-docs-consistency-automation.md)
- **ADRs required:** [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md) (Accepted 2026-10-12; reviewed execution and corpus policy)

---

> **Approved contract reconciliation (2026-10-12).** The maintainer approved the [preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and ADR package. The criteria below are the executable contract; dated opening observations remain historical. This preparation records no task delivery. Each implementation step includes verification and two fresh independent review rounds under [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); new task states stop at `In Review`.

## User story

As a maintainer (or agent) returning to the project after a pause, I want `docs/roadmap/current.md`, the phase index and the Phase B/C phase files to state the true current position and no stale "next step", so that the first file I open orients me correctly.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). `docs/roadmap/current.md` is documented as "a short pointer file" but has grown to ~18 dated banners, and its lower half still describes April–May 2026: the *Last completed task* bullet stops at T-028 although T-029 (Phase 1 and Phase 2) merged on 2026-06-01, *Next task to open* still names the already-finished `task_create_from_image`, *Next review trigger* still waits for the B6 closure trio, and *Active decisions* stops at ADR-0027. Several of these are recurrences of Blocker D4-003 from the 2026-05-22 master review. The relevant plan items are in [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) (Track B.2-2, "Roadmap & task/review index synchronization" and "ADR corrections & cross-links").

The ADR-0040 kickoff (2026-10-11) already did the following, so this task must **not** redo it: the new 2026-10-11 decision banner and the *Active phase / Active milestone / Active task / Working branch* bullets of `current.md`; the B.2 gating wording, the "Phase A … it is active" fix and the phase-count wording in `phases/README.md`; the dotted-ID/Track convention in `roadmap/README.md`; the status banners in `phase-b2.md` and `phase-c.md`; the supersession note in `phase-b.md`; the ADR-0040 index row; and the status sentences of `README.md` and `CLAUDE.md`.

## Acceptance criteria

- [x] `current.md` *Last completed work* names **T-030–T-037 / Track B.2-1** with PR #48 and its verified 2026-10-12 merge; historical completion also records **T-029** (Phase 1 PR #44, Phase 2 PR #45, both merged 2026-06-01 — confirm with `git log --date=short`), and a dated banner records T-029's completion; the PR #43 / `b6-closure` branch is marked merged and retired, and the *In review* bullet no longer contradicts it (plan items at snapshot lines 120, 165, 171).
- [x] The stale bullets are corrected: *Next task to open* and *Next review trigger* describe the Phase B.2 position (the selected Track B.2-2 work and its two-round step reviews, then the still-open HIGH correctness work; eventual phase-closure reviews belong to [T-075](T-075-phase-b2-closure.md)); *Active decisions* lists ADR-0030, 0031, 0033, 0037, 0038, 0039 and 0040 with their real statuses and no longer calls T-016 a draft; the *Notes* section is refreshed or explicitly marked historical, and its unsafe-log counts match the log (33 entries: 32 Active, 1 Removed — re-count before writing).
- [x] *Last reviews* includes the 2026-07-15 full-repository review with an explicit provenance sentence (the review is a local-only document and is not in the repository; `phase-b2.md` and the task files are self-contained), and any 2026-05-31 / 2026-06-01 reviews that are missing from the list.
- [x] The dated banners are in reverse-chronological order again (the 2026-05-08 / 2026-05-09 / 2026-05-08 sequence is out of order), and the file's opening sentence describes what the file now is. Move dated banners and old live-state snapshots to `docs/roadmap/current-archive.md`, preserving their dates, measured evidence and supersession notes. Keep a concise explicitly delimited live-state section in current.md and link the archive; record the archival boundary in the review history.
- [x] `phase-c.md` §"Carry-forwards from Phase B" gains the three missing seam-review forward-flags — gate-#3 context-resolution atomicity (relevant to C2/C3), gate-#1 loader trust, and an `SP_EL1` high-water-mark bullet distinct from the IRQ/`TTBR1` item — each cross-referenced to [the consolidated Phase-B security review](../../reviews/security-reviews/2026-06-01-phase-b-closure.md) and the milestone that makes it live (plan item at snapshot line 132).
- [x] `phase-b.md` B6 dependency-ordered task sequence: the status tags of steps 1, 5 and 6 read **Done** with their merge PRs (T-022 → #36, T-027 → #41, T-028 → #42), or the pre-closure narrative is wrapped in a "preserved as historical record" framing as the B5 section above it is (plan item at snapshot line 229).
- [x] Verification: every relative link in `current.md`, `phase-b.md` and `phase-c.md` resolves; `grep -n "it is active" docs/roadmap/phases/README.md` returns nothing; `git diff --stat` includes only these content files, the linked archive and the approved step-scoped tracking/evidence files.

## Out of scope

- The Phase B task-file frontmatter and the `phase-b/README.md` index — [T-048](T-048-phase-b-task-corpus-sync.md).
- The review-family README indices — [T-049](T-049-review-indices-sync.md).
- Re-sequencing the ADR ledgers — [T-054](T-054-adr-ledger-renumbering-cascade.md).
- Folding Phase C's review-derived items into C1–C5 — [T-074](T-074-phase-c-readiness-sweep.md).

## Approach

Separate live state from the preserved historical tail; update live claims from actual source/task/merge evidence instead of treating kickoff bullets as immutable current truth. Take every fact from the repository, not from the old text: PR numbers and merge dates from `git log --date=short`, ADR statuses from [`docs/decisions/README.md`](../../../decisions/README.md), unsafe-log counts from [`docs/audits/unsafe-log.md`](../../../audits/unsafe-log.md). For the carry-forward bullets, read the consolidated seam review and state its source-supported triggers precisely: gate-#3 atomicity before C2/C3 preemption, loader trust before untrusted images, and a distinct SP_EL1 high-water check before C3 richer IRQ execution.

## Definition of done

- [x] Every relative link in each touched file resolves (`grep -o '](\.\./[^)]*' | sort -u`, then `ls` each target).
- [x] `git diff --stat` is limited to `docs/roadmap/current.md`, `docs/roadmap/phases/phase-b.md`, `docs/roadmap/phases/phase-c.md`, `docs/roadmap/current-archive.md` and this task file.
- [x] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) (scope `roadmap`).
- [x] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

**Step-scoped evidence allowance.** In addition to the named content files, the step may update this task, `docs/roadmap/current.md`, the B.2 task/track indexes, governing decision references, source-bound reports/raw evidence, canonical review artifacts and their indexes where necessary. Verify this allowance against the step commit range, not the full stacked branch. Record a demonstrated existing-scope reason for any further file.

## Design notes

- **Resolved 2026-10-12:** archive dated banners/history and delimit the concise live-state section, per the approved plan. Historical source observations below are retained.
- Plan-item line numbers refer to the 2026-10-11 snapshot of `phase-b2.md`; re-verify against the live files with `grep -n` (spec rule: PR #46 and the kickoff changed roadmap line numbers).
- Additional drift found on 2026-10-11 and **not** among the 141 review items: *Next task to open*, *Next review trigger*, *Active decisions*, *Notes* and the "short pointer file" self-description. They are included here because they sit in the same file and mislead in the same way.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-12 | Codex (AI agent), maintainer-approved reconciliation | Old: T-029 as latest completion, stale first-wave triggers, archive undecided and four-file-only scope. Approved replacement: latest T-030–T-037 plus historical T-029, selected B.2-2 live state, linked preserved archive/delimiter and all three source-bound seam triggers. See [approved preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); preparation only, status unchanged. |
| 2026-10-12 | Codex (AI agent), coordinator cross-reference check | ROOT-01: added the T-056 Informs backlink to match its newly explicit prerequisite/surface reference, following start-task step 9; no dependency scope or task state changed. |
| 2026-10-13 | Codex implementation coordinator | Step 10 starts after Step 9 canonical both-round commit 20a0d25. [Preflight](../../reports/2026-10-13-t047-roadmap-state-preflight.md) records actual source/merge/audit/history review, complete archive boundary and distinct stack/IRQ flags. No new ADR or maintainer decision; In Progress, all 11 criteria unchecked until implementation and both fresh paired rounds. |
| 2026-10-13 | Codex implementation author | [Implementation/evidence](../../reports/2026-10-13-t047-roadmap-state-reconciliation.md): 22 original dated groups plus full preamble/live-state/Notes tail preserved; 23 groups including explicit T-029 recovery, reverse chronological with original same-day order. Twelve live task rows/46-task inventory, seven Git integration records, 33 audit entries (32 Active/one Removed), exact three B6 status changes and four distinct C flags verified; errors 0. Original clean archive boundary 20a0d25 is separate from kickoff c989237. In Progress/all 11 criteria unchecked; both fresh paired rounds pending. |
| 2026-10-13 | Codex implementation coordinator | [Both fresh code/security rounds](../../reviews/code-reviews/2026-10-13-t047-roadmap-state-reconciliation.md) Approve cumulative 20a0d25..8a89fd2 after actual peer-initial and R2 prior-final cross-reading; zero confirmed R1/R2 or unresolved source findings, no corrective commit warranted. Full reports/initial prefixes and original captures retained with hashes. All eleven criteria checked; In Review/no date_done, maintainer approval/merge pending. Archive source boundary remains clean 20a0d25; publication only updates live lifecycle/discovery and evidence. T-056 parser starts next under ADR-0043; no runtime/hosted/Done or phase-opening claim. |
