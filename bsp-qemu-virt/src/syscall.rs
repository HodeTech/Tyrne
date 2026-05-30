//! BSP-side syscall glue: the `SVC` trap frame and the Rust entry the
//! `vectors.s` sync trampoline calls.
//!
//! The architecture-agnostic, panic-free dispatch logic lives in the kernel
//! ([`tyrne_kernel::syscall`]). This module owns only the **hardware-facing**
//! half:
//!
//! - [`SyscallTrapFrame`] — the `#[repr(C)]` mirror of the register frame the
//!   `tyrne_sync_trampoline` in `vectors.s` saves (`x0`–`x30` + `SP_EL0` +
//!   `ELR_EL1` + `SPSR_EL1`); its field order and offsets must match the asm
//!   `stp` sequence byte-for-byte (a compile-time `size_of` guard catches drift).
//! - [`syscall_entry`] — reads the syscall number + arguments from the saved
//!   frame, builds a [`SyscallContext`] from the BSP statics, calls
//!   [`tyrne_kernel::syscall::dispatch`], and applies the returned
//!   [`SyscallEffect`] by writing the status + payload back into the frame.
//!
//! ## B5 scope and the `0x200` / `0x400` split
//!
//! The shared trampoline is installed at **both** sync vector slots — current-EL
//! (`VBAR_EL1 + 0x200`) and lower-EL-AArch64 (`VBAR_EL1 + 0x400`) — because the
//! save → dispatch → `ERET` mechanism is privilege-entry-agnostic. In B5 the
//! only `SVC` comes from an **EL1 kernel-stub** (see `kernel_entry`'s syscall
//! smoke), which — executing at the *current* EL — takes the `0x200` vector,
//! **not** the lower-EL `0x400` vector. A real EL0 task taking the `0x400`
//! vector (with the EL0↔EL1 privilege transition and copy-user against a
//! separate userspace `TTBR0_EL1`) is verified at runtime in **B6**, per
//! [ADR-0030 §Simulation row-to-verification mapping][adr-0030]. The `0x400`
//! handler is installed now so B6 adds only the EL0 task, not new trap plumbing.
//!
//! `caller_table` is a dedicated **kernel-stub** capability table in B5
//! ([`crate::SYSCALL_STUB_TABLE`]); B6 replaces it with the scheduler's
//! current-task table once a real EL0 task exists.
//!
//! Audit: UNSAFE-2026-0029 (the trap-frame asm + this entry's frame
//! reads/writes).
//!
//! [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md

use tyrne_kernel::syscall::{
    dispatch, SyscallArgs, SyscallContext, SyscallEffect, UserAccessWindow,
};

/// Saved-register frame the `tyrne_sync_trampoline` in `vectors.s` populates
/// before branching into [`syscall_entry`] on an `SVC`.
///
/// `#[repr(C)]` is **mandatory**: the field order and byte offsets must match
/// the asm `stp` sequence in `vectors.s` exactly. The frame is 272 bytes total
/// (`x0`–`x29` as 15 pairs, then `x30`/`SP_EL0`, then `ELR_EL1`/`SPSR_EL1`),
/// 16-byte SP-aligned. Unlike the IRQ [`TrapFrame`][crate::exceptions::TrapFrame]
/// (which saves only the AAPCS64 caller-saved set), the syscall frame saves the
/// **full** general-purpose register file plus `SP_EL0` so it is a complete
/// snapshot of the trapped context — the shape a real EL0 task (B6) and any
/// future preemption arc require.
///
/// Fields are private: the only reader/writer is [`syscall_entry`] in this
/// module, and keeping the raw register snapshot un-`pub` avoids exposing
/// (or accidentally logging) trapped register contents elsewhere.
#[repr(C)]
pub struct SyscallTrapFrame {
    // `x0`–`x29` saved as 15 consecutive pairs at offsets 0x00..0xF0.
    x0_x1: [u64; 2],
    x2_x3: [u64; 2],
    x4_x5: [u64; 2],
    x6_x7: [u64; 2],
    x8_x9: [u64; 2],
    x10_x11: [u64; 2],
    x12_x13: [u64; 2],
    x14_x15: [u64; 2],
    x16_x17: [u64; 2],
    x18_x19: [u64; 2],
    x20_x21: [u64; 2],
    x22_x23: [u64; 2],
    x24_x25: [u64; 2],
    x26_x27: [u64; 2],
    x28_x29: [u64; 2],
    /// `x30` (LR) at 0xF0 and `SP_EL0` at 0xF8.
    x30_sp_el0: [u64; 2],
    /// `ELR_EL1` (return address) at 0x100 and `SPSR_EL1` (saved PSTATE) at 0x108.
    elr_spsr: [u64; 2],
}

// The trampoline reserves exactly 272 bytes and writes through fixed offsets
// mirroring the field order above. A size/layout drift between the asm and this
// `#[repr(C)]` would corrupt saved registers on every syscall; this guard fails
// the build before that can ship. (Mirrors the `TrapFrame` 192-byte guard.)
const _: () = assert!(core::mem::size_of::<SyscallTrapFrame>() == 272);

/// Length of the syscall copy-from/to-user window in B5: the whole RAM extent,
/// reached through the kernel's high-half direct map (post-T-022 / ADR-0033).
///
/// The B5 EL1 kernel-stub executes in the high half; its buffer — a
/// `.rodata`-resident `&[u8]` in the kernel image — is reachable at its
/// high-half VA, so the window base is `phys_to_kernel_va(PMM_EXTENT_START)`
/// (see [`syscall_entry`]) and the stub buffer is in range. Because the
/// stub's "user" pointer **is** a valid kernel VA, the dispatcher's direct
/// deref works for the stub; B6's real EL0 task instead lives at a *user* VA
/// in its own `TTBR0_EL1`, so B6 derives a tighter per-task window AND
/// replaces the direct deref with a per-page user-VA→kernel-VA translation
/// (T-021 carry-forward gate #1 — see [`UserAccessWindow`]'s module docs).
/// The subtraction is a `const`, so it
/// cannot wrap at runtime: const-eval rejects an underflow at **build time**
/// (an inverted extent is a hard compile error, never a release wrap). The
/// explicit assertion below makes that invariant — and its failure message —
/// unambiguous rather than relying on a raw "subtract with overflow" const-eval
/// error.
const _: () = assert!(
    crate::PMM_EXTENT_END >= crate::PMM_EXTENT_START,
    "PMM extent must be non-inverted: PMM_EXTENT_END >= PMM_EXTENT_START"
);
const SYSCALL_USER_WINDOW_LEN: usize = crate::PMM_EXTENT_END - crate::PMM_EXTENT_START;

/// Rust entry for the `SVC` sync trampoline (`vectors.s`).
///
/// Reads the syscall number (`x8`) and arguments (`x0`–`x5`) from the saved
/// `frame`, dispatches through [`tyrne_kernel::syscall::dispatch`], and applies
/// the resulting [`SyscallEffect`] by writing the status (`x0`) and payload
/// (`x1`–`x7`) back into the frame. Returns to the trampoline, which restores
/// the (now result-bearing) frame and `ERET`s.
///
/// # Safety
///
/// `extern "C"` so the asm trampoline can `bl` it. `frame` is guaranteed valid
/// by the trampoline (constructed via `stp` immediately before the `bl`, on the
/// kernel stack); this function dereferences it only inside `unsafe` blocks.
///
/// **Why `unsafe` is required.** The function reads and writes the saved
/// register frame through a raw `*mut SyscallTrapFrame` (the asm calling
/// convention passes a pointer, not a `&mut`), and it materialises momentary
/// references to the write-once BSP statics via `assume_init_{mut,ref}`.
/// **Invariants upheld.** (1) The four statics it reaches
/// (`EP_ARENA` / `IPC_QUEUES` / `SYSCALL_STUB_TABLE` / `CONSOLE`) are all
/// written before the syscall smoke issues any `SVC`; (2) v1 is single-core and
/// the `SVC` handler runs with interrupts masked (exception entry masks `DAIF`),
/// so no peer aliases them mid-call; (3) the momentary `&mut`s are scoped to the
/// single `dispatch` call and do not cross a context switch — the data-plane
/// syscalls do not switch and the control-plane ones return a directive *before*
/// any switch, honouring the [ADR-0021] discipline; (4) the frame writes touch
/// only `x0`–`x7`, leaving the trampoline's restore of `x8`–`x30` + `SP_EL0` +
/// `ELR_EL1` + `SPSR_EL1` intact. **Rejected alternatives.** Passing a `&mut
/// SyscallTrapFrame` from the asm is impossible (asm has no Rust references);
/// holding the BSP statics behind a lock would deadlock the interrupts-masked
/// handler with no soundness gain under single-core cooperative semantics.
///
/// Audit: UNSAFE-2026-0029 (trap-frame asm + frame access) + UNSAFE-2026-0010
/// (`StaticCell` pattern) + UNSAFE-2026-0014 (momentary `&mut` to kernel state).
#[unsafe(no_mangle)]
pub unsafe extern "C" fn syscall_entry(frame: *mut SyscallTrapFrame) {
    // SAFETY: `frame` is valid per the trampoline contract above; read the
    // syscall number (x8) and argument words (x0..x5) out of the saved frame.
    // Audit: UNSAFE-2026-0029.
    let args = unsafe {
        let f = &*frame;
        SyscallArgs {
            number: f.x8_x9[0],
            args: [
                f.x0_x1[0], f.x0_x1[1], f.x2_x3[0], f.x2_x3[1], f.x4_x5[0], f.x4_x5[1],
            ],
        }
    };

    // SAFETY: build the dispatch context from the write-once BSP statics. All
    // four are initialised in `kernel_entry` before the syscall smoke runs;
    // single-core + interrupts-masked-in-handler means no aliasing; the
    // momentary `&mut`s drop at the end of the `dispatch` call and never cross a
    // switch. Audit: UNSAFE-2026-0010 (StaticCell) + UNSAFE-2026-0014 (momentary
    // `&mut` to kernel state) + UNSAFE-2026-0029 (the syscall arc).
    let effect = unsafe {
        let mut ctx = SyscallContext {
            ep_arena: (*crate::EP_ARENA.0.get()).assume_init_mut(),
            queues: (*crate::IPC_QUEUES.0.get()).assume_init_mut(),
            caller_table: (*crate::SYSCALL_STUB_TABLE.0.get()).assume_init_mut(),
            console: (*crate::CONSOLE.0.get()).assume_init_ref(),
            user_window: UserAccessWindow::new(
                tyrne_hal::phys_to_kernel_va(crate::PMM_EXTENT_START),
                SYSCALL_USER_WINDOW_LEN,
            ),
        };
        dispatch(&mut ctx, args)
    };

    match effect {
        SyscallEffect::Resume(r) => {
            // SAFETY: write the status (x0) + payload (x1..x7) back into the
            // saved frame; the trampoline restores them on `ERET`. Touches only
            // x0..x7. Audit: UNSAFE-2026-0029.
            unsafe {
                let f = &mut *frame;
                f.x0_x1[0] = r.status; // x0 = status
                f.x0_x1[1] = r.payload[0]; // x1
                f.x2_x3[0] = r.payload[1]; // x2
                f.x2_x3[1] = r.payload[2]; // x3
                f.x4_x5[0] = r.payload[3]; // x4
                f.x4_x5[1] = r.payload[4]; // x5
                f.x6_x7[0] = r.payload[5]; // x6
                f.x6_x7[1] = r.payload[6]; // x7
            }
        }
        SyscallEffect::Reschedule => {
            // task_yield. v1 B5 stand-in: there is no scheduler-resident EL0
            // task issuing this (the smoke runs the stub before `start()`), so
            // the real `yield_now` wiring lands in B6 once the caller is an EL0
            // task. The dispatcher-level routing (number 3 → Reschedule) is
            // host-tested; here we resume with `Ok` (x0 = 0) — task_yield
            // "always succeeds in v1" per ADR-0031.
            // SAFETY: write x0 only. Audit: UNSAFE-2026-0029.
            unsafe {
                (*frame).x0_x1[0] = tyrne_kernel::syscall::OK_STATUS;
            }
        }
        SyscallEffect::Terminate(_code) => {
            // task_exit. The ABI says "does not return", but v1 has no EL0
            // context register file to drop — real termination lands in B6. The
            // dispatcher-level routing (number 4 → Terminate) is host-tested;
            // here we defensively resume with `Ok` so a stray kernel-stub
            // task_exit cannot wedge the boot before B6 wires real termination.
            // SAFETY: write x0 only. Audit: UNSAFE-2026-0029.
            unsafe {
                (*frame).x0_x1[0] = tyrne_kernel::syscall::OK_STATUS;
            }
        }
    }
}
