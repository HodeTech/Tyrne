//! Boot-time MMU activation routine for `bsp-qemu-virt`.
//!
//! Implements the activation sequence pinned by [ADR-0027 §Simulation][adr-0027]:
//! populate the four bootstrap page-table frames with the v1 identity
//! layout, configure `MAIR_EL1` / `TCR_EL1` / `TTBR0_EL1` / `TTBR1_EL1`,
//! invalidate caches + TLB, and flip `SCTLR_EL1.{M,I,C} = 1` to enable
//! the MMU + I-cache + D-cache.
//!
//! Called once by `kernel_entry` after the boot-time `cpu.now_ns()`
//! snapshot and before any MMIO-touching step (timer banner / GIC
//! initialisation). After this routine returns, every load and
//! instruction-fetch goes through the live translation regime.
//!
//! ## Audit-log coordinates
//!
//! - [UNSAFE-2026-0022] — page-table frame writes (the bulk of this
//!   module's body): writing the `L0` / `L1` / `L2_low` / `L2_high` block
//!   + table descriptors directly to the four bootstrap frames.
//! - [UNSAFE-2026-0023] — system-register writes (`MSR MAIR_EL1`,
//!   `MSR TCR_EL1`, `MSR TTBR0_EL1`, `MSR TTBR1_EL1`, `MSR SCTLR_EL1`).
//!   Originally introduced for `QemuVirtMmu::activate` (Stage 3); this
//!   routine extends the entry's scope via Amendment.
//! - [UNSAFE-2026-0024] — TLB / I-cache invalidate asm + barriers
//!   (`TLBI VMALLE1` / `IC IALLU` / `DSB ISH` / `ISB`). Same scope-
//!   extension Amendment pattern.
//!
//! [adr-0027]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0027-kernel-virtual-memory-layout.md
//! [UNSAFE-2026-0022]: https://github.com/HodeTech/Tyrne/blob/main/docs/audits/unsafe-log.md
//! [UNSAFE-2026-0023]: https://github.com/HodeTech/Tyrne/blob/main/docs/audits/unsafe-log.md
//! [UNSAFE-2026-0024]: https://github.com/HodeTech/Tyrne/blob/main/docs/audits/unsafe-log.md

use core::arch::asm;

use tyrne_hal::mmu::vmsav8::{
    block_descriptor, flags_to_descriptor_bits, table_descriptor, MAIR_EL1_VALUE,
    SCTLR_EL1_MMU_ENABLE_MASK, TCR_EL1_VALUE, TCR_EL1_VALUE_HIGH_HALF,
};
use tyrne_hal::{MappingFlags, KERNEL_HIGH_HALF_OFFSET};

// Linker symbols for the four bootstrap page-table frames. The Rust
// type `[u64; 512]` mirrors the actual storage shape (one 4 KiB frame
// = 512 × 8 B descriptors) so casting `addr_of!(...)` to `*mut u64`
// is alignment-clean. The linker script (`bsp-qemu-virt/linker.ld`)
// places each symbol at a 4 KiB-aligned offset inside the `.bss`
// range so `_start`'s BSS-zero loop pre-zeros every byte before this
// routine runs.
extern "C" {
    static __boot_pt_l0: [u64; 512];
    static __boot_pt_l1: [u64; 512];
    static __boot_pt_l2_low: [u64; 512];
    static __boot_pt_l2_high: [u64; 512];
    /// High-half (`TTBR1_EL1`) root frames (T-022 / ADR-0033). The two L2
    /// tables above are SHARED between the low-identity and high-half
    /// regimes — a block descriptor's output address is the PA, identical
    /// whether reached via the low or high VA — so only the L0/L1 roots are
    /// new. See [`high_half_activate`].
    static __boot_pt_l0_hh: [u64; 512];
    static __boot_pt_l1_hh: [u64; 512];
}

/// Entries per 4 KiB translation table.
const ENTRIES_PER_TABLE: usize = 512;

/// L2 block-descriptor stride in bytes (2 MiB).
const BLOCK_2MIB: u64 = 2 * 1024 * 1024;

/// Activate the MMU.
///
/// Walks the [ADR-0027 §Simulation][adr-0027] state-machine in order:
///
/// 1. Populate the four bootstrap page-table frames with the v1 layout.
/// 2. Configure `MAIR_EL1` / `TCR_EL1` / `TTBR0_EL1` / `TTBR1_EL1` and
///    issue an `ISB` so the writes are observed before the MMU enable.
/// 3. Invalidate the TLB + I-cache, then flip `SCTLR_EL1.{M,I,C} = 1`
///    and `ISB` to drain the pipeline so the next instruction-fetch
///    goes through the freshly-installed regime.
///
/// # Safety
///
/// - Must be called exactly once per boot, before any MMIO-touching
///   step (the timer banner, the GIC initialisation), so those steps
///   inherit the device-attribute mapping this routine installs.
/// - Must be called at EL1 with the bootstrap frames pre-zeroed by the
///   `_start` BSS-zero loop (the linker script places `.boot_pt`
///   inside the `[__bss_start, __bss_end)` range — see
///   [`linker.ld`][linker]).
/// - The kernel image must already live at PA `0x4008_0000` and be
///   identity-covered by the `L2_high` block range `[0x4000_0000,
///   0x4800_0000)` this routine populates — without that, the next
///   instruction-fetch after `SCTLR.M = 1` faults (per ADR-0027
///   §Simulation §Step 3).
///
/// [adr-0027]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0027-kernel-virtual-memory-layout.md
/// [linker]: https://github.com/HodeTech/Tyrne/blob/main/bsp-qemu-virt/linker.ld
pub unsafe fn mmu_bootstrap() {
    // `addr_of!` of an `extern "C" static` is itself safe — it does
    // not dereference the symbol; it just yields the linker-resolved
    // address. The casts from `*const [u64; 512]` to `*mut u64` are
    // alignment-clean (8 ≤ alignment-of `[u64; 512]` = 8) and produce
    // base pointers into the 4 KiB-aligned, exclusively-owned, pre-
    // zeroed bootstrap frames per `linker.ld` `.boot_pt` + `_start`'s
    // BSS-zero loop. The pointers are consumed by `write_volatile`s
    // below — those are the audited writes (UNSAFE-2026-0022).
    let l0 = core::ptr::addr_of!(__boot_pt_l0).cast::<u64>().cast_mut();
    let l1 = core::ptr::addr_of!(__boot_pt_l1).cast::<u64>().cast_mut();
    let l2_low = core::ptr::addr_of!(__boot_pt_l2_low)
        .cast::<u64>()
        .cast_mut();
    let l2_high = core::ptr::addr_of!(__boot_pt_l2_high)
        .cast::<u64>()
        .cast_mut();

    // ── Step 1 — populate the bootstrap tables ──────────────────────────────────

    // SAFETY: write the L0 → L1 → L2 chain. All four frames are page-
    // aligned, exclusively owned by this routine for the duration of
    // the call (single-core, single-caller), and pre-zeroed by the
    // BSS loop. Indices used are constant, in-range.
    // Safer alternatives rejected: VMSAv8 page-table descriptors are
    // raw `u64` words at fixed offsets within physical frames the BSP
    // does not own as Rust objects (they are address-keyed, not
    // value-owned). Materialising a `&mut [u64; 512]` reference into
    // these frames is itself the audited operation; wrapping it in a
    // safe-looking abstraction would not remove the underlying raw-
    // pointer write — only obscure where the audit point lives.
    // `core::ptr::write_volatile` is the most honest expression of
    // what the bootstrap is doing. Audit: UNSAFE-2026-0022.
    unsafe {
        // L0[0] → L1
        core::ptr::write_volatile(l0.add(0), table_descriptor(l1 as u64));

        // L1[0] → L2_low (covers 0x0000_0000 .. 0x4000_0000;
        //                 we'll only populate the device-MMIO portion)
        core::ptr::write_volatile(l1.add(0), table_descriptor(l2_low as u64));
        // L1[1] → L2_high (covers 0x4000_0000 .. 0x8000_0000;
        //                  we'll populate 0x4000_0000..0x4800_0000)
        core::ptr::write_volatile(l1.add(1), table_descriptor(l2_high as u64));

        // L2_low[64..73] = 9 × 2 MiB device blocks for
        //   GIC distributor + GIC CPU interface + PL011 UART
        //   spanning 0x0800_0000..0x0920_0000.
        //
        // L2 index for VA `va` is (va >> 21) & 0x1FF; for the
        // 0x0800_0000-based MMIO range (which lives under L1[0])
        // the VA bits 38..30 are all zero, so the L2 index is just
        // (va >> 21) for the bits that remain — that is, 64..72
        // inclusive (9 blocks).
        let device_flags = MappingFlags::DEVICE | MappingFlags::WRITE | MappingFlags::GLOBAL;
        let device_bits = flags_to_descriptor_bits(device_flags);
        let mut va: u64 = 0x0800_0000;
        let mut idx: usize = (va >> 21) as usize;
        while idx < (0x0920_0000_u64 >> 21) as usize {
            let entry = block_descriptor(va, device_bits);
            core::ptr::write_volatile(l2_low.add(idx), entry);
            va += BLOCK_2MIB;
            idx += 1;
        }

        // L2_high[0..64] = 64 × 2 MiB normal-cached blocks covering
        //   0x4000_0000..0x4800_0000 (kernel image + RAM).
        //
        // The VA bits 38..30 = 1 (because L1[1] covers
        // 0x4000_0000..0x8000_0000); the L2 index is therefore
        // (va >> 21) & 0x1FF, which for VA = 0x4000_0000 is 0 and
        // grows to 63 at VA = 0x47E0_0000.
        let ram_flags = MappingFlags::WRITE | MappingFlags::EXECUTE | MappingFlags::GLOBAL;
        let ram_bits = flags_to_descriptor_bits(ram_flags);
        let mut idx: usize = 0;
        let mut pa: u64 = 0x4000_0000;
        while idx < ENTRIES_PER_TABLE / 8 {
            // ENTRIES_PER_TABLE / 8 == 64 — the 128 MiB RAM range.
            let entry = block_descriptor(pa, ram_bits);
            core::ptr::write_volatile(l2_high.add(idx), entry);
            pa += BLOCK_2MIB;
            idx += 1;
        }
    }

    // ── Step 2 — configure system registers ─────────────────────────────────────
    //
    // SAFETY: writes to MAIR_EL1, TCR_EL1, TTBR0_EL1, TTBR1_EL1 stage
    // the translation regime. `SCTLR_EL1.M` is still 0, so the
    // current regime (translation off) remains in effect until Step 3
    // explicitly flips the bit. The trailing `ISB` ensures the system-
    // register writes are observed before the MMU is enabled.
    //
    // `nomem` is **deliberately omitted** here (kept for the prior
    // pre-T-016 commit but removed by the 2026-05-09 review-round
    // per CodeRabbit's compiler-side memory-barrier concern). Without
    // `nomem`, the compiler treats this asm block as a memory clobber
    // and cannot reorder Step 1's page-table descriptor writes past
    // it. (Step 1's writes are `core::ptr::write_volatile`, which are
    // already anchored at the source location, but recording memory
    // intent on the asm block protects against any future non-
    // volatile accesses that land nearby.) Architectural global
    // visibility of those stores is enforced by Step 3's `DSB ISH`,
    // which drains all prior memory accesses inner-shareable before
    // the MMU enable.
    // Safer alternatives rejected: aarch64 EL1 system registers
    // (`MAIR_EL1`, `TCR_EL1`, `TTBR0_EL1`, `TTBR1_EL1`) are accessed
    // exclusively via `MSR` / `MRS` instructions; no `cortex-a` /
    // `aarch64-cpu` crate is currently in the dependency graph (and
    // adding one would be a load-bearing dependency for a single
    // bootstrap site — see ADR-0014's dependency-policy "minimum
    // necessary surface" rule). Inline asm via `core::arch::asm!`
    // is the language-supplied minimal surface for the architected
    // `MSR` instruction. Audit: UNSAFE-2026-0023 (extending its
    // activate-only scope to these bootstrap MAIR/TCR/TTBR/SCTLR
    // writes via Amendment).
    unsafe {
        asm!(
            "msr mair_el1, {mair}",
            "msr tcr_el1, {tcr}",
            "msr ttbr0_el1, {ttbr0}",
            "msr ttbr1_el1, xzr",
            "isb",
            mair = in(reg) MAIR_EL1_VALUE,
            tcr = in(reg) TCR_EL1_VALUE,
            ttbr0 = in(reg) (l0 as u64),
            options(nostack),
        );
    }

    // ── Step 3 — invalidate, then enable the MMU ────────────────────────────────
    //
    // SAFETY: TLBI VMALLE1 + IC IALLU drop any speculatively-cached
    // translation / instruction state from the pre-MMU regime; DSB
    // ISH ensures the invalidates complete inner-shareable; the second
    // ISB drains the pipeline so the SCTLR_EL1.M=1 read-modify-write
    // is observed by every later instruction-fetch. After SCTLR.M=1
    // the next instruction-fetch goes through the new regime; because
    // the kernel image is identity-covered by L2_high[0..64], the
    // fetch succeeds and the PC continues at the same address. Any
    // typo in Step 1 would surface here as a Translation Fault on the
    // next fetch (per ADR-0027 §Simulation §Step 3).
    // Safer alternatives rejected: `TLBI`, `IC IALLU`, `DSB`, `ISB`,
    // and the `MRS`/`MSR SCTLR_EL1` pair are architectural cache- and
    // pipeline-maintenance / system-register instructions with no
    // safe-Rust equivalent. The architected ordering across these
    // instructions (drain → invalidate → enable → drain) cannot be
    // expressed without inline asm because each barrier's effect is
    // global to the CPU pipeline state, not modelled in any safe
    // abstraction. Audit: UNSAFE-2026-0024 (TLB / I-cache asm) +
    // UNSAFE-2026-0023 (SCTLR_EL1 write).
    unsafe {
        asm!(
            "tlbi vmalle1",
            "dsb ish",
            "ic iallu",
            "dsb ish",
            "isb",
            "mrs   x9, sctlr_el1",
            "orr   x9, x9, {mask}",
            "msr   sctlr_el1, x9",
            "isb",
            mask = in(reg) SCTLR_EL1_MMU_ENABLE_MASK,
            // x9 is a temporary; the asm declares it via `out` so the
            // compiler does not assume any value across the block.
            out("x9") _,
            options(nostack, nomem),
        );
    }
}

/// Build the high-half (`TTBR1_EL1`) translation tables and bring the
/// high-half regime live — while still executing in the low-identity
/// regime. Implements [ADR-0033 §Simulation rows 0–1][adr-0033].
///
/// Must run AFTER [`mmu_bootstrap`] (which builds the four low-identity
/// frames + the two L2 tables this routine SHARES, and enables the MMU)
/// and BEFORE the [`crate::kernel_entry`] migration trampoline crosses the
/// PC into the high half. On return both regimes are live: the low identity
/// (`TTBR0_EL1`) the kernel is still executing through, and the high-half
/// (`TTBR1_EL1`, `EPD1 = 0`) the trampoline is about to branch into.
///
/// High-half layout (per [ADR-0033 §"High-half layout"][adr-0033]): every
/// kernel VA is `KERNEL_HIGH_HALF_OFFSET + pa`, so at `T1SZ = 16` they land
/// at `L0[511]` and `L1[508]` (device) / `L1[509]` (RAM). The L2 tables are
/// SHARED with the low identity (a block descriptor's output address is the
/// PA, identical via either VA), so only the L0/L1 roots are new.
///
/// **v1 simplification (RWX-equivalent; PXN-split deferred to ADR-0034).**
/// Sharing `L2_high` makes the high-half RAM window `PXN = 0` (kernel-
/// executable) for its whole span — so the kernel image *and* the
/// physmap/direct-map deref path (page tables, PMM frames, copy-user) live
/// in one `PXN = 0`, `AP = 0b00` window. This is RWX-equivalent to the
/// identity map it replaces (T-016 mapped all RAM `WRITE | EXECUTE`), which
/// [T-022 §Out of scope](../../docs/analysis/tasks/phase-b/T-022-high-half-kernel-mapping.md)
/// explicitly accepts; the [ADR-0033 §High-half-layout][adr-0033] PXN=1
/// physmap region distinct from the PXN=0 image region is the per-section
/// W^X hardening end-state, deferred to ADR-0034. `EL0` is never granted
/// access (`AP = 0b00`), so this is a privileged-side W^X gap only, not an
/// EL0-reachable one.
///
/// # Safety
///
/// - Must be called exactly once per boot, at EL1, after [`mmu_bootstrap`]
///   (the shared L2 tables and the low-identity MMU must already be live)
///   and before the high-half migration trampoline.
/// - The `__boot_pt_l0_hh` / `__boot_pt_l1_hh` frames must be page-aligned
///   and pre-zeroed (the linker places them in `.bss`; `_start`'s BSS-zero
///   loop zeros them) so the unwritten slots read as invalid descriptors.
///
/// Audit: UNSAFE-2026-0022 (high-half page-table frame writes — Amendment)
/// + UNSAFE-2026-0023 (`MSR TTBR1_EL1` / `MSR TCR_EL1` — Amendment).
///
/// [adr-0033]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0033-kernel-high-half-migration.md
pub unsafe fn high_half_activate() {
    // High-half root frames (new); the L2 tables are shared with the low
    // identity. `addr_of!` resolves these `.bss` symbols to their LOW
    // physical addresses here (this routine executes low, so the PC-relative
    // materialisation yields the load address = PA) — exactly the PAs the
    // table/TTBR descriptors must carry.
    let l0_hh = core::ptr::addr_of!(__boot_pt_l0_hh)
        .cast::<u64>()
        .cast_mut();
    let l1_hh = core::ptr::addr_of!(__boot_pt_l1_hh)
        .cast::<u64>()
        .cast_mut();
    let l2_low_pa = core::ptr::addr_of!(__boot_pt_l2_low) as u64;
    let l2_high_pa = core::ptr::addr_of!(__boot_pt_l2_high) as u64;

    // High VAs → page-table indices (computed, not hardcoded, so the
    // KERNEL_HIGH_HALF_OFFSET choice is the single source of truth).
    let off = KERNEL_HIGH_HALF_OFFSET as u64;
    let va_dev = off + 0x0800_0000; // GIC + UART device window base
    let va_ram = off + 0x4000_0000; // RAM (kernel image) window base
    let l0_idx = ((va_ram >> 39) & 0x1FF) as usize; // 511
    let l1_idx_dev = ((va_dev >> 30) & 0x1FF) as usize; // 508
    let l1_idx_ram = ((va_ram >> 30) & 0x1FF) as usize; // 509

    // SAFETY: the three frames are page-aligned, exclusively owned for the
    // duration of this single-core boot call, and pre-zeroed by the BSS
    // loop. Indices are < 512 by the `& 0x1FF` construction. The table
    // descriptors point at the shared L2 tables (device / RAM) and the new
    // L1_hh, all by PA. Safer alternatives rejected: identical to
    // `mmu_bootstrap` Step 1 — VMSAv8 descriptors are raw `u64` words at fixed
    // offsets in frames the BSP owns by address (not as Rust objects), so a
    // safe wrapper would only relocate, not remove, the audited
    // `write_volatile`. Audit: UNSAFE-2026-0022.
    unsafe {
        // L0_hh[511] → L1_hh
        core::ptr::write_volatile(l0_hh.add(l0_idx), table_descriptor(l1_hh as u64));
        // L1_hh[508] → L2_low (device, shared); L1_hh[509] → L2_high (RAM, shared)
        core::ptr::write_volatile(l1_hh.add(l1_idx_dev), table_descriptor(l2_low_pa));
        core::ptr::write_volatile(l1_hh.add(l1_idx_ram), table_descriptor(l2_high_pa));
    }

    // SAFETY: publish the descriptor writes to the table walker (`DSB ISH`)
    // BEFORE installing TTBR1 and clearing EPD1 — so no walk, once enabled,
    // can read a stale/zero descriptor (ADR-0033 §Simulation row 0). Then
    // `MSR TTBR1_EL1` (the high root PA) + `ISB`, then `MSR TCR_EL1` with the
    // EPD1-cleared constant (every TTBR0-governing field byte-stable, so the
    // live low regime is undisturbed — row 1) + `ISB`. After this the high
    // half translates, but the PC/SP/VBAR are still low (the migration
    // trampoline performs the crossing). `nomem` omitted so the descriptor
    // writes above are not reordered past this block. Safer alternatives
    // rejected: identical to `mmu_bootstrap` Step 2 — EL1 system registers
    // (`TTBR1_EL1`, `TCR_EL1`) and the `DSB`/`ISB` ordering have no safe-Rust
    // expression; inline `asm!` is the minimal architected surface (no
    // `cortex-a`-class crate in the dependency graph, per ADR-0014).
    // Audit: UNSAFE-2026-0023.
    unsafe {
        asm!(
            "dsb ish",
            "msr ttbr1_el1, {ttbr1}",
            "isb",
            "msr tcr_el1, {tcr}",
            "isb",
            ttbr1 = in(reg) (l0_hh as u64),
            tcr = in(reg) TCR_EL1_VALUE_HIGH_HALF,
            options(nostack),
        );
    }
}
