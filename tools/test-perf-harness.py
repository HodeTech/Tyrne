#!/usr/bin/env python3
"""Fast synthetic harness metadata/report/failure controls, without a guest."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tyrne perf fixture ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "tools").mkdir()
        (self.root / "bin").mkdir()
        (self.root / "docs/analysis/reports").mkdir(parents=True)
        elf = self.root / "target/aarch64-unknown-none/debug/tyrne-bsp-qemu-virt"
        elf.parent.mkdir(parents=True)
        elf.write_text("synthetic fixture, never executed")
        shutil.copy2(Path(__file__).with_name("perf-harness.sh"), self.root / "tools/perf-harness.sh")
        scripts = {
            "tools/run-qemu.sh": '''#!/usr/bin/env bash
set -euo pipefail
count=0
[[ ! -f "$PERF_COUNTER" ]] || count=$(cat "$PERF_COUNTER")
count=$((count + 1))
echo "$count" > "$PERF_COUNTER"
case "$PERF_SAMPLES" in
 zero) exit 1 ;;
 partial) [[ "$count" -ne 1 ]] || exit 1 ;;
esac
echo "tyrne: boot-to-end elapsed = $((count * 1000000)) ns"
''',
            "bin/qemu-system-aarch64": "#!/usr/bin/env bash\necho 'QEMU fixture version'\n",
            "bin/rustc": "#!/usr/bin/env bash\necho 'rustc fixture compiler'\n",
            "bin/rustup": "#!/usr/bin/env bash\necho 'nightly-fixture-aarch64-host (directory override)'\n",
            "bin/git": '''#!/usr/bin/env bash
case "$*" in
 'rev-parse HEAD') echo aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ;;
 'rev-parse --abbrev-ref HEAD') echo development ;;
 'status --porcelain --untracked-files=no')
   case "$PERF_STATE" in dirty) echo ' M tools/perf-harness.sh' ;; error) exit 42 ;; esac ;;
 *) exit 44 ;;
esac
''',
        }
        for relative, source in scripts.items():
            path = self.root / relative
            path.write_text(source)
            path.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.root / "bin") + os.pathsep + os.environ["PATH"],
                        PERF_COUNTER=str(self.root / "counter"), PERF_STATE="clean", PERF_SAMPLES="all")

    def run_harness(self, iterations=3):
        return subprocess.run(["/bin/bash", str(self.root / "tools/perf-harness.sh"),
                               f"--iterations={iterations}", "--report=fixture"], env=self.env,
                              text=True, capture_output=True, timeout=15)

    def report(self):
        reports = list((self.root / "docs/analysis/reports").glob("*-fixture.md"))
        self.assertEqual(len(reports), 1)
        return reports[0]

    def test_twenty_samples_metadata_and_band(self):
        run = self.run_harness(20)
        self.assertEqual(run.returncode, 0, run.stderr)
        report = self.report().read_text()
        for text in ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "rustc fixture compiler", "nightly-fixture-aarch64-host",
                     "QEMU fixture version", "| Iterations valid | 20 |", "| Tracked worktree | clean |",
                     "| p50 | 10,000,000 | 10.000 |"):
            self.assertIn(text, report)
        self.assertEqual(len(report.split("```text\n")[1].split("```", 1)[0].splitlines()), 20)

    def test_report_overwrite_refused_without_modification(self):
        self.assertEqual(self.run_harness().returncode, 0)
        report = self.report()
        before = report.read_bytes()
        run = self.run_harness()
        self.assertEqual(run.returncode, 1)
        self.assertIn("refusing to overwrite", run.stderr)
        self.assertEqual(report.read_bytes(), before)

    def test_dirty_and_unavailable_git_status_are_not_claimed_clean(self):
        for state, expected in (("dirty", "dirty"), ("error", "unknown")):
            self.env["PERF_STATE"] = state
            run = self.run_harness()
            self.assertEqual(run.returncode, 0, run.stderr)
            report = self.report()
            self.assertIn(f"| Tracked worktree | {expected} |", report.read_text())
            report.unlink()  # Private synthetic fixture only, never a repository report.

    def test_zero_samples_fail_without_report(self):
        self.env["PERF_SAMPLES"] = "zero"
        run = self.run_harness()
        self.assertEqual(run.returncode, 1)
        self.assertIn("zero valid samples", run.stderr)
        self.assertEqual(list((self.root / "docs/analysis/reports").iterdir()), [])

    def test_partial_samples_report_failed_count(self):
        self.env["PERF_SAMPLES"] = "partial"
        run = self.run_harness()
        self.assertEqual(run.returncode, 0, run.stderr)
        report = self.report().read_text()
        self.assertIn("| Iterations valid | 2 |", report)
        self.assertIn("| Iterations failed | 1 |", report)

    def test_failed_measurement_stays_failed_through_explicit_bash_tee(self):
        self.env["PERF_SAMPLES"] = "zero"
        run = subprocess.run(["/bin/bash", "--noprofile", "--norc", "-eo", "pipefail", "-c",
                              '"$1" --iterations=3 2>&1 | tee "$2"', "fixture",
                              str(self.root / "tools/perf-harness.sh"), str(self.root / "pipeline.log")],
                             env=self.env, text=True, capture_output=True, timeout=15)
        self.assertEqual(run.returncode, 1)
        self.assertIn("zero valid samples", (self.root / "pipeline.log").read_text())


if __name__ == "__main__":
    unittest.main()
