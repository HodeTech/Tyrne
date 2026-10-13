# Run and understand the two-task IPC demo

Run the current QEMU demo and follow its capability-checked IPC exchange. The two privileged demo tasks originated in Phase A ([T-005](../analysis/tasks/phase-a/T-005-two-task-ipc-demo.md)); today's reference BSP also schedules the EL0 hello program between them.

**Refresh status:** In Progress — T-050; implementation-review rounds pending. **Verified:** 2026-10-13, source `75de2ba90e151bae33e14d2db4a8278837e7775d`; [fresh build/trace evidence](../analysis/reports/2026-10-13-t050-entry-document-verification.md).

## Goal

Build the matching userland/kernel profiles, observe B → A → EL0 hello/exit → B reply → A completion, and understand which capabilities and scheduler transitions the output exercises.

## Prerequisites

- A checkout with the pinned Rust toolchain, `aarch64-unknown-none`, `llvm-tools-preview`, and `qemu-system-aarch64`; follow [Run under QEMU](run-under-qemu.md#prerequisites).
- Run commands from the repository root. The BSP embeds `userland/hello/hello.bin`, so build userland before the BSP and match debug/release profiles.
- For bounded smoke runs, either `timeout` or Perl, as described in the [QEMU guide](run-under-qemu.md).

## Steps

1. **Build and run the debug demo.** The first command creates the ignored raw userland image; the second embeds it in the kernel.

   ```sh
   tools/build-userland.sh
   cargo kernel-build
   cargo kernel-run
   ```

   Quit interactive QEMU with **Ctrl-A x** after completion. Task A spins permanently; successful completion does not exit QEMU.

2. **Run the bounded exception-logged smoke.** This entry point builds userland and the BSP in order, captures output, and checks the debug console/exit/completion contract.

   ```sh
   tools/smoke.sh --int
   ```

   `--int` selects QEMU `-d int,unimp`: exception and unimplemented-operation logging, not an instruction trace. The PID-scoped raw-log path is printed at startup.

3. **Verify release separately.** Rebuild both artifacts with the same profile; release rejects debug console syscall number 5, so hello emits no greeting but still exits.

   ```sh
   tools/build-userland.sh --release
   cargo kernel-build --release
   tools/run-qemu.sh --release
   ```

   Or use the bounded integration entry point:

   ```sh
   tools/smoke.sh --release --int
   ```

   When returning to debug, rebuild debug userland before the debug BSP again: both profiles write the same `hello.bin` path.

## Verifying it worked

### Expected output

The debug serial sequence below was checked against the fresh trace. `...` replaces build-dependent counts, addresses, frequency/resolution and elapsed time; exception-log records are omitted here.

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

Release has the same ordering without `hello from userspace`. The smoke gate requires greeting in debug, forbids it in release, requires exit/completion, and rejects its listed panic/CPU-fault classes. Separately inspecting both fresh raw logs found exactly two EL0 SVCs per profile; the smoke script does not count SVCs.

### Execution trace

The FIFO starts with **[B, A, user]**; idle is registered separately as a fallback ([ADR-0026](../decisions/0026-idle-dispatch-fallback.md)).

1. **B blocks on receive.** B prints waiting and calls `ipc_recv_and_yield`; the endpoint becomes `RecvWaiting`. B is blocked and A is selected, leaving user ready.
2. **A delivers and yields.** A's send stages the message as `RecvComplete`, appends unblocked B behind user, then yields A to the queue tail. User is selected from [user, B, A].
3. **The EL0 task runs and exits.** Its console call greets only in debug. `task_exit` abandons its syscall frame and dispatches B; the exiting task is not re-enqueued.
4. **B collects and replies.** Receive collects the staged message and returns the endpoint to `Idle`. B sends its reply while A is ready rather than blocked: the endpoint becomes `SendPending`, and the send returns `Enqueued`. B explicitly yields so A can collect it.
5. **A completes and spins.** A resumes, collects the reply, prints reply/completion/timing, then spins without yielding. B's post-yield tail never resumes; idle is not reached in this demo.

### Capability setup and scope

The privileged BSP creates one endpoint and two separate capability tables, each holding a root `SEND | RECV` capability to that endpoint. The scheduler bridges check the calling table's `SEND` or `RECV` right, then resolve the endpoint through its arena. The demo does not transfer a capability with either message.

These EL1 task bodies pass BSP raw pointers through the audited [ADR-0021](../decisions/0021-raw-pointer-scheduler-ipc-bridge.md) bridge; they do not retain mutable references across a context switch. The old UNSAFE-2026-0012 aliasing approach was removed; current bridge operations are covered by [UNSAFE-2026-0014](../audits/unsafe-log.md). Capability checks in privileged demo code demonstrate the API path, not isolation from malicious EL1 code. The separate [EL0 guide](first-userspace.md) explains the user/kernel boundary.

The elapsed line measures from the `kernel_main_high` snapshot after MMU activation/high-half migration to Task A's completion tail. It excludes earlier boot work and is host/QEMU dependent; it is not an IPC latency benchmark. The timer/GIC infrastructure exists, but this demo arms no deadline. Its banner and startup message do not prove timer-IRQ delivery, preemption or idle WFI execution.

## Troubleshooting

- **Missing hello.bin:** build userland first, with the same profile as the BSP. A plain runner does not build either artifact.
- **No greeting in release:** expected; the debug console call returns `BadSyscallNumber`. Exit/completion must still appear.
- **Silent hang:** use the interactive runner's exception log, then inspect the exact path it prints after quitting QEMU:

  ```sh
  tools/run-qemu.sh --int-log
  grep 'Taking exception' '<path-printed-by-run-qemu>'
  ```

  This runner uses `-d int`; smoke's `--int` uses `-d int,unimp`. Consult the [BSP boot checklist](../standards/bsp-boot-checklist.md) for exception/stack/FP diagnostics.
- **A never receives the reply after a modification:** preserve B's explicit post-send yield in this cooperative demo; its send does not block automatically.

The symmetric endpoint rights and one-message pending capacity are demo constraints. The deferred [badge/reply-receive design](../decisions/0018-badge-scheme-and-reply-recv-deferral.md) is not implemented; server protocols can instead use separate endpoints or explicit protocol identity where appropriate. This guide does not prescribe a general server-security design.

## References

- [ADR-0017 — IPC primitive set](../decisions/0017-ipc-primitive-set.md)
- [ADR-0019 — Scheduler shape](../decisions/0019-scheduler-shape.md)
- [ADR-0020 — Context-switch contract](../decisions/0020-cpu-trait-v2-context-switch.md)
- [Scheduler/IPC architecture](../architecture/scheduler.md) and [IPC architecture](../architecture/ipc.md)
- [First userspace task](first-userspace.md)
- [Fresh T-050 verification](../analysis/reports/2026-10-13-t050-entry-document-verification.md)
