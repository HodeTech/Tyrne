//! # Perf micro-bench (T-029) — feature-gated, off by default.
//!
//! When the `perf-bench` Cargo feature is enabled this BSP becomes a
//! **measurement build**: instead of the cooperative IPC demo + the first EL0
//! task, [`run`] sets up two kernel tasks, drives the scheduler / IPC
//! primitives in tight loops, times each with [`Timer::now_ns`], prints the
//! per-operation cost, and parks. The entire normal workload is compiled out
//! under the feature (see `kernel_main_high`'s `#[cfg]` split), so with the
//! feature **off** the production kernel is byte-identical to before T-029.
//!
//! ## What it measures (Phase 1)
//!
//! - **Context switch.** A *driver* task and a *partner* task ping-pong via
//!   [`yield_now`]. Each driver `yield_now` is one driver→partner switch; the
//!   partner answers with one partner→driver switch — so a driver round-trip is
//!   **two** context switches. We report ns/switch = elapsed / (2·N).
//! - **IPC send→recv cycle.** The driver `ipc_send_and_yield`s to the partner,
//!   which `ipc_recv_and_yield`s in a loop. Each driver send delivers to the
//!   waiting partner and yields; the partner receives and re-arms, yielding
//!   back — so one cycle is **1 send + 1 recv + 2 context switches**. We report
//!   ns/cycle = elapsed / N (and note the composition, since the context-switch
//!   leg is measured independently above).
//!
//! ## Why this needs no new `unsafe`
//!
//! The timestamp is [`QemuVirtCpu`]'s safe [`Timer::now_ns`] (the `CNTVCT_EL0`
//! `MRS` it wraps is already audited as **UNSAFE-2026-0015**). The only
//! `unsafe` here is *calling* the already-audited scheduler/IPC bridge entry
//! points (`yield_now` / `ipc_*_and_yield` / `start` / `add_task`), under the
//! exact [ADR-0021] no-`&mut`-across-switch discipline the demo tasks use
//! (**UNSAFE-2026-0014** + the `StaticCell` mechanics UNSAFE-2026-0010/0013).
//! No new register access and no exposure of `CNTVCT_EL0` to EL0 (T-029 AC#4 /
//! the timing-side-channel constraint) — these are kernel-mode (EL1) reads.
//!
//! ## Reused statics
//!
//! To avoid leaving the demo's statics dead under the feature, the bench
//! *reuses* the crate's scheduler/IPC storage: [`crate::SCHED`],
//! [`crate::TASK_ARENA`], [`crate::EP_ARENA`], [`crate::IPC_QUEUES`],
//! [`crate::TABLE_A`] (driver) / [`crate::TABLE_B`] (partner), the three
//! [`crate::TASK_A_STACK`]/`TASK_B_STACK`/`TASK_IDLE_STACK` stacks, and
//! [`crate::idle_entry`]. Under the feature only this module writes them; under
//! `not(feature)` only the demo does. Each is therefore live in exactly one
//! compiled path.
//!
//! [ADR-0021]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0021-raw-pointer-scheduler-ipc-bridge.md

use core::fmt::Write;
use core::sync::atomic::{AtomicU64, AtomicU8, Ordering};

use tyrne_hal::{Cpu, FmtWriter, Timer, VirtAddr};
use tyrne_kernel::cap::{CapHandle, CapObject, CapRights, Capability, CapabilityTable};
use tyrne_kernel::ipc::{IpcQueues, Message};
use tyrne_kernel::mm::BOOTSTRAP_ADDRESS_SPACE_HANDLE;
use tyrne_kernel::obj::endpoint::{create_endpoint, Endpoint, EndpointArena};
use tyrne_kernel::obj::task::{create_task, Task, TaskArena};
use tyrne_kernel::obj::task_loader::{load_image, task_create_from_image};
use tyrne_kernel::sched::{
    ipc_recv_and_yield, ipc_send_and_yield, register_idle, start, yield_now, Scheduler,
};
use tyrne_kernel::syscall::SyscallEffect;

use crate::console::Pl011Uart;
use crate::cpu::QemuVirtCpu;

/// Driver round-trips for the context-switch bench (= `2 ×` this many switches).
const N_CTX_ROUNDTRIPS: u64 = 50_000;
/// Send→recv cycles for the IPC bench.
const N_IPC_CYCLES: u64 = 50_000;
/// Untimed iterations run before each timed loop to reach steady state.
const WARMUP: u64 = 256;

/// Bench phase, read by the partner task to decide how to cooperate.
const PHASE_CTX: u8 = 0;
const PHASE_IPC: u8 = 1;
const PHASE_DONE: u8 = 2;

/// The current bench phase. The driver advances it; the partner reads it each
/// loop iteration to switch between "bounce a `yield_now`" and "receive a
/// message". `Relaxed` is sufficient: this is single-core cooperative, and the
/// only writer→reader handoff is across a cooperative context switch, whose
/// register save/restore is a full barrier — there is no cross-core race to
/// order.
static PHASE: AtomicU8 = AtomicU8::new(PHASE_CTX);

/// The bench endpoint cap handle in each task's own table. Both `TABLE_A`
/// (driver, SEND) and `TABLE_B` (partner, RECV) are fresh tables whose first
/// `insert_root` lands at index 0 / generation 0 — asserted in [`run`].
const BENCH_EP_CAP: CapHandle = CapHandle::from_raw(0, 0);

// ── EL0 syscall round-trip bench (Phase 2) ───────────────────────────────────

/// Timed EL0 syscall round-trips; after this many the kernel terminates the EL0
/// bench task (see [`el0_roundtrip_tick`]) and hands off to the ctx/IPC benches.
const N_EL0_ROUNDTRIPS: u64 = 50_000;
/// Untimed EL0 round-trips before the timed window (steady state).
const EL0_WARMUP: u64 = 256;

/// Compile-time guard: each per-op mean divides by one of these iteration
/// counts, so none may be zero — a future edit setting one to 0 would be a
/// division-by-zero panic at runtime. Caught here at build time instead.
const _: () = assert!(
    N_CTX_ROUNDTRIPS > 0 && N_IPC_CYCLES > 0 && N_EL0_ROUNDTRIPS > 0,
    "perf-bench iteration counts must be non-zero (mean = total / N)"
);

/// A minimal raw-flat EL0 program (entry at offset 0, [ADR-0029] format) that
/// loops a **rejected** syscall, so the kernel can time the EL0↔EL1↔EL0
/// round-trip from `syscall_entry` (T-029 Phase 2 / AC#4) **without** exposing
/// `CNTVCT_EL0` to EL0. Hand-assembled aarch64:
///
/// ```text
///   _start: mov x8, #0   ; D2800008 — syscall number 0 = reserved-invalid
///   loop:   svc #0       ; D4000001 — trap to EL1 → BadSyscallNumber → Resume
///           b   loop     ; 17FFFFFF — branch back to the svc (offset −4)
/// ```
///
/// Number 0 decodes to `BadSyscallNumber` **before** any capability is touched
/// (no cap lookup, no yield, no log), so each `svc` is the *pure* fixed
/// round-trip overhead (trap + 272-byte frame save + decode + return) with no
/// side effect — and the task never switches away, so `syscall_entry` sees
/// back-to-back entries until the kernel forces termination after N.
#[rustfmt::skip]
static BENCH_EL0_IMAGE: [u8; 12] = [
    0x08, 0x00, 0x80, 0xd2, // mov x8, #0
    0x01, 0x00, 0x00, 0xd4, // svc #0
    0xff, 0xff, 0xff, 0x17, // b .-4  (back to the svc)
];

/// Timestamp of the previous `syscall_entry` (0 = "no previous yet"). The
/// entry-to-entry delta is one full EL0 round-trip.
static EL0_PREV_NS: AtomicU64 = AtomicU64::new(0);
/// Count of `syscall_entry` entries seen so far (the EL0 bench task is the only
/// `SVC` source, so every entry is one of its round-trips).
static EL0_ENTRY_COUNT: AtomicU64 = AtomicU64::new(0);
/// Accumulated ns across the N timed deltas (mean = this / `N_EL0_ROUNDTRIPS`).
static EL0_ACCUM_NS: AtomicU64 = AtomicU64::new(0);

/// Set up the EL0 bench task + the two kernel bench tasks and start the
/// scheduler. Never returns: after the driver prints its results it parks, so
/// the measurement build halts (the QEMU harness captures the `tyrne: perf …`
/// lines and stops the guest).
#[allow(
    clippy::too_many_lines,
    reason = "linear measurement-build setup top-to-bottom for auditability — mirrors `kernel_main_high`; splitting into helpers would scatter the load→create→publish→schedule order each step depends on"
)]
pub fn run(cpu: &QemuVirtCpu, console: &Pl011Uart) -> ! {
    {
        let mut w = FmtWriter(console);
        let _ = writeln!(
            w,
            "tyrne: perf-bench \u{2014} measurement build (T-029); compiled out of production"
        );
    }

    // Task arena.
    // SAFETY: `.bss`-resident StaticCell; single-core and the scheduler is not
    // started, so this write-once publish is unaliased. Audit: UNSAFE-2026-0001.
    unsafe {
        (*crate::TASK_ARENA.0.get()).write(TaskArena::default());
    }

    // Load the EL0 bench image into a fresh address space, reusing the
    // bootstrap-AS loader path — PMM / MMU / AS arena / the bootstrap AS
    // authority cap are all initialised before `kernel_main_high`'s workload
    // fork. The image just loops a rejected `svc` (see `BENCH_EL0_IMAGE`); the
    // kernel times consecutive `syscall_entry` entries and terminates it.
    // SAFETY: those five statics are written before the fork (single-core, no
    // task running); the momentary `&mut`/`&`s drop at this block's end and
    // never cross a switch ([ADR-0021]). Audit: UNSAFE-2026-0010 +
    // UNSAFE-2026-0014 (+ the loader's own UNSAFE-2026-0025/0026/0027 for the
    // page-table writes / frame zero-fill / image byte-copy).
    let loaded = unsafe {
        let pmm = (*crate::PMM.0.get()).assume_init_mut();
        let mmu = (*crate::MMU.0.get()).assume_init_ref();
        let table = (*crate::BOOTSTRAP_AS_TABLE.0.get()).assume_init_mut();
        let arena = (*crate::AS_ARENA.0.get()).assume_init_mut();
        let parent_cap = *(*crate::BOOTSTRAP_AS_CAP.0.get()).assume_init_ref();
        load_image(
            &BENCH_EL0_IMAGE,
            pmm,
            mmu,
            table,
            arena,
            parent_cap,
            CapRights::empty(),
            VirtAddr(crate::USERSPACE_IMAGE_BASE_VA),
            crate::USERSPACE_STACK_PAGES,
        )
        .expect("perf-bench: load EL0 bench image failed")
    };

    // The three kernel task handles (driver, partner, idle) + the EL0 bench task
    // (turned into a runnable Task via the T-024 bridge, then resolved to a
    // `TaskHandle`).
    // SAFETY: `TASK_ARENA` + `BOOTSTRAP_AS_TABLE` are written above; the momentary
    // `&mut`s are scoped to this block and drop before any task runs (no
    // cross-switch borrow per [ADR-0021]). Audit: UNSAFE-2026-0010 + UNSAFE-2026-0014.
    let (driver_h, partner_h, idle_h, el0_task_h, el0_as_h) = unsafe {
        let arena = &mut *crate::TASK_ARENA.as_mut_ptr();
        let d = create_task(arena, Task::new(0, BOOTSTRAP_ADDRESS_SPACE_HANDLE))
            .expect("perf-bench: create driver task failed");
        let p = create_task(arena, Task::new(1, BOOTSTRAP_ADDRESS_SPACE_HANDLE))
            .expect("perf-bench: create partner task failed");
        let i = create_task(arena, Task::new(2, BOOTSTRAP_ADDRESS_SPACE_HANDLE))
            .expect("perf-bench: create idle task failed");

        let bootstrap_table = (*crate::BOOTSTRAP_AS_TABLE.0.get()).assume_init_mut();
        let el0_as_h = {
            let cap = bootstrap_table
                .lookup(loaded.as_cap)
                .expect("perf-bench: loaded AS cap is stale");
            match cap.object() {
                CapObject::AddressSpace(h) => h,
                _ => panic!("perf-bench: loaded.as_cap is not an AddressSpace cap"),
            }
        };
        let task_cap = task_create_from_image(
            &loaded,
            bootstrap_table,
            arena,
            3,
            CapRights::DUPLICATE | CapRights::DERIVE | CapRights::REVOKE,
        )
        .expect("perf-bench: task_create_from_image failed");
        let el0_task_h = {
            let cap = bootstrap_table
                .lookup(task_cap)
                .expect("perf-bench: minted Task cap is stale");
            match cap.object() {
                CapObject::Task(h) => h,
                _ => panic!("perf-bench: task_create_from_image returned a non-Task cap"),
            }
        };
        (d, p, i, el0_task_h, el0_as_h)
    };

    // One endpoint: the driver holds SEND, the partner holds RECV. Least
    // privilege — neither duplicates nor transfers the cap (every `ipc_*` call
    // passes `None`), so only the one direction each task uses is granted.
    let mut ep_arena = EndpointArena::default();
    let ep = create_endpoint(&mut ep_arena, Endpoint::new(0)).expect("perf-bench: create endpoint");
    let mut table_d = CapabilityTable::new();
    let mut table_p = CapabilityTable::new();
    let send_cap = table_d
        .insert_root(Capability::new(CapRights::SEND, CapObject::Endpoint(ep)))
        .expect("perf-bench: driver SEND cap insert");
    let recv_cap = table_p
        .insert_root(Capability::new(CapRights::RECV, CapObject::Endpoint(ep)))
        .expect("perf-bench: partner RECV cap insert");
    // Fresh tables → first cap at (index 0, generation 0). The bench tasks
    // reconstruct that handle as `BENCH_EP_CAP`; assert the allocator agrees so
    // a future `insert_root` change can't silently drift the contract.
    assert!(
        send_cap == BENCH_EP_CAP && recv_cap == BENCH_EP_CAP,
        "perf-bench: endpoint caps must resolve to (index 0, generation 0)"
    );

    // Publish the IPC state + the two tables + the EL0 task's own (empty) table.
    // SAFETY: single-core; no task is running yet. Audit: UNSAFE-2026-0001.
    unsafe {
        (*crate::EP_ARENA.0.get()).write(ep_arena);
        (*crate::IPC_QUEUES.0.get()).write(IpcQueues::new());
        (*crate::TABLE_A.0.get()).write(table_d);
        (*crate::TABLE_B.0.get()).write(table_p);
        // Gate #3 sources this for the EL0 bench task; left empty — the rejected
        // no-op `svc` (number 0 → BadSyscallNumber) looks up no capability.
        (*crate::USER_TASK_TABLE.0.get()).write(CapabilityTable::new());
    }

    // Scheduler: the EL0 bench task is added FIRST so `start` dispatches it
    // first; it monopolises the CPU (its rejected `svc` is `Resume`, never
    // yields) until the kernel terminates it after N round-trips, which then
    // dispatches the driver — so the ctx/IPC benches run next. Idle sits in the
    // dispatcher fallback slot ([ADR-0026]).
    let mut sched = Scheduler::<QemuVirtCpu>::new();
    // SAFETY: `add_user_task` / `add_task` / `register_idle` call
    // `init_user_context` / `init_context`; each stack top is 16-byte aligned
    // (TaskStack repr) and outlives the run; kernel entries are `fn() -> !`; the
    // EL0 task's `user_sp` (loader page-aligned) + `kernel_stack_top` are
    // 16-byte-aligned + non-null (debug-asserted by `add_user_task`). No `&mut
    // Scheduler` crosses a switch ([ADR-0021]). Audit: UNSAFE-2026-0009 +
    // UNSAFE-2026-0011 (`top()`) + UNSAFE-2026-0014 + UNSAFE-2026-0032 (`enter_el0`).
    unsafe {
        sched
            .add_user_task(
                cpu,
                el0_task_h,
                el0_as_h,
                loaded.entry_va.0,
                loaded.stack_top_va.0,
                crate::USER_TASK_STACK.top(),
                crate::USER_TASK_TABLE.as_mut_ptr(),
            )
            .expect("perf-bench: add EL0 bench task failed");
        sched
            .add_task(
                cpu,
                driver_h,
                BOOTSTRAP_ADDRESS_SPACE_HANDLE,
                bench_driver,
                crate::TASK_A_STACK.top(),
            )
            .expect("perf-bench: add driver failed");
        sched
            .add_task(
                cpu,
                partner_h,
                BOOTSTRAP_ADDRESS_SPACE_HANDLE,
                bench_partner,
                crate::TASK_B_STACK.top(),
            )
            .expect("perf-bench: add partner failed");
        register_idle(
            core::ptr::from_mut(&mut sched),
            cpu,
            idle_h,
            BOOTSTRAP_ADDRESS_SPACE_HANDLE,
            crate::idle_entry,
            crate::TASK_IDLE_STACK.top(),
        );
    }
    // SAFETY: single-core; no task is running yet. Audit: UNSAFE-2026-0001.
    unsafe {
        (*crate::SCHED.0.get()).write(sched);
    }

    {
        let mut w = FmtWriter(console);
        let _ = writeln!(
            w,
            "tyrne: perf-bench starting scheduler (el0-roundtrip + ctx-switch + IPC, N={N_EL0_ROUNDTRIPS}/{N_CTX_ROUNDTRIPS}/{N_IPC_CYCLES}, warmup={EL0_WARMUP}/{WARMUP})"
        );
    }

    // SAFETY: per [ADR-0021] — `SCHED.as_mut_ptr()` is a pure pointer cast
    // (UNSAFE-2026-0013); `SCHED` was just written and no `&mut Scheduler` is
    // live across the initial switch. `start` is `-> !`. Audit: UNSAFE-2026-0014.
    unsafe {
        start(
            crate::SCHED.as_mut_ptr(),
            cpu,
            crate::activate_address_space,
        );
    }
}

/// The driver task: runs the two timed loops, prints the per-op numbers, parks.
fn bench_driver() -> ! {
    // SAFETY: `CPU` / `CONSOLE` are initialised in `kernel_entry` before
    // `start()`; single-core cooperative scheduling prevents concurrent access.
    // Audit: UNSAFE-2026-0010.
    let cpu = unsafe { (*crate::CPU.0.get()).assume_init_ref() };
    // SAFETY: as above. Audit: UNSAFE-2026-0010.
    let console = unsafe { (*crate::CONSOLE.0.get()).assume_init_ref() };

    // ── Context-switch micro-bench ────────────────────────────────────────────
    for _ in 0..WARMUP {
        driver_yield(cpu);
    }
    let t0 = cpu.now_ns();
    for _ in 0..N_CTX_ROUNDTRIPS {
        driver_yield(cpu);
    }
    let elapsed = cpu.now_ns().saturating_sub(t0);
    let switches = 2 * N_CTX_ROUNDTRIPS;
    {
        let mut w = FmtWriter(console);
        let _ = writeln!(
            w,
            "tyrne: perf ctx-switch = {} ns/switch ({} ns/round-trip; N={N_CTX_ROUNDTRIPS} round-trips = {switches} switches, {elapsed} ns total)",
            elapsed / switches,
            elapsed / N_CTX_ROUNDTRIPS
        );
    }

    // ── IPC send→recv cycle micro-bench ───────────────────────────────────────
    PHASE.store(PHASE_IPC, Ordering::Relaxed);
    // Prime: yield once so the partner observes PHASE_IPC, enters its receive
    // loop, and blocks (RecvWaiting) — so the first timed send is Delivered.
    driver_yield(cpu);
    for _ in 0..WARMUP {
        driver_send(cpu);
    }
    let t0 = cpu.now_ns();
    for _ in 0..N_IPC_CYCLES {
        driver_send(cpu);
    }
    let elapsed = cpu.now_ns().saturating_sub(t0);
    {
        let mut w = FmtWriter(console);
        let _ = writeln!(
            w,
            "tyrne: perf ipc send-recv cycle = {} ns/cycle (1 send + 1 recv + 2 ctx-switch; N={N_IPC_CYCLES}, {elapsed} ns total)",
            elapsed / N_IPC_CYCLES
        );
    }

    // ── Done — park ───────────────────────────────────────────────────────────
    PHASE.store(PHASE_DONE, Ordering::Relaxed);
    {
        let mut w = FmtWriter(console);
        let _ = writeln!(w, "tyrne: perf-bench complete");
    }
    // Park in low-power WFI rather than a busy-spin: the measurement is done and
    // the kernel never exits on its own (the harness stops the guest). IRQs are
    // masked and no IRQ source is enabled in this build, so WFI sleeps until
    // QEMU is killed — no host-CPU spin. Mirrors `idle_entry`'s park.
    loop {
        cpu.wait_for_interrupt();
    }
}

/// The partner task: bounces `yield_now` during the ctx phase, receives during
/// the IPC phase, parks when done.
fn bench_partner() -> ! {
    // SAFETY: `CPU` is initialised before `start()`; single-core cooperative.
    // Audit: UNSAFE-2026-0010.
    let cpu = unsafe { (*crate::CPU.0.get()).assume_init_ref() };
    loop {
        match PHASE.load(Ordering::Relaxed) {
            PHASE_CTX => driver_yield(cpu),
            PHASE_IPC => partner_recv(cpu),
            // Done — low-power WFI park (see `bench_driver`). In practice the
            // partner is blocked in its last `ipc_recv_and_yield` when the
            // driver finishes, so this arm is a defensive park, not the hot path.
            _ => cpu.wait_for_interrupt(),
        }
    }
}

/// One cooperative `yield_now` (used by both tasks for the ctx-switch bench).
#[inline]
fn driver_yield(cpu: &QemuVirtCpu) {
    // SAFETY: per [ADR-0021] — `SCHED.as_mut_ptr()` is a pure pointer cast
    // (UNSAFE-2026-0013); no `&mut` to shared kernel state is live across the
    // cooperative switch. `yield_now` can only error with `NoCurrentTask`,
    // impossible once the scheduler has started. Audit: UNSAFE-2026-0014.
    unsafe {
        yield_now(
            crate::SCHED.as_mut_ptr(),
            cpu,
            crate::activate_address_space,
        )
        .expect("perf-bench: yield_now failed");
    }
}

/// One driver send (Delivered to the waiting partner, then yields to it).
#[inline]
fn driver_send(cpu: &QemuVirtCpu) {
    let msg = Message {
        label: 0xBE0C,
        params: [0; 3],
    };
    // SAFETY: per [ADR-0021] — every `*mut` is a `StaticCell::as_mut_ptr` pure
    // cast (UNSAFE-2026-0013); `ipc_send_and_yield` materialises momentary
    // `&mut`s strictly outside its switch window per the scheduler module's
    // shared contract; `SCHED` / `EP_ARENA` / `IPC_QUEUES` / `TABLE_A` are
    // distinct, initialised referents and `CPU` is borrowed `&`. No `&mut`
    // crosses the switch. Audit: UNSAFE-2026-0014.
    unsafe {
        ipc_send_and_yield(
            crate::SCHED.as_mut_ptr(),
            cpu,
            crate::EP_ARENA.as_mut_ptr(),
            crate::IPC_QUEUES.as_mut_ptr(),
            crate::TABLE_A.as_mut_ptr(),
            BENCH_EP_CAP,
            msg,
            None,
            crate::activate_address_space,
        )
        .expect("perf-bench: ipc_send_and_yield failed");
    }
}

/// One partner receive (blocks → yields to driver when no message is pending).
#[inline]
fn partner_recv(cpu: &QemuVirtCpu) {
    // SAFETY: per [ADR-0021] — same raw-pointer discipline as `driver_send`;
    // `TABLE_B` is the partner's own table. Audit: UNSAFE-2026-0014.
    unsafe {
        ipc_recv_and_yield(
            crate::SCHED.as_mut_ptr(),
            cpu,
            crate::EP_ARENA.as_mut_ptr(),
            crate::IPC_QUEUES.as_mut_ptr(),
            crate::TABLE_B.as_mut_ptr(),
            BENCH_EP_CAP,
            crate::activate_address_space,
        )
        .expect("perf-bench: ipc_recv_and_yield failed");
    }
}

/// Per-entry hook called by `syscall_entry` (feature-gated) for the EL0 bench
/// task — the only `SVC` source in this build, so every entry is one of its
/// round-trips. Times the entry-to-entry delta (one full EL0↔EL1↔EL0 round-trip,
/// hook-to-hook), skips the first delta + `EL0_WARMUP`, accumulates the next
/// `N_EL0_ROUNDTRIPS`, then prints the mean and returns
/// [`SyscallEffect::Terminate`] — which ends the EL0 bench (`task_exit_current`)
/// and hands off to the driver/partner ctx+IPC benches. Otherwise returns
/// `effect` unchanged (the rejected `svc`'s `Resume`), so the EL0 task loops.
///
/// `Relaxed` atomics: single-core and `syscall_entry` runs with IRQs masked, so
/// entries are strictly serial — there is no concurrent access to order.
pub fn el0_roundtrip_tick(effect: SyscallEffect) -> SyscallEffect {
    // SAFETY: `CPU` / `CONSOLE` are initialised before `start()`; single-core
    // cooperative, IRQs masked in the SVC handler. Audit: UNSAFE-2026-0010.
    let cpu = unsafe { (*crate::CPU.0.get()).assume_init_ref() };
    let now = cpu.now_ns();
    let prev = EL0_PREV_NS.swap(now, Ordering::Relaxed);
    let n = EL0_ENTRY_COUNT.fetch_add(1, Ordering::Relaxed);

    // n == 0: first entry — no previous timestamp, so no delta yet.
    // 1..=EL0_WARMUP: warm-up deltas (skipped).
    // EL0_WARMUP+1 ..= EL0_WARMUP+N: the N timed deltas.
    if n == 0 || n <= EL0_WARMUP {
        return effect;
    }
    EL0_ACCUM_NS.fetch_add(now.saturating_sub(prev), Ordering::Relaxed);
    // `>=` (not `==`) so the bench still terminates if `n` ever overshoots the
    // target — defensive against a future preemptive/SMP `syscall_entry` where
    // entries might not increment strictly by one. Serial today, so it fires at
    // exactly `EL0_WARMUP + N_EL0_ROUNDTRIPS` (N timed deltas accumulated).
    if n >= EL0_WARMUP + N_EL0_ROUNDTRIPS {
        let total = EL0_ACCUM_NS.load(Ordering::Relaxed);
        // SAFETY: as above — `CONSOLE` initialised before `start()`. UNSAFE-2026-0010.
        let console = unsafe { (*crate::CONSOLE.0.get()).assume_init_ref() };
        let mut w = FmtWriter(console);
        let _ = writeln!(
            w,
            "tyrne: perf el0 syscall round-trip = {} ns/syscall (kernel-side, hook-to-hook; rejected no-op svc; N={N_EL0_ROUNDTRIPS}, {total} ns total)",
            total / N_EL0_ROUNDTRIPS
        );
        // End the EL0 bench task; `syscall_entry`'s Terminate arm switches to the
        // next ready task (the driver) → the ctx/IPC benches run next.
        return SyscallEffect::Terminate(0);
    }
    effect
}
