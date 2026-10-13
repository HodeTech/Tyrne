# Glossary

Terminology used throughout Tyrne. Entries are alphabetical, with the established `mmu_bootstrap` / `.boot_pt` sub-entry grouping kept together. If a term appears in documentation and is not obvious from general OS-development literacy, it should be listed here.

---

<a id="abi-application-binary-interface"></a>
**ABI (Application Binary Interface).** The contract between a compiled component and the environment it runs in: calling convention, register usage, structure layout, system call numbers. ABIs are what let a binary run on another binary's output without recompilation.

<a id="addressspace"></a>
**AddressSpace.** A kernel object wrapping a BSP MMU translation context for a task's mappings. Tyrne stores it in `AddressSpaceArena`, names it with a generation-tagged handle and exposes cap-gated kernel operations; these operations are not yet userspace syscalls. See [ADR-0028](decisions/0028-address-space-data-structure.md) and the [implementation](../kernel/src/mm/address_space.rs).

<a id="adr-architecture-decision-record"></a>
**ADR (Architecture Decision Record).** A dated, numbered document recording a non-trivial decision, the context, the alternatives considered, and the consequences. Stored under [decisions/](decisions/). Tyrne uses the MADR format.

<a id="ambient-authority"></a>
**Ambient authority.** The anti-pattern where a subject's power is determined by *who it is* or *where it runs*, rather than by capabilities it has been explicitly granted. Tyrne rejects ambient authority by design. See [ADR-0001](decisions/0001-microkernel-architecture.md).

<a id="arena"></a>
**Arena.** A fixed-capacity slot array backing one kernel-object kind, such as tasks, endpoints, notifications or address spaces. Per [ADR-0016](decisions/0016-kernel-object-storage.md), each kind has its own arena; allocation and release need no heap. See [Generation tag](#generation-tag) and [AddressSpace](#addressspace).

<a id="badge"></a>
**Badge.** A value attached to a capability in some capability systems so that a receiver can distinguish callers without trusting a message-supplied identity. In seL4, endpoint badges identify the sending capability. Tyrne has not implemented badges: [ADR-0018](decisions/0018-badge-scheme-and-reply-recv-deferral.md) defers their scheme and the combined reply/receive operation. See [Reply capability](#reply-capability).

<a id="bridge-phase"></a>
**Bridge phase.** A phase inserted between published phases using a dotted identifier so later phase letters stay stable. Tyrne's B.2 consolidation bridge sits between B and C and must close before C/D milestones open or implementation tasks leave `Draft`. Phase C planning, including Proposed ADRs and the readiness sweep, remains permitted. See [ADR-0040](decisions/0040-phase-b2-consolidation-bridge.md) and [Track](#track).

<a id="bsp-board-support-package"></a>
**BSP (Board Support Package).** The concrete implementation of HAL trait surfaces for a specific board. A BSP plugs into the kernel at build time and provides drivers for on-board peripherals.

<a id="capability"></a>
**Capability.** An unforgeable token, held by a subject (process, task, thread), that authorizes a specific operation on a specific object. In a capability-based system, *having the capability is the permission*; there is no separate access control list to consult.

<a id="capability-based-security"></a>
**Capability-based security.** A security model in which authority over an object comes from an explicitly granted, unforgeable capability. Holders can share authority through permitted copy, derivation and transfer operations; the model alone does not prevent a holder from disclosing authority it can transfer. Tyrne checks object rights for IPC and console operations; task yield/exit instead use the current task identity. See [ADR-0001](decisions/0001-microkernel-architecture.md) and [Capability rights](#capability-rights-caprights).

<a id="capability-rights-caprights"></a>
**Capability rights (CapRights).** The bit-flag set attached to a capability that narrows permitted operations. Tyrne currently defines `SEND`, `RECV`, `NOTIFY`, `DUPLICATE`, `DERIVE`, `REVOKE`, `TRANSFER` and `CONSOLE_WRITE`; `EMPTY` denotes no rights. See [ADR-0014](decisions/0014-capability-representation.md), [ADR-0031](decisions/0031-initial-syscall-set.md) and the [source constants](../kernel/src/cap/rights.rs).

<a id="capability-transfer"></a>
**Capability transfer.** An IPC operation that moves a capability from the sender's table into an endpoint's in-flight state, then installs it in the receiver's table when received. Send validates the endpoint, transfer right and queue before removing the capability; receive checks table capacity before consuming the pending state. A full receiver table leaves the transfer pending for retry. See [ADR-0017](decisions/0017-ipc-primitive-set.md) and [IPC implementation](../kernel/src/ipc/mod.rs).

<a id="cdt-capability-derivation-tree"></a>
**CDT (Capability Derivation Tree).** The parent/child tree of capabilities derived from one another via `cap_derive`. Revocation is transitive along this tree: revoking a parent revokes every descendant. In v1 the tree is per-table; cross-table transitivity is deferred per [ADR-0023](decisions/0023-cross-table-capability-revocation-policy.md) (Status: Deferred; conditions for reopening recorded in the placeholder body).

<a id="cntfrq-el0"></a>
**`CNTFRQ_EL0`.** The aarch64 system register reporting the Generic Timer counter frequency in Hz. BSPs read the firmware-supplied value instead of hard-coding a board frequency. Tyrne reads it when constructing `QemuVirtCpu`, caching the frequency and derived resolution; the verified QEMU configuration reports 62.5 MHz. See [ADR-0010](decisions/0010-timer-trait.md).

<a id="cntpct-el0"></a>
**`CNTPCT_EL0`.** The aarch64 system register exposing the Generic Timer's physical counter. Tyrne's QEMU timer implementation uses the virtual view, [CNTVCT_EL0](#cntvct-el0), for reads and the matching `CNTV_*` registers for deadline programming. See [ADR-0010](decisions/0010-timer-trait.md).

<a id="cntvct-el0"></a>
**`CNTVCT_EL0`.** The aarch64 system register exposing the Generic Timer's virtual counter, derived from the physical counter and its virtual offset. Tyrne uses it for `Timer::now_ns`, converting ticks with the cached frequency, and programs absolute deadlines through `CNTV_CVAL_EL0` / `CNTV_CTL_EL0`. See [ADR-0010](decisions/0010-timer-trait.md).

<a id="context-switch"></a>
**Context switch.** The operation of saving the CPU state of one task and loading another so that the second task runs. Cost and frequency of context switches are the classic trade-off driver between monolithic and microkernel designs. In Tyrne the primitive is [`ContextSwitch::context_switch`](../hal/src/context_switch.rs) per [ADR-0020](decisions/0020-cpu-trait-v2-context-switch.md).

<a id="cooperative-scheduling"></a>
**Cooperative scheduling.** A scheduling model in which running tasks give up the CPU by yielding, blocking or exiting rather than being preempted by a scheduler tick. Tyrne currently runs cooperatively on one core; preemption belongs to [Phase C](roadmap/phases/phase-c.md), after the mandatory B.2 exit gate.

<a id="el0-el1-exception-levels"></a>
**EL0 / EL1 (Exception Levels).** ARM aarch64 privilege levels. EL0 is unprivileged (userspace); EL1 is the kernel/OS level. A task runs application code at EL0 and traps into the kernel at EL1 via an `SVC` (syscall) or an exception/interrupt. Tyrne drops to EL1 at boot ([ADR-0024](decisions/0024-el-drop-policy.md)) and exposes the EL0→EL1 syscall boundary in Phase B5 ([ADR-0030](decisions/0030-syscall-abi.md)). The higher levels (EL2 hypervisor, EL3 secure monitor) are not used by the kernel. See also *Syscall*, *SVC*.

<a id="endpoint"></a>
**Endpoint.** In seL4-style IPC, a kernel object used to rendezvous senders and receivers. Possessing a capability to an endpoint is what grants the right to send or receive.

<a id="generation-tag"></a>
**Generation tag.** The counter stored alongside every arena slot that detects stale handles. When a slot is freed and reused, its generation increments; a handle carries the generation it was issued with, so lookup can distinguish "same slot, new object" from "same slot, same object". See [ADR-0016](decisions/0016-kernel-object-storage.md).

<a id="generic-timer-arm"></a>
**Generic Timer (ARM).** The aarch64 counter and comparator subsystem providing time reads and timer interrupts. Tyrne's [Timer trait](../hal/src/timer.rs) and [QEMU implementation](../bsp-qemu-virt/src/cpu.rs) support virtual-counter reads, one-shot absolute deadlines and cancellation, with GIC v2 virtual-timer PPI 27 wiring. Reported integer-nanosecond resolution rounds to nearest (minimum 1 ns); deadline conversion separately rounds upward to ticks to honor at-or-after timing. The default demo arms no deadline, so its timer banner does not demonstrate IRQ delivery or preemption. See [ADR-0010](decisions/0010-timer-trait.md).

<a id="hal-hardware-abstraction-layer"></a>
**HAL (Hardware Abstraction Layer).** The set of traits and types that decouple the kernel from any specific CPU or board. A BSP implements HAL traits; the kernel depends only on the traits.

<a id="handle-typed"></a>
**Handle (typed).** An opaque value identifying a kernel object, such as `TaskHandle`, `EndpointHandle`, `NotificationHandle` or `AddressSpaceHandle`. It carries a slot index and generation tag. A `CapHandle` is a different, also generation-tagged handle into a particular capability table, rather than an object-arena handle. See [ADR-0016](decisions/0016-kernel-object-storage.md) and [capability-table handles](../kernel/src/cap/table.rs).

<a id="hubris"></a>
**Hubris.** A Rust microkernel from Oxide Computer Company, designed for embedded management controllers. Emphasizes compile-time task definition, minimal runtime flexibility, strict memory isolation. A major inspiration for Tyrne.

<a id="ipc-inter-process-communication"></a>
**IPC (Inter-Process Communication).** The mechanism by which tasks in separate address spaces exchange data and capabilities. In microkernels IPC is the hot path and its design dominates performance.

<a id="kernel"></a>
**Kernel.** The trusted, privileged core of an operating system. Tyrne provides capabilities, scheduling, IPC, memory management and interrupt dispatch through portable kernel mechanisms and privileged BSP implementations. Userspace drivers and services are the target architecture; the current EL0 workload is the hello program. See [architecture/overview.md](architecture/overview.md).

<a id="madr-markdown-architectural-decision-records"></a>
**MADR (Markdown Architectural Decision Records).** A lightweight markdown template for ADRs, with explicit sections for decision drivers, considered options, and pros/cons. Tyrne uses a slightly simplified MADR; see [decisions/template.md](decisions/template.md).

<a id="mair-memory-attribute-indirection-register"></a>
**MAIR (Memory Attribute Indirection Register).** The aarch64 register (`MAIR_EL1`) holding memory-attribute encodings selected by each page descriptor's `AttrIndx`. Tyrne uses index 0 for device-nGnRnE and index 1 for normal memory with inner and outer write-back/write-allocate cacheability. Shareability is a separate descriptor field: current normal RAM is inner-shareable, and device mappings are non-shareable. See [ADR-0027](decisions/0027-kernel-virtual-memory-layout.md) and the [descriptor encoder](../hal/src/mmu/vmsav8.rs).

<a id="mapperflush"></a>
**MapperFlush.** A `#[must_use]` token returned by `Mmu::map` / `Mmu::unmap`, carrying the modified virtual address. `flush(mmu)` invalidates that address; `ignore()` records a deliberate omission, normally followed by bulk invalidation. The unused-result lint encourages explicit handling, but the token is `Copy` and can be explicitly discarded: it is not a linear proof of unique discharge or address-space identity. See [ADR-0027](decisions/0027-kernel-virtual-memory-layout.md), the [type](../hal/src/mmu/mod.rs) and [T-040](analysis/tasks/phase-b2/T-040-mapperflush-asid-discriminant.md). Inspired by the Rust x86_64 paging API.

<a id="microkernel"></a>
**Microkernel.** A kernel design that keeps privileged mechanisms small, typically covering address spaces, tasks, IPC and scheduling, while placing drivers and services in isolated userspace components. Tyrne follows this target design; current QEMU hardware drivers remain in the privileged BSP, and its first EL0 program is hello. See [ADR-0001](decisions/0001-microkernel-architecture.md).

<a id="miri"></a>
**Miri.** A Rust interpreter that detects undefined behavior on executed test paths, including violations of its pointer-aliasing model. Tyrne uses the pinned `cargo +nightly-2026-01-15 miri test --workspace --exclude tyrne-bsp-qemu-virt` command. The [fresh T-049 report](analysis/reports/2026-10-13-t049-miri-validation.md) records exercised host paths, warnings and exclusions; a passing run is not proof about all unsafe code, hardware or EL0 execution.

<a id="mmu-memory-management-unit"></a>
**MMU (Memory Management Unit).** Hardware that translates virtual addresses and enforces page permissions. Tyrne temporarily uses low identity mappings during bootstrap, then executes the kernel through high-half `TTBR1_EL1` and activates per-task address-space roots through `TTBR0_EL1`. See [ADR-0033](decisions/0033-kernel-high-half-migration.md) and [memory-management.md](architecture/memory-management.md).

<a id="mmu-bootstrap"></a>
**`mmu_bootstrap`.** The once-per-boot BSP function populating the four initial low-regime page-table frames and enabling translation/cache control at EL1. The separate `high_half_activate` step populates two more roots and migrates kernel execution to the high half. Bootstrap follows early console/vector setup and precedes the post-migration boot-timing snapshot; it is not the first MMIO operation. See the [source](../bsp-qemu-virt/src/mmu_bootstrap.rs), [ADR-0027](decisions/0027-kernel-virtual-memory-layout.md) and [ADR-0033](decisions/0033-kernel-high-half-migration.md).

<a id="boot-pt"></a>
**`.boot_pt`.** The established name for the statically reserved bootstrap-table range bracketed by `__boot_pt_start` / `__boot_pt_end` inside the linker's `.bss` output section. It contains six 4 KiB frames (24 KiB): four low-regime tables and two high-half roots sharing the existing L2 tables. Boot assembly zeroes the range with BSS before Rust initializes it; no allocator is needed at that point. It is not a separate output section in the current [linker script](../bsp-qemu-virt/linker.ld). See [memory-management.md](architecture/memory-management.md).

<a id="notification"></a>
**Notification.** A kernel object for asynchronous bit-OR signalling: callers accumulate bits in a 64-bit word through `ipc_notify`, guarded by `NOTIFY`. It carries no message body. Blocking notification wait/wake is not wired in the current IPC API. See [ADR-0017](decisions/0017-ipc-primitive-set.md).

<a id="pmm-physical-memory-manager"></a>
**PMM (Physical Memory Manager).** The kernel allocator for physical memory frames. Tyrne's bitmap PMM reserves boot/kernel ranges, zero-fills each returned 4 KiB frame and validates frees. Its current synchronization discipline is single-core, not SMP-safe. See [ADR-0035](decisions/0035-physical-memory-manager.md) and [PMM implementation](../kernel/src/mm/pmm.rs).

<a id="psci-power-state-coordination-interface"></a>
**PSCI (Power State Coordination Interface).** The ARM standard for boot, CPU-on/off, and system reset. On aarch64 QEMU `virt` and Raspberry Pi 4, PSCI is the portable way to bring secondary cores online.

<a id="qemu"></a>
**QEMU.** An open-source machine emulator and virtualizer. Tyrne primary development uses QEMU's aarch64 `virt` machine.

<a id="ready-queue"></a>
**Ready queue.** The scheduler's bounded FIFO of task handles that are runnable and waiting for the CPU. Tyrne's queue capacity equals the task arena capacity, so it can never refuse an enqueue when the total task count is within the limit. See [ADR-0019](decisions/0019-scheduler-shape.md).

<a id="rendezvous-ipc"></a>
**Rendezvous IPC.** An IPC model matching senders and receivers at an endpoint, borrowed from the L4 family. Tyrne v1 uses a bounded staged form: a send can leave one pending message, and receive can register a waiter or collect a staged delivery. Scheduler bridges handle blocking/yielding; the raw send/receive functions do not both block until a transfer completes. See [ADR-0017](decisions/0017-ipc-primitive-set.md) and [IPC architecture](architecture/ipc.md).

<a id="reply-capability"></a>
**Reply capability.** A capability mechanism in systems such as seL4 that grants a receiver authority to reply to a particular caller. Tyrne has no automatic single-use reply-capability mechanism today; [ADR-0018](decisions/0018-badge-scheme-and-reply-recv-deferral.md) defers the badge scheme and combined reply/receive design. The demo replies with its existing endpoint capability. See [Badge](#badge) and [Endpoint](#endpoint).

<a id="sel4"></a>
**seL4.** A formally verified microkernel in the L4 family. Its verified correctness and capability-based design are reference points for Tyrne, even though Tyrne is not aiming for full formal verification in its first years.

<a id="stacked-borrows"></a>
**Stacked Borrows.** A model of Rust pointer-aliasing rules used by Miri, tracking pointer tags and invalidation across accesses. Tyrne's raw-pointer scheduler/IPC bridge is designed to satisfy the model without keeping mutable references alive across context switches. See [ADR-0021](decisions/0021-raw-pointer-scheduler-ipc-bridge.md) and the [Miri report](analysis/reports/2026-10-13-t049-miri-validation.md).

<a id="staticcell"></a>
**StaticCell.** A BSP helper wrapping `UnsafeCell<MaybeUninit<T>>` for one-time initialization of static kernel state. The initialized contents can still be mutated through disciplined raw-pointer access; they are not immutable after boot. Current safety arguments assume single-core cooperative execution and no live mutable borrow across a switch. See the [implementation](../bsp-qemu-virt/src/main.rs) and [ADR-0021](decisions/0021-raw-pointer-scheduler-ipc-bridge.md).

<a id="svc-supervisor-call"></a>
**SVC (Supervisor Call).** The ARM aarch64 instruction a lower exception level uses to synchronously trap into a higher one. An `SVC` from EL0 takes the lower-EL synchronous exception vector at EL1; an `SVC` issued at EL1 takes the *current-EL* vector instead. Tyrne's syscall ABI uses `SVC #0` with the syscall number in `x8` ([ADR-0030](decisions/0030-syscall-abi.md)). See also *Syscall*, *EL0 / EL1*.

<a id="syscall-system-call"></a>
**Syscall (system call).** A synchronous entry from EL0 into the EL1 kernel through `SVC`. Tyrne v1 recognizes send, recv, task_yield and task_exit, plus debug-only console_write; release rejects console syscall number 5. IPC/console operations validate capabilities, while yield/exit require current-task identity. The dispatcher is panic-free for syscall inputs; non-SVC EL0 faults still reach the BSP panic path. task_exit does not return. See [ADR-0031](decisions/0031-initial-syscall-set.md) and [Syscall ABI](#syscall-abi).

<a id="syscall-abi"></a>
**Syscall ABI.** The register-level contract for a syscall: which register carries the syscall number (`x8`), which carry arguments (`x0`–`x5`), and how the status + payload return (`x0` = status word with `0` = `Ok`, `x1`–`x7` = payload). Fixed by [ADR-0030](decisions/0030-syscall-abi.md). A hardware-specific instance of an *ABI*.

<a id="tcb-trusted-computing-base"></a>
**TCB (Trusted Computing Base).** The components whose correctness is necessary for a system's security guarantees. Tyrne aims to keep that set small by isolating drivers and services in userspace; current QEMU UART/GIC/MMU/timer implementations and boot/syscall glue remain privileged BSP code alongside kernel/HAL mechanisms. The lone EL0 hello is not evidence that userspace driver/service isolation has shipped. See [security-model.md](architecture/security-model.md), [Microkernel](#microkernel) and [Trust boundary](#trust-boundary).

<a id="track"></a>
**Track.** A named sub-unit of a bridge phase. Phase B.2 uses B.2-1 through B.2-6, distinct from Phase B's B0–B6 milestones. See [ADR-0040](decisions/0040-phase-b2-consolidation-bridge.md) and [Bridge phase](#bridge-phase).

<a id="trust-boundary"></a>
**Trust boundary.** A line in the system at which assumptions about integrity, confidentiality, or availability change. Crossing a trust boundary should require an explicit capability check. Trust boundaries are drawn in [architecture/security-model.md](architecture/security-model.md).

<a id="unsafe-rust"></a>
**Unsafe (Rust).** A block of Rust code that opts out of some compiler-enforced invariants (e.g., to dereference raw pointers or call FFI). In Tyrne, every `unsafe` block is commented with justification (invariants, rejected alternatives, audit tag) per [`unsafe-policy.md`](standards/unsafe-policy.md), and tracked in the audit log.

<a id="unsafecell"></a>
**UnsafeCell.** Rust's primitive for interior mutability: a `&UnsafeCell<T>` is allowed to produce a `*mut T`. Tyrne's BSP uses `UnsafeCell` (usually inside a `StaticCell`) to hold kernel state in `static` storage without `static mut` aliasing hazards.

<a id="userspace"></a>
**Userspace.** Code executing outside the privileged kernel, at EL0 on Tyrne's current aarch64 target. The running userspace workload is `userland/hello`; userspace drivers, filesystems, networking and services are planned architectural components. See [first-userspace.md](guides/first-userspace.md) and [architecture/overview.md](architecture/overview.md).
