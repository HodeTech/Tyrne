# T-049 — Synchronise the review-family indices

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

As a reader looking for the project's reviews, I want every review artifact to be listed in its family index and every index to describe the review families that exist, so that the Phase B closure reviews are discoverable through the documented entry points.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), covering the review-index items of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-2.
The Phase B closure batch of 2026-05-31 / 2026-06-01 added review files that no index lists: `business-reviews/2026-06-01-phase-b-closure.md`; `security-reviews/2026-05-31-T-022-high-half-migration.md`, `2026-06-01-T-028-el0-userspace-wireup.md`, and `2026-06-01-phase-b-closure.md`; and `performance-optimization-reviews/2026-06-01-B6-closure.md` (an index-versus-`ls` comparison on 2026-10-11 finds exactly these five).
The B6 performance review also deviates from the performance [`master-plan.md`](../../reviews/performance-optimization-reviews/master-plan.md) template and its own acceptance list omits the "Index in README.md updated" item that was in fact not done.
Smaller gaps: [`reviews/README.md`](../../reviews/README.md) never mentions the master-review family, the coverage and Miri reports under `docs/analysis/reports/` are frozen at 2026-04-23/27, and at least ten review-archive files link into the pre-migration `.claude/skills/` path.
To stop the gap recurring, a closure-batch index sweep item is added to the business master-plan; mechanical enforcement is [T-056](T-056-docs-consistency-automation.md).

## Acceptance criteria

- [x] `business-reviews/README.md`: a row for `2026-06-01-phase-b-closure.md` is appended after the current last row (line 38) in the table's `Date | Scope | File` format.
- [x] `security-reviews/README.md`: rows for the three missing files are appended after line 41 in the table's `Date | Scope | Verdict | File` format, each verdict copied from that file's own Verdict section rather than re-judged.
- [x] `performance-optimization-reviews/README.md`: a row for `2026-06-01-B6-closure.md` is appended after line 31 in the `Date | Scope | File` format. Together with the three criteria above, `for f in <dir>/20*; do grep -q "$(basename "$f")" <dir>/README.md || echo "$f"; done` prints nothing for the business, security, and performance directories.
- [x] `2026-06-01-B6-closure.md` is brought to the master-plan shape (the file has Baseline, Micro-measurements, Verdict only): the missing Hotspot, Proposal, Measurement, and Regression check sections are added, restating evidence the cycle already recorded (host-test pass, smoke pass, unsafe diff), and its acceptance list (lines 88-93) gains the "Index in README.md updated" item as a dated 2026-10-13 structural reconciliation using only the evidence originally recorded, with explicit measurement limitations. Do not invent a retrospective run or change the original verdict, provenance or measurements.
- [x] `reviews/README.md` (table at lines 7-14): the master-review family is added as a fifth row or a short "Master reviews" subsection linking [`master-review/README.md`](../../reviews/master-review/README.md) and stating its trigger (on-demand, whole-tree sweep); any "four types" wording made inaccurate by the choice is reconciled (`reviews/README.md:3,7`, `docs/analysis/README.md:24`).
- [x] Retired `.claude/skills/` Markdown navigation targets resolve to verified immutable historical commit permalinks containing each cited file. Preserve old paths quoted as defect evidence and all historical verdicts/measurements; do not substitute current skill content where it changes the evidence. A migration note cannot satisfy link validity. Record exact document/destination/reason/review/fixture for any unavoidable exception under ADR-0043; no archive-wide exclusion or unreviewed broken-link exception is permitted.
- [x] Add fresh source-bound coverage and Miri reports now under `docs/analysis/reports/`, executing the pinned-toolchain workspace Miri command excluding only the BSP and the repository coverage command. Record actual counts, percentages, tools and limitations; opening expectations and old reports are historical, not new results.
- [x] Repair additional broken review-archive/master-plan navigation found by the full-corpus baseline scan within this bounded scope, preserving quoted defect data and evidence. Verify current destinations or immutable historical targets as appropriate. Explicitly link canonical reviews, companion plans, nested tracks and master-review runs from their proper discovery surfaces without misclassifying companion plans as verdict-bearing reports.
- [x] The business master-plan acceptance criteria (`docs/analysis/reviews/business-reviews/master-plan.md:80-88`) gain a "closure-batch index sweep" item for milestone-completion and phase-closure reviews: every review artifact of the closure batch is listed in its family README and the family table in `reviews/README.md` is current, mirroring the existing smoke-trace item.

## Out of scope

- Re-judging or rewriting any review verdict.
- Re-judging code reviews; discovery fixes for their companion plans/indexes are in scope.
- Implementing the checker itself: [T-056](T-056-docs-consistency-automation.md). This task owns bounded baseline repair of review navigation before that gate is enabled.
- The architecture-docs closure item in the same master-plan list: [T-045](T-045-docs-overview-taskloader-arch-index.md).

## Approach

Read each canonical report's own scope/verdict and preserve its family's table format.
Reconcile B6's missing template sections with a dated structural note citing existing evidence and limitations; do not perform or imply a new historical measurement.
Repair retired skill navigation with immutable commit permalinks after verifying the historical commit contains the destination, preserving quoted paths as data.
Scan and repair other broken archive/master-plan navigation within the approved corpus scope; record each disposition without rewriting historical findings.
Link companion plans, nested tracks and master-review runs explicitly through their proper discovery surfaces.
Run fresh coverage and workspace Miri now, recording exact source/tools/results in new reports, then add the closure-batch index-sweep hook.

## Definition of done

Doc-only variant:

- [x] Every relative link (`](…)` target) in each touched file resolves to an existing path or heading.
- [x] `git diff --stat` lists only the three family READMEs, `reviews/README.md` (and `docs/analysis/README.md` if its wording changed), `performance-optimization-reviews/2026-06-01-B6-closure.md`, the business `master-plan.md`, repaired review-archive/master-plan files, affected discovery indexes and companion plans, fresh reports/raw evidence, `docs/roadmap/current.md`, and this task file.
- [x] Text is English; new tables stay within a readable width ([`documentation-style.md`](../../../standards/documentation-style.md)).
- [x] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [x] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

**Step-scoped evidence allowance.** In addition to the named content files, the step may update this task, `docs/roadmap/current.md`, the B.2 task/track indexes, governing decision references, source-bound reports/raw evidence, canonical review artifacts and their indexes where necessary. Verify this allowance against the step commit range, not the full stacked branch. Record a demonstrated existing-scope reason for any further file.

## Design notes

**Resolved by approval on 2026-10-12.** Add dated B6 structural sections, use verified immutable historical skill permalinks, repair bounded baseline navigation and run fresh coverage/Miri now. The old note-only, current-skill-substitution and defer alternatives are not executable under ADR-0043.

**Location re-verification (2026-10-11, against the current tree).**
`business-reviews/README.md:38`, `security-reviews/README.md:41`, `performance-optimization-reviews/README.md:31` reproduce as the last table rows; `reviews/README.md:7-14` reproduces.
The plan item describes all three tables as `Date | Scope | Verdict | File`; in the tree only the security table has a Verdict column (business and performance are `Date | Scope | File`), so each table's own format governs.
The plan item says the B6 omission can be handled "mirroring how B2-B5 handled baseline-only cycles"; the B2, B3, B4, and B5 performance reviews in fact all carry the full six master-plan sections (Baseline, Hotspot, Proposal, Measurement, Regression check, Verdict), so no exemption precedent exists.
A scratch relative-link scan of `docs/analysis/reviews` (fenced blocks skipped) finds 17 dead `.claude/skills/` link targets in 10 files (three of them master-review track files quoting the stale links); line numbers vary, so rerun the scan rather than trusting this count.
`code-reviews/README.md` omits only `2026-05-06-full-tree-comprehensive-review-plan.md`, which looks like a companion plan to an indexed review; confirm its companion role and add an explicit discovery link without inventing a review verdict.

**Sequencing.** The master-plan list is also edited by [T-045](T-045-docs-overview-taskloader-arch-index.md) (a different item); expect a trivial merge.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-12 | Codex (AI agent), maintainer-approved reconciliation | Old: note-only or current-path retired-link alternatives, other archive repairs excluded, B6 exemption/fresh reports deferred, companion left undiscovered. Approved replacement: verified immutable historical permalinks, bounded full baseline navigation repair, dated B6 structural sections, fresh coverage/Miri now and explicit companion/master-review discovery; expanded DoD evidence scope. See [approved preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); preparation only, status unchanged. |
| 2026-10-13 | Codex (AI agent), Step 5 kickoff | Starts after T-048 both fresh complementary/code rounds at `468812b8e765f655edcfcfca161586e609d2478f`. Complete related-document navigation preflight covered 35 existing files / 6,137 lines in 76 untruncated chunks; preparation is not either implementation review. Corrected the B6 criterion’s planned 2026-10-12 reconciliation date to actual 2026-10-13; original opening history and verdicts remain preserved. Scope: canonical/companion/master-run discovery, verified historical navigation, B6 structure and fresh source-bound Miri/coverage. No delivery or new runtime result claimed at kickoff. |
| 2026-10-13 | Codex (AI agent), Step 5 implementation | Added five canonical rows, companion/master-run discovery, closure sweep and dated B6 template reconciliation; preserved original verdicts/measurements/quoted defects. Repaired all 48 baseline navigation occurrences and bound 419 existing line citations to verified review-era source, with explicit range/label caveats. Fresh clean `0ab0ba4` Miri: 366 pass / two ignored / seven provenance warnings; coverage: 363 pass, 95.87% lines, unmeasured branches and local/CI tool difference explicit. [Implementation/evidence report](../../reports/2026-10-13-t049-review-corpus-reconciliation.md) records checks and boundaries. Two fresh complementary review rounds pending; status remains In Progress and acceptance boxes unchecked. |
| 2026-10-13 | Codex (AI agent), verified Round-1 disposition | Primary five-role review: Request changes for Low C01 (quoted infrastructure proposal destination); complementary evidence review: scoped Approve, zero findings. Preserved exact original proposed Markdown with adjacent archive navigation and dated explanation; updated final navigation hashes/disposition. Documented captured Miri blank-EOF warning without normalizing raw output. Both raw hashes remain unchanged; status In Progress, new fresh complementary Round 2 pending. |
| 2026-10-13 | Codex (AI agent), both fresh rounds complete | [Canonical four-context review](../../reviews/code-reviews/2026-10-13-t049-review-corpus-reconciliation.md) retains both primary and complementary rounds, original Request changes and verified Low C01 correction at `aa37e2c`; no unresolved finding. All nine AC and five DoD verified; fresh runtime provenance/limitations retained. Status In Review, no date_done or maintainer merge claim. T-045 deferred master-plan navigation DoD now closes against the repaired targets. |
