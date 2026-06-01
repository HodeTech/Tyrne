# Guide: First userspace task (B6)

Tyrne's first **real EL0 userspace program** — `userland/hello` — loaded at boot,
run in its own address space at exception level 0, greeting the console through a
capability-gated `console_write` syscall, and exiting cleanly via `task_exit`.
This is the milestone that closes Phase B: the kernel now runs untrusted user
code across the EL0↔EL1 privilege boundary.

## What it proves

The full userspace round-trip, end to end:

- A raw-flat userspace image (built from a Rust crate, not hand-coded bytes) is
  **loaded** into a fresh address space — image mapped `USER | EXECUTE`, stack
  `USER | WRITE` ([ADR-0029](../decisions/0029-initial-userspace-image-format.md),
  [task_loader](../../kernel/src/obj/task_loader.rs)).
- The task **runs in EL0** in its own `TTBR0_EL1` address space, dropped there by
  the one-shot `enter_el0` `ERET` trampoline with the EL0-visible register file
  scrubbed ([ADR-0037](../decisions/0037-el0-entry-context.md)).
- It makes a **`console_write` syscall over the lower-EL `VBAR_EL1+0x400`
  vector** — the real EL0→EL1 trap the B5 EL1-stub `+0x200` proxy could not prove.
- The kernel resolves the call against the task's **own** capability table
  (gate #3, [T-026](../analysis/tasks/phase-b/T-026-current-task-cap-table.md)),
  checks the `DebugConsole`/`CONSOLE_WRITE` capability, and **copies the buffer
  through the task's own address space** with a per-page `USER`-flag translation
  (gate #1, [T-025](../analysis/tasks/phase-b/T-025-user-access-translation.md)) —
  so a userspace pointer can never name kernel memory.
- The task **`task_exit`s**; the scheduler terminates it and dispatches the next.

The whole thing is **memory-isolated by construction**: the kernel lives high-half
in `TTBR1_EL1` (`UXN`/`PXN` from EL0), so the userspace `TTBR0` holds only the
task's image + stack and cannot reach kernel memory
([ADR-0033](../decisions/0033-kernel-high-half-migration.md)).

## How to run

```sh
# One command — builds the userland image, the kernel, and runs the smoke:
tools/smoke.sh --int            # debug build (the greeting is visible; see below)

# Or step by step:
tools/build-userland.sh         # cargo build userland/hello → rust-objcopy → hello.bin
cargo kernel-build              # embeds hello.bin via include_bytes!
cargo kernel-run                # boot under QEMU virt
```

> **Debug vs release:** `console_write` (syscall number 5) is **debug-gated**
> ([ADR-0031](../decisions/0031-initial-syscall-set.md)). In a **debug** build the
> greeting prints; in a **release** build the syscall returns `BadSyscallNumber`
> and emits nothing, but the EL0 task still runs the `+0x400` trap and exits.

## Expected output (debug)

Among the boot lines:

```text
tyrne: hello from kernel_main
...
hello from userspace
tyrne: userspace task exited
tyrne: all tasks complete
```

With `--int` (instruction/exception trace) the EL0 round-trip is visible:

```text
Exception return from AArch64 EL1 to AArch64 EL0 PC 0x800000   ← ERET into EL0 at the image entry
Taking exception 2 [SVC] on CPU 0  ...from EL0 to EL1          ← console_write SVC → the +0x400 vector
hello from userspace                                            ← gate #1 translated the buffer; dispatcher emitted
Exception return from AArch64 EL1 to AArch64 EL0 PC 0x800034    ← ERET back to EL0
Taking exception 2 [SVC] on CPU 0  ...from EL0 to EL1          ← task_exit SVC
tyrne: userspace task exited                                    ← the kernel reports termination
tyrne: all tasks complete
```

Exactly two EL0 `SVC` exceptions, each `ERET`ing cleanly; **no new fault class**.

## What the program does

[`userland/hello/src/main.rs`](../../userland/hello/src/main.rs) is a
`#![no_std] #![no_main]` AArch64 program whose entire body is:

```rust
#[no_mangle]
#[link_section = ".text._start"]   // placed at offset 0 of the raw-flat image
pub extern "C" fn _start() -> ! {
    let _ = console_write(HELLO_CONSOLE_CAP, b"hello from userspace\n");
    task_exit(0)
}
```

It links the [`tyrne-user`](../../userland/tyrne-user/src/lib.rs) crate, which
provides **safe wrappers** over the syscall ABI — each a thin `svc #0` shim
(`x8` = number, `x0`–`x5` = args, per
[ADR-0030](../decisions/0030-syscall-abi.md)). `HELLO_CONSOLE_CAP = 0` is the
handle of the task's root capability — the `DebugConsole` cap the kernel seeds
into the task's table at boot.

## How it's built (the pipeline)

Per [ADR-0039](../decisions/0039-userland-build-pipeline.md):

1. `cargo build -p tyrne-userland-hello --target aarch64-unknown-none` — a normal
   Rust build, linked by [`hello.ld`](../../userland/hello/hello.ld) which fixes
   the entry at offset 0 / VA `0x0080_0000` and forbids `.data`/`.bss` (the image
   is `USER|EXECUTE`, no `WRITE`).
2. `rust-objcopy -O binary` (from the pinned `llvm-tools-preview` — no Cargo
   dependency) strips the ELF to a **raw flat** byte stream → `hello.bin`.
3. The BSP embeds it via `include_bytes!`; its `build.rs` asserts the `.bin`
   exists (run `tools/build-userland.sh` first — `tools/smoke.sh` and CI do this
   automatically).

The userland crates are workspace members excluded from `default-members`, so the
host commands (`cargo test`, `cargo build`) skip them.

## How it runs (the wire-up)

At boot ([`bsp-qemu-virt/src/main.rs`](../../bsp-qemu-virt/src/main.rs)):

1. `load_image(USERSPACE_IMAGE, …)` maps the image + a stack into a fresh address
   space and returns a `LoadedImage`.
2. `task_create_from_image(…)` mints a runnable `Task` from it
   ([T-024](../analysis/tasks/phase-b/T-024-task-create-from-image.md)).
3. A `CapabilityTable` for the task is seeded with one `DebugConsole` /
   `CONSOLE_WRITE` capability at the root slot (handle `0` = `HELLO_CONSOLE_CAP`).
4. `add_user_task(…)` enqueues the task `Ready`, binding its address space,
   per-task `[entry, stack_top)` window, capability table, and a kernel
   `SP_EL1` stack.
5. The scheduler dispatches it: the activation hook installs the task's
   `TTBR0_EL1` and clears `EPD0`, then `enter_el0` `ERET`s into EL0.
6. On `task_exit`, `Scheduler::task_exit_current` drops the task and dispatches
   the next.

## The boundary (why this is safe)

Three gates make the EL0 syscall boundary safe (all proven at runtime here):

| Gate | What it stops | Where |
|------|---------------|-------|
| **#1** per-page user-VA translation + `USER` check | a confused-deputy passing a kernel VA to `console_write` | [T-025](../analysis/tasks/phase-b/T-025-user-access-translation.md) |
| **#2** EL0 entry context + register scrub + per-task `SP_EL1` | kernel state leaking into EL0; an EL0→EL1 trap on an uninitialised stack | [T-023](../analysis/tasks/phase-b/T-023-el0-entry-context.md) |
| **#3** per-task capability table | EL0 naming a capability it does not hold | [T-026](../analysis/tasks/phase-b/T-026-current-task-cap-table.md) |

Plus the high-half regime ([ADR-0033](../decisions/0033-kernel-high-half-migration.md)):
the kernel is absent from the task's `TTBR0` and `UXN`/`PXN`-protected in `TTBR1`,
so EL0 has no path to kernel memory or kernel execution.

The first attacker-observable EL0 boundary was security-reviewed at
[2026-06-01](../analysis/reviews/security-reviews/2026-06-01-T-028-el0-userspace-wireup.md)
(Approve; 0 confirmed exploitable defects).

## Known limitations (v1)

- **One EL0 task, code + read-only data only.** No `.data`/`.bss` (no writable
  globals outside the stack); per-section permissions are a future ADR-0034.
- **`console_write` is debug-gated** — absent from the release syscall surface.
- **No resource reclamation on exit.** A `task_exit`'d task's slot, address
  space, and capability table are not freed (the SEC-T028-01 / SEC-T024-01
  object-lifecycle gap) — inert in v1, closed by the successor lifecycle ADR.
- **Cooperative, single-core.** No preemption; tasks yield/exit explicitly.

## References

- [ADR-0029](../decisions/0029-initial-userspace-image-format.md) — raw-flat image format
- [ADR-0030](../decisions/0030-syscall-abi.md) / [ADR-0031](../decisions/0031-initial-syscall-set.md) — syscall ABI + v1 set
- [ADR-0033](../decisions/0033-kernel-high-half-migration.md) — high-half kernel
- [ADR-0037](../decisions/0037-el0-entry-context.md) — EL0 entry context
- [ADR-0039](../decisions/0039-userland-build-pipeline.md) — userland build pipeline
- [T-022](../analysis/tasks/phase-b/T-022-high-half-kernel-mapping.md) … [T-028](../analysis/tasks/phase-b/T-028-el0-userspace-wireup.md) — the B6 task arc
- [Two-task IPC demo](two-task-demo.md) — the kernel-task (EL1) cooperative demo this runs alongside
