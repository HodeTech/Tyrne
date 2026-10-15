#!/usr/bin/env python3
"""Check indexed and complete HEAD-history storage limits (ADR-0044).

Python 3.9+ standard library and Git; offline and read-only. Worktree changes
and untracked files do not describe stored Git blobs. Shallow/promisor inputs
fail closed. Gitlinks store external commit IDs, not parent-repository blobs.
"""

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
LIMITS = {"blob": 1048576, "reports": 524288, "catalog": 131072}
REPORTS = "docs/analysis/reports/"


class InputError(ValueError):
    """The requested complete Git snapshot cannot be verified."""


def git(root, *args, data=None, optional=False):
    # Honor the explicit root/index rather than ambient alternate Git state.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root), *args],
        input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
    )
    if optional and result.returncode == 1:
        return b""
    if result.returncode:
        raise InputError("Git " + args[0] + " failed: " + result.stderr.decode("utf-8", "replace").strip())
    return result.stdout


def entries(raw, *, index=False):
    """Read NUL-delimited Git paths without filename quoting ambiguity."""
    result = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, middle, last = metadata.decode("ascii").split()
        path = path.decode("utf-8", "strict")
        if index:
            oid = middle
            if last != "0":
                raise InputError("Resolve unmerged index entries before checking footprint")
            kind = "commit" if mode == "160000" else "blob"
        else:
            kind, oid = middle, last
        if mode == "160000" and kind == "commit":
            continue
        if kind != "blob" or mode not in {"100644", "100755", "120000"}:
            raise InputError("Unsupported Git entry mode/type at " + path)
        result.append((path, oid))
    return sorted(result)


def catalog_stem(path):
    name = PurePosixPath(path)
    if path.startswith(REPORTS) and name.name.endswith(("-evidence-catalog.md", "-evidence-catalog.json")):
        return str(name.with_suffix(""))
    return None


def scan(root):
    root = root.resolve()
    if not root.is_dir():
        raise InputError("Root is not an existing directory")
    top = git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()
    if Path(top).resolve() != root:
        raise InputError("Root must be the Git working-tree top level")
    if git(root, "rev-parse", "--is-shallow-repository").strip() != b"false":
        raise InputError("Complete history is required; shallow repositories are unsupported")
    grafts = Path(git(root, "rev-parse", "--git-path", "info/grafts").decode("utf-8").rstrip("\n"))
    if (grafts if grafts.is_absolute() else root / grafts).exists():
        raise InputError("Complete original history is required; legacy graft files are unsupported")
    partial = git(root, "config", "--get", "extensions.partialClone", optional=True).strip()
    promisors = git(root, "config", "--bool", "--get-regexp", r"^remote\..*\.promisor$", optional=True)
    if partial or any(line.rsplit(b" ", 1)[-1] == b"true" for line in promisors.splitlines()):
        raise InputError("Complete local objects are required; promisor/partial clones are unsupported")
    head = git(root, "rev-parse", "--verify", "HEAD").decode("ascii").strip()
    indexed = entries(git(root, "ls-files", "--stage", "-z"), index=True)
    history = git(root, "rev-list", "--format=%H:%T", "--no-commit-header", head).decode("ascii")
    trees = {}
    for line in history.splitlines():
        commit, tree = line.split(":")
        trees[tree] = min(commit, trees.get(tree, commit))
    def snapshots():
        # Retain one tree at a time, not every historical path inventory.
        yield "index", indexed
        for tree, commit in sorted(trees.items()):
            yield commit, entries(git(root, "ls-tree", "-r", "-z", tree))

    sizes = {}
    findings, seen = [], set()

    def issue(path, code, message, source, identity):
        key = (path, code, identity)
        if key not in seen:
            seen.add(key)
            findings.append({"path": path, "line": 1, "code": code, "message": message, "source": source})

    for source, snapshot in snapshots():
        missing = sorted({oid for _, oid in snapshot} - sizes.keys())
        if missing:
            raw = git(root, "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)",
                      data=("\n".join(missing) + "\n").encode("ascii"))
            batch = {}
            for line in raw.decode("ascii").splitlines():
                fields = line.split()
                if len(fields) != 3 or fields[1] != "blob" or not fields[2].isdigit():
                    raise InputError("A required stored blob is missing or invalid")
                batch[fields[0]] = int(fields[2])
            if set(batch) != set(missing):
                raise InputError("Git returned an incomplete blob-size inventory")
            sizes.update(batch)
        report_files = []
        catalogs = {}
        for path, oid in snapshot:
            size = sizes[oid]
            if size > LIMITS["blob"]:
                issue(path, "footprint-blob", str(size) + " bytes exceeds 1 MiB per stored blob", source, oid)
            if path.startswith(REPORTS) and PurePosixPath(path).suffix.casefold() != ".md":
                report_files.append((path, oid))
            stem = catalog_stem(path)
            if stem:
                catalogs.setdefault(stem, []).append((path, oid))
        total = sum(sizes[oid] for _, oid in report_files)
        if total > LIMITS["reports"]:
            issue(REPORTS.rstrip("/"), "footprint-reports", str(total) + " bytes exceeds 512 KiB of non-Markdown reports",
                  source, tuple(report_files))
        for stem, members in sorted(catalogs.items()):
            total = sum(sizes[oid] for _, oid in members)
            if total > LIMITS["catalog"]:
                issue(stem, "footprint-catalog", str(total) + " bytes exceeds 128 KiB per catalog pair",
                      source, tuple(members))
    return {"head": head, "indexed_blobs": len(indexed), "historical_trees": len(trees),
            "unique_blobs": len(sizes), "limits_bytes": LIMITS,
            "findings": sorted(findings, key=lambda item: (item["path"], item["code"], item["source"], item["message"]))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Git worktree root; default is script-relative")
    parser.add_argument("--json", action="store_true", help="Deterministic JSON report")
    args = parser.parse_args()
    try:
        report = scan(args.root)
        status = 1 if report["findings"] else 0
    except (InputError, OSError, UnicodeError, ValueError) as error:
        report = {"findings": [{"path": ".", "line": 1, "code": "input", "message": str(error), "source": "input"}]}
        status = 2
    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        for finding in report["findings"]:
            path = finding["path"]
            if any(ord(char) < 32 or ord(char) == 127 for char in path):
                path = json.dumps(path, ensure_ascii=True)
            print(f"{path}:1: {finding['code']}: {finding['message']} (source {finding['source']})")
        print(f"repository footprint: {len(report['findings'])} findings")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
