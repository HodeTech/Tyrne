# T-054 verification evidence

These are bounded coordinator diagnostics for [T-054](../../tasks/phase-b2/T-054-adr-ledger-renumbering-cascade.md), not independent review reports or the delivered T-056 gate.

- [semantic-baseline.json](semantic-baseline.json): immutable pre-content inventory of all 32 original definitions, source hashes and ambiguity resolutions at f8c9b7f34a28d0974cbc9e03f1ef8355dc2df4f3; earlier preparation is separately attributed.
- [kickoff-navigation.json](kickoff-navigation.json): immutable visible-corpus navigation diagnostic before content migration.
- [live-reference-migration.json](live-reference-migration.json): actual 71 source-line edit records, including original text, replacement and purpose resolution. Earlier preparation and actual clean/kickoff bases are separate fields.
- [verify-migration.py](verify-migration.py): source comparison; uses Python 3.9+ standard library and Git, resolves repository root from its own file and reads the recorded Git base. It reads the current worktree; optional output is the only write.
- [implementation-verification.json](implementation-verification.json): actual initial post-content comparison, keyed to kickoff HEAD and owned worktree hashes. It is not rewritten after review.
- [implementation-navigation.json](implementation-navigation.json): actual initial post-content visible-corpus navigation diagnostic. It uses the existing third-party Markdown diagnostic, not T-056's complete grammar.

- [r1-correction-verification.json](r1-correction-verification.json) and [r1-correction-navigation.json](r1-correction-navigation.json): separate actual post-R1-correction captures at the implementation HEAD plus corrected worktree; the initial snapshots above remain immutable.

From any working directory, invoke the script by its path:

~~~sh
python3 docs/analysis/reports/2026-10-13-t054-verification-evidence/verify-migration.py
~~~

The example path assumes repository cwd; an absolute path works elsewhere. A fresh invocation reports the current HEAD/worktree and may include later bookkeeping paths; compare owned source hashes when reproducing the frozen content result. The optional --output /tmp/t054-comparison.json retains a separate new result. Exit status is nonzero when a comparison check fails. Missing Git objects/files or invalid evidence also fail rather than returning a green result. The source-bound semantic edit ledger is review evidence; it cannot prove that the original human meaning was interpreted correctly. Independent review checks that meaning against source.
