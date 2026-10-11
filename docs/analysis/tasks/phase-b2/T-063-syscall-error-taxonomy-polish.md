# T-063 — Polish the kernel SyscallError taxonomy

- **Phase:** B.2
- **Milestone:** Track B.2-4
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-064](T-064-tyrne-user-api-polish.md) (its userspace decode API should include the new code)
- **ADRs required:** append-only revision-note rider on [ADR-0030](../../../decisions/0030-syscall-abi.md) (a new stable top-level status code); no new ADR

---

## User story

As the syscall dispatcher, I want the "no current task" control-plane rejection to have its own stable `SyscallError` variant and status code, so that userspace never has to pattern-match a capability-error code (`0x102`) for a condition that involves no capability.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-4 (at the time of writing: the items starting "`SyscallError` has no variant for the 'no current task'…" at line 400 and "Status-code block encoding relies on manual discipline…" at line 403, plus the Polish item "Add a tiny `SyscallError -> &'static str`/`Display` helper…" at line 608). Today `dispatch()` answers `task_yield` / `task_exit` with no current EL0 task by borrowing `SyscallError::from(CapError::InvalidHandle)` (`kernel/src/syscall/dispatch.rs:144-160`), i.e. status `0x102`. The enum (`kernel/src/syscall/error.rs:59-85`) has no variant for this control-plane failure, so the wire-visible code is indistinguishable from a stale or absent capability handle. The branch is defensive-only in v1 (it is not reachable from a real EL0 caller), which makes now the cheap moment to fix it, before any userspace binding branches on `0x102`.

The same file encodes the Cap/Ipc blocks by OR-ing a per-variant literal into `CAP_STATUS_BASE` (`0x100`) / `IPC_STATUS_BASE` (`0x200`) (`error.rs:46-48`, `:122-148`). Nothing fails the build if a literal ever grows past the block width, unlike the `NULL_CAP_HANDLE` precedent (`kernel/src/syscall/abi.rs:41-44`). Status codes are ABI ([ADR-0030](../../../decisions/0030-syscall-abi.md)), so the new code and the guard are recorded as an append-only rider on that ADR.

## Acceptance criteria

- [ ] `SyscallError::NoCurrentTask` exists in `kernel/src/syscall/error.rs` with a doc comment, and `as_status()` returns the next free top-level code (planned `4`; `1`-`3` are taken and the module-level table at `error.rs:17-22` says `1`-`3`, so verify and update that table).
- [ ] `dispatch()` returns it from the `task_yield` and `task_exit` no-current-task arms instead of `Cap(InvalidHandle)`. The data-plane `console_write` fail-closed result (`Cap(InvalidHandle)` from the empty table) is unchanged. Stale wording is fixed: `dispatch.rs:105` (`has_current_task` field doc), `dispatch.rs:548`, `:615-616` (test comments) and `bsp-qemu-virt/src/syscall.rs:238`.
- [ ] A compile-time guard in `error.rs`, in the style of `abi.rs:41-44`, fails the build if **any individual encoded status value** — each top-level code and each value produced by an arm of `cap_error_code` / `ipc_error_code` — does not fit below its block base (`0x100`). It does not rely on a hand-maintained maximum: each arm returns a named per-variant constant and the guard asserts those constants one by one (or iterates a single const array that the arms also use), so a new variant cannot receive a code the guard does not cover. The chosen form is recorded in Design notes.
- [ ] A `SyscallError -> &'static str` helper (and/or `Display`) lives in `error.rs`, matches exhaustively without a wildcard (same ABI-guard property as the encoders), and covers the composed `Cap(..)` / `Ipc(..)` variants.
- [ ] Tests: `top_level_status_codes_are_stable` (`error.rs:172-177`) pins the new code; the `ok_status_is_zero_and_no_error_encodes_to_it` list (`error.rs:156-170`) includes it; `task_yield_with_no_current_task_fails_closed` (`dispatch.rs:546`), `task_exit_with_no_current_task_fails_closed` (`:576`) and the control-plane half of `incomplete_binding_context_fails_closed_on_both_planes` (`:607`) assert `NoCurrentTask` while the data-plane half still asserts `InvalidHandle`; one test asserts every variant's name string is non-empty and distinct.
- [ ] ADR: an append-only `## Revision notes` section on [ADR-0030](../../../decisions/0030-syscall-abi.md) records the new variant, its status code, the rationale (no capability involved, defensive-only branch) and the guard; the ADR body is not edited.

## Out of scope

- The userspace-side decode / classification API in `tyrne-user`; that is [T-064](T-064-tyrne-user-api-polish.md), which should include the new code once this lands.
- Giving `console_write` a bounded length or new error classes (`BadArgument` producers): [T-039](T-039-console-write-bounded-spin-and-length-cap.md).
- Wiring any real EL0 path to the new variant; the branch stays unreachable from EL0 in v1.

## Approach

Add the variant and its `as_status` arm, point the two dispatcher arms at it, and update the three host tests and four comments named above. Add the compile-time guard next to the encoders and the name helper next to the enum so the userspace-facing string table has one source of truth (the Polish item's intent: `tyrne-user` must not re-derive a parallel table). Because `SyscallError` is `#[non_exhaustive]` and the encoders match exhaustively inside the crate, forgetting an arm is a compile error, which keeps the ABI change mechanical. Append the ADR-0030 revision note in the same PR as the code.

## Definition of done

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean (a BSP comment is touched).
- [ ] `cargo host-test` passes with the updated and new tests.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean.
- [ ] `tools/smoke.sh --int` PASS (trace unchanged; the branch is not reached at runtime).
- [ ] The PR description declares security relevance per [`security-review.md`](../../../standards/security-review.md) (syscall dispatcher change).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0030`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions (small).** (1) Form of the compile-time guard: named per-variant constants shared by the encoder arms and the assertions (asserted one by one), or one const array used by both; a guard that asserts only on the highest-numbered variant or on a hand-kept maximum is not accepted. (2) Whether the helper is `fn name(self) -> &'static str`, a `core::fmt::Display` impl, or both; [`error-handling.md`](../../../standards/error-handling.md) says to write a short `Display` only where needed. Record both choices in the review history.
- `SchedError::NoCurrentTask` (`kernel/src/sched/mod.rs:175`) already names the same condition inside the scheduler; reusing the name keeps the two spaces readable side by side. The two types are unrelated at the type level.
- **Location re-verification (2026-10-11).** All cited code lines reproduce on HEAD. `phase-b2.md` line numbers are live as of writing (the two Track B.2-4 items were at 398 and 401 in the pre-kickoff snapshot); locate by the quoted lead words if they shift again.
- Sequencing: no code dependency. Landing before [T-064](T-064-tyrne-user-api-polish.md) lets that task decode `4` from day one; if it lands first, T-064 adds the arm in a follow-up edit.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
