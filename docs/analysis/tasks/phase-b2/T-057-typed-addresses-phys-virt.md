# T-057 — Give PhysAddr/VirtAddr an audited API and use typed addresses at public boundaries

- **Phase:** B.2
- **Milestone:** Track B.2-4
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-042](T-042-pmm-defensive-validation.md), [T-043](T-043-user-access-hardening.md)
- **Informs:** [T-060](T-060-user-access-walk-helper-dedup.md), [T-061](T-061-mechanical-dedup-bundle.md)
- **ADRs required:** none

---

## User story

As a kernel developer, I want `PhysAddr` and `VirtAddr` to carry a small audited arithmetic/alignment API and to appear in the public signatures that today take raw `usize`, so that mixing up a physical address, a virtual address and a plain integer becomes a compile error instead of a latent bug.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from five items in [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-4 (lines 351, 354, 360, 363, 366) plus the Polish item at line 656. `PhysAddr(pub usize)` and `VirtAddr(pub usize)` (`hal/src/mmu/mod.rs:168`, `:164`) are bare wrappers with no methods, so every caller does its arithmetic through `.0`. The two direct-map helpers `phys_to_kernel_va(pa: usize) -> usize` and `kernel_va_to_phys(va: usize) -> usize` (`:104`, `:142`) drop the newtypes they exist to keep apart; the user-copy path (`UserAccessWindow::new(base: usize, len)` at `kernel/src/syscall/user_access.rs:77`, `copy_from_user`/`copy_to_user`/`probe_user_pages` at `:186-192`, `:269`, `:140`), `ContextSwitch::init_user_context` (`hal/src/context_switch.rs:122-128`, two `usize` plus one `*mut u8`) and `Pmm::could_yield_pa_overlapping(&self, Range<usize>)` (`kernel/src/mm/pmm.rs:620`) do the same.

None of this is a live bug; it is cheap now and expensive once Phase C multiplies the call sites. The task touches the public HAL API and about a dozen call sites, so it carries the full verification set (host, Miri, smoke). `PhysFrame::from_aligned` (`hal/src/mmu/mod.rs:185`) is the in-tree model for an alignment-checked constructor.

## Acceptance criteria

- [ ] `PhysAddr` and `VirtAddr` each gain `checked_add(usize) -> Option<Self>`, `wrapping_add(usize) -> Self`, `align_up(usize) -> Self` and `is_aligned_to(usize) -> bool` (`#[must_use]`, `const fn` where possible), documented including the behaviour on overflow and on a non-power-of-two alignment.
- [ ] `phys_to_kernel_va(pa: PhysAddr) -> VirtAddr` and `kernel_va_to_phys(va: VirtAddr) -> PhysAddr`; the hard `assert!` windows at `hal/src/mmu/mod.rs:112` and `:151` are unchanged; all 12 production call sites are migrated (`bsp-qemu-virt/src/mmu.rs:360,520,585`; `bsp-qemu-virt/src/main.rs:1015,1076,1143,1358,1359,1684`; `kernel/src/mm/mod.rs:145`; `kernel/src/mm/pmm.rs:409`; `kernel/src/obj/task_loader.rs:604`). Any raw-`usize` escape hatch kept for asm/linker-symbol interop is `pub(crate)` or otherwise documented as not part of the public surface.
- [ ] `UserAccessWindow::new` takes `base: VirtAddr` (`len` stays `usize`), and `copy_from_user`, `copy_to_user`, `probe_user_pages` and `UserAccessWindow::validate` take `VirtAddr` for the user pointer; callers (`kernel/src/sched/mod.rs:511`, `kernel/src/syscall/dispatch.rs:253,286`, and their tests) are updated.
- [ ] `ContextSwitch::init_user_context` no longer mixes raw `usize` and a raw pointer for the entry, user-stack and kernel-stack arguments; every implementor (`bsp-qemu-virt/src/cpu.rs:601`, `test-hal/src/context_switch.rs:194`, the kernel test fakes at `kernel/src/sched/mod.rs:1685,2627`) and the caller (`kernel/src/sched/mod.rs:486`) is updated. Which of the two alternatives in the phase item was chosen is recorded in the review history.
- [ ] `Pmm::could_yield_pa_overlapping` takes `core::ops::Range<PhysAddr>`; its production caller (`kernel/src/obj/task_loader.rs:606`) and the pmm tests (`kernel/src/mm/pmm.rs:1248,1262,1391`) are updated.
- [ ] Tests: `hal/src/mmu/mod.rs` has no `#[cfg(test)]` module today, so a new one covers every new method at its boundaries (0, `PAGE_SIZE - 1`, `usize::MAX` overflow, `align == 1`) and the typed direct-map round trip. Every pre-existing test passes with mechanical type edits only (no changed assertion); `cargo host-test` (366 tests at HEAD), `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` and `tools/smoke.sh --int` pass.
- [ ] Documentation: append-only revision notes on [ADR-0009](../../../decisions/0009-mmu-trait.md) (its sentence at line 177, "Arithmetic operators are not implemented in v1; callers use `.0`", needs the named-method API recorded) and on [ADR-0037](../../../decisions/0037-el0-entry-context.md) (line 40 quotes the raw-`usize` `init_user_context` signature).

## Out of scope

- Making the `.0` fields private or adding operator impls (`Add`, `BitAnd`): the item asks for named methods only.
- `tyrne-user`'s bare-`u64` capability handle (`CapWord`): [T-064](T-064-tyrne-user-api-polish.md).
- The DEVICE exclusion, zero-length probe and top-page test in `user_access.rs`: [T-043](T-043-user-access-hardening.md) (a dependency). Deduplicating the per-page loop: [T-060](T-060-user-access-walk-helper-dedup.md).
- Correcting the `could_yield_pa_overlapping` doc text at `pmm.rs:560-565`: [T-072](T-072-doc-comment-hygiene.md).
- Turning the direct-map helpers' hard `assert!` into a `Result` (Polish item, `phase-b2.md:655`): tracked as a Phase D forward flag, not changed here.
- The `MapperFlush` AS/ASID discriminant in the same file: [T-040](T-040-mapperflush-asid-discriminant.md).

## Approach

Add the four methods on both newtypes, modelled on `PhysFrame::from_aligned`, then change the signatures listed above and let the compiler find the call sites. Per the item's Action, the direct-map helpers either change signature outright or keep a `pub(crate)` raw-`usize` form with typed public wrappers; the BSP crates cannot use a `pub(crate)` hatch from `hal`, so asm/linker-symbol sites there construct `PhysAddr(..)`/`VirtAddr(..)` explicitly. For `init_user_context` the item offers `VirtAddr` for all three arguments, or a lightweight marker type that distinguishes entry-VA from stack-VA so a transposed pair fails to compile. Keep each step a mechanical type change; no value, assertion or branch may change.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean (BSP call sites change).
- [ ] `cargo host-test` passes with the new tests added.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean.
- [ ] `tools/smoke.sh --int` PASS (kernel and BSP code changed).
- [ ] No new `unsafe`, so no new audit entry. If a signature change alters the wording of an audit entry (for example UNSAFE-2026-0032 in [`unsafe-log.md`](../../../audits/unsafe-log.md)), it is corrected by Amendment.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Choices recorded in the review history (none blocks starting).** (a) `align_up` cannot signal overflow in the Action's signature; the in-file precedent is the hard `assert!` at `hal/src/mmu/mod.rs:112`, and a `checked_` variant could sit beside it. (b) `VirtAddr` for both the entry and the user stack does not by itself make a transposed pair fail to compile, because both are `VirtAddr`; only the marker-type alternative does. (c) Whether the raw-`usize` hatch exists at all. (d) `checked_add` is read as returning `Option<Self>`; the Action's line writes `-> Self` for the pair. (e) `kernel/src/obj/task_loader.rs:605` computes `image_pa_start.saturating_add(image.len())`; the Action's API has no `saturating_add`, so that site either keeps `.0` arithmetic or the API gains one more method.
- **Not host-testable.** The 4 GiB window assertions short-circuit on host (`KERNEL_HIGH_HALF_OFFSET == 0`), so the typed helpers' panic paths are exercised only by the kernel build.
- **Sequencing.** After [T-042](T-042-pmm-defensive-validation.md) (`pmm.rs`) and [T-043](T-043-user-access-hardening.md) (`user_access.rs`, including `probe_user_pages`); before [T-060](T-060-user-access-walk-helper-dedup.md), which writes its helper against the final signatures, and [T-061](T-061-mechanical-dedup-bundle.md), which edits `MappingFlags` in the same `hal/src/mmu/mod.rs`. [T-071](T-071-unsafe-contract-hardening.md) edits `add_user_task`, which forwards to `init_user_context`; whichever lands second rebases.
- **Re-verification (2026-10-11).** Every code location above was re-checked with `grep -n`/`sed -n` against the current tree; none had drifted. `phase-b2.md` line numbers are from the live file, which is 2 lines longer than the pre-kickoff snapshot used for planning (was 349, 352, 358, 361, 364, 653 and 654).

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
