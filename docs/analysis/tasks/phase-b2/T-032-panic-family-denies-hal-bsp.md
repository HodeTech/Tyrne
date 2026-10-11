# T-032 — Deny panic-family lints in tyrne-hal and tyrne-bsp-qemu-virt

- **Phase:** B.2
- **Milestone:** Track B.2-1
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-052](T-052-standards-docs-reality-sync.md)
- **ADRs required:** none

---

## User story

As the maintainer enforcing the error-handling standard, I want `clippy::panic`, `clippy::unwrap_used` and `clippy::expect_used` denied in `tyrne-hal` and `tyrne-bsp-qemu-virt` as they already are in `tyrne-kernel`, so that the standard's "Clippy enforces this" claim is true for every in-scope crate and a stray `unwrap()` on the syscall or exception path fails CI.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). `kernel/src/lib.rs:62-66` carries the deny attributes; `hal/src/lib.rs` (only `#![no_std]`, line 33) and `bsp-qemu-virt/src/main.rs:22-40` (no deny attribute) do not. `docs/standards/error-handling.md:55-60` says `unwrap()`/`expect()` are forbidden "in the kernel and in the HAL" and that clippy enforces it in kernel crates, and `docs/standards/code-style.md:129` lists the three lints as "deny in kernel paths". Post-Phase-B6 the BSP's `syscall.rs` and `exceptions.rs` are live hostile-input surfaces (EL0 traps), so the gap is no longer cosmetic.

This task covers the MEDIUM item of `phase-b2.md` Track B.2-1 "`clippy::unwrap_used`/`expect_used`/`panic` are denied only in `tyrne-kernel`" (line 45 as of the opening snapshot; locate by headline). The plan prefers adding the denies over narrowing the standard's wording.

## Acceptance criteria

- [ ] `hal/src/lib.rs` carries `#![deny(clippy::panic)]`, `#![deny(clippy::unwrap_used)]` and `#![deny(clippy::expect_used)]` in the same form as `kernel/src/lib.rs:62-64`, with a short comment of why; `cargo host-clippy` is clean.
- [ ] `bsp-qemu-virt/src/main.rs` carries the same three attributes; `cargo kernel-clippy` is clean.
- [ ] The `perf-bench` variant is also clean: `cargo clippy --target aarch64-unknown-none -p tyrne-bsp-qemu-virt --features perf-bench -- -D warnings` (its `perf_bench.rs` is never compiled by default clippy and holds about 18 expect/panic sites).
- [ ] Every new `#[allow(clippy::panic | clippy::unwrap_used | clippy::expect_used)]` is scoped to a function or item (no crate-level or module-level allow) and has `reason = "..."`; `bsp-qemu-virt/src/syscall.rs` has none, and `exceptions.rs` has only function-scoped ones on its two deliberate fatal-fault `panic!` sites. Checked by `grep -n "allow(clippy::\(panic\|unwrap_used\|expect_used\)" bsp-qemu-virt/src/*.rs`.
- [ ] Each allowed site group is classified in the review history (one-shot init, demo-task body, deliberate fatal abort, or provably infallible) and the non-init `bsp-qemu-virt/src/mmu.rs:317` `.unwrap()` is resolved by restructuring or by an allow whose reason states why it cannot fail.
- [ ] Tests: a probe that calls `.unwrap()` on a `None` placed temporarily in non-test code of `tyrne-hal` and of the BSP makes `cargo host-clippy` / `cargo kernel-clippy` fail (recorded in the review history, probe reverted).

## Out of scope

- Rewording `error-handling.md` / `code-style.md`: [T-052](T-052-standards-docs-reality-sync.md) owns the "uniform coverage" claim and decides its final wording once this lands.
- `tyrne-test-hal` (host-test fakes legitimately panic; see the comment at `kernel/src/lib.rs:51-61`).
- Turning init-path `expect`s into `Result` propagation, and the other kernel-only denies (`arithmetic_side_effects`, `float_arithmetic`).
- A lint forbidding `#[allow]` without a reason.

## Approach

Add the three attributes to both crate roots, copying the kernel's form and explaining the rationale in a comment like the kernel's. Run `cargo host-clippy` and `cargo kernel-clippy` (and the `perf-bench` command above) and handle each hit by the cheapest honest option: scoped `#[allow(..., reason = "...")]` on legitimate one-shot init-path call sites, mirroring the kernel's `#[cfg(test)]` allow pattern (`kernel/src/syscall/dispatch.rs:335-343`), or a small restructuring where the failure cannot happen. Single-line greps of `panic!(`, `.unwrap()` and `.expect(` found: `hal/src` none; BSP `main.rs` 28 (in `idle_entry`, `task_b`, `task_a` and `kernel_main_high`), `exceptions.rs` 2 (`irq_entry`, `panic_entry`, both deliberate aborts per error-handling.md section 5), `mmu.rs` 1, `perf_bench.rs` 18, `syscall.rs` 0. Clippy, not this count, is the authority.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean (hal source changes).
- [ ] `tools/smoke.sh --int` PASS (BSP source changes).
- [ ] If the `mmu.rs:317` fix moves code inside the `unsafe` expression, the audit entry cited there (UNSAFE-2026-0025) is re-checked and amended if its text no longer matches.
- [ ] Changes touching boot, MMU, exception handling or an `unsafe` region receive a distinct security-review pass, explicit approval of any changed unsafe reasoning, and a recorded artifact plus `Security-Review:` trailer. Routine code-review rounds do not substitute for that pass.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with a `Refs: ADR-0040` trailer.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Location re-verification (2026-10-11, HEAD `400dec0`):** `kernel/src/lib.rs:62-66`, `hal/src/lib.rs` (no deny; `#![no_std]` at :33), `bsp-qemu-virt/src/main.rs:22-40`, `error-handling.md:55,60` and `code-style.md:129` were re-checked and match the plan item; nothing drifted. `phase-b2.md` line numbers shift as banners are added, so locate its items by headline.
- Sequencing hazard: [T-030](T-030-ci-release-profile-gate.md) adds a CI clippy pass over the `perf-bench` variant. Whichever of the two lands second must make that variant clean too, which is why the third criterion lives here.
- `syscall.rs` and `exceptions.rs` are hostile-input surfaces: a scoped allow there needs a stronger reason than "init path", and `syscall.rs` currently needs none.
- `hal` currently has no `panic!`/`unwrap`/`expect` call at all (its `assert!`s are not flagged by `clippy::panic`), so its deny is expected to land with no allows; this is a regression guard.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-11 | Codex (AI agent) | Preflight contract review: see [review artifact](../../reviews/code-reviews/2026-10-11-phase-b2-track1-preflight.md); documentation corrected, implementation not started; ADR-0040 remains Proposed. |
