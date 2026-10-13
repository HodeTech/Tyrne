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

The ADR-0040 approval follow-up in this index is explicitly an independent approval artifact. It uses the dedicated `conduct-approval-review` template; its inclusion here does not convert it to a code review.

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
| 2026-10-12 | T-034 QEMU EL0 smoke, both fresh rounds complete: R1 HIGH pipeline masking fixed locally/hosted; R2 code/security Approve, no new finding; live registration read-back recorded; final PR pending | [2026-10-12-t034-qemu-smoke.md](2026-10-12-t034-qemu-smoke.md) |
| 2026-10-12 | T-036 native ARM CI: both fresh code/integration rounds Approve; duplicate Low enforcement wording fixed, no new R2 finding; hosted proof green; live registration/full-policy read-back complete; later diagnostic-race finding and fix reviewed with T-035, final PR pending | [2026-10-12-t036-native-arm-ci.md](2026-10-12-t036-native-arm-ci.md) |
| 2026-10-12 | T-035 weekly performance/full classic protection plus late T-036 correction: both fresh rounds complete; R1 inherited Medium fixed, R2 code/security Approve whole combined delta, corrected hosted evidence green; final maintainer PR pending | [2026-10-12-t035-ci-hygiene-tail.md](2026-10-12-t035-ci-hygiene-tail.md) |
| 2026-10-12 | Final Track B.2-1 six-entry documentation reconciliation: fresh independent Approve; one Low baseline-tense correction verified, all eight tasks In Review; final maintainer PR/merge evidence separate | [2026-10-12-phase-b2-track1-final-docs.md](2026-10-12-phase-b2-track1-final-docs.md) |
| 2026-10-12 | PR48 follow-up A, fresh R1 at `50ab72b`: code Approve; shared Low R1-SEC-01 corrected in publication, fresh R2 pending | [2026-10-12-pr48-tools-followup-r1.md](2026-10-12-pr48-tools-followup-r1.md) |
| 2026-10-12 | PR48 follow-up A, fresh R2 cumulative `1e281ac..683965b`: Approve, zero new findings, R1 Low resolved; both A rounds complete, B pending | [2026-10-12-pr48-tools-followup-r2.md](2026-10-12-pr48-tools-followup-r2.md) |
| 2026-10-12 | PR48 follow-up B, fresh R1 at `5816c93`: code Approve, two Low prose findings corrected by coordinator; cumulative R2 pending | [2026-10-12-pr48-docs-followup-r1.md](2026-10-12-pr48-docs-followup-r1.md) |
| 2026-10-12 | PR48 follow-up B, distinct fresh R1 integration: Approve, same two Low findings, full peer cross-read | [2026-10-12-pr48-docs-integration-r1.md](2026-10-12-pr48-docs-integration-r1.md) |
| 2026-10-12 | PR48 follow-up B, fresh R2 cumulative `a1eb406..646ba33`: code Approve, zero new findings, both R1 Low corrections verified; both B rounds complete | [2026-10-12-pr48-docs-followup-r2.md](2026-10-12-pr48-docs-followup-r2.md) |
| 2026-10-12 | PR48 follow-up B, distinct fresh R2 integration: Approve same cumulative source, zero new findings, both R1 corrections verified and full peer cross-read | [2026-10-12-pr48-docs-integration-r2.md](2026-10-12-pr48-docs-integration-r2.md) |
| 2026-10-12 | Track B.2-2 preflight/proposals: initial two rounds plus two fresh supplied-review follow-up rounds; Low findings corrected and independently verified, zero unresolved proposal blockers; copyright resolved, explicit ADR/plan approval and implementation pending | [2026-10-12-phase-b2-track2-preflight.md](2026-10-12-phase-b2-track2-preflight.md) |
| 2026-10-12 | Track B.2-2 Step 0 Acceptance/contracts: both fresh rounds Approve corrected cumulative source, duplicated T-055 conflict and backlink finding resolved; preparation only, T-051 next | [2026-10-12-phase-b2-track2-step0.md](2026-10-12-phase-b2-track2-step0.md) |
| 2026-10-13 | T-051 contribution/security status: both fresh code rounds and subsequent distinct security passes Approve, zero findings; In Review, maintainer SECURITY wording review before merge | [2026-10-13-t051-contribution-security-status.md](2026-10-13-t051-contribution-security-status.md) |
| 2026-10-13 | T-045 architecture entry points, both fresh rounds; three R1 findings corrected in `deec107`, no new R2 finding; T-046 coherence recheck next | [2026-10-13-t045-architecture-entry-points.md](2026-10-13-t045-architecture-entry-points.md) |
| 2026-10-13 | T-046 seven whole subsystem chapters and T-045 shared coherence; six R1 findings fixed in `4b33607`, no new R2 finding | [2026-10-13-t046-subsystem-architecture.md](2026-10-13-t046-subsystem-architecture.md) |
| 2026-10-13 | T-048 historical Phase B task reconciliation; both fresh rounds Approve, one R1 Low provenance correction verified at `a50f94a`; no new B.2 Done or runtime claim | [2026-10-13-t048-phase-b-task-reconciliation.md](2026-10-13-t048-phase-b-task-reconciliation.md) |
| 2026-10-13 | T-049 review discovery, immutable historical navigation and fresh Miri/coverage; both fresh rounds complete, Low C01 corrected and verified, no unresolved finding | [2026-10-13-t049-review-corpus-reconciliation.md](2026-10-13-t049-review-corpus-reconciliation.md) |
| 2026-10-13 | T-050 entry documents, guides/glossary/skills and copyright; both fresh code/security rounds Approve, one Low in each corrected and verified, zero unresolved delta findings | [2026-10-13-t050-entry-document-refresh.md](2026-10-13-t050-entry-document-refresh.md) |
| 2026-10-13 | T-055 append-only ADR/source/index/procedure corrections; both fresh code/security rounds Approve, two unique R1 Low findings fixed and verified, zero new R2 or unresolved findings | [2026-10-13-t055-adr-corrections.md](2026-10-13-t055-adr-corrections.md) |
| 2026-10-13 | T-052/T-053 standards and source/tooling reconciliation; both fresh paired rounds, zero source/seam findings | [2026-10-13-t052-t053-standards-reconciliation.md](2026-10-13-t052-t053-standards-reconciliation.md) |
| 2026-10-13 | T-054 stable planned ADR identities; both fresh paired rounds Approve, one unique R1 Low fixed and verified, zero new R2 or unresolved findings | [2026-10-13-t054-planned-adr-identities.md](2026-10-13-t054-planned-adr-identities.md) |
| 2026-10-13 | T-047 roadmap live/archive/B6/Phase-C reconciliation — both fresh paired rounds; zero source findings | [2026-10-13-t047-roadmap-state-reconciliation.md](2026-10-13-t047-roadmap-state-reconciliation.md) |

## Companion plans

Companion plans describe review execution; they do not supply independent verdicts.

- [May-6 full-tree comprehensive review plan](2026-05-06-full-tree-comprehensive-review-plan.md), owned by the [May-6 canonical review](2026-05-06-full-tree-comprehensive.md). The canonical review links its preflight and Tracks A–J; the May-7 and May-8 canonical reviews likewise link their nested tracks.
