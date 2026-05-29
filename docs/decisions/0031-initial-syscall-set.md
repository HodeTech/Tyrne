# 0031 — Initial syscall set (B-phase)

- **Status:** Accepted
- **Date:** 2026-05-29
- **Deciders:** @cemililik

## Context

[ADR-0030](0030-syscall-abi.md) settles *how* a syscall is made — the register calling convention (`x8` = number, `x0`–`x5` = arguments, `x0` = status, `x1`–`x7` = payload), the `SVC #0` trap, and the `SyscallError` space. This ADR settles *which* syscalls exist in the B-phase and the concrete per-call register layout each one instantiates.

The set must be **small**. [Phase B § B5](../roadmap/phases/phase-b.md#milestone-b5--syscall-boundary) names the floor and the ceiling in one sentence: "At minimum: `send`, `recv`, `console_write` (debug-gated), `task_yield`, `task_exit`. No more in v1." The reasoning is the same "smallest shape that works now" discipline ADR-0029 (raw-flat image) and ADR-0035 (bitmap PMM) applied: every syscall is a permanent piece of the userspace ABI surface and a panic-free dispatch path the kernel must keep correct forever. Adding a syscall is cheap to write and expensive to ever remove, so v1 ships exactly the calls B6's first "hello" userspace task needs to do useful work and exercise the boundary — and not one more.

What B6's first userspace task must be able to do: print to the serial console (`console_write`), exit cleanly so the kernel reclaims it (`task_exit`), and — to prove the IPC path works end-to-end across the privilege boundary, not just kernel-internally — send and receive on an endpoint (`send` / `recv`). `task_yield` rounds out cooperative multitasking from EL0. Capability-management syscalls (`cap_copy` / `cap_derive` / `cap_revoke`), `notify`, and address-space `map`/`unmap` are deliberately **not** exposed in v1 — no v1 userspace consumer needs them, and the kernel-internal surfaces remain reachable only from EL1.

The stakes: a syscall number, once a userspace binary depends on it, is part of a stable contract. Getting the *set* wrong (too large) is unused attack surface in the dispatcher; getting it too small blocks B6. Getting a per-call layout wrong means re-churning the `tyrne-user` wrapper. The decision is bounded because the numbers and layouts are pinned by host ABI tests when the dispatcher lands ([T-021](../analysis/tasks/phase-b/T-021-syscall-dispatch.md)), so an error is caught mechanically rather than at runtime.

## Decision drivers

- **B6 sufficiency.** The set must be exactly enough for B6's "hello from userspace" + clean exit + an IPC round-trip, and no more. See [phase-b §B6](../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello).
- **Panic-free dispatch surface.** Every syscall is a handler the dispatcher must keep panic-free on all untrusted input ([ADR-0030](0030-syscall-abi.md), B0 hardening). Fewer syscalls = smaller audited surface.
- **Register-budget fit.** Each call's arguments must fit in `x0`–`x5` (six words) and its results in `x0`–`x7` per [ADR-0030](0030-syscall-abi.md), without spilling to a stack-passed block that would need its own copy-from-user validation. The widest call drives the budget.
- **Reuse of existing kernel surfaces.** A syscall handler should be a thin validator + a call into an existing kernel primitive (`ipc_send` / `ipc_recv` / scheduler `yield_now` / the console HAL), not new subsystem logic. The syscall layer adds the EL0 boundary, not new capability semantics.
- **Defence-in-depth on the number space.** An uninitialised `x8` (zero) must not accidentally name a real syscall; a release build must not expose a debug-only console.
- **No capability authority widening.** The syscalls expose operations the caller's capabilities *already* authorise; the syscall layer is a gate, never a new grant. `console_write` is the one debug affordance and is gated accordingly.

## Considered options

1. **The phase-b floor set: `send`, `recv`, `console_write`, `task_yield`, `task_exit` (five).** Exactly what B6 needs.
2. **A larger "useful from day one" set** adding `notify`, `cap_copy` / `cap_derive` / `cap_revoke`, and address-space `map` / `unmap` — so userspace can manage its own capabilities and memory without a later ABI bump.
3. **An ultra-minimal set: `console_write` + `task_exit` (two).** The absolute floor to make B6's greeting + exit work, deferring even IPC from EL0 to a later milestone.

## Decision outcome

Chosen option: **Option 1 — the five-syscall phase-b floor set.**

It is the smallest set that lets B6's first userspace task both *do* something observable (`console_write`, `task_exit`) and *exercise the boundary that B5 exists to build* (`send` / `recv` cross the EL0→EL1 line, proving capability-gated IPC works from userspace, not just kernel-internally). `task_yield` makes cooperative multitasking reachable from EL0 with a near-zero-cost handler. Option 3 is too small — it would ship a syscall boundary that never carries an IPC message, leaving the most security-relevant path (capability-gated `send`/`recv` from untrusted EL0) unexercised until a later milestone, which defeats the point of building the boundary now. Option 2's extra calls have **no v1 consumer**; each would be unused dispatch surface to keep panic-free, and `IpcError`/`CapError` are `#[non_exhaustive]`, so the set can grow without breaking the ABI when a real consumer appears.

### Syscall table (v1)

Numbers instantiate [ADR-0030](0030-syscall-abi.md)'s convention: `x8` = number, arguments in `x0`–`x5`, `x0` = status (`0` = `Ok`), payload in `x1`–`x7`. **Number `0` is reserved-invalid** (an uninitialised `x8` must fault, not dispatch) and always returns `SyscallError::BadSyscallNumber`. The integers `1`–`5` below are a **fixed decision**, not tentative: as an Accepted ABI ADR, this table *is* the contract. T-021's host tests **regression-verify** these numbers and layouts; they do not get to choose them.

| `x8` | Name | Arguments (`x0`…) | Returns (`x0`=status, then payload) | Capability checked | Backing primitive |
|------|------|-------------------|--------------------------------------|--------------------|-------------------|
| `0` | *(reserved-invalid)* | — | always `BadSyscallNumber` | — | — |
| `1` | `send` | `x0`=ep cap handle, `x1`=`msg.label`, `x2..x4`=`msg.params[0..3]`, `x5`=transfer cap handle (or the reserved **null-handle sentinel** = "no transfer") | `x1`=`SendOutcome` (`0`=Delivered, `1`=Enqueued) | endpoint cap (`SEND`) | [`ipc_send`](../../kernel/src/ipc/mod.rs) |
| `2` | `recv` | `x0`=ep cap handle | `x1`=`RecvOutcome` (`0`=Received, `1`=Pending), `x2`=`msg.label`, `x3..x5`=`msg.params[0..3]`, `x6`=transferred cap handle (or null sentinel if none) | endpoint cap (`RECV`) | [`ipc_recv`](../../kernel/src/ipc/mod.rs) |
| `3` | `task_yield` | — (args ignored) | *(no payload)* | self (current task) | scheduler `yield_now` |
| `4` | `task_exit` | `x0`=exit code | **does not return** to the caller | self (current task) | scheduler task-termination (B6) |
| `5` | `console_write` | `x0`=debug-console cap handle, `x1`=user VA of byte buffer, `x2`=length | `x1`=bytes written | debug-console cap (write) | console HAL `write_bytes`, via copy-from-user |

Notes that bind the table:

- **`send` / `recv` carry the `Message` in registers**, not via a user-pointer buffer. A `Message` is four words (`label` + three `params`); register-passing fits the [ADR-0030](0030-syscall-abi.md) budget (`send` uses `x0`–`x5` for args; `recv` returns in `x1`–`x6`) and avoids a copy-from/to-user round-trip on the common small-message path. When messages grow past the register budget (post-v1), a pointer-buffer variant lands without disturbing these numbers. The **null-handle sentinel** that means "no transfer" / "no cap received" is a reserved `CapHandle` value no live handle can take; its exact bit pattern is T-021's encoder detail (it must round-trip with `Option<CapHandle>`).
- **Every syscall that names a *separate* object is capability-gated, per [P1 / P4](../standards/architectural-principles.md).** `send` / `recv` check the endpoint capability (`SEND` / `RECV`); `console_write` checks a **debug-console capability** (its first argument, `x0`). `task_yield` / `task_exit` act on the **caller's own task** — the kernel identifies the caller from its trusted current-task pointer (set at dispatch, not a forgeable argument). This is the caller's inherent authority over its own execution thread, not ambient authority over another object, so these two take no object-capability argument; the trust-boundary check P4 demands is "is there a valid current task?" (always true on the syscall path) plus the kernel never letting the caller name a *different* task. No syscall reaches a privileged effect on another object without a capability.
- **`console_write` is capability-gated *and* debug-gated** — two independent gates. (1) **Capability gate (authority):** the caller must hold a debug-console capability (arg `x0`); the dispatcher validates it (resolves, kind = debug-console, carries the write right) before any output, returning a typed `SyscallError` otherwise — this is the [P1 / P4](../standards/architectural-principles.md)-mandated authority check, present in *all* builds. The concrete `CapObject` kind for the debug console and its grant-at-load wiring are [T-021](../analysis/tasks/phase-b/T-021-syscall-dispatch.md) (object + check) and B6 (grant to the first userspace task). (2) **Debug gate (defence-in-depth):** in a non-debug build the dispatcher additionally treats number `5` as unknown and returns `BadSyscallNumber`, so the debug console is *absent* from the production syscall surface even for a holder of the capability. The exact debug-gate mechanism (`cfg!(debug_assertions)` arm vs. a Cargo feature) is T-021's implementation choice; the two-gate *contract* is fixed here. **`console_write` is the only syscall that takes a user pointer**: its handler validates `[ptr, ptr+len)` against the **active** address space via copy-from-user before touching a byte (B5 sub-item 5); it never dereferences the raw pointer.
- **`task_exit` does not return.** Control does not come back to the caller, so the ABI defines no return value for it. Its real semantics — mark the EL0 task terminated, drop its context, dispatch the next ready task — depend on the per-task EL0 context register file that does not exist until B6 (gated on the [ADR-0033 high-half placeholder](0027-kernel-virtual-memory-layout.md)). T-021 implements the dispatch and a kernel-stub stand-in; the real EL0-task termination lands with B6's first userspace task.
- **`task_yield` always succeeds in v1** (status `Ok`); it is a thin EL0-reachable wrapper over the scheduler's cooperative `yield_now`, acting on the caller's own task.

### Simulation

Representative invocations walking the [ADR-0030](0030-syscall-abi.md) convention (`(state-pre, action, state-post, observable)`):

| Step | State pre | Action | State post | Observable effect |
|------|-----------|--------|------------|-------------------|
| 0 | caller: `x8`=5 (`console_write`), `x0`=valid debug-console cap, `x1`=buf VA, `x2`=len; **debug build**; buf mapped in active AS | dispatch → **cap check on `x0` passes** → copy-from-user validates `[buf,buf+len)` → console `write_bytes` | bytes emitted on serial | `x0`←`0` (`Ok`), `x1`←len; **no raw user-ptr deref** |
| 1 | caller: `x8`=5, `x0`=stale / wrong-kind / no-write debug-console cap | dispatch → **cap check on `x0` fails** before any output | unchanged | `x0`←typed `SyscallError` (`Cap`/`Ipc`-family); **console untouched — authority gate, all builds** |
| 2 | caller: `x8`=5, `x0`=valid cap, `x1`=buf VA, `x2`=len; **buf not mapped** in active AS | cap check passes; copy-from-user range check fails | unchanged | `x0`←`FaultAddress`; kernel never read the buffer |
| 3 | caller: `x8`=2 (`recv`), `x0`=ep cap; a sender already delivered `{label, params, cap}` | `ipc_recv` → `Ok(Received{msg, cap})`; install cap into caller table | endpoint `Idle`; cap in caller table | `x0`←`0`, `x1`←`0`(Received), `x2`←label, `x3..x5`←params, `x6`←new cap handle |
| 4 | caller: `x8`=4 (`task_exit`), `x0`=code | mark caller (the current task) terminated; dispatch next ready task | caller gone; scheduler runs another task | **no return** to caller; kernel reports termination (B6) |

The second, independent **release debug-gate** (number `5` → `BadSyscallNumber` in non-debug builds, even for a capability holder) is not a separate row — it short-circuits dispatch ahead of row 0's cap check and is covered in the binding note above.

#### Simulation row-to-verification mapping

Per the [`write-adr` skill §Procedure step 5 sub-bullet](../../.agents/skills/write-adr/SKILL.md), all rows are discharged by **[T-021](../analysis/tasks/phase-b/T-021-syscall-dispatch.md)** (the dispatcher task), because every row is a trampoline/dispatch behaviour:

- Row 0 (`console_write` happy path, cap check passes) → T-021 host copy-from-user test + the QEMU kernel-stub-SVC smoke trace showing the emitted bytes.
- Row 1 (debug-console **capability check fails**) → T-021 host dispatcher test asserting a stale/wrong-kind/no-write cap yields a typed `SyscallError` with no console output (the [P1 / P4](../standards/architectural-principles.md) authority gate).
- Row 2 (`FaultAddress`) → T-021 host copy-from-user out-of-range test.
- Row 3 (`recv` register unpack) → T-021 host ABI encode/decode round-trip test over `RecvOutcome` + `Message` + `Option<CapHandle>`.
- Row 4 (`task_exit` no-return) → T-021 dispatcher test (kernel-stub stand-in); real EL0 termination → B6.
- The release **debug-gate** → T-021 host dispatcher test asserting number `5` → `BadSyscallNumber` under `not(debug_assertions)`.

The IPC *error-taxonomy* rows these syscalls inherit (a `send` to a stale/wrong-kind/no-`SEND` cap) are discharged by **[T-020](../analysis/tasks/phase-b/T-020-syscall-error-taxonomy.md)** per [ADR-0030 §Simulation row 3](0030-syscall-abi.md#simulation). The runtime EL0-vs-EL1 verification split (B5 kernel-stub via the current-EL `0x200` vector vs. B6 real EL0 via `0x400`) is recorded in [ADR-0030 §Simulation row-to-verification mapping](0030-syscall-abi.md#simulation).

### Dependency chain

For this decision to be **fully** in effect:

```text
1. Syscall calling convention + SyscallError space.                 — ADR-0030 (opens with this ADR)
2. Panic-free dispatcher decoding x8 → one of {1..5}, else
   BadSyscallNumber; number 0 reserved-invalid.                     — T-021 (opens with this ADR)
3. Handlers wiring each syscall to its backing primitive
   (ipc_send/ipc_recv/yield_now/console write_bytes/terminate).     — T-021
4. Debug-console capability kind (CapObject) + the dispatcher's
   capability check for console_write (the P1/P4 authority gate).   — T-021 (object + check)
5. copy-from-user for console_write's buffer.                       — T-021
6. The release debug-gate mechanism for console_write.              — T-021 (design-notes choice)
7. EL0-ready Task context so task_exit/task_yield have a real EL0
   task to terminate/reschedule.                                    — ADR-0033 (placeholder) + Phase B6
8. Debug-console capability granted to the first userspace task.    — Phase B6
9. tyrne-user safe wrappers exposing these five calls.              — Phase B6 (deferred)
```

Steps 1–6 are grounded in ADR-0030 + T-021, opened in the same commit set as this ADR per [ADR-0025 §Rule 1](0025-adr-governance-amendments.md). Steps 7–9 are explicit forward-flags (the [ADR-0033 high-half placeholder](0027-kernel-virtual-memory-layout.md) and B6), the same shape [ADR-0029](0029-initial-userspace-image-format.md) used for its deferred build-pipeline step. Until step 7 lands, the five syscalls are exercised by an EL1 kernel-stub caller (B5 acceptance criterion #7), not a real EL0 task.

## Consequences

### Positive

- **The dispatch surface is minimal and fully audited.** Five real syscalls + one reserved-invalid number; every handler is a thin validator over an existing kernel primitive. Nothing to keep panic-free that no consumer needs.
- **The boundary is exercised, not just built.** `send`/`recv` from EL0 prove capability-gated IPC across the privilege line — the highest-value B5 test — rather than deferring it.
- **Every object-naming syscall is capability-gated; no ambient authority.** `send`/`recv` check the endpoint cap, `console_write` checks a debug-console cap, and `task_yield`/`task_exit` act only on the caller's own (trusted-current-task) identity — upholding [P1 / P4](../standards/architectural-principles.md) uniformly across the v1 set.
- **`0`-reserved + the release debug-gate are defence-in-depth on top of the capability gate.** An uninitialised syscall number faults; production builds drop `console_write` from the surface entirely even for a capability holder.
- **Register-passing keeps the common path allocation-free and copy-free.** Only `console_write` touches user memory, so only one handler carries the copy-from-user cost; `send`/`recv` stay register-only.
- **`#[non_exhaustive]` error spaces mean the set can grow safely.** Adding `notify` or `cap_*` later is additive — new numbers, new `From` paths — with no break to the v1 five.

### Negative

- **No userspace capability management in v1.** A v1 EL0 task cannot `cap_copy`/`derive`/`revoke` its own caps; it works only with the caps the loader/parent granted. *Mitigation:* no v1 userspace needs this; the kernel-internal cap operations remain available, and the syscalls land when a real consumer (a multi-task userspace service, post-B6) surfaces.
- **No `notify` from EL0.** An EL0 task cannot signal a notification. *We accept this* — v1's notification users are kernel-internal; the syscall is additive later.
- **`Message` is register-bound to four words.** A larger payload needs a pointer-buffer variant. *Mitigation:* the four-word `Message` is fixed by [ADR-0017](0017-ipc-primitive-set.md); a wider message is a separate ADR with its own syscall number, leaving these layouts intact.
- **`task_exit` semantics are only half-real in B5.** Until B6's EL0 context exists, `task_exit` is dispatcher-plumbing over a kernel-stub. *Mitigation:* the ABI shape ("does not return") is fixed now; the termination behaviour lands with the task it terminates.

### Neutral

- **Syscall numbers `0`–`5` are a fixed decision, not tentative.** As an Accepted ABI ADR, this table is the contract; T-021's host tests regression-verify the numbers and layouts, they do not choose them.
- **The release debug-gate *mechanism* is left to T-021** (a `cfg!(debug_assertions)` arm vs. a Cargo feature) — but the gate's *existence* and the capability check are both fixed decisions here.
- **A new `CapObject` kind (debug console) lands in T-021.** This is the smallest object addition that keeps `console_write` capability-gated; it is the first capability kind introduced by a syscall rather than by the kernel-object subsystem directly.
- **The set maps one-to-one onto the future `tyrne-user` crate's public API.** B6's wrapper crate exposes exactly these five.

## Pros and cons of the options

### Option 1 — five-syscall floor set (chosen)

- **Pro:** Exactly B6's needs; smallest panic-free dispatch surface.
- **Pro:** Exercises the capability-gated IPC boundary from EL0 (the key B5 test).
- **Pro:** Register-only for four of five calls; one copy-from-user path.
- **Con:** No EL0 cap-management / `notify` in v1 (additive later; no v1 consumer).

### Option 2 — larger "useful from day one" set

- **Pro:** Userspace can manage its own caps + memory without a later ABI bump.
- **Con:** Every added call is unused dispatch surface that must be kept panic-free with **no v1 consumer** to validate it — speculative ABI.
- **Con:** Larger audited attack surface at the most security-sensitive boundary, for zero v1 benefit.
- **Con:** `#[non_exhaustive]` already makes growth non-breaking, so the "avoid a later bump" pro is moot.

### Option 3 — ultra-minimal `console_write` + `task_exit`

- **Pro:** Absolute smallest path to B6's greeting + exit.
- **Con:** Ships a syscall boundary that never carries an IPC message — the most security-relevant EL0→EL1 path (capability-gated `send`/`recv`) stays unexercised, defeating the purpose of building the boundary in B5.
- **Con:** `task_yield` is near-free to add and makes cooperative EL0 multitasking reachable; omitting it is false economy.

## References

- [Phase B §B5 — Syscall boundary](../roadmap/phases/phase-b.md#milestone-b5--syscall-boundary) — the floor/ceiling sentence this ADR implements.
- [Phase B §B6 — First userspace "hello"](../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello) — the consumer that justifies the set.
- [ADR-0030 — Syscall ABI and userspace error taxonomy](0030-syscall-abi.md) — the convention these calls instantiate.
- [ADR-0017 — IPC primitive set](0017-ipc-primitive-set.md) — `send`/`recv`/`notify` and the four-word `Message` shape.
- [ADR-0014 — Capability representation](0014-capability-representation.md) — the `CapHandle` the null-sentinel reserves against.
- [`docs/architecture/ipc.md`](../architecture/ipc.md) — the IPC operations `send`/`recv` wrap.
- [seL4 manual §"System Calls"](https://sel4.systems/Info/Docs/seL4-manual-latest.pdf) — minimal syscall-set prior art for a capability kernel.
