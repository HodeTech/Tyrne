# C3-kernel-ipc-obj — IPC & kernel objects (master review, commit 288ddb2)

## Summary

This track covers the IPC primitive layer (`kernel/src/ipc/mod.rs`) and the kernel-object
type system it sits on top of (`kernel/src/obj/{mod,endpoint,notification,task,arena}.rs`).
The code is in very good shape: it is 100% safe Rust (the one audited `unsafe` in the
`obj` subtree lives in `task_loader`, which is outside this track), the pre-flight discipline
that ADR-0017 §"Capability transfer rationale" and `docs/architecture/ipc.md` §Invariants
demand is correctly implemented, and the security-critical properties (a sender cannot
transfer authority it does not hold; capability checks precede every side effect; the move-only
`Capability` is never duplicated) hold up under close reading and adversarial test review.
The rendezvous state machine, the `ReceiverTableFull` pre-flight, the stale-generation reset,
the `TRANSFER`-right enforcement, and the ADR-0032 `ipc_cancel_recv` rollback are each backed
by focused tests, several of which are genuine adversarial sequences (cancel-on-`RecvComplete`,
recv-with-full-table-then-retry, bad-transfer-cap-preserves-`RecvWaiting`).

I found **no Blocker and no Major** issues. The findings are all Minor / Nit: a small set of
correctness-adjacent gaps in the *kernel-object* layer (no destroy-time reachability or
drain enforcement is wired anywhere in-tree — by design per ADR-0016, but the `Endpoint`
destroy path is reachable from the IPC test and is the exact hazard `reset_if_stale_generation`'s
`debug_assert!` only catches in debug), an asymmetry in the derives on `RecvOutcome` vs
`SendOutcome` that degrades both ergonomics and test rigor, a stale `~990-line` claim in the
architecture doc (the file is 1425 lines), one missing-test gap on the `Notification` arena
slot-reuse path through `ipc_notify`, and the usual pre-alpha dead-code surface
(`Notification::consume`, `Endpoint::id`, the per-kind `get_*` accessors have no production
caller yet). Everything material is either correct or already tracked in an ADR/doc rider for
Phase B. Praise is warranted for the pre-flight ordering and the cap-transfer atomicity tests.

Scope note: the IPC fast path / scheduler-bridge wrappers (`ipc_send_and_yield`,
`ipc_recv_and_yield`) live in `sched/mod.rs` (Track C-sched) — I read them only to verify the
`ipc_cancel_recv` contract and the `PendingAfterResume` decode, and route bridge-side findings
to Cross-track notes rather than raising them here.

## Findings (by severity)

### Blocker

None.

### Major

None.

### Minor

---

**C3-001 — `Endpoint` destroy is reachable but no drain/reachability check guards an in-flight capability; the only safety net is a debug-only `debug_assert!`.**
`kernel/src/ipc/mod.rs:216-233` (`reset_if_stale_generation`); `kernel/src/obj/endpoint.rs:83-88` (`destroy_endpoint`); `kernel/src/ipc/mod.rs:973-1005` (`stale_queue_state_reset_on_slot_reuse` test).

Description. `destroy_endpoint` frees the arena slot and bumps the generation, but it does
*not* consult `IpcQueues`. If an endpoint is destroyed while its `IpcQueues` slot holds
`SendPending { cap: Some(_) }` or `RecvComplete { cap: Some(_) }`, the parked `Capability`
is owned only by the endpoint state (per the module doc at lines 30-37 and `ipc.md` §Invariants
"Move-only capabilities"). On the next `ipc_*` against a *new* endpoint allocated in the same
slot, `reset_if_stale_generation` overwrites the state with `Idle` and the parked `Capability`
is dropped on the floor — a silently leaked authority. In release builds the only thing standing
between this and a real leak is that the `debug_assert!` at lines 220-228 is compiled out.

Why it matters. This is the single most security-relevant gap in the track. A dropped
`Capability` is a loss of authority that no table accounts for; under the move-only invariant
the kernel is supposed to hold exactly one instance, and here it holds zero after destroy. It
is *currently benign* only because (a) no production code calls `destroy_endpoint` with a
cap-bearing pending state — the IPC test at line 985-986 destroys an endpoint that is only in
`RecvWaiting` (no cap), and (b) ADR-0032 §Consequences and the `ipc_cancel_recv` doc-comment
(lines 448-463) explicitly defer the drain primitive to Phase B2+. The code is honest about
this: the doc-comment, the architecture doc §"Open questions" ("Endpoint destruction-with-pending-cap
policy"), and the ADR-0032 rider all flag it. So this is correctly *tracked*, not *unhandled*.
But the reviewer's job is to record that a release-build silent capability leak is reachable
through a `pub fn` (`destroy_endpoint`) the moment any caller frees a cap-bearing endpoint, and
the guard is debug-only.

Suggested fix. No code change is required for v1 correctness, and forcing the drain primitive
now would front-run the Phase B2 destroy ADR. The conservative improvement that does *not*
need that ADR: have `destroy_endpoint` (or a thin wrapper the IPC layer owns) take `&mut IpcQueues`
and return `ObjError::StillReachable` — or a new `ObjError::HasPendingTransfer` — when the slot
holds a `Some(cap)` state, mirroring the caller-managed reachability pattern ADR-0016 already
established for `references_object`. That converts the debug-only assert into a release-safe
typed refusal. At minimum, add a `#[cfg(not(debug_assertions))]`-aware note at the
`destroy_endpoint` site pointing back to the hazard, since today nothing at the destroy site
mentions it.

---

**C3-002 — `RecvOutcome` derives only `Debug`; `SendOutcome` derives `Copy, Clone, Debug, Eq, PartialEq`. The asymmetry forces `let-else`/`matches!` instead of `assert_eq!` and weakens test rigor.**
`kernel/src/ipc/mod.rs:122-139` (`RecvOutcome`) vs `kernel/src/ipc/mod.rs:104-120` (`SendOutcome`).

Description. `RecvOutcome` cannot be compared for equality, so every test that wants to assert
on a received message destructures with `let RecvOutcome::Received { msg, cap: None } = ... else
{ panic!(...) }` and then `assert_eq!(msg, ...)` (e.g. lines 677-680, 715-718, 1071-1074), and
the `Pending` arm is checked with `matches!` (lines 694, 1195, 1209). `SendOutcome`, by contrast,
is asserted directly with `assert_eq!(outcome, SendOutcome::Enqueued)`.

Why it matters. (1) The `let-else { panic! }` shape silently accepts the *wrong cap presence*:
`let RecvOutcome::Received { msg, cap: None }` will `panic!` if a cap unexpectedly *appears*,
which is fine, but several call sites match `cap: Some(recv_cap_h)` and never assert the inner
handle's properties beyond `lookup(...).is_ok()`. A derived `PartialEq` would let tests assert
the *whole* outcome in one expression and make "unexpected `Pending`" a clean equality failure
rather than a `panic!` with a formatted message. (2) It is an API-ergonomics wart: a downstream
syscall layer (Phase B) that wants to compare a recv outcome cannot, and will reinvent the
destructure. The reason for the asymmetry is presumably that `RecvOutcome::Received` carries a
`CapHandle` and the author wanted to keep it lightweight — but `CapHandle` is `Copy + Eq +
PartialEq` (`cap/table.rs:40-44`) and `Message` is `Copy + Eq + PartialEq` (line 67), so
`RecvOutcome` *can* derive all five with no obstacle. `Copy` is the only debatable one (the
struct is two words plus an `Option<CapHandle>`); `Clone + Eq + PartialEq` are free wins.

Suggested fix. Add `#[derive(Clone, Debug, Eq, PartialEq)]` (and `Copy` if the size is
acceptable) to `RecvOutcome`. Then simplify the test destructures to `assert_eq!`. This also
satisfies error-handling.md's design-checklist spirit (consistent derive sets across sibling
result types).

---

**C3-003 — No test exercises `ipc_notify` across a notification-slot generation bump (the `NotificationArena` stale-handle path is untested through the IPC entry point).**
`kernel/src/ipc/mod.rs:408-420` (`ipc_notify`); `kernel/src/obj/notification.rs:142-155` (arena-level stale test exists, but not via `ipc_notify`).

Description. The endpoint side has `stale_queue_state_reset_on_slot_reuse` (lines 973-1005)
proving that a *recreated endpoint* does not inherit stale IPC state and that a stale endpoint
cap is rejected. The notification side has no equivalent: there is no test that destroys a
notification, recreates one in the same slot, and confirms a stale `notif_cap` makes `ipc_notify`
return `IpcError::InvalidCapability` (the `get_mut(...).ok_or(InvalidCapability)` branch at
lines 415-417). The arena-level `destroy_invalidates_handle` test (notification.rs:142) proves
`get_notification` fails on a stale handle, but it does not go through `ipc_notify`, so the
`ok_or(IpcError::InvalidCapability)` mapping at the IPC boundary is uncovered.

Why it matters. testing.md §"What has tests" requires that an error path — "a new variant in an
`Error` enum" — has a test that provokes it, and that public-API contracts be covered. The
`ipc_notify` → stale-handle → `InvalidCapability` edge is the notification analogue of an
already-tested endpoint edge; leaving it uncovered is an inconsistency, and it is exactly the
kind of arena-staleness regression the endpoint test was written to guard against. Note also
that `ipc_notify` validates the *cap* (rights + kind) but resolves the handle against the arena
*after* — a stale handle that still satisfies the cap rights check (e.g. a duplicated cap whose
underlying notification was destroyed) is the realistic adversarial case.

Suggested fix. Add a test mirroring `stale_queue_state_reset_on_slot_reuse`: create a
notification, install a NOTIFY cap, `destroy_notification`, then assert `ipc_notify` with the
old cap returns `IpcError::InvalidCapability`. (A `cap_drop` of the cap is not even required to
provoke the arena-side failure, which makes the test sharper.)

---

**C3-004 — Architecture doc claims the IPC surface "fits in one ~990-line file"; the file is now 1425 lines.**
`docs/architecture/ipc.md:14`; actual `kernel/src/ipc/mod.rs` = 1425 lines.

Description. `ipc.md` §Context states the audit-friendliness argument rests on "the entire IPC
surface fits in one ~990-line file under `unsafe-policy.md` review." The file is 1425 lines
(roughly 560 of which are tests). The `~990` figure predates the T-011 test bundle and the
T-015 / ADR-0032 `ipc_cancel_recv` additions.

Why it matters. code-review.md §"Author's responsibilities" item 7 (the post-fix grep sweep)
exists precisely to catch literals that drift across docs and source; this is a stale literal of
that class. It is a documentation-accuracy nit, not a correctness issue, but the "fits in ~990
lines" claim is load-bearing for the doc's stated rationale (a small auditable surface), so an
out-of-date number undercuts the argument it is making.

Suggested fix. Update to "~1.4k-line file (about 560 lines of which are host tests)" or drop the
specific number in favour of "a single file". Apply the grep sweep for `990` (only this one hit
exists in the doc tree).

---

**C3-005 — `ipc_notify` takes `&CapabilityTable` but `ipc_cancel_recv` also takes `&CapabilityTable`, while `ipc_send`/`ipc_recv` take `&mut`; the inconsistency is correct but undocumented at the type level.**
`kernel/src/ipc/mod.rs:411` (`ipc_notify`, `&CapabilityTable`); `:486` (`ipc_cancel_recv`, `&CapabilityTable`); `:267`/`:346` (`ipc_send`/`ipc_recv`, `&mut CapabilityTable`).

Description. The four IPC entry points split into two groups by table mutability: `send`/`recv`
need `&mut` (they `cap_take` / `insert_root`), while `notify`/`cancel_recv` need only `&`
(they only `lookup` for validation). This is *correct* and is even a small soundness asset — the
scheduler bridge's Deadlock rollback relies on `ipc_cancel_recv` taking `&CapabilityTable` so it
can re-borrow the table as shared while the arena/queues are borrowed `&mut`
(`sched/mod.rs:1158-1163`, and the SAFETY comment there explicitly notes "recovery does not
mutate caller-table state"). But nothing in `ipc/mod.rs` documents *why* two functions take `&`
and two take `&mut`; a future maintainer "tidying" the signatures to a uniform `&mut` would
silently break the bridge's borrow discipline.

Why it matters. The signature asymmetry is a deliberate, security-relevant invariant (it is what
keeps the rollback's borrows non-aliasing), but it reads like an inconsistency. A reader applying
code-style.md's consistency goal might "fix" it and not discover the breakage until Miri fails on
the bridge test.

Suggested fix. Add one sentence to `ipc_cancel_recv`'s and `ipc_notify`'s doc-comments noting that
the `&CapabilityTable` (shared) borrow is intentional and is depended upon by the scheduler
bridge's rollback borrow split. No code change.

### Nit

---

**C3-006 — Pre-alpha dead code: `Notification::consume`, `Endpoint::id`, and the per-kind `get_endpoint`/`get_notification`/`get_task` accessors have no production caller.**
`kernel/src/obj/notification.rs:41-45` (`consume`); `kernel/src/obj/endpoint.rs:31-34` (`id`);
`endpoint.rs:92`, `notification.rs:104`, `task.rs:126` (`get_*`).

Description. `Notification::consume` (the documented "consume half of the wait/notify pair") is
called only from `notification.rs` tests; `ipc_notify` never reads or clears the word, and there
is no `ipc_wait`/`ipc_poll` primitive yet (consistent with ADR-0017 §"`wait` operation" deferral
to A5+ and the `ipc.md` §"Notification waiter wake-up" open question). `Endpoint::id` and the
three `get_*` arena accessors are likewise test-only today. These are pre-alpha scaffolding, not
defects.

Why it matters. P12 (no half-finished subsystems) tolerates documented skeletons; these are
documented (each carries a doc-comment and the module headers say "v1 skeleton"). The note is
recorded only so the master review has a complete dead-code inventory. The risk is purely that an
unused `pub fn` accretes assumptions; clippy's `dead_code` does not fire because they are `pub`.

Suggested fix. None for v1. When the Phase B notification-wait path lands, confirm `consume` is
actually wired (the silent-sleep hazard `ipc_notify`'s doc-comment at lines 395-403 warns about).

---

**C3-007 — `Message` is fully caller-controlled and `#[derive(Default)]`; `params` interpretation is opaque. Correct, but the `Default` derive invites a zero message being mistaken for "no message".**
`kernel/src/ipc/mod.rs:67-73`.

Description. `Message` derives `Default` (all-zero). The kernel never inspects fields (by design,
ADR-0017 §"Message content is opaque"), and the rendezvous machine distinguishes "no message"
structurally (the `EndpointState` variant), not by a sentinel — so a zero `Message` is a perfectly
valid payload and is *not* confused with absence anywhere in this file. The `Default` derive is
used by tests indirectly via `test_msg`. This is fine.

Why it matters. Purely forward-looking: when the syscall ABI marshals `Message` from registers
(Phase B), a `Default`-constructed `Message` could become an accidental "empty" convention. No
action now; flagged so the ABI ADR does not lean on `Message::default()` as a semantic signal.

Suggested fix. None. Optionally drop the `Default` derive if no caller needs it once tests stop
relying on it, to remove the temptation.

---

**C3-008 — `take_cap_if_some` / `install_cap_if_some` collapse `cap_take`'s distinct `CapError` variants into one IPC error each, discreetly losing root cause.**
`kernel/src/ipc/mod.rs:536-560`.

Description. `take_cap_if_some` maps every `cap_take` failure (`InvalidHandle`, `HasChildren`) to
`IpcError::InvalidTransferCap`; `install_cap_if_some` maps every `insert_root` failure
(`CapsExhausted`) to `IpcError::ReceiverTableFull`. error-handling.md §7 ("preserve root cause")
says not to "collapse distinct failures into a generic error." Here the collapse is *mostly*
defensible — from the sender's perspective `InvalidHandle` and `HasChildren` are both "this handle
is not transferable", and `InvalidTransferCap`'s doc (lines 86-87) says "invalid or stale", which
covers both. And the pre-flight at lines 276-283 already lookups the transfer cap, so a bare
`InvalidHandle` is improbable by the time `cap_take` runs; the realistic `cap_take` failure is
`HasChildren` (a derived-from cap). The test `send_with_bad_transfer_cap_preserves_recv_waiting`
(lines 902-941) drives exactly the `HasChildren` → `InvalidTransferCap` path.

Why it matters. A userspace caller (Phase B) that gets `InvalidTransferCap` cannot tell "stale
handle" (retry is pointless) from "has children, revoke first" (retry after `cap_revoke` works).
That is a *handleable distinction* per error-handling.md's checklist. It is a Nit today because
there is no userspace caller, but the lossy mapping is baked into the v1 surface.

Suggested fix. Consider a distinct `IpcError::TransferCapHasChildren` (or carry the inner
`CapError`, mirroring `SchedError::Ipc(IpcError)`'s nesting pattern) so the actionable
"revoke-then-retry" case is distinguishable. `IpcError` is `#[non_exhaustive]`, so adding a
variant is backward-compatible.

---

**C3-009 — `unreachable!()` in `ipc_send` relies on a non-local pre-check; an `expect`-style comment or `debug_assert` would localize the invariant.**
`kernel/src/ipc/mod.rs:317-320`.

Description. The `SendPending`/`RecvComplete` arm of the commit-phase match is `unreachable!()`,
justified by the pre-flight `peek_state` queue-full check at lines 293-298. The reasoning is
sound (the pre-check returns `QueueFull` before this match runs, and nothing mutates the state
between peek and commit because there is no concurrency in v1). error-handling.md §10 permits
`unimplemented!()`/`unreachable!()` for "genuinely unreachable branches that Rust's type system
cannot prove" — this qualifies. The comment at line 318 ("Excluded by the pre-check above")
documents it.

Why it matters. The unreachability is a *temporal* invariant (peek-then-commit with no
interleaving), not a structural one. Under any future change that splits the peek and commit
across a yield/await point (preemption, B5+), this `unreachable!()` becomes reachable and panics
in release. The existing comment is good but does not flag the fragility-under-preemption.

Suggested fix. Either return `Err(IpcError::QueueFull)` from this arm instead of `unreachable!()`
(defense-in-depth: the cost is one branch, and it cannot mis-fire), or extend the comment to note
that the unreachability depends on the single-threaded peek-then-commit window and must be
re-audited when preemption lands (cross-reference ADR-0032 §Context's preemption note).

### Praise

---

**C3-P1 — Pre-flight-before-mutation is implemented exactly as the invariant demands, on both send and recv paths.**
`kernel/src/ipc/mod.rs:271-303` (send), `:348-371` (recv).

`ipc_send` validates the endpoint cap (+SEND), validates the transfer cap (+TRANSFER) via a
non-mutating `lookup`, confirms the arena slot is live, and does the queue-full `peek_state`
check — all *before* the `cap_take` that is the first irreversible mutation. `ipc_recv`'s
`pending_has_cap && caller_table.is_full()` check (lines 361-368) returns `ReceiverTableFull`
before the `core::mem::replace` that moves the state to `Idle`, so a full receiver table never
drops an in-flight cap. This is the `ipc.md` §Invariants "Pre-flight before mutation" property
realized precisely, and the comments at lines 354-360 even pin the maintenance contract ("If
install_cap_if_some's error conditions ... change, this invariant must be revisited"). Exemplary.

---

**C3-P2 — The cap-transfer atomicity tests are genuinely adversarial, not happy-path theater.**
`kernel/src/ipc/mod.rs:1088-1164` (`recv_with_full_table_preserves_pending_cap`),
`:902-941` (`send_with_bad_transfer_cap_preserves_recv_waiting`),
`:1252-1314` (`cancel_recv_on_recv_complete_does_not_drop_message_or_cap`).

These tests do the hard thing: they provoke a failure (full table / `HasChildren` transfer cap /
cancel-on-`RecvComplete`), assert the *typed* error, and then prove the parked state *survived*
by completing the operation successfully afterward and checking the cap is live in the receiver's
table. `recv_with_full_table_preserves_pending_cap`'s two-act structure (fail, free a slot, retry,
assert `cap: Some(_)`) is exactly the regression shape testing.md §"What has tests" asks for, and
it directly defends the most security-sensitive IPC property (no silent authority loss). This is
the standard the rest of the kernel's tests should be held to.

---

**C3-P3 — The `reset_if_stale_generation` guard pair tests both halves of the assertion's predicate.**
`kernel/src/ipc/mod.rs:1373-1424`.

`stale_send_pending_with_some_cap_panics_in_debug` (gated by `#[cfg(debug_assertions)]`) proves
the loud guard fires on a cap-bearing stale state, and `stale_recv_waiting_resets_silently` +
`stale_send_pending_without_cap_resets_silently` prove the predicate is *not over-broad* (no-cap
states reset silently). Testing both "the assert fires when it should" and "the assert does not
fire when it shouldn't" is a discipline rarely seen and exactly right for a guard whose whole
value is its precision.

---

**C3-P4 — Generation-tagged slot reuse in `Arena` and the parallel `slot_generations` in `IpcQueues` are a clean, correct use-after-free defense with no `unsafe`.**
`kernel/src/obj/arena.rs:159-194`; `kernel/src/ipc/mod.rs:179-243`.

`Arena::free` bumps the generation before returning the value (arena.rs:169), and every lookup
checks `slot.generation != id.generation`. The IPC layer cannot share the arena's generation
directly (it indexes a parallel state array), so it keeps its own `slot_generations` shadow and
reconciles on every access via `reset_if_stale_generation`. The const assertion `N <= Index::MAX`
(arena.rs:108-113) closes the index-truncation hole at compile time. The whole use-after-destroy
story is structural, not disciplinary — matching ADR-0016's stated goal — and is entirely safe
Rust.

## Claims register

| Claim | Source `file:line` | How to verify |
|---|---|---|
| Sender cannot transfer a cap without holding `TRANSFER` | `ipc/mod.rs:276-283` | `send_without_transfer_right_on_xfer_cap_fails` test (`:945-969`); rights bit `TRANSFER = 1<<3` (`cap/rights.rs:28`) |
| `SEND`/`RECV`/`NOTIFY` rights don't overlap each other or `TRANSFER` | `cap/rights.rs:28-34` | bits 3,4,5,6 distinct; `KNOWN_BITS` union (`:43-51`); ADR-0017 §"CapRights bits" required non-overlap |
| Cap is removed from sender table before delivery, installed in receiver atomically | `ipc/mod.rs:303` (`cap_take`), `:375` (`install_cap_if_some`) | `send_transfers_cap_atomically` (`:723-767`); `cap_take` impl (`cap/table.rs:455-475`) |
| Capability is move-only (never two instances of same authority) | `cap/mod.rs:114-127` (`Capability`, no `Copy`/`Clone`) | type does not derive `Copy`/`Clone`; `EndpointState` is `!Copy` (`ipc/mod.rs:147`) |
| Queue-full pre-check leaves state + table unchanged on `QueueFull` | `ipc/mod.rs:293-298` (`peek_state` before any mutation) | `second_send_when_pending_fails` (`:856-884`); `second_recv_when_waiting_fails` (`:886-898`) |
| Full receiver table returns `ReceiverTableFull` before state moves to `Idle` | `ipc/mod.rs:361-368` | `recv_with_full_table_preserves_pending_cap` two-act test (`:1088-1164`) |
| `cap_take` failure (HasChildren) preserves `RecvWaiting` | `ipc/mod.rs:300-303` (take before state mutation) | `send_with_bad_transfer_cap_preserves_recv_waiting` (`:902-941`) |
| Stale endpoint slot resets to `Idle`, never inherits predecessor's waiter state | `ipc/mod.rs:216-233` | `stale_queue_state_reset_on_slot_reuse` (`:973-1005`); guard tests (`:1373-1424`) |
| `ipc_cancel_recv` reverses only `RecvWaiting → Idle`; no-op on other states | `ipc/mod.rs:494-498` | `cancel_recv_*` tests (`:1176-1344`); ADR-0032 §Simulation row 3b |
| Bridge Deadlock path restores BOTH scheduler and endpoint state | `sched/mod.rs:1142-1169` | `ipc_recv_and_yield_deadlock_rolls_back_endpoint_state` (`sched/mod.rs:1725-1769`); ADR-0032 §Decision |
| `ipc_cancel_recv` takes `&CapabilityTable` so bridge can split borrows | `ipc/mod.rs:486`; `sched/mod.rs:1158-1163` | SAFETY comment at `sched/mod.rs:1150-1157`; Miri 143/143 per `ipc.md:142` |
| Resume-path `Pending` becomes `PendingAfterResume`, not `Ok(Pending)` | `sched/mod.rs:1228-1232` | `ipc_recv_and_yield_resume_pending_returns_typed_err` (`sched/mod.rs:1956-2043`) |
| `ipc_notify` is fire-and-forget; no waiter wake in v1 | `ipc/mod.rs:408-420` (no unblock step) | doc-comment `:395-403`; ADR-0017 §"Blocking model"; `ipc.md` §"Open questions" |
| `Notification::consume` has no production caller | `obj/notification.rs:41-45` | `rg '\.consume\(\)'` → only `notification.rs` tests (lines 138-139) |
| `Endpoint::id` / `get_*` accessors test-only | `obj/endpoint.rs:31-34,92` | `rg '\.id\(\)|get_endpoint'` → only test modules |
| `Arena` capacity bound enforced at compile time | `obj/arena.rs:108-113` | `const { assert!(N <= Index::MAX...) }` in `new` |
| IPC file is 1425 lines, not ~990 | `kernel/src/ipc/mod.rs` (EOF 1425) | `wc -l`; contradicts `ipc.md:14` |
| `RecvOutcome` lacks `Eq`/`PartialEq` derives (asymmetry vs `SendOutcome`) | `ipc/mod.rs:123` vs `:105` | both `pub enum` derive lines; `Message`+`CapHandle` are both `Eq` so derive is feasible |

## Cross-track notes

- **To C-sched (`kernel/src/sched/mod.rs`).** The IPC↔scheduler contract is honored on both
  sides: the bridge's Phase 2 Deadlock branch calls `ipc_cancel_recv` exactly once with the same
  `ep_cap` Phase 1 validated, in a momentary `&CapabilityTable` borrow taken *after* the scheduler
  `&mut` is dropped (`sched/mod.rs:1142-1169`). C3-005 (document the `&` vs `&mut` table-borrow
  asymmetry in `ipc/mod.rs`) is a hazard that primarily protects the bridge — flag it for the
  sched track too, since a "uniform `&mut`" cleanup there would also surface. Also: the
  pre-Phase-1 `NoCurrentTask` guard (`sched/mod.rs:1043-1045`) exists specifically so a current-less
  early return cannot strand the endpoint in `RecvWaiting` — verify the sched track confirms
  `ipc_recv_and_yield_with_no_current_task_leaves_endpoint_idle` (`:1779`) still passes; that test
  is the only thing proving the guard is ordered before the Phase 1 mutation.

- **To C-cap (`kernel/src/cap/table.rs`).** This track depends on `cap_take` returning the
  capability *value* (not just dropping it) and on `insert_root` being infallible-after-`is_full()`-check.
  Both hold (`table.rs:455-475`, `:143-156`, `:482-484`). C3-008 (lossy `CapError → IpcError`
  mapping) is a shared boundary concern: if the cap track ever splits `cap_take`'s errors further,
  the IPC mapping at `ipc/mod.rs:536-547` should be revisited in lockstep.

- **To the docs/architecture track.** C3-004 (`~990-line` → 1425) and the `ipc.md` §"Open
  questions" item "Endpoint destruction-with-pending-cap policy" (which is C3-001's tracking entry)
  both live in `docs/architecture/ipc.md`. The doc is otherwise accurate: its state-machine
  Mermaid diagram (`ipc.md:32-52`) matches `EndpointState` (`ipc/mod.rs:148-163`) edge-for-edge,
  and the capability-transfer pre-flight prose (`ipc.md:84-91`) matches the code.

- **To the Phase B / destroy-path ADR (future).** C3-001 is the concrete artifact the eventual
  endpoint-destroy ADR must reckon with: `destroy_endpoint` (`obj/endpoint.rs:83`) is `pub` and
  cap-blind today. ADR-0032 §Consequences §Positive's "Forward-cleanup primitive for endpoint
  destroy" wording (and the `ipc_cancel_recv` doc rider at `ipc/mod.rs:448-463`) already warn that
  `cancel_recv`'s no-op-on-cap-bearing-states semantics are *wrong* for a destroy drain — that
  warning is correct and should anchor the destroy ADR.

## Coverage checklist

- [x] `kernel/src/ipc/mod.rs` — 1425 lines — read in full (incl. all 30+ test fns).
- [x] `kernel/src/obj/mod.rs` — 102 lines — read in full.
- [x] `kernel/src/obj/endpoint.rs` — 115 lines — read in full.
- [x] `kernel/src/obj/notification.rs` — 156 lines — read in full.
- [x] `kernel/src/obj/task.rs` — 188 lines — read in full.
- [x] `kernel/src/obj/arena.rs` — 292 lines — read in full.

Context read for verification (not part of the track, read partially or in full as noted):
ADR-0017 (full), ADR-0018 (full), ADR-0032 (full), ADR-0016 (full), `docs/architecture/ipc.md`
(full), `kernel/src/cap/table.rs` (full), `kernel/src/cap/mod.rs` (full),
`kernel/src/cap/rights.rs` (full), `kernel/src/sched/mod.rs` (IPC-bridge sections + grep map),
standards: `architectural-principles.md`, `error-handling.md`, `testing.md`, `code-review.md`,
`code-style.md` (all full).
