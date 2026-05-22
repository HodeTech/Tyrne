# C2-kernel-mm — memory management (master review, commit 288ddb2)

Track scope: the kernel-side memory-management subsystem.

- `kernel/src/mm/pmm.rs` (1195 lines) — bitmap physical-frame allocator per ADR-0035.
- `kernel/src/mm/address_space.rs` (1380 lines) — `AddressSpace<M>` kernel object + cap-gated `cap_*` wrappers per ADR-0028.
- `kernel/src/mm/mod.rs` (169 lines) — subsystem parent, `PhysFrameRange`, `phys_frame_kernel_ptr`.

Context consulted: ADR-0035, ADR-0028, ADR-0027 (via cross-refs), `hal/src/mmu/mod.rs` (`FrameProvider`/`Mmu`/`PhysFrame`/`MapperFlush` contracts), `test-hal/src/mmu.rs` (`FakeMmu`/`VecFrameProvider`), `kernel/src/obj/task_loader.rs` (the principal external caller), `kernel/src/obj/arena.rs` (`SlotId`/`Arena`), `kernel/src/cap/table.rs` (cap surface), `docs/audits/unsafe-log.md` (UNSAFE-2026-0025/0026/0027), and the standards (unsafe-policy, error-handling, testing, code-style, code-review, architectural-principles).

## Summary

This is high-quality, conservatively-engineered code. The PMM is a faithful, well-tested implementation of ADR-0035's Option A bitmap allocator; the `AddressSpace<M>` object and its cap-gated wrappers are a clean realisation of ADR-0028 Option A with no ambient-authority gaps. The two `unsafe` surfaces in scope (PMM frame-zeroing UNSAFE-2026-0026; the `Mmu::create_address_space` trait-contract call site that rides UNSAFE-2026-0026's zero-fill guarantee) carry rigorous, policy-conformant SAFETY comments with correct invariants, stated rejected alternatives, and live audit references. I found **no Blocker and no Major correctness or memory-safety defects.** The frame accounting is consistent (cached counters cross-checked against the bitmap by test), the alignment proofs are sound, the overlap/double-free/exhaustion paths are validated and tested, and the `could_yield_pa_overlapping` frame-range arithmetic is off-by-one-correct.

The findings are concentrated in **documentation accuracy** (a genuinely stale PMM module banner), **maintainability/robustness hardening** (the documented "mutate-before-fallible-return" leak window in `alloc_frame`; a `pub`-but-unexported visibility inconsistency), and **a bounded performance/ergonomics concern** in `could_yield_pa_overlapping` for large input ranges. Test adequacy is strong on the PMM side and good on the address-space side, with a few adversarial gaps worth closing (PMM `new` capacity/`OutOfRange`-on-undersized-`N` path; allocation determinism across a free-in-the-middle pattern; `cap_map` intermediate-frame `OutOfFrames` through a real walker).

Severity counts: Blocker 0, Major 0, Minor 6, Nit 5, Praise 4.

## Findings

### Blocker

None.

### Major

None.

### Minor

#### C2-001 — PMM module-level doc banner is stale: claims "No `unsafe`" and that alloc/free/stats land "in the next commit"
`kernel/src/mm/pmm.rs:13-16`

The module doc-comment reads:

> Commit 1 (this file, initial landing): `Pmm` struct + bitmap arithmetic + `Pmm::new` constructor + four host tests pinning `Pmm::new`'s contract. **No `unsafe`. The next commit adds `alloc_frame` / `free_frame` / `stats`.**

The file as committed contains `alloc_frame`, `free_frame`, `stats`, `could_yield_pa_overlapping`, a live `unsafe { core::ptr::write_bytes(...) }` block (line 436), and far more than four tests. The "Commit 1 … No unsafe … next commit adds …" narrative describes a mid-arc intermediate state of T-017 that no longer matches the landed file.

Why it matters: documentation-accuracy is an explicit reviewer checklist item (code-review.md §Review checklist → Documentation), and a banner that says "No `unsafe`" on a file whose central operation is a raw-pointer write is actively misleading to the next reader — it points them away from the one place in the file where memory-safety is negotiated. It also contradicts the file's own UNSAFE-2026-0026 SAFETY block.

Suggested fix: replace the commit-by-commit narrative with a steady-state description of the module's responsibilities ("tracks the managed extent via a bitmap; reserves init-time ranges; implements `FrameProvider`; zero-fills allocated frames under UNSAFE-2026-0026"), or move the commit-arc note into a historical "Implementation history" line that does not assert present-tense properties.

#### C2-002 — `alloc_frame` mutates bitmap/hint/counters *before* the fallible `PhysFrame::from_aligned` return (self-documented latent frame-leak)
`kernel/src/mm/pmm.rs:365-460`

The function sets the bitmap bit, advances `hint`, decrements `free_count`, and increments `allocated_count` (lines 366-369), then performs the zero-fill, and only at the very end returns `PhysFrame::from_aligned(PhysAddr(pa_usize))` (line 460), which is an `Option`. The code's own comment (lines 446-459) honestly flags the consequence: if a future change ever weakens the alignment proof, `from_aligned` returns `None`, the function returns `None` to the caller, and the frame is permanently leaked (bit set, no handle handed out, counters already moved).

Today this is *not* a live bug — `extent.start` is page-aligned by `Pmm::new` validation (i) and `idx * PAGE_SIZE` preserves alignment, so `from_aligned` is provably `Some`. But the standard ordering for a fallible-tail operation is "compute the fallible value first, mutate state only once it has succeeded." Keeping the mutation after the `from_aligned` would make the leak *structurally impossible* rather than merely *currently unreachable*, and would let a future maintainer who alters the validation set fail safe.

Why it matters: P2 (small, defensible TCB) and the project's "when in doubt, choose the more conservative option" rule both favour structural impossibility over proof-by-current-invariant for a memory-accounting primitive. The cost is a 4-line reorder.

Suggested fix: compute `let frame = PhysFrame::from_aligned(PhysAddr(pa_usize))?;` (or a `match` that returns `None` without mutating) *before* the `set_bit`/`hint`/counter updates and the zero-fill; perform the mutations and zero-fill only on the `Some` path; then return `Some(frame)`. The zero-fill must still run after the bit is conceptually "owned", but since the alignment check is pure and side-effect-free, it can precede the commit safely.

#### C2-003 — `could_yield_pa_overlapping` is `O((range_len / PAGE_SIZE) × populated_reserved)` over a caller-supplied range; a large range walks every covered frame
`kernel/src/mm/pmm.rs:578-626`

The helper clips `pa_range` to the extent and then iterates **every covered frame index** (`for idx in start_idx..end_idx`), doing an `O(populated_reserved)` `.any(|r| r.contains(...))` scan per frame. For the sole production caller (task_loader's 8-byte / 1-frame image, T-019) this is a single iteration and entirely fine, as the docstring notes. But the method is `pub` and takes an arbitrary `core::ops::Range<usize>`: a caller passing a range spanning the whole 128 MiB extent (32 768 frames) × `R = 8` reserved slots performs ~256 K `contains` checks for a query that is answerable in `O(populated_reserved)` with pure interval arithmetic.

Why it matters: it is a public allocator-adjacent query whose cost scales with attacker/caller-influenced input size. ADR-0035 explicitly calls out keeping the PMM's hot paths bounded; this helper's complexity is unbounded in the input-range length even though the *answer* never needs per-frame enumeration.

Suggested fix: replace the per-frame loop with an interval computation — the clipped query overlaps a yieldable frame iff `[clipped_start, clipped_end)` is not fully covered by the union of the reserved ranges that intersect it. Concretely: subtract the (at most `R`) reserved intervals from the clipped query interval and return `true` iff any residue remains. That is `O(populated_reserved)` regardless of range length and removes the frame-by-frame walk entirely. (If the per-frame form is retained for clarity, cap it / document the intended max range length in the `# Algorithm` section as a precondition.)

#### C2-004 — `destroy_address_space` and `get_address_space_mut` are `pub` but not re-exported from `mm/mod.rs`, unlike their siblings
`kernel/src/mm/address_space.rs:303-310, 324-329` and `kernel/src/mm/mod.rs:90-94`

`mm/mod.rs`'s `pub use address_space::{...}` re-exports `create_address_space` and `get_address_space` (plus the cap-gated wrappers and types) but omits `destroy_address_space` and `get_address_space_mut`, both of which are declared `pub` on the module. The result is an inconsistent public surface: half the free-function family is reachable as `crate::mm::create_address_space` / `get_address_space`, the other half only as `crate::mm::address_space::destroy_address_space` / `get_address_space_mut`. `destroy_address_space` has no caller outside the module (only `cap_create_address_space`'s rollback arm at line 672 uses it, in-module), and `get_address_space_mut` is used in-module by `cap_map`/`cap_unmap`.

Why it matters: it is a low-grade API-coherence smell — a reviewer cannot tell from the `pub use` list which functions are "the kernel-facing surface". Either the two functions are part of the surface (then export them) or they are module-internal (then narrow them to `pub(crate)` / `pub(in crate::mm)`), which would also document intent. The doc-comment on `destroy_address_space` already says its only v1 use is the in-module rollback path, which argues for `pub(crate)`.

Suggested fix: pick one — add both to the `pub use` block for symmetry, or downgrade `destroy_address_space` (and `get_address_space_mut`, if no external caller is planned before B4) to `pub(crate)`. Given the doc-stated single in-module caller, `pub(crate)` is the more honest signal and shrinks the cap-bypass-able surface (P2).

#### C2-005 — `Pmm::new` has no host test for the `OutOfRange`-on-undersized-`N` path, which is the load-bearing bitmap-size invariant
`kernel/src/mm/pmm.rs:196-198` (code) / `kernel/src/mm/pmm.rs:697-1195` (tests)

The check `if total_frames > N.saturating_mul(8) { return Err(PmmError::OutOfRange) }` is the *single* guard that prevents the private `set_bit`/`read_bit`/`clear_bit` helpers (which index `bitmap[byte]` and would panic on out-of-bounds) from ever receiving an out-of-range index. Every other in-bounds argument is established by this invariant. The test module pins misaligned-extent, too-many-ranges, overlapping-ranges, out-of-extent-ranges, and the alloc/free/exhaustion cycle — but I find no test that constructs a `Pmm<N, R>` whose `extent.frame_count() > N * 8` and asserts `Err(OutOfRange)`. (e.g. `Pmm<1, _>` over a 16-frame extent: 16 frames > 1*8 = 8 → must reject.)

Why it matters: testing.md requires an error path (a new `Error` variant) to have a test that provokes it, and this particular variant guards the bitmap against buffer overflow. A BSP that picks too small an `N` is exactly the "init-time programming error" the code's comment (lines 191-195) says it surfaces; without a test, a regression that (say) flipped the comparison to `>=` or dropped the `saturating_mul` would not be caught by the suite.

Suggested fix: add `new_rejects_extent_larger_than_bitmap` constructing an undersized `Pmm` and asserting `Err(PmmError::OutOfRange)`; optionally add the exact-fit boundary case (`total_frames == N * 8` must succeed).

#### C2-006 — `cap_map`'s intermediate-table `OutOfFrames` path is only exercised through `FakeMmu` (which never allocates intermediates), so the leaf-vs-intermediate frame-ownership contract is untested at this layer
`kernel/src/mm/address_space.rs:719-737` and tests at `:1152-1268`

`cap_map` passes `pmm` as the `&mut dyn FrameProvider` to `mmu.map(...)`, which (in the real `QemuVirtMmu`) pulls intermediate L1/L2/L3 frames from it and, per the `Mmu::map` failure contract (hal/src/mmu/mod.rs:368-388, clause 3), may *retain* those intermediates inside the AS on an `Err` while leaving the leaf `pa` un-consumed (clause 2). The `FakeMmu` used in every `cap_map` test (test-hal/src/mmu.rs:148-177) has no intermediate tables and ignores the `_frames` provider entirely, so the host tests verify the happy path, the `MisalignedAddress` pass-through, and `WrongKind` — but never drive a `MmuMapError(OutOfFrames)` through `cap_map`, and therefore never observe the partial-intermediate-allocation behaviour that task_loader's rollback path (and any future caller) depends on.

Why it matters: this is the wrapper that brings UNSAFE-2026-0025 (real page-table descriptor writes) into play; the `Mmu::map` failure-semantics contract is "load-bearing for unsafe-free callers" per the HAL doc. The contract is tested at the BSP layer and via task_loader's rollback tests, but the `cap_map` wrapper's own behaviour under intermediate-frame exhaustion is not pinned at this module's boundary.

Suggested fix: add a `FakeMmu`-based variant (or a small purpose-built fake) whose `map` consumes from the provider and returns `OutOfFrames` when the provider is empty, then assert `cap_map` returns `Err(MmuMapError(OutOfFrames))` and that the flush token is *not* discharged on the error path (the `?` at line 734 returns before `token.flush`, which is correct — worth pinning). This also documents, by test, that `cap_map` makes no rollback promise about intermediate frames (consistent with the HAL contract).

### Nit

#### C2-007 — `Pmm::new`'s inverted-range guard is partly shadowed by saturating `frame_count`
`kernel/src/mm/pmm.rs:218-220`

Validation (iv)'s inverted-range check (`if range.end.0 < range.start.0 { return Err(OutOfRange) }`) runs *after* the extent-bounds check at lines 215-217. For an inverted range, `PhysFrameRange::frame_count()` already returns 0 (via `len_bytes()`'s `saturating_sub`, mod.rs:66-81), so even without this guard an inverted range would mark zero bits and contribute zero to `reserved_count` — harmless. The explicit guard is defensible as fail-fast, but its placement and the doc wording ("non-inverted (`range.end >= range.start`)") imply it is the primary defence when in fact the saturating arithmetic already neutralises the case. Also note the guard returns `OutOfRange` while the doc-comment (lines 156-159) groups inversion under "page-aligned … fits inside … and is non-inverted" without naming which error inversion yields; the prose could be read as MisalignedAddress.

Suggested fix: keep the guard (it is the more honest "reject malformed input" stance), but tighten the doc to state explicitly that an inverted reserved range returns `OutOfRange`, and note that it is defence-in-depth on top of the zero-length saturating behaviour.

#### C2-008 — Private bitmap helpers use panic-on-OOB `bitmap[byte]` indexing under a "caller's responsibility" contract in a panic-denied crate
`kernel/src/mm/pmm.rs:661-687`

`set_bit`/`read_bit`/`clear_bit`/`first_zero_bit` index with `bitmap[byte]` (panicking on out-of-bounds) and document the bound as the caller's responsibility. The bound is in fact upheld everywhere (alloc scans `hint..total_frames`; free computes from a validated PA; `new` from validated ranges; all bounded by the line-196 size check). This is a deliberate, reasonable perf choice. The nit is only that the kernel crate denies `clippy::panic`/`unwrap`/`expect`, and a raw index is a latent panic site whose safety rests entirely on the C2-005 invariant; a `debug_assert!(byte < bitmap.len())` in each helper would document the contract and catch a future mis-call in debug/Miri without any release cost.

Suggested fix: add `debug_assert!(idx / 8 < bitmap.len(), "bitmap index out of range")` (or equivalent) at the top of each helper. Mirrors the `debug_assert!(idx < ENTRIES_PER_TABLE)` discipline the BSP MMU walker already uses (per UNSAFE-2026-0025).

#### C2-009 — Test names omit the `test_<subject>_<condition>_<expected>` prefix the testing standard prescribes
`kernel/src/mm/pmm.rs:710+`, `kernel/src/mm/address_space.rs:817+`

testing.md §Test naming fixes the convention as `test_<subject>_<condition>_<expected_outcome>` (e.g. `test_capability_table_full_returns_caps_exhausted`). The track's tests use the descriptive-but-prefixless form (`new_rejects_overlapping_reserved_ranges`, `cap_map_installs_mapping_and_flushes_tlb`). The names are clear and arguably better than the prescribed form, and the deviation is project-wide (task_loader and test-hal do the same), so this is not a track-specific defect — but it is a documented standard the code does not follow.

Suggested fix: project-level decision — either update testing.md to bless the prefixless convention actually in use, or rename. Not worth churning this track alone; flagging for the standards-vs-practice reconciliation that a master review should surface.

#### C2-010 — `PhysFrameRange::frame_count` / `len_bytes` assume page-aligned bounds but the type does not enforce it; `contains` + arithmetic are total, so this is documentation-only
`kernel/src/mm/mod.rs:63-88`

`frame_count` documents "Assumes both bounds are page-aligned (caller's responsibility)" and `len_bytes` treats inverted ranges as zero. Callers in pmm.rs validate alignment via `is_aligned()` before relying on `frame_count`, so no live issue. The nit: `PhysFrameRange` carries raw `PhysAddr` and is `pub` with `pub` fields and a `pub const fn new` that performs no validation, so a caller can construct an unaligned or inverted range and call `frame_count` and get a truncating result. This is by design (mod.rs:33-37 "soft invariant; the BSP validation layer is canonical"), but a one-line note on `new` pointing at "validate via `Pmm::new` / `is_aligned` before trusting `frame_count`" would close the loop for a reader who reaches `new` first.

Suggested fix: add a sentence to `PhysFrameRange::new`'s doc noting it performs no alignment/ordering validation and that `frame_count`/`len_bytes` are only meaningful for page-aligned, non-inverted bounds.

#### C2-011 — `MmuMapError` / `MmuUnmapError` distinction in `AddressSpaceError` adds two variants where the wrapped `MmuError` already discriminates direction by context
`kernel/src/mm/address_space.rs:262-265`

`AddressSpaceError` carries both `MmuMapError(MmuError)` and `MmuUnmapError(MmuError)`. The doc (lines 222-228) justifies preserving the underlying taxonomy without flattening, which is correct and good. The nit is the *map-vs-unmap* split specifically: a caller already knows whether it called `cap_map` or `cap_unmap`, so the directional discriminator carries information the call site already has, and error-handling.md §Error-type design checklist asks "does each variant represent a distinct case a caller could handle differently?" A caller that wants to branch on `OutOfFrames` vs `AlreadyMapped` reads the inner `MmuError` either way; one wrapping variant `Mmu(MmuError)` would suffice. This is genuinely borderline (the split does aid `Debug` output and matches the `cap_map`/`cap_unmap` symmetry), so it is a nit, not a recommendation to change.

Suggested fix: none required; if a future cleanup pass touches this enum, consider whether a single `Mmu(MmuError)` variant is clearer. Documenting the deliberate choice (already mostly done) is sufficient.

### Praise

#### C2-012 — Exemplary `unsafe` discipline at the PMM zero-fill site
`kernel/src/mm/pmm.rs:380-438`

The SAFETY block is a model of the unsafe-policy.md §1 contract: it states why `unsafe` is needed (no safe expression of "zero this PA range" without an equally-unsafe slice materialisation), enumerates five concrete invariants (alignment by construction, exclusive ownership proven by the just-set bitmap bit, identity-mapping per ADR-0027, `isize::MAX` non-overflow, single-core no-peer-observer), walks four rejected alternatives with reasons (not just "this is faster"), and cites a live audit entry (UNSAFE-2026-0026) whose body in `docs/audits/unsafe-log.md` matches the comment precisely. This is exactly the standard the policy asks for and rarely gets.

#### C2-013 — Frame-accounting integrity is anchored against the bitmap, not self-consistency
`kernel/src/mm/pmm.rs:299-307` and test `:1056-1083`

`stats()` deliberately reports `total_frames` from `self.extent.frame_count()` rather than summing the three cached counters, so a counter-drift bug surfaces as a stats-vs-extent disagreement instead of silently re-establishing internal consistency (a classic accounting-bug-hider). The `stats_parity_with_bitmap_bit_count` test then cross-checks `reserved + allocated == popcount(bitmap)`. This is precisely the right invariant to pin for a cached-counter allocator, and it would catch the most likely class of regression.

#### C2-014 — No-ambient-authority preflight ordering in `cap_create_address_space` closes every frame-leak path structurally
`kernel/src/mm/address_space.rs:530-676`

The wrapper resolves the parent cap, checks DERIVE / no-widening / derivation-depth, and preflights *both* the arena and the cap-table for capacity, all **before** the single `pmm.alloc_frame()` (line 600). Because `FrameProvider` has no `free_frame`, this ordering is what makes the post-alloc steps' failure arms (steps 6/7) structurally unreachable in v1 — the depth preflight (step 2c) in particular prevents a `cap_derive`-time `DerivationTooDeep` from leaking an already-allocated root frame. The reasoning is documented step-by-step and pinned by `cap_create_rejects_too_deep_parent_without_consuming_pmm`, which asserts `pmm.remaining() == 1` on rejection. This is careful, security-first sequencing (P1) with a regression test that would catch a re-ordering.

#### C2-015 — `could_yield_pa_overlapping`'s deliberate over-approximation is correct and the reasoning is load-bearing
`kernel/src/mm/pmm.rs:520-563` and test `:1127-1174`

The helper queries extent + reserved-ranges only and intentionally does **not** consult the live bitmap to filter out currently-`Allocated` frames — because an `Allocated` frame becomes a yield candidate again the moment its owner frees it, so a soundness argument that depended on allocation timing would be fragile. Treating "non-reserved frame ⇒ might be yielded" keeps the non-overlap proof for UNSAFE-2026-0027 independent of timing. The `treats_allocated_frame_as_yieldable` test pins exactly this, with both the positive (allocated → still reported) and negative (reserved → excluded) cases. This is the right call for a memory-safety-supporting predicate, and the docstring explains the trade-off and the false-positive escape hatch for callers.

## Claims register

| Claim | Source `file:line` | How to verify |
|-------|--------------------|---------------|
| PMM alloc is O(N) worst-case, amortised O(1) via hint | `pmm.rs:309-362`; ADR-0035 §Decision outcome | Read `alloc_frame`: forward scan `hint..total_frames` then wrap `0..hint`; both linear in frame count. Hint advances on alloc (`:367`), rewinds on free (`:511-513`). Matches ADR-0035 row 1/3. |
| Free is O(1) bit-clear + O(populated_reserved) defensive scan | `pmm.rs:479-518` | `free_frame` iterates `reserved_ranges.iter().flatten()` (`:498`) = populated slots only, then a single `read_bit` + `clear_bit`. Reserved scan is O(≤R); R=8 for bsp-qemu-virt. |
| Allocated frames are zero-filled before return (FrameProvider contract) | `pmm.rs:436-438`; test `:898-961` | `write_bytes(pa_ptr, 0, PAGE_SIZE)`. Test pre-poisons backing with 0xA5 and asserts all 4096 bytes are 0 post-alloc. Cross-ref UNSAFE-2026-0026 status note + T-019 amendment (runtime smoke-verified). |
| `extent.start` page-alignment ⇒ every returned frame is page-aligned | `pmm.rs:185-187, 376-377, 460` | `Pmm::new` rejects unaligned extent (validation i); `idx * PAGE_SIZE` preserves alignment; `PhysFrame::from_aligned` re-checks. Provably-Some at `:460`. |
| Bitmap-size invariant `total_frames <= N*8` guards all index math | `pmm.rs:196-198` | The only bound feeding `set_bit`/`read_bit`/`clear_bit` argument range. NOT directly unit-tested (see C2-005). |
| Overlapping reserved ranges are rejected (half-open pairwise) | `pmm.rs:223-237`; test `:755-790` | `a.start < b.end && b.start < a.end` over i<j. Test covers overlap, duplicate, and accepts touching `[a,b)+[b,c)`. |
| `free_frame` rejects reserved-frame and double-free without bitmap corruption | `pmm.rs:494-507`; test `:991-1020` | Reserved scan returns `DoubleFree` before bit-clear; already-0 bit returns `DoubleFree`. Test asserts both + unchanged counters. |
| `free_frame` rejects PA outside extent before index arithmetic | `pmm.rs:483-485`; test `:1177-1194` | `!self.extent.contains(pa)` fail-fast prevents `saturating_sub` underflow / OOB index. Test covers below-start and at/above-end. |
| `could_yield_pa_overlapping` frame-range math is off-by-one-correct for half-open ranges | `pmm.rs:604-624` | end_idx = ceil((clipped_end - start)/PAGE). Trace: [0,4096)→idx{0}; [0,4097)→{0,1}; 1-byte→{0}. Verified no boundary off-by-one. |
| `cap_create_address_space` allocates the PMM frame only after arena+table+depth preflight | `address_space.rs:570-600`; test `:1310-1379` | All capacity/rights/depth checks precede `alloc_frame` at `:600`. Test asserts `pmm.remaining()==1` after `DerivationTooDeep`. |
| AS cap is minted as a derivation-tree *child* (revocation cascades) | `address_space.rs:665-669`; test `:1272-1308` | Uses `table.cap_derive(parent,...)` not `insert_root`. Test revokes parent, asserts child no longer resolves. |
| Bootstrap AS handle deterministically names arena slot 0, gen 0 | `address_space.rs:59-60`; `arena.rs:57-73` | `BOOTSTRAP_ADDRESS_SPACE_HANDLE = from_slot(SlotId::first_slot())` = (0,0); first `Arena::allocate` returns gen 0 (arena.rs `:153`). Discipline: BSP must allocate bootstrap AS first. |
| StaleHandle resolution via generation tag | `address_space.rs:730-731, 774-775`; `arena.rs:163-184` | `get_address_space_mut` → `Arena::get_mut` returns None on generation mismatch. Tests `arena_get_with_stale_handle_returns_none`, `cap_map`/`cap_unmap` StaleHandle arms. |
| `cap_map`/`cap_unmap` discharge the MapperFlush token (TLB invalidate) | `address_space.rs:735, 779`; test `:1152-1173, :1249-1254` | `token.flush(mmu)`. FakeMmu records `tlb_address_invalidations`; tests assert `==vec![va]` (map) and `vec![va,va]` (map+unmap). |
| Activation hook is wired and fail-soft on stale handle | `address_space.rs:370-386`; `bsp-qemu-virt/src/main.rs:363` | `activate_address_space_handle` no-ops + `debug_assert!(false)` on stale; BSP calls it from the context-switch closure. |
| `Mmu::create_address_space` call site satisfies the `unsafe fn` precondition (aligned+zeroed+exclusive) | `address_space.rs:600-640` | SAFETY block at `:604-639` cites PhysFrame alignment, UNSAFE-2026-0026 zero-fill, stack-frame exclusivity. Matches HAL contract hal/src/mmu/mod.rs:330-335. |
| Audit tags referenced by the track exist and match | `pmm.rs:429`, `address_space.rs:469/640`, `mod.rs:107/152` → `unsafe-log.md:544,566` | UNSAFE-2026-0026 (PMM zero-fill) and 0027 (loader copy) present with matching Operation/Invariants; 0025 (MMU map writes) at `:516`. |
| `phys_frame_kernel_ptr` is a safe cast; only the deref at call sites is unsafe | `mod.rs:165-169` | `frame.as_usize() as *mut u8` — infallible integer→pointer cast. Single forward-compat indirection point for ADR-0033. Adopted by task_loader (`task_loader.rs:666`); PMM site intentionally not yet routed (mod.rs:152-159). |

## Cross-track notes

- **HAL contract dependency (track for `hal/` + BSP).** `cap_map`'s soundness for unsafe-free callers rests on `Mmu::map`'s failure-semantics contract (hal/src/mmu/mod.rs:353-409, clauses 1-3): on `Err`, no mapping at `va`, `pa` not consumed, intermediates may be retained. task_loader's rollback (`task_loader.rs:682-704, 737-741`) and any future `cap_map` caller free the leaf frame on map-failure relying on clause 2. A BSP `Mmu::map` impl that writes the leaf descriptor before its last fallible step would create UB through safe code. The MM track is correct *given the contract*; verifying the `QemuVirtMmu::map` impl actually upholds clauses 1-3 belongs to the HAL/BSP track (UNSAFE-2026-0025).

- **Caps track.** The wrappers depend on `CapabilityTable::{lookup, cap_derive, depth_of, is_full, cap_revoke, cap_drop}` and `MAX_DERIVATION_DEPTH` (cap/table.rs). `cap_create_address_space`'s leak-freedom proof assumes `cap_derive` re-checks DERIVE/no-widening/depth and that `is_full`/`depth_of` are accurate — confirmed present (cap/table.rs:143,246,317,427,482,491; MAX_DERIVATION_DEPTH=16). The caps track should confirm `cap_derive`'s only post-preflight-failure arm is `InvalidHandle` (as the MM doc claims at address_space.rs:658-664).

- **task_loader track (obj/).** Principal external consumer of both files. It takes `&mut Pmm<N,R>` concretely (not `&mut dyn FrameProvider`) specifically to reach `Pmm::free_frame` for rollback (task_loader.rs:419-421) — a deliberate coupling worth noting in that track. The `could_yield_pa_overlapping` C2-003 perf concern is presently masked because task_loader passes a 1-frame range; if a future loader supports large images this becomes live.

- **Arena track (obj/arena.rs).** `AddressSpaceArena<M>` is `Arena<AddressSpace<M>, 8>`; all stale-handle/capacity guarantees the MM track relies on are arena properties (generation bump on `free`, `is_full`, `allocate` returns None when full). Confirmed sound.

- **Test-hal track.** `FakeMmu::map` ignores the `FrameProvider` and has no intermediate tables (test-hal/src/mmu.rs:148-177), which is why C2-006 (intermediate-frame `OutOfFrames` through `cap_map`) is untested at this layer. If the test-hal grows a frame-consuming fake, the MM track should add the corresponding `cap_map` exhaustion test.

- **Docs/ADR track.** ADR-0028 §Negative consequence and §Simulation row 3 describe `QemuVirtMmu::activate` as doing a full `TLBI VMALLE1` (no per-task ASID, `TCR_EL1.AS=0`); the MM-side `activate_address_space_handle` correctly delegates to `Mmu::activate` and adds nothing. The TLB-coherency correctness lives in the BSP `activate` impl, not in this track.

## Coverage checklist

- [x] `kernel/src/mm/pmm.rs` — read in full (1195 lines). PMM struct, `PmmError`, `PmmStats`, `Pmm::new`, `extent`, `stats`, `alloc_frame` (+ SAFETY), `free_frame`, `could_yield_pa_overlapping`, `FrameProvider` impl, bitmap helpers, `force_alloc_failure_after`, and all `#[cfg(test)]` tests.
- [x] `kernel/src/mm/address_space.rs` — read in full (1380 lines; two reads: 1-1137 then 1138-1380). `AddressSpace<M>`, `wrap_bootstrap`/`from_mmu_address_space`/`root_frame`/`inner`/`inner_mut`, `AddressSpaceHandle`, `AddressSpaceArena<M>`, `AddressSpaceError`, `create_address_space`/`destroy_address_space`/`get_address_space`/`get_address_space_mut`, `activate_address_space_handle`, `resolve_address_space_cap`, `cap_create_address_space` (+ SAFETY), `cap_map`, `cap_unmap`, and all `#[cfg(test)]` tests.
- [x] `kernel/src/mm/mod.rs` — read in full (169 lines). Module docs, `PhysFrameRange` (`new`/`is_aligned`/`len_bytes`/`frame_count`/`contains`), re-exports, `phys_frame_kernel_ptr` (+ forward-compat doc).

Total in-scope lines reviewed: 2744 (1195 + 1380 + 169).
