# T-060 — Deduplicate the copy-user per-page walk

- **Phase:** B.2
- **Milestone:** Track B.2-4
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-043](T-043-user-access-hardening.md), [T-057](T-057-typed-addresses-phys-virt.md)
- **Informs:** none
- **ADRs required:** none

---

## User story

As the copy-user trust boundary, I want the per-page validated-copy walk to exist once, so that a future fix to its cursor arithmetic or its permission checks applies to both copy directions automatically.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from the item at [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) line 377 and the Polish item at line 610 (Track B.2-4). In `kernel/src/syscall/user_access.rs`, pass 2 of `copy_from_user` (`:204-248`) and pass 2 of `copy_to_user` (`:287-316`) are the same loop: compute `page_base`, `in_page`, `page_remaining` and `run = min(page_remaining, end - cur)`, re-translate the page with `Mmu::translate`, re-check the leaf flags, do one `core::ptr::copy`, and advance `cur`. They differ only in the permission re-check (`USER` for reads, `USER` and `WRITE` for writes) and the direction of the copy. Each loop holds one of the module's two non-test `unsafe` blocks (`:243`, `:311`), both covered by audit entry UNSAFE-2026-0030 in [`unsafe-log.md`](../../../audits/unsafe-log.md).

This is the userspace-to-kernel trust boundary (a trigger in [`security-review.md`](../../../standards/security-review.md)), so the refactor must be behaviour-preserving and reviewed as such. It follows [T-043](T-043-user-access-hardening.md), which changes the same flag checks (DEVICE exclusion) and adds the missing `copy_to_user` top-page test, and [T-057](T-057-typed-addresses-phys-virt.md), which retypes `user_ptr` to `VirtAddr`; writing the helper after both means it is written once against the final signatures.

## Acceptance criteria

- [ ] A private generic `walk_user_pages<M: Mmu>(mmu, task_as, user_ptr, len, require_write, per_page: impl FnMut(...)) -> Result<(), SyscallError>` owns the cursor arithmetic, the per-page translate, the flag checks and the cursor advance; `copy_from_user` and `copy_to_user` pass only a short direction-specific closure. `grep -n 'PAGE_SIZE.wrapping_sub(in_page)' kernel/src/syscall/user_access.rs` returns exactly one line (two today: `:211` and `:294`).
- [ ] The two `unsafe` blocks stay distinct: non-test `user_access.rs` still contains exactly two `unsafe {` blocks, each with its own `// SAFETY:` comment that states its direction, range, ownership/permission, disjointness and no-interleaving invariants (the four in the current comments); no single block serves both directions.
- [ ] Permission semantics are preserved exactly: the read direction re-checks `USER` only, the write direction `USER` and `WRITE` (via `require_write`), and a non-`USER` or non-writable leaf still returns `SyscallError::FaultAddress` before any byte moves, including everything [T-043](T-043-user-access-hardening.md) added.
- [ ] Tests: every existing `user_access` test and the `console_write` tests in `dispatch.rs` pass with no edited assertion, including `copy_from_user_range_ending_in_top_page_does_not_spuriously_fault` (`user_access.rs:601`) and the `copy_to_user` counterpart added by T-043; `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean (these tests perform real copies); `tools/smoke.sh --int` PASS (hello's `console_write` exercises the read path).
- [ ] A mutation check is recorded in the review history: temporarily breaking the helper's run computation (and, separately, its per-page flag re-check) makes at least one read-direction test and one write-direction test fail, which shows the shared helper is covered in both directions.
- [ ] Audit: UNSAFE-2026-0030 is re-read against the new code. If its Location wording ("the single `unsafe` block in each of `copy_from_user` and `copy_to_user`") no longer matches, an **Amendment** is appended per [`unsafe-policy.md`](../../../standards/unsafe-policy.md) (Amendment mechanism, line 74; second reviewer required for this trust-boundary entry) following [`justify-unsafe`](../../../../.agents/skills/justify-unsafe/SKILL.md); either way "re-read, accurate" or the amendment is noted in the review history. The stale `copy_nonoverlapping` heading is [T-069](T-069-unsafe-log-corrections.md)'s.
- [ ] Security review recorded in the review history and the `Security-Review:` trailer (Trust-boundaries and Memory-safety checklists).

## Out of scope

- DEVICE-page exclusion, the zero-length probe short-circuit and the `copy_to_user` top-page test: [T-043](T-043-user-access-hardening.md) (a dependency).
- Retyping the pointer arguments to `VirtAddr`: [T-057](T-057-typed-addresses-phys-virt.md) (a dependency).
- Per-chunk re-probing and the double page-table walk in `console_write` / `probe_user_pages` (performance): [T-073](T-073-console-write-copy-path-performance-decision.md).
- Adding the worked example to the module doc for future pointer-returning syscalls (separate Polish item).
- Pass 1 (`probe_user_pages`, `:140-170`) is a separate, simpler page-by-page loop; folding it into the helper is not asked for by the item.

## Approach

Extract the shared per-page loop into a private generic helper, as the item describes: the helper does translate, flag checks and cursor arithmetic once, and `copy_from_user`/`copy_to_user` supply a three-line closure around `core::ptr::copy` (source and destination swapped). Keep both `unsafe` sites and their SAFETY comments distinct, as the item requires. Do not change the two-pass structure (probe everything, then copy), the all-or-nothing guarantee, or the order of the window check, zero-length early return and probe.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean.
- [ ] `tools/smoke.sh --int` PASS (kernel code changed).
- [ ] Audit entry UNSAFE-2026-0030 verified or amended as above; no new `unsafe` block.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`, `Audit: UNSAFE-2026-0030` (if amended) and a `Security-Review: <reviewer>` trailer.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open choice, recorded in the review history (does not block starting).** Whether pass 1 is also expressed through the helper with a no-op closure. If not, the saturating cursor advance in `probe_user_pages` (`:161-168`) stays its own code path, still covered by both top-page tests through the shared probe.
- **Sequencing.** After T-043 and T-057 (both edit the same functions). [T-069](T-069-unsafe-log-corrections.md) edits the heading of the same audit entry; the two edits touch different text.
- **Re-verification (2026-10-11).** The loop bounds, the two `unsafe` blocks (`:243`, `:311`), the top-page test (`:601`) and `copy_to_user_rejects_read_only_user_page` (`:486`) were re-checked with `grep -n`/`sed -n`; no drift (the item's `204-248` and `287-315` bound the loops from their `let end` to the cursor advance). The `phase-b2.md` lines are from the live file (was 375 and 608 in the pre-kickoff snapshot).

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
