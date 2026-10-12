# T-037 — Fix the bare-metal target gate in the userland crates

- **Phase:** B.2
- **Milestone:** Track B.2-3
- **Status:** Done
- **Created:** 2026-10-11
- **date_done:** 2026-10-12
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-036](T-036-ci-arm64-host-check-job.md), [T-038](T-038-console-write-x2-clobber.md), [T-064](T-064-tyrne-user-api-polish.md), [T-067](T-067-adversarial-el0-smoke-image.md)
- **ADRs required:** none

---

## User story

As a developer on an Apple-Silicon or ARM64-Linux machine, I want the userland crates to select the bare-metal code path only on the real `aarch64-unknown-none` target, so that `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` (the exact command CI runs) and the other workspace host commands build on my machine.

## Context

**Opening snapshot (2026-10-11, before `f2d577f`):** Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from three items in [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-3 (lines 286, 322, 325, one bug surfaced three times). `userland/hello/build.rs:18` links the userland linker script when `CARGO_CFG_TARGET_ARCH == "aarch64"`, and the cfg gates in `userland/hello/src/main.rs` and `userland/tyrne-user/src/lib.rs` use `target_arch = "aarch64"` alone. That is true on an aarch64 **host** as well as on the bare-metal triple. The discriminator is `target_os = "none"`: `aarch64-unknown-none` has it, an Apple-Silicon host has `"macos"`. The correct pattern already exists at `bsp-qemu-virt/src/main.rs:144` (`#[cfg(all(target_arch = "aarch64", target_os = "none"))]`).

Measured 2026-10-11 on an Apple-Silicon Mac (nightly-2026-01-15): `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` fails with `error[E0152]: found duplicate lang item panic_impl`, because the host build of `hello` takes the `#![no_std]` + `#[panic_handler]` branch while std is also linked. CI never sees this because every job runs on x86_64 `ubuntu-latest` (the arm64-host CI signal is [T-036](T-036-ci-arm64-host-check-job.md)). At task opening, the fix below had been **verified on a scratch copy of HEAD on 2026-10-11 but not yet applied to the repository**. Implementation commit `f2d577f` now applies it; the review history records verification and remaining review gates.

## Acceptance criteria

- [x] `userland/hello/build.rs` emits `cargo:rustc-link-arg=-T…/hello.ld` only when both `CARGO_CFG_TARGET_ARCH == "aarch64"` and `CARGO_CFG_TARGET_OS == "none"`; its header comment and the comment at lines 16-17 describe the OS check.
- [x] Every `target_arch = "aarch64"` gate in `userland/hello/src/main.rs` (lines 23, 25, 31, 41, 54, 63) and `userland/tyrne-user/src/lib.rs` (lines 28, 35, 44, 83, 126, 134, 152) becomes `all(target_arch = "aarch64", target_os = "none")` (negated as `not(all(...))` for the host stubs at `main.rs:63`, `lib.rs:126` and `:152`). `grep -rn 'target_arch = "aarch64"' userland --include='*.rs'` shows no gate that lacks `target_os = "none"`.
- [x] Each of the three files carries a one-line comment at its gate cross-referencing the other two and `bsp-qemu-virt/src/main.rs:144`, so the pattern cannot drift independently again.
- [x] On an arm64 host, `cargo check --workspace --exclude tyrne-bsp-qemu-virt`, `cargo clippy --workspace --exclude tyrne-bsp-qemu-virt --all-targets -- -D warnings` and `cargo test --workspace --exclude tyrne-bsp-qemu-virt` pass.
- [x] Tests: `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` (the exact CI command, `.github/workflows/ci.yml:224`) passes on an arm64 host; the verified scratch run was 46 hal + 259 kernel + 58 test-hal + 3 doc tests.
- [x] The bare-metal output is unchanged: `tools/build-userland.sh` yields `hello.bin` of 117 bytes with sha256 `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`, and `cargo kernel-build`, `cargo kernel-clippy` and `tools/smoke.sh --int` pass as before.
- [x] Decision recorded in this task's review history: keep the spelled-out inline `all(...)` form (the verified one) or centralise it as a `tyrne_bare_metal` cfg alias (see Design notes).

## Out of scope

- Adding an arm64 host job to CI, which would catch a regression of this bug: [T-036](T-036-ci-arm64-host-check-job.md).
- The `x2` clobber in the `console_write` shim in the same file: [T-038](T-038-console-write-x2-clobber.md). This task appends the target-gate amendment to UNSAFE-2026-0033 when narrowing the cfg; T-038 owns the later clobber amendment. Preserve the original audit fields rather than rewriting the Status wording.
- API, doc and `no_std` polish of `tyrne-user` (items at `phase-b2.md` 357, 406, 514, 517, 520): [T-064](T-064-tyrne-user-api-polish.md).
- The `--exclude tyrne-userland-hello --exclude tyrne-user` arguments on the `cargo llvm-cov` step (`.github/workflows/ci.yml:277`); changing coverage scope is not part of this fix.

## Approach

Apply the verified fix: in `userland/hello/src/main.rs` and `userland/tyrne-user/src/lib.rs`, replace each `target_arch = "aarch64"` gate with `all(target_arch = "aarch64", target_os = "none")`. In `userland/hello/build.rs`, additionally require `std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("none")`. Cargo sets those variables for the **target** being built, so a host build (including `cargo miri`, whose target is the host triple) falls through to the std stub. The phase item also suggests one shared alias, `tyrne_bare_metal`, set through `.cargo/config.toml` `[target.aarch64-unknown-none] rustflags = ["--cfg", "tyrne_bare_metal"]`. Cargo exports extra target cfgs to build scripts through `CARGO_CFG_<cfg>` (so a custom alias could be read as `CARGO_CFG_TYRNE_BARE_METAL`); native `#[cfg]` on the build-script binary itself instead describes its host. The inline architecture-and-OS form needs no custom cfg registration and is the default recommendation. See [Cargo's build-script environment documentation](https://doc.rust-lang.org/cargo/reference/environment-variables.html#environment-variables-cargo-sets-for-build-scripts).

## Definition of done

Beyond the acceptance criteria:

- [x] `cargo fmt --all -- --check` clean.
- [x] `cargo host-clippy` clean with `-D warnings`.
- [x] `cargo kernel-clippy` clean.
- [x] `cargo host-test` passes.
- [x] Miri: the workspace command in the acceptance criteria is the gate; the narrower `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` only matters when kernel/hal/test-hal code changes, which it does not here.
- [x] `tools/smoke.sh --int` PASS (userland code changed).
- [x] No new `unsafe` identifier is needed; append the target-narrowing amendment to UNSAFE-2026-0033 and obtain a distinct security review of the changed compilation boundary, recording the artifact and `Security-Review:` trailer.
- [x] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [x] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Decision to record.** The inline `all(...)` form is the one verified on the scratch copy and has no new moving parts. A cfg alias needs a `[target.aarch64-unknown-none] rustflags` entry and a `check-cfg` registration to avoid `unexpected_cfgs` warnings. Default recommendation: keep the inline form unless the alias is judged worth that cost.
- **Not tested separately.** Whether the `tyrne-user/src/lib.rs` edit is strictly required (that crate is unconditionally `#![no_std]`, so only `hello` breaks the host build) was not isolated. Keep the three files consistent regardless.
- **Item scope.** The phase item at line 325 lists `lib.rs:28,35,44,83,134`; the live tree has two more gates, the `not(target_arch = "aarch64")` host stubs at `lib.rs:126` and `:152`, which must flip with the others or the host build loses `console_write`/`task_exit`.
- **Re-verification.** All file:line locations above were checked against the current tree on 2026-10-11 (`grep -n 'target_arch' userland/hello/src/main.rs userland/tyrne-user/src/lib.rs`, `sed -n 12,23p userland/hello/build.rs`); none had drifted. The `phase-b2.md` line numbers (286, 322, 325) were taken from the live file after the ADR-0040 kickoff added its status banner (+2 lines versus the pre-kickoff snapshot).
- **Sequencing.** Land before [T-038](T-038-console-write-x2-clobber.md) and [T-064](T-064-tyrne-user-api-polish.md), which edit the same files. [T-036](T-036-ci-arm64-host-check-job.md) needs this fix so its job can start green.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-11 | Codex (AI agent) | Preflight contract review: see [review artifact](../../reviews/code-reviews/2026-10-11-phase-b2-track1-preflight.md); documentation corrected, implementation not started; ADR-0040 remains Proposed. |
| 2026-10-11 | Codex (AI agent) | Started after maintainer Acceptance of ADR-0040 (`960bdef`). Live source still reproduces the three arch-only gates and ARM Miri failure recorded in the approval follow-up. Keep the inline `all(target_arch = "aarch64", target_os = "none")` form: no custom cfg registration or build-script host/target ambiguity. |
| 2026-10-11 | Codex (AI agent) | Implementation gates passed on Apple Silicon / `nightly-2026-01-15`: workspace check, workspace clippy `--all-targets -D warnings`, workspace test and exact workspace Miri (each excluding only BSP); native/Miri totals 366 passed plus two ignored HAL doctests. `cargo host-clippy`, `cargo host-test`, `cargo fmt --all -- --check`, userland build, kernel build/clippy and `tools/smoke.sh --int --timeout 5` passed. Debug image remains 117 bytes / SHA-256 `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`. Smoke contains greeting, userspace exit and completion with two SVCs and no fault. A compiled build-script matrix emitted the linker argument only for aarch64/none, not ARM macOS/Linux, x86 Linux/none, or missing target variables. In Review for two fresh rounds; security approval remains pending. |
| 2026-10-12 | Codex (AI agent); `b21_step1_round1_security` | Introducing commit `f2d577f96b4c98f3c0998f538304e38d4232d409`. Distinct security pass [approves the target-boundary narrowing](../../reviews/security-reviews/2026-10-12-t037-target-boundary.md), independently reproducing workspace Miri/native tests (366 passed), 15 fail-closed target-environment cases, host/bare-metal cfg expansions and the unchanged image SHA. It expressly excludes T-038's known x2 defect. First-round lifecycle wording findings fixed; second fresh round remains pending. |
| 2026-10-12 | `b21_step1_round2_code`; `b21_step1_round2_security` | Fresh second round on `960bdef..69a4109`: both Approve, no new findings; both first-round Low lifecycle findings resolved. The [code report](../../reviews/code-reviews/2026-10-12-t037-target-boundary.md) and [security report](../../reviews/security-reviews/2026-10-12-t037-target-boundary.md) record independent target-matrix/cfg expansion, unchanged source bodies and original audit-prefix checks. Security also executes host stubs locally and reproduces the exact 117-byte hash from a fresh isolated bare-metal build. No claim of T-038 assembly soundness, hosted ARM execution or Done promotion. Both required review rounds and applicable local implementation gates pass; T-033 may start under ADR-0040's stacked-execution policy. T-037 remains In Review for the final PR. |
| 2026-10-12 | @cemililik; Codex recorded completion | Maintainer merged [PR #48](https://github.com/HodeTech/Tyrne/pull/48) at full `c16997e003fbd1726d1205734380394781c52002` and explicitly authorized Done promotion. First merged-main [CI 38217531542](https://github.com/HodeTech/Tyrne/actions/runs/38217531542) passes all seven jobs, including native ARM/Miri and both production QEMU profiles; downloaded controls are 23/23. Default-branch [performance dispatch 38217799773](https://github.com/HodeTech/Tyrne/actions/runs/38217799773) passes with 20 valid/0 failed samples. [Post-merge retrospective](../../reviews/business-reviews/2026-10-12-phase-b2-track1-completion.md) records exact-source evidence, remaining scope and next Ready task T-038. Status In Review → Done; date_done 2026-10-12. Phase B.2 remains Active. |
