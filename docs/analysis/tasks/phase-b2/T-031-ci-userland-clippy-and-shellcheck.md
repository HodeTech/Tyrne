# T-031 — Clippy the userland crates and shellcheck the tooling scripts in CI

- **Phase:** B.2
- **Milestone:** Track B.2-1
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** none
- **ADRs required:** none

---

## User story

As the maintainer of a project whose rule 2 is "every `unsafe` block is justified and checked", I want CI to lint the userland crates that hold the EL0 syscall-trap asm and to shellcheck the `tools/` scripts, so that the only code with zero lint coverage stops being unchecked by construction.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). `tyrne-user` and `tyrne-userland-hello` are workspace members but not `default-members` (`Cargo.toml:23-27`), so `host-clippy` skips them (`.cargo/config.toml:44-45`); `kernel-clippy` is `-p tyrne-bsp-qemu-virt` only (`.cargo/config.toml:32-34`), and the BSP does not depend on the userland crates (`bsp-qemu-virt/Cargo.toml:15-17`; the image is embedded as a prebuilt `hello.bin`). `tools/build-userland.sh:30-34` only runs `cargo build`. So the raw `svc #0` shims in `userland/tyrne-user/src/lib.rs:92-141` are never clippy-checked on any target. Separately no CI step lints shell, although `tools/smoke.sh:53,55` already carry `# shellcheck disable=SC2086` directives.

This task covers two items of `phase-b2.md` Track B.2-1 (line numbers as of the opening snapshot; locate by headline): the HIGH "Userland crates carrying the raw unsafe syscall-trap asm are never clippy-checked in CI" (line 30) and the LOW "No shellcheck ... runs in CI" (line 54). The Polish items that restate them (userland clippy gap, shellcheck the `tools/` scripts) are closed by the same work.

## Acceptance criteria

- [ ] After `tools/build-userland.sh`, `cargo clippy -p tyrne-user -p tyrne-userland-hello --target aarch64-unknown-none -- -D warnings` exits 0 locally; its first-run findings are listed in the review history and each is fixed or given a scoped `#[allow(...)]` with a `reason`.
- [ ] The `kernel-build` job runs that exact command as its own step, placed after the `tools/build-userland.sh` step (next to `cargo kernel-clippy`).
- [ ] `shellcheck tools/*.sh` exits 0 locally at default severity (baseline in Design notes), with each remaining suppression a scoped `# shellcheck disable=SCnnnn` carrying a reason comment and no file-wide disable.
- [ ] CI runs `shellcheck tools/*.sh` as a step in the fast lane (`lint-and-host-test`) or a dedicated job, prints `shellcheck --version`, and is green; the CI shellcheck version is recorded in the review history.
- [ ] Negative tests, recorded in the review history: on a scratch branch (never merged), a clippy-triggering change in `userland/tyrne-user/src/lib.rs` and an unquoted variable in a `tools/*.sh` script each turn the matching CI step red.
- [ ] Documentation: `docs/guides/ci.md` (job table "Fails on" cells and the local-command table) and `docs/standards/infrastructure.md` ("Required gates" bullets) name the userland clippy command and the shellcheck step; the `ci.yml` header comment (lines 7-9) is still accurate.

## Out of scope

- Fixing the host-target `cfg` gate in the userland crates: [T-037](T-037-userland-bare-metal-cfg-gate.md).
- `--smp`/`--timeout` changes to `tools/run-qemu.sh` and `tools/smoke.sh`: [T-033](T-033-qemu-tooling-smp-and-timeout.md) (whichever task lands second re-runs shellcheck).
- The `console_write` clobber fix in the same file: [T-038](T-038-console-write-x2-clobber.md); API polish: [T-064](T-064-tyrne-user-api-polish.md).
- Linting the userland crates for the host target (they are bare-metal-only by design).

## Approach

Userland: add the clippy command to the `kernel-build` job, which already installs the pinned nightly with `clippy` and the `aarch64-unknown-none` target (`ci.yml:116-123`); no new job and no new required-check name. An optional `userland-clippy` alias in `.cargo/config.toml` (mirroring `kernel-clippy`) keeps local and CI invocations identical; decide while implementing and record it. Shell: add `shellcheck tools/*.sh` to the fast lane (`ubuntu-latest` ships shellcheck, per the plan item). Run both commands locally first, record the output, fix real findings, and suppress only demonstrated false positives with a scoped directive and a reason, following the style already used at `tools/smoke.sh:53`.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean if any kernel, hal or test-hal source changes (not expected).
- [ ] `tools/smoke.sh --int` PASS if any BSP, kernel or userland source changes (possible via clippy fixes in `tyrne-user`/`hello`); also PASS after any `tools/*.sh` edit that touches `smoke.sh`.
- [ ] If a clippy fix changes `userland/tyrne-user/src/lib.rs` asm, the matching audit entry (UNSAFE-2026-0033) is checked against the new text.
- [ ] Every touched markdown file has all `](...)` link targets resolving.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with a `Refs: ADR-0040` trailer.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Shellcheck baseline (measured 2026-10-11, shellcheck 0.11.0 from Homebrew, `shellcheck tools/*.sh`, exit 1):** one warning and four infos.
  - `tools/smoke.sh:28` SC2054 (warning): `INT_FLAGS=(-d int,unimp)`; the comma is part of QEMU's `-d` value, so this is a false positive needing a scoped disable with a reason.
  - `tools/perf-harness.sh:67` SC2329 (info): `cleanup_in_flight` is reported as never invoked, but it is called through `trap` at `:88-90`; scoped disable.
  - `tools/perf-harness.sh:484,519,597` SC2295 (info): `${VAR#${REPO_ROOT}/}` should quote the inner expansion (`${VAR#"${REPO_ROOT}"/}`), which is what shellcheck suggests; fix, do not suppress.
  - `tools/build-userland.sh` and `tools/run-qemu.sh` are clean.
- `ubuntu-latest` may carry an older shellcheck than 0.11.0 and could report the same condition under a different code or not at all (SC2329 is recent); the first CI run is the authority, so re-check the suppressions against its output.
- The userland clippy baseline is **not measured** in this opening pass (no build was run); record it as the first step of implementation. Workspace lints apply to both crates (`[lints] workspace = true`), so `clippy::pedantic` warnings become errors under `-D warnings`.
- **Location re-verification (2026-10-11, HEAD `400dec0`):** all `file:line` citations above were re-checked against the tree and match; nothing drifted. `phase-b2.md` line numbers shift as banners are added, so locate its items by headline.
- Sequencing: no hard dependency, but [T-033](T-033-qemu-tooling-smp-and-timeout.md), [T-037](T-037-userland-bare-metal-cfg-gate.md), [T-038](T-038-console-write-x2-clobber.md) and [T-064](T-064-tyrne-user-api-polish.md) edit the same scripts and userland files, so rebase and re-run both commands when one of them lands first.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
