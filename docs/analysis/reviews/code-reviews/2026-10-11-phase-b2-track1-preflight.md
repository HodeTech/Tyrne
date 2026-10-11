# Code review 2026-10-11 — Phase B.2 Track B.2-1 preflight

- **Change:** Track B.2-1 task/decision contracts at baseline `7786582`, reviewed on `development`; documentation corrections and proposed execution policy in this change.
- **Reviewer:** Codex (root), with independent read-only reviews by `b21_docs_ci_review` (GPT-6.1-sol, high) and `b21_docs_governance_review` (GPT-6-astra, high).
- **Risk class:** Ordinary — this change edits planning/review documents only; security-sensitive implementation receives separate security review under its task.
- **Security-review cross-reference:** n/a for this documentation change; T-037 and applicable T-031/T-032 source changes explicitly require separate security passes.

## Correctness

The existing CI/source premises were checked against the tree, rather than inferred from the backlog. The root reviewer read the canonical agent guide, numbered ADR corpus and standards; the supplementary governance pass read the full Phase B.2 plan, `current.md` including historical banners, all 46 Phase B.2 tasks and the requested roadmap/task indexes. Direct review also covered the Track B.2-1 task contracts, T-037, applicable skills, CI workflow/Cargo configuration and the CI/QEMU guides. The original July review is local-only and is not a task dependency.

Verified findings and actions:

| ID | Severity | Finding | Action in this preflight / implementation owner |
|----|----------|---------|--------------------------------------------------|
| PF-01 | High | Smoke completion can be printed by kernel task A independently of EL0 registration; the existing gate cannot establish its claimed EL0 round trip. | T-034 now requires the existing greeting and task-exit markers plus completion/fault checks, with an omitted-EL0 negative probe. Runtime fix belongs to T-034. |
| PF-02 | Medium | The track requires release tests for a bare-metal BSP with no host-test target; baseline prose conflates debug/release totals. | Distinguish bare-metal compilation from host tests; correct debug 366 versus release 356 in ADR-0040 and the current banner. |
| PF-03 | Medium | Named polish is inconsistently described as gating, and optional T-036/T-056 benefits are unconditional. | Reconcile the index and ADR benefits with rule 3; T-036 is explicitly included in this requested sequence without changing the whole phase's optional-task rule. T-074's own exit-gating contract is preserved. |
| PF-04 | Medium | The scope checkpoint permits reversing Option A through a revision note. | Require a superseding ADR for outcome reversal, preserving clarification/allowed-deferral riders. |
| PF-05 | Medium | T-035 offers PR-gated performance without a matching threshold contract; a standard edit is offered as an alternative to ADR governance. | Propose weekly/on-demand informational reporting and existing-protection JSON in ADR-0040; standards follow Acceptance. Synchronise T-035's criteria with those choices. |
| PF-06 | Medium | T-036's mandatory native commands conflict with its check-plus-Miri option, and merge policy may be decided only in task history. | Propose required native check/clippy/test plus Miri on Ubuntu ARM in ADR-0040; routine setup remains in task history. |
| PF-07 | Medium | T-037 says build scripts cannot see custom target cfgs. | Correct the distinction between Cargo's `CARGO_CFG_*` environment and host compilation of the build script; retain inline architecture-and-OS gates as the recommendation. |
| PF-08 | Medium | Conditional unsafe/security review obligations are incomplete; T-037 defers its audit synchronisation to another task. | Require distinct security review/trailers where applicable and a T-037 target-narrowing amendment to UNSAFE-2026-0033; T-038 retains the clobber amendment. |
| PF-09 | Medium | Scratch-branch probes, dependency-`Done` sequencing and pre-merge `main` evidence conflict with the requested single-branch/end-only PR workflow. | Propose isolated-copy/runner probes and the narrowly scoped stacked-execution convention; keep tasks `In Review` and distinguish local, hosted, PR and post-merge evidence. |
| PF-10 | Medium | ADR-0040/T-075 can count a recorded "yes" as completing a task whose chosen path still requires implementation. | Clarify exit-accounted permitted deferral versus chosen implementation criteria and maintainer-only `Done`. |
| PF-11 | Low | CI's permissions comment says it never uploads artifacts, which T-034 invalidates. | Add its correction to T-034's documentation criterion; keep least-privilege permissions. |

All listed documentation actions are applied in this change. No runtime fix or CI enforcement is claimed complete. ADR-0040 remains `Proposed`; T-035/T-036 stay `Draft` pending its Acceptance. The eight-step sequence in the task index includes T-037 as the only cross-track prerequisite.

## Style

Repository prose remains English. Existing task IDs, statuses and Accepted ADR bodies are preserved; policy changes are proposed in the still-editable ADR-0040. No source/configuration changes, new dependency, new unsafe identifier, branch switch away from `development`, or live GitHub mutation is part of this preflight correction.

## Test coverage

Baseline checks on 2026-10-11, pinned `nightly-2026-01-15`, Apple Silicon:

- `cargo host-test --quiet`: 46 HAL + 259 kernel + 58 test-HAL + 3 passing doctests = **366**; two pre-existing HAL doctest examples are ignored and are not counted as passing.
- `cargo test --release --quiet`: 46 HAL + 249 kernel + 58 test-HAL + 3 passing doctests = **356**; the same two doctest examples are ignored. Three cfg-dependent unused imports are reported in `kernel/src/syscall/dispatch.rs` tests; T-030 will clean those while establishing release verification, without changing syscall gate logic.
- The independent CI review reproduced ShellCheck 0.11.0's one warning/four information findings (exit 1), matching T-031's recorded baseline.

These checks establish existing evidence and correct the count claims; they do not substitute for the implementation's negative tests, hosted results, artifacts or live protection read-back. Each gate task specifies both its positive run and isolated negative probes. A probe harness that correctly detects failure can pass; it must not be reported as a red production workflow.

## Documentation

The reviewed policy packet is ADR-0040, the Track B.2-1 sequence in the task index, T-030…T-037 and the narrowly related T-075 exit-accounting clarification. A separate ADR number is unnecessary because the governing ADR is still `Proposed`. After Acceptance, implementation updates the affected guides/standards alongside each step and performs a final cross-document reconciliation before the PR.

Release kernel clippy is included now. Release EL0 smoke needs a valid scenario for the intentionally absent debug-console syscall; the current hello expects that syscall. T-065/T-067 retain their feature/scenario contracts, and the CI docs must state the existing limitation rather than imply release boot coverage.

## Integration

Read-only GitHub inspection on 2026-10-11 found a public `HodeTech/Tyrne` repository, default branch `main`, no repository rulesets and classic `main` protection with these required GitHub Actions display names:

- `fmt + clippy + host tests (nightly)`
- `aarch64-unknown-none kernel build (nightly)`
- `host crates on stable`
- `miri (Stacked Borrows)`

Strict up-to-date checks, linear history and conversation resolution are enabled; force pushes and deletion are disabled. T-035's proposed representation preserves the live mechanism and existing policy; smoke/ARM checks are added only after remote success. No administrative token is proposed for CI.

The ARM runner's availability was verified from [GitHub's runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners); Cargo's target-cfg statement was checked against [Cargo's environment reference](https://doc.rust-lang.org/cargo/reference/environment-variables.html#environment-variables-cargo-sets-for-build-scripts). The proposed performance workflow has a targeted `development` validation trigger because its first default-branch dispatch cannot be certified before merge. Native `main`/dispatch evidence remains explicitly pending until the maintainer merges; no fabricated status transition closes that gap.

## Verdict

**Comment — documentation contracts corrected; maintainer Acceptance pending.**

Implementation may begin only after the maintainer approves the concrete revised ADR-0040. The required eight-step implementation and two fresh review rounds per step are still ahead. This preflight is neither a Phase B.2 closure nor an approval to mark any task `Done`.

## Review history

| Date | Reviewer | Evidence / result |
|------|----------|-------------------|
| 2026-10-11 | `b21_docs_ci_review`, GPT-6.1-sol high | Independent source/CI/task-contract pass; eight verified findings, incorporated above. No edits. |
| 2026-10-11 | `b21_docs_governance_review`, GPT-6-astra high | Independent governance/dependency pass and complete supplementary roadmap/task-corpus pass; verified contract issues incorporated above. No edits. |
| 2026-10-11 | Codex root | Reconciled findings against source/standards; reran debug/release baselines; drafted the corrected policy packet. |
