# ADR-0041–0043 — Supplied review reconciliation

This report records source-verified dispositions for the maintainer's review of the Proposed ADR package and makes the required Acceptance-time and task-contract edits reviewable before implementation.

- **Date:** 2026-10-12
- **Author:** Codex (AI agent), on behalf of @cemililik
- **Review baseline:** `development` at `fb23823793b821b70f1252e16bb1b482f72fe1fe`.
- **Scope:** Proposed ADRs 0041–0043 and their [preflight plan](2026-10-12-phase-b2-track2-preflight-and-plan.md); no implementation, Accepted-ADR amendment, standard edit or task promotion.
- **State:** Reconciliation prepared and both fresh independent follow-up rounds complete; the sole Low finding is corrected and independently verified. Explicit maintainer package approval remains pending.
- **Prior review:** [Initial two-round preparation review](../reviews/code-reviews/2026-10-12-phase-b2-track2-preflight.md). Its original verdict/evidence remain historical; this supplied review and its follow-up do not erase them.
- **Authorization:** The maintainer supplied a readiness review with M/L/O findings, not an explicit Acceptance instruction. Copyright identity alone was approved separately and is unchanged.

## Source verification and dispositions

| ID | Source verification | Disposition in the revised proposal |
|----|---------------------|-------------------------------------|
| M1 | ADR-0040 Track B.2-1 implementation policy rule 4 explicitly limits the execution exception to that sequence/T-037; the proposal named its extension but promised the old-record clarification only for numbering. | Confirmed. ADR-0043 and the plan require a dated ADR-0040 rider for both Decision outcome rule 7 and implementation policy rule 4 in the same commit as 0043 Acceptance. A concrete rider is drafted in the plan; the Accepted record remains untouched pending approval. |
| M2 | T-055's sixth AC requires “index needs no edit / no anomalies”; its DoD omits the ADR index. The existing sync skill reports title/slug differences and has vocabulary narrower than the actual Deferred/partial-supersession corpus. | Confirmed live-contract conflict; the general reconciliation was already planned but needed literal scope. The plan now specifies the replacement AC, anomaly/disposition report and expanded DoD including the ADR index, sync skill and evidence/review artifacts. Step 0 applies this before T-055 implementation, after approval. |
| M3 | T-049 permits leaving dead retired-skill links with a history note and excludes other archive link repairs; neither is compatible with the selected full-corpus gate. | Confirmed. ADR-0043 explicitly rejects the note-only alternative. The plan requires verified immutable historical skill permalinks, preserved quoted paths/verdicts/measurements, bounded archive/master-plan repair ownership and the corresponding AC/Approach/Design-notes/Out-of-scope/DoD replacements. |
| L1 | Filing Proposed records 0041–0043 already occupies those identifiers; C2/C3/C4 and D1/D2 then collide with filed records. No 0044 record exists, so D3 still has only the C5 inter-ledger collision. | Confirmed in part, with that D3 distinction. ADR-0043 Context and Neutral consequences now state the temporary expanded collision set and T-054's complete migration ownership. No tentative row or filed number is changed here. |
| L2 | The old Option 4 grouped shell implementation and a packaged parser despite different costs. | Clarified. Separate Options 4 and 5 each have their own pros/cons; chosen Option 1 is unchanged. |
| L3 | ADR-0025's actual title is “ADR governance amendments: forward-reference contract, rider hygiene.” | Corrected the two abbreviated/misdescriptive reference labels in ADR-0041 and ADR-0043 to the actual title. Destinations and ADR-0025 are unchanged. |
| L4 | Literal sync-adr-index step 6 calls title/filename-slug differences reportable; 0040–0043 use descriptive titles and shorter slugs. Matching index/header text is a different comparison. | Recorded with M2. T-055 must report those differences and dispositions alongside existing metadata anomalies. Do not rename filed records, invent dates or silently suppress anomalies to claim clean comparison. |
| L5 | The standard-change procedure explicitly requires the changed standard's References to cite its motivating ADR; the original T-052 naming AC did not say so. | Added the requirement to ADR-0042's outcome/dependency chain and the plan's mandatory T-052 naming-AC replacement. testing.md remains unchanged until approval and the implementing step. |
| L6 | The initial commit grouped 0041/0042 and used a space rather than the skill example's em dash. Its English conventional subject and actual ADR trailers are present; the plan explains grouping so cross-links resolve at each checkpoint. | Documented justified presentation exception; no substantive defect or history rewrite. Keep the mutually linked proposal commit intact. Future single-record initial proposals follow the skill example. |
| O1 | write-adr permits retroactive Accepted filing only with maintainer agreement; that agreement was not supplied for this package. Current testing.md still contains its written prefix rule independently of the recovered record's status. | Recommendation: keep recovery Proposed until explicit approval. ADR-0041 now states that this status describes record approval and does not suspend the existing written rule. Acceptance remains a separate, reviewable transition. |
| O2 | The existing plan already intended 0042 Acceptance plus 0041 supersession together; it did not prescribe the hypothesized three commits leaving two contradictory Accepted ADRs. | Recommendation made explicit in both ADRs and the plan: first accept 0041 alone; then atomically accept 0042, flip 0041, add its callout and update both index rows in one commit. No committed checkpoint may leave both Accepted. |
| O3 | ADR-0040 Decision outcome rule 3 makes T-056 optional for general phase-exit accounting, just as the first implementation wave separately chose optional T-036 and required its delivered check. Policy approval is not task delivery. | Recommendation clarified: retain phase-wide optional status, fully implement/verify T-056 in this selected sequence, and require its checker on revisions containing delivered CI wiring. Acceptance alone neither enables the gate nor completes T-056. No carry-forward is selected by this plan. |

## Concrete approval and implementation boundaries

The proposed Acceptance sequence is:

1. After explicit approval and the careful re-read, accept ADR-0041's historical recovery with its index row in a separate commit.
2. Atomically accept ADR-0042, supersede ADR-0041 with the forward callout, and update both index rows; preserve the old body.
3. Accept ADR-0043 and append the dated ADR-0040 rider covering both numbered rules in that same commit, with actual relative links and the actual Acceptance date.
4. Apply the plan's mandatory literal task-contract reconciliations at Step 0, recording their old/new clauses and governing ADRs in task history before implementation starts.
5. Execute all thirteen implementation steps, including T-056 implementation and both fresh review rounds per step. No new task reaches Done through agent action.

Steps 1–4 are not performed by this proposal correction. In particular, [T-049](../tasks/phase-b2/T-049-review-indices-sync.md), [T-052](../tasks/phase-b2/T-052-standards-docs-reality-sync.md), [T-055](../tasks/phase-b2/T-055-adr-append-only-corrections.md), [ADR-0040](../../decisions/0040-phase-b2-consolidation-bridge.md), standards and workflows remain unchanged pending the package approval boundary.

O1–O3 are recommendations presented for approval, not inferred maintainer answers. The supplied review's Ready/Ready-with-follow-up verdict is a readiness assessment. It does not replace the maintainer's requested explicit new-ADR approval.

## Follow-up verification record

The coordinator verified the findings against the live task contracts, ADR-0025 rider rule, ADR-0040's two distinct rule blocks, the three ADR proposals, sync/standard-change/supersession procedures, and the C/D ledger rows. This report does not adopt the supplied approximate test count as a new measurement or rerun implementation/runtime gates for a Markdown-only correction.

Four fresh independent contexts assessed the corrected cumulative proposal in two follow-up rounds. Their source hashes, findings, dispositions and five master-plan roles are recorded in the existing preparation-review artifact. The original two rounds are preserved and are not relabeled as reviews of these new corrections.

The first follow-up round identified one residual Step 9 alternative that still allowed the ADR-0040 rider to be added later. The coordinator confirmed it against the revised mandatory Acceptance-time sequence and changed Step 9 to verification of that already-filed rider in `7ccdde49aa77b35f181349adae4425bc68eb8801`. Both first-round contexts verified the correction; both new second-round contexts reviewed the cumulative corrected proposal at that tip, found no new issue and returned Approve for proposal readiness only. There are no unresolved proposal-review findings. The recommendation/Acceptance/task-delivery boundaries above remain in force.
