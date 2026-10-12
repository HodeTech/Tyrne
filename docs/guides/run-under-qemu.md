# Run Tyrne under QEMU

Build and boot Tyrne on QEMU's `virt` AArch64 machine. This guide is for contributors verifying the kernel and its embedded EL0 hello task from a checkout.

## Goal

Boot the single-core debug kernel, observe the userspace greeting, task exit and scheduler completion, then return to the shell.

## Prerequisites

- A checkout of this repository and a Unix-like host; run the commands below from the repository root.
- Rustup with network access for the pinned toolchain and components in [`rust-toolchain.toml`](../../rust-toolchain.toml). The first Cargo invocation installs them, including the bare-metal target and LLVM tools used by the userland build.
- QEMU with AArch64 system support. On macOS:

  ```sh
  brew install qemu
  ```

  On Debian / Ubuntu:

  ```sh
  sudo apt install qemu-system-arm
  ```

  Verify:

  ```sh
  qemu-system-aarch64 --version
  ```

- For automated smoke runs, either coreutils `timeout` (normally present on Linux) or Perl (present on macOS).

## Steps

1. **Install the pinned toolchain** by running Cargo from the checkout.

   ```sh
   cargo --version
   ```

2. **Build userland, then the kernel.** The BSP embeds `userland/hello/hello.bin`; it must exist before the kernel build. Always rebuild userland for the matching profile before rebuilding the kernel, including when switching profiles.

   ```sh
   tools/build-userland.sh
   cargo kernel-build
   ```

   The ELF is `target/aarch64-unknown-none/debug/tyrne-bsp-qemu-virt`.

3. **Boot interactively** with the shell helper or Cargo alias.

   ```sh
   tools/run-qemu.sh
   ```

   ```sh
   cargo kernel-run
   ```

   Both default to one core. The equivalent manual command keeps that supported default:

   ```sh
   qemu-system-aarch64 \
       -M virt \
       -cpu cortex-a72 \
       -m 128M \
       -smp 1 \
       -nographic \
       -serial mon:stdio \
       -kernel target/aarch64-unknown-none/debug/tyrne-bsp-qemu-virt
   ```

4. **Exit QEMU** after the completion marker: press `Ctrl-A`, then `x`. Alternatively, press `Ctrl-A`, then `c` to enter the monitor and type `quit`. The completed demo continues spinning in task A and does not exit QEMU itself.

### Automated smoke and release builds

To build and run the optimized profile through Cargo, build its matching userland first:

```sh
tools/build-userland.sh --release
cargo kernel-build-release
cargo kernel-run-release
```

The release ELF is `target/aarch64-unknown-none/release/tyrne-bsp-qemu-virt`. Restore the debug userland with `tools/build-userland.sh` before returning to a debug kernel or perf-bench build.

For a bounded run that builds both images first, captures the trace and checks the debug EL0 markers and fault classes:

```sh
tools/smoke.sh --int --timeout 5
```

The command prints its trace path and exits after the budget; a timeout after successful completion is expected. An explicit ELF path skips both builds. Increase the budget on a slower host.

For an interactive release build, use matching userland and kernel profiles:

```sh
tools/build-userland.sh --release
cargo kernel-build --release
tools/run-qemu.sh --release
```

The current release syscall gate rejects the debug console call, so the release trace has no userspace greeting; it still has task exit and completion. Rebuild debug userland before returning to a debug kernel build.

### Core count

Both shell helpers accept `--smp N` and the `QEMU_SMP` environment default. Precedence is the last `--smp N`, then `QEMU_SMP`, then `1`. A count must be a positive integer; empty, zero, negative and non-numeric values exit 2 with usage. A valid flag overrides even an invalid environment default. Missing `--smp` or `--timeout` values also exit 2 with a flag-specific message.

```sh
QEMU_SMP=1 tools/run-qemu.sh --smp 1
tools/smoke.sh --smp 1 --timeout 5
```

**N > 1 is unsupported by the current kernel.** These options prepare tooling for Phase C; today's boot assembly has no secondary-core park guard or SMP bring-up. CI and normal smoke verification use one core. Passing a larger value is not evidence that multiple cores work.

Cargo's static runner in [`.cargo/config.toml`](../../.cargo/config.toml) remains at one core. Override it explicitly to use the shell helper, which receives Cargo's ELF path:

```sh
CARGO_TARGET_AARCH64_UNKNOWN_NONE_RUNNER="tools/run-qemu.sh --smp 1" cargo kernel-run
```

To verify the override without launching QEMU:

```sh
CARGO_TARGET_AARCH64_UNKNOWN_NONE_RUNNER=echo cargo kernel-run
```

This prints the kernel ELF path. Use a relative path starting with `./` if an ELF filename begins with `--`.

## Verifying it worked

Among the debug boot messages, expect these markers in order:

```text
hello from userspace
tyrne: userspace task exited
tyrne: all tasks complete
```

The real EL0 task makes two expected SVC exceptions (console and exit); these are not CPU faults. No panic, translation/permission fault, data/prefetch abort or unallocated instruction should appear. The smoke script requires all three exact debug marker lines and rejects panic/fault patterns. Release requires exit/completion and forbids the greeting; an explicit release ELF needs `--release` to select that contract. The `QEMU debug + release smoke (nightly)` CI job runs both profiles with `--int` and uploads traces, including failures; see [CI guide](ci.md#guest-smoke-and-diagnostic-artifacts). It does not assert an exact SVC count or exit code.

Run the argument regression checks without QEMU or a build:

```sh
tools/test-qemu-tooling.sh
```

They use a stub to verify argument handling, not guest runtime or SMP support. Run `tools/test-smoke-gates.sh` for profile/fault trace fixtures, or add `--real` for three private kernel rejection probes; see the [CI guide](ci.md#guest-smoke-and-diagnostic-artifacts) for prerequisites and retained evidence.

## Troubleshooting

**The BSP reports a missing userland image.** Run the matching-profile userland build before the kernel build, as in step 2.

**LLVM tools or the bare-metal target are missing.** Restore the components on the repository's pinned nightly:

```sh
rustup component add llvm-tools-preview
rustup target add aarch64-unknown-none
```

**The kernel hangs silently.** Capture exception details with the interactive helper, or use the bounded smoke run:

```sh
tools/run-qemu.sh --int-log
tools/smoke.sh --int --timeout 20
```

The helper prints the exception-log path. Inspect it for unexpected fault classes; use one core and verify that the userland and kernel profiles match.

**The kernel ELF is missing.** Run the two builds in step 2. The interactive helper runs an existing ELF; it does not build one.

## References

- [Boot architecture](../architecture/boot.md) and [HAL architecture](../architecture/hal.md).
- [ADR-0012: QEMU boot flow](../decisions/0012-boot-flow-qemu-virt.md).
- [ADR-0039: Userland build pipeline](../decisions/0039-userland-build-pipeline.md).
- [Phase C: SMP and preemption](../roadmap/phases/phase-c.md).
- [QEMU `virt` machine documentation](https://qemu.readthedocs.io/en/latest/system/arm/virt.html).
