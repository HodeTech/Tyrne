# Security policy

Tyrne is a security-oriented operating system project. Even while it is in pre-alpha, we want to handle security observations carefully.

## Project status and guarantees

Tyrne is **pre-alpha**: no production use is supported and no security guarantees are made for the current tree. Phase B closed on 2026-06-01. The kernel boots on QEMU `virt` aarch64 and runs its first EL0 userspace task. Phase B.2 is the active consolidation bridge; Phase C is next and gated on B.2 completion. See [current focus](docs/roadmap/current.md) for active work and the [security model](docs/architecture/security-model.md) for the architectural threat model; design goals there must be distinguished from the implementation limits below.

## Current EL0 boundary and limits

The v1 ABI defines five calls ([ADR-0030](docs/decisions/0030-syscall-abi.md), [ADR-0031](docs/decisions/0031-initial-syscall-set.md)):

| Number | Call | Authority and availability |
|--------|------|----------------------------|
| 1 | `ipc_send` | Endpoint capability with `SEND`. |
| 2 | `ipc_recv` | Endpoint capability with `RECV`. |
| 3 | `task_yield` | Acts on the current caller's own task; no capability argument. |
| 4 | `task_exit` | Terminates scheduling of the current caller; does not return; no capability argument. |
| 5 | `console_write` | `DebugConsole` capability with `CONSOLE_WRITE`; available only when `debug_assertions` is enabled. |

In a normal release build, only calls 1–4 are recognized. For number 5, [`SyscallNumber::decode`](kernel/src/syscall/abi.rs) returns `None` and the [dispatcher](kernel/src/syscall/dispatch.rs) returns `BadSyscallNumber` before capability lookup or console output, even if the caller holds a debug-console capability. In debug builds the console capability is checked before buffer access/output; the buffer's range and user-accessible page mappings are validated before output.

Kernel APIs for capability management, notifications and address spaces exist, but **none is exposed as an EL0 syscall in v1**. The ABI is not a claim that every kernel service is available to userspace.

The current demonstration has explicit limits:

- The [QEMU BSP](bsp-qemu-virt/src/main.rs) embeds a trusted `userland/hello` image and loads it through the [task loader](kernel/src/obj/task_loader.rs). This is not a supported arbitrary-untrusted-image loading service.
- A non-`SVC` EL0 synchronous fault follows the [vector panic path](bsp-qemu-virt/src/vectors.s) and panics the whole kernel. Per-task fault containment and supervisor notification are not implemented; syscall argument validation does not provide that execution-time containment.
- [`task_exit_current`](kernel/src/sched/mod.rs) stops scheduling the caller but does not reclaim its task slot, address space or capability table. Object destruction and resource reclamation remain future work.

These limits are also recorded in the [Phase B seam review](docs/analysis/reviews/security-reviews/2026-06-01-phase-b-closure.md). They preclude treating the demonstration as an availability or resource-isolation guarantee for hostile workloads.

## Reporting a security issue

Until a dedicated disclosure channel is set up, please report security-relevant observations by opening a **private security advisory** on GitHub:

https://github.com/HodeTech/Tyrne/security/advisories/new

Do not open a public issue for anything that looks like it might be security-sensitive, even in this early phase.

Where possible, include:

- A description of the observation and the affected file(s), commit(s), or ADR(s).
- Reasoning about why it is a risk — the threat, the assumed attacker capability, the affected assets.
- A suggested mitigation, if you have one.

## Scope

Everything in the `Tyrne` repository is in scope. Third-party dependencies are reviewed upstream; reporters are encouraged to also notify the upstream project when the root cause lives there.

## Disclosure

Because there are no production deployments yet, the current policy is **fix first, disclose later**. As the project matures, this policy will be revised and published here with explicit timelines and coordination expectations.

## For AI agents

If during any code or document review an AI agent notices something that plausibly weakens a security property (a removed capability check, a new ambient authority, a silenced security test, an undocumented `unsafe` block, or a proprietary blob entering the tree), the agent should **stop, flag the observation to the maintainer, and not proceed with the change**.
