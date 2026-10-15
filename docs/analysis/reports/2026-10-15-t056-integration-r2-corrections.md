# T056 Step12 — R2 metadata-context corrections

- **Date:** 2026-10-15.
- **Author:** Codex implementation coordinator; sole repository writer on development.
- **Independent reviewed source:** 770d86b4fd5360773ec4b441913d65e86c88a9ad; cumulative base91a64b5df2e1228221ba653c2ad5402474b5229d.
- **Author repair base:** 54d603b73738e006787b8ea386cbb14e3046f1cb; the intervening commit retains R1 evidence/status only.
- **State:** author repair verified; actual same-R2 committed-fix verification and reconciliation remain pending. T-056 stays In Progress/all16unchecked/no date_done. This is not a new ADR, review round, task delivery or merge approval.

## Independent findings and disclosure

Different fresh CODE and SECURITY contexts independently froze their [complete original INITIAL reports](2026-10-15-t056-integration-evidence/r2-initial-reports.json) before disclosure. Root personally read both in full, then authorized cross-reading. Both complete cross-read reports were also read. Their original HOLDs and procedural/read/retention limitations remain unchanged; the CODE review's late mandatory-context reading is explicitly disclosed, not backdated as compliant preflight.

| Reconciled group | Severity and independently validated defect |
|---|---|
| CODE R2-C01 | Medium: live headings/fields inside multiline inline-HTML attributes incorrectly supply state; hidden duplicate fields incorrectly reject real state. |
| CODE R2-C02 / SECURITY R2-S01 | Medium, one overlapping group: shared record-header scanning accepts task/ADR metadata inside indented fences or HTML attributes, also affecting live task joins. |
| ROOT-R2-COMPANION01 | Medium, root-attributed after initials: hidden companion headings/ownership bullets exempt an unindexed plan; a hidden unrelated heading can disable genuine ownership. Both reviewers independently validate/replay this additional consumer. |

Root reproduced all three on immutable770d86b, with valid all-family fixtures and missing/ordinary controls. The first live draft lacked Cargo/log inputs for all-family checking; its read errors remain retained and are not used as all-family proof. The corrected default-all fixture reproduces the live false greens on both runtimes. Root's Note-wrapped header example belongs to the shared-header group, not a fourth finding. Earlier six R1 groups and RV-S01 retain their historical scoped closure and original severities.

## Tests-first chronology

Six new metadata methods separately test rejection of hidden authority and preservation of real authority across record headers, live state and companion sections. Task/ADR forms, one-/three-space fences, a/span/div attributes, hidden unrelated headings and LF/CRLF/CR live forms are covered. Every original118 metadata method remains byte-identical; navigation tests and parser implementation are unchanged.

The first scratch layout put the six tools directly in its root. It produced41 failures per runtime:38 genuine new assertion failures plus three existing resource-test import failures caused by that incorrect layout. Before any implementation edit, the same source and unchanged test expectations were rerun in a repository-like tools directory. Both runtimes then produce exactly38 new assertion failures, with all118 old methods passing. Both raw stages and all source snapshots remain in [lossless author evidence](2026-10-15-t056-integration-evidence/r2-corrections-verification.json). No fixture oracle was withdrawn or weakened. The exact124-method before file was subsequently applied to the repository.

## Repair and verified behavior

A shared metadata projection starts from original block-masked text and erases actual inline HTML tag spans at their original offsets. Record-header field eligibility uses that projection while its raw first-H1/leading-header/body boundary remains intact. Companion section headings and ownership bullets use the same projection. Live masking occurs on the complete original document before region slicing, preserving global reference definitions and original physical-line interpretation.

This changes three metadata consumers, without changing permissive actual HTML navigation, block classification, source/audit scope, parser grammar, lifecycle policy, index requirements, required-check identity or branch settings. Fences/comments/raw HTML and tag attributes cannot supply metadata or duplicate authority. Real missing/duplicate fields and real companion section changes remain errors. The guide records this existing context contract; Accepted ADR0043 already governs the repair.

Actual Python3.9.6 and3.13.14 author checks pass:161 navigation methods and124 metadata methods per runtime; default all, explicit all from another cwd, links-only and seven-family subset. The source-stable corpus is392 Markdown files/7040 local targets/925 fragments/zero findings; metadata-only navigation counters are zero. Six Python files accept Python3.9 grammar and compile in memory. Forty-eight original root default-all/subset reproductions now match intended rejection/pass outcomes on both runtimes. Complete commands, environments, streams, inputs and before/after public/source hashes are retained in the linked evidence. These are author checks, not reviewer executions or universal grammar/resource proof.

Later publication prose changes the navigation census and is verified separately. The previous770d86b Linux checkpoint does not certify this new repair. Actual same-reviewer committed verification, authorized peer-fix reconciliation, exact repaired-source hosted execution, canonical both-round filing and Step13 remain required. Combined publication into PR49 is authorized; maintainer SECURITY wording review, task promotion and merge remain separate.
