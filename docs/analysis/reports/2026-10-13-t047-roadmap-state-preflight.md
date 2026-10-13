# T-047 — roadmap live-state preflight and execution plan

- **Date:** 2026-10-13.
- **Author:** Codex implementation coordinator.
- **Clean source:** 20a0d25e69a0ce9872ee9dd58e7bd994f22230e1, development; Step 9's actual full both-round canonical boundary.
- **Authority:** [approved 13-step plan](2026-10-12-phase-b2-track2-preflight-and-plan.md), Accepted [ADR-0043](../../decisions/0043-documentation-corpus-consistency.md), [T-047](../tasks/phase-b2/T-047-roadmap-state-and-phase-index-sync.md).
- **State:** pre-content plan/source inventory only. Seven AC/four DoD remain unchecked; no delivery/reviewer/maintainer verdict.

## Reverified sources and decisions

The full approved T-047 contract, current pointer/history, roadmap/phase indexes, relevant B/C phase context, consolidated Phase-B seam security review and actual task/ADR states were reviewed. Earlier read-only preparation at c508fa62/a93926b is not implementation evidence; the [baseline](2026-10-13-t047-verification-evidence/semantic-baseline.json) records the actual clean source above. Current has 141 lines/82594 UTF-8 bytes, with 22 dated groups and an old contradictory live-state tail. The outdated T-028 last-task/PR #48-open/first-wave bullets reproduce. The phases index already has no “it is active” phrase; no unnecessary index rewrite is planned.

Git integration records, including squash integrations, are captured with full IDs, author/committer dates, subjects and parents. T-029 PR #44/#45 both integrated 2026-06-01; Phase-B closure PR #43 is integrated and its b6-closure branch is historical/retired. Latest completed work remains T-030–T-037/PR #48 on 2026-10-12. PR #36's actual Git integration date is 2026-05-30, while an old human narrative says May 31; new B6 status text will name Done/PR #36 without inventing a May 31 merge. Historical dates, measured evidence and original supersession notes remain verbatim in the archive.

The unsafe-log inventory is 33 entries: 32 Active, one Removed (0012), from each entry's first status. This is a metadata recount, not re-audit or soundness proof. The 2026-07-15 review is local-only and absent from the repository; self-contained phase-b2/task records provide provenance without a dead private-file link.

The existing Phase-C carry-forward section contains lifecycle, reserved 0034 and K3-4 only. The approved AC requests gate #3 atomicity, gate #1 loader trust and SP_EL1 high-water distinct from IRQ/TTBR1. No separate IRQ/TTBR1 item currently exists, so four source-backed bullets are needed: the three requested flags plus that distinct IRQ item. Both latter concerns are explicit in the consolidated review's final forward-flag bullet. This is a demonstrated same-section completeness repair under the approved contract, not a new architecture decision or T-074 milestone rewrite.

## Bounded execution plan

1. Preserve all original dated groups byte-for-byte in same-directory current-archive.md, reverse chronological by event date, retaining same-day source order and full multi-paragraph May 8/May 9 groups. Preserve the original preamble and entire old live-state/Notes tail as explicitly historical snapshots. Add a clearly recovered June1 T-029 completion banner, without replacing the latest completed wave. Same-directory placement preserves relative-link path math. A prewrite assertion rejected an initial date-in-link grouping false positive; the baseline records the corrected headline-only segmentation.
2. Replace current.md with a concise dated live section delimited exactly by current-state:start/current-state:end HTML comments. Describe active B.2-2/T-047/development, actual task table/counts, latest wave/historical T-029/retired closure, real decision states, recent reviews, next selected T-056 then HIGH correctness work and eventual T-075 closure. Keep the archive linked. The delimiter is a routine choice within Accepted ADR-0043; no new ADR/maintainer choice is needed.
3. Correct only the B6 sequence's T-022/T-027/T-028 status tags to Done with PR #36/41/42, preserving dependency rationale and implementation narrative. Add separate C flags: atomic context before C2/C3 preemption/SMP, loader trust before first untrusted-image/filesystem exposure (E, or earlier C if it exposes it), SP_EL1 high-water before C3 richer IRQ execution, and IRQ/TTBR1 verification before C3 preemptive IRQ enablement. T-029 performance is not stack-bound evidence.
4. Retain reproducible archive/source/merge/status/audit checks and fresh bounded navigation; commit. Run fresh paired R1 code/security, validate/fix/commit, then different fresh paired R2; fully retain actual reports and cross-read chronology. Stop T-047 In Review/no date_done; automatically continue T-056 after the actual both-round canonical boundary.

Content scope is current.md, linked archive, phase-b.md and phase-c.md; tracking/evidence/review bookkeeping uses the approved allowance. No runtime, unsafe-log, filed ADR, numeric planning identity, C/D gate, T-074 folding or external publication change. Root remains sole writer. Existing PR49 publication barrier remains; this step claims no hosted execution.
