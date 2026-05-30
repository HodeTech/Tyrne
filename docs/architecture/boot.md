# Boot flow

Tyrne boots in four stages: QEMU (or the board firmware) hands control to the ELF entry point, a short assembly stub sets up the runtime environment, a Rust entry function (`kernel_entry`) wires the BSP together and brings up every kernel subsystem, and finally `start()` transfers control to the cooperative scheduler. This document is the "how" for Phase 4c on `bsp-qemu-virt`; the "why" for each concrete choice lives in [ADR-0012](../decisions/0012-boot-flow-qemu-virt.md). Each future BSP will follow the same stage structure with its own addresses and peripherals.

## Context

The overall three-layer architecture is described in [`overview.md`](overview.md), and the HAL traits the kernel uses are in [`hal.md`](hal.md). This document focuses specifically on the boot path from reset to scheduler steady state, as implemented for the QEMU `virt` aarch64 target.

## Design

### Stages

The four boot stages, each with a tightly bounded responsibility:

1. **Firmware / loader.** QEMU's `-kernel` flag loads the ELF image at its linked-in load address (`0x40080000` per [ADR-0012](../decisions/0012-boot-flow-qemu-virt.md)), sets the PC to the ELF's entry point (`_start`), and enters at EL1 (default QEMU `virt`) or EL2 (`-machine virtualization=on`, or most real-hardware boot stacks delivering at EL2). The device-tree blob address is placed in `x0`; v1 ignores it.
2. **Assembly stub (`_start`).** Three phases: first, K3-12 (interrupts masked via `MSR DAIFSet, #0xf`) executes at the very head of the reset vector so a spurious interrupt cannot escape into an uninstalled vector table. Second, the EL drop (per [ADR-0024](../decisions/0024-el-drop-policy.md)) reads `CurrentEL`; on EL2 it configures `HCR_EL2` / `SPSR_EL2` / `ELR_EL2` and `eret`s to a post-drop label, on EL1 it falls through, on EL3 (or any unexpected EL) it halts in a named-label `wfe`-loop (`halt_unsupported_el: wfe ; b halt_unsupported_el`) — there is no Rust panic infrastructure pre-`kernel_entry`. Third, the conventional setup: load `__stack_top` into `SP`, enable FP/SIMD via `CPACR_EL1`, zero the BSS range (`__bss_start` .. `__bss_end`) using 8-byte stores, and branch to `kernel_entry`. If `kernel_entry` ever returns (it shouldn't), the stub falls into a defensive `wfe ; b 2b` halt loop. After phase two, every later instruction runs at EL1 — the precondition T-009's `UNSAFE-2026-0016` runtime check now relies on as a load-bearing invariant rather than a defensive guard.
3. **`kernel_entry` → `kernel_main_high` (Rust, in the BSP).** The first Rust code to run, split across the high-half migration (T-022 / ADR-0033; see §"High-half migration" below for the mechanism):
   - **`kernel_entry` (LOW physical alias, MMU off → low identity).** Constructs a throwaway low-MMIO `Pl011Uart` for early diagnostics, installs the EL1 vector table (T-012, low vectors), **activates the low-identity MMU** via `mmu_bootstrap` (T-016 / ADR-0027 — lands the v1 identity layout in `TTBR0_EL1`, flips `SCTLR_EL1.{M,I,C} = 1`; MMIO goes through device-nGnRnE attributes), then **builds the high-half `TTBR1_EL1` tables** via `high_half_activate` (T-022 / ADR-0033 — `EPD1 1→0`, both regimes now live) and **branches the running kernel into the high half** through the migration trampoline (`MSR VBAR`-high; rebase `SP`; `br kernel_main_high`). It never returns. Marked `#[no_mangle] extern "C"` so the assembly stub can find it.
   - **`kernel_main_high` (HIGH half, `TTBR1_EL1`).** Frees `TTBR0_EL1` (null + `EPD0 = 1` + `TLBI VMALLE1`), prints `tyrne: high-half active`, then runs the rest of bring-up at high-half addresses: constructs the persistent `Pl011Uart` + `QemuVirtCpu` at the HIGH device-MMIO alias, captures the boot-to-end timestamp, **initialises the Physical Memory Manager** (T-017 / ADR-0035 — bitmap allocator over the 128 MiB RAM extent, two reserved ranges covering the QEMU firmware region and the kernel image / `.bss` / `.boot_pt` / boot stack), **initialises the address-space arena** (T-018 / ADR-0028 — wraps the bootstrap L0 root as `AddressSpaceArena<QemuVirtMmu>` slot 0 + mints the bootstrap AS authority cap; no `Mmu::create_address_space` on the populated root per ADR-0028 §Simulation row 0), **loads the embedded userspace placeholder image** via [`task_loader::load_image`](task-loader.md) (T-019 / ADR-0029 — produces a `LoadedImage` for the embedded `mov w0, #42; ret` blob; **does NOT execute** — runnability gates on B6 per phase-b §B4 §Revision-notes; first runtime exerciser of [UNSAFE-2026-0025](../audits/unsafe-log.md) post-bootstrap `Mmu::map`, [UNSAFE-2026-0026](../audits/unsafe-log.md) `Pmm::alloc_frame` zero-fill, and [UNSAFE-2026-0027](../audits/unsafe-log.md) loader byte-copy), initialises the GIC, unmasks `DAIF.I`, prints the timer banner, then sets up the kernel-object arenas + capability tables + IPC + scheduler before transferring control to `start()`.
4. **Scheduler start (`start`).** The final call in `kernel_main_high` is `start(SCHED.as_mut_ptr(), cpu, activate_address_space)`, which hands control to the cooperative FIFO scheduler and never returns; the scheduler runs the first ready task and drives the cooperative IPC demo until the system halts (see [scheduler.md](scheduler.md)). An early design intended a portable `tyrne_kernel::run` that a BSP would delegate to; the B-phase brought subsystem bring-up into the kernel-entry path instead, and `start` (defined in `kernel/src/sched/mod.rs`) is the actual handoff point. Consolidating the bring-up back into a portable kernel entry is a possible future refactor.

### High-half migration (T-022 / ADR-0033)

Since [T-022](../analysis/tasks/phase-b/T-022-high-half-kernel-mapping.md) the kernel runs in the high half (`TTBR1_EL1`) so `TTBR0_EL1` is free for per-task userspace — the [ADR-0033](../decisions/0033-kernel-high-half-migration.md) prerequisite that unblocks a real EL0 task's `SVC` vector fetch (B6). The kernel image is **linked high** (`KBASE = 0xFFFF_FFFF_4008_0000`) but **loaded low** (`0x4008_0000`); the ELF entry is forced to `_start`'s low physical address (`_start_phys`, [`linker.ld`](../../bsp-qemu-virt/linker.ld)) because the MMU is off at reset. A single linear high-half offset `KERNEL_HIGH_HALF_OFFSET = 0xFFFF_FFFF_0000_0000` maps physical memory: `kernel_VA = OFFSET + PA` ([`tyrne_hal::phys_to_kernel_va`](../../hal/src/mmu/mod.rs)). The boot-time transition (ADR-0033 §Simulation):

1. **`kernel_entry` (LOW).** Runs at the low physical alias with the MMU off. Because the whole image is high-linked *uniformly*, PC-relative `adrp`/`adr` references resolve to LOW (load) addresses at runtime (the offset cancels between in-image symbols), so no separate identity-VMA section is needed. It enables the low-identity MMU (`mmu_bootstrap`), then builds the high-half `TTBR1` tables and clears `EPD1` (`mmu_bootstrap::high_half_activate`: `DSB ISH` → `MSR TTBR1_EL1` → `ISB` → `MSR TCR_EL1` with `EPD1 = 0` → `ISB`). Both regimes are now live; the kernel still executes low.
2. **Migration trampoline (the crossing).** A small inline-asm block: `MSR VBAR_EL1, <high>` + `ISB` (high vectors live before the branch) → `add sp, sp, OFFSET` (rebase `SP` to the high stack alias) → `br <kernel_main_high high VA>`, `options(noreturn)`. The PC physically crosses low→high at the `br`; `DAIF` is masked and no `StaticCell` holds a low VA, so the crossing cannot brick.
3. **`kernel_main_high` (HIGH).** Frees `TTBR0_EL1` (`MSR TTBR0_EL1, xzr` + set `EPD0 = 1` + `TLBI VMALLE1` + `DSB ISH`), prints the new **`tyrne: high-half active`** boot marker, then constructs the console + GIC at their high device-MMIO aliases and runs the rest of the bring-up (§Stage 3) at high-half addresses. Function pointers / vtables (absolute, HIGH) are all taken here, so they stay reachable once `TTBR0` is freed.

v1 maps the whole high-half RAM window `PXN = 0` (RWX-equivalent, like the identity map it replaces; `AP = 0b00` keeps EL0 with no access); the ADR-0033 layout's distinct `PXN = 1` physmap region is per-section W^X hardening deferred to ADR-0034. The migration is **fault-clean** (`-d int,unimp`: exactly the 2 syscall-smoke `SVC` exceptions, zero new Translation/Permission faults). Audit: [UNSAFE-2026-0031](../audits/unsafe-log.md) + Amendments to 0022/0023/0024.

> **Forward limit (Pi 4 / large images).** `KERNEL_HIGH_HALF_OFFSET = 0xFFFF_FFFF_0000_0000` bounds the direct map to the **low 4 GiB** of PA, and the migration mask (`OFFSET | (addr & 0xFFFF_FFFF)`) assumes the kernel image PA is below 4 GiB. A BSP with > 4 GiB RAM or peripherals above 4 GiB (e.g. the Raspberry Pi 4, Phase D) needs a different offset **and** a revisited mask before carrying this pattern over.

### Boot-time sequence

```mermaid
sequenceDiagram
    participant QEMU as QEMU virt / firmware
    participant Asm as _start (asm stub)
    participant KE as kernel_entry (BSP, Rust)
    participant U as PL011 UART

    QEMU->>Asm: PC = _start, DTB in x0 (ignored), entry EL = 1 or 2
    Note over Asm: Phase 1 — K3-12: msr daifset, #0xf<br/>(interrupts masked from very first instruction)
    Note over Asm: Phase 2 — EL drop (per ADR-0024)<br/>read CurrentEL; mask bits[3:2]
    alt CurrentEL == EL2
        Asm->>Asm: configure HCR_EL2 (RW=1, E2H=0, TGE=0)
        Asm->>Asm: SPSR_EL2 = EL1h | DAIF masked (0x3c5)
        Asm->>Asm: ELR_EL2 = post_eret label; eret
        Note over Asm: now at EL1, DAIF still masked
    else CurrentEL == EL1
        Note over Asm: fall through (no drop needed)
    else CurrentEL == EL3 (unsupported)
        Note over Asm: halt_unsupported_el: wfe ; b halt_unsupported_el
    end
    Note over Asm: Phase 3 — conventional setup<br/>SP ← __stack_top<br/>CPACR_EL1.FPEN ← 0b11; isb<br/>BSS zeroed (__bss_start..__bss_end)
    Asm->>KE: bl kernel_entry  (EL = 1, guaranteed)
    Note over KE: T-009 / UNSAFE-2026-0016 asserts CurrentEL == 1<br/>as a load-bearing post-condition of Phase 2
    Note over KE: ── kernel_entry (LOW physical alias; MMU off) ──
    KE->>KE: early Pl011Uart at LOW 0x0900_0000 (identity)
    KE->>U: write_bytes(b"tyrne: hello from kernel_main\n")
    KE->>KE: install VBAR_EL1 (low vectors; T-012)
    KE->>KE: mmu_bootstrap() — low-identity MMU on<br/>(T-016 / ADR-0027)
    KE->>U: write_bytes(b"tyrne: mmu activated\n")
    KE->>KE: high_half_activate() — build TTBR1 tables, EPD1 1→0<br/>(T-022 / ADR-0033; both regimes now live)
    KE->>KE: migration trampoline — MSR VBAR-high; ISB;<br/>add sp,sp,OFFSET; br kernel_main_high (PC crosses low→high)
    Note over KE: ── kernel_main_high (HIGH half, TTBR1_EL1) ──
    KE->>KE: free TTBR0_EL1 (xzr + EPD0=1 + TLBI VMALLE1)
    KE->>KE: Pl011Uart + QemuVirtCpu at HIGH device-MMIO alias
    KE->>U: write_bytes(b"tyrne: high-half active\n")
    KE->>KE: boot_ns = cpu.now_ns() snapshot (post-migration)
    KE->>KE: Pmm::new — Physical Memory Manager init<br/>(T-017 / ADR-0035)
    KE->>U: write_bytes(b"tyrne: pmm initialized (...)\n")
    KE->>KE: AddressSpace arena init — wrap bootstrap L0<br/>(T-018 / ADR-0028; populated-but-uninstalled root post-T-022)
    KE->>U: write_bytes(b"tyrne: address-space-arena ready (...)\n")
    KE->>KE: task_loader::load_image — embedded raw-flat blob<br/>into a fresh AS (T-019 / ADR-0029; NOT executed)
    KE->>U: write_bytes(b"tyrne: image loaded (...)\n")
    KE->>KE: GIC init + DAIF.I unmask (T-012; high device-MMIO)
    KE->>U: write_bytes(b"tyrne: timer ready (...)")
    KE->>KE: kernel-object setup, IPC, scheduler
    KE->>KE: start() — never returns
    Note over KE: steady state — cooperative IPC demo (high half)
```

### Memory map at boot

The kernel image is a single contiguous block starting at `0x40080000`; RAM below that is reserved for QEMU's internal use. The initial stack is a 64 KiB region reserved at the image's tail.

```
0x4000_0000  ─── RAM start (reserved for QEMU firmware region)
             ...
0x4008_0000  ─── _start (.text.boot) ← ELF entry
             .text
             .rodata
             .data
             .bss              (zeroed by _start)
             [reserved 64 KiB] (initial stack region)
__stack_top  ─── high end of stack
             ...
0x4800_0000  ─── end of 128 MiB RAM region
```

- **Code and read-only data** (`.text`, `.rodata`) are loaded at their linked addresses.
- **Initialized data** (`.data`) is loaded from the ELF.
- **BSS** is zeroed in `_start` before Rust executes, so all `static` items in safe Rust see their declared initial values (zero for BSS-resident statics).
- **Stack** grows downward from `__stack_top`. Nothing enforces that it does not grow into `.bss` — stack overflow is undefined behaviour in v1. Guard pages arrive with MMU setup.

### What `_start` does, line-by-line

```asm
.section .text.boot, "ax"
.global _start
_start:
    /* (1) K3-12: mask DAIF before anything else. */
    msr     daifset, #0xf

    /* (2) EL drop per ADR-0024. Read CurrentEL; mask bits[3:2]. */
    mrs     x0, CurrentEL
    and     x0, x0, #(3 << 2)
    cmp     x0, #(2 << 2)
    b.eq    el2_to_el1                // EL2 → drop to EL1
    cmp     x0, #(1 << 2)
    b.eq    post_eret                 // already at EL1 → skip drop
halt_unsupported_el:                  // EL3 (or anything else) → halt
    wfe
    b       halt_unsupported_el

el2_to_el1:
    mov     x0, #(1 << 31)            // HCR_EL2.RW = 1 (EL1 = aarch64); E2H/TGE = 0 (non-VHE)
    msr     hcr_el2, x0
    mov     x0, #0x3c5                // SPSR_EL2 = EL1h | DAIF masked
    msr     spsr_el2, x0
    adrp    x0, post_eret
    add     x0, x0, :lo12:post_eret
    msr     elr_el2, x0
    eret

post_eret:
    /* (3) Conventional setup. From here on, EL is guaranteed = 1. */
    adrp    x0, __stack_top           // page-aligned base of the symbol
    add     x0, x0, :lo12:__stack_top // add the low 12 bits
    mov     sp, x0                    // set SP

    mov     x0, #0x300000             // CPACR_EL1.FPEN = 0b11
    msr     cpacr_el1, x0
    isb

    adrp    x0, __bss_start
    add     x0, x0, :lo12:__bss_start
    adrp    x1, __bss_end
    add     x1, x1, :lo12:__bss_end
0:  cmp     x0, x1
    b.hs    1f
    str     xzr, [x0], #8
    b       0b

1:  bl      kernel_entry              // hand off to Rust
2:  wfe                               // defensive halt if we return
    b       2b
```

`adrp + add` with `:lo12:` is the standard aarch64 idiom for "address of symbol" — PC-relative, handles any static layout the linker picks. `str xzr, [x0], #8` stores the zero register with post-increment. `eret` consumes `SPSR_EL2`'s mode + DAIF + register state and `ELR_EL2`'s target address: after the instruction the CPU runs at EL1 with DAIF still masked (the K3-12 mask propagates via `SPSR_EL2`'s DAIF bits, so no second `msr daifset` is needed at `post_eret`). The full safety argument lives in [`UNSAFE-2026-0017`](../audits/unsafe-log.md).

### Linker script responsibilities

[`bsp-qemu-virt/linker.ld`](../../bsp-qemu-virt/linker.ld) pins the above memory map:

- `ENTRY(_start)` — the ELF's `e_entry` is set to `_start`'s address.
- `MEMORY` — a single `RAM` region: `ORIGIN = 0x40080000, LENGTH = 128M`.
- `.text` starts with `KEEP(*(.text.boot))`, guaranteeing `_start` is at `0x40080000`.
- `.bss` is 8-byte aligned at both ends so the BSS-zero loop can step by 8.
- A 64 KiB stack region is reserved after `.bss`; `__stack_top` names its high end.
- `/DISCARD/` drops `.comment`, `.note.*`, `.eh_frame*`, and `.gcc_except_table*` — unwinding tables are dead weight under [`panic=abort`](../standards/error-handling.md).

### Panic path

When `kernel_entry`, the scheduler, or any later kernel code panics, control reaches the BSP's `#[panic_handler]` function. In Phase 4c, that handler:

1. Reconstructs the `Pl011Uart` (the original instance may not be reachable from the panic context).
2. Writes a short marker (`"\n!! tyrne panic !!\n"`).
3. Writes the panic message using `FmtWriter` adapted onto the `Console`.
4. Halts in a `spin_loop` that never returns.

This is the minimum useful panic reporting. Future revisions will add core id, register state, and a backtrace — each requires additional infrastructure that is not in v1.

## Invariants

Properties the boot flow maintains. These are the claims a reader can rely on and a test can exercise.

- **Entry is deterministic.** `_start` always runs the same sequence of instructions on the same input.
- **Interrupts are masked from the very first instruction.** K3-12: `MSR DAIFSet, #0xf` is the literal first instruction at `_start`. The mask carries through the EL drop via `SPSR_EL2`'s DAIF bits, so it is still in effect at `kernel_entry`. Tasks unmask explicitly via `Cpu::restore_irq_state(IrqState(0))` when they need interrupts.
- **`kernel_entry` runs at EL1 unconditionally.** Per [ADR-0024](../decisions/0024-el-drop-policy.md): if the BSP is delivered at EL2, `_start`'s drop sequence transitions to non-VHE EL1; if delivered at EL1, the drop is a no-op; if delivered at EL3 (no v1 hardware target does), `_start` halts loudly. T-009's `UNSAFE-2026-0016` runtime check inside `QemuVirtCpu::new` is the post-condition that pins this.
- **The stack is set before any Rust code runs.** No Rust code executes with an undefined `SP`.
- **BSS is zero when Rust sees it.** All `static` items in safe Rust have their declared initial values.
- **`kernel_entry` never runs more than once.** There is only one boot CPU in v1; it calls `kernel_entry` once.
- **`kernel_entry` never returns to the asm stub.** It is `-> !`; a return would be a bug and is defensively halted by the stub.
- **Hardware MMIO addresses are hardcoded.** No runtime discovery. BSP-specific; justified because `virt` is a fixed platform.
- **`panic=abort`, not unwind.** No unwinding tables in the binary; panics halt.

## Trade-offs

- **EL drop is `boot.s`-side, not kernel-side.** [ADR-0024 Option A](../decisions/0024-el-drop-policy.md) — the kernel reasons about exactly one EL (EL1, non-VHE) and `boot.s` does the work of getting there. The alternative (multi-EL kernel code) was rejected because the maintenance tax compounds across every later HAL impl. The cost is ~30 lines of asm in `_start`.
- **DTB ignored.** Convenient now; will need explicit parsing when the first board with runtime topology (Pi 4) lands.
- **Stack is a fixed 64 KiB with no guard page.** Overflow is UB. Good enough for v1; per-task stacks with guards come with the scheduler.
- **`_start` is hand-written assembly.** Every BSP will have its own. A shared-boot library would force premature commonality; we accept the duplication to keep each BSP's boot transparent.
- **Hardcoded UART base.** `0x0900_0000` is QEMU `virt` specific. Each BSP carries its own constants; the trade is deliberate (see [P6 — HAL separation](../standards/architectural-principles.md#p6--hal-separation)).

## Open questions

- **EL3 → EL2 → EL1 chain.** v1 hardware targets do not boot at EL3; if a future BSP requires it, a follow-up task adds the EL3→EL2 transition on top of the existing EL2→EL1 logic per ADR-0024 §Open questions.
- **DTB parsing and `BootInfo`.** The kernel's typed boot-info contract, probably introduced with Pi 4 support.
- **Multi-core start.** PSCI `CPU_ON` for secondary cores.
- ~~**High-half kernel migration.**~~ **Resolved (T-022 / ADR-0033, 2026-05-30)** — the kernel now runs in `TTBR1_EL1` and `TTBR0_EL1` is freed for per-task userspace (see §"High-half migration" above). v1 keeps the whole high-half RAM window `PXN = 0` (RWX-equivalent); per-section W^X hardening (a distinct `PXN = 1` physmap) is deferred to **ADR-0034**.
- **Guard-page stacks.** With the MMU now active (T-016), guard-page stacks become reachable — pending a follow-on B-phase task that remaps a stack region's bottom page as invalid.
- **Measured boot / attestation.** Hardware-dependent; deferred per [ADR-0012](../decisions/0012-boot-flow-qemu-virt.md).

## References

- [ADR-0012: Boot flow and memory layout for `bsp-qemu-virt`](../decisions/0012-boot-flow-qemu-virt.md).
- [ADR-0024: EL drop to EL1 policy](../decisions/0024-el-drop-policy.md).
- [ADR-0004: Target platforms](../decisions/0004-target-platforms.md).
- [ADR-0006: Workspace layout](../decisions/0006-workspace-layout.md).
- [`hal.md`](hal.md) — the HAL traits the BSP implements.
- [`overview.md`](overview.md) — three-layer architecture.
- [`docs/guides/run-under-qemu.md`](../guides/run-under-qemu.md) — how to actually run the kernel.
- QEMU `virt` machine documentation — https://qemu.readthedocs.io/en/latest/system/arm/virt.html
- ARM *Architecture Reference Manual* (ARMv8-A) — `adrp` / `ERET` / EL semantics.
- PL011 UART documentation — for the console implementation.
