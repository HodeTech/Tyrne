# C4-kernel-task-loader — task loader (master review, commit 288ddb2)

## Summary

**Verdict: APPROVE (no Blocker, no Major).** The task loader
(`kernel/src/obj/task_loader.rs`, 2271 lines) and the kernel crate root
(`kernel/src/lib.rs`, 57 lines) are in unusually good shape. The loader is
the product of six recorded review rounds plus two follow-up commits, and it
shows: the preflight chain, the integer-overflow discipline, the rollback
contract, the single audited `unsafe` block, and the row-to-test mapping are
all carefully built and cross-referenced to ADR-0029 / T-019 / the unsafe
log.

The track brief frames this as a "trust boundary for untrusted image data."
The load-bearing observation is that **ADR-0029 makes the image a raw-flat
byte stream with zero structured metadata** — offset 0 is the entry
instruction; every other byte is `copy_nonoverlapping`-ed verbatim into a
freshly-zeroed frame. There is therefore **no parser and no
attacker-controllable structured-input surface** in v1. The only inputs the
loader interprets are scalars (`image_base_va`, `stack_size_pages`,
`parent_as_cap`, `new_rights`), and each is validated or has its validation
correctly delegated. All such inputs originate from trusted BSP compile-time
constants today; the "untrusted" framing is forward-looking (B5+ filesystem
modules), and the loader is correctly scoped for that future without
over-building it now.

Correctness review of the security-relevant arithmetic found **no overflow,
truncation, off-by-one, or over-mapping defect**. Every size/offset/VA
computation uses saturating primitives or total operations (`div_ceil`,
`is_multiple_of`); the VA-range bound, the exact intermediate-frame budget,
and the PA-overlap preflight are each individually sound and were
cross-checked against the actual `Pmm`, `cap_map`/`cap_unmap`/
`cap_create_address_space`, the HAL `Mmu::map` failure contract, and the BSP
`walk_or_alloc_table` lazy-allocation behaviour. Mapping permissions respect
W^X per region (image `USER|EXECUTE`, stack `USER|WRITE`). The rollback
contract is implemented exactly as documented, including the deliberate v1
leaks.

Findings are all **Minor / Nit** (documentation-completeness and
test-coverage gaps on delegated paths) plus several **Praise** items.

Severity counts: **Blocker 0, Major 0, Minor 4, Nit 4, Praise 6.**

## Findings (by severity)

### Blocker

None.

### Major

None.

### Minor

#### C4-001 — `WidenedRights` is a reachable delegated error that `load_image`'s docs and tests both omit

`kernel/src/obj/task_loader.rs:332-337` (the `AddressSpaceCreationFailed`
doc-comment) and `:584-586` (the call site).

`load_image` threads `new_rights` straight into
`cap_create_address_space`, whose **step 2b**
(`kernel/src/mm/address_space.rs:558-561`) enforces a no-widening rule:
`if !parent_cap.rights().contains(new_rights) { return
Err(CapError::WidenedRights); }`. So a caller that passes a `new_rights`
set not held by `parent_as_cap` gets
`LoadError::AddressSpaceCreationFailed(AddressSpaceError::CapError(
CapError::WidenedRights))`.

The `AddressSpaceCreationFailed` doc-comment enumerates the delegated
failure modes as "`CapError::InsufficientRights` if `parent_as_cap` lacks
DERIVE, plus the T-018-guarded `CapsExhausted` / `DerivationTooDeep` /
`ArenaFull` paths" — **`WidenedRights` is missing** from that list, even
though it is just as reachable as `InsufficientRights` and is arguably the
*more* likely caller mistake (asking for rights the parent doesn't hold).
The T-019 task file's `AddressSpaceCreationFailed` bullet
(`docs/analysis/tasks/phase-b/T-019-task-loader.md:43`) has the same
omission.

**Why it matters.** A reviewer or future caller reading the variant's
doc-comment to understand "what can `cap_create_address_space` fail with"
will not learn that a widened-rights request is rejected here. For a
security-first kernel where the rights lattice is the core authority model,
silently under-documenting a no-widening rejection on the AS-creation path
is a real (if low-severity) documentation gap.

**Suggested fix.** Add `WidenedRights` to the `AddressSpaceCreationFailed`
doc-comment's delegated-variant list (and to the T-019 bullet), e.g.
"...covers `CapError::InsufficientRights` (parent lacks DERIVE),
`CapError::WidenedRights` (`new_rights ⊄ parent_cap.rights`), plus the
T-018-guarded `CapsExhausted` / `DerivationTooDeep` / `ArenaFull` paths."

#### C4-002 — No test exercises the delegated DERIVE-adjacent rejection beyond the missing-DERIVE case

`kernel/src/obj/task_loader.rs:1471-1527`
(`missing_derive_surfaces_via_address_space_creation_failed`) is the only
test that drives the `AddressSpaceCreationFailed` path, and it only covers
the `InsufficientRights` (missing-DERIVE) sub-case. Every other test in the
module passes `new_rights = CapRights::empty()`, so:

- the `WidenedRights` delegated path (C4-001) is **never executed** by the
  host test suite, and
- the happy-path mint with a **non-empty** `new_rights` (the realistic B5+
  shape, where the loaded AS cap actually carries rights) is never
  exercised — every passing test mints an AS cap with `empty()` rights.

**Why it matters.** testing.md §"What has tests" expects distinct
caller-discriminable error cases to be pinned; `WidenedRights` is a distinct,
reachable variant on a security-relevant (rights-lattice) path with zero
coverage. The §Simulation row-5 verification artefacts pin only the
missing-DERIVE leg of the delegation.

**Suggested fix.** Add a `widened_rights_surfaces_via_address_space_creation_failed`
test (parent cap holding, say, `DERIVE` only; call with
`new_rights = CapRights::DERIVE | CapRights::REVOKE`; assert
`AddressSpaceCreationFailed(CapError(WidenedRights))` and PMM byte-stable),
and a happy-path variant that mints with a non-empty `new_rights` and asserts
the returned `as_cap` resolves with those rights.

#### C4-003 — `kernel/src/lib.rs` `## Subsystems` rustdoc omits the entire `mm` subsystem (and the loader's home in `obj`)

`kernel/src/lib.rs:21-33`.

The crate declares `pub mod mm;` (line 55), but the `## Subsystems`
doc-list documents only `obj`, `cap`, `ipc`, and `sched`. **`mm` — the home
of the PMM (ADR-0035), the `AddressSpace<M>` object (ADR-0028), and every
dependency the task loader composes — is entirely absent** from the
crate-root subsystem list. Separately, the `obj` bullet
(`:21-22`) still describes obj as the A3-era "per-type arenas holding the
concrete entities that capabilities name" and links only Phase-A tasks
(T-001..T-004); it does not mention that `obj` now also hosts B4's
`task_loader`.

**Why it matters.** The crate root is the canonical entry point a reader hits
first (and CLAUDE.md directs agents to read it). A B-phase reader looking for
"where does memory management live" gets no pointer from the rustdoc, and the
`mm` ↔ `obj::task_loader` composition that is the whole of B4 is invisible at
the top level. documentation-style.md's accuracy expectation is not met for
the two newest subsystems.

**Suggested fix.** Add an `mm` bullet to `## Subsystems` (Phase B / T-017 +
T-018, PMM + `AddressSpace<M>`), and extend the `obj` bullet to note the B4
`task_loader` resident (or at least add the relevant B-phase task links).

#### C4-004 — `intermediate_frame_count`'s "exact" guarantee is BSP-coupled but lives in a HAL-agnostic kernel module

`kernel/src/obj/task_loader.rs:90-95, 113-122, 126-156`.

`intermediate_frame_count` hard-codes the VMSAv8 21/30/39 bit-shifts and
relies on the BSP's `walk_or_alloc_table` allocating an intermediate frame
**only** when the parent entry is invalid (verified at
`bsp-qemu-virt/src/mmu.rs:464-479` — the lazy path). The function's docstring
is candid about this ("exact for a BSP that lazy-allocates ... a BSP that
pre-allocates more aggressively would observe this count as a lower bound"),
and v1 has a single aarch64 BSP, so the count is exact today.

The architectural concern (P6 — HAL separation) is that a **kernel-core**
module now encodes a page-table-format constant *and* a BSP allocation-policy
assumption. If a second BSP (or a RISC-V `Sv39` port) lands without satisfying
the lazy-allocation contract, this becomes a **silent budget undercount** —
the `FrameBudgetExceeded` preflight would pass, then `cap_map` would fail mid-
loop with `MmuError::OutOfFrames`, surfacing as `MapFailed` and forcing the
rollback path (which the loader handles correctly, but the preflight's whole
purpose is to make that path structurally unreachable). The docstring already
names the right escape hatch (`Mmu::intermediate_frames_for_span` on the HAL).

**Why it matters.** This is a forward-looking maintainability/architecture
risk, not a v1 defect. It is worth a tracked note so the "exact budget"
invariant is revisited the moment a second BSP or page-table format appears,
rather than discovered via a mid-loop allocation failure.

**Suggested fix.** No code change for v1. Add a one-line forward-flag (an ADR
rider or a `// FORWARD:` comment) that the exact-budget contract must move to
a HAL method, or be re-derived per format, before a second BSP/translation
regime lands. Optionally `debug_assert!` in `load_image` that the post-loop
PMM delta equals `1 + image_pages + stack_pages + intermediate_budget` under
the lazy BSP, to catch budget drift in host/Miri runs.

### Nit

#### C4-005 — Production surface (~824 lines) is healthy; the 2271-line file size is dominated by tests

`kernel/src/obj/task_loader.rs` overall.

Per the brief's "assess whether it should be decomposed": lines 66-823 are
production code (helper + `load_image` + `rollback`); the remaining ~1447
lines are the `#[cfg(test)]` module. `load_image` itself is a single linear
state machine with a justified `#[allow(clippy::too_many_lines)]`
(`:474-480`) whose reason — preserving the §Simulation row-to-code mapping —
is sound. **No decomposition is warranted**; splitting the state machine into
one-helper-per-row would obscure exactly the mapping reviewers verify against.
The only mild observation is that the test module is large enough that a
future reader benefits from the section banners already present (which the
author has provided). Recorded as a Nit purely to answer the brief's
decomposition question: the answer is "no, keep it."

#### C4-006 — `OutOfFrames` doc-comment says "mid-image-or-stack-loop" but the variant is shared; consider naming both injection mechanisms

`kernel/src/obj/task_loader.rs:357-366`.

The `OutOfFrames` doc-comment notes the variant is "structurally unreachable
post-`FrameBudgetExceeded` preflight" and retained defensively — accurate. A
reader auditing how the defensive path is *tested* must cross to
`task-loader.md` to learn it is driven by `Pmm::force_alloc_failure_after`.
Minor polish: a one-line "exercised in tests via
`Pmm::force_alloc_failure_after`" pointer in the variant doc (mirroring how
the unsafe block points at its audit entry) would keep the
defensive-path-coverage story self-contained.

#### C4-007 — `LoadError` derives are correct but `result_large_err` is worth a glance

`kernel/src/obj/task_loader.rs:256-376`.

`LoadError` is `Copy` and `#[non_exhaustive]` per error-handling.md §2/§"error
checklist" — good. Its largest variant wraps `AddressSpaceError` (which itself
wraps `CapError`/`MmuError`, both small `Copy` enums) or carries
`{ base, end }` (two `VirtAddr` = 16 bytes). The type is comfortably under the
~128-byte `clippy::result_large_err` warn threshold, so this is not a defect —
noted only to confirm the dimension was checked. No action.

#### C4-008 — Module-doc and `load_error_variants_pattern_match_exhaustively` test both say "10-variant"; keep them in lockstep with the enum

`kernel/src/obj/task_loader.rs:2095` (test comment "Pin the 10-variant
taxonomy") and the enum at `:258-376`.

The test enumerates all ten variants in an explicit array + exhaustive match,
so adding/removing a variant breaks the test at compile time (excellent — this
is the right mechanism). The Nit is only that the *prose* "10-variant" count
also appears in `current.md` and the task file; those prose counts are not
compiler-checked and have already drifted once in this arc (8 → 9 → 10). No
change needed in-track; flagging the cross-file prose-count fragility for the
docs track.

### Praise

#### C4-P1 — Exhaustive integer-overflow discipline on every size/offset/VA computation

Every arithmetic operation on attacker-/caller-influenced quantities uses
saturating primitives or total operations: `image.len().div_ceil(PAGE_SIZE)`
(`:525`), `saturating_add`/`saturating_mul` for the VA span and frame budget
(`:536-557`), `is_multiple_of` for alignment (`:505`), and the documented
`usize::MAX` saturation sentinel for the VA-range overflow path
(`:539-544`). This is exactly the discipline `error-handling.md` /
`#![deny(clippy::arithmetic_side_effects)]` demand, and it is applied
uniformly with no gaps. The `intermediate_frame_count` helper is likewise
fully saturating and has an explicit zero-span guard (`:132-135`).

#### C4-P2 — The PA-overlap preflight is a genuinely strong, mechanically-enforced safety boundary

`:563-579` discharges `UNSAFE-2026-0027`'s "source and destination do not
overlap" invariant at runtime via `Pmm::could_yield_pa_overlapping`, replacing
a previously documentation-only BSP-layout argument. Crucially, because the
check covers the *entire* allocatable extent (extent minus reserved), it is
sound for **all** subsequent `alloc_frame` returns — root, intermediates, and
leaves — not just the leaf-copy site the SAFETY comment narrates. Running it
once before the loop is therefore both sufficient and minimal. Converting a
"trust the BSP linker script" invariant into a typed fail-fast rejection is a
model of the security-first posture.

#### C4-P3 — The single `unsafe` block carries a textbook SAFETY comment and is the only one in the production path

`:624-668`. The SAFETY comment states why unsafe is needed, enumerates four
numbered invariants (slice validity, identity-mapping via the centralised
`phys_frame_kernel_ptr` helper, in-bounds write, runtime-enforced
non-overlap), explicitly rejects three safer alternatives (`write_volatile`,
`from_raw_parts_mut`, HAL relocation), and cites the audit entry — fully
conformant with unsafe-policy.md §1/§7. `task-loader.md:140` confirms the loader
has "exactly one block"; everything else (preflights, both `cap_map` paths,
rollback, construction) is safe Rust. Routing the destination pointer through
`crate::mm::phys_frame_kernel_ptr` so the future ADR-0033 high-half migration
touches one helper is excellent forward-design.

#### C4-P4 — Rollback contract is implemented exactly as specified, including honest leak accounting

`rollback` (`:795-823`) unwinds stack-then-image in reverse install order via
`cap_unmap` + `free_frame`, swallows secondary errors (correct — a rollback
error must not mask the primary failure), and uses `cap_drop` (not
`cap_revoke`) with a precise justification for the leaf-cap case
(`:455-461`). The forward path frees the failing iteration's leaf frame
*before* invoking `rollback`, relying on `Mmu::map` clause 2 ("`pa` not
consumed on Err", `hal/src/mmu/mod.rs:362-388`) — and the code comment
(`:684-690`) explicitly names that the trait contract is the load-bearing
safety argument. The v1 leaks (root L0 + intermediates + arena slot) are
documented in the variant docs, the function rustdoc, T-019, and
`task-loader.md`, all consistently. This four-way cross-reference is what a
high-assurance audit trail should look like.

#### C4-P5 — `intermediate_frame_count` is exact, and the regression that motivated it is pinned by a worked-example test

The helper replaced an off-by-one hard-coded constant (`6`) that
under-counted whenever the image span crossed more than one 2 MiB L2 slot.
The fix is the *exact* distinct-table count per VMSAv8 index decomposition
(`:142-155`), and the precise reviewer counter-example (8 MiB image crossing
5 L2 slots ⇒ 7 intermediates) is encoded as
`intermediate_frame_count_8mib_image_one_stack_page_crosses_five_l2`
(`:1202-1214`), alongside L1-boundary-crossing, minimal, zero-span, and
saturated-input cases. I independently re-derived the shift→level mapping
against the BSP walker and confirm the count is exact for the v1 BSP.

#### C4-P6 — Test suite pins every §Simulation row, the rollback paths, and the malformed/adversarial scalar inputs

The 33 host tests cover: empty image, zero stack, misaligned base (PMM
byte-stable), stale/wrong-kind parent cap, VA-limit boundary (both the
accepted `== LIMIT` edge and the rejected past-limit + saturated-overflow
sentinel), VA-range-before-frame-budget ordering, PA-overlap (with a
`.rodata`-resident disjoint companion that asserts rather than silently
skips), tail-zeroing on a partial page, USER|EXECUTE vs USER|WRITE flag pins,
and all three rollback shapes (mid-image `cap_map` fail via `FailingMapMmu`,
mid-stack `cap_map` fail, mid-loop `alloc_frame` exhaustion via
`force_alloc_failure_after`). The adversarial *scalar* surface
(`stack_size_pages = usize::MAX`, near-`usize::MAX` base, off-by-one
misalignment) is well covered — appropriate given the raw-flat format has no
structured bytes to fuzz. The two coverage gaps are the delegated rights paths
in C4-002.

## Claims register

| Claim | Source `file:line` | How to verify |
|-------|--------------------|---------------|
| Image is raw-flat with no parsed metadata; offset 0 = entry; bytes copied verbatim | `task_loader.rs:1-9`, ADR-0029 §Decision outcome `docs/decisions/0029-...:36-40` | Read ADR-0029; confirm loader does no byte interpretation beyond `copy_nonoverlapping` (`:664-668`) and `entry_va = image_base_va` (`:768`). **Verified.** |
| `intermediate_frame_count` is *exact* for the v1 lazy-allocating BSP | `task_loader.rs:90-95` | Cross-read `bsp-qemu-virt/src/mmu.rs:464-479` (`walk_or_alloc_table` allocates only when `DESC_VALID_BIT == 0`). **Verified** — exact for v1; lower-bound for an eager BSP (see C4-004). |
| VMSAv8 shift→level mapping (21=L3, 30=L2, 39=L1) is correct | `task_loader.rs:142-155` | Compare against `hal/src/mmu/mmu mod`/BSP `VA_L*_SHIFT` (`bsp-qemu-virt/src/mmu.rs:50-53`): L0=39,L1=30,L2=21,L3=12. Helper counts distinct *parent indices*, so l1_count↔shift39 etc. **Verified consistent.** |
| `span_end == USERSPACE_VA_LIMIT` is the accepted half-open boundary | `task_loader.rs:540-545`, `:1161-1185` | T0SZ=16 ⇒ valid VA `[0, 2^48)`; a frame at `[LIMIT-PAGE, LIMIT)` has top byte `2^48-1`, addressable. Test `accepts_..._minus_span` passes. **Verified.** |
| `Mmu::map` does not consume `pa` on Err (clause 2) — the rollback `free_frame(frame)` is safe | `task_loader.rs:684-691`, `hal/src/mmu/mod.rs:362-388` | Read the HAL trait failure-semantics contract; confirm BSP `map` writes the leaf descriptor only after all fallible steps (`bsp-qemu-virt/src/mmu.rs:434-447`). **Verified.** |
| Intermediate L1/L2/L3 frames leak on rollback in v1 | `task_loader.rs:449-453`, `hal/src/mmu/mod.rs:368-376` | HAL clause 3 explicitly permits retaining intermediates on Err; `cap_unmap` removes leaf only. **Verified** (deliberate v1 baseline). |
| Non-overlap of `copy_nonoverlapping` is runtime-enforced for all later allocations | `task_loader.rs:563-579`, `pmm.rs:520-626` | `could_yield_pa_overlapping` covers extent-minus-reserved; every `alloc_frame` return is within that set ⇒ disjoint from image. **Verified** (stronger than the SAFETY comment claims). |
| `could_yield_pa_overlapping` over-approximates (ignores live bitmap) | `pmm.rs:542-563` | Read the §Conservatism doc; the helper does not consult `Allocated` bits. Harmless for the loader (image is `.rodata`, not a staged Allocated frame). **Verified — not a loader defect.** |
| DERIVE check is delegated to `cap_create_address_space` step 2a; surfaces as `AddressSpaceCreationFailed(InsufficientRights)` | `task_loader.rs:16-21, 509-517`, `address_space.rs:555-557` | Read step 2a; test `missing_derive_..._failed` (`:1471-1527`). **Verified.** |
| No-widening (`WidenedRights`) is *also* delegated but undocumented in the loader | `address_space.rs:558-561` vs `task_loader.rs:332-337` | Step 2b returns `WidenedRights`; loader docs omit it. **Verified gap → C4-001/C4-002.** |
| No `unwrap`/`expect`/`panic` on the production path | `task_loader.rs:66-823` | grep confirms all such tokens are inside `#[cfg(test)]` (allowed via `:826-832`). `lib.rs:47-50` denies them crate-wide. **Verified.** |
| Loader has exactly one `unsafe` block in production | `task_loader.rs:664-668`, `task-loader.md:140` | grep `unsafe ` in `:66-823` → one block. **Verified.** |
| 33 host tests; "10-variant" `LoadError` | `task_loader.rs` (33 `#[test]`), `:258-376` | `grep -c '#\[test\]'` = 33; enum has 10 variants; `task-loader.md:144` says 33. **Verified.** |
| BSP smoke call uses `new_rights = CapRights::empty()` (passes no-widening) | `bsp-qemu-virt/src/main.rs:1056` | `empty ⊆ any` ⇒ step 2b passes; BSP `.expect(...)` is an init-path expect permitted by error-handling.md §4. **Verified — out of track.** |

## Cross-track notes

- **C2 (kernel-mm) / PMM + AddressSpace:** This track depends heavily on
  `cap_map`, `cap_unmap`, `cap_create_address_space`
  (`kernel/src/mm/address_space.rs`), and `Pmm::{alloc_frame, free_frame,
  stats, could_yield_pa_overlapping, extent}` (`kernel/src/mm/pmm.rs`). I
  read those signatures and contracts to validate the loader's claims, but
  the implementations themselves are C2's review surface. Two items the
  mm-track reviewer should confirm independently: (a) `cap_create_address_space`
  step 2b `WidenedRights` (relevant to C4-001/C4-002 — the loader correctly
  delegates, but the contract should be co-documented); (b) `phys_frame_kernel_ptr`
  (`kernel/src/mm/mod.rs:165-169`) is `pub(crate)` and infallible-by-design —
  the loader's identity-mapping invariant rides on it.

- **HAL track:** The loader's rollback safety leans on `Mmu::map` clause 2 +
  clause 3 (`hal/src/mmu/mod.rs:353-389`). That contract text is the HAL
  track's surface; the loader is a correct *consumer* of it. The
  load-bearing comment at `task_loader.rs:684-690` correctly identifies a BSP
  clause-2 violation as the one way to turn this safe code unsound.

- **BSP track:** `intermediate_frame_count`'s exactness is coupled to
  `bsp-qemu-virt/src/mmu.rs` `walk_or_alloc_table` lazy allocation (C4-004).
  If the BSP reviewer is also looking at a future second BSP, flag the
  coupling there too.

- **Docs track:** Prose variant-count "10-variant" and test-count "33"
  appear in `current.md`, `task-loader.md`, and the T-019 task file; these
  are not compiler-checked and have drifted before (C4-008). The `mm`
  subsystem omission in `lib.rs` (C4-003) is a code-doc issue I fixed-scope
  to this track, but the broader "crate-root rustdoc is A-phase-era" pattern
  may recur in other module roots the docs track covers.

## Coverage checklist

- [x] `kernel/src/obj/task_loader.rs` — **read in full** (2271 lines / 2272
  reported by reader incl. trailing newline; read across pages 1-1184 and
  1184-2271). Production code lines 1-823 (module doc, `intermediate_frame_count`,
  `USERSPACE_VA_LIMIT`, `LoadedImage`, `LoadError`, `load_image`, `rollback`)
  and the full `#[cfg(test)]` module lines 825-2271 all reviewed.
- [x] `kernel/src/lib.rs` — **read in full** (57 lines).

**Context read (read-only, for verification — not part of the two track
files):** `docs/decisions/0029-initial-userspace-image-format.md`,
`docs/architecture/task-loader.md`,
`docs/analysis/tasks/phase-b/T-019-task-loader.md`, `kernel/src/mm/mod.rs`,
`kernel/src/mm/pmm.rs` (alloc/free/stats/extent/could_yield_pa_overlapping),
`kernel/src/mm/address_space.rs` (cap_create_address_space / cap_map /
cap_unmap / resolve_address_space_cap / AddressSpaceError),
`kernel/src/cap/table.rs` (cap_drop / lookup / is_full),
`kernel/src/cap/mod.rs` (CapError / Capability::{kind,object,rights}),
`hal/src/mmu/mod.rs` (Mmu::map failure contract, MmuError, MappingFlags),
`bsp-qemu-virt/src/mmu.rs` (walk_or_alloc_table lazy allocation),
`bsp-qemu-virt/src/main.rs` (load_image call site),
`docs/standards/{unsafe-policy,error-handling,architectural-principles,
code-review,testing}.md`, `docs/roadmap/current.md`, and read-only git log /
blame for the T-019 commit arc (8 commits across 6 review rounds).
