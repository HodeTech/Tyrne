# Tasks

Individual task user stories, organized per phase. Each task is a short markdown document following the shape in [`TEMPLATE.md`](TEMPLATE.md).

## Layout

```text
tasks/
├── README.md        — this file
├── TEMPLATE.md      — user-story template
├── phase-a/         — Phase A tasks
│   ├── README.md    — phase-local task index
│   └── T-NNN-<slug>.md
├── phase-b/
├── phase-b2/        — bridge Phase B.2 (dotted phase ID; ADR-0040)
├── phase-c/
└── … (one folder per phase)
```

Task IDs (`T-NNN`) are sequential **across the whole project**, not restarted per phase. The phase folder structure is for reading convenience, not for namespacing IDs.

**Phase B.2 Track B.2-1 (2026-10-12):** The [approved eight-step sequence](phase-b2/README.md) is merged in [PR #48](https://github.com/HodeTech/Tyrne/pull/48), including optional T-036 and prerequisite T-037. T-030–T-037 are Done with date_done 2026-10-12 and explicit maintainer authorization. Each step has two fresh rounds and verified corrections; first-main CI and default-branch performance dispatch passed. The [post-merge retrospective](../reviews/business-reviews/2026-10-12-phase-b2-track1-completion.md) records completion and remaining scope. Phase B.2 stays Active with 38 tasks remaining; HIGH T-038 is the next Ready candidate, not started.

**Phase B.2 Track B.2-2 (2026-10-15):** All twelve selected tasks T-045–T-056 are implemented/In Review. The [integrated record](../reports/2026-10-15-phase-b2-track2-completion-readiness.md) traces 58 opening findings and 156 criteria; one maintainer SECURITY wording criterion remains pending. Both integrated review rounds are complete; final publication-tip CI is recorded at handoff in explicitly authorized combined [PR #49](https://github.com/HodeTech/Tyrne/pull/49). The phase has 8 Done/12 In Review/26 unimplemented tasks; next implementation is HIGH T-038, Ready and unstarted. Only maintainer-approved review/merge permits Done.

## Status vocabulary

| Status | Meaning |
|--------|---------|
| `Draft` | Exists but criteria are not settled. |
| `Ready` | Criteria settled; dependencies resolved; ready to be picked up. |
| `In Progress` | Actively being worked on. Reflected in [`../../roadmap/current.md`](../../roadmap/current.md). |
| `In Review` | Code / docs landed; awaiting maintainer review. |
| `Done` | Merged and reviewed; acceptance criteria met. |
| `Blocked` | Cannot proceed; reason documented inline. |
| `Superseded` | Replaced; link forward to the replacement(s). |

Status transitions are author-driven. Only the maintainer authorizes `Done`.

## Lifecycle

1. **Create** the task with the [`start-task`](../../../.agents/skills/start-task/SKILL.md) skill. It copies [`TEMPLATE.md`](TEMPLATE.md) into the right phase folder and assigns the next T-NNN.
2. **Move to `In Progress`** when work begins. Update [`../../roadmap/current.md`](../../roadmap/current.md) to point at the task.
3. **Work the acceptance criteria.** Any ADRs listed as dependencies are written (via `write-adr`) before implementation code lands.
4. **Move to `In Review`** when all criteria appear satisfied. The maintainer's review confirms.
5. **Move to `Done`** after maintainer-authorized review/merge. Insert the optional `- **date_done:** YYYY-MM-DD` immediately after `Created`, using the real ISO completion date. Omit it while open; do not fabricate historical dates. Update `current.md`; if it was the last task of the milestone, trigger a business review via [`conduct-review`](../../../.agents/skills/conduct-review/SKILL.md).

## Conventions

- Filename: `T-NNN-<kebab-slug>.md`, where `<slug>` is an imperative-verb phrase (`capability-table-foundation`, `el-drop-to-el1`).
- Exactly one task per file.
- Required frontmatter fields are always present — no placeholder values left over from the template. The optional `date_done` follows the lifecycle rule above.
- Acceptance criteria are concrete and testable (3–8 items; at most 10, or split the task).
- If a task has open design decisions, they become ADR acceptance criteria on the task.

See [ADR-0013](../../decisions/0013-roadmap-and-planning.md) for the full planning-process rules.
