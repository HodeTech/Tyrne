# T-026 — current-task capability table + per-task window in `syscall_entry` (B6 gate #3)

- **Phase:** B
- **Milestone:** B6 — First userspace "hello" (step 4b of the [B6 dependency-ordered sequence](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello); closes [T-021 carry-forward **gate #3**](../../../roadmap/phases/phase-b.md#t-021-carry-forward-gates-must-close-before-a-real-el0-task-runs))
- **Status:** Draft (sibling of [T-025](T-025-user-access-translation.md); opened in the [ADR-0038](../../../decisions/0038-mmu-translate-and-user-access.md) Propose commit because that ADR's dependency chain names it — [ADR-0025 §Rule 1](../../../decisions/0025-adr-governance-amendments.md). **No ADR of its own.**)
- **Created:** 2026-05-31
- **Author:** @cemililik (+ Claude Opus 4.8 agent)
- **Dependencies:** [T-025](T-025-user-access-translation.md) (the translate-based, `<M: Mmu>`-generic `SyscallContext` this sources a real task's AS + capability table into); [ADR-0030](../../../decisions/0030-syscall-abi.md) (§Dependency-chain step 7 already names "`SYSCALL_STUB_TABLE` → scheduler current-task table" — this task needs **no new ADR**); [ADR-0021](../../../decisions/0021-raw-pointer-scheduler-ipc-bridge.md) (the raw-pointer scheduler-bridge discipline the per-task `*mut CapabilityTable` rides); [ADR-0014](../../../decisions/0014-capability-representation.md) (per-subject table unforgeability — the property gate #3 preserves); [ADR-0037](../../../decisions/0037-el0-entry-context.md) (`add_user_task` — the registration site the cap-table binding is added to); [ADR-0028](../../../decisions/0028-address-space-data-structure.md) (the `AddressSpaceHandle` → `AddressSpace` lookup the window derivation uses).
- **Informs:** With [T-025](T-025-user-access-translation.md), completes the syscall-boundary gates so the B6 wire-up can run a real EL0 task: `syscall_entry` then resolves capabilities in the **running task's own table** (not the kernel stub) and copies through the **running task's own AS** (translate-checked). Does **not** itself run a task.
- **ADRs required:** **None.** Pure plumbing authorised by [ADR-0030 §Dependency-chain step 7](../../../decisions/0030-syscall-abi.md) + [ADR-0014](../../../decisions/0014-capability-representation.md); the raw-pointer binding follows the [ADR-0021](../../../decisions/0021-raw-pointer-scheduler-ipc-bridge.md) umbrella (an Amendment to UNSAFE-2026-0012/0014 if the aliasing surface widens, decided in implementation — no new ADR). No new `unsafe` design.

---

## User story

As the kernel, I want `syscall_entry` to resolve a syscall's capability handles in the **running EL0 task's own capability table** and to bound/translate its user buffers against the **running task's own address space** — both looked up from the scheduler's current task — so that a real EL0 task names only the capabilities it holds (per-subject unforgeability, [ADR-0014](../../../decisions/0014-capability-representation.md)) and the gate #1 translate path ([T-025](T-025-user-access-translation.md)) runs against the right `TTBR0`. Today `syscall_entry` resolves against a dedicated `SYSCALL_STUB_TABLE` and bounds against the whole RAM extent — correct only for the trusted B5 EL1 stub.

## Context

The scheduler tracks the current task (`Scheduler::current: Option<TaskHandle>`) and per-slot `task_address_space_handles[]`, but has **zero** knowledge of capability tables — they live as independent BSP statics (`TABLE_A`/`TABLE_B`/`SYSCALL_STUB_TABLE`), and `syscall_entry` holds no scheduler reference. T-026 adds the missing binding (task → its capability table) and rewires `syscall_entry` to source both the capability table and the address space from the scheduler's current task, **failing closed** when no current task resolves. [ADR-0030 §Dependency-chain step 7](../../../decisions/0030-syscall-abi.md) already named this as the B6 step; no new decision is needed.

## Acceptance criteria

- [ ] **Scheduler task→table binding** ([`kernel/src/sched/mod.rs`](../../../../kernel/src/sched/mod.rs)): a per-slot `task_cap_tables: [Option<*mut CapabilityTable>; TASK_ARENA_CAPACITY]` (mirroring `task_address_space_handles`; **raw pointer — tables stay BSP-owned**, no ownership transfer, [ADR-0021](../../../decisions/0021-raw-pointer-scheduler-ipc-bridge.md) discipline), written by `add_user_task` (new `cap_table: *mut CapabilityTable` parameter). **Not** embedded in `Task` (keeps `Task` minimal — `id + address_space_handle`).
- [ ] **Scheduler accessors:** `current_user_table(&self) -> Option<*mut CapabilityTable>` and `current_address_space_handle(&self) -> Option<AddressSpaceHandle>` — resolve `current` → slot index → the parallel arrays; `None` when there is no current task or the slot is unregistered.
- [ ] **`syscall_entry` rewire** ([`bsp-qemu-virt/src/syscall.rs`](../../../../bsp-qemu-virt/src/syscall.rs)): source `caller_table` from `SCHED.current_user_table()` (not `SYSCALL_STUB_TABLE`), the AS from `current_address_space_handle()` → `AS_ARENA`, and the per-task `UserAccessWindow` from the loaded image span; pass `mmu` + `task_as` into the `<M: Mmu>` `SyscallContext` ([T-025](T-025-user-access-translation.md)).
- [ ] **Fail-closed** (security-critical, never weaken): if `current` is `None`, the slot has no bound table, or the AS handle is stale/absent, `syscall_entry` **must not** fall back to `SYSCALL_STUB_TABLE` or any ambient table. It dispatches with an **empty** `CapabilityTable` (every lookup → `CapError::InvalidHandle`) + `UserAccessWindow::empty()` (every non-zero copy → `FaultAddress`), or short-circuits to `SyscallError::FaultAddress`/`InvalidHandle` before dispatch. No path resolves a capability in a table other than the verified current task's own ([ADR-0014](../../../decisions/0014-capability-representation.md) preserved).
- [ ] **Dispatcher unchanged:** [`dispatch`](../../../../kernel/src/syscall/dispatch.rs) resolves only against `ctx.caller_table` / `ctx.user_window` / `ctx.mmu` — only the BSP's *source* of those moves. Panic-free, host-tested behaviour intact.
- [ ] **Host tests:** `add_user_task` records the cap-table pointer; `current_user_table()` / `current_address_space_handle()` return the running task's binding and `None` for no-current / unregistered slot; a fake-current-task dispatch resolves a cap **only** in that task's table (a cap absent from it → `InvalidHandle`); the no-current-task path yields the fail-closed empty-table/empty-window outcome (`FaultAddress`/`InvalidHandle`), never an ambient grant.
- [ ] **All gates green:** host tests (+N), host + kernel clippy `-D warnings`, `cargo fmt --check`, kernel build, Miri. **QEMU smoke:** the dormant `+0x200` smoke is re-seeded with a fake current task (or retired in favour of the B6 `+0x400` EL0 smoke); documented in the PR. `SYSCALL_STUB_TABLE` retired from the real-EL0 path.

## Out of scope

- **gate #1 (the translate mechanism)** — [T-025](T-025-user-access-translation.md) (this rides on it).
- **Running a real EL0 task / the `+0x400` round-trip** — the B6 wire-up.
- **Seeding the EL0 task's table with its initial caps** (the debug-console cap) — the B6 wire-up (this task makes the table *reachable*; populating it is the wire-up's job).
- **A `CapabilityTableArena` / kernel-owned table registry** — out of scope; the raw-pointer binding matches the existing IPC bridge. A registry is a later ADR if the BSP-static model is outgrown.

## Approach

Mirror the existing `task_address_space_handles` parallel-array pattern for the cap-table binding (single source of truth, set at `add_user_task`), add the two accessors, and rewire `syscall_entry` to source table + AS + window from `SCHED.current`. The fail-closed default (empty table + empty window) is the security crux: a forgotten or stale binding **over-grants nothing**. The `*mut CapabilityTable` aliasing rides the [ADR-0021](../../../decisions/0021-raw-pointer-scheduler-ipc-bridge.md) no-`&mut`-across-switch discipline — the syscall path holds the `&mut` across one dispatch and does not context-switch on that data plane; the `Send`/`Sync` story for the pointer array gets an explicit audit note (UNSAFE-2026-0012/0014 Amendment) if the surface widens.

## Definition of done

All acceptance criteria checked; gates green (incl. Miri); the smoke change documented; `current.md` + [phase-b.md gate #3](../../../roadmap/phases/phase-b.md#t-021-carry-forward-gates-must-close-before-a-real-el0-task-runs) updated; **security-relevant — flagged for explicit security review** (capability-table sourcing + fail-closed). Lands **after** [T-025](T-025-user-access-translation.md) (its `<M: Mmu>` `SyscallContext` is the surface this sources into).

## Review history

- **2026-05-31 — opened Draft** in the [ADR-0038](../../../decisions/0038-mmu-translate-and-user-access.md) Propose commit (the ADR's dependency chain names it; [ADR-0025 §Rule 1](../../../decisions/0025-adr-governance-amendments.md)). No ADR of its own — pure plumbing per [ADR-0030 §Dependency-chain step 7](../../../decisions/0030-syscall-abi.md). Implementation follows T-025's merge.
