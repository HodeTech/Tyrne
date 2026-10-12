# T-046 — Refresh the subsystem architecture chapters (hal, scheduler, exceptions, security-model, memory-management, boot, ipc)

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

As a contributor reading a subsystem chapter, I want each chapter to describe the EL0 entry path, the syscall boundary, and the high-half kernel as the live, tested mechanisms they are, so that I do not mistake shipped behaviour for dormant or future work.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), covering the subsystem-chapter items of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-2.
Seven chapters under `docs/architecture/` were written while Phase B was in progress and still describe milestone B6 as upcoming: `hal.md:94` and `scheduler.md:73` call the EL0 entry mechanism "dormant", `exceptions.md:58,105` say the `+0x400` syscall path is "runtime-verified in B6", and `boot.md:19,76-77` still shows a `tyrne: image loaded` banner and says the loaded image "does NOT execute", although `bsp-qemu-virt/src/main.rs:1438-1627` now brings up the first EL0 task (T-028).
`security-model.md:128-143` lists capability kinds that do not exist and omits `DebugConsole`, the kind that gates the one live privileged operation.
The remaining items are small: a stale high-half "future" paragraph in `memory-management.md`, an untagged ASCII-art memory map in `boot.md`, an absolute GitHub URL and a drifted line-count claim in `ipc.md`, and a missing ADR-0023 pointer in `security-model.md`.

The entry-point documents (`overview.md`, `task-loader.md`, the architecture index) and the freshness-marker convention are [T-045](T-045-docs-overview-taskloader-arch-index.md).
Because the live path was delivered by [T-024](../phase-b/T-024-task-create-from-image.md), [T-025](../phase-b/T-025-user-access-translation.md), [T-026](../phase-b/T-026-current-task-cap-table.md), and [T-028](../phase-b/T-028-el0-userspace-wireup.md) under [ADR-0039](../../../decisions/0039-userland-build-pipeline.md), those are the citations the rewritten passages use.

## Acceptance criteria

Each criterion is one document. Review every current-state claim in all seven chapters against code and retained fresh debug/release traces, including claims outside the originally named stale sentences. Clearly label future mechanisms with their decision/roadmap authority.

- [x] `hal.md`: line 94 no longer calls the `init_user_context` mechanism "dormant" or defers the first EL0 task to "the B6 wire-up"; it says the mechanism is live and cites T-023/T-024/T-028 and ADR-0039 (verified against `kernel/src/sched/mod.rs:444` and `bsp-qemu-virt/src/main.rs:1438-1627`); `grep -n "dormant" docs/architecture/hal.md` returns nothing.
- [x] `scheduler.md`: lines 73 and 90 are updated the same way (the "Shipped dormant ... arrives with the B6 wire-up" sentence and the "(EL0 userspace-task, B6)" tag); `grep -n "dormant" docs/architecture/scheduler.md` returns nothing.
- [x] `exceptions.md`: lines 58, 105, 109, and 133 state in the past tense that the `+0x400` EL0 path is exercised at runtime, with the T-028 QEMU-smoke evidence cited (two expected SVCs inspected in the retained debug/release exception traces; smoke.sh gates markers and panic/fault rejection, not an exact SVC count); the sequence-diagram participant at line 109 ("EL0 task in B6") and the "(B6)" at line 133 no longer read as future work.
- [x] `security-model.md` capability table (lines 128-143): split into "Implemented (v1)" (Task, Endpoint, Notification, AddressSpace, DebugConsole with its `CONSOLE_WRITE` right) and "Planned" (the remaining kinds), linking ADR-0031; the kinds and the rights column of the implemented table are verified against `kernel/src/cap/mod.rs:110` (`CapObject`) and `kernel/src/cap/rights.rs`, not carried over from the old "Typical rights" column. Line 330 (cross-table CDT open question) gains "(see ADR-0023 for the deferred decision and its candidate options)" with a relative link, mirroring line 328.
- [x] `memory-management.md`: the "Forward-portable to the future high-half kernel" paragraph (line 206) and its sibling at line 240 ("Forward-compat to high-half migration (ADR-0033 placeholder)") are rewritten in past tense: the migration landed via T-022 / ADR-0033 and `phys_to_kernel_va` / `phys_frame_kernel_ptr` is the realised helper (verified in `hal/src/mmu/mod.rs:104` and `kernel/src/mm/mod.rs:141`), cross-linking the 2026-05-30 Amendments of UNSAFE-2026-0026 and UNSAFE-2026-0027 (`docs/audits/unsafe-log.md:580`, `:608`).
- [x] `boot.md` content: stage-3 prose (line 19) and the Mermaid sequence (lines 36-83) drop the removed `tyrne: image loaded` banner, correct the "does NOT execute" claim (lines 19, 76), and add the EL0-task bring-up as its own documented stage (AS / Task capability resolution, `USER_TASK_TABLE` console-cap seeding, `add_user_task`, `FAILCLOSED_TABLE` publish), verified against `bsp-qemu-virt/src/main.rs:1438-1627`; `grep -n "tyrne: image loaded\|NOT executed\|does NOT execute" docs/architecture/boot.md` returns nothing.
- [x] `boot.md` memory map (lines 89-101): the untagged ASCII-art fence is replaced by a Mermaid diagram or a plain table with every fence tagged, and its addresses are re-checked against `bsp-qemu-virt/linker.ld` (the map predates the high-half link at `KBASE`); no code fence in the file lacks a language tag.
- [x] `ipc.md`: the `[cancel-recv]` reference at line 65 uses the relative path `../../kernel/src/ipc/mod.rs`, and the "~1425-line file" claim at line 14 is dropped or corrected against `wc -l kernel/src/ipc/mod.rs` (1720 lines on 2026-10-11); `grep -n "github.com/HodeTech" docs/architecture/ipc.md` returns nothing.
- [x] Freshness marker: each of the seven chapters carries the one-line "last verified against" marker defined by T-045 (form and date recorded in this task's review history) after its content has been verified by the criteria above.

- [x] Correct present-tense fault supervision/reclamation, priority/preemption, userspace services/driver IRQ paths and nonexistent BootInfo handoffs; document current cooperative FIFO scheduling, BSP-owned bring-up, bare syscall IPC versus blocking scheduler bridges, live high-half/per-task TTBR0 operation and source-defined capability/loader bounds. Recheck and, if needed, reconcile T-045's overview/index with these chapters. Complete a distinct independent security review of boundary claims in both review rounds.

## Out of scope

- Primary ownership of `overview.md`, `task-loader.md`, `docs/architecture/README.md`, the freshness-marker convention, and the phase-closure checklist item: [T-045](T-045-docs-overview-taskloader-arch-index.md).
- A dedicated new chapter synthesising the syscall ABI and EL0 execution model (a Polish item in `phase-b2.md`).
- Changing any code or ADR text; if a chapter disagrees with an Accepted ADR, the ADR is authoritative and the discrepancy goes to the maintainer.
- The `tyrne: image loaded` line in `README.md` (owned by [T-050](T-050-entry-docs-and-glossary-sync.md)).

## Approach

Edit each chapter in place; keep its structure, replace the stale claims, and cite the tasks and ADRs that delivered the live path (T-024, T-025, T-026, T-028; ADR-0030, ADR-0031, ADR-0037, ADR-0038, ADR-0039).
For `security-model.md`, derive the "Implemented" table from `CapObject` and `CapRights` first, then verify each remaining row against actual planning authority before labelling it "Planned"; do not preserve invented kinds/rights as an implemented contract.
For `boot.md`, rebuild the stage-3 description from `kernel_main_high` as it reads today; the fresh source-bound debug/release traces retained by T-045 are the reference sequence, and fragile values are elided with `...`.
For the memory map, the plan item allows either a Mermaid diagram (for example a vertical `flowchart TB`) or a tagged plain table; prefer whichever stays accurate with the least text, and record the choice in the review history.
Mermaid only for diagrams, per the documentation-style standard.

## Definition of done

Doc-only variant:

- [x] Every relative link (`](…)` target) in each touched file resolves to an existing path or heading.
- [x] `git diff --stat` lists only: `docs/architecture/{hal,scheduler,exceptions,security-model,memory-management,boot,ipc}.md`, the necessary overview/index coherence corrections, `docs/roadmap/current.md` and this task file.
- [x] New or changed diagrams are Mermaid with a prose lead-in; all fences are tagged; text is English ([`documentation-style.md`](../../../standards/documentation-style.md)).
- [x] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [x] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

**Step-scoped evidence allowance.** In addition to the named content files, the step may update this task, `docs/roadmap/current.md`, the B.2 task/track indexes, governing decision references, source-bound reports/raw evidence, canonical review artifacts and their indexes where necessary. Verify this allowance against the step commit range, not the full stacked branch. Record a demonstrated existing-scope reason for any further file.

## Design notes

**Open decisions.** None blocking (memory-map form and marker wording are implementer choices recorded in the review history).

**Location re-verification (2026-10-11, against the current tree).**
All plan-item locations reproduce: `hal.md:94`, `scheduler.md:73,90`, `exceptions.md:58,105,133`, `security-model.md:132-143` (table header at 132, rows 134-143, heading at 128), `security-model.md:330`, `memory-management.md:206`, `boot.md:19,76-77,89-101`, `ipc.md:14,65`; the EL0 setup in `main.rs` spans lines 1438-1627.
Additional occurrences of the same stale premises, folded into the criteria above: `exceptions.md:109` and `:133`, `scheduler.md:90`, `memory-management.md:240`.
`memory-management.md:194` also cites the `tyrne: image loaded (...)` smoke line as the verification artefact; that sentence is historical (2026-05-14) and should be marked as such rather than removed.
The `ipc.md` line count has drifted from the claimed 1425 to 1720.

**Sequencing.**
The overview Boot-flow diagram and the README Status cells owned by [T-045](T-045-docs-overview-taskloader-arch-index.md) depend on the `boot.md` rewrite here; if T-045 lands first, re-check them after this task.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-12 | Codex (AI agent), maintainer-approved reconciliation | Old: selected sentence edits, unchanged planned capability rows and an exact-count smoke-script claim. Approved replacement: all seven chapters source-verified, future mechanisms labelled, actual rights/bounds/fault/exit behavior, inspected trace counts and distinct security rounds; overview/index coherence permitted. See [approved preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); preparation only, status unchanged. |
| 2026-10-13 | Codex (AI agent) | Step 3 starts after T-045 completed both fresh code/security rounds (`d71aa4a`). Whole seven-chapter source review, exact date/source/task freshness, actual capability rights and boot/exception/scheduler limits, then overview/boot/index coherence. Runtime source remains unchanged from T-045 capture `4ad0b3d`; reuse those retained matching-profile traces without claiming another run. No new decision or executable change; both fresh rounds remain pending. |
| 2026-10-13 | Codex (AI agent), implementation | Whole seven-chapter refresh against source `da18ed5c2a2d8b3d61f82337a9da021d05d73451`; no executable delta from retained runtime `4ad0b3d`. Applied the exact T-045 marker form, chose a PA/VMA table for boot memory layout, preserved incoming memory/boot anchors and scheduler historical revision, rechecked all nine index cells plus overview/boot coherence. Broader source-defined bounds/fault/exit/IRQ/transfer behavior replace stale design claims. [Verification report](../../reports/2026-10-13-t046-subsystem-architecture-verification.md); review rounds pending, status remains In Progress. |
| 2026-10-13 | Codex (AI agent), R1 corrections | Initial fresh code and distinct subsequent security passes at `5e191ad` requested six unique source-confirmed prose corrections (three Medium, three Low): SP_EL0 frame slot, block-error split, inherited idle mask, free-list capacity check, PanicInfo diagnostic order, and PMM type-versus-free alignment boundary. All occurrences and the verification report corrected; no executable/evidence mutation or new run. First-round correction verification and fresh R2 remain pending; status In Progress. |
| 2026-10-13 | Codex (AI agent), both fresh rounds complete | [Code rounds](../../reviews/code-reviews/2026-10-13-t046-subsystem-architecture.md) and [distinct security rounds](../../reviews/security-reviews/2026-10-13-t046-subsystem-architecture.md) Approve cumulative `d71aa4a..4b33607`. Six unique R1 findings fixed and independently verified; no new R2 finding. Whole seven chapters, nine index cells and overview/boot/loader coherence checked; T-045 shared criteria close. Status In Review, no date_done. T-048 proceeds; no new runtime run or full-corpus/phase closure claim. |
