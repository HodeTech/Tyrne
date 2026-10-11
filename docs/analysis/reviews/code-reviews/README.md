# Code reviews

Per-change code quality review: correctness, style, test coverage, documentation. One artifact per non-trivial change, so "has this been reviewed?" is answerable from the repo.

## When to conduct

- **Every PR / non-trivial change** once the project has moved past the bootstrap phase and PRs become routine.
- **Not for trivial changes.** A typo fix, a single-line comment update, or a formatter-only diff does not require a code-review artifact. The line is judgement — if you would pause at the PR to think about it, produce a review.
- **During the solo phase,** the maintainer performs code-review passes on their own work. The artifact exists so that future-maintainer or a contributor arriving later can see the review trail.

## What this review produces

A dated file `YYYY-MM-DD-<context>.md` in this folder, following the shape in [`master-plan.md`](master-plan.md). Sections: correctness, style, test coverage, documentation, verdict.

## Relationship to the `perform-code-review` skill

[`perform-code-review`](../../../../.agents/skills/perform-code-review/SKILL.md) describes how to **conduct** the review during development. This folder holds the resulting artifact.

For security-sensitive changes, a code review is **not** sufficient — a security review (in [`../security-reviews/`](../security-reviews/)) is additionally required. The code-review artifact notes which security reviews are expected or already produced.

## Index

| Date | Scope | File |
|------|-------|------|
| 2026-04-21 | Tyrne project → Phase A exit (Phase 1–4c bootstrap + A1–A6 kernel core) | [2026-04-21-tyrne-to-phase-a.md](2026-04-21-tyrne-to-phase-a.md) |
| 2026-05-06 | Full-tree comprehensive (Phase A + B0 + B1, multi-agent) at `214052d` — Verdict: Request changes (7 blocker-class doc drift items; all other tracks Approve/Comment/Iterate) | [2026-05-06-full-tree-comprehensive.md](2026-05-06-full-tree-comprehensive.md) (with sub-artefacts under [`2026-05-06-full-tree/`](2026-05-06-full-tree/)) |
| 2026-05-07 | PR #12–#17 multi-axis post-merge sweep (T-014 hotfix + α/β/γ/δ + T-015), 8-axis fan-out across `298b5d2a..8dc433ee` — Verdict: Approve, 7 Minor follow-ups for a hygiene PR before ADR-0027 drafting; 1 Major forward-flagged for ADR-0030 / ADR-0019; zero Blockers | [2026-05-07-pr-12-to-17-multi-axis-review.md](2026-05-07-pr-12-to-17-multi-axis-review.md) (with sub-artefacts under [`2026-05-07-pr-12-to-17-multi-axis-review/`](2026-05-07-pr-12-to-17-multi-axis-review/)) |
| 2026-05-08 | PR #19 / #20 / #21 multi-axis pre-merge sweep (path-drift sweep + ADR-0027/T-016 open + P10 perf-harness baseline), 4-track fan-out — Verdict: Approve all three; one same-branch fix on #20 (`phase-b.md` §B2 status block stale `Proposed`); 3 Track-2 Majors flow to T-016 / hygiene PR (escape-hatch doc, MMU-instance binding rationale, ADR-0034 placeholder for kernel-image section permissions); zero Blockers | [2026-05-08-pr-19-20-21-multi-axis-review.md](2026-05-08-pr-19-20-21-multi-axis-review.md) (with sub-artefacts under [`2026-05-08-pr-19-20-21-multi-axis-review/`](2026-05-08-pr-19-20-21-multi-axis-review/)) |
| 2026-10-11 | Phase B.2 Track B.2-1 preflight: CI/task/governance contracts, proposed execution policy; maintainer Acceptance pending | [2026-10-11-phase-b2-track1-preflight.md](2026-10-11-phase-b2-track1-preflight.md) |
| 2026-10-11 | ADR-0040 independent approval follow-up: supplied findings reconciled, ledger and coverage-label corrections verified, pinned-nightly baseline reproduced — ready for Acceptance; implementation pending | [2026-10-11-adr-0040-approval-follow-up.md](2026-10-11-adr-0040-approval-follow-up.md) |
| 2026-10-12 | T-037 target boundary: both fresh code/security rounds Approve scoped delta; round 2 on `960bdef..69a4109` verifies two Low fixes, no new findings; existing HIGH T-038 excluded; final PR and maintainer review pending | [2026-10-12-t037-target-boundary.md](2026-10-12-t037-target-boundary.md) |
| 2026-10-12 | T-033 QEMU tooling: both fresh code/integration rounds Approve; round 2 at `eede01c` found Low R2-INT-01 (completion spins, not WFI), verified and corrected; final maintainer review pending | [2026-10-12-t033-qemu-tooling.md](2026-10-12-t033-qemu-tooling.md) |
| 2026-10-12 | T-031 lint gates: both fresh code/integration rounds Approve; Low R1-CODE-01 and R2-CODE-01 verified and fixed; hosted CI green; final maintainer PR review pending | [2026-10-12-t031-lint-gates.md](2026-10-12-t031-lint-gates.md) |
| 2026-10-12 | T-030 release gates: both fresh code/security rounds Approve, no new finding; local/hosted gates and independent real/adversarial checks passed; final maintainer PR pending | [2026-10-12-t030-release-gates.md](2026-10-12-t030-release-gates.md) |
| 2026-10-12 | T-032 panic-family denies: both fresh code/security rounds Approve, no new finding; changed UNSAFE-2026-0025 reasoning explicitly approved; final maintainer PR pending | [2026-10-12-t032-panic-family-denies.md](2026-10-12-t032-panic-family-denies.md) |
| 2026-10-12 | T-034 QEMU EL0 smoke, both fresh rounds complete: R1 HIGH pipeline masking fixed locally/hosted; R2 code/security Approve, no new finding; live registration/final PR pending | [2026-10-12-t034-qemu-smoke.md](2026-10-12-t034-qemu-smoke.md) |
