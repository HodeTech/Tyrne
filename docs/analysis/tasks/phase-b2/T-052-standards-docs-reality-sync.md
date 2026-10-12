# T-052 — Reconcile standards claims with CI and lint reality (decisions required)

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-032](T-032-panic-family-denies-hal-bsp.md)
- **Informs:** [T-056](T-056-docs-consistency-automation.md)
- **ADRs required:** [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md) (Accepted 2026-10-12; reviewed execution and corpus policy); [ADR-0042](../../../decisions/0042-descriptive-test-names.md) (Accepted; supersedes ADR-0041 before the naming edit)

---

> **Approved contract reconciliation (2026-10-12).** The maintainer approved the [preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and ADR package. The criteria below are the executable contract; dated opening observations remain historical. This preparation records no task delivery. Each implementation step includes verification and two fresh independent review rounds under [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); new task states stop at `In Review`.

## User story

As a contributor who relies on the standards to know what the project enforces, I want five standards claims that disagree with the code to be either made true or corrected, so that the standards stop promising a naming convention, a register dump, CI checks, a logging facade, and uniform deny-lints that do not exist.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), covering the five "decision required" items in the "Standards docs" group of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-2.
Each item is a place where a standard states something the tree does not do, and each has two honest fixes, "make the code match" or "make the standard match", which is a maintainer decision rather than a typo correction.
The five claims, re-verified on 2026-10-11: `testing.md:62-77` mandates `test_<subject>_<condition>_<expected_outcome>` but none of the roughly 365 `#[test]` functions in kernel, hal, test-hal, bsp, and userland (`grep -rn '#\[test\]'` count at opening) carries the `test_` prefix; `error-handling.md:73` says the development panic handler "dumps register state" but `bsp-qemu-virt/src/main.rs:1666-1700` prints a banner and the `PanicInfo`, then spins; `error-handling.md:139` says CI flags `todo!()` and `unimplemented!()` but only `todo = "deny"` exists in `Cargo.toml` `[workspace.lints.clippy]`; `logging-and-observability.md:50-60` describes the `tyrne-log` facade in present tense, and no such crate is a workspace member; `error-handling.md:3` and `code-style.md:129` imply uniform coverage by the `clippy::panic`/`unwrap_used`/`expect_used` denies, which exist only in `kernel/src/lib.rs:62-64`.
This task depends on [T-032](T-032-panic-family-denies-hal-bsp.md), which adds the panic-family denies to `tyrne-hal` and `bsp-qemu-virt`, so the uniformity claim is judged against the post-T-032 tree.
The purely mechanical standards fixes are [T-053](T-053-standards-docs-mechanical-fixes.md).

## Acceptance criteria

Every decision below is recorded in this task's review history with its classification (claim correction, or rule change). A rule change follows [`propose-standard-change`](../../../../.agents/skills/propose-standard-change/SKILL.md) (ADR accepted before the standard changes). This task is documentation-only: where the chosen option is "make the code match", the code work is opened as a named follow-up task and the standard is annotated as a tracked gap until it lands.

- [ ] Test naming: apply Accepted ADR-0042 after ADR-0041's atomic supersession. Document descriptive unprefixed `<subject>_<condition>_<expected_outcome>` guidance, ordinary snake_case and concise unambiguous names without mechanically fixed word counts; use the three actual IPC test identifiers from ADR-0042. Add testing.md's References link to ADR-0042, verify it and record the downstream-effects search. No naming lint or mass rename.
- [ ] Panic handler: correct the claim to the current banner, PanicInfo message/location and spin/halt behavior. Distinguish saved exception diagnostics from generic panic-time register dumps. The maintainer approved removing the automatic register-dump follow-up obligation; no dump feature or new task is required by this correction.
- [ ] `unimplemented!()`: state that `todo!()` is denied by the workspace clippy::todo lint, while unimplemented! has no automated deny today and relies on review. Preserve intentional host stubs; no Cargo/lint-level change. Verify Cargo.toml and required workspace Clippy coverage.
- [ ] Logging facade (`logging-and-observability.md`): a status banner at the top states that the standard is forward-looking, that the `tyrne-log` crate and log-service architecture do not exist yet, and that the kernel currently emits diagnostics only through the raw `Console`/UART path; the present-tense sentence at line 52 ("The project provides a logging facade") is aligned with it; verified against the `Cargo.toml` workspace members.
- [ ] Deny-lint uniformity (`error-handling.md:3` and `:60`, `code-style.md:129`): after T-032 has landed, the three statements name exactly the crates that carry the panic-family denies (verified with `grep -n "deny(clippy" kernel/src/lib.rs hal/src/lib.rs bsp-qemu-virt/src/main.rs`), and the "userspace services uniformly" scope claim is narrowed or footnoted for crates without them (`test-hal`, `userland/*` carry only the workspace-level lints).
- [ ] Downstream-effects search recorded (`propose-standard-change` step 7): `.agents/skills/`, architecture documents, and other standards are searched for restatements of the five changed claims, and each hit is updated or listed in the review history.

- [ ] Review adjacent error-handling claims so planned TaskFault delivery, supervision and reclamation are explicitly future work rather than current fault isolation.

## Out of scope

- The mechanical standards corrections (`panic = "abort"` location, "(planned)" CI wording, commit scopes, lint-list additions, tagged fences, grammar): [T-053](T-053-standards-docs-mechanical-fixes.md).
- Adding the panic-family denies to `tyrne-hal` and `bsp-qemu-virt`: [T-032](T-032-panic-family-denies-hal-bsp.md).
- Implementing a register dump, mass test rename or naming lint; none is selected and no automatic follow-up task is required.
- Enforcement-status tags on volatile claims across standards (a Polish item owned by T-053).
- Writing the `tyrne-log` facade.

## Approach

Record naming as the Accepted ADR-0042 rule change and the other four choices as source-backed claim corrections.
Apply the approved unprefixed guidance and motivating References entry, current panic behavior, review-only unimplemented! boundary, planned logging/fault-supervision status and exact kernel/HAL/BSP deny scope with explicit scoped allowances.
Do not change lint levels, add a register-dump task or promise unimplemented runtime features.
T-032 is already Done; verify its actual source and search standards, architecture and skills for every restatement, updating it or recording the scoped disposition.

## Definition of done

Doc-only variant:

- [ ] Every relative link (`](…)` target) in each touched file resolves to an existing path or heading.
- [ ] `git diff --stat` lists only: `docs/standards/{testing,error-handling,code-style,logging-and-observability}.md`, downstream documents demonstrably restating these same claims (with recorded dispositions), `docs/roadmap/current.md`, and this task file.
- [ ] Text is English; fences are tagged ([`documentation-style.md`](../../../standards/documentation-style.md)).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040` (plus any ADR a rule change adds).
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

**Step-scoped evidence allowance.** In addition to the named content files, the step may update this task, `docs/roadmap/current.md`, the B.2 task/track indexes, governing decision references, source-bound reports/raw evidence, canonical review artifacts and their indexes where necessary. Verify this allowance against the step commit range, not the full stacked branch. Record a demonstrated existing-scope reason for any further file.

## Design notes

**Resolved 2026-10-12.** Naming follows Accepted ADR-0042; panic prose matches current behavior without an automatic dump follow-up; unimplemented! remains review-enforced; logging/fault supervision remain planned; deny scope names actual crates/allowances. No runtime or lint-level change is selected.

**Location re-verification (2026-10-11, against the current tree).**
All plan-item locations reproduce: `testing.md:62-77`, `error-handling.md:3,73,139`, `logging-and-observability.md:50-60`, `code-style.md:129`.
Two details the plan item does not state: `error-handling.md:60` and `code-style.md:129` already say "kernel crates" / "kernel paths", so the over-claim is in the scope sentence at `error-handling.md:3` and in the unqualified "uniformly" reading, not in those two lines' literal wording; and `code-style.md:116` repeats the `unimplemented!()` rule without an enforcement claim.
The test count is approximate (365 `#[test]` attributes by `grep`; 345 by a scratch scan that pairs each attribute with the next `fn`); the 366-test `cargo host-test` total also counts doc-tests and omits release-only tests, so re-run a count rather than quoting a number.

**Sequencing.** [T-053](T-053-standards-docs-mechanical-fixes.md) tags the fence at `testing.md:67` that item (1) may rewrite, and also edits `error-handling.md`; whichever lands second rebases (no hard dependency).

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-12 | Codex (AI agent), maintainer-approved reconciliation | Old: naming alternatives without explicit motivating reference, automatic register-dump follow-up and a one-line unimplemented deny option. Approved replacement: Accepted ADR-0042 guidance plus testing References/downstream search; current panic behavior without automatic follow-up; review-only unimplemented and actual deny/logging/fault scope, with no lint/runtime change. See [approved preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); preparation only, status unchanged. |
| 2026-10-12 | Codex (AI agent), coordinator cross-reference check | ROOT-01: added the T-056 Informs backlink to match its newly explicit prerequisite/surface reference, following start-task step 9; no dependency scope or task state changed. |
