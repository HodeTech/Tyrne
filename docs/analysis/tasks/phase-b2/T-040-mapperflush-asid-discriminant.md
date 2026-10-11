# T-040 — Add an AS/ASID discriminant to MapperFlush

- **Phase:** B.2
- **Milestone:** Track B.2-3
- **Status:** Draft
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** Phase C Milestone C5, multi-core TLB shootdown ([`phase-c.md`](../../../roadmap/phases/phase-c.md))
- **ADRs required:** an append-only revision-note rider on [ADR-0009](../../../decisions/0009-mmu-trait.md) (precedent: the T-016 / ADR-0027 rider at ADR-0009 line 225), or a new ADR if the public shape changes beyond the token; decide and record (see Open decisions)

---

## User story

As the MMU abstraction, I want a flush token to be bound to the address space it was minted for, so that flushing a token against the wrong address space is rejected instead of silently invalidating the wrong TLB entry.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from the HIGH item at [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) line 283. `MapperFlush` (`hal/src/mmu/mod.rs:394`) is `MapperFlush(VirtAddr)`: it stores only a virtual address, and `flush<M: Mmu + ?Sized>(self, mmu: &M)` (`:432`) calls `mmu.invalidate_tlb_address(va)` (trait method at `:632`, which takes no address-space argument). The doc comment at `hal/src/mmu/mod.rs:376-386` excuses this because "v1 has a single `Mmu` instance and a single address space" and says "the multi-AS step (flagged in ADR-0027) must add an AS/ASID discriminant ... and make `flush` reject a mismatch". That premise is stale: Phase B shipped multi-address-space infrastructure (the arena-backed `AddressSpace` objects of ADR-0028, `cap_map`/`cap_unmap` in `kernel/src/mm/address_space.rs:728,775`, and the task loader's `cap_map` calls at `kernel/src/obj/task_loader.rs:701,756`), and a real EL0 task runs in its own address space. Today the BSP uses ASID 0 globally (`bsp-qemu-virt/src/mmu.rs:392-395`), so nothing is mis-invalidated in practice. The cliff is that nothing in the type system prevents it once ASIDs differ.

The phase item asks for the discriminant to land as a prerequisite for, or together with, the first real per-task `cap_map` call. The loader's calls (above) mean that call already exists, so the practical deadline is now: before Phase C work depends on a per-AS flush discipline. Milestone C5 (multi-core TLB shootdown) needs a per-AS/ASID-aware flush before it can safely broadcast invalidations.

## Acceptance criteria

- [ ] Decision recorded, per Open decisions below: the representation of the discriminant, what `flush` compares it against, and the failure mode. The record is an append-only ADR-0009 revision-note rider (or a new ADR if the public `Mmu` shape changes beyond the token) and it is Accepted before the code lands.
- [ ] `MapperFlush` carries the discriminant, and every token minter is updated: `QemuVirtMmu::map`/`unmap` (`bsp-qemu-virt/src/mmu.rs:296,323`), the `test-hal` fakes (`FakeMmu`, `OutOfFramesMmu` and `BlockMappedMmu`, `test-hal/src/mmu.rs:178,358,512`), and the test `FailingMapMmu` in `kernel/src/obj/task_loader.rs` (`:2115,2148,2165`).
- [ ] A token can only be flushed against the address space it was minted for: with a compile-time brand a mismatch is a type error; with a stored identity `MapperFlush::flush` rejects a mismatched token using the chosen failure mode. The kernel's `cap_map` and `cap_unmap` flush sites (`kernel/src/mm/address_space.rs:744,788`) keep working unchanged in behaviour for matching tokens.
- [ ] Tests follow the chosen representation. **Compile-time brand:** a `compile_fail` doctest (or equivalent) shows that flushing a token minted for address space A against address space B does not compile. **Stored identity (a token can reach a flush for another address space):** a `test-hal` test shows the mismatched flush is rejected with the chosen failure mode and invalidates nothing. In both cases a test shows a matching flush still invalidates; the existing token tests (`test-hal/src/mmu.rs:868-905`) are updated; a kernel address-space test exercises two distinct address spaces through `cap_map` (extending `cap_map_installs_mapping_and_flushes_tlb`, `address_space.rs:1161`).
- [ ] Documentation: the `MapperFlush` doc comment (`hal/src/mmu/mod.rs:376-386`) drops the single-address-space caveat and describes the new check; `docs/architecture/memory-management.md` section "The `MapperFlush` flush-token discipline" (line 112) matches.

## Out of scope

- A per-AS ASID allocator and ASID-tagged `TLBI`/`TTBR0` encoding in the BSP (a Polish item in `phase-b2.md`, line 648; it needs its own decision).
- Multi-core TLB shootdown, inner-shareable `TLBI` encodings, and `activate()` ordering: Phase C Milestone C5 and the Phase C backlog.
- Changing the capability layer or `AddressSpace` object lifetime rules.

## Approach

The phase item suggests two representations: a `PhantomData` address-space id, or a stored ASID, with `flush` rejecting a mismatch. Which one fits depends on what exists today. The BSP has no ASID values (all zero), and `invalidate_tlb_address` has no address-space parameter, so "reject a mismatch" needs something to compare against: either `flush` takes the target address space, or `invalidate_tlb_address` becomes address-space-aware, or the check is purely type-level. The `Mmu` trait already exposes a per-address-space identity, `address_space_root(&Self::AddressSpace) -> PhysFrame` (`hal/src/mmu/mod.rs:491`), which a minting `Mmu` could record. This task must pick one, record it, then implement it across the minters and tests listed above.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes with the new tests added.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean (hal, test-hal and kernel code change).
- [ ] `tools/smoke.sh --int` PASS (the BSP `Mmu` impl changes).
- [ ] Any changed `unsafe` has an Amendment in [`unsafe-log.md`](../../../audits/unsafe-log.md) (for example UNSAFE-2026-0024, the `TLBI VAE1` site, if its operand encoding changes) per [`unsafe-policy.md`](../../../standards/unsafe-policy.md).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0009` (and `Refs: ADR-0040`) and, if applicable, `Audit:` / `Security-Review:` trailers.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions.**
  1. Representation: a type-level (`PhantomData`) address-space id, a stored identity (for example the root frame, or the arena handle), or a stored ASID (all zero today, so it discriminates nothing until an allocator exists).
  2. What `flush` compares against: a new address-space parameter on `flush`, an address-space-aware `invalidate_tlb_address`, or a compile-time brand with no runtime check.
  3. Failure mode on mismatch. A panic in `flush` conflicts with the panic-family deny that [T-032](T-032-panic-family-denies-hal-bsp.md) adds to `tyrne-hal` unless it carries a scoped `#[allow]` with a reason; a `Result` return changes every call site. Prefer the option that keeps the kernel dispatch path panic-free.
  4. ADR-0009 rider versus a new ADR, depending on how far the public shape moves (project rule 5; `phase-b2.md` closing note).
- **Relevance to C5.** The chosen discriminant is what a TLB-shootdown protocol would carry across cores; keep it small and `Copy`.
- **Re-verification (2026-10-11).** All hal, test-hal, kernel and BSP locations above were checked against the current tree. The item's range `hal/src/mmu/mod.rs:376-386` is exact. `phase-b2.md` line 283 is the live number after the kickoff banner (+2). The stale "never invokes `cap_map`" remark in the `cap_map` doc comment (`kernel/src/mm/address_space.rs:699-704`) is noted here but not owned by this task.
- **Sequencing.** No task dependency. Land after [T-041](T-041-blockmappedmmu-already-mapped.md) if both touch `test-hal/src/mmu.rs` in the same window, to avoid conflicts (soft, not a dependency).

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Draft |
