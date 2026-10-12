#!/usr/bin/env bash
# Emit a deliberate actual smoke rejection for the CALLER's pipeline check.
# Expected exit: 1 with the missing-EL0 diagnostic. This is a synthetic trace,
# not a guest boot; the CI run step must preserve this status through tee.
set -euo pipefail
[[ $# -eq 0 ]] || { echo "Usage: tools/probe-smoke-pipeline.sh (deliberately exits 1)" >&2; exit 2; }
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROBE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/tyrne-smoke-pipeline.XXXXXX")"
trap 'rm -rf "$PROBE_DIR"' EXIT
mkdir "$PROBE_DIR/bin"
touch "$PROBE_DIR/kernel.elf"
cat > "$PROBE_DIR/bin/qemu-system-aarch64" <<'STUB'
#!/usr/bin/env bash
printf '%s\n' 'tyrne: all tasks complete'
STUB
chmod +x "$PROBE_DIR/bin/qemu-system-aarch64"
# Do not catch/rewrite the actual smoke status or invent its diagnostic.
PATH="$PROBE_DIR/bin:$PATH" TMPDIR="$PROBE_DIR" QEMU_SMP=1 \
    "$REPO_ROOT/tools/smoke.sh" --int --timeout 1 "$PROBE_DIR/kernel.elf"
