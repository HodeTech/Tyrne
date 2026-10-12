# T-049 — Synchronise the review-family indices

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-056](T-056-docs-consistency-automation.md)
- **ADRs required:** none

---

## User story

As a reader looking for the project's reviews, I want every review artifact to be listed in its family index and every index to describe the review families that exist, so that the Phase B closure reviews are discoverable through the documented entry points.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), covering the review-index items of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-2.
The Phase B closure batch of 2026-05-31 / 2026-06-01 added review files that no index lists: `business-reviews/2026-06-01-phase-b-closure.md`; `security-reviews/2026-05-31-T-022-high-half-migration.md`, `2026-06-01-T-028-el0-userspace-wireup.md`, and `2026-06-01-phase-b-closure.md`; and `performance-optimization-reviews/2026-06-01-B6-closure.md` (an index-versus-`ls` comparison on 2026-10-11 finds exactly these five).
The B6 performance review also deviates from the performance [`master-plan.md`](../../reviews/performance-optimization-reviews/master-plan.md) template and its own acceptance list omits the "Index in README.md updated" item that was in fact not done.
Smaller gaps: [`reviews/README.md`](../../reviews/README.md) never mentions the master-review family, the coverage and Miri reports under `docs/analysis/reports/` are frozen at 2026-04-23/27, and at least ten review-archive files link into the pre-migration `.claude/skills/` path.
To stop the gap recurring, a closure-batch index sweep item is added to the business master-plan; mechanical enforcement is [T-056](T-056-docs-consistency-automation.md).

## Acceptance criteria

- [ ] `business-reviews/README.md`: a row for `2026-06-01-phase-b-closure.md` is appended after the current last row (line 38) in the table's `Date | Scope | File` format.
- [ ] `security-reviews/README.md`: rows for the three missing files are appended after line 41 in the table's `Date | Scope | Verdict | File` format, each verdict copied from that file's own Verdict section rather than re-judged.
- [ ] `performance-optimization-reviews/README.md`: a row for `2026-06-01-B6-closure.md` is appended after line 31 in the `Date | Scope | File` format. Together with the three criteria above, `for f in <dir>/20*; do grep -q "$(basename "$f")" <dir>/README.md || echo "$f"; done` prints nothing for the business, security, and performance directories.
- [ ] `2026-06-01-B6-closure.md` is brought to the master-plan shape (the file has Baseline, Micro-measurements, Verdict only): the missing Hotspot, Proposal, Measurement, and Regression check sections are added, restating evidence the cycle already recorded (host-test pass, smoke pass, unsafe diff), and its acceptance list (lines 88-93) gains the "Index in README.md updated" item; or, if the maintainer prefers an exemption, a one-line note states the abbreviated shape is intentional. The choice is recorded in the review history; the review's verdict is not changed.
- [ ] `reviews/README.md` (table at lines 7-14): the master-review family is added as a fifth row or a short "Master reviews" subsection linking [`master-review/README.md`](../../reviews/master-review/README.md) and stating its trigger (on-demand, whole-tree sweep); any "four types" wording made inaccurate by the choice is reconciled (`reviews/README.md:3,7`, `docs/analysis/README.md:24`).
- [ ] `.claude/skills/` references: either (a) a one-line note in `reviews/README.md` states that review artifacts dated before the 2026-05-14 skills migration (commit `77d3e7e`) link into the retired `.claude/skills/` path and are left as historical snapshots, or (b) the dead markdown link targets are rewritten to `.agents/skills/`. The choice is recorded in the review history; under (b) only link targets change and a relative-link check over `docs/analysis/reviews` reports no remaining `.claude/skills/` target.
- [ ] Coverage and Miri reports: a decision is recorded in the review history, either to add a fresh coverage re-run and Miri validation report under `docs/analysis/reports/` now (same commands as the 2026-04-23 / 2026-04-27 reports; the 2026-10-11 results of 96.31 % regions / 95.87 % lines and Miri with 0 UB on kernel, hal, and test-hal are the expected data) or to defer to the first natural checkpoint named in the plan item (Phase C open or first Phase C milestone close).
- [ ] The business master-plan acceptance criteria (`docs/analysis/reviews/business-reviews/master-plan.md:80-88`) gain a "closure-batch index sweep" item for milestone-completion and phase-closure reviews: every review artifact of the closure batch is listed in its family README and the family table in `reviews/README.md` is current, mirroring the existing smoke-trace item.

## Out of scope

- Re-judging or rewriting any review verdict.
- The code-reviews index, which is already complete apart from the companion plan file noted in Design notes.
- Repairing the other broken relative links in the review archive that do not point at `.claude/skills/`; the link checker is [T-056](T-056-docs-consistency-automation.md).
- The architecture-docs closure item in the same master-plan list: [T-045](T-045-docs-overview-taskloader-arch-index.md).

## Approach

Add the five index rows by reading each file's own scope and verdict lines, and follow each table's existing column format.
For the B6 performance review, the plan item offers adding the "Regression check" evidence plus the index row, or an explicit exemption note; adding the sections is preferred because every other closure review in that folder carries the full six sections.
For `.claude/skills/`, the plan item offers a historical-snapshot note or a mechanical path rename; whichever is chosen, review verdicts stay untouched.
Then add the closure-batch index-sweep criterion to the business master-plan, using the same wording style as the smoke-trace item, so the index update is checked at closure rather than rediscovered by the next master review.

## Definition of done

Doc-only variant:

- [ ] Every relative link (`](…)` target) in each touched file resolves to an existing path or heading.
- [ ] `git diff --stat` lists only the three family READMEs, `reviews/README.md` (and `docs/analysis/README.md` if its wording changed), `performance-optimization-reviews/2026-06-01-B6-closure.md`, the business `master-plan.md`, the files that carry rewritten `.claude/skills/` links under option (b), any new report, `docs/roadmap/current.md`, and this task file.
- [ ] Text is English; new tables stay within a readable width ([`documentation-style.md`](../../../standards/documentation-style.md)).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

**Open decisions (implementer or maintainer, each recorded in the review history).**
(1) B6 performance review: add the missing sections vs write an exemption note.
(2) `.claude/skills/`: historical note vs path rewrite. Caveat for the rewrite option: prose in `business-reviews/2026-05-14-B3-closure.md` (lines 121, 147) and in the master-review track files discusses the migration or quotes the stale paths as findings, so a blind string replace would falsify history; limit it to markdown link targets, or prefer the note.
(3) Coverage and Miri reports: fresh now vs deferred.

**Location re-verification (2026-10-11, against the current tree).**
`business-reviews/README.md:38`, `security-reviews/README.md:41`, `performance-optimization-reviews/README.md:31` reproduce as the last table rows; `reviews/README.md:7-14` reproduces.
The plan item describes all three tables as `Date | Scope | Verdict | File`; in the tree only the security table has a Verdict column (business and performance are `Date | Scope | File`), so each table's own format governs.
The plan item says the B6 omission can be handled "mirroring how B2-B5 handled baseline-only cycles"; the B2, B3, B4, and B5 performance reviews in fact all carry the full six master-plan sections (Baseline, Hotspot, Proposal, Measurement, Regression check, Verdict), so no exemption precedent exists.
A scratch relative-link scan of `docs/analysis/reviews` (fenced blocks skipped) finds 17 dead `.claude/skills/` link targets in 10 files (three of them master-review track files quoting the stale links); line numbers vary, so rerun the scan rather than trusting this count.
`code-reviews/README.md` omits only `2026-05-06-full-tree-comprehensive-review-plan.md`, which looks like a companion plan to an indexed review; confirm and leave as is.

**Sequencing.** The master-plan list is also edited by [T-045](T-045-docs-overview-taskloader-arch-index.md) (a different item); expect a trivial merge.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
