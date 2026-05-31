//! # tyrne-user
//!
//! Safe userspace wrappers over the Tyrne EL0 syscall ABI. This crate is what a
//! userspace program (e.g. [`tyrne-userland-hello`]) links against to invoke
//! syscalls without writing its own `unsafe` inline assembly.
//!
//! Each wrapper packs the [ADR-0030][adr-0030] register convention (`x8` =
//! number, `x0`–`x5` = arguments; `x0` = status, `x1`–`x7` = payload) around a
//! single `svc #0`, the [ADR-0031][adr-0031] trap instruction. The `unsafe`
//! surface is confined to the `svc` shims here; callers stay in safe Rust.
//!
//! The crate is `#![no_std]` and carries **no dependency on the kernel** — the
//! syscall numbers are restated here per [ADR-0031][adr-0031] (the contract is
//! the ABI, not a shared type). The host-side authority is
//! `tyrne_kernel::syscall::abi::SyscallNumber::as_u64`; if these drift, the
//! kernel's ABI host tests and this crate's numbers must be reconciled.
//!
//! [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
//! [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md

#![no_std]

use core::arch::asm;

/// `task_exit` syscall number (`x8`), per [ADR-0031][adr-0031]. Restated
/// userspace-side; the kernel authority is `SyscallNumber::TaskExit as 4`.
///
/// [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md
const SYS_TASK_EXIT: u64 = 4;

/// `console_write` syscall number (`x8`), per [ADR-0031][adr-0031]. **Debug-gated**
/// in the kernel (number `5` decodes to a syscall only in a debug build; a
/// release kernel returns `BadSyscallNumber` and emits nothing). Restated
/// userspace-side; the kernel authority is `SyscallNumber::ConsoleWrite as 5`.
///
/// [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md
const SYS_CONSOLE_WRITE: u64 = 5;

/// The capability word the first userspace task ([`tyrne-userland-hello`]) names
/// for its debug console — the **T-027 ↔ T-028 interface** (per
/// [ADR-0039][adr-0039]). It is the packed handle of the **root** capability of
/// a freshly created table: index `0`, generation `0`, so the ABI packing
/// `(generation << 16) | index` yields `0`. The EL0 wire-up (T-028) **must**
/// seed the task's `DebugConsole` capability so it resolves to this handle
/// (`insert_root` into a fresh table yields index 0 / generation 0). Defined
/// once here; not duplicated by value across the program and the seeding site.
///
/// [adr-0039]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0039-userland-build-pipeline.md
pub const HELLO_CONSOLE_CAP: u64 = 0;

/// A syscall rejection: the non-zero kernel status word returned in `x0`. `0`
/// means success and is never wrapped in this type (the wrappers return `Ok`).
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub struct SyscallError(
    /// The raw kernel status word (`x0`); the low/high blocks encode the
    /// kernel's `SyscallError` taxonomy ([ADR-0030][adr-0030]).
    ///
    /// [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
    pub u64,
);

/// Write `buf` to the debug console named by the capability word `cap`.
///
/// Returns the number of bytes the kernel accepted on success, or the raw
/// kernel status word on rejection (an absent/wrong capability, an
/// out-of-window or untranslatable buffer, etc. — the kernel dispatcher is
/// panic-free and fails closed). `cap` is a packed handle into the **caller's
/// own** capability table (e.g. [`HELLO_CONSOLE_CAP`]); it grants nothing the
/// task does not already hold.
///
/// # Errors
///
/// Returns [`SyscallError`] wrapping the non-zero `x0` status when the kernel
/// rejects the call.
#[allow(
    clippy::cast_possible_truncation,
    reason = "the returned byte count is <= buf.len() <= usize::MAX; the u64 -> usize \
              cast is lossless on every supported (64-bit) target"
)]
pub fn console_write(cap: u64, buf: &[u8]) -> Result<usize, SyscallError> {
    let status: u64;
    let written: u64;
    // SAFETY: `svc #0` is the EL0→EL1 syscall trap. We load the ABI registers
    // exactly per ADR-0030 — x8 = the console_write number, x0 = the capability
    // word, x1 = the buffer base pointer, x2 = the length — and read back
    // x0 = status and x1 = the accepted byte count. The kernel dispatcher is
    // panic-free and, post-gate-#1 (T-025), translates [x1, x1+x2) through the
    // caller's own address space requiring USER, copying at most `buf.len()`
    // bytes; it never writes through these pointers and never touches userspace
    // memory outside `buf`. `buf` is only read (a shared borrow). x3..x7 are
    // marked clobbered (caller-saved scratch/payload). No flags or stack state
    // are relied upon across the trap. Audit: UNSAFE-2026-0033.
    unsafe {
        asm!(
            "svc #0",
            in("x8") SYS_CONSOLE_WRITE,
            inout("x0") cap => status,
            inout("x1") buf.as_ptr() as u64 => written,
            in("x2") buf.len() as u64,
            lateout("x3") _,
            lateout("x4") _,
            lateout("x5") _,
            lateout("x6") _,
            lateout("x7") _,
        );
    }
    if status == 0 {
        Ok(written as usize)
    } else {
        Err(SyscallError(status))
    }
}

/// Terminate the current task with exit `code`. Does not return — the kernel
/// removes the task from the scheduler and never re-enters it.
pub fn task_exit(code: u64) -> ! {
    // SAFETY: `svc #0` with x8 = the task_exit number and x0 = the exit code.
    // task_exit acts on the caller's own task identity (no capability), and the
    // kernel terminates the task without returning to EL0, so the
    // `options(noreturn)` contract holds. Only x0 is passed; no memory is
    // accessed. Audit: UNSAFE-2026-0033.
    unsafe {
        asm!(
            "svc #0",
            in("x8") SYS_TASK_EXIT,
            in("x0") code,
            options(noreturn),
        );
    }
}
