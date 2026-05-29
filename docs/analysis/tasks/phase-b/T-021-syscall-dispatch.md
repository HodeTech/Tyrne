# T-021 — EL0→EL1 `SVC` dispatch: trap trampoline, panic-free dispatcher, copy-from/to-user

- **Phase:** B
- **Milestone:** B5 — Syscall boundary (this task is B5's trap/dispatch implementation — the EL0→EL1 `SVC` path that instantiates [ADR-0030](../../../decisions/0030-syscall-abi.md)'s convention and [ADR-0031](../../../decisions/0031-initial-syscall-set.md)'s syscall set)
- **Status:** In Review
- **Created:** 2026-05-29
- **In Progress:** 2026-05-29
- **In Review:** 2026-05-29
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

- [x] The Rust dispatcher is installed at **both** sync exception-vector slots — current-EL-with-SPx (`VBAR_EL1 + 0x200`, the EL1 self-`SVC` path B5 exercises) and lower-EL-AArch64 (`VBAR_EL1 + 0x400`, the real EL0 path verified in B6). The vector entry saves `x0`–`x30` + `SP_EL0` to a trap frame and, on `ESR_EL1.EC == SVC64`, routes to the dispatcher; other sync causes route to the existing fault path (out of scope here).
- [x] A panic-free dispatcher decodes `x8`: number `0` and any number outside the v1 set return `SyscallError::BadSyscallNumber`; numbers `1`–`5` dispatch to handlers for `send` / `recv` / `task_yield` / `task_exit` / `console_write` per [ADR-0031](../../../decisions/0031-initial-syscall-set.md). No path can `panic!`/`unwrap`/`expect` on register-supplied input.
- [x] **Every object-naming syscall performs a capability check** ([P1 / P4](../../../standards/architectural-principles.md)): `send`/`recv` validate the endpoint cap; `console_write` validates a **debug-console capability** (its `x0` arg) — a new `CapObject` kind introduced here — before any output. `task_yield`/`task_exit` act only on the trusted current-task identity (no object-cap argument).
- [x] `SyscallError` (per [ADR-0030](../../../decisions/0030-syscall-abi.md)) lands with `From<CapError>` / `From<IpcError>` impls and a stable numeric status encoding host-tested against the fixed [ADR-0031](../../../decisions/0031-initial-syscall-set.md) numbers; `0` is reserved for `Ok`.
- [x] `copy_from_user` / `copy_to_user` validate the byte range against the **active** address space and never dereference a raw user pointer outside a validated mapping; `console_write`'s buffer goes through `copy_from_user` **after** its capability check passes.
- [x] `console_write` carries **two independent gates**: the capability check above (all builds) and the release debug-gate — absent (returns `BadSyscallNumber`) in non-debug builds (mechanism chosen here, recorded in §Design notes).
- [x] Host ABI encode/decode tests cover: number decode (incl. `0`/out-of-range), the debug-console **capability-check-fails** path, `From<IpcError>`/`From<CapError>` round-trips, `RecvOutcome`+`Message`+`Option<CapHandle>` register packing, and copy-from/to-user range validation (in-range, out-of-range, zero-length, wrap).
- [x] QEMU smoke: an EL1 kernel-stub issues an `SVC` (taking the current-EL `0x200` sync vector) and the trace shows the round-trip (and, for `console_write` with a granted debug-console cap, the emitted bytes). New `UNSAFE-YYYY-NNNN` audit entry for the trap-frame asm. **(The real EL0 `0x400` round-trip is B6's smoke, not this task's.)**
- [x] All gates green incl. `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt`.

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

### Module split (kernel ↔ BSP)

The implementation deliberately splits along the HAL line ([P6](../../../standards/architectural-principles.md)):

- **`tyrne-kernel`** (`kernel/src/syscall/`, architecture-agnostic, host-testable, panic-free):
  - `error.rs` — `SyscallError` + `From<CapError>` / `From<IpcError>` + the stable numeric status encoding.
  - `abi.rs` — `SyscallNumber` decode (with the debug-gate), the register frame types (`SyscallArgs` / `SyscallReturn` / `SyscallEffect`), and the value↔register packing (`Message`, outcomes, `Option<CapHandle>` with the null sentinel).
  - `user_access.rs` — `UserAccessWindow` + `copy_from_user` / `copy_to_user`.
  - `dispatch.rs` — the `dispatch` entry point, the per-syscall handlers, the `SyscallContext`, and the debug-console capability check.
- **`tyrne-bsp-qemu-virt`** (hardware-facing):
  - `vectors.s` — `tyrne_sync_trampoline`, installed at **both** `VBAR_EL1 + 0x200` (current-EL, the B5 path) and `+0x400` (lower-EL AArch64, the B6 EL0 path).
  - `syscall.rs` — `SyscallTrapFrame` (`#[repr(C)]`) + `syscall_entry` (reads the frame, builds a `SyscallContext` from the BSP statics, calls `dispatch`, writes the result back).
  - `main.rs` — `syscall_boundary_smoke` (the EL1 kernel-stub `SVC` caller) + the `SYSCALL_STUB_TABLE` static.

### Debug-gate mechanism (chosen: `cfg!(debug_assertions)` match guard)

`SyscallNumber::decode` recognises `console_write`'s number `5` only under `5 if cfg!(debug_assertions)`; in a release build it falls through to `None`, so the dispatcher returns `BadSyscallNumber` and the debug console is absent from the production surface even for a capability holder. Chosen over a Cargo feature because: (a) zero manifest wiring; (b) it matches the kernel's existing `debug_assertions` discipline (`debug_assert!` sites); (c) the `[profile.release]` in `Cargo.toml` leaves `debug-assertions` at its default (off in release, on in dev/host-test), so the gate is correct by construction; (d) `cfg!` (a runtime const-bool), **not** `#[cfg]`, keeps the `ConsoleWrite` match arm compiled and referenced in every build — so no dead-code warning arises in release. The two complementary tests `console_write_is_a_syscall_in_debug_builds` / `console_write_is_absent_in_release_builds` (and the six `#[cfg(debug_assertions)]`-gated functional `console_write` dispatch tests) pin both halves; `cargo test --release` exercises the release path.

### Trap-frame layout (272 bytes, full register file)

`SyscallTrapFrame` saves the **full** GPR set `x0`–`x30` plus `SP_EL0`, `ELR_EL1`, `SPSR_EL1` — 17 register pairs = 272 bytes, 16-byte aligned. This is deliberately larger than the IRQ `TrapFrame` (192 bytes, AAPCS64 caller-saved only): the syscall path must be a *complete* snapshot of the trapped context, the shape a real EL0 task (B6) and any future preemption arc require, and it must save `SP_EL0` (the EL0 stack for the `+0x400` path). The asm `stp` offsets in `vectors.s` mirror the `#[repr(C)]` field order; a `const _: () = assert!(size_of::<SyscallTrapFrame>() == 272)` guard fails the build on drift (mirrors the IRQ frame's guard). The handler writes only `x0`–`x7` (status + payload) back; the trampoline restores `x8`–`x30` + `SP_EL0` + `ELR_EL1` + `SPSR_EL1` to their trapped values, so the ABI-clobbered `x8`–`x18` are in fact preserved (a harmless superset). On `ESR_EL1.EC == 0x15` (SVC64) the trampoline calls `syscall_entry`; any other sync cause branches to the existing `panic_entry` (out of scope here).

### Copy-from/to-user bound-check strategy (`UserAccessWindow`)

`UserAccessWindow` models the active address space's user-accessible region as a single contiguous half-open VA window `[base, base + len)`. `copy_from_user` / `copy_to_user` call `validate(ptr, len)` first: a zero-length access is trivially OK (no bytes touched); a range whose end overflows `usize` is rejected (`checked_add`, the wrap case); a range not wholly contained in the window is rejected. Only on `Ok` is the pointer dereferenced (via `core::ptr::copy_nonoverlapping`), so the kernel never touches an unvalidated user pointer. `console_write` validates the **whole** range up front (so a faulting buffer emits nothing — no partial output) then copies + emits in 256-byte chunks through a kernel stack buffer (bounding stack footprint regardless of `len`). In v1 the deref relies on the bootstrap AS's identity map ([ADR-0027](../../../decisions/0027-kernel-virtual-memory-layout.md) §Decision outcome (a)); the **B6 forward path** ([ADR-0033](../../../decisions/0027-kernel-virtual-memory-layout.md) high-half placeholder) replaces the int-to-pointer deref with a per-page user-VA → kernel-VA translation and derives a tighter window from the EL0 task's mapped region — **without** changing the `copy_*` call-site signatures or the window-containment/wrap/zero-length logic. Host tests pin in-range / out-of-range / overrun / zero-length / wrap; the Miri-clean test pattern exposes a real host `Vec<u8>`'s provenance via `as usize` (matching `pmm.rs` / `task_loader.rs`).

### Data-plane vs. control-plane (the `SyscallEffect` directive)

`send` / `recv` / `console_write` are **data-plane**: they complete inside the dispatcher (over IPC arena/queues, the cap table, the console, and validated user memory) and produce `SyscallEffect::Resume(SyscallReturn)`. `task_yield` / `task_exit` are **control-plane**: they touch the scheduler, which is raw-pointer-wired and generic over the BSP CPU ([ADR-0021](../../../decisions/0021-raw-pointer-scheduler-ipc-bridge.md)), so the dispatcher returns a `Reschedule` / `Terminate(code)` *directive* instead of calling the scheduler directly. This keeps `dispatch` pure and host-testable without a live scheduler, and matches [ADR-0031](../../../decisions/0031-initial-syscall-set.md)'s "B5 lands the dispatch; real EL0 yield/termination is B6" split — in B5 the smoke runs the stub before `start()`, so the BSP glue treats both directives as documented stand-ins (write `Ok` status); the dispatcher-level routing (number → directive) is host-tested.

### Debug-console capability (the new `CapObject` kind)

`console_write` is gated on a new `CapObject::DebugConsole` (a **unit** variant — the debug console is a singleton with no arena-backed kernel object, so it carries no handle, the smallest object addition per [ADR-0031](../../../decisions/0031-initial-syscall-set.md)) plus a new `CapRights::CONSOLE_WRITE` bit (`1 << 7`, added to `KNOWN_BITS`). The check — `resolve → kind == DebugConsole → carries CONSOLE_WRITE` — mirrors the IPC `validate_ep_cap` order and returns the in-kernel `CapError` (`InvalidHandle` / `WrongKind` / `InsufficientRights`) which composes into `SyscallError::Cap`. The check runs in **all** builds (the [P1/P4](../../../standards/architectural-principles.md) authority gate); the debug-gate is the independent second gate.

### Stable `SyscallError` status encoding

`0` = `Ok` (reserved); `1`–`3` = the top-level variants (`BadSyscallNumber` / `BadArgument` / `FaultAddress`); `0x101`–`0x107` = `Cap(_)` (`0x100 | cap_code`); `0x201`–`0x207` = `Ipc(_)` (`0x200 | ipc_code`). The per-variant encoders match `CapError` / `IpcError` **exhaustively without a wildcard** (same crate, despite `#[non_exhaustive]`), so adding a variant to either is a compile error here until its stable code is assigned — the safeguard a stable ABI wants. Pinned by the `error.rs` host tests.

### Two new `unsafe` audit entries

- **[UNSAFE-2026-0029](../../../audits/unsafe-log.md#unsafe-2026-0029--svc-sync-trap-trampoline--syscall_entry-register-frame-access)** — the `SVC` sync trampoline asm + `syscall_entry`'s frame reads/writes (distinct from the IRQ path's UNSAFE-2026-0020: larger frame, sync cause + `ESR` decode, result write-back).
- **[UNSAFE-2026-0030](../../../audits/unsafe-log.md#unsafe-2026-0030--validated-copy-fromto-user-byte-move-via-coreptrcopy_nonoverlapping)** — the validated copy-from/to-user byte move (distinct from the loader's UNSAFE-2026-0027: copy across the userspace trust boundary, gated by `UserAccessWindow::validate`).

## Review history

- **2026-05-29 — implementation landed (Draft → In Progress → In Review).** Lands across the kernel `syscall` module (4 files) + cap-system additions (`CapRights::CONSOLE_WRITE`, `CapObject::DebugConsole`, `CapHandle::from_raw`) + the BSP trap trampoline (`vectors.s` `tyrne_sync_trampoline` at `0x200`/`0x400`) + `syscall.rs` (`SyscallTrapFrame` + `syscall_entry`) + the `kernel_entry` `SVC` smoke. **Gates:** `cargo fmt --check`, `cargo host-clippy -D warnings`, `cargo kernel-clippy -D warnings`, `cargo kernel-build` all clean; **host tests 236** (was 196 — +40 syscall tests), 43 hal + 53 test-hal unchanged; `cargo test --release` green (the debug-gate release-path tests); `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` clean (permissive provenance, matching the kernel's established int-to-pointer test pattern). **QEMU smoke (debug):** the two new lines `tyrne: hello from the syscall boundary (console_write via SVC)` + `tyrne: syscall smoke ok (console_write status=0x0, bytes=63; bad-number status=0x1)` appear after the `timer ready` banner and before `starting cooperative scheduler`; `-d int,unimp,guest_errors` shows exactly **two** `SVC` exceptions taken at the current-EL vector (`from EL1 to EL1 ... with ESR 0x15/0x56000000` — EC = SVC64), each `ERET`ing cleanly, plus only the pre-existing PL011-disabled-UART warnings (no new fault class); the full demo still runs to `tyrne: all tasks complete`. Two new audit entries (UNSAFE-2026-0029 / 0030). **Security-relevant** — flagged for explicit security review per CLAUDE.md §non-negotiable #1 (the EL0→EL1 trust boundary).
