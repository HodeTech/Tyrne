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
//! ## The `0x200` / `0x400` split
//!
//! The shared trampoline is installed at **both** sync vector slots — current-EL
//! (`VBAR_EL1 + 0x200`) and lower-EL-AArch64 (`VBAR_EL1 + 0x400`) — because the
//! save → dispatch → `ERET` mechanism is privilege-entry-agnostic. The only
//! `SVC` today comes from the [`crate::syscall_boundary_smoke`] EL1 stub, which —
//! executing at the *current* EL — takes the `0x200` vector. A real EL0 task
//! taking the `0x400` vector (with the EL0↔EL1 privilege transition and copy-user
//! against a separate userspace `TTBR0_EL1`) is the B6 wire-up, per
//! [ADR-0030 §Simulation row-to-verification mapping][adr-0030]. The `0x400`
//! handler is installed now so the wire-up adds only the EL0 task, not new trap
//! plumbing.
//!
//! `caller_table` is sourced per-syscall from the **scheduler's running task**
//! (gate #3 / T-026): `syscall_entry` resolves the current task's own capability
//! table, address space, and user-access window from `SCHED.current`, and **fails
//! closed** when no task is current — the empty [`crate::FAILCLOSED_TABLE`] (every
//! lookup → `InvalidHandle`) + an empty window, so a syscall with no running task
//! names no capability and copies no byte.
//!
//! Audit: UNSAFE-2026-0029 (the trap-frame asm + this entry's frame
//! reads/writes).
//!
//! [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md

use tyrne_hal::Console; // `write_bytes` (the task-exit termination report)
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

// The B5 whole-RAM-extent `SYSCALL_USER_WINDOW_LEN` is gone: post-gate-#3
// (T-026) the user-access window is **per task**, sourced from the scheduler's
// current task (`current_user_window()`), not a fixed extent — see `syscall_entry`.

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
/// **Invariants upheld.** (1) The statics it reaches (`SCHED` / `EP_ARENA` /
/// `IPC_QUEUES` / `CONSOLE` / `MMU` / `AS_ARENA` / `FAILCLOSED_TABLE` /
/// `BOOTSTRAP_AS`) are all written before the syscall smoke issues any `SVC` —
/// the smoke is sequenced *after* `SCHED` is published, so `SCHED.current` reads
/// a valid (empty, not-yet-started) scheduler; (2) v1 is single-core and the
/// `SVC` handler runs with interrupts masked (exception entry masks `DAIF`), so
/// no peer aliases them mid-call; (3) the momentary `&mut`s are scoped to the
/// single `dispatch` call and do not cross a context switch — the data-plane
/// syscalls do not switch and the control-plane ones return a directive *before*
/// any switch, honouring the [ADR-0021] discipline; (4) the frame writes touch
/// only `x0`–`x7`, leaving the trampoline's restore of `x8`–`x30` + `SP_EL0` +
/// `ELR_EL1` + `SPSR_EL1` intact; (5) **gate #3 (M4):** with a current EL0 task,
/// `caller_table` is `&mut *current_user_table()` — a momentary `&mut` to the
/// task's own capability table (a BSP static recorded by `add_user_task` via the
/// [ADR-0021] raw-pointer bridge), lexically contained to this one `dispatch`
/// call and never crossing a switch; with no current task, missing task window,
/// or stale / absent task address-space handle, it is the empty `FAILCLOSED_TABLE`
/// (every lookup → `InvalidHandle`) and `task_as` the never-dereferenced
/// bootstrap-AS placeholder behind an empty window, so an incomplete running-task
/// context names no capability and copies no byte (UNSAFE-2026-0014 Amendment).
/// **Rejected alternatives.** Passing a `&mut
/// SyscallTrapFrame` from the asm is impossible (asm has no Rust references);
/// holding the BSP statics behind a lock would deadlock the interrupts-masked
/// handler with no soundness gain under single-core cooperative semantics.
///
/// Audit: UNSAFE-2026-0029 (trap-frame asm + frame access) + UNSAFE-2026-0010
/// (`StaticCell` pattern) + UNSAFE-2026-0014 (momentary `&mut` to kernel state,
/// incl. the gate-#3 cap-table-pointer deref).
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

    // SAFETY: build the dispatch context from the **running EL0 task's**
    // bindings, sourced from the scheduler (gate #3 / T-026), or the FAIL-CLOSED
    // default when the running-task syscall context is incomplete. `SCHED` /
    // `EP_ARENA` / `IPC_QUEUES` / `CONSOLE` / `MMU` / `AS_ARENA` /
    // `FAILCLOSED_TABLE` / `BOOTSTRAP_AS` are all published before the
    // (post-`SCHED`-init) smoke runs; single-core + interrupts-masked ⇒ no
    // aliasing; the momentary `&mut`s drop at the end of `dispatch` and never
    // cross a switch. The `&mut *table_ptr` is the gate-#3 cap-table dereference
    // (M4 — UNSAFE-2026-0014 Amendment; see this fn's `# Safety`). Audit:
    // UNSAFE-2026-0010 + UNSAFE-2026-0014 + UNSAFE-2026-0029.
    let effect = unsafe {
        let sched = (*crate::SCHED.0.get()).assume_init_ref();
        let current_table = sched.current_user_table();
        let current_as = sched.current_address_space_handle();
        let current_window = sched.current_user_window();

        // Accept the running task's syscall context only as a complete unit:
        // table + user window + generation-checked AS. Any missing / stale piece
        // makes the whole context all-or-nothing fail-closed — the empty table +
        // empty window (so data-plane syscalls grant no cap and copy no byte from
        // a partially bound task) AND `has_current_task = false` (so the
        // control-plane syscalls, which consult no capability, are rejected too).
        let arena = (*crate::AS_ARENA.0.get()).assume_init_ref();
        let resolved_task_as =
            current_as.and_then(|h| tyrne_kernel::mm::get_address_space(arena, h));
        let (caller_table, user_window, task_as, has_current_task) =
            match (current_table, current_window, resolved_task_as) {
                (Some(table_ptr), Some(window), Some(asp)) => {
                    (&mut *table_ptr, window, asp.inner(), true)
                }
                _ => (
                    (*crate::FAILCLOSED_TABLE.0.get()).assume_init_mut(),
                    UserAccessWindow::empty(),
                    (*crate::BOOTSTRAP_AS.0.get()).assume_init_ref(),
                    false,
                ),
            };

        let mut ctx = SyscallContext {
            ep_arena: (*crate::EP_ARENA.0.get()).assume_init_mut(),
            queues: (*crate::IPC_QUEUES.0.get()).assume_init_mut(),
            caller_table,
            console: (*crate::CONSOLE.0.get()).assume_init_ref(),
            user_window,
            mmu: (*crate::MMU.0.get()).assume_init_ref(),
            task_as,
            has_current_task,
        };
        dispatch(&mut ctx, args)
    };

    // T-029 Phase 2 (perf-bench measurement build only): time consecutive EL0
    // syscall round-trips kernel-side and, after N, force `Terminate` to end the
    // bench EL0 task (handing off to the ctx/IPC benches). Feature-gated, so
    // production `syscall_entry` is byte-identical. See `perf_bench`.
    #[cfg(feature = "perf-bench")]
    let effect = crate::perf_bench::el0_roundtrip_tick(effect);

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
            // task_yield (T-028): cooperatively yield the CPU. `yield_now`
            // re-enqueues the current EL0 task `Ready` + switches to the next;
            // when this task is re-dispatched `yield_now` returns here and we
            // `ERET` back to EL0 with `x0 = Ok` (task_yield "always succeeds in
            // v1" — ADR-0031). Reached only with a current task (the dispatcher
            // returns `Resume(InvalidHandle)` when none — handled above).
            // NOTE: `hello` does not call task_yield, so this BSP path is wired
            // but exercised only by a future userspace task; `yield_now`'s logic
            // is host-tested, and `enter_el0` is one-shot so later resumes take
            // this cooperative path (UNSAFE-2026-0032).
            //
            // SAFETY: `SCHED` + `CPU` are published before `start()`; the SVC
            // handler runs single-core with IRQs masked (exception entry), so no
            // peer aliases them. `yield_now` honours the [ADR-0021] no-`&mut`-
            // across-switch discipline and resumes this frame on re-dispatch.
            // Audit: UNSAFE-2026-0008 + UNSAFE-2026-0014 + UNSAFE-2026-0029.
            unsafe {
                let cpu = (*crate::CPU.0.get()).assume_init_ref();
                let res = tyrne_kernel::sched::yield_now(
                    crate::SCHED.as_mut_ptr(),
                    cpu,
                    crate::activate_address_space,
                );
                // `yield_now`'s only `Err` is `NoCurrentTask`, which gate #3
                // precludes here (this arm is reached only with a current task).
                // Assert it so a broken invariant surfaces in debug instead of
                // being masked by the `OK_STATUS` below. task_yield "always
                // succeeds in v1" (ADR-0031), so EL0 still resumes Ok.
                debug_assert!(
                    res.is_ok(),
                    "task_yield: yield_now failed unexpectedly (NoCurrentTask should be precluded by gate #3): {res:?}"
                );
                (*frame).x0_x1[0] = tyrne_kernel::syscall::OK_STATUS;
            }
        }
        SyscallEffect::Terminate(_code) => {
            // task_exit (T-028): terminate the current EL0 task + dispatch the
            // next. `task_exit_current` is `-> !`: it switches to the next ready
            // task (or idle) and **abandons this syscall-handler frame**, so we
            // never `ERET` back to the exiting task (honouring the ABI's "does
            // not return"). The exiting task's slot / AS / cap table are not
            // reclaimed in v1 (the deferred SEC-T024-01 object-lifecycle gap).
            // Reached only with a current task (gate #3 rejects it otherwise).
            // The exit code is unused in v1 (the scheduler tracks no exit status).
            //
            // SAFETY: `SCHED` + `CPU` + `CONSOLE` are published before `start()`;
            // single-core + IRQs masked in the SVC handler; `task_exit_current`
            // honours the [ADR-0021] discipline and abandons this frame (its
            // throwaway context is never restored). Audit: UNSAFE-2026-0008 +
            // UNSAFE-2026-0014 + UNSAFE-2026-0029.
            unsafe {
                let console = (*crate::CONSOLE.0.get()).assume_init_ref();
                console.write_bytes(b"tyrne: userspace task exited\n");
                let cpu = (*crate::CPU.0.get()).assume_init_ref();
                tyrne_kernel::sched::task_exit_current(
                    crate::SCHED.as_mut_ptr(),
                    cpu,
                    crate::activate_address_space,
                );
            }
        }
    }
}
