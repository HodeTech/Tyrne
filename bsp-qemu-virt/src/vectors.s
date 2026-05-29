/*
 * aarch64 EL1 exception vector table for tyrne-bsp-qemu-virt.
 *
 * See docs/architecture/exceptions.md and ADR-0011 for the design.
 * UNSAFE-2026-0020 is the audit-log entry covering this file.
 *
 * Layout (per ARM ARM, DDI 0487G.b §D1.10): 16 entries × 0x80 bytes
 * each, 2 KiB total, 2 KiB-aligned. The CPU branches to the entry for
 * the relevant exception class; each entry has at most 32 instructions.
 *
 *   +0x000 sync   curr_el_sp0
 *   +0x080 IRQ    curr_el_sp0
 *   +0x100 FIQ    curr_el_sp0
 *   +0x180 SError curr_el_sp0
 *   +0x200 sync   curr_el_spx
 *   +0x280 IRQ    curr_el_spx   ← the only entry that fires in v1
 *   +0x300 FIQ    curr_el_spx
 *   +0x380 SError curr_el_spx
 *   +0x400 sync   lower_el_aarch64
 *   +0x480 IRQ    lower_el_aarch64
 *   +0x500 FIQ    lower_el_aarch64
 *   +0x580 SError lower_el_aarch64
 *   +0x600 sync   lower_el_aarch32
 *   +0x680 IRQ    lower_el_aarch32
 *   +0x700 FIQ    lower_el_aarch32
 *   +0x780 SError lower_el_aarch32
 *
 * Tyrne runs at EL1 with SPSel = 1 (per ADR-0024's EL drop +
 * SPSR_EL2 = 0x3c5 = EL1h). An IRQ taken from kernel code lands at
 * +0x280. The two *sync* entries (+0x200 current-EL and +0x400 lower-EL
 * AArch64) route to the SVC sync trampoline (T-021): on ESR_EL1.EC ==
 * SVC64 they save the full register frame and call the Rust syscall
 * dispatcher; any other sync cause falls through to the panic path.
 * In v1 only the +0x200 path fires (an EL1 kernel-stub `SVC`); the
 * +0x400 (real EL0) path is wired now but exercised at runtime in B6.
 * FIQ/SError on any class, and sync on the unused SP_EL0 / AArch32
 * categories, still trampoline to a panic.
 *
 * Each entry is one `b <label>` instruction; the rest of the 32-slot
 * region pads with .balign back to the next entry boundary so the
 * symbols stay layout-correct against the CPU's expected offsets.
 */

    .section .text.vectors, "ax"
    .balign 2048
    .global tyrne_vectors

tyrne_vectors:
    // ── Current EL with SP_EL0 (unused; SPSel=1 in v1) ────────────────
    .balign 0x80
    b       tyrne_unhandled_exception_trampoline    // +0x000 sync
    .balign 0x80
    b       tyrne_unhandled_irq_trampoline          // +0x080 IRQ
    .balign 0x80
    b       tyrne_unhandled_exception_trampoline    // +0x100 FIQ
    .balign 0x80
    b       tyrne_unhandled_exception_trampoline    // +0x180 SError

    // ── Current EL with SP_ELx (the live category in v1) ──────────────
    .balign 0x80
    b       tyrne_sync_trampoline                   // +0x200 sync (SVC→dispatch; else→panic) ★
    .balign 0x80
    b       tyrne_irq_curr_el_trampoline            // +0x280 IRQ ★
    .balign 0x80
    b       tyrne_unhandled_exception_trampoline    // +0x300 FIQ
    .balign 0x80
    b       tyrne_unhandled_exception_trampoline    // +0x380 SError

    // ── Lower EL using AArch64 (the real EL0 syscall path; B6) ───────
    .balign 0x80
    b       tyrne_sync_trampoline                   // +0x400 sync (EL0 SVC path; runtime-verified in B6)
    .balign 0x80
    b       tyrne_unhandled_irq_trampoline          // +0x480 IRQ
    .balign 0x80
    b       tyrne_unhandled_exception_trampoline    // +0x500 FIQ
    .balign 0x80
    b       tyrne_unhandled_exception_trampoline    // +0x580 SError

    // ── Lower EL using AArch32 (no userspace, no aarch32 in v1) ──────
    .balign 0x80
    b       tyrne_unhandled_exception_trampoline    // +0x600 sync
    .balign 0x80
    b       tyrne_unhandled_irq_trampoline          // +0x680 IRQ
    .balign 0x80
    b       tyrne_unhandled_exception_trampoline    // +0x700 FIQ
    .balign 0x80
    b       tyrne_unhandled_exception_trampoline    // +0x780 SError
    .balign 0x80
    // (table ends at +0x800 — 2 KiB total)

/*
 * ── IRQ trampoline (curr_el_spx) ──────────────────────────────────────
 *
 * Save the AAPCS64 caller-saved GPRs (x0..x18) plus x30 (LR) plus
 * ELR_EL1 + SPSR_EL1 to the kernel stack, call irq_entry(&mut frame)
 * in Rust, then restore everything and ERET.
 *
 * Frame layout (192 bytes; 16-byte aligned):
 *   [sp + 0x00]  x0,  x1
 *   [sp + 0x10]  x2,  x3
 *   [sp + 0x20]  x4,  x5
 *   [sp + 0x30]  x6,  x7
 *   [sp + 0x40]  x8,  x9
 *   [sp + 0x50]  x10, x11
 *   [sp + 0x60]  x12, x13
 *   [sp + 0x70]  x14, x15
 *   [sp + 0x80]  x16, x17
 *   [sp + 0x90]  x18, x30 (lr)
 *   [sp + 0xA0]  ELR_EL1, SPSR_EL1
 *   [sp + 0xB0]  reserved (alignment to 192 = 0xC0)
 *
 * Rust function signature:
 *   #[no_mangle] extern "C" fn irq_entry(frame: *mut TrapFrame);
 *
 * AAPCS64 callee-saved registers (x19..x28, x29) survive the bl
 * naturally — Rust preserves them across function-call boundary, so
 * the trampoline doesn't need to save them. (If a future preemption
 * scheme needs the full register set, the trampoline grows.)
 */
// The 192-byte stack carve-out and the per-`stp` byte offsets below mirror
// the Rust-side `TrapFrame` `#[repr(C)]` definition; a size or layout drift
// would corrupt every saved register on every IRQ. The compile-time guard
// `const _: () = assert!(core::mem::size_of::<TrapFrame>() == 192)` next to
// the `TrapFrame` definition in `bsp-qemu-virt/src/exceptions.rs` fails the
// build before the drift can reach an IRQ. Update both sides together if
// the frame ever grows.
tyrne_irq_curr_el_trampoline:
    sub     sp, sp, #192
    stp     x0,  x1,  [sp, #0x00]
    stp     x2,  x3,  [sp, #0x10]
    stp     x4,  x5,  [sp, #0x20]
    stp     x6,  x7,  [sp, #0x30]
    stp     x8,  x9,  [sp, #0x40]
    stp     x10, x11, [sp, #0x50]
    stp     x12, x13, [sp, #0x60]
    stp     x14, x15, [sp, #0x70]
    stp     x16, x17, [sp, #0x80]
    stp     x18, x30, [sp, #0x90]
    mrs     x0,  elr_el1
    mrs     x1,  spsr_el1
    stp     x0,  x1,  [sp, #0xA0]

    mov     x0, sp
    bl      irq_entry

    ldp     x0,  x1,  [sp, #0xA0]
    msr     elr_el1, x0
    msr     spsr_el1, x1
    ldp     x18, x30, [sp, #0x90]
    ldp     x16, x17, [sp, #0x80]
    ldp     x14, x15, [sp, #0x70]
    ldp     x12, x13, [sp, #0x60]
    ldp     x10, x11, [sp, #0x50]
    ldp     x8,  x9,  [sp, #0x40]
    ldp     x6,  x7,  [sp, #0x30]
    ldp     x4,  x5,  [sp, #0x20]
    ldp     x2,  x3,  [sp, #0x10]
    ldp     x0,  x1,  [sp, #0x00]
    add     sp, sp, #192
    eret

/*
 * ── SVC sync trampoline (current-EL +0x200 and lower-EL +0x400) ──────
 *
 * Installed at BOTH sync slots (T-021); the save → dispatch → ERET
 * mechanism is privilege-entry-agnostic. Saves the FULL register file
 * (x0..x30) plus SP_EL0, ELR_EL1, and SPSR_EL1 to a 272-byte frame,
 * routes on ESR_EL1.EC, and — for SVC64 (EC == 0x15) — calls the Rust
 * dispatcher with a pointer to the frame, then restores and ERETs. Any
 * other sync cause (data/instruction abort, etc.) falls through to the
 * panic path: those are out of scope for T-021's syscall arc.
 *
 * Frame layout (272 bytes; 16-byte aligned) — MUST match the
 * `#[repr(C)] SyscallTrapFrame` in `src/syscall.rs` byte-for-byte; the
 * `const _: () = assert!(size_of::<SyscallTrapFrame>() == 272)` guard
 * there fails the build on drift:
 *   [sp + 0x00] x0,  x1        [sp + 0x80] x16, x17
 *   [sp + 0x10] x2,  x3        [sp + 0x90] x18, x19
 *   [sp + 0x20] x4,  x5        [sp + 0xA0] x20, x21
 *   [sp + 0x30] x6,  x7        [sp + 0xB0] x22, x23
 *   [sp + 0x40] x8,  x9        [sp + 0xC0] x24, x25
 *   [sp + 0x50] x10, x11       [sp + 0xD0] x26, x27
 *   [sp + 0x60] x12, x13       [sp + 0xE0] x28, x29
 *   [sp + 0x70] x14, x15       [sp + 0xF0] x30 (lr), SP_EL0
 *                              [sp + 0x100] ELR_EL1, SPSR_EL1
 *
 * Rust function signature:
 *   #[no_mangle] extern "C" fn syscall_entry(frame: *mut SyscallTrapFrame);
 *
 * On return the dispatcher has written x0 (status) + x1..x7 (payload)
 * into the frame; the restore below reloads them, and x8..x30 + SP_EL0 +
 * ELR_EL1 + SPSR_EL1 are restored to their trapped values. Audit:
 * UNSAFE-2026-0029.
 */
tyrne_sync_trampoline:
    sub     sp, sp, #272
    stp     x0,  x1,  [sp, #0x00]
    stp     x2,  x3,  [sp, #0x10]
    stp     x4,  x5,  [sp, #0x20]
    stp     x6,  x7,  [sp, #0x30]
    stp     x8,  x9,  [sp, #0x40]
    stp     x10, x11, [sp, #0x50]
    stp     x12, x13, [sp, #0x60]
    stp     x14, x15, [sp, #0x70]
    stp     x16, x17, [sp, #0x80]
    stp     x18, x19, [sp, #0x90]
    stp     x20, x21, [sp, #0xA0]
    stp     x22, x23, [sp, #0xB0]
    stp     x24, x25, [sp, #0xC0]
    stp     x26, x27, [sp, #0xD0]
    stp     x28, x29, [sp, #0xE0]
    mrs     x0,  sp_el0
    stp     x30, x0,  [sp, #0xF0]      // x30 (lr) + SP_EL0
    mrs     x0,  elr_el1
    mrs     x1,  spsr_el1
    stp     x0,  x1,  [sp, #0x100]     // ELR_EL1 + SPSR_EL1

    // Route on ESR_EL1.EC (bits [31:26]). SVC64 == 0x15 → syscall
    // dispatch; any other sync cause → panic path.
    mrs     x0,  esr_el1
    lsr     x0,  x0,  #26
    and     x0,  x0,  #0x3f
    cmp     x0,  #0x15
    b.ne    1f

    // SVC: hand the frame pointer to the Rust dispatcher.
    mov     x0,  sp
    bl      syscall_entry

    // Restore the (now result-bearing) frame and ERET. x0/x1 are scratch
    // for the system-register restores, so they are reloaded LAST.
    ldp     x0,  x1,  [sp, #0x100]
    msr     elr_el1,  x0
    msr     spsr_el1, x1
    ldp     x30, x0,  [sp, #0xF0]
    msr     sp_el0,   x0
    ldp     x2,  x3,  [sp, #0x10]
    ldp     x4,  x5,  [sp, #0x20]
    ldp     x6,  x7,  [sp, #0x30]
    ldp     x8,  x9,  [sp, #0x40]
    ldp     x10, x11, [sp, #0x50]
    ldp     x12, x13, [sp, #0x60]
    ldp     x14, x15, [sp, #0x70]
    ldp     x16, x17, [sp, #0x80]
    ldp     x18, x19, [sp, #0x90]
    ldp     x20, x21, [sp, #0xA0]
    ldp     x22, x23, [sp, #0xB0]
    ldp     x24, x25, [sp, #0xC0]
    ldp     x26, x27, [sp, #0xD0]
    ldp     x28, x29, [sp, #0xE0]
    ldp     x0,  x1,  [sp, #0x00]
    add     sp,  sp,  #272
    eret

    // Non-SVC sync exception → panic (class 0 = generic). Does not return.
1:  mov     x0,  #0
    mrs     x1,  esr_el1
    bl      panic_entry
2:  wfe
    b       2b

/*
 * ── Unhandled-exception trampoline (sync/FIQ/SError, any class) ──────
 *
 * Save a minimal frame and call panic_entry. Does not return (panics).
 * Rust signature:
 *   #[no_mangle] extern "C" fn panic_entry(class: u64, esr: u64) -> !;
 *
 * `class` is a fixed integer encoding (0=sync, 1=fiq, 2=serror); the
 * trampolines use a simple constant.
 *
 * `esr` is read from ESR_EL1; helps narrow down "what went wrong" in
 * panic output.
 */
tyrne_unhandled_exception_trampoline:
    // Reserve 16 bytes for SP alignment; we don't return.
    sub     sp, sp, #16
    mov     x0, #0                    // class = 0 (sync/FIQ/SError, generic)
    mrs     x1, esr_el1
    bl      panic_entry
    // panic_entry never returns — defensively halt.
1:  wfe
    b       1b

/*
 * ── Unhandled-IRQ trampoline (lower-EL or curr_el_sp0; should not
 *    fire in v1) ────────────────────────────────────────────────────
 *
 * v1 has no userspace and runs with SPSel=1, so an IRQ taken from
 * SP_EL0 mode or from a lower EL is a kernel-state corruption signal.
 * Halt loudly.
 */
tyrne_unhandled_irq_trampoline:
    sub     sp, sp, #16
    mov     x0, #1                    // class = 1 (unhandled IRQ outside curr_el_spx)
    mrs     x1, esr_el1
    bl      panic_entry
1:  wfe
    b       1b

/*
 * ── Trampoline-end markers ────────────────────────────────────────────
 *
 * Used by the linker (and by the audit log) to bound the vector
 * region. `tyrne_vectors_end` is one past the last byte of the
 * trampolines; `linker.ld` does not currently use these symbols but
 * having them makes the section bounds easy to verify in objdump.
 */
    .global tyrne_vectors_end
tyrne_vectors_end:
