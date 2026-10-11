# CI: what runs, where, and when

This guide describes the GitHub Actions pipeline configured in [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml). It is the first external gate beyond self-review and agent-review. When the CI is red, the commit is not mergeable, even if local checks passed.

## Jobs

| Job | Toolchain | Wall time (expected) | Fails on |
|-----|-----------|----------------------|----------|
| `lint-and-host-test` | pinned nightly + `rustfmt` + `clippy` | ~2 min | `cargo fmt --check` diff, clippy warning, debug/release host test failure, absent release-only syscall tests, tooling ShellCheck finding, expected-failure probe mismatch or stubbed QEMU argument regression |
| `kernel-build` | pinned nightly + `aarch64-unknown-none` + `clippy` | ~1 min | Debug/release kernel or debug perf-bench build error, kernel/userland/perf-bench clippy warning or expected-failure probe mismatch |
| `qemu-smoke` | pinned nightly + `llvm-tools-preview` + QEMU | ~2–4 min; 10 min bound | Missing debug/release EL0 markers, release greeting, panic/CPU-fault trace, build failure or expected-failure probe mismatch |
| `arm64-host-check` | pinned nightly + `clippy` + `miri`, `ubuntu-24.04-arm` | 101 s first hosted run; 15 min bound | Native workspace check/clippy/test/Miri failure, wrong host or arch-only regression probe mismatch |
| `host-stable-check` | stable (no extra components) | ~2 min | host crates failing to build or test on stable Rust |
| `miri` | pinned nightly + `miri` component | ~10–15 min | Any Stacked Borrows violation in `cargo +nightly miri test --workspace --exclude tyrne-bsp-qemu-virt` |
| `coverage` | pinned nightly + `llvm-tools-preview` + `cargo-llvm-cov` | ~3–5 min | **Never** (informational only, `continue-on-error: true`) |

The ARM job runs on `ubuntu-24.04-arm`; the remaining jobs use `ubuntu-latest` (x86_64). Every cache key and restore prefix includes `runner.os` and `runner.arch`, plus toolchain and lockfile identity, so ARM cannot restore x86_64 build artifacts.

### Why do the kernel jobs run on the pinned nightly, not stable?

The kernel needs nightly to build (inline asm intrinsics / lang items — see `rust-toolchain.toml` and ADR-0002). `rust-toolchain.toml` pins `nightly-2026-01-15` at the repo root, and rustup's override precedence means that file selects the pinned nightly for **every** in-repo `cargo` invocation regardless of `rustup default`. So `lint-and-host-test`, `kernel-build`, `qemu-smoke`, `arm64-host-check`, `miri`, and `coverage` all select the pin explicitly (`cargo +$NIGHTLY_PIN …`) — the same toolchain a contributor's local `cargo` uses.

### What does `host-stable-check` give us, then?

A genuine "the host-buildable crates compile and pass tests on **stable** Rust" signal. It runs `cargo +stable build` and `cargo +stable host-test` over the workspace `default-members` (kernel, hal, test-hal) — the bare-metal BSP is excluded because it needs nightly. The `+stable` prefix bypasses the `rust-toolchain.toml` override so this job exercises stable for real. It deliberately does **not** run clippy/fmt with `-D warnings`: `clippy::pedantic` is `warn` workspace-wide and stable is a rolling toolchain, so a future stable pedantic lint could redden the gate with no code change of ours — lint/format enforcement lives only on the pinned-nightly jobs. If a host crate ever grows a `#![feature(...)]` it does not strictly need, this job is the one that goes red on stable.

### Why an ARM64 host job?

An arch-only `target_arch = "aarch64"` cfg accidentally includes bare-metal panic handlers and entry points on an ARM host. Cross-building on x86 cannot expose that host hazard. `arm64-host-check` verifies the machine is `aarch64` and Rust targets `aarch64-unknown-linux-gnu`, then runs all four native commands below with the pinned nightly. Only the BSP is excluded; both userland crates participate. Miri is mandatory alongside native compilation and execution.

```sh
cargo check --workspace --exclude tyrne-bsp-qemu-virt
cargo clippy --workspace --exclude tyrne-bsp-qemu-virt --all-targets -- -D warnings
cargo test --workspace --exclude tyrne-bsp-qemu-virt
cargo miri setup
cargo miri test --workspace --exclude tyrne-bsp-qemu-virt
tools/test-ci-gates.sh --arm-host
```

The ARM-only probe restores hello's six arch-only predicates in a temporary copy, then requires the exact workspace clippy command to reject duplicate `panic_impl`. A successful probe means the compiler rejected the regression, not that Miri failed in production. It refuses non-ARM Rust hosts, uses a private Cargo target and removes the temporary copy on exit. [T-036](../analysis/tasks/phase-b2/T-036-ci-arm64-host-check-job.md) separates Apple Silicon, hosted Linux ARM, final PR and post-merge evidence. Its exact display name is `ARM64 host check + clippy + tests + Miri (nightly)`; live registration completed on 2026-10-12 after hosted green and both fresh review rounds.

### How the action versions are pinned

Every third-party GitHub Action is pinned to a full 40-character commit SHA with the human-readable version in a trailing comment (e.g. `actions/checkout@11bd719… # v4.2.2`). Tags are mutable; SHAs are not. This applies the same anti-silent-drift discipline used for `NIGHTLY_PIN` and `cargo-llvm-cov` to the actions that wrap them — `taiki-e/install-action` in particular downloads and executes a prebuilt binary, so a tag repoint would be arbitrary code execution in CI. See [`docs/standards/infrastructure.md`](../standards/infrastructure.md) §"Supply-chain security" → "GitHub Actions pinning" for the refresh path.

## Triggers

- **Every push** to `main` or `development`.
- **Every PR** targeting `main` or `development`.

Concurrent runs on the same branch cancel each other — only the latest commit's verdict matters.

## Philosophy

The CI matrix mirrors what a contributor should run locally before opening a PR:

| Local command | CI job |
|---|---|
| `cargo fmt --all -- --check` | `lint-and-host-test` |
| `cargo host-clippy` | `lint-and-host-test` |
| `tools/test-ci-gates.sh --hal` (panic-family rejection in a disposable copy) | `lint-and-host-test`, after host clippy |
| `cargo host-test` | `lint-and-host-test` |
| `cargo test --release` | `lint-and-host-test` |
| `tools/check-release-tests.sh` (both named release tests must pass) | `lint-and-host-test` |
| `tools/test-ci-gates.sh --release` (profile-flip rejection in a disposable copy) | `lint-and-host-test` |
| `shellcheck --version` + `shellcheck tools/*.sh` | `lint-and-host-test` |
| `tools/test-ci-gates.sh --shell` (expected failure in a disposable copy) | `lint-and-host-test` |
| `tools/test-qemu-tooling.sh` (stubbed QEMU arguments) | `lint-and-host-test` |
| `cargo kernel-build` | `kernel-build` |
| `cargo kernel-clippy` | `kernel-build` |
| `tools/test-ci-gates.sh --bsp` (panic-family rejection in a disposable copy) | `kernel-build`, after debug kernel clippy |
| `cargo clippy -p tyrne-user -p tyrne-userland-hello --target aarch64-unknown-none -- -D warnings` | `kernel-build`, after debug userland build |
| `tools/test-ci-gates.sh --userland` (expected failure in a disposable copy) | `kernel-build` |
| `tools/build-userland.sh --release` + `cargo kernel-build-release` | `kernel-build`, after debug steps |
| `cargo clippy --release --target aarch64-unknown-none -p tyrne-bsp-qemu-virt -- -D warnings` | `kernel-build`, after release image build |
| `tools/build-userland.sh` + `cargo build --target aarch64-unknown-none -p tyrne-bsp-qemu-virt --features perf-bench` | `kernel-build`, restore debug image immediately before perf build |
| `cargo clippy --target aarch64-unknown-none -p tyrne-bsp-qemu-virt --features perf-bench -- -D warnings` | `kernel-build`, last variant lint |
| `tools/smoke.sh --int` + `tools/smoke.sh --release --int` (matching images) | `qemu-smoke` |
| `tools/test-smoke-gates.sh` (synthetic traces) | `lint-and-host-test` and `qemu-smoke` |
| `tools/test-smoke-gates.sh --real` (also private kernel variants) | `qemu-smoke` |
| Native workspace check/clippy/test/Miri and `tools/test-ci-gates.sh --arm-host` (commands above) | `arm64-host-check` |
| `cargo +stable build` + `cargo +stable host-test` (host crates) | `host-stable-check` |
| `cargo +nightly miri test --workspace --exclude tyrne-bsp-qemu-virt` | `miri` |
| `cargo llvm-cov --workspace --exclude tyrne-bsp-qemu-virt --summary-only` | `coverage` |

If you pass these locally, CI should pass too. Your local `cargo` runs the pinned nightly automatically (the `rust-toolchain.toml` override), which is the same toolchain the kernel CI jobs use — so a local/CI divergence on those jobs is rare. If you see one, confirm your pinned nightly is installed (`rustup toolchain list` should show `nightly-2026-01-15`); rustup installs it on first use, but a stale or partial install can drift. For the `host-stable-check` job, reproduce with the explicit prefix: `cargo +stable build` (install stable first with `rustup toolchain install stable` if needed).

### Lint and release regression probes

The real ShellCheck and bare-metal userland clippy steps must pass first. `tools/test-ci-gates.sh` then copies the current tracked worktree into a temporary directory, uses a separate Cargo target directory, injects a shell quoting error or a clone-on-Copy lint, and asserts that the exact matching command fails with its expected diagnostic. A passing probe means the deliberate regression was rejected; it is not a red production workflow. The copy is removed on exit, with no source, branch or shared image change. ShellCheck's installed version is printed in CI; measured local and hosted versions are recorded in [T-031](../analysis/tasks/phase-b2/T-031-ci-userland-clippy-and-shellcheck.md).

The release guard runs `cargo test --release -p tyrne-kernel --lib -- console_write_is_absent_in_release_builds console_write_number_is_bad_syscall_in_release_build` and requires both exact test names to pass plus a two-pass summary. Cargo's success alone is insufficient: setting release `debug-assertions = true` compiles both tests out, returns success with zero tests and exposes `console_write`. The `--release` probe makes that profile change only in its disposable copy and requires the guard to reject it. [T-030](../analysis/tasks/phase-b2/T-030-ci-release-profile-gate.md) records local and hosted evidence separately.

The HAL and BSP deny `clippy::panic`, `clippy::unwrap_used` and `clippy::expect_used` at their crate roots. The `--hal` and `--bsp` probes inject a non-test `None` unwrap outside any allowed function, then require the exact `cargo host-clippy` / `cargo kernel-clippy` command to fail with `clippy::unwrap_used`. The BSP probe first builds its matching debug userland image inside the disposable copy; it never overwrites the checkout's shared image. Existing boot/demo/benchmark invariants and deliberate fatal aborts have narrow function-scoped exceptions with reasons, catalogued in [T-032](../analysis/tasks/phase-b2/T-032-panic-family-denies-hal-bsp.md). These three lints do not prohibit `assert!` or prove a panic-free kernel.

The kernel job builds debug first, then release with its matching userland image, then restores the debug userland immediately before debug perf-bench build/lint. The separate `qemu-smoke` job boots matching debug and release ELFs; compilation alone does not establish guest behavior.

### Guest smoke and diagnostic artifacts

`qemu-smoke` (display name `QEMU debug + release smoke (nightly)`) builds each matching userland/kernel profile explicitly before booting it with `--int`. Debug requires exact serial lines `hello from userspace`, `tyrne: userspace task exited` and `tyrne: all tasks complete`. Release requires exit/completion and forbids any userspace greeting. Both reject panic/CPU-fault patterns. Job-scoped explicit Bash enables pipefail so `tee` cannot turn a failed production smoke into a green step. A separate synthetic completion-only probe deliberately fails the actual smoke entry point through the inherited CI log pipeline; it requires nonzero pipeline status plus the real missing-exit diagnostic, and retains its output artifact. Removing pipefail makes this guard fail. An explicit ELF skips compilation; pass `--release` for release expectations. These are marker checks, not an exact SVC count or proof of exit code zero.

```sh
tools/build-userland.sh
cargo kernel-build
tools/smoke.sh --int target/aarch64-unknown-none/debug/tyrne-bsp-qemu-virt
tools/build-userland.sh --release
cargo kernel-build-release
tools/smoke.sh --release --int target/aarch64-unknown-none/release/tyrne-bsp-qemu-virt
tools/build-userland.sh
```

The 20 synthetic trace fixtures cover both positive profiles, each missing required marker, all six panic/fault patterns in both profiles and the forbidden release greeting. With `--real`, three additional disposable kernels omit EL0 publication, omit completion or add a release greeting. Each actual negative must have the intended marker shape, no unrelated fault and the expected smoke rejection. The host-only harness requires Python 3; actual variants additionally need the same Rust/LLVM/QEMU prerequisites as the production guest. It copies current tracked source, uses private build/image paths and removes the copy on exit; no broken source commit or branch is needed.

```sh
tools/test-smoke-gates.sh
tools/test-smoke-gates.sh --real --artifact-dir /tmp/tyrne-smoke-review-evidence
```

The artifact directory must be new; existing paths are refused. `results.json` binds probes to HEAD, a dirty-tracked-worktree flag and the smoke-script hash, and labels synthetic fixtures separately from actual private kernel traces. CI uploads `qemu-smoke-<sha>-<attempt>` on success and failure, retaining it for 14 days. It contains production PID-suffixed raw traces, combined output, probe traces/results/build logs, source/run identity, QEMU/Rust versions and diagnostic wall time. On early failures it contains the evidence available so far. Artifact upload uses runtime credentials with `contents: read`; no token permission is widened.

## Why is `tyrne-bsp-qemu-virt` excluded from Miri and coverage?

The BSP is a bare-metal `no_std` + `no_main` binary whose panic handler conflicts with `std`'s `panic_impl` lang item when built for the host target (which Miri and llvm-cov both require). The `qemu-smoke` job exercises the BSP under actual single-core QEMU. The completed demo spins, so QEMU is stopped by a watchdog; the smoke verdict comes from the trace, not the expected timeout exit status.

## When does the coverage job start gating?

Today `coverage` is informational: `continue-on-error: true` in the workflow. After T-011 closes (which raises `sched/mod.rs` past 90 % and the workspace past 96 %), the plan is to flip this job to enforce a floor. The floor should be slightly below the measured baseline so regressions trip the gate but normal churn does not.

## Adding a new check

1. Add a job to [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).
2. Keep the fast-lane job order stable — `lint-and-host-test` must remain first so red PRs fail quickly.
3. If the check requires a nightly feature, put it in its own job (not folded into `lint-and-host-test`).
4. Update this guide's table.

## Nightly pinning

Miri and cargo-llvm-cov use a **pinned** nightly declared via the `NIGHTLY_PIN` env var at the top of [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml). Rolling nightly means that a miri or `llvm-tools` regression on the public nightly channel breaks CI without any commit of ours being the cause; pinning isolates us from that.

cargo-llvm-cov itself is also pinned — installed via [`taiki-e/install-action`](https://github.com/taiki-e/install-action) which downloads a prebuilt binary rather than compiling from source. The version is in the workflow as `tool: cargo-llvm-cov@<x.y.z>` (`0.6.16` at the time of writing). Pinning the tool prevents an upstream release from silently changing what "coverage" reports.

Current pins:
- `NIGHTLY_PIN = nightly-2026-01-15` (set 2026-04-23 when R6 landed).
- `cargo-llvm-cov 0.6.16` (set 2026-04-28; see `coverage` job in `ci.yml`).

To bump either pin:

1. Open an issue titled "Bump &lt;pin&gt; to &lt;new-version&gt;" stating the reason (new Miri check we want, a compiler feature we need, a cargo-llvm-cov bug fix, a security advisory, routine refresh).
2. Update the `NIGHTLY_PIN` env var or the `tool: cargo-llvm-cov@…` line in `.github/workflows/ci.yml` and the "Current pins" list above.
3. Run `cargo +nightly-YYYY-MM-DD miri test --workspace --exclude tyrne-bsp-qemu-virt` and `cargo +nightly-YYYY-MM-DD llvm-cov --workspace --exclude tyrne-bsp-qemu-virt --summary-only` locally; make sure both are green on the new pin.
4. Land the pin bump in its own commit with `Refs:` to the issue. The two pins can be bumped together or independently.

## Branch protection and `continue-on-error`

The `coverage` job is marked `continue-on-error: true`. GitHub's UI renders this as a **neutral / yellow** verdict rather than green or red. Be deliberate when configuring branch-protection rules:

- **Do not add `coverage` to the required-checks list** while it is informational; the neutral result does not satisfy `required == passing`, so every push would be blocked even when coverage is fine.
- **Do add the six real gates** to required checks. GitHub matches each job's display **name**, not its id, so add these exact strings: `fmt + clippy + host tests (nightly)`, `aarch64-unknown-none kernel build (nightly)`, `host crates on stable`, `miri (Stacked Borrows)`, `QEMU debug + release smoke (nightly)`, and `ARM64 host check + clippy + tests + Miri (nightly)`. The ARM check was registered after remote green and both fresh rounds on 2026-10-12, with full-policy read-back in [T-036](../analysis/tasks/phase-b2/T-036-ci-arm64-host-check-job.md). The smoke check was registered on 2026-10-12 after corrected remote green and both fresh review rounds; [T-034](../analysis/tasks/phase-b2/T-034-ci-qemu-smoke-job.md) records live read-back evidence.
- When coverage flips from informational to enforcing (planned post-T-011), remove `continue-on-error: true` first, confirm a full run is green, then add the job to branch-protection.
