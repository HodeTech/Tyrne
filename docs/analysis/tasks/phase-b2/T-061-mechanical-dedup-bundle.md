# T-061 — Remove mechanical duplication (object boilerplate, bitflag types, descriptor encoders, GIC enable/disable)

- **Phase:** B.2
- **Milestone:** Track B.2-4
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-057](T-057-typed-addresses-phys-virt.md)
- **Informs:** none
- **ADRs required:** none (a short rider or ADR if the bitflags-crate question is closed here; see the last criterion)

---

## User story

As a maintainer of the audited kernel and HAL surface, I want four pieces of mechanically duplicated code collapsed into one definition each, so that a fix cannot land in one copy and be missed in its twin and the audited surface shrinks.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from four LOW items in [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-4 (lines 380, 383, 386, 389) plus the bitflags Polish item at line 574. The duplications: the handle-wrapper plus `create_*`/`destroy_*`/`get_*` boilerplate in `kernel/src/obj/endpoint.rs:37-120`, `notification.rs:48-109` and `task.rs:64-128`; the hand-rolled bitflag types `MappingFlags` (`hal/src/mmu/mod.rs:220-315`) and `CapRights` (`kernel/src/cap/rights.rs:18-129`); `block_descriptor` and `page_descriptor` (`hal/src/mmu/vmsav8.rs:451-463`, `:479-490`); and `QemuVirtGic::enable`/`disable` (`bsp-qemu-virt/src/gic.rs:316-340`, `:342-362`).

All four are **pure refactors with zero behaviour change** and the existing tests must pass unchanged. It follows [T-057](T-057-typed-addresses-phys-virt.md) because both edit `hal/src/mmu/mod.rs` (`PhysAddr`/`VirtAddr` and `MappingFlags` live in the same file).

## Acceptance criteria

- [ ] Object boilerplate: a `macro_rules! typed_object_arena!` (or a generic `TypedHandle<Kind>` plus free functions) in `kernel/src/obj/arena.rs` generates the handle wrapper, the arena alias and `create_*`/`destroy_*`/`get_*` for the three kinds. Public names and signatures are unchanged (`EndpointHandle`, `create_endpoint`, `destroy_endpoint`, `get_endpoint` and the `Notification`/`Task` equivalents, plus the `#[cfg(test)]` `test_handle`). The C3-001 hazard documentation on `destroy_endpoint` (`endpoint.rs:78-109`) is preserved and `cargo host-clippy` stays free of `missing_docs` warnings; the `wc -l` of the three modules before and after is recorded.
- [ ] Bitflag types: one `macro_rules!` generates the shared body of `MappingFlags` and `CapRights`, with an option that omits `BitAndAssign`/`SubAssign`, so `CapRights` stays deliberately narrowing (the rationale comment at `rights.rs:131-139` survives). Two differences are preserved on purpose: `CapRights::from_raw` masks to `KNOWN_BITS` (`rights.rs:90`) while `MappingFlags::from_raw` keeps unknown bits (`mmu/mod.rs:256`). A `compile_fail` doctest pins that `CapRights` has no `&=`/`-=`. Where the macro lives (exported from `hal`, which `kernel` already depends on, or a new internal workspace crate) is recorded in the review history.
- [ ] Descriptor encoders: a private `fn leaf_descriptor(pa: u64, bits: DescriptorBits, is_page: bool, oa_mask: u64) -> u64` carries the shared bit composition; `block_descriptor` and `page_descriptor` stay `pub const fn` one-liners with unchanged docs. A differential test compares both against an in-test copy of the pre-refactor bodies over every `DescriptorBits` combination (`attr_idx` 0..=7, `ap` 0..=3, `sh` 0..=3, `ng`, `pxn`, `uxn`) and several PAs including unaligned ones.
- [ ] GIC: a private `fn set_bit_register(&self, base: usize, irq: IrqNumber)` holds the offset and bit computation; `enable` and `disable` become one-line callers passing `GICD_ISENABLER_BASE` (`0x100`) and `GICD_ICENABLER_BASE` (`0x180`). The two assertion messages are byte-identical to today's. A table of the computed register offset and bit for IRQ 0, 27, 31, 32 and 1019 under both bases, equal before and after, is recorded in the review history. Audit entry UNSAFE-2026-0019 (its Location names `enable`/`disable`) is amended per [`unsafe-policy.md`](../../../standards/unsafe-policy.md) if the `unsafe` block moves into the helper.
- [ ] Tests and gates: all pre-existing tests pass with no edited assertion; before the macro change, characterization tests for `MappingFlags` (union, intersection, difference, `contains`, `is_empty`, the three operators, `from_raw`/`raw` round trip with unknown bits) are committed, since `hal/src/mmu/mod.rs` has none today; `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean; `cargo kernel-clippy` clean; `tools/smoke.sh --int` PASS.
- [ ] Bitflags-crate decision recorded (Polish, `phase-b2.md:574`): "still no" or "adopt", as an append-only revision-note rider on [ADR-0009](../../../decisions/0009-mmu-trait.md) (open question, line 220) and [ADR-0014](../../../decisions/0014-capability-representation.md) (line 252), or as a new ADR. If "still no", the two doc comments that point at the open question (`mmu/mod.rs:214-216`, `rights.rs:3-4`) are updated; adopting the crate would be a dependency addition and follows the `add-dependency` skill and `cargo-vet` rules, which is why the default expectation is "still no".

## Out of scope

- Reconciling or changing the diverging `from_raw` unknown-bit semantics (Polish item, `phase-b2.md:658`): this task only preserves them.
- Typed `get_*_mut` wrappers and the `(table, pmm, mmu, as_arena)` context-struct bundle (separate Polish items).
- The module doc-comment corrections in `endpoint.rs`/`notification.rs`/`task.rs`: [T-072](T-072-doc-comment-hygiene.md) (`phase-b2.md:496`).
- Arena internals and the capability table: [T-058](T-058-capability-table-on-arena.md) and [T-068](T-068-kernel-tests-and-nits-bundle.md). The fourth instance of the handle pattern, `AddressSpaceHandle` (`kernel/src/mm/address_space.rs:163`), is not in the item; adopting the macro there is optional and must be recorded if done.

## Approach

`macro_rules!` only, unless the bitflags decision says otherwise. For the handle macro, take the per-kind doc strings as macro arguments so the endpoint's long hazard note survives. For the bitflag macro, parameterise the type name, the raw type, whether to generate the in-place narrowing operators, and the `from_raw` masking behaviour. For the descriptor encoders, pass the page-bit and OA mask into the shared helper. For the GIC, factor out the register-offset and bit computation and keep a single `unsafe` call with a SAFETY comment valid for both the set-enable and clear-enable banks.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean (the GIC and BSP code change).
- [ ] `cargo host-test` passes with the new tests added.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean.
- [ ] `tools/smoke.sh --int` PASS (kernel and BSP code changed).
- [ ] No new `unsafe`; the one moved GIC `unsafe` block keeps its SAFETY comment and audit tag (UNSAFE-2026-0019), amended if needed.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040` (and `Audit: UNSAFE-2026-0019` if amended); one commit per duplication keeps each reviewable.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **GIC verification limit.** `bsp-qemu-virt` has no `#[test]` target, and `grep -rn 'arm_deadline\|cancel_deadline'` finds no caller of `Timer::arm_deadline`/`cancel_deadline` (the only users of `gic.enable`/`gic.disable`, at `bsp-qemu-virt/src/cpu.rs:723`, `:747`) outside the trait definition and its implementations, so the smoke run does not exercise these two functions. The offset table and review of the diff are the evidence; `tools/smoke.sh --int` only proves the boot path is unchanged.
- **Sequencing.** After [T-057](T-057-typed-addresses-phys-virt.md). `obj/arena.rs` is also edited by [T-058](T-058-capability-table-on-arena.md) and [T-068](T-068-kernel-tests-and-nits-bundle.md), and `rights.rs` is read by [T-059](T-059-capability-resolve-typed-primitive.md); no order is imposed, whichever lands second rebases.
- **Re-verification (2026-10-11).** All code ranges above were re-checked with `sed -n`/`grep -n` (the three object modules' `get_*` functions end at lines 120, 109 and 128; `CapRights` and its inherent `impl` span `rights.rs:18-129`); no drift. The `phase-b2.md` lines are from the live file (was 378, 381, 384, 387 and 572 in the pre-kickoff snapshot).

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
