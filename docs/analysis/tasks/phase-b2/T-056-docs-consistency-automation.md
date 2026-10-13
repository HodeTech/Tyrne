# T-056 — Automate docs-corpus consistency checks (polish; optional for exit)

- **Phase:** B.2
- **Milestone:** Track B.2-2 (Polish items; not exit-gating)
- **Status:** In Progress
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-048](T-048-phase-b-task-corpus-sync.md), [T-049](T-049-review-indices-sync.md), [T-052](T-052-standards-docs-reality-sync.md), [T-053](T-053-standards-docs-mechanical-fixes.md), [T-054](T-054-adr-ledger-renumbering-cascade.md), [T-055](T-055-adr-append-only-corrections.md); [T-047](T-047-roadmap-state-and-phase-index-sync.md) supplies the delimited live-state surface
- **Informs:** none
- **ADRs required:** [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md) (Accepted 2026-10-12; reviewed execution and corpus policy)

---

> **Approved contract reconciliation (2026-10-12).** The maintainer approved the [preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and ADR package. The criteria below are the executable contract; dated opening observations remain historical. This preparation records no task delivery. Each implementation step includes verification and two fresh independent review rounds under [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); new task states stop at `In Review`.

## User story

As the maintainer, I want the documentation drift that two full-tree reviews found by hand to be detected by a small offline script, so that index gaps, broken links and inconsistent planned identities are caught on the pull request that introduces them.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). Four of the documentation findings in Track B.2-2 of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) are recurrences of items the 2026-05-22 master review had already fixed (Blockers D4-001, D4-002, D4-003, D4-005 and Major D4-004): ADR-number collisions between phase ledgers, a stale `current.md`, a task index missing tasks, task files stuck at `In Review`. They recur because each fix was made by hand and nothing checks it. The Polish list in `phase-b2.md` asks for the same checks to be mechanised: a relative-link checker, index-versus-disk reconciliation, detection of duplicate tentative ADR numbers, commit-scope drift, untagged fences, task-status versus `current.md` consistency, and the audit-tag cross-check that the last review did by hand (33 of 33 tags matched in both directions). This task is optional for the Phase B.2 exit and is fully selected for this requested sequence; its reconciled dependencies establish a green corpus before the required CI wiring is enabled. Acceptance alone does not deliver this task.

## Acceptance criteria

- [ ] Implement a Python 3.9+ standard-library command under tools/ with explicit UTF-8, script-relative default root, isolated fixture-root override, sorted deterministic file:line findings, zero only on success and nonzero for invalid input/inconsistency. No third-party dependency, network or repository-setting mutation. Document usage, exit codes, supported grammar/limits, interpreter requirement, adding checks and Required enforcement in docs/guides/ci.md and docs/standards/infrastructure.md. The delivered CI step is the selected ongoing index-consistency procedure; no new sync skill is needed.
- [ ] Local links: check docs/**/*.md, README.md, CLAUDE.md, AGENTS.md, SECURITY.md, CONTRIBUTING.md and .agents/skills/**/*.md; resolve files/directories and fragments. Document/test real inline/reference links and images, escaped/balanced/angle destinations, URL decoding, same-file/duplicate/Unicode headings, HTML anchors, source #L references and code-span/fence exclusions. Diagnose relevant unsupported forms rather than silently dropping them. External URIs are not fetched.
- [ ] Task indexes: exact T-*.md membership, duplicate detection, normalized lifecycle-status agreement; validate date_done when present and require it for newly completed tasks under the adopted convention without fabricating old dates.
- [ ] Review/ADR indexes: exact canonical membership with duplicates/missing/extra findings; distinguish companions, nested tracks, master-review runs, README/master plans. Verify ADR status/date including Deferred, prose-extended dates and partial supersession; reserved 0034 requires no file.
- [ ] Planned ADRs: validate unique live purpose definitions and resolved live references; reject tentative numeric ledger definitions. Distinguish repeated references, historical aliases, filed numeric ADRs and explicitly unallocated planning.
- [ ] Standards fences: reject untagged opening fences while accounting for fence length and closing fences.
- [ ] Unsafe audit references: every source audit-tag reference resolves to a log entry and every Active entry has an active source audit annotation; explicitly handle Removed entries and historical explanatory mentions. Do not claim Rust parsing or proof of unsafe soundness.
- [ ] Optional live-state consistency: implement only against T-047's reliable delimited section, or record a concrete reason for skipping it. Skip static commit-scope allowlisting because the standard permits prior-use scopes and review-agreed extensions; record this disposition.
- [ ] Meaningful isolated positive/negative fixtures cover every implemented check, supported grammar and false-positive control, operating in temporary roots without scratch branches or committed regressions. The stabilized whole corpus passes before CI enablement; genuine baseline defects return to their named owner rather than being suppressed. Historical exceptions follow ADR-0043's exact-destination/reason/review/fixture contract, never blanket exclusions.
- [ ] Run both checker and fixture suite as failing steps in the existing lint-and-host-test job under Accepted ADR-0043. Preserve its job/check identity, all six required contexts/app bindings and branch-protection settings. Verify exact-source macOS/local and Linux/hosted execution; Acceptance alone is not gate delivery.

## Out of scope

- Fixing the drift the checks find in the other synchronisation tasks ([T-048](T-048-phase-b-task-corpus-sync.md), [T-049](T-049-review-indices-sync.md), [T-054](T-054-adr-ledger-renumbering-cascade.md), [T-055](T-055-adr-append-only-corrections.md)); this task only prevents recurrence.
- Network checks (external URLs), spell checking, or prose linting.
- Rewriting existing skills beyond adding an index entry.

## Approach

Implement the bounded Markdown parser and link fixtures first, then add each index/ledger/fence/audit check with isolated positive and negative fixtures.
Use Python 3.9+ standard library, already supported by existing required CI tooling; syntax compilation is not a formatter/linter.
Run on the stabilized corpus and distinguish real documentation defects from parser false positives. Repair false positives with regression fixtures and return real baseline issues to their named task owners before enabling the required existing-job CI steps.
Run locally on macOS and verify Linux through exact-source hosted CI after publication; record each evidence boundary honestly.

## Definition of done

- [ ] Python 3.9-compatible syntax compilation and isolated unittest/CLI fixtures pass; independent review verifies style/maintainability against existing Python tools. No fictitious standard-library formatter/linter or undeclared package installation.
- [ ] The final whole-corpus run is green with reproducible output in task history; exact-source local/macOS and hosted/Linux results are recorded, with hosted evidence required before delivery is certified.
- [ ] Every relative link in touched Markdown resolves, and all six required contexts retain their identity/app binding.
- [ ] Scope includes tools/checker/fixture files, existing CI wiring, usage/standard documentation and necessary task/track/current/evidence/review indexes; changes beyond that require a demonstrated existing-scope reason.
- [ ] Commit follows commit-style.md (tooling scope) with Refs: ADR-0040, ADR-0043.
- [ ] Task stops at In Review for maintainer approval; optional-for-general-phase-exit status is preserved, but this selected implementation cannot close by decision or carry-forward alone.

## Design notes

- **Resolved 2026-10-12:** Accepted ADR-0043 selects Python 3.9+ stdlib, a required failing step in the existing lint job and CI enforcement as the index-consistency procedure. The static commit-scope check is skipped; the live-state check depends on a reliable delimiter.
- This task consumes these Polish items of `phase-b2.md`: link checker, index-vs-disk automation (`sync-task-index`/`sync-review-index` or CI grep), duplicate tentative ADR numbers, commit-scope drift, untagged fences, task-status vs `current.md` consistency, and the audit-tag cross-reference automation.
- A related risk the checks do not cover: a numeric claim in prose ("33 entries", "366 tests") going stale; the phase's Polish list proposes "status as of `<date>`" stamps for that instead.
- It is polish: if it is not done by the closure, [T-075](T-075-phase-b2-closure.md) records it as a carry-forward.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Draft |
| 2026-10-12 | Codex (AI agent), maintainer-approved reconciliation | Old: shell/no-Python premise, numeric collisions, narrow link/audit scope and generic language formatter/linter requirement with three prerequisites. Approved replacement: Accepted ADR-0043 Python 3.9 stdlib grammar and six check families, expanded dependencies, meaningful fixtures/syntax/independent style, optional-check dispositions and required existing-job CI with exact-source macOS/Linux evidence; optional phase-exit accounting retained, full implementation selected. See [approved preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); preparation only, status unchanged. |
| 2026-10-13 | Codex implementation coordinator | Step 11 starts after actual T-047 canonical both-round commit fd9009b; all seven prerequisites implemented/verified/two-round reviewed under Accepted ADR-0043. [Parser preflight](../../reports/2026-10-13-t056-parser-preflight.md) records bounded grammar, existing local-only corpus boundary, source inventory and the prewrite status-normalization correction to seventeen legacy date_done gaps (T-015 has a date-extended Done status, no date_done field). In Progress/all sixteen criteria unchecked; parser first, remaining checks/required wiring/exact-source hosted evidence remain Step 12. No new ADR/decision, task delivery or publication claimed. |
| 2026-10-13 | Codex parser implementation author | Step 11 adds bounded offline CLI/parser/isolated grammar and false-positive fixtures plus existing CI-guide usage. [Implementation and actual verification](../../reports/2026-10-13-t056-parser-implementation.md) separate base-plus-worktree source from future review/delivery. T-049 quoted-evidence follow-up is source-preserving and part of this step's review scope; parser corrections retain regression fixtures. In Progress/all sixteen criteria unchecked, both fresh paired rounds and Step 12/hosted gates pending; no task delivery or external publication. |
