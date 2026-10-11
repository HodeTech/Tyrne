#!/usr/bin/env bash
# Profile-aware smoke regression checks. See --help for actual guest probes.
set -euo pipefail
exec python3 "$(dirname "$0")/test-smoke-gates.py" "$@"
