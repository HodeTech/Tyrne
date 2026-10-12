# T-045 — Refresh the entry-point architecture docs (overview, task-loader, architecture index)

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** In Progress
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-056](T-056-docs-consistency-automation.md)
- **ADRs required:** [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md) (Accepted 2026-10-12; reviewed execution and corpus policy)

---

> **Approved contract reconciliation (2026-10-12).** The maintainer approved the [preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and ADR package. The criteria below are the executable contract; dated opening observations remain historical. This preparation records no task delivery. Each implementation step includes verification and two fresh independent review rounds under [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); new task states stop at `In Review`.

## User story

As a new reader of the repository, I want the architecture entry points (`overview.md`, `task-loader.md`, and the architecture index) to describe the system as it is after Phase B closed, so that the first document I open does not tell me userspace, syscalls, and address spaces are future work.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), covering the "Entry-point & core architecture docs" items of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-2.
Phase B closed on 2026-06-01 and the kernel now runs a real EL0 task through the capability-gated syscall boundary, but `docs/architecture/overview.md:5` still carries a `Status (2026-04-27)` banner that says the userspace, syscall, and address-space layers "remain Phase B / Phase C work".
`docs/architecture/task-loader.md` is wrong in the same direction: its "Scope boundary" (lines 13-21) says the loader produces a non-runnable descriptor and that `task_create_from_image` "lands with B6", and its "Embedded image content" (lines 92-103) says the 8-byte placeholder blob "is not executed in B4", while the live path is `load_image` -> `task_create_from_image` -> `add_user_task` -> EL0 execution.
`docs/architecture/README.md` has a Status column (lines 13-23) that does not track the linked documents and a Status paragraph (line 7) that says "many documents listed below are planned" although only two of the eleven listed documents (`drivers.md`, `userspace.md`) are still planned.

This task owns the three documents above, the "last verified against" convention, and the phase-closure checklist hook that stops the architecture docs from being left behind again.
The seven subsystem chapters (`hal`, `scheduler`, `exceptions`, `security-model`, `memory-management`, `boot`, `ipc`) are [T-046](T-046-docs-subsystem-chapters-refresh.md).
The kickoff already refreshed `docs/roadmap/current.md`, the phase index, and the top-level README status sentences; this task does not touch them.

## Acceptance criteria

- [ ] `overview.md` status banner (line 5) is rewritten to the post-Phase-B state (Phase B closed 2026-06-01, first EL0 userspace task running through the syscall boundary, Phase B.2 active, Phase C next), verified against `docs/roadmap/current.md`; `grep -n "Phase A is complete\|remain Phase B / Phase C work" docs/architecture/overview.md` returns nothing.
- [ ] `overview.md` "Syscall surface" (lines 194-206) matches the implemented v1 ABI and cites ADR-0030 and ADR-0031: the five syscalls (`ipc_send`, `ipc_recv`, `task_yield`, `task_exit`, `console_write` with its debug-build gate), verified against `kernel/src/syscall/abi.rs:50-62`; the speculative names (`task_create`, `as_create`, `debug_put`, …) are either removed or moved under an explicit "planned, not implemented" label. The choice is recorded in the review history.
- [ ] `overview.md` "Address spaces" (line 169) and "Boot flow" (line 105) thread in the relevant ADR-0027..0039 links (at least 0027, 0028, 0033, 0035, 0037, 0038, 0039 where each applies), and the Boot-flow Mermaid sequence is resynced with the sequence in `boot.md` (lines 36-83) so no step in the overview diagram contradicts it.
- [ ] `task-loader.md` introduction (line 3) and "Scope boundary" (lines 13-21, heading included) describe the landed state: `load_image` (`kernel/src/obj/task_loader.rs:507`) -> `task_create_from_image` (`:917`, T-024) -> `add_user_task` (`kernel/src/sched/mod.rs:444`, T-023) -> scheduled EL0 execution (T-028); verified against those locations and the EL0 setup in `bsp-qemu-virt/src/main.rs`.
- [ ] `task-loader.md` "Embedded image content" (lines 92-103) describes the real `hello` image and ADR-0039's build pipeline, the 8-byte `mov w0, #42; ret` sample is kept only under an explicit historical marking, and the stale `tyrne: image loaded (entry = 0x800000; ... image bytes 8 ...)` sentence at line 130 is corrected against a fresh `tools/smoke.sh --int` trace (eliding fragile values with `...` is acceptable).
- [ ] `docs/architecture/README.md`: the Status paragraph (line 7) matches its own table, and every Status cell distinguishes the latest documented implementation coverage from the task/commit that last edited the chapter. Verify edit provenance with `git log --oneline -- <file>` and verify coverage against implementation source; do not imply T-024/T-028 edited `task-loader.md` merely because its refreshed content covers them.
- [ ] The "last verified against" freshness marker is defined once (one line containing verification date, exact source baseline and owning task; form recorded in the review history) in the Conventions section of `docs/architecture/README.md` and applied to `overview.md` and `task-loader.md`; the other seven chapters receive it from T-046.
- [ ] Phase closure hook: an item is added to the business master-plan acceptance criteria (`docs/analysis/reviews/business-reviews/master-plan.md:80-88`, the list that applies to phase-closure reviews) requiring that the `docs/architecture/` chapters, their freshness markers, and the README Status column are re-verified in the closure batch.

- [ ] Review the whole overview and loader chapters against source, including current/planned HAL ownership, cooperative scheduling, IPC bridge versus syscall behavior, high-half translation, loader overlap/range/frame arithmetic and exit/fault limits. Recheck the overview boot flow and all architecture-index cells after T-046; cite retained fresh debug/release traces and distinguish manual exception counts from script assertions.

## Out of scope

- The seven subsystem chapters (`hal`, `scheduler`, `exceptions`, `security-model`, `memory-management`, `boot`, `ipc`): [T-046](T-046-docs-subsystem-chapters-refresh.md).
- The README Quick-Start trace and other top-level entry docs: [T-050](T-050-entry-docs-and-glossary-sync.md).
- `docs/roadmap/current.md` and the phase index: already refreshed by the kickoff, and [T-047](T-047-roadmap-state-and-phase-index-sync.md) for the remainder.
- The review-index sweep item in the same master-plan list: [T-049](T-049-review-indices-sync.md).
- A new dedicated architecture chapter for the syscall ABI / EL0 execution model (a Polish item in `phase-b2.md`); it may be picked up opportunistically but is not part of this task.

## Approach

Rewrite rather than patch the stale passages.
For `overview.md`, keep the existing structure (layers, boot flow, IPC, address spaces, interrupts, syscall surface) and bring each section to the post-Phase-B state, citing ADR-0027..0039 where the section's claim rests on them; the plan item offers either updating the syscall list to the real ABI or relabelling it as design-time speculation, and updating it is preferred because the ABI is Accepted and implemented.
For `task-loader.md`, rewrite "Scope boundary" and "Embedded image content" as described in the plan item, and fix the other places in the file that repeat the same premise (line 3 and line 130).
Read every claim against the code before writing it; fresh debug and release `tools/smoke.sh --int` / `--release --int` runs are the reference traces, with raw output, exact source revision, pinned toolchain and QEMU version retained. Inspect the expected two SVCs and absence of other fault classes separately from the script's marker/fault gates.
Finally add the freshness-marker convention and the master-plan closure item so the staleness root cause (five architecture docs describing B6 as future after B6 closed) has a named owner at the next closure.

## Definition of done

Doc-only variant:

- [ ] Every relative link (`](…)` target) in each touched file resolves to an existing path or heading.
- [ ] `git diff --stat` lists only: `docs/architecture/overview.md`, `docs/architecture/task-loader.md`, `docs/architecture/README.md`, `docs/analysis/reviews/business-reviews/master-plan.md`, `docs/roadmap/current.md`, and this task file.
- [ ] New or changed diagrams are Mermaid, preceded by a short prose description; all fences are tagged; text is English ([`documentation-style.md`](../../../standards/documentation-style.md)).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

**Step-scoped evidence allowance.** In addition to the named content files, the step may update this task, `docs/roadmap/current.md`, the B.2 task/track indexes, governing decision references, source-bound reports/raw evidence, canonical review artifacts and their indexes where necessary. Verify this allowance against the step commit range, not the full stacked branch. Record a demonstrated existing-scope reason for any further file.

## Design notes

**Open decisions.** None blocking.
The exact wording of the freshness marker (date, task ID, or commit) is a small implementer choice and is recorded in the review history.

**Location re-verification (2026-10-11, against the current tree).**
All cited locations reproduce: `overview.md:5`, `:194-206`; `task-loader.md:13-21`, `:92-103`; `architecture/README.md:7`, `:11-23`.
Two further occurrences of the same stale premise were found in `task-loader.md` (line 3, "documented separately when B5/B6 land", and line 130, the `image loaded ... image bytes 8` trace) and are included above.
`memory-management.md:194` and `boot.md:77` also mention the removed `tyrne: image loaded` banner; they belong to [T-046](T-046-docs-subsystem-chapters-refresh.md).

**Sequencing.**
The README Status cells and the overview Boot-flow resync both depend on content that [T-046](T-046-docs-subsystem-chapters-refresh.md) changes (`boot.md` diagram, seven chapters).
There is no hard dependency, but whichever of the two lands second re-checks those cells and that diagram.
The master-plan list is also edited by [T-049](T-049-review-indices-sync.md) (different item); expect a trivial merge.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-12 | Codex (AI agent), maintainer-approved reconciliation | Old: named stale sentences, a marker of unspecified form and edit history treated as coverage. Approved replacement: whole-chapter sweep, date/source/task freshness, separate edit/coverage provenance and fresh debug/release raw traces with manual SVC inspection; T-046 coherence recheck. See [approved preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); preparation only, status unchanged. |
| 2026-10-13 | Codex (AI agent) | Step 2 started after T-051 completed both fresh code/security rounds (`d6cb853`). Apply the architecture-writing procedure, source/date/task freshness convention, whole overview/loader sweep and closure hook; fresh matching-profile debug/release traces are captured before prose edits. T-046 must subsequently recheck overview/boot/index coherence. |
| 2026-10-13 | Codex (AI agent) | Implementation: whole overview/loader refresh, ABI enumeration replaced speculative names, date/full-source/task marker defined in architecture index, edit provenance separated from coverage, closure hook added. Fresh debug/release commands both exit 0 at `4ad0b3d`; retained raw evidence and manual two-SVC inspection are in the [verification report](../../reports/2026-10-13-t045-architecture-verification.md). No executable change or new ADR; task remains In Progress pending both fresh code/security rounds. T-046 owns the immediate detailed boot/index coherence recheck. |
| 2026-10-13 | Codex (AI agent), Round 1 corrections | Fresh code review and subsequent distinct security review found one shared Medium Task-generation overclaim and two Low ambiguities (transfer preflight stages; idle/timer runtime interpretation, the latter coordinator-origin and independently verified). Corrected overview/report against scheduler accessors, BSP binding, IPC send/receive and Task A's completion spin. No executable or raw-evidence bytes changed; second fresh round remains pending. |
