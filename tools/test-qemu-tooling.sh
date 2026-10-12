#!/usr/bin/env bash
# Regression checks for QEMU argument parsing; no real guest or build required.
# Run from any directory: tools/test-qemu-tooling.sh.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
PROBE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/tyrne-qemu-args.XXXXXX")"
trap 'rm -rf "$PROBE_DIR"' EXIT
mkdir "$PROBE_DIR/bin"
ELF="$PROBE_DIR/kernel image.elf"
touch "$ELF"
cat > "$PROBE_DIR/bin/qemu-system-aarch64" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$@" > "$QEMU_TEST_ARGS"
printf '%s\n' 'hello from userspace' 'tyrne: userspace task exited' 'tyrne: all tasks complete'
STUB
chmod +x "$PROBE_DIR/bin/qemu-system-aarch64"
export PATH="$PROBE_DIR/bin:$PATH"
export TMPDIR="$PROBE_DIR"
export QEMU_TEST_ARGS="$PROBE_DIR/argv"
unset QEMU_SMP
CASES=0

check_run() {
    local expected_rc="$1"
    shift
    local rc=0
    rm -f "$QEMU_TEST_ARGS"
    "$@" > "$PROBE_DIR/output" 2>&1 || rc=$?
    if [[ "$rc" -ne "$expected_rc" ]]; then
        cat "$PROBE_DIR/output" >&2
        printf 'FAIL: expected exit %s, got %s: %s\n' "$expected_rc" "$rc" "$*" >&2
        exit 1
    fi
    if grep -q 'unbound variable' "$PROBE_DIR/output"; then
        echo "FAIL: shell internals leaked into argument diagnostics" >&2
        exit 1
    fi
    if [[ "$expected_rc" -eq 2 ]]; then
        grep -q '^error:' "$PROBE_DIR/output"
        grep -q 'Usage:' "$PROBE_DIR/output"
        [[ ! -f "$QEMU_TEST_ARGS" ]]
    fi
    CASES=$((CASES + 1))
}

check_smp() {
    local expected="$1"
    shift
    check_run 0 "$@"
    local actual
    actual="$(awk '$0 == "-smp" { getline; print; exit }' "$QEMU_TEST_ARGS")"
    [[ "$actual" == "$expected" ]] || {
        printf 'FAIL: expected -smp %s, got %s\n' "$expected" "$actual" >&2
        exit 1
    }
    # The explicit path contains spaces and must remain one argv element.
    [[ "$(tail -n 1 "$QEMU_TEST_ARGS")" == "$ELF" ]]
}

for script in tools/run-qemu.sh tools/smoke.sh; do
    check_smp 1 "$script" "$ELF"
    check_smp 3 env QEMU_SMP=3 "$script" "$ELF"
    check_smp 2 env QEMU_SMP=3 "$script" --smp 2 "$ELF"
    check_smp 2 env QEMU_SMP=invalid "$script" --smp 2 "$ELF"
    check_smp 4 "$script" "$ELF" --smp 4
    check_smp 2 "$script" --smp 3 --smp 2 "$ELF"
    for invalid in 0 abc -1 1.5 '' '2 3' '2;exit'; do
        check_run 2 "$script" --smp "$invalid" "$ELF"
        check_run 2 env QEMU_SMP="$invalid" "$script" "$ELF"
    done
    check_run 2 "$script" --smp
    grep -q -- '--smp requires a value' "$PROBE_DIR/output"
    check_run 2 "$script" --smp --release "$ELF"
    check_run 2 "$script" --unknown
    check_run 2 "$script" "$ELF" "$ELF"
    check_run 0 env QEMU_SMP=invalid "$script" --help
    grep -q 'QEMU_SMP' "$PROBE_DIR/output"
done

check_run 2 tools/smoke.sh --timeout
grep -q -- '--timeout requires a value' "$PROBE_DIR/output"
for invalid in 0 abc -1 1.5 '' --int; do
    check_run 2 tools/smoke.sh --timeout "$invalid" "$ELF"
    grep -q -- '--timeout' "$PROBE_DIR/output"
done
check_smp 1 tools/smoke.sh --timeout 1 --int "$ELF"
check_smp 1 tools/run-qemu.sh --release --int-log "$ELF"
printf 'PASS: %s QEMU tooling argument cases (stubbed QEMU; no SMP claim)\n' "$CASES"
