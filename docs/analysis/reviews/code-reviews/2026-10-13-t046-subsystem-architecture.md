# Code review 2026-10-13 — T-046 subsystem architecture

- **Change:** `development`, cumulative `d71aa4a0ddcdbdca4089ba5ccd2d949ec4367e48..4b336072bd9c28d786e46cb9c205c6eac73a1f41`.
- **Reviewer:** Codex coordinator for @cemililik, consolidating two fresh code contexts and distinct subsequent security contexts.
- **Risk class:** Security-sensitive documentation; no executable change.
- **Security-review cross-reference:** [Both distinct full security rounds](../security-reviews/2026-10-13-t046-subsystem-architecture.md).
- **Contract:** [T-046](../../tasks/phase-b2/T-046-docs-subsystem-chapters-refresh.md), Step 3 of the [approved plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md).

## Review rounds and corrections

| Round | Fresh context / model / effort | Outcome |
|-------|--------------------------------|---------|
| 1 code | `b22_t046_r1_code`, GPT-6.1 Sol / high | Initial Request changes; all corrections verified and actual final security disposition read; final scoped Approve. |
| 1 security | `b22_t046_r1_security`, GPT-6 Astra / high | Initial Changes requested; final scoped Approve at `4b33607`, 24 OK / 9 N/A / zero flagged across 33 items. |
| 2 code | `b22_t046_r2_code`, GPT-6.1 Sol / high | Zero new findings; final Approve after actual distinct security report read. |
| 2 security | `b22_t046_r2_security`, GPT-6 Astra / high | Approve at `4b33607`, zero new findings; full checklist and principles below in the paired artifact. |

Each security pass began after its corresponding code assessment completed, with a fresh checklist and distinct context. Round 2 used different agents. The coordinator read all actual reports and bounded follow-ups; this canonical consolidation/tracking is bookkeeping, not another independent review.

| Unique R1 finding | Origin / severity | Source-backed correction in `4b33607` |
|-------------------|-------------------|--------------------------------------|
| C1 / S1: saved user SP | Shared / Medium | Syscall frame is 34 u64 values including SP_EL0, not padding; syscall.rs repr(C) and vectors.s save/restore agree. |
| C2 / S2: block errors | Shared / Medium | Real map returns AlreadyMapped into a block; unmap/translate return BlockMapped. Chapter/report corrected; old fake remains T-041-owned. |
| C3 / S3: idle IRQ state | Shared / Medium | WFI/yield body has no entry unmask; initial dispatch abandons an IrqGuard and context switch does not restore DAIF. Boot's earlier clear is not wake evidence. Both chapters/report corrected. |
| C4 / S4: capacity cost | Shared / Low | is_full checks free_head.is_none(), without scan or reservation. IPC/report/trade-off wording corrected. |
| C5 / S5: panic output | Shared / Low | Exception class/ESR/class-id or IRQ identifier is printed through BSP PanicInfo; no pre-handler saved-frame print. Both chapters/report corrected. |
| S6: PMM alignment boundary | Security-only / Low | PhysFrame construction enforces alignment; free-time checks cover extent, reservations and allocated bit. Chapter/report corrected. |

All six unique findings and duplicates are resolved. Original initial verdicts/origins remain recorded; Round 2 raises no additional finding and requires no empty fix commit.

## Correctness

Both final code passes approve seven complete refreshed chapters, their current/planned distinctions and shared overview/loader/index coherence. HAL signatures and privileged BSP ownership are real; no BootInfo/Timer::init/portable board selector is invented. Cooperative FIFO/current-slot binding, separate idle fallback, AS activation, resumed stack semantics, bridge Delivered/Enqueued/Pending/Deadlock behavior and non-reclaiming exit agree with bodies. Bare EL0 IPC remains distinct from EL1 scheduling bridges.

Five CapObject kinds/eight rights, copy peers/derive children, trusted new_object correlation, descendant-only local revoke, leaf movement, separate sender/receiver preflights and stale-generation housekeeping are accurately bounded. Boot/PMM/MMU/AS/loader sequencing, permissions, arithmetic, frame/trap layouts, effects, initial scrub, DAIF and timer order match implementations. Missing ongoing SIMD preservation, physical ownership, lifecycle, fault supervision and IRQ/idle proof are explicit existing scope, not silently delivered mechanisms.

## Style

English prose, descriptive links, small prose-led Mermaid diagrams, tagged fences and a source-derived PA/VMA table meet repository style. The old scheduler revision and T-019 banner are clearly historical. Conventional English docs commits carry relevant ADR references; no Rust style, dependency, binary or unsafe delta exists.

## Test coverage

Both code reviewers read existing cap/IPC/scheduler/syscall/user-access/MMU/timer/PMM/AS/loader boundary tests as contract context before source-body assessment. No new API/error/behavior is introduced; new runtime tests or repeated builds are unnecessary for these prose corrections and were not run.

The [verification report](../../reports/2026-10-13-t046-subsystem-architecture-verification.md) separates checked source `da18ed5` from retained runtime `4ad0b3d8a9d43310fcd937013131bffadcc803d7`. Reviewers independently matched all six log hashes and inspected both raw traces: EL0 PC 0x800000, two SVCs, exit/completion, debug-only greeting, no other recorded exception/fault. Manual counts are separate from smoke assertions; release rejection is source-derived. Executable/configuration paths remain unchanged. Evidence establishes neither idle/WFI wake, timer delivery, hostile loading, full trap SIMD isolation, complete reclamation, SMP nor global soundness.

## Documentation

Whole HAL/scheduler/security/IPC/boot/memory/exceptions claims were verified beyond the original stale sentences. Seven exact date/source/task markers and all nine previous edit SHAs/index cells were independently checked. Coverage differs from edit ownership; overview/loader remain T-045-owned, two planned chapters remain unwritten. The retained live memory/boot anchors resolve; overview's boot flow agrees with expanded boot, pre-dispatch table publication and final Task A spin. T-045's two shared criteria can now be checked. Its separate old master-plan navigation criterion remains T-049-owned.

The report preserves six corrected findings and existing runtime limits, without preclaiming whole-corpus grammar, new execution, task Done or phase closure. Relevant decisions/audit riders were checked for meaning; no new ADR or audit entry is required for factual corrections.

## Integration

The reviewed 13-file range fits seven chapters/index and approved task/tracking/evidence allowance. Bounded coordinator checks find 575 local paths and 34 fragments with no missing target; reviewer scans state their own different file/form scopes. Fences/stale tokens/freshness and diff-check pass. These do not replace T-056. No executable/configuration or retained-evidence delta exists.

At frozen tip T-046 is In Progress; canonical bookkeeping moves it only to In Review. No date_done, Phase C/D opening, PR49 barrier change or publication occurs. Remaining existing runtime work keeps its named T-038/T-040/T-041 and Phase C/D/E owners.

Explicit full code checklist: correctness, capability semantics, fault containment, unsafe discipline, error handling, tests/evidence, whole documentation, P1–P12, dependencies, naming/style and commit messages all considered and clear within this documentation scope. No new code/API/unsafe/dependency needs rustdoc/audit/test additions. Each final code approval consumes its actual paired security report.

## Verdict

**Approve — both fresh code rounds paired with both distinct security passes at `4b33607`.** Six R1 findings corrected and independently verified; R2 zero new findings. T-046 moves to In Review, T-045's shared overview/boot/index checks close, and the authorized sequence proceeds to T-048. This is not Done promotion, phase closure, full-corpus or runtime-security certification.
