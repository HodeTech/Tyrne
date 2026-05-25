# 0036 — QEMU virt is GICv2 / no-IOMMU in v1; corrects GICv3/SMMUv3 in ADR-0004/0006/0012

- **Status:** Accepted
- **Date:** 2026-05-22
- **Deciders:** @cemililik

## Context

Three foundational platform ADRs describe the QEMU `virt` interrupt controller
and IOMMU incorrectly:

- [ADR-0004 §Decision outcome](0004-target-platforms.md) calls the QEMU `virt`
  controller "GICv3".
- [ADR-0006 §Decision outcome](0006-workspace-layout.md) lists the
  `tyrne-bsp-qemu-virt` role as implementing "GICv3 + PL011 + SMMUv3".
- [ADR-0012 §Decision drivers](0012-boot-flow-qemu-virt.md) names the
  "`GICv3` distributor at `0x0800_0000`".

The shipped code contradicts all three. The BSP driver is a GICv2 driver
([`bsp-qemu-virt/src/gic.rs:1`](../../bsp-qemu-virt/src/gic.rs) — "GIC v2 driver
for QEMU virt aarch64") that programs the memory-mapped `GICD_*` / `GICC_*`
interface of GICv2 (per ARM IHI 0048B); it does **not** use the GICv3 system-register
interface (`ICC_IAR1_EL1`, `ICC_EOIR1_EL1`, etc.). QEMU's `virt` machine defaults
to a GICv2 (GIC-400-class) controller; GICv3 is only provided when the machine is
launched with `-machine gic-version=3`, which the project's runner does not pass.

For the IOMMU, [`hal/src/lib.rs:62`](../../hal/src/lib.rs) defines `pub trait Iommu {}` —
an empty marker with no methods and no implementation anywhere in `bsp-qemu-virt/`.
There is no SMMUv3 driver. QEMU `virt` can expose an SMMUv3 only when launched with
`-device smmuv3`, which the project does not do today.

These are accuracy errors in Accepted ADR bodies. Under the append-only rule
([CLAUDE.md rule 5](../../CLAUDE.md)) the bodies of those ADRs cannot be edited to
match reality — doing so would rewrite the historical record. Worse, the append-only
policy has *frozen* the contradiction in place: a reader following the conflict-resolution
convention ("disagree with a decision by writing a new ADR that supersedes the old one"
— [decisions/README.md](README.md)) has no forward pointer telling them the GICv3/SMMUv3
statements are wrong. This ADR is the corrective record those three ADRs need, and it
authorises one-line top-of-file redirect riders on each (append-only-legal — the riders
do not alter the original bodies).

This is a **retroactive-recovery ADR** in the sense of the [write-adr skill](../../.agents/skills/write-adr/SKILL.md)
§Procedure step 4: it records a correction after the fact, marked explicitly here, rather
than gating future work.

## Decision drivers

- **The build is the source of truth for what hardware v1 targets.** The driver, the
  MMIO register set, and the empty `Iommu` trait are unambiguous; the ADRs are the side
  that drifted.
- **Append-only preservation of the historical record.** ADR-0004/0006/0012 must keep
  their original bodies. A correction belongs in a new ADR plus append-only riders, never
  in an edit to the frozen Decision outcome.
- **A reader who hits the stale line must be redirected, not silently misled.** Without a
  forward pointer the contradiction is undetectable from inside the old ADR.
- **Honesty about aspirational invariants.** The security model's DMA-capability-scoping
  invariant ("a device may only DMA to memory it holds a capability for") depends on an
  IOMMU that does not exist on QEMU virt in v1. It must be stated as *future-on-QEMU*
  (currently aspirational), not as a property the running system enforces.
- **No weakening of any security guarantee.** Correcting the record to say "no IOMMU in
  v1" does not remove a guarantee the kernel ever made; it documents that the guarantee is
  not yet in force on this target, which is the more conservative statement.

## Considered options

1. **Edit the three ADR bodies in place.** Change "GICv3" → "GICv2" and remove the SMMUv3
   claim directly in ADR-0004/0006/0012.
2. **New corrective ADR + append-only top-of-file redirect riders (chosen).** Record the
   correction here; append a one-line redirect to each affected ADR pointing readers to
   this record, leaving the original bodies intact.
3. **Leave it alone; rely on the architecture docs being correct.** The architecture docs
   (`overview.md`, `exceptions.md`, `hal.md`, `phase-b.md`) already say GICv2; treat the
   ADR statements as known-stale and do nothing.

## Decision outcome

Chosen option: **Option 2 — a new corrective ADR plus append-only top-of-file redirect
riders on ADR-0004, ADR-0006, and ADR-0012.**

The corrected facts for QEMU `virt` v1 are:

- **Interrupt controller: GICv2.** QEMU `virt` is GICv2 (GIC-400-class) by default; the
  BSP ships a GICv2-only driver using the `GICD_*` / `GICC_*` MMIO interface. GICv3 would
  require `-machine gic-version=3` and a system-register driver, neither of which exists in
  v1. The Raspberry Pi 4 first-hardware target is also GICv2 (its GIC-400). The address
  `0x0800_0000` named in ADR-0012 is **correct** — only the version label "GICv3" is wrong.

- **IOMMU: none in v1.** **QEMU virt is GICv2 / no IOMMU in v1; the `Iommu` trait is a
  stub reserved for a future SMMUv3 ADR.** The empty `pub trait Iommu {}` in
  `hal/src/lib.rs` is a deliberate placeholder, not an implemented surface. No SMMUv3
  driver is built; QEMU virt would require `-device smmuv3` and a future ADR to introduce
  one.

- **DMA-capability-scoping invariant is future-on-QEMU (currently aspirational).** The
  security model's intent that device DMA be confined to capability-granted memory cannot be
  enforced without an IOMMU. On QEMU virt v1 there is no IOMMU, so the invariant is not in
  force; it becomes enforceable only when a future SMMUv3 ADR lands an `Iommu`
  implementation and the kernel programs it. Until then it is documented as aspirational,
  not as a running guarantee. This is consistent with `security-model.md`, which already
  frames SMMUv3 as future/conditional ("ADR required before the first driver that enables
  bus-master DMA").

The three affected ADRs keep their Accepted status: each contains exactly one stale clause,
not a wrong decision, so a status flip to `Superseded by 0036` would overstate the change
(their target-platform, workspace-layout, and boot-flow decisions all stand). Instead each
gains a one-line top-of-file redirect rider added in the same change that lands this ADR.

### Simulation

Not applicable — this ADR settles a single-shape factual correction; there is no
state-machine to simulate.

### Dependency chain

For this decision to be fully in effect:

```text
1. This corrective ADR exists and is Accepted — ADR-0036 (this file).
2. One-line redirect riders appended to the top of the affected ADR bodies —
   ADR-0004, ADR-0006, ADR-0012 (added in the same change as this ADR;
   append-only, bodies otherwise unchanged).
3. The future SMMUv3 / IOMMU ADR that gives the DMA-scoping invariant teeth —
   no T-NNN today; opens with the first driver that enables bus-master DMA
   (per security-model.md), at which point the `Iommu` trait gains a concrete
   implementation. Reserved as a forward-flag only; no implementation work
   depends on it before that driver exists.
```

Steps 1 and 2 are discharged by the change that lands this ADR. Step 3 is a named
forward-flag with no slot opened today, mirroring the ADR-0033/0034 placeholder pattern,
because no current implementation work depends on it.

## Consequences

### Positive

- A reader who hits "GICv3" or "SMMUv3" in ADR-0004/0006/0012 now has a forward pointer to
  the corrected record, restoring the conflict-resolution path the append-only rule had
  frozen.
- The ADR corpus stops contradicting the build and the architecture docs on the interrupt
  controller and IOMMU.
- The DMA-scoping invariant is stated honestly as aspirational-on-QEMU, so no reader
  assumes a protection the hardware does not provide in v1.

### Negative

- One more ADR and three riders to maintain. *Mitigation:* the riders are one line each and
  the correction is mechanical; the alternative (in-place edits) would violate the
  append-only rule, which is the higher cost.
- The numbering jumps to 0036 (slots 0030/0031/0033/0034 remain reserved placeholders).
  *Mitigation:* the gaps are intentional and documented in [decisions/README.md](README.md);
  ADR numbers are stable history and are never renumbered.

### Neutral

- This ADR makes no new platform decision; it corrects the record of decisions already made.
  The first-hardware target (Pi 4) and the QEMU-virt-first strategy are unchanged.
- Phase-C and Phase-D plan files that reuse numbers 0027–0036 for future subjects must
  renumber above the live Phase-B ceiling; this ADR consumes 0036, so those plans renumber
  to 0037+ (coordinated separately; recorded here so the cross-stream renumbering base is
  unambiguous).

## Pros and cons of the options

### Option 1 — edit the three ADR bodies in place

- Pro: a single reader of the old ADR sees the corrected fact with no second hop.
- Con: violates the append-only rule (CLAUDE.md rule 5) — it rewrites Accepted Decision
  outcomes and destroys the historical record of what was originally believed.
- Con: leaves no trace that a correction happened, so the *why* (build is GICv2/no-IOMMU) is
  lost.

### Option 2 — new corrective ADR + redirect riders (chosen)

- Pro: append-only-legal; original bodies preserved.
- Pro: records the corrected facts and their rationale in one citable place.
- Pro: gives the reader of any stale line a forward pointer.
- Con: two-hop read (old ADR → redirect → this ADR) and a small maintenance surface.

### Option 3 — leave it alone

- Pro: zero work.
- Con: the contradiction stays frozen; an agent or contributor reading the foundational ADRs
  is actively misled about the interrupt controller and IOMMU, and the conflict-resolution
  convention provides no escape hatch.

## References

- [ADR-0004: Target hardware platforms and support tiers](0004-target-platforms.md) —
  corrected here (GICv3 → GICv2).
- [ADR-0006: Workspace layout and initial crate boundaries](0006-workspace-layout.md) —
  corrected here (GICv3 + SMMUv3 → GICv2; `Iommu` is a stub).
- [ADR-0012: Boot flow and memory layout for `bsp-qemu-virt`](0012-boot-flow-qemu-virt.md) —
  corrected here (GICv3 distributor → GICv2 distributor; the `0x0800_0000` address is
  correct).
- [ADR-0011: `IrqController` HAL trait signature (v1)](0011-irq-controller-trait.md) —
  abstracts both GICv2 and GICv3; its trait surface is unaffected by this correction.
- [`bsp-qemu-virt/src/gic.rs`](../../bsp-qemu-virt/src/gic.rs) — the GICv2 driver (source of
  truth for the controller version).
- [`hal/src/lib.rs`](../../hal/src/lib.rs) — `pub trait Iommu {}` (the empty stub).
- [`docs/architecture/security-model.md`](../architecture/security-model.md) — frames
  SMMUv3 / DMA scoping as future/conditional; consistent with this ADR.
- ARM *GIC Architecture Specification* — GICv2 `GICD_*` / `GICC_*` MMIO vs. GICv3 `ICC_*`
  system-register interface.
- ARM *GIC-400 Technical Reference Manual* — the GICv2 implementation in QEMU virt and Pi 4.
- QEMU `virt` machine documentation — https://qemu.readthedocs.io/en/latest/system/arm/virt.html
  (default `gic-version=2`; `-device smmuv3` for the IOMMU).
