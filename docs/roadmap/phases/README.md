# Phase plan

Ten phases plus a short consolidation bridge ([Phase B.2](phase-b2.md)), in rough execution order. Each phase is a separate file so detail can grow without any single document becoming unnavigable.

The plan is a **sequence**, not a schedule: there are no dates. Later phases are sketched at lower resolution than earlier ones; detail appears as its turn approaches. The *why* behind the whole system lives in [ADR-0013](../../decisions/0013-roadmap-and-planning.md).

## Phase index

| Phase | Title | Detail level | Exit bar |
|-------|-------|--------------|----------|
| [A](phase-a.md) | Kernel core on QEMU `virt` | Detailed | Two kernel tasks exchange IPC messages under capability control on QEMU. |
| [B](phase-b.md) | Real userspace | Detailed | A userspace task runs in its own address space and makes syscalls. |
| [B.2](phase-b2.md) | Consolidation & hardening (bridge) | Detailed | CI enforces every claimed gate; docs reflect Phase B's closure; the review-surfaced correctness/robustness/quality defects are fixed. **Mandatory gate before Phase C** (and D), per [ADR-0040](../../decisions/0040-phase-b2-consolidation-bridge.md); Phase B.2 is the active phase. |
| [C](phase-c.md) | Multi-core | Detailed | Preemptive scheduler across two or more cores with working cross-core IPC. |
| [D](phase-d.md) | Raspberry Pi 4 (first real hardware) | Detailed | `bsp-pi4` boots on a real Pi 4 at feature parity with QEMU virt. |
| [E](phase-e.md) | Driver model and essential services | Medium | Userspace drivers + log + storage + filesystem + network services composed. |
| [F](phase-f.md) | Smart-home deployment | Medium | A real Tyrne-firmware device running in the maintainer's smart home. |
| [G](phase-g.md) | Security maturation | Medium | Measured boot, cryptography primitives, TLS, first formal-verification pilot. |
| [H](phase-h.md) | Platform expansion | Light | `bsp-pi5`, `bsp-jetson` (CPU-only), first RISC-V BSP. |
| [I](phase-i.md) | Mobile | Light | First prototype boot on phone-class hardware. |
| [J](phase-j.md) | AI-native userspace layer (opt-in) | Sketch | Optional AI-integrated features running entirely in userspace above the kernel's trust boundary. Per [ADR-0015](../../decisions/0015-ai-integration-stance.md). |

**Where we are (2026-10-15):** Phase A and Phase B are closed; [Phase B.2](phase-b2.md) is active under [ADR-0040](../../decisions/0040-phase-b2-consolidation-bridge.md). Track B.2-1/T-030–T-037 is Done after [PR #48](https://github.com/HodeTech/Tyrne/pull/48), maintainer authorization and verified first-main gates. Track B.2-2/T-045–T-056 is implemented/In Review; [integrated verification](../../analysis/reports/2026-10-15-phase-b2-track2-completion-readiness.md) and both fresh rounds are complete; final publication-tip CI is recorded before maintainer review in combined [PR #49](https://github.com/HodeTech/Tyrne/pull/49). Of 46 tasks, 8 are Done, 12 In Review and 26 unimplemented (19 Ready/7 Draft). HIGH T-038 is Ready/unstarted and next. Phase C/D remain gated by whole B.2 exit; [current.md](../current.md) is the live pointer.

## Dependency sketch

```mermaid
flowchart LR
    A[Phase A<br/>kernel core] --> B[Phase B<br/>real userspace]
    B --> B2[Phase B.2<br/>consolidation & hardening]
    B2 --> C[Phase C<br/>multi-core]
    B2 --> D[Phase D<br/>Pi 4]
    D --> E[Phase E<br/>drivers + services]
    E --> F[Phase F<br/>smart home]
    E --> G[Phase G<br/>security maturation]
    D --> H[Phase H<br/>platforms]
    F --> I[Phase I<br/>mobile]
    G --> I
    G -. opt-in .-> J[Phase J<br/>AI-native userspace]
    E -. opt-in .-> J
    H --> I
```

The edges `B2 --> C` and `B2 --> D` are **binding gates** ([ADR-0040](../../decisions/0040-phase-b2-consolidation-bridge.md)): no Phase C or Phase D milestone opens and no Phase C or Phase D implementation task leaves `Draft` while Phase B.2 is open.

After the whole B.2 exit bar is met, Phases C and D may overlap; D does not wait for C to finish. Pi 4 directly depends on the corrected shared kernel/HAL, MMU and syscall foundations, as ADR-0040 specifies. This is why the sketch draws both binding edges from B.2 and no finish-before-start edge from C to D.

## Why split by file

A single `phases.md` with full detail for ten phases and a bridge would run well over a thousand lines. Splitting lets:

- Each phase accumulate detail as its turn approaches without bloating the others.
- Diffs that touch one phase not noise-pollute PRs that touch another.
- The plan index stay one page long.

Detail grows as the phase approaches its turn: the active phase and the next few carry the most detail; later phases are sketches.

## Living-document note

Commits that touch phase files describe what changed — a milestone added, a task reordered, a sub-breakdown expanded — with a brief rationale. Structural changes (adding or dropping a phase) require an ADR per [ADR-0013](../../decisions/0013-roadmap-and-planning.md).
