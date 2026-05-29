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

use tyrne_hal::Console;

use crate::cap::{CapError, CapHandle, CapKind, CapRights, CapabilityTable};
use crate::ipc::{ipc_recv, ipc_send, IpcQueues};
use crate::obj::EndpointArena;

use super::abi::{
    decode_required_cap_handle, decode_send_message, encode_recv_outcome, encode_send_outcome,
    SyscallArgs, SyscallEffect, SyscallNumber, SyscallReturn,
};
use super::error::SyscallError;
use super::user_access::{copy_from_user, UserAccessWindow};

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
/// exists. Either way the dispatcher never lets a syscall name a capability
/// outside this one table — the per-subject unforgeability [ADR-0014][adr-0014]
/// guarantees.
///
/// [adr-0021]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0021-raw-pointer-scheduler-ipc-bridge.md
/// [adr-0014]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0014-capability-representation.md
pub struct SyscallContext<'a> {
    /// The endpoint kernel-object arena `send` / `recv` resolve handles against.
    pub ep_arena: &'a mut EndpointArena,
    /// The IPC waiter-state queues `send` / `recv` advance.
    pub queues: &'a mut IpcQueues,
    /// The calling task's capability table — the only table any syscall in this
    /// dispatch may name a capability in.
    pub caller_table: &'a mut CapabilityTable,
    /// The debug console `console_write` emits to after its capability check.
    pub console: &'a dyn Console,
    /// The active address space's user-accessible window, validated against by
    /// `console_write`'s copy-from-user.
    pub user_window: UserAccessWindow,
}

/// Decode and execute one syscall, returning the trampoline's next action.
///
/// **Panic-free on every input.** An unrecognised number (including `0` and the
/// debug-gated `console_write` in release) yields
/// [`SyscallError::BadSyscallNumber`]; every capability / pointer failure yields
/// a typed [`SyscallError`] as a value. No register-supplied value can drive
/// this function to `panic!` / `unwrap` / `expect`.
#[must_use]
pub fn dispatch(ctx: &mut SyscallContext<'_>, args: SyscallArgs) -> SyscallEffect {
    let Some(number) = SyscallNumber::decode(args.number) else {
        // Number 0 (reserved-invalid), out-of-range, or console_write in a
        // non-debug build (the release debug-gate): no capability is touched.
        return SyscallEffect::Resume(SyscallReturn::error(SyscallError::BadSyscallNumber));
    };
    match number {
        SyscallNumber::Send => SyscallEffect::Resume(sys_send(ctx, args.args)),
        SyscallNumber::Recv => SyscallEffect::Resume(sys_recv(ctx, args.args)),
        // Control-plane: act on the caller's own task; see SyscallEffect.
        SyscallNumber::TaskYield => SyscallEffect::Reschedule,
        SyscallNumber::TaskExit => SyscallEffect::Terminate(args.args[0]),
        SyscallNumber::ConsoleWrite => SyscallEffect::Resume(sys_console_write(ctx, args.args)),
    }
}

/// `send` (number `1`): `ipc_send` on the endpoint capability in `x0`.
///
/// `x0` = endpoint cap handle, `x1` = `msg.label`, `x2`–`x4` = `msg.params`,
/// `x5` = transfer cap handle (or the null sentinel). The endpoint capability
/// check (`SEND` right, right kind, live object) happens inside [`ipc_send`];
/// its [`IpcError`][crate::ipc::IpcError] composes into [`SyscallError::Ipc`].
fn sys_send(ctx: &mut SyscallContext<'_>, args: [u64; 6]) -> SyscallReturn {
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
        Ok(outcome) => SyscallReturn::ok().with_payload(0, encode_send_outcome(outcome)),
        Err(e) => SyscallReturn::error(SyscallError::from(e)),
    }
}

/// `recv` (number `2`): `ipc_recv` on the endpoint capability in `x0`.
///
/// `x0` = endpoint cap handle. On success the message + optional transferred
/// capability pack into `x1`–`x6` per [`encode_recv_outcome`]. The endpoint
/// capability check (`RECV` right, right kind, live object) happens inside
/// [`ipc_recv`]; its error composes into [`SyscallError::Ipc`].
fn sys_recv(ctx: &mut SyscallContext<'_>, args: [u64; 6]) -> SyscallReturn {
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
fn sys_console_write(ctx: &mut SyscallContext<'_>, args: [u64; 6]) -> SyscallReturn {
    let cons_cap = decode_required_cap_handle(args[0]);
    let ptr = args[1] as usize;
    let len = args[2] as usize;

    // Gate 1 — capability (authority). Validate before any output or any read
    // of the user buffer; a stale / wrong-kind / no-CONSOLE_WRITE cap returns a
    // typed Cap-family error with the console untouched.
    if let Err(e) = validate_debug_console_cap(&*ctx.caller_table, cons_cap) {
        return SyscallReturn::error(SyscallError::from(e));
    }

    // Validate the whole range up front so a faulting buffer emits *nothing*
    // (no partial output before the fault is detected).
    if let Err(e) = ctx.user_window.validate(ptr, len) {
        return SyscallReturn::error(e);
    }

    // Copy + emit in bounded chunks. Each chunk's range is a sub-range of the
    // already-validated whole, so `copy_from_user`'s re-validation always
    // passes; its error arm is handled for type honesty but is unreachable here.
    let mut buf = [0u8; CONSOLE_WRITE_CHUNK];
    let mut offset: usize = 0;
    while offset < len {
        // `wrapping_sub` cannot wrap (offset < len) and satisfies the
        // arithmetic-side-effects lint; `min` bounds the chunk to the buffer.
        let remaining = len.wrapping_sub(offset);
        let chunk = core::cmp::min(remaining, CONSOLE_WRITE_CHUNK);
        let Some(chunk_ptr) = ptr.checked_add(offset) else {
            // Unreachable: the up-front validate proved ptr + len did not wrap,
            // and offset < len. Defensive fault keeps the path total.
            return SyscallReturn::error(SyscallError::FaultAddress);
        };
        if let Err(e) = copy_from_user(&ctx.user_window, chunk_ptr, &mut buf[..chunk]) {
            return SyscallReturn::error(e);
        }
        ctx.console.write_bytes(&buf[..chunk]);
        let Some(next) = offset.checked_add(chunk) else {
            // Unreachable: offset + chunk <= len <= the validated end. Defensive.
            return SyscallReturn::error(SyscallError::FaultAddress);
        };
        offset = next;
    }

    // x1 = bytes written (all of them, on success).
    SyscallReturn::ok().with_payload(0, len as u64)
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
    reason = "tests may use pragmas forbidden in production kernel code"
)]
mod tests {
    use super::{dispatch, SyscallContext, CONSOLE_WRITE_CHUNK};
    use crate::cap::{CapHandle, CapObject, CapRights, Capability, CapabilityTable};
    use crate::ipc::IpcQueues;
    use crate::obj::endpoint::{create_endpoint, Endpoint, EndpointArena};
    use crate::syscall::abi::{
        encode_cap_handle, SyscallArgs, SyscallEffect, SyscallNumber, RECV_OUTCOME_RECEIVED,
        SEND_OUTCOME_ENQUEUED,
    };
    use crate::syscall::error::SyscallError;
    use crate::syscall::user_access::UserAccessWindow;
    use tyrne_test_hal::FakeConsole;

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

    // ── number decode ────────────────────────────────────────────────────────

    #[test]
    fn bad_number_zero_returns_bad_syscall_number_touching_nothing() {
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        let console = FakeConsole::new();
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
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
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
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
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
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
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
        };
        assert_eq!(
            dispatch(
                &mut ctx,
                call(SyscallNumber::TaskExit, [0x2A, 0, 0, 0, 0, 0])
            ),
            SyscallEffect::Terminate(0x2A)
        );
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
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
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
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
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
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::empty(),
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

    // ── console_write: capability gate ───────────────────────────────────────

    #[test]
    #[cfg(debug_assertions)] // console_write number 5 is debug-gated; release path tested separately
    fn console_write_with_no_cap_returns_cap_invalid_handle_no_output() {
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new(); // empty: handle resolves to nothing
        let console = FakeConsole::new();
        let backing = b"hello".to_vec();
        let base = backing.as_ptr() as usize;
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::new(base, backing.len()),
        };
        let bogus = encode_cap_handle(Some(CapHandle::from_raw(0, 0)));
        let effect = dispatch(
            &mut ctx,
            call(
                SyscallNumber::ConsoleWrite,
                [bogus, base as u64, backing.len() as u64, 0, 0, 0],
            ),
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
        let mut queues = IpcQueues::new();
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
        let backing = b"hi".to_vec();
        let base = backing.as_ptr() as usize;
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::new(base, backing.len()),
        };
        let effect = dispatch(
            &mut ctx,
            call(
                SyscallNumber::ConsoleWrite,
                [
                    encode_cap_handle(Some(wrong)),
                    base as u64,
                    backing.len() as u64,
                    0,
                    0,
                    0,
                ],
            ),
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
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let mut table = CapabilityTable::new();
        // Debug-console cap WITHOUT the CONSOLE_WRITE right.
        let cap = table
            .insert_root(Capability::new(CapRights::empty(), CapObject::DebugConsole))
            .unwrap();
        let console = FakeConsole::new();
        let backing = b"hi".to_vec();
        let base = backing.as_ptr() as usize;
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::new(base, backing.len()),
        };
        let effect = dispatch(
            &mut ctx,
            call(
                SyscallNumber::ConsoleWrite,
                [
                    encode_cap_handle(Some(cap)),
                    base as u64,
                    backing.len() as u64,
                    0,
                    0,
                    0,
                ],
            ),
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
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let (mut table, cons_cap) = table_with_console_cap();
        let console = FakeConsole::new();
        let message = b"tyrne: hello via console_write\n";
        let backing = message.to_vec();
        let base = backing.as_ptr() as usize; // expose provenance
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::new(base, backing.len()),
        };
        let effect = dispatch(
            &mut ctx,
            call(
                SyscallNumber::ConsoleWrite,
                [
                    encode_cap_handle(Some(cons_cap)),
                    base as u64,
                    backing.len() as u64,
                    0,
                    0,
                    0,
                ],
            ),
        );
        match effect {
            SyscallEffect::Resume(r) => {
                assert_eq!(r.status, 0);
                assert_eq!(r.payload[0], backing.len() as u64); // x1 = bytes written
            }
            other => panic!("expected Resume(ok), got {other:?}"),
        }
        assert_eq!(console.captured(), backing);
    }

    #[test]
    #[cfg(debug_assertions)] // console_write number 5 is debug-gated; release path tested separately
    fn console_write_spanning_multiple_chunks_emits_all_bytes() {
        // Exercise the chunking loop: a buffer larger than one chunk.
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let (mut table, cons_cap) = table_with_console_cap();
        let console = FakeConsole::new();
        let len = CONSOLE_WRITE_CHUNK * 2 + 7;
        let backing: Vec<u8> = (0..len).map(|i| (i % 251) as u8).collect();
        let base = backing.as_ptr() as usize;
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::new(base, backing.len()),
        };
        let effect = dispatch(
            &mut ctx,
            call(
                SyscallNumber::ConsoleWrite,
                [
                    encode_cap_handle(Some(cons_cap)),
                    base as u64,
                    backing.len() as u64,
                    0,
                    0,
                    0,
                ],
            ),
        );
        match effect {
            SyscallEffect::Resume(r) => assert_eq!(r.payload[0], len as u64),
            other => panic!("expected Resume(ok), got {other:?}"),
        }
        assert_eq!(console.captured(), backing);
    }

    #[test]
    #[cfg(debug_assertions)] // console_write number 5 is debug-gated; release path tested separately
    fn console_write_out_of_range_buffer_faults_without_output() {
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let (mut table, cons_cap) = table_with_console_cap();
        let console = FakeConsole::new();
        let backing = b"unreachable".to_vec();
        let base = backing.as_ptr() as usize;
        // Window covers a different region than the buffer pointer.
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::new(base.wrapping_add(0x1_0000), backing.len()),
        };
        let effect = dispatch(
            &mut ctx,
            call(
                SyscallNumber::ConsoleWrite,
                [
                    encode_cap_handle(Some(cons_cap)),
                    base as u64,
                    backing.len() as u64,
                    0,
                    0,
                    0,
                ],
            ),
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

    // ── release debug-gate ───────────────────────────────────────────────────

    #[test]
    #[cfg(not(debug_assertions))]
    fn console_write_number_is_bad_syscall_in_release_build() {
        // In a release build the debug-gate drops console_write from the
        // surface entirely, even for a holder of a valid debug-console cap.
        let mut ep_arena = EndpointArena::default();
        let mut queues = IpcQueues::new();
        let (mut table, cons_cap) = table_with_console_cap();
        let console = FakeConsole::new();
        let backing = b"nope".to_vec();
        let base = backing.as_ptr() as usize;
        let mut ctx = SyscallContext {
            ep_arena: &mut ep_arena,
            queues: &mut queues,
            caller_table: &mut table,
            console: &console,
            user_window: UserAccessWindow::new(base, backing.len()),
        };
        // Number 5 directly (SyscallNumber::ConsoleWrite::as_u64() == 5).
        let effect = dispatch(
            &mut ctx,
            SyscallArgs {
                number: 5,
                args: [
                    encode_cap_handle(Some(cons_cap)),
                    base as u64,
                    backing.len() as u64,
                    0,
                    0,
                    0,
                ],
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
}
