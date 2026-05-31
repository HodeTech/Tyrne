//! Validated copy-from / copy-to user memory.
//!
//! A syscall handler must never dereference a raw user pointer without first
//! proving the requested `[ptr, ptr + len)` byte range lies inside the active
//! address space's user-accessible region ([ADR-0030 §Simulation row 4][adr-0030],
//! [P4][principles]) **and** that every page it spans is actually mapped
//! `USER`-accessible in the task's own translation tables. [`UserAccessWindow`]
//! models the first (range) gate; [`copy_from_user`] / [`copy_to_user`] add the
//! per-page translation gate and only then move bytes.
//!
//! ## Window first-gate + per-page translation (ADR-0038 / gate #1)
//!
//! Two layers, both load-bearing:
//!
//! 1. **[`UserAccessWindow`] — the cheap first gate.** A single contiguous
//!    half-open VA window `[base, base + len)` derived per task from its mapped
//!    image+stack span. It rejects an out-of-range or wrapping request before
//!    any page-table walk. It bounds the range; it does **not** prove ownership.
//! 2. **Per-page `Mmu::translate` — the load-bearing boundary.** For every page
//!    the range spans, the copy resolves the user VA through the task's own
//!    translation regime ([`Mmu::translate`][translate]) and **requires
//!    [`MappingFlags::USER`]** (plus [`MappingFlags::WRITE`] for the write
//!    direction). This is the confused-deputy defence: a kernel (non-`USER`)
//!    page that merely falls in-window is rejected with
//!    [`SyscallError::FaultAddress`], so an EL0 caller cannot name privileged
//!    memory ([phase-b §B6 gate #1][gate1]). The translated frame is rebased to
//!    a kernel-reachable pointer through the high-half direct map
//!    ([`crate::mm::phys_frame_kernel_ptr`], [ADR-0033][adr-0033]).
//!
//! **All-or-nothing (two-pass).** Both copy entry points first *probe* every
//! spanned page (translate + permission check); only if every page passes does
//! the copy phase run. A fault on the probe pass moves **zero** bytes — no
//! prefix is committed on a mid-range fault. (`console_write` adds its own
//! whole-range probe so a multi-chunk emit is likewise all-or-nothing.)
//!
//! This replaces the v1 identity-map int-to-pointer dereference (B5, when the
//! only `SVC` caller was an EL1 kernel stub on the identity-mapped bootstrap AS).
//! The `copy_from_user` / `copy_to_user` *contract* (validate, then move; zero-
//! length short-circuit; `FaultAddress` on failure) is unchanged; the function
//! signatures gain a `mmu` + `task_as` (the trait surface the translation needs).
//!
//! [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
//! [adr-0033]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0033-kernel-high-half-migration.md
//! [translate]: tyrne_hal::Mmu::translate
//! [gate1]: https://github.com/HodeTech/Tyrne/blob/main/docs/roadmap/phases/phase-b.md
//! [principles]: https://github.com/HodeTech/Tyrne/blob/main/docs/standards/architectural-principles.md

use tyrne_hal::{MappingFlags, Mmu, VirtAddr, PAGE_SIZE};

use crate::mm::phys_frame_kernel_ptr;

use super::error::SyscallError;

/// Low 12 bits of a page-aligned address — `va & !PAGE_MASK` is the page base,
/// `va & PAGE_MASK` the in-page offset. A const so the `- 1` is compile-time
/// (no runtime arithmetic for the `arithmetic_side_effects` lint).
const PAGE_MASK: usize = PAGE_SIZE - 1;

/// A validated view of the active address space's user-accessible bytes.
///
/// Carries a single contiguous half-open VA window `[base, base + len)` — the
/// cheap **first gate** (range/wrap/zero-length) per the module docs. A copy
/// whose `[ptr, ptr + len)` range is not wholly contained in the window — or
/// that wraps past `usize::MAX` — is rejected with [`SyscallError::FaultAddress`]
/// **before** any pointer is dereferenced. Ownership/permission is proven
/// separately by the per-page [`Mmu::translate`][tyrne_hal::Mmu::translate]
/// `USER` check in [`copy_from_user`] / [`copy_to_user`].
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
    /// The dispatcher uses this as the fail-closed default when no active user
    /// region is known (e.g. a context with no mapped userspace, or an
    /// unresolved current task); any non-zero copy against it returns
    /// [`SyscallError::FaultAddress`].
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

/// Probe every page the range `[user_ptr, user_ptr + len)` spans: resolve it
/// through `task_as` ([`Mmu::translate`][tyrne_hal::Mmu::translate]) and require
/// [`MappingFlags::USER`] (plus [`MappingFlags::WRITE`] when `require_write`).
///
/// This is the **all-or-nothing probe pass**: a single failing page rejects the
/// whole copy before any byte moves. `console_write` also calls it directly to
/// make a multi-chunk emit all-or-nothing. `len` must be non-zero (callers
/// short-circuit a zero-length copy before probing).
///
/// # Errors
///
/// [`SyscallError::FaultAddress`] on a wrap, a translate failure
/// ([`MmuError::NotMapped`][nm] / [`MmuError::BlockMapped`][bm]), or a leaf
/// missing the required permission.
///
/// [nm]: tyrne_hal::MmuError::NotMapped
/// [bm]: tyrne_hal::MmuError::BlockMapped
pub(crate) fn probe_user_pages<M: Mmu>(
    mmu: &M,
    task_as: &M::AddressSpace,
    user_ptr: usize,
    len: usize,
    require_write: bool,
) -> Result<(), SyscallError> {
    let end = user_ptr
        .checked_add(len)
        .ok_or(SyscallError::FaultAddress)?;
    let mut page = user_ptr & !PAGE_MASK;
    while page < end {
        let (_frame, flags) = mmu
            .translate(task_as, VirtAddr(page))
            .map_err(|_| SyscallError::FaultAddress)?;
        if !flags.contains(MappingFlags::USER) {
            return Err(SyscallError::FaultAddress);
        }
        if require_write && !flags.contains(MappingFlags::WRITE) {
            return Err(SyscallError::FaultAddress);
        }
        // Advance with `saturating_add`, not `checked_add`: a valid (non-
        // wrapping) range ending in the very last page of the address space
        // would otherwise overflow on this final increment and spuriously
        // fault. Saturating clamps `page` to `usize::MAX` (≥ `end`), so the
        // `page < end` guard terminates after the last page is probed. The
        // range's no-wrap property was already proven by the `end` `checked_add`
        // above; this is purely the cursor walk.
        page = page.saturating_add(PAGE_SIZE);
    }
    Ok(())
}

/// Copy `dst.len()` bytes **from** user memory at `user_ptr` into `dst`.
///
/// Validates `[user_ptr, user_ptr + dst.len())` against `window` (range gate),
/// then **two-pass**: pass 1 probes every spanned page (translate + `USER`);
/// only if all pass does pass 2 copy each page's sub-run through the high-half
/// direct map. A zero-length `dst` is a no-op that always succeeds. On any
/// failure (out-of-window, wrap, unmapped/block page, non-`USER` leaf) the user
/// pointer is **not** dereferenced and no byte is copied.
///
/// # Errors
///
/// [`SyscallError::FaultAddress`] if the range is out of the window, wraps, or
/// any spanned page fails to translate to a `USER` leaf.
pub fn copy_from_user<M: Mmu>(
    mmu: &M,
    task_as: &M::AddressSpace,
    window: &UserAccessWindow,
    user_ptr: usize,
    dst: &mut [u8],
) -> Result<(), SyscallError> {
    let len = dst.len();
    window.validate(user_ptr, len)?;
    if len == 0 {
        return Ok(());
    }
    // Pass 1 — probe every page (translate + USER) before any byte moves.
    probe_user_pages(mmu, task_as, user_ptr, len, /* require_write */ false)?;

    // Pass 2 — copy each page's sub-run. The AS is immutable across the
    // single-core, interrupts-masked syscall, so each page re-translates
    // identically to the probe; the per-page USER re-check is defence in depth.
    let end = user_ptr
        .checked_add(len)
        .ok_or(SyscallError::FaultAddress)?;
    let mut cur = user_ptr;
    while cur < end {
        let page_base = cur & !PAGE_MASK;
        let in_page = cur.wrapping_sub(page_base); // < PAGE_SIZE
        let page_remaining = PAGE_SIZE.wrapping_sub(in_page); // >= 1
        let run = core::cmp::min(page_remaining, end.wrapping_sub(cur)); // >= 1
        let (frame, flags) = mmu
            .translate(task_as, VirtAddr(page_base))
            .map_err(|_| SyscallError::FaultAddress)?;
        if !flags.contains(MappingFlags::USER) {
            return Err(SyscallError::FaultAddress);
        }
        let dst_off = cur.wrapping_sub(user_ptr);
        // SAFETY: copy `run` bytes from the user page into the kernel `dst`.
        //
        // **Why `unsafe`.** The source names *userspace* memory by an integer
        // VA; reconstructing a readable pointer to it cannot be expressed in
        // safe Rust. `Mmu::translate` resolved `page_base` to the physical
        // frame backing it; `phys_frame_kernel_ptr` rebases that frame to a
        // kernel-reachable pointer via the high-half direct map (ADR-0033), and
        // `.add(in_page)` offsets to the sub-run start.
        //
        // **Invariants.** (1) **Range** — `window.validate` proved `[user_ptr,
        // user_ptr+len)` is in-window and non-wrapping; `run = min(page-rem,
        // range-rem) >= 1` and `cur < end`, so `[cur, cur+run)` is in range and
        // `dst_off + run <= len` (the `dst` write stays in-bounds). (2)
        // **Ownership + permission** — the probe pass proved every spanned page
        // translates to a `USER` leaf; this pass re-checks `USER`, so the source
        // frame is genuinely the task's own user page (the confused-deputy
        // defence — a kernel page is rejected, never read). (3) **Disjointness**
        // — `dst` is a kernel buffer; the source is a userspace page; distinct
        // allocations / address regions, so `core::ptr::copy` (conservative
        // memmove) moves between non-overlapping memory. (4) **No interleaving**
        // — single-core cooperative, SVC handler runs with `DAIF` masked, so no
        // peer mutates the source or the mapping mid-copy. Audit:
        // UNSAFE-2026-0030 (per-page translation; supersedes the v1 identity map).
        unsafe {
            let kptr = phys_frame_kernel_ptr(frame).add(in_page);
            core::ptr::copy(kptr.cast_const(), dst.as_mut_ptr().add(dst_off), run);
        }
        cur = cur.checked_add(run).ok_or(SyscallError::FaultAddress)?;
    }
    Ok(())
}

/// Copy `src.len()` bytes **to** user memory at `user_ptr` from `src`.
///
/// The symmetric write-side primitive to [`copy_from_user`]: validates the
/// range against `window`, **two-pass** probes every spanned page requiring
/// [`MappingFlags::USER`] **and** [`MappingFlags::WRITE`], then writes each
/// page's sub-run. No v1 syscall returns data through a user pointer (`recv`
/// returns its message in registers), so this has no v1 caller yet — it is the
/// natural completion of the validated user-access primitive ([ADR-0030][adr-0030]
/// dependency-chain step 5 names "copy-from/to-user"); the first pointer-returning
/// syscall (Phase B6+) uses it without re-deriving the validation.
///
/// # Errors
///
/// [`SyscallError::FaultAddress`] if the range is out of the window, wraps, or
/// any spanned page fails to translate to a writable `USER` leaf.
///
/// [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
pub fn copy_to_user<M: Mmu>(
    mmu: &M,
    task_as: &M::AddressSpace,
    window: &UserAccessWindow,
    user_ptr: usize,
    src: &[u8],
) -> Result<(), SyscallError> {
    let len = src.len();
    window.validate(user_ptr, len)?;
    if len == 0 {
        return Ok(());
    }
    // Pass 1 — probe every page requiring USER + WRITE before any byte is
    // written, so a mid-range fault leaves the user buffer untouched
    // (all-or-nothing: a partial write to USER memory would be observable).
    probe_user_pages(mmu, task_as, user_ptr, len, /* require_write */ true)?;

    // Pass 2 — write each page's sub-run.
    let end = user_ptr
        .checked_add(len)
        .ok_or(SyscallError::FaultAddress)?;
    let mut cur = user_ptr;
    while cur < end {
        let page_base = cur & !PAGE_MASK;
        let in_page = cur.wrapping_sub(page_base);
        let page_remaining = PAGE_SIZE.wrapping_sub(in_page);
        let run = core::cmp::min(page_remaining, end.wrapping_sub(cur));
        let (frame, flags) = mmu
            .translate(task_as, VirtAddr(page_base))
            .map_err(|_| SyscallError::FaultAddress)?;
        if !flags.contains(MappingFlags::USER) || !flags.contains(MappingFlags::WRITE) {
            return Err(SyscallError::FaultAddress);
        }
        let src_off = cur.wrapping_sub(user_ptr);
        // SAFETY: writes `run` bytes from the kernel `src` to the user page.
        // The invariants from [`copy_from_user`] hold with the direction
        // reversed: range validity (`window.validate` + the `run`/`cur`
        // arithmetic), ownership+permission (the probe proved every page is a
        // writable `USER` leaf; re-checked here), disjointness (`src` is a
        // kernel buffer, the destination a userspace page — distinct regions),
        // and no single-core interleaving under the `DAIF`-masked SVC handler.
        // `core::ptr::copy` is the conservative memmove. Audit: UNSAFE-2026-0030.
        unsafe {
            let kptr = phys_frame_kernel_ptr(frame).add(in_page);
            core::ptr::copy(src.as_ptr().add(src_off), kptr, run);
        }
        cur = cur.checked_add(run).ok_or(SyscallError::FaultAddress)?;
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
    use tyrne_hal::{MappingFlags, Mmu, PhysAddr, PhysFrame, VirtAddr, PAGE_SIZE};
    use tyrne_test_hal::{BlockMappedMmu, FakeUserMem};

    // The translate-based copy resolves a user VA to a `PhysFrame`, rebases it
    // via `phys_frame_kernel_ptr` (identity on host) and reads / writes the
    // backing bytes — so a test page must be a real, page-aligned host
    // allocation. [`tyrne_test_hal::FakeUserMem`] provides exactly that: it
    // allocates page-aligned host pages, maps a synthetic user VA range onto
    // them in a `FakeMmu` AS with the given per-page flags, and exposes
    // provenance so the int-to-pointer rebase recovers it under Miri.

    /// The whole-region window for `mem` (the cheap range first-gate).
    fn whole_window(mem: &FakeUserMem) -> UserAccessWindow {
        UserAccessWindow::new(mem.base_va(), mem.region_len())
    }

    const UVA: usize = 0x40_0000; // a synthetic, page-aligned user base VA

    // ── in-range success ──────────────────────────────────────────────────────

    #[test]
    fn copy_from_user_translates_and_copies_a_user_page() {
        let mem = FakeUserMem::new(UVA, 1, MappingFlags::USER | MappingFlags::WRITE);
        let src: Vec<u8> = (0..16u8).collect();
        mem.write(0, &src);

        let mut dst = [0u8; 8];
        copy_from_user(
            mem.mmu(),
            mem.address_space(),
            &whole_window(&mem),
            UVA,
            &mut dst,
        )
        .expect("in-range user page copy must succeed");
        assert_eq!(dst, [0, 1, 2, 3, 4, 5, 6, 7]);

        // An interior, in-range sub-slice also succeeds.
        let mut dst2 = [0u8; 4];
        copy_from_user(
            mem.mmu(),
            mem.address_space(),
            &whole_window(&mem),
            UVA + 8,
            &mut dst2,
        )
        .expect("interior copy");
        assert_eq!(dst2, [8, 9, 10, 11]);
    }

    #[test]
    fn copy_to_user_in_range_moves_bytes() {
        let mem = FakeUserMem::new(UVA, 1, MappingFlags::USER | MappingFlags::WRITE);
        let payload = [0xAAu8, 0xBB, 0xCC, 0xDD];
        copy_to_user(
            mem.mmu(),
            mem.address_space(),
            &whole_window(&mem),
            UVA + 2,
            &payload,
        )
        .expect("in-range copy_to_user");
        assert_eq!(mem.read(2, 4), payload);
        // Bytes outside the written range are untouched.
        assert_eq!(mem.read(0, 1), [0]);
        assert_eq!(mem.read(6, 1), [0]);
    }

    #[test]
    fn copy_from_user_spanning_two_pages_copies_all() {
        // A range straddling the page boundary exercises the multi-page loop.
        let mem = FakeUserMem::new(UVA, 2, MappingFlags::USER | MappingFlags::WRITE);
        let pattern: Vec<u8> = (0..32u8).collect();
        mem.write(PAGE_SIZE - 16, &pattern); // 16 bytes in page 0, 16 in page 1
        let mut dst = [0u8; 32];
        copy_from_user(
            mem.mmu(),
            mem.address_space(),
            &whole_window(&mem),
            UVA + PAGE_SIZE - 16,
            &mut dst,
        )
        .expect("cross-page copy");
        assert_eq!(dst.to_vec(), pattern);
    }

    // ── confused-deputy + translate failures ──────────────────────────────────

    #[test]
    fn copy_from_user_rejects_in_window_non_user_page() {
        // The gate #1 regression: a page that is mapped + in-window but lacks the
        // USER bit (a kernel / guard page) must be rejected with FaultAddress —
        // the range bound alone would have let it through.
        let mem = FakeUserMem::new(UVA, 1, MappingFlags::WRITE); // NO USER bit
        mem.write(0, &[1, 2, 3, 4]);
        let mut dst = [0u8; 4];
        assert_eq!(
            copy_from_user(
                mem.mmu(),
                mem.address_space(),
                &whole_window(&mem),
                UVA,
                &mut dst
            ),
            Err(SyscallError::FaultAddress)
        );
        assert_eq!(dst, [0; 4], "no byte may be copied from a non-USER page");
    }

    #[test]
    fn copy_from_user_faults_on_unmapped_page() {
        // In-window VA but no mapping in the task AS → translate NotMapped →
        // FaultAddress. The window is widened past the single mapped page so the
        // range gate passes and the translate gate is the one that rejects.
        let mem = FakeUserMem::new(UVA, 1, MappingFlags::USER | MappingFlags::WRITE);
        let wide = UserAccessWindow::new(UVA, 2 * PAGE_SIZE); // page 1 is unmapped
        let mut dst = [0u8; 8];
        assert_eq!(
            copy_from_user(
                mem.mmu(),
                mem.address_space(),
                &wide,
                UVA + PAGE_SIZE,
                &mut dst
            ),
            Err(SyscallError::FaultAddress)
        );
    }

    #[test]
    fn copy_from_user_multipage_second_page_unmapped_copies_nothing() {
        // All-or-nothing: page 0 is a valid USER page, page 1 is unmapped. The
        // probe pass faults before page 0's bytes are copied into `dst`.
        let mem = FakeUserMem::new(UVA, 1, MappingFlags::USER | MappingFlags::WRITE);
        mem.write(PAGE_SIZE - 8, &[9; 8]);
        let wide = UserAccessWindow::new(UVA, 2 * PAGE_SIZE);
        let mut dst = [0u8; 16]; // 8 bytes from page 0, 8 from the unmapped page 1
        assert_eq!(
            copy_from_user(
                mem.mmu(),
                mem.address_space(),
                &wide,
                UVA + PAGE_SIZE - 8,
                &mut dst
            ),
            Err(SyscallError::FaultAddress)
        );
        assert_eq!(
            dst, [0; 16],
            "all-or-nothing: no prefix copied on a later fault"
        );
    }

    #[test]
    fn copy_to_user_rejects_read_only_user_page() {
        // copy_to_user requires WRITE: a USER-but-read-only page is rejected and
        // no byte is written.
        let mem = FakeUserMem::new(UVA, 1, MappingFlags::USER); // USER, no WRITE
        let payload = [1u8, 2, 3, 4];
        assert_eq!(
            copy_to_user(
                mem.mmu(),
                mem.address_space(),
                &whole_window(&mem),
                UVA,
                &payload
            ),
            Err(SyscallError::FaultAddress)
        );
        assert_eq!(
            mem.read(0, 4),
            [0; 4],
            "no byte written to a read-only page"
        );
    }

    #[test]
    fn copy_from_user_block_mapped_page_faults() {
        // A 2 MiB block-mapped leaf (e.g. the bootstrap kernel map) is not a
        // 4 KiB user page; `translate` returns `BlockMapped`, which the probe
        // maps to `FaultAddress` — the same reject as an unmapped page. Closes
        // the copy-path coverage of the probe's `BlockMapped` translate-error
        // arm (the `BlockMappedMmu` decorator injects it).
        let mmu = BlockMappedMmu::with_blocked([VirtAddr(UVA)]);
        // SAFETY: the inner FakeMmu stores `root` without dereferencing it.
        let as_ =
            unsafe { mmu.create_address_space(PhysFrame::from_aligned(PhysAddr(0x1000)).unwrap()) };
        let window = UserAccessWindow::new(UVA, PAGE_SIZE);
        let mut dst = [0u8; 8];
        assert_eq!(
            copy_from_user(&mmu, &as_, &window, UVA, &mut dst),
            Err(SyscallError::FaultAddress)
        );
        assert_eq!(dst, [0; 8], "no byte copied from a block-mapped leaf");
    }

    // ── range gate (window) ────────────────────────────────────────────────────

    #[test]
    fn copy_from_user_out_of_window_faults_before_translate() {
        let mem = FakeUserMem::new(UVA, 1, MappingFlags::USER | MappingFlags::WRITE);
        // Window covers a different region than the pointer we read.
        let window = UserAccessWindow::new(UVA + PAGE_SIZE, PAGE_SIZE);
        let mut dst = [0u8; 8];
        assert_eq!(
            copy_from_user(mem.mmu(), mem.address_space(), &window, UVA, &mut dst),
            Err(SyscallError::FaultAddress)
        );
    }

    #[test]
    fn copy_from_user_overrun_past_window_end_faults() {
        let mem = FakeUserMem::new(UVA, 1, MappingFlags::USER | MappingFlags::WRITE);
        let window = UserAccessWindow::new(UVA, 4); // shorter than the 8-byte read
        let mut dst = [0u8; 8];
        assert_eq!(
            copy_from_user(mem.mmu(), mem.address_space(), &window, UVA, &mut dst),
            Err(SyscallError::FaultAddress)
        );
    }

    #[test]
    fn zero_length_copy_is_ok_even_for_unmapped_pointer() {
        // A zero-length copy touches no bytes and short-circuits before any
        // window check or translate — proven with an empty window + a never-
        // translated AS + an arbitrary address.
        let mem = FakeUserMem::new(UVA, 1, MappingFlags::USER | MappingFlags::WRITE);
        let window = UserAccessWindow::empty();
        let mut dst: [u8; 0] = [];
        assert_eq!(
            copy_from_user(
                mem.mmu(),
                mem.address_space(),
                &window,
                0xDEAD_0000,
                &mut dst
            ),
            Ok(())
        );
        let src: [u8; 0] = [];
        assert_eq!(
            copy_to_user(mem.mmu(), mem.address_space(), &window, 0xDEAD_0000, &src),
            Ok(())
        );
    }

    #[test]
    fn wrapping_range_faults() {
        let window = UserAccessWindow::new(0, usize::MAX);
        assert_eq!(
            window.validate(usize::MAX - 2, 8),
            Err(SyscallError::FaultAddress)
        );
    }

    #[test]
    fn validate_exact_window_fit_is_ok() {
        // Pure range-gate check (no translation): exact fit (end == window_end)
        // is in bounds; one byte past faults.
        let window = UserAccessWindow::new(0x1000, 0x100);
        assert_eq!(window.validate(0x1000, 0x100), Ok(()));
        assert_eq!(window.validate(0x1080, 0x80), Ok(()));
        assert_eq!(
            window.validate(0x1000, 0x101),
            Err(SyscallError::FaultAddress)
        );
    }

    #[test]
    fn copy_from_user_range_ending_in_top_page_does_not_spuriously_fault() {
        // Regression (reviewer-found): a valid, non-wrapping range ending in the
        // very last page of the address space must not fault — the probe's
        // page-cursor advance saturates instead of overflowing.
        let top_page = usize::MAX & !(PAGE_SIZE - 1); // 0xFFFF_FFFF_FFFF_F000
        let mem = FakeUserMem::new(top_page, 1, MappingFlags::USER | MappingFlags::WRITE);
        mem.write(0, &[7, 8, 9, 10]);
        // Window [top_page, usize::MAX] — len = PAGE_SIZE - 1, non-wrapping (a
        // full PAGE_SIZE would itself wrap and be rejected by the range gate).
        let window = UserAccessWindow::new(top_page, PAGE_SIZE - 1);
        let mut dst = [0u8; 4];
        copy_from_user(mem.mmu(), mem.address_space(), &window, top_page, &mut dst)
            .expect("a valid range ending in the top page must not spuriously fault");
        assert_eq!(dst, [7, 8, 9, 10]);
    }
}
