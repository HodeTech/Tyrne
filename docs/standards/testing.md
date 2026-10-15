# Testing

How Tyrne code is tested. The kernel / `no_std` context imposes constraints that ordinary Rust testing handles gracefully with some adaptation; this standard spells out those adaptations and fixes the vocabulary so that reviewers and CI can agree on what a test is and what it proves.

## Scope

Applies to all crates in the Tyrne workspace: kernel, HAL, BSPs, userspace services, and build/tooling. Tests are themselves code and subject to [code-style.md](code-style.md).

## Test layers

Tyrne uses four layers. A given change almost always adds or updates tests in more than one layer.

### 1. Unit tests

- Live in the source file they test (`#[cfg(test)] mod tests { ... }`).
- Run with the host standard library (`cargo test -p <crate>`), isolated from kernel concerns.
- Test pure logic: data structures, algorithms, capability-token invariants, encoding/decoding.
- A unit test for a kernel module runs in a harness that stubs out the kernel's HAL traits with host-friendly test doubles.
- Fast — the full unit-test suite must finish in under a minute on a contemporary laptop.

### 2. Integration tests

- Live in the crate's `tests/` directory.
- Run in `cargo test` but exercise across-module contracts inside a single crate.
- For kernel-facing crates, integration tests may require a host-side harness that instantiates a fake capability table, fake address space, etc.
- Fail fast on contract violations that unit tests cannot see because they cross module boundaries.

### 3. QEMU boot / smoke tests

- Boot the kernel under QEMU `virt` (primary target) and assert it reaches a known checkpoint.
- **Required:** `tools/smoke.sh` boots the normal debug or release kernel image under QEMU and checks profile-specific serial markers within a timeout, rejecting panic and CPU-fault traces. Build matching userland first, then the kernel; use `tools/smoke.sh --int` or `tools/smoke.sh --release --int`. These are normal images, not a compiled Rust `test` configuration.
- Debug requires greeting, task exit and completion; release requires exit/completion and forbids the debug-console greeting. Captured serial and exception output supports diagnosis. Exact SVC counting and adversarial EL0 images are separate scope, not current smoke gates.
- The current scenario is the boot/EL0 hello/exit round trip. Additional QEMU scenarios must state what behavior they prove; the current smoke does not establish general page-fault containment.
- Slower — seconds per test. Run as a CI gate but not on every file save.

### 4. Hardware smoke tests

- Exercise the kernel on real hardware (Pi 4, Pi 5, Jetson CPU) during release preparation.
- Manual or semi-automated depending on lab setup.
- Not a CI gate (yet). Required per Tier 2+ target before a release.

## What has tests

Every change meets this minimum:

- A **public API** added or changed has unit tests for its contract.
- An **unsafe invariant** documented in a `# Safety` section has an integration or unit test that exercises the path under normal and adversarial inputs, where that is feasible with a host-side harness.
- A **bug fix** has a regression test that fails before the fix and passes after. A bug fix with no regression test is suspect and returned to the author.
- A **syscall** added or changed has at least one QEMU-boot test that exercises it end-to-end.
- An **error path** — a new variant in an `Error` enum — has a test that provokes it.
- A **concurrency fix** is accompanied by a test or, where deterministic testing is impossible, a documented rationale in the PR.

## What does not need tests

- Trivially correct getters / setters that are generated or obvious.
- Compile-time impls (`From`, `Display`) whose behavior is implied by the types, when the type system already constrains the content.
- Test code itself — but helper functions in test code should be simple enough to be obviously correct.

These exemptions are narrow. When in doubt, write the test.

## Test naming

Use descriptive `snake_case` names, following Accepted [ADR-0042](../decisions/0042-descriptive-test-names.md). The guidance is:

```text
<subject>_<condition>_<expected_outcome>
```

There is no mandatory `test_` prefix or mechanically fixed word count. Concise names are valid when the subject, condition and result are unambiguous in context; an existing `test_` prefix is also valid. Review checks meaning rather than enforcing a naming lint or mass rename.

Actual IPC test identifiers in `kernel/src/ipc/mod.rs`:

- `send_without_send_right_fails`
- `recv_without_recv_right_fails`
- `send_with_wrong_object_kind_returns_wrong_object_kind`

The condition and outcome should be specific enough that a reader can diagnose a failure from the name alone.

## Fixtures and doubles

- Prefer explicit fixtures over hidden globals. A test that needs a fake `MemoryCap` constructs one locally.
- Test doubles for HAL traits live in the existing `test-hal` crate. They implement the same traits with deterministic, inspectable behavior.
- Do not share mutable state between tests. Tests run in parallel by default; a shared mutable global will corrupt. Use `thread_local!` or per-test instances.

## Non-determinism

- Tests are deterministic. Random input is fine when seeded; unseeded randomness is not.
- Time-dependent tests use a mock clock, not `std::time`.
- QEMU tests avoid depending on precise timings. They assert on output content, not on how long a step took.

## Coverage

The project does not set a hard coverage number. Coverage is a lagging indicator; good tests are better than lots of tests. That said:

- Kernel core subsystems (IPC, capabilities, memory, scheduler) should approach or exceed 80% line coverage once the implementation lands.
- Hardware interaction code is harder to cover; the QEMU smoke layer compensates.

Coverage is measured with `cargo llvm-cov` on host-runnable tests. Hardware-only paths are excluded from the coverage denominator.

## CI gates

Enforced in CI today (block merge):

- `cargo test` (host crates, `default-members`) — must pass.
- `cargo test --release` (same host crates) — must pass. The separate `tools/check-release-tests.sh` guard requires both named release-only console tests to execute and pass; its isolated profile-flip rejection probe must also pass.
- Clippy with `-D warnings` — must pass through the `host-clippy` and `kernel-clippy` aliases plus `cargo clippy -p tyrne-user -p tyrne-userland-hello --target aarch64-unknown-none -- -D warnings` after the userland image build; these cover distinct host and bare-metal targets (see [infrastructure.md](infrastructure.md) §"Required gates").
- `shellcheck tools/*.sh` at default severity — must pass. Isolated expected-failure probes also verify that the shell and userland lint commands reject their deliberate regressions; the production source stays clean.
- `cargo fmt --all -- --check` — must pass.
- Host crates on stable Rust (`host-stable-check`) — must build/test clean; pinned-nightly jobs enforce linting.
- Miri (Stacked Borrows) over the host-test suite — must pass.
- Native ARM workspace check/clippy/test/Miri on `ubuntu-24.04-arm`, excluding only the BSP; host-gated userland remains included. An isolated arch-only hello regression must fail workspace clippy with compiler exit 101 and either the exact duplicate-`panic_impl` diagnostic or `error: unwinding panics are not supported without std`; parallel all-target compilation can report either first. Offline fixtures assert both classes, refuse unrelated/tool errors and verify cleanup. Live required-check registration and full-policy read-back completed on 2026-10-12 after hosted green and both fresh rounds. See [ci.md](../guides/ci.md#why-an-arm64-host-job).

- Debug/release single-core QEMU EL0 smoke (`qemu-smoke`) with matching images, required profile markers and panic/CPU-fault rejection. Synthetic trace fixtures and three actual private kernel mutations verify rejection; production/probe traces and provenance are uploaded even on failure. Exact SVC counting and adversarial EL0 images remain separate scope.

Offline branch-protection safety fixtures validate drift, app bindings, additive-only writes, remote green proof and CI refusal without live API calls or admin credentials.

Not yet enforced in CI:

- Hardware smoke tests — run periodically, not per-PR.

A red CI is never ignored. Flaky tests are bugs, not facts of life.

## Failure mode

When a test fails in CI:

1. The author reproduces locally.
2. If the failure reveals a real bug, the test stays and the bug is fixed.
3. If the failure reveals a flaky test, the flaky test is fixed (not disabled) in the same PR.
4. Disabling a test with `#[ignore]` requires a comment referencing a tracking issue and a statement of what would re-enable it.

## Anti-patterns to reject

- Tests that assert nothing (a function is called; its output is not checked).
- Tests that mutate shared state and depend on test order.
- `#[ignore]`d tests without a tracking issue.
- Tests that hide failures behind `if let Err(_) = ... { /* ignore */ }`.
- Tests that take the exact code under test and restate it — test the *behavior*, not the implementation.
- QEMU tests that depend on exact timing rather than content.

## Tooling

- `cargo test` — host-side unit and integration tests.
- `cargo llvm-cov` — coverage measurement.
- `miri` — runs unit tests under an interpreter that catches some UB.
- **Required:** `tools/smoke.sh` / `tools/smoke.sh --release` for matching debug/release QEMU images; see [run-under-qemu.md](../guides/run-under-qemu.md) for build prerequisites and exception logging.
- `cargo-nextest` — optional, for faster test runs; acceptable but not required.

## References

- [ADR-0040 — Phase B.2 consolidation bridge](../decisions/0040-phase-b2-consolidation-bridge.md).
- [ADR-0042 — Descriptive test names without a mandatory test_ prefix](../decisions/0042-descriptive-test-names.md).
- The Rust Book, Testing chapter: https://doc.rust-lang.org/book/ch11-00-testing.html
- Embedded Rust testing patterns: https://docs.rust-embedded.org/book/
- `cargo-nextest`: https://nexte.st/
- Hubris testing approach (prior art): https://hubris.oxide.computer/
