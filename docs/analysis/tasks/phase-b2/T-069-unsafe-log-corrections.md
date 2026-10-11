# T-069 — Correct the unsafe audit log entries

- **Phase:** B.2
- **Milestone:** Track B.2-5
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** none
- **ADRs required:** none

---

## User story

As the maintainer running the quarterly `unsafe` review, I want every audit-log entry to match the code site it audits, so that I can trust an entry's Location, Operation and Invariants without cross-reading its Amendments and the source.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from three items and one Polish item in [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) Track B.2-5: UNSAFE-2026-0028's fields contradict its own Amendment (line 475), a second `Pl011Uart::new` site cites UNSAFE-2026-0001 without being covered by it (line 478), UNSAFE-2026-0030's heading still names `copy_nonoverlapping` (line 490), and the Polish item at line 620 (state the "no slot reuse" precondition in UNSAFE-2026-0008 and 0014). The first two share a root cause: T-022 split `kernel_entry` into `kernel_entry` and `kernel_main_high`, and the log was updated for UNSAFE-2026-0022 to 0027 (each carries a T-022 Amendment) but not for these.

The log is append-only ([`unsafe-policy.md`](../../../standards/unsafe-policy.md) section 3 and the log header): an entry's original body must not be rewritten, and the only permitted post-hoc forms are a status change and a dated `**Amendment (YYYY-MM-DD, commit SHA): <short title>.**` block appended at the entry's end, which restates the additional location, operation, invariants and rejected alternatives (canonical example: UNSAFE-2026-0011). The plan's "update the Location/Invariants fields" alternative is therefore not available; its "correction note pointing to the Amendment" alternative is, as a new Amendment. On 2026-10-11 the log has 33 `### UNSAFE-` entries (32 Active, 1 Removed), 48 Amendment blocks, and no orphan tag in either direction; that invariant must survive.

## Acceptance criteria

- [ ] UNSAFE-2026-0028 gains an appended Amendment stating that its sole call site is the bootstrap-AS wrap block in `kernel_main_high` (`bsp-qemu-virt/src/main.rs:1176`, `from_existing_root`) and that the `kernel_entry` wording in its Location (log line 636), Operation (637), Invariants (640) and Status (649) is historical. No existing line of the entry is edited.
- [ ] UNSAFE-2026-0001 gains an Amendment covering the persistent Console built in `kernel_main_high`, `Pl011Uart::new(tyrne_hal::phys_to_kernel_va(PL011_UART_BASE))` (`main.rs:1013-1015`): new function, new address expression (the high-half alias of the same PL011), the three original invariants restated for it, and a sentence that the `kernel_entry` early console (`main.rs:841`) stays covered by the original body.
- [ ] UNSAFE-2026-0030: the title question (log line 676) is decided and recorded in the review history (Open decisions). Default: the `###` heading is left unchanged and an Amendment states that it names the original primitive while both `unsafe` blocks use `core::ptr::copy` (`user_access.rs:245,313`). If the maintainer instead rules for a rename, every inbound `#unsafe-2026-0030--…` anchor (7 occurrences in 6 files, listed in Design notes) is repointed in the same commit.
- [ ] UNSAFE-2026-0008 and UNSAFE-2026-0014 each gain an Amendment stating the precondition their distinct-task-index invariant silently depends on: no live `TaskHandle` in `current`/`ready`/`idle` names a slot whose Arena generation has since advanced (no task-slot reuse). Each says why it holds in v1 (evidence in Design notes) and that the future task/slot-reclamation lifecycle ADR must carry it as an acceptance criterion.
- [ ] Policy compliance for every Amendment added: the exact `**Amendment (YYYY-MM-DD, commit SHA): <short title>.**` header (the SHA may be backfilled after the commit, as [`justify-unsafe`](../../../../.agents/skills/justify-unsafe/SKILL.md) step 5 allows); placed at the end of its own entry; a `Reviewed by` line in the style of that entry, repeating the second-reviewer requirement for 0028 and 0030, whose entries state it ([`unsafe-policy.md`](../../../standards/unsafe-policy.md) Review items 3-4); `git diff` of the log shows no removed line.
- [ ] Tests: the tag cross-check in Approach prints nothing before and after, the entry count is still 33, and the Amendment count rises by exactly the number added (five on the default path: 0001, 0008, 0014, 0028, 0030), with the before/after numbers recorded in the review history.

## Out of scope

- UNSAFE-2026-0033 (x2 clobber): [T-038](T-038-console-write-x2-clobber.md). Amendments for 0020 and 0029: [T-070](T-070-trap-frame-offset-assertions.md). Amendments for 0025 and 0026: [T-071](T-071-unsafe-contract-hardening.md).
- Any source change. In particular the code half of the slot-reuse finding (promote `debug_assert_ne!` to a real check; fix the "Shared safety contract" comment at `kernel/src/sched/mod.rs:684-689`) is Phase C work, listed in [`phase-c.md`](../../../roadmap/phases/phase-c.md) under the "Context-switch anti-aliasing invariant" item.
- Automating the tag cross-check: [T-056](T-056-docs-consistency-automation.md).

## Approach

Append one Amendment per tag (five on the default path), each restating the corrected location, operation and invariants rather than editing the old text. Use the existing T-022 Amendments (e.g. the one on 0028 itself, log line 651) as the style reference. Run the cross-check before the first edit and after the last:

```bash
comm -3 <(grep -rhoE 'UNSAFE-[0-9]{4}-[0-9]{4}' --include='*.rs' --include='*.s' bsp-qemu-virt kernel hal test-hal userland | sort -u) \
        <(grep -oE '^### UNSAFE-[0-9]{4}-[0-9]{4}' docs/audits/unsafe-log.md | sed 's/^### //' | sort -u)   # no output
grep -c '^### UNSAFE-' docs/audits/unsafe-log.md        # 33
grep -c '\*\*Amendment (20' docs/audits/unsafe-log.md   # 48 before; +1 per Amendment added
git diff --numstat main...HEAD -- docs/audits/unsafe-log.md | awk '$2 != 0'   # no output: nothing deleted
```

## Definition of done

Beyond the acceptance criteria (documentation-only task):

- [ ] Every `](…)` target in `docs/audits/unsafe-log.md` and in this file resolves (`cd docs/audits && grep -oE '\]\([^)#[:space:]]+' unsafe-log.md | sed 's/^](//' | grep -v '^http' | sort -u | while read -r p; do [ -e "$p" ] || echo "BROKEN: $p"; done` prints nothing).
- [ ] `git diff --stat` shows only `docs/audits/unsafe-log.md`, this task file, the phase-b2 task index and `docs/roadmap/current.md` (plus the six files carrying inbound anchors only if the rename ruling is taken).
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040` and one `Audit: UNSAFE-2026-NNNN` trailer per amended tag.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decision, UNSAFE-2026-0030 title.** The plan says "update the heading". Editing a heading edits the entry's original body (policy section 3), and it breaks inbound anchors. Seven links in six files target `#unsafe-2026-0030--validated-copy-fromto-user-byte-move-via-coreptrcopy_nonoverlapping`: `docs/analysis/tasks/phase-b/T-021-syscall-dispatch.md:99`, `docs/architecture/exceptions.md:135`, `docs/roadmap/current.md:23`, `docs/analysis/reviews/business-reviews/2026-05-29-B5-closure.md:43`, `docs/analysis/reviews/performance-optimization-reviews/2026-05-29-B5-closure.md:210,213` and `docs/analysis/reviews/security-reviews/2026-05-29-B5-syscall-boundary.md:6`. The mechanical-edit exemption in section 3 covers terminology sweeps with a named, uniform substitution; whether a primitive rename qualifies is a maintainer call. Default is the conservative Amendment-only path; record the ruling in the review history.
- **Evidence for the slot-reuse Amendments (re-verify when writing).** The only non-test `destroy_task` call is the rollback at `kernel/src/obj/task_loader.rs:963`, on a handle created in the same call and never registered with the scheduler; `task_exit_current` does not reclaim the exiting task's slot (UNSAFE-2026-0008's own 2026-06-01 Amendment, SEC-T028-01; see also [T-028](../phase-b/T-028-el0-userspace-wireup.md) line 25). The precondition wording is taken from the `phase-c.md` item named above.
- **Wider observation, not owned here.** UNSAFE-2026-0001 is also cited as the audit tag for 11 further `StaticCell` write-once publication sites in `bsp-qemu-virt/src/main.rs` (lines 1021, 1026, 1028, 1045, 1072, 1091, 1098, 1363, 1413, 1531, 1631) and 3 in `perf_bench.rs`, which its Operation field does not describe. The plan item covers only the `Pl011Uart::new` site; flag the pattern to the maintainer for the next quarterly review rather than widening the Amendment silently.
- **Re-verification (2026-10-11).** All cited locations match the current tree; `phase-b2.md` line numbers are those of the live file (snapshot plus 2), so locate items by their headline words. The brief counted 49 amendments; `grep -c 'Amendment ('` gives 49 only because it also matches the policy sentence at log line 8 (48 real blocks).
- **Sequencing.** [T-038](T-038-console-write-x2-clobber.md), [T-070](T-070-trap-frame-offset-assertions.md) and [T-071](T-071-unsafe-contract-hardening.md) also append Amendments to this file, and [T-044](T-044-bootstrap-as-handle-invariant.md) edits the `kernel_main_high` block cited above. Cite entries by tag and symbol, not only by line, and keep each entry's Amendments in date order when resolving merge conflicts.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
