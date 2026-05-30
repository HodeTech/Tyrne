#!/usr/bin/env bash
# Non-interactive QEMU smoke runner for automated use (CI / agent loops).
#
# Unlike tools/run-qemu.sh (interactive, mon:stdio), this runs QEMU with a
# pure serial console (no monitor — so an stdin EOF cannot quit QEMU early),
# bounds the run with a wall-clock timeout (the kernel idles in WFI after
# "tyrne: all tasks complete" and never exits on its own), captures the full
# trace to a log file, and reports the boot markers.
#
# Usage:
#   tools/smoke.sh                       — debug build, 20s budget
#   tools/smoke.sh --release             — release build
#   tools/smoke.sh --int                 — add -d int,unimp (fault-class check)
#   tools/smoke.sh --timeout 30          — override the wall-clock budget (s)
#   tools/smoke.sh <path/to/elf>         — explicit ELF
#
# The full trace is written to ${TMPDIR:-/tmp}/tyrne-smoke.<pid>.log (printed).
set -euo pipefail

PROFILE="debug"
TO=20
INT_FLAGS=()
KERNEL=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --release) PROFILE="release"; shift ;;
        --int) INT_FLAGS=(-d int,unimp); shift ;;  # no guest_errors: PL011 noise interleaves the trace
        --timeout) TO="$2"; shift 2 ;;
        -h|--help) sed -n '2,/^set -/p' "$0" | sed 's/^# \{0,1\}//;/^set -/d' >&2; exit 0 ;;
        --*) echo "error: unknown flag: $1" >&2; exit 2 ;;
        *) KERNEL="$1"; shift ;;
    esac
done

# Validate the budget: it is passed to `timeout`/`alarm()` as integer seconds.
# Both fail (or misbehave) on a non-numeric value, and zero is worse than
# invalid — `timeout 0s` *disables* the timeout and `alarm(0)` cancels it, so a
# zero budget would let the WFI-idling kernel hang the run forever. Require a
# strictly positive integer (the regex rejects "0", non-numerics, and "").
if ! [[ "$TO" =~ ^[1-9][0-9]*$ ]]; then
    echo "error: --timeout must be a positive integer (seconds); got '$TO'" >&2
    exit 2
fi

[[ -z "$KERNEL" ]] && KERNEL="target/aarch64-unknown-none/${PROFILE}/tyrne-bsp-qemu-virt"
if [[ ! -f "$KERNEL" ]]; then
    echo "error: kernel image not found at $KERNEL (run 'cargo kernel-build' first)" >&2
    exit 1
fi

LOG="${TMPDIR:-/tmp}/tyrne-smoke.$$.log"
echo "smoke: $KERNEL  (budget ${TO}s)  log -> $LOG" >&2

# The kernel idles in WFI after completion and never exits on its own, so the
# run must be bounded by a wall-clock timeout. Prefer coreutils `timeout(1)`
# (present on most Linux CI images); fall back to a Perl `alarm()` wrapper
# (macOS ships Perl but not `timeout`); error out if neither is available.
QEMU_ARGS=(
    -M virt -cpu cortex-a72 -m 128M -smp 1
    -display none -serial stdio -monitor none
    "${INT_FLAGS[@]+"${INT_FLAGS[@]}"}"
    -kernel "$KERNEL"
)
if command -v timeout >/dev/null 2>&1; then
    timeout "${TO}s" qemu-system-aarch64 "${QEMU_ARGS[@]}" </dev/null > "$LOG" 2>&1 || true
elif command -v perl >/dev/null 2>&1; then
    # Perl alarm wrapper: fork QEMU, SIGTERM it after $TO seconds. QEMU inherits
    # the child's stdout/stderr (redirected to $LOG by the caller below).
    TO="$TO" perl -e '
        my $pid = fork();
        if ($pid == 0) { open(STDIN, "<", "/dev/null"); exec(@ARGV) or die "exec: $!"; }
        $SIG{ALRM} = sub { kill("TERM", $pid); };
        alarm($ENV{TO});
        waitpid($pid, 0);
    ' qemu-system-aarch64 "${QEMU_ARGS[@]}" > "$LOG" 2>&1 || true
else
    echo "error: neither 'timeout(1)' nor 'perl' is available to bound the ${TO}s run" >&2
    exit 1
fi

echo "===== trace =====" >&2
cat "$LOG"
echo "===== markers =====" >&2
grep -nE "tyrne:|panic|all tasks complete|high-half" "$LOG" || echo "(no tyrne markers found)"
echo "===== fault classes (int log, if --int) =====" >&2
grep -nE "Taking exception|Translation fault|Permission fault|Data Abort|Prefetch Abort" "$LOG" | head -40 || true

# ── Gate (usable as a CI / regression check) ──────────────────────────────────
# The kernel idles in WFI after completion and is SIGTERM'd, so a non-zero QEMU
# exit is expected and ignored above (|| true). Pass/fail is decided by the
# trace contents, not QEMU's exit code: the completion marker must appear, and
# there must be no panic or CPU fault. `--int` uses `-d int,unimp` (no
# `guest_errors`), so the pre-existing PL011 "data written to disabled UART"
# noise does not interleave with the serial markers or the fault grep.
rc=0
if ! grep -q "all tasks complete" "$LOG"; then
    echo "FAIL: 'tyrne: all tasks complete' marker missing (boot did not finish)" >&2
    rc=1
fi
if grep -qE "tyrne panic|Translation fault|Permission fault|Data Abort|Prefetch Abort|Unallocated Instruction" "$LOG"; then
    echo "FAIL: a panic / CPU-fault class appeared in the trace" >&2
    rc=1
fi
[[ $rc -eq 0 ]] && echo "PASS: boot reached 'all tasks complete' with no panic/fault" >&2
exit $rc
