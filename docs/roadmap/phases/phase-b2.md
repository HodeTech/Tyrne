# Phase B.2 — Consolidation & Hardening

Phase B (B0–B6) closed 2026-06-01, and Phase C (multi-core) is the next planned body of feature work. Before Phase C's scheduler and address-space code grows a second, concurrent dimension, this short bridge phase pays down the debt surfaced by the 2026-07-15 full-repository review: CI gaps that let real defects (an inline-asm register-clobber UB bug, a release-profile security gate that has never once been exercised, a host/target confusion that breaks builds on aarch64 dev machines) go undetected; a documentation tree that in dozens of places still describes Phase B as unfinished, describes the current syscall boundary as "dormant," or has simply drifted out of sync with the task/review corpus it is supposed to index; and a long tail of correctness, robustness, code-quality, and unsafe-audit findings that are cheap to fix now and materially riskier to leave lying around once Phase C's concurrency work starts touching the same files. None of this is multi-core work. The point of Phase B.2 is narrow and mechanical: make CI actually enforce what the project's own standards claim it enforces, make the documentation tell the truth about the project's current state, and fix the concrete defects the review found — so that Phase C starts on a base whose gates are real and whose docs can be trusted.

**Exit bar:** CI enforces every gate the project's own standards docs claim it enforces; the documentation tree accurately reflects Phase B's 2026-06-01 closure and Phase C's start; and the feature-independent correctness, robustness, and quality defects surfaced by the 2026-07-15 full-repository review are fixed.

**Scope:** Near-term, feature-independent hardening — CI/merge-gate wiring, documentation-cascade correction, and the correctness/robustness/quality/unsafe-audit/performance findings from the review that do not require new kernel features or new syscall surface.

**Out of scope:**
- **Multi-core work of any kind** — secondary-core start, per-core state, preemptive scheduling, cross-core IPC, TLB shootdown. That is Phase C, and nothing in this phase implements it (some findings below merely note where a fix *gates* a Phase C milestone's acceptance criteria).
- **Real-hardware / aarch64 register-and-barrier hygiene** for a non-QEMU target. That is Phase D (Raspberry Pi 4).
- **Capability enforcement that requires new syscall wiring** (e.g. a new `MemoryRegionCap`-driven device-mapping syscall, driver-facing capabilities). That is Phase E (first real driver).
- **Test-HAL / HAL abstraction parity for new BSPs.** That is Phase H.

This phase's findings and remediation actions are drawn from the 2026-07-15 full-repository review — an internal review pass, not itself a document published anywhere in this tree. Every item below stands on its own file:line location in the shipped tree, so remediation does not depend on that source being available.

To avoid colliding with Phase B's B0–B6 milestone IDs, the work below is organized as **Track B.2-1** through **Track B.2-6** rather than numbered milestones.

---

## Track B.2-1 — CI enforcement & merge gates

The project's standards docs (`infrastructure.md`, `code-review.md`, `error-handling.md`) describe a CI posture that is, in several concrete and security-relevant ways, more thorough than what `.github/workflows/ci.yml` actually runs. This track closes that gap: every claimed gate either becomes a real, merge-blocking CI check, or the claim is corrected to match reality (the documentation half of that correction is tracked under Track B.2-2 where it doesn't require a CI change).

### Sub-breakdown

- **[🟠 HIGH]** The security-relevant release-profile contract (`console_write` debug-gate) is never built or tested by CI — `.cargo/config.toml:29-37` (kernel-build alias); `.github/workflows/ci.yml:96-101,140-143`
  **Action:** Add a CI step (or job) that runs `cargo build --release --target aarch64-unknown-none -p tyrne-bsp-qemu-virt` and `cargo test --release -p tyrne-kernel` (or workspace-wide `--release`) so the `not(debug_assertions)` code and its pinning tests are exercised on every PR. Mirror `kernel-build`/`kernel-run` with `kernel-build-release`/`kernel-run-release` aliases in `.cargo/config.toml`.

- **[🟠 HIGH]** Userland crates carrying the raw unsafe syscall-trap asm are never clippy-checked in CI, on any target — `Cargo.toml:23-27` (default-members); `.cargo/config.toml:32-34,44-45` (kernel-clippy/host-clippy aliases); `bsp-qemu-virt/Cargo.toml:15-17`; `tools/build-userland.sh:30-34`; `userland/tyrne-user/src/lib.rs:92-141`
  **Action:** Add `cargo clippy -p tyrne-user -p tyrne-userland-hello --target aarch64-unknown-none -- -D warnings` alongside `kernel-clippy` in the kernel-build job (after `build-userland.sh`, reusing the aarch64 toolchain already installed there); update `docs/guides/ci.md`'s job table.

- **[🟠 HIGH]** `tools/smoke.sh` — the only automated check of actual kernel boot/IPC/syscall-boundary behavior — is never invoked by CI — `.github/workflows/ci.yml` (entire jobs block, lines 65-277 — no job references `tools/smoke.sh`); `docs/guides/ci.md:55`; `docs/standards/infrastructure.md:82`
  **Action:** Add a `qemu-smoke` job: install `qemu-system-aarch64` (`apt-get install qemu-system-arm` on `ubuntu-latest`), run `tools/build-userland.sh && cargo kernel-build && tools/smoke.sh`, gate merge on its exit code. File a fresh, explicitly Phase-B.2-scoped task rather than relying on the stale T-009 cross-reference. This gates Milestone C1's own "QEMU run with `-smp 4` brings all four cores to a known checkpoint" acceptance criterion — the smoke harness needs to already be a real, exercised CI gate before Phase C tasks extend it to multi-core.

- **[🟠 HIGH]** The release debug-gate's regression test never executes in CI; a broken gate would go undetected — `kernel/src/syscall/abi.rs:377-383` (`console_write_is_absent_in_release_builds`); `kernel/src/syscall/abi.rs:87` (the `cfg!(debug_assertions)` guard it verifies); `.github/workflows/ci.yml:100-101,188-189,224`
  **Action:** Add a dedicated CI job/step running `cargo test --release --lib -p tyrne-kernel -- console_write_is_absent_in_release_builds` (narrow filter, keeps it fast). Add a comment next to `[profile.release]` in Cargo.toml (mirroring the existing overflow-checks comment) stating explicitly that `debug-assertions` must stay at its Cargo default (false) in release because `SyscallNumber::decode` gates `console_write` on it.

- **[🟠 HIGH]** QEMU smoke tests (the only test layer exercising BSP hardware-facing code) are not wired into CI, right as Phase C (concurrency) begins — `.github/workflows/ci.yml` (no smoke job); `tools/smoke.sh` (exists, unused by CI); `docs/roadmap/phases/phase-b.md:291` (flag K3-7)
  **Action:** Same remedy as the `smoke.sh`-in-CI finding above — this is the cross-cut instance of the identical gap, independently surfaced. Land the `qemu-smoke` job before any SMP-touching PR lands so the first concurrency regression is caught by CI, not by a human running `smoke.sh` manually.

- **[🟡 MEDIUM]** CI never builds, lints, or smoke-tests the `--release` profile — only `--debug` is ever exercised — `.github/workflows/ci.yml:135-143`
  **Action:** Add a release-profile build (ideally + kernel-clippy + smoke) step to the kernel-build job, or a matrix axis `profile: [debug, release]`, so fat-LTO-specific codegen issues surface in CI. At minimum, record the gap explicitly in `infrastructure.md`'s "Planned gates" section until it lands.

- **[🟡 MEDIUM]** `clippy::unwrap_used`/`expect_used`/`panic` are denied only in `tyrne-kernel`, not in `tyrne-hal` or `tyrne-bsp-qemu-virt` — the standard's own "Tooling" claim is false for two of the three in-scope crates — `hal/src/lib.rs:1-51` (no `#![deny(...)]`); `bsp-qemu-virt/src/main.rs:22-40` (no `#![deny(...)]`); contrast `kernel/src/lib.rs:62-66`; `docs/standards/error-handling.md:60`
  **Action:** Add `#![deny(clippy::panic)]`, `#![deny(clippy::unwrap_used)]`, `#![deny(clippy::expect_used)]` to `hal/src/lib.rs` and `bsp-qemu-virt/src/main.rs` (with scoped `#[allow(...)]` on legitimate one-shot init-path call sites, matching the pattern kernel's `#[cfg(test)]` blocks already use). Preferable to narrowing the standard's wording, given `bsp-qemu-virt/src/syscall.rs` and `exceptions.rs` are now live hostile-input surfaces post-Phase-B6.

- **[⚪ LOW]** The `perf-bench` feature (542 lines, alters `main.rs` control flow) is never compiled by CI — `bsp-qemu-virt/Cargo.toml:19-24`
  **Action:** Add `cargo build --target aarch64-unknown-none -p tyrne-bsp-qemu-virt --features perf-bench` (and a matching clippy pass) as a CI step in the `kernel-build` job, or at minimum add an entry to `infrastructure.md`'s "Planned gates" section.

- **[⚪ LOW]** `tools/perf-harness.sh` is likewise never invoked by CI — no automated perf-regression signal — `.github/workflows/ci.yml` (no job references it); `docs/standards/infrastructure.md:114`
  **Action:** Lower priority than the smoke-test gate; consider a scheduled (nightly/weekly) `workflow_dispatch`/cron job running `tools/perf-harness.sh --iterations=20 --report=ci-nightly` and archiving the report as a build artifact, once the smoke job lands.

- **[⚪ LOW]** No shellcheck (or any shell linter) runs in CI, despite the scripts already anticipating it — `.github/workflows/ci.yml` (no shellcheck step); `tools/smoke.sh:53,55`
  **Action:** Add a cheap `shellcheck tools/*.sh` step to the fast lane (or a dedicated job); `ubuntu-latest` ships shellcheck preinstalled.

- **[⚪ LOW]** QEMU wrapper tooling hardcodes `-smp 1` with no override, ahead of Phase C multi-core work — `tools/run-qemu.sh:92`; `tools/smoke.sh:73`
  **Action:** Add a `--smp N` (default 1) passthrough to `run-qemu.sh` and `smoke.sh` now, before Phase C tasks start depending on these scripts — this directly gates Milestone C1's `-smp 4` acceptance criterion; cheaper to do as an isolated tooling change now than to retrofit under Phase C time pressure.

- **[⚫ INFO]** "What gates merge" is documented only in comments, not verifiable as code — `.github/workflows/ci.yml:7-9`; `docs/guides/ci.md:85-91`
  **Action:** Low priority given repo size, but worth tracking: GitHub repository rulesets (`gh api repos/{owner}/{repo}/rulesets`) or Terraform (`github_branch_protection`/`github_repository_ruleset`) would make merge-gate configuration reviewable and diffable like any other infra change instead of trusted-by-comment.

### Acceptance criteria

- `cargo build --release` + `cargo test --release` for the kernel and BSP crates run on every PR, including the `console_write_is_absent_in_release_builds` regression.
- `tyrne-user` and `tyrne-userland-hello` are clippy-checked in CI on the `aarch64-unknown-none` target.
- A `qemu-smoke` job runs `tools/smoke.sh` on every PR and gates merge on its exit code.
- `hal` and `bsp-qemu-virt` carry the same `clippy::panic`/`unwrap_used`/`expect_used` denies `kernel` already has.
- `tools/run-qemu.sh` and `tools/smoke.sh` accept an `--smp N` override, unblocking Milestone C1's own smoke acceptance criterion.
- The remaining low/info items (perf-bench build, perf-harness.sh scheduling, shellcheck, "what gates merge" as code) are tracked even if not all land within B.2.

---

## Track B.2-2 — Documentation cascade (Phase-B closure)

Phase B closed 2026-06-01, but the closure was never cascaded through the full documentation tree: the entry-point architecture doc, several subsystem chapters, the task/review indices, nine task files' own frontmatter, CONTRIBUTING.md/SECURITY.md, several ADRs, and a long tail of standards docs and cross-references all still describe an earlier project state — in a few places (SECURITY.md's "not yet a userspace-bearing OS") the drift has become an outright false statement about the shipped security boundary. This track is the closure quartet's missed follow-through, run once as a batch.

### Sub-breakdown

**Entry-point & core architecture docs**

- **[🟠 HIGH]** overview.md — the designated entry-point document — describes the system as stuck at end-of-Phase-A, but Phase B is fully closed and Phase C is active — `docs/architecture/overview.md:5`
  **Action:** Rewrite the status banner to reflect Phase B closure and Phase C's start; thread ADR-0027..0039 into the relevant sections (Address spaces, Syscall surface, Boot flow). Add this doc to whatever checklist/skill governs phase closure so it is updated as part of every phase's closure quartet, not left behind.

- **[🟠 HIGH]** task-loader.md's central claims are now false: the loader is described as producing a non-runnable descriptor loading an unexecuted placeholder blob, but the code runs a real EL0 task end-to-end — `docs/architecture/task-loader.md:13-21,92-103`
  **Action:** Rewrite the "Scope boundary" and "Embedded image content" sections to describe the landed state: `load_image` → `task_create_from_image` (T-024) → `add_user_task` (T-023) → scheduled EL0 execution (T-028), with the real `hello` image and ADR-0039's build pipeline. Retire or clearly historically-mark the 8-byte placeholder code sample.

- **[🟡 MEDIUM]** hal.md, scheduler.md and exceptions.md describe the EL0 entry-context mechanism and the `+0x400` syscall path as "dormant"/only "runtime-verified in B6", but B6 has landed and the path is live, tested, and security-reviewed — `docs/architecture/hal.md:94`; `docs/architecture/scheduler.md:73,90`; `docs/architecture/exceptions.md:58,105,133`
  **Action:** Update all three documents to say the mechanism is live (not dormant), cite T-024/T-025/T-026/T-028 and ADR-0039, and change exceptions.md's "exercised at runtime in B6" to past tense with the T-028 QEMU-smoke evidence.

- **[🟡 MEDIUM]** security-model.md's capability-type table omits DebugConsole — the one capability kind that is actually implemented and gates the only currently-live, attacker-reachable privileged operation — while listing several kinds that do not exist in the code — `docs/architecture/security-model.md:132-143`
  **Action:** Split the table into "Implemented (v1)" (Task, Endpoint, Notification, AddressSpace, DebugConsole — with DebugConsole's CONSOLE_WRITE right) and "Planned" (MemoryRegionCap, IrqCap, TimerCap, etc.); cross-link ADR-0031.

- **[🟡 MEDIUM]** overview.md's "Syscall surface" enumeration does not match the Accepted, implemented syscall ABI and never cites ADR-0030 / ADR-0031 — `docs/architecture/overview.md:194-206`
  **Action:** Either update the list to the real v1 ABI and cite ADR-0030/ADR-0031, or explicitly relabel the section "Syscall surface (design-time speculation, superseded by ADR-0030/ADR-0031 — see exceptions.md)".

- **[🟡 MEDIUM]** docs/architecture/README.md's per-document Status column is not kept in sync with the linked documents' own content — `docs/architecture/README.md:11-23`
  **Action:** Update each Status cell to name the latest task/ADR that touched the document (e.g. task-loader.md → "T-019, T-024, T-028"); fold into the same phase-closure checklist that fixes the three findings above.

- **[🟡 MEDIUM]** memory-management.md's "Frame allocation discipline" section frames the high-half PA-to-VA helper as a future need, but it already landed and is in active use — `docs/architecture/memory-management.md:206`
  **Action:** State (past tense) that the high-half migration landed via T-022/ADR-0033 and that `phys_to_kernel_va`/`phys_frame_kernel_ptr` is the realised helper, cross-linking the UNSAFE-2026-0026/0027 Amendments the document already cites elsewhere.

- **[🟡 MEDIUM]** docs/architecture/boot.md is stale relative to the current main.rs boot flow (missing banner still shown as present; EL0 execution now real but documented as not-yet-executed) — `docs/architecture/boot.md:19,76-77` (vs. `bsp-qemu-virt/src/main.rs` — no `tyrne: image loaded` banner exists anywhere in the file; EL0 task setup at main.rs:1438-1628)
  **Action:** Update boot.md's stage-3 description and Mermaid sequence diagram: drop the removed banner line, correct the "does NOT execute" claim, and add the EL0-task bring-up steps (AS/Task cap resolution, USER_TASK_TABLE console-cap seeding, `add_user_task`, FAILCLOSED_TABLE publish) as their own documented stage.

- **[⚪ LOW]** boot.md's boot-time memory map is an untagged, ASCII-art diagram — violates two explicit documentation-style rules simultaneously — `docs/architecture/boot.md:89-101`
  **Action:** Convert to a Mermaid diagram (e.g. `block-beta` or a vertically-stacked `flowchart TB`), or at minimum tag the fence ```text``` and drop the box-drawing connectors in favour of a plain table.

- **[⚪ LOW]** ipc.md links an in-repo file with an absolute GitHub blob/main URL instead of a relative path — `docs/architecture/ipc.md:65`
  **Action:** Change to a relative path: `[cancel-recv]: ../../kernel/src/ipc/mod.rs`.

- **[⚫ INFO]** ipc.md's file-size claim ("~1425-line file") has drifted ~20% out of date — `docs/architecture/ipc.md:14`
  **Action:** Either drop the specific line count or update it; the underlying architectural claim is unaffected.

- **[⚪ LOW]** docs/architecture/README.md's "Status" prose directly contradicts its own Index table two paragraphs below — `docs/architecture/README.md:7`
  **Action:** Replace with reality-matching prose, e.g. "Most subsystem chapters are written and Accepted; `drivers.md` and `userspace.md` remain planned pending the corresponding Phase E/driver-model ADRs."

**Roadmap & task/review index synchronization**

- **[🟠 HIGH]** current.md's live-state bullets are stale relative to the repository's actual HEAD — the most recently completed work (T-029) is entirely unreflected — `docs/roadmap/current.md:76-81`
  **Action:** Mark PR #43 and the b6-closure branch merged/retired, set "Last completed task" to T-029 (PR #44/#45), add a fresh dated banner recording T-029's Phase 1 + Phase 2 completion. Recurrence of Blocker D4-003 from the 2026-05-22 master review.

- **[🟠 HIGH]** docs/analysis/tasks/phase-b/README.md task index is missing 8 of the phase's 23 tasks (T-022 through T-029) and shows wrong statuses for the two it does list — `docs/analysis/tasks/phase-b/README.md:22-23`
  **Action:** Add index rows for T-022–T-029 with correct milestones/statuses; correct the T-020/T-021 rows to "Done". Recurrence of Blocker D4-005 from the 2026-05-22 master review.

- **[🟡 MEDIUM]** The same task-index gap, restated with the milestone/status detail — all 8 missing tasks delivered the phase's closing milestone (B6) — `docs/analysis/tasks/phase-b/README.md:9-23`
  **Action:** Same fix as the finding above (near-duplicate finding from a separate review pass, both listed for completeness); additionally note each missing task's own frontmatter still reads "In Review" (see the frontmatter-status finding below) as a related-but-separate defect. Run an `ls`-vs-table reconciliation as a periodic check, or fold into a future `sync-adr-index`-style skill for task indices.

- **[🟠 HIGH]** Nine task files' frontmatter Status field is stuck at "In Review" (or an internally self-contradictory Status line) despite the roadmap declaring them Done/merged with commit hashes and dates — `docs/analysis/tasks/phase-b/T-020-syscall-error-taxonomy.md:5` (and identically T-021 through T-029)
  **Action:** Flip the Status field to Done (with a `date_done` entry, following the T-019 precedent) for every task current.md/phase-b.md already treats as merged and closed; add a merge-confirmation row to each task's Review history. Recurrence of Major D4-004 from the 2026-05-22 master review.

- **[🟡 MEDIUM]** Two of the six forward-flagged items from the 2026-06-01 Phase-B-closure security seam review — the ones most relevant to Phase C's own scope — are absent from every carry-forward tracking artifact — `docs/roadmap/phases/phase-c.md:126-132` (§Carry-forwards from Phase B); business/security 2026-06-01 phase-b-closure review artifacts (§Adjustments / source of the forward-flags)
  **Action:** Add explicit bullets for gate-#3 context-resolution atomicity and gate-#1 loader-trust to phase-c.md's §Carry-forwards, cross-referenced to Milestones C2/C3 (the milestones that make them live); add an SP_EL1 high-water-mark bullet distinct from the already-tracked IRQ/TTBR1 item.

- **[🟡 MEDIUM]** The business-, security-, and performance-optimization-review index READMEs are missing their most recent (2026-05-31/2026-06-01, Phase-B-closing) entries, including the T-028 EL0-boundary and consolidated Phase-B security reviews — `docs/analysis/reviews/business-reviews/README.md:38`; `docs/analysis/reviews/security-reviews/README.md:41`; `docs/analysis/reviews/performance-optimization-reviews/README.md:31`
  **Action:** Add the missing rows to all three index tables, following each table's existing format (Date | Scope | Verdict | File). Consider a lightweight CI check or a `conduct-review` skill acceptance criterion that greps the directory listing against the README table.

- **[🟡 MEDIUM]** Three of four review-family README indices were never updated for the Phase-B-closure batch — the project's most important reviews to date are undiscoverable via the documented index — `docs/analysis/reviews/security-reviews/README.md:41`; `docs/analysis/reviews/business-reviews/README.md:38`; `docs/analysis/reviews/performance-optimization-reviews/README.md:31`
  **Action:** Same fix as the finding above (near-duplicate finding, both listed for completeness); should become a checked acceptance-criterion of the closure-trio workflow.

- **[🟡 MEDIUM]** docs/guides/README.md is stale on both its status prose and its own guide inventory: it calls the project "the architecture phase", uses an orphaned pre-lettered-phase numbering scheme, and omits 2 of the 4 guide files that actually exist — including the guide for the project's flagship EL0-userspace milestone — `docs/guides/README.md:7,12-19`
  **Action:** Rewrite the Status paragraph to match README.md's framing. Add rows for `two-task-demo.md` and `first-userspace.md` with status "Accepted". Replace "Planned — Phase 2/3/4" with the lettered-phase scheme or drop the tag. Add a `first-userspace.md` link to README.md's "Documentation map" §"Reader who wants to do something concrete" list.

- **[⚪ LOW]** Phase-plan README's living-document note still claims Phase A is the active phase, contradicted by the project's own current-focus banner — `docs/roadmap/phases/README.md:51`
  **Action:** Update the parenthetical to name the actually-active phase, or better, drop the specific phase name from the illustrative aside entirely ("the currently active phase carries the most detail; later phases are sketches") so this sentence doesn't need editing every phase transition.

- **[⚪ LOW]** The most recent performance review (B6 closure) deviates from the master-plan's mandated six-section template and its own acceptance-criteria checklist silently drops the "Index in README.md updated" item — which was in fact not done — `docs/analysis/reviews/performance-optimization-reviews/2026-06-01-B6-closure.md:88-93`; master-plan.md (§Acceptance criteria)
  **Action:** Add a "Regression check" section (host-test pass, smoke pass, unsafe-diff already exist elsewhere and just need restating) plus the README index row, or add a one-line note explaining the abbreviated shape is an intentional exemption (mirroring how B2–B5 handled baseline-only cycles).

- **[⚪ LOW]** The top-level reviews index never mentions the master-review family, which produced the corpus's largest and most consequential single artifact — `docs/analysis/reviews/README.md:7-14` ("The four types" table)
  **Action:** Add a fifth row (or a short "Master reviews" subsection linking to master-review/README.md), noting the trigger ("on-demand, whole-tree sweep") that document already documents.

- **[⚪ LOW]** Coverage and Miri validation reports are frozen at 2026-04-23/27 (pre-T-016) despite roughly a dozen unsafe-touching tasks (T-016 through T-029) landing since — `docs/analysis/reports/2026-04-27-coverage-rerun.md`; `docs/analysis/reports/2026-04-23-miri-validation.md`
  **Action:** Already correctly triaged as Nit-severity in 2026-05-22 and remains low-urgency (administrative snapshot gap, not correctness — Miri/coverage are re-run and reported inline at every milestone closure). If the dedicated-report convention should stay alive, a single fresh report at the next natural checkpoint (Phase C open, or first Phase-C milestone close) closes it cheaply.

- **[⚪ LOW]** Dead cross-references to the pre-migration `.claude/skills/` path in at least 10 review-archive files — `docs/analysis/reviews/business-reviews/2026-05-09-B2-closure.md:26`; `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-g-process.md`
  **Action:** Either leave as an acknowledged historical-snapshot artifact with a one-line note added to `docs/analysis/reviews/README.md` warning that pre-2026-05-14 review links into `.claude/skills/` are stale, or do a mechanical `.claude/skills/` → `.agents/skills/` string replace across the archive (low-risk pure path rename).

- **[⚫ INFO]** T-029's frontmatter omits the required Milestone field — `docs/analysis/tasks/phase-b/T-029-perf-microbench.md:3-6`
  **Action:** Add a Milestone line (e.g. "B6 follow-on / Phase B closure tail — not gated on a numbered B-milestone").

- **[🟡 MEDIUM]** README's literal Quick-Start boot trace shows a console line the kernel no longer prints — `README.md:95` (vs. `bsp-qemu-virt/src/main.rs:1318-1335`)
  **Action:** Remove the `tyrne: image loaded (...)` line from README's Quick-Start trace, or add a real print of the loaded-image parameters at the `task_create_from_image`/`add_user_task` call site and keep the README line honest. Prefer eliding fragile trace segments with `...`, as `first-userspace.md` already does.

- **[🟡 MEDIUM]** docs/roadmap/current.md and T-029's own task file are stale relative to the actual (already-merged) git history — T-029 is complete but shown as active/Draft/In Review — `docs/roadmap/current.md:7,76,81` (vs. `docs/analysis/tasks/phase-b/T-029-perf-microbench.md:4`)
  **Action:** Flip T-029's Status line to Done (Phase 1 + Phase 2 both merged); add a closing roadmap banner recording T-029's completion, updating "Active task"/"Last completed task"/"Working branch" accordingly.

- **[⚪ LOW]** README's "small audited set" enumeration of kernel-crate unsafe omits the security-critical copy-from/to-user unsafe operation — `README.md:56` (vs. `docs/audits/unsafe-log.md:676` and `kernel/src/syscall/user_access.rs:243,311`)
  **Action:** Extend the sentence to name the copy-from/to-user unsafe explicitly (arguably the one most worth naming, given it is the syscall-boundary trust gate), or reword from an implicitly-exhaustive list to an explicitly illustrative one.

- **[⚪ LOW]** docs/roadmap/current.md line 77 self-contradicts line 74 on PR #43's merge status — `docs/roadmap/current.md:77` (vs. `:74`)
  **Action:** Update the "In review" bullet to "none" (or list whatever is actually in review post-T-029); fold PR #43 into the "Last completed milestone" framing already present at line 81.

**Standards docs**

- **[🟠 HIGH]** CONTRIBUTING.md and SECURITY.md describe a project state roughly two milestones and a whole phase behind reality; SECURITY.md's core factual claim is now false — `CONTRIBUTING.md:3,14`; `SECURITY.md:7`
  **Action:** Update both files' opening status paragraphs to match README.md's "Status at a glance"/CLAUDE.md's project-state paragraph: Phase B (B0–B6) closed 2026-06-01; Phase C active; first EL0 userspace task running through the syscall boundary. In SECURITY.md specifically, remove or correct "not yet a userspace-bearing OS" — that claim is now the opposite of true, and the syscall/capability boundary is exactly the surface SECURITY.md exists to describe accurately. Also update the trailing "refined as Phase B progresses" (SECURITY.md:7) since Phase B is closed.

- **[🟡 MEDIUM]** testing.md's mandated test-naming convention has 0% adoption in the actual codebase — `docs/standards/testing.md:63-77`
  **Action:** Either update testing.md to document the convention actually in use (`<subject>_<condition>_<expected_outcome>`, without a `test_` prefix, which real names already follow reasonably well), or do a mechanical rename sweep and add a clippy/CI check flagging new `#[test]` fns lacking the prefix.

- **[🟡 MEDIUM]** error-handling.md claims the kernel panic handler "dumps register state"; the actual handler only prints the `PanicInfo` message and location — `docs/standards/error-handling.md:73`
  **Action:** Either implement a register dump (x0-x30/SP/ELR_EL1/ESR_EL1/FAR_EL1 via inline asm, printed before the spin loop) and keep the standard as-is, or soften the claim to describe what exists today and track the register dump as a named follow-up.

- **[🟡 MEDIUM]** error-handling.md misstates where and how `panic = "abort"` is configured — `docs/standards/error-handling.md:143`
  **Action:** Correct to: "The bare-metal target sets `-C panic=abort` via `.cargo/config.toml`'s `[target.aarch64-unknown-none] rustflags` — not a `Cargo.toml` profile key — scoped to the kernel/BSP build only; host-side `cargo test` builds of kernel/hal/test-hal retain unwinding for the test harness."

- **[🟡 MEDIUM]** code-review.md's Tooling section says CI is "(planned)"; infrastructure.md and the actual workflow show CI has been live and merge-blocking since Phase 4 — `docs/standards/code-review.md:124-129`
  **Action:** Update to: "CI (live, Phase 4+) enforces format, clippy (host + kernel aliases), host tests, kernel build, and Miri; coverage is informational only and does not block merge — see infrastructure.md." Keep "Branch protection (planned)" as-is; that claim is still accurate.

- **[🟡 MEDIUM]** error-handling.md claims CI "flags" both `todo!()` and `unimplemented!()`, but only `todo!()` has an actual deny-level lint — `docs/standards/error-handling.md:139`
  **Action:** Either add `unimplemented = "deny"` to `[workspace.lints.clippy]` (mirroring `todo`), or narrow the sentence to "`todo!()` presence is denied by the `clippy::todo` workspace lint; `unimplemented!()` has no automated CI check today and relies on review."

- **[🟡 MEDIUM]** logging-and-observability.md presents a fully-designed, non-existent logging facade in present-tense prescriptive language, without a status marker — `docs/standards/logging-and-observability.md:50-60`
  **Action:** Add an explicit banner at the top: "Status: forward-looking. The `tyrne-log` crate and log-service architecture described here do not exist yet; the kernel currently emits diagnostics only via the raw Console/UART path. This document records the intended design."

- **[🟡 MEDIUM]** error-handling.md claims uniform kernel+HAL+userspace coverage, but the enforcing deny-lints exist only in `kernel/src/lib.rs` — `docs/standards/error-handling.md:3`; `docs/standards/code-style.md:129`
  **Action:** Either add the same `#![deny(...)]` block to `hal/src/lib.rs` (see Track B.2-1's clippy-denies finding), or narrow the standards language to "deny-enforced in the kernel crate; HAL and BSP crates rely on `clippy::pedantic` (warn) plus review."

- **[⚪ LOW]** commit-style.md's allowed-scope list is stale against actual, current commit history (including the 5 most recent commits) — `docs/standards/commit-style.md:53-56`
  **Action:** Refresh the scope list from `git log --format=%s | grep -oE '\(([a-z0-9/_.+, -]+)\)'` (at minimum add `perf`, `roadmap`, `analysis`, `audits`, `architecture`, `mmu`); consider explicit sub-lists for process/doc scopes vs. code scopes.

- **[⚪ LOW]** code-style.md's "canonical" lint list omits three active workspace lints, most notably `clippy::todo` — `docs/standards/code-style.md:118-130`
  **Action:** Add the three missing lints, keeping the `todo` entry's rationale (P12 tie-in) visible.

- **[⚪ LOW]** bsp-boot-checklist.md's QEMU exception-log path is stale — actual script produces a PID-suffixed filename, not the fixed path the doc quotes — `docs/standards/bsp-boot-checklist.md:218-224`
  **Action:** Replace with the accurate description: "the logfile path is printed at startup as `${TMPDIR:-/tmp}/qemu_int.<pid>.log`; grep the printed path, not a fixed name."

- **[⚪ LOW]** documentation-style.md's own "never use an untagged fence" rule is violated three times within docs/standards itself — `docs/standards/commit-style.md:15,25`; `docs/standards/testing.md:67`
  **Action:** Tag the three fences `text` (they are illustrative templates/patterns, not executable code).

- **[⚪ LOW]** testing.md's "(to be added with the workspace)" for the test-hal crate is stale — the crate already exists — `docs/standards/testing.md:82`
  **Action:** Drop the parenthetical.

- **[⚫ INFO]** release.md still carries the "an Tyrne-specific" grammar error flagged by the prior review two months ago — `docs/standards/release.md:16`
  **Action:** Change "an Tyrne-specific" to "a Tyrne-specific".

**ADR corrections & cross-links**

- **[🟡 MEDIUM]** Unsubstantiated, technically dubious "safety-relevant" rationale baked into an Accepted ADR and duplicated into source rustdoc — `docs/decisions/0008-cpu-trait.md:158` (§Revision notes, 2026-05-22 entry); duplicated at `hal/src/cpu.rs:99-104`
  **Action:** Either attach concrete evidence (a rustc/LLVM issue link, a Miri trace, or a disassembly) as an append-only addition to the 0008 revision note and the rustdoc, or add a follow-up append-only note retracting the unverified aliasing claim and keeping only the defensible "avoid vtable indirection on the hot critical-section path" rationale.

- **[🟡 MEDIUM]** ADR-0033 has no top-of-file pointer to its own load-bearing post-Accept correction (stale KBASE / two-offset model stays the first thing a reader sees) — `docs/decisions/0033-kernel-high-half-migration.md:28,67,105-112,128` vs. `:186-192` (Revision notes)
  **Action:** Add a top-of-file blockquote in the same style already used at `docs/decisions/0022-idle-task-and-typed-scheduler-deadlock.md:7-11`, recording that the shipped `KBASE` is `0xFFFF_FFFF_4008_0000` (not `0xFFFF_FFFF_8008_0000`) and a single offset (`KERNEL_HIGH_HALF_OFFSET`) replaces the two-offset model described below.

- **[🟡 MEDIUM]** Phase C's 2026-06-01 ADR-number renumbering was not cascaded downstream, recreating a direct collision with Phase D's ADR ledger on ADR-0042/0043/0044 — `docs/roadmap/phases/phase-c.md:118-122` vs. `docs/roadmap/phases/phase-d.md:162-167`
  **Action:** Re-run the cascading renumbering: shift Phase D (and E–I if they also now collide) up past Phase C's new ceiling (ADR-0044); add a "downstream-renumbering note" to phase-d.md analogous to the one already present in phase-e.md. Recurrence of Blocker D4-001/D4-002 from the 2026-05-22 master review.

- **[🟡 MEDIUM]** phase-b.md's own B6 dependency-ordered task sequence self-contradicts "DONE"/"landed" against "In Review" for the same task in the same sentence, with no historical-record framing to disambiguate — `docs/roadmap/phases/phase-b.md:250,254,255`
  **Action:** Flip the three parenthetical task-status tags (steps 1, 5, 6) to "Done" with their merge PR numbers (T-022 → PR #36, T-027 → PR #41, T-028 → PR #42, matching current.md's own citations), or explicitly wrap the pre-closure narrative in a "preserved as historical record" framing the way the B5 section above it already does.

- **[⚪ LOW]** ADR-0011 still asserts "QEMU virt is GICv3" — the exact claim ADR-0036 was written to correct — with no reader-facing redirect — `docs/decisions/0011-irq-controller-trait.md:11`
  **Action:** Add the same one-line append-only top-of-file redirect banner already used on ADR-0004/0006/0012: "Correction: QEMU `virt` is GICv2 in v1, not GICv3; see ADR-0036. The trait surface described here is version-agnostic and unaffected."

- **[⚪ LOW]** ADR-0012's "EL drop" open question was never marked resolved, despite ADR-0024 settling it a month before the file was next edited — `docs/decisions/0012-boot-flow-qemu-virt.md:148` (§Open questions)
  **Action:** Append a strikethrough + resolution note mirroring the existing "Boot-time MMU activation" treatment: "*Resolved 2026-04-27 by ADR-0024 (EL drop to EL1 policy).*"

- **[⚪ LOW]** security-model.md's cross-table-CDT open question does not cross-link ADR-0023, which already contains the option catalogue for resolving it — `docs/architecture/security-model.md:330` vs. `docs/decisions/0023-cross-table-capability-revocation-policy.md`
  **Action:** Add "(see ADR-0023 for the deferred decision and its candidate options)", mirroring the IOMMU/SMMU bullet at line 328.

- **[⚫ INFO]** ADR-0018 is the only ADR in 0001-0020 that omits any pros/cons comparison of its considered options — `docs/decisions/0018-badge-scheme-and-reply-recv-deferral.md` (§Considered options, lines 33-49)
  **Action:** Append (purely additive) a "## Pros and cons of the options" section restating the six options' tradeoffs, for structural uniformity with the rest of the corpus.

**Misc doc hygiene**

- **[⚪ LOW]** Two Phase-A task files have relative links to source files that are one directory level short and therefore resolve to a nonexistent path — `docs/analysis/tasks/phase-a/T-004-cooperative-scheduler.md:25`
  **Action:** Add one more `../` to both links (`../../../../hal/src/context_switch.rs` and `../../../../kernel/src/cap/table.rs`). Consider adding a markdown-link-checker to CI given the density of relative cross-links and that at least 3 broken links have survived multiple prior review passes undetected.

- **[⚪ LOW]** T-011's coverage-baseline link is broken while an identical, correctly-formed link to the same document sits 75 lines later in the same file — `docs/analysis/tasks/phase-b/T-011-missing-tests-bundle.md:25`
  **Action:** Fix line 25 to match line 100's correct relative path.

- **[⚪ LOW]** Glossary is missing entries for PMM and AddressSpace — two heavily-used, Tyrne-specific kernel-object/subsystem terms that sit at the same conceptual tier as already-defined siblings (MMU, Endpoint, Notification) — `docs/glossary.md` (insertion points: before line 9 for AddressSpace, before line 75 for PMM)
  **Action:** Add a PMM (Physical Memory Manager) entry citing ADR-0035, and an AddressSpace entry citing ADR-0028, following the `update-glossary` skill's format and cross-linking conventions.

- **[⚪ LOW]** Glossary violates its own stated alphabetical-order invariant in two places — `docs/glossary.md:57-67,81-83`
  **Action:** Reorder the M-section to MADR, MAIR, MapperFlush, Microkernel, Miri, MMU; swap Reply capability/Rendezvous IPC to Rendezvous IPC, Reply capability. Both are pure cut-and-paste moves with no content changes.

- **[⚪ LOW]** add-bsp skill's "verify the smoke test" example trace is stale — it shows a round-robin loop format the kernel no longer produces, which would mislead a BSP porter about what success looks like — `.agents/skills/add-bsp/SKILL.md:159-166`
  **Action:** Replace the example trace with the current minimal-success shape plus a note ("exact trailing lines depend on kernel version — see README.md Quick Start for the current reference trace") so this doesn't re-drift on the next kernel demo change.

- **[⚫ INFO]** NOTICE and LICENSE's Apache-2.0 appendix name different copyright holders for the same codebase — `NOTICE:2`, `LICENSE:189`
  **Action:** Align the two, or make the relationship explicit (e.g. "Copyright 2026 HodeTech (Cemil İlik) and Tyrne contributors" in both places).

### Acceptance criteria

- overview.md, task-loader.md, hal.md, scheduler.md, exceptions.md, security-model.md, memory-management.md, boot.md, and docs/architecture/README.md all reflect Phase B closed / Phase C active, with correct ADR cross-links.
- current.md's live-state bullets match HEAD; the phase-b task index lists all 23 tasks with correct statuses; all nine "In Review" task frontmatters flip to Done with `date_done` entries.
- CONTRIBUTING.md, SECURITY.md, and the affected standards docs (testing.md, error-handling.md, code-review.md, logging-and-observability.md, commit-style.md, code-style.md) match current CI/tooling reality.
- All four review-family README indices include every Phase-B-closing entry.
- The Phase C ADR ledger renumbering is cascaded to Phase D (and E–I if colliding).
- Every broken/stale relative link identified above is fixed.

---

## Track B.2-3 — Immediate correctness & robustness fixes

These are live defects in shipped code — not documentation drift, not stylistic preference. Two are memory-safety-adjacent (an inline-asm register clobber that is Rust `asm!` UB, and a host/target confusion that silently miscompiles on aarch64 dev machines); the rest are correctness gaps in the syscall boundary, the PMM, and the test-HAL fakes the kernel's own test suite trusts.

### Sub-breakdown

- **[🟠 HIGH]** MapperFlush's documented "single address space" assumption is already stale relative to Phase B's shipped multi-AS infrastructure — `hal/src/mmu/mod.rs:376-386`
  **Action:** Land the AS/ASID discriminant on `MapperFlush` (e.g. a `PhantomData` AS-id or a stored ASID, with `flush` rejecting a mismatch) as a prerequisite for, or in the same change as, the first real per-task `cap_map` call — not deferred to "the multi-AS step" as an indefinite future milestone, since that infrastructure is already merged. Relevant to Milestone C5 (multi-core TLB shootdown), which needs a per-AS/ASID-aware flush discipline before it can safely broadcast invalidations.

- **[🟠 HIGH]** `userland/hello/build.rs` picks the userland linker script by `target_arch == "aarch64"`, which is true on aarch64 HOST targets too, not just the bare-metal target — `userland/hello/build.rs:16-20`
  **Action:** Discriminate on `CARGO_CFG_TARGET_OS == "none"` (the property that actually distinguishes the bare-metal target from every hosted aarch64 triple), matching the pattern already used in `bsp-qemu-virt/src/main.rs:144`. Apply the identical fix to `userland/hello/src/main.rs:23`'s `cfg_attr`. Add a one-line comment at each site cross-referencing the other, since this class of mistake has now occurred twice in the same crate pair (see the two related findings below).

- **[🟠 HIGH]** console_write's exposure is worse than a bounded loop: each byte write can spin indefinitely inside a masked-interrupt, non-preemptible context if the UART backpressures — `kernel/src/syscall/dispatch.rs:295` (`ctx.console.write_bytes(&buf[..chunk]);`)
  **Action:** Either bound `Pl011Uart::write_bytes`'s per-byte spin with an iteration cap or a Timer-based deadline and surface a typed failure the dispatcher can translate into a syscall error instead of hanging forever, or — if flow control is never enabled on the target hardware and this is judged structurally unreachable — add an explicit doc comment (or audit-log-style justification) recording that assumption so a future BSP port (Pi 4) doesn't silently inherit an unbounded-spin console path under masked interrupts. This directly gates Milestone C3 item 6 (the `Cpu::without_interrupts` interrupt-masked critical-section primitive): an unbounded spin under masked interrupts is exactly the deadlock shape C3's discipline exists to prevent once real IRQs can interrupt kernel code.

- **[🟡 MEDIUM]** console_write's chunk loop has no length cap and runs entirely with interrupts masked — `kernel/src/syscall/dispatch.rs:252-300`
  **Action:** Add an explicit maximum (e.g. `const MAX_CONSOLE_WRITE_LEN: usize = 4096;`) checked before Gate 1/2/3, returning `SyscallError::BadArgument` when `len` exceeds it, with a test pinning the boundary. Resolve together with the busy-spin finding above, since capping `len` alone does not fix the per-byte unbounded-spin risk.

- **[🟡 MEDIUM]** No `MappingFlags::DEVICE` exclusion — `copy_from_user`/`copy_to_user` would silently memcpy MMIO registers once userspace drivers exist — `kernel/src/syscall/user_access.rs:152-160` (`probe_user_pages`), `:213-218` (copy_from_user pass 2), `:296-301` (copy_to_user pass 2)
  **Action:** Add an explicit `!flags.contains(MappingFlags::DEVICE)` guard (or a documented, deliberate decision to allow it with a volatile/typed-MMIO API instead) to `probe_user_pages`, and record the decision either inline or as a forward-referenced open question in ADR-0038 or the Phase E (first real driver) task list, so the gap is a designed decision rather than an oversight discovered when the first driver syscall lands.

- **[🟡 MEDIUM]** Bootstrap address-space handle is a compile-time assumption, never reconciled against the real allocation — `kernel/src/obj/arena.rs:57-73` (`SlotId::first_slot`), corroborated by `kernel/src/mm/address_space.rs:59-60` and `bsp-qemu-virt/src/main.rs:1176-1186/1424-1434`
  **Action:** Add `debug_assert_eq!(bootstrap_as_handle, tyrne_kernel::mm::BOOTSTRAP_ADDRESS_SPACE_HANDLE, "bootstrap AS allocation invariant violated: first_slot() assumption broken")` immediately after the real allocation in main.rs, converting the prose discipline into a loud, testable invariant. Better still, thread the real `bootstrap_as_handle` through to every `Task::new(...)` call site instead of the assumed constant. Relevant to Milestone C2's per-core current-task-pointer work, which will multiply the number of places this assumption is relied on.

- **[⚪ LOW]** `PmmError::MisalignedAddress` doc-comment claims `free_frame` returns it defensively, but `free_frame` never constructs this variant — `kernel/src/mm/pmm.rs:46-51` (doc) vs. `:504-543` (free_frame body)
  **Action:** Add the defensive check the doc already promises — `if !pa.0.is_multiple_of(PAGE_SIZE) { return Err(PmmError::MisalignedAddress); }` at the top of free_frame — matching the project's fail-fast/defense-in-depth preference and the reserved-range inversion check's own rationale a few lines above.

- **[⚪ LOW]** `Pmm::new`'s pairwise reserved-range overlap check produces a false-positive `OverlappingReservedRanges` rejection for a zero-length reserved range nested inside another range — `kernel/src/mm/pmm.rs:247-253`
  **Action:** Skip the overlap check for any range with `frame_count() == 0` inside the pairwise loop, since such a range can never affect bitmap-vs-counter parity regardless of its position.

- **[⚪ LOW]** `Pmm::new` validates reserved-range inversion explicitly but has no equivalent explicit check for the top-level extent's own inversion — `kernel/src/mm/pmm.rs:199-214` (extent validation) vs. `:234-236` (reserved-range inversion check)
  **Action:** Add a symmetric `if extent.end.0 < extent.start.0 { return Err(PmmError::OutOfRange); }` immediately after the alignment check, matching the treatment already given to every reserved range.

- **[⚪ LOW]** `probe_user_pages` does not special-case `len == 0`, so a future direct caller with an unaligned pointer gets a spurious fault instead of the documented trivial-accept — `kernel/src/syscall/user_access.rs:140-170`
  **Action:** Add `if len == 0 { return Ok(()); }` at the top of `probe_user_pages` itself, matching `UserAccessWindow::validate`'s own handling.

- **[⚪ LOW]** The "ends in the top page must not spuriously fault" regression is pinned only for `copy_from_user`, not the structurally-duplicated `copy_to_user` — `kernel/src/syscall/user_access.rs:600-615` (existing test) vs. `:286-317` (copy_to_user pass 2, untested at this edge)
  **Action:** Add a symmetric `copy_to_user_range_ending_in_top_page_does_not_spuriously_fault` test (or extract the shared per-page cursor arithmetic per Track B.2-4's dedup item, making a single test suffice for both directions).

- **[🟠 HIGH]** `BlockMappedMmu::map` returns `MmuError::BlockMapped` instead of the contractually-required `AlreadyMapped` — `test-hal/src/mmu.rs:533-547` (also self-tested wrong at `test-hal/src/mmu.rs:1108-1117`)
  **Action:** Change `BlockMappedMmu::map` to return `Err(MmuError::AlreadyMapped)` for a blocked `va` (leave `unmap`/`translate` returning `BlockMapped`, which are correct today). Update the in-file test `block_mapped_mmu_injects_block_mapped_on_map_and_unmap` to assert `AlreadyMapped` from `map()`. Update the two dependent kernel tests (`kernel/src/mm/address_space.rs:1384-1439`, `kernel/src/obj/task_loader.rs:2504-2539`) and the `LoadError::MapFailed` doc-comment at `task_loader.rs:394-401` to match.

- **[🟠 HIGH]** console_write's inline asm declares `x2` as `in`-only, but the kernel unconditionally overwrites `x2` on every syscall return — unmarked register clobber (Rust `asm!` UB) — `userland/tyrne-user/src/lib.rs:102-115` (esp. line 108); cross-referenced with `bsp-qemu-virt/src/syscall.rs:224` and `bsp-qemu-virt/src/vectors.s:237`
  **Action:** Change the operand to `inout("x2") buf.len() as u64 => _,` (discarding the output, matching the style already used for x3-x7's `lateout(...) _`). Update the SAFETY comment (line 99) to read "x2..x7 are marked clobbered" and correct the UNSAFE-2026-0033 audit-log entry (`docs/audits/unsafe-log.md:756,761`) to match.

- **[🟠 HIGH]** `hello/build.rs`'s target check (`CARGO_CFG_TARGET_ARCH == "aarch64"`) cannot distinguish the real bare-metal target from a host build on an aarch64 host, breaking `cargo check --workspace` / miri / llvm-cov on Apple Silicon or ARM64 Linux dev machines — `userland/hello/build.rs:16-20`
  **Action:** Gate on the OS component too (or the full triple), not just the arch: `if std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("none") { ... }`, or compare the full `TARGET` env var to the literal `"aarch64-unknown-none"`. (Same underlying bug as the finding above; independently surfaced by a second review pass and listed separately per the source review's own routing.)

- **[🟠 HIGH]** The arch-only cfg gate is not confined to `build.rs` — the identical flaw recurs in `main.rs`'s crate attribute and throughout `lib.rs`'s cfg gates, giving the bug a much larger blast radius than the linker-script symptom alone — `userland/hello/src/main.rs:23`; `userland/tyrne-user/src/lib.rs:28,35,44,83,134`
  **Action:** Fix all three files' target-selection gates uniformly: replace every `target_arch = "aarch64"` guard with a check that also pins the OS/environment — e.g. `#[cfg(all(target_arch = "aarch64", target_os = "none"))]` — or better, centralize the condition as a single `cfg` alias (`#[cfg(tyrne_bare_metal)]` set via `.cargo/config.toml`'s `[target.aarch64-unknown-none] rustflags = ["--cfg", "tyrne_bare_metal"]`) so the three call sites cannot drift independently in the future. Track B.2-1 tracks adding the arm64-host CI signal that would catch a regression here.

- **[⚪ LOW]** `smoke.sh`'s `--timeout` flag crashes with an unbound-variable error instead of a usage message if no value is given — `tools/smoke.sh:29`
  **Action:** Either check `[[ $# -ge 2 ]]` before consuming `$2` and emit a clear "--timeout requires a value" error, or switch to the `--timeout=SECONDS` style already used by `perf-harness.sh` for consistency.

### Acceptance criteria

- `MapperFlush` carries an AS/ASID discriminant and rejects a mismatched flush.
- `userland/hello/build.rs`, `main.rs`, and `tyrne-user/src/lib.rs`'s target gates all discriminate on `target_os == "none"` (or a shared `cfg` alias).
- `console_write`'s per-byte spin is bounded and its chunk length is capped; both are regression-tested.
- `BlockMappedMmu::map` returns `AlreadyMapped`; dependent kernel tests and the `LoadError::MapFailed` doc-comment are updated to match.
- The userland `console_write` syscall shim marks `x2` as clobbered, matching the kernel's actual register usage; the UNSAFE-2026-0033 audit entry is corrected.
- `Pmm::new` rejects an inverted top-level extent and no longer false-positives on a zero-length nested reserved range; `free_frame` defensively checks alignment.
- `smoke.sh --timeout` fails with a clear usage message, not an unbound-variable crash.

---

## Track B.2-4 — Code quality & API design polish

None of these are live bugs; all are cheap-now, expensive-later hygiene: newtype discipline that would turn a class of unit-confusion mistakes into compile errors, duplicated security-critical logic (the capability-resolution pattern, the `Arena` free-list machinery) that risks a fix landing in one copy and not its twin, and a handful of test-coverage gaps on already-designed error paths.

### Sub-breakdown

**Newtype discipline**

- **[🟡 MEDIUM]** PA↔VA direct-map conversion functions use raw `usize`, not the `PhysAddr`/`VirtAddr` newtypes they exist to keep distinct — `hal/src/mmu/mod.rs:104` and `hal/src/mmu/mod.rs:142`
  **Action:** Change the signatures to `phys_to_kernel_va(pa: PhysAddr) -> VirtAddr` and `kernel_va_to_phys(va: VirtAddr) -> PhysAddr` (or keep a `pub(crate)` raw-usize escape hatch for asm/linker-symbol interop and add the typed wrappers as the public surface).

- **[🟡 MEDIUM]** `PhysAddr`/`VirtAddr` are naked pub-usize newtypes with zero arithmetic/alignment methods — `hal/src/mmu/mod.rs:164` (`VirtAddr(pub usize)`) and `hal/src/mmu/mod.rs:168` (`PhysAddr(pub usize)`)
  **Action:** Add `checked_add`/`wrapping_add(usize) -> Self`, `align_up(align: usize) -> Self`, `is_aligned_to(align: usize) -> bool` directly on both types, mirroring the pattern already used for `PhysFrame::from_aligned`.

- **[🟡 MEDIUM]** `tyrne-user`'s syscall wrappers pass capability handles as bare `u64` with no local newtype — `userland/tyrne-user/src/lib.rs:57` (`HELLO_CONSOLE_CAP: u64`) and `userland/tyrne-user/src/lib.rs:89` (`console_write(cap: u64, buf: &[u8])`)
  **Action:** Add a small local newtype in `tyrne-user` (e.g. `pub struct CapWord(pub u64);`), independent of the kernel crate per the module's own "restate the ABI, don't share the type" philosophy, and change `console_write`'s `cap` parameter and `HELLO_CONSOLE_CAP`'s type to it.

- **[⚪ LOW]** `UserAccessWindow` and `copy_from_user`/`copy_to_user` take raw `usize` pointers instead of `VirtAddr` — `kernel/src/syscall/user_access.rs:77` (`UserAccessWindow::new(base: usize, len: usize)`) and `kernel/src/syscall/user_access.rs:186-192`
  **Action:** Change `UserAccessWindow::new`'s `base` and the `user_ptr` parameters of `copy_from_user`/`copy_to_user`/`probe_user_pages` to `VirtAddr`, keeping `len` as `usize`.

- **[⚪ LOW]** `ContextSwitch::init_user_context` mixes raw `usize` addresses with a raw pointer for conceptually similar arguments — `hal/src/context_switch.rs:122-128`
  **Action:** Use `VirtAddr` consistently for all three, or add a lightweight marker type distinguishing entry-VA from stack-VA so a transposed pair fails to compile.

- **[⚫ INFO]** `Pmm::could_yield_pa_overlapping` drops the `PhysAddr` newtype at its own API boundary — `kernel/src/mm/pmm.rs:620` (`could_yield_pa_overlapping(&self, pa_range: core::ops::Range<usize>) -> bool`)
  **Action:** Change the parameter to `core::ops::Range<PhysAddr>`; trivial, drop-in change at the one call site.

**Dead-code / duplication removal**

- **[🟡 MEDIUM]** `CapabilityTable` hand-reimplements the generic `Arena`'s slot/free-list/generation machinery instead of using it — `kernel/src/cap/table.rs:86-156,563-654` vs. `kernel/src/obj/arena.rs:16-215`
  **Action:** Rebase `CapabilityTable`'s storage on `Arena<SlotEntry, CAP_TABLE_CAPACITY>` (as `AddressSpaceArena` already does), converting Arena's `Option`-based errors to the appropriate `CapError` at the boundary. Collapses two independently-audited copies of the single most security-critical free-list/generation-counter pattern in the kernel into one.

- **[🟡 MEDIUM]** The "resolve capability → check kind → check rights" pattern is hand-rolled five separate times across four modules — `kernel/src/ipc/mod.rs:589-602,604-616`; `kernel/src/mm/address_space.rs:430-441`; `kernel/src/syscall/dispatch.rs:321-333`; `kernel/src/sched/mod.rs:555-570`
  **Action:** Factor a single crate-internal primitive on `CapabilityTable`, e.g. `fn resolve_typed<T>(&self, handle: CapHandle, extract: impl FnOnce(CapObject) -> Option<T>, required: CapRights) -> Result<T, CapError>`, performing lookup → extract-or-WrongKind → rights-check-or-InsufficientRights once. Pins the ADR-0030 ordering in exactly one place instead of five.

- **[🟡 MEDIUM]** `copy_from_user`/`copy_to_user` duplicate the entire per-page validated-copy loop — `kernel/src/syscall/user_access.rs:204-248` (copy_from_user pass 2) vs. `:287-315` (copy_to_user pass 2)
  **Action:** Extract the shared per-page loop into a private generic helper, e.g. `fn walk_user_pages<M: Mmu>(mmu, task_as, user_ptr, len, require_write, per_page: impl FnMut(...)) -> Result<(), SyscallError>` that does the translate+flags+arithmetic once; `copy_from_user`/`copy_to_user` supply only a three-line direction-specific closure around `core::ptr::copy`. Keeps both `unsafe` sites' SAFETY comments distinct.

- **[⚪ LOW]** Endpoint/Notification/Task kernel-object modules duplicate the identical handle-wrapper + create/destroy/get boilerplate three times — `kernel/src/obj/endpoint.rs:37-120`; `kernel/src/obj/notification.rs:48-109`; `kernel/src/obj/task.rs:64-128`
  **Action:** Introduce a `macro_rules! typed_object_arena!` (or a generic `TypedHandle<Kind>` + generic free functions) in `obj/arena.rs`, and have the three modules invoke it. Pure mechanical de-duplication, reduces the audited-code surface by roughly two-thirds for this pattern.

- **[⚪ LOW]** `MappingFlags` and `CapRights` are structurally identical hand-rolled bitflag types duplicated across two crates — `hal/src/mmu/mod.rs:220-315` vs. `kernel/src/cap/rights.rs:18-129`
  **Action:** Add a small internal `macro_rules! bitset_type!` (living in `hal` or a tiny near-zero `tyrne-bits` internal crate) that both `MappingFlags` and `CapRights` invoke, with a flag to omit `BitAndAssign`/`SubAssign` for the deliberately-narrowing `CapRights` type.

- **[⚪ LOW]** `block_descriptor`/`page_descriptor` encoders duplicate their bit-composition body — `hal/src/mmu/vmsav8.rs:451-463` (block_descriptor) vs. `:479-490` (page_descriptor)
  **Action:** A private `fn leaf_descriptor(pa: u64, bits: DescriptorBits, is_page: bool, oa_mask: u64) -> u64` removes the duplication with no loss of clarity and guarantees the two encoders can't silently diverge on a shared field.

- **[⚪ LOW]** `QemuVirtGic::enable`/`disable` duplicate register-offset and bit-mask computation — `bsp-qemu-virt/src/gic.rs:316-340` (enable) vs. `:342-362` (disable)
  **Action:** Factor a private `fn set_bit_register(&self, base: usize, irq: IrqNumber)` taking the register base as a parameter; `enable`/`disable` become one-line callers passing `GICD_ISENABLER_BASE`/`GICD_ICENABLER_BASE`.

- **[🟡 MEDIUM]** `KERNEL_IMAGE_PHYS_BASE` (linker.ld) and `KERNEL_IMAGE_START` (main.rs) are independently hardcoded with no compile-time cross-check, unlike the sibling `KERNEL_HH_OFFSET` constant — `bsp-qemu-virt/linker.ld:41` and `bsp-qemu-virt/src/main.rs:102`
  **Action:** Add a compile-time cross-check analogous to `KERNEL_HH_OFFSET`'s — `PROVIDE(__kernel_image_phys_base = KERNEL_IMAGE_PHYS_BASE);` in the linker script, exposed as an `extern "C"` symbol, asserted equal to `KERNEL_IMAGE_START` at `kernel_entry` (a runtime assert, since linker-script constants can't be const-asserted against Rust directly). Alternatively, follow ADR-0039's `--defsym` upgrade path when the BSP layout is next touched (e.g. the Pi 4 port).

- **[⚪ LOW]** `bsp-qemu-virt/linker.ld`'s `/DISCARD/` list is less rigorous than `hello.ld`'s — no `.got`/`.got.plt` handling or ASSERT, despite the file's own header claiming the design depends entirely on PC-relative addressing — `bsp-qemu-virt/linker.ld:115-120`
  **Action:** Mirror `hello.ld`'s pattern: add a `.got : { *(.got .got.plt) }` output section plus `ASSERT(SIZEOF(.got) == 0, "kernel image must be non-PIC...")`, turning the header comment's prose invariant into a build-time-checked one.

**API design & taxonomy**

- **[🟡 MEDIUM]** `SyscallError` has no variant for the "no current task" control-plane failure; `dispatch.rs` is forced to misreport it as a capability error — `kernel/src/syscall/error.rs:59-85` (the `SyscallError` enum); consumed at `kernel/src/syscall/dispatch.rs:144-161`
  **Action:** Add a `SyscallError::NoCurrentTask` variant with its own stable top-level status code (e.g. `4`, next free after `BadArgument`=2/`FaultAddress`=3), and have `dispatch.rs`'s `task_yield`/`task_exit` no-current-task branches return it instead of borrowing `CapError::InvalidHandle`. Low-risk since `SyscallError` is `#[non_exhaustive]` and the branch is unreachable from a real EL0 caller in v1 (defensive-only) — a good moment to fix the taxonomy before any userspace binding pattern-matches on `0x102`.

- **[⚪ LOW]** Status-code block encoding relies on manual discipline with no compile-time bound guard, unlike the file's own `NULL_CAP_HANDLE` precedent — `kernel/src/syscall/error.rs:46-48` (`CAP_STATUS_BASE`/`IPC_STATUS_BASE`) and `:122-148`
  **Action:** Add a `const _: () = assert!(...)` (mirroring `abi.rs:41-44`) bounding the maximum literal used in `cap_error_code`/`ipc_error_code` below `CAP_STATUS_BASE`'s width.

- **[🟡 MEDIUM]** `tyrne-user::SyscallError` exposes only the raw status word, with no decode/classification API — `userland/tyrne-user/src/lib.rs:61-68`
  **Action:** Add a decode step — either a small mirrored enum with `From<SyscallError>`/`TryFrom<u64>`, or at minimum classification methods (`is_cap_error`, `is_ipc_error`, `top_level_kind`) built from the same `0x100`/`0x200` block constants the kernel already documents.

- **[🟡 MEDIUM]** The BSP-side syscall trust boundary (fail-closed gate #3 selection logic) has zero automated test coverage of any kind — `bsp-qemu-virt/src/syscall.rs:143-294` (`syscall_entry`, esp. the match at lines 182-193)
  **Action:** Extract the match's branch-selection logic into a small, host-testable pure function — e.g. `fn resolve_syscall_context(current_table, current_window, resolved_as) -> (bool, ...)` — mirroring the `start_prelude` extraction pattern already used successfully in `kernel/src/sched/mod.rs` (T-011). Pair with a QEMU-smoke assertion (once CI-gated per Track B.2-1) that a syscall issued with no current task actually observes FAILCLOSED_TABLE behavior end-to-end.

- **[🟡 MEDIUM]** The only real EL0 userspace program exercises just two syscalls (console_write, task_exit); no end-to-end test proves the confused-deputy defenses against a real (non-fake) MMU — `userland/hello/src/main.rs:44-49` (`_start`); `kernel/src/syscall/user_access.rs` tests (all against `FakeMmu`/`BlockMappedMmu`, never `bsp-qemu-virt`'s `QemuVirtMmu`)
  **Action:** Add a second, deliberately-adversarial userland image (or extend `hello` behind a feature flag) that attempts an out-of-window `console_write`, a `console_write` against a page without USER, and an IPC call with a stale capability handle, asserting each is rejected via the real trap frame + real page tables. Wire into the future `qemu-smoke` CI job (Track B.2-1).

- **[⚪ LOW]** `IpcQueues::peek_state` is named and documented as a non-mutating read but silently mutates state on the stale-generation path — `kernel/src/ipc/mod.rs:254-271` (`reset_if_stale_generation`), `:278-281` (`peek_state`), `:330-333` (call-site comment)
  **Action:** Add one sentence to `peek_state`'s doc-comment distinguishing "non-destructive to any live endpoint's observable state" from "side-effect-free" (it takes `&mut self`), or rename to `state_for_read` to remove the ambiguity directly.

**Testing gaps & misc hygiene**

- **[⚪ LOW]** No regression test pins self-transfer (`transfer == Some(ep_cap)`) semantics in `ipc_send` — `kernel/src/ipc/mod.rs:303-374` (`ipc_send`); test module `:668-1720`
  **Action:** Add a regression test that calls `ipc_send(..., ep_cap, ..., transfer: Some(ep_cap))` and asserts it succeeds, that the sender's table no longer resolves `ep_cap` afterward, and that the receiver obtains a valid capability to the same endpoint.

- **[⚪ LOW]** Arena capacity const-assert is off-by-one (overly conservative, not exploitable) — `kernel/src/obj/arena.rs:109-112`
  **Action:** Change the condition to `N <= (Index::MAX as usize) + 1` (underflow-guarded for `N == 0`) and update the assertion message. Low priority — no current instantiation is anywhere near this boundary.

- **[⚪ LOW]** `Arena::allocate` has no must-use protection despite an unrecoverable-leak failure mode — `kernel/src/obj/arena.rs:145`
  **Action:** Add an explicit `#[must_use]` to `Arena::allocate` (overriding the clippy `&mut self` heuristic). Optional: the same for `Arena::free`'s `Option<T>` for symmetry.

- **[⚪ LOW]** Generation counter is unwidened/unguarded against wraparound-induced stale-handle revalidation (ABA) — `kernel/src/obj/arena.rs:169`
  **Action:** At minimum, add a doc comment on `Generation`/`Arena::free` acknowledging the accepted wraparound bound so it reads as a reviewed, deliberate tradeoff. For genuine hardening, consider retiring a slot from the free list once its generation reaches `Generation::MAX` rather than wrapping (the arena has 16 slots of headroom to lose one permanently).

- **[⚪ LOW]** Test coverage gaps on three explicitly-designed panic/error paths: `register_idle` double-registration, `enqueue_ready`'s invariant panic, and `add_task`/`add_user_task`'s `QueueFull` error — `kernel/src/sched/mod.rs:787-800` (register_idle assert), `:598-609` (enqueue_ready panic), `:392` and `:497` (QueueFull production sites)
  **Action:** Add three small tests mirroring the file's existing white-box style: (a) `#[should_panic(expected = "register_idle called twice")]` calling `register_idle` twice; (b) fill `sched.ready` to capacity then trigger `enqueue_ready` inside a `#[should_panic]` test; (c) fill the ready queue to `TASK_ARENA_CAPACITY` and assert the `(N+1)`th `add_task` call returns `Err(SchedError::QueueFull)`.

- **[⚫ INFO]** Bridge entry points document a "pointer validity" precondition but perform zero defensive checks on it, inconsistent with the `debug_assert` precedent set elsewhere in the same file — `kernel/src/sched/mod.rs:667-668` (documented precondition), `:772-815,1093-1107,1259-1290,1369-1407` (none add a `debug_assert` on their `*mut` parameters)
  **Action:** Optional polish: add `debug_assert!(!sched.is_null())` (and companions for `ep_arena`/`queues`/`caller_table` where present) at the top of each bridge entry point, matching the precedent already set by `add_user_task`. Low priority given the caller surface is BSP-only, not attacker-reachable.

- **[⚫ INFO]** `start_prelude`'s panic message hardcodes 'start' even though `task_exit_current` shares the same helper — `kernel/src/sched/mod.rs:872`
  **Action:** Reword to be caller-agnostic, e.g. "scheduler dispatch called with empty ready queue and no idle task", or thread a `&'static str` caller-tag into `start_prelude`.

- **[⚪ LOW]** The endpoint cap-leak-on-destroy `debug_assert!` regression test injects private state directly rather than driving the documented leak scenario through the real public-API sequence — `kernel/src/ipc/mod.rs:1668-1686` (`stale_send_pending_with_some_cap_panics_in_debug`); `kernel/src/obj/endpoint.rs:80-102` (C3-001 doc)
  **Action:** Add a companion test that drives the real sequence: `ipc_send(..., Some(xfer_cap))` to reach `SendPending{cap:Some(_)}`, then `table.cap_drop(ep_cap); destroy_endpoint(...)`, then a fresh `create_endpoint` in the likely-same slot, then a subsequent IPC op — `#[should_panic]` in debug, confirming the actual production call path trips the guard.

- **[⚫ INFO]** Redundant fully-qualified path for an already-imported constant — `test-hal/src/mmu.rs:569`
  **Action:** Drop the `tyrne_hal::` qualifier for consistency with the rest of the file.

**Misc**

- **[⚪ LOW]** Stale comment: `task_a`'s IPC send no longer "yields to B" once the EL0 `hello` task shares the ready FIFO — it yields to `hello` first — `bsp-qemu-virt/src/main.rs:671-673` (and the mirrored comment at `:692-696`)
  **Action:** Update the comment in `task_a` (and its `ipc_recv_and_yield` counterpart) to describe the actual post-T-028 interleaving (send unblocks B → generic FIFO yield actually dispatches `hello` first → `hello` exits → B resumes), or, if determinism of the demo trace is considered valuable, consider whether `hello` should be added to the scheduler *after* the A/B demo tasks are known to have finished their round trip — the current comment should not claim behavior the FIFO does not produce.

- **[⚪ LOW]** The debug-console security gate is keyed off the general-purpose `debug_assertions` cfg rather than a dedicated feature flag — `kernel/src/syscall/abi.rs:69-91`
  **Action:** Introduce a dedicated, explicit Cargo feature (e.g. `debug-console`, off by default) that gates `SyscallNumber::ConsoleWrite` instead of reusing `debug_assertions`. Only `cargo kernel-build`/dev workflows enable it explicitly (e.g. via a `kernel-build-debug` alias that passes `--features debug-console`), decoupling the security posture from any future profile that happens to turn on `debug-assertions` for unrelated reasons.

### Acceptance criteria

- `PhysAddr`/`VirtAddr` gain arithmetic/alignment helpers; `phys_to_kernel_va`/`kernel_va_to_phys` and `UserAccessWindow` use typed addresses at their public boundaries.
- `CapabilityTable` is rebased on the shared `Arena` type; the five hand-rolled resolve-capability call sites use one shared primitive.
- `copy_from_user`/`copy_to_user` share their per-page validated-copy loop.
- `SyscallError` gains a `NoCurrentTask` variant; `tyrne-user::SyscallError` gains a decode/classification API.
- The BSP syscall trust boundary's branch-selection logic is extracted into a host-testable pure function with test coverage.
- The remaining low/info dead-code and doc-nit items are cleaned up opportunistically; none are release-blocking for this phase.

---

## Track B.2-5 — Unsafe-audit & doc-comment hygiene

Separate from Track B.2-2's architecture-level documentation, this track is the code-level counterpart: `docs/audits/unsafe-log.md` entries whose Location/Invariants fields no longer match their call sites, and rustdoc/doc-comments in source files that describe a state of the world Phase B has since moved past. Several of these discharge security-relevant invariants (the PMM's `could_yield_pa_overlapping`, the copy-user path's `FrameProvider::alloc_frame` contract) — leaving them stale risks a future maintainer reasoning from a wrong premise.

### Sub-breakdown

- **[⚪ LOW]** Doc comment incorrectly claims an L0 block descriptor exists in VMSAv8-64 — `hal/src/mmu/vmsav8.rs:222-228`
  **Action:** Change the second bullet to "L1/L2 with bit1=0 → block descriptor (huge page)" and add an explicit bullet: "L0 with bit1=0 → reserved (translation fault); VMSAv8-64 defines no L0 block descriptor."

- **[⚪ LOW]** UNSAFE-2026-0028's Location/Invariants fields contradict its own Amendment — `docs/audits/unsafe-log.md:636,640,651` (call site: `bsp-qemu-virt/src/main.rs:1176-1186`, inside `kernel_main_high`)
  **Action:** Update the Location: and Invariants: fields to say `kernel_main_high` (or add a one-line correction note pointing to the Amendment), consistent with how sibling entries UNSAFE-2026-0022/0023/0024/0025/0026/0027 each got a T-022 Amendment.

- **[⚪ LOW]** A second `Pl011Uart::new` call site (`kernel_main_high`, high-half alias) also cites UNSAFE-2026-0001 despite mismatching both the entry's Location and Operation fields — `bsp-qemu-virt/src/main.rs:1013-1015` (vs. `docs/audits/unsafe-log.md:17-18`)
  **Action:** Add an Amendment to UNSAFE-2026-0001 explicitly covering the high-half persistent-Console construction in `kernel_main_high` (same underlying device, different address expression and function), following the same append-only Amendment discipline used elsewhere. Same root cause as the two findings above: audit-log entries not updated when T-022 split `kernel_entry` into two functions.

- **[⚫ INFO]** Doc-comment typo: duplicated word "dispatch dispatch" — `bsp-qemu-virt/src/exceptions.rs:34`
  **Action:** Change to "because the IRQ-dispatch table is the natural home for".

- **[⚪ LOW]** `bsp-qemu-virt/src/main.rs`'s `PMM_EXTENT_START` comment cites a `linker.ld` `MEMORY`/`RAM`/`ORIGIN` construct that was deleted from linker.ld during the ADR-0033 high-half migration and never existed again since — `bsp-qemu-virt/linker.ld` (whole file, no `MEMORY` block present) cross-referenced from `bsp-qemu-virt/src/main.rs:95-96`
  **Action:** Update the main.rs:95-96 doc comment to stop referencing a `MEMORY`/`RAM`/`ORIGIN` construct that no longer exists — e.g. "Matches linker.ld's KERNEL_IMAGE_PHYS_BASE-derived KBASE placement (`. = KBASE` at line ~50) for QEMU virt" or point at ADR-0033 instead. If Track B.2-4's linker-symbol cross-check lands, fold this comment fix into the same change.

- **[⚪ LOW]** Crate-level doc comment claims the kernel "defines... interrupt dispatch", contradicting both reality and the file's own P6 claim two lines later — `kernel/src/lib.rs:5-10`
  **Action:** Reword to accurately scope the crate, e.g.: "This crate defines the capability system, scheduler, IPC primitives, memory management, and the EL0→EL1 syscall boundary's kernel-side half (`syscall`). Asynchronous interrupt handling is board-specific and lives in the BSP per [P6](../../standards/architectural-principles.md); the kernel side only sees cooperative interrupt-masking primitives (`sched::IrqGuard`) around context switches." (In the source doc-comment itself, wire `[P6]` to whatever intra-doc reference the crate uses for the BSP interrupt-handling principle.)

- **[⚫ INFO]** Audit-log entry title for UNSAFE-2026-0030 still names the superseded primitive (`copy_nonoverlapping`) that this file no longer uses — `docs/audits/unsafe-log.md:676` (heading) vs. `kernel/src/syscall/user_access.rs:245,313`
  **Action:** Update the UNSAFE-2026-0030 heading to say `core::ptr::copy` (or "byte move" without naming a specific primitive) to match the amended operation.

- **[⚫ INFO]** Lint-provenance comment enumerates workspace lints but omits two that actually exist (`unreachable_pub`, `unused_must_use`) — `kernel/src/lib.rs:51-54`
  **Action:** Either add the two missing lint names, or (more robust against future drift) replace the itemized list with a pointer: "see `[workspace.lints]` in the root Cargo.toml for the full list."

- **[⚪ LOW]** Module doc-comments in endpoint.rs / notification.rs / task.rs describe a design that never materialized and is now factually wrong — `kernel/src/obj/endpoint.rs:5-7,16-17`; `kernel/src/obj/notification.rs:5-7`; `kernel/src/obj/task.rs:5-7`
  **Action:** Refresh all three module docs now that Phase B is closed: state plainly where the real state lives (`ipc::IpcQueues` for endpoint waiters; scheduler-side per-task arrays in `sched::Scheduler` for context; and for Notification, that blocking-wait remains unimplemented and is still an open roadmap item, not an A4-completed feature).

- **[⚪ LOW]** `SchedError::QueueFull` doc comment claims it is produced "only" by `add_task`, but `add_user_task` returns it through the identical path — `kernel/src/sched/mod.rs:178-186` (doc), `:493-497` (add_user_task's matching QueueFull path)
  **Action:** Update the doc comment to "Produced by [`add_task`] or [`add_user_task`] at registration time..." (or link both).

- **[🟡 MEDIUM]** `could_yield_pa_overlapping`'s doc-comment is stale: describes the ADR-0033 high-half migration as a future placeholder, but it landed at T-022 and the call site already uses it — `kernel/src/mm/pmm.rs:560-565`
  **Action:** Update the doc-comment to state the migration is complete and name the actual helper (`tyrne_hal::kernel_va_to_phys`), matching the phrasing already used in mod.rs's `phys_frame_kernel_ptr` doc and in task_loader.rs's own comment at the call site. This is a security-relevant invariant description (it discharges UNSAFE-2026-0027's non-overlap precondition) — leaving it stale risks a future maintainer reasoning from a wrong premise.

- **[⚪ LOW]** `Pmm::new`'s inline "Validation (i)/(ii)/(iii)/(iv)" code-comment labels don't correspond to the doc-comment's 5 enumerated steps — `kernel/src/mm/pmm.rs:159-178` (docstring steps 1-5) vs. `:200,207-214,216,223,239` (inline validation labels)
  **Action:** Renumber the inline roman-numeral labels to match the docstring's 1-5 ordering (or switch the docstring to reference the same non-sequential internal labels), so a maintainer cross-referencing the two doesn't have to reverse-engineer the correspondence.

- **[⚪ LOW]** Duplicate "Step 4" comment label in `cap_create_address_space` — the unsafe `create_address_space` block should be labeled Step 5 — `kernel/src/mm/address_space.rs:605` and `:611`
  **Action:** Relabel the comment at line 611 from "Step 4" to "Step 5" so the code matches the docstring enumeration.

- **[⚪ LOW]** `load_image`'s public-fn contract omits that a mis-sourced image slice can panic the kernel via `kernel_va_to_phys`, not return `LoadError` — `kernel/src/obj/task_loader.rs:589-608` (row 4 preflight), `:604` (`kernel_va_to_phys` call site); `hal/src/mmu/mod.rs` `kernel_va_to_phys`
  **Action:** Add a one-line `# Panics` section to `load_image`'s rustdoc cross-referencing `kernel_va_to_phys`'s own panic contract, so a future caller passing a non-kernel-owned image slice discovers the precondition from the doc rather than from a kernel abort.

- **[⚪ LOW]** console_write's doc comment implies a partial-write result but v1's kernel semantics are strictly all-or-nothing — `userland/tyrne-user/src/lib.rs:72-77`
  **Action:** Tighten the doc to state the v1 guarantee explicitly, e.g. "Returns `buf.len()` on success (v1 is all-or-nothing: a partial write never happens) or the raw kernel status word on rejection."

- **[⚪ LOW]** `tyrne-user`'s `#![no_std]` is unconditional, contradicting its own doc comment's claim to mirror the kernel's `cfg_attr(not(test), no_std)` discipline — `userland/tyrne-user/src/lib.rs:21` and `:27`
  **Action:** Either change line 21 to `#![cfg_attr(not(test), no_std)]` to actually match the kernel's discipline, or fix the comment to stop claiming a pattern the code doesn't use.

- **[⚫ INFO]** hello's panic exit code (101) and the success exit code (0) are currently discarded by the kernel — not yet an observable distinction — `userland/hello/src/main.rs:44-58`
  **Action:** Optional: add a one-line note to the panic handler's doc comment that the exit code is currently write-only from userspace's perspective, to set correct reader expectations until a future task surfaces task exit status.

- **[⚪ LOW]** `cap_create_address_space`'s doc comment claims it resolves the parent cap "via `resolve_address_space_cap`", but the function body reimplements the lookup+kind-check inline instead of calling that helper — `kernel/src/mm/address_space.rs:447` (doc claim) vs. `:547-553` (actual body)
  **Action:** Either make `cap_create_address_space` actually call `resolve_address_space_cap` (extending it to also return the Capability/rights/depth it needs), or correct the doc comment. The former also resolves an identical `task_loader.rs:538-543` duplicate by giving all these sites one real shared implementation.

- **[🟡 MEDIUM]** `TrapFrame` / `SyscallTrapFrame` lack the per-field `offset_of!` pinning the project itself identified as necessary for this exact class of asm/Rust layout drift — `bsp-qemu-virt/src/exceptions.rs:112` and `bsp-qemu-virt/src/syscall.rs:90` (contrast: `bsp-qemu-virt/src/cpu.rs:339-344`)
  **Action:** Add `core::mem::offset_of!` const-asserts for every field of `TrapFrame` and `SyscallTrapFrame`, mirroring `cpu.rs:340-344`. Consider promoting the pattern into `unsafe-policy.md` as a companion to the existing S5a naked-fn rule so future trap-frame-shaped structs inherit the discipline by default — directly relevant as Phase C's SMP/preemption work introduces new trap-frame-shaped structs.

- **[🟡 MEDIUM]** `FrameProvider::alloc_frame`'s load-bearing zero-initialised contract is documented in prose on a safe trait method, not enforced as an `unsafe fn` contract, unlike the structurally identical `Mmu::create_address_space` — `hal/src/mmu/mod.rs:349-355` (contrast `hal/src/mmu/mod.rs:481-488`; consumed unsafely at `bsp-qemu-virt/src/mmu.rs:622-631`)
  **Action:** Either mark `FrameProvider::alloc_frame` `unsafe fn` with a `# Safety` section stating the zero-init and exclusive-ownership requirements, mirroring `Mmu::create_address_space`, or add a debug-only zero-scan assertion at the one production consumption point (`walk_or_alloc_table`'s allocate-new-table branch).

- **[⚪ LOW]** `add_user_task` hardens the `cap_table` null-pointer hazard for release builds but leaves the equally load-bearing `kernel_stack_top`/`user_sp` invariants debug-assert-only — `kernel/src/sched/mod.rs:455-480` and `:510`
  **Action:** Defensible today since `add_user_task` is `unsafe fn` and its caller is in-tree BSP/loader code, so treat as polish. For uniform posture, consider the same release-mode degrade-safely pattern for `kernel_stack_top`/`user_sp`, or document in the function's `# Safety` section why `cap_table` alone warranted extra release-mode hardening.

### Acceptance criteria

- Every UNSAFE-2026-NNNN audit-log entry cited above matches its actual call site (Location/Invariants fields, Amendment cross-references, and heading text all consistent).
- All module/crate/function doc-comments identified above are corrected to describe the current, landed behavior.
- `could_yield_pa_overlapping`'s doc-comment states the ADR-0033 migration is complete and names the real helper.
- `TrapFrame`/`SyscallTrapFrame` gain `offset_of!` const-asserts for every field, mirroring `cpu.rs`.
- `FrameProvider::alloc_frame`'s zero-init contract is either an `unsafe fn` with a `# Safety` section, or backed by a debug-only zero-scan assertion.

---

## Track B.2-6 — Performance micro-fixes

Two small, low-severity performance findings surfaced by the review land here. Both are explicitly framed by the review itself as deliberate safety-over-performance tradeoffs rather than defects, so neither blocks this phase's exit bar — they're tracked so they aren't lost, and so the review's own recommendation to fix them "once the first non-console/production syscall lands" has a durable home.

### Sub-breakdown

- **[⚪ LOW]** console_write's whole-range probe and per-chunk copy re-probe every page redundantly — `kernel/src/syscall/dispatch.rs:252-300`
  **Action:** This is a deliberate, documented safety-over-performance tradeoff, not an oversight — treat as low priority. Once Track B.2-3's length cap lands (bounding worst-case iterations), consider whether a single probed-then-trusted copy pass (skip the chunk-level re-probe once the whole range already passed Gate 3, keeping only the chunk-level re-validate) would meaningfully cut per-page `Mmu::translate` calls without weakening the all-or-nothing guarantee — profile first.

- **[⚪ LOW]** `copy_from_user`/`copy_to_user` walk the page table twice for every page touched — `kernel/src/syscall/user_access.rs:150-154` (`probe_user_pages`), `:199` and `:213-215` (copy_from_user's second translate)
  **Action:** Before the first production syscall that carries a real (non-console) buffer lands, restructure `probe_user_pages` to cache the resolved `PhysFrame` per page into a small fixed-size buffer so the copy pass consumes the cached frame instead of re-translating. Keeps the cheap USER-bit re-check while dropping the second 4-level table walk. Low urgency today since the only caller is debug-only; worth fixing opportunistically alongside whichever task adds the first real `copy_to_user` caller.

### Acceptance criteria

- Either fixed, or explicitly deferred with a one-line profiling note, once Track B.2-3's console_write length cap lands.

---

## Polish & excellence opportunities

None of the following are defects — they are the review's excellence-track observations, grouped by theme and condensed. They are not gating for Phase B.2's exit bar; pick them up opportunistically alongside the track work above, or leave them for a future phase's backlog.

### Documentation

- **Polish** — Add a dedicated architecture chapter for the syscall ABI / EL0 execution model, synthesizing the pipeline diagram, capability-gating discipline, audit-log surface, and rollback/error taxonomy that today are scattered across four inconsistently-tensed documents.
- **Polish** — Adopt a lightweight "last verified against" freshness marker on each architecture doc, tied to the phase-closure checklist — the same staleness root cause (task-loader.md, hal.md, scheduler.md, exceptions.md, overview.md all describing B6 as future work after B6 closed) repeated five times.
- **Polish** — Resync overview.md's boot-flow Mermaid diagram with boot.md's now much richer sequence, since overview.md is the first document a reader opens.
- **Polish** — Consolidate the scattered Phase-C (multi-core) readiness backlog into one index (in phase-c.md or a short new ADR) cross-linking every deferred single-core assumption.
- **Polish** — Close the two dangling append-only-correction gaps (ADR-0011 GICv3, ADR-0012 EL-drop) in the same sweep as the other ADR fixes in Track B.2-2 — the only two places the project's otherwise-working forward-pointer mechanism was applied inconsistently.
- **Polish** — Revisit the bitflags-crate open question now that two hand-rolled bitfields exist project-wide (Track B.2-4) — a short successor ADR/rider deciding "still no" or "yes, adopt now" closes the question before a third and fourth hand-rolled bitfield accrete.
- **Polish** — Ground the IrqGuard vtable-aliasing claim (ADR-0008) in rustc/LLVM evidence or retract it — the same rigor unsafe-policy demands of safety-relevant unsafe code should apply to safety-relevant ADR rationale duplicated into source rustdoc.
- **Polish** — console_write's production/debug gate rides on `cfg!(debug_assertions)` rather than a dedicated Cargo feature; ADR-0031 left this as an open implementation choice, but a dedicated `debug-console` feature (default off) would make the gate's intent explicit and independently auditable.
- **Polish** — Extract the `write-adr` skill's §Simulation + row-to-verification-mapping discipline into a lightweight linter/checklist, mechanising a check that is currently enforced entirely by careful re-reading.
- **Polish** — Automate the drift-detection this review had to do by hand (test-naming adoption, commit-scope drift, untagged fences, broken cross-references) as a standing ~50-line script rather than a periodic full manual pass.
- **Polish** — Mark each standard's volatile (CI/tooling-dependent) claims with an explicit enforcement-status tag, mirroring infrastructure.md's exemplary "Required (enforced today)" / "Planned (not yet enforced)" / "Advisory" split — the other five CI-referencing standards state their gates in flat prose, which is exactly where this review found staleness.
- **Polish** — Give logging-and-observability.md an explicit implementation-status banner — the single largest gap between prescriptive tone and implementation reality in the standards folder.
- **Polish** — Reconcile commit-style.md's scope enum with reality and add the CI gate the doc itself calls "planned", in one pass, so future scope drift doesn't re-accumulate the way it did between the list's original authoring and today's 38-commit `roadmap` usage.
- **Polish** — Institutionalize a roadmap/task-corpus consistency check (diff each phase README's task index against `ls`, flag any task current.md calls "Done" whose own Status isn't, collect tentative ADR numbers across all phase files and flag duplicates) instead of relying on periodic master-review sweeps.
- **Polish** — Formalize the `date_done` field in TEMPLATE.md — a template field is cheaper to keep correct than a prose convention that has to be independently rediscovered each time, and this exact gap let the Status-drift defect recur nine times in a row.
- **Polish** — Add a lightweight relative-link checker to the docs corpus (no network calls, repo-relative-only) — near-zero-cost and would have caught two of the broken-link findings above automatically.
- **Polish** — Add `<a id="...">` anchors immediately before each glossary headword so the 20 existing cross-references can land precisely, without changing the glossary's flat-list visual format.
- **Polish** — Automate the index-vs-disk reconciliation this review had to do by hand (a `sync-task-index`/`sync-review-index` skill, or a CI grep step comparing `ls <dir>` against each README table).
- **Polish** — Add a one-line "status as of `<date>`" stamp on high-churn status paragraphs, or have them defer to `docs/roadmap/current.md` as the mechanically-checkable source of truth instead of restating the phase number inline.
- **Polish** — Codify a "closure-batch index sweep" checklist item in the business master-plan, mirroring the existing "no closure-trio without recorded smoke" acceptance criterion — the performance master-plan's own "Index in README.md updated" AC already exists in principle but isn't enforced at closure time.
- **Polish** — Add a "Phase-C readiness sweep" cross-reference table before Phase C tasks are scoped, consolidating the security review, the business review's Adjustments, and phase-c.md's own carry-forwards into one artifact.
- **Polish** — Run a second whole-tree master review at the Phase B → Phase C boundary — the prior master review's ROI was clearly high (4 Blockers + 18 Majors found and mostly fixed same-week), and a phase boundary is the textbook trigger point for the next run.

### Build / infra / CI

- **Polish** — Parameterize the QEMU core count (`QEMU_SMP` env var threaded through `tools/run-qemu.sh`, plus a documented cargo-runner override) ahead of Phase C, so `cargo run`/`cargo kernel-run` don't silently stay single-core once the scheduler grows SMP support.
- **Polish** — Consider migrating to Rust edition 2024 once Phase C stabilizes, making several hand-enforced lint levels the language default rather than a repo-local override a future crate could forget to inherit.
- **Polish** — Make the release profile self-documenting about panic strategy with a one-line comment directly above `[profile.release]` pointing at `.cargo/config.toml`'s rustflags.
- **Polish** — Wire `tools/smoke.sh` into CI as a real `qemu-smoke` job — the single largest gap between what the project's docs/README/CLAUDE.md claim is verified and what CI actually enforces (see Track B.2-1's findings; this is the same fix, framed as closing that trust gap).
- **Polish** — Close the userland-crate clippy gap (Track B.2-1) — the userland crates carry the actual EL0/EL1 unsafe syscall-trap boundary, exactly the code CLAUDE.md's rule #2 is most concerned with, yet are the only crates with zero clippy coverage in CI.
- **Polish** — Shellcheck the `tools/` scripts, especially `perf-harness.sh` (600 lines of bash with background-job watchdogs, signal traps, and awk pipelines — a script that already carries shellcheck-disable directives implying this was the original intent).
- **Polish** — Add `--smp` passthrough to `run-qemu.sh`/`smoke.sh` ahead of Phase C (Track B.2-1) — cheaper to do now than to retrofit once SMP tasks are already in flight and depend on the tooling.
- **Polish** — Add a build-time size guard (`ASSERT(__bss_end - KBASE <= 0x0800_0000 * 64, ...)`) bounding the kernel image against its mapped 128 MiB RAM window, moving a future overflow from a cryptic runtime translation fault to a clear build error.
- **Polish** — Add `OUTPUT_ARCH(aarch64)` to both linker scripts — a low-cost, purely defensive addition common in embedded/from-scratch OS linker scripts that gives the linker an extra independent cross-arch check.
- **Polish** — Extend the aarch64-host build-hazard fix (Track B.2-3) with an actual periodic or PR-gated arm64 host-check CI job — the bug class is otherwise structurally invisible to CI, since all runners are x86_64.

### Kernel: capabilities & syscall

- **Polish** — Document the `debug_assertions` ↔ release-profile dependency directly in Cargo.toml, next to the existing `overflow-checks` comment (see Track B.2-1's release-gate finding for the same underlying concern).
- **Polish** — Add a tiny `SyscallError -> &'static str`/`Display` helper for kernel-side diagnostics, kept close to the source of truth rather than letting `tyrne-user`'s error-rendering code re-derive a parallel string table.
- **Polish** — Make the `has_current_task` ↔ empty-table pairing self-checking (a `debug_assert`), not just correctly-constructed-by-convention — the file's own docstring calls this "the single most security-sensitive control-flow join in the kernel".
- **Polish** — Extract the duplicated per-page cursor-walk arithmetic into one shared helper (see Track B.2-4's `copy_from_user`/`copy_to_user` dedup finding) so a future fix to the cursor math automatically applies to both directions.
- **Polish** — Add a short worked example to `user_access.rs`'s module doc for future pointer-returning syscalls, lowering the chance a future syscall re-implements a weaker ad hoc validation.

### Kernel: IPC / objects / scheduler

- **Polish** — Make `SendOutcome` and `RecvOutcome` `#[non_exhaustive]`, matching `IpcError`, for a symmetric forward-compatibility stance across the whole public IPC outcome/error surface.
- **Polish** — Document the compound-failure error-priority in `ipc_send` explicitly, matching the treatment the module already gives the ADR-0030 K2-5 ordering commentary.
- **Polish** — Give `Task` a hazard doc-comment symmetric with `Endpoint`'s C3-001, pre-empting the same bug class at the same documentation bar.
- **Polish** — Add typed `get_*_mut` wrappers for symmetry with `get_task`/`get_endpoint`/`get_notification`, tightening the API surface so "typed handles are the only way in" stays visibly true rather than true only by convention.
- **Polish** — Make the `current_idx != next_idx` invariant self-defending instead of debug-only — the single invariant the entire ADR-0021 raw-pointer bridge depends on for its no-aliasing soundness claim; the file already has the idiom for this (the idle-filter guard) two dozen lines away.
- **Polish** — Amend the UNSAFE-2026-0008 / UNSAFE-2026-0014 audit entries to state the "no slot reuse" precondition explicitly, in the same spirit as ADR-0026's own postmortem lesson about writing an explicit state-machine simulation table.

### Kernel: memory (PMM/address-space)

- **Polish** — Round out reserved-range capacity boundary test coverage to mirror the existing N*8 exact-fit test, closing the same off-by-one risk class symmetrically.
- **Polish** — Collapse or type-distinguish `wrap_bootstrap` vs. `from_mmu_address_space` — the "call exactly once, only for the already-live bootstrap topology" invariant is currently documentation-only; a marker type or restricted visibility would make it compiler-checked.
- **Polish** — Assert the bootstrap-handle ordering invariant at the BSP call site (`debug_assert_eq!(bootstrap_as_handle, BOOTSTRAP_ADDRESS_SPACE_HANDLE)`), converting a silently-violable convention into a checked one (see Track B.2-3's related finding).

### Test-HAL & userland

- **Polish** — Clarify the unsafe-policy's "`#[cfg(test)]` modules" wording to explicitly cover dev-dependency-only crates, so SAFETY comments in `test-hal` are literal-compliant rather than compliant-by-charitable-reading.
- **Polish** — Document `set_now`'s monotonicity break explicitly, or split it from the monotonic-safe advance API, so a future test author doesn't unknowingly rely on backward-time behavior no real Tyrne target can produce.
- **Polish** — Give `tyrne-user`'s `SyscallError` decode helpers instead of a bare status word (see Track B.2-4's decode-API finding) — as soon as a second userspace program needs to branch on error kind, it would otherwise reverse-engineer the bit layout by hand.
- **Polish** — Wrap capability handles in a userland newtype instead of a bare `u64` (see Track B.2-4's `CapWord` finding) — cheap to prevent early, expensive to retrofit once more syscalls/caps exist.
- **Polish** — Extend `hello.ld`'s PIC-artifact ASSERTs to relocation sections — the one category of PIC artifact the current script's loud-build-time-failure philosophy doesn't yet cover.

### Cross-cut: concurrency/SMP

- **Polish** — Codify the "single-core cooperative" invariant as one greppable marker (a `const TYRNE_SINGLE_CORE_V1: bool = true;` or `cfg` feature referenced by the ~13 files/subsystems that key off it) instead of ~64 independent prose restatements, turning Phase C's kickoff into a literal, compiler-checkable worklist (`#[cfg(not(feature = "smp"))]` gating the current unsynchronized fast paths). Directly de-risks the Milestone C1/C2 migration.

### Doc/code contradictions

- **Polish** — Automate a doc/trace drift check in CI — this review found exactly one class of defect (a README trace line for a print statement that no longer exists) that a machine-checkable invariant would catch for free.
- **Polish** — Bind `docs/roadmap/current.md` updates to the merge commit itself, not a follow-up doc pass — the gap is process sequencing, not missing tooling, given the project's already-disciplined skill-driven procedures.
- **Polish** — Timestamp/pin the roadmap's top banner to a commit SHA, so a reader can tell at a glance whether it reflects HEAD without cross-referencing `git log` by hand.

### Cross-cut: performance

- **Polish** — Schedule the per-AS ASID allocator now that Phase C is starting and real per-task address spaces exist — `activate()`'s full flush is no longer purely theoretical now that T-028 landed the first real EL0 task with its own AS, and Phase C's cross-core `TLBI VMALLE1IS` broadcast would make the same-core cost far more expensive per switch. Relevant to Milestone C5 (TLB shootdown) — landing the already-forward-flagged `AddressSpace::asid` field before Phase C's scheduler work begins avoids compounding an expensive pattern across cores.
- **Polish** — Turn the IPC-delivery receiver lookup into O(1) by storing the blocked `TaskHandle` directly in the endpoint's `IpcQueues` waiter state, before Phase C's larger task counts make the already-documented O(N) scan both bigger and harder to retrofit.
- **Polish** — Reverse-index (or refcount) capability→object references before Phase C destroy/revoke traffic grows, landing alongside the ADR-0023 cross-table-CDT work the in-code note already cross-references.
- **Polish** — Re-run and extend the T-029 perf harness after the SVC trampoline callee-saved-register trim (a performance fix tracked outside this phase's routing), adding a fourth measured primitive (`Mmu::activate`'s TLB-flush cost in isolation) to quantify the ASID-allocator opportunity above.

### Cross-cut: quality/API/testing

- **Polish** — Track `phys_to_kernel_va`/`kernel_va_to_phys`'s hard `assert!` (reachable transitively from the syscall-facing copy path, currently inert) as a named forward-flag for the Phase D (Pi 4) planning docs — fixing it now would mean plumbing a `Result` through a `const fn` for no present benefit.
- **Polish** — Give `PhysAddr`/`VirtAddr` a small, audited arithmetic/alignment API (see Track B.2-4's newtype findings — same fix, framed as excellence).
- **Polish** — Add `Nanos`/`Ticks` newtypes to `hal::timer`, turning the exact class of mistake the trait doc warns about into a compile error, at zero runtime cost.
- **Polish** — Reconcile `CapRights::from_raw` and `MappingFlags::from_raw`'s diverging unknown-bit semantics, or cross-reference the deliberate divergence explicitly in both doc comments.
- **Polish** — Promote `tools/smoke.sh` from a manual maintainer ritual to a first-class CI gate with a companion coverage-of-scenarios report (see Track B.2-1 — same fix, framed as rigor-parity with the host-test suite's invariant-based assertions).
- **Polish** — Extract a host-testable "resolve syscall context" pure function from `bsp-qemu-virt/src/syscall.rs::syscall_entry` (see Track B.2-4's BSP-trust-boundary finding — same fix).
- **Polish** — Bundle the recurring `(table, pmm, mmu, as_arena)` quadruple into a small context struct, mirroring `SyscallContext`'s existing pattern, and shrinking several already-flagged `too_many_arguments` sites.
- **Polish** — Let `task_loader`'s image-page loop and stack-page loop share their alloc+map+rollback shape — the function's own comment already flags this as intentional, acknowledged duplication.
- **Polish** — Centralize the u128-to-saturating-u64 cast used by `ticks_to_ns` and `ns_to_ticks` in one place, consistent with the module's own stated goal.

### Cross-cut: unsafe audit

- **Polish** — Codify the `offset_of!` pinning pattern (Track B.2-5) as a standing unsafe-policy rule, a companion to the existing S5a naked-fn rule, so it automatically covers the next trap-frame-shaped struct Phase C's SMP/preemption work introduces.
- **Polish** — Automate the audit-tag-to-source cross-reference the quarterly review currently does by hand — this pass found 33 of 33 tags matching bidirectionally, a genuinely strong result worth locking in mechanically as the ~250-site unsafe surface grows through Phase C.
- **Polish** — Extend the release-mode fail-closed degrade pattern uniformly within `add_user_task` (see Track B.2-5's related finding) — consistency of security posture across a single function's parameters is itself a readability and audit win.

---

## Closing note on ADRs

Introducing Phase B.2 is itself a **structural change to the roadmap** — inserting a phase between B and C — and therefore requires a governing ADR per [ADR-0013](../../decisions/0013-roadmap-and-planning.md) and the roadmap change-process (see [roadmap/README.md §"Changing the roadmap"](../../roadmap/README.md#changing-the-roadmap): "Adding or dropping a phase… requires an ADR that supersedes the affected statements"). That ADR — recording the decision to add a consolidation-bridge phase and superseding the phase-index statements it affects — is a **prerequisite for this phase**, tracked as a named-but-unallocated ADR placeholder (in the style of ADR-0034) until it is written via the [`write-adr`](../../../.agents/skills/write-adr/SKILL.md) skill and linked here.

Beyond that structural ADR, the track work above changes no *other* Accepted architectural decision — every item is a documentation correction, a CI wiring change, or a code fix. If, in the course of executing a track, a fix turns out to imply an additional design decision — for example, choosing between the two `MappingFlags::DEVICE` remediation options in Track B.2-3, or deciding to add a scheduled (rather than PR-gated) perf-regression CI job in Track B.2-1 — write it up and route it through the same ADR governance rather than deciding it silently inside this phase's backlog.

Covers all 141 review findings + 71 polish items routed to this phase.
