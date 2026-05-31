# 0037 — EL0 entry context (userspace register file + enter-EL0/`ERET` path)

- **Status:** Accepted
- **Date:** 2026-05-31
- **Deciders:** @cemililik

## Context

[T-022 / ADR-0033](0033-kernel-high-half-migration.md) merged the high-half migration: the kernel runs in `TTBR1_EL1` and `TTBR0_EL1` is freed for per-task userspace. The next step toward [B6 — first userspace "hello"](../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello) is **running a task at EL0** — which the kernel cannot do today:

- The [`Task`](../../kernel/src/obj/task.rs) kernel object carries only `id: u32` + `address_space_handle` — **no entry context** (no user entry PC, no user stack pointer).
- The cooperative context-switch machinery is **EL1-only**: [`ContextSwitch::init_context`](../../hal/src/context_switch.rs) takes `entry: fn() -> !` (a *kernel* function pointer) + a kernel `stack_top`, and [`Aarch64TaskContext`](../../bsp-qemu-virt/src/cpu.rs) saves only the AAPCS64 callee-saved EL1 register set (`x19`–`x28`/`fp`/`lr`/`sp`/`d8`–`d15`, 168 bytes). There is **no path** that sets `ELR_EL1`/`SPSR_EL1`/`SP_EL0` and `ERET`s into EL0.
- ADR-0033 deliberately scoped itself to the migration and named the "EL0-ready `Task` context + enter-EL0/`ERET` path" a **separate B6 task** ([ADR-0033 §Dependency chain note](0033-kernel-high-half-migration.md)). [phase-b.md §B6](../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello) anticipated this decision ("folded into ADR-0033 or a sibling ADR"); ADR-0033's Accepted scope forecloses folding, so this **sibling ADR** settles it.
- The [B5 syscall trampoline](../../bsp-qemu-virt/src/vectors.s) already provides the **return-to-EL0** half (it saves `ELR_EL1`/`SPSR_EL1`/`SP_EL0` into the 272-byte `SyscallTrapFrame` and `ERET`s). What is missing is the **first-entry-into-EL0** half — and the [T-021 carry-forward **gate #2**](../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello): on a real EL0→EL1 trap the CPU switches to `SP_EL1`, which must already point at a valid kernel stack, but nothing initialises a per-task `SP_EL1` today (the only `SP` setup is the one boot-time `mov sp, __stack_top` in [`boot.s`](../../bsp-qemu-virt/src/boot.s)).

This ADR settles **how an EL0 task's first entry is expressed and how it integrates with the existing cooperative scheduler**, without yet wiring a runnable userspace task (that is `task_create_from_image` + the gate-#1 work + `userland/hello`, the B6 tasks that build on this one). It is implemented by **[T-023](../analysis/tasks/phase-b/T-023-el0-entry-context.md)**.

## Decision drivers

- **Minimum surface, staged ([CLAUDE.md #6](../../CLAUDE.md)).** B6 lands many firsts; this task adds *only* the EL0 first-entry mechanism, independently reviewable before `task_create_from_image` consumes it.
- **Reuse the verified cooperative machinery.** The scheduler, `context_switch_asm`, the per-task kernel stack, and the syscall trampoline's return-to-EL0 already exist and are smoke-/host-verified. An EL0 task should be a *kernel-managed task that drops to EL0*, not a parallel execution model.
- **Zero asm/`repr(C)` layout drift.** `context_switch_asm` reads `Aarch64TaskContext` at fixed byte offsets guarded by `const _: () = assert!(size_of == 168)` ([cpu.rs](../../bsp-qemu-virt/src/cpu.rs)). Any field added to that struct risks corrupting *every* cooperative switch (the [T-022 verification pass](../analysis/reviews/security-reviews/2026-05-31-T-022-high-half-migration.md) flagged this explicitly). The chosen design must not perturb that layout.
- **Security: the EL0 entry is the trust-boundary primitive.** The `ERET`-into-EL0 asm sets `SPSR_EL1` (the EL the CPU drops to) and `SP_EL0`; a wrong `SPSR` (e.g. dropping to EL1 instead of EL0, or leaving `DAIF` unmasked under a model that assumes masked) is a privilege/isolation defect. It must be a small, audited, single-purpose `unsafe` region.
- **`SP_EL1` correctness without new register bookkeeping.** Gate #2 must close, ideally without a separate per-task `SP_EL1` slot to keep in sync.

## Considered options

1. **Reuse `Aarch64TaskContext` + a one-shot `enter_el0` `ERET` trampoline.** Initialise a user task's *existing* kernel context so the first `context_switch_asm` restore lands in a small kernel trampoline that builds the EL0 state and `ERET`s. Carry the user entry VA + user SP in two already-restored callee-saved slots (`x19`/`x20`); leave the struct layout unchanged. `SP_EL1` = the task's kernel stack (the context's `sp`), set by the same switch.
2. **Extend `Aarch64TaskContext` with explicit EL0 fields** (`ELR_EL1`, `SPSR_EL1`, `SP_EL0`) and a dedicated enter-EL0 asm that loads them.
3. **A separate `UserTaskContext` struct + a distinct enter-EL0 scheduler path** parallel to the cooperative `ContextSwitch`.

## Decision outcome

**Chosen: Option 1 — reuse `Aarch64TaskContext` + a one-shot `enter_el0` trampoline; the kernel-object `Task` and the `Aarch64TaskContext` layout are both unchanged.**

This is the minimum-surface, lowest-risk integration: it reuses the verified cooperative switch verbatim, touches no asm offset, and closes gate #2 *by construction*.

**EL0 execution model.** A userspace task is a kernel-managed task that drops to EL0 on first dispatch and re-enters the kernel on every trap:

- **First entry.** [T-023](../analysis/tasks/phase-b/T-023-el0-entry-context.md) adds `ContextSwitch::init_user_context(ctx, user_entry: usize, user_sp: usize, kernel_stack_top)` (additive trait method, sibling of `init_context`) which sets, in the task's existing `Aarch64TaskContext`: `x19 = user_entry`, `x20 = user_sp`, `lr = enter_el0` (a new kernel trampoline), `sp = kernel_stack_top`. When the scheduler first dispatches the task, the unchanged `context_switch_asm` restores `x19`/`x20`/`sp` and `ret`s into `enter_el0`.
- **`enter_el0` trampoline** (new `#[unsafe(naked)]` asm, [UNSAFE-2026-0032]): runs at `EL1h` on the task's kernel stack; `MSR SP_EL0, x20` (user stack), `MSR ELR_EL1, x19` (user entry), `MSR SPSR_EL1, #0x3C0` (`M = EL0t`, `D/A/I/F` masked — see "v1 simplification"), `ERET` → the PC drops to EL0 at `user_entry` with `SP = user_sp`. It never returns (the `ERET` leaves EL1).
- **`SP_EL1` (gate #2) closed by construction.** Because the task entered EL0 *from* its own kernel context, `SP_EL1` still holds that context's `sp` (the per-task kernel stack the cooperative switch restored). When the EL0 task later traps via `+0x400`, the CPU switches to `SP_EL1` = that same kernel stack, and the syscall trampoline's first `sub sp, #272` lands in valid kernel memory. No separate `SP_EL1` slot is introduced; the existing per-task kernel stack *is* `SP_EL1`.
- **Trap / return / yield.** On `SVC`, the existing trampoline saves the EL0 frame on `SP_EL1` and runs `syscall_entry`; a `Resume` directive `ERET`s back to EL0 (the return-to-EL0 half B5 built). A cooperative `task_yield` is handled kernel-side by the existing `yield_now` (the syscall handler runs on the task's kernel stack, so a kernel context switch out/in is the ordinary cooperative path); the task resumes its *kernel* frame inside `syscall_entry`, which `ERET`s back to EL0. The `enter_el0` trampoline therefore runs **exactly once** per task (first dispatch); subsequent resumes are ordinary cooperative switches.

**D2 — where the EL0 context lives (the question phase-b.md §B6 left open): neither on the kernel-object `Task` nor in a new `TaskContext` struct.** The EL0 entry parameters are consumed at `init_user_context` time and encoded into the *existing* `Aarch64TaskContext` via the two callee-saved slots the switch already restores; the arch-specific `ERET` mechanics live in the BSP (where `Aarch64TaskContext` + `context_switch_asm` live), behind one additive HAL trait method. The kernel-object `Task` stays `id + address_space_handle` (storage-minimal; it is *task identity*, not register state — matching the existing `ContextSwitch`/`Cpu` separation, [ADR-0020](0020-cpu-trait-v2-context-switch.md)), and the 168-byte `Aarch64TaskContext` layout is untouched (no asm-offset drift). The `(user_entry, user_sp)` a task needs comes from the loader's [`LoadedImage`](../../kernel/src/obj/task_loader.rs) at creation time (the `task_create_from_image` B6 task), passed straight into `init_user_context` — they never need to persist on the `Task`.

**v1 simplification (cooperative, no preemption): `SPSR_EL1 = 0x3C0` (EL0t, `DAIF` masked).** v1's scheduler is cooperative; the EL0 "hello" task runs to its `console_write` + `task_exit` without preemption. Masking `DAIF` at EL0 keeps the cooperative no-preemption invariant (no timer IRQ interrupts the EL0 task) and matches the rest of the v1 model. **Preemptive EL0** (IRQ-at-EL0 → save the EL0 frame → reschedule → resume) is deferred to the preemption task (Phase C / a future ADR); it reuses the same trampoline with an unmasked-`I` `SPSR` and the IRQ vector's lower-EL path.

### Simulation

The worst-case interaction — the scheduler running a freshly-created EL0 task, the task trapping, and the abort path. `DAIF` masked at EL1 throughout the kernel-side handling.

| Step | State pre | Action | State post | Observable / verification |
|------|-----------|--------|------------|---------------------------|
| 0 | A user task's `Aarch64TaskContext` was `init_user_context`'d (`x19 = user_entry`, `x20 = user_sp`, `lr = enter_el0`, `sp = kernel_stack_top`); the scheduler selects it for its first run. | `context_switch_asm` (unchanged) restores `x19`/`x20`/`sp` from the context and `ret`s to `lr`. | `x19 = user_entry`, `x20 = user_sp`, `SP_EL1 = kernel_stack_top`, PC = `enter_el0`, still EL1h. | T-023 host test: `init_user_context` sets the four slots (asserted via the test-hal fake / the real `Aarch64TaskContext` fields). |
| 1 | At `enter_el0`, EL1h, on the task's kernel stack. | `MSR SP_EL0, x20` → `MSR ELR_EL1, x19` → `MSR SPSR_EL1, #0x3C0` → `ERET`. | PC at EL0 = `user_entry`, `SP = user_sp`, `DAIF` masked, `SP_EL1` retains `kernel_stack_top`. | QEMU smoke (B6 wire-up). For T-023: the asm assembles, the kernel boots unchanged (mechanism dormant, no caller). UNSAFE-2026-0032. |
| 2 | EL0 task runs; issues `SVC`. | CPU vectors to `VBAR_EL1+0x400` → `tyrne_sync_trampoline` switches to `SP_EL1` (= `kernel_stack_top`, still valid) and saves the 272-byte frame; routes to `syscall_entry`. | Kernel handles the syscall on the task's kernel stack; **gate #2 holds** (`SP_EL1` valid). | gate #2 closed by construction (no new `SP_EL1` register management). UNSAFE-2026-0029 (existing trampoline). |
| 3 | Syscall handled; directive is `Resume` (or `Reschedule`). | `Resume`: trampoline restores `ELR_EL1`/`SPSR_EL1`/`SP_EL0` from the frame and `ERET`s back to EL0. `Reschedule`: ordinary cooperative `yield_now` on the kernel side; on resume, the kernel frame in `syscall_entry` continues and `ERET`s back. | EL0 task resumes; `enter_el0` is **not** re-run. | B6 wire-up smoke (real `+0x400` round-trip). |
| 4 | Any precondition violated (e.g. `user_entry` unmapped in the task's `TTBR0`, or the user image absent). | `enter_el0`'s `ERET` faults on the first EL0 fetch → vectors to `VBAR_EL1` (high, mapped in `TTBR1`, present for every AS) → panic-class handler → halt. | Visible boot/run halt; no silent wrong-EL execution. | B6 QEMU smoke fail-stop (no `userspace greeting` marker). |

#### Simulation row-to-verification mapping

Per [`write-adr` skill §Procedure step 5](../../.agents/skills/write-adr/SKILL.md), each row maps to a verification artefact in [T-023](../analysis/tasks/phase-b/T-023-el0-entry-context.md):

- **Row 0** → host test pinning `init_user_context`'s slot assignment (`x19`/`x20`/`lr`/`sp`) + the scheduler `add_user_task` path.
- **Rows 1–3** → [UNSAFE-2026-0032](../audits/unsafe-log.md) (the `enter_el0` `ERET` asm) + the **B6 wire-up** QEMU smoke (the real EL0 `+0x400` round-trip — T-023 ships the dormant mechanism; the runtime proof is the wire-up task, the same staging T-021's `+0x400` handler used).
- **Row 4** → the B6 QEMU smoke abort gate (a wrong EL0 entry fail-stops before the userspace greeting marker).

### Dependency chain

For this decision to be **fully** in effect:

```text
1. ContextSwitch::init_user_context (additive HAL trait method) + the
   QemuVirtCpu impl (enter_el0 naked-asm trampoline) + the test-hal
   FakeContextSwitch impl.                                              — T-023 (opens with this ADR)
2. Scheduler add_user_task(handle, ash, user_entry, user_sp,
   kernel_stack_top) — mirrors add_task but calls init_user_context.    — T-023
3. UNSAFE-2026-0032 audit entry (the enter_el0 ERET asm; security-
   sensitive → second-reviewer per unsafe-policy §Review.4).            — T-023
```

Downstream consumers are **not** prerequisites of this ADR and are deliberately absent: `task_create_from_image` (the `LoadedImage` → runnable `Task`-cap bridge that calls `add_user_task`), the [gate #1](../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello) per-task user-VA translation, `userland/hello` + `tyrne-user`, and the wire-up smoke are separate B6 tasks opened *after* T-023.

## Consequences

### Positive

- **Zero layout drift.** `Aarch64TaskContext` (168 bytes) and `context_switch_asm`'s offsets are untouched; the cooperative switch is reused verbatim. The single highest-risk failure mode (asm/`repr(C)` drift) is avoided by construction.
- **Gate #2 closed for free.** Per-task `SP_EL1` is the task's kernel stack (restored by the existing switch); no separate `SP_EL1` slot to initialise or keep in sync.
- **Minimal, single-purpose `unsafe`.** One new naked-asm trampoline (`enter_el0`), audited, second-reviewer-gated; everything else is safe Rust (`init_user_context` writes plain `u64` context fields).
- **Kernel-object `Task` stays minimal** (`id + address_space_handle`); the EL0 register state is BSP/HAL-owned, matching the [ADR-0020](0020-cpu-trait-v2-context-switch.md) `ContextSwitch`/`Cpu` separation.

### Negative

- **Implicit register hand-off (`x19`/`x20`).** The `(user_entry, user_sp)` pair travels from `init_user_context` to `enter_el0` through two callee-saved slots rather than named struct fields — a small bit of low-level coupling. *Mitigation:* it is contained in exactly two well-commented sites (the init writer + the trampoline reader), pinned by a host test, and is the conventional way to pass initial arguments to a freshly-spawned thread; the alternative (named fields) costs the layout drift we are explicitly avoiding. **We accept this cost** because it removes the asm-offset-drift risk entirely.
- **`enter_el0` is not runtime-verifiable in T-023.** There is no EL0 task to enter yet, so T-023 proves only that the asm assembles and the kernel boots unchanged; the runtime `ERET`-to-EL0 proof is the B6 wire-up smoke. *Mitigation:* the same staging T-021 used for the `+0x400` handler; the asm is small, hand-traced in the audit entry, and second-reviewer-gated.

### Neutral

- **v1 masks `DAIF` at EL0** (no preemption). Preemptive EL0 reuses the same trampoline with an unmasked-`I` `SPSR` + the IRQ lower-EL path; deferred to the preemption task.
- **No change to the syscall return path.** The B5 trampoline's return-to-EL0 half is reused unchanged; this ADR adds only the first-entry half.

## Pros and cons of the options

### Option 1 — reuse `Aarch64TaskContext` + `enter_el0` trampoline (chosen)

- **Pro:** zero asm-layout drift; gate #2 closed by construction; reuses the verified cooperative switch + the B5 return-to-EL0 half; minimal single-purpose `unsafe`.
- **Pro:** kernel-object `Task` unchanged; one additive HAL trait method.
- **Con:** implicit `x19`/`x20` hand-off (mitigated: two commented sites + a host test).

### Option 2 — extend `Aarch64TaskContext` with explicit EL0 fields

- **Pro:** named `ELR_EL1`/`SPSR_EL1`/`SP_EL0` fields, no implicit register hand-off.
- **Con:** changes the 168-byte layout **and** the security-critical `context_switch_asm` byte offsets — the exact drift the size-assert exists to catch; a mistake corrupts *every* cooperative switch. Most of those fields are needed only once (first entry), so they would be dead weight on every kernel-thread context.

### Option 3 — separate `UserTaskContext` struct + a distinct enter-EL0 scheduler path

- **Pro:** clean separation of EL0 vs EL1 contexts.
- **Con:** duplicates the per-task storage + a parallel context-switch path for what the existing cooperative switch already does; more surface, more `unsafe`, more to keep in sync — against the minimum-surface driver.

## References

- [ADR-0033 — Kernel high-half migration](0033-kernel-high-half-migration.md) — freed `TTBR0_EL1`; named the EL0 context a separate B6 task (this ADR).
- [ADR-0020 — `Cpu` trait v2 + `ContextSwitch`](0020-cpu-trait-v2-context-switch.md) — the cooperative context-switch trait this ADR extends additively.
- [ADR-0030 — Syscall ABI](0030-syscall-abi.md) / [ADR-0031](0031-initial-syscall-set.md) — the syscall trampoline whose return-to-EL0 half is reused.
- [ADR-0024 — EL drop to EL1 policy](0024-el-drop-policy.md) — the boot-time EL1 establishment; this ADR is the symmetric EL1→EL0 first-entry.
- [phase-b.md §B6](../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello) — the milestone + the three T-021 carry-forward gates (this ADR + T-023 close gate #2).
- [T-022 high-half migration security review (2026-05-31)](../analysis/reviews/security-reviews/2026-05-31-T-022-high-half-migration.md) — flagged the `Aarch64TaskContext` layout-drift risk this ADR avoids.
- ARM *Architecture Reference Manual* (ARMv8-A) §D1 — `SPSR_EL1` format (`M[3:0]` = EL/SP-select, `DAIF` bits), `ERET` semantics (`PC ← ELR_EL1`, `PSTATE ← SPSR_EL1`).
