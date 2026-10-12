#!/usr/bin/env bash
# Assert that deliberate regressions fail the real CI commands in a disposable
# copy of the tracked worktree. Never alters repository source or branches.
# Usage: tools/test-ci-gates.sh --shell | --userland | --release | --hal | --bsp | --arm-host
set -euo pipefail

usage() {
    echo "Usage: tools/test-ci-gates.sh --shell | --userland | --release | --hal | --bsp | --arm-host" >&2
}

[[ $# -eq 1 ]] || { usage; exit 2; }
MODE="$1"
case "$MODE" in
    --shell|--userland|--release|--hal|--bsp|--arm-host) ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
esac

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
if [[ "$MODE" == "--arm-host" ]]; then
    HOST_TARGET="$(rustc -vV | sed -n 's/^host: //p')"
    [[ "$HOST_TARGET" == aarch64-* ]] || {
        echo "error: --arm-host requires a native aarch64 Rust host; got $HOST_TARGET" >&2
        exit 1
    }
fi
PROBE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/tyrne-ci-gates.XXXXXX")"
trap 'rm -rf "$PROBE_DIR"' EXIT
TREE="$PROBE_DIR/tree"
mkdir "$TREE"
# Read the current tracked files, not a historical commit or the build cache.
# NUL delimiters preserve spaces; cp -p preserves executable scripts.
while IFS= read -r -d '' path; do
    mkdir -p "$TREE/$(dirname "$path")"
    cp -p "$REPO_ROOT/$path" "$TREE/$path"
done < <(git ls-files -z)
export CARGO_TARGET_DIR="$PROBE_DIR/target"
export CARGO_TERM_COLOR=never
cd "$TREE"

run_negative() {
    local diagnostic="$1"
    shift
    local rc=0
    "$@" > "$PROBE_DIR/diagnostic.log" 2>&1 || rc=$?
    if [[ "$rc" -eq 0 ]]; then
        cat "$PROBE_DIR/diagnostic.log" >&2
        echo "FAIL: deliberate $MODE regression unexpectedly passed" >&2
        exit 1
    fi
    if [[ "$MODE" == "--arm-host" ]]; then
        # --all-targets can report the no_std binary's unwind rejection before
        # the test harness's duplicate panic handler. Both reject this exact
        # copied cfg mutation; unrelated failures and tool errors must fail.
        if [[ "$rc" -ne 101 ]]; then
            cat "$PROBE_DIR/diagnostic.log" >&2
            echo "FAIL: ARM clippy probe expected compiler exit 101; got $rc" >&2
            exit 1
        fi
        if ! grep -Fxq "$diagnostic" "$PROBE_DIR/diagnostic.log"; then
            diagnostic='error: unwinding panics are not supported without std'
        fi
        if ! grep -Fxq "$diagnostic" "$PROBE_DIR/diagnostic.log"; then
            cat "$PROBE_DIR/diagnostic.log" >&2
            echo "FAIL: ARM clippy probe failed without a recognized cfg-regression diagnostic" >&2
            exit 1
        fi
    elif ! grep -Fq "$diagnostic" "$PROBE_DIR/diagnostic.log"; then
        cat "$PROBE_DIR/diagnostic.log" >&2
        echo "FAIL: command failed without expected diagnostic: $diagnostic" >&2
        exit 1
    fi
    printf 'PASS: %s regression rejected (exit %s; diagnostic %s)\n' "$MODE" "$rc" "$diagnostic"
}

case "$MODE" in
    --arm-host)
        # Restore only hello's six original arch-only predicates in the copy.
        # Keep build.rs and the syscall shim unchanged to isolate this hazard.
        python3 - <<'PROBE'
from pathlib import Path
path = Path("userland/hello/src/main.rs")
source = path.read_text()
gate = 'all(target_arch = "aarch64", target_os = "none")'
if source.count(gate) != 6:
    raise SystemExit("FAIL: ARM probe expected exactly six hello target predicates")
path.write_text(source.replace(gate, 'target_arch = "aarch64"'))
PROBE
        # shellcheck disable=SC2016  # Backticks are literal compiler diagnostic data, not commands.
        run_negative 'error[E0152]: found duplicate lang item `panic_impl`' cargo clippy --workspace --exclude tyrne-bsp-qemu-virt --all-targets -- -D warnings
        ;;
    --shell)
        cat > tools/ci-lint-probe.sh <<'PROBE'
#!/usr/bin/env bash
probe_value="$1"
echo $probe_value
PROBE
        run_negative SC2086 shellcheck tools/*.sh
        ;;
    --userland)
        cat >> userland/tyrne-user/src/lib.rs <<'PROBE'

#[allow(dead_code, reason = "disposable CI lint regression probe")]
fn ci_lint_probe() -> u64 {
    let value = 1_u64;
    value.clone()
}
PROBE
        run_negative clippy::clone_on_copy cargo clippy -p tyrne-user -p tyrne-userland-hello --target aarch64-unknown-none -- -D warnings
        ;;
    --release)
        awk '{ print } $0 == "[profile.release]" { print "debug-assertions = true" }' Cargo.toml > Cargo.toml.probe
        mv Cargo.toml.probe Cargo.toml
        run_negative 'FAIL: release syscall gate requires both named tests to pass' tools/check-release-tests.sh
        ;;
    --hal|--bsp)
        if [[ "$MODE" == "--hal" ]]; then
            ROOT="hal/src/lib.rs"
        else
            ROOT="bsp-qemu-virt/src/main.rs"
            # The tracked copy excludes hello.bin. Build it only in this
            # disposable tree, so a missing image cannot mask the lint probe.
            tools/build-userland.sh
        fi
        cat >> "$ROOT" <<'PROBE'

#[allow(dead_code, reason = "disposable CI panic-family regression probe")]
fn ci_panic_family_probe() -> u64 {
    core::hint::black_box(None::<u64>).unwrap()
}
PROBE
        if [[ "$MODE" == "--hal" ]]; then
            run_negative clippy::unwrap_used cargo host-clippy
        else
            run_negative clippy::unwrap_used cargo kernel-clippy
        fi
        ;;
esac
