# T-021 — EL0→EL1 `SVC` dispatch: trap trampoline, panic-free dispatcher, copy-from/to-user

- **Phase:** B
- **Milestone:** B5 — Syscall boundary (this task is B5's trap/dispatch implementation — the EL0→EL1 `SVC` path that instantiates [ADR-0030](../../../decisions/0030-syscall-abi.md)'s convention and [ADR-0031](../../../decisions/0031-initial-syscall-set.md)'s syscall set)
- **Status:** Ready
- **Created:** 2026-05-29
- **Author:** @cemililik (+ Claude Opus 4.8 agent)
- **Dependencies:** [ADR-0030](../../../decisions/0030-syscall-abi.md) + [ADR-0031](../../../decisions/0031-initial-syscall-set.md) (both `Accepted`); [T-020](T-020-syscall-error-taxonomy.md) (the granular `IpcError` + redacted `Capability` `Debug` the dispatcher composes/relies on); [T-012](T-012-exception-and-irq-infrastructure.md) (the `VBAR_EL1` vector table the EL0-sync vector slots into); [T-013](T-013-el-drop-to-el1.md) (EL drop to EL1).
- **Informs:** Closes [ADR-0030 §Dependency chain steps 2–5](../../../decisions/0030-syscall-abi.md#dependency-chain) and [ADR-0031 §Dependency chain steps 2–5](../../../decisions/0031-initial-syscall-set.md#dependency-chain), and discharges every [ADR-0031 §Simulation](../../../decisions/0031-initial-syscall-set.md#simulation) row + [ADR-0030 §Simulation](../../../decisions/0030-syscall-abi.md#simulation) rows 0/1/2/4/5. Unblocks Phase B6 (first userspace "hello"); the deferred `task_create_from_image` wrapper ([phase-b §B4 §Revision-notes](../../../roadmap/phases/phase-b.md#milestone-b4--task-loader)) composes on top.
- **ADRs required:** [ADR-0030](../../../decisions/0030-syscall-abi.md), [ADR-0031](../../../decisions/0031-initial-syscall-set.md). Will introduce at least one new `UNSAFE-YYYY-NNNN` audit entry for the trap-frame save/restore asm (per [unsafe-policy](../../../standards/unsafe-policy.md)).

---

## User story

As the kernel, I want a userspace `SVC #0` to land in the EL1 sync vector, save the caller's registers, decode the syscall number, validate the caller's capabilities, perform the operation through an existing kernel primitive, encode a typed result, and `ERET` back to EL0 — **never panicking on any untrusted input** — so that EL0 code can call the kernel safely and a bad number / missing capability / out-of-bounds pointer returns a typed `SyscallError` instead of taking down the kernel.

## Context

[T-020](T-020-syscall-error-taxonomy.md) landed the pure-Rust foundation (the granular `IpcError`, the redacted `Capability` `Debug`). This task lands the **hardware-facing** half of B5 and is deliberately a separate task: the EL0→EL1 trap is the single most security-sensitive boundary in the system, involves hand-written register-save asm and `unsafe`, and warrants its own focused review rather than being bundled with the error-taxonomy refactor (CLAUDE.md §6).

A structural constraint shapes this task's *runtime* verification, and the vector path it can actually exercise. A **real** EL0 task cannot yet take the trap, because the loaded userspace address space holds only image + stack (no kernel mappings, so the EL1 vector fetch would translation-fault) and the `Task` struct carries no EL0 context register file — both gated on the [ADR-0033 high-half placeholder](../../../decisions/0027-kernel-virtual-memory-layout.md) and Phase B6.

Crucially, the only `SVC` this milestone can drive comes from an **EL1 kernel-stub**, and an `SVC` issued at EL1 takes the **current-EL-with-SPx** sync vector at `VBAR_EL1 + 0x200` — **not** the lower-EL (EL0) sync vector at `+0x400`. So B5's acceptance criterion #7 proves the *shared* dispatcher / trap-frame / `ERET` mechanism via the `0x200` self-`SVC` path; it does **not** prove the `0x400` vector entry, the EL0↔EL1 privilege transition, or copy-user against a separate userspace `TTBR0_EL1` AS. Those are runtime-verified in **B6** with the first real EL0 task, per [ADR-0030 §Simulation row-to-verification mapping](../../../decisions/0030-syscall-abi.md#simulation). This task therefore installs the dispatcher at *both* the `0x200` and `0x400` sync slots (the handler is privilege-entry-agnostic) but only the `0x200` path runs at B5; host tests carry the rest of the dispatcher's correctness.

## Acceptance criteria

- [ ] The Rust dispatcher is installed at **both** sync exception-vector slots — current-EL-with-SPx (`VBAR_EL1 + 0x200`, the EL1 self-`SVC` path B5 exercises) and lower-EL-AArch64 (`VBAR_EL1 + 0x400`, the real EL0 path verified in B6). The vector entry saves `x0`–`x30` + `SP_EL0` to a trap frame and, on `ESR_EL1.EC == SVC64`, routes to the dispatcher; other sync causes route to the existing fault path (out of scope here).
- [ ] A panic-free dispatcher decodes `x8`: number `0` and any number outside the v1 set return `SyscallError::BadSyscallNumber`; numbers `1`–`5` dispatch to handlers for `send` / `recv` / `task_yield` / `task_exit` / `console_write` per [ADR-0031](../../../decisions/0031-initial-syscall-set.md). No path can `panic!`/`unwrap`/`expect` on register-supplied input.
- [ ] **Every object-naming syscall performs a capability check** ([P1 / P4](../../../standards/architectural-principles.md)): `send`/`recv` validate the endpoint cap; `console_write` validates a **debug-console capability** (its `x0` arg) — a new `CapObject` kind introduced here — before any output. `task_yield`/`task_exit` act only on the trusted current-task identity (no object-cap argument).
- [ ] `SyscallError` (per [ADR-0030](../../../decisions/0030-syscall-abi.md)) lands with `From<CapError>` / `From<IpcError>` impls and a stable numeric status encoding host-tested against the fixed [ADR-0031](../../../decisions/0031-initial-syscall-set.md) numbers; `0` is reserved for `Ok`.
- [ ] `copy_from_user` / `copy_to_user` validate the byte range against the **active** address space and never dereference a raw user pointer outside a validated mapping; `console_write`'s buffer goes through `copy_from_user` **after** its capability check passes.
- [ ] `console_write` carries **two independent gates**: the capability check above (all builds) and the release debug-gate — absent (returns `BadSyscallNumber`) in non-debug builds (mechanism chosen here, recorded in §Design notes).
- [ ] Host ABI encode/decode tests cover: number decode (incl. `0`/out-of-range), the debug-console **capability-check-fails** path, `From<IpcError>`/`From<CapError>` round-trips, `RecvOutcome`+`Message`+`Option<CapHandle>` register packing, and copy-from/to-user range validation (in-range, out-of-range, zero-length, wrap).
- [ ] QEMU smoke: an EL1 kernel-stub issues an `SVC` (taking the current-EL `0x200` sync vector) and the trace shows the round-trip (and, for `console_write` with a granted debug-console cap, the emitted bytes). New `UNSAFE-YYYY-NNNN` audit entry for the trap-frame asm. **(The real EL0 `0x400` round-trip is B6's smoke, not this task's.)**
- [ ] All gates green incl. `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt`.

## Out of scope

- A real EL0 task taking the trap, the per-task EL0 context register file, kernel mappings in the userspace AS, and therefore the **runtime proof of the lower-EL `0x400` vector + EL0↔EL1 transition + userspace-AS copy-user** — Phase B6 + the [ADR-0033 high-half placeholder](../../../decisions/0027-kernel-virtual-memory-layout.md). (This task installs the `0x400` handler but only runtime-exercises the `0x200` current-EL path.)
- Granting the debug-console capability to a userspace task (this task defines the cap kind + the check; the grant-at-load wiring is B6) — Phase B6.
- The `tyrne-user` safe wrapper crate and the `userland/hello` binary — Phase B6.
- `notify` / capability-management / address-space syscalls — not in the [ADR-0031](../../../decisions/0031-initial-syscall-set.md) v1 set.
- Full fault containment / supervisor endpoint (a crashing task's parent observes the fault) — Phase E per [phase-b §B5 flag K3-4](../../../roadmap/phases/phase-b.md#flags-to-resolve-during-b5).

## Approach

_(Settled at the ADR level; detailed approach filled when the task moves to In Progress.)_ The vector entry mirrors [T-012](T-012-exception-and-irq-infrastructure.md)'s trampoline discipline (save GPRs to a frame, call Rust, restore, `ERET`); the dispatcher is a `match` over the decoded number into thin handlers over `ipc_send`/`ipc_recv`/`yield_now`/console/terminate; copy-from/to-user walks the active translation to bound-check before any access. The §Simulation tables in [ADR-0030](../../../decisions/0030-syscall-abi.md#simulation) and [ADR-0031](../../../decisions/0031-initial-syscall-set.md#simulation) are the row-by-row spec; this task discharges all rows except ADR-0030 row 3 (T-020's).

## Definition of done

All acceptance criteria checked; gates green (incl. Miri); audit-log entry added; `current.md` updated; **security-relevant** — flagged for explicit security review per CLAUDE.md.

## Design notes

- _(Filled when the task moves to In Progress — debug-gate mechanism choice, trap-frame layout, copy-user bound-check strategy.)_

## Review history

- _(filled on close)_
