# Architecture documentation

This folder describes **how Tyrne is designed and implemented**. Decisions explain the [why](../decisions/); these chapters explain structure, interactions and data flow. Read coverage and verification separately: an Accepted document can still contain historical or planned material.

## Status

Nine indexed chapters exist and are Accepted documents; two (`drivers.md`, `userspace.md`) are planned and unwritten. [T-045](../analysis/tasks/phase-b2/T-045-docs-overview-taskloader-arch-index.md) refreshed overview/loader; [T-046](../analysis/tasks/phase-b2/T-046-docs-subsystem-chapters-refresh.md) now reconciles all seven subsystem chapters against the live post-Phase-B source and the same retained debug/release traces. This records document coverage and source verification, not task Done promotion or proof of every stated invariant. Phase B.2 is active and Phase C remains gated; see [current focus](../roadmap/current.md).

## Index

The last column records **document editing**, while the middle column records **implementation described**. Previous edit commits were verified at T-045's source baseline and retained in its evidence metadata; the refresh owner is recorded separately below. Covering T-024 or T-028 does not imply those tasks edited the loader chapter.

| Document | Implementation coverage recorded | Status / document edit provenance |
|----------|----------------------------------|-----------------------------------|
| [`overview.md`](overview.md) | Through B6: trusted EL0 hello, syscall ABI, TTBR split; current/planned boundaries. | Accepted; T-045 refresh (previous edit `24530fb`); source/date marker in chapter. |
| [`security-model.md`](security-model.md) | Live v1 kinds/rights, trusted-loader and mapping boundaries, current fault/exit limits; planned defenses labelled. | Accepted; T-046 refresh (previous edit `afeed10`); source/date marker in chapter. |
| [`hal.md`](hal.md) | Six live traits, EL0 context entry, privileged QEMU implementations and empty IOMMU placeholder. | Accepted; T-046 refresh (previous edit `771ebd1`); source/date marker in chapter. |
| [`boot.md`](boot.md) | Reset, TTBR1 migration, PMM/loader, caller-table publication, real EL0 dispatch and completion spin. | Accepted; T-046 refresh (previous edit `dfba2b6`); source/date marker in chapter. |
| [`scheduler.md`](scheduler.md) | Cooperative FIFO, per-task AS/table/window registration, fallback idle, IPC bridges and non-reclaiming exit. | Accepted; T-046 refresh (previous edit `bbc42e8`); source/date marker in chapter. |
| [`ipc.md`](ipc.md) | Depth-one bare primitives, optional leaf transfer, bounded state/generation handling and separate EL1 bridges. | Accepted; T-046 refresh (previous edit `d20e6d0`); source/date marker in chapter. |
| [`exceptions.md`](exceptions.md) | Vectors/GIC/timer support, live EL0 +0x400 SVC/effects, explicit unexercised IRQ/idle and FP/SIMD limits. | Accepted; T-046 refresh (previous edit `806c966`); source/date marker in chapter. |
| [`memory-management.md`](memory-management.md) | Temporary identity then shared TTBR1/per-task TTBR0, PMM/AS/map/flush and trusted ownership/lifecycle limits. | Accepted; T-046 refresh (previous edit `3ecef5e`); source/date marker in chapter. |
| [`task-loader.md`](task-loader.md) | Loading (T-019), Task creation (T-024), context (T-023), build (T-027), scheduled EL0 (T-028). | Accepted; T-045 refresh (previous edit `f15ae9a`, pre-B6 preparation); source/date marker in chapter. |
| `drivers.md` | Planned userspace driver model, grants and IRQ interface. | Planned; no file or edit provenance. |
| `userspace.md` | Planned init, system services and service composition. | Planned; no file or edit provenance. |

T-046 rechecked all nine coverage/edit-provenance cells and the overview/boot summary against source; see its [verification report](../analysis/reports/2026-10-13-t046-subsystem-architecture-verification.md). The [T-045 report](../analysis/reports/2026-10-13-t045-architecture-verification.md) retains earlier document-edit provenance and the exact executable/runtime capture. Fresh markers identify source checked, not a later prose commit or maintainer acceptance.

## Reading order

Start with [`overview.md`](overview.md), then [`task-loader.md`](task-loader.md) for the first EL0 path. Follow other chapters for subsystem detail, checking current versus planned boundaries and the source markers. The current security boundary is also summarized in [SECURITY.md](../../SECURITY.md).

## Conventions

- Architectural diagrams use Mermaid, with explanatory prose before each (see [documentation style](../standards/documentation-style.md)).
- Every subsystem document begins with a substantive summary paragraph.
- Code snippets are illustrative pseudocode unless explicitly marked as real source.
- Claims resting on a decision link to its ADR; current implementation claims are checked against executable source and dated riders.
- **Freshness marker:** `> **Last verified against:** YYYY-MM-DD; source <full 40-character commit SHA>; owner <linked T-NNN>.` Use one line per chapter; it names the source baseline checked, not the later document-edit commit. T-045 applies it to overview/loader; T-046 applies it to the other seven chapters.
- Phase closure re-verifies chapters, markers and this index in the closure batch, per the [business review master plan](../analysis/reviews/business-reviews/master-plan.md#acceptance-criteria).
