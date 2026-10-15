# T-056 integration — first-round correction evidence

The implementation coordinator prepared these repairs after both independent R1 INITIALs and their authorized peer cross-reads were frozen against f4e11d9. This is author verification awaiting the same reviewers' committed-fix verification; it is not a fresh round, approval or task delivery certification.

## Six reconciled groups

| Group | R1 ownership | Repair and regression controls |
|---|---|---|
| Review discovery | CODE C01 / SECURITY S04 | Unused Markdown definitions and images grant no discovery; actual full/collapsed/shortcut references and HTML links still do. Ordinary link validation still checks unused definitions. Event and master-run negatives are covered. |
| Explanatory annotations | CODE C02, later replayed by SECURITY | A monotonic explanation boundary suppresses inner annotation starts without suppressing reference resolution. Nested/wrapped explanations, Removed history, explicit later list members and real parenthesized safe assertions are covered. |
| Source-redirection syntax | CODE C03 / SECURITY S01 / coordinator corroboration | Whitespace/comment-separated macro tokens and all three delimiters are recognized. Direct/nested conditional path attributes are inspected separately from cfg predicates. Supported stored literals remain accepted; dynamic/outside paths diagnose. String/comment/include_bytes controls remain inert. |
| Redirection lookup work | CODE C04 / SECURITY S03 | A sorted string-offset index replaces repeated prefix scans; repeated literal destinations share guarded resolution. A 24,000-constant whole-command regression checks practical resource behavior. This finite ten-second watchdog is not a universal CPU/memory bound. |
| Cargo overrides | CODE C05 / SECURITY S02 | Root patch/replace local paths, including virtual-root and URL-keyed tables, enter the existing transitive member inventory. Missing/malformed/private/outside/aliased paths diagnose; default-members never narrows scope. |
| Live block context | SECURITY S05, later replayed by CODE | Exact delimiters must be standalone top-level comments. Original parsed rows, block context and globally defined references are retained rather than reparsing a slice. Outer/split fences, enclosing comments and HTML attributes cannot authorize the region. Raw pre/script/style/textarea blocks retain literal context through their closing line, including embedded fence text; real later state and inner examples remain valid. |

The raw HTML variant was independently found by the coordinator while validating S05's boundary and belongs to that same group. No finding is closed by this author document; reviewer verification remains required. These changes implement already Accepted [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md), with no new runtime Rust, unsafe block, dependency or policy decision.

## Executed chronology and retained limits

[Verification records](r1-fixes-verification.json), [complete source stages](r1-fixes-source-snapshots.json) and [lossless raw streams](r1-fixes-streams.json) are coordinator-generated evidence, with exact payload hashes and recoverable original UTF-8 bytes. Escaped stream envelopes preserve whitespace without editing failed output. The source stages are inert data, not imported programs. Commands use own-TMP scratch directories and explicitly disable bytecode creation.

- Eleven new metadata methods ran before repairs on both interpreters: 42 failed assertions on each; Python3.9 also hit the ten-second redirection-resource watchdog. Python3.13 completed that finite workload, so no timeout is claimed there. The additional full-document reference control exposed loss of definitions outside the extracted region.
- The first repair run failed: the coordinator initially attempted to mutate immutable BlockLine records; 35 errors and five assertions are retained. This was corrected with record replacement. The new alias control's expected family was corrected to the existing input diagnostic, and the unused-definition control's mistaken diagnostic name was corrected to path. Existing fixture expectations were preserved.
- The second repair run had only the new incorrect destination-diagnostic assertion remaining. After its correction, all160/110 methods passed on both runtimes; these first-green results and source remain a separate stage.
- A subsequent raw-HTML probe falsely accepted all four literal block forms. Its tests-first four failures are preserved. Block parsing now prevents literal HTML contents from manufacturing fences, live comments or Markdown headings, while preserving actual HTML navigation. The navigation regression was added with that fix; no failing-before run is claimed for that additional navigation method.
- Final source-bound runs pass **161 navigation and111 metadata methods** on both Python3.9.6 and3.13.14. Eight CLI corpus runs pass: default/all from another cwd/links/seven metadata families on each runtime, all with empty PATH. Full/links counters are391 public Markdown files,7017 local targets,919 fragments,zero findings. Metadata-only counters are391/0/0/zero. These counts precede this evidence document's publication, which changes the public corpus.

The final executed six Python files remained byte-identical after execution; syntax parses with the Python3.9 grammar and compiles in memory. These are macOS author runs, not hosted/Linux evidence. Prior INITIALs, their severities, independent execution boundaries and disclosed scratch-location corrections remain unchanged. No semantic regression expectation was withdrawn to obtain success.

## Publication and remaining work

The maintainer explicitly selected combined publication into [PR #49](https://github.com/HodeTech/Tyrne/pull/49) on2026-10-15; the [plan](../2026-10-12-phase-b2-track2-preflight-and-plan.md#publication-and-remaining-phase-work) records that authorization. Development remains the only working/source branch. Exact-source hosted gates, R1 committed-fix verification, different fresh R2 reviewers and Step13 closure are still required. T-056 remains In Progress/all16 criteria unchecked/no date_done; T-051 wording review and maintainer merge authorization remain separate.

## Syntax references

- [Cargo root patch/replace override semantics](https://doc.rust-lang.org/cargo/reference/overriding-dependencies.html#the-patch-section).
- [Rust conditional attribute expansion and nested cfg_attr](https://doc.rust-lang.org/reference/conditional-compilation.html#the-cfg_attr-attribute).

These primary references support scope syntax, not a claim that this bounded checker evaluates Cargo feature/dependency resolution or implements a Rust AST.
