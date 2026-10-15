# T-054 verification evidence

These are bounded coordinator diagnostics for [T-054](../../tasks/phase-b2/T-054-adr-ledger-renumbering-cascade.md), not independent review reports or the delivered T-056 gate.

- [semantic-baseline.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t054-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t054-verification-evidence/semantic-baseline.json"): immutable pre-content inventory of all 32 original definitions, source hashes and ambiguity resolutions at f8c9b7f34a28d0974cbc9e03f1ef8355dc2df4f3; earlier preparation is separately attributed.
- [kickoff-navigation.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t054-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t054-verification-evidence/kickoff-navigation.json"): immutable visible-corpus navigation diagnostic before content migration.
- [live-reference-migration.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t054-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t054-verification-evidence/live-reference-migration.json"): actual 71 source-line edit records, including original text, replacement and purpose resolution. Earlier preparation and actual clean/kickoff bases are separate fields.
- [verify-migration.py](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t054-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t054-verification-evidence/verify-migration.py"): source comparison; uses Python 3.9+ standard library and Git, resolves repository root from its own file and reads the recorded Git base. It reads the current worktree; optional output is the only write.
- [implementation-verification.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t054-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t054-verification-evidence/implementation-verification.json"): actual initial post-content comparison, keyed to kickoff HEAD and owned worktree hashes. It is not rewritten after review.
- [implementation-navigation.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t054-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t054-verification-evidence/implementation-navigation.json"): actual initial post-content visible-corpus navigation diagnostic. It uses the existing third-party Markdown diagnostic, not T-056's complete grammar.

- [r1-correction-verification.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t054-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t054-verification-evidence/r1-correction-verification.json") and [r1-correction-navigation.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t054-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t054-verification-evidence/r1-correction-navigation.json"): separate actual post-R1-correction captures at the implementation HEAD plus corrected worktree; the initial snapshots above remain immutable.

From any working directory, invoke the script by its path:

~~~sh
python3 docs/analysis/reports/2026-10-13-t054-verification-evidence/verify-migration.py
~~~

The example path assumes repository cwd; an absolute path works elsewhere. A fresh invocation reports the current HEAD/worktree and may include later bookkeeping paths; compare owned source hashes when reproducing the frozen content result. The optional --output /tmp/t054-comparison.json retains a separate new result. Exit status is nonzero when a comparison check fails. Missing Git objects/files or invalid evidence also fail rather than returning a green result. The source-bound semantic edit ledger is review evidence; it cannot prove that the original human meaning was interpreted correctly. Independent review checks that meaning against source.

## Canonical publication checks

- [publication-verification.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t054-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t054-verification-evidence/publication-verification.json"): separate current-worktree comparison after canonical report/lifecycle edits; reviewed content hashes remain those of a93926b.
- [publication-navigation.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t054-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t054-verification-evidence/publication-navigation.json"): fresh visible-corpus diagnostic after canonical additions, with its actual source/scope and grammar limits.
- [publication-manifest.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t054-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t054-verification-evidence/publication-manifest.json"): final actual report/prefix/capture/content hashes, lifecycle/scope and publication-check correspondence. Original snapshots above remain unchanged.

Both fresh paired rounds Approve the corrected frozen source. Full actual reports are retained in the [code artifact](../../reviews/code-reviews/2026-10-13-t054-planned-adr-identities.md) and [security artifact](../../reviews/security-reviews/2026-10-13-t054-planned-adr-identities.md). These final captures are coordinator bookkeeping, not a third review round or T-056 delivery.

> **Evidence migration (2026-10-16).** Raw evidence links now open the [immutable archive catalog](../2026-10-16-pr49-evidence-catalog.md). Each link title retains its exact archived member path. Original verdicts, measurements, limitations and execution SHA identities remain historical; the archive bundle restores their original source.
