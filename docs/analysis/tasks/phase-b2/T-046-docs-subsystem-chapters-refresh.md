# T-046 — Refresh the subsystem architecture chapters (hal, scheduler, exceptions, security-model, memory-management, boot, ipc)

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

As a contributor reading a subsystem chapter, I want each chapter to describe the EL0 entry path, the syscall boundary, and the high-half kernel as the live, tested mechanisms they are, so that I do not mistake shipped behaviour for dormant or future work.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), covering the subsystem-chapter items of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-2.
Seven chapters under `docs/architecture/` were written while Phase B was in progress and still describe milestone B6 as upcoming: `hal.md:94` and `scheduler.md:73` call the EL0 entry mechanism "dormant", `exceptions.md:58,105` say the `+0x400` syscall path is "runtime-verified in B6", and `boot.md:19,76-77` still shows a `tyrne: image loaded` banner and says the loaded image "does NOT execute", although `bsp-qemu-virt/src/main.rs:1438-1627` now brings up the first EL0 task (T-028).
`security-model.md:128-143` lists capability kinds that do not exist and omits `DebugConsole`, the kind that gates the one live privileged operation.
The remaining items are small: a stale high-half "future" paragraph in `memory-management.md`, an untagged ASCII-art memory map in `boot.md`, an absolute GitHub URL and a drifted line-count claim in `ipc.md`, and a missing ADR-0023 pointer in `security-model.md`.

The entry-point documents (`overview.md`, `task-loader.md`, the architecture index) and the freshness-marker convention are [T-045](T-045-docs-overview-taskloader-arch-index.md).
Because the live path was delivered by [T-024](../phase-b/T-024-task-create-from-image.md), [T-025](../phase-b/T-025-user-access-translation.md), [T-026](../phase-b/T-026-current-task-cap-table.md), and [T-028](../phase-b/T-028-el0-userspace-wireup.md) under [ADR-0039](../../../decisions/0039-userland-build-pipeline.md), those are the citations the rewritten passages use.

## Acceptance criteria

Each criterion is one document. Every factual statement written is verified against the code or the `tools/smoke.sh --int` trace, not copied from the old text.

- [ ] `hal.md`: line 94 no longer calls the `init_user_context` mechanism "dormant" or defers the first EL0 task to "the B6 wire-up"; it says the mechanism is live and cites T-023/T-024/T-028 and ADR-0039 (verified against `kernel/src/sched/mod.rs:444` and `bsp-qemu-virt/src/main.rs:1438-1627`); `grep -n "dormant" docs/architecture/hal.md` returns nothing.
- [ ] `scheduler.md`: lines 73 and 90 are updated the same way (the "Shipped dormant ... arrives with the B6 wire-up" sentence and the "(EL0 userspace-task, B6)" tag); `grep -n "dormant" docs/architecture/scheduler.md` returns nothing.
- [ ] `exceptions.md`: lines 58, 105, 109, and 133 state in the past tense that the `+0x400` EL0 path is exercised at runtime, with the T-028 QEMU-smoke evidence cited (the exact 2-SVC fault-class assertion in `tools/smoke.sh --int`); the sequence-diagram participant at line 109 ("EL0 task in B6") and the "(B6)" at line 133 no longer read as future work.
- [ ] `security-model.md` capability table (lines 128-143): split into "Implemented (v1)" (Task, Endpoint, Notification, AddressSpace, DebugConsole with its `CONSOLE_WRITE` right) and "Planned" (the remaining kinds), linking ADR-0031; the kinds and the rights column of the implemented table are verified against `kernel/src/cap/mod.rs:110` (`CapObject`) and `kernel/src/cap/rights.rs`, not carried over from the old "Typical rights" column. Line 330 (cross-table CDT open question) gains "(see ADR-0023 for the deferred decision and its candidate options)" with a relative link, mirroring line 328.
- [ ] `memory-management.md`: the "Forward-portable to the future high-half kernel" paragraph (line 206) and its sibling at line 240 ("Forward-compat to high-half migration (ADR-0033 placeholder)") are rewritten in past tense: the migration landed via T-022 / ADR-0033 and `phys_to_kernel_va` / `phys_frame_kernel_ptr` is the realised helper (verified in `hal/src/mmu/mod.rs:104` and `kernel/src/mm/mod.rs:141`), cross-linking the 2026-05-30 Amendments of UNSAFE-2026-0026 and UNSAFE-2026-0027 (`docs/audits/unsafe-log.md:580`, `:608`).
- [ ] `boot.md` content: stage-3 prose (line 19) and the Mermaid sequence (lines 36-83) drop the removed `tyrne: image loaded` banner, correct the "does NOT execute" claim (lines 19, 76), and add the EL0-task bring-up as its own documented stage (AS / Task capability resolution, `USER_TASK_TABLE` console-cap seeding, `add_user_task`, `FAILCLOSED_TABLE` publish), verified against `bsp-qemu-virt/src/main.rs:1438-1627`; `grep -n "tyrne: image loaded\|NOT executed\|does NOT execute" docs/architecture/boot.md` returns nothing.
- [ ] `boot.md` memory map (lines 89-101): the untagged ASCII-art fence is replaced by a Mermaid diagram or a plain table with every fence tagged, and its addresses are re-checked against `bsp-qemu-virt/linker.ld` (the map predates the high-half link at `KBASE`); no code fence in the file lacks a language tag.
- [ ] `ipc.md`: the `[cancel-recv]` reference at line 65 uses the relative path `../../kernel/src/ipc/mod.rs`, and the "~1425-line file" claim at line 14 is dropped or corrected against `wc -l kernel/src/ipc/mod.rs` (1720 lines on 2026-10-11); `grep -n "github.com/HodeTech" docs/architecture/ipc.md` returns nothing.
- [ ] Freshness marker: each of the seven chapters carries the one-line "last verified against" marker defined by T-045 (form and date recorded in this task's review history) after its content has been verified by the criteria above.

## Out of scope

- `overview.md`, `task-loader.md`, `docs/architecture/README.md`, the freshness-marker convention, and the phase-closure checklist item: [T-045](T-045-docs-overview-taskloader-arch-index.md).
- A dedicated new chapter synthesising the syscall ABI and EL0 execution model (a Polish item in `phase-b2.md`).
- Changing any code or ADR text; if a chapter disagrees with an Accepted ADR, the ADR is authoritative and the discrepancy goes to the maintainer.
- The `tyrne: image loaded` line in `README.md` (owned by [T-050](T-050-entry-docs-and-glossary-sync.md)).

## Approach

Edit each chapter in place; keep its structure, replace the stale claims, and cite the tasks and ADRs that delivered the live path (T-024, T-025, T-026, T-028; ADR-0030, ADR-0031, ADR-0037, ADR-0038, ADR-0039).
For `security-model.md`, derive the "Implemented" table from `CapObject` and `CapRights` first, then move every other row to "Planned" unchanged.
For `boot.md`, rebuild the stage-3 description from `kernel_main_high` as it reads today; the `tools/smoke.sh --int` output and the README Quick-Start trace of 2026-10-11 are the reference sequence, and fragile values are elided with `...`.
For the memory map, the plan item allows either a Mermaid diagram (for example a vertical `flowchart TB`) or a tagged plain table; prefer whichever stays accurate with the least text, and record the choice in the review history.
Mermaid only for diagrams, per the documentation-style standard.

## Definition of done

Doc-only variant:

- [ ] Every relative link (`](…)` target) in each touched file resolves to an existing path or heading.
- [ ] `git diff --stat` lists only: `docs/architecture/{hal,scheduler,exceptions,security-model,memory-management,boot,ipc}.md`, `docs/roadmap/current.md` and this task file.
- [ ] New or changed diagrams are Mermaid with a prose lead-in; all fences are tagged; text is English ([`documentation-style.md`](../../../standards/documentation-style.md)).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

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
