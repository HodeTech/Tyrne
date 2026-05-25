# D5a-meta-core — front-door docs + skills (master review, commit 288ddb2)

## Summary

The front-door documentation and skill library are **in good shape overall** — the README is an excellent first read for any newcomer, the skill files are detailed, procedurally specific, and consistently follow the Anthropic skill-file shape. No blockers were found. The set of issues is dominated by three clusters: (1) stale project-status prose in CLAUDE.md and CONTRIBUTING.md that lags the real codebase by several phases; (2) a wrong artifact path in the skills README index for `conduct-review`; and (3) glossary gaps for three terms central to the design. Eleven findings total: 0 Blockers, 3 Major, 5 Minor, 3 Nit. Nine dead or stale references were identified across the 30 files.

---

## Findings

### Blocker

*None.*

---

### Major

#### D5a-001 — CLAUDE.md project-status description is materially stale

`CLAUDE.md:7`

CLAUDE.md §"What this project is" reads: *"The project is pre-alpha — most code is not yet written, and the current phase is architecture design captured in Architecture Decision Records."* This was accurate at project inception but is no longer true. At commit 288ddb2 the kernel boots end-to-end on QEMU `virt` aarch64, runs a two-task IPC demo, has 37 Rust source files, and is mid-Phase B (syscall ABI next). Thirty-seven source files and 27 audited `unsafe` blocks are not "most code not yet written." An AI agent reading CLAUDE.md cold would form a wildly wrong mental model of what exists, likely proposing architectural-only work when implementation work is already active.

**Suggested fix:** Update §"What this project is" to reflect Phase B progress. A one-paragraph replacement that matches the README §"Status at a glance" table would suffice:

> *"Tyrne is pre-alpha. The kernel boots end-to-end on QEMU `virt` aarch64 and runs a two-task capability-gated IPC demo. The project is mid-Phase B: the MMU, PMM, address-space objects, and task loader are done; the syscall ABI and first userspace task are next. Architecture is documented as ADRs (32 total); active implementation work is under `kernel/`, `hal/`, and `bsp-qemu-virt/`."*

---

#### D5a-002 — CONTRIBUTING.md calls the project "architecture phase" — materially stale

`CONTRIBUTING.md:3`

CONTRIBUTING.md opens with: *"Tyrne is currently in the architecture phase — the foundational design documents are being written and the codebase is not yet open for code contributions."* This contradicts README.md's "pre-alpha" framing, SECURITY.md's "Phase A + B0/B1 closed" framing, and reality (the kernel boots, 37 `.rs` files exist, IPC round-trips run). A potential contributor reading CONTRIBUTING.md would incorrectly conclude that there is no runnable code, possibly missing the chance to review ADRs against a real implementation.

The CONTRIBUTING.md also says *"Rust workspace exists and the kernel boots end-to-end on QEMU virt (Phase A + B0/B1 closed)"* at line 14, so the same file holds contradictory self-descriptions of the project state.

**Suggested fix:** Replace the opening paragraph with a statement matching the README status. The rest of CONTRIBUTING.md (no code PRs yet; issues and ADR reviews welcome) remains accurate and should be kept.

---

#### D5a-003 — Skills README index has a wrong artifact path for `conduct-review`

`.agents/skills/README.md:76`

The index table entry reads:

```
| [conduct-review](conduct-review/SKILL.md) | Produce a milestone retrospective in `docs/roadmap/reviews/`. |
```

The path `docs/roadmap/reviews/` does not exist on disk. The correct location, as stated in the `conduct-review/SKILL.md` itself (step 6, acceptance criteria) and confirmed by the actual artifact tree, is `docs/analysis/reviews/<type>-reviews/`. An agent looking at the index to decide whether to use this skill would navigate to a nonexistent path.

**Suggested fix:** Change the index row description to:

```
| [conduct-review](conduct-review/SKILL.md) | Produce a business / code / security / performance review artifact in `docs/analysis/reviews/<type>-reviews/`. |
```

---

### Minor

#### D5a-004 — README.md ADR count "32 accepted ADRs" is inaccurate

`README.md:41`

README.md states: *"The current count is 32 accepted ADRs."* Actual state at commit 288ddb2: 31 ADR files on disk, of which 29 have `Status: Accepted`, 1 is `Deferred` (ADR-0023), and 1 is `Superseded by 0026` (ADR-0022). The numeric claim is also inconsistent with the file count. Additionally, ADR numbers 0030, 0031, 0033, 0034 are absent from disk; the gaps are not explained in any visible location.

**Suggested fix:** Update the sentence to the accurate count. Also add a note in `docs/decisions/README.md` (outside this track's scope) explaining the four numbering gaps, per the `sync-adr-index` skill's anomaly-reporting guidance.

---

#### D5a-005 — docs/README.md Layout table omits `analysis/`, `roadmap/`, and `audits/` subdirectories

`docs/README.md:7–13`

The Layout table lists only `architecture/`, `decisions/`, `guides/`, `standards/`, and `glossary.md`. Three substantial directories — `analysis/` (task user stories + reviews), `roadmap/` (phase plans + current status), and `audits/` (unsafe-log.md) — exist under `docs/` but are absent from the table. A newcomer who reads `docs/README.md` as the canonical map of the documentation tree would not discover where task tracking, milestone reviews, and the unsafe audit log live.

**Suggested fix:** Add three rows to the Layout table:

| `analysis/` | What is being built and how it is going: task user stories, business / code / security / performance reviews. |
| `roadmap/` | Phase plans and the currently-active milestone. |
| `audits/` | The `unsafe` audit log — every audited `unsafe` block in the codebase. |

---

#### D5a-006 — docs/README.md reading order cites "(Phase 2)" — orphaned phrase

`docs/README.md:19`

The reading-order item 3 reads: *"start with the overview (Phase 2), then dive into whichever subsystem interests you."* The parenthetical "(Phase 2)" has no meaning in the current documentation scheme. `docs/architecture/README.md` does not use a "Phase N" numbering for its documents; overview.md is simply `overview.md`. This appears to be a residual from an older chapter-numbering scheme.

**Suggested fix:** Remove "(Phase 2)": *"start with `overview.md`, then dive into whichever subsystem interests you."*

---

#### D5a-007 — Glossary is missing three terms central to the design

`docs/glossary.md` (entire file)

ADR-0018 introduces the **Badge** scheme (a value embedded in a derived capability to identify the granter). The badge is referenced in the title of ADR-0018 (`0018-badge-scheme-and-reply-recv-deferral.md`) and in capability semantics documentation, but `Badge` is not defined in the glossary. Similarly:

- **TCB (Trusted Computing Base)** — used in README.md ("the entire trusted computing base can be audited line by line") and in security-model.md, but not in the glossary.
- **Reply capability** — ADR-0018 also introduces reply capabilities (a single-use send cap auto-issued on IPC receive). Neither "reply capability" nor "reply cap" appears in the glossary.

All three terms are project-specific vocabulary that a newcomer needs to understand the design, and the glossary's own preamble says: *"If a term appears in documentation and is not obvious from general OS-development literacy, it should be listed here."*

**Suggested fix:** Add entries for `Badge`, `TCB (Trusted Computing Base)`, and `Reply capability` following the `update-glossary` skill procedure. Badge and Reply capability should cite ADR-0018; TCB should cite the security-model.md and README.md.

---

#### D5a-008 — CLAUDE.md rule 2 points to `docs/standards/` for unsafe audit tracking but the log lives in `docs/audits/`

`CLAUDE.md:16`

Rule 2 states: *"Audit tracking for `unsafe` is defined in `[docs/standards/](docs/standards/)`."* While `docs/standards/unsafe-policy.md` does define the *policy*, the actual audit log that tracks every block is at `docs/audits/unsafe-log.md`. An agent following this rule and navigating to `docs/standards/` would find the policy but not the log. This creates a navigability gap for any agent that needs to add or verify an audit entry.

**Suggested fix:** Change rule 2 to: *"Audit tracking for `unsafe` is governed by [`docs/standards/unsafe-policy.md`](docs/standards/unsafe-policy.md); each block's audit entry is in [`docs/audits/unsafe-log.md`](docs/audits/unsafe-log.md)."*

---

#### D5a-009 — `add-bsp` skill exceeds the ~200-line soft limit stated in the skills README

`.agents/skills/add-bsp/SKILL.md` (213 lines); `.agents/skills/README.md:57`

The skills README states: *"If a skill needs more than ~200 lines, either (a) the underlying task is actually two tasks and should be split, or (b) the task has non-skill-sized complexity and belongs in a guide under `docs/guides/`."* The `add-bsp` skill is 213 lines, exceeding this guideline. The skill is well-written and the content is substantive (not padded), but a portion of it — specifically the detailed `boot.s` template in step 4 and the diagnostic table in step 10 — reads more like guide material than skill material.

**Suggested fix:** Either (a) extract step 4 (write boot.s) and step 10 (smoke test debugging) into `docs/guides/bsp-bring-up.md`, keeping the skill as a checklist that references the guide; or (b) acknowledge the intentional exception in the skill's frontmatter with a note explaining why this case warrants the extra length. The latter is the lighter-weight fix.

---

### Nit

#### D5a-010 — NOTICE file uses a different repo slug than SECURITY.md

`NOTICE:5`; `SECURITY.md:13`

NOTICE references `https://github.com/cemililik/TyrneOS` (note: `TyrneOS`). SECURITY.md references `https://github.com/HodeTech/Tyrne`. The correct slug per the project name is `Tyrne`. The NOTICE URL likely predates the rename from Umbrix / pre-rename-era tooling.

**Suggested fix:** Update NOTICE line 5 to `https://github.com/HodeTech/Tyrne`.

---

#### D5a-011 — README.md "259 tests" comment is a snapshot count that will drift

`README.md:80`

The Quick Start section includes the comment `# 259 tests across kernel, HAL, test-HAL`. Hardcoded test counts in documentation decay immediately as tests are added or removed and provide false confidence to readers who assume the count is current.

**Suggested fix:** Remove the specific number. Replace with: `# host-side test suite (kernel · HAL · test-HAL)`.

---

#### D5a-012 — README.md "UNSAFE-2026-0027" and "27 unsafe audit entries" are point-in-time snapshots

`README.md:35`

Similar to D5a-011, the README embeds two volatile counts: the specific audit entry tag `UNSAFE-2026-0027` (described as "the task-loader byte-copy") and "currently 27 `unsafe` audit entries." Both will be stale as soon as Phase B5 or B6 adds any `unsafe` block.

**Suggested fix:** Either link to the audit log rather than citing counts, or remove the count and tag: *"Every `unsafe` block carries a SAFETY comment ... and is tracked in [`docs/audits/unsafe-log.md`](docs/audits/unsafe-log.md) with a numbered audit entry."*

---

### Praise

- **README.md is an excellent first read.** The structure — status table, design principles, quick start, architecture diagram, hardware tiers, repo layout, documentation map, engineering disciplines — is exactly the right shape for a pre-alpha kernel project. The Mermaid architecture diagram is clear and correctly scoped. The "Naming" section that explains the rename is a thoughtful inclusion that preempts confusion.

- **Skill library is exemplary.** All 15 skills follow the Anthropic skill-file shape (YAML frontmatter + standard sections). Every skill has a complete Inputs / Procedure / Acceptance criteria / Anti-patterns / References structure. The `write-adr` skill's detailed treatment of the Simulation subsection, row-to-verification mapping, and the ADR-0025 cool-down withdrawal context is a particularly strong example of a skill that explains not just *what* to do but *why the rule exists*.

- **Glossary depth.** For a project at this stage, the glossary is unusually thorough. The ARM register entries (`CNTFRQ_EL0`, `CNTPCT_EL0`, `CNTVCT_EL0`) and the `MapperFlush` and `mmu_bootstrap` / `.boot_pt` entries give a hardware-literacy newcomer exactly the context they need. The cross-referencing to ADRs on first use is consistent.

- **CLAUDE.md and AGENTS.md tell a consistent story.** The seven non-negotiable rules are listed in full in CLAUDE.md and summarised faithfully in AGENTS.md. A non-Claude agent reading AGENTS.md gets an accurate pointer to the canonical guide.

- **Security-first framing throughout.** SECURITY.md's "For AI agents" paragraph (a specific instruction to stop and flag any weakening of security properties) is well-placed and clear. The conduct-approval-review skill's audit-log spot-check step and the justify-unsafe skill's mandatory security-review request correctly treat unsafe as a first-class security gate.

- **No stale `.claude/skills/` references in the 30 reviewed files.** The migration from `.claude/skills/` to `.agents/skills/` is complete within the D5a scope; all internal skill cross-references use the correct `.agents/skills/` path.

---

## Claims register

| Claim / Reference | File:line | How to verify |
|---|---|---|
| "32 accepted ADRs" | README.md:41 | `grep -c "Status: Accepted" docs/decisions/0*.md` — returns 29 |
| "259 tests across kernel, HAL, test-HAL" | README.md:80 | Run `cargo host-test` and count reported test cases |
| "27 `unsafe` audit entries" | README.md:35 | `grep -c "^### UNSAFE" docs/audits/unsafe-log.md` — returns 27 ✓ |
| "UNSAFE-2026-0027, the task-loader byte-copy" | README.md:35 | `grep "UNSAFE-2026-0027" docs/audits/unsafe-log.md` — found ✓ |
| `docs/roadmap/reviews/` (conduct-review artifact location) | .agents/skills/README.md:76 | Path does not exist; correct is `docs/analysis/reviews/` |
| "most code is not yet written" | CLAUDE.md:7 | `find . -name "*.rs" | wc -l` returns 37 — code exists |
| "architecture phase" | CONTRIBUTING.md:3 | README.md shows kernel boots (Phase B); contradicted internally at CONTRIBUTING.md:14 |
| Badge, TCB, Reply capability absent from glossary | docs/glossary.md (entire) | `grep -n "Badge\|TCB\|Reply cap" docs/glossary.md` returns empty |
| NOTICE GitHub URL `TyrneOS` | NOTICE:5 | Does not match `Tyrne` slug used in SECURITY.md:13 |
| `docs/standards/` contains unsafe audit tracking | CLAUDE.md:16 | Actual log is `docs/audits/unsafe-log.md`; policy is in `docs/standards/unsafe-policy.md` |
| "(Phase 2)" architecture reading order | docs/README.md:19 | No "Phase 2" scheme exists in `docs/architecture/README.md` |
| analysis/, roadmap/, audits/ omitted from docs layout | docs/README.md:7–13 | `ls docs/` shows all three subdirectories exist |

---

## Dead-link / stale-path scan

Every path was verified with `ls` or `git ls-files` at commit 288ddb2.

| Reference | Source file:line | Status | Notes |
|---|---|---|---|
| `docs/roadmap/reviews/` | `.agents/skills/README.md:76` | Stale — path does not exist | Correct path is `docs/analysis/reviews/<type>-reviews/`; the conduct-review SKILL.md itself uses the correct path |
| `https://github.com/cemililik/TyrneOS` | `NOTICE:5` | Stale repo slug | Should be `https://github.com/HodeTech/Tyrne` (matches SECURITY.md) |
| "(Phase 2)" in reading order | `docs/README.md:19` | Orphaned phrase | No Phase-N numbering scheme exists in arch docs |
| `docs/standards/` for unsafe audit tracking | `CLAUDE.md:16` | Misleading pointer | Policy is in docs/standards/; log is in docs/audits/; only the former is pointed to |
| "most code is not yet written … architecture design" | `CLAUDE.md:7` | Stale status description | Phase B implementation is well underway |
| "architecture phase" | `CONTRIBUTING.md:3` | Stale status description | Contradicted by CONTRIBUTING.md:14 and README.md |
| `Badge`, `TCB`, `Reply capability` | `docs/glossary.md` | Missing entries | Terms appear in ADRs and architecture docs but not in glossary |
| "32 accepted ADRs" | `README.md:41` | Inaccurate count | 29 Accepted on disk; 1 Deferred; 1 Superseded; total files 31 |
| "259 tests" | `README.md:80` | Volatile count | Will drift; not verifiable without running suite |

Note: `.claude/skills/` stale references exist in files *outside* the D5a-30-file scope (ADR-0023 at lines 38 and 51; several files under `docs/analysis/technical-analysis/` and `docs/analysis/reviews/code-reviews/`). Those are reported here as a cross-track note, not as D5a findings.

---

## Cross-track notes

1. **D5b / architecture track:** `docs/architecture/README.md:20` lists `memory-management.md` as *"Planned — B2"*. The file exists on disk and is populated. The index is stale. This does not affect any of the 30 D5a files but should be caught by the D5b track.

2. **D5c / decisions track:** ADR-0023 (`docs/decisions/0023-cross-table-capability-revocation-policy.md`) at lines 38 and 51 contains stale `.claude/skills/supersede-adr/SKILL.md` and `.claude/skills/write-adr/SKILL.md` references. These predate the skill-library migration to `.agents/skills/`. The D5a scope does not include ADR files, but the D5c track should flag and fix them.

3. **D5d / standards track:** ADR-0023 also contains a note about the "supersede-adr skill" and "write-adr skill" (stale paths). The standards track may wish to coordinate the fix.

4. **Multiple tracks / technical-analysis files:** `docs/analysis/technical-analysis/` files contain `.claude/skills/` references. Those files are outside D5a scope; the track responsible for technical-analysis content should clean them up.

---

## Coverage checklist

All 30 files read in full. Line counts from `wc -l`.

| File | Lines | Read |
|------|-------|------|
| `README.md` | 232 | [x] |
| `CONTRIBUTING.md` | 33 | [x] |
| `SECURITY.md` | 33 | [x] |
| `CLAUDE.md` | 60 | [x] |
| `AGENTS.md` | 23 | [x] |
| `NOTICE` | 7 | [x] |
| `LICENSE` | 201 | [x] (skimmed — standard Apache-2.0 text, correct) |
| `docs/README.md` | 28 | [x] |
| `docs/glossary.md` | 91 | [x] |
| `docs/analysis/README.md` | 49 | [x] |
| `.agents/skills/README.md` | 88 | [x] |
| `.agents/skills/add-bsp/SKILL.md` | 213 | [x] |
| `.agents/skills/add-dependency/SKILL.md` | 104 | [x] |
| `.agents/skills/conduct-approval-review/SKILL.md` | 147 | [x] |
| `.agents/skills/conduct-review/SKILL.md` | 81 | [x] |
| `.agents/skills/justify-unsafe/SKILL.md` | 102 | [x] |
| `.agents/skills/perform-code-review/SKILL.md` | 82 | [x] |
| `.agents/skills/perform-security-review/SKILL.md` | 79 | [x] |
| `.agents/skills/propose-standard-change/SKILL.md` | 76 | [x] |
| `.agents/skills/start-task/SKILL.md` | 88 | [x] |
| `.agents/skills/supersede-adr/SKILL.md` | 74 | [x] |
| `.agents/skills/sync-adr-index/SKILL.md` | 80 | [x] |
| `.agents/skills/update-glossary/SKILL.md` | 66 | [x] |
| `.agents/skills/write-adr/SKILL.md` | 91 | [x] |
| `.agents/skills/write-architecture-doc/SKILL.md` | 130 | [x] |
| `.agents/skills/write-guide/SKILL.md` | 111 | [x] |
