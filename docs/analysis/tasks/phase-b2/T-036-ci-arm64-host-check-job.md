# T-036 — Add an arm64 host-check CI job

- **Phase:** B.2
- **Milestone:** Track B.2-1 (polish; not exit-gating)
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-037](T-037-userland-bare-metal-cfg-gate.md)
- **Informs:** none
- **ADRs required:** ADR-0040 (Accepted), including its Track B.2-1 implementation policy

---

## User story

As the maintainer developing on Apple Silicon, I want a CI job that builds, lints and tests the workspace on an arm64 host, so that the bug class "a `target_arch = "aarch64"` gate also matches the host" cannot reappear unnoticed.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), which marks this task as polish and optional for the Phase B.2 exit: if it is not completed it is recorded as a carry-forward in the closure review. Every CI job runs on `ubuntu-latest` (`.github/workflows/ci.yml:74,109,161,199,233`), an x86_64 host, so a cfg gate that tests only `target_arch = "aarch64"` evaluates false there and looks correct. On an arm64 host it is true for the host build too: `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` (CI's exact Miri command) fails with `error[E0152]: found duplicate lang item panic_impl` (measured 2026-10-11 on an Apple-Silicon Mac). The userland gates were added in T-027's review round (`ce25727` "cfg-gate for --workspace/Miri", `68f07ec` "gate hello.ld to aarch64") and CI could only ever exercise them on x86_64; [T-037](T-037-userland-bare-metal-cfg-gate.md) fixes the gates, this task adds the signal that would have caught them.

This task covers the Polish item "Extend the aarch64-host build-hazard fix (Track B.2-3) with an actual periodic or PR-gated arm64 host-check CI job" (line 601 of the opening snapshot of `phase-b2.md`) and the closing sentence of the Track B.2-3 HIGH item "The arch-only cfg gate is not confined to `build.rs`" (line 323): "Track B.2-1 tracks adding the arm64-host CI signal". Locate both by headline, since that file shifts as banners are added.

## Acceptance criteria

- [x] ADR-0040's Track B.2-1 policy is Accepted before implementation: D1 required PR check, D2 `ubuntu-24.04-arm`, D3 native check/clippy/test, D4 workspace Miri included. Record routine command/runner setup details in task history.
- [ ] `.github/workflows/ci.yml` has a job on `ubuntu-24.04-arm` using the pinned nightly that runs `cargo check`, `cargo clippy --all-targets -- -D warnings`, `cargo test` and `cargo miri test`, each with `--workspace --exclude tyrne-bsp-qemu-virt`; architecture-specific caches cannot restore x86_64 build artifacts.
- [ ] The job is green on `development` and the final PR after T-037; record wall time in the review history. Verify the first merged `main` run after maintainer merge, and keep that evidence pending until it exists.
- [ ] Negative test, recorded in the review history: restoring the arch-only gate in an isolated temporary copy of `userland/hello/src/main.rs` makes the exact ARM workspace gate command fail. Repeat in an isolated hosted ARM runner workspace with an expected-failure assertion; never create a scratch branch or commit the regression. Record the original Miri failure class separately from a harness's successful assertion of that failure.
- [ ] Add the job's exact display name to live branch protection after the remote green run; record the date and read-back evidence and include it in T-035's versioned definition. Preserve all existing required checks.
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

- **Decisions Accepted by the maintainer in ADR-0040 on 2026-10-11:**
  - **D1 trigger.** Required on PRs and normal CI pushes, so an ARM-host regression is caught before merge.
  - **D2 runner.** Explicit `ubuntu-24.04-arm`, verified against [GitHub's current runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) on 2026-10-11; this is a standard runner available without a paid-runner commitment for the public repository. Linux keeps the environment close to the x86 CI jobs; the maintainer's macOS validation remains complementary evidence.
  - **D3 commands.** Native check, clippy and tests all run. Miri does not replace native linking/testing.
  - **D4 Miri.** Include the exact workspace command that exposed the bug. Record its actual runtime before considering a later cadence change; do not weaken the required check silently.
- **Location re-verification (2026-10-11, HEAD `400dec0`):** the `runs-on` lines of `ci.yml`, `infrastructure.md:106-110,209` and the commit hashes above were re-checked and match; nothing drifted.
- Sequencing: depends on [T-037](T-037-userland-bare-metal-cfg-gate.md); independent of the other Track B.2-1 tasks. Not an exit gate.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Draft |
| 2026-10-11 | Codex (AI agent) | Preflight contract review: see [review artifact](../../reviews/code-reviews/2026-10-11-phase-b2-track1-preflight.md); documentation corrected, implementation not started; ADR-0040 remains Proposed. |
| 2026-10-11 | @cemililik; Codex recorded the decision | ADR-0040 Accepted after the [approval follow-up](../../reviews/code-reviews/2026-10-11-adr-0040-approval-follow-up.md); design choices settled, status Ready. Implementation and hosted evidence remain pending. |
