# Boot flow

The QEMU virt BSP takes a low physical ELF entry to a shared high-half EL1 kernel, builds a trusted EL0 image and its caller bindings, then starts cooperative scheduling. This chapter follows the actual reset assembly, linker layout and Rust setup rather than a future portable boot protocol. The EL1 IPC demo and EL0 hello interleave; the one-round completion path ends in Task A's busy-spin.

> **Last verified against:** 2026-10-13; source da18ed5c2a2d8b3d61f82337a9da021d05d73451; owner [T-046](../analysis/tasks/phase-b2/T-046-docs-subsystem-chapters-refresh.md).

## Context

[ADR-0012](../decisions/0012-boot-flow-qemu-virt.md) records the initial board layout; [ADR-0024](../decisions/0024-el-drop-policy.md) establishes EL1 entry. [ADR-0027](../decisions/0027-kernel-virtual-memory-layout.md) adds translation; [ADR-0033](../decisions/0033-kernel-high-half-migration.md) and its dated riders define high-half migration. The current image pipeline follows [ADR-0039](../decisions/0039-userland-build-pipeline.md). The BSP composes kernel mechanisms directly; there is no `BootInfo` value or portable `kernel_main(boot_info)` handoff.

## Design

### Stages

1. **Loader/reset.** QEMU loads the ELF at its physical load addresses and enters `_start_phys`. The literal first instruction masks DAIF. EL2 drops to non-VHE EL1h; EL1 continues; unsupported ELs halt.
2. **Assembly initialization.** Set SP, enable FP/SIMD through CPACR_EL1, zero BSS, then branch to Rust `kernel_entry` with MMU off.
3. **Translation migration.** Emit the early low-address UART marker, install low vectors, enable identity translation, build/activate TTBR1 and rebase PC/SP/VBAR high. `kernel_main_high` disables/nulls TTBR0 and flushes low translations.
4. **Privileged setup.** Construct persistent high-address console/CPU, capture the boot timestamp, initialize PMM and wrap the bootstrap root as an AddressSpace. Load the real embedded hello image into its own AS. Configure GIC, unmask DAIF.I and report timer readiness; no deadline is armed by the default demo.
5. **EL0 task bring-up.** Resolve loaded AS capability, create Task capability, resolve the Task, seed its separate table with DebugConsole/CONSOLE_WRITE at the asserted hello handle, then publish that table and the empty fail-closed table before registration/dispatch. Register EL1 B, EL1 A, EL0 hello and separate idle fallback; publish the scheduler.
6. **Dispatch.** Start with B. When hello is selected, activate its TTBR0, restore initial context and ERET to EL0. Hello attempts console output and exits through two SVCs in both profiles. The remaining EL1 exchange completes; Task A prints completion/elapsed and spins. Exit does not reclaim the old Task/AS/table/frames.

### High-half migration (T-022 / ADR-0033)

The whole image is linked uniformly at `KBASE = 0xFFFF_FFFF_4008_0000`, loaded at `0x4008_0000`, with one `0xFFFF_FFFF_0000_0000` offset for image and direct map. Before migration, PC-relative references resolve to low runtime aliases. After migration, function/static references resolve high. The BSP compile-time assertion pins its offset to the HAL constant.

Low bootstrap tables use four frames; high L0/L1 use two more and share the low layout's L2 tables. The BSP enables TTBR1 walks, rebases SP and VBAR, then branches to the high function. Once PC/SP/vectors are high, it writes TTBR0=0, sets EPD0 and invalidates. Per-task activation later installs a low root, clears EPD0 and flushes ASID-0 translations. TTBR1 remains privileged and shared. The EL1 demo/idle root has USER-clear mappings; hello gets separate USER pages.

The direct-map offset/migration mask are limited to physical addresses below 4 GiB. A future BSP with larger RAM/high peripherals must revisit them. Initial kernel RAM is RWX-equivalent; per-section permissions remain reserved as ADR-0034 in the [ADR index](../decisions/README.md).

### Boot-time sequence

This sequence expands the [overview](overview.md#boot-flow) with table publication and keeps EL1/EL0 interleaving explicit.

```mermaid
sequenceDiagram
    participant R as Reset assembly
    participant B as BSP Rust setup
    participant S as Cooperative scheduler
    participant U as EL0 hello
    R->>R: mask DAIF, drop EL2 if needed, set SP
    R->>R: enable FP/SIMD, zero BSS
    R->>B: kernel_entry
    B->>B: low UART, vectors, identity MMU
    B->>B: TTBR1 on; PC/SP/VBAR high; TTBR0 off
    B->>B: high console/CPU, timestamp, PMM, bootstrap AS
    B->>B: load hello; initialize GIC and timer support
    B->>B: resolve AS, mint/resolve Task, seed caller table
    B->>B: publish USER_TASK_TABLE and FAILCLOSED_TABLE
    B->>S: register B/A/hello/idle; publish; start
    S->>U: activate user TTBR0, restore context, ERET
    U->>B: console attempt SVC; exit SVC
    B->>S: terminate current without reclamation
    S->>S: finish EL1 reply; Task A prints and spins
```

[Fresh debug/release evidence](../analysis/reports/2026-10-13-t045-architecture-verification.md) binds to unchanged executable source `4ad0b3d8a9d43310fcd937013131bffadcc803d7`. Both profiles show EL0 entry at `0x800000`, task exit and completion; only debug prints the greeting. Manual exception inspection finds two SVCs and no other exception events. Smoke gates markers/fault rejection, not the exact count. Release BadSyscallNumber is source-derived, not a printed return status. Neither run exercises timer delivery or idle/WFI.

### Memory map at boot

The linker defines physical load addresses and high VMAs separately; dynamic section sizes are intentionally not rendered as fixed addresses.

| Region | Physical / load address | Virtual address / reservation |
|--------|-------------------------|-------------------------------|
| Configured RAM | `[0x4000_0000, 0x4800_0000)` | Direct-map alias at offset + PA after migration. |
| Pre-image reserved RAM | `[0x4000_0000, 0x4008_0000)` | Excluded from PMM allocation. |
| Kernel `.text` start / reset | `0x4008_0000` | `KBASE = 0xFFFF_FFFF_4008_0000`; ELF entry remains low. |
| Vectors | Inside text, 2-KiB aligned | Low VBAR before migration, high VBAR after. |
| `.rodata`, `.data`, `.bss` | Following text at linker-derived LMAs | Corresponding VMA minus/plus the same offset. |
| Bootstrap tables | Six 4-KiB frames inside `.bss` | `__boot_pt_start..__boot_pt_end`, 24 KiB; no separate output `.boot_pt` section. |
| Bootstrap stack | 64 KiB after BSS | 16-byte-aligned `__stack_top`; rebase before disabling TTBR0. |
| Task kernel stacks | Static 4-KiB buffers in the kernel image | Separate A/B/idle/hello stacks; hello's stack is SP_EL1. |
| Hello image / user stack | Fresh PMM frames, not fixed contiguous PAs | Current one-page image at VA `0x800000`, stack `0x801000..0x802000`, SP `0x802000`. |
| MMIO blocks | GIC `0x0800_0000..0x0900_0000`; UART block `0x0900_0000..0x0920_0000` | Same direct-map offset; hardware UART begins at `0x0900_0000`. |

The PMM reserves firmware/pre-image bytes plus the kernel image/BSS/tables/bootstrap stack. Current capture-specific counts are in the report, not constants. Stack guard pages and measured IRQ-rich high-water headroom are not implemented guarantees.

### What `_start` does, line-by-line

[`boot.s`](../../bsp-qemu-virt/src/boot.s) is the actual assembly source:

| Order | Operation and purpose |
|-------|-----------------------|
| 1 | `msr daifset, #0xf`, before vector installation or Rust. |
| 2 | Read CurrentEL; EL2 writes HCR_EL2 with RW=1/E2H=TGE=0, SPSR_EL2=`0x3c5`, ELR_EL2=post_eret, then ERET. EL1 branches directly; unsupported ELs WFE-loop. |
| 3 | PC-relative address of `__stack_top` becomes SP before entering Rust. |
| 4 | Set CPACR_EL1.FPEN=3 and ISB, allowing compiler-generated FP/SIMD. |
| 5 | Zero `[__bss_start, __bss_end)` using 8-byte stores. |
| 6 | Branch to `kernel_entry`; defensive WFE loop if it returns. |

The EL drop preserves masked DAIF through SPSR. PC-relative link/load uniformity supplies correct pre-MMU addresses; it does not validate arbitrary firmware inputs. Unsupported EL halt has no pre-Rust console diagnosis. Initial EL0 register scrub happens later in the separate entry trampoline, not this BSS loop.

### Linker script responsibilities

[`linker.ld`](../../bsp-qemu-virt/linker.ld) uses `ENTRY(_start_phys)`, high section addresses and low `AT()` LMAs. `.text.boot` is retained first; `.text.vectors` is retained/aligned to 2048. BSS boundaries are 8-byte aligned, table frames 4096-byte aligned, and the bootstrap stack top 16-byte aligned. The six table frames are BSS reservations; no memory-discovery or generic BootInfo map is produced. Unwinding/comment/note sections are discarded under the bare-metal abort profile.

### Panic path

The BSP panic handler chooses the low/high UART alias based on the current stack regime, reconstructs the console, writes `!! tyrne panic !!` and formatted PanicInfo, then spins. There is no general register dump, backtrace, reset or task-supervisor recovery. Specific exception panic paths print their syndrome/frame fields before this handler. If bad translation also removes the vector/console mapping, diagnostic installation cannot guarantee recoverability.

## Invariants

- DAIF is masked at the first reset instruction; EL2-to-EL1 ERET carries that mask.
- SP/BSS/FP setup precede Rust; supported reset entries reach EL1 before privileged Rust setup.
- PC/SP/VBAR move high before TTBR0 is disabled; user activation installs the selected low AS before ERET.
- Published empty fail-closed and real caller tables precede `add_user_task`/`start`.
- User entry/stack and caller bindings come from the trusted loader/registration path; no arbitrary-image boot protocol is exposed.

## Trade-offs

Uniform high linking simplifies aliases and constrains the usable physical window. BSP-owned composition keeps boot concrete but is not yet portable machine discovery. Early UART aids diagnosis while remaining privileged and potentially unbounded polling. Fixed task stacks and fail-stop one-shot setup simplify bring-up without providing guard pages, full rollback or resource recovery.

## Open questions

[Phase C](../roadmap/phases/phase-c.md) owns the atomic caller-binding and SP_EL1 high-water gates before richer scheduling. [Phase D](../roadmap/phases/phase-d.md) owns hardware BSP/translation/trap-state work. [Phase E](../roadmap/phases/phase-e.md) owns untrusted loading/service authority and lifecycle; verified boot and firmware contracts require deployment decisions. Idle/timer infrastructure still needs a real arming workload for its recorded IRQ-dispatch evidence gap.

## References

- [BSP Rust setup and panic handler](../../bsp-qemu-virt/src/main.rs), [reset assembly](../../bsp-qemu-virt/src/boot.s), [linker](../../bsp-qemu-virt/linker.ld).
- [Memory](memory-management.md), [exceptions](exceptions.md), [HAL](hal.md), [scheduler](scheduler.md), [task loader](task-loader.md).
- [ADR-0035 PMM](../decisions/0035-physical-memory-manager.md), [ADR-0037 EL0 entry](../decisions/0037-el0-entry-context.md), [ADR-0038 user access](../decisions/0038-mmu-translate-and-user-access.md).
- [Unsafe audit](../audits/unsafe-log.md), [QEMU guide](../guides/run-under-qemu.md).
