# T-028 — EL0 userspace wire-up + the `+0x400` round-trip smoke (B6 step 6)

- **Phase:** B
- **Milestone:** B6 — First userspace "hello" (step 6 of the [B6 dependency-ordered sequence](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello) — a true EL0 task takes the lower-EL `VBAR_EL1+0x400` vector, the dispatcher copies `console_write` from its `TTBR0_EL1`, `ERET` returns to EL0, and `task_exit` terminates it — the EL0↔EL1 round-trip B5's `+0x200` proxy could not prove)
- **Status:** Draft (opened in the [ADR-0039](../../../decisions/0039-userland-build-pipeline.md) Propose commit per [ADR-0025 §Rule 1](../../../decisions/0025-adr-governance-amendments.md); implementation follows [T-027](T-027-userland-build-pipeline.md))
- **Created:** 2026-05-31
- **Author:** @cemililik (+ Claude Opus 4.8 agent)
- **Dependencies:** [T-027](T-027-userland-build-pipeline.md) (the embedded real `hello` image this loads + runs); [T-024](T-024-task-create-from-image.md) (`task_create_from_image` — the `LoadedImage` → runnable `CapHandle{CapObject::Task}` bridge); [T-019](T-019-task-loader.md) (`load_image`); [T-023](T-023-el0-entry-context.md) / [ADR-0037](../../../decisions/0037-el0-entry-context.md) (`add_user_task` + `init_user_context` + the `enter_el0`/`ERET` trampoline + per-task `SP_EL1`); [T-025](T-025-user-access-translation.md) (gate #1 — the translate-based copy the `console_write` buffer is checked through); [T-026](T-026-current-task-cap-table.md) (gate #3 — the scheduler sources the running task's table + AS + window); [T-022](T-022-high-half-kernel-mapping.md) / [ADR-0033](../../../decisions/0033-kernel-high-half-migration.md) (the high-half regime that keeps the kernel reachable from the task's `TTBR0`).
- **Informs:** Closes B6's functional milestone — the first real userspace program runs in EL0. Triggers the **explicit EL0-boundary security review** carried forward from the [T-026 Definition of done](T-026-current-task-cap-table.md) (now that the boundary is attacker-observable).
- **ADRs required:** **None** — composes the already-Accepted mechanisms (ADR-0033 high-half, ADR-0037 EL0 entry, ADR-0038 translate, ADR-0030/0031 syscall ABI). Any new `unsafe` in the wire-up (e.g. a per-task kernel stack) gets an audit-log entry per [unsafe-policy](../../../standards/unsafe-policy.md).

---

## User story

As the kernel, I want to load the embedded `hello` image into its own address space, create a runnable EL0 task from it, schedule it, and `ERET` into it — so that the task greets via a real `console_write` syscall taking the lower-EL `+0x400` vector (copied from its own `TTBR0_EL1`, gate-#1-checked) and exits via `task_exit`, proving the EL0↔EL1 round-trip end-to-end.

## Context

Every B6 mechanism is in place and merged: high-half ([T-022](T-022-high-half-kernel-mapping.md)) keeps the kernel reachable from a task's `TTBR0`; the loader ([T-019](T-019-task-loader.md)) + `task_create_from_image` ([T-024](T-024-task-create-from-image.md)) turn a raw image into a runnable Task cap; `add_user_task` + `enter_el0` ([T-023](T-023-el0-entry-context.md)) seed and drop to EL0 with a register scrub; gate #1 ([T-025](T-025-user-access-translation.md)) translate-checks the `console_write` buffer; gate #3 ([T-026](T-026-current-task-cap-table.md)) sources the running task's table + AS + window. T-027 produces the real `hello` image. T-028 is the **wire-up**: it replaces the boot-time loader smoke (which loads + discards) with the full load → create → schedule → run path, and replaces the dormant `+0x200` fail-closed smoke with the live `+0x400` round-trip.

## Acceptance criteria

- [ ] **Load + create:** on boot, `load_image(USERSPACE_IMAGE, …)` → `task_create_from_image(&loaded, …)` mints the EL0 task cap (replacing the load-and-discard smoke).
- [ ] **Per-task capability table seeded:** a `CapabilityTable` for the EL0 task holding a **`DebugConsole`** capability (`CapRights::CONSOLE_WRITE`) at the handle the `hello` program names; bound to the task via `add_user_task`'s `cap_table` parameter (gate #3 — [T-026](T-026-current-task-cap-table.md)). The handle value `hello` hard-codes and the seeded slot must agree.
- [ ] **Per-task kernel stack:** a valid, 16-byte-aligned `SP_EL1` kernel stack (≥ the 272-byte trap frame + the gate-#1 dispatch call-tree depth) passed to `add_user_task` (the EL0→EL1 trap runs the trampoline's `sub sp, sp, #272` on `SP_EL1`, which the CPU does **not** auto-initialise — [T-023](T-023-el0-entry-context.md) gate #2). Source (BSP static vs PMM-allocated) decided in implementation; asserted non-null + aligned.
- [ ] **Schedule + run:** `add_user_task(…)` enqueues the task Ready; the scheduler `start()`/dispatch activates the task's AS (`TTBR0_EL1` installed, `EPD0` cleared — the activation hook fires by construction, [ADR-0028](../../../decisions/0028-address-space-data-structure.md)) and `enter_el0` `ERET`s into EL0 at `entry_va`.
- [ ] **`+0x400` round-trip:** the `hello` `console_write` SVC traps to the **lower-EL** sync vector (`VBAR_EL1+0x400`), `syscall_entry` resolves the task's own table + window + AS (gate #3), gate #1 translates the buffer through the task's `TTBR0`, the dispatcher copies + emits, `x0` = status, the trampoline `ERET`s back to EL0 — the round-trip B5's `+0x200` proxy could not prove.
- [ ] **Clean exit:** the `hello` `task_exit` SVC terminates the task; the kernel reports termination and continues (the cooperative demo still reaches `tyrne: all tasks complete` or the documented post-EL0 shutdown line).
- [ ] **QEMU smoke (acceptance):** the serial trace shows the kernel greeting, then **"hello from userspace"** (or the chosen greeting) in the correct order, then clean `task_exit`; `-d int` shows the `+0x400` lower-EL `SVC` exception (EL0→EL1) with a clean `ERET`; **no new fault class**.
- [ ] **Explicit EL0-boundary security review** (the [T-026](T-026-current-task-cap-table.md) carry-forward DoD): a review of the now-attacker-observable boundary covering gate #1 ([UNSAFE-2026-0030](../../../audits/unsafe-log.md)), gate #2 ([UNSAFE-2026-0032](../../../audits/unsafe-log.md)), the gate-#3 cap-table sourcing (UNSAFE-2026-0014 Amendment), and the register scrub — filed under `docs/analysis/reviews/security-reviews/`.
- [ ] **All gates green:** `cargo fmt --all --check`; host + kernel clippy `-D warnings`; host tests (+ any wire-up regression tests) green; `cargo kernel-build`; `tools/smoke.sh` PASS (the round-trip trace above); Miri 0 UB; any new `unsafe` audited.

## Out of scope

- **The build pipeline + the `hello`/`tyrne-user` crates** — [T-027](T-027-userland-build-pipeline.md).
- **Multiple EL0 tasks / per-task cap-table arena** — later (the BSP-static single-task shape suffices for B6; a registry is a later ADR if outgrown).
- **Per-section permissions (ADR-0034)** + **EL0 non-`SVC` fault containment** (illegal instruction / unmapped deref) — later-phase (the dispatcher is already panic-free; fault containment is Phase E / flag K3-4).
- **The B6 closure trio** (guide + performance cycle + Phase B retrospective) — [B6 step 7](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello).

## Approach

Replace the boot-time loader smoke with the full path: `load_image` → `task_create_from_image` → seed a `CapabilityTable` with a `DebugConsole` cap at the handle `hello` names → `add_user_task` (binding the table + a per-task `SP_EL1` stack) → let the scheduler activate the task's AS and `enter_el0`. The `hello` greeting buffer is a user VA inside `[entry_va, stack_top_va)`, so gate #1 translates it through the task's own `TTBR0` and the gate-#3 window admits it. Retire the dormant `+0x200` fail-closed smoke (its property is now covered by host tests) in favour of the live `+0x400` round-trip. Because this is the first attacker-observable EL0 boundary, the explicit security review is part of the Definition of done — not deferred.

## Definition of done

All acceptance criteria checked; gates green (incl. Miri); the `+0x400` round-trip demonstrated in the smoke trace; the explicit EL0-boundary security review filed (**Approve** before merge); `current.md` + [phase-b.md §B6](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello) updated. Lands **after** [T-027](T-027-userland-build-pipeline.md). Closes B6's functional milestone; the closure trio (step 7 — Phase B retrospective) follows.

## Review history

- **2026-05-31 — opened Draft** in the [ADR-0039](../../../decisions/0039-userland-build-pipeline.md) Propose commit (the ADR's dependency chain names it — step 6; [ADR-0025 §Rule 1](../../../decisions/0025-adr-governance-amendments.md)). Composes already-Accepted mechanisms; no ADR of its own. Implementation follows T-027.
