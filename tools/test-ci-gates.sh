#!/usr/bin/env bash
# Assert that deliberate regressions fail the real CI commands in a disposable
# copy of the tracked worktree. Never alters repository source or branches.
# Usage: tools/test-ci-gates.sh --shell | --userland | --release
set -euo pipefail

usage() {
    echo "Usage: tools/test-ci-gates.sh --shell | --userland | --release" >&2
}

[[ $# -eq 1 ]] || { usage; exit 2; }
MODE="$1"
case "$MODE" in
    --shell|--userland|--release) ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
esac

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
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
    if ! grep -Fq "$diagnostic" "$PROBE_DIR/diagnostic.log"; then
        cat "$PROBE_DIR/diagnostic.log" >&2
        echo "FAIL: command failed without expected diagnostic: $diagnostic" >&2
        exit 1
    fi
    printf 'PASS: %s regression rejected (exit %s; diagnostic %s)\n' "$MODE" "$rc" "$diagnostic"
}

case "$MODE" in
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
esac
