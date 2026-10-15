#!/usr/bin/env python3
"""Offline documentation consistency command (Python 3.9+, ADR-0043).

Local navigation, metadata inventories and bounded source audit references.
No network, Git dependency or repository-setting writes.
"""

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
if sys.version_info < (3, 9):
    raise SystemExit("check-docs requires Python 3.9 or newer")

from docs_metadata import CHECKS, scan_docs

ROOT = Path(__file__).resolve().parents[1]


def select_checks(value):
    if value.strip() == "all":
        return tuple(CHECKS)
    selected = tuple(name.strip() for name in value.split(","))
    if not selected or len(set(selected)) != len(selected) or any(name not in CHECKS for name in selected):
        raise argparse.ArgumentTypeError("Select all or distinct comma-separated families: " + ", ".join(CHECKS))
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository or isolated fixture root; default is script-relative")
    parser.add_argument("--checks", type=select_checks, default=tuple(CHECKS), help="all (default), or distinct comma-separated families: " + ", ".join(CHECKS))
    parser.add_argument("--json", action="store_true", help="Deterministic JSON report on stdout")
    args = parser.parse_args()
    report = scan_docs(args.root, checks=args.checks)
    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    else:
        for finding in report.findings:
            print(f"{finding.path}:{finding.line}: {finding.code}: {finding.message}")
        print(f"docs consistency ({','.join(report.checks)}): {report.files} Markdown files, "
              f"{report.local_targets} local targets, {report.fragments} fragments, "
              f"{len(report.findings)} findings")
    return 1 if report.findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
