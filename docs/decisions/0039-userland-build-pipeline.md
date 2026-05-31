# 0039 — Userland build pipeline (B6 — `userland/hello` + `tyrne-user` + raw-flat embed orchestration)

- **Status:** Accepted
- **Date:** 2026-05-31
- **Deciders:** @cemililik

## Context

[ADR-0029](0029-initial-userspace-image-format.md) settled the userspace image **format** (raw flat binary, entry at offset 0) and explicitly **deferred the build orchestration**: its §Decision-outcome "Build pipeline (B6)" row says B6's `userland/hello/` crate is built via `cargo build --target aarch64-unknown-none` + `objcopy -O binary` and embedded via `include_bytes!`, with "the exact path lands with B6." B4 ([T-019](../analysis/tasks/phase-b/T-019-task-loader.md)) shipped a hand-coded placeholder blob (`USERSPACE_IMAGE` at [`bsp-qemu-virt/src/main.rs`](../../bsp-qemu-virt/src/main.rs) — `mov w0, #42; ret`); that is the only userspace image in tree today, and it is loaded-then-discarded by a boot-time loader smoke (never run in EL0).

With B6's three [T-021 carry-forward gates](../roadmap/phases/phase-b.md#t-021-carry-forward-gates-must-close-before-a-real-el0-task-runs) now closed (gate #1 [T-025](../analysis/tasks/phase-b/T-025-user-access-translation.md), gate #2 [T-023](../analysis/tasks/phase-b/T-023-el0-entry-context.md) EL0-context, gate #3 [T-026](../analysis/tasks/phase-b/T-026-current-task-cap-table.md)), the high-half prerequisite ([T-022](../analysis/tasks/phase-b/T-022-high-half-kernel-mapping.md) / [ADR-0033](0033-kernel-high-half-migration.md)) in place, and `task_create_from_image` ([T-024](../analysis/tasks/phase-b/T-024-task-create-from-image.md)) merged, the remaining B6 work is to (1) produce a **real** userspace program from Rust source and embed it, and (2) wire it to run in EL0. This ADR settles the **process** ADR-0029 deferred: **how** the userland crate is built, objcopy'd, and embedded; **where** the `userland/hello` + `tyrne-user` crates live in the workspace; **which** objcopy tool is used; and **where** the userspace base VA lives so the loader and the userspace linker script cannot drift.

The stakes are precedent, not just plumbing. This is the project's **first** cross-target build artifact (a binary compiled for a *different* privilege domain and embedded into the kernel image). Getting the orchestration wrong has three concrete failure modes: a `build.rs` that invokes `cargo` recursively can deadlock on the workspace target-directory lock; an integration that builds the bare-metal userland under host commands (`cargo test`/`cargo build`) breaks the host test suite; and "build magic" hidden in a build script is hard to audit in a security-first kernel. The shape chosen here is the shape every future userland crate (B7+) will follow.

## Decision drivers

- **Host commands stay untouched.** `cargo host-test` / `cargo build` / `cargo host-clippy` (workspace `default-members` = kernel, hal, test-hal) must not attempt to cross-compile the bare-metal userland — exactly as `bsp-qemu-virt` is already excluded from `default-members`.
- **No new Cargo dependency.** [infrastructure.md](../standards/infrastructure.md) §Dependency policy and the [ADR-0029](0029-initial-userspace-image-format.md) toolchain-alignment driver push to avoid `cargo-binutils` (it would trigger the **K3-8 `cargo-vet init`** flag, [phase-b §Flags](../roadmap/phases/phase-b.md#flags-to-resolve-during-b6)). The `llvm-tools-preview` component — which ships `rust-objcopy` — is **already pinned** ([`rust-toolchain.toml`](../../rust-toolchain.toml)).
- **Auditable, no magic.** A security-first kernel ([CLAUDE.md non-negotiable #1](../../CLAUDE.md)) favours an explicit, reviewable orchestrator over implicit build-script side effects that silently shell out to `cargo`.
- **Reviewer / CI ergonomics.** The canonical build + smoke path must stay simple. The repo already has [`tools/smoke.sh`](../../tools/smoke.sh) as the canonical integration entry point.
- **Smallest shape that works for v1.** B6 ships **one** userspace program. The orchestration should not pay for multi-binary generality the project does not yet have (the [ADR-0027](0027-kernel-virtual-memory-layout.md) / [ADR-0035](0035-physical-memory-manager.md) "smallest shape now, defer richness" pattern).
- **Single source-of-truth for the userspace base VA.** ADR-0029 §Consequences flagged "linker-script awareness leaks into the loader … spec drift potential." The base VA (`0x0080_0000`) is read by the kernel loader *and* by the userspace linker script; a divergence is a silent, hard-to-debug wrong-VA load.
- **Scales to B7+ without a rewrite.** The chosen shape should have a named, additive upgrade path when a second userspace program lands.

## Considered options

1. **`tools/build-userland.sh` pre-build step** — an explicit shell script (peer to `tools/smoke.sh`) runs `cargo build` for the userland crate + `rust-objcopy -O binary`, writing a git-ignored `.bin`; the BSP `build.rs` `include_bytes!`s it (with a clear error if absent); `tools/smoke.sh` runs the script before the kernel build.
2. **BSP `build.rs` with a separate `CARGO_TARGET_DIR`** — the BSP build script invokes `cargo build -p tyrne-userland-hello` into an isolated target dir (the standard nested-cargo lock mitigation), then objcopy + embed; `cargo kernel-build` "just works" with no pre-step.
3. **`cargo xtask` orchestrator** — a workspace `xtask` crate with a `build-userland` subcommand; `cargo` aliases chain it before the kernel build.
4. **Committed pre-built `.bin`** — check the objcopy output into the repo; the BSP `build.rs` only `include_bytes!`s it; a `tools/` script regenerates it on source change.

## Decision outcome

Chosen option: **Option 1 — `tools/build-userland.sh`**, with these bundled sub-decisions:

- **Crates.** Add two workspace members under a new `userland/` directory: `userland/hello/` (package `tyrne-userland-hello`, `#![no_std] #![no_main]`, the raw-flat program) and `userland/tyrne-user/` (package `tyrne-user`, `#![no_std]` library of **safe** syscall wrappers `console_write` / `task_exit`, which `hello` depends on). Both are added to `members` and **excluded from `default-members`** (so host commands skip them, mirroring `bsp-qemu-virt`). `tyrne-` package-name prefix per [ADR-0006](0006-workspace-layout.md).
- **objcopy.** `rust-objcopy -O binary` from the already-pinned `llvm-tools-preview` component — **no Cargo dependency**, so the K3-8 `cargo-vet` flag stays unfired. The script resolves the binary via the active toolchain (`rustc --print sysroot` + the `llvm-tools` bin dir) and fails with a clear diagnostic if the component is missing.
- **Base-VA source-of-truth.** A single `pub const USERSPACE_IMAGE_BASE_VA` lives Rust-side (read by the BSP loader call site and any kernel consumer); the userspace linker script **restates** the same literal with a `keep-in-sync-with` comment, because a linker script cannot import a Rust const. A `ld --defsym`-from-const upgrade is named for full drift-elimination when it earns its keep.
- **Artifact.** The `.bin` is **git-ignored** (regenerated from source; no binary blob in the repo — the Rust source stays the auditable truth). The BSP `build.rs` adds `rerun-if-changed` on it and `include_bytes!`s a stable path; if the file is absent it emits a `panic!` naming `tools/build-userland.sh`. `tools/smoke.sh` runs the script before `cargo kernel-build`, so the canonical path is unchanged.

Option 1 wins on the four most load-bearing drivers: it keeps host commands untouched (the userland is never in a host build set), adds no Cargo dependency, is fully auditable (a shell script a reviewer reads at a glance — the same shape as `tools/smoke.sh`), and is the smallest shape for one binary (no new crate beyond the two the milestone requires). It avoids the nested-cargo deadlock entirely (the script runs `cargo` at top level, not inside a `build.rs`) and commits no binary blob. Its cost — a build step before a bare `cargo kernel-build` — is mitigated by the build script's clear error and by `tools/smoke.sh` chaining it, and the **`cargo xtask` pattern (Option 3) is the named, additive upgrade** when B7+ introduces multiple userspace programs (a shell `for`-loop or an `xtask build-userland` subcommand drops in without disturbing the kernel build).

### Simulation

**Not applicable** — this ADR settles a single-shape process / build-orchestration decision; there is no runtime state machine to simulate. (The EL0↔EL1 round-trip the resulting image exercises is the subject of [T-028](../analysis/tasks/phase-b/T-028-el0-userspace-wireup.md)'s wire-up, walked through [ADR-0030 §Simulation](0030-syscall-abi.md#simulation) and [ADR-0037](0037-el0-entry-context.md); this ADR's subject is how the bytes are produced, not how they run.)

### Dependency chain

For this decision to be fully in effect:

```text
1. Raw-flat image format (entry at offset 0, USER|EXECUTE image)        — ADR-0029 (Accepted)
2. rust-objcopy via the llvm-tools-preview component                    — rust-toolchain.toml (pinned, present)
3. Loader + LoadedImage + task_create_from_image + the syscall gates    — T-019 / T-024 / T-025 / T-026 (Done / merged)
4. EL0 entry context + enter-EL0 path + add_user_task                   — T-023 / ADR-0037 (Done)
5. The build pipeline + userland/hello + tyrne-user crates              — T-027 (Draft, opens with this ADR)
6. EL0 wire-up + the +0x400 round-trip QEMU smoke                       — T-028 (Draft, opens with this ADR)
```

T-027 closes steps 5 (the build pipeline + the two crates + the embedded real image, replacing the placeholder; dormant — not yet run). T-028 closes step 6 (load → `task_create_from_image` → `add_user_task` → the scheduler runs the task in EL0; the real round-trip) and triggers the explicit EL0-boundary security review the [T-026 Definition of done](../analysis/tasks/phase-b/T-026-current-task-cap-table.md) carries forward. Both slots are opened at `Draft` in the same commit as this ADR per [ADR-0025 §Rule 1](0025-adr-governance-amendments.md).

## Consequences

### Positive

- **No new dependency, no new attack surface in the build.** `rust-objcopy` is already in the pinned toolchain; the `cargo-vet` K3-8 flag stays unfired; the orchestrator is hand-written shell + Rust the project owns end-to-end.
- **Host suite is provably unaffected.** The userland crates sit outside `default-members`; `cargo host-test` / `cargo build` / `cargo host-clippy` never touch them, exactly as `bsp-qemu-virt` is excluded today — a pattern already proven in tree.
- **Auditable.** The build order is a short shell script in `tools/`, reviewed like any source file; the embedded image is reproduced from committed Rust source, so the byte stream's provenance is the crate, not an opaque blob.
- **No nested-cargo deadlock.** The script invokes `cargo` at top level (not from inside a `build.rs`), so there is no workspace target-directory lock contention or recursive-cargo fragility.

### Negative

- **A bare `cargo kernel-build` needs the `.bin` present first.** On a fresh checkout, `cargo kernel-build` alone fails until `tools/build-userland.sh` has run. *Mitigation:* the BSP `build.rs` emits a `panic!` that names the script; `tools/smoke.sh` (the canonical **local** entry point) chains the script before the kernel build; the dev loop is `tools/build-userland.sh && cargo kernel-build` or simply `tools/smoke.sh`. (CI is a separate concern — see the next item.) We accept this small ergonomic cost in exchange for no build-script magic and no committed binary.
- **The base VA is stated in two places** (the Rust const and the userspace linker script), because LD cannot import a Rust const. *Mitigation:* a `keep-in-sync-with` comment on the linker-script line, the same discipline ADR-0029 already imposes ("linker-script awareness leaks into the loader"); the `ld --defsym`-from-const path is named for when full drift-elimination earns its keep (B7+ multi-program / multi-BSP).
- **The `.bin` is git-ignored, so CI must build it — and the existing CI `kernel-build` job will break without it.** CI today runs `cargo kernel-build` (and `kernel-clippy`) directly on a clean checkout ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)); post-T-027, that job hits the BSP `build.rs` missing-`.bin` `panic!`, so **T-027 must add the userland build step to the CI workflow ahead of the `kernel-build` / `kernel-clippy` jobs** (and the maintainer-launched `tools/smoke.sh` already chains it locally). *Mitigation:* one step in the workflow; standard for embedded projects. The alternative (committing the blob) trades it for a binary in git history and a freshness-drift check, which we reject. (The QEMU-smoke-in-CI regression gate itself remains the conditionally-deferred flag K3-7 — [phase-b §Flags](../roadmap/phases/phase-b.md#flags-to-resolve-during-b6); no QEMU-smoke CI job exists today.)

### Neutral

- **`cargo xtask` is the named scaling path, not a rejection.** When a second userspace program lands (B7+), the shell script either grows a loop or is replaced by an `xtask build-userland` subcommand; nothing in T-027's shape blocks that, and the kernel build is unaffected either way.
- **Reversible.** Switching to the `build.rs`-auto (Option 2) or committed-`.bin` (Option 4) shape later is a localized change to `build.rs` + `tools/`, touching no kernel or userland source.
- **The userland inherits the `[target.aarch64-unknown-none]` rustflags** (`panic=abort`, `force-frame-pointers`). Both are correct for a userspace blob (no unwinder; frame pointers are negligible overhead for a ~100-byte program); a future performance-sensitive userland can add a crate-local `.cargo/config.toml` override.

## Pros and cons of the options

### Option 1 — `tools/build-userland.sh` pre-build step (chosen)

- **Pro:** Smallest shape for one binary; no new crate; explicit + auditable (peer to `tools/smoke.sh`); no nested-cargo; no Cargo dep; no committed binary; host commands untouched.
- **Pro:** `xtask` remains a clean additive upgrade for B7+ multi-binary.
- **Con:** A bare `cargo kernel-build` needs the script run first (mitigated by a clear `build.rs` error + `tools/smoke.sh` chaining).
- **Con:** Shell is less portable than Rust (the project's dev/CI hosts are Unix; `tools/smoke.sh` already assumes this).

### Option 2 — BSP `build.rs` with a separate `CARGO_TARGET_DIR`

- **Pro:** `cargo kernel-build` "just works" with no pre-step; the standard nested-cargo mitigation (isolated target dir) is well-trodden (bootimage, embedded Rust).
- **Con:** A build script that shells out to `cargo` is exactly the implicit "build magic" an auditable kernel should avoid; the embedded artifact is hidden under `target/**/OUT_DIR` (reviewers cannot inspect it without rebuilding); adds 5–15 s to every kernel build; couples to Cargo internals.

### Option 3 — `cargo xtask` orchestrator

- **Pro:** Explicit, scales cleanly to multiple userspace programs; idiomatic in the Rust ecosystem; `cargo` alias keeps the one-liner.
- **Con:** Adds a whole workspace crate for what B6 needs once — more than the "smallest shape" the single-binary milestone justifies; a cargo alias cannot itself chain a shell step, so the orchestration still needs the alias wired carefully. Reserved as the **named B7+ upgrade**, not the v1 choice.

### Option 4 — Committed pre-built `.bin`

- **Pro:** `cargo kernel-build` is truly standalone (the blob is in tree); reviewers can disassemble the committed artifact.
- **Con:** Puts a binary blob in git history (drift risk if source changes but the blob is not regenerated; a freshness check becomes a CI burden); a security review of a committed binary means trusting/disassembling it rather than reading the source it came from — the opposite of the "Rust source is the auditable truth" posture.

## References

- [ADR-0029 — Initial userspace image format](0029-initial-userspace-image-format.md) — the raw-flat **format** this ADR builds the pipeline for; its §Decision-outcome deferred the build orchestration to B6.
- [ADR-0006 — Workspace layout](0006-workspace-layout.md) — the `members` / `default-members` split and the `tyrne-` package-name prefix this ADR extends to the userland crates.
- [ADR-0027 — Kernel virtual memory layout](0027-kernel-virtual-memory-layout.md) — the `TTBR0_EL1` userspace VA range the base VA (`0x0080_0000`) sits within.
- [rust-toolchain.toml](../../rust-toolchain.toml) — the pinned `llvm-tools-preview` component providing `rust-objcopy`.
- [tools/smoke.sh](../../tools/smoke.sh) — the canonical integration entry point the build script chains into.
- [`cargo-xtask` pattern (matklad)](https://github.com/matklad/cargo-xtask) — the named B7+ multi-binary upgrade path.
- [The `embedded-bootimage` / blog_os build-step pattern](https://os.phil-opp.com/) — prior art for objcopy-and-embed orchestration of a bare-metal artifact.
