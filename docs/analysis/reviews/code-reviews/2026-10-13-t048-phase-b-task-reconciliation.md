# Code review 2026-10-13 — T-048 Phase B task reconciliation

- **Change:** cumulative `a214532..a50f94ab7d8a28d67e3527be6ad0504ca0ca21d1` on `development`, including kickoff `f573ae1d39271da4ea4ded57c1252abb29630683`, implementation `550500f3080179fdb9b7254f64ea6fc48bf636d0` and correction `a50f94ab7d8a28d67e3527be6ad0504ca0ca21d1`.
- **Reviewer:** fresh independent Codex Round 2 reviewer; all five master-plan roles executed sequentially.
- **Date:** 2026-10-13.
- **Exact frozen reviewed HEAD:** `a50f94ab7d8a28d67e3527be6ad0504ca0ca21d1`.
- **Historical reference:** `origin/main` at `c16997e003fbd1726d1205734380394781c52002`; local `main` was not the history source.
- **Risk class:** Ordinary. The cumulative change comprises 21 Markdown files, 117 insertions and 23 deletions; no executable, unsafe, security boundary, dependency, API or CI behavior changes.
- **Security-review cross-reference:** n/a. Historical implementation/security descriptions are preserved, and this review does not grant retrospective security approval.
- **Procedure:** AGENTS/CLAUDE, current focus, numerical ADR corpus, standards, perform-code-review and conduct-review, full code master plan, whole T-048 contract, approved 13-step plan and source-bound reconciliation report. The independent cumulative assessment was completed before reading the actual R1 scratch report or coordinator checker/proof. The complete R1 report, including its bounded final disposition, was then read and reconciled.
- **Output boundary:** read-only repository review; only this scratch artifact is written. The coordinator owns canonical publication, indexing, commits and status updates. No external service mutation, runtime test, branch operation or package installation was performed.
- **Findings:** zero new findings; zero unresolved findings. Prior T048-R1-C01 is resolved. A prior review's arithmetic error is corrected explicitly below and is not an implementation defect.

## Both-round coordinator consolidation

| Round | Fresh context / model / effort | Disposition |
|-------|--------------------------------|-------------|
| 1 | `b22_t048_r1_code`, GPT-6.1 Sol / high | Initial Request changes, one Low T048-R1-C01; correction `a50f94a` independently verified, final scoped Approve. |
| 1 complementary | `b22_t048_r1_preservation`, GPT-6.1 Sol / high | Separate preservation/provenance context completed after the primary correction, before fresh complementary R2; actual assessment retained below. |
| 2 | `b22_t048_r2_code`, GPT-6.1 Sol / high | Fresh independent cumulative assessment and prior-round reconciliation; final disposition is preserved below. |
| 2 complementary | `b22_t048_r2_preservation`, GPT-6.1 Sol / high | Different fresh preservation/provenance context; actual assessment retained below. |

The coordinator read all four actual context reports, including R1's bounded follow-up and the completed different fresh R2. R1 found that the source-bound report named kickoff `f573ae1` as Checked source although assertions ran on the implemented working tree later committed as `550500f`. The coordinator independently verified and corrected it in `a50f94a`: baseline, checked resulting tree and actual immutable implementation are explicit. All historical task facts, bodies, 88 checkboxes and runtime/evidence bytes remained unchanged. The original initial verdict and source-specific finding are retained here; the follow-up is not counted as R2.

The R1 scratch report accidentally totaled its own per-task counts as 98; independent counting and the listed values sum to 88. The implementation report made no 98 claim. This canonical record corrects that review arithmetic while preserving all original task evidence. The record distinguishes the primary five-role code assessments from the complementary preservation/provenance lenses. All four actual contexts are retained; none claims a security pass or runtime execution.

The full fresh R2 assessment below covers all five roles and the explicit checklist. Its clean-tree/tracking observations refer to frozen tip `a50f94a`, before this canonical bookkeeping. No security trigger applies to this metadata/navigation step; neither code round certifies the historical runtime. Publication/index/trailers and later In Review promotion are coordinator bookkeeping, not another independent review or maintainer Done authorization. Cumulative reviewed range is `a214532..a50f94ab7d8a28d67e3527be6ad0504ca0ca21d1`.


## Correctness

**Clean.** The cumulative result satisfies the scoped historical reconciliation contract. Independent assertions used immutable Git reads rather than trusting the report or coordinator proof.

For each of the ten tasks, the complete original body after the frontmatter separator is an exact byte prefix of the new body, followed by exactly one merge-confirmation bullet. All ten independently calculated SHA-256 digests equal the report's preservation table. Other header fields are byte-identical after removing only the authorized status/date additions and T-029's added milestone. Each status is plain `Done`; each real ISO date is immediately after Created.

| Task file, relative to docs/analysis/tasks/ | New history line | Final date | Preserved checkboxes |
|------------------------------------------------|------------------|------------|----------------------|
| phase-b/T-020-syscall-error-taxonomy.md | 82 | 2026-05-29 | 7 |
| phase-b/T-021-syscall-dispatch.md | 110 | 2026-05-29 | 9 |
| phase-b/T-022-high-half-kernel-mapping.md | 69 | 2026-05-30 | 8 |
| phase-b/T-023-el0-entry-context.md | 63 | 2026-05-31 | 9 |
| phase-b/T-024-task-create-from-image.md | 56 | 2026-05-31 | 6 |
| phase-b/T-025-user-access-translation.md | 59 | 2026-05-31 | 9 |
| phase-b/T-026-current-task-cap-table.md | 54 | 2026-05-31 | 9 |
| phase-b/T-027-userland-build-pipeline.md | 61 | 2026-06-01 | 13 |
| phase-b/T-028-el0-userspace-wireup.md | 58 | 2026-06-01 | 11 |
| phase-b/T-029-perf-microbench.md | 48 | 2026-06-01 | 7 |

The historical headers are at lines 5–7 in T-020–T-028 and lines 4–7 in T-029. The existing bodies, previous review entries, measurements, completed acceptance criteria and safety claims remain unchanged.

All integration SHAs in `docs/analysis/reports/2026-10-13-t048-phase-b-task-reconciliation.md:16` through its merge table were independently resolved and checked for real author/committer dates, PR-bearing subjects, ancestry and first-parent membership in the frozen merged-main reference. The dates agree. PR #34 covers T-020/T-021; #36–#42 cover T-022–T-028. PR #42's `0040f23fdc87d6453c2ef9752899b001012bf5c5` has one parent, which is correctly allowed. T-029 includes both #44 `9c61a8ec49ab571b1d9686cb709699bc2fd5879d` and #45 `2ff65cb3bb12684092889fdb910d39af3fe2316d`; the latter's subject explicitly records completion, and its final integration supplies date_done. T-029's approved B6 follow-on milestone is present after Phase.

This historical Done reconciliation is authorized by the approved T-048 contract, especially `docs/analysis/tasks/phase-b2/T-048-phase-b-task-corpus-sync.md:53`, and its pre-existing completion/PR evidence. It does not create general agent authority to promote tasks. The old T-022 roadmap snapshot's later completion wording is preserved; exact integration dates control this contract, and the historical roadmap cleanup is T-047-owned.

The index at `docs/analysis/tasks/phase-b/README.md:7` renders as one table with 23 body rows and four cells per row. Raw row positions are contiguous; all IDs and task destinations are unique; the destination set equals the 23 actual task files. No T-010 is invented. Eight new titles and complete milestone cells at lines 24–31 literally equal their H1 suffixes/frontmatter, including code spans and links. T-020/T-021 at lines 22–23 have the exact requested Done/date/PR statuses. Removing only those eight additions and reverting only those two status cells reconstructs the entire old index byte-for-byte.

The three historical link files reconstruct exactly from their pre-step whole bytes with one authorized replacement each: `phase-a/T-002-kernel-object-storage.md:55`, `phase-a/T-004-cooperative-scheduler.md:25`, and `phase-b/T-011-missing-tests-bundle.md:25`. Targets exist; T-011's replacement equals its pre-existing correct coverage-report destination.

### Prior finding and review-evidence reconciliation

**T048-R1-C01 — Resolved independently.** At `docs/analysis/reports/2026-10-13-t048-phase-b-task-reconciliation.md:4`, kickoff f573ae1 is now explicitly the implementation baseline. Line 5 identifies the checked modified working tree and its later immutable implementation/report commit 550500f, and explains why the clean kickoff does not prove the result. The pre-step comparison and separate merged-main reference remain intact. Direct immutable 550500f reads confirm all ten Done/date headers, complete index, three destination repairs and initial implementation report; the substantive files match the reviewed corrected tip. The two-file correction only clarifies report provenance and appends T-048's correction history. R1's bounded verification agrees, and its original Request changes remains historical rather than being silently overwritten.

**Review arithmetic erratum:** the actual R1 report says “98” checkboxes but lists counts 7, 9, 8, 9, 6, 9, 9, 13, 11 and 7. Those sum to **88**, which independent marker counting and byte comparisons confirm at both baseline and tip. The implementation report makes no 98 claim. Preserve the truthful count 88 when recording canonical evidence; this corrects review arithmetic without implying a missing or altered checkbox.

## Style

**Clean.** New prose and all three step commits are English. Existing bullet history style is retained in the ten historical tasks; T-048 uses its existing table style. There are no introduced fences or diagrams. `git diff --check a214532..a50f94a` passes.

Commit subjects use conventional docs scopes, lengths 61/65/68 characters and actual ADR-0013/0040/0043 trailers. The coherent tasks scope is accepted under the standard's review-agreement extension rule. No Rust formatting, lint, module organization or unsafe annotation changes require review. Long literal index milestones implement the approved contract and are not a style defect.

## Test coverage

**Adequate.** This step adds no public API, Error variant, syscall, concurrency behavior or unsafe invariant. Builds, Rust tests, QEMU, Miri and fresh coverage would not exercise the metadata/navigation change and were not run or newly claimed.

Independent checks completed before prior-review/checker access:

1. Full immutable integration identity/date/subject/ancestry/first-parent checks, including one-parent #42 and both T-029 phases.
2. Ten whole-header and whole-body/history comparisons, all ten preservation digests, all 88 original checkbox lines and the exact appended merge bullets.
3. Actual Markdown rendering with the already-installed Python Markdown package (tables/fenced-code extensions), 23 contiguous unique four-cell rows, exact disk membership and eight literal H1/milestone matches.
4. Three whole-file link-only comparisons and old-index reconstruction.
5. Rendered local-link/fragment validation over the 32 A/B/template/lifecycle documents and all additional changed documents: 37 documents, 1,113 nonempty local paths plus three pathless same-file anchors, 125 Markdown heading references and two source-line references, zero missing/invalid. Code-formatted link labels remain links; fenced/code-contained examples are excluded. Heading generation removes inline formatting and tracks duplicate suffixes; source #L references are validated as bounded source lines rather than Markdown headings.
6. Hidden optional-template-field rendering, complete B.2 status counts, changed-file/risk scope, no added fence and clean whitespace.

After the independent assessment, the coordinator scratch checker was inspected and rerun: its bounded 800 paths / 99 headings / two source-line assertions pass. My matching 32-file rendered scope reproduces R1's broader 807 nonempty paths / 101 headings / two source-line counts; all resolve. The differing extraction grammars are explicitly bounded and are not contradictory claims of a delivered T-056 parser. Existing reviewer tooling did not add a shipping dependency or install a package.

These are static repository/document checks, not fresh hosted CI, runtime, security or coverage evidence. The report labels coordinator scratch checks accurately and makes no machine-independent reproducibility claim about its temporary scripts.

## Documentation

**Clean.** The optional date_done insertion comment at `docs/analysis/tasks/TEMPLATE.md:7` is hidden in rendered output. The surrounding metadata remains one list and Status remains Draft; no active placeholder completion date appears. `docs/analysis/tasks/README.md:36` retains maintainer-only Done authority. Its lifecycle at line 44 and conventions at line 50 match the template: real ISO completion date immediately after Created, maintainer authorization, omit while open, no fabricated historical date and optional field distinct from required metadata.

T-029's two-phase body remains historical and its new merge history supplies final completion context. The reconciliation report separates implemented content, the checked source, historical evidence and still-pending review records. Its correction note at line 59 and T-048 history at line 102 do not prematurely claim this Round 2 outcome.

All local navigation across owned and touched documents validates as described above. No new public Rust item, Safety/Errors section, architecture mechanism or guide is needed for this metadata step. Historical implementation evidence was not re-authored to simulate a fresh run or review.

## Integration

**Clean.** Every changed file has an existing-scope purpose. The contract names the index, ten closures, three link repairs, template/lifecycle, current focus and T-048. The additional B.2 index, plan progress line and source-bound report are allowed by the task's explicit evidence allowance (`docs/analysis/tasks/phase-b2/T-048-phase-b-task-corpus-sync.md:64`) and approved per-step plan. Scope was assessed on the cumulative step, not the full stacked branch.

The independent B.2 inventory is exactly 46 tasks: 8 Done / 26 Ready / 1 In Progress / 3 In Review / 8 Draft. T-048 is the sole In Progress task; T-045/T-046/T-051 stay In Review. The plan, B.2 index and top current-focus pointers agree (`docs/analysis/reports/2026-10-12-phase-b2-track2-preflight-and-plan.md:6`, `docs/analysis/tasks/phase-b2/README.md:44`, `docs/roadmap/current.md:5` and 9). current.md below its scoped live top changes is byte-identical to baseline; its lower dated/active snapshot remains T-047-owned.

There are no dependency, generated artifact, symbol/caller, Cargo, source, unsafe-log, build or CI changes. The full-corpus shipping checker remains T-056-owned. The accepted ADR-0040/0043 stacked-execution and C/D gate rules remain unchanged. Review stayed on clean development; PR49's publication barrier remains in the approved plan. No push, PR mutation, Done promotion or future-step completion is authorized by this review.

### Explicit code-review checklist

| Item | Disposition |
|------|-------------|
| Correctness | Pass: exact historical facts, literal index contract, headers, bodies and navigation independently checked. |
| Capability semantics | N/a: no operation, authority check or capability contract changes. Maintainer-only task authority is retained. |
| Fault containment | N/a: no runtime path/policy change; historical descriptions preserved. |
| Unsafe discipline | N/a: no unsafe region, audit scope, invariant or safety argument changes. |
| Error handling | N/a: no function, Result, panic or boundary conversion change. |
| Tests | Pass: meaningful static contract/render/preservation checks; no redundant runtime run. |
| Documentation | Pass: source binding corrected, template/lifecycle matched, factual records preserved. |
| Architectural principles | P1–P12 individually assessed below. |
| Dependencies | None added or upgraded; dependency-addition skill not triggered. |
| Naming/style | Pass: English and existing Markdown/history conventions; no introduced fence/diagram. |
| Commit message | Pass: three conventional docs commits, appropriate agreed scopes and governing ADR trailers. |

### Architectural principles P1–P12

| Principle | Disposition |
|-----------|-------------|
| P1 — No ambient authority | No runtime authority delta; maintainer-only Done authority remains explicit. |
| P2 — Small TCB | No privileged code/dependency delta. |
| P3 — Userspace drivers/services | No placement or fault-isolation change. |
| P4 — Trust-boundary checks | No trust-boundary operation changes. |
| P5 — Rust-only kernel | No executable code added. |
| P6 — HAL separation | No API/crate/hardware dependency changes. |
| P7 — No proprietary blobs | All changed artifacts are text Markdown. |
| P8 — ADR governance | Applies accepted ADR-0013/0040/0043 and approved contract; no new decision or Accepted-body rewrite. |
| P9 — English artifacts | New repository prose and commits are English. |
| P10 — Mermaid diagrams | No diagrams changed. |
| P11 — Reproducibility | Build inputs unchanged; exact implementation/history source provenance now unambiguous. Static scratch checks are bounded honestly. |
| P12 — Complete declared scope | Scoped content is delivered and independently verified; review/status publication remains coordinator-owned. No task Done or main merge claim. |

## Verdict

**Approve** cumulative `a214532..a50f94ab7d8a28d67e3527be6ad0504ca0ca21d1` across all five code-review roles. Zero new findings, zero unresolved findings; prior Low T048-R1-C01 is independently resolved. Correct the prior review's checkbox arithmetic to 88 when producing the canonical record.

This exact-tip review assesses T-048 Step 4 only. It does not itself promote T-048, approve future steps, override maintainer authority, waive remaining phase gates or authorize publication.


## T-048 Step 4 — complementary Round 1 preservation and navigation review

- **Review date:** 2026-10-13
- **Reviewer:** `/root/b22_t048_r1_preservation`, fresh complementary R1 context; read-only repository access.
- **Exact reviewed source:** `a50f94ab7d8a28d67e3527be6ad0504ca0ca21d1` on `development`.
- **Cumulative comparison:** `a214532..a50f94ab7d8a28d67e3527be6ad0504ca0ca21d1`; implementation `550500f3080179fdb9b7254f64ea6fc48bf636d0`; kickoff baseline `f573ae1d39271da4ea4ded57c1252abb29630683`.
- **Frozen merged-main evidence:** `c16997e003fbd1726d1205734380394781c52002`; local main and moving branch names are not proof sources.
- **Scope/verdict:** **Approve the implemented documentation source for this complementary preservation/navigation lens. Zero new verified implementation findings.** The primary R1 arithmetic erratum is resolved through the required corrected canonical publication input, recorded below; it is not a repository implementation finding. This is one R1 context, not an assertion that R1 as a whole, R2, maintainer approval, or T-048 Done promotion has completed.

### Method and limits

Applied the perform-code-review and conduct-review procedures and code-review master-plan roles within the assigned complementary lens. Read the approved T-048 contract and governing plan, relevant ADR/governance and standards, complete touched historical task documents and review/report context. Substantive independent Git-object, byte-preservation, membership and rendered-table assessment preceded reading the primary R1 report. Then read `/tmp/tyrne-b22-t048-r1-code.md` in full, including its correction follow-up, and reconciled the original finding against the actual corrected source.

All assertions used immutable `git show`/`git ls-tree` sources. Inline Python scratch checks compared exact strings/bytes, recomputed SHA-256, checked literal table cells and whole-file link substitutions. Python-Markdown with its tables extension independently emitted HTML for the Phase B index; an HTML parser counted the actual rendered task rows and checked the emitted task destinations against the frozen Git tree. `git show -s`, `git rev-list --first-parent` and `git merge-base --is-ancestor` checked integration identity, dates, subjects and ancestry. Cumulative `git diff --check a214532 a50f94ab7d8a28d67e3527be6ad0504ca0ca21d1` passed.

No repository write, test-suite execution, commit, push, external message, runtime/build/smoke/Miri/coverage execution, or separate security pass occurred. The checks establish the stated document contracts and evidence identities; they do not rejudge historical implementation/runtime/security claims, prove remote PR review state from a live service, reproduce every coordinator scratch-script count, or implement T-056's future corpus grammar gate. The diff contains 21 documentation files and no executable, build, unsafe, dependency, CI or security-boundary change.

### Correctness and historical preservation

All ten source report integration rows resolve to their full immutable objects, occur in the frozen merged-main first-parent history and are its ancestors. Both Git author and committer dates equal the claimed dates; subjects contain the claimed PR number. PR #42 is correctly treated as a one-parent integration, rather than requiring every integration to have two parents. The final T-029 integration subject explicitly records completion.

| Tasks | Integration evidence | Date |
|-------|----------------------|------|
| T-020, T-021 | PR #34 `f98e1af8e9f044d8d28858ca40c11ede03ef7e06` | 2026-05-29 |
| T-022 | PR #36 `b6549d7e41667d62e42a16491e26165518b09510` | 2026-05-30 |
| T-023 | PR #37 `eb3125f716db7944f80f973ef04e046fb101ada3` | 2026-05-31 |
| T-024 | PR #38 `5f17a30705c49e1b6fccb58b194e259994cf38ab` | 2026-05-31 |
| T-025 | PR #39 `f21eece3e956926d2d2219294850fe8d6f4d4872` | 2026-05-31 |
| T-026 | PR #40 `a8ce11e3b9d48145d9e81d2007dfa5bb8d094c91` | 2026-05-31 |
| T-027 | PR #41 `9551a331645b5843778ffc8ff2f35a85f79845a8` | 2026-06-01 |
| T-028 | PR #42 `0040f23fdc87d6453c2ef9752899b001012bf5c5` | 2026-06-01 |
| T-029 Phase 1 | PR #44 `9c61a8ec49ab571b1d9686cb709699bc2fd5879d` | 2026-06-01 |
| T-029 Phase 2 | PR #45 `2ff65cb3bb12684092889fdb910d39af3fe2316d` | 2026-06-01 |

The approved historical reconciliation authority is explicit in T-048 and the approved plan. The ten records correctly use plain Done and place the real final integration date immediately after Created. T-029 uses Phase 2's final date and names both phases/PRs. Its new B6 follow-on milestone is the specific authorized header exception. Earlier roadmap observations are historical; their broader cleanup remains T-047-owned.

For every T-020 through T-029, the complete original body after the first frontmatter separator, including all previous review history, is an exact byte prefix of the new body. The remainder is exactly one new dated merge-confirmation bullet. Removing the authorized status/date changes and T-029 milestone addition restores the original header exactly. Recomputed original-body SHA-256 values match all ten hashes in `docs/analysis/reports/2026-10-13-t048-phase-b-task-reconciliation.md:38`–47.

Exactly **88** existing checkbox lines are byte-identical: T-020…T-029 counts are **7, 9, 8, 9, 6, 9, 9, 13, 11, 7**. No historical acceptance/DoD checkbox, measurement, test result, safety claim, or original history entry was rewritten or newly checked to suggest fresh verification. The appended merge bullets correctly distinguish historical integration reconciliation from a new implementation/review run.

### Style, navigation and literal contracts

`docs/analysis/tasks/phase-b/README.md:9`–31 contains exactly 23 unique contiguous task rows, equal to the actual phase directory's task-file set. Independent HTML rendering produces one table with 23 task body rows, and all 23 emitted task link destinations exist at the exact reviewed source. No synthetic T-010 row, duplicate or omitted disk member occurs.

The eight added rows at lines 24–31 match the literal source H1 suffix and complete Milestone value, including inline code, punctuation and decision links. T-020 and T-021 retain their old row text except the authorized status/date/PR #34 cells. Literal long milestone cells satisfy the approved contract.

Whole-file comparisons establish exactly one destination substitution in each authorized link-only file: `docs/analysis/tasks/phase-a/T-002-kernel-object-storage.md:55`, `docs/analysis/tasks/phase-a/T-004-cooperative-scheduler.md:25`, and `docs/analysis/tasks/phase-b/T-011-missing-tests-bundle.md:25`. All three repaired targets exist. T-011's precise original destination was `../../reviews/business-reviews/../reports/2026-04-23-coverage-baseline.md`; its replacement is the pre-existing correct report destination `../../reports/2026-04-23-coverage-baseline.md`. No unrelated historical prose changed.

The lifecycle text and `docs/analysis/tasks/TEMPLATE.md:7` consistently require an optional real ISO date_done after Created only for maintainer-authorized Done, omitted while open and never invented for unknown historical dates. The Draft template instruction is an HTML comment and does not render a live date placeholder. New prose is English; no new diagram or code fence requires separate diagram/fence validation.

### Evidence, documentation and integration

The original primary R1 Low provenance finding is resolved at the reviewed source. `docs/analysis/reports/2026-10-13-t048-phase-b-task-reconciliation.md:4`–5 now explicitly separates kickoff baseline, the resulting uncommitted implementation tree on which checks ran, and implementation commit `550500f`. It states that the clean kickoff alone does not prove the reconciliation. The a50 correction changes only this report and T-048 history; historical implementation bytes remain intact.

The source-bound report accurately frames its 800 path / 99 heading / two source-line coordinator checks as bounded scratch verification and disclaims a shipped tool, other-machine reproducibility and the full T-056 grammar gate. This reviewer independently confirms the narrower byte, metadata, table-rendering, repaired-target and ancestry claims described above; it does not silently adopt those larger scan counts as its own execution results. The report's pending-review statements describe its implementation/correction record and do not fabricate fresh review completion.

The cumulative 21-file documentation scope is covered by T-048's named changes plus the explicit step-scoped evidence/task/current/index allowance. T-048 remains In Progress, and independently counted B.2 statuses remain **8 Done / 26 Ready / 1 In Progress / 3 In Review / 8 Draft = 46**. Existing Phase B historical closure does not promote any new B.2 task. No distinct security review is triggered by the metadata-only delta; no security approval is claimed by this ordinary complementary pass.

### Verified actionable review-artifact finding

#### T048-R1-P01 — Low — correct the derived checkbox total before publication

- **Location:** `/tmp/tyrne-b22-t048-r1-code.md:53`.
- **Observed:** The primary R1 scratch report says “All 98 existing acceptance/DoD checkboxes” while the same sentence's ten per-task counts sum to 88. Independent exact-source comparison also counts 88 unchanged checkbox lines.
- **Required correction:** Replace 98 with 88 in the canonical publication input/output and any derivative publisher text before publication. Preserve the correct per-task counts and the byte-preservation conclusion.
- **Impact/disposition:** This is a Low numerical error in a derived review artifact, not an implementation defect or a need to rewrite historical task evidence. No 98-checkbox claim exists in the reviewed source-bound implementation report. Root was notified promptly and reports its unexecuted publisher input is corrected to 88. The erratum is resolved by the canonical-before-publication correction requirement; it is not an outstanding repository implementation finding. This reviewer did not inspect or execute that publisher, so root confirmation is distinguished from independent source checks.

### Verdict

**Approve** the cumulative implemented source at `a50f94ab7d8a28d67e3527be6ad0504ca0ca21d1` for this complementary Round 1 preservation/navigation review, with zero new verified implementation issues and the original provenance clarification independently confirmed. The primary R1 arithmetic erratum is resolved by the required canonical-before-publication correction (root confirms its publisher input now uses 88). Different fresh Round 2 contexts and the coordinator's complete round record remain separate work; this artifact grants no task Done promotion or publication authority.


## T-048 Step 4 — complementary Round 2 preservation and provenance review

- **Review date:** 2026-10-13.
- **Reviewer:** `/root/b22_t048_r2_preservation`, a different fresh complementary R2 context; repository read-only, coordinator sole writer.
- **Exact reviewed source:** clean `development` at `a50f94ab7d8a28d67e3527be6ad0504ca0ca21d1`.
- **Cumulative change:** `a214532..a50f94ab7d8a28d67e3527be6ad0504ca0ca21d1`.
- **Actual implementation:** `550500f3080179fdb9b7254f64ea6fc48bf636d0`; kickoff `f573ae1d39271da4ea4ded57c1252abb29630683`.
- **Frozen historical integration source:** `c16997e003fbd1726d1205734380394781c52002`, the locally available `origin/main` object. Local `main` was not used as the evidence source.
- **Risk class:** Ordinary documentation/metadata/navigation delta; security-review cross-reference n/a. No security approval of historical implementations is claimed.
- **Finding count:** zero new verified repository implementation findings; original Low provenance finding independently confirmed resolved; derived R1 arithmetic erratum independently reconciled to 88.

### Method and limits

Applied perform-code-review, conduct-review and the code-review master plan within this complementary preservation/provenance assignment. Read CLAUDE.md, current-focus context, the applicable skills/master plan, approved plan and complete T-048 contract. The numerical ADR and standards corpus was also ingested through whole-file UTF-8 reads with a bounded filename/line-count/digest inventory; detailed reasoning here focuses on the governing task/lifecycle/history rules, not a new architectural review of every historical ADR. Several initial large display reads were truncated; no preservation assertion relies on those displays. The exact comparisons consumed complete file contents without truncation.

Before opening either R1 scratch report, independently formed the substantive assessment from Git objects and full-file comparisons: merge identity/dates/subjects/first-parent/ancestry, ten original body/history prefixes, allowed header changes, checkbox line identity/counts, literal index cells, disk membership/contiguity, three whole-file single-destination transformations, optional real-date authority and kickoff-versus-implementation evidence. Then read all 70 lines of `/tmp/tyrne-b22-t048-r1-preservation.md` and all 159 lines of `/tmp/tyrne-b22-t048-r1-code.md`, including its actual bounded correction follow-up. The primary fresh R2 report was not used as the basis for this assessment.

After that reconciliation, independently rendered the Phase B index with installed Python-Markdown tables/fenced-code extensions and parsed its HTML, checked the template's hidden instruction, counted B.2 statuses, checked exact correction scope and read the complete unexecuted `/tmp/tyrne-b22-t048-publish.py` to verify its explicit arithmetic erratum. The publisher was not executed or otherwise modified.

No repository file was written, and no build, Rust tests, runtime/smoke/Miri/coverage run, branch/commit/push or external mutation occurred. The only output written by this context is this scratch review. This pass establishes document preservation, metadata, navigation endpoints, rendered membership and local immutable Git provenance; it does not re-execute historical tests, certify security, prove live remote PR review state, claim another-machine reproducibility, reproduce the coordinator's 800/99/two scan counts, or implement the future full-corpus grammar gate owned by T-056.

Two initial scratch assertions failed because of reviewer assumptions, not source defects: a redundant metadata regex and an assumed abbreviated old T-011 path. Those assumptions were removed/corrected using the actual complete source; the substantive checks below pass. Failed scratch attempts are not represented as successful full runs.

### Correctness

All ten records have plain Done status and their real final integration date immediately after Created. Every named integration resolves to the full SHA below, is an ancestor of frozen merged-main, appears in its first-parent list, has equal author/committer dates matching the contract and has the claimed PR number in its subject. Both T-029 integrations were checked; Phase 2 supplies its final completion date. PR #42 is a one-parent integration and is correctly accepted on its actual provenance rather than requiring two-parent merge shape.

| Task | PR | Verified integration | Author = committer date |
|------|----|----------------------|-------------------------|
| T-020, T-021 | #34 | `f98e1af8e9f044d8d28858ca40c11ede03ef7e06` | 2026-05-29 |
| T-022 | #36 | `b6549d7e41667d62e42a16491e26165518b09510` | 2026-05-30 |
| T-023 | #37 | `eb3125f716db7944f80f973ef04e046fb101ada3` | 2026-05-31 |
| T-024 | #38 | `5f17a30705c49e1b6fccb58b194e259994cf38ab` | 2026-05-31 |
| T-025 | #39 | `f21eece3e956926d2d2219294850fe8d6f4d4872` | 2026-05-31 |
| T-026 | #40 | `a8ce11e3b9d48145d9e81d2007dfa5bb8d094c91` | 2026-05-31 |
| T-027 | #41 | `9551a331645b5843778ffc8ff2f35a85f79845a8` | 2026-06-01 |
| T-028 | #42 | `0040f23fdc87d6453c2ef9752899b001012bf5c5` | 2026-06-01 |
| T-029 Phase 1 | #44 | `9c61a8ec49ab571b1d9686cb709699bc2fd5879d` | 2026-06-01 |
| T-029 Phase 2 | #45 | `2ff65cb3bb12684092889fdb910d39af3fe2316d` | 2026-06-01 |

Subjects independently inspected include the #34 B5 T-020/T-021 integration, #37 B6 opening/T-023 integration, #42 first-real-EL0 T-028 wire-up and #45 “T-029 Phase 2 … (completes T-029)”; the others explicitly name the expected task branch and PR. The approved historical closure authority is explicit in T-048 and the plan and supported by existing maintainer completion/PR records. It is not a general authorization for an agent to promote new tasks to Done. The old current.md T-022 date discrepancy remains historical T-047-owned context; exact 2026-05-30 integration evidence is correctly used here.

For every T-020–T-029, original complete body bytes after the first frontmatter separator are an exact prefix of the resulting body. The remaining suffix is exactly one new dated merge-confirmation bullet. Original header content is restored exactly by removing only status/date changes and T-029's authorized added milestone. This covers complete older implementation/review history, measurements, fault/security wording and every checkbox; it is stronger than comparing selected quoted sentences.

| Task | Original-body SHA-256 | Unchanged checkbox lines |
|------|----------------------|--------------------------|
| T-020 | `91205d69952ee65e6c287428a23aa471552fda9f2200753e840fb7c5e00f40f3` | 7 |
| T-021 | `ec6d367597ff5d839ac703b9d03bb9a6877fac82d50bd68bce9dd5b9d2d6c547` | 9 |
| T-022 | `6d8abaf2e46b9a9b6599096afc5e2479917911f813e753b2b26af2e5f0dbca62` | 8 |
| T-023 | `0ad1cb9c50212cfb16fc78569bb1b132967b4f472c53462d28bb46b02f99e876` | 9 |
| T-024 | `5364f746c04c31164e5d8cc6d147f1d0ffca166c3a93ea66e3af852ec9bc4a7d` | 6 |
| T-025 | `e849695c7c00d7c6f0bfa41748a0891f7fc86beff7e97ef3706b43ca9f7fc2cf` | 9 |
| T-026 | `50809789c9645b3e923ebc9b1cdb995cbe14da15b497b35a770cd43d25486303` | 9 |
| T-027 | `9ea03eec23e289b89541236d3993953e06e44fa6477b6ef9636a94ade6d8061b` | 13 |
| T-028 | `5e141c7e81817e5b88913ed50648b0d0e7dd39491812c1b35f62d8198c457603` | 11 |
| T-029 | `07e5b01c906783ca0f74c90e34f4b09af3cbd22ac7abb62e4baafaf9dbea5c4b` | 7 |

The total is **88**, independently counted from actual checkbox lines, not borrowed from a prior total. All ten hashes match the source-bound report. T-029's sole additional Milestone is exactly “B6 follow-on / Phase B closure tail — not gated on a numbered B-milestone”; both PRs/full SHAs remain in its merge confirmation. No historical checkbox is newly ticked to imply fresh verification.

### Style

The index consists of 23 unique contiguous four-cell task rows equal to the directory task-file set; no missing/duplicate member or synthetic T-010 exists. Actual Markdown rendering produces one table and 23 task body rows, with 23 unique valid task-file destinations. The eight new title cells equal each literal H1 suffix and eight milestone cells equal each complete metadata value, including code spans, punctuation and links. Long cells follow the approved literal contract. Older index wording is preserved except the two authorized T-020/T-021 completion cells.

The three link-only documents are complete original files with exactly one authorized destination replacement each. T-002 changes `../../../kernel/src/cap/table.rs` to `../../../../kernel/src/cap/table.rs`; T-004 changes `../../../hal/src/context_switch.rs` to `../../../../hal/src/context_switch.rs`; T-011 changes `../../reviews/business-reviews/../reports/2026-04-23-coverage-baseline.md` to `../../reports/2026-04-23-coverage-baseline.md`. All repaired destinations exist; T-011 now matches its second existing report link. No unrelated prose was rewritten. `git diff --check a214532..a50f94a` passes. New prose is English, with no introduced diagram or fence.

### Test coverage

Meaningful independent checks cover exact Git integration, whole-file/header/body preservation, SHA-256, 88 checkbox identities, membership/contiguity/literal cells, actual table rendering, all three destination transformations, date authority, correction scope and B.2 counts. No executable behavior/API/error/unsafe contract changes; runtime/build tests would not exercise this metadata repair and were neither run nor newly claimed. Coordinator bounded navigation scan counts remain attributed to their source report, not claimed as this review's own scan results. The changed targets and rendered index endpoints were independently verified.

### Documentation

Template and lifecycle consistently describe optional date_done immediately after Created, with a real ISO date only for maintainer-authorized Done, omitted while open and never invented for historical tasks. Rendering confirms that the Draft template's insertion instruction remains an HTML comment, rather than a live date placeholder. Required fields remain distinct from this optional field.

**T048-R1-C01 — Resolved.** Independently observed before prior-report reading: source-bound report lines 4–5 explicitly distinguish kickoff f573ae1, checked resulting uncommitted implementation and immutable implementation commit 550500f. Git reads confirm kickoff T-020 is still In Review while implementation T-020 is Done; the newly cited implementation actually contains the reconciliation. The a50 correction modifies exactly the report and T-048 history. It changes no historical phase/task/template/lifecycle implementation bytes and preserves separate pre-step comparison and merged-main identities. The actual primary R1 follow-up approves that corrected source; this fresh R2 confirms the correction independently rather than counting the follow-up as R2.

**T048-R1-P01 derived scratch erratum — Resolved for canonical publication input.** The actual primary R1 report still says 98 while its listed ten counts and independent source count total 88. The complementary R1 report correctly identifies this as Low derived review arithmetic, not a repository implementation defect. The source-bound implementation report contains no 98 claim. Read-only inspection of the complete unexecuted publisher confirms its canonical consolidation explicitly records the 98→88 correction and uses 88 in its preservation/completion claims. Original R1 finding/follow-up history is retained. This verifies the draft input; it does not claim the canonical artifact already exists or that the publisher was executed.

### Integration

The cumulative diff contains 21 Markdown files and no executable, unsafe/audit-log, dependency, build, CI or security-boundary changes. Named task/index/lifecycle/link changes plus step-tracking/report files fit the approved Step 4 and evidence allowance. Independently counted B.2 states remain **8 Done / 26 Ready / 1 In Progress / 3 In Review / 8 Draft = 46**; T-048 is In Progress while canonical review bookkeeping is pending. No new B.2 Done promotion, Phase C/D gate change or HIGH T-038 delivery occurs. Existing historical Phase B reconciliation is distinct from later maintainer authorization for new B.2 task completion. Root retains publication/index/status/commit bookkeeping authority.

### Verdict

**Approve** cumulative implemented source `a214532..a50f94ab7d8a28d67e3527be6ad0504ca0ca21d1` for this fresh complementary Round 2 preservation/provenance lens. Zero new verified repository implementation findings; T048-R1-C01 is independently resolved, and the 98→88 derived scratch erratum is verified corrected in the unexecuted canonical publication input.

This completes this different fresh complementary R2 context after the actual complementary R1 and primary R1 follow-up were available. It supplements the coordinator's five-role round record; it is not a standalone security approval, maintainer Done authorization, publication permission or claim of a fresh runtime result.
