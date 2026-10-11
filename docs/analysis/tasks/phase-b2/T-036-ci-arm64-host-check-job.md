# T-036 — Add an arm64 host-check CI job

- **Phase:** B.2
- **Milestone:** Track B.2-1 (polish; not exit-gating)
- **Status:** Draft
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-037](T-037-userland-bare-metal-cfg-gate.md)
- **Informs:** none
- **ADRs required:** none

---

## User story

As the maintainer developing on Apple Silicon, I want a CI job that builds, lints and tests the workspace on an arm64 host, so that the bug class "a `target_arch = "aarch64"` gate also matches the host" cannot reappear unnoticed.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), which marks this task as polish and optional for the Phase B.2 exit: if it is not completed it is recorded as a carry-forward in the closure review. Every CI job runs on `ubuntu-latest` (`.github/workflows/ci.yml:74,109,161,199,233`), an x86_64 host, so a cfg gate that tests only `target_arch = "aarch64"` evaluates false there and looks correct. On an arm64 host it is true for the host build too: `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` (CI's exact Miri command) fails with `error[E0152]: found duplicate lang item panic_impl` (measured 2026-10-11 on an Apple-Silicon Mac). The userland gates were added in T-027's review round (`ce25727` "cfg-gate for --workspace/Miri", `68f07ec` "gate hello.ld to aarch64") and CI could only ever exercise them on x86_64; [T-037](T-037-userland-bare-metal-cfg-gate.md) fixes the gates, this task adds the signal that would have caught them.

This task covers the Polish item "Extend the aarch64-host build-hazard fix (Track B.2-3) with an actual periodic or PR-gated arm64 host-check CI job" (line 601 of the opening snapshot of `phase-b2.md`) and the closing sentence of the Track B.2-3 HIGH item "The arch-only cfg gate is not confined to `build.rs`" (line 323): "Track B.2-1 tracks adding the arm64-host CI signal". Locate both by headline, since that file shifts as banners are added.

## Acceptance criteria

- [ ] Decisions D1-D4 (trigger, runner, command set, Miri in or out; see Design notes) are made and recorded before the job merges, in the review history or, if the maintainer judges it a policy change, in an ADR or rider, as the closing note of `phase-b2.md` requires for design decisions surfaced by a task.
- [ ] `.github/workflows/ci.yml` (or a separate workflow, if periodic) has a job on a GitHub-hosted arm64 runner using the pinned nightly that runs at least `cargo check`, `cargo clippy --all-targets -- -D warnings` and `cargo test`, each with `--workspace --exclude tyrne-bsp-qemu-virt`, plus `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` if D4 included it.
- [ ] The job is green on `main` after T-037 has landed; its wall time is recorded in the review history.
- [ ] Negative test, recorded in the review history: on a scratch branch (never merged), restoring the arch-only gate in `userland/hello/build.rs` or `userland/hello/src/main.rs` turns the job red.
- [ ] Merge policy matches the decision: if PR-gated, the job's exact display name is added to branch protection (manual, outside the repo) and the date recorded; if periodic, the trigger and where a failure becomes visible are documented.
- [ ] Documentation: `docs/guides/ci.md` (job table, and a short "why an arm64 job" paragraph) and `docs/standards/infrastructure.md` (the "Runners" list at lines 106-110 and the workflow job list at line 209) describe the job; the `ci.yml` header comment stays accurate.

## Out of scope

- The cfg fix itself: [T-037](T-037-userland-bare-metal-cfg-gate.md).
- The merge-gating QEMU smoke job: [T-034](T-034-ci-qemu-smoke-job.md); building the BSP for the host (impossible by design, always excluded).
- Replacing or changing the existing x86_64 jobs, or running llvm-cov on arm64.

## Approach

Add one job that mirrors the existing `lint-and-host-test` toolchain setup (`ci.yml:81-84`) on an arm64 runner, then runs the three cargo commands above. The commands are the ones recorded as passing after T-037 on a scratch copy (check, clippy `--all-targets`, test, and Miri). Land it after T-037, otherwise it is red from its first run. If Miri is included, mirror the `miri` job's `cargo miri setup` step and expect a longer runtime than the plain commands.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes.
- [ ] Every touched markdown file has all `](...)` link targets resolving.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with a `Refs: ADR-0040` trailer.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions (maintainer):**
  - **D1 trigger.** PR-gated (catches the regression before merge, costs runner minutes on every PR), periodic via cron or `workflow_dispatch` (cheap, late signal), or both.
  - **D2 runner.** `macos-latest` (an arm64 image, and the maintainer's own development environment), or an arm64 Linux hosted runner if one is available to this repository (a label such as `ubuntu-24.04-arm`; availability, cost and minute multipliers must be checked against GitHub's current documentation when deciding, not assumed here).
  - **D3 commands.** Whether `cargo clippy` and `cargo test` are both needed or `cargo check` plus Miri suffices.
  - **D4 Miri.** Whether the Miri gate runs on arm64; it is the command that originally exposed the bug, but it is the slowest.
- **Location re-verification (2026-10-11, HEAD `400dec0`):** the `runs-on` lines of `ci.yml`, `infrastructure.md:106-110,209` and the commit hashes above were re-checked and match; nothing drifted.
- Sequencing: depends on [T-037](T-037-userland-bare-metal-cfg-gate.md); independent of the other Track B.2-1 tasks. Not an exit gate.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Draft |
