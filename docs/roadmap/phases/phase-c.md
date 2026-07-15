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

---

## Review-derived work items (2026-07-15 full-repository review)

The 2026-07-15 full-repository review examined the codebase at the Phase B/C boundary specifically through a concurrency/SMP-readiness lens. Every item below is grouped by which part of Phase C it gates or extends, cross-referencing Milestones C1-C5 and the existing "Carry-forwards from Phase B" list rather than restating their bodies. Severity tags: 🔴 critical · 🟠 high · 🟡 medium · ⚪ low · ⚫ info.

### 1. Entry gate — the two SMP-critical defects (must close before any secondary core boots)

These two findings block Milestone C1's first secondary-core boot outright: C2's `PerCore<T>` migration and C2/C3's frame-allocation work both implicitly assume neither defect still exists. Both are 🔴.

- 🔴 **`StaticCell`'s blanket `unsafe impl<T> Sync` erases all compiler protection against cross-core aliasing for every kernel global.**
  `bsp-qemu-virt/src/main.rs:161-170`.
  Action: before Milestone C1/C2 lands any secondary-core boot code, either (a) make `StaticCell<T>: Sync` conditional on a project-defined marker implemented only for types that are genuinely safe to share (this defeats the purpose for most of today's uses), or (b) replace every write-once-then-shared-mutable-access pattern with the `PerCore<T>` abstraction Milestone C2 already plans, wrapped where genuinely shared by the real spinlock / `Cpu::without_interrupts` primitive Milestone C3 introduces. Track this as an explicit **prerequisite gate on C1/C2**, not something C2's `PerCore<T>` work will pick up incidentally — every existing `assume_init_mut()` call site in `main.rs` / `perf_bench.rs` / `syscall.rs` needs to be re-audited and re-wrapped, not just the ones a first pass happens to touch.

- 🔴 **`Pmm` bitmap read-modify-write (`set_bit`/`clear_bit`) is non-atomic; concurrent `alloc_frame` on two cores can double-allocate the same physical frame.**
  `kernel/src/mm/pmm.rs:741-746` and `:348-486`.
  Action: (1) fix the misleading comment at `pmm.rs:450-453` now — it currently asserts a "set_bit atomicity" invariant the code does not provide, which is exactly the class of stale/incorrect SAFETY reasoning that causes real bugs later. (2) Before any Phase C code path can reach a shared `Pmm` from more than one core, wrap frame allocation in the Milestone C3 `Cpu::without_interrupts`-style spinlock, or convert the bitmap to `AtomicU8`/`AtomicUsize` fetch-or/fetch-and with `Ordering::AcqRel`. **Call-out: as written, none of C1-C5's sub-breakdowns name the physical frame allocator at all**, despite it being one of the two or three most safety-critical shared structures in the kernel — add an explicit "PMM concurrency" line item to Milestone C2 or C3's sub-breakdown before either lands.

### 2. Shared-state SMP-safety — concurrency contracts and locking discipline (ties to Milestone C1/C2)

Twenty-eight findings, all variations on the same theme the review's cross-cut/security section names directly: capability-table, arena, PMM, and per-core-identity code is soundness-justified almost entirely by "v1 is single-core," and that premise expires the moment C1 boots a second core.

**StaticCell audit & consolidation hygiene** (companions to Epic 1's `StaticCell` defect):

- 🟡 **Multiple `StaticCell` single-write publishes are audited under the wrong UNSAFE-2026 ID.**
  `bsp-qemu-virt/src/main.rs:1021,1026,1028,1045,1072,1091,1098,1363,1413,1531,1631` vs. `docs/audits/unsafe-log.md:14-25` and `:133-144`.
  Action: sweep every `Audit: UNSAFE-2026-0001` citation in `main.rs` and re-point the plain `StaticCell`-write sites (not `Pl011Uart` construction) to UNSAFE-2026-0010, or add an Amendment to 0001 explicitly folding in the `StaticCell`-write pattern — but not leave both entries silently overlapping without a documented reason.
- ⚪ **CI's Miri gate explicitly excludes the `bsp-qemu-virt` crate, so the `StaticCell` aliasing discipline underlying the Epic-1 defect has zero automated soundness verification.**
  `.github/workflows/ci.yml:224` (`cargo +$NIGHTLY_PIN miri test --workspace --exclude tyrne-bsp-qemu-virt`).
  Action: extract the `StaticCell` aliasing pattern itself (`UnsafeCell<MaybeUninit<T>>` + blanket `Sync` + `as_mut_ptr`/`assume_init_mut` discipline) into a small, no-asm, host-buildable module that CAN run under `cargo miri test` in isolation, so Miri's Stacked Borrows checker can catch the exact bug class Epic 1 describes before it manifests on real hardware.
- 🟡 **56 call sites in `bsp-qemu-virt` hand-inline the same unsafe `StaticCell` dereference instead of a shared accessor.**
  `bsp-qemu-virt/src/main.rs` (31 sites), `perf_bench.rs` (11), `syscall.rs` (11), `exceptions.rs` (1), `cpu.rs` (2).
  Action: add `unsafe fn get(&self) -> &T` / `unsafe fn get_mut(&mut self) -> &mut T` to `StaticCell<T>` with one comprehensive `# Safety` doc, and have call sites write `unsafe { CPU.get() }` with a one-line SAFETY comment referencing the type-level contract instead of re-deriving it 56 times. This does not weaken any check — every call site is still individually `unsafe {}` — it only consolidates the reasoning into one audited definition.

**Capability-table / Arena / Pmm concurrency contracts:**

- ⚪ **`ContextSwitch: Send + Sync` ships without the ADR revision note the project's own process requires for post-Accept drift.**
  `hal/src/context_switch.rs:32`.
  Action: add a short revision-note rider to ADR-0020 recording that the shipped `ContextSwitch` trait carries `: Send + Sync`, matching the precedent the ADR itself already set for the d8-d15 correction.
- ⚫ **`Iommu` is the only HAL trait in the crate without a `Send + Sync` supertrait bound.**
  `hal/src/lib.rs:62`.
  Action: change to `pub trait Iommu: Send + Sync {}` now, matching the crate-wide convention, so the pinning ADR for its real method surface starts from the already-correct bound.
- ⚪ **Generation counter still has no overflow/poisoning guard.**
  `kernel/src/cap/table.rs:642-654` (`free_slot`).
  Action: not a blocker — the ADR already accepts this for v1. As a cheap proactive step ahead of Phase C, reserve `Generation::MAX` as a permanent-poison sentinel: `free_slot` stops advancing past it and marks the slot permanently unallocatable; `pop_free` never returns a slot at the sentinel.
- ⚪ **`SyscallContext` hands out unsynchronized `&mut` references to cross-task shared kernel objects — will not survive Phase C SMP unchanged.**
  `kernel/src/syscall/dispatch.rs:78-111`.
  Action: per project rule 5, land an ADR now specifying the SMP synchronization strategy for the shared IPC objects (spinlock-guarded arena/queues, per-core partitioning, or a dedicated IPC-server core) before the first multi-core syscall path is implemented, so `SyscallContext`'s shape can be deliberately redesigned rather than retrofitted under time pressure.
- 🟡 **Context-switch anti-aliasing invariant (`current_idx != next_idx`) is enforced only by `debug_assert_ne!`, and the documented proof omits the "no slot reuse" premise it silently depends on.**
  `kernel/src/sched/mod.rs:686-689` (documented invariant), `:1179-1206` (`yield_now` switch window), `:1517-1548` (`ipc_recv_and_yield` switch window).
  Action: two fixes — (1) promote the aliasing check to an unconditional `assert!`, or make aliasing structurally unreachable by comparing `current_idx == next_idx` before taking raw-pointer references (mirroring the existing pattern at line 1462); (2) update the "Shared safety contract" (lines 686-689) and UNSAFE-2026-0008/0014 audit-log entries with an explicit Amendment stating the invariant's true precondition ("no live `TaskHandle` anywhere in `current`/`ready`/`idle` names a slot whose Arena generation has since advanced"), and add that precondition as an acceptance-criterion line item to the future task/slot-reclamation lifecycle ADR (SEC-T024-01's successor).
- ⚪ **`ipc_cancel_recv` authorizes on RECV-right possession, not on caller identity — a co-holder of a RECV cap on the same endpoint can silently cancel a different task's pending receive.**
  `kernel/src/ipc/mod.rs:563-580` (`fn ipc_cancel_recv`); `EndpointState::RecvWaiting` at `:195`; doc note at `:534-540`.
  Action: (1) add an explicit SECURITY doc-comment stating the load-bearing invariant that `ipc_cancel_recv` must only ever be invoked with the exact `ep_cap`/table pair that performed the matching `ipc_recv` (self-rollback only) — currently true by convention only. (2) Preferably, thread a lightweight caller/task token alongside `RecvWaiting` now and have `ipc_cancel_recv` verify it before clearing the slot. ADR-0032 §Consequences already earmarks this function for the B2+ endpoint-destroy "drain receivers" sweep and for preemption-rollback — exactly the kind of caller that could plausibly pass a different task's context if the invariant stays convention-only.
- 🟡 **`alloc_frame`'s wrap-around scan branch (the SMP-forward-compat path) has zero test coverage, and it is exactly the path Phase C is about to make reachable.**
  `kernel/src/mm/pmm.rs:383-390`.
  Action: since tests in this module already reach into private fields (`pmm.hint`, `pmm.bitmap`), add a targeted white-box test that directly sets `pmm.hint` above a known-free lower index and asserts `alloc_frame` still finds it via the wrap pass. Pins the wrap-scan's correctness independent of whether the "hint <= lowest-free" invariant continues to hold once Phase C introduces concurrent allocators.
- ⚪ **No documented SMP/locking discipline for `AddressSpaceArena` consumers ahead of Phase C.**
  `kernel/src/mm/address_space.rs:594-597, 653, 665-669` (repeated "single-core cooperative model" soundness arguments).
  Action: when Phase C work begins on this module, reframe these comments around "the caller must hold both `table` and `arena` under a single lock (or single `&mut` borrow) for the duration of the call" rather than "single-core." Add a short module-level "## Concurrency" doc section now, naming the exact invariant (whole-function atomicity across `table` + `arena` + `pmm`) a future spinlock wrapper must preserve.
- 🟡 **`security-model.md`'s "authority dropped on termination" invariant is not upheld by the current implementation, with no caveat noted in the doc.**
  `docs/architecture/security-model.md:301` vs. `kernel/src/sched/mod.rs:958-968` and `bsp-qemu-virt/src/syscall.rs:268-293`.
  Action: add a "v1 scope limitation" sub-bullet to the "Fault containment does not leak authority" invariant, mirroring the existing revocation-transitivity pattern, pointing at SEC-T024-01/SEC-T028-01 and stating precisely what is/isn't true today. Impact is currently contained (no second/attacker-controlled task exists to receive a reused slot), but this should land before Phase C or before any multi-task, task-creation-from-userspace feature makes slot/table reuse reachable.
- 🟡 **Every capability-table / IPC-state unsafe access is soundness-justified solely by "v1 is single-core" — no synchronization design exists ahead of Phase C.**
  `kernel/src/cap/table.rs` (whole file — no Sync/lock primitives); `kernel/src/ipc/mod.rs` (`EP_ARENA`/`IpcQueues`, no sync); `bsp-qemu-virt/src/syscall.rs:117-141`.
  Action: before Phase C lands any second-core dispatch, write the ADR the open-question list already calls for ("Revocation semantics under concurrent use") and decide the concrete model: per-core capability-table ownership, a global lock around `EP_ARENA`/`IpcQueues`, or per-core endpoint sharding. Treat the ~15+ "v1 is single-core" SAFETY comments as a checklist to re-audit item-by-item once that ADR is accepted.

**Per-core identity & boot topology (ties to Milestone C1/C2):**

- 🟡 **`IrqGuard` is unconditionally `Send` despite wrapping per-core, execution-context-affine interrupt-mask state.**
  `hal/src/cpu.rs:115-135`.
  Action: add a `_not_send: core::marker::PhantomData<*const ()>` field (or equivalent) so `IrqGuard` is statically `!Send`, matching its actual core-affine semantics. Land this now, before Phase C introduces the first code path that could plausibly move a guard across cores — zero-cost, purely additive, and much cheaper before any caller depends on `IrqGuard: Send`.
- 🟡 **`current_core_id()` derives `CoreId` from `MPIDR_EL1.Aff0` only, with no check that Aff1/Aff2/Aff3 are actually zero.**
  `bsp-qemu-virt/src/cpu.rs:226-239` (`Cpu::current_core_id`).
  Action: add a `debug_assert!((mpidr >> 8) & 0xFF_FFFF == 0, "...")` documenting and enforcing the flat-topology assumption, so a future multi-cluster configuration fails loudly instead of silently aliasing cores. Note in the comment what changes when GICv3 / >8 cores land.
- 🟡 **No per-core stack mechanism in `_start`/`linker.ld` — every core that ever executes `_start` gets the identical `sp = __stack_top`.**
  `bsp-qemu-virt/src/boot.s:104-107`; `bsp-qemu-virt/linker.ld:108-110`.
  Action: before Milestone C1's secondary-core bring-up lands, extend `_start` to read `MPIDR_EL1` (or accept a core index via PSCI `CPU_ON`'s context-id argument) and index into a per-core stack array sized `NUM_CORES * STACK_SIZE`, reserved in `linker.ld`. Design together with the MPIDR aff-checking fix above so both use the same affinity-to-index mapping.
- 🟡 **`CoreId` is a bare `u32` type alias, not a newtype — zero compile-time distinctness, and Phase C (SMP) is the very next phase.**
  `hal/src/cpu.rs:12`.
  Action: before Phase C lands any per-core state, convert `CoreId` to a proper newtype (`pub struct CoreId(pub u32);` at minimum, matching the project's `IrqNumber` pattern). Zero-runtime-cost, low-effort now (one alias, three call sites); progressively more expensive to retrofit once C2's per-core scheduler code threads `CoreId` through array indices, atomics, and IPI routing.

**Cross-core panic & fault propagation (ties to Milestone C4's IPI primitive):**

- 🟡 **Panic handler halts without masking interrupts, so an armed timer IRQ can still execute code after a panic.**
  `bsp-qemu-virt/src/main.rs:1666-1701` (`#[panic_handler] fn panic`).
  Action: as the very first action of the panic handler — before reconstructing the UART — mask all four DAIF bits (`asm!("msr daifset, #0xf")`, mirroring `boot.s`'s idiom). Guarantees the diagnostic UART write and final halt loop are truly atomic and that no ISR runs in a kernel state the panic may have left inconsistent.
- 🟡 **Panic handler halts only the panicking core; no cross-core halt/IPI exists, so surviving cores keep mutating shared kernel state a panic may have left inconsistent.**
  `bsp-qemu-virt/src/main.rs:1666-1701`.
  Action: not called out anywhere in phase-c.md's carry-forwards or milestones today. Add an explicit "cross-core panic propagation" requirement to **Milestone C4** (which already introduces the IPI primitive for cross-core wakeup) — reuse that mechanism to broadcast a halt-all-cores signal from the panic handler once IPI support exists. Fine until then (v1 is genuinely single-core), but flag it now so ADR-0043's IPI design accounts for a "halt everyone" message type, not just wakeup.
- ⚫ **EL0 non-SVC synchronous faults (illegal instruction, unmapped deref, alignment fault) halt the entire kernel via `panic_entry` — correctly tracked as K3-4/Phase E, but the SMP angle needs a documentation addendum.**
  `bsp-qemu-virt/src/vectors.s:60-77` (only `ESR_EL1.EC==SVC64` routes to dispatch); `bsp-qemu-virt/src/exceptions.rs:277-307` (`panic_entry`, unconditional `panic!`); `docs/roadmap/phases/phase-c.md:132` (K3-4 carry-forward).
  Action: no change needed to close this item — it is already correctly tracked and deliberately deferred to Phase E. One addendum worth adding to the existing K3-4 carry-forward note now: under SMP, a panic on one core currently has no defined story for signalling/halting the *other* cores (today's single-core `loop { spin_loop() }` halts everything by being the only core). When Milestone C1/C2 land, the K3-4 write-up (or ADR-0041 per-core state) should say explicitly whether a same-core EL0 fault still takes the whole machine down post-SMP, or is scoped sooner.

**Console / shared I/O state:**

- 🟡 **`FakeConsole`'s `Mutex` fully serializes writes, eliminating the byte-interleaving the `Console` contract permits and the real UART driver explicitly produces.**
  `test-hal/src/console.rs:8-11, 58-64`.
  Action: either (a) add an explicit doc caveat that `FakeConsole` cannot reproduce byte-level interleaving and should not be used to assert "no corruption under concurrency," or (b) add an opt-in interleaving-capable variant (e.g. `FakeConsole::new_interleaved()` that releases the lock between bytes) so Phase C multi-core tests can actually exercise and catch missing synchronization around console/logging call sites.
- ⚪ **`Console`/`Pl011Uart` writes are unsynchronized across cores by explicit design, accepted as "best-effort" — a real but consciously-scoped risk for Phase C debuggability.**
  `bsp-qemu-virt/src/console.rs:46-58` and `hal/src/console.rs:26-29`.
  Action: consider a minimal per-line spinlock (or a per-message length/sequence-number prefix) around `write_bytes`, specifically for the boot-banner and panic paths, once Milestone C1 brings up secondary cores. Debuggability quality-of-life only, not a correctness requirement given the trait's explicit contract.

**SMP-readiness testing debt:**

- ⚫ **`Scheduler<C>`'s single global `current`/`idle`/`ready`/`contexts` shape is the review's explicit SMP-readiness inventory item for the scheduler's core data layout.**
  `kernel/src/sched/mod.rs:249-330` (Scheduler fields) and `:772-799` (`register_idle`).
  Action: no action needed beyond what Milestones C2/C3 already plan. Recorded here to give the eventual ADR-0042 author a precise enumeration of exactly which `Scheduler<C>` fields need per-core partitioning vs. a shared lock (ready queue and `contexts` are natural lock-protected-shared or per-core-with-work-stealing candidates; `task_cap_tables`/`task_address_space_handles`/`task_user_windows` are read-mostly per-task metadata a `RwLock`-shaped primitive would suit).
- 🟡 **Coverage-percentage and Miri baseline reports have not been refreshed since 2026-04-27, despite ~2.5x test growth and entirely new subsystems landing.**
  `docs/analysis/reports/2026-04-27-coverage-rerun.md`; `docs/analysis/reports/2026-04-23-miri-validation.md`.
  Action: produce a fresh `docs/analysis/reports/<date>-coverage-post-phase-b.md` (and a paired Miri narrative update) now that Phase B is closed — reuse the existing template and per-file triage method. Establishes the coverage floor Phase C's SMP work will be measured against.
- 🟡 **Test harness (test-hal + kernel `#[cfg(test)]`) is entirely single-threaded; the raw-pointer scheduler/IPC aliasing discipline (ADR-0021) that Phase C's SMP work will directly stress has no multi-threaded test double.**
  `docs/analysis/reports/2026-04-23-miri-validation.md` ("What this does NOT validate" + "Next measurement"); `test-hal/src/cpu.rs` (`FakeCpu`, single-threaded); `kernel/src/sched/mod.rs:2558-2570` (`ResetQueuesCpu`'s `unsafe impl Send/Sync`, never exercised across a real thread).
  Action: before any Phase C PR lands cross-core scheduler/IPC/cap-table mutation, add a genuinely concurrent test-hal double (e.g. a `ThreadedCpu` running `context_switch` bodies via real `std::thread::spawn` + a barrier, or a loom-style model-checked harness) and re-run Miri/the aliasing tests under it. Track explicitly as a Phase C prerequisite, mirroring how ADR-0032's preemption forward-flags are tracked.
- ⚫ **`testing.md`'s "Layer 2: Integration tests" (per-crate `tests/` directory) is defined but entirely unused.**
  `docs/standards/testing.md:21-26`; workspace-wide `find -type d -name tests` returns no matches.
  Action: either (a) reconcile the doc — note that v1 satisfies the cross-module-contract goal via inline tests and that `tests/` is reserved for genuine cross-*crate* scenarios, or (b) start populating `kernel/tests/` with a true end-to-end scenario now that Phase C adds cross-crate SMP concerns inline unit tests are less suited to model.

**Address-space preflight-then-commit family (same remediation family; needs Milestone C3's lock primitive):**

- 🟡 **`cap_create_address_space`'s preflight-then-commit sequence is non-atomic across the whole function body, relying solely on "single-core cooperative" for correctness.**
  `kernel/src/mm/address_space.rs:586-603` and `:649-679`.
  Action: same remediation family as the Epic-1 `Pmm` finding — this function needs to run under whatever per-CPU-lock primitive Milestone C3's `Cpu::without_interrupts` establishes before any code path can call it from more than one core. Worth noting explicitly in ADR-0042 or a companion capability-subsystem note, since this "preflight then commit across N steps" pattern likely recurs elsewhere in the object layer.
- 🟡 **`task_loader.rs`'s `load_image` has the identical unlocked preflight-then-commit pattern as `cap_create_address_space`.**
  `kernel/src/obj/task_loader.rs:579-587` (frame-budget preflight) and the subsequent commit steps later in `load_image`'s body.
  Action: fold into the same remediation family as the finding above rather than a separate follow-up — both `cap_create_address_space` and `load_image` need to run under the Milestone C3 per-CPU-lock primitive before either can be called from more than one core concurrently. Name both call sites explicitly in the eventual capability-subsystem SMP-readiness ADR.

### 3. Preemption & TOCTOU (gates Milestone C3; extends into C4/C5)

- 🟠 **`ipc_send`'s `unreachable!()` is a self-documented ticking time bomb for Phase C preemption, and is not carried into the Phase C roadmap's tracked-items list.**
  `kernel/src/ipc/mod.rs:357-371` (the `unreachable!()` arm); cross-ref `docs/roadmap/phases/phase-b.md:287` (flags it as "later-phase, tracked"); `docs/roadmap/phases/phase-c.md:128-132` ("Carry-forwards from Phase B" — **omits it**).
  Action: two independent actions — (1) **add this item explicitly to this file's "Carry-forwards from Phase B" list**, alongside SEC-T028-01/ADR-0034/K3-4, so it cannot be lost between phase-closure documents; (2) land the fix the code itself already recommends (see finding directly below) as part of, or immediately before, Milestone C3, ideally pre-emptively rather than discovered via a crash under QEMU `-smp N` testing.
- 🟡 **`ipc_send`'s queue-full commit path panics via `unreachable!()` instead of erroring — cheap to defuse now.**
  `kernel/src/ipc/mod.rs:330-373`.
  Action: replace `unreachable!()` with `return Err(IpcError::QueueFull)` — a single-line, zero-risk change identical to what `ipc_recv` already does for its analogous state — rather than waiting for Milestone C3 preemption work to make the race live. `IpcError::QueueFull` and its `SyscallError` composition already exist and are already tested for the ordinary QueueFull path.
- 🟠 **`copy_from_user`/`copy_to_user`'s two-pass probe-then-copy is a TOCTOU window the moment address-space mutation can happen concurrently with a syscall.**
  `kernel/src/syscall/user_access.rs:198-249` and `:280-317`.
  Action: this is explicitly the concern **Milestone C5** (TLB shootdown) partially addresses, but C5's acceptance criteria ("cross-core unmap is safely observable on all cores before the next memory access") describe post-unmap visibility, not protection of an in-flight probe-then-copy window against a *concurrent* unmap. When C4/C5 land, either (a) re-translate-and-recheck per byte-run atomically with the unmap path (hold a per-AS lock across the whole copy, not just the probe), or (b) make unmap defer physical-frame reuse until an RCU-like grace period / IPI-synchronized quiescence, so a stale translation used mid-copy still points at valid (if logically-unmapped) memory. Flag explicitly in the ADR-0044 (TLB shootdown) design doc — this is narrower and more security-relevant than plain TLB staleness.
- ⚪ **`copy_from_user`/`copy_to_user`'s two-pass probe-then-copy correctness rests on an explicit single-core assumption with no test (or test harness) to catch a Phase C violation.**
  `kernel/src/syscall/user_access.rs:201-203, 238-241, 308-309` (SAFETY comments).
  Action: file this explicitly as a test-debt/forward-flag item (mirroring ADR-0032's preemption forward-flags) so whatever ADR introduces cross-core page-table mutation must either (a) prove single-writer-per-AS still holds under SMP, or (b) add a re-validation-on-copy (not just on-probe) discipline, with a test that models the race via test-hal (e.g. a decorator MMU that mutates a mapping between a probe and copy call) before Milestone C3's scheduler work ships.
- ⚪ **The file's single-core, DAIF-masked "no interleaving" soundness basis is not carried forward into the Phase C (SMP) plan.**
  `kernel/src/syscall/user_access.rs:236-241, 303-310`.
  Action: add this file's interleaving invariant as an explicit Phase C carry-forward item (alongside SEC-T028-01/ADR-0034/K3-4 in this file), or add a code-level forward marker pointing at ADR-0044, so whoever lands C3/C4/C5 is forced to re-examine and re-prove (or re-synchronize, via the TLB-shootdown protocol) this file's two-pass translate-then-copy design before SMP ships.
- ⚪ **Running-task syscall context is assembled from three separate, non-atomic scheduler reads.**
  `bsp-qemu-virt/src/syscall.rs:169-171`.
  Action: before Phase C introduces cross-core mutation of scheduler task-bindings, either add a single `Scheduler` accessor that returns all three pieces from one borrow of `current`, or add an explicit comment naming "no interleaving between these three reads" as a precondition to be re-verified when SMP scheduling design lands.
- ⚪ **Gate-#3 running-task context is exposed as three independently-read accessors, not a single atomic snapshot.**
  `kernel/src/sched/mod.rs:530-550` (`current_user_table` / `current_address_space_handle` / `current_user_window`).
  Action: add a single `Scheduler::current_syscall_context(&self) -> Option<(*mut CapabilityTable, AddressSpaceHandle, UserAccessWindow)>`-shaped accessor that reads `self.current` exactly once and returns all three, and have the BSP `syscall_entry` call that instead of the three separate methods. Closes the documented forward-flag at negligible cost today; same remediation family as the finding directly above (BSP-side vs. kernel-side of the same non-atomicity).
- ⚪ **Stale docstring in `vectors.s` claims "v1 has no userspace," contradicted by the project's shipped EL0 syscall boundary.**
  `bsp-qemu-virt/src/vectors.s:285-291` (`tyrne_unhandled_irq_trampoline` docstring).
  Action: update the comment to state the real, current invariant — an IRQ cannot currently be taken while at EL0 because `enter_el0` masks DAIF for the EL0 dispatch (cite ADR-0037 §Decision outcome) — and note that this trampoline must be replaced with a real EL0-aware IRQ path (saving `SP_EL0` at minimum) **before Milestone C3's preemptive EL0 lands**.
- 🟡 **SVC trampoline spills 11 GPRs the AAPCS64 ABI already guarantees preserved, on every single syscall.**
  `bsp-qemu-virt/src/vectors.s:206-211,245-250` (`tyrne_sync_trampoline`); `bsp-qemu-virt/src/syscall.rs:73-79` (`SyscallTrapFrame`).
  Action: trim `SyscallTrapFrame`/`tyrne_sync_trampoline` to the set that is *not* ABI-guaranteed: x0-x18, x30, plus SP_EL0/ELR_EL1/SPSR_EL1 — mirroring the IRQ trampoline's already-applied reasoning. Update the `#[repr(C)]` struct, its `size_of` guard, and doc comments (frame drops from 272 to ~184 bytes). Re-run the T-029 `perf-bench` build to confirm the round-trip cost drops. Relevant to Milestone C3 because a shorter, translate-once critical section is a tighter interrupt-latency bound once preemption is live; if a future preemptive-syscall design genuinely needs a complete register snapshot at this exact point, that should be re-justified by the ADR that introduces it.

### 4. Multi-core MMU / GIC / TLB (gates Milestone C5)

- 🟡 **TLBI mnemonics are local-PE-only, but comments and the unsafe-log audit entries claim (and rely on) cross-core broadcast semantics for future SMP.**
  `bsp-qemu-virt/src/mmu.rs:235, 403-408, 422, 432-434, 442`; `docs/audits/unsafe-log.md:480,486,490,492,514`.
  Action: switch the three call sites to the inner-shareable broadcast encodings (`tlbi vae1is, {reg}` / `tlbi vmalle1is` x2). The existing `dsb ish` immediately after each TLBI then correctly waits for the broadcast invalidation domain-wide, matching what the comments already claim. Update UNSAFE-2026-0023/0024's "Rejected alternatives"/"Invariants relied on" text to stop asserting no asm change is needed for SMP. This also simplifies **Milestone C5**: ARM's IS-suffixed TLBI gives hardware-broadcast invalidation for free within one inner-shareable domain, without requiring a software IPI-shootdown protocol for the common single-domain case.
- 🟡 **`Mmu::map`/`unmap`'s intermediate-table-allocation walk has no documented (or enforced) mutual-exclusion contract for concurrent callers on the same `AddressSpace`.**
  `bsp-qemu-virt/src/mmu.rs:575-634` (`walk_or_alloc_table`), `:491-560` (`walk_and_install_leaf`).
  Action: before Phase C's first SMP boot lands, (a) add an explicit "must not be called concurrently for the same `AddressSpace`; callers must hold a per-AddressSpace lock" clause to the `Mmu` trait doc-comment and to both functions' SAFETY sections now, and (b) introduce the actual per-`AddressSpace` lock at the kernel `cap_map`/`cap_unmap` layer (`kernel/src/mm/address_space.rs`) ahead of enabling a second core. Same class of latent, currently-invisible concurrency debt as the Pmm finding in Epic 1 — parallel in urgency, distinct in mechanism (data race on page-table mutation vs. missing cross-core cache invalidation).
- 🟡 **No secondary-core park guard: `_start` will race on every core the instant `-smp` is raised above 1.**
  `bsp-qemu-virt/src/boot.s:45-62` (whole `_start`, no MPIDR_EL1 check anywhere in the file).
  Action: add a cheap, permanent defensive guard at the very top of `_start` — read `MPIDR_EL1`, mask to AFF0 (bits 7:0), and if non-zero, `wfe`-park in a dedicated `secondary_park:` loop (mirroring the existing `halt_unsupported_el` pattern) instead of falling through. ~4 instructions; makes a future `-smp N>1` fail safe instead of racing, and gives **Milestone C1**'s PSCI `CPU_ON` work a natural place to wake secondaries later. Land now, independent of the Phase C SMP task, as forward-hardening.
- 🟡 **`QemuVirtGic::init()` conflates one-time distributor-wide programming with per-core CPU-interface bring-up.**
  `bsp-qemu-virt/src/gic.rs:153-247`.
  Action: before **Milestone C1** lands secondary-core start, split `init()` into `init_distributor()` (steps 1-6, called once by the primary core before any secondary comes up) and `init_cpu_interface()` (step 7, called by every core including the primary, once each). Small, low-risk refactor to do now (still single-core, zero behavioural change if the BSP calls both in sequence) that removes an obvious footgun for whoever writes the C1 secondary-core entry path.
- 🟡 **Entire timer-IRQ delivery path (trampoline round-trip, GIC acknowledge/EOI) has never actually fired in this codebase, as of "Phase B complete."**
  `bsp-qemu-virt/src/exceptions.rs:186-275` (`irq_entry`); no runtime caller of `arm_deadline` anywhere in the tree.
  Action: before or alongside Phase C work, add a minimal smoke path that actually exercises `irq_entry`'s timer arm — a boot-time `arm_deadline` call with a short deadline in the BSP demo, or a dedicated integration test asserting the demo observes the IRQ round-trip via a serial marker line. Converts the "Pending QEMU smoke verification" status in UNSAFE-2026-0019/0020/0021 into an actual pass and gives **Milestone C3**'s timer-tick wiring and **Milestone C4**'s IPI extensions a verified foundation to extend rather than an unverified one.
- ⚪ **`QemuVirtMmu::activate()`'s barrier order (ISB then DSB ISHST) is the reverse of the DSB-before-enable pattern used correctly elsewhere in the same file.**
  `bsp-qemu-virt/src/mmu.rs:227-243` (`Mmu::activate`).
  Action: reorder `activate()` to `dsb ishst` → `msr ttbr0_el1` → clear `EPD0` → `isb` → `tlbi vmalle1` → `dsb ish` → `isb`, matching `high_half_activate()`'s publish-before-enable shape, and cross-reference the two sites in a comment so a future editor who touches one updates the other. Robustness/consistency only — no runtime behaviour change today.
- ⚫ **`compiler_fence(SeqCst)` on the spurious-IRQ return path provides no actual guarantee and is labelled misleadingly as "defence-in-depth."**
  `bsp-qemu-virt/src/exceptions.rs:211-222`.
  Action: either remove the fence (it currently does nothing observable), or replace the comment with an honest note that a *future* SMP-visible write in this branch would need a real memory barrier (`core::sync::atomic::fence` backed by `dmb`, not just `compiler_fence`), not this one.

### Polish & excellence (SMP prep)

The 29 routed polish items are not defects; each is marked **Polish** and condensed into thematic groups without dropping any.

**HAL / BSP / aarch64:**

- **Polish** — Document the `Mmu` trait's concurrency contract ahead of Phase C: the trait's existing `Send + Sync` bound leaves the actual method-level safety obligation unstated.
- **Polish** — Build a consolidated "single-core assumptions" inventory: ~19 statics each individually document "single-core cooperative" as their soundness argument; one audit-ready inventory turns 19 scattered greps into a single SMP-transition checklist.
- **Polish** — Design fault isolation for non-SVC sync exceptions from EL0 before Phase C's multi-task/multi-core world makes a single-task fault routine rather than exceptional (touches P1/P2 in spirit).
- **Polish** — Make the SMP-broadcast TLBI change now, while cheap: no behaviour change for single-core v1 (IS-suffixed TLBI is a strict superset of local-only), high payoff for Milestone C5 planning.
- **Polish** — Split `QemuVirtGic::init()` into `init_distributor()`/`init_cpu_interface()` ahead of Milestone C1, even if `init()` stays a convenience wrapper for the still-single-core v1 boot path.
- **Polish** — Add a boot-time self-test that actually fires an IRQ through the trampoline before relying on the timer, converting UNSAFE-2026-0019/0020/0021's "Pending QEMU smoke verification" into an actual pass ahead of Milestone C3/C4.
- **Polish** — Expose `set_priority`/`set_target` on `QemuVirtGic` now, even if unused by v1, so Milestone C4's IPI-vs-device-IRQ priority and per-core SPI routing work lands as a consumer of an already-reviewed API.
- **Polish** — Log task identity and exit code on `task_exit` instead of a generic message — once Phase C brings concurrent tasks, a code-free exit message turns every multi-task failure into a guessing game.
- **Polish** — Bundle the fail-closed console-DoS and TOCTOU items into one pre-Phase-C hardening pass, resolved or explicitly accepted at Phase C kickoff per CLAUDE.md's phase-pause process.
- **Polish** — Signpost the local-vs-broadcast TLBI call sites for Phase C, keeping the well-tracked TODO discoverable where a future SMP author will look first.
- **Polish** — Land a trivial secondary-core park guard now, ahead of Phase C, converting "silent multi-core boot corruption during early Phase C spikes" into "secondaries park quietly."
- **Polish** — Consider a boot self-test/latch pattern for the handful of must-run-exactly-once routines, converting a future refactor mistake (e.g. SMP work accidentally calling `kernel_entry` per-core before the park guard lands) from silent page-table corruption into a loud, diagnosable panic.

**Kernel: capabilities & syscall:**

- **Polish** — State `CapabilityTable`'s concurrency contract explicitly on the type itself (not just in ADR-0021): "Not internally synchronized: every mutating method requires `&mut self`... Phase C's per-CPU or locked-table story will wrap this guarantee rather than change it."
- **Polish** — Cap `console_write`'s length and land the SMP synchronization ADR before Milestone C3's first multi-core syscall path, per rule 5.
- **Polish** — Fuse `copy_from_user`/`copy_to_user`'s probe-pass and copy-pass to translate each page once instead of twice, shortening the DAIF-masked critical section relevant once Milestone C3's `without_interrupts` discipline lands.
- **Polish** — Give `copy_from_user`/`copy_to_user` their own bounded-chunk discipline (not just `console_write`'s), so an unbounded interrupt-masked copy doesn't become a scheduling-latency outlier once Milestone C3's timer-tick preemption is live.
- **Polish** — Consider `clippy::indexing_slicing` (or equivalent) to close the one implicit-panic class the current lint set doesn't cover, proposed as its own small ADR/task rather than flipped on unilaterally, given a panic on one core is a bigger liveness problem under Phase C SMP than today.

**Kernel: IPC / objects / scheduler:**

- **Polish** — Document `Arena<T,N>`'s single-core contract explicitly in code (a `# Concurrency` module-doc section citing ADR-0016 §Open questions), and weigh an explicit `!Sync` marker in the future multi-core ADR so cross-core sharing must opt in via a deliberate wrapper.
- **Polish** — Close the gate-#3 non-atomicity forward-flag now, while free: one struct and one field read today vs. re-auditing every call site after preemption lands.

**Kernel: memory (PMM/address-space):**

- **Polish** — Formalize the Phase C (SMP) synchronization plan for `Pmm` before multi-core lands — an ADR amendment to ADR-0035 or a fresh ADR committing to global spinlock, `AtomicU8`/CAS bitmap words, or per-core free-list caches, turning the "SMP extension keeps this invariant via set_bit atomicity" comment into a discharged, implemented guarantee.
- **Polish** — Add a debug-only `Pmm` self-check that cross-verifies bitmap, `reserved_ranges`, and counters in one pass, paying for itself once SMP or capability-driven `MemoryRegionCap` grants mutate the PMM from more call sites.
- **Polish** — Add an atomic `cap_protect` primitive for permission transitions, letting future loader/JIT code implement true write-XOR-execute transitions without the fault-prone unmap/remap window, strengthening the W^X story ahead of ADR-0034.

**Test-HAL & userland:**

- **Polish** — Give `FakeMmuState` a per-core dimension ahead of Phase C (key `activated_root` and TLB logs by `CoreId`/thread-id), avoiding a scramble once the first multi-core scheduler test needs it.
- **Polish** — Give `FakeConsole` an interleaving-capable mode ahead of Phase C, so higher-level logging code's tolerance of non-atomic multi-byte console writes can be host-tested before it's tested for the first time on real hardware.
- **Polish** — Add a strict/gated acknowledge mode to `FakeIrqController`, so a missed `enable()` (silently-dead timer preemption) or a double-EOI (desynchronized interrupt priority state) becomes catchable pre-Phase-C rather than a live-hardware surprise.

**Cross-cut: concurrency/SMP:**

- **Polish** — Add an explicit "PMM / capability-table SMP audit" task to Milestone C2 or C3's sub-breakdown: "Audit and lock/atomic-ify `Pmm` and `CapabilityTable`/`AddressSpaceArena` for cross-core access," closing the gap between the roadmap and the concrete inventory this review produced.

**Cross-cut: quality/API/testing:**

- **Polish** — Encode `SyscallContext`'s "current task" as a structural `Option` rather than four independently-set fields plus a bool, since Phase C and any second BSP will add more construction sites where `has_current_task = true` could be set without a resolved `task_as`/`caller_table`.
- **Polish** — Publish a Phase-C-opening coverage + Miri baseline as the SMP-readiness gate, giving a clean before/after line for whatever coverage regressions (or improvements) Phase C introduces.

**Cross-cut: security:**

- **Polish** — Write the ADR for capability/IPC-state concurrency control before Phase C's first second-core dispatch, per rule 5/6, turning a standing open question every future unsafe block can cite into a concrete pre-Phase-C gate.

---

Covers all 46 review findings + 29 polish items routed to this phase.
