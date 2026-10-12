# Code review 2026-10-12 — PR48 follow-up A, round 1

- **Change:** [PR48](https://github.com/HodeTech/Tyrne/pull/48), immutable `1e281ac89d791dc3c6920a038ec26381a49623f3..50ab72bf2c15a4d34be25a1491a357313e50390a` on `development`.
- **Reviewer:** fresh Codex code-review agent `/root/pr48_tools_r1_code`, acting in all five roles sequentially for @cemililik; distinct from the author and security reviewer.
- **Date:** 2026-10-12.
- **Risk class:** Security-sensitive assurance tooling. Production kernel, HAL, BSP, userland, unsafe regions, ADRs and live policy are unchanged by this delta.
- **Security-review cross-reference:** `/tmp/tyrne-pr48-tools-r1-security.md`, fresh distinct round-1 pass; publication under the canonical security-review folder belongs to the coordinating author.
- **Scope:** follow-up A only: captured REST protection fixture and conservative boundary tests; exact-command clean ARM baseline before the six-cfg negative; empty-diagnostic refusal; actual Undefined Instruction smoke token; optional performance metadata fallbacks and minimization of override paths/hostname; five cargo-bin cache-path removals. Remaining supplied-report documentation work is follow-up B and is neither approved nor required prematurely here.

## Correctness

- **ARM baseline attribution — pass.** `tools/test-ci-gates.sh` defines one `ARM_COMMAND` array: `cargo clippy --workspace --exclude tyrne-bsp-qemu-virt --all-targets -- -D warnings`. The same array executes on the unmodified private copy and after exactly six hello cfg gates are changed from `all(target_arch = "aarch64", target_os = "none")` to arch-only. The build script and syscall shim are copied unchanged. Any clean-baseline failure stops before mutation. The negative must return compiler exit 101 and contain an exact complete line for duplicate `panic_impl` or unsupported unwinding without std. Empty diagnostics, unrelated/near-match lines, successful commands and tool-failure exits are refused. This makes the second diagnostic attributable to the intentional source change given the successful same-command control; it does not establish a universal classifier for every Rust failure.
- **ARM isolation — pass.** Host verification precedes cargo; temporary tracked-source copies use NUL-safe filenames, a private target and cleanup traps. Fixtures verify originals remain byte-identical, source paths with spaces work, calls occur clean then mutated, malformed anchors cause no cargo invocation, and refusal paths clean up. Independent actual Apple ARM execution passed with the negative returning 101/E0152.
- **Protection fixture — pass.** No production normalizer or write path changes. The complete captured protection-endpoint response normalizes to the entire committed definition, including six app-bound checks and non-status policy. A new independent read-only GET at API version `2022-11-28` exactly matched the parsed fixture. Branch-summary `name`/`protection_url`, enforcement scope, and review dismissal/bypass actor extensions remain unrepresentable and refused. This fixture does not authorize ignoring new policy fields.
- **Smoke fault token — pass.** `tools/smoke.sh:151` now matches QEMU's actual `Undefined Instruction` class. Both debug and release synthetic cases retain all required markers while injecting each of six fault classes, so success cannot hide the fault. The production profile requirements and intentional SVC handling are unchanged.
- **Performance metadata — pass.** `tools/perf-harness.sh` keeps completed measurements when `uname`, QEMU version, `rustc -V`, or active-toolchain discovery fails, recording `(unknown)` and suppressing failed-command output. The active rustup toolchain identifier is retained while its override explanation is removed; `uname -srm` excludes the hostname. Valid/failed sample accounting, percentile calculation, watchdog behavior and overwrite refusal remain intact. This is minimization of these normal metadata fields, not a claim to sanitize arbitrary successful tool output or all diagnostic artifacts.
- **Cache paths — pass with one Low wording finding.** Five `~/.cargo/bin` cache entries are removed while registry/git/target caches, architecture keys and installation steps remain. Exact-head hosted runs completed successfully. The remaining coverage comment still contrasts itself with sibling jobs; see R1-SEC-01 below.

**Blocking correctness findings:** none.

## Style

ShellCheck 0.11.0 over all `tools/*.sh`, actionlint 1.7.12, and immutable-range `git diff --check` passed. Naming, quoting, Bash arrays, explicit Python exceptions and focused fixture helpers are consistent with the surrounding tooling. No Rust style/unsafe exception is introduced. The delta is 207 insertions and 27 deletions across 14 files, within the medium review size.

**Style findings:** none beyond the Low documentation comment below.

## Test coverage

### Independent execution and source provenance

The reviewer extracted `git archive 50ab72bf2c15a4d34be25a1491a357313e50390a` into a private temporary tree. Archive SHA-256: `ccb0619a9976e64ca3d6d7cd4388e8caec5ba9e0aa24e21acb7c88937a5e5e27`. A synthetic private git commit was created solely for scripts that use tracked-file inventories and git metadata; its fixture SHA is not represented as the reviewed source SHA. No repository bytes, shared target, branch, policy or remote state were changed by this reviewer. Private logs are discoverable through `/tmp/tyrne-pr48-code-r1-dir` and are temporary evidence, not canonical repository artifacts.

Environment: Darwin 27.0.0 arm64, Rust host `aarch64-apple-darwin`, pinned `nightly-2026-01-15`, rustc `1.94.0-nightly (86a49fd71 2026-01-14)`, LLVM 21.1.8.

| Independently executed command | Outcome | Evidence meaning |
|---|---|---|
| `python3 tools/test-branch-protection.py` and `python3 -O tools/test-branch-protection.py` | 29 tests each, pass | Real-response normalization plus conservative validation/write-refusal/transport controls; no real administrative writes |
| `python3 tools/test-perf-harness.py` and `python3 -O tools/test-perf-harness.py` | 7 tests each, pass | Synthetic samples, metadata/privacy, overwrite/failure/dirty/tee controls |
| `python3 tools/test-arm-host-probe.py` and `python3 -O tools/test-arm-host-probe.py` | 11 tests each, pass | Controlled exact argv, baseline order/failure, diagnostic/status/host/anchor/cleanup cases |
| `python3 tools/test-smoke-gates.py` | 20 cases, pass | Synthetic traces only; independent local run did not boot private mutant guests |
| `bash tools/test-ci-gates.sh --arm-host` | pass | Real native Apple ARM clean clippy, then intentional six-cfg failure 101/E0152 |
| `shellcheck tools/*.sh` | pass | All shell scripts, default severity |
| `actionlint` | pass | Workflow syntax/integration |
| `python3 tools/branch-protection.py check` | pass | Fresh read-only REST/GraphQL/rulesets full-policy comparison |
| `git diff --check <base> <head>` | pass | Immutable delta whitespace |

The `-O` executions demonstrate that Python test and production boundary checks still operate when the top-level interpreter optimizes assertions. Stub subprocesses have their own interpreters; this is not a claim that every child process runs optimized.

### Before/after regression sensitivity

New test bytes were retained while only the relevant production script was replaced privately with base `1e281ac` bytes, then restored:

- `ArmProbeTests.test_failing_baseline_never_reaches_mutation_assertion` fails against the old script in all nine baseline diagnostic/status subcases: the recorded first invocation is already mutated (`False`) instead of the required clean baseline (`True`). It passes at the reviewed head. The initial mistyped unittest class selector produced a loader error and was discarded; it is not counted as regression evidence.
- The 20-case new smoke suite rejects the old script at `debug-fault-5`: expected fault exit 1, observed exit 0. At the reviewed head both debug and release Undefined Instruction cases pass. Synthetic evidence is explicitly distinguished from actual guest execution.
- An isolated metadata control used the new fixture helper and a uname stub accepting both argument layouts, to avoid confounding metadata fallback with the separate `-a` to `-srm` change. For each of rustc/rustup/QEMU and exit 1/127, head bytes retained three valid samples, emitted one report with unknown metadata and no failure-output canary; old bytes exited 1/127 and emitted no report. The original whole new test also rejects old bytes, but its strict new uname stub can fail first with 64; the isolated control supplies the causal fallback evidence.
- No before/after failure is expected for the new REST fixture: the implementation deliberately stays unchanged, and the new coverage pins an observed shape without weakening conservative refusal.

### Hosted exact-head integration evidence

Read-only `gh run view` independently confirmed completed `success` and exact head `50ab72bf2c15a4d34be25a1491a357313e50390a` for all three runs:

| Run | Event and result |
|---|---|
| [38210439123](https://github.com/HodeTech/Tyrne/actions/runs/38210439123) | PR CI; all seven jobs success, including ARM, QEMU, Miri, nightly/stable host, kernel and informational coverage |
| [38210436230](https://github.com/HodeTech/Tyrne/actions/runs/38210436230) | Development push CI; all seven jobs success |
| [38210436174](https://github.com/HodeTech/Tyrne/actions/runs/38210436174) | Development push performance validation; report job success |

Downloaded artifacts were fetched by the coordinating author; this reviewer independently inspected the extracted report, production smoke outputs and parsed probe results. Smoke provenance records clean exact source, current script SHA-256 `cac6e377c442854384ceb9954ab664d9a0b7d95261eb0ddfb4ba98d3e1795c7a` matching the immutable script, and 23 passed cases: 20 synthetic plus three actual private kernel variants. Production debug/release outputs reach userspace exit and all-tasks completion with the expected profile console contract and no configured fault class. The new Undefined Instruction cases are present. This reviewer did not independently download/recompute the service archive digest or rebuild those three hosted mutant kernels.

The downloaded performance report identifies clean full source, pinned compiler/toolchain, QEMU 8.2.2, 20 valid/0 failed samples, and a 100-second full harness run. This reviewer recomputed nearest-rank p10/p50/p90 from its 20 raw samples: `5,232,672 / 5,473,392 / 7,277,776 ns` (`5.233 / 5.473 / 7.278 ms`). Report SHA-256 independently matches `24c143abb0151de1eb3fb38ff3d74f3e060effd2a6c492cc8389bebca565ae85`. The report retains the toolchain identifier and omits the usual override path and hostname. These are informational QEMU measurements, not a calibrated performance gate or hardware benchmark.

**Missing tests that block this delta:** none. A real Undefined Instruction mutant guest is not claimed; the actual token matcher is exercised directly by controlled trace fixtures and positive actual guest integration remains covered. First merged-main and default-branch-only dispatch evidence remains pending maintainer merge.

## Documentation

The fixture README states endpoint/API-version provenance and conservative representability boundaries. The ARM guide explains the identical-command clean baseline and bounded negative acceptance. T-034/T-035/T-036 append the new evidence while retaining `In Review`; no agent Done promotion or ADR revision occurs.

**R1-SEC-01 — Low, nonblocking, independently corroborated:** `.github/workflows/ci.yml:438` still says cargo-bin is omitted here “unlike the sibling jobs.” This delta removed cargo-bin from those sibling caches, so that contrast is stale. Update the comment to describe the current all-job behavior. Root has assigned this to the A round-1 correction before round 2. At immutable `50ab72b` it is still open; this review does not certify the future correction. It is one shared finding, not an additional independent defect count.

The supplied report's remaining prose, examples, historical token references and claim corrections are explicitly allocated to follow-up B. Their absence from A is not a new A blocker, and this review does not clear them. The post-fix token sweep found the old fault token in pre-existing task prose and the newly stale sibling-cache comment; the two have distinct scope dispositions. ADR-0040's implementation policy and the `Refs: ADR-0040` trailer govern this change. No new public Rust item or unsafe contract requires rustdoc or an audit amendment.

## Integration

Prerequisites were read directly, with bounded output and recovery of initial truncations: AGENTS, complete CLAUDE and current roadmap, all 39 existing numbered ADR files in numerical order (0034 is reserved and absent), and all 15 files under standards including the index. The `perform-code-review` and `conduct-review` skills and complete code-review master plan/template were read. The supplied attachment and read-only PR body establish intent; test changes were read before implementation. The broader PR body retains previous validation-tip history and is part of the separate documentation reconciliation, not falsely treated as exact-head proof.

No crate, external dependency, toolchain pin, runtime source, action SHA, token permission or live protection change occurs in A. Removing cached installed binaries does not remove the current explicit install steps. Native Linux ARM and Apple ARM evidence complement each other. Advisory coverage/performance are not promoted to required policy. The full live policy check remains equal to the committed definition; the reviewer made no write call.

### Complete code-review checklist

| Checklist item | Disposition and basis |
|---|---|
| Correctness | Pass; actual response equality, exact ARM clean/mutated command, narrow fault token and metadata controls above |
| Capability semantics | Runtime N/A; no capability/syscall contract changes. Administrative schema continues refusing unknown authority policy |
| Fault containment | Pass within tooling scope; faults reject despite success markers, failure cannot be hidden by metadata or tee controls |
| Unsafe discipline | N/A; no shipped Rust/asm/unsafe/audit-log edits. Existing HIGH T-038 remains excluded and unresolved |
| Error handling | Pass; explicit baseline/empty-diagnostic/status refusal; optional metadata fallback does not suppress failed measurements |
| Tests | Pass; independent normal/optimized suites, causal old-byte controls, native ARM, and exact-head hosted evidence |
| Documentation | Low R1-SEC-01 open; scoped guide/fixture provenance updated; follow-up B deliberately pending |
| Architectural principles | All P1–P12 explicitly considered below |
| Dependencies | N/A; no additions/updates or supply-chain trust change |
| Naming and style | Pass; ShellCheck/actionlint/diff check and manual helpers/quoting review |
| Commit message | Pass for scoped implementation: conventional `fix(ci): strengthen PR review probes and report metadata`, explanatory body, `Refs: ADR-0040`; no unsafe Audit trailer required. Paired assurance artifact publication is coordinated separately |

### Architectural principles P1–P12

| Principle | Outcome |
|---|---|
| P1 — No ambient authority | Preserved; no runtime grants; no CI administrative token and no policy writes |
| P2 — Smallest defensible TCB | Preserved; all changes are host assurance tooling, no kernel growth |
| P3 — Drivers/filesystems/network in userspace | N/A; no subsystem placement change |
| P4 — Capability checks at boundaries | Runtime N/A; policy fixtures retain authority-field refusal before any write |
| P5 — Rust-only kernel | Preserved; no kernel/assembly change; shell/Python are existing host tools |
| P6 — HAL separation | Preserved; no hardware detail enters kernel |
| P7 — No proprietary blobs | Preserved; fixture is text JSON, no binary/firmware introduced |
| P8 — ADR decisions | Preserved; routine controls implement Accepted ADR-0040 without new policy |
| P9 — English repository | Pass; added text/commit English |
| P10 — Mermaid diagrams | N/A; no diagrams/images added |
| P11 — Reproducibility | Preserved/improved metadata attribution; pinned toolchain/dependencies unchanged; timestamp remains measurement metadata, not shipped binary |
| P12 — No half-finished main subsystems | Pass for A's declared scope; no runtime stubs; follow-up B and post-merge evidence remain explicitly pending |

## Verdict

**Approve** for immutable follow-up A round 1, with one **Low nonblocking** documentation finding R1-SEC-01; **0 Blocker, 0 High, 0 Medium** new findings. Blocking list: **none**.

This approval covers the scoped tooling behavior and evidence. The fresh paired security artifact was read in full before final handoff; its scoped Approve, 33 explicit checklist dispositions, eight axes, limitations and shared Low R1-SEC-01 agree with this review. It does not complete the required second fresh round, approve follow-up B, promote tasks to Done, merge PR48, certify first-main/dispatch evidence, or establish universal Rust/kernel safety. The previously known HIGH T-038 register-clobber issue remains outside this change and is not cleared by tests, Miri or smoke success.

### Paired review reconciliation

Read the complete `/tmp/tyrne-pr48-tools-r1-security.md` (204 lines at cross-read) after completing the independent code findings and executions. Its additional 29 adversarial subcases strengthen conservative-policy, near-match diagnostic and failed-output canary coverage; those are peer-executed evidence, not counted as this reviewer's own tests. No unresolved code/security verdict conflict or additional blocker was found. Both reports keep R1-SEC-01 open at exact 50ab and require fresh verification of the forthcoming correction. Canonical publication/index/trailer recording remains the coordinating author's task under this reviewer's no-repository-edit constraint.

## Coordinator publication and finding disposition

The complete reviewer report above is preserved at its immutable reviewed source. The [paired canonical report](../security-reviews/2026-10-12-pr48-tools-followup-r1.md) is published alongside it; private `/tmp` evidence paths remain acquisition locations, not durable links. The coordinator read both full reports and independently verified R1-SEC-01. This publication commit replaces the stale sibling-cache contrast with the current explicit-install/all-cache-bin-omission comment. Actionlint and whitespace checks pass after that comment-only correction. This records the correction, not a reviewer certification of future source; fresh round 2 is still required.
