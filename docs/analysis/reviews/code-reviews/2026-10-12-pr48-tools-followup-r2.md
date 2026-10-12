# Code review 2026-10-12 — PR48 follow-up A, fresh round 2

- **Change:** [PR48](https://github.com/HodeTech/Tyrne/pull/48), immutable cumulative `1e281ac89d791dc3c6920a038ec26381a49623f3..683965b5aa2f5da2e11429aa42803bb3a5fa6f60`, development only.
- **Reviewer:** fresh independent Codex agent `/root/pr48_tools_r2_code`, acting for @cemililik in all five canonical roles sequentially; distinct from implementation, round-1 reviewers and round-2 security agent.
- **Date:** 2026-10-12.
- **Risk class:** Security-sensitive assurance tooling; paired security review required.
- **Security-review cross-reference:** `/tmp/tyrne-pr48-tools-r2-security.md`; coordinator owns canonical publication.
- **Scope:** follow-up A tooling/fixtures and its round-1 correction/publication. Follow-up B documentation remains planned and is not approved here. No repository or remote mutation was performed by this reviewer.

## Correctness

**New findings: none; blocking findings: none.** Each scoped behavior was checked afresh across the full cumulative range rather than relying on round-1 approval.

- **ARM attribution and refusal:** `tools/test-ci-gates.sh:83–110` defines the exact all-target workspace clippy command once. It validates six original hello cfg anchors, runs the same command on unmodified private source/private target, and stops on any failed baseline. Only then does it replace those six predicates, preserving the build script/syscall shim, and require compiler exit 101 plus an exact complete duplicate-panic or no-std-unwind diagnostic. Empty diagnostic refusal at lines 45–49 precedes the negative command. Fixtures verify clean→mutated order, failure stopping before mutation, wrong statuses, success, unrelated/near-match diagnostics, host/anchor/copy/CLI refusal, original-byte preservation and cleanup. This establishes the intended controlled regression assertion under trusted tools, not general compiler-output authenticity or exclusion of every possible external coincident failure.
- **Smoke fault detection:** `tools/smoke.sh:151` and `tools/test-smoke-gates.py:21` now use the producer's actual `Undefined Instruction` token, consistent with the BSP standard. Both profile fixtures retain the success markers while adding the fault; both reject it. Existing marker and release-greeting contracts are preserved. This is a specific matcher correction, not exhaustive CPU-fault detection or an adversarial-EL0/runtime-safety proof.
- **Performance reporting:** `tools/perf-harness.sh:251–264` treats failed uname/QEMU-version/rustc/rustup discovery as unknown metadata, discarding failed partial stdout and suppressing stderr. Normal rustup override explanation is removed while the toolchain identifier remains; `uname -srm` omits hostname. Failed measurements still fail the existing threshold; optional metadata does not turn them into success. Sample accounting, watchdog/statistics, source-state attribution and append-only report refusal remain intact. Minimization applies to normal metadata fields, not arbitrary successful output from hostile/custom tools or every auxiliary artifact.
- **Protection response coverage:** `tools/test-branch-protection.py:105–125` normalizes the complete captured protection-endpoint fixture to the entire committed policy and separately refuses summary/enforcement/review-actor extensions. Production adapter and policy definition are byte-unchanged. The dated fixture is observed-shape coverage, not future live-policy equality, permission to drop policy-bearing fields, or administrative write authority.
- **Cache changes:** five cargo-bin cache paths are removed while explicit installations, registry/git/target paths, architecture keys, action pins and token permissions remain. The coverage comment now accurately states all CI caches omit cargo-bin. Existing generated build-cache trust is not eliminated by this change.

## Style

**Findings: none.** ShellCheck 0.11.0, actionlint 1.7.12 against both explicit workflow files, and immutable-range whitespace checking pass. Quoting, Bash arrays, focused fixture helpers and explicit exception checks fit existing tooling. The corrected YAML comment's indentation has no semantic effect and is understandable; it is not a substantive style defect. No Rust style or unsafe exception is introduced.

## Test coverage

### Independent exact-source execution

Extracted `git archive 683965b5aa2f5da2e11429aa42803bb3a5fa6f60` into a private temporary tree. Archive SHA-256 `f09c5623bfc2f4de2ea91770e061c79a1def216887576bf9e8c6df8d45388ff1`; 410 tracked files. A separate read-only Git shim answers only tracked inventory, exact reviewed HEAD and hash-compared tracked status. All other Git operations are refused. This supplies the metadata absent from a Git archive without creating a private branch/commit; it is not a test of Git itself. Real Bash/Python/Cargo/rustc and the probe code were unchanged. Private outputs/logs are located by `/tmp/tyrne-pr48-code-r2-dir`; no shared target, image or build output was used. Manifest recheck after experiments reports zero changed tracked source files.

Environment: Darwin 27.0.0 arm64, Rust host `aarch64-apple-darwin`, pinned nightly 2026-01-15, rustc 1.94.0-nightly `86a49fd71` (2026-01-14), LLVM 21.1.8.

| Independently executed check | Outcome and interpretation |
|---|---|
| `python3 tools/test-branch-protection.py`, and `python3 -O ...` | 29 methods pass each; fake API, no administrative calls |
| `python3 tools/test-perf-harness.py`, and `python3 -O ...` | 7 methods pass each; synthetic measurements/metadata/privacy/failure/overwrite/tee controls |
| `python3 tools/test-arm-host-probe.py`, and `python3 -O ...` | 11 methods pass each; controlled diagnostics/argv/order/status/isolation/refusal |
| `python3 tools/test-smoke-gates.py --artifact-dir <private-new-dir>` | 20 synthetic cases pass, completed JSON; no local guest build claimed |
| `bash tools/test-ci-gates.sh --arm-host` | Actual native Apple ARM clean clippy followed by intentional six-cfg failure 101/E0152; pass |
| `shellcheck tools/*.sh` | Pass, default severity |
| `actionlint .github/workflows/ci.yml .github/workflows/performance.yml` | Pass |
| `git diff --check <immutable-base> <immutable-head>` | Pass |

Initial bare `actionlint` discovery returned 3 because the archive has no `.git`; explicit workflow arguments resolved that environment prerequisite. One intermediate metadata-sensitivity driver attempted `git show` after installing the deliberately restrictive shim into its process PATH and stopped with 90; the corrected driver acquired base bytes through real `/usr/bin/git` before fixture execution. Neither failed setup is counted as a passing check. Python `-O` applies to the top-level suite; stub subprocess shebang interpreters are not thereby all optimized. Unittest assertions and production explicit exceptions remain active.

### Independent old-source sensitivity

In the private tree only, new tests were retained while the relevant production script was replaced with base 1e281ac bytes, then restored:

- The ARM baseline-refusal method fails against old bytes in all nine diagnostic/status subcases because its first invocation is already mutated (`False` instead of `True`). At reviewed head the complete 11-method suite passes.
- New smoke fixtures fail old bytes at `debug-fault-5`: expected fault rejection 1, observed 0. Reviewed head passes all 20, including Undefined Instruction in both profiles.
- An isolated rustc-metadata failure control uses a neutral uname stub accepting either invocation, avoiding confounding fallback with the independent uname-argument change. Base bytes exit 127 and write no report; reviewed head exits 0, preserves three valid samples, writes unknown compiler metadata and omits the failed-output canary. The full new suite additionally covers all four commands at exits 1/127.
- No old-source failure is expected for the added REST capture: adapter behavior deliberately remains conservative and unchanged.

**Missing tests that block A: none.** Actual Undefined Instruction mutant guest execution is not claimed. Full local Rust/Miri/kernel guest suites were not independently repeated for this host-only delta; actual Apple ARM compiler rejection and scoped fixtures were rerun, and hosted integration is separately attributed below.

### Parent-acquired hosted evidence independently inspected

These service summaries/logs/downloads were acquired by the coordinator, then independently parsed/read by this reviewer. This is not independent API retrieval, archive authentication or local re-execution of the hosted guests.

| Hosted source/run | Inspected result |
|---|---|
| Exact 683965b [PR 38212028399](https://github.com/HodeTech/Tyrne/actions/runs/38212028399), [push 38212023751](https://github.com/HodeTech/Tyrne/actions/runs/38212023751) | Full immutable SHA, correct event, completed/success and all seven jobs success in each parent-fetched JSON |
| Exact 50ab [PR 38210439123](https://github.com/HodeTech/Tyrne/actions/runs/38210439123), [push 38210436230](https://github.com/HodeTech/Tyrne/actions/runs/38210436230) | Full 50ab SHA, correct events, completed/success and seven jobs success each |
| Exact 50ab [performance 38210436174](https://github.com/HodeTech/Tyrne/actions/runs/38210436174) | Development push, completed/success; informational report job success |

`smoke-50ab` completed results name full 50ab, clean tracked state, current smoke digest and 23/23 passing cases: 20 synthetic plus three actual private kernel variants. Independently read production debug/release output: debug greeting/exit/completion; release exit/completion without greeting; neither configured fault class appears. Both fault-5 raw fixtures contain Undefined Instruction. `arm-50ab.log` identifies actual native Linux ARM and rejection 101/E0152; native and Miri each have 366 passing tests and two ignored HAL doctests. Successful baseline stdout is not separately retained, so baseline pass follows from the reviewed fail-closed flow plus overall probe success rather than a quoted baseline log.

The committed exact-byte performance snapshot names clean full 50ab source, 20 valid/0 failed, 100-second harness run, QEMU 8.2.2, pinned toolchain identifier, and hostname/override-path minimization. Independently recomputed its file SHA-256 `24c143abb0151de1eb3fb38ff3d74f3e060effd2a6c492cc8389bebca565ae85` and nearest-rank p10/p50/p90 from all 20 raw values: **5,232,672 / 5,473,392 / 7,277,776 ns**. This is an informational QEMU band; no calibrated regression or hardware-performance verdict. Service artifact-archive digest was not independently recomputed. Perf harness, performance workflow, smoke and ARM probe bytes are identical between 50ab and 683965b; this supports relevance of earlier scoped behavioral evidence but does not relabel it as a 683965b performance run. First-main and default-branch dispatch remain merge-dependent.

## Documentation

**New findings: none. R1-SEC-01 resolved at immutable 683965b.** At `.github/workflows/ci.yml:438–439`, the obsolete “unlike the sibling jobs” contrast has been replaced by explicit tool installation/all-CI-cache bin omission. A token sweep plus the five-path diff verifies the correction; actionlint passes after it. This closes the one shared Low round-1 issue, without duplicating its count as a new defect.

The fixture README names endpoint/API-version and conservative extension boundaries. The ARM guide now explains same-command baseline attribution. New task history and round-1 publication preserve immutable-source/time distinctions, paired reports, pending fresh R2/B, known HIGH and merge-dependent evidence. All eight task status fields remain In Review. Existing broader PR-body/documentation reconciliation is expressly follow-up B; it is neither approved by this verdict nor raised prematurely as a new A blocker. No Rust public item, unsafe contract, ADR outcome or runtime architecture changed.

## Integration

Prerequisites read directly: AGENTS, complete CLAUDE/current roadmap; all 39 actual numbered ADRs in numerical order (0001–0033, 0035–0040; 0034 absent); all 15 standard files including README; perform-code-review/conduct-review skills; complete code master plan/template; both full round-1 reports; supplied Turkish attachment. Initial long-output truncations were recovered by bounded reads. Read-only `gh pr view 48` description was read before tests; it reflects earlier PR context, while the explicit assigned immutable scope is authoritative. Fixtures/test source were read before implementation; source/callers/workflow/docs cumulative diff was then inspected. All 19 changed files were covered, including added reports/index/history files.

No crate/dependency/toolchain/action-pin/token-permission/runtime-Rust/asm/unsafe/ADR/audit/production-policy-adapter/definition change occurs in this range. Existing policy remains six app-bound checks with strict checking and retained non-status settings. No live apply/check/export was performed by this reviewer; offline schema equality is not a live drift claim. No task promotion, checkout, commit, push, API write, PR comment or message to external persons was made. Root owns repository artifact/index/trailer publication.

### Complete code-review checklist

| Item | Disposition and evidence |
|---|---|
| Correctness | Pass; exact-command baseline, bounded diagnostics, token matcher, optional metadata and full capture equality |
| Capability semantics | Runtime N/A; no capability contract changes. Administrative unknown authority fields remain refused |
| Fault containment | Pass within tooling scope; success markers cannot hide configured faults; optional metadata does not mask failed measurements |
| Unsafe discipline | N/A to delta; no changed unsafe/asm/audit. Existing HIGH T-038 x2 clobber remains open/excluded |
| Error handling | Pass; explicit baseline/empty/status/refusal paths and unknown metadata; failure pipeline controls pass |
| Tests | Pass; independent normal/-O suites, native compiler, synthetic smoke, before/after controls and attributed hosted evidence |
| Documentation | Pass for A; shared Low corrected, B deliberately pending |
| Architectural principles | P1–P12 considered individually below |
| Dependencies | N/A; graph/pins unchanged, stdlib Python/existing Bash tools only |
| Naming/style | Pass; tooling lints, manual quoting/helpers and whitespace check |
| Commit messages | Pass; conventional scoped fix/publication subjects, explanations and valid ADR-0013/0040 references; R1 trailers accurately scoped 50ab, no unsafe Audit trailer needed |

### Architectural principles P1–P12

| Principle | Disposition |
|---|---|
| P1 No ambient authority | Preserved; no runtime grants or CI admin credential |
| P2 Smallest defensible TCB | Preserved; host tooling only, no privileged source growth |
| P3 Userspace drivers/filesystems/network | N/A; no subsystem placement change |
| P4 Capability checks at boundaries | Runtime unchanged; administrative conservative schema checks preserved |
| P5 Rust-only kernel | Preserved; Bash/Python remain host tools, no new kernel/assembly source |
| P6 HAL separation | Preserved; no HAL/kernel interface or hardware placement change |
| P7 No proprietary blobs | Preserved; text JSON/report fixtures only, no committed guest binary |
| P8 ADR decisions | Pass; Accepted ADR-0040 governs routine tooling controls; no new policy decision |
| P9 English repository | Pass for changed artifacts/commits; Turkish attachment is external review input |
| P10 Mermaid diagrams | N/A; no diagram added |
| P11 Reproducibility | Preserved; pins unchanged, normal source/toolchain provenance retained and optional unknown explicit; measurement timestamp is report metadata |
| P12 Complete declared scope | Pass for A; no runtime stubs; B, maintainer review and merge-dependent proof explicitly pending |

## Verdict

**Approve for follow-up A at immutable 683965b; zero new Blocker/High/Medium/Low findings. Blocking list: none.** Independent work and the complete provisional report were finished before awaiting the fresh paired security report. Its full artifact was then read and reconciled as recorded below. This scoped verdict does not approve B, merge PR48, promote any of the eight tasks, certify future tips/main/dispatch or establish runtime safety. Existing **HIGH T-038 x2 clobber remains open and excluded**, undowngraded by green tests/Miri/smoke.

## Paired-review reconciliation

Read the complete 192-line `/tmp/tyrne-pr48-tools-r2-security.md` after writing this complete independent provisional report. The fresh peer Approves the same immutable cumulative range with zero new findings and verifies R1-SEC-01 resolved. Its eight axes, all 33 explicit checklist dispositions, P1–P12, source/evidence limitations and retained HIGH T-038/B/merge-dependent exclusions agree with this review. Its additional 42 adversarial subcases, normal and optimized, are peer-executed evidence, not this reviewer’s tests. No unresolved verdict conflict or additional blocker emerged. Coordinator publication/index/trailers remain separate from review execution.

## Coordinator publication

The complete report above is published with the [paired canonical security report](../security-reviews/2026-10-12-pr48-tools-followup-r2.md). Private paths identify ephemeral acquisition/execution locations. The coordinator read both complete reports and reconciled their matching Approve verdicts, zero new findings and verified R1-SEC-01 correction. This completes both fresh rounds for follow-up A; follow-up B remains a separate implementation/review step. No task promotion or merge is performed.
