# T-035 — Track and land the CI hygiene tail (perf-harness schedule, merge gates as code)

- **Phase:** B.2
- **Milestone:** Track B.2-1
- **Status:** Draft
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-034](T-034-ci-qemu-smoke-job.md)
- **Informs:** none
- **ADRs required:** possibly an ADR or revision-note rider (see Design notes -> Open decisions)

---

## User story

As the maintainer, I want an explicit, recorded decision on whether the performance harness runs on a schedule in CI and whether the merge-gate configuration is kept as reviewable code, so that two low-priority gaps are either closed or consciously accepted instead of drifting as trusted-by-comment.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), which classes this as a "decide and record" task: it satisfies the Phase B.2 exit by recording the decisions, not necessarily by implementing both. `tools/perf-harness.sh` is the canonical source for boot-to-end timing claims but no CI job runs it (`docs/standards/infrastructure.md:114` says "Maintainer-launched only; not yet wired into CI"), so there is no automated performance signal. Separately, "what gates merge" is stated only in the `ci.yml` header comment (`.github/workflows/ci.yml:7-9`) and prose (`docs/guides/ci.md:85-91`, `infrastructure.md:186`); the actual required-checks list is a GitHub UI setting that no diff can review.

This task covers two items of `phase-b2.md` Track B.2-1 (line numbers as of the opening snapshot; locate by headline): LOW "`tools/perf-harness.sh` is likewise never invoked by CI" (line 51) and INFO "'What gates merge' is documented only in comments, not verifiable as code" (line 60). The track's acceptance criteria explicitly allow these low/info tails to be tracked without all landing in B.2, and the phase's closing note requires a scheduled-versus-gated CI choice to be routed through ADR governance rather than decided inside the backlog.

## Acceptance criteria

- [ ] Decision D1 (perf-harness in CI) is recorded before any implementation, in the venue chosen under D3, and linked from the review history; if the answer is "not now", it is recorded under "Planned gates" in `docs/standards/infrastructure.md` instead.
- [ ] Decision D2 (merge gates as code) is recorded the same way before any implementation.
- [ ] If D1 chose a scheduled run: a workflow with `schedule` and `workflow_dispatch` triggers builds the kernel, runs `tools/perf-harness.sh --iterations=20 --report=ci-nightly`, and uploads the output as an artifact; one manual `workflow_dispatch` run is green and its artifact contents are recorded; the job is not added to the required checks.
- [ ] If D2 chose to implement: the chosen artefact (committed ruleset definition or Terraform) is in the repo with documented export, diff and apply commands, and a diff of the live settings against it is recorded as clean; otherwise "not now" is recorded.
- [ ] Documentation: `docs/guides/ci.md` and `docs/standards/infrastructure.md` (including the line-114 sentence in the performance-harness section and the "Planned gates" list) match the decisions taken; the `ci.yml` header comment (lines 7-9) is still accurate.

## Out of scope

- The merge-gating smoke job itself: [T-034](T-034-ci-qemu-smoke-job.md) (this task depends on it landing first, as the plan item says).
- A regression-detecting harness mode (a `--baseline` option taking a previous report file), which `infrastructure.md:134` marks as not in scope for v1.
- Release-profile and `perf-bench` build gates: [T-030](T-030-ci-release-profile-gate.md).
- An arm64 host-check job: [T-036](T-036-ci-arm64-host-check-job.md).

## Approach

First settle D1 to D3 with the maintainer, recording each. Then implement only what was chosen. For a scheduled harness run, a separate workflow file is the simplest way to keep `schedule:` off the PR pipeline (`ci.yml` triggers on push and pull_request, lines 29-33); it must follow the repo conventions (SHA-pinned actions, least-privilege `permissions`), build the userland image and the kernel first, and archive the harness report. For merge gates as code, `gh api repos/{owner}/{repo}/rulesets` (named in the plan item) is the starting point for exporting what is configured today.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes.
- [ ] Every touched markdown file has all `](...)` link targets resolving.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040` (plus the new ADR number if D3 produced one).
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions (maintainer):**
  - **D1 — perf-harness in CI.** (a) Scheduled and informational: cron plus `workflow_dispatch`, report archived as an artifact, as the plan item suggests; (b) PR-gated; (c) not now, recorded as a planned gate. Facts bearing on it: the harness has no regression threshold (`infrastructure.md:134`), and QEMU TCG shows about 15-30 % run-to-run variance (`infrastructure.md:131`), so a PR gate would be noisy and could assert nothing; a scheduled job only accumulates data until a `--baseline` mode exists. The harness exits 0 on success, 1 on environmental failure, 2 on argument errors (`perf-harness.sh:38-39`) and refuses to overwrite an existing report.
  - **D2 — merge gates as code.** (a) Not now: keep the UI setting and the documented list; (b) check in a repository-ruleset definition exported with `gh api` and document how to diff and apply it by hand (applying needs an admin credential, and `infrastructure.md:104` says secrets never enter CI, so this stays a manual step); (c) Terraform (`github_branch_protection` / `github_repository_ruleset`), which adds a tool, state and a credential the repo does not have today.
  - **D3 — recording venue.** A new ADR, a revision-note rider on ADR-0040, or a standards change via the [`propose-standard-change`](../../../../.agents/skills/propose-standard-change/SKILL.md) skill (the latter fits an `infrastructure.md` rule). The decision follows [`write-adr`](../../../../.agents/skills/write-adr/SKILL.md) rules if an ADR is chosen.
- **Location re-verification (2026-10-11, HEAD `400dec0`):** `ci.yml:7-9`, `ci.md:85-91`, `infrastructure.md:114,134,131,186,104` and `perf-harness.sh` exit codes were re-checked and match; nothing drifted. `phase-b2.md` line numbers shift as banners are added, so locate its items by headline.
- Sequencing: after [T-034](T-034-ci-qemu-smoke-job.md); the plan item defers the schedule until the smoke job lands.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Draft |
