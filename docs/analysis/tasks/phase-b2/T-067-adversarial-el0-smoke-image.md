# T-067 — Add an adversarial EL0 userland image to the smoke suite

- **Phase:** B.2
- **Milestone:** Track B.2-4
- **Status:** Draft
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-034](T-034-ci-qemu-smoke-job.md), [T-037](T-037-userland-bare-metal-cfg-gate.md)
- **Informs:** none
- **ADRs required:** possibly an append-only revision-note rider on [ADR-0039](../../../decisions/0039-userland-build-pipeline.md) (a second userland image changes the build pipeline); no new ADR expected

---

## User story

As the maintainer of the EL0/EL1 trust boundary, I want a deliberately hostile EL0 program run under QEMU on every smoke, so that the confused-deputy defences are proven against the real trap frame and the real page tables, not only against the test fakes.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-4 (the item "The only real EL0 userspace program exercises just two syscalls…" at line 412). The only EL0 program is `hello`, which performs one valid `console_write` and `task_exit` (`userland/hello/src/main.rs:44-49`). The kernel's confused-deputy defences (the per-task window, the per-page `USER` check, the capability gate) are tested on the host in `kernel/src/syscall/user_access.rs` and `dispatch.rs`, but only against `FakeMmu` / `BlockMappedMmu` (`user_access.rs:333`); nothing ever drives them from a real EL0 task through `QemuVirtMmu` and the hardware trap frame. A bug in the BSP glue or the real page-table walker would pass every current test.

The phase item asks for a second, adversarial image (or `hello` behind a feature) that attempts an out-of-window `console_write`, a `console_write` against a page without `USER`, and an IPC call with a stale capability handle, asserting each is rejected. Several mechanics are undecided, which is why this task is `Draft`: the BSP embeds exactly one image (`bsp-qemu-virt/src/main.rs:375`, loaded at `:1318`), `tools/build-userland.sh` and the BSP `build.rs` hard-code `hello.bin`, `tyrne-user` has no `send` wrapper, and the kernel discards task exit codes (`bsp-qemu-virt/src/syscall.rs:268`), so results must reach the trace some other way.

## Acceptance criteria

- [ ] Decisions recorded (review history; ADR-0039 rider if the pipeline changes): second crate vs `hello` behind a feature; how the kernel loads and selects the image; the marker protocol; how the debug-only `console_write` interacts with [T-065](T-065-debug-console-feature-flag.md); how a non-`USER` page is provisioned inside the task's window.
- [ ] The adversarial image builds through the userland pipeline as a raw-flat image ([ADR-0029](../../../decisions/0029-initial-userspace-image-format.md)), with `hello.ld`-style ASSERTs against `.data` / `.bss` / `.got`, and the default `hello.bin` is byte-identical before and after this task (record the sha256).
- [ ] The image attempts (1) a `console_write` whose buffer lies outside the task's window, (2) a `console_write` whose buffer lies on a mapped page without `USER`, and (3) an IPC `send` with a stale capability handle; each is rejected with the typed status the host tests already pin for the same class (`console_write_out_of_range_buffer_faults_without_output`, `dispatch.rs:1153`, and `console_write_cap_ok_but_non_user_page_emits_nothing`, `:1186`, for the first two; `IpcError::StaleHandle`, status `0x201`, for the third, since `validate_ep_cap` maps an unresolved endpoint capability to it at `kernel/src/ipc/mod.rs:594`), with no panic, no fault class in the `--int` trace, and none of the attacked bytes printed.
- [ ] Smoke: `tools/smoke.sh` gains a mode that asserts one distinct marker per attack and exits non-zero if any marker is missing or a fault class appears. The assertion is shown to bite: weaken one gate locally, observe the smoke go red, restore it, and record the result.
- [ ] CI: the `qemu-smoke` job from T-034 runs the adversarial smoke within its timeout; the job table in `docs/guides/ci.md` and `docs/guides/first-userspace.md` describe the second image.
- [ ] Audit: any new `unsafe` (for example an IPC `send` shim) has an entry or Amendment in [`unsafe-log.md`](../../../audits/unsafe-log.md) per [`justify-unsafe`](../../../../.agents/skills/justify-unsafe/SKILL.md).
- [ ] Security review recorded per [`security-review.md`](../../../standards/security-review.md) (`Security-Review:` trailer): the change adds hostile code on the EL0 boundary and touches the boot-time task setup.

## Out of scope

- Changing any kernel gate or error code; this task only observes the existing defences. A defect it finds is fixed in its own task.
- The `qemu-smoke` job itself and `--smp`: [T-034](T-034-ci-qemu-smoke-job.md), [T-033](T-033-qemu-tooling-smp-and-timeout.md).
- Extracting and unit-testing the BSP context selection: [T-066](T-066-bsp-syscall-context-extraction.md).
- Host-side hardening of `user_access.rs`: [T-043](T-043-user-access-hardening.md).
- Fuzzing or a general EL0 test framework.

## Approach

Stay within the project's smallest-shape discipline ([ADR-0039](../../../decisions/0039-userland-build-pipeline.md)): ADR-0039 already names the upgrade for a second userspace program (a shell loop in `tools/build-userland.sh`, or an `xtask build-userland` subcommand), so extend the existing pipeline rather than invent a new one. The adversarial program restates the syscall ABI through `tyrne-user` where a wrapper exists and needs a new audited shim for `send`. Markers must be emitted by the program itself through a valid `console_write` after each rejection (the kernel does not surface exit codes), which makes the debug-gated console a dependency of the smoke build; resolve that together with T-065.

## Definition of done

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` and `cargo kernel-clippy` clean with `-D warnings`.
- [ ] `cargo clippy -p tyrne-user -p tyrne-userland-hello --target aarch64-unknown-none -- -D warnings` clean, extended to the new crate if one is added.
- [ ] `cargo host-test` passes; `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean if any kernel / hal / test-hal code changes.
- [ ] `tools/build-userland.sh && cargo kernel-build && tools/smoke.sh --int` PASS for the default build, and the adversarial smoke PASS with all markers.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0039`, `Audit:` and `Security-Review:` trailers as applicable.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions (why this is `Draft`).** (1) Second crate vs `hello` behind a feature flag (and the matching `include_bytes!` / `build.rs` change; today both hard-code `userland/hello/hello.bin`). (2) Loading and identification: a build-time image switch vs loading both and creating a second task (the address-space arena holds 8 slots, `ADDRESS_SPACE_ARENA_CAPACITY`, `kernel/src/mm/address_space.rs:41`). (3) Marker protocol and where results appear. (4) The non-`USER` target page: the per-task window is `[entry_va, user_sp)` (`kernel/src/sched/mod.rs:511-514`) and the loader maps only `USER` pages, so the adversarial build must provision one deliberately. (5) Interaction with T-065, since the markers need `console_write`.
- **Location re-verification (2026-10-11).** All cited code lines reproduce on HEAD. `phase-b2.md` line numbers are live as of writing (the pre-kickoff snapshot had them two lower); locate by the quoted lead words if they shift again.
- Sequencing: needs T-034 first (the job it extends) and T-037 first (a new userland crate must build on host / Miri). T-065 may land before or after; whichever is second adapts.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Draft |
