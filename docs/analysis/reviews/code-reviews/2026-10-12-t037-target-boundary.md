# Code review 2026-10-12 — T-037 target boundary

Independent round 1 review of the first approved Track B.2-1 implementation step: restrict the hello entry/build script and userspace SVC shims to bare-metal aarch64 while restoring ARM host workspace tooling.

- **Reviewer:** `b21_step1_round1_code`, independent fresh agent context, delegated by Codex root.
- **Reviewed:** `960bdef..f2d577f`; implementation commit `f2d577f96b4c98f3c0998f538304e38d4232d409`, on `development`.
- **Procedure:** [perform-code-review](../../../../.agents/skills/perform-code-review/SKILL.md), [conduct-review](../../../../.agents/skills/conduct-review/SKILL.md), and the [code master plan](master-plan.md).
- **Risk class:** security-sensitive compilation boundary around existing syscall assembly and the userspace entry; no assembly instruction or operand change.
- **Paired security review:** [`b21_step1_round1_security`'s distinct pass](../security-reviews/2026-10-12-t037-target-boundary.md), communicated to this reviewer as **Approve** for the target-boundary narrowing. It expressly excludes the existing T-038 x2 defect.
- **Cycle state:** round 1 recorded; the second fresh code/security round remains pending. This artifact is not a Done-promotion, merge-readiness, or maintainer-approval verdict.

## Correctness

**Clean for the reviewed implementation.** The reviewer first read T-037's opening baseline, acceptance criteria, review history, the prior [preflight](2026-10-11-phase-b2-track1-preflight.md), and the [ADR-0040 approval follow-up](2026-10-11-adr-0040-approval-follow-up.md). The implementation was then read in dependency order: userspace types/constants/wrappers, hello's target build selection, and the hello caller/entry/panic/host paths. Complete changed source files, manifests, Cargo target flags/aliases, linker script, build pipeline, and affected CI command definitions were inspected.

All 13 userland Rust cfg gates require `all(target_arch = "aarch64", target_os = "none")`; the three host stub gates use its exact negation. On ARM desktop hosts, hello therefore selects ordinary `std` and `main`, while `tyrne-user` remains `no_std` with its pre-existing safe host stubs. The build script reads Cargo's **target** architecture and OS environment, rather than the build-script binary's host cfg. Its linker decision agrees with the source gates and the BSP's established predicate.

The diff changes no syscall number, capability word, public signature, SVC instruction, assembly operand, return/error branch, panic behavior on the bare-metal target, or entry/link section. Debug image bytes are independently preserved. The known input-only x2 defect is unchanged and remains [T-038](../../tasks/phase-b2/T-038-console-write-x2-clobber.md)'s owner; passing tests and an unchanged image do not certify its soundness.

## Style

**Clean.** Rustfmt and workspace clippy with warnings denied pass. The inline predicate requires no custom cfg registration, dependency, or new build configuration. Comments explain why ARM host architecture is insufficient and cross-reference the other two userland gates and the BSP gate. No preference-only refactor is requested.

## Test coverage

**Clean for this step's declared scope.** The existing workspace compilation/test commands exercise the broken ARM host selection directly. An isolated before/after test-harness compilation reproduced the pre-fix duplicate panic handler and demonstrated that the current hello source compiles with the same native compiler/dependency arguments. The build-script matrix independently checks both axes and missing variables. Bare-metal build/hash and QEMU trace checks cover the retained target path.

Commands executed independently on Apple Silicon, host `aarch64-apple-darwin`, pinned `nightly-2026-01-15` (`rustc 1.94.0-nightly`, commit `86a49fd71`, LLVM 21.1.8):

| Command / check | Result |
|-----------------|--------|
| `cargo check --workspace --exclude tyrne-bsp-qemu-virt` | PASS |
| `cargo clippy --workspace --exclude tyrne-bsp-qemu-virt --all-targets -- -D warnings` | PASS |
| `cargo test --workspace --exclude tyrne-bsp-qemu-virt --quiet` | PASS: 46 HAL + 259 kernel + 58 test-HAL + 3 doctests = **366**; two pre-existing HAL doctests ignored |
| `cargo fmt --all -- --check` | PASS |
| `tools/build-userland.sh` | PASS; debug image **117 bytes** |
| `shasum -a 256 userland/hello/hello.bin` and `wc -c userland/hello/hello.bin` | **117 bytes**, SHA-256 `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88` |
| `cargo kernel-build` | PASS |
| `cargo kernel-clippy` | PASS |
| `tools/smoke.sh --int --timeout 5` | PASS; trace manually checked for greeting, userspace exit, completion, exactly two SVCs, and no panic/fault |
| Compiled `userland/hello/build.rs` matrix | PASS: linker argument present only for aarch64/none; absent for aarch64/macos, aarch64/linux, x86_64/linux, x86_64/none, and both target variables missing. Both rerun directives remain present. |
| Native `rustc --test` before/after regression | PASS as a regression probe: hello at `960bdef` fails with **E0152 duplicate panic_impl**; hello at `f2d577f` compiles |
| `rg` sweep of userland architecture/OS gates | PASS: no architecture-only Rust gate remains |

The build-script matrix compiled the repository script with `rustc` into a temporary directory, supplied `CARGO_MANIFEST_DIR` and each listed Cargo target environment, and asserted both linker selection and the two rerun directives. The before/after probe wrote only the baseline hello source to a temporary directory and invoked `rustc --edition=2021 --test --extern tyrne_user=<existing host rlib> -L dependency=target/debug/deps`, first on that baseline and then on current hello, with outputs in the temporary directory. It checks the changed entry/panic selection, not a complete baseline workspace checkout.

**Limits:** this reviewer did not rerun full workspace Miri, stable, release, Linux ARM, hosted CI, or hardware checks. T-037 records the author's exact workspace Miri pass; its historical pre-fix failure is also recorded in the prior approval artifact. Those are author/prior-review evidence, not independent Miri execution by this reviewer. The paired security reviewer separately reports its own Miri and cfg-expansion checks. No performance conclusion follows from this single QEMU smoke run.

## Documentation

Two **Low**, nonblocking lifecycle findings were returned against **f2d577f**. File:line references in this table refer to that commit, before follow-up edits.

| ID | Severity / location | Finding and required correction |
|----|---------------------|---------------------------------|
| T037-CR1-01 | Low — `docs/analysis/tasks/phase-b2/T-037-userland-bare-metal-cfg-gate.md:20–22` | Context describes the old architecture-only gates and says the scratch fix “has NOT been applied,” contradicting the implementation and checked criteria. Identify this explicitly as the opening snapshot and record that f2d577f applied the fix. |
| T037-CR1-02 | Low — `docs/roadmap/current.md:82`, `:83`, `:85` | The top pointer correctly says T-037 In Review on development, while live Active task/In review/Working branch fields still say none, pending ADR Acceptance, and `docs/phase-b2-kickoff`. Synchronize the live fields while preserving labeled historical content. |

At the reviewed commit, T-037:57's checked roadmap-update criterion overstates lifecycle reconciliation because those live fields contradict the new pointer. No behavioral acceptance criterion was found falsely checked. The security/audit completion criterion at T-037:55 is correctly unchecked at f2d577f; a distinct security artifact/trailer and amendment's introducing SHA are required follow-up, not completed evidence at that commit.

**Follow-up observation, separate from the reviewed range:** after the initial verdict, root authorized this reviewer to write only this artifact and its index row. Root's working changes were inspected: the task's scratch-fix sentence now distinguishes task opening from f2d577f implementation; the roadmap adds a dated implementation banner and synchronizes the three live prefixes. This is a limited inspection of the working lifecycle corrections, not a replacement review of a committed follow-up range or completion of the second fresh round. Root also has audit/security-recording edits in progress; this code artifact does not certify the uncommitted trailer or those completion claims.

## Integration

**Clean locally.** Native ARM workspace commands and the explicit aarch64-none build both pass. No dependency, lockfile, toolchain, feature, coverage scope, CI job, or architectural contract changes. The build script's target environment agrees with the Rust cfg decision. Existing CI workspace Miri includes the userland members, while the narrower default-member host aliases and coverage exclusions are unchanged. The future native ARM hosted gate remains [T-036](../../tasks/phase-b2/T-036-ci-arm64-host-check-job.md)'s scope.

The required standards checklist was considered:

| Item | Outcome |
|------|---------|
| Correctness, invariants and API contracts | Satisfied for target selection; unchanged SVC bodies retain the explicitly owned T-038 defect. |
| Capability semantics and fault containment | No authority, transfer, revocation, caller table, user-pointer handling, or kernel fault behavior change. |
| Unsafe discipline | Existing compilation boundary narrowed; original audit fields preserved and an amendment added. Paired security review covers the narrowing; completion recording follows separately. |
| Error handling | No new error type, swallowed error, panic path, or changed failure behavior. |
| Tests and style | Independent results above; all applicable local checks pass. |
| Documentation | Two Low lifecycle findings above; no architectural guide or public API expansion required. |
| P1–P12 | No new ambient authority/TCB/driver placement/trust-boundary change; Rust/HAL/blob/ADR/language/diagram/reproducibility/incremental-scope requirements respected. |
| Dependencies and commit references | No dependency addition; commit has valid `Refs: ADR-0040` and `Audit: UNSAFE-2026-0033`. Security trailer is pending follow-up at the reviewed commit. |
| Post-fix sweep | All userland cfg gates checked; historical architecture-only wording in the original append-only audit entry is preserved and qualified by its amendment. |

## Verdict

**Approve — code scope only**, with T037-CR1-01 and T037-CR1-02 to correct before round 2. No new runtime blocker was found. The distinct [security pass](../security-reviews/2026-10-12-t037-target-boundary.md) approves this boundary narrowing without certifying T-038's existing x2 contract.

The complete two-round cycle, committed follow-up review, security-record/trailer finalization, final PR, maintainer review and Done promotion are outside this round 1 verdict and remain pending as applicable. Review work made no source edits, commits, branch changes, or external calls. The repository was clean at the end of the read-only verdict pass; subsequent authorization permits only this code-review artifact and its index row.

## Review history

| Date | Reviewer | Evidence / result |
|------|----------|-------------------|
| 2026-10-12 | `b21_step1_round1_code` | Fresh independent round 1 on `960bdef..f2d577f`: AGENTS/CLAUDE/current roadmap, numbered ADRs in numerical order, all standards, skills, prior evidence, full changed source and local checks. Approve code scope; two Low lifecycle findings returned. |
| 2026-10-12 | `b21_step1_round1_code` | Parent authorized only this artifact and index row after the verdict. Limited inspection of root's working lifecycle corrections noted above; second fresh round remains pending. |
