#!/usr/bin/env python3
"""Offline contract tests for the native ARM compiler-rejection assertion.

The actual compiler probe still runs in the native ARM job. These fixtures
control its two observed diagnostics, exit status, host and source preconditions.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "tools/test-ci-gates.sh",
    "userland/hello/src/main.rs",
    "userland/hello/build.rs",
    "userland/tyrne-user/src/lib.rs",
)
DUPLICATE = 'error[E0152]: found duplicate lang item `panic_impl`'
UNWIND = "error: unwinding panics are not supported without std"


class ArmProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tyrne ARM probe ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.tree = self.root / "source with spaces"
        self.bin = self.root / "bin"
        self.scratch = self.root / "scratch"
        for directory in (self.tree, self.bin, self.scratch):
            directory.mkdir()
        for name in FILES:
            target = self.tree / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        self.stub("git", """
import json, os, sys
assert sys.argv[1:] == ['ls-files', '-z']
sys.stdout.buffer.write(b''.join(p.encode() + b'\\0' for p in json.loads(os.environ['PROBE_FILES'])))
""")
        self.stub("rustc", """
import os, sys
assert sys.argv[1:] == ['-vV']
print('host: ' + os.environ['PROBE_HOST'])
""")
        self.stub("cargo", """
import json, os, pathlib, sys
assert sys.argv[1:] == ['clippy', '--workspace', '--exclude', 'tyrne-bsp-qemu-virt', '--all-targets', '--', '-D', 'warnings']
source = pathlib.Path('userland/hello/src/main.rs').read_text()
baseline = 'all(target_arch = "aarch64", target_os = "none")' in source
assert not baseline or source.count('all(target_arch = "aarch64", target_os = "none")') == 6
assert source.count('target_arch = "aarch64"') == 6
target = pathlib.Path(os.environ['CARGO_TARGET_DIR']).resolve()
assert target.parent == pathlib.Path.cwd().parent
assert target.parent.parent == pathlib.Path(os.environ['TMPDIR']).resolve()
assert os.environ['CARGO_TERM_COLOR'] == 'never'
receipt = pathlib.Path(os.environ['PROBE_RECEIPT'])
calls = json.loads(receipt.read_text()) if receipt.exists() else []
calls.append({'argv': sys.argv[1:], 'baseline': baseline})
receipt.write_text(json.dumps(calls))
print(os.environ['PROBE_BASE_DIAGNOSTIC'] if baseline else os.environ['PROBE_DIAGNOSTIC'], file=sys.stderr)
sys.exit(int(os.environ['PROBE_BASE_STATUS'] if baseline else os.environ['PROBE_STATUS']))
""")
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
                        TMPDIR=str(self.scratch), PROBE_FILES=json.dumps(FILES),
                        PROBE_HOST="aarch64-unknown-linux-gnu", PROBE_DIAGNOSTIC=DUPLICATE,
                        PROBE_STATUS="101", PROBE_BASE_STATUS="0", PROBE_BASE_DIAGNOSTIC="",
                        PROBE_RECEIPT=str(self.root / "cargo.json"))

    def stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/usr/bin/env python3\n" + body)
        path.chmod(0o755)

    def hashes(self):
        return {name: hashlib.sha256((self.tree / name).read_bytes()).hexdigest() for name in FILES}

    def run_probe(self, diagnostic=DUPLICATE, status=101, host="aarch64-unknown-linux-gnu",
                  args=("--arm-host",), calls=2):
        before = self.hashes()
        receipt = Path(self.env["PROBE_RECEIPT"])
        receipt.unlink(missing_ok=True)
        env = dict(self.env, PROBE_DIAGNOSTIC=diagnostic, PROBE_STATUS=str(status), PROBE_HOST=host)
        result = subprocess.run(["/bin/bash", str(self.tree / FILES[0]), *args], env=env,
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(before, self.hashes(), "source files changed")
        self.assertEqual([], list(self.scratch.iterdir()), "temporary tree leaked")
        observed = json.loads(receipt.read_text()) if receipt.exists() else []
        self.assertEqual(calls, len(observed), result.stdout + result.stderr)
        self.assertEqual([True, False][:calls], [call["baseline"] for call in observed])
        return result

    def test_both_observed_compiler_rejections(self):
        for diagnostic in (DUPLICATE, UNWIND):
            with self.subTest(diagnostic=diagnostic):
                result = self.run_probe(diagnostic)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn("exit 101; diagnostic " + diagnostic, result.stdout)

    def test_success_is_not_rejection_even_with_diagnostic(self):
        for diagnostic in (DUPLICATE, UNWIND, ""):
            with self.subTest(diagnostic=diagnostic):
                result = self.run_probe(diagnostic, status=0)
                self.assertEqual(1, result.returncode)
                self.assertIn("unexpectedly passed", result.stderr)

    def test_tool_failures_are_not_compiler_rejections(self):
        for status in (1, 2, 126, 127, 137):
            for diagnostic in (DUPLICATE, UNWIND):
                with self.subTest(status=status, diagnostic=diagnostic):
                    result = self.run_probe(diagnostic, status=status)
                    self.assertEqual(1, result.returncode)
                    self.assertIn("expected compiler exit 101", result.stderr)

    def test_unrelated_or_near_match_diagnostics_are_rejected(self):
        for diagnostic in ("error: network unavailable", "", "note: " + UNWIND,
                           DUPLICATE + " extra", "prefix " + DUPLICATE):
            with self.subTest(diagnostic=diagnostic):
                result = self.run_probe(diagnostic)
                self.assertEqual(1, result.returncode)
                self.assertIn("without a recognized cfg-regression diagnostic", result.stderr)

    def test_host_refusal_precedes_cargo(self):
        result = self.run_probe(host="x86_64-unknown-linux-gnu", calls=0)
        self.assertEqual(1, result.returncode)
        self.assertIn("requires a native aarch64 Rust host", result.stderr)

    def test_apple_arm_host(self):
        result = self.run_probe(host="aarch64-apple-darwin")
        self.assertEqual(0, result.returncode, result.stderr)

    def test_cfg_anchor_drift_precedes_cargo(self):
        path = self.tree / FILES[1]
        source = path.read_text()
        path.write_text(source.replace('all(target_arch = "aarch64", target_os = "none")',
                                       'target_arch = "aarch64"', 1))
        result = self.run_probe(calls=0)
        self.assertEqual(1, result.returncode)
        self.assertIn("expected exactly six hello target predicates", result.stderr)

    def test_copy_failure_precedes_cargo_and_cleans_up(self):
        self.env["PROBE_FILES"] = json.dumps([*FILES, "missing-tracked-file"])
        result = self.run_probe(calls=0)
        self.assertNotEqual(0, result.returncode)

    def test_cli_usage(self):
        for args, expected in (((), 2), (("--bogus",), 2), (("--arm-host", "extra"), 2),
                               (("--help",), 0)):
            with self.subTest(args=args):
                result = self.run_probe(args=args, calls=0)
                self.assertEqual(expected, result.returncode)
                self.assertIn("Usage:", result.stderr)

    def test_failing_baseline_never_reaches_mutation_assertion(self):
        for status in (1, 101, 127):
            for diagnostic in (DUPLICATE, UNWIND, "error: unrelated failure"):
                with self.subTest(diagnostic=diagnostic, status=status):
                    self.env.update(PROBE_BASE_STATUS=str(status), PROBE_BASE_DIAGNOSTIC=diagnostic)
                    result = self.run_probe(calls=1)
                    self.assertEqual(1, result.returncode)
                    self.assertIn("unmodified ARM clippy baseline did not pass", result.stderr)

    def test_empty_diagnostic_is_refused_before_negative_command(self):
        script = self.tree / FILES[0]
        source = script.read_text()
        anchor = "run_negative '" + DUPLICATE + "'"
        self.assertEqual(1, source.count(anchor))
        script.write_text(source.replace(anchor, "run_negative ''"))
        result = self.run_probe(calls=1)
        self.assertEqual(1, result.returncode)
        self.assertIn("requires a nonempty diagnostic", result.stderr)


if __name__ == "__main__":
    unittest.main()
