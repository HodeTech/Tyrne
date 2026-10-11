# T-034 — Add a merge-gating qemu-smoke CI job

- **Phase:** B.2
- **Milestone:** Track B.2-1
- **Status:** In Review
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-030](T-030-ci-release-profile-gate.md), [T-033](T-033-qemu-tooling-smp-and-timeout.md)
- **Informs:** [T-035](T-035-ci-hygiene-tail.md), [T-066](T-066-bsp-syscall-context-extraction.md), [T-067](T-067-adversarial-el0-smoke-image.md), [T-074](T-074-phase-c-readiness-sweep.md)
- **ADRs required:** none

---

## User story

As the maintainer, I want CI to boot the kernel under QEMU and fail the PR when the boot, the EL0 round trip or the fault-class check breaks, so that the only automated check of BSP hardware-facing and syscall-boundary behaviour stops being a manual ritual before Phase C adds concurrency.

## Context

The following describes the opening baseline; current implementation and evidence are recorded in Review history.

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). `tools/smoke.sh` boots the built ELF under `qemu-system-aarch64`, bounds the run, captures the trace and exits non-zero if the `tyrne: all tasks complete` marker is missing or a panic / CPU-fault pattern appears (`tools/smoke.sh:102-119`). No CI job invokes it: the job list in `.github/workflows/ci.yml` (lines 65-277) never mentions it, `docs/guides/ci.md:55` still defers the automation to "a T-009 follow-up", and `docs/standards/infrastructure.md:82` lists it under "Planned gates" as maintainer-launched. Phase B's own flag K3-7 (`docs/roadmap/phases/phase-b.md:291`) asked for exactly this wiring once CI existed. Milestone C1's `-smp 4` smoke criterion builds on this job, so it must be a real, exercised gate before any SMP-touching PR.

This task covers two HIGH items of `phase-b2.md` Track B.2-1 (line numbers as of the opening snapshot; locate by headline): "`tools/smoke.sh` ... is never invoked by CI" (line 33) and its cross-cut restatement "QEMU smoke tests ... are not wired into CI, right as Phase C begins" (line 39). It **replaces the stale T-009 cross-reference** in `ci.md:55`: T-009 was the timer-init task, and this task is the smoke-in-CI follow-up that sentence meant.

## Acceptance criteria

- [x] `.github/workflows/ci.yml` has a `qemu-smoke` job on `ubuntu-latest` with an explicit display `name:`, a `timeout-minutes` bound, SHA-pinned actions (per `infrastructure.md` "GitHub Actions pinning"), and the `kernel-build` job's toolchain setup (pinned nightly, `aarch64-unknown-none`, `llvm-tools-preview`) plus `sudo apt-get install -y qemu-system-arm`; it builds the debug userland/kernel and runs `tools/smoke.sh --int`, then builds the release userland/kernel and runs `tools/smoke.sh --release --int`. Build the matching userland before each profile because `hello.bin` is shared.
- [x] The plain-vs-`--int` choice is recorded in the review history: `--int` is used (see Design notes).
- [x] The debug smoke requires all three existing serial markers: `hello from userspace`, `tyrne: userspace task exited`, and `tyrne: all tasks complete`, as well as absence of panic/CPU-fault patterns. Completion alone is insufficient: kernel task A can print it without an EL0 task ever running.
- [x] Release smoke requires `tyrne: userspace task exited` and `tyrne: all tasks complete`, forbids `hello from userspace`, and rejects panic/CPU-fault patterns. Explicit ELF invocations select the correct expectation through `--release` where applicable; document and test that contract. No syscall/userland behaviour is changed for this check.
- [x] On failure the job uploads the smoke trace (`${TMPDIR:-/tmp}/tyrne-smoke.$$.log`, a PID-suffixed name per `smoke.sh:65`) as an artifact.
- [ ] Negative tests, recorded in the review history: isolated copies/runner workspaces demonstrate that omitting the EL0 task, omitting completion, emitting a panic/CPU-fault trace, and injecting a greeting into a release trace each make the same smoke gate exit non-zero. The hosted probe asserts those failures and uploads a downloadable trace artifact. No scratch branch or deliberately broken commit is used; distinguish expected probe failures from the clean production job's verdict.
- [ ] Live GitHub step: add the job's exact display name to branch protection's required checks after its first remote green run; preserve all existing settings and record the date and read-back evidence. T-035 subsequently versions and verifies this policy; ADR-0040 specifies the approved apply arrangement.
- [x] Documentation: `docs/guides/ci.md` (job table, local-command table, the `ci.md:55` paragraph rewritten to say the smoke job exists and no longer cites T-009, and the required-check list at line 90 with its "four real gates" count) and `docs/standards/infrastructure.md` (the bullet at line 82 moved from "Planned gates" to "Required gates", the "Runners" smoke line at 109, the required-checks list at 186, the job list at 209) name the new job and check name; the `ci.yml` header comment (lines 7-9) lists it among the merge gates, and its permissions comment no longer claims that the pipeline never uploads artifacts.
- [ ] The first green run's wall time and the CI QEMU version are recorded in the review history next to the local baseline (2026-10-11, maintainer's Mac, QEMU 11.1.1: `tools/smoke.sh --int` PASS, boot-to-end 4.7 ms).

## Out of scope

- Multi-core runs (`--smp` above 1): the job runs the default single-core configuration; the flag itself is [T-033](T-033-qemu-tooling-smp-and-timeout.md).
- Asserting the exact EL0 SVC count or adding per-attack markers in the script: [T-067](T-067-adversarial-el0-smoke-image.md) and [T-066](T-066-bsp-syscall-context-extraction.md).
- Scheduling `tools/perf-harness.sh`: [T-035](T-035-ci-hygiene-tail.md).

## Approach

Add one job, copying the `kernel-build` setup block (`ci.yml:107-134`) so the toolchain and cache keys stay consistent, then install QEMU from apt (`run-qemu.sh:74` already names the package). Build and smoke debug first, then release; always produce the matching userland before the BSP. `smoke.sh` without an ELF argument rebuilds both (`smoke.sh:50-57`); explicit matching build steps distinguish compilation from boot failures, with the second build incremental (or pass the ELF path and profile explicitly). Make the marker expectations profile-aware: hello already ignores a rejected console call (`userland/hello/src/main.rs:45-47`) and exits even in release, so profile-aware marker checks need no syscall/userland behavior change. Upload traces on success and failure with an `if: always()` artifact step; PID-suffixed names require a glob, optionally with `TMPDIR` set to `${{ runner.temp }}`. Top-level `permissions: contents: read` already suffices for artifact upload. Pin any new action by full commit SHA with a trailing version comment; do not copy a SHA from memory.

## Definition of done

Beyond the acceptance criteria:

- [x] `cargo fmt --all -- --check` clean.
- [x] `cargo host-clippy` clean with `-D warnings`.
- [x] `cargo kernel-clippy` clean.
- [x] `cargo host-test` passes.
- [x] `tools/smoke.sh --int` and `tools/smoke.sh --release --int` PASS locally.
- [ ] The new job is green on the final PR that adds it.
- [x] Every touched markdown file has all `](...)` link targets resolving.
- [x] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with a `Refs: ADR-0040` trailer.
- [x] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Why `--int`.** `smoke.sh` always applies the panic/fault grep (`tyrne panic|Translation fault|Permission fault|Data Abort|Prefetch Abort|Unallocated Instruction`, line 114), but without `-d int,unimp` QEMU never logs exceptions, so those patterns could not match; `--int` is what makes the CPU-fault gate real. It does not count SVCs: the "exactly two EL0 `SVC` exceptions" expectation in `docs/guides/first-userspace.md` is a human-read trace property, not a scripted assertion.
- **EL0 evidence.** The completion marker is emitted independently in `task_a` (`bsp-qemu-virt/src/main.rs`, locate `all tasks complete`). Require the already-existing userspace greeting and syscall-exit marker too. This closes the boot/EL0 claim made by this task; new adversarial images and exact SVC counting remain T-067's scope.
- **Release evidence.** Require task exit/completion and forbid the greeting, matching the existing release debug-console contract. T-065 later changes that mechanism to an explicit feature and must update these smoke expectations alongside the build commands; T-067 adds console-dependent adversarial coverage separately.
- The CI QEMU is whatever `ubuntu-latest` packages, likely older than the 11.1.1 used locally; the trace format the script greps is expected to be stable but the first run is the evidence. Record both versions.
- GitHub's branch-protection UI offers a check only after it has run, hence the manual step follows the first run. The job's `name:` is the string to register, not its id.
- **Location re-verification (2026-10-11, HEAD `400dec0`):** `ci.md:55`, `infrastructure.md:82`, `phase-b.md:291`, `ci.yml:65-277` and `smoke.sh:50-57,65,102-119` were re-checked and match; nothing drifted. `ci.md:90` and `infrastructure.md:109,186,209` are additional edit points found while verifying. `phase-b2.md` line numbers shift as banners are added, so locate its items by headline.
- Sequencing: depends on [T-030](T-030-ci-release-profile-gate.md) for release build aliases/security gates and [T-033](T-033-qemu-tooling-smp-and-timeout.md) for the final flags; it must land before any SMP-touching PR.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-11 | Codex (AI agent) | Preflight contract review: see [review artifact](../../reviews/code-reviews/2026-10-11-phase-b2-track1-preflight.md); documentation corrected, implementation not started; ADR-0040 remains Proposed. |
| 2026-10-12 | Codex (AI agent) | Started approved step 6 after T-032 implementation gates and both fresh code/security rounds (`07449f1`). Plan: profile-aware exact serial markers in the existing smoke entry point; required bounded debug/release actual QEMU job using `--int`, matching images and always-uploaded diagnostics; 20 controlled trace cases and three isolated actual kernel mutations with marker-shape validation; local/hosted proof, two fresh code/security rounds, then live required-check registration preserving every setting/app binding. No new ADR or runtime behavior change. Private pre-fix baseline at `6e191e2`: omitting only EL0 scheduler publication leaves completion present, greeting/exit absent, yet old smoke exits 0. Ephemeral evidence `/tmp/tyrne-b21-step6-el0-omission-baseline.{json,log}`. |
| 2026-10-12 | Codex (AI agent) | Local implementation passes fmt, host/kernel clippy, 366 host tests (two ignored HAL doctests), actionlint, default ShellCheck and 59 existing argv cases. Clean matching debug and release QEMU smoke both pass with `--int --timeout 5`; debug image is restored (117 bytes, SHA `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`). The actual negative harness passes 20 synthetic trace cases plus three real private kernel variants, each exit 1 with intended diagnostic and verified marker shape/no unrelated fault. Fault cases are synthetic, not actual CPU-fault injection. All private copies/targets/images use disposable paths. Local QEMU version and logs/results: `/tmp/tyrne-b21-step6/`; the opening 4.7 ms figure is historical emulated boot timing, not this job’s wall time. Initial actionlint caught invalid runner context at job-level env; evidence path initialization moved to a step/GITHUB_ENV and actionlint now passes. Upload action v7.0.2 SHA was verified against its official tag/action source; contents:read retained. Hosted evidence, live check registration, both fresh rounds and final PR remain pending. |
