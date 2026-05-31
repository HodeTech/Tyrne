# Architecture Decision Records

Every non-trivial architectural, security, or process decision in Tyrne is recorded here as an **ADR** (Architecture Decision Record) using a lightweight **MADR** (Markdown Architectural Decision Records) style.

## Why ADRs

- They preserve the **why**, not just the **what**. This is the information that decays fastest and is most expensive to re-derive years later.
- They make the evolution of the project readable: you can follow the numbered history and see how the design language developed, including the options that were rejected.
- They give future contributors (human or AI) a way to disagree with a decision by writing a new ADR that supersedes an old one, rather than silently changing code.

## Format

All ADRs live in this folder, named `NNNN-short-kebab-slug.md`, where `NNNN` is a zero-padded four-digit sequence number. Use [template.md](template.md) as the starting point for a new ADR.

Each ADR contains:

- **Title** (matches the filename, minus the number prefix).
- **Status** — `Proposed`, `Accepted`, `Deprecated`, or `Superseded by NNNN`.
- **Date** — ISO-8601.
- **Deciders** — who signed off.
- **Context** — the question the project was facing and the constraints that applied.
- **Decision drivers** — the forces that influenced the choice.
- **Considered options** — the alternatives examined.
- **Decision outcome** — the option chosen, with a short justification.
- **Consequences** — positive, negative, and neutral effects, with mitigations where relevant.
- **References** — prior art, literature, upstream discussions.

## Index

| # | Title | Status | Date |
|---|-------|--------|------|
| 0001 | [Capability-based microkernel architecture](0001-microkernel-architecture.md) | Accepted | 2026-04-20 |
| 0002 | [Rust as the implementation language](0002-implementation-language-rust.md) | Accepted | 2026-04-20 |
| 0003 | [Apache-2.0 license](0003-license-apache-2.md) | Accepted | 2026-04-20 |
| 0004 | [Target hardware platforms and tiers](0004-target-platforms.md) | Accepted | 2026-04-20 |
| 0005 | [English as the documentation and code language](0005-documentation-language-english.md) | Accepted | 2026-04-20 |
| 0006 | [Workspace layout and initial crate boundaries](0006-workspace-layout.md) | Accepted | 2026-04-20 |
| 0007 | [Console HAL trait signature](0007-console-trait.md) | Accepted | 2026-04-20 |
| 0008 | [Cpu HAL trait signature (v1, single-core scope)](0008-cpu-trait.md) | Accepted | 2026-04-20 |
| 0009 | [Mmu HAL trait signature (v1)](0009-mmu-trait.md) | Accepted | 2026-04-20 |
| 0010 | [Timer HAL trait signature (v1)](0010-timer-trait.md) | Accepted | 2026-04-20 |
| 0011 | [IrqController HAL trait signature (v1)](0011-irq-controller-trait.md) | Accepted | 2026-04-20 |
| 0012 | [Boot flow and memory layout for bsp-qemu-virt](0012-boot-flow-qemu-virt.md) | Accepted | 2026-04-20 |
| 0013 | [Roadmap and planning process](0013-roadmap-and-planning.md) | Accepted | 2026-04-20 |
| 0014 | [Capability representation](0014-capability-representation.md) | Accepted | 2026-04-20 |
| 0015 | [AI integration stance: userspace-only, kernel-neutral](0015-ai-integration-stance.md) | Accepted | 2026-04-20 |
| 0016 | [Kernel object storage](0016-kernel-object-storage.md) | Accepted | 2026-04-21 |
| 0017 | [IPC primitive set](0017-ipc-primitive-set.md) | Accepted | 2026-04-21 |
| 0018 | [Badge scheme and `reply_recv` fastpath: formal deferral](0018-badge-scheme-and-reply-recv-deferral.md) | Accepted | 2026-04-21 |
| 0019 | [Scheduler shape](0019-scheduler-shape.md) | Accepted | 2026-04-21 |
| 0020 | [`ContextSwitch` trait and `Cpu` v2](0020-cpu-trait-v2-context-switch.md) | Accepted | 2026-04-21 |
| 0021 | [Raw-pointer scheduler IPC-bridge API](0021-raw-pointer-scheduler-ipc-bridge.md) | Accepted | 2026-04-22 |
| 0022 | [Idle task and typed scheduler deadlock error](0022-idle-task-and-typed-scheduler-deadlock.md) | Superseded by 0026 (idle-task-location axis only; typed-error axis stands) | 2026-04-22 |
| 0023 | [Cross-table capability revocation policy](0023-cross-table-capability-revocation-policy.md) | Deferred | 2026-04-27 |
| 0024 | [EL drop to EL1 policy](0024-el-drop-policy.md) | Accepted | 2026-04-27 |
| 0025 | [ADR governance amendments: forward-reference contract, rider hygiene](0025-adr-governance-amendments.md) | Accepted | 2026-04-27 |
| 0026 | [Idle dispatch via separate fallback slot](0026-idle-dispatch-fallback.md) | Accepted | 2026-05-06 |
| 0027 | [Kernel virtual memory layout (B2 — identity-mapped MMU activation)](0027-kernel-virtual-memory-layout.md) | Accepted | 2026-05-08 |
| 0028 | [Address-space data structure (B3 — kernel-object + capability-gated `Mmu::map` wrappers + activation-on-context-switch)](0028-address-space-data-structure.md) | Accepted | 2026-05-11 |
| 0029 | [Initial userspace image format (B4 — raw flat binary)](0029-initial-userspace-image-format.md) | Accepted | 2026-05-14 |
| 0030 | [Syscall ABI and userspace error taxonomy (B5)](0030-syscall-abi.md) | Accepted | 2026-05-29 |
| 0031 | [Initial syscall set (B5 — `send`/`recv`/`console_write`/`task_yield`/`task_exit`)](0031-initial-syscall-set.md) | Accepted | 2026-05-29 |
| 0032 | [Endpoint state rollback on `ipc_recv_and_yield` Deadlock + `ipc_cancel_recv` primitive](0032-endpoint-rollback-and-cancel-recv.md) | Accepted | 2026-05-07 |
| 0033 | [Kernel high-half migration (B6 — kernel → `TTBR1_EL1`, boot-time)](0033-kernel-high-half-migration.md) | Accepted | 2026-05-30 |
| 0035 | [Physical Memory Manager (B3 prerequisite — bitmap allocator)](0035-physical-memory-manager.md) | Accepted | 2026-05-09 |
| 0036 | [QEMU virt is GICv2 / no-IOMMU in v1; corrects GICv3/SMMUv3 in ADR-0004/0006/0012](0036-qemu-virt-gicv2-no-iommu-v1.md) | Accepted | 2026-05-22 |
| 0037 | [EL0 entry context (B6 — userspace register file + enter-EL0/`ERET` path + per-task `SP_EL1`)](0037-el0-entry-context.md) | Accepted | 2026-05-31 |
| 0038 | [`Mmu::translate` read-only walk + per-task user-access translation (B6 gate #1)](0038-mmu-translate-and-user-access.md) | Accepted | 2026-05-31 |
| 0039 | [Userland build pipeline (B6 — `userland/hello` + `tyrne-user` + raw-flat embed orchestration)](0039-userland-build-pipeline.md) | Accepted | 2026-05-31 |

> **Numbering gaps.** Slot **0034** is intentionally reserved, not missing: 0034 (kernel-image section permissions) is a named-but-unallocated placeholder forward-flagged in ADR-0027. No file exists for it yet; it opens when the corresponding work surfaces (the first attacker-observable EL0 execution — likely B6). (Slot **0033** (high-half migration) was filed `Proposed` on 2026-05-29 to open B6 and `Accepted` on 2026-05-30, and is no longer a gap; slots **0030**/**0031** were filed and `Accepted` on 2026-05-29 for B5.) ADR numbers are stable history and are never renumbered.

## Creating a new ADR

The authoritative, step-by-step procedure is the [`write-adr` skill](../../.agents/skills/write-adr/SKILL.md) (and [`supersede-adr`](../../.agents/skills/supersede-adr/SKILL.md) when overriding an old ADR). Read it in full before drafting; the summary below is a reminder, not a substitute.

1. Copy [template.md](template.md) to the next available number: `NNNN-your-slug.md`.
2. Fill it in. Start with status `Proposed`.
3. For an ADR whose subject is a multi-step state machine (capability flows, IPC handshakes, scheduler dispatch, exception/IRQ entry, MMU/TLB transitions, syscall ABI handshakes), include a **§Simulation** table (3–5 rows walking the worst-case interaction) per [ADR-0025](0025-adr-governance-amendments.md) and the `write-adr` skill; other ADR subjects use the one-line "Not applicable" note. Every ADR's §Decision outcome must also include a **§Dependency chain** grounding each forward-reference in a real `T-NNN` (per ADR-0025 §Rule 1).
4. Open a PR (once the PR process is established) or, in the solo phase, commit directly with a descriptive commit message referencing the ADR number.
5. When the decision is settled, re-read end-to-end (per `write-adr` skill §10) and change the status to `Accepted` in a separate commit from the initial `Proposed` draft.
6. If a later ADR overrides this one, mark the old one `Superseded by NNNN` and link forward to the new record. Do **not** delete or rewrite the old ADR — the historical reasoning is the point.
