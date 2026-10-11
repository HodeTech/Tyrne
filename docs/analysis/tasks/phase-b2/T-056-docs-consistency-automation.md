# T-056 — Automate docs-corpus consistency checks (polish; optional for exit)

- **Phase:** B.2
- **Milestone:** Track B.2-2 (Polish items; not exit-gating)
- **Status:** Draft
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-048](T-048-phase-b-task-corpus-sync.md), [T-049](T-049-review-indices-sync.md), [T-054](T-054-adr-ledger-renumbering-cascade.md)
- **Informs:** none
- **ADRs required:** an ADR (or a revision-note rider on the ADR that motivated the CI standard, found per [`propose-standard-change`](../../../../.agents/skills/propose-standard-change/SKILL.md) step 2) recording the merge-blocking-versus-advisory decision, `Accepted` before any CI step lands; none if the script stays a local-only tool

---

## User story

As the maintainer, I want the documentation drift that two full-tree reviews found by hand to be detected by a small offline script, so that index gaps, broken links and duplicate ADR numbers are caught on the pull request that introduces them.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). Four of the documentation findings in Track B.2-2 of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) are recurrences of items the 2026-05-22 master review had already fixed (Blockers D4-001, D4-002, D4-003, D4-005 and Major D4-004): ADR-number collisions between phase ledgers, a stale `current.md`, a task index missing tasks, task files stuck at `In Review`. They recur because each fix was made by hand and nothing checks it. The Polish list in `phase-b2.md` asks for the same checks to be mechanised: a relative-link checker, index-versus-disk reconciliation, detection of duplicate tentative ADR numbers, commit-scope drift, untagged fences, task-status versus `current.md` consistency, and the audit-tag cross-check that the last review did by hand (33 of 33 tags matched in both directions). This task is optional for the Phase B.2 exit and depends on the three synchronisation tasks so that the checks start green.

## Acceptance criteria

- [ ] One script under `tools/` (shell unless the design decision below picks otherwise; `shellcheck`-clean once [T-031](T-031-ci-userland-clippy-and-shellcheck.md) has landed) runs offline and deterministically, exits non-zero on any finding, and prints one line per finding with `file:line`.
- [ ] It implements these checks: (a) every relative Markdown link in `docs/**/*.md`, `README.md`, `CLAUDE.md`, `SECURITY.md`, `CONTRIBUTING.md` resolves; (b) each task folder's `README.md` index lists exactly the `T-*.md` files on disk with matching statuses, and the review-family and ADR indices list exactly the files on disk; (c) no two tentative ADR numbers in the phase ledgers coincide and none collides with a written ADR; (d) no opening code fence in `docs/standards/` is untagged; (e) every `UNSAFE-YYYY-NNNN` tag in source resolves to an entry in `docs/audits/unsafe-log.md` and every entry has a source use, in both directions.
- [ ] Optional checks, each either implemented or recorded as skipped with the reason: a task that `current.md` calls `Done` whose own `Status` is not `Done`; commit subjects whose scope is missing from the documented list in `commit-style.md`.
- [ ] Each implemented check starts green on the tree as it stands after T-048, T-049 and T-054, and has a recorded negative test: a deliberate defect in a scratch copy (a broken link, a task missing from an index, a duplicated ledger number, an untagged fence, an orphan audit tag) makes it fail.
- [ ] The script and its checks are documented (usage, exit codes, how to add a check) in `docs/guides/ci.md` or `docs/standards/infrastructure.md`. If a CI gate is selected, the documentation also states its status (`Required` or `Advisory` per the decision below, or `Planned` until the CI step lands); if the script stays a local-only tool, the documentation states that no CI gate exists and the decision is recorded in this task's review history.
- [ ] **Decision recorded:** whether the script runs as a merge-blocking CI step (for example in `lint-and-host-test`), as an advisory CI step, or as a local-only tool. Wiring it into CI in either form changes the CI gate policy, so the decision is recorded in the ADR named in *ADRs required* and that ADR is `Accepted` before the CI step lands; a local-only tool is recorded in this task's review history. If blocking, `docs/guides/ci.md` and `infrastructure.md` list it under required gates (if advisory, under advisory gates).
- [ ] A procedure for keeping indices in step exists: either a `sync-task-index` / `sync-review-index` skill under `.agents/skills/` (indexed in its `README.md`) or, if a CI step was selected, that CI step; record which.

## Out of scope

- Fixing the drift the checks find in the other synchronisation tasks ([T-048](T-048-phase-b-task-corpus-sync.md), [T-049](T-049-review-indices-sync.md), [T-054](T-054-adr-ledger-renumbering-cascade.md), [T-055](T-055-adr-append-only-corrections.md)); this task only prevents recurrence.
- Network checks (external URLs), spell checking, or prose linting.
- Rewriting existing skills beyond adding an index entry.

## Approach

Start with the cheapest high-value checks (link resolution, index-versus-disk) and add the rest one at a time, each with its negative test. Keep the script small and dependency-free (`grep`, `awk`, `find`, `sed` — the repository has no Python tooling today); if one check needs a real parser, say so in the design decision rather than adding a dependency silently. Run it first on the post-T-048/T-049/T-054 tree, fix the checker (not the docs) if it reports false positives, and only then wire it into CI.

## Definition of done

- [ ] If the shell implementation is chosen: `shellcheck` clean and the script runs on both macOS and Linux (no GNU-only flags without a fallback — the maintainer's machine is macOS, CI is Ubuntu). If another language is chosen: that language's standard formatter/linter is clean, the script runs on both macOS and Linux, and any new dependency is named in the recorded design decision.
- [ ] The script's own run on the final tree is green; its output is pasted into the review history.
- [ ] Every relative link in each touched Markdown file resolves.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) (scope `tooling`) with `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions:** script language (shell vs another language — shell is preferred because nothing else is installed in CI for docs); merge-blocking vs advisory; skill vs CI step for index sync.
- This task consumes these Polish items of `phase-b2.md`: link checker, index-vs-disk automation (`sync-task-index`/`sync-review-index` or CI grep), duplicate tentative ADR numbers, commit-scope drift, untagged fences, task-status vs `current.md` consistency, and the audit-tag cross-reference automation.
- A related risk the checks do not cover: a numeric claim in prose ("33 entries", "366 tests") going stale; the phase's Polish list proposes "status as of `<date>`" stamps for that instead.
- It is polish: if it is not done by the closure, [T-075](T-075-phase-b2-closure.md) records it as a carry-forward.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Draft |
