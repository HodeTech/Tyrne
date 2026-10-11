# T-059 — Introduce a single typed capability-resolution primitive

- **Phase:** B.2
- **Milestone:** Track B.2-4
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-058](T-058-capability-table-on-arena.md)
- **Informs:** none
- **ADRs required:** none

---

## User story

As the IPC, address-space, syscall and scheduler layers, we want one `CapabilityTable::resolve_typed` that performs "resolve, check kind, check rights" once, so that the ADR-0030 error ordering is pinned in a single place instead of being re-derived at five call sites.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from the item at [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) line 374 (Track B.2-4). The pattern is hand-rolled in five functions:

| Function | Location | Error type returned | Rights check |
|----------|----------|---------------------|--------------|
| `validate_ep_cap` | `kernel/src/ipc/mod.rs:589` | `IpcError` | caller-supplied (`SEND`/`RECV`) |
| `validate_notif_cap` | `kernel/src/ipc/mod.rs:604` | `IpcError` | `NOTIFY` |
| `resolve_address_space_cap` | `kernel/src/mm/address_space.rs:430` | `AddressSpaceError::CapError` | none (v1 rights model, documented at `:408-429`) |
| `validate_debug_console_cap` | `kernel/src/syscall/dispatch.rs:321` | `CapError` | `CONSOLE_WRITE` |
| `Scheduler::resolve_ep_cap` | `kernel/src/sched/mod.rs:555` | `SchedError::Ipc` | none (done inside `ipc_send`/`ipc_recv`) |

[ADR-0030](../../../decisions/0030-syscall-abi.md) (line 91) fixes the order `StaleHandle`, then `WrongObjectKind`, then `MissingRight`, i.e. in `CapError` terms `InvalidHandle`, `WrongKind`, `InsufficientRights`. Five copies mean a future fix to the order can land in one and not the others. This is a security-sensitive refactor of the authority check (capabilities are a trigger in [`security-review.md`](../../../standards/security-review.md)): **the exact error-ordering semantics must be preserved**, and the order must be pinned by a test at every call site.

## Acceptance criteria

- [ ] `CapabilityTable` gains a crate-internal `fn resolve_typed<T>(&self, handle: CapHandle, extract: impl FnOnce(CapObject) -> Option<T>, required: CapRights) -> Result<T, CapError>` that does lookup, then extract-or-`WrongKind`, then rights-check-or-`InsufficientRights`, in that order; its doc comment cites ADR-0030 line 91. Unit tests in `kernel/src/cap/table.rs` pin each failure, success, the case "wrong kind and missing right returns `WrongKind`", and that `required = CapRights::empty()` demands nothing.
- [ ] All five functions above delegate to it with a thin mapping to their own error type (`InvalidHandle` to `StaleHandle`, `WrongKind` to `WrongObjectKind`, `InsufficientRights` to `MissingRight` where applicable); none of the five bodies calls `lookup` directly any more, and their return types and public behaviour are unchanged.
- [ ] The order is pinned at every site. Existing and unchanged: the wrong-kind-and-lacking-the-right tests for `ipc_send`/`ipc_recv`/`ipc_notify`/`ipc_cancel_recv` (`ipc/mod.rs:970,995,1011,1609`). To add: a `console_write` test with a wrong-kind capability that also lacks `CONSOLE_WRITE` (the current wrong-kind test at `dispatch.rs:1030` uses a capability that carries the right bit, so it cannot tell kind-first from rights-first); `Scheduler::resolve_ep_cap` stale and wrong-kind cases asserting `SchedError::Ipc(StaleHandle)` and `SchedError::Ipc(WrongObjectKind)` (`sched/mod.rs` has no such assertion today); an address-space capability with empty rights still resolves (the success test at `address_space.rs:993` uses a capability with non-empty rights), pinning the v1 rights model.
- [ ] The arena-liveness `StaleHandle` that ADR-0030 (line 93) places after the rights check in the IPC operation bodies is untouched, and the existing test `send_with_dropped_cap_handle_returns_stale_handle` (`ipc/mod.rs:1026`) and its siblings still pass unchanged.
- [ ] Tests and gates: `cargo host-test` (366 tests at HEAD) passes with no edited assertion; `cargo test --release` passes (`dispatch.rs` is touched and the two release-only tests must stay green); `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean; `tools/smoke.sh --int` PASS.
- [ ] Security review recorded in the review history and the `Security-Review:` trailer, working the Capability-correctness checklist in [`security-review.md`](../../../standards/security-review.md).
- [ ] Documentation: the comment above `validate_ep_cap` (`ipc/mod.rs:585-588`) and the `dispatch.rs` doc at `:306-320` point at the primitive instead of restating the order; the `table.rs` module doc names the primitive as the one place the ordering lives.

## Out of scope

- The storage rebase: [T-058](T-058-capability-table-on-arena.md) (a dependency; this task builds on it).
- Two other inline kind checks that are not among the item's five: `cap_create_address_space` (`address_space.rs:547-553`) and the `load_image` preflight (`obj/task_loader.rs:535-543`). Whether they call `resolve_address_space_cap` or just get their docs fixed is [T-072](T-072-doc-comment-hygiene.md) (phase-b2.md line 523).
- Adding a rights model to address-space capabilities (deferred in the `resolve_address_space_cap` doc to a later ADR).
- Any change to the syscall error taxonomy: [T-063](T-063-syscall-error-taxonomy-polish.md).

## Approach

Factor `resolve_typed` onto `CapabilityTable` exactly as the item sketches. Each call site passes an `extract` closure (`|o| match o { CapObject::Endpoint(h) => Some(h), _ => None }` and similar; for the debug console, a closure returning `Some(())` for `CapObject::DebugConsole`) and its required rights, then maps the `CapError` into its own error type. Write the primitive's tests first, then migrate one site per commit so each commit keeps the full suite green.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes with the new tests added.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean.
- [ ] `tools/smoke.sh --int` PASS (kernel code changed).
- [ ] No new `unsafe`, so no new audit entry.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040` and a `Security-Review: <reviewer>` trailer.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Why the error types stay per-site.** The five sites return four different error types, so the primitive returns the common `CapError` and each site keeps a one-line mapping; making the primitive generic over the error type would hide the ordering behind trait plumbing.
- **Sequencing.** After [T-058](T-058-capability-table-on-arena.md) (same file, `cap/table.rs`). `dispatch.rs` is also touched by [T-039](T-039-console-write-bounded-spin-and-length-cap.md) and [T-063](T-063-syscall-error-taxonomy-polish.md), and `ipc/mod.rs` by [T-068](T-068-kernel-tests-and-nits-bundle.md); no order is imposed, whichever lands second rebases.
- **Re-verification (2026-10-11).** The five function locations above were confirmed with `grep -n 'fn validate_ep_cap\|fn validate_notif_cap\|fn resolve_address_space_cap\|fn validate_debug_console_cap\|fn resolve_ep_cap'`; the item's ranges (`ipc/mod.rs:589-602,604-616`, `address_space.rs:430-441`, `dispatch.rs:321-333`, `sched/mod.rs:555-570`) still bound those functions, no drift. The `phase-b2.md` lines are from the live file (was 372 and 521 in the pre-kickoff snapshot).

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
