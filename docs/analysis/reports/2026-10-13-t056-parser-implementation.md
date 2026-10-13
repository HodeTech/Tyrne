# T-056 Step 11 — offline navigation parser

- **Date:** 2026-10-13.
- **Author:** Codex implementation coordinator, sole writer on development.
- **Clean step base:** fd9009bb510a8351cb3f8f404f2db9d76c978134; kickoff 9b62a06, T-049 owning quotation clarification 0c62391.
- **Authority:** [approved plan](2026-10-12-phase-b2-track2-preflight-and-plan.md), [parser preflight](2026-10-13-t056-parser-preflight.md), Accepted [ADR-0043](../../decisions/0043-documentation-corpus-consistency.md), [T-056](../tasks/phase-b2/T-056-docs-consistency-automation.md).
- **State:** In Progress/all sixteen criteria unchecked. Local parser implementation is ready for fresh paired R1/R2 after its verification/commit; no task delivery, hosted CI or reviewer/maintainer approval claimed.

## Implemented contract

[CLI](../../../tools/check-docs.py), [reusable parser/resolver](../../../tools/docs_consistency.py) and [isolated contract fixtures](../../../tools/test-check-docs.py) implement the local-link portion, with [usage/grammar limits](../../guides/ci.md#documentation-consistency). Python 3.9+ stdlib only, explicit UTF-8, script-relative default root, Git-free temporary-root override, sorted file:line diagnostics and nonzero invalid/inconsistent input; no network, setting/source/report write or dependency install. Output retention is explicit caller redirection.

The lexer preserves source offsets and distinguishes actual code/comments from prose across fence types/lengths, quote/list containers and paragraph boundaries. Links/images include reference normalization/continuations, balanced/escaped/angle/empty paths and titles, and image destinations inside link labels. Undefined explicit references, duplicate definitions, interrupted definitions, unsupported nested links and excessive nesting fail visibly. Paths resolve with URL/HTML/Markdown decoding, exact case, repository-root semantics, root/private-alias protection and explicit symlink-input limits. Headings preserve code/label text and Unicode marks, allocate duplicate suffixes without custom-anchor consumption, and coexist with HTML id/name and bounded source-line references.

All public archives/reviews/skills remain scanned. Only the three existing .gitignore local-only analysis prefixes are non-repository input; active navigation into them fails even through a symlink alias. Maximum document/label/nesting limits are explicit. This is a bounded source grammar, not full CommonMark rendering, external-link validation, Rust parsing or architectural/soundness proof.

## Source-validated baseline and author regression work

The first whole-corpus prototype scan yielded three candidates. One D1 candidate was a parser false positive caused by crossing a Markdown block with a code span: source stayed byte-identical and a regression fixes it. The two D2b reference examples were intended historical quotations; [T-049-owned exact preservation proof](2026-10-13-t056-parser-evidence/t049-quoted-evidence-repair.json) verifies that explicit literal delimiters and a dated note preserve all old quoted and other source bytes. No archive exclusion or unreviewed broken-link exception was used. This owning follow-up is included in the forthcoming cumulative Step 11 reviews.

Contract fixtures preceded implementation; the first test entry point stopped with absent parser module. Additional comment/definition precedence, images in link labels, definition paragraph boundary and empty-title cases were observed failing before correction during author development. These are author regression observations, not agent findings or an assertion of a committed before-version. Private exploratory corpus captures remain distinct from the retained final source-bound results. The prewrite seventeen-versus-sixteen status-normalization correction is recorded in the immutable source inventory; no old completion date is invented.

## Verification and remaining gates

[Verification identity/results](2026-10-13-t056-parser-evidence/implementation-verification.json), [raw fixture output](2026-10-13-t056-parser-evidence/implementation-fixtures.log) and [whole-corpus JSON](2026-10-13-t056-parser-evidence/implementation-checker.json) bind actual local commands to base-plus-worktree source hashes. Separate absolute-path execution from /tmp checks default-root/cwd behavior. Syntax compilation/AST checks use Python 3.9 in memory, not a formatter/linter. No repo bytecode, scratch branch, deliberate broken commit, package install or unrelated Rust/QEMU/Miri result is claimed.

Both fresh paired rounds remain pending at this implementation boundary. All task/review/ADR/ledger/fence/audit/live checks, usage/standard integration and required existing-job wiring/exact-source hosted Linux verification belong to Step 12. Static commit-scope allowlisting remains skipped under ADR-0043. T-056 remains optional for the general phase exit but fully selected here; it cannot close by carry-forward or Acceptance alone. HIGH T-038, C/D gates, maintainer approval and PR49 publication barrier remain unchanged.
