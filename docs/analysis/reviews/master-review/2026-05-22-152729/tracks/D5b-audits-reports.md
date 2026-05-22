# D5b-audits-reports — unsafe-log + reports (master review, commit 288ddb2)

## Summary

All 8 files read in full. The unsafe-log is thorough, append-only-discipline is generally excellent, and the cross-file `Audit:` tagging in source is dense and consistent. Three under-documented unsafe sites were found (one Major, one Minor, one Nit); the reports carry expected staleness from the snapshots they capture but two figures need annotation. The most pressing finding is the lack of an audit-log entry for `QemuVirtAddressSpace::from_existing_root` — an `unsafe fn` with correct `# Safety` doc but no `UNSAFE-YYYY-NNNN` tag anywhere in its safety argument or in the log. The Miri integer-to-pointer-cast warnings confirmed by gate-reproduction are unmentioned in either the 2026-04-23 Miri report or any subsequent document, creating a silent gap in the paper trail. The `FakeMmu::create_address_space` issue flagged by C8 is confirmed: it is an `unsafe fn` implementing an `unsafe`-trait-method with neither a `# Safety` doc comment nor an `Audit:` tag, and no entry in the log.

**Verdict:** Reviewable, no release blockers. One Major finding (missing log entry for `from_existing_root`), two Minor findings, three Nit-level gaps, and three Praise notes.

**Severity counts:** Blocker: 0 | Major: 1 | Minor: 2 | Nit: 3 | Praise: 3

**Log-to-code mismatches found:** 2 (code unsafe with no log entry); 0 (log entry with no matching code).

---

## Findings (by severity)

### Blocker

None.

---

### Major

#### D5b-001 — `QemuVirtAddressSpace::from_existing_root` is an `unsafe fn` with no audit-log entry

**File:line:** `bsp-qemu-virt/src/mmu.rs:125`

**Description.** `pub unsafe fn from_existing_root(root: PhysFrame) -> Self` is an `unsafe fn` with a well-written `# Safety` section (lines 97–127) explaining that the caller must supply a currently-live VMSAv8 L0 translation table. The only call site (`bsp-qemu-virt/src/main.rs:923`) has a SAFETY comment that attributes the surrounding block to UNSAFE-2026-0010 and UNSAFE-2026-0014; neither entry covers this constructor. Searching the entire audit log confirms: no UNSAFE-2026-XXXX entry names `from_existing_root`, its file `bsp-qemu-virt/src/mmu.rs`, or its operation (wrapping an already-live L0 root frame without zero-fill). This violates unsafe-policy.md §3 ("Every `unsafe` block has an audit entry") and §2 ("unsafe fn requires `# Safety`… `Audit:` reference").

The function was introduced alongside T-018 / T-019 address-space work (the `from_existing_root` constructor is mentioned in the ADR-0028 context), which is when UNSAFE-2026-0022 through UNSAFE-2026-0027 were added. The omission is likely a review oversight rather than deliberate.

**Suggested fix.** Open a new audit entry UNSAFE-2026-0028 (next in sequence) for `from_existing_root`. Operation: wrapping an already-live L0 VMSAv8 root frame into `QemuVirtAddressSpace` without zero-fill. Invariants: (a) `root` is a currently-live, correctly-populated L0 frame established by `mmu_bootstrap` and installed as `TTBR0_EL1`; (b) only one such frame exists per kernel boot (no aliased `QemuVirtAddressSpace` possible for the bootstrap root); (c) subsequent map/unmap calls through the resulting object use the same page-table walker invariants as UNSAFE-2026-0025. Add `// Audit: UNSAFE-2026-0028.` to the call site's SAFETY comment and to the function's `# Safety` section.

---

### Minor

#### D5b-002 — `FakeMmu::create_address_space` is an `unsafe fn` impl with no `# Safety` doc and no audit tag

**File:line:** `test-hal/src/mmu.rs:133`

**Description.** The HAL `Mmu` trait declares `create_address_space` as `unsafe fn` with a `# Safety` section (hal/src/mmu/mod.rs:330–335). The concrete trait implementation in `test-hal/src/mmu.rs:133` is:

```rust
unsafe fn create_address_space(&self, root: PhysFrame) -> FakeAddressSpace {
    FakeAddressSpace { root, mappings: HashMap::new() }
}
```

This has no `/// # Safety` doc comment and no `// Audit:` tag. Unsafe-policy.md §2 requires every `unsafe fn` to carry a `# Safety` rustdoc section; §3 requires an audit-log entry or at minimum an `Audit:` tag. Fourteen call sites in the same file carry `// SAFETY: FakeMmu::create_address_space does not dereference `root`...` comments — the reasoning exists at the call sites but not at the `unsafe fn` declaration itself, which is where a reader encounters the unsafety first. The `FailingMapMmu::create_address_space` in `kernel/src/obj/task_loader.rs:1750` similarly forwards to the FakeMmu impl with a three-point SAFETY comment but still cites no audit tag.

This is test code and the function body has zero unsafe operations (it simply stores `root`); the unsafety is caller-side contractual. However, the missing `# Safety` doc and missing `Audit:` tag are clippy-suppressable only because `missing_safety_doc` is presumably not denied for test code. Regardless, the policy is clear.

**Suggested fix.** Add a `/// # Safety` section to `FakeMmu::create_address_space` explaining that: (a) the function itself performs no unsafe operations; (b) the `unsafe` stems from the trait-level contract that `root` must be exclusively-owned + page-aligned + zero-initialised, which in test code is structurally guaranteed by the test fixtures; (c) misuse in production code is prevented by the trait being gated to BSP implementors. Add `// Audit: UNSAFE-2026-0028` (or a dedicated test-scope sub-entry under an existing entry) to the declaration, or open a test-only entry UNSAFE-2026-0029. The C8-test-hal review track should be cross-referenced here.

---

#### D5b-003 — Miri integer-to-pointer cast warnings unmentioned in the 2026-04-23 Miri report and in no subsequent document

**File:line:** `docs/analysis/reports/2026-04-23-miri-validation.md` (the report itself; code: `kernel/src/mm/pmm.rs:378`, `kernel/src/mm/pmm.rs:874`, `kernel/src/obj/task_loader.rs:871`, `kernel/src/mm/mod.rs:168`)

**Description.** The 2026-04-23 Miri report covers 111 tests passing under Stacked Borrows and contains a prescient "What this does NOT validate" section. It says nothing about integer-to-pointer cast warnings because none existed yet (PMM and task-loader `unsafe` was not written until T-017 / T-019, months later). Gate-reproduction (`gate-reproduction.md`, Gate 5) now documents that Miri emits advisory `this program is using integer-to-pointer casts` warnings at four sites:

- `kernel/src/mm/pmm.rs:874` — `aligned_backing` test helper
- `kernel/src/mm/pmm.rs:378` — `Pmm::alloc_frame` identity-map cast (`pa_usize as *mut u8`)
- `kernel/src/obj/task_loader.rs:871` — `aligned_backing` test helper in task-loader
- `kernel/src/mm/mod.rs:168` — `phys_frame_kernel_ptr` (`frame.as_usize() as *mut u8`)

These are advisory, not errors. But no report or audit entry names them. The UNSAFE-2026-0026 and UNSAFE-2026-0027 entries do not mention the Miri warning; the `phys_frame_kernel_ptr` helper (`kernel/src/mm/mod.rs`) has no audit entry at all (the cast is in a safe function whose doc-comment says "the `as *mut u8` cast is infallible Rust; only the *dereference* at the call site is `unsafe`"). The gate-reproduction report records them correctly, but the canonical ongoing tracking of Miri health belongs in the miri-validation report or a successor.

The advisory means Miri cannot fully track pointer provenance through these sites, which is exactly the `strict_provenance` migration path the UNSAFE-2026-0027 Amendment notes. Until that migration lands, the current state should be explicitly acknowledged somewhere in the audit trail.

**Suggested fix.** Append a dated follow-up note to `2026-04-23-miri-validation.md` (or create a successor `2026-05-21-miri-validation.md`) naming the four integer-to-pointer cast sites, confirming they are advisory-only under Miri, and cross-referencing the `phys_frame_kernel_ptr` helper + UNSAFE-2026-0026 / UNSAFE-2026-0027's future strict-provenance migration note. Optionally add a sentence to those two audit entries' Amendment chains. This is a paper-trail gap, not a code correctness issue.

---

### Nit

#### D5b-004 — Coverage reports show stale test counts; no report covers the T-019 era

**File:line:** `docs/analysis/reports/2026-04-27-coverage-rerun.md:6` (headline numbers); `docs/analysis/reports/2026-04-23-miri-validation.md:7`

**Description.** The most recent written coverage report (`2026-04-27-coverage-rerun.md`) shows 143 tests and 96.33% workspace regions — both stale at commit 288ddb2 (260 tests, 96.26% regions per gate-reproduction). The Miri report shows 111 tests. These are point-in-time baselines, not claims about HEAD; per the review brief, dated baselines are acceptable as historical snapshots. However:

1. The coverage-rerun's "Next measurement" guidance (`docs/analysis/reports/2026-04-27-coverage-rerun.md:80`) said "re-run at T-011 closure" — T-017, T-018, T-019, and several other tasks have since landed, each with new unsafe and tests, but no coverage report was produced for any of them. The B2-closure, B3-closure perf reports mark phase boundaries but there is no corresponding coverage snapshot.
2. The `hal/src/mmu.rs` row in the 2026-04-27 report says "40.82% — no production impl yet" (a 2026-04-23 figure copied forward). Gate-reproduction now shows `hal/src/mmu/mod.rs` at 67.74% — a meaningful improvement once the MMU trait grew implementations and tests in T-016 and later. The row is now misleading for a reader who expects the report to reflect T-019-era state.

**Suggested fix.** Create a `2026-05-21-coverage-rerun.md` report using the gate-reproduction numbers (260 tests, 96.26% regions), updating the per-file table, and noting that `hal/src/mmu/mod.rs` improved from 40.82% to 67.74%. Mark this as the new B3-closure coverage baseline. This is an administrative gap, not a correctness issue.

---

#### D5b-005 — Perf baselines do not note test-count or coverage context

**File:line:** `docs/analysis/reports/perf-baseline-2026-05-08-post-pr-19-pre-adr-0027.md`, `docs/analysis/reports/perf-baseline-2026-05-08-post-t-016-mmu-activated.md`, `docs/analysis/reports/perf-baseline-2026-05-09-B2-closure.md`, `docs/analysis/reports/perf-baseline-2026-05-14-B3-closure.md`

**Description.** All four perf reports are structurally identical and well-formed: they record inputs (git HEAD, build profile, QEMU version, host uname), methodology, and raw samples with percentiles. The nit is that none cross-references the coverage or Miri baseline at the same commit, so a reader comparing perf snapshots across milestones cannot quickly verify whether a perf improvement was accompanied by reduced test coverage. The B2-closure report uses `release` profile (correct for the reported ~4.6 ms p50) while the earlier two reports use `debug` profile (resulting in ~6–9 ms p50) — this comparison is not highlighted in any of the four files themselves.

For the B3-closure report (commit `6334881`): the p50 of ~11.9 ms is roughly 2.5× the B2 release p50. This is expected (T-019 added `load_image` calls including page-table walks and PMM allocations on every boot), but there is no sentence in the B3-closure report acknowledging the increase or attributing it to T-019's boot-path additions.

**Suggested fix.** Add a one-paragraph "Context" section to each perf report naming: (a) what changed since the prior baseline (e.g., "T-016 activated the MMU; boot adds ~1.5 ms of page-table setup"), and (b) test-count + coverage percentage at the same commit. This is cosmetic but aids future readers who need to understand why numbers changed.

---

#### D5b-006 — FakeCpu and ResetQueuesCpu `unsafe impl Send/Sync` lack Audit tags

**File:line:** `kernel/src/sched/mod.rs:1261–1263`, `1911–1913`

**Description.** `FakeCpu` (lines 1261–1263) and `ResetQueuesCpu` (lines 1911–1913) each have `unsafe impl Send for ... {}` and `unsafe impl Sync for ... {}` with `// SAFETY:` comments that are adequate. However, neither has an `// Audit: UNSAFE-YYYY-NNNN` tag. Unsafe-policy.md §3 requires an audit-log entry for every unsafe region, including `unsafe impl`. The policy §4 ("unsafe impl follows the same discipline") is explicit.

These are test-only types in a `#[cfg(test)]` module. The safety arguments are simple and well-stated. There may be a reasonable project convention that test-only `unsafe impl`s on trivially-safe ZST types are exempt from the full log. If so, that exemption should be documented in `unsafe-policy.md`; currently it is not.

**Suggested fix.** Either: (a) add these four `unsafe impl`s to the audit log (possibly a single entry covering all four test-harness marker impls); or (b) add a clarifying footnote to `unsafe-policy.md §3` stating that test-only `unsafe impl Send/Sync` on ZST + trivially-thread-safe types in `#[cfg(test)]` blocks are exempt from individual log entries, with a blanket justification in the policy document itself. Option (b) is likely the correct project call; option (a) is the strictly policy-compliant path today.

---

### Praise

#### D5b-P1 — Amendment discipline is exemplary

The amendment chain for UNSAFE-2026-0006, UNSAFE-2026-0011, UNSAFE-2026-0014, UNSAFE-2026-0015, UNSAFE-2026-0017, UNSAFE-2026-0019, UNSAFE-2026-0020, UNSAFE-2026-0021, UNSAFE-2026-0025, UNSAFE-2026-0026, and UNSAFE-2026-0027 demonstrates first-rate append-only discipline. Each amendment is dated, SHA-tagged, scoped to a concrete change, and re-states why the original invariants still hold or how they are extended. UNSAFE-2026-0014 accumulates seven amendments spanning five tasks and two PRs without once editing the original body — a model for future contributors.

---

#### D5b-P2 — `Audit:` cross-referencing in source is thorough and consistent

Every audited `unsafe` block in the production codebase carries an `// Audit: UNSAFE-2026-XXXX` tag. Module-level `//!` doc comments in `bsp-qemu-virt/src/cpu.rs`, `gic.rs`, `exceptions.rs`, `mmu.rs`, `mmu_bootstrap.rs`, and `kernel/src/obj/mod.rs` provide a map of which entries cover the file. This is substantially above the policy minimum and makes log-to-code reconciliation easy. The only gap identified (D5b-001 and D5b-002) is the `from_existing_root` constructor and the FakeMmu impl.

---

#### D5b-P3 — Perf baseline series spans four snapshots and is methodologically clean

The four perf reports (`post-pr-19`, `post-t-016`, `B2-closure`, `B3-closure`) form a coherent series with identical methodology sections, raw-sample dumps, and percentile tables. The `Note on p99 at small n` caveat was added starting with the B2-closure report — a good update. The reports are an honest instrument for catching performance regressions at phase boundaries.

---

## Unsafe-log reconciliation (preliminary)

**How this table was built:** the log was read in full (UNSAFE-2026-0001 through UNSAFE-2026-0027). Each entry's Location field and Amendments were recorded. Then `rg -n "unsafe"` was run over every non-test, non-target Rust source file; all `unsafe fn`, `unsafe impl`, `unsafe {}`, and `unsafe extern` occurrences were compared against the log. Files searched: `bsp-qemu-virt/src/{console,cpu,exceptions,gic,main,mmu,mmu_bootstrap}.rs`, `hal/src/{cpu.rs,context_switch.rs,mmu/mod.rs,mmu/vmsav8.rs}`, `kernel/src/{sched/mod,mm/pmm,mm/address_space,mm/mod,obj/task_loader}.rs`, `test-hal/src/mmu.rs`.

### Audit log entries vs. code (production code only)

| UNSAFE ID | Log location (file field) | Code site confirmed? | Notes |
|-----------|--------------------------|---------------------|-------|
| UNSAFE-2026-0001 | `bsp-qemu-virt/src/main.rs::kernel_entry` | Yes | `Pl011Uart::new(PL011_UART_BASE)` at line 712 |
| UNSAFE-2026-0002 | `bsp-qemu-virt/src/main.rs::panic` | Yes | `Pl011Uart::new(PL011_UART_BASE)` at line 1299 |
| UNSAFE-2026-0003 | `bsp-qemu-virt/src/console.rs` | Yes | `unsafe impl Send for Pl011Uart {}` line 51; `Audit: UNSAFE-2026-0003` at line 50 |
| UNSAFE-2026-0004 | `bsp-qemu-virt/src/console.rs` | Yes | `unsafe impl Sync for Pl011Uart {}` line 58; `Audit: UNSAFE-2026-0004` at line 57 |
| UNSAFE-2026-0005 | `bsp-qemu-virt/src/console.rs::Pl011Uart::write_bytes` | Yes | `unsafe { read_volatile / write_volatile }` at line 71; `Audit: UNSAFE-2026-0005` at line 70 |
| UNSAFE-2026-0006 | `bsp-qemu-virt/src/cpu.rs` | Yes | `unsafe impl Send / Sync for QemuVirtCpu` lines 213, 222; amendment coverage for post-T-009 struct confirmed |
| UNSAFE-2026-0007 | `bsp-qemu-virt/src/cpu.rs` | Yes | `MRS`/`MSR` inline asm blocks in `current_core_id`, `disable_irqs`, `restore_irq_state`, `wait_for_interrupt`, `instruction_barrier`; `Audit: UNSAFE-2026-0007` at each site |
| UNSAFE-2026-0008 | `bsp-qemu-virt/src/cpu.rs` + `kernel/src/sched/mod.rs` | Yes | `context_switch_asm` (naked fn, line 355); `context_switch` and callers in sched; `Audit: UNSAFE-2026-0008` at sites |
| UNSAFE-2026-0009 | `bsp-qemu-virt/src/cpu.rs::QemuVirtCpu::init_context` + `kernel/src/sched/mod.rs::Scheduler::add_task` | Yes | `ctx.lr`/`ctx.sp` writes; `Audit: UNSAFE-2026-0009` at sites |
| UNSAFE-2026-0010 | `bsp-qemu-virt/src/main.rs` | Yes | `unsafe impl Sync for StaticCell<T>` at line 136; `Audit: UNSAFE-2026-0010` |
| UNSAFE-2026-0011 | `bsp-qemu-virt/src/main.rs` | Yes | `unsafe impl Sync for TaskStack` at line 193; `TaskStack::top` inner `unsafe {}` at line 214; `Audit: UNSAFE-2026-0011` at both sites |
| UNSAFE-2026-0012 | `bsp-qemu-virt/src/main.rs::task_a/task_b` | Correctly **Removed** 2026-04-22 | No code site expected; `&mut` aliasing eliminated by ADR-0021 |
| UNSAFE-2026-0013 | `bsp-qemu-virt/src/main.rs::StaticCell::as_mut_ptr` | Yes | `self.0.get().cast::<T>()` path; `Audit: UNSAFE-2026-0013` at line 162 |
| UNSAFE-2026-0014 | `kernel/src/sched/mod.rs` free functions | Yes | Momentary `&mut` pattern in `yield_now`, `ipc_send_and_yield`, `ipc_recv_and_yield`, `start`, `start_prelude`, `register_idle`; `Audit: UNSAFE-2026-0014` at each site; seven amendments confirmed |
| UNSAFE-2026-0015 | `bsp-qemu-virt/src/cpu.rs::QemuVirtCpu::new` + `now_ns` | Yes | `MRS CNTFRQ_EL0` and `MRS CNTVCT_EL0`; amendment for register-family swap confirmed; `Audit: UNSAFE-2026-0015` at sites |
| UNSAFE-2026-0016 | `bsp-qemu-virt/src/cpu.rs::QemuVirtCpu::new` | Yes | `MRS CurrentEL` assertion; replaced by `current_el()` call per T-013 Amendment; `Audit: UNSAFE-2026-0016` reference in `new()` body |
| UNSAFE-2026-0017 | `bsp-qemu-virt/src/boot.s` | Yes (assembly) | `DAIF mask + EL drop sequence` at `_start`; amendments for HCR_EL2 literal-write rationale + GAS halt-loop syntax correction confirmed |
| UNSAFE-2026-0018 | `hal/src/cpu.rs::current_el` | Yes | `unsafe {}` block with `MRS CurrentEL` at line 179; `Audit: UNSAFE-2026-0018` at line 178; `# Safety` in fn doc |
| UNSAFE-2026-0019 | `bsp-qemu-virt/src/gic.rs` | Yes | `QemuVirtGic` MMIO surface; `unsafe fn new`, `unsafe fn init`, four private helpers, `unsafe impl Send/Sync`; `Audit: UNSAFE-2026-0019` at all sites; partial smoke verification amendments |
| UNSAFE-2026-0020 | `bsp-qemu-virt/src/vectors.s` + `exceptions.rs` + `main.rs::kernel_entry` | Yes | Vector table install + asm trampolines + `irq_entry`/`panic_entry`; `Audit: UNSAFE-2026-0020` at all sites |
| UNSAFE-2026-0021 | `bsp-qemu-virt/src/cpu.rs::arm_deadline/cancel_deadline` + `exceptions.rs::irq_entry` | Yes | `MSR CNTV_CVAL_EL0`/`CNTV_CTL_EL0` writes; `Audit: UNSAFE-2026-0021` at sites; pending smoke verification amendments |
| UNSAFE-2026-0022 | `bsp-qemu-virt/src/mmu_bootstrap.rs::mmu_bootstrap` Step 1 | Yes | `write_volatile` on `*mut u64` for L0/L1/L2 page-table frames; `Audit: UNSAFE-2026-0022` at line 120; T-016 Stage 6 smoke verification amendment |
| UNSAFE-2026-0023 | `bsp-qemu-virt/src/mmu.rs::activate` + `mmu_bootstrap.rs` Step 2 | Yes | `MSR TTBR0_EL1 + ISB + TLBI + DSB + ISB`; `Audit: UNSAFE-2026-0023`; bootstrap-Amendment + smoke verification confirmed |
| UNSAFE-2026-0024 | `bsp-qemu-virt/src/mmu.rs::invalidate_tlb_address/all` + `mmu_bootstrap.rs` Step 3 | Yes | `TLBI VAE1/VMALLE1 + DSB ISH + ISB` + `IC IALLU`; `Audit: UNSAFE-2026-0024`; amendments confirmed |
| UNSAFE-2026-0025 | `bsp-qemu-virt/src/mmu.rs::map/unmap/walk_and_install_leaf/walk_or_alloc_table` | Yes | `read_volatile`/`write_volatile` on `*mut u64` in 4-level page-table walk; `Audit: UNSAFE-2026-0025` throughout; T-019 post-bootstrap smoke Amendment |
| UNSAFE-2026-0026 | `kernel/src/mm/pmm.rs::alloc_frame` | Yes | `write_bytes(pa_ptr, 0u8, PAGE_SIZE)` at line 436; `Audit: UNSAFE-2026-0026` at lines 429–430; T-019 runtime Amendment |
| UNSAFE-2026-0027 | `kernel/src/obj/task_loader.rs::load_image` | Yes | `copy_nonoverlapping(src, dst, chunk.len())` at line 664; `Audit: UNSAFE-2026-0027` at lines 621–622; five amendments through review-round 4 |

**Result: 27 log entries — 26 Active + 1 Removed (UNSAFE-2026-0012). All 26 Active entries match confirmed code sites.**

### Code unsafe with NO log entry

| Code site | File:line | Nature | Severity |
|-----------|-----------|--------|----------|
| `QemuVirtAddressSpace::from_existing_root` | `bsp-qemu-virt/src/mmu.rs:125` | `unsafe fn` with `# Safety` doc but no `Audit:` tag and no log entry | **Major** (D5b-001) |
| `FakeMmu::create_address_space` | `test-hal/src/mmu.rs:133` | `unsafe fn` trait impl — no `# Safety` doc, no `Audit:` tag, no log entry | **Minor** (D5b-002) |
| `FakeCpu` `unsafe impl Send/Sync` | `kernel/src/sched/mod.rs:1261–1263` | `// SAFETY:` present, no `Audit:` tag, no log entry | **Nit** (D5b-006) |
| `ResetQueuesCpu` `unsafe impl Send/Sync` | `kernel/src/sched/mod.rs:1911–1913` | `// SAFETY:` present, no `Audit:` tag, no log entry | **Nit** (D5b-006) |
| `FailingMapMmu::create_address_space` | `kernel/src/obj/task_loader.rs:1750` | `unsafe fn` test-only delegation; has 3-point `// SAFETY:` comment but no `Audit:` tag; delegates to `FakeMmu` (D5b-002 parent) | Nit (subsumed under D5b-002) |

**Note on `phys_frame_kernel_ptr`:** `kernel/src/mm/mod.rs:168` contains `frame.as_usize() as *mut u8` — an integer-to-pointer cast — in a `pub(crate) fn` that is not itself `unsafe`. The function's doc-comment explicitly states the cast is a safe Rust operation and that only the dereference at the call site is `unsafe`. This is correct and requires no audit entry of its own; the cast is not an `unsafe {}` block. Noted here for the X3 pass.

---

## Claims register

| Claim | File:line | How to verify |
|-------|-----------|---------------|
| 2026-04-23 baseline: 111/111 tests pass under Miri | `2026-04-23-miri-validation.md:7` | Point-in-time; reproduced at HEAD as 260/260 (`gate-reproduction.md` Gate 5). Historical figure is correct for the time. |
| 2026-04-23 baseline: workspace regions 94.41% | `2026-04-23-coverage-baseline.md:14` | Point-in-time; gate-reproduction shows 96.26% at HEAD. Drift explained by T-009 through T-019 additions. |
| 2026-04-27 post-T-011: workspace regions 96.33%, 143 tests | `2026-04-27-coverage-rerun.md:9` | Point-in-time snapshot; gate-reproduction shows 96.26% / 260 tests at HEAD (slight decrease in % due to new uncovered paths in T-017/T-018/T-019). |
| `hal/src/mmu.rs` at 40.82% (no MMU impl yet) | `2026-04-27-coverage-rerun.md:27` | **Stale.** Gate-reproduction shows `hal/src/mmu/mod.rs` at 67.74% — the MMU trait grew coverage once T-016 impl + vmsav8 helpers landed. Row caption "no production impl yet" is now incorrect. |
| perf-baseline 2026-05-08 pre-ADR-0027: p50 = 4.642 ms (debug) | `perf-baseline-2026-05-08-post-pr-19-pre-adr-0027.md:48` | Point-in-time baseline; no gate to replay (QEMU determinism). Methodology described; reproducible in principle. |
| perf-baseline 2026-05-08 post-t-016-mmu-activated: p50 = 6.153 ms (debug) | `perf-baseline-2026-05-08-post-t-016-mmu-activated.md:53` | Point-in-time. Working-tree state note explains the numbers cannot be exactly reproduced post-merge. |
| perf-baseline B2-closure: p50 = 4.642 ms (release) | `perf-baseline-2026-05-09-B2-closure.md:55` | Point-in-time; commit `b0035ce`. The identical p50 as the debug pre-ADR-0027 report is a coincidence (different branch / different build profile). |
| perf-baseline B3-closure: p50 = 11.884 ms (release, commit `6334881`) | `perf-baseline-2026-05-14-B3-closure.md:55` | Point-in-time. The ~2.6× increase vs B2 is consistent with T-019 adding `load_image` page-table walks (~7 `alloc_frame` calls + 4-level walk × 2 per boot). Not explained in the report. |
| UNSAFE-2026-0019 "Pending QEMU smoke verification" for `acknowledge`/`end_of_interrupt` | `unsafe-log.md`, UNSAFE-2026-0019 Status + Amendments | Status is correctly still Pending; gate-reproduction smoke trace confirms no IRQ fires and GIC dispatch arm is unreached. Consistent. |
| UNSAFE-2026-0020 "Pending QEMU smoke verification" for trampoline | `unsafe-log.md`, UNSAFE-2026-0020 Status + Amendments | Same as above — trampoline unexercised by v1 demo. Status correct. |
| UNSAFE-2026-0021 "Pending QEMU smoke verification" for timer writes | `unsafe-log.md`, UNSAFE-2026-0021 Status + Amendments | Same — timer never armed in v1 demo. Status correct. |
| UNSAFE-2026-0025 post-bootstrap `Mmu::map` smoke-verified (Amendment 2026-05-14) | `unsafe-log.md`, UNSAFE-2026-0025 Amendment | Confirmed by gate-reproduction Gate 7 trace (`tyrne: image loaded` line implies successful `cap_map` post-bootstrap calls). |
| UNSAFE-2026-0026 `alloc_frame` zero-fill smoke-verified (Amendment 2026-05-14) | `unsafe-log.md`, UNSAFE-2026-0026 Amendment | Confirmed — `alloc_frame` exercised by T-019 BSP wiring; gate-reproduction smoke trace consistent. |
| UNSAFE-2026-0027 `copy_nonoverlapping` smoke-verified (Status, line 588) | `unsafe-log.md`, UNSAFE-2026-0027 Status | Confirmed by gate-reproduction Gate 7 (`tyrne: image loaded` with 8-byte image). |

---

## Cross-track notes (for the X3 unsafe-audit pass)

The following items are handed off to the X3 deeper unsafe-audit pass:

1. **`QemuVirtAddressSpace::from_existing_root` (D5b-001, Major).** A new audit entry is needed. The call site (`bsp-qemu-virt/src/main.rs:921–927`) has adequate `// SAFETY:` prose but lacks an `Audit:` tag. X3 should confirm whether any other `from_existing_root` callers exist and whether the bootstrap-wrapper path in `kernel/src/mm/address_space.rs::AddressSpace::wrap_bootstrap` also needs its own entry.

2. **`FakeMmu::create_address_space` (D5b-002, Minor).** Test-only `unsafe fn` missing `# Safety` doc. X3 should verify whether `clippy::missing_safety_doc` is currently suppressed for test code (e.g., via `#[allow(...)]` on the test module) and whether the policy intends an exemption. The `FailingMapMmu::create_address_space` in `task_loader.rs:1750` is a parallel case.

3. **Test-harness `unsafe impl Send/Sync` (D5b-006, Nit).** `FakeCpu` and `ResetQueuesCpu` in `kernel/src/sched/mod.rs`. X3 should determine whether the project's implicit test-exemption should be codified in `unsafe-policy.md`.

4. **Miri integer-to-pointer cast warnings (D5b-003, Minor).** The four sites producing Miri advisory warnings (`pmm.rs:378`, `pmm.rs:874`, `task_loader.rs:871`, `mm/mod.rs:168`) are unmentioned in any audit entry. X3 should assess whether `core::ptr::with_exposed_provenance` / `strict_provenance` migration is practical at the kernel level given the identity-mapping assumption, and whether the `phys_frame_kernel_ptr` helper requires its own audit entry or can be covered by a note in UNSAFE-2026-0026 and UNSAFE-2026-0027.

5. **`boot.s` DAIF mask + EL drop (UNSAFE-2026-0017).** X3 should verify that the GAS halt-loop syntax correction Amendment (`halt_unsupported_el: wfe ; b halt_unsupported_el`) matches the actual `boot.s` source at HEAD 288ddb2.

6. **`context_switch_asm` `#[unsafe(naked)]` attribute (UNSAFE-2026-0008).** Unsafe-policy.md §5a requires `#[unsafe(naked)]` for any function whose body saves/restores SP. Confirmed at `bsp-qemu-virt/src/cpu.rs:354`: `#[unsafe(naked)]` is present. X3 should confirm the `naked_asm!` discipline at that function.

7. **`kernel/src/mm/pmm.rs:378` test-helper cast.** The `aligned_backing` helper at line 874 (`((raw as usize + 4095) & !4095) as *mut u8`) is a `*mut u8` cast in test code and triggers a Miri warning. It has no `// SAFETY:` comment annotating the integer-to-pointer step (the outer `unsafe {}` at line 926 covers `write_bytes`, not the cast itself). X3 should verify whether `clippy::undocumented_unsafe_blocks` is satisfied here.

---

## Coverage checklist (all 8 files)

| File | Lines | Read? |
|------|-------|-------|
| `docs/audits/unsafe-log.md` | 609 | [x] Read in full (4 passes: 1–210, 211–420, 421–520, 521–609) |
| `docs/analysis/reports/2026-04-23-coverage-baseline.md` | 76 | [x] Read in full |
| `docs/analysis/reports/2026-04-23-miri-validation.md` | 62 | [x] Read in full |
| `docs/analysis/reports/2026-04-27-coverage-rerun.md` | 110 | [x] Read in full |
| `docs/analysis/reports/perf-baseline-2026-05-08-post-pr-19-pre-adr-0027.md` | 89 | [x] Read in full |
| `docs/analysis/reports/perf-baseline-2026-05-08-post-t-016-mmu-activated.md` | 97 | [x] Read in full |
| `docs/analysis/reports/perf-baseline-2026-05-09-B2-closure.md` | 96 | [x] Read in full |
| `docs/analysis/reports/perf-baseline-2026-05-14-B3-closure.md` | 96 | [x] Read in full |

Total lines read: 1 235 (docs). Additionally, source code scans were performed across 21 Rust source files for unsafe-log reconciliation.
