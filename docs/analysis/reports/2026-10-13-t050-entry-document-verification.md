# T-050 entry-document verification — 2026-10-13

- **Task / plan:** [T-050](../tasks/phase-b2/T-050-entry-docs-and-glossary-sync.md), Step 6 of the [approved plan](2026-10-12-phase-b2-track2-preflight-and-plan.md).
- **Executed source:** clean `development` at `75de2ba90e151bae33e14d2db4a8278837e7775d` after T-049’s canonical boundary `054e13e`. Entry-document edits described below are subsequent working-tree changes, not claimed at that executed source.
- **State:** T-050 In Review after both fresh code/security rounds and bounded correction verification; canonical boundary below supersedes the implementation-time pending snapshots. No Done, maintainer review, hosted CI or merge claim.
- **Evidence:** [full preparation/source map](2026-10-13-t050-entry-document-preflight.md), [raw captures/metadata](2026-10-13-t050-entry-document-evidence/README.md), [glossary disposition/ID ledger](2026-10-13-t050-entry-document-evidence/glossary.json).

## Existing-document review and implementation scope

The retained preparation map reviews all existing entry/guide/glossary/skill/path/license targets and their relevant source definitions. Its initial partial prerequisite ledger and subsequent independent full-corpus completion remain explicitly separate; preparation is not either implementation-review round. Source remained unchanged through T-049 publication and the T-050 kickoff. No new architectural decision, BSP, phase, syscall, lifecycle policy or parser is introduced.

README now shows current versus target placement, per-table revocation, current high-half/per-task translation, an illustrative unsafe list including audited user copies, six workspace members and the verified userland-before-BSP/profile commands. Its serial trace removes the nonexistent loader banner and uses actual EL0 interleaving with fragile values elided. Both existing task guides follow write-guide’s complete structure; they explain console return versus non-returning exit, free-function dispatch, unreclaimed resources, AP/UXN/PXN, current W^X/fault-containment limits, timer/idle non-execution and raw-log options. Guides inventory contains the four substantive files; availability and refresh review status are distinguished from acceptance. The prior execution-trace anchor remains for existing historical links.

The BSP procedure masks DAIF before stack/FP/BSS setup, labels its skeleton as already-EL1, requires the existing accepted target boot policy for EL2, and distinguishes minimal declared-workload success from full reference EL0/IPC smoke. Exception diagnostics use the printed PID-scoped path. Analysis/roadmap/start-task path templates cover lowercase dot-free IDs: C → phase-c; B.2 → phase-b2 and phase-b2.md; Tracks remain distinct from B milestones.

Glossary additions are AddressSpace, Bridge phase, PMM and Track. Pure M-section and Rendezvous/Reply ordering moves are separately recorded from factual corrections. All 54 existing/new bold headwords have immediate explicit unique stable anchors derived from their full displayed headword (lowercase ASCII alphanumerics, other runs to hyphens). The established mmu_bootstrap/.boot_pt grouping is retained as the sole local ordering exception. Existing definitions were verified against current rights/handles, IPC stages, MMU/frame allocation, source-qualified timer arithmetic, raw-pointer discipline and syscall behavior; target userspace services and dynamically exercised Miri coverage are qualified. No outward glossary-link sweep is claimed or required by the approved contract.

The maintainer’s exact common copyright line was recorded in task history before editing. NOTICE line 2 and LICENSE appendix line 189 now read `Copyright 2026 HodeTech, Cemil ILIK and Tyrne Contributors`. LICENSE indentation/newline and every other byte remain unchanged; no legal-policy change is made.

## Clean-source build prerequisites

The coordinator exported tracked HEAD with git archive into a disposable directory. Assertions confirmed no target/, no generated hello.bin and no .git initially. The shared installed Rust/Cargo/QEMU tools and machine caches were reused; this is not a fresh-install test. Root repository HEAD/status remained unchanged and clean throughout capture. The source tar hash is `68500b9e7a5f05d48b668ca6bd8e1c28ed8e7f5625e6ee4d2fbf5f10a56ebe28`; the archive was not retained, and exact source is available from Git.

Commands ran sequentially in that export, with matching profiles. The explicit README prerequisite builds preceded each smoke; smoke then repeated its normal automatic matching build (warm reuse within that profile). Interactive mon:stdio/Ctrl-A behavior was not newly automated; the same resulting images were exercised through smoke’s noninteractive runner.

| Capture | Exact command | Exit |
|---------|---------------|-----:|
| debug-userland | `tools/build-userland.sh` | 0 |
| debug-kernel | `cargo kernel-build` | 0 |
| debug-smoke | `tools/smoke.sh --int --timeout 5` | 0 |
| release-userland | `tools/build-userland.sh --release` | 0 |
| release-kernel | `cargo kernel-build --release` | 0 |
| release-smoke | `tools/smoke.sh --release --int --timeout 5` | 0 |

Tools: pinned nightly-2026-01-15, rustc 1.94.0-nightly `86a49fd71fecd25b0fd20247db0ba95eeceaba28`, cargo `6d1bd93c47f059ec1344cb31e68a2fb284cbc6b1`, LLVM 21.1.8, QEMU 11.1.1, Python 3.9.6, Darwin arm64 / aarch64-apple-darwin. Exact tool output and UTC capture intervals are retained; no tool upgrade, dependency or CI change was made. Captures ran 2026-10-13 UTC/Europe-Istanbul. Compiler/target/QEMU override variables recorded in metadata were unset.

## Fresh raw traces and manual interpretation

### Debug

Raw [QEMU output](2026-10-13-t050-entry-document-evidence/debug.qemu.log): 1139 bytes, SHA-256 `80a53a565fa95fcf4d509d38668ddc9ad3a73b03bff93d74b16a17797a1c0d8c`. Raw hello image: 117 bytes, SHA-256 `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`; ELF identities are in metadata.

```text
tyrne: hello from kernel_main
tyrne: mmu activated
tyrne: high-half active
tyrne: pmm initialized (32593 frames available; 175 reserved)
tyrne: address-space-arena ready (1 / 8 slots used; bootstrap AS root = 0x40099000)
tyrne: timer ready (62500000 Hz, resolution 16 ns)
tyrne: starting cooperative scheduler
tyrne: task B — waiting for IPC
tyrne: task A -- sending IPC
Exception return from AArch64 EL1 to AArch64 EL0 PC 0x800000
Taking exception 2 [SVC] on CPU 0
...from EL0 to EL1
...with ESR 0x15/0x56000000
...with SPSR 0x3c0
...with ELR 0x800034
...to EL1 PC 0xffffffff40080c00 PSTATE 0x3c5
hello from userspace
Exception return from AArch64 EL1 to AArch64 EL0 PC 0x800034
Taking exception 2 [SVC] on CPU 0
...from EL0 to EL1
...with ESR 0x15/0x56000000
...with SPSR 0x600003c0
...with ELR 0x80005c
...to EL1 PC 0xffffffff40080c00 PSTATE 0x3c5
tyrne: userspace task exited
tyrne: task B — received IPC (label=0xaaaa); replying
tyrne: task A — received reply (label=0xbbbb); done
tyrne: all tasks complete
tyrne: boot-to-end elapsed = 5068000 ns
qemu-system-aarch64: terminating on signal 15 from pid 52249 (<unknown process>)
```

### Release

Raw [QEMU output](2026-10-13-t050-entry-document-evidence/release.qemu.log): 1113 bytes, SHA-256 `2a09900e123c78f16118db5999f7f8a1aa358ece6e779cf86788915f61ef499a`. Raw hello image: 69 bytes, SHA-256 `ade8d1695182284e1efba2436c5ead8e4db6dac816f61852d436fc3d300362df`; ELF identities are in metadata.

```text
tyrne: hello from kernel_main
tyrne: mmu activated
tyrne: high-half active
tyrne: pmm initialized (32598 frames available; 170 reserved)
tyrne: address-space-arena ready (1 / 8 slots used; bootstrap AS root = 0x40094000)
tyrne: timer ready (62500000 Hz, resolution 16 ns)
tyrne: starting cooperative scheduler
tyrne: task B — waiting for IPC
tyrne: task A -- sending IPC
Exception return from AArch64 EL1 to AArch64 EL0 PC 0x800000
Taking exception 2 [SVC] on CPU 0
...from EL0 to EL1
...with ESR 0x15/0x56000000
...with SPSR 0x3c0
...with ELR 0x800020
...to EL1 PC 0xffffffff40080c00 PSTATE 0x3c5
Exception return from AArch64 EL1 to AArch64 EL0 PC 0x800020
Taking exception 2 [SVC] on CPU 0
...from EL0 to EL1
...with ESR 0x15/0x56000000
...with SPSR 0x3c0
...with ELR 0x80002c
...to EL1 PC 0xffffffff40080c00 PSTATE 0x3c5
tyrne: userspace task exited
tyrne: task B — received IPC (label=0xaaaa); replying
tyrne: task A — received reply (label=0xbbbb); done
tyrne: all tasks complete
tyrne: boot-to-end elapsed = 3643008 ns
qemu-system-aarch64: terminating on signal 15 from pid 52345 (<unknown process>)
```

Both raw logs show exactly two Taking exception SVC records, each from EL0 to EL1, and no other Taking exception record or listed fault class. The first ERET enters EL0, the second resumes after the console call; exit then prints its marker and dispatches B without returning to the exiting task. Debug contains one greeting; release contains none. Both have one exit and one completion marker. The delivered serial excerpts are ordered subsequences with explicit value elision, not fabricated complete raw output.

The FIFO source agrees: initial [B,A,user] → B blocks → A delivers to B/yields behind user → user exits → B receives/replies/yields → A receives/completes/spins. B’s tail and idle remain unreached. This is neither a timer-IRQ/preemption test nor a benchmark: the observed 5,068,000 / 3,643,008 ns lines are host-dependent single-run elapsed values after the high-half snapshot, not comparable performance measurements. Smoke’s marker/fault gates and the coordinator’s separate SVC/order inspection are different checks.

The successful path does not prove all permission/isolation cases, arbitrary hostile EL0 behavior, resource reclamation, strict provenance, SMP, real hardware or every ABI property. Current non-SVC fault panic, privileged executable RAM and lifecycle gaps remain explicit descriptions of existing behavior, not new policy. Existing host adversarial tests and historical security reviews remain distinct evidence. Both fresh code/security rounds must assess the actual document change next.

## Coordinator static verification

Coordinator checks passed: all touched rendered local paths/fragments, both full guide structures and four-file inventory, tagged fences, five ordered serial/exception excerpt blocks against retained debug output, exact 50-to-54 headword inventory/54 IDs and only the approved ordering moves, source-qualified BSP DAIF/scope and phase paths, raw stream hashes/exits/order, exact one-line LICENSE delta and step-only allowlist. The [diagnostic snapshot](2026-10-13-t050-entry-document-evidence/verification.json) labels the checked subsequent implementation working tree separately from the clean executed source. The checker initially caught sorting by parenthetical expansions (MMU, Syscall, Unsafe); before commit, ordering was corrected to primary headwords while retaining complete displayed-headword anchor IDs. No original definition is frozen merely to preserve a move. These checks are one-off diagnostics using an existing Python Markdown tool, not the T-056 shipping parser/grammar/fixture suite. Both fresh implementation-review rounds remain pending.

## Round 1 correction — 2026-10-13

Fresh primary code review confirmed Low C01: the first-userspace boot wire-up combined an address-space handle and a raw capability-table pointer under the word “handles”. Source `add_user_task` takes `AddressSpaceHandle` and `*mut CapabilityTable` separately; its safety contract requires the table to outlive the task and forbids a live mutable borrow across a context switch. The BSP subsequently dereferences that stored pointer for syscall dispatch. The guide now states those distinct inputs and caller obligations. The distinct security reviewer independently confirmed the shared finding after its initial standalone assessment; count C01 once under code-review provenance. No runtime or retained raw-evidence bytes changed. Both complete rounds and canonical integration remain pending.

The post-correction bounded diagnostic passes on the same 32-file implementation range: 13 Markdown files, 293 rendered local targets, 18 fragments, zero errors; all 14 retained stream hashes, six recorded exits, glossary inventory/order/anchors and LICENSE preservation checks still pass. `git diff --check` passes. The retained verification.json remains the earlier implementation snapshot (292 targets), not a rewritten claim about this later tree.

## Round 2 correction — 2026-10-13

Fresh primary R2 code review confirmed Low R2-C01: the new Bridge phase definition said B.2 must close before all C/D “work begins”. Accepted ADR-0040 Decision outcome rule 2 instead gates milestone opening and implementation tasks leaving Draft, while explicitly permitting Phase C planning, Proposed ADRs and the readiness sweep. The glossary now preserves that distinction. The separate fresh R2 security reviewer independently corroborated this shared code-origin finding after completing its own source/evidence assessment. Count it once, separately from resolved R1 C01. No new policy, ADR, glossary vocabulary/anchor, runtime source or retained raw-evidence change. Bounded R2 correction verification and canonical integration remain pending.

## Canonical review boundary — 2026-10-13

[Code](../reviews/code-reviews/2026-10-13-t050-entry-document-refresh.md) and [security](../reviews/security-reviews/2026-10-13-t050-entry-document-refresh.md) artifacts retain all four complete delivered reports, original findings/verdicts and final bounded approvals. Both fresh rounds approve corrected source 946f45f. R1 C01 fixed at 5236156 and R2-C01 fixed at 946f45f; each code-origin Low is counted once, security corroborations attributed. Zero unresolved delta findings; existing HIGH T-038 remains Ready.

T-050 acceptance/DoD now checked against delivered evidence and step-scoped allowances; status In Review without date_done. The later canonical bookkeeping has separate coordinator static verification; retained verification.json remains the original 292-target implementation snapshot. Six runtime commands and all raw evidence still refer to clean executed 75de2ba. No new run, human approval, hosted CI, merge or future-tool certification. T-055 starts next.

Final coordinator publication diagnostic: 39 step paths (the original 32 plus seven canonical/lifecycle surfaces), 20 Markdown files, 664 rendered local targets and 42 fragments, zero errors. Four exact delivered report copies and unique table-index membership verified; all 54 glossary anchors, 27 existing-definition dispositions, five serial excerpts, 14 raw stream hashes, six recorded exits and one-line LICENSE preservation pass. Task-state recount: 8 Done, 24 Ready, 6 In Review, 8 Draft; no new Done. This bounded existing-Markdown-tool diagnostic is not T-056 grammar coverage. An initial coordinator count assertion incorrectly expected 35 original paths; it failed before commit, was corrected to the verified 32, and the complete check was rerun.
