# T-050 — Refresh README, guides index, glossary, and the add-bsp skill trace

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** none
- **ADRs required:** none

---

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
- [ ] `README.md` Quick-Start trace (line 96 and its neighbours): the `tyrne: image loaded (...)` line is removed and every remaining line is verified against a live `cargo kernel-run` / `tools/smoke.sh --int` trace, eliding fragile values with `...` as [`first-userspace.md`](../../../guides/first-userspace.md) does; `grep -n "image loaded" README.md` returns nothing.
- [ ] `README.md:57` (kernel-crate `unsafe` enumeration) names the copy-from/to-user byte move (audit entry UNSAFE-2026-0030, `kernel/src/syscall/user_access.rs`), or is reworded as explicitly illustrative; verified against [`unsafe-log.md`](../../../audits/unsafe-log.md).
- [ ] `docs/glossary.md`: entries for **AddressSpace** (cites [ADR-0028](../../../decisions/0028-address-space-data-structure.md); inserted before `ADR`, line 9) and **PMM** (Physical Memory Manager; cites [ADR-0035](../../../decisions/0035-physical-memory-manager.md); inserted before `PSCI`, line 75), written per the [`update-glossary`](../../../../.agents/skills/update-glossary/SKILL.md) format and verified against `kernel/src/mm/`.
- [ ] `docs/glossary.md` ordering: the M section (lines 57-67) reads MADR, MAIR, MapperFlush, Microkernel, Miri, MMU, and Rendezvous IPC precedes Reply capability (lines 81-83); both are pure moves, so `git diff --word-diff` shows no changed entry text.
- [ ] `docs/glossary.md` anchors: an `<a id="…"></a>` is placed immediately before each headword, ids are unique and stable, and the rendered list looks unchanged; the id scheme is recorded in the review history.
- [ ] `.agents/skills/add-bsp/SKILL.md` step 10 (lines 155-166): the example trace is replaced by the current minimal-success shape (ending at the `tyrne: all tasks complete` marker that `tools/smoke.sh` gates on) plus a note that exact trailing lines depend on the kernel version and point to the README Quick Start; verified against the live trace.
- [ ] `NOTICE:2` and `LICENSE:189` name the same copyright holder: the maintainer's choice of holder string is recorded in the review history first (see Open decisions), then both files are updated; only line 189 of `LICENSE` changes.

## Out of scope

- CONTRIBUTING.md and SECURITY.md status text: [T-051](T-051-contributing-and-security-status.md).
- Architecture chapters and the architecture index: [T-045](T-045-docs-overview-taskloader-arch-index.md), [T-046](T-046-docs-subsystem-chapters-refresh.md).
- Outward links from other documents to the new glossary entries (`update-glossary` step 5); the anchors make them possible, adding them is an optional follow-up.
- Reordering `mmu_bootstrap` and `.boot_pt` (sub-entries placed after `MMU`), which the plan item does not flag.
- Changing any Apache-2.0 license text other than the copyright line of the appendix.

## Approach

Start from the live trace, because three criteria depend on it: run `tools/smoke.sh --int` (or `cargo kernel-run`) and copy the lines that exist, eliding counts and addresses.
Then edit the README and the add-bsp skill from that trace, add the two glossary entries following the skill's format (self-contained first sentence, ADR citation), perform the two cut-and-paste reorderings, and add anchors in one mechanical pass.
Rewrite the guides index Status paragraph in the README's framing and add the two missing rows.
The NOTICE/LICENSE alignment waits on the maintainer's decision; if it is still open when everything else is done, the task stays at `Ready` with that single criterion unchecked and a one-line proposal in the review history.

## Definition of done

Doc-only variant:

- [ ] Every relative link (`](…)` target) in each touched file resolves to an existing path or heading.
- [ ] `git diff --stat` lists only: `README.md`, `docs/guides/README.md`, `docs/glossary.md`, `.agents/skills/add-bsp/SKILL.md`, `NOTICE`, `LICENSE`, and this task file.
- [ ] Text is English; fences are tagged ([`documentation-style.md`](../../../standards/documentation-style.md)).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

**Open decisions.**
(1) Copyright holder string: `NOTICE:2` names the organisation plus contributors, `LICENSE:189` names the individual maintainer plus contributors, and the root `Cargo.toml` `authors` field (line 32) names the individual. The plan item suggests one combined string naming both the organisation and the maintainer in both files; which wording is used is a legal-identity choice for the maintainer. If undecided, leave the one-line proposal in the review history; this task does not close until it is decided.
(2) Anchor id scheme (for example lowercase hyphenated headword) is an implementer choice recorded in the review history.

**Location re-verification (2026-10-11, against the current tree).**
Drifted by the kickoff's README edit: the Quick-Start `image loaded` line is `README.md:96` (was 95) and the unsafe enumeration is `README.md:57` (was 56).
Unchanged: `docs/guides/README.md:7,12-19` (table at 11-19), `docs/glossary.md:57-67` and `:81-83` (50 entries today, so 52 anchors once the two new entries exist), `.agents/skills/add-bsp/SKILL.md:155-166` (step heading at 155, trace fence at 159-166), `NOTICE:2`, `LICENSE:189`.
Adjacent, not in the plan item: the same skill (lines 150, 170) quotes a fixed `/tmp/qemu_int.log`, while `tools/run-qemu.sh` now writes `${TMPDIR:-/tmp}/qemu_int.<pid>.log`; fix it in the same edit if it is still wrong when you get there.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
