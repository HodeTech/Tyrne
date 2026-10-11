# T-039 — Bound console_write's per-byte spin and cap its length

- **Phase:** B.2
- **Milestone:** Track B.2-3
- **Status:** Draft
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-073](T-073-console-write-copy-path-performance-decision.md); Phase C Milestone C3 item 6 ([`phase-c.md`](../../../roadmap/phases/phase-c.md), `Cpu::without_interrupts`)
- **ADRs required:** possibly a revision-note rider on [ADR-0007](../../../decisions/0007-console-trait.md) (Console trait) and/or [ADR-0031](../../../decisions/0031-initial-syscall-set.md); decide and record (see Open decisions)

---

## User story

As the kernel's interrupt-masked syscall path, I want `console_write` to have a bounded run time (a capped length and no unbounded UART spin), so that a stalled UART or an oversized request from EL0 cannot hang the core.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from two items in [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-3 (line 289 HIGH, line 292 MEDIUM). `sys_console_write` (`kernel/src/syscall/dispatch.rs:228-304`) validates the whole range, then copies and emits in 256-byte chunks (`CONSOLE_WRITE_CHUNK`, `dispatch.rs:50`; loop at `:276-297`), calling `ctx.console.write_bytes(&buf[..chunk])` at `:295`. Two things are unbounded. First, `len` has no upper limit, so one syscall can run an arbitrarily long chunk loop. Second, `Pl011Uart::write_bytes` (`bsp-qemu-virt/src/console.rs:61-87`) busy-waits on `UARTFR.TXFF` with no iteration or time bound (`while read_volatile(fr) & UARTFR_TXFF != 0 { spin_loop() }`, lines 79-81; audited as UNSAFE-2026-0005). The syscall handler runs with interrupts masked, so a UART that backpressures would hang the core with no recovery. The length cap alone does not fix the spin, which is why the two items are resolved together.

This gates Phase C Milestone C3 item 6, the `Cpu::without_interrupts` critical-section primitive: an unbounded spin under masked interrupts is exactly the deadlock shape C3 exists to prevent once real IRQs can interrupt kernel code. Note also that the `Console` contract (`hal/src/console.rs:16-31`, ADR-0007) says a console that cannot write "silently drops bytes" and that implementations should not "block indefinitely", which the PL011 implementation does not currently honour.

## Acceptance criteria

- [ ] Decision recorded (Open decisions below): bound the spin (a) or document the unbounded-spin assumption (b); whether `Console::write_bytes` changes signature; and the cap's placement and error. The record is an ADR-0007 and/or ADR-0031 revision-note rider where a contract changes, otherwise this task's review history.
- [ ] Spin handling implemented per the decision. For (a): `Pl011Uart::write_bytes` (`bsp-qemu-virt/src/console.rs:61-87`) cannot loop forever (iteration cap or Timer deadline) and its exhaustion behaviour is defined (drop, or a typed failure the dispatcher maps to a syscall error). For (b): the assumption is stated in the `write_bytes` doc comment and in an appended UNSAFE-2026-0005 Amendment so the Pi 4 BSP cannot silently inherit an unbounded spin.
- [ ] `const MAX_CONSOLE_WRITE_LEN: usize = 4096;` is added next to `CONSOLE_WRITE_CHUNK` in `kernel/src/syscall/dispatch.rs`; `sys_console_write` returns `SyscallError::BadArgument` when `len` exceeds it, before any output or user-memory read.
- [ ] Tests: a boundary test pins `len == MAX_CONSOLE_WRITE_LEN` (accepted, all bytes emitted) and `len == MAX_CONSOLE_WRITE_LEN + 1` (`BadArgument`, console untouched); under (a), a test pins the bounded-spin behaviour on whatever host-testable path the decision creates. Each new test fails before the change and passes after.
- [ ] Documentation: the `SyscallError::BadArgument` doc comment (`kernel/src/syscall/error.rs:68-71`, currently "no v1 producer today") names `console_write` as its first producer, and the new cap is stated in the `sys_console_write` doc comment.

## Out of scope

- A bounded-chunk discipline for the general `copy_from_user`/`copy_to_user` path (a Phase C polish item), and the double page-table walk cost: [T-073](T-073-console-write-copy-path-performance-decision.md).
- Introducing `Cpu::without_interrupts` or any spinlock: Phase C Milestone C3.
- The `debug_assertions` gate on `console_write` itself: [T-065](T-065-debug-console-feature-flag.md).
- Any Pi 4 UART driver work (Phase D).

## Approach

Add the length cap first: a `MAX_CONSOLE_WRITE_LEN` constant of 4096 checked at the top of `sys_console_write`, returning `BadArgument`, with a boundary test. For the spin, the phase item offers two routes. (a) Bound `Pl011Uart::write_bytes`'s per-byte wait with an iteration cap or a Timer-based deadline and surface a typed failure the dispatcher can translate into a syscall error. (b) If flow control is never enabled on the target and the spin is judged structurally unreachable, add an explicit doc comment (or an audit-log-style justification) recording that assumption so a future BSP port does not inherit an unbounded spin under masked interrupts. Changing `Console::write_bytes` to return a `Result` alters the HAL trait and would need an ADR-0007 revision-note rider.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes with the new tests added.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean (kernel, and hal/test-hal if the `Console` trait or its fake changes).
- [ ] `tools/smoke.sh --int` PASS (BSP and kernel code change); the `hello from userspace` line still appears.
- [ ] Any new or changed `unsafe` has an audit entry or Amendment in [`unsafe-log.md`](../../../audits/unsafe-log.md) per [`unsafe-policy.md`](../../../standards/unsafe-policy.md) / [`justify-unsafe`](../../../../.agents/skills/justify-unsafe/SKILL.md).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040` (plus `Refs: ADR-0007` / `ADR-0031` if a rider lands) and `Audit:` / `Security-Review:` trailers if applicable.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions.**
  1. Spin: (a) bound it, or (b) document the assumption. Within (a): an iteration cap or a Timer deadline, and what exhaustion does. Dropping bytes already fits the `Console` contract with no trait change but gives the dispatcher nothing to report; a typed failure needs `write_bytes` to return a `Result` (an ADR-0007 rider) or a separate fallible method.
  2. If the dispatcher reports a spin failure, which `SyscallError` it maps to (an existing variant, or a new stable status code, which is an ADR-0030 matter).
  3. Whether the 4096-byte cap, which is observable ABI behaviour for `console_write`, needs an ADR-0031 revision note.
  4. Placement of the cap check relative to the capability gate. The phase item says "before Gate 1/2/3"; the alternative is after Gate 1 so an unauthorised caller always sees the capability error first. Either way no byte is read or emitted before the capability check passes (ADR-0031 line 55).
  5. How to test the bound: the BSP crate has no host test target, so the poll loop would have to be extracted into a closure-taking function in a host-testable crate (precedent: the `start_prelude` extraction in T-011), or be covered by review only. Decide and record.
- **Re-verification (2026-10-11).** `dispatch.rs:295` is exact. The phase item cites the loop as `dispatch.rs:252-300`; the live function is `:228-304` with the chunk loop at `:276-297` (the item's range had drifted). `phase-b2.md` lines 289/292 are live numbers after the kickoff banner (+2).
- **Sequencing.** No dependencies. [T-073](T-073-console-write-copy-path-performance-decision.md) depends on the cap landing first. The userland `console_write` docs ([T-064](T-064-tyrne-user-api-polish.md)) are the natural place to mention the cap once it exists.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Draft |
