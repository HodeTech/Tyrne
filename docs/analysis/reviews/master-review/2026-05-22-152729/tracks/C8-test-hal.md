# C8-test-hal — fake HAL for host tests (master review, commit 288ddb2)

## Summary

The `tyrne-test-hal` crate provides five deterministic host-side fake implementations of the `tyrne_hal` traits: `FakeMmu`, `FakeCpu`, `FakeIrqController`, `FakeTimer`, and `FakeConsole`. The crate is the sole testing surface used by the 200+ kernel unit tests; fidelity gaps here directly determine whether those tests actually exercise the real HAL contract or merely exercise a more permissive shadow.

**Overall verdict: Solid with targeted gaps.** The fakes are well-structured, internally consistent, and correctly mirror the majority of the real HAL contracts. The crate demonstrates commendable discipline in modeling error conditions (alignment rejections, invalid flag combinations, double-map detection) that were explicitly requested by prior review rounds. The unsafe surface is narrow and its invariants are sound. However, five gaps were found that have genuine fidelity risk and require attention before the test suite can be considered a faithful proxy for hardware behavior:

1. The `unsafe fn create_address_space` implementation has no `# Safety` doc-comment and no audit-log entry, both of which are required by the project's unsafe policy.
2. `FakeMmu` never returns `MmuError::OutOfFrames` from `map`, so kernel-side `OutOfFrames` rollback paths are untested against the HAL contract.
3. `FakeMmu` never returns `MmuError::BlockMapped`, masking a kernel-visible error variant that the real BSP can produce.
4. The `FakeIrqController` does not enforce the `GIC_MAX_IRQ` range on `enable`/`disable`, permitting kernel tests to pass `IrqNumber` values that would panic or corrupt MMIO on real hardware.
5. `VecFrameProvider::alloc_frame` does not enforce the `FrameProvider` contract that frames are zero-initialized, so any kernel code that relies on the zero-fill guarantee is untested.

Severity counts: 1 Major, 4 Minor, 4 Nit, 2 Praise.

---

## Findings (by severity)

### Major

#### C8-001 — `unsafe fn create_address_space` lacks `# Safety` doc-comment and audit-log entry

**File:** `test-hal/src/mmu.rs:133`

**Description:**
`FakeMmu` implements `Mmu::create_address_space` as an `unsafe fn` (required by the trait signature). The trait's `# Safety` contract (`root` must be page-aligned, exclusively owned, and zero-initialized) is visible on the HAL trait itself, but `FakeMmu`'s override has no `# Safety` section in its doc-comment and no audit-log entry (`UNSAFE-YYYY-NNNN`).

The unsafe policy (`docs/standards/unsafe-policy.md §1, §2, §3`) is unambiguous:
- Every `unsafe fn` must have a `# Safety` section in its doc-comment.
- Every `unsafe` block and `unsafe fn` declaration must have an adjacent `// SAFETY:` comment explaining (a) invariants upheld, (b) rejected alternatives, (c) audit reference.
- An audit-log entry in `docs/audits/unsafe-log.md` is required.

The function body is trivial (`FakeAddressSpace { root, mappings: HashMap::new() }`), but the *policy* requirement is not waived for trivial implementations. The test-site call sites all have `// SAFETY:` comments explaining why `FakeMmu::create_address_space` is safe to call — the implementation itself does not document which parts of the trait's contract it upholds or waives.

**Why it matters:** Reviewers auditing any new call site of `create_address_space` in test code look at the implementation's `# Safety` section to understand the contract being exercised. Its absence is a policy violation that the CI gate (`clippy::missing_safety_doc`) should catch but apparently does not for trait method overrides in this context.

**Suggested fix:**
Add to `FakeMmu::create_address_space` a `// SAFETY:` comment on the impl block entry:
```rust
// SAFETY:
// (a) Invariants upheld: FakeAddressSpace is a pure host-side HashMap with no
//     hardware interaction; the `root` PhysFrame is stored as a value (not
//     dereferenced). The page-alignment invariant is enforced upstream by
//     `PhysFrame::from_aligned`. The zero-fill and exclusive-ownership
//     pre-conditions on `root` are vacuously satisfied — FakeMmu never reads
//     or writes the frame's physical memory.
// (b) Rejected alternatives: making the trait method `safe fn` is impossible;
//     the trait declaration is `unsafe fn` so every impl must use the same
//     signature.
// Audit: [new entry UNSAFE-2026-NNNN to be created in docs/audits/unsafe-log.md]
```
Add a corresponding entry to `docs/audits/unsafe-log.md`.

---

### Minor

#### C8-002 — `FakeMmu::map` never returns `MmuError::OutOfFrames` (fidelity gap)

**File:** `test-hal/src/mmu.rs:148–177`

**Description:**
The `Mmu::map` trait contract documents `MmuError::OutOfFrames` as a possible return value when `frames.alloc_frame()` returns `None` during intermediate-table allocation. The real `QemuVirtMmu::map` implementation in `bsp-qemu-virt/src/mmu.rs:510` returns this error via `frames.alloc_frame().ok_or(MmuError::OutOfFrames)`.

`FakeMmu::map` accepts a `_frames: &mut dyn FrameProvider` parameter (note the underscore suppressing an unused-variable warning) and never calls `alloc_frame`. It therefore cannot return `OutOfFrames` regardless of how the `FrameProvider` is configured.

**Fidelity risk:** The kernel's `cap_create_address_space` + `load_image` test suites include extensive `OutOfFrames` rollback tests (see `kernel/src/obj/task_loader.rs:1954–2003`). Those tests drive `OutOfFrames` through the PMM running dry, not through intermediate-table exhaustion in `Mmu::map` itself. The distinct case where intermediate-table allocation fails inside `map` — and `pa` (the leaf frame) is retained by the caller per the trait's failure-semantics clause (2) — is never exercised through the fake. A real BSP that incorrectly returns `pa` as consumed on `OutOfFrames` would not be caught by any current host test.

**Note:** Because `FakeMmu` has no multi-level page table structure, this limitation is intrinsic to the flat-HashMap design — the fake cannot model intermediate-table allocation at all. The gap should be explicitly documented and a fidelity note added to the `FakeMmu` struct doc-comment, even if a full simulation is out of scope.

**Suggested fix:** Add to the `FakeMmu` struct doc-comment:
> **Fidelity note — `OutOfFrames` from intermediate-table allocation:** `FakeMmu` does not model multi-level page-table structure and therefore never returns `MmuError::OutOfFrames` from `map`. Kernel tests that need to exercise the `map`-internal `OutOfFrames` path (the leaf-frame rollback contract at failure-semantics clause (2)) require a purpose-built fake that wraps `FakeMmu` and injects the error, or must be deferred to BSP-level QEMU tests.

Also add a test that explicitly documents this known gap (see `FakeIrqController`'s `disabled_irq_can_still_be_injected_for_test_purposes` as a precedent for self-documenting limitations).

---

#### C8-003 — `FakeMmu` never returns `MmuError::BlockMapped` (fidelity gap)

**File:** `test-hal/src/mmu.rs:179–193`

**Description:**
`MmuError::BlockMapped` is a real error returned by `QemuVirtMmu::unmap` (and `map`) when the page-table walk encounters a large-block descriptor at L1/L2 — a situation that arises naturally after the bootstrap MMU setup installs 2 MiB block mappings for the kernel image. The real BSP's `walk_or_alloc_table` returns `MmuError::BlockMapped` via `bsp-qemu-virt/src/mmu.rs:494`.

`FakeMmu`'s `unmap` uses a flat `HashMap` and can only return `NotMapped` or `MisalignedAddress`. The `BlockMapped` variant is absent. Kernel code that calls `Mmu::unmap` and must handle `BlockMapped` distinctly from `NotMapped` (the `AddressSpaceError::MmuUnmapError` wrapping in `kernel/src/mm/address_space.rs:779`) is never exercised through this path.

**Fidelity risk:** Lower than C8-002 because v1 has no `cap_unmap` callers at runtime, but the `cap_unmap` test in `address_space.rs` only tests the happy path and `NotMapped` rejection. Any kernel logic that pattern-matches on `MmuUnmapError(BlockMapped)` versus `MmuUnmapError(NotMapped)` is untested.

**Suggested fix:** Add a doc-comment note to `FakeMmu` (alongside the C8-002 note):
> **Fidelity note — `BlockMapped`:** `FakeMmu` does not model block descriptors and therefore never returns `MmuError::BlockMapped`. Tests that need to exercise `BlockMapped` handling must use a purpose-built decorator fake.

---

#### C8-004 — `FakeIrqController` does not validate `IrqNumber` range (fidelity gap)

**File:** `test-hal/src/irq_controller.rs:94–99`

**Description:**
The real `QemuVirtGic::enable` and `QemuVirtGic::disable` (`bsp-qemu-virt/src/gic.rs:317–362`) both `assert!(irq.0 < GIC_MAX_IRQ)` (= 1020), panicking if a caller passes an out-of-range IRQ number. This assertion exists because `irq.0 >= 1020` would compute a register offset outside the distributor MMIO window, producing a hardware fault.

`FakeIrqController::enable` and `disable` insert/remove from a `HashSet<IrqNumber>` unconditionally. An `IrqNumber(1023)` — the GIC's spurious-interrupt sentinel — or `IrqNumber(u32::MAX)` would be silently accepted.

**Fidelity risk:** Kernel code under test that accidentally constructs an out-of-range `IrqNumber` (a logic bug in interrupt number calculation) would pass on the host but panic on real hardware. The test would give false confidence.

**Suggested fix:** Add a range assertion to `FakeIrqController::enable` and `disable` matching the GIC's upper bound, with a doc-note explaining this mirrors the real BSP's contract. The constant should be imported or mirrored:
```rust
/// Architectural maximum INTID; mirrors `QemuVirtGic::GIC_MAX_IRQ`.
/// Any enable/disable call above this panics, matching real-hardware behavior.
const FAKE_MAX_IRQ: u32 = 1020;

fn enable(&self, irq: IrqNumber) {
    assert!(
        irq.0 < FAKE_MAX_IRQ,
        "FakeIrqController::enable: IrqNumber({}) exceeds architectural max {}",
        irq.0,
        FAKE_MAX_IRQ,
    );
    self.locked().enabled.insert(irq);
}
```
Add a corresponding test that confirms the assertion fires.

---

#### C8-005 — `VecFrameProvider` does not enforce the zero-initialized-frame contract

**File:** `test-hal/src/mmu.rs:14–36`

**Description:**
The `FrameProvider` trait (`hal/src/mmu/mod.rs:204–208`) states:
> `alloc_frame` — Allocate a **zero-initialized** `PhysFrame`.

The real `Pmm::alloc_frame` (`kernel/src/mm/pmm.rs:311–430`) zero-fills the frame before returning it, and this is verified by the test `alloc_frame_returns_first_free_and_zeroes_payload`. `VecFrameProvider::alloc_frame` simply pops from a `Vec<PhysFrame>` of pre-constructed frames; the frame addresses point to physical memory in the host address space, and the `PhysFrame` type carries no actual byte content — it is purely a typed address.

**Fidelity risk:** In the fake context, `FakeMmu` never dereferences the physical address, so the zero-fill contract is vacuously satisfied for `FakeMmu`-based tests. However, any kernel code or integration test that uses `VecFrameProvider` with a fake that *does* read frame contents (e.g., a future fake that walks a simulated page-table tree) would get non-zero content from `VecFrameProvider` without warning. The current doc-comment on `VecFrameProvider` makes no mention of this deviation from the contract.

**Suggested fix:** Add a doc-note to `VecFrameProvider`:
> **Contract note:** `VecFrameProvider` does not zero-fill returned frames. The `FrameProvider::alloc_frame` contract requires zero-initialized frames; this fake satisfies that contract vacuously because `FakeMmu` never dereferences the physical address. If used with a fake that reads frame contents, the caller is responsible for ensuring the frames were zero-initialized before insertion.

---

### Nit

#### C8-006 — Test function names do not follow the project's `test_<subject>_<condition>_<expected_outcome>` convention

**File:** All five test modules, e.g. `test-hal/src/mmu.rs:214`, `test-hal/src/cpu.rs:125`, `test-hal/src/irq_controller.rs:117`, `test-hal/src/timer.rs:116`, `test-hal/src/console.rs:74`

**Description:**
`docs/standards/testing.md` prescribes the naming pattern:
```
test_<subject>_<condition>_<expected_outcome>
```
Examples: `test_endpoint_send_with_no_receiver_returns_no_receiver`.

The test-hal tests use a shorter, subject-first pattern without the `test_` prefix, e.g.:
- `mapping_flags_union_and_contains`
- `default_cpu_reports_core_zero_with_irqs_enabled`
- `enable_marks_line_as_enabled`
- `new_starts_at_zero_with_given_resolution`

These names are generally readable, but they deviate from the convention. This inconsistency with the kernel test files (which also use shorter names) suggests the convention is not yet uniformly enforced, but it is a policy divergence worth flagging.

**Suggested fix:** Align with the declared convention when next touching these files. The kernel tests in `kernel/src/sched/mod.rs` and `kernel/src/mm/address_space.rs` already use the shorter form, so this is a project-wide consistency nit rather than a test-hal-exclusive issue.

---

#### C8-007 — `FakeTimer::advance` uses `saturating_add` but `set_now` does not guard against overflow; semantics differ

**File:** `test-hal/src/timer.rs:43–55`

**Description:**
`advance` uses `saturating_add` to prevent clock overflow:
```rust
state.now_ns = state.now_ns.saturating_add(delta_ns);
```
`set_now` assigns directly:
```rust
self.locked().now_ns = ns;
```
This is intentional and correct for `set_now` (no arithmetic involved), but the difference is undocumented. A test author reading `advance` may assume overflow is impossible and write `set_now(u64::MAX)` without considering that a subsequent `advance` will saturate (yielding `u64::MAX` + anything = `u64::MAX`). The `Timer::now_ns` contract is monotonic; `set_now(u64::MAX)` followed by any `advance` call will not violate monotonicity (it stays at `u64::MAX`), but the saturation behavior is worth a brief doc note on `advance`.

**Suggested fix:** Add one sentence to `advance`'s doc-comment:
> Saturates at `u64::MAX` rather than wrapping; `now_ns` is monotonic across both `advance` and `set_now`.

---

#### C8-008 — `FakeMmu::map` accepts a `_frames` parameter it silently ignores

**File:** `test-hal/src/mmu.rs:154`

**Description:**
The parameter is named `_frames` (underscore prefix) to suppress the unused-variable lint. This is a valid Rust idiom, but a caller who passes a `VecFrameProvider` with frames remaining may be surprised that `map` never consumes any of them — the `FakeMmu` never allocates intermediate page-table frames regardless of how many frames are available. Currently the test `map_unmap_round_trip` passes a `VecFrameProvider` with one frame that is never consumed (line 267–268), which is consistent with the fake's behavior but potentially confusing.

The comment at line 154 (`_frames: &mut dyn FrameProvider`) has no explanatory note about why frames are not consumed.

**Suggested fix:** Rename the parameter and add a brief comment:
```rust
// `frames` is accepted for trait-signature compatibility but not consumed:
// FakeMmu uses a flat HashMap and has no intermediate page-table structure
// to allocate. See C8-002 in the master-review track for the fidelity note.
_frames: &mut dyn FrameProvider,
```

---

#### C8-009 — `lib.rs` doc-comment references ADR-0007 through ADR-0011 but `ContextSwitch` fake is absent from the crate

**File:** `test-hal/src/lib.rs:18–21`

**Description:**
The crate doc-comment states:
> All five Phase 4b HAL traits now have fakes: `FakeConsole` (ADR-0007), `FakeCpu` (ADR-0008), `FakeMmu` (ADR-0009), `FakeTimer` (ADR-0010), `FakeIrqController` (ADR-0011).

The `tyrne_hal` crate exposes a sixth accepted trait, `ContextSwitch` (ADR-0020), for which there is no fake in `tyrne-test-hal`. The scheduler's unit tests in `kernel/src/sched/mod.rs` work around this by defining an inline `FakeCpu` that implements both `Cpu` and `ContextSwitch`. This is a minor inconsistency with the "all HAL traits have fakes" claim in the lib doc and creates a maintenance burden (two independent FakeCpu implementations that can drift).

This is a Nit in isolation, but it has a minor cross-track implication: the scheduler's inline `FakeCpu` does not track `disable_irqs` / `restore_irq_state` state the way `tyrne_test_hal::FakeCpu` does, so tests using the inline fake cannot assert on IRQ-state changes.

**Suggested fix:** Either update the doc-comment to note that `ContextSwitch` is not yet faked (because it requires assembly and a real stack, making a host fake awkward), or add a `FakeContextSwitch` that records `context_switch` call count and `init_context` invocations without actually switching stacks. At minimum, file a tracking issue and link it from the doc-comment.

---

### Praise

#### C8-P01 — Excellent fidelity on alignment and invalid-flag rejection in `FakeMmu`

`FakeMmu::map` and `FakeMmu::unmap` both correctly reject unaligned VAs with `MmuError::MisalignedAddress`, and `FakeMmu::map` correctly rejects `DEVICE | EXECUTE` with `MmuError::InvalidFlags`. The PR #23 review-round comments at lines 159 and 163–170 are well-placed and explain the specific contract parity each check provides. This demonstrates exactly the right pattern for a fake: reject what the real implementation would reject, so kernel code that passes bad inputs fails on the host just as it would on hardware. The associated tests (`map_rejects_unaligned_va`, `unmap_rejects_unaligned_va`, `map_rejects_device_plus_execute`) are concise and pin the contract precisely.

---

#### C8-P02 — `MapperFlush` token discipline fully exercised

The `must_use` token-discharge discipline (flush vs. ignore) is exercised by seven distinct tests in `test-hal/src/mmu.rs:350–480`. The tests are notably thorough: they separately pin the semantics of `flush` (invokes `invalidate_tlb_address`), `ignore` (does not), the carried virtual address, the bulk-map-then-invalidate-all pattern, and the map/unmap return value's VA. This suite provides strong regression coverage for the `MapperFlush` type that lives in `tyrne_hal` and is exercised by all downstream consumers.

---

## Claims register

| Claim | Source file:line | How to verify |
|-------|-----------------|---------------|
| FakeMmu mirrors `QemuVirtMmu::map`'s rejection of unaligned VA | `test-hal/src/mmu.rs:158–161` | `test-hal` test `map_rejects_unaligned_va`; compare with `bsp-qemu-virt/src/mmu.rs:210` |
| FakeMmu mirrors `QemuVirtMmu::map`'s rejection of `DEVICE\|EXECUTE` | `test-hal/src/mmu.rs:163–171` | `test-hal` test `map_rejects_device_plus_execute`; compare with `bsp-qemu-virt/src/mmu.rs:224` |
| FakeMmu models `AlreadyMapped` on double-map | `test-hal/src/mmu.rs:172–174` | `test-hal` test `double_map_returns_already_mapped`; compare with `bsp-qemu-virt/src/mmu.rs:437–438` |
| FakeMmu models `NotMapped` on unmap of unmapped VA | `test-hal/src/mmu.rs:189–192` | `test-hal` test `unmap_missing_returns_not_mapped`; compare with `bsp-qemu-virt/src/mmu.rs:421–423` |
| FakeMmu records per-address and all-TLB invalidations separately | `test-hal/src/mmu.rs:68–71` | `test-hal` test `tlb_invalidations_recorded_in_order` |
| FakeCpu correctly implements IrqGuard nesting (restore outer on inner drop) | `test-hal/src/cpu.rs:158–172` | `test-hal` test `nested_irq_guards_restore_outer_state`; same logic exercised by `hal/src/cpu.rs:118–122` |
| FakeIrqController `acknowledge` is FIFO (models GIC IAR behavior) | `test-hal/src/irq_controller.rs:102–104` | `test-hal` test `acknowledge_returns_pending_fifo` |
| FakeTimer `advance` saturates at `u64::MAX` | `test-hal/src/timer.rs:44–45` | `test-hal` test `advance_moves_clock_forward` (does not test saturation edge); no test for `saturating_add` at `u64::MAX` — gap |
| FakeConsole captures bytes across multiple writes | `test-hal/src/console.rs:59–64` | `test-hal` test `captures_successive_byte_writes` |
| `FakeMmu::create_address_space` body does not dereference `root` | `test-hal/src/mmu.rs:133–137` (impl body comment at call sites) | Read function body directly; `root` is only stored, not dereferenced |
| `VecFrameProvider` frames are zero-initialized (claimed vacuously) | `test-hal/src/mmu.rs:9–30` | **UNVERIFIED** — `VecFrameProvider` does not zero frames; contract satisfied only vacuously because `FakeMmu` never dereferences physical addresses |
| `FakeIrqController::enable` is idempotent | `test-hal/src/irq_controller.rs:94–96` (HashSet insert) | `test-hal` test `enable_is_idempotent` |

---

## Cross-track notes

### Route to test-coverage view
- **C8-002 (OutOfFrames from map):** The `task_loader` tests exercise `OutOfFrames` via PMM exhaustion, not via intermediate-table allocation in `Mmu::map`. A cross-track note for the C-test-coverage reviewer: the `MmuError::OutOfFrames` path in `QemuVirtMmu::map` (`bsp-qemu-virt/src/mmu.rs:510`) has no host-side test exercising it. This is a coverage gap in the BSP.
- **C8-003 (BlockMapped):** The `cap_unmap` wrapper in `kernel/src/mm/address_space.rs:779` propagates `MmuUnmapError(BlockMapped)`, but there is no test that injects this error through a fake. The pattern-match arm for `BlockMapped` in any kernel code that destructures `MmuUnmapError` is dead under host tests.
- **C8-004 (IrqNumber range):** The kernel's interrupt-number construction paths are untested for out-of-range values; this gap is inherited from the fake not asserting the bound.

### Route to code-to-code (unsafe) pass
- **C8-001 (missing Safety doc and audit entry for `create_address_space`):** The unsafe policy requires an audit-log entry. This is an omission in `docs/audits/unsafe-log.md`; no entry for `FakeMmu::create_address_space` exists as of commit 288ddb2.
- The `create_address_space` unsafe at `kernel/src/mm/address_space.rs:640` documents its invariants thoroughly and references UNSAFE-2026-0026. The corresponding fake's unsafe fn should be in the same audit chain.

### Duplicate FakeCpu concern
The kernel's scheduler tests define their own inline `FakeCpu` (at `kernel/src/sched/mod.rs:1252`) that implements both `Cpu` and `ContextSwitch` as no-ops. This duplicates `tyrne_test_hal::FakeCpu` for the `Cpu` surface while adding `ContextSwitch`. The two implementations can drift: the inline `FakeCpu` does not track `irqs_enabled` state. Any scheduler test that exercises IRQ-guard behavior during a context switch would not catch a correctness bug in interrupt masking. This is a maintenance hazard that a `FakeContextSwitch` in `tyrne-test-hal` would close.

---

## Coverage checklist

All seven files read in full. Line counts are as of commit 288ddb2.

- [x] `test-hal/src/mmu.rs` — 539 lines
- [x] `test-hal/src/cpu.rs` — 190 lines (191 with trailing newline)
- [x] `test-hal/src/irq_controller.rs` — 189 lines (190 with trailing newline)
- [x] `test-hal/src/timer.rs` — 175 lines (176 with trailing newline)
- [x] `test-hal/src/console.rs` — 94 lines (95 with trailing newline)
- [x] `test-hal/src/lib.rs` — 32 lines (33 with trailing newline)
- [x] `test-hal/Cargo.toml` — 18 lines

Related context files also read (not part of the 7-file track but necessary for fidelity analysis):
- `hal/src/mmu/mod.rs` (full trait contract and `MapperFlush` shape)
- `hal/src/cpu.rs` (full `Cpu` + `IrqGuard` + `IrqState` surface)
- `hal/src/irq_controller.rs` (full `IrqController` contract)
- `hal/src/timer.rs` (full `Timer` contract)
- `hal/src/console.rs` (full `Console` contract)
- `bsp-qemu-virt/src/mmu.rs` (real `QemuVirtMmu` implementation for fidelity comparison)
- `bsp-qemu-virt/src/gic.rs` (real `QemuVirtGic` for `IrqNumber` range contract)
- `kernel/src/mm/address_space.rs` (kernel consumer of `FakeMmu`)
- `kernel/src/obj/task_loader.rs` (kernel consumer of `FakeMmu` + `VecFrameProvider`)
- `docs/audits/unsafe-log.md` (to check for existing audit entries covering test-hal)
- `docs/standards/testing.md`, `unsafe-policy.md`, `code-review.md`, `code-style.md`
