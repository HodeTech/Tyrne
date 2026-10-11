# Code review 2026-10-12 — T-033 QEMU tooling

- **Change:** T-033 on `development`, `3a7c264..d5c13a0`.
- **Reviewer:** `b21_step2_round1_code` (Codex AI agent, `gpt-6.1-sol`, high reasoning), acting on behalf of @cemililik.
- **Risk class:** Ordinary.
- **Security-review cross-reference:** n/a — developer tooling, argument tests, workflow integration and documentation only; no kernel, HAL, syscall, scheduler, boot assembly or `unsafe` implementation changes.

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
