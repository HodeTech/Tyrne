# T-022 — High-half kernel mapping: boot-time migration to `TTBR1_EL1` + per-task `TTBR0` swap

- **Phase:** B
- **Milestone:** B6 — First userspace "hello" (this is B6's **gating prerequisite**: making the kernel reachable from every task's active translation so a real EL0 task's `SVC` vector fetch + the EL1 handler translate — the [ADR-0033](../../../decisions/0033-kernel-high-half-migration.md) high-half migration; per [phase-b §B6 opening sequence](../../../roadmap/phases/phase-b.md#b6-opening-sequence--prerequisites))
- **Status:** Draft
- **Created:** 2026-05-29
- **Author:** @cemililik (+ Claude Opus 4.8 agent)
- **Dependencies:** [ADR-0033](../../../decisions/0033-kernel-high-half-migration.md) — must be `Accepted` before code lands (settles the boot-time high-half §Simulation + the link-high/load-low + `KERNEL_VA_OFFSET` discipline); [ADR-0027](../../../decisions/0027-kernel-virtual-memory-layout.md) (the reserved `TTBR1`/`EPD1` + the byte-stable high-half `TCR` fields this consumes); [T-016](T-016-mmu-activation.md) (the `mmu_bootstrap` + `QemuVirtMmu` + `vmsav8` encoders this extends); [T-018](T-018-address-space-kernel-object.md) (the `activate` differ-path that goes live).
- **Informs:** Closes [ADR-0033 §Dependency chain steps 1–6](../../../decisions/0033-kernel-high-half-migration.md#dependency-chain) and discharges every [ADR-0033 §Simulation](../../../decisions/0033-kernel-high-half-migration.md#simulation) row (the row-to-verification mapping is recorded in this task's review-history row on completion). Unblocks B6's subsequent tasks — the EL0-ready `Task` context + enter-EL0/`ERET` path (T-021 carry-forward gate #2), `task_create_from_image`, the per-task `console_write` window + gate #1/#3, `tyrne-user` + `userland/hello`. Lifts the still-pending `Pending QEMU smoke verification` riders on [UNSAFE-2026-0023 / 0024](../../../audits/unsafe-log.md) (T-022's per-task `TTBR0` swap is the first post-bootstrap address-space-switching caller).
- **ADRs required:** [ADR-0033](../../../decisions/0033-kernel-high-half-migration.md), [ADR-0027](../../../decisions/0027-kernel-virtual-memory-layout.md). Introduces **new** `UNSAFE-YYYY-NNNN` audit entries (the absolute-jump migration trampoline asm; the per-task `TTBR0_EL1` swap; the `KERNEL_VA_OFFSET` PA↔VA helper deref) + **Amendments** to UNSAFE-2026-0022 / 0023 / 0024 per [unsafe-policy](../../../standards/unsafe-policy.md).

---

## User story

As the kernel, I want to run in the high half (`TTBR1_EL1`) — present in every address space's high VA range — so that `TTBR0_EL1` is free for per-task userspace mappings and a real EL0 task's `SVC` vector fetch + the EL1 handler + copy-user all translate, **without** the kernel ever being present in (or leakable from) the user-active translation regime.

## Context

[ADR-0033](../../../decisions/0033-kernel-high-half-migration.md) settles the decision and the boot-time transition shape; this task implements it. It is **B6's gating prerequisite** ([phase-b §B6](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello)) and is deliberately landed **alone and staged**, before the EL0-entry / `task_create_from_image` / `userland` tasks build on the settled high-half regime ([CLAUDE.md #6](../../../../CLAUDE.md)).

The migration switches the running kernel's own PC/SP/`VBAR` translation regime from identity/low (`TTBR0`) to high (`TTBR1`) **at boot** (inside / right after [`mmu_bootstrap`](../../../../bsp-qemu-virt/src/mmu_bootstrap.rs), before any `StaticCell` is written and before the GIC/timer is live), where `DAIF` is masked and no low-VA pointer survives — the framing that removes the live-kernel bricking hazards (ADR-0033 §Decision outcome). It is the highest-stakes code in the project so far; the ADR's §Simulation was hardened against two adversarial verification passes.

## Acceptance criteria

- [ ] **Link-high/load-low.** The kernel is linked at `KBASE = 0xFFFF_FFFF_8008_0000` (LMA low via linker `AT`); a low-linked, position-independent `.idmap`-style early section holds `boot.s`, the high-half table builder, and the migration trampoline so they resolve `VA == PA` while the MMU is off / identity-only. (Closes the early-`adrp`-computes-high brick ADR-0033 §Consequences names.)
- [ ] **`KERNEL_VA_OFFSET` PA↔VA helper** replaces every `addr_of!`-as-PA site (`mmu_bootstrap` `TTBR` programming, the `__boot_pt_l0` re-read in `kernel_entry`, [`crate::mm::phys_frame_kernel_ptr`](../../../../kernel/src/mm/mod.rs)'s identity body). PA-computation host-tested.
- [ ] **High-half `TTBR1` tables** built per [ADR-0033 §"High-half layout"](../../../decisions/0033-kernel-high-half-migration.md): kernel image (`PXN = 0`/`UXN = 1`), kernel physmap/direct-map (`PXN = 1`), device MMIO — with the vector table + all handler/branch targets inside the `PXN = 0` image window. `vmsav8` high-half encoders host-tested.
- [ ] **EPD1-cleared `TCR_EL1` constant** in [`tyrne_hal::mmu::vmsav8`](../../../../hal/src/mmu/vmsav8.rs): bit 23 = 0, every `TTBR0`-governing field byte-identical to `TCR_EL1_VALUE`; host-tested.
- [ ] **The boot-time migration** runs the ADR-0033 §Simulation rows 0–3: build `TTBR1` (`ISB` after the `TTBR1` write, `DSB ISH` for the table memory) → `EPD1` `1→0` + `ISB` → trampoline (`VBAR`-high + `ISB`, `SP`-high, `LDR`/`BR` to the `PXN = 0` high continuation, `DAIF` masked) → `TTBR0`-null + `EPD0 = 1` + `ISB` + `TLBI VMALLE1` + `DSB ISH` + `ISB`. A new `tyrne: high-half active` boot marker prints after the jump.
- [ ] **Per-task `TTBR0_EL1` swap goes live:** [`QemuVirtMmu::activate`](../../../../bsp-qemu-virt/src/mmu.rs) drives the real per-task swap with per-task ASID values (`A1 = 0`, ASID in `TTBR0_EL1.ASID`); the [T-018](T-018-address-space-kernel-object.md) `activate` differ-path that short-circuits in v1 now fires. Host test pins the differ path with distinct ASes.
- [ ] **Audit:** new entries (trampoline asm; per-task `TTBR0` swap; `KERNEL_VA_OFFSET` deref) + Amendments to UNSAFE-2026-0022 / 0023 / 0024; the 0023/0024 `Pending QEMU smoke verification` riders lifted.
- [ ] **All gates green** incl. `cargo +nightly miri test --workspace --exclude tyrne-bsp-qemu-virt`. **QEMU smoke:** full demo to `tyrne: all tasks complete` with the new `tyrne: high-half active` line; `-d int,unimp,guest_errors` shows **zero new Translation/Permission fault classes** (the migration is fault-clean) — the row-4 abort gate.

## Out of scope

- The EL0-ready `Task` context register file (`ELR_EL1`/`SPSR_EL1`/`SP_EL0` + per-task `SP_EL1`) + the enter-EL0/`ERET` path — the next B6 task (T-021 carry-forward gate #2).
- `task_create_from_image` (`LoadedImage` → runnable `CapHandle{CapObject::Task(...)}`) — Phase B6.
- The per-task `console_write` window + per-page user-VA→kernel-VA translation (T-021 gate #1) and the `SYSCALL_STUB_TABLE` → current-task-table swap (gate #3) — Phase B6.
- `tyrne-user` + `userland/hello` + the build pipeline — Phase B6.
- Per-section kernel-image permissions (`.text` RX / `.rodata` R / `.data` RW) — [ADR-0034](../../../decisions/0027-kernel-virtual-memory-layout.md) placeholder; v1 high-half image is RWX-equivalent like the identity map it replaces.

## Approach

_(Settled at the ADR level — see [ADR-0033 §Simulation](../../../decisions/0033-kernel-high-half-migration.md#simulation) + §Dependency chain; the detailed approach + the §Simulation row-to-verification mapping are filled when the task moves to `In Progress`.)_ The migration trampoline is hand-asm (the compiler cannot be guaranteed to emit position-independent, no-`adrp`-to-high code for arbitrary Rust); the low-linked early section keeps `boot.s` + the table builder resolving low; the high-half tables reuse the host-tested `vmsav8` encoders. **Fallback:** if the link-split / position-independence discipline proves intractable on the LLVM/lld toolchain, ADR-0033 §Consequences documents the Option 2 interim (map the kernel into every `TTBR0`) — escalate to the maintainer before switching.

## Definition of done

All acceptance criteria checked; gates green (incl. Miri); audit-log entries + Amendments added; `current.md` updated; **security-relevant — flagged for explicit security review** per [CLAUDE.md #1](../../../../CLAUDE.md) (this changes the kernel's own translation regime and the kernel/user isolation boundary — the highest-stakes change in the project so far).
