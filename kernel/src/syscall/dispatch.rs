//! The panic-free syscall dispatcher.
//!
//! [`dispatch`] decodes the `x8` syscall number, validates the caller's
//! capabilities, performs the operation through an existing kernel primitive,
//! and produces a [`SyscallEffect`] for the BSP trampoline to apply. It is the
//! single most security-sensitive control-flow join in the kernel, so it is
//! held to one hard rule from [ADR-0030][adr-0030] / B0's hardening pattern:
//!
//! > **No path may `panic!` / `unwrap` / `expect` on any register-supplied
//! > input.** Every failure — bad number, missing/stale/wrong-kind capability,
//! > out-of-bounds pointer — returns a typed [`SyscallError`] as a value.
//!
//! The dispatcher operates on the **data plane** (capabilities, IPC, console,
//! user memory) and is pure, host-testable Rust over kernel state references.
//! The two **control-plane** syscalls (`task_yield` / `task_exit`) return a
//! [`SyscallEffect`] directive instead of touching the scheduler directly,
//! because the scheduler is raw-pointer-wired per [ADR-0021][adr-0021] and
//! generic over the BSP CPU — keeping them as directives keeps `dispatch`
//! testable without a live scheduler and matches [ADR-0031][adr-0031]'s "B5
//! lands the dispatch; real EL0 yield/termination is B6" split.
//!
//! Every object-naming syscall performs a capability check before any effect
//! ([P1 / P4][principles]): `send` / `recv` validate the endpoint capability
//! inside [`ipc_send`] / [`ipc_recv`]; `console_write` validates a debug-console
//! capability here before a single byte is emitted. `task_yield` / `task_exit`
//! act only on the trusted current-task identity (no object-capability argument).
//!
//! [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
//! [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md
//! [adr-0021]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0021-raw-pointer-scheduler-ipc-bridge.md
//! [principles]: https://github.com/HodeTech/Tyrne/blob/main/docs/standards/architectural-principles.md

use tyrne_hal::{Console, Mmu};

use crate::cap::{CapError, CapHandle, CapKind, CapRights, CapabilityTable};
use crate::ipc::{ipc_recv, ipc_send, IpcQueues};
use crate::obj::EndpointArena;

use super::abi::{
    decode_required_cap_handle, decode_send_message, encode_recv_outcome, encode_send_outcome,
    SyscallArgs, SyscallEffect, SyscallNumber, SyscallReturn,
};
use super::error::SyscallError;
use super::user_access::{copy_from_user, probe_user_pages, UserAccessWindow};

/// Maximum bytes `console_write` stages through its kernel stack buffer per
/// chunk. The handler validates the whole `[ptr, ptr + len)` range up front,
/// then copies and emits in chunks of this size — bounding the kernel-stack
/// footprint regardless of the userspace length argument.
const CONSOLE_WRITE_CHUNK: usize = 256;

/// The kernel state a single syscall dispatch reads and mutates.
///
/// The BSP trampoline builds this from its statics (the active task's IPC
/// arena / queues, the caller's capability table, the console, and the active
/// address space's user-access window) and hands it to [`dispatch`] for the
/// duration of one syscall. The borrows live only across the dispatch call —
/// they never cross a context switch, honouring the [ADR-0021][adr-0021]
/// no-`&mut`-across-switch discipline (the data-plane syscalls do not switch;
/// the control-plane ones return a directive *before* any switch happens).
///
/// `caller_table` is the **current task's** capability table. In B5 the only
/// `SVC` comes from an EL1 kernel-stub, so the BSP passes a dedicated stub
/// table; B6 wires the scheduler's current-task table once a real EL0 task
/// exists (gate #3 / T-026). Either way the dispatcher never lets a syscall
/// name a capability outside this one table — the per-subject unforgeability
/// [ADR-0014][adr-0014] guarantees.
///
/// `mmu` + `task_as` are the translation surface `console_write`'s copy-from-user
/// resolves user pointers through (gate #1 / [ADR-0038][adr-0038]): every user
/// page is translated through the running task's own address space and checked
/// for `USER` access before a byte is read. Generic over `M: Mmu` so the
/// dispatcher stays architecture-agnostic and host-testable against `FakeMmu`.
///
/// [adr-0021]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0021-raw-pointer-scheduler-ipc-bridge.md
/// [adr-0014]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0014-capability-representation.md
/// [adr-0038]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0038-mmu-translate-and-user-access.md
pub struct SyscallContext<'a, M: Mmu> {
    /// The endpoint kernel-object arena `send` / `recv` resolve handles against.
    pub ep_arena: &'a mut EndpointArena,
    /// The IPC waiter-state queues `send` / `recv` advance.
    pub queues: &'a mut IpcQueues,
    /// The calling task's capability table — the only table any syscall in this
    /// dispatch may name a capability in.
    pub caller_table: &'a mut CapabilityTable,
    /// The debug console `console_write` emits to after its capability check.
    pub console: &'a dyn Console,
    /// The active address space's user-accessible window — the cheap range
    /// first-gate `console_write`'s copy-from-user validates against.
    pub user_window: UserAccessWindow,
    /// The MMU used to translate user pointers per page (gate #1).
    pub mmu: &'a M,
    /// The running task's address space — the translation regime user pointers
    /// are resolved through. Sourced from the scheduler's current task in B6
    /// (gate #3 / T-026); in B5 it is the EL1 stub's bootstrap AS.
    pub task_as: &'a M::AddressSpace,
    /// Whether a running EL0 task is current (gate #3 / T-026). The BSP sets it
    /// `true` only when the running task's capability table, user-access window,
    /// and (generation-checked) address space **all** resolve from the scheduler
    /// — the same all-or-nothing unit as the data-plane context; any incomplete
    /// binding yields `false`. The **control-plane**
    /// syscalls (`task_yield` / `task_exit`) act on the trusted current-task
    /// identity ([ADR-0031][adr-0031]) and consult **no** capability, so the
    /// empty fail-closed `caller_table` cannot guard them — the dispatcher
    /// instead rejects them with `InvalidHandle` when this is `false` (H2). A
    /// data-plane syscall with no current task fails closed via the empty table
    /// regardless of this flag.
    ///
    /// [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md
    pub has_current_task: bool,
}

/// Decode and execute one syscall, returning the trampoline's next action.
///
/// **Panic-free on every syscall input.** An unrecognised number (including `0`
/// and the debug-gated `console_write` in release) yields
/// [`SyscallError::BadSyscallNumber`]; every capability / pointer failure yields
/// a typed [`SyscallError`] as a value. No register-supplied value can drive
/// this function to `panic!` / `unwrap` / `expect`.
///
/// This is **syscall-input-scoped**: it concerns the dispatcher's response to
/// the register frame of an `SVC`. It is distinct from EL0 **execution-time
/// faults** — a non-`SVC` synchronous fault (illegal instruction, unmapped
/// deref by running EL0 code) is *not* handled here; in v1 it routes to the
/// kernel panic handler (a denial-of-self, not an escalation — the faulting
/// task harms only itself), the explicitly-deferred K3-4 / Phase E fault-
/// containment item (Phase B closure security review, 2026-06-01).
#[must_use]
pub fn dispatch<M: Mmu>(ctx: &mut SyscallContext<'_, M>, args: SyscallArgs) -> SyscallEffect {
    let Some(number) = SyscallNumber::decode(args.number) else {
        // Number 0 (reserved-invalid), out-of-range, or console_write in a
        // non-debug build (the release debug-gate): no capability is touched.
        return SyscallEffect::Resume(SyscallReturn::error(SyscallError::BadSyscallNumber));
    };
    match number {
        SyscallNumber::Send => SyscallEffect::Resume(sys_send(ctx, args.args)),
        SyscallNumber::Recv => SyscallEffect::Resume(sys_recv(ctx, args.args)),
        // Control-plane: act on the caller's own task. These consult no
        // capability, so the empty fail-closed `caller_table` does not guard
        // them — gate #3 (T-026, H2) rejects them here when no EL0 task is
        // current (nothing to yield / exit). With a current task they return
        // the directive the BSP applies (real `yield_now` / termination is the
        // B6 wire-up).
        SyscallNumber::TaskYield => {
            if ctx.has_current_task {
                SyscallEffect::Reschedule
            } else {
                SyscallEffect::Resume(SyscallReturn::error(SyscallError::from(
                    CapError::InvalidHandle,
                )))
            }
        }
        SyscallNumber::TaskExit => {
            if ctx.has_current_task {
                SyscallEffect::Terminate(args.args[0])
            } else {
                SyscallEffect::Resume(SyscallReturn::error(SyscallError::from(
                    CapError::InvalidHandle,
                )))
            }
        }
        SyscallNumber::ConsoleWrite => SyscallEffect::Resume(sys_console_write(ctx, args.args)),
    }
}

/// `send` (number `1`): `ipc_send` on the endpoint capability in `x0`.
///
/// `x0` = endpoint cap handle, `x1` = `msg.label`, `x2`–`x4` = `msg.params`,
/// `x5` = transfer cap handle (or the null sentinel). The endpoint capability
/// check (`SEND` right, right kind, live object) happens inside [`ipc_send`];
/// its [`IpcError`][crate::ipc::IpcError] composes into [`SyscallError::Ipc`].
fn sys_send<M: Mmu>(ctx: &mut SyscallContext<'_, M>, args: [u64; 6]) -> SyscallReturn {
    let ep_cap = decode_required_cap_handle(args[0]);
    let msg = decode_send_message(args);
    let transfer = super::abi::decode_cap_handle(args[5]);
    // Disjoint field reborrows: ep_arena / queues / caller_table are distinct
    // fields, so the three `&mut` reborrows do not alias.
    match ipc_send(
        &mut *ctx.ep_arena,
        &mut *ctx.queues,
        ep_cap,
        &mut *ctx.caller_table,
        msg,
        transfer,
    ) {
        Ok(outcome) => SyscallReturn::ok().with_payload::<0>(encode_send_outcome(outcome)),
        Err(e) => SyscallReturn::error(SyscallError::from(e)),
    }
}

/// `recv` (number `2`): `ipc_recv` on the endpoint capability in `x0`.
///
/// `x0` = endpoint cap handle. On success the message + optional transferred
/// capability pack into `x1`–`x6` per [`encode_recv_outcome`]. The endpoint
/// capability check (`RECV` right, right kind, live object) happens inside
/// [`ipc_recv`]; its error composes into [`SyscallError::Ipc`].
fn sys_recv<M: Mmu>(ctx: &mut SyscallContext<'_, M>, args: [u64; 6]) -> SyscallReturn {
    let ep_cap = decode_required_cap_handle(args[0]);
    match ipc_recv(
        &mut *ctx.ep_arena,
        &mut *ctx.queues,
        ep_cap,
        &mut *ctx.caller_table,
    ) {
        Ok(outcome) => encode_recv_outcome(outcome),
        Err(e) => SyscallReturn::error(SyscallError::from(e)),
    }
}

/// `console_write` (number `5`, debug-gated): emit a user buffer to the console.
///
/// `x0` = debug-console cap handle, `x1` = user VA of the buffer, `x2` = length.
/// Two independent gates, in order: (1) the **capability gate** — the cap must
/// resolve, be [`CapKind::DebugConsole`], and carry [`CapRights::CONSOLE_WRITE`]
/// (all builds; the [P1 / P4][principles] authority check); (2) the **debug
/// gate** — number `5` only reaches here in a debug build ([`SyscallNumber::decode`]
/// returns `None` for it in release). Only after the capability check passes is
/// the buffer range validated and copied through [`copy_from_user`]; the raw
/// user pointer is never dereferenced before both the cap check and the range
/// check succeed.
///
/// [principles]: https://github.com/HodeTech/Tyrne/blob/main/docs/standards/architectural-principles.md
#[allow(
    clippy::cast_possible_truncation,
    reason = "Tyrne targets are 64-bit (aarch64 kernel / x86-64 host tests); \
              usize == u64, so the u64 register words → usize casts are lossless"
)]
fn sys_console_write<M: Mmu>(ctx: &mut SyscallContext<'_, M>, args: [u64; 6]) -> SyscallReturn {
    let cons_cap = decode_required_cap_handle(args[0]);
    let ptr = args[1] as usize;
    let len = args[2] as usize;

    // Gate 1 — capability (authority). Validate before any output or any read
    // of the user buffer; a stale / wrong-kind / no-CONSOLE_WRITE cap returns a
    // typed Cap-family error with the console untouched.
    if let Err(e) = validate_debug_console_cap(&*ctx.caller_table, cons_cap) {
        return SyscallReturn::error(SyscallError::from(e));
    }

    // Gate 2 — range (cheap first gate). Validate the WHOLE range up front.
    if let Err(e) = ctx.user_window.validate(ptr, len) {
        return SyscallReturn::error(e);
    }

    // Gate 3 — per-page translation (gate #1, ADR-0038). PROBE every page the
    // whole buffer spans (translate through the task's AS + require USER) BEFORE
    // emitting any chunk, so a faulting buffer — including an in-window kernel
    // (non-USER) VA — emits *nothing* (the confused-deputy defence + all-or-
    // nothing, §Simulation rows 1/4). The per-chunk `copy_from_user` below
    // re-validates + re-probes its own chunk for self-containment; this
    // whole-range probe is what bounds the multi-chunk *emit*.
    if len > 0 {
        if let Err(e) = probe_user_pages(
            ctx.mmu,
            ctx.task_as,
            ptr,
            len,
            /* require_write */ false,
        ) {
            return SyscallReturn::error(e);
        }
    }

    // Copy + emit in bounded chunks through a kernel stack buffer.
    //
    // Unreachability of the three defensive error arms below (kept for totality,
    // never hit on this path): the up-front `validate(ptr, len)` proved that
    // `ptr + len` does not overflow `usize` AND that `[ptr, ptr + len)` is wholly
    // inside the active window. The loop invariant `0 <= offset < len` then gives
    // `ptr + offset <= ptr + len` (no overflow → `checked_add` is `Some`) and
    // `[chunk_ptr, chunk_ptr + chunk) ⊆ [ptr, ptr + len)` (a sub-range of the
    // validated whole → `copy_from_user`'s re-validation is `Ok`), and
    // `offset + chunk <= len` (no overflow → `checked_add` is `Some`). The arms
    // exist only so the function is total even if a future refactor weakens the
    // up-front check.
    let mut buf = [0u8; CONSOLE_WRITE_CHUNK];
    let mut offset: usize = 0;
    while offset < len {
        // `wrapping_sub` cannot wrap (offset < len) and satisfies the
        // arithmetic-side-effects lint; `min` bounds the chunk to the buffer.
        let remaining = len.wrapping_sub(offset);
        let chunk = core::cmp::min(remaining, CONSOLE_WRITE_CHUNK);
        let Some(chunk_ptr) = ptr.checked_add(offset) else {
            return SyscallReturn::error(SyscallError::FaultAddress);
        };
        if let Err(e) = copy_from_user(
            ctx.mmu,
            ctx.task_as,
            &ctx.user_window,
            chunk_ptr,
            &mut buf[..chunk],
        ) {
            return SyscallReturn::error(e);
        }
        ctx.console.write_bytes(&buf[..chunk]);
        let Some(next) = offset.checked_add(chunk) else {
            return SyscallReturn::error(SyscallError::FaultAddress);
        };
        offset = next;
    }

    // x1 = bytes written (all of them, on success).
    SyscallReturn::ok().with_payload::<0>(len as u64)
}

/// Validate that `cons_cap` authorises a console write: it must resolve in the
/// caller's table, name the [`CapKind::DebugConsole`] singleton, and carry the
/// [`CapRights::CONSOLE_WRITE`] right.
///
/// Returns the in-kernel [`CapError`] so the caller composes it into
/// [`SyscallError::Cap`]; the resolve → kind → rights order mirrors the IPC
/// capability-validation order ([ADR-0030][adr-0030]'s taxonomy).
///
/// # Errors
///
/// - [`CapError::InvalidHandle`] — the handle did not resolve (stale / absent).
/// - [`CapError::WrongKind`] — the capability is not a debug-console capability.
/// - [`CapError::InsufficientRights`] — it lacks [`CapRights::CONSOLE_WRITE`].
///
/// [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
fn validate_debug_console_cap(
    table: &CapabilityTable,
    cons_cap: CapHandle,
) -> Result<(), CapError> {
    let cap = table.lookup(cons_cap)?;
    if cap.kind() != CapKind::DebugConsole {
        return Err(CapError::WrongKind);
    }
    if !cap.rights().contains(CapRights::CONSOLE_WRITE) {
        return Err(CapError::InsufficientRights);
    }
    Ok(())
}

#[cfg(test)]
#[allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::arithmetic_side_effects,
    clippy::cast_possible_truncation,
    clippy::too_many_arguments,
    reason = "tests may use pragmas forbidden in production kernel code; \
              run_console_write threads the SyscallContext pieces"
)]
mod tests {
    use super::{dispatch, SyscallContext, CONSOLE_WRITE_CHUNK};
    use crate::cap::{CapHandle, CapObject, CapRights, Capability, CapabilityTable};
    use crate::ipc::IpcError;
    use crate::ipc::IpcQueues;
    use crate::obj::endpoint::{create_endpoint, Endpoint, EndpointArena};
    use crate::syscall::abi::{
        decode_cap_handle, encode_cap_handle, SyscallArgs, SyscallEffect, SyscallNumber,
        NULL_CAP_HANDLE, RECV_OUTCOME_PENDING, RECV_OUTCOME_RECEIVED, SEND_OUTCOME_ENQUEUED,
    };
    use crate::syscall::error::SyscallError;
    use crate::syscall::user_access::UserAccessWindow;
    use tyrne_hal::{MappingFlags, Mmu, PhysAddr, PhysFrame};
    use tyrne_test_hal::{FakeAddressSpace, FakeConsole, FakeMmu, FakeUserMem};

    // ── fixtures ─────────────────────────────────────────────────────────────

    /// Mint a debug-console capability with `CONSOLE_WRITE` in a fresh table,
    /// returning `(table, handle)`.
    fn table_with_console_cap() -> (CapabilityTable, CapHandle) {
        let mut table = CapabilityTable::new();
        let h = table
            .insert_root(Capability::new(
                CapRights::CONSOLE_WRITE,
                CapObject::DebugConsole,
            ))
            .unwrap();
        (table, h)
    }

    /// A `SyscallArgs` whose number is `n` and whose arg words are `args`.
    fn call(n: SyscallNumber, args: [u64; 6]) -> SyscallArgs {
        SyscallArgs {
            number: n.as_u64(),
            args,
        }
    }

    /// A `FakeMmu` + empty address space for syscalls that never copy from user
    /// (everything except `console_write`). Both returned values must outlive
    /// the `SyscallContext` that borrows them.
    fn empty_mmu_as() -> (FakeMmu, <FakeMmu as Mmu>::AddressSpace) {
        let mmu = FakeMmu::new();
        // SAFETY: FakeMmu::create_address_space stores the root, never derefs it.
        let as_ =
            unsafe { mmu.create_address_space(PhysFrame::from_aligned(PhysAddr(0x1000)).unwrap()) };
        (mmu, as_)
    }

    /// Dispatch a `console_write` of `[ptr, len)` (cap word `cap_word`) against
    /// the given translation surface + window, returning the effect. Folds the
    /// per-test `ep_arena` / `queues` (unused by `console_write`) + the context
    /// construction so each console test reads as a one-liner.
    fn run_console_write(
        table: &mut CapabilityTable,
        console: &FakeConsole,
        mmu: &FakeMmu,
        task_as: &FakeAddressSpace,
        window: UserAccessWindow,
        cap_word: u64,
        ptr: u64,
        len: u64,
    ) -> SyscallEffect {
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: table,
            console,
            user_window: window,
            mmu,
            task_as,
            has_current_task: true,
        };
        dispatch(
            &mut ctx,
            call(SyscallNumber::ConsoleWrite, [cap_word, ptr, len, 0, 0, 0]),
        )
    }

    // ── number decode ────────────────────────────────────────────────────────

    #[test]
    fn bad_number_zero_returns_bad_syscall_number_touching_nothing() {
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
            mmu: &mmu,
            task_as: &task_as,
            has_current_task: true,
        };
        let effect = dispatch(
            &mut ctx,
            SyscallArgs {
                number: 0,
                args: [0; 6],
            },
        );
        match effect {
            SyscallEffect::Resume(r) => {
                assert_eq!(r.status, SyscallError::BadSyscallNumber.as_status());
            }
            other => panic!("expected Resume(BadSyscallNumber), got {other:?}"),
        }
        assert!(console.captured().is_empty());
    }

    #[test]
    fn out_of_range_number_returns_bad_syscall_number() {
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
            mmu: &mmu,
            task_as: &task_as,
            has_current_task: true,
        };
        let effect = dispatch(
            &mut ctx,
            SyscallArgs {
                number: 99,
                args: [0; 6],
            },
        );
        assert_eq!(
            effect,
            SyscallEffect::Resume(super::SyscallReturn::error(SyscallError::BadSyscallNumber))
        );
    }

    // ── control-plane routing ────────────────────────────────────────────────

    #[test]
    fn task_yield_routes_to_reschedule() {
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
            mmu: &mmu,
            task_as: &task_as,
            has_current_task: true,
        };
        assert_eq!(
            dispatch(&mut ctx, call(SyscallNumber::TaskYield, [0; 6])),
            SyscallEffect::Reschedule
        );
    }

    #[test]
    fn task_exit_routes_to_terminate_with_code() {
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
            mmu: &mmu,
            task_as: &task_as,
            has_current_task: true,
        };
        assert_eq!(
            dispatch(
                &mut ctx,
                call(SyscallNumber::TaskExit, [0x2A, 0, 0, 0, 0, 0])
            ),
            SyscallEffect::Terminate(0x2A)
        );
    }

    // ── control-plane fail-closed (gate #3 / T-026, H2) ──────────────────────

    #[test]
    fn task_yield_with_no_current_task_fails_closed() {
        // Control-plane consults no capability, so the empty fail-closed table
        // cannot guard it; the dispatcher rejects task_yield with InvalidHandle
        // when no EL0 task is current (nothing to yield) — not Reschedule.
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
            mmu: &mmu,
            task_as: &task_as,
            has_current_task: false,
        };
        let effect = dispatch(&mut ctx, call(SyscallNumber::TaskYield, [0; 6]));
        match effect {
            SyscallEffect::Resume(r) => assert_eq!(
                r.status,
                SyscallError::Cap(crate::cap::CapError::InvalidHandle).as_status()
            ),
            other => panic!("expected Resume(InvalidHandle), not Reschedule, got {other:?}"),
        }
    }

    #[test]
    fn task_exit_with_no_current_task_fails_closed() {
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
            mmu: &mmu,
            task_as: &task_as,
            has_current_task: false,
        };
        let effect = dispatch(
            &mut ctx,
            call(SyscallNumber::TaskExit, [0x2A, 0, 0, 0, 0, 0]),
        );
        match effect {
            SyscallEffect::Resume(r) => assert_eq!(
                r.status,
                SyscallError::Cap(crate::cap::CapError::InvalidHandle).as_status()
            ),
            other => panic!("expected Resume(InvalidHandle), not Terminate, got {other:?}"),
        }
    }

    #[test]
    #[cfg(debug_assertions)] // exercises console_write (number 5), which is debug-gated
    fn incomplete_binding_context_fails_closed_on_both_planes() {
        // Models the context the BSP `syscall_entry` builds on an INCOMPLETE
        // running-task binding (any of table / window / generation-checked AS
        // missing or stale): the empty `FAILCLOSED_TABLE` + an empty window +
        // `has_current_task = false`. The BSP match that assembles it is
        // no_std / no_main and not host-testable directly; this pins the
        // dispatcher's handling of that exact context — **both** planes must
        // fail closed in the *same* context: the data-plane `console_write` via
        // the empty table (InvalidHandle, no output) and the control-plane
        // `task_yield` via the `has_current_task` gate (InvalidHandle, not
        // Reschedule). Closes the incomplete-context coverage gate #3's BSP
        // fallback arm cannot unit-test itself (T-026 review-round).
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new(); // empty: the FAILCLOSED_TABLE analog
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
            mmu: &mmu,
            task_as: &task_as,
            has_current_task: false,
        };

        // Data-plane: console_write fails closed via the empty table (the cap
        // gate rejects before the window / translate is ever consulted).
        let bogus = encode_cap_handle(Some(CapHandle::from_raw(0, 0)));
        match dispatch(
            &mut ctx,
            call(SyscallNumber::ConsoleWrite, [bogus, 0x40_0000, 5, 0, 0, 0]),
        ) {
            SyscallEffect::Resume(r) => assert_eq!(
                r.status,
                SyscallError::Cap(crate::cap::CapError::InvalidHandle).as_status(),
                "data-plane console_write must fail closed on an incomplete binding"
            ),
            other => panic!("expected Resume(InvalidHandle), got {other:?}"),
        }
        assert!(
            console.captured().is_empty(),
            "no byte may be emitted from the incomplete-binding fallback context"
        );

        // Control-plane: task_yield fails closed via the has_current_task gate
        // (the empty table cannot guard it — it consults no capability).
        match dispatch(&mut ctx, call(SyscallNumber::TaskYield, [0; 6])) {
            SyscallEffect::Resume(r) => assert_eq!(
                r.status,
                SyscallError::Cap(crate::cap::CapError::InvalidHandle).as_status(),
                "control-plane task_yield must fail closed on an incomplete binding"
            ),
            other => panic!("expected Resume(InvalidHandle), not Reschedule, got {other:?}"),
        }
    }

    // ── send / recv ──────────────────────────────────────────────────────────

    #[test]
    fn send_with_no_receiver_enqueues_and_returns_ok() {
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        let ep = create_endpoint(&mut ep_arena, Endpoint::new(0)).unwrap();
        let ep_cap = table
            .insert_root(Capability::new(
                CapRights::SEND | CapRights::RECV,
                CapObject::Endpoint(ep),
            ))
            .unwrap();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
            mmu: &mmu,
            task_as: &task_as,
            has_current_task: true,
        };
        let cap_word = encode_cap_handle(Some(ep_cap));
        let effect = dispatch(
            &mut ctx,
            call(
                SyscallNumber::Send,
                [cap_word, 0xAB, 1, 2, 3, encode_cap_handle(None)],
            ),
        );
        match effect {
            SyscallEffect::Resume(r) => {
                assert_eq!(r.status, 0, "send must succeed");
                assert_eq!(r.payload[0], SEND_OUTCOME_ENQUEUED);
            }
            other => panic!("expected Resume, got {other:?}"),
        }
    }

    #[test]
    fn send_without_send_right_returns_typed_ipc_missing_right() {
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        let ep = create_endpoint(&mut ep_arena, Endpoint::new(0)).unwrap();
        // RECV only — no SEND. ipc_send → MissingRight → SyscallError::Ipc.
        let ep_cap = table
            .insert_root(Capability::new(CapRights::RECV, CapObject::Endpoint(ep)))
            .unwrap();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
            mmu: &mmu,
            task_as: &task_as,
            has_current_task: true,
        };
        let cap_word = encode_cap_handle(Some(ep_cap));
        let effect = dispatch(
            &mut ctx,
            call(
                SyscallNumber::Send,
                [cap_word, 0, 0, 0, 0, encode_cap_handle(None)],
            ),
        );
        match effect {
            SyscallEffect::Resume(r) => assert_eq!(
                r.status,
                SyscallError::Ipc(crate::ipc::IpcError::MissingRight).as_status()
            ),
            other => panic!("expected Resume(error), got {other:?}"),
        }
    }

    #[test]
    fn recv_of_enqueued_message_unpacks_into_registers() {
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        let ep = create_endpoint(&mut ep_arena, Endpoint::new(0)).unwrap();
        let ep_cap = table
            .insert_root(Capability::new(
                CapRights::SEND | CapRights::RECV,
                CapObject::Endpoint(ep),
            ))
            .unwrap();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
            mmu: &mmu,
            task_as: &task_as,
            has_current_task: true,
        };
        let cap_word = encode_cap_handle(Some(ep_cap));
        // Enqueue a message via the send syscall.
        let _ = dispatch(
            &mut ctx,
            call(
                SyscallNumber::Send,
                [cap_word, 0x55, 7, 8, 9, encode_cap_handle(None)],
            ),
        );
        // Receive it back.
        let effect = dispatch(
            &mut ctx,
            call(SyscallNumber::Recv, [cap_word, 0, 0, 0, 0, 0]),
        );
        match effect {
            SyscallEffect::Resume(r) => {
                assert_eq!(r.status, 0);
                assert_eq!(r.payload[0], RECV_OUTCOME_RECEIVED); // x1
                assert_eq!(r.payload[1], 0x55); // x2 label
                assert_eq!(r.payload[2], 7); // x3 param0
                assert_eq!(r.payload[3], 8); // x4 param1
                assert_eq!(r.payload[4], 9); // x5 param2
            }
            other => panic!("expected Resume(Received), got {other:?}"),
        }
    }

    // ── review-round follow-up: end-to-end transfer + Pending + chunk boundary ─
    //
    // These close the dispatch-level coverage gaps the T-021 review-round
    // surfaced: the transfer-cap wiring (x5 decode → ipc_send cap_take, and
    // ipc_recv install → x6 pack) had no through-dispatch test, nor did the
    // RecvOutcome::Pending register packing or the exact one-chunk boundary.

    #[test]
    fn send_with_transfer_cap_then_recv_returns_cap_in_x6() {
        // Exercises the x5 transfer-handle decode → `ipc_send` `cap_take` AND the
        // `ipc_recv` → `encode_recv_outcome` x6 cap-pack, end-to-end through
        // `dispatch` — wiring no existing dispatch test covered (every other send
        // test passes the null sentinel; the recv test never asserts x6).
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        // ep1: the comm endpoint (SEND|RECV). ep2: the object whose cap we move.
        let ep1 = create_endpoint(&mut ep_arena, Endpoint::new(0)).unwrap();
        let ep2 = create_endpoint(&mut ep_arena, Endpoint::new(1)).unwrap();
        let ep_cap = table
            .insert_root(Capability::new(
                CapRights::SEND | CapRights::RECV,
                CapObject::Endpoint(ep1),
            ))
            .unwrap();
        // The transferred cap needs the TRANSFER right (ipc_send enforces it).
        let xfer_cap = table
            .insert_root(Capability::new(
                CapRights::TRANSFER,
                CapObject::Endpoint(ep2),
            ))
            .unwrap();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
            mmu: &mmu,
            task_as: &task_as,
            has_current_task: true,
        };
        let ep_word = encode_cap_handle(Some(ep_cap));

        // send with the transfer handle in x5.
        let send_effect = dispatch(
            &mut ctx,
            call(
                SyscallNumber::Send,
                [ep_word, 0x77, 0, 0, 0, encode_cap_handle(Some(xfer_cap))],
            ),
        );
        assert!(
            matches!(send_effect, SyscallEffect::Resume(r) if r.status == 0),
            "send-with-transfer must succeed, got {send_effect:?}"
        );
        // The transferred cap left the sender's table (cap_take).
        assert!(
            ctx.caller_table.lookup(xfer_cap).is_err(),
            "transferred cap must be taken out of the sender's table"
        );

        // recv collects the message AND the transferred cap (x6).
        let recv_effect = dispatch(
            &mut ctx,
            call(SyscallNumber::Recv, [ep_word, 0, 0, 0, 0, 0]),
        );
        let SyscallEffect::Resume(r) = recv_effect else {
            panic!("expected Resume from recv, got {recv_effect:?}");
        };
        assert_eq!(r.status, 0);
        assert_eq!(r.payload[0], RECV_OUTCOME_RECEIVED); // x1
        assert_eq!(r.payload[1], 0x77); // x2 label
                                        // x6 carries the transferred cap as a non-null handle that resolves.
        assert_ne!(r.payload[5], NULL_CAP_HANDLE, "x6 must carry a real handle");
        let received = decode_cap_handle(r.payload[5]).expect("x6 decodes to Some(handle)");
        assert!(
            ctx.caller_table.lookup(received).is_ok(),
            "the transferred cap must be installed in the receiver's table"
        );
    }

    #[test]
    fn send_with_stale_transfer_handle_returns_invalid_transfer_cap() {
        // A valid endpoint cap but a transfer handle (x5) that resolves to
        // nothing: `ipc_send`'s transfer pre-flight returns `InvalidTransferCap`,
        // composing into `SyscallError::Ipc(InvalidTransferCap)` (status 0x205).
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        let ep = create_endpoint(&mut ep_arena, Endpoint::new(0)).unwrap();
        let ep_cap = table
            .insert_root(Capability::new(CapRights::SEND, CapObject::Endpoint(ep)))
            .unwrap();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
            mmu: &mmu,
            task_as: &task_as,
            has_current_task: true,
        };
        // x5 = a handle naming no live slot (index far past CAP_TABLE_CAPACITY).
        let stale_xfer = encode_cap_handle(Some(CapHandle::from_raw(50, 7)));
        let effect = dispatch(
            &mut ctx,
            call(
                SyscallNumber::Send,
                [encode_cap_handle(Some(ep_cap)), 0, 0, 0, 0, stale_xfer],
            ),
        );
        match effect {
            SyscallEffect::Resume(r) => assert_eq!(
                r.status,
                SyscallError::Ipc(IpcError::InvalidTransferCap).as_status()
            ),
            other => panic!("expected Resume(InvalidTransferCap), got {other:?}"),
        }
    }

    #[test]
    fn recv_with_no_sender_returns_pending_packing() {
        // recv on an endpoint with no waiting sender returns RecvOutcome::Pending:
        // status Ok, x1 = pending code, x2..x7 zeroed (deterministic).
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        let ep = create_endpoint(&mut ep_arena, Endpoint::new(0)).unwrap();
        let ep_cap = table
            .insert_root(Capability::new(CapRights::RECV, CapObject::Endpoint(ep)))
            .unwrap();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
            mmu: &mmu,
            task_as: &task_as,
            has_current_task: true,
        };
        let effect = dispatch(
            &mut ctx,
            call(
                SyscallNumber::Recv,
                [encode_cap_handle(Some(ep_cap)), 0, 0, 0, 0, 0],
            ),
        );
        let SyscallEffect::Resume(r) = effect else {
            panic!("expected Resume(Pending), got {effect:?}");
        };
        assert_eq!(r.status, 0);
        assert_eq!(r.payload[0], RECV_OUTCOME_PENDING); // x1
        assert_eq!(
            &r.payload[1..],
            &[0, 0, 0, 0, 0, 0],
            "x2..x7 must be zeroed on Pending"
        );
    }

    #[test]
    #[cfg(debug_assertions)] // console_write number 5 is debug-gated
    fn console_write_exactly_one_chunk_emits_all_bytes() {
        // Boundary: len == CONSOLE_WRITE_CHUNK exercises the `offset < len` loop
        // termination exactly — one chunk, then offset == len.
        let (mut table, cons_cap) = table_with_console_cap();
        let console = FakeConsole::new();
        let payload: Vec<u8> = (0..CONSOLE_WRITE_CHUNK).map(|i| (i % 251) as u8).collect();
        let mem = FakeUserMem::new(0x40_0000, 1, MappingFlags::USER | MappingFlags::WRITE);
        mem.write(0, &payload);
        let effect = run_console_write(
            &mut table,
            &console,
            mem.mmu(),
            mem.address_space(),
            UserAccessWindow::new(mem.base_va(), mem.region_len()),
            encode_cap_handle(Some(cons_cap)),
            mem.base_va() as u64,
            payload.len() as u64,
        );
        match effect {
            SyscallEffect::Resume(r) => assert_eq!(r.payload[0], CONSOLE_WRITE_CHUNK as u64),
            other => panic!("expected Resume(ok), got {other:?}"),
        }
        assert_eq!(console.captured(), payload);
    }

    // ── console_write: capability gate ───────────────────────────────────────

    #[test]
    #[cfg(debug_assertions)] // console_write number 5 is debug-gated; release path tested separately
    fn console_write_with_no_cap_returns_cap_invalid_handle_no_output() {
        // The cap gate fails first, before any range/translate — so an empty
        // translation surface + a never-read buffer pointer suffice.
        let mut table = CapabilityTable::new(); // empty: handle resolves to nothing
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let bogus = encode_cap_handle(Some(CapHandle::from_raw(0, 0)));
        let effect = run_console_write(
            &mut table,
            &console,
            &mmu,
            &task_as,
            UserAccessWindow::empty(),
            bogus,
            0x40_0000,
            5,
        );
        match effect {
            SyscallEffect::Resume(r) => assert_eq!(
                r.status,
                SyscallError::Cap(crate::cap::CapError::InvalidHandle).as_status()
            ),
            other => panic!("expected Resume(Cap error), got {other:?}"),
        }
        assert!(
            console.captured().is_empty(),
            "no byte may be emitted when the capability check fails"
        );
    }

    #[test]
    #[cfg(debug_assertions)] // console_write number 5 is debug-gated; release path tested separately
    fn console_write_with_wrong_kind_cap_returns_cap_wrong_kind() {
        let mut ep_arena = EndpointArena::default();
        let mut table = CapabilityTable::new();
        // An endpoint cap where a debug-console cap is required.
        let ep = create_endpoint(&mut ep_arena, Endpoint::new(0)).unwrap();
        let wrong = table
            .insert_root(Capability::new(
                CapRights::CONSOLE_WRITE, // even with the right bit, wrong kind
                CapObject::Endpoint(ep),
            ))
            .unwrap();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let effect = run_console_write(
            &mut table,
            &console,
            &mmu,
            &task_as,
            UserAccessWindow::empty(),
            encode_cap_handle(Some(wrong)),
            0x40_0000,
            2,
        );
        match effect {
            SyscallEffect::Resume(r) => assert_eq!(
                r.status,
                SyscallError::Cap(crate::cap::CapError::WrongKind).as_status()
            ),
            other => panic!("expected Resume(WrongKind), got {other:?}"),
        }
        assert!(console.captured().is_empty());
    }

    #[test]
    #[cfg(debug_assertions)] // console_write number 5 is debug-gated; release path tested separately
    fn console_write_without_write_right_returns_insufficient_rights() {
        let mut table = CapabilityTable::new();
        // Debug-console cap WITHOUT the CONSOLE_WRITE right.
        let cap = table
            .insert_root(Capability::new(CapRights::empty(), CapObject::DebugConsole))
            .unwrap();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        let effect = run_console_write(
            &mut table,
            &console,
            &mmu,
            &task_as,
            UserAccessWindow::empty(),
            encode_cap_handle(Some(cap)),
            0x40_0000,
            2,
        );
        match effect {
            SyscallEffect::Resume(r) => assert_eq!(
                r.status,
                SyscallError::Cap(crate::cap::CapError::InsufficientRights).as_status()
            ),
            other => panic!("expected Resume(InsufficientRights), got {other:?}"),
        }
        assert!(console.captured().is_empty());
    }

    // ── console_write: happy path + fault ────────────────────────────────────

    #[test]
    #[cfg(debug_assertions)] // console_write number 5 is debug-gated; release path tested separately
    fn console_write_emits_buffer_and_returns_byte_count() {
        let (mut table, cons_cap) = table_with_console_cap();
        let console = FakeConsole::new();
        let message = b"tyrne: hello via console_write\n";
        let mem = FakeUserMem::new(0x40_0000, 1, MappingFlags::USER | MappingFlags::WRITE);
        mem.write(0, message);
        let effect = run_console_write(
            &mut table,
            &console,
            mem.mmu(),
            mem.address_space(),
            UserAccessWindow::new(mem.base_va(), mem.region_len()),
            encode_cap_handle(Some(cons_cap)),
            mem.base_va() as u64,
            message.len() as u64,
        );
        match effect {
            SyscallEffect::Resume(r) => {
                assert_eq!(r.status, 0);
                assert_eq!(r.payload[0], message.len() as u64); // x1 = bytes written
            }
            other => panic!("expected Resume(ok), got {other:?}"),
        }
        assert_eq!(console.captured(), message);
    }

    #[test]
    #[cfg(debug_assertions)] // console_write number 5 is debug-gated; release path tested separately
    fn console_write_spanning_multiple_chunks_emits_all_bytes() {
        // Exercise the chunking loop: a buffer larger than one chunk (and
        // larger than one page, so it also exercises the multi-page translate).
        let (mut table, cons_cap) = table_with_console_cap();
        let console = FakeConsole::new();
        let len = CONSOLE_WRITE_CHUNK * 2 + 7;
        let payload: Vec<u8> = (0..len).map(|i| (i % 251) as u8).collect();
        let mem = FakeUserMem::new(0x40_0000, 1, MappingFlags::USER | MappingFlags::WRITE);
        mem.write(0, &payload);
        let effect = run_console_write(
            &mut table,
            &console,
            mem.mmu(),
            mem.address_space(),
            UserAccessWindow::new(mem.base_va(), mem.region_len()),
            encode_cap_handle(Some(cons_cap)),
            mem.base_va() as u64,
            len as u64,
        );
        match effect {
            SyscallEffect::Resume(r) => assert_eq!(r.payload[0], len as u64),
            other => panic!("expected Resume(ok), got {other:?}"),
        }
        assert_eq!(console.captured(), payload);
    }

    #[test]
    #[cfg(debug_assertions)] // console_write number 5 is debug-gated; release path tested separately
    fn console_write_out_of_range_buffer_faults_without_output() {
        // Cap passes, but the buffer pointer falls outside the window → the
        // range first-gate rejects before any translate. (No mapping needed.)
        let (mut table, cons_cap) = table_with_console_cap();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        // Window covers a different region than the buffer pointer (0x40_0000).
        let effect = run_console_write(
            &mut table,
            &console,
            &mmu,
            &task_as,
            UserAccessWindow::new(0x50_0000, 16),
            encode_cap_handle(Some(cons_cap)),
            0x40_0000,
            11,
        );
        match effect {
            SyscallEffect::Resume(r) => {
                assert_eq!(r.status, SyscallError::FaultAddress.as_status());
            }
            other => panic!("expected Resume(FaultAddress), got {other:?}"),
        }
        assert!(
            console.captured().is_empty(),
            "a faulting buffer must emit nothing — the cap check passed but the range did not"
        );
    }

    // ── gate #1: confused-deputy + all-or-nothing (ADR-0038) ─────────────────

    #[test]
    #[cfg(debug_assertions)] // console_write number 5 is debug-gated
    fn console_write_cap_ok_but_non_user_page_emits_nothing() {
        // THE confused-deputy regression: a holder of a valid debug-console cap
        // points at an in-window page that is mapped but NOT user-accessible
        // (the kernel-VA case under the legacy wide window, or any non-USER
        // leaf). The cap gate passes and the range gate passes, but the per-page
        // translate USER-check rejects it — nothing is emitted.
        let (mut table, cons_cap) = table_with_console_cap();
        let console = FakeConsole::new();
        let mem = FakeUserMem::new(0x40_0000, 1, MappingFlags::WRITE); // mapped, NO USER bit
        mem.write(0, b"secret kernel bytes");
        let effect = run_console_write(
            &mut table,
            &console,
            mem.mmu(),
            mem.address_space(),
            UserAccessWindow::new(mem.base_va(), mem.region_len()),
            encode_cap_handle(Some(cons_cap)),
            mem.base_va() as u64,
            19,
        );
        match effect {
            SyscallEffect::Resume(r) => {
                assert_eq!(r.status, SyscallError::FaultAddress.as_status());
            }
            other => panic!("expected Resume(FaultAddress), got {other:?}"),
        }
        assert!(
            console.captured().is_empty(),
            "a non-USER in-window page must emit nothing — the confused-deputy defence"
        );
    }

    #[test]
    #[cfg(debug_assertions)] // console_write number 5 is debug-gated
    fn console_write_multipage_second_page_unmapped_emits_nothing() {
        // All-or-nothing: page 0 is a valid USER page, the buffer spans into an
        // unmapped page 1. The up-front whole-range probe faults before any
        // chunk of page 0 is emitted.
        let (mut table, cons_cap) = table_with_console_cap();
        let console = FakeConsole::new();
        let mem = FakeUserMem::new(0x40_0000, 1, MappingFlags::USER | MappingFlags::WRITE);
        mem.write(0, &[0xEE; 4096]);
        // Window spans two pages; only page 0 is mapped. The buffer starts late
        // in page 0 and runs into the unmapped page 1.
        let wide = UserAccessWindow::new(mem.base_va(), 2 * 4096);
        let effect = run_console_write(
            &mut table,
            &console,
            mem.mmu(),
            mem.address_space(),
            wide,
            encode_cap_handle(Some(cons_cap)),
            (mem.base_va() + 4096 - 8) as u64,
            16, // 8 bytes in page 0, 8 in the unmapped page 1
        );
        match effect {
            SyscallEffect::Resume(r) => {
                assert_eq!(r.status, SyscallError::FaultAddress.as_status());
            }
            other => panic!("expected Resume(FaultAddress), got {other:?}"),
        }
        assert!(
            console.captured().is_empty(),
            "all-or-nothing: a later unmapped page must emit no prefix from page 0"
        );
    }

    // ── release debug-gate ───────────────────────────────────────────────────

    #[test]
    #[cfg(not(debug_assertions))]
    fn console_write_number_is_bad_syscall_in_release_build() {
        // In a release build the debug-gate drops console_write from the
        // surface entirely, even for a holder of a valid debug-console cap —
        // the number fails to decode before any cap / range / translate gate.
        let (mut table, cons_cap) = table_with_console_cap();
        let console = FakeConsole::new();
        let (mmu, task_as) = empty_mmu_as();
        // Number 5 directly (SyscallNumber::ConsoleWrite::as_u64() == 5).
        let effect = run_console_write(
            &mut table,
            &console,
            &mmu,
            &task_as,
            UserAccessWindow::empty(),
            encode_cap_handle(Some(cons_cap)),
            0x40_0000,
            4,
        );
        match effect {
            SyscallEffect::Resume(r) => {
                assert_eq!(r.status, SyscallError::BadSyscallNumber.as_status());
            }
            other => panic!("expected Resume(BadSyscallNumber), got {other:?}"),
        }
        assert!(console.captured().is_empty());
    }
}
