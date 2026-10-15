# Business review 2026-10-12 — Phase B.2 Track B.2-1 completion

Track B.2-1 is Done after the maintainer merged PR48, authorized the eight task promotions and the remaining first-main/dispatch acceptance evidence passed.
This review records deliveries, lessons and the remaining Phase B.2 work; it closes neither the phase nor any other track.

- **Trigger:** maintainer-initiated, following Track B.2-1 completion; bridge tracks are distinct from numbered milestones.
- **Scope:** Track B.2-1, including optional T-036 and sole cross-track prerequisite T-037; PR48 follow-ups A/B and post-merge evidence.
- **Period:** 2026-10-11 approved kickoff (`960bdef`) → 2026-10-12 merge and verification (`c16997e`). This is the first business review of this track; the prior [Phase B retrospective](2026-06-01-phase-b-closure.md) was read for context and remains historical.
- **Participants:** @cemililik (review, merge and explicit Done authorization); Codex as scribe, executing all five business-review roles sequentially. A separate agent supplies a bounded bookkeeping check, not a new promotion/code/security verdict.

## What landed

**Commits:** The reviewed development tip is `f2758e3808c0c47b105ad3e13417dbe789cefff7`; the maintainer merged [PR48](https://github.com/HodeTech/Tyrne/pull/48) at `c16997e003fbd1726d1205734380394781c52002`, 2026-10-12 07:24:09 UTC.
The complete approved-implementation history below retains individual source/evidence identities rather than relabeling every review as the squash commit.
Task associations come from task IDs in subjects, task files changed by the commit or the original step ownership; an unassigned row advances integration/governance or shared evidence.

<details>
<summary>All 47 commits in 960bdef^..f2758e3, oldest first</summary>

- `9e17d04` (2026-10-11) — docs(roadmap): make Phase B.2 a mandatory gate before Phase C (ADR-0040) and open its 46 tasks (#47); T-030, T-031, T-032, T-033, T-034, T-035, T-036, T-037, T-038, T-039, T-040, T-041, T-042, T-043, T-044, T-045, T-046, T-047, T-048, T-049, T-050, T-051, T-052, T-053, T-054, T-055, T-056, T-057, T-058, T-059, T-060, T-061, T-062, T-063, T-064, T-065, T-066, T-067, T-068, T-069, T-070, T-071, T-072, T-073, T-074, T-075.
- `960bdef` (2026-10-11) — docs(adr): accept ADR-0040 and Track B.2-1 policy; T-035, T-036.
- `f2d577f` (2026-10-11) — fix(userspace): restrict syscall shims to bare metal; T-037.
- `69a4109` (2026-10-12) — docs(userspace): reconcile T-037 review records; T-037.
- `3a7c264` (2026-10-12) — docs(userspace): record second T-037 review round; T-037.
- `54e8f77` (2026-10-12) — feat(tooling): validate QEMU core count and timeout arguments; T-033.
- `d5c13a0` (2026-10-12) — docs(tooling): record T-033 implementation gates; T-033.
- `eede01c` (2026-10-12) — docs(tooling): record first T-033 review round; T-033.
- `05f1736` (2026-10-12) — docs(tooling): correct completion state after T-033 review; T-033.
- `82d1c42` (2026-10-12) — ci: lint userland and tooling scripts; T-031.
- `1cb3526` (2026-10-12) — docs(standards): enforce userland and shell lint gates; T-031.
- `0acf0cd` (2026-10-12) — fix(ci): support hosted ShellCheck trap analysis; T-031.
- `e79e10a` (2026-10-12) — docs(standards): reconcile first T-031 review findings; T-031.
- `8437158` (2026-10-12) — docs(analysis): complete second T-031 review round; T-031.
- `b8ad56f` (2026-10-12) — ci: enforce release and perf build contracts; T-030.
- `c716ae3` (2026-10-12) — docs(standards): enforce release and perf verification gates; T-030.
- `364b746` (2026-10-12) — docs(analysis): record hosted T-030 gate evidence; T-030.
- `5cd9ee8` (2026-10-12) — docs(analysis): record first T-030 review round; T-030.
- `8591ceb` (2026-10-12) — docs(analysis): complete second T-030 review round; T-030.
- `c3f32c8` (2026-10-12) — fix(bsp-qemu-virt): enforce panic-family lint boundaries; T-032.
- `b6572cc` (2026-10-12) — docs(analysis): reconcile T-032 audit and evidence state; T-032.
- `4f2c38c` (2026-10-12) — docs(analysis): record hosted T-032 gate evidence; T-032.
- `6e191e2` (2026-10-12) — docs(analysis): record first T-032 review round; T-032.
- `07449f1` (2026-10-12) — docs(analysis): record second T-032 review round; T-032.
- `6450005` (2026-10-12) — ci: gate debug and release EL0 smoke under QEMU; T-034.
- `41d9682` (2026-10-12) — docs(analysis): record hosted T-034 guest proof; T-034.
- `97a6c83` (2026-10-12) — fix(ci): preserve QEMU smoke failures through logging; T-034.
- `9092581` (2026-10-12) — docs(analysis): verify hosted T-034 pipeline correction; T-034.
- `0c86c3d` (2026-10-12) — docs(analysis): record second T-034 review round; T-034.
- `9c5191c` (2026-10-12) — docs(ci): record required QEMU check registration; T-034.
- `bf20ec9` (2026-10-12) — ci: require native ARM64 workspace checks and Miri; T-036.
- `5c95cd3` (2026-10-12) — docs(analysis): record first T-036 review and ARM evidence; T-036.
- `2d4d21e` (2026-10-12) — docs(analysis): record second T-036 review round; T-036.
- `69ac515` (2026-10-12) — docs(ci): record required native ARM check registration; T-036.
- `e873995` (2026-10-12) — ci: add weekly performance reports and versioned merge policy; T-035, T-036.
- `7deb16e` (2026-10-12) — fix(ci): accept both proven ARM cfg rejection diagnostics; T-035, T-036.
- `cfc8872` (2026-10-12) — chore(ci): reconcile merged kickoff ancestry; shared integration/governance or evidence.
- `67f8c9b` (2026-10-12) — docs(analysis): record final Track B.2-1 review round; T-035, T-036.
- `bd27fe5` (2026-10-12) — docs(roadmap): reconcile Track B.2-1 implementation status; shared integration/governance or evidence.
- `acd0013` (2026-10-12) — docs(roadmap): reconcile final Track B.2-1 documentation; shared integration/governance or evidence.
- `1e281ac` (2026-10-12) — docs(roadmap): record green Track B.2-1 PR evidence; T-034, T-035, T-036.
- `50ab72b` (2026-10-12) — fix(ci): strengthen PR review probes and report metadata; T-034, T-035, T-036.
- `683965b` (2026-10-12) — docs(analysis): record PR48 tooling review and correction; T-034, T-035, T-036.
- `a1eb406` (2026-10-12) — docs(analysis): record fresh PR48 tooling round two; T-034, T-035, T-036.
- `5816c93` (2026-10-12) — docs(ci): reconcile PR48 review claims and current guidance; T-034, T-035.
- `646ba33` (2026-10-12) — docs(analysis): correct PR48 review wording and record round one; T-035.
- `f2758e3` (2026-10-12) — docs(analysis): publish PR48 follow-up completion and hosted evidence; T-035.

</details>

The post-merge development ancestry commit `0613f9b67cfc03b9c0b8d477740e2f915da29c4c` records the squash without changing the tree or switching branches.
This prevents subsequent development PRs from replaying the already merged implementation.

**ADRs:**

- [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md), *Phase B.2 consolidation bridge*, Accepted by the maintainer on 2026-10-11 before implementation. Its existing CI/ARM/performance/classic-protection decisions govern this work; no new decision is introduced by completion bookkeeping. Accepted-body SHA-256 remains `5b82f632157033d193e64ac554390bacb9944fcd7a79fac9760a666c5f02ff2c`.

**Tasks closed (all date_done 2026-10-12):**

- [T-037](../../tasks/phase-b2/T-037-userland-bare-metal-cfg-gate.md): architecture-plus-target-OS gates restore native ARM workspace/Miri and preserve the recorded initial bare-metal image.
- [T-033](../../tasks/phase-b2/T-033-qemu-tooling-smp-and-timeout.md): validated SMP overrides, precedence and missing-value handling; 59 controlled cases, without implementing SMP.
- [T-031](../../tasks/phase-b2/T-031-ci-userland-clippy-and-shellcheck.md): bare-metal userland clippy and ShellCheck with isolated rejection controls.
- [T-030](../../tasks/phase-b2/T-030-ci-release-profile-gate.md): release build/lint/host tests, both named release-only syscall guards and debug perf-bench build/lint.
- [T-032](../../tasks/phase-b2/T-032-panic-family-denies-hal-bsp.md): HAL/BSP panic-family denies, scoped justified boot exceptions and reviewed unmap audit amendment.
- [T-034](../../tasks/phase-b2/T-034-ci-qemu-smoke-job.md): required real debug/release EL0 smoke, fault/profile checks, failure-preserving log pipelines and downloadable diagnostics.
- [T-036](../../tasks/phase-b2/T-036-ci-arm64-host-check-job.md): required native Linux ARM check/clippy/test/Miri, isolated regression rejection and architecture-separated caches; optional for the phase exit but delivered here.
- [T-035](../../tasks/phase-b2/T-035-ci-hygiene-tail.md): weekly/on-demand informational 20-run reporting and complete classic-main protection JSON with fail-closed export/check/local apply; default-branch dispatch criterion now complete.

Each implementation step completed two fresh independent rounds; security-sensitive steps received distinct security review.
Both supplied-review follow-up steps also completed two fresh rounds, with their second rounds reporting zero new findings and verifying first-round corrections.
The [implementation/review map](../../../roadmap/phases/phase-b2.md#implementation-status-2026-10-12) and [17-item reconciliation](../../reports/2026-10-12-pr-48-supplied-review-reconciliation.md) retain full reports, verified fixes, qualified claims and exact-source limits.
Done promotion rests on the maintainer's merge and explicit instruction, with acceptance evidence checked below; this retrospective is not an independent approval review.

### Post-merge evidence

| Evidence | Observed result |
|----------|-----------------|
| [First main CI 38217531542](https://github.com/HodeTech/Tyrne/actions/runs/38217531542) | Push event, full merged `c16997e003fbd1726d1205734380394781c52002`, all seven jobs success |
| [Native ARM job 114705667835](https://github.com/HodeTech/Tyrne/actions/runs/38217531542/job/114705667835) | Check/clippy/test/Miri pass, 101 s job; native/Miri each 366 pass, two ignored HAL doctests; clean control passes, private arch-only probe rejected with exit 101/E0152 |
| Downloaded smoke evidence | Clean tracked source `c16997e`, correct production debug/release traces; 23/23 controls (20 synthetic, three actual private kernels); 119 s evidence interval |
| [Main performance dispatch 38217799773](https://github.com/HodeTech/Tyrne/actions/runs/38217799773) | Actual workflow_dispatch on clean full merged main source, registered active workflow; 20 requested/20 valid/0 failed, 101 s harness/132 s evidence |
| [Exact-byte main report](../../reports/perf-baseline-2026-10-12-t035-main-dispatch-check.md) | Raw nearest-rank p10/p50/p90 = 8,470,496 / 9,079,824 / 10,252,512 ns; p99 = max = 12,763,984 ns at n=20; file SHA-256 `de2f838bfdd4b6bb2b1ec4c4a22fcdd630c2d24dac5d8eb3323daa588f4b0974` |
| Full live protection read-back | Read-only check matches committed definition: six exact required names bound to Actions app 15368, strict checking; all other policy values preserved |

The coordinator retrieved the run summaries, downloaded artifacts, read the complete production traces/performance report and recomputed report arithmetic/digests.
These are actual hosted executions and locally inspected downloads, not a new local Rust/QEMU/Miri rerun.
This documentation-only update needs link/status/preservation checks; source and workflow behavior are unchanged.
Performance artifact 11732776508 is 4,183 bytes, expires 2026-10-26; archive SHA-256 `599dbded6a4d138f5986cd7270382248db052179fd00c736e9e3591b0cf03b95` is service-reported, not locally recomputed.
Smoke artifact 11733175759 is 24,124 bytes; archive SHA-256 `7488747dda638ebea5906b33995d9ee9c6358b8973ef9ea1b3d816460dedaa22` is likewise service-reported.
The exact report file is retained in Git independently of artifact expiry; earlier measurement snapshots remain byte-identical.
The live policy still permits administrator bypass and requires zero approvals; producer app identity does not certify workflow body integrity.
Performance and coverage remain informational. No timing band here proves a cross-host regression or calibrated tail reliability.
Weekly Monday 03:17 UTC reporting is configured and active; this evidence verifies manual dispatch, not execution of a future cron tick.

### Captured production QEMU traces

These are verbatim complete downloaded production traces from the first merged-main run, including completion, boot-to-end timing and expected watchdog termination.
The smoke command uses `-d int,unimp`, which records exactly two SVC exception events in each profile and no other exception event in these traces.
`guest_errors` is not enabled by this command, so no guest_errors count is claimed.
Debug source-trace SHA-256 is `94091361df6cb9d3983d99d52f48cac254e6d386f92510582ec2dce881d4994f`; release is `225f6778bf249db1f3e12411f3cb7b74378f8ece34cec6272a8e0af28b6b0acf`.
The debug greeting is present; release correctly lacks it while completing the userspace task and IPC demo.

Debug:

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
...with ELR 0x800034
...to EL1 PC 0xffffffff40080c00 PSTATE 0x3c5
hello from userspace
Exception return from AArch64 EL1 to AArch64 EL0 PC 0x800034
Taking exception 2 [SVC] on CPU 0
...from EL0 to EL1
...with ESR 0x15/0x56000000
...with ELR 0x80005c
...to EL1 PC 0xffffffff40080c00 PSTATE 0x3c5
tyrne: userspace task exited
tyrne: task B — received IPC (label=0xaaaa); replying
tyrne: task A — received reply (label=0xbbbb); done
tyrne: all tasks complete
tyrne: boot-to-end elapsed = 15449264 ns
qemu-system-aarch64: terminating on signal 15 from pid 4052 (timeout)
```

Release:

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
...with ELR 0x800020
...to EL1 PC 0xffffffff40080c00 PSTATE 0x3c5
Exception return from AArch64 EL1 to AArch64 EL0 PC 0x800020
Taking exception 2 [SVC] on CPU 0
...from EL0 to EL1
...with ESR 0x15/0x56000000
...with ELR 0x80002c
...to EL1 PC 0xffffffff40080c00 PSTATE 0x3c5
tyrne: userspace task exited
tyrne: task B — received IPC (label=0xaaaa); replying
tyrne: task A — received reply (label=0xbbbb); done
tyrne: all tasks complete
tyrne: boot-to-end elapsed = 4856160 ns
qemu-system-aarch64: terminating on signal 15 from pid 4183 (timeout)
```

## What changed in the plan

- The Accepted full-Phase-B.2 scope and C/D gates remain intact. The approved execution order included cross-track T-037 first and optional T-036; it did not complete the rest of Track B.2-3.
- The twelve Track B.2-1 opening findings are delivered through the task map. Release kernel clippy and real release EL0 smoke were included before implementation; the original baseline remains historical.
- All eight task headers now say Done with date_done, and current roadmap/index pointers supersede pre-merge In Review and pending-main/dispatch states. Existing review verdicts, unsuccessful evidence and exact-byte captures keep their original identities.
- No new task, ADR, dependency, security policy or runtime behavior is introduced by this update. The complete phase still has 38 tasks outstanding.
- ADR-0040's full scope checkpoint follows CI and HIGH-correctness work; completion of this CI wave alone does not satisfy that checkpoint. A switch to the narrower scope would still require a superseding ADR.

## What we learned

A negative probe must distinguish the intended regression from an already-broken baseline.
The ARM assertion now runs the identical command on clean private source before six cfg mutations, requires the observed exit/diagnostic contract and accepts both proven Cargo diagnostic classes.
Its real hosted race showed why an E0152-only assumption was too narrow even when the original defect was real.

Log capture is part of a gate's correctness.
The first smoke review found that a logging pipeline could mask rejection; explicit pipefail and a matching pipeline negative control make the actual workflow enforce the intended result.
Separate production traces, synthetic fixtures and private actual-kernel probes make the evidence interpretable.

Recorded source identity matters as much as a green badge.
Optional tool metadata can fail without invalidating valid timing samples, while required measurement failures remain errors.
Nearest-rank p99 changes rank at n=100 but that fact alone says nothing about statistical reliability; the generator and new main report say so explicitly.
Historical captured bytes remain preserved with a dated superseding interpretation, rather than silently rewriting measurements.
The prior Phase B retrospective's same-host comparison caution still applies.

Host tests, Miri and smoke are complementary signals, not a proof of every inline-assembly contract.
HIGH T-038 is still open: the userspace declaration treats x2 as input-only while the kernel overwrites it on syscall return.
Completing T-037 and the CI gates makes that focused fix ready and verifiable; it does not clear it by implication.

## Adjustments

- [ ] Pick up HIGH [T-038](../../tasks/phase-b2/T-038-console-write-x2-clobber.md) next, retaining its Ready state until implementation begins. Trigger: the next explicitly started development task. Its contract requires no new ADR, but does require the append-only UNSAFE-2026-0033 amendment, separate security review, userland lint/build/smoke and disassembly/image evidence.
- [ ] Then prioritize remaining small correctness fixes T-041–T-044 and high-visibility T-051 under the existing [recommended waves](../../tasks/phase-b2/README.md#recommended-order). Trigger: completion of the preceding task; this retrospective starts none of them.
- [ ] Prepare and obtain maintainer approval for recorded decisions before implementing decision-bearing T-039/T-040 and the other identified decision tasks. Trigger: their own preflight; do not use a status update to settle architectural choices.
- [ ] Complete the documentation, quality and unsafe-audit work before [T-074 readiness](../../tasks/phase-b2/T-074-phase-c-readiness-sweep.md) and [T-075 closure](../../tasks/phase-b2/T-075-phase-b2-closure.md). Trigger: their dependency/exit criteria. Preserve the full B.2 gate before C/D.

Remaining primary task ownership (shared documentation work in T-064 is counted once):

| Scope | Remaining tasks | Count |
|-------|-----------------|------:|
| B.2-2 documentation cascade | T-045–T-056 | 12 |
| B.2-3 correctness and robustness | T-038–T-044 | 7 |
| B.2-4 code quality and API design | T-057–T-068 | 12 |
| B.2-5 unsafe-audit and doc comments | T-069–T-072 | 4 |
| B.2-6 performance decisions | T-073 | 1 |
| Readiness and closure | T-074, T-075 | 2 |
| **Total** | **30 Ready, 8 Draft** | **38** |

Of the original 46 tasks, eight are Done. Of the 38 remaining, T-056 is optional polish and the other 37 retain their individual phase-exit criteria.
The existing full-scope decision and each task's permitted evidence-based deferral rules remain unchanged; no deferral is invented here.

## Next

- Active phase: B.2, still Active; Phase C and D remain gated.
- Active milestone: no numbered milestone is opened; Track B.2-1 is Done, correctness Track B.2-3 is the next recommended focus.
- Active task: none In Progress; T-038 is the next Ready candidate and has not started.
- Next review trigger: T-038 implementation and its required code/security rounds; the full scope checkpoint follows CI and HIGH-correctness work, with phase readiness/closure later at T-074/T-075.
