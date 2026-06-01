# Phase C — Multi-core

**Exit bar:** Two or more cores running concurrently, scheduled preemptively, with working cross-core IPC.

**Scope:** Secondary core start via PSCI, per-core state, preemptive scheduling with timer tick, cross-core IPC, multi-core TLB shootdown. Still on QEMU virt; Pi 4 is Phase D.

**Out of scope:** Real hardware, userspace drivers, filesystem, network.

---

## Milestone C1 — Secondary core start

Bring secondary cores online via PSCI `CPU_ON`. Each core arrives at a kernel entry point and waits until the primary core hands it work.

### Sub-breakdown

1. **ADR-0040 — Secondary core start protocol.** PSCI vs. spin-table. Entry point for secondaries (shared with primary or separate). Rendezvous semantics (when the primary considers a secondary "up").
2. **`Cpu` trait v3 extension** — adds `start_core(core_id, entry, context)` and `core_count()`; probably as a sibling `MultiCore` trait to keep `Cpu` v2 stable.
3. **Secondary-core asm entry** in `bsp-qemu-virt` — minimal per-core stack setup before Rust.
4. **Per-core state struct** introduced here (fully fleshed out in C2).
5. **Tests** — QEMU run with `-smp 4` brings all four cores to a known checkpoint; serial shows each core announcing itself.

### Acceptance criteria

- ADR-0040 Accepted.
- `Cpu::start_core` (or sibling trait) lands in `tyrne-hal`.
- All configured cores reach the Rust-level rendezvous point on QEMU.

---

## Milestone C2 — Per-core state

Every online core needs its own current-task pointer, IRQ-mask shadow, and scheduler queue (if per-core queues are chosen).

### Sub-breakdown

1. **ADR-0041 — Per-core state access pattern.** `TPIDR_EL1` pointer vs. indexed lookup. Thread-local-like access to the current core's state.
2. **`PerCore<T>` abstraction** — kernel-provided primitive for per-core state with interior synchronization.
3. **Current-task pointer** moved to per-core state.
4. **Tests** — each core sees its own state; no accidental cross-core access.

### Acceptance criteria

- ADR-0041 Accepted.
- Per-core state accessible from any core via the chosen pattern.
- Tests cover the access invariants.

---

## Milestone C3 — Preemptive scheduler (with timer tick)

Replace the cooperative scheduler from A5 with a preemptive one driven by the timer tick. Per-core scheduling queues (probably; ADR decides).

### Sub-breakdown

1. **ADR-0042 — Scheduler topology.** Per-core queues with work stealing, vs. a single global queue with locking, vs. hybrid. Real-time guarantees (or the lack thereof).
2. **Timer tick wiring** — [`Timer`](../../../hal/src/timer.rs) arm-deadline fires an IRQ; [`IrqController`](../../../hal/src/irq_controller.rs) delivers it; ISR triggers the scheduler's tick handler.
3. **Preemption points** — when and how a running task can be interrupted and the scheduler invoked.
4. **Time slice** — configurable per-task or global for v1.
5. **Idle-core behaviour** — WFI until IRQ, wake on timer or work-steal signal.
6. **Interrupt-masked critical-section primitive on [`tyrne-hal::Cpu`](../../../hal/src/cpu.rs).** Introduce a closure-based `Cpu::without_interrupts(|| { ... })` (equivalent of `x86_64::instructions::interrupts::without_interrupts`) backed by aarch64 `DAIF` manipulation. Every spin-locked kernel resource that an IRQ handler can touch must be acquired inside this closure to avoid handler-vs.-main-path deadlock. Discipline is mandatory, not optional; C3 makes it real because this is the phase where IRQs can interrupt kernel code.
7. **Tests** — two userspace tasks (from B6) time-slice; tick frequency observable; tasks that never yield still get preempted.

### Acceptance criteria

- ADR-0042 Accepted.
- Preemption works: a CPU-bound userspace task is preempted by the tick and another runnable task gets CPU time.
- Idle cores enter low-power WFI.
- No scheduling-related deadlocks or priority inversions (v1 is single priority, so this is mostly vacuous; real-time concerns deferred).

---

## Milestone C4 — Cross-core IPC

A sender on core 0 sending to a receiver on core 1 works. The receiver wakes on the right core; migration is not in scope.

### Sub-breakdown

1. **ADR-0043 — Cross-core wakeup.** IPI-based (inter-processor interrupt) vs. polling. Latency expectations.
2. **IPI support** — new primitive on `IrqController` (or a sibling trait) to send an IPI to another core.
3. **Endpoint rendezvous across cores** — the wait/wake path handles the cross-core case correctly.
4. **Tests** — cross-core IPC round trip; behaviour when the receiver's core is idle (WFI'd); behaviour when both cores are busy.

### Acceptance criteria

- ADR-0043 Accepted.
- IPI primitive implemented for QEMU virt (GICv2 SGI; QEMU virt is GICv2, GIC-400 on Pi 4 — the SGI mechanism applies to both; no IOMMU in v1, per ADR-0036).
- Cross-core IPC has the same correctness guarantees as same-core IPC (atomic cap transfer, etc.).

---

## Milestone C5 — Multi-core TLB shootdown

When an address space is modified on one core, other cores with that address space active must invalidate their TLBs.

### Sub-breakdown

1. **ADR-0044 — TLB shootdown protocol.** Broadcast IPI vs. per-address targeted; whether to extend `Mmu` trait or add a sibling.
2. **`invalidate_tlb_cross_core` primitive** — probably on a sibling trait, since `Mmu` v1 is single-core.
3. **Integration with address-space unmap paths.**
4. **Tests** — cross-core unmap visibility is immediate; stale TLB entries never observed after shootdown.

### Acceptance criteria

- ADR-0044 Accepted.
- Cross-core unmap is safely observable on all cores before the next memory access.

### Phase C closure

Business review. Phase D (Pi 4) or Phase D + E overlap becomes active.

---

## ADR ledger for Phase C

| ADR | Purpose | Expected state | Note |
|-----|---------|----------------|------|
| ADR-0040 | Secondary core start protocol | C1 | renumbered 2026-06-01 from ADR-0037 (ADR-0037 consumed by Phase B6 for EL0 entry context / T-023); was previously renumbered 2026-05-22 from ADR-0027 (collided with Accepted ADR-0027 kernel-virtual-memory-layout) |
| ADR-0041 | Per-core state access pattern | C2 | renumbered 2026-06-01 from ADR-0038 (ADR-0038 consumed by Phase B6 for `Mmu::translate` + user-access translation / T-025); was previously renumbered 2026-05-22 from ADR-0028 (collided with Accepted ADR-0028 address-space-data-structure) |
| ADR-0042 | Scheduler topology (preemptive) | C3 | renumbered 2026-06-01 from ADR-0039 (ADR-0039 consumed by Phase B6 for the userland build pipeline / T-027); was previously renumbered 2026-05-22 from ADR-0029 (collided with Accepted ADR-0029 initial-userspace-image-format) |
| ADR-0043 | Cross-core wakeup (IPI) | C4 | renumbered 2026-06-01 from ADR-0040; was renumbered 2026-05-22 from ADR-0030 (reserved by phase-b.md §B5 ledger for the syscall ABI) |
| ADR-0044 | TLB shootdown protocol | C5 | renumbered 2026-06-01 from ADR-0041; was renumbered 2026-05-22 from ADR-0031 (reserved by phase-b.md §B5 ledger for the initial syscall set) |

Numbers are tentative; final numbers are assigned when the ADR is actually written, per [ADR-0013](../../decisions/0013-roadmap-and-planning.md).

## Carry-forwards from Phase B (closed 2026-06-01)

Items identified during Phase B closure that survive into Phase C:

- **Object-lifecycle ADR (SEC-T024-01 / SEC-T028-01).** When a task exits, its capability slots and the objects they point to must be cleaned up correctly. The B6 security review (T-028 EL0-boundary + consolidated Phase-B seam) forward-flagged the exit path and pinned it as **SEC-T028-01**. An ADR and implementation task cover this; the slot is unallocated (first C-phase task that deals with task lifecycle will write it).
- **Per-section kernel-image permissions (ADR-0034).** B6 deferred this hardening step (`.text` RX / `.rodata` R / `.bss`+`.data` RW re-mapping at 4 KiB granularity). ADR-0034 is a named-but-unallocated placeholder (see [ADR index](../../decisions/README.md)); it opens with the first C-phase task whose threat model makes kernel W+X a meaningful surface.
- **EL0 fault containment (K3-4).** A non-`SVC` EL0 synchronous fault (illegal instruction, unmapped deref) currently halts the whole kernel; the syscall dispatcher itself is panic-free, but fault isolation requires a supervisor endpoint for the crashing task. Tracked as flag K3-4; targeted at Phase E (first real driver task), not Phase C.

## Open questions carried into Phase C

- Whether preemption is tick-driven or also includes manual preemption points (e.g., long-running kernel operations yielding).
- Whether per-core queues with work-stealing justify their complexity in v1 (global queue with locking may suffice).
- Real-time guarantees for the scheduler (probably "none beyond priority" in v1; richer RT is a later ADR).
- Whether ADR-0034 (per-section permissions) should land as C-phase hardening before or concurrently with C1, given that C3's preemption makes the kernel W+X surface larger.
