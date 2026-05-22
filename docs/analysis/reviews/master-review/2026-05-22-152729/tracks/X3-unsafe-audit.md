# X3-unsafe-audit — unsafe ↔ audit-log reconciliation (master review, commit 288ddb2)

Reviewer lens: X3 (unsafe-audit reconciliation). Anchor commit: 288ddb2.
Inputs: this is a verification-and-extension of the **preliminary** reconciliation
in [`D5b-audits-reports.md`](D5b-audits-reports.md) plus the cross-track notes
routed here from C2 (kernel-mm), C4 (task-loader), C5 (kernel-sched), C7 (bsp),
and C8 (test-hal). Method: full read of `docs/audits/unsafe-log.md` (all 610
lines, entries UNSAFE-2026-0001 … 0027) and `docs/standards/unsafe-policy.md`;
ground-truth `rg` enumeration of every `unsafe` token across `kernel/`, `hal/`,
`bsp-qemu-virt/src/`, `test-hal/`; per-site read of every flagged location; and a
cross-tabulation of `Audit: UNSAFE-2026-NNNN` references in source against the
log. Read-only throughout; this file is the sole artefact written.

---

## Summary

**Counts (production + test source, excluding `target/`):**

| Metric | Count |
|---|---|
| Distinct `unsafe` **sites** (fn decls + impls + blocks; see note) | **130** |
| of which `unsafe fn` declarations | 23 (15 production, 4 sched-test, 4 = HAL/BSP trait-decl + impls counted once) |
| of which `unsafe impl Send/Sync` | 12 (8 production, 4 test) |
| of which `unsafe trait` | 0 |
| of which `unsafe extern` / `#[unsafe(naked)]` | 1 naked fn (`context_switch_asm`) |
| of which `unsafe {}` blocks | ~94 (production + test) |
| Audit-log entries total | **27** (UNSAFE-2026-0001 … 0027) |
| Log entries Active | 26 |
| Log entries Removed | 1 (UNSAFE-2026-0012) |
| Distinct audit IDs referenced in source | **27** (0001–0027; all resolve) |
| **Production** unsafe sites fully compliant (SAFETY + `# Safety` where needed + live `Audit:` tag + matching log entry) | all production sites **except `from_existing_root`** |
| Code unsafe with **NO** log entry (under-documented) | **5** (1 production, 4 test) |
| Log entries with **NO / stale** code site (over-claimed) | **0** |
| Append-only / amendment-discipline violations (ADR-0025-class) | **0** |

> **Note on the site count.** `rg -e '\bunsafe\b'` returns 299 *lines*, but that
> figure double-counts: it includes prose in `//!`/`///` doc comments, `// SAFETY:`
> comments that contain the word, and the policy/skill-quoting strings. The
> **130 figure counts actual `unsafe`-keyword language constructs** (fn decls,
> impls, blocks, the naked attribute) found by the four targeted greps. C5
> independently counted 71 `unsafe` tokens in `sched/mod.rs` alone (production +
> test) against 54 `// SAFETY:` blocks; that gap is expected (fn decls + impls +
> `# Safety` prose carry the keyword without being SAFETY-commented *blocks*).
> The reconciliation below is by *site identity*, not raw token count, so the
> exact token total is not load-bearing for any finding.

**Headline.** The log is in excellent shape: **all 27 entries map to real,
current code sites; zero are stale; zero have an append-only violation.** Every
production `unsafe {}` block and every audited `unsafe fn` carries a conforming
`// SAFETY:` comment with a live `Audit:` tag. The discipline is, as C5/C7/C2/C4
all independently found, well above the policy floor.

The reconciliation **confirms all five gaps** flagged by D5b/C8 and adds two
material clarifications the preliminary pass left open:

1. **(Confirmed, Major)** `QemuVirtAddressSpace::from_existing_root`
   (`bsp-qemu-virt/src/mmu.rs:125`) is an `unsafe fn` with a thorough `# Safety`
   doc but **no audit-log entry and no `Audit:` tag** anywhere in its safety
   argument. This is the single most serious finding.

2. **(Confirmed, Minor)** `FakeMmu::create_address_space`
   (`test-hal/src/mmu.rs:133`) is an `unsafe fn` trait impl with **no `# Safety`
   doc, no `// SAFETY:` comment, and no log entry**.

3. **(Confirmed, Minor — new clarification)** Two *more* trait-impl `unsafe fn`s
   share the same shape and were **not** flagged by D5b/C8:
   `QemuVirtMmu::create_address_space` (`bsp-qemu-virt/src/mmu.rs:151`, a
   one-line non-`# Safety` comment, no `Audit:` tag) and
   `FailingMapMmu::create_address_space` (`kernel/src/obj/task_loader.rs:1750`,
   has a 3-point `// SAFETY:` but no `# Safety` doc and no `Audit:` tag).

4. **(Confirmed, Nit)** Four test-only `unsafe impl Send/Sync` on `FakeCpu`
   (`kernel/src/sched/mod.rs:1261,1263`) and `ResetQueuesCpu` (`:1911,1913`)
   carry adequate `// SAFETY:` prose but **no `Audit:` tag and no log entry**.

5. **(Confirmed, Minor — routed to X1)** The four Miri integer-to-pointer cast
   sites are unmentioned in any audit entry; `phys_frame_kernel_ptr` has no entry
   (correctly — it is a safe cast). Soundness assessment routed to X1-security.

**The decisive new finding for items 2–4 — why CI does not catch them.**
D5b ("clippy-suppressable only because `missing_safety_doc` is presumably not
denied for test code") and C8 ("the CI gate … should catch but apparently does
not") both *guessed* at a lint-config gap. I verified the actual mechanism and it
is **not** a config gap:

- The workspace `Cargo.toml` sets `clippy::missing_safety_doc = "deny"`,
  `clippy::undocumented_unsafe_blocks = "deny"`, and
  `rust::unsafe_op_in_unsafe_fn = "deny"` (`Cargo.toml:35,42-43`).
- **All four crates opt in** via `[lints] workspace = true`
  (`bsp-qemu-virt/Cargo.toml:19-20`, `test-hal/Cargo.toml:16-17`,
  `hal/Cargo.toml:13-14`, `kernel/Cargo.toml:19-20`). There is **no
  `#[allow(missing_safety_doc)]` anywhere** in the tree.
- The reason the missing `# Safety` docs pass `deny` CI is a **documented clippy
  design property**: `missing_safety_doc` fires on a *trait declaration* and on
  *free / inherent* `unsafe fn`, but **not** on a trait-method *implementation*
  whose trait declaration already carries the `# Safety` section. The HAL trait
  decl `Mmu::create_address_space` (`hal/src/mmu/mod.rs:330-334`) has the
  `# Safety` section, so every `impl` of it (`FakeMmu`, `QemuVirtMmu`,
  `FailingMapMmu`) is exempt from the lint by clippy's own rules.
- `from_existing_root` is an *inherent* `unsafe fn`, so it **does** need a
  `# Safety` doc — and it has one (the lint is satisfied). What it lacks is the
  *audit-log entry / `Audit:` reference*, which **no lint enforces** (per
  unsafe-policy §3 the audit log is reconciled "periodically" against
  `cargo-geiger`, not in CI). `undocumented_unsafe_blocks` is satisfied at its
  call site (`main.rs:921`) because a `// SAFETY:` block is *present* — even
  though that block's `Audit:` tag points at the wrong entries (0010+0014).

**Net:** these are genuine **policy violations** (unsafe-policy §2 "`# Safety` …
`Audit:` reference"; §3 "every `unsafe` block has an audit entry"; §4 "`unsafe
impl` … same discipline"), but they are **not detectable by the current CI lint
set** — they require the manual quarterly audit-log reconciliation the policy
§Enforcement names. That is the structural reason they slipped through, and it is
itself worth recording (see X3-005).

**Verdict: reviewable, no release blocker.** One Major (missing log entry for an
`unsafe fn`), three Minor, one Nit, plus Praise. Severity counts: **Blocker 0 ·
Major 1 · Minor 3 · Nit 1 · Praise 3.**

---

## Reconciliation table

Production unsafe sites and their audit status. "SAFETY?" = conforming adjacent
`// SAFETY:` comment present (invariants + rejected-alt + audit ref). "# Safety?"
= rustdoc `# Safety` section present where required (— = not an `unsafe fn`, so
n/a). "Log match?" = the named audit entry's Location/Operation still matches the
code at 288ddb2.

| File:line | Kind | SAFETY? | # Safety? | Audit id | Log match? | Verdict |
|---|---|---|---|---|---|---|
| `bsp/console.rs:41` | `const unsafe fn new` | yes | yes | 0001 | yes | OK |
| `bsp/console.rs:51` | `unsafe impl Send` | yes | — | 0003 | yes | OK |
| `bsp/console.rs:58` | `unsafe impl Sync` | yes | — | 0004 | yes | OK |
| `bsp/console.rs:71` | block (MMIO r/w) | yes | — | 0005 | yes | OK |
| `bsp/cpu.rs:120` | `unsafe fn new` | yes | yes | 0015/0016 | yes | OK |
| `bsp/cpu.rs:175,230,248,265,274,282` | blocks (MRS/MSR/WFI/ISB) | yes | — | 0007/0015/0016 | yes | OK |
| `bsp/cpu.rs:213` | `unsafe impl Send` | yes | — | 0006 | yes (Amendment covers 2-field shape) | OK |
| `bsp/cpu.rs:222` | `unsafe impl Sync` | yes | — | 0006 | yes | OK |
| `bsp/cpu.rs:354` | `#[unsafe(naked)] context_switch_asm` | yes | yes | 0008 | yes (naked + naked_asm! confirmed) | OK (Praise) |
| `bsp/cpu.rs:412,416` | `unsafe fn context_switch` + block | yes | yes | 0008 | yes | OK |
| `bsp/cpu.rs:424,480` | `unsafe fn init_context` + block | yes | yes | 0009 | yes | OK |
| `bsp/cpu.rs:507,520,533,545,557` | blocks (CNTV writes / timer) | yes | — | 0015/0021 | yes | OK |
| `bsp/exceptions.rs:172,216` | blocks (`irq_entry` GIC + timer mask) | yes | — | 0020/0021 | yes | OK |
| `bsp/gic.rs:117` | `const unsafe fn new` | yes | yes | 0019 | yes | OK |
| `bsp/gic.rs:153` | `unsafe fn init` | yes | yes | 0019 | yes | OK |
| `bsp/gic.rs:258,271,286,298` | 4 private MMIO `unsafe fn` | yes | yes | 0019 | yes | OK |
| `bsp/gic.rs:158…383` | blocks (distributor/cpu-iface MMIO) | yes | — | 0019 | yes | OK |
| `bsp/gic.rs:311` | `unsafe impl Send` | yes | — | 0019 | yes | OK |
| `bsp/gic.rs:313` | `unsafe impl Sync` | yes | — | 0019 | yes | OK |
| `bsp/main.rs:136` | `unsafe impl<T> Sync StaticCell` | yes | — | 0010 | yes | OK |
| `bsp/main.rs:193` | `unsafe impl Sync TaskStack` | yes | — | 0011 | yes | OK |
| `bsp/main.rs:205,214` | `unsafe fn top` + block | yes | yes | 0011 (Amendment) | yes | OK |
| `bsp/main.rs:162` (`as_mut_ptr`) | inherent fn w/ block | yes | (helper) | 0013 | yes | OK |
| `bsp/main.rs:921-927` | block: **`from_existing_root` call** | yes (prose) | — | **0010+0014 (WRONG)** | tags do not cover this op | **see X3-001** |
| `bsp/main.rs` (≈40 publish/bridge blocks) | blocks | yes | — | 0001/0010/0011/0013/0014/0020/etc. | yes | OK |
| `bsp/main.rs:1299` (panic) | block (`Pl011Uart::new`) | yes | — | 0002 | yes | OK |
| `bsp/mmu.rs:125` | **`pub unsafe fn from_existing_root`** | **n/a (decl)** | **yes** | **NONE** | **no entry exists** | **X3-001 (Major)** |
| `bsp/mmu.rs:151` | `unsafe fn create_address_space` (trait impl) | **no** (1-line comment, no audit) | no (rides trait decl) | **NONE** | n/a | **X3-002 (Minor)** |
| `bsp/mmu.rs:187` | block (`activate` TTBR0/TLBI asm) | yes | — | 0023 | yes | OK |
| `bsp/mmu.rs:248,330` | blocks (`map`/`unmap` walk entry) | yes | — | 0025 | yes | OK |
| `bsp/mmu.rs:382` | `unsafe fn walk_and_install_leaf` | yes | yes | 0025 | yes | OK |
| `bsp/mmu.rs:398…518` | blocks (descriptor read/write) | yes | — | 0025 | yes | OK |
| `bsp/mmu.rs:464` | `unsafe fn walk_or_alloc_table` | yes | yes | 0025 | yes | OK |
| `bsp/mmu_bootstrap.rs:88` | `pub unsafe fn mmu_bootstrap` | yes | yes | 0022/0023/0024 | yes | OK |
| `bsp/mmu_bootstrap.rs:121,203,238` | blocks (PT writes / sysreg / TLBI+IC) | yes | — | 0022/0023/0024 | yes | OK |
| `bsp/boot.s` / `vectors.s` | asm (DAIF/EL-drop; vector table) | yes (file prose) | — | 0017 / 0020 | yes (named-label halt loop confirmed) | OK |
| `hal/cpu.rs:179` | block (`current_el` MRS) | yes | (fn is safe) | 0018 | yes | OK |
| `hal/mmu/mod.rs:335` | `unsafe fn create_address_space` (**trait decl**) | n/a | **yes** | (decl; covered per-impl) | — | OK (decl carries the contract) |
| `hal/context_switch.rs:50,64` | `unsafe fn` (trait decls) | n/a | yes | 0008/0009 (per impl) | — | OK |
| `kernel/sched/mod.rs:320` | `pub unsafe fn add_task` (+block :332) | yes | yes | 0009/0014 | yes | OK |
| `kernel/sched/mod.rs:516` | `pub unsafe fn register_idle` (+block :529,551) | yes | yes | 0014 (Amendment) | yes | OK |
| `kernel/sched/mod.rs:594` | `unsafe fn start_prelude` (+block :600) | yes | yes | 0014 (Amendment) | yes | OK |
| `kernel/sched/mod.rs:656` | `pub unsafe fn start` (+blocks :665-712) | yes | yes | 0008/0014 | yes | OK |
| `kernel/sched/mod.rs:750` | `pub unsafe fn yield_now` (+blocks) | yes | yes | 0008/0014 | yes | OK |
| `kernel/sched/mod.rs:921` | `pub unsafe fn ipc_send_and_yield` | yes | yes | 0008/0014 | yes | OK (see C5-005 wording nit) |
| `kernel/sched/mod.rs:1026` | `pub unsafe fn ipc_recv_and_yield` | yes | yes | 0008/0014 | yes | OK |
| `kernel/mm/pmm.rs:436` | block (`write_bytes` zero-fill) | yes | — | 0026 | yes | OK (Praise C2-012) |
| `kernel/mm/address_space.rs:640` | block (`create_address_space` call) | yes | — | 0026 | yes | OK |
| `kernel/mm/mod.rs:165` (`phys_frame_kernel_ptr`) | safe int→ptr cast (NOT unsafe) | n/a | n/a | none (correct) | — | OK (see X3-006) |
| `kernel/obj/task_loader.rs:664` | block (`copy_nonoverlapping`) | yes | — | 0027 | yes | OK (Praise C4-P3) |
| **Test-only sites** | | | | | | |
| `kernel/sched/mod.rs:1261,1263` | `unsafe impl Send/Sync FakeCpu` | yes | — | **NONE** | n/a | **X3-004 (Nit)** |
| `kernel/sched/mod.rs:1911,1913` | `unsafe impl Send/Sync ResetQueuesCpu` | yes | — | **NONE** | n/a | **X3-004 (Nit)** |
| `kernel/sched/mod.rs:1280,1288,1929,1946` | test `unsafe fn` (FakeCpu/ResetQueuesCpu `context_switch`/`init_context`) | yes | (ride trait decls 0008/0009) | (test) | n/a | OK-ish (test; ride trait `# Safety`) |
| `kernel/sched/mod.rs` (≈60 test blocks) | blocks (bridge tests) | yes | — | 0008/0014 etc. (test) | n/a | OK (Praise C5-P5) |
| `test-hal/mmu.rs:133` | `unsafe fn create_address_space` (impl) | **no** | **no** | **NONE** | n/a | **X3-002 (Minor)** |
| `test-hal/mmu.rs:243…524` | 14 test blocks (`create_address_space` calls) | yes | — | (test) | n/a | OK |
| `kernel/obj/task_loader.rs:1750` | `unsafe fn create_address_space` (FailingMapMmu) | partial (3-pt, no audit) | no | **NONE** | n/a | **X3-002 (Minor)** |
| `kernel/obj/task_loader.rs:939,1392,1485,1713,1720,1762,1830` | test blocks | yes | — | (test) | n/a | OK |

(Paths abbreviated: `bsp/` = `bsp-qemu-virt/src/`. The ≈40 BSP `main.rs` publish
blocks and the ≈60 sched-test / 14 test-hal / 7 task-loader-test blocks are
grouped — each was spot-checked and carries a `// SAFETY:` comment; none is an
additional under-documented site beyond those named.)

---

## Code unsafe with NO log entry (under-documented)

| # | Code site | File:line | Kind | `# Safety`? | `// SAFETY:`? | `Audit:` tag? | Severity |
|---|---|---|---|---|---|---|---|
| 1 | `QemuVirtAddressSpace::from_existing_root` | `bsp-qemu-virt/src/mmu.rs:125` | inherent `pub unsafe fn` | **yes** (97-127) | n/a (decl) — call site has one | **no** (call site cites 0010+0014, neither covers the op) | **Major (X3-001)** |
| 2 | `FakeMmu::create_address_space` | `test-hal/src/mmu.rs:133` | trait-impl `unsafe fn` | **no** | **no** | **no** | Minor (X3-002) |
| 3 | `QemuVirtMmu::create_address_space` | `bsp-qemu-virt/src/mmu.rs:151` | trait-impl `unsafe fn` | no (rides decl) | one-line non-conforming comment | **no** | Minor (X3-002) |
| 4 | `FailingMapMmu::create_address_space` | `kernel/src/obj/task_loader.rs:1750` | trait-impl `unsafe fn` (test) | no | partial (3-point, no audit ref) | **no** | Minor (X3-002, test) |
| 5 | `FakeCpu` + `ResetQueuesCpu` `unsafe impl Send/Sync` | `kernel/src/sched/mod.rs:1261,1263,1911,1913` | 4 × `unsafe impl` (test) | — | yes | **no** | Nit (X3-004) |

**Important scoping correction vs D5b.** D5b's preliminary "Code unsafe with NO
log entry" table named four rows and treated `QemuVirtMmu::create_address_space`
(the *real* BSP trait impl) as implicitly fine. It is **not** fully fine: like
its `FakeMmu` sibling it is an `unsafe fn` with no `# Safety` doc, a
non-conforming one-line comment, and no `Audit:` tag. It is lower-risk than the
`FakeMmu` case (its body is the real production constructor and its call site at
`kernel/src/mm/address_space.rs:640` *does* carry a full SAFETY block citing
UNSAFE-2026-0026), but for completeness it belongs in the same finding (X3-002).
This is the one substantive item the preliminary pass missed.

**`mmu_bootstrap` and the walk helpers are NOT under-documented.** D5b did not
claim they were, but to close the loop: `mmu_bootstrap` (`:88`),
`walk_and_install_leaf` (`:382`), and `walk_or_alloc_table` (`:464`) are all free
`unsafe fn`s and all carry proper `# Safety` sections with `Audit:` tags
(0022/0023/0024 and 0025 respectively). Confirmed by direct read.

---

## Log entries with NO / again-stale code site (over-claimed / stale)

**None.** All 27 entries reconcile:

- **26 Active entries** each resolve to a live code site at 288ddb2. Spot-verified
  the high-risk / heavily-amended ones directly: 0014's four Amendments name
  `start` / `start_prelude` / `register_idle` / the IPC-bridge + activation-hook
  sites, and all are present in `sched/mod.rs`; 0025's 2026-05-14 Amendment names
  the post-bootstrap `Mmu::map` path, present; 0026/0027's T-019 Amendments name
  `alloc_frame` zero-fill and `load_image` `copy_nonoverlapping`, both present.
- **UNSAFE-2026-0012** is correctly **Removed** (2026-04-22, `f9b72f8`) with the
  follow-up rider for `Scheduler::start`. No `&mut self` scheduler-bridge code
  remains (C5 confirmed `&mut self` survives only on `add_task`, which does not
  context-switch and is correctly *not* under 0012). No "Removed-but-present"
  residue.
- Every `Audit: UNSAFE-2026-NNNN` reference found in source (0001–0027) resolves
  to an existing log entry. There is **no dangling source reference** to a
  non-existent ID, and **no log ID without a source reference** (0012 is
  referenced 8× in the Removed/rider prose and ADR cross-refs, which is correct
  for a retired entry).

The "Pending QEMU smoke verification" statuses on 0019/0020/0021 (IRQ-take /
trampoline / deadline-arm paths) are **correctly still Pending** — the v1 demo
arms no deadline, so those code arms are genuinely unexercised. That is a
status-accuracy property, not a stale-entry problem; consistent with C7 and the
gate-reproduction trace.

---

## Amendment / append-only discipline issues (ADR-0025)

**None. The append-only discipline is exemplary — confirmed, not merely
asserted.** I read every Amendment and Status-change block in full:

- Every scope expansion is an **`Amendment (YYYY-MM-DD, commit SHA): <title>`**
  block appended at the entry's end, restating the additional
  location/operation/invariants/rejected-alternatives without editing the
  original body. 0014 carries **six** such Amendments (T-011, T-012, T-014,
  T-015, T-018 + the original) across five tasks and never rewrites its body —
  the canonical model.
- The two **deliberate in-place corrections** in 0017 (HCR_EL2 RMW rationale;
  GAS halt-loop syntax) are themselves handled *as Amendments* with an explicit
  "Discipline note for future readers" recording that the introducing-commit
  boundary (not merge-to-main) locks the body. This is the discipline working
  *correctly*, including a self-correction of an earlier in-place edit.
- 0015's "Note for casual readers" + 2026-04-23 Amendment (CNTPCT→CNTVCT register
  swap, EL-precondition tightening) preserves the superseded original and points
  the reader to the Amendment first. Correct.
- The 0026/0027 "new entry vs Amendment of 0001/0026" adjudications are explicitly
  reasoned against the `justify-unsafe` skill's audit-tag-scoping discipline (the
  operations differ on source/primitive/ownership-proof axes). Correct calls.
- The **mechanical-edit exemption** (unsafe-policy §3) is invoked nowhere in a way
  that touches a semantic field; the URL-rename sweep (`TyrneOS`→`Tyrne`) appears
  only in link targets. No semantic field of any entry was altered by a sweep.

No entry shows a rewritten Operation / Invariants-substance / Rejected-alternatives
/ Status field. **Zero ADR-0025-class violations.**

---

## Findings (by severity)

### Blocker

None.

### Major

#### X3-001 — `QemuVirtAddressSpace::from_existing_root` is an `unsafe fn` with no audit-log entry; its call site mis-attributes the unsafety to two unrelated entries

**File:line:** `bsp-qemu-virt/src/mmu.rs:125` (declaration); `bsp-qemu-virt/src/main.rs:921-927` (sole call site).

**Confirmation of D5b-001, with the attribution defect made precise.**
`pub unsafe fn from_existing_root(root: PhysFrame) -> Self` has a well-written
`# Safety` section (lines 97-127) whose contract is genuinely *distinct* from
`Mmu::create_address_space`'s: `create_address_space` requires a **zero-filled**
root; `from_existing_root` requires an **already-live, populated** root (it
wraps the bootstrap L0 frame `mmu_bootstrap` installed into `TTBR0_EL1`). That
distinctness is exactly why it is its own constructor — and exactly why it needs
its own audit entry. A full `rg` of `docs/audits/unsafe-log.md` for
`from_existing_root`, `wrap_bootstrap`, and the operation confirms **no entry
names it**. The next free sequence number is **UNSAFE-2026-0028**.

The call site's `// SAFETY:` block (`main.rs:909-920`) does carry an `Audit:`
line — but it reads `Audit: UNSAFE-2026-0010 (StaticCell pattern) +
UNSAFE-2026-0014 (momentary &mut to the just-initialised arena)`. Those two
entries cover the *surrounding* `StaticCell`/arena `&mut` mechanics, **not** the
`from_existing_root` operation (wrapping an already-live, non-zero-filled L0 root
without zero-fill). So the one place a reader would look for the constructor's
audit reference points them at two entries that say nothing about it. This is the
worst sub-case of an under-documented site: it *looks* audited but is not.

**Why it matters.** This is the only **production** `unsafe fn` in the entire tree
with no audit entry. It sits at the security-sensitive boot/MMU boundary
(installing the live translation root into a kernel object). unsafe-policy §2
requires the `# Safety` section to carry an `Audit:` reference; §3 requires every
`unsafe` region to have a log entry; the `justify-unsafe` skill's acceptance
criteria require both the log entry and the `Audit:` trailer. All three are
unmet. Because no CI lint reconciles the log (only the manual quarterly pass
does — see X3-005), this slipped through every PR gate.

**Suggested fix.** Open **UNSAFE-2026-0028** for `from_existing_root`. Operation:
"wrap an already-live, populated VMSAv8 L0 root frame into
`QemuVirtAddressSpace` without zero-fill." Invariants: (a) `root` is the
currently-live L0 frame established by `mmu_bootstrap` and installed as
`TTBR0_EL1`; (b) its 512 descriptors are correctly encoded with at least the
kernel-half mappings populated; (c) exactly one such frame exists per boot (the
bootstrap root — no aliased wrapper possible); (d) subsequent `Mmu::map`/`unmap`
on the result use the UNSAFE-2026-0025 walker invariants. Rejected alternatives:
routing the bootstrap root through `create_address_space` (rejected — that
contract demands a *zero-filled* root, which the live root is not). Then **add
`// Audit: UNSAFE-2026-0028.` to both** the `# Safety` doc (per §2) and the
`main.rs:921` call-site SAFETY block (replacing/supplementing the 0010+0014
attribution, which should be narrowed to the StaticCell/arena lines it actually
covers). Security-sensitive (boot + MMU) → second-reviewer per unsafe-policy
§Review.4. Soundness of the *contract itself* is routed to X1-security below.

**Severity rationale: Major (not Blocker).** The code is sound — the `# Safety`
contract is correct and the sole caller honours it (C7-P5/claims confirm
`mmu_bootstrap` populates the exact frame). This is an audit-trail completeness
defect on a security-relevant `unsafe fn`, not a memory-safety defect. It does
not block release but is the highest-priority audit fix.

### Minor

#### X3-002 — Three trait-impl `unsafe fn create_address_space` overrides lack `# Safety` docs, `Audit:` tags, and log entries; CI cannot catch this by clippy design

**File:lines:** `test-hal/src/mmu.rs:133` (`FakeMmu`);
`bsp-qemu-virt/src/mmu.rs:151` (`QemuVirtMmu`);
`kernel/src/obj/task_loader.rs:1750` (`FailingMapMmu`, test).

**Confirms and extends D5b-002 / C8-001.** All three implement the
`unsafe fn create_address_space` trait method. None carries a `# Safety` rustdoc
section; none carries an `Audit:` tag; none has a log entry:

- `FakeMmu` — no `# Safety`, **no `// SAFETY:` at all**, body is
  `FakeAddressSpace { root, mappings: HashMap::new() }` (no unsafe ops).
- `QemuVirtMmu` — no `# Safety`; a single non-conforming inline comment ("No
  allocation; the safety contract of the trait method covers …") that names no
  invariants-upheld / rejected-alts / audit-ref triple.
- `FailingMapMmu` (test) — a 3-point `// SAFETY:` that *does* explain the
  delegation but cites no audit ref; body forwards to `FakeMmu`'s impl.

**The CI-mechanism clarification (the part D5b/C8 guessed at).** I verified there
is **no lint-config gap and no `#[allow]`**. `clippy::missing_safety_doc =
"deny"` is active in all four crates. The reason these pass is that **clippy's
`missing_safety_doc` does not fire on a trait-method implementation** when the
trait *declaration* (`hal/src/mmu/mod.rs:330-334`) already has the `# Safety`
section — by clippy's own design. So C8's "the CI gate should catch but apparently
does not" is explained: it *cannot*, and that is expected clippy behaviour, not a
project misconfiguration. The policy violation (§2/§4) is real but is only
catchable by the manual quarterly reconciliation, not by lint.

**Why it matters.** unsafe-policy §2 ("every `unsafe fn` has a `# Safety`
section") and §4 ("`unsafe impl` … follow the same discipline") are written
unconditionally; the `justify-unsafe` acceptance criteria require a `# Safety`
section and an audit tag for `unsafe fn` with no trait-impl carve-out. A reviewer
auditing a *new* call site reads the impl's `# Safety` first; its absence sends
them up to the trait decl, which is a fidelity speed-bump for the fakes (whose
whole job is to mirror the contract).

**Suggested fix (two parts).** (1) **Policy decision the project must make:**
either (a) add a one-line clause to unsafe-policy §2/§4 stating that a trait-impl
`unsafe fn` inherits its trait-declaration's `# Safety` and need not repeat it
(codifying the clippy reality, the lower-friction option), or (b) require impls
to restate `# Safety` and treat the clippy gap as a known limitation closed only
by the quarterly pass. (2) **Regardless of (1):** these three impls (plus the
non-conforming `QemuVirtMmu` comment) should carry a conforming `// SAFETY:` and
an `Audit:` tag. The cleanest record is a **single log entry, UNSAFE-2026-0029**,
"`create_address_space` trait-impl construction (FakeMmu / QemuVirtMmu /
FailingMapMmu) — body performs no unsafe operation; unsafety is the trait-level
caller contract that `root` is page-aligned, exclusively-owned, zero-filled,"
covering all three impls. Route the policy decision and this entry's wording to
the maintainer; C8-001 already drafted suitable SAFETY prose for the `FakeMmu`
case.

#### X3-003 — The audit log has no policy on test-only `unsafe`, but policy + skill are written unconditionally; the gap should be resolved one way or the other

**Files:** `docs/standards/unsafe-policy.md` (§3, §4, Scope);
`.agents/skills/justify-unsafe/SKILL.md` (§Acceptance criteria).

**This is the cross-track question C5/C8 routed here, answered.** I searched the
policy, the skill, and the log preamble for any `#[cfg(test)]` / test-only
exemption. **There is none.** unsafe-policy §Scope says "The rules apply equally
in kernel, HAL, and userspace code"; §3 says "every `unsafe` block" without
qualification; §4 says `unsafe impl` "follow the same discipline"; the skill's
acceptance checklist has no test carve-out. The *only* mention of "test" in the
policy is the `miri` tooling line (§Tooling).

Yet in practice the project has **a large body of test-only unsafe that is not in
the log**: the 4 `unsafe impl Send/Sync` on `FakeCpu`/`ResetQueuesCpu`
(X3-004), the 4 sched-test `unsafe fn context_switch`/`init_context` impls, the
14 `test-hal` and 7 task-loader-test `create_address_space` call blocks, and the
~60 sched-test bridge blocks. None has a log entry, and that is almost certainly
the *intended* behaviour (logging every test double's `Send` impl would drown the
log). The discipline is therefore **implicit and undocumented** — exactly the
state C5/C8 flagged.

**Why it matters.** An implicit exemption is a latent inconsistency: a future
contributor reading the policy literally would either (a) add dozens of test-only
entries, bloating the log, or (b) conclude the existing test unsafe is
non-compliant. Either reading is defensible from the current text, which means
the text is underspecified.

**Suggested fix.** Add an explicit clause to unsafe-policy §3 (and mirror it in
the skill): test-only `unsafe` in `#[cfg(test)]` modules requires a conforming
`// SAFETY:` comment (already the norm and clippy-enforced via
`undocumented_unsafe_blocks`) but is **exempt from individual audit-log
entries**, *provided* the unsafe is confined to test doubles / harness code and
touches no production type. Production `unsafe` reachable from non-test builds
remains fully logged. This codifies what the project already does, keeps the log
focused on the real TCB, and removes the literal-reading ambiguity. (This is
D5b-006 option (b), which I concur is the correct project call.)

### Nit

#### X3-004 — Four test-only `unsafe impl Send/Sync` (`FakeCpu`, `ResetQueuesCpu`) have adequate SAFETY prose but no `Audit:` tag

**File:lines:** `kernel/src/sched/mod.rs:1261,1263` (`FakeCpu`); `:1911,1913` (`ResetQueuesCpu`).

Confirms D5b-006. Both pairs carry concise, correct `// SAFETY:` comments
(`FakeCpu` is a ZST marker; `ResetQueuesCpu` holds a `*mut IpcQueues` that the
single test thread exclusively owns). Neither carries an `Audit:` tag. Per §4
this is a (test-only) discipline gap. Under the X3-003 fix this becomes a
documented non-issue: the SAFETY comments stay, the `Audit:` tags are not
required for `#[cfg(test)]` doubles. **No code change needed if X3-003 is
adopted; otherwise add a single shared entry** "test-harness ZST/exclusive-owner
`unsafe impl Send/Sync`." Recorded as Nit because it is test-only and the safety
arguments are sound and present.

### Praise

#### X3-P1 — Append-only / amendment discipline is genuinely exemplary (verified, not assumed)

Reading all 27 entries with their Amendment chains in full: UNSAFE-2026-0014's
six Amendments span five tasks and two PRs without one in-place body edit;
0017's two corrections are themselves handled as Amendments with an explicit
discipline note that even self-corrects an earlier in-place edit; 0015 preserves
its superseded register-family text behind a reader-warning + Amendment. This is
the strongest application of ADR-0025 / unsafe-policy §3 in the repository and
should be the reference other audit logs are held to. (Concurs with D5b-P1.)

#### X3-P2 — Source-side `Audit:` cross-referencing is dense, accurate, and machine-reconcilable

Every one of the 27 audit IDs is referenced in source, module-level `//!`
comments map which entries cover each BSP file, and the only mis-attribution in
the entire tree is the X3-001 call-site (which cites real entries, just the wrong
ones for that operation). The cross-tabulation of `rg`-extracted source tags
against the log produced **zero dangling references and zero unreferenced live
entries**. This made the reconciliation fast and is well above the policy floor.
(Concurs with D5b-P2, C5 note 2, C7-P1.)

#### X3-P3 — The four highest-risk production unsafe surfaces are textbook-conformant

`context_switch_asm` (`#[unsafe(naked)]` + `naked_asm!` sole body + `extern "C"`
+ compile-time size guard, UNSAFE-2026-0008 — confirms the C5 cross-track ask and
C7-P2); the PMM zero-fill (`write_bytes`, UNSAFE-2026-0026 — five enumerated
invariants, four rejected alternatives, C2-012); the task-loader byte-copy
(`copy_nonoverlapping`, UNSAFE-2026-0027 — runtime-enforced non-overlap preflight,
C4-P3); and the 4-level page-table walker (UNSAFE-2026-0025 — index-bound
`debug_assert!`, leaf-written-last ordering). Each names invariants + rejected
alternatives + a live audit tag whose log body matches the code. These are the
sites where a defect would matter most, and they are the most carefully
documented.

---

## Cross-track notes (route soundness questions to X1-security)

These are *soundness* questions beyond X3's reconciliation remit; routed to
**X1-security** with the audit-trail facts X3 established:

1. **`from_existing_root` contract soundness (from X3-001).** X3 confirms the
   *audit-trail* gap (no entry). X1 should assess whether the **contract itself**
   is sound: the constructor wraps the live `TTBR0_EL1` root without zero-fill,
   relying on `mmu_bootstrap` having populated it. Confirm (a) the sole caller
   (`main.rs:923`) runs strictly *after* `mmu_bootstrap` returns; (b) no second
   `from_existing_root` / `create_address_space` ever wraps the same bootstrap
   frame (alias-freedom); (c) the `wrap_bootstrap` path
   (`kernel/src/mm/address_space.rs:814`) does not also need its own entry. C7's
   cross-track note (HAL-trait-fit) already asks the trait-fit reviewer to confirm
   `wrap_bootstrap` is the only non-`create_address_space` route to the bootstrap
   root; X1 should pair with that.

2. **Miri integer-to-pointer cast advisories (from D5b-003, C5-004).** Four sites
   emit Miri `int2ptr` advisories: `pmm.rs:378` (`alloc_frame` identity cast),
   `pmm.rs:874` + `task_loader.rs:871` (test `aligned_backing` helpers),
   `mm/mod.rs:168` (`phys_frame_kernel_ptr`). X3 confirms **none is named in any
   audit entry** and that this is *not* a log defect — `phys_frame_kernel_ptr` is
   a *safe* cast (only the deref at call sites is unsafe, correctly covered by
   0026/0027), so it needs no entry of its own. X1 should assess whether the
   `strict_provenance` / `with_exposed_provenance` migration (named in 0027's
   forward-note) is practical given the identity-mapping assumption, and whether a
   dated note belongs in the Miri report (D5b-003's suggested fix).

3. **Miri is not a CI gate (PRIMARY, from C5-004).** The entire soundness of the
   raw-pointer scheduler/IPC bridge (UNSAFE-2026-0008/0014) rests on a
   doc-comment "no `&mut` across the switch" contract whose only mechanical
   verifier is `cargo +nightly miri test`, run manually. X3 confirms the
   *audit-log* side is fully in sync (0014's Amendments name every bridge entry
   point), but the log's correctness is only as strong as the Miri runs behind it.
   X1 should carry K3-7 (Miri CI gate on `sched/` + `ipc/`) as a Phase-B exit
   prerequisite, consistent with the 2026-04-21 security review making
   UNSAFE-2026-0012 the #1 Phase-B blocker. **A future refactor that lets a
   momentary `&mut` escape its block would compile, pass non-Miri tests, and
   reintroduce 0012-class UB while every audit entry still looks correct** — the
   audit log cannot detect that class of regression; only Miri can.

4. **Test-double fidelity vs the unsafe contracts (from C8).** `FakeMmu` never
   returns `OutOfFrames`/`BlockMapped`; `VecFrameProvider` does not zero-fill.
   These are *fidelity* gaps, not audit-log gaps, but they mean the host tests
   that "verify" UNSAFE-2026-0025's rollback/error contracts exercise a more
   permissive shadow. X1/test-coverage should note that the 0025 unmap-path and
   the `cap_map` intermediate-`OutOfFrames` path (C2-006) have no faithful host
   test behind their "smoke-verified" / "host-tested" claims.

5. **`boot.s` halt-loop + `#[unsafe(naked)]` (housekeeping, from D5b/C5).**
   Confirmed at HEAD: `boot.s` uses the named-label form
   (`halt_unsupported_el: wfe ; b halt_unsupported_el`) matching 0017's
   2026-04-27 GAS-syntax-correction Amendment; `context_switch_asm`
   (`cpu.rs:354`) is `#[unsafe(naked)]` per §5a / 0008. No discrepancy; no X1
   action needed — recorded for completeness.

6. **The CI-cannot-catch-it structural gap (new, X3-005-class).** The deepest
   root cause behind X3-001/002/004 is that **no CI lint reconciles the audit log
   against the source** — `missing_safety_doc` is exempt on trait impls by design,
   `undocumented_unsafe_blocks` only checks that *a* SAFETY comment exists (not
   that its `Audit:` tag is correct or that a log entry exists), and the
   log-vs-source reconciliation is the *manual quarterly* pass (unsafe-policy
   §Enforcement). The three under-documented `create_address_space` impls and the
   mis-attributed `from_existing_root` call site all passed every PR gate for that
   reason. X1/infra should consider whether a lightweight CI check —
   "every `unsafe fn`/`unsafe impl`/`unsafe {}` with an `Audit:` tag references an
   ID that exists in the log, and every non-test `unsafe fn` carries an `Audit:`
   tag" — is worth adding, to move log-drift detection from quarterly to per-PR.
   This would have caught X3-001 at introduction.
