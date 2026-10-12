# T-050 — Refresh README, guides index, glossary, and the add-bsp skill trace

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

As a newcomer following the README, the guides index, the glossary, and the BSP-porting skill, I want each of them to show the project as it is today, so that the Quick-Start output I compare against, the guide list I browse, and the terms I look up are accurate.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), covering the entry-document and glossary items of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-2 ("Roadmap & task/review index synchronization" and "Misc doc hygiene").
The README Quick-Start trace shows a `tyrne: image loaded (...)` line (now `README.md:96`) that the kernel no longer prints (`grep -n "image loaded" bsp-qemu-virt/src/main.rs` finds nothing); the README's "small audited set" of kernel `unsafe` (`README.md:57`) omits the copy-from/to-user block that guards the syscall boundary; [`docs/guides/README.md`](../../../guides/README.md) still calls the project "in the architecture phase" and omits two of the four guide files that exist; the glossary lacks PMM and AddressSpace and breaks its own alphabetical rule in two places; `.agents/skills/add-bsp/SKILL.md` shows a round-robin trace the kernel no longer produces; and `NOTICE` and `LICENSE` name different copyright holders.
The kickoff already rewrote the README status sentences, which shifted the two README locations by one line from the plan item's numbers.
CONTRIBUTING.md and SECURITY.md are [T-051](T-051-contributing-and-security-status.md); the architecture chapters are [T-045](T-045-docs-overview-taskloader-arch-index.md) and [T-046](T-046-docs-subsystem-chapters-refresh.md).

## Acceptance criteria

- [ ] `docs/guides/README.md`: the Status paragraph (line 7) matches the README's framing instead of "the architecture phase"; rows for `two-task-demo.md` and `first-userspace.md` are added with the status their own headers justify; the stale "Planned — Phase 2/3/4" tags (lines 13-19) are replaced with the lettered-phase scheme or dropped; `ls docs/guides/*.md` and the table list the same set of existing files.
- [ ] `README.md` "Documentation map" (the "Reader who wants to do something concrete" list, lines 242-247) links `docs/guides/first-userspace.md`.
- [ ] `README.md` Quick-Start trace (line 96 and its neighbours): the `tyrne: image loaded (...)` line is removed and every remaining line is verified against a live `cargo kernel-run` / `tools/smoke.sh --int` trace, eliding fragile values with `...` as [`first-userspace.md`](../../../guides/first-userspace.md) does; `grep -n "image loaded" README.md` returns nothing. `README.md:57` (kernel-crate `unsafe` enumeration) names the copy-from/to-user byte move (audit entry UNSAFE-2026-0030, `kernel/src/syscall/user_access.rs`), or is reworded as explicitly illustrative; verified against [`unsafe-log.md`](../../../audits/unsafe-log.md).
- [ ] `docs/glossary.md`: entries for **AddressSpace** (cites [ADR-0028](../../../decisions/0028-address-space-data-structure.md); inserted before `ADR`, line 9) and **PMM** (Physical Memory Manager; cites [ADR-0035](../../../decisions/0035-physical-memory-manager.md); inserted before `PSCI`, line 75), written per the [`update-glossary`](../../../../.agents/skills/update-glossary/SKILL.md) format and verified against `kernel/src/mm/`; plus entries for **Bridge phase** (a phase inserted after publication with a dotted ID such as `B.2`; cites [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md)) and **Track** (the sub-unit of a bridge phase, `B.2-1`…`B.2-6`).
- [ ] `docs/glossary.md` ordering: the M section (lines 57-67) reads MADR, MAIR, MapperFlush, Microkernel, Miri, MMU, and Rendezvous IPC precedes Reply capability (lines 81-83); record the pure ordering moves separately from source-verified factual corrections to existing glossary definitions; do not freeze stale entry text.
- [ ] `docs/glossary.md` anchors: an `<a id="…"></a>` is placed immediately before each headword, ids are unique and stable, and the rendered list looks unchanged; the id scheme is recorded in the review history.
- [ ] Path templates that hard-code `phase-<letter>` are generalised for dotted bridge-phase IDs: `docs/analysis/README.md` (line 16), `docs/roadmap/README.md` (lines 16 and 21) and `.agents/skills/start-task/SKILL.md` (lines 21, 30, 41, 43, 61) say `phase-<id>` and note that phase `B.2` maps to the folder `phase-b2` and the file `phase-b2.md`, so the first person opening a task under a bridge phase finds a documented path.
- [ ] `.agents/skills/add-bsp/SKILL.md` step 10 (lines 155-166): the example trace is replaced by the current minimal-success shape (ending at the `tyrne: all tasks complete` marker that `tools/smoke.sh` gates on) plus a note that exact trailing lines depend on the kernel version and point to the README Quick Start; verified against the live trace.
- [ ] `NOTICE:2` and `LICENSE:189` name the same copyright holder: the maintainer's choice of holder string is recorded in the review history first (see Open decisions), then both files are updated; only line 189 of `LICENSE` changes.

- [ ] Verify clean-checkout README/two-task commands build userland before the BSP; correct first-userspace/two-task guide semantics (exit does not return to EL0 or reclaim resources; task_exit_current is a free function; AP/UXN/PXN meanings are precise). Correct existing glossary claims about console rights, badges, preemption, deadlines, GIC/MMU/bootstrap frames and Tree Borrows from source. Make the add-bsp boot template mask DAIF before unsafe setup and distinguish minimal BSP success from the full reference EL0 trace. Document --int as int,unimp and use the printed PID-scoped log path.

## Out of scope

- CONTRIBUTING.md and SECURITY.md status text: [T-051](T-051-contributing-and-security-status.md).
- Architecture chapters and the architecture index: [T-045](T-045-docs-overview-taskloader-arch-index.md), [T-046](T-046-docs-subsystem-chapters-refresh.md).
- Outward links from other documents to the new glossary entries (`update-glossary` step 5); the anchors make them possible, adding them is an optional follow-up.
- Changing glossary vocabulary beyond the approved four additions and source-backed corrections; retain the explicitly grouped `mmu_bootstrap` / `.boot_pt` sub-entry convention.
- Changing any Apache-2.0 license text other than the copyright line of the appendix.

## Approach

Start from the live trace, because three criteria depend on it: run `tools/smoke.sh --int` (or `cargo kernel-run`) and copy the lines that exist, eliding counts and addresses.
Then edit the README and the add-bsp skill from that trace, add all four glossary entries following the skill's format (self-contained first sentence, ADR citation), perform the two cut-and-paste reorderings, and add anchors in one mechanical pass.
Rewrite the guides index Status paragraph in the README's framing and add the two missing rows.
The maintainer resolved the identity on 2026-10-12: use the common line `Copyright 2026 HodeTech, Cemil ILIK and Tyrne Contributors` in NOTICE and the LICENSE appendix, preserving spelling/capitalization and all other license text.

## Definition of done

Doc-only variant:

- [ ] Every relative link (`](…)` target) in each touched file resolves to an existing path or heading.
- [ ] `git diff --stat` lists only: `README.md`, `docs/guides/{README,two-task-demo,first-userspace}.md`, `docs/glossary.md`, `.agents/skills/add-bsp/SKILL.md`, `.agents/skills/start-task/SKILL.md`, `docs/analysis/README.md`, `docs/roadmap/README.md`, `NOTICE`, `LICENSE`, `docs/roadmap/current.md`, and this task file.
- [ ] Text is English; fences are tagged ([`documentation-style.md`](../../../standards/documentation-style.md)).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

**Step-scoped evidence allowance.** In addition to the named content files, the step may update this task, `docs/roadmap/current.md`, the B.2 task/track indexes, governing decision references, source-bound reports/raw evidence, canonical review artifacts and their indexes where necessary. Verify this allowance against the step commit range, not the full stacked branch. Record a demonstrated existing-scope reason for any further file.

## Design notes

**Open decisions.**
(1) Resolved by the maintainer on 2026-10-12: `HodeTech, Cemil ILIK and Tyrne Contributors`; apply the exact common copyright line in the Approach.
(2) Anchor id scheme (for example lowercase hyphenated headword) is an implementer choice recorded in the review history.

**Location re-verification (2026-10-11, against the current tree).**
Drifted by the kickoff's README edit: the Quick-Start `image loaded` line is `README.md:96` (was 95) and the unsafe enumeration is `README.md:57` (was 56).
Unchanged: `docs/guides/README.md:7,12-19` (table at 11-19), `docs/glossary.md:57-67` and `:81-83` (50 entries at opening, so 54 anchors after all four approved new entries (recount at implementation)), `.agents/skills/add-bsp/SKILL.md:155-166` (step heading at 155, trace fence at 159-166), `NOTICE:2`, `LICENSE:189`.
Adjacent, not in the plan item: the same skill (lines 150, 170) quotes a fixed `/tmp/qemu_int.log`, while `tools/run-qemu.sh` now writes `${TMPDIR:-/tmp}/qemu_int.<pid>.log`; fix it in the same edit if it is still wrong when you get there.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-12 | Codex (AI agent), maintainer-approved reconciliation | Old: two-entry/52-anchor approach, existing definition text frozen, guide/build/template corrections omitted and copyright undecided. Approved replacement: four terms/54 anchors after recount, source-backed existing definitions and clean-checkout/guide/DAIF corrections; exact Copyright 2026 HodeTech, Cemil ILIK and Tyrne Contributors line approved. See [approved preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); preparation only, status unchanged. |
