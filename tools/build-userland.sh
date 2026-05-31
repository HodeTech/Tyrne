#!/usr/bin/env bash
# Build the Tyrne userland program(s) and strip to raw flat binaries (ADR-0039).
#
# Produces userland/hello/hello.bin (git-ignored via the repo's `*.bin` rule)
# by compiling the `tyrne-userland-hello` crate for aarch64-unknown-none and
# stripping it with `rust-objcopy -O binary` from the pinned `llvm-tools-preview`
# component (NO Cargo dependency — keeps the K3-8 cargo-vet flag unfired).
#
# Must run BEFORE `cargo kernel-build`: the BSP embeds the .bin via
# `include_bytes!`, and its build.rs panics if the .bin is absent. `tools/smoke.sh`
# and the CI kernel-build job both run this first.
#
# Usage:
#   tools/build-userland.sh            — debug profile (matches a debug kernel)
#   tools/build-userland.sh --release  — release profile (matches --release kernel)
set -euo pipefail

PROFILE="debug"
case "${1:-}" in
    --release) PROFILE="release"; shift ;;
    "") ;;
    -h|--help) sed -n '2,/^set -/p' "$0" | sed 's/^# \{0,1\}//;/^set -/d' >&2; exit 0 ;;
    *) echo "error: unknown argument: $1 (usage: $0 [--release])" >&2; exit 2 ;;
esac

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "build-userland: cargo build -p tyrne-userland-hello --target aarch64-unknown-none (${PROFILE})" >&2
if [[ "$PROFILE" == "release" ]]; then
    cargo build -p tyrne-userland-hello --target aarch64-unknown-none --release
else
    cargo build -p tyrne-userland-hello --target aarch64-unknown-none
fi

# Resolve rust-objcopy from the active toolchain's llvm-tools (no Cargo dep).
SYSROOT="$(rustc --print sysroot)"
OBJCOPY="$(find "$SYSROOT" -type f -name 'rust-objcopy' 2>/dev/null | head -n1)"
if [[ -z "$OBJCOPY" ]]; then
    echo "error: rust-objcopy not found under $SYSROOT" >&2
    echo "       install the llvm-tools-preview component (pinned in rust-toolchain.toml):" >&2
    echo "       rustup component add llvm-tools-preview" >&2
    exit 1
fi

ELF="target/aarch64-unknown-none/${PROFILE}/hello"
BIN="userland/hello/hello.bin"
if [[ ! -f "$ELF" ]]; then
    echo "error: expected userland ELF not found at $ELF" >&2
    exit 1
fi

"$OBJCOPY" -O binary "$ELF" "$BIN"
echo "build-userland: wrote $BIN ($(wc -c < "$BIN" | tr -d ' ') bytes)" >&2
