# Code review 2026-10-16 — PR49 footprint prevention

Both different fresh complementary rounds are complete. R1's one Low root-resolution group and R2's one Medium commit-graph false-green group are fixed and independently verified on committed sources by both contexts in their respective rounds. Zero unresolved findings. All eight complete initial/fix reports below preserve their original verdicts, severity, discovery attribution, actual executions and read limits.

- **Change:** `development`, `433d42d3686b79d0b110053d83358bf864061523..588edbfaaa6dfdffafc09e97ddadaac006313fcb`; implementation `2d83602`, R1 correction `fb9e4b9`, R2 correction `588edbf`.
- **Reviewer:** Codex coordinator with four separately instantiated fresh contexts; R1 CODE/operational integrity used GPT-6.1-sol/GPT-6-astra, R2 reversed those assignments, all with high effort.
- **Risk class:** Ordinary tooling with consequential Git-history/storage boundaries.
- **Security-review cross-reference:** Formal runtime trigger N/A; complementary adversarial Git/CI integrity passes remain separately attributable.

## Correctness

The separate offline/read-only guard checks indexed objects and all complete HEAD-history trees, including committed-then-deleted violations and every merge parent. Inclusive limits are 1 MiB per blob, 512 KiB non-Markdown reports per tree and 128 KiB per catalog pair. Identical blobs count per path; Gitlinks are external identities and symlink target text is stored. Shallow/promisor/missing/unmerged/graft inputs fail closed; ambient alternate Git state and replacement/commit-graph views cannot substitute for actual ancestry.

PRC1-01=PIR1-01 (Low) closes at `fb9e4b9`: Python3.9 symlink-loop root failures become structured input errors. PIR2-01 (Medium) closes at `588edbf`: derived commit-graph cache metadata is disabled. The second discovery belongs to integrity R2; CODE R2's original approval remains preserved as the earlier limited discovery result. Both corrections have actual independent failing-before and passing-after observations on both supported runtimes. No broader object-authenticity or runtime-safety proof is claimed.

## Style

Small standard-library production code, meaningful temporary-Git tests and English conventional commits follow Accepted ADR-0044. The binary cache fixture is confined to disposable tests and follows the documented Git format; supplemental SHA-256-format variants pass. No runtime, unsafe, dependency or existing parser source change.

## Test coverage

At `588edbf`, Python 3.9.6 and 3.13.14 each pass 23 footprint methods. The guard reports 501 indexed blobs / 479 historical trees / 2971 unique blobs / zero findings; the corpus reports 406 files / 7302 targets / 1276 fragments / zero findings. Existing 161 navigation / 124 metadata methods pass on both at `fb9e4b9` in each fresh R2 initial; their six files are unchanged by the correction. Complete reports distinguish these exact sources. Independent probes additionally cover second-parent ancestry, sparse/linked/packed/SHA-256 repositories, missing objects/Git, read-only inventories and suppressed external helpers; no packet-capture or OS-sandbox claim.

## Documentation

Guide, standards and common review skill document storage limits, invalid-input/status behavior, complete-history scope, exclusions, original execution identities and durable recovery. Original initials are not rewritten into approvals; complete post-freeze fix/peer reconciliations are separate snapshots. Temporary scratch paths in originals describe execution locations; the committed regression and complete canonical observations retain the reproducible essential contract.

## Integration

Full history and two failing steps are added only to the existing lint job. Pinned checkout, unpersisted credentials, `contents: read`, seven jobs, six required app-15368 contexts and protection remain unchanged. All six existing checker/fixture sources and tracked Rust bytes equal original `97dbcd1`. The guard preserves check-docs.py's offline/no-Git contract. T-056 remains In Progress until exact-source hosted/ordinary remote-clone gates; no Done, merge, remote-ref replacement or future hosted success is asserted here.

## Verdict

**Approve — reviewed prevention implementation.** Both required fresh rounds and actual committed-fix/peer reconciliation are complete. Two unique groups closed (one Low, one Medium), zero unresolved. Proceed to final candidate validation and the already-approved exact development lease/publication/hosted/clone sequence. Maintainer PR/SECURITY wording review and merge remain separate.

## Preserved original reports

Complete verbatim UTF-8 snapshots are enclosed as inert Markdown, with independently checked digests. No original is overwritten or presented as a later execution.

### prevention-r1-code.md

SHA-256: `8610cdcf47e5ad403c994de95c9cd01f883e1f24722f5ff5779d65f489cc8174`.

````````markdown
# Code review 2026-10-16 — PR49 prevention R1 CODE

- **Change:** `433d42d3686b79d0b110053d83358bf864061523..2d83602f92e6afddb46d32f9d7b14eb6021aec77` on `development`.
- **Reviewer:** Codex independent R1 CODE agent, all five roles executed sequentially.
- **Date:** 2026-10-16.
- **Risk class:** Ordinary repository tooling.
- **Security-review cross-reference:** n/a; no capability/IPC/syscall/memory/scheduler/boot/crypto/unsafe or dependency change.
- **Source stages:** preflight `803ff08e25d52310137e69007fdb5b36e513c49a`; implementation and independently tested HEAD `2d83602f92e6afddb46d32f9d7b14eb6021aec77`.
- **Independence:** No peer report or peer finding was read before this initial report froze. The assignment disclosed the author's previously corrected graft regression; it was independently reproduced as described below.

## Correctness

**PRC1-01 — Low, requested correction: Python 3.9 root-resolution errors escape the CLI input boundary.** `tools/check-repo-footprint.py:73` calls `Path.resolve()`, while the handler at `tools/check-repo-footprint.py:157` omits `RuntimeError`. On supported Python 3.9.6, passing a self-referential symlink as `--root` raises `RuntimeError: Symlink loop from ...`; the command exits **1**, prints no JSON and emits a traceback. The documented contract at `docs/guides/ci.md:205` reserves exit 1 for policy findings and exit 2 for invalid/unverifiable input. Python 3.13.14 returns the intended exit 2/input JSON for the same fixture. This is a bounded CLI/portability defect, not a storage-policy bypass.

Convert the root-resolution failure into `InputError` (or narrowly handle the supported pathlib exception at that boundary), and add a real symlink-loop-root fixture asserting exit 2, parseable `code: input` JSON and no traceback on both supported runtimes. Preserve exit 1 for actual footprint findings.

Independent reproduction, executed from the repository root with each interpreter:

```sh
python3 - <<'PY'
from pathlib import Path
import subprocess, sys, tempfile
script = Path('tools/check-repo-footprint.py').resolve()
with tempfile.TemporaryDirectory(prefix='tyrne-review-root-') as directory:
    root = Path(directory) / 'cycle'
    root.symlink_to('cycle')
    result = subprocess.run([sys.executable, str(script), '--root', str(root), '--json'],
                            capture_output=True, text=True)
    print(sys.version.split()[0], result.returncode, repr(result.stdout), repr(result.stderr))
PY
```

The same heredoc was run with `/opt/homebrew/bin/python3.13`. Actual results: 3.9.6 → exit 1, empty stdout, traceback ending in `RuntimeError`; 3.13.14 → exit 2, one JSON input finding (`Root is not an existing directory`), empty stderr.

No additional confirmed accounting/history defect. Inclusive blob limits, per-path report totals, catalog-pair totals, historical add-then-delete rejection, unique-size caching, deterministic source selection and NUL-delimited path handling match the approved contract. Replacement objects are suppressed and legacy graft files rejected. Missing required objects fail closed. Gitlinks are intentionally excluded and symlink target text counted.

Capability semantics, kernel fault containment and unsafe discipline are not applicable to the scoped files. No production Rust changed.

## Style

No additional finding. The implementation uses Python 3.9-compatible standard-library APIs and a readable separation between Git access, entry decoding, snapshot accounting and CLI presentation. Tree inventories stream one snapshot at a time; blob sizes are cached by identity. Existing Rust formatter/Clippy rules do not apply to the new Python files. Both scoped commit subjects and ADR-0043/0044 trailers follow the repository convention.

## Test coverage

The 21 committed methods exercise real disposable Git repositories through the public CLI: exact/over boundaries, duplicate-content path accounting, historical violations, catalog pairing, staged versus worktree/untracked content, symlinks/Gitlinks, control-character filenames, deterministic JSON/text, invalid roots, unmerged index, missing blob, shallow/promisor inputs, ambient Git variables, replacement objects, grafts and script-relative defaults. All pass on both local runtimes. The missing category is PRC1-01's Python 3.9 root-resolution exception.

Six independent supplemental temporary-Git probes passed: linked worktree with a deleted oversized historical blob → exit 1/footprint-blob; sparse index → exit 0; removed parent commit object → exit 2/input; Git unavailable with empty PATH → exit 2/input; packed history containing a deleted oversized blob → exit 1/footprint-blob; SHA-256 object-format repository with oversized staged blob → exit 1/footprint-blob and a 64-character HEAD identity. These used the committed fixture helpers through `runpy.run_path('tools/test-repo-footprint.py')`; all mutations remained in disposable repositories.

The author-disclosed graft fix was independently checked using a disposable copy of the current checker with only lines 81–83 removed. A fixture committed an oversized blob, deleted it in the next commit, then grafted HEAD into a root. That isolated prior behavior returned exit 0; the committed candidate returned exit 2/input. This is an actual independent regression observation, not a claim that a historical commit was executed.

No kernel/QEMU run was necessary for this Python/documentation-only unit.

## Documentation

No additional finding beyond PRC1-01's CLI contract mismatch. The CI guide describes root defaults, statuses, index/history scope, aggregate accounting, excluded refs/reflogs, complete-input requirements, Gitlinks/symlinks and limits of the result. Standards and the common review skill ground retention rules in Accepted ADR-0044 while preserving ADR-0043 and original evidence identities. Task/preflight wording distinguishes the earlier release pointer from step-six guidance; no Done or hosted-delivery claim is introduced.

## Integration

The workflow diff adds `fetch-depth: 0` only to the existing lint checkout and adds two ordinary failing steps. `persist-credentials: false`, top-level `contents: read`, job names, six required context/app bindings and the versioned protection definition remain unchanged. No dependency or administrative credential is added. Existing docs command/modules have no scoped source change; an actual run with empty PATH still passes, independently confirming that this unit introduces no Git executable dependency into that command.

Executed evidence at the exact committed candidate:

| Command | Actual result |
|---|---|
| `python3 --version`; `git --version` | Python 3.9.6; Git 2.54.0 (Apple Git-157) |
| `python3 tools/test-repo-footprint.py` | 21 methods, OK |
| `/opt/homebrew/bin/python3.13 tools/test-repo-footprint.py` | 21 methods, OK; interpreter independently identified as 3.13.14 |
| `python3 tools/check-repo-footprint.py --json` | Exit 0; HEAD `2d83602f92e6afddb46d32f9d7b14eb6021aec77`; 501 indexed blobs / 477 historical trees / 2964 unique blobs / zero findings |
| `python3 tools/test-check-docs.py` | 161 methods, OK |
| `python3 tools/test-docs-metadata.py` | 124 methods, OK |
| `python3 tools/check-docs.py` | 406 Markdown files / 7302 local targets / 1276 fragments / zero findings |
| `compile(Path(name).read_bytes(), name, 'exec')` for both new Python files | Python 3.9 syntax passes without bytecode writes |
| `subprocess.run([sys.executable, 'tools/check-docs.py'], env=dict(os.environ, PATH=''), ...)` | Exit 0, same 406/7302/1276/zero result |
| `git diff --check 433d42d3686b79d0b110053d83358bf864061523 2d83602f92e6afddb46d32f9d7b14eb6021aec77` | Exit 0, no output |
| `git status --short`; `git rev-parse HEAD` | Clean worktree; exact candidate unchanged |

## Verdict

**Request changes** for the single Low PRC1-01 input-contract/portability defect. No other verified scoped finding remains. The correction should be independently verified on a committed fix before this R1 finding closes.

Reading and execution limits: read AGENTS.md, full CLAUDE.md, current state, approved cleanup description, Accepted ADR-0044, relevant governing ADR/standards and both review skills/master plan. Read the current PR49 description through `gh pr view 49 --repo HodeTech/Tyrne --json title,body,headRefName,headRefOid,baseRefName` before tests/implementation; its published head is still original `97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4`, distinct from this local unit. Read the new fixture file before implementation and reviewed the complete scoped diff. This report does not claim a wholesale semantic reread of old archived sources, every historical ADR or prior peer reports. No new hosted CI, remote clone, protection API proof, lease publication, archive-recovery audit or final-candidate delivery is claimed; those later gates remain separate. No repository file/ref/commit/remote mutation or private-note access occurred. Only this assigned external report and its digest are persisted; scratch fixtures were temporary.
````````

### prevention-r1-integrity.md

SHA-256: `35359b993990d8e6076c0caec0ee943ca7d2ef57fe2ccdb61ed594f5aa9b27d8`.

````````markdown
# Code review 2026-10-16 — PR49 prevention R1 operational integrity

- **Change:** `433d42d3686b79d0b110053d83358bf864061523..2d83602f92e6afddb46d32f9d7b14eb6021aec77` (preflight `803ff08` and prevention implementation).
- **Reviewer:** Codex independent operational-integrity reviewer, `/root/cleanup_prevention_r1_integrity`.
- **Risk class:** Ordinary tooling. No runtime/capability/IPC/memory/unsafe implementation change.
- **Security-review cross-reference:** n/a; adversarial operational checks here are CODE review, not formal runtime security review.
- **Freeze:** This initial report was written without reading the complementary R1 review or receiving its findings. Coordinator supplied source identities and the second interpreter path only.
- **Authority:** Accepted ADR-0044 and approved cleanup plan; no broad exclusions, dependency addition, ref mutation, publication or merge authorized by this verdict.

## Correctness

**PIR1-01 — Low — Python 3.9 symlink-loop roots escape the input-error boundary.** `tools/check-repo-footprint.py:73` calls `Path.resolve()`; the exception boundary at `tools/check-repo-footprint.py:157` omits `RuntimeError`. On supported Python 3.9.6, passing a self-referential symlink as `--root` exits 1 with a traceback and empty stdout instead of exit 2 with the documented JSON input finding. Python 3.13.14 correctly returns exit 2. This remains fail-closed (no false green), but breaks the stated machine-readable CLI/error classification contract and supported-runtime consistency. Catch/convert the path-resolution failure at the path boundary and add a temporary symlink-loop regression asserting exit 2, JSON `input`, and no traceback on both runtimes.

Reproduction from the project root, creating only temporary filesystem content:

```sh
/usr/bin/python3 - <<'PYCODE'
from pathlib import Path
import subprocess
import tempfile
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory) / "loop"
    root.symlink_to(root)
    result = subprocess.run([
        "/usr/bin/python3", "tools/check-repo-footprint.py",
        "--root", str(root), "--json",
    ], capture_output=True)
    print(result.returncode, result.stdout.decode(), result.stderr.decode())
PYCODE
```

Actual: exit 1, empty stdout, traceback ending `RuntimeError: Symlink loop from ...`. Identical probe using `/opt/homebrew/bin/python3.13` returns exit 2 and an `input` finding, `Root is not an existing directory`.

The core storage behavior otherwise checks out: index object identities, inclusive byte boundaries, per-path aggregation despite blob deduplication, per-snapshot historical report/catalog totals, all parents of HEAD ancestry, and stored symlink text. Deduplicating identical historical trees is safe for these content/path predicates. Gitlinks are expressly outside parent-repository blob accounting. Replacement refs are suppressed, graft files rejected (including common-dir grafts in a linked worktree), and shallow/promisor state fails closed. Missing/unmerged objects do not become success. The implementation issues read commands only and disables optional locks/fsmonitor; a disposable repository's complete file-content hash inventory was identical before and after the guard.

The already-fixed legacy-graft false green was discovered by the author before this review; the committed fixture and current rejection were inspected/run here. This report does not relabel it as an independent reviewer discovery or claim to have rerun the author's original failing source.

## Style

No finding. Small standard-library implementation, explicit limits/error boundary, deterministic ordering and NUL-safe record handling fit the existing tooling. Conventional English commit messages reference ADR-0043/0044. No Rust formatting, unsafe, dependency or source-style change is present. Avoid expanding this fix into unrelated tooling refactors.

## Test coverage

The 21 real temporary-Git methods cover inclusive limits, deleted oversized history, report/catalog aggregates, staged versus worktree bytes, symlinks/Gitlinks, control-character paths, JSON determinism, missing objects, unmerged index, shallow/partial/promisor rejection, replacement/graft suppression, ambient GIT state and script-relative defaults. Both supported local interpreters pass all 21. Missing category: PIR1-01's Python-version-sensitive root resolution failure.

Additional independent real-Git probes passed:

- A merge whose second-parent ancestry introduced then removed an oversized blob: exit 1 with `footprint-blob` attributed to the offending ancestor.
- Sparse checkout with a sparse index and an oversized blob outside the materialized paths: exit 1 with `footprint-blob`.
- Detached linked worktree with common `.git/info/grafts`: exit 2 with the graft input finding.
- Complete before/after file SHA-256 inventory of a disposable repository (including its Git metadata): unchanged after a failing oversized-index scan.
- Promisor config with an external-protocol URL: exit 2 at preflight; no fetch command is present in the tool. This is an execution/code-path check, not packet capture or an OS network sandbox proof.

Fixtures were run in disposable repositories; this reviewer did not switch, commit, stage, edit or create project refs. No hostile temporary fixture entered project history.

## Documentation

No separate finding beyond PIR1-01's implementation mismatch with the documented exit/JSON contract. The guide clearly distinguishes index/history from unstaged/untracked/reflog/other-branch content, documents per-pair/per-tree bounds and source attribution, and keeps semantic/authenticity claims outside the guard. Guidance preserves historical identities, canonical verdicts, independent archive recovery and exact-path reviewed future exceptions. No directory bypass or new dependency was introduced.

Reading order: full CLAUDE/AGENTS and live pointer; approved cleanup plan, Accepted ADR-0044 and live PR49 description before tests; tests before implementation. Governance/standards reading focused on ADR-0013/0025/0040/0043/0044 and the code-review master plan, both invoked skills, documentation/testing/infrastructure/code/security/release/commit/unsafe/error/principle standards. Large initial combined output was truncated; load-bearing ADR-0025/0040/0043 and infrastructure were reread separately. This is not a claimed exhaustive semantic reread of every old ADR, unrelated standard, archive payload or historical review. The live PR description still names original published `97dbcd1`; it was treated as the historical remote stage, with the approved cleanup record supplying this local unit's scope.

## Integration

The only workflow changes add full history to the existing lint checkout and two failing footprint steps. Checkout remains SHA-pinned, `persist-credentials: false`; top-level `contents: read` and required job names are unchanged. The versioned six required contexts retain app ID 15368. No administrative credential or branch-protection mutation is added. The merge-second-parent probe supports checking the synthetic PR merge ancestry; actual final-source hosted execution remains the coordinator's pending gate.

Actual commands/results at reviewed HEAD:

| Command | Actual result |
|---|---|
| `git rev-parse HEAD`; `git status --porcelain=v1` | Exact `2d83602f92e6afddb46d32f9d7b14eb6021aec77`; clean |
| `gh pr view 49 --json title,body,headRefOid,baseRefName` | Open description retrieved; remote head original `97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4`, base main |
| `/usr/bin/python3 tools/test-repo-footprint.py` (also PATH `python3`) | 21 passed, Python 3.9.6 |
| `/opt/homebrew/bin/python3.13 tools/test-repo-footprint.py` | 21 passed, Python 3.13.14 |
| Each interpreter with `tools/test-check-docs.py` | 161 passed each |
| Each interpreter with `tools/test-docs-metadata.py` | 124 passed each |
| Each interpreter with `tools/check-docs.py` | 406 Markdown files / 7302 local targets / 1276 fragments / 0 findings each |
| Each interpreter with `tools/check-repo-footprint.py --json` | 501 indexed blobs / 477 historical trees / 2964 unique blobs / 0 findings each |
| `git diff --exit-code 97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4 2d83602 -- tools/check-docs.py tools/docs_audit.py tools/docs_consistency.py tools/docs_metadata.py tools/test-check-docs.py tools/test-docs-metadata.py '*.rs'` | Exit 0: six existing checker/test files and all tracked Rust bytes equal |
| In-memory `compile(path.read_bytes(), str(path), 'exec')` for both new scripts | Passed on Python 3.9.6; no bytecode written |
| `git diff --check 433d42d..2d83602` | Passed |

Git was `2.54.0 (Apple Git-157)` on macOS. No Linux hosted run, QEMU/Rust build, remote clone, archive semantic re-review, live protection API revalidation, or final lease/publication was performed by this reviewer. Those are separate delivery gates; no claim here promotes tasks to Done or certifies final hosted readiness. The executable Rust is unchanged; runtime/QEMU retesting is not evidence needed for the Python path-resolution finding. Report/index integration is delegated to the sole repository writer under this review assignment; the complete initial and digest are stored outside Git.

## Verdict

**Request changes.** Fix and independently verify **PIR1-01 (Low)** before closing this review round. There is no observed false-green storage result or runtime security finding. The required correction is narrowly scoped to the documented invalid-input/JSON contract on Python 3.9; two fresh rounds and final publication/hosted/clone checks remain separate gates.
````````

### prevention-r1-code-fix.md

SHA-256: `199d1c9894a9bcb2635a21505057caeddd31c0bce481287126d09dbca7b594d6`.

````````markdown
# Code review 2026-10-16 — PR49 prevention R1 CODE committed-fix verification

- **Change:** `2d83602f92e6afddb46d32f9d7b14eb6021aec77..fb9e4b9560908067b3cd97aa205ef36223bda316`, development.
- **Reviewer:** Original independent R1 CODE reviewer; actual follow-up verification, all five roles.
- **Date:** 2026-10-16.
- **Risk class:** Ordinary tooling.
- **Security-review cross-reference:** n/a; no kernel/security-sensitive implementation change.
- **Initial preserved:** `prevention-r1-code.md`, SHA-256 `8610cdcf47e5ad403c994de95c9cd01f883e1f24722f5ff5779d65f489cc8174`; original **Request changes**, Low PRC1-01 and reproduction remain unchanged.
- **Peer reconciliation authority:** Both initials froze before disclosure. Only afterward, on coordinator authorization, this reviewer read the complete peer initial `prevention-r1-integrity.md` and independently confirmed its SHA-256 `35359b993990d8e6076c0caec0ee943ca7d2ef57fe2ccdb61ed594f5aa9b27d8`.

## Correctness

**PRC1-01 / PIR1-01 — Low — Closed at fb9e4b9560908067b3cd97aa205ef36223bda316.** The committed correction at `tools/check-repo-footprint.py:73` narrowly catches `RuntimeError` from root resolution and converts it to the existing `InputError` boundary. It leaves accounting, ancestry traversal, ordinary policy exit 1 and other exception paths unchanged.

Actual direct CLI verification with a temporary self-referential symlink and `--root <loop> --json`:

- `/usr/bin/python3` (3.9.6): exit 2; one `input` finding, message `Root cannot be resolved`; empty stderr.
- `/opt/homebrew/bin/python3.13` (3.13.14): exit 2; one `input` finding, message `Root is not an existing directory`; empty stderr.

Both outputs parse as JSON and contain no traceback. The contract requires the same error category/status, not identical OS/interpreter error wording. No new correctness finding.

Peer reconciliation: the peer's PIR1-01 and this reviewer's PRC1-01 describe the same Python 3.9 `Path.resolve()` exception, same documented CLI boundary and same remedy. They form one unique Low group. The full peer report contains no additional finding or conflicting scoped verdict. Its complementary probes are peer-attributed evidence, not relabeled as this reviewer's own executions.

## Style

Clean. The catch is confined to the operation known to raise this version-specific exception, with a useful Python-version comment. It avoids broad suppression of unrelated runtime errors. The conventional fix commit references ADR-0044; no dependency, unsafe or Rust-style change.

## Test coverage

The new `test_symlink_loop_root_returns_structured_input_error` uses the public CLI and real temporary symlink, asserting exit 2, parsed input code and absence of traceback. All **22** committed footprint methods pass on both supported local runtimes, retaining existing blob/report/catalog, deleted-history, incomplete-input and ancestry controls.

The new regression was independently tested against the prior checker: retrieve `git show 2d83602f92e6afddb46d32f9d7b14eb6021aec77:tools/check-repo-footprint.py`, write it beside the current committed fixture file in a temporary `tools/` directory, then execute `python3 <temporary-tools>/test-repo-footprint.py FootprintTests.test_symlink_loop_root_returns_structured_input_error`. Actual result: exit 1, one failure, `AssertionError: 1 != 2`, exposing the prior traceback. The identical committed method passes in the fixed 22-method suite. No project file or ref was modified for this before/after check.

## Documentation

Clean. The appended prevention-R1 correction checkpoint preserves both original Low IDs, original failed-before behavior and remaining review/delivery gates. The existing documented exit-2/JSON contract now matches Python 3.9 behavior. The checkpoint does not prematurely claim this verification or R2 completion. No historical initial verdict or source identity was rewritten.

## Integration

The three-file correction affects only root exception handling, its fixture and the execution checkpoint. CI wiring, required names/app bindings, permissions, limits, existing docs parser and production Rust are unchanged.

Actual commands/results at the committed fix:

| Command | Actual result |
|---|---|
| `git rev-parse HEAD fb9e4b9`; `git status --short` | Both resolve to `fb9e4b9560908067b3cd97aa205ef36223bda316`; clean |
| `python3 tools/test-repo-footprint.py` | 22 methods, OK |
| `/opt/homebrew/bin/python3.13 tools/test-repo-footprint.py` | 22 methods, OK |
| `python3 tools/check-repo-footprint.py --json` | Exit 0; exact fixed HEAD; 501 indexed blobs / 478 historical trees / 2967 unique blobs / zero findings |
| `/opt/homebrew/bin/python3.13 tools/check-repo-footprint.py --json` | Same fixed HEAD, counts, limits and zero findings |
| `python3 tools/check-docs.py` | 406 Markdown files / 7302 local targets / 1276 fragments / zero findings |
| `/opt/homebrew/bin/python3.13 tools/check-docs.py` | Same corpus result |
| In-memory `compile(Path(name).read_bytes(), name, 'exec')` for both scripts | Python 3.9 syntax passed without bytecode writes |
| `git diff --check 2d83602f92e6afddb46d32f9d7b14eb6021aec77 fb9e4b9560908067b3cd97aa205ef36223bda316` | Passed, no output |

The existing 161/124 documentation fixture suites were executed in the preserved initial review; they were not rerun for this narrowly scoped correction because their implementation and fixtures are unchanged. The actual current full corpus was rerun on both interpreters. No Rust/QEMU run is needed for this correction.

## Verdict

**Approve the committed R1 correction.** Closed unique groups: **1**, PRC1-01 = PIR1-01 (Low). Open verified scoped groups: **0**. No new finding. The original initial **Request changes** remains preserved and is superseded only as to its now-verified correction; this report does not erase or restate the initial as an approval.

Limits: this is actual same-context committed-fix verification plus authorized post-freeze peer reconciliation, not a fresh R2. It does not claim Linux hosted execution, final source publication, exact lease verification, remote clone, live protection API revalidation or archive semantic recovery. Those separate gates remain pending. No project mutation, ref/commit/remote change or private-note access occurred. Only this assigned external fix report/digest are persisted; before/after fixtures were disposable.
````````

### prevention-r1-integrity-fix.md

SHA-256: `aaee0898bfcdef7cca84c08bc5a84c1b1edd7d26a6ee714d0e2d3e56ba9953b5`.

````````markdown
# Code review 2026-10-16 — PR49 prevention R1 integrity committed-fix verification

- **Change:** `2d83602f92e6afddb46d32f9d7b14eb6021aec77..fb9e4b9560908067b3cd97aa205ef36223bda316` on development.
- **Reviewer:** Codex independent operational-integrity reviewer, `/root/cleanup_prevention_r1_integrity`; same context as the frozen initial.
- **Risk class:** Ordinary tooling.
- **Security-review cross-reference:** n/a; no runtime security-sensitive implementation change.
- **Initial preserved:** `prevention-r1-integrity.md`, SHA-256 `35359b993990d8e6076c0caec0ee943ca7d2ef57fe2ccdb61ed594f5aa9b27d8`.
- **Peer read:** After both initials froze and coordinator authorized reconciliation, read the complete `prevention-r1-code.md`, SHA-256 `8610cdcf47e5ad403c994de95c9cd01f883e1f24722f5ff5779d65f489cc8174`. Both digests independently recomputed and matched. No initial was edited.

## Correctness

**PIR1-01 / PRC1-01 — Low — closed at fb9e4b9560908067b3cd97aa205ef36223bda316.** The narrow `try` around initial `root.resolve()` converts Python 3.9's `RuntimeError` into `InputError`. This reaches the established structured exit-2 handler without suppressing later programming errors or changing ordinary policy-finding exit 1. Python 3.13 continues to reject the same invalid root. No storage accounting, limit, ancestry, offline or read-only check was weakened.

Actual pre-fix verification was repeated independently: a disposable directory received the committed new test file and `git show 2d83602:tools/check-repo-footprint.py`; Python 3.9 ran only `FootprintTests.test_symlink_loop_root_returns_structured_input_error`. It failed (test process exit 1), showing the underlying CLI exit 1 and `RuntimeError: Symlink loop from ...`. The same targeted regression against the actual committed checker passes on both supported runtimes. No deliberately broken project file or ref was created.

## Style

No new finding. The exception conversion is local to the known path-resolution boundary and carries its cause. The short comment accurately explains the supported Python-version distinction. Commit subject/trailer remain conventional and reference ADR-0044.

## Test coverage

The real public-CLI regression checks exit 2, parseable JSON containing `input`, and no traceback. It is a behavior test with demonstrated failure against the original source, not a restatement of implementation internals. Both complete footprint suites pass all 22 methods; existing policy-boundary and history negative controls still reject as expected. The narrow correction does not justify broadening or redoing unrelated runtime tests.

## Documentation

No new finding. The appended cleanup checkpoint accurately attributes both fresh initials, coordinator reproduction, tests-first repair and pending review/final-delivery gates. Original graft discovery remains attributed to author self-review; this fix does not alter that historical record. No original verdict was overwritten, task promoted, or hosted result claimed.

## Integration

Actual verification on macOS with Git 2.54.0 (Apple Git-157):

| Command / observation | Result |
|---|---|
| `git rev-parse HEAD`; `git status --porcelain=v1` | Exact `fb9e4b9560908067b3cd97aa205ef36223bda316`; clean |
| `git show --stat fb9e4b9`; `git diff 2d83602..fb9e4b9 -- tools/check-repo-footprint.py tools/test-repo-footprint.py docs/analysis/reports/2026-10-16-pr49-evidence-cleanup.md` | Complete three-file correction/checkpoint reviewed |
| Temporary current regression against checker bytes from `git show 2d83602:tools/check-repo-footprint.py`, `/usr/bin/python3` | Expected failure, 1 test / 1 failure; underlying original CLI traceback and exit 1 reproduced |
| `/usr/bin/python3 tools/test-repo-footprint.py FootprintTests.test_symlink_loop_root_returns_structured_input_error` | 1 passed |
| `/opt/homebrew/bin/python3.13 tools/test-repo-footprint.py FootprintTests.test_symlink_loop_root_returns_structured_input_error` | 1 passed |
| `/usr/bin/python3 tools/test-repo-footprint.py` | 22 passed (Python 3.9.6) |
| `/opt/homebrew/bin/python3.13 tools/test-repo-footprint.py` | 22 passed (Python 3.13.14) |
| Each interpreter with `tools/check-repo-footprint.py --json` | Exit 0, exact fix HEAD, 501 indexed blobs / 478 historical trees / 2967 unique blobs / 0 findings |
| Each interpreter with `tools/check-docs.py` | Exit 0, 406 Markdown files / 7302 local targets / 1276 fragments / 0 findings |
| `git diff --check 2d83602..fb9e4b9` | Passed |
| SHA-256 computation over both complete frozen R1 initials | Both expected digests matched |

Peer reconciliation: PRC1-01 and PIR1-01 describe precisely the same root-resolution exception, severity, reproduction and requested remedy. They count as **one unique Low group**, now closed by this actual committed-source verification. The peer report's distinct linked-worktree, missing-parent, missing-Git, packed-object and SHA-256-format probes complement this review's merge-parent, sparse-index, linked-graft and read-only probes; no contradictory verdict or unaddressed peer finding exists. Peer-only execution remains attributed to that report, not claimed as independently repeated here. The initial reports were independently frozen before this comparison.

Limits: This is verification of the narrow committed correction and reconciliation of both complete initial reports. Prior 161/124 dual-runtime fixture execution remains evidence at the original source, not falsely relabeled as rerun here; those six checker/test files are outside the correction. No new hosted Linux CI, runtime/QEMU run, remote clone, live protection API proof, archive semantic review or publication occurred. Existing CI/context/permission conclusions from the initial review remain valid because none changed. All repository writes/ref operations, canonical review/index integration and later delivery gates remain with the coordinator; this reviewer wrote only assigned external reports and disposable scratch.

## Verdict

**Approve the R1 correction and close the R1 unique finding group.** One unique group closed (PIR1-01 = PRC1-01, Low); zero open groups and zero new findings. Both original Request-changes verdicts remain preserved as historical initials. A different fresh R2 and final publication/hosted/ordinary-clone verification remain required; this approval does not authorize merge or Done promotion.
````````

### prevention-r2-code.md

SHA-256: `3d928a50fc302b7db4c6bc3b515d9a3eb298579c7087ebc52d82068eeb005e6f`.

````````markdown
# Code review 2026-10-16 — PR49 prevention R2 CODE

- **Change:** `433d42d3686b79d0b110053d83358bf864061523..fb9e4b9560908067b3cd97aa205ef36223bda316`, development.
- **Reviewer:** Fresh independent Codex R2 CODE reviewer, `/root/cleanup_prevention_r2_code`; all five roles executed sequentially.
- **Risk class:** Ordinary repository tooling.
- **Security-review cross-reference:** n/a; no runtime capabilities, IPC, syscalls, memory, scheduler, boot, crypto, unsafe or dependency implementation changes.
- **Source stages:** preflight `803ff08e25d52310137e69007fdb5b36e513c49a`; implementation `2d83602f92e6afddb46d32f9d7b14eb6021aec77`; actual reviewed/tested fix HEAD `fb9e4b9560908067b3cd97aa205ef36223bda316`.
- **Independence:** This initial freezes without reading the complementary R2 report or receiving its findings. The four complete prior R1 initial/fix reports were read as permitted historical evidence; their executions remain attributed to those reviewers.

## Correctness

No new finding. The complete nine-file change was reviewed against Accepted ADR-0044 and the approved cleanup description, with public CLI fixtures read before implementation. `tools/check-repo-footprint.py:41` decodes NUL-separated Git records and rejects unmerged/unsupported input; `:93` reads staged object identities; `:94` traverses all HEAD parents, deduplicating identical trees without losing path-sensitive policy coverage. Blob-size caching does not collapse repeated-path aggregate contributions. The inclusive 1 MiB blob, 512 KiB non-Markdown report and 128 KiB catalog-pair limits at `:130`–`:147` agree with the accepted preflight/guide. Symlink target text is counted; Gitlinks are explicitly outside parent-repository blob accounting. Worktree-only changes cannot substitute for staged bytes.

The complete-input boundary at `:72`–`:91` rejects shallow, promisor and graft views before traversal. Git replacement views and ambient GIT variables are suppressed; missing required trees/blobs fail closed. All Git invocations are read commands, optional locking and fsmonitor are disabled, and the command never initiates a fetch. The invalid-input handler preserves exit 2/JSON while actual policy findings retain exit 1. Deterministic ordering/source selection is appropriate for a storage report; this is not a claim of chronology or verdict authenticity.

The earlier **PRC1-01 = PIR1-01 (Low)** remains closed by the preserved original R1 fix verifications. This R2 independently confirms the narrow Python 3.9 root-resolution conversion at `:73`–`:77` and actually reproduced the failing new regression against pre-fix checker bytes. It neither relabels the original discovery nor erases the original Request-changes verdicts. Kernel capability semantics, fault containment and unsafe obligations are not applicable to this tooling-only diff.

## Style

No finding. The small standard-library implementation separates Git access, entry parsing, accounting and presentation clearly. Python 3.9 syntax compilation succeeds without writing bytecode. Names/comments describe the public storage contract rather than an incidental implementation. Conventional English commits reference ADR-0043/0044 as appropriate. There is no dependency addition, Rust formatting change or unsafe region.

## Test coverage

All **22** committed methods pass on Python **3.9.6** and **3.13.14**. These are meaningful public-CLI tests using actual disposable Git repositories, covering boundaries, per-path aggregate/pair accounting, historical deletion, staging versus worktree/untracked content, symlinks/Gitlinks, control characters, deterministic JSON/text, incomplete inputs, ambient Git state, replacement/graft defenses and script-relative defaults. No blocking missing test category was identified.

Additional independently executed Python 3.9 probes used `runpy.run_path('tools/test-repo-footprint.py')` to reuse only fixture setup helpers, then called the actual CLI:

| Disposable construction and actual operation | Observed result |
|---|---|
| Commit `docs/analysis/reports/nested/a-evidence-catalog.md` of 131073 bytes; construct a clean merge tree using `git commit-tree <initial-tree> -p <initial> -p <bad-commit>`; update only disposable HEAD/index to that merge | Exit 1, `footprint-catalog`: second-parent historical nested catalog remains covered |
| Commit `nested/old.dat`; obtain `git rev-parse HEAD:nested`; delete that loose tree object from the disposable object store | Exit 2, `input`: missing historical tree fails closed |
| Commit two report logs of 262145 identical bytes each; stage deletion of one with `git rm`; run the guard | Exit 1, `footprint-reports`: staged deletion does not hide the historical aggregate |
| SHA-256 every file, including Git metadata, before and after the preceding failing guard | Inventories identical: no file-content writes observed |
| Configure promisor true and an allowed `ext::touch <marker>` remote in a disposable repo | Exit 2, `input`; helper marker absent |
| Copy current regression fixture beside actual `git show 2d83602:tools/check-repo-footprint.py` bytes in a temporary tools directory; run only `FootprintTests.test_symlink_loop_root_returns_structured_input_error` | Test process exit 1, `AssertionError: 1 != 2`; the current full suite passes that same regression |

The external-helper check demonstrates preflight rejection on the exercised path, not network packet capture or OS sandbox isolation. QEMU/Rust execution is unnecessary to establish this Python/documentation change; no runtime behavior changed.

## Documentation

No finding. The CI guide documents root defaults, status codes, staged/history boundaries, identical-blob path accounting, Gitlinks/symlinks, excluded reflogs/other branches, complete-input requirements and semantic limits. Standards/common-skill guidance follows Accepted ADR-0044, keeps canonical reports in Git and raw streams outside it, and preserves exact-path review requirements for future exceptions. No broad exclusion or bypass is introduced. The T-056 criterion correction accurately separates the already-delivered release pointer from step-six retention guidance. Appended checkpoints preserve actual original source identities and pending gates without Done or new hosted-delivery claims.

Read the actual PR49 description using `gh pr view 49 --json body,title,headRefOid` before fixtures/implementation. Its remote head remains original `97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4`; the approved cleanup record supplies the local maintenance-unit description. The stale remote final-head description is an explicitly pending publication update, not evidence that this local candidate already passed hosted CI.

## Integration

No finding. `.github/workflows/ci.yml:92` supplies full history only to the existing lint checkout; its two new footprint steps fail normally on nonzero status. SHA-pinned checkout, unpersisted credentials and `contents: read` remain. Job/context identities and all six app-15368 entries in the versioned protection definition are unchanged. The public docs checker remains Git-independent, confirmed by execution with empty PATH. Six existing checker/fixture files and all tracked Rust bytes compare identically to original97.

Actual commands/results at fixed HEAD on macOS, Git `2.54.0 (Apple Git-157)`:

| Command | Actual result |
|---|---|
| `/usr/bin/python3 --version`; `/opt/homebrew/bin/python3.13 --version` | 3.9.6; 3.13.14 |
| Each interpreter with `tools/test-repo-footprint.py` | 22 passed each |
| Each interpreter with `tools/check-repo-footprint.py --json` | Exit 0; exact fb9e4b9 HEAD; 501 indexed blobs / 478 historical trees / 2967 unique blobs / zero findings |
| Each interpreter with `tools/test-check-docs.py` | 161 passed each |
| Each interpreter with `tools/test-docs-metadata.py` | 124 passed each |
| Each interpreter with `tools/check-docs.py` | 406 Markdown files / 7302 local targets / 1276 fragments / zero findings |
| Python 3.9 in-memory `compile(Path(name).read_bytes(), name, 'exec')` for both new scripts | Passed, no bytecode write |
| `subprocess.run(['/usr/bin/python3','tools/check-docs.py'], env=dict(os.environ, PATH=''), ...)` | Exit 0; same corpus counts/zero findings |
| `git diff --exit-code 97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4 fb9e4b9560908067b3cd97aa205ef36223bda316 -- tools/check-docs.py tools/docs_audit.py tools/docs_consistency.py tools/docs_metadata.py tools/test-check-docs.py tools/test-docs-metadata.py '*.rs'` | Exit 0 |
| `git diff --check 433d42d3686b79d0b110053d83358bf864061523 fb9e4b9560908067b3cd97aa205ef36223bda316` | Exit 0 |
| Final `git status --porcelain=v1`; `git rev-parse HEAD` | Clean; exact fb9e4b9560908067b3cd97aa205ef36223bda316 |

## Verdict

**Approve this scoped implementation.** Zero new findings, zero open verified scoped groups. Both fresh R2 initials still require their authorized post-freeze reconciliation, and final candidate publication/hosted/ordinary-remote-clone gates remain separate. This verdict does not authorize merging PR49, Done promotion, ref replacement or a runtime security claim.

Reading limits: full AGENTS/CLAUDE, current state, both invoked review skills and complete code master plan; governing ADR-0043/0044, approved cleanup record, relevant ADR-0013/0025/0040 governance and code/testing/documentation/infrastructure/security/unsafe/error/style/commit/principle standards; complete new tests/implementation and scoped diff. Initial bulk ADR/standards reads were truncated, so this report does not claim an exhaustive semantic reread of every historical ADR or unrelated standard. The load-bearing ADR-0043/0044, policy/guide changes and master plan were read directly. No archive payload semantic re-review, new hosted Linux run, runtime/QEMU build, remote clone, live protection API revalidation, exact lease publication or final recovery audit was performed. Prior R1 probes/results are not relabeled as R2 executions. Repository report/index integration is delegated to the sole writer. No project edit, stage, commit, branch/ref operation, remote mutation, private-note access or source export occurred; only this assigned external report/digest persist, and adversarial repositories were disposable.
````````

### prevention-r2-integrity.md

SHA-256: `2344edd3c103908f01780b942a8b3d973d027b1c5e696ecc80655ad5d6f92bb5`.

````````markdown
# Code review 2026-10-16 — PR49 prevention R2 operational integrity

- **Change:** `433d42d3686b79d0b110053d83358bf864061523..fb9e4b9560908067b3cd97aa205ef36223bda316` on development; full preflight, prevention implementation and R1 correction unit.
- **Reviewer:** Codex independent fresh R2 reviewer, `/root/cleanup_prevention_r2_integrity`; all five roles performed sequentially.
- **Risk class:** Ordinary tooling; no runtime-sensitive implementation or dependency changes.
- **Security-review cross-reference:** n/a. Adversarial Git checks are part of this CODE review.
- **Independence:** No complementary R2 report or findings read before this initial freeze. Previous R1 integrity initial/fix reports were read, preserving their original Request-changes and closed Low group. The coordinator independently reproduced the new finding after disclosure; that is separately attributed, not substituted for this reviewer's execution.
- **Authority:** Approved cleanup plan and Accepted ADR-0044. This review does not authorize publication, merge, ref changes or Done promotion. Sole repository writer integrates canonical reporting.

## Correctness

**PIR2-01 — Medium — commit-graph cache can hide oversized original ancestry.** At `tools/check-repo-footprint.py:26–32` the Git wrapper disables replacements and fsmonitor, but leaves `core.commitGraph` enabled. The history inventory at `tools/check-repo-footprint.py:94` consequently trusts cached parents/root-tree metadata. In a complete disposable repository, a checksum-valid cache with the final deletion commit's parent list truncated made the committed-then-deleted 1,048,577-byte blob disappear from traversal. Both supported runtimes then returned exit 0, `historical_trees: 1`, and no findings. The same repository's raw commit objects still contain three commits; `git -c core.commitGraph=false rev-list --count HEAD` returns 3, while default `rev-list` returns 1. `git commit-graph verify` exits 1 and reports that the HEAD parent list terminates early. With commit-graph reading disabled through a disposable Git wrapper, the unchanged guard returns exit 1 and `footprint-blob` on both runtimes.

This is a concrete false green against the complete-original-history contract, analogous to the already-addressed graft ancestry view. The precondition is a locally inconsistent/tampered Git cache; this report does not claim that a normal tracked PR file can install that cache on a clean hosted runner. Medium reflects loss of the central storage guarantee, rather than a demonstrated remote compromise. A narrow remedy is `-c core.commitGraph=false` in the existing read-command wrapper, with a real regression that fails against this source and passes after correction. Do not silently weaken the history promise or introduce a directory exception.

Reproduction details: create three commits (small initial tree; add `large.dat` containing `b'x' * 1048577`; delete it), then run `git commit-graph write --reachable`. In `.git/objects/info/commit-graph`, read the chunk lookup table at byte 8 (12-byte records, count at header byte 6); find HEAD's index in the sorted `OIDL` SHA-1 list. Its `CDAT` record starts at `CDAT_offset + index * 36`. Replace the two big-endian parent words at record offset 20 with `0x70000000`, then recompute the last 20 bytes as SHA-1 of all preceding bytes. The graph needs owner-write permission because Git creates it read-only. This preserves the checksum, all commit/blob objects, refs and index. Git's [commit-graph format](https://git-scm.com/docs/commit-graph-format) specifies these parent/cache fields and checksum; the finding itself is established by execution.

Complete temp-only construction and all additional probes are in `/tmp/tyrne-prevention-r2-integrity-probes.py`, SHA-256 `9ab6d624a814c1ae1ab78d75180d7b16bd43712cbbf8a20168de9be53852d7c3`; run `/opt/homebrew/bin/python3.13 /tmp/tyrne-prevention-r2-integrity-probes.py` from any directory. It invokes both CLIs, asserts the observations above and removes temporary repositories automatically. The initial separate cache experiment stopped at Git's read-only cache permissions; after explicitly allowing owner writes in scratch, the false green reproduced. A first broad probe draft also stopped on an invalid cross-repository ref in its setup; that unrelated setup line was removed before the complete passing run. Neither draft failure is attributed to the guard.

Other reviewed accounting is correct: inclusive boundaries; stored index objects versus worktree bytes; per-path report/catalog totals despite identical blob content; all merge parents under ordinary object traversal; safe identical-tree deduplication; symlink target text; Gitlink exclusion; deterministic findings and missing/unmerged-object rejection. R1's Python 3.9 root-resolution correction remains narrow and tested. No second unique finding was confirmed.

## Style

No finding. Standard-library Python, explicit limits, NUL-delimited parsing and deterministic sorting fit existing tools. English conventional commits carry ADR-0043/0044 references. No Rust naming, unsafe, formatting or dependency-policy concern applies. The cache correction should stay confined to the existing Git boundary and its behavioral fixture.

## Test coverage

All 22 real temporary-Git methods pass independently on Python 3.9.6 and 3.13.14. They exercise index/history boundaries, deleted blobs/report/catalog totals, exact catalog pairs, staged/worktree distinctions, symlinks/Gitlinks, control-character names, deterministic JSON/text, shallow/promisor/partial input, missing objects, unmerged index, replacement/graft suppression, ambient GIT state, invalid/default roots and the R1 symlink-loop regression. **Missing regression:** PIR2-01's inconsistent commit-graph cache. The original suite's green result does not resolve that failure.

Additional independent probes executed on both runtimes:

- Oversized content introduced/deleted only through a merge's second parent: exit 1 with the original `footprint-blob` finding. Before/after SHA-256 file inventories, including Git metadata, were equal after both failing scans; this checks file bytes, not timestamps or every conceivable external side effect.
- Detached linked worktree with common-directory `info/grafts`: exit 2, `input`.
- Ambient `GIT_DIR`, `GIT_OBJECT_DIRECTORY`, `GIT_INDEX_FILE`, `GIT_SHALLOW_FILE` and `GIT_CONFIG_COUNT/KEY/VALUE` overrides: original target still rejected with exit 1.
- Oversized content on an unrelated orphan branch: exit 0 for clean HEAD, as expressly documented. Missing raw parent commit and missing Git executable: exit 2 with structured input findings and no traceback.
- Cache experiment: before mutation exit 1 / 2 historical trees; after mutation exit 0 / 1 historical tree; disabling cache reading restores exit 1 / 2 historical trees. Raw object ancestry remains 3 commits throughout.
- Ordinary local Git-transport clone using `--no-local --single-branch --branch development`: exact fb9e4b9, full Git fsck success, guard success on both runtimes with 478 historical trees. A disposable synthetic two-parent PR merge using clean main and candidate HEAD also passes on both runtimes; identical tree deduplication correctly keeps 478 trees. This is a local source-clone/merge test, not the required final ordinary remote clone or hosted CI.

The fixture code uses disposable repositories with hook/signing suppression, no project branch switches or deliberately broken project commits. The guard contains no fetch command, suppresses lazy fetch/promisor input and invokes read-only Git commands with optional locks disabled. No packet capture or OS network sandbox proof is claimed.

## Documentation

No independent documentation finding. The guide distinguishes stored objects from untracked/unstaged bytes, HEAD from unrelated refs/reflogs, and bounds from semantic/authenticity proof. Its complete-history promise exposes PIR2-01. Retention guidance preserves original review verdicts, read limits, failed-before observations and original SHAs; exact-path reviewed exceptions remain the only future exception mechanism. Task timing clarification correctly separates the already-landed release pointer from step-six general retention guidance. The R1 checkpoint preserves initial verdicts and pending gates. No historical measurements were relabeled as runs on rewritten source.

Reading order/scope: full AGENTS/CLAUDE and live pointer; approved cleanup description, Accepted ADR-0044 and actual open PR49 description before tests; complete footprint tests before implementation; then all nine changed files and their complete scoped diff. Governing process sources include both review skills, the five-role master plan, ADR-0013/0025/0040/0043/0044 and relevant documentation, infrastructure, code/security-review, testing, style, unsafe, error and commit standards. Some initial combined governance reads were truncated; load-bearing ADR-0025/0040/0043 and infrastructure/documentation sources were read again in bounded outputs. This is not an exhaustive semantic reread of all unrelated ADRs, standards, old archive payloads or historical review records. Actual PR49 still names original remote head97; the approved cleanup record supplies this unit's local source stage.

## Integration

CI only adds full history to the existing lint checkout and two failing footprint steps. Its pinned checkout, `persist-credentials: false`, top-level `contents: read`, seven job identities and existing check wiring remain unchanged otherwise. The versioned policy is byte-identical across this scope; all six exact display contexts continue to match workflow names and app ID15368. No administrative credential, required-context addition, protection mutation, package or production Rust change is introduced. A fresh clean CI checkout is unlikely to have this cache fault; local completeness remains promised and must be repaired.

Executed commands/results on macOS, Git2.54.0 (Apple Git-157):

| Command / observation | Actual result |
|---|---|
| `gh pr view 49 --repo HodeTech/Tyrne --json number,title,body,headRefName,baseRefName,headRefOid,state` | Open development→main; published original `97dbcd16f1d9ed1f6e620bc17aa5349fe907c1a4` |
| `git rev-parse HEAD`; `git status --porcelain=v1` before/final | Exact `fb9e4b9560908067b3cd97aa205ef36223bda316`; clean |
| Each interpreter with `tools/test-repo-footprint.py` | 22 passed each |
| Each interpreter with `tools/test-check-docs.py` / `tools/test-docs-metadata.py` | 161 / 124 passed each |
| Each interpreter with `tools/check-docs.py` | 406 Markdown files / 7302 local targets / 1276 fragments / 0 findings |
| Each interpreter with `tools/check-repo-footprint.py --json` on actual project | Exit 0; 501 indexed blobs / 478 historical trees / 2967 unique blobs / 0 findings |
| In-memory `compile` of both new scripts on each interpreter | Passed; no bytecode written |
| `git diff --check 433d42d..fb9e4b9` | Passed |
| `git diff --exit-code 97dbcd1 fb9e4b9 --` six existing checker/test paths and `'*.rs'` | Passed: all six files and all tracked Rust bytes unchanged from original97 |
| `git diff --exit-code 433d42d fb9e4b9 -- .github/branch-protection/main.json` | Passed: versioned full policy unchanged |
| Temp-only probe script above | All final assertions passed, including observed false green and cache-disabled rejection |

Limits: no Linux hosted source execution, Rust/QEMU build, final remote clone, lease/publication, live branch-protection API revalidation, private notes or full archive semantic review. Those remain distinct coordinator gates. Existing Rust bytes are unchanged; Python/Git behavioral verification is appropriate to this unit. Only this assigned report/digest and disposable external scratch were written; no repository source, index, ref, remote or review initial was changed.

## Verdict

**Request changes.** One unique blocking group: **PIR2-01 (Medium)**. Add a tests-first regression and disable the alternate commit-graph ancestry view, then independently verify the committed correction and reconcile complementary R2 reports. R1's one Low group stays closed; original R1 initials remain unchanged. Final candidate validation, exact-lease publication, hosted/ordinary remote-clone gates and maintainer approval remain pending.
````````

### prevention-r2-code-fix.md

SHA-256: `016444bb3787dcebe1662e971736937d08f92a38999c0e3de4d06ec2c9980080`.

````````markdown
# Code review 2026-10-16 — PR49 prevention R2 CODE committed-fix verification

- **Change:** `fb9e4b9560908067b3cd97aa205ef36223bda316..588edbfaaa6dfdffafc09e97ddadaac006313fcb`, development.
- **Reviewer:** Original fresh R2 CODE reviewer, `/root/cleanup_prevention_r2_code`, actual follow-up in the same context; all five roles executed.
- **Risk class:** Ordinary tooling.
- **Security-review cross-reference:** n/a; no runtime-sensitive implementation change.
- **Preserved initial:** `prevention-r2-code.md`, original **Approve / zero findings**, independently rehashed unchanged as `3d928a50fc302b7db4c6bc3b515d9a3eb298579c7087ebc52d82068eeb005e6f`.
- **Post-freeze peer read:** The coordinator authorized reading the complete frozen `prevention-r2-integrity.md`; independently computed SHA-256 `2344edd3c103908f01780b942a8b3d973d027b1c5e696ecc80655ad5d6f92bb5` matches. Its original **Request changes / Medium PIR2-01** remains intact.

## Correctness

**PIR2-01 — Medium — closed at 588edbfaaa6dfdffafc09e97ddadaac006313fcb.** The integrity reviewer independently discovered the checksum-valid inconsistent commit-graph cache hiding oversized original ancestry. The coordinator then independently reproduced it. This CODE review initially missed that case; its original approval is historical, not a denial of the peer finding. After authorized disclosure, this reviewer actually reproduced the public-CLI false green on both supported runtimes using the new regression and the original checker bytes from fb9e4b9.

The correction at `tools/check-repo-footprint.py:31` adds `-c core.commitGraph=false` to the existing Git read wrapper. It disables cached ancestry/tree metadata for all invoked Git commands so the existing HEAD traversal reads original commit objects. It does not alter the three byte limits, index accounting, parent traversal policy, replacement/graft defenses, structured error boundary, offline behavior or read-only command set. The regression now reports exit 1 and the original offending commit, rather than a false-green one-tree report. No new correctness finding.

The peer finding's Medium severity is appropriate to a demonstrated loss of the central history guarantee under an inconsistent local cache. Neither the original peer nor this verification claims that normal tracked PR content can install such a cache on clean hosted CI. This fix is not a general object-authenticity verification claim. Kernel capability, fault-containment and unsafe checks remain non-applicable to the scoped files.

## Style

No finding. The one-option production correction is confined to the existing Git boundary. The conventional English fix commit references ADR-0044. The new fixture's binary work is justified by the actual cache behavior under test, uses Python standard-library `hashlib`/`struct`, and mutates only its disposable cache. It does not add a production parser or dependency.

## Test coverage

Read the new fixture before the production correction. It creates real initial/add/delete commits, writes a real standalone commit graph, finds HEAD through the OID lookup chunk, changes only its cached parent entries, recomputes the checksum, confirms three raw commits and invokes the public CLI. Assertions require the policy finding and original offending-commit source. Version/base-chain checks and hash-width selection make the binary assumptions explicit. The chunk lookup, hash algorithms, H+16 commit-data row and absent-parent sentinel agree with Git's [documented cache format](https://git-scm.com/docs/commit-graph-format).

Actual independent before/after verification:

1. Read old checker bytes with `git show fb9e4b9560908067b3cd97aa205ef36223bda316:tools/check-repo-footprint.py`; put those bytes beside the current test file in a disposable directory.
2. Run `FootprintTests.test_inconsistent_commit_graph_cannot_hide_oversized_history` there with `/usr/bin/python3` and `/opt/homebrew/bin/python3.13`. Both test processes exit 1 with `AssertionError: 0 != 1`; the old guard's JSON has one historical tree, one unique blob and no findings. This is an actual observed prior-source false green, not an inferred regression.
3. Run the complete committed fixture suite with both interpreters. All **23** methods pass on each, including that same regression and all previous policy/error controls.
4. Independently exercise the regression in a SHA-256-format disposable repository by loading the fixture with `runpy`, wrapping only its temporary `git init` helper to add `--object-format=sha256`, and executing the single unchanged test with `unittest` on Python 3.9. It passes. This supplements the default SHA-1 execution and checks the fixture's alternate hash-width/checksum branch.

No blocking portability or maintainability issue was identified. The exercised Git is 2.54.0 (Apple Git-157), with Python 3.9.6/3.13.14 on macOS; this does not substitute for the later Linux hosted gate. The existing 161/124 documentation suites passed on both runtimes in this reviewer's initial R2; their six source/fixture files are unchanged by this four-file correction, so those suites were not rerun here. Current full-corpus checks were rerun on both runtimes.

## Documentation

No finding. The guide now explicitly names commit-graph cache suppression and the new regression. The appended execution checkpoint distinguishes this CODE initial's approval from the integrity initial's finding and records the coordinator's before/after observation, pending actual review verification and remaining delivery gates. It does not overwrite original verdicts or invent historical source execution. The production correction is appropriately narrow for Accepted ADR-0044's original-history contract.

## Integration

The complete four-file correction changes the Git option, its fixture, guide and cleanup checkpoint. CI configuration, required contexts/app bindings, permissions, storage policy, existing docs checker and Rust/dependency files do not change. No runtime/QEMU retesting is needed for this correction.

Actual commands/results at exact committed fix:

| Command / observation | Actual result |
|---|---|
| `git rev-parse HEAD 588edbf`; `git status --porcelain=v1` | Both identities resolve to 588edbfaaa6dfdffafc09e97ddadaac006313fcb; clean |
| `git diff fb9e4b9560908067b3cd97aa205ef36223bda316 588edbfaaa6dfdffafc09e97ddadaac006313fcb --` the four correction paths; `git show -s --format=full 588edbf` | Complete correction and commit reviewed |
| Each interpreter against temporary old checker/current targeted regression | Expected test failure; old guard false-green exit 0 reproduced |
| `/usr/bin/python3 tools/test-repo-footprint.py` | 23 passed |
| `/opt/homebrew/bin/python3.13 tools/test-repo-footprint.py` | 23 passed |
| Each interpreter with `tools/check-repo-footprint.py --json` | Exit 0; exact 588edbf HEAD; 501 indexed blobs / 479 historical trees / 2971 unique blobs / zero findings |
| Each interpreter with `tools/check-docs.py` | Exit 0; 406 Markdown files / 7302 local targets / 1276 fragments / zero findings |
| SHA-256 disposable-init variant of the committed cache regression, Python 3.9 | One test passed |
| In-memory `compile(Path(name).read_bytes(), name, 'exec')` for both scripts, Python 3.9 | Passed; no bytecode write |
| `git diff --check fb9e4b9560908067b3cd97aa205ef36223bda316 588edbfaaa6dfdffafc09e97ddadaac006313fcb` | Passed |
| SHA-256 recomputation of both R2 initials | Both frozen digests verified; neither initial edited |

## Verdict

**Approve the committed correction and close PIR2-01 (Medium).** Post-freeze reconciliation identifies one unique R2 group, discovered by the integrity reviewer and absent from this reviewer's initial. It is now independently reproduced before the fix and verified corrected by this reviewer. R2 groups closed: **1**; open verified scoped groups: **0**; new findings: **0**. The previously closed R1 Low group remains closed. Both original R2 initial verdicts and their actual reading/execution limits remain preserved.

Limits: this is same-context committed-fix verification and authorized peer reconciliation, not another fresh independent round. Peer-only cache-verifier, linked-worktree, local-clone, synthetic-merge and ambient-environment observations are not claimed as this reviewer's executions. No new hosted Linux CI, final remote clone, live protection API proof, archive semantic audit, exact lease/publication or merge occurred. Those delivery gates remain separate. No project file, index, ref, branch or remote mutation, private-note access or source export occurred. Only this assigned external fix report/digest persist; before/after and SHA-256 fixtures were disposable. Canonical report/index integration remains with the sole repository writer.
````````

### prevention-r2-integrity-fix.md

SHA-256: `80a310cc4b9645b7a2764eaf00503b7b3f1cb237283411664c32e76997da54f8`.

````````markdown
# Code review 2026-10-16 — PR49 prevention R2 integrity fix verification

- **Change:** `fb9e4b9560908067b3cd97aa205ef36223bda316..588edbfaaa6dfdffafc09e97ddadaac006313fcb` on development.
- **Reviewer:** Codex operational-integrity reviewer, `/root/cleanup_prevention_r2_integrity`, same context as the frozen fresh R2 initial; all five roles performed.
- **Risk class:** Ordinary tooling.
- **Security-review cross-reference:** n/a; no runtime-sensitive implementation change.
- **Initial preserved:** `prevention-r2-integrity.md`, SHA-256 `2344edd3c103908f01780b942a8b3d973d027b1c5e696ecc80655ad5d6f92bb5`, original Request-changes verdict and Medium discovery unchanged.
- **Authorized peer read:** Both initials froze before disclosure. Read the complete `prevention-r2-code.md`; independently recomputed SHA-256 `3d928a50fc302b7db4c6bc3b515d9a3eb298579c7087ebc52d82068eeb005e6f` matches. Its original Approve/zero-new-findings initial remains unchanged.

## Correctness

**PIR2-01 — Medium — closed at588edbfaaa6dfdffafc09e97ddadaac006313fcb.** The existing Git read wrapper now sets `-c core.commitGraph=false` at `tools/check-repo-footprint.py:32`. This prevents `rev-list` from substituting inconsistent derived parent/tree data for raw commit ancestry. Existing replacement suppression, shallow/promisor/graft rejection, optional-lock/fsmonitor controls, index accounting and policy limits are unchanged. It introduces neither fetching nor writes nor an object-authenticity guarantee.

Independently repeated the actual failing-before check, using only disposable copies: copy the current committed test file beside checker bytes obtained by `git show fb9e4b9560908067b3cd97aa205ef36223bda316:tools/check-repo-footprint.py`, then run `FootprintTests.test_inconsistent_commit_graph_cannot_hide_oversized_history`. Both Python3.9.6 and3.13.14 fail with `AssertionError: 0 != 1`; the old CLI reports no findings and one historical tree. Against the actual committed correction, both targeted tests pass and attribute `footprint-blob` to the original oversized commit. This directly validates the original false-green remedy without relabeling author checks as independent execution.

No new finding. R1's single Low symlink-loop group remains closed; its initial severity/verdicts are not changed by this verification.

## Style

No finding. The single command-line configuration override belongs at the existing Git boundary. The fixture confines its cache mutation to a disposable repository; its comment explains that stored commit objects remain intact. The English commit message/trailer references ADR-0044. No Rust, unsafe, dependency or unrelated refactor change.

## Test coverage

Read the new regression before the implementation correction. It creates three real commits with an oversized add/delete ancestor, explicitly enables the cache in the fixture, writes a standalone graph, uses the documented OID/chunk/CDAT layout to truncate cached HEAD parents and recomputes the checksum. It confirms three raw commits with cache reading disabled, then requires policy exit1, precisely `footprint-blob`, and exact original offending-source attribution. The demonstrated dual-runtime failing-before result shows the mutation genuinely exercises the reported behavior.

The parser derives hash width/digest from the graph header, validates version/standalone shape, and locates chunks independently of their order; optional generation/Bloom chunks do not change the offsets it uses. Fixed first-parent words and owner-write permissions match the documented Git format and supported macOS/Linux fixture environment. In additional disposable copies, explicitly adding `--object-format=sha256` only to fixture repository initialization exercised the SHA-256 branch: the targeted regression passes on both runtimes. Those copies are supplemental probes, not committed test changes or claims about old historical execution. No blocking portability/maintainability issue was found.

All23 committed footprint methods pass on both runtimes. Existing bounds, replacement/graft, missing-object, root and input controls remain exercised. Whole-corpus and actual project guard checks also pass on the exact correction below. Existing161/124 checker methods were already run in this review's initial atfb9; they were not rerun or falsely rebound here because their six source files are unchanged by this correction.

## Documentation

No finding. Guide wording now includes commit-graph cache suppression and its fixture. The appended checkpoint preserves the initial peer Approve and this review's Request changes/Medium discovery, separates coordinator reproduction from reviewer execution, and leaves committed verification/final delivery pending until actually done. It explicitly limits the local-cache precondition and avoids claiming normal tracked PR files can install such a cache on clean CI. Historical assertions, original identities, task states and prior review initials are preserved.

Complete four-file correction diff and conventional commit metadata were read. Governing review skills, five-role master plan, approved description, Accepted ADR-0044 and contextual sources/read limits remain those recorded in the full-unit initial; this follow-up is an actual correction review, not a claimed third fresh round or exhaustive archive semantic reread.

## Integration

The workflow, versioned protection, six existing checker/test sources and all tracked Rust bytes are byte-identical across the correction. Consequently required display names/app15368 bindings, unpersisted checkout credentials, full-history wiring and `contents: read` remain unchanged. Disabling a derived Git cache changes no project dependency or CI privilege. Current guard/corpus behavior confirms the small correction integrates with the real repository.

Actual commands/results on macOS, Git2.54.0 (Apple Git-157):

| Command / operation | Actual result |
|---|---|
| `git rev-parse HEAD`; `git status --porcelain=v1` before/final | Exact `588edbfaaa6dfdffafc09e97ddadaac006313fcb`; clean |
| SHA-256 of both complete R2 initials | Both expected digests match; originals unchanged |
| Temporary current targeted regression beside checker from `git show fb9e4b9:tools/check-repo-footprint.py`, each interpreter | Expected test exit1; CLI false green independently reproduced on both |
| Each interpreter with `tools/test-repo-footprint.py FootprintTests.test_inconsistent_commit_graph_cannot_hide_oversized_history` | 1 passed each against actual588 source |
| Disposable explicit SHA-256 initialization, same targeted regression/current checker, each interpreter | 1 passed each |
| Each interpreter with `tools/test-repo-footprint.py` | 23 passed each |
| Each interpreter with `tools/check-repo-footprint.py --json` | Exit0; exact588 HEAD;501 indexed blobs /479 historical trees /2971 unique blobs /0 findings |
| Each interpreter with `tools/check-docs.py` | Exit0;406 Markdown files /7302 local targets /1276 fragments /0 findings |
| In-memory syntax compilation of both new scripts on both runtimes | Passed, no bytecode written |
| `git diff --check fb9e4b9..588edbf` | Passed |
| `git diff --exit-code fb9e4b9 588edbf --` workflow, versioned protection, six existing checker/test paths and `'*.rs'` | Passed: all unchanged |

Peer reconciliation: the complementary initial approved the same full source with zero newly identified findings and did not exercise the inconsistent commit-graph case. This review uniquely discovered **PIR2-01 (Medium)**; its executed reproduction and actual committed fix now resolve the additional group. The peer's merge/catalog, missing-tree, staged historical aggregate, read-only and external-helper probes remain attributed to that reviewer. There is no unresolved contradiction or unaddressed peer finding. Original initials accurately retain different discovery coverage and verdicts; closure records the later common corrected state.

Limits: this verifies the narrow committed correction and reconciles both complete frozen initials. No new hosted Linux execution, final remote clone, archive recovery/semantic re-review, live protection API check, exact lease/publication, runtime/QEMU build, Done promotion or merge occurred. Those remain coordinator/maintainer gates. Only assigned external reports/digests and disposable scratch were written; no repository source/index/ref/remote or initial report was changed.

## Verdict

**Approve the committed R2 correction and close PIR2-01 (Medium).** One unique R2 group closed; zero open groups, zero new findings. R1's unique Low remains closed. Both original R2 verdicts/severities/discovery records are preserved; this same-context verification/reconciliation completes this reviewer's R2 obligations. Final candidate, lease, hosted/ordinary remote-clone and maintainer gates remain separate.
````````
