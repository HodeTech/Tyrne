# T-032 — Deny panic-family lints in tyrne-hal and tyrne-bsp-qemu-virt

- **Phase:** B.2
- **Milestone:** Track B.2-1
- **Status:** In Review
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-052](T-052-standards-docs-reality-sync.md)
- **ADRs required:** none

---

## User story

As the maintainer enforcing the error-handling standard, I want `clippy::panic`, `clippy::unwrap_used` and `clippy::expect_used` denied in `tyrne-hal` and `tyrne-bsp-qemu-virt` as they already are in `tyrne-kernel`, so that the standard's "Clippy enforces this" claim is true for every in-scope crate and a stray `unwrap()` on the syscall or exception path fails CI.

## Context

The following describes the opening baseline; implementation and verification are recorded in Review history.

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). `kernel/src/lib.rs:62-66` carries the deny attributes; `hal/src/lib.rs` (only `#![no_std]`, line 33) and `bsp-qemu-virt/src/main.rs:22-40` (no deny attribute) do not. `docs/standards/error-handling.md:55-60` says `unwrap()`/`expect()` are forbidden "in the kernel and in the HAL" and that clippy enforces it in kernel crates, and `docs/standards/code-style.md:129` lists the three lints as "deny in kernel paths". Post-Phase-B6 the BSP's `syscall.rs` and `exceptions.rs` are live hostile-input surfaces (EL0 traps), so the gap is no longer cosmetic.

This task covers the MEDIUM item of `phase-b2.md` Track B.2-1 "`clippy::unwrap_used`/`expect_used`/`panic` are denied only in `tyrne-kernel`" (line 45 as of the opening snapshot; locate by headline). The plan prefers adding the denies over narrowing the standard's wording.

## Acceptance criteria

- [x] `hal/src/lib.rs` carries `#![deny(clippy::panic)]`, `#![deny(clippy::unwrap_used)]` and `#![deny(clippy::expect_used)]` in the same form as `kernel/src/lib.rs:62-64`, with a short comment of why; `cargo host-clippy` is clean.
- [x] `bsp-qemu-virt/src/main.rs` carries the same three attributes; `cargo kernel-clippy` is clean.
- [x] The `perf-bench` variant is also clean: `cargo clippy --target aarch64-unknown-none -p tyrne-bsp-qemu-virt --features perf-bench -- -D warnings` (its `perf_bench.rs` is never compiled by default clippy and holds about 18 expect/panic sites).
- [x] Every new `#[allow(clippy::panic | clippy::unwrap_used | clippy::expect_used)]` is scoped to a function or item (no crate-level or module-level allow) and has `reason = "..."`; `bsp-qemu-virt/src/syscall.rs` has none, and `exceptions.rs` has only function-scoped ones on its two deliberate fatal-fault `panic!` sites. Inspect every attached function, including multiline attributes (a single-line grep does not enumerate them).
- [x] Each allowed site group is classified in the review history (one-shot init, demo-task body, deliberate fatal abort, or provably infallible) and the non-init `bsp-qemu-virt/src/mmu.rs:317` `.unwrap()` is resolved by restructuring or by an allow whose reason states why it cannot fail.
- [x] Tests: a probe calling `.unwrap()` on a `None` in non-test code of isolated copies of `tyrne-hal` and the BSP makes the exact `cargo host-clippy` / `cargo kernel-clippy` commands fail with the intended lint. Record local and hosted results separately; remove the disposable copies on exit, with no regression branch or commit.

## Out of scope

- Rewording `error-handling.md` / `code-style.md`: [T-052](T-052-standards-docs-reality-sync.md) owns the "uniform coverage" claim and decides its final wording once this lands.
- `tyrne-test-hal` (host-test fakes legitimately panic; see the comment at `kernel/src/lib.rs:51-61`).
- Turning init-path `expect`s into `Result` propagation, and the other kernel-only denies (`arithmetic_side_effects`, `float_arithmetic`).
- A lint forbidding `#[allow]` without a reason.

## Approach

Add the three attributes to both crate roots, copying the kernel's form and explaining the rationale in a comment like the kernel's. Run `cargo host-clippy` and `cargo kernel-clippy` (and the `perf-bench` command above) and handle each hit by the cheapest honest option: scoped `#[allow(..., reason = "...")]` on legitimate one-shot init-path call sites, mirroring the kernel's `#[cfg(test)]` allow pattern (`kernel/src/syscall/dispatch.rs:335-343`), or a small restructuring where the failure cannot happen. Single-line greps of `panic!(`, `.unwrap()` and `.expect(` found: `hal/src` none; BSP `main.rs` 28 (in `idle_entry`, `task_b`, `task_a` and `kernel_main_high`), `exceptions.rs` 2 (`irq_entry`, `panic_entry`, both deliberate aborts per error-handling.md section 5), `mmu.rs` 1, `perf_bench.rs` 18, `syscall.rs` 0. Clippy, not this count, is the authority.

## Definition of done

Beyond the acceptance criteria:

- [x] `cargo fmt --all -- --check` clean.
- [x] `cargo host-clippy` clean with `-D warnings`.
- [x] `cargo kernel-clippy` clean.
- [x] `cargo host-test` passes.
- [x] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean (hal source changes).
- [x] `tools/smoke.sh --int` PASS (BSP source changes).
- [x] If the `mmu.rs:317` fix moves code inside the `unsafe` expression, the audit entry cited there (UNSAFE-2026-0025) is re-checked and amended if its text no longer matches.
- [x] Changes touching boot, MMU, exception handling or an `unsafe` region receive a distinct security-review pass, explicit approval of any changed unsafe reasoning, and a recorded artifact plus `Security-Review:` trailer. Routine code-review rounds do not substitute for that pass.
- [x] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with a `Refs: ADR-0040` trailer.
- [x] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

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
| 2026-10-12 | Codex (AI agent) | Started approved step 5 after T-030 implementation gates and both fresh code/security rounds (`8591ceb`). Isolated real-Clippy baseline: host 0 hits; default BSP 31 hits; perf BSP 26 hits (counts overlap by variant). Plan: three crate-root denies in HAL/BSP, ten function-scoped reasoned exception groups, remove unused MMU dummy-frame unwrap by passing the existing typed root, append UNSAFE-2026-0025 amendment, and add isolated local/hosted `None`-unwrap probes using exact host/kernel clippy aliases. Verify host/default/release/perf lint, host tests, Miri and real debug smoke; then two fresh code/security rounds with explicit changed unsafe-reasoning approval. No new architecture or policy decision. |
| 2026-10-12 | Codex (AI agent) | Exception inventory: `main::kernel_main_high` and `perf_bench::run` are one-shot trusted setup (expect + panic); `main::idle_entry` is a trusted scheduler invariant (expect); `main::task_a` / `task_b` are trusted one-round demo bodies (expect + panic); `perf_bench::driver_yield` / `driver_send` / `partner_recv` are trusted benchmark task protocol/invariant helpers (expect); `exceptions::irq_entry` / `panic_entry` retain deliberate fatal abort policy (panic only). No HAL, syscall, MMU, crate-wide or module-wide panic-family allow is added. Assertions are outside these three Clippy lints; no panic-free claim is made. Gates and distinct reviews pending. |
| 2026-10-12 | Codex (AI agent) | Local implementation gates pass: fmt, ShellCheck 0.11.0/actionlint, host/default/release/perf clippy and debug/release/perf builds; 366 host tests and 366 Miri tests, no UB failure (existing warnings retained; two HAL doctests ignored). Default real QEMU smoke (`--int --timeout 5`) shows greeting, userspace exit, completion, two expected SVCs and no fault class; debug hello remains 117 bytes/SHA `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`. Actual private `--hal` / `--bsp` probes reject `None.unwrap()` at exit 101 with `clippy::unwrap_used`; BSP image is built only in its copy. Eleven controlled probe/CLI cases verify expected rejection, unexpected-green/unrelated-failure refusal, exact aliases, private target/image, unchanged originals and cleanup under Bash 3.2/spaced paths; 59 QEMU argument cases pass. The first controlled fixture had an escaped-NUL construction error in its git stub; corrected fixture passes and no failed check was accepted as evidence. Existing audit entry/amendments are byte-preserved with only the new 0025 amendment appended. Hosted evidence and both fresh code/security rounds pending; status In Review. Ephemeral logs `/tmp/tyrne-b21-step5/`. |
| 2026-10-12 | Codex (AI agent) | Implementation committed as `c3f32c8`; 0025 amendment now records that actual SHA. Negative-probe criterion remains unchecked until hosted results exist, although local results already pass; distinct security criterion remains unchecked until its real approval is recorded. Final PR and both fresh review rounds are pending. |
| 2026-10-12 | Codex (AI agent) | First [hosted run at `b6572cc`](https://github.com/HodeTech/Tyrne/actions/runs/38181326486) passed all five jobs. Downloaded fast-lane log records HAL rejection at exit 101 with `clippy::unwrap_used`; kernel log records the private 117-byte BSP image build and the same intended BSP rejection. Production debug/release/perf build/lint steps remain green with the 117 → 69 → restored 117-byte image sequence; hosted host tests report 366 debug / 356 release passes and two ignored HAL doctests. Expected-failure probes passed because the intended regression was rejected, not because a production job failed. Both fresh code/security rounds and explicit 0025 reasoning approval remain pending; status In Review. Ephemeral hosted metadata/logs in `/tmp/tyrne-b21-step5/`. |
| 2026-10-12 | Independent review agents / Codex reconciliation | Round 1 [code](../../reviews/code-reviews/2026-10-12-t032-panic-family-denies.md) and distinct [security](../../reviews/security-reviews/2026-10-12-t032-panic-family-denies.md) Approve at `4f2c38c`, no actionable finding or source fix. Both explicitly approve changed 0025 unmap reasoning; actual approval is appended to the audit entry and recorded by this follow-up trailer. Independent real unwrap/expect/panic rejection, unwrap-deny removal controls, isolation/cleanup and historical audit-byte checks pass. Report wording preserves unchanged non-SVC policy without assigning future work to a phase. Runtime BSP unmap/SMP and existing HIGH T-038 remain excluded. Second fresh round and final maintainer PR review pending; In Review. |
| 2026-10-12 | Independent fresh review agents / Codex reconciliation | Round 2 [code](../../reviews/code-reviews/2026-10-12-t032-panic-family-denies.md#round-2-code-review) and distinct [security](../../reviews/security-reviews/2026-10-12-t032-panic-family-denies.md#round-2-security-review) Approve at `6e191e2`, no actionable finding or source fix. Both explicitly approve changed 0025 reasoning and verify actual Round 1 recording. Fresh real compiler mutations establish sibling-module and same-lint callee enforcement; removal of only the two T-032 additions restores baseline audit bytes exactly. All five jobs at exact reviewed head pass in [run 38181945962](https://github.com/HodeTech/Tyrne/actions/runs/38181945962). Both fresh rounds complete; final maintainer PR pending, status In Review. Proceed to approved step 6 (T-034). |
