#!/usr/bin/env python3
"""Challenge the real smoke entry point with synthetic and private guest traces."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parent.parent
GREETING = "hello from userspace"
EXIT = "tyrne: userspace task exited"
COMPLETE = "tyrne: all tasks complete"
FAULTS = (
    "tyrne panic", "Translation fault", "Permission fault", "Data Abort",
    "Prefetch Abort", "Unallocated Instruction",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--real", action="store_true", help=(
        "also build/boot three private kernel variants; requires pinned Rust, "
        "llvm-tools, aarch64-unknown-none and QEMU"))
    parser.add_argument("--artifact-dir", type=Path, help=(
        "retain results/traces in this NEW directory; existing paths are refused"))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="tyrne smoke gates ") as temp:
        scratch = Path(temp)
        artifacts = args.artifact_dir.resolve() if args.artifact_dir else scratch / "results"
        if artifacts.exists():
            parser.error(f"artifact directory already exists: {artifacts}")
        artifacts.mkdir(parents=True, exist_ok=False)
        results = {
            "source_sha": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
            "tracked_worktree_dirty": bool(subprocess.check_output(
                ["git", "status", "--porcelain", "--untracked-files=no"], cwd=REPO)),
            "smoke_sha256": hashlib.sha256((REPO / "tools/smoke.sh").read_bytes()).hexdigest(),
            "real_requested": args.real,
            "cases": [],
            "completed": False,
        }

        def save():
            (artifacts / "results.json").write_text(json.dumps(results, indent=2) + "\n")

        def command(argv, cwd, env, log):
            with log.open("w") as output:
                return subprocess.run(argv, cwd=cwd, env=env, stdout=output,
                                      stderr=subprocess.STDOUT, check=False).returncode

        def smoke(name, profile, env, elf, kind, expected, diagnostic="", cwd=REPO,
                  expected_markers=None):
            trace_dir = scratch / name
            trace_dir.mkdir()
            env = dict(env, TMPDIR=str(trace_dir))
            argv = [str(cwd / "tools/smoke.sh"), "--int", "--timeout", "5"]
            if profile == "release":
                argv.append("--release")
            argv.append(str(elf))
            output = artifacts / (name + ".output.log")
            rc = command(argv, cwd, env, output)
            traces = list(trace_dir.glob("tyrne-smoke.*.log"))
            if len(traces) != 1:
                raise RuntimeError(f"{name}: expected one raw trace, got {len(traces)}")
            shutil.copyfile(traces[0], artifacts / (name + ".trace.log"))
            text = output.read_text()
            raw = traces[0].read_text()
            observed = {marker: marker in raw.splitlines() for marker in (GREETING, EXIT, COMPLETE)}
            passed = rc == expected and (not diagnostic or diagnostic in text)
            if expected_markers is not None:
                passed = (passed and observed == expected_markers and
                          not any(fault in raw for fault in FAULTS))
            results["cases"].append({
                "name": name, "kind": kind, "profile": profile, "exit": rc,
                "expected_exit": expected, "diagnostic": diagnostic, "passed": passed,
                "observed_markers": observed,
            })
            save()
            if not passed:
                raise RuntimeError(f"{name}: expected exit {expected} and {diagnostic!r}; "
                                   f"got {rc}. See {output}")
            print(f"PASS: {name} ({kind}; exit {rc})", flush=True)

        save()
        try:
            env = os.environ.copy()
            env.pop("QEMU_SMP", None)
            stub_dir = scratch / "bin"
            stub_dir.mkdir()
            stub = stub_dir / "qemu-system-aarch64"
            stub.write_text('#!/usr/bin/env bash\nset -euo pipefail\ncat "$SMOKE_FIXTURE"\n')
            stub.chmod(0o755)
            fixture_env = dict(env, PATH=str(stub_dir) + os.pathsep + env["PATH"])
            elf = scratch / "fixture kernel.elf"
            elf.touch()
            fixture = scratch / "fixture.trace"
            fixture_env["SMOKE_FIXTURE"] = str(fixture)

            def synthetic(name, profile, lines, expected=1, diagnostic=""):
                fixture.write_text("\n".join(lines) + "\n")
                smoke(name, profile, fixture_env, elf, "synthetic trace fixture",
                      expected, diagnostic)

            for profile in ("debug", "release"):
                markers = [GREETING, EXIT, COMPLETE] if profile == "debug" else [EXIT, COMPLETE]
                synthetic(profile + "-positive", profile, markers, expected=0)
                for index, marker in enumerate(markers):
                    synthetic(f"{profile}-missing-{index}", profile,
                              [m for m in markers if m != marker],
                              diagnostic=f"FAIL: '{marker}' marker missing")
                for index, fault in enumerate(FAULTS):
                    synthetic(f"{profile}-fault-{index}", profile, markers + [fault],
                              diagnostic="FAIL: a panic / CPU-fault class appeared")
            synthetic("release-greeting", "release", [GREETING, EXIT, COMPLETE],
                      diagnostic="FAIL: release trace contains forbidden userspace greeting")

            if args.real:
                tree = scratch / "tree"
                tree.mkdir()
                tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=REPO)
                for raw in tracked.split(b"\0"):
                    if raw:
                        relative = Path(os.fsdecode(raw))
                        destination = tree / relative
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(REPO / relative, destination)
                private_env = dict(env, CARGO_TARGET_DIR=str(scratch / "target"),
                                   CARGO_TERM_COLOR="never", TMPDIR=str(scratch))
                source = tree / "bsp-qemu-virt/src/main.rs"
                original = source.read_text()

                def replace_once(text, old, new):
                    if text.count(old) != 1:
                        raise RuntimeError(f"private mutation anchor changed: {old!r}")
                    return text.replace(old, new, 1)

                start = '            sched\n                .add_user_task('
                end = '                .expect("add_user_task (EL0 hello) failed: queue full or arena exhausted");'
                omitted = replace_once(original, start,
                                       '            if core::hint::black_box(false) {\n' + start)
                omitted = replace_once(omitted, end, end + '\n            }')
                completion = 'console.write_bytes(b"tyrne: all tasks complete\\n");'
                variants = (
                    ("real-omit-el0", "debug", omitted,
                     f"FAIL: '{EXIT}' marker missing"),
                    ("real-omit-completion", "debug", replace_once(original, completion,
                     'console.write_bytes(b"tyrne: private omitted completion\\n");'),
                     f"FAIL: '{COMPLETE}' marker missing"),
                    ("real-release-greeting", "release", replace_once(original, completion,
                     'console.write_bytes(b"hello from userspace\\ntyrne: all tasks complete\\n");'),
                     "FAIL: release trace contains forbidden userspace greeting"),
                )
                for name, profile, mutated, diagnostic in variants:
                    source.write_text(mutated)
                    build = [str(tree / "tools/build-userland.sh")]
                    if profile == "release":
                        build.append("--release")
                    for label, argv in (("userland", build),
                                        ("kernel", ["cargo", "kernel-build"] +
                                         (["--release"] if profile == "release" else []))):
                        log = artifacts / f"{name}.{label}.log"
                        if command(argv, tree, private_env, log) != 0:
                            raise RuntimeError(f"{name}: private {label} build failed; see {log}")
                    kernel = scratch / "target/aarch64-unknown-none" / profile / "tyrne-bsp-qemu-virt"
                    expected_markers = {GREETING: True, EXIT: True, COMPLETE: True}
                    if name == "real-omit-el0":
                        expected_markers.update({GREETING: False, EXIT: False})
                    elif name == "real-omit-completion":
                        expected_markers[COMPLETE] = False
                    smoke(name, profile, private_env, kernel, "actual private kernel variant",
                          1, diagnostic, cwd=tree, expected_markers=expected_markers)
                source.write_text(original)
            results["completed"] = True
            print(f"PASS: {len(results['cases'])} smoke gate cases; "
                  "synthetic traces and actual guests are labeled separately", flush=True)
        finally:
            save()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
