# T-051 — Update CONTRIBUTING.md and SECURITY.md to the post-Phase-B state

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** none
- **ADRs required:** [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md) (Accepted 2026-10-12; reviewed execution and corpus policy)

---

> **Approved contract reconciliation (2026-10-12).** The maintainer approved the [preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and ADR package. The criteria below are the executable contract; dated opening observations remain historical. This preparation records no task delivery. Each implementation step includes verification and two fresh independent review rounds under [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); new task states stop at `In Review`.

## User story

As an external reader deciding whether to contribute or report a vulnerability, I want CONTRIBUTING.md and SECURITY.md to describe the project and its security boundary as they are after Phase B, so that I am not told the system has no userspace when it already runs untrusted EL0 code.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), covering the single HIGH item of the "Standards docs" group in [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-2.
`CONTRIBUTING.md:3` says Tyrne is "mid-way through Phase B" and "runs a two-task IPC demo", and `CONTRIBUTING.md:14` says "Phase A and milestones B0–B3 closed; B4 active".
`SECURITY.md:7` says the same thing in security terms: "Phase A and milestones B0–B3 closed; B4 active", "it is not yet a userspace-bearing OS", and a threat model "refined as Phase B progresses".
All three are out of date: Phase B closed on 2026-06-01, and the kernel runs a real EL0 task (`userland/hello`) that crosses the capability-gated syscall boundary.
Of the Track B.2-2 items this is the only one that is a false statement about the shipped security boundary, because SECURITY.md exists to describe the syscall and capability surface accurately; it is small and should land early.
The ADR-0040 kickoff already updated the README "Status at a glance" and the CLAUDE.md project-state paragraph, and those are the wording sources; no other document is in scope.

## Acceptance criteria

- [ ] `CONTRIBUTING.md:3` is rewritten to the current state (Phase B closed 2026-06-01, first EL0 userspace task running through the capability-gated syscall boundary, Phase B.2 active, Phase C next and gated by B.2), consistent with the README "Status at a glance"; `grep -n "mid-way through Phase B\|two-task IPC demo" CONTRIBUTING.md` returns nothing.
- [ ] `CONTRIBUTING.md:14` no longer says "milestones B0–B3 closed; B4 active"; the boundary for unsolicited pull requests is restated against the active phase and points to [`current.md`](../../../roadmap/current.md) as the source of truth instead of repeating milestone IDs; `grep -n "B4 active" CONTRIBUTING.md` returns nothing.
- [ ] `SECURITY.md:7` (Project status and guarantees): "not yet a userspace-bearing OS", "B4 active", and "refined as Phase B progresses" are removed; the pre-alpha, no-production-use, and no-security-guarantees statements are kept; the link to `docs/architecture/security-model.md` still resolves.
- [ ] `SECURITY.md` states precisely what is reachable from EL0 today, verified against `kernel/src/syscall/abi.rs` (`SyscallNumber`, lines 50-62, and its `decode`) and ADR-0030 / ADR-0031: the five-syscall v1 set (`ipc_send`, `ipc_recv`, `task_yield`, `task_exit`, `console_write`), that `console_write` is both capability-gated and debug-build-only (in a non-debug build `SyscallNumber::decode` returns `None` for number 5, and the dispatcher maps that `None` to `BadSyscallNumber`, `kernel/src/syscall/dispatch.rs` line 133), and that EL0 has no capability-management, notification, or address-space syscalls in v1.
- [ ] Any statement about when the withheld syscalls will be wired cites the document that says so (ADR-0031 "Negative" consequences, or the Phase E plan), not a date or phase invented here; `grep -n "Phase E" SECURITY.md` is either empty or each hit is backed by a cited roadmap line.

- [ ] CONTRIBUTING.md replaces the stale future-implementation section with the current workflow and existing CI guidance. SECURITY.md states the present limits: the BSP embeds a trusted image; non-SVC EL0 synchronous faults panic the whole kernel; task exit stops scheduling without resource reclamation; kernel APIs exceed the EL0 syscall surface. Verify against dispatcher, vectors, scheduler and loader; complete distinct code/document and security review roles in both rounds, then retain maintainer SECURITY wording review before merge.

## Out of scope

- The README status sentences, the CLAUDE.md project-state paragraph, and `docs/roadmap/*`: already updated by the ADR-0040 kickoff or owned by [T-047](T-047-roadmap-state-and-phase-index-sync.md).
- The rest of the README and the glossary: [T-050](T-050-entry-docs-and-glossary-sync.md).
- Any change to the disclosure process, the reporting channel, or the "fix first, disclose later" policy in SECURITY.md.
- Contribution-policy redesign; updating the stale future-implementation section to the current workflow and existing CI guide is in scope.
- Any code or CI change; the debug-console gating itself is [T-065](T-065-debug-console-feature-flag.md).

## Approach

Take the wording from the README "Status at a glance" and the CLAUDE.md project-state paragraph as they stand after the kickoff, and keep the paragraphs short enough that they do not need editing at every milestone: state the phase-level facts and defer to `current.md` for anything finer.
For SECURITY.md, read `kernel/src/syscall/abi.rs` and the two ADRs first and write the reachable-surface description from them, not from the previous paragraph or from the README; the syscall numbers and the debug gate are the load-bearing facts, and the debug-build gate currently rides on `debug_assertions` (see Design notes).
Keep the language factual and free of marketing adjectives, per the documentation style.

## Definition of done

Doc-only variant:

- [ ] Every relative link (`](…)` target) in each touched file resolves to an existing path or heading.
- [ ] `git diff --stat` lists only: `CONTRIBUTING.md`, `SECURITY.md`, `docs/roadmap/current.md`, and this task file.
- [ ] The SECURITY.md wording is reviewed by the maintainer before merge, since it is security-policy text (CLAUDE.md rule on flagging security-relevant changes).
- [ ] Text is English ([`documentation-style.md`](../../../standards/documentation-style.md)).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

**Step-scoped evidence allowance.** In addition to the named content files, the step may update this task, `docs/roadmap/current.md`, the B.2 task/track indexes, governing decision references, source-bound reports/raw evidence, canonical review artifacts and their indexes where necessary. Verify this allowance against the step commit range, not the full stacked branch. Record a demonstrated existing-scope reason for any further file.

## Design notes

**Open decisions.** None blocking.
Ambiguity to resolve while writing: the task brief says the capability-management syscalls are "not wired until Phase E", but ADR-0031 (line 121) only says they land "when a real consumer (a multi-task userspace service, post-B6) surfaces", while `phase-e.md` (Epic 1, lines 132-166) ties the `cap_map`/`cap_unmap` syscall wiring to Phase E hardening; write only what the cited document supports.

**Location re-verification (2026-10-11, against the current tree).**
`CONTRIBUTING.md:3` and `:14`, and `SECURITY.md:7`, all reproduce unchanged; neither file was touched by the kickoff.
Adjacent, not in the plan item: `CONTRIBUTING.md:17-23` ("When the project enters the implementation phase ... will be expanded with ... CI gates") is also out of step, because implementation is under way and CI gates exist (see `docs/guides/ci.md`); this adjacent stale section is included in the approved 2026-10-12 contract.
`console_write` being debug-build-only currently depends on `cfg!(debug_assertions)` in `SyscallNumber::decode`; if [T-065](T-065-debug-console-feature-flag.md) later moves the gate to a dedicated feature, the SECURITY.md sentence needs a one-line update then.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-12 | Codex (AI agent), maintainer-approved reconciliation | Old: future-implementation CONTRIBUTING section excluded and current EL0 fault/exit limits incomplete. Approved replacement: present workflow plus five-syscall surface and trust/fault/reclamation limits, separate security reviews and maintainer SECURITY review before merge; disclosure unchanged. See [approved preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); preparation only, status unchanged. |
