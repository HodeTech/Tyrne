# Run the first userspace task

Build and observe `userland/hello`, Tyrne's first real EL0 program. It runs in its own address space, attempts a capability-gated console syscall, then exits through the real lower-EL exception vector. This guide explains the current reference BSP's path and its limits.

**Refresh status:** In Progress — T-050; implementation-review rounds pending. **Verified:** 2026-10-13, source `75de2ba90e151bae33e14d2db4a8278837e7775d`; [fresh build/trace evidence](../analysis/reports/2026-10-13-t050-entry-document-verification.md).

## Goal

Run the debug and release EL0 smoke, distinguish a returning console syscall from non-returning task exit, and understand the mappings and capability checks exercised by the hello path.

## Prerequisites

- Follow the [QEMU guide prerequisites](run-under-qemu.md#prerequisites): pinned Rust, `aarch64-unknown-none`, `llvm-tools-preview`, and QEMU aarch64.
- Run commands from the repository root. Bounded smoke needs `timeout` or Perl.
- Build userland before the BSP, matching profiles. Its `build.rs` requires the generated, ignored `userland/hello/hello.bin` before compilation.

## Steps

1. **Build and run debug.** Smoke builds userland then the kernel and bounds the QEMU run:

   ```sh
   tools/smoke.sh --int
   ```

   Or run the same build prerequisites interactively:

   ```sh
   tools/build-userland.sh
   cargo kernel-build
   cargo kernel-run
   ```

   Quit interactive QEMU with **Ctrl-A x** after completion.

2. **Verify release.** Smoke chooses release for both builds and forbids the userspace greeting:

   ```sh
   tools/smoke.sh --release --int
   ```

   For an interactive release run:

   ```sh
   tools/build-userland.sh --release
   cargo kernel-build --release
   tools/run-qemu.sh --release
   ```

   Both profiles write the same `hello.bin`; rebuild matching userland before switching the BSP's profile. Plain kernel build/run aliases do not orchestrate userland.

3. **Inspect the printed raw-log path.** Smoke's `--int` enables QEMU `-d int,unimp` (exception and unimplemented-operation logging), not instruction tracing. Inspect the path printed by that run:

   ```sh
   grep -E 'Exception return|Taking exception|tyrne:|hello from userspace' '<path-printed-by-smoke>'
   ```

## Verifying it worked

Debug serial output includes, in this order, among the full [IPC demo trace](two-task-demo.md#expected-output):

```text
tyrne: task B — waiting for IPC
tyrne: task A -- sending IPC
hello from userspace
tyrne: userspace task exited
tyrne: task B — received IPC (label=0xaaaa); replying
tyrne: task A — received reply (label=0xbbbb); done
tyrne: all tasks complete
```

Release omits `hello from userspace`: syscall number 5 decodes to `BadSyscallNumber` when debug assertions are disabled. Hello ignores that result and calls exit. Both profiles must still reach exit/completion without the smoke gate's listed panic/CPU-fault classes.

The fresh debug exception log has this sequence; unrelated register records and variable PC values are elided:

```text
Exception return from AArch64 EL1 to AArch64 EL0 PC ...
Taking exception 2 [SVC] on CPU 0
...from EL0 to EL1
hello from userspace
Exception return from AArch64 EL1 to AArch64 EL0 PC ...
Taking exception 2 [SVC] on CPU 0
...from EL0 to EL1
tyrne: userspace task exited
```

The first ERET enters hello; the console SVC returns through the second ERET. The exit SVC **does not ERET back to the exiting task**: its handler frame is abandoned while dispatching the next task. Release follows the same two-SVC structure without the greeting. Manual inspection of both fresh raw logs counted exactly two EL0 SVCs and no other exception class; the smoke script itself checks markers/fault patterns rather than counting SVCs. This successful path does not exhaustively prove isolation against hostile inputs.

### Program and build pipeline

The bare-metal entry excerpt from [hello's source](../../userland/hello/src/main.rs) is:

```rust
use tyrne_user::{console_write, task_exit, HELLO_CONSOLE_CAP};

static GREETING: &[u8] = b"hello from userspace\n";

#[no_mangle]
#[link_section = ".text._start"]
pub extern "C" fn _start() -> ! {
    let _ = console_write(HELLO_CONSOLE_CAP, GREETING);
    task_exit(0)
}
```

The source also supplies bare-metal conditional attributes, a panic handler and a host-tooling stub; the excerpt is not the complete program. [tyrne-user](../../userland/tyrne-user/src/lib.rs) provides safe wrappers around the audited SVC shim (`x8` number, `x0`–`x5` arguments). `HELLO_CONSOLE_CAP` is the generation-zero root handle at slot zero seeded by the BSP.

Per [ADR-0039](../decisions/0039-userland-build-pipeline.md), the build script compiles hello for `aarch64-unknown-none`, links with [hello.ld](../../userland/hello/hello.ld) at VA `0x0080_0000`, and runs the pinned toolchain's `rust-objcopy -O binary` to produce the raw-flat image. The image forbids writable `.data`/`.bss`; its greeting is read-only in-image data. The BSP embeds the generated bytes through `include_bytes!`. The two userland crates are workspace members outside the three default host members; plain default host commands skip them, while explicit workspace commands can compile their host stubs.

### Boot wire-up and exit

At boot, the [reference BSP](../../bsp-qemu-virt/src/main.rs):

1. Loads the raw image and stack into a fresh address space through `load_image`, producing `LoadedImage`.
2. Creates a task through `task_create_from_image` and seeds its own table with a `DebugConsole` / `CONSOLE_WRITE` capability at the hello handle.
3. Enqueues it through `add_user_task`, binding address-space/table handles, the image/stack window and a per-task kernel `SP_EL1` stack.
4. Activates the task's `TTBR0_EL1`, clears `EPD0`, and uses the one-shot `enter_el0` trampoline to ERET with scrubbed EL0-visible registers.
5. Dispatches console input through the lower-EL synchronous `VBAR_EL1+0x400` vector and the task's own capability table/address-space translation.
6. Handles exit with the unsafe module-level free function `tyrne_kernel::sched::task_exit_current`, which selects another task and never returns to the exiting one. It is not a `Scheduler` method or resource destructor.

The exit code is currently ignored. Exit stops scheduling this task but does not free its task slot, address space or capability table, and does not install a terminal task state. These existing lifecycle limits remain tracked by SEC-T024-01 / SEC-T028-01; no new lifecycle decision is implied here.

### Mapping and boundary checks

| Current mechanism | Meaning and limit |
|-------------------|-------------------|
| Per-page user-VA translation and `USER` check | Console input is read through the task's mappings; kernel pointers are not accepted as user buffers. Host adversarial tests supplement the successful EL0 path. |
| EL0 entry scrub and per-task `SP_EL1` | Initializes the user context and the stack used on a lower-EL trap. The smoke exercises entry/return, not every register-leak or stack-exhaustion scenario. |
| Per-task capability table | Resolves console authority in the calling task's table, with `DebugConsole` kind and `CONSOLE_WRITE` right checks. |

`AP` controls data-access permission; `UXN` blocks EL0 instruction fetch; `PXN` blocks privileged instruction fetch. They have different roles. Current high-half RAM uses `AP=00`, `UXN=1`, `PXN=0`: EL0 has no data access or execution there, but the privileged RAM window remains executable. Device mappings use `AP=00` and both execute-never bits set. The user image uses `AP=11`, `UXN=0`, `PXN=1`; its writable stack uses `AP=01` with both execute-never bits set. See the [descriptor encoder](../../hal/src/mmu/vmsav8.rs), [ADR-0033](../decisions/0033-kernel-high-half-migration.md) and [memory architecture](../architecture/memory-management.md).

Separate kernel-image/physmap permissions and full per-section W^X are future work (reserved ADR-0034). The original [EL0 security review](../analysis/reviews/security-reviews/2026-06-01-T-028-el0-userspace-wireup.md) retains its historical Approve verdict; this guide's smoke result is not a new adversarial security certification. Non-SVC EL0 faults currently reach the BSP panic path, so per-task fault containment is not complete.

## Troubleshooting

- **hello.bin missing:** run the matching-profile userland build first; the kernel aliases alone do not generate it.
- **No release greeting:** expected. Investigate missing exit/completion instead.
- **QEMU remains running after completion:** Task A spins and never yields; bounded smoke terminates QEMU after its timeout, then judges the captured markers/fault classes. Interactive runs need Ctrl-A x. Idle/timer-IRQ delivery is not exercised by this default path.
- **Silent fault or unexpected exception:** inspect the exact PID-scoped log path printed by the runner, then use the [BSP boot checklist](../standards/bsp-boot-checklist.md). Do not treat host tests as a substitute for EL0 smoke.

## References

- [ADR-0029 — Raw-flat userspace image](../decisions/0029-initial-userspace-image-format.md)
- [ADR-0030 — Syscall ABI](../decisions/0030-syscall-abi.md) and [ADR-0031 — Initial syscall set](../decisions/0031-initial-syscall-set.md)
- [ADR-0033 — Kernel high-half](../decisions/0033-kernel-high-half-migration.md)
- [ADR-0037 — EL0 entry context](../decisions/0037-el0-entry-context.md)
- [ADR-0039 — Userland build pipeline](../decisions/0039-userland-build-pipeline.md)
- [Task-loader architecture](../architecture/task-loader.md)
- [Two-task IPC demo](two-task-demo.md)
- [Fresh T-050 verification](../analysis/reports/2026-10-13-t050-entry-document-verification.md)
