# T-047 — Synchronise roadmap live state and phase index

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none (phase-level precondition: [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) `Accepted`, see the [task index](README.md))
- **Informs:** [T-074](T-074-phase-c-readiness-sweep.md)
- **ADRs required:** none

---

## User story

As a maintainer (or agent) returning to the project after a pause, I want `docs/roadmap/current.md`, the phase index and the Phase B/C phase files to state the true current position and no stale "next step", so that the first file I open orients me correctly.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). `docs/roadmap/current.md` is documented as "a short pointer file" but has grown to ~18 dated banners, and its lower half still describes April–May 2026: the *Last completed task* bullet stops at T-028 although T-029 (Phase 1 and Phase 2) merged on 2026-06-01, *Next task to open* still names the already-finished `task_create_from_image`, *Next review trigger* still waits for the B6 closure trio, and *Active decisions* stops at ADR-0027. Several of these are recurrences of Blocker D4-003 from the 2026-05-22 master review. The relevant plan items are in [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) (Track B.2-2, "Roadmap & task/review index synchronization" and "ADR corrections & cross-links").

The ADR-0040 kickoff (2026-10-11) already did the following, so this task must **not** redo it: the new 2026-10-11 decision banner and the *Active phase / Active milestone / Active task / Working branch* bullets of `current.md`; the B.2 gating wording, the "Phase A … it is active" fix and the phase-count wording in `phases/README.md`; the dotted-ID/Track convention in `roadmap/README.md`; the status banners in `phase-b2.md` and `phase-c.md`; the supersession note in `phase-b.md`; the ADR-0040 index row; and the status sentences of `README.md` and `CLAUDE.md`.

## Acceptance criteria

- [ ] `current.md` *Last completed task* names **T-029** (Phase 1 PR #44, Phase 2 PR #45, both merged 2026-06-01 — confirm with `git log --date=short`), and a dated banner records T-029's completion; the PR #43 / `b6-closure` branch is marked merged and retired, and the *In review* bullet no longer contradicts it (plan items at snapshot lines 120, 165, 171).
- [ ] The stale bullets are corrected: *Next task to open* and *Next review trigger* describe the Phase B.2 position (first wave from the [task index](README.md); triggers: ADR-0040 Accept, the closure security review and business review of [T-075](T-075-phase-b2-closure.md)); *Active decisions* lists ADR-0030, 0031, 0033, 0037, 0038, 0039 and 0040 with their real statuses and no longer calls T-016 a draft; the *Notes* section is refreshed or explicitly marked historical, and its unsafe-log counts match the log (33 entries: 32 Active, 1 Removed — re-count before writing).
- [ ] *Last reviews* includes the 2026-07-15 full-repository review with an explicit provenance sentence (the review is a local-only document and is not in the repository; `phase-b2.md` and the task files are self-contained), and any 2026-05-31 / 2026-06-01 reviews that are missing from the list.
- [ ] The dated banners are in reverse-chronological order again (the 2026-05-08 / 2026-05-09 / 2026-05-08 sequence is out of order), and the file's opening sentence describes what the file now is. **Open decision** (record it in the review history): keep banners inline vs move banners older than a chosen cut-off to an archive file such as `docs/roadmap/current-archive.md`.
- [ ] `phase-c.md` §"Carry-forwards from Phase B" gains the three missing seam-review forward-flags — gate-#3 context-resolution atomicity (relevant to C2/C3), gate-#1 loader trust, and an `SP_EL1` high-water-mark bullet distinct from the IRQ/`TTBR1` item — each cross-referenced to [the consolidated Phase-B security review](../../reviews/security-reviews/2026-06-01-phase-b-closure.md) and the milestone that makes it live (plan item at snapshot line 132).
- [ ] `phase-b.md` B6 dependency-ordered task sequence: the status tags of steps 1, 5 and 6 read **Done** with their merge PRs (T-022 → #36, T-027 → #41, T-028 → #42), or the pre-closure narrative is wrapped in a "preserved as historical record" framing as the B5 section above it is (plan item at snapshot line 229).
- [ ] Verification: every relative link in `current.md`, `phase-b.md` and `phase-c.md` resolves; `grep -n "it is active" docs/roadmap/phases/README.md` returns nothing; `git diff --stat` touches only these three files and this task file.

## Out of scope

- The Phase B task-file frontmatter and the `phase-b/README.md` index — [T-048](T-048-phase-b-task-corpus-sync.md).
- The review-family README indices — [T-049](T-049-review-indices-sync.md).
- Re-sequencing the ADR ledgers — [T-054](T-054-adr-ledger-renumbering-cascade.md).
- Folding Phase C's review-derived items into C1–C5 — [T-074](T-074-phase-c-readiness-sweep.md).

## Approach

Edit `current.md` from the bottom up (the stale tail first) so that the kickoff's new banner and live-state bullets stay untouched. Take every fact from the repository, not from the old text: PR numbers and merge dates from `git log --date=short`, ADR statuses from [`docs/decisions/README.md`](../../../decisions/README.md), unsafe-log counts from [`docs/audits/unsafe-log.md`](../../../audits/unsafe-log.md). For the carry-forward bullets, read the consolidated seam review and quote its wording rather than paraphrasing the plan item.

## Definition of done

- [ ] Every relative link in each touched file resolves (`grep -o '](\.\./[^)]*' | sort -u`, then `ls` each target).
- [ ] `git diff --stat` is limited to `docs/roadmap/current.md`, `docs/roadmap/phases/phase-b.md`, `docs/roadmap/phases/phase-c.md` and this task file.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) (scope `roadmap`).
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions:** banner archive vs inline (criterion 4).
- Plan-item line numbers refer to the 2026-10-11 snapshot of `phase-b2.md`; re-verify against the live files with `grep -n` (spec rule: PR #46 and the kickoff changed roadmap line numbers).
- Additional drift found on 2026-10-11 and **not** among the 141 review items: *Next task to open*, *Next review trigger*, *Active decisions*, *Notes* and the "short pointer file" self-description. They are included here because they sit in the same file and mislead in the same way.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
