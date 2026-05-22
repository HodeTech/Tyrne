# C7-bsp — board support package (master review, commit 288ddb2)

## Summary

The QEMU `virt` aarch64 BSP is the most `unsafe`/MMIO/assembly-dense area of
Tyrne, and it is in unusually good shape for a pre-alpha kernel. I read all 12
track files in full plus ADR-0012 / ADR-0024 / ADR-0027, `boot.md`,
`exceptions.md`, the `bsp-boot-checklist`, the `unsafe-policy`,
`architectural-principles`, `error-handling` standards, the five HAL traits the
BSP implements (`Cpu`, `ContextSwitch`, `Timer`, `Mmu`, `IrqController`,
`Console`), the `vmsav8` encoders, and cross-checked every audit ID against
`docs/audits/unsafe-log.md`.

**Verdict: SHIP with minor follow-ups. No Blockers, no Majors.** The boot
sequence is correct end-to-end against the ADRs; the BSS-zero/stack/EL-drop
chain matches the checklist exactly; the MMU bootstrap descriptor math is
correct (I independently recomputed every L0/L1/L2 index and PA range); the GIC
init/EOI sequence is spec-conformant; the vector table is correctly 2 KiB
aligned with the right 16-entry layout; the context-switch stub is
`#[unsafe(naked)]` with a compile-time size guard and saves d8–d15; and **all 27
`unsafe` audit IDs referenced in BSP source resolve to entries in the audit
log**. Every `unsafe` block I inspected carries a conforming `SAFETY:` comment
(invariants + rejected alternatives + audit ref) and every `unsafe fn` has a
`# Safety` section — `unsafe-policy` §1/§2 are satisfied throughout.

Findings are concentrated in (a) one documentation inconsistency (ADR-0012 still
says "GICv3" while the entire implementation is GICv2), (b) a small number of
defence-in-depth / consistency nits in the asm and MMIO paths, and (c) a
maintainability observation about `main.rs` at 1308 lines. The single most
useful structural improvement is decomposing `kernel_entry`, but the code's own
rationale for keeping it linear is defensible and I have filed it as Minor, not
Major.

Severity counts: **Blocker 0 · Major 0 · Minor 6 · Nit 7 · Praise 6.**

## Findings

### Blocker

None.

### Major

None.

### Minor

---

**C7-001 — ADR-0012 documents "GICv3" but the BSP implements GICv2 end-to-end**
`docs/decisions/0012-boot-flow-qemu-virt.md:24` (and the cross-track doc surface)

ADR-0012 §Decision drivers line 24 reads "…`GICv3` distributor at `0x0800_0000`…".
Every piece of the actual implementation is **GIC v2**: `gic.rs:1` ("GIC v2
driver"), the `QemuVirtGic` struct, the `GICC_IAR`/`GICC_EOIR` CPU-interface
register model (a v2 memory-mapped CPU interface — GICv3 uses system-register
`ICC_*` access), the CPU-interface base `0x0801_0000` (`gic.rs:35`), and
`exceptions.md` which says GICv2 throughout. The single-write `GICC_EOIR`
"priority-drop + deactivate in one" behaviour the code relies on
(`gic.rs:378-384`) is the GICv2 model.

Why it matters: ADR-0012 is the *normative source* the `add-bsp` skill points a
future BSP author to (`add-bsp/SKILL.md:17,211`), and `gic.rs:32` cites
`hw/arm/virt.c` as the source-of-truth for the base. QEMU `virt` actually
exposes a GICv2 by default and a GICv3 only with `-machine gic-version=3`; the
code is correct for the default, but the ADR mislabels the controller the
project committed to. A reader reconciling ADR-0012 against `gic.rs` will hit a
contradiction on the very first peripheral.

Suggested fix: correct ADR-0012 line 24 to `GICv2` (append-only — ADRs are
immutable per CLAUDE.md rule #5, so this is a §Revision-notes / superseding-ADR
correction, not an in-place edit unless it qualifies as the `unsafe-policy`-style
mechanical-terminology exemption; treat as a documentation ADR follow-up). The
BSP source needs no change. (Routed to the doc-accuracy pass.)

---

**C7-002 — `MAIR_EL1` device attribute is `0x00` (device-nGnRnE) by *omission*,
relying on the implicit `Attr2..7 = 0`; the named index is correct but the value
is never asserted to be reachable for the GIC/UART blocks**
`hal/src/mmu/vmsav8.rs:63` + `bsp-qemu-virt/src/mmu_bootstrap.rs:141-150`

`MAIR_EL1_VALUE = 0x0000_0000_0000_FF00` encodes `Attr0 = 0x00` (device-nGnRnE)
and `Attr1 = 0xFF` (normal). The device blocks in `mmu_bootstrap` are encoded
with `flags_to_descriptor_bits(DEVICE|WRITE|GLOBAL)` → `attr_idx = ATTR_IDX_DEVICE
= 0` (`vmsav8.rs:46,259-263`). This is *correct*. The Minor concern is that the
device attribute byte `0x00` is indistinguishable from "unset MAIR slot" — there
is no positive bit pattern to assert. The host test
`mair_value_attr0_device_attr1_normal_others_zero` (`vmsav8.rs:382-389`) checks
`MAIR & 0xFF == 0x00`, which passes for *any* value whose low byte is zero,
including an all-zero `MAIR` (which would map normal RAM as device too if
`ATTR_IDX_NORMAL` ever regressed to 0).

Why it matters: device-nGnRnE = `0x00` is genuinely the architecture's encoding,
so this is not a bug — but the test cannot distinguish "device attribute is
correctly programmed" from "MAIR is zero". A future regression that zeroed
`Attr1` would not be caught by this assertion alone (the `Attr1 == 0xFF` check
*would* catch it, so coverage is adequate today; the fragility is in the device
half).

Suggested fix: no source change required. Optionally add a comment at
`vmsav8.rs:46` noting that `0x00` is both the device encoding *and* the
zero-value, so the device-attribute correctness rests on `ATTR_IDX_NORMAL = 1`
selecting the non-zero `Attr1`. (Routed to test-adequacy notes.)

---

**C7-003 — `cpu.rs` `wait_for_interrupt()` uses `options(nostack, nomem)` on
`WFI`, but the surrounding idle loop reads scheduler state immediately after
the wake**
`bsp-qemu-virt/src/cpu.rs:270-277`

`WFI` is annotated `options(nostack, nomem)`. Architecturally `WFI` itself
touches no memory, so `nomem` is *literally* accurate for the instruction. The
subtlety: `nomem` tells the compiler the asm has no memory side effects and
imposes no ordering, so the compiler is free to reorder non-volatile memory
accesses across the `WFI`. In `idle_entry` (`main.rs:428-459`) the very next
operation after `cpu.wait_for_interrupt()` is `yield_now(SCHED.as_mut_ptr(), …)`,
which reads scheduler state. Because the wake condition (an IRQ having fired and
updated some future scheduler flag) is communicated through *volatile* MMIO + an
exception round-trip (which is itself a compiler barrier via the `extern "C"`
`irq_entry` call), there is no actual miscompilation today — v1's `irq_entry` is
ack-and-ignore and touches no scheduler state, so the idle loop observes nothing
through `WFI` that `nomem` could reorder incorrectly.

Why it matters: this is a latent footgun for the *first* preemption/wake hook.
The moment `irq_entry` writes a scheduler flag that idle's post-`WFI` code reads
through a non-volatile path, `nomem` permits the read to be hoisted *before* the
`WFI`. The `cpu.rs:8-17` and `exceptions.md` already flag the wake hook as future
work, so the hazard is real and forward-dated.

Suggested fix: keep `nomem` for now (correct for v1) but add a one-line note at
`cpu.rs:270` that when a scheduler-wake hook lands, `wait_for_interrupt` must
either drop `nomem` or the wake flag must be `Atomic`/volatile. Alternatively
drop `nomem` now (it costs nothing on a once-per-idle path) for defence in
depth, mirroring the deliberate `nomem`-omission discipline already applied in
`mmu.rs:196` and `mmu_bootstrap.rs:213`. (Routed to security + unsafe-audit
passes.)

---

**C7-004 — `Pl011Uart::write_bytes` uses plain `self.base + offset` while every
other MMIO site in the BSP uses `saturating_add`**
`bsp-qemu-virt/src/console.rs:72,76`

`console.rs` computes `(self.base + UARTFR)` and `(self.base + UARTDR)` with
plain `+`. The GIC driver (`gic.rs:259,272,287,299,324,350`) deliberately uses
`saturating_add` for the identical "base + register offset" pattern, and
`main.rs:832` uses `saturating_add` for the stack-top round-up. The offsets here
are tiny compile-time constants (`0x00`, `0x18`) and `base` is a fixed
`0x0900_0000`, so overflow is impossible in practice and a debug-build overflow
panic would never trigger.

Why it matters: pure consistency / defence-in-depth. A reviewer auditing MMIO
arithmetic has to notice that one of the four MMIO modules uses a different
addition idiom. Uniformity reduces the audit surface.

Suggested fix: switch to `self.base.saturating_add(UARTFR)` /
`saturating_add(UARTDR)` to match `gic.rs`, or document in `console.rs` why the
plain add is acceptable here (constant offsets, fixed base). (Routed to
code-style / consistency.)

---

**C7-005 — `main.rs` is 1308 lines with a ~580-line `kernel_entry`; the linear
structure is defended but the static-cell init blocks are mechanically
repetitive and could be helper-extracted without obscuring order**
`bsp-qemu-virt/src/main.rs:707-1289`

`kernel_entry` carries `#[allow(clippy::too_many_lines)]` with a rationale
(`main.rs:703-706`) that splitting into helpers "obscures the order each phase
depends on". I agree with the *spirit* — the boot sequence's linearity is an
auditability feature and the `bsp-boot-checklist` is explicitly order-sensitive.
However, the function interleaves genuine phase logic with a large amount of
mechanical `unsafe { (*CELL.0.get()).write(value) }` boilerplate (e.g.
`main.rs:719-722, 782-784, 847-849, 878-886, 935-954, 1103, 1151-1153,
1205-1212, 1266-1268`). Each is individually justified but collectively they
roughly double the function's length and dilute the phase structure the
`#[allow]` is trying to protect.

Why it matters: the function is the single hardest-to-scan unit in the track.
The repeated `write`/`assume_init_ref` pattern is exactly the kind of thing a
small typed helper (`fn publish<T>(cell: &StaticCell<T>, v: T) -> &T`) would
collapse to one auditable line per cell, *preserving* top-to-bottom order while
removing the boilerplate noise.

Suggested fix: introduce a `StaticCell::publish(&self, value: T) -> &T` (write +
`assume_init_ref` in one `unsafe`, audited under the existing UNSAFE-2026-0001/
0010 entries) and use it for the write-once publish sites. This keeps the linear
phase order intact (the call order is unchanged), removes ~40 lines of
repetition, and concentrates the `unsafe` justification in one place instead of
a dozen. Do **not** extract the *phases* into helpers — the `#[allow]`'s
reasoning is sound there. (Routed to maintainability / refactor.)

---

**C7-006 — Two extern-static declarations of the bootstrap page-table symbols
exist (`main.rs` and `mmu_bootstrap.rs`); the `[u64; 512]` element type is
declared in both, with no single source of truth**
`bsp-qemu-virt/src/main.rs:687` + `bsp-qemu-virt/src/mmu_bootstrap.rs:47-52`

`__boot_pt_l0` is declared `extern "C" { static __boot_pt_l0: [u64; 512]; }` in
both `main.rs:687` (just L0) and `mmu_bootstrap.rs:48` (all four frames). The
linker symbol is just an address; the `[u64; 512]` typing is a Rust-side fiction
chosen so `addr_of!(...).cast::<u64>()` is alignment-clean (documented well at
`mmu_bootstrap.rs:40-46, 89-96`). The two declarations agree today, but nothing
enforces that they stay in sync — if one were changed to `[u64; 1024]` the other
would silently keep `512`, and the `linker.ld` reservation (`linker.ld:66-73`,
four `. = . + 4096` blocks) is a *third* independent encoding of the same "512
u64 per frame" fact.

Why it matters: three independent restatements of the page-table frame size
(`main.rs`, `mmu_bootstrap.rs`, `linker.ld`) with no compile-time cross-check.
The MMU descriptor structs elsewhere in the track have compile-time size guards
(`cpu.rs:326` for `Aarch64TaskContext`, `exceptions.rs:77` for `TrapFrame`); the
bootstrap frames have none.

Suggested fix: declare the four extern statics once in `mmu_bootstrap.rs` and
`pub(crate) use` the L0 symbol from `main.rs` (or expose a
`mmu_bootstrap::boot_pt_l0_addr() -> usize` accessor) so there is one
declaration. Optionally add `const _: () = assert!(ENTRIES_PER_TABLE == 512)`
adjacent to the linker-reservation comment to tie the Rust constant to the
`linker.ld` `4096` choice. (Routed to maintainability + cross-track to linker.)

---

### Nit

**C7-007 — `linker.ld` does not place `.rodata` / `.data` as read-only vs
read-write; the entire image is RWX via the 2 MiB block mapping**
`bsp-qemu-virt/linker.ld:38-44` + `mmu_bootstrap.rs:159`

The RAM blocks are mapped `WRITE | EXECUTE | GLOBAL` (`mmu_bootstrap.rs:159`),
i.e. kernel R/W/X across the whole 128 MiB including `.text` and `.rodata`. This
is explicitly acknowledged and deferred by ADR-0027 §Decision outcome
(ADR-0034 placeholder, `0027:158`). No action needed in v1 — flagging only so
the master review's security pass has the W^X gap on record as a *known,
ADR-tracked* deferral, not an oversight. (Routed to security pass.)

**C7-008 — `idle_entry`/`task_a`/`task_b` re-fetch `CONSOLE`/`CPU` via
`assume_init_ref` multiple times within one function**
`bsp-qemu-virt/src/main.rs:473,508 / 572,625,645`

`task_b` reads `CONSOLE` at `:473` then again at `:508`; `task_a` similarly at
`:572`, `:625`, `:645`. Each is a separate `unsafe` block with its own SAFETY
comment (correct), but the repetition is avoidable by binding once at the top.
Harmless; cosmetic. (Code-style.)

**C7-009 — `console.rs` module doc cites ADR-0007 for the `Console` trait but
the file header is the only place the polling/TX-only contract is stated**
`bsp-qemu-virt/src/console.rs:1-14`

The TX-only, no-RX, no-baud, FIFO-poll contract is documented only in the struct
doc. Fine for v1, but the `add-bsp` skill (`SKILL.md:124-125`) tells future BSP
authors to "follow the existing `Pl011Uart`" — a one-line pointer from the skill
to this contract, or a note that RX is out of scope, would help. (Doc.)

**C7-010 — `exceptions.rs` `TrapFrame._reserved: [u64; 2]` is padding but never
written by the trampoline, so it holds uninitialised stack bytes**
`bsp-qemu-virt/src/exceptions.rs:68-69` + `vectors.s:122`

The trampoline does `sub sp, sp, #192` and writes offsets `0x00..0xB0`; the
`[sp, #0xB0]` reserved slot (`_reserved`) is left as whatever was on the stack.
`irq_entry` never reads it, so this is sound, but a future handler that
`#[derive(Debug)]`-prints the whole `TrapFrame` (the struct derives `Debug`,
`:44`) would emit garbage for `_reserved`. Consider a comment that the field is
deliberately uninitialised, or zero it for clean debug output. (Defence-in-depth
/ doc.)

**C7-011 — `gic.rs` `read_cpu_interface` is defined but only `acknowledge` reads
the CPU interface; `read_distributor` likewise only used by `init`'s TYPER read**
`bsp-qemu-virt/src/gic.rs:286-291`

`read_cpu_interface` (`:286`) is used once (`acknowledge`, `:369`);
`read_distributor` once (`init`'s TYPER, `:165`). Both are appropriately
`unsafe fn` with `# Safety`. No dead code (the module-level `#![allow(dead_code)]`
seen in `mmu.rs` is *not* present here, confirming these are reached). Pure
observation — the helper symmetry (read/write × dist/cpuif) is good design even
though two of the four readers are single-use. (No action.)

**C7-012 — `boot.s` comment says "EL0 cannot happen at reset" but the dispatch
has no explicit EL0 arm; it falls into `halt_unsupported_el`**
`bsp-qemu-virt/src/boot.s:58-62`

Correct behaviour (EL0 at reset is impossible; if it somehow occurred it would
halt loudly, which is the right failure). The comment is accurate. Flagging only
that the `halt_unsupported_el` label semantically covers "EL3 *and* any other
value including the impossible EL0" — the `boot.md:41` and ADR-0024 phrasing
("EL3 or any unexpected value") matches. Consistent. (No action.)

**C7-013 — `Cargo.toml` has no `[lints] workspace = true` comment explaining the
deny-heavy posture relied on by the SAFETY discipline**
`bsp-qemu-virt/Cargo.toml:19-20`

`[lints] workspace = true` is present (good — this is what makes
`clippy::undocumented_unsafe_blocks` / `missing_safety_doc` deny per
`unsafe-policy.md:169-170` apply here). Nit: the entire `unsafe`-audit story
depends on these workspace lints being `deny`; a one-line comment pointing to
the workspace lint table would make the dependency explicit for a reader who
opens only this crate. (Doc.)

### Praise

**C7-P1 — Exemplary `unsafe` discipline.** All 27 audit IDs referenced in BSP
source (`UNSAFE-2026-0001..0027`) resolve to entries in
`docs/audits/unsafe-log.md` — I verified this mechanically. Every `unsafe` block
I read has a SAFETY comment with invariants + rejected alternatives + audit ref
(`unsafe-policy` §1), and every `unsafe fn` (`QemuVirtCpu::new`,
`Pl011Uart::new`, `QemuVirtGic::new`/`init`, `from_existing_root`,
`context_switch`/`init_context`, `mmu_bootstrap`, `walk_and_install_leaf`,
`walk_or_alloc_table`, `irq_entry`, `panic_entry`, `TaskStack::top`,
`StaticCell::as_mut_ptr`) has a `# Safety` section (§2). This is the single
strongest aspect of the track and a model for the rest of the codebase.

**C7-P2 — Context-switch stub is textbook-correct.** `context_switch_asm`
(`cpu.rs:354-405`) is `#[unsafe(naked)]` per `unsafe-policy` §5a / checklist §6,
saves the full AAPCS64 callee set *including d8–d15* (the exact omission the
`add-bsp` skill warns about, `SKILL.md:203`), routes `sp` through the x8 scratch
because `sp` cannot be a store source operand, and is pinned by a compile-time
`assert!(size_of::<Aarch64TaskContext>() == 168)` (`cpu.rs:326`). The byte
offsets in the asm, the doc comment, and the `repr(C)` struct all agree.

**C7-P3 — MMU bootstrap descriptor math is correct and independently
verifiable.** I recomputed every index: L0[0]→L1, L1[0]→L2_low, L1[1]→L2_high;
device blocks `L2_low[64..72]` cover `0x0800_0000..0x0920_0000` (GIC dist idx 64,
GIC CPU-iface idx 64, PL011 idx 72 — all inside the 9-block span); RAM blocks
`L2_high[0..63]` cover `0x4000_0000..0x4800_0000` (128 MiB). The
barrier/invalidate ordering (DSB ISHST → TLBI → DSB ISH → ISB; and the
activate-path TTBR0 → ISB → DSB ISHST → TLBI → DSB ISH → ISB) matches ADR-0027
§Simulation and the Linux `__primary_switch` precedent, with the deliberate
`nomem`-omission to force a memory clobber documented at `mmu_bootstrap.rs:180-191`
and `mmu.rs:181-186`.

**C7-P4 — Vector table layout is spec-conformant.** `vectors.s` is `.balign
2048`, 16 entries × `0x80`, with the live `curr_el_spx` IRQ at `+0x280` correctly
the only non-panic entry for a kernel running `SPSel=1`. The `TrapFrame` is
192-byte SP-aligned with a compile-time size guard (`exceptions.rs:77`) mirroring
the asm `sub sp, sp, #192`, and the GIC ack/EOI contract is honoured exactly:
spurious returns with **no** EOI (`exceptions.rs:176-187`), real IRQs EOI once
(`:228, :238`). This is the GICv2 architecture's required discipline.

**C7-P5 — EL-drop and boot-checklist compliance is complete.** `boot.s` masks
DAIF as the literal first instruction (K3-12, checklist §1a), drops EL2→EL1 with
explicit non-VHE `HCR_EL2 = 1<<31` and `SPSR_EL2 = 0x3c5` (DAIF propagates
through `eret`, so no second mask needed — correctly noted), halts loudly on EL3,
enables `CPACR_EL1.FPEN = 0b11` before any NEON (checklist §2), and zeroes BSS
with 8-byte stores over the 8-byte-aligned range (checklist §5). All MOV
immediates (`0x3c5`, `0x300000`, `1<<31`) are validly encodable as single MOVZ —
I verified. The `UNSAFE-2026-0016` `current_el() == 1` post-condition in
`QemuVirtCpu::new` ties the asm invariant to a Rust-side runtime check.

**C7-P6 — HAL separation (P6) is clean.** Every board-specific address
(`PL011_UART_BASE`, GIC bases, RAM extent, kernel load addr) is a named const in
the BSP; the kernel crate is referenced only through HAL traits and typed kernel
APIs. Assembly is confined to `boot.s` / `vectors.s` / inline `asm!` /
`naked_asm!` exactly where Rust cannot express the semantics (P5), and each asm
stub has a safe-or-`unsafe fn` Rust wrapper. No proprietary blobs (P7). The MMIO
attack surface obeys the device-attribute discipline (DEVICE ⇒ PXN=UXN=1, never
executable — `mmu.rs:224-226` rejects `DEVICE|EXECUTE`).

## Claims register

| Claim | Source `file:line` | How to verify |
|-------|-------------------|---------------|
| Kernel image loads at PA `0x4008_0000` | `main.rs:81`, `linker.ld:21`, ADR-0012:49 | `linker.ld` `MEMORY RAM ORIGIN = 0x40080000`; matches `KERNEL_IMAGE_START`. Objdump `e_entry` of the built ELF == `0x40080000`. ✅ consistent across all three. |
| RAM extent `0x4000_0000..0x4800_0000` (128 MiB) | `main.rs:76-78`, ADR-0027:50 | `PMM_EXTENT_START/END`; RAM block loop maps 64 × 2 MiB = 128 MiB (`mmu_bootstrap.rs:163`). ✅ |
| PL011 UART base `0x0900_0000` | `main.rs:111`, `console.rs:35`, ADR-0012:24 | QEMU `virt` device tree / `hw/arm/virt.c`. L2 idx 72 (`0x0900_0000>>21`) is inside device span 64..72. ✅ |
| GIC distributor `0x0800_0000`, CPU interface `0x0801_0000` | `gic.rs:32,35`, ADR-0011, exceptions.md:102-103 | QEMU `virt` GICv2. Both at L2 idx 64; device span 64..72 covers them. ✅ **but** ADR-0012:24 mislabels as "GICv3" — see C7-001. |
| Device MMIO mapped `0x0800_0000..0x0920_0000` (9 × 2 MiB blocks) | `mmu_bootstrap.rs:132-150`, ADR-0027:51 | `idx = va>>21`; loop `64..(0x0920_0000>>21)=73` ⇒ idx 64..72 inclusive = 9 blocks. Recomputed independently. ✅ |
| Bootstrap page tables: L0→L1, L1[0]→L2_low, L1[1]→L2_high | `mmu_bootstrap.rs:123-130`, `linker.ld:56-62`, ADR-0027:88 | L1[0] covers `0x0`-`0x4000_0000` (MMIO); L1[1] covers `0x4000_0000`-`0x8000_0000` (RAM). VA bits 38:30 = 1 for RAM range ⇒ L1 idx 1. ✅ |
| `.boot_pt` (4 frames, 16 KiB) lives inside `[__bss_start,__bss_end)` so `_start` zeroes it | `linker.ld:46-77`, `boot.s:118-127`, ADR-0027:87 | `__boot_pt_*` between `__bss_start` (`:47`) and `__bss_end` (`:76`); BSS loop runs `__bss_start..__bss_end`. ✅ |
| `__boot_pt_l0` symbol = live L0 root written into `TTBR0_EL1` | `main.rs:687,896`, `mmu_bootstrap.rs:212` | `mmu_bootstrap` writes `ttbr0 = l0 as u64`; `main.rs` reads `addr_of!(__boot_pt_l0)` to wrap the AS. Same symbol. ✅ |
| MAIR `Attr0=device-nGnRnE(0x00)`, `Attr1=normal(0xFF)` | `vmsav8.rs:63`, ADR-0027:53-56 | `MAIR_EL1_VALUE = 0x...FF00`; host test `vmsav8.rs:382-389`. ✅ (caveat C7-002 re device-byte aliasing). |
| TCR `T0SZ=16, EPD1=1, IPS=0b010, TG0=4K` | `vmsav8.rs:134-164`, ADR-0027:57 | Field decomposition + host test `tcr_value_carries_...` (`:392-409`). ✅ |
| SCTLR enable mask = M|C|I only | `vmsav8.rs:174`, ADR-0027:58 | `(1<<0)|(1<<2)|(1<<12)`; host test `:412-422`. ✅ |
| Vector table 2 KiB-aligned, 16×0x80, IRQ live at `+0x280` | `vectors.s:39,42-83`, `linker.ld:33`, exceptions.md:58 | `.balign 2048`; `.text.vectors` `ALIGN(2048)` in linker; `+0x280` = curr_el_spx IRQ. ✅ |
| `VBAR_EL1` written once, before `DAIF.I` unmask | `main.rs:761-769` (install) vs `:1122-1124` (unmask) | Install precedes unmask by ~360 lines; nothing else writes VBAR_EL1. exceptions.md:220 invariant. ✅ |
| `TrapFrame` = 192 bytes; `Aarch64TaskContext` = 168 bytes | `exceptions.rs:77`, `cpu.rs:326` | Compile-time `assert!`. Asm offsets in `vectors.s`/`cpu.rs` match. ✅ |
| GICv2 EOI = priority-drop + deactivate in one write | `gic.rs:378-384`, irq_controller.rs:56-58 | Single `GICC_EOIR` write; spurious path skips EOI (`exceptions.rs:176-187`). GICv2 architecture (IHI 0048B). ✅ |
| Timer = virtual counter `CNTVCT_EL0`, PPI 27 | `cpu.rs:48,444-489`, exceptions.rs:35, ADR-0010 | `mrs cntvct_el0`; `TIMER_IRQ = IrqNumber(27)`. Two copies of the `27` constant (`cpu.rs:48`, `exceptions.rs:35`) — see cross-track note. ✅ values agree. |
| `CNTFRQ_EL0` = 62.5 MHz on QEMU virt → resolution 16 ns | `cpu.rs:64-75`, timer.rs:113-115,281-283 | Read at `new()`; `resolution_ns_for_freq(62_500_000)=16` (host test). Asserts non-zero (`cpu.rs:178`). ✅ |
| `kernel_entry` runs at EL1 (post EL-drop) | `boot.s:64-98`, `cpu.rs:135-139` | EL2→EL1 `eret`; `current_el()==1` assert. ADR-0024 Option A. ✅ |
| Userspace placeholder VA `0x0080_0000`, not executed | `main.rs:314,327,1028-1060`, ADR-0029 | L0/L1 idx 0, L2 idx 4, L3 idx 0 — empty slots in a *fresh* AS (loader allocs new root), no bootstrap-table aliasing. `load_image` produces metadata only. ✅ |
| `panic=abort`, unwinding tables discarded | `linker.ld:83-88`, boot.md:179, error-handling.md:143 | `/DISCARD/` drops `.eh_frame*`/`.gcc_except_table*`; workspace `panic="abort"`. ✅ |

## Cross-track notes

- **→ Security pass + unsafe-audit pass.** Route all MMIO/asm `unsafe` here:
  `gic.rs` (UNSAFE-2026-0019 — full distributor/CPU-interface MMIO surface),
  `mmu.rs` (0023 activate sysregs, 0024 TLB asm, 0025 descriptor writes),
  `mmu_bootstrap.rs` (0022 PT writes, 0023 MAIR/TCR/TTBR/SCTLR, 0024 TLBI/IC),
  `cpu.rs` (0006–0009 Send/Sync/context-switch, 0015 timer MRS, 0021 CNTV
  writes), `console.rs` (0003–0005), `exceptions.rs` (0020 vector install +
  trampolines, 0021 timer-mask). Specific items needing a second security
  reviewer's eye: **C7-003** (`WFI nomem` vs future wake hook — soundness
  forward-hazard), **C7-007** (W^X gap — kernel `.text` is RWX; ADR-0034-tracked
  but the security pass should confirm the deferral is still acceptable at this
  phase), and the W^X-adjacent fact that DEVICE mappings are correctly
  non-executable (`mmu.rs:224`, good).

- **→ Code↔code (HAL-trait-fit) pass.** The BSP implements `Cpu`,
  `ContextSwitch`, `Timer`, `Mmu`, `IrqController`, `Console` faithfully against
  the trait contracts in `hal/src/`. Two fit observations: (1) `Mmu::map`'s
  load-bearing Err-rollback contract (`hal/src/mmu/mod.rs:353-389`: "no mapping
  at va / pa not consumed on Err") is satisfied by `walk_and_install_leaf`
  writing the leaf descriptor *last* (`mmu.rs:434-447`) and returning before any
  leaf write on the `AlreadyMapped`/`OutOfFrames` paths — confirm this stays
  true if the walker is refactored. (2) `from_existing_root` is a BSP-specific
  `unsafe fn` *outside* the `Mmu` trait (companion to `create_address_space` for
  the bootstrap-root case, ADR-0028 row 0) — the trait-fit reviewer should
  confirm the kernel's `AddressSpace::wrap_bootstrap` path (`main.rs:921-927`)
  is the only caller and that it never routes through the zero-fill
  `create_address_space`.

- **→ Doc-accuracy pass.** C7-001 (ADR-0012 "GICv3" → GICv2) is the one
  substantive doc defect. `boot.md` and `exceptions.md` are accurate against the
  code (I cross-read both in full).

- **→ Constants-dedup (minor, code↔code).** `TIMER_IRQ`/`TIMER_IRQ_ID` (27) is
  declared in both `cpu.rs:48` and `exceptions.rs:35` with a comment
  acknowledging the duplication (`exceptions.rs:31-34`). Values agree; consider a
  shared `pub(crate) const` if a third site ever appears.

## Coverage checklist

All 12 track files read in full (line counts verified via `wc -l` at commit
288ddb2; assembly `.s` and `.ld` read in full as required):

- [x] `bsp-qemu-virt/src/main.rs` — 1308 lines (read in two passes: 1-1029, then 1029-1308)
- [x] `bsp-qemu-virt/src/cpu.rs` — 566 lines
- [x] `bsp-qemu-virt/src/mmu.rs` — 521 lines
- [x] `bsp-qemu-virt/src/gic.rs` — 385 lines
- [x] `bsp-qemu-virt/src/exceptions.rs` — 272 lines
- [x] `bsp-qemu-virt/src/mmu_bootstrap.rs` — 256 lines
- [x] `bsp-qemu-virt/src/console.rs` — 81 lines
- [x] `bsp-qemu-virt/src/boot.s` — 136 lines (assembly, read in full)
- [x] `bsp-qemu-virt/src/vectors.s` — 204 lines (assembly, read in full)
- [x] `bsp-qemu-virt/linker.ld` — 89 lines (linker script, read in full; spec said 90)
- [x] `bsp-qemu-virt/build.rs` — 17 lines
- [x] `bsp-qemu-virt/Cargo.toml` — 20 lines (spec said ~22)

Context also read in full: ADR-0012, ADR-0024, ADR-0027; `docs/architecture/
boot.md`, `docs/architecture/exceptions.md`; `docs/standards/bsp-boot-checklist.md`,
`unsafe-policy.md`, `architectural-principles.md`, `error-handling.md`;
`hal/src/{cpu,context_switch,irq_controller,timer}.rs`, `hal/src/mmu/{mod,vmsav8}.rs`;
`.agents/skills/add-bsp/SKILL.md`. Audit IDs cross-checked against
`docs/audits/unsafe-log.md` (27 referenced, 27 present).
