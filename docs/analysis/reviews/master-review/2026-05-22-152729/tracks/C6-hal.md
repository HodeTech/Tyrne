# C6-hal — hardware abstraction layer (master review, commit 288ddb2)

Track C6 reviews the `tyrne-hal` crate: the trait surface that realises architectural
principle **P6 (HAL separation)** plus two clusters of pure, host-testable arithmetic
that every aarch64 BSP shares — the VMSAv8 page-table descriptor encoders
(`mmu/vmsav8.rs`) and the tick/ns timer helpers (`timer.rs`). Eight files, 1 971 lines.

The two concrete implementors (`bsp-qemu-virt`, `test-hal`) were read in full to judge
trait fitness, and the governing ADRs (0007–0011, 0020, 0027) plus `docs/architecture/hal.md`
were cross-checked for contract accuracy.

## Summary

The HAL is in excellent shape and is the strongest-engineered subsystem reviewed so far.
The trait surface is narrow, object-safe where it must be, and generic where an associated
type is genuinely needed (`Mmu::AddressSpace`, `ContextSwitch::TaskContext`). Every `unsafe`
item carries a conforming `# Safety` section and an audit tag. The two pure-arithmetic
modules are exemplary: the descriptor encoders match ADR-0027 §Decision-outcome bit-for-bit
(I verified MAIR/TCR/SCTLR values, the AP/SH/AttrIdx/PXN/UXN table, and the OA masks against
the ARM ARM and the ADR §Simulation rows), and the timer helpers handle the saturation /
round-to-nearest / ceiling-division edge cases with property-style tests. Trait fitness is
confirmed by construction: `bsp-qemu-virt` consumes `block_descriptor` (bootstrap),
`page_descriptor` + `table_descriptor` (post-bootstrap `map`), and all timer helpers, while
`test-hal` implements every trait with deterministic fakes that mirror the real contracts
(VA-alignment + `DEVICE|EXECUTE` rejection were back-ported into `FakeMmu` so host tests
catch the same misuse hardware would).

The findings are dominated by **documentation/contract accuracy**, not behaviour. The one
finding I rate **Major** is a genuine trait-contract gap: `ContextSwitch`'s safety contract
enumerates the aarch64 callee-saved set but **omits the SIMD/FP registers `d8`–`d15`**, which
a correct AAPCS64 implementation must also save (and which the QEMU BSP *does* save). A second
BSP author who implements to the enumerated list literally would ship a context switch that
corrupts FP state across a yield — exactly the class of subtle, load-late bug the HAL's
trait contracts exist to prevent. Everything else is Minor/Nit.

No blocker. No memory-safety defect. No P5/P6 violation (the crate is `#![no_std]`, traits-only
plus pure helpers, zero hardware addresses, zero board names).

Severity counts: Blocker 0 · Major 1 · Minor 6 · Nit 6 · Praise 5.

## Findings (by severity)

### Major

#### C6-001 — `ContextSwitch` safety contract omits `d8`–`d15` from the "all callee-saved registers" enumeration
`hal/src/context_switch.rs:19-24` (and the duplicate at `:36-39`)

The trait-level safety contract reads:

> Implementations must ensure that `context_switch` atomically saves all callee-saved
> registers of the current execution context and restores all callee-saved registers of
> the next context. On aarch64 that is `x19`–`x28`, `x29` (fp), `x30` (lr), and `sp`.

This enumeration is **incomplete**. Per AAPCS64, the SIMD/FP callee-saved set — the lower
64 bits of `v8`–`v15` (i.e. `d8`–`d15`) — must also be preserved across a call whenever
FP is enabled. The QEMU BSP's own implementation knows this: `Aarch64TaskContext` includes
`d8_d15: [u64; 8]` and `context_switch_asm` saves/restores them, with an explicit comment
("d8–d15 must be saved whenever `CPACR_EL1.FPEN` is non-zero … the compiler may allocate
those registers for any kernel-level task and will not emit callee-save spills across a
cooperative yield" — `bsp-qemu-virt/src/cpu.rs:299-301`). So the *normative prose that
defines the contract* contradicts the *only correct implementation of it*.

**Why it matters.** The trait's `# Safety` section is the contract a future BSP author
(Pi 4, Pi 5, Jetson, the second aarch64 lineage that the whole HAL exists to enable)
implements against. Someone reading `context_switch.rs` and saving exactly the four listed
classes would produce a context switch that silently clobbers `d8`–`d15` on every yield.
The failure is data-dependent (only manifests when the compiler has live FP callee-saved
state across a `context_switch` call), so it survives smoke tests and surfaces as rare,
near-undebuggable corruption — the precise hazard the project's "trait contracts must be
implementable correctly across boards" discipline targets. The same omission is in
ADR-0020 §Safety contract (line 165) and in the ADR's `Aarch64TaskContext` sketch (which
predates the BSP adding the FP fields), so this is a contract that drifted from its
implementation and was never reconciled.

**Suggested fix.** Amend both occurrences in `context_switch.rs` to read "… that is the
general-purpose callee-saved registers `x19`–`x28`, `x29` (fp), `x30` (lr), `sp`, **and the
SIMD/FP callee-saved registers `d8`–`d15` (the lower 64 bits of `v8`–`v15`) whenever FP is
enabled (`CPACR_EL1.FPEN ≠ 0`)**." Optionally generalise the per-arch enumeration to "the
target ABI's full callee-saved register set" so the contract is not aarch64-specific in a
crate that intends to grow a RISC-V lineage. Add an Amendment rider to ADR-0020 recording
that the FP set was added with the T-012-era BSP impl and the contract text now matches.
This is a doc-only change to the track file, but it closes a real cross-board correctness
gap; flag for security/second review per the boot-path + `unsafe` gate.

### Minor

#### C6-002 — `Mmu::map`'s `InvalidFlags` contract cites a case no implementor produces (and the type system permits)
`hal/src/mmu/mod.rs:400-401`

The `# Errors` doc says `InvalidFlags` is returned "if `flags` cannot be applied (for
example, **user + kernel-only combinations**)." No such combination exists in `MappingFlags`
(the five flags are `WRITE`/`EXECUTE`/`USER`/`DEVICE`/`GLOBAL`; there is no "kernel-only"
flag — kernel-only is the *absence* of `USER`), and neither implementor ever returns
`InvalidFlags` for anything but `DEVICE | EXECUTE`. So the one concrete example the contract
gives is unrepresentable, while the case both implementors actually reject (`DEVICE|EXECUTE`,
`bsp-qemu-virt/src/mmu.rs:224-226`, `test-hal/src/mmu.rs:169-171`) is **not** named in the
trait doc at all. A safe kernel caller reading the trait cannot know that `DEVICE|EXECUTE`
will fail.

**Why.** `InvalidFlags` is part of the `unsafe`-free safety contract callers route error
handling against; an example that cannot occur plus a real case that is undocumented makes
the contract actively misleading. **Fix.** Replace the "user + kernel-only" example with the
real rule: "Returned when `flags` requests an unrepresentable combination — in v1, any
mapping with both `DEVICE` and `EXECUTE` set, because MMIO is never executable
(ADR-0027 §Decision outcome (b))." Consider hoisting the `DEVICE|EXECUTE` rejection into a
shared `MappingFlags::validate()` helper in the HAL so the rule lives once instead of being
copy-pasted into every BSP + the fake (it is currently duplicated in three places).

#### C6-003 — `flags_to_descriptor_bits` silently ignores unknown / out-of-range `MappingFlags` bits
`hal/src/mmu/vmsav8.rs:252-310`, in concert with `MappingFlags::from_raw` (`mmu/mod.rs:110-112`)

`from_raw(bits: u32)` accepts any 32-bit pattern; `flags_to_descriptor_bits` only consults
the five defined bits via `contains`, so a value with bits ≥ 5 set (or a typo'd raw constant
crossing an ABI boundary, the documented use case for `from_raw`) is silently coerced — the
unknown bits vanish with no error. Given the encoders are the security-critical translation
from kernel intent to actual page permissions, a "garbage in → plausible-looking descriptor
out" path is a latent footgun.

**Why.** Defence-in-depth at the permission-encoding boundary is cheap and the project's
security-first posture argues for it. **Fix.** Either document explicitly on `from_raw` and
on `flags_to_descriptor_bits` that bits outside the known set are ignored by design, or add
a `MappingFlags::is_valid()` / mask check that the BSP `map` path can assert. At minimum add
a const `MappingFlags::ALL`/mask and a unit test asserting `flags_to_descriptor_bits` is
insensitive to bits ≥ 5 (locks the chosen behaviour either way).

#### C6-004 — `block_descriptor` / `page_descriptor` "garbage in, garbage out" unaligned-PA contract is a sharp edge for the security-critical encoder
`hal/src/mmu/vmsav8.rs:314-334` (block), `:336-353` (page)

Both encoders mask the PA into the OA field (`pa & BLOCK_OA_MASK_L2` / `pa & PAGE_OA_MASK_L3`),
silently dropping low bits when the caller passes an unaligned address; the doc says
alignment "is expected to be validated upstream." For `page_descriptor` the BSP does feed it
a `PhysFrame` (alignment-guaranteed by the newtype), so that call site is safe. But
`block_descriptor` takes a raw `u64` and the bootstrap caller passes raw `va`/`pa` integers
(`mmu_bootstrap.rs:146,165`) with no `PhysFrame` gate — the only protection is the loop
arithmetic happening to be 2 MiB-aligned. A future block-mapping caller that computes an
unaligned base would get a descriptor pointing at a *different* physical frame than intended,
with no diagnostic.

**Why.** Silent address truncation in a page-table encoder is a memory-safety-adjacent
hazard (it maps the wrong physical page). **Fix.** Either accept `PhysFrame` (and a typed
2 MiB-block frame) instead of raw `u64` so the type system enforces alignment, or add a
`debug_assert!(pa & !MASK == ... )` style alignment check in the encoders. If the
garbage-in/garbage-out contract is deliberate for `const fn` reasons, strengthen the doc to
say the truncation is *silent and can map the wrong frame*, not merely that validation lives
upstream.

#### C6-005 — `MapperFlush` does not bind the minting `Mmu`/`AddressSpace`, so a token can be flushed against the wrong instance
`hal/src/mmu/mod.rs:230-233, 279-281`

`MapperFlush::flush<M: Mmu + ?Sized>(self, mmu: &M)` accepts *any* `Mmu`, and the token
carries only a `VirtAddr` — not the address space it was minted for. The doc acknowledges
this ("does not bind the minting `Mmu` instance … v1 has a single `Mmu` instance so the
absence of an instance-identity check is harmless; future multi-CPU / multi-address-space
topologies may grow the shape"). It is correctly flagged, so this is Minor, but it is a
real future-soundness cliff: once there is more than one address space, flushing a token
from AS-A against AS-B invalidates the wrong TLB entry, and nothing in the type system
prevents it.

**Why.** TLB-invalidation is the discipline `MapperFlush` exists to enforce; a token that
can target the wrong AS quietly defeats the discipline in exactly the multi-AS world the
token is meant to scale to. **Fix (track-level: record, do not implement now).** Note in the
roadmap/ADR-0027 follow-up that the multi-AS step must add an AS/ASID discriminant to
`MapperFlush` (e.g. a `PhantomData<AS-id>` or a stored ASID) and make `flush` reject a
mismatch. Acceptable to defer for v1; the finding is that the cliff should be a tracked item,
not only a doc aside.

#### C6-006 — Timer-helper `# Panics` (divide-by-zero on `frequency_hz == 0`) is sound, but the panic lives in a `const fn` reachable from non-init runtime callers
`hal/src/timer.rs:94-106, 136-153, 198-213`

`ticks_to_ns` / `ns_to_ticks` / `resolution_ns_for_freq` `assert!` on zero frequency. The
reasoning is documented and the BSP validates `CNTFRQ_EL0 != 0` at construction
(`bsp-qemu-virt/src/cpu.rs:178-181`), so the asserts are unreachable in production. However,
`ticks_to_ns` is on `Timer::now_ns`'s hot path (called on every `now_ns`) and `error-handling.md`
§4 forbids panics outside one-shot init on kernel/HAL paths. The mitigation here is that the
frequency is validated once and cached, so `now_ns` cannot actually trip the assert — but the
*helper* is `pub` and a future caller could pass an unvalidated frequency on a hot path. This
is a contract-shape note, not a live bug.

**Why.** Keeping panics provably-init-only is a project invariant; a `pub` panicking helper
on a hot-path-adjacent surface is worth a guard rail. **Fix.** Document on each helper that
callers must pass a frequency validated at init (the BSP pattern), or offer non-panicking
`checked_*` variants returning `Option<u64>` for any caller that cannot guarantee a non-zero
frequency at the call site. Current `assert!` form is acceptable given the cache; flag as a
known-good-with-rationale entry rather than a defect.

#### C6-007 — `docs/architecture/hal.md` `Cpu` section lists methods the trait does not have (and an obsolete `Cpu::enable_interrupts()` in the boot diagram)
`docs/architecture/hal.md:78-85, 240` vs `hal/src/cpu.rs:44-76`

The architecture doc's `Cpu` bullet list still advertises "Number of cores online",
"Secondary-core start via PSCI", and "Context save / restore primitives used by the scheduler"
as `Cpu` responsibilities, and the boot sequence diagram calls `Cpu::enable_interrupts()`.
The actual v1 `Cpu` trait has none of these: core-count and PSCI are explicitly deferred
(`cpu.rs:31-33`), context switch moved to the separate `ContextSwitch` trait per ADR-0020,
and there is no `enable_interrupts` (the trait exposes `disable_irqs` / `restore_irq_state`).
The doc is partly hedged ("Treat the bullet points as responsibilities, not the final
signature") but the boot diagram presents `enable_interrupts()` as a concrete call.

**Why.** `hal.md` is the canonical orientation doc a new BSP author reads first; method names
that do not exist send them looking for a trait method that was deliberately deferred or
renamed. **Fix.** Reconcile the `Cpu` bullets with the shipped trait (or annotate the
deferred items as "future ADR"), and update the boot diagram's `Cpu::enable_interrupts()` to
the real shape (interrupts are unmasked via `restore_irq_state` / DAIF, and the GIC sequence,
not a `Cpu` method).

### Nit

#### C6-008 — `lib.rs` status block calls the `Iommu` trait a "remaining trait stub … placeholder" but it is the only non-ADR'd trait, and `hal.md` already commits its method shape
`hal/src/lib.rs:21-22, 52-62`

`pub trait Iommu {}` is an empty marker; the module doc frames it as a placeholder "whose
method surface will be pinned by its own ADR." Fine, but the comment says "the remaining
trait stub *below*" (singular) which is accurate today; just ensure that when the IOMMU ADR
lands the stub does not silently accrete methods without the `# Safety`/audit discipline the
rest of the crate upholds. No change needed now; flag so it is not forgotten.

#### C6-009 — `IrqState(pub usize)` and `MappingFlags`/`VirtAddr`/`PhysAddr` expose `pub` inner fields by convention-only opacity
`hal/src/cpu.rs:21-22`, `hal/src/mmu/mod.rs:29,33,83`

Several newtypes document "treat as opaque" / "not an invitation to inspect" but expose the
inner field as `pub` so BSPs can construct from raw bits. This is a deliberate, documented
trade-off (matches `MapperFlush::new`'s reasoning) and is fine for v1, but it means the
opacity is unenforced — kernel code *can* read `IrqState.0` and synthesise DAIF bits. A
`from_raw`/`as_raw` accessor pair (as `MappingFlags` already has) would let the field be
private while keeping the BSP escape hatch. Low priority; record as a consistency item
(`MappingFlags` does it right with `from_raw`/`raw`; `IrqState`/`VirtAddr`/`PhysAddr` do not).

#### C6-010 — `now_ns` re-reads `frequency_hz` field on every call; doc says it is cached but the multiply uses it each time
`hal/src/timer.rs` (helper) + `bsp-qemu-virt/src/cpu.rs:444-489`

Not a HAL-crate defect (the helper is pure), but the trait's perf-relevant contract is worth
a note: `ticks_to_ns(count, frequency_hz)` does a u128 multiply + divide on every `now_ns`.
For a monotonic-clock read on a potentially hot scheduler path, a precomputed
fixed-point `ns_per_tick` (Q32.32) multiply would avoid the per-call 128-bit divide. The
current form is correct and exact (the divide is why); flagging only as a future
optimisation the trait shape permits (the helper could gain a `ticks_to_ns_scaled(count,
ns_per_tick_q32)` companion). Defer.

#### C6-011 — `MmuError` lacks an `InvalidFlags`-style variant distinction the doc implies, and `BlockMapped` is documented only on `unmap` but reachable conceptually on `map` too
`hal/src/mmu/mod.rs:185-195, 392-401, 418-426`

`BlockMapped` is listed in `unmap`'s `# Errors` but `map`'s `# Errors` lists `AlreadyMapped`
for the block case — and the BSP confirms this asymmetry deliberately (`mmu.rs:491-498`:
`map` into a block → `AlreadyMapped`, `unmap` → `BlockMapped`). The behaviour is intentional
and well-commented in the BSP, but the *trait* doc for `map` never explains why a 2 MiB block
surfaces as `AlreadyMapped` rather than `BlockMapped`, so a reader comparing the two `# Errors`
lists sees an unexplained inconsistency. **Fix.** One sentence in `map`'s `# Errors` noting
"a `va` inside an existing large block returns `AlreadyMapped` (not `BlockMapped`): the 4 KiB
slot is structurally occupied; block-split is deferred to B3+."

#### C6-012 — Doc-link to `docs/architecture/exceptions.md` referenced from `irq_controller`/GIC but file presence not confirmable from HAL crate
`hal/src/irq_controller.rs` (ADR-0011 link) — cross-checked via `bsp-qemu-virt/src/gic.rs:18-23`

The GIC module links `docs/architecture/exceptions.md §"GIC v2 driver"`. This is a BSP file,
not a HAL file, but the HAL `IrqController` contract leans on the same EOI/ack semantics; a
reviewer verifying the HAL contract has to chase a doc the HAL crate does not reference. Minor
discoverability nit — consider citing `exceptions.md` from `irq_controller.rs`'s module doc
so the trait contract and its architectural narrative are co-located.

#### C6-013 — `current_el()` is `cfg`-gated to `target_os = "none"` only; the rich `# Safety`/audit prose lives on a function absent from the unit-test build
`hal/src/cpu.rs:164-194`

`current_el()` exists only on `aarch64 + target_os="none"`. Correct (host reads of `CurrentEL`
trap), and the doc explains it thoroughly. The nit: there is no host-side stub or
compile-time test that the function's signature/contract stays in sync with its sole caller
(`QemuVirtCpu::new`), because the function simply does not exist on the test target. A
`#[cfg(not(...))]` companion returning a mock-or-`unimplemented!` (clearly test-only) is one
option; or accept the gap as inherent. Low priority — recording for completeness.

### Praise

#### C6-P1 — VMSAv8 descriptor encoders are correct and exhaustively tested
`hal/src/mmu/vmsav8.rs`

I verified the encoders bit-for-bit against ARM ARM §D5.3 and ADR-0027 §Decision-outcome /
§Simulation: valid bit, block-vs-table bit semantics per level, `AttrIndx[2:0]`@[4:2],
`AP[2:1]`@[7:6], `SH[1:0]`@[9:8], `AF`@10, `nG`@11, `PXN`@53, `UXN`@54, `BLOCK_OA_MASK_L2`
([47:21]) and `PAGE_OA_MASK_L3` ([47:12]). The MAIR (`0x..FF00`), TCR (field-by-field
decomposition with T0SZ=16/IPS=0b010/EPD1=1/TG0=00/TG1=10) and SCTLR mask all match the ADR.
The `flags_to_descriptor_bits` "locked-shut-by-default" execute-never policy (DEVICE→PXN=UXN=1,
kernel-X→PXN=0/UXN=1, user-X→PXN=1/UXN=0, non-X→both 1) is a genuinely security-positive
default and is tested for every flag combination. This is model HAL code.

#### C6-P2 — Timer arithmetic handles the hard edges and proves it
`hal/src/timer.rs`

128-bit intermediate + saturating cast (monotonicity at the ~584-year wrap), round-to-nearest
resolution with an explicit ≥1 ns floor for >2 GHz counters, ceiling division for `ns_to_ticks`
(so the IRQ fires at-or-after the deadline, never before — correctly tied to ADR-0010's
"reaches or exceeds" wording). The property-style monotonicity sweep and the explicit
"plateau after saturation" test lock behaviour that a naive `wrapping_mul` would silently
break. The named-message panics on zero frequency are guarded by tests. Exemplary.

#### C6-P3 — `MapperFlush` `#[must_use]` flush-token discipline
`hal/src/mmu/mod.rs:211-298`

Turning "did you remember to invalidate the TLB?" from a reviewer-attention problem into a
compile error (`unused_must_use`, denied workspace-wide) is exactly the right use of the type
system for a high-assurance kernel. The `flush` / `ignore` asymmetry making the bulk-vs-single
intent explicit is a nice touch, and the soundness analysis (the token's only power is a TLB
*hint*, not a memory-safety op) is honest about what the discipline does and does not buy.

#### C6-P4 — Object-safety vs. associated-type split is principled and consistent
`hal/src/cpu.rs`, `hal/src/context_switch.rs`, `hal/src/mmu/mod.rs`

`Cpu`/`Timer`/`IrqController`/`Console` stay object-safe (`&dyn`) for the pervasive, dynamic
call sites; `Mmu` and `ContextSwitch` use associated types where the scheduler/AS-storage
genuinely needs compile-time layout, and the rationale (preserve `Cpu` object-safety; avoid
heap/type-erasure) is recorded in ADR-0009/0020 and echoed in the doc-comments. `IrqGuard`'s
choice of a concrete type parameter over `&dyn Cpu` (with the `.rodata`-aliasing rationale)
shows real care.

#### C6-P5 — `test-hal` fakes mirror the real contracts, including the failure cases
`test-hal/src/mmu.rs`, `timer.rs`, `cpu.rs`, `irq_controller.rs`, `console.rs`

The fakes are not happy-path-only: `FakeMmu` enforces VA-alignment and rejects
`DEVICE|EXECUTE` (back-ported "so kernel logic exercised on the host catches the same misuse
it would catch on hardware"), `FakeTimer` documents that it does *not* fire deadlines (and
why), `FakeIrqController` models the spurious/empty case via `pop_front → None`. This is the
behaviour the architecture doc demands ("any divergence between test-hal and QEMU is a bug in
whichever side claims to match the architecture") and it is actually delivered. The
`nested_irq_guards_restore_outer_state` test is the right test for the `IrqGuard` compose
contract.

## Claims register

Trait contracts the implementors (bsp + test-hal) must uphold; route the **bold** rows to the
code↔code contradiction pass (a normative claim that an implementor contradicts or under-honours).

| Claim | Source `file:line` | How to verify |
|---|---|---|
| **`ContextSwitch` impls save "all callee-saved registers … `x19`–`x28`, `x29`, `x30`, `sp`"** | `hal/src/context_switch.rs:21-24` | **Contradiction**: BSP impl additionally saves `d8`–`d15` (`bsp-qemu-virt/src/cpu.rs:306-319,382-390`); contract under-enumerates the AAPCS64 callee-saved set (C6-001). A literal impl would corrupt FP state. |
| **`Mmu::map` returns `InvalidFlags` for "user + kernel-only combinations"** | `hal/src/mmu/mod.rs:400-401` | **Contradiction**: unrepresentable in `MappingFlags`; both impls only reject `DEVICE|EXECUTE` (`bsp .../mmu.rs:224-226`, `test-hal/.../mmu.rs:169-171`), which the trait doc never names (C6-002). |
| `Mmu::map` on `Err` guarantees (1) no mapping at `va`, (2) `pa` not consumed, (3) intermediate frames not promised back | `hal/src/mmu/mod.rs:353-389` | Inspect `walk_and_install_leaf` (`bsp .../mmu.rs:382-449`): leaf write is last, after all fallible steps; `pa` only consumed on the success branch. Add a host test for the rollback path (kernel `task_loader` relies on (2)). |
| `Mmu::create_address_space` requires `root` zero-initialised + exclusively owned | `hal/src/mmu/mod.rs:330-335` | BSP `from_existing_root` documents the *distinct* "already-live, non-zero" contract (`bsp .../mmu.rs:97-127`); confirm callers pick the right constructor (bootstrap → `from_existing_root`; PMM-alloc → `create_address_space`). |
| `Timer::arm_deadline(deadline_ns)` is **absolute** time; arming replaces prior; past deadlines fire promptly | `hal/src/timer.rs:38-43`, ADR-0010:76 | BSP writes `CNTV_CVAL_EL0 = ns_to_ticks(deadline_ns, freq)` (absolute 64-bit compare) — `bsp .../cpu.rs:491-537`; `FakeTimer` stores last value (`test-hal/.../timer.rs:95-97`). Verify ns_to_ticks output is treated as absolute (consistent because `now_ns = ticks_to_ns(CNTVCT)`). |
| `IrqController::acknowledge` returns `None` on spurious (GIC INTID 1023) / race | `hal/src/irq_controller.rs:44-51` | GIC folds 1023 → `None` (`bsp .../gic.rs:364-376`); `FakeIrqController` returns `None` on empty queue (`test-hal/.../irq_controller.rs:102-104`). Both honour it. |
| `IrqController` enable/disable idempotent | `hal/src/irq_controller.rs:29-30` | GIC ISENABLER/ICENABLER are write-1-to-set/clear, inherently idempotent (`gic.rs:316-362`); fake uses a `HashSet` (idempotent). `enable_is_idempotent` test present. |
| `Console::write_bytes` synchronous, infallible, no-alloc, `Send+Sync` | `hal/src/console.rs:16-39` | PL011 spins on TXFF then writes DR, no heap, `unsafe impl Send/Sync` justified (`bsp .../console.rs:60-81`); `FakeConsole` captures to a `Mutex<Vec>` (host-only). |
| Helpers `panic!` on `frequency_hz == 0`; BSP must validate at boot | `hal/src/timer.rs:80-88,131-134,188-192` | BSP asserts `CNTFRQ_EL0 > 0` in `QemuVirtCpu::new` (`bsp .../cpu.rs:178-181`) so the helper assert is unreachable in prod; `should_panic` tests cover the assert itself. |
| `flags_to_descriptor_bits`: DEVICE→AttrIdx0/SH00/PXN=UXN=1; normal→AttrIdx1/SH11 | `hal/src/mmu/vmsav8.rs:252-310` | Matches ADR-0027 §Simulation row 1 (device `SH=00`, RAM `SH=11`, `AP=00`, `AF=1`, `nG=0`); 8 unit tests in-file; consumed by `mmu_bootstrap.rs:141-169` and `mmu.rs:441-442`. |
| Descriptor encoders: block bit1=0 (L2), page/table bit1=1 | `hal/src/mmu/vmsav8.rs:178-208,322-367` | Verified against ARM ARM §D5.3 and the in-file tests (`block_descriptor_*`, `page_descriptor_*`, `table_descriptor_*`); OA masks `[47:21]`/`[47:12]` correct. |
| `MappingFlags::from_raw` accepts arbitrary bits; only bits 0-4 are meaningful | `hal/src/mmu/mod.rs:105-112`, `vmsav8.rs:252-258` | Unknown bits silently ignored by `contains` (C6-003); no test locks this. Add `flags_to_descriptor_bits` insensitivity test for bits ≥ 5. |
| `MapperFlush::flush` accepts any `Mmu`; token carries only `VirtAddr` (no AS binding) | `hal/src/mmu/mod.rs:230-233,279-281` | True by signature; harmless in single-AS v1, future-unsound for multi-AS (C6-005). Verify ADR-0027 follow-up tracks adding an AS/ASID discriminant. |

## Cross-track notes

- **→ C? bsp-qemu-virt track (stale module doc, doc-accuracy):** `bsp-qemu-virt/src/cpu.rs:11-17`
  module header still states the timer deadline-arming half is "intentionally `unimplemented!()`
  until GIC + interrupt-vector-table wiring lands," but `arm_deadline`/`cancel_deadline` are
  fully implemented at `:491-561` (per ADR-0010's 2026-04-28 revision / T-012). The header
  contradicts the body. This is BSP-track, surfaced here because it concerns the `Timer`
  trait contract's realisation.
- **→ ADR-governance / docs track:** ADR-0020 §Safety contract (line 165) and its
  `Aarch64TaskContext` sketch omit `d8`–`d15` (root of C6-001); ADR-0009's `map`/`unmap`
  `# Errors` predate the `DEVICE|EXECUTE`/`InvalidFlags` rule that ADR-0027 added (root of
  C6-002). Both ADRs need an Amendment reconciling contract text with the shipped impl.
- **→ docs/architecture track:** `hal.md` `Cpu` bullet list and boot diagram drifted from the
  v1 trait (C6-007). The `Mmu` and `Timer` sections of `hal.md`, by contrast, are accurate and
  current — the drift is localised to the `Cpu` subsection and the sequence diagram.
- **→ kernel/task_loader track:** kernel's `task_loader::load_image` rollback path is named in
  `Mmu::map`'s contract (`mmu/mod.rs:378-388`) as relying on failure-guarantee (2) (`pa` not
  consumed). The contradiction pass should confirm the kernel caller actually frees the leaf
  frame on `Err` and does not also free intermediate frames (which (3) says it must not).

## Coverage checklist

- [x] `hal/src/lib.rs` (62 lines) — read in full; crate-level docs, re-exports, `Iommu` stub.
- [x] `hal/src/console.rs` (66 lines) — read in full; `Console` trait + `FmtWriter`.
- [x] `hal/src/context_switch.rs` (70 lines) — read in full; **C6-001 (Major) found here.**
- [x] `hal/src/irq_controller.rs` (59 lines) — read in full; `IrqController` + `IrqNumber`.
- [x] `hal/src/cpu.rs` (194 lines) — read in full; `Cpu`/`IrqGuard`/`IrqState`/`current_el`.
- [x] `hal/src/timer.rs` (484 lines) — read in full; `Timer` trait + tick/ns helpers + tests.
- [x] `hal/src/mmu/mod.rs` (438 lines) — read in full; `Mmu`/`MapperFlush`/`MappingFlags`/types.
- [x] `hal/src/mmu/vmsav8.rs` (588 lines) — read in full; descriptor encoders + consts + tests.

Context read for trait-fitness/contract verification (not part of the 8-file count):
`docs/architecture/hal.md`; ADR-0009, 0010, 0020, 0027 (and indices of 0007/0008/0011);
lenses code-review / architectural-principles / unsafe-policy / error-handling / testing /
code-style; implementors `bsp-qemu-virt/src/{mmu.rs, mmu_bootstrap.rs, cpu.rs, gic.rs,
console.rs}` and `test-hal/src/{mmu.rs, timer.rs, cpu.rs, irq_controller.rs, console.rs}`;
plus a workspace-wide ripgrep of every vmsav8 encoder, MAIR/TCR/SCTLR const, and timer helper
to confirm each shared helper has a live consumer (no dead-encoder findings).
