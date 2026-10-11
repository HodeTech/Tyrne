# Code review 2026-10-12 — T-032 panic-family denies

- **Change:** T-032 on `development`, `8591ceb..4f2c38c`.
- **Reviewers:** fresh independent `b21_step5_round1_code` (`gpt-6.1-sol` / high requested), paired with distinct `b21_step5_round1_security` (`gpt-6-astra` / high requested), acting on behalf of @cemililik. Reports distinguish orchestration configuration from runtime identity.
- **Risk class:** Security-sensitive boot/exception/MMU context and changed unsafe-call reasoning.
- **Security-review cross-reference:** [distinct security artifact](../security-reviews/2026-10-12-t032-panic-family-denies.md).

> **Current reconciliation:** Both fresh code/security rounds Approve with no new actionable finding. Changed UNSAFE-2026-0025 reasoning is explicitly approved in both rounds, with actual approval recorded append-only. Independent compiler mutations verify sibling and callee exception boundaries; historical audit bytes are preserved. Local/hosted implementation gates passed. Runtime BSP unmap, SMP and unchanged HIGH T-038 remain outside this scoped approval. Final maintainer PR review remains pending; T-032 stays In Review.

## Round 1 code review

- **Change:** approved Track B.2-1 step 5 on `development`, `8591ceb..4f2c38c6a8fdf221e00a0f0cb461303ed0b74b55`; implementation `c3f32c8`, audit/evidence reconciliation `b6572cc`, hosted evidence-only `4f2c38c`. Twelve files, 122 additions / 25 deletions.
- **Reviewer:** fresh independent delegated agent `/root/b21_step5_round1_code`, acting on behalf of @cemililik. Parent requested `gpt-6.1-sol`, high reasoning, `fork_turns=none`; these are orchestration settings, not an independently attested runtime model identity.
- **Date:** 2026-10-12, Europe/Istanbul; hosted timestamps cited here are UTC on 2026-10-11.
- **Risk class:** Security-sensitive: boot, exception handling and MMU call-site safety reasoning. No syscall implementation or assembly change.
- **Security-review cross-reference:** distinct fresh [Round 1 security report](../security-reviews/2026-10-12-t032-panic-family-denies.md), read in full after its completion: **Approve**, no new finding, explicit changed UNSAFE-2026-0025 reasoning approval. Canonical report was parent-saved and awaiting its recording commit at verdict time.
- **Procedure:** `perform-code-review`, `conduct-review`, complete code-review master plan and standard checklist. Five roles executed sequentially. The task and its actual negative-test harness were read before the executable diff; crate configuration and walker implementation before callers, workflow and evidence documentation. `justify-unsafe` was also read to check the changed reasoning against the unsafe standard. Parent explicitly owns canonical publication, index, task/history and trailer changes; this report writes only to `/tmp`.

### Correctness

**No actionable code finding.** The changes enforce the stated three-lint boundary without adding a runtime panic, changing a public API, widening authority, or changing existing fatal-fault behavior.

HAL and BSP have each of `deny(clippy::panic)`, `deny(clippy::unwrap_used)` and `deny(clippy::expect_used)` at the crate root. Existing workspace lint inheritance, warning enforcement and kernel denies are preserved. HAL receives no exception. The ten new exception groups were inspected together with their entire attached function bodies, including multiline attributes and feature selection:

| Functions | Lints allowed | Classification and evidence |
|---|---|---|
| `main::kernel_main_high` | expect, panic | One-shot trusted boot: static PMM/linker alignment, initially empty arenas/tables, loader/object setup and scheduler population before start |
| `perf_bench::run` | expect, panic | One-shot measurement setup: trusted static image, fixed capacities, task/cap construction and publish-before-start order |
| `main::idle_entry` | expect | Trusted scheduler invariant: yielding after start requires a current task; no init classification is falsely applied to its loop |
| `main::task_a`, `main::task_b` | expect, panic | Trusted one-round kernel demo with static capability tables and fixed rendezvous protocol; unchanged runtime behavior |
| `perf_bench::driver_yield` | expect | Trusted post-start current-task invariant |
| `perf_bench::driver_send`, `perf_bench::partner_recv` | expect | Statically provisioned narrow SEND/RECV capabilities and fixed benchmark ping-pong protocol |
| `exceptions::irq_entry` | panic | Existing unhandled-IRQ fatal abort after EOI; spurious/timer branches retain ordinary return |
| `exceptions::panic_entry` | panic | Existing deliberate fatal unhandled-exception policy; no added unwrap/expect allowance |

Every new allowance has `reason = ...` and is attached to a function. None is crate/module-wide. `syscall.rs` and MMU have none. The exceptions preserve the ADR/error-handling policy rather than introducing a new exception policy. The guide and task explicitly avoid claiming that three Clippy lints forbid assertions or establish a panic-free kernel. Existing non-SVC EL0 fatal behavior is unchanged and outside this scoped approval.

`QemuVirtMmu::unmap` still validates VA alignment, calls the same walker with the same root, VA, flags, null provider and literal `true`, then returns the descriptor-derived frame and `MapperFlush`. Only the unused third argument changes from constructing/unwrapping an aligned zero frame to copying `as_.root`. `PhysFrame` is a copyable aligned-address wrapper; passing it does not create another ownership token or dereference the frame. In `walk_and_install_leaf`, the `unmap` branch reads the L3 descriptor, checks validity, masks the output PA, clears the descriptor and returns that PA's typed frame. Every use of parameter `pa` occurs solely in the `else` map branch. Intermediate walking propagates `unmap` and neither allocates nor consumes the provider when true. The replacement therefore changes no descriptor, allocation, pointer computation, returned frame, error, or caller flush obligation.

**Reviewed the changed unsafe call and adjacent SAFETY reasoning in `bsp-qemu-virt/src/mmu.rs:306–334`; agree with the unchanged-root/unused-PA argument for literal `unmap = true`.** This code approval is scoped to that changed argument/reasoning, not a certification of every historical walker or SMP claim. The appended UNSAFE-2026-0025 amendment explicitly preserves that limitation and accurately states that the normal smoke does not exercise BSP unmap. The distinct security reviewer has separately approved that changed argument/reasoning, as recorded in the paired report.

The probe uses `black_box(None::<u64>).unwrap()` in non-test crate-root code outside allowed functions. `black_box` prevents the test from relying on an obviously constant None diagnostic; the required diagnostic is `clippy::unwrap_used`. `run_negative` requires nonzero command status and that specific diagnostic; command success or unrelated failure alone cannot pass. Exact aliases retain their target/package selection. The BSP builds its debug image before linting only inside the tracked-current-worktree copy. Each invocation replaces `CARGO_TARGET_DIR` with a private sibling directory, avoiding shared caches and image writes. The existing NUL-delimited copy loop and quoted paths preserve tracked names/modes. EXIT cleanup handles the tested normal/error exits.

### Style

**Clean.** Independent default-severity ShellCheck on the changed script and Bash syntax checks pass, as does range whitespace validation. The implementation uses existing Rust attribute forms and explicit scoped reasons; no broad suppression, dependency, toolchain, target flag or unrelated refactor appears. English prose and conventional commit subjects are maintained. All three range commits include `Refs: ADR-0040`; implementation and audit reconciliation include `Audit: UNSAFE-2026-0025`. The security trailer correctly awaits actual separate approval and parent-owned recording rather than being fabricated in advance.

### Test coverage

**Adequate for this enforcement change; no missing blocking test.** The new persistent probes exercise real compiler behavior, and the independent controls establish that they detect removal of the new enforcement. No new public API or Error variant requires another contract test. The MMU substitution is behavior-preserving; existing `cap_unmap_returns_unmapped_frame` asserts returned PA and both flushes, and loader rollback tests assert committed leaf-frame reclamation. Those run over a fake MMU, so they are complementary evidence rather than execution of this hardware walker.

Independent verification in this review:

| Check | Observed result |
|---|---|
| Actual `/bin/bash tools/test-ci-gates.sh --hal` in private tracked snapshot | Harness exit 0; real Clippy exit 101, `clippy::unwrap_used` |
| Actual `--bsp` in private tracked snapshot | Harness exit 0; private 117-byte debug image built, real Clippy exit 101 with intended lint |
| Remove only HAL unwrap deny in private snapshot, rerun exact harness | Harness exit 1; Cargo succeeds and script rejects the unexpected-green regression |
| Remove only BSP unwrap deny in private snapshot, rerun exact harness | Harness exit 1 with same unexpected-green diagnostic |
| Private probe-directory cleanup | Checked after all four cases; outer snapshot/targets also removed by `TemporaryDirectory` |
| Original HAL/BSP sources and existing hello image | SHA-256 unchanged before/after; outer copied tree never gained hello.bin |
| Changed script ShellCheck / `/bin/bash -n` / range whitespace | All exit 0 |
| Unsafe-log history preservation | Removing exactly the one new T-032 amendment yields byte-identical baseline log |
| Changed Markdown relative file destinations | 418 references resolve; heading anchors not checked |
| Reviewed tip and working tree | Exact `4f2c38c6a8fdf221e00a0f0cb461303ed0b74b55`, clean |

Captured independent real-case results: `/tmp/tyrne-b21-r1-code-verification.json`. The reviewer fixture's first outer snapshot had no Git metadata, so its nested tracked-copy command could not enumerate files and the fixture assertion failed. This was corrected by a private read-only `git ls-files` shim directed at the original repository; actual Cargo and repository probe logic were unchanged. The corrected four-case run passed. No failed check is counted as evidence and no repository fix was indicated.

Parent-supplied implementation evidence separately covers fmt, ShellCheck 0.11.0/actionlint, clean host/default/release/perf clippy and corresponding builds, 366 host and 366 Miri passes with existing warnings/two ignored HAL doctests, debug QEMU greeting/exit/completion/two expected SVCs/no faults, unchanged 117-byte SHA `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`, eleven controlled isolation/error/CLI cases and 59 QEMU argument fixtures. Those broad checks were not all repeated here. The review's real Cargo compilations and deny-removal controls directly cover the changed contract; a duplicate broad suite or guest smoke would add little for this behavior-preserving lint delta.

### Documentation

**No actionable finding.** The CI guide documents both exact probe commands, their isolated images/targets and the meaning of expected rejection. T-032 classifies every exception group and distinguishes the original baseline, local gates, hosted evidence and pending distinct review. Task, index and all three live current-focus pointers agree on In Review on development; no Done, merge or final-PR approval is inferred.

UNSAFE-2026-0025 gains one dated amendment identifying actual implementation SHA `c3f32c8`, operation, unchanged invariants, rejected unnecessary allowance and explicit runtime-verification limit. Independent byte comparison confirms all original entries and prior amendments remain intact. Existing historical SMP-forward claims are expressly excluded and retained under T-069 ownership. The audit's pending-security sentence is honest at the reviewed tip and requires append-only completion recording after approval. No standard or Accepted ADR body is rewritten; this implements existing error-handling discipline under Accepted ADR-0040, and T-052 retains standards-reality wording ownership. There is no new architectural or policy decision requiring a new ADR.

### Integration

**Clean for the delta.** Both new probe steps run after the corresponding positive lint in existing required jobs, without `continue-on-error`. Workflow job names, action pins, permissions, triggers and workspace membership are unchanged. The copied toolchain file selects the same nightly outside the original checkout's directory override. Debug/release/perf coverage is retained; BSP probe image construction occurs only in its own copy and cannot disturb the production debug → release → restored debug sequence.

Direct inspection of parent-downloaded `/tmp/tyrne-b21-step5/hosted-run.json` identifies completed success at exact executable/audit tip `b6572cc65857b99f3ac3661b99cea809a7b12e88` with all five jobs successful: [hosted run 38181326486](https://github.com/HodeTech/Tyrne/actions/runs/38181326486). Inspected supplied fast-lane line 202 records intended HAL rejection at exit 101; kernel lines 213–214 record the private 117-byte image and intended BSP rejection. Kernel lines 173/244/276 corroborate production image sizes 117 → 69 → restored 117; metadata records release and perf compilation/lint steps successful. Fast-lane summaries corroborate 366 debug and 356 release passes with the two ignored doctests excluded. The reviewer inspected these supplied files but did not independently fetch GitHub logs.

Parent additionally reports all five jobs green at exact docs-only reviewed tip `4f2c38c` in [run 38181458269](https://github.com/HodeTech/Tyrne/actions/runs/38181458269). This is coordinator-fetched metadata attribution, not a separate API fetch by this reviewer. There is no executable delta between the first detailed hosted evidence and reviewed tip. These are development results; post-merge main, final PR review and hosted guest smoke are not inferred. T-034 still owns hosted QEMU runtime enforcement.

#### Complete standard checklist

| Item | Disposition |
|---|---|
| Intent/tests first, topological review | Task and actual probe read first; configurations/walker before caller/workflow/docs |
| Correctness | Three denies per crate; ten reviewed scoped groups; unused-frame substitution preserves behavior |
| Capability semantics | No new authority, object, transfer, revocation or trust-boundary bypass; static demo/bench rights unchanged |
| Fault containment | No syscall/fatal policy change; no new hot-path panic; established EL0 non-SVC limitation remains |
| Unsafe discipline | Changed call/comment explicitly approved above; audit append verified; paired distinct security approval received and read |
| Error handling | Exact intended lint rejection required; success and deny-removal refused; cleanup checked |
| Tests | Real private probes plus real deny-removal controls; broad local/hosted evidence attributed |
| Documentation | Commands, exception inventory, audit/history/status and evidence limits reconcile |
| Dependencies | None added/upgraded; dependency workflow not triggered |
| Naming/style | Existing English/attribute/shell conventions; independent syntax/ShellCheck/whitespace pass |
| Commit messages | Three conventional commits, valid ADR/Audit references; security completion remains parent-owned |
| Performance | Lints/attributes/probes add no shipped runtime work; changed MMU value is unused; no measured speedup or new performance claim |
| Publication/lifecycle | Parent owns canonical artifact/index/trailer/history; task stays In Review; no Done or merge action |

#### Architectural principles P1–P12

| Principle | Disposition |
|---|---|
| P1 No ambient authority | Preserved; no authority surface change |
| P2 Small defensible TCB | Preserved; enforcement strengthens, verification growth is host-only |
| P3 Userspace drivers/services | Unaffected; no subsystem placement change |
| P4 Capability boundaries | Preserved; unchanged runtime checks and provisioned demo/bench caps |
| P5 Rust/audited assembly | Rust lint/call changes audited; assembly untouched, no soundness certification |
| P6 HAL separation | Preserved; no board detail enters HAL/kernel interfaces |
| P7 No proprietary blobs | Preserved; disposable image built from tracked Rust, no committed binary |
| P8 ADR governance | Existing Accepted ADR-0040/error policy implemented; no new policy choice |
| P9 English | Changed artifacts and commits English |
| P10 Mermaid | No diagram change needed |
| P11 Reproducibility | Pin/lock/flags unchanged; fresh private targets prevent stale-negative proof; no bit-for-bit kernel certification |
| P12 Complete scoped work | Acceptance implementation/evidence satisfied; distinct Round 1 security review received; second-round/maintainer lifecycle remains explicit |

#### Read coverage and limits

Read AGENTS and complete CLAUDE, current roadmap including historical banners, numerical ADR corpus (0001–0033, 0035–0040; 0034 has no file), all standards/index, skill index and both complete review skills/master plan. Bounded follow-up reads recovered truncated substantive portions. Read relevant complete preflight and T-030/T-037 code records, T-032 task/approved sequence, actual probe, full executable diff and attached exception functions, MMU root/value/walker contracts, build helper/BSP build script/Cargo configuration and affected workflow ordering, changed guide/status/audit material, commits and supplied hosted metadata/log excerpts, then the full completed paired Round 1 security report. Existing cap-unmap and rollback test contracts were inspected as complementary evidence after the primary probe-first review.

This is a focused code review, not a whole-repository unsafe re-audit or security pass. No shared image/kernel ELF write, repository/GitHub edit, branch mutation, commit, independent broad host/Miri/stable suite, guest QEMU run, hardware/SMP test, performance measurement, signal/kill cleanup stress test or full historical-anchor audit was performed. Existing HIGH T-038 remains excluded and unaffected; host tests/Miri/lint success cannot certify its assembly soundness. BSP unmap was inspected statically, not newly executed in QEMU.

### Verdict

**Approve T-032 at `4f2c38c` for this fresh Round 1 code review. No actionable findings.** All five axes, the complete standard checklist and P1–P12 are covered. Independent real probes/deny-removal controls and the attributed local/hosted evidence support the implementation. The completed distinct fresh security report was read in full and separately approves the scoped delta and changed UNSAFE-2026-0025 reasoning, preserving the same runtime-unmap, SMP and T-038 exclusions.

Parent-owned canonical publication/index/trailer/audit completion recording, second fresh code/security rounds and final maintainer PR review remain pending. This approval does not promote Done, authorize merge, certify assembly/whole-kernel soundness or claim new BSP unmap runtime verification.

## Round 2 code review

- **Change:** approved Track B.2-1 step 5, T-032 on `development`, `8591ceb..6e191e229d932ea7a3e330cfa55e9e0dc981f4e8`. Implementation `c3f32c8`, audit-SHA reconciliation `b6572cc`, hosted evidence `4f2c38c`, full Round 1 reports and actual unsafe approval recording `6e191e2`.
- **Reviewer:** fresh independent delegated agent `/root/b21_step5_round2_code`, acting on behalf of @cemililik. Requested configuration: `gpt-6.1-sol`, high reasoning, `fork_turns=none`; this is configuration provenance, not independently attested runtime model identity.
- **Date:** 2026-10-12, Europe/Istanbul. Hosted timestamps are UTC.
- **Risk class:** Security-sensitive: boot/exception/MMU context and changed unsafe-call reasoning. No syscall or assembly implementation change.
- **Security-review cross-reference:** distinct [security artifact](../security-reviews/2026-10-12-t032-panic-family-denies.md). Full completed Round 1 code and security reports were read; their explicit approval of changed UNSAFE-2026-0025 reasoning is now truthfully recorded append-only. The completed independent Round 2 security report was read in full at `/tmp/tyrne-b21-t032-round2-security.md`: **Approve**, no actionable finding, explicit changed 0025 approval and verified actual Round 1 recording. Parent owns its canonical publication and completed-pair recording.
- **Procedure:** `perform-code-review`, `conduct-review`, all five master-plan axes, complete code-review checklist and P1–P12. `justify-unsafe` was consulted for changed reasoning. Task/acceptance criteria and actual negative-probe harness were read before implementation, followed by configuration/types, full affected walker, callers/attached exception function bodies, workflow and evidence documents. Parent owns canonical publication/index/trailer/history; this reviewer writes only temporary verification evidence and this report.

### Correctness

**No actionable finding.** Each of HAL and BSP gains the three intended crate-root denies, with no weakening of existing kernel/workspace lint enforcement. HAL has no exception; syscall and MMU paths have no panic-family allowance. No runtime panic, public API, error variant, capability operation or fault-policy change is added.

The ten exception groups were inspected as multiline attributes and with their full attached function bodies:

| Functions | Allowed lints | Classification |
|---|---|---|
| `main::kernel_main_high` | expect, panic | One-shot trusted boot: static image/configuration, fixed-capacity objects, table/arena initialization and scheduler population before start |
| `perf_bench::run` | expect, panic | One-shot trusted measurement setup: static image, object/cap creation and publish-before-start order |
| `main::idle_entry` | expect | Trusted post-start scheduler invariant, accurately described as such rather than initialization |
| `main::task_a`, `main::task_b` | expect, panic | Existing trusted one-round kernel IPC demo with fixed capabilities and rendezvous protocol |
| `perf_bench::driver_yield` | expect | Trusted post-start current-task invariant |
| `perf_bench::driver_send`, `perf_bench::partner_recv` | expect | Statically provisioned SEND/RECV caps and fixed benchmark protocol |
| `exceptions::irq_entry` | panic | Existing fatal unhandled-IRQ branch after EOI; timer/spurious return paths preserved |
| `exceptions::panic_entry` | panic | Existing fatal unhandled-exception policy |

Every group is function-scoped and has a concrete `reason`. None permits unwrap. No new crate/module exemption appears. Reasons neither label live syscall input as boot nor promise task-fault containment that the existing BSP does not implement. Non-SVC fatal behavior remains unchanged; no future-phase assignment or expanded policy approval is inferred. Assertions are outside these three Clippy lints, as the guide explicitly explains. The change enforces three source-level lints, not absence of all panic mechanisms.

`QemuVirtMmu::unmap` still performs the VA alignment check and invokes `walk_and_install_leaf` with the identical root, VA, flags, null provider and literal `true`. The third argument changes from an infallible aligned-zero frame construction/unwrap to a copy of the existing typed root. `PhysFrame` is a Copy aligned-address wrapper, not an ownership token. No new reference, pointer dereference, allocation or authority arises from copying it.

I traced the complete helper, including all intermediate success/error branches. Each intermediate call receives the unchanged `unmap` selector, returns typed missing/block errors without allocating when true, and never sees `pa`. The true L3 arm reads the current leaf, extracts its masked PA, clears the slot and returns the descriptor-derived frame. The parameter `pa` occurs only in the false/map arm's descriptor encoding and return. Consequently the substituted value cannot affect descriptor accesses, errors, returned frame, allocation, ordering or caller flush obligations on this literal-true call. The kernel `cap_unmap` caller retains authorization/arena resolution before mutation and discharges the returned flush token before returning the frame.

**Reviewed `unsafe` in `bsp-qemu-virt/src/mmu.rs:307–333`, including the changed call/comment at :319–328; agree with and explicitly approve the changed SAFETY reasoning under UNSAFE-2026-0025.** Reusing an already-valid typed value for a genuinely ignored argument removes an unnecessary panic-family expression without an MMU allowance or broader unsafe scope. Existing valid-root, exclusively owned table lifetime, direct-map and index-bound obligations remain load-bearing. This approves the delta, not every historical table-walker or SMP claim.

The probe adds `black_box(None::<u64>).unwrap()` in non-test crate-root code outside allowances and requires nonzero exit plus the exact `clippy::unwrap_used` diagnostic. It rejects success or unrelated failure alone. Actual host/kernel aliases select the intended packages/targets and retain `-D warnings`. The BSP builds source-derived userland inside its copied tree before probing, preventing missing-image failure from serving as lint evidence. The existing NUL-delimited copy loop preserves tracked filenames and modes; a fresh private target prevents stale compiler results; EXIT cleanup covers observed normal/error exits. No shared image/kernel output is written.

### Style

**Clean.** Independent Bash syntax checking, default-severity ShellCheck and range whitespace validation pass. Rust attributes follow existing conventions with explicit reasons. No toolchain/target flag/dependency change, unrelated refactor, broad suppression or style churn appears. Changed prose and conventional commit subjects are English. All four commits carry valid `Refs: ADR-0040`; implementation/audit reconciliation/actual review recording carry `Audit: UNSAFE-2026-0025` where applicable. The final recording commit names the real distinct reviewer and existing artifact in `Security-Review:`; it does not retroactively claim the implementation had an approval that was then pending.

### Test coverage

**Adequate for the scoped enforcement change; no missing blocking test.** The persistent tests exercise the exact real Clippy commands, rather than a synthetic string search or alternate flags. Existing fake-MMU `cap_unmap_returns_unmapped_frame` checks returned PA and both TLB invalidations, while rollback tests cover kernel-level leaf reclamation. Those contracts are complementary evidence, not execution of this BSP walker. No public API/Error variant was added. Static ignored-parameter equivalence supports the only runtime expression substitution; the ordinary smoke does not exercise BSP unmap.

Fresh independent checks in this round used the pinned nightly, `/bin/bash`, Python `TemporaryDirectory` roots with spaces and private target/source trees:

| Check | Observed result |
|---|---|
| Real `tools/test-ci-gates.sh --hal` | Harness 0; actual host Clippy 101 with `clippy::unwrap_used`; private probe root removed |
| Real `tools/test-ci-gates.sh --bsp` | Harness 0; private 117-byte image built; actual kernel Clippy 101 with intended unwrap lint; private probe root removed |
| HAL root expect probe in tracked private snapshot | Exact `cargo host-clippy` 101 with `clippy::expect_used` |
| BSP separate panic helper called by panic-allowed `task_a` | Exact `cargo kernel-clippy` 101 with `clippy::panic`; caller allowance does not propagate to callee |
| Perf separate expect helper called by expect-allowed `driver_yield` | Exact feature-aware perf Clippy 101 with `clippy::expect_used`; caller allowance does not propagate to callee |
| Additional BSP panic helper called by idle | Exact kernel Clippy 101 with `clippy::panic` |
| Audit historical-byte comparison | Removing only both T-032 additions (2,571 bytes) restores `8591ceb` log exactly |
| Shared source/image and cleanup | HAL/BSP root SHA-256 and existing hello SHA unchanged; outer snapshots/targets removed |
| Script syntax, ShellCheck, range whitespace | All exit 0 |

Logs and machine-readable results: `/tmp/tyrne-b21-t032-round2-code-checks/`. The same-lint panic-callee control specifically uses `task_a`, whose caller permits panic; the extra idle-callee case alone would not establish this same-lint property. No failed fixture is counted as a passing check. The shared debug image remains SHA-256 `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`.

Full Round 1 reports separately record fresh real unwrap probes, deny-removal controls and expect/panic rejection in both crates. These were read as prior independent evidence, not represented as this reviewer's executions. Parent-supplied implementation checks cover fmt/actionlint, host/default/release/perf builds and Clippy, 366 host and 366 Miri passes with existing warnings/two ignored HAL doctests, real debug greeting/exit/completion/two SVCs/no fault class, eleven controlled probe/CLI cases and 59 QEMU argument cases. This round did not repeat those broad suites or guest smoke without a source concern.

### Documentation

**No actionable finding.** The guide matches the two exact commands, private BSP image construction and meaning of expected rejection. Task history enumerates all ten classifications, differentiates baseline/local/hosted/review evidence, and correctly retains In Review. The index/current focus and review history preserve second-round/final maintainer PR pending state, with no Done or merge claim.

The actual implementation SHA in the dated 0025 amendment resolves to `c3f32c8`; the amendment states the operation, unchanged invariants, rejected allowance and runtime/SMP limits. The appended actual Round 1 recording matches the full source reports: both explicitly approve the changed argument reasoning and the distinct security report has a scoped Approve verdict. The historically pending sentence remains intact and is completed by a subsequent truthful record. Independent comparison proves original entries and every earlier amendment are byte-preserved. The retained historical SMP-forward claim is expressly excluded, with T-069 owning that work. No standard or Accepted ADR body is rewritten. Existing error-handling policy under ADR-0040 supplies the decision; T-052 retains standards/reality wording ownership.

### Integration

**Clean for the delta.** New CI steps follow the corresponding positive lints in existing jobs without `continue-on-error`. Required job names, action pins, permissions, triggers, workspace membership, lockfile and toolchain are unchanged. Copied toolchain/config select the same nightly/aliases outside the checkout override. Private BSP image/targets cannot disturb the production debug → release → restored debug sequence. No executable source changes occur after `c3f32c8` in the reviewed range.

I inspected parent-downloaded `/tmp/tyrne-b21-step5/hosted-run.json`, `hosted-fastlane.log` and `hosted-kernel.log`. Metadata binds `b6572cc` to completed success for all five jobs in [run 38181326486](https://github.com/HodeTech/Tyrne/actions/runs/38181326486). Fast-lane line 202 records HAL rejection101/unwrap; kernel lines213–214 record private117-byte build and BSP rejection101/unwrap. Kernel lines173/244/276 corroborate production117 →69 →117 bytes, and metadata records positive release/perf gates successful. This is direct inspection of supplied files, not an independent GitHub fetch.

Parent reports read-only metadata confirming all five success at docs-only `4f2c38c` in [run38181458269](https://github.com/HodeTech/Tyrne/actions/runs/38181458269), and exact reviewed `6e191e2` in [run38181945962](https://github.com/HodeTech/Tyrne/actions/runs/38181945962). These later metadata queries are coordinator-supplied evidence. No post-merge main, live branch-protection settings or hosted guest execution is inferred; T-034 owns runtime CI smoke.

#### Complete standard checklist

| Item | Disposition |
|---|---|
| Intent/tests first and topological review | Task/harness before implementation; types/configuration/walker before caller/workflow/docs |
| Correctness | Three denies per crate, ten reasoned scopes, unchanged true-arm behavior |
| Capability semantics | No authority, rights, transfer/revocation or trust-boundary bypass change; provisioned demo/bench caps preserved |
| Fault containment | Existing fatal policy preserved; no new hot-path panic; syscall receives no allowance |
| Unsafe discipline | Changed call/SAFETY explicitly approved above; exact audit preservation and truthful prior distinct approval verified |
| Error handling | Typed errors/caller flush preserved; exact intended diagnostic required; observed cleanup |
| Tests | Fresh real probes plus same-lint callee scope controls; attributed prior/broad evidence |
| Documentation | Guide/task/status/actual review recording reconcile; limits explicit |
| Dependencies | None added/upgraded; addition workflow not triggered |
| Naming/style | Existing attribute/shell/English conventions; independent syntax/ShellCheck/whitespace clean |
| Commit messages/trailers | Four conventional subjects, valid ADR/Audit/review references; actual security recording truthful |
| Performance | No new shipped work from lint attributes/probes; unused value substitution; no speedup claim or measurement needed |
| Lifecycle/publication | Parent owns recording; task remains In Review, final human PR pending |

#### Architectural principles P1–P12

| Principle | Disposition |
|---|---|
| P1 No ambient authority | Preserved; no capability operation or grant added |
| P2 Small defensible TCB | Preserved; verification growth host-only, redundant runtime expression removed |
| P3 Userspace drivers/services | Unaffected; no subsystem placement change |
| P4 Capability boundaries | Preserved; unchanged checks and static least-privilege provisioning |
| P5 Rust/audited assembly | Rust call change explicitly audited; assembly untouched and not certified |
| P6 HAL separation | Preserved; hardware details remain BSP-local |
| P7 No proprietary blobs | Preserved; private source-derived image, no committed binary |
| P8 ADR governance | Existing Accepted ADR-0040 and MMU/error contracts followed; no new policy choice |
| P9 English | Changed repository artifacts and commits English |
| P10 Mermaid | No diagram change required |
| P11 Reproducibility | Pin/lock/flags preserved, private targets; no bit-for-bit kernel attestation |
| P12 Complete declared scope | Concrete implementation/gates present; fresh review and human lifecycle kept explicit |

#### Read coverage and limits

Read AGENTS, complete CLAUDE, current roadmap including historical banners, numerical ADR corpus 0001–0033 and0035–0040 (0034 has no file), all standards/index, skill index, both complete review skills/code master plan and relevant unsafe skill. Bounded follow-ups recovered truncated policy portions. Read T-032 and actual harness before executable diff; full affected exception function bodies and walker/helper, frame/root/flush contracts and kernel cap-unmap regression, image helper/build script, Cargo/toolchain/target configuration, affected workflow ordering, guide/status/audit/commit changes and both full completed Round 1 reports, then the full completed distinct Round 2 security report. This mandatory context reading is not a whole-repository recertification.

No repository/GitHub edit, commit, branch mutation, external communication or shared image/kernel ELF build was performed. Fresh compiler experiments and source-derived image were confined to disposable private trees/targets. No independent broad host/Miri/stable suite, guest QEMU run, BSP unmap runtime, hardware/SMP test, performance measurement, hostile termination cleanup stress test, full Markdown-anchor audit or live branch-protection audit is claimed. Existing HIGH T-038 remains unchanged/excluded; successful lint/Miri/boot cannot certify its assembly soundness. Historical audit preservation does not endorse every historical claim.

### Verdict

**Approve this fresh Round 2 code review of T-032 at `6e191e2`. No actionable findings or requested source changes.** All five axes, the full standard checklist and P1–P12 are covered. Fresh real compiler probes/same-lint scope controls, static MMU equivalence, exact audit preservation and honestly attributed prior/local/hosted evidence support the delta. Explicit approval of changed UNSAFE-2026-0025 reasoning is recorded above. Completed distinct Round 1 and fresh Round 2 security reports were read in full. The separate Round 2 report also Approves without new findings, explicitly agrees with the changed 0025 reasoning, and verifies the actual Round 1 approval recording. It independently passed positive host/kernel Clippy and sibling-module boundary probes; these are security-reviewer evidence, not this code reviewer’s executions. Parent must publish and truthfully record the completed second pair.

This code verdict does not promote Done, authorize merge, certify whole-kernel/assembly/SMP soundness or claim new BSP unmap runtime verification. Parent-owned publication/index/trailer/history and final maintainer PR review remain pending.
