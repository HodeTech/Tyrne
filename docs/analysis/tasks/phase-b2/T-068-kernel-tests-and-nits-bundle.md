# T-068 — Close kernel test gaps and clean up nits

- **Phase:** B.2
- **Milestone:** Track B.2-4
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** none
- **ADRs required:** none

---

## User story

As the kernel's IPC, arena and scheduler code, I want my designed-but-untested paths pinned by tests and my misleading docs, bounds and messages corrected, so that Phase C can change this code with the regressions already caught.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from the "Testing gaps & misc hygiene" and "Misc" groups of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-4 (eleven LOW / INFO items between lines 415 and 449, located by their lead words below). None is a live bug: they are an ambiguous doc comment, three regression tests that were never written, an over-conservative const-assert, a missing `#[must_use]`, an undocumented generation-wrap bound, missing defensive pointer asserts, one misleading panic message, one test that injects private state instead of driving the public sequence, a redundant path qualifier and a stale BSP comment. They are bundled so the discipline lands once; the criteria are grouped by area to stay within the limit.

The state that Phase C will touch is exactly this code: the endpoint queues (`kernel/src/ipc/mod.rs`), the shared `Arena` (`kernel/src/obj/arena.rs`), and the raw-pointer scheduler bridge (`kernel/src/sched/mod.rs`). Behaviour changes are limited to two: the Arena capacity bound is widened by one, and `#[must_use]` can turn an ignored `allocate` result into a compile error.

## Acceptance criteria

- [ ] IPC docs: `IpcQueues::peek_state` (`ipc/mod.rs:278-281`, call-site comment `:330-333`) is no longer described as side-effect-free; either its doc says "non-destructive to any live endpoint's observable state" while noting it takes `&mut self` and may reset a stale-generation slot, or it is renamed `state_for_read` with every call site updated. Record which.
- [ ] IPC tests, each failing before and passing after where a behaviour is pinned: (a) a self-transfer test calls `ipc_send(.., ep_cap, .., Some(ep_cap))` (the cap needs `SEND` and `TRANSFER`), asserts success, that the sender's table no longer resolves `ep_cap`, and that the receiver obtains a valid capability to the same endpoint; (b) a companion to `stale_send_pending_with_some_cap_panics_in_debug` (`ipc/mod.rs:1668-1686`) drives the public sequence (`ipc_send` with `Some(xfer_cap)`, `cap_drop` + `destroy_endpoint`, fresh `create_endpoint` into the same slot, a subsequent IPC op) and is `#[should_panic]` in debug.
- [ ] Arena bound: the const-assert (`arena.rs:109-112`) becomes `N <= (Index::MAX as usize) + 1` (underflow-safe for `N == 0`) with an updated message, the stale `N <= u16::MAX` wording in `new()`'s doc and in-code comments is fixed, and `Arena::allocate` (`arena.rs:145`) gets `#[must_use]` (optionally `free`). `grep -rn "\.allocate(" kernel bsp-qemu-virt` shows no call site that discards the result, since the workspace denies `unused_must_use`.
- [ ] Arena generation: the wrap-around bound is documented on `Generation` / `Arena::free` (`arena.rs:20`, `:169`: a `u32` that wraps after 2^32 frees of one slot) as an accepted, reviewed trade-off. Whether to also retire a slot at `Generation::MAX` is decided and recorded; implemented only if chosen.
- [ ] Scheduler tests: (a) `register_idle` twice is `#[should_panic(expected = "register_idle called twice")]` (`sched/mod.rs:787-800`); (b) `enqueue_ready` on a full `sched.ready` is `#[should_panic]` (`:598-609`); (c) `QueueFull` is returned by both `add_task` (`:392`) and `add_user_task` (`:497`) when the ready queue is at `TASK_ARENA_CAPACITY`, with no partial registration left behind.
- [ ] Scheduler hardening: each bridge entry point that takes raw pointers (`register_idle` `:772`, `yield_now` `:1093`, `ipc_send_and_yield` `:1259`, `ipc_recv_and_yield` `:1369`) starts with `debug_assert!(!ptr.is_null())` for `sched` and for `ep_arena` / `queues` / `caller_table` where present; the `start_prelude` panic text (`:872`) is caller-agnostic and keeps the substring `empty ready queue` that the existing `start_prelude_panics_on_empty_ready_queue` test (`:2782`) pins.
- [ ] Comment and nit edits: the `task_a` comment (`bsp-qemu-virt/src/main.rs:671-673`; check `:692-696` too and edit only what is false) describes the post-T-028 interleaving instead of "yields to B"; the redundant `tyrne_hal::` qualifier at `test-hal/src/mmu.rs:569` is dropped (`PAGE_SIZE` is already imported at `:7`).
- [ ] Verification: `cargo host-test` (new tests included), `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal`, `cargo kernel-clippy` and `tools/smoke.sh --int` all pass, the smoke trace unchanged.

## Out of scope

- Correcting the `SchedError::QueueFull` doc (`sched/mod.rs:178-186`) and other stale doc comments: [T-072](T-072-doc-comment-hygiene.md).
- Typed `get_*_mut` wrappers, `#[non_exhaustive]` on `SendOutcome` / `RecvOutcome` and the other kernel Polish items; they stay in `phase-b2.md` as an opportunistic backlog.
- Rebasing the capability table on `Arena`: [T-058](T-058-capability-table-on-arena.md).
- The `BlockMappedMmu` fidelity fix in `test-hal/src/mmu.rs`: [T-041](T-041-blockmappedmmu-already-mapped.md).

## Approach

Everything is local: doc and comment edits, ten small tests in the existing white-box style (the test modules already reach private fields such as `queues.states` and `sched.ready`), one const-assert change, one attribute, and a handful of `debug_assert!`s that follow the precedent already set in `add_user_task` (`sched/mod.rs:462-478`). The reworded `start_prelude` message, for example "scheduler dispatch called with empty ready queue and no idle task", must keep `empty ready queue` for the existing `should_panic` matcher. For the `task_a` comment, the preferred fix is to describe what the FIFO does (the 2026-10-11 reference trace shows `hello from userspace` and `userspace task exited` between `task A -- sending IPC` and `task B -- received IPC`); reordering task registration so `hello` runs last is an alternative the phase item mentions, but it changes every documented trace and is not chosen here unless the maintainer decides otherwise.

## Definition of done

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean (a BSP comment is touched).
- [ ] `cargo host-test` passes with the new tests added.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean.
- [ ] `tools/smoke.sh --int` PASS with an unchanged trace.
- [ ] No new `unsafe`; if an existing block is touched, the audit entry is still accurate ([`unsafe-log.md`](../../../audits/unsafe-log.md)).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md).
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Decisions to record in the review history:** `peek_state` doc vs rename; whether to retire slots at `Generation::MAX` (the per-type arenas have 16 slots, 8 for address spaces, `kernel/src/obj/mod.rs:83-89` and `kernel/src/mm/address_space.rs:41`); how the extra handle for the `QueueFull` test is produced. `sched.ready` has capacity `TASK_ARENA_CAPACITY` (`sched/mod.rs:250`) and the task arena yields at most that many live handles, so the `(N+1)`-th `add_task` needs a forged or reused handle, or a pre-filled `sched.ready`.
- Bridge entry points `start` (`sched/mod.rs:933`) and `task_exit_current` (`:979`) also take `*mut Scheduler` but delegate to `start_prelude`; include them in the assert sweep or leave them, and say which.
- **Location re-verification (2026-10-11).** All cited code lines reproduce on HEAD. One narrowing: at `bsp-qemu-virt/src/main.rs:692-696` the comment describes the receive side ("Task A resumes here after B delivered the reply") and looks accurate; only `:671-673` literally says "yields to B". `phase-b2.md` line numbers are live as of writing (the pre-kickoff snapshot had them two lower); locate by the quoted lead words if they shift again.
- Sequencing: no dependency. [T-041](T-041-blockmappedmmu-already-mapped.md) edits `test-hal/src/mmu.rs` near line 569 and [T-071](T-071-unsafe-contract-hardening.md) edits `add_user_task` in `sched/mod.rs`; rebase, no logical conflict.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
