# D2a-adr-early — ADRs 0001-0018 + index/template (master review, commit 288ddb2)

## Summary

All 18 ADRs, the README index, and the template were read in full and cross-checked against the actual codebase, the write-adr / supersede-adr / sync-adr-index skill files, ADR-0025 governance rules, and the documentation style standard. The corpus is in strong shape overall: decisions are well-reasoned, alternatives are credible, consequences include real negatives with mitigations, and the append-only convention is respected throughout. Three accuracy mismatches between ADR text and the implemented code were found (one Major, two Minor), along with several Minor/Nit documentation hygiene issues and a cluster of stale skill-path references in ADR-0013.

Severity counts: **0 Blockers**, **1 Major**, **6 Minor**, **5 Nits**, **5 Praise items**.

No ADR in range 0001-0018 is silently outdated without being properly addressed; evolution beyond the v1 decisions described in these ADRs is correctly documented through riders, revision notes in later ADRs, or the supersession mechanism.

---

## Findings

### Blocker

None.

---

### Major

**D2a-001** — ADR-0008: `IrqGuard` type signature changed without a rider

`file: docs/decisions/0008-cpu-trait.md:87-102`

ADR-0008 §Decision outcome specifies `IrqGuard<'a>` as taking `&'a dyn Cpu` (dynamic dispatch):

```rust
pub struct IrqGuard<'a> {
    cpu: &'a dyn Cpu,
    prev: IrqState,
}
impl<'a> IrqGuard<'a> {
    pub fn new(cpu: &'a dyn Cpu) -> Self { … }
}
```

The actual implementation in `hal/src/cpu.rs:102-122` uses a generic type parameter instead:

```rust
pub struct IrqGuard<'a, C: Cpu> {
    cpu: &'a C,
    prev: IrqState,
}
```

The code's rustdoc (lines 86-91 of `hal/src/cpu.rs`) explains the reason ("coercing a concrete type to a trait object at certain inlining depths can produce vtable references that alias unrelated data in `.rodata`; using a concrete type parameter eliminates the coercion site entirely"), but this rationale and the resulting type-signature change are not recorded in ADR-0008. There is no `## Revision notes` section in ADR-0008 at all.

This matters because: (a) the Decision outcome's signature is incorrect as of the current codebase, so any reader or agent relying on the ADR to understand the `IrqGuard` API will be misled; (b) the architectural argument for the change — vtable-alias risk under inlining — is safety-relevant and belongs in the design record.

**Suggested fix:** Add a `## Revision notes` section to ADR-0008 with a rider dated at the time the change was made, following the same pattern as the ADR-0009 and ADR-0010 revision-notes riders. The rider should: state that `IrqGuard` was changed to generic `<C: Cpu>`, explain the vtable/inlining aliasing hazard that motivated it, note the Audit entry (if any) that covers the change, and confirm that the `Cpu` trait itself remains object-safe (`&dyn Cpu` is still the kernel's canonical handle for calling individual trait methods).

---

### Minor

**D2a-002** — ADR-0012: GIC version claim is incorrect (says GICv3, BSP uses GICv2)

`file: docs/decisions/0012-boot-flow-qemu-virt.md:24`

The Decision drivers section states: "we currently hardcode MMIO addresses (PL011 at `0x0900_0000`, **`GICv3` distributor** at `0x0800_0000`, etc.)". The QEMU `virt` BSP (`bsp-qemu-virt/src/gic.rs:29`, `gic.rs:37`, `gic.rs:82`) consistently names and implements a **GICv2** controller using the `GICC_*/GICD_*` memory-mapped interface characteristic of GICv2. GICv3's System Register interface (`ICC_IAR1_EL1`, `ICC_EOIR1_EL1` via `MSR`/`MRS`) is not present.

ADR-0006 carries the same error at `docs/decisions/0006-workspace-layout.md:47`: "GICv3 + PL011 + SMMUv3" in the BSP role description.

This affects accuracy. A future BSP author or reviewer reading ADR-0012 will be misled about the GIC version actually used.

**Suggested fix:** Add riders to both ADR-0012 and ADR-0006 correcting "GICv3" to "GICv2" with the note that the default QEMU `virt` machine without `-machine gic-version=3` provides a GICv2 (GIC-400 compatible) controller; GICv3 would require explicit QEMU machine configuration.

---

**D2a-003** — ADR-0006: BSP role description claims SMMUv3 implementation; SMMUv3 is not implemented

`file: docs/decisions/0006-workspace-layout.md:47`

The crate-table row for `tyrne-bsp-qemu-virt` lists "GICv3 + PL011 + **SMMUv3**" as the implementations provided. The HAL exposes a stub-only `Iommu` trait (`hal/src/lib.rs:62`): `pub trait Iommu {}`. There is no SMMUv3 driver anywhere in `bsp-qemu-virt/src/`. The `Iommu` trait is itself described as a placeholder pending a future ADR in `hal/src/lib.rs`.

**Suggested fix:** Add a rider to ADR-0006 correcting the BSP role description to remove the SMMUv3 claim; replace with a note that `Iommu` is a stub-only trait pending its own ADR when a concrete IOMMU caller arrives.

---

**D2a-004** — ADR-0013: Multiple skill paths reference deleted `.claude/skills/` directory

`file: docs/decisions/0013-roadmap-and-planning.md:9,129,139,140,141,215`

ADR-0013 references `.claude/skills/` at six locations:
- Line 9: "skills](../../.claude/skills/) encode procedures"
- Lines 129, 139, 140, 141: four `[skill](../../.claude/skills/<name>/SKILL.md)` links
- Line 215: "skills](../../.claude/skills/)"

The project memory records that `.claude/skills/` was deleted and all skills migrated to `.agents/skills/<slug>/SKILL.md` on 2026-05-14 (commit `77d3e7e`). The `.claude/` directory does not exist in the working tree. All six links are therefore dead references.

ADR-0025 (which would otherwise govern a correction) explicitly grandfathers ADR-0001 through ADR-0024: "The two rules ... do not retroactively apply to ADRs already Accepted." A rider is still appropriate for accuracy.

**Suggested fix:** Add a rider to ADR-0013 §Revision notes noting the skills directory migration (2026-05-14, commit `77d3e7e`) and that the `.claude/skills/` links are now stale; the canonical skill library is at `.agents/skills/`. The ADR body is left intact per the append-only rule; the rider provides the live redirect.

---

**D2a-005** — template.md: Cites ADR-0018 as an example of `Deferred` status, but ADR-0018 is `Accepted`

`file: docs/decisions/template.md:11`

The template comment reads: `Deferred — recognised as needed but explicitly postponed; no file body required if filed-but-deferred (see ADR-0018, ADR-0023).` ADR-0023 is correctly status `Deferred`. ADR-0018 is status `Accepted`; it formally records a deferral of two features (badge scheme, `reply_recv`) but is itself an Accepted decision record, not a Deferred placeholder.

A reader studying the template to understand the `Deferred` status will be confused by the ADR-0018 citation.

**Suggested fix:** Remove ADR-0018 from the `Deferred` example parenthetical, leaving only `(see ADR-0023)` as the example of a filed-but-deferred slot.

---

**D2a-006** — README `Creating a new ADR` section does not mention Simulation or Dependency chain requirements

`file: docs/decisions/README.md:64-71`

The README's five-step procedure for creating an ADR was written before ADR-0025 and the write-adr skill were updated with the §Simulation table and §Dependency chain requirements. A new contributor following the README alone would not know these sections are required for multi-step state-machine ADRs and all post-ADR-0025 ADRs respectively.

The `write-adr` skill is the authoritative procedure, so there is no practical ambiguity for agents that read CLAUDE.md and follow the skill. But the README is read directly by human contributors arriving from GitHub, who may never open the skill file.

**Suggested fix:** Add a brief note to the `Creating a new ADR` section pointing to the `write-adr` skill (`docs/.agents/skills/write-adr/SKILL.md`) for the complete procedure, and noting that ADRs covering multi-step state machines require a §Simulation table and a §Dependency chain per ADR-0025.

---

**D2a-007** — ADR-0012: Memory layout diagram does not reflect `.boot_pt` section added by ADR-0027

`file: docs/decisions/0012-boot-flow-qemu-virt.md:63-70` (memory layout diagram)

The diagram shows:
```
0x40080000  _start (.text.boot)
            .text / .rodata / .data
            .bss          — zeroed in _start
            (64 KiB)      — initial stack region
            __stack_top
```

ADR-0027's rider on ADR-0012 (lines 149-149) correctly documents the `.boot_pt` reservation added inside `.bss`. However, the diagram itself is not updated to show the `.boot_pt` frames (16 KiB = 4 × 4 KiB frames) within `.bss`. A reader looking at the diagram gets a misleading picture of the actual layout.

This is a Minor rather than Major because the rider text explicitly and correctly describes the change; the diagram is simply not synced.

**Suggested fix:** Add a small update to the memory layout diagram (inside the ADR-0012 §Revision notes or as a new rider) showing the `.bss` subsections, or replace the diagram inline and note the update in revision notes. Alternatively, add a note below the diagram: "Updated layout with `.boot_pt` frames: see §Open questions rider for ADR-0027 resolution."

---

### Nit

**D2a-008** — ADR-0001: Missing `## Pros and cons` entry for Microkernel option in `Microkernel (capability-based)` subheading style

`file: docs/decisions/0001-microkernel-architecture.md:81-87`

Minor formatting inconsistency: the `Pros and cons of the options` section uses `### Monolithic kernel`, `### Microkernel (capability-based)`, `### Hybrid kernel`, `### Unikernel`, `### Exokernel` as sub-headings, which is good. All options are represented — no missing entry. This is a non-issue; the nit is stylistic: the heading `### Microkernel (capability-based)` could more precisely match the option name stated in §Considered options: "Microkernel (capability-based, seL4 / Hubris lineage)". No fix required; note for consistency audits.

---

**D2a-009** — ADR-0009 revision note: cross-references ADR-0017's `ipc_cancel_recv` rider as "precedent"

`file: docs/decisions/0009-mmu-trait.md:224`

The ADR-0009 revision note (2026-05-08) says "Mirrors the [ADR-0017 §Revision rider for `ipc_cancel_recv`](0017-ipc-primitive-set.md) precedent". The `ipc_cancel_recv` rider in ADR-0017 is dated 2026-05-07, one day earlier than the ADR-0009 rider. If the ADR-0009 rider was written to mirror a precedent from ADR-0017, the chronology is plausible. This is noted for accuracy but is not an error.

---

**D2a-010** — ADR-0016: `CapObject` enum code sketch uses different variant name than final implementation

`file: docs/decisions/0016-kernel-object-storage.md:121-132`

The ADR's `CapObject` sketch shows variants `Task(TaskHandle)`, `Endpoint(EndpointHandle)`, `Notification(NotificationHandle)`, and comments `// MemoryRegion arrives in Phase B`. The final code in `kernel/src/cap/mod.rs` has `Task`, `Endpoint`, `Notification`, `AddressSpace(AddressSpaceHandle)`, and `MemoryRegion` (stubbed). The `AddressSpace` variant is Phase B work covered by ADR-0028, which correctly documents the addition. The ADR sketch is therefore out-of-date by Phase B additions that postdate ADR-0016. This is expected evolution and ADR-0028 covers it; the finding is a Nit to note the ADR sketch is no longer current, not an error.

---

**D2a-011** — ADR-0014: `Negative consequences` generation-overflow discussion is more detailed than the code

`file: docs/decisions/0014-capability-representation.md:206`

The ADR states: "v1 does *not* implement a slot-poisoning mechanism — the current `Slot` layout has no dedicated poison indicator, and `free_slot` wraps the generation without checking for overflow." This matches the code (`slot.generation = slot.generation.wrapping_add(1)` at `kernel/src/cap/table.rs:583`). The ADR is accurate; the finding is that this is a known deferred risk documented correctly. No action needed. Noted for the claims register.

---

**D2a-012** — ADR-0017 rider (line 215): mentions "ADR-0030" for future syscall ABI

`file: docs/decisions/0017-ipc-primitive-set.md:215`

The rider says "the future syscall-ABI ADR (currently pencilled as ADR-0030) decides whether to expose it directly." ADRs 0030 and 0031 do not exist in the repository. This is a forward-reference to a not-yet-filed ADR. Per ADR-0025 §Rule 1, "future, not-yet-opened task" wording is forbidden. However, the rule explicitly states it applies to *task* forward-references ("future task X will do Y"), not to ADR forward-references pencilled by number. Additionally, the rule was not retroactively applied to ADRs 0001-0024. The finding is a Nit: the "pencilled as ADR-0030" language is informal and creates an expectation that an ADR-0030 slot will exist; if the slot is not opened, the reference rots. Consider changing "pencilled as ADR-0030" to a descriptive "a future syscall-ABI ADR" without a number prediction.

---

### Praise

**D2a-P1** — ADR-0001 through ADR-0018: Consistent, credible alternatives in every ADR

Every ADR in this range presents at least two real alternatives. None of the rejected options are strawmen — the cons of the chosen option and the pros of rejected options are honestly stated. This is the ADR set's strongest property and makes the corpus genuinely valuable as a design record. The seL4/Hubris lineage context in ADR-0001, the Rust vs. Ada/SPARK comparison in ADR-0002, and the Option A/B/C/D analysis in ADR-0009 are particularly well-balanced.

**D2a-P2** — ADR-0009, ADR-0010, ADR-0017: Revision notes riders used correctly for additive changes

The three riders in ADR-0009 (MapperFlush token), ADR-0010 (IRQ-armed half landing, timer ns_to_ticks addition), and ADR-0017 (ipc_cancel_recv) all correctly use the append-only revision-notes pattern: the original body is untouched, the rider explicitly dates the change, cites the implementing task and commit, and explains why the change is additive rather than superseding. This is exactly the pattern ADR-0025 codified, and these ADRs demonstrate it working well in practice.

**D2a-P3** — ADR-0014: Safety-aware negative consequences (generation overflow) explicitly named and deferred consciously

ADR-0014's negative consequence on generation overflow (line 206) is unusually good: it names the exact failure mode (`u32::MAX` wrapping), explains what is *not* implemented (no poison sentinel), describes two concrete mitigation options (`u32::MAX` sentinel vs. `poisoned: bool` field), and explicitly defers the decision. This is the kind of documented, conscious technical debt that is far safer than undocumented technical debt.

**D2a-P4** — ADR-0018: Principled deferral with named revisit triggers

ADR-0018's "Revisit triggers" section (three numbered conditions under which the deferral should be superseded) is an excellent pattern for a formal deferral ADR. It converts "we'll do this later" into a checkable specification: a reader can evaluate whether any trigger condition has been met.

**D2a-P5** — ADR-0012: Open questions resolved inline with riders

ADR-0012 uses the open-questions section to name five deferreds (EL drop, DTB parsing, multi-core start, boot-time MMU activation, stack size policy). Three of these were subsequently resolved and the resolutions were appended as riders directly on the relevant open-question text. The "Boot-time MMU activation" open question even uses strikethrough to mark it as resolved. This demonstrates the append-only evolution pattern working as intended.

---

## Claims register

| ADR decision / claim | ADR file:line | Verification status / code evidence |
|---|---|---|
| Kernel uses capability-based microkernel; TCB is small | 0001:39 | Confirmed: kernel/ crate has no driver code; bsp-qemu-virt is separate |
| All code in Rust, `no_std` for kernel | 0002:34-36 | Confirmed: `hal/`, `kernel/`, `bsp-qemu-virt/` are all Rust; `kernel/Cargo.toml` is `no_std` |
| Apache-2.0 single license | 0003:36 | Confirmed: `LICENSE` is Apache-2.0; `Cargo.toml` `[workspace.package]` says `license = "Apache-2.0"` |
| Primary target QEMU virt aarch64; load address 0x40080000 | 0004:29, 0012:48 | Confirmed: `bsp-qemu-virt/linker.ld` ORIGIN=0x40080000 |
| English in repository; Turkish in chat only | 0005:32-33 | Confirmed: all committed files are English |
| Four crates: tyrne-kernel, tyrne-hal, tyrne-bsp-qemu-virt, tyrne-test-hal | 0006:37-48 | Confirmed: `Cargo.toml` workspace members match; `tools/` subdirectory not a separate crate |
| BSP implements "GICv3 + PL011 + SMMUv3" | 0006:47 | **INACCURATE**: BSP uses GICv2 (`bsp-qemu-virt/src/gic.rs`); SMMUv3 is a stub-only `Iommu` trait; see D2a-002, D2a-003 |
| Console trait: `fn write_bytes(&self, bytes: &[u8])` + `Send + Sync` | 0007:37-39 | Confirmed: `hal/src/console.rs:34-39` matches exactly |
| FmtWriter<'a>(pub &'a dyn Console) adapter | 0007:43-52 | Confirmed: `hal/src/console.rs:59-66` matches exactly |
| Cpu trait: five methods (current_core_id, disable_irqs, restore_irq_state, wait_for_interrupt, instruction_barrier) | 0008:69-77 | Confirmed: `hal/src/cpu.rs:44-76` matches |
| IrqGuard<'a> takes &'a dyn Cpu | 0008:87-102 | **INACCURATE**: actual is `IrqGuard<'a, C: Cpu>` generic; no rider; see D2a-001 |
| Mmu trait: associated AddressSpace type, map/unmap return MapperFlush (via ADR-0009 rider) | 0009:56-114, revision note:224 | Confirmed: `hal/src/mmu/mod.rs:300-438` matches including MapperFlush |
| ADR-0012: GICv3 distributor at 0x0800_0000 | 0012:24 | **INACCURATE**: BSP uses GICv2 at 0x0800_0000; see D2a-002 |
| Stack: 64 KiB region, __stack_top | 0012:52 | Confirmed: `linker.ld` uses `. = . + 64K; __stack_top = .;` |
| .boot_pt frames inside .bss (ADR-0027 rider) | 0012:149 | Confirmed: `linker.ld` shows .boot_pt frames inside .bss range |
| CAP_TABLE_CAPACITY = 64, MAX_DERIVATION_DEPTH = 16 | 0014:59-63 | Confirmed: `kernel/src/cap/table.rs:19,26` |
| CapHandle = (index: u16, generation: u32) | 0014:68-72 | Confirmed: `kernel/src/cap/table.rs:41-44` |
| Generation bumps with wrapping_add (no poison in v1) | 0014:206 | Confirmed: `kernel/src/cap/table.rs:583` uses `wrapping_add(1)` |
| CapRights four v1 bits: DUPLICATE=1, DERIVE=2, REVOKE=4, TRANSFER=8 | 0014:79-86 | Confirmed: `kernel/src/cap/rights.rs` matches |
| SEND/RECV/NOTIFY rights do not overlap existing bits (T-003) | 0017:209 | Confirmed: `kernel/src/cap/rights.rs` SEND=1<<4, RECV=1<<5, NOTIFY=1<<6 |
| IPC operations: ipc_send, ipc_recv, ipc_notify (three primitives) | 0017:56-98 | Confirmed: `kernel/src/ipc/mod.rs:6-8` documents exactly these three |
| ENDPOINT_QUEUE_DEPTH = 1 | 0017:116-122 | Confirmed: `kernel/src/ipc/mod.rs:82` notes "depth 1 in v1" |
| Message struct: label: u64 + params: [u64; 3] | 0017:87-94 | Confirmed: `kernel/src/ipc/mod.rs:68` matches |
| ipc_cancel_recv is recovery primitive only, not user-observable | 0017 revision:215 | Confirmed: `kernel/src/ipc/mod.rs:425-444` documents kernel-internal use only |
| ADR-0018: badge and reply_recv deferred; ADR-0018 is itself Accepted | 0018:53-64 | Confirmed: both features deferred to named trigger conditions; ADR status is Accepted |
| Kernel object storage: per-type arenas Task/Endpoint/Notification | 0016:59-61 | Confirmed: `kernel/src/obj/mod.rs`, `task.rs`, `endpoint.rs`, `notification.rs` |
| Generic Arena<T, N> used for all three kinds | 0016:171 | Confirmed: `kernel/src/obj/arena.rs:88` implements `Arena<T, const N: usize>` |
| AI-neutral kernel; four hooks reserved | 0015:55-84 | Confirmed by code: no LLM or inference code anywhere in kernel/ or hal/ |
| Skills directory at .agents/skills/ (migrated 2026-05-14) | Memory, not in 0001-0018 | ADR-0013 still references deleted .claude/skills/; see D2a-004 |

---

## ADR status table

| ADR | Title | Status as written | Code agrees? | Notes |
|---|---|---|---|---|
| 0001 | Capability-based microkernel architecture | Accepted | Yes | Kernel structure matches the decision |
| 0002 | Rust as the implementation language | Accepted | Yes | All code is Rust; no_std confirmed |
| 0003 | Apache-2.0 license | Accepted | Yes | LICENSE + Cargo.toml match |
| 0004 | Target hardware platforms and support tiers | Accepted | Yes | QEMU virt is Tier 1; Pi 4 Tier 2 as documented |
| 0005 | English as documentation and code language | Accepted | Yes | Repository is entirely English |
| 0006 | Workspace layout and initial crate boundaries | Accepted | Mostly — GICv3/SMMUv3 claims inaccurate (D2a-002, D2a-003) | Four-crate split is accurate; crate roles table has two inaccurate peripheral claims |
| 0007 | Console HAL trait signature | Accepted | Yes | write_bytes + FmtWriter match exactly |
| 0008 | Cpu HAL trait signature (v1, single-core scope) | Accepted | Partial — IrqGuard signature changed (D2a-001) | Five Cpu trait methods match; IrqGuard changed to generic without rider |
| 0009 | Mmu HAL trait signature (v1) | Accepted | Yes | Trait matches; MapperFlush extension properly documented in revision notes |
| 0010 | Timer HAL trait signature (v1) | Accepted | Yes | Four-method trait matches; ns_to_ticks helper addition documented in revision notes |
| 0011 | IrqController HAL trait signature (v1) | Accepted | Yes | Four-method trait matches exactly |
| 0012 | Boot flow and memory layout for bsp-qemu-virt | Accepted | Mostly — GICv3 claim inaccurate (D2a-002); diagram misses .boot_pt (D2a-007) | Load address 0x40080000, stack 64 KiB, kernel_entry all confirmed; open questions resolved with riders |
| 0013 | Roadmap and planning process | Accepted | Structurally yes — stale .claude/skills/ links (D2a-004) | Folder layout, task IDs, review types all match actual repo structure |
| 0014 | Capability representation | Accepted | Yes | Types, constants, generation wrap all match code |
| 0015 | AI integration stance: userspace-only, kernel-neutral | Accepted | Yes | No AI/LLM code in privileged paths confirmed |
| 0016 | Kernel object storage | Accepted | Yes (with phase-B evolution) | Three arenas plus generic Arena<T,N> confirmed; AddressSpace added in Phase B per ADR-0028 |
| 0017 | IPC primitive set | Accepted | Yes | Three primitives confirmed; cancel_recv addition properly documented as additive rider |
| 0018 | Badge scheme and reply_recv deferral | Accepted | Yes | Both features correctly deferred; revisit triggers documented |

---

## Cross-track notes

- **Track D2b (ADRs 0019-0035) coordination:** ADR-0020 supersedes ADR-0008 on the `ContextSwitch` trait / `Cpu v2` axis; Track D2b reviewers should note that ADR-0008's `Cpu` trait (v1) is still the authoritative reference for the five core methods and the IrqState/IrqGuard types. ADR-0020 adds context-switch primitives rather than replacing the core. The undocumented IrqGuard change (D2a-001) predates or coincides with ADR-0020 work; Track D2b should check whether ADR-0020 addresses the IrqGuard type change.

- **Track D2b (ADR-0022 / ADR-0026):** ADR-0022 is listed in the README index as "Superseded by 0026 (idle-task-location axis only; typed-error axis stands)". The ADR-0022 file header confirms: `Status: Superseded by 0026 (idle-task-location axis only; typed-error axis stands)`. The split supersession is correctly documented on both ends. Track D2b should verify the actual ADR-0022 body has the callout per the `supersede-adr` skill requirements.

- **Track D2b (ADR-0025):** ADR-0025 grandfathers ADRs 0001-0024, meaning the absence of §Simulation and §Dependency chain sections in ADR-0007 through ADR-0018 is not a defect — they predate the requirement. This review does not flag those absences as findings.

- **Security track coordination:** ADR-0014's generation-overflow finding (D2a-011) is a known deferred risk. The security track should confirm no path exists in the current codebase that could realistically exhaust a slot's `u32::MAX` generation counter in a realistic workload. The fix path described in ADR-0014 (sentinel at `u32::MAX` or a `poisoned: bool` field) should be confirmed as the intended approach.

- **Track covering ADR-0030/0031/0033/0034 gaps:** The index correctly has no entries for 0030, 0031, 0033, 0034. ADR-0017's rider (D2a-012) references "ADR-0030" informally. ADR-0012's rider mentions "ADR-0033 placeholder". These are future-ADR predictions, not claims that those slots exist. The numbering gaps are intentional (slots not yet opened). No remediation needed; flagged so the gap-accounting track is aware.

---

## Coverage checklist

All 20 files in scope were read in full.

| File | Lines | Read in full |
|---|---|---|
| `docs/decisions/0001-microkernel-architecture.md` | 114 | [x] |
| `docs/decisions/0002-implementation-language-rust.md` | 110 | [x] |
| `docs/decisions/0003-license-apache-2.md` | 98 | [x] |
| `docs/decisions/0004-target-platforms.md` | 123 | [x] |
| `docs/decisions/0005-documentation-language-english.md` | 83 | [x] |
| `docs/decisions/0006-workspace-layout.md` | 143 | [x] |
| `docs/decisions/0007-console-trait.md` | 115 | [x] |
| `docs/decisions/0008-cpu-trait.md` | 165 | [x] |
| `docs/decisions/0009-mmu-trait.md` | 237 | [x] |
| `docs/decisions/0010-timer-trait.md` | 161 | [x] |
| `docs/decisions/0011-irq-controller-trait.md` | 145 | [x] |
| `docs/decisions/0012-boot-flow-qemu-virt.md` | 164 | [x] |
| `docs/decisions/0013-roadmap-and-planning.md` | 219 | [x] |
| `docs/decisions/0014-capability-representation.md` | 263 | [x] |
| `docs/decisions/0015-ai-integration-stance.md` | 170 | [x] |
| `docs/decisions/0016-kernel-object-storage.md` | 239 | [x] |
| `docs/decisions/0017-ipc-primitive-set.md` | 225 | [x] |
| `docs/decisions/0018-badge-scheme-and-reply-recv-deferral.md` | 98 | [x] |
| `docs/decisions/README.md` | 70 | [x] |
| `docs/decisions/template.md` | 121 | [x] |

Total lines read: 3063 across the 20 in-scope files. Lens documents read in full: `docs/standards/documentation-style.md`, `.agents/skills/write-adr/SKILL.md`, `.agents/skills/supersede-adr/SKILL.md`, `.agents/skills/sync-adr-index/SKILL.md`, `docs/decisions/0025-adr-governance-amendments.md`. Code files cross-checked: `hal/src/console.rs`, `hal/src/cpu.rs`, `hal/src/mmu/mod.rs`, `hal/src/irq_controller.rs`, `hal/src/timer.rs`, `hal/src/lib.rs`, `kernel/src/cap/table.rs`, `kernel/src/cap/mod.rs`, `kernel/src/cap/rights.rs`, `kernel/src/obj/arena.rs`, `kernel/src/ipc/mod.rs`, `bsp-qemu-virt/src/gic.rs`, `bsp-qemu-virt/src/main.rs`, `bsp-qemu-virt/linker.ld`, `Cargo.toml`.
