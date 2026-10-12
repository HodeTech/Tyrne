# Phase B — tasks

Tasks belonging to [Phase B — Real userspace](../../../roadmap/phases/phase-b.md).

## Index

| ID | Title | Milestone | Status |
|----|-------|-----------|--------|
| [T-006](T-006-raw-pointer-scheduler-api.md) | Raw-pointer scheduler API refactor | B0 | Done (2026-04-27) |
| [T-007](T-007-idle-task-typed-deadlock.md) | Idle task + typed `SchedError::Deadlock` + resume-path hardening | B0 | Done (2026-04-27) |
| [T-008](T-008-architecture-docs.md) | Architecture docs (scheduler.md + ipc.md + hal.md/overview.md updates) | B0 | Done (2026-04-27) |
| [T-009](T-009-timer-init-cntvct.md) | Timer init + `CNTVCT_EL0` measurement | B0 | Done (2026-04-27) |
| [T-011](T-011-missing-tests-bundle.md) | Missing tests bundle (ReceiverTableFull + slot-reuse + ipc_send_and_yield + start_prelude + cap-table sweep) | B0 | Done (2026-04-27) |
| [T-012](T-012-exception-and-irq-infrastructure.md) | Exception infrastructure and interrupt delivery (GIC + IVT + timer-IRQ + idle-WFI) | B1 | Done (2026-04-28) |
| [T-013](T-013-el-drop-to-el1.md) | EL drop to EL1 in boot (boot.s asm extension + `current_el` HAL helper) | B1 | Done (2026-04-27) |
| [T-014](T-014-idle-dispatch-fallback.md) | Idle dispatch via separate fallback slot (closes B1 smoke regression; implements ADR-0026) | B1 | Done (2026-05-07) |
| [T-015](T-015-endpoint-rollback-cancel-recv.md) | Endpoint state rollback on `ipc_recv_and_yield` Deadlock + `ipc_cancel_recv` primitive (implements ADR-0032) | B2 prep | Done (2026-05-07) |
| [T-016](T-016-mmu-activation.md) | MMU activation with identity-mapped kernel + `MapperFlush` token discipline (implements ADR-0027) | B2 | Done (2026-05-08; B2 milestone Closed 2026-05-09) |
| [T-017](T-017-physical-memory-manager.md) | Physical Memory Manager (PMM): bitmap allocator + reservation tracking + `FrameProvider` impl (implements ADR-0035) | B3 | Done (2026-05-10) |
| [T-018](T-018-address-space-kernel-object.md) | `AddressSpace` kernel object + capability-gated `Mmu::map`/`unmap` wrappers + activation-on-context-switch (implements ADR-0028) | B3 | Done (2026-05-11; live on `main` 2026-05-14 via PR #28) |
| [T-019](T-019-task-loader.md) | Task loader: embedded raw-flat userspace image → `LoadedImage` metadata (implements ADR-0029) | B4 | Done (2026-05-16 via PR #31 merge) |
| [T-020](T-020-syscall-error-taxonomy.md) | Syscall error taxonomy: split `IpcError::InvalidCapability` + redact `Capability`/`CapObject` `Debug` (implements ADR-0030 K2-5 / K3-9) | B5 | Done (2026-05-29, PR #34) |
| [T-021](T-021-syscall-dispatch.md) | EL0→EL1 `SVC` dispatch: trap trampoline + panic-free dispatcher + copy-from/to-user (implements ADR-0030 / ADR-0031) | B5 | Done (2026-05-29, PR #34) |
| [T-022](T-022-high-half-kernel-mapping.md) | High-half kernel mapping: boot-time migration to `TTBR1_EL1` + per-task `TTBR0` swap | B6 — First userspace "hello" (this is B6's **gating prerequisite**: making the kernel reachable from every task's active translation so a real EL0 task's `SVC` vector fetch + the EL1 handler translate — the [ADR-0033](../../../decisions/0033-kernel-high-half-migration.md) high-half migration; per [phase-b §B6 opening sequence](../../../roadmap/phases/phase-b.md#b6-opening-sequence--prerequisites)) | Done (2026-05-30, PR #36) |
| [T-023](T-023-el0-entry-context.md) | EL0 entry context: userspace register file + enter-EL0/`ERET` path + per-task `SP_EL1` | B6 — First userspace "hello" (step 2 of the [B6 opening sequence](../../../roadmap/phases/phase-b.md#b6-opening-sequence--prerequisites); closes [T-021 carry-forward **gate #2**](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello)) | Done (2026-05-31, PR #37) |
| [T-024](T-024-task-create-from-image.md) | `task_create_from_image`: `LoadedImage` → runnable `CapObject::Task` capability | B6 — First userspace "hello" (step 3 of the [B6 opening sequence](../../../roadmap/phases/phase-b.md#b6-opening-sequence--prerequisites); the deferred [B4 §3](../../../roadmap/phases/phase-b.md#milestone-b4--task-loader) bridge) | Done (2026-05-31, PR #38) |
| [T-025](T-025-user-access-translation.md) | `Mmu::translate` + per-task user-access translation (B6 gate #1) | B6 — First userspace "hello" (step 4a of the [B6 dependency-ordered sequence](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello); closes the security-critical [T-021 carry-forward **gate #1**](../../../roadmap/phases/phase-b.md#t-021-carry-forward-gates-must-close-before-a-real-el0-task-runs)) | Done (2026-05-31, PR #39) |
| [T-026](T-026-current-task-cap-table.md) | current-task capability table + per-task window in `syscall_entry` (B6 gate #3) | B6 — First userspace "hello" (step 4b of the [B6 dependency-ordered sequence](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello); closes [T-021 carry-forward **gate #3**](../../../roadmap/phases/phase-b.md#t-021-carry-forward-gates-must-close-before-a-real-el0-task-runs)) | Done (2026-05-31, PR #40) |
| [T-027](T-027-userland-build-pipeline.md) | `userland/hello` + `tyrne-user` + the raw-flat build pipeline (B6 step 5) | B6 — First userspace "hello" (step 5 of the [B6 dependency-ordered sequence](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello) — `tyrne-user` crate + `userland/hello/` crate + the `cargo build → rust-objcopy -O binary → include_bytes!` pipeline + the shared base-VA source-of-truth) | Done (2026-06-01, PR #41) |
| [T-028](T-028-el0-userspace-wireup.md) | EL0 userspace wire-up + the `+0x400` round-trip smoke (B6 step 6) | B6 — First userspace "hello" (step 6 of the [B6 dependency-ordered sequence](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello) — a true EL0 task takes the lower-EL `VBAR_EL1+0x400` vector, the dispatcher copies `console_write` from its `TTBR0_EL1`, `ERET` returns to EL0, and `task_exit` terminates it — the EL0↔EL1 round-trip B5's `+0x200` proxy could not prove) | Done (2026-06-01, PR #42) |
| [T-029](T-029-perf-microbench.md) | feature-gated micro-bench (EL0 round-trip / IPC / context-switch) | B6 follow-on / Phase B closure tail — not gated on a numbered B-milestone | Done (2026-06-01, PR #44 / PR #45) |

Tasks are added here as they become active. See [`../../../roadmap/phases/phase-b.md`](../../../roadmap/phases/phase-b.md) for the full phase plan.
