# T-041 — Make BlockMappedMmu::map return AlreadyMapped

- **Phase:** B.2
- **Milestone:** Track B.2-3
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** none
- **ADRs required:** none

---

## User story

As the kernel test suite, I want the `BlockMappedMmu` fake to return exactly what the real MMU walker returns when `map` hits a block descriptor, so that the kernel tests that trust it pin the real contract instead of a fiction.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from the HIGH item at [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) line 316. The `Mmu::map` contract in `hal/src/mmu/mod.rs:545-551` says a `va` inside an existing large block returns `MmuError::AlreadyMapped` on `map`, explicitly **not** `BlockMapped`, while `unmap` and `translate` do return `BlockMapped` ("the asymmetry is deliberate"). The real walker does this (`bsp-qemu-virt/src/mmu.rs:590-612`: `Err(if unmap { BlockMapped } else { AlreadyMapped })`). The fake does not: `BlockMappedMmu::map` (`test-hal/src/mmu.rs:533-547`) returns `Err(MmuError::BlockMapped)`, and its own test `block_mapped_mmu_injects_block_mapped_on_map_and_unmap` (`:1101-1124`) asserts the wrong value at `:1117`. Two kernel tests then pin the fake's behaviour as if it were the contract.

The kernel suite trusts the test-HAL fakes, so a fake that disagrees with the trait contract makes green tests prove the wrong thing. Today the error is only a variant name inside rollback tests, but any future kernel code that branches on `AlreadyMapped` versus `BlockMapped` from `map` would be tested against the wrong behaviour.

## Acceptance criteria

- [ ] `BlockMappedMmu::map` (`test-hal/src/mmu.rs:533-547`) returns `Err(MmuError::AlreadyMapped)` for a blocked `va`, still before any state change (no mapping installed, `pa` not consumed). `unmap` (`:549-558`) and `translate` (`:560-574`) keep returning `BlockMapped`.
- [ ] The in-file test `block_mapped_mmu_injects_block_mapped_on_map_and_unmap` asserts `AlreadyMapped` from `map` and `BlockMapped` from `unmap`, and still asserts the address space is unmodified; rename it if the old name would now mislead.
- [ ] Kernel tests updated to the contract: `cap_map_propagates_block_mapped_and_leaves_no_mapping` (`kernel/src/mm/address_space.rs:1384-1454`, assertion at `:1414`) expects `AddressSpaceError::MmuMapError(MmuError::AlreadyMapped)`; `rolls_back_on_block_mapped_mid_image_loop` (`kernel/src/obj/task_loader.rs:2502-2542`, assertion at `:2529`) expects `LoadError::MapFailed(MmuMapError(AlreadyMapped))`. Their no-mapping, no-frame-consumed and rollback-accounting assertions are unchanged, and the stale comments naming `BlockMapped` are fixed.
- [ ] Documentation: the `LoadError::MapFailed` doc comment (`kernel/src/obj/task_loader.rs:394-401`) no longer says a block hit surfaces as `BlockMapped` from `map`; the `BlockMappedMmu` rustdoc and doctest (`test-hal/src/mmu.rs:433-461`) and the `test-hal/src/lib.rs:21-27` crate note describe the split (`map` gives `AlreadyMapped`; `unmap` and `translate` give `BlockMapped`).
- [ ] Tests: `cargo host-test` passes with the updated tests; the translate-path coverage that relies on `BlockMapped` (`kernel/src/syscall/user_access.rs:511-515`) passes unchanged.

## Out of scope

- Changing `unmap` or `translate` behaviour in the fake or the real walker; both are correct today.
- The `MapperFlush` address-space discriminant, which also touches `test-hal/src/mmu.rs`: [T-040](T-040-mapperflush-asid-discriminant.md).
- Adding block-splitting (deferred in the `Mmu` contract) or any change to the real `QemuVirtMmu`.

## Approach

Change only `BlockMappedMmu::map`, as the phase item states: return `Err(MmuError::AlreadyMapped)` for a blocked `va`, leaving `unmap` and `translate` returning `BlockMapped`. Then update the in-file test, the two dependent kernel tests, and the doc comments listed above so every statement of the behaviour agrees with the `Mmu::map` contract at `hal/src/mmu/mod.rs:545-551` and the real walker.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean (test-hal and kernel code change).
- [ ] No BSP, userland or kernel runtime code changes, so `tools/smoke.sh --int` is not required.
- [ ] No `unsafe` change, so no audit entry.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Re-verification (2026-10-11).** All locations were checked against the current tree. Two ranges in the phase item are slightly short: the whole `cap_map` test is `address_space.rs:1384-1454` (the item said `1384-1439`) and the whole loader test is `task_loader.rs:2502-2542` (the item said `2504-2539`); the fix is the same. `phase-b2.md` line 316 is the live number after the kickoff banner (+2).
- **Why `AlreadyMapped`.** The trait doc reasons that the requested 4 KiB slot is structurally occupied by the block and block-splitting is deferred; `BlockMapped` on `map` would invite callers to treat it as retryable after a split that does not exist.
- **Sequencing.** Independent. If [T-040](T-040-mapperflush-asid-discriminant.md) lands first, rebase onto its `test-hal/src/mmu.rs` changes (soft ordering only).

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
