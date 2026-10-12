# Security review 2026-10-12 — PR48 tooling follow-up A, fresh round 1

- **Change:** [PR #48](https://github.com/HodeTech/Tyrne/pull/48), `development`, immutable `1e281ac89d791dc3c6920a038ec26381a49623f3..50ab72bf2c15a4d34be25a1491a357313e50390a`.
- **Reviewer:** Codex agent `/root/pr48_tools_r1_security`, acting for the maintainer; this is the agent's verdict, not a maintainer sign-off.
- **Date:** 2026-10-12, Europe/Istanbul.
- **Separation from code review:** fresh security checklist/context, separate agent from implementation and the paired `/root/pr48_tools_r1_code` ordinary code review. The completed prior T-035 code/security history is context, not reused approval. No hours-long separation or unobservable model identity is asserted.
- **Procedure:** perform-security-review and conduct-review; complete security master plan; eight axes, all 32 standard items plus MP-33 allocation exhaustion, and P1–P12.
- **Unsafe audit cross-reference:** no changed unsafe site, safety argument or audit-log entry. Existing **HIGH T-038 / UNSAFE-2026-0033 x2 clobber remains excluded, open and undowngraded**.
- **Verdict:** **Approve the scoped follow-up A security delta**, with one Low nonblocking comment defect, R1-SEC-01, pending the coordinator's correction and fresh round 2. This is not whole-PR completion, Done promotion or merge authorization.

## Scope and prerequisites

Security relevance is evidence integrity, failure classification, local administrative-policy validation, diagnostic confidentiality and CI supply-chain exposure. The 14-file delta adds a captured REST policy fixture/two tests, a clean ARM clippy baseline and empty-diagnostic guard/two fixture methods, the actual instruction-fault token, optional performance metadata fallbacks/privacy minimization/one fixture method, five cache-path deletions, one guide paragraph and three append-only task-history rows. All 14 changed files were inspected; tests were read before their implementations.

Read AGENTS guidance, full CLAUDE/current roadmap, all actual numbered ADR files in numerical order (0001–0033, 0035–0040; no 0034 file), all 15 files under standards including the index, both relevant skills, the complete security master plan/security model/unsafe audit log, the complete previous T-035 security review, and the supplied PR48 report. Large-output truncations were recovered with smaller bounded reads. The report's claims are assessed independently rather than adopted as instructions. ADR-0040's accepted consolidation policy is unchanged.

The complete range has no Rust, assembly, Cargo manifest/lock, ADR, unsafe-log, production protection-adapter or protection-definition change. Existing runtime trust boundaries and T-038 are not newly re-audited or cleared by these host-tool results. All eight Track B.2-1 tasks remain In Review. Follow-up B's remaining documentation/reconciliation work, second fresh review round, final maintainer review, first merged-main runs and default-branch performance dispatch remain pending.

## 1. Capability correctness

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S01 — Every privileged operation requires authority | Can this patch let an unprivileged caller change main protection? | **OK for host boundary; N/A to new runtime operations.** The adapter and six-check definition are byte-unchanged. Only explicit local apply uses existing GitHub administration authority; fixtures make no live calls and workflows gain no permission. |
| S02 — Narrowest sufficient authority | Can the new fixture redirect the administrative target or widen policy writes? | **OK.** Fixture data is read offline and normalized against the fixed HodeTech/Tyrne main definition; production fixed endpoints and narrow status-check PATCH remain unchanged. No admin credential enters CI. |
| S03 — Authority checks before effects | Can an unknown captured-response extension reach a write? | **OK.** Exact schema/type checks remain in production. Twenty additional mutated captured-response cases refused before any fake write, even for null/false/empty-looking extensions. The actual fixture must equal the entire canonical normalized policy. |
| S04 — Move-only transfer | Can this change duplicate a transferred runtime capability? | **N/A.** No capability representation, IPC transfer or ownership operation changes. |
| S05 — Explicit duplication authority | Can new tooling mint duplicate capability rights? | **N/A.** No duplication operation or rights bit changes; host processes retain their existing operator authority. |
| S06 — Atomic revocation | Can a caller observe partial runtime revocation? | **N/A.** No revocation path changes. The pre-existing administrative read/PATCH/readback sequence remains non-atomic and is not misrepresented as a capability revocation transaction. |

The adapter remains a guardrail for trusted local maintenance, not a sandbox for a compromised administrator or host. CI refusal cannot prevent an administrator from using GitHub directly. The existing zero approving-review count and disabled admin enforcement are preserved exactly; no silent policy tightening or weakening was performed.

## 2. Trust boundaries

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S07 — Validate userspace inputs before kernel use | Can malformed input cross a newly weakened parser? | **N/A to kernel; OK for host analogue.** No syscall parser changes. The captured protection endpoint response is validated with the existing exact schema; unsupported fields are still rejected. |
| S08 — User pointers need validated mappings | Can a supplied address become a privileged dereference? | **N/A.** No user pointer, address-space map, copy-user path or kernel dereference changes. Host GitHub transport still uses argv/stdin JSON, not shell interpolation. |
| S09 — Bound user lengths against mapped regions | Can a length overrun a mapped buffer or incomplete evidence masquerade as complete? | **N/A to memory; OK for retained host evidence contract.** No buffer consumer changes. Existing check evidence length/total/100-entry ceiling tests pass; partial performance samples remain explicitly counted. |
| S10 — Typed message parsing | Can policy-bearing fields or unrelated compiler errors be accepted as harmless metadata? | **OK.** New policy tests reject enforcement and actor fields instead of stripping them. ARM accepts only exit 101 plus one exact full diagnostic line after an identical clean command succeeds. Empty expected diagnostic and tested near matches fail. |
| S11 — IPC grants no excess authority | Can a sender transfer rights it does not hold? | **N/A.** IPC, capability tables and rights transfer are unchanged. Offline policy normalization does not create authority. |

**REST fixture and fail-closed policy.** `tools/fixtures/main-protection-2026-10-12.json` is a complete observed body for the protection endpoint, including URL metadata and context ordering. Independently parsed and compared it with the parent-supplied read-only capture: equal. Normalization with the separately versioned GraphQL rule equals the entire canonical definition, including all six app-bound checks and non-status fields. Capture acquisition is the parent's action; the committed fixture is a dated sample, not live drift attestation. Neither the adapter nor policy changed.

The supplied report's M-3 broad metadata-dropping suggestion is not justified: dismissal/bypass actors and enforcement scope are policy. Branch-summary `name`/`protection_url` cannot establish that those keys belong to the protection endpoint. The new tests intentionally refuse them. An unexpected future endpoint shape can stop maintenance until reviewed adaptation; availability loss is preferable to silent policy loss. This fixture does not claim to model every supported GitHub response or replace the GraphQL/ruleset reads. No live administrative mutation was run to discover behavior.

**ARM attribution.** `tools/test-ci-gates.sh:83–110` defines the exact clippy command once, checks all six original cfg anchors, runs it on an unmodified private copy/private target, refuses any clean-baseline failure, then replaces exactly those six predicates and runs the same command. Build script and syscall shim are preserved. Exit 101 plus either exact E0152 duplicate-panic line or exact no_std unwind line remains required; unrelated errors, tool statuses, successful command exits and empty diagnostics fail. The baseline closes the specific false-attribution route where an already-broken source emitted a recognized class before mutation. It does not formally prove causal isolation from nondeterministic external failures or a hostile compiler; a diagnostic coinciding with a new unrelated failure could still exist. This is a controlled regression assertion under trusted tools, not compiler-output attestation.

**Smoke boundary.** Both real smoke and synthetic faults now use `Undefined Instruction`, the producer spelling documented in the BSP boot checklist. Independent synthetic traces in both profiles contain the completion markers plus that fault and correctly fail, so success markers cannot hide it. Hosted artifacts contain those cases. This is not a proof of exhaustive CPU exception detection, exact SVC counts or adversarial EL0 behavior; those remain outside this delta.

## 3. Memory safety

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S12 — New unsafe satisfies policy | Can new unsafe escape SAFETY/audit review? | **N/A.** No production Rust/assembly or unsafe body/contract changes. Shell/Python host tools do not create a new unsafe audit entry. |
| S13 — Safety invariants at every caller | Can these passing gates wrongly certify an existing unsafe contract? | **Flagged — existing excluded HIGH T-038.** The input-only x2 syscall-shim mismatch is unchanged and not endorsed. No new unsafe caller broadens its contract; this scoped approval leaves the HIGH open. |
| S14 — No uninitialized memory exposed | Can new partially filled memory reach a task or log? | **N/A to runtime.** No kernel buffer initialization changes; failed optional metadata is replaced with explicit unknown rather than retained partial command output. |
| S15 — No use-after-free | Can changed ownership or cleanup destroy live source? | **N/A to pointers; OK for host isolation.** Probe copies use a fresh temporary directory/private Cargo target and quoted cleanup. Fixtures verify four original files' hashes and empty scratch after success/refusal/copy failure. |
| S16 — No aliasing violations | Can a borrow now cross a context switch or race? | **N/A.** Rust references, context switches, locks and memory ownership are unchanged. Private experiment copies do not share production build outputs. |

Read the complete audit log for reconciliation and checked the exact diff for absence of unsafe/SAFETY/audit changes. This is an applicability check, not a fresh sign-off of every historical audit argument. Known old claims are interpreted with their amendments and T-038 exclusion; a clean host compiler/Miri run cannot clear architecture assembly defects.

## 4. Kernel-mode discipline

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S17 — No ISR allocations | Can interrupt delivery allocate through a new report path? | **N/A.** Reporting and probes run on the host; no ISR path changes. |
| S18 — No unbounded kernel loops | Can an input newly stall the guest kernel? | **N/A.** Kernel loops are unchanged. The existing finite measurement count, per-guest watchdog and hosted job timeouts remain; optional metadata fallbacks add no retry loop. |
| S19 — Minimize critical sections | Can clippy/API waits hold a kernel lock? | **N/A.** No scheduler state, IRQ masking or critical-section changes. |
| S20 — No hot-path kernel panic | Can the intentional panic-handler regression enter shipped code? | **N/A to changed runtime; OK for tooling separation.** The regression exists only in the disposable hello copy, with unchanged shipped predicates. A baseline failure aborts before mutation. |
| MP-33 — Typed allocation-exhaustion error, not panic | Can resource exhaustion now panic the kernel? | **N/A.** No kernel allocation path, arena quota or exhaustion error changes. Host disk/memory exhaustion is not treated as evidence of a passing compiler rejection. |

The extra clean clippy run costs bounded CI time; native actual execution and hosted ARM success demonstrate feasibility at this source. Successful synthetic metadata does not mean a missing QEMU can run a guest: fallback only handles metadata collection, while missing measurements still fail the existing threshold. No timing-regression threshold or required performance check is introduced.

## 5. Cryptography

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S21 — Reviewed primitives, no homemade crypto | Can a new algorithm forge evidence or rights? | **N/A.** No cryptographic primitive/protocol is introduced. SHA identifiers/digests are provenance references, not a new authentication scheme. |
| S22 — Keys absent from logs/errors/Debug | Can optional metadata errors expose key material? | **OK for applicable diagnostics.** Four metadata commands suppress stderr and discard partial stdout on failure; independent canary tests verify neither stream's secret-like text survives. No new key handling exists. |
| S23 — Constant-time comparisons | Can a secret comparison leak timing? | **N/A.** Comparisons involve public policy, compiler diagnostics, identifiers and sample counts; no secret equality operation changes. |
| S24 — Acceptable randomness | Can weak randomness mint predictable authority? | **N/A.** No key/token/nonce generator changes. Temporary isolation uses existing platform mktemp/TemporaryDirectory mechanisms. |
| S25 — Correct nonces/IVs/salts | Can reuse break authentication? | **N/A.** No encryption, nonce, IV or salt state is introduced. |

## 6. Secrets and logging

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S26 — No secrets in diagnostics | Can normal provenance expose the private checkout path/hostname, or failures preserve sensitive partial output? | **OK within the specified minimization boundary.** Report uses `uname -srm`; rustup explanation is removed after the first space while the normal version/host identifier remains. Failed commands become `(unknown)` with stderr suppressed; independent tests check both streams. No credential store/environment dump is added. |
| S27 — Sensitive Debug redacts/absent | Can a changed formatter expose capability bits? | **N/A to Rust Debug; OK for host representation change.** No sensitive Rust type changes. The report removes unnecessary local identity fields, with explicit unknown metadata and source-state provenance retained. |

`tools/perf-harness.sh:251–264` handles failures of uname, QEMU-version, rustc and rustup commands separately from valid measured samples. Normal toolchain identifiers retain reproducibility value; the override explanation can contain private checkout paths and is dropped. Nonzero metadata commands cannot publish their partial stdout as a successful field. The seven permanent methods include status 1/127 cases, privacy assertions, sample counts, overwrite refusal, dirty/unknown Git state and failed measurement propagation through explicit Bash/tee. Custom tests additionally send canaries on stderr and stdout together, testing the report and process output.

This is minimization of the reported normal host/toolchain fields, not universal arbitrary-output sanitization. A custom toolchain identifier itself can contain operator-chosen identifying text; command output from compromised tools is outside the trusted-tool model. Existing archived reports are unchanged and remain historical; follow-up B must reconcile the supplied report's documentation concerns rather than retroactively relabel them. The unchanged hosted workflow separately captures raw toolchain/version files on a disposable public runner. The inspected newly generated report omits override explanation and hostname; this does not promise that every auxiliary artifact or every historical report has been redacted.

## 7. Dependencies

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S28 — Dependency policy followed | Does this patch pull in unaudited third-party code? | **OK.** No dependency/toolchain/action pin changes; Python uses stdlib and existing Bash tools. Five executable cache paths are removed. |
| S29 — Trust category understood | Can cache data silently replace installed executables or be mistaken for runtime trust? | **OK for reduced surface.** Changed caches omit cargo-bin while preserving registry/git/target caches. Tool installation remains explicit and action/toolchain pins unchanged. Existing build-cache trust remains; this is not hermetic build attestation. |
| S30 — cargo-vet updated as required | Is a new kernel-linked crate unaudited? | **N/A.** Cargo graph and lockfile are unchanged; no new cargo-vet decision or claim of running cargo-audit/vet. |

The workflow diff is exactly five deletions of `~/.cargo/bin`; keys, restore prefixes, registry/git/target paths, job permissions, triggers and commands remain unchanged. Rust toolchains are explicitly installed before the affected caches. Coverage explicitly installs pinned cargo-llvm-cov; smoke/performance/coverage already omitted bin. All cache keys/prefixes retain OS and architecture separation; restore prefixes intentionally need not contain a lockfile hash.

Cache matching includes version as well as key/branch, and version incorporates the cached path list and compression. Thus the changed path list separates the old bin-containing cache version even with unchanged textual keys; this is an inference from the pinned action's documented semantics, not a live cache inventory or destructive cache experiment. [Pinned actions/cache v4.2.3 README, Cache Version](https://raw.githubusercontent.com/actions/cache/5a3ec84eff668545956fd18022155c47e93e2684/README.md), [GitHub cache matching reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching#cache-key-matching).

No historical caches were deleted. Registry/git/target remain trusted build inputs and can contain generated executable build artifacts; omission of bin reduces one overwrite surface and does not eliminate all cache poisoning possibilities. Hosted-source execution itself remains trusted only to the workflow's existing privilege boundary. The retained coverage comment incorrectly contrasts its omission with siblings; R1-SEC-01 records that narrow documentation defect below.

## 8. Threat-model impact

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S31 — Reconciled with security model | Can host evidence falsely weaken runtime isolation or repository protection? | **OK for scoped delta.** No runtime principal, authority, MMU/IPC/DMA boundary changes. Evidence becomes more conservative: clean baseline, exact fault token, retained policy refusal, explicit unknown metadata and smaller executable cache surface. |
| S32 — Model changes documented/tracked | Is a new trust assumption hidden or a planned policy change silently applied? | **OK.** ADR-0040 policy is byte-unchanged. Host compiler/cache/admin assumptions and non-atomic maintenance limits remain. Follow-up B's producer-app boundary explanation is still pending; no CODEOWNERS/reviewer/admin policy change is silently adopted. |

The supplied M-2 assertion is not established here as a demonstrated hosted duplicate-name bypass. App ID identifies a check producer, not the integrity of its workflow's contents; trusted workflow review remains an actual boundary to document in B. The adapter separately rejects duplicate name matches in the evidence it uses to authorize adding a check. That local API guard is not a theorem about GitHub's merge enforcement. We neither conflate those boundaries nor claim that a trivial duplicate hosted job was proven to bypass the required job.

The existing final reread/full readback narrows but cannot remove another-administrator races: separate policy reads and PATCH are not atomic compare-and-swap. That accepted local-maintenance limitation is unchanged; no live apply was performed. Performance remains informational, separate from required smoke, with failed measurements failing workflow execution and no calibrated merge threshold. Schedule/dispatch on the default branch and first merged-main proof remain merge-dependent.

## Findings

### R1-SEC-01 — Low, nonblocking: stale sibling-cache contrast

- **Location at reviewed head:** `.github/workflows/ci.yml:438–440`.
- **Evidence:** coverage's cache comment still says bin is omitted “unlike the sibling jobs,” but this delta removes all five remaining sibling cargo-bin paths. The comment now misstates the reviewed cache boundary.
- **Impact:** documentation/post-fix-sweep inconsistency; no execution, permission or policy effect. Cache removal itself is security-positive within the limits above.
- **Required correction:** remove the contrast and describe explicit tool installation and bin omission consistently.
- **Owner/status:** coordinator verified the finding and plans an A round-1 correction before fresh round 2. **Open at immutable 50ab**; a future change is not certified by this report. This does not block scoped security approval.

No new High/Medium security defect or blocking finding was established. T-038 remains a pre-existing excluded HIGH, not a newly waived minor finding. Other supplied-report documentation matters remain assigned to planned follow-up B; this verdict does not silently close them.

## Architectural principles P1–P12

| Principle | Disposition and justification |
|---|---|
| P1 — No ambient authority | **OK.** No runtime grant or CI administration authority added; local admin adapter unchanged. |
| P2 — Smallest defensible TCB | **OK.** Host tooling only; no kernel TCB increase. |
| P3 — Drivers/filesystems/network in userspace | **N/A.** No runtime placement changes. |
| P4 — Capability checks at every boundary | **OK for host analogue.** Unknown policy fails before writes; runtime capability boundaries unchanged. |
| P5 — Rust-only kernel/justified assembly | **N/A to changed code.** Bash/Python are host tools; no unsafe or assembly contract broadened. T-038 remains HIGH. |
| P6 — HAL separation | **N/A.** No kernel/HAL dependency/interface changes. |
| P7 — No proprietary blobs | **OK.** Text fixture/scripts only; no new committed guest binary. |
| P8 — Decisions in ADRs | **OK.** ADR-0040 unchanged; corrections implement its existing policy rather than revising it. |
| P9 — English repository | **OK for delta.** New diagnostics/fixtures/comments/history are English. Remaining supplied-report language/documentation concerns belong to B. |
| P10 — Mermaid diagrams | **N/A.** No new diagram. |
| P11 — Reproducibility | **OK within evidence limits.** Toolchain/action pins and lockfile unchanged; normal toolchain identifier/source state retained; optional missing data explicitly unknown. Timings remain host-contextual. |
| P12 — No half-finished main subsystem | **OK for scoped development review.** All eight tasks stay In Review; pending A correction/R2, B documentation, maintainer review and merge-dependent evidence are not declared complete. |

## Independent execution and provenance

All executable checks used a private archive of the exact head at `/tmp/tyrne-pr48-security-r1.LaSkZ5`; no repository edit, checkout, branch creation, commit, live API mutation or shared image/build output was used. The private tracked-content manifest includes 407 files, SHA-256 checked after experiments with **zero changed source bytes**. Python bytecode/temp files are not production artifacts.

The first synthetic smoke invocation stopped because a Git archive lacks `.git`; this was an environment prerequisite failure, not a passing test. For subsequent synthetic/native probes, a separate read-only Git shim answered only `rev-parse HEAD`, tracked status and `ls-files -z` from the exact immutable manifest. Status compares every archived tracked file's hash; all other Git commands are refused. Real Bash/Python/Cargo/rustc and probe source were unmodified. This supplies archive metadata without a branch/commit mutation; it is disclosed because this is not a test of Git itself. Native Cargo outputs are private to the probe's fresh temporary target and removed by its EXIT trap.

| Independently executed check | Result and limit |
|---|---|
| `python3 tools/test-branch-protection.py`, repeated with `-O` | **29 methods pass in each mode.** Offline fake API; no administrative credentials/live transport. |
| `python3 tools/test-perf-harness.py`, repeated with `-O` | **7 methods pass in each mode.** Synthetic timing/metadata and pipeline controls, not real guest timing. |
| `python3 tools/test-arm-host-probe.py`, repeated with `-O` | **11 methods pass in each mode.** Controlled stub diagnostics, exact command/private source/target assertions, source preservation and cleanup. |
| `tools/test-smoke-gates.sh` with manifest Git shim | **20 synthetic cases pass**, completed JSON, exact smoke hash. No local real guest builds were requested. |
| `tools/test-ci-gates.sh --arm-host` with manifest Git shim | **Actual native Apple ARM clean compile then mutation rejection pass**, exit 101/E0152, captured `/tmp/tyrne-pr48-security-r1-native.log`. No actual Linux ARM compiler claim from this local run. |
| `/tmp/tyrne-pr48-security-r1-attacks.py`, normal and `-O` | **4 unittest methods / 29 subcases pass in each mode:** 20 unknown captured-extension value combinations, duplicate JSON key, four whitespace/ANSI near-match diagnostics, four stdout/stderr metadata canaries. Assertions use unittest methods and remain active under optimization. |
| `shellcheck tools/*.sh`; actionlint on both workflows | **Pass.** Existing source unchanged by tools. |
| Exact-range invariant check | No Rust/assembly/Cargo/ADR/audit/adapter/policy-definition changes. Fixture JSON equals parent capture. |

The normal and optimized ARM wrapper suites spawn shebang Python stub processes normally; running the top-level suite with `-O` does not automatically propagate optimization to those child interpreters. Their top-level unittest assertions remain active. The production adapter uses explicit exceptions rather than optimization-removable assertions. Counts are test methods, not counts of real compiler runs or all subcases.

The coordinator separately reports private new-tests/old-base controls distinguishing the old metadata failure, missing clean baseline and Undefined Instruction gap. Those are parent-executed experiments, not claimed as this reviewer's execution. Paired code review also independently performed old-code controls; its complete artifact is cross-read before finalization.

### Reviewed source digests

| File | SHA-256 |
|---|---|
| `tools/test-ci-gates.sh` | `34c3bc7dd449393828f122c9f203cc353e4e32fcfc6d6a6c5160815106c1e04d` |
| `tools/perf-harness.sh` | `800a5ae2d771a19ff74c47748f68d62c3295ae4fae3014dbed6b488c9737a530` |
| `tools/smoke.sh` | `cac6e377c442854384ceb9954ab664d9a0b7d95261eb0ddfb4ba98d3e1795c7a` |
| `tools/branch-protection.py` (unchanged) | `747b196e11e21340d0a7d607c7699fd129d58f9df54b96199ff6bad6907a55bd` |
| `.github/branch-protection/main.json` (unchanged) | `edd66dad0b4591c937556be55f6c473bf87e23173cde931c53347b6dc88b8a5b` |
| ADR-0040 (unchanged) | `5b82f632157033d193e64ac554390bacb9944fcd7a79fac9760a666c5f02ff2c` |

## Parent-acquired hosted evidence independently inspected

The coordinator acquired these service summaries/logs/artifacts; this reviewer inspected the downloaded local evidence. This is not independent API retrieval, artifact-archive authentication or a new live policy operation. Sources all name exact full head 50ab; subsequent source changes need fresh evidence/review.

- [PR CI 38210439123](https://github.com/HodeTech/Tyrne/actions/runs/38210439123) and [push CI 38210436230](https://github.com/HodeTech/Tyrne/actions/runs/38210436230): parsed parent `run-{id}.json`, exact full SHA, correct events, completed/success and all seven jobs success in each.
- [Performance 38210436174](https://github.com/HodeTech/Tyrne/actions/runs/38210436174): exact-head development push, completed/success; full report and metadata inspected. **20 requested / 20 valid / 0 failed**, clean tracked state, normal nightly identifier, no report override path/hostname, QEMU 8.2.2. Harness wall **100 s**, enclosing evidence interval **137 s**. Recomputed nearest-rank p10/p50/p90 from all 20 raw values: **5,232,672 / 5,473,392 / 7,277,776 ns**. No calibrated regression conclusion follows from those values.
- Recomputed report-file SHA-256: **`24c143abb0151de1eb3fb38ff3d74f3e060effd2a6c492cc8389bebca565ae85`**. This is the report file's digest; the service artifact archive digest is only parent/service-reported and was not independently recomputed.
- `/tmp/tyrne-pr48-followup/arm-50ab.log`: actual native `aarch64-unknown-linux-gnu`; exact probe prints exit 101/E0152. Native tests and Miri each total **366 passing**, with **two ignored HAL doctests**. The baseline log is not separately archived on success; the reviewed control flow plus overall probe success means it passed. No fabricated baseline stdout is quoted.
- `/tmp/tyrne-pr48-followup/smoke-50ab/*`: results name exact full 50ab, clean tracked source, smoke hash `cac6e377…`, completed true and all **23 cases passing** (20 synthetic plus three actual private kernel variants). Inspected both actual production traces: debug greeting/exit/completion; release exit/completion with no greeting; neither contains the rejected fault classes. Both new `fault-5` traces visibly contain Undefined Instruction and their results reject it. These are downloaded hosted guests, not local re-execution.
- `/tmp/tyrne-pr48-followup/main-protection-live.json`: equals the complete committed REST fixture after parsing. Parent additionally reports read-only live full-policy check pass; this reviewer did not execute any live export/check/apply. A historical capture cannot guarantee future drift absence.

Full Rust/Miri guest-runtime suites were not independently rerun locally for this host-only delta. Hosted evidence and the actual local ARM command are accurately separated. Cache version/path semantics were checked against official documentation at the pinned action revision; the first GitHub blob fetch failed, then its raw immutable README was successfully read. No live cache deletion/poisoning experiment was performed.

## Paired-review reconciliation and publication

Provisional findings were sent before waiting for the peer to prevent mutual completion deadlock. The complete 125-line paired code report `/tmp/tyrne-pr48-tools-r1-code.md` was read before this security handoff. It independently Approves the exact same range with zero new blocking/High/Medium findings and the same one Low R1-SEC-01. Its reported independent read-only live check/GET, old-production regression controls and hosted API retrieval are peer evidence, not reattributed as this reviewer's actions. Its private synthetic Git commit is disclosed as fixture metadata; this reviewer used the separate read-only manifest shim described above. The findings and scope limitations agree; no further issue was found during cross-read. R1-SEC-01 was also independently noticed by the peer and coordinator, with one shared finding rather than duplicate blocker claims.

The coordinator owns canonical artifact/index/trailer publication under this reviewer's explicit no-repository-edit constraint. This temporary full report does not claim that later recording has happened. Future corrected source and fresh round 2 remain separate.

## Verdict

**Approve — scoped security review of follow-up A at immutable `50ab72bf2c15a4d34be25a1491a357313e50390a`.**

All eight axes, all 33 checklist dispositions and P1–P12 are covered. No new blocking security defect was established. R1-SEC-01 is a Low nonblocking stale-comment issue, open at this head with an authorized correction planned before fresh round 2. Existing HIGH T-038 remains excluded, open and undowngraded. Follow-up B documentation/reconciliation, maintainer review, all eight tasks' In Review status and merge-dependent first-main/default-dispatch evidence remain untouched by this approval.

## Coordinator publication and finding disposition

The complete reviewer report above is preserved at its immutable reviewed source. The [paired canonical report](../code-reviews/2026-10-12-pr48-tools-followup-r1.md) is published alongside it; private `/tmp` evidence paths remain acquisition locations, not durable links. The coordinator read both full reports and independently verified R1-SEC-01. This publication commit replaces the stale sibling-cache contrast with the current explicit-install/all-cache-bin-omission comment. Actionlint and whitespace checks pass after that comment-only correction. This records the correction, not a reviewer certification of future source; fresh round 2 is still required.
