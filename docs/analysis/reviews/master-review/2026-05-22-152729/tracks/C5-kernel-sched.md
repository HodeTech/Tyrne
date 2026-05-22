# C5-kernel-sched — scheduler (master review, commit 288ddb2)

Track: C5-kernel-sched. Anchor commit: 288ddb2. Reviewer lens: code-review.md,
architectural-principles.md (P1, P2), unsafe-policy.md, error-handling.md,
testing.md.

File under review (read in full): `kernel/src/sched/mod.rs` (2652 lines).

Context read (read-only): ADR-0019 (scheduler-shape), ADR-0020 (cpu-trait-v2),
ADR-0021 (raw-pointer-scheduler-ipc-bridge), ADR-0022 / ADR-0026 (idle dispatch),
ADR-0028 (address-space) refs, ADR-0032 (endpoint rollback / cancel-recv) refs;
`docs/architecture/scheduler.md`; `hal/src/context_switch.rs`; `hal/src/cpu.rs`;
`bsp-qemu-virt/src/cpu.rs` (`context_switch_asm`, `#[unsafe(naked)]`);
`kernel/src/ipc/mod.rs` (`ipc_send` / `ipc_recv` / `ipc_cancel_recv` signatures);
`docs/audits/unsafe-log.md` entries UNSAFE-2026-0008 / 0013 / 0014;
`docs/standards/{unsafe-policy,error-handling,code-review,testing,architectural-principles}.md`.

## Summary

This is the largest and most `unsafe`-heavy kernel file (71 `unsafe` keyword
occurrences, 54 `// SAFETY:` comments, 7 production `unsafe fn`s plus 4 in the
test module). It is also, by a clear margin, the **most carefully built and best
documented file the C5 reviewer has seen in this track**. Every production
`unsafe` block carries a SAFETY comment that names invariants upheld, rejected
safer alternatives, and an `UNSAFE-2026-NNNN` audit tag — fully conforming to
`unsafe-policy.md §1`. Every `unsafe fn` (including the module-private
`start_prelude`) has a `# Safety` doc section (`§2`). The raw-pointer bridge
discipline mandated by ADR-0021 — "no `&mut` to `Scheduler<C>`, `EndpointArena`,
`IpcQueues`, or `CapabilityTable` alive across `cpu.context_switch`" — is
implemented exactly as the ADR and the architecture doc describe: each momentary
`&mut` is confined to a lexical block that closes strictly before the switch, and
re-derived strictly after. The context-switch split-borrow on
`contexts[current_idx]` vs `contexts[next_idx]` is genuinely non-aliasing because
the running task is never in the ready queue, so `current_idx != next_idx` by
construction (asserted in debug at each switch site).

Correctness of the scheduling logic holds up under close reading: the FIFO
`SchedQueue` wrap arithmetic is provably in-range; the idle-as-fallback dispatch
chain (`ready.dequeue().or(idle)`) matches ADR-0026's queue-state simulation and
its regression test reproduces the exact 2026-05-06 smoke hang; the
`ipc_recv_and_yield` Deadlock path performs the symmetric scheduler + endpoint
rollback ADR-0032 requires; and the self-dispatch guard
(`s.idle.filter(|&h| h != current_handle)`) closes the release-mode UB that would
arise if idle context-switched to itself. The hot path never allocates, never
loops unboundedly, and panics only on genuine kernel-programming-error invariant
violations (with `#[allow(clippy::panic, reason=...)]` justifications that match
`error-handling.md §5`).

No **Blocker** and no **Major** findings. The findings below are **Minor**
maintainability / robustness observations and **Nits**, plus substantial
**Praise**. The single most material item is C5-001: the file is 2652 lines, of
which ~1417 are a single `#[cfg(test)] mod tests` — the production surface is
~1234 lines and is fine, but the test module has grown to the point where a split
would improve navigability. The most security-relevant item for downstream passes
is C5-004: the entire soundness of this file rests on a *documented contract*
verified by Miri rather than the borrow checker, and Miri is **not yet in CI** —
this is a known, ADR-acknowledged state, but it should be explicitly carried to
the security and unsafe-audit passes as the file's central residual risk.

Severity counts: Blocker 0, Major 0, Minor 5, Nit 6, Praise 7.

## Findings

### Blocker

None.

### Major

None.

### Minor

---

**C5-001 — Test module (~1417 lines) dominates the file; consider extracting to `sched/tests.rs`**
`kernel/src/sched/mod.rs:1235-2652`

The `#[cfg(test)] mod tests` block runs from line 1235 to the end of file (line
2652) — roughly 1417 lines, larger than the entire production surface
(~1234 lines, lines 1-1234). The tests are excellent (see Praise C5-P5), but the
file as a whole is hard to navigate: a reader looking for the bridge logic must
scroll past, or an editor must page through, a test module bigger than the code it
tests.

*Why it matters.* `code-review.md` treats reviewability as a first-class property
("Small changes review better than big changes"); the same logic applies to file
size for an unsafe-heavy hot-path module. Rust idiom allows moving the test module
to a sibling file with `#[cfg(test)] mod tests;` + `sched/tests.rs`, keeping
`super::*` imports working. This is purely mechanical and changes no behaviour.

*Suggested fix.* Extract the test module to `kernel/src/sched/tests.rs` (or split
by concern: `tests/queue.rs`, `tests/bridge.rs`, `tests/idle.rs`). Leaves the
production file ~1234 lines — a comfortable size for the most-audited file in the
kernel. Note this is a *file-organisation* suggestion, not a request to change the
tests; defer if the maintainer prefers single-file modules at this phase.

---

**C5-002 — `unblock_receiver_on` panics on a "cannot happen" full-queue, identical pattern duplicated in `yield_now`; factor the invariant into one checked helper**
`kernel/src/sched/mod.rs:376-385` and `kernel/src/sched/mod.rs:782-789`

Two sites enqueue under the same load-bearing invariant ("the running task is not
in the ready queue, so at most `TASK_ARENA_CAPACITY-1` other tasks are queued, so
`enqueue` cannot fail") and both resolve a `Result` by `panic!` with a near-identical
`#[allow(clippy::panic, reason=...)]`. A third site (`add_task`, line 337) maps the
same enqueue error to a typed `SchedError::QueueFull` instead — three slightly
different treatments of the same `SchedQueue::enqueue` failure.

*Why it matters.* The panic is genuinely unreachable in correct code and the
justification is sound, so this is not a correctness defect. But the invariant is
the kind of thing that a future change (preemption re-enqueueing the preempted
task, multi-waiter wake re-enqueueing several tasks, SMP) could quietly violate,
and having the assertion spelled out in two prose-duplicated `#[allow]` blocks
makes it easier to drift. `architectural-principles.md` favours making invariants
explicit and centralised; ADR-0026 itself notes the value of an explicit, single
home for the "idle is never enqueued / queue is never full" invariants.

*Suggested fix.* A private `fn enqueue_ready(&mut self, h: TaskHandle)` that
encapsulates the "this enqueue is infallible by the no-double-enqueue invariant"
panic with one SAFETY-style comment, called from both `unblock_receiver_on` and
`yield_now`. Leaves `add_task`'s typed-error path as-is (it is the one site where
the failure is *not* invariant-guaranteed, because it runs before dispatch). Pure
refactor; no behaviour change.

---

**C5-003 — `unblock_receiver_on` performs an `O(N)` linear scan over `task_states` per delivery; documented but worth a forward-looking note**
`kernel/src/sched/mod.rs:362-390`

`unblock_receiver_on` scans all `TASK_ARENA_CAPACITY` slots to find the single
task blocked on a given endpoint. This is explicitly sanctioned by ADR-0019
(O(N) at N ≤ 16) and the doc-comment says so. It is called on the IPC send hot
path (`ipc_send_and_yield` → `s.unblock_receiver_on(ep_handle)` at line 954).

*Why it matters.* Not a defect at v1 scale — the scan is 16 iterations of a `Copy`
enum comparison, cheaper than the context switch that follows. The note is forward
defensive: when `TASK_ARENA_CAPACITY` grows or multi-waiter endpoints land (both
named as future ADRs in `scheduler.md` Open questions), this scan becomes the
scheduler's per-message cost. The performance pass should track it; no action at
this commit.

*Suggested fix.* None now. When the multi-waiter ADR is written, prefer an
endpoint-indexed waiter list over widening this scan. Recording here so the
performance and IPC tracks have a single pointer to the cost.

---

**C5-004 — Whole-file soundness rests on a doc-comment contract verified by Miri, and Miri is not yet a CI gate; route to security + unsafe-audit passes**
`kernel/src/sched/mod.rs:393-473` (shared safety contract) and every bridge body

The raw-pointer bridge deliberately trades the borrow checker's compile-time
non-aliasing guarantee for a *documented* "no `&mut` across the switch" invariant
(ADR-0021 §Consequences — Negative explicitly accepts this). The verification path
the ADR names is `cargo +nightly miri test` on the host tests, run "once CI exists
(K3-7)". Per `docs/standards/infrastructure.md` and the 2026-04-23 Miri-validation
report, Miri is run **manually** today and is **not** a per-PR gate; the
architecture doc's claim "Stacked Borrows verifies this on every miri run" is true
only for runs the maintainer remembers to do.

*Why it matters.* This is the file's single largest residual risk and it is
inherent to the chosen design, not a defect in the code as written. Every "the
`&mut` is contained to this block" SAFETY claim in this file is enforced only by
(a) reviewer eyes and (b) Miri-when-run. A future edit that lets a momentary
`&mut` escape its block — e.g. by hoisting a `let s = &mut *sched;` above the
switch during a refactor — would compile cleanly, pass non-Miri tests, and
reintroduce exactly the UNSAFE-2026-0012 UB the bridge was built to remove. The
2026-05-06 smoke regression is precedent that "host tests + static analysis +
review" cleared a real defect six times; the analogous failure here would be an
aliasing-UB regression that only Miri catches.

*Suggested fix.* No code change in this file. Carry to the security pass and the
unsafe-audit pass as the central finding: prioritise wiring `cargo +nightly miri
test --workspace --exclude tyrne-bsp-qemu-virt` into CI (the K3-7 task the ADR
already names) and gate `kernel/src/sched/` + `kernel/src/ipc/` changes on it. See
Cross-track notes.

---

**C5-005 — `ipc_send_and_yield` holds four live `&mut` referents simultaneously in Phase 1; sound, but the SAFETY comment under-states the distinctness requirement it relies on**
`kernel/src/sched/mod.rs:941-961`

Phase 1 of `ipc_send_and_yield` materialises four `&mut` references at once —
`s: &mut Scheduler<C>`, `arena_ref: &mut EndpointArena`,
`queues_ref: &mut IpcQueues`, `table_ref: &mut CapabilityTable` — and calls both
`ipc_send(arena_ref, queues_ref, …, table_ref, …)` and
`s.unblock_receiver_on(ep_handle)` while all four are live. This is sound: the
four referents are distinct objects (no aliasing among them), and crucially **no
context switch happens inside this block** — the switch is deferred to the
re-entrant `yield_now(sched, …)` call at line 973, which runs *after* this block's
`&mut`s have dropped (line 961). So the "no `&mut` across the switch" rule is not
violated.

*Why it matters.* The correctness depends on the four pointers being
*non-overlapping objects*, which the shared safety contract states ("The four
pointers must not alias each other …", lines 915-916, 1014-1016) but the
**per-block** SAFETY comment at lines 933-940 phrases only as "valid, distinct,
and exclusively-owned" without re-stating that `s` and the three arena pointers
must be disjoint from each other. A reviewer auditing this block in isolation has
to walk back up to the function-level `# Safety` to confirm the distinctness of
all four. Minor, because the function doc does carry it; the gap is purely between
the block-local comment and the function-level contract.

*Suggested fix.* Add one clause to the line 933-940 SAFETY comment: "and `sched`,
`ep_arena`, `queues`, `caller_table` refer to four disjoint objects, so the four
`&mut`s materialised here do not alias." No behaviour change; tightens the local
audit story for the one block that holds the most simultaneous `&mut`s.

### Nit

---

**C5-N1 — `address_space_activation_target` is defined between `yield_now` and `ipc_send_and_yield`, splitting the three bridge entry points**
`kernel/src/sched/mod.rs:873-901`

The pure helper `address_space_activation_target` sits in the middle of the
bridge-function run (after `yield_now`, before `ipc_send_and_yield`). Reading the
three bridge entry points top-to-bottom is interrupted by a helper. Minor;
consider grouping all private helpers (this + the `Scheduler::resolve_ep_cap` /
`unblock_receiver_on` already in the impl block) together, or moving this one up
beside `resolve_ep_cap`. Cosmetic.

---

**C5-N2 — `start`'s `# IRQ state on task entry` doc says tasks begin with interrupts masked, but `register_idle`'s body comment claims idle's WFI will wake; these can read as contradictory without the BSP context**
`kernel/src/sched/mod.rs:631-639`

`start`'s doc (lines 631-639) correctly states that because the bootstrap
`IrqGuard` Drop never runs, tasks begin executing with DAIF masked, and "a task
that needs interrupts enabled must call `cpu.restore_irq_state(IrqState(0))`
explicitly." Meanwhile `scheduler.md` and the BSP describe idle's body as
`wait_for_interrupt() + yield_now` with WFI as the production wake form. A reader
of just this file might wonder how idle's WFI ever wakes if it boots masked.
(Resolution: WFI wakes on a pending IRQ regardless of the DAIF *mask*; the mask
gates whether the handler runs, not whether WFI exits. And idle is reached via a
`context_switch` whose `IrqGuard` *does* drop on return, restoring the prior
state.) This is correct but subtle; one sentence in the `start` doc cross-linking
to the WFI-vs-mask distinction would save the next reader the detour. Doc-only.

---

**C5-N3 — `SchedError::QueueFull` is declared but only reachable from `add_task`, never from the bridge**
`kernel/src/sched/mod.rs:176` (variant) and `:339` (sole producer)

`SchedError::QueueFull` is produced only by `add_task` (line 339). The bridge
functions never surface it (their enqueues are invariant-infallible and panic
instead, per C5-002). This is consistent and intentional, but a reader scanning
`SchedError` may expect `QueueFull` from `yield_now`/`ipc_*`. A one-line doc on
the variant noting "produced only by `add_task` at registration time; the bridge
treats a full ready queue as an unreachable invariant violation (panic), see
`yield_now`" would disambiguate. Doc-only.

---

**C5-N4 — `Scheduler::new` doc says "all contexts zero-initialised" but contexts are `C::TaskContext::default()`, not necessarily zero**
`kernel/src/sched/mod.rs:290-302`

The doc-comment on `Scheduler::new` (line 290) says "all contexts
zero-initialised", and the struct field doc (line 278) similarly says "either
zero-initialised by `Default`". For the QEMU BSP's `Aarch64TaskContext`, `Default`
does produce all-zero, so the statement is true today. But `ContextSwitch::TaskContext`
only requires `Default + Send` (per `hal/src/context_switch.rs:31`), and `Default`
is not contractually "all zero". Prefer "default-initialised by
`C::TaskContext::default()`" to avoid implying a guarantee the trait bound does
not make. Doc accuracy nit.

---

**C5-N5 — `unblock_receiver_on` reads `task_handles[idx]` with `if let Some(handle)` but the invariant guarantees it is `Some` whenever the state is `Blocked`**
`kernel/src/sched/mod.rs:374`

When a slot's `task_states[idx]` is `Blocked { .. }`, the slot is occupied, so
`task_handles[idx]` is necessarily `Some` (both are written together in `add_task`
/ `register_idle` and never independently cleared in v1). The `if let
Some(handle)` (line 374) therefore has an implicit-but-unstated dead `else`. This
is defensively fine (silently does nothing if the invariant is somehow broken),
but it is the one place in the file where an invariant is handled by silent
fall-through rather than an asserted/typed path — slightly inconsistent with the
file's otherwise loud-on-invariant-violation style (cf. the `panic!` in the very
next block). Consider a `debug_assert!(self.task_handles[idx].is_some(), …)` to
make the invariant explicit, matching the file's prevailing discipline. Optional.

---

**C5-N6 — `start` defensive tail loop uses `core::hint::spin_loop()` while idle uses `wait_for_interrupt()`; harmless inconsistency in unreachable code**
`kernel/src/sched/mod.rs:718-725`

`start`'s post-`context_switch` tail (unreachable because the switch abandons the
frame) spins with `core::hint::spin_loop()`. It is correctly `#[allow(clippy::empty_loop,
reason=...)]` and genuinely never executes. No change needed; noting only that the
file contains two "park the CPU" idioms (this spin vs idle's WFI). Since this loop
is provably dead, `spin_loop()` is the right choice (no `cpu` borrow needed).
Pure observation.

### Praise

---

**C5-P1 — Exemplary `unsafe` discipline: every block names invariants, rejected alternatives, and an audit tag**
`kernel/src/sched/mod.rs` (54 SAFETY comments across the file)

This file is the reference implementation of `unsafe-policy.md` in the repository.
Every production `unsafe` block carries a `// SAFETY:` comment with all three
mandated parts (invariants upheld, rejected safer alternatives, `UNSAFE-2026-NNNN`
audit reference). The "Shared safety contract" prose block (lines 405-473) states
the cross-cutting invariant once and each per-block comment refers back to it,
which keeps the bodies focused without losing rigour — exactly the pattern
`unsafe-policy.md` anti-patterns section wants instead of `// SAFETY: trust me`.
Every `unsafe fn` (all 7 production, including module-private `start_prelude`) has
a `# Safety` doc section.

---

**C5-P2 — The raw-pointer bridge implements ADR-0021 precisely; momentary-`&mut` discipline is mechanically correct at every site**
`kernel/src/sched/mod.rs:750-871` (`yield_now`), `:921-984`, `:1026-1233`

Each bridge entry confines its `&mut` materialisation to a block that closes
(`}; // s drops here`) strictly before the `cpu.context_switch` call, and Phase 3
re-derives fresh `&mut`s only after the switch returns. The context-switch call
itself uses raw-pointer arithmetic (`(*sched).contexts.as_mut_ptr()` +
`.add(idx)`) for the split borrow rather than `&mut (*sched)`, so even the
scheduler struct is never `&mut`-borrowed across the switch. This matches the
audit log (UNSAFE-2026-0014) and the architecture doc verbatim. The discipline is
hard to get right and it is right here.

---

**C5-P3 — The idle self-dispatch guard closes a real release-mode UB, and the comment explains exactly why**
`kernel/src/sched/mod.rs:1108-1120`

The `or_else(|| s.idle.filter(|&idle_h| idle_h != current_handle))` guard in
`ipc_recv_and_yield` (mirrored by `yield_now`'s `Some(idle_h) if idle_h !=
current_handle` at line 811) prevents the dispatcher from selecting idle when idle
*is* the current task — which would make `next_idx == current_idx` and alias the
same `contexts` slot as both `&mut` and `&` at the switch site. The inline comment
(lines 1108-1115) names this as release-mode UB that the debug_assert tripwire
would catch only in debug. This is precisely the kind of subtle, release-only
hazard that distinguishes a high-assurance kernel from a working one, and it has a
dedicated regression test (`ipc_recv_and_yield_with_idle_as_current_returns_deadlock`).

---

**C5-P4 — Symmetric scheduler+endpoint rollback on the Deadlock path (ADR-0032) is implemented atomically and correctly**
`kernel/src/sched/mod.rs:1132-1170`

When `ipc_recv_and_yield` blocks the sole task and finds no dispatch target, it
restores `s.task_states[current_idx]` to `prior_state` and `s.current` to
`current_handle` *inside* the scheduler `&mut` block (lines 1136-1137), then —
after that block drops — reverses Phase 1's `Idle → RecvWaiting` endpoint
transition via `ipc_cancel_recv` in a separate momentary borrow (lines 1158-1163).
The two rollbacks live in disjoint borrows so no cross-arena alias is ever live,
and the `caller_table` is taken as `&` (not `&mut`) on the recovery path because
cancel does not mutate it (matching `ipc_cancel_recv`'s `&CapabilityTable`
signature). The pre-Phase-1 `current.is_none()` guard (lines 1043-1045) is a
genuinely good fix: it prevents a `NoCurrentTask` early-return from leaking an
uncancelled `RecvWaiting`, with a dedicated regression test. This is meticulous
state-machine engineering.

---

**C5-P5 — Test suite is unusually thorough for a hard-to-test subsystem, with named regression guards tied to specific incidents**
`kernel/src/sched/mod.rs:1235-2652`

The test module covers: FIFO queue mechanics (incl. wrap-around and full),
state transitions, the activation hook (same-AS short-circuit + cross-AS fire +
the pure helper), `unblock_receiver_on` hit/miss, all three `ipc_send_and_yield`
terminal shapes (Delivered/Enqueued/Err-preserves-state), the `Deadlock` rollback
(scheduler *and* endpoint state), `PendingAfterResume` via a bespoke
`ResetQueuesCpu` double, the `start_prelude` happy/panic paths, and — critically —
the `unblock_after_yield_dispatches_unblocked_receiver_not_idle` regression that
reproduces the exact 2026-05-06 smoke hang. The tests honour the pointer-derivation
discipline (`core::ptr::from_mut` once per referent, never re-borrowed) and say so
in comments, so they themselves are Miri-clean. `start`'s post-prelude assembly
switch — the one genuinely un-host-testable part — is correctly excised into
`start_prelude` so everything else stays asserted. This directly answers
`testing.md`'s "unsafe invariant has a test that exercises the path" and "bug fix
has a regression test" rules.

---

**C5-P6 — Error model is clean: typed `SchedError` with `#[non_exhaustive]`, `From<IpcError>`, and richly-documented variants**
`kernel/src/sched/mod.rs:167-230`

`SchedError` follows `error-handling.md` to the letter: `#[non_exhaustive]`,
derives the full `Copy/Clone/Debug/Eq/PartialEq` set, converts `IpcError` at the
boundary via `From` (lines 226-230), and each variant is documented with the
conditions that produce it. The `Deadlock` variant doc (lines 179-223) is a
small essay on the three shapes that resolve to it and the rollback scope — far
above the bar. The bridge never logs-and-returns, never collapses distinct IPC
failures, and surfaces `PendingAfterResume` as a typed `Err` rather than letting
`Ok(Pending)` propagate to a downstream panic.

---

**C5-P7 — Hot-path hygiene: no allocation, no unbounded loops, panics only on true invariant violations with justified `#[allow]`s**
`kernel/src/sched/mod.rs` (whole production surface)

The scheduling decision is O(1) (dequeue + a couple of array writes); the only
O(N) operation (`unblock_receiver_on`) is bounded by the compile-time arena
capacity. There is no heap touch anywhere (consistent with ADR-0016 / ADR-0019).
Every `panic!` is gated behind a kernel-programming-error invariant and carries a
`#[allow(clippy::panic, reason=...)]` whose reason is accurate — matching
`error-handling.md §5` ("panic is an assertion, not error handling") and the
kernel-crate clippy `deny(clippy::panic)` posture. The `register_idle`
double-registration `assert!` is deliberately unconditional (not `debug_assert!`)
so the single-idle invariant cannot be silently violated in release — a
correct security-conscious choice, well explained at lines 492-502.

## Claims register

| Claim | Source `file:line` | How to verify |
|---|---|---|
| No `&mut Scheduler<C>` / arena / queues / table is alive across `cpu.context_switch` (the core ADR-0021 invariant). | `kernel/src/sched/mod.rs:419-429` (contract); each bridge body, e.g. `:838`, `:961`, `:1140` (`}; // drops here`) before the switch at `:863`, `:973`, `:1199`. | Read each bridge fn: confirm every `let s = &mut *sched;` (and arena/queue/table `&mut`) lives in a block whose `}` precedes the `cpu.context_switch` call. Then run `cargo +nightly miri test -p tyrne-kernel` — Stacked Borrows fails if any `&mut` escapes. **Caveat: Miri is not a CI gate yet (C5-004).** |
| The split borrow `contexts[current_idx]` (`&mut`) vs `contexts[next_idx]` (`&`) is non-aliasing because indices differ. | `:855-868` (yield), `:1193-1204` (recv), `:712-715` (start, throwaway vs next). | `current_idx != next_idx` holds because the running task is removed from the ready queue before dispatch, so `next_handle != current_handle`. Asserted in debug at `:841-844`, `:1173-1176`. Verify: trace that `s.current` is dequeued/removed before `s.ready.dequeue()` runs. Audit: UNSAFE-2026-0008. |
| Pointer validity + exclusive ownership of all `*mut` params (Shared safety contract). | `:411-418` (contract); function `# Safety` sections at `:315`, `:504`, `:586`, `:649`, `:745`, `:912`, `:1012`. | This is a *caller* obligation, not checkable inside the file. Verify at the BSP call sites: `bsp-qemu-virt/src/main.rs:451-602` constructs each pointer via `StaticCell::as_mut_ptr()` (UNSAFE-2026-0013) without materialising `&mut`. Single-core cooperative model means only one task runs at a time → only one dereference site live. |
| ADR-0021 promises UNSAFE-2026-0012 retires *in full* (no residual aliasing window). | ADR-0021 §Decision outcome lines 35-39; audit-log `UNSAFE-2026-0012` status. | `rg "UNSAFE-2026-0012" docs/audits/unsafe-log.md` → status `Removed — 2026-04-22, commit f9b72f8`. Confirm no `&mut self` receiver remains on any scheduler entry point: `rg "&mut self" kernel/src/sched/mod.rs` returns only `add_task` (an `unsafe fn` taking `&mut self` — see note below) and test/Default impls. |
| `add_task` still uses `&mut self` — is that an ADR-0021 violation? | `:320-344`. | **Not a violation.** `add_task` performs no `cpu.context_switch` (it only `init_context` + enqueues), so its `&mut self` never spans a switch. ADR-0021's rule is specifically "no `&mut` across the switch", not "no `&mut self` anywhere". `start`/`yield_now`/`ipc_*` were converted because they *do* switch; `add_task` and `register_idle`(the latter raw-pointer for set-once-assert symmetry) need not be. Confirm by grepping `add_task`'s body for `context_switch` (absent). |
| The idle task is never enqueued in the ready queue (ADR-0026 structural property). | `:516-559` (`register_idle` — no `ready.enqueue` call); field doc `:262-274`. | Read `register_idle`: it writes `s.idle = Some(handle)` and `task_states`/`task_handles`/`task_address_space_handles` but never `s.ready.enqueue`. Test `register_idle_stores_handle_in_idle_slot_and_not_in_ready_queue` (`:2126`) asserts `sched.ready.is_empty()` post-call. |
| Dispatcher consults idle only when ready queue is empty (`ready.dequeue().or(idle)`). | `:612-618` (start_prelude), `:801-819` (yield), `:1116-1120` (recv). | Trace each dispatch site: `s.ready.dequeue()` is tried first; idle is `or`/`or_else` fallback. Test `dispatcher_picks_idle_only_when_ready_queue_empty` (`:2164`) and `unblock_after_yield_dispatches_unblocked_receiver_not_idle` (`:2244`, the 2026-05-06 regression guard). |
| Deadlock path restores BOTH scheduler and endpoint state (ADR-0032 symmetric rollback). | `:1132-1170`. | Scheduler restore at `:1136-1137` (inside `&mut` block); endpoint restore via `ipc_cancel_recv` at `:1158-1163` (separate borrow, after scheduler block drops). Tests `ipc_recv_and_yield_returns_deadlock_when_ready_queue_empty` (`:1655`) and `..._deadlock_rolls_back_endpoint_state` (`:1725`) assert a subsequent `ipc_recv` sees `Pending` (clean `Idle`), not `QueueFull` (leaked `RecvWaiting`). |
| Self-dispatch (idle == current) is rejected to avoid release-mode UB. | `:1116-1119` (`.filter(|&idle_h| idle_h != current_handle)`), `:811`. | Test `ipc_recv_and_yield_with_idle_as_current_returns_deadlock` (`:1832`) registers idle, sets it current, and asserts `Err(Deadlock)` + state restored rather than a self-switch. |
| `register_idle` panics unconditionally (release too) on double registration. | `:534-544`. | `assert!(s.idle.is_none(), …)` is plain `assert!`, not `debug_assert!`. Verify: no `cfg(debug_assertions)` gating; the `#[allow(clippy::panic)]` reason names boot-time discipline. |
| `start_prelude` panics on empty-ready + no-idle (boot programming error). | `:607-618`. | `match s.ready.dequeue() { Some → … None → match s.idle { Some → … None → panic! } }`. Test `start_prelude_panics_on_empty_ready_queue` (`:2101`, `#[should_panic(expected="empty ready queue")]`). |
| Activation-on-context-switch hook fires only on cross-AS switch; v1 short-circuits. | `:873-901` (`address_space_activation_target`), call sites `:851`, `:1185`, `:697`. | Pure helper returns `Some(n)` only when both handles known and differ. Tests at `:1467` (same-AS → no fire), `:1521` (diff-AS → fire), `:1565` (pure-fn table). In v1 all tasks share `BOOTSTRAP_ADDRESS_SPACE_HANDLE` → always `None` → zero overhead. |
| `#[unsafe(naked)]` discipline for context-switch (unsafe-policy §5a). | NOT in this file — `bsp-qemu-virt/src/cpu.rs:354-405`. | The scheduler only *consumes* `ContextSwitch::context_switch` (a trait method). The naked asm lives in the BSP and is correct: `#[unsafe(naked)]` + `naked_asm!` sole body + `extern "C"`, saves/restores x19-x28/fp/lr/sp/d8-d15, `mov x8,sp` workaround. Audit: UNSAFE-2026-0008. This track confirms the scheduler's `cpu.context_switch` calls match the trait's `# Safety` (IRQ disabled via `IrqGuard`, contexts valid). |
| `SchedError::Deadlock` is structurally unreachable in v1 with idle registered. | `:179-223` (variant doc); ADR-0026 §Decision outcome simulation table. | The dispatch chain falls back to idle, so Deadlock needs idle `None` AND queue empty AND current blocked. With BSP `register_idle` at boot (`bsp-qemu-virt/src/main.rs`), idle is always `Some`. Verify the BSP calls `register_idle` exactly once in `kernel_entry`. |

## Cross-track notes

Route the following to the **security pass** and **unsafe-audit pass**:

1. **(Primary, from C5-004) Miri is not a CI gate.** The entire soundness of this
   file — and of `kernel/src/ipc/mod.rs`, which shares the discipline — depends on
   a doc-comment contract whose only mechanical verifier is `cargo +nightly miri
   test`, currently run manually (per `docs/standards/infrastructure.md` and the
   2026-04-23 Miri-validation report). ADR-0021 §Consequences and `scheduler.md`
   both *assume* Miri runs in CI ("once CI exists; K3-7"). Until K3-7 lands, a
   refactor that lets a momentary `&mut` escape its block compiles and passes
   non-Miri tests while reintroducing UNSAFE-2026-0012-class UB. Recommend the
   security pass flag K3-7 (Miri CI gate on `sched/` + `ipc/`) as a Phase-B exit
   prerequisite, consistent with the 2026-04-21 security review that made
   UNSAFE-2026-0012 the #1 Phase-B blocker.

2. **(Unsafe-audit) The audit log is in sync with the source as of this commit.**
   I cross-checked the file's `UNSAFE-2026-NNNN` citations (0008 context-switch
   split-borrow, 0009 init_context, 0014 momentary-`&mut`, plus 0012/0013 prose
   references) against `docs/audits/unsafe-log.md`: every cited tag exists, 0012 is
   correctly `Removed`, and 0014's Amendments name all four scheduler entry points
   (`start`/`start_prelude`/`register_idle` + bridge). No discrepancy found. The
   unsafe-audit pass should confirm the *count* (`cargo-geiger`) reconciles — this
   track counted 71 `unsafe` keyword occurrences and 54 `// SAFETY:` comments in
   the file (the gap is expected: `unsafe fn` definitions, `unsafe impl Send/Sync`
   in tests, and the per-function `# Safety` prose all contain the keyword without
   being SAFETY-commented blocks).

3. **(Security, forward) IRQ-driven scheduler mutation is a future hazard.**
   ADR-0021's 2026-04-28 Amendment and UNSAFE-2026-0014's IRQ-frame Amendment
   establish that any future IRQ handler touching the scheduler must follow the
   same momentary-`&mut` discipline. v1's `irq_entry` is ack-and-ignore and does
   not touch `Scheduler` (verified: the bridge in this file has no IRQ-side caller).
   When preemption / wake-on-deadline lands, the security pass should re-audit the
   IRQ→scheduler boundary against this file's discipline.

4. **(IPC + performance tracks) `unblock_receiver_on` O(N) scan and single-waiter
   semantics** (C5-003) are the scheduler-side coupling points to IPC. The
   multi-waiter ADR (named open in `scheduler.md`) will touch both this scan and
   the `SchedError`/`IpcError` surface; flag for joint review when written.

## Coverage checklist

- [x] `kernel/src/sched/mod.rs` — **2652 lines, read in full** (lines 1-1249 first
  page, 1250-2652 second page; line count confirmed via `wc -l` = 2652, file ends
  at line 2652 with the test module's closing brace). Production surface lines
  1-1234; `#[cfg(test)] mod tests` lines 1235-2652.

Confirmation: every line of the track file was read. Supporting context files
(ADR-0019/0020/0021/0026, `scheduler.md`, `hal/src/context_switch.rs`,
`hal/src/cpu.rs`, `bsp-qemu-virt/src/cpu.rs` context-switch asm,
`kernel/src/ipc/mod.rs` signatures, `docs/audits/unsafe-log.md` entries
0008/0013/0014, and the five lens standards) were read to the extent needed to
verify the claims above.
