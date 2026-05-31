# Phase B — Real userspace

**Exit bar:** A userspace task (a real separate binary, not a kernel-level stub) runs in its own address space, with its own capability table, and can make syscalls back into the kernel.

**Exit-quality prerequisite — Miri.** Before Phase B is declared complete, **a green `cargo +nightly miri test` (Stacked Borrows) run over the host-test suite is a Phase-B exit prerequisite**, not merely a per-PR gate — with particular weight on `kernel/src/sched/**` and `kernel/src/ipc/**`, where the raw-pointer scheduler/IPC bridge trades the borrow checker's compile-time non-aliasing guarantee for the documented no-`&mut`-across-`context_switch` invariant (ADR-0021 / [UNSAFE-2026-0014](../../audits/unsafe-log.md)). Miri is the only mechanical verifier of that invariant; the 2026-04-21 security review made the aliasing discipline the #1 Phase-B blocker. The `miri` CI job is blocking-by-construction (no `continue-on-error`) per [`infrastructure.md` §"Miri as a blocking gate"](../../standards/infrastructure.md#miri-as-a-blocking-gate); this line records the milestone-exit requirement. (Closes master-review finding MR-009; recorded at B4 closure, 2026-05-28.)

**Scope:** Land the Phase A exit-hygiene fixes surfaced by the 2026-04-21 reviews, drop to EL1, activate the MMU with a kernel mapping, introduce per-task address spaces, build a task loader, define the syscall entry / dispatch, run the first userspace "hello world" in EL0. Still single-core; Pi 4 is Phase D; drivers are Phase E.

**Out of scope:** Multi-core, real hardware, userspace drivers, network, filesystem, cryptography.

**Source reviews informing this plan:**
- [Code review — Tyrne → Phase A exit](../../analysis/reviews/code-reviews/2026-04-21-tyrne-to-phase-a.md)
- [Security review — Tyrne → Phase A exit](../../analysis/reviews/security-reviews/2026-04-21-tyrne-to-phase-a.md)
- [A3–A6 business review / Phase A retrospective](../../analysis/reviews/business-reviews/2026-04-21-A6-completion.md)

Items flagged with 🚩 are decisions that must be settled during the named milestone before code lands. They are listed in the *Open questions* section as well, so nothing drops.

---

## Milestone B0 — Phase A exit hygiene

Cleans up the items the 2026-04-21 Phase-A code and security reviews surfaced. Every Phase-B capability that follows rides on top of the fixes here: preemption and SMP cannot start while `UNSAFE-2026-0012` (aliasing) is live; userspace cannot reach the scheduler while `ipc_recv_and_yield` can panic on deadlock; the subsystem architecture docs need to exist before external contributors navigate the code. B0 therefore runs **before** the EL-drop / MMU / syscall pipeline.

### Sub-breakdown

1. **ADR-0021 — Raw-pointer scheduler API.** Reshape `Scheduler::ipc_send_and_yield` / `Scheduler::ipc_recv_and_yield` so no `&mut` reference to `SCHED` / `EP_ARENA` / `IPC_QUEUES` / `TABLE_*` is live across the cooperative context switch. Resolves UNSAFE-2026-0012 (Security review §1 / §3 blocker #1).
2. **ADR-0022 — Idle task + typed `SchedError::Deadlock`.** Register a kernel idle task at boot so the ready queue is never empty; convert the `panic!("deadlock: …")` at [`kernel/src/sched/mod.rs:388-395`](../../../kernel/src/sched/mod.rs#L388-L395) to a typed error. Bundle: also convert `Scheduler::start`'s empty-queue panic at [sched/mod.rs:246-253](../../../kernel/src/sched/mod.rs#L246-L253) to `Err(SchedError::QueueEmpty)`; also harden the `debug_assert!` in the `ipc_recv_and_yield` resume path at [sched/mod.rs:417-421](../../../kernel/src/sched/mod.rs#L417-L421) to a release-mode `Err(...)`. Security review §4; code review §Correctness (Scheduler bullets 2, 4).
3. **ADR-0023 — Cross-table capability revocation policy.** Record the v1 single-table scope of the "Revocation is transitive" invariant (already qualified in [`docs/architecture/security-model.md`](../../architecture/security-model.md) by commit `de66d68`). 🚩 **Decision:** accept-deferred (option a; recommended — no code work, document the limitation and push cross-table CDT to Phase C) vs. implement-now (option b; substantial storage + IPC rewiring, only justified if a multi-task server appears in B3–B6 that needs post-transfer revocation).
4. **Architecture docs × 3** via the [`write-architecture-doc`](../../../.agents/skills/write-architecture-doc/SKILL.md) skill: `docs/architecture/kernel-objects.md` (ADR-0016 + Arena pattern), `docs/architecture/ipc.md` (ADR-0017 + ADR-0018 + state machine), `docs/architecture/scheduler.md` (ADR-0019 + ADR-0020 + IPC bridge + UNSAFE-2026-0008). Code review §Documentation follow-up #2.
5. **Timer initialisation** — populate `QemuVirtCpu`'s `Timer` trait impl with `CNTVCT_EL0` (virtual counter, register-family-aligned with the deferred `CNTV_*` deadline-arming registers per ADR-0010) and `CNTFRQ_EL0` reads; wire a free-running counter so IPC round-trip latency and context-switch overhead can be measured. Unlocks the first hypothesis-driven performance-review cycle (baseline at [`2026-04-21-A6-baseline.md`](../../analysis/reviews/performance-optimization-reviews/2026-04-21-A6-baseline.md) is blocked on this). *Note: the original phase-plan wording said "CNTPCT_EL0"; T-009 second-read review surfaced the register-family mismatch and switched to `CNTVCT_EL0`.*
6. **Scheduler / IPC hardening bundle.** Grouped in T-010 with ADR-0022's implementation:
   - `const { assert!(N > 0) }` on `SchedQueue::new` so zero-capacity constructions are a build-time error, matching `Arena::new`'s pattern. (`CapabilityTable` is not generic over its capacity, so it carries the analogous compile-time guard in a different form — `const { assert!(CAP_TABLE_CAPACITY <= Index::MAX) }` — rather than an `N > 0` assertion.)
   - `debug_assert_ne!(current_idx, next_idx)` before the split-borrow `unsafe` blocks in `yield_now` / `ipc_recv_and_yield` to catch regressions that stop dequeuing the running task.
   - Replace `debug_assert!` in the resume path with a hard `Err(SchedError::Ipc(...))` return (see item 2 above).
7. **`TaskArena` local → global StaticCell migration.** Bundled with T-006 (ADR-0021) to avoid two rounds of BSP static-cell churn. Brings `TaskArena` into the same reachability story as `EP_ARENA` / `TABLE_{A,B}` and satisfies the ADR-0016 "arenas belong to the kernel" framing. Post-A6 inline review feedback #15.
8. **Missing-tests bundle.** T-011 adds:
   - `IpcError::ReceiverTableFull` provoked + cap-retention assertion (code review §Test coverage).
   - Slot-reuse with a pending transfer cap in a destroyed endpoint (code review §Test coverage).
   - Once ADR-0022 lands, the `Scheduler::start` empty-queue and `ipc_recv_and_yield` deadlock should-panic tests are replaced by returns-Err tests.

### Acceptance criteria

- ✅ ADR-0021, ADR-0022 Accepted at B0 (ADR-0022 was later partially superseded by ADR-0026 in B1 on its *idle-task-location* axis only; the *typed-error* axis — `SchedError::Deadlock` — that B0 depends on still stands); ADR-0023 deferred (Phase B6+ revocation work; "accept-deferred" path per the original B0 plan).
- ✅ No `panic!(...)` remaining in `kernel/src/sched/mod.rs` reachable in production; the `start` / `start_prelude` "empty ready queue" panic survives as a kernel-programming-error guard rendered structurally unreachable by ADR-0022's idle-task-at-boot rule.
- ✅ `docs/audits/unsafe-log.md` UNSAFE-2026-0012 entry marked `Removed` with the resolution commit (`f9b72f8` — T-006 / ADR-0021).
- ✅ Two architecture docs committed (`scheduler.md` + `ipc.md`) with the `hal.md` Timer subsection update; linked from `docs/architecture/README.md` as Accepted. The originally-projected third doc was subsumed: `kernel-core.md` and `scheduling.md` were collapsed into `scheduler.md` + `ipc.md` per T-008's scope-discipline call.
- ✅ `QemuVirtCpu` implements `Timer`; IPC round-trip latency measurable via `CNTVCT_EL0` (virtual counter, register-family-aligned with the future deadline-arming `CNTV_*` registers per UNSAFE-2026-0015's first Amendment).
- ✅ 143 host tests green (130 → 143 via T-011's +13 tests; B0 final count exceeds the 109+ target by 31%).
- ✅ QEMU smoke still matches the A6 trace; T-013 added two more boot-path lines (DAIF mask + EL drop) without changing the kernel-entry trace.
- ✅ Phase-A security-review blocker #1 (UNSAFE-2026-0012) closed; #2 (cross-table revocation) deferred per ADR-0023's accept-deferred path; #3 (idle task + typed deadlock) closed in ADR-0022.

**Status: B0 closed 2026-04-27** with PR #9's merge to `main` (merge commit `9a66e8b`). All required tasks Done; T-010 (optional split) explicitly not opened. Phase-A exit hygiene complete.

### Tasks under B0

- [T-006 — Raw-pointer scheduler API refactor + TaskArena global migration](../../analysis/tasks/phase-b/T-006-raw-pointer-scheduler-api.md) — Done (2026-04-27)
- [T-007 — Idle task + typed `SchedError::Deadlock` + resume-path hardening](../../analysis/tasks/phase-b/T-007-idle-task-typed-deadlock.md) — Done (2026-04-27)
- [T-008 — Architecture docs (scheduler.md + ipc.md + hal.md/overview.md updates)](../../analysis/tasks/phase-b/T-008-architecture-docs.md) — Done (2026-04-27)
- [T-009 — Timer init + `CNTVCT_EL0` measurement](../../analysis/tasks/phase-b/T-009-timer-init-cntvct.md) — Done (2026-04-27)
- T-010 — (optional) Split of T-007 if ADR-0022 scope grows past one task *(not opened — T-007 closed without needing the split)*
- [T-011 — Missing tests bundle](../../analysis/tasks/phase-b/T-011-missing-tests-bundle.md) — Done (2026-04-27)

### Flags to resolve during B0

- 🚩 **Cross-table CDT (ADR-0023).** accept-deferred (preferred) vs. implement-now. Revisit if a multi-task server surfaces in B3–B6.
- 🚩 **`IpcError` split (K2-5).** Deferred from B0 into B5 so the full userspace-exposed error taxonomy is designed once. See open questions below.
- 🚩 **Architecture-doc scope.** Whether `docs/architecture/ipc.md` also covers notifications or a separate file later (notifications are A3-aware but v1 has no waiter list — the full semantics arrive with the first notification user).

### Informs

B1 / B2 / B3 all depend on a panic-free scheduler and a non-UB aliasing story. B5's syscall ABI design rides on the typed error pattern established by B0's hardening.

---

## Milestone B1 — Drop to EL1 in boot, install exception infrastructure

Extend the BSP reset stub so that when QEMU delivers us at EL2, we configure `HCR_EL2`, `SPSR_EL2`, `ELR_EL2`, and issue `ERET` to land in EL1. When QEMU delivers at EL1, the stub is a no-op on that axis.

The scope of this milestone was extended on 2026-04-27 (after T-009 — the time-source half of `Timer` — landed in `In Review`) to include the *exception delivery infrastructure* that ADR-0022's first-rider sub-rider gated on. Concretely: **GICv2 distributor + CPU interface** configuration on QEMU virt (GICv2 has no redistributor — that is GICv3 terminology; QEMU virt defaults to GICv2 unless `-machine gic-version=3` is set; this GICv2 / no-IOMMU reality was later ratified by [ADR-0036](../../decisions/0036-qemu-virt-gicv2-no-iommu-v1.md), which corrects the GICv3 / SMMUv3 statements in ADR-0004 / 0006 / 0012), an EL1 exception vector table install at `VBAR_EL1`, a thin handler-dispatch loop, and the generic-timer-IRQ wiring that lets `Timer::arm_deadline` and `Timer::cancel_deadline` actually fire interrupts. Without this work, `arm_deadline` / `cancel_deadline` remain `unimplemented!()` and idle's body cannot move from `spin_loop` to `wfi`.

### Sub-breakdown

1. ✅ **[ADR-0024](../../decisions/0024-el-drop-policy.md) — EL drop to EL1 policy** *(Accepted 2026-04-27)*. Settled choice: always drop to EL1 in `boot.s`, regardless of where firmware/emulator delivers the kernel. EL3 entry halts; VHE explicitly off.
2. ✅ **Asm extension** in `bsp-qemu-virt/src/boot.s` for EL2→EL1 transition — delivered by [T-013](../../analysis/tasks/phase-b/T-013-el-drop-to-el1.md) (Done 2026-04-27). **Bundle K3-12:** explicit `msr daifset, #0xf` at the top of `_start` is in place per the [BSP boot checklist](../../standards/bsp-boot-checklist.md) §1a update.
3. ✅ **Rust helper for reading current EL** — delivered by T-013 as `pub fn tyrne_hal::cpu::current_el() -> u8` (free function chosen per ADR-0024 §Open questions). UNSAFE-2026-0018 audits the helper; UNSAFE-2026-0016's T-013 Amendment records the load-bearing-post-condition shift now that `boot.s` actually drives EL1.
4. ✅ **Tests** — QEMU smoke at default config (EL1 entry) and at `-machine virtualization=on` (EL2 entry) both verified by the maintainer 2026-04-27 prior to PR #9 merge; identical trace post-`post_eret` confirms the EL drop's correctness on both paths.
5. ✅ **Exception infrastructure and interrupt delivery** *(Done 2026-04-28)* — delivered by [T-012](../../analysis/tasks/phase-b/T-012-exception-and-irq-infrastructure.md) across three implementation commits + one documentation sweep + two review-fix sweeps; promoted to `Done` via PR #10 merge to `main`. Closes the deferred halves of ADR-0010 (`Timer::arm_deadline` / `cancel_deadline` real on `QemuVirtCpu`) and ADR-0022 first rider's *Sub-rider* (idle's WFI activation; `idle_entry` body is now `wait_for_interrupt` + `yield_now`). Three new audit entries: UNSAFE-2026-0019 (GIC v2 MMIO), UNSAFE-2026-0020 (vector table + asm trampolines), UNSAFE-2026-0021 (CNTV_CTL/CVAL writes). UNSAFE-2026-0014 gains an Amendment naming `irq_entry` as a future site of the same momentary-`&mut` pattern; ADR-0021 §Revision notes gains the 2026-04-28 Amendment extending the no-`&mut`-across-switch rule to the IRQ frame. v1's `irq_entry` is *ack-and-ignore* — masks `CNTV_CTL_EL0` + EOIs the GIC + returns; no scheduler-state mutation today. Future scheduler-touching arcs (preemption, `time_sleep_until` wake) follow the ADR-0021 Amendment's discipline. T-012 did not split into T-012a / T-012b; the substantive arc landed as one task. Maintainer-side QEMU smoke + Miri pass remain pending per the same disclaimer T-013 used; the audit-log "Pending QEMU smoke verification" status notes on UNSAFE-2026-0019 / 0020 / 0021 stay until the maintainer has actually run the smoke, then lift via append-only Amendment.

### Acceptance criteria

- ADR-0024 Accepted.
- Kernel boots at EL1 in all QEMU configurations we care about.
- Smoke test boots both QEMU variants and asserts the greeting still appears.
- `boot.s` starts with explicit IRQ masking.
- BSP boot checklist updated with the "mask DAIF before anything else" rule.
- **T-012 delivered (Done 2026-04-28):** `arm_deadline` fires real IRQs through the GIC; `idle_entry`'s body is `wait_for_interrupt` + `yield_now` (closing ADR-0022's first rider in full). Promoted to `Done` via PR #10 merge to `main`. Maintainer-side QEMU smoke verification of the deliberate-deadline path + `cargo +nightly miri test` remain explicitly pinned for the maintainer's CI / hardware run; audit-log entries UNSAFE-2026-0019 / 0020 / 0021 keep their "Pending QEMU smoke verification" status notes until the maintainer lifts them via append-only Amendment.

**Status: B1 implementation complete 2026-04-28** with PR #10's merge to `main` (merge commit `7b42bbe`). T-013 (EL drop) Done 2026-04-27 via PR #9; T-012 (exception infrastructure + IRQ delivery + idle WFI) Done 2026-04-28 via PR #10. **B1 closure review trio landed 2026-04-28** via PR #11 — [business retrospective](../../analysis/reviews/business-reviews/2026-04-28-B1-closure.md), [consolidated security review](../../analysis/reviews/security-reviews/2026-04-28-B1-closure.md), [performance baseline](../../analysis/reviews/performance-optimization-reviews/2026-04-28-B1-closure.md). The only items still pending before B1 flips to milestone-level `Done` are **maintainer-side QEMU smoke verification** and **`cargo +nightly miri test` pass** on the R6 CI skeleton; both lift the `Pending QEMU smoke verification` status notes on UNSAFE-2026-0019 / 0020 / 0021 via append-only Amendment after they run.

**Status update (2026-05-06): B1 implementation reopened.** First end-to-end QEMU smoke at HEAD `214052d` surfaced an idle-dispatch regression inherited unmodified from T-007 (B0) through ADR-0022 Option A. The kernel hangs in `WFI` after `task_a`'s `ipc_send_and_yield` because the FIFO ready queue dispatches idle (which sat at the queue head from the previous round) instead of the just-unblocked `task_b`. v1's demo never arms a deadline, so no IRQ fires. Diagnosed via [`-d exec`](../../analysis/reviews/business-reviews/2026-05-06-B1-smoke-regression.md) trace; fix arc tracked in:

6. ✅ **[ADR-0026 — Idle dispatch via separate fallback slot](../../decisions/0026-idle-dispatch-fallback.md)** *(Accepted 2026-05-06)*. Supersedes ADR-0022's *idle-task-location* axis only (Option A → Option B); typed-error axis stands. Repurposes the previously-reserved-but-unused ADR-0026 slot.
7. ✅ **[T-014 — Idle dispatch via separate fallback slot](../../analysis/tasks/phase-b/T-014-idle-dispatch-fallback.md)** *(Done 2026-05-07)*. Refactored `Scheduler<C>` to add `idle: Option<TaskHandle>` field + `register_idle` raw-pointer free fn; updated dispatch sites (`start_prelude`, `yield_now`, `ipc_recv_and_yield`) to consult `idle` only when ready queue is empty; updated `bsp-qemu-virt::kernel_entry` to call `register_idle`. **Verification — 152 host tests + 152 miri all green; QEMU smoke produces the full demo trace** through `tyrne: all tasks complete` plus the boot-to-end timing line (~5.5–6.5 ms typical). UNSAFE-2026-0014 gained its third Amendment naming `register_idle` as the new sanctioned site. UNSAFE-2026-0019 / 0020 gained 2026-05-06 *partial-verification* + *post-T-014 smoke* Amendments noting that the setup sites are now confirmed under sustained execution but the IRQ-take/dispatch path itself remains unexercised by the v1 demo. UNSAFE-2026-0021 unchanged (demo still doesn't arm any deadline). Promoted to `Done` 2026-05-07 with the [B1 closure trio](../../analysis/reviews/business-reviews/2026-05-07-B1-closure.md).

**Status: B1 closed 2026-05-07.** All three implementation tasks Done: T-013 + T-012 + T-014. Closure trio (business + consolidated security + performance) is the canonical source for B1's closing metrics — see [`2026-05-07-B1-closure.md`](../../analysis/reviews/business-reviews/2026-05-07-B1-closure.md) (business retro is the entry point; security + performance are linked from there). The 2026-04-28 trio remains as historical record of what was believed at PR #10 merge. Audit-log entries UNSAFE-2026-0019 / 0020 / 0021 retain `Pending QEMU smoke verification` notes for the IRQ-dispatch path until a future task arms a real `arm_deadline`. **B2-prep follow-on T-015 (ADR-0032 / `ipc_cancel_recv`) Done 2026-05-07** in PR #17 — symmetric scheduler+endpoint rollback on `SchedError::Deadlock`, 158/158 host tests + miri clean immediately post-T-015 (159/159 post-PR-#18 hygiene; PR #18 added one more regression test for the `RecvComplete` no-op branch), smoke trace byte-for-byte unchanged from post-T-014 baseline. B2 prep (ADR-0027 kernel virtual memory layout) is now the active implementation thread.

---

## Milestone B2 — MMU activation (kernel-half mapping)

Turn on the MMU with an identity map for the kernel image region and its stack. This is the foundation that per-task address spaces will layer atop.

**Status: B2 Closed 2026-05-09** via [the closure-trio](../../analysis/reviews/business-reviews/2026-05-09-B2-closure.md) ([business retro](../../analysis/reviews/business-reviews/2026-05-09-B2-closure.md) + [security review](../../analysis/reviews/security-reviews/2026-05-09-B2-closure.md) + [performance baseline](../../analysis/reviews/performance-optimization-reviews/2026-05-09-B2-closure.md)). ADR-0027 `Accepted` 2026-05-08; T-016 (MMU activation) `Done` 2026-05-08 (PR #23 merged 2026-05-09). The closure-trio confirms: 185/185 host + miri clean; release ELF `.text 22,384` (+364 vs post-T-015) / `.bss 40,208` (+17,952; dominantly the 16 KiB `.boot_pt` reservation); release-build harness band p10/p50/p90 = 4.262/4.642/6.456 ms (the first release-codegen baseline-of-record); UNSAFE-2026-0022 / 0023 / 0024 / 0025 introduced with bootstrap-Amendments + 2026-05-09 smoke-verification Amendments; smoke-trace adds exactly one new `tyrne: mmu activated` line (every other line byte-stable). **Carry-forward (post-closure):** UNSAFE-2026-0019 / 0020 / 0021 retain `Pending QEMU smoke verification` for the IRQ-take / dispatch path (gates on first deadline-arming caller); UNSAFE-2026-0025 gains a similar status note (gates on first B3+ post-bootstrap `Mmu::map` caller); pre-existing PL011 "data written to disabled UART" guest-errors noise queued as a follow-on B-phase BSP task. **Original status text (preserved as historical record):** [ADR-0027](../../decisions/0027-kernel-virtual-memory-layout.md) committed to identity-only mapping in B2 (kernel in `TTBR0_EL1`; `TTBR1_EL1` reserved for future high-half ADR-0033 placeholder), MAIR indices 0/1 for device-nGnRnE / normal-cached, four bootstrap page-table frames in `.boot_pt`, and the typed [`MapperFlush`](../../../hal/src/mmu/mod.rs) flush-token discipline at the `Mmu` trait surface (additive change to `map`/`unmap` return types). Companion [`docs/architecture/memory-management.md`](../../architecture/memory-management.md) landed in the same PR. ADR-0027 is the **first non-recovery-primitive state-machine ADR drafted under [`write-adr` skill §Simulation](../../../.agents/skills/write-adr/SKILL.md) discipline** (ADR-0026 was the retro-source; ADR-0032 was the first application but its subject is a recovery primitive). Accept landed as a separate commit per `write-adr` §10. T-016 implementation lands across six independently-bisectable commits; smoke trace gains a single new line (`tyrne: mmu activated`) and is otherwise byte-stable. UNSAFE-2026-0022 / 0023 / 0024 / 0025 introduced; UNSAFE-2026-0023 / 0024 each carry an Amendment block recording the bootstrap-site scope extension.

### Sub-breakdown

1. ✅ **[ADR-0027 — Kernel virtual memory layout](../../decisions/0027-kernel-virtual-memory-layout.md)** *(Accepted 2026-05-08; Propose + careful-re-read separate-commit pair per [`write-adr` skill §10](../../../.agents/skills/write-adr/SKILL.md))*. Settled choice: identity-only mapping in B2 (`TTBR0_EL1` carries the kernel; `TTBR1_EL1` reserved with `EPD1=1` for future high-half ADR-0033 placeholder); 4 KiB granule + 48-bit VA + 4-level translation; MAIR indices 0 (device-nGnRnE) and 1 (normal-cached, write-back, write-allocate, inner+outer shareable); four bootstrap page-table frames in `.boot_pt` (statically reserved, pre-zeroed by the BSS-zero loop); typed [`MapperFlush`](../../../hal/src/mmu/mod.rs) flush-token discipline (additive `Result<MapperFlush, MmuError>` return type for `Mmu::map` / `unmap`). Includes the §Simulation table walking the SCTLR.M=1 transition end-to-end — first ADR to apply the rule forward.
2. ✅ **[T-016 — MMU activation with identity-mapped kernel + `MapperFlush` token discipline](../../analysis/tasks/phase-b/T-016-mmu-activation.md)** *(Done 2026-05-08; six bisectable commits on branch `t-016-mmu-activation`)*. Bundled task (mirrors T-012 shape) covering: HAL `MapperFlush` token + ADR-0009 §Revision rider; pure VMSAv8 descriptor encoders in [`tyrne_hal::mmu::vmsav8`](../../../hal/src/mmu/vmsav8.rs) (host-tested); `QemuVirtMmu` impl in [`bsp-qemu-virt/src/mmu.rs`](../../../bsp-qemu-virt/src/mmu.rs); `linker.ld` `.boot_pt` reservation; `mmu_bootstrap` Rust routine in [`bsp-qemu-virt/src/mmu_bootstrap.rs`](../../../bsp-qemu-virt/src/mmu_bootstrap.rs); `kernel_entry` wiring; four audit-log entries (UNSAFE-2026-0022 through 0025) + Amendments to 0023/0024 for bootstrap-site scope extension; cross-references to [`docs/architecture/memory-management.md`](../../architecture/memory-management.md) verified byte-stable. Smoke trace gained one new `tyrne: mmu activated` line; every other line byte-stable from post-T-015 baseline. Host tests: 182/182 (was 159 — +12 vmsav8 + 6 MapperFlush + 5 round-trip-update).
3. **Initial page-table construction (covered by T-016).** Bootstrap-time identity-mapping of kernel image + RAM range (128 MiB at 0x4000_0000..0x4800_0000) + MMIO range (GIC + UART at 0x0800_0000..0x0902_0000); 2 MiB block descriptors at L2 keep the bootstrap to four page-table frames. Finer-grained per-section permissions (`.text` RX vs `.rodata` R vs `.bss/.data` RW) await a follow-on B-phase task that re-maps the kernel-image region into 4 KiB pages with section-specific flags — out of scope for T-016.
4. **MMU activation sequence (covered by T-016).** Exact `MAIR_EL1` / `TCR_EL1` / `TTBR0_EL1` / `TTBR1_EL1` / `SCTLR_EL1` writes per ADR-0027 §Decision outcome (a) + §Simulation. TLB + I-cache invalidate + barrier sequence (`TLBI VMALLE1; DSB ISH; IC IALLU; DSB ISH; ISB; SCTLR_EL1.{M,I,C} = 1; ISB`) lands as audit-tag UNSAFE-2026-0024.
5. **Physical frame allocator (PMM) — separate B-phase task (post-T-016).** v1's bootstrap uses static reservation in `.boot_pt`; a real PMM is needed before the kernel calls `Mmu::map` for runtime mappings. The HAL trait's `&mut dyn FrameProvider` parameter is PMM-ready today; the kernel just doesn't have a PMM caller yet. T-NNN slot opens when first runtime map call surfaces.
6. **Physical-frame capability (`MemoryRegionCap`) first real use — separate B-phase task.** Wires the capability system to actual memory; exercises `MappingFlags::USER` (encoded correctly by `QemuVirtMmu` per T-016 host tests, but unused in v1).
7. **Deliberate-trap routing through exception vectors — separate B-phase task.** Page-fault routing into the capability system; depends on the syscall ABI (ADR-0030, B5).

### Acceptance criteria

- ADR-0027 Accepted (separate Accept commit per [`write-adr` skill §10](../../../.agents/skills/write-adr/SKILL.md)).
- T-016 Done: kernel runs with the MMU on; identity-mapped kernel + RAM + MMIO; `MapperFlush` token discipline at the `Mmu` trait surface; UNSAFE-2026-0022 through 0025 audit entries land with full Operation / Invariants / Rejected-alternatives shape.
- Smoke trace gains exactly one new line (`tyrne: mmu activated`); otherwise byte-stable; `-d int,unimp,guest_errors` empty.
- (Subsequent B2 tasks, separate from T-016) Physical frame allocator has host-tested correctness and a QEMU integration smoke; `MemoryRegionCap` first real use; deliberate traps route through the exception-vector table.

### Flags to resolve during B2

- 🚩 **Generation wrap (K3-1).** Does `MemoryRegionCap` slot churn plausibly reach `2^32` free-reuse cycles on a single slot? If yes, widen generation to `u64` or switch to a monotonic system-wide counter (write a successor ADR); if no, document the bound and move on. Decide while `MemoryRegionCap` is being wired.

### Informs

B3 builds per-task address spaces on top of this. B5 (syscall trap) reuses the exception-vector work.

---

## Milestone B3 — Address space abstraction

Multiple per-task translation tables. Capability-gated map / unmap. Activation on context switch (tie-in to A5's context switch, now post-B0 with raw-pointer scheduler API).

**Status: B3 Closed 2026-05-14** via PR #29's closure trio (business + security + performance baseline; merge commit `b425dc1`). B3 §1 closed 2026-05-10 (T-017 PMM); B3 §§2–7 closed 2026-05-11 (T-018 AddressSpace kernel object). [ADR-0035](../../decisions/0035-physical-memory-manager.md) settles the PMM design (bitmap allocator with hint pointer, 4 KiB metadata for QEMU virt's 32 K frames, reservation-list at init); T-017 implements it. [ADR-0028](../../decisions/0028-address-space-data-structure.md) settles the AddressSpace data-structure (Option A — generic `AddressSpace<M: Mmu>` wrapping `M::AddressSpace` inline; per-type arena); T-018 implements the kernel object + cap-gated wrappers + activation hook in 6 bisectable commits.

### Sub-breakdown

1. ✅ **ADR-0035 — Physical Memory Manager (bitmap allocator).** B3 prerequisite. Settles allocation discipline + reservation tracking + `FrameProvider` impl shape. Includes the §Simulation table walking init / alloc / free / exhaustion / recovery state transitions. Forward-portable to high-half kernel (ADR-0033 placeholder) without algorithm rewrite. *Accepted 2026-05-09 (Propose + careful-re-read separate-commit pair per [`write-adr` skill §10](../../../.agents/skills/write-adr/SKILL.md)).*
2. ✅ **ADR-0028 — Address-space data structure.** How a BSP-specific `AddressSpace` is represented; who owns its page tables; how it integrates with the `Mmu` trait's associated type. **Sits above ADR-0035** — consumes PMM frames for the root translation table + intermediate L1/L2/L3 frames via [`Mmu::map`](../../../hal/src/mmu/mod.rs)'s `&mut dyn FrameProvider`. *Accepted 2026-05-11 via PR #27.*
3. ✅ **`AddressSpace` kernel object** — a new kernel-object type, like those from A3, with `AddressSpaceCap`. *T-018 commits 1-2 (2026-05-11).*
4. ✅ **Map / unmap operations** — wrappers around [`Mmu::map`](../../../hal/src/mmu/mod.rs) / `Mmu::unmap` that validate the caller's capabilities. *T-018 commit 3 (2026-05-11) — `cap_create_address_space` / `cap_map` / `cap_unmap`.*
5. ✅ **TLB invalidation on unmap** — single-core only; multi-core is Phase C. **Already implemented** in [T-016](../../analysis/tasks/phase-b/T-016-mmu-activation.md) at the HAL surface (`MapperFlush::flush(&mmu)` discharges the per-VA invalidate); B3 §4 wires this into the capability-gated unmap path. *T-018 commit 3 (`cap_unmap` discharges the flush token).*
6. ✅ **Activation on context switch** — the context-switch path invokes [`Mmu::activate`](../../../hal/src/mmu/mod.rs) when crossing between tasks with different address spaces. *T-018 commit 4 (scheduler-side hook) + commit 5 (BSP-side activation closure). v1 demo: all tasks share `BOOTSTRAP_ADDRESS_SPACE_HANDLE`; hook short-circuits at runtime; host tests pin the fire path.*
7. ✅ **Tests** — address-space isolation (each `AddressSpace` gets a distinct arena slot + root and its own per-handle mapping store; the cross-AS "AS-X cannot read AS-Y" guarantee is the QEMU acceptance criterion below, verified *structurally* in the host tests rather than by a single named cross-visibility assertion); activation round-trip. *T-018 host tests in `kernel/src/mm/address_space.rs::tests` (17 at T-018 landing; 22 at HEAD after master-review remediation) + scheduler activation-hook tests (3 tests). Workspace total 221/221 at the 2026-05-11 landing snapshot.*

### Tasks under B3

- [T-017 — Physical Memory Manager (PMM): bitmap allocator + reservation tracking + `FrameProvider` impl](../../analysis/tasks/phase-b/T-017-physical-memory-manager.md) — Done (2026-05-10; 4 bisectable commits on branch `t-017-physical-memory-manager`; UNSAFE-2026-0026 introduced as new entry)
- [T-018 — `AddressSpace` kernel object + capability-gated `Mmu::map`/`unmap` wrappers + activation-on-context-switch](../../analysis/tasks/phase-b/T-018-address-space-kernel-object.md) — Done (2026-05-11; 6 bisectable commits on branch `t-018-address-space-kernel-object`; zero new unsafe audit entries — UNSAFE-2026-0014 umbrella gained a scope-extension Amendment for the activation hook + BSP-side closure)

### Acceptance criteria

- ADR-0035 Accepted; ADR-0028 Accepted.
- T-017 Done: PMM live; bitmap allocator; reservation list at init; `FrameProvider` impl; smoke trace gains `tyrne: pmm initialized (...)` line.
- T-018 Done: two address spaces coexist; the kernel activates each when its owning task runs.
- Isolation verified on QEMU: AS-X cannot read AS-Y's data.

### Flags to resolve during B3

- 🚩 **Cross-table revocation — revisit.** If ADR-0023 was accept-deferred in B0, B3 is the point where a two-task-with-shared-endpoint scenario becomes concrete. If the limitation bites any specific B3 test, promote cross-table CDT to B4 or B5; otherwise confirm the deferral holds through to Phase C.

---

## Milestone B4 — Task loader

Load a userspace binary into an address space. For B4 the binary is statically embedded in the kernel image (e.g., `include_bytes!`); the filesystem / dynamic loading comes later.

**Status: B4 Closed 2026-05-28** via the closure trio ([business retrospective](../../analysis/reviews/business-reviews/2026-05-28-B4-closure.md) + [security review](../../analysis/reviews/security-reviews/2026-05-28-B4-closure.md) (Approve) + [performance baseline](../../analysis/reviews/performance-optimization-reviews/2026-05-28-B4-closure.md)), which is the canonical source for B4's closing metrics. ADR-0029 Accepted; T-019 (task loader) merged to `main` 2026-05-16 (PR #31). The §Sub-breakdown / §Acceptance-criteria / §Revision-notes below stand as the design record; the past-tense framing reflects that the implementation has landed.

### Sub-breakdown

1. ✅ **[ADR-0029 — Initial userspace image format](../../decisions/0029-initial-userspace-image-format.md)** *(Accepted)*. Raw flat binary vs. minimal ELF subset. v1 favoured raw flat (simplest).
2. ✅ **Loader** — maps the embedded binary into a fresh address space via `cap_create_address_space` + `cap_map` (the AddressSpace cap surface from [ADR-0028](../../decisions/0028-address-space-data-structure.md)), sets up the initial stack, marks the entry point. The `MemoryRegionCap` shape for per-frame ownership tracking is **deferred to B5+** per the [B3 closure §Adjustments](../../analysis/reviews/business-reviews/2026-05-14-B3-closure.md#adjustments); v1's loader operates with kernel-mode authority through the AS cap and accepts the rollback-leaks-frames v1 baseline T-019 documents.
3. **Task creation from a binary** — `task_create_from_image(image, as_cap, initial_caps) -> TaskCap`. *Deferred to B5/B6 per the §Revision notes below; T-019 delivered the `LoadedImage` metadata struct half.*
4. ✅ **Tests** — host-side loader correctness (given an image blob, produce the expected mapping); QEMU-side task creation without yet running the task (that's B6).

### Acceptance criteria

- ✅ ADR-0029 Accepted.
- ✅ A kernel test loads the embedded userspace image into an address space and reports the entry point and initial stack pointer (the `LoadedImage` shape — see §Revision notes).

### Revision notes

- **2026-05-14 — `LoadedImage` / `task_create_from_image` split.** During the ADR-0029 propose + T-019 Draft cycle, the pre-Accept review surfaced that the §Sub-breakdown §3 wording (`task_create_from_image(image, as_cap, initial_caps) -> TaskCap`) overreaches what is achievable in B4 alone. The current `Task` struct ([`kernel/src/obj/task.rs`](../../../kernel/src/obj/task.rs)) carries only `id + address_space_handle` — no PC/SP context register file; `ContextSwitch::init_context` requires a stable entry-point function pointer + kernel-stack backing that userspace doesn't have until B5+ introduces EL0 entry. Beyond context shape, the loader's new AS contains only image + stack mappings — **no kernel mappings**, so any EL1 exception taken while the AS is active translation-faults on the vector fetch (the ADR-0033 high-half placeholder, gated on B5's per-task TTBR0 swap, addresses this). Accordingly: B4's load-bearing deliverable is now a [`LoadedImage` metadata struct](../../analysis/tasks/phase-b/T-019-task-loader.md) (`{ as_cap, entry_va, stack_top_va, image_bytes, stack_bytes }`); the `task_create_from_image` wrapper that turns it into a runnable `CapHandle{CapObject::Task(...)}` lands with B5 or B6 after kernel-mapping-in-userspace-AS + EL0 context-init + syscall ABI prerequisites are in place. The §Acceptance criteria above ("report the entry point and initial stack pointer") is exactly the `LoadedImage` shape; only the §Sub-breakdown §3 wording overreached. No structural change to B4's scope; the §Sub-breakdown §3 entry stays for forward-reference clarity but should be read as "the `task_create_from_image` surface lands incrementally across B4 → B6, not in T-019 alone".

---

## Milestone B5 — Syscall boundary

Traps from EL0 into EL1 via `SVC` (or the chosen mechanism). Syscall dispatch validates the caller's capabilities. Establish the initial syscall set and the calling convention.

**Status (2026-05-29): CLOSED via the closure trio.** B5 (syscall boundary) is formally **Closed** — [security review](../../analysis/reviews/security-reviews/2026-05-29-B5-syscall-boundary.md) (**Approve**, eight axes) + [business retrospective](../../analysis/reviews/business-reviews/2026-05-29-B5-closure.md) + [performance baseline](../../analysis/reviews/performance-optimization-reviews/2026-05-29-B5-closure.md), the **canonical source for B5's closing metrics** (339 host tests incl. local Miri 0 UB; release band p10/p50/p90 = 17.645/20.300/24.706 ms — a same-host control proves a real ~+2.9 ms one-time boot `SVC`-smoke cost, not host jitter; audit log 30 entries / 29 Active; QEMU smoke clean + 2 expected `SVC` exceptions, zero new fault class). T-020 + T-021 merged via [PR #34](https://github.com/HodeTech/Tyrne/pull/34) (`f98e1af`). **The real EL0 `+0x400` round-trip + the three T-021 carry-forward gates are carried to B6** (the §B6 acceptance criteria + "T-021 carry-forward gates" subsection below). **Pre-closure status (preserved as the design record):** implementation in review. [ADR-0030](../../decisions/0030-syscall-abi.md) (syscall ABI + the K2-5 `IpcError` taxonomy split) and [ADR-0031](../../decisions/0031-initial-syscall-set.md) (the five-syscall v1 set) are **Accepted**. **[T-020](../../analysis/tasks/phase-b/T-020-syscall-error-taxonomy.md)** (the `IpcError::InvalidCapability` → `StaleHandle`/`MissingRight`/`WrongObjectKind` split + `Capability`/`CapObject` `Debug` redaction — sub-breakdown §6) is **In Review**. **[T-021](../../analysis/tasks/phase-b/T-021-syscall-dispatch.md)** (the EL0→EL1 `SVC` trap trampoline + panic-free dispatcher + copy-from/to-user + the debug-console capability + `SyscallError` — sub-breakdown §§3–5 + 7) is **In Review** on branch `t-021-syscall-dispatch`: a new architecture-agnostic kernel `syscall` module + the BSP `SVC` sync trampoline (installed at `VBAR_EL1+0x200` and `+0x400`), exercised at B5 by an EL1 kernel-stub `SVC` (current-EL `+0x200` path) with all gates green (host tests 236; `test --release`; Miri clean; QEMU smoke shows the round-trip + `console_write` emitted bytes). The **real EL0 `+0x400` round-trip** is carried to B6 per the acceptance criteria below. Remaining after T-020/T-021 merge: the deferred [`task_create_from_image`](#milestone-b4--task-loader) wrapper, then B6.

### Sub-breakdown

1. **ADR-0030 — Syscall ABI.** Register calling convention (which regs carry syscall number vs. arguments vs. return); maximum arg count; error-return convention (register + flag vs. `Result`-like encoding); asynchronous vs. synchronous semantics. **Bundle K2-5:** design the full userspace error taxonomy as part of this ADR — split `IpcError::InvalidCapability` into `StaleHandle` / `MissingRight` / `WrongObjectKind` (code review §Correctness IPC bullet 4) so the syscall error space and the in-kernel error space agree from the start.
2. **ADR-0031 — Initial syscall set for B-phase.** At minimum: `send`, `recv`, `console_write` (debug-gated), `task_yield`, `task_exit`. No more in v1.
3. **Exception-vector dispatch** — the EL0-synchronous vector routes to a Rust syscall dispatcher after saving user registers.
4. **Syscall dispatcher** — maps a syscall number to a handler, validates capabilities, performs the operation, returns. **Must be panic-free on every untrusted input** (typed error for every failure path), consistent with B0's hardening pattern.
5. **Copy-from / copy-to user** — validated access to userspace memory through the active address space. No raw dereferencing of user pointers.
6. **`Capability::Debug` redaction (K3-9).** Before `console_write` can log a `Capability` value (it never should, but userspace-reachable log paths demand defense-in-depth), redact the derived `Debug` impl on `Capability` — either a custom impl that prints `Capability { rights: …, object: <redacted> }` or a `Redacted<T>` wrapper type. Security review §6.
7. **Tests** — host-side ABI encoder/decoder tests; QEMU smoke where a kernel-stub "userspace" makes a syscall.

### Acceptance criteria

- ✅ ADR-0030 and ADR-0031 Accepted (2026-05-29).
- The syscall **dispatch mechanism** works and preserves register state: the dispatcher is installed at both the current-EL (`VBAR_EL1+0x200`) and lower-EL (`+0x400`) sync vectors, and the round-trip is exercised at B5 via an **EL1 kernel-stub `SVC`** that takes the current-EL `0x200` vector (per [ADR-0030 §Simulation](../../decisions/0030-syscall-abi.md#simulation), an `SVC` issued at EL1 cannot take the lower-EL vector). The **real EL0 round-trip through the `0x400` vector** — with the EL0↔EL1 privilege transition and copy-user against a separate userspace `TTBR0_EL1` — requires kernel mappings in the userspace AS + an EL0 context register file (gated on the ADR-0033 high-half placeholder) and is therefore a **B6 acceptance criterion**, not B5. *(Done — T-021; the `0x200` proxy round-trip is QEMU-smoke-verified, the `0x400` handler is installed but its runtime exercise is B6's.)*
- Invalid syscalls (bad number, missing/stale/wrong-kind capability, out-of-bounds pointer) return typed errors without panicking; every object-naming syscall performs a capability check (P1/P4). *(Done — T-021.)*
- Copy-from-user never dereferences raw user pointers outside the validated mapping. *(Done — T-021.)*
- `IpcError` variants are split per ADR-0030's taxonomy (`StaleHandle` / `WrongObjectKind` / `MissingRight`); all call sites and tests updated. *(Done — T-020.)*
- `Capability` (and `CapObject`) `Debug` output redacts the named kernel object. *(Done — T-020.)*

### Flags to resolve during B5

- 🚩 **Fault containment (K3-4).** Task-body `.expect` / `panic!` still halts the whole kernel today. The syscall dispatcher itself must be panic-free (acceptance criterion above), but full fault containment (a supervisor endpoint the crashing task's parent can observe) is Phase E work (first real driver task). Decision at B5: confirm the split — dispatcher panic-free now, supervisor design deferred. Recommendation: defer to Phase E.
- 🚩 **`IpcError` split timing.** If ADR-0030 becomes too large, split the error-taxonomy portion into a sibling ADR and implement it in parallel; ensure both land before the first userspace call.

---

## Milestone B6 — First userspace "hello"

A real userspace task, loaded by B4, running in EL0 in its own address space, makes a `console_write` syscall, and exits cleanly via `task_exit`.

### B6 opening sequence & prerequisites

> Added at B5 closure (2026-05-29) as the careful pre-B6 plan. The *decisions* named below are settled by their ADRs when B6 opens; this section fixes the **order and the dependency rationale**, not the decisions. The §Sub-breakdown that follows is the original B6 task list; steps 5–7 below map onto it.

**The gating prerequisite — the kernel must stay reachable from every task's active translation.** Today the loader's userspace AS holds **only** image + stack ([`task_loader.rs`](../../../kernel/src/obj/task_loader.rs)): no kernel mappings. The moment a real EL0 task issues an `SVC` (or takes any exception), the CPU vectors to `VBAR_EL1` and *fetches* the trampoline instruction — which lives at a kernel PA **not mapped in that task's `TTBR0_EL1`** → translation-fault on the vector fetch, unrecoverable. (B5's smoke worked only because the EL1 stub runs in the *bootstrap* AS, where the kernel is identity-mapped.) **Nothing in B6 runs until this is solved** (`TCR_EL1.EPD1 = 1` today — TTBR1 disabled).

**ADRs that open B6** (per [ADR-0025 §Rule 1](../../decisions/0025-adr-governance-amendments.md), the first implementation task opens in the same commit as the ADR's *Dependency chain*):

1. **ADR-0033 — kernel reachable from every AS.** Settle: full **high-half** (kernel → `TTBR1_EL1`, `EPD1 = 0`; per-task userspace → `TTBR0_EL1`) vs. **map-the-kernel-into-each-`TTBR0`**. The [ADR-0027 §Decision-outcome](../../decisions/0027-kernel-virtual-memory-layout.md) cost analysis (Option C vs D — high-half costs a linker-script + jump-to-high-half dance + identity teardown + ~4 `unsafe` entries; the map-into-each-AS path trades that for per-AS kernel-mapping bookkeeping) is the starting point. High-half is the named, standard shape; the ADR must also settle `TCR_EL1.A1`/ASID per ADR-0027 §"ASID".
2. **EL0 task context decision** (folded into ADR-0033 or a sibling ADR). [`Task`](../../../kernel/src/obj/task.rs) carries only `id + address_space_handle` today; running EL0 needs an entry context (`ELR_EL1` = entry, `SPSR_EL1` = EL0t, `SP_EL0` = stack top) + a per-task `SP_EL1` kernel stack + an *enter-EL0 / `ERET`-into-EL0* path distinct from the cooperative [`ContextSwitch`](../../../hal/src/context_switch.rs) (which saves only the kernel callee-saved set). The syscall trampoline already provides the *return*-to-EL0 half; the *first-entry* half is new.
3. **ADR-0034 — kernel-image section permissions** (optional in B6). Its trigger (first attacker-observable EL0 execution) fires at B6, but it is hardening, **not** a functional blocker (the v1 `hello` is code-only, mapped `USER | EXECUTE`). Decide in B6 whether to harden now or defer.

**Dependency-ordered task sequence** (each rides on the prior):

1. ✅ **ADR-0033 + the high-half migration** ([T-022](../../analysis/tasks/phase-b/T-022-high-half-kernel-mapping.md), **In Review 2026-05-30**): the kernel now runs in `TTBR1_EL1` (boot-time migration; `tyrne: high-half active` marker), `TTBR0_EL1` is freed for per-task userspace, and `<QemuVirtMmu as Mmu>::activate` writes a per-task root PA into it (the runtime distinct-AS swap fires in B6, step 3). Single linear high-half offset; whole-image-high-linked + forced-low entry; fault-clean QEMU smoke. **This unblocks the rest of B6** (steps 2–7 build on the settled high-half regime).
2. **EL0 task context register file + the enter-EL0 path + per-task `SP_EL1`** (closes [T-021 carry-forward gate #2](#milestone-b6--first-userspace-hello)).
3. **`task_create_from_image`** — `LoadedImage` → runnable `CapHandle{CapObject::Task(...)}` (composes steps 1 + 2; the deferred [§B4 §3](#milestone-b4--task-loader) bridge).
4. **Close the remaining T-021 carry-forward gates:** the per-task `console_write` window + per-page user-VA → kernel-VA translation returning `FaultAddress` (**gate #1 — security-critical**; without it an EL0 debug-console-cap holder reads arbitrary kernel memory), and `SYSCALL_STUB_TABLE` → the scheduler's current-task table (**gate #3**).
5. **`tyrne-user` crate** (safe wrappers) + **`userland/hello/` crate** + the `cargo build → objcopy -O binary → include_bytes!` pipeline + the shared `userland-layout` source-of-truth ([ADR-0029 §"Build pipeline (B6)"](../../decisions/0029-initial-userspace-image-format.md)). *(§Sub-breakdown items 1 + 3.)*
6. **Wire-up + QEMU smoke** *(§Sub-breakdown items 2 + 4)*: a true EL0 task takes the lower-EL `+0x400` vector, the dispatcher copies `console_write` from the task's `TTBR0_EL1`, `ERET` returns to EL0, and `task_exit` terminates it — the EL0↔EL1 round-trip B5's `+0x200` proxy could not prove.
7. **Closure = the Phase B retrospective** *(§Sub-breakdown items 5–7)*: the guide, the first hypothesis-driven performance cycle (real EL0 round-trip / IPC / context-switch vs the A6 baseline — and a same-host control, given the [B5 perf leg](../../analysis/reviews/performance-optimization-reviews/2026-05-29-B5-closure.md)'s finding that the harness is nearing its resolving floor), and a security review of the now-attacker-observable boundary.

### Sub-breakdown

1. **Userspace "hello" program** — a minimal `no_std, no_main` binary living in `userland/hello/` (new crate) that calls the syscall ABI directly.
2. **Wire-up** — kernel loads this binary on boot via B4, creates a task in its AS (via B3), schedules it (via A5 + B0), runs it (via B1/B2/B5).
3. **Syscall library** — a small `tyrne-user` crate exposing safe wrappers for the B5 syscalls.
4. **QEMU smoke** — trace shows kernel greeting + userspace greeting in correct order + task_exit + kernel shutdown message.
5. **Guide** — `docs/guides/first-userspace.md` explains what this demonstrates.
6. **Performance review** — first hypothesis-driven cycle using the timer introduced in B0. Measure IPC round-trip, context-switch, boot time; compare against A6 baseline.
7. **Business review** — Phase B retrospective.

### Acceptance criteria

- Userspace "hello from userspace" appears on the serial console after the kernel's greeting.
- **The real EL0→EL1 syscall round-trip is exercised at runtime** (carried over from B5): a true EL0 task takes the lower-EL sync vector (`VBAR_EL1+0x400`), the dispatcher copies the `console_write` buffer from the userspace `TTBR0_EL1` address space, and `ERET` returns to EL0 — the half B5's EL1 kernel-stub proxy could not prove (see [ADR-0030 §Simulation](../../decisions/0030-syscall-abi.md#simulation)).
- Userspace can call `task_exit` cleanly; the kernel reports task termination.
- Guide: `docs/guides/first-userspace.md` committed.
- Performance review recording IPC round-trip and context-switch numbers against the A6 baseline.
- Business review recording Phase B retrospective.

### T-021 carry-forward gates (must close *before* a real EL0 task runs)

The [T-021](../../analysis/tasks/phase-b/T-021-syscall-dispatch.md) review-round (2026-05-29) confirmed **no live B5 defect** but identified three forward-gates that the B5 EL1-kernel-stub proxy did not need and that B6 **must** close when it wires the first real EL0 task. They are intentionally B6 work; tracked here so they are not missed:

1. 🚩 **`console_write` user-window + deref (the single most important gate).** The copy is a direct int-to-pointer deref bounded by a `UserAccessWindow` ([`bsp-qemu-virt/src/syscall.rs`](../../../bsp-qemu-virt/src/syscall.rs) `SYSCALL_USER_WINDOW_LEN`); post-T-022 that window is the whole **high-half RAM direct-map alias** (`phys_to_kernel_va(PMM_EXTENT_START)`). It is harmless today because the *only* caller is the trusted EL1 stub (its buffer is a legitimate kernel high VA, and `EPD0 = 1` means no real EL0 task can even reach `syscall_entry`). If B6 wires `syscall_entry` to a real EL0 task **unchanged**, an EL0 holder of a debug-console capability could pass an in-window **high (kernel) VA** and have EL1 copy privileged memory to the console. B6 must (a) derive a **per-task** window from the EL0 task's actually-mapped region (not the RAM extent) and (b) replace the int-to-pointer deref with a per-page user-VA → kernel-VA translation **walking the task's own `TTBR0`** (the forward path documented in [`user_access.rs`](../../../kernel/src/syscall/user_access.rs) module docs + [`crate::mm::phys_frame_kernel_ptr`](../../../kernel/src/mm/mod.rs)). **The window/translation failure must return `SyscallError::FaultAddress`, never panic.** **Hard ordering precondition (sharpened by the T-022 review):** this gate MUST be closed *before* `syscall_entry` becomes reachable by any real EL0 task — the bounds-check + direct deref is **necessary-but-insufficient** as a privilege boundary (it bounds the range; it does not prove the pointer names the *task's* memory rather than a kernel high-half VA that merely falls in-window). Fails closed today only because `EPD0 = 1` keeps EL0 out of `syscall_entry` until the EL0-entry task lands.

   **✅ Mechanism LANDED (2026-05-31, [T-025](../../analysis/tasks/phase-b/T-025-user-access-translation.md) / [ADR-0038](../../decisions/0038-mmu-translate-and-user-access.md)).** `Mmu::translate` (read-only walk) + the **two-pass** per-page translate-based `copy_from_user`/`copy_to_user` (every spanned page resolved through the task's own AS, **`USER` required**, `FaultAddress` on any miss/non-`USER`/block — never panic) + the per-task `[entry_va, stack_top_va)` window first-gate now exist and are exhaustively host-tested (confused-deputy reject, unmapped, read-only, multi-page all-or-nothing). The hard-ordering precondition is satisfied — the translate-based boundary is in **before** any real EL0 task is enabled. In B5 `syscall_entry` passes the bootstrap AS, so the stub's kernel-VA `console_write` is now correctly **rejected** (smoke: `status=0x3`, the gate-#1 demonstration). **Remaining for the wire-up:** sourcing the *running EL0 task's* AS + per-task window from the scheduler so a real task's USER buffer translates — that is **gate #3** ([T-026](../../analysis/tasks/phase-b/T-026-current-task-cap-table.md)).
2. 🚩 **`SP_EL1` initialisation for the `+0x400` entry.** The sync trampoline's first `sub sp, sp, #272` runs on `SP_EL1`, which the CPU does **not** auto-initialise on an EL0→EL1 trap. B6's per-task EL0 context-init must set `SP_EL1` to a valid kernel stack before any EL0 task is schedulable (and should assert it). Subsumed by the "EL0-ready context register file" work (ADR-0033 placeholder) but named here explicitly.
3. ✅ **`SYSCALL_STUB_TABLE` → scheduler current-task table — CLOSED (2026-05-31, [T-026](../../analysis/tasks/phase-b/T-026-current-task-cap-table.md)).** `syscall_entry` now sources the *running EL0 task's* capability table, address space, and user-access window from `SCHED.current` (scheduler `task_cap_tables` / `task_user_windows` parallel arrays + `current_*` accessors, written by `add_user_task`), and **fails closed** when no task is current — the empty `FAILCLOSED_TABLE` (every lookup → `InvalidHandle`) + an empty window. The **control-plane** syscalls (`task_yield`/`task_exit`, which consult no capability) are gated in the dispatcher on a `has_current_task` flag → `InvalidHandle` when no task is current (H2). `SYSCALL_STUB_TABLE` retired; mandatory UNSAFE-2026-0014 Amendment (the cap-table-pointer deref). Host-tested + smoke shows the no-current-task fail-closed (`console_write` → `0x102`). The runtime per-task exercise (a real EL0 task naming its own caps) is the B6 wire-up.

Two further hazards are later-phase (already tracked, not B6): `ipc_send`'s `unreachable!()` becomes a release panic-from-userspace only under **preemption/SMP** (harden to `Err(QueueFull)` when preemption lands — ADR-0032 / note C3-009); and **fault containment** for an EL0 non-`SVC` sync fault (illegal instruction, unmapped deref) is Phase E / flag K3-4 (the dispatcher itself is already panic-free).

### Flags to resolve during B6

- 🚩 **CI rollout (K3-7).** If a CI pipeline exists by B6, wire the QEMU smoke as a regression gate (`qemu-system-aarch64 ... | grep "all tasks complete"`). If CI is still absent, defer to Phase C.
- 🚩 **`cargo-vet init` (K3-8).** Required only if any external dependency landed by B6 (none planned, but if a crate is added anywhere in B1–B6 this becomes a prerequisite for that PR).
- 🚩 **`write_bytes` TX timeout (K3-5).** Only applies to non-QEMU BSPs. If bsp-qemu-virt is still the only BSP, defer to the first non-QEMU BSP (Pi 4 in Phase D). Otherwise add the timeout cap.

### Phase B closure

When B6 is Done, run a business review. Phase C becomes active after that review.

---

## ADR ledger for Phase B (post-review)

| ADR | Purpose | Expected state | Note |
|-----|---------|----------------|------|
| ADR-0021 | Raw-pointer scheduler API (UNSAFE-2026-0012 resolution) | B0 | new — from 2026-04-21 security review blocker #1 |
| ADR-0022 | Idle task + typed scheduler deadlock error | B0 | new — from 2026-04-21 security review blocker #3 |
| ADR-0023 | Cross-table capability revocation policy | B0 (accept-deferred expected) | new — from 2026-04-21 security review blocker #2 |
| ADR-0024 | EL drop policy | B1 (Accepted 2026-04-27) | was ADR-0021 in the pre-review plan |
| ADR-0025 | ADR governance amendments (forward-reference, riders) | meta-process (Accepted 2026-04-27) | new — captures the rules T-006/T-009 retros surfaced; not B-phase content. Cool-down rule withdrawn pre-Accept; see ADR-0025 §Revision notes |
| ADR-0026 | Idle dispatch via separate fallback slot (supersedes ADR-0022 Option A) | B1 (Accepted 2026-05-06) | **repurposed.** Originally reserved for T-012 exception-vector / dispatch shape, which T-012 absorbed without a separate ADR. Slot reassigned 2026-05-06 to the idle-dispatch supersession motivated by the [B1 smoke regression](../../analysis/reviews/business-reviews/2026-05-06-B1-smoke-regression.md). Drives [T-014](../../analysis/tasks/phase-b/T-014-idle-dispatch-fallback.md). |
| ADR-0027 | Kernel virtual memory layout (B2 — identity-mapped MMU activation) | B2 (**Accepted 2026-05-08**) | was ADR-0025 in the pre-2026-04-27 plan; renumbered down by 2 because ADR-0025 (governance) and ADR-0026 (T-012 reservation) consumed slots. Drives [T-016](../../analysis/tasks/phase-b/T-016-mmu-activation.md) (Draft 2026-05-08; moves to In Progress with this Accept). First ADR to apply [`write-adr` skill §Simulation](../../../.agents/skills/write-adr/SKILL.md) discipline forward (rather than retro-extracted as for ADR-0026 / ADR-0032). Accept landed as a separate commit per `write-adr` §10. Companion architecture doc: [`docs/architecture/memory-management.md`](../../architecture/memory-management.md). |
| ADR-0028 | Address-space data structure (B3 — kernel-object + capability-gated `Mmu::map` wrappers + activation-on-context-switch) | B3 (**Accepted 2026-05-11**) | was ADR-0026 in the pre-2026-04-27 plan. Drives [T-018 (Draft 2026-05-11; moves to In Progress with the same-day Accept)](../../analysis/tasks/phase-b/T-018-address-space-kernel-object.md). Chosen shape: **Option A — Generic `AddressSpace<M: Mmu>` wrapping `M::AddressSpace` inline; per-type `AddressSpaceArena<M>`**. Reuses [ADR-0016](../../decisions/0016-kernel-object-storage.md)'s per-type fixed-size-block arena pattern; propagates the existing `M: Mmu` generic axis from [ADR-0019](../../decisions/0019-scheduler-shape.md) / [ADR-0020](../../decisions/0020-cpu-trait-v2-context-switch.md); zero new `unsafe` audit-log entries (the activation borrow rides UNSAFE-2026-0014's existing umbrella); zero HAL trait surface change (post-T-016 [`Mmu`](../../../hal/src/mmu/mod.rs) trait stays stable). Includes the §Simulation table walking bootstrap-AS wrap / create / map / activation-on-context-switch state transitions per [`write-adr` skill §Simulation](../../../.agents/skills/write-adr/SKILL.md). |
| ADR-0029 | Initial userspace image format | B4 | was ADR-0027 |
| ADR-0030 | Syscall ABI (includes `IpcError` taxonomy per K2-5) | B5 (**Accepted 2026-05-29**) | was ADR-0028. Settles the register convention (`x8`=number, `x0`–`x5` args, `SVC #0`, `x0`=status) + the dedicated-status-register encoding + `SyscallError` composition + the K2-5 `IpcError` split; drives [T-020](../../analysis/tasks/phase-b/T-020-syscall-error-taxonomy.md) + [T-021](../../analysis/tasks/phase-b/T-021-syscall-dispatch.md) (merged PR #34, `f98e1af`). |
| ADR-0031 | Initial syscall set | B5 (**Accepted 2026-05-29**) | was ADR-0029. Fixes the five-syscall v1 set (`send` / `recv` / `task_yield` / `task_exit` / `console_write`; `0` reserved-invalid); numbers `1`–`5` are a fixed ABI decision regression-verified by T-021's host tests, not chosen by the dispatcher. |
| ADR-0032 | Endpoint state rollback on `ipc_recv_and_yield` Deadlock + `ipc_cancel_recv` primitive | B2 prep (**Accepted 2026-05-07**) | drove [T-015 (Done 2026-05-07)](../../analysis/tasks/phase-b/T-015-endpoint-rollback-cancel-recv.md) via PR #17. Surfaced as Track A non-blocker in the [2026-05-06 comprehensive review](../../analysis/reviews/code-reviews/2026-05-06-full-tree-comprehensive.md) and a forward-flagged item in the [2026-05-07 B1 closure security review](../../analysis/reviews/security-reviews/2026-05-07-B1-closure.md). Closed before B-phase task lands the first userspace-driven endpoint destroy. ADR-0017 §Revision notes rider records the additive recovery primitive (user-observable surface unchanged). |
| [ADR-0033](../../decisions/0033-kernel-high-half-migration.md) | Kernel high-half migration (kernel → `TTBR1_EL1`, boot-time; reachable from every task AS) | **B6 (Accepted 2026-05-30)** | **filed** to open B6 — the gating prerequisite (an EL0 task's `SVC` vector fetch must translate, impossible while the kernel is identity-only in `TTBR0`). Extends [ADR-0027](../../decisions/0027-kernel-virtual-memory-layout.md) §Decision outcome (Option D) — consumes the reserved `TTBR1`/`EPD1` + byte-stable high-half `TCR` fields; **no supersede**. Boot-time migration (DAIF-masked window, no live low-VA pointers), staged. Drives [T-022](../../analysis/tasks/phase-b/T-022-high-half-kernel-mapping.md) (Draft; opens with the Propose commit per [ADR-0025 §Rule 1](../../decisions/0025-adr-governance-amendments.md)). §Simulation hardened against two adversarial verification passes; Option B (map-kernel-into-every-TTBR0) is the documented fallback. **Accepted 2026-05-30** after the maintainer careful-re-read (review-round folded into the Proposed draft); drives [T-022](../../analysis/tasks/phase-b/T-022-high-half-kernel-mapping.md) (**In Review 2026-05-30** — migration implemented + all gates green incl. Miri + QEMU smoke fault-clean; whole-image-high-linked + single linear high-half offset; the ADR's Option-2 fallback was not needed). |
| ADR-0034 | Kernel-image section permissions (.text RX / .rodata R / .bss/.data RW) | B-late (placeholder; named-but-unallocated) | named in [ADR-0027 §Decision outcome (a)](../../decisions/0027-kernel-virtual-memory-layout.md) as the future home of finer-grained kernel-image permissions. v1 maps the entire 128 MiB RAM range as kernel R/W/X via 2 MiB blocks; T-016 §Out of scope and [`memory-management.md` §"v1 layout"](../../architecture/memory-management.md) defer the re-map. Opens with the first B-phase task whose threat model includes a kernel R/W of `.text` as a meaningful surface — likely **B6** — the first attacker-observable EL0 execution context (the v1 `hello` is code-only mapped `USER\|EXECUTE`, so ADR-0034 is hardening, not a B6 functional blocker; decide in B6 whether to harden now or defer). |
| ADR-0035 | Physical Memory Manager (B3 prerequisite — bitmap allocator) | B3 (**Accepted 2026-05-09**) | new — drove the realisation that B3's "Address space abstraction" milestone has a foundational prerequisite (a real `FrameProvider` impl over physical RAM) which deserves its own ADR rather than being absorbed into ADR-0028 (address-space data structure). Drives [T-017 (Draft 2026-05-09; moves to In Progress with this Accept)](../../analysis/tasks/phase-b/T-017-physical-memory-manager.md). Bitmap allocator with hint pointer; 4 KiB metadata for QEMU virt's 32 K frames; reservation-list at init + cached for `free_frame` defensive validation per the §Simulation §Step 2 Critical row; forward-portable to high-half kernel without algorithm rewrite. Includes the §Simulation table walking init / alloc / free / exhaustion / recovery state transitions per [`write-adr` skill §Simulation](../../../.agents/skills/write-adr/SKILL.md). Accept landed as a separate commit per `write-adr` §10 after a careful re-read pass that surfaced and corrected three substantive drafting issues (broken anchor, safe-Rust-vs-`unsafe` zeroing contradiction, muddled "undefined-vs-error" wording in §Simulation row 2; the row-2 fix tightened the Pmm struct contract to add a cached reserved-range list for defensive `free_frame` validation, propagated to T-017). |
| ADR-0036 | QEMU virt is GICv2 / no-IOMMU in v1 (corrects ADR-0004 / 0006 / 0012) | post-B1 (**Accepted 2026-05-22**) | new — surfaced by the [2026-05-22 full-tree master review](../../analysis/reviews/master-review/2026-05-22-152729/consolidated.md): the foundational ADRs carried GICv3 / SMMUv3 statements that do not match the GICv2, no-IOMMU reality of QEMU `virt` that B1's GIC work (above) actually assumed. **Corrects** (append-only redirect rider; does **not** supersede) [ADR-0004](../../decisions/0004-target-platforms.md) / [ADR-0006](../../decisions/0006-workspace-layout.md) / [ADR-0012](../../decisions/0012-boot-flow-qemu-virt.md). Ratifies the GICv2 fact stated in the B1 milestone. |

Numbers are tentative. Final numbers are assigned when the ADR is actually written, per [ADR-0013](../../decisions/0013-roadmap-and-planning.md).

---

## Open questions / flagged decisions (Phase B)

### Decisions that must close during their named milestone

- 🚩 **B0 — Cross-table capability revocation.** Accept-deferred (recommended) vs. implement-now. Answer locks ADR-0023.
- 🚩 **B0 — Architecture-doc scope.** Whether notifications get their own architecture doc in B0 or later.
- 🚩 **B2 — Generation wrap-around (K3-1).** Raise counter, monotonic scheme, or document the bound.
- 🚩 **B3 — Cross-table revocation, revisit.** If the deferred ADR-0023 decision bites any B3 test, promote.
- 🚩 **B5 — Fault containment scope (K3-4).** Confirm the split: dispatcher panic-free in B5, supervisor endpoint in Phase E.
- 🚩 **B5 — `IpcError` split timing.** Bundle with ADR-0030 or split into its own ADR.
- 🚩 **B6 — CI rollout timing (K3-7).** Wire QEMU-smoke regression gate if CI exists.
- 🚩 **B6 — `cargo-vet init` (K3-8).** Prerequisite only if an external dep lands during Phase B.
- 🚩 **B6 — `write_bytes` TX timeout (K3-5).** Only applies when a non-QEMU BSP exists.

### Watch-list items (monitored, no decision required unless triggered)

- **K3-13 — TPIDR_EL0 save-set.** If any Phase B milestone introduces TLS at EL1, extend `Aarch64TaskContext` and `context_switch_asm` in the same commit; update UNSAFE-2026-0008 audit entry.
- **Priority classes (ADR-0019 open question).** Single class remains the Phase B default; multiple classes may become a driver for Phase C's preemption work.

---

## How to start Phase B

> **Historical onboarding record (B0–B4 complete).** Phase B implementation is done: B0, B1, B2, B3, and B4 are all closed (B4 closed 2026-05-28 via its closure trio — see the B4 status line above). The active next step is B5 (syscall boundary); the live operational pointer for what to open next is [`docs/roadmap/current.md`](../current.md), not this section. The numbered procedure below is preserved as the entry procedure that was followed when Phase B opened — it is a record of how B0 was started, not live instructions.

1. Open **T-006** (raw-pointer scheduler API refactor) via the [`start-task`](../../../.agents/skills/start-task/SKILL.md) skill. Writing ADR-0021 is the first step inside that task.
2. After T-006 is In Progress, parallel work on **T-008** (architecture docs) is safe — they do not touch the same code.
3. **T-007** (idle task + typed deadlock) should follow T-006 so both changes land on top of the settled `Scheduler` shape.
4. **T-009** (timer init) can run in parallel with any of the above — it only touches `QemuVirtCpu` and does not intersect the scheduler refactor.
5. **T-011** (missing tests) comes last within B0 so the tests are written against the final shape of the code they exercise.
6. B1 starts only after B0 closes with its business review (short milestone retrospective per ADR-0013).
