# 0030 — Syscall ABI and userspace error taxonomy

- **Status:** Proposed
- **Date:** 2026-05-29
- **Deciders:** @cemililik

## Context

[Phase B § B5 — Syscall boundary](../roadmap/phases/phase-b.md#milestone-b5--syscall-boundary) opens the first synchronous entry path from EL0 (userspace) into EL1 (kernel). The EL-drop machinery ([ADR-0024](0024-el-drop-policy.md), T-013) and the exception-vector table ([T-012](../analysis/tasks/phase-b/T-012-exception-and-irq-infrastructure.md), [`exceptions.md`](../architecture/exceptions.md)) already exist; what is missing is the **contract** a userspace binary and the kernel agree on when control crosses that boundary: which register carries the syscall number, which registers carry arguments, how a result and an error are returned, and what the userspace-facing error space looks like.

This ADR must be settled **before** any dispatcher or trap trampoline is written, because every later artefact rides on it: the EL0-side `SVC` stub in the future `tyrne-user` crate (B6), the EL1-side register save/restore frame, the dispatcher's argument decode, and the host-side ABI encoder/decoder tests. Choosing the convention after the trampoline lands means re-churning all of them. The same front-loading discipline that [ADR-0027](0027-kernel-virtual-memory-layout.md) (MMU activation) and [ADR-0029](0029-initial-userspace-image-format.md) (image format) applied to their boundaries applies here.

A second, tightly-coupled question lands in this ADR by deliberate bundling (the **K2-5** roadmap item): the **userspace error taxonomy**. Today [`IpcError::InvalidCapability`](../../kernel/src/ipc/mod.rs) collapses three distinct failure modes — a stale/absent handle, a wrong-kind object, and a missing right — behind one variant. The [2026-04-21 Phase-A code review](../analysis/reviews/code-reviews/2026-04-21-tyrne-to-phase-a.md) flagged this as a future improvement; the [error-handling standard §"Error-type design checklist"](../standards/error-handling.md) says each variant must "represent a distinct case a caller could handle differently." The moment a syscall returns these errors to userspace is the moment the distinction becomes load-bearing — a language binding wants to map a stale handle (use-after-free; do not retry) differently from a missing right (permission denied; acquire the right) differently from a wrong-kind handle (a type error in the caller). Designing the syscall error space and splitting the in-kernel `IpcError` **in the same ADR** keeps the two spaces in agreement "from the start", which is exactly what the [phase-b §B5 sub-breakdown](../roadmap/phases/phase-b.md#milestone-b5--syscall-boundary) requires.

The stakes of getting the ABI wrong are bounded but cross-cutting: the register convention is the widest interface in the system (every syscall, every userspace binding) and is hard to change once binaries depend on it. The stakes of getting the taxonomy wrong are lower (`IpcError` is `#[non_exhaustive]`, so it can grow), but the security review's redaction concern (the companion `Capability` `Debug` redaction — B5 sub-item 6 / K3-9 — landed in [T-020](../analysis/tasks/phase-b/T-020-syscall-error-taxonomy.md) and discussed under §"Security of the taxonomy split" below) means the error space is part of the userspace-observable surface and deserves a deliberate decision rather than incremental drift.

## Decision drivers

- **AAPCS64 alignment.** Userspace stubs and the kernel dispatcher are both compiled by the same Rust/LLVM aarch64 backend. A convention that reuses the procedure-call register roles (`x0`–`x7` argument/result, `x8` indirect-result/syscall slot by Linux precedent, `x19`–`x29` callee-saved) minimises impedance: the EL0 stub can be a thin `asm!` wrapper and the EL1 side can hand the saved frame to a normal Rust function. Fighting AAPCS64 costs hand-written shuffling on both sides.
- **Panic-free return of every error.** The [dispatcher must be panic-free on every untrusted input](../roadmap/phases/phase-b.md#milestone-b5--syscall-boundary) (B0's hardening pattern). The error-return encoding must therefore be able to represent *every* failure as a value in a register — never as a trap, never as a sentinel that aliases a valid result. This rules out "return `-1` and read a thread-local errno later" style schemes that need extra state.
- **Agreement between in-kernel and userspace error spaces.** The kernel already has granular per-module error enums ([`CapError`](../../kernel/src/cap/mod.rs) with `InvalidHandle` / `InsufficientRights` / `WrongKind`; [`IpcError`](../../kernel/src/ipc/mod.rs); `AddressSpaceError`; `LoadError`; `SchedError`). The syscall error space should *compose* from these via `From` impls per the [error-handling standard §3 / §7](../standards/error-handling.md), not re-invent a parallel flat space that drifts out of sync. The `IpcError` collapse is the one place where the in-kernel space is *less* granular than userspace needs, so it is split here.
- **Result/value disambiguation.** A capability kernel routinely returns a fresh `CapHandle` (an opaque `u32`-ish index) or a byte count from a syscall. A Linux-style "negative = -errno, non-negative = value" scheme forces every such return through a signedness reinterpretation and steals the high bit from the value space. A capability handle or a length that happens to look like `-EFAULT` is a latent confusion. A *dedicated status register* removes that ambiguity at the cost of one register.
- **Argument width.** The widest v1 syscall (`send`) needs an endpoint handle + a message label + three payload words + an optional transfer handle = up to six argument words. The convention must carry at least six arguments without spilling to the stack, because copy-from-user of a stack-spilled argument block is exactly the unvalidated-pointer hazard B5 sub-item 5 exists to prevent.
- **Forward-portability.** The convention is chosen for aarch64 but should not bake in anything that a second architecture (a future RISC-V or x86-64 port) could not mirror with its own register file. "Syscall number in a general register, args in argument registers, status + payload in result registers, a synchronous trap instruction" is a shape every architecture can express; "syscall number in the `SVC` 16-bit immediate" is aarch64-specific.
- **No information leak that aids forgery.** Splitting `InvalidCapability` reveals *which* validation step failed. For a capability system this is safe (see §Decision outcome → "Security of the taxonomy split"), but the decision must say *why* explicitly rather than assume it.

## Considered options

### Syscall-number location

1. **Number in `x8`, args in `x0`–`x5`, `SVC #0`** (Linux-aarch64 shape). A general register carries the syscall number; the `SVC` immediate is always `0`.
2. **Number in the `SVC` immediate (`SVC #n`), args in `x0`–`x7`.** The trap instruction itself encodes the syscall.
3. **Hybrid: small "syscall class" in the `SVC` immediate, sub-number in `x8`.** Two-level dispatch.

### Result / error encoding

A. **Dedicated status register: `x0` = status word (0 = `Ok`, non-zero = stable error code), `x1`+ = payload.** Result and error never alias.
B. **Signed `x0`: negative = `-errno`, non-negative = value** (Linux). One register carries both.
C. **Condition-flag based: `PSTATE.C` set on error, `x0` = value-or-code.** The carry bit discriminates.

## Decision outcome

Chosen options: **Syscall-number Option 1** (`x8` = number, `x0`–`x5` = args, `SVC #0`) and **error-encoding Option A** (dedicated status register `x0`, payload in `x1`–`x7`), plus the **K2-5 `IpcError` split** and the **`SyscallError` composition type**.

### Register calling convention (v1)

| Register | On entry (EL0 → EL1) | On return (EL1 → EL0) |
|----------|----------------------|------------------------|
| `x8` | Syscall number (see [ADR-0031](0031-initial-syscall-set.md)) | clobbered |
| `x0`–`x5` | Argument words 0–5 (syscall-specific; see ADR-0031) | `x0` = **status** (`0` = `Ok`; non-zero = `SyscallError` code), `x1`–`x7` = return payload (syscall-specific; v1 uses at most `x1`–`x6`, for `recv`) |
| `x6`, `x7` | reserved (must be ignored by the kernel in v1) | clobbered |
| `x9`–`x18` | caller-saved scratch (AAPCS64) | clobbered |
| `x19`–`x29`, `SP_EL0`, `x30` (LR) | preserved by the kernel across the trap | preserved |
| `PSTATE` | — | restored from `SPSR_EL1` by `ERET` |

The trap instruction is **`SVC #0`**. The `SVC` immediate is not used to carry information in v1 — keeping it `0` leaves the immediate free for a future fast-path class split (Option 3) without re-encoding existing stubs. The kernel reads the syscall number from `x8`, the arguments from `x0`–`x5`, validates the caller's capabilities, performs the operation, writes `x0` (status) and `x1`–`x7` (payload), and `ERET`s. No syscall reads or writes userspace memory implicitly: any pointer passed in an argument register is validated by copy-from/to-user against the **active** address space (B5 sub-item 5, T-021) before the kernel touches the bytes.

The concrete per-syscall argument and return-register layout, and the concrete syscall numbers, are settled by [ADR-0031](0031-initial-syscall-set.md); this ADR fixes only the *convention* those layouts instantiate.

### Error-return encoding and the `SyscallError` space

`x0` is the **status word**: `0` means `Ok` (read the payload from `x1`–`x7`, syscall-specific); any non-zero value is a stable `SyscallError` discriminant and the payload registers are undefined. The kernel-side error type is:

```rust
#[non_exhaustive]
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum SyscallError {
    BadSyscallNumber,          // x8 named no syscall in the v1 set
    BadArgument,               // an argument was structurally invalid (e.g. label width)
    FaultAddress,              // a user pointer fell outside the active address space
    Cap(CapError),             // capability-table failure (composed via From)
    Ipc(IpcError),             // IPC failure (composed via From)
    // address-space / loader variants land with their first syscall consumer
}
```

`SyscallError` is built by `From<CapError>` / `From<IpcError>` impls per the [error-handling standard §7 "preserve root cause"](../standards/error-handling.md) — the dispatcher does not collapse distinct IPC failures into a generic "internal error". The flat numeric encoding (which non-zero integer each variant maps to) is a stable contract pinned by host ABI tests **when the dispatcher lands (T-021)**; this ADR fixes that the encoding *exists*, is stable, is composed (not re-invented), and that `0` is reserved for `Ok`. `SyscallError` is **not** introduced as dead code ahead of its first producer: the type lands in [T-021](../analysis/tasks/phase-b/T-021-syscall-dispatch.md) alongside the dispatcher that constructs it, consistent with the codebase's no-speculative-surface discipline ([`CapRights::from_raw`](../../kernel/src/cap/rights.rs) §"Forward-API note C1-007" is the analogous "land it with its first ABI consumer" precedent).

### The K2-5 `IpcError` split (lands now, in T-020)

The one in-kernel error that is *less* granular than the userspace space needs is split immediately, because it is pure-Rust and host-testable without any trampoline:

`IpcError::InvalidCapability` → **`IpcError::StaleHandle`** + **`IpcError::MissingRight`** + **`IpcError::WrongObjectKind`**.

The mapping at each validation site:

- **`StaleHandle`** — the capability handle did not resolve in the table (`lookup` failed), or the named kernel object was destroyed (arena `get`/`get_mut` returned `None` after a generation bump). "The reference is dead; re-acquire, do not retry."
- **`WrongObjectKind`** — the capability resolved but names the wrong kind of object for the operation (e.g. a `Notification` cap handed to `ipc_send`). "Programming error in the caller; you passed the wrong handle."
- **`MissingRight`** — the capability resolved and is the right kind, but does not carry the right the operation requires (`SEND` / `RECV` / `NOTIFY`). "You hold the object but lack authority; obtain the right."

The validation **order** is `StaleHandle → WrongObjectKind → MissingRight` (resolve → type-check → authority-check). This is the natural diagnostic precedence — a wrong-kind handle is a more fundamental error than a missing right — and it matches [`CapError`](../../kernel/src/cap/mod.rs)'s existing `InvalidHandle` / `WrongKind` / `InsufficientRights` shape so the two spaces read the same way. Re-ordering is observable only for a capability that is *both* wrong-kind and missing-right; all existing rights-failure tests use correct-kind capabilities and therefore continue to return `MissingRight` unchanged.

There are **two distinct `StaleHandle` sources with different precedence**. The first — a *cap-table* `lookup` miss — is the resolve step and ranks first, ahead of kind and rights. The second — an *arena* staleness miss (the cap resolves and is the right kind, but the named kernel object was destroyed and `arena.get` returns `None`) — is structurally a *later* check: it needs an already-resolved, kind-checked, **rights-authorized** handle to index the arena, so in the operation bodies (`ipc_send` / `ipc_recv` / `ipc_notify` / `ipc_cancel_recv`) it runs *after* the rights check. Consequently a capability that is the right kind, lacks the right, **and** names a destroyed object reports `MissingRight`, not `StaleHandle`. This is intentional and harmless: both facts concern the caller's own handle, and "you don't hold the right" is the more actionable answer; the strict `StaleHandle`-first total order applies to the *resolve* step, not to the post-authorization arena-liveness re-check.

`IpcError::InvalidTransferCap` is **not** split in this ADR. Its collapse (`InvalidHandle` vs `HasChildren`, documented as note C3-008 in [`ipc/mod.rs`](../../kernel/src/ipc/mod.rs)) is a separate, transfer-side distinction; `IpcError` is `#[non_exhaustive]`, so a `TransferCapHasChildren` variant can be added by a later ADR without a breaking change when a userspace transfer consumer needs it. Splitting it now would be speculative.

### Security of the taxonomy split

Collapsing the three failure modes was originally defended as attacker-resistance — the caller cannot learn *which* check failed. Splitting reverses that, so the decision must justify why it is safe:

A capability table is **per-subject and unforgeable** ([ADR-0014](0014-capability-representation.md)). A task only ever sees handles into its **own** table; generation tags prevent a stale handle from aliasing a live one. The three new variants therefore reveal only facts about handles the caller already possesses and controls: that *its own* handle is stale, names the wrong kind, or lacks a right. None of this helps forge a capability, enumerate another subject's caps, or mount a confused-deputy attack — the information is about the caller's own authority, not the kernel's secrets. The diagnostic value (a genuine [error-handling §checklist](../standards/error-handling.md) "handleable distinction") therefore dominates the negligible residual leak. This is the explicit trade ADR-0030 accepts. (The *object identity* a capability names — the slot index / generation — remains redacted from `Capability`'s `Debug` impl per B5 sub-item 6 / K3-9, landed in T-020; the taxonomy split does not expose it.)

### Simulation

A worst-case EL0 `SVC` handshake through the chosen convention (`(state-pre, action, state-post, observable)`):

| Step | State pre | Action | State post | Observable effect |
|------|-----------|--------|------------|-------------------|
| 0 | EL0 task running; `x8`=NR, `x0`–`x5`=args | `SVC #0` | `ELR_EL1`←PC+4, `SPSR_EL1`←PSTATE, `PSTATE.EL`←1, `PC`←`VBAR_EL1`+0x400 (lower-EL aarch64 sync) | trap into EL1 sync vector; **no kernel state mutated yet** |
| 1 | EL1 sync vector; user GPRs live | save `x0`–`x30` + `SP_EL0` to the trap frame; read `ESR_EL1.EC`; `0b010101` (SVC64) → syscall dispatch, else → fault routing (B5 out-of-scope) | trap frame holds user regs; Rust dispatcher entered with `(nr=x8, args=x0..x5)` | dispatcher runs at EL1 on the kernel stack |
| 2 | dispatcher; `nr` not in the v1 set | `decode(nr)` → `None` | `x0`←`SyscallError::BadSyscallNumber` code; payload registers undefined | **panic-free**; no capability touched; falls through to ERET |
| 3 | dispatcher; `nr`=`send`; `ep_cap` stale / wrong-kind / missing `SEND` | `ipc_send` → `Err(IpcError::{StaleHandle\|WrongObjectKind\|MissingRight})` → `From` → `SyscallError::Ipc(_)` | `x0`←non-zero status; payload undefined; **endpoint + caller-table state unchanged** (pre-flight returns before mutation) | typed error, no panic, observable state byte-identical to pre-call |
| 4 | dispatcher; `nr`=`console_write(cons_cap, ptr, len)`; `cons_cap` valid but `[ptr,ptr+len)` not mapped in the active AS | capability check on `cons_cap` passes (debug-console cap, per [ADR-0031](0031-initial-syscall-set.md)); then `copy_from_user` validates the range against the active translation → out of range | `x0`←`SyscallError::FaultAddress`; **no raw deref of `ptr`** | panic-free; capability-gated; the kernel never dereferences an unvalidated user pointer |
| 5 | dispatcher; `nr`=`send`; ok | `ipc_send` → `Ok(outcome)`; restore frame | `x0`←`0` (`Ok`); `x1`←outcome encoding; `ERET` | return to EL0; `SPSR_EL1`/`ELR_EL1` restore PSTATE+PC; results in `x0`/`x1` |

#### Simulation row-to-verification mapping

Per the [`write-adr` skill §Procedure step 5 sub-bullet](../../.agents/skills/write-adr/SKILL.md), each row maps to a concrete verification artefact in an implementing task:

- **Row 3 (IPC error taxonomy) → [T-020](../analysis/tasks/phase-b/T-020-syscall-error-taxonomy.md)** host tests: the per-variant `ipc_send`/`ipc_recv`/`ipc_notify`/`ipc_cancel_recv` tests pinning `StaleHandle` / `WrongObjectKind` / `MissingRight`, plus the `From<IpcError> for SyscallError` round-trip test (the latter lands with `SyscallError` in T-021). T-020 discharges this row **now**.
- **Rows 0, 1 (`SVC` trap + register frame save/restore) — split across two milestones.** The dispatcher and trap-frame asm are **shared** code that is privilege-entry-agnostic; the *only* difference between the two entry paths is which `VBAR_EL1` slot the handler is installed at and which mode `SPSR_EL1` restores. The table's row 0 describes the **real EL0 ABI** path — an `SVC` from EL0 takes the **lower-EL-AArch64** sync vector at `VBAR_EL1 + 0x400` and `ERET`s back to EL0. **A real EL0 task cannot take this trap until B6** (it needs kernel mappings in its address space so the vector fetch translates, plus an EL0-ready context register file — both gated on the [ADR-0033 high-half placeholder](0027-kernel-virtual-memory-layout.md)). So **rows 0/1 are runtime-verified in B6**, not B5. **T-021's B5-reachable proxy** is an **EL1 kernel-stub** that issues `SVC #0`, which — because it executes at the *current* EL — takes the **current-EL-with-SPx** sync vector at `VBAR_EL1 + 0x200`, **not** the lower-EL vector. T-021 therefore installs the same dispatcher at *both* the `0x200` and `0x400` sync slots, host-tests the dispatcher logic directly, and smoke-tests the shared trap-frame-save → decode → `ERET` mechanism via the `0x200` self-`SVC` path (new `UNSAFE-YYYY-NNNN` audit entry). What the `0x200` proxy does **not** prove — the `0x400` vector entry itself, the EL0↔EL1 privilege transition, and copy-user against a *separate* userspace `TTBR0_EL1` AS — is exactly what B6's real EL0 round-trip closes.
- **Row 2 (unknown number → `BadSyscallNumber`) → T-021**: host dispatcher decode test.
- **Row 4 (capability check + copy-from-user bounds) → T-021**: host copy-from/to-user range-validation tests + the debug-console capability check ([ADR-0031](0031-initial-syscall-set.md)).
- **Row 5 (success `ERET`) → T-021** for the `0x200` proxy round-trip (host ABI encode/decode + smoke); the real EL0 `0x400` round-trip → **B6**.

T-020 discharges row 3 in this milestone. T-021 discharges rows 2/4 and the *mechanism* half of rows 0/1/5 (via the `0x200` current-EL proxy + host tests). The *real-EL0* half of rows 0/1/5 (the `0x400` lower-EL vector + privilege transition + userspace-AS copy-user) is runtime-verified in **B6**, when a real EL0 task first exists. No row is left without a named artefact, and no row's verification is over-claimed for the milestone it lands in (avoiding both the skill's "Simulation table without verification = documentation drift" anti-pattern and an over-stated B5 smoke).

### Dependency chain

For this decision to be **fully** in effect:

```text
1. Split IpcError::InvalidCapability → StaleHandle / MissingRight / WrongObjectKind
   across ipc/mod.rs + sched/mod.rs + tests; redact Capability's Debug (K3-9). — T-020 (opens with this ADR)
2. SyscallError composition type + From<CapError>/From<IpcError> impls.            — T-021 (opens with this ADR)
3. EL0-sync exception-vector entry + user-register trap frame save/restore.       — T-021
4. Panic-free syscall dispatcher (x8 decode → handler → x0/x1.. encode).          — T-021
5. copy-from/to-user validated against the active address space.                  — T-021
6. The concrete v1 syscall set + per-call register layout + numbers.              — ADR-0031 (opens with this ADR)
7. Kernel mappings in the userspace AS + EL0-ready Task context register file
   (so a real EL0 task can take the trap and the EL1 vector fetch translates).    — ADR-0033 (high-half;
                                                                                     slot reserved, opens with
                                                                                     the first per-task TTBR0 swap)
8. tyrne-user safe syscall wrapper crate + first EL0 caller.                       — Phase B6 (deferred)
```

Steps 1–2 + 6 are grounded in tasks/ADRs opened in the same commit set as this ADR (T-020, T-021, ADR-0031), per [ADR-0025 §Rule 1](0025-adr-governance-amendments.md). Steps 3–5 are T-021's scope. Step 7 is the [ADR-0033 high-half placeholder](0027-kernel-virtual-memory-layout.md) (named-but-unallocated, the same forward-flag shape [ADR-0029](0029-initial-userspace-image-format.md) used for ADR-0034) — until it lands, the syscall path is exercised by an **EL1 kernel-stub caller** (B5 acceptance criterion #7), not a real EL0 task. Step 8 is the natural B6 work and is not opened today.

## Consequences

### Positive

- **The widest interface in the system is settled once, before any code depends on it.** The EL0 stub, the EL1 frame, the dispatcher, the host ABI tests, and the `tyrne-user` crate all instantiate one written convention. No "decide the ABI by what the first trampoline happened to do" drift.
- **Result and error never alias.** The dedicated status register means a `CapHandle`, a byte count, or a `Message` word returned in `x1` can take any bit pattern — including ones that would look like `-EFAULT` under a signed-errno scheme — without ambiguity. This removes a whole class of latent confusion that Linux's convention carries.
- **The in-kernel and userspace error spaces agree from the start.** `SyscallError` composes from `CapError` / `IpcError` via `From`; the `IpcError` split removes the one place where the kernel was coarser than userspace needs. A binding can map every failure to a distinct, handleable cause.
- **The taxonomy split is immediately useful and immediately testable.** Splitting `InvalidCapability` is pure-Rust; T-020 lands it with host tests in this milestone, well ahead of the trampoline, so the error space is exercised by the existing IPC test suite before the first syscall exists.
- **AAPCS64 reuse keeps both sides thin.** The EL0 stub is a register-load + `SVC #0`; the EL1 side hands a saved frame to ordinary Rust. No bespoke marshalling.

### Negative

- **Six argument registers cap the v1 syscall arg width.** A syscall needing more than six word-sized arguments must pass a pointer to an argument block — which then needs copy-from-user validation. *Mitigation:* the v1 set ([ADR-0031](0031-initial-syscall-set.md)) is designed to fit in six registers (`send` is the widest at six). When a wider syscall surfaces (B6+), it uses the already-required copy-from-user path; no ABI change.
- **One register spent on status.** Option B (signed errno) would free `x0` to carry a value. *We accept this cost* because the disambiguation it buys (no value/-errno aliasing) is worth one register in a 31-register file, and a capability kernel returns opaque handles constantly.
- **The taxonomy split reveals which validation step failed.** A marginal information leak versus the prior collapse. *We accept this* on the §"Security of the taxonomy split" argument: the facts revealed are about the caller's own per-subject, unforgeable handles and aid no forgery or enumeration. The decision is explicit, not incidental.
- **`SyscallError`'s concrete numeric encoding is deferred to T-021.** This ADR fixes the convention but not the integers. *Mitigation:* the integers are a stable contract the moment T-021's host ABI tests pin them; deferring avoids committing numbers before the dispatcher's shape is concrete, and `0 = Ok` (the only number userspace branches on structurally) is fixed here.

### Neutral

- **`SVC #0` leaves the immediate free.** A future fast-path "syscall class" split (Option 3) can use the `SVC` immediate without re-encoding v1 stubs, because v1 stubs all use `#0`.
- **The convention is aarch64-shaped but architecture-portable in spirit.** "Number in a GPR, args in arg regs, status+payload in result regs, synchronous trap" is expressible on RISC-V (`ecall`, `a7`=nr, `a0`–`a5` args) and x86-64 (`syscall`, `rax`=nr) with the same structure; only the register names change. No second-architecture ADR is forced today.
- **`x6`/`x7` reserved, not used.** v1 ignores them; reserving rather than repurposing keeps room for a seventh/eighth argument or a future flags word without a convention break.

## Pros and cons of the options

### Syscall-number Option 1 — number in `x8`, `SVC #0` (chosen)

- **Pro:** Matches Linux-aarch64, so the mental model and any borrowed tooling/disassembly intuition transfer; `x0`–`x7` stay free for arguments/results.
- **Pro:** The `SVC` immediate stays `0` and free for a future class split.
- **Pro:** Architecture-portable shape (a GPR carries the number).
- **Con:** Costs one register (`x8`) that a pure-immediate scheme would leave free for an argument.

### Syscall-number Option 2 — number in the `SVC` immediate

- **Pro:** Frees `x8`; the trap instruction self-documents the call in a disassembly.
- **Con:** The `SVC` immediate is 16 bits and **aarch64-specific** — a second-architecture port cannot mirror it (RISC-V `ecall` / x86-64 `syscall` carry no immediate), forcing a divergent convention later.
- **Con:** The number is baked into the instruction stream, so a syscall stub cannot compute its number at runtime (e.g. a generic `syscall(nr, ...)` shim) — every syscall needs its own hand-written `SVC #n`.

### Syscall-number Option 3 — hybrid class + sub-number

- **Pro:** Enables a fast-path class (e.g. a register-only `send`) without a table lookup.
- **Con:** Two-level dispatch is premature for a five-syscall v1 set; pure over-engineering today. *Kept available* by Option 1's free `SVC` immediate.

### Error-encoding Option A — dedicated status register (chosen)

- **Pro:** Result and error never alias; payload registers carry any bit pattern.
- **Pro:** Maps one-to-one onto Rust `Result<Payload, SyscallError>` on both sides.
- **Con:** Spends one register on status.

### Error-encoding Option B — signed `-errno` in `x0`

- **Pro:** Frees a register; the universal Unix convention.
- **Con:** Steals the high bit / negative range from every value return; a handle or length that aliases `-errno` is a latent bug. Bad fit for a kernel that returns opaque handles constantly.

### Error-encoding Option C — condition-flag (`PSTATE.C`)

- **Pro:** Frees `x0` entirely for the value.
- **Con:** `PSTATE` is restored from `SPSR_EL1` by `ERET`; threading a result flag through the saved-PSTATE path is fragile and easy to clobber. Architecture-specific and error-prone. Rejected.

## References

- [Phase B §B5 — Syscall boundary](../roadmap/phases/phase-b.md#milestone-b5--syscall-boundary) — milestone scope, including the K2-5 bundle and the panic-free-dispatcher requirement.
- [ADR-0024 — EL drop to EL1 policy](0024-el-drop-policy.md) — the EL0/EL1 privilege boundary this ABI crosses.
- [ADR-0031 — Initial syscall set](0031-initial-syscall-set.md) — the concrete v1 syscalls + per-call register layout that instantiate this convention.
- [ADR-0017 — IPC primitive set](0017-ipc-primitive-set.md) — the IPC operations whose error taxonomy is split here (see its §Revision notes rider).
- [ADR-0014 — Capability representation](0014-capability-representation.md) — per-subject unforgeable handles; the basis for the taxonomy-split security argument.
- [error-handling standard](../standards/error-handling.md) — §3/§7 `From`-composition, the design checklist's "handleable distinction" rule.
- [`docs/architecture/exceptions.md`](../architecture/exceptions.md) — the EL1 vector table the syscall vector slots into.
- [`docs/architecture/security-model.md`](../architecture/security-model.md) — the userspace→kernel trust boundary.
- [Linux aarch64 syscall ABI](https://www.kernel.org/doc/html/latest/arm64/) — `x8`=number, `x0`–`x5` args, `x0` return (Option 1 / Option B prior art).
- [ARM ARM §D1 "The AArch64 System Level Programmers' Model"](https://developer.arm.com/documentation/ddi0487/latest) — `SVC`, `ESR_EL1.EC`, `ELR_EL1` / `SPSR_EL1` / `ERET` semantics.
- [Procedure Call Standard for the Arm 64-bit Architecture (AAPCS64)](https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst) — caller/callee-saved register roles.
- [seL4 manual §"System Calls"](https://sel4.systems/Info/Docs/seL4-manual-latest.pdf) — message-register / dedicated-status-word prior art for a capability kernel.
