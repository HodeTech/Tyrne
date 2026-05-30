//! Memory-management subsystem.
//!
//! Top-level parent for the kernel-side memory-management modules.
//! Hosts the Physical Memory Manager (PMM) per [ADR-0035] and the
//! kernel-side `AddressSpace<M>` object per [ADR-0028].
//!
//! See [T-017] for the PMM arc, [T-018] for the `AddressSpace` arc, and
//! [`docs/architecture/memory-management.md`] for the synthesised
//! architecture chapter.
//!
//! [ADR-0028]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0028-address-space-data-structure.md
//! [ADR-0035]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0035-physical-memory-manager.md
//! [T-017]: https://github.com/HodeTech/Tyrne/blob/main/docs/analysis/tasks/phase-b/T-017-physical-memory-manager.md
//! [T-018]: https://github.com/HodeTech/Tyrne/blob/main/docs/analysis/tasks/phase-b/T-018-address-space-kernel-object.md

pub mod address_space;
pub mod pmm;

use tyrne_hal::{PhysAddr, PAGE_SIZE};

/// A half-open physical-frame range: `[start, end)`.
///
/// Used by the Physical Memory Manager (PMM) to describe both the
/// total managed physical-RAM extent and the kernel-reserved regions
/// (kernel image / `.boot_pt` / boot stack) handed to [`Pmm::new`].
///
/// The range carries raw [`PhysAddr`] values rather than [`tyrne_hal::PhysFrame`]
/// so it can describe multi-page regions in one entry without
/// frame-by-frame enumeration. `Pmm::new` validates page-alignment of
/// the bounds before mutating any bitmap state per [ADR-0035 §Simulation
/// §Step 0][adr-0035].
///
/// `start <= end` is a soft invariant — `Pmm::new` treats an
/// inverted range as zero-length (no frames covered) rather than
/// panicking; the validation layer at the BSP is the canonical
/// source for "well-formed range".
///
/// [adr-0035]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0035-physical-memory-manager.md#simulation
/// [`Pmm::new`]: pmm::Pmm::new
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub struct PhysFrameRange {
    /// Inclusive start of the range. Must be [`PAGE_SIZE`]-aligned for
    /// `Pmm::new` to accept it.
    pub start: PhysAddr,
    /// Exclusive end of the range. Must be [`PAGE_SIZE`]-aligned for
    /// `Pmm::new` to accept it.
    pub end: PhysAddr,
}

impl PhysFrameRange {
    /// Construct a range from raw bounds.
    ///
    /// Performs **no** alignment or ordering validation: the soft
    /// `start <= end` invariant and page-alignment are the caller's
    /// responsibility (canonically [`Pmm::new`], which validates both
    /// before trusting [`frame_count`][Self::frame_count] /
    /// [`len_bytes`][Self::len_bytes]). [`frame_count`][Self::frame_count]
    /// and [`len_bytes`][Self::len_bytes] are only meaningful for
    /// page-aligned, non-inverted bounds — an inverted range reads as
    /// zero-length and an unaligned range yields a truncating frame
    /// count (C2-010).
    ///
    /// [`Pmm::new`]: pmm::Pmm::new
    #[must_use]
    pub const fn new(start: PhysAddr, end: PhysAddr) -> Self {
        Self { start, end }
    }

    /// Return `true` if both bounds are [`PAGE_SIZE`]-aligned.
    #[must_use]
    pub const fn is_aligned(self) -> bool {
        self.start.0.is_multiple_of(PAGE_SIZE) && self.end.0.is_multiple_of(PAGE_SIZE)
    }

    /// Return the half-open range's length in bytes (or 0 if `end <
    /// start`).
    #[must_use]
    pub const fn len_bytes(self) -> usize {
        // Saturating sub keeps `clippy::arithmetic_side_effects`
        // happy and treats inverted ranges as zero-length per the
        // soft-invariant note above.
        self.end.0.saturating_sub(self.start.0)
    }

    /// Return the number of [`PAGE_SIZE`]-frames the range covers.
    /// Assumes both bounds are page-aligned (caller's responsibility).
    #[must_use]
    pub const fn frame_count(self) -> usize {
        // `len_bytes()` is bounded by `usize::MAX`; integer division
        // by the non-zero `PAGE_SIZE` is total. No side effects to
        // trigger `arithmetic_side_effects`.
        self.len_bytes().wrapping_div(PAGE_SIZE)
    }

    /// Return `true` if `pa` falls in `[start, end)`.
    #[must_use]
    pub const fn contains(self, pa: PhysAddr) -> bool {
        pa.0 >= self.start.0 && pa.0 < self.end.0
    }
}

pub use address_space::{
    activate_address_space_handle, cap_create_address_space, cap_map, cap_unmap,
    create_address_space, get_address_space, AddressSpace, AddressSpaceArena, AddressSpaceError,
    AddressSpaceHandle, ADDRESS_SPACE_ARENA_CAPACITY, BOOTSTRAP_ADDRESS_SPACE_HANDLE,
};
pub use pmm::{Pmm, PmmError, PmmStats};

/// Return a kernel-writable raw pointer for `frame`'s base PA.
///
/// Since the high-half migration ([ADR-0033], T-022) the kernel runs in the
/// `TTBR1_EL1` high half and reaches physical memory through the high-half
/// direct map, so a frame's kernel VA is
/// [`tyrne_hal::phys_to_kernel_va(pa)`][phys_to_kernel_va] =
/// `KERNEL_HIGH_HALF_OFFSET + pa`. This helper *centralises* that translation:
/// every kernel-side caller that needs to read or write a PMM-allocated
/// frame's payload (e.g. [`crate::obj::task_loader::load_image`]'s
/// `copy_nonoverlapping` byte-copy site under [UNSAFE-2026-0027]) routes
/// through this one function. (Before T-022 the kernel was identity-mapped
/// and the body was the bare `pa as *mut u8`; ADR-0033 §Negative replaced it
/// with the direct-map rebase in this single place, leaving every call site
/// source-compatible.)
///
/// The function itself is safe (the `as *mut u8` cast is infallible
/// Rust); only the *dereference* at the call site is `unsafe` and
/// requires the audit-log entry that names the call site's specific
/// ownership / aliasing discipline.
///
/// The PMM's zero-fill site ([`kernel/src/mm/pmm.rs`](pmm.rs)) and the BSP's
/// page-table walk ([`bsp-qemu-virt/src/mmu.rs`]) perform the same
/// direct-map rebase at their own `unsafe` deref sites; their audit-log
/// entries ([UNSAFE-2026-0026], [UNSAFE-2026-0027]) gained ADR-0033
/// Amendments at the T-022 commit.
///
/// [ADR-0033]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0033-kernel-high-half-migration.md
/// [phys_to_kernel_va]: tyrne_hal::phys_to_kernel_va
/// [UNSAFE-2026-0026]: https://github.com/HodeTech/Tyrne/blob/main/docs/audits/unsafe-log.md
/// [UNSAFE-2026-0027]: https://github.com/HodeTech/Tyrne/blob/main/docs/audits/unsafe-log.md
#[must_use]
#[inline]
pub(crate) fn phys_frame_kernel_ptr(frame: tyrne_hal::PhysFrame) -> *mut u8 {
    // Direct-map rebase: kernel VA = KERNEL_HIGH_HALF_OFFSET + pa (ADR-0033).
    // The helper is infallible (`wrapping_add` + cast); only the *dereference*
    // at the call site is `unsafe` and carries the audit-log entry.
    tyrne_hal::phys_to_kernel_va(frame.as_usize()) as *mut u8
}
