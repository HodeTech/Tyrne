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
#   tools/smoke.sh --int                 — add -d int,unimp,guest_errors
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
        --int) INT_FLAGS=(-d int,unimp,guest_errors); shift ;;
        --timeout) TO="$2"; shift 2 ;;
        -h|--help) sed -n '2,/^set -/p' "$0" | sed 's/^# \{0,1\}//;/^set -/d' >&2; exit 0 ;;
        --*) echo "error: unknown flag: $1" >&2; exit 2 ;;
        *) KERNEL="$1"; shift ;;
    esac
done

[[ -z "$KERNEL" ]] && KERNEL="target/aarch64-unknown-none/${PROFILE}/tyrne-bsp-qemu-virt"
if [[ ! -f "$KERNEL" ]]; then
    echo "error: kernel image not found at $KERNEL (run 'cargo kernel-build' first)" >&2
    exit 1
fi

LOG="${TMPDIR:-/tmp}/tyrne-smoke.$$.log"
echo "smoke: $KERNEL  (budget ${TO}s)  log -> $LOG" >&2

# perl alarm wrapper: fork QEMU, SIGTERM it after $TO seconds. QEMU inherits
# the child's stdout/stderr (redirected to $LOG by the caller below).
TO="$TO" perl -e '
    my $pid = fork();
    if ($pid == 0) { open(STDIN, "<", "/dev/null"); exec(@ARGV) or die "exec: $!"; }
    $SIG{ALRM} = sub { kill("TERM", $pid); };
    alarm($ENV{TO});
    waitpid($pid, 0);
' qemu-system-aarch64 -M virt -cpu cortex-a72 -m 128M -smp 1 \
    -display none -serial stdio -monitor none \
    "${INT_FLAGS[@]+"${INT_FLAGS[@]}"}" \
    -kernel "$KERNEL" > "$LOG" 2>&1 || true

echo "===== trace =====" >&2
cat "$LOG"
echo "===== markers =====" >&2
grep -nE "tyrne:|panic|all tasks complete|high-half" "$LOG" || echo "(no tyrne markers found)"
echo "===== fault classes (int log, if --int) =====" >&2
grep -nE "Taking exception|Translation fault|Permission fault|Data Abort|Prefetch Abort" "$LOG" | head -40 || true
