# T-035 — Track and land the CI hygiene tail (perf-harness schedule, merge gates as code)

- **Phase:** B.2
- **Milestone:** Track B.2-1
- **Status:** In Review
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-034](T-034-ci-qemu-smoke-job.md), [T-036](T-036-ci-arm64-host-check-job.md)
- **Informs:** none
- **ADRs required:** ADR-0040 (Accepted), including its Track B.2-1 implementation policy

---

## User story

As the maintainer, I want an explicit, recorded decision on whether the performance harness runs on a schedule in CI and whether the merge-gate configuration is kept as reviewable code, so that two low-priority gaps are either closed or consciously accepted instead of drifting as trusted-by-comment.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) as a decision-bearing task. The Accepted Track B.2-1 policy chooses implementation of both items; recording those choices alone does not satisfy the remaining implementation and evidence criteria. At the opening baseline, `tools/perf-harness.sh` was the canonical source for boot-to-end timing claims but no CI job ran it (`docs/standards/infrastructure.md:114` says "Maintainer-launched only; not yet wired into CI"), so there was no automated performance signal. Separately, "what gates merge" was stated only in the `ci.yml` header comment (`.github/workflows/ci.yml:7-9`) and prose (`docs/guides/ci.md:85-91`, `infrastructure.md:186`); the actual required-checks list was a GitHub setting that no diff could review.

This task covers two items of `phase-b2.md` Track B.2-1 (line numbers as of the opening snapshot; locate by headline): LOW "`tools/perf-harness.sh` is likewise never invoked by CI" (line 51) and INFO "'What gates merge' is documented only in comments, not verifiable as code" (line 60). The track's acceptance criteria explicitly allow these low/info tails to be tracked without all landing in B.2, and the phase's closing note requires a scheduled-versus-gated CI choice to be routed through ADR governance rather than decided inside the backlog.

## Acceptance criteria

- [x] Decision D1 is Accepted in ADR-0040 before implementation: weekly Monday `03:17 UTC` plus `workflow_dispatch`, informational, with a `development` push trigger limited to changes to the performance workflow or harness for pre-merge validation.
- [x] Decision D2 is Accepted in ADR-0040 before implementation: version the existing classic `main` branch protection as JSON, with read-only export/check and explicit local apply tooling; no Terraform or ruleset migration.
- [x] The performance workflow builds the debug userland and kernel, runs `tools/perf-harness.sh --iterations=20 --report=ci-nightly`, and uploads the report with SHA/toolchain/QEMU metadata. Its first hosted `development` run is green and the downloaded artifact contents and wall time are recorded. The job is not a required check.
- [ ] Verify manual dispatch after default-branch registration following maintainer merge; keep that evidence pending until it exists.
- [x] The committed branch-protection definition preserves every existing setting and the GitHub Actions application bindings, includes the remote-green smoke and ARM checks, and has documented export, diff/check and apply commands. A read-back comparison against the live settings is clean; unexpected drift stops apply until reconciled. No administrative secret is available to CI.
- [x] Documentation: `docs/guides/ci.md` and `docs/standards/infrastructure.md` (including the line-114 sentence in the performance-harness section and the "Planned gates" list) match the decisions taken; the `ci.yml` header comment (lines 7-9) is still accurate. Explain that GitHub schedules are best effort, run from the default branch, and are automatically disabled after 60 days without repository activity in public repositories; document how to re-enable/dispatch the workflow.

## Out of scope

- The merge-gating smoke job itself: [T-034](T-034-ci-qemu-smoke-job.md) (this task depends on it landing first, as the plan item says).
- A regression-detecting harness mode (a `--baseline` option taking a previous report file), which `infrastructure.md:134` marks as not in scope for v1.
- Release-profile and `perf-bench` build gates: [T-030](T-030-ci-release-profile-gate.md).
- An arm64 host-check job: [T-036](T-036-ci-arm64-host-check-job.md).

## Approach

Implement ADR-0040's Accepted D1-D3 policy. Use a separate performance workflow to keep measurements off the required PR pipeline; follow the repo's SHA pinning and least-privilege conventions, build the userland image before the kernel, and archive the report. Read-only inspection on 2026-10-11 found `gh api repos/HodeTech/Tyrne/rulesets` empty and `main` protected by classic branch protection. Export that existing mechanism through `gh api repos/HodeTech/Tyrne/branches/main/protection`; normalise response-only metadata separately from the apply payload, preserve all policy fields, and fail closed on settings the tooling cannot represent. Test drift detection and apply preconditions against local fixtures before any live mutation. Also query GraphQL-only deployment/review/actor policy and refuse nonempty unsupported extensions or new rulesets. Apply only after new required checks have succeeded remotely, then compare full read-back. Smoke/ARM were already registered in T-034/T-036, so this step's real apply is a verified no-op; offline fixtures exercise the mutating path.

## Definition of done

Beyond the acceptance criteria:

- [x] `cargo fmt --all -- --check` clean.
- [x] `cargo host-clippy` clean with `-D warnings`.
- [x] `cargo kernel-clippy` clean.
- [x] `cargo host-test` passes.
- [x] Every touched markdown file has all `](...)` link targets resolving.
- [x] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [x] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Decisions Accepted by the maintainer in ADR-0040 on 2026-10-11:**
  - **D1 — scheduled informational reporting.** The harness has no regression threshold (`infrastructure.md:134`), and QEMU TCG has substantial run-to-run variance. A real performance-regression merge gate therefore needs a separate calibrated-baseline decision. This task implements measurements now rather than leaving an unspecified PR-gating option or a "not now" outcome. The harness exits 0 on success, 1 on environmental failure, 2 on argument errors and refuses to overwrite a report.
  - **D2 — classic branch-protection JSON.** Preserve the live mechanism instead of migrating it merely to gain a reviewable artifact. The plan's ruleset/Terraform examples are alternatives, not evidence that a ruleset already exists. Administrative application stays local and explicit; CI receives no privileged token.
  - **D3 — record the choices before Acceptance.** ADR-0040 carried these choices while Proposed; the maintainer has now Accepted them. Substantive `infrastructure.md` changes follow the Accepted ADR through [`propose-standard-change`](../../../../.agents/skills/propose-standard-change/SKILL.md); a standard edit cannot replace ADR governance.
- **Location re-verification (2026-10-11, HEAD `400dec0`):** `ci.yml:7-9`, `ci.md:85-91`, `infrastructure.md:114,134,131,186,104` and `perf-harness.sh` exit codes were re-checked and match; nothing drifted. `phase-b2.md` line numbers shift as banners are added, so locate its items by headline.
- Sequencing: after [T-034](T-034-ci-qemu-smoke-job.md) and [T-036](T-036-ci-arm64-host-check-job.md), so the committed protection definition includes both remote-green checks. The plan item defers the schedule until the smoke job lands.
- **Schedule semantics:** [GitHub's event reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) documents possible delays/dropped scheduled runs and public-repository inactivity disabling; weekly reporting is recurring evidence, not an execution-time guarantee.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Draft |
| 2026-10-11 | Codex (AI agent) | Preflight contract review: see [review artifact](../../reviews/code-reviews/2026-10-11-phase-b2-track1-preflight.md); documentation corrected, implementation not started; ADR-0040 remains Proposed. |
| 2026-10-11 | @cemililik; Codex recorded the decision | ADR-0040 Accepted after the [approval follow-up](../../reviews/code-reviews/2026-10-11-adr-0040-approval-follow-up.md); design choices settled, status Ready. Implementation and hosted evidence remain pending. |
| 2026-10-12 | Codex (AI agent) | Step 8 implementation: separate weekly Monday03:17UTC/dispatch/targeted-development performance workflow, 20 debug iterations, SHA/Rust/QEMU/run/wall metadata, pipefail and always-uploaded14-day artifacts. Versioned six-check classic policy includes REST settings, GraphQL-only review/deployment/actor baseline and empty rulesets. Local export/check/full read-back match; explicit apply returned no-op, no live write needed. Offline tests cover additive-only PATCH, drift before/after, green proof, CI refusal, unknown/unrepresentable policy and transport credential redaction; 27 tests pass normally and with Python optimization. Six synthetic performance controls pass, including report preservation and pipeline rejection. No CI admin credential or new dependency. |
| 2026-10-12 | Codex (AI agent) | Real local QEMU11.1.1 debug measurement: 20/20 valid, zero failed, 100 s harness wall; p10/p50/p90 =4.085/4.210/4.505 ms. [Immutable local report](../../reports/perf-baseline-2026-10-12-t035-local-check.md) identifies HEAD69ac515 and dirty tracked worktree: this is pre-commit local evidence, not hosted/clean-source certification. Final metadata failure-path adjustment is covered by synthetic controls; no timing algorithm changed. fmt, host/kernel clippy and366 host tests pass; actionlint/ShellCheck/link/whitespace gates passed. First hosted performance artifact, both fresh rounds, final PR and post-merge dispatch remain pending. |
| 2026-10-12 | Codex (AI agent) | First hosted development CI [38186988733](https://github.com/HodeTech/Tyrne/actions/runs/38186988733) passed all seven jobs at source `e8739957ea0a2ceabb33fa7519cadb1a1d2be57e`. Separate [performance run 38186988714 / job 114611329672](https://github.com/HodeTech/Tyrne/actions/runs/38186988714/job/114611329672) passed: downloaded report has 20 valid/zero failed samples, clean full SHA, pinned Rust 1.94.0-nightly, QEMU8.2.2 Linux x86_64 and p10/p50/p90 8.409/9.120/12.622 ms. Harness101 s, evidence139 s, full job144 s (API seconds). [Exact-byte hosted report snapshot](../../reports/perf-baseline-2026-10-12-t035-hosted-check.md) retained independently of 14-day artifact expiry. Service artifact11719932471, 4180 bytes, service-reported SHA256 `c6d1d5a59141638093ec9ddcb9af0531022ad77830a904625fddf7f1c2f75f86`; archive digest was not independently recomputed. Manual dispatch/default-branch schedule and first merged main remain pending until maintainer merge. |
| 2026-10-12 | Fresh independent code/security reviewers; Codex reconciled | R1 code Request changes for inherited Medium T-036 diagnostic race R1-CODE-01; scoped T-035 security Approve with no new actionable finding. Both full reports read and published in [code](../../reviews/code-reviews/2026-10-12-t035-ci-hygiene-tail.md) and [security](../../reviews/security-reviews/2026-10-12-t035-ci-hygiene-tail.md). Verified correction keeps exact compiler command/private mutation, requires101 plus either exact observed diagnostic, and adds nine permanent offline tests. Normal/-O controls and actual Apple ARM rejection pass; fixture rejects old single-diagnostic assertion. Corrected hosted proof and fresh R2 whole combined delta pending. |
| 2026-10-12 | Fresh independent Round2 code/security reviewers; Codex reconciled | Both Approve the whole `69ac515..7deb16e` delta, zero new actionable finding; R1-CODE-01 resolved. Full reports read and appended to the [code](../../reviews/code-reviews/2026-10-12-t035-ci-hygiene-tail.md) and [security](../../reviews/security-reviews/2026-10-12-t035-ci-hygiene-tail.md) artifacts. Corrected [CI38187736985 / ARM114613632255](https://github.com/HodeTech/Tyrne/actions/runs/38187736985/job/114613632255) passes all seven jobs; actual native Linux ARM probe exercises101/unwind class, native/Miri each366pass/two ignored. ARM job96s, probe7s, setup18s/Miri57s. Downloaded current-SHA smoke artifact11720437310 has clean provenance, both correct production profiles and23/23 passed controls (20 synthetic, three actual private kernels), wall97s; service archive digest is reported, not locally recomputed. Performance remains source-bound to e873995 with identical workflow/harness bytes. Tasks stay In Review; integrated entry-doc update and final PR are next, first-main/dispatch merge-dependent. |
