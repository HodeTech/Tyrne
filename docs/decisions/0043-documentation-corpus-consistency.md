# 0043 — Documentation corpus consistency and planned ADR identities

- **Status:** Proposed
- **Date:** 2026-10-12
- **Deciders:** @cemililik

## Context

[Track B.2-2](../roadmap/phases/phase-b2.md#track-b2-2--documentation-cascade-phase-b-closure) owns the post-Phase-B documentation cascade under [ADR-0040](0040-phase-b2-consolidation-bridge.md).
At source `7d48f50603fa0d30464ea7b032f4f0fb82c3964c`, its tasks reproduce repeated task/review index drift, stale live roadmap pointers and collisions between tentative ADR numbers in different phase ledgers.
There are 32 numbered planned-decision rows across Phases C–I, including two separate F2 decisions; three numbers collide between C and D, and C's tentative 0040 collides with the filed governance ADR.
Filing this proposal package also occupies 0041–0043, even while Proposed: C2/C3/C4's tentative 0041/0042/0043 and D1/D2's tentative 0042/0043 now collide with filed records.
D3's tentative 0044 still collides with C5 but has no filed ADR at this checkpoint.
[T-054](../analysis/tasks/phase-b2/T-054-adr-ledger-renumbering-cascade.md) explicitly offers stable purpose identifiers as an alternative to another numeric cascade.
[T-056](../analysis/tasks/phase-b2/T-056-docs-consistency-automation.md) offers local, advisory or required automation, with an Accepted decision required before either CI option.

The original task brief's assumption that the repository has no Python tooling is obsolete: the existing required lint job already runs standard-library Python policy and regression tools.
The current six required GitHub Actions contexts are versioned in [main.json](../../.github/branch-protection/main.json); introducing another status context or an administrative workflow is unnecessary for this check.
The corpus contains historical snapshots and quoted defects, so a checker must distinguish live claims from history and parse Markdown deliberately instead of applying a global regex to every occurrence.

This proposal adds a documentation-maintenance policy and chooses T-054's existing stable-identifier option.
It does not narrow the whole-phase scope, open Phase C/D, or change ADR-0040's outcome.
In the same commit that accepts this ADR, append a dated rider to ADR-0040 covering both Decision outcome rule 7's historical numeric-cascade wording and Track B.2-1 implementation policy rule 4's explicitly limited stacked-execution exception.
The rider points to this ADR's purpose-identity choice and Track B.2-2-only execution extension; ADR-0040's original body, filed number, status and whole-phase outcome remain intact.

## Decision drivers

- Stop the third recurrence of tentative-number collisions without renumbering filed ADRs.
- Catch mechanical drift on the PR that introduces it, while preserving historical evidence and verdicts.
- Reuse existing CI runtime and required-check identity, with no new third-party dependency or credential.
- Make the checker deterministic, offline, portable and testable with isolated positive and negative fixtures.
- Define exactly what is checked; tag/link consistency does not prove architectural truth or Rust memory safety.
- Keep dependent work executable on `development` while maintainer review owns final completion.

## Considered options

1. **Stable planned-decision identifiers plus a required offline Python check in the existing lint job.** Eliminate numeric placeholders and gate bounded mechanical consistency.
2. **Another numeric cascade plus local-only checking.** Keep tentative numbers and let contributors run an optional tool.
3. **Stable identifiers plus advisory CI checking.** Report drift remotely without failing a required job.
4. **A shell implementation.** Keep the command in shell while implementing the same bounded parsing and index contracts.
5. **A third-party Markdown parser.** Reuse a packaged parser while retaining the same consistency policy.

## Decision outcome

Chosen option, subject to approval: **Option 1 — stable identifiers and required offline consistency checking**.

### Planned ADR identity

Use a stable, purpose-specific identifier such as `ADR-C1-secondary-core-start` or `ADR-F2-spi-service` for each live planned-decision ledger row.
The identifier includes the milestone and a semantic slug; two decisions in one milestone receive different slugs.
It is a planning identifier, not a filed ADR number, filename, status or authorization to implement that future phase.
Assign the actual four-digit ADR number only when the record is written, following [write-adr](../../.agents/skills/write-adr/SKILL.md).
At filing, preserve the purpose identifier as a historical alias and connect its ledger row to the real ADR.

T-054 migrates all 32 existing numbered rows and their live prose references by meaning, with one unique definition per purpose and links to its ledger location.
Real references to filed ADRs, especially ADR-0040, remain numeric.
The reserved ADR-0034 slot remains reserved.
Explicitly unnumbered decisions, including the object-lifecycle, G1.5 and Phase J work, remain discoverable as unallocated planning; their existence is not an invalid numeric placeholder.
Dated old numeric aliases remain historical and do not reserve numbers.

### Tool and gate

Implement T-056 as a Python 3.9+ standard-library command under `tools/` with no third-party package, network request or repository-setting write.
Use explicit UTF-8, a script-relative default repository root with a fixture-root override, sorted traversal and `file:line` findings.
Exit zero only when all selected checks succeed; invalid input or inconsistent content exits nonzero.
Run the checker and its isolated fixture suite as failing steps inside the existing `lint-and-host-test` job.
Keep that job's check name, the six required contexts and their app bindings intact.
No live branch-protection mutation is needed.

The required checks are:

1. **Local Markdown links:** resolve file/directory targets and fragments in `docs/**/*.md` and root `README.md`, `CLAUDE.md`, `AGENTS.md`, `SECURITY.md` and `CONTRIBUTING.md`; also check Markdown skill files under `.agents/skills/`, because this track refreshes their instructions and links.
2. **Task indexes:** compare the phase-local index's task rows with actual `T-*.md` files, reject missing/extra/duplicate rows and compare normalized lifecycle statuses. Validate `date_done` when present and require it for newly completed tasks covered by the adopted template convention; do not invent historical completion dates.
3. **Review and ADR indexes:** reconcile canonical report/record membership with the appropriate family index, and reject missing/extra/duplicate entries. Preserve the distinction between canonical reviews, companion plans, nested track reports, master-review runs, README files and master plans. Verify ADR status and date against the record, including the existing Deferred and partial-supersession forms; reserve 0034 without requiring a file.
4. **Planned ADR definitions:** require unique live purpose identifiers, resolve their live references and reject tentative numeric ledger definitions that collide with filed ADRs or continue the removed numbering workflow. Count definitions separately from repeated prose references.
5. **Standard fences:** reject untagged opening fences in `docs/standards/`, accounting for fence length and closing fences.
6. **Unsafe audit tags:** every source audit-tag reference resolves to an actual log entry; every Active entry has an active source audit annotation. Removed entries and explanatory historical mentions receive explicit treatment. This is reference reconciliation, not a Rust parser proving every unsafe block is audited or sound.

Document the Markdown grammar supported by the tool and test real repository forms: inline and reference links, images, escaped/balanced destinations, angle-bracket destinations, URL decoding, same-file fragments, duplicate heading suffixes, Unicode, explicit HTML anchors, and code-span/fence exclusion.
External URI destinations are not fetched.
Source `#L…` fragments are source-line references, not Markdown heading identifiers.
Recognized local-link forms must not be silently discarded to obtain a green result; diagnose unsupported relevant forms or extend the parser with a regression fixture.

The optional live-state check is implemented only against an explicitly delimited current-state section established by T-047; dated archives are excluded from live status interpretation but retain link checking.
If that surface cannot support a reliable check, record the optional check as skipped with a concrete reason.
Skip a static commit-scope allowlist: the current standard permits prior-use scopes and review-agreed extensions, which a static list cannot adjudicate honestly.
This is not a new commitlint policy.

### Baseline repair and historical evidence

T-048 repairs the known Phase-A/B task links; T-049 owns review-index synchronization and a bounded mechanical repair of additional broken review links found by the full-corpus scan.
Repair live navigation to current targets.
Review-archive Markdown links into the retired `.claude/skills/` tree must use verified immutable historical commit permalinks that contain the cited target.
T-049's original note-only alternative is incompatible with this gate and is removed during its pre-implementation contract reconciliation; a history note does not resolve a dead destination.
For other historically removed source targets, prefer a verified immutable historical commit permalink when pointing at the current file would change the evidence.
Quoted old paths remain quoted data, and review findings, verdicts, measurements and provenance are not rewritten.
Any unavoidable exception must identify the exact document, destination and reason, be reviewable and have a fixture; no archive-wide exclusion is permitted.
The intended initial release has no unreviewed broken-link exception.

T-055 also reconciles the ADR index's existing descriptive-title and metadata conventions against actual headers, reporting the baseline anomalies explicitly rather than claiming a strict clean comparison prematurely.
Before T-055 implementation, replace its unconditional “index needs no edit / no anomalies” AC with source-based index reconciliation and an explicit anomaly/disposition report, and add `docs/decisions/README.md` and the sync skill to its allowed scope.
Report title/filename-slug differences, including 0040–0043, without renaming filed records or claiming that a matching index/header removes those differences.
Support the template's existing Deferred vocabulary and the historical partial-supersession status without changing the meaning of either record.
Syntax compilation and fixture execution are required for the Python tool; independent review checks formatting and maintainability against the existing Python tools.
There is no claimed standard-library Python formatter or linter and no package installation hidden behind this choice.

### Reviewed execution on one branch

For this maintainer-requested Track B.2-2 sequence, a dependent task may start once its prerequisite implementation, applicable verification and both fresh independent review rounds pass on `development`.
The prerequisite remains `In Review` until maintainer approval/merge; this extends ADR-0040's explicitly limited Track B.2-1 stacked-execution exception to this Track B.2-2 sequence only.
The [preflight and step plan](../analysis/reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) names task ownership, acceptance-criterion reconciliations and validation.
No agent promotes the new tasks to Done.
Scope or ADR decisions materially different from this proposal return to the maintainer before dependent implementation.

### Simulation

Not applicable — this ADR settles documentation and CI policy; there is no kernel state machine to simulate.

### Dependency chain

1. Explicit maintainer Acceptance after the [write-adr](../../.agents/skills/write-adr/SKILL.md) careful re-read; in that same commit, append the ADR-0040 rider for Decision outcome rule 7 and Track B.2-1 implementation policy rule 4. Reconcile the affected task contracts before their implementation, as specified in the approved plan.
2. [T-048](../analysis/tasks/phase-b2/T-048-phase-b-task-corpus-sync.md) and [T-049](../analysis/tasks/phase-b2/T-049-review-indices-sync.md) reconcile task/review indexes and baseline links.
3. [T-055](../analysis/tasks/phase-b2/T-055-adr-append-only-corrections.md) reconciles the existing ADR metadata anomalies with append-only record corrections.
4. [T-052](../analysis/tasks/phase-b2/T-052-standards-docs-reality-sync.md) and [T-053](../analysis/tasks/phase-b2/T-053-standards-docs-mechanical-fixes.md) make standards truthful and opening fences tagged.
5. [T-054](../analysis/tasks/phase-b2/T-054-adr-ledger-renumbering-cascade.md) establishes purpose identities and repairs live references.
6. [T-047](../analysis/tasks/phase-b2/T-047-roadmap-state-and-phase-index-sync.md) separates live roadmap state from historical snapshots.
7. [T-056](../analysis/tasks/phase-b2/T-056-docs-consistency-automation.md) implements the checker, isolated fixtures, usage documentation and required CI step after the corpus starts green. Verify it on macOS locally and Linux in hosted CI.

The decision takes effect on Acceptance; the operational gate is delivered and verified by T-056, not by filing or accepting this record alone.
It is required on source revisions containing the delivered CI wiring; default-branch enforcement follows that wiring's merge.
This does not change ADR-0040 Decision outcome rule 3: T-056 remains optional for phase-exit accounting in general.
This requested sequence selects implementation, including all T-056 verification, and does not select a carry-forward or permit a decision-only completion.

## Consequences

### Positive

- Filed ADRs no longer invalidate unrelated future planning identifiers.
- Mechanical index, link, fence and audit-reference drift fails an existing required check.
- Local and hosted verification use the same offline command and isolated fixtures.
- Historical evidence stays attributable instead of being rewritten to resemble current implementation.

### Negative

- A custom bounded Markdown parser needs maintenance. Mitigate with a documented grammar, real-corpus positive fixtures and one negative fixture per check, including false-positive controls.
- Baseline repair exceeds the original three automation prerequisites. Give those repairs explicit ownership in T-049/T-055 and complete them before enabling the gate.
- A documentation defect can block the existing lint job. We accept this because the chosen gate protects mechanically verifiable repository contracts; it does not gate prose style or external service availability.
- Python is needed by contributors running the command. Existing CI/tooling already uses it; document the interpreter requirement and test supported macOS/Linux execution rather than adding an undeclared parser dependency.
- Historical aliases complicate validation. Parse live definitions and explicit historical context rather than banning every old numeric string.

### Neutral

- Kernel/userland behavior, unsafe code, performance policy and classic branch-protection settings are unaffected by this policy.
- Correctness work outside this track, including HIGH T-038 and ADR-0040's later scope checkpoint, retains its own ownership.
- Optional T-056 is deliberately included in this requested implementation, without making all Phase-B.2 polish items mandatory.
- Filing the proposal package temporarily increases filed-number collisions in the untouched tentative ledgers; T-054 migrates every affected live definition/reference before the consistency gate is enabled.

## Pros and cons of the options

### Option 1 — Stable identities and required Python checking

- Pro: addresses both recurring identity drift and mechanical corpus drift at their point of introduction.
- Pro: uses an existing runtime and required job without new privileges or package dependencies.
- Con: needs parser/fixture maintenance and a clean baseline before rollout.

### Option 2 — Numeric cascade and local checking

- Pro: small immediate ledger edit and no new PR gate.
- Con: the next filed ADR can recreate the collision; local checking depends on authors remembering to run it.

### Option 3 — Stable identities and advisory CI

- Pro: removes number collisions and makes consistency reports visible without blocking work.
- Con: a green required suite could still merge the exact drift this track is intended to prevent.

### Option 4 — Shell implementation

- Pro: shell already runs the repository's build and smoke commands and needs no Python-specific command entry point.
- Con: balanced links, Unicode anchors and structured indexes would require substantial custom parsing or reliance on platform-specific utilities, making the same portable fixture contract harder to maintain.

### Option 5 — Third-party Markdown parser

- Pro: a mature parser can supply a larger tested Markdown grammar and reduce custom tokenization work.
- Con: adds packaging, versioning and dependency-review cost beyond the existing standard-library tool environment. Reconsider only if concrete unsupported corpus forms make the bounded implementation inadequate, with a new explicit decision before adoption.

## References

- [ADR-0013 — Roadmap and planning](0013-roadmap-and-planning.md).
- [ADR-0025 — ADR governance amendments: forward-reference contract, rider hygiene](0025-adr-governance-amendments.md).
- [ADR-0040 — Phase B.2 governance](0040-phase-b2-consolidation-bridge.md).
- [T-054 — Planned ADR identities](../analysis/tasks/phase-b2/T-054-adr-ledger-renumbering-cascade.md).
- [T-056 — Consistency automation](../analysis/tasks/phase-b2/T-056-docs-consistency-automation.md).
- [Existing Python policy tooling](../../tools/branch-protection.py).
- [Existing CI workflow](../../.github/workflows/ci.yml).
- [Versioned required-check policy](../../.github/branch-protection/main.json).
- [Documentation standard](../standards/documentation-style.md).
- [Preflight and step plan](../analysis/reports/2026-10-12-phase-b2-track2-preflight-and-plan.md).
