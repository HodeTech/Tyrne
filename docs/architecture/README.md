# Architecture documentation

This folder describes **how Tyrne is designed and implemented**. Decisions explain the [why](../decisions/); these chapters explain structure, interactions and data flow. Read coverage and verification separately: an Accepted document can still contain historical or planned material.

## Status

Nine indexed chapters exist and are Accepted documents; two (`drivers.md`, `userspace.md`) are planned and unwritten. [T-045](../analysis/tasks/phase-b2/T-045-docs-overview-taskloader-arch-index.md) refreshes the overview and loader against the post-Phase-B source. The seven subsystem chapters await the whole-chapter [T-046](../analysis/tasks/phase-b2/T-046-docs-subsystem-chapters-refresh.md) sweep. Their coverage entries below describe identifiable content, **not** a fresh certification of each chapter's claims. Phase B.2 is active and Phase C remains gated; see [current focus](../roadmap/current.md).

## Index

The last column records **document editing**, while the middle column records **implementation described**. At T-045's source baseline, `git log -1 -- <file>` yielded the previous edit commits shown below. Covering T-024 or T-028 does not imply those tasks edited the loader chapter.

| Document | Implementation coverage recorded | Status / document edit provenance |
|----------|----------------------------------|-----------------------------------|
| [`overview.md`](overview.md) | Through B6: trusted EL0 hello, syscall ABI, TTBR split; current/planned boundaries. | Accepted; T-045 refresh (previous edit `24530fb`); source/date marker in chapter. |
| [`security-model.md`](security-model.md) | Capability/trust design and ADR-0036 SMMUv3 policy; current-boundary sweep pending T-046. | Accepted; last edit `afeed10`; verification refresh pending T-046. |
| [`hal.md`](hal.md) | HAL/BSP design, Cpu/ContextSwitch and EL0-context additions; whole surface sweep pending T-046. | Accepted; last edit `771ebd1` (T-023 follow-up); verification refresh pending T-046. |
| [`boot.md`](boot.md) | Reset/EL drop and T-022 high-half migration; stale loader/steady-state passages await T-046. | Accepted; last edit `dfba2b6` (T-022 follow-up); verification refresh pending T-046. |
| [`scheduler.md`](scheduler.md) | Cooperative FIFO, IPC bridge, address-space activation, T-023 EL0-context mechanism. | Accepted; last edit `bbc42e8` (T-023); verification refresh pending T-046. |
| [`ipc.md`](ipc.md) | Depth-one endpoints, notifications, transfer, bridge and typed IPC errors; EL0 distinction awaits T-046. | Accepted; last edit `d20e6d0`; verification refresh pending T-046. |
| [`exceptions.md`](exceptions.md) | Vector/GICv2/timer infrastructure and T-021 SVC dispatch; live B6 path sweep pending T-046. | Accepted; last edit `806c966` (T-021); verification refresh pending T-046. |
| [`memory-management.md`](memory-management.md) | Bootstrap MMU, PMM, AS/loader and high-half additions; stale post-B6 claims await T-046. | Accepted; last edit `3ecef5e` (T-022 follow-up); verification refresh pending T-046. |
| [`task-loader.md`](task-loader.md) | Loading (T-019), Task creation (T-024), context (T-023), build (T-027), scheduled EL0 (T-028). | Accepted; T-045 refresh (previous edit `f15ae9a`, pre-B6 preparation); source/date marker in chapter. |
| `drivers.md` | Planned userspace driver model, grants and IRQ interface. | Planned; no file or edit provenance. |
| `userspace.md` | Planned init, system services and service composition. | Planned; no file or edit provenance. |

T-046 must recheck every cell and the overview boot summary after refreshing its seven chapters. The [T-045 verification report](../analysis/reports/2026-10-13-t045-architecture-verification.md) retains edit provenance and source/runtime evidence for this pass.

## Reading order

Start with [`overview.md`](overview.md), then [`task-loader.md`](task-loader.md) for the first EL0 path. Follow other chapters for subsystem detail, checking the coverage/status above until T-046 completes its sweep. The current security boundary is also summarized in [SECURITY.md](../../SECURITY.md).

## Conventions

- Architectural diagrams use Mermaid, with explanatory prose before each (see [documentation style](../standards/documentation-style.md)).
- Every subsystem document begins with a substantive summary paragraph.
- Code snippets are illustrative pseudocode unless explicitly marked as real source.
- Claims resting on a decision link to its ADR; current implementation claims are checked against executable source and dated riders.
- **Freshness marker:** `> **Last verified against:** YYYY-MM-DD; source <full 40-character commit SHA>; owner <linked T-NNN>.` Use one line per chapter; it names the source baseline checked, not the later document-edit commit. T-045 applies it to overview/loader; T-046 applies it to the other seven chapters.
- Phase closure re-verifies chapters, markers and this index in the closure batch, per the [business review master plan](../analysis/reviews/business-reviews/master-plan.md#acceptance-criteria).
