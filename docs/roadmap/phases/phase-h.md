# Phase H — Platform expansion

**Exit bar:** `bsp-pi5`, `bsp-jetson` (CPU-only), and one RISC-V BSP each boot and run the Phase A / B / E subset on real hardware.

**Scope:** Prove that the HAL abstraction is real. Each new BSP is mostly additive and stresses the HAL interfaces written in Phase A.

**Out of scope:** Mobile (Phase I); new architectural features; rework of HAL traits (those are a signal that the abstraction was wrong, resolved via ADR).

---

## Milestone H1 — `bsp-pi5`

Raspberry Pi 5 uses BCM2712 (Cortex-A76) with a new RP1 southbridge that handles peripherals differently than Pi 4.

### Sub-breakdown

1. **ADR-0063 — Pi 5 differences.** RP1 southbridge, peripheral topology, console routing, GIC changes.
2. **New BSP** `bsp-pi5/` — mirrors `bsp-pi4`'s shape with Pi 5 specifics.
3. **QEMU parity** — Phase A / B features work on Pi 5.
4. **Additive expectation**: the HAL trait surfaces do not change; any change is a signal for an ADR that reviews whether the HAL was wrong.

### Acceptance criteria

- ADR-0063 Accepted.
- Pi 5 boots and runs the test suite from Phase D's parity list.

## Milestone H2 — `bsp-jetson` (CPU-only)

NVIDIA Jetson Orin Nano / Orin NX / AGX Orin as aarch64 boards. Per [ADR-0004](../../decisions/0004-target-platforms.md), the GPU is out of scope (proprietary blob).

### Sub-breakdown

1. **ADR-0064 — Jetson boot chain.** CBoot / U-Boot sequence, where Tyrne inserts itself.
2. **New BSP** `bsp-jetson/` with the specific Jetson model(s) supported.
3. **`config` documentation** for users setting up Jetson hardware.

### Acceptance criteria

- ADR-0064 Accepted.
- A Jetson board boots Tyrne to the Phase A / B exit bar.
- Release notes are explicit: Jetson's GPU / NPU are inaccessible.

## Milestone H3 — First RISC-V BSP

Candidate: an MMU-capable RISC-V board — e.g., a SiFive HiFive Unmatched / Unleashed or a StarFive VisionFive 2. The first non-aarch64 target — validates that `Cpu`, `Mmu`, `IrqController`, `Timer` abstract correctly across architectures. MMU-less RISC-V microcontrollers (ESP32-C6, ESP32-C3, RP2350-RISCV, etc.) are deliberately out of scope for H3 because they cannot exercise the `Mmu` trait; if a future ADR decides to cover no-MMU targets, that is a separate milestone with its own acceptance criteria.

### Sub-breakdown

1. **ADR-0065 — RISC-V target choice.** Specific board, specific ISA subset (RV32 vs. RV64, extensions).
2. **`Cpu` / `Mmu` / `IrqController` extensions or splits** if needed — e.g., RISC-V's PLIC differs from GIC enough that an adapter or sibling trait may be warranted. If so, an ADR captures the architectural separation.
3. **New BSP** `bsp-<target>/`.
4. **Parity tests** on real hardware for the Phase A / B subset.

### Acceptance criteria

- ADR-0065 Accepted.
- RISC-V BSP boots Tyrne; the test suite runs within the architecture's capabilities.

### Phase H closure

Business review. The HAL abstraction has been tested by three architecturally distinct targets (Pi 5, Jetson, RISC-V); any leaks in the abstraction surface here.

## ADR ledger for Phase H

| ADR | Purpose | Expected state | Notes |
|-----|---------|----------------|-------|
| ADR-0063 | Pi 5 differences | H1 | renumbered 2026-05-22, was ADR-0052 (cascade from the Phase C/D collision fix, MR-001) |
| ADR-0064 | Jetson boot chain | H2 | renumbered 2026-05-22, was ADR-0053 (cascade) |
| ADR-0065 | RISC-V target choice | H3 | renumbered 2026-05-22, was ADR-0054 (cascade) |

## Open questions carried into Phase H

- Whether any HAL trait needs a v2 to accommodate architectural differences that Phase A could not foresee.
- The degree to which BSPs should share helper code (e.g., a `bsp-arm-gic` crate between Pi 4 / Pi 5 / Jetson) vs. remaining independent.
- Whether to target a specific RISC-V profile (e.g., RVA22) or stay minimal.

---

## Review-derived work items (2026-07-15 full-repository review)

Phase H's exit bar depends on the HAL abstraction being real: `bsp-pi5`, `bsp-jetson`, and the first RISC-V BSP are each validated, before any hardware is in hand, against the host-side HAL doubles in `test-hal/`, and each new BSP author leans directly on the trait contracts in `hal/`. The two epics below matter precisely *because* of that dependency — a test double that diverges from real BSP behavior lets a new-BSP implementation pass host tests while being wrong on hardware, and a HAL trait contract that is ambiguous or under-specified gets a different (and possibly incompatible) reading from each new BSP author who has to interpret it. Both epics are therefore work that should land before or alongside H1 (`bsp-pi5`), so that `bsp-jetson` (H2) and the RISC-V BSP (H3) inherit a truthful test-HAL and a tightened trait surface rather than each rediscovering the same gaps.

### Epic 1 — Test-HAL fidelity & parity

Keeps the host-side HAL doubles in `test-hal/` bit-faithful to real BSP behavior, so that a new BSP validated against these doubles (gating Milestone H1, and by inheritance H2/H3) is being validated against a truthful model rather than a convenient one.

- ⚪ **LOW** — `BlockMappedMmu` checks block-membership before alignment/flags validation in `test-hal`, inverting the real walker's precedence.
  - Location: `test-hal/src/mmu.rs:533-547` and `test-hal/src/mmu.rs:549-558`
  - Action: Factor the shared map-precondition validation (alignment + `DEVICE`/`EXECUTE` checks) that `FakeMmu::map` performs into one small helper, and have `BlockMappedMmu::map`/`unmap` (and any other decorator) call it **before** consulting `is_blocked`, so the decorator's check-order is structurally tied to the base fake's (and the real BSP's) precedence instead of relying on convention. This turns the file's own documented claim that "the injecting decorators … add exactly one failure mode each, delegating the success path unchanged" (`test-hal/src/mmu.rs:107-109`) into an enforced invariant rather than a per-decorator duplication.

- ⚪ **LOW** — `FakeUserMem`'s size arithmetic is unchecked in `test-hal`, unlike the identical pattern in sibling kernel test fixtures.
  - Location: `test-hal/src/mmu.rs:621` and `test-hal/src/mmu.rs:697`
  - Action: Use `npages.checked_mul(PAGE_SIZE).expect("test math")` in both `new()` and `region_len()` (or compute the byte length once and store it), matching the defensive-arithmetic convention already established in `kernel/src/obj/task_loader.rs`'s equivalent fixture.

- ⚪ **LOW** — `FakeUserMem::write`/`read` bound checks use unchecked addition, the same overflow-then-OOB shape as the `npages * PAGE_SIZE` finding above, at a different site.
  - Location: `test-hal/src/mmu.rs:663` and `test-hal/src/mmu.rs:679`
  - Action: Use `off.checked_add(bytes.len()).is_some_and(|end| end <= self.region_len())` (and the `read` equivalent) so an overflowing offset/length combination fails the guard instead of silently wrapping past it.

- ⚪ **LOW** — `FakeIrqController::acknowledge` does not gate on `IrqController::enable`, unlike the real GICv2, so a kernel bug that forgets to enable an IRQ line before expecting delivery is invisible to host tests.
  - Location: `test-hal/src/irq_controller.rs:45-55, 124-126, 217-226`
  - Action: Keep the loose `inject`/`acknowledge` for tests that deliberately want to bypass gating, but add a second, stricter helper (e.g. `acknowledge_enabled_only`, or a `debug_assert` behind a `strict` flag set at construction) that mirrors the real GIC by only returning an IRQ from `acknowledge` if `is_enabled` is true for it. Route any future scheduler/timer-IRQ integration tests through the strict variant — relevant as H1–H3 each bring up interrupt handling on new hardware — so a missing `enable()` call is caught on the host rather than on real silicon.

- ⚪ **LOW** — `FakeIrqController::end_of_interrupt` does not validate the acknowledge/EOI pairing invariant its own trait documents.
  - Location: `test-hal/src/irq_controller.rs:128-130`
  - Action: Track an "active" set populated by `acknowledge` and cleared by `end_of_interrupt`; have `end_of_interrupt` panic (matching this crate's existing style of enforcing architectural invariants via `assert!`, e.g. the `FAKE_MAX_IRQ` guard) when called with an IRQ that is not currently active. Low priority since `FakeIrqController` is not yet consumed by any kernel test (confirmed via repo-wide search), but worth doing before it is wired into any Phase H BSP's IRQ-handling tests.

- ⚪ **LOW** — `FakeTimer::set_now` silently permits moving the clock backward, violating the `Timer` trait's monotonicity contract, and this is already exercised unflagged by the crate's own tests.
  - Location: `test-hal/src/timer.rs:48-55, 131-137`
  - Action: Document on `set_now` that it intentionally bypasses the trait's monotonicity guarantee and is for test setup only (e.g. seeding the clock before other calls), not for simulating time reversal mid-scenario; consider renaming to make the escape hatch obvious (e.g. `reset_now_unchecked`) or adding a `debug_assert` that most call sites only use it before any `advance`/read has occurred.

- ⚪ **LOW** — `FakeTimer::new` accepts `resolution_ns == 0`, a value no real `Timer` implementation can produce.
  - Location: `test-hal/src/timer.rs:24-36`
  - Action: Add `assert!(resolution_ns > 0, "FakeTimer: resolution_ns must be > 0 — no real Timer implementation can report 0")` in `new`, mirroring the production invariant, so the fake cannot model an impossible timer — one that a new BSP's real timer driver (H1–H3) could never actually exhibit.

- ⚪ **LOW** — `FakeContextSwitch::init_context` resets `is_user`/`user_sp`/`entry_addr` on slot reuse but leaves the `switched` marker stale.
  - Location: `test-hal/src/context_switch.rs:170-185` (contrast with the reuse test at 278-299)
  - Action: Add `ctx.switched = false;` to both `init_context` and `init_user_context` for full re-seed consistency, and extend `init_context_clears_prior_user_markers_on_reuse` (or add a sibling test) to assert `switched` is also cleared on reuse.

- ⚪ **LOW** — `FakeIrqController::inject` lacks the `FAKE_MAX_IRQ` range guard that `enable`/`disable` enforce, letting tests inject architecturally-impossible `IrqNumber`s.
  - Location: `test-hal/src/irq_controller.rs:53-55`
  - Action: Add the same `assert!(irq.0 < FAKE_MAX_IRQ, ...)` guard to `inject` (or explicitly document why injection is allowed to model impossible INTIDs, if that is ever intentionally useful for a specific negative test). This keeps the fake's three interrupt-numbering entry points (enable/disable/inject) consistently bounded to what real GICv2 hardware can actually present, so a test author's typo or miscomputed constant surfaces as a host-side panic instead of silently exercising the kernel against a state hardware can never produce.

### Epic 2 — HAL abstraction hardening

Trait-bound items in `hal/` itself that stress the abstraction surface Phase H's exit bar depends on ("the HAL abstraction has been tested by three architecturally distinct targets"). Unlike Epic 1, these are contract gaps in the trait definitions, not in the test doubles that model them — left unresolved, each new BSP author in H1–H3 answers the same open question independently, risking divergent (and possibly incompatible) behavior across `bsp-pi5`, `bsp-jetson`, and the RISC-V BSP.

- 🟡 **MEDIUM** — `Timer::resolution_ns()`'s trait doc says deadlines round "to nearest," which contradicts the ceiling-rounding rationale that the trait's own `arm_deadline` contract actually requires.
  - Location: `hal/src/timer.rs:50-54`
  - Action: Reword `Timer::resolution_ns`'s doc to match the contract `arm_deadline`/`ns_to_ticks` actually enforce, e.g.: "Deadlines round *up* to the next multiple of this value (ceiling), never down, so `arm_deadline`'s 'fires at-or-after deadline_ns' guarantee holds; finer precision at the call site is silently lost." Left as-is, a future BSP author (e.g. for the RISC-V target in Milestone H3, or a Pi 5/Jetson-style target that arms its hardware comparator directly rather than reusing `ns_to_ticks`) could implement a literal "round to nearest" reading and produce deadlines that fire early, silently breaking `sleep_until`-class correctness.

- ⚪ **LOW** — `IrqController::enable`/`disable`'s contract is silent on out-of-range `IrqNumber` behavior; the one shipped implementation diverges from the ADR's own stated expectation by panicking instead of no-op'ing.
  - Location: `hal/src/irq_controller.rs:37-59`
  - Action: Settle the out-of-range behavior in an **ADR before any H1–H3 implementation assumes a particular contract** — changing a HAL trait signature is a structural decision (this file's own Out-of-scope calls out "rework of HAL traits … resolved via ADR"), and moving `enable`/`disable` to `Result<(), IrqError>` is exactly such a change, with migration impact on every existing and future BSP impl plus all kernel call sites. Extend or supersede [ADR-0011](../../decisions/0011-irq-controller-trait.md)'s open question with an ADR that (a) chooses one required behavior for an out-of-range `IrqNumber` — `Result<(), IrqError>`, clamp/no-op, or a documented panic — weighing error-handling.md's rule that `panic!` is reserved for broken invariants and is not a substitute for `Result` once callers are less trusted (the `IrqCap` capability layer will feed capability-derived values in), and (b) records the trait-signature migration impact. **Until that ADR is approved, H1–H3 must not assume a `Result`-based signature** — pin the decision down before the GICv2-derived (H1, H2) and PLIC-derived (H3, per Milestone H3's sub-breakdown item 2) `IrqController` impls each have to guess.

This epic's companion constants-duplication concern — the GICv2 architectural max-IRQ value living independently in `test-hal` and in the real driver — is not a defect but is carried below as a polish item, since it is currently harmless drift risk rather than an observed inconsistency.

### Polish & excellence

- **Polish** — Tighten the few `test-hal` SAFETY comments that don't yet name the rejected safer alternative, bringing them up to the same letter-of-policy standard the rest of the crate already sets (it cross-references PR review rounds and ADRs for its fidelity gaps).
- **Polish** — De-duplicate the GICv2 architectural max-IRQ constant between `FakeIrqController` and the real driver **without** hoisting it into the generic `tyrne_hal::irq_controller` trait module: that module is architecture-neutral and must stay so for the RISC-V PLIC path (Milestone H3), whose interrupt numbering has no ARM GIC bound — an ARM-only constant does not belong in the generic HAL API. Share it as an **implementation-local** constant instead (e.g. a GICv2-specific `hal` submodule or a small shared `gic` constants module that both `bsp-qemu-virt`'s driver and `test-hal`'s GICv2-modelling `FakeIrqController` import), so the fake and the real driver track one GICv2 bound — and `bsp-pi5`/`bsp-jetson` (H1/H2) reuse that GIC value while the PLIC BSP (H3) is free to define its own — rather than a future GICv3/LPI extension or differing board max-IRQ silently drifting the fake out of sync with the bound it models.
- **Polish** — Note in `test-hal`'s `lib.rs` Status section that `FakeIrqController` and `FakeTimer` are not yet consumed by any kernel test (confirmed via repo-wide search), turning "this fidelity gap doesn't matter yet" into a documented, trackable fact ahead of Phase H wiring these fakes into new-BSP-adjacent test suites.

Covers all 11 review findings + 3 polish items routed to this phase (one map-validation polish item folded into Epic 1's `BlockMappedMmu` check-order finding).
