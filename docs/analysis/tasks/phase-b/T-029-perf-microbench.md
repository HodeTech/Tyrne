# T-029 — feature-gated micro-bench (EL0 round-trip / IPC / context-switch)

- **Phase:** B (perf instrumentation; follow-up to the [B6 closure perf baseline](../../reviews/performance-optimization-reviews/2026-06-01-B6-closure.md))
- **Status:** Draft (opened in the B6-closure commit; the [B6 closure perf review](../../reviews/performance-optimization-reviews/2026-06-01-B6-closure.md) defers the per-op micro-measurements here)
- **Created:** 2026-06-01
- **Author:** @cemililik (+ Claude Opus 4.8 agent)
- **Dependencies:** the timer ([ADR-0010](../../../decisions/0010-timer-abstraction.md) — `Cpu::now_ns` / `CNTVCT_EL0`); the scheduler (`yield_now` / `context_switch`), IPC (`ipc_send`/`ipc_recv`), and the EL0 syscall path ([T-028](T-028-el0-userspace-wireup.md)).

---

## User story

As a kernel developer, I want **direct per-operation timing** for the EL0↔EL1 syscall round-trip, the IPC send→recv round-trip, and the cooperative context-switch, so the [B6 closure perf baseline](../../reviews/performance-optimization-reviews/2026-06-01-B6-closure.md) can report real µs numbers for these primitives — which the boot-to-end harness cannot resolve (each is ~µs, far below its ~ms floor).

## Context

The B6 closure perf review established (via a same-host control) that running the first EL0 task adds **no measurable boot-to-end cost** — the per-op costs are below the harness floor. Measuring them **directly** needs new `CNTVCT_EL0`-based instrumentation, which is real `unsafe`-touching kernel/BSP code (the `MRS CNTVCT_EL0` reads are the UNSAFE-2026-0015 family) deserving its own gate + audit pass rather than a closure-tail addition.

## Acceptance criteria

- [ ] **Feature-gated** (`perf-bench`, off by default): a measurement path in the BSP that runs at boot (before the cooperative demo) and prints the µs numbers, compiled out of the production kernel entirely.
- [ ] **Context-switch:** time N round-trips of `cpu.context_switch` (or `yield_now` between two bench tasks) via `now_ns`; report per-switch ns.
- [ ] **IPC round-trip:** time N `ipc_send` + `ipc_recv` cycles on a bench endpoint; report per-round-trip ns.
- [ ] **EL0 round-trip:** time the EL0↔EL1↔EL0 syscall round-trip **kernel-side** (e.g. timing consecutive `syscall_entry` entries for a bench EL0 loop) — **without** exposing `CNTVCT_EL0` to EL0 (no `CNTKCTL_EL1.EL0VCTEN` enable; a timing side-channel Tyrne does not want in production).
- [ ] **No production change:** with the feature off, the kernel binary + smoke + footprint are byte-identical to before; the `unsafe` `MRS` reads are audited (UNSAFE-2026-0015 family / a new entry as needed).
- [ ] **Update the [B6 closure perf baseline](../../reviews/performance-optimization-reviews/2026-06-01-B6-closure.md)** §Micro-measurements with the per-op numbers + methodology.
- [ ] Gates green (fmt, clippy, host tests, kernel build, smoke with + without the feature, Miri).

## Out of scope

- Optimizing any of the measured primitives (this is a *baseline* per the [master plan](../../reviews/performance-optimization-reviews/master-plan.md) — a measured change is a separate cycle).
- Exposing the counter to EL0 (rejected — timing side-channel).

## Review history

- **2026-06-01 — opened Draft** in the B6-closure commit; the [B6 closure perf review](../../reviews/performance-optimization-reviews/2026-06-01-B6-closure.md) records the aggregate (sub-floor) finding and defers the per-op micro-measurements here so the instrumentation gets a focused, gated, audited pass.
