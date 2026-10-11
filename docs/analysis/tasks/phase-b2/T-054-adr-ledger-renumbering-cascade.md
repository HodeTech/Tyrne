# T-054 — Cascade the ADR ledger renumbering across phase files

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none (phase-level precondition: [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) `Accepted`, see the [task index](README.md))
- **Informs:** [T-056](T-056-docs-consistency-automation.md), [T-074](T-074-phase-c-readiness-sweep.md)
- **ADRs required:** none

---

## User story

As the author of a future ADR, I want the phase ledgers to assign each planned ADR a number that is unique and does not collide with a written ADR, so that "which number do I use" never needs a cascade-renumbering pass.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). Each phase file carries a ledger of *planned* ADRs with *tentative* numbers ("final numbers are assigned when the ADR is actually written"). Two problems exist. First, the plan item at `phase-b2.md` (snapshot line 226) records that Phase C's 2026-06-01 renumbering (ADR-0040…0044) was never cascaded: Phase C and Phase D both claim ADR-0042, 0043 and 0044 (`phase-c.md` ledger vs `phase-d.md` ledger). Second, the real ADR-0040 is now the Phase B.2 governance ADR, so *every* placeholder from 0040 upward is off by at least one. This is the third time the same cascade is needed (Blockers D4-001/D4-002 of the 2026-05-22 master review, the 2026-06-01 shift, now 0040).

Current ledger inventory (verify before editing): Phase C 5 rows (0040–0044), D 5 ADR rows plus one `_(none)_` row (0042–0046), E 6 (0047–0052), F 5 (0053–0057), G 5 (0058–0062), H 3 (0063–0065), I 3 (0066–0068); about 106 mentions of `ADR-004x…006x` across `phase-b2.md`, `phase-c.md`…`phase-i.md`.

## Acceptance criteria

- [ ] **Decision recorded** (see Open decisions) on numeric re-sequencing vs slug-based placeholders, in this task's review history.
- [ ] After the change no two ledger rows across all phase files carry the same number (under the slug workflow: no ledger row carries a tentative number and every slug appears once), and no ledger row carries a number that belongs to a written ADR (`ls docs/decisions/` vs `grep -n '^| ADR-' docs/roadmap/phases/*.md`). With numeric re-sequencing the target mapping is: C 0041–0045, D 0046–0050, E 0051–0056, F 0057–0061, G 0062–0066, H 0067–0069, I 0070–0072 (adjust if the inventory above has changed).
- [ ] Every prose reference to a planned ADR number inside the phase files is updated consistently with its ledger row — including cross-phase references, which must be resolved one by one because the same string means different ADRs in different files (for example `phase-d.md` quoting Phase C's "ADR-0043, roadmap C4").
- [ ] Each ledger carries a dated note: under the numeric workflow a downstream-renumbering note analogous to the one already in `phase-e.md` (§"Downstream-renumbering note"), including `phase-d.md`; under the slug workflow a note that tentative numbers were removed. The Phase C note added at kickoff is updated to match.
- [ ] `phase-b2.md`'s two mentions and `docs/decisions/README.md`'s *Numbering gaps* note are consistent with the new ledgers.
- [ ] Historical documents (reviews, dated banners in `current.md`) keep the numbers they quoted; the note in the ledger states that older documents use the old tentative numbers.
- [ ] A reproducible duplicate check exists and is recorded (a `grep`/`awk` one-liner in this task or, if [T-056](T-056-docs-consistency-automation.md) has landed, its check) and reports no duplicates (slug workflow: no duplicate slugs and no remaining tentative numbers).

## Out of scope

- Writing any of the planned ADRs.
- ADR-0034 (kernel-image section permissions): it is a reserved slot below 0040 and is not renumbered.
- The object-lifecycle ADR slot named in `phase-c.md` carry-forwards (it has no number yet).
- Folding Phase C review items into the milestones — [T-074](T-074-phase-c-readiness-sweep.md).

## Approach

Decide first (see Open decisions), then follow the matching workflow.

**Numeric workflow** (if numeric placeholders are kept). Process one phase file at a time with its own old→new mapping; do **not** run one global search-and-replace, because Phase C's and Phase D's old numbers are the same strings. After each file, grep for the old numbers inside that file to catch leftovers, then resolve cross-phase references by reading the sentence. Update the ledger rows' *Note* column with "renumbered 2026-MM-DD, was ADR-00NN" in the existing style so history stays traceable. Finish with the duplicate check across all phase files.

**Slug workflow** (if stable slugs are preferred). There is no old→new numeric mapping and no renumbering note. Replace each tentative number in a ledger row with a stable slug identifier (for example `ADR-C1 secondary-core-start`), use the same identifier in every prose reference, and add one dated note per ledger saying that tentative numbers were removed and that the real number is assigned when the ADR is written. Phase files can be done in any order because the identifiers are unique by construction. Finish by checking that each identifier appears in exactly one ledger row, that no tentative `ADR-004x…006x` number remains in any phase file, and that cross-phase references name the identifier rather than a number.

## Definition of done

- [ ] Every relative link in each touched file resolves.
- [ ] `git diff --stat` is limited to `docs/roadmap/phases/*.md`, `docs/decisions/README.md`, this task file and `docs/roadmap/current.md`.
- [ ] The duplicate check output is pasted into the review history.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) (scope `roadmap`).
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions:** (a) re-sequence numerically once more (simple; stays correct only until the next real ADR is written), or (b) replace tentative numbers in the ledgers with stable slugs (for example `ADR-C1 secondary-core-start`) and assign the number only when the ADR is written. Option (b) removes the recurring cascade permanently; it costs one larger edit now. The recommended choice is (b); the criteria above are written to hold for either.
- The ledger convention "Numbers are tentative" is already stated in every ledger; the problem is that readers (and review documents) still quote the numbers as if they were reserved.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
