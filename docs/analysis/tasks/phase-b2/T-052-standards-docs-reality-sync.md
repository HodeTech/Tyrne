# T-052 — Reconcile standards claims with CI and lint reality (decisions required)

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-032](T-032-panic-family-denies-hal-bsp.md)
- **Informs:** none
- **ADRs required:** none at opening (a decision that changes a standard's rule follows the `propose-standard-change` skill and may add one)

---

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

- [ ] Test naming (`testing.md:62-77`): decision recorded. If the in-use convention is documented, the pattern and its three examples are changed to the unprefixed `<subject>_<condition>_<expected_outcome>` form, with examples that are real test names found by `grep -rn "fn <name>" kernel hal test-hal`; if the rename-plus-lint option is chosen, the follow-up task is named and the section says the prefix is not yet adopted.
- [ ] Panic handler (`error-handling.md:73`): decision recorded. Either the sentence is softened to what `bsp-qemu-virt/src/main.rs:1666-1700` does today (banner, `PanicInfo` message and location, halt) with the register dump named as a tracked follow-up, or the follow-up task to implement the dump (x0-x30, SP, ELR_EL1, ESR_EL1, FAR_EL1) is opened and the sentence is annotated until it lands.
- [ ] `unimplemented!()` (`error-handling.md:139`; related `code-style.md:116`): decision recorded. Either `unimplemented = "deny"` is added to `[workspace.lints.clippy]` in `Cargo.toml` as a recorded code change (and the sentence stays), or the sentence is narrowed to "`todo!()` presence is denied by the `clippy::todo` workspace lint; `unimplemented!()` has no automated CI check today and relies on review". Verified against `Cargo.toml` and `.github/workflows/ci.yml`.
- [ ] Logging facade (`logging-and-observability.md`): a status banner at the top states that the standard is forward-looking, that the `tyrne-log` crate and log-service architecture do not exist yet, and that the kernel currently emits diagnostics only through the raw `Console`/UART path; the present-tense sentence at line 52 ("The project provides a logging facade") is aligned with it; verified against the `Cargo.toml` workspace members.
- [ ] Deny-lint uniformity (`error-handling.md:3` and `:60`, `code-style.md:129`): after T-032 has landed, the three statements name exactly the crates that carry the panic-family denies (verified with `grep -n "deny(clippy" kernel/src/lib.rs hal/src/lib.rs bsp-qemu-virt/src/main.rs`), and the "userspace services uniformly" scope claim is narrowed or footnoted for crates without them (`test-hal`, `userland/*` carry only the workspace-level lints).
- [ ] Downstream-effects search recorded (`propose-standard-change` step 7): `.agents/skills/`, architecture documents, and other standards are searched for restatements of the five changed claims, and each hit is updated or listed in the review history.

## Out of scope

- The mechanical standards corrections (`panic = "abort"` location, "(planned)" CI wording, commit scopes, lint-list additions, tagged fences, grammar): [T-053](T-053-standards-docs-mechanical-fixes.md).
- Adding the panic-family denies to `tyrne-hal` and `bsp-qemu-virt`: [T-032](T-032-panic-family-denies-hal-bsp.md).
- Implementing the register dump, the mass test rename, or a naming lint; those are follow-up tasks if chosen.
- Enforcement-status tags on volatile claims across standards (a Polish item owned by T-053).
- Writing the `tyrne-log` facade.

## Approach

For each of the five items pick the option the plan item offers, write the decision into the review history, then make the minimal edit.
Because this task is documentation-only, an option that needs code (the register dump, the mass test rename plus lint) is recorded here and opened as a named follow-up task, while the standard is annotated as a tracked gap until it lands.
The one code option that costs a single line is `unimplemented = "deny"`; if it is chosen, the `Cargo.toml` edit lands here and `cargo host-clippy` and `cargo kernel-clippy` must stay clean.
For the uniformity item, wait for T-032 (the declared dependency) and then describe what the tree really enforces.

## Definition of done

Doc-only variant:

- [ ] Every relative link (`](…)` target) in each touched file resolves to an existing path or heading.
- [ ] `git diff --stat` lists only: `docs/standards/{testing,error-handling,code-style,logging-and-observability}.md`, any ADR or follow-up task file created by a decision, `Cargo.toml` only if `unimplemented = "deny"` was chosen (then `cargo host-clippy` and `cargo kernel-clippy` are clean), `docs/roadmap/current.md`, and this task file.
- [ ] Text is English; fences are tagged ([`documentation-style.md`](../../../standards/documentation-style.md)).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040` (plus any ADR a rule change adds).
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

**Open decisions (maintainer, one per item above).**
(1) Test naming: document the unprefixed convention vs rename 345 tests and add a lint. (2) Register dump: soften the claim vs implement the dump. (3) `unimplemented!()`: deny it workspace-wide vs narrow the sentence. (4) None needed for the logging banner. (5) Uniformity: resolved by T-032 landing plus accurate wording, unless the maintainer wants `test-hal` and the userland crates covered too.

**Location re-verification (2026-10-11, against the current tree).**
All plan-item locations reproduce: `testing.md:62-77`, `error-handling.md:3,73,139`, `logging-and-observability.md:50-60`, `code-style.md:129`.
Two details the plan item does not state: `error-handling.md:60` and `code-style.md:129` already say "kernel crates" / "kernel paths", so the over-claim is in the scope sentence at `error-handling.md:3` and in the unqualified "uniformly" reading, not in those two lines' literal wording; and `code-style.md:116` repeats the `unimplemented!()` rule without an enforcement claim.
The test count is approximate (365 `#[test]` attributes by `grep`; 345 by a scratch scan that pairs each attribute with the next `fn`); the 366-test `cargo host-test` total also counts doc-tests and omits release-only tests, so re-run a count rather than quoting a number.

**Sequencing.** [T-053](T-053-standards-docs-mechanical-fixes.md) tags the fence at `testing.md:67` that item (1) may rewrite, and also edits `error-handling.md`; whichever lands second rebases (no hard dependency).

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
