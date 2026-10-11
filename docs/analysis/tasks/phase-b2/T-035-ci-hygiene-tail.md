# T-035 — Track and land the CI hygiene tail (perf-harness schedule, merge gates as code)

- **Phase:** B.2
- **Milestone:** Track B.2-1
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-034](T-034-ci-qemu-smoke-job.md), [T-036](T-036-ci-arm64-host-check-job.md)
- **Informs:** none
- **ADRs required:** ADR-0040 (Accepted), including its Track B.2-1 implementation policy

---

## User story

As the maintainer, I want an explicit, recorded decision on whether the performance harness runs on a schedule in CI and whether the merge-gate configuration is kept as reviewable code, so that two low-priority gaps are either closed or consciously accepted instead of drifting as trusted-by-comment.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) as a decision-bearing task. The Accepted Track B.2-1 policy chooses implementation of both items; recording those choices alone does not satisfy the remaining implementation and evidence criteria. `tools/perf-harness.sh` is the canonical source for boot-to-end timing claims but no CI job runs it (`docs/standards/infrastructure.md:114` says "Maintainer-launched only; not yet wired into CI"), so there is no automated performance signal. Separately, "what gates merge" is stated only in the `ci.yml` header comment (`.github/workflows/ci.yml:7-9`) and prose (`docs/guides/ci.md:85-91`, `infrastructure.md:186`); the actual required-checks list is a GitHub setting that no diff can review.

This task covers two items of `phase-b2.md` Track B.2-1 (line numbers as of the opening snapshot; locate by headline): LOW "`tools/perf-harness.sh` is likewise never invoked by CI" (line 51) and INFO "'What gates merge' is documented only in comments, not verifiable as code" (line 60). The track's acceptance criteria explicitly allow these low/info tails to be tracked without all landing in B.2, and the phase's closing note requires a scheduled-versus-gated CI choice to be routed through ADR governance rather than decided inside the backlog.

## Acceptance criteria

- [x] Decision D1 is Accepted in ADR-0040 before implementation: weekly Monday `03:17 UTC` plus `workflow_dispatch`, informational, with a `development` push trigger limited to changes to the performance workflow or harness for pre-merge validation.
- [x] Decision D2 is Accepted in ADR-0040 before implementation: version the existing classic `main` branch protection as JSON, with read-only export/check and explicit local apply tooling; no Terraform or ruleset migration.
- [ ] The performance workflow builds the debug userland and kernel, runs `tools/perf-harness.sh --iterations=20 --report=ci-nightly`, and uploads the report with SHA/toolchain/QEMU metadata. Its first hosted `development` run is green and the downloaded artifact contents and wall time are recorded. Verify the manual dispatch after default-branch registration; do not claim it happened before merge. The job is not a required check.
- [ ] The committed branch-protection definition preserves every existing setting and the GitHub Actions application bindings, includes the remote-green smoke and ARM checks, and has documented export, diff/check and apply commands. A read-back comparison against the live settings is clean; unexpected drift stops apply until reconciled. No administrative secret is available to CI.
- [ ] Documentation: `docs/guides/ci.md` and `docs/standards/infrastructure.md` (including the line-114 sentence in the performance-harness section and the "Planned gates" list) match the decisions taken; the `ci.yml` header comment (lines 7-9) is still accurate. Explain that GitHub schedules are best effort, run from the default branch, and are automatically disabled after 60 days without repository activity in public repositories; document how to re-enable/dispatch the workflow.

## Out of scope

- The merge-gating smoke job itself: [T-034](T-034-ci-qemu-smoke-job.md) (this task depends on it landing first, as the plan item says).
- A regression-detecting harness mode (a `--baseline` option taking a previous report file), which `infrastructure.md:134` marks as not in scope for v1.
- Release-profile and `perf-bench` build gates: [T-030](T-030-ci-release-profile-gate.md).
- An arm64 host-check job: [T-036](T-036-ci-arm64-host-check-job.md).

## Approach

Implement ADR-0040's Accepted D1-D3 policy. Use a separate performance workflow to keep measurements off the required PR pipeline; follow the repo's SHA pinning and least-privilege conventions, build the userland image before the kernel, and archive the report. Read-only inspection on 2026-10-11 found `gh api repos/HodeTech/Tyrne/rulesets` empty and `main` protected by classic branch protection. Export that existing mechanism through `gh api repos/HodeTech/Tyrne/branches/main/protection`; normalise response-only metadata separately from the apply payload, preserve all policy fields, and fail closed on settings the tooling cannot represent. Test drift detection and apply preconditions against local fixtures before any live mutation. Apply only after the new required checks have succeeded remotely, then read back and compare.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes.
- [ ] Every touched markdown file has all `](...)` link targets resolving.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

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
