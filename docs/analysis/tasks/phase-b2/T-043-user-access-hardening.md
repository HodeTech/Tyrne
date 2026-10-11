# T-043 — Harden the copy-user path (DEVICE exclusion, zero-length probe, top-page test)

- **Phase:** B.2
- **Milestone:** Track B.2-3
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-057](T-057-typed-addresses-phys-virt.md), [T-060](T-060-user-access-walk-helper-dedup.md)
- **ADRs required:** an append-only revision-note rider on [ADR-0038](../../../decisions/0038-mmu-translate-and-user-access.md) recording the DEVICE decision (a new ADR only if the allow-with-typed-MMIO-API route is chosen instead; see Design notes)

---

## User story

As the syscall copy-user path, I want to refuse device (MMIO) pages, handle a zero-length probe without a spurious fault, and have both copy directions pinned by the same edge-case tests, so that `copy_from_user`/`copy_to_user` can never be turned into an MMIO register read/write and their documented edge cases hold.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from three items in [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-3 (lines 295 MEDIUM, 310 LOW, 313 LOW), all in `kernel/src/syscall/user_access.rs`. First, the per-page checks require `MappingFlags::USER` (and `WRITE` for writes) but never exclude `MappingFlags::DEVICE`: `probe_user_pages` (`:140`, checks at `:155-160`) and the two pass-2 re-checks (`copy_from_user` `:216`, `copy_to_user` `:299`) would let a `memcpy` through the high-half direct map touch MMIO registers once userspace drivers exist. The real walker does report `DEVICE` (`hal/src/mmu/vmsav8.rs:397-431`, `descriptor_bits_to_flags`), so a guard here is effective on `QemuVirtMmu`. There is no such mapping for EL0 in v1, which is why this is a decision to make before the first driver syscall rather than a live exploit.

Second, `probe_user_pages` does not special-case `len == 0`: with an unaligned `user_ptr`, `end == user_ptr` while the first page base is below it, so the loop probes one page and can fault spuriously. Callers short-circuit today and `UserAccessWindow::validate` accepts zero length, but the function's doc only says "`len` must be non-zero". Third, "a valid range ending in the top page must not spuriously fault" is pinned only for `copy_from_user` (test at `:600-615`), not for the structurally duplicated `copy_to_user` (pass 2 at `:286-317`).

## Acceptance criteria

- [ ] Decision recorded as an append-only `## Revision notes` rider on ADR-0038 (the ADR has no such section yet, so the rider adds it): default **fail closed**, i.e. a leaf carrying `MappingFlags::DEVICE` is rejected with `SyscallError::FaultAddress`, with a forward reference to the Phase E first-driver work. If the allow-with-typed/volatile-MMIO route is chosen instead, a new ADR is written before code lands (`phase-b2.md` closing note).
- [ ] `probe_user_pages` and both pass-2 re-checks (`user_access.rs:216`, `:299`) reject a `DEVICE` leaf with `FaultAddress` under the chosen decision; an all-or-nothing multi-page range containing one `DEVICE` page moves zero bytes.
- [ ] `probe_user_pages` returns `Ok(())` immediately for `len == 0`, matching `UserAccessWindow::validate`; its doc comment (`:123-139`) no longer says the caller must short-circuit.
- [ ] Tests (using `FakeUserMem` with `USER | WRITE | DEVICE`, which `FakeMmu` accepts): `copy_from_user` and `copy_to_user` each reject a `DEVICE` page and a multi-page range with a `DEVICE` page (destination/user bytes untouched); `probe_user_pages` with `len == 0` and an unaligned pointer returns `Ok`; and `copy_to_user_range_ending_in_top_page_does_not_spuriously_fault` mirrors the existing `copy_from_user_range_ending_in_top_page_does_not_spuriously_fault` (`:601`). The DEVICE and zero-length tests fail before the change; the top-page test is a symmetric regression pin and may pass before it.
- [ ] Documentation: the module doc (`user_access.rs:1-58`) names the `DEVICE` exclusion beside the `USER` requirement, and [UNSAFE-2026-0030](../../../audits/unsafe-log.md) gains an Amendment recording the added precondition on the copy sites (the SAFETY comments at `:220-243` and `:303-311` are updated to match).

## Out of scope

- Deduplicating the per-page walk of `copy_from_user`/`copy_to_user`: [T-060](T-060-user-access-walk-helper-dedup.md) (sequenced after this task so one top-page test then covers both directions).
- Typed address arguments for these functions: [T-057](T-057-typed-addresses-phys-virt.md).
- A device-mapping syscall, driver capabilities, or any MMIO access API for userspace: Phase E.
- Caching translations to avoid the double page-table walk: [T-073](T-073-console-write-copy-path-performance-decision.md).

## Approach

Add the `DEVICE` rejection next to the existing `USER`/`WRITE` checks in `probe_user_pages` and in each pass-2 loop (the pass-2 checks are defence in depth that mirror the probe, so they get the same condition). Add `if len == 0 { return Ok(()); }` as the first statement of `probe_user_pages`. Add the tests listed above next to the existing ones in the `tests` module, reusing `FakeUserMem`. Write the ADR-0038 rider first so the gap becomes a designed decision, then implement it.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes with the new tests added.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean (kernel code changes; the copy sites are Miri-exercised via `FakeUserMem`).
- [ ] `tools/smoke.sh --int` PASS (kernel code on the `console_write` path changes); the `hello from userspace` line still appears.
- [ ] The UNSAFE-2026-0030 Amendment is appended per [`unsafe-policy.md`](../../../standards/unsafe-policy.md) and [`justify-unsafe`](../../../../.agents/skills/justify-unsafe/SKILL.md), with `Audit: UNSAFE-2026-0030` in the commit.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0038` and `Refs: ADR-0040`, and a `Security-Review:` trailer (this is the EL0 memory boundary).
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Decision to record.** Default is fail closed, consistent with CLAUDE.md rule 1. Allowing `DEVICE` pages through a typed or volatile MMIO API is a different design (it changes what a copy means) and belongs in an ADR, not in this fix.
- **Re-verification (2026-10-11).** The item's locations hold: `probe_user_pages` is `:140` (the item cited `:140-170`), the `USER`/`WRITE` checks are `:155-160`, the pass-2 checks `:216` and `:299`, and the existing top-page test `:601`. `phase-b2.md` lines 295/310/313 are live numbers after the kickoff banner (+2).
- **Sequencing.** Before [T-060](T-060-user-access-walk-helper-dedup.md): once the two loops share one helper, the DEVICE check and the top-page test then cover both directions. [T-057](T-057-typed-addresses-phys-virt.md) retypes these functions' arguments afterwards.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
