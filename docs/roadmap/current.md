# Current focus

The live pointer to selected work, task states and review triggers. Dated banners and earlier live-state/Notes snapshots are preserved in [current-archive.md](current-archive.md); the full plan is in [phases/](phases/).

<!-- current-state:start -->
## Live state — 2026-10-16

- **Active phase:** [B.2 — Consolidation & Hardening](phases/phase-b2.md), mandatory whole-phase gate before C/D under [ADR-0040](../decisions/0040-phase-b2-consolidation-bridge.md). Phase C and D remain gated.
- **Selected track:** B.2-2 is Done under the approved [13-step plan](../analysis/reports/2026-10-12-phase-b2-track2-preflight-and-plan.md), including reviewed ADR-0044 maintenance. All twelve tasks T-045–T-056 are Done after PR49 merge and explicit maintainer completion authorization.
- **Active task:** None. [Post-merge verification](../analysis/reviews/business-reviews/2026-10-16-phase-b2-track2-completion.md) binds merged source `52fa323`, first-main CI and completed criteria. HIGH T-038 is the next Ready candidate; it has not started.
- **Working branch:** development, as requested by the maintainer.
- **Last completed work:** Track B.2-2 / T-045–T-056, Done on 2026-10-16 (Europe/Istanbul) after [PR49](https://github.com/HodeTech/Tyrne/pull/49) merge at `52fa323`, verified first-main gates and explicit authorization. Track B.2-1 / T-030–T-037 remains Done after PR48.
- **Historical completion:** [T-029](../analysis/tasks/phase-b/T-029-perf-microbench.md), Phase 1 [PR #44](https://github.com/HodeTech/Tyrne/pull/44) and Phase 2 [PR #45](https://github.com/HodeTech/Tyrne/pull/45), both merged 2026-06-01. Its recovered dated banner is in the archive.
- **Last completed milestone:** B6 / Phase B, closed by [PR #43](https://github.com/HodeTech/Tyrne/pull/43) on 2026-06-01 at `ca932ac`; b6-closure is merged and retired. No Phase B closure review remains pending.
- **In review:** none. **In progress:** none. **Phase inventory:** 46 tasks — 20 Done, 19 Ready, 0 In Review, 0 In Progress, 7 Draft; see the [task index](../analysis/tasks/phase-b2/README.md).

### Selected task states

| Task | Status |
|------|--------|
| [T-045](../analysis/tasks/phase-b2/T-045-docs-overview-taskloader-arch-index.md) | Done |
| [T-046](../analysis/tasks/phase-b2/T-046-docs-subsystem-chapters-refresh.md) | Done |
| [T-047](../analysis/tasks/phase-b2/T-047-roadmap-state-and-phase-index-sync.md) | Done |
| [T-048](../analysis/tasks/phase-b2/T-048-phase-b-task-corpus-sync.md) | Done |
| [T-049](../analysis/tasks/phase-b2/T-049-review-indices-sync.md) | Done |
| [T-050](../analysis/tasks/phase-b2/T-050-entry-docs-and-glossary-sync.md) | Done |
| [T-051](../analysis/tasks/phase-b2/T-051-contributing-and-security-status.md) | Done |
| [T-052](../analysis/tasks/phase-b2/T-052-standards-docs-reality-sync.md) | Done |
| [T-053](../analysis/tasks/phase-b2/T-053-standards-docs-mechanical-fixes.md) | Done |
| [T-054](../analysis/tasks/phase-b2/T-054-adr-ledger-renumbering-cascade.md) | Done |
| [T-055](../analysis/tasks/phase-b2/T-055-adr-append-only-corrections.md) | Done |
| [T-056](../analysis/tasks/phase-b2/T-056-docs-consistency-automation.md) | Done |

### Next work and review triggers

- **Next work:** HIGH [T-038 — console_write x2 clobber](../analysis/tasks/phase-b2/T-038-console-write-x2-clobber.md), Ready and unstarted. Its unsafe Amendment, separate security review and userland/QEMU evidence remain required. No new ADR is required for its existing contract.
- **Next review trigger:** T-038 implementation and required code/security rounds when explicitly started. B.2-2 implementation, integrated reviews and all three maintenance units are complete; [post-merge retrospective](../analysis/reviews/business-reviews/2026-10-16-phase-b2-track2-completion.md) records actual closure. Whole-phase readiness/closure remains at T-074/T-075.
- **Following correctness work:** [T-038 — console_write x2 clobber](../analysis/tasks/phase-b2/T-038-console-write-x2-clobber.md) is Ready/HIGH and has not started. T-037 is Done; the documentation track does not clear this checkpoint. Eventual whole-phase closure reviews belong to [T-075](../analysis/tasks/phase-b2/T-075-phase-b2-closure.md); all B.2 exit gates still apply to C/D.

### Active decisions

[ADR-0030](../decisions/0030-syscall-abi.md), [ADR-0031](../decisions/0031-initial-syscall-set.md), [ADR-0033](../decisions/0033-kernel-high-half-migration.md), [ADR-0037](../decisions/0037-el0-entry-context.md), [ADR-0038](../decisions/0038-mmu-translate-and-user-access.md), [ADR-0039](../decisions/0039-userland-build-pipeline.md), [ADR-0040](../decisions/0040-phase-b2-consolidation-bridge.md), [ADR-0042](../decisions/0042-descriptive-test-names.md), [ADR-0043](../decisions/0043-documentation-corpus-consistency.md), [ADR-0044](../decisions/0044-review-evidence-retention.md) are Accepted. [ADR-0041](../decisions/0041-test-name-prefix-policy-recovery.md) is Superseded by ADR-0042. The [complete ADR index](../decisions/README.md) includes all filed statuses and reserved 0034. T-016 is completed history, not a draft task.

### Last reviews

- **2026-10-16:** [B.2-2 completion retrospective](../analysis/reviews/business-reviews/2026-10-16-phase-b2-track2-completion.md), after PR49 merge and explicit Done authorization; first-main seven jobs/six app-15368 contexts pass, all twelve tasks and all 161 criteria complete.

- **2026-10-15:** [Track B.2-2 integrated code](../analysis/reviews/code-reviews/2026-10-15-phase-b2-track2-integration.md) and [separate security](../analysis/reviews/security-reviews/2026-10-15-phase-b2-track2-integration.md), both fresh rounds complete at7d1eca0. One Low README-target finding fixed/verified, zero unresolved findings. Twelve tasks In Review; human SECURITY wording and PR merge remain.

- **2026-10-15:** [T-056 Step12 code](../analysis/reviews/code-reviews/2026-10-15-t056-integration.md) and [separate security](../analysis/reviews/security-reviews/2026-10-15-t056-integration.md), both rounds complete at4044b79; all nine groups closed. Exact-source hosted evidence passes; later final-tip/Step 13 gates remain.

- **2026-10-15:** [T-056 Step11 both code rounds](../analysis/reviews/code-reviews/2026-10-13-t056-parser.md) and [separate security rounds](../analysis/reviews/security-reviews/2026-10-13-t056-parser.md), with explicitly attributed replacement R2 committed-fix verification at830de9d; all verified findings closed. Full task/remaining CI/hosted delivery is pending.

- **2026-10-13:** latest completed step, [T-047 both fresh code/security rounds](../analysis/reviews/code-reviews/2026-10-13-t047-roadmap-state-reconciliation.md); zero confirmed or unresolved source findings. Earlier B.2-2 steps are linked by the [code](../analysis/reviews/code-reviews/README.md) and [security](../analysis/reviews/security-reviews/README.md) indexes.
- **2026-10-12:** [Track B.2-1 completion retrospective](../analysis/reviews/business-reviews/2026-10-12-phase-b2-track1-completion.md), after PR #48 merge and verified merged-main gates.
- **2026-07-15:** full-repository review, a local-only document that is not in the repository. [Phase B.2](phases/phase-b2.md) and its [task corpus](../analysis/tasks/phase-b2/README.md) are self-contained; no private-file link is needed to execute their contracts.
- **2026-06-01:** [Phase B business closure](../analysis/reviews/business-reviews/2026-06-01-phase-b-closure.md), [consolidated seam security review](../analysis/reviews/security-reviews/2026-06-01-phase-b-closure.md), [T-028 EL0 security review](../analysis/reviews/security-reviews/2026-06-01-T-028-el0-userspace-wireup.md) and [B6 performance baseline](../analysis/reviews/performance-optimization-reviews/2026-06-01-B6-closure.md).
- **2026-05-31:** [T-022 high-half security review](../analysis/reviews/security-reviews/2026-05-31-T-022-high-half-migration.md). Its review date is distinct from PR36's May 30 integration date.

### Notes

The [unsafe log](../audits/unsafe-log.md) has 33 entries: 32 Active, one Removed (0012), recounted 2026-10-13 in the [source inventory](../analysis/reports/2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t047-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t047-verification-evidence/semantic-baseline.json"). This metadata inventory is not a new unsafe audit or runtime security proof. B.2-2 Done promotions now rest on actual PR49 merge and explicit maintainer authorization; future task promotions retain their own review/merge gates.

<!-- current-state:end -->

> **Evidence migration (2026-10-16).** Raw evidence links now open the [immutable archive catalog](../analysis/reports/2026-10-16-pr49-evidence-catalog.md). Each link title retains its exact archived member path. Original verdicts, measurements, limitations and execution SHA identities remain historical; the archive bundle restores their original source.
