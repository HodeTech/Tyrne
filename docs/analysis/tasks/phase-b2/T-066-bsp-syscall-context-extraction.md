# T-066 — Extract the BSP syscall-context selection into a host-testable function

- **Phase:** B.2
- **Milestone:** Track B.2-4
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-067](T-067-adversarial-el0-smoke-image.md) (the adversarial image exercises the same trust boundary end to end)
- **ADRs required:** none

---

## User story

As the syscall trust boundary, I want the fail-closed context selection in `syscall_entry` to be a pure, unit-tested function, so that a regression that hands a partially bound task a capability table or user window is caught by `cargo host-test` instead of by review alone.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-4 (the item "The BSP-side syscall trust boundary (fail-closed gate #3 selection logic) has zero automated test coverage…" at line 409) and the Polish item "Make the `has_current_task` <-> empty-table pairing self-checking (a `debug_assert`)…" at line 609 (line 660 repeats the extraction as a Polish item; same fix). `syscall_entry` (`bsp-qemu-virt/src/syscall.rs:143-295`) decides, per syscall, which capability table, user window and address space the dispatcher sees. The decision is the `match` at `:182-193`: only when the running task's table, window and generation-checked address space all resolve does it use them (`has_current_task = true`); any missing piece selects the empty `FAILCLOSED_TABLE`, an empty window, the bootstrap-AS placeholder and `has_current_task = false`. `kernel/src/syscall/dispatch.rs` calls itself the "single most security-sensitive control-flow join in the kernel" (`:6`), and this `match` is the join that feeds it.

The BSP is a bare-metal `no_main` binary with no test target (zero `#[test]` under `bsp-qemu-virt/src`), so nothing exercises the `match`. The dispatcher test `incomplete_binding_context_fails_closed_on_both_planes` (`dispatch.rs:605-664`) builds the fallback context by hand and says so in its comment (`:611-612`): "The BSP match that assembles it is no_std / no_main and not host-testable directly." A bug in the selection itself (for example treating a partial binding as running) would pass every test. An end-to-end check used to exist (a boot-time EL1 `svc` before the scheduler started); no function of that name remains in the tree, only stale comments (`bsp-qemu-virt/src/main.rs:328`, `bsp-qemu-virt/src/syscall.rs:22`).

## Acceptance criteria

- [ ] The branch selection is extracted into a small pure function (the phase item's example: `resolve_syscall_context(current_table, current_window, resolved_as) -> (bool, ...)`), called from `syscall_entry`; its location and return shape are recorded in the review history. Behaviour of `syscall_entry` is unchanged and its `unsafe` blocks keep their SAFETY comments.
- [ ] Tests: host unit tests enumerate all eight present/absent combinations of the three inputs and assert that exactly one (all three present) selects the running task's own table, window and address space with `has_current_task = true`, and the other seven select the fail-closed table, the empty window and `has_current_task = false`.
- [ ] The `has_current_task` <-> empty-table/window pairing is self-checking: either the result type makes an inconsistent pairing unconstructible, or a `debug_assert` guards it where the `SyscallContext` is built or dispatched, with a debug-only `#[should_panic]` test when the assert form is chosen.
- [ ] Smoke pairing: once [T-034](T-034-ci-qemu-smoke-job.md) is merged, the QEMU smoke asserts a trace marker proving a syscall issued with no current task was answered by the fail-closed context end to end; the trigger mechanism is recorded in Design notes. If T-034 has not merged when the rest is done, this criterion is replaced by a follow-up task opened in the same commit.
- [ ] Audit: UNSAFE-2026-0014 and UNSAFE-2026-0029 in [`unsafe-log.md`](../../../audits/unsafe-log.md) still describe the code accurately; if the extraction moves a raw-pointer dereference or changes a justification, an append-only Amendment is added per [`unsafe-policy.md`](../../../standards/unsafe-policy.md), otherwise the review history says why none is needed.
- [ ] Security review recorded per [`security-review.md`](../../../standards/security-review.md) (`Security-Review:` trailer): the change touches the userspace-to-kernel trust boundary.

## Out of scope

- Changing which bindings the scheduler records per task, or the dispatcher's gates: unchanged here.
- Making `NoCurrentTask` a distinct status code: [T-063](T-063-syscall-error-taxonomy-polish.md).
- Reconciling the bootstrap address-space handle assumption: [T-044](T-044-bootstrap-as-handle-invariant.md).
- Adversarial EL0 attack coverage against the real MMU: [T-067](T-067-adversarial-el0-smoke-image.md).

## Approach

Follow the `start_prelude` precedent (`kernel/src/sched/mod.rs:850`, extracted for testability in [T-011](../phase-b/T-011-missing-tests-bundle.md)): move only the selection logic out, keep every raw-pointer dereference and `assume_init_*` call in the BSP, and pass the function already-resolved values (the three `Option`s from `current_user_table()`, `current_user_window()` and the generation-checked address-space lookup, `syscall.rs:169-181`). The BSP keeps supplying the fallback references. The function must hold no hardware or static state so it can be tested on the host.

## Definition of done

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes with the new tests.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean.
- [ ] `tools/build-userland.sh && cargo kernel-build && tools/smoke.sh --int` PASS with an unchanged trace (plus the new marker once T-034 is in).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Security-Review: <reviewer>` and, if an Amendment is added, `Audit: UNSAFE-2026-0014` / `Audit: UNSAFE-2026-0029`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions (record in the review history).** (1) Home of the function: the kernel crate (natural; the BSP cannot run `#[cfg(test)]` under `cargo host-test`) vs a host-compiled module elsewhere. (2) Return shape: a tuple with a `bool` (the phase item's sketch) vs a typed enum that makes the pairing unconstructible. (3) Expressing "table is empty" for a `debug_assert`: `CapabilityTable` has `is_full` but no emptiness accessor (`kernel/src/cap/table.rs:494`), so an assert needs a small new accessor; [T-058](T-058-capability-table-on-arena.md) rebases that file, so coordinate sequencing. (4) Smoke trigger: since no EL1 stub remains, the "syscall with no current task" must come from a new diagnostic (for example an `svc` issued from kernel mode before `start()`), or the assertion is deferred to a follow-up.
- While touching `bsp-qemu-virt/src/syscall.rs`, the module doc at `:17-28` still says the only `SVC` comes from the (removed) EL1 smoke stub; fix opportunistically, it is not a criterion.
- **Location re-verification (2026-10-11).** All cited code lines reproduce on HEAD (`syscall.rs:143-295` is the whole function; the plan item says `143-294`). `phase-b2.md` line numbers are live as of writing (the pre-kickoff snapshot had them two lower); locate by the quoted lead words if they shift again.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
