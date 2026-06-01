# Security review 2026-06-01 — Phase B closure (consolidated, B0–B6)

- **Subject:** the **integrated** Phase B kernel surface, now that a real EL0 userspace task is attacker-observable (B6). Each Phase B task was individually security-reviewed (T-022 high-half = Approve; T-025/T-026 adversarial passes; [T-028 EL0-boundary](2026-06-01-T-028-el0-userspace-wireup.md) = Approve, 0 confirmed exploitable). This consolidated pass is the **seam review**: does the *combination* of the Phase B subsystems — capability system, IPC, MMU/AddressSpace/PMM, the high-half regime, the syscall boundary, and the EL0 transition — introduce a defect a per-task review could miss at the boundaries between tasks?
- **Reviewer:** @cemililik (+ Claude Opus 4.8 (1M context) agent, adversarial across the eight axes of the [master plan](master-plan.md) via a 5-lens / 29-agent workflow with per-finding skeptic verification). Performed **2026-06-01** at the B6-closure HEAD.
- **Method:** 5 integrated lenses (capability+IPC integrity · MMU/AS isolation · the EL0↔EL1 transition · panic-freedom + fault containment · secrets/deps/threat-synthesis), each finding refuted-or-confirmed by two independent skeptics against the live code.

## Result by axis

| Axis | Verdict |
|------|---------|
| **1. Capability correctness** | **Pass.** Per-subject unforgeability ([ADR-0014](../../../decisions/0014-capability-representation.md)) holds across the integrated surface: every decoded handle (incl. a forged/sentinel word) is `lookup`-validated (bounds + generation + occupancy) against the **running task's own** table (gate #3); no cross-table or EL0-forged cap resolves. The null-handle sentinel (`u64::MAX`) provably cannot collide with a packable handle (compile-time asserted). |
| **2. Trust boundaries** | **Pass.** The EL0→EL1 `SVC`/`+0x400` path is kernel-fixed; the register scrub leaves EL0 no kernel state on every entry; `SPSR_EL1` = EL0t. gate #3 fail-closes to the empty `FAILCLOSED_TABLE` on any incomplete binding. |
| **3. Memory safety** | **Pass.** gate #1 (per-page `Mmu::translate` + `USER`) closes the confused-deputy across the high-half boundary; the task's `TTBR0` holds only image+stack, the kernel is high-half `UXN`/`PXN`. W^X holds (image `USER|EXECUTE` no `WRITE`; stack `USER|WRITE` no `EXECUTE`). `task_exit_current`'s abandon-frame switch is Miri-0-UB. No PMM double-allocation seam found. |
| **4. Kernel-mode discipline** | **Pass** (with forward-flags, §below). The `task_exit_current`/`run_dispatched`/`yield_now` calls from the SVC handler honour the [ADR-0021](../../../decisions/0021-raw-pointer-scheduler-ipc-bridge.md) no-`&mut`-across-switch discipline + the `IrqGuard`/`DAIF` masking; the dispatcher is panic-free on **syscall input** (§4-forward-flag scopes this). |
| **5. Cryptography** | **N/A.** |
| **6. Secrets and logging** | **Pass.** No path logs capability contents, buffer data, kernel pointers, or register state (the T-020 `Debug` redaction + the register scrub + the fixed console strings). The `include_bytes!` userland image is the committed `hello` crate's bytes. |
| **7. Dependencies** | **Pass.** No external crate added in Phase B; the userland links only in-tree `tyrne-user`; `rust-objcopy` is from the pinned toolchain (cargo-vet K3-8 unfired). |
| **8. Threat-model impact** | **Pass** (§below). Post-Phase-B attacker = a real EL0 task. It can `console_write` its own `USER` buffer and `task_exit`/`task_yield` its own identity; it provably **cannot** escalate, read kernel/foreign memory, forge caps, or corrupt the scheduler. |

## Verdict

**Approve.** No live security defect; **no fix required** to close Phase B. Five integrated seam lenses with per-finding skeptic verification produced **0 confirmed exploitable defects** (17 findings: 12 refuted as non-exploitable/accepted-v1-gap, 5 nits). Four lenses clean; the fifth's findings are forward-flags (below), not Phase-B defects. The integrated EL0 boundary is sound under the v1 threat model (single-core, cooperative). Gates at closure: fmt/clippy/kernel-build clean; **host tests 366** (46 hal / 259 kernel / 58 test-hal / 3 doc); Miri `--workspace --exclude tyrne-bsp-qemu-virt` **0 UB**; QEMU smoke proves the EL0 round-trip + clean `task_exit`, zero new fault class.

### Scope clarification the seam review surfaced (phase-gated here)

The Phase B "**panic-free dispatcher**" property is **syscall-input-scoped**: the dispatcher cannot be panicked by any *syscall register input* an EL0 attacker supplies (bad number → `BadSyscallNumber`; bad/forged cap → `InvalidHandle`; OOB/unmapped/non-`USER`/over-length buffer → `FaultAddress`; null handle → typed error — all fail closed). It is **distinct from execution-time fault handling**: an EL0 **non-`SVC` synchronous fault** (illegal instruction, unmapped deref — e.g. EL0 code running off its own image) currently routes to the kernel panic handler. This is a **denial-of-self, not an escalation** (the faulting task harms only itself; no privilege gain, no memory disclosure), and is the explicitly-deferred **K3-4 / Phase E** item — recorded here so Phase C readers do not mistake "panic-free dispatcher" for "EL0 cannot fault the kernel down."

### Forward-flagged items (carry-forward to Phase C / later; non-blocking; confirmed non-exploitable in v1)

- **Non-`SVC` EL0 fault containment (K3-4, Phase E).** An EL0 sync fault panics the kernel (denial-of-self). Phase E should add an EL0-fault handler that terminates the offending task, not the kernel.
- **Object lifecycle on exit (SEC-T024-01 / SEC-T028-01).** The exiting task's slot/AS/table are not reclaimed and its `task_states` stays `Ready` (orphaned) — inert in v1 (unreachable handle, slot not reused); the successor lifecycle ADR adds a terminal state + reclamation.
- **Gate #3 context resolution is non-atomic.** `syscall_entry` reads the three scheduler accessors (table/AS/window) without an atomic guarantee — sound under single-core + masked-IRQ (no peer mutates mid-read), a hazard to revisit under **preemption/SMP**.
- **Gate #1 trusts the loader.** The confused-deputy defence is correct *given* the loader never maps kernel memory as `USER` — enforced by the loader, not re-checked by the dispatcher. Sound for v1's build-time-embedded image; revisit if untrusted-image / filesystem loading lands.
- **Per-section W^X (ADR-0034).** Image is `USER|EXECUTE` (no per-section RX/.text vs R/.rodata split) — hardening, deferred.
- **SP_EL1 stack worst-case not empirically bounded** (4 KiB; the perf [T-029](../../tasks/phase-b/T-029-perf-microbench.md) micro-bench + a high-water check would quantify it); **IRQ-under-task-`TTBR0` relies on `TTBR1`** implicitly (assert under preemption).

These match the carry-forwards in the [Phase B retrospective](../business-reviews/2026-06-01-phase-b-closure.md) §Adjustments and the existing K3-4 flag; the seam review confirms each remains non-exploitable in the integrated v1 picture.
