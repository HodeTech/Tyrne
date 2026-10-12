# Security review 2026-10-12 — T-030 release gates

- **Change:** T-030 on `development`, `8437158..364b746`.
- **Reviewer:** fresh independent `b21_step4_round1_security`, acting on behalf of @cemililik; `gpt-6-astra` / high requested with fresh context.
- **Separation from code review:** separate agent and empty security checklist; no implementation or paired code-review context inherited.
- **Unsafe audit cross-reference:** n/a; test imports only, no unsafe body, predicate or safety-reasoning change. Existing HIGH T-038 remains explicitly excluded.
- **Paired code review:** [code-review artifact](../code-reviews/2026-10-12-t030-release-gates.md).

> **Current reconciliation:** Round 1 Approve, no new security finding. The report's third-test wording was corrected to *third passing matching test* before publication; verdict and evidence are unchanged. Both fresh security rounds now Approve with no new finding; the second round independently exercises real positive/negative checks and 16 controlled cases. Final maintainer PR review remains pending. This follow-up records the distinct approval; it does not retroactively claim a review trailer on the earlier implementation commit or promote Done.

## Round 1 security review

**Approve the T-030 release-profile CI delta in `8437158..364b746`. No new security finding.** This is a distinct security review of the change, not a certification of the whole kernel, a Done promotion, or merge approval. Fresh round 2 and final maintainer review remain required.

- **Reviewer:** `/root/b21_step4_round1_security`, independent of the implementation and the paired code-review agent.
- **Requested configuration:** `gpt-6-astra`, high reasoning, fresh context (`fork_turns=none`); this records the requested configuration, not an independently attested runtime model identity.
- **Date:** 2026-10-12, Europe/Istanbul.
- **Scope:** implementation `b8ad56f`, standards reconciliation `c716ae3`, and evidence-only task/current updates `364b746` on `development`; 14 changed files. The production syscall gate, syscall implementation, assembly, unsafe bodies and safety reasoning are unchanged. The Rust delta consists only of three test imports scoped to `cfg(debug_assertions)`.
- **Procedure:** dedicated `perform-security-review` and `conduct-review` skills, security standard and security master plan. The actual standard contains **32** checklist items; its kernel-mode allocation-exhaustion addition in the master plan makes **33 total**, all explicitly covered below.
- **Mutation boundary:** no repository edit, commit, branch, GitHub mutation, external message, shared image/kernel build, or QEMU execution. Independent guard fixtures and this report use temporary files only. Coordinator owns publication, review index/cross-reference and the truthful `Security-Review` recording follow-up.

### Read coverage and evidence provenance

Read AGENTS/CLAUDE, the complete current roadmap including historical banners, the numbered ADR corpus in numerical traversal (0001–0033 and 0035–0040; 0034 is a reserved slot), all files in `docs/standards/`, the skills index and both applicable skills, the full security master plan and security model. Revisited missing portions of truncated reads in smaller slices. This is baseline reading, not a claim to re-audit every subsystem governed by those documents.

Read the existing two release-only tests before analyzing the implementation; then the complete executable delta, complete guard/harness, workflow and Cargo configuration, surrounding syscall decode/dispatch logic, build-userland orchestration and BSP image checks. Read all changed documentation hunks, T-030 in full, the Phase B.2 preflight review and both T-037 security rounds, plus UNSAFE-2026-0033 and its amendments. ADR-0030/0031 explain the debug-console contract; ADR-0039 explains the matching-image build order; Accepted ADR-0040 authorizes this CI policy. No new ADR decision was silently selected.

Independent execution here is the ten-case controlled guard matrix described below. The broader local suite is coordinator-reported evidence; hosted evidence was inspected in the coordinator-fetched logs, rather than fetched or re-executed by this reviewer. The hosted run covers `c716ae3`; `364b746` changes evidence documents only.

### 1. Capability correctness

| # | Standard item | Outcome and adversarial justification |
|---|---|---|
| 1 | Every privileged operation requires the right capability | **OK for delta.** Could release callers obtain console authority through an accidentally enabled debug interface? CI now requires decode(5) to reject and the dispatch test to return `BadSyscallNumber`; existing authority checks are unchanged. |
| 2 | Narrowest sufficient capability | **OK for delta.** No new grant, right, capability type or bypass is introduced; the debug-only path retains `DebugConsole`/`CONSOLE_WRITE`. |
| 3 | Checks precede side effects and failed checks leak no state | **OK for delta.** Release decode rejects before capability lookup, pointer translation or output; the release dispatcher test checks both the precise denial status and an empty console. |
| 4 | Capability transfer remains move-only | **N/A.** Neither transfer nor capability representation changes. |
| 5 | Duplication requires explicit authority | **N/A.** No duplication operation or caller changes. |
| 6 | Revocation is atomic with concurrent use | **N/A.** This compile/test enforcement changes no revocation or concurrency path. |

The dispatch test grants a valid console capability, so rejection cannot accidentally pass merely because the capability is absent. Its empty user window does not make the status assertion vacuous: an exposed console path would return an address error rather than the required bad-syscall status. The separate decode test directly pins the release number table.

### 2. Trust boundaries

| # | Standard item | Outcome and adversarial justification |
|---|---|---|
| 7 | Validate all userspace input before use | **OK for delta.** No new runtime input reaches the kernel; raw syscall number 5 remains denied under release configuration, independently of supplied arguments. |
| 8 | Validate userspace pointers through mappings | **OK for delta.** No pointer consumer or mapping check changes; release denial occurs before the unchanged copy-user path. |
| 9 | Range-check buffer lengths | **OK for delta.** The import cfgs do not change length checks or test assertions; no larger range becomes accepted. |
| 10 | Parse messages into typed structures | **N/A.** No message wire format, decoder or parser changes. |
| 11 | IPC cannot grant more authority than caller holds | **N/A.** IPC and transfer behavior are untouched. |

**Build/CI trust analysis.** The new boundary is source/configuration → release-test evidence. `check-release-tests.sh:10–15` requires the two fully qualified libtest success lines and a two-passed/zero-failed summary, closing the zero-match success hazard. Its `set -euo pipefail` prevents `tee` from masking Cargo failure. Tests cannot disappear, become ignored, be renamed, or gain a third passing matching test without failing the guard. Ordinary libtest output under the pinned toolchain is the intended interface; a format change fails closed.

`test-ci-gates.sh:19–33,73–76` copies tracked current worktree files with NUL-delimited names, preserves executable modes, uses a fresh private `mktemp` tree and target directory, and removes only that quoted directory on exit. The profile is changed only inside this tree. `run_negative` requires both a nonzero exit and the matching guard diagnostic; unrelated Cargo compilation failure alone cannot pass the probe. The observed profile-flip exit is 1. Although the generic helper accepts any nonzero value with the diagnostic, that does not weaken this current path: the guard emits this diagnostic itself immediately before exit 1.

The copied `rust-toolchain.toml` preserves the implicit Cargo pin; the normal workflow uses the matching explicit nightly. A private target directory prevents an old release test executable from satisfying the negative experiment. Tracked source and the compiler/build environment remain trusted: this is regression detection, not authentication of a malicious compiler, forged test output, hostile same-user process, or malicious repository code. The deliberate stub used by this review tests parsing/error propagation, not that broader trust premise.

**Workflow token/cache/profile analysis.** No trigger, credential, permission, secret, action version or cache key is added or widened. Existing `contents: read`, immutable action pins and `persist-credentials: false` remain. No PR-controlled metadata is interpolated into the new shell commands. Existing Cargo caches are a build acceleration trust surface, not an authorization boundary; the new negative target is outside those caches. The workflow keeps existing required job names and adds blocking steps without `continue-on-error` on the new gates.

The kernel job builds matching debug userland/kernel, matching release userland/kernel and release clippy, then immediately restores debug userland before debug `perf-bench` build and final lint (`ci.yml:166–179`). The BSP only checks image presence/change, not its profile; the explicit ordering is therefore load-bearing and correct. No concurrent job writes this job's workspace. Local simultaneous builds would still require caller coordination, an existing property not newly promised by these aliases.

### 3. Memory safety

| # | Standard item | Outcome and adversarial justification |
|---|---|---|
| 12 | New unsafe satisfies unsafe-policy | **N/A.** There is no new/modified unsafe operation, unsafe function, SAFETY comment or safety assumption in the delta. Test import cfgs need no audit entry/amendment. |
| 13 | SAFETY invariants hold for every caller | **Flagged — existing HIGH T-038, excluded.** Existing input-only `x2` in the userland console shim conflicts with kernel write-back; this review does not affirm that invariant. No affected caller, operand, safety reasoning or compilation boundary is changed here. |
| 14 | No uninitialized memory exposed | **OK for delta.** No storage, memory access, initialization, assembly output or runtime code changes. |
| 15 | No use-after-free; raw-pointer lifetimes valid | **OK for delta.** No ownership/lifetime, allocation, raw-pointer construction or dereference changes. |
| 16 | No aliasing violations | **OK for delta.** Cfg-scoping imports cannot introduce conflicting references; existing unsafe contracts are not newly certified. |

**Unsafe verdict explicitly N/A to this delta.** Unlike T-037, which changed predicates enclosing existing unsafe sites and required a boundary amendment, T-030 changes only test imports and CI/configuration enforcement. UNSAFE-2026-0033 is relevant background, not a modified audit contract. No audit ID or amendment is warranted. The original `x2` claim remains excluded at HIGH severity under T-038. Passing clippy, host Miri, release builds or matching images does not certify SVC assembly soundness.

### 4. Kernel-mode discipline

| # | Standard item | Outcome and adversarial justification |
|---|---|---|
| 17 | No allocation in ISR context | **N/A.** No ISR or kernel allocation code changes. |
| 18 | Kernel loops bounded | **N/A.** No runtime loop changes; file copying/testing occurs on the host with finite tracked inputs. |
| 19 | Critical sections minimal and justified | **N/A.** No lock, IRQ mask, scheduling or critical section changes. |
| 20 | No new hot-path kernel panic | **OK for delta.** New failures are host script exit codes; production kernel panic/error behavior is unchanged. |
| 33 | Allocation failure produces a typed error (master-plan addition) | **N/A.** No kernel allocation/exhaustion path changes. Host `mktemp`, copy or Cargo failures propagate as command failures instead of inventing green test evidence. |

CI takes additional build time and isolated disk space, but no user-controlled runtime work or kernel resource budget is expanded. Host workflow timing is not a performance-regression claim about the guest.

### 5. Cryptography

| # | Standard item | Outcome and adversarial justification |
|---|---|---|
| 21 | Primitives reviewed; no roll-your-own crypto | **N/A.** No cryptographic primitive or algorithm introduced. |
| 22 | Keys absent from logs/debug/display | **N/A.** No key material or key handling introduced. |
| 23 | Secret comparisons constant-time | **N/A.** Test names, summary text and Cargo profile metadata are public values, not secrets. |
| 24 | Randomness from an acceptable source | **N/A.** No kernel/security RNG changes; host `mktemp` is used for safe temporary-file creation rather than cryptographic authority. |
| 25 | Nonce/IV/salt use correct | **N/A.** No such operation changes. |

### 6. Secrets and logging

| # | Standard item | Outcome and adversarial justification |
|---|---|---|
| 26 | No secrets in logs, panics, prints or errors | **OK.** New output is Cargo/libtest diagnostics and fixed gate text, with no secret/token interpolation; temporary logs are removed on ordinary exit and error paths. |
| 27 | Sensitive Debug implementations redact | **N/A.** No Debug/Display implementation or sensitive type changes. |

Could release testing itself enable production console output? The tests execute host fakes; only the private negative tree enables debug assertions. The production release profile receives a comment and retains its existing false default. Existing kernel diagnostic output is not claimed to disappear: the scoped contract removes the user-facing `console_write` syscall from the release decode table.

### 7. Dependencies

| # | Standard item | Outcome and adversarial justification |
|---|---|---|
| 28 | New dependencies evaluated per policy | **N/A.** No crate, binary dependency, action or lockfile addition. The script uses existing host shell/Cargo utilities. |
| 29 | Dependency trust category understood | **OK for delta.** New orchestration executes only during host verification; it adds no code to the privileged runtime TCB or userland artifact. |
| 30 | cargo-vet decisions updated | **N/A.** Dependency graph and audit decisions are unchanged; dormant external-dependency gates are not represented as newly active. |

### 8. Threat-model impact

| # | Standard item | Outcome and adversarial justification |
|---|---|---|
| 31 | Reconciled against security-model.md | **OK.** The change improves detection of developer error that would expose a debug syscall to malicious userspace; capability, memory, fault and DMA boundaries remain unchanged. |
| 32 | Model shift documented or tracked | **N/A — no model shift.** No new principal, privilege, runtime communication path or defended attacker class is introduced. Existing T-034 runtime smoke and T-065 explicit-feature work retain ownership. |

The gate is meaningful but bounded: it exercises the host-compiled release syscall contract plus cross-compilation/lint of the bare-metal image; it is not proof of release EL0 execution. A target-specific future gate regression would need the T-034 runtime test, and a deliberate source author can change tests and guard together. Neither limitation is obscured by the current docs.

### Architectural principles P1–P12

| Principle | Result |
|---|---|
| P1 — No ambient authority | **OK:** release syscall absence is enforced without granting new runtime authority. |
| P2 — Smallest defensible TCB | **OK:** only host verification grows; production Rust unchanged. |
| P3 — Drivers in userspace | **N/A:** no subsystem placement or driver change. |
| P4 — Checks at trust boundaries | **OK:** unchanged runtime checks are complemented by fail-closed release evidence. |
| P5 — Rust-only kernel / audited assembly | **OK for delta:** shell is host tooling; no assembly or unsafe change approved. |
| P6 — HAL separation | **OK:** three cfg-scoped test imports introduce no hardware dependence into kernel runtime. |
| P7 — No proprietary binary blobs | **OK:** userland remains rebuilt from source; no binary is committed. |
| P8 — ADR governance | **OK:** ADR-0030/0031/0039 and Accepted ADR-0040 govern the work; standards follow that existing policy. |
| P9 — English artifacts | **OK:** changed code, comments, diagnostics and docs are English. |
| P10 — Mermaid diagrams | **N/A:** no diagram introduced. |
| P11 — Reproducibility | **OK for delta:** pinned toolchain/lockfile preserved, isolated target used for negative probe, matching image order explicit; this is not a bit-for-bit reproducibility audit. |
| P12 — Complete declared scope | **OK:** T-030 implementation gates are concrete; remaining review lifecycle, T-034 runtime coverage and T-065 mechanism change are explicitly separated. |

### Independent adversarial verification

Executed the actual guard in a private fixture tree with a controlled Cargo stub, `/bin/bash`, repository and temporary paths containing spaces. Results are saved in `/tmp/tyrne-b21-t030-round1-security-probes.json`.

| Case | Expected / observed exit |
|---|---|
| Both exact success lines and two-pass summary | 0 / 0 |
| Both tests vanished, zero-pass summary | 1 / 1 |
| Missing ABI success line | 1 / 1 |
| Missing dispatch success line | 1 / 1 |
| Renamed ABI module despite successful summary | 1 / 1 |
| ABI line reports ignored | 1 / 1 |
| Correct two names but three-pass summary | 1 / 1 |
| Correct names but failed summary | 1 / 1 |
| Cargo prints valid green transcript then returns 101 | 101 / 101 |
| Unexpected `--release` argument to the no-argument guard | 2 / 2 |

Every created gate log was removed after success and failure. The argument-rejection case exits before log creation. These probes independently establish the parser and pipeline's fail-closed behavior. They do not substitute for real Cargo execution; that complementary evidence is present in the coordinator's local execution and the inspected hosted logs.

### Hosted/local evidence and limits

The inspected hosted logs for [run 38179424325](https://github.com/HodeTech/Tyrne/actions/runs/38179424325), at `c716ae3`, show release totals **249 kernel + 46 HAL + 58 test-HAL + 3 doc = 356**, with two existing ignored HAL doctests; both exact named narrow tests and a two-pass summary; and the isolated profile flip rejected with **exit 1 and the guard diagnostic**. The kernel log shows **117-byte debug → 69-byte release → restored 117-byte debug**, then final debug perf build/lint. Coordinator-reported run metadata records all five jobs successful. The 13-second hosted release step wall time is build/test overhead, not guest performance.

Coordinator local evidence reports fmt, ShellCheck/actionlint, host/debug/release/perf/userland clippy, debug/release/perf builds, 366 debug and 356 release host tests, Miri 366 with zero UB failures and existing warnings, real narrow guard/profile-flip rejection, seven controlled guard cases and 59 stubbed QEMU fixtures. This reviewer did not repeat that full suite because the independent negative matrix addressed the novel failure concern. The reported restored debug SHA is `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`; no shared image was written by this review.

No runtime QEMU, hardware, target-specific syscall execution, cryptographic, SMP or broad kernel-soundness certification is made. T-038's known HIGH `x2` clobber defect remains excluded and unmitigated by these gates. Release runtime verification belongs to T-034. Hosted evidence is pre-merge development evidence, not a first-main/post-merge result.

### Findings, checklist completion and verdict

**No newly introduced security defect found.** All eight axes, 32 standard items, the master-plan allocation item, adversarial CI trust/failure cases and P1–P12 have explicit dispositions. The unchanged HIGH T-038 issue is retained in the memory-safety checklist without downgrading or implicitly approving it.

**Approve Round 1 for `8437158..364b746`.** No source correction is requested. Publish this report with the paired code-review cross-reference/index and accurate security-review trailer as the coordinating follow-up, then complete the separate fresh Round 2. No task is promoted to Done and no merge is authorized by this verdict.

## Round 2 security review

**Approve the T-030 delta in `8437158..5cd9ee8`. No new actionable security finding.** The existing HIGH T-038 assembly-contract defect remains expressly excluded. This review does not promote a task to Done or replace final maintainer PR review.

- **Change:** approved Track B.2-1 step 4, `development`, `8437158..5cd9ee8a01ac523e48146e2224284b871e3619ab`.
- **Reviewer:** fresh independent Codex security agent `/root/b21_step4_round2_security`, acting on behalf of @cemililik.
- **Date:** 2026-10-12, Europe/Istanbul.
- **Requested configuration:** `gpt-6-astra`, high reasoning, `fork_turns=none`. This is coordinator-supplied orchestration provenance, not independent runtime model-identity attestation.
- **Separation from code review:** dedicated fresh security context and empty checklist, separate from implementation and the paired Round 2 code reviewer. This agent did not perform the paired code review. Earlier canonical reviews were read as historical evidence, not adopted as the verdict.
- **Unsafe audit cross-reference:** N/A for the delta. No unsafe site, enclosing production cfg, safety argument or caller changes. UNSAFE-2026-0033 and its amendments were read as relevant background; its existing x2 claim is excluded under T-038.
- **Procedure:** `perform-security-review` and `conduct-review`, security standard, complete security master plan and security model; all eight axes performed sequentially. The standard has **32 items**. The master plan adds allocation-exhaustion handling, yielding **33 total dispositions** below; the extra item is explicitly labeled MP-1, not presented as a 33rd standard checkbox.
- **Recording boundary:** report and evidence files under `/tmp` only. No repository/GitHub edit, commit, branch mutation, shared image/kernel ELF write or external message. Coordinator owns canonical publication, index/cross-reference and truthful security-review trailer. Tasks remain In Review; final human PR review is pending.

### Scope, reading and evidence provenance

The 18-file range comprises implementation `b8ad56f`, standards reconciliation `c716ae3`, hosted evidence `364b746`, and Round 1 reports/index/task/current recording `5cd9ee8`. Executable changes are the release build/run aliases, release host tests and named-test guard, private profile-flip rejection, release cross-build/clippy, debug perf-bench build/clippy with matching image restoration, and three test-only imports scoped with `cfg(debug_assertions)`. The manifest adds a comment rather than changing the release profile. No production syscall mechanism changes.

Mandatory baseline read: AGENTS, full CLAUDE, full current roadmap including historical banners, all 39 numbered ADR files in numerical order (0001–0033 and 0035–0040; 0034 has no file), all 15 files in `docs/standards/` including README, skill index, both applicable review skills, full security master plan and full security model. Truncated reads were recovered in bounded slices. Reading this corpus is not a fresh audit of every unchanged subsystem.

Task intent and the actual release-only ABI/dispatch tests were read before the implementation. The focused source pass covered the guard/harness in full, Cargo configuration/manifests/toolchain, complete workflow, build-userland helper and BSP image build checks, syscall decode/dispatch entry and console validation, release test fixtures, relevant userland/BSP x2 operands, all executable and changed documentation hunks, task/index sequencing, prior preflight, both T-037 security rounds and both canonical T-030 Round 1 artifacts. The Round 1 recording accurately preserves its reviewed range and pending Round 2 state; `5cd9ee8` records a real separate security-review trailer without retroactively claiming one on implementation.

Independent Git-object comparisons confirm the complete ABI file, userland shim, BSP syscall file, unsafe log, lockfile and toolchain are byte-identical across the review range. Dispatcher bytes before `mod tests` are identical. Its only Rust delta is moving `CONSOLE_WRITE_CHUNK`, `MappingFlags` and `FakeUserMem` imports behind the same debug-assertions predicate used by their test callers. No changed unsafe audit is required.

Independent execution here consists of the real release guard, real isolated release profile-flip probe, 13 controlled guard cases, and three controlled probe/isolation cases described below. Parent's broad local suite and fetched hosted data remain explicitly attributed. This agent did not independently fetch GitHub metadata or rerun hosted jobs.

### 1. Capability correctness

| Standard item | Outcome and adversarial justification |
|---|---|
| S01 — Every introduced privileged operation requires a capability | **OK for delta.** Could release userspace gain console access when debug assertions drift? The new gate detects disappearance of the tests that enforce number-5 denial; production authority is unchanged. No new privileged operation is introduced. |
| S02 — Narrowest sufficient capability | **OK for delta.** Could the changes broaden a grant? No cap kind, right or lookup changes; the debug console still requires DebugConsole plus CONSOLE_WRITE. |
| S03 — Capability checks precede effects; failed checks leak no state | **OK for delta.** Could a release call emit before rejection? Decode returns None before capability lookup or pointer access; the unchanged dispatch test checks BadSyscallNumber and an empty console capture. |
| S04 — Transfer move-only, no accidental cloning | **N/A.** No capability transfer, representation or ownership operation changes. |
| S05 — Duplication requires explicit authority | **N/A.** No duplication operation or authority change exists in this delta. |
| S06 — Revocation atomic, no half-applied state | **N/A.** Build/test enforcement changes neither revocation nor concurrency. |

The dispatcher regression holds a valid console capability and names raw syscall 5. Its empty user window does not make the test vacuous: entering the console handler would produce a range error rather than the asserted BadSyscallNumber. The ABI test separately asserts decode(5) is None. These are meaningful existing behavior tests; the new wrapper verifies they actually ran.

### 2. Trust boundaries

| Standard item | Outcome and adversarial justification |
|---|---|
| S07 — Validate userspace inputs before kernel use | **OK for delta.** Could arbitrary syscall arguments bypass the profile contract? The unchanged decoder rejects the number before reading argument-dependent resources; no new runtime input path is added. |
| S08 — User pointers only through validated mappings | **OK for delta.** Could cfg-scoped imports bypass mapping validation? No pointer consumer or translation code changes. Release rejection precedes the unchanged user-copy path. |
| S09 — Range-check user buffer lengths | **OK for delta.** Could a larger range become accepted? Pointer/length handling is byte-preserved in production; test import scoping does not alter range checks. |
| S10 — Typed parsing of userspace message contents | **N/A.** No message format, decoder or parser changes. |
| S11 — IPC grants no excess/untransferred authority | **N/A.** No IPC authority or transfer changes. |

**Source/configuration to CI evidence is the changed trust boundary.** `tools/check-release-tests.sh` selects one kernel library binary and two filters. It requires both fully qualified exact successful test lines and a two-passed/zero-failed summary. Zero tests, missing/renamed/ignored required tests, duplicate evidence for one required test, and an additional passing matching test fail. A third matching **ignored** test alongside the two required passes is accepted; this does not invalidate execution of those two tests. The report does not claim all third matching tests are rejected.

`set -euo pipefail` preserves Cargo failure through tee: independently, exact green text followed by Cargo exit 101 still exits 101. A pinned libtest output-format change would fail closed. This is regression checking over trusted source/build tools, not authenticity checking against a malicious compiler, forged Cargo stdout or a repository author who changes both implementation and its tests.

`test-ci-gates.sh --release` makes its profile mutation only after copying tracked current files into a private mktemp tree, using NUL-separated names and preserved script modes. It assigns a separate Cargo target directory, preserves the pin/configuration, and requires both a nonzero guard status and the expected diagnostic. An unrelated compiler failure is rejected as insufficient evidence; an unexpectedly successful mutated gate is also rejected. Independent controlled execution verified the precise single insertion beneath `[profile.release]`, exact Cargo argument vector, copied working directory, sibling private target, absence of .git/untracked sentinel, unchanged source manifest and cleanup. Real execution then confirmed this logic rejects the actual profile flip.

**Workflow authority and profile handling.** No new secret, environment-derived shell interpolation, permission widening, action version, trigger or cache-key change occurs. Existing read-only contents token, nonpersisted checkout credentials and SHA-pinned actions remain. Added steps are blocking inside existing required job names. Private negative compilation cannot reuse the normal target tree. Hosted job workspaces isolate sibling jobs; this change does not claim to make simultaneous local builds sharing hello.bin safe.

The kernel job builds release userland before release kernel build/clippy, then immediately restores debug userland before debug perf build/lint. The BSP checks image existence and changes, not image profile, making this ordering substantive. Cargo feature/profile flags are before the clippy delimiter. Supplied hosted logs corroborate 117-byte debug → 69-byte release → 117-byte debug restoration. These are compilation gates; T-034 owns release guest execution.

### 3. Memory safety

| Standard item | Outcome and adversarial justification |
|---|---|
| S12 — New unsafe satisfies unsafe-policy | **N/A.** No unsafe operation, enclosing production cfg or safety-reasoning change exists; test imports do not require an audit amendment. |
| S13 — Safety invariants hold for every call site | **Flagged — existing HIGH T-038, expressly excluded.** Could a valid caller assume x2 survives? The unchanged shim declares input-only x2 while the kernel overwrites saved x2. No operand/caller/compilation boundary is changed here; this approval does not affirm that existing invariant. |
| S14 — No uninitialized memory exposed | **OK for delta.** No buffer initialization, assembly output or runtime memory-access change can newly expose bytes. |
| S15 — No use-after-free; pointer lifetimes justified | **OK for delta.** No allocation, raw-pointer construction, lifetime or ownership changes are introduced. |
| S16 — No aliasing violations | **OK for delta.** Import cfgs introduce no reference or mutation; existing unsafe contracts are not newly certified. |

T-038 remains HIGH at `userland/tyrne-user/src/lib.rs:107` versus `bsp-qemu-virt/src/syscall.rs:224`. Read-only source inspection confirms the input-only/write-back mismatch remains; Git-object comparison confirms both files are unchanged. Host Miri, successful builds, host regression tests or an observed boot cannot downgrade or prove away this assembly contract defect. T-030's approval is restricted to the enforcement delta, not whole-kernel soundness. Unlike T-037, this change narrows no predicate surrounding an unsafe site and needs no corresponding UNSAFE-2026-0033 amendment.

### 4. Kernel-mode discipline

| Item | Outcome and adversarial justification |
|---|---|
| S17 — No ISR allocation | **N/A.** No interrupt handler or kernel allocation path changes. |
| S18 — Kernel loops bounded with termination | **N/A.** No kernel loop changes; finite tracked-file copying is host tooling, not a new attacker-driven kernel loop. |
| S19 — Critical sections minimized | **N/A.** No scheduler state, synchronization or IRQ-masked region changes. |
| S20 — No new hot-path kernel panic | **OK for delta.** New failures are host command exits; the production panic/error behavior is untouched. |
| MP-1 — Typed allocation-exhaustion error (master-plan extra, not a standard checkbox) | **N/A.** No kernel allocation or exhaustion handling changes. Host temp/copy/build failures cannot satisfy the intended positive/negative evidence contracts merely by failing. |

The new jobs consume host compilation time/disk; they do not enlarge kernel resource limits. Guest performance is not inferred from CI step wall time. Existing runtime loop/critical-section debt remains outside this scoped delta.

### 5. Cryptography

| Standard item | Outcome and adversarial justification |
|---|---|
| S21 — Reviewed primitives; no homemade crypto | **N/A.** No primitive, algorithm or protocol is added. |
| S22 — Keys absent from logs, errors and Debug | **N/A.** No key material or key handling is introduced. |
| S23 — Constant-time comparisons where needed | **N/A.** Test names and profile metadata are public; no secret-dependent comparison changes. |
| S24 — Acceptable randomness source | **N/A.** No security RNG changes. Host mktemp provides exclusive temporary-file creation, not cryptographic capability generation. |
| S25 — Correct nonce/IV/salt handling | **N/A.** No nonce, IV or salt operation changes. |

### 6. Secrets and logging

| Standard item | Outcome and adversarial justification |
|---|---|
| S26 — No secrets in diagnostic channels | **OK.** Could the new logs reveal capability bits or credentials? New output is fixed gate text and ordinary test/build diagnostics; no secret argument is added. Ordinary success/error cleanup was observed. |
| S27 — Sensitive Debug impls redact or are absent | **N/A.** No formatting implementation or sensitive type changes. |

The profile flip affects only the copied tree. The real release profile still uses the false default; no production console output is enabled by the probe. The contract concerns the user-facing syscall's presence, not removal of every kernel diagnostic. No signal/kill cleanup guarantee is asserted by this review.

### 7. Dependencies

| Standard item | Outcome and adversarial justification |
|---|---|
| S28 — New dependencies evaluated under policy | **N/A.** No crate, action, binary dependency or lockfile addition/upgrade occurs. Existing shell/Cargo utilities implement the new host checks. |
| S29 — Dependency trust category understood | **OK for delta.** Could build tooling become privileged runtime code? New shell orchestration remains host-only; no additional code is linked into the kernel. |
| S30 — cargo-vet trust decisions updated | **N/A.** Dependency graph/trust decisions are unchanged; no new audit decision is necessary or claimed. |

Pinned toolchain and lockfile are byte-preserved. There is no proprietary blob addition. Userland remains source-built under ADR-0039; this review did not write the shared image.

### 8. Threat-model impact

| Standard item | Outcome and adversarial justification |
|---|---|
| S31 — Reconciled with security-model.md | **OK.** Could a developer configuration error expose a debug syscall to hostile userspace? The new gate detects the disappearing-test failure mode. Runtime capability, memory, fault, DMA and boot trust boundaries remain unchanged. |
| S32 — Model changes updated or follow-up linked | **N/A — no model shift.** No new principal, authority, communication path or attacker class is introduced. T-034 retains runtime smoke and T-065 the explicit debug feature; this gate claims neither. |

Accepted ADR-0031 governs the capability-plus-debug contract, ADR-0039 the explicit image build, and ADR-0040 the reviewed development sequence and CI scope. Standards changes implement those decisions and do not select a new policy. The threat model's aspirational whole-system guarantees are not treated as proof that all existing implementation debt is resolved. A host release test cannot establish target-specific SVC execution; a future target-specific regression requires complementary runtime evidence.

### Architectural principles P1–P12

| Principle | Disposition |
|---|---|
| P1 — No ambient authority | **OK:** release denial is enforced; no new runtime privilege is granted. |
| P2 — Smallest defensible TCB | **OK:** production code is unchanged; added shell runs only on host verification. |
| P3 — Drivers in userspace | **N/A:** no driver or subsystem placement change. |
| P4 — Checks at every trust boundary | **OK for delta:** existing capability/mapping checks are preserved; CI evidence now fails closed. |
| P5 — Rust kernel, audited unsafe | **OK for delta:** shell is tooling; no new unsafe approval or assembly-soundness claim. |
| P6 — HAL separation | **OK:** cfg-scoped test imports add no hardware dependency to production kernel code. |
| P7 — No proprietary blobs | **OK:** no binary addition; matching userland is built from source. |
| P8 — ADR decisions | **OK:** Accepted ADR-0040 precedes downstream standards; ADR-0031/0039 contracts are preserved. |
| P9 — English repository artifacts | **OK:** changed source, diagnostics, documentation and review artifacts are English. |
| P10 — Mermaid diagrams | **N/A:** no diagram addition. |
| P11 — Reproducibility | **OK for delta:** pin/lockfile unchanged, matching image sequence explicit, probe target private. This is not a bit-for-bit reproducibility audit. |
| P12 — Complete declared scope | **OK:** concrete T-030 gates and negative checks are present; later runtime work and final human review remain explicitly pending. |

### Independent verification

Executed on `aarch64-apple-darwin`, Rust `1.94.0-nightly (86a49fd71 2026-01-14)`, LLVM 21.1.8, selected by `nightly-2026-01-15`; `/bin/bash` 3.2.57. Python TemporaryDirectory managed private roots and cleanup. The real positive guard used a private CARGO_TARGET_DIR/TMPDIR; the real negative helper created its own isolated copied tree/target beneath that private TMPDIR. Neither wrote a shared kernel ELF or hello.bin. Only `--release` probe mode was executed.

| Real check | Observed result |
|---|---|
| `/bin/bash tools/check-release-tests.sh` | Exit 0; both exact test names passed, 2 passed / 0 failed / 247 filtered. |
| `/bin/bash tools/test-ci-gates.sh --release` | Harness exit 0; real profile flip rejected with guard exit 1 and expected diagnostic. |
| Cleanup inspection | No gate logs or probe roots remained under private TMPDIR; outer target/root removed on scope exit. |
| `git diff --check 8437158..5cd9ee8` | Exit 0. |
| Git source-object comparison | Production ABI/dispatch prefix, shim/BSP syscall, unsafe log, toolchain and lockfile unchanged. |

Controlled guard execution used the actual script in private paths containing spaces and glob metacharacters, a deterministic Cargo stub, and cleanup checks after every case:

| Case | Expected / observed exit |
|---|---|
| Both exact passing lines plus two-pass summary | 0 / 0 |
| Same passing lines in reversed order | 0 / 0 |
| Zero tests | 1 / 1 |
| Missing ABI line | 1 / 1 |
| Missing dispatch line | 1 / 1 |
| Wrong module-qualified ABI name | 1 / 1 |
| Duplicate ABI line replacing dispatch evidence | 1 / 1 |
| Required ABI test ignored | 1 / 1 |
| Failed summary | 1 / 1 |
| Third passing matching test, three-pass summary | 1 / 1 |
| Extra ignored matching test, required two still pass | 0 / 0 |
| Cargo 101 despite exact green output | 101 / 101 |
| Unexpected guard argument | 2 / 2 |

Three controlled executions of the actual probe and actual guard additionally checked the profile insertion, target/cwd isolation, exact Cargo argv, exclusion of .git/untracked sentinel, unchanged original manifest and complete cleanup:

| Probe case | Expected / observed harness result |
|---|---|
| Mutated Cargo returns zero-test success | Exit 0: guard exit 1 with matching diagnostic accepted as intended rejection. |
| Unrelated compiler error, Cargo 101 | Exit 1: no expected guard diagnostic, so no false-positive evidence. |
| Mutation unexpectedly leaves exact green two-test output | Exit 1: successful guard is rejected as an ineffective negative experiment. |

Evidence files: `/tmp/tyrne-b21-t030-round2-security-real.log`, `/tmp/tyrne-b21-t030-round2-security-matrix.json`, `/tmp/tyrne-b21-t030-round2-security-probe-matrix.json`. Stubbed outcomes establish parser, pipeline and harness behavior; the real runs supply complementary actual compilation/test evidence. No failed fixture/check was accepted.

### Supplied hosted/local evidence and limits

I inspected parent-fetched `/tmp/tyrne-b21-step4/hosted-run.json`, `hosted-fastlane.log`, and `hosted-kernel.log`. Metadata binds [run 38179424325](https://github.com/HodeTech/Tyrne/actions/runs/38179424325) to `c716ae3d312b1a6213ec35346a87940a79af3465` with success in all five jobs. Relevant log entries show 46 HAL + 249 kernel + 58 test-HAL + 3 doc = **356 release passes**, with two existing ignored HAL doctests; exact narrow test passes; guard PASS; and profile-flip rejection at exit 1. Kernel entries show the 117 → 69 → 117-byte image order, release kernel build/clippy and final debug perf build/clippy. These are independently inspected supplied logs, not independently fetched/re-executed hosted checks. Later commits through reviewed HEAD change documentation only.

The coordinator additionally reports exact reviewed HEAD `5cd9ee8` green in all five jobs at [run 38180378759](https://github.com/HodeTech/Tyrne/actions/runs/38180378759), based on its read-only GitHub metadata inspection. I did not fetch or inspect that later run's logs. The earlier inspected logs establish the executable behavior; the later metadata is parent-supplied exact-HEAD evidence.

Broader local implementation results are parent/task-record evidence: fmt, host/debug/release/perf/userland clippy, debug/release/perf builds, **366 debug / 356 release host passes**, Miri **366** with no UB failure and existing warnings, 59 QEMU argument fixtures and restored debug image SHA `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`. I did not repeat that entire suite. The task's local 1.49 s and hosted 13 s release timings concern build/test overhead, not guest performance.

Limits: no full unchanged dispatcher/kernel audit, broad unsafe-log reconciliation, full-suite Miri/stable rerun, additional bare-metal/profile build, actual QEMU/EL0 or hardware/SMP execution, bit-identical build comparison, cryptographic review, hostile termination stress, live protection audit or independent hosted fetch. No current execution result settles T-038. No first-main, post-merge or release-runtime coverage is claimed.

### Findings, completion and verdict

**No new security finding and no requested source correction.** The 32 standard checkbox items plus the one master-plan allocation item, all eight axes and P1–P12 are explicitly disposed. The unchanged HIGH T-038 issue is retained as flagged/excluded without severity reduction. Round 1's corrected distinction between additional passing and additional ignored matching tests is independently reproduced.

**Approve Round 2 for `8437158..5cd9ee8`.** All applicable changed-surface items are OK; the remaining flagged invariant belongs to unchanged T-038 and is outside this approval. This is the second independent security pass for T-030, not a whole-system soundness finding, Done promotion, final PR approval or merge authorization. The coordinator must publish this full result/cross-reference/index and accurate review trailer in its authorized recording follow-up; final human PR review remains pending.
