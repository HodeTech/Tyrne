//! # tyrne-bsp-qemu-virt
//!
//! Board Support Package for QEMU's aarch64 `virt` machine — the primary
//! development target per [ADR-0004][adr-0004] and the BSP that every
//! Tyrne feature is first exercised against.
//!
//! This crate is the bootable binary: it provides the reset vector
//! (`_start`, assembled from `boot.s` via [`core::arch::global_asm!`]),
//! the Rust entry `kernel_entry`, a panic handler, and the hardware
//! implementations of the HAL traits. The A6 milestone demonstrates an
//! end-to-end IPC round trip: Task B registers as receiver on a capability-
//! gated endpoint, Task A sends a message, B replies, and A receives the
//! reply — proving the Phase A exit bar.
//!
//! The boot flow is documented in [`docs/architecture/boot.md`][boot-doc]
//! and the memory-layout decisions in [ADR-0012][adr-0012].
//!
//! [adr-0004]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0004-target-platforms.md
//! [adr-0012]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0012-boot-flow-qemu-virt.md
//! [boot-doc]: https://github.com/HodeTech/Tyrne/blob/main/docs/architecture/boot.md

#![no_std]
#![no_main]
// Binary crate: `pub` items serve the linker (`#[no_mangle]`) rather than
// external consumers; `unreachable_pub` is therefore expected throughout.
#![allow(unreachable_pub, reason = "binary crate; pub items are for the linker")]

use core::arch::global_asm;
use core::cell::UnsafeCell;
use core::fmt::Write;
use core::mem::MaybeUninit;
use core::panic::PanicInfo;

use tyrne_hal::mmu::vmsav8::TCR_EL1_EPD0_BIT;
use tyrne_hal::{Console, Cpu, FmtWriter, Timer};
use tyrne_hal::{PhysAddr, VirtAddr, KERNEL_HIGH_HALF_OFFSET, PAGE_SIZE};
use tyrne_kernel::cap::{CapHandle, CapObject, CapRights, Capability, CapabilityTable};
use tyrne_kernel::ipc::{IpcQueues, Message, RecvOutcome};
use tyrne_kernel::mm::{PhysFrameRange, Pmm};
use tyrne_kernel::obj::endpoint::{create_endpoint, Endpoint, EndpointArena};
use tyrne_kernel::obj::task::{create_task, Task, TaskArena};
use tyrne_kernel::obj::task_loader::load_image;
use tyrne_kernel::sched::{
    ipc_recv_and_yield, ipc_send_and_yield, register_idle, start, yield_now, Scheduler,
};

mod console;
mod cpu;
mod exceptions;
mod gic;
mod mmu;
mod mmu_bootstrap;
mod syscall;

use console::Pl011Uart;
use cpu::QemuVirtCpu;
use gic::{QemuVirtGic, QEMU_VIRT_GIC_CPU_INTERFACE_BASE, QEMU_VIRT_GIC_DISTRIBUTOR_BASE};

// ─── Physical memory layout (T-017 / ADR-0035) ────────────────────────────────
//
// Per [ADR-0012] the QEMU virt machine ships 128 MiB of RAM at PA
// `0x4000_0000..0x4800_0000`; the kernel image is loaded by `-kernel` at
// `0x4008_0000` (i.e. the first 512 KiB of RAM is QEMU-firmware-reserved).
// The PMM manages this entire 128 MiB extent via a bitmap of one bit per
// `PAGE_SIZE` (4 KiB) frame: 32 768 frames → 4 096 bitmap bytes.
//
// At init time the BSP reserves: (1) the QEMU firmware region
// `[0x4000_0000, 0x4008_0000)`; (2) the kernel-image + `.bss` (which
// contains `.boot_pt` per T-016 / ADR-0027 §Decision outcome (a)) +
// boot-stack region `[0x4008_0000, __stack_top_aligned)`. Two
// reservations cover everything that must never be handed to a
// runtime caller.
//
// [ADR-0012]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0012-boot-flow-qemu-virt.md

/// PMM-managed extent base PA. Matches `linker.ld` `MEMORY` `RAM`
/// `ORIGIN` for QEMU virt.
const PMM_EXTENT_START: usize = 0x4000_0000;
/// PMM-managed extent end PA (exclusive). 128 MiB above the start.
const PMM_EXTENT_END: usize = 0x4800_0000;
/// Kernel image load address (per linker.ld `.text.boot` placement and
/// QEMU virt's `-kernel` discipline).
const KERNEL_IMAGE_START: usize = 0x4008_0000;

/// PMM bitmap byte count: 32 768 frames / 8 bits = 4 096 bytes.
/// Sized at compile time per the BSP's static RAM extent; if the
/// extent changes (future Pi 4 BSP), this const grows accordingly
/// per the per-BSP-const-generic discipline of ADR-0035.
///
/// **Ceiling division** ensures the last byte is allocated even
/// when the managed frame count is not a multiple of 8 (per PR #26
/// round-1 review). For QEMU virt's 32 768 frames the result is
/// 4 096 bytes either way (32 768 is a multiple of 8); the ceiling
/// form is forward-defensive for future BSPs with non-multiple-of-8
/// frame counts.
const PMM_BITMAP_BYTES: usize = ((PMM_EXTENT_END - PMM_EXTENT_START) / PAGE_SIZE).div_ceil(8);
/// Reserved-range cache capacity. v1 has 2 ranges (firmware + kernel
/// image+bss+stack); 8 provides headroom for future BSP layouts
/// (DTB / ATF / ACPI / initrd / framebuffer reservations) without
/// forcing a recompile when more arrive.
const PMM_RESERVED_RANGES: usize = 8;

/// Concrete BSP-side PMM type alias.
type BspPmm = Pmm<PMM_BITMAP_BYTES, PMM_RESERVED_RANGES>;

/// MMIO base of the QEMU `virt` machine's PL011 UART.
///
/// Hardcoded per [ADR-0012][adr-0012]; each BSP carries its own
/// peripheral addresses. QEMU `virt` has exposed this address across
/// all versions the project targets.
///
/// [adr-0012]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0012-boot-flow-qemu-virt.md
const PL011_UART_BASE: usize = 0x0900_0000;

// Pin the HAL high-half offset to the literal the linker script (`KBASE =
// KERNEL_HH_OFFSET + KERNEL_IMAGE_PHYS_BASE`) and the migration path assume.
// A drift between the linker's hardcoded value and `tyrne_hal` would silently
// corrupt every high-half VA↔PA computation (ADR-0033 / T-022); fail the build
// instead.
//
// Gated on the kernel build: `KERNEL_HIGH_HALF_OFFSET` is `0` on any non
// `target_os = "none"` build (host/IDE analysis, incl. an aarch64 host), where
// this assert is irrelevant — without the guard it would fire a spurious
// failure under rust-analyzer / a hosted `cargo check` on Apple Silicon.
#[cfg(all(target_arch = "aarch64", target_os = "none"))]
const _: () = assert!(KERNEL_HIGH_HALF_OFFSET == 0xFFFF_FFFF_0000_0000);

// ─── StaticCell ───────────────────────────────────────────────────────────────
//
// Task entry functions are `fn() -> !` — they cannot capture environment.
// The scheduler, CPU, console, and IPC infrastructure are stored as immutable
// statics wrapping `UnsafeCell<MaybeUninit<T>>` so all tasks can reach them
// without `static mut`. All accesses remain `unsafe`; safety is ensured by the
// single-core, cooperative execution model (no two tasks run simultaneously).

/// `Sync` wrapper around `UnsafeCell<MaybeUninit<T>>` for write-once globals.
///
/// Written exactly once from `kernel_entry` (before `start()` is called).
/// Tasks then access the value through `assume_init_ref` / `assume_init_mut`.
/// All accesses are `unsafe`; this type only satisfies the `Sync` bound that
/// `static` requires.
struct StaticCell<T>(UnsafeCell<MaybeUninit<T>>);

// SAFETY: Tyrne v1 is single-core and cooperative; no two tasks ever run
// simultaneously, so there are no data races on `StaticCell` contents.
// Rejected alternatives: `Mutex` / `RwLock` require a runtime (heap, OS) or
// a spin implementation that itself relies on `unsafe` and adds overhead
// inappropriate for a bare-metal `static`. `OnceCell` / `LazyCell` from
// `core` are not available in `no_std` without an allocator in A5/A6.
// Audit: UNSAFE-2026-0010.
unsafe impl<T> Sync for StaticCell<T> {}

impl<T> StaticCell<T> {
    const fn new() -> Self {
        Self(UnsafeCell::new(MaybeUninit::uninit()))
    }

    /// Return a raw `*mut T` pointer to the cell's storage without
    /// materialising a `&mut` to the underlying `MaybeUninit<T>`.
    ///
    /// Used by the raw-pointer scheduler bridge per [ADR-0021]: the BSP
    /// hands `*mut T` to the kernel's `ipc_send_and_yield` /
    /// `ipc_recv_and_yield` / `yield_now` entry points so that no `&mut`
    /// reference to any shared kernel state is alive across
    /// `cpu.context_switch`.
    ///
    /// The implementation is a plain pointer cast (`UnsafeCell::get()`
    /// returns `*mut MaybeUninit<T>`, then `cast::<T>` is a zero-cost
    /// reinterpretation permitted because `MaybeUninit<T>` shares `T`'s
    /// layout), so no borrow of any kind is produced here.
    ///
    /// # Safety
    ///
    /// The caller must ensure the cell has been initialised via a prior
    /// `(*cell.0.get()).write(...)` before dereferencing the returned pointer,
    /// and must not use the pointer to create a `&mut T` that outlives a
    /// cooperative context switch (ADR-0021). Audit: UNSAFE-2026-0013.
    ///
    /// [ADR-0021]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0021-raw-pointer-scheduler-ipc-bridge.md
    #[inline]
    #[allow(
        clippy::mut_from_ref,
        reason = "returns a raw pointer, not a reference; aliasing discipline documented in ADR-0021"
    )]
    const fn as_mut_ptr(&self) -> *mut T {
        self.0.get().cast::<T>()
    }
}

// ─── Task-stack storage ───────────────────────────────────────────────────────

/// Aligned storage for one task's call stack.
///
/// `#[repr(C, align(16))]` guarantees the 16-byte sp alignment required by
/// AAPCS64 at every function-call boundary. The inner array is wrapped in
/// `UnsafeCell` so the static need not be `mut`; all access is still `unsafe`.
#[repr(C, align(16))]
struct TaskStack(UnsafeCell<[u8; 4096]>);

// SAFETY: single-core cooperative kernel; only one task touches each stack at
// a time, and no task can interrupt another (cooperative scheduling).
// Rejected alternatives: wrapping in `Mutex` would add lock overhead and
// require a runtime or spin implementation. Making the static `mut` would
// expose the interior to safe code via `static mut` aliasing, which is
// worse. `UnsafeCell` with manual discipline is the standard bare-metal
// pattern and is the minimal wrapper that satisfies the `Sync` bound.
// Audit: UNSAFE-2026-0011.
unsafe impl Sync for TaskStack {}

impl TaskStack {
    const fn new() -> Self {
        Self(UnsafeCell::new([0u8; 4096]))
    }

    /// Return a pointer one past the end of the stack (the initial sp value).
    ///
    /// # Safety
    ///
    /// The caller must ensure this `TaskStack` outlives every task that uses it.
    unsafe fn top(&self) -> *mut u8 {
        // SAFETY: UnsafeCell deref is sound under the caller's
        // outlives-task contract (see `# Safety`) and single-core
        // cooperative scheduling; `add(4096)` is a one-past-end
        // sentinel, not an out-of-bounds dereference. Rejected
        // alternatives + full rationale live in UNSAFE-2026-0011's
        // 2026-04-23 Amendment (covers both the Sync marker and
        // `top()`'s pointer arithmetic under one audit entry).
        // Audit: UNSAFE-2026-0011.
        unsafe { (*self.0.get()).as_mut_ptr().add(4096) }
    }
}

/// Stack for task A.
static TASK_A_STACK: TaskStack = TaskStack::new();
/// Stack for task B.
static TASK_B_STACK: TaskStack = TaskStack::new();
/// Stack for the kernel idle task (ADR-0022). Sized the same as application
/// task stacks — the idle loop's `wfi` + `yield_now` path uses far less than
/// 4 KiB, but keeping a uniform `TaskStack` avoids a second static type just
/// for the idle path.
static TASK_IDLE_STACK: TaskStack = TaskStack::new();

// ─── Global kernel state ──────────────────────────────────────────────────────

/// The cooperative scheduler, concrete over the QEMU BSP CPU type.
static SCHED: StaticCell<Scheduler<QemuVirtCpu>> = StaticCell::new();

/// The CPU handle — needed by `yield_now` and IPC bridge to mask IRQs.
static CPU: StaticCell<QemuVirtCpu> = StaticCell::new();

/// The GIC v2 controller handle. Constructed once in `kernel_entry`
/// and accessed via `&` from `irq_entry` (the asm-trampoline-side
/// dispatcher in `src/exceptions.rs`). Pre-T-012 v1 had no IRQ source;
/// T-012 lights this up alongside the vector-table install.
static GIC: StaticCell<QemuVirtGic> = StaticCell::new();

/// The PL011 console — used by task functions for diagnostic output.
static CONSOLE: StaticCell<Pl011Uart> = StaticCell::new();

/// Boot-time `now_ns()` snapshot, written once by `kernel_main_high` after the
/// CPU is constructed and read by `task_a` to compute the boot-to-end
/// elapsed time. T-009 measurement scaffold; replaced by a richer
/// instrumentation surface when the first hypothesis-driven performance
/// review is conducted.
static BOOT_NS: StaticCell<u64> = StaticCell::new();

/// Physical Memory Manager (T-017 / ADR-0035). Constructed once in
/// `kernel_entry` immediately after `mmu_bootstrap()` returns, before
/// GIC init, so any post-bootstrap `Mmu::map` caller can pull frames
/// for intermediate page tables. v1's cooperative IPC demo never
/// calls `alloc_frame`, but the PMM is published so future B3+ work
/// (`AddressSpace` bring-up — ADR-0028 placeholder + T-018) can layer
/// on top without further BSP-side change. The static is sized
/// 4 KiB bitmap + 8 reserved-range slots + cached counters ≈ 4.1 KiB
/// of `.bss` per ADR-0035 §Consequences §Bounded metadata.
static PMM: StaticCell<BspPmm> = StaticCell::new();

// ─── AddressSpace infrastructure (T-018 / ADR-0028) ──────────────────────────

/// The `QemuVirtMmu` instance the activation hook + future cap-gated
/// `Mmu::map`/`unmap` paths invoke. `QemuVirtMmu` is zero-sized today
/// (`QemuVirtMmu::new()` is `const`); storing it in a `StaticCell`
/// here gives the activation closure a stable address it can reach
/// from inside the scheduler's `IrqGuard` scope.
static MMU: StaticCell<mmu::QemuVirtMmu> = StaticCell::new();

/// The address-space arena. v1 capacity `ADDRESS_SPACE_ARENA_CAPACITY`
/// (= 8) — bootstrap AS + headroom for future B5+ userspace ASes.
static AS_ARENA: StaticCell<tyrne_kernel::mm::AddressSpaceArena<mmu::QemuVirtMmu>> =
    StaticCell::new();

/// A BSP-local copy of the bootstrap [`QemuVirtAddressSpace`][mmu::QemuVirtAddressSpace]
/// for [`syscall_entry`][crate::syscall::syscall_entry] to pass as the
/// `SyscallContext`'s `task_as` (the translation regime gate #1's per-page
/// `Mmu::translate` resolves user pointers through, [ADR-0038]). `QemuVirtAddressSpace`
/// is `Copy` (it carries only the root `PhysFrame`), so this is a copy of the
/// same root the kernel arena's bootstrap AS wraps — the kernel's
/// `AddressSpace<M>::inner` is `pub(crate)`, so the BSP keeps its own handle
/// rather than reach through the wrapper. **B5/dormant only:** the EL1 stub
/// runs in this bootstrap AS, whose low-identity table maps no `USER` page —
/// so a stub `console_write` of a kernel VA is correctly rejected by gate #1
/// (the demonstration in [`syscall_boundary_smoke`]). B6 (gate #3 / T-026)
/// sources the *running EL0 task's* AS from the scheduler instead.
///
/// [ADR-0038]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0038-mmu-translate-and-user-access.md
static BOOTSTRAP_AS: StaticCell<mmu::QemuVirtAddressSpace> = StaticCell::new();

/// The bootstrap "AS authority" cap. Kernel-init's parent cap for any
/// `cap_create_address_space` invocation that wants to mint a new AS.
/// Stored as a `CapHandle` into [`BOOTSTRAP_AS_TABLE`] (the kernel-
/// init's cap table; distinct from `TABLE_A`/`TABLE_B` which are the
/// per-task tables for the IPC demo).
///
/// **Live as of T-019.** The task loader smoke at the end of
/// `kernel_main` reads this cap and passes it as `parent_as_cap` to
/// `task_loader::load_image`, which derives the loaded image's AS cap
/// from it (DERIVE rights granted at mint time below). The previous
/// `#[allow(dead_code)]` covering the "v1 demo creates no second AS"
/// state was removed when T-019 turned the cap into the live parent
/// authority for the loader's mint.
static BOOTSTRAP_AS_CAP: StaticCell<CapHandle> = StaticCell::new();

/// Kernel-init's capability table. Mirrors `TABLE_A`/`TABLE_B`'s
/// pattern but for the kernel-init context — holds the bootstrap AS
/// authority cap and (post-T-019) the loaded-image AS cap minted by
/// `task_loader::load_image`. B5+ will grow this with the kernel-init's
/// untyped / memory-region authority caps.
static BOOTSTRAP_AS_TABLE: StaticCell<CapabilityTable> = StaticCell::new();

// ─── T-019 task loader placeholder image (ADR-0029) ───────────────────────────

/// Placeholder userspace image: 8 bytes of aarch64 `mov w0, #42; ret`
/// per [ADR-0029 §Decision outcome (Build pipeline — B4 / T-019)][adr-0029].
/// The real B6 "hello" userspace binary lands with `userland/hello/`
/// per [ADR-0029 §Decision outcome (Build pipeline — B6)][adr-0029];
/// T-019 ships with this hand-coded blob as the loader's smoke fixture.
///
/// **Not executed.** T-019 produces a `LoadedImage` describing a
/// populated AS; running gates on B5 (syscall ABI per ADR-0030) + B6
/// (first userspace "hello") which together provide the prerequisites
/// (kernel mappings in userspace AS, EL0-ready context, syscall
/// entry).
///
/// [adr-0029]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0029-initial-userspace-image-format.md
static USERSPACE_IMAGE: &[u8] = &[0x40, 0x05, 0x80, 0x52, 0xc0, 0x03, 0x5f, 0xd6];

/// Base VA the loader places the image at — userspace VA range per
/// [ADR-0027 §Decision outcome (a)][adr-0027]'s `TTBR0_EL1` range.
/// `0x0080_0000` (8 MiB) is a pragmatic, page-aligned userspace VA:
/// well clear of the null-page guard region used to trap dereferences,
/// far below `USERSPACE_VA_LIMIT` (= `1 << 48`) so no overflow concern
/// arises for placeholder-sized image+stack spans, and structurally
/// aligned at the 8 MiB boundary which simplifies any mental arithmetic
/// reading the smoke trace. Hard-coded for the placeholder blob; B6's
/// `userland` linker script picks the real VA.
///
/// [adr-0027]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0027-kernel-virtual-memory-layout.md
const USERSPACE_IMAGE_BASE_VA: usize = 0x0080_0000;

/// Stack region size in `PAGE_SIZE`-multiples. Minimum 1; v1's
/// placeholder never pushes to its stack but the loader requires a
/// non-zero stack region (and the future `task_create_from_image`
/// wrapper needs a defined `sp`).
const USERSPACE_STACK_PAGES: usize = 1;

/// Scheduler activation-hook callback for address-space changes.
///
/// Passed to [`yield_now`] / [`ipc_send_and_yield`] /
/// [`ipc_recv_and_yield`] / [`start`] as the `activate_address_space`
/// closure parameter (per T-018 commit 4's scheduler-side hook).
/// Looks up `handle` in [`AS_ARENA`] and invokes [`tyrne_hal::Mmu::activate`]
/// via [`tyrne_kernel::mm::activate_address_space_handle`]. Stale
/// handles are silently ignored — the scheduler's
/// `task_address_space_handles` array stores only handles minted
/// through the AS arena, so a stale hit indicates a use-after-free
/// in scheduler state that no recovery here can fix; logging /
/// panic would compound the failure inside an `IrqGuard` scope.
///
/// In v1 every task runs on the bootstrap AS, so the scheduler's
/// `address_space_activation_target` helper short-circuits before
/// ever invoking this function. The wiring is in place so future
/// B5+ multi-AS userspace tasks slot in additively.
fn activate_address_space(handle: tyrne_kernel::mm::AddressSpaceHandle) {
    // SAFETY: `AS_ARENA` and `MMU` are written exactly once in
    // `kernel_entry` before `start()` is called; the activation hook
    // runs inside the scheduler's `IrqGuard` scope (after the
    // `&mut Scheduler<C>` borrow drops) so no peer can race. The
    // shared `&` reborrows below do not alias any live `&mut`. Audit:
    // UNSAFE-2026-0010 (StaticCell pattern) + UNSAFE-2026-0014
    // (momentary `&` across cooperative switches).
    unsafe {
        let arena = (*AS_ARENA.0.get()).assume_init_ref();
        let mmu = (*MMU.0.get()).assume_init_ref();
        tyrne_kernel::mm::activate_address_space_handle(arena, handle, mmu);
    }
}

// ─── IPC infrastructure ───────────────────────────────────────────────────────

/// Endpoint arena — the kernel-object pool backing the IPC demo endpoint.
static EP_ARENA: StaticCell<EndpointArena> = StaticCell::new();

/// IPC queue state for all endpoint slots.
static IPC_QUEUES: StaticCell<IpcQueues> = StaticCell::new();

/// Task A's capability table — contains Task A's cap on the demo endpoint.
static TABLE_A: StaticCell<CapabilityTable> = StaticCell::new();

/// Task B's capability table — contains Task B's cap on the demo endpoint.
static TABLE_B: StaticCell<CapabilityTable> = StaticCell::new();

/// Task A's endpoint capability handle (index into `TABLE_A`).
static EP_CAP_A: StaticCell<CapHandle> = StaticCell::new();

/// Task B's endpoint capability handle (index into `TABLE_B`).
static EP_CAP_B: StaticCell<CapHandle> = StaticCell::new();

// ─── Syscall-boundary fail-closed fallback table (T-026 / gate #3) ────────────

/// The **empty** capability table the syscall dispatcher resolves against when
/// [`syscall::syscall_entry`] cannot resolve a running EL0 task from the
/// scheduler (its `current_user_table()` returns `None`) — the **fail-closed**
/// default for gate #3 (T-026). Every cap lookup against it returns
/// `CapError::InvalidHandle`, so a syscall issued with no running task names no
/// capability — never an ambient table (the [ADR-0014] per-subject
/// unforgeability holds). It is **never minted into**: a real EL0 task brings
/// its own table, recorded in the scheduler by `add_user_task` and dereferenced
/// by `syscall_entry`. Distinct from `TABLE_A` / `TABLE_B` (the IPC-demo tables).
///
/// [ADR-0014]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0014-capability-representation.md
static FAILCLOSED_TABLE: StaticCell<CapabilityTable> = StaticCell::new();

/// Task kernel-object arena — global per [ADR-0016]. Although the v1 demo
/// never reads this arena after `create_task` has returned the two
/// `TaskHandle`s, global storage is the uniform pattern established by
/// ADR-0016 for every kernel-object kind. Keeping `TaskArena` here (and
/// not on `kernel_entry`'s stack) avoids a second BSP static-cell churn
/// when task destruction / status-query APIs arrive in later Phase B work.
///
/// [ADR-0016]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0016-kernel-object-storage.md
static TASK_ARENA: StaticCell<TaskArena> = StaticCell::new();

// ─── Idle task ────────────────────────────────────────────────────────────────

/// Kernel idle task — runs when no application task is ready.
///
/// Per [ADR-0022] (idle-task ownership) + [ADR-0026] (idle dispatch via
/// fallback slot, supersedes ADR-0022's *idle-task-location* axis), the
/// BSP owns the idle entry function and registers it via [`register_idle`]
/// rather than [`Scheduler::add_task`]. The loop body is
/// `cpu.wait_for_interrupt()` + `yield_now`: `WFI` suspends the core
/// until any unmasked IRQ raises a wake, then the cooperative `yield_now`
/// returns control to the dispatcher. The dispatcher consults the idle
/// fallback slot only when [`Scheduler::ready`] is empty, so idle never
/// displaces a real Ready task — the structural fix for the 2026-05-06
/// QEMU smoke regression where round-robin FIFO had selected idle ahead
/// of a just-unblocked receiver.
///
/// In v1's cooperative IPC demo, idle's loop body executes only when both
/// application tasks are simultaneously blocked on IPC. The demo's flow
/// keeps at least one of `task_a` / `task_b` Ready at every step, so idle
/// is structurally unreachable in the demo path — but if a future caller
/// arms a deadline via `arm_deadline` and both application tasks happen
/// to block at the same moment, idle's `WFI` becomes observable.
///
/// Full IPC-graph deadlock (every task blocked + no wake source ever
/// fires) is visible today as "idle waiting forever", not a panic — the
/// kernel stays live; typed `SchedError::Deadlock` is reachable only if
/// the BSP did not register idle at all (i.e. `register_idle` was not
/// called before `start`).
///
/// [ADR-0022]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0022-idle-task-and-typed-scheduler-deadlock.md
/// [ADR-0026]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0026-idle-dispatch-fallback.md
fn idle_entry() -> ! {
    // SAFETY: CPU is fully initialised in `kernel_entry` before `start()`;
    // single-core cooperative scheduling prevents concurrent access.
    // Audit: UNSAFE-2026-0010.
    let cpu = unsafe { (*CPU.0.get()).assume_init_ref() };
    loop {
        // T-012 step 5: idle waits for an interrupt instead of busy-
        // spinning. `wait_for_interrupt` issues a `WFI` instruction
        // which suspends the core until any unmasked IRQ raises a
        // wake. Closes ADR-0022 first rider's *Sub-rider* gate ("WFI
        // activation requires *two* tasks, not one") — the time-source
        // half landed with T-009; the IRQ-delivery half landed with
        // T-012's GIC + vector-table install (commit `a043079`).
        //
        // T-014: idle is now in the dispatcher's fallback slot per
        // ADR-0026, not the FIFO. The dispatcher routes here only when
        // both `task_a` and `task_b` are Blocked simultaneously and no
        // other task is Ready; the v1 cooperative IPC demo's flow
        // keeps at least one of them Ready at every step, so this
        // `WFI` remains structurally unreachable in the demo path.
        cpu.wait_for_interrupt();
        // SAFETY: per ADR-0021 — `SCHED.as_mut_ptr()` is a pure pointer
        // cast (UNSAFE-2026-0013); idle's stack frame holds no `&mut` to
        // any shared state across the cooperative switch. `yield_now`
        // can only return `Err(NoCurrentTask)`, which is impossible once
        // the scheduler has started. Audit: UNSAFE-2026-0014.
        unsafe {
            yield_now(SCHED.as_mut_ptr(), cpu, activate_address_space)
                .expect("idle: yield_now failed");
        }
    }
}

// ─── Task B ───────────────────────────────────────────────────────────────────

/// IPC demo — receiver side. Registers as receiver on the endpoint, waits for
/// Task A's message, then sends a reply and yields to Task A. Control does not
/// return from that final yield in the v1 single-round demo: Task A's
/// `ipc_recv_and_yield` picks up the reply without blocking and runs to its
/// own spin loop. The tail-end `loop { spin_loop() }` therefore satisfies the
/// `fn() -> !` return type but is structurally unreachable.
fn task_b() -> ! {
    // SAFETY: CONSOLE is fully initialised in `kernel_entry` before `start()`;
    // single-core cooperative scheduling prevents concurrent access.
    // Audit: UNSAFE-2026-0010.
    let console = unsafe { (*CONSOLE.0.get()).assume_init_ref() };
    let mut w = FmtWriter(console);
    let _ = writeln!(w, "tyrne: task B \u{2014} waiting for IPC");

    // Register as receiver on the endpoint. If no sender is ready, blocks and
    // yields to Task A. Resumes when Task A delivers a message.
    //
    // SAFETY: per ADR-0021 — every `*mut` here is produced by
    // `StaticCell::as_mut_ptr()`, which is a pure pointer cast and never
    // materialises a `&mut`. `ipc_recv_and_yield` itself takes raw pointers
    // and only creates momentary `&mut`s strictly outside its
    // `cpu.context_switch` window (per the scheduler module's shared safety
    // contract). The four statics (`SCHED`, `EP_ARENA`, `IPC_QUEUES`,
    // `TABLE_B`) refer to distinct referents. `CPU` is accessed via `&`, an
    // immutable borrow which is always aliasing-safe. No `&mut` in this
    // task's stack frame crosses the cooperative switch — this is the
    // pattern that retires UNSAFE-2026-0012. Audit: UNSAFE-2026-0014.
    let recv_outcome = unsafe {
        ipc_recv_and_yield(
            SCHED.as_mut_ptr(),
            (*CPU.0.get()).assume_init_ref(),
            EP_ARENA.as_mut_ptr(),
            IPC_QUEUES.as_mut_ptr(),
            TABLE_B.as_mut_ptr(),
            *(*EP_CAP_B.0.get()).assume_init_ref(),
            activate_address_space,
        )
        .expect("task B: ipc_recv failed")
    };

    let RecvOutcome::Received { msg, .. } = recv_outcome else {
        panic!("task B: expected Received outcome from ipc_recv_and_yield")
    };

    // SAFETY: CONSOLE initialised in kernel_entry; single-core cooperative. Audit: UNSAFE-2026-0010.
    let console = unsafe { (*CONSOLE.0.get()).assume_init_ref() };
    let mut w = FmtWriter(console);
    let _ = writeln!(
        w,
        "tyrne: task B \u{2014} received IPC (label=0x{:x}); replying",
        msg.label
    );

    // Send reply. Since Task A is in the ready queue (not yet blocked on recv),
    // this transitions the endpoint to SendPending and returns Enqueued — no
    // auto-yield. An explicit yield_now follows so Task A can collect the reply.
    let reply = Message {
        label: 0xBBBB,
        params: [0; 3],
    };
    // SAFETY: per ADR-0021 — same raw-pointer discipline as the
    // `ipc_recv_and_yield` call above. `yield_now` follows the same shared
    // safety contract — caller-side never materialises a `&mut` across the
    // switch. Audit: UNSAFE-2026-0014.
    unsafe {
        ipc_send_and_yield(
            SCHED.as_mut_ptr(),
            (*CPU.0.get()).assume_init_ref(),
            EP_ARENA.as_mut_ptr(),
            IPC_QUEUES.as_mut_ptr(),
            TABLE_B.as_mut_ptr(),
            *(*EP_CAP_B.0.get()).assume_init_ref(),
            reply,
            None,
            activate_address_space,
        )
        .expect("task B: ipc_send reply failed");

        // Yield explicitly so Task A can receive the reply that was just queued
        // as SendPending. Without this yield, A's ipc_recv_and_yield would never
        // run (cooperative scheduling; B never blocks again after the send).
        // `yield_now` only errors with `NoCurrentTask`, which cannot happen
        // once the scheduler has started.
        yield_now(
            SCHED.as_mut_ptr(),
            (*CPU.0.get()).assume_init_ref(),
            activate_address_space,
        )
        .expect("task B: yield_now after reply failed");
    }

    // Unreachable in the v1 single-round demo — see the task_b doc comment.
    // The loop satisfies `fn() -> !`; Task A's `ipc_recv_and_yield` runs to
    // its own spin loop without yielding back, so no further Task B code
    // executes. A post-reply epilogue would require either a dedicated
    // rendezvous (e.g. a completion notification) or an extra yield from
    // Task A, both out of scope for A6.
    loop {
        core::hint::spin_loop();
    }
}

// ─── Task A ───────────────────────────────────────────────────────────────────

/// IPC demo — initiator side. Sends a message to Task B, then waits for
/// the reply. On receiving the reply, prints the Phase A completion banner.
fn task_a() -> ! {
    // SAFETY: CONSOLE initialised in kernel_entry; single-core cooperative.
    // Audit: UNSAFE-2026-0010.
    let console = unsafe { (*CONSOLE.0.get()).assume_init_ref() };
    console.write_bytes(b"tyrne: task A -- sending IPC\n");

    let msg = Message {
        label: 0xAAAA,
        params: [1, 2, 3],
    };

    // Send to Task B. Because the scheduler adds B before A, B has already
    // called ipc_recv_and_yield and is in RecvWaiting state. The send delivers
    // immediately (Delivered) and ipc_send_and_yield yields to B.
    //
    // SAFETY: per ADR-0021 — same raw-pointer discipline as task_b.
    // Audit: UNSAFE-2026-0014.
    unsafe {
        ipc_send_and_yield(
            SCHED.as_mut_ptr(),
            (*CPU.0.get()).assume_init_ref(),
            EP_ARENA.as_mut_ptr(),
            IPC_QUEUES.as_mut_ptr(),
            TABLE_A.as_mut_ptr(),
            *(*EP_CAP_A.0.get()).assume_init_ref(),
            msg,
            None,
            activate_address_space,
        )
        .expect("task A: ipc_send failed");
    }

    // Task A resumes here after B delivered the reply. The endpoint is now in
    // SendPending (B's reply). Calling ipc_recv_and_yield collects it immediately
    // without blocking (SendPending → Received → Idle).
    //
    // SAFETY: per ADR-0021 — same raw-pointer discipline as task_b's
    // ipc_recv_and_yield call. Audit: UNSAFE-2026-0014.
    let reply_outcome = unsafe {
        ipc_recv_and_yield(
            SCHED.as_mut_ptr(),
            (*CPU.0.get()).assume_init_ref(),
            EP_ARENA.as_mut_ptr(),
            IPC_QUEUES.as_mut_ptr(),
            TABLE_A.as_mut_ptr(),
            *(*EP_CAP_A.0.get()).assume_init_ref(),
            activate_address_space,
        )
        .expect("task A: ipc_recv (reply) failed")
    };

    let RecvOutcome::Received { msg: reply, .. } = reply_outcome else {
        panic!("task A: expected Received outcome from reply ipc_recv_and_yield")
    };

    // SAFETY: CONSOLE initialised in kernel_entry; single-core cooperative. Audit: UNSAFE-2026-0010.
    let console = unsafe { (*CONSOLE.0.get()).assume_init_ref() };
    let mut w = FmtWriter(console);
    let _ = writeln!(
        w,
        "tyrne: task A \u{2014} received reply (label=0x{:x}); done",
        reply.label
    );
    console.write_bytes(b"tyrne: all tasks complete\n");

    // T-009 measurement: print boot-to-end elapsed time. Uses `now_ns` on
    // the live Timer impl and the BOOT_NS snapshot taken in `kernel_main_high`.
    // `saturating_sub` is defensive — the hardware counter is monotonic so
    // `now >= boot_ns` always holds, but the saturating form makes the
    // subtraction's correctness obvious to a reader scanning for overflow
    // hazards.
    //
    // SAFETY: CPU and BOOT_NS were both initialised in `kernel_entry`
    // before `start()`; single-core cooperative scheduling prevents any
    // concurrent writer. Audit: UNSAFE-2026-0010.
    let elapsed_ns = unsafe {
        let cpu = (*CPU.0.get()).assume_init_ref();
        let boot_ns = *(*BOOT_NS.0.get()).assume_init_ref();
        cpu.now_ns().saturating_sub(boot_ns)
    };
    let _ = writeln!(w, "tyrne: boot-to-end elapsed = {elapsed_ns} ns",);

    loop {
        core::hint::spin_loop();
    }
}

// ─── Syscall-boundary smoke — gate #3 fail-closed (T-026) ─────────────────────

/// EL1 `SVC` smoke for the syscall boundary, demonstrating **gate #3
/// fail-closed** ([T-026]).
///
/// Issues two `SVC #0` traps from EL1 (the current-EL `VBAR_EL1 + 0x200` sync
/// vector — an EL1 `SVC` cannot take the lower-EL `+0x400` path; the real-EL0
/// round-trip is the B6 wire-up). It runs **after `SCHED` is published but
/// before `start()`**, so `SCHED.current` is `None` — no running EL0 task. The
/// dispatcher therefore **fails closed**: with no current task it resolves
/// capabilities against the empty [`FAILCLOSED_TABLE`] and bounds user buffers
/// with an empty window, so a syscall carries **no authority**:
///
/// 1. **`console_write`** (number `5`) → the cap (any handle) is looked up in
///    the empty table → `SyscallError::Cap(InvalidHandle)` (status `0x102`),
///    nothing emitted. Gate #1's per-page `Mmu::translate` boundary (T-025) is
///    never reached — the cap gate rejects first; the positive copy path is
///    host-tested and runs at the B6 wire-up.
/// 2. a **reserved-invalid number** (`0`) → `SyscallError::BadSyscallNumber`
///    (status `0x1`), panic-free, capability untouched.
///
/// Both `ERET` cleanly (the `SVC` mechanism is exercised); neither over-grants.
/// `task_yield` / `task_exit` are not driven here — their gate-#3 control-plane
/// fail-closed is host-tested. This supersedes the B5 "stub mints a console cap
/// and emits a greeting" smoke: post-gate-#3 a syscall with no running task is
/// rejected, which is the security property worth demonstrating.
///
/// [T-026]: https://github.com/HodeTech/Tyrne/blob/main/docs/analysis/tasks/phase-b/T-026-current-task-cap-table.md
#[allow(
    clippy::cast_possible_truncation,
    reason = "Tyrne's BSP target is 64-bit aarch64; pointer/usize → u64 \
              register-word casts are lossless"
)]
fn syscall_boundary_smoke(console: &Pl011Uart) {
    // Initialise the empty fail-closed fallback table the dispatcher resolves
    // against when no EL0 task is current (gate #3). Never minted into.
    //
    // SAFETY: `FAILCLOSED_TABLE` lives in `.bss`; this is its single write,
    // before any `SVC` issues. Audit: UNSAFE-2026-0010 (StaticCell pattern).
    unsafe {
        (*FAILCLOSED_TABLE.0.get()).write(CapabilityTable::new());
    }

    // (1) console_write via SVC with no current task → fail-closed InvalidHandle.
    // The cap word (`0`) and the buffer are irrelevant: with `SCHED.current ==
    // None` the dispatcher resolves against the empty `FAILCLOSED_TABLE`, so the
    // cap lookup rejects before the window / per-page translate is ever reached.
    let buf: &[u8] = b"tyrne: (no current task; gate #3 fail-closed)\n";
    let cap_word = 0u64;
    let status: u64;
    // SAFETY: `SVC #0` traps to the EL1 current-EL sync vector (+0x200), runs
    // the panic-free dispatcher, and `ERET`s back here. x8 = number, x0..x2 =
    // args; the handler writes x0 = status, clobbers x0..x7, preserves
    // x8..x30 + SP_EL0. Audit: UNSAFE-2026-0029.
    unsafe {
        core::arch::asm!(
            "svc #0",
            in("x8") 5u64,
            inout("x0") cap_word => status,
            inout("x1") buf.as_ptr() as u64 => _,
            in("x2") buf.len() as u64,
            out("x3") _,
            out("x4") _,
            out("x5") _,
            out("x6") _,
            out("x7") _,
        );
    }

    // (2) reserved-invalid number 0 → BadSyscallNumber, panic-free.
    let bad_status: u64;
    // SAFETY: same `SVC` trap mechanism; number 0 is reserved-invalid, so the
    // dispatcher returns a typed `SyscallError::BadSyscallNumber` in x0 without
    // touching any capability or panicking. Audit: UNSAFE-2026-0029.
    unsafe {
        core::arch::asm!(
            "svc #0",
            in("x8") 0u64,
            out("x0") bad_status,
            out("x1") _,
            out("x2") _,
            out("x3") _,
            out("x4") _,
            out("x5") _,
            out("x6") _,
            out("x7") _,
        );
    }

    let mut w = FmtWriter(console);
    let _ = writeln!(
        w,
        "tyrne: syscall smoke ok (gate #3 fail-closed — no current task: console_write status={status:#x}; bad-number status={bad_status:#x})"
    );
}

// ─── Boot entry ───────────────────────────────────────────────────────────────

// Reset entry (`_start`). See `boot.s` and `docs/architecture/boot.md`.
global_asm!(include_str!("boot.s"));

// EL1 exception vector table (`tyrne_vectors`). See `vectors.s` and
// `docs/architecture/exceptions.md`. Audit: UNSAFE-2026-0020.
global_asm!(include_str!("vectors.s"));

extern "C" {
    /// Symbol exported by `vectors.s`; resolves to the 2 KiB-aligned
    /// base of the EL1 vector table. Written to `VBAR_EL1` once at
    /// boot.
    static tyrne_vectors: u8;

    /// Symbol exported by `linker.ld`; resolves to one byte past the
    /// top of the boot stack (i.e. the highest PA the kernel image
    /// occupies in `.bss` + 64 KiB stack). Used by T-017's PMM-init
    /// to compute the kernel-reserved range. Per `linker.ld` the
    /// symbol is 16-byte-aligned (post-`ALIGN(16); . = . + 64K`),
    /// so the BSP rounds it up to 4 KiB at PMM-init time.
    static __stack_top: u8;

    /// L0 root translation-table frame, reserved in `linker.ld`'s
    /// `.bss` section by T-016. `mmu_bootstrap()` populates it with
    /// the bootstrap kernel mappings + writes its address to
    /// `TTBR0_EL1`. T-018 commit 5 reads its PA here to wrap the
    /// already-live topology in an [`AddressSpace<QemuVirtMmu>`]
    /// kernel object — per ADR-0028 §Simulation row 0, the wrap
    /// must NOT call `Mmu::create_address_space` (which would
    /// re-zero the L0 frame).
    static __boot_pt_l0: [u64; 512];
}

/// Mask of the low 4 GiB of physical address space — the bound on the QEMU
/// virt kernel image PA. The migration `br`/`VBAR` targets are derived by
/// masking a symbol address to this and OR-ing [`KERNEL_HIGH_HALF_OFFSET`]; a
/// future BSP with an image PA ≥ 4 GiB (e.g. Pi 4) must revisit this + the
/// offset (see [`high_half_alias`] + the linker.ld / `KERNEL_HIGH_HALF_OFFSET`
/// forward-notes).
const KERNEL_IMAGE_PA_MASK: usize = 0xFFFF_FFFF;

/// Compute the high-half image alias of a kernel-symbol address, for the
/// boot-time migration's `MSR VBAR_EL1` / `br` targets.
///
/// Masking the low 32 bits recovers the symbol's **PA** whether the compiler
/// materialised it PC-relative (low, while `kernel_entry` runs at the low
/// physical alias) or absolute (high); OR-ing [`KERNEL_HIGH_HALF_OFFSET`] then
/// yields its high-half VA. Correct only while the image PA is below 4 GiB —
/// the `debug_assert!` fails fast (in debug builds) if `addr` is neither a low
/// PA nor its exact high-half alias, which would mean the image escaped the
/// low-4 GiB window the mask assumes.
#[inline]
fn high_half_alias(addr: usize) -> usize {
    let pa = addr & KERNEL_IMAGE_PA_MASK;
    debug_assert!(
        addr == pa || addr == (KERNEL_HIGH_HALF_OFFSET | pa),
        "migration: symbol address is neither a low PA nor its high-half alias \
         — the kernel image PA must be < 4 GiB (KERNEL_IMAGE_PA_MASK)",
    );
    KERNEL_HIGH_HALF_OFFSET | pa
}

/// Low-half boot entry — the `_start` (`boot.s`) branch target.
///
/// Runs at the LOW physical alias of the kernel image with the MMU off (the
/// linker forces the ELF entry to the physical address of `_start`; see
/// [`linker.ld`] + [ADR-0033]). It enables the low-identity MMU, builds the
/// high-half (`TTBR1_EL1`) tables, then performs the boot-time high-half
/// migration: install the high vectors, rebase `SP` to the high stack alias,
/// and branch the PC into [`kernel_main_high`] (the high-half image alias).
/// It never returns.
///
/// Only PC-relative-safe, identity-mapped work happens here (early
/// diagnostics via a throwaway low-MMIO console, the MMU bring-up, the
/// migration asm). Everything that takes a `&'static`/function-pointer
/// address (the `StaticCell` publishes, `create_task`, the scheduler) lives
/// in [`kernel_main_high`] so those absolute addresses resolve HIGH and stay
/// reachable once `TTBR0_EL1` is freed for userspace.
///
/// [ADR-0033]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0033-kernel-high-half-migration.md
/// [`linker.ld`]: https://github.com/HodeTech/Tyrne/blob/main/bsp-qemu-virt/linker.ld
#[unsafe(no_mangle)]
pub extern "C" fn kernel_entry() -> ! {
    // ── Early diagnostics (low identity) ──────────────────────────────────────
    //
    // A throwaway console at the LOW PL011 MMIO base (identity-mapped while
    // the migration has not yet run). The persistent `CONSOLE` StaticCell is
    // constructed with the HIGH device-MMIO alias only after the migration,
    // in `kernel_main_high`.
    //
    // SAFETY: 0x0900_0000 is the well-known QEMU virt PL011 UART MMIO base,
    // exclusively owned by this kernel in v1, identity-mapped pre-migration.
    // Audit: UNSAFE-2026-0001.
    let early_console = unsafe { Pl011Uart::new(PL011_UART_BASE) };
    early_console.write_bytes(b"tyrne: hello from kernel_main\n");

    // ── Exception vector install — T-012 (must run before mmu_bootstrap) ──────
    //
    // `mmu_bootstrap`'s Step 3 is the only point in v1 where a fault
    // is plausible *before* steady-state code paths take over: a typo
    // in any descriptor or system-register value would surface as a
    // Translation / Permission Fault on the next instruction-fetch
    // after `SCTLR.M = 1` (per ADR-0027 §Simulation §Step 3).
    // Installing VBAR_EL1 first means such a fault goes to the
    // panic-class vector (which writes to UART and halts) rather
    // than fetching from VBAR's reset value (silent hang). System-
    // register writes are MMU-independent, so this step is safe to
    // run pre-MMU.
    //
    // Limit of this defence (recorded by 2026-05-09 review-round
    // Axis 4): the panic vector itself fetches from PA `tyrne_vectors`
    // and writes diagnostic output to the PL011 UART. If the bad
    // descriptor lives in `L2_high[0]` (kernel image — covers
    // `0x4000_0000..0x4020_0000`, which contains the panic vector
    // itself) or `L2_low[72]` (the 2 MiB block containing the PL011
    // UART at `0x0900_0000`), the fault produces a recursive trap
    // (silent hang) that pre-installing VBAR_EL1 cannot rescue. The
    // defence covers ~80 % of the descriptor-error failure surface;
    // the remaining 20 % is caught by the host-tested encoders + the
    // §Simulation table review discipline.

    // SAFETY: `tyrne_vectors` is exported by src/vectors.s as the
    // 2 KiB-aligned base of the EL1 vector table. `MSR VBAR_EL1, x`
    // is privileged at EL1 (always available); the write does not
    // mutate any other state and `options(nostack, nomem)` is correct
    // (the asm reads no memory, writes no stack). Audit: UNSAFE-2026-0020.
    unsafe {
        let vbar_addr = core::ptr::addr_of!(tyrne_vectors) as u64;
        core::arch::asm!(
            "msr vbar_el1, {0}",
            "isb",
            in(reg) vbar_addr,
            options(nostack, nomem),
        );
    }

    // ── MMU activation — T-016 / ADR-0027 ─────────────────────────────────────
    //
    // Activates the MMU with the v1 identity-mapped layout per
    // ADR-0027 §Decision outcome (a). After this call returns, every
    // subsequent load and instruction-fetch goes through the live
    // translation regime; MMIO accesses go through the device-nGnRnE
    // mapping installed for `0x0800_0000..0x0920_0000` (GIC + UART).
    // GIC `init` and the timer banner therefore *follow* this call so
    // their MMIO writes inherit the device attributes.

    // SAFETY: called exactly once per boot, at EL1, with `.boot_pt`
    // pre-zeroed by `_start`'s BSS-zero loop, before any subsequent
    // MMIO step (GIC init, timer banner). The kernel image lives at
    // PA `0x4008_0000` and is identity-covered by L2_high[0..64].
    // Audit: UNSAFE-2026-0022 (page-table writes) + UNSAFE-2026-0023
    // (system-register writes — MAIR/TCR/TTBR/SCTLR) +
    // UNSAFE-2026-0024 (TLB / I-cache invalidate asm).
    unsafe {
        mmu_bootstrap::mmu_bootstrap();
    }
    early_console.write_bytes(b"tyrne: mmu activated\n");

    // ── High-half table build — T-022 / ADR-0033 §Simulation rows 0-1 ─────────
    //
    // Build the TTBR1_EL1 tables and enable TTBR1 walks (EPD1 1→0). Both
    // translation regimes are live on return; the kernel still executes low.
    //
    // SAFETY: called once, at EL1, after `mmu_bootstrap` (the shared L2 tables
    // + the low-identity MMU are live) and before the migration trampoline.
    // Audit: UNSAFE-2026-0022 / 0023 (Amendments).
    unsafe {
        mmu_bootstrap::high_half_activate();
    }

    // ── Boot-time high-half migration — T-022 / ADR-0033 §Simulation row 2 ────
    //
    // Install the high VBAR (so a fault on the first high fetch vectors to a
    // mapped handler), rebase SP to the high stack alias, and branch the PC
    // into the high-half image (`kernel_main_high`). The low identity stays
    // live (TTBR0 is freed inside `kernel_main_high`), DAIF is masked (since
    // `_start`), and no `StaticCell` holds a low VA yet, so the few pre-`br`
    // instructions cannot brick. The high targets are derived by masking the
    // (PC-relative-resolved) address to its physical part and OR-ing the
    // high-half offset, so the computation is correct regardless of how the
    // compiler materialises the symbol addresses.
    let high_vbar = high_half_alias(core::ptr::addr_of!(tyrne_vectors) as usize);
    let high_entry = high_half_alias(kernel_main_high as *const () as usize);
    // SAFETY: the absolute-jump migration trampoline (ADR-0033 §Simulation
    // row 2). `MSR VBAR_EL1` to the high vector base (mapped PXN=0 in TTBR1) +
    // `ISB` so high vectors are live before the branch; `add sp, sp, off`
    // rebases SP to the high alias of the same boot stack; `br` crosses the PC
    // from the low identity to the high-half image alias. Both regimes are
    // live across the branch and DAIF is masked, so the crossing cannot fault.
    // `options(noreturn)`: control never returns (kernel_main_high is `-> !`),
    // so changing SP here is sound. Audit: UNSAFE-2026-0031.
    unsafe {
        core::arch::asm!(
            "msr vbar_el1, {vbar}",
            "isb",
            "add sp, sp, {off}",
            "br  {entry}",
            vbar = in(reg) high_vbar,
            off = in(reg) KERNEL_HIGH_HALF_OFFSET,
            entry = in(reg) high_entry,
            options(noreturn),
        );
    }
}

/// High-half kernel main — the migration trampoline's branch target.
///
/// Entered via `br` from [`kernel_entry`] with the PC, `SP`, and `VBAR_EL1`
/// all resolving through the high half (`TTBR1_EL1`). Frees `TTBR0_EL1` (the
/// low identity) for per-task userspace, then runs the full boot sequence
/// (console / CPU / PMM / address space / loader / IPC / syscall smoke /
/// scheduler) at high-half addresses. Never returns.
///
/// `#[inline(never)]` + `#[unsafe(no_mangle)]` keep it a stable, addressable
/// symbol — `kernel_entry` takes its address to compute the migration branch
/// target.
///
/// # Panics
///
/// Panics if any kernel-object allocation or capability-table operation
/// fails; all capacities are statically bounded and the demo uses far fewer
/// objects than the limits, so in practice none of these branches are
/// reachable.
#[unsafe(no_mangle)]
#[inline(never)]
#[allow(
    clippy::too_many_lines,
    reason = "BSP boot sequence is intentionally linear top-to-bottom for auditability — splitting into helpers obscures the order each phase depends on (per docs/standards/bsp-boot-checklist.md)"
)]
extern "C" fn kernel_main_high() -> ! {
    // ── Free TTBR0 — the low identity — T-022 / ADR-0033 §Simulation row 3 ────
    //
    // SP was rebased to the high alias by the migration trampoline, so this
    // function's frame is already high. Null `TTBR0_EL1`, set `EPD0 = 1`
    // (disable TTBR0 walks until a per-task AS activates), and flush stale low
    // translations. After this the kernel is structurally absent from the low
    // half — `TTBR0_EL1` is free for userspace.
    //
    // SAFETY: register-only writes (no table-memory mutation, so no `DSB`
    // before the `TLBI` is required). `MSR TTBR0_EL1, xzr` + `ISB`; set `EPD0`
    // via a read-modify-write of `TCR_EL1` + `ISB`; `TLBI VMALLE1` + `DSB ISH`
    // + `ISB` to drop and complete the stale low translations.
    // Audit: UNSAFE-2026-0023 / 0024 (Amendments) + UNSAFE-2026-0031.
    unsafe {
        core::arch::asm!(
            "msr ttbr0_el1, xzr",
            "isb",
            "mrs {t}, tcr_el1",
            "orr {t}, {t}, {epd0}",
            "msr tcr_el1, {t}",
            "isb",
            "tlbi vmalle1",
            "dsb ish",
            "isb",
            epd0 = in(reg) TCR_EL1_EPD0_BIT,
            t = out(reg) _,
            options(nostack, nomem),
        );
    }

    // ── Hardware setup (high-half device MMIO) ────────────────────────────────
    //
    // The console + GIC now reach the PL011 / GIC registers through the HIGH
    // device-MMIO alias (`phys_to_kernel_va`) — the low identity is gone.
    //
    // SAFETY: the PL011 UART reached via its high-half alias is the same
    // device, exclusively owned in v1. Audit: UNSAFE-2026-0001.
    let console = unsafe { Pl011Uart::new(tyrne_hal::phys_to_kernel_va(PL011_UART_BASE)) };
    // SAFETY: constructed exactly once; single-core v1; we are at EL1 (the EL
    // drop completed in boot.s). See QemuVirtCpu::new # Safety. Audit: UNSAFE-2026-0006.
    let cpu = unsafe { QemuVirtCpu::new() };

    // SAFETY: single-core; no concurrent writer exists before `start()`.
    // Audit: UNSAFE-2026-0001.
    unsafe {
        (*CONSOLE.0.get()).write(console);
        (*CPU.0.get()).write(cpu);
    }
    // SAFETY: CONSOLE / CPU written just above. Audit: UNSAFE-2026-0001.
    let console = unsafe { (*CONSOLE.0.get()).assume_init_ref() };
    // SAFETY: as above. Audit: UNSAFE-2026-0001.
    let cpu = unsafe { (*CPU.0.get()).assume_init_ref() };

    console.write_bytes(b"tyrne: high-half active\n");

    // ── boot_ns snapshot (T-016 / ADR-0027; post-migration per ADR-0033) ──────
    //
    // `cpu.now_ns()` reads `CNTVCT_EL0` (system register, MMU-independent).
    // Sampled just after the high-half migration so the boot-to-end baseline
    // measures the high-half steady state. NOTE: this excludes BOTH
    // `mmu_bootstrap` (MMU activation, ~< 100 µs — which the pre-T-022 boot_ns
    // deliberately *included*) and the migration (~ a few µs), so the metric's
    // meaning shifted vs the pre-T-022 baseline (now "high-half-steady-state to
    // end", not "MMU-activation to end"). Both excluded costs are immaterial
    // against the ~ms boot-to-end total; the perf review records the shift.
    let boot_ns = cpu.now_ns();
    // SAFETY: single-core; no concurrent writer exists before `start()`.
    // Audit: UNSAFE-2026-0001.
    unsafe {
        (*BOOT_NS.0.get()).write(boot_ns);
    }

    // ── PMM init — T-017 / ADR-0035 ──────────────────────────────────────────
    //
    // Activates the Physical Memory Manager over the 128 MiB QEMU virt
    // RAM extent with two reserved ranges (firmware region + kernel
    // image / .bss / .boot_pt / boot stack). After this call returns
    // any future Mmu::map call (none in v1's cooperative demo; first
    // caller is B3+ AddressSpace bring-up via T-018) can pull frames
    // by passing `&mut PMM` as `&mut dyn FrameProvider`. The PMM stays
    // unused at runtime in v1; init is verified end-to-end by the
    // smoke trace's `tyrne: pmm initialized (...)` line and the
    // host-test coverage of `Pmm::new` + `Pmm::stats`.
    //
    // `__stack_top` is 16-byte-aligned per linker.ld (post-`ALIGN(16); . = . + 64K`).
    // Round up to 4 KiB so `PhysFrameRange::is_aligned` passes; the
    // few-byte slack at the tail falls into the kernel-reserved range
    // (already off-limits for the PMM) so the round-up cannot collide
    // with a valid runtime allocation.
    //
    // SAFETY: `addr_of!(__stack_top)` reads the linker symbol's
    // address without dereferencing the (zero-byte) extern static;
    // single-core boot-time, no concurrent observer. Same discipline
    // as the pre-existing `addr_of!(tyrne_vectors)` site.
    // Audit: UNSAFE-2026-0001 (StaticCell pattern for `PMM`).
    // `addr_of!` resolves HIGH here (kernel_main_high runs in the high half),
    // so convert the symbol's high-half VA back to its PA for the PMM's
    // physical-frame reservation (ADR-0033 §Negative — addr_of!-as-PA fix).
    let stack_top_addr = tyrne_hal::kernel_va_to_phys(core::ptr::addr_of!(__stack_top) as usize);
    let stack_top_aligned_up = stack_top_addr.saturating_add(PAGE_SIZE - 1) & !(PAGE_SIZE - 1);
    let pmm_extent = PhysFrameRange::new(PhysAddr(PMM_EXTENT_START), PhysAddr(PMM_EXTENT_END));
    let pmm_reserved = [
        // (1) QEMU firmware-reserved region: PMM extent start
        // through the kernel image's load address.
        PhysFrameRange::new(PhysAddr(PMM_EXTENT_START), PhysAddr(KERNEL_IMAGE_START)),
        // (2) Kernel image (.text + .rodata + .data) + .bss
        // (which contains .boot_pt) + boot-stack region.
        PhysFrameRange::new(PhysAddr(KERNEL_IMAGE_START), PhysAddr(stack_top_aligned_up)),
    ];
    let pmm_value = BspPmm::new(pmm_extent, &pmm_reserved)
        .expect("Pmm::new — BSP-static config; reservation list is well-formed by construction");

    // SAFETY: single-core; no concurrent writer exists before `start()`.
    // Audit: UNSAFE-2026-0001.
    unsafe {
        (*PMM.0.get()).write(pmm_value);
    }

    // Banner with stats. SAFETY: PMM was just written above; the
    // `&` reference does not outlive the `writeln!` borrow.
    // Audit: UNSAFE-2026-0001.
    let pmm_stats = unsafe { (*PMM.0.get()).assume_init_ref().stats() };
    {
        let mut w = FmtWriter(console);
        let _ = writeln!(
            w,
            "tyrne: pmm initialized ({} frames available; {} reserved)",
            pmm_stats.free_frames, pmm_stats.reserved_frames
        );
    }

    // ── Address-space arena init — T-018 / ADR-0028 ───────────────────────────
    //
    // Materialise the BSP-specific `Mmu` instance, then wrap the
    // already-active L0 root frame (written into `TTBR0_EL1` by
    // `mmu_bootstrap` above) into a kernel-side `AddressSpace<QemuVirtMmu>`
    // and publish it as arena slot 0 (the bootstrap AS). Mint the
    // bootstrap AS authority cap in `BOOTSTRAP_AS_TABLE`. Order
    // (per ADR-0028 §Simulation row 0): wrap_existing_root → wrap_bootstrap
    // → arena.alloc → cap mint → banner. **No** `Mmu::create_address_space`
    // call on the bootstrap root — that would re-zero the live L0 frame
    // and break the running translation tables.

    // SAFETY: MMU is a zero-sized type; writing through the StaticCell
    // is bookkeeping only. Audit: UNSAFE-2026-0010.
    unsafe {
        (*MMU.0.get()).write(mmu::QemuVirtMmu::new());
    }

    // SAFETY: AS_ARENA is in `.bss` (zero-init'd by _start); the write
    // here installs the default-constructed arena. Audit: UNSAFE-2026-0010.
    unsafe {
        (*AS_ARENA.0.get()).write(tyrne_kernel::mm::AddressSpaceArena::<mmu::QemuVirtMmu>::new());
    }

    // Compute the L0 root PA. The `__boot_pt_l0` linker symbol resolves
    // to the PA of the bootstrap L0 frame (identity-mapped post-MMU per
    // ADR-0027), already populated by `mmu_bootstrap` and written into
    // TTBR0_EL1.
    //
    // SAFETY: `addr_of!` of an `extern "C"` static is itself safe — no
    // load happens here, only the symbol's address is taken.
    let l0_root = {
        // `addr_of!` resolves HIGH (high-half execution); the L0 root is named
        // by its PA, so convert back (ADR-0033 §Negative — addr_of!-as-PA fix).
        let pa = tyrne_hal::kernel_va_to_phys(core::ptr::addr_of!(__boot_pt_l0) as usize);
        tyrne_hal::PhysFrame::from_aligned(PhysAddr(pa))
            .expect("L0 root must be 4 KiB-aligned per linker.ld `.boot_pt` reservation")
    };

    // Wrap the bootstrap root (the low-identity L0 `mmu_bootstrap` built)
    // and publish it as arena slot 0. The `bootstrap_root_pa` for the banner
    // is read directly from `l0_root` — the wrapped `AddressSpace<QemuVirtMmu>`
    // stores exactly this `PhysFrame` and the round-trip is pinned by
    // `wrap_bootstrap_returns_address_space_with_root` in
    // `kernel/src/mm/address_space.rs::tests`.
    let bootstrap_root_pa = l0_root.as_usize();
    // SAFETY:
    // - AS_ARENA was just written above; the momentary &mut to the
    //   just-initialised arena (the `assume_init_mut()` line) drops at
    //   scope end. Audit: UNSAFE-2026-0010 (StaticCell pattern) +
    //   UNSAFE-2026-0014 (momentary &mut to the just-initialised arena).
    //   These two entries cover ONLY the StaticCell/arena publish
    //   mechanics, not the `from_existing_root` wrap below.
    // - `QemuVirtAddressSpace::from_existing_root(l0_root)` requires
    //   `l0_root` to be a valid, **populated** VMSAv8 L0 translation table
    //   (see its `# Safety` doc). `mmu_bootstrap` populated this exact frame
    //   as the low-identity root and installed it in `TTBR0_EL1`; **post-T-022
    //   `kernel_main_high` has already freed `TTBR0_EL1` (null + `EPD0 = 1`)
    //   before this block runs**, so the frame is no longer the *live* TTBR0 —
    //   it is a populated-but-uninstalled table retained as arena slot 0
    //   (kernel-init's AS authority + the cap-derivation parent for the
    //   loader). Its descriptors are correctly encoded per the host-tested
    //   `tyrne_hal::mmu::vmsav8` encoders. The wrap does NOT zero-fill (which
    //   would corrupt the populated descriptor topology a future `activate` /
    //   `map` walk relies on) — that is why it cannot route through the
    //   zero-fill `create_address_space`. Audit: UNSAFE-2026-0028 (+ its
    //   2026-05-30 T-022 Amendment refining "live" → "populated").
    let bootstrap_as_handle = unsafe {
        let arena = (*AS_ARENA.0.get()).assume_init_mut();
        let inner = mmu::QemuVirtAddressSpace::from_existing_root(l0_root);
        // Stash a copy for `syscall_entry`'s `task_as` (gate #1 translation
        // source). `QemuVirtAddressSpace` is `Copy` — the same root the kernel
        // arena's bootstrap AS wraps below. Audit: UNSAFE-2026-0010 (StaticCell).
        (*BOOTSTRAP_AS.0.get()).write(inner);
        let address_space = tyrne_kernel::mm::AddressSpace::wrap_bootstrap(inner);
        tyrne_kernel::mm::create_address_space(arena, address_space)
            .expect("bootstrap AS allocation in empty arena cannot fail")
    };

    // Mint the bootstrap AS authority cap. The kernel-init holds full
    // rights over the bootstrap AS; future per-AS caps land via
    // cap_create_address_space with narrowed rights.
    //
    // SAFETY: BOOTSTRAP_AS_TABLE in `.bss`; write installs the
    // default-constructed table. Audit: UNSAFE-2026-0010.
    unsafe {
        (*BOOTSTRAP_AS_TABLE.0.get()).write(CapabilityTable::new());
    }
    // SAFETY: BOOTSTRAP_AS_TABLE just written; momentary &mut for the
    // insert_root call drops at scope end. Audit: UNSAFE-2026-0014.
    let bootstrap_as_cap = unsafe {
        let table = (*BOOTSTRAP_AS_TABLE.0.get()).assume_init_mut();
        let cap = Capability::new(
            CapRights::DUPLICATE | CapRights::DERIVE | CapRights::REVOKE | CapRights::TRANSFER,
            CapObject::AddressSpace(bootstrap_as_handle),
        );
        table
            .insert_root(cap)
            .expect("bootstrap AS cap mint in empty table cannot fail")
    };
    // SAFETY: BOOTSTRAP_AS_CAP write installs the just-minted handle.
    // Audit: UNSAFE-2026-0010.
    unsafe {
        (*BOOTSTRAP_AS_CAP.0.get()).write(bootstrap_as_cap);
    }

    {
        let mut w = FmtWriter(console);
        let _ = writeln!(
            w,
            "tyrne: address-space-arena ready (1 / {} slots used; bootstrap AS root = {:#x})",
            tyrne_kernel::mm::ADDRESS_SPACE_ARENA_CAPACITY,
            bootstrap_root_pa
        );
    }

    // ── Task loader smoke — T-019 / ADR-0029 ──────────────────────────────────
    //
    // First runtime exerciser of the loader half of B4: load the
    // embedded raw-flat userspace placeholder blob into a fresh
    // address space and print a one-line metadata banner. **Does NOT
    // execute the loaded image** — runnability gates on B5/B6 per
    // phase-b §B4 §Revision-notes. This block is the first post-
    // bootstrap caller of `cap_create_address_space` + `cap_map`, so
    // it exercises UNSAFE-2026-0025 (page-table descriptor writes)
    // and UNSAFE-2026-0026 (PMM frame zero-fill) for real, and is
    // the introducing site for UNSAFE-2026-0027 (the loader's
    // copy_nonoverlapping byte-copy).
    //
    // SAFETY:
    // **Why unsafe is required.** The block materialises momentary
    // `&mut`/`&` references to the five write-once static cells
    // `PMM` / `MMU` / `AS_ARENA` / `BOOTSTRAP_AS_TABLE` /
    // `BOOTSTRAP_AS_CAP` via `assume_init_{mut,ref}` on
    // `MaybeUninit<T>`. The compiler cannot prove these cells are
    // already initialised at this point, nor that no concurrent peer
    // holds an alias — that reasoning lives in the BSP boot flow's
    // initialisation order and the v1 single-core cooperative model.
    //
    // **Invariants upheld.**
    // (1) **Initialisation order.** All five cells are written exactly
    //     once earlier in `kernel_entry`, before this block runs:
    //     `PMM` (post-`mmu_bootstrap` PMM-init step); `MMU` and
    //     `AS_ARENA` (T-018 AS-arena init step); `BOOTSTRAP_AS_TABLE`
    //     and `BOOTSTRAP_AS_CAP` (bootstrap-AS-cap mint step). Each
    //     `assume_init_*` therefore satisfies `MaybeUninit`'s
    //     initialised-payload contract.
    // (2) **No concurrent aliasing.** v1 is single-core + cooperative
    //     and the scheduler has not been started yet (`SCHED` is not
    //     written and `start()` not invoked until far below this
    //     block), so no peer task or interrupt handler can observe
    //     the cells while this block runs.
    // (3) **Scope-limited &mut.** The four `&mut`s (`pmm`, `table`,
    //     `arena`, plus the `&` for `mmu` and the by-value copy for
    //     `parent_cap`) are local `let` bindings inside the
    //     `unsafe { ... }` expression. They drop at the closing
    //     brace and do **not** cross any cooperative switch — the
    //     borrow lifetimes are bounded by the single `load_image`
    //     call inside this same block per ADR-0021's no-`&mut`-
    //     across-switch discipline.
    // (4) **Audit IDs.** Pattern is covered by UNSAFE-2026-0010
    //     (`StaticCell`'s `Sync` marker + write-once contract) and
    //     UNSAFE-2026-0014 (momentary `&mut` to just-initialised
    //     state across the cooperative-switch boundary).
    //
    // **Why safer alternatives were rejected.** A `Box<Mutex<T>>` /
    // `RwLock<T>` would require either a heap allocator (v1's
    // bare-metal kernel has none) or a spin lock that is itself
    // `unsafe` to construct + adds boot-time overhead with no
    // soundness win under single-core cooperative semantics.
    // `OnceCell` / `LazyCell` from `core` require a constructor
    // closure invoked at access time, which cannot express the
    // boot-flow ordering constraints this block depends on (PMM
    // must be initialised before MMU before AS arena before
    // cap-table). The `StaticCell` + write-once pattern is the
    // minimal `Sync` shape that matches the actual boot semantics;
    // every access path is `unsafe` so the audit log can name
    // exactly which invariants each call site relies on.
    let loaded = unsafe {
        let pmm = (*PMM.0.get()).assume_init_mut();
        let mmu = (*MMU.0.get()).assume_init_ref();
        let table = (*BOOTSTRAP_AS_TABLE.0.get()).assume_init_mut();
        let arena = (*AS_ARENA.0.get()).assume_init_mut();
        let parent_cap = *(*BOOTSTRAP_AS_CAP.0.get()).assume_init_ref();
        // `new_rights = CapRights::empty()` is intentional in v1: the
        // address-space cap-rights model is **kind-only** today, not
        // per-operation. `resolve_address_space_cap`'s doc-comment
        // (`kernel/src/mm/address_space.rs`) records the v1 contract
        // — "this helper checks the cap *kind* only — not the specific
        // rights bits; per-operation rights (`MAP`, `UNMAP`, `ACTIVATE`)
        // are deferred to B5+ and will require an ADR". The
        // `CapRights` enum (`kernel/src/cap/rights.rs`) accordingly
        // exposes `DUPLICATE / DERIVE / REVOKE / TRANSFER / SEND / RECV /
        // NOTIFY` only — no `MAP` / `UNMAP` bit exists to pass here.
        // When the future ADR introduces them, this call site updates
        // to `CapRights::MAP | CapRights::UNMAP` (the minimum set the
        // loader exercises on the new cap: `cap_map` for installs +
        // `cap_unmap` for rollback); the change is purely additive at
        // this site.
        load_image(
            USERSPACE_IMAGE,
            pmm,
            mmu,
            table,
            arena,
            parent_cap,
            CapRights::empty(),
            VirtAddr(USERSPACE_IMAGE_BASE_VA),
            USERSPACE_STACK_PAGES,
        )
        .expect("task_loader::load_image failed on BSP smoke")
    };

    {
        let mut w = FmtWriter(console);
        let _ = writeln!(
            w,
            "tyrne: image loaded (entry = {:#x}; sp = {:#x}; image bytes {}; stack bytes {}; AS cap = idx {})",
            loaded.entry_va.0,
            loaded.stack_top_va.0,
            loaded.image_bytes,
            loaded.stack_bytes,
            loaded.as_cap.index(),
        );
    }

    // ── GIC init + DAIF unmask — T-012 (now post-MMU) ─────────────────────────
    //
    // Sequence (per docs/architecture/exceptions.md §"Implementation map"):
    //   1. Construct + init the GIC v2 controller. `init` disables every
    //      SPI, sets default priorities, routes SPIs to CPU 0, then
    //      enables the distributor + CPU interface. No IRQ source is
    //      enabled at this point — `enable(IrqNumber)` is a separate call.
    //      MMIO writes go through the device-nGnRnE mapping installed
    //      by `mmu_bootstrap`.
    //   2. Unmask DAIF.I (clear the I bit only — D, A, F stay masked).
    //      With nothing enabled at the GIC, this is a no-op for IRQ
    //      delivery; future `enable` calls will deliver IRQs through the
    //      now-installed vector table.

    // SAFETY: QEMU virt's GICv2 distributor + CPU interface live at
    // their well-known MMIO bases (per ADR-0011 references and the
    // QemuVirtGic module-level docs); single-core v1 means no
    // concurrent writer exists. The construction itself does no MMIO.
    // Audit: UNSAFE-2026-0019.
    let gic = unsafe {
        QemuVirtGic::new(
            tyrne_hal::phys_to_kernel_va(QEMU_VIRT_GIC_DISTRIBUTOR_BASE),
            tyrne_hal::phys_to_kernel_va(QEMU_VIRT_GIC_CPU_INTERFACE_BASE),
        )
    };
    // SAFETY: single-core; no concurrent writer to GIC static yet.
    // Audit: UNSAFE-2026-0001 (StaticCell pattern) + UNSAFE-2026-0019.
    unsafe { (*GIC.0.get()).write(gic) };

    // SAFETY: GIC was just published. `init` performs the boot-time
    // MMIO programming sequence per its doc; DAIF still masked, so no
    // IRQ can fire mid-init. Audit: UNSAFE-2026-0019.
    unsafe {
        let gic_ref = (*GIC.0.get()).assume_init_ref();
        gic_ref.init();
    }

    // SAFETY: With the vector table installed and the GIC initialised
    // (but no IRQ enabled at the GIC), unmasking DAIF.I is safe — no
    // IRQ source can fire until a later `gic.enable(...)` call. The
    // other DAIF bits (D, A, F) stay masked.
    //
    // `MSR DAIFClr, #0x2` clears the I bit specifically (bit value
    // matches PSTATE.DAIF[1]; cf. ARM ARM §C5.2.7). `options(nostack,
    // nomem)` is correct.
    // Audit: UNSAFE-2026-0020.
    unsafe {
        core::arch::asm!("msr daifclr, #0x2", options(nostack, nomem),);
    }

    // ── Timer banner — T-009 (now post-MMU) ──────────────────────────────────
    //
    // The CPU's Timer impl is live the moment `QemuVirtCpu::new` returned
    // (it sampled CNTFRQ_EL0 and cached the resolution). Print the timer
    // parameters so QEMU output makes the measurement visible. The UART
    // write goes through the device-nGnRnE mapping installed by
    // `mmu_bootstrap`. The boot-to-end baseline (`BOOT_NS`) was captured just
    // above — *post* high-half migration — so it measures the high-half steady
    // state and therefore *excludes* the MMU-activation + migration cost (see
    // the `boot_ns` snapshot comment above for the metric-meaning shift vs the
    // pre-T-022 baseline, which included MMU activation).
    {
        let mut w = FmtWriter(console);
        let _ = writeln!(
            w,
            "tyrne: timer ready ({} Hz, resolution {} ns)",
            cpu.frequency_hz(),
            cpu.resolution_ns()
        );
    }

    // ── Kernel-object setup ───────────────────────────────────────────────────

    // Publish the Task arena before any `create_task` call — subsequent
    // access is via raw pointer per the ADR-0021 discipline, even though
    // the arena sees no post-setup use in the v1 demo.
    // SAFETY: single-core; no task is running yet. Audit: UNSAFE-2026-0001.
    unsafe {
        (*TASK_ARENA.0.get()).write(TaskArena::default());
    }
    // SAFETY: `TASK_ARENA` was just written above; momentary `&mut` is
    // scoped to these three `create_task` calls and drops before any task
    // runs. Audit: UNSAFE-2026-0014.
    let (handle_a, handle_b, handle_idle) = unsafe {
        let arena = &mut *TASK_ARENA.as_mut_ptr();
        let ha = create_task(
            arena,
            Task::new(0, tyrne_kernel::mm::BOOTSTRAP_ADDRESS_SPACE_HANDLE),
        )
        .expect("create_task A failed");
        let hb = create_task(
            arena,
            Task::new(1, tyrne_kernel::mm::BOOTSTRAP_ADDRESS_SPACE_HANDLE),
        )
        .expect("create_task B failed");
        let hi = create_task(
            arena,
            Task::new(2, tyrne_kernel::mm::BOOTSTRAP_ADDRESS_SPACE_HANDLE),
        )
        .expect("create_task idle failed");
        (ha, hb, hi)
    };

    // ── IPC infrastructure ────────────────────────────────────────────────────

    let mut ep_arena = EndpointArena::default();
    let ep_handle =
        create_endpoint(&mut ep_arena, Endpoint::new(0)).expect("create_endpoint failed");

    // Least privilege: both tasks need both directions on the same endpoint —
    // A sends the initial message and receives the reply; B receives the
    // initial message and sends the reply. Neither task duplicates or
    // transfers the endpoint capability (every `ipc_*` call passes `None`),
    // so DUPLICATE and TRANSFER rights are deliberately omitted.
    let ep_rights = CapRights::SEND | CapRights::RECV;

    let mut table_a = CapabilityTable::new();
    let mut table_b = CapabilityTable::new();

    let cap_a = Capability::new(ep_rights, CapObject::Endpoint(ep_handle));
    let cap_b = Capability::new(ep_rights, CapObject::Endpoint(ep_handle));

    let ep_cap_a = table_a
        .insert_root(cap_a)
        .expect("table A: insert_root failed");
    let ep_cap_b = table_b
        .insert_root(cap_b)
        .expect("table B: insert_root failed");

    // Publish IPC state before the scheduler starts.
    // SAFETY: single-core; no task is running yet. Audit: UNSAFE-2026-0001.
    unsafe {
        (*EP_ARENA.0.get()).write(ep_arena);
        (*IPC_QUEUES.0.get()).write(IpcQueues::new());
        (*TABLE_A.0.get()).write(table_a);
        (*TABLE_B.0.get()).write(table_b);
        (*EP_CAP_A.0.get()).write(ep_cap_a);
        (*EP_CAP_B.0.get()).write(ep_cap_b);
    }

    // ── Scheduler setup ───────────────────────────────────────────────────────

    let mut sched = Scheduler::<QemuVirtCpu>::new();

    // Task B is added FIRST so the scheduler runs B before A. B calls
    // ipc_recv_and_yield and enters RecvWaiting; only then does A call
    // ipc_send_and_yield, ensuring Delivered (not Enqueued) on the first send.
    // The idle task is registered via `register_idle` (NOT `add_task`) per
    // [ADR-0026]: idle lives in the dispatcher's fallback slot
    // (`Scheduler::idle`) and is dispatched only when the ready queue is
    // empty. This is the structural fix for the 2026-05-06 smoke regression
    // — idle is no longer a FIFO resident that round-robin can dispatch
    // ahead of a just-unblocked receiver.
    //
    // SAFETY: add_task / register_idle call init_context; stack tops are
    // 16-byte aligned (guaranteed by TaskStack's repr) and remain valid
    // for the process lifetime. Entry functions are `fn() -> !`. Audit:
    // UNSAFE-2026-0009 (init_context site) + UNSAFE-2026-0014
    // (register_idle's momentary `&mut Scheduler<C>` discipline).
    //
    // [ADR-0026]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0026-idle-dispatch-fallback.md
    unsafe {
        sched
            .add_task(
                cpu,
                handle_b,
                tyrne_kernel::mm::BOOTSTRAP_ADDRESS_SPACE_HANDLE,
                task_b,
                TASK_B_STACK.top(),
            )
            .expect("add_task B failed: queue full or arena exhausted");
        sched
            .add_task(
                cpu,
                handle_a,
                tyrne_kernel::mm::BOOTSTRAP_ADDRESS_SPACE_HANDLE,
                task_a,
                TASK_A_STACK.top(),
            )
            .expect("add_task A failed: queue full or arena exhausted");
        register_idle(
            core::ptr::from_mut(&mut sched),
            cpu,
            handle_idle,
            tyrne_kernel::mm::BOOTSTRAP_ADDRESS_SPACE_HANDLE,
            idle_entry,
            TASK_IDLE_STACK.top(),
        );
    }

    // Publish the scheduler before transferring control.
    // SAFETY: single-core; no task is running yet. Audit: UNSAFE-2026-0001.
    unsafe {
        (*SCHED.0.get()).write(sched);
    }

    // ── Syscall-boundary smoke — gate #3 fail-closed (T-026) ──────────────────
    //
    // Sequenced **after `SCHED` is published** (above) but **before `start()`**:
    // `syscall_entry` now sources the caller's table / AS / window from
    // `SCHED.current` (gate #3), so `SCHED` must be initialised — and `current`
    // is `None` here (the scheduler is published but not started), which is
    // exactly the fail-closed case this smoke demonstrates. The real EL0
    // `+0x400` round-trip (with a running task) is the B6 wire-up.
    syscall_boundary_smoke(console);

    console.write_bytes(b"tyrne: starting cooperative scheduler\n");

    // Transfer control to Task B (the first ready task). Does not return.
    // SAFETY: per ADR-0021 — `SCHED.as_mut_ptr()` is a pure pointer cast
    // (UNSAFE-2026-0013); `SCHED` was written above and no other code path
    // holds a `&mut Scheduler` at this point. `start` honours the raw-pointer
    // discipline: no `&mut` is live across the initial context switch.
    // Audit: UNSAFE-2026-0014.
    //
    // No defensive `loop {}` follows: `start` is `-> !`, so the type
    // system proves nothing after this call is reachable. Adding a
    // belt-and-braces parking loop would be flagged as
    // `unreachable_code` — for the `-> !` case the type signature is
    // already the belt-and-braces (any future refactor that drops
    // `-> !` becomes a hard build error in every caller's return-type
    // analysis).
    unsafe {
        start(SCHED.as_mut_ptr(), cpu, activate_address_space);
    }
}

// ─── Panic handler ────────────────────────────────────────────────────────────

#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    // Pick the UART MMIO alias for the regime we panicked in, so the panic
    // prints in BOTH the early-boot (pre-migration, low identity) and the
    // steady-state (post-migration, high half) windows — rather than silently
    // translation-faulting if the high alias is used before it is live. The
    // migration trampoline rebases `SP` into the high half, so
    // `sp >= KERNEL_HIGH_HALF_OFFSET` iff the kernel is running high (where the
    // low identity is gone and the high device alias is the only mapped UART);
    // below it we are still on the low identity stack and the physical base is
    // mapped.
    let sp: usize;
    // SAFETY: reading `SP` into a GPR is a side-effect-free register move; no
    // memory/stack/flags touched. Audit: UNSAFE-2026-0002.
    unsafe {
        core::arch::asm!("mov {}, sp", out(reg) sp, options(nostack, nomem, preserves_flags));
    }
    let uart_base = if sp >= KERNEL_HIGH_HALF_OFFSET {
        tyrne_hal::phys_to_kernel_va(PL011_UART_BASE)
    } else {
        PL011_UART_BASE
    };
    // SAFETY: constructing a fresh Pl011Uart in the panic path is best-effort
    // diagnostic output. Writes may interleave if the original instance is
    // still reachable — acceptable per the Console contract (ADR-0007). The
    // base is the regime-correct alias selected above. Audit: UNSAFE-2026-0002.
    let console = unsafe { Pl011Uart::new(uart_base) };

    console.write_bytes(b"\n!! tyrne panic !!\n");
    let mut w = FmtWriter(&console);
    let _ = writeln!(w, "{info}");

    loop {
        core::hint::spin_loop();
    }
}
