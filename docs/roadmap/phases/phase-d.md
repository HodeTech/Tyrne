# Phase D — Raspberry Pi 4 (first real hardware)

**Exit bar:** `bsp-pi4` boots on a real Pi 4 at feature parity with `bsp-qemu-virt` — all of Phase A / B / C features work on hardware.

**Scope:** A second BSP (`bsp-pi4`) with its own reset, UART, timer, GIC-400, MMU setup; a DTB parser (`tyrne-dt`) so the kernel learns board topology at runtime; SD-card boot. HAL traits that worked for QEMU continue to work; differences are isolated to the BSP.

**Out of scope:** Pi-specific drivers beyond what the kernel needs to boot (those belong in Phase E's driver model); Wi-Fi (blob-dependent, deferred); multi-core on Pi (may drop in naturally if C was done first).

---

## Milestone D1 — `bsp-pi4` scaffolding

A new BSP crate that compiles for `aarch64-unknown-none` and provides a minimal reset path. No HAL impls yet; just the shell.

### Sub-breakdown

1. **ADR-0042 — Pi 4 boot flow.** Load address under Pi firmware (`kernel_address` in `config.txt`); Pi firmware's initial CPU mode; what `config.txt` settings Tyrne expects.
2. **New crate** `bsp-pi4/` with its own `Cargo.toml`, `build.rs`, `linker.ld`, `boot.s`, `main.rs`, `console.rs` — mirroring `bsp-qemu-virt` structure.
3. **Pi firmware interaction** — `config.txt` documentation and the expected load / entry addresses.
4. **Placeholder main** that just spins in `wfe`; no console yet (D3 adds that).

### Acceptance criteria

- ADR-0042 Accepted.
- `cargo build --target aarch64-unknown-none -p tyrne-bsp-pi4` produces an ELF.
- `config.txt` example committed alongside.

---

## Milestone D2 — GIC-400 implementation

Pi 4 uses GIC-400 (a GICv2 implementation). The `IrqController` impl differs from `bsp-qemu-virt`'s GICv2 only in base addresses and board specifics — QEMU virt is GICv2, Pi 4 is GIC-400 (also GICv2); no IOMMU in v1, per ADR-0036.

### Sub-breakdown

1. **ADR-0043 — GIC-400 register layout.** Distributor / CPU-interface base addresses on BCM2711; register offsets used; which features are used vs. ignored.
2. **`IrqController` impl** in `bsp-pi4/src/irq.rs`.
3. **Tests** — host-side register layout; the real verification is D8 on hardware.

### Acceptance criteria

- `IrqController` trait is implemented for Pi 4.
- Implementation compiles and passes host-side layout tests.

---

## Milestone D3 — Pi 4 PL011 UART

Pi 4 has both a mini-UART and a PL011 (UART0). We use the PL011 for diagnostic output, with the board-specific baud-rate init that QEMU skipped.

### Sub-breakdown

1. **ADR-0044 — Pi 4 console choice.** PL011 vs. mini-UART; which pins; what baud rate; whether GPIO pin-muxing is part of the BSP or out of scope.
2. **PL011 init sequence** — baud-rate register programming (QEMU's PL011 is pre-initialized; Pi's is not).
3. **`Console` impl** in `bsp-pi4/src/console.rs` using the same trait as `bsp-qemu-virt` with the Pi-specific init.
4. **Tests** — host-side: none meaningful (hardware behaviour); D7 exercises it on real hardware.

### Acceptance criteria

- ADR-0044 Accepted.
- `Console` impl compiles; the first real-hardware smoke will validate it.

---

## Milestone D4 — ARM generic timer on Pi 4

The generic timer works like on QEMU; the difference is the frequency (from `CNTFRQ_EL0`) and any Pi-specific interrupt routing.

### Sub-breakdown

1. **`Timer` impl** in `bsp-pi4/src/timer.rs`, reading `CNTFRQ_EL0` for frequency.
2. **Interrupt-line number** for the timer IRQ on Pi 4 (PPI, line number per BCM2711).
3. **Tests** — parity with `bsp-qemu-virt` where possible.

### Acceptance criteria

- `Timer` impl compiles; frequency reporting is correct when tested on hardware (D7 / D8 validation).

---

## Milestone D5 — MMU on Pi 4

MMU activation on Pi 4. Memory layout is different (RAM at `0x0000_0000` on Pi vs. `0x4000_0000` on QEMU); peripherals at high addresses.

### Sub-breakdown

1. **ADR-0045 — Pi 4 memory layout.** Kernel load address; peripheral window (`0xFE00_0000` class on BCM2711); identity vs. high-half choices here.
2. **`Mmu` impl** — inherits VMSAv8 from QEMU's impl; differences in the linker script and the MMIO mapping tables.
3. **Cache maintenance** — Pi 4 specifics (cache lines, I/D separation, which invalidate sequences are necessary).
4. **Tests** — B2's test suite applied to Pi 4.

### Acceptance criteria

- ADR-0045 Accepted.
- Kernel runs with the MMU on on Pi 4.

---

## Milestone D6 — DTB parser (`tyrne-dt`)

A userspace-agnostic library crate that parses a flattened device tree into a typed structure. Used by the BSP at boot to read what the firmware told it about the machine.

### Sub-breakdown

1. **ADR-0046 — DTB parsing scope.** Full FDT spec support vs. a minimal read-only subset; zero-copy vs. owned parsing; allocation strategy (probably `no_std + alloc` with an arena).
2. **New crate** `tyrne-dt/` — separate from `tyrne-hal` so BSPs opt in.
3. **Parser API** — `DeviceTree::from_bytes(ptr) -> Result<DeviceTree, Error>`; iterators over nodes; property lookup.
4. **Pi 4 integration** — `kernel_entry` parses the DTB passed in `x0` and emits a `BootInfo` struct.
5. **Host tests** — parse known fixtures (QEMU-generated DTB, Pi 4 DTB samples).

### Acceptance criteria

- ADR-0046 Accepted.
- `tyrne-dt` parses a real DTB into typed records.
- `bsp-pi4` uses it at boot; the kernel's `BootInfo` contains at least memory-map and UART-address entries read from the DTB.

---

## Milestone D7 — SD-card boot

The kernel image, along with firmware, `config.txt`, and any boot files, is placed on an SD card; the Pi 4 boots from that card.

### Sub-breakdown

1. **Image packaging** — a script in `tools/` that produces an `sdcard/` directory (or a `.img` file) ready to be written with `dd`.
2. **First real-hardware boot** — runs the D3 console output; the maintainer sees the kernel greeting on a USB-UART cable.
3. **Guide** — `docs/guides/boot-pi4.md` walking through building, writing to SD, connecting UART, booting.

### Acceptance criteria

- Kernel prints its greeting on Pi 4 hardware via the PL011 UART.
- Guide is reproducible.

---

## Milestone D8 — QEMU parity on Pi 4

All Phase A / B / (C if done) features work on Pi 4 as they do on QEMU virt.

### Sub-breakdown

1. **Run the two-task IPC demo** (A6) on Pi 4.
2. **Run the first userspace "hello"** (B6) on Pi 4.
3. **If Phase C is done:** preemption and multi-core IPC on Pi 4.
4. **Business review.**

### Acceptance criteria

- A6 / B6 (and C5 if applicable) produce the expected traces on real Pi 4 hardware.
- Review records any hardware-specific learnings for future BSPs.

### Phase D closure

Business review; the phase is the most significant in terms of validating that "portable code" claim. Phase E (driver model) follows.

---

## ADR ledger for Phase D

| ADR | Purpose | Expected state | Note |
|-----|---------|----------------|------|
| ADR-0042 | Pi 4 boot flow | D1 | renumbered 2026-05-22, was ADR-0032 (collided with the live Accepted ADR-0032 endpoint-rollback-and-cancel-recv; Phase D shifted above Phase C's new ceiling) |
| ADR-0043 | GIC-400 register layout | D2 | renumbered 2026-05-22, was ADR-0033 (reserved by phase-b.md §B5 ledger for the kernel high-half migration) |
| ADR-0044 | Pi 4 console choice (PL011 vs. mini-UART) | D3 | renumbered 2026-05-22, was ADR-0034 (reserved by phase-b.md §B5 ledger for kernel-image section permissions) |
| _(none)_ | D4 — ARM generic timer on Pi 4 | D4 | implementation-only milestone; the generic-timer behaviour and the `Timer` trait are already settled by ADR-0010, so D4 requires no new ADR. The ledger jumps D3 → D5 for this reason. |
| ADR-0045 | Pi 4 memory layout | D5 | renumbered 2026-05-22, was ADR-0035 (collided with the live Accepted ADR-0035 physical-memory-manager) |
| ADR-0046 | DTB parsing scope | D6 | renumbered 2026-05-22, was ADR-0036 (avoids the ADR-0036 supersession slot reserved for the GICv2/no-IOMMU decision) |

Numbers are tentative; final numbers are assigned when the ADR is actually written, per [ADR-0013](../../decisions/0013-roadmap-and-planning.md).

## Open questions carried into Phase D

- Whether we target Pi 4 rev 1.4 specifically or accept a range.
- USB-to-TTL cable model the guide assumes (community standards).

## Resolved

- **SD-image composition including the Pi's closed-source firmware blobs.** Resolved per [ADR-0004](../../decisions/0004-target-platforms.md): closed-source blobs that sit *below* the kernel (e.g., the VC4 stage-0 firmware on Pi 4) are out of our blob-policy scope. The SD image may therefore include them when that is the only way to boot the hardware.

---

## Review-derived work items (2026-07-15 full-repository review)

The 2026-07-15 full-repository review turned up a cluster of aarch64 hardware-correctness findings in `hal/` and `bsp-qemu-virt/` that are, without exception, **silent on QEMU `virt`** — the emulator either doesn't model the trapping/timing/register behaviour precisely enough to expose them, or the current single-task/single-core demo workload never exercises the code path that would. None of them have caused an observed failure to date. All of them are the kind of gap that turns into a boot hang, a silent data leak across an address-space or privilege boundary, or a hard-to-diagnose corruption the first time the same code runs against real GIC-400/PL011/MMU silicon on a Pi 4 — several are explicitly inherited wholesale by `bsp-pi4` per Milestone D5's "inherits VMSAv8 from QEMU's impl" and Milestone D2's "differs from `bsp-qemu-virt`'s GICv2 only in base addresses and board specifics." They are grouped below into three epics and must be resolved as part of Phase D hardware bring-up, not deferred past it. A **Polish & excellence** subsection follows with the review's non-defect quality findings routed to this phase.

### Epic 1 — Privilege-boundary register hygiene

EL2→EL1 drop and EL0/EL1 trap-frame handling that omit or under-specify register scrubbing. QEMU's emulated core never faults on an unset CPTR_EL2 and never surfaces FP/SIMD state corruption across a trap in the current single-task demo; real silicon will not be as forgiving, and Phase C's preemption/multi-task work (validated on Pi 4 in Milestone D8) is exactly the workload that would first expose a leak here.

- **[🟠 HIGH]** `ContextSwitch::init_user_context`'s trait-level contract omits the security-critical register-scrub obligation that ADR-0037 identifies as HIGH severity.
  - Location: `hal/src/context_switch.rs:84-121`
  - Action: Add an explicit bullet to `init_user_context`'s `# Safety` section (or a new normative `# Implementor contract` subsection, since this is an obligation on implementations, not callers) stating that implementations must scrub every EL0-readable register not part of the explicit `(user_entry, user_sp)` hand-off — GPRs, SIMD/FP registers, and FPCR/FPSR/TPIDR_EL0/TPIDRRO_EL0 — before dropping to EL0, so no EL1 kernel state (pointers, stack addresses, capability data) is disclosed to userspace. Today this fact is recoverable only by archaeology through ADR-0037's revision history and the BSP's unsafe-log entry; it needs to be durable and discoverable in the one contract every future BSP author (starting with whoever writes `bsp-pi4`'s context-switch code) is expected to read.
  - Gates: Milestone D1 (`bsp-pi4` scaffolding mirrors `bsp-qemu-virt`'s context-switch structure) and Milestone D8 (preemption/multi-task validation on hardware).

- **[🟠 HIGH]** CPTR_EL2 is never initialized before the EL2→EL1 drop, unlike HCR_EL2/SPSR_EL2/ELR_EL2, which are all explicitly pinned.
  - Location: `bsp-qemu-virt/src/boot.s:64-98 (el2_to_el1)`
  - Action: Add an explicit CPTR_EL2 write inside `el2_to_el1`, before the `eret` — e.g. `mov x0, #0x33ff` / `msr cptr_el2, x0` — clearing TFP so FP/SIMD is never trapped to EL2 (RES1-safe for the pre-SVE register format). Document the choice the same way HCR_EL2/SPSR_EL2 are documented, and add an ADR-0024 addendum or audit-log note since this sits in the same UNSAFE-2026-0017-audited block.
  - Gates: Milestone D1 — `bsp-pi4/src/boot.s` is scaffolded by mirroring `bsp-qemu-virt/src/boot.s`; fix this in the source before it is copied into a second BSP.

- **[🟠 HIGH]** The IRQ trap frame never saves/restores FP/SIMD register state, despite CPACR_EL1 explicitly enabling untrapped FP/SIMD and the codebase's own boot comment admitting the compiler emits NEON in ordinary (non-float) code.
  - Location: `bsp-qemu-virt/src/exceptions.rs:47-112 (TrapFrame)`, `bsp-qemu-virt/src/vectors.s:115-160 (tyrne_irq_curr_el_trampoline)`; root cause enabled at `bsp-qemu-virt/src/boot.s:109-116`.
  - Action: Pick one of: (a) add `-C target-feature=-neon,-fp-armv8` (or equivalent) to the `aarch64-unknown-none` rustflags in `.cargo/config.toml` so "no FP/SIMD anywhere in the kernel image" becomes a compiler-enforced invariant, matching the project's existing preference for compile-time guards (cf. the `size_of::<TrapFrame>() == 192` assert); (b) extend `TrapFrame`/the IRQ trampoline to save/restore the caller-saved FP/SIMD registers (V0-V7, V16-V31, FPSR, FPCR); or (c) set `CPACR_EL1.FPEN = 0` for kernel-mode execution so an inadvertent FP/SIMD access traps loudly instead of silently corrupting state, consistent with the fail-loud philosophy already used in `panic_entry`. Record the choice as an ADR/audit-log entry.
  - Gates: Milestone D8 (preemption/multi-task IPC on hardware is the first workload likely to interleave FP/SIMD-touching code across an IRQ).

- **[🟠 HIGH]** Exception trampolines never save/restore/scrub the SIMD-FP register file (V0-V7, V16-V31, FPCR/FPSR) across an EL1 trap, despite FP/SIMD being live-usable at EL0/EL1.
  - Location: `bsp-qemu-virt/src/vectors.s:127-160 (tyrne_irq_curr_el_trampoline)` and `bsp-qemu-virt/src/vectors.s:195-253 (tyrne_sync_trampoline)`.
  - Action: Either (a) save/restore the full (or at minimum caller-saved: V0-V7, V16-V31) SIMD/FP register file plus FPCR/FPSR in both trampolines; or (b) scrub V0-V31/FPCR/FPSR on every `tyrne_sync_trampoline` restore path (not just the one-shot `enter_el0`) to close the confidentiality gap even if (a) is deferred for cost reasons; or (c) structurally prevent the hazard via a codegen restriction (`-C target-feature=-neon` plus a reviewed escape hatch for the boot-time zero-init the project already relies on). At minimum, add a `# Safety`/audit-log note next to both trampolines recording this as a known, unaudited gap — today neither UNSAFE-2026-0020 nor UNSAFE-2026-0029 mentions FP/SIMD register scope.
  - Gates: Milestone D8, same rationale as above; overlaps directly with the IRQ trap-frame finding.

- **[⚪ LOW]** `context_switch_asm` saves/restores d8-d15 (FP data) but never FPCR/FPSR (FP control/status).
  - Location: `bsp-qemu-virt/src/cpu.rs:372-423 (context_switch_asm)`; cf. `Aarch64TaskContext` at `cpu.rs:298-329`.
  - Action: Either add `fpcr`/`fpsr` fields to `Aarch64TaskContext` and save/restore them alongside d8-d15 (cheap: two more registers), or explicitly document in the struct's doc comment that kernel-level cooperative tasks are assumed never to modify FPCR/FPSR, so the omission is a documented invariant rather than an unexamined gap.
  - Gates: Milestone D1/D8 — same register-hygiene sweep as the two HIGH trampoline findings above; fix together.

### Epic 2 — MMU & TLB hardware correctness

Descriptor construction, activation ordering, and walk/translate logic in the shared VMSAv8 code that `bsp-pi4`'s `Mmu` impl will inherit near-verbatim per Milestone D5. QEMU's TLB/MMU emulation tolerates orderings and omissions that real Cortex-A72 silicon may not.

- **[🟠 HIGH]** `Mmu::activate` installs the new TTBR0 before invalidating stale TLB entries — break-before-make is inverted.
  - Location: `bsp-qemu-virt/src/mmu.rs:227-243 (QemuVirtMmu::activate)`
  - Action: Reorder to flush-then-install: `dsb ishst; tlbi vmalle1; dsb ish` first (draining/invalidating while TTBR0 still names the outgoing context), then `msr ttbr0_el1, {ttbr0}` plus the EPD0 clear and a closing `isb`. Additionally, document in this function's SAFETY comment (or the `Mmu::activate` trait contract) whether the caller is required to mask IRQ/FIQ around the call — the corrected ordering removes the CPU's-own-lookup race but not a genuinely concurrent access from another exception context landing mid-sequence. This flush-then-install sequence is the **authoritative** ordering; a low-severity companion barrier-order item in [Phase C](phase-c.md#review-derived-work-items-2026-07-15-full-repository-review)'s SMP MMU epic points here and must be kept in sync.
  - Gates: Milestone D5 directly — `bsp-pi4`'s `Mmu` impl "inherits VMSAv8 from QEMU's impl," so this bug would otherwise ship into the second BSP unmodified. Fix before D5's implementation work begins.

- **[🟡 MEDIUM]** Descriptor validity/table/AF bit constants are module-private in HAL, forcing a byte-for-byte duplicate copy in the BSP walker.
  - Location: `hal/src/mmu/vmsav8.rs:221,229-233` (cf. `bsp-qemu-virt/src/mmu.rs:63-65,366,371,380,533,549,592,604`)
  - Action: Make `DESC_VALID_BIT`, `DESC_TABLE_OR_PAGE_BIT`, and `DESC_AF_BIT` (and, for consistency, `DESC_NG_BIT`/`DESC_PXN_BIT`/`DESC_UXN_BIT`) `pub const` in `hal/src/mmu/vmsav8.rs`, matching the treatment already given to the OA masks. Delete the duplicate declarations in the BSP and import the HAL constants instead, so there is exactly one textual definition of every VMSAv8 descriptor-field bit position in the codebase — important before a second BSP (`bsp-pi4`) needs its own copy of the same walker.
  - Gates: Milestone D5.

- **[🟡 MEDIUM]** `flags_to_descriptor_bits` has no defense-in-depth guard against `USER | WRITE | EXECUTE` (a user-writable-and-executable mapping).
  - Location: `hal/src/mmu/vmsav8.rs:342-350` (cf. `hal/src/mmu/mod.rs:559-564`)
  - Action: Extend the documented `InvalidFlags` contract (and whichever layer enforces it — currently the BSP's `map()`) to also reject `USER | WRITE | EXECUTE`, or at minimum add a `debug_assert!` in `flags_to_descriptor_bits` flagging the combination, closing the gap before any syscall surface can reach it. Kernel-only WRITE+EXECUTE (the existing, ADR-0034-blessed bootstrap RWX block mapping) must remain unaffected — scope the new check to the USER-tagged case specifically.
  - Gates: Milestone D5.

- **[⚪ LOW]** `DescriptorBits` has fully public, unvalidated fields; the silent-truncation hazard documented for `pa` is undocumented and untested for `attr_idx`/`ap`/`sh`.
  - Location: `hal/src/mmu/vmsav8.rs:260-275 (struct)` and `:479-490 (page_descriptor masking)`
  - Action: Either (a) make `DescriptorBits`'s fields non-`pub` with `flags_to_descriptor_bits` as the sole safe constructor, or (b) document the truncation hazard on the struct itself and add a pinning test analogous to `block_descriptor_drops_low_bits_for_unaligned_pa` for out-of-range `attr_idx`/`ap`/`sh`.
  - Gates: Milestone D5.

- **[⚪ LOW]** `mmu_bootstrap` Step 3's SCTLR-enable asm block is marked `options(nomem)`, contradicting the project's own stated rationale for omitting `nomem` on barrier sequences.
  - Location: `bsp-qemu-virt/src/mmu_bootstrap.rs:246-261 (mmu_bootstrap, Step 3 asm block, options at line 258)`
  - Action: Drop `nomem` from Step 3's asm options (matching Step 2's already-justified pattern), or, if `nomem` is intentional, add a comment explaining why reordering across the SCTLR-enable point is safe here and why that reasoning differs from Step 2's. Treat as unverified-in-codegen (no cargo/objdump available for the static review) but apply the conservative fix per CLAUDE.md's "when in doubt, the conservative option wins."
  - Gates: Milestone D5.

- **[⚪ LOW]** `docs/audits/unsafe-log.md` and `mmu.rs`'s own module doc describe an obsolete (pre-T-022) instruction sequence for `QemuVirtMmu::activate`.
  - Location: `bsp-qemu-virt/src/mmu.rs:9-14 (module doc)`; `docs/audits/unsafe-log.md:473-501 (UNSAFE-2026-0023 entry)`
  - Action: Append a dated Amendment to UNSAFE-2026-0023 documenting `activate()`'s EPD0-clear addition (new MRS/AND/MSR TCR_EL1 + DSB ISHST instructions) and its `options(nostack)` (no `nomem`) choice with rationale; update `mmu.rs:9-14`'s summary to match the current sequence. Do this alongside the break-before-make reorder above so the audit log describes the corrected sequence, not another stale one.
  - Gates: Milestone D5.

- **[⚪ LOW]** `Mmu::translate` cannot resolve any VA inside a block-mapped region — it returns `MmuError::BlockMapped` instead of decoding the block.
  - Location: `bsp-qemu-virt/src/mmu.rs:326-388 (translate)`, specifically the `walk_or_alloc_table(..., unmap=true)` reuse at lines 348-357.
  - Action: Extend `translate()` to detect a block descriptor at L1/L2 and decode it directly using the appropriate `BLOCK_OA_MASK` (already exported from `vmsav8.rs`) plus the VA's sub-block offset, calling the existing `descriptor_bits_to_flags` (bit-position-compatible with both block and page descriptors). At minimum, document the current block-mapped-region limitation prominently in `translate()`'s doc comment.
  - Gates: Milestone D5.

- **[⚪ LOW]** `unmap`'s L3-leaf validation checks only the Valid bit, not the reserved/page bit that `translate()` checks.
  - Location: `bsp-qemu-virt/src/mmu.rs:529-544 (walk_and_install_leaf, unmap branch)`
  - Action: Add the same `(existing & DESC_TABLE_OR_PAGE_BIT) == 0 -> NotMapped` check to the unmap branch of `walk_and_install_leaf` for defense-in-depth and consistency with `translate()`'s stricter validation.
  - Gates: Milestone D5.

### Epic 3 — Boot & GIC on real silicon

The remaining HAL/BSP hardware findings: GIC-400 register-programming completeness, boot-time sanity checks that are compiled out in release, and console/build hygiene. Milestone D2's GIC-400 impl and Milestone D1/D7's boot path inherit these patterns directly.

- **[🟡 MEDIUM]** `high_half_alias` (`main.rs:800-808`)'s boot-time sanity checks are `debug_assert!`s that release builds silently drop — both the migration-target validity check and the >4 GiB kernel-image PA-mask guard. *(The review filed the migration-target check and the >4 GiB PA-mask guard as two items against the same function; merged here.)*
  - Location: `bsp-qemu-virt/src/main.rs:800-808 (fn high_half_alias)` (cross-ref `Cargo.toml:59-70` `overflow-checks`, `tools/smoke.sh:12-56`)
  - Action: The workspace already treats `overflow-checks` as a security property that must not be dropped for performance; apply the same reasoning to this function's checks — either (a) promote both `debug_assert!`s to unconditional `assert!`s (the function runs exactly twice per boot — negligible cost), or (b) set `debug-assertions = true` in `[profile.release]` for the workspace, consistent with the `overflow-checks` precedent already set two lines above it in the same file.
  - Gates: Milestone D1/D7 — this guards the target of an unconditional `br` mid-boot; Pi 4's boot flow (ADR-0042) must not carry a release-mode-silent version of the same hazard. Also Milestone D5 (its ADR-0045 Pi 4 memory layout): Pi 4's RAM base (`0x0000_0000`) and peripheral window differ from QEMU's, and the 4 GiB PA-mask assumption behind the PA-guard is flagged in `boot.md` as a "forward limit" needing re-validation on real hardware.

- **[🟡 MEDIUM]** `GICD_IPRIORITYR` is never programmed for IRQ IDs 0-31 (SGIs/PPIs, including the timer's own PPI 27) during `init()`.
  - Location: `bsp-qemu-virt/src/gic.rs:188-210 (Step 4, priority loop starts at FIRST_SPI = 32)`
  - Action: Add a small separate loop (or four `write_distributor` calls) in `init()` that programs `GICD_IPRIORITYR0-7` (byte offsets 0..31) to `DEFAULT_PRIORITY_BYTE` as well, before the distributor is enabled — 8 extra word writes at boot, closing the gap between the doc comment's stated intent and actual behavior.
  - Gates: Milestone D2 directly — Pi 4's GIC-400 `IrqController` differs from QEMU's GICv2 impl "only in base addresses and board specifics," so this omission would otherwise carry straight into `bsp-pi4/src/irq.rs`.

- **[🟡 MEDIUM]** Unbounded, interrupt-masked UART TX-FIFO poll turns `console_write` into a system-wide stall vector.
  - Location: `bsp-qemu-virt/src/console.rs:78-84` (root cause), compounded by the masked-IRQ invariant documented at `bsp-qemu-virt/src/syscall.rs:118-119`.
  - Action: Bound the poll — add an iteration/time cap in `write_bytes` that drops remaining bytes once exceeded (consistent with ADR-0007's own "best-effort... dropping bytes... is preferable to deadlocking" philosophy) — and/or enforce a hard per-syscall byte cap before the chunk loop in `sys_console_write`. Currently Medium rather than High because `console_write` is debug-gated out of release builds and v1 ships one demo task, but this becomes reachable the moment a second task gets a console capability or a future ADR lifts the debug gate — and Pi 4's PL011 (Milestone D3) has different, board-specific FIFO drain timing than QEMU's pre-initialized model, so the stall duration is not validated by QEMU testing alone.
  - Gates: Milestone D3.

- **[🟡 MEDIUM]** The `perf-bench` feature has zero automated build/run coverage; existing tooling structurally cannot validate it.
  - Location: `bsp-qemu-virt/Cargo.toml:24` (feature def); `.github/workflows/ci.yml:140-143` (kernel-build job); `tools/smoke.sh:110`.
  - Action: Add a `kernel-build-perf-bench` CI step/job that runs `cargo +$NIGHTLY_PIN build --target aarch64-unknown-none -p tyrne-bsp-qemu-virt --features perf-bench` (and the matching clippy invocation) so a breaking change to the bench module goes red. Separately, give `tools/smoke.sh` a `--features <list>` passthrough and either an alternate `--done-marker` string or auto-detection of perf-bench builds.
  - Gates: Milestone D8 (hardware-parity validation tooling should not have a blind spot the CI already has).

- **[⚪ LOW]** `init()`'s SPI priority/target loop bound trusts the hardware-reported `GICD_TYPER` line count unclamped, unlike `enable()`/`disable()`'s hard-asserted `GIC_MAX_IRQ` bound.
  - Location: `bsp-qemu-virt/src/gic.rs:160-167 (irq_count derivation)` vs. `gic.rs:317-322 / 342-348 (enable/disable asserts against GIC_MAX_IRQ = 1020)`
  - Action: Clamp `irq_count = irq_count.min(GIC_MAX_IRQ as usize)` right after deriving it from `GICD_TYPER`, so `init()` and `enable`/`disable` share the same upper bound. This matters more on real GIC-400 than on QEMU's emulated distributor, where `GICD_TYPER`'s reported line count is whatever the emulator author chose rather than a value that can genuinely vary by SoC revision.
  - Gates: Milestone D2.

- **[⚪ LOW]** `TIMER_IRQ_ID` is duplicated between `exceptions.rs` and `cpu.rs` with no compile-time cross-check.
  - Location: `bsp-qemu-virt/src/exceptions.rs:32-36 (TIMER_IRQ_ID: u32 = 27)` and `bsp-qemu-virt/src/cpu.rs:49 (TIMER_IRQ: IrqNumber = IrqNumber(27))`
  - Action: Either define the constant once (e.g. in `gic.rs` or a small shared `irq_ids` module) and import it from both sites, or add `const _: () = assert!(TIMER_IRQ_ID == crate::cpu::TIMER_IRQ.0);` next to one of the two definitions. Pi 4's PPI routing for the generic timer (Milestone D4) is a different line number in principle, so this pattern needs to not silently drift a second time when `bsp-pi4` defines its own copy.
  - Gates: Milestone D2/D4.

- **[⚪ LOW]** GICv2 `acknowledge()`/`end_of_interrupt()` mask away GICC_IAR's CPU-ID subfield (bits [12:10]), which GICv2 requires be echoed back verbatim in GICC_EOIR for SGIs. *(The review filed this against two slightly different line ranges in `gic.rs` as separate items; they are the same underlying gap, merged here.)*
  - Location: `bsp-qemu-virt/src/gic.rs:364-376` / `:369-370` (`acknowledge`) and `:378-385` (`end_of_interrupt`); `hal/src/irq_controller.rs:13 (IrqNumber)`.
  - Action: Zero-cost today; no action needed for v1 (single-core, timer-only — no SGI/IPI traffic). When the future SGI/IPI ADR is written, preserve the CPU-ID subfield explicitly: either widen `IrqNumber` (or add a parallel raw-acknowledge type / a dedicated `acknowledge_sgi()` path) to carry the untruncated GICC_IAR value through to `end_of_interrupt`, or scope a GIC-driver-private raw-EOI path for the SGI ID range. Leave a forward-note next to the relevant mask constant now so it is discoverable without re-deriving it later.
  - Note: the review cites this as gated by "ADR-0043, roadmap C4" for the eventual SGI/IPI ADR — a number that now collides with Phase D's own ADR-0043 (GIC-400 register layout, per the ADR ledger below, renumbered 2026-05-22). Flag as an ADR-numbering item to reconcile when Phase C's SGI/IPI ADR is actually drafted (also tracked under Phase B.2 Track B.2-2's ADR-ledger cascade-renumbering finding).
  - Gates: none directly in Phase D (single-core Pi 4 has no SGI/IPI traffic yet); tracked here so it is not lost before Phase C's SGI/IPI work is ported to Pi 4 in a later phase.

- **[⚪ LOW]** Reported per-op perf-bench numbers never disclose build profile, even though the default toolchain path is `dev` (opt-level=1), not `release`.
  - Location: `bsp-qemu-virt/src/perf_bench.rs:367-374 (ctx-switch banner)`, `:390-397 (IPC banner)`, `:531-536 (EL0 banner)`.
  - Action: Have `build.rs` forward Cargo's own `PROFILE`/`OPT_LEVEL` env vars via `println!("cargo:rustc-env=TYRNE_BUILD_PROFILE={}", std::env::var("PROFILE").unwrap())`, then have `perf_bench.rs`'s three banners include `env!("TYRNE_BUILD_PROFILE")` (or at minimum `cfg!(debug_assertions)`) in the printed line, mirroring `perf-harness.sh`'s existing convention. This matters for Phase D because Pi 4 vs. QEMU timing comparisons (Milestone D8) are meaningless if the profile isn't recorded alongside the number.
  - Gates: Milestone D8.

- **[⚪ LOW]** `build.rs`'s userland-image existence check is unconditional even though it serves only the non-bench (production demo) path.
  - Location: `bsp-qemu-virt/build.rs:28-35`; `bsp-qemu-virt/src/main.rs:375`.
  - Action: Either (a) gate `USERSPACE_IMAGE` (and related constants, if perf-bench-dead too) behind `#[cfg(not(feature = "perf-bench"))]` in `main.rs` and make `build.rs`'s assert conditional on `CARGO_FEATURE_PERF_BENCH` being unset; or (b) if the coupling is intentional, say so explicitly in a doc comment.
  - Gates: Milestone D1/D7 (bsp-pi4's own build.rs will need the same decision made, not re-derived from scratch).

- **[⚫ INFO]** `boot.s` comment overstates that the BSS-zero loop involves NEON instructions.
  - Location: `bsp-qemu-virt/src/boot.s:109-116`.
  - Action: Tighten the comment to say "...before the first NEON instruction the compiler may emit in Rust code (`kernel_entry` and beyond)" and drop the "BSS zeroing" clause, since the explicit hand-written loop never uses NEON.
  - Gates: Milestone D1 (boot.s is mirrored into `bsp-pi4`; fix the comment at the source).

### Polish & excellence

Non-defect quality findings from the 2026-07-15 full-repository review, condensed into grouped bullets. None are dropped from the source list of 28.

- **HAL trait-contract precision** (documentation-only, zero runtime cost, all in `hal/`): state explicitly that `IrqController` performs no capability/authorization checking of its own (matches CLAUDE.md's no-ambient-authority rule); spell out that `IrqState` captures the full D/A/I/F mask, not just IRQ, ahead of a future RISC-V/PLIC HAL implementer who won't have aarch64's DAIF vocabulary to fall back on; add an explicit non-aliasing bullet to `ContextSwitch::context_switch`'s `# Safety` section; clarify `Console`'s "avoid blocking indefinitely" language against expected UART FIFO-full spin loops (directly relevant to Pi 4's PL011, which is flakier than QEMU's pre-initialized model); give BSPs a shared IRQ-range validation policy instead of each choosing independently (QEMU's GICv2 panics on out-of-range; nothing stops `bsp-pi4` from silently no-op'ing the same case); cross-reference ADR-0037's DAIF-at-EL0 masking directly from `vectors.s`; consider echoing FPCR/FPSR/NZCV-adjacent state explicitly in the `# Safety`/audit-log entries for the two live trampolines (would have caught the Epic 1 FP/SIMD gap by construction).

- **Constants, duplication, and type-safety hygiene**: mark `DescriptorBits` `#[non_exhaustive]` (consistent with `MmuError`'s own treatment in the same crate); derive `TABLE_NLA_MASK` from `PAGE_OA_MASK_L3` instead of retyping the identical literal; use the workspace's `VirtAddr` newtype for `Pl011Uart::base` instead of raw `usize`, making the "must be mapped for kernel access" contract compiler-checked — directly useful when `bsp-pi4/src/console.rs` (Milestone D3) writes its own PL011 driver against the same trait; add `publish = false` to `bsp-qemu-virt/Cargo.toml` (and other bare-metal-only crates, including the forthcoming `bsp-pi4`); unify or cross-reference the two independent warm-up constants `WARMUP`/`EL0_WARMUP` (both = 256) with a one-line "kept equal by convention, not coupling" note; extend the compile-time layout-guard pattern (`const _: () = assert!(...)`) already used for `TrapFrame`/`SyscallTrapFrame`/`Aarch64TaskContext` to the four bootstrap page-table frame declarations, which are the one remaining ABI-shaped fact without one.

- **Fail-stop verification and defense-in-depth polish**: add a `debug_assert!` second line of defense in `descriptor_bits_to_flags` for the caller-validated V/page/AF bits; promote the migration-target check to an unconditional `assert!` (echoes the Epic 3 finding above — same fix, same file); teach `translate()` to decode block descriptors (echoes the Epic 2 finding above); give `panic_entry` a small `ESR_EL1.EC` decode table (cheap, no allocation, already anticipated as a deferred follow-up in `unsafe-log.md:406` — pays for itself the first time a Phase C/D bring-up bug lands in this exact panic path); state explicitly that `CNTVCT_EL0` reads carry no ISB barrier and that the skew is bounded and negligible at N=50,000 round-trips; add a host-side decode assertion for `BENCH_EL0_IMAGE`'s hand-assembled bytes (a `const fn` compile-time assertion matching each 4-byte word against its documented encoding, in the style of the existing `N_*_ROUNDTRIPS` non-zero guard).

- **Boot-path and audit-log bookkeeping**: run a dedicated audit-log sweep for the T-022 `kernel_entry`/`kernel_main_high` split — UNSAFE-2026-0028 is confirmed stale in its header fields, and 0001/0010 still say `kernel_entry` for what are now largely `kernel_main_high`-resident operations, a pattern that has recurred at least three times and is more efficiently fixed in one sweep; expand the crate-level doc comment to cover the T-028 EL0 task, since roughly half of `kernel_main_high`'s current logic (loader, AS/Task cap resolution, `add_user_task`, `USER_TASK_TABLE`) exists to run a real EL0 program and the module doc gives no signal of that; record the actual T-028-era boot dispatch order in `docs/architecture/boot.md` or the sched module doc, since it is an emergent, non-local result of three independently-reasonable pieces of code; convert the ASCII "Memory map at boot" diagram in `boot.md` to an inline Mermaid diagram (per [documentation-style.md](../../standards/documentation-style.md)'s Mermaid-only rule), reflecting the T-022/ADR-0033 link-high/load-low reality and **replacing** — not duplicating — the ASCII version (two sections of the same document currently disagree on the level of detail; also tracked under Phase B.2 Track B.2-2's `boot.md`-diagram finding); add a small script/lint that cross-checks `unsafe-log.md` entries against the asm/unsafe blocks they claim to cover (a grep-based CI check flagging an asm `!` line-count change with no corresponding new Amendment date) to preserve the audit trail's credibility going forward, including through Phase D's own new `bsp-pi4` unsafe blocks.

- **Code-size and test-quality polish** (run-once boot paths, negligible runtime impact): the BSS-zero loop could use `DC ZVA` or a NEON pair-store for boot-time code-size/perf polish; `enter_el0`'s manual 61-instruction GPR/vector-register zeroing sweep could shrink via a small loop; fix the break-before-make ordering in `activate()` before it gets a second real caller (echoes the Epic 2 HIGH finding — flagged again here because `bsp-pi4`'s `Mmu` impl is precisely that "second real caller"); extract `syscall_entry`'s frame-to-struct marshalling into small, pure, host-testable functions (e.g. `args_from_words`/`write_resume_words`) so a register-order transposition is caught at `cargo test` time rather than by reading a QEMU trace — the highest-value item in this group given it covers the widest untrusted-input surface in the system.

---

Covers all 25 routed review findings (23 after merging 2 near-duplicate pairs — the GICv2 CPU-ID/EOI items and the `high_half_alias` release-`debug_assert!` items) + 28 polish items routed to this phase.
