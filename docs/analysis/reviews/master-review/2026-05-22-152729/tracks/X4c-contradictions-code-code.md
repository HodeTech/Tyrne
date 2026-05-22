# X4c — code ↔ code contradictions (master review, commit 288ddb2)

Scope: contradictions and inconsistencies **within the code**, across crates and
modules — HAL trait surface (`hal/src/**`) vs its two implementors
(`bsp-qemu-virt/src/**`, `test-hal/src/**`), kernel↔HAL contract drift, divergent
duplicated logic, and the same constant encoded differently in multiple files.
Every row below was verified by opening **both** sides; file:line is cited on each.

Method: read the feeding Wave-2 tracks (C2, C4, C5, C6, C7, C8), then re-derived
each candidate against the live sources, and ran workspace-wide ripgrep for shared
constants (`PAGE_SIZE`/`4096`, `ENTRIES_PER_TABLE`/`512`, the VMSAv8 shifts
`21/30/39/12`, the timer IRQ `27`, `GIC_MAX_IRQ`/`1020`/`1023`, `IrqState`).

This pass reports **contradictions only**. Where the conflict is purely
doc-vs-doc or doc-vs-ADR, it is routed to X4a (trait-contract doc fixes) rather
than restated as a code defect. Soundness consequences are routed to X1.

## Summary (confirmed inconsistencies by severity)

| Severity | Count | IDs |
|---|---|---|
| Blocker | 0 | — |
| Major | 3 | X4c-001 (ContextSwitch d8–d15 trait↔impl), X4c-002 (`IrqState` encoding means opposite things in the two `Cpu` impls), X4c-003 (FakeMmu cannot produce `OutOfFrames`/`BlockMapped` — fake contradicts the real `Mmu` failure contract the kernel rollback rides on) |
| Minor | 6 | X4c-004 (`InvalidFlags` doc cites an unrepresentable case; real `DEVICE\|EXECUTE` case unnamed), X4c-005 (no `ContextSwitch` fake → duplicated, drifting inline `FakeCpu`), X4c-006 (`ENTRIES_PER_TABLE` defined twice with different definitions; "512 entries / 4 KiB frame" encoded in ≥4 places), X4c-007 (VMSAv8 shift constants duplicated kernel↔BSP with conflicting level *names*), X4c-008 (`VecFrameProvider` violates the `FrameProvider` zero-fill contract the BSP walker depends on), X4c-009 (FakeIrqController omits the `GIC_MAX_IRQ` range guard the BSP asserts) |
| Nit | 5 | X4c-010 (timer IRQ `27` encoded twice, two types), X4c-011 (`TaskStack` hard-codes `4096` instead of `PAGE_SIZE`), X4c-012 (RAM-extent size encoded two ways; `ENTRIES_PER_TABLE / 8` overloaded to mean "64 RAM blocks"), X4c-013 (`Scheduler::new` doc says "zero-initialised" but uses `Default`, and BSP `init_context` silently depends on `Default == zero`), X4c-014 (`FakeTimer::set_now` can move the clock backwards, contradicting the `now_ns` monotonic contract) |
| Praise | 2 | X4c-P1, X4c-P2 |

Most serious trait-vs-impl divergence: **X4c-001** — the `ContextSwitch` safety
contract enumerates the aarch64 callee-saved set but omits `d8`–`d15`, while the
only correct implementor (the QEMU BSP) saves them. A second BSP author
implementing the contract literally would ship a context switch that silently
corrupts FP state across a cooperative yield.

---

## Contradiction register

| ID | Topic | SIDE A (file:line) | SIDE B (file:line) | Nature of conflict | Severity | Suggested fix |
|---|---|---|---|---|---|---|
| **X4c-001** | `ContextSwitch` callee-saved set: contract under-enumerates vs impl | Trait `# Safety` contract: "all callee-saved registers … `x19`–`x28`, `x29` (fp), `x30` (lr), and `sp`" — `hal/src/context_switch.rs:18-24` (the only register list in the contract) | BSP saves the GP set **plus `d8`–`d15`**: struct field `d8_d15: [u64;8]` `bsp-qemu-virt/src/cpu.rs:315-318`; asm `stp d8,d9…d14,d15` `cpu.rs:382-385`; restore `cpu.rs:387-390`; rationale comment `cpu.rs:295-301` | Normative trait prose contradicts its only correct implementation. The contract is what a *second* BSP (Pi 4/5, Jetson) implements against; saving exactly the four listed classes corrupts `d8`–`d15` on every yield whenever the compiler has live FP callee-saved state. Data-dependent → survives smoke tests. | **Major** | Amend both occurrences in `context_switch.rs` to add "and the SIMD/FP callee-saved registers `d8`–`d15` (lower 64 bits of `v8`–`v15`) whenever FP is enabled (`CPACR_EL1.FPEN ≠ 0`)", or generalise to "the target ABI's full callee-saved set". Reconcile ADR-0020. (Doc fix → X4a; soundness of a literal 2nd impl → X1.) |
| **X4c-002** | `IrqState.0` encoding means **opposite** things in the two `Cpu` implementors | BSP: `IrqState.0` is the **raw DAIF** value — `IrqState(daif)` `bsp-qemu-virt/src/cpu.rs:240-256`, restored via `msr daif,{}` `cpu.rs:259-266`. DAIF bits *set* = masked, so `IrqState(0)` = **interrupts enabled**. Kernel doc bakes this in: "tasks begin … **masked** (DAIF = 0xF) … must call `cpu.restore_irq_state(IrqState(0))`" `kernel/src/sched/mod.rs:636-638` | test-hal `FakeCpu`: `IrqState.0` is a **boolean** — `IrqState(usize::from(state.irqs_enabled))` `test-hal/src/cpu.rs:101`, restored as `irqs_enabled = state.0 != 0` `cpu.rs:107`. So `IrqState(0)` = **interrupts disabled** (the opposite). | The same literal `IrqState(0)` means "enabled" against the BSP and "disabled" against `tyrne_test_hal::FakeCpu`. The trait documents the value as opaque (`hal/src/cpu.rs:14-20`), so synthesising it is out-of-contract — yet the scheduler doc recommends exactly that synthesis with the DAIF meaning. Any future host test that drove the `restore_irq_state(IrqState(0))` enable-path against the real `tyrne_test_hal::FakeCpu` would assert the inverse of production behaviour. Masked today only because the scheduler's *inline* fakes make `restore_irq_state` a no-op (`sched/mod.rs:1272,1922`). | **Major** | Either (a) make the contract concrete enough that both impls agree on a canonical encoding (e.g. "0 = the state with IRQs unmasked"), or (b) forbid synthesising `IrqState` literals in kernel docs/code and have the scheduler obtain an "IRQs-enabled" token from the `Cpu` impl. At minimum, fix `tyrne_test_hal::FakeCpu` to use the DAIF-compatible polarity so a shared fake cannot invert the BSP. (Soundness/contract → X1 + X4a.) |
| **X4c-003** | `FakeMmu` can never return `OutOfFrames` or `BlockMapped`; contradicts the real `Mmu` failure-semantics contract | Trait promises `OutOfFrames` (mid-walk frame exhaustion) and `BlockMapped`, with a **load-bearing failure contract** clauses (1)-(3) `hal/src/mmu/mod.rs:353-399, 423-426`; BSP produces both: `OutOfFrames` at `bsp-qemu-virt/src/mmu.rs:510`, `BlockMapped` at `mmu.rs:493-497` | `FakeMmu::map` takes `_frames` and **never calls `alloc_frame`** `test-hal/src/mmu.rs:154,148-177` (flat `HashMap`, no intermediate tables) → cannot return `OutOfFrames`; `FakeMmu::unmap` `mmu.rs:179-193` returns only `NotMapped`/`MisalignedAddress` → never `BlockMapped` | The fake silently under-honours the contract every kernel test exercises. The `task_loader` rollback path frees the leaf frame on `Err` **relying on clause (2)** (`kernel/src/obj/task_loader.rs:682-691`), and `cap_map` rides clauses (2)/(3) (`kernel/src/mm/address_space.rs:719-737`) — but the mid-walk `OutOfFrames` path that exercises that split is untestable through the fake (the loader's `OutOfFrames` tests drive PMM exhaustion, a different mechanism). The fake therefore *claims* to mirror `Mmu` but cannot reproduce two of its error variants. | **Major** | Add a frame-consuming decorator fake (or extend `FakeMmu` to pull from the provider and return `OutOfFrames` when empty), and a `BlockMapped`-injecting fake; pin `cap_map`/`load_image` against them. Document the intrinsic gap on the `FakeMmu` struct doc. (Coverage → X1/test-view; the contradiction is fake↔real contract.) |
| **X4c-004** | `Mmu::map` `InvalidFlags` doc cites an unrepresentable case; the real rejected case is unnamed | Trait `# Errors`: "`InvalidFlags` … for example, **user + kernel-only combinations**" `hal/src/mmu/mod.rs:400-401`. No "kernel-only" flag exists (`MappingFlags` = WRITE/EXECUTE/USER/DEVICE/GLOBAL, `mmu/mod.rs:89-97`); kernel-only is the *absence* of USER | Both impls return `InvalidFlags` for exactly one case — `DEVICE \| EXECUTE` — which the trait never names: `bsp-qemu-virt/src/mmu.rs:224-226`, `test-hal/src/mmu.rs:169-171` | The single concrete example in the contract is unrepresentable in the type, while the case both implementors actually reject is undocumented. A safe kernel caller routing error handling cannot learn from the trait that `DEVICE\|EXECUTE` fails. The rejection rule is also copy-pasted in three places (both impls + the doc would be the natural single home). | **Minor** | Replace the example with the real rule ("any mapping with both `DEVICE` and `EXECUTE`, because MMIO is never executable, ADR-0027"). Consider hoisting the check into a shared `MappingFlags::validate()` so the rule lives once. (Doc fix → X4a.) |
| **X4c-005** | No `ContextSwitch` fake in `test-hal` → duplicated, drift-prone inline `FakeCpu` in the kernel | `test-hal` exposes fakes for the five other traits but **no `ContextSwitch` impl** anywhere in the crate (`test-hal/src/cpu.rs` implements `Cpu` only); lib doc claims "all five … HAL traits now have fakes" `test-hal/src/lib.rs` | Kernel scheduler tests define their own inline `FakeCpu` + `FakeCtx` implementing **both** `Cpu` and `ContextSwitch` `kernel/src/sched/mod.rs:1252-1295` (and a 2nd `ResetQueuesCpu` `:1915-1927`) | Two independent `Cpu` fakes that can drift. The inline ones do **not** track IRQ state (`disable_irqs → IrqState(0)`, `restore_irq_state` no-op — `sched/mod.rs:1269-1272`) while `tyrne_test_hal::FakeCpu` *does* (`test-hal/src/cpu.rs:99-108`), so scheduler tests cannot assert IRQ-mask changes across a switch — and the polarity disagreement feeds X4c-002. The inline `init_context` is a full no-op (`sched/mod.rs:1288-1294`) vs the BSP's lr/sp write. | **Minor** | Add a `FakeContextSwitch` (records `context_switch`/`init_context` calls) to `test-hal`, or correct the lib doc to state `ContextSwitch` is intentionally un-faked and why. Either way, eliminate the polarity divergence with `tyrne_test_hal::FakeCpu`. |
| **X4c-006** | "512 entries per 4 KiB frame" encoded in ≥4 places; `ENTRIES_PER_TABLE` defined **twice with different definitions** | `const ENTRIES_PER_TABLE: usize = 512` (bare literal) `bsp-qemu-virt/src/mmu_bootstrap.rs:55`; four `static …: [u64; 512]` `mmu_bootstrap.rs:48-51`; one more `[u64; 512]` `bsp-qemu-virt/src/main.rs:687` | `const ENTRIES_PER_TABLE: usize = PAGE_SIZE / 8` (derived = 512) `bsp-qemu-virt/src/mmu.rs:57`; linker reserves the frames as four `. = . + 4096` `bsp-qemu-virt/linker.ld:67-73` | The same crate has two `const ENTRIES_PER_TABLE` with *different definitions* (one literal `512`, one `PAGE_SIZE/8`), plus the `[u64;512]` array-type fiction in two files and the `4096`×4 linker reservation — none cross-checked at compile time. If `PAGE_SIZE` ever changed, `mmu.rs` would track it and `mmu_bootstrap.rs`/`main.rs`/`linker.ld` would silently not. The MMU descriptor structs elsewhere *do* have compile-time size guards (`cpu.rs:326`, `exceptions.rs:77`); the bootstrap frames have none. | **Minor** | Declare the four extern statics once and re-export the L0 symbol; define one `ENTRIES_PER_TABLE` (prefer `PAGE_SIZE/8`) shared by both modules; add `const _: () = assert!(ENTRIES_PER_TABLE == 512)` beside the linker-reservation comment. (Extends C7-006.) |
| **X4c-007** | VMSAv8 per-level shift constants duplicated kernel↔BSP, with **conflicting level names** | Kernel: bare literals `>> 21`, `>> 30`, `>> 39` `kernel/src/obj/task_loader.rs:142-153`, and the 39-shift table is called **"L1 (1 GiB block)"** `task_loader.rs:151` | BSP: named consts `VA_L0_SHIFT=39, VA_L1_SHIFT=30, VA_L2_SHIFT=21, VA_L3_SHIFT=12` `bsp-qemu-virt/src/mmu.rs:50-53`; the 39-shift table is **`VA_L0_SHIFT`** (L0) `mmu.rs:50` | The same 39-bit shift names a level called **L1** in the kernel and **L0** in the BSP — a naming contradiction layered on a duplication: the kernel re-encodes the BSP's page-table-format constants (bare literals vs named consts) with no shared source of truth, *and* labels the levels off-by-one relative to the BSP. The budget arithmetic happens to be correct (it counts distinct parent indices, level-name-agnostic), but a maintainer reconciling the two files sees L1=39 here and L0=39 there. P6 (HAL-separation) smell: kernel-core encodes a BSP format constant. | **Minor** | Surface a HAL `Mmu::intermediate_frames_for_span` (already named as the escape hatch in `task_loader.rs:121`) so the shifts live once in the format owner; until then, align the level *labels* between the two files and reference the BSP's `VA_L*_SHIFT` naming. (Extends C4-004.) |
| **X4c-008** | `VecFrameProvider` violates the `FrameProvider` zero-fill contract the BSP walker depends on | Trait: "`alloc_frame` — Allocate a **zero-initialized** `PhysFrame`" `hal/src/mmu/mod.rs:204-208`. BSP `walk_or_alloc_table` **reads** the (zeroed) intermediate frame's descriptor slot and relies on it: "caller's `FrameProvider` contract guarantees the frame is zero-initialised when we receive it" `bsp-qemu-virt/src/mmu.rs:510-518` (and the leaf read `mmu.rs:437` assumes a clean descriptor) | `VecFrameProvider::alloc_frame` just `self.available.pop()` `test-hal/src/mmu.rs:33-35` — no zero-fill; the `PhysFrame` is a typed address, the backing bytes are whatever was in the `Vec`'s frames | The fake provider does not honour the zero-fill guarantee the real BSP walker structurally depends on. Vacuously safe *today* only because `FakeMmu` never dereferences the address (flat HashMap); but `VecFrameProvider` is `pub` and pairing it with any frame-reading fake (the decorator X4c-003 recommends) would feed the BSP-style walker non-zero descriptor bytes → garbage table/leaf decode. The contract owner (PMM) *does* zero (`kernel/src/mm/pmm.rs:436-438`). | **Minor** | Document the deviation on `VecFrameProvider`, or have it zero a backing buffer. If a frame-reading fake is added (X4c-003), this becomes load-bearing. (Confirms C8-005/C2-006 with the BSP-dependency teeth.) |
| **X4c-009** | `FakeIrqController` omits the `GIC_MAX_IRQ` range guard the BSP asserts | BSP `enable`/`disable` `assert!(irq.0 < GIC_MAX_IRQ)` (=1020) `bsp-qemu-virt/src/gic.rs:317-322,343-348`; out-of-range computes an offset outside the distributor MMIO window | `FakeIrqController::enable`/`disable` insert/remove from a `HashSet` **unconditionally** `test-hal/src/irq_controller.rs:94-99` — `IrqNumber(1023)` (the spurious sentinel) or `u32::MAX` silently accepted | Same input that *panics* on hardware *passes* on the host. The trait does not state an upper bound, so neither impl violates the *written* contract — but the implementors disagree on the de-facto bound, and the fake gives false confidence for any kernel logic that miscomputes an IRQ number. | **Minor** | Mirror the bound in `FakeIrqController` (`assert!(irq.0 < 1020)` with a doc-note that it matches the GIC), and add a test that the assertion fires. Consider stating the architectural max on the trait so both sides reference one number. (Confirms C8-004.) |
| X4c-010 | Timer IRQ `27` encoded twice, two different types | `const TIMER_IRQ: IrqNumber = IrqNumber(27)` `bsp-qemu-virt/src/cpu.rs:48` | `const TIMER_IRQ_ID: u32 = 27` `bsp-qemu-virt/src/exceptions.rs:35` | Same hardware constant (the Generic Timer virtual-timer PPI) defined twice in the same crate with different types and names; the duplication is acknowledged in a comment but not deduplicated. Values agree today. | **Nit** | Single `pub(crate) const TIMER_IRQ: IrqNumber` consumed by both call sites (`cpu.rs:535,559`, `exceptions.rs:190`). (Confirms C7 cross-track note.) |
| X4c-011 | `TaskStack` hard-codes `4096` instead of `PAGE_SIZE` | `struct TaskStack(UnsafeCell<[u8; 4096]>)` + `[0u8; 4096]` + `.add(4096)` `bsp-qemu-virt/src/main.rs:183,197,214` | Rest of BSP/kernel uses `tyrne_hal::PAGE_SIZE` (e.g. `main.rs:94,832`, `mmu.rs:57,210`, `pmm.rs`) | Three production sites encode the page size as a magic literal where the workspace otherwise threads the named `PAGE_SIZE`. The stack is page-sized by intent but not tied to the constant. | **Nit** | Use `PAGE_SIZE` (or a named `TASK_STACK_BYTES`) for the three occurrences. |
| X4c-012 | RAM-extent size encoded two ways; `ENTRIES_PER_TABLE / 8` overloaded to mean "64 RAM blocks" | RAM extent as `0x4800_0000 - 0x4000_0000` (128 MiB) via `PMM_EXTENT_{START,END}` `bsp-qemu-virt/src/main.rs:76-78` | RAM block count computed as `ENTRIES_PER_TABLE / 8 == 64` `bsp-qemu-virt/src/mmu_bootstrap.rs:163-164` | The "128 MiB RAM" fact is encoded independently in two files, and the bootstrap loop derives the 64-block count from `ENTRIES_PER_TABLE / 8` — a quantity semantically unrelated to RAM size that only equals 64 because `ENTRIES_PER_TABLE` is 512. A change to the RAM extent in `main.rs` would not update the bootstrap loop, and vice-versa. | **Nit** | Derive the block count from `(PMM_EXTENT_END - PMM_EXTENT_START) / BLOCK_2MIB` (the actual relationship) rather than `ENTRIES_PER_TABLE / 8`, and source the extent from one shared const. |
| X4c-013 | `Scheduler::new` doc says "zero-initialised" but uses `Default`; BSP `init_context` silently depends on `Default == zero` | Scheduler doc/field: "all contexts **zero-initialised** by `Default`" `kernel/src/sched/mod.rs:278,290`; init is `C::TaskContext::default()` `sched/mod.rs:300`; trait bound is only `Default` `hal/src/context_switch.rs:31` | BSP `init_context` writes only `lr`/`sp`, comment: "All other callee-saved registers are zero (**from Default**)" `bsp-qemu-virt/src/cpu.rs:433-437` | The scheduler claims a zero guarantee the `Default` bound does not make, and the BSP `init_context`'s correctness *depends* on that guarantee (it never clears `x19`–`x28`/`d8`–`d15`). True for `Aarch64TaskContext` (`#[derive(Default)]` → all-zero, `cpu.rs:304`), but a second BSP whose `TaskContext::default()` left garbage in callee-saved slots would have the first restore load that garbage. | **Nit** | Either tighten the trait bound's intent ("`Default` must zero all saved-register slots") and say so, or have `init_context` zero the slots it relies on. Fix the scheduler doc to say "default-initialised". (Confirms C5-N4 with the BSP-dependency angle.) |
| X4c-014 | `FakeTimer::set_now` can move the clock backwards, contradicting `now_ns` monotonic contract | Trait: "`now_ns` — Monotonic: **never goes backwards**" `hal/src/timer.rs:33-36`; BSP reads a free-running counter (monotonic) `bsp-qemu-virt/src/cpu.rs:480-488` | `FakeTimer::set_now` assigns `now_ns = ns` unconditionally `test-hal/src/timer.rs:53-55`; the in-crate test does `advance(100)` then `set_now(42)` → `now=42` `timer.rs:132-137` | The fake exposes a test affordance that lets the monotonic clock go backwards. It is a test-only helper (not the trait method), so it does not break the `Timer` impl per se, but it lets a test set up a clock state the real hardware can never reach, weakening fidelity. | **Nit** | Document `set_now` as a test escape hatch that may break monotonicity, or have it `assert!(ns >= now_ns)` / saturate to `now_ns`. |

---

## HAL trait ↔ implementor conformance matrix

Legend: ✅ consistent · ⚠ divergent (see ID) · n/a = trait method has no analogue.
"Kernel expectation" = the de-facto contract the kernel relies on at call sites.

### `Console` (`hal/src/console.rs`)

| Method | BSP `Pl011Uart` | test-hal `FakeConsole` | Kernel expectation | Consistent? |
|---|---|---|---|---|
| `write_bytes` | spin-on-TXFF + DR write, infallible, no-alloc (`console.rs`) | capture to `Mutex<Vec<u8>>` (`test-hal/src/console.rs:58-64`) | best-effort byte sink | ✅ |

### `Cpu` (`hal/src/cpu.rs`)

| Method | BSP `QemuVirtCpu` | test-hal `FakeCpu` | Kernel inline `FakeCpu`/`ResetQueuesCpu` | Kernel expectation | Consistent? |
|---|---|---|---|---|---|
| `current_core_id` | `MPIDR_EL1` | configurable `core_id` | `0` | core id | ✅ |
| `disable_irqs` → `IrqState` | **raw DAIF** (`cpu.rs:240-256`) | **bool** `irqs_enabled` (`cpu.rs:99-104`) | `IrqState(0)` const (`sched/mod.rs:1269-1272,1919-1922`) | save+restore mask | ⚠ **X4c-002** (encodings mean opposite things) |
| `restore_irq_state` | `msr daif` (`cpu.rs:259-266`) | `irqs_enabled = s.0 != 0` (`cpu.rs:106-108`) | no-op | round-trip the saved state | ⚠ **X4c-002** |
| `wait_for_interrupt` | `WFI` | counts calls | no-op | halt until IRQ | ✅ |
| `instruction_barrier` | `ISB` | counts calls | no-op | pipeline sync | ✅ |
| `current_el()` (free fn) | aarch64+none only (`cpu.rs:164-194`) | absent on host (cfg-gated) | absent | EL assert at boot | ✅ (cfg-gated by design) |

### `ContextSwitch` (`hal/src/context_switch.rs`)

| Method | BSP `QemuVirtCpu` | test-hal | Kernel inline `FakeCpu`/`ResetQueuesCpu` | Kernel expectation | Consistent? |
|---|---|---|---|---|---|
| `type TaskContext` | `Aarch64TaskContext` (168 B, incl. `d8_d15`) `cpu.rs:304-326` | **none** | `FakeCtx { switched }` `sched/mod.rs:1254-1257` | `Default + Send`, zero on default | ⚠ **X4c-001** (contract omits `d8`–`d15`), **X4c-005** (no test-hal fake), **X4c-013** (`Default==zero` reliance) |
| `context_switch` | naked asm, saves `x19`–`x28`/fp/lr/sp/**d8–d15** `cpu.rs:354-405` | **none** | sets `current.switched=true` `sched/mod.rs:1280-1286` | atomic save/restore of callee set | ⚠ **X4c-001** |
| `init_context` | writes `lr`,`sp`; relies on Default-zero for the rest `cpu.rs:424-438` | **none** | full no-op `sched/mod.rs:1288-1294` | seed entry+sp | ⚠ **X4c-005/013** |

### `Mmu` (`hal/src/mmu/mod.rs`)

| Method | BSP `QemuVirtMmu` | test-hal `FakeMmu` | Kernel expectation | Consistent? |
|---|---|---|---|---|
| `create_address_space` (unsafe) | store root, no alloc `mmu.rs:151-155` | store root, no deref `test-hal/src/mmu.rs:133-138` | aligned+zeroed+exclusive root | ✅ (note: test-hal impl lacks `# Safety`/audit — C8-001, route X1) |
| `address_space_root` | `as_.root` | `as_.root` | identity | ✅ |
| `activate` | `msr ttbr0` + barriers + TLBI `mmu.rs:161-199` | record `activated_root` | swap AS | ✅ |
| `map` — VA align | reject `MisalignedAddress` `mmu.rs:210` | reject `MisalignedAddress` `test-hal/src/mmu.rs:160` | reject unaligned | ✅ |
| `map` — `DEVICE\|EXECUTE` | reject `InvalidFlags` `mmu.rs:224-226` | reject `InvalidFlags` `test-hal/src/mmu.rs:169-171` | reject (impls agree) | ✅ impls, ⚠ **X4c-004** (trait doc names a *different*, unrepresentable case) |
| `map` — `AlreadyMapped` | leaf valid → err `mmu.rs:438-439`; block → `AlreadyMapped` `mmu.rs:493-497` | key present → err `test-hal/src/mmu.rs:172-174` | err on double-map | ✅ |
| `map` — `OutOfFrames` (mid-walk) | `alloc_frame().ok_or(OutOfFrames)` `mmu.rs:510` | **never** (`_frames` ignored) `test-hal/src/mmu.rs:154` | clause (2)/(3) on Err | ⚠ **X4c-003** |
| `map` — failure clauses (1)-(3) | leaf write last (`mmu.rs:441-447`), `pa` not consumed on Err | flat insert; no intermediate state | rollback frees leaf only (`task_loader.rs:682-691`) | ✅ in BSP; ⚠ untestable via fake (**X4c-003**) |
| `unmap` — `BlockMapped` | `mmu.rs:493-497` | **never** (flat map) `test-hal/src/mmu.rs:179-193` | distinguish from `NotMapped` | ⚠ **X4c-003** |
| `unmap` — `NotMapped` | `mmu.rs:422-423` | `ok_or(NotMapped)` `test-hal/src/mmu.rs:192` | err on unmap-missing | ✅ |
| `invalidate_tlb_address/all` | TLBI asm `mmu.rs:281-339` | record counts | TLB hint | ✅ |
| `FrameProvider::alloc_frame` zero-fill | walker depends on zeroed frames `mmu.rs:510-518` | `VecFrameProvider` pops, no zero `test-hal/src/mmu.rs:33-35`; PMM zeros `pmm.rs:436` | zeroed frame | ⚠ **X4c-008** |

### `Timer` (`hal/src/timer.rs`)

| Method | BSP `QemuVirtCpu` | test-hal `FakeTimer` | Kernel expectation | Consistent? |
|---|---|---|---|---|
| `now_ns` (monotonic) | `CNTVCT_EL0`→`ticks_to_ns`, saturating `cpu.rs:480-488` | returns stored `now_ns` `timer.rs:91-93` | never goes backwards | ⚠ **X4c-014** (`set_now` can rewind the fake) |
| `arm_deadline` (absolute, rounds to resolution) | `ns_to_ticks`→`CNTV_CVAL` `cpu.rs:491-537` | stores raw `deadline_ns`, **does not fire** `timer.rs:95-97` | absolute deadline | ✅ (documented fake limitation — does not fire) |
| `cancel_deadline` | masks `CNTV_CTL` | clears + counts `timer.rs:99-103` | clear pending | ✅ |
| `resolution_ns` | from `CNTFRQ_EL0` | configurable | rounding granularity | ✅ |

### `IrqController` (`hal/src/irq_controller.rs`)

| Method | BSP `QemuVirtGic` | test-hal `FakeIrqController` | Kernel expectation | Consistent? |
|---|---|---|---|---|
| `enable`/`disable` (idempotent) | ISENABLER/ICENABLER write-1, **+ `assert!(irq.0 < GIC_MAX_IRQ)`** `gic.rs:316-362` | `HashSet` insert/remove, **no range check** `irq_controller.rs:94-99` | idempotent enable/disable | ⚠ **X4c-009** |
| `acknowledge` (spurious→None) | `GICC_IAR`; INTID 1023→None `gic.rs:364-376` | `pop_front()`→None on empty `irq_controller.rs:102-104` | None on spurious | ✅ |
| `end_of_interrupt` | single `GICC_EOIR` write (GICv2) `gic.rs:378-384` | record history | EOI paired with ack | ✅ (note: trait doc says "GICv3"/"GICv2", impl is GICv2 — doc → X4a) |

---

## Refuted candidates (with proof)

- **R1 — "task_loader relies on `Mmu::map` NOT consuming `pa` on failure — is that guaranteed?"**
  **CONFIRMED guaranteed, not a contradiction.** The trait promises clause (2)
  explicitly (`hal/src/mmu/mod.rs:361-367,378-388`), and the BSP upholds it: in
  `walk_and_install_leaf` the leaf descriptor write is the **last** operation,
  after every fallible step (`bsp-qemu-virt/src/mmu.rs:434-447`); on the
  `AlreadyMapped`/`OutOfFrames` branches it returns before any leaf write
  (`mmu.rs:438-439`, and `walk_or_alloc_table` returns the error before the leaf
  is reached, `mmu.rs:510`). The kernel caller frees the leaf on Err
  (`task_loader.rs:691`) and does **not** free intermediates (honouring clause
  (3)). The *only* code↔code issue here is that the path is **untestable through
  `FakeMmu`** (folded into X4c-003); the contract itself is consistent.

- **R2 — "`PAGE_SIZE` (4 KiB) might be encoded inconsistently across crates."**
  **REFUTED for the named constant.** `PAGE_SIZE` is defined once
  (`hal/src/mmu/mod.rs:21`), re-exported (`hal/src/lib.rs:48`), and consumed via
  `tyrne_hal::PAGE_SIZE` by both the BSP (`mmu.rs:43`, `main.rs:35`,
  `mmu_bootstrap` arithmetic) and the kernel (`mm/mod.rs:19`, `mm/pmm.rs:22`,
  `task_loader`). The only bare-`4096` production occurrences are the `TaskStack`
  array (X4c-011, Nit) and the bootstrap frame reservations (X4c-006); the rest
  of the `4096` hits are inside `#[cfg(test)]` modules in `pmm.rs`. The page-size
  *value* is consistent everywhere.

- **R3 — "The two `FakeCpu` IRQ-mask semantics might be merely a duplication."**
  **PARTIALLY REFUTED → escalated.** It is not *merely* duplication: the two
  encodings are not just different representations of the same state, they assign
  **opposite meanings to the same value** (`IrqState(0)` = enabled on the BSP,
  disabled in `tyrne_test_hal::FakeCpu`). Recorded as the contradiction X4c-002,
  not a benign dup.

- **R4 — "`MapperFlush::flush` accepting any `Mmu` is a code↔code contradiction."**
  **REFUTED as a contradiction (future-soundness cliff, already tracked).** Both
  implementors honour the token identically and the doc openly states the
  no-instance-binding for single-AS v1 (`hal/src/mmu/mod.rs:230-233`). No
  implementor contradicts another; it is a forward-design note (C6-005), not a
  present inconsistency.

---

## Cross-track notes

### → X1 (soundness / unsafe-audit)
- **X4c-001** — a *literal* second-BSP `ContextSwitch` impl built to the
  enumerated list would corrupt `d8`–`d15` across a yield: this is the soundness
  consequence of the contract gap. The v1 BSP is correct; the risk is for the
  next board.
- **X4c-002** — the `IrqState` polarity divergence is masked today only because
  the scheduler's *inline* test fakes make `restore_irq_state` a no-op. A shared
  `tyrne_test_hal::FakeCpu` (the natural consolidation under X4c-005) would invert
  the BSP's enable/disable meaning — an aliasing/critical-section hazard if any
  test ever asserted IRQ state across the switch. Pair with the existing C5-004
  "Miri-not-in-CI" note: the bridge's soundness rests on IRQs actually being
  masked across `context_switch`, which no host fake currently verifies.
- **X4c-003 / X4c-008** — the `Mmu::map` failure contract (clauses 2/3) and the
  `FrameProvider` zero-fill guarantee are both load-bearing for `unsafe`-free
  kernel callers (`task_loader` rollback `task_loader.rs:682-691`; `cap_map`
  `address_space.rs:719-737`) and for the BSP page-table walker
  (`mmu.rs:437,510-518`). Neither is exercisable through the current fakes; a
  frame-consuming + block-injecting decorator fake closes the gap (also routed to
  the test-coverage view by C2-006 / C8-002 / C8-003).
- **X4c-006** — the bootstrap page-table frames have no compile-time size guard
  while the other MMU/exception structs do; a `PAGE_SIZE` change would silently
  desync the `512`/`4096` encodings. Recommend the `assert!` guard as a
  defence-in-depth item.

### → X4a (trait-contract doc fixes)
- **X4c-004** — `Mmu::map` `# Errors`: replace the unrepresentable "user +
  kernel-only" example with the real `DEVICE|EXECUTE` rule (ADR-0027); consider a
  shared `MappingFlags::validate()` so the rule has one home.
- **X4c-001 (doc half)** — `context_switch.rs` `# Safety` + ADR-0020 must add
  `d8`–`d15` to the callee-saved enumeration.
- **`IrqController` GICv3/GICv2 prose** — the trait doc references "GICv3"
  (`irq_controller.rs:32,49,56`) and `IrqNumber`'s "~16 million lines"
  (`irq_controller.rs:9-11`) while the only implementor is GICv2
  (`gic.rs:78` `GIC_MAX_IRQ=1020`); reconcile (ties to C7-001's ADR-0012 "GICv3"
  defect). Pure doc, but it is trait-prose-vs-impl.
- **X4c-013 (doc half)** — `Scheduler::new` "zero-initialised" should read
  "default-initialised", and the `ContextSwitch::TaskContext` bound should state
  whether `Default` is required to zero the saved-register slots (the BSP relies
  on it).

### → docs / constants-dedup (maintainability)
- **X4c-006/007/010/011/012** — five "same fact, multiple encodings" items:
  `ENTRIES_PER_TABLE`/`512`/`4096` (≥4 sites, two conflicting `const`
  definitions); VMSAv8 shifts `21/30/39/12` duplicated kernel↔BSP with conflicting
  L0/L1 *labels*; timer IRQ `27` (two types); `TaskStack` `4096` literal; the
  128 MiB RAM extent encoded two ways. None are live bugs at this commit (single
  BSP, values agree), but each is a silent-desync risk the moment a second
  BSP/extent/page-size appears. The VMSAv8-shift item (X4c-007) is the one with a
  *current* inconsistency (the L0-vs-L1 naming), so it ranks above the rest.

---

## Praise

- **X4c-P1 — The `Mmu::map` failure-semantics contract is genuinely load-bearing
  and the BSP + kernel cooperate correctly.** The trait spells out clauses
  (1)-(3) (`hal/src/mmu/mod.rs:353-389`), the BSP writes the leaf descriptor last
  to honour clause (2) (`bsp-qemu-virt/src/mmu.rs:441-447`), and the kernel
  rollback names the trait clause as its safety argument
  (`kernel/src/obj/task_loader.rs:682-691`). This three-way agreement
  (trait ↔ BSP ↔ kernel caller) is exactly the discipline a capability kernel
  needs — the only gap is that the fake can't *test* it (X4c-003).

- **X4c-P2 — The two implementors agree precisely on the behaviours the fake
  *does* model.** VA-alignment rejection, `DEVICE|EXECUTE` rejection,
  double-map → `AlreadyMapped`, unmap-missing → `NotMapped`, FIFO ack, idempotent
  enable, spurious → `None`, and the `MapperFlush` `#[must_use]` token discharge
  are all mirrored bit-for-bit between `bsp-qemu-virt` and `test-hal` (matrix
  above). The back-ported `DEVICE|EXECUTE` and VA-alignment checks in `FakeMmu`
  (`test-hal/src/mmu.rs:160,169-171`) are the right pattern: reject on the host
  what hardware would reject. Where the fakes diverge from the BSP, it is by
  *omission* of harder-to-model behaviours, never by modelling them *differently*.
