# T-047 verification evidence

- [semantic-baseline.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t047-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t047-verification-evidence/semantic-baseline.json"): actual clean source, original dated-group/preamble/tail hashes, full Git integration records and first-status unsafe inventory. Metadata only, not unsafe re-audit or delivery.

Original source and later snapshots remain separately attributable. The archive stays beside current.md so original relative paths retain their meaning. Further captures are added only when actually produced.

- [verify-roadmap.py](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t047-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t047-verification-evidence/verify-roadmap.py"): bounded source/history diagnostic, Python 3.9+ stdlib/Git, root from its own location; optional explicit output is its only write.
- [implementation-verification.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t047-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t047-verification-evidence/implementation-verification.json"): original actual post-content comparison, kickoff HEAD plus worktree hashes; retained unchanged after review.
- [implementation-navigation.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t047-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t047-verification-evidence/implementation-navigation.json"): actual visible-corpus navigation capture using the existing third-party diagnostic, with explicit grammar/source limits.

From repository cwd:

~~~sh
python3 docs/analysis/reports/2026-10-13-t047-verification-evidence/verify-roadmap.py
~~~

An absolute script path works from another cwd. Use --output /tmp/t047-comparison.json for a separate fresh result; do not overwrite original snapshots. Comparison errors or invalid/missing source fail nonzero. This is an intentionally step-bound diagnostic, not general T-056 functionality: later owning edits can legitimately change its frozen content, so reproduce historical results on the recorded source and compare the owned hashes. It inventories audit metadata, not source annotations or Rust soundness. Navigation uses the existing third-party diagnostic rather than proving complete Markdown grammar.

- [publication-manifest.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t047-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t047-verification-evidence/publication-manifest.json"): actual completed four-report identities/initial-prefix retention, unchanged original captures and archive/B/C source, explicit later live-state lifecycle transition; coordinator verification, not a third independent round.
- [publication-verification.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t047-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t047-verification-evidence/publication-verification.json"): separate actual final source/history comparison after authorized In Review bookkeeping.
- [publication-navigation.json](../2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t047-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t047-verification-evidence/publication-navigation.json"): separate actual final visible-corpus navigation with the same third-party/approximate grammar limits.

> **Evidence migration (2026-10-16).** Raw evidence links now open the [immutable archive catalog](../2026-10-16-pr49-evidence-catalog.md). Each link title retains its exact archived member path. Original verdicts, measurements, limitations and execution SHA identities remain historical; the archive bundle restores their original source.
