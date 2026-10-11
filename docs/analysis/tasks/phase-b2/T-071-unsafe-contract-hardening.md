# T-071 — Make unsafe preconditions enforceable (FrameProvider::alloc_frame, add_user_task)

- **Phase:** B.2
- **Milestone:** Track B.2-5
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** none
- **ADRs required:** an append-only [ADR-0009](../../../decisions/0009-mmu-trait.md) revision-note rider, only if `FrameProvider::alloc_frame` becomes `unsafe fn` (see Open decisions)

---

## User story

As the kernel's `unsafe` audit surface, I want the two load-bearing preconditions the review found, zero-initialised frames from `FrameProvider::alloc_frame` and valid stack arguments to `add_user_task`, to be enforced by an `unsafe` contract or a release-mode check rather than by prose and debug asserts, so that a wrong implementer or caller fails loudly instead of corrupting a translation table or entering EL0 on a bad stack.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md) from [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) lines 529 (MEDIUM), 532 (LOW) and the Polish item at line 669. `FrameProvider::alloc_frame` (`hal/src/mmu/mod.rs:349-355`) is a safe trait method whose doc says "Allocate a zero-initialized `PhysFrame`". The BSP walker relies on that: `walk_or_alloc_table` (`bsp-qemu-virt/src/mmu.rs:622-631`) installs a table descriptor pointing at the returned frame and its SAFETY comment says "caller's `FrameProvider` contract guarantees the frame is zero-initialised" (audit UNSAFE-2026-0025); a non-zero frame would later be walked as pre-populated descriptors. The structurally identical contract on `Mmu::create_address_space` (`hal/src/mmu/mod.rs:481-488`) is an `unsafe fn` with a `# Safety` section. Implementers: `Pmm` (`kernel/src/mm/pmm.rs:722`, which zero-fills under UNSAFE-2026-0026), `NullFrameProvider` (`bsp-qemu-virt/src/mmu.rs:457`) and test-hal's `VecFrameProvider` (`test-hal/src/mmu.rs:52`, documented as not zero-filling and satisfying the contract only vacuously).

`Scheduler::add_user_task` (`kernel/src/sched/mod.rs:444-516`) is an `unsafe fn` that hardens one hazard for release builds: it keeps `None` instead of `Some(null)` for a null `cap_table` (`:510`, after the `debug_assert!` at `:477-480`). The equally load-bearing `kernel_stack_top` (non-null, 16-byte aligned; becomes `SP_EL1`) and `user_sp` (16-byte aligned; becomes `SP_EL0`) are `debug_assert!` only (`:455-471`), so a release build forwards them unchecked to `init_user_context` (`:485-492`).

## Acceptance criteria

- [ ] Decision D1 (how `alloc_frame`'s zero-init contract is enforced) is recorded in the review history; if the answer is `unsafe fn`, an append-only revision-note rider is added to ADR-0009 (`## Revision notes`, precedent: the 2026-05-31 `translate` rider) in the same change.
- [ ] D1 implemented. Either (a) `alloc_frame` becomes `unsafe fn` with a `# Safety` section stating zero-initialised, page-aligned and exclusively owned until returned, mirroring `create_address_space`; the two trait-dispatch call sites (`bsp-qemu-virt/src/mmu.rs:623`, `test-hal/src/mmu.rs:397`) carry conforming `// SAFETY:` comments and the three implementers compile against the new contract; or (b) `walk_or_alloc_table`'s new-table branch (`mmu.rs:622-631`) gains a debug-only assertion that all 512 descriptor words of `new_table` are zero before the table descriptor is installed, compiled out in release.
- [ ] Audit log: an Amendment on UNSAFE-2026-0025 (the consumer; its Operation, log line 536, names this allocation and its justification changes under either option) and, only under option (a), on UNSAFE-2026-0026 (the producer). Each uses the `**Amendment (YYYY-MM-DD, commit SHA): <short title>.**` header, is appended at the entry's end with no existing line edited (`git diff` of the log shows no removed line), carries a `Reviewed by` line, and states the second-reviewer requirement ([`unsafe-policy.md`](../../../standards/unsafe-policy.md) section 3, Review items 3-4). The UNSAFE tag cross-check from [T-069](T-069-unsafe-log-corrections.md) Approach still prints nothing.
- [ ] Decision D2 (`add_user_task` posture for `kernel_stack_top` and `user_sp`) is recorded in the review history.
- [ ] D2 implemented. Either (a) a null or misaligned `kernel_stack_top`, or a misaligned `user_sp`, is refused in release builds before `init_user_context` runs, leaving no partial registration, with the `# Errors` section (`:408-412`) extended and one host test per rejected input; or (b) the `# Safety` section (`:414-434`) states why only `cap_table` warranted release-mode hardening and the debug asserts stay.
- [ ] Tests: `cargo host-test` and `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` pass; `cargo kernel-build`, `cargo kernel-clippy` and `tools/smoke.sh --int` pass with an unchanged trace. Under D1 (b), a recorded negative check shows the assertion firing when the PMM's zero-fill is temporarily skipped (debug boot panics; not committed).
- [ ] The security review required for memory-management, scheduler and `unsafe` changes ([`security-review.md`](../../../standards/security-review.md)) is filed; the commit carries `Audit:` trailers for each amended tag and a `Security-Review:` trailer.

## Out of scope

- Making `Pmm`'s bitmap atomic, or any SMP allocation change: Phase C ([`phase-c.md`](../../../roadmap/phases/phase-c.md) section 1); the false atomicity comment is [T-042](T-042-pmm-defensive-validation.md).
- Typed `PhysAddr`/`VirtAddr` arguments to `init_user_context`: [T-057](T-057-typed-addresses-phys-virt.md).
- The `MapperFlush` address-space discriminant: [T-040](T-040-mapperflush-asid-discriminant.md).
- Freeing frames or any `free_frame` on the `FrameProvider` trait.

## Approach

The two decisions are independent and can land as separate commits. For D1, the plan item offers two forms and does not pick one; the trade-offs are in Design notes. For D2, the plan calls the current state defensible (the function is `unsafe`, its callers are in-tree) and offers either the release-mode degrade-safely pattern already used for `cap_table` or a documented rationale for why `cap_table` alone needed it. Whichever is chosen, make the posture uniform and visible inside `add_user_task` (the Polish item), update the audit Amendments to match, and keep every `// SAFETY:` comment conforming to [`unsafe-policy.md`](../../../standards/unsafe-policy.md) section 1.

## Definition of done

Beyond the acceptance criteria:

- [ ] `cargo fmt --all -- --check` clean.
- [ ] `cargo host-clippy` clean with `-D warnings`.
- [ ] `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes with any new tests added.
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean (hal, kernel and test-hal code change).
- [ ] `tools/smoke.sh --int` PASS (BSP and kernel code change).
- [ ] Every `](…)` target in the edited docs (`unsafe-log.md`, and `0009-mmu-trait.md` if the rider is added) resolves.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040` (and `Refs: ADR-0009` for the rider), `Audit: UNSAFE-2026-0025` (and `-0026`) and `Security-Review: <reviewer>` trailers.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Open decision D1.** Option (a) puts the proof burden on the caller, but the MMU walker cannot verify that a provider zeroed a frame; the guarantee is really made by each implementer. A third form not in the plan item, `unsafe trait FrameProvider`, models that directly (each `impl` carries the promise; `unsafe-policy.md` section 4 then requires a SAFETY comment on every production impl and an audit tag for `Pmm`'s). Option (b) is cheap and covers the one production consumer, but it checks nothing for fakes that never dereference frames (`VecFrameProvider`'s vacuous case). Decide, and put the reasoning in the ADR-0009 rider if the trait changes. Whether a trait method may be implemented as a safe `fn` when declared `unsafe fn` in the trait should be checked against the compiler before the criteria are finalised.
- **Open decision D2.** The plan does not define "degrade safely" for stack arguments. Refusing registration needs a typed outcome: `SchedError` is `#[non_exhaustive]` (`sched/mod.rs:171-173`), so a new variant is possible but is an API addition to decide explicitly. The window computation already fails closed for `user_sp < user_entry` (`saturating_sub`, `:505-514`).
- **Related stale doc, same edit.** The doc comment on `walk_or_alloc_table` (`bsp-qemu-virt/src/mmu.rs:567`) says it will "allocate a fresh frame from `frames`, zero it", but the body zeroes nothing; it relies on the provider contract. Correct the sentence when touching this site; its `# Safety` section (`:571-574`) also omits the provider contract.
- **Test-only exemption.** `unsafe-policy.md` section 3 exempts `unsafe` in `#[cfg(test)]` modules from audit entries; `test-hal` is a dev-dependency library crate, an open wording question (Polish item at `phase-b2.md` line 630). Give any new `unsafe` in `test-hal` a conforming SAFETY comment regardless.
- **Re-verification (2026-10-11).** All cited locations match the current tree. `phase-b2.md` line numbers are those of the live file; locate items by their headline words.
- **Sequencing.** `kernel/src/sched/mod.rs` is also edited by [T-068](T-068-kernel-tests-and-nits-bundle.md) and [T-072](T-072-doc-comment-hygiene.md), and `hal/src/mmu/mod.rs` by [T-040](T-040-mapperflush-asid-discriminant.md) and [T-057](T-057-typed-addresses-phys-virt.md); the hunks are disjoint but expect line numbers to move. [T-069](T-069-unsafe-log-corrections.md), [T-070](T-070-trap-frame-offset-assertions.md) and [T-038](T-038-console-write-x2-clobber.md) also append to `unsafe-log.md`.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
