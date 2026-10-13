# T-055 — ADR corrections, index anomalies and dispositions

- **Date:** 2026-10-13.
- **Base:** development e8104e3 (Step 7 kickoff), following T-050 canonical publication 69afa33. Exact baseline SHA is retained in the evidence JSON; implementation is the subsequent working tree, not a claim of clean committed execution.
- **Task / authority:** [T-055](../tasks/phase-b2/T-055-adr-append-only-corrections.md), [approved plan](2026-10-12-phase-b2-track2-preflight-and-plan.md), [ADR-0025](../../decisions/0025-adr-governance-amendments.md), [ADR-0043](../../decisions/0043-documentation-corpus-consistency.md).
- **Preflight / evidence:** [existing-document review and extra-scope reasons recorded before edits](2026-10-13-t055-adr-correction-preflight.md), [raw checks and metadata](2026-10-13-t055-verification-evidence/README.md).
- **State:** T-055 In Review after both fresh code/security rounds and bounded correction verification; canonical boundary below supersedes earlier pending checkpoints. No ADR decision/status/date change, runtime behavior, Done or human approval.

## Append-only correction ledger

| Surface | Correction and preservation |
|---------|-----------------------------|
| [ADR-0008](../../decisions/0008-cpu-trait.md#revision-notes), [IrqGuard rustdoc](../../../hal/src/cpu.rs) | Dated retraction of unverified generalized vtable/.rodata aliasing explanation; historical boot failure and concrete-dispatch rationale retained. Comment only; no claim that dynamic dispatch is unsound. |
| [ADR-0033](../../decisions/0033-kernel-high-half-migration.md) | Dated top pointer to existing May-30 canonical single-offset/KBASE correction. Body/status/date intact. |
| [ADR-0011](../../decisions/0011-irq-controller-trait.md) | Dated GICv2 banner points to ADR-0036; trait and old body intact. |
| [ADR-0012](../../decisions/0012-boot-flow-qemu-virt.md#open-questions) | Exact original EL-drop sentence wrapped in strikethrough; resolved April-27 by ADR-0024, pointer actually applied October-13. No fabricated historical edit date. |
| [ADR-0018](../../decisions/0018-badge-scheme-and-reply-recv-deferral.md#pros-and-cons-of-the-options) | Appended dated pros/cons for all six options before References, same template placement as other ADRs. A/D deferrals unchanged; original emulation/compatibility text preserved and present applicability qualified against current IPC. |
| [ADR-0010](../../decisions/0010-timer-trait.md#revision-notes), [Timer rustdoc](../../../hal/src/timer.rs) | Previously recorded extra scope: factual rider/comment distinguish approximate resolution from existing ceiling deadline conversion and saturation. No function or policy change. |
| [supersede-adr](../../../.agents/skills/supersede-adr/SKILL.md), [P7 compatibility anchor](../../standards/architectural-principles.md#p7--no-proprietary-blobs) | Previously recorded extra scope: template links now quoted Markdown data, existing append-only discipline restored, invisible legacy P7 ID repairs four original ADR-0015 links while preserving ADR-0015 and current P7 rule bytes. |
| [ADR index](../../decisions/README.md), [sync procedure](../../../.agents/skills/sync-adr-index/SKILL.md) | Exact source titles/status/full Date, reporting aliases and historical forms separately; whole/partial supersession distinguished from ordinary riders. README Format changes separately authorized by T-055, beyond an ordinary table-only sync. |

## Source provenance and limits

Full historical commit 4fe547cf47beb54a51ad09f8a5705d2f30841a29 and its CPU/BSP changes were read. Its commit message reports QEMU failure and a generic-dispatch fix; it also changes FP/SIMD setup and naked context-switch assembly. No retained isolated reproduction, disassembly, Miri diagnostic or compiler issue proves the generalized cause. Retracting that explanation does not retract the recorded observation or settle all possible compiler/runtime questions. The unchanged CPU/guard API remains source-defined.

Timer provenance: full d820a88d902e77ccf33b30ebe9c7be03a9c25cea changes floor to ceiling to honor the existing reaches-or-exceeds contract; full 5c9cf069c2f5fa3be77c048d865ae89c4055ba11 includes the 3 Hz / 333333334 ns → 2 ticks regression. T-012 history records both, and d820a88 is an ancestor of merged main c16997e. Current helpers separately compute nearest-integer period (minimum 1 ns) and saturating ceiling tick count. This is evidence for existing behavior, not a new rounding decision, exact IRQ-latency proof or unlimited representability guarantee.

The original six ADR-0018 options and accepted A/D outcomes are preserved. Its old unqualified sender-handle emulation and source-compatibility claims are not repeated as current guarantees: received IPC contains no authenticated sender-capability identity, and adding fields/parameters needs a compatibility assessment. No successor decision or implemented badge/reply_recv feature is claimed.

## Baseline index/header differences

42 files and 42 uniquely indexed rows, numeric order, no membership/filename/status mismatch. **14 title mismatches: eight descriptive aliases and six inline-code-markup omissions. One Date mismatch: ADR-0023's full authoritative prose was truncated.** Every row below is reconciled to the exact source header, without editing that header.

| ADR / field | Old index value | Authoritative header / delivered value | Disposition |
|-------------|-----------------|----------------------------------------|-------------|
| 0004 / title | Target hardware platforms and tiers | Target hardware platforms and support tiers | Exact header copied; historical source unchanged. |
| 0007 / title | Console HAL trait signature | `Console` HAL trait signature | Exact header copied; historical source unchanged. |
| 0008 / title | Cpu HAL trait signature (v1, single-core scope) | `Cpu` HAL trait signature (v1, single-core scope) | Exact header copied; historical source unchanged. |
| 0009 / title | Mmu HAL trait signature (v1) | `Mmu` HAL trait signature (v1) | Exact header copied; historical source unchanged. |
| 0010 / title | Timer HAL trait signature (v1) | `Timer` HAL trait signature (v1) | Exact header copied; historical source unchanged. |
| 0011 / title | IrqController HAL trait signature (v1) | `IrqController` HAL trait signature (v1) | Exact header copied; historical source unchanged. |
| 0012 / title | Boot flow and memory layout for bsp-qemu-virt | Boot flow and memory layout for `bsp-qemu-virt` | Exact header copied; historical source unchanged. |
| 0020 / title | `ContextSwitch` trait and `Cpu` v2 | `Cpu` trait v2: context-switch extension | Exact header copied; historical source unchanged. |
| 0023 / date | 2026-04-27 | 2026-04-27 (deferred at B0 closure); placeholder body landed 2026-05-07 (B1 closure trio) | Exact header copied; historical source unchanged. |
| 0026 / title | Idle dispatch via separate fallback slot | Idle dispatch via separate fallback slot (supersedes ADR-0022 Option A) | Exact header copied; historical source unchanged. |
| 0029 / title | Initial userspace image format (B4 — raw flat binary) | Initial userspace image format | Exact header copied; historical source unchanged. |
| 0030 / title | Syscall ABI and userspace error taxonomy (B5) | Syscall ABI and userspace error taxonomy | Exact header copied; historical source unchanged. |
| 0031 / title | Initial syscall set (B5 — `send`/`recv`/`console_write`/`task_yield`/`task_exit`) | Initial syscall set (B-phase) | Exact header copied; historical source unchanged. |
| 0033 / title | Kernel high-half migration (B6 — kernel → `TTBR1_EL1`, boot-time) | Kernel high-half migration | Exact header copied; historical source unchanged. |
| 0037 / title | EL0 entry context (B6 — userspace register file + enter-EL0/`ERET` path + per-task `SP_EL1`) | EL0 entry context (userspace register file + enter-EL0/`ERET` path) | Exact header copied; historical source unchanged. |

## Title/filename-slug differences — separate retained observations

35 literal normalized full-title/filename-slug differences remain after index synchronization. For this diagnostic, lowercase ASCII alphanumerics are retained and other runs joined with hyphens. This is a transparent literal comparison, not semantic proof that a short descriptive slug is defective. These include 0040–0043; no filed file is renamed, no title rewritten and no anomaly concealed behind a “clean index” claim. All 35 have the same disposition: preserve immutable filed identity, report the difference.

| ADR file | Normalized full title |
|----------|-----------------------|
| [0001-microkernel-architecture.md](../../decisions/0001-microkernel-architecture.md) | `capability-based-microkernel-architecture` |
| [0002-implementation-language-rust.md](../../decisions/0002-implementation-language-rust.md) | `rust-as-the-implementation-language` |
| [0003-license-apache-2.md](../../decisions/0003-license-apache-2.md) | `apache-2-0-license` |
| [0004-target-platforms.md](../../decisions/0004-target-platforms.md) | `target-hardware-platforms-and-support-tiers` |
| [0005-documentation-language-english.md](../../decisions/0005-documentation-language-english.md) | `english-as-the-documentation-and-code-language` |
| [0006-workspace-layout.md](../../decisions/0006-workspace-layout.md) | `workspace-layout-and-initial-crate-boundaries` |
| [0007-console-trait.md](../../decisions/0007-console-trait.md) | `console-hal-trait-signature` |
| [0008-cpu-trait.md](../../decisions/0008-cpu-trait.md) | `cpu-hal-trait-signature-v1-single-core-scope` |
| [0009-mmu-trait.md](../../decisions/0009-mmu-trait.md) | `mmu-hal-trait-signature-v1` |
| [0010-timer-trait.md](../../decisions/0010-timer-trait.md) | `timer-hal-trait-signature-v1` |
| [0011-irq-controller-trait.md](../../decisions/0011-irq-controller-trait.md) | `irqcontroller-hal-trait-signature-v1` |
| [0012-boot-flow-qemu-virt.md](../../decisions/0012-boot-flow-qemu-virt.md) | `boot-flow-and-memory-layout-for-bsp-qemu-virt` |
| [0013-roadmap-and-planning.md](../../decisions/0013-roadmap-and-planning.md) | `roadmap-and-planning-process` |
| [0015-ai-integration-stance.md](../../decisions/0015-ai-integration-stance.md) | `ai-integration-stance-userspace-only-kernel-neutral` |
| [0018-badge-scheme-and-reply-recv-deferral.md](../../decisions/0018-badge-scheme-and-reply-recv-deferral.md) | `badge-scheme-and-reply-recv-fastpath-formal-deferral` |
| [0020-cpu-trait-v2-context-switch.md](../../decisions/0020-cpu-trait-v2-context-switch.md) | `cpu-trait-v2-context-switch-extension` |
| [0021-raw-pointer-scheduler-ipc-bridge.md](../../decisions/0021-raw-pointer-scheduler-ipc-bridge.md) | `raw-pointer-scheduler-ipc-bridge-api` |
| [0022-idle-task-and-typed-scheduler-deadlock.md](../../decisions/0022-idle-task-and-typed-scheduler-deadlock.md) | `idle-task-and-typed-scheduler-deadlock-error` |
| [0024-el-drop-policy.md](../../decisions/0024-el-drop-policy.md) | `el-drop-to-el1-policy` |
| [0025-adr-governance-amendments.md](../../decisions/0025-adr-governance-amendments.md) | `adr-governance-amendments-forward-reference-contract-rider-hygiene` |
| [0026-idle-dispatch-fallback.md](../../decisions/0026-idle-dispatch-fallback.md) | `idle-dispatch-via-separate-fallback-slot-supersedes-adr-0022-option-a` |
| [0027-kernel-virtual-memory-layout.md](../../decisions/0027-kernel-virtual-memory-layout.md) | `kernel-virtual-memory-layout-b2-identity-mapped-mmu-activation` |
| [0028-address-space-data-structure.md](../../decisions/0028-address-space-data-structure.md) | `address-space-data-structure-b3-kernel-object-capability-gated-mmu-map-wrappers-activation-on-context-switch` |
| [0030-syscall-abi.md](../../decisions/0030-syscall-abi.md) | `syscall-abi-and-userspace-error-taxonomy` |
| [0031-initial-syscall-set.md](../../decisions/0031-initial-syscall-set.md) | `initial-syscall-set-b-phase` |
| [0032-endpoint-rollback-and-cancel-recv.md](../../decisions/0032-endpoint-rollback-and-cancel-recv.md) | `endpoint-state-rollback-on-ipc-recv-and-yield-deadlock-ipc-cancel-recv-primitive` |
| [0035-physical-memory-manager.md](../../decisions/0035-physical-memory-manager.md) | `physical-memory-manager-b3-prerequisite-bitmap-allocator` |
| [0036-qemu-virt-gicv2-no-iommu-v1.md](../../decisions/0036-qemu-virt-gicv2-no-iommu-v1.md) | `qemu-virt-is-gicv2-no-iommu-in-v1-corrects-gicv3-smmuv3-in-adr-0004-0006-0012` |
| [0037-el0-entry-context.md](../../decisions/0037-el0-entry-context.md) | `el0-entry-context-userspace-register-file-enter-el0-eret-path` |
| [0038-mmu-translate-and-user-access.md](../../decisions/0038-mmu-translate-and-user-access.md) | `mmu-translate-read-only-walk-per-task-user-access-translation-b6-gate-1` |
| [0039-userland-build-pipeline.md](../../decisions/0039-userland-build-pipeline.md) | `userland-build-pipeline-b6-userland-hello-tyrne-user-raw-flat-embed-orchestration` |
| [0040-phase-b2-consolidation-bridge.md](../../decisions/0040-phase-b2-consolidation-bridge.md) | `phase-b-2-consolidation-bridge-governance-gating-and-exit-criteria` |
| [0041-test-name-prefix-policy-recovery.md](../../decisions/0041-test-name-prefix-policy-recovery.md) | `test-name-prefix-policy-historical-recovery` |
| [0042-descriptive-test-names.md](../../decisions/0042-descriptive-test-names.md) | `descriptive-test-names-without-a-mandatory-prefix` |
| [0043-documentation-corpus-consistency.md](../../decisions/0043-documentation-corpus-consistency.md) | `documentation-corpus-consistency-and-planned-adr-identities` |

## Existing metadata and supersession forms

| Observation | Evidence and disposition |
|-------------|--------------------------|
| ADR-0023 Deferred / full prose Date | Existing deferred placeholder and B0/B1 history; preserve exact status and entire Date. Not Accepted, not a newly invented filing date or blanket malformed-date exemption. |
| ADR-0022 → 0026, partial | Older header/callout and newer Context agree: only idle-task-location superseded; typed-error axis stands. Preserve full qualification rather than collapsing it to whole-decision supersession. Target 0026 remains Accepted. |
| ADR-0041 → 0042, whole | Header/callout and new Context/References reciprocate; target 0042 Accepted, historical prefix record remains Superseded. No transition performed here. |
| Ordinary correction/implementation riders | A link to a later ADR alone does not imply supersession or require status changes. Compare explicit decision/scope before classifying it. |
| Missing slot 0034 | ADR-0027 and the index explicitly reserve kernel-section permissions. Preserve gap and all later numbers; no placeholder file fabricated. |
| Other metadata/membership defects | Initial extraction found none beyond those itemized. Unknown/missing/malformed forms must still be reported; the documented existing forms do not authorize new ones. |

The machine-readable baseline contains every row and before/after field difference. A post-edit header comparison, scoped preservation/navigation diagnostics and actual command outcomes are recorded below after execution; neither extraction nor a link scan proves architectural correctness.

## Executed implementation verification — 2026-10-13

Required cargo fmt --all -- --check, cargo host-clippy and cargo host-test all exit 0 on the recorded implementation working tree. Host tests: 46 HAL + 259 kernel + 58 test-HAL unit tests and 3 doctests = 366 passed; two HAL example doctests intentionally ignored, zero failed. No test/signature/runtime-token change; this is current execution evidence, not inferred from an older report. Exact two edited Rust-file hashes match captures. All six raw stream byte counts/SHA-256 values verify; root read the full 398-line test stdout and both nonempty stderr streams, with three empty streams retained.

[Static preservation snapshot](2026-10-13-t055-verification-evidence/static-verification.json) verifies six corrected ADRs are insertion-only except the exact approved ADR-0012 sentence wrapper; all Status/Date/Deciders fields unchanged. Non-rustdoc source lines match base; ADR-0015 bytes unchanged and P7 delta is only the invisible compatibility ID. Exact 42-row header/index comparison has zero remaining mismatches, while all 35 title/slug differences and historical forms remain reported. Both whole and partial supersession pointers resolve consistently. No other executable/config/build/dependency/CI surface changed.

[Bounded navigation snapshot](2026-10-13-t055-verification-evidence/navigation.json) checks 364 tracked/visible-untracked Markdown files, 6047 rendered local targets and 611 fragments with zero candidates before these final bookkeeping links. This is an existing third-party Markdown diagnostic of actual rendered forms, not complete grammar coverage or the future Python-stdlib T-056 gate. The six preflight defects are repaired without an archive exception. New tagged Markdown template fences render the two dummy paths as code, and the compatibility anchor resolves all four preserved ADR-0015 targets.

Raw host-test stdout ends with its original blank line; preserve it byte-for-byte. Default step whitespace inspection reports that raw blank EOF; the separate non-log diff check passes. Neither this exception nor the earlier T-049 raw evidence is normalized or hidden as a clean unqualified whole-branch check. At the implementation checkpoint both fresh code/security rounds were pending; task criteria stay unchecked until canonical closure. Existing HIGH T-038 remains unresolved.

## Round 1 confirmed corrections — 2026-10-13

Independent code and security contexts assessed e8104e3..f256a610 before exchanging actual reports. Both approved with one Low finding: R1-C01/S01 is the same stale timer-helper citation, counted once. Remove the nonexistent current-trait quote, explain nearest-integer resolution as an approximation that can round either way, and separate its representational floor from deadline conversion. Functions, signatures and tests remain unchanged. This also removes the helper's incorrect claim that nearest reporting never understates the hardware period; its existing 19.2 MHz example demonstrates the approximation.

Low C-ROOT-01 was found separately by the coordinator and corroborated by the reviewers only after their independent checkpoints. Its [additional-file reason](2026-10-13-t055-adr-correction-preflight.md#round-1-additional-file-reason--recorded-before-correction) was recorded before editing propose-standard-change. Align the stale in-place amendment instruction with existing ADR-0025: preserve Accepted bodies, use dated evidence-backed factual riders, keep Proposed drafts editable, and retain explicit maintainer approval/Accepted authority before a substantive new or changed standard decision. This is the fifth demonstrated additional file, not a new rule or independent reviewer discovery.

The earlier executed raw evidence and source hashes remain immutable and describe the implementation captured before f256a610. The timer rustdoc correction changes its current file hash without changing executable source; verify the original capture against that implementation commit, and separately verify the corrected cumulative source against the kickoff. R1 bounded fix verification and fresh R2 are still required. The stale top-level pending-verification summary has also been corrected; this bookkeeping note is not a third repository finding.

[Correction verification](2026-10-13-t055-verification-evidence/r1-correction-verification.json) records actual post-fix fmt and host-clippy exits 0, cumulative append-only/non-rustdoc preservation, exact index/forms, six immutable original stream hashes and original source hashes bound to f256a610. The updated timer source hash is separate. No additional test run was needed for prose-only corrections; the primary reviewer independently reran all three checks on frozen f256a610 (366 passed/two ignored). The post-fix bounded scan found 364 Markdown files/6057 local targets/615 fragments, zero candidates before this final link. Default step diff inspection exits 2 solely for the retained raw test blank EOF; non-log inspection exits 0. Bounded reviewer verification follows the correction commit.

## Canonical boundary — 2026-10-13

[Code](../reviews/code-reviews/2026-10-13-t055-adr-corrections.md) and [security](../reviews/security-reviews/2026-10-13-t055-adr-corrections.md) preserve all four complete actual reports, initial findings/verdicts and subsequent verification/reconciliation. Both rounds Approve 23391c7; two unique R1 Low findings fixed, zero new R2 or unresolved findings. R1-C01/S01 is independently corroborated; C-ROOT-01 keeps coordinator origin. Task criteria are checked and status In Review without date_done.

The actual cumulative reviewed inventory is 28 files; the R2 assignment's 27 was corrected before assessment. The separate correction snapshot counted 27 before its own JSON was written, so it is not a final committed inventory. Original implementation snapshots/raw streams remain unchanged; later canonical publication has separate scoped diagnostics. No hosted CI, T-056 grammar certification, new runtime execution, human review or T-038 closure. Step 8/T-052/T-053 is next.

[Canonical publication verification](2026-10-13-t055-verification-evidence/publication-verification.json) independently checks exact once-only retention of the four final actual reports, membership in rendered family-index tables, seven AC/five DoD boxes, In Review/no date_done, original raw/source bindings and cumulative scope/preservation. The final cumulative publication has 36 paths and 366 Markdown files/6087 local targets/615 fragments with zero candidates in the bounded diagnostic. This is coordinator bookkeeping, not another independent review or the shipped T-056 gate.
