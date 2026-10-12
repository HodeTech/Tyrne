# 0041 — Test-name prefix policy: historical recovery

- **Status:** Superseded by 0042
- **Date:** 2026-10-12
- **Deciders:** @cemililik

> **Superseded by [ADR-0042: Descriptive test names without a mandatory prefix](0042-descriptive-test-names.md) (2026-10-12).** The original decision below is preserved for the historical record.

## Context

This is a **retroactive recovery of an existing written standard**, not a claim that the maintainer previously accepted an ADR for it.
At source `7d48f50603fa0d30464ea7b032f4f0fb82c3964c`, [testing.md §Test naming](../standards/testing.md#test-naming) prescribes `test_<subject>_<condition>_<expected_outcome>` and gives three prefixed examples.
The rule has no identified motivating ADR, and the implemented tests use descriptive names without that prefix.
[T-052](../analysis/tasks/phase-b2/T-052-standards-docs-reality-sync.md) must resolve the mismatch.

The [standard-change procedure](../../.agents/skills/propose-standard-change/SKILL.md) requires recovering an implicit decision before superseding it.
This record captures only the historical prefix rule; [ADR-0042](0042-descriptive-test-names.md) proposes its replacement.
Both records remain Proposed pending explicit maintainer approval.
Proposed describes this ADR record's approval state; it does not suspend the existing written rule in testing.md, which continues to apply while the replacement remains Proposed.
Neither this proposal nor its historical framing authorizes a mass rename or a change to the standard.

## Decision drivers

- Preserve the provenance of a normative rule before replacing it.
- Distinguish written policy from observed adoption: the historical standard is evidence of the former, not the latter.
- Keep the recovery separate from the replacement so the transition is reviewable.
- Avoid inventing a past approval, naming lint, or implementation effort.

## Considered options

1. **Recover the existing prefix rule in a dedicated ADR**, then decide its replacement separately.
2. **Treat removal of the prefix as an ordinary factual correction**, leaving the implicit rule without a decision record.
3. **Keep the rule and rename the tests**, making the implementation adopt the written prefix convention.

## Decision outcome

Chosen option, subject to approval: **Option 1 — recover the historical rule separately**.

The recovered rule is: test names follow `test_<subject>_<condition>_<expected_outcome>`; condition and outcome should explain the behavior a failure identifies.
There is no recovered claim of automated naming enforcement or demonstrated adoption.
This record does not recover unrelated testing requirements.

If the maintainer approves the proposed replacement, record this recovery as Accepted in a separate commit from its initial proposal.
In the next transition commit, atomically accept ADR-0042, mark this record `Superseded by 0042`, add its forward callout and update both index rows, preserving this body.
There must be no committed checkpoint with both contradictory records Accepted.
The replacement becomes effective before T-052 edits the standard.
If the replacement is rejected, do not silently implement it or claim this recovery resolved the adoption gap.

### Simulation

Not applicable — this ADR recovers a process rule; there is no runtime state machine to simulate.

### Dependency chain

1. The existing [testing standard](../standards/testing.md#test-naming) supplies the historical rule being recovered.
2. Explicit maintainer approval and the careful re-read required by [write-adr](../../.agents/skills/write-adr/SKILL.md) precede Acceptance.
3. [ADR-0042](0042-descriptive-test-names.md) owns the proposed replacement and supersession transition.
4. [T-052](../analysis/tasks/phase-b2/T-052-standards-docs-reality-sync.md) owns the resulting standard edit and downstream-effects search.

## Consequences

### Positive

- The old rule has a citable record and a visible successor instead of disappearing in a prose edit.
- Historical recovery is explicitly distinguished from historical maintainer approval.
- A naming-policy change can be assessed separately from unrelated CI or runtime behavior.

### Negative

- Two ADRs are needed for a small rule change. We accept this cost because the standard-change procedure explicitly requires recovery followed by supersession.
- An Accepted recovery could be mistaken for a request to rename tests. The transition instructions and successor pointer make the intended sequence explicit; no rename is authorized by this proposal.

### Neutral

- Source code, test filters, test counts and CI behavior do not change when this historical record is filed.
- The initial proposal and subsequent status transitions are separate commits.

## Pros and cons of the options

### Option 1 — Dedicated recovery

- Pro: follows the existing standard-change procedure and preserves both sides of the policy transition.
- Pro: makes the lack of adoption and prior ADR approval explicit.
- Con: adds an ADR whose useful lifetime as an Accepted current rule may be very short.

### Option 2 — Factual correction only

- Pro: the smallest edit and immediate alignment with existing test names.
- Con: removes a normative requirement without the recovery and supersession required by the project procedure.

### Option 3 — Rename the tests

- Pro: preserves the existing written naming rule and creates consistent prefix adoption.
- Con: creates broad source/filter churn for a prefix that adds no behavioral information; any new naming enforcement still needs its own design and validation.

## References

- [T-052 — Standards claims and reality](../analysis/tasks/phase-b2/T-052-standards-docs-reality-sync.md).
- [Testing standard — Test naming](../standards/testing.md#test-naming).
- [Propose standard change](../../.agents/skills/propose-standard-change/SKILL.md).
- [Supersede ADR](../../.agents/skills/supersede-adr/SKILL.md).
- [ADR-0025 — ADR governance amendments: forward-reference contract, rider hygiene](0025-adr-governance-amendments.md).
- [ADR-0042 — Proposed descriptive naming policy](0042-descriptive-test-names.md).
