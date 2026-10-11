# Code review 2026-10-12 — T-030 release gates

- **Change:** T-030 on `development`, `8437158..364b746`.
- **Reviewers:** fresh independent `b21_step4_round1_code` (`gpt-6.1-sol` / high requested) and distinct `b21_step4_round1_security` (`gpt-6-astra` / high requested), acting on behalf of @cemililik. Reports distinguish requested configuration from runtime identity.
- **Risk class:** CI enforcement/tooling with test-only syscall imports; production syscall logic and unsafe reasoning unchanged.
- **Security-review cross-reference:** [distinct security review](../security-reviews/2026-10-12-t030-release-gates.md).

> **Current reconciliation:** Round 1 code and security reviews both Approve, with no new actionable finding. Report wording was tightened to say that an additional *passing* matching test fails the two-pass guard; an additional ignored test does not invalidate execution of the two required passing tests. This is a report precision correction, not a source finding. Local and hosted implementation gates passed. The second fresh round and final maintainer PR review remain pending; T-030 stays In Review.

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
