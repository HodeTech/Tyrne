# T-070 — Pin trap-frame layouts with offset_of! assertions

- **Phase:** B.2
- **Milestone:** Track B.2-5
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** none
- **ADRs required:** none

---

## User story

As the maintainer of the EL0-to-EL1 trap path, I want every field offset of `TrapFrame` and `SyscallTrapFrame` pinned by a compile-time assertion against the offsets `vectors.s` hard-codes, so that a layout-preserving field reorder fails the build instead of silently corrupting saved registers on the first IRQ or syscall.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from the MEDIUM item at [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) line 526 and the Polish item at line 667. Two `#[repr(C)]` structs are filled by hand-written asm at fixed offsets: `TrapFrame` (`bsp-qemu-virt/src/exceptions.rs:48`, 12 fields of 16 bytes, 192 total) for the IRQ trampoline, and `SyscallTrapFrame` (`bsp-qemu-virt/src/syscall.rs:63`, 17 fields, 272 total) for the SVC trampoline. Their only compile-time guards are size checks (`exceptions.rs:112`, `syscall.rs:90`), which a same-size reorder of two `[u64; 2]` fields passes. `Aarch64TaskContext` already has the stronger form: `bsp-qemu-virt/src/cpu.rs:339-344` pins its size and every field offset the asm uses with `core::mem::offset_of!`, and its comment states that a size-only assert would not catch a layout-preserving reorder.

The audit log currently understates this gap in both directions. UNSAFE-2026-0020 says asm/Rust mismatches "are caught at first IRQ fire, not at compile time" (`docs/audits/unsafe-log.md:396`), while UNSAFE-2026-0029 says the size guard "fails the build on any drift" (`:659`), which is not true for a same-size reorder. The log is append-only, so both are corrected by Amendment. The Polish item asks for the pattern to become a standing rule beside `unsafe-policy.md` section 5a, so the structs Phase C's preemption work adds inherit it.

## Acceptance criteria

- [ ] `exceptions.rs`: a `const _: () = assert!(core::mem::offset_of!(TrapFrame, FIELD) == OFFSET)` for all 12 fields, next to the existing size assert: `x0_x1` 0x00, `x2_x3` 0x10 and so on in steps of 0x10 to `x18_lr` 0x90, `elr_spsr` 0xA0, `_reserved` 0xB0. The expected values are copied from the layout table in `vectors.s:98-110`, not derived from the Rust struct.
- [ ] `syscall.rs`: the same for all 17 `SyscallTrapFrame` fields: `x0_x1` 0x00 to `x28_x29` 0xE0, `x30_sp_el0` 0xF0, `elr_spsr` 0x100, matching the table in `vectors.s:173-185`.
- [ ] A failing assert is a compile error: temporarily changing one expected offset (or swapping two fields) makes `cargo kernel-build` fail at const evaluation. The command and the error line are recorded in the review history; the change is not committed.
- [ ] The comments in `vectors.s` that name the guard (lines 120-126 for the IRQ trampoline, 173-176 for the SVC trampoline) say that size and every field offset are pinned; the human-readable layout tables stay as the authority.
- [ ] Audit log: Amendments on UNSAFE-2026-0020 and UNSAFE-2026-0029 record that the trampoline/Rust layout agreement is now compile-time pinned per field, and which earlier statement they correct (log lines 396 and 659). The original text is not edited (`git diff` of the log shows no removed line); each Amendment uses the `**Amendment (YYYY-MM-DD, commit SHA): <short title>.**` header and a `Reviewed by` line, and states the second-reviewer requirement, per [`unsafe-policy.md`](../../../standards/unsafe-policy.md) section 3 and Review items 3-4.
- [ ] Policy: `docs/standards/unsafe-policy.md` gains a subsection after section 5a (before section 6) requiring `size_of` plus per-field `offset_of!` const asserts for any `#[repr(C)]` type whose layout is hard-coded by hand-written asm or `naked_asm!`, citing `cpu.rs`, `exceptions.rs` and `syscall.rs` as the exemplars. The route taken (see Design notes) is recorded in the review history.
- [ ] Tests and review: `cargo kernel-build`, `cargo kernel-clippy` and `tools/smoke.sh --int` pass with an unchanged trace (the assertions add no code); the security review required for asm/Rust layout at the EL0-to-EL1 boundary ([`security-review.md`](../../../standards/security-review.md): syscalls, boot, `unsafe` regions) is filed and named in the commit's `Security-Review:` trailer.

## Out of scope

- Any behavioural change to the trampolines or to the frame layouts, including zeroing `TrapFrame._reserved` (it is deliberately uninitialised and redacted in `Debug`; see its field note).
- Pinning `Aarch64TaskContext` again: `cpu.rs:339-344` already covers it.
- Extracting the syscall-context selection in `syscall_entry`: [T-066](T-066-bsp-syscall-context-extraction.md) (it works on `syscall.rs:143-294`, a different region of the same file).
- The wording fixes in the same BSP files: [T-072](T-072-doc-comment-hygiene.md) (`exceptions.rs:34`, `main.rs:95-96`).

## Approach

For each struct, add one `offset_of!` assert per field directly under the existing size assert, in field order, with the offsets typed as literals from the `vectors.s` layout comments. That literal-versus-struct comparison is what makes the pin meaningful: the asm comment stays the human-readable authority and the build fails if the Rust side drifts from it. `core::mem::offset_of!` is already in use in the crate (`cpu.rs`), and the `SyscallTrapFrame` fields are private, which is fine because the asserts live in the same module. Then update the two `vectors.s` comments, append the two audit Amendments, and add the policy subsection. The asserts add no `unsafe`, so no new audit entry is needed.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings` (the BSP is excluded from host builds by design; this confirms nothing else moved).
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes; Miri is not required (no kernel, hal or test-hal code changes).
- [ ] `tools/smoke.sh --int` PASS (BSP code changed).
- [ ] Every `](…)` target in the edited docs (`unsafe-policy.md`, `unsafe-log.md`) resolves, and the UNSAFE tag cross-check from [T-069](T-069-unsafe-log-corrections.md) Approach still prints nothing.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`, `Audit: UNSAFE-2026-0020`, `Audit: UNSAFE-2026-0029` and `Security-Review: <reviewer>` trailers.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decision, how the policy rule lands.** `propose-standard-change` says a substantive standards change is ADR-first. `unsafe-policy.md` section 5a itself was added without an ADR (commit `6f258fb`, 2026-04-21, with the BSP boot checklist). Choose between following the skill (write or identify the motivating ADR, then edit the standard) and treating this as a clarification in the section 5a mould, and record the ruling in the review history before editing the standard. The code and audit work does not wait on it.
- **Re-verification (2026-10-11).** The documented layouts are cited as whole tables rather than single rows: IRQ table `vectors.s:98-110` with `stp` at `:129-141` and `ldp` at `:146-158`; SVC table `:173-185` with `stp` at `:197-216` and `ldp` at `:232-251`. The `exceptions.rs:112` and `syscall.rs:90` locations in the plan item are the existing size asserts, not the struct definitions (`exceptions.rs:48`, `syscall.rs:63`).
- **Sequencing.** [T-038](T-038-console-write-x2-clobber.md) and [T-071](T-071-unsafe-contract-hardening.md) also append Amendments to `unsafe-log.md`; keep each entry's Amendments in date order on merge. [T-072](T-072-doc-comment-hygiene.md) edits a different line of `exceptions.rs`.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
