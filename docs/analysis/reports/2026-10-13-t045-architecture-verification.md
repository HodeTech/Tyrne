# T-045 — Architecture source and runtime verification

This report binds the overview/loader refresh to executable source, retained matching-profile QEMU runs and document-edit provenance. It records bounded implementation evidence, not a phase-closure or task-Done verdict.

- **Date:** 2026-10-13 (Europe/Istanbul; runtime capture began 2026-10-12 UTC).
- **Owner:** [T-045](../tasks/phase-b2/T-045-docs-overview-taskloader-arch-index.md), Step 2 of the [approved plan](2026-10-12-phase-b2-track2-preflight-and-plan.md).
- **Exact runtime/source revision:** `4ad0b3d8a9d43310fcd937013131bffadcc803d7`, `development`; tracked tree clean before capture.
- **Environment:** Darwin arm64; pinned `nightly-2026-01-15`, rustc `1.94.0-nightly (86a49fd71 2026-01-14)`, LLVM 21.1.8; QEMU 11.1.1. Complete toolchain/version text and SHA-256 manifests are retained in [metadata.json](2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t045-architecture-evidence "Archived member: docs/analysis/reports/2026-10-13-t045-architecture-evidence/metadata.json").
- **Scope:** overview, loader, architecture index, phase-closure architecture checklist hook, task/tracking and source-bound evidence. No Rust, assembly, dependency, toolchain or CI change.

## Runtime capture

Executed sequentially before prose edits so the shared `hello.bin` always matched the kernel profile:

```sh
tools/smoke.sh --int
tools/smoke.sh --release --int
```

Both commands exited **0**. They built userland before the matching BSP, then ran QEMU `virt`, `cortex-a72`, 128 MiB, one core, serial stdio without monitor, with **`-d int,unimp`** and the script's default 20-second budget. `guest_errors` was not enabled. After completion/elapsed output, Task A busy-spins without yielding until the expected timeout/SIGTERM ends QEMU; the script decides success from its marker and fault gates, not QEMU's process exit status. These runs exercise neither idle/WFI nor timer IRQ delivery; the default demo arms no deadline.

| Profile | Image size | Image SHA-256 | Script result |
|---------|------------|---------------|---------------|
| debug | 117 bytes | `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88` | PASS: exit/completion plus required greeting, no panic/fault match. |
| release | 69 bytes | `ade8d1695182284e1efba2436c5ead8e4db6dac816f61852d436fc3d300362df` | PASS: exit/completion, greeting forbidden, no panic/fault match. |

Raw QEMU traces: [debug](2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t045-architecture-evidence "Archived member: docs/analysis/reports/2026-10-13-t045-architecture-evidence/debug.qemu.log"), [release](2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t045-architecture-evidence "Archived member: docs/analysis/reports/2026-10-13-t045-architecture-evidence/release.qemu.log"). Complete command output: [debug stdout](2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t045-architecture-evidence "Archived member: docs/analysis/reports/2026-10-13-t045-architecture-evidence/debug.stdout.log") / [stderr](2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t045-architecture-evidence "Archived member: docs/analysis/reports/2026-10-13-t045-architecture-evidence/debug.stderr.log"), [release stdout](2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t045-architecture-evidence "Archived member: docs/analysis/reports/2026-10-13-t045-architecture-evidence/release.stdout.log") / [stderr](2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t045-architecture-evidence "Archived member: docs/analysis/reports/2026-10-13-t045-architecture-evidence/release.stderr.log"). Metadata includes original PID-log paths, ELF/image sizes and hashes, capture times, flags and all retained-log hashes. Binary artifacts are regenerated and not committed.

The root separately read both raw traces. Each has **two `Taking exception 2 [SVC]` events**, zero other `Taking exception` events and zero Translation/Permission fault, Data/Prefetch Abort, Undefined Instruction or panic matches. Each enters EL0 at PC `0x800000`, reaches `tyrne: userspace task exited` and `tyrne: all tasks complete`; only debug contains `hello from userspace`. These are **manual evidence counts**, not an assertion that `smoke.sh` enforces an exact SVC count. The console attempt still traps in release; ABI decoding rejects its number before output, then `hello` exits. That rejection's status follows source inspection, not an independently printed trace value.

The traces' elapsed values (debug 5,106,000 ns; release 3,501,008 ns), reserved-frame counts and addresses describe these particular runs. They are not new performance baselines or stable ABI values. Absence of observed faults in these demonstrations does not establish arbitrary fault containment or global memory safety.

## Source reconciliation

| Claim area | Source inspected | Result reflected in chapters |
|------------|------------------|------------------------------|
| Boot and ownership | [`boot.s`](../../../bsp-qemu-virt/src/boot.s), [`main.rs`](../../../bsp-qemu-virt/src/main.rs), [`Cargo.toml`](../../../kernel/Cargo.toml) | Mask/drop/stack/BSS before Rust; low bootstrap → high-half transition → PMM/AS/load → GIC/timer → scheduling. BSP owns wiring and privileged board drivers; only QEMU BSP exists. |
| EL0 context and binding | [`sched/mod.rs`](../../../kernel/src/sched/mod.rs), [`cpu.rs`](../../../bsp-qemu-virt/src/cpu.rs), [`syscall.rs`](../../../bsp-qemu-virt/src/syscall.rs) | Task identity is separate from scheduler context; per-task kernel stack and TTBR0 activation are live. BSP reads registered table/window bindings by current scheduler slot and generation-resolves the AS; incomplete binding fails closed. No separate current-Task generation or table-pointer identity validation is claimed. |
| Syscalls | [`abi.rs`](../../../kernel/src/syscall/abi.rs), [`dispatch.rs`](../../../kernel/src/syscall/dispatch.rs), [`user_access.rs`](../../../kernel/src/syscall/user_access.rs) | Numbers 1–5; number 5 debug-gated; yield/exit act only on current caller without a capability argument. USER checks and range checks precede buffer output. |
| IPC | [`ipc/mod.rs`](../../../kernel/src/ipc/mod.rs), scheduler bridge, dispatcher | Bare send/recv return outcomes; EL1 bridge adds cooperative block/unblock/yield. EL0 uses bare primitives, not blocking wrappers. Send checks source authority/endpoint capacity before movement into the endpoint; receive checks table capacity before installation and preserves pending authority on a full table. Notifications have no v1 syscall. |
| Capability and memory limits | [`cap/mod.rs`](../../../kernel/src/cap/mod.rs), [`address_space.rs`](../../../kernel/src/mm/address_space.rs), [`mmu.rs`](../../../bsp-qemu-virt/src/mmu.rs) | Capability is move-only; memory mapping helpers are kind-checked trusted APIs without full per-operation rights/physical-ownership checks. ASID 0 with flush on root swap; shared privileged TTBR1. |
| Loader validation and cleanup | [`task_loader.rs`](../../../kernel/src/obj/task_loader.rs), [`pmm.rs`](../../../kernel/src/mm/pmm.rs) | VA check before budget; equality at one-past limit valid; zero base legal. Seven intermediates for 8 MiB image + one-page stack. High VA converted to PA for overlap. Leaves/cap cleaned; root/intermediate/AS slot not reclaimed. |
| Image/build and faults | [`hello`](../../../userland/hello/src/main.rs), [`hello.ld`](../../../userland/hello/hello.ld), [`build-userland.sh`](../../../tools/build-userland.sh), BSP handlers | Real raw-flat Rust image replaces historical 8-byte sample; no current image-loaded banner. RX image/RW-NX stack do not imply kernel W^X or ROP prevention. Non-SVC EL0 synchronous fault panics the kernel; exit is not complete resource reclamation. |

The old speculative syscall enumeration was **removed**, rather than retained as an alternative ABI. Planned services and memory/IRQ authority are explicitly labeled. ADR-0037 governs EL0 entry; ADR-0038 governs user-access translation; ADR-0039 governs building the image. Reserved ADR-0034 is linked through the ADR index because no numbered file exists yet, and concerns kernel section permissions, not userspace section metadata.

The loader test surface contains **42 `#[test]` functions** at the exact baseline. This inventory was checked against source; no fresh host suite, Miri or coverage run is claimed for this prose-only change. Those executions belong to their later evidence-owning steps where required.

## Provenance and freshness

The [architecture index](../../architecture/README.md) defines a single-line marker with date, full source SHA and linked task owner. It identifies the code baseline inspected, not the later documentation commit. Overview and loader use the exact runtime/source baseline above. The index distinguishes chapter coverage from last editing provenance; the full previous edit SHAs/messages from `git log -1 -- <file>` are retained in metadata.

| Chapter | Previous document edit | Verification scope now |
|---------|------------------------|------------------------|
| overview | `24530fb` | Whole chapter, T-045. |
| task-loader | `f15ae9a` (pre-B6 preparation) | Whole chapter, T-045; covers T-024/T-028 without attributing old edits to them. |
| hal | `771ebd1` | Content/provenance surveyed for index; full refresh T-046. |
| scheduler | `bbc42e8` | Content/provenance surveyed for index; full refresh T-046. |
| exceptions | `806c966` | Content/provenance surveyed for index; full refresh T-046. |
| security-model | `afeed10` | Content/provenance surveyed for index; full refresh T-046. |
| memory-management | `3ecef5e` | Content/provenance surveyed for index; full refresh T-046. |
| boot | `dfba2b6` | Current common reset/MMU/high-half prefix checked; stale loader/steady-state detail explicitly owned by T-046. |
| ipc | `d20e6d0` | Content/provenance surveyed for index; full refresh T-046. |

The overview's boot summary follows executable source. Its shared reset, EL drop, bootstrap and high-half stages agree with the existing boot chapter; that chapter's obsolete non-running blob/banner and incomplete scheduler ending are corrected by the immediately following T-046 step. No old boot sequence is copied as current truth. T-046 must recheck the overview, detailed boot sequence and all index cells together before finishing; this is an approved sequencing dependency, not unowned deferral. The new phase-closure master-plan hook requires the same chapter/marker/index verification in every closure batch.

## Verification boundaries

The root checked simple local targets and relevant Markdown fragments, tagged Mermaid fences, exact source references, retained-log hashes, old/new claims and step scope before the implementation commit. Full-corpus grammar enforcement is T-056's later deliverable. Two fresh code/document rounds, each followed by a distinct security pass, are recorded separately after the implementation commit; this report does not pre-claim their verdicts. Maintainer Done promotion remains pending PR review/merge.

> **Evidence migration (2026-10-16).** Raw evidence links now open the [immutable archive catalog](2026-10-16-pr49-evidence-catalog.md). Each link title retains its exact archived member path. Original verdicts, measurements, limitations and execution SHA identities remain historical; the archive bundle restores their original source.
