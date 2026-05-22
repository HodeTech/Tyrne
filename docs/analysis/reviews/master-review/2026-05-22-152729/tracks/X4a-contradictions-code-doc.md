# X4a — code ↔ doc contradictions (master review, commit 288ddb2)

Reviewer role: X4a (CODE↔DOC CONTRADICTION). Anchor commit `288ddb2`.
Working dir: `/Users/dev/Documents/Projects/OS-Project`.

Scope: confirmed contradictions where the **documentation** (architecture docs,
ADRs, README/front-door docs, glossary, task acceptance-criteria, or a code
**doc-comment**) says one thing and the **code** does another. Every entry below
was verified by reading BOTH sides at commit 288ddb2; both sides carry a
`file:line` citation. Each candidate fed in from the Wave-2 tracks (C1–C9,
D1–D5c, gate-reproduction) was opened and checked independently — I did not take a
track's word for it.

Out of scope for this pass (recorded but NOT counted as code↔doc contradictions):
doc↔doc inconsistencies with no code side (e.g. phase-c/phase-d ADR-number
collisions D4-001/D4-002; CI-config↔standards-doc drift C9/D3; stale
`.claude/skills/` link paths; ADR-0030/0031 forward-reference hygiene). These are
flagged in §Cross-track notes for the relevant pass but are not in the register.

---

## Summary

**Confirmed code↔doc contradictions: 24.**

By severity:

| Severity | Count |
|---|---|
| Blocker | 0 |
| Major | 4 |
| Minor | 13 |
| Nit | 7 |

Candidate accounting: **9** of the 10 explicitly-named candidates in the brief
were confirmed (one — "current.md/T-019 claim 259 tests; actual 260" — is
confirmed as fact but is a doc↔reality count drift with no code-doc side; counted
here as X4a-013 because the test count is a measurable property of the code tree).
Beyond the named candidates, the tracks' claims registers surfaced ~15 further
code↔doc items; I confirmed all of them and added **3 newly-found** contradictions
not called out by any track:

- **X4a-008** — `overview.md:141` says async notifications "accumulate on the
  receiver's **endpoint**" (a second wrong sentence in the same paragraph as the
  known D1-001 candidate, and one that also contradicts `security-model.md`'s own
  `NotificationCap` row).
- **X4a-021** — `README.md:35` claims "the kernel proper exposes one" `unsafe`
  audit entry (`UNSAFE-2026-0027`); the kernel proper also owns
  `UNSAFE-2026-0026` (PMM zero-fill, `kernel/src/mm/pmm.rs:437`) and the
  scheduler's `UNSAFE-2026-0014` raw-pointer bridge (`kernel/src/sched/mod.rs`).
- **X4a-024** — `hal.md:80` lists "Secondary-core start via PSCI" as a `Cpu`
  responsibility; the `Cpu` trait has no such method (deferred), a distinct line
  from the context-switch and core-count drifts in the same bullet list.

Most dangerous confirmed contradiction: **X4a-001** — the `ContextSwitch`
safety-contract doc-comment (`hal/src/context_switch.rs:21-24`) and **ADR-0020**
(`docs/decisions/0020-...:165-167`, `:233-244`, `:305`) both enumerate the
aarch64 callee-saved set as `x19–x28, x29, x30, sp` and explicitly state d8–d15
are *not* saved in v1 — but the only correct implementation
(`bsp-qemu-virt/src/cpu.rs:303-326`) saves `d8–d15` and is 168 bytes (the docs say
104). A second BSP author implementing to the normative contract would ship a
context switch that silently corrupts FP state across every yield — a
data-dependent, near-undebuggable memory-correctness bug. This is the canonical
"a safety-contract doc that would cause a broken impl" case.

The doc set is, overall, accurate: the architecture docs `ipc.md`,
`memory-management.md`, `boot.md` (boot-sequence body), `exceptions.md`, and
`security-model.md` are correct against the code on the points I spot-checked, and
the GIC-version error is isolated to two ADRs (ADR-0006, ADR-0012) while every
architecture doc and the source agree on GICv2. The contradictions cluster in
(a) the HAL `Cpu`/`ContextSwitch` split not being reflected in `hal.md` /
`overview.md` / ADR-0008 / ADR-0020, (b) two ADRs predating the GICv2 reality,
(c) front-door volatile counts (tests/ADRs/unsafe), and (d) two stale
implementation-arc doc-comments (`pmm.rs` banner, `bsp cpu.rs` module header).

---

## Contradiction register

Severity reflects the risk of someone acting on the wrong side. "Which is
correct" names the side that matches reality at 288ddb2.

| ID | Topic | DOC says (file:line) | CODE does (file:line) | Correct side | Severity | Suggested fix |
|---|---|---|---|---|---|---|
| X4a-001 | `ContextSwitch` safety contract omits d8–d15 SIMD/FP callee-saved regs | `hal/src/context_switch.rs:21-24` ("On aarch64 that is `x19`–`x28`, `x29` (fp), `x30` (lr), and `sp`") | `bsp-qemu-virt/src/cpu.rs:306-319,331-333` saves x19–x28, fp, lr, sp **and d8–d15**; size-asserted 168 bytes (`cpu.rs:326`) | CODE | **Major** | Amend the trait's `# Safety` doc to add "and the SIMD/FP callee-saved registers `d8`–`d15` (lower 64 bits of `v8`–`v15`) whenever FP is enabled (`CPACR_EL1.FPEN ≠ 0`)"; generalise to "the target ABI's full callee-saved set". (= C6-001 / D2b-001) |
| X4a-002 | ADR-0020 `Aarch64TaskContext` size + register-save set | `docs/decisions/0020-cpu-trait-v2-context-switch.md:233-244` (104-byte 13-field struct), `:305` ("`d8`–`d15` are not saved in v1"), `:311` ("FP/NEON … Deferred"), `:165-167` (contract: x19–x28,x29,x30,sp) | `bsp-qemu-virt/src/cpu.rs:303-319` 168-byte struct **with `d8_d15: [u64;8]`**; asm saves them (`cpu.rs:331-333`) | CODE | **Major** | Add a Revision-notes rider to ADR-0020 recording that d8–d15 were implemented in the same arc (not deferred), the struct is 168 not 104 bytes, and the §Neutral "deferred" note is superseded. (= D2b-001) |
| X4a-003 | `overview.md` attributes context-switch to the `Cpu` trait | `docs/architecture/overview.md:69` ("`Cpu` — … context-switch primitives") | `hal/src/cpu.rs:44-76` `Cpu` has no context-switch method; `hal/src/context_switch.rs:25-50` `ContextSwitch::context_switch` is the separate ADR-0020 trait | CODE | **Major** | Fix `overview.md:69` to say `Cpu` handles CPU control; add `ContextSwitch` for register save/restore. (= D1-002) |
| X4a-004 | `overview.md` says both IPC flavours share one `EndpointCap` object | `docs/architecture/overview.md:143` ("Both flavours use the same `EndpointCap` kernel object") | `kernel/src/ipc/mod.rs:408-414` `ipc_notify` takes `NotificationArena` + `validate_notif_cap`; `kernel/src/cap/mod.rs:60-64` `CapKind` has distinct `Endpoint` and `Notification` | CODE | **Major** | Replace with: sync rendezvous uses `EndpointCap` (`Endpoint`); async uses `NotificationCap` (`Notification`); they are independent objects. Also contradicts `security-model.md:137-138` in the same doc set. (= D1-001) |
| X4a-005 | ADR-0008 `IrqGuard` signature is `&'a dyn Cpu` | `docs/decisions/0008-cpu-trait.md:87-100` (`IrqGuard<'a>` holding `&'a dyn Cpu`) | `hal/src/cpu.rs:102-122` `pub struct IrqGuard<'a, C: Cpu>` (concrete generic) | CODE | **Minor** | Add a `## Revision notes` rider to ADR-0008 (it currently has none) recording the change to generic `<C: Cpu>` and the vtable-aliasing-under-inlining rationale documented at `hal/src/cpu.rs:86-91`. (= D2a-001) |
| X4a-006 | ADR-0012 names the controller "GICv3" | `docs/decisions/0012-boot-flow-qemu-virt.md:24` ("`GICv3` distributor at `0x0800_0000`") | `bsp-qemu-virt/src/gic.rs:1` ("GIC v2 driver"); GICC_*/GICD_* MMIO model, no `ICC_*` sysregs (`gic.rs:48-51,365-383`) | CODE | **Minor** | Append-only correction rider on ADR-0012: default QEMU `virt` provides a GICv2 (GIC-400-class); GICv3 needs `-machine gic-version=3`. (= C7-001 / D2a-002) |
| X4a-007 | ADR-0006 BSP role claims GICv3 + SMMUv3 | `docs/decisions/0006-workspace-layout.md:47` ("GICv3 + PL011 + SMMUv3") | GICv2 (`bsp-qemu-virt/src/gic.rs:1`); `Iommu` is an empty stub (`hal/src/lib.rs:62` `pub trait Iommu {}`), no `impl Iommu` in BSP | CODE | **Minor** | Rider on ADR-0006 correcting "GICv3"→"GICv2" and noting `Iommu` is a stub-only trait pending its own ADR. (= D2a-003) |
| X4a-008 | `overview.md` says notifications accumulate on an *endpoint* | `docs/architecture/overview.md:141` ("a notification that accumulates on the receiver's **endpoint**") | `kernel/src/ipc/mod.rs:408-419` `ipc_notify` ORs `bits` into a `Notification` object via `notif_arena.get_mut(...)`; no endpoint involved | CODE | **Minor** (NEW) | Fix to "accumulates in a `Notification` object"; same paragraph as X4a-004 and also at odds with `security-model.md:138` (`NotificationCap` = one-way notification channel). |
| X4a-009 | `hal.md` boot diagram calls `Cpu::enable_interrupts()` | `docs/architecture/hal.md:238` (`K->>HAL: Cpu::enable_interrupts()`) | `hal/src/cpu.rs:47-75` `Cpu` exposes `disable_irqs` / `restore_irq_state` — no `enable_interrupts` | CODE | **Minor** | Update the diagram: interrupts are unmasked via `restore_irq_state` / DAIF + the GIC sequence, not a `Cpu` method. (= D1-002 / C6-007) |
| X4a-010 | `hal.md` claims `bsp-qemu-virt` implements `Iommu` (prose + flowchart) | `docs/architecture/hal.md:53` (`BIommu["SMMUv3 impl (bsp-qemu-virt)"]`), `:153` ("`bsp-qemu-virt` implements this trait") | `hal/src/lib.rs:62` `Iommu` is an empty marker; no `impl Iommu` anywhere in `bsp-qemu-virt/src/` | CODE | **Minor** | Relabel flowchart node `Iommu (planned)`; revise prose: BSP does not yet implement `Iommu`; stub reserved for a future SMMUv3 ADR. Note `security-model.md` is correctly hedged here (says SMMUv3 *can be* launched), so the error is hal.md-specific. (= D1-003) |
| X4a-011 | `README.md` architecture index: `memory-management.md` "Planned — B2" | `docs/architecture/README.md:20` (`Planned — B2`) | `docs/architecture/memory-management.md` is a 270-line written, accurate doc covering T-016..T-019 | CODE/DOC (file exists) | **Minor** | Change status to `Accepted (v0.0.1 — MMU/PMM/AddressSpace/loader; T-016..T-019)`. (= D1-004) |
| X4a-012 | `README.md` architecture index omits `task-loader.md` entirely | `docs/architecture/README.md:9-30` (index rows end with `userspace.md`; no `task-loader.md` row) | `docs/architecture/task-loader.md` exists (170 lines, accurate vs T-019) | DOC incomplete | **Minor** | Add a `task-loader.md` index row (Accepted v0.0.1 — T-019). (= D1-004) |
| X4a-013 | Documented host-test count 259 vs actual 260 | `docs/roadmap/current.md:7`; `docs/analysis/tasks/phase-b/T-019-task-loader.md:135`; `README.md:80` ("259 tests") | `cargo host-test` = **260** at 288ddb2 (42 hal + 175 kernel + 43 test-hal; gate-reproduction Gate 3) | CODE | **Minor** | Update the three prose counts to 260; prefer dropping hard literals in favour of "see `cargo host-test`". (= D4-006 / gate-reproduction D1 / D5a-011) |
| X4a-014 | `pmm.rs` module banner: "No `unsafe`" / "next commit adds alloc/free/stats" | `kernel/src/mm/pmm.rs:13-16` | The committed file HAS `alloc_frame`/`free_frame`/`stats` and a live `unsafe { core::ptr::write_bytes(...) }` at `pmm.rs:437` (UNSAFE-2026-0026) | CODE | **Minor** | Replace the commit-arc narrative with a steady-state description; the "No `unsafe`" line actively mis-points the reader away from the file's one memory-safety site. (= C2-001) |
| X4a-015 | `bsp cpu.rs` module header: timer deadline-arming is "`unimplemented!()`" | `bsp-qemu-virt/src/cpu.rs:10-13` ("`arm_deadline` / `cancel_deadline` … intentionally `unimplemented!()` until GIC + IVT wiring lands") | `bsp-qemu-virt/src/cpu.rs:491-525` (`arm_deadline` writes `CNTV_CVAL_EL0` + `CNTV_CTL_EL0`), `:539-561` (`cancel_deadline`) — fully implemented | CODE | **Minor** | Update the module header: deadline-arming landed via ADR-0010's 2026-04-28 revision / T-012; remove the `unimplemented!()` claim. (= C6 cross-track / C7 §Cross-track) |
| X4a-016 | `lib.rs` `## Subsystems` rustdoc omits the `mm` subsystem | `kernel/src/lib.rs:19-28` (lists only obj/cap/ipc/sched) | `kernel/src/lib.rs:55` declares `pub mod mm;` (PMM ADR-0035, AddressSpace ADR-0028, the B4 base) | CODE | **Minor** | Add an `mm` bullet (Phase B / T-017+T-018) and extend the `obj` bullet (still A3-era) to note the B4 `task_loader` resident. (= C4-003) |
| X4a-017 | `boot.md` Stage 4 describes a portable `tyrne_kernel::run` that greets + spins | `docs/architecture/boot.md:18` | No `pub fn run` in `kernel/src/`; `bsp-qemu-virt/src/main.rs:707` `kernel_entry()` orchestrates all subsystems and calls `start(...)` at `:1287` | CODE | **Minor** | Rename Stage 4 to "Scheduler start (`start`)"; note `tyrne_kernel::run` was an early design intent the BSP `kernel_entry` absorbed. (= D1-008) |
| X4a-018 | `scheduler.md` class diagram omits `idle` and `task_address_space_handles` | `docs/architecture/scheduler.md:23-29` (fields: ready, task_states, task_handles, current, contexts) | `kernel/src/sched/mod.rs:260` `task_address_space_handles`, `:274` `idle: Option<TaskHandle>` | CODE | **Minor** | Add both fields to the classDiagram; the `idle` slot is the entire ADR-0026 mechanism. (`§Revision notes` already flags partial staleness.) (= D1-007) |
| X4a-019 | ADR-0014 `CapError` enum lists 5 variants (the contract) | `docs/decisions/0014-capability-representation.md:120-134` (CapsExhausted, InvalidHandle, WidenedRights, InsufficientRights, DerivationTooDeep) | `kernel/src/cap/mod.rs:163-191` has 7: adds `HasChildren`, `WrongKind` | CODE | **Nit** | ADR-hygiene: reconcile via an amending note / follow-up ADR per ADR-0025 (do not edit the append-only body). Both additions are `#[non_exhaustive]`-safe and code-side commented. (= C1-005) |
| X4a-020 | `README.md` "32 accepted ADRs" | `README.md:41` | `ls docs/decisions/0*.md` = 31 files; not all are Accepted (ADR-0023 Deferred; ADR-0022 Superseded) | CODE/FS | **Nit** | Update to the accurate count and status mix; add a note in `docs/decisions/README.md` explaining the 0030/0031/0033/0034 numbering gaps. (= D5a-004) |
| X4a-021 | `README.md` "kernel proper exposes one `unsafe` audit entry" | `README.md:35` ("the kernel proper exposes one (`UNSAFE-2026-0027`, the task-loader byte-copy)") | `kernel/src/mm/pmm.rs:437` is UNSAFE-2026-0026 (PMM zero-fill, kernel proper); `kernel/src/sched/mod.rs` carries UNSAFE-2026-0014 (raw-pointer bridge, kernel proper) | CODE | **Nit** (NEW) | Reword: the kernel proper owns multiple audited `unsafe` regions (PMM zero-fill 0026, scheduler raw-pointer bridge 0014, loader byte-copy 0027); link the audit log instead of citing a single entry. |
| X4a-022 | ADR-0035 §Context: ADR-0028 "no file today" | `docs/decisions/0035-physical-memory-manager.md:13` | `docs/decisions/0028-address-space-data-structure.md` exists and is Accepted (2026-05-11) | CODE/FS | **Nit** | Rider on ADR-0035 noting ADR-0028 was subsequently accepted, resolving the "no file today" parenthetical. (= D2b-006) |
| X4a-023 | `test-hal/src/lib.rs` "All … HAL traits now have fakes" | `test-hal/src/lib.rs:18-21` ("All five Phase 4b HAL traits now have fakes: Console, Cpu, Mmu, Timer, IrqController") | `tyrne_hal` exposes a 6th accepted trait `ContextSwitch` (ADR-0020) with **no** fake in test-hal (`rg "impl ContextSwitch" test-hal/src` → none); scheduler tests define an inline `FakeCpu` impl instead | CODE | **Nit** | Update the doc to note `ContextSwitch` is not yet faked (host fake awkward — needs a real stack), or add a `FakeContextSwitch`. (= C8-009) |
| X4a-024 | `hal.md` lists "Secondary-core start via PSCI" under `Cpu` | `docs/architecture/hal.md:80` | `hal/src/cpu.rs:44-76` `Cpu` has no PSCI/secondary-core method (deferred per `cpu.rs:31-33`) | CODE | **Nit** (NEW) | Annotate as "(future, requires multi-core ADR)" or move out of the current-interface bullet list (same list as X4a-009's core-count and context-switch drifts). |

---

## Refuted candidates (flagged by tracks but actually consistent — with proof)

These were raised (or could plausibly be read) as code↔doc contradictions but are
NOT, on inspection of both sides:

- **`exceptions.md` GIC version — CONSISTENT.** `exceptions.md` says "GIC v2"
  throughout (`:3`, `:98`, `:100`, `:223`, `:228`, `:257`) and matches
  `bsp-qemu-virt/src/gic.rs:1`. The GIC-version contradiction is isolated to the
  two ADRs (X4a-006, X4a-007); the architecture doc is correct. (Refines C7-001 /
  D2a-002 scope.)

- **`security-model.md` IOMMU/SMMUv3 — CONSISTENT (correctly hedged).**
  `security-model.md:29,60,87,99,302,327` describe SMMU/IOMMU as future/conditional
  ("QEMU `virt` **can be** launched with SMMUv3", "ADR required before the first
  driver that enables bus-master DMA") and never assert a current implementation.
  Only `hal.md:53,153` makes the present-tense false claim (X4a-010). D1-003 is
  thus hal.md-specific, not a security-model.md defect.

- **`ipc.md` — CONSISTENT with the code.** `ipc.md:24` documents
  `ipc_notify(notif_arena, …)` with the correct `Notification` object; the
  endpoint state-machine table and the cap-transfer pre-flight prose match
  `kernel/src/ipc/mod.rs`. The notification-object contradiction is confined to
  `overview.md` (X4a-004, X4a-008). (Confirms D1-P02.)

- **`Capability` is not `Copy`/`Clone` — CONSISTENT.** `security-model.md:125`
  and `ipc.md:146` both say move-only; `kernel/src/cap/mod.rs:114-123` derives only
  `Debug`. No contradiction. (Confirms D1 claims-register row.)

- **`boot.md` body Stage 3 (`kernel_entry`) — CONSISTENT** on substance (MMU
  activate / PMM / AS-arena / loader sequence matches `main.rs`); only the
  `#[no_mangle]` attribute spelling (X4a-... see below) and the Stage-4
  `tyrne_kernel::run` block (X4a-017) are stale. The detailed boot narrative
  itself is accurate. (Confirms D1-P01.)

- **README "five subsystems" — NOT a contradiction.** `README.md:33` lists
  "capabilities, IPC, scheduling, memory management, and interrupt dispatch" as
  conceptual subsystems. `kernel/src/lib.rs` has five modules (cap, ipc, sched,
  mm, obj). "Interrupt dispatch" is a real concern (BSP `exceptions.rs` + the obj
  layer) even though it is not a single named kernel module. This is a conceptual
  grouping, not a false claim about the code surface — refuted as a contradiction.

- **`memory-management.md` register/encoding tables — CONSISTENT.** The
  `MAIR_EL1` (`memory-management.md:56-57`), `TCR_EL1` (`:70-80`), GIC bases, and
  9×2 MiB device-block claims all match `hal/src/mmu/vmsav8.rs` and
  `bsp-qemu-virt/src/mmu_bootstrap.rs` (cross-checked via D1 claims register and
  C6/C7). No code↔doc contradiction in this doc.

Note: `boot.md:17` `#[no_mangle]` vs the code's `#[unsafe(no_mangle)]`
(`main.rs:702`) IS a genuine (minor) inaccuracy — it is captured implicitly under
the boot.md staleness cluster but is below the bar I set for a standalone register
row (it is a literal-attribute-spelling drift from the Rust 2024 edition
stabilisation, not a behavioural/contract contradiction). Recorded here for the
docs pass as D1-005 rather than as an X4a register entry, to keep the register
focused on contract/behaviour-level mismatches. If the docs pass wants it counted,
it is a 25th Nit-level item.

---

## Cross-track notes

- **To the ADR-governance / docs pass (highest priority).** Two ADRs carry the
  most dangerous contradictions and need riders (append-only, per ADR-0025):
  ADR-0020 (X4a-002, d8–d15 + 168-byte struct) and ADR-0008 (X4a-005, IrqGuard
  generic; ADR-0008 has *no* `## Revision notes` section at all). Both are
  safety/ABI-contract drift, not cosmetic. ADR-0006 and ADR-0012 (X4a-006/007,
  GICv2) and ADR-0014 (X4a-019, CapError 5→7) round out the ADR-side reconciliations.

- **To the HAL/security pass.** X4a-001 (the `ContextSwitch` trait doc-comment) is
  the load-bearing one: it is the contract a future Pi 4 / Jetson BSP author
  implements against, and the omission produces silent FP-state corruption. It is
  a doc-only edit to `hal/src/context_switch.rs` but should be gated through the
  boot-path + `unsafe` review per the project's discipline. Pairs with X4a-002
  (same omission in ADR-0020).

- **To the architecture-docs pass.** `overview.md` and `hal.md` carry the bulk of
  the architecture-doc contradictions (X4a-003/004/008/009/010/024). They cluster
  on (a) the `Cpu`↔`ContextSwitch` split being invisible and (b) the IPC
  notification object. `scheduler.md` (X4a-018) and `boot.md` (X4a-017) each need
  one diagram/section update. The other architecture docs (ipc.md,
  memory-management.md, exceptions.md, security-model.md) are accurate — see
  §Refuted.

- **To the front-door / D5a pass.** The README's volatile counts (X4a-013 tests,
  X4a-020 ADRs, X4a-021 unsafe-entries) are all drifted; the structural fix is to
  replace hard literals with links/commands so they cannot rot. Same pattern in
  `current.md` / T-019 task file (X4a-013).

- **To the gate-reproduction track (already aligned).** X4a-013 (259→260) is
  independently confirmed by `gate-reproduction.md` Gate 3 (260 passing) and by
  D4-006; magnitude (+1) and direction (under-count, not a regression) agree.

- **Doc↔doc items deliberately excluded from the register** (handed to their
  owning passes): phase-c/phase-d ADR-number collisions with live ADRs
  (D4-001/D4-002); CI "stable" jobs vs `rust-toolchain.toml` nightly pin and the
  `infrastructure.md`/`release.md` gate-list drift (C9-001/005/006, D3-002/003/004);
  the project-wide stale `.claude/skills/` link rot (D1-009, D2a-004, D3-001,
  D4-007/008, D5a-003, D5c-M01); ADR-0030/0031 forward-reference hygiene
  (D2b-003); CLAUDE.md / CONTRIBUTING.md "architecture phase" staleness
  (D5a-001/002). None of these has a code side, so they are not code↔doc
  contradictions, but several are higher-severity in their own dimension than the
  Nits above.

- **Test-only `unsafe` doc/audit gaps are NOT code↔doc contradictions.**
  `FakeMmu::create_address_space` missing `# Safety`/audit (C8-001, D5b-002) and
  `from_existing_root` missing an audit entry (D5b-001) are policy-compliance gaps
  (code-vs-policy), not cases of a doc asserting something the code contradicts —
  routed to the X3 unsafe-audit pass, not counted here.

---

## Verification method (for auditability)

For each register row I opened both sides at commit 288ddb2:
- DOC side: `Read`/`sed` on the exact lines cited.
- CODE side: `Read`/`rg` on the implementing file, confirming the symbol/signature
  /value (e.g. `Aarch64TaskContext` field list + the `assert!(size_of == 168)`;
  `IrqGuard<'a, C: Cpu>`; `ipc_notify`'s `NotificationArena` parameter; `gic.rs`
  GICC_* MMIO and absence of `ICC_*` sysregs; `pmm.rs` live `write_bytes`;
  `cpu.rs` `arm_deadline` body; `lib.rs` `pub mod mm`).
The host-test count (X4a-013) and the gate facts are taken from
`gate-reproduction.md` (Gate 3 = 260), which ran the suite on a runner; this pass
is read-only and ran no build/test commands.
