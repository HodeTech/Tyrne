# T-029 — feature-gated micro-bench (EL0 round-trip / IPC / context-switch)

- **Phase:** B (perf instrumentation; follow-up to the [B6 closure perf baseline](../../reviews/performance-optimization-reviews/2026-06-01-B6-closure.md))
- **Status:** Both phases implemented (Phase 1 ctx-switch + IPC merged via PR #44; Phase 2 EL0 syscall round-trip in review). All acceptance criteria met. Split into two phases per the maintainer (measure-then-halt build; methodical pace).
- **Created:** 2026-06-01
- **Author:** @cemililik (+ Claude Opus 4.8 agent)
- **Dependencies:** the timer ([ADR-0010](../../../decisions/0010-timer-trait.md) — `Cpu::now_ns` / `CNTVCT_EL0`); the scheduler (`yield_now` / `context_switch`), IPC (`ipc_send`/`ipc_recv`), and the EL0 syscall path ([T-028](T-028-el0-userspace-wireup.md)).

---

## User story

As a kernel developer, I want **direct per-operation timing** for the EL0↔EL1 syscall round-trip, the IPC send→recv round-trip, and the cooperative context-switch, so the [B6 closure perf baseline](../../reviews/performance-optimization-reviews/2026-06-01-B6-closure.md) can report real µs numbers for these primitives — which the boot-to-end harness cannot resolve (each is ~µs, far below its ~ms floor).

## Context

The B6 closure perf review established (via a same-host control) that running the first EL0 task adds **no measurable boot-to-end cost** — the per-op costs are below the harness floor. Measuring them **directly** needs new `CNTVCT_EL0`-based instrumentation, which is real `unsafe`-touching kernel/BSP code (the `MRS CNTVCT_EL0` reads are the UNSAFE-2026-0015 family) deserving its own gate + audit pass rather than a closure-tail addition.

## Acceptance criteria

- [x] **Feature-gated** (`perf-bench`, off by default): a **measurement build** in the BSP that runs the micro-benches *instead of* the cooperative demo (the maintainer chose measure-then-halt over bench-then-demo — cleaner separation, truly compiled out of production) and prints the µs numbers, compiled out of the production kernel entirely. *(Phase 1: `bsp-qemu-virt/src/perf_bench.rs` + the `kernel_main_high` `#[cfg]` fork.)*
- [x] **Context-switch:** time N round-trips of `yield_now` between two bench tasks via `now_ns`; report per-switch ns. *(Phase 1: 3 595 ns/switch on QEMU-virt/TCG, N = 50 000.)*
- [x] **IPC round-trip:** time N `ipc_send` + `ipc_recv` cycles on a bench endpoint; report per-cycle ns. *(Phase 1: 23 308 ns/cycle, of which ≈16 117 ns is pure IPC over the 2 switches, N = 50 000.)*
- [x] **EL0 round-trip:** time the EL0↔EL1↔EL0 syscall round-trip **kernel-side** (timing consecutive `syscall_entry` entries for a looping EL0 bench task) — **without** exposing `CNTVCT_EL0` to EL0 (no `CNTKCTL_EL1.EL0VCTEN`; a timing side-channel Tyrne does not want in production). *(Phase 2: a hand-assembled 12-byte EL0 image loops a rejected `svc`; a feature-gated `syscall_entry` hook times + force-`Terminate`s it after N → hands off to the ctx/IPC benches. 9 108 ns/syscall on QEMU-virt/TCG, N = 50 000.)*
- [x] **No production change:** with the feature off, the kernel is **code- and footprint-identical** to before — verified each phase: `.text`/`.data`/`.bss` byte-identical, `rust-size` footprint identical; the only ELF difference is `.rodata` `#[track_caller]` panic-location line/col `u32`s shifting (source positions move below the `#[cfg]` forks — a mechanical effect, not codegen), and the feature-off smoke is the unchanged demo trace. No new `unsafe` *operation* — the timing reuses the safe `Timer::now_ns` (its `MRS CNTVCT_EL0` is **UNSAFE-2026-0015**); the bench-caller blocks (incl. the Phase-2 EL0-task load via `load_image`/`add_user_task`) are covered by the **UNSAFE-2026-0014 Amendments** (2026-06-01).
- [x] **Update the [B6 closure perf baseline](../../reviews/performance-optimization-reviews/2026-06-01-B6-closure.md)** §Micro-measurements with the per-op numbers + methodology. *(Phase 1: context-switch + IPC; Phase 2: EL0 round-trip — section complete.)*
- [x] Gates green (fmt, clippy ±feature, host tests, kernel build ±feature, smoke without the feature + a bounded feature-on run, Miri). *(Both phases.)*

## Out of scope

- Optimizing any of the measured primitives (this is a *baseline* per the [master plan](../../reviews/performance-optimization-reviews/master-plan.md) — a measured change is a separate cycle).
- Exposing the counter to EL0 (rejected — timing side-channel).

## Phasing

Split into two phases (maintainer decision, 2026-06-01):

- **Phase 1 — context-switch + IPC** *(merged, PR #44).* The `perf-bench` feature (the workspace's first), `bsp-qemu-virt/src/perf_bench.rs`, the measure-then-halt `#[cfg]` fork, and the two kernel-side benches. Reuses the audited scheduler/IPC bridge (UNSAFE-2026-0014) + the safe `now_ns` — no new `unsafe` operation, no EL0, no `syscall_entry` change.
- **Phase 2 — EL0 syscall round-trip** *(this PR).* A hand-assembled 12-byte EL0 bench image (added to the same `perf_bench::run` scheduler scenario, dispatched first) + a feature-gated `syscall_entry` hook (`el0_roundtrip_tick`) that times consecutive entries and force-`Terminate`s the EL0 task after N (handing off to the ctx/IPC benches). Still no `CNTVCT_EL0` for EL0. Reuses the audited `load_image`/`add_user_task` (UNSAFE-2026-0030/0032) + the Terminate arm (T-028). Completes the baseline §Micro-measurements and flips AC#4/#6.

## Review history

- **2026-06-01 — opened Draft** in the B6-closure commit; the [B6 closure perf review](../../reviews/performance-optimization-reviews/2026-06-01-B6-closure.md) records the aggregate (sub-floor) finding and defers the per-op micro-measurements here so the instrumentation gets a focused, gated, audited pass.
- **2026-06-01 — Phase 1 implemented** (merged via PR #44, incl. a review-round: `Relaxed` PHASE, WFI park, MD040 fence, cross-run-drift note). `perf-bench` feature + `perf_bench.rs` (ctx-switch + IPC) + measure-then-halt fork. Gates green; byte-identity (feature off) `.text`/`.data`/`.bss` + footprint identical (only `.rodata` panic-loc shift). Audit: UNSAFE-2026-0014 Amendment. Numbers (QEMU-virt/TCG, relative-only): ctx-switch 3 595 ns/switch; IPC send→recv cycle 23 308 ns/cycle.
- **2026-06-01 — Phase 2 implemented.** EL0 syscall round-trip: a hand-assembled 12-byte EL0 image loops a rejected `svc`; `el0_roundtrip_tick` (feature-gated `syscall_entry` hook) times consecutive entries + force-`Terminate`s after N → hands off to the ctx/IPC benches (one combined measurement build). Un-gated `USER_TASK_STACK`/`USER_TASK_TABLE` (now the EL0 bench task's `SP_EL1` + empty table). Gates green (fmt, clippy ±feature, host tests, kernel build ±feature, feature-off smoke = unchanged demo trace, one feature-on run captured all three numbers + `perf-bench complete`, Miri). Byte-identity (feature off): `.text`/`.data`/`.bss` + footprint identical, 32-byte `.rodata` panic-loc shift. **EL0 syscall round-trip 9 108 ns/syscall** (QEMU-virt/TCG, N = 50 000) — ≈3.6× a context switch.
