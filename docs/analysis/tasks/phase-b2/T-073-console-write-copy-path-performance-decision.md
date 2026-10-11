# T-073 — Decide the console_write copy-path performance items

- **Phase:** B.2
- **Milestone:** Track B.2-6
- **Status:** Draft
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-039](T-039-console-write-bounded-spin-and-length-cap.md)
- **Informs:** none
- **ADRs required:** none

---

## User story

As the maintainer, I want the two known redundant page-table walks in the user-copy path either removed with evidence or explicitly deferred with a measurement and a trigger, so that a deliberate safety-over-performance tradeoff is a recorded decision rather than a forgotten finding.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). Track B.2-6 of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) holds two low-severity items that the source review itself calls deliberate: (1) `console_write` probes the whole user range with `probe_user_pages` and then, per chunk, `copy_from_user` probes and re-validates again (`kernel/src/syscall/dispatch.rs`, probe at lines 252-262 and the chunk loop to line 300), so every page is translated more than once; (2) `copy_from_user` and `copy_to_user` walk the page table twice per page — once in `probe_user_pages` (`kernel/src/syscall/user_access.rs` lines 140-170) and again in pass 2 (`:199` onward, translate at about `:213`). The phase's own acceptance rule is: "either fixed, or explicitly deferred with a one-line profiling note, once Track B.2-3's `console_write` length cap lands" — hence the dependency on [T-039](T-039-console-write-bounded-spin-and-length-cap.md), which bounds the worst-case iteration count. The only caller today is the debug-only `console_write`, so there is no production cost.

## Acceptance criteria

- [ ] A measurement is recorded before any change: cost of `console_write` and of the user-copy path at several lengths (a single byte, one page, and the cap from T-039), taken with the existing perf tooling (`tools/perf-harness.sh`, the `perf-bench` feature, the T-029 pattern) and the same-host control required by the [performance master plan](../../reviews/performance-optimization-reviews/master-plan.md); extend the micro-bench only if the existing ones cannot isolate the path.
- [ ] **Decision recorded** for each of the two items — implement now or defer — in this task's review history, with the measurement as evidence.
- [ ] If item 1 is implemented: the chunk loop skips the chunk-level re-probe while keeping the chunk-level re-validation; the all-or-nothing guarantee is preserved and pinned by a test (a fault on a later page emits nothing); existing `console_write` tests are unchanged and pass.
- [ ] If item 2 is implemented: `probe_user_pages` caches the resolved `PhysFrame` per page in a small fixed-size buffer so the copy pass consumes it instead of re-translating, keeping the cheap `USER`-bit re-check; the copy-path unit tests pass unchanged; Miri is clean; the UNSAFE-2026-0030 audit entry gets an Amendment if either `unsafe` site moves.
- [ ] If an item is deferred: a one-line note with the measurement and the trigger ("before the first production syscall that carries a real, non-console buffer") is added where the next implementer will see it — the module documentation of `user_access.rs` and this task's review history — and the item is listed as a carry-forward for the closure ([T-075](T-075-phase-b2-closure.md)).
- [ ] Whatever is chosen, a before/after (or deferral) summary of the measurement is in the review history; no security property changes (`probe` still runs before any byte moves; DEVICE and non-`USER` pages still fault).

## Out of scope

- The unbounded per-byte spin and the length cap — [T-039](T-039-console-write-bounded-spin-and-length-cap.md).
- Hardening the copy path (DEVICE exclusion, zero-length probe) — [T-043](T-043-user-access-hardening.md); de-duplicating the two copy loops — [T-060](T-060-user-access-walk-helper-dedup.md).
- Optimising anything outside the user-copy and `console_write` path.

## Approach

Profile first; the review's own recommendation is "profile first". If the measured cost on the debug-only path is negligible, record the deferral and stop — that is a complete outcome for this task. If an item is implemented, change one thing at a time and re-measure. Sequence relative to [T-060](T-060-user-access-walk-helper-dedup.md): if the two copy loops have already been merged into one walk helper, implement the cache there once.

## Definition of done

- [ ] `cargo fmt --all -- --check`, `cargo host-clippy`, `cargo kernel-clippy` clean (if code changes).
- [ ] `cargo host-test` passes; `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean if code changes.
- [ ] `tools/smoke.sh --int` PASS if code changes.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Location re-verification (2026-10-11, HEAD `400dec0`):** the `console_write` probe and chunk loop in `dispatch.rs` (lines 252-300) and the probe and pass-2 translate in `user_access.rs` (lines 140-218) match the tree. `probe_user_pages` is also the function [T-043](T-043-user-access-hardening.md) hardens (its zero-length case), so land T-043 first or rebase carefully.
- **Open decisions:** implement vs defer, per item.
- Status is `Draft` because the outcome depends on the measurement.
- This is the only task whose "done" may legitimately contain no code change.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Draft |
