# Track B.2-2 — Preflight review and implementation plan

This document records the source-backed documentation review, decisions awaiting the maintainer, reconciled task contracts and the reviewed-step execution plan for Track B.2-2.
It is the implementation brief for a documentation and tooling wave; it does not report implementation as complete.

- **Status:** Proposed — awaiting maintainer approval of the ADR package and the unresolved copyright wording.
- **Date:** 2026-10-12
- **Author:** Codex (AI agent), on behalf of @cemililik
- **Source baseline:** clean `development` at `7d48f50603fa0d30464ea7b032f4f0fb82c3964c`; `origin/main` at `c16997e003fbd1726d1205734380394781c52002`.
- **Scope:** T-045–T-056, including optional T-056; 57 original documentation items plus the already-fixed living-document item account for all 58 Track B.2-2 findings.
- **Authorization:** maintainer requested this track, `development` only, two fresh independent review rounds per implementation step, fixes/commits between rounds, and approval of new ADRs before implementation.
- **Publication baseline:** [PR #49](https://github.com/HodeTech/Tyrne/pull/49) is still open from the same `development` head. Keep this preparation local; publishing a separate track PR requires that predecessor to be merged or the maintainer to choose a combined PR explicitly.

## Evidence and existing-document review

The governing agent instructions, previously read numerical ADR corpus and standards are the process basis; the preflight rechecked the task contracts and relevant decision/source passages against this baseline.
Three independent read-only agents examined architecture/onboarding, roadmap/task/review/ADR history, and standards/CI/automation respectively.
Their findings were reconciled against the source; these are preflight advisory checks, not either of the two implementation review rounds and not an approval-promotion verdict.

| Area | Existing documents and authoritative evidence reviewed | Required disposition |
|------|------------------------------------------------------|----------------------|
| Scope and status | [Phase B.2](../../roadmap/phases/phase-b2.md), [current focus](../../roadmap/current.md), [roadmap](../../roadmap/README.md), [phase index](../../roadmap/phases/README.md), [tasks process](../tasks/README.md), [B.2 task index](../tasks/phase-b2/README.md), all twelve task briefs | Keep B.2 Active and C/D gated; select this track without closing the later HIGH-correctness checkpoint. |
| Architecture | All nine existing chapters and [architecture index](../../architecture/README.md); ADRs 0007–0012, 0014, 0017–0023 and 0027–0039 where their mechanisms apply; current HAL/kernel/BSP/userland implementations | Review whole owned chapters for current-versus-planned claims, not only the stale sentences named at opening. |
| Historical closure | [Phase B plan](../../roadmap/phases/phase-b.md), T-020–T-029, first-parent merge history and the B5/B6 closure/security/performance records | Reconcile merged task states from evidence; preserve historical measurements and findings. |
| Reviews and reports | Four family indexes/master plans, master-review index and cited tracks, B6 performance review, old coverage/Miri reports, Track B.2-1 records | Add missing discovery links, repair navigation and obtain fresh reports now. |
| Entry points | Root README, CONTRIBUTING, SECURITY, guides/index, glossary, NOTICE/LICENSE and add-bsp/start-task skills | Repair clean-checkout instructions and current security boundaries; copyright remains a maintainer identity choice. |
| Standards and CI | Testing, error handling, logging, code/commit/review style, release and BSP checklist; infrastructure/CI guide, Cargo manifests/config, workflows, shell/Python tooling and versioned protection | Separate factual corrections from rule changes; implement the approved consistency gate without altering required-check identity. |
| ADR history | ADR-0008/0011/0012/0018/0033 and their sources; ADR-0025/0040 governance, ADR template/index; C–J phase ledgers and cross-phase references | Apply dated append-only corrections; migrate tentative identities by meaning; report index anomalies honestly. |

### Verified findings that change the writing brief

1. **The architecture is more stale than its banners.** Overview/HAL describe a nonexistent `BootInfo`/userspace-init handoff, priority/preemption and driver/IRQ service paths as current. The live reference BSP owns bring-up, runs kernel A/B plus one real EL0 `hello`, and uses a single-core cooperative scheduler. Rewrite or clearly label planned behavior with its actual decision/roadmap authority.
2. **Current fault isolation and teardown must be precise.** [The vector path](../../../bsp-qemu-virt/src/vectors.s) sends non-SVC synchronous faults to panic; [task exit](../../../kernel/src/sched/mod.rs) stops scheduling without reclaiming task/AS/table resources. The [Phase-B seam review](../reviews/security-reviews/2026-06-01-phase-b-closure.md) already tracks these limits. Remove present-tense TaskFault/supervisor/cleanup promises from current-state descriptions without implementing those future mechanisms here.
3. **Kernel IPC and EL0 syscall IPC are different surfaces.** [The dispatcher](../../../kernel/src/syscall/dispatch.rs) calls the bare send/receive primitives; [scheduler bridges](../../../kernel/src/sched/mod.rs) provide separate blocking/context-switch behavior. Explain the actual contract instead of attributing every bridge behavior to the five-syscall v1 ABI.
4. **Capability tables and rights are source-defined.** [CapObject](../../../kernel/src/cap/mod.rs) has five live variants; [rights](../../../kernel/src/cap/rights.rs) include DUPLICATE/DERIVE/REVOKE/TRANSFER and the IPC/console rights. Scope correlation, cross-table revocation and illustrative future kinds must not be described as already-enforced contracts.
5. **Memory/loader claims need a full consistency pass.** Bootstrap identity mode is temporary; current kernel high-half/per-task TTBR0 operation is live. The [loader](../../../kernel/src/obj/task_loader.rs) converts embedded high VA to PA for overlap checking. Correct its L3 arithmetic and half-open range description; NX does not prevent return-oriented execution through existing executable code.
6. **The clean-checkout command sequence is incomplete.** [BSP build.rs](../../../bsp-qemu-virt/build.rs) requires `hello.bin`; README and the two-task guide need `tools/build-userland.sh` before a direct kernel build. Update current guides before indexing them as current onboarding instructions.
7. **Smoke observations are not all script assertions.** [smoke.sh](../../../tools/smoke.sh) enforces profile-specific markers and panic/fault rejection; its `--int` trace prints exception events but does not assert an exact two-SVC count. Capture debug/release traces and inspect/count them explicitly. Do not claim `guest_errors` was enabled by `--int`, which uses `int,unimp`.
8. **Task-opening snapshots need reconciliation.** T-047 must record the completed T-030–T-037 wave as current history, not reset “last completed” to T-029. T-050 adds four glossary terms, so the baseline 50 headwords would become 54, not the stale 52-anchor expectation. Architecture index coverage citations are not evidence that T-024/T-028 edited a chapter: actual edit history and implementation coverage are separate facts.
9. **The unimplemented lint option is not a harmless one-line change.** [tyrne-user host stubs](../../../userland/tyrne-user/src/lib.rs) deliberately call `unimplemented!`; required ARM workspace Clippy compiles those stubs. Document the current lint/review boundary rather than adding a global deny in this track.
10. **Historical index and link drift is concrete.** Five canonical closure reviews are missing from indexes, Phase B indexes 15 of 23 task files, and three A/B task links are broken. Additional historical/master-plan links require bounded repair before a whole-corpus gate can start green. Preserve old quoted paths and verdicts; use historical permalinks where current targets would change the evidence.
11. **The IrqGuard diagnosis has provenance but lacks retained proof.** Commit `4fe547c` records an observed QEMU failure and generic-dispatch fix, without retained disassembly/Miri/compiler-issue evidence for the generalized `.rodata` aliasing explanation. Retract that unverified explanation, acknowledge the historical observation and retain the defensible direct-dispatch rationale.
12. **ADR index “no anomalies” is not true at baseline.** Existing descriptive-title differences, ADR-0023's prose-extended Date/Deferred status, ADR-0022's partial supersession and reserved 0034 need explicit handling. Reconcile source metadata and procedure vocabulary without guessing dates, changing historical decisions or hiding anomalies.
13. **The automation language premise is obsolete.** Python already runs in the required lint job. Use Python 3.9+ standard library, compatible with local Python 3.9.6, and verify Linux execution remotely; syntax compilation is not a formatter/linter.

## Decisions presented before implementation

All recommendations below are proposals. Acceptance of the referenced ADRs and approval of the listed contract reconciliations precede implementation; elapsed time is not approval.

| Decision | Recommendation | Approval / implementation boundary |
|----------|----------------|-------------------------------------|
| Historical naming rule | File [ADR-0041](../../decisions/0041-test-name-prefix-policy-recovery.md), then explicitly accept the recovered historical rule before superseding it. | Do not imply an earlier ADR approval or rename tests during recovery. |
| Current test naming | Accept [ADR-0042](../../decisions/0042-descriptive-test-names.md): descriptive names without mandatory `test_`, real examples, review-enforced clarity. | Separate Accept/supersession commit; then T-052 changes the standard. |
| Planned ADR identity | Accept [ADR-0043](../../decisions/0043-documentation-corpus-consistency.md): unique milestone-plus-purpose slugs; numeric IDs assigned at filing. | T-054 migrates live rows/references; 0034 and filed numbers stay intact; ADR-0040 gets an additive clarification. |
| T-056 tool/gate | Include optional T-056; Python 3.9+ stdlib, offline deterministic command and isolated fixtures, failing step inside existing required lint job. | Accept ADR-0043 before any CI/policy implementation. No seventh required context or third-party package. |
| Panic documentation | Describe banner + PanicInfo message/location + spin/halt, distinguish saved exception diagnostics from generic panic-time registers. Approve removing T-052's automatic register-dump follow-up obligation. | This closes a false current-state claim; no new register-dump feature or ungrounded implementation promise is made. Choosing a feature instead needs a separately scoped task/design before proceeding. |
| `unimplemented!` and lint scope | State that `todo` is workspace-denied, `unimplemented!` relies on review, and panic-family per-crate denies apply to kernel/HAL/BSP with scoped allowances. | Preserve host stubs and avoid expanding runtime/lint policy in a documentation correction. |
| Copyright identity | Pending maintainer answer: proposed common line `Copyright 2026 HodeTech, Cemil İlik and Tyrne contributors`. Alternatives are either existing holder string. | No NOTICE/LICENSE edit until the exact holder wording is supplied/approved; this is textual alignment, not an inferred rights transfer. |
| History and fresh evidence | Archive old current-focus material; add missing B6 template sections as dated structural reconciliation; mechanically repair archive links; run fresh coverage/Miri reports now. | Keep historical verdicts, sources and measured numbers intact. No fabricated retrospective runs. |
| Commit scopes | Recommend `syscalls`, `architecture`, `bsp-<board>` for new examples; document historically used aliases/prior-use scopes and retain the existing review-agreement extension rule. | No new prohibition or static commitlint allowlist. |
| Dependency execution | Extend reviewed stacked execution to this track as specified by ADR-0043. | Both rounds and verification must pass before dependent work starts; all new task states stop at In Review. |

### ADR approval sequence

The initial proposal commit contains ADR-0041 and ADR-0042 together so their cross-links resolve at every committed checkpoint.
After approval: accept the historical recovery separately, then accept ADR-0042 and supersede ADR-0041 with both index/callout directions intact.
Accept ADR-0043 separately and append its dated ADR-0040 clarification before applying its standard/CI changes.
The standard-change skill's proposal cross-links are staged through task/plan/index references here; the standards themselves are edited only after Acceptance.

## Task-contract reconciliation

After approval, each affected task receives a dated reconciliation entry linking this plan and its applicable ADR, then its literal AC/DoD text is corrected before the task is implemented.
Its original opening history remains intact.
Task “Ready” at baseline is not authority to bypass a newly identified ADR precondition.

| Task | Reconciled scope and acceptance evidence |
|------|------------------------------------------|
| [T-045](../tasks/phase-b2/T-045-docs-overview-taskloader-arch-index.md) | Whole entry-chapter current/planned sweep; define freshness as source baseline/date/owning task; distinguish document history from implementation coverage. Recheck overview boot/index after T-046. |
| [T-046](../tasks/phase-b2/T-046-docs-subsystem-chapters-refresh.md) | Whole seven-chapter factual sweep, including fault/lifecycle, IPC bridge, high-half and HAL contract corrections. Exact SVC count is inspected trace evidence; add independent security review of boundary claims. |
| [T-047](../tasks/phase-b2/T-047-roadmap-state-and-phase-index-sync.md) | Correct all live bullets, preserve and archive dated history, record T-029 as historical completion and T-030–T-037 as the latest completed wave. Add the three seam-review carry-forwards with their actual triggers. |
| [T-048](../tasks/phase-b2/T-048-phase-b-task-corpus-sync.md) | Existing ten merged task closures, 23-row index and three link repairs. Formalize date_done in template and lifecycle; do not re-author old task implementation evidence. |
| [T-049](../tasks/phase-b2/T-049-review-indices-sync.md) | Five missing canonical reviews; explicit companion/master-review discovery; dated B6 structural repair; fresh coverage/Miri; bounded archive/master-plan link repairs discovered by T-056 baseline scan. Preserve quoted defect provenance. |
| [T-050](../tasks/phase-b2/T-050-entry-docs-and-glossary-sync.md) | Four terms and stable anchors, existing glossary factual corrections, build prerequisites, README current/target labels, two-task/first-userspace guide corrections and safe add-bsp template. Await copyright identity. |
| [T-051](../tasks/phase-b2/T-051-contributing-and-security-status.md) | Current five-syscall/security-limit description and present contribution workflow, including the stale “when implementation begins” section. Maintainer reviews SECURITY wording before merge; disclosure policy is untouched. |
| [T-052](../tasks/phase-b2/T-052-standards-docs-reality-sync.md) | Accepted naming change; approved panic-claim correction without promised register-dump task; truthful lint/logging scope, planned fault/supervision status and downstream-effects search. |
| [T-053](../tasks/phase-b2/T-053-standards-docs-mechanical-fixes.md) | Original eight corrections plus adjacent false tooling-status claims (missing_docs under -D warnings, planned audit/vet, live smoke runner). panic=abort target flags also cover userland built for that same triple. No lint-level change. |
| [T-054](../tasks/phase-b2/T-054-adr-ledger-renumbering-cascade.md) | Purpose identities, semantic cross-phase mapping and live-definition duplicate check; preserve real ADR-0040 references, historical aliases and unnumbered decisions. |
| [T-055](../tasks/phase-b2/T-055-adr-append-only-corrections.md) | Five dated append-only ADR corrections and IrqGuard comment; source-based ADR-index normalization with anomalies reported/resolved; align sync procedure vocabulary to existing template/partial-supersession precedent. |
| [T-056](../tasks/phase-b2/T-056-docs-consistency-automation.md) | Approved Python/gate/slug/index/history/audit contracts from ADR-0043; real syntax + fixture verification and independent style review replace the stale generic formatter/linter requirement. Run whole-corpus green before enabling CI. |

Each step's allowed diff consists of its named task content plus the necessary task/current/track index updates, governing decision references, review artifacts and review index entries.
Assess the allowlist on that step's commit range, not the entire stacked development diff.
Extra file changes require a demonstrated existing-scope reason and a recorded review disposition; this is not authority for unrelated cleanup.

## Execution steps after approval

Each row is a review boundary; large rows may use several focused commits inside the step, without skipping either review round.
The same root author implements changes; reviewers do not mutate the shared worktree.

| Step | Tasks | Delivered result and verification |
|------|-------|-----------------------------------|
| 0 | ADR package / preflight | Reviewable Proposed documents, separate Acceptance transitions after explicit approval, corrected task briefs. No task delivery claimed. |
| 1 | T-051 | CONTRIBUTING/SECURITY describe current EL0 boundary and workflow. Verify against ABI/dispatcher/vector/exit source; separate code/document and security review roles. |
| 2 | T-045 | Define freshness convention; refresh overview/loader/index and architecture closure hook. Capture fresh debug/release QEMU traces, inspect SVC/fault counts and verify source-backed mapping/loading claims. |
| 3 | T-046 | Refresh seven subsystem chapters; recheck Step 2 overview/index/boot diagram coherence. Independent architecture/correctness and security-boundary reviews. |
| 4 | T-048 | Close already-merged Phase-B task records from exact merge evidence, index/date_done/template/lifecycle and known task-link repairs. Verify membership/status/date and historical evidence preservation. |
| 5 | T-049 | Complete review discovery and bounded link repairs; reconcile B6 template using existing evidence; run and commit fresh source-bound coverage/Miri reports. Check all canonical membership, historical provenance and repaired targets. |
| 6 | T-050 | README, guides, glossary, skill instructions and approved NOTICE/LICENSE wording. Verify clean-checkout command prerequisites, live traces, anchor uniqueness/order and source-defined terminology. |
| 7 | T-055 | Apply five ADR corrections and comment; normalize source/index metadata and report known conventions. Verify append-only diffs, fmt/host-clippy/host-test and unchanged runtime source apart from the doc comment. |
| 8 | T-052, T-053 | Reconcile overlapping standards in focused commits under Accepted policy. Verify actual CI/lints/config, downstream references, fence tags and scope history. |
| 9 | T-054 | Migrate all 32 planned-purpose rows plus live references; append ADR-0040 clarification if not already filed at Acceptance. Verify unique definitions, resolved references and historical/filed-number preservation. |
| 10 | T-047 | Concise accurate live focus plus preserved archive, B6 status tags and Phase-C seam carry-forwards. Verify live status claims against task files and source merge records. |
| 11 | T-056, parser portion | Implement deterministic offline link/fragment parser and meaningful positive/negative fixtures. Run against stabilized full corpus; discovered actual baseline defects return to their named owner rather than being suppressed. |
| 12 | T-056, integration portion | Add task/review/ADR/ledger/fence/audit checks, optional live-state check if reliable, usage documentation and existing-job CI wiring. Verify all isolated rejection/false-positive fixtures, macOS/local and Linux/hosted execution. |
| 13 | Integrated track record | Reverify architecture freshness, all 58 item dispositions and twelve task AC/DoDs; update six entry documents and publish final review/evidence. Leave delivered tasks In Review and create the separate PR after the predecessor publication barrier clears. |

### The review loop for every implementation step

1. Implement the step, run its applicable checks and commit a reviewable result with English conventional messages and actual ADR references.
2. Start round 1 with fresh independent agents. Use at least two complementary contexts; architecture/security-sensitive descriptions receive a distinct security pass, and checker/CI changes receive parser/adversarial plus integration coverage. Select model/effort according to complexity (normally high effort; governance/parser seams may use the frontier model).
3. Independently validate each finding against the source/evidence, record its disposition, fix verified issues, rerun affected checks and commit.
4. Start round 2 with different fresh contexts. Verify the first-round corrections and the cumulative step rather than only its last patch; fix/commit confirmed findings and run the affected checks.
5. Complete the step only when no verified blocker remains. Record both rounds using the relevant master-plan roles and index the artifact, then continue automatically to the next step.

The preparation documents also receive two fresh independent rounds before they are presented for approval; those rounds assess proposal readiness, not ADR Acceptance or task delivery.
No external review comments/messages or live policy changes are needed by this plan.

## Verification and evidence contract

- **Documentation steps:** check relative targets and fragments, fence/diagram form, task/index/current coherence, changed-file scope and `git diff --check`; verify factual prose against source and cite the decisions that supply its authority.
- **Trace-bearing steps:** build userland first, build matching kernel debug/release, capture `tools/smoke.sh --int` and `--release --int`, retain exact raw evidence with source/toolchain/QEMU identity, and distinguish inspected exception counts from automated marker/fault gates.
- **Fresh reports:** execute the pinned-toolchain workspace Miri command excluding only the BSP and the repository coverage command; record actual counts/percentages/limitations, not the opening expected numbers. Old reports remain historical.
- **Comment-bearing T-055:** fmt, host Clippy and host tests as required by the task; validate no executable Rust/unsafe delta.
- **Automation:** syntax compilation plus isolated unittest/CLI fixtures for every implemented check and valid edge form; fixtures operate in temporary roots, never by committing deliberate regressions or creating branches. Validate Python 3.9 compatibility locally and the available hosted Python interpreter on Linux.
- **CI publication:** inspect exact-source PR/push results and new step logs. All six required contexts retain app 15368 bindings; coverage/performance remain informational. Hosted evidence is recorded only after actual execution, with first-main evidence remaining merge-dependent where relevant.
- **Traceability:** task histories name commits, verification and review rounds. New tasks/ADRs remain Proposed/In Review until the applicable maintainer action; existing Phase-B merge closure is separately evidenced historical reconciliation.

## Publication and remaining phase work

Stay on `development` throughout.
At preparation, PR #49 owns this same remote source branch, so pushing new commits would enlarge that already-open bookkeeping PR.
Keep proposals/local implementation local until its merge, unless the maintainer explicitly chooses to combine the work; do not close, merge or repurpose PR #49 silently.
After its merge, fetch and reconcile ancestry on development without changing main or discarding local commits, then publish the Track B.2-2 PR from the same branch.

Selecting this documentation track is the maintainer's requested order, not a claim that T-038 or the other correctness work completed.
HIGH T-038 remains Ready; T-039/T-040 and later decision-bearing tasks keep their own preconditions.
ADR-0040's scope checkpoint still follows CI and HIGH-correctness work, and all Phase B.2 exit criteria still gate C/D.
This plan does not add implementation tasks or change the 46-task phase inventory.
