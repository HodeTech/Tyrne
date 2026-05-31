/*
 * Userspace linker script for the v1 "hello" raw-flat image (ADR-0029 / ADR-0039).
 *
 * The loader (kernel/src/obj/task_loader.rs) maps the objcopy'd bytes at a
 * fixed userspace VA with the entry instruction at OFFSET 0. This script:
 *   - fixes the image at USERSPACE_IMAGE_BASE_VA (0x0080_0000),
 *   - places `_start` (in `.text._start`) FIRST in `.text` so offset 0 is the
 *     entry, then the rest of `.text`, then `.rodata` (the greeting),
 *   - forbids `.data` / `.bss`: the single image region maps USER|EXECUTE (no
 *     WRITE), so a writable byte would fault on first write — the ASSERTs below
 *     fail the build LOUDLY rather than silently embed unwritable globals.
 *
 * USERSPACE_IMAGE_BASE_VA must be kept in sync with the Rust-side constant
 * `USERSPACE_IMAGE_BASE_VA` in bsp-qemu-virt/src/main.rs (a linker script
 * cannot import a Rust const — ADR-0039 §Decision outcome; the `--defsym`
 * upgrade is named there for full drift-elimination if it earns its keep).
 */

USERSPACE_IMAGE_BASE_VA = 0x00800000;

ENTRY(_start)

SECTIONS {
    . = USERSPACE_IMAGE_BASE_VA;

    .text : {
        KEEP(*(.text._start))   /* _start first => offset 0 is the entry */
        *(.text .text.*)
    }

    .rodata : ALIGN(8) {
        *(.rodata .rodata.*)
    }

    /* v1 forbids writable data (image is USER|EXECUTE, no WRITE) and is
     * non-PIC (fixed VA — no relocations). Collect any stray .data/.bss/.got so
     * the ASSERTs can prove they are empty rather than let a writable byte or a
     * PIC artifact silently slip into the raw-flat image. */
    .data : { *(.data .data.*) }
    .bss  : { *(.bss .bss.* COMMON) }
    .got  : { *(.got .got.plt) }

    ASSERT(SIZEOF(.data) == 0,
        "userland hello: .data must be empty (image maps USER|EXECUTE, no WRITE)")
    ASSERT(SIZEOF(.bss) == 0,
        "userland hello: .bss must be empty (image maps USER|EXECUTE, no WRITE)")
    ASSERT(SIZEOF(.got) == 0,
        "userland hello: .got must be empty (v1 is non-PIC, fixed-VA — no relocations)")

    /* Drop metadata/unwind/debug sections — not part of the raw-flat image. */
    /DISCARD/ : {
        *(.comment)
        *(.note .note.*)
        *(.eh_frame .eh_frame_hdr)
        *(.ARM.exidx .ARM.exidx.*)
        *(.ARM.attributes)
        *(.debug .debug.*)
    }
}
