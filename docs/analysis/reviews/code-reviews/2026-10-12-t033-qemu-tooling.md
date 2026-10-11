# Code review 2026-10-12 — T-033 QEMU tooling

- **Change:** T-033 on `development`, `3a7c264..d5c13a0`.
- **Reviewers:** `b21_step2_round1_code`, `b21_step2_round1_integration`, `b21_step2_round2_code`, `b21_step2_round2_integration`, acting on behalf of @cemililik. Orchestration requested `gpt-6.1-sol` with high reasoning for each; round-2 reports state their own runtime-visibility limits.
- **Risk class:** Ordinary.
- **Security-review cross-reference:** n/a — developer tooling, argument tests, workflow integration and documentation only; no kernel, HAL, syscall, scheduler, boot assembly or `unsafe` implementation changes.

> **Current reconciliation:** Round 2 integration identified Low R2-INT-01: the newly refreshed guide repeated an inherited WFI claim. Source `task_a` actually spins after completion. The maintainer-facing guide and matching live smoke/performance descriptions are corrected; previous review prose below is preserved as reviewed-snapshot history, and its WFI statements are superseded by this note. No runtime implementation changed. All four scoped verdicts are Approve; final maintainer PR review remains pending.

## Round 1 code review

### 1. Scope and verdict

**Approve. No introduced blocking or non-blocking findings.**

Reviewed `3a7c264..d5c13a0` on `development`, ending at `d5c13a046db2e8a90d339f39efb651ed4c3bed9e`.

**Risk class: Ordinary.** This change modifies developer tooling, argument tests, workflow integration and documentation. It changes no kernel, HAL, syscall, scheduler, boot assembly or `unsafe` implementation. A separate security-review artifact is therefore not required for this range.

Approval covers T-033's declared tooling scope. It establishes neither SMP runtime support nor maintainer approval to merge or promote the task to `Done`.

### 2. Read coverage and procedure

Read `AGENTS.md` and `CLAUDE.md` in full before reviewing implementation, followed by `docs/roadmap/current.md`, all 39 numbered ADRs in numerical order (`0001`–`0040`, excluding reserved/unwritten `0034`), and all 15 files under `docs/standards/`. Any truncated orientation output was repaired with bounded reads.

Read both applicable skills in full:

- `.agents/skills/perform-code-review/SKILL.md`
- `.agents/skills/conduct-review/SKILL.md`

Read the code-review master plan and the preceding Track B.2-1 preflight artifact. Read T-033's intent and acceptance criteria, then the complete new test harness **before** the implementation. Reviewed the complete runner scripts, Cargo configuration, all changed Markdown documents and the workflow's affected job/context. Inspected the entire range's diff and both commit messages.

Supporting source reads included `tools/build-userland.sh`, `bsp-qemu-virt/build.rs`, and the locations of the documented runtime markers.

No tracked files, commits or branches were changed during the review. Negative experiments used disposable temporary copies. This report was subsequently saved at the root reviewer's explicit request.

### 3. Correctness

**Clean.**

Both runners implement the documented precedence: the last `--smp N`, then `QEMU_SMP`, then `1`. Validation occurs after parsing, allowing a valid explicit flag to override an invalid or empty environment value. Invalid final values fail before QEMU or default builds run.

Missing `--smp` and `--timeout` operands produce usage diagnostics and exit `2`, without accessing an unset `$2`. Both scripts preserve an explicit ELF containing spaces as one argument. The smoke script now rejects additional positional ELF arguments consistently.

The regex validates decimal text directly rather than performing shell arithmetic, avoiding arithmetic interpretation or overflow during validation. Very large positive decimal text is forwarded unchanged; this proves argument handling, not QEMU acceptance of that core count.

Independent boundary probes covered whitespace, newline, leading zero, plus sign, repeated valid/invalid flags, empty environment override, help with an invalid environment, missing operands and repeated timeout options.

### 4. Style and portability

**Clean for introduced code.**

Executed on macOS with:

```sh
/bin/bash --version
/bin/bash -n tools/run-qemu.sh tools/smoke.sh tools/test-qemu-tooling.sh
git diff --check 3a7c264..d5c13a0
```

Bash was **3.2.57**. Syntax and diff checks passed. A separate test run placed a `/bin/bash` symlink first on `PATH`, forcing the harness and both runners' `#!/usr/bin/env bash` invocations onto Bash 3.2; all 59 cases passed.

The new harness has executable mode `100755`. New repository prose and commit messages are English. Both commits follow the existing Conventional Commits convention and contain `Refs: ADR-0040`.

### 5. Test coverage and sensitivity

**Adequate for the declared change.**

Reproduced:

```sh
/bin/bash tools/test-qemu-tooling.sh
```

Result:

```text
PASS: 59 QEMU tooling argument cases (stubbed QEMU; no SMP claim)
```

Additionally ran **25 independent stub cases** using `/bin/bash`, a temporary QEMU executable, an ELF containing spaces, captured argv and explicit exit-code assertions. All passed. These independently checked the default, malformed inputs, precedence boundaries, missing operands and timeout repetition.

Tested the permanent harness against **nine isolated mutants**. Every mutant was rejected with exit `1`:

- Ignoring explicit SMP precedence in either runner.
- Removing `run-qemu.sh`'s missing-value guard.
- Removing `smoke.sh`'s missing-timeout guard.
- Disabling SMP validation in either runner.
- Hard-coding forwarded SMP to `1` in either runner.
- Restoring silent acceptance of an additional smoke ELF.

Reproduced the original timeout bug from an isolated copy of:

```sh
git show 3a7c264:tools/smoke.sh
```

Running that copy with `--timeout` returned `1` and reported `$2: unbound variable`; the current runner returns `2` with its flag-specific usage diagnostic. This confirms regression sensitivity against the baseline, beyond testing only the patched implementation.

Ran the real default single-core integration path:

```sh
env -u QEMU_SMP tools/smoke.sh --int --timeout 5
```

**PASS**, using QEMU **11.1.1**. The build produced the **117-byte debug hello image**, whose SHA-256 remained:

```text
05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88
```

The captured trace showed:

```text
hello from userspace
tyrne: userspace task exited
tyrne: all tasks complete
```

It contained exactly **two expected SVC exceptions on CPU 0**, with no panic or fault class. Trace location:

```text
/var/folders/d2/k7c1fj3976g7_qq7113f66p00000gn/T/tyrne-smoke.51834.log
```

No alternate-profile userland or multi-core guest was built or run.

### 6. Documentation

**Clean.**

The refreshed guide correctly requires building matching-profile userland before the kernel, describes the current EL0 markers and WFI completion behavior, distinguishes release greeting behavior, and documents both shell and Cargo runner overrides.

The unsupported status of `N > 1` is explicit. The guide does not imply that accepting a core-count argument establishes secondary-core bring-up.

Reproduced the documented Cargo override:

```sh
CARGO_TARGET_AARCH64_UNKNOWN_NONE_RUNNER=echo cargo kernel-run
```

It printed:

```text
target/aarch64-unknown-none/debug/tyrne-bsp-qemu-virt
```

Independently checked all relative Markdown targets in the six changed Markdown files, excluding inline-code examples: **240 targets and 24 anchors resolved; zero failures**.

Lifecycle wording remains honest: T-033 is `In Review`; the guide index labels its refresh `In Review`; hosted and fresh-review evidence pending at the reviewed commit is not represented as already complete. The existing completion-only smoke gate is accurately distinguished from T-034's forthcoming debug/release EL0 enforcement.

### 7. Integration and existing findings

**Clean for this range.**

The permanent argument suite is in the existing required fast lane, needs no real guest or kernel build, and adds no framework or dependency. The static Cargo runner retains `-smp 1`. Existing interactive and default smoke behavior remains intact.

Reproduced:

| Command | Result |
|---|---|
| `actionlint -shellcheck=''` | Exit `0`; workflow/schema checks pass |
| `shellcheck tools/run-qemu.sh tools/smoke.sh tools/test-qemu-tooling.sh` | Exit `1`; only existing smoke SC2054 |
| `actionlint` | Exit `1`; existing SC2086 findings on unquoted `NIGHTLY_PIN` expansions |
| `git status --short` | Empty at completion of the read-only review |

The SC2054 expression is unchanged from baseline `3a7c264:tools/smoke.sh`; the workflow expansions likewise predate this range. Their immediate owner is **T-031**, and T-033's history records them accurately. They are not introduced T-033 findings.

Hosted evidence was **provided by the root reviewer**, not independently fetched in this pass: [d5c13a0 CI run](https://github.com/HodeTech/Tyrne/actions/runs/38176428435) succeeded, and the root inspected the fast-lane log containing the new step's **PASS59** result.

I did not independently rerun the unrelated Rust fmt/clippy/host-test gates; those are author-recorded evidence. The real smoke independently rebuilt the default userland and kernel.

### 8. Full checklist

| Review item | Outcome |
|---|---|
| Correctness | Pass; parser, precedence, validation and forwarding independently exercised |
| Capability semantics | Unaffected; no guest authority boundary changed |
| Fault containment | Unaffected; real single-core smoke remains fault-clean |
| `unsafe` discipline | N/A; no `unsafe` or audit entry changed |
| Error handling | Pass; malformed arguments exit `2` before side effects |
| Tests | Pass; 59 permanent cases, 25 independent cases, nine rejected mutants, baseline regression reproduction |
| Documentation | Pass; guide contracts and lifecycle consistent; links and anchors resolve |
| Architectural principles | P1–P7 unaffected; P8 follows Accepted ADR-0040; P9 English; P10 no diagrams; P11 pins/dependencies unchanged; P12 scope complete without an SMP-support claim |
| Dependencies | None added |
| Naming/style/portability | Pass; Bash 3.2 execution and syntax checks |
| Commit messages | Pass; conventional subjects and valid ADR trailer |
| Workflow integration | Pass; executable dependency-free harness in required fast lane |
| Security-review cross-reference | N/A for this ordinary tooling range |
| Review artifact/index | Report saved at the root reviewer's request; index updates remain outside this reviewer's authorized write scope |

**Final verdict: Approve T-033 at `d5c13a0`.** No confirmed introduced issue requires a fix before the second fresh review round.

## Round 1 integration review

- **Change:** `development`, `3a7c264..d5c13a0` — 11 files, 263 insertions and 91 deletions.
- **Reviewer/model:** `b21_step2_round1_integration` (`gpt-6.1-sol`, high).
- **Review date:** 2026-10-12.
- **Risk class:** Ordinary tooling/documentation change. No Rust, assembly, capability, memory-management or `unsafe` implementation changes.
- **Security-review cross-reference:** No mandatory separate security review identified for this diff. This review makes no kernel soundness or SMP-support claim.
- **Verdict:** **Approve within this review’s scope. No actionable new finding.**

### Correctness

The parser changes implement the agreed contract:

- Both helpers pass the selected core count as one quoted QEMU argument.
- Precedence is the last `--smp N`, then `QEMU_SMP`, then `1`.
- An empty environment value is rejected; a valid flag overrides an invalid environment default.
- Missing final values, invalid counts/budgets, unknown long flags and extra ELF arguments return 2 with usage.
- Invalid input is rejected before building or launching QEMU.
- Explicit ELF paths containing spaces survive argument forwarding.
- Default and release profile paths remain correct.

Mixed-error behavior is consistent with the implementation: argument-loop errors precede final value validation; SMP validation precedes timeout validation. For example, `--smp 0 --unknown` reports the unknown flag, while `--smp 0 --timeout bad <ELF>` reports the SMP error. Help exits immediately when encountered; using `--help` as a consumed SMP value produces the numeric-validation error. These behaviors introduce no contradiction with the agreed task contract.

Independent isolated probes also confirmed that default smoke builds userland before the kernel, passes `--release` to both builds when selected, and skips both builds for an explicit ELF. All build commands in those probes were stubs; the shared source tree and `hello.bin` were untouched.

### Style

The changes follow the existing Bash style and retain Bash 3.2 compatibility. `bash -n` passes for both helpers and the new regression harness.

ShellCheck returns 1 solely for the existing `smoke.sh` comma-token warning:

```text
tools/smoke.sh:43 — SC2054 — INT_FLAGS=(-d int,unimp)
```

Neither the new harness nor `run-qemu.sh` produces a finding. This is the explicitly accepted immediate T-031 carry-forward, not a new defect.

`actionlint -shellcheck=''` returns 0. Existing workflow `NIGHTLY_PIN` quoting findings remain assigned to T-031; disabling ShellCheck integration here establishes workflow/schema validity only.

Both commits use the expected subject format and contain `Refs: ADR-0040`. `git diff --check 3a7c264..d5c13a0` passes.

### Test coverage

Independent executions:

| Check | Result |
|---|---|
| `tools/test-qemu-tooling.sh` | PASS, 59 cases |
| Same harness with a restricted base-utility `PATH`, without real Cargo/QEMU | PASS, 59 cases |
| Additional disposable-copy CLI/profile/platform probes | PASS, 31 cases |
| `bash -n tools/run-qemu.sh tools/smoke.sh tools/test-qemu-tooling.sh` | Exit 0 |
| `shellcheck tools/run-qemu.sh tools/smoke.sh tools/test-qemu-tooling.sh` | Only existing SC2054; exit 1 |
| `actionlint -shellcheck=''` | Exit 0 |
| Changed Markdown relative links and anchors | 240 targets, including 24 anchors, resolve |

The additional 31 probes used temporary copies of the two helpers, empty ELF fixtures, logging Cargo/userland/QEMU stubs, and a restricted `PATH` selecting the Perl fallback. For **each** helper they exercised:

```text
<ELF>
QEMU_SMP=7 <ELF>
QEMU_SMP=0 --smp 2 <ELF>
--smp bad --smp 5 <ELF>
--smp 5 --smp bad <ELF>
--smp bad --help
--help --unknown
--smp --help <ELF>
--smp 0 --unknown
--smp
--smp 01 <ELF>
--smp +2 <ELF>
```

The remaining probes exercised:

```text
smoke.sh --smp 0 --timeout bad <ELF>
smoke.sh --timeout bad --timeout 2 <ELF>
smoke.sh --timeout --smp 2 <ELF>
smoke.sh
smoke.sh --release
run-qemu.sh
run-qemu.sh --release
```

Assertions covered exit status, diagnostics, absence of launch/build side effects on usage errors, selected `-smp` operand, profile paths and build ordering.

The committed harness deliberately covers argument handling rather than guest behavior. It does not assert every QEMU operand, actual watchdog duration, guest faults or real SMP operation. Its explicit-ELF cases also do not cover default build ordering/profile selection; the independent probes covered those paths without a real build. These are scope limits, not acceptance failures. Runtime strengthening and negative guest probes remain T-034 work.

I did not run real builds, write the shared userland image, or independently repeat Cargo’s runner-echo command because that command may build. The Cargo alias/static-runner source agrees with the documented override; the task’s recorded runner-echo evidence belongs to the implementer.

The parent additionally supplied successful hosted CI for `d5c13a0`, including the new 59-case step: [CI run 38176428435](https://github.com/HodeTech/Tyrne/actions/runs/38176428435). This is supplied hosted evidence, not an independently inspected run in this pass.

### Documentation

The revised QEMU guide gives a coherent path from checkout to debug boot:

- It requires the userland build before the BSP embeds `hello.bin`.
- It specifies matching profiles and rebuilding debug userland after release.
- It distinguishes the interactive helper from smoke’s build-and-run behavior.
- It explains completion followed by WFI and the QEMU exit controls.
- It describes debug greeting, task exit and completion, with the release greeting difference.
- It documents shell-helper precedence and Cargo’s explicit runner override.
- It keeps Cargo’s static runner at one core and clearly states that larger core counts are unsupported by today’s kernel.

The documented prerequisites match `rust-toolchain.toml`, `tools/build-userland.sh` and the Cargo aliases. The guide accurately limits the existing smoke gate to completion/fault checks and assigns stronger EL0 marker enforcement to T-034.

Task status, task index, current active task and guide refresh state remain **In Review**. The new text does not promote T-033 or T-037 to Done or imply that the required fresh rounds/final maintainer PR review have already completed.

All 240 actual relative Markdown links in the six changed Markdown files resolve, including 24 anchors. Inline and fenced code examples were excluded; a first naïve scan identified the literal `` `](...)` `` example as a link, which was corrected in the checker.

### Integration

The new test step runs in the existing fast lane and requires no real QEMU, Rust compilation or new package/framework. Its dependencies are Bash, ordinary filesystem/text utilities and either `timeout` or Perl. The native 59-case run exercised GNU `timeout`; the isolated 31-case run exercised Perl. A restricted base-utility `PATH` also ran the committed harness successfully without real Cargo/QEMU availability.

No action pins, permissions, cache keys, branch protection or external dependency declarations change. The new regression is blocking through the existing job rather than a separate required-status name.

The full existing smoke gate still has the preflight-recorded EL0-evidence limitation. This diff neither introduces that limitation nor claims to close it; T-034 owns the stronger runtime gate.

#### Code-review checklist

| Checklist item | Assessment |
|---|---|
| Correctness and boundary conditions | Pass; parser, precedence, errors, quoting and profiles checked |
| Capability semantics | Not affected |
| Fault containment | Usage errors stop before launch/build; guest mechanisms unchanged |
| Unsafe discipline | No `unsafe` or assembly change |
| Error handling | Pass; required usage failures return 2 without shell-internals errors |
| Tests | Pass; committed harness and independent probes, limits recorded |
| Documentation | Pass; guide, CI mapping, links and lifecycle checked |
| Architectural principles | Consistent; no SMP/runtime support claim |
| Dependencies | No new external dependency or framework |
| Naming/style | Pass, with explicitly deferred baseline SC2054 |
| Commit messages | Pass; both commits include ADR-0040 references |

#### Read coverage and execution boundaries

Read the canonical `AGENTS.md` and `CLAUDE.md`, complete `current.md`, all 39 existing numbered ADRs (`0001–0033`, `0035–0040`; `0034` has no file), all standards including their index, skills index, `perform-code-review`, `conduct-review`, the code-review master plan, T-033 and the Track B.2-1 preflight review. Oversized initial prerequisite reads were recovered through bounded section reads before reviewing the tests and implementation.

Read the new test harness **before** the implementation diff. Reviewed every changed hunk across all 11 files, both complete runner scripts, the complete test harness, Cargo configuration, the relevant CI lane, the QEMU/CI guide changes, build-userland script, toolchain configuration and lifecycle/index changes.

No repository edits, saved artifact, commit, branch operation, real build or external message was performed during the review. Final working tree remained clean. This temporary report was saved afterward at the parent’s explicit request; no repository file was changed.

### Verdict

**Approve for T-033 round 1 integration/CLI/docs review.** No new correction is required from this pass. Existing ShellCheck/workflow quoting findings remain limited to the immediately following T-031 step. Fresh round 2 and final maintainer PR review remain required; task statuses stay **In Review**.

## Round 2 code review

- **Change:** T-033 on `development`, exact range `3a7c264..eede01c`, ending at `eede01c2dd8b368c729720eab6f712bf7bcd1263`.
- **Reviewer/model:** `b21_step2_round2_code`, Codex AI agent (GPT-6 family; exact runtime model variant is not exposed to this reviewer), acting on behalf of @cemililik.
- **Date:** 2026-10-12.
- **Risk class:** Ordinary developer tooling, tests, CI integration and documentation.
- **Security-review cross-reference:** n/a for mandatory security review: this range changes no Rust, assembly, kernel/HAL, capabilities, syscalls, memory-management, scheduler or `unsafe` implementation. The paired independent integration review remains a separate review deliverable. This report provides neither kernel soundness certification nor an SMP-support claim.
- **Verdict:** **Approve. No introduced blocking or non-blocking findings.**

### Read coverage and procedure

Read the canonical agent guide (`CLAUDE.md`) in full, the complete current-roadmap pointer, all 39 existing numbered ADRs in numerical order (`0001`–`0040`, excluding reserved/unwritten `0034`), and all 15 files in `docs/standards/`. Recovered truncated prerequisite output with bounded reads. Inspected the skills inventory and followed the complete `perform-code-review` and `conduct-review` skills and code-review master plan.

Read T-033's intent and acceptance criteria, then the complete permanent regression harness before the implementation. Read the preceding Track B.2-1 preflight and full round-1 reports as context without treating their verdicts as this review's evidence. Reviewed every changed file and hunk in the 13-file range, including the new review record, all three commit messages, both complete runners, Cargo configuration and the affected fast CI lane. Supporting reads covered the complete userland builder, BSP build script, toolchain pin and source locations for the documented runtime markers and target gates.

The five review roles below were performed sequentially in this independent pass. No repository source/document edit, commit, branch operation or external message occurred. Disposable copies and stubs were created outside the repository. The only real build was the authorized default debug smoke path; no alternate-profile userland image or multi-core guest was built/run. The requested report was saved in `/tmp`; repository publication/index reconciliation belongs to the root reviewer.

### Correctness

**Clean.** Both runners implement the stated last-flag/environment/default precedence and validate the final value before build or QEMU side effects. The `${QEMU_SMP-1}` expansion distinguishes an unset environment default from an invalid empty value; an explicit valid flag can override either invalid environment text or an earlier invalid flag. Positive decimal validation does not evaluate untrusted text as shell arithmetic.

The new operand guards prevent an unset `$2` read. Missing operands, invalid counts/budgets, unknown long flags and extra ELF arguments produce usage errors with exit 2. The interactive runner's conversion to a consuming `while` loop advances every successful non-exit branch. Quoted array/argument forwarding preserves an explicit ELF containing spaces and passes the selected SMP value as exactly one operand. The default remains `-smp 1` in both helpers and Cargo's static runner.

Independent boundary probes covered leading zeroes, signs, surrounding whitespace, embedded newline/tab, comma-separated text, shell-metacharacter text, invalid final repetition, valid overrides, help precedence, missing values and a positive integer larger than a machine word. The large value is forwarded literally, not promised to be accepted by QEMU. Isolated default-profile checks verified userland-before-kernel build ordering, matching release flags and the selected debug/release ELF paths without changing the shared userland image.

### Style and portability

**Clean for introduced code.** On macOS, `/bin/bash` reports **3.2.57**. Syntax checking passed for both runners and the new test script. Independent runner probes used `/bin/bash` directly, and their QEMU stubs confirmed Bash 3.2 execution. A restricted `PATH` with a `bash` symlink to `/bin/bash` also forced the permanent harness and its child scripts onto Bash 3.2; all 59 cases passed.

`git diff --check 3a7c264..eede01c` passed. The permanent harness has executable mode `100755`. New prose and all three commit messages are English. Each commit follows the existing Conventional Commits format and references the existing Accepted `ADR-0040`.

Lint results are explicitly limited:

| Check | Result |
|---|---|
| `shellcheck tools/run-qemu.sh tools/smoke.sh tools/test-qemu-tooling.sh` | Exit 1; only `smoke.sh:43` SC2054 on `INT_FLAGS=(-d int,unimp)` |
| `actionlint -shellcheck=''` | Exit 0; workflow/schema validity |
| Full `actionlint` | Exit 1; 16 SC2086 reports on existing unquoted `NIGHTLY_PIN` expansions |

The SC2054 expression and workflow expansions are present verbatim in baseline `3a7c264`. These inherited findings are accurately recorded and assigned to the immediately following T-031 step; they are not introduced T-033 findings. Neither disabled ShellCheck integration nor a green hosted run is reported as a full lint-clean result.

### Test coverage

**Adequate for T-033's declared contract.** Independently executed:

| Check | Evidence/result |
|---|---|
| `/bin/bash -n tools/run-qemu.sh tools/smoke.sh tools/test-qemu-tooling.sh` | Exit 0 |
| `/bin/bash tools/test-qemu-tooling.sh` | PASS: 59 cases, native available timeout backend |
| Permanent suite with restricted base-utility `PATH` and forced Bash 3.2 | PASS: 59 cases; Perl fallback, no real Cargo/QEMU |
| Additional independently constructed isolated-copy probes | PASS: 47 boundary/default-profile cases under Bash 3.2, using Perl fallback |
| Baseline missing-timeout reproduction | `git show 3a7c264:tools/smoke.sh`, disposable copy, `--timeout`: exit 1 with `$2: unbound variable` |
| Current missing-timeout regression | Exit 2, flag-specific error plus usage; no build/launch events |
| `env -u QEMU_SMP tools/smoke.sh --int --timeout 5` | PASS, real default single-core debug boot |
| `CARGO_TARGET_AARCH64_UNKNOWN_NONE_RUNNER=echo cargo kernel-run` | Printed `target/aarch64-unknown-none/debug/tyrne-bsp-qemu-virt` |

The 47 independent probes asserted return codes, diagnostics, absent side effects on invalid input, selected SMP operand, absence of empty QEMU arguments, intact spaced ELF paths, Bash version, default profile paths and build order. They used a separate temporary fixture containing copies of the scripts, fake kernel ELFs, and logging userland/Cargo/QEMU stubs. Release-profile checks were entirely stubbed.

The real smoke used QEMU **11.1.1**, built the **117-byte debug hello image**, and emitted the userspace greeting, task exit and completion in order. Trace inspection showed exactly **two expected SVC exceptions on CPU 0**, no panic or CPU fault, and expected SIGTERM after the watchdog budget. Trace:

```text
/var/folders/d2/k7c1fj3976g7_qq7113f66p00000gn/T//tyrne-smoke.64031.log
```

The image SHA-256 remained:

```text
05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88
```

The permanent harness proves argument handling, not actual SMP operation, watchdog duration, fault handling or complete EL0 runtime enforcement. T-034 owns stronger debug/release marker enforcement and negative guest probes. This pass did not repeat unrelated broad Rust suites or Miri, and does not independently certify the prior round's mutation-test results.

### Documentation

**Clean.** The guide's commands and explanations agree with the builders, Cargo aliases and runtime markers: matching-profile userland precedes the kernel build; interactive helpers run existing ELFs; smoke builds when no explicit ELF is supplied; completion is followed by WFI; release console rejection does not prevent exit/completion. The shell and Cargo override workflows are explicit, and the Cargo echo override was independently exercised.

The core-count section documents last-flag/environment/default precedence, empty-value rejection and valid explicit overrides. It clearly labels N > 1 as unsupported preparation for Phase C, with no secondary-core park guard or bring-up claim. The completion/fault-only smoke gate is distinguished from T-034's forthcoming EL0 enforcement.

Independently checked all actual relative Markdown links in the changed Markdown documents, excluding fenced and inline code examples: **255 targets, including 24 anchors, zero failures**. Task, guide-refresh and roadmap lifecycle states remain `In Review`; round 2 and final maintainer review are honestly pending at the reviewed commit. The new round-1 artifact is a record of prior evidence, not a task promotion.

### Integration

**Clean for this range.** The executable dependency-free harness runs in the existing required fast lane, without new packages, a real guest or a Rust build. The new step leaves action pins, workflow permissions, cache keys and required-status names unchanged. Standard Bash/base utilities and timeout-or-Perl suffice; both native and restricted-PATH executions passed.

The scripts' existing default and explicit-ELF workflows remain compatible. The Cargo runner remains statically single-core; the documented override receives the ELF path correctly. No dependency, lockfile, toolchain, kernel ABI or unsafe-audit entry changes.

Hosted evidence was supplied by the root reviewer rather than fetched in this pass: [successful d5c13a0 CI run](https://github.com/HodeTech/Tyrne/actions/runs/38176428435), including root inspection of the new 59-case step. The range after `d5c13a0` adds review/lifecycle documentation only; no later source/CI changes are implied to have received separate hosted execution. Local verification above applies to `eede01c`. Final tracked working tree was clean.

### Full checklist

| Review item | Assessment |
|---|---|
| Correctness | Pass; precedence, validation, consumption, forwarding and defaults independently checked |
| Capability semantics | Unaffected; no guest authority boundary changed |
| Fault containment | Usage errors stop before build/launch; real single-core trace shows no fault; kernel mechanisms unchanged |
| Unsafe discipline | N/A; no `unsafe`, assembly or audit entry changes; no soundness certification |
| Error handling | Pass; malformed arguments return 2 with usage and no shell-internals error |
| Tests | Pass; 59 native + 59 forced-Bash cases, 47 independent probes, baseline bug reproduction and real debug smoke |
| Documentation | Pass; contracts, build/profile prerequisites, markers, overrides, lifecycle and all local links checked |
| Architectural principles | Consistent; P1–P7 unaffected; P8 Accepted ADR-0040; P9 English; P10 no diagram; P11 pins/dependencies unchanged; P12 tooling scope complete without SMP overclaim |
| Dependencies | None introduced |
| Naming/style/portability | Pass for introduced code; Bash 3.2 execution; inherited lint findings explicitly retained for T-031 |
| Commit messages | Pass; three conventional commits, valid ADR-0040 references |
| Workflow integration | Pass; executable stub suite in existing required fast lane |
| Security-review cross-reference | N/A for ordinary tooling range; paired independent integration pass separate |
| Review artifact/index | Full temp report saved as requested; root owns repository append/index updates |

### Verdict

**Approve T-033 at `eede01c` for this independent round-2 code review.** No introduced finding requires a source correction. Existing lint work remains with T-031. This verdict does not mark T-033 Done, approve the final maintainer merge, certify SMP support or certify kernel soundness.

## Round 2 integration review

- **Change:** T-033 on `development`, `3a7c264..eede01c` (head `eede01c2dd8b368c729720eab6f712bf7bcd1263`).
- **Reviewer:** `b21_step2_round2_integration`, independent Codex AI agent (session identifies the model as GPT-6; exact runner variant is not exposed to this agent).
- **Date:** 2026-10-12.
- **Risk class:** Ordinary host tooling, tests, CI and documentation. No Rust, boot assembly, capability, syscall, scheduler, MMU or `unsafe` implementation changes.
- **Security-review cross-reference:** N/A for this scoped delta; this pass is not a guest security review or a kernel soundness claim.
- **Verdict:** **Approve with one Low, non-blocking documentation finding (R2-INT-01).**

### Correctness

**Clean.** Both helpers implement the stated flag/environment/default precedence, including last-flag wins, a valid explicit value overriding an invalid or empty environment value, and rejection of an empty environment value when no flag overrides it. `${QEMU_SMP-1}` correctly distinguishes unset from empty. The final regex validates decimal text without shell arithmetic and rejects zero, signs, leading zeroes, whitespace and non-digits. Very large decimal text is passed unchanged; QEMU's acceptance of that count is not established by these checks.

The argument loops consume each argument or exit. Missing `--smp` operands, and the missing `smoke.sh --timeout` operand, return 2 with a flag-specific diagnostic and usage, without an unset `$2` access. Final invalid values stop before default builds or QEMU launch. Both helpers reject extra ELF arguments, and quoted explicit paths containing spaces remain one QEMU operand. Help exits immediately when encountered as a flag; when consumed as a numeric operand it is rejected. Repeated timeout operands use the last value, consistent with the existing parsing pattern.

Independent copied-runner probes confirm that the default debug and release ELF paths remain correct. Default smoke builds userland before the kernel, forwards `--release` to both builds when selected, and skips both builds for an explicit ELF. The interactive helper only runs an existing ELF. These probes used empty ELF fixtures and logging build/QEMU stubs; no shared `hello.bin` was written.

### Style

**Clean for introduced code.** The changes follow the surrounding Bash conventions, retain Bash 3.2 compatibility and add no unrelated refactoring. `/bin/bash` is 3.2.57 on this host. Syntax checks pass for both helpers and the regression script. The permanent 59-case suite also passes with a `/bin/bash` symlink first on `PATH`, forcing the harness and its env-shebang children onto Bash 3.2, when invoked from outside the checkout.

The harness is tracked executable (`100755`). New repository prose and all three commit messages are English. All three subjects follow Conventional Commits and include `Refs: ADR-0040`. `git diff --check 3a7c264..eede01c` passes.

Local ShellCheck exits 1 solely for the unchanged `smoke.sh` SC2054 expression `INT_FLAGS=(-d int,unimp)`. Full actionlint exits 1 with 16 existing SC2086 reports on workflow `NIGHTLY_PIN` expansions. The two-line workflow delta adds only the new test step; those expansions predate T-033. `actionlint -shellcheck=''` exits 0 and establishes workflow/schema validity only. These are the explicitly recorded, immediately following T-031 carry-forwards, not introduced findings and not a claim of clean full lint.

### Test coverage

**Adequate for T-033.** Read the complete new regression harness before the helper implementations. It checks observable exit status, diagnostic content, no QEMU launch on usage errors, the selected SMP operand, and preservation of an explicit ELF containing spaces. Its fake guest markers allow the existing smoke output gate to complete without requiring a real build or guest.

Independent executions in this round:

| Check | Result |
|---|---|
| `/bin/bash tools/test-qemu-tooling.sh` | PASS, 59 cases |
| Same harness with Bash 3.2 forced for all env-shebang children, invoked outside the checkout | PASS, 59 cases |
| Independently constructed copied-runner probes | PASS, 39 cases |
| Original `3a7c264` smoke copy with bare `--timeout` | Reproduced exit 1 and `unbound variable` |
| Current smoke with bare `--timeout` | Exit 2, `--timeout requires a value`, usage |
| `/bin/bash -n tools/run-qemu.sh tools/smoke.sh tools/test-qemu-tooling.sh` | Exit 0 |
| Diff whitespace check | Exit 0 |
| Workflow/schema actionlint, ShellCheck integration disabled | Exit 0 |
| Changed Markdown local destinations | 255 links, including 24 anchors, resolve |

For each helper, the independent probe set covered bare `--smp`, a flag consumed as an operand, zero, empty environment, valid flag overriding empty environment, invalid-then-valid and valid-then-invalid repeated flags, `01`, `+2`, newline/tab operands, a very large positive decimal string, help with invalid environment and following unknown flag, help consumed as a value, a space-containing ELF before the flag, and default debug/release paths. Smoke-specific probes covered repeated timeout validity, a flag consumed as timeout, bare timeout, and an actual Perl fallback selected through a restricted utility `PATH` with no `timeout`, real Cargo or real QEMU exposed. Logging assertions established build order, profile forwarding and the absence of build/launch side effects for usage failures.

Limits are explicit: the permanent suite uses explicit ELF fixtures and does not itself cover default build order, profiles, real watchdog duration, guest faults or EL0 execution. This round independently covered the build/profile contracts through copies and selected the real Perl path, but did not measure watchdog duration. Runtime marker strengthening and negative guest traces remain T-034. No real build, real QEMU, alternate-profile image or multi-core guest was run by this reviewer; the parent assigned real default smoke to the other independent reviewer. The source/default-path probes do not substitute for that runtime evidence.

### Documentation

**One Low, non-blocking finding.**

**R2-INT-01 — The refreshed guide inaccurately describes the post-completion loop as WFI.** `docs/guides/run-under-qemu.md:73` newly says “The completed kernel idles in WFI”. In the current default demo, `task_a` prints completion at `bsp-qemu-virt/src/main.rs:723`, prints timing, then immediately enters `loop { core::hint::spin_loop(); }` at lines 742–744 without yielding or exiting. The source explicitly documents at lines 533–537 that the WFI idle fallback is structurally unreachable in the demo path. The old guide described a spin loop; this refresh introduces the inaccurate WFI claim. Existing smoke/perf WFI comments predate this range and are not additional introduced findings. The practical instructions to exit QEMU and use a watchdog remain correct, so this is Low and non-blocking. **Requested correction:** say the kernel continues running/spins after completion and does not exit QEMU itself; change no guest behavior.

The guide otherwise supplies a coherent checkout-to-debug-boot sequence: matching-profile userland first, then kernel, then interactive boot. The prerequisites agree with the pinned toolchain, `tools/build-userland.sh`, the BSP's existence/change checks and Cargo aliases. QEMU's exit controls and the need for a bounded noninteractive run are correctly described; the WFI mechanism needs the narrow wording correction above. The current EL0 greeting, task-exit and completion markers replace the obsolete first-kernel-greeting workflow. Release greeting absence is explained, together with rebuilding debug userland before returning to debug.

The core-count section documents last-flag/environment/default precedence and invalid-value behavior. Both help headers explain the new option and precedence. The guide and helper headers explicitly say that counts above one are unsupported by today's kernel; the static Cargo runner remains `-smp 1`. The Cargo environment override is shown with both the shell helper and `echo`, and source inspection confirms that Cargo supplies the ELF path to that runner. I did not repeat `cargo kernel-run` because it may build; its recorded implementation/round-1 execution is separate supplied evidence.

The guide accurately describes the current smoke gate as completion/fault checks and links T-034 for stronger debug/release EL0 enforcement. It does not claim the new stub CI step boots a guest. T-033, its task index, current focus, guide refresh and review index remain `In Review`/round-2-pending at this snapshot. No agent review is represented as maintainer permission to merge or mark Done. The round-1 artifact and hosted result are historical evidence, and the second-round evidence is intentionally not preclaimed.

Checked actual relative Markdown destinations in all eight changed Markdown files, excluding inline and fenced code examples: **255 targets, including 24 anchors, resolve; zero failures**. External web destinations were not fetched in this local review.

### Integration

**Clean for this range.** The dependency-free, executable harness runs in the existing required fast job, with no `continue-on-error`, conditional skip, additional framework, new action or permissions change. It needs Bash, normal text/filesystem utilities and either timeout or Perl. The required job's status name remains unchanged, so the new check inherits that existing gate rather than requiring a new branch-protection name. The workflow uses checkout-root execution, matching the harness's own repository-root resolution.

Cargo's static single-core runner, build aliases, action pins, caches, permissions and guest implementation remain unchanged. `tools/perf-harness.sh` continues to receive the environment default through `run-qemu.sh`; no new perf flag is required by T-033. The documented release/default build sequencing agrees with the unchanged userland embedding pipeline. The explicit-ELF smoke contract remains build-free.

Hosted CI is **supplied evidence, not independently fetched in this pass**: the task history and parent report [CI run 38176428435 at `d5c13a0`](https://github.com/HodeTech/Tyrne/actions/runs/38176428435) successful, including PASS59 in the new fast-lane step. `eede01c` adds review/lifecycle documentation rather than an additional executable change. I did not independently rerun Rust fmt/clippy/host-test/Miri gates; the range changes no Rust and those results remain author/hosted evidence.

### Full code-review checklist

| Item | Assessment |
|---|---|
| Correctness | Pass; parser, precedence, validation, forwarding, defaults and build order checked |
| Capability semantics | Unaffected; no guest authority boundary change |
| Fault containment | Usage errors precede build/launch; guest fault mechanisms unchanged |
| `unsafe` discipline | N/A; no `unsafe` or audit-log change |
| Error handling | Pass; required usage errors return 2 without shell internals |
| Tests | Pass for scoped tooling; permanent suite, independent probes and baseline regression reproduced; runtime limits stated |
| Documentation | Minor; R2-INT-01 corrects the new WFI wording; help, CI mapping, local links/anchors and lifecycle otherwise pass |
| Architectural principles | P1–P7 unaffected; P8 follows Accepted ADR-0040; P9 English; P10 no new diagram; P11 pins/dependencies unchanged; P12 completes the scoped tooling contract without claiming SMP support |
| Dependencies | None added; no add-dependency procedure triggered |
| Naming/style/portability | Pass for introduced code; Bash 3.2; baseline lint carry-forwards explicitly identified |
| Commit messages | Pass; all three conventional subjects and ADR-0040 references |
| CI/caller integration | Pass; existing required fast-lane job; static Cargo runner unchanged |
| Security review | Separate security artifact not required for this ordinary scoped delta |
| Artifact/index publication | Parent owns repository append/index/history updates; this reviewer was explicitly restricted to a temporary report |

### Read coverage and boundaries

Read AGENTS/CLAUDE and complete current focus; all 39 existing numbered ADRs in numerical order (`0001–0033`, `0035–0040`; `0034` is reserved/unwritten), all 15 standards including their index, the skills index, both applicable review skills, full code-review master plan, preflight review and complete T-033 round-1 artifact. Oversized prerequisite/diff outputs were recovered with bounded reads rather than ignored.

Read T-033 intent and tests before implementations; reviewed both complete helpers, the full new harness, all changed hunks, changed Markdown content/lifecycle context, Cargo configuration, full workflow context, userland build script, pinned toolchain, BSP build checks and relevant runtime marker locations. Executed all five master-plan roles in this independent pass.

No repository file, commit, branch, shared binary or external application was mutated. Probe directories were disposable and removed. The final repository status was clean. The only retained write is this temporary report, explicitly requested by the parent; repository artifact/index/history publication remains with the parent.

### Verdict

**Approve T-033 at `eede01c` with one Low, non-blocking documentation finding, R2-INT-01, for the round-2 integration, UX, documentation and CI review; all five axes are covered.** Existing SC2054/workflow quoting warnings retain their immediate T-031 ownership. This verdict establishes neither SMP runtime support nor kernel soundness, and it does not promote T-033 to Done or replace final maintainer PR review.

## Finding reconciliation

| ID | Severity | Source verification | Resolution |
|----|----------|---------------------|------------|
| R2-INT-01 | Low | `bsp-qemu-virt/src/main.rs` task A prints completion, records elapsed time, then enters `loop { core::hint::spin_loop(); }` without yielding to `idle_entry`. | Corrected the guide, smoke comments and live performance-harness header/generated methodology to describe continued spinning. Timeout/exit behavior and all executable Rust/Bash logic are unchanged. Historical review text is retained with the superseding note above. |

Verification of this wording-only correction: source inspection, Bash syntax and the 59-case argument regression suite pass; the full ShellCheck baseline remains the same five findings owned by the immediately following T-031 step. No additional real guest run is claimed for a prose-only correction.
