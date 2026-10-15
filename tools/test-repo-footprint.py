#!/usr/bin/env python3
"""Real temporary-Git contract fixtures for ADR-0044 storage enforcement."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
TOOL = Path(__file__).with_name("check-repo-footprint.py").resolve()
REPORTS = "docs/analysis/reports/"


def git(root, *args, data=None):
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    return subprocess.check_output(
        ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", "-C", str(root), *args],
        input=data, stderr=subprocess.PIPE, env=env,
    )


@contextmanager
def repository():
    with tempfile.TemporaryDirectory(prefix="tyrne-footprint-") as directory:
        root = Path(directory)
        git(root, "init", "--quiet", "--initial-branch=development")
        write(root, "README.md", b"fixture\n")
        commit(root)
        yield root


def write(root, path, data):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def commit(root):
    git(root, "add", "--all")
    git(root, "commit", "--quiet", "-m", "fixture")


def check(root, *, env=None, cwd=None, extra=()):
    result = subprocess.run([sys.executable, str(TOOL), "--root", str(root), "--json", *extra],
                            capture_output=True, env=env, cwd=cwd)
    return result, json.loads(result.stdout)


def codes(report):
    return {finding["code"] for finding in report["findings"]}


class FootprintTests(unittest.TestCase):
    def test_exact_blob_boundary_and_untracked_worktree_do_not_fail(self):
        with repository() as root:
            write(root, "source.dat", b"x" * 1048576)
            git(root, "add", "source.dat")
            write(root, "source.dat", b"y" * 1048577)
            write(root, "untracked.dat", b"z" * 1048577)
            result, report = check(root)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(report["indexed_blobs"], 2)
            self.assertEqual(report["findings"], [])

    def test_staged_blob_above_boundary_is_rejected(self):
        with repository() as root:
            write(root, "source.dat", b"x" * 1048577)
            git(root, "add", "source.dat")
            result, report = check(root)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(codes(report), {"footprint-blob"})
            self.assertEqual(report["findings"][0]["path"], "source.dat")
            self.assertEqual(report["findings"][0]["source"], "index")

    def test_deleted_oversized_historical_blob_is_rejected(self):
        with repository() as root:
            write(root, "old.dat", b"x" * 1048577)
            commit(root)
            offending = git(root, "rev-parse", "HEAD").decode().strip()
            (root / "old.dat").unlink()
            commit(root)
            result, report = check(root)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(codes(report), {"footprint-blob"})
            self.assertEqual(report["findings"][0]["source"], offending)

    def test_exact_report_total_excludes_markdown(self):
        with repository() as root:
            write(root, REPORTS + "a.json", b"a" * 262144)
            write(root, REPORTS + "b.log", b"b" * 262144)
            write(root, REPORTS + "report.md", b"m" * 700000)
            git(root, "add", "--all")
            result, report = check(root)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(report["findings"], [])

    def test_report_total_counts_each_path_even_when_blobs_are_identical(self):
        with repository() as root:
            for name in ["a.json", "b.json"]:
                write(root, REPORTS + name, b"a" * 262145)
            git(root, "add", "--all")
            result, report = check(root)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(codes(report), {"footprint-reports"})
            self.assertIn("524290", report["findings"][0]["message"])

    def test_deleted_historical_report_aggregate_is_rejected(self):
        with repository() as root:
            for name in ["a.json", "b.json"]:
                write(root, REPORTS + name, b"a" * 300000)
            commit(root)
            shutil.rmtree(root / REPORTS)
            commit(root)
            result, report = check(root)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(codes(report), {"footprint-reports"})
            self.assertNotEqual(report["findings"][0]["source"], "index")

    def test_catalog_pair_boundary_and_independent_pairs(self):
        with repository() as root:
            for name in ["first", "second"]:
                write(root, REPORTS + name + "-evidence-catalog.md", b"m" * 65536)
                write(root, REPORTS + name + "-evidence-catalog.json", b"j" * 65536)
            git(root, "add", "--all")
            result, report = check(root)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(report["limits_bytes"], {"blob": 1048576, "reports": 524288, "catalog": 131072})

    def test_catalog_pair_above_limit_is_rejected(self):
        with repository() as root:
            write(root, REPORTS + "sample-evidence-catalog.md", b"m" * 65536)
            write(root, REPORTS + "sample-evidence-catalog.json", b"j" * 65537)
            git(root, "add", "--all")
            result, report = check(root)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(codes(report), {"footprint-catalog"})

    def test_deleted_historical_catalog_pair_is_rejected(self):
        with repository() as root:
            write(root, REPORTS + "sample-evidence-catalog.md", b"m" * 65536)
            write(root, REPORTS + "sample-evidence-catalog.json", b"j" * 65537)
            commit(root)
            shutil.rmtree(root / REPORTS)
            commit(root)
            result, report = check(root)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(codes(report), {"footprint-catalog"})

    def test_symlink_stores_target_text_and_gitlink_stores_no_blob(self):
        with repository() as root:
            write(root, "untracked-large.dat", b"x" * 1048577)
            (root / "link").symlink_to("untracked-large.dat")
            git(root, "add", "link")
            head = git(root, "rev-parse", "HEAD").decode().strip()
            git(root, "update-index", "--add", "--cacheinfo", "160000," + head + ",submodule")
            result, report = check(root)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(report["indexed_blobs"], 2)

    def test_control_character_paths_are_nul_safe_and_json_is_deterministic(self):
        with repository() as root:
            names = ["z\nodd.dat", "a\todd.dat"]
            for name in names:
                write(root, name, b"x" * 1048577)
            git(root, "add", *names)
            first, report = check(root)
            second, _ = check(root)
            self.assertEqual(first.returncode, 1)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual([f["path"] for f in report["findings"]], sorted(names))
            text = subprocess.run([sys.executable, str(TOOL), "--root", str(root)], capture_output=True)
            self.assertEqual(text.returncode, 1)
            self.assertEqual(len(text.stdout.splitlines()), 3)
            self.assertNotIn(b"Traceback", text.stderr)

    def test_shallow_history_fails_closed(self):
        with repository() as root:
            (root / ".git/shallow").write_bytes(git(root, "rev-parse", "HEAD"))
            result, report = check(root)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(codes(report), {"input"})
            self.assertIn("shallow", report["findings"][0]["message"])

    def test_promisor_configuration_fails_before_lazy_fetch(self):
        with repository() as root:
            git(root, "config", "remote.invalid.promisor", "true")
            git(root, "config", "remote.invalid.url", "https://invalid.invalid/no-network")
            result, report = check(root)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(codes(report), {"input"})
            self.assertIn("promisor", report["findings"][0]["message"])

    def test_partial_clone_marker_fails_closed(self):
        with repository() as root:
            git(root, "config", "extensions.partialClone", "invalid")
            result, report = check(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("partial", report["findings"][0]["message"])

    def test_unmerged_index_is_not_a_clean_snapshot(self):
        with repository() as root:
            oid = git(root, "rev-parse", "HEAD:README.md").decode().strip()
            git(root, "update-index", "--index-info", data=("100644 " + oid + " 1\tconflict\n").encode())
            result, report = check(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("unmerged", report["findings"][0]["message"])

    def test_missing_blob_fails_closed(self):
        with repository() as root:
            git(root, "update-index", "--add", "--cacheinfo", "100644," + "1" * 40 + ",missing.dat")
            result, report = check(root)
            self.assertEqual(result.returncode, 2)
            self.assertIn("missing", report["findings"][0]["message"])

    def test_explicit_root_ignores_ambient_git_state(self):
        with repository() as root, repository() as other:
            write(root, "large.dat", b"x" * 1048577)
            git(root, "add", "large.dat")
            env = dict(os.environ, GIT_DIR=str(other / ".git"), GIT_WORK_TREE=str(other),
                       GIT_INDEX_FILE=str(other / ".git/index"))
            result, report = check(root, env=env, cwd=other)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(codes(report), {"footprint-blob"})

    def test_replacement_ref_cannot_hide_oversized_history(self):
        with repository() as root:
            initial = git(root, "rev-parse", "HEAD").decode().strip()
            write(root, "large.dat", b"x" * 1048577)
            commit(root)
            offending = git(root, "rev-parse", "HEAD").decode().strip()
            (root / "large.dat").unlink()
            commit(root)
            git(root, "replace", offending, initial)
            result, report = check(root)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(codes(report), {"footprint-blob"})

    def test_legacy_grafts_cannot_hide_oversized_history(self):
        with repository() as root:
            write(root, "large.dat", b"x" * 1048577)
            commit(root)
            (root / "large.dat").unlink()
            commit(root)
            (root / ".git/info/grafts").write_bytes(git(root, "rev-parse", "HEAD"))
            result, report = check(root)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(codes(report), {"input"})
            self.assertIn("graft", report["findings"][0]["message"])

    def test_invalid_root_and_subdirectory_fail_closed(self):
        with repository() as root, tempfile.TemporaryDirectory() as empty:
            for target in [Path(empty), root / "absent", root / ".git"]:
                result, report = check(target)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertEqual(codes(report), {"input"})

    def test_symlink_loop_root_returns_structured_input_error(self):
        with tempfile.TemporaryDirectory(prefix="tyrne-footprint-loop-") as directory:
            root = Path(directory) / "loop"
            root.symlink_to("loop")
            result = subprocess.run(
                [sys.executable, str(TOOL), "--root", str(root), "--json"], capture_output=True,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(codes(json.loads(result.stdout)), {"input"})
            self.assertNotIn(b"Traceback", result.stderr)

    def test_script_relative_default_is_independent_of_cwd(self):
        with repository() as root, tempfile.TemporaryDirectory() as elsewhere:
            tools = root / "tools"
            tools.mkdir()
            script = tools / TOOL.name
            shutil.copyfile(TOOL, script)
            git(root, "add", "--all")
            result = subprocess.run([sys.executable, str(script), "--json"], cwd=elsewhere, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(json.loads(result.stdout)["findings"], [])


if __name__ == "__main__":
    unittest.main()
