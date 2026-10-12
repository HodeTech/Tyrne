# Code review 2026-10-12 — Track B.2-2 preflight and proposal package

- **Change:** `development`, initial cumulative proposal range `7d48f50603fa0d30464ea7b032f4f0fb82c3964c..289f461f430bde2b33da7e9c7fadc1dbebd1a7a3`; targeted correction `2f963e228686cb4f3db3ef5f653d2241a18e5fcd` and maintainer-reply reconciliation `519501f8d827eb436ea2ab060a30fc2681f636fd`.
- **Date:** 2026-10-12
- **Reviewer:** Codex coordinator and four independent review contexts, acting for @cemililik; the maintainer has not approved the proposed ADR package.
- **Risk class:** Ordinary — proposal documents only. No executable behavior, unsafe region, standard, task status, CI step or live policy changed.
- **Security-review cross-reference:** Not applicable to this proposal-only delta. The implementation plan requires distinct security reviews of architecture/security-boundary descriptions; this artifact supplies no runtime security verdict.
- **Description:** [Preflight and 13-step implementation plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md), Proposed ADRs [0041](../../../decisions/0041-test-name-prefix-policy-recovery.md), [0042](../../../decisions/0042-descriptive-test-names.md) and [0043](../../../decisions/0043-documentation-corpus-consistency.md), their index rows and the current-focus preparation notice.

**Subsequent supplied-review follow-up:** The maintainer supplied M1–M3, L1–L6 and O1–O3 after the original review. Their [source-verified reconciliation](../../reports/2026-10-12-adr-0041-0043-supplied-review-reconciliation.md) and revised proposals completed two further fresh independent rounds, recorded below; the sole Low finding is corrected and verified. Explicit maintainer approval remains pending. The original rounds/verdict below remain tied to their recorded source, not to these later edits.

The initial range contains six Markdown files and 528 additions. Both broad rounds reviewed that same cumulative proposal, rather than only the last commit. The three earlier read-only preflight agents informed the writing brief; they are not counted as either review round. The coordinator read all four reviewer reports, validated the sole finding against the ADR template, and merged their five-role results here under the [code-review master plan](master-plan.md).

| Round | Independent context | Model / effort | Original result | Follow-up disposition |
|-------|---------------------|----------------|-----------------|-----------------------|
| 1 | `b22_proposals_r1_governance` — decision authority, recovery/supersession, history and execution gates | GPT-6 Astra / high | Ready for maintainer proposal review; zero verified findings | No fix required |
| 1 | `b22_proposals_r1_contracts` — all twelve task AC/DoDs, source facts, dependencies and integration | GPT-6.1 Sol / high | Approve for proposal readiness; zero verified findings | No fix required |
| 2 | `b22_proposals_r2_governance` — fresh authority/history/policy analysis | GPT-6 Astra / high | Approve for proposal readiness; one Low R2-GOV-01, zero blockers | Independently verified corrected in `2f963e2`; copyright-reply record in `519501f` clean |
| 2 | `b22_proposals_r2_contracts` — fresh task/source/checker/CI analysis | GPT-6.1 Sol / high | Approve for proposal readiness; zero additional verified findings | Independently verified `2f963e2` correction and `519501f` reply record |

Round-2 agents did not read the round-1 reports before independent analysis. The second contracts reviewer received the governance finding only after reaching its independent conclusions; its correction verification is identified separately, not counted as another discovery or broad round. All reviewer work was read-only in the repository. The coordinator alone committed the changes.

## Correctness

No unresolved finding.

- ADR-0041 recovers the actual written `test_` convention without inventing earlier maintainer ADR approval, lint enforcement or adoption. ADR-0042's three unprefixed names resolve to real IPC tests. Explicit approval, a separate recovery Acceptance, replacement Acceptance/supersession with preserved history and both index directions, then the T-052 standard edit are in the correct authority order.
- ADR-0043 chooses T-054's existing stable-purpose alternative. Both rounds checked the 32 numbered C–I ledger rows; the source distribution is 5/5/6/5/5/3/3, with two distinct F2 decisions. Filed numeric ADRs, reserved 0034, historical aliases and explicitly unallocated decisions are preserved by the proposed contract.
- The ADR-0040 clarification is additive and Acceptance-gated. It openly extends the reviewed stacked-execution exception to this requested sequence, while preserving the whole-phase exit bar, T-038 Ready and the outstanding HIGH-correctness scope checkpoint. New implementation tasks stop at In Review.
- Every T-045–T-056 AC/DoD has an implementation owner or an explicitly proposed reconciliation in the plan. The original opening history remains intact; literal contract corrections occur after approval and before implementation. Optional T-056 is included without adding to the 46-task phase inventory or the 58 original track-item accounting.
- The source-backed brief distinguishes current non-SVC panic/resource-retention limits from future isolation/cleanup, bare syscall IPC primitives from scheduler bridges, and smoke marker/fault gates from manually inspected SVC counts. These facts become implementing-task writing/verification obligations, not a claim that the architecture refresh is already delivered.
- T-052's automatic register-dump follow-up obligation is explicitly proposed for removal with maintainer approval. Actual generic panic output is a banner and PanicInfo followed by spinning; saved exception diagnostics do not establish that feature. Existing host `unimplemented!` stubs also justify the proposed truthful lint description instead of an unapproved global deny.

## Style

No unresolved finding.

The ADRs contain the MADR sections, grounded dependency references, substantive alternatives/costs and process-decision Simulation exemptions. Repository text and commit messages are English. No binary asset, new diagram, mass rename or unrelated source cleanup is introduced. Proposal and corrective commits use conventional subjects and relevant ADR trailers. Cumulative `git diff --check` passes.

## Test coverage

No executable delta requires runtime tests at this preparation boundary. No new Rust, QEMU, Miri, coverage, hosted CI or future checker result is claimed by these reviews.

- The coordinator's limited path-existence check passes for 273 straightforward relative Markdown targets across the six proposal-touched files; a separate limited heading check passes for the four new-proposal fragment references. These checks cover the actual simple proposal forms, not the future bounded corpus parser or every Markdown grammar form.
- The proposed T-056 contract requires deterministic offline UTF-8/root handling, sorted file:line diagnostics, nonzero failure, Python 3.9 compatibility and isolated positive, negative and false-positive fixtures. It names real link/image/reference/escape/heading/HTML/code forms rather than promising a regex-only check.
- Every proposed index, ledger, fence and audit-tag check has an explicit boundary. Active/Removed audit entries and historical references are distinguished; reference reconciliation does not prove Rust soundness. Archives retain link checking, and exact reviewed fixture-backed exceptions cannot become a blanket exclusion.
- Syntax compilation is not described as Python formatting/linting. Independent maintainability review, macOS execution and hosted Linux evidence remain implementation obligations. Fresh exact-source Miri/coverage and matching debug/release raw smoke evidence likewise belong to their named implementation steps.

## Documentation

### R2-GOV-01 — Low: dependency-chain order differed from the execution plan — resolved

- **Original location:** ADR-0043 Dependency chain, lines 114–119 at `289f461`; compare the plan's Steps 4–10 and [ADR template](../../../decisions/template.md) requirement to list the chain in implementation order.
- **Evidence:** The ADR listed T-054 before task/review/index repairs and T-047 before standards, while the plan placed T-048/T-049, T-055, T-052/T-053, T-054, T-047 before T-056.
- **Impact:** Readers received two orderings. All hard prerequisites still preceded T-056, so this was a nonblocking clarity defect.
- **Disposition:** Coordinator confirmed the mismatch and committed `2f963e2`, changing only the five prerequisite-list lines to match the plan. Both fresh round-2 contexts independently verified that no obligation or approval boundary changed and all three ADRs remained Proposed. No unresolved finding remains.

All twelve task briefs and the six requested entry paths were covered by the preparation. The plan explicitly addresses obsolete glossary arithmetic, task closure snapshots, Python assumptions, ADR-index anomalies, extra broken historical navigation, architecture current/planned claims and clean-checkout guide prerequisites. It preserves historical verdicts, measured numbers and quoted defect provenance, using verified immutable links when a current target would alter the evidence.

The maintainer subsequently supplied the exact holder identity `HodeTech, Cemil ILIK and Tyrne Contributors`. Commit `519501f` records that spelling/capitalization and the common `Copyright 2026 HodeTech, Cemil ILIK and Tyrne Contributors` line in the plan, resolves only that input and keeps ADR/plan approval pending. Both round-2 contexts checked the narrow reconciliation. NOTICE and LICENSE remain unchanged until T-050's implementation step; the reply is not inferred to approve any ADR.

## Integration

No unresolved finding.

- The plan retains two fresh independent rounds, verified fixes/commits and applicable checks per implementation step. T-045 defines freshness before T-046 applies/rechecks it; merged T-032 already satisfies T-052's prerequisite; task/review/ADR/standards/ledger/live-state repairs precede T-056 integration. The parser and integration portions have distinct review boundaries, and final Step 13 rechecks all twelve task contracts and 58 item dispositions.
- Python already runs in the existing required `lint-and-host-test` job. The proposed command/fixture steps reuse that job and retain the six app-15368 required contexts. No seventh context, third-party parser, privileged workflow, credential or live settings write is introduced by the proposal.
- Root and both contracts contexts independently queried [PR #49](https://github.com/HodeTech/Tyrne/pull/49): OPEN, development to main, remote head `7d48f50603fa0d30464ea7b032f4f0fb82c3964c`. No push occurred. Publication waits for that predecessor's merge or an explicit maintainer combined-PR decision; local implementation can proceed after the separate ADR/plan approval gate.
- Root byte-compared all 39 pre-existing ADR files against the baseline and verified unchanged runtime/tool/workflow/standard/audit/task subtrees. ADR-0040 SHA-256 remains `5b82f632157033d193e64ac554390bacb9944fcd7a79fac9760a666c5f02ff2c`. All three new ADRs and their index rows remain Proposed. No Track B.2-2 task has started or been promoted.

## Verdict

**Approve — preparation and proposal readiness only.** Two fresh broad rounds completed; the sole Low finding is corrected and independently verified. Zero unresolved findings or blockers remain within this proposal-review scope.

Present ADR-0041/0042/0043, the 13-step plan and its explicit task-contract reconciliations for maintainer approval. Copyright identity is resolved. ADR Acceptance, implementation verification/security reviews, task delivery, publication clearance and final maintainer review/merge remain their own later boundaries. This is not a `conduct-approval-review` promotion verdict or authority to implement the still-Proposed decisions.

This indexed artifact records the completed reviews; its publication is checked by the coordinator and is not represented as another independent broad review of itself.

## Supplied-review follow-up — 2026-10-12

The maintainer's subsequent readiness review did not authorize Acceptance. The coordinator validated all twelve M/L/O items, revised the three Proposed ADRs and made literal Step 0 contract replacements plus the Acceptance-time rider reviewable in the plan. Accepted ADRs, standards, skills, task files, workflows and executable sources remain unchanged.

- **Initial corrected source:** `aff9ff4aa6eee8607c1a74efd4bcd5e699da6f3d`.
- **Final corrected source:** `7ccdde49aa77b35f181349adae4425bc68eb8801`.
- **Focused supplied-follow-up range:** `fb23823793b821b70f1252e16bb1b482f72fe1fe..7ccdde49aa77b35f181349adae4425bc68eb8801`.
- **Cumulative preparation range:** `7d48f50603fa0d30464ea7b032f4f0fb82c3964c..7ccdde49aa77b35f181349adae4425bc68eb8801`.
- **Risk class / security cross-reference:** Ordinary proposal-only delta; n/a for runtime security. Later security review obligations remain unchanged.

| Follow-up round | Fresh context | Model / effort | Result |
|-----------------|---------------|----------------|--------|
| 1 | `b22_supplied_r1_governance` | GPT-6 Astra / high | Approve for proposal readiness after R1-GOV-01 Low correction verified at `7ccdde4` |
| 1 | `b22_supplied_r1_contracts` | GPT-6.1 Sol / high | Approve; zero additional findings, disclosed correction independently verified |
| 2 | `b22_supplied_r2_governance` | GPT-6 Astra / high | Approve; zero new findings, cumulative correction and governance obligations verified |
| 2 | `b22_supplied_r2_contracts` | GPT-6.1 Sol / high | Approve; zero new findings, cumulative correction and all twelve task/58-item owners verified |

All four contexts are new relative to the original preparation reviews. Second-round contexts did not read the first-follow-up-round temporary reports; they verified the disclosed correction directly against source. The coordinator read all four complete reports and reconciled their five-role outputs below. Reviewers made no repository or remote writes. The initial preparation rounds remain distinct historical reviews.

### Correctness

No unresolved finding. ADR-0043 now requires the ADR-0040 rider in its Acceptance commit for both Decision outcome rule 7 and **Track B.2-1 implementation policy** rule 4; it does not mistakenly target Decision outcome rule 4, which governs Phase C status. The drafted rider preserves the old body/status and whole-phase outcome while explicitly naming the limited extension.

M2/M3/L5 have mandatory literal Step 0 replacements: T-055's index/no-anomalies clause and scope; T-049's note-only alternative, other-archive exclusion and scope; T-052's motivating standard reference. Task provenance and the five Accepted-ADR corrections' additions-only/status limits remain preserved. These clauses are specified for application after explicit approval, not reported as already implemented.

O1–O3 are concretely proposed: recovery remains Proposed without suspending the existing written standard; 0042 Acceptance and 0041 supersession are atomic after separate recovery Acceptance; selected T-056 delivery is fully verified while general optional phase-exit accounting remains unchanged. Acceptance alone does not deliver or activate its required gate.

### Style

No new actionable style issue. MADR/English conventions are maintained, shell and packaged-parser alternatives have separate costs, and ADR-0025 reference labels match the actual title. The grouped initial proposal/punctuation exception remains explicitly justified; no reviewed history is rewritten for it.

### Test coverage

The exact cumulative range and targeted Step 9 correction pass `git diff --check`. The coordinator's limited path check passes 121 straightforward relative targets in the seven follow-up-touched documents before final review-record publication; this is not a complete Markdown parser or a full-corpus gate result. The four simple new-proposal heading fragments remain valid.

Independent read-only checks confirm 42 numbered ADR records/42 unique index rows, baseline metadata/title anomalies, 32 live numbered ledger definitions and unchanged prior ADR/source/task/standard/CI files. These are static preparation checks. No Rust, QEMU, Miri, coverage, hosted CI or future checker fixture result is claimed; those remain implementing-task gates.

### Documentation

The supplied [M/L/O disposition table](../../reports/2026-10-12-adr-0041-0043-supplied-review-reconciliation.md#source-verification-and-dispositions) accounts for every item. L1 distinguishes the newly occupied 0041–0043 collisions from unfiled D3/C5 0044. L4 reports title/slug differences separately from index/header equality without forced renames or invented dates. Historical skill navigation must use verified immutable targets while quoted paths/verdicts/measurements remain evidence.

**R1-GOV-01 — Low, resolved:** At `aff9ff4`, Step 9 still allowed appending the rider later if it had not been filed at Acceptance. This contradicted the new same-commit requirement. Coordinator commit `7ccdde4` changes Step 9 to verification of the already-filed Acceptance-time rider and records the discovery. Both first-round contexts verified the exact correction; both fresh second-round contexts verified the cumulative corrected obligations and found no remaining delayed-rider alternative.

### Integration

No new blocker. All twelve task briefs were compared with the reconciled plan, including the complete original 58-item ownership accounting. Required consistency checks remain in the existing lint job, retaining the six app-bound contexts and Python standard-library runtime. The corpus repair owners precede checker enablement; required enforcement applies to revisions with delivered wiring, and default-branch enforcement follows merge.

Root reverified the 39 pre-existing ADRs byte-for-byte and unchanged runtime/tool/workflow/standard/audit/task subtrees. All new ADRs/index rows remain Proposed; T-056 remains Draft and the other eleven track tasks Ready. T-038, the HIGH checkpoint and C/D exit gates retain their existing state. Copyright identity remains resolved separately. Work stays local on development while PR #49 owns its remote source branch; no new publication authority is inferred.

### Follow-up verdict

**Approve — revised proposal readiness only.** Two fresh follow-up rounds completed; R1-GOV-01 is corrected and independently verified, with zero new second-round findings and zero unresolved proposal blockers. All supplied items are corrected in the draft package or covered by explicit Acceptance-time/Step 0 obligations.

Present the revised package and O1–O3 recommendations for explicit maintainer approval. ADR Acceptance, literal task reconciliation, implementation and final task delivery have not occurred. This appended record supersedes the earlier pending-follow-up notice; it preserves all original source-bound reviews and is coordinator-checked publication, not another independent review round of itself.
