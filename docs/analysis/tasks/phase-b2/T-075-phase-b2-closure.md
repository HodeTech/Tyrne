# T-075 — Close Phase B.2

- **Phase:** B.2
- **Milestone:** B.2 closure
- **Status:** Draft
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** every Phase B.2 task except the two optional polish tasks — [T-030](T-030-ci-release-profile-gate.md) to [T-035](T-035-ci-hygiene-tail.md), [T-037](T-037-userland-bare-metal-cfg-gate.md) to [T-055](T-055-adr-append-only-corrections.md), [T-057](T-057-typed-addresses-phys-virt.md) to [T-074](T-074-phase-c-readiness-sweep.md), and every task numbered T-076 or later opened in `docs/analysis/tasks/phase-b2/` (for example items pulled forward by T-074, which adds each one to this list when it opens it); [T-036](T-036-ci-arm64-host-check-job.md) and [T-056](T-056-docs-consistency-automation.md) are optional and, if still open, become recorded carry-forwards
- **Informs:** Phase C (opens when this task is `Done`)
- **ADRs required:** [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) (a closing revision note is appended)

---

## User story

As the maintainer, I want Phase B.2 closed with evidence — every finding accounted for, the full gate matrix green on the final tree, and the roadmap pointers restored — so that Phase C opens on a base whose gates are real and whose documents can be trusted.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), which defines the B.2 exit bar as the acceptance criteria of Tracks B.2-1…B.2-6 and requires a closure that goes beyond the usual ADR-0013 business review: a verification report covering all 141 items (the source review of 2026-07-15 was static analysis; nothing in it was compiled or run), a security review of the phase's `unsafe`/asm/capability changes, and a regression check. The Phase B closure quartet ([retrospective](../../reviews/business-reviews/2026-06-01-phase-b-closure.md), consolidated security review, performance baseline, guide) is the precedent. The 2026-10-11 baseline the final matrix is compared with: 366 host tests (46 hal, 259 kernel, 58 test-hal, 3 doc), `hello.bin` 117 bytes, smoke boot-to-end ≈ 4.7 ms with exactly 2 SVC exceptions, llvm-cov 96.31 % lines, Miri 0 UB on kernel/hal/test-hal, 33 unsafe-log entries (32 Active, 1 Removed).

## Acceptance criteria

- [ ] A **verification report** (under `docs/analysis/reports/`) accounts for all 141 plan items: each is *fixed* (task and merge PR), *not reproduced* (evidence), or *deferred* (reason and trigger); the totals reconcile with the Track tables in [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) (12 / 58 / 16 / 32 / 21 / 2).
- [ ] The **full gate matrix** is run on the final tree and recorded verbatim: `cargo fmt --all -- --check`, `cargo host-clippy`, `cargo kernel-clippy`, userland clippy, `cargo host-test`, `cargo +stable test`, `cargo test --release`, **`cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` on an arm64 host**, `tools/build-userland.sh`, `cargo kernel-build` (debug and release), `tools/smoke.sh --int`, `cargo llvm-cov`; each compared with the baseline in Context, with any difference explained.
- [ ] A **consolidated security review** of Phase B.2's security-relevant changes (at least the `x2` shim fix, `console_write` bounding, `MapperFlush` discriminant, copy-user hardening and de-duplication, the `CapabilityTable`/resolve refactors, trap-frame `offset_of!` pins, the `alloc_frame` contract, the `debug-console` gate if landed, and the BSP context extraction) is filed under `docs/analysis/reviews/security-reviews/` using the [`perform-security-review`](../../../../.agents/skills/perform-security-review/SKILL.md) skill, with a verdict.
- [ ] A **performance regression check** compares the SVC/`console_write` path and boot-to-end with the pre-B.2 baseline using `tools/perf-harness.sh` and the same-host control ([master plan](../../reviews/performance-optimization-reviews/master-plan.md)).
- [ ] A **business review / retrospective** is filed under `docs/analysis/reviews/business-reviews/` following the [business master plan](../../reviews/business-reviews/master-plan.md), including what was learned about the plan-outruns-execution pattern and whether the ADR-0040 scope checkpoint was used; the closure-batch index sweep is done (all four review-family README indices list the new artefacts).
- [ ] The unsafe log is consistent: audit tags in code and log cross-checked in both directions with **zero orphans**, entry/amendment counts recorded against the 33 / 49 baseline.
- [ ] Roadmap pointers are restored: `current.md` names Phase C as the active phase and B.2 as the last closed phase; `phases/README.md`, `phase-b2.md` (status Closed), `phase-c.md` (status banner removed), `README.md` and `CLAUDE.md` status sentences are updated; ADR-0040 gets an append-only closing revision note; unfinished polish tasks are listed as carry-forwards.
- [ ] Every task in `docs/analysis/tasks/phase-b2/` — including any opened after 2026-10-11 — is `Done` or recorded as a carry-forward; comparing `ls docs/analysis/tasks/phase-b2/T-*.md` with the index and with this task's Dependencies shows no open task outside that set.
- [ ] Verification: every relative link in the touched files resolves; the closure review documents `Done` only after the verbatim smoke trace and a clean fault count, per the business master plan's acceptance rule.

## Out of scope

- Opening Phase C milestones or tasks (that follows this task; the groundwork is [T-074](T-074-phase-c-readiness-sweep.md)).
- Any new code change other than fixes the regression check forces.

## Approach

Run the closure only after all dependencies are `Done` (or recorded as carry-forwards). Build the verification report incrementally from each task's review history — the per-task "re-verified against the live tree" notes required by ADR-0040 rule 5 are its source. Use the [`conduct-review`](../../../../.agents/skills/conduct-review/SKILL.md) skill for the business, security and performance artefacts so they land in the right folders with the right shape.

## Definition of done

- [ ] All criteria above checked; the verification report totals match the track tables.
- [ ] Commit messages follow [`commit-style.md`](../../../standards/commit-style.md) (scopes `roadmap`, `analysis`).
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated; the maintainer authorises `Done`.

## Design notes

- The two optional tasks may close as carry-forwards: T-036 (arm64 host check) and T-056 (docs-consistency automation). Recording them is mandatory; completing them is not.
- Tasks that end in an explicit decision (T-035, T-039, T-040, T-065, T-067, T-073) count as complete when the decision is recorded, as ADR-0040 rule 3 states.
- Status is `Draft` until the dependency set stabilises; promote to `Ready` when the last implementation task is `In Review`.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Draft |
