//! Deterministic fake [`tyrne_hal::Mmu`] for host-side tests.

use std::collections::HashMap;
use std::sync::Mutex;
use tyrne_hal::{
    FrameProvider, MapperFlush, MappingFlags, Mmu, MmuError, PhysFrame, VirtAddr, PAGE_SIZE,
};

/// A simple [`FrameProvider`] backed by a `Vec` of pre-allocated frames.
///
/// Pops from the end, so the order in which frames are consumed is the
/// reverse of insertion order. Tests can query [`Self::remaining`] to
/// check how many frames were used.
///
/// # Contract note — frames are NOT zero-filled
///
/// The [`FrameProvider::alloc_frame`] contract requires zero-initialised
/// frames (the real [`Pmm`][pmm] zero-fills before returning, and the BSP
/// page-table walker *reads* the resulting zeroed descriptor slots).
/// `VecFrameProvider` does **not** zero-fill: a [`PhysFrame`] in the fake
/// is a typed *address*, not a region of backing bytes, so there is
/// nothing to zero. This satisfies the contract only **vacuously** —
/// [`FakeMmu`] (and the [`OutOfFramesMmu`] / [`BlockMappedMmu`]
/// decorators) never dereference a frame's physical memory.
///
/// If a future fake is added that *reads* frame contents (e.g. one that
/// walks a simulated page-table tree), the caller is responsible for
/// ensuring the inserted frames point at genuinely zero-initialised
/// backing memory; pairing such a fake with `VecFrameProvider` as-is
/// would feed it non-zero descriptor bytes.
///
/// [pmm]: https://github.com/cemililik/Tyrne/blob/main/kernel/src/mm/pmm.rs
pub struct VecFrameProvider {
    available: Vec<PhysFrame>,
}

impl VecFrameProvider {
    /// Construct a `VecFrameProvider` from the given frames.
    #[must_use]
    pub fn new(frames: Vec<PhysFrame>) -> Self {
        Self { available: frames }
    }

    /// Return the number of frames remaining.
    #[must_use]
    pub fn remaining(&self) -> usize {
        self.available.len()
    }
}

impl FrameProvider for VecFrameProvider {
    fn alloc_frame(&mut self) -> Option<PhysFrame> {
        self.available.pop()
    }
}

/// Address-space representation used by [`FakeMmu`].
///
/// Stores mappings as a `HashMap` keyed by virtual address. The fake has
/// no intermediate page tables; its purpose is to validate the behaviour
/// of kernel code against the [`Mmu`] contract, not to model `VMSAv8`.
pub struct FakeAddressSpace {
    root: PhysFrame,
    mappings: HashMap<VirtAddr, (PhysFrame, MappingFlags)>,
}

impl FakeAddressSpace {
    /// Return the number of live mappings in this address space.
    #[must_use]
    pub fn mapping_count(&self) -> usize {
        self.mappings.len()
    }

    /// Look up the mapping for a virtual address, if any.
    #[must_use]
    pub fn lookup(&self, va: VirtAddr) -> Option<(PhysFrame, MappingFlags)> {
        self.mappings.get(&va).copied()
    }
}

/// A [`Mmu`] that records activations, TLB invalidations, and mapping
/// operations for test assertions.
///
/// # Intrinsic fidelity gap
///
/// `FakeMmu` models mappings as a **flat `HashMap`** keyed by virtual
/// address; it has no multi-level page-table structure. Two `MmuError`
/// variants the real [`QemuVirtMmu`][bsp] can return are therefore
/// **never** produced by `FakeMmu`:
///
/// - [`MmuError::OutOfFrames`] — raised by the real walker when an
///   intermediate-table allocation fails mid-walk. `FakeMmu::map`
///   ignores its `FrameProvider` (no intermediate tables to allocate),
///   so it cannot exhaust it. Use [`OutOfFramesMmu`] to exercise the
///   kernel's mid-walk `OutOfFrames` rollback path (`load_image` /
///   `cap_map` failure-semantics clause (2): `pa` is not consumed).
/// - [`MmuError::BlockMapped`] — raised by the real walker when a walk
///   hits a 2 MiB block descriptor at L1/L2 (e.g. the bootstrap block
///   mappings). `FakeMmu` has no block descriptors. Use
///   [`BlockMappedMmu`] to exercise kernel code that distinguishes
///   `BlockMapped` from `NotMapped`.
///
/// Everything `FakeMmu` *does* model is bit-for-bit faithful to the real
/// impl (VA-alignment rejection, `DEVICE | EXECUTE` rejection, double-map
/// → `AlreadyMapped`, unmap-missing → `NotMapped`, the `MapperFlush`
/// token discipline). The injecting decorators above wrap a `FakeMmu` and
/// add exactly one failure mode each, delegating the success path
/// unchanged.
///
/// [bsp]: https://github.com/cemililik/Tyrne/blob/main/bsp-qemu-virt/src/mmu.rs
pub struct FakeMmu {
    state: Mutex<FakeMmuState>,
}

struct FakeMmuState {
    activated_root: Option<PhysFrame>,
    tlb_address_invalidations: Vec<VirtAddr>,
    tlb_all_count: u64,
}

impl FakeMmu {
    /// Construct a new `FakeMmu` with no address space activated.
    #[must_use]
    pub fn new() -> Self {
        Self {
            state: Mutex::new(FakeMmuState {
                activated_root: None,
                tlb_address_invalidations: Vec::new(),
                tlb_all_count: 0,
            }),
        }
    }

    /// Return the root frame of the currently activated address space, if
    /// any.
    ///
    /// # Panics
    ///
    /// Panics if the internal mutex has been poisoned.
    #[must_use]
    pub fn activated_root(&self) -> Option<PhysFrame> {
        self.locked().activated_root
    }

    /// Return a copy of the list of per-address TLB invalidations seen so
    /// far, in the order they were issued.
    ///
    /// # Panics
    ///
    /// Panics if the internal mutex has been poisoned.
    #[must_use]
    pub fn tlb_address_invalidations(&self) -> Vec<VirtAddr> {
        self.locked().tlb_address_invalidations.clone()
    }

    /// Return the number of full-TLB invalidations issued.
    ///
    /// # Panics
    ///
    /// Panics if the internal mutex has been poisoned.
    #[must_use]
    pub fn tlb_all_count(&self) -> u64 {
        self.locked().tlb_all_count
    }

    fn locked(&self) -> std::sync::MutexGuard<'_, FakeMmuState> {
        self.state.lock().expect("FakeMmu mutex poisoned")
    }
}

impl Default for FakeMmu {
    fn default() -> Self {
        Self::new()
    }
}

impl Mmu for FakeMmu {
    type AddressSpace = FakeAddressSpace;

    /// # Safety
    ///
    /// Inherits the [`Mmu::create_address_space`] trait-declaration
    /// contract (`root` page-aligned, exclusively owned, zero-filled).
    /// `FakeMmu` upholds it *vacuously*: the body never dereferences
    /// `root`'s physical memory — it stores the `PhysFrame` value (an
    /// aligned address) into a host-side `HashMap`-backed
    /// [`FakeAddressSpace`]. The zero-fill and exclusive-ownership
    /// pre-conditions therefore cannot be observed; alignment is enforced
    /// upstream by [`PhysFrame::from_aligned`].
    unsafe fn create_address_space(&self, root: PhysFrame) -> FakeAddressSpace {
        // SAFETY: no unsafe operation in this body — `root` is stored, not
        // dereferenced. Per unsafe-policy §4, this alloc-free trait-impl
        // `unsafe fn` inherits the trait declaration's `# Safety` contract;
        // it is a host-only test double and warrants no audit-log entry
        // (test-harness `unsafe` is exempt from individual log entries when
        // confined to test doubles — see unsafe-policy §3 / X3-003).
        FakeAddressSpace {
            root,
            mappings: HashMap::new(),
        }
    }

    fn address_space_root(&self, as_: &Self::AddressSpace) -> PhysFrame {
        as_.root
    }

    fn activate(&self, as_: &Self::AddressSpace) {
        self.locked().activated_root = Some(as_.root);
    }

    fn map(
        &self,
        as_: &mut FakeAddressSpace,
        va: VirtAddr,
        pa: PhysFrame,
        flags: MappingFlags,
        // `frames` is accepted for trait-signature compatibility but not
        // consumed: `FakeMmu` uses a flat `HashMap` and has no
        // intermediate page-table structure to allocate, so it never
        // returns `MmuError::OutOfFrames` regardless of how many frames
        // are available. See the `FakeMmu` struct-doc fidelity gap and
        // `OutOfFramesMmu` for the decorator that exercises that path.
        _frames: &mut dyn FrameProvider,
    ) -> Result<MapperFlush, MmuError> {
        // Mirror the real `Mmu` contract: VA must be `PAGE_SIZE`-aligned.
        // Without this check, kernel-side code that passes unaligned VAs
        // would silently succeed under host tests and fail on real hardware.
        // (PR #23 review-round 2026-05-09 Finding 7.)
        if !va.0.is_multiple_of(PAGE_SIZE) {
            return Err(MmuError::MisalignedAddress);
        }
        // Mirror `QemuVirtMmu::map`'s rejection of unrepresentable flag
        // combinations (DEVICE + EXECUTE — MMIO is never executable per
        // ADR-0027 §Decision outcome (b)). Keeps the FakeMmu's contract
        // identical to the real impl so kernel logic exercised on the
        // host catches the same misuse it would catch on hardware.
        // (PR #23 review-round 2026-05-09 Finding 3 / 7.)
        if flags.contains(MappingFlags::DEVICE) && flags.contains(MappingFlags::EXECUTE) {
            return Err(MmuError::InvalidFlags);
        }
        if as_.mappings.contains_key(&va) {
            return Err(MmuError::AlreadyMapped);
        }
        as_.mappings.insert(va, (pa, flags));
        Ok(MapperFlush::new(va))
    }

    fn unmap(
        &self,
        as_: &mut FakeAddressSpace,
        va: VirtAddr,
    ) -> Result<(MapperFlush, PhysFrame), MmuError> {
        // Mirror the real `Mmu` contract: VA must be `PAGE_SIZE`-aligned.
        // (PR #23 review-round 2026-05-09 Finding 7.)
        if !va.0.is_multiple_of(PAGE_SIZE) {
            return Err(MmuError::MisalignedAddress);
        }
        as_.mappings
            .remove(&va)
            .map(|(pa, _)| (MapperFlush::new(va), pa))
            .ok_or(MmuError::NotMapped)
    }

    fn invalidate_tlb_address(&self, va: VirtAddr) {
        self.locked().tlb_address_invalidations.push(va);
    }

    fn invalidate_tlb_all(&self) {
        self.locked().tlb_all_count += 1;
    }
}

// ── Failure-injecting decorator MMUs ──────────────────────────────────────────
//
// `FakeMmu`'s flat-HashMap design cannot reproduce two `MmuError` variants the
// real `QemuVirtMmu` returns: `OutOfFrames` (mid-walk intermediate-table
// allocation failure) and `BlockMapped` (walk hits a 2 MiB block descriptor).
// Kernel rollback logic (`load_image`, `cap_map`, `cap_unmap`) rides those
// clauses, so the two decorators below let host tests drive both failure paths.
// Each wraps a `FakeMmu`, reuses `FakeAddressSpace`, and delegates the success
// path verbatim — adding exactly one injected failure mode.

/// A [`Mmu`] decorator over [`FakeMmu`] that returns
/// [`MmuError::OutOfFrames`] from [`Mmu::map`] once its
/// [`FrameProvider`] is exhausted, modelling the real walker's mid-walk
/// intermediate-table allocation failure.
///
/// Each successful `map` call consumes **one** frame from the provider
/// passed to `map` (standing in for one intermediate page-table frame).
/// When the provider returns `None`, `map` returns `OutOfFrames`
/// **before** touching the address space, honouring the [`Mmu::map`]
/// failure-semantics contract: no mapping at `va`, and `pa` is **not**
/// consumed (the caller may safely return it to its provider). All other
/// methods delegate to the inner [`FakeMmu`] unchanged.
///
/// # Example
///
/// ```
/// use tyrne_test_hal::{OutOfFramesMmu, VecFrameProvider};
/// use tyrne_hal::{MappingFlags, Mmu, MmuError, PhysAddr, PhysFrame, VirtAddr};
///
/// let frame = |a| PhysFrame::from_aligned(PhysAddr(a)).unwrap();
/// let mmu = OutOfFramesMmu::new();
/// // SAFETY: the inner FakeMmu never dereferences `root`.
/// let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
///
/// // A provider with zero frames → the first map fails with OutOfFrames.
/// let mut empty = VecFrameProvider::new(vec![]);
/// let err = mmu
///     .map(&mut as_, VirtAddr(0x4000), frame(0x8000), MappingFlags::WRITE, &mut empty)
///     .unwrap_err();
/// assert_eq!(err, MmuError::OutOfFrames);
/// // pa was not consumed and no mapping was installed.
/// assert_eq!(as_.mapping_count(), 0);
/// ```
pub struct OutOfFramesMmu {
    inner: FakeMmu,
}

impl OutOfFramesMmu {
    /// Construct an `OutOfFramesMmu` wrapping a fresh [`FakeMmu`].
    #[must_use]
    pub fn new() -> Self {
        Self {
            inner: FakeMmu::new(),
        }
    }

    /// Borrow the inner [`FakeMmu`] for activation / TLB introspection
    /// (e.g. [`FakeMmu::activated_root`],
    /// [`FakeMmu::tlb_address_invalidations`]).
    #[must_use]
    pub fn inner(&self) -> &FakeMmu {
        &self.inner
    }
}

impl Default for OutOfFramesMmu {
    fn default() -> Self {
        Self::new()
    }
}

impl Mmu for OutOfFramesMmu {
    type AddressSpace = FakeAddressSpace;

    /// # Safety
    ///
    /// Inherits [`Mmu::create_address_space`]; delegates to the inner
    /// [`FakeMmu`], which never dereferences `root`.
    unsafe fn create_address_space(&self, root: PhysFrame) -> FakeAddressSpace {
        // SAFETY: forwards to FakeMmu::create_address_space, an alloc-free
        // store of an aligned `PhysFrame`. See FakeMmu's `# Safety`.
        unsafe { self.inner.create_address_space(root) }
    }

    fn address_space_root(&self, as_: &Self::AddressSpace) -> PhysFrame {
        self.inner.address_space_root(as_)
    }

    fn activate(&self, as_: &Self::AddressSpace) {
        self.inner.activate(as_);
    }

    fn map(
        &self,
        as_: &mut FakeAddressSpace,
        va: VirtAddr,
        pa: PhysFrame,
        flags: MappingFlags,
        frames: &mut dyn FrameProvider,
    ) -> Result<MapperFlush, MmuError> {
        // Pull one frame to model an intermediate-table allocation. If the
        // provider is empty, fail with OutOfFrames BEFORE mutating `as_`
        // and WITHOUT consuming `pa` — exactly the real walker's contract.
        if frames.alloc_frame().is_none() {
            return Err(MmuError::OutOfFrames);
        }
        // Frame consumed; delegate the success path to the inner FakeMmu,
        // which performs the alignment / flag / double-map checks and the
        // actual insert. It ignores its own `frames` argument.
        self.inner.map(as_, va, pa, flags, frames)
    }

    fn unmap(
        &self,
        as_: &mut FakeAddressSpace,
        va: VirtAddr,
    ) -> Result<(MapperFlush, PhysFrame), MmuError> {
        self.inner.unmap(as_, va)
    }

    fn invalidate_tlb_address(&self, va: VirtAddr) {
        self.inner.invalidate_tlb_address(va);
    }

    fn invalidate_tlb_all(&self) {
        self.inner.invalidate_tlb_all();
    }
}

/// A [`Mmu`] decorator over [`FakeMmu`] that injects
/// [`MmuError::BlockMapped`] for a configured set of virtual addresses,
/// modelling the real walker hitting a 2 MiB block descriptor at L1/L2.
///
/// A VA registered via [`Self::block`] (or [`Self::with_blocked`]) makes
/// both [`Mmu::map`] and [`Mmu::unmap`] return `BlockMapped` for that VA
/// (checked **before** any address-space mutation, so the failure
/// semantics — no state change, `pa` not consumed — hold). Any VA not in
/// the blocked set delegates to the inner [`FakeMmu`] unchanged, so the
/// success path and the `NotMapped` / `AlreadyMapped` / alignment
/// behaviours stay faithful.
///
/// # Example
///
/// ```
/// use tyrne_test_hal::BlockMappedMmu;
/// use tyrne_hal::{MappingFlags, Mmu, MmuError, PhysAddr, PhysFrame, VirtAddr};
///
/// let frame = |a| PhysFrame::from_aligned(PhysAddr(a)).unwrap();
/// let mmu = BlockMappedMmu::with_blocked([VirtAddr(0x4000)]);
/// // SAFETY: the inner FakeMmu never dereferences `root`.
/// let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
///
/// // unmap of a blocked VA surfaces BlockMapped, distinct from NotMapped.
/// let err = mmu.unmap(&mut as_, VirtAddr(0x4000)).unwrap_err();
/// assert_eq!(err, MmuError::BlockMapped);
/// // A non-blocked VA falls through to the inner FakeMmu (NotMapped here).
/// let err = mmu.unmap(&mut as_, VirtAddr(0x5000)).unwrap_err();
/// assert_eq!(err, MmuError::NotMapped);
/// ```
pub struct BlockMappedMmu {
    inner: FakeMmu,
    blocked: std::collections::HashSet<VirtAddr>,
}

impl BlockMappedMmu {
    /// Construct a `BlockMappedMmu` with no blocked addresses (delegates
    /// everything to the inner [`FakeMmu`] until [`Self::block`] is
    /// called).
    #[must_use]
    pub fn new() -> Self {
        Self {
            inner: FakeMmu::new(),
            blocked: std::collections::HashSet::new(),
        }
    }

    /// Construct a `BlockMappedMmu` pre-loaded with the given blocked
    /// virtual addresses.
    #[must_use]
    pub fn with_blocked(addrs: impl IntoIterator<Item = VirtAddr>) -> Self {
        Self {
            inner: FakeMmu::new(),
            blocked: addrs.into_iter().collect(),
        }
    }

    /// Register `va` so that subsequent `map` / `unmap` on it return
    /// [`MmuError::BlockMapped`].
    pub fn block(&mut self, va: VirtAddr) {
        self.blocked.insert(va);
    }

    /// Borrow the inner [`FakeMmu`] for activation / TLB introspection.
    #[must_use]
    pub fn inner(&self) -> &FakeMmu {
        &self.inner
    }

    fn is_blocked(&self, va: VirtAddr) -> bool {
        self.blocked.contains(&va)
    }
}

impl Default for BlockMappedMmu {
    fn default() -> Self {
        Self::new()
    }
}

impl Mmu for BlockMappedMmu {
    type AddressSpace = FakeAddressSpace;

    /// # Safety
    ///
    /// Inherits [`Mmu::create_address_space`]; delegates to the inner
    /// [`FakeMmu`], which never dereferences `root`.
    unsafe fn create_address_space(&self, root: PhysFrame) -> FakeAddressSpace {
        // SAFETY: forwards to FakeMmu::create_address_space, an alloc-free
        // store of an aligned `PhysFrame`. See FakeMmu's `# Safety`.
        unsafe { self.inner.create_address_space(root) }
    }

    fn address_space_root(&self, as_: &Self::AddressSpace) -> PhysFrame {
        self.inner.address_space_root(as_)
    }

    fn activate(&self, as_: &Self::AddressSpace) {
        self.inner.activate(as_);
    }

    fn map(
        &self,
        as_: &mut FakeAddressSpace,
        va: VirtAddr,
        pa: PhysFrame,
        flags: MappingFlags,
        frames: &mut dyn FrameProvider,
    ) -> Result<MapperFlush, MmuError> {
        // Inject BlockMapped before any state change: no mapping at `va`,
        // `pa` not consumed — honours the Mmu::map failure contract.
        if self.is_blocked(va) {
            return Err(MmuError::BlockMapped);
        }
        self.inner.map(as_, va, pa, flags, frames)
    }

    fn unmap(
        &self,
        as_: &mut FakeAddressSpace,
        va: VirtAddr,
    ) -> Result<(MapperFlush, PhysFrame), MmuError> {
        if self.is_blocked(va) {
            return Err(MmuError::BlockMapped);
        }
        self.inner.unmap(as_, va)
    }

    fn invalidate_tlb_address(&self, va: VirtAddr) {
        self.inner.invalidate_tlb_address(va);
    }

    fn invalidate_tlb_all(&self) {
        self.inner.invalidate_tlb_all();
    }
}

#[cfg(test)]
mod tests {
    use super::{BlockMappedMmu, FakeMmu, OutOfFramesMmu, VecFrameProvider};
    use tyrne_hal::{MapperFlush, MappingFlags, Mmu, MmuError, PhysAddr, PhysFrame, VirtAddr};

    fn frame(addr: usize) -> PhysFrame {
        PhysFrame::from_aligned(PhysAddr(addr)).expect("test addr must be page-aligned")
    }

    #[test]
    fn mapping_flags_union_and_contains() {
        let rw = MappingFlags::WRITE;
        let rwx = rw | MappingFlags::EXECUTE;
        assert!(rwx.contains(MappingFlags::WRITE));
        assert!(rwx.contains(MappingFlags::EXECUTE));
        assert!(!rwx.contains(MappingFlags::USER));
    }

    #[test]
    fn mapping_flags_difference_clears_bits() {
        let rwx = MappingFlags::WRITE | MappingFlags::EXECUTE;
        let rw = rwx.difference(MappingFlags::EXECUTE);
        assert!(rw.contains(MappingFlags::WRITE));
        assert!(!rw.contains(MappingFlags::EXECUTE));
    }

    #[test]
    fn phys_frame_rejects_unaligned() {
        assert!(PhysFrame::from_aligned(PhysAddr(0x1001)).is_none());
        assert!(PhysFrame::from_aligned(PhysAddr(0x1000)).is_some());
    }

    #[test]
    fn create_address_space_stores_root() {
        let mmu = FakeMmu::new();
        let root = frame(0x1000);
        // SAFETY: FakeMmu::create_address_space does not dereference `root`;
        // it only stores the PhysFrame value. Alignment is upheld because
        // `frame()` (and PhysFrame::from_aligned) reject unaligned addresses.
        let as_ = unsafe { mmu.create_address_space(root) };
        assert_eq!(mmu.address_space_root(&as_), root);
        assert_eq!(as_.mapping_count(), 0);
    }

    #[test]
    fn activate_records_root() {
        let mmu = FakeMmu::new();
        let root = frame(0x1000);
        // SAFETY: FakeMmu::create_address_space does not dereference `root`;
        // it only stores the PhysFrame value. Alignment is upheld because
        // `frame()` (and PhysFrame::from_aligned) reject unaligned addresses.
        let as_ = unsafe { mmu.create_address_space(root) };
        assert!(mmu.activated_root().is_none());
        mmu.activate(&as_);
        assert_eq!(mmu.activated_root(), Some(root));
    }

    #[test]
    fn map_unmap_round_trip() {
        let mmu = FakeMmu::new();
        // SAFETY: FakeMmu::create_address_space does not dereference its
        // argument; `frame(0x1000)` is page-aligned by construction.
        let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
        let mut fp = VecFrameProvider::new(vec![frame(0x2000)]);

        let flush = mmu
            .map(
                &mut as_,
                VirtAddr(0x4000),
                frame(0x8000),
                MappingFlags::WRITE,
                &mut fp,
            )
            .expect("first map must succeed");
        flush.flush(&mmu);
        assert_eq!(as_.mapping_count(), 1);

        let (pa, flags) = as_
            .lookup(VirtAddr(0x4000))
            .expect("lookup must find mapping");
        assert_eq!(pa, frame(0x8000));
        assert!(flags.contains(MappingFlags::WRITE));

        let (unmap_flush, returned) = mmu
            .unmap(&mut as_, VirtAddr(0x4000))
            .expect("unmap must succeed");
        unmap_flush.flush(&mmu);
        assert_eq!(returned, frame(0x8000));
        assert_eq!(as_.mapping_count(), 0);
    }

    #[test]
    fn double_map_returns_already_mapped() {
        let mmu = FakeMmu::new();
        // SAFETY: FakeMmu::create_address_space does not dereference its
        // argument; `frame(0x1000)` is page-aligned by construction.
        let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
        let mut fp = VecFrameProvider::new(vec![]);

        mmu.map(
            &mut as_,
            VirtAddr(0x4000),
            frame(0x8000),
            MappingFlags::WRITE,
            &mut fp,
        )
        .expect("first map must succeed")
        .flush(&mmu);

        let err = mmu
            .map(
                &mut as_,
                VirtAddr(0x4000),
                frame(0x9000),
                MappingFlags::WRITE,
                &mut fp,
            )
            .expect_err("second map must fail");
        assert_eq!(err, MmuError::AlreadyMapped);
    }

    #[test]
    fn unmap_missing_returns_not_mapped() {
        let mmu = FakeMmu::new();
        // SAFETY: FakeMmu::create_address_space does not dereference its
        // argument; `frame(0x1000)` is page-aligned by construction.
        let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
        let err = mmu
            .unmap(&mut as_, VirtAddr(0x4000))
            .expect_err("unmap of unmapped va must fail");
        assert_eq!(err, MmuError::NotMapped);
    }

    #[test]
    fn tlb_invalidations_recorded_in_order() {
        let mmu = FakeMmu::new();
        mmu.invalidate_tlb_address(VirtAddr(0x4000));
        mmu.invalidate_tlb_address(VirtAddr(0x5000));
        mmu.invalidate_tlb_all();
        assert_eq!(
            mmu.tlb_address_invalidations(),
            vec![VirtAddr(0x4000), VirtAddr(0x5000)]
        );
        assert_eq!(mmu.tlb_all_count(), 1);
    }

    // ── MapperFlush token semantics ───────────────────────────────────────────

    #[test]
    fn mapper_flush_carries_virt_addr() {
        let token = MapperFlush::new(VirtAddr(0x4000));
        assert_eq!(token.virt_addr(), VirtAddr(0x4000));
    }

    #[test]
    fn mapper_flush_flush_invokes_invalidate_tlb_address() {
        let mmu = FakeMmu::new();
        let token = MapperFlush::new(VirtAddr(0x12_3000));
        token.flush(&mmu);
        assert_eq!(
            mmu.tlb_address_invalidations(),
            vec![VirtAddr(0x12_3000)],
            "flush() must invoke invalidate_tlb_address for the held VA"
        );
        assert_eq!(
            mmu.tlb_all_count(),
            0,
            "flush() must not invoke invalidate_tlb_all"
        );
    }

    #[test]
    fn mapper_flush_ignore_is_documented_noop() {
        let mmu = FakeMmu::new();
        let token = MapperFlush::new(VirtAddr(0x4000));
        token.ignore();
        assert!(
            mmu.tlb_address_invalidations().is_empty(),
            "ignore() must not invoke invalidate_tlb_address"
        );
        assert_eq!(
            mmu.tlb_all_count(),
            0,
            "ignore() must not invoke invalidate_tlb_all"
        );
    }

    #[test]
    fn map_returns_token_with_mapped_va() {
        let mmu = FakeMmu::new();
        // SAFETY: FakeMmu::create_address_space does not dereference its
        // argument; `frame(0x1000)` is page-aligned by construction.
        let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
        let mut fp = VecFrameProvider::new(vec![]);

        let flush = mmu
            .map(
                &mut as_,
                VirtAddr(0x4_0000),
                frame(0x8000),
                MappingFlags::WRITE,
                &mut fp,
            )
            .expect("map must succeed");
        assert_eq!(
            flush.virt_addr(),
            VirtAddr(0x4_0000),
            "map's MapperFlush must carry the VA passed to map"
        );
        flush.flush(&mmu);
        assert_eq!(mmu.tlb_address_invalidations(), vec![VirtAddr(0x4_0000)]);
    }

    #[test]
    fn unmap_returns_token_with_unmapped_va_and_frame() {
        let mmu = FakeMmu::new();
        // SAFETY: FakeMmu::create_address_space does not dereference its
        // argument; `frame(0x1000)` is page-aligned by construction.
        let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
        let mut fp = VecFrameProvider::new(vec![]);

        mmu.map(
            &mut as_,
            VirtAddr(0x5_0000),
            frame(0x9000),
            MappingFlags::WRITE,
            &mut fp,
        )
        .expect("map must succeed")
        .ignore();

        let (flush, returned) = mmu
            .unmap(&mut as_, VirtAddr(0x5_0000))
            .expect("unmap must succeed");
        assert_eq!(returned, frame(0x9000), "unmap must return the mapped PA");
        assert_eq!(
            flush.virt_addr(),
            VirtAddr(0x5_0000),
            "unmap's MapperFlush must carry the VA passed to unmap"
        );
        flush.flush(&mmu);
        assert_eq!(mmu.tlb_address_invalidations(), vec![VirtAddr(0x5_0000)]);
    }

    #[test]
    fn bulk_map_with_ignore_then_invalidate_tlb_all() {
        let mmu = FakeMmu::new();
        // SAFETY: page-aligned by construction.
        let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
        let mut fp = VecFrameProvider::new(vec![]);

        for (i, &va) in [
            VirtAddr(0x10_0000),
            VirtAddr(0x11_0000),
            VirtAddr(0x12_0000),
        ]
        .iter()
        .enumerate()
        {
            mmu.map(
                &mut as_,
                va,
                frame(0x100_0000 + i * 0x1000),
                MappingFlags::WRITE,
                &mut fp,
            )
            .expect("map must succeed")
            .ignore();
        }
        mmu.invalidate_tlb_all();

        assert!(
            mmu.tlb_address_invalidations().is_empty(),
            "bulk-with-ignore must not issue per-address invalidates"
        );
        assert_eq!(mmu.tlb_all_count(), 1);
    }

    // ── Contract parity with real Mmu (PR #23 review-round 2026-05-09) ────────

    #[test]
    fn map_rejects_unaligned_va() {
        let mmu = FakeMmu::new();
        // SAFETY: page-aligned by construction.
        let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
        let mut fp = VecFrameProvider::new(vec![]);

        let err = mmu
            .map(
                &mut as_,
                VirtAddr(0x4001), // off by one byte
                frame(0x8000),
                MappingFlags::WRITE,
                &mut fp,
            )
            .expect_err("unaligned VA must fail");
        assert_eq!(err, MmuError::MisalignedAddress);
        assert_eq!(
            as_.mapping_count(),
            0,
            "rejected map must not insert a mapping"
        );
    }

    #[test]
    fn unmap_rejects_unaligned_va() {
        let mmu = FakeMmu::new();
        // SAFETY: page-aligned by construction.
        let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };

        let err = mmu
            .unmap(&mut as_, VirtAddr(0x4_0123))
            .expect_err("unaligned VA must fail");
        assert_eq!(err, MmuError::MisalignedAddress);
    }

    #[test]
    fn map_rejects_device_plus_execute() {
        let mmu = FakeMmu::new();
        // SAFETY: page-aligned by construction.
        let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
        let mut fp = VecFrameProvider::new(vec![]);

        let err = mmu
            .map(
                &mut as_,
                VirtAddr(0x0900_0000),
                frame(0x0900_0000),
                MappingFlags::DEVICE | MappingFlags::EXECUTE,
                &mut fp,
            )
            .expect_err("DEVICE + EXECUTE must be rejected");
        assert_eq!(err, MmuError::InvalidFlags);
        assert_eq!(as_.mapping_count(), 0);
    }

    // ── Failure-injecting decorators ──────────────────────────────────────────

    #[test]
    fn out_of_frames_mmu_maps_while_frames_available() {
        let mmu = OutOfFramesMmu::new();
        // SAFETY: the inner FakeMmu never dereferences `root`.
        let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
        let mut fp = VecFrameProvider::new(vec![frame(0x2000)]);

        mmu.map(
            &mut as_,
            VirtAddr(0x4000),
            frame(0x8000),
            MappingFlags::WRITE,
            &mut fp,
        )
        .expect("map must succeed while a frame is available")
        .flush(mmu.inner());
        assert_eq!(as_.mapping_count(), 1);
        assert_eq!(fp.remaining(), 0, "one frame must have been consumed");
    }

    #[test]
    fn out_of_frames_mmu_returns_out_of_frames_when_provider_empty() {
        let mmu = OutOfFramesMmu::new();
        // SAFETY: the inner FakeMmu never dereferences `root`.
        let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
        let mut fp = VecFrameProvider::new(vec![]);

        let err = mmu
            .map(
                &mut as_,
                VirtAddr(0x4000),
                frame(0x8000),
                MappingFlags::WRITE,
                &mut fp,
            )
            .expect_err("empty provider must yield OutOfFrames");
        assert_eq!(err, MmuError::OutOfFrames);
        // Failure semantics: no mapping at va, pa not consumed.
        assert_eq!(as_.mapping_count(), 0, "failed map must not mutate the AS");
    }

    #[test]
    fn block_mapped_mmu_injects_block_mapped_on_map_and_unmap() {
        let mmu = BlockMappedMmu::with_blocked([VirtAddr(0x4000)]);
        // SAFETY: the inner FakeMmu never dereferences `root`.
        let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
        let mut fp = VecFrameProvider::new(vec![]);

        let map_err = mmu
            .map(
                &mut as_,
                VirtAddr(0x4000),
                frame(0x8000),
                MappingFlags::WRITE,
                &mut fp,
            )
            .expect_err("blocked VA must fail map with BlockMapped");
        assert_eq!(map_err, MmuError::BlockMapped);
        assert_eq!(as_.mapping_count(), 0);

        let unmap_err = mmu
            .unmap(&mut as_, VirtAddr(0x4000))
            .expect_err("blocked VA must fail unmap with BlockMapped");
        assert_eq!(unmap_err, MmuError::BlockMapped);
    }

    #[test]
    fn block_mapped_mmu_delegates_unblocked_addresses() {
        let mut mmu = BlockMappedMmu::new();
        mmu.block(VirtAddr(0x4000));
        // SAFETY: the inner FakeMmu never dereferences `root`.
        let mut as_ = unsafe { mmu.create_address_space(frame(0x1000)) };
        let mut fp = VecFrameProvider::new(vec![]);

        // An unblocked VA falls through to the inner FakeMmu: a successful
        // map, then unmap-missing → NotMapped (distinct from BlockMapped).
        mmu.map(
            &mut as_,
            VirtAddr(0x5000),
            frame(0x9000),
            MappingFlags::WRITE,
            &mut fp,
        )
        .expect("unblocked map must succeed")
        .flush(mmu.inner());
        let (_flush, returned) = mmu
            .unmap(&mut as_, VirtAddr(0x5000))
            .expect("unblocked unmap must succeed");
        assert_eq!(returned, frame(0x9000));

        let err = mmu
            .unmap(&mut as_, VirtAddr(0x6000))
            .expect_err("missing VA must be NotMapped, not BlockMapped");
        assert_eq!(err, MmuError::NotMapped);
    }
}
