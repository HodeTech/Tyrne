# T-030 — Gate the release profile in CI (build, test, release-only regression tests)

- **Phase:** B.2
- **Milestone:** Track B.2-1
- **Status:** In Review
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-034](T-034-ci-qemu-smoke-job.md), [T-065](T-065-debug-console-feature-flag.md)
- **ADRs required:** none

---

## User story

As the maintainer relying on the `console_write` debug-gate to keep the debug console off the production syscall surface, I want CI to build and test the `--release` profile on every PR, so that a broken gate is caught by a red check instead of by a human who happens to run a release build.

## Context

The following describes the opening baseline; implementation and verification are recorded in Review history.

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). `SyscallNumber::decode` hides syscall number 5 (`console_write`) behind `cfg!(debug_assertions)` (`kernel/src/syscall/abi.rs:87`), and two tests pin that behaviour only in a non-debug build: `console_write_is_absent_in_release_builds` (`abi.rs:377-383`) and `console_write_number_is_bad_syscall_in_release_build` (`kernel/src/syscall/dispatch.rs:1255-1257`). Both are `#[cfg(not(debug_assertions))]`, and every CI job (`.github/workflows/ci.yml:96-101,140-143,188-189,224`) builds and tests the debug profile only, so neither has ever run in CI and the release kernel (fat LTO, `Cargo.toml:65-70`) is never built there. Both tests pass locally under `cargo test --release` (2026-10-11).

This task covers four items of `phase-b2.md` Track B.2-1 (line numbers as of the opening snapshot; locate by headline): the HIGH "release-profile contract ... never built or tested by CI" (line 27), the HIGH "release debug-gate's regression test never executes in CI" (line 36), the MEDIUM "CI never builds, lints, or smoke-tests the `--release` profile" (line 42), and the LOW "`perf-bench` feature ... never compiled by CI" (line 48; `bsp-qemu-virt/Cargo.toml:19-24`, 542-line `perf_bench.rs`).

## Acceptance criteria

- [x] `.cargo/config.toml` gains `kernel-build-release` and `kernel-run-release` aliases beside `kernel-build`/`kernel-run` (same flags plus `--release`); `tools/build-userland.sh --release && cargo kernel-build-release` succeeds locally and writes `target/aarch64-unknown-none/release/tyrne-bsp-qemu-virt`.
- [ ] CI builds the release kernel on every PR (step order: `tools/build-userland.sh --release`, then `cargo kernel-build-release`, appended after the existing debug steps in `kernel-build`).
- [ ] CI runs `cargo test --release` over the host crates (workspace `default-members`) on every PR; the first green run's totals and wall time are recorded in the review history (local baseline: 249 kernel + 46 hal + 58 test-hal + 3 doc).
- [ ] A separate narrow CI step runs `cargo test --release -p tyrne-kernel --lib -- console_write_is_absent_in_release_builds console_write_number_is_bad_syscall_in_release_build` and fails unless both tests ran (for example by asserting `2 passed` in the libtest output), so a regression names the gate.
- [ ] Negative test, recorded in the review history: in an isolated temporary copy, adding `debug-assertions = true` under `[profile.release]` makes the exact two-test gate command fail. Repeat the probe in an isolated hosted runner workspace; its harness must assert the expected non-zero result. Do not create another branch or commit the probe. Record local and hosted results separately; an expected-failure harness passing is not a red production workflow.
- [x] Root `Cargo.toml` carries a comment next to `[profile.release]` stating that `debug-assertions` must stay at Cargo's release default (false) because `SyscallNumber::decode` gates `console_write` on it (`abi.rs:87`); `grep -n "debug-assertions" Cargo.toml` finds it and no `debug-assertions = true` key exists.
- [ ] CI builds and lints the debug `perf-bench` variant in `kernel-build`: restore its matching image with `tools/build-userland.sh` immediately before `cargo build --target aarch64-unknown-none -p tyrne-bsp-qemu-virt --features perf-bench` and `cargo clippy --target aarch64-unknown-none -p tyrne-bsp-qemu-virt --features perf-bench -- -D warnings`, both green (any finding surfaced by never-linted code is fixed or given a scoped `#[allow]` with a reason).
- [ ] CI also runs release kernel clippy (`cargo clippy --release --target aarch64-unknown-none -p tyrne-bsp-qemu-virt -- -D warnings`), after the release userland build.
- [ ] Documentation: `docs/guides/ci.md` job table and local-command table, `docs/standards/infrastructure.md` "Required gates", and the `ci.yml` header comment (lines 7-9) describe the new steps; release-profile EL0 QEMU smoke is owned by T-034 and is not claimed enforced until that job passes remotely.

## Out of scope

- Running the release ELF under QEMU (`tools/smoke.sh --release --int`): [T-034](T-034-ci-qemu-smoke-job.md) implements and verifies this alongside its debug smoke.
- Replacing the `debug_assertions` mechanism with a dedicated Cargo feature: [T-065](T-065-debug-console-feature-flag.md).
- Any change to the gate logic in `abi.rs` or `dispatch.rs`.

## Approach

Mirror the existing debug entry points: add the two release aliases to `.cargo/config.toml`, then extend CI. Prefer extra steps in the existing required jobs (`kernel-build` for the release build and the `perf-bench` build/clippy; `lint-and-host-test` or `kernel-build` for `cargo test --release`) so no new required-check name is needed; if wall time forces a dedicated job, its display name must be added to branch protection (manual, outside the repo) and to the three docs. Run the debug steps first and the `perf-bench` steps last. Since `build-userland.sh --release` overwrites the shared `userland/hello/hello.bin`, restore the debug image immediately before the non-release perf build/lint. The BSP `build.rs` checks image existence and watches changes, but does not validate the embedded image's profile. Keep the narrow two-test step even though the full `cargo test --release` also executes the tests; its job is to name the gate and to detect the vanishing-test case described below. Spell the `perf-bench` clippy command out in full; do not append `--features` to the `kernel-clippy` alias, because the alias already ends in `-- -D warnings` and trailing cargo arguments would land after it.

## Definition of done

Beyond the acceptance criteria:

- [x] `cargo fmt --all -- --check` clean.
- [x] `cargo host-clippy` clean with `-D warnings`.
- [x] `cargo kernel-clippy` clean.
- [x] `cargo host-test` passes.
- [x] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean if any kernel, hal or test-hal source changes (not expected).
- [x] `tools/smoke.sh --int` PASS if any BSP source changes (possible via `perf-bench` clippy fixes).
- [x] Every touched markdown file has all `](...)` link targets resolving.
- [x] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with a `Refs: ADR-0040` trailer.
- [x] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Vanishing-test hazard.** Both release-only tests are gated `cfg(not(debug_assertions))`. If someone sets `debug-assertions = true` in `[profile.release]`, those tests are compiled out rather than failing, the debug-gated sibling `console_write_is_a_syscall_in_debug_builds` (`abi.rs:371-375`) runs and passes, and `console_write` silently exists in the "release" kernel. A bare name filter that matches zero tests also exits 0. The "both tests ran" assertion is therefore the only thing that makes the profile-flip failure visible; do not drop it.
- **Location re-verification (2026-10-11, HEAD `400dec0`):** every `file:line` above was re-checked with `sed -n`/`grep -n` and matches the tree; nothing drifted. `phase-b2.md` line numbers shift as banners are added, so locate its items by headline.
- The Polish item "release profile self-documenting about panic strategy" is already satisfied by `Cargo.toml:59-60`; the new comment belongs in that same block.
- Sequencing: independent of the other Track B.2-1 tasks. [T-065](T-065-debug-console-feature-flag.md) must land after this task so the release gate exists to catch a mistake there.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-11 | Codex (AI agent) | Preflight contract review: see [review artifact](../../reviews/code-reviews/2026-10-11-phase-b2-track1-preflight.md); documentation corrected, implementation not started; ADR-0040 remains Proposed. |
| 2026-10-12 | Codex (AI agent) | Started approved step 4 after T-031 local/hosted gates and both fresh rounds (`8437158`). Live verification in an isolated archive of `e79e10a`: adding release `debug-assertions = true` makes the exact narrow Cargo command exit 0 with 0 tests (259 filtered out), confirming the vanishing-test hazard. Isolated perf-bench clippy baseline is clean. Plan: release aliases/build/clippy and full host tests in existing jobs; canonical two-name/two-pass assertion with isolated local/hosted profile-flip probe; cfg-scope three debug-only test imports; restore debug image immediately before perf build/lint. Run conditional Miri and distinct security review for the syscall test-file delta. No new policy decision or ADR. |
| 2026-10-12 | Codex (AI agent) | Local gates passed: fmt, full ShellCheck 0.11.0/actionlint, host clippy, debug/release kernel clippy, exact userland clippy, 366 debug host tests and 356 release host tests (249 kernel + 46 HAL + 58 test-HAL + 3 doc; two ignored HAL doctests in either profile). Warm local `cargo test --release` wall time 1.49 s; the three unused debug-only imports are now cfg-scoped, with no syscall gate-logic change. Debug/release kernel builds and release-run alias echo pass; release hello is 69 bytes, then debug image restored to 117 bytes/SHA `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88` immediately before clean perf-bench build/clippy. Miri passes the same 366 tests with no UB failure (existing optimization/provenance warnings retained). The canonical guard runs exactly two named release tests; isolated profile flip is rejected with guard exit 1. Seven controlled guard outcomes verify missing/incorrect tests, failure summary, Cargo pipe failure propagation and cleanup under Bash 3.2/spaced paths; 59 QEMU argument fixtures pass. No BSP/runtime source changed, so conditional new smoke gate is N/A; T-034 owns release QEMU execution. Hosted proof and both fresh code/security rounds pending. Logs: `/tmp/tyrne-b21-step4/` (ephemeral). |
