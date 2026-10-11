# Code review 2026-10-12 — T-036 native ARM CI

- **Change:** approved Track B.2-1 step 7, `9c5191c..bf20ec9`.
- **Round 1 reviewers:** fresh `b21_step7_round1_code` and `b21_step7_round1_integration`, each requested `gpt-6.1-sol` / high, empty inherited context. Configuration provenance, not runtime identity attestation.
- **Risk:** Ordinary CI/tooling-only delta; no shipped Rust or unsafe change.

> **Reconciliation:** Round 1 both Approve, one duplicate Low premature merge-enforcement wording finding. Coordinator verified and corrected it; actual hosted Linux ARM job passed in 101 s and all seven development jobs passed. Round 2, live registration, final PR and post-merge evidence remain pending. T-036 stays In Review.

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
