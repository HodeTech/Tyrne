#!/usr/bin/env bash
# Require both release-only console_write regression tests to execute and pass.
# Cargo alone exits successfully when cfg changes make the filters match nothing.
set -euo pipefail
[[ $# -eq 0 ]] || { echo "Usage: tools/check-release-tests.sh" >&2; exit 2; }
cd "$(dirname "$0")/.."
GATE_LOG="$(mktemp "${TMPDIR:-/tmp}/tyrne-release-tests.XXXXXX")"
trap 'rm -f "$GATE_LOG"' EXIT

cargo test --release -p tyrne-kernel --lib -- console_write_is_absent_in_release_builds console_write_number_is_bad_syscall_in_release_build | tee "$GATE_LOG"
if ! grep -Fxq 'test syscall::abi::tests::console_write_is_absent_in_release_builds ... ok' "$GATE_LOG" ||
   ! grep -Fxq 'test syscall::dispatch::tests::console_write_number_is_bad_syscall_in_release_build ... ok' "$GATE_LOG" ||
   ! grep -Fq 'test result: ok. 2 passed; 0 failed;' "$GATE_LOG"; then
    echo "FAIL: release syscall gate requires both named tests to pass (2 passed)" >&2
    exit 1
fi
echo "PASS: both release-only console_write regression tests executed"
