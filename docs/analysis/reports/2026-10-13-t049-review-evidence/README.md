# T-049 retained execution and navigation evidence — 2026-10-13

Runtime captures executed clean source `0ab0ba427ae97d5233afd01dfe7205b1ae8bc0c3` before archive/report edits; UTC timestamps correspond to 2026-10-13 Europe/Istanbul. Raw bytes and metadata are retained together, with SHA-256 in each metadata record and companion report.

- [Miri raw output](miri.log) and [metadata](miri.json); [interpreted report](../2026-10-13-t049-miri-validation.md).
- [Coverage raw output](coverage.log) and [metadata](coverage.json); [interpreted report](../2026-10-13-t049-coverage-rerun.md).

Navigation evidence records historical source binding and bounded repair, not runtime execution or either fresh review round.

- [Navigation dispositions, source objects/ranges and file hashes](navigation.json).
- [Completed preparation read ledger](preflight-read-ledger.json): 35 full documents / 6,137 lines / 76 bounded chunks; preparation is not an implementation-review round.
- [Coordinator verification results](verification.json), with parser/scope limitations; [reconciliation report](../2026-10-13-t049-review-corpus-reconciliation.md). No binary, profile database or generated build artifact is retained.

The original Miri output ends with a blank line (line 543), so default `git diff --check` reports that narrow raw-output formatting warning. Raw bytes and SHA-256 remain unchanged. Non-log changes are checked separately; this record does not claim a universally clean default whitespace check.
