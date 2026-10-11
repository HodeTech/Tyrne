# Code review 2026-10-12 — T-030 release gates

- **Change:** T-030 on `development`, `8437158..364b746`.
- **Reviewers:** fresh independent `b21_step4_round1_code` (`gpt-6.1-sol` / high requested) and distinct `b21_step4_round1_security` (`gpt-6-astra` / high requested), acting on behalf of @cemililik. Reports distinguish requested configuration from runtime identity.
- **Risk class:** CI enforcement/tooling with test-only syscall imports; production syscall logic and unsafe reasoning unchanged.
- **Security-review cross-reference:** [distinct security review](../security-reviews/2026-10-12-t030-release-gates.md).

> **Current reconciliation:** Round 1 code and security reviews both Approve, with no new actionable finding. Report wording was tightened to say that an additional *passing* matching test fails the two-pass guard; an additional ignored test does not invalidate execution of the two required passing tests. This is a report precision correction, not a source finding. Local and hosted implementation gates passed. Both fresh code/security rounds now Approve with no new actionable finding; independent real and controlled checks confirm the release evidence contract. Final maintainer PR review remains pending; T-030 stays In Review.

## Round 1 code review

- **Date:** 2026-10-12, Europe/Istanbul. Hosted log timestamps are UTC on 2026-10-11.
- **Change:** T-030, approved Track B.2-1 step 4, `development`, `8437158..364b74626d54fffd5a73d6bec833877308eb5285`. Implementation `b8ad56f`, downstream standards `c716ae3`, hosted evidence-only follow-up `364b746`; 14 files, 117 additions / 33 deletions.
- **Reviewer:** fresh independent delegated agent `b21_step4_round1_code`, Codex, acting on behalf of @cemililik. Parent confirms requested spawn configuration `fork_turns: none`, `gpt-6.1-sol`, high reasoning. This is orchestration provenance; an independently verified runtime model identifier is not exposed.
- **Risk class:** CI enforcement and developer tooling, with a test-only import change in a syscall source file. No production syscall gate logic, signature, authority requirement, unsafe region, assembly, BSP implementation, dependency or toolchain changes.
- **Security-review cross-reference:** distinct fresh Round 1 security pass is commissioned separately by the parent. This code review does not substitute for that pass or certify kernel/assembly soundness.
- **Procedure:** `perform-code-review`, `conduct-review`, complete code-review master plan; all five roles completed sequentially. `propose-standard-change` read to audit governance. Task intent and actual release-only tests were read before the executable diff; guard/probe helpers and Cargo configuration before workflow callers and downstream documentation. Parent explicitly requested a read-only temporary report: canonical publication, review index, task history and any commit/trailer reconciliation remain parent-owned.

### Correctness

**No actionable finding.** The new gate closes the specific vanishing-test hazard without changing the syscall mechanism.

The existing ABI release test asserts that number 5 decodes to `None`. The dispatcher release test supplies a valid console capability but expects `BadSyscallNumber` and an empty console capture. Both compile only with `not(debug_assertions)`. They establish the intended release contract at two layers; neither merely checks a source string or restates the guard parser.

`check-release-tests.sh` selects only the kernel library target and both named filters. It requires each fully qualified test's exact successful line and the `2 passed; 0 failed;` summary. Thus zero selected tests, one missing test, an ignored test, a test with an incorrect module-qualified name, additional passing tests, or failure summaries cannot satisfy the gate. Cargo and `tee` run inside a `set -euo pipefail` pipeline, so a command failure cannot be hidden by the output parser. The unpredictable temporary log is removed by EXIT cleanup. The real run succeeded with exactly two tests; controlled Cargo exit 42 propagated even when stdout contained both successful names and a perfect two-pass summary.

`test-ci-gates.sh --release` reuses the existing tracked-current-worktree snapshot and rejection contract. The profile insertion occurs only in the private copied manifest. The probe runs the canonical script, requiring both a nonzero guard status and its specific failure diagnostic. Cargo compilation/tool failures without that diagnostic are not accepted as profile-regression proof. The copied toolchain/configuration selects the repository's pin; its sibling private Cargo target prevents shared cached artifacts from certifying the mutation. Independent controlled inspection verified exactly one `debug-assertions = true` insertion under the release table, the exact Cargo argument vector, private cwd/target, no `.git` or untracked `hello.bin`, and removal of the private root afterward. The actual isolated profile-flip probe passed by observing guard exit 1.

Both aliases preserve target and package selection and add only `--release`. The production fast lane runs full release host tests before the named guard and negative probe. None uses `continue-on-error` or unconditional success. The kernel job performs existing debug work first, builds release userland before release kernel build/clippy, then restores debug userland immediately before the final debug perf-bench build and lint. The perf Cargo features appear before the clippy `--` separator. No flags are appended after the existing alias's rustc delimiter.

The shared image boundary is explicitly handled. `build-userland.sh` writes one profile-dependent `hello.bin`; BSP `build.rs` checks existence and watches changes but cannot establish the image's profile. The workflow restores the correct image at the precise boundary. Hosted logs independently inspected here show 117-byte debug → 69-byte release → restored 117-byte debug, followed directly by successful dev-profile perf build/lint. This is compile coverage, not release guest execution.

The only Rust delta splits three imports under `#[cfg(debug_assertions)]`: `CONSOLE_WRITE_CHUNK`, `MappingFlags`, and `FakeUserMem`. Reference and enclosing-test cfg inspection matches those gates. Shared fixtures and imports needed by the release test stay unconditional. No test assertion or production function changes. The independently compiled release kernel library confirms the scoped imports remain sufficient in that profile.

### Style

**Clean.** Independent default-severity ShellCheck 0.11.0 over `tools/*.sh`, full actionlint 1.7.12, Bash syntax checks, and range whitespace checks pass. The real and controlled scripts execute under macOS `/bin/bash` 3.2.57. Paths containing spaces and glob metacharacters were used in controlled checks. Script modes are executable; existing snapshot copying preserves modes. No new lint suppression, warning relaxation or unnecessary dependency appears.

All three range commits use Conventional Commits, English messages and valid `Refs: ADR-0040` trailers. Implementation also references ADR-0031 and ADR-0039. The existing Accepted ADR precedes the standards commit. No new unsafe audit record is required by an import-only test delta. Separate security review publication/trailer handling remains parent-owned.

### Test coverage

Independent checks performed in this fresh review:

| Check | Observed result |
|---|---|
| Real `tools/check-release-tests.sh`, separate temporary Cargo target | Exit 0; both exact tests pass, 2 passed / 0 failed / 247 filtered |
| Real `/bin/bash tools/test-ci-gates.sh --release` | Harness exit 0; intentional profile change rejected by guard exit 1 and expected diagnostic |
| Controlled valid two-test output | Exit 0, temporary log removed |
| Controlled zero-test / vanished output | Exit 1, cleanup verified |
| Controlled missing ABI test | Exit 1, cleanup verified |
| Controlled missing dispatcher test | Exit 1, cleanup verified |
| Controlled incorrect fully qualified name | Exit 1, cleanup verified |
| Controlled ignored test | Exit 1, cleanup verified |
| Controlled failed summary | Exit 1, cleanup verified |
| Controlled three-pass summary | Exit 1, cleanup verified |
| Controlled Cargo exit 42 with perfect successful test output | Exit 42 propagated, cleanup verified |
| Controlled private profile-flip snapshot and exact command inspection | Correct manifest mutation, cwd, target and argv; no `.git`/`hello.bin`; complete private-root cleanup |
| ShellCheck over every tooling script | 0.11.0; exit 0 at default severity |
| Full actionlint | 1.7.12; exit 0 |
| Changed scripts `/bin/bash -n` | Exit 0 |
| `git diff --check 8437158..364b746` | Exit 0 |
| Changed Markdown relative file targets | 257 references resolve; code examples excluded; not an exhaustive historical-anchor claim |
| Final branch/worktree check | `development`, clean, HEAD `364b74626d54fffd5a73d6bec833877308eb5285` |

Controlled probe source is `/tmp/tyrne-r1-code-probes.py`. The first isolation assertion compared macOS `/var` and `/private/var` path spellings literally and failed in this review fixture; resolving both paths corrected the fixture. The corrected run completed every assertion above. This was not a repository defect or an accepted failed verification.

Root separately supplies local fmt, host clippy, 366 debug and 356 release host passes, debug/release kernel build/clippy, userland clippy, perf build/lint, 59 QEMU argument fixtures, 366 Miri passes with no UB failure and existing warnings, seven additional controlled guard outcomes, and restored debug image hash `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`. Those are attributed implementation results, not all independently repeated here. The new guard's real private-target compilation and targeted adversarial checks address the highest-risk changed contract directly. No new production behavior or unsafe invariant needs an additional Rust test in this delta.

### Documentation

**No actionable finding.** The task criteria and review history distinguish the opening baseline, isolated reproducer, local implementation, and first hosted green. The 356 release count correctly excludes two ignored HAL doctests and differs from 366 debug passes. Local warm 1.49 s and hosted 13 s are labeled separately as build/test wall time, not guest-performance measurements.

The CI job/local-command tables, workflow header and three downstream standards now name release host coverage, the explicit named-test assertion, profile-flip rejection, release kernel build/clippy, and debug perf build/lint after image restoration. The QEMU guide documents both release aliases and the need to restore debug userland afterward. The task and guide explain why Cargo zero-test success is insufficient. T-034 retains ownership of release EL0 runtime enforcement; no current compilation or agent result is presented as hosted guest coverage.

This implements Accepted ADR-0040 and ADR-0039's explicit matching-image pipeline. Standards are minimally updated after the motivating ADR; no Accepted decision is reversed, no new architecture choice is introduced, and P1–P12 need no amendment. The downstream testing/release summaries are updated along with infrastructure, avoiding the discrepancy found during T-031. All three live current-focus pointers, task and task index agree on T-030 `In Review`, implementation gates passed, fresh review rounds pending. Historical dated banners remain history. No premature Done or final-PR/merged-main claim occurs.

### Integration

The existing required job display names, triggers, least-privilege permissions, action SHAs, workspace default-members and Rust pin remain unchanged. The added checks are within already required jobs. The host command omits the bare-metal BSP as intended through `default-members`; the BSP has separate target-aware compilation/linting. The copied release probe reads the same pin and canonical guard. Positive commands run before their expected-failure probes; a deliberately rejected mutation counts as a successful harness, not a failed production workflow.

Direct inspection of parent-downloaded `/tmp/tyrne-b21-step4/hosted-run.json` associates [run 38179424325](https://github.com/HodeTech/Tyrne/actions/runs/38179424325) with exact executable/standards head `c716ae3d312b1a6213ec35346a87940a79af3465` and success in all five jobs. This reviewer did not independently fetch GitHub metadata. Direct inspection of supplied logs corroborates the material claims:

- Fast lane lines 672/928/992/1014 report 46 HAL + 249 kernel + 58 test-HAL + 3 doctests = 356 passes; line 999 records two ignored doctests.
- Lines 1027–1032 show both exact release-only names, two passes and guard PASS; line 1040 shows profile-flip rejection with guard exit 1.
- Kernel lines 173/225/257 show matching image sizes 117 → 69 → 117. Release kernel clippy completes at line 247; final debug perf build/lint complete at lines 266/275.
- Metadata release-host step spans 22:11:52Z to 22:12:05Z, supporting the recorded 13 s hosted step wall time.

The evidence-only `364b746` changes task/current prose after that successful executable head. No executable delta follows the hosted-green `c716ae3`. These are hosted development results; final PR, post-merge main and later smoke/ARM/protection registration evidence remain outside this step.

### Explicit checklist disposition

| Standard item | Disposition |
|---|---|
| Intent before diff / tests first / topological order | Pass; task and actual release tests before guard/configuration/workflow/docs |
| Correctness | Pass; named execution assertion, profile order and matching images |
| Capability semantics | Production authority unchanged; valid-cap release test still requires rejection |
| Fault containment | Kernel fault behavior unchanged; no BSP runtime delta; release runtime remains T-034 |
| Unsafe discipline | No unsafe/assembly/safety-argument changes; no audit amendment needed |
| Error handling | Pipeline failures propagate; absent/partial/wrong/ignored/failed evidence rejected; cleanup observed |
| Tests | Real positive/negative commands and nine controlled outcomes plus isolation assertions pass |
| Documentation | Commands, downstream standards, status pointers and evidence attribution reconciled |
| Architectural principles P1–P12 | No conflict: capability/fault/memory architecture unchanged; explicit build, lean TCB and no binary blobs/dependencies preserved |
| Dependencies | None added or upgraded; dependency workflow N/A |
| Naming/style | ShellCheck/actionlint/Bash syntax/whitespace clean; English and existing conventions |
| Commit messages | Three conventional commits; valid ADR references; standards follow Acceptance |
| Separate security review | Parent commissions distinct pass; this report does not replace it |
| Build/runtime checks | Private host release compilation here; root/hosted build variants explicitly attributed; no new BSP behavior warrants a duplicated smoke run |
| Lifecycle / publication | Development and In Review preserved; parent publishes artifact/index/history; no merge or Done authorization |

### Read coverage and limits

Read full AGENTS/CLAUDE, current focus including historical banners, all 39 existing numbered ADRs in numerical order (0001–0033, 0035–0040; 0034 has no file), every standard including its index, skill index, both full review skills, complete code-review master plan and standard-change procedure. Bounded follow-up reads recovered truncated substantive portions. Read the complete prior preflight and T-031 review artifacts; full T-030 task, approved eight-step sequence/index context, actual release tests and adjacent fixtures/cfg references, both new/extended scripts, complete executable range diff, Cargo configuration/manifests, userland image helper, BSP build script, full workflow and CI guide, changed QEMU guide/standards/status/task portions, all three commit descriptions, and relevant parent-fetched hosted metadata/log evidence.

No claim to reread the entire unchanged syscall dispatcher, userland/assembly implementation, unrelated task backlog, or every historic anchor. No shared image or kernel ELF write, alternate-profile shared build, independent Miri/stable/full-host-suite rerun, guest smoke, SMP/hardware test, performance study, signal/kill stress test, repo edit, branch mutation, commit or GitHub mutation. Normal and guard-error cleanup were exercised; hostile termination cleanup is not claimed. Known T-038 asm debt remains outside this review and cannot be disproved by lint/test success.

### Verdict

**Approve T-030 at `364b746` for this fresh Round 1 code review; no actionable findings.** All five axes and the standard checklist are complete. Real guard/profile-flip checks, adversarial parser/error/isolation verification, and the attributed hosted results support the scoped implementation. Separate security review, the second fresh round and final maintainer PR remain required. This verdict does not promote Done, authorize a merge, certify kernel soundness, or claim release guest coverage.

## Round 2 code review

- **Change:** approved Track B.2-1 step 4, T-030 on `development`, `8437158..5cd9ee8a01ac523e48146e2224284b871e3619ab`. Implementation `b8ad56f`, downstream standards `c716ae3`, hosted evidence `364b746`, Round 1 records `5cd9ee8`; 18 files, 410 additions / 33 deletions including review records.
- **Reviewer:** fresh independent delegated agent `/root/b21_step4_round2_code`, acting on behalf of @cemililik. Parent requests `gpt-6.1-sol`, high reasoning, `fork_turns=none`; these are requested orchestration settings, not an independently attested runtime model identity.
- **Date:** 2026-10-12, Europe/Istanbul; hosted timestamps cited below are UTC on 2026-10-11.
- **Risk class:** security-sensitive context: CI enforcement of the release syscall surface and test-only imports in a syscall module. Production syscall logic, authority, assembly, unsafe bodies and safety arguments are unchanged.
- **Security-review cross-reference:** existing distinct [Round 1 security review](../security-reviews/2026-10-12-t030-release-gates.md) covers the same executable delta. A distinct fresh Round 2 security pass is commissioned separately by the parent and must be reconciled before the step's two-round lifecycle is complete. This report is the code pass only.
- **Procedure:** `perform-code-review`, `conduct-review`, full code-review standard/master plan; five roles executed sequentially. `propose-standard-change` also read to audit standards governance. Task and actual release tests read first, then Cargo/profile prerequisites and guard/probe implementations, workflow callers, downstream documentation and review records. Parent owns canonical publication, review index, task history and any commit/trailer updates; no repository or GitHub mutation was performed here.

### Correctness

**No actionable finding.** The implementation fulfills the narrow release-verification contract without modifying the production mechanism it protects.

The existing ABI test asserts `SyscallNumber::decode(5) == None` under `not(debug_assertions)`. The dispatcher test grants a valid `DebugConsole` capability with `CONSOLE_WRITE`, calls the ordinary dispatcher and requires both the precise `BadSyscallNumber` status and empty console output. This is meaningful despite its empty user window: an accidentally exposed console handler would return a different address error, rather than the required number rejection. Both tests disappear when release debug assertions are enabled; merely running Cargo with their filters cannot establish their presence.

`tools/check-release-tests.sh` selects the kernel library and the two named filters, requires the exact fully qualified successful test line for each, and requires a `2 passed; 0 failed;` summary. Independent real execution in a private tracked snapshot observed both passes and 247 filtered tests. After the isolated release profile flip, the exact raw Cargo command returned exit 0 with zero tests and 259 filtered tests, while the canonical guard returned exit 1 with its specific missing-test diagnostic. This directly reproduces the hazard and verifies its correction.

The evidence parser has the intended scope. Zero matches, either required name missing, a wrong module-qualified name, a required test ignored, a failing summary or a third passing matching test cannot satisfy it. Two required passes plus an additional ignored matching test do satisfy it; the contract proves two passes, rather than banning every possible third match. The script relies on the pinned toolchain's ordinary libtest text format; formatting drift fails closed. The guard is regression detection within a trusted source/compiler environment, not authentication against fabricated compiler/test output.

`set -euo pipefail` keeps a failing Cargo command or `tee` from becoming a green guard. A controlled Cargo stub that emitted a perfect successful transcript and then exited 42 caused the guard to exit 42. The unique `mktemp` log is quoted throughout and removed on normal success and tested error paths. Invalid script arguments return 2 before log creation. Controlled runs used Bash 3.2 and paths with spaces, and verified the exact Cargo argument vector and temporary-log cleanup.

The extended `test-ci-gates.sh --release` inserts `debug-assertions = true` only beneath `[profile.release]` in its private tracked-current-worktree copy. Its preexisting copy loop uses NUL-delimited tracked filenames and preserves executable modes. The copied pin/configuration and fresh private Cargo target prevent certification by the checkout's old release executable. The `run_negative` helper requires both nonzero status and the guard's fixed diagnostic: an unrelated compiler failure alone cannot pass it. Independent execution of the actual repository harness succeeded by observing guard exit 1, and its private directory was absent afterward. The source manifest remained unchanged.

The release build/run aliases preserve the debug aliases' target/package selections and add `--release`. Full host release tests are a separate blocking step before the narrow guard and negative probe. The existing `default-members` restrict that host command to kernel, HAL and test-HAL, while the bare-metal BSP has its own target-aware build/lint steps.

The kernel job's profile transitions are correct and explicit: existing debug image/build/lint; matching release userland, release kernel build and release clippy; restored debug userland immediately before debug `perf-bench` build and clippy. Cargo's feature/target/package flags remain before the clippy `--` delimiter. No new gate has `continue-on-error` or unconditional success handling. `build-userland.sh` writes one profile-dependent `hello.bin`; BSP `build.rs` checks presence and watches changes but does not verify the profile. Therefore the restore step is load-bearing. Source order and inspected hosted logs agree on 117-byte debug → 69-byte release → restored 117-byte debug before final dev-profile perf work. These are compilation/lint claims, not guest execution claims.

The entire Rust delta scopes three test imports with `cfg(debug_assertions)`: `CONSOLE_WRITE_CHUNK`, `MappingFlags`, `FakeUserMem`. Their test references are in existing debug-only tests; common release fixtures and imports remain available. Independent real release and debug test compilation passed. No production function, test assertion, syscall number, capability, unsafe operation or audit reasoning changes.

### Style

**Clean.** Independent default-severity ShellCheck 0.11.0 over all `tools/*.sh`, actionlint 1.7.12 over the workflow, `/bin/bash -n` on both changed scripts and range whitespace checks all pass. No lint relaxation, suppression, new dependency or refactor unrelated to T-030 appears. The guard is executable; snapshot copying preserves executable permissions. Comments, diagnostics, documentation and four commit messages are English.

All four commits have intelligible Conventional Commit subjects and valid ADR references. The implementation names ADR-0040/0031/0039; the standards commit follows the already Accepted governing ADR. Round 1's follow-up records both code/security references and explicitly does not fabricate a retroactive trailer on the initial implementation. An import-only test edit creates no unsafe audit obligation. The final maintainer PR and this round's publication/trailer reconciliation remain parent-owned.

### Test coverage

**Adequate for the declared delta; no missing blocking test.** The highest-risk changed behavior was independently executed, including the real regression and actual negative harness. Broad unchanged checks are attributed below rather than represented as freshly repeated.

Independent commands and fixtures in this round:

| Check | Result |
|---|---|
| Real guard in private tracked snapshot / private Cargo target | Exit 0; both exact release tests pass; 2 passed / 0 failed / 247 filtered |
| Exact raw narrow Cargo command after private release profile flip | Exit 0; 0 passed / 0 failed / 259 filtered; original hazard reproduced |
| Real guard after that same flip | Exit 1; zero tests and required guard diagnostic |
| Real debug ABI contract after restoring private manifest | Exit 0; debug console-number test passes; 1 passed / 258 filtered |
| Actual repository `tools/test-ci-gates.sh --release`, private temporary root | Harness exit 0; deliberate regression rejected at guard exit 1; private probe tree cleaned |
| Controlled valid two-pass evidence | Exit 0 |
| Controlled zero tests | Exit 1 |
| Controlled missing ABI test | Exit 1 |
| Controlled missing dispatcher test | Exit 1 |
| Controlled wrong fully qualified ABI name | Exit 1 |
| Controlled required test ignored | Exit 1 |
| Controlled third passing matching test | Exit 1 |
| Controlled required two passes plus extra ignored match | Exit 0; intentional acceptance |
| Controlled failure summary | Exit 1 |
| Controlled Cargo exit 42 after valid successful transcript | Exit 42; pipeline failure preserved |
| Unexpected guard argument | Exit 2; usage diagnostic |
| Exact Cargo argument vector / temporary gate-log cleanup | Asserted for every controlled Cargo case; cleanup passed |
| ShellCheck 0.11.0, actionlint 1.7.12, Bash syntax, range whitespace | All exit 0 |
| Changed Markdown relative links and heading anchors | 295 relative references, including 26 heading fragments; all resolve |
| Read-only GitHub run metadata for exact reviewed HEAD | All five jobs successful; release/probe/kernel/perf steps successful |
| Branch / worktree / reviewed HEAD | `development`, clean, `5cd9ee8a01ac523e48146e2224284b871e3619ab` |

Independent test driver: `/tmp/tyrne-b21-t030-r2-code-checks.py`; complete captured results: `/tmp/tyrne-b21-t030-round2-code-checks.json`. Python `tempfile.TemporaryDirectory` owns the snapshot, its Cargo target, fixture binaries and temporary logs; cleanup completed. No shared `hello.bin` or kernel ELF was built or overwritten. The actual harness's own implementation was run unchanged and its cleanup observed.

One review-fixture correction was necessary: the first documentation-link scanner treated the literal inline-code example `](...)` in a task criterion as a real link. Excluding inline code and fenced examples corrected the scanner; the corrected full scan passed. This was a reviewer fixture false positive, not a repository defect or an accepted failed check.

Coordinator/task-recorded local evidence separately reports full fmt, host/debug/release/perf/userland clippy, debug/release/perf builds, 366 debug and 356 release host passes, 366 Miri passes with no UB failure and existing warnings, 59 stubbed QEMU argument fixtures, matching image restoration and debug-image SHA-256 `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`. This reviewer did not rerun that entire suite. This round's independent real tests and controlled failure matrix directly test the changed enforcement contract; no new production behavior or unsafe invariant warrants a duplicate guest smoke here. T-034 retains hosted release EL0 runtime enforcement.

### Documentation

**No actionable finding.** The task, CI guide's job/local command tables, workflow header and infrastructure/testing/release standards describe the implemented release host tests, exact named execution assertion, isolated profile-flip rejection, release kernel build/clippy and restored-debug perf build/lint. The QEMU guide provides the two release aliases with a matching-userland prerequisite and an explicit restoration instruction before returning to debug. The new command is documented at the script header and in the guide.

The task's recorded totals are correctly 249 kernel + 46 HAL + 58 test-HAL + 3 doctests = 356 release passes, with two ignored HAL doctests excluded. Debug has 366 passing tests. The first hosted release step spans 13 seconds, distinct from the 1.49-second warm local run and from guest performance. Historical task rows retain their point-in-time pending states; the final row and active current-focus/index pointers agree on T-030 `In Review`, first round passed and second round pending. No final-PR, merged-main, Done or hosted release-runtime claim is made.

Governance is consistent: Accepted ADR-0040 authorizes the CI execution policy; ADR-0030/0031 govern the debug console; ADR-0039 governs the explicit source-built matching-image pipeline. Standards changes are minimal and downstream summaries were updated, with existing references to ADR-0040. No architectural reversal, new policy choice, principle amendment or new ADR is needed. Round 1's parser wording now correctly distinguishes a third passing match from an extra ignored match, independently verified here. Both prior review artifacts preserve T-038's exclusion and honest evidence provenance.

The corrected link scan covers every changed Markdown file's ordinary inline relative links outside code, including heading targets, and reports no broken link. It is not a whole-repository Markdown parser or an external URL availability audit.

### Integration

**Clean within T-030.** No workspace member/default-member, toolchain, lockfile, dependency, third-party action SHA, cache key, workflow trigger, required job display name or permission changes. New checks are ordinary blocking steps in the existing required jobs. Host tests and bare-metal compilation remain target-correct. The negative probe reads the current tracked source and the same canonical guard rather than a historical checkout, and does not commit a broken regression or create an alternate branch.

Hosted evidence has two explicitly different provenances:

1. **Independently fetched exact-HEAD metadata.** `gh run view 38180378759 --json headSha,conclusion,status,url,jobs` returned completed/success at exact `5cd9ee8a01ac523e48146e2224284b871e3619ab`, with all five job conclusions successful. The host release test, explicit syscall guard, profile-flip probe, release kernel build/clippy, debug-image restoration and perf build/lint steps are individually successful. The metadata is saved at `/tmp/tyrne-b21-t030-round2-code-hosted.json`. [Exact-HEAD hosted run](https://github.com/HodeTech/Tyrne/actions/runs/38180378759).
2. **Direct inspection of coordinator-downloaded first-green metadata/logs.** `/tmp/tyrne-b21-step4/hosted-run.json` identifies successful run `38179424325` at `c716ae3d312b1a6213ec35346a87940a79af3465`, all five jobs green. This reviewer inspected those supplied files; their original download was the coordinator's. Fast-lane log lines 672/928/992/1014 corroborate 46 + 249 + 58 + 3 = 356 release passes; line 999 records two ignored doctests; lines 1027–1032 show both exact names, two passes and guard PASS; line 1040 shows the isolated flip rejected at exit 1. Kernel log lines 173/225/257 show 117 → 69 → 117 bytes; lines 247/266/275 show completed release clippy and final debug perf build/lint. Metadata supports the first release step's 13-second span. [First-green hosted run](https://github.com/HodeTech/Tyrne/actions/runs/38179424325).

`git diff --name-only c716ae3..5cd9ee8` contains only task/current/review Markdown and indexes, so the earlier detailed logs cover the same executable delta; the second metadata fetch additionally establishes a full green run at the exact reviewed tip. No claim is made to independently download or inspect the second run's full logs. These are development/pre-merge results; post-merge main, final PR approval, runtime smoke, ARM-job registration and later protection changes are not inferred.

#### Complete code-review checklist

| Required item | Explicit disposition |
|---|---|
| Intent first / actual tests before implementation / topological traversal | Pass; task and release tests, then prerequisites/guard/probe, workflow and downstream docs |
| Correctness | Pass; tested named execution, profile-flip rejection and matching-image order |
| Capability semantics | No production change; valid-cap release rejection remains asserted before handler side effects |
| Fault containment | No fault handling or BSP runtime change; no new userspace-to-kernel failure path; T-034 owns runtime verification |
| Unsafe discipline | No new/modified unsafe, assembly or safety reasoning; no audit record/amendment needed; T-038 not certified |
| Error handling | Real/controlled failure paths propagate; unrelated failures cannot independently satisfy the negative probe |
| Tests | Real positive, reproduced regression, actual negative harness, debug contract and controlled adversarial cases pass |
| Documentation | New commands/profile obligations and status/evidence distinctions documented; links checked |
| Architectural principles | All P1–P12 explicitly considered below |
| Dependencies | None added/upgraded; add-dependency procedure not triggered |
| Naming/style | English, minimal cfg import scopes, executable scripts, independent ShellCheck/actionlint/syntax clean |
| Commit messages | Four intelligible conventional commits, valid ADR references, truthful review follow-up |
| Post-fix downstream sweep | Release commands and summaries reconciled across workflow, guides, task/index/current and three standards; no production rename |
| Separate security review | Same-delta Round 1 security artifact read; distinct fresh Round 2 pass is separately commissioned and parent must reconcile it |
| Local execution / behavioral validation | Independent private host execution and failure reproduction completed; unchanged guest behavior does not require an additional T-030 smoke |
| Canonical output/index/lifecycle | Parent explicitly owns publication/index/history; this full temporary report is the requested deliverable; no Done or merge action |

#### Architectural principles P1–P12

| Principle | Disposition |
|---|---|
| P1 — No ambient authority | Pass for delta; release number rejection is enforced without granting new authority |
| P2 — Smallest defensible TCB | Pass; only host verification grows, production code unchanged |
| P3 — Drivers/filesystems/network in userspace | Unaffected; no subsystem placement change |
| P4 — Capability checks at trust boundaries | Pass for delta; unchanged runtime checks and valid-cap release-denial test remain meaningful |
| P5 — Rust-only kernel / audited assembly | Pass for delta; shell/Python here are host tooling; no assembly or unsafe edit approved |
| P6 — HAL separation | Pass; cfg-scoped test imports retain HAL/fake abstractions; no board detail enters kernel runtime |
| P7 — No proprietary binary blobs | Pass; matching images built from existing Rust source; no committed binary |
| P8 — ADR governance | Pass; Accepted ADR-0040 and existing 0030/0031/0039 govern the work; standards follow Acceptance |
| P9 — English artifacts | Pass; changed artifacts, diagnostics and commits are English |
| P10 — Mermaid diagrams | Not triggered; no diagram added |
| P11 — Reproducibility | Preserved for delta; pin/lock unchanged, isolated negative target and explicit matching profile order; no bit-for-bit reproducibility certification |
| P12 — Complete declared scope | Pass for T-030 implementation; review lifecycle and T-034 runtime ownership remain explicit; task stays In Review |

#### Read coverage and limits

Read full AGENTS and CLAUDE, current roadmap including historical banners, all 39 existing numbered ADRs in numerical traversal (0001–0033, 0035–0040; reserved 0034 has no file), every standards file including its index, skill index, both applicable review skills, complete code-review master plan and standard-change skill. Bounded follow-up reads recovered truncated substantive portions. Read full prior Track B.2-1 preflight, current T-030 Round 1 code/security artifacts, T-030 task, approved sequence/index context, actual release tests and adjacent fixtures/cfg references, complete changed scripts/configuration/workflow, image helper/BSP build script, full CI guide, changed QEMU guide/task/status/standards/index material, four commit descriptions and hosted evidence described above.

This is full governing-document coverage plus focused change review, not a re-audit of every unchanged subsystem. No complete unchanged dispatcher/assembly reread, full roadmap backlog re-review, hardware/SMP test, guest QEMU execution, new performance study, broad fresh Miri/stable/full-host rerun, signal/kill cleanup stress test, hostile toolchain/process test or external URL crawl is claimed. Normal and tested error cleanup passed. Shell/regression tooling assumes trusted tracked source and ordinary Cargo/libtest output. Known HIGH T-038 (`x2` clobber/safety-claim debt in the userland console shim) is unchanged, excluded and unmitigated by these gates; compiling/linting or passing host Miri does not certify SVC assembly soundness.

### Verdict

**Approve T-030 at `5cd9ee8` for this fresh Round 2 code review. No actionable findings and no source correction requested.** All five axes, every code-review checklist item and P1–P12 are covered. Independent real positive/regression/negative checks, controlled failure cases, inspected first-green logs and independently fetched exact-tip hosted metadata support the scoped verdict.

The parent must reconcile the separate fresh Round 2 security verdict and publish the complete reports before declaring the two-round step cycle complete. T-030 remains `In Review` for the final maintainer PR. This review does not promote Done, merge, certify whole-kernel/assembly safety, or claim hosted release EL0 coverage.
