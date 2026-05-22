# Tyrne master review — consolidated report

| Field | Value |
|---|---|
| **Run id** | `2026-05-22-152729` |
| **Anchor commit (HEAD)** | `288ddb2be98e4a679cb5a07ba8a70e52b82c21a7` ("docs(readme): rewrite root README for a first-time reader") |
| **Date** | 2026-05-22 |
| **Project** | Tyrne — capability-based microkernel in Rust (pre-alpha; QEMU `virt` aarch64 primary target, Raspberry Pi 4 first hardware) |
| **Scope** | 251 in-scope tracked files / 45,757 lines (per `../00-coverage-manifest.md`) |
| **Out of scope** | `docs/analysis/reviews/master-review/**` (this review's own output); `docs/analysis/technical-analysis/**` (untracked / gitignored, per maintainer) |
| **Method** | 4 waves, 25 track agents + 1 consolidation agent. Read-only on the repo (one mutating gate-reproduction run on a separate runner). |
| **Dimensions applied** | code-correctness · optimization · security · maintainability · refactor · usability · business-alignment · doc-quality · contradictions |

---

## Executive summary

**Overall verdict: APPROVE the shipped kernel; do NOT yet rely on the documentation set or the CI gate as the project's records claim you can.**

The split is the headline. The **shipped kernel code is in genuinely strong shape**: there are **0 code-correctness Blockers**, the dedicated security pass returns **PASS** (no security Blocker, no security Major in the shipping binary), all seven reproduced gates are green — **260/260 host tests**, **260/260 under Miri with zero detected UB**, **96.26% workspace region coverage**, a byte-stable **QEMU smoke trace through `tyrne: all tasks complete`** — and the unsafe-audit reconciliation found the audit log fully in sync (27 entries, all resolve to live code, zero stale, zero append-only violations). The capability core, the raw-pointer scheduler bridge, the PMM, the task loader, and the VMSAv8 encoders are all carefully built and well-tested.

**Where the issues actually are** — and the framing matters because most of the high-severity findings are NOT defects in how the kernel runs:

1. **CI / gate integrity (the real Blockers).** What CI *runs* is not what its job names, its setup steps, and the docs *claim* it runs: the two "stable" jobs silently execute on the pinned nightly (the `rust-toolchain.toml` override shadows `rustup default stable`), so the "builds clean on stable" guarantee is never tested; the documented required-gate set lists `cargo-audit` / `cargo-vet` / QEMU-smoke as merge gates that **do not exist** in `ci.yml`; and the CI header claims coverage is "required for merge" while the job runs `continue-on-error: true`. These block *reliance on the gate / the doc that describes it* — they do not stop the kernel from working or block this commit's compile.

2. **Documentation drift, including frozen ADRs that contradict the code.** A cluster of front-door and architecture docs lag the implementation by 2–3 milestones (CLAUDE.md/CONTRIBUTING.md still say "architecture phase / most code not yet written"; the architecture index marks a written doc "Planned"); several **Accepted ADRs assert hardware/contract facts the code contradicts** (GICv3/SMMUv3 in ADR-0004/0006/0012 vs the shipped GIC v2 + empty `Iommu` stub; ADR-0020's 104-byte/no-FP context vs the shipped 168-byte/d8–d15 one) and the append-only policy has *frozen* those contradictions in place; the Phase C and Phase D plans **reuse ADR numbers already Accepted on `main`**; and ~49 cross-references are broken/stale (42 `.claude/skills/` link-rot + 7 `hal/src/mmu.rs` path-rot).

3. **One latent FP-register context-switch contract gap that will bite a second BSP.** The `ContextSwitch` trait safety contract (and ADR-0020) enumerate the aarch64 callee-saved set but **omit `d8`–`d15`**. The shipping QEMU BSP saves them correctly, so v1 is sound — but a second BSP author (Pi 4 / Jetson, the entire reason the HAL exists) implementing to the literal contract would ship a context switch that silently corrupts FP state across every yield. Data-dependent, survives smoke tests, near-undebuggable. This is the single most important *code-adjacent* correctness item and is corroborated by five independent tracks.

The Blockers/Majors therefore cluster in **CI/infra integrity, documentation/ADR drift, and the one latent context-switch contract gap** — not in the kernel's operation.

### Severity tally (canonical, after de-duplication)

| Severity | Count | What they are |
|---|---:|---|
| **Blocker** | 4 | All are *doc/CI/plan reliance* blockers (gate integrity, frozen foundational ADRs, roadmap ADR-number collision, broken normative-doc links). **0 are kernel-code-correctness or security Blockers.** |
| **Major** | 18 | The d8–d15 contract gap; CI hardening (RUSTFLAGS clobber, action SHA-pinning, no `permissions:`); Miri-not-a-CI-gate; an O(n) PMM helper; the missing `from_existing_root` audit entry; an `IrqState` polarity inversion between fakes; the FakeMmu fidelity gap; ADR/arch-doc drift; front-door & `current.md` staleness; and the OTA/field-update product gap. |
| **Minor** | ~46 | Polish, forward-flags, contract-text accuracy, test-coverage edges, link rot, prose drift (grouped in compact tables below; each points to its owning track). |
| **Nit** | ~33 | Cosmetic / consistency / volatile-literal items. |
| **Praise** | 40+ | Capability core, unsafe discipline, test rigor, shell tooling, doc/review structure (summarized below). |

### Top things to fix first (ordered)

1. **Fix the d8–d15 context-switch contract** (`hal/src/context_switch.rs` `# Safety` + an ADR-0020 amendment/superseding rider) before a second BSP is written. The code is correct; the contract a second author implements against is not.
2. **Resolve the Phase C / Phase D ADR-number collision** — renumber both phase plans above the live Phase-B ceiling before any Phase-C work begins (an agent following the plan would overwrite a live Accepted ADR).
3. **Make CI honest and complete:** decide the toolchain intent and align job names + `docs/guides/ci.md`; stop `RUSTFLAGS` from clobbering `.cargo/config.toml`; either add or demote the audit/vet/qemu-smoke "required" gates; fix the coverage `continue-on-error` contradiction.
4. **Harden CI supply-chain:** SHA-pin third-party Actions and add a top-level `permissions: contents: read`.
5. **Write a supersession ADR** correcting the frozen GICv3/SMMUv3 statements in ADR-0004/0006/0012 (append-only-legal redirect), and reconcile ADR-0020 to the shipped 168-byte context.
6. **Wire Miri (and ideally a lightweight unsafe-audit reconciliation) into CI** — it is the only mechanical verifier of the scheduler/IPC raw-pointer aliasing discipline and is currently manual.
7. **Refresh the front door & resume pointer:** `current.md` (flip T-019 to Done, fix milestone), CLAUDE.md / CONTRIBUTING.md status, the architecture index, and sweep the ~49 broken links.
8. **Add `UNSAFE-2026-0028`** for `from_existing_root` (the one production `unsafe fn` with no audit entry).

### Praise / strengths (balance)

The review is balanced: the project's substance is strong and several dimensions are exemplary.

- **Capability core.** 100% safe Rust, heap-free, panic-free in production; move-only `Capability` (neither `Copy` nor `Clone`) enforced by the type system; narrowing-only rights with per-operation authority checks *strictly before any side effect*; `from_raw` masks reserved rights bits before the ABI even exists; the `cap_revoke` BFS carries a written size-proof + release-safe overflow guard.
- **Unsafe discipline.** Every production `unsafe` block carries a three-part SAFETY comment (invariants / rejected alternatives / live `UNSAFE-2026-NNNN` tag). The audit log is exemplary append-only (UNSAFE-2026-0014 has six amendments across five tasks with zero in-place body edits); UNSAFE-2026-0012 correctly retired. The scheduler and BSP are reference implementations of `unsafe-policy.md`.
- **Test rigor.** 260 host tests including genuinely adversarial sequences (cap-transfer atomicity, widening rejection, stale-handle on every entry point, the 2026-05-06 smoke-hang regression guard, debug-assert-fires-and-does-not-over-fire pairs). Miri-clean. ~96% coverage.
- **Shell tooling.** `tools/perf-harness.sh` is the strongest single artifact in the build track: correct three-trap process cleanup, locale + SIGPIPE hardening, bash-3.2 portability, nearest-rank percentiles.
- **Doc / review structure.** ADR-anchored architecture docs; typed business/code/security/performance reviews with master plans; the `write-adr` §Simulation-table discipline demonstrably eliminated smoke regressions from B2 onward; the AI-integration stance (ADR-0015) is a model of goal coherence; honest, explicit out-of-scope discipline throughout.

---

## Scope & method

- **HEAD SHA:** `288ddb2be98e4a679cb5a07ba8a70e52b82c21a7`.
- **In-scope:** 251 tracked files / 45,757 lines across kernel, HAL, BSP, test-HAL, build/CI config, all architecture docs, all 31 ADRs + index/template, all standards, the full roadmap + task corpus, meta/front-door docs + skills, the audits/reports, and the existing review archive.
- **Out of scope:** `docs/analysis/reviews/master-review/**` (this review's own output) and `docs/analysis/technical-analysis/**` (untracked / gitignored).

**Wave structure:**

| Wave | Purpose | Agents |
|---|---|---|
| **Wave 0** | Coverage manifest — file→track map, 251 files / 45,757 lines | 1 (manifest) |
| **Wave 1** | Gate reproduction — fmt/clippy/host-test/kernel-build/miri/coverage/QEMU-smoke on a runner | 1 (gate-reproduction) |
| **Wave 2** | 17 deep-read tracks — 9 code (C1–C9) + 8 doc (D1, D2a, D2b, D3, D4, D5a, D5b, D5c) | 17 |
| **Wave 3** | 7 cross-cutting tracks — X1 security, X2 performance, X3 unsafe-audit, X4a/b/c contradictions, X5 business-alignment | 7 |
| **Wave 4** | Consolidation / merge (this report) | 1 |

**Dimensions applied (everywhere — see the §Dimension coverage matrix):** code-correctness, optimization, security, maintainability, refactor, usability, business-alignment, doc-quality, contradictions.

---

## Master findings register

Findings are de-duplicated to one canonical entry each (`MR-NNN`), assigned the **highest severity any track gave the issue**, with corroborating tracks listed. "Doc/CI Blocker" means the finding blocks **reliance on the documentation or the CI gate** (and/or active corruption of a correct artifact by an agent following stale instructions) — **none of the four Blockers stops the kernel from operating or blocks this commit's compile.**

### Blockers (4)

#### MR-001 — Phase C and Phase D plans reuse ADR numbers already Accepted and live on `main`
**Severity: Blocker** · Corroborating: **D4-001, D4-002, X4b-001, X5-003**
**Files:** `docs/roadmap/phases/phase-c.md:17,37,56,79,98,116-122` (assigns ADR-0027–0031 to C1–C5); `docs/roadmap/phases/phase-d.md:17,36,53,87,105,160-166` (assigns ADR-0032–0036 to D1–D6). Live conflicts: `docs/decisions/0027-kernel-virtual-memory-layout.md`, `0028-address-space-data-structure.md`, `0029-initial-userspace-image-format.md`, `0032-endpoint-rollback-and-cancel-recv.md`, `0035-physical-memory-manager.md` (all **Accepted, on `main`**); `phase-b.md:202-203,273-277` reserves 0030/0031 (syscall ABI / initial syscall set, B5) and names 0033/0034 placeholders.
**Description.** Every one of the ten ADR numbers the two future-phase plans claim is already spoken for: 0027/0028/0029/0032/0035 are live Accepted decisions with unrelated subjects, and 0030/0031/0033/0034 are reserved by the Phase-B ledger and the ADR-0027/0028/0029 dependency chains. The collision is currently *only in the plan files* — `docs/decisions/` has no 0030/0031/0033/0034 files yet (so the on-disk corpus is coherent; X4b-P02 praises this).
**Why it matters.** The roadmap is the instruction set the maintainer and agents follow. An agent told by `phase-c.md` to "write ADR-0027 — Secondary core start protocol" would create a filename collision with the live kernel-virtual-memory-layout decision, silently corrupting a load-bearing record — at the exact moment Phase C opens, and directly against the project's "decisions-on-the-record are trustworthy" guarantee.
**Suggested fix.** Renumber **all** Phase-C and Phase-D ADR placeholders to start above the Phase-B ceiling (first free slot is **ADR-0036+**; coordinate Phase C, D, and E so they share a common base). Update both ledger tables and every in-text sub-breakdown + acceptance-criteria reference. Record the "renumbered, was ADR-00xx" provenance in the ledger Notes column (mirroring the exemplary `phase-b.md` precedent, D4-P02).

#### MR-002 — CI "stable" jobs actually run on the pinned nightly; the stable build is never tested, and config/names/docs disagree
**Severity: Blocker** (against gate integrity / reproducibility) · Corroborating: **C9-001, D3-004, D3-013, X4a (cross-ref), X4b (cross-ref)**
**Files:** `.github/workflows/ci.yml:43-69` (lint-and-host-test), `:75-100` (kernel-build); `rust-toolchain.toml:11`; `docs/guides/ci.md:9-12,37`; `docs/standards/infrastructure.md:19`.
**Description.** Both fast-lane jobs run `rustup default stable` then call bare `cargo …`. But `rust-toolchain.toml` pins `nightly-2026-01-15` at the repo root, and rustup's override precedence makes that pin shadow `rustup default` for every in-repo `cargo` invocation. `actions/checkout` places the file on disk before any `cargo` runs, so `fmt`, `host-clippy`, `host-test`, `kernel-build`, and `kernel-clippy` all execute on nightly — not stable. (The miri/coverage jobs correctly use `rustup override set $NIGHTLY_PIN` + explicit `cargo +$NIGHTLY_PIN`.)
**Why it matters.** Three concrete failures: (a) the job names lie ("on stable" but runs nightly); (b) the implicit "Tyrne's host crates build/lint clean on stable" guarantee is **never exercised** — an accidental nightly-only feature in a host crate stays green; (c) `docs/guides/ci.md:37` tells a diverging contributor to `rustup update stable`, advice that cannot resolve the divergence it is offered for. This is the precise gate-integrity gap the build track exists to catch.
**Suggested fix.** Decide the intent and align all three (config + names + docs). Since the kernel needs nightly to build (inline asm / lang items, ADR-0002 §Negative), the truthful option is: drop the `rustup default stable` dance, install/select the pinned nightly the way the miri/coverage jobs do, rename the jobs to drop "stable," and fix `docs/guides/ci.md`'s toolchain column to "pinned nightly" (matching `infrastructure.md:19`). If a stable-builds-clean signal is genuinely wanted, scope an explicit `cargo +stable …` host-only subset.

#### MR-003 — Documented required-gate set ≠ enforced CI gates; coverage job contradicts itself; release gate lists nonexistent jobs
**Severity: Blocker** (gate/doc reliance; D3 rated the coverage-lie and release-gate items Blocker) · Corroborating: **D3-002, D3-003, C9-005, C9-006, X1-003**
**Files:** `docs/standards/infrastructure.md:65-73`; `docs/standards/release.md:61`; `docs/standards/testing.md:105`; `.github/workflows/ci.yml:5-7` (header) vs `:137-141` (`continue-on-error: true`); `docs/guides/ci.md:73-77`.
**Description.** Three overlapping doc↔CI integrity gaps: (1) `infrastructure.md` §"Required gates (block merge)" and `release.md:61` list `cargo-audit`, `cargo-vet`, and a QEMU-smoke gate as merge/release gates, but **no such jobs exist** in `ci.yml` (audit/vet are partially disclosed as "dormant"; the QEMU-smoke gate is a hard release-gate item with no caveat in `release.md`; `testing.md:105` presents QEMU-smoke as an existing CI requirement). (2) The `ci.yml` header comment (`:5-7`) says coverage is "still required for merge into `main`," but the job runs `continue-on-error: true` and is documented everywhere else as informational — `docs/guides/ci.md:75` even warns *not* to add it to required checks. (3) The documented clippy gate (`--workspace --all-targets`) does not match the executed `host-clippy` alias (no `--workspace`).
**Why it matters.** For a security-first project the documented assurance must not exceed the enforced assurance. A reader cross-checking "what blocks merge" against the standards believes audit/vet/smoke are enforced; they are not. Whoever configures branch protection from the contradictory header would wrongly add the neutral-result coverage job to required checks and break every push.
**Suggested fix.** Reconcile the docs to reality and/or add the jobs. Mark audit/vet/smoke as "planned, not yet enforced" in both `infrastructure.md` and `release.md` (or move them to a clearly-labeled "Planned gates" subsection), and either wire the QEMU-smoke job (`docs/guides/ci.md:39-41` already scopes it) or demote it. Fix the `ci.yml:5-7` header to say only Miri is required-but-slow; coverage is informational until the post-T-011 flip. Align the clippy gate command with the two-alias reality (or add `--workspace`).

#### MR-004 — Stale `.claude/skills/` links in live normative docs break the dependency-onboarding & review procedures (part of ~49 broken cross-references)
**Severity: Blocker** (D3 rated the normative `infrastructure.md` instances Blocker — they break the cargo-vet onboarding trigger) · Corroborating: **D3-001, D1-009, D2a-004, D4-007, D4-008, D5a-003, D5c-M01, X4b-009, X1-008**
**Files (normative, live — not dated historical snapshots):** `docs/standards/infrastructure.md:72,192`; `docs/decisions/0013,0023,0025,0026,0027,0035` (multiple lines); `docs/architecture/memory-management.md:132`, `security-model.md:268`; `docs/roadmap/README.md:25,45,46`, `current.md:84`; `docs/roadmap/phases/phase-b.md:27,111,115,125,148,270,271,278,307`; the business/security/performance review master-plans; `.agents/skills/README.md:76` (wrong artifact path for `conduct-review`); `.gitignore:44-46` (stale comment).
**Description.** The skill library migrated from `.claude/skills/` to `.agents/skills/` on 2026-05-14 (commit `77d3e7e`). The X4b programmatic scan over 1,255 relative links across 80 live docs found **49 confirmed broken links**: 42 stale `.claude/skills/…` references across 11 live files, plus **7 broken `hal/src/mmu.rs` links** (the module was refactored to `hal/src/mmu/mod.rs` + `mmu/vmsav8.rs`) across `ADR-0027`, `memory-management.md`, `current.md`, `phase-b.md` (the last contradicts itself — line 115 stale, line 271 correct). One scanner hit (`new-doc.md`) is an illustrative-template false positive; `CHANGELOG.md` is an honestly-disclosed forward reference. Historical review snapshots deliberately retain old paths and are excluded.
**Why it matters.** `infrastructure.md`'s "wired in once the first external dependency lands per [add-dependency]" note is the *trigger* that tells maintainers how to arm cargo-audit/cargo-vet; a 404 there breaks the cargo-vet onboarding path. The `.agents/skills/` rename did not run a repo-wide `grep -F` sweep — a textbook `code-review.md` "post-fix produces stale documentation" miss. The `from_existing_root`/`hal/src/mmu.rs` path rot was caught by *no* Wave-2 track individually.
**Suggested fix.** One repo-wide sweep over **live** docs (excluding dated banners + `docs/analysis/reviews/**` historical snapshots): `.claude/skills/` → `.agents/skills/` (verify each target exists) and `hal/src/mmu.rs` → `hal/src/mmu/mod.rs`. Fix `.agents/skills/README.md:76` (`docs/roadmap/reviews/` → `docs/analysis/reviews/<type>-reviews/`) and the `.gitignore` comment. This closes MR-004 and most of D1-009/D2a-004/D3-001/D4-007/D4-008/D5a-003/D5c-M01 at once.

### Majors (18)

#### MR-005 — `ContextSwitch` safety contract (and ADR-0020) omit `d8`–`d15`; a contract-literal second BSP would silently corrupt FP state across every yield
**Severity: Major** · Corroborating: **C6-001, D2b-001, X1-001, X4a-001, X4a-002, X4c-001**
**Files:** `hal/src/context_switch.rs:18-24` and `:36-39` (the normative contract: "On aarch64 that is `x19`–`x28`, `x29` (fp), `x30` (lr), and `sp`"); `docs/decisions/0020-cpu-trait-v2-context-switch.md:165-167,233-244,304-311` (104-byte struct; "`d8`–`d15` … not saved in v1"). **Correct implementation:** `bsp-qemu-virt/src/cpu.rs:303-326` (168-byte struct with `d8_d15: [u64;8]`, compile-time `assert!(size_of == 168)`), `:382-390` (asm saves/restores them), `:295-301` (rationale: must be saved whenever `CPACR_EL1.FPEN ≠ 0`).
**Description.** Three sources disagree: the trait `# Safety` text and ADR-0020 both enumerate only the GP callee-saved set and ADR-0020 explicitly states the FP set is deferred — but the only correct implementor saves `d8`–`d15` and is 168 bytes (the ADR says 104). Per AAPCS64, `d8`–`d15` must be preserved whenever FP is enabled, which the BSP enables (`CPACR_EL1.FPEN = 0b11`) before any NEON.
**Why it matters.** The trait `# Safety` section is the contract a future Pi 4 / Pi 5 / Jetson BSP author implements against — the whole reason the HAL trait exists. An author saving exactly the four listed classes produces a context switch that clobbers `d8`–`d15` on every yield. The failure is data-dependent (only when the compiler has live FP callee-saved state across a switch), so it survives smoke tests and surfaces as rare, near-undebuggable corruption — exactly the class of bug the HAL's trait contracts exist to prevent. v1 is sound (the BSP is correct); this is the single most important latent cross-board correctness item.
**Suggested fix.** Amend both occurrences in `context_switch.rs` to add "**and the SIMD/FP callee-saved registers `d8`–`d15` (lower 64 bits of `v8`–`v15`) whenever FP is enabled (`CPACR_EL1.FPEN ≠ 0`)**", and preferably generalise to "the target ABI's full callee-saved set" for the future RISC-V lineage. Add a Revision-notes rider to ADR-0020 recording that the FP set was implemented in the same arc (not deferred), the struct is 168 not 104 bytes, and the §Neutral "deferred" note is superseded. Doc/contract-only change; route through the boot-path + `unsafe` review gate.

#### MR-006 — Foundational platform ADRs (0004/0006/0012) assert GICv3 + SMMUv3; the code ships GIC v2 + an empty `Iommu` stub, and append-only has frozen the contradiction
**Severity: Blocker (strategic, X5) / Major (doc↔doc, X4b)** → recorded as **Major** in the register, but flagged in §Executive summary as part of the foundational-ADR-credibility risk · Corroborating: **X5-001, X4b-002, D2a-002, D2a-003, C7-001, D1-003, X4a-006, X4a-007**
**Files:** `docs/decisions/0004-target-platforms.md:31`, `0006-workspace-layout.md:47`, `0012-boot-flow-qemu-virt.md:24` (all say "GICv3"/"SMMUv3"); **reality:** `bsp-qemu-virt/src/gic.rs:1` ("GIC v2 driver", GICC_*/GICD_* MMIO, no `ICC_*` sysregs), `hal/src/lib.rs:62` (`pub trait Iommu {}` empty stub, no BSP impl); **already-corrected docs:** `docs/architecture/overview.md:77`, `exceptions.md`, `phase-b.md:77` all correctly say GICv2. Phase C still rides the false premise (`phase-c.md:87` "GICv3 SGI").
**Description.** The first ADRs a reader is told to read assert hardware facts the build contradicts. The 2026-05-06 review corrected the architecture docs but not the ADRs (append-only forbids in-place body edits), so the contradiction is now structural. The project's own convention ("the ADR is authoritative when they disagree") tells a careful reader to believe the *wrong* document. The address in ADR-0012 (`0x0800_0000`) is correct — only the *version label* is wrong. Note: `security-model.md` is correctly hedged (SMMUv3 framed as future/conditional), so this is ADR/`hal.md`-specific, not a security-model defect.
**Why it matters.** Tyrne's entire differentiation is "decisions are on the record and the record is trustworthy." Foundational ADRs that contradict the build, frozen by the project's own policy, is the class of latent rot that erodes a high-assurance project's credibility faster than a bug — and it has already propagated into the Phase C plan. It also forces an honest admission: the security model leans on SMMUv3-in-CI as the DMA-capability gate, but with no `Iommu` impl the "DMA is capability-scoped where hardware permits" invariant is currently aspirational even on QEMU.
**Suggested fix.** Use the supersession mechanism that exists for exactly this: one short ADR (e.g. "QEMU virt is GICv2 / no-IOMMU in v1; corrects the GICv3/SMMUv3 statements in ADR-0004/0006/0012") plus append-only one-line revision-note pointers at the top of 0004/0006/0012 redirecting a reader who hits the stale line. Fix the forward references (`phase-c.md:87` GICv2/GIC-400; `hal.md` `Iommu` "planned" per MR-013). State the DMA-scoping invariant as future-on-QEMU honestly.

#### MR-007 — `RUSTFLAGS: -D warnings` in CI clobbers `.cargo/config.toml` per-target rustflags; the kernel CI build loses `panic=abort` + frame pointers
**Severity: Major** · Corroborating: **C9-002**
**Files:** `.github/workflows/ci.yml:30`; `.cargo/config.toml:14-21,51-52`.
**Description.** CI sets a process-wide `env: RUSTFLAGS: -D warnings`. Cargo replaces (does not merge) `target.<triple>.rustflags` when `RUSTFLAGS` is set, so the `[target.aarch64-unknown-none] rustflags = ["-C","panic=abort","-C","force-frame-pointers=yes"]` block is silently ignored in the `kernel-build` job. The kernel ELF CI compiles is therefore a *different binary* than every local build (where `RUSTFLAGS` is unset and the config applies), and the config comment's own invariant ("panic=abort … only applies to the bare-metal target") is quietly broken.
**Why it matters.** Reproducibility/fidelity (P11): CI is meant to be the reference build but compiles a different artifact. `panic=abort` changes codegen (unwinding tables, panic path, link behavior for a `no_std` binary with its own `#[panic_handler]`); the project is one refactor away from CI and local diverging on link success. `force-frame-pointers=yes` (wanted for panic backtraces) is also dropped.
**Suggested fix.** Stop setting codegen-affecting flags via a global env var that clobbers config. Best: drop the `RUSTFLAGS` env (the `host-clippy`/`kernel-clippy` aliases already pass `-D warnings`), and if a deny-warnings build is wanted, add it to a mergeable `build.rustflags` / `[target.'cfg(all())']` block. Verify by building the kernel with/without `RUSTFLAGS` and diffing the ELF's unwinding sections.

#### MR-008 — CI supply-chain hygiene: third-party Actions pinned by mutable tag (not SHA), and no `permissions:` block
**Severity: Major** · Corroborating: **C9-003, C9-004, X1-007**
**Files:** `.github/workflows/ci.yml:47,54,79,87,111,117,142,158,162` (all `@v4`/`@v2` tags); whole file (no `permissions:` key).
**Description.** Every external action (`actions/checkout@v4`, `actions/cache@v4`, and especially `taiki-e/install-action@v2`, which downloads and *executes* a prebuilt binary into the build) is referenced by a moving tag — a tag repoint is arbitrary code execution in CI. With no `permissions:` block, the auto-provisioned `GITHUB_TOKEN` may carry write scopes.
**Why it matters.** This is the central supply-chain control for the pipeline and directly ties to P11 and `infrastructure.md`'s supply-chain section. The irony is sharp: the workflow pins the Rust nightly and `cargo-llvm-cov@0.6.16` to exact versions *specifically to stop upstream silently changing what runs*, yet the actions wrapping those tools are unpinned. Squarely the security model's adversary #3 (supply-chain tampering).
**Suggested fix.** SHA-pin every third-party action (40-char SHA with the tag in a trailing comment), add a top-level `permissions: contents: read` (override per-job only where genuinely needed — none do today), and codify SHA-pinning + a Dependabot/`pinact` refresh path in `infrastructure.md` §Supply-chain.

#### MR-009 — Miri is the only mechanical verifier of the scheduler/IPC raw-pointer aliasing discipline, and it is not a per-PR CI gate
**Severity: Major** · Corroborating: **X1-002, C5-004, X3 (cross-track)**
**Files:** `kernel/src/sched/mod.rs:393-473` (shared safety contract) + every bridge body; `kernel/src/ipc/mod.rs` (shares the discipline); `docs/standards/infrastructure.md`; the ADR-0021 "verify via miri once CI exists (K3-7)" path.
**Description.** The raw-pointer bridge deliberately trades the borrow checker's compile-time non-aliasing guarantee for a *documented* "no `&mut` across `cpu.context_switch`" invariant (ADR-0021 §Consequences accepts this). The named verification path is `cargo +nightly miri test`, run **manually** today (the job exists in `ci.yml` but required-status enforcement is branch-protection config not present in-tree). Miri currently passes 260/260 with zero UB.
**Why it matters.** A future refactor that lets a momentary `&mut` escape its block — e.g. hoisting `let s = &mut *sched;` above the switch — would compile cleanly, pass every non-Miri test, and reintroduce exactly the UNSAFE-2026-0012-class aliasing UB the bridge was built to remove. The 2026-05-06 smoke regression is precedent that "host tests + static analysis + review" cleared a real defect repeatedly; the analogous failure here is catchable *only* by Miri. The audit log cannot detect this class of regression. (This is regression-prevention, not remediation of a present UB.)
**Suggested fix.** Wire `cargo +nightly miri test --workspace --exclude tyrne-bsp-qemu-virt` as a blocking gate on `kernel/src/sched/**` and `kernel/src/ipc/**` changes (the K3-7 task ADR-0021 already names), and make it a Phase-B exit prerequisite — consistent with the 2026-04-21 security review that made the aliasing discipline the #1 Phase-B blocker.

#### MR-010 — `could_yield_pa_overlapping` inner loop is O(range_frames × R); unbounded for a caller-controlled input range
**Severity: Major** · Corroborating: **X2-001, C2-003, C4 (caller)**
**Files:** `kernel/src/mm/pmm.rs:578-626`; sole production caller `kernel/src/obj/task_loader.rs:577`.
**Description.** The helper iterates every frame index in the (clipped) input range, doing an `O(populated_reserved)` scan per frame. The sole production caller passes the 8-byte image's 1-frame span (single iteration, safe). But the function is `pub`, takes an arbitrary `Range<usize>` with no precondition, and is the one PMM operation whose cost is not bounded by a small constant: a caller passing the full 128 MiB extent (32,768 frames × R=8) performs ~262,144 `contains` checks.
**Why it matters.** ADR-0035 explicitly calls for keeping PMM hot paths bounded. A future filesystem-backed image loader (B5+) or a robustness auditor could pass a large range. The *answer* never needs per-frame enumeration — it is answerable in O(populated_reserved) with interval arithmetic. Not a correctness defect; a `pub`, precondition-free, quadratic forward hazard.
**Suggested fix.** Replace the per-frame loop with interval arithmetic: clip the query range, subtract the (≤ R) intersecting reserved intervals, return `true` iff any residue remains — O(R) regardless of range length. If the loop is kept for clarity, add a documented max-range precondition.

#### MR-011 — `QemuVirtAddressSpace::from_existing_root` is the only production `unsafe fn` with no audit-log entry; its call site mis-attributes the unsafety to two unrelated entries
**Severity: Major** · Corroborating: **D5b-001, X3-001**
**Files:** `bsp-qemu-virt/src/mmu.rs:125` (declaration, with a correct `# Safety` section at `:97-127`); `bsp-qemu-virt/src/main.rs:921-927` (sole call site, whose SAFETY block cites `UNSAFE-2026-0010 + 0014`).
**Description.** `pub unsafe fn from_existing_root(root: PhysFrame) -> Self` wraps the already-live, populated bootstrap L0 frame `mmu_bootstrap` installed into `TTBR0_EL1` — a contract genuinely *distinct* from `Mmu::create_address_space` (which requires a **zero-filled** root). A full search of `docs/audits/unsafe-log.md` confirms **no entry names it**. Worse, the call site's `Audit:` line points at 0010 (StaticCell pattern) + 0014 (momentary `&mut` to the arena), neither of which covers the wrap-a-live-non-zero-root operation — so it *looks* audited but is not. (X3 verified this slipped through every PR gate because no CI lint reconciles the audit log; `missing_safety_doc` is satisfied by the present `# Safety`, and `undocumented_unsafe_blocks` only checks that *a* SAFETY comment exists, not that its `Audit:` tag is correct.)
**Why it matters.** This is the only production `unsafe fn` in the tree with no audit entry, at the security-sensitive boot/MMU boundary (installing the live translation root into a kernel object). unsafe-policy §2/§3 and the `justify-unsafe` skill all require the log entry + correct `Audit:` trailer. The code is sound (the contract is correct and the sole caller honours it); this is an audit-trail completeness defect, the highest-priority audit fix.
**Suggested fix.** Open **UNSAFE-2026-0028** for `from_existing_root` (operation: wrap an already-live, populated VMSAv8 L0 root without zero-fill; invariants: established by `mmu_bootstrap`, installed as `TTBR0_EL1`, exactly one per boot, subsequent map/unmap use the 0025 walker invariants; rejected alternative: routing through `create_address_space`, which demands a zero-filled root). Add `// Audit: UNSAFE-2026-0028.` to both the `# Safety` doc and the call-site SAFETY block (narrowing the 0010+0014 attribution to the StaticCell/arena lines they actually cover). Security-sensitive → second reviewer.

#### MR-012 — `overview.md` claims both IPC flavours share one `EndpointCap` object; notifications are a separate `NotificationCap`/`Notification`
**Severity: Major** · Corroborating: **D1-001, X4a-004, X4a-008, X4b-010**
**Files:** `docs/architecture/overview.md:143` ("Both flavours use the same `EndpointCap` kernel object") and `:141` ("a notification that accumulates on the receiver's **endpoint**"); **code:** `kernel/src/ipc/mod.rs:408-419` (`ipc_notify` takes `NotificationArena`, ORs bits into a `Notification`), `kernel/src/cap/mod.rs:60-64` (distinct `CapKind::Endpoint`/`Notification`). Also contradicts `glossary.md:69` and `security-model.md:138` within the doc set; `ipc.md` is correct.
**Description.** Two wrong sentences in the same `overview.md` paragraph: synchronous rendezvous uses `EndpointCap`/`Endpoint`, asynchronous notification uses the independent `NotificationCap`/`Notification` (no endpoint involved).
**Why it matters.** `overview.md` is the doc a reader who wants the design starts from; the claim could lead a contributor to implement `ipc_notify` against an endpoint or expect the endpoint state machine to handle notification bits. It also contradicts the project's own glossary and security model.
**Suggested fix.** Rewrite both sentences to name the two distinct objects: "Synchronous rendezvous uses `EndpointCap` (kernel object `Endpoint`). Asynchronous notification uses `NotificationCap` (kernel object `Notification`); a notification accumulates bits in a `Notification` object. The two are independent; `ipc.md` describes both."

#### MR-013 — `hal.md` attributes context-switch to `Cpu` (it is the separate `ContextSwitch` trait) and falsely claims `bsp-qemu-virt` implements `Iommu`
**Severity: Major** · Corroborating: **D1-002, D1-003, X4a-003, X4a-009, X4a-010, X4a-024, C6-007**
**Files:** `docs/architecture/hal.md:53,78-85,152-153,238` and `docs/architecture/overview.md:69`; **code:** `hal/src/cpu.rs:44-76` (`Cpu` has no context-switch / PSCI / core-count / `enable_interrupts` method), `hal/src/context_switch.rs:25-64` (the separate ADR-0020 trait), `hal/src/lib.rs:62` (`Iommu` empty stub, no BSP impl).
**Description.** `hal.md` (a) attributes "context save/restore primitives" to `Cpu` and has no `#### ContextSwitch` section, hiding the ADR-0020 split that exists to limit the `unsafe` audit surface; (b) advertises `Cpu` methods that do not exist ("Number of cores online," "Secondary-core start via PSCI," `Cpu::enable_interrupts()` in the boot diagram); (c) asserts in prose + flowchart that `bsp-qemu-virt` implements a "SMMUv3 impl" of `Iommu` — which is an empty marker trait with no implementation anywhere in the BSP.
**Why it matters.** `hal.md` is the canonical orientation doc a new BSP author reads first; method names that do not exist send them hunting for deferred/renamed methods, the invisible `Cpu`/`ContextSwitch` split undercuts the safety rationale, and the false `Iommu` claim misrepresents the current security posture.
**Suggested fix.** Remove context-switch from `hal.md` §`Cpu` and `overview.md:69`; add a `#### ContextSwitch` subsection (ADR-0020; `context_switch`/`init_context`; the `Scheduler<C: ContextSwitch + Cpu>` bound). Annotate core-count/PSCI/`enable_interrupts` as future or fix the boot diagram (interrupts unmask via `restore_irq_state`/DAIF + the GIC sequence). Relabel the `Iommu` flowchart node "planned" and revise the prose to "BSP does not yet implement `Iommu`; the trait is a stub reserved for a future SMMUv3 ADR."

#### MR-014 — Architecture index marks the written `memory-management.md` "Planned — B2" and omits `task-loader.md` entirely
**Severity: Major** · Corroborating: **D1-004, X4b-003, X4b-004, X4a-011, X4a-012, X5-009**
**Files:** `docs/architecture/README.md:20` (status "Planned — B2", no link) and the index (no `task-loader.md` row); **reality:** `docs/architecture/memory-management.md` (270 lines, accurate, covers T-016..T-019), `docs/architecture/task-loader.md` (170 lines, accurate vs T-019).
**Description.** The index that claims to be the map of the architecture docs marks a fully-written Accepted document as not-yet-done and entirely omits an existing one — the `write-architecture-doc` skill's "index updated" acceptance criterion is unmet for the two newest subsystem docs.
**Why it matters.** A reader told to start from the architecture index will not discover the task-loader design at all and will think memory-management is unwritten — the same "delivered work described as not-yet-done" credibility pattern as the front-door drift (MR-015).
**Suggested fix.** Change `memory-management.md`'s row to `Accepted (v0.0.1 — MMU/PMM/AddressSpace/loader; T-016..T-019)` and make it a link; add a `task-loader.md` row (`Accepted v0.0.1 — T-019`).

#### MR-015 — Front-door docs materially understate delivery: "32 accepted ADRs," "architecture phase," "most code not yet written" (and CONTRIBUTING.md self-contradicts)
**Severity: Major** · Corroborating: **D5a-001, D5a-002, D5a-004, X4b-006, X4b-007, X4b-015, X5-002**
**Files:** `README.md:41` ("32 accepted ADRs"; actual 29 Accepted / 1 Deferred / 1 Superseded / 31 files), `:35,80` (hardcoded "27 unsafe entries," "UNSAFE-2026-0027," "259 tests"); `CLAUDE.md:7` ("most code is not yet written … current phase is architecture design"); `CONTRIBUTING.md:3` ("in the architecture phase … codebase not yet open") vs `:14` (same file: "the kernel boots end-to-end on QEMU virt"); `SECURITY.md:7` ("Phase A + B0/B1 closed").
**Description.** Four front-door docs disagree with each other and with reality (mid-Phase B, ~37 `.rs` files, kernel boots end-to-end) about what phase the project is in; the README's ADR count is wrong on both number and qualifier; CONTRIBUTING.md contradicts itself within one file.
**Why it matters.** CLAUDE.md is explicitly the entry point for the AI agents that do most of the work — an agent reading "most code not yet written / architecture design" will propose architecture-only work and mis-scope tasks, degrading the maintainer's force multiplier. CONTRIBUTING.md's "architecture phase" turns away exactly the ADR-vs-implementation reviewers the README invites. For a project whose brand is "auditable / honest," a wrong front-door ADR count is the first quantitative claim a skeptic checks. These are the cheapest high-leverage fixes in the review.
**Suggested fix.** Replace CLAUDE.md §"What this project is" with the README's accurate "mid-Phase B; MMU/PMM/AS/task-loader done; syscall ABI next" framing (D5a-001 gives drop-in text — but use "31 ADR files / 29 Accepted," not "32"). Rewrite CONTRIBUTING.md's opening to match the body. De-hardcode the volatile README counts (link to `docs/audits/unsafe-log.md` and `docs/decisions/README.md`).

#### MR-016 — `current.md` operational state is frozen pre-merge: T-019 still "In Review," wrong working branch, last-milestone three behind, internally self-contradictory
**Severity: Major** · Corroborating: **D4-003, D4-004, X4b-011, X4b-012, X4b-013, X5-005**
**Files:** `docs/roadmap/current.md:54-58` (T-019 "In Review on PR #31"; working branch `t-016-mmu-activation`; "Last completed milestone: B1") vs the same file's `:52` dated banners recording B2/B3 closures; `docs/analysis/tasks/phase-b/T-019-task-loader.md:6` (frontmatter `Status: In Review`, no `date_done`); git: PR #31 merged at `7f876af` (the commit immediately before HEAD).
**Description.** The live operational section lags the merge by three milestones and contradicts its own dated banners: T-019 merged 2026-05-16 but is still "In Review"; the named working branch closed 2026-05-08; "last completed milestone B1" while B2/B3 are recorded closed in the same file; the B4 closure trio (business + security + performance) has never fired because the Done flip was never recorded.
**Why it matters.** `current.md` is the project's promised "resume in under a minute" artifact (ADR-0013) and the single source of truth for "where are we." Three milestones stale + self-contradictory breaks the resume guarantee and means the closure-trio event-trigger that keeps the methodical-pace discipline honest never runs — the pace is honored in the *code* but the *bookkeeping that proves it* is lagging.
**Suggested fix.** Run the `start-task`/`conduct-review` update discipline: flip T-019 to `Done` with `date_done: 2026-05-16` (and check the satisfied DoD items); update the working branch to "none / awaiting B4 closure trio"; promote last-completed-milestone to B4; add T-018/T-019 to the phase-b task index (MR-019); trigger the B4 closure trio.

#### MR-017 — `IrqState(0)` means *opposite* things in the two `Cpu` implementors; the scheduler doc bakes in the BSP polarity
**Severity: Major** · Corroborating: **X4c-002** (newly surfaced by the code↔code pass; sibling to C5-N2)
**Files:** BSP `bsp-qemu-virt/src/cpu.rs:240-266` (`IrqState.0` = raw DAIF; DAIF bits set = masked, so `IrqState(0)` = IRQs **enabled**); `kernel/src/sched/mod.rs:636-638` (doc: "tasks begin masked … must call `restore_irq_state(IrqState(0))`"); test-hal `test-hal/src/cpu.rs:99-108` (`IrqState.0` = boolean `irqs_enabled`, so `IrqState(0)` = IRQs **disabled** — the inverse).
**Description.** The same literal `IrqState(0)` means "enabled" against the BSP and "disabled" against `tyrne_test_hal::FakeCpu`. The trait documents the value as opaque, so synthesising `IrqState(0)` is out-of-contract — yet the scheduler doc recommends exactly that synthesis with the DAIF meaning. Masked today only because the scheduler's *inline* test fakes make `restore_irq_state` a no-op; the moment a shared `tyrne_test_hal::FakeCpu` is used (the natural consolidation under MR-018's sibling), any test driving the enable-path would assert the inverse of production behaviour.
**Why it matters.** The bridge's soundness rests on IRQs actually being masked across `context_switch`; an inverted fake plus the doc-blessed `IrqState(0)` synthesis is an aliasing/critical-section hazard that no host fake currently verifies (pairs with MR-009).
**Suggested fix.** Either make the contract concrete enough that both impls agree on a canonical encoding (e.g. "0 = the state with IRQs unmasked") or forbid synthesising `IrqState` literals in kernel docs/code (obtain an "IRQs-enabled" token from the `Cpu` impl). At minimum, fix `tyrne_test_hal::FakeCpu` to the DAIF-compatible polarity so a shared fake cannot invert the BSP.

#### MR-018 — `FakeMmu` can never produce `OutOfFrames` or `BlockMapped`, so the kernel rollback contract it "verifies" runs against a more permissive shadow; `create_address_space` impl lacks `# Safety`/audit
**Severity: Major** · Corroborating: **C8-001, C8-002, C8-003, X4c-003, D5b-002, X3-002**
**Files:** `test-hal/src/mmu.rs:133` (`unsafe fn create_address_space` — no `# Safety`, no `// SAFETY:`, no audit), `:148-177` (`map` ignores `_frames`, flat HashMap — never `OutOfFrames`), `:179-193` (`unmap` — never `BlockMapped`); real impl `bsp-qemu-virt/src/mmu.rs:493-497,510`; kernel callers relying on the `Mmu::map` failure clauses `kernel/src/obj/task_loader.rs:682-691`, `kernel/src/mm/address_space.rs:719-737`.
**Description.** The fake silently under-honours two error variants of the contract every kernel test exercises. The `task_loader` rollback frees the leaf frame on `Err` *relying on clause (2)* and `cap_map` rides clauses (2)/(3), but the mid-walk `OutOfFrames` path that exercises that split is untestable through the fake (the loader's `OutOfFrames` tests drive PMM exhaustion, a different mechanism). The fake's `create_address_space` is also an `unsafe fn` with no `# Safety` doc and no audit tag (C8-001 rated this Major; X3 verified clippy cannot catch it because `missing_safety_doc` is exempt on trait impls whose declaration carries `# Safety`).
**Why it matters.** The host suite "verifies" the load-bearing `Mmu::map` failure contract (UNSAFE-2026-0025's rollback/error path) against a fake that cannot reproduce two of its variants — a fidelity gap behind a "smoke-verified"/"host-tested" claim. A real BSP that incorrectly returned `pa` as consumed on `OutOfFrames` would not be caught.
**Suggested fix.** Add a frame-consuming decorator fake (or extend `FakeMmu` to pull from the provider and return `OutOfFrames` when empty) and a `BlockMapped`-injecting fake; pin `cap_map`/`load_image` against them. Document the intrinsic gap on the `FakeMmu` struct doc. Add a `# Safety` section + audit tag to the three `create_address_space` impls (decide the policy: either codify that a trait-impl `unsafe fn` inherits the declaration's `# Safety`, or restate it — see MR-024 and X3-002).

#### MR-019 — ADR-0019 scheduler API sketch and the phase-b task index diverge from the shipped structures
**Severity: Major** · Corroborating: **D2b-002, D4-005, X4b-014**
**Files:** `docs/decisions/0019-scheduler-shape.md:153-185` (shows `ipc_send_and_yield`/`ipc_recv_and_yield`/`yield_now` as `&mut self` methods, a separate `TaskContexts<C>` struct, no `task_address_space_handles`/`idle`/`activate_address_space`); **code:** `kernel/src/sched/mod.rs:239-281,921,1026` (free `unsafe fn`s taking `*mut Scheduler<C>` per ADR-0021; context array inlined; B3/ADR-0028 fields added). Also `docs/analysis/tasks/phase-b/README.md:1-21` (index ends at T-017; T-018 and T-019 missing).
**Description.** ADR-0019's public API sketch was never updated with a rider after ADR-0021 (free-function bridge), ADR-0026 (idle slot), and ADR-0028 (`task_address_space_handles` + `activate_address_space` parameter) reshaped the scheduler — a reader following only ADR-0019 forms an incorrect mental model. Separately, the phase-b task index is two tasks behind the directory it indexes.
**Why it matters.** ADR/index drift on the project's most-audited subsystem and the navigability promise (ADR-0013 "open the folder and see the work"). Both are mechanical.
**Suggested fix.** Add a Revision-notes rider to ADR-0019 pointing to ADR-0021/0026/0028 for the evolved shape (append-only; leave the original sketch). Add T-018 (B3) and T-019 (B4) rows to the phase-b task index.

#### MR-020 — ADR-0008 `IrqGuard` signature changed from `&dyn Cpu` to generic `<C: Cpu>` with no Revision-notes rider
**Severity: Major** · Corroborating: **D2a-001, X4a-005**
**Files:** `docs/decisions/0008-cpu-trait.md:87-102` (specifies `IrqGuard<'a>` holding `&'a dyn Cpu`); **code:** `hal/src/cpu.rs:102-122` (`pub struct IrqGuard<'a, C: Cpu>`), with the rationale at `:86-91` (coercing a concrete type to a trait object at certain inlining depths can produce vtable references that alias unrelated `.rodata`).
**Description.** The shipped `IrqGuard` uses a concrete generic, not dynamic dispatch, for a documented safety-relevant reason — but ADR-0008 has *no* `## Revision notes` section at all, so its Decision-outcome signature is incorrect against the codebase and the vtable-aliasing rationale is absent from the design record.
**Why it matters.** A reader or agent relying on the ADR to understand the `IrqGuard` API is misled, and a safety-relevant architectural argument is missing from the decision record.
**Suggested fix.** Add a `## Revision notes` rider to ADR-0008 (mirroring the ADR-0009/0010/0017 rider pattern) recording the change to generic `<C: Cpu>`, the vtable/inlining aliasing hazard, and that the `Cpu` trait itself remains object-safe.

#### MR-021 — No phase covers a field-update / OTA / image-rollback mechanism, yet the product target is unattended device firmware
**Severity: Major** · Corroborating: **X5-004** (unique product-gap finding)
**Files:** product target `docs/roadmap/phases/phase-f.md:3,5,72` ("a real physical device runs Tyrne **as its firmware**"; 7-day-uptime bar); coverage that exists: persistence (E5), measured boot (G1), TEE (G1.5), crypto/signatures (G2), TLS (G3), signed release `.img` + key rotation (`release.md:102,114`); gap: a ripgrep across `docs/roadmap/phases/*.md` for update/OTA/A-B/dual-bank/recovery/reflash returns **no milestone**.
**Description.** Across all ten phases there is no milestone for delivering a *new* image to an already-running device. `release.md` produces and signs an initial image but covers nothing about updating a deployed one.
**Why it matters.** A security-first OS shipping as firmware for unattended multi-day/year operation needs a patch path — for such a project that is a *security* property, not a convenience. The threat model accepts "signing-key compromise handled by rotation," which implicitly assumes a deployed device can be re-trusted to a new key (an update path no phase builds). The very first deployed Tyrne device (the Phase F "reason to exist") would be unpatchable in the field — and update is painful to retrofit (it touches boot, image layout, A/B partitioning, rollback-on-failed-boot, signature verification). It stands out *because* everything around it (persistence, secure/measured boot, crypto, TLS) is on the plan.
**Suggested fix.** Add a milestone — most naturally Phase F (e.g. F5 — secure field update) or a late-G item — covering image transport, signature/measurement verification of the new image (ties to G1/G2), an A/B or dual-bank layout with automatic rollback on failed boot, and the capability model for "who may trigger an update." It need not be detailed now, but it should *exist* on the plan; at minimum add it to the Phase F/G "Open questions."

#### MR-022 — `unblock_receiver_on` / `yield_now` `panic!` on an invariant-guaranteed full ready queue; the invariant is duplicated across two `#[allow]` blocks
**Severity: Major** (forward security/robustness — X1 filed it under kernel-mode discipline) · Corroborating: **X1-F4, C5-002, X2-003**
**Files:** `kernel/src/sched/mod.rs:376-385` (`unblock_receiver_on`) and `:782-789` (`yield_now`); a third site (`add_task`, `:337`) maps the same `SchedQueue::enqueue` failure to a typed `SchedError::QueueFull`.
**Description.** Two sites enqueue under the same load-bearing invariant ("the running task is not in the ready queue, so ≤ `TASK_ARENA_CAPACITY-1` others are queued, so `enqueue` cannot fail") and both resolve the `Result` by `panic!` with near-identical `#[allow(clippy::panic, reason=…)]` prose. The panic is genuinely unreachable in correct v1 code (so this is not a present defect), but the invariant is exactly the kind a future change (preemption re-enqueueing the preempted task, multi-waiter wake, SMP) could quietly violate — converting the panic into a reachable kernel-mode crash. The `unblock_receiver_on` scan also runs *inside* the momentary `&mut Scheduler` borrow on the IPC send path (X2-003) — moot at v1 scale (16 iterations) but a forward note for the preemption ADR.
**Why it matters.** Centralising the invariant reduces drift risk; making the failure typed (or a single asserted helper) prevents a future change from turning "my enqueue failed" into a kernel crash.
**Suggested fix.** Factor a private `fn enqueue_ready(&mut self, h: TaskHandle)` encapsulating the "infallible by the no-double-enqueue invariant" panic with one SAFETY-style comment, called from both sites; leave `add_task`'s typed-error path as-is. Flag for the preemption/multi-waiter ADR (prefer an endpoint-indexed waiter list over the O(N) scan).

### Minor & Nit findings (grouped by area)

For Minor/Nit items the canonical entry is the owning track's finding ID; consult `tracks/<ID>.md` for full detail, file:line on every side, and suggested fix. Items already absorbed into a Blocker/Major above (e.g. the per-track GIC-version, stale-link, `create_address_space`-audit, and d8–d15 instances) are not repeated here.

**Kernel — capability (cap):**

| Finding | Sev | File:line | Track |
|---|---|---|---|
| `free_slot` publishes `free_head` before its bounds check (latent free-list corruption / panic on a future OOB caller) | Minor | `kernel/src/cap/table.rs:575-585` | C1-001, X1-F2 |
| `references_object` is O(tables × CAP_TABLE_CAPACITY) (one non-subtree-bounded op) | Minor | `kernel/src/cap/table.rs:531-536` | C1-002, X2 |
| `unlink_from_siblings` returns `InvalidHandle` for internal-bookkeeping inconsistency (conflated with stale-handle); add `debug_assert!` | Minor | `kernel/src/cap/table.rs:629-631,603` | C1-003 |
| Peer-of-a-root revoke asymmetry undocumented + untested | Minor | `kernel/src/cap/table.rs:170-229` | C1-004, X1-F1 |
| ADR-0014 `CapError` lists 5 variants; code has 7 (`HasChildren`, `WrongKind`) | Nit | `kernel/src/cap/mod.rs:163-191` vs ADR-0014:120-134 | C1-005, X4a-019 |
| `CapRights` operator surface asymmetric (`BitOrAssign` but no `BitAndAssign`/`Sub`) | Nit | `kernel/src/cap/rights.rs:109-127` | C1-006 |
| Forward-looking `from_raw`/`raw`/`KNOWN_BITS`/`difference`/`is_empty` have only test callers (intended ABI surface) | Nit | `kernel/src/cap/rights.rs:43-107` | C1-007 |
| `cap_copy`/`cap_derive` duplicate the child-list-prepend sequence | Nit | `kernel/src/cap/table.rs:202-223,285-302` | C1-008 |
| `MAX_DERIVATION_DEPTH ≤ u8::MAX` relied on but not `const`-asserted | Nit | `kernel/src/cap/table.rs:275` | C1-009 |
| `SlotEntry` size unverified vs ADR-0023's "32 bytes" claim; add `size_of` assertion | Nit | `kernel/src/cap/table.rs:71-77` | X2-N4 |

**Kernel — memory management (mm):**

| Finding | Sev | File:line | Track |
|---|---|---|---|
| PMM module banner stale ("No `unsafe`"; "next commit adds alloc/free/stats") — actively mis-points the reader | Minor | `kernel/src/mm/pmm.rs:13-16` | C2-001, X4a-014 |
| `alloc_frame` mutates bitmap/hint/counters *before* the fallible `from_aligned` return (self-documented latent leak) | Minor | `kernel/src/mm/pmm.rs:365-460` | C2-002 |
| `destroy_address_space`/`get_address_space_mut` `pub` but not re-exported (API-coherence) | Minor | `kernel/src/mm/address_space.rs:303-329`, `mod.rs:90-94` | C2-004 |
| No host test for `Pmm::new` `OutOfRange`-on-undersized-N (the bitmap-size invariant) | Minor | `kernel/src/mm/pmm.rs:196-198` | C2-005 |
| `cap_map` intermediate-frame `OutOfFrames` path untested at this layer (FakeMmu can't model it) | Minor | `kernel/src/mm/address_space.rs:719-737` | C2-006 (→ MR-018) |
| `alloc_frame` wrap-path O(N) nature undocumented; `first_zero_bit` is dead/hint-unaware | Minor/Nit | `kernel/src/mm/pmm.rs:356-363,685-687` | X2-002, X2-004 |
| Inverted-range guard partly shadowed by saturating `frame_count`; private bitmap helpers panic-on-OOB; prefixless test names; `PhysFrameRange::new` no validation; `MmuMapError`/`MmuUnmapError` split | Nit | `kernel/src/mm/pmm.rs:218-220,661-687`, `mm/mod.rs:63-88`, `address_space.rs:262-265` | C2-007..C2-011 |

**Kernel — IPC & objects (ipc/obj):**

| Finding | Sev | File:line | Track |
|---|---|---|---|
| `destroy_endpoint` can silently leak a parked `Capability` in release (guard is debug-only) | Minor | `kernel/src/obj/endpoint.rs:83-88`, `ipc/mod.rs:216-233` | C3-001, X1-010 |
| `RecvOutcome` derives only `Debug` while `SendOutcome` derives the full set (weakens test rigor) | Minor | `kernel/src/ipc/mod.rs:122-139` vs `:104-120` | C3-002 |
| No test exercises `ipc_notify` across a notification-slot generation bump | Minor | `kernel/src/ipc/mod.rs:408-420` | C3-003 |
| `ipc.md` "~990-line file" claim; file is 1425 lines (load-bearing for the "small auditable surface" rationale) | Minor | `docs/architecture/ipc.md:14` | C3-004 |
| `&` vs `&mut` table-borrow asymmetry across the four IPC entry points is correct but undocumented (a "tidy to uniform `&mut`" would break the bridge) | Minor | `kernel/src/ipc/mod.rs:411,486,267,346` | C3-005 |
| Pre-alpha dead code (`Notification::consume`, `Endpoint::id`, `get_*`); `Message` `Default`; lossy `CapError→IpcError` mapping; `unreachable!()` on a temporal invariant | Nit | `kernel/src/obj/*.rs`, `ipc/mod.rs:317-320,536-560` | C3-006..C3-009 |

**Kernel — task loader & sched:**

| Finding | Sev | File:line | Track |
|---|---|---|---|
| `WidenedRights` is a reachable delegated error omitted from `load_image` docs + tests | Minor | `kernel/src/obj/task_loader.rs:332-337,584-586` | C4-001, C4-002 |
| `lib.rs` `## Subsystems` rustdoc omits `mm` (and the loader's home in `obj`) | Minor | `kernel/src/lib.rs:21-33` | C4-003, X4a-016 |
| `intermediate_frame_count` exact-budget guarantee is BSP-coupled in a HAL-agnostic module (silent undercount risk for a 2nd BSP / RISC-V) | Minor | `kernel/src/obj/task_loader.rs:90-156` | C4-004, X4c-007 |
| Loader Nits: file dominated by tests (keep, don't decompose); `OutOfFrames` doc; `result_large_err`; "10-variant" prose drift | Nit | `kernel/src/obj/task_loader.rs` | C4-005..C4-008 |
| sched test module (~1417 lines) dominates the file; consider `sched/tests.rs` | Minor | `kernel/src/sched/mod.rs:1235-2652` | C5-001 |
| `unblock_receiver_on` O(N) scan (documented, bounded ≤16); forward note for multi-waiter | Minor | `kernel/src/sched/mod.rs:362-390` | C5-003, X2-003 |
| `ipc_send_and_yield` Phase-1 four-`&mut` block SAFETY comment under-states the distinctness requirement | Minor | `kernel/src/sched/mod.rs:941-961` | C5-005 |
| sched Nits: helper placement; IRQ-state doc subtlety; `QueueFull` only from `add_task`; "zero-initialised" vs `Default`; `if let Some` dead-else; spin vs WFI | Nit | `kernel/src/sched/mod.rs` | C5-N1..C5-N6, X4c-013 |

**HAL & BSP:**

| Finding | Sev | File:line | Track |
|---|---|---|---|
| `Mmu::map` `# Errors` cites an unrepresentable "user + kernel-only" case; the real rejected case (`DEVICE\|EXECUTE`) is unnamed | Minor | `hal/src/mmu/mod.rs:400-401` | C6-002, X4c-004 |
| `flags_to_descriptor_bits` silently ignores unknown `MappingFlags` bits (permission-encoding boundary) | Minor | `hal/src/mmu/vmsav8.rs:252-310`, `mmu/mod.rs:110-112` | C6-003 |
| `block_descriptor`/`page_descriptor` silent unaligned-PA truncation (can map the wrong frame) | Minor | `hal/src/mmu/vmsav8.rs:314-353` | C6-004 |
| `MapperFlush` does not bind the minting `Mmu`/AS (future multi-AS soundness cliff) | Minor | `hal/src/mmu/mod.rs:230-281` | C6-005 |
| Timer `# Panics` (divide-by-zero) sound but live in a `pub const fn` reachable from non-init callers | Minor | `hal/src/timer.rs:94-213` | C6-006 |
| No `ContextSwitch` fake in test-hal → duplicated/drifting inline `FakeCpu` (feeds MR-017) | Minor | `test-hal/src/lib.rs:18-21`, `kernel/src/sched/mod.rs:1252-1295` | C8-009, X4c-005 |
| `VecFrameProvider` does not honor the `FrameProvider` zero-fill contract the BSP walker depends on | Minor | `test-hal/src/mmu.rs:14-36` | C8-005, X4c-008 |
| `FakeIrqController` omits the `GIC_MAX_IRQ` range guard the BSP asserts | Minor | `test-hal/src/irq_controller.rs:94-99` | C8-004, X4c-009 |
| `MAIR` device-attr `0x00` aliases "unset"; WFI `nomem` vs future wake-hook; plain `+` vs `saturating_add` in console MMIO; `main.rs` 1308 lines (publish-boilerplate helper); 3× page-table-size encodings; W^X gap (ADR-0034-tracked) | Minor | `bsp-qemu-virt/src/{cpu,console,main,mmu_bootstrap}.rs` | C7-002..C7-007, X1-006, X1-009 |
| HAL/BSP Nits: `Iommu` stub; `IrqState`/newtype opacity; `now_ns` per-call divide; `BlockMapped`-on-map doc; `current_el` cfg-gating; `TrapFrame._reserved`; single-use GIC readers; `Cargo.toml` lints comment; module-doc staleness; timer/IRQ constant dups | Nit | `hal/src/*`, `bsp-qemu-virt/src/*` | C6-008..C6-013, C7-008..C7-013, X4c-010..X4c-012, X4c-014, C8-006..C8-008 |

**Build / CI / tooling:**

| Finding | Sev | File:line | Track |
|---|---|---|---|
| `host-clippy` alias lacks `--workspace` vs documented gate (incidental equivalence) | Minor | `.cargo/config.toml:45`, `infrastructure.md:68` | C9-008 |
| `.gitignore` comment names the old `.claude/skills/` tree | Minor | `.gitignore:44-46` | C9-009 |
| `run-qemu.sh` treats any unrecognized arg (incl. typo'd flags) as the kernel path; fixed `/tmp/qemu_int.log` collides | Minor | `tools/run-qemu.sh:23-39,54-67` | C9-010, C9-011 |
| `perf-harness.sh` 50% threshold `(n+1)/2` vs "fewer than 50%" prose | Minor | `tools/perf-harness.sh:322-329` | C9-012 |
| Coverage cache omits `~/.cargo/bin` (defensible but undocumented) | Minor | `.github/workflows/ci.yml:164-167` | C9-013 |
| CI header stale host-test count "111"; softfloat target documented but absent; QEMU-runner string in 3 places; `overflow-checks=true` rationale; `Cargo.lock` v4 floor; perf-harness report overwrite | Nit | `ci.yml`, `rust-toolchain.toml`, `Cargo.toml`, `Cargo.lock`, `perf-harness.sh` | C9-014..C9-019 |

**Standards / ADRs / roadmap / meta:**

| Finding | Sev | File:line | Track |
|---|---|---|---|
| `commit-style.md` Conventional-Commits not enforced; non-compliant commits on `main`; `audit`/`style` types undocumented | Major | `docs/standards/commit-style.md:38-53` | D3-005 |
| `code-style.md` says `missing_docs` is `deny`; workspace sets `warn` | Major | `code-style.md:58`, `Cargo.toml:36` | D3-006 |
| `security-review.md:88` gates a checklist item on `security-model.md` "not yet existing" — it exists (and SECURITY.md asserts it does) | Major | `security-review.md:88`, `SECURITY.md:7` | D3-007, X4b-005 |
| `testing.md:105` lists QEMU-smoke as an existing CI gate — none exists | Major | `testing.md:105` | D3-008 (→ MR-003) |
| ADR-late drift/hygiene: ADR-0027 references ADR-0030/0031 without placeholder files; ADR-0028 sim row 3 TLB-flush note; ADR-0035 "ADR-0028 no file today"; ADR-0029 broken anchor | Minor | `docs/decisions/0027,0028,0029,0035` | D2b-003..D2b-007, X4b-016, X4b-023 |
| ADR-early hygiene: template cites ADR-0018 as Deferred (it's Accepted); README "Creating an ADR" omits Simulation/Dependency-chain; ADR-0012 layout diagram misses `.boot_pt`; ADR-0017 "pencilled ADR-0030" | Minor/Nit | `docs/decisions/template.md:11`, `README.md`, `0012`, `0017` | D2a-005..D2a-012, X4b-022 |
| Standards drift: `infrastructure.md:19` toolchain claim (→ MR-002); `result_large_err`/`missing_errors_doc` claimed-but-unset; `code-style.md` ADR-0006/clippy.toml/allocator refs; `bsp-boot-checklist.md --debug` flag absent; `tyrne-log` crate "planned" not flagged; `release.md` article typo / signing-doc; one-sentence-per-line; `style` type; inline Turkish `Yüksek` | Minor/Nit | `docs/standards/*` | D3-009..D3-021 |
| Roadmap staleness: `phase-b.md` "How to start" obsolete; B4 milestone future-tense; test-count traceability; phase-d D4 ledger gap; phase-README boilerplate | Minor/Nit | `docs/roadmap/phases/*`, `current.md` | D4-009..D4-014 |
| Meta/front-door: `docs/README.md` layout omits analysis/roadmap/audits + "(Phase 2)"; CLAUDE.md rule-2 points unsafe-tracking at `docs/standards/` (log is in `docs/audits/`); glossary missing Badge/TCB/Reply-capability; `add-bsp` skill exceeds ~200-line soft limit; NOTICE slug `TyrneOS` | Minor/Nit | `docs/README.md`, `CLAUDE.md:16`, `docs/glossary.md`, `.agents/skills/add-bsp/SKILL.md`, `NOTICE:5` | D5a-005..D5a-012, X4b-017..X4b-021 |
| Audits/reports: Miri int-to-ptr cast advisories unmentioned in any report; coverage/perf reports lack T-019-era snapshot + Δ-context; test-only `unsafe impl Send/Sync` (FakeCpu/ResetQueuesCpu) lack `Audit:` tags | Minor/Nit | `docs/analysis/reports/*`, `kernel/src/sched/mod.rs:1261-1263,1911-1913` | D5b-003..D5b-006, X3-004 |
| Existing-reviews: pre-template `A6-completion.md` headings; `2026-04-28-B1-closure` not marked superseded in index; inline Turkish `Yüksek` in security-reviews README | Minor | `docs/analysis/reviews/**` | D5c-m01..D5c-m03 |
| Doc-count drift in proposed *fixes* (use 31 ADR files / 29 Accepted, not 32; skill path is `.agents/skills/...` not `docs/.agents/...`; host count 260 not 259) | Nit | (cross-track correction) | X4b cross-track notes |

---

## Dimension coverage matrix

Every dimension was applied to every area. Cell = brief health mark (✅ healthy · ⚠️ has findings, with the canonical MR / track refs). "Bus.-align" and some dimensions are N/A for narrow code areas (—).

| Area | Correctness | Optimization | Security | Maintainability | Refactor | Usability | Bus.-align | Doc-quality | Contradictions |
|---|---|---|---|---|---|---|---|---|---|
| kernel-cap | ✅ | ⚠️ C1-002 | ✅ (X1 Axis 1 OK) | ⚠️ C1-003/008 | ⚠️ C1-008 | — | — | ⚠️ MR-005-adj C1-005 | ⚠️ C1-005 |
| kernel-mm | ✅ | ⚠️ **MR-010** | ✅ (X1) | ⚠️ C2-004 | ⚠️ C2-002 | — | — | ⚠️ MR (pmm banner) | ⚠️ C2-001 |
| kernel-ipc-obj | ✅ | ✅ (O(1)) | ⚠️ C3-001/X1-010 | ⚠️ C3-002/005 | ⚠️ C3-008 | — | — | ⚠️ C3-004 | ✅ |
| task-loader | ✅ | ✅ | ✅ (X1-P2) | ⚠️ C4-004 | ✅ (keep) | — | — | ⚠️ C4-001/003 | ⚠️ C4-004 |
| sched | ✅ | ✅ (X2-P2) | ⚠️ **MR-009/022** | ⚠️ C5-001 | ⚠️ C5-002 | — | — | ⚠️ MR-017 | ⚠️ MR-017 |
| hal | ✅ (impl) | ⚠️ C6-010 | ⚠️ **MR-005** | ⚠️ C6-005 | ⚠️ C6-002 | — | — | ⚠️ **MR-005/013** | ⚠️ **MR-005** |
| bsp | ✅ | ✅ (X2-P1) | ⚠️ X1-006/009 | ⚠️ C7-005/006 | ⚠️ C7-005 | — | — | ⚠️ C7-001 | ⚠️ **MR-006** |
| test-hal | ✅ | ✅ | ⚠️ MR-018 | ⚠️ C8-009 | ⚠️ C8-008 | — | — | ⚠️ C8-002/003 | ⚠️ **MR-017/018** |
| build/CI | ⚠️ **MR-002/007** | ✅ | ⚠️ **MR-008** | ⚠️ C9-013 | — | ⚠️ C9-010 | — | ⚠️ **MR-002/003** | ⚠️ **MR-002/003** |
| architecture-docs | — | — | ✅ (security-model honest) | ✅ | — | ⚠️ MR-014 | — | ⚠️ **MR-012/013/014** | ⚠️ **MR-012/013** |
| ADRs | — | — | ⚠️ **MR-006** | ✅ (append-only) | — | — | — | ⚠️ **MR-005/006/020** | ⚠️ **MR-005/006/019/020** |
| standards | — | — | ✅ | ✅ | — | ⚠️ D3-014 | — | ⚠️ **MR-003** D3-005/006 | ⚠️ **MR-002/003** |
| roadmap/tasks | — | — | — | ⚠️ MR-016/019 | — | ⚠️ MR-016 | ⚠️ **MR-021** | ⚠️ **MR-001/016** | ⚠️ **MR-001/016** |
| meta/skills | — | — | ✅ | ✅ (skill shape) | — | ⚠️ MR-004 | ⚠️ **MR-015** | ⚠️ **MR-015** | ⚠️ **MR-004/015** |
| audits/reports | ✅ | ✅ (perf series) | ✅ | ✅ (amendments) | — | — | — | ⚠️ D5b-003/004 | ⚠️ MR-011 D5b |
| existing-reviews | — | — | ✅ | ✅ | — | — | ✅ | ⚠️ D5c-M01 | ✅ |

---

## Contradiction register

Confirmed contradictions, de-duplicated, pulled from X4a / X4b / X4c. Broken/stale cross-reference summary: **~49 confirmed** (42 `.claude/skills/` link-rot + 7 `hal/src/mmu.rs` path-rot) across live normative docs (X4b scan of 1,255 links / 80 docs; 1 false positive `new-doc.md`, 1 disclosed-future `CHANGELOG.md` excluded) — see MR-004.

### Code ↔ doc (X4a — 24 confirmed; 4 Major)

| Contradiction | Doc side | Code side | Correct | Sev | MR/Track |
|---|---|---|---|---|---|
| `ContextSwitch` contract omits d8–d15 | `hal/src/context_switch.rs:21-24` | BSP saves d8–d15, 168B (`cpu.rs:306-326`) | CODE | Major | MR-005 |
| ADR-0020 104B / FP-deferred | `0020:233-244,305` | 168B w/ `d8_d15` (`cpu.rs:303-319`) | CODE | Major | MR-005 |
| `overview.md` context-switch on `Cpu` | `overview.md:69` | separate `ContextSwitch` trait | CODE | Major | MR-013 |
| `overview.md` notify uses `EndpointCap`/endpoint | `overview.md:141,143` | `NotificationArena`/`Notification` (`ipc/mod.rs:408`) | CODE | Major | MR-012 |
| ADR-0008 `IrqGuard` `&dyn Cpu` | `0008:87-102` | `IrqGuard<'a, C: Cpu>` (`cpu.rs:102`) | CODE | Minor | MR-020 |
| ADR-0012/0006 GICv3/SMMUv3 | `0012:24`, `0006:47` | GICv2 + empty `Iommu` | CODE | Minor→ | MR-006 |
| `hal.md` BSP implements `Iommu` | `hal.md:53,153` | `pub trait Iommu {}` stub | CODE | Minor→ | MR-013 |
| `hal.md` `Cpu::enable_interrupts()` / PSCI / core-count | `hal.md:80,238` | `Cpu` lacks them | CODE | Minor | MR-013 |
| README index `memory-management.md` "Planned"; `task-loader.md` missing | `architecture/README.md:20` | both docs exist & accurate | DOC | Minor→ | MR-014 |
| 259 tests | `current.md:7`, `README.md:80`, T-019:135 | 260 (gate-repro) | CODE | Minor | MR-016/gate |
| pmm banner "No unsafe" | `pmm.rs:13-16` | live `write_bytes` (`:437`) | CODE | Minor | C2-001 |
| bsp cpu.rs header timer "`unimplemented!()`" | `cpu.rs:10-13` | fully implemented (`:491-561`) | CODE | Minor | C6/C7 |
| `lib.rs` Subsystems omit `mm` | `lib.rs:19-28` | `pub mod mm` (`:55`) | CODE | Minor | C4-003 |
| `boot.md` Stage 4 `tyrne_kernel::run` | `boot.md:18` | `kernel_entry` calls `start()` | CODE | Minor | D1-008 |
| `scheduler.md` class diagram omits `idle`/`task_address_space_handles` | `scheduler.md:23-29` | both fields present | CODE | Minor | D1-007 |
| ADR-0014 `CapError` 5 vs 7 | `0014:120-134` | 7 variants (`mod.rs:163`) | CODE | Nit | C1-005 |
| README "32 ADRs"; "kernel proper one unsafe entry"; ADR-0035 "0028 no file"; test-hal "all fakes" | various | reality | CODE/FS | Nit | MR-015, X4a-020/021/022/023 |

### Doc ↔ doc (X4b — 23 confirmed; 1 Blocker, 8 Major)

| Contradiction | Doc A | Doc B | Correct | Sev | MR |
|---|---|---|---|---|---|
| Phase C/D reuse live ADR numbers | `phase-c.md`, `phase-d.md` ledgers | live ADRs + phase-b ledger | Phase B | Blocker | MR-001 |
| GIC version: arch-docs/phase-b (v2) vs ADR-0004/0006/0011/0012 + phase-c/d (v3) | `overview.md:77`, `exceptions.md`, `phase-b.md:77` | ADRs + `phase-c.md:87`, `phase-d.md:32` | v2 | Major | MR-006 |
| `memory-management.md` index status; `task-loader.md` absent | `architecture/README.md:20` | files exist | files | Major | MR-014 |
| SECURITY.md "exists/Accepted" vs security-review.md "once it exists" | `SECURITY.md:7` | `security-review.md:88` | SECURITY.md | Major | MR-003-adj |
| status drift CONTRIBUTING/SECURITY/CLAUDE vs README/current.md | front-door docs | README/current.md | README | Major | MR-015 |
| CONTRIBUTING.md self-contradicts | `:3` | `:14` | line 14 | Major | MR-015 |
| `hal/src/mmu.rs` links broken (7) | ADR-0027, mem-mgmt, current, phase-b | module is `mmu/mod.rs` | mmu/mod.rs | Major | MR-004 |
| `.claude/skills/` rot (42 links, 11 files) | many | `.agents/skills/` | .agents | Major | MR-004 |
| overview.md notify-object vs glossary/ipc.md | `overview.md:143` | `glossary.md:69`, `ipc.md` | glossary/ipc | Minor | MR-012 |
| current.md internal (B1 vs B2/B3; T-016 branch vs Done; T-019 In Review vs merged) | `current.md:54-58` | `current.md:52` + git | git/banner | Minor | MR-016 |
| phase-b task index omits T-018/T-019; README "32 ADRs"; decisions index numbering gaps; docs/README layout; CLAUDE rule-2 audit path | various | reality | — | Minor | MR-019/015/004 |
| NOTICE `TyrneOS`; hal.md "CI uses SMMUv3" vs security-model "should be"; orphan "Phase 2/3"; template ADR-0018; ADR-0035 "0028 no file" | various | reality | — | Nit | MR-015/006 |

### Code ↔ code (X4c — 14 confirmed; 3 Major)

| Contradiction | Side A | Side B | Sev | MR |
|---|---|---|---|---|
| `ContextSwitch` contract under-enumerates vs BSP impl | `context_switch.rs:18-24` | BSP saves d8–d15 | Major | MR-005 |
| `IrqState(0)` = enabled (BSP) vs disabled (FakeCpu) | `cpu.rs:240-256` | `test-hal/cpu.rs:101` | Major | MR-017 |
| FakeMmu can't return `OutOfFrames`/`BlockMapped` (real contract kernel rollback rides on) | `test-hal/mmu.rs:148-193` | `bsp .../mmu.rs:493,510` | Major | MR-018 |
| `Mmu::map` `InvalidFlags` doc cites unrepresentable case; real `DEVICE\|EXECUTE` unnamed | `mmu/mod.rs:400-401` | both impls reject D\|E | Minor | C6-002 |
| No `ContextSwitch` fake → drifting inline FakeCpu | `test-hal/lib.rs` | `sched/mod.rs:1252` | Minor | MR-017 |
| `ENTRIES_PER_TABLE` defined twice differently; "512/4096" in ≥4 places | `mmu_bootstrap.rs:55` | `mmu.rs:57` | Minor | C7-006 |
| VMSAv8 shifts duplicated kernel↔BSP with conflicting L0/L1 *names* | `task_loader.rs:142-153` | `mmu.rs:50-53` | Minor | C4-004 |
| `VecFrameProvider` violates zero-fill contract BSP walker depends on | `test-hal/mmu.rs:33-35` | `bsp .../mmu.rs:510-518` | Minor | MR-018 |
| FakeIrqController omits `GIC_MAX_IRQ` guard | `test-hal/irq_controller.rs:94-99` | `gic.rs:317-322` | Minor | C8-004 |
| Timer IRQ 27 dup; `TaskStack` 4096 literal; RAM-extent two ways; `Scheduler::new` "zero" vs `Default`; `FakeTimer::set_now` can rewind | various | various | Nit | C7/C5/X4c |

---

## Unsafe audit reconciliation

From X3 (verification-and-extension of D5b), with C2/C4/C5/C7/C8 inputs. Method: full read of `docs/audits/unsafe-log.md` (610 lines, entries 0001–0027) + `unsafe-policy.md`; ground-truth `rg` enumeration of every `unsafe` token; per-site read; cross-tabulation of source `Audit:` tags against the log.

**Totals:**

| Metric | Value |
|---|---|
| Distinct `unsafe` language constructs (fn decls + impls + blocks + naked) | ~130 (production + test) |
| Audit-log entries | **27** (UNSAFE-2026-0001…0027); 26 Active, 1 Removed (0012) |
| Distinct audit IDs referenced in source | 27 — **all resolve** |
| Log entries with NO / stale code site (over-claimed) | **0** |
| Append-only / amendment-discipline violations (ADR-0025-class) | **0** |
| Code unsafe with NO log entry (under-documented) | **5** (1 production, 4 test) |

**Compliance.** Every production `unsafe {}` block and every audited `unsafe fn` carries a conforming three-part `// SAFETY:` comment with a live `Audit:` tag whose log body matches the code at HEAD. The four highest-risk production surfaces are textbook-conformant: `context_switch_asm` (`#[unsafe(naked)]` + sole `naked_asm!` body + compile-time size guard, 0008); PMM zero-fill (`write_bytes`, 0026 — five invariants, four rejected alternatives); task-loader byte-copy (`copy_nonoverlapping`, 0027 — runtime-enforced non-overlap preflight); the 4-level page-table walker (0025 — index-bound `debug_assert!`, leaf-written-last). UNSAFE-2026-0012 (the old aliasing window) is correctly `Removed`. The 0019/0020/0021 "Pending QEMU smoke verification" statuses are *correctly* still pending (the v1 demo arms no deadline, so those IRQ-take/dispatch arms are genuinely unexercised).

**Under-documented sites (5):**

| # | Site | Kind | Gap | Sev |
|---|---|---|---|---|
| 1 | `bsp-qemu-virt/src/mmu.rs:125` `from_existing_root` | inherent `pub unsafe fn` | **no log entry**; call site cites 0010+0014 (neither covers the op) → **needs UNSAFE-2026-0028** | **Major** (MR-011) |
| 2 | `test-hal/src/mmu.rs:133` `FakeMmu::create_address_space` | trait-impl `unsafe fn` | no `# Safety`, no `// SAFETY:`, no audit | Minor (MR-018) |
| 3 | `bsp-qemu-virt/src/mmu.rs:151` `QemuVirtMmu::create_address_space` | trait-impl `unsafe fn` | non-conforming one-line comment, no audit (X3 extension; D5b missed) | Minor |
| 4 | `kernel/src/obj/task_loader.rs:1750` `FailingMapMmu::create_address_space` (test) | trait-impl `unsafe fn` | 3-pt SAFETY but no audit ref | Minor |
| 5 | `kernel/src/sched/mod.rs:1261-1263,1911-1913` `FakeCpu`/`ResetQueuesCpu` `unsafe impl Send/Sync` (test) | 4× `unsafe impl` | adequate SAFETY, no `Audit:` tag | Nit |

**The CI-cannot-catch-it root cause (X3-005-class).** No CI lint reconciles the audit log against source: `missing_safety_doc` is exempt on trait-method impls whose declaration already carries `# Safety` (clippy by design); `undocumented_unsafe_blocks` only checks that *a* SAFETY comment exists, not that its `Audit:` tag is correct or that a log entry exists; log-vs-source reconciliation is the *manual quarterly* pass (`unsafe-policy.md §Enforcement`). All five gaps slipped through every PR gate for that reason. A lightweight CI check ("every `Audit:` tag references an existing ID; every non-test `unsafe fn` carries an `Audit:` tag") would have caught MR-011 at introduction.

**Policy gap.** `unsafe-policy.md` has *no* documented test-only exemption, yet the project has a large body of test-only `unsafe` that is (correctly) not logged. The implicit exemption should be codified: test-only `unsafe` in `#[cfg(test)]` doubles/harness code requires a `// SAFETY:` comment (clippy-enforced) but is exempt from individual audit-log entries; production `unsafe` reachable from non-test builds remains fully logged.

**Discipline verdict: EXEMPLARY.** The append-only / amendment discipline and source-side `Audit:` cross-referencing are the strongest application of `unsafe-policy.md`/ADR-0025 in the repository, verified line-by-line. The audit trail is fully trustworthy with the single Major exception of the missing `from_existing_root` entry.

> **Miri integer-to-pointer cast advisories** (4 sites: `pmm.rs:378,874`, `task_loader.rs:871`, `mm/mod.rs:168`) are advisory-only (not errors), reflect the documented identity-mapping pattern (0025/0026), and are unmentioned in any report — a paper-trail gap, not a code defect. `phys_frame_kernel_ptr` correctly needs no entry of its own (it is a *safe* cast; only the deref at call sites is unsafe). A `strict_provenance` migration is the forward-looking cleanup 0027 already names.

---

## Gate reproduction results

From `gate-reproduction.md` (run on a macOS arm64 host; rustc `1.94.0-nightly` matching the `nightly-2026-01-15` pin; qemu 10.2.2).

| # | Gate | Command | Status | Key numbers |
|---|---|---|---|---|
| 1 | fmt | `cargo fmt --all -- --check` | **PASS** | exit 0, no diff |
| 2a | host clippy | `cargo host-clippy` | **PASS** | 0 warnings (`-D warnings`) |
| 2b | kernel clippy | `cargo kernel-clippy` | **PASS** | 0 warnings on `aarch64-unknown-none` |
| 3 | host tests | `cargo host-test` | **PASS** | **260 passed** (42 hal + 175 kernel + 43 test-hal), 0 failed |
| 4 | kernel build | `cargo kernel-build` | **PASS** | aarch64-unknown-none ELF produced |
| 5 | miri | `cargo +nightly miri test --workspace --exclude tyrne-bsp-qemu-virt` | **PASS** | 260 passed, 0 failed; int→ptr cast warnings only (advisory) |
| 6 | coverage | `cargo llvm-cov --workspace --exclude tyrne-bsp-qemu-virt --summary-only` | **PASS** | Regions **96.26%** / Lines 95.76% / Functions 93.09% |
| 7 | QEMU smoke | `qemu-system-aarch64 -M virt … -kernel tyrne-bsp-qemu-virt` | **PASS** | full trace through `tyrne: all tasks complete`; ~27–33 ms; **629** guest_error events (all pre-existing PL011-disabled-UART noise) |

**All seven gates PASS.** Actual host-test count: **260**. Coverage: **96.26%** regions. QEMU smoke **success marker reached** (`tyrne: all tasks complete`); the smoke serial trace is byte-identical to the `current.md` T-019 banner; `-d int,unimp,guest_errors` event count is **629** (matches the T-019 banner exactly), all `PL011 data written to disabled UART` — no `Taking exception`, no `unimp`, no new fault classes. miri detected **zero UB / zero Stacked-Borrows violations**.

**Documented-claim drift (all Minor or Nit; no Blocker-severity drift):**

| # | Claim | Documented | Actual | Δ | Sev |
|---|---|---|---|---|---|
| D1 | host-test count (`current.md` T-019 banner, README, T-019 task file) | 259 | 260 | +1 | Minor (under-count, not a regression; +1 test landed in round-5 commit `5078944`) |
| D2 | workspace region coverage (`2026-04-27` follow-up) | 96.37% | 96.26% | −0.11pp | Minor (T-019 `task_loader.rs` at 93.83% pulled the total just below the post-T-011 high-water mark; both T-011 floors still met) |
| D3 | Miri int→ptr cast advisories | (unmentioned) | present at 4 sites | — | Minor (advisory; under audit control; no report names them) |
| D4 | `hal/src/mmu/mod.rs` coverage | 40.82% (old `hal/src/mmu.rs`) | 67.74% | +26.92pp | Nit (positive — file restructured in T-016) |
| D5 | guest-error count vs T-016 baseline | 379 | 629 | +250 | Nit (expected — new banner lines; matches T-019 claim exactly) |

---

## Prioritized follow-up recommendations

Concrete proposals, **not applied**. Each: what · why · rough effort (S/M/L) · whether it is a **task** or an **ADR**. Grouped by urgency.

### Do before more building

1. **Fix the d8–d15 context-switch contract.** What: amend `hal/src/context_switch.rs` `# Safety` (both occurrences) to enumerate `d8`–`d15` (and generalise to "the target ABI's full callee-saved set"); add an ADR-0020 Revision-notes rider (168B / FP-not-deferred). Why: a contract-literal 2nd BSP corrupts FP state across every yield. Effort: **S**. → **ADR rider + code-doc task** (route through boot-path/`unsafe` review). [MR-005]
2. **Renumber the Phase C / Phase D ADR ledgers.** What: shift all C/D ADR placeholders above the live Phase-B ceiling (start ~ADR-0036), propagate to every sub-breakdown + AC, record provenance in Notes. Why: prevents an agent overwriting a live Accepted ADR. Effort: **S**. → **task**. [MR-001]
3. **Write a supersession ADR for the GICv3/SMMUv3 + IOMMU statements.** What: one ADR correcting ADR-0004/0006/0012 to GICv2/no-IOMMU-in-v1 + append-only top-of-file redirect pointers; fix `phase-c.md:87` and the `hal.md` `Iommu` "planned" framing; state the DMA-scoping invariant as future-on-QEMU. Why: foundational ADRs contradict the build and the conflict-resolution rule points readers at the wrong doc. Effort: **M**. → **ADR + doc task**. [MR-006, MR-013]
4. **Make CI honest and complete.** What: (a) align toolchain — drop `rustup default stable`, install/select the pin, rename jobs, fix `ci.md`; (b) stop `RUSTFLAGS` clobbering config (move `-D warnings` to a mergeable place); (c) add or demote the audit/vet/qemu-smoke "required" gates and fix the coverage `continue-on-error` header contradiction; (d) align the clippy gate command. Why: gate integrity / reproducibility. Effort: **M**. → **task** (+ small standards-doc edits). [MR-002, MR-003, MR-007]
5. **Harden CI supply-chain.** What: SHA-pin every third-party action; add top-level `permissions: contents: read`; codify both in `infrastructure.md`. Why: a tag repoint on `taiki-e/install-action` is CI code-execution; least-privilege token. Effort: **S**. → **task**. [MR-008]
6. **Add `UNSAFE-2026-0028` for `from_existing_root`** and fix the call-site `Audit:` attribution. Why: the only production `unsafe fn` with no audit entry, at the boot/MMU boundary. Effort: **S**. → **task**. [MR-011]
7. **Refresh `current.md` + trigger the B4 closure trio.** What: flip T-019 to Done (`date_done: 2026-05-16`), fix working branch + last-milestone, add T-018/T-019 to the phase-b index, run the closure trio. Why: the resume-friendliness guarantee is broken and the pace-discipline trigger never fired. Effort: **S** (doc) + **M** (closure trio). → **task**. [MR-016, MR-019]
8. **Sweep the ~49 broken cross-references.** What: repo-wide over live docs: `.claude/skills/` → `.agents/skills/`, `hal/src/mmu.rs` → `hal/src/mmu/mod.rs`; fix `.agents/skills/README.md:76` and the `.gitignore` comment. Why: broken normative procedures (incl. the cargo-vet onboarding trigger). Effort: **S**. → **task**. [MR-004]

### Soon

9. **Wire Miri (and a lightweight unsafe-audit reconciliation) into CI** as a blocking gate on `sched/**`+`ipc/**`. Why: the only mechanical verifier of the raw-pointer aliasing discipline is manual; a lint reconciling `Audit:` tags would have caught MR-011. Effort: **M**. → **task** (K3-7). [MR-009, MR-011]
10. **Replace `could_yield_pa_overlapping`'s per-frame loop with interval arithmetic** (O(R)). Why: `pub`, precondition-free, quadratic for large ranges; first felt when images grow (B5+). Effort: **S**. → **task**. [MR-010]
11. **Reconcile front-door status** (CLAUDE.md / CONTRIBUTING.md / SECURITY.md / README counts) and the architecture index (`memory-management.md` status + `task-loader.md` row); de-hardcode volatile counts (link, don't cite). Why: CLAUDE.md mis-orients the agents that do the work; "auditable/honest" brand. Use 31 ADR files / 29 Accepted, host count 260. Effort: **S**. → **task**. [MR-015, MR-014]
12. **Fix the `IrqState` polarity inversion + add a `FakeContextSwitch`.** What: make `tyrne_test_hal::FakeCpu` use DAIF-compatible polarity (or make the contract concrete / forbid `IrqState` literal synthesis); add a `ContextSwitch` fake so scheduler tests can assert IRQ-mask changes. Why: a shared fake would invert production IRQ semantics; consolidates the duplicated inline fakes. Effort: **M**. → **task**. [MR-017]
13. **Close the FakeMmu fidelity gaps.** What: add a frame-consuming + `BlockMapped`-injecting decorator fake; pin `cap_map`/`load_image` against them; add `# Safety`+audit to the `create_address_space` impls; have `VecFrameProvider` zero (or document). Why: the host suite "verifies" the load-bearing `Mmu::map` failure contract against a more permissive shadow. Effort: **M**. → **task**. [MR-018]
14. **Add ADR-0019 / ADR-0008 Revision-notes riders** (scheduler free-function shape + B3 fields; `IrqGuard` generic + vtable rationale). Why: the most-audited subsystem's ADRs misdescribe the shipped API. Effort: **S**. → **ADR riders**. [MR-019, MR-020]
15. **Add an OTA / field-update milestone to the roadmap** (Phase F5 or late-G): image transport, signature/measurement verification, A/B with rollback-on-failed-boot, the "who may update" capability. Why: an unattended security-first firmware product is otherwise unpatchable in the field. Effort: **S** (plan) now; **L** later. → **roadmap task** (+ a future ADR). [MR-021]
16. **Reconcile the standards-vs-reality drift** (commit-style enforcement + `audit`/`style` types; `missing_docs` deny-vs-warn; `security-review.md` Phase-3 conditional; `testing.md` QEMU-smoke claim; `tyrne-log`/`result_large_err`/`missing_errors_doc` claimed-but-unset). Why: standards that overstate enforcement erode trust. Effort: **M**. → **task** (+ `propose-standard-change` where a real config change is wanted). [D3-005..D3-016]
17. **Codify the test-only `unsafe` exemption** in `unsafe-policy.md` (and add the missing test `Audit:` tags or the blanket clause). Effort: **S**. → **standards change**. [X3-003, D5b-006]

### Opportunistic

18. **Defensive-correctness polish:** reorder `free_slot` (head published last + `debug_assert!`); reorder `alloc_frame` to compute the fallible value first; add `debug_assert!` to `unlink_from_siblings`, the bitmap helpers, and the `MAX_DERIVATION_DEPTH ≤ u8::MAX` / `SlotEntry`-size / `ENTRIES_PER_TABLE==512` `const` assertions. Effort: **S** each. → **task**. [C1-001/003/009, C2-002/008, X2-N4, C7-006]
19. **Decompose the mega-files if desired:** extract `sched/tests.rs`; introduce `StaticCell::publish` to collapse `main.rs` boilerplate. (Keep `task_loader.rs` and `kernel_entry` linear — the rationale is sound.) Effort: **M**. → **task**. [C5-001, C7-005]
20. **De-duplicate "same fact, many encodings":** timer IRQ 27, `TaskStack` 4096→`PAGE_SIZE`, the 128 MiB RAM extent, the VMSAv8 shifts (align the L0/L1 *labels* — the one with a *current* inconsistency), ideally via a HAL `Mmu::intermediate_frames_for_span`. Effort: **M**. → **task**. [X4c-006/007/010/011/012, C4-004]
21. **Refresh the reports:** a `2026-05-21` coverage rerun (260/96.26%, note `mmu/mod.rs` 40.82%→67.74%); a Δ-context paragraph in the B3 perf report; a Miri-advisory note. Effort: **S**. → **task**. [D5b-003/004/005]
22. **Cosmetic/usability:** `run-qemu.sh` `--help` + unknown-flag rejection + PID-suffixed int-log; glossary Badge/TCB/Reply-capability; NOTICE slug `Tyrne`; README "(representative)" trace caveat; `docs/README.md` layout rows; CLAUDE rule-2 audit-log pointer. Effort: **S**. → **task**. [C9-010/011, D5a-005..D5a-012]

---

## Coverage appendix

**Confirmation: 251 / 251 in-scope files were read in full.** Every Wave-2 track's coverage checklist marks every owned file `[x] read in full`, with line counts verified (mostly via `wc -l`); the per-track totals reconcile to the `00-coverage-manifest.md` totals:

| Track | Files | Lines | All read in full? |
|---|---:|---:|---|
| C1-kernel-cap | 3 | 1577 | ✅ |
| C2-kernel-mm | 3 | 2744 | ✅ |
| C3-kernel-ipc-obj | 6 | 2278 | ✅ |
| C4-kernel-task-loader | 2 | 2328 | ✅ |
| C5-kernel-sched | 1 | 2652 | ✅ |
| C6-hal | 8 | 1961 | ✅ |
| C7-bsp | 12 | 3855 | ✅ |
| C8-test-hal | 7 | 1236 | ✅ |
| C9-build-infra | 12 | 1111 | ✅ |
| D1-architecture | 10 | 2220 | ✅ |
| D2a-adr-early | 20 | 3063 | ✅ |
| D2b-adr-late | 13 | 2377 | ✅ |
| D3-standards | 15 | 2178 | ✅ |
| D4-roadmap-tasks | 43 | 4067 | ✅ |
| D5a-meta-core | 30 | 2716 | ✅ |
| D5b-audits-reports | 8 | 1235 | ✅ |
| D5c-existing-reviews | 58 | 8159 | ✅ |
| **TOTAL** | **251** | **45,757** | **✅ 251/251** |

**Files a track could not fully cover: none.** Every file in the manifest is owned by exactly one Wave-2 track and was read in full by that track's agent (each track also read substantial additional context — ADRs, standards, caller call-sites, the audit log — to verify claims, listed in each track's coverage checklist). The gate-reproduction track independently executed all seven gates on a runner. The cross-cutting tracks (X1–X5) re-read the security-sensitive / contradiction-relevant source directly rather than relying on the Wave-2 tracks' word.

**Out of scope (explicitly excluded, per the manifest):**
- `docs/analysis/reviews/master-review/**` — this review's own output (would be self-referential).
- `docs/analysis/technical-analysis/**` — untracked / gitignored, per the maintainer. (Several tracks note these untracked files contain additional stale `.claude/skills/` references; they are deliberately *not* findings, consistent with the historical-snapshot exclusion.)

Historical review snapshots under `docs/analysis/reviews/**` (the D5c corpus) were read in full as in-scope files, but their stale `.claude/skills/` links are point-in-time records (per `current.md:11`) and are *not* counted among the ~49 live broken links.
