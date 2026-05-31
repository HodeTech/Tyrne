# 0038 — `Mmu::translate` read-only walk + per-task user-access translation (B6 gate #1)

- **Status:** Accepted
- **Date:** 2026-05-31
- **Deciders:** @cemililik

## Context

B6 wires the first real EL0 task. The moment that task issues `console_write` — the only v1 syscall that reads a userspace buffer — the kernel must copy bytes *out of the task's address space* onto the debug console. Today ([`kernel/src/syscall/user_access.rs`](../../kernel/src/syscall/user_access.rs)) the copy is a direct int-to-pointer dereference (`user_ptr as *const u8`) bounded by a single [`UserAccessWindow`] range that the BSP currently sets to the **entire 128 MiB RAM extent** ([`bsp-qemu-virt/src/syscall.rs`](../../bsp-qemu-virt/src/syscall.rs) `SYSCALL_USER_WINDOW_LEN`). That model is sound *only* because B5's sole syscall caller is a trusted EL1 kernel stub running in the bootstrap address space — where the kernel is identity-mapped — and because `TCR_EL1.EPD0 = 1` keeps any real EL0 task out of `syscall_entry` entirely.

When B6 enables a real EL0 task, that model becomes a privilege-escalation vector. An EL0 holder of a debug-console capability could pass an in-window **high-half kernel VA** to `console_write`; under the current bounds-check-then-dereference, the kernel would copy privileged memory to the console — a confused-deputy read of arbitrary kernel state. The range bounds-check is **necessary but not sufficient**: it proves the pointer lies in a range; it does not prove the pointer names *the task's own* memory rather than a kernel address that merely falls in-window. [phase-b §B6 gate #1](../roadmap/phases/phase-b.md#t-021-carry-forward-gates-must-close-before-a-real-el0-task-runs) names this the single most important gate and makes closing it a **hard precondition** for `syscall_entry` becoming EL0-reachable.

Closing it requires the kernel to resolve each user VA through the **task's own `TTBR0_EL1` translation tables** and confirm the leaf is `USER`-accessible before dereferencing. [ADR-0009 §Open questions](0009-mmu-trait.md) deferred exactly this primitive — *"Translation walk queries. `lookup(va) -> Option<(PhysFrame, MappingFlags)>` … deferred until a concrete caller needs it."* B6 gate #1 is that caller. This ADR settles the trait surface for the walk query and the kernel-side policy that consumes it. Left implicit, the walk would be re-invented ad hoc in the syscall path — a second `unsafe` page-table walker duplicating the BSP's, with no descriptor decoder and no test seam — and the security property would continue to rest on the bounds-check the threat model already rejects.

## Decision drivers

- **The confused-deputy defence is the whole point.** The leaf-level `USER` permission check — not the range bound — is what stops an EL0 caller from naming kernel memory. The design must make that check the load-bearing boundary.
- **Never panic; fail closed.** A translation miss, a block-mapped region, or a missing `USER` bit must return `SyscallError::FaultAddress`, never panic and never copy. (The dispatcher's panic-free contract, [ADR-0030](0030-syscall-abi.md).)
- **Reuse the audited walker; do not duplicate it.** The BSP already owns the L0→L3 VMSAv8 walk in `QemuVirtMmu::map`/`unmap` (UNSAFE-2026-0025). A read-only query should reuse that machinery, not grow a second walk surface in the kernel.
- **Architecture portability ([P6](../standards/architectural-principles.md#p6--hal-separation)).** Page-table-format knowledge (VMSAv8 descriptor decode) belongs in the HAL/BSP, behind the `Mmu` trait — a future Sv39 BSP supplies its own `translate`. The kernel must not decode descriptors.
- **Host-testable without QEMU or a real EL0 task.** The security boundary must be provable on the host: `FakeMmu` can model `translate` as a flat map, so the per-page copy-user logic and the confused-deputy reject are unit-testable *before* any EL0 task exists.
- **Additive, byte-stable trait extension.** Existing `Mmu` methods stay byte-stable and the `copy_from_user`/`copy_to_user` *contract* is preserved; the change rides ADR-0009's additive-extension pattern (cf. the [`MapperFlush` rider](0009-mmu-trait.md#revision-notes)).

## Considered options

1. **Add `Mmu::translate` (read-only walk query) to the HAL trait + decode in the BSP; the kernel copy-user path calls it per page.** The deferred ADR-0009 query arrives; the kernel stays format-agnostic.
2. **Software page-table walk in the kernel** against the AS root frame, using new `vmsav8` *decoder* functions called from `kernel/src/mm`. No trait change.
3. **Keep the single window; pre-translate it once at dispatch and bounds-check against the translated kernel range.** No per-page query; tighten the window only.

## Decision outcome

Chosen option: **Option 1 — add a read-only `Mmu::translate` query to the trait, decode in the BSP, and have the kernel copy-user path translate per page and enforce `USER`.**

`translate` is the long-deferred ADR-0009 walk query, arriving with its first concrete caller:

```rust
/// Resolve `va` through this address space's translation tables (read-only
/// walk) to the page frame that backs it and that leaf's mapping flags.
///
/// The deferred "translation walk query" of [ADR-0009] §Open questions,
/// added now that B6 gate #1 (user-access translation) is its first caller.
/// Returns the PAGE_SIZE-aligned frame containing `va`; the caller re-adds
/// the in-page offset (`va.0 & (PAGE_SIZE - 1)`) for the exact PA.
///
/// # Errors
/// - [`MmuError::NotMapped`]   — no valid leaf descriptor covers `va`.
/// - [`MmuError::BlockMapped`] — `va` resolves through a block descriptor;
///   v1 `translate` serves only 4 KiB page leaves (block-mapped regions,
///   e.g. the bootstrap kernel map, are never user-reachable).
fn translate(
    &self,
    as_: &Self::AddressSpace,
    va: VirtAddr,
) -> Result<(PhysFrame, MappingFlags), MmuError>;
```

It is additive, takes `&Self::AddressSpace` (read-only — no `FrameProvider`, no mutation), and reuses the BSP's existing descriptor masks/bit-definitions through one new pure decoder, `vmsav8::descriptor_bits_to_flags` — the inverse of the existing `flags_to_descriptor_bits`, **lock-shut**: it reconstructs only the five named `MappingFlags` (`USER`/`WRITE`/`EXECUTE`/`DEVICE`/`GLOBAL`), so an unrecognised bit pattern never widens permissions. `FaultAddress` is never produced by the HAL — `translate` returns `MmuError`; the **kernel** maps any error to `SyscallError::FaultAddress`.

The kernel copy-user policy ([`user_access.rs`](../../kernel/src/syscall/user_access.rs)):

- `copy_from_user` / `copy_to_user` become generic over `<M: Mmu>` and take `mmu: &M` plus the task's `&M::AddressSpace`. Their **contract** (validate, then move bytes; `FaultAddress` on failure; zero-length short-circuit) is unchanged.
- The int-to-pointer dereference is replaced by a **two-pass** per-page walk (all-or-nothing): **pass 1 probes** every page the `[ptr, ptr + len)` range spans — `mmu.translate(task_as, page_va)` → require `MappingFlags::USER` (and additionally `WRITE` for `copy_to_user`); only if *every* page passes does **pass 2 copy**, rebasing each frame to a kernel pointer via [`crate::mm::phys_frame_kernel_ptr`](../../kernel/src/mm/mod.rs) + the in-page offset and moving its byte sub-run. **Any `translate` error, or a leaf lacking `USER`, on the probe pass → `SyscallError::FaultAddress`, copying/emitting nothing (no prefix on a mid-range fault).**
- The [`UserAccessWindow`](../../kernel/src/syscall/user_access.rs) survives as a cheap **first gate** (range containment, wrap rejection, zero-length short-circuit), now derived **per task** from `[entry_va, stack_top_va)` (the loader's contiguous image+stack span) rather than the RAM extent. The window bounds the range; **`translate`'s `USER` check proves ownership + permission** — the necessary-and-sufficient pair gate #1 demands.

This composes [ADR-0009](0009-mmu-trait.md) (the trait's home), [ADR-0033](0033-kernel-high-half-migration.md) (the high-half direct map `phys_frame_kernel_ptr` rebases through), and [ADR-0030](0030-syscall-abi.md) (the `UserAccessWindow` + `FaultAddress` copy-user contract this plugs into). The additive trait method is also recorded as a §Revision-notes rider on ADR-0009, per that ADR's `MapperFlush` precedent.

Option 2 was rejected: it duplicates the L0→L3 walk and descriptor decode in the kernel, grows a *second* `unsafe` walk surface to audit, and puts VMSAv8 format knowledge above the HAL boundary (a [P6](../standards/architectural-principles.md#p6--hal-separation) violation). Option 3 was rejected: a single pre-translated window still cannot distinguish a task page from an in-window kernel page once the window covers anything but one task's own pages, and it provides no per-page `USER` enforcement — it re-bounds the range without proving ownership, leaving the confused-deputy gap open for any multi-region or aliased layout.

### Simulation

The worst-case interaction is `console_write` from a real EL0 task whose buffer pointer is attacker-chosen. State = `(window first-gate, per-page translate + USER check, observable output)`.

| # | state-pre (caller passes) | action | state-post | observable effect |
|---|---|---|---|---|
| 0 | `ptr,len` wholly in `[entry_va, stack_top_va)`, all pages `USER` | window OK → `translate` each page → `USER` present | copy each page sub-run; emit | bytes written to console; `Ok` |
| 1 | in-window **low-VA page** in `[entry_va, stack_top_va)` whose leaf lacks `USER` (a guard page, RO-shared page, or an adversarially mis-mapped page) | window OK → `translate` → flags **without `USER`** | **reject before any deref** | **`FaultAddress`; nothing emitted** — the `USER` check is load-bearing (it proves the page *grants user access*, not merely that the VA is in range) |
| 2 | in-window but page unmapped (gap in task AS) | window OK → `translate` → `Err(NotMapped)` | reject | `FaultAddress`; nothing emitted |
| 3 | range escapes `[entry_va, stack_top_va)` or wraps past `usize::MAX` | window `validate` fails (cheap first gate) | reject before any `translate` | `FaultAddress`; no walk performed |
| 4 | multi-page span; page 0 `USER`-ok, page 1 unmapped | up-front probe `translate`s every page → page 1 `Err` | reject before emit (all-or-nothing) | `FaultAddress`; **no prefix emitted** |
| 5 | `copy_to_user`: in-window page is `USER` but **not `WRITE`** (RO data) | window OK → `translate` → `USER` present, `WRITE` absent | reject before write | `FaultAddress`; nothing written |

> The high-half **kernel-VA** confused-deputy (the B5-legacy threat, when the window was the whole RAM extent) is caught by the **window first gate** under the per-task window — a high-half VA is not in `[entry_va, stack_top_va)`, so it fails as row 3, never reaching the `USER` check. Once the window is tight, the residual *in-range* threat the `USER` check defends is row 1. Both layers are retained as defence-in-depth.

Row-to-verification mapping (discharged by **T-025**, recorded in its review-history row): row 0 → `copy_from_user_translates_and_copies_a_user_page`; row 1 → `copy_from_user_rejects_in_window_non_user_page` (the confused-deputy regression test) + `dispatch::console_write_cap_ok_but_non_user_page_emits_nothing`; row 2 → `copy_from_user_faults_on_unmapped_page`; row 3 → the retained `UserAccessWindow::validate` tests; row 4 → `console_write_multipage_second_page_unmapped_emits_nothing`; row 5 → `copy_to_user_rejects_read_only_user_page`. The read-only `QemuVirtMmu::translate` walk rides UNSAFE-2026-0025 (extended, not new).

### Dependency chain

```text
For this decision to be fully in effect:
1. Mmu trait is the home of the deferred walk query         — ADR-0009 (Accepted)
2. High-half direct map (phys_frame_kernel_ptr rebase)      — ADR-0033 (Accepted)
3. UserAccessWindow + FaultAddress copy-user contract       — ADR-0030 (Accepted)
4. Mmu::translate + vmsav8::descriptor_bits_to_flags
   + QemuVirtMmu/FakeMmu impls + per-page translate-based
   copy_from_user/copy_to_user + per-task window            — T-025 (Draft, opened with this ADR)
5. syscall_entry sources the per-task window + the running
   task's AS / capability table so translate runs against a
   real task AS (gate #3 plumbing)                          — T-026 (Draft, opened with this ADR)
6. A real EL0 task exercises the boundary at runtime        — B6 wire-up (phase-b §B6 step 6)
```

T-025 lands step 4 (the mechanism + its full host-test proof — provable *without* a real EL0 task). Step 5 (T-026) is gate #3 — no ADR of its own; it rides [ADR-0030 §Dependency-chain](0030-syscall-abi.md) + [ADR-0014](0014-capability-representation.md) per-subject-table unforgeability. The runtime exercise (step 6) is the later B6 wire-up. The security benefit is fully realised only once steps 4–6 all land; **step 4 must merge before any EL0 task is enabled** (the hard ordering precondition — gate #1 fails closed today only because `EPD0 = 1`).

## Consequences

### Positive

- The confused-deputy read is closed at the leaf-`USER` level — the boundary the threat model actually requires, not a range bound.
- The deferred ADR-0009 walk query lands with a real caller and a test seam; future consumers (a page-fault handler, copy-on-write, a debugger) inherit a clean, format-agnostic `translate`.
- The read-only walk reuses the BSP's audited walker (UNSAFE-2026-0025 umbrella); **no new `unsafe` walk surface** in the kernel.
- Fully host-testable: the security property is proven on the host against `FakeMmu` before a real EL0 task exists.

### Negative

- **`SyscallContext` grows generic over `<M: Mmu>` and gains `mmu` + `task_as`.** Every construction site (the `dispatch` host tests + the BSP `syscall_entry`) must thread a `FakeMmu` / address space. *Mitigation:* the change is mechanical and the copy *contract* is preserved even though the context widens — we accept the one-time churn for a format-agnostic, testable boundary.
- **A page-table walk per spanned page on every `console_write`** (plus an all-or-nothing probe pass) is slower than a single dereference. *Accepted:* `console_write` is not a hot path, buffers are small, and correctness/security dominate. Revisit if a bulk user-copy syscall appears.
- **`translate` becomes stable ABI** once shipped; the `(PhysFrame, MappingFlags)` return shape is then hard to change. *Accepted:* it mirrors `unmap`'s `PhysFrame` return and descriptor granularity; the maintainer ratifies the shape at Accept.

### Neutral

- The per-task `UserAccessWindow` becomes a defence-in-depth first gate rather than the boundary; it is retained for the cheap wrap / zero-length / range short-circuit, not relied on for ownership.
- `translate` serves only 4 KiB page leaves in v1 (block-mapped regions return `BlockMapped`); the loader maps user pages page-granular, so user buffers are always L3 pages.

## Pros and cons of the options

### Option 1 — `Mmu::translate` query + BSP decode (chosen)

- Pro: reuses the audited walker; no kernel-side descriptor decode ([P6](../standards/architectural-principles.md#p6--hal-separation)-clean).
- Pro: `FakeMmu` makes the security boundary host-testable without QEMU / a real EL0 task.
- Pro: lands the deferred ADR-0009 query for all future consumers.
- Con: widens `SyscallContext` to `<M: Mmu>` and threads `mmu` / `task_as`; per-page walk cost.

### Option 2 — kernel software walk + new decoders

- Pro: no trait change.
- Con: duplicates the L0→L3 walk and adds a second `unsafe` walk surface to audit.
- Con: puts VMSAv8 descriptor knowledge in the kernel (a [P6](../standards/architectural-principles.md#p6--hal-separation) violation); a future Sv39 BSP cannot reuse it.

### Option 3 — pre-translate the single window, bounds-check only

- Pro: smallest code change; no per-page query.
- Con: no per-page `USER` enforcement — leaves the confused-deputy gap open whenever the window is not exactly one task's own pages.
- Con: a single contiguous translated range cannot model a task whose mapped regions are non-contiguous.

## References

- [ADR-0009 — `Mmu` HAL trait signature (v1)](0009-mmu-trait.md) — §Open questions "Translation walk queries"; §Revision notes (this ADR's rider).
- [ADR-0030 — Syscall ABI](0030-syscall-abi.md) — `UserAccessWindow` / `FaultAddress` / the copy-user contract this plugs into.
- [ADR-0033 — Kernel high-half migration](0033-kernel-high-half-migration.md) — the direct map `phys_frame_kernel_ptr` rebases through.
- [ADR-0014 — Capability representation](0014-capability-representation.md) — per-subject table unforgeability (gate #3 / T-026 rides this).
- [phase-b.md §B6 — T-021 carry-forward gates](../roadmap/phases/phase-b.md#t-021-carry-forward-gates-must-close-before-a-real-el0-task-runs) — gate #1 threat + hard ordering precondition.
- ARM *Architecture Reference Manual*, ARMv8-A — VMSAv8 stage-1 descriptor layout (AP[7:6], UXN/PXN, AttrIdx[4:2], nG) that `descriptor_bits_to_flags` decodes.
- Linux `arch/arm64` `__arch_copy_from_user` + `access_ok` — prior art for translate-checked user copies; `flush`/exec zeroing rationale.
