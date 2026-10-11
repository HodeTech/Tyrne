# T-058 — Rebase CapabilityTable storage on the shared Arena

- **Phase:** B.2
- **Milestone:** Track B.2-4
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-059](T-059-capability-resolve-typed-primitive.md)
- **ADRs required:** none

---

## User story

As the kernel's capability subsystem, I want my slot, free-list and generation storage to come from the one shared `Arena`, so that the most security-critical free-list/generation pattern in the kernel exists, and is audited, exactly once.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from the item at [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) line 371 (Track B.2-4). `kernel/src/cap/table.rs` hand-implements a slot array, a free list and per-slot generation counters (`Slot`, `SlotEntry`, `CapabilityTable::new`, lines 86-156; `resolve_handle`, `entry_of`, `pop_free`, `link_child`, `free_slot`, lines 563-654). `kernel/src/obj/arena.rs` (lines 16-215) is the same machinery written generically, and `AddressSpaceArena` already instantiates it (`kernel/src/mm/address_space.rs:201`). A fix to one copy can silently miss the other; [ADR-0016](../../../decisions/0016-kernel-object-storage.md) already describes the arena as "the same shape as `CapabilityTable`".

This is a security-sensitive refactor: `CapabilityTable` is the authority store. **No behaviour change is allowed.** Every `CapHandle` value (`(u16 index, u32 generation)`, packed into a register word by `kernel/src/syscall/abi.rs`, with the `NULL_CAP_HANDLE` const-assert at `abi.rs:41-44`), every `CapError` result and the free-list reuse order must stay bit-for-bit identical. Capabilities are a mandatory trigger in [`security-review.md`](../../../standards/security-review.md).

## Acceptance criteria

- [ ] `CapabilityTable` stores its entries in `Arena<SlotEntry, CAP_TABLE_CAPACITY>`; the hand-rolled `Slot`, `free_head`, `pop_free` and `free_slot` machinery (`table.rs:88-93,108-111,588-593,642-654`) is gone. Arena's `Option` results are converted to `CapError` inside the table (no free slot becomes `CapsExhausted`, stale or empty becomes `InvalidHandle`), with every existing mapping unchanged.
- [ ] No behaviour change: the 36 existing tests in `kernel/src/cap/table.rs` pass with no edited assertion (`git diff` shows additions only inside `mod tests`), including `slot_entry_size_matches_adr_0023` (`SlotEntry` stays 32 bytes), and so does the whole `cargo host-test` suite (366 tests at HEAD).
- [ ] A characterization test is committed first, green on the old implementation: it replays a fixed script (`insert_root`, `cap_copy`, `cap_derive`, `cap_drop`, `cap_take`, `cap_revoke`, re-insert into freed slots, table exhaustion) and asserts the exact `index()` and `generation()` of every returned handle and that a freed slot is reused next (LIFO). It stays green, unedited, after the rebase.
- [ ] Failure atomicity is pinned: a new test shows `cap_copy` and `cap_derive` returning `CapsExhausted` on a full table leave the source's child list untouched (a following `cap_drop(parent)` still succeeds without `HasChildren`). The existing `cap_derive_on_full_table_returns_caps_exhausted` (`table.rs:1167`) asserts only that the parent stays live.
- [ ] Any new `Arena` API the rebase needs (index-addressed access, iteration for `references_object`, a production `SlotId` constructor; see Design notes) is `pub(crate)`, minimal, and covered by unit tests in `arena.rs`. `CapHandle` keeps its `(u16, u32)` shape and its `from_raw`/`index`/`generation` accessors.
- [ ] Tests and gates: `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean; `tools/smoke.sh --int` PASS.
- [ ] Security review recorded: the PR declares capability relevance, the reviewer works the Capability-correctness checklist in [`security-review.md`](../../../standards/security-review.md), and the outcome is in the review history and the `Security-Review:` trailer.
- [ ] Documentation: append-only revision note on [ADR-0014](../../../decisions/0014-capability-representation.md) (its Table layout section shows the inline `slots`/`free_head` layout); the `arena.rs` module doc (lines 9-11, "mirrors the `CapabilityTable`") and the `table.rs` module doc describe the shared storage.

## Out of scope

- The typed resolution primitive: [T-059](T-059-capability-resolve-typed-primitive.md) (it builds on this storage).
- Arena hygiene (capacity const-assert off-by-one, `#[must_use]` on `allocate`, generation-wrap documentation or slot retirement): [T-068](T-068-kernel-tests-and-nits-bundle.md). Generation semantics must not change here.
- A reverse index or refcount for `references_object`, and the cross-table CDT question (ADR-0023): Polish items, not this task.
- The typed-handle `macro_rules!` for the object modules: [T-061](T-061-mechanical-dedup-bundle.md).
- Changing `CAP_TABLE_CAPACITY` (64) or `MAX_DERIVATION_DEPTH` (16).

## Approach

Rebase on `Arena<SlotEntry, CAP_TABLE_CAPACITY>` as `AddressSpaceArena` does, and convert Arena's `Option`-based errors to the appropriate `CapError` at the table boundary (phase-b2.md line 372). Keep `SlotEntry` and its raw-index tree links (`parent`, `first_child`, `next_sibling`) as they are; the 32-byte size test and the revoke/unlink walks depend on them. Land the characterization test first in its own commit so a reviewer sees it pass on both implementations.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes with the new tests added.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean.
- [ ] `tools/smoke.sh --int` PASS (kernel code changed).
- [ ] No `unsafe` is introduced (`table.rs` and `arena.rs` have none today); no audit entry is expected.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040` and a `Security-Review: <reviewer>` trailer.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Constraints the plan item does not spell out (read from the code).** (1) `Arena` has no index-only accessor, no iterator and no production `SlotId` constructor (`SlotId::from_parts` is `#[cfg(test)]`, `arena.rs:53`), yet the tree links are raw indices, `cap_revoke` frees collected indices, `references_object` scans every slot and `CapHandle::from_raw` rebuilds a handle from untrusted raw parts; the rebase therefore adds crate-internal Arena surface, and that surface is the part to review hardest. A forged `SlotId` must keep failing lookup exactly as a forged `CapHandle` does today. (2) `Arena::allocate` takes the value up front, whereas `cap_copy`/`cap_derive` pop the slot, splice it into the parent's child list via `link_child` (which needs the new index) and only then write the entry; the rebase must keep "`CapsExhausted` leaves no partial state". (3) `Arena::new` and `CapabilityTable::new` are both non-`const`.
- **Open implementation choices** (recorded in the review history, none blocks starting): the shape of the Arena accessors, and whether `CapHandle` wraps a `SlotId` or keeps its own fields.
- **Sequencing.** Before [T-059](T-059-capability-resolve-typed-primitive.md). `obj/arena.rs` is also edited by [T-068](T-068-kernel-tests-and-nits-bundle.md) and [T-061](T-061-mechanical-dedup-bundle.md); no order is imposed, whichever lands second rebases.
- **Re-verification (2026-10-11).** `table.rs:86-156` and `:563-654` still bound the cited code, `arena.rs:16-215` still bounds `Arena`, and `AddressSpaceArena` is at `address_space.rs:201`; no drift. The `phase-b2.md` line is from the live file (was 369 in the pre-kickoff snapshot).

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
