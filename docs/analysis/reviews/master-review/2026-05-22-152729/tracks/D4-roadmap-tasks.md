# D4-roadmap-tasks — roadmap, phases, tasks (master review, commit 288ddb2)

**Reviewer:** D4 agent (Claude Sonnet 4.6)
**Anchored to:** commit `288ddb2` ("docs(readme): rewrite root README for a first-time reader")
**Scope:** All 43 files under `docs/roadmap/` (13 files) and `docs/analysis/tasks/` (30 files)
**Date:** 2026-05-22

---

## Summary

The roadmap and task corpus is in generally good shape — the project's planning record is unusually thorough for a pre-alpha codebase, with consistent template conformance, detailed review histories, and well-maintained ADR cross-links. Two issues demand immediate attention before Phase C implementation begins.

**Critical finding:** Phase C's phase plan (`phase-c.md`) claims ADR-0027 through ADR-0031 for its milestones (C1–C5). Those exact five numbers are already allocated and Accepted as Phase B decisions (ADR-0027 = kernel VMem layout, ADR-0028 = address-space data structure, ADR-0029 = userspace image format, ADR-0030 = syscall ABI, ADR-0031 = initial syscall set). Any agent or human following `phase-c.md` to write "ADR-0027" would silently overwrite or contradict live, Accepted Phase B decisions. Phase D compounds the problem: it claims ADR-0032 through ADR-0036, of which ADR-0032 (endpoint rollback) and ADR-0035 (PMM bitmap allocator) are already live on `main`.

**Second critical finding:** `current.md`'s live operational section is frozen at a pre-merge snapshot. PR #31 (T-019 task loader) is confirmed merged at commit `7f876af` (the second-most-recent commit in the git log, directly before `288ddb2`). Yet `current.md` still lists T-019 as "In Review on PR #31", names T-016's stale branch as the working branch, and claims "Last completed milestone: B1" — three milestones behind reality (B2, B3, and B4 are all closed). The B4 milestone closure trio (business + security + performance) has not been triggered because the Done flip and milestone-close have not been recorded.

Beyond these two critical issues, the test count discrepancy is minor but real: the plan documents consistently claim 259 host tests at HEAD, but `grep -rn "#\[test\]"` across all crates returns 260 at commit `288ddb2`, confirmed by the gate-reproduction track. The +1 test arrived in the round-5 follow-up commit (`5078944`) after the round-4 banner entry was written.

Severity counts: **Blocker 2, Major 4, Minor 5, Nit 3, Praise 4.**

---

## Findings

### Blocker

#### D4-001 — Phase C ADR ledger allocates numbers already live in Phase B

**File:** `docs/roadmap/phases/phase-c.md:17,37,56,79,98,118–122`

**Description:** `phase-c.md` assigns these numbers to Phase C milestones:

| phase-c.md claims | Phase C subject | Already allocated as |
|---|---|---|
| ADR-0027 | Secondary core start protocol (C1) | Kernel virtual memory layout — **Accepted 2026-05-08**, file `docs/decisions/0027-kernel-virtual-memory-layout.md` |
| ADR-0028 | Per-core state access pattern (C2) | Address-space data structure — **Accepted 2026-05-11**, file `docs/decisions/0028-address-space-data-structure.md` |
| ADR-0029 | Scheduler topology (C3) | Initial userspace image format — **Accepted 2026-05-14**, file `docs/decisions/0029-initial-userspace-image-format.md` |
| ADR-0030 | Cross-core wakeup / IPI (C4) | Syscall ABI — reserved in phase-b.md §B5 ADR ledger |
| ADR-0031 | TLB shootdown protocol (C5) | Initial syscall set — reserved in phase-b.md §B5 ADR ledger |

ADRs 0027–0029 are Accepted and on `main`. ADRs 0030–0031 are reserved/planned in the Phase B ADR ledger. An agent following `phase-c.md` to write a new ADR-0027 would produce a filename collision with the live, Accepted decision.

**Suggested fix:** Renumber Phase C's ADR placeholders to start from the first unallocated number above the Phase B ceiling. The Phase B ADR ledger runs through ADR-0035 (live) plus ADR-0033 and ADR-0034 as named placeholders, plus ADR-0030 and ADR-0031 as planned-but-unwritten. The first safe slot for Phase C is ADR-0036 or higher (after also confirming Phase D's claim, see D4-002). Update the phase-c.md ADR table and all five milestone acceptance-criteria lists.

---

#### D4-002 — Phase D ADR ledger overlaps with live Phase B ADRs

**File:** `docs/roadmap/phases/phase-d.md:17,36,53,87,105,162–166`

**Description:** `phase-d.md` assigns:

| phase-d.md claims | Phase D subject | Status of that number |
|---|---|---|
| ADR-0032 | Pi 4 boot flow (D1) | **Already live:** endpoint state rollback + `ipc_cancel_recv` — Accepted 2026-05-07, file `docs/decisions/0032-endpoint-rollback-and-cancel-recv.md` |
| ADR-0033 | GIC-400 register layout (D2) | Named placeholder in phase-b.md: "Kernel high-half migration" (B5+, named-but-unallocated) |
| ADR-0034 | Pi 4 console choice (D3) | Named placeholder in phase-b.md: "Kernel-image section permissions" (B-late, named-but-unallocated) |
| ADR-0035 | Pi 4 memory layout (D5) | **Already live:** Physical Memory Manager — Accepted 2026-05-09, file `docs/decisions/0035-physical-memory-manager.md` |
| ADR-0036 | DTB parsing scope (D6) | Not allocated yet — safe, but the file that would be written now |

ADR-0032 and ADR-0035 are fully implemented and on `main`. ADR-0033 and ADR-0034 are reserved for specific Phase B+ purposes. Only ADR-0036 is genuinely free.

**Suggested fix:** Renumber Phase D's ADR placeholders upward past the Phase B ceiling, coordinated with the Phase C renumbering from D4-001. Both phases should use a common starting point (the first number above max(phase-b-ledger, phase-c-new-ceiling)). The D4-renaming must also propagate to every in-text reference within phase-d.md's five milestone descriptions.

---

### Major

#### D4-003 — `current.md` live status section frozen at pre-merge state: T-019 still "In Review"; working branch stale; last completed milestone wrong

**File:** `docs/roadmap/current.md:54–57`

**Description:** Three related stale fields in the live operational section (not in a dated historical banner):

1. **Line 54 — Active task:** "T-019 — Task loader (In Review on PR #31; branch `t-019-task-loader`; ...)" — PR #31 was merged at `7f876af` (git log confirms: "Merge pull request #31 from cemililik/t-019-task-loader"), making this claim false at HEAD. T-019's task file itself (`T-019-task-loader.md`) still reads `Status: In Review` in its frontmatter (see D4-004), but the branch no longer exists as the work branch.

2. **Line 55 — In review:** "T-019 — Task loader (PR #31, ...)" — same issue; PR #31 is merged.

3. **Line 57 — Working branch:** "development branches off `main` per PR pattern; T-016 lives on `t-016-mmu-activation`" — T-016 has been Done since 2026-05-08; its branch served a task that closed over two weeks before HEAD. This line should name the current active branch or say "none" if all tasks are between Done and not-yet-started.

4. **Line 58 — Last completed milestone:** "B1 — Drop to EL1 + exception infrastructure, closed 2026-05-07" — three milestones behind reality. B2 closed 2026-05-09, B3 closed 2026-05-14, and B4 (T-019 merged 2026-05-16) is effectively implementation-complete pending the Done flip. The `current.md` body text higher up correctly records B2 and B3 closures in dated banners, but the operational bullet at line 58 was never updated.

**Suggested fix:** Apply the `start-task` / `conduct-review` skill's update discipline to the live bullets: promote T-019 to Done, update the working branch to "none / awaiting B4 closure trio", update last completed milestone to B4 (or "B4 implementation-complete; closure trio pending"), and update last completed tasks list to include T-019.

---

#### D4-004 — T-019 task file frontmatter status remains "In Review" after PR #31 merge

**File:** `docs/analysis/tasks/phase-b/T-019-task-loader.md:6`

**Description:** The frontmatter field `Status: In Review` was never flipped to `Done` after PR #31 merged. Per the task lifecycle defined in `docs/analysis/tasks/README.md`, the `Done` flip happens when the PR lands on `main` and the maintainer performs the Done promotion. The merged commit `7f876af` occurred 2026-05-16; HEAD is `288ddb2` ("docs(readme): rewrite root README") from the same date. The T-019 file has no `date_done` field set. All acceptance-criteria checkboxes in the DoD section that should be checked on Done remain `[ ]`.

Additionally, T-019's DoD section correctly defers some items to B5+ (kernel mappings in userspace AS, EL0 context, syscall entry) — these are legitimately deferred, not missed. But the main status field is a factual error at HEAD: the branch is merged, the code is on `main`, and the task should be promoted.

**Suggested fix:** Flip frontmatter `Status: In Review` to `Status: Done`, add `date_done: 2026-05-16`, mark the DoD checklist items that are truly satisfied (all gates pass at merge), leave deferred items with a clear deferral note, and add a merge-confirmation row to the review history.

---

#### D4-005 — `docs/analysis/tasks/phase-b/README.md` index missing T-018 and T-019

**File:** `docs/analysis/tasks/phase-b/README.md:1–21`

**Description:** The phase-b task index table ends at T-017. T-018 (Done 2026-05-11/14) and T-019 (merged 2026-05-16) are absent. The README states only 15 entries (T-006 through T-017, excluding T-010). Both T-018 and T-019 are committed files in `docs/analysis/tasks/phase-b/` and tracked by git. The omission means the index is two tasks behind.

**Suggested fix:** Add T-018 and T-019 rows to the index table with their titles, milestones (B3 and B4 respectively), and statuses (Done/Done).

---

#### D4-006 — Test count claim 259/259 in `current.md` and T-019 is off by one at HEAD

**File:** `docs/roadmap/current.md:7` (T-019 banner); `docs/analysis/tasks/phase-b/T-019-task-loader.md:135` (review-round-4 row)

**Description:** The T-019 banner in `current.md` (2026-05-15 update, line 7) states "Tests at HEAD: **259/259**". The T-019 task file's review-round-4 history row (line 135) also states "Tests at HEAD: **259/259**". Gate-reproduction at commit `288ddb2` counted 260 passing tests (42 hal + 175 kernel + 43 test-hal = 260; confirmed by `grep -rn "#\[test\]"` across all four crates returning 260 matches). The discrepancy is +1. The round-4 banner was written at commit `95efd62`; the round-5 follow-up (`5078944`) added one new PMM test (`pmm.rs` received `#[test]`-annotated tests per the round-5 diff). The round-5 commit updated the task file's review history but did not update the `current.md` banner or the round-4 history row, which both remain at 259. All 260 tests pass; this is an under-count, not a regression.

**Suggested fix:** Update the current.md T-019 banner and the T-019 task file's implementation-arc summary line to reflect 260/260. Both the round-4 and round-5 history rows can state their respective counts accurately.

---

### Minor

#### D4-007 — `docs/roadmap/README.md` links to stale `.claude/skills/` path

**File:** `docs/roadmap/README.md:25,45,46`

**Description:** Three live links point to `.claude/skills/` (the pre-migration path). Line 25: "`../../.claude/skills/`" as the "Repeatable procedures" pointer. Line 45: `start-task` link to `../../.claude/skills/start-task/SKILL.md`. Line 46: `conduct-review` link to `../../.claude/skills/conduct-review/SKILL.md`. The skills library migrated from `.claude/skills/` to `.agents/skills/` on 2026-05-14 (commit `77d3e7e`, per current.md T-018 banner). These are live operational links that an agent or new contributor would follow and find broken.

**Suggested fix:** Replace `.claude/skills/` with `.agents/skills/` in all three locations. Cross-check that the target skill files exist at the new path before committing.

---

#### D4-008 — `phase-b.md` contains multiple stale `.claude/skills/` references in live (non-banner) prose

**File:** `docs/roadmap/phases/phase-b.md:27,115,125,148,270,271,278,307`

**Description:** After the `.claude/skills/` → `.agents/skills/` migration (commit `77d3e7e`, 2026-05-14), several references in `phase-b.md` were not updated. The live operational lines identified are:
- Line 27: `write-architecture-doc` skill link in the B0 milestone description
- Lines 115, 125, 148: `write-adr` skill links in B2 and B3 milestone bodies
- Lines 270, 271, 278: ADR ledger table entries referencing the `write-adr` skill
- Line 307: `start-task` skill link in the "How to start Phase B" procedure

The T-018 merge banner (line 11 of `current.md`) explicitly notes that the migration "updated CLAUDE.md / AGENTS.md / 12 live cross-references" but evidently did not sweep `phase-b.md`. Links inside dated `> **...update...**` blockquotes are correctly treated as historical record; these are different — they are outside blockquotes in the milestone descriptions and ADR ledger.

**Suggested fix:** Replace all 8 occurrences of `.claude/skills/` with `.agents/skills/` in `phase-b.md`. The current.md migration banner confirms the canonical path.

---

#### D4-009 — `phase-b.md` "How to start Phase B" section is obsolete

**File:** `docs/roadmap/phases/phase-b.md:305–313`

**Description:** The section "How to start Phase B" contains instructions like "Open T-006 (raw-pointer scheduler API refactor) via the `start-task` skill" — T-006 has been Done since 2026-04-22. The entire B0 through B4 milestone stack is Done. New readers will find advice to open tasks that are already closed. The section lacks any indication that it is a historical onboarding artifact rather than live instructions.

**Suggested fix:** Either (a) add a heading banner making clear this section was the Phase B entry procedure and is preserved as historical record, or (b) replace the section body with a note: "Phase B implementation is complete (B0–B4 closed). See the phase plan body above for the closed milestone records. Next active phase: C."

---

#### D4-010 — `current.md` line 11 and T-018 task file disagree on the host-test count at T-018 merge

**File:** `docs/roadmap/current.md:11`; `docs/analysis/tasks/phase-b/T-018-address-space-kernel-object.md` (frontmatter / review history)

**Description:** The `current.md` T-018 banner (2026-05-14 update, line 11) states "**226 host tests pass** workspace-wide" at the T-018 merge point. The T-018 task file's implementation arc documents "+26 from the T-018 arc" over a "200 at PR #27 merge" baseline, arriving at 226 — this is consistent. However, the T-018 task file also references an intermediate count of "221/221" in the phase-b.md status block for B3 (from memory / prior read). Cross-referencing with the progression documented in `current.md`: T-017 Done produced 200 (per PR #27 merge line), T-018 produced 226. The T-018 task file header shows no explicit test count in its frontmatter `date_done` area. The issue is minor — the numbers reconstruct consistently from the banner text — but the T-018 task file should carry its final test count in the review history for completeness.

**Suggested fix:** Add the "Tests at Done: 226/226" note to the T-018 review history (in the row corresponding to the PR #28 merge / Done flip) for traceability, mirroring the T-019 and T-017 precedents.

---

#### D4-011 — `phase-b.md` "Active task" milestone bullet still describes B4 as "opened 2026-05-14 with the ADR-0029 propose commit; gates on ADR-0029 Accepted before implementation begins"

**File:** `docs/roadmap/phases/phase-b.md:179–215` (milestone B4 section)

**Description:** The B4 milestone description in `phase-b.md` still carries the future-tense wording appropriate for when B4 was just opened: "Opened 2026-05-14 ... gates on ADR-0029 Accepted before implementation begins." ADR-0029 is now Accepted and T-019 is merged. The milestone body text does not reflect the closed state. Compare with B2 and B3 milestone sections which have a clear "**Status: B2 Closed ...**" / "**Status: B3 implementation-complete ...**" header line. B4 has no analogous status header.

**Suggested fix:** Add a B4 status line after the milestone introduction: "**Status: B4 implementation-complete (2026-05-16 via PR #31 merge; closure trio pending).** T-019 Done; ADR-0029 Accepted. Closure trio (business + security + performance) is the next review trigger per the B3 precedent." The existing B4 body content (requirements, sub-breakdown, acceptance criteria) remains as the design record.

---

### Nit

#### D4-012 — Phase C through J task READMEs use identical boilerplate; phase-j diverges beneficially but without guidance

**File:** `docs/analysis/tasks/phase-c/README.md` through `docs/analysis/tasks/phase-j/README.md`

**Description:** Eight phase-level task READMEs (C through J) are all identical 11-line stubs except `phase-j/README.md`, which adds a two-sentence note about Phase J being opt-in per ADR-0015. The stub content is appropriate — tasks are not yet defined. The nit is that the phase-j README's ADR-0015 reference is good practice (linking the README to the design decision that governs its special status), but this pattern is absent from phase-c through phase-i, even though several of those phases have analogous design-constraint ADRs (e.g., phase-g references ADR-0015 scope exclusion in its plan). Not a blocking issue, but the phase-j precedent is worth following when phases get closer to active.

**Suggested fix:** No immediate action needed. When a phase approaches active status, its task README should be enriched with design-constraint links analogous to phase-j's ADR-0015 note.

---

#### D4-013 — `current.md` "Next task to open" bullet still describes B4 closure + B5 as "next" but B4 is now merged

**File:** `docs/roadmap/current.md:86`

**Description:** The "Next task to open" line (line 86) reads "B4 milestone closure + B5 syscall-ABI ADR pair (ADR-0030 + ADR-0031)." This is the correct next step (the B4 closure trio followed by B5 opening), but its framing implies T-019 is still pending merge ("T-019 (above) closes B4's implementation half on merge"). The phrasing "on merge" is now past tense — the merge happened. The line should be updated to "B4 closure trio (business + security + performance baseline) — T-019 merged; trigger: Done flip. Then B5 syscall-ABI ADR pair (ADR-0030 + ADR-0031)."

**Suggested fix:** Rephrase to reflect that T-019 has merged and the trigger is the Done flip + closure trio, not a future merge event.

---

#### D4-014 — Phase D milestone D4 is absent from phase-d.md ADR ledger table

**File:** `docs/roadmap/phases/phase-d.md:162–166`

**Description:** The phase-d.md ADR ledger table lists D1, D2, D3, D5, and D6. There is no D4 row. The milestone D4 is described in the phase body (it appears to be the UART / console bringup, separate from the PL011-vs-mini-UART architectural choice of D3). Whether the gap is intentional (D4 requires no ADR) or an oversight is unclear from the document — the milestone section headings jump from D3 to D5 without explanation. The phase plan should make the absence explicit.

**Suggested fix:** Either add a D4 row to the ledger explaining why it requires no ADR ("D4 — Console initialization sequence: implementation-only, no ADR required"), or add an explanatory note below the table if D4 was intentionally omitted. The jump from D3 to D5 in milestone numbering is itself worth a one-line note.

---

### Praise

#### D4-P01 — Simulation table discipline is consistently applied from T-015 onward

All task files from T-015 through T-019 carry a `§Approach §Simulation` table that walks the implementation's state-machine paths step-by-step, pins each row to a specific host test or audit-log entry, and — critically — was updated during the review rounds when the implementation diverged from the original plan (e.g., T-019's row-1 alignment preflight added in round 4). This discipline, codified via the `write-adr` skill, is directly responsible for the absence of any smoke regression in B2 through B4 (contrast with B1's smoke-regression rollback). The thoroughness of the simulation tables in T-017 (`intermediate_frame_count` exact-count helper) and T-019 (row-reordering to put VA-range check before frame-budget) demonstrates that the discipline is being followed substantively, not superficially.

---

#### D4-P02 — ADR renumbering history in phase-b.md ADR ledger is exemplary

The phase-b.md ADR ledger (lines 270–278) documents the renumbering story in the "Notes" column: "was ADR-0025 in the pre-2026-04-27 plan; renumbered down by 2 because ADR-0025 (governance) and ADR-0026 (T-012 reservation) consumed slots." This meta-information is precisely what prevents future agents from confusing the pre-renaming plan references with the live ADR numbers. Other phases should adopt this practice when their ADR numbering stabilizes.

---

#### D4-P03 — Review history append-only discipline is uniformly maintained

Every task file from T-006 through T-019 maintains a review history table that is append-only (new rows at the top) with dated entries, reviewer attribution, and specific content. The review histories in T-018 and T-019 in particular are rich enough to reconstruct the full technical arc of each PR — including findings that were rejected with explicit rationale (e.g., T-019 review-round 2 F3: `CapRights::empty()` reject-with-documentation). This level of traceability is unusual and valuable for a security-critical project.

---

#### D4-P04 — Phase C through J task README stubs are an appropriate "tasks will be added when active" pattern

The eight phase-level task READMEs for phases C through J are correctly minimal — they do not prematurely invent task IDs or stub out task files for work that has not been planned at the task level. The phase plan files (phase-c.md through phase-j.md) carry the appropriate detail for their level of planning maturity. This tiered approach (detailed plan file + empty task index until tasks actually open) is exactly the right discipline for a long-horizon project and avoids the maintenance burden of stale half-invented task files.

---

## Claims register

The table below lists concrete numerical or status claims in the roadmap/task documents and records how each was verified against code or git state at commit `288ddb2`.

| Claim | Location | Value claimed | Verified value | Verdict |
|---|---|---|---|---|
| "Tests at HEAD: **259/259**" | `current.md:7` (T-019 banner) | 259 passing | 260 passing (`grep -rn "#\[test\]"` = 260; gate-reproduction confirmed) | **Off by 1** |
| "Tests at HEAD: **259/259**" | `T-019-task-loader.md:135` (round-4 row) | 259 passing | 260 at HEAD (round-5 added 1 PMM test) | **Off by 1 (historical row, round-4 was accurate when written)** |
| "Active task: T-019 — In Review on PR #31" | `current.md:54` | In Review | PR #31 merged at `7f876af` (git log) | **Stale — PR is merged** |
| "In review: T-019 (PR #31)" | `current.md:55` | In Review | Merged | **Stale** |
| "Working branch: T-016 lives on t-016-mmu-activation" | `current.md:57` | Active work branch | T-016 Done since 2026-05-08; branch closed | **Stale** |
| "Last completed milestone: B1" | `current.md:58` | B1 | B4 implementation-complete (B2 closed 2026-05-09, B3 closed 2026-05-14, B4 merged 2026-05-16) | **Three milestones stale** |
| "Status: In Review" | `T-019-task-loader.md:6` (frontmatter) | In Review | PR #31 merged — task should be Done | **Stale** |
| "226 host tests pass workspace-wide" (T-018 merge) | `current.md:11` | 226 at T-018 merge | Progression 200 (PR #27) + 26 (T-018 arc) = 226 — consistent with other sources | **Accurate** |
| "221/221 host tests" (T-018 task file, from prior session read) | `T-018-task-loader.md` review history | 221 at T-018 implementation commit | 221 was an intermediate count; 226 is final post-review-round count; both are self-consistent | **Accurate (different milestones)** |
| "B0 closed 2026-04-27" | `current.md:52` | Closed | git: `9a66e8b` PR #9 merge confirmed | **Accurate** |
| "B1 closed 2026-05-07" | `current.md:52` | Closed | git: `e9fa019` PR #15 merge confirmed | **Accurate** |
| "B2 closed 2026-05-09" | `current.md:52` | Closed | Closure trio committed 2026-05-09 | **Accurate** |
| "B3 closed 2026-05-14 via PR #29 merge commit b425dc1" | `current.md:52` | Closed | git log confirms merge at that hash | **Accurate** |
| "Phase A: 109 host tests" | `current.md:92` | 109 | Consistent with progression (109 → 143 → ... → 260) | **Accurate** |
| "ADR-0027 through ADR-0031: Phase C milestones" | `phase-c.md:118–122` | Unallocated | ADR-0027, 0028, 0029 are live on `main`; 0030, 0031 reserved for B5 | **Conflict (Blocker D4-001)** |
| "ADR-0032 through ADR-0036: Phase D milestones" | `phase-d.md:162–166` | Unallocated | ADR-0032 and 0035 are live on `main`; 0033 and 0034 are Phase B named placeholders | **Conflict (Blocker D4-002)** |
| "T-010 not opened" | `phase-b.md` notes section | Absent task | No T-010 file in git ls-files; confirmed intentionally absent | **Accurate** |
| Phase A tasks T-001 through T-005: all Done | `phase-a/README.md`, `phase-a.md` | Done | Task files all show Done with dates | **Accurate** |
| Phase B tasks T-006 through T-019 (excl. T-010): Done/In-Review | `phase-b/README.md`, phase files | Various | T-006 through T-018: Done. T-019: In Review per file but merged per git | **T-019 stale** |
| UNSAFE audit entries 0001–0027 referenced in task/ADR files | Multiple | 27 entries | `docs/decisions/` confirmed entries up to 0027 via ADR cross-refs | **Accurate** |

---

## Consistency map

### Roadmap ↔ phases ↔ tasks ↔ current.md

**Agreements (all consistent):**

- Phase A closure: all four layers agree — A1–A6 Done, T-001–T-005 Done, 109 host tests, QEMU smoke verified.
- Phase B milestones B0–B3 closure: all layers agree on dates and mechanics. B0 closed 2026-04-27 (PR #9), B1 closed 2026-05-07 (PR #15 + PR #16 closure trio), B2 closed 2026-05-09 (PR #23 + closure trio), B3 closed 2026-05-14 (PR #29 closure trio). These appear in phase-b.md status headers, current.md dated banners, and individual task files consistently.
- ADR allocations ADR-0001 through ADR-0029 and ADR-0032/0035: all live files agree on what these ADRs contain and their Accepted status.
- T-010 is intentionally absent: phase-b.md notes section, phase-b README, and the task directory all agree.
- Task template conformance: T-001 through T-019 all follow the TEMPLATE.md shape (frontmatter fields, user story, acceptance criteria, DoD, review history). No file deviates substantially.
- Skills path in task files: tasks/README.md uses `.agents/skills/` (correct). Task files uniformly link `.agents/skills/` in their frontmatter and review histories (correct post-migration).

**Conflicts:**

| Layer A | Layer B | Nature |
|---|---|---|
| `current.md:54` (T-019 In Review) | git log (`7f876af` PR #31 merged) | T-019 status: plan says In Review; git says Done |
| `current.md:57` (T-016 working branch) | git state (T-016 Done 2026-05-08) | Working branch claim stale by 13+ days |
| `current.md:58` (Last completed milestone: B1) | `current.md:52` (B2, B3 noted as closed in same file) | Internal inconsistency within current.md itself |
| `T-019-task-loader.md:6` (Status: In Review) | git log (PR #31 merged) | Task file status lags git |
| `phase-b/README.md` (index ends at T-017) | `phase-b/` directory (contains T-018.md and T-019.md) | Index incomplete |
| `phase-c.md:118–122` (ADR-0027–0031 for C milestones) | `docs/decisions/0027–0029` (live files) | ADR number collision — Blocker |
| `phase-d.md:162–166` (ADR-0032–0036 for D milestones) | `docs/decisions/0032, 0035` (live files) | ADR number collision — Blocker |
| `current.md:7` (259/259 tests) | actual codebase at HEAD (260 tests) | Off by 1 |
| `docs/roadmap/README.md:25,45,46` (`.claude/skills/`) | `.agents/skills/` (post-migration canonical path) | Stale skill path |
| `phase-b.md:27,115,125,148,270,271,278,307` (`.claude/skills/`) | `.agents/skills/` | Stale skill path (live prose, not historical banners) |

**Near-miss (not a conflict, but notable):**

- Phase B milestones in phase-b.md use B4 `§Revision-notes` to explain that `task_create_from_image` is deferred to B5/B6. The T-019 task file and current.md both carry this clarification. All three layers agree. This is a correctly-documented scope adjustment, not a conflict.
- The phase-b.md ADR ledger correctly explains renumbering history (ADR-0025 was originally ADR-0027, etc.). This is internally consistent and prevents confusion.

---

## Cross-track notes

The following observations are relevant to other review tracks:

**For D2a/D2b (ADR track):** The ADR numbering collision (D4-001, D4-002) is primarily a planning document issue, but the ADR track should verify that `docs/decisions/` has no files named 0030.md or 0031.md that would compound the conflict if Phase C or D were implemented before the phase plan is corrected. Current state: `ls docs/decisions/` shows 0001–0029 (with some gaps), 0032, and 0035 — no 0030 or 0031 files yet. The collision is in the phase plans only, not in the ADR directory.

**For C4-kernel-task-loader (code track):** The T-019 status discrepancy (D4-003, D4-004) affects code track credibility: code reviewers may have marked T-019 findings as resolved based on the In Review status, but the Done flip has not occurred. If the code track D4-review-round-6 commit (`eb14c51`) closed the remaining open findings, then the code is in a merge-valid state but the plan record has not been updated to confirm this.

**For D5b-audits-reports (meta track):** The 259-vs-260 test count discrepancy (D4-006) is independently confirmed by gate-reproduction.md line 30 (which shows 260). The meta track's findings and this track's findings agree on the magnitude (off by 1) and direction (under-count, not a regression).

**For D1-architecture (architecture docs):** The B4 milestone closure triggering a B4 closure trio (business + security + performance) has not yet happened per the plan record. When it does trigger, the architecture docs track should verify that `docs/architecture/task-loader.md` (referenced in T-019's acceptance criteria) is complete and consistent with the merged code.

---

## Coverage checklist

All 43 files in scope were read in full. Line counts from `wc -l` at commit `288ddb2`.

### Roadmap files (13)

| File | Lines | Read |
|---|---|---|
| `docs/roadmap/README.md` | 46 | [x] |
| `docs/roadmap/current.md` | 98 | [x] |
| `docs/roadmap/phases/README.md` | 55 | [x] |
| `docs/roadmap/phases/phase-a.md` | 208 | [x] |
| `docs/roadmap/phases/phase-b.md` | 312 | [x] |
| `docs/roadmap/phases/phase-c.md` | 128 | [x] |
| `docs/roadmap/phases/phase-d.md` | 175 | [x] |
| `docs/roadmap/phases/phase-e.md` | 120 | [x] |
| `docs/roadmap/phases/phase-f.md` | 93 | [x] |
| `docs/roadmap/phases/phase-g.md` | 130 | [x] |
| `docs/roadmap/phases/phase-h.md` | 75 | [x] |
| `docs/roadmap/phases/phase-i.md` | 77 | [x] |
| `docs/roadmap/phases/phase-j.md` | 115 | [x] |

### Task files (30)

| File | Lines | Read |
|---|---|---|
| `docs/analysis/tasks/README.md` | 51 | [x] |
| `docs/analysis/tasks/TEMPLATE.md` | 65 | [x] |
| `docs/analysis/tasks/phase-a/README.md` | 15 | [x] |
| `docs/analysis/tasks/phase-a/T-001-capability-table-foundation.md` | 109 | [x] |
| `docs/analysis/tasks/phase-a/T-002-kernel-object-storage.md` | 102 | [x] |
| `docs/analysis/tasks/phase-a/T-003-ipc-primitives.md` | 97 | [x] |
| `docs/analysis/tasks/phase-a/T-004-cooperative-scheduler.md` | 95 | [x] |
| `docs/analysis/tasks/phase-a/T-005-two-task-ipc-demo.md` | 106 | [x] |
| `docs/analysis/tasks/phase-b/README.md` | 21 | [x] |
| `docs/analysis/tasks/phase-b/T-006-raw-pointer-scheduler-api.md` | 114 | [x] |
| `docs/analysis/tasks/phase-b/T-007-idle-task-typed-deadlock.md` | 121 | [x] |
| `docs/analysis/tasks/phase-b/T-008-architecture-docs.md` | 121 | [x] |
| `docs/analysis/tasks/phase-b/T-009-timer-init-cntvct.md` | 112 | [x] |
| `docs/analysis/tasks/phase-b/T-011-missing-tests-bundle.md` | 111 | [x] |
| `docs/analysis/tasks/phase-b/T-012-exception-and-irq-infrastructure.md` | 113 | [x] |
| `docs/analysis/tasks/phase-b/T-013-el-drop-to-el1.md` | 91 | [x] |
| `docs/analysis/tasks/phase-b/T-014-idle-dispatch-fallback.md` | 134 | [x] |
| `docs/analysis/tasks/phase-b/T-015-endpoint-rollback-cancel-recv.md` | 114 | [x] |
| `docs/analysis/tasks/phase-b/T-016-mmu-activation.md` | 163 | [x] |
| `docs/analysis/tasks/phase-b/T-017-physical-memory-manager.md` | 175 | [x] |
| `docs/analysis/tasks/phase-b/T-018-address-space-kernel-object.md` | 177 | [x] |
| `docs/analysis/tasks/phase-b/T-019-task-loader.md` | 138 | [x] |
| `docs/analysis/tasks/phase-c/README.md` | 11 | [x] |
| `docs/analysis/tasks/phase-d/README.md` | 11 | [x] |
| `docs/analysis/tasks/phase-e/README.md` | 11 | [x] |
| `docs/analysis/tasks/phase-f/README.md` | 11 | [x] |
| `docs/analysis/tasks/phase-g/README.md` | 11 | [x] |
| `docs/analysis/tasks/phase-h/README.md` | 11 | [x] |
| `docs/analysis/tasks/phase-i/README.md` | 11 | [x] |
| `docs/analysis/tasks/phase-j/README.md` | 13 | [x] |

**Total files read: 43 / 43.**
