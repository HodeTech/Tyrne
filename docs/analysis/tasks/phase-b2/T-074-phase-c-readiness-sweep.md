# T-074 — Run the Phase C readiness sweep

- **Phase:** B.2
- **Milestone:** Track B.2 readiness (Polish items; prepares Phase C, not exit-gating on its own)
- **Status:** Draft
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-033](T-033-qemu-tooling-smp-and-timeout.md), [T-034](T-034-ci-qemu-smoke-job.md), [T-047](T-047-roadmap-state-and-phase-index-sync.md), [T-054](T-054-adr-ledger-renumbering-cascade.md)
- **Informs:** [T-075](T-075-phase-b2-closure.md)
- **ADRs required:** none (a successor ADR or rider only if the single-core-marker decision below needs one)

---

## User story

As the maintainer about to open Phase C, I want every SMP-readiness item scattered across the roadmap folded into one index and into the C1–C5 milestone plans, so that Phase C starts on the day Phase B.2 closes without rediscovering its entry gates.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), which allows Phase C *planning* while B.2 is open but forbids opening Phase C milestones or leaving `Draft` on Phase C tasks. The Polish list in [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) asks for a consolidated Phase C readiness index and a cross-reference table "before Phase C tasks are scoped", and for the single-core assumption to become one greppable marker. Separately, [`phase-c.md`](../../../roadmap/phases/phase-c.md) §"Review-derived work items" records items that none of the milestone bodies C1–C5 mentions yet: cross-core `Pmm` serialization as a boot-order gate on `CPU_ON` (C1/C2), the `ipc_send` `unreachable!()` (C3), the `user_access.rs` interleaving invariant, cross-core panic propagation (C4), and the two SMP-critical entry gates (`StaticCell`'s blanket `Sync`, the non-atomic PMM bitmap) which remain **Phase C** work and are not fixed in B.2. The task runs late in B.2 so it can use the final ADR numbers ([T-054](T-054-adr-ledger-renumbering-cascade.md)), the carry-forwards added by [T-047](T-047-roadmap-state-and-phase-index-sync.md), and the working smoke job and `--smp N` tooling ([T-034](T-034-ci-qemu-smoke-job.md), [T-033](T-033-qemu-tooling-smp-and-timeout.md)).

## Acceptance criteria

- [ ] `phase-c.md` gains one readiness index (a table: item → origin → milestone it gates → owner task/ADR → state) that lists the two entry gates, the review-derived items of its §§1–4, the Phase B carry-forwards (object-lifecycle ADR, ADR-0034, K3-4, the three seam-review flags added by T-047) and the B.2 outputs Phase C depends on (smoke job, `--smp N`, `without_interrupts` prerequisites).
- [ ] Each review-derived item is folded into the milestone C1–C5 sub-breakdown or acceptance criteria that it gates, with the wording of the original item preserved by link, not duplicated; in particular C1 names the cross-core `Pmm` serialization as a boot-order gate on `CPU_ON`, and C4 names cross-core panic propagation.
- [ ] Every item is classified **stays in Phase C** or **pulled forward into a Phase B.2 task**. For any pulled-forward item (for example the `ipc_send` `unreachable!()` that `phase-c.md` calls "cheap to defuse now") a new `T-NNN` is opened under `docs/analysis/tasks/phase-b2/` with the next free number and added to the [task index](README.md) in the same change.
- [ ] The Phase C ADR ledger uses the numbers/identifiers produced by T-054, and each of C1–C5's ADRs is mapped to its milestone once.
- [ ] **Decisions recorded** in this task's review history: (a) whether the "single-core v1" assumption becomes one greppable marker (constant or `cfg` feature) referenced by the roughly 13 subsystems that rely on it, and (b) whether a second whole-tree master review is run at the B→C boundary (run now, or explicitly skipped with the reason). If (a) is "yes" the marker is added or a Phase C task is opened for it.
- [ ] A Phase-C-opening baseline is recorded (host tests, Miri, coverage, smoke trace with `--smp 1`), giving the before/after line the Polish item asks for.
- [ ] Verification: every link in the touched files resolves; `git diff --stat` shows only roadmap/task files unless a pulled-forward task is implemented separately.

## Out of scope

- Fixing `StaticCell` or making the PMM bitmap atomic or serialised — these are Phase C Milestone C1/C2 entry gates.
- Opening Phase C milestones or moving any Phase C task past `Draft` (forbidden while B.2 is open by ADR-0040).
- Writing the Phase C ADRs.

## Approach

Read `phase-c.md` §§1–4 and "Polish & excellence (SMP prep)" in full, then build the index table first and fold each row into the milestone text, linking back to the original item. Keep the reasoning for each classification in one line. Run the sweep after the code tasks of Tracks B.2-1 and B.2-3 have landed so the baseline reflects the post-B.2 tree.

## Definition of done

- [ ] Every relative link in each touched file resolves.
- [ ] Any new task file follows [`TEMPLATE.md`](../TEMPLATE.md) and the [`start-task`](../../../../.agents/skills/start-task/SKILL.md) rules and is indexed.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) (scope `roadmap`).
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decisions:** single-core marker (criterion 5a); second master review (criterion 5b).
- The Polish items this task consumes are in `phase-b2.md` §"Polish & excellence opportunities" (Documentation: "Consolidate the scattered Phase-C readiness backlog"; "Add a Phase-C readiness sweep cross-reference table"; Cross-cut concurrency/SMP: the `TYRNE_SINGLE_CORE_V1` marker; Documentation: "Run a second whole-tree master review at the Phase B → Phase C boundary").
- Status is `Draft` because the classification of pulled-forward items depends on how far the code tasks have progressed when the sweep runs.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Draft |
