# CI: what runs, where, and when

This guide describes the GitHub Actions pipeline configured in [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml). It is the first external gate beyond self-review and agent-review. When the CI is red, the commit is not mergeable, even if local checks passed.

## Jobs

| Job | Toolchain | Wall time (expected) | Fails on |
|-----|-----------|----------------------|----------|
| `lint-and-host-test` | pinned nightly + `rustfmt` + `clippy` | ~2 min | `cargo fmt --check` diff, any clippy warning, any failing host test |
| `kernel-build` | pinned nightly + `aarch64-unknown-none` + `clippy` | ~1 min | `cargo kernel-build` error, any kernel-clippy warning |
| `host-stable-check` | stable + `rustfmt` + `clippy` | ~2 min | host crates failing to fmt/clippy/build/test on stable Rust |
| `miri` | pinned nightly + `miri` component | ~10–15 min | Any Stacked Borrows violation in `cargo +nightly miri test --workspace --exclude tyrne-bsp-qemu-virt` |
| `coverage` | pinned nightly + `llvm-tools-preview` + `cargo-llvm-cov` | ~3–5 min | **Never** (informational only, `continue-on-error: true`) |

All jobs run on `ubuntu-latest`. Each caches cargo registry + build artefacts keyed by `Cargo.lock` hash, so warm runs are far faster than first runs.

### Why do the kernel jobs run on the pinned nightly, not stable?

The kernel needs nightly to build (inline asm intrinsics / lang items — see `rust-toolchain.toml` and ADR-0002). `rust-toolchain.toml` pins `nightly-2026-01-15` at the repo root, and rustup's override precedence means that file selects the pinned nightly for **every** in-repo `cargo` invocation regardless of `rustup default`. So `lint-and-host-test`, `kernel-build`, `miri`, and `coverage` all select the pin explicitly (`cargo +$NIGHTLY_PIN …`) — the same toolchain a contributor's local `cargo` uses.

### What does `host-stable-check` give us, then?

A genuine "the host-buildable crates compile, lint, and test on **stable** Rust" signal. It runs `cargo +stable fmt/clippy/build/test` over the workspace `default-members` (kernel, hal, test-hal) — the bare-metal BSP is excluded because it needs nightly. The `+stable` prefix bypasses the `rust-toolchain.toml` override so this job exercises stable for real. If a host crate ever grows a `#![feature(...)]` it does not strictly need, this job is the one that goes red on stable.

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
| `cargo fmt --all -- --check` | `lint-and-host-test` (step 1) |
| `cargo host-clippy` | `lint-and-host-test` (step 2) |
| `cargo host-test` | `lint-and-host-test` (step 3) |
| `cargo kernel-build` | `kernel-build` |
| `cargo kernel-clippy` | `kernel-build` |
| `cargo +stable fmt/clippy/build/test` (host crates) | `host-stable-check` |
| `cargo +nightly miri test --workspace --exclude tyrne-bsp-qemu-virt` | `miri` |
| `cargo llvm-cov --workspace --exclude tyrne-bsp-qemu-virt --summary-only` | `coverage` |

If you pass these locally, CI should pass too. Your local `cargo` runs the pinned nightly automatically (the `rust-toolchain.toml` override), which is the same toolchain the kernel CI jobs use — so a local/CI divergence on those jobs is rare. If you see one, confirm your pinned nightly is installed (`rustup toolchain list` should show `nightly-2026-01-15`); rustup installs it on first use, but a stale or partial install can drift. For the `host-stable-check` job, reproduce with the explicit prefix: `cargo +stable build` (install stable first with `rustup toolchain install stable` if needed).

## Why is `tyrne-bsp-qemu-virt` excluded from Miri and coverage?

The BSP is a bare-metal `no_std` + `no_main` binary whose panic handler conflicts with `std`'s `panic_impl` lang item when built for the host target (which Miri and llvm-cov both require). BSP code is exercised indirectly via the QEMU smoke test; automating that runs under CI is a T-009 follow-up (the timer init task) — once the kernel can produce a finish-signal, QEMU can exit non-zero on mismatch and CI can assert the trace.

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
- **Do add `lint-and-host-test`, `kernel-build`, `host-stable-check`, and `miri`** to required checks — those four are the real gates.
- When coverage flips from informational to enforcing (planned post-T-011), remove `continue-on-error: true` first, confirm a full run is green, then add the job to branch-protection.
