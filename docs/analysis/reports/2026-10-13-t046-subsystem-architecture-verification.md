# T-046 — Subsystem architecture verification

- **Date:** 2026-10-13, Europe/Istanbul.
- **Owner:** [T-046](../tasks/phase-b2/T-046-docs-subsystem-chapters-refresh.md), approved Step 3 under [ADR-0043](../../decisions/0043-documentation-corpus-consistency.md).
- **Source baseline checked:** `da18ed5c2a2d8b3d61f82337a9da021d05d73451` on development, after T-045's canonical review publication.
- **Exact runtime capture:** `4ad0b3d8a9d43310fcd937013131bffadcc803d7`, [T-045 report](2026-10-13-t045-architecture-verification.md) and [metadata](2026-10-13-t045-architecture-evidence/metadata.json). All executable paths remain identical; this step reuses retained evidence and claims no repeated build, smoke, host test, coverage or Miri run.

## Whole-chapter reconciliation

Each chapter's summary, context, design, invariant, trade-off, open-question and reference claims were checked, including those beyond the original named drift. Source bodies and dated decision/audit riders take precedence over stale adjacent code comments. Existing relevant boundary tests were read as contract context, not reported as newly passing.

| Chapter | Load-bearing source and corrections |
|---------|------------------------------------|
| [HAL](../../architecture/hal.md) | Actual Cpu/ContextSwitch/Mmu/IRQ/Timer/Console signatures, empty Iommu; privileged QEMU implementations, FrameProvider callbacks, round-up deadlines, live EL0 initial scrub versus incomplete trap SIMD preservation. Remove invented BootInfo/Timer::init/build packages and unimplemented hardware claims. |
| [Scheduler](../../architecture/scheduler.md) | Per-slot AS/table/window arrays and current accessors; trusted registration without Task-generation/table-identity check, activation hook, separate idle fallback without an entry unmask, inherited dispatch-mask limitation, resume semantics, bridge receive rollback and non-reclaiming exit. Preserve the 2026-05-06 paragraph as explicitly historical rather than a current staleness verdict. |
| [IPC](../../architecture/ipc.md) | Message words, four endpoint states, generation-reset housekeeping/debug assertion versus release discard, leaf transfer/source and free-list-head receive-capacity stages, new receiver root and cross-table revocation limit. Bare EL0 calls differ from EL1 Delivered wake/yield and Pending block/resume. No current Miri count or line-count claim. |
| [Security model](../../architecture/security-model.md) | Five CapObject kinds/eight named rights; copy peers versus derive children, trusted arbitrary new_object correlation, descendant-only revoke and leaf drop/take. Actual PanicInfo-based fault diagnostics/exit leaks, PMM/arena/table bounds, no current badge/supervisor/IOMMU/secure-boot/crypto assurance. Future authority comes from the existing roadmap and deferred ADR-0023. |
| [Boot](../../architecture/boot.md) | boot.s, linker.ld and main's low/high/setup/registration bodies. DAIF-first EL drop, stack/FP-SIMD/BSS, vectors twice, six table frames inside BSS, PMM after TTBR0-off, matching raw image, caller tables before add_user/start, real hello interleaved with EL1 demo, Task A final spin. PA/VMA table avoids invented fixed section ends. |
| [Memory](../../architecture/memory-management.md) | Temporary identity → high-half/per-task roots, actual TCR/MAIR/AP/PXN/UXN/nG, AlreadyMapped for map into a block, BlockMapped for unmap/translate, no automatic split, must-use limits, PMM high-pointer helpers/type-enforced frame alignment versus free-time extent/reservation/allocation checks, AS preflight/child derivation, kind-only map/unmap and lifecycle leaks. Retain T-019's removed banner solely as dated historical evidence. |
| [Exceptions](../../architecture/exceptions.md) | Actual vector targets, 192-byte IRQ frame and 272-byte syscall frame (including SP_EL0, no padding), absent SIMD save, complete binding, debug decode order, Resume/Reschedule/Terminate distinction, timer ceil conversion/mask/EOI, no scheduler IRQ mutation. Installed delivery/idle paths are not asserted exercised. |

## Shared T-045 checks

The overview's reset/MMU/high-half/PMM/load/GIC/table/register/EL0/completion sequence agrees with the expanded boot sequence, including table publication before dispatch and EL1/EL0 interleaving. Both name Task A's final busy-spin. No overview correction is needed. Its ADR and current/planned limits agree with all seven refreshed chapters.

Every architecture-index cell was rechecked. Nine existing Accepted documents remain distinct from two unwritten planned chapters. Overview/loader retain T-045 edit ownership and source `4ad0b3d`; the seven refreshed chapters name T-046 and exact checked source `da18ed5`. Earlier nine edit SHAs remain the independently verified T-045 metadata records. Implementation coverage does not imply that a historically covered task edited a document.

Incoming live anchors `memory-management.md#frame-allocation-discipline` and `boot.md#high-half-migration-t-022--adr-0033` are preserved. Old review `#L...` links and retired skill provenance remain T-049-owned archive work, without silently treating them as valid heading links. T-045's shared criteria can be checked only after T-046's two fresh rounds complete; its old master-plan navigation criterion remains pending T-049 repair.

## Evidence and limits

Both retained profiles reach EL0 PC `0x800000`, exit and completion; debug alone emits the greeting. Each raw trace contains exactly two SVC events and no other exception events/fault matches. Counts are manual inspection, not smoke.sh assertions. The captured runtime neither arms timer IRQs nor selects idle/WFI; it cannot prove arbitrary loader safety, complete destruction/reclamation, full FP/SIMD trap isolation, preemption/SMP or kernel-wide soundness. Release syscall rejection follows the source decoder, not a printed status value.

This prose refresh changes no Rust/assembly, ABI, unsafe contract, dependency, CI identity, architectural decision or raw evidence. No new ADR is needed for the maintainer-approved correction of actual current behavior. Fresh independent code and subsequent distinct security rounds remain required and will be recorded separately after the implementation commit. This report does not preclaim their verdict, task Done promotion, phase closure or whole-corpus cleanliness.

## Implementation checks

Coordinator checks passed: `git diff --check`; the bounded inline-path scan over eight chapter/index files plus this report, including code-formatted labels (280 local paths, zero missing); a separate bounded check of ten current chapter heading links, seven exact freshness lines, balanced tagged fences and all four task-specific stale-token checks. These scratch checks cover the stated files/forms and do not replace T-056's later full-corpus grammar gate. A read-only comparison of kernel/HAL/BSP/userland/test-hal/tools/Cargo/config/CI/toolchain paths confirms no delta from the exact runtime capture. The old business-master-plan link is unchanged and remains T-049-owned.

## First-round corrections

Fresh code context `b22_t046_r1_code` completed at `5e191ad`; the distinct subsequent security context `b22_t046_r1_security` completed its own source assessment before reading the code report. Their initial verdicts requested three Medium and three Low unique factual corrections. The coordinator independently verified each against source and corrected all occurrences:

| Finding / origin | Correction |
|------------------|------------|
| C1 / S1, shared Medium | The 272-byte syscall frame includes SP_EL0; all 34 u64 slots are saved values, with no padding. |
| C2 / S2, shared Medium | Map into a block returns AlreadyMapped; unmap/translate return BlockMapped. Corrected the chapter/report duplicate; T-041 still owns its older fake. |
| C3 / S3, shared Medium | Idle performs WFI/yield without an explicit IRQ unmask. Initial dispatch holds a guard on an abandoned caller frame; boot's earlier unmask does not establish an unmasked idle entry. Actual mask/delivery evidence remains required. |
| C4 / S4, shared Low | Receive capacity checks the free-list head, without a table scan or slot reservation. |
| C5 / S5, shared Low | Exception messages carry class/ESR/class-id or IRQ identifier through the BSP's PanicInfo output; no prior saved-frame print/dump exists. Corrected boot/security wording. |
| S6, security-only Low | PhysFrame construction supplies alignment; free-time checks cover extent, reservations and allocation state. |

No runtime change, new decision or new test execution is involved. Bounded correction verification by the first-round reviewers and the two fresh second-round contexts are still pending at this correction record; no final approval is preclaimed.
