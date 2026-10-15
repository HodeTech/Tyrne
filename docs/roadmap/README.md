# Tyrne roadmap

The roadmap is **the plan** — what we intend to build and in what order. It answers two questions:

1. **Where are we going?** — [`phases/`](phases/) (Phase A through Phase J, plus the bridge Phase B.2).
2. **Where are we now?** — [`current.md`](current.md).

The plan is separate from the work. Individual tasks and reviews live under [`../analysis/`](../analysis/) and are cross-linked from here. See [ADR-0013](../decisions/0013-roadmap-and-planning.md) for the rationale behind this split.

**Track B.2-1 completion (2026-10-12):** The [eight-step sequence](../analysis/tasks/phase-b2/README.md) is merged in [PR #48](https://github.com/HodeTech/Tyrne/pull/48); T-030–T-037 are Done with maintainer authorization. Both fresh rounds per step and verified fixes are recorded. First-main CI and default-branch performance dispatch passed; the [post-merge retrospective](../analysis/reviews/business-reviews/2026-10-12-phase-b2-track1-completion.md) records the evidence and remaining scope. Next candidate: HIGH T-038 (Ready, not started). The whole Phase B.2 exit bar still gates C and D.

**Track B.2-2 implementation (2026-10-16):** Track B.2-2 / T-045–T-056 is Done after maintainer-authorized [PR49](https://github.com/HodeTech/Tyrne/pull/49) merge and verified first-main gates. The [completion retrospective](../analysis/reviews/business-reviews/2026-10-16-phase-b2-track2-completion.md) records all twelve delivered tasks, 161 checked criteria, completed evidence-retention maintenance and source-bound validation. Phase B.2 has 20 Done / 19 Ready / 7 Draft tasks; 26 remain unimplemented. HIGH T-038 is next, Ready and unstarted. Track B.2-1 remains Done; Phase B.2 stays Active and continues to gate C/D.

## What lives here

| Path | Purpose |
|------|---------|
| [`README.md`](README.md) | This file. |
| [`phases/README.md`](phases/README.md) | Index of phase files with a one-paragraph summary each. |
| [`phases/phase-<id>.md`](phases/) | Detailed breakdown of one phase, with its milestones and acceptance criteria. |
| [`current.md`](current.md) | Short pointer to the active phase, milestone, and task. Updated often. |

## What does **not** live here

- **Individual task user stories** — they live under [`../analysis/tasks/phase-<id>/`](../analysis/tasks/).
- **Reviews** — they live under [`../analysis/reviews/<type>/`](../analysis/reviews/).
- **Design rationale for architectural choices** — [`../decisions/`](../decisions/) (ADRs).
- **Procedural rules** — [`../standards/`](../standards/).
- **Repeatable procedures** — [`../../.agents/skills/`](../../.agents/skills/).

## How to read the roadmap

- **New to the project:** read [`phases/README.md`](phases/README.md), then skim the phase files top-to-bottom. Then look at [`current.md`](current.md) to see where work is.
- **Returning after a pause:** open [`current.md`](current.md) first. It points to the active phase / milestone / task and the date of the last review.
- **Planning the next work session:** [`current.md`](current.md) names the active task; the task file lists its acceptance criteria; the phase file shows what it leads to.

## Conventions

- **Phase IDs** are letters (A, B, C, …), in execution order, stable once published. A **bridge phase** inserted after publication carries a dotted ID so later letters are not renumbered (`B.2`, between B and C; see [ADR-0040](../decisions/0040-phase-b2-consolidation-bridge.md)).
- **Milestone IDs** are `<phase><N>` (A1, A2, …), stable once the milestone becomes active. A bridge phase's sub-units are **Tracks** (`B.2-1` … `B.2-6`), not milestones, so they cannot collide with `B0`–`B6`.
- **Task IDs** (`T-NNN`) are stable across the whole project and live under [`../analysis/tasks/`](../analysis/tasks/).
- **Path IDs** are lowercase without dots: phase C maps to `phase-c` / `phase-c.md`; bridge B.2 maps to `phase-b2` / `phase-b2.md`. The `phase-<id>` templates above cover both.

See [ADR-0013](../decisions/0013-roadmap-and-planning.md) for the full identifier and change-process rules.

## Changing the roadmap

- **Tweaking a phase's milestones or sub-breakdowns** — edit the phase file.
- **Adding or dropping a phase, or reordering phases at the top level** — structural change; requires an ADR that supersedes the affected statements.
- **Opening a new task** — [`start-task`](../../.agents/skills/start-task/SKILL.md) skill.
- **Running a review** — [`conduct-review`](../../.agents/skills/conduct-review/SKILL.md) skill.
