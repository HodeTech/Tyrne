# T-065 — Gate console_write on a dedicated debug-console feature

- **Phase:** B.2
- **Milestone:** Track B.2-4
- **Status:** Draft
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-030](T-030-ci-release-profile-gate.md) (the release gate must exist to catch a mistake here)
- **Informs:** none
- **ADRs required:** append-only revision-note rider on [ADR-0031](../../../decisions/0031-initial-syscall-set.md) (it left the gate mechanism open); no new ADR unless the rider turns out to change a decided contract

---

## User story

As the kernel's syscall surface, I want `console_write` to exist only when an explicit `debug-console` feature is enabled, so that the privileged debug syscall's presence is an auditable build decision rather than a side effect of the general-purpose `debug_assertions` setting.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-4 (the item "The debug-console security gate is keyed off the general-purpose `debug_assertions` cfg…" at line 452) and the Polish items at lines 576 and 607. `SyscallNumber::decode` treats number `5` as `console_write` only when `cfg!(debug_assertions)` holds (`kernel/src/syscall/abi.rs:87`, documented at `:60` and `:69-72`). The release profile never overrides `debug-assertions` (`Cargo.toml:65-70`), so release builds drop the syscall; but any future profile that enables `debug-assertions` for an unrelated reason (for example a profiling or fuzzing profile) would silently re-expose a privileged syscall. [ADR-0031](../../../decisions/0031-initial-syscall-set.md) fixed the two-gate contract (capability gate plus debug gate) and explicitly left the mechanism open (`:55`, `:129`: "a `cfg!(debug_assertions)` arm vs. a Cargo feature").

The kernel crate has no features today; the BSP has one, `perf-bench` (`bsp-qemu-virt/Cargo.toml`), which is the precedent for a default-off measurement/debug feature. Ten kernel tests in `kernel/src/syscall/dispatch.rs` (`#[cfg(debug_assertions)]` at lines 606, 968, 997, 1029, 1064, 1096, 1124, 1152, 1185, 1219), plus `abi.rs:372`, and the two release-only tests (`abi.rs:378` `console_write_is_absent_in_release_builds`, `dispatch.rs:1256` `console_write_number_is_bad_syscall_in_release_build`) are keyed on `debug_assertions` and must be re-keyed with the gate. This is security-sensitive: it decides whether a privileged syscall exists in a given image.

## Acceptance criteria

- [ ] Decision recorded: an append-only `## Revision notes` rider on ADR-0031 states the feature name and scope, where it is defined and forwarded, which build aliases / scripts / CI jobs enable it, and how the tests are re-keyed (answers to the Open decisions below). It lands before or with the code.
- [ ] `SyscallNumber::decode` gates number `5` on the feature instead of `cfg!(debug_assertions)`; the doc comments at `abi.rs:60` and `:69-72` match; `grep -rn debug_assertions kernel/src/syscall` no longer finds the console gate.
- [ ] Tests: the 11 console-related `#[cfg(debug_assertions)]` gates and the two `not(debug_assertions)` tests above are re-keyed to the feature, and two decoupling tests are executed by CI: feature off means number `5` decodes to `None` even with debug assertions on (the default `cargo host-test`), and feature on means it decodes in a release-profile test run.
- [ ] Build wiring: the feature is defined, the BSP forwards it, and the aliases / scripts / CI jobs from the rider build the intended variants (the `kernel-build-debug` alias with `--features debug-console` per the phase item; the T-030 release jobs build without it).
- [ ] Smoke: the QEMU smoke asserts the `hello from userspace` line in the feature-on build and its absence, with the task still exiting, in the feature-off build. Today `tools/smoke.sh:110-118` asserts only the `all tasks complete` marker and the absence of fault classes, so a silently-off gate would not turn it red.
- [ ] Documentation: the comment next to `[profile.release]` that T-030 adds in `Cargo.toml` is rewritten to describe the feature gate (no longer a `debug-assertions` dependency); the "Debug vs release" notes in `docs/guides/first-userspace.md` (`:47-50`, `:156`), the README status row (`:31`) and the run commands in `docs/guides/run-under-qemu.md` / `docs/guides/ci.md` are updated.
- [ ] Security review recorded per [`security-review.md`](../../../standards/security-review.md) (`Security-Review:` trailer).

## Out of scope

- The CI release-profile gate itself and the `kernel-build-release` aliases: [T-030](T-030-ci-release-profile-gate.md).
- The `qemu-smoke` CI job: [T-034](T-034-ci-qemu-smoke-job.md); whichever of T-034 and this task lands second updates that job's build command.
- Bounding or length-capping `console_write` itself: [T-039](T-039-console-write-bounded-spin-and-length-cap.md).
- Adversarial smoke markers that depend on `console_write`: [T-067](T-067-adversarial-el0-smoke-image.md).

## Approach

Introduce a default-off `debug-console` Cargo feature and replace the `cfg!(debug_assertions)` match guard with `cfg!(feature = "debug-console")` (keeping `cfg!`, not `#[cfg]`, so the `ConsoleWrite` arm stays compiled and referenced in every build, as `abi.rs:69-76` explains). Only the `cargo kernel-build` / dev workflows enable it explicitly, via a `kernel-build-debug` alias. Define the kernel feature in `tyrne-kernel` and have the BSP forward it, following the `perf-bench` precedent; settle the remaining items below in the rider first.

## Definition of done

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` and `cargo kernel-clippy` clean with `-D warnings`, in both feature states.
- [ ] `cargo host-test` passes, and the feature-on test run (command recorded in the rider) passes.
- [ ] `cargo test --release` passes (T-030's release tests, re-keyed).
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean.
- [ ] `tools/build-userland.sh && cargo kernel-build-debug && tools/smoke.sh --int` PASS (alias name per the rider), plus the release / feature-off smoke result recorded.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0031` and a `Security-Review:` trailer.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions (why this is `Draft`).** (1) Feature name and scope (`debug-console`, default off per the phase item). (2) Where it is defined: kernel crate plus BSP forwarding (`debug-console = ["tyrne-kernel/debug-console"]`) vs another arrangement. (3) Which aliases, scripts (`tools/smoke.sh:56` builds with `cargo kernel-build`; `tools/run-qemu.sh`) and CI jobs enable it. (4) How `cargo host-test` covers the feature-on tests: an alias change vs a second CI step. (5) Whether the BSP's unconditional seeding of the `DebugConsole` capability (`bsp-qemu-virt/src/main.rs:1514-1518`) is also feature-gated. (6) Smoke / CI build variants (see criteria 4-5).
- Cargo features are additive and unified across the build graph, so a build's posture is the union of every edge that enables the feature. Enable it only from the BSP's own feature, never from another crate's default features, and say so in the rider.
- With the gate off, `userland/hello` still runs: its `console_write` returns `BadSyscallNumber`, which the program ignores (`userland/hello/src/main.rs:45-47`), then it exits; this is exactly the release behaviour `first-userspace.md` already describes.
- If [T-051](T-051-contributing-and-security-status.md) has written "`console_write` is debug-build-only" into `SECURITY.md`, update that sentence here.
- **Location re-verification (2026-10-11).** All cited code lines reproduce on HEAD. `phase-b2.md` line numbers are live as of writing (the pre-kickoff snapshot had them two lower); locate by the quoted lead words if they shift again.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Draft |
