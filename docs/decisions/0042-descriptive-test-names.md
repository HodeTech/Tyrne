# 0042 — Descriptive test names without a mandatory prefix

- **Status:** Proposed
- **Date:** 2026-10-12
- **Deciders:** @cemililik

## Context

This ADR proposes to supersede [ADR-0041 — Test-name prefix policy: historical recovery](0041-test-name-prefix-policy-recovery.md) **after that recovery has been explicitly accepted**.
The earlier written rule requires a `test_` prefix, but the shipped test corpus uses descriptive, unprefixed names.
The mismatch reproduces at source `7d48f50603fa0d30464ea7b032f4f0fb82c3964c`; real examples in [the IPC tests](../../kernel/src/ipc/mod.rs) include `send_without_send_right_fails`, `recv_without_recv_right_fails`, and `send_with_wrong_object_kind_returns_wrong_object_kind`.
The prefix requirement provides no additional description of the tested behavior, and adopting it now would churn source and test filters.

[T-052](../analysis/tasks/phase-b2/T-052-standards-docs-reality-sync.md) asks the maintainer to choose between documenting the in-use convention and renaming/enforcing the historical prefix convention.
This record proposes the former as a normative rule change, not a typo fix.
It changes no test behavior, test-layer requirements, or coverage policy.

## Decision drivers

- A failing test name should identify the subject, relevant condition and expected result.
- The naming standard should be usable by contributors and reflected in actual examples.
- Avoid a source-wide rename whose only effect is a redundant prefix.
- Keep enforcement claims accurate: naming remains a review obligation, not a claimed Clippy or CI naming rule.

## Considered options

1. **Use descriptive names without a mandatory prefix**, retaining the subject/condition/outcome guidance and real examples.
2. **Adopt the historical `test_` prefix**, rename the corpus and add a naming check.
3. **Remove naming guidance entirely**, leaving each author to choose.

## Decision outcome

Chosen option, subject to approval: **Option 1 — descriptive names without a mandatory prefix**.

Document `<subject>_<condition>_<expected_outcome>` as a naming guide, using the three real IPC names above as examples.
Use ordinary Rust `snake_case`; concise names are acceptable when the behavior is already unambiguous.
The three descriptive components are guidance, not a requirement for a mechanically fixed number of underscore-separated words.
Review checks whether the name explains the behavior.
No naming-prefix lint, mass rename, or retrospective rejection of historical prefixed names is introduced.

After explicit maintainer approval, first accept ADR-0041's historical recovery in its own commit.
Then, in one atomic supersession commit, accept this ADR, change ADR-0041 to `Superseded by 0042`, add its forward callout and update both index rows.
Do not commit this ADR as Accepted while ADR-0041 remains Accepted.
Only after that transition may T-052 replace the standard's pattern and examples.
That standard edit must also add a References entry linking this ADR, as required by the standard-change procedure.

### Simulation

Not applicable — this ADR settles a naming convention; there is no runtime state machine to simulate.

### Dependency chain

1. [ADR-0041](0041-test-name-prefix-policy-recovery.md) records the implicit historical rule and must be Accepted before its supersession.
2. Explicit maintainer approval and the [write-adr](../../.agents/skills/write-adr/SKILL.md) careful re-read precede this ADR's Acceptance.
3. [T-052](../analysis/tasks/phase-b2/T-052-standards-docs-reality-sync.md) changes the test-naming section, adds this ADR to the standard's References and searches downstream standards, skills and architecture documents.
4. [T-053](../analysis/tasks/phase-b2/T-053-standards-docs-mechanical-fixes.md) reconciles tagged fences in the same standard; the two tasks coordinate the shared file.

## Consequences

### Positive

- The standard teaches the convention contributors encounter in the source.
- Examples are executable test identifiers rather than invented scenarios.
- Test behavior and existing filters retain their identities.

### Negative

- Name quality remains a review judgment. We accept that cost because a prefix check cannot establish behavioral clarity.
- A simple prefix search no longer identifies every test. Use Rust test attributes and test-runner discovery instead; both already identify tests independently of their names.

### Neutral

- Historical names remain valid; this is guidance for new and edited tests.
- All existing test, regression, syscall-smoke and error-path obligations remain in force.

## Pros and cons of the options

### Option 1 — Descriptive names

- Pro: matches actual practice and makes the name's information content the review criterion.
- Pro: needs a small standard edit and no runtime or test-filter migration.
- Con: semantic clarity cannot be reduced to a prefix check.

### Option 2 — Mandatory prefix and enforcement

- Pro: gives a simple syntactic convention with mechanical enforcement.
- Con: requires widespread churn and a checker while leaving name quality a review judgment.

### Option 3 — No naming guidance

- Pro: removes a convention that is not mechanically enforced.
- Con: loses useful expectations for diagnosing failures and reviewing regression tests.

## References

- [ADR-0041 — Historical prefix rule](0041-test-name-prefix-policy-recovery.md).
- [T-052 — Standards claims and reality](../analysis/tasks/phase-b2/T-052-standards-docs-reality-sync.md).
- [Testing standard](../standards/testing.md).
- [Real IPC regression and rights tests](../../kernel/src/ipc/mod.rs).
- [Propose standard change](../../.agents/skills/propose-standard-change/SKILL.md).
