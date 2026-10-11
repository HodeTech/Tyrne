# T-042 — Harden PMM input validation (+ correct the false atomicity comment)

- **Phase:** B.2
- **Milestone:** Track B.2-3
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-057](T-057-typed-addresses-phys-virt.md), [T-072](T-072-doc-comment-hygiene.md)
- **ADRs required:** none

---

## User story

As the physical memory manager, I want `Pmm::new` and `free_frame` to reject every malformed input their documentation promises to reject (and accept a harmless zero-length range), so that init-time mistakes fail fast and my safety comments do not claim guarantees the code lacks.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from three LOW items in [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-3 (lines 301, 304, 307), one Polish item (line 624, reserved-range capacity boundary coverage), and one extra item routed "now" by [`phase-c.md`](../../../roadmap/phases/phase-c.md) line 159 (item (1) of the `Pmm` finding under "Entry gate", section at line 149). All of it is in `kernel/src/mm/pmm.rs`. Three input-validation gaps: `PmmError::MisalignedAddress` is documented as also returned by `free_frame` (`pmm.rs:46-51`) but `free_frame` (`:504-543`) never constructs it; `Pmm::new`'s pairwise overlap check (`:247-253`, condition at `:249`) rejects a zero-length reserved range nested inside another range as `OverlappingReservedRanges`, although such a range can never affect the bitmap-versus-counter parity; and `Pmm::new` rejects an inverted reserved range (`:234-236`) but has no equivalent check for an inverted top-level extent (`:199-214`), so `end < start` silently builds an empty PMM.

The extra item is a false safety premise. The SAFETY comment on the frame-zeroing `write_bytes` (`pmm.rs:450-453`, audit entry UNSAFE-2026-0026) says "SMP extension keeps this invariant via the set_bit atomicity that precedes the write". But `set_bit` and `clear_bit` (`pmm.rs:741-746`, `:759-764`) are plain non-atomic read-modify-write on a `&mut [u8]`; no atomicity exists today. Making the bitmap atomic or serialised is Phase C work (`phase-c.md` "Entry gate"), not this task.

## Acceptance criteria

- [ ] `Pmm::free_frame` returns `Err(PmmError::MisalignedAddress)` for a PA that is not `PAGE_SIZE`-aligned, as its first check (`if !pa.0.is_multiple_of(PAGE_SIZE)`), leaving state byte-stable; the `free_frame` doc comment (`pmm.rs:488-503`) and the `PmmError::MisalignedAddress` doc (`:46-51`) agree with the behaviour.
- [ ] `Pmm::new` skips the pairwise overlap check for any range with `frame_count() == 0`, so a zero-length range nested in (or touching) another range is accepted with consistent `reserved_count`/bitmap parity; real overlaps are still rejected.
- [ ] `Pmm::new` rejects an inverted extent (`extent.end.0 < extent.start.0`) with `Err(PmmError::OutOfRange)` immediately after the alignment check; a zero-length extent (`end == start`) behaves as before. The `Pmm::new` doc comment (`pmm.rs:153-197`) lists the new validation.
- [ ] Tests: new unit tests fail before and pass after for each new path that can be constructed: zero-length nested range accepted; inverted extent rejected; free of a misaligned frame rejected **only if** a sound test-only construction exists (a test-only `unsafe` construction with a SAFETY comment, see Design notes; this task does not require one) — otherwise the guard is verified by code inspection plus the doc comment, and that decision is recorded in the review history; and a reserved-range capacity boundary pair mirroring the exact-fit half of `new_rejects_extent_larger_than_bitmap` (`pmm.rs:1405`): exactly `R` reserved ranges accepted, `R + 1` rejected (`new_rejects_too_many_reserved_ranges`, `:831`, covers only the reject side).
- [ ] The false premise is corrected as a comment-only change: the SAFETY text at `pmm.rs:450-453` no longer claims `set_bit` atomicity and says the bitmap is plain non-atomic, so SMP safety needs a lock or atomics (Phase C, `phase-c.md` "Entry gate"); every other `atomic`/`SMP` mention in the file was reviewed (`grep -n -i 'atomic\|SMP' kernel/src/mm/pmm.rs`) and reworded where it implies the bitmap is already SMP-safe. The diff for this criterion touches no executable line.
- [ ] `cargo miri test -p tyrne-kernel` stays clean with the new tests.

## Out of scope

- Making the bitmap atomic, adding a lock, or any cross-core `Pmm` serialisation: Phase C (`phase-c.md` line 159, items (2) and (3)).
- The stale `could_yield_pa_overlapping` doc and the `Pmm::new` "Validation (i)..(iv)" label mismatch: [T-072](T-072-doc-comment-hygiene.md), which is sequenced after this task because it edits the same file.
- Typed-address API work on `PhysAddr`/`Range<usize>`: [T-057](T-057-typed-addresses-phys-virt.md).

## Approach

Each fix follows the phase item. `free_frame`: add `if !pa.0.is_multiple_of(PAGE_SIZE) { return Err(PmmError::MisalignedAddress); }` at the top. Overlap check: skip pairs where either range has `frame_count() == 0` (inverted ranges are already rejected earlier in the function, so zero frames means `start == end`). Extent: add `if extent.end.0 < extent.start.0 { return Err(PmmError::OutOfRange); }` right after the alignment check, mirroring the reserved-range treatment. Then add the tests, then correct the comment in a separate, comment-only commit so reviewers can confirm no behaviour changed in it.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes with the new tests added.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean (kernel code changes).
- [ ] `tools/smoke.sh --int` PASS (the BSP builds its PMM through `Pmm::new` at boot; confirm the `pmm initialized` banner is unchanged).
- [ ] No new `unsafe`; the SAFETY comment edit does not change the operation, and UNSAFE-2026-0026 already says a future SMP bitmap "will need atomic compare-exchange" (`docs/audits/unsafe-log.md:570`), so no Amendment is expected. Confirm and record that in the review history.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0035` and `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Constructibility of a misaligned frame.** `PhysFrame`'s field is private to `tyrne-hal` (`hal/src/mmu/mod.rs:178`) and `PhysFrame::from_aligned` rejects unaligned input, so from `tyrne-kernel` a misaligned `PhysFrame` cannot be built; the `PmmError` doc itself calls the path "defensive". Decide and record how the new guard is exercised: a test-only construction with a SAFETY comment (test-only `unsafe` is exempt from audit entries under [`unsafe-policy.md`](../../../standards/unsafe-policy.md)), or, if no sound construction exists, code inspection plus the doc comment. Do not add a production-visible constructor to `tyrne-hal` for this.
- **Other SMP mentions.** `pmm.rs:345`, `:369` and `:380` describe the wrap-scan as forward-compatibility for SMP per-core caches; they do not repeat the `set_bit` atomicity claim. Reword them only if they read as "already SMP-ready".
- **Re-verification (2026-10-11).** All `pmm.rs` locations in the three item citations and the premise comment were confirmed against the current tree and had not drifted. `phase-b2.md` lines 301/304/307/624 and `phase-c.md` lines 149/159 are live numbers (the phase-b2 numbers are +2 versus the pre-kickoff snapshot).
- **Sequencing.** Before [T-072](T-072-doc-comment-hygiene.md) (same file). Informs [T-057](T-057-typed-addresses-phys-virt.md), which later changes `could_yield_pa_overlapping`'s signature.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
