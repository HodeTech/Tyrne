# Security review 2026-10-12 — T-030 release gates

- **Change:** T-030 on `development`, `8437158..364b746`.
- **Reviewer:** fresh independent `b21_step4_round1_security`, acting on behalf of @cemililik; `gpt-6-astra` / high requested with fresh context.
- **Separation from code review:** separate agent and empty security checklist; no implementation or paired code-review context inherited.
- **Unsafe audit cross-reference:** n/a; test imports only, no unsafe body, predicate or safety-reasoning change. Existing HIGH T-038 remains explicitly excluded.
- **Paired code review:** [code-review artifact](../code-reviews/2026-10-12-t030-release-gates.md).

> **Current reconciliation:** Round 1 Approve, no new security finding. The report's third-test wording was corrected to *third passing matching test* before publication; verdict and evidence are unchanged. The second fresh round and final maintainer PR review remain pending. This follow-up records the distinct approval; it does not retroactively claim a review trailer on the earlier implementation commit or promote Done.

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
