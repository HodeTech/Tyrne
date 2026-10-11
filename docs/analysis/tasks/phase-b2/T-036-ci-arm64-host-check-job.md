# T-036 — Add an arm64 host-check CI job

- **Phase:** B.2
- **Milestone:** Track B.2-1 (polish; not exit-gating)
- **Status:** In Review
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-037](T-037-userland-bare-metal-cfg-gate.md)
- **Informs:** none
- **ADRs required:** ADR-0040 (Accepted), including its Track B.2-1 implementation policy

---

## User story

As the maintainer developing on Apple Silicon, I want a CI job that builds, lints and tests the workspace on an arm64 host, so that the bug class "a `target_arch = "aarch64"` gate also matches the host" cannot reappear unnoticed.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), which marks this task as polish and optional for the Phase B.2 exit; the requested Track B.2-1 sequence nevertheless includes it. At the opening baseline, every CI job ran on `ubuntu-latest`, an x86_64 host, so a cfg gate that tested only `target_arch = "aarch64"` evaluated false there and looked correct. On an arm64 host it matched the host build too: `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` failed with `error[E0152]: found duplicate lang item panic_impl` (measured 2026-10-11 on an Apple-Silicon Mac). The userland gates were added in T-027's review round (`ce25727` "cfg-gate for --workspace/Miri", `68f07ec` "gate hello.ld to aarch64"); [T-037](T-037-userland-bare-metal-cfg-gate.md) fixes them, and this task adds the native ARM signal that would have caught the bug.

This task covers the Polish item "Extend the aarch64-host build-hazard fix (Track B.2-3) with an actual periodic or PR-gated arm64 host-check CI job" (line 601 of the opening snapshot of `phase-b2.md`) and the closing sentence of the Track B.2-3 HIGH item "The arch-only cfg gate is not confined to `build.rs`" (line 323): "Track B.2-1 tracks adding the arm64-host CI signal". Locate both by headline, since that file shifts as banners are added.

## Acceptance criteria

- [x] ADR-0040's Track B.2-1 policy is Accepted before implementation: D1 required PR check, D2 `ubuntu-24.04-arm`, D3 native check/clippy/test, D4 workspace Miri included. Record routine command/runner setup details in task history.
- [x] `.github/workflows/ci.yml` has a job on `ubuntu-24.04-arm` using the pinned nightly that runs `cargo check`, `cargo clippy --all-targets -- -D warnings`, `cargo test` and `cargo miri test`, each with `--workspace --exclude tyrne-bsp-qemu-virt`; architecture-specific caches cannot restore x86_64 build artifacts.
- [x] The job is green on `development` after T-037; record wall time in the review history.
- [ ] The final PR's ARM check is green.
- [ ] Verify the first merged `main` run after maintainer merge; this evidence remains pending until it exists.
- [x] Negative test, recorded in the review history: restoring the arch-only gate in an isolated temporary copy of `userland/hello/src/main.rs` makes the exact ARM workspace gate command fail. Repeat in an isolated hosted ARM runner workspace with an expected-failure assertion; never create a scratch branch or commit the regression. Record the original Miri failure class separately from a harness's successful assertion of that failure.
- [ ] Add the job's exact display name to live branch protection after the remote green run; record the date and read-back evidence and include it in T-035's versioned definition. Preserve all existing required checks.
- [x] Documentation: `docs/guides/ci.md` (job table and "why an arm64 job") and `docs/standards/infrastructure.md` (runners and workflow jobs) describe the job; the `ci.yml` header comment distinguishes intended and live registration.

## Out of scope

- The cfg fix itself: [T-037](T-037-userland-bare-metal-cfg-gate.md).
- The merge-gating QEMU smoke job: [T-034](T-034-ci-qemu-smoke-job.md); building the BSP for the host (impossible by design, always excluded).
- Replacing or changing the existing x86_64 jobs, or running llvm-cov on arm64.

## Approach

Run all four mandatory native workspace commands on `ubuntu-24.04-arm`, with the pinned nightly, clippy and Miri installed and `cargo miri setup` before interpretation. Verify the actual machine and Rust host before running checks. Exclude only the bare-metal BSP so both host-gated userland crates participate. Every workflow cache key and restore prefix includes `runner.arch`. After positive clippy, `tools/test-ci-gates.sh --arm-host` restores only hello's six arch-only predicates in a private tracked-worktree copy and requires the exact workspace clippy command to fail with the duplicate `panic_impl` diagnostic. Native ARM is required; the probe refuses x86 hosts before making a copy. Its success asserts rejection and is separate from the historical Miri failure.

## Definition of done

Beyond the acceptance criteria:

- [x] `cargo fmt --all -- --check` clean.
- [x] `cargo host-clippy` clean with `-D warnings`.
- [x] `cargo kernel-clippy` clean.
- [x] `cargo host-test` passes.
- [x] Every touched markdown file has all `](...)` link targets resolving.
- [x] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with a `Refs: ADR-0040` trailer.
- [x] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

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
| 2026-10-12 | Codex (AI agent) | Step 7 implementation: required native ARM job, all four commands, exact host verification and architecture-isolated caches throughout CI. On `aarch64-apple-darwin`, pinned rustc `1.94.0-nightly (86a49fd71 2026-01-14)`, workspace check/clippy/test/Miri passed (366 tests, two ignored HAL doctests; existing Miri optimization/provenance warnings, no UB). The private arch-only clippy regression exited 101 with `error[E0152]: found duplicate lang item panic_impl`; the harness correctly returned success. fmt, host/kernel clippy and host tests passed. Linux ARM hosted timing, two fresh rounds, live registration and final PR evidence remain pending. |
| 2026-10-12 | Codex (AI agent) | Ten controlled ARM probe/CLI cases passed under system Bash 3.2, covering intended rejection, unexpected success, unrelated failure, x86 host refusal, anchor drift, argument errors, paths with spaces, private Cargo targets, source preservation and cleanup. Actionlint, ShellCheck, changed Markdown link resolution and whitespace checks passed. |
| 2026-10-12 | Codex (AI agent) | Hosted Linux ARM source `bf20ec9739db635183b1b930f4da9f2c2b6813bf`, [run 38184932784 / ARM job 114605118899](https://github.com/HodeTech/Tyrne/actions/runs/38184932784/job/114605118899): all four workspace gates passed on verified `aarch64-unknown-linux-gnu`, pinned rustc 1.94.0-nightly; native tests and Miri each passed 366 tests with two ignored HAL doctests. Isolated arch-only clippy failed with E0152/exit101 and the expected-failure harness passed. Full job 101 s; native check 1 s, clippy 1 s, negative probe 7 s, native tests 4 s, Miri setup 17 s and Miri 54 s (API timestamp granularity). Downloaded log and job JSON inspected; existing Miri warnings are not UB findings. Live registration, final PR and first merged main remain separate pending evidence. |
| 2026-10-12 | Codex (AI agent) | Full development run 38184932784 completed success for all seven jobs, including coverage (informational). Required ARM registration remains deferred until both fresh rounds are complete; this green source is eligible for the subsequent local administrative addition. |
| 2026-10-12 | Fresh independent code + integration reviewers; Codex reconciled | Round 1 both Approve; one duplicate Low enforcement-wording finding independently verified and fixed. Full reports and correction are in the [code review](../../reviews/code-reviews/2026-10-12-t036-native-arm-ci.md). No runtime blocker; fresh Round 2 and live registration pending. |
| 2026-10-12 | Fresh independent code + integration reviewers; Codex reconciled | Round 2 both Approve, zero new findings; Low correction independently verified. Full reports read and appended to the [review](../../reviews/code-reviews/2026-10-12-t036-native-arm-ci.md). Both rounds and local/hosted gates complete; live registration is the next authorized action, final PR/main evidence remains pending. |
