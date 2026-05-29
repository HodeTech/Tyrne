//! Validated copy-from / copy-to user memory.
//!
//! A syscall handler must never dereference a raw user pointer without first
//! proving the requested `[ptr, ptr + len)` byte range lies inside the active
//! address space's user-accessible region ([ADR-0030 §Simulation row 4][adr-0030],
//! [P4][principles]). [`UserAccessWindow`] models that region; [`copy_from_user`]
//! / [`copy_to_user`] validate against it and only then move bytes.
//!
//! ## v1 window model and forward path
//!
//! v1 models the active address space's accessible region as a **single
//! contiguous half-open VA window** `[base, base + len)` and performs the byte
//! move under the kernel's identity map ([ADR-0027 §Decision outcome (a)][adr-0027]:
//! every PA in the managed extent is reachable at `VA == PA` from kernel code).
//! This is the granularity v1 can express — the [`Mmu`][mmu] trait exposes no
//! translation-walk query, and the only `SVC` B5 runs comes from an **EL1
//! kernel-stub** on the identity-mapped bootstrap AS (so `user VA == kernel VA`).
//!
//! When a real EL0 task runs against a *separate* userspace `TTBR0_EL1` (Phase
//! B6, gated on the [ADR-0033 high-half placeholder][adr-0027]), this validator
//! tightens in two forward-compatible ways that **do not** change the
//! [`copy_from_user`] / [`copy_to_user`] call-site signatures: (1) the window is
//! derived from the EL0 task's actually-mapped image+stack region rather than
//! the identity-mapped RAM extent, and (2) the int-to-pointer dereference is
//! replaced by a per-page translation of the user VA to a kernel-reachable VA
//! (the same single-helper-body migration [`crate::mm::phys_frame_kernel_ptr`]
//! documents). The window-containment check, the wrap rejection, and the
//! zero-length short-circuit below are unchanged by that migration.
//!
//! [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
//! [adr-0027]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0027-kernel-virtual-memory-layout.md
//! [mmu]: tyrne_hal::Mmu
//! [principles]: https://github.com/HodeTech/Tyrne/blob/main/docs/standards/architectural-principles.md

use super::error::SyscallError;

/// A validated view of the active address space's user-accessible bytes.
///
/// v1 carries a single contiguous half-open VA window `[base, base + len)`; see
/// the module docs for the window model and the B6 forward path. A copy whose
/// `[ptr, ptr + len)` range is not wholly contained in the window — or that
/// wraps past `usize::MAX` — is rejected with [`SyscallError::FaultAddress`]
/// **before** any pointer is dereferenced.
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub struct UserAccessWindow {
    base: usize,
    len: usize,
}

impl UserAccessWindow {
    /// Construct a window covering the half-open VA range `[base, base + len)`.
    #[must_use]
    pub const fn new(base: usize, len: usize) -> Self {
        Self { base, len }
    }

    /// Construct an empty window that accepts only zero-length accesses.
    ///
    /// The dispatcher uses this as a safe default when no active user region is
    /// known (e.g. a context with no mapped userspace); any non-zero copy
    /// against it returns [`SyscallError::FaultAddress`].
    #[must_use]
    pub const fn empty() -> Self {
        Self { base: 0, len: 0 }
    }

    /// Validate that `[ptr, ptr + len)` lies wholly within this window.
    ///
    /// A zero-length access is always accepted (it touches no bytes, so no
    /// containment is required). A range that wraps past `usize::MAX`, or that
    /// falls partly or wholly outside `[base, base + len)`, is rejected.
    ///
    /// # Errors
    ///
    /// [`SyscallError::FaultAddress`] if the range wraps or is not contained.
    pub fn validate(&self, ptr: usize, len: usize) -> Result<(), SyscallError> {
        if len == 0 {
            // Empty range touches no bytes; trivially in-bounds.
            return Ok(());
        }
        // `checked_add` (not `+`) both satisfies `clippy::arithmetic_side_effects`
        // and is the actual wrap check: a request whose end overflows `usize`
        // is a fault, never a silently-wrapped in-range access.
        let Some(end) = ptr.checked_add(len) else {
            return Err(SyscallError::FaultAddress);
        };
        let Some(window_end) = self.base.checked_add(self.len) else {
            return Err(SyscallError::FaultAddress);
        };
        if ptr >= self.base && end <= window_end {
            Ok(())
        } else {
            Err(SyscallError::FaultAddress)
        }
    }
}

/// Copy `dst.len()` bytes **from** user memory at `user_ptr` into `dst`.
///
/// Validates `[user_ptr, user_ptr + dst.len())` against `window` first; on any
/// failure the user pointer is **not** dereferenced. A zero-length `dst` is a
/// no-op that always succeeds.
///
/// # Errors
///
/// [`SyscallError::FaultAddress`] if the range is out of the window or wraps.
pub fn copy_from_user(
    window: &UserAccessWindow,
    user_ptr: usize,
    dst: &mut [u8],
) -> Result<(), SyscallError> {
    let len = dst.len();
    window.validate(user_ptr, len)?;
    if len > 0 {
        // SAFETY: the byte copy reads `len` bytes from the user VA `user_ptr`
        // into the kernel-owned `dst` slice.
        //
        // **Why `unsafe` is required.** `user_ptr` arrives as an integer
        // register word (the ABI passes user pointers as `u64`); reconstructing
        // a `*const u8` from it and reading through it cannot be expressed in
        // safe Rust — there is no safe `&[u8]` to borrow because the bytes live
        // in the caller's (userspace's) address space, named only by an integer
        // the kernel does not own a reference into.
        //
        // **Invariants upheld.** (1) **Range validity.** `window.validate`
        // above proved `[user_ptr, user_ptr + len)` is wholly contained in the
        // active address space's accessible window and does not wrap, so every
        // one of the `len` source bytes is a readable address in the active AS.
        // (2) **Identity map (v1).** Per [ADR-0027 §Decision outcome (a)] the
        // bootstrap AS the B5 EL1 kernel-stub runs on identity-maps the managed
        // extent, so `user_ptr` is directly readable by kernel code at `VA == PA`
        // (the B6 forward path replaces this with a per-page translation — see
        // the module docs — without changing this call site's contract).
        // (3) **Disjointness — the soundness basis.** `dst` is a valid Rust
        // slice (good for `len` writes by the slice invariant). Soundness
        // requires `[user_ptr, user_ptr + len)` and `dst` to be **disjoint**,
        // which holds structurally: `user_ptr` names *userspace* memory while
        // `dst` is a *kernel* buffer — distinct allocations in v1 (e.g.
        // `console_write`'s fresh 256-byte stack buffer), separate address
        // spaces in B6. `validate` proves *bounds*, not disjointness;
        // disjointness comes from the user/kernel memory model. An aliasing
        // `user_ptr` would be **UB regardless of the copy primitive**: `dst` is
        // `&mut` (exclusive), so an overlapping read through `user_ptr` violates
        // that exclusivity — empirically confirmed under Miri's Stacked Borrows
        // ("strongly protected" `Unique` tag). `core::ptr::copy` (memmove) is
        // used as the conservative primitive; it is *not* a licence to alias —
        // disjointness, not the primitive, is load-bearing. (`copy_nonoverlapping`
        // would be equally sound under that same disjointness invariant; `copy`
        // is kept so the primitive adds no overlap precondition of its own.)
        // (4) **No interleaving.** v1 is single-core cooperative and the SVC
        // handler runs with interrupts masked (exception entry masks `DAIF`),
        // so no peer mutates the source mid-copy.
        //
        // **Why safer alternatives were rejected.** `core::slice::from_raw_parts`
        // would borrow the user bytes as a `&[u8]` — still `unsafe`, same
        // provenance requirement, and it would advertise a borrow of memory the
        // kernel does not own; the explicit `core::ptr::copy` is the honest
        // expression of "read bytes the validator just bounded". A HAL trait
        // method would relocate the `unsafe` to the HAL surface without removing
        // it; user-memory access is a kernel-syscall concern, so the discipline
        // (validated-range-then-copy under the disjointness invariant) belongs here.
        //
        // Audit: UNSAFE-2026-0030.
        unsafe {
            core::ptr::copy(user_ptr as *const u8, dst.as_mut_ptr(), len);
        }
    }
    Ok(())
}

/// Copy `src.len()` bytes **to** user memory at `user_ptr` from `src`.
///
/// The symmetric write-side primitive to [`copy_from_user`]: validates the
/// range against `window` first, then moves bytes. No v1 syscall returns data
/// through a user pointer (`recv` returns its message in registers), so this
/// has no v1 caller yet — it is the natural completion of the validated
/// user-access primitive ([ADR-0030][adr-0030] dependency-chain step 5 names
/// "copy-from/to-user") and the first pointer-returning syscall (Phase B6+)
/// uses it without re-deriving the validation. Shares [`UserAccessWindow::validate`]
/// with [`copy_from_user`], so it is not speculative surface.
///
/// # Errors
///
/// [`SyscallError::FaultAddress`] if the range is out of the window or wraps.
///
/// [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
pub fn copy_to_user(
    window: &UserAccessWindow,
    user_ptr: usize,
    src: &[u8],
) -> Result<(), SyscallError> {
    let len = src.len();
    window.validate(user_ptr, len)?;
    if len > 0 {
        // SAFETY: the byte copy writes `len` bytes from the kernel-owned `src`
        // slice to the user VA `user_ptr`. The invariants from [`copy_from_user`]
        // hold with the direction reversed — range validity (just proven by
        // `window.validate`), the v1 identity map ([ADR-0027 §Decision outcome (a)]),
        // and no single-core interleaving under the interrupts-masked SVC handler.
        // The **soundness basis is again disjointness**: `src` (a kernel buffer)
        // and the userspace destination `[user_ptr, user_ptr + len)` are disjoint
        // by the user/kernel memory model. An aliasing pair would be UB regardless
        // of the copy primitive — `src` is `&` (shared, read-only for its
        // lifetime), so writing through `user_ptr` into bytes `src` covers
        // violates that borrow (Miri-confirmed). `core::ptr::copy` (memmove) is
        // the conservative primitive, not a licence to alias. Same
        // rejected-alternatives reasoning as `copy_from_user` (`from_raw_parts_mut`
        // relocates rather than removes the `unsafe`; a HAL method moves the audit
        // point off the syscall layer).
        // Audit: UNSAFE-2026-0030.
        unsafe {
            core::ptr::copy(src.as_ptr(), user_ptr as *mut u8, len);
        }
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
    use super::{copy_from_user, copy_to_user, UserAccessWindow};
    use crate::syscall::error::SyscallError;

    // Host tests follow the kernel's established Miri-clean pattern (see
    // `kernel/src/mm/pmm.rs::tests` + `task_loader::tests`): a real host
    // `Vec<u8>` provides backing memory, its pointer is *exposed* via
    // `as usize` when constructing the window, and the validated copy's
    // int-to-pointer dereference recovers that exposed provenance under
    // Miri's permissive-provenance mode. The integer the syscall ABI passes
    // is therefore a genuine, in-bounds host address in every success path;
    // the failure paths reject before any dereference, so they never need a
    // valid pointer at all.

    // ── range validation: in-range ───────────────────────────────────────────

    #[test]
    fn copy_from_user_in_range_moves_bytes() {
        let backing: Vec<u8> = (0..16u8).collect();
        let base = backing.as_ptr() as usize; // expose provenance
        let window = UserAccessWindow::new(base, backing.len());

        let mut dst = [0u8; 8];
        copy_from_user(&window, base, &mut dst).expect("in-range copy must succeed");
        assert_eq!(dst, [0, 1, 2, 3, 4, 5, 6, 7]);

        // An interior, in-range sub-slice also succeeds.
        let mut dst2 = [0u8; 4];
        copy_from_user(&window, base + 8, &mut dst2).expect("in-range interior copy");
        assert_eq!(dst2, [8, 9, 10, 11]);
    }

    #[test]
    fn copy_to_user_in_range_moves_bytes() {
        let mut backing: Vec<u8> = vec![0u8; 16];
        let base = backing.as_mut_ptr() as usize; // expose provenance
        let window = UserAccessWindow::new(base, backing.len());

        let src = [0xAAu8, 0xBB, 0xCC, 0xDD];
        copy_to_user(&window, base + 2, &src).expect("in-range copy_to_user");
        assert_eq!(&backing[2..6], &[0xAA, 0xBB, 0xCC, 0xDD]);
        // Bytes outside the written range are untouched.
        assert_eq!(backing[0], 0);
        assert_eq!(backing[6], 0);
    }

    // ── range validation: out-of-range ───────────────────────────────────────

    #[test]
    fn copy_from_user_out_of_range_faults_without_deref() {
        let backing: Vec<u8> = vec![0u8; 16];
        let base = backing.as_ptr() as usize;
        // Window covers a *different* region than the pointer we will read.
        let window = UserAccessWindow::new(base + 0x1000, 16);

        let mut dst = [0u8; 8];
        // `base` is below the window → fault, and the dereference never happens
        // (the assertion that this is safe is the whole point of the test).
        assert_eq!(
            copy_from_user(&window, base, &mut dst),
            Err(SyscallError::FaultAddress)
        );
    }

    #[test]
    fn copy_from_user_overrun_past_window_end_faults() {
        let backing: Vec<u8> = vec![0u8; 16];
        let base = backing.as_ptr() as usize;
        // Window is shorter than the requested read: [base, base+4) but read 8.
        let window = UserAccessWindow::new(base, 4);
        let mut dst = [0u8; 8];
        assert_eq!(
            copy_from_user(&window, base, &mut dst),
            Err(SyscallError::FaultAddress)
        );
    }

    #[test]
    fn copy_to_user_out_of_range_faults() {
        let mut backing: Vec<u8> = vec![0u8; 16];
        let base = backing.as_mut_ptr() as usize;
        let window = UserAccessWindow::new(base, 4);
        let src = [1u8, 2, 3, 4, 5, 6, 7, 8];
        assert_eq!(
            copy_to_user(&window, base, &src),
            Err(SyscallError::FaultAddress)
        );
        assert!(
            backing.iter().all(|&b| b == 0),
            "no byte may be written on fault"
        );
    }

    // ── range validation: zero-length ────────────────────────────────────────

    #[test]
    fn zero_length_copy_is_ok_even_for_unmapped_pointer() {
        // A zero-length copy touches no bytes, so it succeeds regardless of the
        // pointer — no dereference occurs. Use an empty window + an arbitrary
        // (never-dereferenced) address to prove the short-circuit.
        let window = UserAccessWindow::empty();
        let mut dst: [u8; 0] = [];
        assert_eq!(copy_from_user(&window, 0xDEAD_0000, &mut dst), Ok(()));
        let src: [u8; 0] = [];
        assert_eq!(copy_to_user(&window, 0xDEAD_0000, &src), Ok(()));
    }

    // ── range validation: wrap ───────────────────────────────────────────────

    #[test]
    fn wrapping_range_faults() {
        // A pointer near usize::MAX with a non-trivial length wraps; the
        // validator rejects it instead of computing a smaller wrapped end.
        let window = UserAccessWindow::new(0, usize::MAX);
        assert_eq!(
            window.validate(usize::MAX - 2, 8),
            Err(SyscallError::FaultAddress)
        );
        // And the copy entry points reject it before any dereference.
        let mut dst = [0u8; 8];
        assert_eq!(
            copy_from_user(&window, usize::MAX - 2, &mut dst),
            Err(SyscallError::FaultAddress)
        );
    }

    #[test]
    fn validate_exact_window_fit_is_ok() {
        // [base, base+len) fitting the window exactly (end == window_end) is in
        // bounds — the half-open boundary is inclusive of the last byte.
        let window = UserAccessWindow::new(0x1000, 0x100);
        assert_eq!(window.validate(0x1000, 0x100), Ok(()));
        assert_eq!(window.validate(0x1080, 0x80), Ok(()));
        // One byte past the end faults.
        assert_eq!(
            window.validate(0x1000, 0x101),
            Err(SyscallError::FaultAddress)
        );
    }
}
