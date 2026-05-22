# C1-kernel-cap — capability subsystem (master review, commit 288ddb2)

## Summary

The capability subsystem is in **strong health**. It faithfully implements ADR-0014 (index-based arena, generation-tagged handles, embedded derivation tree, cascading revocation), is genuinely `unsafe`-free and `no_std`/heap-free, enforces narrowing-only rights and per-operation authority checks before any side effect, and is supported by a thorough unit-test suite (38 tests in `table.rs`, 7 in `rights.rs`) that covers the adversarial cases the project's testing standard asks for (widening, missing-rights, stale-handle, exhaustion, depth cap, sibling-list integrity, cascade). No Blockers. The headline issues are all **Minor/Nit**: one backwards-ordered write in `free_slot` that is a latent free-list-corruption hazard if a future caller ever passes an out-of-range index (currently unreachable), a couple of error-code-conflation spots where genuine internal-bug paths reuse `InvalidHandle`, a small documentation/code gap around peer-of-root revocation asymmetry, and an O(n) `references_object` scan that is correct-but-watch as the table or call frequency grows. **Verdict: approve** — the subsystem is mergeable as-is; the findings below are polish and forward-flags, not gates.

## Findings

### Blocker

None.

### Major

None.

(One item below — C1-001 — is `Minor (forward-flagged)`: a latent correctness hazard that is unreachable under current callers but should be corrected before any caller can pass an attacker- or bug-influenced index to `free_slot`.)

### Minor

**C1-001 — `free_slot` updates `free_head` *before* the bounds check, corrupting the free list on an out-of-range index** — `kernel/src/cap/table.rs:575-585`
`free_slot` sets `self.free_head = Some(index)` on line 577, *then* does the bounds check `self.slots.get_mut(index as usize)` on line 579 with an early `return` on line 580.

```rust
fn free_slot(&mut self, index: Index) {
    let old_free_head = self.free_head;
    self.free_head = Some(index);              // (1) head updated first
    let Some(slot) = self.slots.get_mut(index as usize) else {
        return;                               // (2) ...but on OOB we bail here
    };
    slot.entry = None;
    slot.generation = slot.generation.wrapping_add(1);
    slot.next_free = old_free_head;           // (3) never runs on the OOB path
}
```
If `index >= CAP_TABLE_CAPACITY`, the function leaves `free_head = Some(<oob>)` while the slot's `next_free` is never wired to `old_free_head`. The result is doubly broken: (a) the prior free list is orphaned (every previously-free slot is leaked), and (b) the next `pop_free()` executes `self.slots[head as usize]` (table.rs:568) with an out-of-range index → kernel panic (an out-of-bounds index, which on a `[Slot; N]` is a bounds-check panic).
**Why it matters.** This is the security heart of the kernel and the data-structure-integrity invariant is load-bearing. Today every caller (`cap_drop`, `cap_take`, `cap_revoke`) derives `index` from `resolve_handle`/the validated tree walk, so the OOB branch is unreachable and this is latent — hence Minor, not Blocker. But the ordering is simply backwards: the `Some(index)` head update should be the *last* write, gated on the bounds check succeeding. The current shape means a single future mistake (a caller computing an index, an `Index`-width change, a refactor that frees a raw index) silently converts into free-list corruption instead of a clean no-op.
**Suggested resolution.** Reorder so the head is only published after the slot is confirmed in-range:
```rust
fn free_slot(&mut self, index: Index) {
    let Some(slot) = self.slots.get_mut(index as usize) else {
        debug_assert!(false, "free_slot called with out-of-range index");
        return;
    };
    slot.entry = None;
    slot.generation = slot.generation.wrapping_add(1);
    slot.next_free = self.free_head;
    self.free_head = Some(index);
}
```
(The borrow of `self.free_head` after `get_mut` needs a small reshuffle — read `let old = self.free_head;` before the `get_mut`, assign `slot.next_free = old;`, then `self.free_head = Some(index);` after the block.) A `debug_assert!` on the OOB branch matches the project's existing pattern in `cap_revoke` (table.rs:357) for "this means an internal bug."

**C1-002 — `references_object` is an O(n) full-table scan invoked from object-destroy paths; cost compounds across many watcher tables** — `kernel/src/cap/table.rs:531-536`
`references_object` iterates all `CAP_TABLE_CAPACITY` slots (`self.slots.iter().filter_map(...).any(...)`). The doc-comment acknowledges this ("linear in `CAP_TABLE_CAPACITY`; acceptable at Phase A's scale", table.rs:526-527). The ADR-0016 reachability check (per the comment at table.rs:520-529, and `obj/mod.rs:48,99`) calls this per *candidate destroy* against every *watcher table*, so the real cost is O(tables × CAP_TABLE_CAPACITY).
**Why it matters.** Not a bug, and explicitly documented as a Phase-A trade. But it is the one operation in this module whose complexity is not bounded by a small constant or the derivation subtree — it is bounded by the whole capability space, replicated per watcher table. As the number of tasks (= tables) grows, object destruction becomes O(total capabilities in the system). Flagging so the perf pass tracks it.
**Suggested resolution.** Acceptable to keep for now. When the watcher-set grows, consider a reverse index (object → set of referencing slots) or a per-object refcount maintained at `insert_root`/`cap_derive`/`free_slot`. No change required this round; record as a known scaling item alongside the ADR-0023 cross-table-CDT deferral, which touches the same "who references this object across tables" question.

**C1-003 — `unlink_from_siblings` returns `InvalidHandle` for an internal-bookkeeping inconsistency, conflating a real bug with a normal stale-handle error** — `kernel/src/cap/table.rs:629-631` (also the inner `None` arms at 603 and the take's `entry.take()` fallback at 470)
When the sibling walk falls off the end of the parent's child list without finding `index`, the code returns `Err(CapError::InvalidHandle)` with the comment "the parent's child list is inconsistent. The latter is an internal bug." (table.rs:629-631). The same `InvalidHandle` value is what a *legitimate* stale handle produces.
**Why it matters.** error-handling.md §7 ("Preserve root cause… Do not collapse distinct… failures") and the testing standard's "an error path has a test that provokes it" both push toward distinguishing "user gave me a dead handle" from "my own tree is corrupt." Today `cap_drop`/`cap_take` reach `unlink_from_siblings` only *after* `resolve_handle` has already validated the handle, so a returned `InvalidHandle` from the *walk* can only mean internal corruption — yet it is indistinguishable from the ordinary case by the caller, and there is no `debug_assert!` to surface it in tests (unlike the analogous corruption guard in `cap_revoke` at table.rs:357/381).
**Suggested resolution.** Add a `debug_assert!(false, "parent child-list inconsistent")` before the `Err(CapError::InvalidHandle)` on table.rs:631 (and at the `None`-parent-entry arm on 603), mirroring the `cap_revoke` cycle/duplicate guard. This keeps the release behavior conservative (still returns an error, does not corrupt state) while making the "this is a bug, not a stale handle" case loud in test/CI. A dedicated `CapError` variant (e.g. `Corrupt`) is *not* recommended — it would widen the public error surface for a should-never-happen path; the `debug_assert!` is the right weight.

**C1-004 — Peer-of-a-root is itself a root, so `cap_revoke` on the original root cannot reach the peer; the asymmetry vs. peer-of-a-child is untested and only implicitly documented** — `kernel/src/cap/table.rs:170-229` (`cap_copy`), tree shape; contrast test `copy_of_a_child_shares_parent` (table.rs:895-906)
`cap_copy` installs the peer "at the same position in the derivation tree as the source" (table.rs:158-160): same `parent`, same `depth`. For a *child* source the peer shares the parent, so revoking the parent kills both (covered by `copy_of_a_child_shares_parent`). For a *root* source (`parent == None`), the peer is a second independent root. There is therefore **no capability that can `cap_revoke` a peer-of-a-root via the local CDT** — the original root's `cap_revoke` only walks *its own* descendants, and the peer is a sibling root, not a descendant.
**Why it matters.** This is a real security-relevant lifecycle property, not a bug — it is the within-table analogue of the cross-table revocation gap that ADR-0023 defers. A reviewer or future caller could wrongly assume "revoke the source root → its `cap_copy` peers die too." The behavior is correct under ADR-0014's model (peers are siblings; revoke is subtree-only), but it is only *implicitly* documented and has no test pinning it.
**Suggested resolution.** (a) Add a one-line note to `cap_copy`'s doc-comment: "A peer of a *root* capability is itself an independent root; `cap_revoke` on the original root does not reach it (peers are siblings, and revoke is subtree-only)." (b) Add a test `cap_copy_of_root_then_revoke_root_leaves_peer_alive` symmetric to `copy_of_a_child_shares_parent`, asserting the peer survives `cap_revoke(root)`. This pins the documented asymmetry and feeds the contradiction pass (the claim "revoke kills all copies" must be scoped to "copies that are descendants").

**C1-005 — ADR-0014's `CapError` enum (the contract) lists 5 variants; the implementation has 7 (`HasChildren`, `WrongKind`) — the ADR is now stale against the code** — `kernel/src/cap/mod.rs:161-192` vs. ADR-0014 lines 120-134
`mod.rs` defines `CapError` with `HasChildren` (mod.rs:180-183) and `WrongKind` (mod.rs:184-191) in addition to the five the ADR enumerates. Both additions are legitimate (`HasChildren` enforces the "don't orphan children on drop" rule from `cap_drop`'s contract; `WrongKind` lands with T-018 per the comment) and `#[non_exhaustive]` makes them non-breaking. But ADR-0014's "Core types" block (the canonical contract) still shows the 5-variant enum and the old `CapObject(u64)` placeholder / `CapKind` without `AddressSpace`.
**Why it matters.** P8 / ADR-0025 treat ADRs as the decision of record; the documentation-accuracy dimension asks whether doc matches code. The drift is benign (additive, well-commented in code) but the ADR no longer reflects the implemented surface. The code-side comments already explain *why* each addition exists, which is good.
**Suggested resolution.** This is an **ADR-hygiene** item, not a code change — out of scope for editing in this track, but flagged for the contradiction/cross-track pass: ADR-0014's type listing should be reconciled (the ADR is append-only for *decisions*, so the right move is a short amending note or a follow-up ADR, per ADR-0025, not an in-place edit of the original body). `mod.rs` itself is fine. Cross-reference: the same staleness affects the `CapObject(u64)` placeholder, which the code (mod.rs:87-99, ADR-0016) has already replaced with the typed enum.

### Nit

**C1-006 — `CapRights` operator surface is asymmetric: `BitOrAssign` exists but no `BitAndAssign`; no `Sub`/`Not`** — `kernel/src/cap/rights.rs:109-127`
`BitOr`, `BitAnd`, and `BitOrAssign` are implemented, but there is no `BitAndAssign` (despite `intersection` existing and being the natural narrowing op), nor `Sub`/`SubAssign` (despite `difference` existing). Minor ergonomic asymmetry: a caller can write `rights |= X` but must write `rights = rights & X` for narrowing.
**Why it matters.** Pure ergonomics; nothing is broken. Narrowing (intersection / difference) is arguably the *more* security-relevant direction for a rights bitfield, so it is slightly odd that the in-place form exists only for the widening (`|=`) direction.
**Suggested resolution.** Optional: add `BitAndAssign` (delegating to `intersection`) for symmetry, or leave it and rely on the named `intersection`/`difference` methods. If kept method-only, that is a defensible "make narrowing explicit, not operator-sugar" stance — in which case consider whether `BitOrAssign` should likewise be dropped for symmetry. Either direction is fine; the current mix is the only nit.

**C1-007 — `from_raw` / `raw` / `KNOWN_BITS` / `difference` / `is_empty` have no non-test callers yet; their doc-comments assert ABI-boundary behavior that no ABI exercises today** — `kernel/src/cap/rights.rs:43-107`
`KNOWN_BITS` (rights.rs:43-51), `from_raw` (rights.rs:67-70), `raw` (rights.rs:74-76), `difference` (rights.rs:98-100), and `is_empty` (rights.rs:104-106) are currently used only from the rights unit tests (`empty()` *is* used externally, in `mm/address_space.rs`). `from_raw`'s doc makes a forward-looking security claim ("a hostile or buggy caller cannot use them to weaken `contains`/subset checks", rights.rs:63-66) about an ABI boundary that does not exist pre-userspace.
**Why it matters.** This is *intended* forward-looking API surface (the masking behavior in `from_raw` is genuinely the right design for the future syscall/ABI layer, and the test `from_raw_masks_unknown_bits` already pins it). It is not accidental dead code. The only nit is that the claims are currently unverified by any real caller, so the contradiction pass should treat them as "design intent, not yet load-bearing." No removal warranted — removing and re-adding at the ABI boundary would be churn.
**Suggested resolution.** Leave as-is. Optionally annotate the cluster with a `// Used at the ABI boundary (T-0xx, userspace); test-only today.` marker so a future dead-code audit does not mistake them for cruft. The masking design and its test are a strength (see Praise).

**C1-008 — `cap_copy` and `cap_derive` duplicate the "read parent's first_child, splice as new head, repoint parent.first_child" logic** — `kernel/src/cap/table.rs:202-223` vs. `285-302`
The child-list prepend sequence (read `former_first_child`, write the new `SlotEntry` with `next_sibling: former_first_child`, then set `parent_entry.first_child = Some(new_index)`) appears nearly verbatim in `cap_copy` (table.rs:202-223) and `cap_derive` (table.rs:285-302). The only differences are `cap_copy`'s `parent` is an `Option` (it may be a root, hence the `match parent { Some/None }`) while `cap_derive` always has a concrete parent.
**Why it matters.** Maintainability only. The two copies must stay in lockstep for the linked-list invariants `cap_revoke`/`unlink_from_siblings` rely on; a divergence between them would be a subtle tree-corruption bug. The duplication is small and currently correct.
**Suggested resolution.** Optional: extract a private helper, e.g. `fn link_child(&mut self, new_index: Index, parent: Option<Index>)` that reads the parent's current `first_child`, sets the new slot's `next_sibling`, and repoints `first_child`. Both call sites would then share one implementation of the invariant. Low priority; do not over-abstract if it obscures the per-call-site error handling (`cap_copy`'s `None => return Err(InvalidHandle)` parent-entry guard at table.rs:205).

**C1-009 — Doc-comment math claim "`new_depth_usize` fits in `u8` because `MAX_DERIVATION_DEPTH ≤ u8::MAX`" is correct but relies on an un-asserted relationship** — `kernel/src/cap/table.rs:275`
The truncating cast `new_depth_usize as u8` (table.rs:280) is justified by the comment "`MAX_DERIVATION_DEPTH ≤ u8::MAX`" (table.rs:275). `MAX_DERIVATION_DEPTH` is `16` (table.rs:26), so this holds, and the depth-cap check on table.rs:272 guarantees `new_depth_usize ≤ MAX_DERIVATION_DEPTH` before the cast. But unlike `CapabilityTable::new`, which encodes its bound as a `const { assert!(CAP_TABLE_CAPACITY <= Index::MAX as usize) }` (table.rs:108), there is no compile-time assertion that `MAX_DERIVATION_DEPTH <= u8::MAX`.
**Why it matters.** Defensive-correctness nit. If a future ADR raises `MAX_DERIVATION_DEPTH` above 255 (the ADR explicitly contemplates loosening the cap — ADR-0014 "Open questions"/Consequences), the `depth: u8` field (table.rs:76) and this cast both silently overflow/truncate, and the only signal would be a wrong depth, not a build error.
**Suggested resolution.** Add `const { assert!(MAX_DERIVATION_DEPTH <= u8::MAX as usize) };` near the cast (or once in the module), matching the `const { assert!(...) }` idiom already used in `new`. This converts the future foot-gun into a hard build error, consistent with the project's "either failure is a hard build error rather than a runtime panic" stance (table.rs:106-107).

### Praise

**C1-P1 — Checks strictly precede side effects in every mutating operation.** `cap_copy` (rights/DUPLICATE/widening checks at table.rs:188-193 *before* `pop_free` at 196), `cap_derive` (DERIVE/widening/depth at 263-274 *before* `pop_free` at 282), `cap_revoke` (REVOKE at 325-327 *before* the BFS), and the IPC integration (`take_cap_if_some` is called *after* the queue-full pre-check, ipc/mod.rs:300-303) all order authority and validity checks ahead of any allocation or state mutation. This is exactly the "checks before side effects" discipline the security dimension asks for, and it makes the error paths leave the table unmutated (verified by tests like `cap_derive_on_full_table_returns_caps_exhausted` asserting the parent stays live, table.rs:1106).

**C1-P2 — Move-only capability discipline is enforced by the type system, not by convention.** `Capability` derives only `Debug` (mod.rs:123) — deliberately not `Copy`/`Clone` (mod.rs:114-119) — so duplication is *only* possible through `cap_copy` (which gates on `DUPLICATE`) and transfer is *only* possible through `cap_take` (move out) + `insert_root` (move in), as the IPC layer uses it (ipc/mod.rs:536-560). This realizes ADR-0014's "move-only discipline, enforced by Rust" driver concretely and is the strongest single property in the subsystem.

**C1-P3 — `from_raw` masks unknown bits, closing a real ABI smuggling vector before the ABI exists.** `CapRights::from_raw` ANDs incoming bits with `KNOWN_BITS` (rights.rs:68-70), so a future untrusted caller cannot set reserved bits to weaken `contains`/subset checks. The test `from_raw_masks_unknown_bits` (rights.rs:179-188) pins both the masking and the "purely-reserved-bits collapses to EMPTY" edge. Designing the masking in *now*, with a test, rather than retrofitting it at the syscall layer, is the conservative security-first choice the project's rules demand.

**C1-P4 — The `cap_revoke` BFS carries a written size-proof and a release-safe overflow guard.** The comment block at table.rs:329-347 proves the scratch array (`[0; CAP_TABLE_CAPACITY]`) cannot overflow (each live node has exactly one parent and appears in one sibling chain, so ≤ CAP_TABLE_CAPACITY distinct indices), and the loops pair a `debug_assert!` (loud in tests) with a `break` on the bound (conservative in release) so a bookkeeping bug "cannot be escalated to a revocation that silently fails to free memory" (table.rs:337-339). This is model defensive coding for a security-critical walk.

**C1-P5 — Test suite covers the adversarial and edge cases the standards demand.** Beyond happy paths, the suite hits: widening rejection (`cap_copy_rejects_widened_rights`, `cap_derive_rejects_widened_rights`), missing-authority (`*_without_*_right_fails`), stale-handle on every entry point (`cap_copy_on_stale_handle`, `cap_take_stale_handle`, `lookup_on_stale_handle`, `cap_revoke_on_stale_handle`), exhaustion on both `insert_root` and `cap_derive`, the depth cap, generation bump on reuse for both `cap_drop` and `cap_take`, and — notably — sibling-list integrity under head/middle removal with a follow-up `cap_revoke` to prove the list still walks (`drop_first_child_updates_parent_first_child_pointer`, `cap_take_middle_sibling_preserves_list_integrity`). The T-011 targeted-branch block (table.rs:1056-1078) documents *why* each gap-closing test exists. This meets testing.md's "provoke every error path" bar.

## Claims register

| Claim | Source `file:line` | How to verify |
|---|---|---|
| Module contains no `unsafe` and no heap | `kernel/src/cap/table.rs:6-7` | `rg -n "unsafe\|alloc\|Box\|Vec" kernel/src/cap/` returns nothing in non-comment code; confirmed by read — true. |
| Handle lookup is O(1) (direct slot index + generation compare) | `resolve_handle` table.rs:541-553 | Single `slots.get(index)` + two field compares; no loop. True. |
| Use-after-revoke is structurally impossible (stale handle fails generation check) | mod.rs:166-169; ADR-0014:198 | `free_slot` bumps `generation` (table.rs:583); `resolve_handle` compares it (table.rs:546). Tests `freed_slot_is_reused_with_bumped_generation`, `drop_twice_returns_invalid_handle`. True. |
| `cap_copy`/`cap_derive` cannot widen rights | rights.rs:11-14; doc table.rs:166-168, 241-242 | `if !rights.contains(new_rights) { return Err(WidenedRights) }` (table.rs:191-193, 266-268). Tests `*_rejects_widened_rights`. True. |
| `cap_copy` requires `DUPLICATE`; `cap_derive` requires `DERIVE`; `cap_revoke` requires `REVOKE` | table.rs:188-190, 263-265, 325-327 | Explicit `contains` checks before any allocation/mutation. Tests `*_without_*_right_fails`. True. |
| Revocation invalidates the entire descendant subtree but preserves `src` | doc table.rs:310; ADR-0014:178-179 | BFS frees all descendants (table.rs:398-401), then clears `src.first_child` (table.rs:404-406); `src` slot untouched. Tests `cap_revoke_removes_only_descendants`, `cap_revoke_cascades_depth_three`. True. |
| Revocation BFS scratch array cannot overflow | table.rs:329-347 (size proof) | Proof: one parent per node, one sibling chain → ≤ CAP_TABLE_CAPACITY distinct indices; array sized at CAP_TABLE_CAPACITY; `debug_assert!`+`break` guards (table.rs:357-363, 381-387). Sound. |
| `cap_drop` refuses interior nodes (will not orphan children) | doc table.rs:413-418; mod.rs:180-183 | `if has_children { return Err(HasChildren) }` (table.rs:434-436). Test `cap_drop_on_interior_node_returns_has_children`. True. |
| `cap_take` moves the capability out and invalidates the handle (move-only transfer) | doc table.rs:443-454 | `entry.take()` (table.rs:467-470) + `free_slot` (473) → generation bump; returns `Capability` by value. Test `cap_take_returns_capability_and_invalidates_handle`. True. |
| `cap_take` is the atomic-removal half of IPC capability transfer | table.rs:446-448; ipc/mod.rs:33-36, 300-303 | `take_cap_if_some` calls `cap_take` after queue pre-checks; failure leaves endpoint state unchanged. Test `ipc_send` HasChildren regression (ipc/mod.rs:904-925). True for the *removal* side; see Cross-track note re: receiver-side re-rooting. |
| Capability is move-only (not `Copy`, not `Clone`) | mod.rs:114-127 (only `#[derive(Debug)]`) | No `Copy`/`Clone` derive or impl; duplication only via `cap_copy`. True (compiler-enforced). |
| `from_raw` masks bits outside `KNOWN_BITS` so reserved bits cannot weaken checks | rights.rs:59-70 | `Self(bits & Self::KNOWN_BITS.0)`. Test `from_raw_masks_unknown_bits`. True. |
| `references_object` returns true iff a *live* capability names the target; cleared by drop/revoke | doc table.rs:520-529 | Iterates `entry.as_ref()` (skips freed slots) comparing `object()`. Tests `references_object_sees_live_caps_only`, `cap_revoke_clears_references_object`. True. |
| `references_object` is linear in CAP_TABLE_CAPACITY | table.rs:526-527 | Full `slots.iter()` scan. True; see C1-002 for the per-watcher-table multiplier. |
| `depth_of` returns 0 for a root, +1 per derive; used as an mm preflight | doc table.rs:496-507 | `insert_root` sets `depth:0` (table.rs:153); `cap_derive` sets `parent_depth+1` (table.rs:271). Caller mm/address_space.rs:571 preflights before PMM. True. |
| Derivation depth is hard-capped at MAX_DERIVATION_DEPTH (16) | table.rs:21-26, 270-274 | `if new_depth_usize > MAX_DERIVATION_DEPTH { Err(DerivationTooDeep) }`. Test `cap_derive_enforces_depth_cap`. True. |
| Table capacity is a compile-time constant (64) | table.rs:13-19 | `pub const CAP_TABLE_CAPACITY: usize = 64;`. True; matches ADR-0014:59. |
| `CapKind`/`CapObject` discriminators match 1:1 for kinds with live storage; `MemoryRegion` reserved | mod.rs:46-99 | `CapKind` has 5 variants; `CapObject` has 4 (no `MemoryRegion`); `CapObject::kind()` total match (mod.rs:104-111). True. |
| `CapError` is `#[non_exhaustive]` so new variants are non-breaking | mod.rs:161 | Attribute present. True. |
| Revocation is per-table-transitive only; transferred caps are not reachable from sender's CDT | ADR-0023:11-13 | `insert_root` on the receiver side makes the moved cap a root (parent=None, depth=0), severing the link (ipc/mod.rs:549-560). Consistent with the deferral. True — see Cross-track. |
| `CapError` enum has the 5 variants ADR-0014 specifies | ADR-0014:120-134 | **Stale** — implementation has 7 (`HasChildren`, `WrongKind` added). See C1-005. |

## Cross-track notes

- **For the IPC track (and security pass): receiver-side re-rooting of transferred caps.** When a derived capability is transferred via IPC, the receiver installs it with `insert_root` (`ipc/mod.rs:549-560`), which sets `parent = None`, `depth = 0`. The transferred cap therefore becomes a *root* in the receiver's table, losing its original depth and any parent linkage. This is correct under ADR-0023's per-table-only-revocation deferral, but it has two consequences worth confirming in the IPC/security pass: (1) a cap that was deep in the sender's tree re-enters the receiver's tree at depth 0, so the receiver could derive a *fresh* MAX_DERIVATION_DEPTH-deep chain from it — the depth cap is per-table, not global; (2) the sender's `cap_revoke` can never reach the receiver's copy (the documented ADR-0023 gap). Neither is a bug; both should be explicitly acknowledged by the contradiction pass against any doc claiming "revoke kills all copies" globally.
- **For the contradiction pass: ADR-0014 type listing is stale (C1-005).** ADR-0014's "Core types" block shows a 5-variant `CapError`, the old `CapObject(u64)` placeholder, and a `CapKind` without `AddressSpace`. The implemented code (mod.rs) has diverged additively (all changes are well-commented and ADR-referenced in code). The ADR is the decision-of-record; reconcile via an amending note / follow-up ADR per ADR-0025 (do not edit the append-only body in place). The same staleness affects ADR-0023:47 ("Capability slot is currently 32 bytes per ADR-0014") — verify against the current `SlotEntry` layout (table.rs:71-77: `Capability` + 3×`Option<u16>` + `u8`) during the perf/contradiction pass.
- **For the perf pass: `references_object` O(tables × capacity) (C1-002).** Tracked here as the one non-subtree-bounded operation in the module. Pairs naturally with the ADR-0023 cross-table-CDT question (both are "who references this object across tables").
- **For the security pass: confirm `WrongKind` is enforced by *callers*, not the cap table.** `CapError::WrongKind` is defined in `cap/mod.rs` but never *returned* by `cap/table.rs`; the kind-mismatch checks live in `mm/address_space.rs` (resolvers at 426-430, 543) and `obj/task_loader.rs:516`. The cap table itself does no kind-checking on lookup (by design — `lookup` returns the raw `&Capability` and callers match on `object()`). Worth a uniform-trust-boundary check in the security pass: every caller that resolves a typed cap must match the variant; verify none rely on the table to enforce kind. (IPC's `validate_ep_cap`/`validate_notif_cap` do this correctly, ipc/mod.rs:503-534.)

## Coverage checklist

- [x] `kernel/src/cap/table.rs` — read in full (1188 lines; confirmed via `wc -l` = 1188).
- [x] `kernel/src/cap/mod.rs` — read in full (192 lines; confirmed via `wc -l` = 192).
- [x] `kernel/src/cap/rights.rs` — read in full (197 lines; confirmed via `wc -l` = 197).

Context also read in full or in relevant part: ADR-0014 (capability-representation), ADR-0023 (cross-table revocation), standards (code-review, architectural-principles, error-handling, testing, code-style); caller call-sites inspected in `kernel/src/ipc/mod.rs`, `kernel/src/mm/address_space.rs`, `kernel/src/obj/{mod,task,task_loader}.rs`, `kernel/src/sched/mod.rs`.
