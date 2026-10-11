# T-044 — Reconcile the bootstrap address-space handle with the real allocation

- **Phase:** B.2
- **Milestone:** Track B.2-3
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** none (relevant to Phase C Milestone C2, per-core state; see Design notes)
- **ADRs required:** none

---

## User story

As the BSP's kernel-init path, I want the bootstrap address-space handle that tasks are created against to be the handle the arena actually returned (and a checked invariant where the constant is still used), so that a reordering of init code cannot silently point every bootstrap task at the wrong address space.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from the MEDIUM item at [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) line 298 and the Polish item at line 626 ("Assert the bootstrap-handle ordering invariant at the BSP call site"), which is the same fix. `kernel/src/mm/address_space.rs:59` defines `BOOTSTRAP_ADDRESS_SPACE_HANDLE` as `AddressSpaceHandle::from_slot(SlotId::first_slot())`, i.e. arena index 0, generation 0 (`kernel/src/obj/arena.rs:57-73`). It is a compile-time guess that holds only if the bootstrap address space is the first allocation in the address-space arena, a calling discipline recorded in prose (`address_space.rs:42-58`).

The BSP does allocate the real handle: `bsp-qemu-virt/src/main.rs:1176-1186` stores `create_address_space(...)` in `bootstrap_as_handle` and uses it for the bootstrap capability (`:1203`). But the three kernel demo tasks are then created with the constant instead (`Task::new(0|1|2, tyrne_kernel::mm::BOOTSTRAP_ADDRESS_SPACE_HANDLE)`, `main.rs:1424-1434`), as are the `add_task`/`register_idle` calls (`:1579`, `:1588`, `:1624`) and the `perf-bench` scenario (`bsp-qemu-virt/src/perf_bench.rs:201-205`, `:300`, `:309`, `:318`). Nothing reconciles the two values. If a refactor allocated another address space first, the constant would silently name the wrong arena slot.

## Acceptance criteria

- [ ] Immediately after the real allocation (after `main.rs:1186`) the BSP asserts `debug_assert_eq!(bootstrap_as_handle, tyrne_kernel::mm::BOOTSTRAP_ADDRESS_SPACE_HANDLE, "bootstrap AS allocation invariant violated: first_slot() assumption broken")`.
- [ ] The real `bootstrap_as_handle` is threaded to the BSP's `Task::new` call sites (`main.rs:1424`, `:1429`, `:1434`; `perf_bench.rs:201`, `:203`, `:205`) and to the `add_task`/`register_idle` calls that take the same constant (`main.rs:1579`, `:1588`, `:1624`; `perf_bench.rs:300`, `:309`, `:318`), so no BSP production path relies on the assumed constant. If a site must keep the constant, the review history says which and why.
- [ ] Documentation: the doc comment of `BOOTSTRAP_ADDRESS_SPACE_HANDLE` (`address_space.rs:42-58`) and the `Task::new` doc (`kernel/src/obj/task.rs:31-36`) state that the BSP now asserts the allocation order and passes the real handle.
- [ ] Tests: `tools/smoke.sh --int` PASS in a debug build (so the new `debug_assert_eq!` executes) with the same trace and fault class as before; `cargo kernel-build` (debug and `--release`) and `cargo build --target aarch64-unknown-none -p tyrne-bsp-qemu-virt --features perf-bench` compile, since `perf_bench.rs` changes. The BSP has no host test target, so the assertion's coverage is the smoke run; note that `debug_assert_eq!` is compiled out of release builds.

## Out of scope

- Collapsing or type-distinguishing `wrap_bootstrap` versus `from_mmu_address_space` (a separate Polish item, `phase-b2.md` line 625).
- Per-core current-task pointers and the rest of Milestone C2.
- Changing `SlotId::first_slot()` or the arena allocation order; this task only checks and carries the real value.
- Kernel-crate tests that use the constant (`kernel/src/obj/task.rs:139-186` and similar); they run against a controlled fixture arena where the constant is correct by construction.

## Approach

Add the `debug_assert_eq!` exactly as the phase item words it, right after the `unsafe` block that allocates the bootstrap address space, converting the prose discipline into a loud invariant in debug builds. Then do the phase item's "better still": replace the constant with the in-scope `bootstrap_as_handle` (it is `Copy`, and `kernel_main_high` encloses all the `main.rs` sites) at each call site listed above. `perf_bench::run(cpu, console)` (`perf_bench.rs:147`) takes no handle today, so its sites need either an added parameter or a read of the handle where `perf_bench.rs` already pulls `BOOTSTRAP_AS_CAP`/`AS_ARENA` from the BSP statics (`:174-178`); choose the smaller change and keep the `perf-bench` build green.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes (no host-test changes expected; the kernel crate is not modified beyond doc comments).
- [ ] `tools/smoke.sh --int` PASS (BSP code changes).
- [ ] No new `unsafe`; the assertion sits outside the existing `unsafe` block, so no audit entry is needed. UNSAFE-2026-0028's own text is corrected by [T-069](T-069-unsafe-log-corrections.md), not here.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0028` and `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Relevance to C2.** Milestone C2 (per-core state, including a per-core current-task pointer) multiplies the places that name an address space for a task. Removing the assumed constant from the BSP now means C2 starts from a checked value rather than a convention. See [`phase-c.md`](../../../roadmap/phases/phase-c.md).
- **Re-verification (2026-10-11).** The item's locations were checked against the current tree: `arena.rs:57-73` (doc and `first_slot`), `address_space.rs:59`, `main.rs:1176-1186` and `:1424-1434` hold. The item listed only the `Task::new` sites; the `add_task`/`register_idle` and `perf_bench.rs` sites above carry the same assumption and were found by `grep -rn BOOTSTRAP_ADDRESS_SPACE_HANDLE bsp-qemu-virt/src`. `phase-b2.md` lines 298/626 are live numbers after the kickoff banner (+2).
- **Sequencing.** Independent of the other Track B.2-3 tasks. If [T-032](T-032-panic-family-denies-hal-bsp.md) has landed, a `debug_assert_eq!` is not caught by `clippy::panic`; no allow is needed.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
