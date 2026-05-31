# T-023 — EL0 entry context: userspace register file + enter-EL0/`ERET` path + per-task `SP_EL1`

- **Phase:** B
- **Milestone:** B6 — First userspace "hello" (step 2 of the [B6 opening sequence](../../../roadmap/phases/phase-b.md#b6-opening-sequence--prerequisites); closes [T-021 carry-forward **gate #2**](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello))
- **Status:** Draft
- **Created:** 2026-05-31
- **Author:** @cemililik (+ Claude Opus 4.8 agent)
- **Dependencies:** [ADR-0037](../../../decisions/0037-el0-entry-context.md) — must be `Accepted` before code lands (settles the EL0 execution model + the reuse-`Aarch64TaskContext` decision + the `SPSR_EL1 = 0x3C0` v1 simplification); [ADR-0033](../../../decisions/0033-kernel-high-half-migration.md) (the high-half regime this runs on — kernel in `TTBR1`, `TTBR0` free); [ADR-0020](../../../decisions/0020-cpu-trait-v2-context-switch.md) (the `ContextSwitch` trait this extends additively); [ADR-0030/0031](../../../decisions/0030-syscall-abi.md) (the syscall trampoline's return-to-EL0 half this reuses).
- **Informs:** Closes [ADR-0037 §Dependency chain](../../../decisions/0037-el0-entry-context.md#dependency-chain) + gate #2. Unblocks `task_create_from_image` (which calls `add_user_task`), then gate #1 (per-task user-VA translation), then `userland/hello` + the wire-up smoke.
- **ADRs required:** [ADR-0037](../../../decisions/0037-el0-entry-context.md). Introduces **new** `UNSAFE-2026-0032` (the `enter_el0` `ERET`-into-EL0 naked-asm trampoline; security-sensitive → second-reviewer per [unsafe-policy §Review.4](../../../standards/unsafe-policy.md)).

---

## User story

As the kernel, I want a verified mechanism to start a task at EL0 — set its user entry PC, user stack, and EL0 `PSTATE`, and `ERET` into it on a valid per-task kernel stack — so that a later task (`task_create_from_image`) can turn a `LoadedImage` into a runnable userspace task, and a real EL0 trap (`+0x400`) lands on a valid `SP_EL1`.

## Context

[ADR-0037](../../../decisions/0037-el0-entry-context.md) settles the EL0 execution model: a userspace task is a kernel-managed task that drops to EL0 on first dispatch via a one-shot `enter_el0` trampoline, reusing the cooperative `context_switch` machinery and the B5 return-to-EL0 half. This task implements **only** that mechanism — it does **not** wire a runnable userspace task (no `task_create_from_image`, no `userland/hello` yet), so it is dormant until the wire-up task consumes it. This matches the staging the [T-021 `+0x400` handler](T-021-syscall-dispatch.md) used: install the mechanism now, runtime-prove it at wire-up.

`SP_EL1` (gate #2) is closed **by construction**: the task enters EL0 from its own kernel context, so `SP_EL1` retains that context's `sp` (the per-task kernel stack the switch restored); a later `+0x400` trap lands on it. No separate `SP_EL1` slot is introduced.

## Acceptance criteria

- [ ] **`ContextSwitch::init_user_context`** added to the HAL trait ([`hal/src/context_switch.rs`](../../../../hal/src/context_switch.rs)) as an additive sibling of `init_context`, with a `# Safety` section: `unsafe fn init_user_context(&self, ctx: &mut Self::TaskContext, user_entry: usize, user_sp: usize, kernel_stack_top: *mut u8)`.
- [ ] **`QemuVirtCpu::init_user_context`** ([`bsp-qemu-virt/src/cpu.rs`](../../../../bsp-qemu-virt/src/cpu.rs)) writes the existing `Aarch64TaskContext` (no layout change): `x19 = user_entry`, `x20 = user_sp`, `lr = enter_el0`, `sp = kernel_stack_top`. The 168-byte `size_of` assert is untouched.
- [ ] **`enter_el0` trampoline** (new `#[unsafe(naked)] unsafe extern "C" fn enter_el0() -> !`): reads `x19`/`x20`, `MSR SP_EL0, x20` → `MSR ELR_EL1, x19` → `MSR SPSR_EL1, #0x3C0` (EL0t, `DAIF` masked) → `ERET`. Audited **UNSAFE-2026-0032**.
- [ ] **`test-hal` `FakeContextSwitch`** (or equivalent) implements `init_user_context`, recording the args so the scheduler path is host-testable.
- [ ] **`Scheduler::add_user_task`** ([`kernel/src/sched/mod.rs`](../../../../kernel/src/sched/mod.rs)) mirrors `add_task` but calls `init_user_context` (raw-pointer / momentary-`&mut` discipline per [ADR-0021](../../../decisions/0021-raw-pointer-scheduler-ipc-bridge.md), no `&mut` across a switch).
- [ ] **Host tests**: `init_user_context` sets the four context slots; `add_user_task` routes through `init_user_context` with the right args (via the fake). The slot assignment (`x19`/`x20`) is pinned so a future refactor that breaks the `enter_el0` hand-off fails the test.
- [ ] **Audit:** new **UNSAFE-2026-0032** under the Operation / Invariants / Rejected-alternatives shape; second-reviewer-flagged.
- [ ] **All gates green:** host tests (+ the new ones); host + kernel clippy `-D warnings`; `cargo fmt --check`; kernel build (the `enter_el0` asm assembles); `cargo +nightly miri test --workspace --exclude tyrne-bsp-qemu-virt`. **QEMU smoke:** the kernel boots unchanged to `tyrne: all tasks complete` (the mechanism is dormant — no EL0 task yet — so the trace is byte-stable vs the post-T-022 baseline; the runtime `ERET`-to-EL0 proof is the B6 wire-up task).

## Out of scope

- `task_create_from_image` (the `LoadedImage` → runnable `CapHandle{CapObject::Task(...)}` bridge that calls `add_user_task`) — the next B6 task.
- The per-task `console_write` window + per-page user-VA→kernel-VA translation (gate #1) and the `SYSCALL_STUB_TABLE` → current-task-table swap (gate #3) — B6.
- `tyrne-user` + `userland/hello` + the build pipeline + the wire-up smoke (the runtime EL0 `+0x400` round-trip) — B6.
- Preemptive EL0 (IRQ-at-EL0 → reschedule; an unmasked-`I` `SPSR`) — deferred (ADR-0037 §Neutral).

## Approach

_(Settled at the ADR level — see [ADR-0037 §Decision outcome + §Simulation](../../../decisions/0037-el0-entry-context.md#simulation).)_ Reuse `Aarch64TaskContext` + a one-shot `enter_el0` trampoline; carry `(user_entry, user_sp)` in the `x19`/`x20` callee-saved slots the switch already restores; `SP_EL1` = the task's kernel stack. The trampoline is hand-asm (the `MSR SPSR_EL1`/`ERET` sequence cannot be expressed in safe Rust); it runs exactly once per task (first dispatch).

## Definition of done

All acceptance criteria checked; gates green (incl. Miri); UNSAFE-2026-0032 added; `current.md` updated; **security-relevant — flagged for explicit security review** (the `ERET`-into-EL0 asm is the EL1→EL0 trust-boundary primitive: a wrong `SPSR` is a privilege/isolation defect).

## Review history

- **2026-05-31 — Draft opened alongside [ADR-0037](../../../decisions/0037-el0-entry-context.md) (Proposed)**, in the same commit per [ADR-0025 §Rule 1](../../../decisions/0025-adr-governance-amendments.md). The EL0 execution model + the reuse-`Aarch64TaskContext` decision (vs extending the struct or a separate `UserTaskContext`) were settled in ADR-0037 to avoid `context_switch_asm` layout drift — the risk the [T-022 security review](../../reviews/security-reviews/2026-05-31-T-022-high-half-migration.md) explicitly flagged.
