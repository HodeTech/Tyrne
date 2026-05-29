# T-020 — Syscall error taxonomy: split `IpcError::InvalidCapability` + redact `Capability` `Debug`

- **Phase:** B
- **Milestone:** B5 — Syscall boundary (this task is B5's pure-Rust foundation: the userspace-facing error taxonomy + capability-Debug redaction that the dispatcher in [T-021](T-021-syscall-dispatch.md) builds on; [ADR-0030](../../../decisions/0030-syscall-abi.md) settles the taxonomy)
- **Status:** In Review
- **Created:** 2026-05-29
- **Author:** @cemililik (+ Claude Opus 4.8 agent)
- **Dependencies:** [ADR-0030](../../../decisions/0030-syscall-abi.md) — must be `Accepted` before code lands (settles the `StaleHandle` / `MissingRight` / `WrongObjectKind` split and the §"Security of the taxonomy split" rationale). No prior task gates this; it is pure-Rust over the existing `kernel/src/ipc` + `kernel/src/cap` surfaces.
- **Informs:** Grounds [ADR-0030 §Dependency chain step 1](../../../decisions/0030-syscall-abi.md#dependency-chain) and discharges [ADR-0030 §Simulation row 3](../../../decisions/0030-syscall-abi.md#simulation). Unblocks [T-021](T-021-syscall-dispatch.md), whose dispatcher composes `SyscallError` from the now-granular `IpcError` and must never log an unredacted `Capability`. Closes the [2026-04-21 Phase-A code review](../../reviews/code-reviews/2026-04-21-tyrne-to-phase-a.md)'s `InvalidCapability`-collapse follow-up (K2-5) and the security review §6 redaction item (K3-9).
- **ADRs required:** [ADR-0030](../../../decisions/0030-syscall-abi.md). Adds an additive §Revision-notes rider to [ADR-0017](../../../decisions/0017-ipc-primitive-set.md) (the IPC primitive set whose error taxonomy is refined — **not** superseded; the three-primitive surface is unchanged). No supersession.

---

## User story

As a future userspace caller (and the [T-021](T-021-syscall-dispatch.md) dispatcher that serves it), I want IPC capability failures to be reported as three distinct, handleable errors — a stale handle, a wrong-kind object, a missing right — instead of one collapsed `InvalidCapability`, and I want a `Capability`'s `Debug` output to never leak the kernel object it names, so the syscall error space is honest and a userspace-reachable log path cannot disclose capability internals.

## Context

[ADR-0030](../../../decisions/0030-syscall-abi.md) bundles the **K2-5** error-taxonomy decision with the syscall ABI so the in-kernel and userspace error spaces agree from the start. Today [`IpcError::InvalidCapability`](../../../../kernel/src/ipc/mod.rs) collapses three failure modes the [error-handling standard §"design checklist"](../../../standards/error-handling.md) says a caller would handle differently. This task performs the split — pure-Rust, host-testable, with no dependency on the (yet-unwritten) trap trampoline — so the error space is exercised by the existing IPC test suite well ahead of the first syscall.

The same milestone's security item (**K3-9**, B5 sub-item 6, [security review §6](../../reviews/security-reviews/2026-04-21-tyrne-to-phase-a.md)) requires `Capability`'s derived `Debug` to be redacted before any userspace-reachable log path (`console_write`, T-021) can format one. The redaction is equally pure-Rust and is bundled here because it touches the same `kernel/src/cap` surface and shares the "make the userspace-observable error/diagnostic surface safe before the dispatcher exists" framing.

This task deliberately **excludes** the trap trampoline, the dispatcher, `SyscallError`, and copy-from/to-user — those are [T-021](T-021-syscall-dispatch.md). Splitting the milestone keeps the security-critical hardware-facing boundary in its own task with its own review, per CLAUDE.md §6 ("do not dump entire subsystems in a single pass").

## Acceptance criteria

- [x] `IpcError::InvalidCapability` is removed and replaced by `IpcError::StaleHandle`, `IpcError::MissingRight`, `IpcError::WrongObjectKind`, each with a doc-comment describing its distinct meaning per [ADR-0030](../../../decisions/0030-syscall-abi.md). `IpcError` stays `#[non_exhaustive]`.
- [x] Every production site is mapped to the correct variant: `validate_ep_cap` / `validate_notif_cap` (`ipc/mod.rs`) and `resolve_ep_cap` (`sched/mod.rs`) resolve in the order `StaleHandle → WrongObjectKind → MissingRight`; arena `get`/`get_mut` staleness failures map to `StaleHandle`.
- [x] Every existing test asserting `InvalidCapability` is updated to its correct post-split variant (rights failures → `MissingRight`; stale-handle/destroyed-object → `StaleHandle`), and the `sched` bridge test is updated.
- [x] New host tests pin each new variant on a path that does **not** already prove it — `WrongObjectKind` for `ipc_send` / `ipc_recv` / `ipc_notify` (wrong-kind caps that carry the right, proving kind-before-rights), and `StaleHandle` for `ipc_send` on both a dropped cap handle and a destroyed endpoint.
- [x] `Capability`'s `Debug` impl is custom (not derived) and prints `Capability { rights: <rights>, object: <redacted> }` — `rights` visible, the named object redacted — per [ADR-0030 §"Security of the taxonomy split"](../../../decisions/0030-syscall-abi.md#security-of-the-taxonomy-split) and the K3-9 redaction requirement. **`CapObject` is also redacted** (kind-only `Debug`, hiding the wrapped handle) — closing the defense-in-depth gap the adversarial review raised. Two host tests pin both layers.
- [x] All gates green: `cargo fmt --all -- --check`, `cargo host-test` (194 kernel), `cargo host-clippy`, `cargo kernel-clippy`, `cargo kernel-build`, and `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` (no UB).
- [x] Docs updated: [`docs/architecture/ipc.md`](../../../architecture/ipc.md) §"`IpcError` taxonomy", [`docs/architecture/security-model.md`](../../../architecture/security-model.md) redaction rule broadened to capabilities, [`docs/glossary.md`](../../../glossary.md) syscall terms, the ADR index, and the [ADR-0017](../../../decisions/0017-ipc-primitive-set.md) §Revision-notes rider.

## Out of scope

- The EL0→EL1 `SVC` trap trampoline, the panic-free dispatcher, `SyscallError`, and copy-from/to-user — all [T-021](T-021-syscall-dispatch.md).
- Splitting `IpcError::InvalidTransferCap` (note C3-008) — deferred to a future ADR when a userspace transfer consumer needs the `TransferCapHasChildren` distinction.
- Redacting the **individual kernel-object handle types** (`TaskHandle` / `EndpointHandle` / `NotificationHandle` / `AddressSpaceHandle` / `SlotId`) and the userspace-facing `CapHandle` — these keep their derived `Debug` for kernel-internal diagnostics (scheduler dispatch traces, arena bookkeeping, test-failure messages) where the slot/generation is the useful information and never crosses to userspace. (`CapObject` *is* redacted in this task — see §Design notes — because it is the type a `Capability` carries toward a log boundary. The deeper per-handle redaction, if ever wanted, is a separate kernel-Debug-hygiene decision; T-021's `console_write` review must confirm no kernel-object handle is formatted into the userspace-reachable path.)
- Any userspace crate, EL0 context, or real syscall invocation — Phase B6.

## Approach

### Error split (`kernel/src/ipc/mod.rs`)

Replace the single `InvalidCapability` variant with the three new ones (doc-commented). Rewrite `validate_ep_cap` and `validate_notif_cap` to the `lookup→StaleHandle`, `kind→WrongObjectKind`, `rights→MissingRight` order (resolve, then type-check, then authority-check — matching `CapError`'s `InvalidHandle`/`WrongKind`/`InsufficientRights` shape). Map the four arena `get`/`get_mut` staleness sites (`ipc_send`/`ipc_recv`/`ipc_notify`/`ipc_cancel_recv`) to `StaleHandle`. Update each operation's `# Errors` doc section to name the three variants.

### Scheduler bridge (`kernel/src/sched/mod.rs`)

`resolve_ep_cap` maps `lookup→StaleHandle` and `kind→WrongObjectKind` (it performs no rights check; rights are validated inside `ipc_send`/`ipc_recv`). `SchedError::Ipc(IpcError)` + its `From` impl propagate the split transparently through `?`; the only test to update is the bridge's send-error-preserves-state test (a correct-kind endpoint cap lacking `SEND` → `MissingRight`).

### Capability `Debug` redaction (`kernel/src/cap/mod.rs`)

Remove `#[derive(Debug)]` from `Capability`; add a hand-written `impl core::fmt::Debug` that emits `rights` and a `<redacted>` placeholder for `object`. `EndpointState` (which embeds `Option<Capability>`) derives only `Default`, so no cascade. Update the struct doc-comment to describe the redaction instead of "Debug is derived … exposes typed handles".

### Simulation

This task is a refactor of an existing state machine, not a new one; the relevant state-machine simulation is [ADR-0030 §Simulation](../../../decisions/0030-syscall-abi.md#simulation). This task **discharges row 3** of that table (the IPC-error-taxonomy mapping) via the per-variant host tests; the row-to-verification mapping is recorded in §Review history on completion.

### Error handling

Per [error-handling standard §2](../../../standards/error-handling.md): the enum stays `#[non_exhaustive]`, derives `Debug, Copy, Clone, Eq, PartialEq`, and each new variant is a distinct handleable case. No `From` impl changes (the split is within `IpcError`; `SchedError::Ipc`/`SyscallError::Ipc` wrap it unchanged).

## Definition of done

All acceptance criteria checked; gates green (incl. Miri — a [Phase-B exit prerequisite](../../../roadmap/phases/phase-b.md) with weight on `sched`/`ipc`); docs updated; ADR-0017 rider added; `current.md` reflects T-020 `In Review` (implementation complete, awaiting maintainer merge) and B5 in progress. **Security-relevant** (capabilities + IPC): flagged for explicit review per CLAUDE.md.

## Design notes

- The validation **order change** (kind-before-rights) is observable only for a capability that is both wrong-kind *and* missing-right; all existing rights-failure tests use correct-kind caps and remain `MissingRight`. Documented in [ADR-0030 §"The K2-5 `IpcError` split"](../../../decisions/0030-syscall-abi.md#the-k2-5-ipcerror-split-lands-now-in-t-020).
- The security argument for revealing the failure mode (per-subject, unforgeable handles ⇒ no forgery/enumeration aid) is in [ADR-0030 §"Security of the taxonomy split"](../../../decisions/0030-syscall-abi.md#security-of-the-taxonomy-split). The redaction keeps the *object identity* hidden even as the *failure mode* becomes visible — the two are independent surfaces.
- Redaction approach is a custom `impl Debug`, not a `Redacted<T>` wrapper, matching the codebase's direct-impl style and avoiding a cascading wrapper refactor; no code structurally depends on `Capability: Debug`.
- **`CapObject` redaction (folded in from the adversarial review).** The first redaction pass touched only `Capability`. An adversarial self-review flagged that `CapObject` (and the handle types it wraps) still derived `Debug`, so a `CapObject` formatted directly — now or in a future error/log — would leak the slot index + generation the `Capability` layer hides. Verified there is **no** current production formatter of `CapObject` (the only capability-type `Debug` formatter in the tree is the redacting `Capability::Debug`; `IpcError`/`SchedError` carry no capability payload; `EndpointState` has no `Debug`), so this was a *latent* gap, not a live leak. Per CLAUDE.md rule 1 ("when in doubt, choose the more conservative option") the gap was closed at the source: `CapObject` now has a kind-only redacting `Debug`. The individual handle types keep their derived `Debug` (kernel-internal diagnostics) — see §Out of scope.

## Review history

- **2026-05-29 — Implementation complete; `In Progress → In Review`.** Landed the K2-5 `IpcError` split (`StaleHandle` / `WrongObjectKind` / `MissingRight`, validation reordered to resolve→type-check→authority across `validate_ep_cap` / `validate_notif_cap` / `sched::resolve_ep_cap`; 4 arena-staleness sites → `StaleHandle`) and the K3-9 redaction (`Capability` + `CapObject` `Debug` redacted). Tests: 6 existing assertions remapped + 8 new variant/redaction tests (kernel suite **187 → 196**). **Row-to-verification mapping** ([ADR-0030 §Simulation](../../../decisions/0030-syscall-abi.md#simulation)): row 3 (IPC error taxonomy) → `send_with_wrong_object_kind_returns_wrong_object_kind`, `recv_with_wrong_object_kind_returns_wrong_object_kind`, `notify_with_wrong_object_kind_returns_wrong_object_kind`, `cancel_recv_with_wrong_object_kind_returns_wrong_object_kind`, `send_with_dropped_cap_handle_returns_stale_handle`, `send_to_destroyed_endpoint_returns_stale_handle`, `cancel_recv_to_destroyed_endpoint_returns_stale_handle`, `notify_with_stale_handle_after_slot_reuse_fails`, plus the remapped `*_without_*_right_fails` (`MissingRight`) tests and the `sched` bridge `ipc_send_and_yield_send_error_preserves_scheduler_state` test — so all four operations (`ipc_send` / `ipc_recv` / `ipc_notify` / `ipc_cancel_recv`) pin all three variants; the K3-9 redaction → `cap::tests::debug_redacts_named_object_but_keeps_rights` + `capobject_debug_redacts_handle_but_shows_kind`. Gates all green: `fmt`, `host-test` (196 kernel / 43 hal / 53 test-hal), `host-clippy`, `kernel-clippy`, `kernel-build`, `miri` (no UB; Stacked Borrows).
- **2026-05-29 — Adversarial multi-lens self-review** (security / correctness / completeness / design). Verdict: **no Blocker/Major findings**; the split's reordering is consistent across the direct and scheduler-bridge paths, the `format_args!` redaction is sound, and `EndpointState` cannot leak. One Minor defense-in-depth finding (`CapObject`/handle `Debug` derives) was folded in for `CapObject` (see §Design notes); one Nit (test-module `#[allow]` pragma) was assessed and intentionally not applied (the test uses only `format!`/`assert!`, triggering none of the forbidden pragmas).
- **2026-05-29 — Maintainer review (post-rebase).** A maintainer review of the ADR/task arc raised: (Major) the same-day ADR corrections had been folded into the *Accepted* bodies (append-only concern) — resolved by rebasing the branch so the corrections land in the `Proposed` draft and Accept is a separate clean commit (no Accepted body edited post-Accept); (Major) the phase-b §B5 acceptance criterion over-promised a real EL0 round-trip — narrowed to the current-EL kernel-stub mechanism, with the real `0x400` EL0 round-trip moved to §B6; (Minor) `current.md` banner/links and (Minor) the ADR-0030 row-3 mapping over-claiming `cancel_recv` coverage — the latter resolved by adding `cancel_recv_with_wrong_object_kind_*` + `cancel_recv_to_destroyed_endpoint_*` tests; (Nit) the arena-staleness ordering caveat added to ADR-0030 §K2-5. No code-correctness or security bug was found by either review.
