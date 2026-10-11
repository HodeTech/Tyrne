# T-064 — Polish the tyrne-user API (CapWord, error decode, docs)

- **Phase:** B.2
- **Milestone:** Track B.2-4
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-037](T-037-userland-bare-metal-cfg-gate.md), [T-038](T-038-console-write-x2-clobber.md) (same files; land first to avoid conflicts)
- **Informs:** none
- **ADRs required:** none

---

## User story

As the author of the second userspace program, I want `tyrne-user` to type its capability words and classify syscall failures, so that I never pass a bare `u64` as a capability or reverse-engineer the kernel's status-word layout by hand.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-4 (items starting "`tyrne-user`'s syscall wrappers pass capability handles as bare `u64`…" at line 357 and "`tyrne-user::SyscallError` exposes only the raw status word…" at line 406) plus three Track B.2-5 doc items at lines 514, 517 and 520. `userland/tyrne-user/src/lib.rs` is the only userspace library and `hello` is its only consumer. It exposes `HELLO_CONSOLE_CAP: u64` (`lib.rs:57`), `console_write(cap: u64, buf: &[u8])` (`lib.rs:89`, with a host stub at `:128`) and a `SyscallError(pub u64)` that wraps the raw `x0` status (`lib.rs:61-68`). The kernel documents the status layout (`1`-`3` top level, `0x100 | cap code`, `0x200 | ipc code`; `kernel/src/syscall/error.rs:17-22`), but userspace has no way to use it without re-deriving the bit layout.

The three doc items are small mismatches in the same two files. The `console_write` doc (`lib.rs:72-77`) reads like a partial write is possible, but the v1 kernel is all-or-nothing (the whole range is probed before any byte is emitted; `kernel/src/syscall/dispatch.rs:228-300`). The crate carries an unconditional `#![no_std]` (`lib.rs:21`) while the comment at `lib.rs:23-27` says it mirrors the kernel's `cfg_attr(not(test), no_std)` discipline. `hello`'s panic handler exits with code `101` (and success with `0`), but the kernel discards the code (`SyscallEffect::Terminate(_code)`, `bsp-qemu-virt/src/syscall.rs:268`).

## Acceptance criteria

- [ ] `tyrne-user` defines a local capability newtype (planned name `CapWord`, wrapping `u64`) that does not depend on the kernel crate ("restate the ABI, don't share the type"); `HELLO_CONSOLE_CAP` and both `console_write` variants (the `asm!` one and the host stub) use it; `userland/hello/src/main.rs` needs at most a trivial call-site edit.
- [ ] A decode or classification API for `tyrne_user::SyscallError` is added, built from the documented `0x100` / `0x200` block constants: either a small mirrored enum with `From<SyscallError>` / `TryFrom<u64>`, or methods such as `is_cap_error`, `is_ipc_error`, `top_level_kind`. The chosen shape is recorded in the review history; if [T-063](T-063-syscall-error-taxonomy-polish.md) has landed, the new `NoCurrentTask` code is decoded too, otherwise a comment names the gap.
- [ ] Tests: unit tests in `tyrne-user` pin the classification of `1`-`3`, the cap block (`0x101`-`0x107`), the IPC block (`0x201`-`0x207`) and an unrecognised value (classified, never panics). They run under `cargo test -p tyrne-user` and are picked up by CI's Miri step (`cargo miri test --workspace --exclude tyrne-bsp-qemu-virt`).
- [ ] Behaviour preserved: `tools/build-userland.sh` produces a `hello.bin` whose size and sha256 equal those produced at T-038's merge commit (the newtype is zero-cost; record both values), and `tools/smoke.sh --int` is PASS with an unchanged trace.
- [ ] Doc fixes: `console_write`'s doc states the v1 guarantee (`Ok(buf.len())` on success, or the raw status on rejection; a partial write never happens); the `#![no_std]` / comment mismatch is resolved by one of the two options in the phase item (`#![cfg_attr(not(test), no_std)]`, or correcting the comment) and the choice is recorded in the review history; `hello`'s panic handler doc notes that the exit codes (`101`, `0`) are write-only from userspace until a task surfaces exit status.
- [ ] Documentation: `docs/guides/first-userspace.md` (lines 87, 95, 125 mention `HELLO_CONSOLE_CAP`) still reads correctly, and the UNSAFE-2026-0033 operand description in [`unsafe-log.md`](../../../audits/unsafe-log.md) is still accurate after the type change (append an Amendment only if it is not).

## Out of scope

- The `x2` clobber fix and the UNSAFE-2026-0033 amendment for it: [T-038](T-038-console-write-x2-clobber.md).
- The bare-metal `cfg` gate rework in these files: [T-037](T-037-userland-bare-metal-cfg-gate.md).
- New syscall wrappers (`send`, `recv`, `task_yield`); a wrapper adds `unsafe` and needs its own audit entry (relevant to [T-067](T-067-adversarial-el0-smoke-image.md)).
- Surfacing task exit status to userspace (a future kernel change).
- A shared kernel/userspace error type; the crate stays independent of the kernel.

## Approach

Add the newtype and thread it through the three signatures; keep the packed-handle layout documented where it already is (`kernel/src/syscall/abi.rs:20-26`: index in bits `0..16`, generation in bits `16..48`; and `lib.rs:47-55`) as the only description of what the word contains. For decoding, restate the block bases and per-block codes userspace-side with a comment pointing at `kernel/src/syscall/error.rs` and its pinned tests, since there is deliberately no shared type; a drift is therefore caught by review, not by the compiler. The `no_std` choice interacts with the tests criterion: with an unconditional `#![no_std]` the crate cannot host `#[cfg(test)]` unit tests without an `extern crate std`, which favours the `cfg_attr(not(test), no_std)` option.

## Definition of done

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo clippy -p tyrne-user -p tyrne-userland-hello --target aarch64-unknown-none -- -D warnings` clean (the command [T-031](T-031-ci-userland-clippy-and-shellcheck.md) adds to CI; run it locally even if T-031 has not landed).
- [ ] `cargo host-test` passes, and `cargo test -p tyrne-user` passes with the new tests.
- [ ] `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` clean (valid once T-037 has landed).
- [ ] `tools/build-userland.sh && cargo kernel-build && tools/smoke.sh --int` PASS.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md); no `Audit:` trailer unless an Amendment is appended.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions (recorded in the review history).** (1) Decode API shape: mirrored enum vs classification methods. (2) `no_std` handling: `cfg_attr(not(test), no_std)` vs fixing the comment (note `hal/src/lib.rs:33` also uses an unconditional `#![no_std]`). (3) Whether `CapWord`'s field is `pub` (the phase item's example) or constructed through a `const fn`.
- **Location re-verification (2026-10-11).** Every cited line reproduces on HEAD: `lib.rs:21`, `:27`, `:57`, `:61-68`, `:72-77`, `:89`, `:128`; `hello/src/main.rs:44-58`. T-037 edits the `cfg` lines (`:28`, `:35`, `:44`, `:83`, `:134`) and T-038 edits the `asm!` block (`:102-115`), so line numbers will shift before this task starts; re-locate by symbol.
- `phase-b2.md` line numbers are live as of writing (the pre-kickoff snapshot had them two lower); locate by the quoted lead words if they shift again.
- CI's llvm-cov step excludes `tyrne-user` (`.github/workflows/ci.yml:277`), so the new tests add no coverage-gate risk; the Miri step does include the crate.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
