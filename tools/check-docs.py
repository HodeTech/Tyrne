#!/usr/bin/env python3
"""Offline documentation consistency command (Python 3.9+, ADR-0043).

Step 11 supplies local navigation; remaining check families/required CI wiring
belong to Step 12. No network, Git dependency or repository-setting writes.
"""

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
if sys.version_info < (3, 9):
    raise SystemExit("check-docs requires Python 3.9 or newer")

from docs_consistency import scan_links

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository or isolated fixture root; default is script-relative")
    parser.add_argument("--checks", choices=("links",), default="links", help="Selected implemented check family (Step 11: links)")
    parser.add_argument("--json", action="store_true", help="Deterministic JSON report on stdout")
    args = parser.parse_args()
    report = scan_links(args.root)
    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    else:
        for finding in report.findings:
            print(f"{finding.path}:{finding.line}: {finding.code}: {finding.message}")
        print(f"docs consistency (links): {report.files} Markdown files, "
              f"{report.local_targets} local targets, {report.fragments} fragments, "
              f"{len(report.findings)} findings")
    return 1 if report.findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
