# 0040 — Phase B.2 consolidation bridge: governance, gating, and exit criteria

- **Status:** Proposed
- **Date:** 2026-10-11
- **Deciders:** @cemililik

## Context

Phase B closed on 2026-06-01 and the roadmap declared Phase C (multi-core) active. On 2026-07-15 a full-repository review of the Phase B/C boundary produced a large backlog of defects, CI gaps and documentation drift. PR #46 (merged 2026-07-16) routed that backlog into the roadmap, and in doing so added a new bridge phase, **Phase B.2 — Consolidation & Hardening** ([`phase-b2.md`](../roadmap/phases/phase-b2.md)), between Phase B and Phase C.

Adding a phase is a structural roadmap change. [ADR-0013](0013-roadmap-and-planning.md) §"Changing the roadmap" and [`docs/roadmap/README.md`](../roadmap/README.md) require an ADR that supersedes the affected statements. PR #46 did not provide one: at that time, `phase-b2.md`'s closing note recorded the ADR as "a named-but-unallocated placeholder", but the ADR index's *Numbering gaps* note registered no such slot, so the requirement was not tracked anywhere an ADR reader would look. In the same change the roadmap became internally inconsistent about the phase's force: `phases/README.md` called B.2 "Recommended before Phase C", its dependency graph drew `B2 --> C` and `B2 --> D` as hard edges, and `phase-b2.md` named items that gate specific Phase C acceptance criteria (C1 `-smp 4` smoke, C3 `Cpu::without_interrupts`, C2 per-core pointers, C5 TLB shootdown). Separately, `current.md` still named Phase C as the active phase although no Phase C milestone, task or ADR existed.

At the decision baseline `8d6fab5` (2026-10-11), no code had changed since 2026-06-01 (the last commit touching `kernel/`, `hal/`, `bsp-qemu-virt/`, `test-hal/` or `userland/` is dated 2026-06-01); the only work after Phase B was documentation. On 2026-10-11 the project's own gates were executed for the first time on the maintainer's machine (Apple Silicon, `nightly-2026-01-15`): `cargo fmt --check`, `cargo host-clippy`, `cargo kernel-clippy`, 366 debug host tests (also under stable), and 356 release host tests including the two release-only `console_write` debug-gate tests, Miri on `tyrne-hal`/`tyrne-kernel`/`tyrne-test-hal` with no UB, `tools/smoke.sh --int` (full boot to EL0 `hello` and IPC round trip), and `cargo llvm-cov` at 96.31 % regions / 95.87 % lines all passed. Two things did not: CI's exact Miri command (`cargo miri test --workspace --exclude tyrne-bsp-qemu-virt`) fails on an arm64 host with `error[E0152]: found duplicate lang item panic_impl`, because the userland crates gate bare-metal code on `target_arch` alone ([T-037](../analysis/tasks/phase-b2/T-037-userland-bare-metal-cfg-gate.md)); and CI never runs `tools/smoke.sh` or the `--release` profile at all. The observed single-core baseline passes these checks; this does not establish Rust soundness or exclude the known latent defects, including T-038's asm clobber, that this phase must resolve before concurrency makes them costlier.

The maintainer has chosen to run the whole phase before Phase C. This ADR records that decision, supplies the missing governance, and settles the ambiguities above.

At kickoff, while this ADR was `Proposed`, the `Active` phase label identified the selected roadmap focus and `Ready` task labels identified prepared task scopes. Neither label authorised implementation: Acceptance was a phase-level precondition under the task index, and no task could start before it.

## Decision drivers

- **Security-first, memory-safety-through-Rust** (CLAUDE.md rules 1–2): a register-clobber UB in the EL0 syscall shim and a never-exercised release-profile security gate sit on the project's most attacker-reachable boundary.
- **Process integrity:** ADR-0013 requires an ADR for a structural roadmap change; a phase that exists in the plan without one weakens every other planning rule.
- **One unambiguous status:** a returning maintainer (or agent) must read one answer to "what is active, and what gates what".
- **Concurrency amplifies debt:** Phase C touches the same files (`pmm.rs`, `sched/mod.rs`, `user_access.rs`, the BSP) and adds a dimension in which latent defects stop being latent.
- **Verification honesty:** the source review was static analysis; only the project's own gates, run on the real tree, are evidence.
- **Pace** (CLAUDE.md rule 6): methodical, phased, reviewable — but planning without execution (132 days without a code change at decision time) is itself a risk.
- **Stable identifiers:** ADR-0013 makes phase letters stable once published; inserting a lettered phase would renumber every later phase.

## Considered options

1. **Option A — Full Phase B.2 as a mandatory gate before Phase C.** All six tracks are in scope; Phase C does not open until the B.2 exit bar is met.
2. **Option B — Narrow Phase B.2.** Only the blocking core (CI gates, correctness fixes, the high-severity documentation items) gates Phase C; the rest becomes a rolling backlog run alongside Phase C.
3. **Option C — Minimum fixes, then Phase C.** A handful of small fixes and one smoke CI job, B.2 formally deferred.
4. **Option D — Fold the work into Phase C's milestones.** No bridge phase; each item is attached to the Phase C milestone it gates.
5. **Option E — Keep the status quo.** B.2 stays "recommended", Phase C stays "active", no ADR.

## Decision outcome

Chosen option: **Option A — Full Phase B.2 as a mandatory gate before Phase C.**

The decision drivers that dominate are *security-first on the EL0 boundary*, *one unambiguous status*, and *concurrency amplifies debt*. Option A is the only option that both closes every verification gap before concurrency work starts and leaves no half-gated ambiguity. The costs (delay, and gating on many low-severity items) are real and are addressed by the exit-bar definition and the checkpoint below rather than by narrowing the scope up front. The concrete rules:

1. **Structure and identifiers.** Phase B.2 sits between Phase B and Phase C. The dotted identifier `B.2` is a deliberate, narrow extension of ADR-0013's letters-only phase IDs: it avoids renumbering Phases C–J, which ADR-0013 declares stable. Its sub-units are **Tracks** `B.2-1`…`B.2-6` (not milestones, which would collide with `B0`–`B6`). Its phase file is `phase-b2.md`, and its task folder is [`docs/analysis/tasks/phase-b2/`](../analysis/tasks/phase-b2/). Any future bridge phase follows the same pattern.
2. **Gate.** Phase B.2 is a **hard prerequisite** of Phase C and Phase D (the `B2 --> C` and `B2 --> D` edges of the dependency graph are binding). Phase D ports the same aarch64 kernel/HAL, MMU and syscall foundations to Pi 4; it directly needs the corrected contracts and verification gates rather than copying known defects into a second BSP. This deliberately applies the same whole-phase exit bar to D even if C and D overlap after B.2; it does not depend on C finishing first. While B.2 is open, no Phase C or Phase D milestone may open and no Phase C or Phase D implementation task may leave `Draft`. Planning artefacts for Phase C — scoping drafts, `Proposed` ADRs, the readiness sweep ([T-074](../analysis/tasks/phase-b2/T-074-phase-c-readiness-sweep.md)) — are allowed and encouraged so that Phase C starts without delay once B.2 closes. The two SMP-critical defects (`StaticCell`'s blanket `Sync`, the non-atomic PMM bitmap) remain Phase C entry gates and are *not* fixed in B.2; B.2 only corrects the false safety premise comment in `pmm.rs` ([T-042](../analysis/tasks/phase-b2/T-042-pmm-defensive-validation.md)).
3. **Scope and exit bar.** The exit bar is the acceptance criteria of Tracks B.2-1 to B.2-6 as written in `phase-b2.md`, including each track's own deferral clauses (low/info tails that are "tracked even if not all land"). Of the 141 plan items, 140 are owned by tasks T-030…T-073 (one of them, the `current.md` / T-029 staleness item, is split between T-047 and T-048) and one — the `phases/README.md` living-document note — was already fixed by the kickoff; the 71 polish items are **not** gating as a set and stay in `phase-b2.md` as an opportunistic backlog (a few are consumed by named tasks, as the task index records; those tasks are gating only for their plan items). Two tasks are polish and optional for exit — [T-036](../analysis/tasks/phase-b2/T-036-ci-arm64-host-check-job.md) and [T-056](../analysis/tasks/phase-b2/T-056-docs-consistency-automation.md) — and, if not completed, are recorded as carry-forwards in the closure review. A task whose acceptance criteria permit an explicit, evidenced "decide and defer" outcome can satisfy phase-exit accounting that way. Choosing implementation requires the task's remaining implementation and verification criteria; recording a "yes" decision alone does not complete it. Neither exit accounting nor an agent review authorises a `Done` promotion.
4. **Status of Phase C.** Phase C is reclassified from "active" to "**next, gated by Phase B.2**". The statements this ADR supersedes are: `phase-b.md` §Phase B closure ("Phase C is now active"), `docs/roadmap/current.md` (the *Active phase* bullet naming Phase C), the status paragraphs of `README.md` and `CLAUDE.md`, the "Recommended before Phase C" wording in `phases/README.md`, and the Phase C status targets in `phase-b2.md` Track B.2-2. Live targets are corrected and dated historical statements receive explicit supersession notes in the same change. When B.2 closes, Phase C becomes active again and the live pointers advance through the closure task ([T-075](../analysis/tasks/phase-b2/T-075-phase-b2-closure.md)); historical records remain preserved.
5. **Evidence and verification discipline.** `phase-b2.md` is self-contained: every item stands on its own `file:line` location. The source review is a local-only document and is **not** a dependency of any task. Because that review was static, **every B.2 task begins by re-verifying its item against the live tree**; an item that no longer reproduces closes with evidence and no code change. B.2 closure includes a verification report that accounts for all 141 items as *fixed*, *not reproduced*, or *deferred with a recorded reason*.
6. **Inherited process.** Tasks are opened with the [`start-task`](../../.agents/skills/start-task/SKILL.md) skill; every `unsafe` change follows [`justify-unsafe`](../../.agents/skills/justify-unsafe/SKILL.md) and the append-only audit-log discipline; changes that touch capabilities, IPC, syscalls, memory or `unsafe` get a security review per [`security-review.md`](../standards/security-review.md); a design decision surfaced by a task is routed through an ADR or a revision-note rider rather than decided silently (as `phase-b2.md`'s closing note already requires). Closure follows ADR-0013 (business review) and additionally includes a security review of B.2's `unsafe`/asm/capability changes and a regression check (host tests, Miri, `tools/smoke.sh --int`, release build).
7. **ADR numbering.** This ADR takes **0040**, the next free number after 0039, as the [`write-adr`](../../.agents/skills/write-adr/SKILL.md) skill prescribes. The phase ledgers in `phase-c.md`…`phase-i.md` assign *tentative* numbers starting at 0040 ("final numbers are assigned when the ADR is actually written"); those placeholders now shift and already collide between Phases C and D. Phase E's current ledger is 0047–0052; its historical "was ADR-0040/0041/0042" notes are not current slots. They are ordinal placeholders only, and re-sequencing them, including the downstream E–I cascade, is [T-054](../analysis/tasks/phase-b2/T-054-adr-ledger-renumbering-cascade.md). A written ADR's number never changes.
8. **Scope checkpoint.** After the CI gates and the HIGH-severity correctness tasks are done (the waves described in the [task index](../analysis/tasks/phase-b2/README.md)), the maintainer reassesses the remaining scope. Narrowing it to Option B changes this decision outcome and requires a new superseding ADR; a revision note cannot reverse an Accepted decision. Deferrals already permitted by the exit criteria are recorded with evidence and do not change the outcome.

### Track B.2-1 implementation policy

The first implementation wave uses the choices recorded below for [T-035](../analysis/tasks/phase-b2/T-035-ci-hygiene-tail.md) and [T-036](../analysis/tasks/phase-b2/T-036-ci-arm64-host-check-job.md). They take effect upon maintainer Acceptance of this ADR; a proposal alone authorises no implementation or live repository-setting change.

This wave also includes release kernel clippy and both debug/release QEMU smoke in T-030/T-034. The existing hello program ignores a rejected console call and exits, so debug can require its greeting while release forbids that greeting; both must demonstrate task exit/completion without panic or CPU fault. No userland or syscall-gate mechanism change is needed to establish those runtime checks.

1. **Performance reporting — weekly and on demand, informational.** Implement T-035 with a separate workflow scheduled weekly at `03:17 UTC` on Monday, plus `workflow_dispatch`. Also run it on pushes to `development` that change this workflow or `tools/perf-harness.sh`, so the job and its downloadable report can be verified before default-branch registration. Build the debug userland and kernel with the pinned nightly, run `tools/perf-harness.sh --iterations=20 --report=ci-nightly`, and archive the report with the commit SHA, toolchain and QEMU version. A failed measurement is a visible failed workflow; timing changes do not block merges. There is no calibrated regression threshold today, and QEMU TCG measurements vary with the runner. This wave adds recurring evidence without pretending it proves a performance-regression bound.
2. **Merge policy — version the existing classic branch protection.** On 2026-10-11, read-only inspection of `HodeTech/Tyrne` found no repository rulesets (`GET /repos/HodeTech/Tyrne/rulesets` returned `[]`); `main` instead has classic branch protection with four required GitHub Actions checks, strict up-to-date checking, required linear history and conversation resolution, and disabled force pushes and deletion. Implement T-035 with a committed JSON definition of that existing policy and documented read-only export/check commands plus an explicit maintainer-side apply command. Preserve every existing setting, including the check-source application binding; add the smoke and ARM checks only after they have succeeded remotely. Do not introduce Terraform, migrate protection mechanisms, grant a CI job administrative credentials, or remove an existing required check. An unexpected live-policy change must stop application for reconciliation rather than be overwritten silently.
3. **ARM host verification — a required PR check.** Include T-036 in this requested Track B.2-1 implementation, although it remains optional for the phase-wide exit bar. Use the explicit GitHub-hosted `ubuntu-24.04-arm` runner and pinned nightly; run workspace `cargo check`, `cargo clippy --all-targets -- -D warnings`, `cargo test` and `cargo miri test`, each excluding only `tyrne-bsp-qemu-virt`. Native tests exercise host linking; Miri also reproduces the command that originally exposed the target-gating bug. The public repository can use this standard ARM runner without a paid-runner commitment ([GitHub runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)). Install T-037 first, isolate caches by runner architecture, and make the ARM job required after its first remote green run.
4. **Execution and evidence — one branch, reviewed steps.** Follow the maintainer's requested `development`-only workflow: implement and commit one step, complete two rounds with fresh independent reviewers, fix and commit confirmed findings, then continue automatically. A dependent task may start when its predecessor is implemented and its applicable gates and both review rounds pass on this branch; the predecessor remains `In Review` until the maintainer reviews and merges the final PR. This is the explicit stacked-execution exception to the usual dependency-`Done` rule, limited to this Track B.2-1 sequence and its T-037 prerequisite. No task is promoted to `Done` by an agent. Run negative experiments in isolated temporary copies and, where hosted evidence is required, in isolated runner workspaces; do not create scratch branches or commit deliberately broken source. Distinguish a failing command inside an expected-failure probe from a red workflow. Record local evidence, hosted evidence, and post-merge evidence separately; a first `main` run or default-branch-only dispatch can only be certified after the maintainer's merge.

These choices are implemented by existing tasks; they allocate no new task or ADR identifiers. Substantive changes to the corresponding infrastructure standard follow this ADR's Acceptance, using [`propose-standard-change`](../../.agents/skills/propose-standard-change/SKILL.md). Routine implementation choices (flag spelling, aliases and equivalent command layout) are recorded in task history. A materially different merge policy or a real performance-regression threshold requires a further decision before implementation.

The policy alternatives considered alongside the phase-wide options above are:

| Choice | Selected option and cost | Credible alternatives and reason not selected |
|--------|--------------------------|------------------------------------------------|
| Performance cadence | Weekly/on-demand measurements, with targeted `development` validation; costs recurring runner time/storage. | Every-PR measurements give earlier data but no calibrated regression verdict; deferral saves cost but leaves the existing measurement gap open. |
| Protection representation | JSON for existing classic protection; requires careful response/payload normalisation and drift handling. | A repository-ruleset migration offers modern policy composition but adds migration/overlap risk unrelated to this gap; Terraform offers managed state but adds tooling, state and credential operations to a repository that has none today. |
| ARM enforcement | Required native check/clippy/test plus Miri; adds an ARM runner to the PR critical path. | Periodic-only verification reduces PR cost but detects the demonstrated host regression after merge; native-only verification is faster but omits the exact Miri path that exposed it. |
| ARM runner | Explicit Ubuntu ARM image; does not exercise macOS-specific tooling. | An ARM macOS runner matches the maintainer's OS but has a different tool environment from Linux CI; local Apple-Silicon checks complement the Linux job without adding a second ARM matrix axis now. |

### Simulation

Not applicable — this ADR settles a governance and sequencing decision; there is no state machine to simulate.

### Dependency chain

For this decision to be fully in effect:

1. ADR-0040 `Accepted` by the maintainer after the careful re-read of the [`write-adr`](../../.agents/skills/write-adr/SKILL.md) skill (step 10).
2. The 46 task files exist and are indexed — [T-030](../analysis/tasks/phase-b2/T-030-ci-release-profile-gate.md) through [T-075](../analysis/tasks/phase-b2/T-075-phase-b2-closure.md) in [`docs/analysis/tasks/phase-b2/`](../analysis/tasks/phase-b2/) (opened in the same change as this ADR).
3. Roadmap pointers reflect the decision: the new *Active phase* statement in `current.md`, the gating wording in `phases/README.md` and `phase-b2.md`, the dotted-ID convention in `roadmap/README.md`, the supersession notes in `phase-b.md` and `phase-c.md`, and the status paragraphs of `README.md` and `CLAUDE.md` (same change as this ADR).
4. Remaining roadmap drift is cleaned up — [T-047](../analysis/tasks/phase-b2/T-047-roadmap-state-and-phase-index-sync.md).
5. Planned ADR numbers are re-sequenced — [T-054](../analysis/tasks/phase-b2/T-054-adr-ledger-renumbering-cascade.md).
6. Phase C is prepared for a zero-delay start — [T-074](../analysis/tasks/phase-b2/T-074-phase-c-readiness-sweep.md).
7. Phase B.2 is closed and the pointers are restored — [T-075](../analysis/tasks/phase-b2/T-075-phase-b2-closure.md).

Steps 4–7 close under their own tasks; this ADR is *in effect* from step 3 and *fully realised* at step 7.

## Consequences

### Positive

- Phase B.2 becomes a legitimate phase under the project's own rules; the "recommended or gating?" ambiguity is gone.
- CI will enforce what the standards documents already claim: `--release`, userland clippy, panic-family denies in `hal`/`bsp`, and above all a merge-gating QEMU smoke job.
- The maintainer's own machine regains a working Miri gate (T-037); when the optional T-036 is taken, an arm64 host check catches the same class of error before merge. T-036 is included in the first Track B.2-1 implementation wave defined above.
- A latent Rust `asm!` UB in the EL0 syscall shim (T-038) and an unbounded spin under masked interrupts (T-039) are closed before Phase C's interrupt discipline depends on them.
- Documentation, task indices and the ADR ledger are brought back in step; the optional T-056 mechanises drift detection if taken, otherwise closure records its carry-forward explicitly.
- Phase C starts on a base whose gates are real, with its entry gates already scoped (T-074).

### Negative

- **Feature work is delayed** by 46 tasks, after a period of 132 days without code changes. *Accepted:* the checkpoint in rule 8 lets the maintainer narrow the scope on evidence, and the waves lead with code and CI rather than documents so that the phase does not repeat the plan-outruns-execution pattern.
- **Gating on low-severity items has low marginal safety value:** only 18 of the 141 findings are HIGH. *Mitigation:* the exit bar inherits each track's deferral clauses, polish is non-gating as a set, and an evidenced deferral satisfies exit accounting only where the task permits it; a chosen implementation must meet its implementation and verification criteria.
- **The dotted identifier `B.2` is an exception** to ADR-0013's letter-only phases. *Accepted:* it is the only way to insert a phase without renumbering stable identifiers; the exception is recorded here and in the roadmap README.
- **Task overhead:** 46 tasks require individual scope, review evidence and status updates. *Mitigation:* the maintainer may group tasks on one branch and PR; the first Track B.2-1 wave uses the reviewed-step convention above.
- **Additional CI and administration cost:** ARM Miri adds a second interpretation run and can lengthen the PR critical path; weekly performance reports consume runner time and artifact storage; the branch-protection definition requires drift checks and deliberate application. *Accepted:* the ARM-host regression is verified, measurements stay off the PR gate, and administrative application remains a local, reviewed operation with no privileged CI token. Hosted timings and artifact retention are recorded during implementation; a runner outage is investigated rather than silently downgrading a required check.
- **Planned ADR numbers shift** (T-054), invalidating tentative numbers quoted in older reviews and banners. *Accepted:* those numbers were explicitly tentative.

### Neutral

- The live phase pointers advance when B.2 closes; dated historical statements and their supersession notes remain preserved.
- Phase D has a direct B.2 prerequisite for the shared aarch64 foundations and verification gates; C/D overlap after B.2 does not relax that prerequisite.
- Items the review routed to Phases D, E, G and H are unaffected.

## Pros and cons of the options

### Option A — Full B.2 as a mandatory gate (chosen)

- Pro: closes every verification gap and the documentation drift before concurrency work begins.
- Pro: unambiguous; one status, one exit bar; no half-gated items.
- Pro: the work is already fully specified in `phase-b2.md`, with locations.
- Con: the longest path back to feature work.
- Con: gates on ~123 non-HIGH items; mitigated by deferral clauses and the rule-8 checkpoint.

### Option B — Narrow B.2

- Pro: covers all 18 HIGH items and turns the verified gates into permanent merge gates in a shorter time.
- Pro: lower task overhead; faster return to Phase C.
- Con: requires a second decision about *which* items are blocking, and the boundary must be policed.
- Con: leaves medium/low drift and quality items open while Phase C changes the same files, making them costlier later.
- Not chosen: the maintainer preferred a single, complete gate; Option B remains reachable through the rule-8 checkpoint.

### Option C — Minimum fixes, then Phase C

- Pro: fastest return to features; fixes the Miri gate, the `x2` clobber, the false PMM comment and adds a smoke job in days.
- Con: leaves the governance gap open (B.2 must still be formally deferred, which itself needs an ADR) and the documentation drift in place, including `SECURITY.md`'s false statement about the shipped boundary.
- Con: Phase C's SMP work would proceed on a CI that still skips `--release` and userland clippy.

### Option D — Fold the work into Phase C milestones

- Pro: no new phase, no structural roadmap change, no dotted identifier.
- Con: the items are feature-independent; attaching them to C1–C5 hides them, mixes unrelated review concerns in Phase C PRs, and still leaves the 58 documentation findings with no natural home.
- Con: Phase C's own entry gates would then compete with this backlog for attention.

### Option E — Keep the status quo

- Pro: no further work on planning.
- Con: leaves a phase without its required ADR, a contradiction between "recommended" and a hard graph edge, and `current.md` naming a phase with no task as active.
- Con: it is the state that produced 132 days without a code change.

## References

- [ADR-0013 — Roadmap and planning process](0013-roadmap-and-planning.md) (§"Changing the roadmap"; a revision-note rider pointing here is added in the same change).
- [ADR-0025 — ADR governance amendments](0025-adr-governance-amendments.md) (Rule 1: forward-references grounded in real tasks).
- [`docs/roadmap/phases/phase-b2.md`](../roadmap/phases/phase-b2.md) — the plan this ADR governs.
- [`docs/roadmap/README.md`](../roadmap/README.md) §"Changing the roadmap".
- [`docs/analysis/tasks/phase-b2/README.md`](../analysis/tasks/phase-b2/README.md) — the task index and recommended order.
- [`docs/roadmap/phases/phase-c.md`](../roadmap/phases/phase-c.md) §"Review-derived work items" — the two SMP-critical entry gates that remain in Phase C.
