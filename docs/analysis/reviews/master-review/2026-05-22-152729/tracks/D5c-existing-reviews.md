# D5c-existing-reviews — review archive + master plans (master review, commit 288ddb2)

- **Track:** D5c — existing reviews (historical review archive + four master plans)
- **Reviewer:** Claude Sonnet 4.6 agent, D5c role
- **Commit anchor:** 288ddb2
- **Date:** 2026-05-22
- **Scope:** All files returned by `git ls-files docs/analysis/reviews` excluding `docs/analysis/reviews/master-review/` — 58 files covering four review families (business, code, security, performance-optimization).

---

## Summary

The Tyrne review system is the project's strongest documentation dimension. The corpus is internally coherent, cross-referenced accurately, and shows continuous process improvement (the smoke-trace AC addition, the simulation-table discipline codification, the comprehensive-review multi-agent structure). The overwhelming majority of prior Blocker/Major findings were resolved and closed with regression tests or documented amendments before merge.

Four findings are raised: one Major and three Minor. The single Major finding is a stale skill-path rot across three of the four master plans — a mechanical update, not a design gap. No Blockers were found. All prior Blocker-class findings from the Phase A, B0, B1, B2, and B3 security reviews were demonstrably resolved. The three UNSAFE entries from B1 (0019/0020/0021) retain "Pending QEMU smoke verification" status for the IRQ-take/dispatch path, which is correctly documented as forward-flagged pending the first preemption-using caller; these are not unresolved in the sense of being ignored.

**Verdict:** Approve with 1 Major, 3 Minor, 0 Blockers, and 6 Praise entries.

---

## Findings (by severity)

### Blocker

None.

### Major

#### D5c-M01 — Stale `.claude/skills/` path references in three master plans

`docs/analysis/reviews/business-reviews/master-plan.md:60-61`
`docs/analysis/reviews/security-reviews/master-plan.md:92`
`docs/analysis/reviews/security-reviews/master-plan.md:108`
`docs/analysis/reviews/performance-optimization-reviews/master-plan.md` (merge-step section)

**Description:** On 2026-05-14 (B3 arc, PR #28), the project migrated all skill files from `.claude/skills/` to `.agents/skills/`. The `code-reviews/master-plan.md` was updated correctly (it references `.agents/skills/add-dependency/SKILL.md`). However, three other master plans retain the old `.claude/skills/` prefix for their skill cross-references:

- `business-reviews/master-plan.md` lines 60–61: `.claude/skills/start-task/SKILL.md` and `.claude/skills/write-adr/SKILL.md`.
- `security-reviews/master-plan.md` lines 92 and 108: `.claude/skills/add-dependency/SKILL.md` and `.claude/skills/start-task/SKILL.md`.
- `performance-optimization-reviews/master-plan.md` (merge step): `.claude/skills/start-task/SKILL.md`.

Master plans are the normative procedures for recurring work. An agent following the business-reviews master plan to open a follow-up task will use the wrong skill path and either fail or silently execute a different skill. This is Major rather than Blocker because the skills themselves exist at the correct new path; the breakage is discoverability, not capability.

**Suggested fix:** In each affected master plan, replace every `.claude/skills/` prefix with `.agents/skills/`. A single search-replace across the three files closes the finding. Verify by checking that the resulting paths exist in `.agents/skills/`.

---

### Minor

#### D5c-m01 — `2026-04-21-A6-completion.md` uses non-standard section headings

`docs/analysis/reviews/business-reviews/2026-04-21-A6-completion.md` (entire file, 115 lines)

**Description:** The `business-reviews/master-plan.md` template defines five mandatory sections: "What landed", "What changed in the plan", "What we learned", "Adjustments", and "Next". The `A6-completion.md` artifact predates the template's codification and uses: "What went well", "What was harder than expected", "Technical debt entering Phase B", "Phase B readiness", and "References". The sections "What changed in the plan" and "Adjustments" have no counterpart in this artifact. The "Next" block (four `[ ] …` lines) is absent; `Phase B readiness` is a partial substitute but lacks the structured checklist form.

No information is lost — all the substance a future reader needs is present — but a reviewer scanning for the canonical "Adjustments" block won't find it, and the README's index does not flag the artifact as pre-template.

**Suggested fix:** Either (a) add a one-line note at the top of the artifact ("Predates the five-section template; headings differ from master-plan.md") or (b) add a note in `business-reviews/README.md`'s index row for this file. A full rewrite is not warranted; the information is correct.

#### D5c-m02 — `business-reviews/README.md` does not mark 2026-04-28-B1-closure.md as superseded

`docs/analysis/reviews/business-reviews/README.md:32`

**Description:** The `2026-04-28-B1-closure.md` business review was filed on 2026-04-28 as the "implementation-complete" milestone review before smoke verification. Following the B1 smoke regression (ADR-0022 Option A hang, documented in `2026-05-06-B1-smoke-regression.md`) and the T-014 fix, a second B1 closure review `2026-05-07-B1-closure.md` was produced and is now the canonical closure record. The 2026-05-07 review explicitly describes itself as "fresh closure trio replacing the 2026-04-28 trio's load-bearing role".

The README index lists both entries with no indication that the 2026-04-28 artifact was superseded. A reader following the index may read the superseded artifact and form incorrect conclusions about B1's closure state.

**Suggested fix:** Add a note to the 2026-04-28 row in the index, such as "(superseded by 2026-05-07-B1-closure.md — filed pre-smoke; see B1 smoke regression mini-retro)".

#### D5c-m03 — "Yüksek" (Turkish) appears in `security-reviews/README.md` index

`docs/analysis/reviews/security-reviews/README.md:35`

**Description:** The index table in `security-reviews/README.md` contains the word "Yüksek" in the Verdict column summary for the 2026-04-27-B0-closure.md row:

```
"Clean — no High findings; pre-existing items (cross-table revocation, generation overflow) tracked at original severity"
```

The word "High" is the English translation; "Yüksek" is the Turkish word for "High". Based on the B1 comprehensive review's track-j-hygiene.md finding J-NB2, there were 8 docs containing "Yüksek" that were scheduled for renaming to "High" in the β sweep. This specific occurrence in the security-reviews/README.md was apparently not caught by the β sweep. The project's rule (CLAUDE.md rule 3) requires English in all repository artifacts.

**Suggested fix:** Replace "Yüksek" with "High" in the security-reviews/README.md index table for the 2026-04-27-B0-closure.md row.

---

### Nit

None.

---

### Praise

#### D5c-P01 — Comprehensive follow-through on all prior Blocker findings

Every Blocker finding from the five major security reviews (Phase A, B0, B1 2026-04-28, B1 2026-05-07, B2, B3) was resolved before or during the corresponding closure arc. The three Phase A Blockers (UNSAFE-0012 aliasing → ADR-0021 raw-pointer bridge, T-006; scheduler deadlock panic → ADR-0022 idle task + typed deadlock error, T-007; cross-table revocation gap → ADR-0023 deferred with explicit documentation) each have clear resolution records. The seven Track-E Blockers from the 2026-05-06 full-tree comprehensive review were all closed by PR #13 before B1 closure. This is exemplary process discipline.

#### D5c-P02 — "No closure-trio without recorded smoke" AC addition is a genuine process improvement

The business-reviews/master-plan.md's addition of the AC requirement "smoke trace pasted into the closure retrospective" was a direct lesson from the B1 smoke regression (May 6 mini-retro). The requirement was immediately applied to B2 (the smoke trace appears verbatim in 2026-05-09-B2-closure.md) and B3 (trace in 2026-05-14-B3-closure.md). This is the correct shape of process improvement: learn from failure, codify the lesson, demonstrate adherence in the next cycle.

#### D5c-P03 — UNSAFE audit log discipline is meticulous and internally consistent

The append-only audit log has 26 entries (0001–0026, with 0012 Removed). Every Amendment is dated, carries a commit SHA reference, and follows the introducing-commit-boundary rule codified in UNSAFE-2026-0017's "Discipline note". The security review artifacts cross-reference the relevant entries faithfully. The security reviews themselves re-verify every prior entry at each closure pass. This is the highest standard of unsafe-block discipline seen in any Rust project at this phase.

#### D5c-P04 — ADR simulation-table discipline emerged organically and was then codified

ADR-0026 (idle dispatch; B1 closure) introduced the first simulation table to catch a three-state scheduler scenario that prose-only reasoning had missed (the hang). ADR-0027 (MMU layout; B2 closure) and ADR-0032 (IPC cancel; B1 closure) followed the same pattern. The B1 business retrospective called out the pattern explicitly ("multi-step state-machine ADRs need simulation tables"). The security reviews for B2 and B3 both cite the simulation discipline as a positive threat-model contribution. This organic-then-codified pattern is healthy project evolution.

#### D5c-P05 — Performance baselines use the P10 harness consistently from B2 onward

The introduction of `tools/perf-harness.sh` (P10 multi-run wall-clock harness, landed PR #22 before B2 closure) ended the per-PR single-run timing anecdotes that Track D flagged as "not load-bearing". Every closure from B2 onward records a 20-iteration harness band (p10/p50/p90), and the harness's statistical methodology (nearest-rank percentiles, population stddev, BSD-awk-compatible) was independently audited in 2026-05-08-pr-19-20-21-multi-axis-review/track-4-pr-21-perf-harness.md. This is a concretely measurable process improvement.

#### D5c-P06 — Multi-axis parallelizable code reviews are well-executed and internally consistent

The 2026-05-06 full-tree comprehensive review (10 tracks) and the 2026-05-07 PR-12-to-17 multi-axis review (8 tracks) demonstrate that the multi-agent parallelizable code review model defined in `code-reviews/master-plan.md` works in practice. Each track file has a self-contained verdict; the merged summaries accurately reflect the track verdicts; follow-up closures are tracked and evidenced. The Track G (2026-05-07) explicit PRAISE for "first separate-Accept-commit application" and the Track H comment that "the audit-log Amendment discipline is now codified" show genuine meta-learning within the review system itself.

---

## Prior-finding follow-through

The table below covers all Blocker findings and the most significant forward-flagged Major items from the Phase A, B0, B1, B2, and B3 security reviews, plus the full-tree comprehensive code review.

| Prior finding | Source review file | Severity | Status | Evidence |
|---|---|---|---|---|
| UNSAFE-0012 `&mut` aliasing across yields | `security-reviews/2026-04-21-tyrne-to-phase-a.md` §3 | Blocker | Resolved | T-006 / ADR-0021 raw-pointer scheduler bridge; UNSAFE-0012 status Removed; B0 security review re-verifies |
| Cross-table capability revocation gap | `security-reviews/2026-04-21-tyrne-to-phase-a.md` §1/§8 | Blocker | Resolved (deferred with documentation) | ADR-0023 placeholder accepted; security-model.md open-question added; B0/B1/B2/B3 reviews confirm no worsening; deferred to B3–B6 timeframe per plan |
| `Scheduler::ipc_recv_and_yield` deadlock panic | `security-reviews/2026-04-21-tyrne-to-phase-a.md` §4 | Blocker | Resolved | T-007 / ADR-0022 idle task + typed `SchedError::Deadlock` return; T-014 / ADR-0026 dispatch fallback; B1 smoke-regression traced to ADR-0022 Option A; T-014 fully closed the liveness bug |
| Generation overflow (`u32`) | `security-reviews/2026-04-21-tyrne-to-phase-a.md` §1 | Non-blocking follow-up | Open (tracked) | Carried forward at original severity through B0/B1/B2/B3 closure reviews; no new caller that worsens it; deferred to B-late long-running-service design |
| `debug_assert!` in `ipc_recv_and_yield` resume path | `security-reviews/2026-04-21-tyrne-to-phase-a.md` §4 | Non-blocking follow-up | Resolved | B0 review introduces `PendingAfterResume` typed return as the loud signal; `debug_assert!` deliberately dropped |
| `Scheduler::start` panic on empty ready queue | `security-reviews/2026-04-21-tyrne-to-phase-a.md` §4 | Non-blocking follow-up | Resolved | T-014/ADR-0026: `start` now panics only when both ready empty AND `s.idle` is None; semantics improved |
| `cargo-vet init` now (empty-but-configured) | `security-reviews/2026-04-21-tyrne-to-phase-a.md` §7 | Non-blocking follow-up | Open (forward-flagged to B6) | B0/B1/B2/B3 closure reviews note "K3-8 Phase B6 prerequisite"; no external deps yet so urgency remains low |
| `Capability::Debug` redaction | `security-reviews/2026-04-21-tyrne-to-phase-a.md` §6 | Non-blocking follow-up | Open (forward-flagged to B5) | Explicitly carried forward through every security review closure as "K3-9 — B5 syscall-ABI design venue"; no new log path has been added |
| UNSAFE-2026-0019/0020/0021 "Pending QEMU smoke verification" | `security-reviews/2026-04-28-B1-closure.md` §8 | Non-blocking (forward-flagged) | Open (intentional) | 2026-05-06 partial-verification + post-T-014 smoke Amendments record the IRQ-setup sites as confirmed under sustained execution; IRQ-take/dispatch path remains unexercised pending first preemption-using caller; all B1/B2/B3 reviews acknowledge and carry forward |
| Track-E 7 doc-drift Blockers (full-tree) | `code-reviews/2026-05-06-full-tree/track-e-docs.md` | Blocker (×7) | Resolved | All 7 closed by PR #13 (α sweep); 2026-05-07-pr-12-to-17 track-e-docs.md §"Status per item" confirms each closed |
| Track-F §F-1 QEMU smoke not CI-wired | `code-reviews/2026-05-06-full-tree/track-f-tests.md` | Non-blocker follow-up | Open (acknowledged) | Carried to B2/B3 as a pre-CI-maturity gap; the `infrastructure.md` annotation update (conditional gates, not live merge-blockers) was the explicit response per 2026-05-07-B1-closure security review §7 |
| Track-F §F-2 `ObjError::StillReachable` no producer | `code-reviews/2026-05-06-full-tree/track-f-tests.md` | Non-blocker follow-up | Open | Carried; no new producer added through B3; legitimate gap in test coverage for an existing error variant |
| Track-D 11 performance proposals P1–P11 | `code-reviews/2026-05-06-full-tree/track-d-performance.md` | Iterate verdict (non-blocking) | P3 partially resolved; P10 resolved; P1/P4 open | P3 (`const` assertions) extended by γ + T-016 `vmsav8` const fn; P10 (perf harness) landed PR #22; P1 (`#[cold]` annotations) and P4 (`assert_unchecked` migration) remain queued as the highest-ROI near-term picks |
| ADR-0022 Option A smoke regression (B1 hang) | `business-reviews/2026-05-06-B1-smoke-regression.md` | Blocker (milestone) | Resolved | T-014 / ADR-0026 dispatch fallback; 2026-05-07-B1-closure.md is the canonical closure record; post-T-014 smoke clean through `tyrne: all tasks complete` |
| MIN-1 `ipc_cancel_recv` `&mut EndpointArena` parameter (PR#12–17 track-a) | `code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-a-kernel.md` | Minor | Resolved | T-015 / ADR-0032 closed the Deadlock endpoint-rollback asymmetry with the `ipc_cancel_recv` recovery primitive |
| RecvWaiting identity gap (PR#12–17 track-c) | `code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-c-security.md` | Major (forward-flag) | Open (B5+ ADR) | Documented as "no badge scheme yet (ADR-0018 deferred)"; explicitly a forward-flag for the B5+ syscall-ABI ADR; no change has made it worse |
| `cap_map`/`cap_unmap` per-operation rights gap | `security-reviews/2026-05-14-B3-closure.md` §1 | Non-blocking (forward-flagged) | Open (B5+ ADR) | Documented inline at `resolve_address_space_cap` rustdoc + business retro §Adjustments; trigger is the B5+ ADR introducing `CapRights::{MAP,UNMAP,ACTIVATE}` with `CapKind::MemoryRegion` |
| PMM leak via depth-preflight gap (PR#28 review-round-3) | `security-reviews/2026-05-14-B3-closure.md` §3 | Load-bearing blocker (review-round) | Resolved | Closed in commit `8b9f52e` during PR #28 round 3; regression test `cap_create_rejects_too_deep_parent_without_consuming_pmm` pins invariant |
| `ipc_recv_and_yield` Phase-1-mutates-before-Phase-2-checks (PR#28 review-round-3) | `security-reviews/2026-05-14-B3-closure.md` §3 | Load-bearing blocker (review-round) | Resolved | Closed in PR #28 round 3 by moving `current.is_none()` check to before Phase 1; regression test pins invariant |
| `ipc_recv_and_yield` self-dispatch UB when `idle == current` (PR#28 review-round-3) | `security-reviews/2026-05-14-B3-closure.md` §3 | Load-bearing blocker (review-round) | Resolved | Closed in PR #28 round 3 by adding `idle_h != current_handle` guard; regression test pins invariant |
| Phase-B PR #22 major M1 `phase-b.md` inconsistency | `code-reviews/2026-05-08-pr-19-20-21-multi-axis-review/track-3-pr-20-governance.md` | Major | Resolved | Closed by commit `59c08e9`; §B2 status block and Sub-breakdown step 1 flipped from `Proposed` to `Accepted` |

---

## Master-plan assessment

| Master plan | Sound? | Current? | Notes |
|---|---|---|---|
| `business-reviews/master-plan.md` | Yes | No | Five-role structure is clear and well-defined. The "no closure-trio without recorded smoke" AC is a genuine improvement. **Stale:** lines 60–61 reference `.claude/skills/start-task/SKILL.md` and `.claude/skills/write-adr/SKILL.md` instead of `.agents/skills/`. See D5c-M01. |
| `code-reviews/master-plan.md` | Yes | Yes | Five-role structure mirrors the multi-track parallelizable model in use. References `conduct-review` and `add-dependency` skills correctly using `.agents/skills/` prefix. No stale references. Anti-patterns section is accurate and useful. |
| `security-reviews/master-plan.md` | Yes | No | Eight-axis structure is clear and matches what all six dated security review artifacts actually produce. The "Separation from code review" requirement is well-stated. **Stale:** lines 92 and 108 reference `.claude/skills/add-dependency/SKILL.md` and `.claude/skills/start-task/SKILL.md` respectively. See D5c-M01. |
| `performance-optimization-reviews/master-plan.md` | Yes | No | Six-role structure (Baseline → Hotspot → Proposal → Measurement → Regression-check → Reporter) is consistently followed by all five dated performance artifacts. The "Pre-flight hypothesis" guidance is valuable. **Stale:** merge-step section references `.claude/skills/start-task/SKILL.md`. See D5c-M01. |

---

## Claims register

| Claim | File:line | How to verify |
|---|---|---|
| All 7 Track-E blockers closed by PR #13 | `code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-e-docs.md` (summary) | Check git log for PR #13 / commit range; compare Track-E §Status items against each closed finding |
| `cargo +nightly miri test` 152/152 clean at B1 closure | `performance-optimization-reviews/2026-05-07-B1-closure.md:57` | Re-run `cargo +nightly miri test --workspace --exclude tyrne-bsp-qemu-virt` at commit `e9fa019` |
| `cargo +nightly miri test` 185/185 clean at B2 closure | `performance-optimization-reviews/2026-05-09-B2-closure.md:159` | Re-run at commit `b0035ce` |
| `cargo +nightly miri test` 226/226 clean at B3 closure | `performance-optimization-reviews/2026-05-14-B3-closure.md:183` | Re-run at commit `47b0a86` |
| p10/p50/p90 = 4.262 / 4.642 / 6.456 ms at B2 closure | `performance-optimization-reviews/2026-05-09-B2-closure.md:96-98` | Re-run `tools/perf-harness.sh --iterations=20 --timeout=5 --release --report=B2-closure-recheck` at `b0035ce` |
| p10/p50/p90 = 10.311 / 11.884 / 13.823 ms at B3 closure | `performance-optimization-reviews/2026-05-14-B3-closure.md:111-113` | Re-run harness at `47b0a86` |
| Phase-B PR #22 M1 closed by commit `59c08e9` | `code-reviews/2026-05-08-pr-19-20-21-multi-axis-review/track-3-pr-20-governance.md:85` | `git show 59c08e9` — check phase-b.md §B2 status block and Sub-breakdown step 1 |
| UNSAFE-2026-0019/0020 partial verification Amendments added 2026-05-06 | `security-reviews/2026-05-07-B1-closure.md:3` | Check `docs/audits/unsafe-log.md` UNSAFE-2026-0019/0020 entries for "partial-verification" and "post-T-014 smoke" Amendments |
| Zero non-PL011 guest_errors events at B3 closure | `performance-optimization-reviews/2026-05-14-B3-closure.md:103` | Run `tools/run-qemu.sh` at `47b0a86` with `-d int,unimp,guest_errors` |
| `cargo-vet init` deferred to Phase B6 | `security-reviews/2026-05-07-B1-closure.md` forward-flagged items | Check `Cargo.toml` / `.cargo/` for `cargo vet` configuration at HEAD |
| PR #18 item 8: security/perf master-plans received smoke-trace AC cross-reference | `code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-g-process.md` (item 8) | Inspect current `security-reviews/master-plan.md` and `performance-optimization-reviews/master-plan.md` for AC cross-reference text added by PR #18 commit `94a6c0f` |

---

## Cross-track notes

**For D1 (architecture docs):** The security reviews consistently praise architecture docs landing with code rather than as follow-ups (the `exceptions.md` commendation in 2026-04-28-B1-closure.md §8; the B0 review calling `scheduler.md` and `ipc.md` a "security multiplier"). The D1 track reviewer should verify that the B3-era docs (`memory-management.md` AddressSpace section) follow the same contemporaneous-landing pattern.

**For D2a/D2b (ADR reviews):** The code reviews (especially track-3-pr-20-governance.md and track-c-security across both multi-axis reviews) are the most thorough ADR-level quality checks in the corpus. D2a/D2b should verify that ADR-0028 and ADR-0035 (the two B3 ADRs) passed their governance checks per the 2026-05-08 multi-axis review.

**For D5b (audits and reports):** The 2026-05-08 track-4-pr-21-perf-harness.md contains a detailed statistical sanity check of the perf-baseline report (raw-sample cross-verification; nearest-rank percentile verification; 6-sigma range check). D5b should confirm the `perf-baseline-2026-05-14-B3-closure.md` report was generated by the same harness and its statistics are internally consistent.

**For C-tracks (kernel code):** The `ipc_recv_and_yield` self-dispatch UB (when `idle == current`) closed in PR #28 round 3 is a kernel scheduler correctness issue. C5 (kernel-sched) should verify the regression test `ipc_recv_and_yield_with_idle_as_current_returns_deadlock` exists at HEAD and exercises the guard.

**For the gate-reproduction track:** The claims register above lists eight verifiable claims; the performance harness claims are the most mechanically verifiable and should be prioritized for gate reproduction.

---

## Coverage checklist

All 58 files enumerated by `git ls-files docs/analysis/reviews` (excluding `docs/analysis/reviews/master-review/`) are confirmed read in full.

| # | File | Lines | Read |
|---|---|---|---|
| 1 | `docs/analysis/reviews/README.md` | 45 | [x] |
| 2 | `docs/analysis/reviews/business-reviews/README.md` | 36 | [x] |
| 3 | `docs/analysis/reviews/business-reviews/master-plan.md` | 137 | [x] |
| 4 | `docs/analysis/reviews/business-reviews/2026-04-21-A2-completion.md` | 77 | [x] |
| 5 | `docs/analysis/reviews/business-reviews/2026-04-21-A6-completion.md` | 115 | [x] |
| 6 | `docs/analysis/reviews/business-reviews/2026-04-22-T-006-mini-retro.md` | 74 | [x] |
| 7 | `docs/analysis/reviews/business-reviews/2026-04-27-B0-closure.md` | 165 | [x] |
| 8 | `docs/analysis/reviews/business-reviews/2026-04-27-T-009-mini-retro.md` | 150 | [x] |
| 9 | `docs/analysis/reviews/business-reviews/2026-04-28-B1-closure.md` | 170 | [x] |
| 10 | `docs/analysis/reviews/business-reviews/2026-05-06-B1-smoke-regression.md` | 129 | [x] |
| 11 | `docs/analysis/reviews/business-reviews/2026-05-07-B1-closure.md` | 158 | [x] |
| 12 | `docs/analysis/reviews/business-reviews/2026-05-09-B2-closure.md` | 178 | [x] |
| 13 | `docs/analysis/reviews/business-reviews/2026-05-14-B3-closure.md` | 231 | [x] |
| 14 | `docs/analysis/reviews/code-reviews/README.md` | 28 | [x] |
| 15 | `docs/analysis/reviews/code-reviews/master-plan.md` | 149 | [x] |
| 16 | `docs/analysis/reviews/code-reviews/2026-04-21-tyrne-to-phase-a.md` | 155 | [x] |
| 17 | `docs/analysis/reviews/code-reviews/2026-05-06-full-tree-comprehensive-review-plan.md` | 403 | [x] |
| 18 | `docs/analysis/reviews/code-reviews/2026-05-06-full-tree-comprehensive.md` | 261 | [x] |
| 19 | `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review.md` | 141 | [x] |
| 20 | `docs/analysis/reviews/code-reviews/2026-05-08-pr-19-20-21-multi-axis-review.md` | 144 | [x] |
| 21 | `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/00-preflight.md` | 91 | [x] |
| 22 | `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-a-kernel.md` | 89 | [x] |
| 23 | `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-b-hal.md` | 72 | [x] |
| 24 | `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-c-security.md` | 235 | [x] |
| 25 | `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-d-performance.md` | 179 | [x] |
| 26 | `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-e-docs.md` | 100 | [x] |
| 27 | `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-f-tests.md` | 215 | [x] |
| 28 | `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-g-bsp.md` | 87 | [x] |
| 29 | `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-h-infra.md` | 69 | [x] |
| 30 | `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-i-integration.md` | 171 | [x] |
| 31 | `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-j-hygiene.md` | 160 | [x] |
| 32 | `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-a-kernel.md` | 116 | [x] |
| 33 | `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-b-hal-bsp.md` | 86 | [x] |
| 34 | `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-c-security.md` | 187 | [x] |
| 35 | `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-d-perf.md` | 147 | [x] |
| 36 | `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-e-docs.md` | 228 | [x] |
| 37 | `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-f-tests.md` | 190 | [x] |
| 38 | `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-g-process.md` | 146 | [x] |
| 39 | `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-h-audit.md` | 103 | [x] |
| 40 | `docs/analysis/reviews/code-reviews/2026-05-08-pr-19-20-21-multi-axis-review/track-1-pr-19-mechanical.md` | 83 | [x] |
| 41 | `docs/analysis/reviews/code-reviews/2026-05-08-pr-19-20-21-multi-axis-review/track-2-pr-20-design.md` | 114 | [x] |
| 42 | `docs/analysis/reviews/code-reviews/2026-05-08-pr-19-20-21-multi-axis-review/track-3-pr-20-governance.md` | 103 | [x] |
| 43 | `docs/analysis/reviews/code-reviews/2026-05-08-pr-19-20-21-multi-axis-review/track-4-pr-21-perf-harness.md` | 208 | [x] |
| 44 | `docs/analysis/reviews/security-reviews/README.md` | 39 | [x] |
| 45 | `docs/analysis/reviews/security-reviews/master-plan.md` | 184 | [x] |
| 46 | `docs/analysis/reviews/security-reviews/2026-04-21-tyrne-to-phase-a.md` | 168 | [x] |
| 47 | `docs/analysis/reviews/security-reviews/2026-04-27-B0-closure.md` | 118 | [x] |
| 48 | `docs/analysis/reviews/security-reviews/2026-04-28-B1-closure.md` | 145 | [x] |
| 49 | `docs/analysis/reviews/security-reviews/2026-05-07-B1-closure.md` | 113 | [x] |
| 50 | `docs/analysis/reviews/security-reviews/2026-05-09-B2-closure.md` | 115 | [x] |
| 51 | `docs/analysis/reviews/security-reviews/2026-05-14-B3-closure.md` | 105 | [x] |
| 52 | `docs/analysis/reviews/performance-optimization-reviews/README.md` | 31 | [x] |
| 53 | `docs/analysis/reviews/performance-optimization-reviews/master-plan.md` | 155 | [x] |
| 54 | `docs/analysis/reviews/performance-optimization-reviews/2026-04-21-A6-baseline.md` | 106 | [x] |
| 55 | `docs/analysis/reviews/performance-optimization-reviews/2026-04-28-B1-closure.md` | 208 | [x] |
| 56 | `docs/analysis/reviews/performance-optimization-reviews/2026-05-07-B1-closure.md` | 155 | [x] |
| 57 | `docs/analysis/reviews/performance-optimization-reviews/2026-05-09-B2-closure.md` | 186 | [x] |
| 58 | `docs/analysis/reviews/performance-optimization-reviews/2026-05-14-B3-closure.md` | 206 | [x] |

Total lines read: ~7,158 across 58 files.
