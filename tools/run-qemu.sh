#!/usr/bin/env bash
# Run the Tyrne kernel under QEMU virt aarch64.
#
# Usage:
#   tools/run-qemu.sh                                         — debug build
#   tools/run-qemu.sh --release                               — release build
#   tools/run-qemu.sh --int-log                               — log exceptions (PID-suffixed temp file)
#   tools/run-qemu.sh <path/to/elf>                           — explicit ELF path
#   tools/run-qemu.sh -h | --help                             — show this usage
#
# --int-log adds `-d int -D <logfile>` to the QEMU invocation, where
# <logfile> is ${TMPDIR:-/tmp}/qemu_int.<pid>.log (printed at startup).
# Use it when the kernel hangs silently to see what exception fired.
# After the run: grep "Taking exception" <logfile>
#
# See docs/guides/run-under-qemu.md for the full walkthrough and the
# manual invocation used under the hood. The QEMU invocation below is
# kept in sync with the `runner` line in .cargo/config.toml.

set -euo pipefail

BUILD_PROFILE="debug"
KERNEL=""
INT_LOG=""

usage() {
    # Echo the usage block above (lines after the shebang up to the first
    # blank line), stripping the leading "# ".
    sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//' >&2
}

for arg in "$@"; do
    case "$arg" in
        --release)
            BUILD_PROFILE="release"
            ;;
        --int-log)
            INT_LOG="yes"
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --*)
            echo "error: unknown flag: $arg" >&2
            usage
            exit 2
            ;;
        *)
            if [[ -n "$KERNEL" ]]; then
                echo "error: unexpected extra argument: $arg" >&2
                echo "       (the kernel path was already set to: $KERNEL)" >&2
                usage
                exit 2
            fi
            KERNEL="$arg"
            ;;
    esac
done

if [[ -z "$KERNEL" ]]; then
    KERNEL="target/aarch64-unknown-none/${BUILD_PROFILE}/tyrne-bsp-qemu-virt"
fi

if [[ ! -f "$KERNEL" ]]; then
    echo "error: kernel image not found at $KERNEL" >&2
    echo "hint: run 'cargo kernel-build' first (or 'cargo build --release --target aarch64-unknown-none -p tyrne-bsp-qemu-virt' for release)" >&2
    exit 1
fi

if ! command -v qemu-system-aarch64 >/dev/null 2>&1; then
    echo "error: qemu-system-aarch64 not found in PATH" >&2
    echo "hint (macOS): brew install qemu" >&2
    echo "hint (Debian/Ubuntu): sudo apt install qemu-system-arm" >&2
    exit 1
fi

INT_LOG_FLAGS=()
if [[ -n "$INT_LOG" ]]; then
    # PID-suffix the log so concurrent runs (or two users on a shared host)
    # do not clobber each other's exception traces. ${TMPDIR:-/tmp} honours a
    # per-user temp dir when one is set.
    INT_LOG_PATH="${TMPDIR:-/tmp}/qemu_int.$$.log"
    INT_LOG_FLAGS=(-d int -D "$INT_LOG_PATH")
    echo "exception log → ${INT_LOG_PATH}  (grep 'Taking exception' to inspect)" >&2
fi

exec qemu-system-aarch64 \
    -M virt \
    -cpu cortex-a72 \
    -m 128M \
    -smp 1 \
    -nographic \
    -serial mon:stdio \
    ${INT_LOG_FLAGS[@]+"${INT_LOG_FLAGS[@]}"} \
    -kernel "$KERNEL"
