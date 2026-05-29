# T-020 — Syscall error taxonomy: split `IpcError::InvalidCapability` + redact `Capability` `Debug`

- **Phase:** B
- **Milestone:** B5 — Syscall boundary (this task is B5's pure-Rust foundation: the userspace-facing error taxonomy + capability-Debug redaction that the dispatcher in [T-021](T-021-syscall-dispatch.md) builds on; [ADR-0030](../../../decisions/0030-syscall-abi.md) settles the taxonomy)
- **Status:** In Progress
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

- [ ] `IpcError::InvalidCapability` is removed and replaced by `IpcError::StaleHandle`, `IpcError::MissingRight`, `IpcError::WrongObjectKind`, each with a doc-comment describing its distinct meaning per [ADR-0030](../../../decisions/0030-syscall-abi.md). `IpcError` stays `#[non_exhaustive]`.
- [ ] Every production site is mapped to the correct variant: `validate_ep_cap` / `validate_notif_cap` (`ipc/mod.rs`) and `resolve_ep_cap` (`sched/mod.rs`) resolve in the order `StaleHandle → WrongObjectKind → MissingRight`; arena `get`/`get_mut` staleness failures map to `StaleHandle`.
- [ ] Every existing test asserting `InvalidCapability` is updated to its correct post-split variant (rights failures → `MissingRight`; stale-handle/destroyed-object → `StaleHandle`), and the `sched` bridge test is updated.
- [ ] New host tests pin each new variant on a path that does **not** already prove it — at minimum a `WrongObjectKind` test for an endpoint operation and for `ipc_notify` (a wrong-kind cap), and a `StaleHandle` test for `ipc_send`/`ipc_recv` against a destroyed endpoint.
- [ ] `Capability`'s `Debug` impl is custom (not derived) and prints `Capability { rights: <rights>, object: <redacted> }` — `rights` visible, the named object redacted — per [ADR-0030 §"Security of the taxonomy split"](../../../decisions/0030-syscall-abi.md#security-of-the-taxonomy-split) and the K3-9 redaction requirement. A host test pins that the output contains the rights and the literal `<redacted>` and does **not** contain the object's handle.
- [ ] All gates green: `cargo fmt --all -- --check`, `cargo host-test`, `cargo host-clippy`, `cargo kernel-clippy`, `cargo kernel-build`, and `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt`.
- [ ] Docs updated: [`docs/architecture/ipc.md`](../../../architecture/ipc.md) §"`IpcError` taxonomy", [`docs/architecture/security-model.md`](../../../architecture/security-model.md) redaction rule broadened to capabilities, [`docs/glossary.md`](../../../glossary.md) syscall terms, the ADR index, and the [ADR-0017](../../../decisions/0017-ipc-primitive-set.md) §Revision-notes rider.

## Out of scope

- The EL0→EL1 `SVC` trap trampoline, the panic-free dispatcher, `SyscallError`, and copy-from/to-user — all [T-021](T-021-syscall-dispatch.md).
- Splitting `IpcError::InvalidTransferCap` (note C3-008) — deferred to a future ADR when a userspace transfer consumer needs the `TransferCapHasChildren` distinction.
- Redacting `CapObject` / `CapHandle` / `SlotId` `Debug` impls themselves — the redaction is at the `Capability` boundary, where the rights+object pairing is the sensitive unit; the handle types remain `Debug` for kernel-internal diagnostics that never cross to userspace.
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

All acceptance criteria checked; gates green (incl. Miri — a [Phase-B exit prerequisite](../../../roadmap/phases/phase-b.md) with weight on `sched`/`ipc`); docs updated; ADR-0017 rider added; `current.md` reflects T-020 Done and B5 in progress. **Security-relevant** (capabilities + IPC): flagged for explicit review per CLAUDE.md.

## Design notes

- The validation **order change** (kind-before-rights) is observable only for a capability that is both wrong-kind *and* missing-right; all existing rights-failure tests use correct-kind caps and remain `MissingRight`. Documented in [ADR-0030 §"The K2-5 `IpcError` split"](../../../decisions/0030-syscall-abi.md#the-k2-5-ipcerror-split-lands-now-in-t-020).
- The security argument for revealing the failure mode (per-subject, unforgeable handles ⇒ no forgery/enumeration aid) is in [ADR-0030 §"Security of the taxonomy split"](../../../decisions/0030-syscall-abi.md#security-of-the-taxonomy-split). The redaction keeps the *object identity* hidden even as the *failure mode* becomes visible — the two are independent surfaces.
- Redaction approach is a custom `impl Debug`, not a `Redacted<T>` wrapper, matching the codebase's direct-impl style and avoiding a cascading wrapper refactor; no code structurally depends on `Capability: Debug`.

## Review history

- _(filled on close)_
