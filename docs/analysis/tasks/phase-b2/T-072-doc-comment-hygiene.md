# T-072 — Correct stale doc comments across kernel, HAL, and BSP

- **Phase:** B.2
- **Milestone:** Track B.2-5
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** [T-042](T-042-pmm-defensive-validation.md), [T-062](T-062-linker-and-boot-consistency-checks.md)
- **Informs:** none
- **ADRs required:** none

---

## User story

As a maintainer reasoning about the kernel from its rustdoc, I want module, crate and function documentation to describe the code that exists after Phase B, so that I never derive an invariant from a comment about a design that did not ship.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). Track B.2-5 of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) is the code-level counterpart of the documentation cascade: twelve doc-comment defects in `hal`, the BSP and the kernel crate. One is security-relevant — the doc of `Pmm::could_yield_pa_overlapping` still describes the ADR-0033 high-half migration as a future placeholder, although it landed with T-022 and the loader already calls `tyrne_hal::kernel_va_to_phys`; that doc discharges the non-overlap precondition of UNSAFE-2026-0027, so a stale premise there misleads whoever reasons about it next. The task is documentation-only except for one behaviour-preserving option (criterion 7). It runs after [T-042](T-042-pmm-defensive-validation.md) (same `pmm.rs`) and [T-062](T-062-linker-and-boot-consistency-checks.md) (the `main.rs` / linker-script comments).

## Acceptance criteria

- [ ] **hal:** `hal/src/mmu/vmsav8.rs` (doc of `DESC_TABLE_OR_PAGE_BIT`, lines 222-228 at opening) no longer claims an L0 block descriptor exists: L0 with bit 1 = 0 is documented as reserved (translation fault), blocks exist only at L1 (1 GiB) and L2 (2 MiB), stated for the 4 KiB-granule, 48-bit-VA configuration this project uses ([ADR-0027](../../../decisions/0027-kernel-virtual-memory-layout.md)); check the Arm ARM descriptor tables for that configuration before wording it (an architecture extension such as FEAT_LPA2 changes which levels allow blocks, so do not state it unqualified).
- [ ] **bsp:** `bsp-qemu-virt/src/exceptions.rs` line 34 reads "IRQ-dispatch table" (no doubled word); the `PMM_EXTENT_START` comment (`main.rs` lines 95-96) no longer cites a linker `MEMORY`/`RAM`/`ORIGIN` construct — it names what actually fixes the value (ADR-0012's 128 MiB RAM at PA `0x4000_0000`, and the `KBASE` placement in `linker.ld`).
- [ ] **kernel crate docs:** `kernel/src/lib.rs` crate documentation (lines 5-10) states the real scope (capability system, scheduler, IPC, memory management, the kernel half of the syscall boundary; asynchronous interrupt handling lives in the BSP per P6; the kernel sees only cooperative masking such as `sched::IrqGuard`), and the lint-provenance comment (lines 51-54) is replaced by a pointer to `[workspace.lints]` in the root `Cargo.toml` instead of an itemised list that omits `unreachable_pub` and `unused_must_use`.
- [ ] **kernel object modules:** the module and type docs of `kernel/src/obj/endpoint.rs` (lines 5-7, 16-17), `notification.rs` (lines 5-7) and `task.rs` (lines 5-7) say where the real state lives — IPC wait state in `ipc::IpcQueues`, scheduler per-task state in the `sched::Scheduler` arrays — and that blocking Notification wait is still unimplemented (an open roadmap item), instead of describing Milestone A4/A5 plans.
- [ ] **sched:** the `SchedError::QueueFull` doc (`kernel/src/sched/mod.rs` lines 178-186) says it is produced by `add_task` **and** `add_user_task` at registration time (both links), still excluding the bridge entry points.
- [ ] **mm docs:** `Pmm::could_yield_pa_overlapping`'s doc (`kernel/src/mm/pmm.rs` lines 560-565) states the ADR-0033 migration is complete and names `tyrne_hal::kernel_va_to_phys` as the helper, matching the phrasing in `phys_frame_kernel_ptr`'s doc and the loader's call-site comment; the inline "Validation (i)…(iv)" labels in `Pmm::new` (including the back-reference near line 397) are renumbered to match the docstring's steps 1-5 (lines 159-178); the duplicate "Step 4" comment in `cap_create_address_space` (`kernel/src/mm/address_space.rs` lines 605 and 611) becomes Step 5 for the second.
- [ ] **helper vs doc:** the doc of `cap_create_address_space` (`address_space.rs` line 447) claims it resolves the parent capability "via `resolve_address_space_cap`" but the body (lines 547-553) re-implements the lookup; `task_loader.rs` lines 538-543 re-implements it too. Either both call the shared helper (behaviour-preserving; `cargo host-test` and Miri unchanged) or the doc is corrected — the choice is recorded in the review history.
- [ ] **loader contract:** `load_image`'s rustdoc gains a `# Panics` section stating that a slice that is not kernel-owned memory makes `kernel_va_to_phys` panic rather than return a `LoadError` (`kernel/src/obj/task_loader.rs`, call site near line 604), cross-referencing `kernel_va_to_phys`'s own panic contract.
- [ ] Verification: `cargo doc --no-deps` (host crates) shows no new warnings; `cargo fmt --all -- --check`, `cargo host-clippy`, `cargo kernel-clippy` clean; `git diff` shows comment-only changes except the optional helper adoption.

## Out of scope

- The false atomicity premise in `pmm.rs` comments — [T-042](T-042-pmm-defensive-validation.md) (behaviour of the bitmap is Phase C work).
- Audit-log entries that mention these sites — [T-069](T-069-unsafe-log-corrections.md).
- Architecture chapters under `docs/architecture/` — [T-045](T-045-docs-overview-taskloader-arch-index.md) and [T-046](T-046-docs-subsystem-chapters-refresh.md).
- Any API or behaviour change other than the optional helper adoption.

## Approach

Work crate by crate in the order of the criteria. For every comment, verify the claim against the code before rewriting it (the loader call to `kernel_va_to_phys` and the `phys_frame_kernel_ptr` doc are the reference phrasing). Keep wording consistent across the three kernel object modules. For the helper/doc choice, prefer calling the helper if the extension needed (returning the capability, its rights and depth) is small; otherwise correct the doc and leave a one-line note.

## Definition of done

- [ ] `cargo fmt --all -- --check`, `cargo host-clippy`, `cargo kernel-clippy` clean; `cargo host-test` passes (count unchanged).
- [ ] `cargo miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` clean if the helper is adopted.
- [ ] Every relative link in each touched file resolves.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Location re-verification (2026-10-11, HEAD `400dec0`):** all cited locations match the tree. The `vmsav8.rs` comment today reads "L0/L1 with bit1=0 → block descriptor (huge page)" followed by a separate L2 bullet; the `QueueFull` doc says "Produced **only** by [`add_task`]" while `add_user_task` returns it at lines 493-497; `address_space.rs` has "Step 4" at both lines 605 and 611 and Steps 6-7 follow.
- **Open decisions:** helper adoption vs doc correction (criterion 7).
- Twelve plan items are grouped into nine criteria by area to stay under the ten-criterion limit; none is dropped.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
