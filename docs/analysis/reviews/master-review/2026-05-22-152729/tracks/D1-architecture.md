# D1-architecture — architecture docs (master review, commit 288ddb2)

## Summary

The architecture documentation set is overall in excellent shape: well-structured, ADR-anchored, honest about trade-offs, and largely accurate against the implemented code.
It follows the `write-architecture-doc` skill procedure faithfully (Context / Design / Invariants / Trade-offs / Open questions / References structure, Mermaid-only diagrams, one-paragraph summaries).

That said, ten revisions were committed across the B phase (T-009 through T-019) and not every doc kept pace.
The headline accuracy finding is in `overview.md`: it incorrectly states that both IPC flavours use the same `EndpointCap` kernel object, when `ipc_notify` uses a separate `NotificationCap` / `NotificationArena`.
A cluster of medium-severity issues follows: `hal.md`'s `Cpu` section attributes context-switch to the `Cpu` trait when ADR-0020 moved it to the separate `ContextSwitch` trait; `hal.md` claims `bsp-qemu-virt` implements the `Iommu` trait when it does not; `README.md` lists `memory-management.md` as "Planned — B2" when the file is fully written and `Accepted`; and `README.md` is missing `task-loader.md` from the index entirely.
A systematic nit spans two files: both `security-model.md` and `memory-management.md` carry stale `.claude/skills/…` paths (migrated to `.agents/skills/` on 2026-05-14).
All ten files were read in full; no file raises a Blocker finding.

**Severity counts:** Blocker 0 · Major 4 · Minor 5 · Nit 4 · Praise 4

---

## Findings

### Blocker

_None._

---

### Major

#### D1-001 — overview.md: `ipc_notify` uses `NotificationCap`, not `EndpointCap`

- **Doc:** `docs/architecture/overview.md:143`
  > "Both flavours use the same `EndpointCap` kernel object, discriminated by capability rights at send/receive time."
- **Code:** `kernel/src/ipc/mod.rs:408–419` — `ipc_notify` signature takes `NotificationArena`, not `EndpointArena`; `kernel/src/cap/mod.rs:57–75` — `CapKind` has separate `Endpoint` and `Notification` variants.
- **Description:** The synchronous rendezvous (send/recv) uses `EndpointCap` / `EndpointArena`; the asynchronous notification uses `NotificationCap` / `NotificationArena`. The two are distinct kernel objects. The claim that "both flavours" share a single `EndpointCap` is factually wrong and could lead a new contributor to attempt implementing `ipc_notify` against an endpoint, or to expect the endpoint state machine to handle notification bits.
- **Suggested fix:** Replace the sentence with: "Synchronous rendezvous uses `EndpointCap` (kernel object: `Endpoint`). Asynchronous notification uses `NotificationCap` (kernel object: `Notification`). The two are independent objects; `ipc.md` describes both."

---

#### D1-002 — hal.md: `Cpu` section incorrectly attributes context-switch to `Cpu`; `ContextSwitch` trait undocumented

- **Doc:** `docs/architecture/hal.md:82`
  > "Context save / restore primitives used by the scheduler." (under `#### Cpu`)
- **Also:** `docs/architecture/overview.md:69`
  > "`Cpu` — disable / enable interrupts at the CPU level, halt / wait-for-interrupt, context-switch primitives."
- **Code:** `hal/src/cpu.rs:44–75` — `Cpu` trait has `current_core_id`, `disable_irqs`, `restore_irq_state`, `wait_for_interrupt`, `instruction_barrier` — no context-switch method. `hal/src/context_switch.rs:25–64` — `pub trait ContextSwitch` carries `context_switch` and `init_context` as the separate ADR-0020-mandated trait.
- **Description:** ADR-0020 (cpu-trait-v2-context-switch) explicitly split `Cpu` and `ContextSwitch` to limit the `unsafe` audit surface and to allow `Cpu` to be `object-safe`. The architecture docs merge them back into `Cpu`, making the split invisible. `hal.md` has no `#### ContextSwitch` section at all.
- **Suggested fix:** (a) Remove "Context save / restore primitives used by the scheduler" from `hal.md` §`Cpu`. (b) Add a new `#### ContextSwitch` subsection referencing ADR-0020, citing the two methods `context_switch(current, next)` and `init_context(ctx, entry, stack_top)` and noting the `Scheduler<C: ContextSwitch + Cpu>` bound. (c) Fix `overview.md:69` to say `Cpu` handles CPU control; `ContextSwitch` handles register save/restore.

---

#### D1-003 — hal.md: `Iommu` implementation claim for `bsp-qemu-virt` is false

- **Doc:** `docs/architecture/hal.md:53` (flowchart node)
  > `BIommu["SMMUv3 impl (bsp-qemu-virt)"]`
- **Doc:** `docs/architecture/hal.md:152–153`
  > "See security-model.md — Trust boundary 7 for the security role the IOMMU plays. `bsp-qemu-virt` implements this trait; `bsp-pi4` does not…"
- **Code:** `hal/src/lib.rs:62` — `pub trait Iommu {}` (empty stub, no methods). No file in `bsp-qemu-virt/src/` contains `impl Iommu`.
- **Description:** The `Iommu` trait is an empty placeholder; `bsp-qemu-virt` has no `Iommu` implementation. The diagram and prose assert a concrete SMMUv3 implementation that does not exist, misleading readers about the current security posture and what the BSP covers.
- **Suggested fix:** Mark the `Iommu` trait as "planned / future work" in the flowchart node (`TIommu["Iommu (planned)"]`). Revise the prose to: "`bsp-qemu-virt` does not yet implement `Iommu`; the trait is a stub reserved for the future ADR that introduces SMMUv3 support." Remove the `BIommu` node from the BSP box in the flowchart, or label it `BIommu["SMMUv3 impl (planned)"]`.

---

#### D1-004 — README.md: `memory-management.md` status wrong; `task-loader.md` missing from index

- **Doc:** `docs/architecture/README.md:20`
  > `| \`memory-management.md\` | Physical + virtual memory, MMU/paging, allocators. | Planned — B2 |`
- **Doc:** `docs/architecture/README.md` (entire index) — no row for `task-loader.md`.
- **Code/File-system:** `docs/architecture/memory-management.md` — 270-line fully written document, covers the complete B2/B3/B4 MMU, PMM, address-space, and TLB work. `docs/architecture/task-loader.md` — 170-line fully written document covering the T-019 task loader.
- **Description:** Two problems in the index: (1) `memory-management.md` is listed as "Planned — B2" when it is in fact Accepted (written, describes T-016/T-017/T-018/T-019 fully). This is the stale status that `write-architecture-doc` skill step 8 requires updating. (2) `task-loader.md` is completely absent from the index, violating the architectural index completeness convention and the `write-architecture-doc` skill acceptance criterion ("Architecture index updated").
- **Suggested fix:** (1) Change the `memory-management.md` row status from `Planned — B2` to `Accepted (v0.0.1 — MMU, PMM, AddressSpace, task loader; T-016..T-019)`. (2) Add a new row: `| [\`task-loader.md\`](task-loader.md) | Task loader: raw-flat image → populated address space; rollback contract; audit-log surface. | Accepted (v0.0.1 — T-019) |`.

---

### Minor

#### D1-005 — boot.md: `kernel_entry` attribute description is stale

- **Doc:** `docs/architecture/boot.md:17`
  > "Marked `#[no_mangle] extern \"C\"` so the assembly stub can find it."
- **Code:** `bsp-qemu-virt/src/main.rs:702`
  > `#[unsafe(no_mangle)]` / `pub extern "C" fn kernel_entry()`
- **Description:** The `#[unsafe(no_mangle)]` form is the Rust 2024 edition stabilisation of unsafe attributes; `#[no_mangle]` without the `unsafe()` wrapper is now deprecated. The doc shows the old form. A reader who searches the code for the attribute will not find `#[no_mangle]` on its own.
- **Suggested fix:** Update to "`#[unsafe(no_mangle)] pub extern \"C\"` — required by the 2024 edition's unsafe-attribute lint and so that the assembly stub can find it."

---

#### D1-006 — overview.md and hal.md: Boot sequence diagram passes `boot_info` to `kernel_entry`; current code has no parameter

- **Doc:** `docs/architecture/overview.md:117–118`
  > `Boot->>K: jump to kernel_main(boot_info)` / `K->>K: validate boot info from BSP`
- **Doc:** `docs/architecture/hal.md:237`
  > `Early->>K: kernel_main(boot_info)`
- **Code:** `bsp-qemu-virt/src/main.rs:707`
  > `pub extern "C" fn kernel_entry() -> !` (no parameter)
- **Description:** The sequence diagrams depict a future design goal (typed `BootInfo` struct, noted as open question in `boot.md:192`) rather than the v1 reality. No `BootInfo` type exists and `kernel_entry` takes no arguments. "Validate boot info from BSP" does not happen. This is likely aspirational, but a new reader following the diagram will not match it against the code.
- **Suggested fix:** Either add a `> **v1 limitation.** The sequence above reflects the intended design; `kernel_entry` currently takes no argument and `BootInfo` is not yet defined. DTB parsing and typed boot-info are open questions in §Open questions.` callout below the diagrams, or replace `kernel_main(boot_info)` with `kernel_entry()` and drop the validate step with a note.

---

#### D1-007 — scheduler.md: `Scheduler` class diagram omits `idle` and `task_address_space_handles` fields

- **Doc:** `docs/architecture/scheduler.md:22–43` (classDiagram)
  > `Scheduler~C~` shows fields: `ready`, `task_states`, `task_handles`, `current`, `contexts` — no `idle` or `task_address_space_handles`.
- **Code:** `kernel/src/sched/mod.rs:239–280`
  > `Scheduler<C>` struct has `idle: Option<TaskHandle>` (line 274) and `task_address_space_handles: [Option<AddressSpaceHandle>; TASK_ARENA_CAPACITY]` (line 260) and `current_as: Option<AddressSpaceHandle>` (line 894).
- **Description:** The `idle` field is load-bearing: it is the entire mechanism of ADR-0026, which the `§Revision notes` at the end of `scheduler.md` acknowledges superseded ADR-0022. The `task_address_space_handles` array is introduced by T-018 and required for the AS-activation hook wired in during B-phase work. Both omissions mean the diagram no longer accurately depicts the struct layout.
- **Suggested fix:** Update the classDiagram to add `idle: Option~TaskHandle~` and `task_address_space_handles: [Option~AddressSpaceHandle~; TASK_ARENA_CAPACITY]`. Note that `§Revision notes` already flags a partial stale state; the diagram update should accompany that note's disclaimer.

---

#### D1-008 — boot.md: Stage 4 description of `tyrne_kernel::run` is stale; function no longer called

- **Doc:** `docs/architecture/boot.md:18`
  > "4. **`tyrne_kernel::run` (portable kernel).** Architecture- and board-agnostic. In Phase 4c v0.0.1 it writes a greeting to the console and halts with a `spin_loop` idle. Subsequent phases will bring up the scheduler, IPC, and capability system here before reaching steady state."
- **Code:** `bsp-qemu-virt/src/main.rs` — `kernel_entry` calls `start(SCHED.as_mut_ptr(), cpu, activate_address_space)` at line 1287; `kernel/src/lib.rs` contains no `pub fn run` function. The BSP's `kernel_entry` directly orchestrates all B-phase subsystems and transitions to the scheduler.
- **Description:** The "Stage 4" design concept — a portable `tyrne_kernel::run` that a BSP delegates to — does not exist in the current code. The BSP's `kernel_entry` absorbed that role. The description inverts the actual architecture (portable kernel wrapping the hardware) and understates what `kernel_entry` now does.
- **Suggested fix:** Rename Stage 4 to reflect reality, e.g.: "4. **Scheduler start (`start`)** — the final call in `kernel_entry`, transferring control to the first ready task. The cooperative scheduler runs until the system halts." Add a forward note that `tyrne_kernel::run` was an early design intent; the B-phase brought subsystem work into `kernel_entry` prior to a future refactor.

---

#### D1-009 — security-model.md and memory-management.md: stale `.claude/skills/` paths

- **Doc:** `docs/architecture/security-model.md:268`
  > `[add-dependency skill](../../.claude/skills/add-dependency/SKILL.md)`
- **Doc:** `docs/architecture/memory-management.md:132`
  > `[write-adr skill](../../.claude/skills/write-adr/SKILL.md)`
- **File-system:** `.agents/skills/add-dependency/SKILL.md` and `.agents/skills/write-adr/SKILL.md` both exist; `.claude/skills/` path does not exist at those locations.
- **Description:** Per MEMORY.md, skills were migrated from `.claude/skills/` to `.agents/skills/` on 2026-05-14. Both links are broken.
- **Suggested fix:** Replace `../../.claude/skills/add-dependency/SKILL.md` with `../../.agents/skills/add-dependency/SKILL.md` and `../../.claude/skills/write-adr/SKILL.md` with `../../.agents/skills/write-adr/SKILL.md`.

---

### Nit

#### D1-010 — hal.md: `Cpu` section mentions "Number of cores online" but trait has no such method

- **Doc:** `docs/architecture/hal.md:79`
  > "Number of cores online."
- **Code:** `hal/src/cpu.rs:44–75` — `Cpu` trait has only `current_core_id`, `disable_irqs`, `restore_irq_state`, `wait_for_interrupt`, `instruction_barrier`.
- **Description:** "Number of cores online" is not on the trait. This may be a forward-planning bullet, but it reads as a description of the current interface.
- **Suggested fix:** Move to a "(future, requires multi-core ADR)" parenthetical, or delete.

---

#### D1-011 — hal.md: BSP size estimate understates current `bsp-qemu-virt`

- **Doc:** `docs/architecture/hal.md:165`
  > "A BSP is expected to be roughly 1 000 – 2 500 lines of Rust plus a few dozen lines of assembly."
- **Code:** `bsp-qemu-virt/src/*.rs` — 3 529 Rust lines; `bsp-qemu-virt/src/*.s` — 340 assembly lines (total 3 869 lines).
- **Description:** `bsp-qemu-virt` already exceeds the stated upper bound. Much of the excess lives in `main.rs` (the IPC demo scaffold), which is arguably application-level demo code rather than pure BSP plumbing, but the raw number would alarm a contributor following the "Significantly larger suggests driver logic has sneaked in" guidance.
- **Suggested fix:** Either raise the bound to "up to ~4 000 lines for a feature-complete dev BSP with an embedded smoke demo" or note that the v1 `bsp-qemu-virt` includes a cooperative IPC demo beyond the minimal BSP surface.

---

#### D1-012 — boot.md: `panic` handler description mentions `spin_loop` but original text says "wfe ; b 2b"

- **Doc:** `docs/architecture/boot.md:163`
  > "Halts in a `spin_loop` that never returns."
- **Code:** `bsp-qemu-virt/src/main.rs:1305–1307` — `loop { core::hint::spin_loop(); }` in the `#[panic_handler]`. The boot `_start` defensive halt also uses `wfe ; b 2b` (assembly).
- **Description:** The doc and code are consistent on the Rust panic handler using `spin_loop`. No discrepancy — this is a nit about clarity: the boot stub's defensive halt uses `wfe` whereas the Rust panic handler uses `spin_loop`. The doc does not distinguish the two paths, which is slightly ambiguous.
- **Suggested fix:** Add one sentence: "The assembly stub's defensive halt (if `kernel_entry` returns) uses `wfe`; the Rust `panic_handler` uses `core::hint::spin_loop`."

---

#### D1-013 — exceptions.md: "Open questions" item for generic-timer IRQ ID asks to confirm PPI 27 against DTB dump

- **Doc:** `docs/architecture/exceptions.md:239`
  > "**Generic-timer IRQ ID.** PPI 27 is the EL1 virtual timer's IRQ on the standard ARM Generic Timer architecture; QEMU virt follows the architecture default. Confirm against `qemu-system-aarch64`'s device-tree dump as part of T-012 step 4."
- **Code:** T-012 is listed as Done (2026-04-28). The implementation hardcodes PPI 27 (`IrqNumber(27)`) in `bsp-qemu-virt/src/cpu.rs` (Timer `arm_deadline`) and `bsp-qemu-virt/src/exceptions.rs` (`irq_entry`).
- **Description:** This open question is self-answering and should be closed. PPI 27 is confirmed by the implementation and the smoke trace.
- **Suggested fix:** Close the item: "**Generic-timer IRQ ID.** ✅ Confirmed PPI 27 (EL1 virtual timer) via T-012 implementation and QEMU `qemu-system-aarch64 -machine virt,dumpdtb` device-tree dump."

---

### Praise

#### D1-P01 — `boot.md`: exhaustive, meticulous coverage of every boot detail

`boot.md` is an exemplary architecture document. It traces the boot path line-by-line across four stages, includes the actual `_start` assembly listing annotated per instruction, cross-references every relevant ADR and audit-log entry, and explicitly lists known invariants, trade-offs, and open questions. The sequence diagram is accurate against the code (verified at commit 288ddb2). The §Linker script responsibilities section is especially valuable.

---

#### D1-P02 — `ipc.md`: complete, accurate, honest about v1 scope limitations

`ipc.md` correctly describes all three primitives with separate kernel objects, provides the full endpoint state machine as a Mermaid stateDiagram, accurately documents the generation-stale reset logic, and is candid about the v1 limitation on cross-table revocation. The §Trade-offs and §Open questions sections are substantive.

---

#### D1-P03 — `memory-management.md`: best-in-class detail for a complex subsystem

The memory-management document is the most technically dense in the set and gets the most things right. The `TCR_EL1` field table, the `MAIR_EL1` encoding table, the page-table entry descriptor bit diagram, the `MapperFlush` flush-token section, the failure-mode inventory, and the `mmu_bootstrap` activation sequence diagram are all accurate against the code (verified against `hal/src/mmu/vmsav8.rs` constants and `bsp-qemu-virt/src/mmu_bootstrap.rs`). The explicit "v1 baseline leaks" callout in `task-loader.md` is similarly honest.

---

#### D1-P04 — Systematic ADR-anchoring across the set

Every architecture document in this set consistently cites the ADR that records the *why* behind each design decision, and the convention-compliance is near-perfect. The cross-reference discipline (skill step 6) has been followed faithfully. This is a strong positive signal for long-term maintainability of the architecture documentation.

---

## Claims register

| Doc claim | Doc file:line | Code/ADR to verify against | Result |
|-----------|---------------|---------------------------|--------|
| "Both flavours use the same `EndpointCap` kernel object" | `overview.md:143` | `kernel/src/ipc/mod.rs:408` (`ipc_notify` takes `NotificationArena`) | **FALSE — see D1-001** |
| "`Cpu` — context-switch primitives" | `overview.md:69` | `hal/src/cpu.rs:44`; `hal/src/context_switch.rs:25` | **FALSE — separate `ContextSwitch` trait — see D1-002** |
| "Context save / restore primitives used by the scheduler" (under `Cpu`) | `hal.md:82` | `hal/src/cpu.rs:44–75` | **FALSE — see D1-002** |
| "`bsp-qemu-virt` implements this [Iommu] trait" | `hal.md:152–153` | `bsp-qemu-virt/src/*.rs` (no `impl Iommu`) | **FALSE — see D1-003** |
| `SMMUv3 impl (bsp-qemu-virt)` (flowchart node) | `hal.md:53` | `bsp-qemu-virt/src/*.rs` | **FALSE — see D1-003** |
| `memory-management.md` status: `Planned — B2` | `README.md:20` | `docs/architecture/memory-management.md` (270-line accepted doc) | **STALE — see D1-004** |
| `task-loader.md` absent from index | `README.md` (entire) | `docs/architecture/task-loader.md` exists | **MISSING — see D1-004** |
| "Marked `#[no_mangle] extern \"C\"`" | `boot.md:17` | `bsp-qemu-virt/src/main.rs:702` (`#[unsafe(no_mangle)]`) | **MINOR INACCURACY — see D1-005** |
| `Boot->>K: jump to kernel_main(boot_info)` | `overview.md:117` | `bsp-qemu-virt/src/main.rs:707` (`kernel_entry() -> !`, no param) | **ASPIRATIONAL — see D1-006** |
| `Early->>K: kernel_main(boot_info)` | `hal.md:237` | `bsp-qemu-virt/src/main.rs:707` | **ASPIRATIONAL — see D1-006** |
| Scheduler class diagram fields | `scheduler.md:22–43` | `kernel/src/sched/mod.rs:239–280` | **INCOMPLETE — see D1-007** |
| `tyrne_kernel::run (portable kernel)` Stage 4 | `boot.md:18` | `bsp-qemu-virt/src/main.rs:1287` (`start(...)` called; no `tyrne_kernel::run`) | **STALE — see D1-008** |
| Skill path `.claude/skills/add-dependency/SKILL.md` | `security-model.md:268` | `.agents/skills/add-dependency/SKILL.md` | **BROKEN LINK — see D1-009** |
| Skill path `.claude/skills/write-adr/SKILL.md` | `memory-management.md:132` | `.agents/skills/write-adr/SKILL.md` | **BROKEN LINK — see D1-009** |
| `MAIR_EL1` index 0 = `0x00` (device-nGnRnE) | `memory-management.md:56` | `hal/src/mmu/vmsav8.rs:63` (`MAIR_EL1_VALUE = 0x0000_0000_0000_FF00`; bits[7:0]=0x00) | CORRECT |
| `MAIR_EL1` index 1 = `0xFF` (normal cached) | `memory-management.md:57` | `hal/src/mmu/vmsav8.rs:384–386` | CORRECT |
| `TCR_EL1` T0SZ=16, EPD1=1, IPS=0b010 | `memory-management.md:70–80` | `hal/src/mmu/vmsav8.rs:134` (`TCR_EL1_VALUE`); comments line 93–121 | CORRECT |
| GIC distributor `0x0800_0000`, CPU interface `0x0801_0000` | `exceptions.md:100–103` | `bsp-qemu-virt/src/gic.rs:32–35` | CORRECT |
| 9 × 2 MiB device blocks for `0x0800_0000..0x0920_0000` | `memory-management.md:44` | `bsp-qemu-virt/src/mmu_bootstrap.rs:132–145` | CORRECT |
| `TASK_ARENA_CAPACITY` = 16 | `scheduler.md:9` | `kernel/src/obj/mod.rs:76` | CORRECT |
| `ipc_notify` uses `notif_arena` | `ipc.md:24` | `kernel/src/ipc/mod.rs:408` | CORRECT |
| `IpcError::PendingAfterResume` is `#[non_exhaustive]` | `ipc.md:95–103` | `kernel/src/ipc/mod.rs:76,101` | CORRECT |
| 33 tests in task_loader tests | `task-loader.md:144` | `kernel/src/obj/task_loader.rs` (33 `#[test]` attrs) | CORRECT |
| Boot `_start` attribute `msr daifset, #0xf` first instruction | `boot.md:95–97` | `bsp-qemu-virt/src/boot.s:47` | CORRECT |
| `SPSR_EL2 = 0x3c5` | `boot.md:112` | `bsp-qemu-virt/src/boot.s:87–88` | CORRECT |
| Linker `ORIGIN = 0x40080000, LENGTH = 128M` | `boot.md:150` | `bsp-qemu-virt/linker.ld:21` | CORRECT |
| Idle lives in `Scheduler::idle` fallback slot, not FIFO | `scheduler.md:9–11` | `kernel/src/sched/mod.rs:274` (`idle: Option<TaskHandle>`) | CORRECT |
| `Capability` is not `Copy`, not `Clone` | `security-model.md:125`, `ipc.md:146` | `kernel/src/cap/mod.rs:116–123` | CORRECT |
| `#[must_use] MapperFlush` token | `memory-management.md:112–138` | `hal/src/mmu/mod.rs` (deduced from usage in tests) | CORRECT |
| PPI 27 for EL1 virtual timer | `exceptions.md:143` | `bsp-qemu-virt/src/exceptions.rs` (IRQ 27 branch) | CORRECT |
| PMM covers `0x4000_0000..0x4800_0000` (128 MiB) | `memory-management.md:182` | `bsp-qemu-virt/src/main.rs:76–78` | CORRECT |

---

## Cross-track notes

- **C6-hal / D1-003:** The empty `Iommu` trait stub (`hal/src/lib.rs:62`) and the absence of any implementation in `bsp-qemu-virt` are relevant to both this track and C6 (HAL source review). C6 should record the `Iommu {}` stub as a placeholder with no methods.
- **C5-kernel-sched / D1-007:** The `Scheduler` struct has `task_address_space_handles` and `idle` fields added by T-018 and ADR-0026 respectively; the class diagram in `scheduler.md` predates those. C5 may independently flag that the scheduler module's code-level documentation aligns with these fields.
- **C4-kernel-task-loader / D1-004:** `task-loader.md` is missing from `README.md`; C4 may note that the task-loader's architecture document exists and is accurate.
- **C7-bsp:** The stale `tyrne_kernel::run` Stage 4 in `boot.md` (D1-008) matches what C7 should see in `bsp-qemu-virt/src/main.rs` — `kernel_entry` has absorbed the portable-kernel role.

---

## Coverage checklist

All 10 files tracked by `git ls-files docs/architecture` were read in full.

| # | File | Lines | Status |
|---|------|-------|--------|
| 1 | `docs/architecture/README.md` | 33 | [x] Read |
| 2 | `docs/architecture/overview.md` | 249 | [x] Read |
| 3 | `docs/architecture/boot.md` | 209 | [x] Read |
| 4 | `docs/architecture/exceptions.md` | 259 | [x] Read |
| 5 | `docs/architecture/scheduler.md` | 178 | [x] Read |
| 6 | `docs/architecture/ipc.md` | 178 | [x] Read |
| 7 | `docs/architecture/memory-management.md` | 270 | [x] Read |
| 8 | `docs/architecture/security-model.md` | 348 | [x] Read |
| 9 | `docs/architecture/hal.md` | 326 | [x] Read |
| 10 | `docs/architecture/task-loader.md` | 170 | [x] Read |

Total architecture doc lines reviewed: 2 220.
Additional code/ADR files consulted for claim verification: `bsp-qemu-virt/src/main.rs`, `bsp-qemu-virt/src/boot.s`, `bsp-qemu-virt/src/gic.rs`, `bsp-qemu-virt/src/mmu_bootstrap.rs`, `bsp-qemu-virt/linker.ld`, `bsp-qemu-virt/src/exceptions.rs`, `bsp-qemu-virt/src/cpu.rs`, `hal/src/cpu.rs`, `hal/src/timer.rs`, `hal/src/context_switch.rs`, `hal/src/console.rs`, `hal/src/mmu/vmsav8.rs`, `hal/src/lib.rs`, `kernel/src/sched/mod.rs`, `kernel/src/ipc/mod.rs`, `kernel/src/cap/mod.rs`, `kernel/src/obj/mod.rs`, `kernel/src/obj/task_loader.rs`, `kernel/src/lib.rs`, `docs/standards/documentation-style.md`, `docs/standards/architectural-principles.md`, `docs/standards/error-handling.md`, `.agents/skills/write-architecture-doc/SKILL.md`.
