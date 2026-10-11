# T-038 — Mark x2 as clobbered in the console_write syscall shim

- **Phase:** B.2
- **Milestone:** Track B.2-3
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-037](T-037-userland-bare-metal-cfg-gate.md) (same file; sequencing avoids merge conflicts)
- **Informs:** [T-064](T-064-tyrne-user-api-polish.md)
- **ADRs required:** none (an unsafe-audit Amendment instead)

---

## User story

As the EL0 syscall shim `tyrne_user::console_write`, I want my inline asm to declare every register the kernel overwrites on return, so that the compiler can never keep a live value in `x2` across the `svc` and the shim stays free of Rust `asm!` undefined behaviour.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from the HIGH item at [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) line 319. The `console_write` asm block in `userland/tyrne-user/src/lib.rs` (lines 102-115) declares the length as `in("x2") buf.len() as u64` (line 108). In Rust's `asm!` rules an `in` register must hold its input value when the block exits; the kernel violates that on every call. For each `SyscallEffect::Resume`, `bsp-qemu-virt/src/syscall.rs:224` stores `r.payload[1]` into the saved frame's `x2` slot (`f.x2_x3[0] = r.payload[1]; // x2`), and the sync trampoline reloads `x2` from the frame at `bsp-qemu-virt/src/vectors.s:237` before `ERET`. `console_write` returns only `payload[0]` (`kernel/src/syscall/dispatch.rs:303`), so `x2` comes back as `0`, not `buf.len()`.

No misbehaviour has been observed, because the only caller (`hello`'s `_start`) does not reuse `x2` after the call. The risk is latent: any codegen change that keeps a value in `x2` across the `svc` would silently corrupt it. The unsafe-audit entry [UNSAFE-2026-0033](../../../audits/unsafe-log.md) (`docs/audits/unsafe-log.md`, lines 751-768) records the same wrong clobber set (`in x2`, only `x3..x7` clobbered, at lines 756 and 761) and must be corrected through the log's append-only Amendment mechanism ([`unsafe-policy.md`](../../../standards/unsafe-policy.md) section 3). `task_exit` (`lib.rs:141-148`) passes only `x0` and is `options(noreturn)`, so it is unaffected.

## Acceptance criteria

- [ ] `userland/tyrne-user/src/lib.rs` `console_write`: the operand at line 108 becomes `inout("x2") buf.len() as u64 => _,`; the `x0`/`x1` operands and the `lateout("x3")` to `lateout("x7")` operands are unchanged.
- [ ] The SAFETY comment (lines 92-101) states that `x2..x7` are marked clobbered and why `x2` is (the kernel overwrites it with payload word 1); `grep -n 'x3\.\.x7' userland/tyrne-user/src/lib.rs` returns nothing.
- [ ] `docs/audits/unsafe-log.md` gains an appended `Amendment (YYYY-MM-DD, commit SHA): …` block on UNSAFE-2026-0033 that states the corrected operand (`inout x2 => _`) and clobber set (`x2..x7`), confirms `task_exit` is unaffected, and notes the cfg gate refined by [T-037](T-037-userland-bare-metal-cfg-gate.md). The original body, including lines 756 and 761, is not edited, so `git diff` of the log shows only added lines.
- [ ] The `unsafe` change is reviewed per [`unsafe-policy.md`](../../../standards/unsafe-policy.md) Review items 3-4 and [`justify-unsafe`](../../../../.agents/skills/justify-unsafe/SKILL.md) step 6 (solo phase: a separate self-review pass by the maintainer); the commit carries `Audit: UNSAFE-2026-0033` and `Security-Review:` trailers.
- [ ] Tests: `tools/build-userland.sh`, `cargo kernel-build` and `tools/smoke.sh --int` pass with the same trace as before (`hello from userspace`, only the two expected EL0 `SVC` exceptions, no new fault class). Also run `cargo clippy -p tyrne-user -p tyrne-userland-hello --target aarch64-unknown-none -- -D warnings`; if it reports pre-existing warnings unrelated to this change, note them for [T-031](T-031-ci-userland-clippy-and-shellcheck.md) rather than fixing them here.
- [ ] The review history records the new `hello.bin` size and sha256 (baseline 117 bytes, `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`; it may legitimately change, or be byte-identical) and the result of disassembling the `svc #0` site (`rust-objdump -d` from the pinned `llvm-tools-preview` on `target/aarch64-unknown-none/debug/hello`), or why that was infeasible.

## Out of scope

- The `target_arch`/`target_os` gate fix in the same file: [T-037](T-037-userland-bare-metal-cfg-gate.md) (lands first).
- The `CapWord` newtype, error decoding and doc items for `tyrne-user`: [T-064](T-064-tyrne-user-api-polish.md).
- Any kernel-side change. The kernel's register write-back (`syscall.rs:217-229`) is correct; only the userspace declaration is wrong.
- The `NoCurrentTask` status code and other `SyscallError` changes: [T-063](T-063-syscall-error-taxonomy-polish.md).

## Approach

Change the one operand as given in the phase item: `inout("x2") buf.len() as u64 => _,`. This matches the style already used for the `lateout(...) _` operands on `x3`-`x7`: the value is passed in, the output is discarded, and the compiler may not assume `x2` survives. Then update the SAFETY comment and append the Amendment to UNSAFE-2026-0033 (read [`unsafe-policy.md`](../../../standards/unsafe-policy.md) section 3 and the log header for the exact heading format `**Amendment (YYYY-MM-DD, commit SHA): <short title>.**`; the commit SHA may be filled in after the commit, as the log permits). The Amendment restates the corrected operation and invariants rather than editing the old text. Check `task_exit` once more when making the change (it passes only `x0`).

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes.
- [ ] Miri: no kernel, hal or test-hal code changes here, so the narrower `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` is not required.
- [ ] `tools/smoke.sh --int` PASS (userland code changed).
- [ ] The UNSAFE-2026-0033 audit Amendment is in the same commit as the code change; the tag cross-check (every `UNSAFE-2026-NNNN` in source resolves to a log entry and vice versa) still holds.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`, `Audit: UNSAFE-2026-0033` and `Security-Review: <reviewer>` trailers.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions (non-blocking).** ADR-0030's register table lists `x8` and `x9`-`x18` as "clobbered" on return, yet the shim declares `in("x8")` and nothing for `x9`-`x18`. This is sound against what the BSP does today: `Resume` writes only `x0`-`x7` and the trampoline restores `x8`-`x30` to their trapped values (`vectors.s:191-192`). It does mean the shim depends on the BSP implementation rather than on the ADR table. Whether to also mark those registers, or to tighten the ADR text, is a possible follow-up and is deliberately not changed here; record any decision in the review history.
- **Optional.** UNSAFE-2026-0033's Status field still says "Dormant in v1"; since T-028 the shims run in every smoke. The Amendment may note that, but it is not a criterion.
- **Re-verification (2026-10-11).** Verified against the current tree: `lib.rs:102-115` and `:108`, `syscall.rs:224`, `vectors.s:237`, `dispatch.rs:303`, `unsafe-log.md:756,761`. One precision note: the phase item also cites `vectors.s:157`; that line is the IRQ trampoline's restore of the same slot and is not on the syscall return path. The syscall return path is `:237`. The `phase-b2.md` line (319) is the live number after the kickoff banner added 2 lines.
- **Sequencing.** After [T-037](T-037-userland-bare-metal-cfg-gate.md) (same file), before [T-064](T-064-tyrne-user-api-polish.md).

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
