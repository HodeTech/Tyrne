# X5-business-alignment — goals ↔ delivery coherence (master review, commit 288ddb2)

- **Reviewer:** X5 agent (business-logic alignment) — Claude Opus 4.7
- **Anchored to:** commit `288ddb2` ("docs(readme): rewrite root README for a first-time reader")
- **Lens:** Is what has been BUILT and DECIDED coherent with the project's stated GOALS, POSITIONING, and PLAN? This is product/business-logic alignment, not code correctness.
- **Method:** Read the project's own framing (README, architecture overview + security-model, ADR-0001/0004/0013/0015, full roadmap incl. phases A–J, architectural-principles P1–P12). Cross-read the Wave-2 tracks (D4-roadmap-tasks, D5a-meta-core, D1-architecture, D5c-existing-reviews, gate-reproduction) for built-vs-claimed ground truth. Independent verification of GIC-version drift, ADR status counts, and roadmap product-capability coverage via ripgrep + read-only git.

---

## Summary + overall alignment verdict

**Verdict: STRONGLY ALIGNED on substance; a cluster of stale framing/forward-plan artifacts erodes the project's single most valuable asset — its credibility — and one genuine product-capability gap (no field-update mechanism) sits in the path to the smart-home-first goal.**

The good news first, because it is the headline. Tyrne is one of the rare pre-alpha projects where the architecture, the decisions, and the build are mutually coherent and the positioning is *earned*, not asserted. The high-security value proposition (capability-based, no ambient authority, smallest-defensible TCB, drivers-in-userspace, audited `unsafe`, no proprietary blobs) is reflected end-to-end in the code that exists: the kernel proper exposes exactly one `unsafe` block (the task-loader byte-copy), capabilities are move-only Rust types, every privileged wrapper is cap-gated, and the gate-reproduction track independently confirms 260/260 host tests, 260/260 miri, 96.26% region coverage, and a byte-stable QEMU smoke trace through `tyrne: all tasks complete`. The "Done" claims for the boot/IPC/MMU/PMM/address-space/task-loader work are justified by the code and the gates. The AI-integration stance (ADR-0015) is a textbook example of goal coherence: it rejects in-kernel AI *because* it would violate P2/P7 and the verification path, and parks AI in an opt-in Phase J — the positioning and the architecture agree. The methodical-pace principle (P12, "no half-finished subsystems on main") is being honored substantively: every milestone B0–B4 closed behind a smoke trace + clean gate count, the one regression (B1) was rolled back and re-issued honestly, and the task-loader deliberately stops at "produces a `LoadedImage`, does not run it" rather than shipping a half-wired runnable-task stub.

The bad news is concentrated and fixable, but it matters disproportionately for *this* project because Tyrne's entire differentiation is "auditable, honest, decisions-on-the-record." Three things undercut that:

1. **Promise-vs-delivery drift in the front door.** The README claims "32 accepted ADRs" (actually 29 Accepted / 1 Deferred / 1 Superseded / 31 files), CLAUDE.md still says "most code is not yet written … the current phase is architecture design," and CONTRIBUTING.md still calls Tyrne "in the architecture phase" — three milestones and ~37 source files out of date. A first-time reader (human or the AI agents that CLAUDE.md is explicitly written for) forms a materially wrong model of the project.
2. **A foundational-ADR-vs-reality contradiction the append-only policy has frozen in place.** The three earliest platform/boot ADRs (0004, 0006, 0012) still assert QEMU `virt` is **GICv3 + SMMUv3** and that the BSP implements them; the code ships a **GIC v2** driver and an *empty* `Iommu` stub. The architecture docs were corrected in the 2026-05-06 review, but the ADRs — which the docs themselves declare authoritative on conflict — were not, and *cannot* be edited in place under the append-only rule. Phase C still plans "GICv3 SGI" on this false premise.
3. **Roadmap forward-plan corruption (Blocker-class, already raised by D4).** Phase C and Phase D reuse ADR numbers 0027–0036 that are *already Accepted and live on `main`* for Phase B. Any agent following the phase plan to "write ADR-0027" collides with a real decision.

And one genuine **product gap**: across all ten phases there is no milestone for an **in-field firmware update / OTA / A-B-rollback mechanism**. The product target (Phase F: "a real physical device in the maintainer's smart-home setup runs Tyrne as its firmware," with a 7-day-uptime acceptance bar) implies devices that will need patching; `release.md` produces a signed initial `.img` but nothing covers updating a deployed device. Measured boot (G1), secure boot, persistence (E5), and crypto (G2/G3) are all on the plan — update is the conspicuous omission.

None of these are "stop the build" in the compile sense. In the strategic sense, finding X5-001 (foundational-ADR drift) and X5-002 (front-door promise drift) should be resolved before the project invites the external ADR review it says it wants, and X5-003 (the ADR-number collision) must be resolved before Phase C starts. The smart-home path is otherwise sound and, encouragingly, *concrete* — Phase E and F name real protocols (Matter/MQTT), real buses (I2C/SPI/GPIO on BCM2711), and real acceptance criteria.

**Severity counts: Blocker 1 · Major 4 · Minor 4 · Nit 2 · Praise 6.**

(The single Blocker, X5-003, is the roadmap ADR-number collision, which this track confirms from the strategic angle and defers to D4-001/D4-002 for the mechanical fix. It is counted once here, not double-counted against D4.)

---

## Findings

### Blocker

#### X5-001 — Foundational platform/boot ADRs (0004, 0006, 0012) contradict the shipped hardware reality, and the append-only policy has frozen the contradiction

**Evidence:**
- `docs/decisions/0004-target-platforms.md:31` — "QEMU's `virt` machine is a fully documented, standard, deterministic aarch64 environment (**GICv3**, PL011 UART, virtio transports, PSCI …)."
- `docs/decisions/0006-workspace-layout.md:47` — `tyrne-bsp-qemu-virt` … "`Cpu`/`Mmu`/`IrqController`/`Timer`/`Console`/`Iommu` impls for **GICv3 + PL011 + SMMUv3**."
- `docs/decisions/0012-boot-flow-qemu-virt.md:24` — hardcoded "`GICv3` distributor at `0x0800_0000`."
- Reality (confirmed by D1-architecture claims register + grep): `bsp-qemu-virt/src/gic.rs` ships a **GIC v2** driver (ADR-0011, UNSAFE-2026-0019, `exceptions.md` §"GIC v2 driver" all say v2); `hal/src/lib.rs:62` `pub trait Iommu {}` is an **empty stub** with no BSP implementation (D1-003).
- `docs/architecture/overview.md:77` (corrected): "The QEMU `virt` machine **defaults to GICv2**; `bsp-qemu-virt` ships a v2-only driver … GICv3 requires `-machine gic-version=3` and is out of scope for v1."

**Why it matters strategically:** Tyrne's entire pitch is "decisions are on the record and the record is trustworthy" (P8; README "Documented decisions, append-only"). The *foundational* ADRs — the first ones a reader is told to read in ADR order — assert hardware facts the build contradicts. Worse, the project's own convention (`overview.md`: "the ADR is authoritative when they disagree") means a careful reader is told to *believe the wrong document*. The 2026-05-06 review fixed the architecture docs but left the ADRs, because ADRs are append-only and editing the body is a policy violation. So the contradiction is now structural, not accidental, and it has already propagated forward into Phase C's plan (X5-003 / phase-c.md:87 "GICv3 SGI"). This is exactly the class of latent rot that erodes a high-assurance project's credibility faster than a bug would.

**Recommendation:** Use the project's own supersession mechanism, which exists precisely for this. Write one short ADR (e.g. ADR-0052 "QEMU virt is GICv2/no-IOMMU in v1; corrects the GICv3/SMMUv3 statements in ADR-0004/0006/0012") that records the corrected hardware baseline and explicitly supersedes the affected statements (not the whole ADRs). Add a one-line revision-note pointer at the top of 0004/0006/0012 ("§X corrected by ADR-0052") — which is append-only-legal — so a reader hitting the stale line is redirected. Then fix the forward references (phase-c.md:87 GICv3→GICv2/GIC-400 reality, and the `Iommu` "planned" framing per D1-003). This also forces a healthy decision: the security-model leans on SMMUv3-in-CI as the DMA-capability gate (`security-model.md:60,99,327`) — if no `Iommu` impl exists yet, the "DMA is capability-scoped where hardware permits" invariant is currently *aspirational on QEMU too*, and that should be stated honestly rather than implied as present.

---

### Major

#### X5-002 — Front-door docs materially understate delivery: "32 accepted ADRs," "architecture phase," "most code not yet written"

**Evidence:**
- `README.md:41` — "The current count is **32 accepted ADRs**." Actual: 29 `Status: Accepted`, 1 Deferred (ADR-0023), 1 Superseded (ADR-0022), 31 files (independently confirmed: `rg -l "Status:.*Accepted"` = 29). (D5a-004.)
- `CLAUDE.md:7` — "The project is pre-alpha — **most code is not yet written**, and the current phase is **architecture design** captured in ADRs." Reality: kernel boots end-to-end, 37 `.rs` files, mid-Phase B (D5a-001).
- `CONTRIBUTING.md:3` — "Tyrne is currently **in the architecture phase** — … the codebase is not yet open for code contributions" — and the *same file* at line 14 says "the kernel boots end-to-end on QEMU virt (Phase A + B0/B1 closed)." Self-contradictory (D5a-002).
- `README.md:35,80` — hardcoded "27 `unsafe` audit entries," "UNSAFE-2026-0027," "259 tests" (the last is also stale: actual 260 per gate-reproduction).

**Why it matters strategically:** CLAUDE.md is explicitly the *entry point for the AI agents that do most of the work on this project*. An agent reading "most code is not yet written, current phase is architecture design" will propose architecture-only work, mis-scope tasks, or fail to look for the running kernel — directly degrading the maintainer's force multiplier. CONTRIBUTING.md's "architecture phase" turns away exactly the kind of contributor the README invites (someone who would review ADRs *against the real implementation*). And for a project whose brand is "auditable / honest," a front-door ADR count that is simply wrong is an own-goal: it is the first quantitative claim a skeptical reader checks.

**Recommendation:** (1) Replace the CLAUDE.md §"What this project is" status sentence with the README's accurate "mid-Phase B; MMU/PMM/AS/task-loader done; syscall ABI next" framing (D5a-001 gives drop-in text). (2) Rewrite CONTRIBUTING.md's opening to match README "pre-alpha, kernel boots" and delete the internal contradiction. (3) De-hardcode the volatile counts in README (link to `docs/audits/unsafe-log.md` and `docs/decisions/README.md` rather than citing snapshot numbers; per D5a-011/012). (4) Fix the ADR count to "29 Accepted" or, better, "see the index" so it cannot rot again. These are the cheapest high-leverage fixes in the whole review: they cost minutes and they protect the one asset (trustworthy front door) the project most depends on.

#### X5-003 — Roadmap forward-plan reuses ADR numbers already Accepted on `main` (Phase C and D)

**Evidence (confirmed independently; mechanical fix owned by D4-001/D4-002):**
- `docs/roadmap/phases/phase-c.md:17,37,56,79,98,118–122` assigns ADR-0027…0031 to milestones C1–C5. But ADR-0027 (kernel VMem layout), 0028 (address-space data structure), 0029 (userspace image format) are **Accepted and on `main`**; 0030/0031 are reserved for Phase B5 (syscall ABI / initial syscall set).
- `docs/roadmap/phases/phase-d.md:17,36,53,87,105,162–166` assigns ADR-0032…0036; **ADR-0032 (endpoint rollback) and ADR-0035 (PMM) are already live**, 0033/0034 are named Phase-B placeholders.
- `ls docs/decisions/` confirms no 0030/0031/0033/0034 *files* yet — so the collision is currently only in the plan, not yet on disk.

**Why it matters strategically:** This is the one finding that can cause active damage to a *correct* artifact. The roadmap is the instruction set the maintainer (and agents) follow to do the next work; an agent told by phase-c.md to "write ADR-0027 — Secondary core start protocol" would create a filename collision with the live, Accepted kernel-VMem decision, silently corrupting a load-bearing record. It directly threatens the "decisions-on-the-record are trustworthy" guarantee at the moment Phase C opens. Severity Blocker in the strategic sense: resolve before any Phase C/D building.

**Recommendation:** Per D4-001/D4-002, renumber Phase C and D ADR placeholders to start above the live ceiling (first free slot is ADR-0036 after Phase B's 0033/0034 placeholders and Phase E's 0037+; pick a common base and propagate to every in-text reference). Add the "renumbered, was ADR-00xx" note in the ledger Notes column, mirroring the exemplary precedent D4-P02 praises in phase-b.md.

#### X5-004 — No phase covers a field-update / OTA / image-rollback mechanism, yet the product is "device firmware"

**Evidence:**
- Product target — `phase-f.md:3,5` "A real physical device … runs Tyrne **as its firmware**"; `phase-f.md:72` acceptance bar "Device runs 7 days uninterrupted … reacts to commands."
- Coverage that *does* exist: persistence (E5 filesystem), measured boot (G1), secure boot / TEE (G1.5), crypto + signatures (G2), signed release `.img` + key rotation (`release.md:102,114`).
- Gap: ripgrep across `docs/roadmap/phases/*.md` for update/OTA/A-B/dual-bank/recovery-partition/reflash/field-update returns **no milestone**. `release.md` describes producing and signing an image, not deploying a *new* image to an already-running device.

**Why it matters strategically:** A smart-home device that ships as firmware and is expected to run unattended for days/years needs a way to receive security patches — and for a *security-first* OS that is a security property, not a convenience. The threat model (security-model.md) accepts "compromise of the maintainer's signing key … handled by rotation," which implicitly assumes a deployed device can be re-trusted to a new key — i.e. it assumes an update path that no phase builds. Without an update story, the very first deployed Tyrne device (the Phase F "reason to exist" milestone) is unpatchable in the field, which contradicts the high-assurance positioning at the moment it first meets reality. This is the kind of capability that is painful to retrofit (it touches boot, image layout, A/B partitioning, rollback-on-failed-boot, and signature verification) and is much cheaper to slot into the plan now.

**Recommendation:** Add a milestone — most naturally a Phase F milestone (F5 — secure field update) or a dedicated late-G item — covering: image transport, signature/measurement verification on the new image (ties to G1/G2), an A/B or dual-bank layout with automatic rollback on failed boot, and the capability model for "who may trigger an update." It need not be detailed now (later phases are deliberately sketchy), but it should *exist* on the plan so the smart-home exit bar is honestly reachable. At minimum, add it to the Phase F / Phase G "Open questions" so the omission is acknowledged rather than silent.

#### X5-005 — `current.md` operational state is frozen pre-merge, masking the true milestone position (B4 implementation-complete)

**Evidence (confirmed by D4-003/D4-004 and git):**
- `current.md:54–55` lists T-019 as "In Review on PR #31"; git shows PR #31 merged at `7f876af` (the commit immediately before HEAD).
- `current.md:57` names `t-016-mmu-activation` (Done 2026-05-08) as the working branch.
- `current.md:58` "Last completed milestone: **B1**" — three behind reality (B2 closed 05-09, B3 closed 05-14, B4 implementation-complete on the 05-16 merge); the *same file* records B2/B3 closures in its dated banners (internal contradiction).
- `T-019-task-loader.md:6` frontmatter still `Status: In Review`; no `date_done`.

**Why it matters strategically:** `current.md` is the project's promised "resume in under a minute after a long pause" artifact (ADR-0013 decision driver) and the single source of truth for "where are we." When it is three milestones stale and internally self-contradictory, the maintainer's resume-friendliness guarantee is broken and the B4 closure trio (business + security + performance review) — which is *the* event-trigger that keeps the methodical-pace discipline honest — never fires. The pace discipline (P12) is being honored in the *code*, but the *bookkeeping* that proves it is lagging, which over time makes "is this milestone really done?" unanswerable from the repo.

**Recommendation:** Run the `start-task` / `conduct-review` update discipline: flip T-019 to Done with `date_done: 2026-05-16`, update the working-branch line to "none / awaiting B4 closure trio," promote last-completed-milestone to B4, and trigger the B4 closure trio per the B3 precedent. This is process hygiene, but for a process-is-the-product project it is load-bearing.

---

### Minor

#### X5-006 — `phase-b/README.md` task index is two tasks behind (missing T-018, T-019)

`docs/analysis/tasks/phase-b/README.md` ends at T-017; T-018 (Done) and T-019 (merged) are absent though both files exist and are git-tracked (D4-005). For a project whose navigability is a stated value (ADR-0013 "phase-scoped browsing"), an index that silently omits the two most recent — and most significant — tasks undercuts the "open the folder and see the work" promise. **Recommendation:** add the two rows (per D4-005).

#### X5-007 — "First real hardware = Pi 4" positioning sits on a board the security model can only partially serve, and this trade-off is under-surfaced in the headline framing

The README and ADR-0004 lead with Raspberry Pi 4 as the first hardware target. But the security model (`security-model.md:60`) notes Pi 4 has **no SMMU** ("any bus-master device … can read or write arbitrary DRAM"), and Phase F (`phase-f.md:91`) notes Pi 4 Wi-Fi needs a **proprietary blob** (conflicting with P7, forcing Ethernet / USB-dongle / documented-exception). Both caveats are honestly documented *where a careful reader digs*, but the top-level "first hardware: Pi 4" framing — and the smart-home story that rides on it — does not foreground that the *flagship security properties* (DMA capability-scoping; blob-free wireless) are exactly the ones Pi 4 cannot fully deliver. This is not a contradiction (the caveats exist), but it is a positioning tension: the first device the product targets is the one where the differentiation is weakest. **Recommendation:** add a one-line "security caveat on Pi 4 (no SMMU; Wi-Fi blob)" pointer near the README hardware-tier table, so the trade-off is visible at the headline level, not only in ADR-0004 / security-model deep cuts. Strategically worth a sentence; it pre-empts the "you market security but your first board can't enforce it" critique.

#### X5-008 — Smart-home "first product domain" is concrete in the plan but invisible in the code/decisions until Phase E/F, with no early de-risking probe

The smart-home target is the project's *raison d'être* (`phase-f.md:5`), and the plan for it is commendably concrete (Matter/MQTT, I2C/SPI/GPIO on real BCM2711, BME280 sensor read, 7-day uptime). But it lives entirely in the medium-detail Phase E/F files; nothing in Phases A–C touches a smart-home-shaped constraint, and there is no early "throwaway probe" to validate the riskiest product assumptions (e.g. that a chosen Matter/MQTT Rust crate is `no_std + alloc`-compatible and `cargo-vet`-clean — flagged as an open question in E6/F3 but not de-risked). For a multi-year solo project, discovering in Phase F that the protocol layer has no viable open Rust implementation would be expensive. **Recommendation:** keep the phasing (it is correct to not build drivers before userspace exists), but consider a low-cost early spike — a paper feasibility check of the Matter/MQTT/`smoltcp`/filesystem crate landscape against `no_std + alloc` + license + vet posture — recorded as a short technical-analysis note now, so the product-critical dependency risk is surfaced years before the phase that depends on it. This honors "sequencing over scheduling" while protecting the goal.

#### X5-009 — `docs/architecture/README.md` index lists `memory-management.md` as "Planned — B2" and omits `task-loader.md`

The architecture index (`README.md:20`) marks a 270-line *written, Accepted* document as "Planned," and entirely omits the existing `task-loader.md` (D1-004). Same class as X5-002 (delivered work described as not-yet-done), localized to the architecture map a "reader who wants the design" is told to start from. **Recommendation:** flip the status and add the missing row (per D1-004).

---

### Nit

#### X5-010 — README "Status at a glance" is excellent but pins volatile specifics that will rot

`README.md:60–72` reproduces the exact boot trace including frame counts and addresses (`32599 frames`, `bootstrap AS root = 0x40095000`). It is currently accurate (gate-reproduction confirms byte-identical), and the honesty is laudable — but addresses/counts shift with any allocator or layout change and will silently mislead. **Recommendation:** keep the trace as illustrative but add "(representative; exact addresses/counts vary)" so a future drift is not read as a regression.

#### X5-011 — `NOTICE` uses repo slug `TyrneOS`; the rest of the project uses `Tyrne`

`NOTICE:5` points to `github.com/cemililik/TyrneOS` vs `Tyrne` everywhere else (D5a-010). Tiny, but it is a public artifact and the project just went through a rename precisely to avoid identity confusion. **Recommendation:** correct to `Tyrne`.

---

### Praise

#### X5-P01 — The AI-integration stance (ADR-0015) is a model of goal coherence

Rather than chase "AI-native OS" hype, ADR-0015 reasons from the project's own principles (P2 TCB-minimization, P7 no-blobs, the formal-verification path, determinism) to *exclude* AI from the kernel, then provides four named, zero-cost-today hooks and an opt-in Phase J. The positioning ("we optimize for durability and auditability, not first-mover") and the architecture agree perfectly, and the decision is recorded so it does not get re-litigated quarterly. This is exactly how a security-first project should handle a tempting-but-corrosive feature request.

#### X5-P02 — Delivery genuinely matches the security value proposition where code exists

The differentiation is not branding. The kernel proper exposes one `unsafe` block; capabilities are move-only (`!Copy`, `!Clone`) Rust types; every privileged operation is cap-gated; resource bounds are compile-time and return typed errors rather than panicking. gate-reproduction independently confirms 260/260 tests, 260/260 miri (zero UB), 96.26% region coverage, and a clean smoke trace. The "smallest defensible TCB" claim is measured against the build, not asserted.

#### X5-P03 — P12 ("no half-finished subsystems on main") is honored substantively, not just stated

The task loader deliberately stops at "produces a `LoadedImage`; does not run it" because running gates on the B5/B6 syscall ABI — the project resisted shipping a tempting half-wired runnable-task stub. B0–B4 each closed behind a verbatim smoke trace + clean `-d guest_errors` count, and the one regression (B1, 2026-05-06) was rolled back and re-issued as a smoke-verified Done rather than papered over. The methodical-pace motto is visible in the commit history, not just the README.

#### X5-P04 — The smart-home-first path is concrete, not merely aspirational

Where many "we'll target IoT" projects wave at the domain, Phase E/F name real protocols (Matter/MQTT), real buses and a real SoC (I2C/SPI/GPIO on BCM2711), a real sensor (BME280), and a falsifiable acceptance bar (7-day uninterrupted uptime; state reflected in a real hub). The phase ordering toward it (kernel core → userspace → multi-core/Pi4 → drivers+services → smart-home) is sound, and the "reason to exist" framing keeps the product goal load-bearing rather than decorative.

#### X5-P05 — Honest, explicit out-of-scope discipline throughout

The security model enumerates what it does *not* defend (physical attackers, microarch side channels, no-IOMMU DMA, signing-key compromise), ADR-0004 documents the Jetson-blob caveat the moment the decision is made, and Phase files carry "Out of scope" headers. This "say what you don't do" discipline is itself a high-assurance signal and is rare at pre-alpha.

#### X5-P06 — The review/decision machinery is the project's strongest dimension and directly serves the positioning

Typed reviews (business/code/security/performance) with master plans, append-only ADRs with supersession, the `write-adr` §Simulation-table discipline that demonstrably eliminated smoke regressions from B2 onward, and per-task review histories rich enough to reconstruct each PR's arc (including *rejected* findings with rationale). For an OS whose pitch is "auditable by construction," the meta-process is itself evidence the pitch is real. (Caveat: the bookkeeping must keep pace with the code — see X5-005.)

---

## Promise-vs-delivery table

| Claimed capability | Source | Actually delivered? | Note |
|---|---|---|---|
| Capability-based, no ambient authority, cap-gated privileged ops | README; security-model; P1/P4 | **Yes** | Move-only caps; every wrapper cap-gated; confirmed in C1-kernel-cap + D1 claims register. |
| Smallest-defensible TCB; drivers/fs/net in userspace | README; ADR-0001; P2/P3 | **Yes (by construction so far)** | Kernel = caps/IPC/sched/mem/IRQ only; one `unsafe` in kernel proper. Drivers/fs/net are *planned* (Phase E), correctly framed as such. |
| Audited `unsafe`, every block with SAFETY + audit entry | README; unsafe-policy; P5 | **Yes** | 27 audit entries; gate-reproduction + D5b confirm inventory alignment. README's *count* is a volatile snapshot (X5-010 class). |
| Memory-safe Rust, miri-clean | README | **Yes** | 260/260 miri, zero UB (advisory int-to-ptr warnings only, already audited). |
| Boots end-to-end on QEMU virt aarch64; 2-task IPC round-trip | README "Done" table | **Yes** | gate-reproduction smoke trace byte-identical through `tyrne: all tasks complete`. |
| MMU / PMM / AddressSpace / task-loader "Done" | README status table | **Yes** | Each behind a closed milestone + smoke line; coverage 93–99%. |
| "32 accepted ADRs" | README:41 | **No** | 29 Accepted / 1 Deferred / 1 Superseded / 31 files. **X5-002.** |
| QEMU virt = GICv3 + SMMUv3; BSP implements them | ADR-0004:31, ADR-0006:47, ADR-0012:24 | **No** | Code ships GIC **v2**; `Iommu` is an empty stub. **X5-001.** Arch docs corrected; ADRs frozen by append-only. |
| "DMA is capability-scoped where hardware permits" | security-model invariants | **Aspirational even on QEMU** | No `Iommu` impl exists yet; SMMUv3-in-CI is planned, not present. Should be stated as future. (sub-finding of X5-001.) |
| 259 host tests | README:80; current.md:7 | **Off by 1** | Actual 260 (gate-reproduction). Volatile hardcode. |
| Project is "in the architecture phase / most code not yet written" | CLAUDE.md:7; CONTRIBUTING.md:3 | **No (materially stale)** | Mid-Phase B; 37 `.rs` files; kernel boots. **X5-002.** |
| Tyrne scales constrained-device → mobile (heterogeneous HW) | README; ADR-0001/0004 | **Stated goal, not yet exercised** | Only QEMU virt today; Pi4/RISC-V/mobile are honestly tiered as future. Coherent *as a goal*, correctly labeled. |
| First product = smart-home device firmware | phase-f | **Planned, concrete, not built** | Honestly Phase F; concrete plan (Matter/MQTT, BCM2711). No misleading present-tense claim. |
| Field-update / patch path for deployed devices | (none) | **Absent from plan** | **X5-004** — gap, not a false claim. |
| `current.md` reflects current state | ADR-0013 resume-friendliness | **No (3 milestones stale)** | **X5-005.** |
| `memory-management.md` written / `task-loader.md` indexed | architecture/README.md | **Written but mislabeled / unlisted** | **X5-009.** |
| Append-only ADRs; record decisions; supersede via new ADR | README; P8 | **Yes, but unused where most needed** | The mechanism exists and is healthy; it just hasn't been applied to the GICv3 drift (X5-001). |

---

## Roadmap-vs-product-goal assessment (is the path to smart-home-first coherent? gaps?)

**Overall: the sequence is sound and the destination is concrete. Two structural issues (one Blocker, one product gap) and a few framing tensions.**

The dependency graph (A kernel-core → B userspace → C multi-core / D Pi4 → E drivers+services → **F smart-home** → G security maturation → H platforms → I mobile → J opt-in AI) is a defensible critical path to the stated product. Crucially, the smart-home goal is *reflected concretely* (X5-P04): Phase E lands the generic plumbing (driver template, log, supervisor, storage, filesystem, network), and Phase F specializes it for the domain with named protocols, buses, a real SoC, a real sensor, and a falsifiable 7-day-uptime bar. This is materially better than the typical "we'll target IoT eventually" hand-wave.

**Ordering is reasonable.** Building the kernel and real userspace before any driver is the correct microkernel discipline (you cannot write a userspace driver before userspace exists). Putting multi-core (C) and Pi4 (D) before drivers (E) is sensible — the Phase plan even notes C/D may overlap. Security maturation (G: measured boot, crypto, TLS, verification pilot) landing *after* the first deployment (F) is a defensible "make it real, then harden" choice and is explicitly acknowledged as possibly overlapping F if crypto is needed earlier.

**Gaps / risks against the product goal:**

1. **No field-update mechanism anywhere (X5-004).** The single biggest *product* gap. A firmware product with a 7-day-uptime device and a security-first posture needs a patch path; none is on the plan. Cheap to slot in now, painful to retrofit.

2. **ADR-number collision corrupts the C/D plan (X5-003 / D4-001/002).** The forward plan for the next two phases reuses live ADR numbers. Must fix before Phase C.

3. **Pi-4-first vs security differentiation tension (X5-007).** The first hardware target is the board where the flagship security properties (DMA scoping, blob-free wireless) are weakest. Honestly documented, but under-foregrounded; worth surfacing because it is the board the smart-home story rides on.

4. **Product-critical dependency risk un-probed until late (X5-008).** The viability of the Matter/MQTT/`smoltcp`/filesystem Rust ecosystem under `no_std + alloc` + no-blob + `cargo-vet` is the assumption the whole product rests on, and it isn't validated until Phases E/F. A cheap early feasibility note would de-risk years ahead.

5. **`smart-home` appears in the plan but the constraint never shapes early phases.** This is *correct* phasing (don't gold-plate), noted only so the maintainer is aware the product domain is entirely deferred to E/F and the early kernel is domain-neutral — which is fine, and arguably the right call for a kernel meant to also scale to general systems and mobile.

**What is NOT a gap (credit where due):** persistence (E5), secure/measured boot (G1), TEE (G1.5), crypto + signatures (G2), TLS (G3), formal-verification pilot (G4), threat-model-v2 (G5), and a network stack (E6) are all explicitly on the plan. The roadmap is unusually complete for the product's needs — update is the conspicuous omission, and it stands out *because* everything around it is covered.

---

## Cross-track notes

- **D4-roadmap-tasks:** This track's X5-003 is D4's Blocker D4-001/D4-002 (ADR-number collision) viewed strategically; the mechanical renumbering fix is D4's. X5-005 corresponds to D4-003/D4-004 (stale `current.md` + T-019 status); X5-006 = D4-005 (missing index rows). No disagreement; X5 adds the *why-it-matters-to-the-positioning* framing.
- **D1-architecture:** X5-001's `Iommu`-stub and GIC-version evidence draw on D1-003/D1-001/D1-004. X5 escalates the GIC issue from "doc drift" to "foundational-ADR-vs-reality, frozen by append-only" because the *ADRs* (not just docs) are wrong and the project's own conflict-resolution rule points readers at the wrong document. Recommend the ADR track (D2a) own the supersession-ADR fix; D1 owns the doc-status fixes.
- **D5a-meta-core:** X5-002 is the strategic consolidation of D5a-001/002/004 (CLAUDE.md/CONTRIBUTING.md/ADR-count). X5 frames these as credibility/agent-effectiveness risks, not just stale prose, because CLAUDE.md is the agents' entry point.
- **D2a/D2b (ADR track):** Please confirm whether a supersession ADR (per X5-001) is the agreed mechanism for correcting the GICv3/SMMUv3 statements in ADR-0004/0006/0012, given the append-only constraint. Also relevant: ADR-0012 hardcodes the GICv3 distributor address — the *address* (`0x0800_0000`) is correct, only the *version label* is wrong, so the correction is narrow.
- **gate-reproduction:** Relied upon as ground truth for all "Done"/delivery claims (260 tests, miri, coverage, smoke). The 259→260 drift feeds X5-002's volatile-count point.
- **D5c-existing-reviews / security:** The "Pending QEMU smoke verification" status on UNSAFE-0019/0020/0021 (IRQ-dispatch path) is correctly forward-flagged, not ignored — consistent with the honest out-of-scope discipline X5-P05 praises. No alignment concern there.
- **For the eventual master-review synthesis:** the through-line of X5 is that Tyrne's *substance* is strongly aligned with its goals, and the residual risk is almost entirely in *artifacts that describe the substance* (front-door counts, foundational ADRs, the forward plan, the resume pointer) drifting from the substance. For a project whose product *is* trustworthiness, those artifacts are not cosmetic — keeping them honest is the work.
