/*
 * Linker script for tyrne-bsp-qemu-virt — link-high / load-low (ADR-0033).
 *
 * See docs/decisions/0012-boot-flow-qemu-virt.md for the original low layout
 * and docs/decisions/0033-kernel-high-half-migration.md + docs/architecture/boot.md
 * for the high-half migration this script enables.
 *
 * The kernel is LINKED at the high-half base KBASE (TTBR1_EL1, VA[55]=1) but
 * LOADED at the physical base 0x40080000 (where QEMU `-kernel` places it). The
 * load address (LMA) of every section is its virtual address (VMA) minus the
 * constant KERNEL_HH_OFFSET — i.e. the whole image is one uniform high-half
 * alias of the physical image. This uniformity is load-bearing:
 *
 *   - `_start` and all early-boot code run at the LOW physical address with
 *     the MMU off. Because the image is high-linked *uniformly*, every
 *     PC-relative `adrp`/`:lo12:` reference resolves to the LOW (load) address
 *     at runtime (the high-link offset cancels between any two in-image
 *     symbols), so early code naturally computes physical addresses without
 *     per-site offset arithmetic.
 *   - The ELF entry point is forced LOW via `_start_phys` (= `_start` minus
 *     KERNEL_HH_OFFSET) so QEMU sets the reset PC to the physical address of
 *     `_start`, not its high VMA (the MMU is off at reset — a high PC would
 *     translation-fault immediately).
 *   - After the boot-time migration (`kernel_entry_low` → `kernel_main_high`)
 *     the kernel runs at its high VMAs; PC-relative references then resolve
 *     HIGH, and stored function pointers (task entries, etc.) — taken AFTER
 *     the migration in `kernel_main_high` — are high too, so they remain
 *     reachable once `TTBR0_EL1` is freed for userspace.
 *
 * T-016 (ADR-0027) reserves the four low-identity bootstrap page-table frames;
 * T-022 (ADR-0033) adds the two high-half root frames (__boot_pt_l0_hh /
 * __boot_pt_l1_hh). All six live in `.bss` so the `_start` BSS-zero loop
 * pre-zeros them before `mmu_bootstrap` / `build_high_half_tables` run.
 */

/* tyrne_hal::KERNEL_HIGH_HALF_OFFSET — kept in sync by a compile-time assert
 * in bsp-qemu-virt/src/main.rs. Forward limit: this offset (and the migration
 * mask in main.rs) bound the direct map to the low 4 GiB of PA; a BSP with
 * > 4 GiB RAM / high peripherals (e.g. Pi 4) needs a different offset. */
KERNEL_HH_OFFSET       = 0xFFFFFFFF00000000;
KERNEL_IMAGE_PHYS_BASE = 0x40080000;
KBASE                  = KERNEL_HH_OFFSET + KERNEL_IMAGE_PHYS_BASE;

/* ELF entry: the LOW physical address of `_start` (MMU is off at reset). */
ENTRY(_start_phys)

SECTIONS {
    /* Virtual addresses are high-half; load addresses (AT) are VMA minus the
     * high-half offset, i.e. the physical image at 0x40080000+. */
    . = KBASE;

    .text : AT(ADDR(.text) - KERNEL_HH_OFFSET) {
        KEEP(*(.text.boot))
        /* aarch64 EL1 exception vector table — VBAR_EL1 requires 2 KiB
         * (2048-byte) alignment per ARM ARM §D11.2. */
        . = ALIGN(2048);
        KEEP(*(.text.vectors))
        *(.text .text.*)
    }

    .rodata : AT(ADDR(.rodata) - KERNEL_HH_OFFSET) ALIGN(8) {
        *(.rodata .rodata.*)
    }

    .data : AT(ADDR(.data) - KERNEL_HH_OFFSET) ALIGN(8) {
        *(.data .data.*)
    }

    .bss : AT(ADDR(.bss) - KERNEL_HH_OFFSET) ALIGN(8) {
        __bss_start = .;
        *(.bss .bss.*)
        *(COMMON)
        /* Bootstrap page-table frames.
         *
         * Low-identity regime (T-016 / ADR-0027) — TTBR0_EL1 root chain:
         *   __boot_pt_l0      — L0 root; entry [0] → L1
         *   __boot_pt_l1      — L1; entry [0] → L2_low (MMIO), [1] → L2_high (RAM)
         *   __boot_pt_l2_low  — L2 covering 0x0800_0000..0x0920_0000 (GIC + UART)
         *   __boot_pt_l2_high — L2 covering 0x4000_0000..0x4800_0000 (kernel + RAM)
         *
         * High-half regime (T-022 / ADR-0033) — TTBR1_EL1 root chain. The high
         * VAs (KERNEL_HH_OFFSET + pa) land at L0[511] and L1[508]/[509]; the two
         * L2 tables above are SHARED (a block descriptor's output address is the
         * PA, identical whether reached via the low or high VA), so only the L0
         * and L1 roots are new:
         *   __boot_pt_l0_hh   — high L0 root; entry [511] → L1_hh
         *   __boot_pt_l1_hh   — high L1; entry [508] → L2_low, [509] → L2_high
         */
        . = ALIGN(4096);
        __boot_pt_start = .;
        __boot_pt_l0 = .;
        . = . + 4096;
        __boot_pt_l1 = .;
        . = . + 4096;
        __boot_pt_l2_low = .;
        . = . + 4096;
        __boot_pt_l2_high = .;
        . = . + 4096;
        __boot_pt_l0_hh = .;
        . = . + 4096;
        __boot_pt_l1_hh = .;
        . = . + 4096;
        __boot_pt_end = .;
        . = ALIGN(8);
        __bss_end = .;
    }

    . = ALIGN(16);
    . = . + 64K;
    __stack_top = .;

    /* Low physical address of `_start`, used as the forced-low ELF entry. */
    _start_phys = _start - KERNEL_HH_OFFSET;

    /DISCARD/ : {
        *(.comment)
        *(.note.*)
        *(.eh_frame*)
        *(.gcc_except_table*)
    }
}
