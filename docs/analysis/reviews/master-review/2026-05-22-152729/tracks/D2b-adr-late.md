# D2b-adr-late — ADRs 0019-0035 (master review, commit 288ddb2)

Anchor commit: `288ddb2`. Working directory: `/Users/dev/Documents/Projects/OS-Project`.

---

## Summary

All 13 target ADR files were read in full. Cross-checks were performed against the primary code files each ADR governs:
`kernel/src/sched/mod.rs`, `bsp-qemu-virt/src/cpu.rs`, `hal/src/context_switch.rs`, `kernel/src/cap/mod.rs`,
`kernel/src/cap/table.rs`, `kernel/src/ipc/mod.rs`, `kernel/src/mm/address_space.rs`, `kernel/src/mm/pmm.rs`,
`kernel/src/obj/task_loader.rs`, `bsp-qemu-virt/linker.ld`, and `docs/decisions/README.md`.

**Overall verdict: CONDITIONALLY ACCEPTED — two Major findings require documentation correction before the ADR set is considered fully current; no Blocker-level code correctness or security issues were found.**

Severity summary:
- Blocker: 0
- Major: 3
- Minor: 4
- Nit: 3
- Praise: 5

The most significant finding is **ADR-0020's outdated `Aarch64TaskContext` specification**: the shipped
`Aarch64TaskContext` struct is 168 bytes and saves `d8–d15` SIMD/FP registers; ADR-0020's `Neutral` note still
describes a 104-byte struct deferring `d8–d15` to Phase B. This is a documentation-vs-code drift with security
implications since the safety contract in `hal/src/context_switch.rs` also omits the SIMD register set.

The numbering gaps (0030, 0031, 0033, 0034) are all **intentionally reserved** future-ADR placeholders, documented
explicitly in ADR-0027 — no action required.

---

## Findings (by severity)

### Blocker

*None identified.*

---

### Major

#### D2b-001 — ADR-0020: `Aarch64TaskContext` size and register-save contract describe a 104-byte struct; shipped code is 168 bytes with d8–d15 saved

**ADR location:** `docs/decisions/0020-cpu-trait-v2-context-switch.md:233-244` (concrete type definition block) and
`:304` (Neutral note: *"NEON / FP registers deferred… d8–d15 are not saved in v1"*)

**Code it drifts from:** `bsp-qemu-virt/src/cpu.rs:299-319` (`Aarch64TaskContext` struct) and `:326`
(`const _: () = assert!(core::mem::size_of::<Aarch64TaskContext>() == 168)`)

**Description.** ADR-0020 specifies a 13-field, 104-byte `Aarch64TaskContext` comprising `x19_x28[10]`, `fp`, `lr`,
and `sp` only. Its `Neutral` bullet explicitly states: *"NEON / FP registers deferred. The aarch64 AAPCS64
callee-saved NEON registers (d8–d15) are not saved in v1 because Phase A kernel tasks do not use floating point. A
Phase B ADR will add them when userspace tasks run with FP enabled."*

The shipped struct in `bsp-qemu-virt/src/cpu.rs` has an additional field `pub d8_d15: [u64; 8]` (8 × 8 = 64 bytes),
making the total 168 bytes. The compile-time size-assertion (`const _: () = assert!(size_of::<Aarch64TaskContext>()
== 168)`) and the assembly routine `context_switch_asm` both handle `d8–d15`. The struct documentation header also
corrects the total: *"Total size: (10 + 1 + 1 + 1) × 8 + 8 × 8 = 104 + 64 = 168 bytes."*

Separately, the `ContextSwitch` trait's safety contract in `hal/src/context_switch.rs:18-23` reads: *"Implementations
must ensure that `context_switch` atomically saves all callee-saved registers … On aarch64 that is `x19`–`x28`,
`x29` (fp), `x30` (lr), and `sp`."* The SIMD/FP callee-saved registers `d8–d15` are omitted from this normative
safety contract text, even though the implementation saves them.

**Security note (per C6-hal cross-track note).** A future implementer reading only ADR-0020 or
`hal/src/context_switch.rs` would omit `d8–d15` from a new BSP's context-switch implementation. If kernel tasks use
SIMD/FP instructions (possible when `CPACR_EL1.FPEN` is non-zero, e.g. after MMU work enables caches), omitting
`d8–d15` causes silent data corruption across context switches — wrong results, not a crash.

**Suggested fix.** Write a Revision-notes rider on ADR-0020 recording: (a) the `d8–d15` save was implemented during
the same arc as the initial draft rather than deferred to Phase B as the ADR stated; (b) the Neutral note "NEON / FP
registers deferred" is superseded by the shipped implementation; (c) the new struct size is 168 bytes (not 104).
Additionally update `hal/src/context_switch.rs:18-23` (the trait's safety-contract doc-comment) to enumerate
`d8–d15` alongside `x19–x28, x29, x30, sp`.

---

#### D2b-002 — ADR-0019 `Scheduler` API sketch diverges from shipped struct and bridge API

**ADR location:** `docs/decisions/0019-scheduler-shape.md:153-183` (Public API sketch)

**Code it drifts from:** `kernel/src/sched/mod.rs:239-281` (`Scheduler` struct definition), `:921` (`ipc_send_and_yield`), `:1026` (`ipc_recv_and_yield`)

**Description.** ADR-0019's Public API sketch shows `Scheduler::yield_now<C: Cpu>`, `ipc_send_and_yield`, and
`ipc_recv_and_yield` as `&mut self` methods on `Scheduler`. After ADR-0021 (raw-pointer bridge), these became
`unsafe fn` free functions taking `*mut Scheduler<C>` — a correct and intentional change, but ADR-0019 was never
updated with a rider to reflect the new API shape.

Three specific drifts:

1. **Method vs. free function.** ADR-0019 shows `impl Scheduler { pub fn ipc_send_and_yield(&mut self, …) }`.
   Shipped code has `pub unsafe fn ipc_send_and_yield<C: ContextSwitch + Cpu>(sched: *mut Scheduler<C>, …)` as a
   module-level free function.
2. **`TaskContexts<C>` type absent.** ADR-0019 introduces `TaskContexts<C>` as a separate struct
   (`struct TaskContexts<C: ContextSwitch> { contexts: [C::TaskContext; TASK_ARENA_CAPACITY] }`). The shipped code
   inlines the context array directly as `contexts: [C::TaskContext; TASK_ARENA_CAPACITY]` inside `Scheduler<C>`.
   No separate `TaskContexts<C>` struct exists.
3. **`task_address_space_handles` field.** The shipped `Scheduler<C>` has a fourth parallel array
   `task_address_space_handles: [Option<AddressSpaceHandle>; TASK_ARENA_CAPACITY]` (added in B3 per ADR-0028). The
   ADR-0019 struct sketch does not mention it (it predates ADR-0028), but the 2026-04-27 Revision-notes rider on
   ADR-0019 references only T-008 / architecture-doc cross-link, not the B3 struct addition.
4. **`activate_address_space` closure parameter.** The shipped `ipc_send_and_yield`, `ipc_recv_and_yield`, and
   `yield_now` functions take an extra `activate_address_space: impl FnOnce(AddressSpaceHandle)` parameter. This is
   the activation-on-context-switch hook added by ADR-0028; ADR-0019's sketch predates it and was not updated.

**Severity context.** This is documentation drift rather than a code bug. ADR-0021 and ADR-0028 contain the
authoritative descriptions of the shifted shapes. However, a reader following only ADR-0019's sketch would form an
incorrect mental model of the scheduler API.

**Suggested fix.** Add a Revision-notes rider on ADR-0019 pointing to ADR-0021 (free-function shape; `TaskContexts`
inlined into `Scheduler`) and ADR-0028 (`task_address_space_handles` and `activate_address_space` additions). The
original API sketch should remain as-is (append-only), but the rider should say which parts were superseded by which
later ADRs.

---

#### D2b-003 — ADR-0027 §Context references ADR-0030 and ADR-0031 as if they are definite future ADRs, but no files or T-NNN tasks exist for them

**ADR location:** `docs/decisions/0027-kernel-virtual-memory-layout.md:19` and `:26`

**Code it drifts from:** `docs/decisions/README.md` (index — no entries for 0030 or 0031); no files at
`docs/decisions/0030-*.md` or `docs/decisions/0031-*.md` confirmed by `git ls-files`.

**Description.** ADR-0027 §Context line 19 names ADR-0030 and ADR-0031 as definite future ADRs: *"ADR-0030 (syscall
ABI) inherits the page-fault / capability-grant story; ADR-0031 / future MMU follow-ups…"*. Line 26 repeats:
*"B5 introduces userspace; that ADR (currently reserved as ADR-0030 for syscall ABI…)"*

Unlike ADR-0033 and ADR-0034 — which are named-but-not-yet-opened placeholders explicitly introduced in ADR-0027's
§Dependency chain and documented clearly as *"no T-NNN is opened today because no implementation work depends on it
before B5"* — ADR-0030 and ADR-0031 have no:
- placeholder files in `docs/decisions/`
- README index rows
- T-NNN task files constraining their scope
- Explicit acknowledgment that they are reserved-but-not-yet-allocated

This is a mild violation of ADR-0025 §Rule 1 (forward-reference contract): the forward-reference names slot numbers
that don't exist as any artefact. Unlike ADR-0033/0034 which are treated as named-forward-flags with deliberate
"no file yet" language, ADR-0030/0031 are referenced as if they will simply materialise. A reader scanning for
ADR-0030's definition will find nothing.

The distinction matters because tasks already reference ADR-0030 (e.g., `T-015` task file: *"The B5+ syscall-ABI ADR
(currently pencilled as ADR-0030 per phase-b.md ledger) decides whether to expose it."*). If the syscall ADR ends up
as a different number, those references silently point at nothing.

**Suggested fix.** Either (a) create placeholder files `docs/decisions/0030-*.md` and `docs/decisions/0031-*.md`
with `Status: Deferred`, mirroring the ADR-0023 pattern — this gives readers a citable artefact; or (b) add a short
note in ADR-0027 §Context explicitly stating *"ADR-0030 and ADR-0031 are reserved slot numbers; no placeholder files
exist yet (contrast ADR-0033/0034 which have explicit placeholder language)"* and align with ADR-0025 §Rule 1 by
acknowledging the T-NNN for those tasks is TBD. Option (a) is preferred for consistency with the established
ADR-0023 and ADR-0027/ADR-0033/ADR-0034 placeholder pattern.

---

### Minor

#### D2b-004 — ADR-0022's "Idle task location" supersession callout accurately describes ADR-0026, but the README index status row for ADR-0022 omits that the typed-error axis still stands

**ADR location:** `docs/decisions/README.md:53`

**Description.** The README index row for ADR-0022 reads: *"Superseded by 0026 (idle-task-location axis only;
typed-error axis stands)"*. The parenthetical is present and accurate — this is good practice. However, for
consistency with how other multi-axis supersessions might be handled, this entry is the only one in the index that
carries inline axis-qualification. A new contributor scanning the index for active decisions on typed scheduler
errors would see "Superseded by 0026" and might conclude the typed-error work is also gone. A cross-reference from
the index to the `Status:` field in ADR-0022 (which contains the same qualifier) would be clearer if the README
§Format spec described the pattern. This is informational rather than blocking.

**Suggested fix.** No change required to the ADR text itself — both ADR-0022 and ADR-0026 are correctly written.
Optionally, ADR-0022 could gain a §See-also note pointing readers at ADR-0026 for the idle-location axis and
affirming the typed-error axis. Low priority.

---

#### D2b-005 — ADR-0028 §Simulation row 3 describes "activation-without-TLB-flush" but implementation does a full TLB flush; the ADR notes this but the simulation cell is not corrected

**ADR location:** `docs/decisions/0028-address-space-data-structure.md:149` (`Negative` bullet) and `:78-79`
(Simulation row 3)

**Code it drifts from:** ADR-0028 §Consequences — Negative note; T-018 task file confirming `TLBI VMALLE1` on every
activate.

**Description.** ADR-0028's §Simulation row 3 says the activation hook issues *"The borrow of `&AddressSpace<M>`
ends before `context_switch`"* and describes the switch target as *"T_b's instruction stream loads its first user-VA
via the swapped TTBR0_EL1"*. The row's "State post" cell says *"TTBR0_EL1 swapped to T_b's root; TLB flushed
(TLBI VMALLE1 in QemuVirtMmu::activate — more conservative than the 'no auto-flush' note in the original design…"*.
The simulation row text itself captures the correction in the State post cell, which is correct.

However, the §Negative bullet at line 149 says *"The §Simulation row 3 cell captures the current sequence verbatim"*
— this note implicitly acknowledges the corrected sequence is in the cell. The issue is that the Simulation row
header-level comment still reads *"activation-on-context-switch decision-point"* without a clear annotation that the
described sequence was updated post-acceptance. A first-time reader of only the row (not the §Negative bullet) would
not know the implementation diverged from the ADR's original intent. The correction is present but discoverable only
if both the simulation cell and the Negative section are read together.

**Suggested fix.** Add a brief in-cell note in row 3's "Switch target / observable effect" column calling out:
*"[Post-acceptance: implementation landed TLBI VMALLE1 more conservatively than the original ADR sketch; see
§Negative bullet below]"*. Alternatively, a Revision-notes rider on ADR-0028 consolidating the post-T-018 correction
would follow ADR-0025 §Rule 2 conventions. Minor because the information is present and correct — only the
discoverability is impacted.

---

#### D2b-006 — ADR-0035 §Decision drivers misstates its relationship to ADR-0028

**ADR location:** `docs/decisions/0035-physical-memory-manager.md:13`

**Description.** ADR-0035 §Context (line 13) says: *"The ADR-0028 slot is reserved for the address-space data
structure (per ADR-0027 §Context; no file today, opens with the second B3 ADR)"*. At the time ADR-0035 was accepted
(2026-05-09), ADR-0028 had not yet been authored. ADR-0028 was subsequently accepted on 2026-05-11. The statement
*"no file today"* is now stale — ADR-0028 does exist and is Accepted.

This is a minor factual inconsistency in the historical narrative. No decision content is affected.

**Suggested fix.** Revision-notes rider on ADR-0035 noting that ADR-0028 was subsequently accepted on 2026-05-11,
resolving the "no file today" parenthetical.

---

#### D2b-007 — ADR-0029 §References contains a broken anchor link for the adr-0034-placeholder

**ADR location:** `docs/decisions/0029-initial-userspace-image-format.md:42`

**Description.** Line 42 reads:
```
[adr-0034-placeholder]: 0027-kernel-virtual-memory-layout.md
```

This link target is used in the §Decision outcome text (line 39) as *"the future [ADR-0034 (kernel-image section
permissions)][adr-0034-placeholder] placeholder's responsibility"*. The anchor resolves to
`0027-kernel-virtual-memory-layout.md` as a whole file — not to the specific §Dependency chain section of ADR-0027
that actually names ADR-0034. A reader following the link lands on ADR-0027 with no indication of where within it
to find the ADR-0034 placeholder discussion. ADR-0028 (line 200) correctly uses the pattern:
*"[ADR-0034 (kernel-image section permissions placeholder)][adr-0027 §Decision outcome]"* with no reference link
syntax, mentioning the exact section — more precise than ADR-0029's vague link.

**Suggested fix.** Change the reference to use a section anchor:
`[adr-0034-placeholder]: 0027-kernel-virtual-memory-layout.md#decision-outcome`

---

### Nit

#### D2b-008 — ADR-0021 §Revision notes refers to commit hashes `6c2e7a0`, `85581ab`, `3b8aa34`, `7eaa10a` but these are not verifiable in a public Git history view

**ADR location:** `docs/decisions/0021-raw-pointer-scheduler-ipc-bridge.md:117-121`

**Description.** The Revision-notes section cites specific commit SHAs for each revision step. This is good practice
per ADR-0025 §Rule 2 (riders should be dateable and auditable). However, those SHAs are not in the current repo's
history under the working-tree at commit `288ddb2` (they appear to be pre-squash commits). A reader attempting to
`git show 6c2e7a0` would get "unknown revision". This is a cosmetic issue — the narrative content of each rider is
self-explanatory without the SHAs — but the SHA citations' value is reduced.

**Suggested fix.** No immediate action required; document as known cosmetic issue. If squash rebases are common in
the workflow, future ADRs should cite the landing commit's SHA (the PR-merge commit) rather than the mid-PR SHAs.

---

#### D2b-009 — ADR-0026 §Revision notes 2026-05-07 rider is unusually long and mixes meta-process content with substantive ADR history

**ADR location:** `docs/decisions/0026-idle-dispatch-fallback.md:168-170`

**Description.** The 2026-05-07 §Revision notes rider in ADR-0026 spans roughly a quarter of the ADR's total
content (lines 168–170 but each line is very long). It discusses: (a) the retro-extraction of the simulation-table
discipline into the `write-adr` skill, (b) Propose+Accept single-commit landing reconciliation, (c) a citation of a
Track G code review finding. This meta-process narrative is useful context but makes ADR-0026 hard to scan for its
core *idle dispatch* decision. Per ADR-0025 §Rule 2: *"Riders are how implementation feedback enters the design
history"* — meta-process content about ADR governance is on the boundary of what a rider should carry.

**Suggested fix.** No change required; the content is technically append-only-policy-compliant. Optionally, future
ADRs with similar governance-reconciliation riders could add a `<!-- meta-process rider -->` HTML comment to enable
visual scanning.

---

#### D2b-010 — ADR-0027 §Simulation table uses a non-standard "half-open range" parenthetical inline mid-row

**ADR location:** `docs/decisions/0027-kernel-virtual-memory-layout.md:88`

**Description.** The Simulation row 1 "Action" cell contains the note: *"(range notation `[start..end]` is
half-open Rust-style throughout this ADR; `[64..73]` means indices 64, 65, …, 72 — 9 entries)"*. This is
a useful clarification but is embedded inside a table cell, making it awkward to read and potentially hidden from
readers who skim the row. The note applies to the entire ADR, yet appears only in the first row where a range
appears.

**Suggested fix.** Move the parenthetical to a standalone footnote or a brief preamble paragraph above the
Simulation table. Nit only.

---

### Praise

#### D2b-P1 — ADR-0025 itself demonstrates the rule it establishes

ADR-0025's §Decision outcome is fully self-referential: it defines the forward-reference contract and immediately
satisfies it by opening no un-grounded T-NNN references. The §Revision notes records a pre-Accept withdrawal of the
cool-down rule with detailed reasoning — exactly the kind of high-fidelity historical record the append-only
principle is meant to preserve. This ADR is a model for the governance-ADR pattern.

---

#### D2b-P2 — ADR-0026 §Simulation table is the finest example of the discipline in the entire set

The simulation table at `docs/decisions/0026-idle-dispatch-fallback.md:54-62` walks 7 steps through the exact
demo-boot state machine, shows that idle is never dispatched under Option B, and provides a direct proof of
correctness. The B1-smoke-regression incident (real hang) → root-cause (FIFO dispatching idle mid-IPC round) →
fix (dedicated idle slot) → formal simulation arc is a textbook retroactive-correctness proof. Other teams and
projects should study this as a pattern for ADR discipline when runtime failures surface design gaps.

---

#### D2b-P3 — ADR-0021 handles the "&mut self" residual hazard with unusual thoroughness

The discovery that even "only the parameters are raw-pointer" still leaves `&mut Scheduler` crossing the switch was
caught and documented within the same day, with the pre-accept vs. post-accept commit SHA timeline recorded
(revision notes: 2026-04-22, two entries). This level of self-auditing rigor — catching and documenting a flaw in
the ADR itself before it was marked Accepted — is commendable and directly contributes to the safety of UNSAFE-2026-0012
being correctly retired.

---

#### D2b-P4 — ADR-0035 PMM simulation table correctly anticipates and handles the "Reserved-vs-Allocated single-bit collapse" hazard

Row 2 of the PMM simulation table (`docs/decisions/0035-physical-memory-manager.md:68`) explicitly names the
security-relevant edge case: a caller passing a `PhysFrame` for a reserved region to `free_frame`. Rather than
treating this as an "in practice won't happen" condition, the ADR mandates a defensive scan of the reserved-ranges
list at `free_frame` time. This converts a silent bitmap corruption into a `PmmError::DoubleFree` return — a good
security-first instinct.

---

#### D2b-P5 — ADR-0029 §Revision notes demonstrates correct append-only discipline after a doc/code divergence

The 2026-05-16 rider in ADR-0029 (`docs/decisions/0029-initial-userspace-image-format.md:127-147`) records a
post-Accept ADR body edit that was a policy violation (in-place modification of illustrative byte literals in
§Decision outcome), then corrects it via a Revision-notes entry that: explains the discrepancy (documented `mov w0,
#42` vs. shipped `MOVZ x0, #2`), gives the correct bytes, names the canonical source of truth
(`bsp-qemu-virt/src/main.rs`), and confirms no decision content changed. This is exactly how ADR-0025 §Rule 2
expects factual corrections to be handled.

---

## Claims register

| ADR decision / claim | ADR file:line | Code to verify against |
|---|---|---|
| `Aarch64TaskContext` is 104 bytes; `d8–d15` deferred to Phase B | `0020:244`, `0020:304` | `bsp-qemu-virt/src/cpu.rs:303-326` — **CONTRADICTED: struct is 168 bytes; d8–d15 saved** |
| `ContextSwitch` trait safety contract covers `x19–x28, x29, x30, sp` on aarch64 | `0020:163-166` | `hal/src/context_switch.rs:18-23` — **PARTIAL: trait contract omits d8–d15** |
| `ipc_send_and_yield` / `ipc_recv_and_yield` are `&mut self` methods on `Scheduler` | `0019:171-181` | `kernel/src/sched/mod.rs:921,1026` — **DRIFT: now unsafe free functions per ADR-0021** |
| `TaskContexts<C>` is a separate struct with `contexts: [C::TaskContext; N]` | `0019:185`, `0020:258-262` | `kernel/src/sched/mod.rs:280` — **DRIFT: inlined directly into `Scheduler<C>` as `contexts` field** |
| `Scheduler<C>` struct: `ready`, `task_states`, `current`, `contexts` fields | `0019:156-160` | `kernel/src/sched/mod.rs:239-281` — **PARTIAL: also has `task_handles`, `task_address_space_handles`, `idle` per ADRs 0021/0026/0028** |
| ADR-0020 `context_switch` saves callee-saved registers; from aarch64 that is `x19–x28, x29, x30, sp` | `0020:163-166` | `bsp-qemu-virt/src/cpu.rs:372-405` — **CONTRADICTED: assembly also saves `d8–d15`** |
| Idle task lives in FIFO ready queue via `add_task` (Option A) | `0022:77-83` | `kernel/src/sched/mod.rs:274` — **SUPERSEDED by ADR-0026 (dedicated `idle: Option<TaskHandle>` slot)** |
| `register_idle` stores idle in `idle: Option<TaskHandle>`, never enqueued in `ready` | `0026:47-48` | `kernel/src/sched/mod.rs:274,555-558` — **CONFIRMED** |
| `SchedError::Deadlock` defensive return; `IpcError::PendingAfterResume` | `0022:73-84` | `kernel/src/sched/mod.rs:172-224` — **CONFIRMED** |
| `ipc_cancel_recv` reverses `Idle → RecvWaiting` in Deadlock path | `0032:42-44` | `kernel/src/ipc/mod.rs:482` — **CONFIRMED** |
| Identity-mapped bootstrap; `TTBR1_EL1` disabled via `EPD1=1` | `0027:52,57` | `bsp-qemu-virt/linker.ld:65-74` (`.boot_pt` section) — **CONFIRMED** |
| `MapperFlush` typed token with `#[must_use]` on `map`/`unmap` | `0027:69-70` | `hal/src/mmu/mod.rs` (not explicitly read but references from T-016 task confirm) — **PRESUMED CONFIRMED** |
| `AddressSpace<M>` wraps `M::AddressSpace` inline; `AddressSpaceArena<M>` per-type arena | `0028:53` | `kernel/src/mm/address_space.rs:78,204` — **CONFIRMED** |
| `CapKind::AddressSpace` + `CapObject::AddressSpace(AddressSpaceHandle)` | `0028:97-98` | `kernel/src/cap/mod.rs:57,98` — **CONFIRMED** |
| Raw flat binary; entry at offset 0 | `0029:36-37` | `kernel/src/obj/task_loader.rs:481-491` — **CONFIRMED** |
| Placeholder bytes `[0x40, 0x05, 0x80, 0x52, 0xc0, 0x03, 0x5f, 0xd6]` = `mov w0, #42; ret` | `0029:140-144` | `bsp-qemu-virt/src/main.rs:314` (`USERSPACE_IMAGE`) — **CONFIRMED** |
| Bitmap PMM, 4 KiB metadata for 128 MiB; hint pointer; safe-Rust body | `0035:47-58` | `kernel/src/mm/pmm.rs:108-183` — **CONFIRMED** |
| `free_frame` defensive scan for reserved ranges | `0035:68` (simulation row 2) | `kernel/src/mm/pmm.rs:479` — **CONFIRMED** |
| `Scheduler<C>` bridge is `unsafe fn` free functions taking `*mut Scheduler<C>` | `0021:35-44` | `kernel/src/sched/mod.rs:921,1026` — **CONFIRMED** |
| No `&mut` to `Scheduler<C>`, arenas, or `CapabilityTable` across `context_switch` | `0021:37` | `kernel/src/sched/mod.rs:393-473` (shared safety contract comment) — **CONFIRMED** |
| ADR-0030 (syscall ABI) and ADR-0031 referenced as future ADRs | `0027:19,26` | `docs/decisions/` — **NO FILES: 0030/0031 do not exist as placeholder or full ADRs** |
| EL-drop sequence in `boot.s`; `UNSAFE-2026-0016` as post-condition | `0024:50-55` | `bsp-qemu-virt/src/cpu.rs:135-138` (`current_el()` assertion in `QemuVirtCpu::new`) — **CONFIRMED** |
| `add_task` signature: `pub unsafe fn add_task(&mut self, cpu, handle, address_space_handle, entry, stack_top)` | `0019:169` (sketch) | `kernel/src/sched/mod.rs:320` — **PARTIAL: ADR-0019 shows `add_task(handle)` only; actual has `address_space_handle` (B3 addition) and `cpu` parameter; also is `pub unsafe fn` on `&mut self`** |

---

## ADR status table

| ADR | Title | Status | Does code agree? | Notes |
|---|---|---|---|---|
| 0019 | Scheduler shape | Accepted | Mostly — API sketch outdated | Three post-Accept structural changes (ADR-0021 bridge free functions; ADR-0026 idle slot; ADR-0028 address-space fields) not reflected in ADR body; riders present for T-008 doc only. See D2b-002. |
| 0020 | `ContextSwitch` trait and `Cpu` v2 | Accepted | Partially — context size/register set outdated | Struct is 168 bytes, not 104; `d8–d15` are saved, not deferred. Safety contract in `hal/src/context_switch.rs` also omits d8–d15. See D2b-001. |
| 0021 | Raw-pointer scheduler IPC-bridge API | Accepted | Yes | Bridge free functions match. Amendment rider for IRQ-handler frame present. |
| 0022 | Idle task and typed scheduler deadlock error | Superseded (idle-location axis) / Accepted (typed-error axis) | Yes for typed-error; superseded shape replaced | Correctly partially-superseded. ADR-0026's simulation table documents the regression. |
| 0023 | Cross-table capability revocation policy | Deferred | N/A | Placeholder body present; deferral conditions well-documented; no code references this ADR. |
| 0024 | EL drop to EL1 policy | Accepted | Yes | `boot.s` EL-drop + `QemuVirtCpu::new` `current_el()` assertion confirmed. |
| 0025 | ADR governance amendments | Accepted | Yes (normative/process only) | Rules are self-referential and correctly applied by later ADRs. Minor issue: ADR-0027 uses ADR-0030/0031 references without placeholder files (see D2b-003). |
| 0026 | Idle dispatch via separate fallback slot | Accepted | Yes | `idle: Option<TaskHandle>` field confirmed; `register_idle` confirmed; simulation table matches code. |
| 0027 | Kernel virtual memory layout | Accepted | Yes | `.boot_pt` section in `linker.ld` confirmed. ADR-0033/0034 explicitly named-but-not-opened. ADR-0030/0031 not as carefully signposted. |
| 0028 | Address-space data structure | Accepted | Yes | `AddressSpace<M>`, `AddressSpaceArena<M>`, `CapKind::AddressSpace`, `CapObject::AddressSpace(AddressSpaceHandle)` confirmed. TLB-flush behaviour corrected in §Negative per D2b-005. |
| 0029 | Initial userspace image format | Accepted | Yes | Raw-flat loader confirmed; byte-encoding corrected in Revision-notes. `USERSPACE_IMAGE` bytes confirmed at `bsp-qemu-virt/src/main.rs:314`. |
| 0032 | Endpoint rollback + `ipc_cancel_recv` | Accepted | Yes | `ipc_cancel_recv` in `kernel/src/ipc/mod.rs:482` confirmed; Deadlock path calls it per `SchedError::Deadlock` doc-comment. |
| 0035 | Physical Memory Manager | Accepted | Yes | `Pmm` struct, `PmmError`, `alloc_frame`, `free_frame` confirmed. Reserved-range defensive scan confirmed. |

---

## Numbering-gap note (0030, 0031, 0033, 0034)

**0033 — "Kernel high-half migration":** Deliberately named-but-not-yet-created placeholder, explicitly documented
in ADR-0027 §Dependency chain (lines 156-157): *"A future ADR will introduce the high-half kernel mapping when B5
userspace work surfaces the per-task TTBR0_EL1 swap requirement. The placeholder slot is reserved (per ADR-0025
§Rule 1, no T-NNN is opened today because no implementation work depends on it before B5). … the ADR-0033 file does
not exist until B5 surfaces the requirement."* Status: **intentionally empty; no action required.**

**0034 — "Kernel-image section permissions":** Deliberately named-but-not-yet-created placeholder, explicitly
documented in ADR-0027 §Dependency chain (line 158): *"A future ADR will introduce per-section permissions on the
kernel image… The placeholder slot is reserved (no T-NNN today; opens with the first B-phase task whose threat model
includes a kernel R/W of .text as a meaningful surface)."* Status: **intentionally empty; no action required.**

**0030 — "Syscall ABI":** Referenced in ADR-0027 §Context as *"ADR-0030 (syscall ABI) inherits the page-fault /
capability-grant story"* and §Decision drivers *"that ADR (currently reserved as ADR-0030 for syscall ABI)"*. Also
referenced in task files `T-015`, `T-019`, `phase-b.md`. **No placeholder file exists. No README index entry
exists.** Unlike ADR-0033/0034, there is no explicit "no file today; opens when…" language normalizing the absence.
Status: **undocumented reservation — recommend creating a Deferred placeholder file (see D2b-003).**

**0031 — "MMU follow-ups / ASID assignment":** Referenced only once in ADR-0027 §Context line 19: *"ADR-0031 /
future MMU follow-ups (ASID assignment, copy-on-write, huge pages) all build on the same layout."* **No placeholder
file exists. No README index entry exists.** Subject matter partially overlaps ADR-0033 (high-half, ASID) and
ADR-0009 §Open questions (huge pages). May have been absorbed into ADR-0033 conceptually.
Status: **undocumented reservation — intent unclear; may be superseded by ADR-0033 scope; recommend either creating
a Deferred placeholder or explicitly deprecating the slot reference in ADR-0027.**

**Why 0032 and 0035 fall out of sequence:** ADR-0032 was authored 2026-05-07 (B1 closure, endpoint rollback) and
ADR-0035 was authored 2026-05-09 (PMM design). ADRs 0033 and 0034 were reserved-but-not-yet-created slots; ADR-0028
(address-space, 2026-05-11) and ADR-0029 (image format, 2026-05-14) arrived after ADR-0032/0035. The numbering
reflects the order the decisions crystallised, not their topic grouping. This is acceptable under the MADR
append-only convention and the project's sequential-numbering policy — no irregularity in the ordering itself.

---

## Cross-track notes

The following items are flagged for cross-track reviewers:

1. **C6-hal (HAL track) — confirmed.** ADR-0020's `ContextSwitch` trait safety contract in
   `hal/src/context_switch.rs:18-23` omits `d8–d15` from the normative list of callee-saved registers. The C6-hal
   track noted this as a potential issue; this review confirms it is a real documentation gap (D2b-001). The code in
   `bsp-qemu-virt/src/cpu.rs` is correct (saves d8–d15); the trait-level contract is the gap.

2. **C5-kernel-sched (Scheduler track).** D2b-002's API-sketch drift (method vs. free function; missing
   `task_address_space_handles` field; missing `activate_address_space` parameter) should be cross-referenced
   against any findings in C5 about the scheduler's call-site discipline. No conflict is expected since ADR-0021
   and ADR-0028 are the authoritative sources for the evolved API.

3. **C2-kernel-mm (Memory management track).** ADR-0028's "activation-without-TLB-flush" note vs. shipped
   `TLBI VMALLE1` (D2b-005) should be reconciled with any C2 findings about the activation hook's TLB discipline.

4. **C4-kernel-task-loader.** ADR-0029's raw-flat format decision drives the loader; the `adr-0034-placeholder`
   broken anchor (D2b-007) means the link from ADR-0029 to ADR-0027 §Decision outcome does not target the specific
   section. No functional impact on the loader implementation.

---

## Coverage checklist

All 13 target ADR files read in full. Line counts verified.

- [x] `docs/decisions/0019-scheduler-shape.md` — 222 lines
- [x] `docs/decisions/0020-cpu-trait-v2-context-switch.md` — 326 lines
- [x] `docs/decisions/0021-raw-pointer-scheduler-ipc-bridge.md` — 153 lines
- [x] `docs/decisions/0022-idle-task-and-typed-scheduler-deadlock.md` — 193 lines
- [x] `docs/decisions/0023-cross-table-capability-revocation-policy.md` — 92 lines
- [x] `docs/decisions/0024-el-drop-policy.md` — 119 lines
- [x] `docs/decisions/0025-adr-governance-amendments.md` — 140 lines
- [x] `docs/decisions/0026-idle-dispatch-fallback.md` — 181 lines
- [x] `docs/decisions/0027-kernel-virtual-memory-layout.md` — 230 lines
- [x] `docs/decisions/0028-address-space-data-structure.md` — 200 lines
- [x] `docs/decisions/0029-initial-userspace-image-format.md` — 159 lines
- [x] `docs/decisions/0032-endpoint-rollback-and-cancel-recv.md` — 154 lines
- [x] `docs/decisions/0035-physical-memory-manager.md` — 208 lines

Total ADR lines reviewed: 2,377

Additional code files cross-checked:
- [x] `kernel/src/sched/mod.rs` (2,652 lines) — primary code for ADRs 0019/0021/0022/0026/0032
- [x] `bsp-qemu-virt/src/cpu.rs` (567 lines) — primary code for ADR-0020
- [x] `hal/src/context_switch.rs` (70 lines) — trait definition for ADR-0020
- [x] `kernel/src/mm/pmm.rs` (surveyed key symbols) — primary code for ADR-0035
- [x] `kernel/src/mm/address_space.rs` (surveyed key symbols) — primary code for ADR-0028
- [x] `kernel/src/cap/mod.rs` (surveyed key symbols) — capability enum for ADR-0028
- [x] `kernel/src/ipc/mod.rs` (surveyed key symbols) — `ipc_cancel_recv` for ADR-0032
- [x] `kernel/src/obj/task_loader.rs` (surveyed key symbols) — loader for ADR-0029
- [x] `bsp-qemu-virt/linker.ld` (surveyed `.boot_pt` section) — for ADR-0027
- [x] `docs/decisions/README.md` (71 lines) — ADR index for gap investigation
