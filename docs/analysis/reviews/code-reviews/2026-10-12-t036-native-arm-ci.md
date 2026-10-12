# Code review 2026-10-12 — T-036 native ARM CI

- **Change:** approved Track B.2-1 step 7, `9c5191c..bf20ec9`.
- **Round 1 reviewers:** fresh `b21_step7_round1_code` and `b21_step7_round1_integration`, each requested `gpt-6.1-sol` / high, empty inherited context. Configuration provenance, not runtime identity attestation.
- **Risk:** Ordinary CI/tooling-only delta; no shipped Rust or unsafe change.

> **Reconciliation:** Round 1 both Approve, one duplicate Low premature merge-enforcement wording finding. Coordinator verified and corrected it; actual hosted Linux ARM job passed in 101 s and all seven development jobs passed. Both fresh Round 2 reviewers Approve with zero new findings and verify the Low correction. Coordinator subsequently registered the ARM check with full-policy read-back; final PR and post-merge evidence remain pending. T-036 stays In Review.

> **Late integration reconciliation (2026-10-12):** Subsequent run38186028266 at `69ac515` exposed a flaky E0152-only assertion: Cargo reported the same private cfg regression as unsupported no_std unwinding first. The earlier source-bound approvals and green runs below are retained unchanged. Step8 corrects the assertion to require compiler exit101 plus either exact observed diagnostic and adds permanent offline controls. The [T-035 review](2026-10-12-t035-ci-hygiene-tail.md) carries the independent cross-step review and corrected hosted evidence; final PR/main remain separate.

## Round 1 — code

# Code review 2026-10-12 — T-036 native ARM64 CI, round 1

- **Change:** `development`, baseline `9c5191cfb8ced7e99e1afe459bb02852fde1a14b` → immutable implementation `bf20ec9739db635183b1b930f4da9f2c2b6813bf` (`ci: require native ARM64 workspace checks and Miri`). Nine changed files; 133 insertions and 39 deletions. This report reviews that source SHA, not subsequent review fixes or evidence updates.
- **Reviewer:** Codex delegated code reviewer, acting on behalf of @cemililik; all five master-plan roles performed independently and sequentially in this pass. This is a review recommendation, not a claim of maintainer approval.
- **Risk class:** Ordinary. The diff adds CI/probe/documentation behavior; it changes no shipped Rust, assembly, boot, capability, syscall, scheduler, memory-management or production `unsafe` implementation. CI trust boundaries are nevertheless examined below.
- **Security-review cross-reference:** n/a for this risk class. The distinct integration reviewer is complementary evidence, not a substituted security approval.

Read before completing the review: AGENTS.md, full CLAUDE.md, current.md, every existing numbered ADR in numerical order (0001–0040; 0034 is intentionally reserved), all fifteen files under docs/standards, both applicable skills (`perform-code-review` and `conduct-review`), the complete code-review master plan, T-036's story, CI guide, the entire changed workflow/probe and associated host-target configuration. Bounded follow-up reads recovered truncated output. ADR-0040 is Accepted and authorizes the eight-step Track B.2-1 sequence; step 7 is within that authorization. No repository edit, commit, branch operation or live settings write was performed by this reviewer. The requested temporary report is supplied to the coordinating agent for canonical filing/indexing.

## Correctness

- **Clean; no correctness blocker.** `.github/workflows/ci.yml:275–320` runs on `ubuntu-24.04-arm`, has a 15-minute timeout and explicit Bash, installs pinned nightly clippy and Miri, selects the same nightly by override, and verifies both actual `uname -m == aarch64` and `rustc` host `aarch64-unknown-linux-gnu`. No target override turns these into cross-compiles. Native compilation, linking/execution, and interpretation are separate mandatory steps; neither the probe nor Miri replaces positive native tests.
- **Exact four commands verified:**

  ```sh
  cargo +"$NIGHTLY_PIN" check --workspace --exclude tyrne-bsp-qemu-virt
  cargo +"$NIGHTLY_PIN" clippy --workspace --exclude tyrne-bsp-qemu-virt --all-targets -- -D warnings
  cargo +"$NIGHTLY_PIN" test --workspace --exclude tyrne-bsp-qemu-virt
  cargo +"$NIGHTLY_PIN" miri test --workspace --exclude tyrne-bsp-qemu-virt
  ```

  The pinned toolchain is `nightly-2026-01-15`; `cargo +"$NIGHTLY_PIN" miri setup` precedes interpretation. Only the bare-metal BSP is excluded. Both host-gated userland crates remain members of these workspace commands, unlike the existing default-members aliases.
- **Native versus guest boundary verified.** `.cargo/config.toml` has target-scoped bare-metal configuration, not a default bare-metal target. The six hello cfg predicates require both aarch64 and `target_os = "none"`; hello's build script applies `hello.ld` only to that bare-metal combination. Native ARM therefore builds the host stub and host-side crate contracts. This catches the original architecture-only cfg mistake, while proving no EL0 SVC, MMIO, bare-metal linker, device or multi-core behavior. Existing cross-build and QEMU jobs remain responsible for their own boundaries.
- **Probe semantics verified.** `tools/test-ci-gates.sh:21–80` refuses a non-aarch64 Rust host before creating a temporary copy; exactly six expected hello predicates must be present. It changes those predicates only in the copied main.rs, leaving the copied build script/syscall shim untouched. It invokes the exact native workspace clippy command with `--all-targets -- -D warnings`, requiring nonzero status and the specific ``error[E0152]: found duplicate lang item `panic_impl` `` diagnostic. Unexpected success and unrelated failure both fail the harness. A successful probe asserts compiler rejection; it is not a production compiler failure or a reproduced production Miri failure.
- **Isolation verified.** `mktemp -d`, quoted paths, NUL-delimited tracked paths, preserved script modes, private `CARGO_TARGET_DIR`, and EXIT cleanup confine modifications/build outputs to the temporary tree. The implementation copies the current tracked worktree, deliberately not an arbitrary historical commit. Review controls used an immutable archive with private git enumeration, so the reviewed source remained exact. No shared userland image was built or replaced. Comparing all 393 regular archived files against `git archive bf20ec9` after controls and the real probe found zero changed bytes; the real-probe temporary parent was empty afterward.

## Style

- **Clean.** The new job follows existing SHA-pinned checkout/cache and explicit toolchain conventions. Names describe the native host scope; shell quoting, argument validation, failure propagation and narrowly justified ShellCheck suppression are appropriate. No new Rust public API, `unsafe`, error enum or audit-log entry is introduced.
- Independently ran `actionlint .github/workflows/ci.yml`, `shellcheck tools/*.sh`, and `bash -n tools/test-ci-gates.sh` on the archived reviewed SHA: all passed. `git diff --check 9c5191c bf20ec9` passed. No style preference is promoted into a finding.
- The implementation commit is English, scoped to one logical CI change, and carries the valid `Refs: ADR-0040` trailer.

## Test coverage

**Present and meaningful:**

| Evidence | Result | What it establishes |
|---|---|---|
| Hosted real Linux ARM job [114605118899](https://github.com/HodeTech/Tyrne/actions/runs/38184932784/job/114605118899), source bf20ec9 | All four positive commands and regression probe passed | Actual native Linux ARM execution, not emulation or a stub |
| Hosted native tests | 46 HAL + 259 kernel + 58 test-HAL + 3 doctests = 366 passed; two HAL doctests ignored | Host suite ran; userland host harnesses also built and ran with zero tests |
| Hosted Miri setup and tests | aarch64-unknown-linux-gnu sysroot prepared; same 366 passed, two ignored | Pinned native-target Miri execution; no UB diagnostic in exercised paths |
| Hosted negative probe | Actual clippy exited 101 with E0152 duplicate panic_impl; harness returned success | Deliberate copied cfg regression is rejected by the intended command |
| Independent real Apple Silicon probe | Real pinned rustc/Cargo; actual rejection 101/E0152; harness success | Reviewer independently reproduced compiler rejection using private source and Cargo home/target |
| Six independent controlled cases | All expected statuses, no source mutation, cleanup passed | Harness sensitivity, architecture guard, anchor guard and quoting/isolation |
| Independent syntax/lint checks | actionlint, ShellCheck, Bash syntax and diff whitespace passed | Workflow/shell validity at immutable source |

The hosted log at `/tmp/tyrne-b21-step7/hosted-arm.log` was inspected directly: checkout fetch/log identifies full SHA `bf20ec9739db635183b1b930f4da9f2c2b6813bf` (lines 93–106), installed rustc is `1.94.0-nightly (86a49fd71 2026-01-14)`, the real machine and Rust host are verified (lines 140–148), and positive/native/Miri results and expected rejection are present. Parent-fetched API timing records the full ARM job as 101 seconds, with Miri setup 17 seconds and interpretation 54 seconds; API times have second granularity. The full seven-job run subsequently completed successfully according to the coordinating agent; this reviewer independently inspected the ARM job log, not all other job logs.

Independent control evidence is `/tmp/tyrne-t036-r1-code/independent-controls.json`, with fixtures/script under the same private directory. Cases were: expected duplicate-panic rejection on reported Darwin ARM; expected rejection on reported Linux ARM; unrelated compiler failure; unexpectedly green compiler; x86 host refusal; and a drifted sixth-predicate anchor. All six controlled cases use **stub rustc/Cargo** (the refusal/anchor guards prevent Cargo from being called), including the nominal Linux case: they prove harness behavior only. They are not presented as real ARM compiler evidence. Commands/PWD/private target were recorded and paths contained spaces. The separate real Apple Silicon probe used actual tools with only git tracked-file enumeration supplied for the archive. The coordinating agent's ten-case fixture set additionally covers CLI help/argument errors; it is supplemental, not the basis of the real compilation claim.

**Missing:** no additional in-scope test is required for this CI-only change. Final-PR ARM green and first post-merge main-run evidence necessarily remain pending. Two ignored HAL doctests and existing Miri optimization/provenance warnings predate this diff; successful Miri proves the exercised host tests, not universal memory safety or hardware behavior. T-038's known x2-clobber work is separate scope and is not reopened here.

## Documentation

**One Low, non-blocking finding:**

- **CODE-T036-R1-01 — Qualify pending live ARM required-check registration.** At immutable source `bf20ec9`, `docs/standards/testing.md:111` adds the ARM gate beneath line 102's heading **“Enforced in CI today (block merge)”**, without qualification. At that same SHA, the workflow header, CI guide, infrastructure standard and T-036 acceptance criteria explicitly say live registration follows hosted green and both fresh review rounds. A workflow job exists and fails correctly, but that does not itself make its display name a branch-protection requirement. A reader relying on the testing standard could infer that this gate already prevents merging. Add the same workflow-enabled/live-registration-pending qualification to this bullet, or place it in a clearly pending-registration subsection. Validation: inspect the resulting prose against the five currently registered checks, and retain pending status until live read-back exists. The coordinating agent independently confirmed this wording issue and is preparing the fix; that subsequent fix is outside this immutable review.

Other documentation is appropriate: job table, exact native commands, Miri setup, host versus guest meaning, rejected-regression meaning, runner/timeout, all-cache architecture isolation, exact display name and pending live registration are recorded. T-036, index and current.md correctly retain `In Review`; they do not claim the final PR or post-merge run exists. Hosted timing was honestly pending when the implementation was committed and can now be appended using the actual source-bound run. ADR-0040 contains the governing decisions before the standards update; no unapproved policy change is being smuggled through a guide.

The pre-existing coverage neutral/post-T-011 wording correction is expressly reserved for the immediately next T-035 step and is not a new T-036 finding. Existing unrelated doctrine cleanup is likewise not expanded into this change.

## Integration

- **Clean; no integration blocker.** Existing x86 host/stable/Miri/coverage, cross-kernel and QEMU smoke jobs retain their behavior; changes to their caches add architecture identity. Every exact key **and** every restore prefix includes both `runner.os` and `runner.arch`; no broad fallback can restore a different architecture:

  | Job/cache namespace | Exact key line | Restore prefix line | Remaining identity |
  |---|---:|---:|---|
  | lint host / cargo | 99 | 101 | nightly pin; lock hash in exact key |
  | kernel / cargo-aarch64 | 156 | 158 | nightly pin; lock hash |
  | guest / qemu-smoke | 234 | 236 | nightly pin; lock hash |
  | native ARM / arm64-host | 304 | 306 | nightly pin; lock hash |
  | host stable / cargo-stable | 354 | 356 | stable namespace; lock hash |
  | Miri / miri | 393 | 395 | nightly pin; lock hash |
  | coverage / llvmcov | 444 | 446 | nightly pin; lock hash |

  Restore prefixes deliberately permit an older lockfile cache within the same OS/architecture/job/toolchain namespace. Stable remains a rolling toolchain namespace as before; this does not undermine architecture isolation. Native ARM targets are also separated by the arm64-host job namespace.
- Runner availability was checked against the primary [GitHub hosted-runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners): `ubuntu-24.04-arm` is a standard public-repository ARM64 runner. The successful source-bound hosted job independently resolves the practical runner/Miri support question for this repository and pin. No paid or self-hosted runner assumption is introduced.
- **CI security boundaries:** global `contents: read` is unchanged; checkout uses a full action SHA and `persist-credentials: false`; cache action is full-SHA pinned. The new job adds no secrets, writable token scopes, `pull_request_target`, untrusted interpolation into shell source, publishing step, privileged service or self-hosted runner. Pull requests execute repository code only within the existing disposable hosted-runner model. Cache contents are build inputs/performance state, not a claimed trust or authenticity boundary. Job failure is not advisory and no `continue-on-error` weakens the ARM commands/probe. Explicit Bash preserves host verification pipeline failures. Live branch protection is deliberately a later, separately read-back action.
- No new dependency, lockfile, binary blob, public API, production behavior or unsafe audit obligation is introduced. T-037's accepted target-gating fix is a real prerequisite already present in the baseline; this change adds independent detection rather than altering it.

**Architectural-principles pass:**

| Principle | Review result |
|---|---|
| P1 no ambient authority | No runtime authority change; CI token remains read-only. |
| P2 smallest TCB | No shipped kernel/TCB growth; tooling stays in CI. |
| P3 userspace drivers/services | No subsystem relocation or device code added. |
| P4 boundary checks | No runtime trust entry changes; CI host/probe boundary checks fail closed. |
| P5 Rust-only kernel | No kernel-language or assembly change; shell/Python are build tooling. |
| P6 HAL separation | BSP excluded from host commands; hardware execution remains separate. |
| P7 no proprietary blobs | No blob or shipped binary addition; existing open toolchain/runner use only. |
| P8 ADRs | Accepted ADR-0040 governs runner, commands, trigger and mandatory Miri. |
| P9 repository English | Changed source/docs/commit are English. |
| P10 Mermaid diagrams | No diagram added. |
| P11 reproducibility | Exact nightly/action pins retained, lock identity retained, all cache fallback boundaries isolate architecture. |
| P12 complete scope | CI implementation complete to step-7 scope; review/live/final-PR/post-merge obligations remain explicit rather than prematurely Done. |

## Verdict

**Approve**

All five role passes are complete. There are **zero Critical, High or Medium findings; one Low documentation finding**, CODE-T036-R1-01, is non-blocking under the master-plan approval semantics. No functional blocker was found. This recommendation applies only to immutable implementation `bf20ec9739db635183b1b930f4da9f2c2b6813bf` and does not approve unreviewed follow-up changes.

The requested fresh second round must review the actual post-fix SHA independently. Live ARM required-check registration/read-back, final maintainer PR review/green and first merged-main run remain distinct pending obligations. Keep the task `In Review` until the authorized process reaches those stages; this code review is not a Done-promotion or live-settings authorization artifact.

## Round 1 — independent integration

# Code review 2026-10-12 — T-036 Step 7 Round 1, independent CI integration/test/documentation

- **Change:** immutable `9c5191cfb8ced7e99e1afe459bb02852fde1a14b..bf20ec9739db635183b1b930f4da9f2c2b6813bf` on `development`; subject `ci: require native ARM64 workspace checks and Miri`.
- **Reviewer:** Codex independent reviewer `/root/b21_step7_round1_integration`; all five master-plan roles executed sequentially. This is a reviewer handoff, not a maintainer approval or a Done promotion.
- **Risk class:** Ordinary. This diff changes CI, a private rejection-test harness and documentation; no shipped Rust, assembly, capability, IPC, syscall, memory, scheduler, boot mechanism or unsafe boundary changes.
- **Security-review cross-reference:** n/a for this diff; CI supply-chain, permissions, credential handling and shell failure propagation were reviewed below.
- **Scope:** nine changed files, 133 insertions / 39 deletions. Source decisions and findings are anchored to `bf20ec9`, including while the parent prepares later documentation/evidence changes. No repository edits, branches, commits or live setting writes were performed by this reviewer.
- **Process inputs:** AGENTS.md, CLAUDE.md, current roadmap focus, numbered ADR corpus through Accepted ADR-0040, repository standards, `perform-code-review` and `conduct-review` skills, and full code-review master plan. Parent's explicit temporary-artifact-only scope defers canonical artifact/index/commit integration to the parent.

## Correctness

No blocking finding.

- The new `arm64-host-check` job in `.github/workflows/ci.yml:274-319` uses explicit `ubuntu-24.04-arm`, pinned `NIGHTLY_PIN`, a 15-minute timeout and explicit Bash. Before checks it verifies both `uname -m = aarch64` and Rust `host: aarch64-unknown-linux-gnu`. This is a native host job, not a bare-metal cross-compilation substitute. GitHub's current official runner table identifies this image as Linux ARM64 with four CPUs; it is a standard public-repository runner. [GitHub-hosted runners reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
- All four required commands use `--workspace --exclude tyrne-bsp-qemu-virt` and no `--target`. Check, clippy with `--all-targets -- -D warnings`, native test, and Miri therefore include both `tyrne-user` and `tyrne-userland-hello`. The default-members-only aliases would omit those crates; the implementation correctly avoids them for this gate. The config has no global build target redirecting these commands to bare metal.
- Miri is installed for the pinned nightly and `cargo miri setup` precedes interpretation. Native linking/testing and Miri remain distinct checks. No global `RUSTFLAGS` or weakened diagnostics are introduced.
- `tools/test-ci-gates.sh --arm-host` checks the actual Rust host is `aarch64-*` before copying. It copies tracked source into a private `mktemp` tree, exports a private Cargo target directory, changes exactly six compound hello cfg predicates to arch-only, and leaves the wrapper/build scripts alone. A count different from six fails before cargo runs. Production sources and the existing shared target/image are not mutated.
- `run_negative` captures a nonzero command status explicitly, rejects an unexpectedly successful command, and also requires the exact fixed duplicate-`panic_impl` E0152 diagnostic. An unrelated compiler failure is refused. The intended clippy failure exits 101 while the successful rejection harness exits 0; those are different outcomes. The harness does not claim that this compile failure is a new Miri UB reproduction.
- Quoted paths, NUL-delimited tracked-file copying, `set -euo pipefail`, and EXIT cleanup preserve operation under system Bash 3.2 and paths containing spaces. Source-anchor drift and non-ARM hosts fail closed. A shell failure is not converted to a passing ARM gate.

## Style

Clean; no style finding.

- Actionlint and ShellCheck both pass independently on the immutable archive. Existing pinned actions and shell conventions are reused. The narrowly scoped ShellCheck suppression protects a literal Rust diagnostic containing backticks.
- English repository text, a `ci:` commit subject and `Refs: ADR-0040` comply with the relevant conventions. No new Rust public API, error variant or unsafe region requires rustdoc, `# Errors`, `# Safety` or an audit entry.
- `git diff --check 9c5191c bf20ec9` passed. No cosmetic redesign is requested.

## Test coverage

The implemented gate has adequate positive and adversarial evidence. No missing blocking test was identified.

**Independent real local execution.** Exact `bf20ec9` was exported with `git archive` into a private path containing a space; Cargo outputs were redirected to a private target directory. Host was Apple Silicon (`aarch64-apple-darwin`), pinned Rust `1.94.0-nightly (86a49fd71 2026-01-14)`. These commands all returned 0:

```sh
actionlint .github/workflows/ci.yml
shellcheck tools/test-ci-gates.sh
cargo +nightly-2026-01-15 check --workspace --exclude tyrne-bsp-qemu-virt
cargo +nightly-2026-01-15 clippy --workspace --exclude tyrne-bsp-qemu-virt --all-targets -- -D warnings
cargo +nightly-2026-01-15 test --workspace --exclude tyrne-bsp-qemu-virt
cargo +nightly-2026-01-15 miri setup
cargo +nightly-2026-01-15 miri test --workspace --exclude tyrne-bsp-qemu-virt
bash tools/test-ci-gates.sh --arm-host
```

Native tests and Miri each report 366 passing tests (46 HAL + 259 kernel + 58 test-hal + 3 doctests), two ignored HAL doctests, and zero failures. Both userland crates appear in the runs even though their host test count is zero. Miri reports no UB; existing optimization/provenance warnings are not a new defect or a proof of complete soundness. Local setup reused the already-built Miri sysroot, so its short setup time is not evidence of a cold hosted setup. The actual local arch-only mutation produced E0152 and clippy exit 101; the harness returned 0.

Local raw evidence: `/var/folders/d2/k7c1fj3976g7_qq7113f66p00000gn/T/tyrne-t036-integration-4xqks6sx/`, `command-0.log` through `command-7.log` and `results.json`. These are reviewer-local logs, not committed CI artifacts.

**Independent mocked failure-path controls.** Using private copies of the same archive and stubbed `rustc`/`cargo`, ten cases passed under `/bin/bash`: intended rejection for Apple and Linux ARM hosts; unexpected green compiler refusal; unrelated compiler-error refusal; x86 refusal without cargo; five-anchor drift refusal without cargo; missing, surplus and unknown argument rejection; help success. The cargo stub additionally checked exact clippy argv, a private Cargo target, and complete cfg mutation. Cleanup and original private source preservation were checked. These validate harness branches and isolation; they are explicitly mocked, not native compiler or Linux execution evidence. Results are in `independent-mocked-controls.json` alongside the logs. Parent's ten-case fixture results at `/tmp/tyrne-b21-step7/fixture-results.json` provide corroborating evidence.

**Hosted evidence received during this review.** I independently inspected the parent's ANSI-stripped `/tmp/tyrne-b21-step7/hosted-arm.log` for job `114605118899` in run `38184932784`. It records Linux `aarch64` / Rust `aarch64-unknown-linux-gnu`, all four workspace gates, both userland members, 366 passing tests plus two ignored doctests for native and Miri, and the expected E0152 clippy exit 101 / harness 0. Miri really builds the Linux ARM sysroot (about 17 seconds in the log). Parent-reported GitHub API timestamps give a 101-second complete job, native check/clippy/test approximately 1/1/4 seconds, rejection probe 7 seconds, setup 17 seconds and interpretation 54 seconds; API seconds are coarse, not benchmarks. [Hosted ARM job](https://github.com/HodeTech/Tyrne/actions/runs/38184932784/job/114605118899).

The parent subsequently reported all seven jobs in the complete run green. I did not independently fetch the complete run API or rerun QEMU: hosted ARM conclusions above are based on the inspected job log; the complete-run result is parent-supplied evidence. The QEMU machinery is unchanged except architecture cache segregation and prior T-034 pipefail correction is retained.

## Documentation

**LOW — T036-R1-INTEGRATION-01: premature merge-blocking claim.** At immutable `bf20ec9`, `docs/standards/testing.md:111` places the new ARM gate under `Enforced in CI today (block merge)` at line 102. The task, guide, current focus and infrastructure standard correctly distinguish implemented CI from pending live required-check registration. A green development run alone does not make the check a live branch-protection requirement. A contributor can therefore read a stronger enforcement guarantee than currently exists.

**Requested correction:** qualify this ARM bullet explicitly as implemented with live required-check registration pending, and remove that qualifier only once the live policy has been applied and verified. This is a minor documentation finding; the workflow's actual test behavior is correct. Parent independently confirmed the finding and is preparing the correction. This report does not treat an unreviewed later working-tree edit as part of `bf20ec9`.

Other documentation passes:

- Task, task index and current focus consistently place T-036 `In Review` as approved step 7 on `development`. T-037 and the preceding selected tasks may have completed both rounds while remaining In Review under Accepted ADR-0040's stacked-sequence exception. Nothing authorizes agent Done promotion.
- Guide and task describe the runner, native-versus-Miri distinction, exact commands, only-BSP exclusion, architecture cache isolation, private negative experiment, host requirement and historical E0152 failure accurately.
- At the commit boundary the source accurately records hosted timing/green evidence as pending. Hosted success arrived during review and can now be added as separately dated evidence. Required-check registration, both completed fresh review rounds, final maintainer PR review and first-main/post-merge evidence remain separate gates; no local or development result substitutes for them.
- Release requirements are prospective policy, not a claim that registration has already happened. No architecture document or new ADR is needed beyond the Accepted ADR-0040 implementation policy.
- Unchanged coverage-neutral/post-T-011 prose belongs to explicitly next T-035. Known T-038 syscall clobber work is outside this diff and is not cleared by the host/Miri results.

## Integration

No integration blocker.

**CI/security review.** Workflow permissions remain `contents: read`; all seven checkouts use the existing SHA-pinned action and `persist-credentials: false`. No administrative token, secret-bearing permission, `pull_request_target`, live policy mutation or new third-party action is added. The job uses GitHub's explicit Bash shell, whose normal runner invocation enables errexit and pipefail, and the negative harness handles its sole intended failure explicitly. No `continue-on-error` weakens ARM results. The 15-minute limit bounds an accidental hang; observed hosted runtime fits with substantial headroom.

**Every cache key and fallback:** inspected all seven `actions/cache` uses, not only the new job. The cargo host, cargo-aarch64/kernel, qemu-smoke, arm64-host, stable, miri and llvmcov namespaces each include `${{ runner.os }}-${{ runner.arch }}` in both the exact key and every restore prefix. There are 14 key/prefix lines with architecture segregation. Linux x86 and Linux ARM therefore cannot restore one another's target cache through a broad fallback. Dedicated job namespaces remain distinct. Toolchain pin/lock portions remain in the existing key structure. The negative probe never uses the shared target cache.

**Dependencies and downstream behavior:** no Cargo manifest/lockfile or shipped Rust changes; no new dependency needing add-dependency procedure. Host and cross-target jobs retain their responsibilities. Both userland members stay in the ARM workspace checks while only the inherently bare-metal BSP is excluded. Existing smoke, release, stable, coverage and x86 Miri jobs remain present. No symbol or ABI changes exist.

**Architectural principles P1–P12:**

| Principle | Disposition and evidence |
|---|---|
| P1 No ambient authority | Pass: no shipped privilege path changes; CI token remains read-only. |
| P2 Smallest defensible TCB | Pass: no kernel/TCB growth; bounded host-side gate only. |
| P3 Userspace placement/fault containment | Unchanged: no driver/service placement or fault boundary change. |
| P4 Capability checks | Unchanged: no syscall, IPC or cross-task entry point changes. |
| P5 Rust-only kernel | Pass: shipped Rust/assembly unchanged; Bash/Python are host test orchestration. |
| P6 HAL separation | Unchanged: no CPU detail enters kernel code; host architecture check stays in CI. |
| P7 No proprietary blobs | Pass: none added, linked, embedded or required. |
| P8 ADR governance | Pass: required ARM/Miri policy, sequencing and registration timing follow Accepted ADR-0040; commit references it. |
| P9 English repository | Pass: changed artifacts and commit are English. |
| P10 Mermaid diagrams | N/a: no diagrams added or changed. |
| P11 Reproducibility | Pass within scope: pinned nightly/actions retained; architecture-segregated exact and fallback caches; no lock/dependency change. |
| P12 Complete declared scope | Pass for implementation review: all required commands and rejection gate exist; external registration/review/merge evidence remains explicitly pending, not silently certified. |

**Standard checklist:** correctness/pass; capability semantics/unchanged; fault containment/unchanged; unsafe annotations/audit/no unsafe change; error handling/pass through fail-closed controls; tests/pass with real and mocked evidence clearly separated; documentation/one Low above; architecture/P1–P12 covered; dependencies/no additions; style/pass; commit format/pass. Canonical review artifact/index insertion is the parent's integration step under the explicit no-repository-writes review assignment.

## Verdict

**Approve** — one Low, non-blocking documentation correction (`T036-R1-INTEGRATION-01`); zero blocking runtime, harness, cache or CI-security findings.

This verdict concerns only the immutable Step 7 implementation. Correct the enforcement wording before the next review round, preserve the hosted evidence boundary, and complete the separately required second fresh round/live registration/final maintainer review/post-merge evidence. It does not promote T-036 to Done, approve a live-policy write, certify a first main run, or resolve T-038.

## Coordinator verification and correction

CODE-T036-R1-01 and T036-R1-INTEGRATION-01 describe the same Low finding. The ARM bullet under the testing standard's enforced-gates heading now explicitly distinguishes workflow enablement from pending live required-check registration. The task, all current pointers and guide separately record source-bound hosted success and measured timing. No runtime source changed. Changed Markdown link targets and whitespace checks passed. Both reports above were read in full before integration; their immutable-source verdicts are preserved. Final PR and first merged main evidence remain pending.

## Round 2 — fresh code

# Code review 2026-10-12 — T-036 Step 7 Round 2, fresh independent code pass

- **Change:** immutable `development` tip `5c95cd3ab2bd97847ef3951b16c59d47563588e3`, against baseline `9c5191cfb8ced7e99e1afe459bb02852fde1a14b`. The runtime CI/probe implementation was committed as `bf20ec9739db635183b1b930f4da9f2c2b6813bf`; the reviewed tip adds the first-round reports, the verified Low correction and source-bound hosted evidence. Eleven changed files, 363 insertions / 40 deletions.
- **Reviewer:** fresh independent delegated code reviewer `/root/b21_step7_round2_code`, on behalf of @cemililik. All five master-plan roles were executed sequentially in this independent pass. This is a review recommendation, not maintainer approval or runtime model identity attestation.
- **Risk:** Ordinary CI/tooling/documentation. No shipped Rust, assembly, boot, scheduler, memory-management, syscall, capability, IPC or production unsafe code changes. A separately paired security pass is not required by the standard; CI supply-chain and failure boundaries were nevertheless examined.
- **Procedure:** read AGENTS.md, full CLAUDE.md, current.md, every numbered ADR in numerical order through ADR-0040 (0034 reserved), all fifteen standard files, both perform-code-review/conduct-review skills, full code-review master plan, complete canonical Round 1 artifact, task story, guide, entire workflow/probe and associated host configuration. Bounded follow-ups recovered truncated tool output. Tests/probe behavior were read before implementation review. No repository/live writes, branch changes or commits were performed. Private archive/controls and this temporary report are the only writes; canonical integration is assigned to the coordinator.

## Correctness

**Clean; no finding.** This is a fresh full implementation pass, not merely verification of the Round 1 prose fix.

The new job at `.github/workflows/ci.yml:275` is named `ARM64 host check + clippy + tests + Miri (nightly)`, runs on explicit `ubuntu-24.04-arm`, uses explicit Bash and a 15-minute timeout, installs pinned nightly clippy/Miri, sets the override and verifies both actual `uname -m = aarch64` and Rust `host: aarch64-unknown-linux-gnu` before executing checks. The pin agrees with `rust-toolchain.toml`: `nightly-2026-01-15`. Miri setup precedes interpretation.

The exact four mandatory commands are present and non-advisory:

```sh
cargo +"$NIGHTLY_PIN" check --workspace --exclude tyrne-bsp-qemu-virt
cargo +"$NIGHTLY_PIN" clippy --workspace --exclude tyrne-bsp-qemu-virt --all-targets -- -D warnings
cargo +"$NIGHTLY_PIN" test --workspace --exclude tyrne-bsp-qemu-virt
cargo +"$NIGHTLY_PIN" miri test --workspace --exclude tyrne-bsp-qemu-virt
```

Only the BSP is excluded. Explicit `--workspace` includes both userland members despite the workspace default-members excluding them. There is no default bare-metal target or global RUSTFLAGS; bare-metal codegen settings remain target-scoped. Native compile/link/test and Miri interpretation are distinct mandatory evidence. Hello's six predicates and its build script keep bare-metal entry/panic/linker behavior gated on both architecture and OS; native ARM exercises the host configuration, not EL0 SVC/MMIO or real hardware.

`tools/test-ci-gates.sh:21` refuses a non-aarch64 Rust host before copying, then uses NUL-delimited tracked-file enumeration, quoted paths, `cp -p`, private mktemp source/target paths and EXIT cleanup. Its `--arm-host` arm requires exactly six expected hello predicates; it modifies only the copied `userland/hello/src/main.rs`, leaving the copied build script and syscall shim intact. It runs exactly `cargo clippy --workspace --exclude tyrne-bsp-qemu-virt --all-targets -- -D warnings`. Nonzero status alone is insufficient: the precise E0152 duplicate `panic_impl` diagnostic must also occur. Unexpected green and unrelated compiler failure reject the probe. The probe's zero status means deliberate compiler rejection was correctly asserted, not a new production Miri failure.

Independent actual Apple ARM positive clippy and real negative compilation passed at the reviewed tip. Independent stub controls additionally verified all intended branches, unchanged private source and complete cleanup; evidence is detailed below. No shared Cargo target or userland image was modified.

## Style

**Clean; no finding.** Workflow conventions, full-SHA checkout/cache actions, explicit toolchain selection, readable job names and shell quoting are consistent with the existing pipeline. The literal-diagnostic ShellCheck suppression is narrow and justified. No new Rust API, error type, dependency or unsafe annotation obligation is introduced.

Independently executed `actionlint .github/workflows/ci.yml`, `shellcheck tools/test-ci-gates.sh`, `bash -n tools/test-ci-gates.sh` on the immutable private archive and `git diff --check 9c5191c 5c95cd3`: all exit 0. The implementation and review-follow-up commits use English Conventional Commits and valid ADR references; the follow-up has the canonical Code-Review trailer. Canonical Round 2 artifact/index integration is the coordinator's remaining mechanical task, consistent with this no-repository-writes assignment.

## Test coverage

**Adequate for this ordinary CI-only scope; no missing in-scope test.** The independent controls concentrate on the changed gate and its failure modes rather than gratuitously repeating unchanged broad gates.

### Newly executed real controls

Exact `5c95cd3` was exported with `git archive` to a private path containing spaces. CARGO_HOME, positive Cargo targets and temporary probe parents were private. A minimal git enumeration adapter supplied the immutable archive's tracked names; Rust/Cargo themselves were real installed tools, not stubs.

| Independent command | Result |
|---|---|
| `rustc -Vv` | `aarch64-apple-darwin`; rustc 1.94.0-nightly, commit 86a49fd71, 2026-01-14 |
| Exact pinned native workspace clippy, all targets, `-D warnings`, excluding only BSP | Exit 0; all five host-buildable workspace crates compiled, including both userland members |
| `bash tools/test-ci-gates.sh --arm-host` with actual compiler/Cargo | Harness exit 0; deliberate regression rejected with compiler exit 101 / exact E0152 duplicate panic_impl |
| Actionlint, ShellCheck, Bash syntax, diff whitespace | Exit 0 |

After execution, all **394 regular archived files** matched their immutable archive bytes; the private probe parent was empty. No kernel image was built by these controls. Newly executed local tests/Miri are not claimed here: their full-suite evidence is independently inspected hosted evidence and the separately preserved Round 1 local results.

### Newly executed controlled failure paths

Six independent cases ran under system `/bin/bash` with stub rustc/Cargo, each in its own private source tree with spaces. Apple ARM and Linux ARM expected rejection returned 0; unexpected compiler success returned 1; unrelated compiler error returned 1; x86 Rust host returned 1 without calling Cargo; a five-predicate anchor drift returned 1 without calling Cargo. Each case verified original private-source preservation and empty temporary parent after exit. Cargo-called cases asserted exact argv, private target path, complete six-predicate mutation, and unchanged copied hello build script/syscall shim.

These nominal Apple/Linux controlled cases prove harness behavior only. They are explicitly **stubs**, not independent real Linux/native/Miri executions. The separate actual Apple compiler execution above supplies real rejection evidence.

Private raw evidence is at `/var/folders/d2/k7c1fj3976g7_qq7113f66p00000gn/T/tyrne-t036-r2-code-3xr0e127`: `real-results.json`, `host.log`, `positive-clippy.log`, `real-negative.log`, `controlled-results.json` and each case's output/command record. This is reviewer-local evidence, not a committed artifact or a hosted rerun.

### Independently inspected hosted evidence

The coordinator-fetched `/tmp/tyrne-b21-step7/hosted-run.json` records a completed successful run with **all seven jobs successful**, including the informational coverage job. `/tmp/tyrne-b21-step7/hosted-arm.log` directly binds checkout to full source SHA `bf20ec9739db635183b1b930f4da9f2c2b6813bf` at lines 92–106. This is the actual hosted source, not the later documentation-only reviewed tip. Independently checked `git diff bf20ec9 5c95cd3` shows no CI/tooling/runtime configuration change between those SHAs, so the hosted implementation evidence remains applicable while the Round 2 prose correction is assessed directly.

The ARM log records real `aarch64` and `aarch64-unknown-linux-gnu` verification, pinned toolchain installation, all four exact workspace commands, E0152/exit101 negative rejection, actual Linux ARM Miri sysroot preparation, native/Miri execution of both userland host harnesses, and native/Miri totals of 46 HAL + 259 kernel + 58 test-HAL + 3 doctests = **366 passed**, with **two ignored HAL doctests**. No UB diagnostic is reported. API timestamps independently calculate ARM job **101 seconds**, Miri setup **17 seconds** and interpretation **54 seconds**; second-resolution times are diagnostic wall times, not performance benchmarks. Hosted link: https://github.com/HodeTech/Tyrne/actions/runs/38184932784/job/114605118899.

I inspected these fetched JSON/log files; I did not fetch a new hosted run, execute Linux ARM locally or rerun QEMU. Other six jobs' success is verified in the run JSON, not by independently inspecting each job log. Existing Miri optimization/provenance warnings, ignored doctests and host/guest scope limitations remain accurately bounded. This does not certify universal memory soundness or the known separate T-038 x2-clobber issue.

## Documentation

**Clean; no new finding. Round 1 Low fixed.** The complete canonical Round 1 report preserves both original immutable-source reports and their evidence boundaries. At reviewed tip `5c95cd3`, `docs/standards/testing.md:111` now explicitly states that the workflow is enabled while live required-check registration awaits hosted green and both fresh review rounds. This qualifies the parent enforced-gates heading and resolves CODE-T036-R1-01 / T036-R1-INTEGRATION-01. The task, guide, infrastructure standard, workflow header and current/index pointers agree on pending live registration and remain `In Review`, not Done.

The task correctly checks development-hosted success, records source-bound timings, and leaves final PR green, first merged-main verification and live ARM registration unchecked. The guide identifies exact display name, commands, host boundary, six-predicate copied regression and positive/native/Miri distinctions. The release standard describes prospective required release gates. ADR-0040 supplies Accepted authority for the policy before these standards edits.

Changed Markdown local-link checking, excluding inline-code examples, found **275 targets and zero missing paths**. Existing coverage-neutral / post-T-011 wording is an explicitly reserved T-035 correction immediately next, not a new T-036 finding. Known T-038 HIGH remains separate and is neither cleared nor reopened by this CI review. Historical roadmap banners and Round 1 reports retain point-in-time statements with reconciliation/current status provided explicitly.

## Integration

**Clean; no finding.** All seven cache exact keys and restore prefixes were checked individually: cargo host (lines 99/101), cargo-aarch64 (156/158), qemu-smoke (234/236), arm64-host (304/306), stable (354/356), Miri (393/395), llvmcov (444/446). All **14** include `${{ runner.os }}-${{ runner.arch }}`; no broad fallback crosses Linux x86/ARM. Distinct job namespaces remain separated. Lock hashes occur in exact keys; restore prefixes intentionally permit earlier lockfile caches within the same OS/architecture/job/toolchain namespace. The stable namespace remains rolling as before. The private rejection probe never uses the workflow shared target cache.

CI security remains within the existing disposable hosted-runner model: global `contents: read`; full-SHA checkout with `persist-credentials: false`; full-SHA cache; no new secrets, writable token scopes, publishing, pull_request_target, untrusted expression injection or self-hosted/privileged service. No `continue-on-error` weakens any ARM command/probe. Explicit Bash preserves pipe failures in host verification; the negative harness isolates its single intended failure with explicit status/diagnostic checking. The new job runs on normal push and PR triggers. Existing x86 host/stable/Miri, kernel, QEMU and informational coverage jobs retain their behavior apart from architecture cache segregation. Cache state is not claimed as an authenticity boundary.

No new Cargo dependency/lockfile change, binary blob, ABI/public API change, shipped TCB growth or audit-log obligation exists. T-037's correct target gating already exists in the baseline; this job adds independent detection. This review does not change live protection. Repository evidence and coordinator context identify the five already registered checks; independent live API read-back is not claimed by this reviewer. ARM registration should follow both fresh rounds and preserve the existing checks/source-app binding, then receive its own read-back evidence.

| Principle | Disposition |
|---|---|
| P1 No ambient authority | Pass: no runtime privilege change; read-only CI token. |
| P2 Smallest TCB | Pass: no shipped kernel/TCB growth. |
| P3 Userspace drivers/services | Unchanged: no subsystem placement/fault-boundary change. |
| P4 Boundary capability checks | Unchanged at runtime; CI host/probe boundaries fail closed. |
| P5 Rust kernel | Pass: shipped Rust/assembly unchanged; shell/Python are tooling. |
| P6 HAL separation | Pass: only BSP excluded from host checks; host tests do not claim device execution. |
| P7 No proprietary blobs | Pass: none added or required. |
| P8 ADR governance | Pass: Accepted ADR-0040 authorizes policy and staged review/registration. |
| P9 English repository | Pass: changed source/docs/commits are English. |
| P10 Mermaid diagrams | Not applicable: no diagram added. |
| P11 Reproducibility | Pass: pin/actions retained; all exact/fallback architecture boundaries preserved. |
| P12 Complete scope | Pass for implementation review: commands/probe/docs complete; live/final PR/main evidence remains pending rather than certified. |

Standard code-review checklist: correctness/pass; capability semantics/unchanged; fault containment/unchanged; unsafe/no change or new audit requirement; error handling/pass through independent fail-closed controls; test coverage/pass with actual/stub/inspected evidence separated; documentation/pass with Round 1 Low verified fixed; architectural principles/all twelve covered; dependencies/no additions; naming/style/pass; commit format/pass. The ordinary risk classification follows the actual change, not the sensitivity of unchanged baseline code copied by a negative experiment.

## Verdict

**Approve — zero new findings at Critical, High, Medium or Low severity.** All five roles and the complete applicable checklist were reassessed independently at immutable `5c95cd3ab2bd97847ef3951b16c59d47563588e3`; the Round 1 Low is corrected. No in-scope blocker was found.

This recommendation is for the reviewed tip only. It is not a Done-promotion, maintainer final approval, live administrative-action approval or first-main certification. Complete canonical Round 2 integration, the separately sequenced live ARM registration/read-back, final maintainer PR green/review and first merged-main evidence as required; T-036 remains In Review.

## Round 2 — fresh independent integration

# Code review 2026-10-12 — T-036 Step 7 Round 2, independent integration/test/documentation

- **Change:** `development`, baseline `9c5191cfb8ced7e99e1afe459bb02852fde1a14b` → immutable reviewed tip `5c95cd3ab2bd97847ef3951b16c59d47563588e3`. The implementation and hosted source is `bf20ec9739db635183b1b930f4da9f2c2b6813bf`; the second commit records first-round reports, the wording correction and source-bound hosted evidence. Eleven files changed overall, 363 insertions / 40 deletions. Workflow and probe bytes at the reviewed tip are identical to bf20ec9.
- **Reviewer:** fresh independent Codex delegated reviewer `/root/b21_step7_round2_integration`, acting on behalf of @cemililik. All five master-plan roles performed sequentially. This is a review recommendation, not maintainer approval, a Done promotion or live policy read-back.
- **Risk class:** Ordinary CI/tooling/docs-only change. No shipped Rust, assembly, capability, IPC, syscall, memory, scheduler, boot, public API, manifest, lockfile or production unsafe modification. Separate security artifact is not required; CI trust boundaries were reviewed below.
- **Security-review cross-reference:** n/a for this ordinary change. Existing T-038 HIGH syscall-register clobber work is explicitly outside this verdict.
- **Process:** Read AGENTS.md, full CLAUDE.md, current roadmap, every existing numbered ADR in numerical order through 0040 (0034 intentionally reserved), all fifteen standards, perform-code-review and conduct-review skills, complete code-review master plan, full canonical first-round report `docs/analysis/reviews/code-reviews/2026-10-12-t036-native-arm-ci.md`, task, workflow, probe and relevant Cargo/userland configuration. Bounded follow-up reads recovered truncated corpus output. Accepted ADR-0040 governs this step and its stacked-sequence review exception. No repository write, branch, commit or live settings operation was performed. Requested temporary-only scope leaves canonical filing/index integration to the coordinator.

## Correctness

**Clean; no new finding.**

The native job uses `ubuntu-24.04-arm`, a 15-minute timeout, explicit Bash, and the pinned `nightly-2026-01-15`. It installs clippy and Miri and sets that exact override before the probe's unqualified Cargo call. Before commands, both `uname -m = aarch64` and `rustc` host `aarch64-unknown-linux-gnu` must pass. There is no `--target`, global Cargo build target or host Rustflags redirecting this gate into cross-compilation. The actual hosted log confirms those host checks ran successfully rather than merely existing as YAML text.

The four mandatory commands are exact:

```sh
cargo +"$NIGHTLY_PIN" check --workspace --exclude tyrne-bsp-qemu-virt
cargo +"$NIGHTLY_PIN" clippy --workspace --exclude tyrne-bsp-qemu-virt --all-targets -- -D warnings
cargo +"$NIGHTLY_PIN" test --workspace --exclude tyrne-bsp-qemu-virt
cargo +"$NIGHTLY_PIN" miri test --workspace --exclude tyrne-bsp-qemu-virt
```

`cargo +"$NIGHTLY_PIN" miri setup` precedes interpretation. Only the BSP is excluded. Both `tyrne-user` and `tyrne-userland-hello` remain workspace members despite their absence from default-members, and both host harnesses occur in the hosted native and Miri logs. Positive native compilation/linking/execution and Miri are separate checks. Host results cannot certify bare-metal entry/SVC/MMIO or QEMU behavior.

The probe checks the Rust host before creating its temporary tree. It copies NUL-delimited tracked paths with preserved file modes, requires exactly six compound hello cfg predicates, replaces those six only in the private main.rs and keeps build.rs and the syscall shim unchanged. Its private Cargo target stays beside the private tree; EXIT cleanup removes both. It then executes the exact workspace all-targets clippy command. Nonzero status plus the fixed E0152 duplicate-panic_impl diagnostic is required. Unexpected compiler success and unrelated compiler failure both fail the harness. Compiler exit 101 and successful harness exit 0 are correctly distinguished; no production Miri failure is claimed by this deliberate compile rejection.

The T-037 compound target gating is already in the baseline and remains unchanged. Native hosts therefore receive the ordinary std hello stub and avoid the bare-metal linker script. The negative mutation isolates the original architecture-only predicate hazard without broadening into build-script or wrapper mutations.

## Style

**Clean.** Independently ran actionlint, ShellCheck for the changed script, Bash syntax checking and `git diff --check 9c5191c 5c95cd3`: all passed. New YAML follows existing SHA-pinned actions and toolchain conventions. The literal-diagnostic ShellCheck suppression is narrow and justified. Shell paths and variables are quoted; argument and failure handling are explicit. No Rust public item, unsafe block, error type or audit entry was added.

Both commits are English and use Conventional Commit form, with relevant ADR trailers. The follow-up documentation commit links its canonical review. No stylistic preference is promoted to a finding.

## Test coverage

**Adequate; no missing blocking test.** Fresh work focused on the unchanged harness and infrastructure failures, rather than repeating the already evidenced entire host/Miri/QEMU suite for a documentation follow-up.

### Fresh independent actual execution

Exported exact tip with `git archive` to `/tmp/tyrne-t036-r2-integration/frozen source`, containing 394 regular files. Only git tracked-file enumeration was supplied privately for the archive; actual rustc/Cargo were used, with private Cargo home and temporary target/tree. Actual host was `aarch64-apple-darwin`; installed compiler reported `rustc 1.94.0-nightly (86a49fd71 2026-01-14)`. Running `/bin/bash tools/test-ci-gates.sh --arm-host` produced the expected clippy exit 101 / E0152 diagnostic and harness exit 0. All archived regular-file hashes were unchanged afterward and the private temporary parent was empty. No shared userland image was produced or replaced.

Fresh logs and controls: `/tmp/tyrne-t036-r2-integration/real-negative.log`, `run-controls.py`, `results.json`, and per-case `output.log` files. The real-negative log intentionally contains the harness's recorded rejection summary; the harness captures the underlying compiler stream in its disposable tree and removes it on cleanup. Actual tool identity was independently checked before the run. No Linux execution is inferred from this local run.

### Fresh controlled failure paths

Nine private cases use stub rustc/Cargo and are explicitly harness controls, not compiler or Linux evidence:

| Controlled case | Harness exit | Cargo called | Result |
|---|---:|---|---|
| Intended E0152 rejection | 0 | Yes | Accepts the intended assertion |
| Unexpectedly green command | 1 | Yes | Refuses false green |
| Unrelated compiler error | 1 | Yes | Refuses unrelated failure |
| x86 Rust host | 1 | No | Refuses wrong host |
| Five instead of six cfg anchors | 1 | No | Refuses source drift |
| rustc tool failure | 42 | No | Propagates infrastructure failure |
| Missing Rust host field | 1 | No | Refuses incomplete identification |
| Python mutation failure | 43 | No | Fails before Cargo |
| File-copy failure | 43 | No | Fails before mutation/Cargo |

Every case preserved its original source hashes and left its temporary parent empty. Cargo-capable controls asserted exact argv, all-six mutation, unchanged build.rs and syscall shim, executable script preservation and a private Cargo target. Paths contain spaces. The fixture uses absolute interpreter paths so injected Python failure reaches the mutation invocation rather than breaking the tool stubs. Its `/tmp` versus `/private/tmp` comparisons use resolved paths; an initial fixture assertion was corrected for that macOS alias before the complete passing run. Those fixture corrections did not change repository source.

### Independently inspected existing hosted evidence

I independently read the provided `/tmp/tyrne-b21-step7/hosted-run.json` and relevant `/tmp/tyrne-b21-step7/hosted-arm.log` evidence. I did not launch or fetch a new hosted run and did not execute Linux locally.

JSON reports completed success for all seven jobs in run 38184932784: ARM, coverage, QEMU, kernel, x86 Miri, stable and lint/host tests. ARM job 114605118899 spans 101 seconds by API timestamps; check/clippy/negative/native tests/setup/Miri are 1/1/7/4/17/54 seconds. These second-granularity figures are execution records, not benchmarks.

The ARM log binds the checkout to full source bf20ec9 at lines 92–106 and records installed pinned compiler, actual aarch64 machine and Linux Rust host at 127–148. Exact commands occur at 170–205 and 639–692. The rejection summary at 203 records exit101/E0152. Native and Miri each pass 46 HAL + 259 kernel + 58 test-HAL + 3 doctests = 366 tests, with two ignored HAL doctests. Both userland host harnesses build/run with zero tests. Miri paths are `target/miri/aarch64-unknown-linux-gnu`; setup and interpretation are separate successful steps. Existing Miri optimization/provenance warnings do not report UB, and successful interpretation proves the exercised paths only. [Hosted ARM job](https://github.com/HodeTech/Tyrne/actions/runs/38184932784/job/114605118899).

The canonical first-round report separately records prior actual Apple Silicon positive check/clippy/test/Miri execution and its raw logs. That is inspected prior evidence, not a fresh positive-suite execution by this reviewer. The byte-identical workflow/probe between hosted source and reviewed tip makes that hosted evidence applicable to the implementation; it does not constitute a hosted run of the follow-up documentation SHA.

## Documentation

**The duplicate Round 1 Low is fixed; no new finding.** At `docs/standards/testing.md:111`, the ARM bullet still appears beneath the enforced-gates heading but now explicitly states that the workflow is enabled and live required-check registration awaits hosted green and both fresh rounds. Together with the guide, infrastructure's separate pending ARM display name, task unchecked live criterion and current pointers, this removes the premature claim that the new workflow itself already blocks merge. The hosted prerequisite has now been satisfied; live registration and the two-round process remain separately recorded rather than inferred.

The reviewed follow-up records source-bound hosted success and measured timing honestly. Task/current/index remain `In Review`; task final-PR green, first merged-main run and live registration are unchecked. The canonical first-round reports preserve immutable bf20ec9 findings and add a reconciliation/correction rather than silently rewriting what those reviewers saw. Both first-round reports were read in full.

Guide commands, only-BSP exclusion, native-versus-guest boundary, mandatory Miri, private arch-only experiment, intended display name and registration sequence match source. Relative file targets in all changed Markdown were checked independently: 275 resolve, with the documentation's literal `](...)` example excluded. This file-existence check does not validate every heading fragment or external link. No changed heading introduces a newly broken fragment in the examined links.

The pre-existing coverage-neutral/post-T-011 prose is expressly reserved for immediately next T-035 under the accepted sequence. It is not a new T-036 finding. The host evidence neither resolves nor downgrades T-038's separate HIGH clobber issue.

## Integration

**Clean; no integration blocker.** All seven jobs remain. Existing x86/stable/Miri/coverage/cross-build/QEMU command behavior is retained; the only changes in their implementations are architecture-separated cache identities. Native ARM is additional coverage, not a substitute for those jobs.

All seven actions/cache blocks and all 14 exact-key/restore-prefix lines were independently checked:

| Namespace | Exact key | Restore prefix |
|---|---:|---:|
| cargo host | 99 | 101 |
| cargo-aarch64 kernel | 156 | 158 |
| qemu-smoke | 234 | 236 |
| arm64-host | 304 | 306 |
| cargo-stable | 354 | 356 |
| miri | 393 | 395 |
| llvmcov | 444 | 446 |

Every exact key and every fallback starts with `${{ runner.os }}-${{ runner.arch }}-`, followed by a distinct job namespace. Pinned namespaces retain nightly identity; stable retains its prior rolling-stable namespace. Exact keys retain lock hashes; restore prefixes deliberately allow an older lock cache within the same OS/architecture/job/toolchain namespace. No broad fallback can restore x86 build state onto ARM. The negative probe bypasses that shared target via its private target tree.

CI security: unchanged top-level `contents: read`, fully SHA-pinned checkout/cache actions, and all checkouts retain `persist-credentials: false`. No secrets, new action dependency, admin token, privileged service, self-hosted runner, writable token scope, pull_request_target trigger, publishing or live-policy mutation is introduced. Shell source does not interpolate untrusted PR content. Explicit Bash preserves pipeline failure; ARM has no continue-on-error and no condition skipping a required positive step. Expected compiler failure is narrowly handled and authenticated by diagnostic rather than treated as arbitrary success. Bounded timeout limits a hang. Cache state remains a performance/build input, not an authenticity claim.

### Architectural principles P1–P12

| Principle | Assessment |
|---|---|
| P1 No ambient authority | Pass: runtime unchanged; CI token remains read-only. |
| P2 Smallest defensible TCB | Pass: no shipped TCB growth; bounded host tooling only. |
| P3 Userspace drivers/services | Unchanged: no placement or fault-boundary move. |
| P4 Checks at boundaries | Pass within scope: host/source-anchor/failure controls fail closed; no runtime boundary changed. |
| P5 Rust-only kernel | Pass: no kernel-language change; Bash/Python remain host tooling. |
| P6 HAL separation | Pass: only inherently bare-metal BSP excluded; hardware behavior remains separate evidence. |
| P7 No proprietary blobs | Pass: none added, embedded or required by this delta. |
| P8 ADR governance | Pass: Accepted ADR-0040 precedes runner/command/Miri/registration policy and standards changes. |
| P9 English repository | Pass: changed artifacts and commits are English. |
| P10 Mermaid diagrams | N/a: no diagram changes. |
| P11 Reproducibility | Pass within scope: exact nightly/action pins retained, lock identities retained, every fallback separates architecture. |
| P12 Complete declared scope | Pass for implementation review: positive/negative gates implemented; live registration/review/final PR/post-merge remain explicit process obligations. |

### Full standard checklist

- Correctness: pass, native target and probe assertions verified.
- Capability semantics: unchanged; no authority/handle/right behavior touched.
- Fault containment: runtime unchanged; probe isolation and cleanup verified.
- Unsafe: no production Rust/unsafe change; no SAFETY/audit/security-approval obligation created.
- Error handling: pass; tool, copy, mutation, unrelated compiler and false-green controls fail closed.
- Tests: pass; actual local negative, fresh controlled cases, syntax/lint checks and inspected source-bound hosted positives clearly distinguished.
- Documentation: pass; Round 1 Low corrected, pending obligations retained, file targets resolve.
- Architecture: all P1–P12 assessed above; no new decision beyond Accepted ADR-0040.
- Dependencies: no manifest/lock/dependency/blob additions.
- Style: pass; actionlint, ShellCheck, Bash syntax and whitespace clean.
- Commit format: pass; English Conventional Commits and ADR/review trailers.
- Review artifact/index: coordinator integration deferred by explicit temporary-report-only assignment.

## Verdict

**Approve. Zero Critical, High, Medium or Low findings in this fresh second-round review.** The first-round Low was independently verified as fixed. All five roles, P1–P12 and the full standard checklist are complete at immutable `5c95cd3ab2bd97847ef3951b16c59d47563588e3`.

Live ARM registration/full-policy read-back, final maintainer PR green/review and first merged-main evidence remain separate pending actions. This recommendation does not promote the task to Done, certify a later SHA, record a live policy write or resolve T-038. Repository worktree remained clean at the frozen SHA after this pass.

## Coordinator Round 2 reconciliation

Fresh `b21_step7_round2_code` and `b21_step7_round2_integration`, each requested `gpt-6.1-sol` / high with empty inherited context, independently Approve. Both full reports were read before integration. No new finding or fix commit is needed. Independent actual/compiler and controlled failure checks support the unchanged implementation; live registration/read-back is the next separately authorized action. Final PR and first merged main evidence remain pending.

## Subsequent live registration

After both fresh rounds, coordinator added exactly the ARM check from remotely green source bf20ec9. The full policy immediately before and after was compared against the prior five-check baseline: all six app bindings15368, strict and every non-status setting were preserved. This subsequent action does not rewrite either immutable review verdict. Final PR and first merged main remain pending.
