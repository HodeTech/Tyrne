# T-048 — Synchronise the Phase B task corpus and fix task-file links

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** Done
- **Created:** 2026-10-11
- **date_done:** 2026-10-16
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-056](T-056-docs-consistency-automation.md)
- **ADRs required:** [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md) (Accepted 2026-10-12; reviewed execution and corpus policy)

---

> **Approved contract reconciliation (2026-10-12).** The maintainer approved the [preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and ADR package. The criteria below are the executable contract; dated opening observations remain historical. This preparation records no task delivery. Each implementation step includes verification and two fresh independent review rounds under [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); new task states stop at `In Review`.

## User story

As a maintainer or agent looking up Phase B work, I want the phase-b task index and every task file's own status to agree with what actually merged, so that I can trust `Status` fields and relative links in the task corpus instead of cross-checking `git log`.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), covering the task-corpus items of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-2 ("Roadmap & task/review index synchronization" and "Misc doc hygiene").
Phase B closed on 2026-06-01, but the task corpus was never closed out with it.
[`phase-b/README.md`](../phase-b/README.md) indexes 15 of the 23 task files (T-022 through T-029 are missing) and shows T-020 as "In Review" and T-021 as "Ready" (lines 22-23); the frontmatter `Status` of T-020 through T-028 still reads "In Review" although `docs/roadmap/current.md` records all of them as merged; T-029 is shown Draft/In Review although both of its phases merged and its frontmatter has no `Milestone` line; and three relative links in older task files resolve to nothing.
This repeats the T-019 status-drift defect that the [2026-05-22 master review](../../reviews/master-review/2026-05-22-152729/tracks/D4-roadmap-tasks.md) recorded as D4-004, and the `date_done` convention that [T-019](../phase-b/T-019-task-loader.md) introduced (`- **date_done:** 2026-05-16`) exists only in that one file, so this task also writes it into the template.
The `current.md` half of the T-029 finding is [T-047](T-047-roadmap-state-and-phase-index-sync.md).

## Acceptance criteria

- [x] `docs/analysis/tasks/phase-b/README.md`: rows for T-022 through T-029 are added (titles from each file's H1, Milestone as in each file's frontmatter, Status `Done` with the date and PR from the table in Design notes), and the T-020 and T-021 rows read `Done (2026-05-29, PR #34)`. Check: the number of `| [T-` rows equals `ls docs/analysis/tasks/phase-b/T-*.md | wc -l` (23 on 2026-10-11).
- [x] T-020 through T-028: the frontmatter `Status` is `Done` and a `- **date_done:** YYYY-MM-DD` line follows `Created`, exactly as in T-019, with each date taken from the merge table in Design notes; `grep -n "^- \*\*Status:\*\* In Review" docs/analysis/tasks/phase-b/T-02[0-8]-*.md` returns nothing.
- [x] T-020 through T-028: each Review history gains a merge-confirmation entry naming the PR number and merge commit from the Design notes table and stating the `In Review` -> `Done` flip, in the style of that file's history (all nine are bullet lists; T-019 shows the table-row form).
- [x] T-029 (`docs/analysis/tasks/phase-b/T-029-perf-microbench.md`): `Status` is `Done` (Phase 1 merged via PR #44, Phase 2 via PR #45, both 2026-06-01), `date_done` is added, a `Milestone` line is added after `Phase` (suggested wording: "B6 follow-on / Phase B closure tail — not gated on a numbered B-milestone"), and its Review history gains the merge-confirmation entry.
- [x] `docs/analysis/tasks/TEMPLATE.md` formalises the `date_done` field in the frontmatter block (after `Created`), with an instruction that it is a real ISO date set on maintainer-authorized `Done`, omitted while open and not fabricated for historical tasks. The lifecycle in `docs/analysis/tasks/README.md` states the same convention.
- [x] Link fixes, verified with a relative-link check over `docs/analysis/tasks/phase-a` and `docs/analysis/tasks/phase-b` (zero broken targets afterwards; three on 2026-10-11): `phase-a/T-004-cooperative-scheduler.md:25` gets the extra `../` (`../../../../hal/src/context_switch.rs`); `phase-a/T-002-kernel-object-storage.md:55` gets the extra `../` (`../../../../kernel/src/cap/table.rs`); `phase-b/T-011-missing-tests-bundle.md:25` is changed to match the correct link on line 100 (`../../reports/2026-04-23-coverage-baseline.md`).

## Out of scope

- `docs/roadmap/current.md` live-state bullets and the T-029 banner: already refreshed by the ADR-0040 kickoff, remainder is [T-047](T-047-roadmap-state-and-phase-index-sync.md).
- Roadmap-state sync and the ADR-ledger renumbering cascade (including any `phase-b.md` wording): see [T-047](T-047-roadmap-state-and-phase-index-sync.md) and [T-054](T-054-adr-ledger-renumbering-cascade.md).
- Review-family indices: [T-049](T-049-review-indices-sync.md).
- Automating the index-vs-disk and status-vs-`current.md` checks, and the link checker itself: [T-056](T-056-docs-consistency-automation.md).
- Rewriting any task file's content beyond the status, `date_done`, `Milestone`, one history entry, and the three links.

## Approach

Work from the table in Design notes; do not re-derive dates from memory.
For each of T-020..T-028 flip `Status` to plain `Done` (as T-019 does; nuance such as "awaiting security review" belongs in the new history entry, not the field), insert `date_done` after `Created`, and append the merge-confirmation entry.
Add the eight missing index rows in the existing column format and fix the two stale rows.
For T-029, apply the same treatment with both PRs named.
Add the `date_done` line to the template, then fix the three links and run the link check over both phase folders.
The maintainer authorises `Done` per the [tasks README](../README.md); here that authorisation is already on record in `current.md` ("Last completed task", PR list), which the entries cite.

## Definition of done

Doc-only variant:

- [x] Every relative link (`](…)` target) in each touched file resolves to an existing path or heading.
- [x] `git diff --stat` lists only: `docs/analysis/tasks/phase-b/README.md`, `docs/analysis/tasks/phase-b/T-02[0-9]-*.md`, `docs/analysis/tasks/phase-b/T-011-missing-tests-bundle.md`, `docs/analysis/tasks/phase-a/T-002-kernel-object-storage.md`, `docs/analysis/tasks/phase-a/T-004-cooperative-scheduler.md`, `docs/analysis/tasks/TEMPLATE.md`, `docs/analysis/tasks/README.md`, `docs/roadmap/current.md`, and this task file.
- [x] Text is English; no new untagged fences ([`documentation-style.md`](../../../standards/documentation-style.md)).
- [x] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [x] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

**Step-scoped evidence allowance.** In addition to the named content files, the step may update this task, `docs/roadmap/current.md`, the B.2 task/track indexes, governing decision references, source-bound reports/raw evidence, canonical review artifacts and their indexes where necessary. Verify this allowance against the step commit range, not the full stacked branch. Record a demonstrated existing-scope reason for any further file.

## Design notes

**Open decisions.** None.

**Merge facts, verified 2026-10-11 with `git log --date=short --first-parent main` (author and committer dates agree):**

| Task | PR | Merge commit | Date |
|------|----|--------------|------|
| T-020, T-021 | #34 | `f98e1af` | 2026-05-29 |
| T-022 | #36 | `b6549d7` | 2026-05-30 |
| T-023 | #37 | `eb3125f` | 2026-05-31 |
| T-024 | #38 | `5f17a30` | 2026-05-31 |
| T-025 | #39 | `f21eece` | 2026-05-31 |
| T-026 | #40 | `a8ce11e` | 2026-05-31 |
| T-027 | #41 | `9551a33` | 2026-06-01 |
| T-028 | #42 | `0040f23` | 2026-06-01 |
| T-029 Phase 1 / Phase 2 | #44 / #45 | `9c61a8e` / `2ff65cb` | 2026-06-01 / 2026-06-01 |

PR numbers match `docs/roadmap/current.md` ("Last completed task" bullet); the hashes for #38-#41 are not in `current.md` and come from `git log` alone.

**Location re-verification (2026-10-11, against the current tree).**
`phase-b/README.md:22-23` reproduces (15 rows, 23 files).
The plan names `T-004...:25` only, but the second broken link of the "two Phase-A task files" is in `phase-a/T-002-kernel-object-storage.md:55` (found by a relative-link scan of both phase folders; no other broken task-file links exist in phase-a or phase-b).
All ten files T-020..T-029 already have every acceptance checkbox ticked, so no checkbox edits are needed.
The plan counts "nine" frontmatters (T-020..T-028); T-029 is handled separately because its status text is a two-phase sentence rather than `In Review`.

**Required reconciliation (2026-10-12).** Lifecycle step 5 in [`../README.md`](../README.md) records the same `date_done` rule as the template. Existing merged-task dates come from the exact merge table; new B.2 tasks remain In Review.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-12 | Codex (AI agent), maintainer-approved reconciliation | Old: date_done only in the template and lifecycle update optional. Approved replacement: matching template/lifecycle rule with real authorized dates, exact merged ten-task closure and 23-row membership; historical source evidence preserved. See [approved preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); preparation only, status unchanged. |
| 2026-10-13 | Codex (AI agent), Step 4 kickoff | T-046 completed both fresh code/security rounds at `4b33607`, canonically recorded in `a214532`. Reconcile ten already-merged Phase B tasks from exact first-parent `origin/main` facts, add eight index rows, formalize authorized real-date lifecycle and repair the three scoped paths. Preserve historical bodies, review entries and checkboxes. Both fresh review rounds remain pending; no new B.2 Done claim or runtime change. |
| 2026-10-13 | Codex (AI agent), implementation | Reconciled ten historically merged tasks from exact `origin/main` first-parent facts; 23 contiguous index members, eight exact H1/milestone rows, optional authorized real-date template/lifecycle and three path repairs. Whole body/history/checkbox preservation verified; bounded 800 paths, 99 headings and two source-line fragments pass. [Source-bound report](../../reports/2026-10-13-t048-phase-b-task-reconciliation.md). No runtime run or new Done promotion; both fresh review rounds pending, status In Progress. |
| 2026-10-13 | Codex (AI agent), R1 provenance correction | One source-confirmed Low finding: the report's kickoff SHA could be mistaken for the implemented checked tree. Clarified baseline versus working-tree verification and implementation commit `550500f`, preserving every underlying fact/result. No task-body, runtime or evidence change; first-round correction verification and fresh R2 remain pending. |
| 2026-10-13 | Codex (AI agent), both fresh rounds complete | [Canonical five-role review](../../reviews/code-reviews/2026-10-13-t048-phase-b-task-reconciliation.md) records both fresh rounds Approve cumulative `a214532..a50f94a`; one R1 Low provenance finding fixed and independently verified, no unresolved finding. Historical ten-task merge/date/preservation, 23-row rendered index, template/lifecycle and scoped links verified. Status In Review, no date_done; T-049 follows. |
| 2026-10-16 | @cemililik (merge/completion authorization); Codex (verification/scribe) | Maintainer merged PR49 at `52fa323` and explicitly authorized Done. First merged-main CI 38820329507 passes all seven jobs and six required app-15368 contexts; [completion retrospective](../../reviews/business-reviews/2026-10-16-phase-b2-track2-completion.md) records source-bound evidence. date_done is the Istanbul completion/authorization date 2026-10-16; actual merge UTC 2026-10-15T22:55:20Z is preserved. |
