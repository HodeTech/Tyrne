# Tyrne

[![CI](https://github.com/HodeTech/Tyrne/actions/workflows/ci.yml/badge.svg)](https://github.com/HodeTech/Tyrne/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![Status: pre-alpha](https://img.shields.io/badge/status-pre--alpha-orange.svg)

> A capability-based microkernel written in Rust, designed to scale from constrained smart-home devices to mobile-class hardware while carrying the same isolation and capability discipline to every tier.

Tyrne is built around a single idea: **no ambient authority**.
Kernel-mediated object operations are authorised by explicitly granted capabilities, and the kernel is designed to keep the trusted computing base auditable.
Userspace drivers, filesystems and network stacks are the target architecture. Today the QEMU BSP supplies privileged hardware drivers; the running workload is two EL1 demo tasks and one EL0 hello program.

The project is pre-alpha.
The kernel boots end-to-end on QEMU `virt` aarch64 today, runs a capability-gated IPC demo, and serves the first real userspace task in EL0 via a capability-gated syscall boundary.
Phase B is **complete** (closed 2026-06-01) — EL1/EL0 privilege separation, the capability-gated syscall ABI, per-task address spaces, and the first real userspace binary are all done.
Phase B.2 (consolidation and hardening: CI gates, correctness fixes, documentation catch-up — [ADR-0040](docs/decisions/0040-phase-b2-consolidation-bridge.md)) is the active phase; Phase C (multi-core) is next and opens when B.2 closes.

---

## Status at a glance

| Area | State |
|------|-------|
| Boot, console, scheduler | **Done** — QEMU `virt` aarch64 completes the cooperative IPC/EL0 demo, then Task A spins without yielding. |
| Capability tables + IPC | **Done** — `cap_copy` / `cap_derive` / `cap_revoke` / `cap_drop`; synchronous send/recv with rollback-on-deadlock. |
| Exception infrastructure + GIC v2 | **Done** — 16-entry vector table at `VBAR_EL1`, generic-timer IRQ wiring and idle WFI fallback; the default demo exercises neither timer IRQ delivery nor idle. |
| MMU activation + page-table walker | **Done** — temporary bootstrap identity mappings, high-half kernel `TTBR1_EL1`, and per-task `TTBR0_EL1`; typed `MapperFlush` discipline. |
| Physical Memory Manager | **Done** — bitmap allocator with zero-fill on `alloc_frame` and three-stage validation on `free_frame`. |
| Per-task `AddressSpace` kernel object | **Done** — cap-gated kernel APIs `cap_create_address_space` / `cap_map` / `cap_unmap`; not yet userspace syscalls. |
| Task loader (load half) | **Done** — `load_image` produces a `LoadedImage` describing a populated address space for a `.rodata`-resident raw-flat blob. |
| Syscall ABI + dispatcher | **Done** — Phase B5; `SVC` trap → panic-free dispatcher → typed `SyscallError`; four release syscalls plus debug-only capability-gated `console_write`; validated copy-from/to-user primitives. |
| First userspace task (EL0) | **Done** — Phase B6 (closed 2026-06-01); `userland/hello` runs in its own address space, attempts `console_write` through the real lower-EL `+0x400` vector (greeting in debug only), and exits via `task_exit`; per-page user-VA translation + per-task capability table in place. |
| Consolidation and hardening | **Active** — Phase B.2 ([ADR-0040](docs/decisions/0040-phase-b2-consolidation-bridge.md)); real CI gates (`--release`, userland clippy, QEMU smoke), correctness and robustness fixes, documentation catch-up; tasks in [`docs/analysis/tasks/phase-b2/`](docs/analysis/tasks/phase-b2/README.md). |
| Multi-core + preemption | **Next** (gated by B.2) — Phase C; secondary core bring-up (PSCI), per-core state, preemptive scheduling, cross-core IPC, multi-core TLB shootdown. |

The active task and its current state live in [`docs/roadmap/current.md`](docs/roadmap/current.md).
Full phase plans are under [`docs/roadmap/phases/`](docs/roadmap/phases/).

---

## What makes Tyrne different

**Capability discipline, end to end.**
Kernel-mediated IPC, debug-console access and address-space mutation require the corresponding capability; task yield/exit use the current task identity.
Capabilities are unforgeable kernel-held tokens with explicit per-table derivation trees; revocation cascades through descendants in that table. Cross-table transitivity is deferred in [ADR-0023](docs/decisions/0023-cross-table-capability-revocation-policy.md).
There is no equivalent of a UNIX root, an admin override, or an ambient `CAP_SYS_ADMIN`.
The discipline is documented in [ADR-0014](docs/decisions/0014-capability-representation.md) and surfaces in every wrapper — `cap_map(cap, …)`, `cap_create_address_space(parent_cap, …)`, etc.

**Microkernel by construction, not by branding.**
The kernel runs exclusively in privileged mode and contains five subsystems: capabilities, IPC, scheduling, memory management, and interrupt dispatch.
The target design puts drivers, filesystems and network stacks in userspace compartments; today hardware drivers remain in the privileged BSP — see [`docs/architecture/overview.md`](docs/architecture/overview.md) for the layer diagram.
Adding a feature does not enlarge the trusted computing base unless it strictly has to.

**Memory safety through Rust + audited `unsafe`.**
All kernel, HAL, and userspace code is Rust.
Every `unsafe` block carries a SAFETY comment explaining (a) why it is needed, (b) the invariants it upholds, and (c) why safer alternatives were rejected, and is tracked in [`docs/audits/unsafe-log.md`](docs/audits/unsafe-log.md) with a numbered ID, a reviewed-by line, and a status field.
The audit log is the source of truth for current `unsafe`. Illustrative kernel operations include PMM frame-zeroing, task-loader copying, the scheduler/IPC raw-pointer bridge, and validated copy-from/to-user byte moves ([UNSAFE-2026-0030](docs/audits/unsafe-log.md), [user-access implementation](kernel/src/syscall/user_access.rs)). `copy_from_user` serves console input; `copy_to_user` is a tested primitive without a v1 syscall caller.

**HAL separation as a hard architectural rule.**
Hardware-specific code lives behind a small set of traits — `Console`, `Cpu`, `Mmu`, `Timer`, `IrqController`, `ContextSwitch` — defined in the `tyrne-hal` crate.
Each Board Support Package implements those traits for one board.
Bringing up a new aarch64 SoC means writing a new BSP, not editing the kernel.

**Heterogeneous hardware as a stated goal.**
The same kernel is intended to scale from microcontroller-class smart-home devices to single-board computers and eventually to mobile-class SoCs.
Hardware tiers (below) make the level of support explicit per target.

**Documented decisions, append-only.**
Every non-trivial architectural choice is captured as an Architecture Decision Record under [`docs/decisions/`](docs/decisions/).
ADRs are append-only: corrections land as revision notes, supersessions write a new ADR.
See the [ADR index](docs/decisions/README.md) for the full list with each ADR's title, status, and date.

---

## Quick start

The primary development target is QEMU's `virt` machine.
From the repository root, build userland before the BSP, then run the debug image:

```sh
# 1. Generate hello.bin for the debug profile.
tools/build-userland.sh

# 2. Build the kernel image (aarch64-unknown-none), embedding hello.bin.
cargo kernel-build

# 3. Run it under QEMU; serial is multiplexed onto your terminal.
cargo kernel-run
```

You should see the debug serial lines below in this order. `...` elides build/host-dependent values; the [fresh T-050 trace](docs/analysis/reports/2026-10-13-t050-entry-document-verification.md) records the exact output.

```text
tyrne: hello from kernel_main
tyrne: mmu activated
tyrne: high-half active
tyrne: pmm initialized (... frames available; ... reserved)
tyrne: address-space-arena ready (... slots used; bootstrap AS root = ...)
tyrne: timer ready (... Hz, resolution ... ns)
tyrne: starting cooperative scheduler
tyrne: task B — waiting for IPC
tyrne: task A -- sending IPC
hello from userspace
tyrne: userspace task exited
tyrne: task B — received IPC (label=0xaaaa); replying
tyrne: task A — received reply (label=0xbbbb); done
tyrne: all tasks complete
tyrne: boot-to-end elapsed = ... ns
```

Exit QEMU with `Ctrl-A x`; Task A spins after completion. For a bounded exception-logged build/run use:

```sh
tools/smoke.sh --int
```

For release, use `tools/smoke.sh --release --int`, or build userland with `--release`, then `cargo kernel-build --release` and `tools/run-qemu.sh --release`. Release omits the debug-only greeting and still reaches exit/completion. Rebuild matching userland when switching profiles: both write the same ignored `hello.bin`.
Full prerequisites, troubleshooting, and a line-by-line trace breakdown live in [`docs/guides/run-under-qemu.md`](docs/guides/run-under-qemu.md).

**Host-side tests** (no QEMU required):

```sh
cargo host-test          # host-side test suite (kernel · HAL · test-HAL)
cargo host-clippy        # -D warnings
cargo kernel-clippy      # -D warnings (kernel crate's stricter lints)
cargo fmt --check
```

---

## Architecture at a glance

Three layers define the target design shown below. The kernel runs at EL1; userspace runs at EL0 via an `SVC` boundary with capability checks for object operations. Init, driver and service tasks in the diagram are planned; today the BSP hardware drivers run at EL1 and hello is the sole EL0 program.

```mermaid
flowchart TB
    subgraph Priv["EL1 — Privileged"]
        Kernel["Kernel<br/>capabilities · IPC · scheduler<br/>memory · interrupt dispatch"]
        HAL["HAL traits<br/>Console · Cpu · Mmu · Timer<br/>IrqController · ContextSwitch"]
        BSP["BSP<br/>(per-board concrete HAL impl)"]
        HW["Hardware<br/>CPU · MMU · GIC · UART · timer · MMIO"]
        Kernel --> HAL --> BSP --> HW
    end
    subgraph User["EL0 — Userspace"]
        Init["init task"]
        Drivers["Driver tasks<br/>(UART · block · net)"]
        Services["System services<br/>(log · fs · net · service manager)"]
        Apps["Applications"]
    end
    Kernel <-->|syscall + IPC| Init
    Kernel <-->|syscall + IPC| Drivers
    Drivers <-->|IPC| Services
    Services <-->|IPC| Apps
```

The kernel sees only the HAL trait surface.
The BSP supplies the concrete implementations (`QemuVirtMmu`, `Pl011Uart`, `QemuVirtGic`, etc.).
Hardware-specific assembly — the reset vector, the EL2→EL1 drop, the exception trampolines — lives in the BSP, never in the portable kernel crate.

For a deeper read, start with [`docs/architecture/overview.md`](docs/architecture/overview.md) and follow its cross-links.

---

## Hardware tiers

Tiers express intended support priority. QEMU `virt` is implemented; the other targets below are planned ports or longer-term goals.

| Tier | Target | Role |
|------|--------|------|
| 1 — primary dev | QEMU `virt`, aarch64 | First bring-up target; CI runs here |
| 2 — first real hardware | Raspberry Pi 4 (BCM2711, Cortex-A72) | Planned first port off emulation |
| 2 | Raspberry Pi 5 (BCM2712, Cortex-A76) | Planned follow-on after Pi 4 |
| 3 | NVIDIA Jetson Nano / Orin (aarch64 CPU only) | Exploratory — see Jetson caveat below |
| 3 | RISC-V embedded SoCs (e.g. ESP32-C3/C6, SiFive) | Roadmap — smart-home class |
| 4 | Mobile-class aarch64 SoCs | Long-term vision |

**Jetson caveat.**
Jetson devices are aarch64, so their CPU side is portable.
Their GPU and Tensor cores require proprietary NVIDIA userspace blobs with no open-source driver.
Tyrne rejects proprietary kernel-adjacent blobs on principle, so Jetson will be supported only as a plain aarch64 board; on-device AI acceleration on Jetson is explicitly out of scope.
Projects that need open NPU acceleration should target Rockchip NPUs, Hailo, or Google Coral instead.
See [ADR-0004](docs/decisions/0004-target-platforms.md).

**No proprietary blobs** is a non-negotiable design rule for everything that touches the kernel or its image.
It is one of seven rules listed at the top of [`CLAUDE.md`](CLAUDE.md).

---

## Repository layout

```text
.
├── kernel/             tyrne-kernel — capability tables, IPC, scheduler,
│                       memory management, kernel objects (Task, Endpoint,
│                       Notification, AddressSpace), task loader.
├── hal/                tyrne-hal — portable trait surface:
│                       Console, Cpu, ContextSwitch, Mmu, Timer, IrqController,
│                       plus pure encoder helpers (VMSAv8 page-table format,
│                       timer tick arithmetic).
├── test-hal/           tyrne-test-hal — in-tree FakeMmu, VecFrameProvider,
│                       FakeCpu, etc. Host-test only; never linked into
│                       a kernel image.
├── bsp-qemu-virt/      tyrne-bsp-qemu-virt — primary dev BSP:
│                       boot.s + vectors.s, EL2→EL1 drop, MMU bootstrap,
│                       PL011 UART driver, GIC v2 driver, kernel_entry
│                       wiring up every subsystem in order.
├── userland/
│   ├── tyrne-user/      Safe syscall wrappers and audited bare-metal SVC shim.
│   └── hello/           First EL0 program; build-userland.sh generates hello.bin.
├── tools/              Developer helpers (userland build, QEMU smoke, perf harness).
├── docs/
│   ├── architecture/   System design chapters (overview · boot · scheduler
│   │                   · IPC · HAL · memory-management · task-loader
│   │                   · exceptions · security-model).
│   ├── decisions/      Architecture Decision Records (MADR-style, append-only).
│   ├── guides/         How-to guides (run-under-qemu, two-task-demo, first-userspace, ci).
│   ├── standards/      Coding, documentation, review, and security standards.
│   ├── audits/         unsafe-log.md — every audited unsafe block.
│   ├── analysis/       Per-task user stories, business / security /
│   │                   performance reviews, and reports.
│   ├── roadmap/        Phase plans + current focus.
│   └── glossary.md
├── .agents/            Procedure library shared by all AI agents that
│                       work in this repo (skills/<slug>/SKILL.md format).
├── CLAUDE.md           Entry point for Claude-based agents.
├── AGENTS.md           Entry point for all AI agents.
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE             Apache-2.0.
└── NOTICE
```

Six Rust workspace members: kernel, HAL, test-HAL, the QEMU BSP and two userland crates. Three default host members are kernel/HAL/test-HAL. The initial split is [ADR-0006](docs/decisions/0006-workspace-layout.md); the userland pipeline is [ADR-0039](docs/decisions/0039-userland-build-pipeline.md).

---

## Documentation map

The repo is documentation-first.
Three reading orders depending on what you need.

**Reader who wants the design.**
Start at [`docs/architecture/overview.md`](docs/architecture/overview.md), then follow its cross-links to the chapter on the subsystem you care about ([boot](docs/architecture/boot.md), [scheduler](docs/architecture/scheduler.md), [IPC](docs/architecture/ipc.md), [memory-management](docs/architecture/memory-management.md), [task-loader](docs/architecture/task-loader.md), [HAL](docs/architecture/hal.md), [exceptions](docs/architecture/exceptions.md), [security-model](docs/architecture/security-model.md)).
Each chapter cites the ADRs it synthesises; the ADR is authoritative when they disagree.

**Reader who wants the *why*.**
Read [`docs/decisions/`](docs/decisions/) in numeric order.
The first dozen ADRs establish the project's design language; the rest apply that language to specific subsystems.
The index in [`docs/decisions/README.md`](docs/decisions/README.md) lists every ADR with title, status, and date.

**Reader who wants to do something concrete.**

- [`docs/guides/run-under-qemu.md`](docs/guides/run-under-qemu.md) — boot the kernel under QEMU.
- [`docs/guides/two-task-demo.md`](docs/guides/two-task-demo.md) — annotated trace of the IPC demo.
- [`docs/guides/first-userspace.md`](docs/guides/first-userspace.md) — build and inspect the first EL0 task, syscall return and exit.
- [`docs/guides/ci.md`](docs/guides/ci.md) — what the CI pipeline runs and why.
- [`docs/standards/`](docs/standards/) — coding, documentation, review, and security disciplines that every change is held to.
- [`docs/glossary.md`](docs/glossary.md) — project-specific terminology.

**Reader who wants to track progress.**
[`docs/roadmap/current.md`](docs/roadmap/current.md) is the single source of truth for what is active right now, what just closed, and what is next.
Full phase plans live alongside it in [`docs/roadmap/phases/`](docs/roadmap/phases/).

---

## Engineering disciplines

A short, opinionated list of the rules every change is held to.
The long-form list is in [`CLAUDE.md`](CLAUDE.md) and the standards under [`docs/standards/`](docs/standards/).

- **Security-first.** When in doubt, choose the more conservative option. Never weaken a capability check, never introduce ambient authority, never suppress a failing security test.
- **Audited `unsafe`.** Every `unsafe` block has an audit-log entry with an Operation / Invariants / Rejected-alternatives section, a reviewer line, and a status field. The kernel crate denies `clippy::panic`, `clippy::unwrap_used`, `clippy::expect_used`, and `clippy::arithmetic_side_effects`.
- **ADR-first for non-trivial decisions.** No "we'll write it down later". Significant architectural / security / process decisions land as an ADR before the code that implements them.
- **English in the repository.** Source, comments, doc-comments, commit messages, PR descriptions, issue text — all English.
- **Mermaid for diagrams.** No PNG / SVG / ASCII-art for architectural illustrations.
- **No proprietary blobs in the kernel image.** Stated rule, not aspirational.
- **Methodical, phased progress.** Non-trivial work is proposed as a phase plan, executed one phase at a time, and reviewed between phases. The pre-alpha pace is deliberate.

---

## Contributing

Tyrne is in early bring-up.
External code contributions are not yet being accepted while the foundational documents and the kernel's core surface are still being written; accepting code PRs too early would fragment the design.
Issues, references, prior-art suggestions, and review of the published ADRs are very welcome.
See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the current contribution channels.

If you have a security-relevant observation, follow the disclosure process in [`SECURITY.md`](SECURITY.md).

---

## Naming

*Tyrne* is a clean-slate invented identifier — no etymology, no guardian / shadow / perimeter motif, no shared trademark surface.
The name was selected in April 2026 after the project's previous working name (Umbrix) was retired for a registry conflict; the rename is recorded in the project's git history but is otherwise unremarkable.
Use *Tyrne* in writing; the verbal form rhymes with *Berne*.

---

## License

Tyrne is licensed under the [Apache License, Version 2.0](LICENSE).
Attribution requirements are in [`NOTICE`](NOTICE).
Contributions are accepted under the same license under the inbound-equals-outbound rule.
