# Business review 2026-06-01 — Phase B closure retrospective (B0–B6: from EL1 boot to the first EL0 userspace task)

Phase B took Tyrne from "a kernel that boots and cooperatively schedules kernel-mode tasks at EL1" to **"a capability microkernel that loads, runs, and cleanly terminates a real userspace program at EL0 across a capability-gated syscall boundary."** B6 — the first userspace "hello" — closes the phase. This is the phase-level retrospective; the per-milestone closure trios (B1–B5) remain the canonical record for their numbers.

## What Phase B built

| Milestone | Delivered | Key ADRs |
|---|---|---|
| **B0** | Phase A exit hygiene (raw-pointer scheduler bridge, typed-deadlock fixes, timer init, the test/doc backlog) | — |
| **B1** | Drop to EL1 in boot + exception/IRQ infrastructure (`VBAR_EL1`, the vector table, the IRQ trampoline + `TrapFrame`) | ADR-0024 |
| **B2** | MMU activation, kernel-half identity mapping | ADR-0027 |
| **B3** | The `AddressSpace` kernel object + cap-gated `Mmu::map`/`unmap` + activation-on-context-switch; the PMM (bitmap allocator) | ADR-0028, ADR-0035 |
| **B4** | The task loader (`load_image` → `LoadedImage`; raw-flat image format) | ADR-0029 |
| **B5** | The syscall boundary: the `SVC` trampoline + the **panic-free** dispatcher + `copy_from/to_user` + the debug-console capability; the `IpcError` taxonomy split + `Debug` redaction | ADR-0030, ADR-0031, ADR-0032 |
| **B6** | **The first real EL0 userspace task.** High-half migration (kernel → `TTBR1`, `TTBR0` freed for userspace); the EL0 entry context + register scrub; `task_create_from_image`; the two syscall gates (per-page user-VA translate + per-task cap-table sourcing); the userland build pipeline; and the wire-up that runs `userland/hello` in EL0 + terminates it | ADR-0033, ADR-0037, ADR-0038, ADR-0039 (+ ADR-0036 the GICv2/no-IOMMU correction) |

**The B6 spine — five gates between "the mechanism exists" and "a real EL0 task is safe":** high-half (kernel reachable from every AS via `TTBR1`, absent from `TTBR0`, `UXN`/`PXN` from EL0); EL0 entry + register scrub + per-task `SP_EL1` (gate #2); per-page user-VA→kernel-VA translation requiring `USER` (gate #1, the confused-deputy defence); per-task capability-table sourcing, fail-closed (gate #3); and the cooperative termination path (`task_exit_current`). Each landed as its own task with its own review; the first EL0 task ran only after all were in.

## Headline numbers (at B6 closure, `c8792cf`)

- **Tests:** 366 host (46 hal / 259 kernel / 58 test-hal / 3 doc) — +27 over B5's 339; `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` **0 UB**.
- **Footprint (release):** `text`+`.rodata` 42,240 / `.bss` 64,240 — bounded growth (the bss is new statics + page-table frames, RAM not image).
- **Boot-to-end:** same-host band p10/p50/p90 = 13.143 / 15.507 / 18.469 ms; **running the first EL0 task adds no measurable boot-to-end cost** (a same-host control proves the EL0 delta is sub-floor) — see the [perf leg](../performance-optimization-reviews/2026-06-01-B6-closure.md).
- **Smoke (the load-bearing evidence):** `ERET`→EL0 → `console_write` over `+0x400` → `hello from userspace` → `task_exit` → `userspace task exited` → `all tasks complete`; exactly the 2 expected EL0 `SVC` exceptions, **zero new fault class**.
- **ADRs:** 12 accepted in Phase B (0027–0039, minus the deferred 0034). **Audit log:** through UNSAFE-2026-0033, every `unsafe` block accounted for.
- **Security:** the now-attacker-observable EL0 boundary reviewed at [2026-06-01](../security-reviews/2026-06-01-T-028-el0-userspace-wireup.md) (Approve) + the [consolidated Phase-B review](../security-reviews/2026-06-01-phase-b-closure.md).

## What changed in the plan

- **B5 split the syscall work pure-Rust-first (T-020) then hardware-boundary (T-021)** — the most security-sensitive milestone landed safely by front-loading the ABI before the trampoline.
- **B6 grew from "wire up the loader" into a five-gate security arc.** The T-021 review surfaced three carry-forward gates that *had* to close before a real EL0 task; B6 closed them as distinct tasks (T-025/T-026 + the T-023 entry context) before T-028 ran anything. "Build the mechanism, defer the transition" (B5) matured into "land every gate, *then* cross the boundary."
- **The high-half migration (ADR-0033) was pulled forward** as the B6 gating prerequisite — the kernel had to stay reachable from a real task's `TTBR0` before any EL0 task could trap.
- **`task_exit` termination was an unplanned scheduler addition.** The cooperative scheduler had no termination path; running the first EL0 task surfaced it (the task ran past `task_exit` → fault). Closed by `task_exit_current` (sharing `start`'s dispatch tail).

## What we learned

### The gate-by-gate discipline made the most dangerous boundary land without an exploitable defect
The EL0 boundary is where a capability OS lives or dies. By closing each gate (#1/#2/#3 + high-half) as its own reviewed task *before* enabling EL0, the first real EL0 task ran with **0 confirmed exploitable defects** across the per-task reviews and the consolidated pass. The "hard ordering precondition" the T-021 review wrote ("close the gates before `syscall_entry` is EL0-reachable") was honoured to the letter.

### Adversarial review + Miri keep catching what confirming review misses
The pattern from B5 (an adversarial pass + Miri caught a soundness over-claim) repeated across B6: adversarial workflows on ADR-0038/0039, T-025/T-026, and the EL0 boundary surfaced real issues (the `--workspace`/Miri host-build regression in T-027; the all-or-nothing binding hardening in T-026) that confirming review would have missed.

### The same-host perf control is now load-bearing, not optional
B5 found the boot-to-end harness near its resolving floor. B6 *proved* it: the raw B6 band was **lower** than B5 (impossible as a real effect) — only the same-host control revealed it as session drift. Cross-session boot-to-end absolutes are no longer meaningful at B-phase granularity; same-host deltas and per-op micro-measurements (deferred to T-029) are.

### "Slow and correct" scaled to a 7-task milestone
B6 spanned T-022…T-028 + three ADRs, each Propose→review→Accept and implement→review→merge, with the security review gated *before* the first EL0 task. The methodical pace did not slow the milestone into incoherence — it kept each gate auditable and the boundary sound.

## Closure status of prior-milestone Adjustments

- **B4 §Adjustments** (the `task_create_from_image` bridge) — **closed** (T-024, merged; consumed by T-028's wire-up).
- **B5 §Adjustments** (the three T-021 carry-forward gates) — **all closed** (gate #1 T-025, gate #2 T-023, gate #3 T-026) before the first EL0 task ran.
- **The B-phase ADR placeholders** — ADR-0033 (high-half) Accepted; ADR-0034 (per-section permissions) still deferred (its trigger fired at B6 but it is hardening, not a functional blocker — carried to Phase C).

## Adjustments (carry-forward to Phase C)

- **Object lifecycle on exit (SEC-T024-01 / SEC-T028-01).** A `task_exit`'d task's slot, address space, and capability table are not reclaimed, and its `task_states` slot stays `Ready` (orphaned). Inert in v1 (the handle is unreachable; the slot is not reused), but the successor lifecycle ADR should add a **terminal task state** + couple reclamation to AS/task destruction.
- **Per-op perf micro-measurements (T-029).** EL0 round-trip / IPC / context-switch need feature-gated `CNTVCT` instrumentation — opened as a focused task so the instrumentation gets a gated, audited pass.
- **EL0 fault containment (K3-4).** An EL0 *non-`SVC`* sync fault (illegal instruction, unmapped deref) currently panics the kernel (a denial-of-self, not an escalation — confirmed). Containing it (an EL0-fault handler that terminates the offending task, not the kernel) is Phase E / flagged.
- **Per-section userspace permissions (ADR-0034).** RX `.text` / R `.rodata` / RW `.data` — needed once userspace grows beyond code + read-only data.
- **Preemption / SMP hazards.** `ipc_send`'s `unreachable!()` and the IRQ-under-task-`TTBR0` invariant become live only under preemption/SMP — to assert when that phase opens.

## Next

Per [phase-b.md §closure](../../../roadmap/phases/phase-b.md#phase-b-closure), Phase C becomes active after this review. Phase B delivered the microkernel core — privilege separation, the capability-gated syscall boundary, and the first userspace task; Phase C builds on a kernel that can now run untrusted user code. The carry-forwards above (object lifecycle, fault containment, per-section permissions) are the natural early Phase-C hardening once a second userspace program or a driver surfaces the need.
