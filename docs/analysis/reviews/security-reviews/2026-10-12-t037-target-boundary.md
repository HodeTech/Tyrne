# Security review 2026-10-12 — T-037 target boundary

> **Current security-review state (2026-10-12):** both independent security rounds approve T-037's compilation-boundary narrowing. Round 2 also verifies the committed `69a4109` audit/lifecycle follow-up. The existing HIGH T-038 register-clobber defect remains expressly excluded. This is not Done promotion or merge certification. The original round-1 report below, including its pending-state wording, is preserved as dated history; the [round-2 report](#round-2) follows it.

Round 1 approves T-037's compilation-boundary narrowing in `960bdef..f2d577f`: no new blocking security defect was found. This verdict does not approve the existing `console_write` register-clobber contract, complete T-037, or certify a merge. The required two-round review cycle remains pending; the fresh round-2 result will be appended after the intervening follow-up commit.

- **Change:** `development`, `960bdef..f2d577f96b4c98f3c0998f538304e38d4232d409`; [T-037](../../tasks/phase-b2/T-037-userland-bare-metal-cfg-gate.md).
- **Reviewer:** fresh independent Codex security agent `/root/b21_step1_round1_security`.
- **Date:** 2026-10-12, Europe/Istanbul.
- **Separation from code review:** distinct security pass, independent of implementation and ordinary code review; [paired code-review artifact](../code-reviews/2026-10-12-t037-target-boundary.md).
- **Unsafe audit cross-reference:** [UNSAFE-2026-0033](../../../audits/unsafe-log.md#unsafe-2026-0033--tyrne-user-el0-syscall-svc-0-shims).
- **Scope:** the three changed source files, accompanying audit amendment and task records; relevant syscall consumers and the [security model](../../../architecture/security-model.md).
- **Context read:** AGENTS, CLAUDE, current roadmap, every numbered ADR present in numerical order, all standards, both review skills, security master plan, security model and the prior [T-028 security review](2026-06-01-T-028-el0-userspace-wireup.md). Truncated document reads were repaired.
- **Mutation boundary:** the review itself was read-only, apart from build artifacts and temporary verification files. A subsequent explicit instruction authorized recording this report and its security-review index row only. Audit/lifecycle follow-up and committing belong to the coordinating agent.

## 1. Capability correctness

| Checklist item | Outcome, adversarial question and justification |
|---|---|
| Privileged operations require capabilities | **OK.** Could ARM host selection invoke an unintended privileged operation? Hosted targets now exclude both Tyrne SVC wrappers; bare-metal operations remain unchanged. |
| Narrowest sufficient capability | **OK.** Could the narrowing broaden console authority? No capability type, handle, right or grant changes; `console_write` retains the existing `DebugConsole`/`CONSOLE_WRITE` check. |
| Checks before side effects; no failed-check leak | **OK.** Could a failed capability check emit bytes? The unchanged dispatcher validates the capability before range checks, copying or emission (`kernel/src/syscall/dispatch.rs:236`). |
| Move-only capability transfer | **N/A.** Could this introduce accidental capability copying? No transfer or capability representation changes. |
| Explicit duplication authority | **N/A.** Could this duplicate authority implicitly? No duplication operation is introduced or modified. |
| Atomic revocation | **N/A.** Could target selection race with revocation? Selection occurs at compilation; no revocation or concurrency path changes. |

`task_exit` continues to act solely on the calling task's identity under [ADR-0031](../../../decisions/0031-initial-syscall-set.md); this change adds no authority over another task.

## 2. Trust boundaries

| Checklist item | Outcome, adversarial question and justification |
|---|---|
| Inputs validated before kernel use | **OK.** Could arbitrary target strings select the Tyrne link path? Both target fields require exact equality; malformed, absent and non-Unicode values fail closed in the independent matrix. Runtime syscall argument handling is unchanged. |
| User pointers restricted to validated mappings | **OK.** Could narrowing expose a pointer to a new kernel consumer? No pointer construction or consumer changes; the existing console path retains whole-range and per-page USER checks before emission. |
| Buffer lengths range-checked | **OK.** Could a different target interpretation widen the supplied range? The slice pointer/length operands and kernel validation remain identical. |
| Typed message parsing | **N/A.** Could malformed messages exploit a new decoder? No message format or parser changes. |
| IPC cannot grant excess authority | **N/A.** Could cross-task communication bypass an authority check? No IPC or transfer code changes. |

The compiler predicate and linker predicate agree: `aarch64 && none`. The normal ARM host uses an ordinary hello `main`; it does not select `_start`, the custom panic handler, `hello.ld`, or the SVC bodies.

## 3. Memory safety

| Checklist item | Outcome, adversarial question and justification |
|---|---|
| Unsafe policy compliance | **OK for narrowing; recording pending.** Could an unsafe site become reachable on an additional target? The selected target set strictly shrinks. Existing comments and audit references remain; the amendment records locations, invariants and alternatives. No new unsafe identifier is warranted. |
| Safety invariants hold for every caller | **Flagged — existing T-038, outside this approval.** Could a valid caller rely on a live value in `x2` surviving the trap? Yes: the existing input-only declaration conflicts with kernel write-back. This review expressly withholds approval of that invariant. No new `unsafe fn` or `# Safety` contract is introduced. |
| No uninitialized memory exposed | **OK for delta.** Could host compilation read uninitialized asm outputs? Hosted expansion contains no SVC sites; bare-metal output declarations and bodies are unchanged. |
| No use-after-free; raw-pointer lifetimes | **OK for delta.** Could the new branch retain a buffer pointer? Host stubs do not access or retain arguments; bare-metal borrowing and pointer lifetimes are unchanged. |
| No aliasing violations | **OK for delta.** Could the host branch create a new conflicting reference? No new references, raw-pointer operations or mutations are introduced. This does not clear T-038's separate assembly-contract defect. |

**Explicit unsafe verdict:** Reviewed the target guards enclosing `userland/tyrne-user/src/lib.rs:101–114` and `:140–147`; I approve the compilation-boundary reasoning that restricts these existing unsafe operations to `all(target_arch = "aarch64", target_os = "none")`. I do **not** affirm the existing `console_write` SAFETY comment's complete register-discipline claim. Original unsafe bodies and operands are preserved.

## 4. Kernel-mode discipline

| Checklist item | Outcome, adversarial question and justification |
|---|---|
| No ISR allocation | **N/A.** Could an interrupt newly allocate? No interrupt code or allocation is changed. |
| Bounded kernel loops | **N/A.** Could malformed target values cause a runtime kernel loop? Build-time comparisons introduce no kernel execution path. |
| Minimal critical sections | **N/A.** Could the change extend a lock or IRQ-masked region? No synchronization or critical section changes. |
| No new hot-path kernel panic | **OK.** Could a host stub panic affect the Tyrne kernel? Stubs exist only outside the bare-metal configuration; explicit host calls would panic locally. Existing build-script `expect` remains build-time only. |
| Typed allocation-exhaustion errors | **N/A.** Could resource exhaustion now panic in the kernel? No kernel allocation or error path changes. |

## 5. Cryptography

| Checklist item | Outcome, adversarial question and justification |
|---|---|
| Reviewed primitives | **N/A.** Could a new primitive be weak? No cryptography introduced. |
| Keys absent from diagnostics | **N/A.** Could new key handling expose material? No key material or handling introduced. |
| Constant-time comparisons | **N/A.** Could target comparisons expose a secret? Architecture and OS names are public build metadata. |
| Acceptable randomness | **N/A.** Could predictable randomness weaken authority? No random source or use changes. |
| Nonce/IV/salt correctness | **N/A.** Could reuse break a cryptographic contract? No nonce, IV or salt operations. |

## 6. Secrets and logging

| Checklist item | Outcome, adversarial question and justification |
|---|---|
| No secrets in logs, panic output, debug prints or errors | **OK.** Could hostile target text inject diagnostic/linker directives? Target values are compared, never printed; the negative newline-injection case emitted only the two fixed rerun directives. No new runtime diagnostics expose arguments. |
| Sensitive Debug implementations redact | **N/A.** Could newly derived formatting disclose a capability? No type or `Debug` implementation changes; the existing syscall status type is unchanged. |

`CARGO_MANIFEST_DIR` supplies the pre-existing linker path. This change does not create or claim protection against a compromised build environment.

## 7. Dependencies

| Checklist item | Outcome, adversarial question and justification |
|---|---|
| New dependencies follow add-dependency | **N/A.** Could this import unreviewed code? No manifest, lockfile or dependency addition. |
| Trust category understood | **N/A.** Could build-time code move into the kernel? No dependency role or linkage changes; existing in-tree userspace dependency remains. |
| cargo-vet decisions updated | **N/A.** Could an unaudited dependency slip through? No dependency graph or trust decision changes. |

## 8. Threat-model impact

| Checklist item | Outcome, adversarial question and justification |
|---|---|
| Reconciled with security model | **OK.** Could the target predicate become an authorization boundary? It selects the intended compilation ABI and reduces accidental hosted execution. Runtime authority remains enforced by unchanged kernel capability and mapping checks. |
| Model changes documented or tracked | **N/A — no model shift.** Does this defend against a hostile compiler or forged custom target? No such protection is claimed. Build configuration remains trusted; a custom `aarch64`/`none` target still selects the bare-metal branch. No security-model amendment is needed. |

## Findings and recording follow-up

**No new security findings requiring a source fix.**

**Existing HIGH issue retained outside this approval:** `userland/tyrne-user/src/lib.rs:107` declares `x2` input-only, while `bsp-qemu-virt/src/syscall.rs:224` overwrites the saved register on return. [T-038](../../tasks/phase-b2/T-038-console-write-x2-clobber.md) explicitly tracks this. Both the operand and surrounding SVC bodies are unchanged by T-037. Passing host Miri and matching bare-metal bytes do not establish assembly soundness.

**Minor pending audit bookkeeping at reviewed commit `f2d577f`:** `docs/audits/unsafe-log.md:770` has the provisional introducing-commit reference, and `:775` records review pending. Fill in `f2d577f96b4c98f3c0998f538304e38d4232d409`, append the actual reviewer/result dated October 12, preserve the historical pending statement, and record the artifact/index/trailer in the authorized follow-up. These are expected post-review recording steps; they were not represented as complete during this review. The coordinating agent owns the audit and lifecycle follow-up; the artifact and index are recorded separately under the reviewer agent's subsequent artifact-only authorization.

## Independent verification

All successful checks ran against `f2d577f` on `aarch64-apple-darwin`, pinned `nightly-2026-01-15`:

- `cargo test --workspace --exclude tyrne-bsp-qemu-virt --quiet`: **366 passed**, two existing ignored HAL doctests.
- `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt --quiet`: **366 passed**, two ignored doctests; existing optimization/provenance warnings. This exercises hosted code, **not SVC assembly**.
- Compiled `userland/hello/build.rs` using `rustc`, then ran **15 environment cases**: only exact `aarch64`/`none` emitted the linker argument. ARM macOS/Linux/Windows, x86 targets, missing/empty fields, case mismatch, newline injection and non-Unicode OS values did not.
- `rustc --print cfg` checked ARM macOS, ARM Linux, ARM bare-metal and x86 Linux target identities.
- `rustc --crate-type lib --edition=2021 --target … -Zunpretty=expanded userland/tyrne-user/src/lib.rs`: ARM macOS expansion contains **zero SVC sites and host stubs**; bare-metal expansion contains **two SVC sites and no host stubs**.
- `cargo build -p tyrne-userland-hello --target aarch64-unknown-none --quiet`, followed by pinned `rust-objcopy -O binary` into a temporary file: **117 bytes**, SHA-256 `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`.
- Git-object comparison: the previous unsafe log is an **exact byte prefix** of the new log; **1542 bytes appended**. Both source files' non-comment, non-attribute bodies are identical.
- The tracked working tree remained clean throughout the read-only review; this artifact and index row were written only after separate authorization.

The environment matrix was `(arch, OS) = (aarch64, none)`, `(aarch64, macos)`, `(aarch64, linux)`, `(aarch64, windows)`, `(x86_64, none)`, `(x86_64, linux)`, `(missing, none)`, `(aarch64, missing)`, `(missing, missing)`, `(empty, empty)`, `(aarch64, None)`, `(aarch64, none\n)`, `(aarch64\n, none)`, `(aarch64, none\ncargo:rustc-link-arg=-evil)`, and `(aarch64, byte 0xff)`. Each process exited successfully; positive stdout contained one linker directive and two rerun directives, while every negative contained only the two rerun directives.

Parent-reported clippy, workspace check and QEMU smoke results are supporting evidence; this reviewer did not independently repeat those gates. The original baseline binary was not rebuilt by this reviewer; the independently produced current binary matches its recorded hash.

## Round-1 verdict and remaining cycle

**Approve T-037's compilation-boundary narrowing in `960bdef..f2d577f`.** No new blocking security defect was found. Existing T-038 remains at its original HIGH severity, separately tracked and expressly excluded from assembly-soundness approval; it is not downgraded to justify this verdict. The narrowing introduces no new operation and reduces the target set that can compile the existing operations.

The audit-recording follow-up and fresh round 2 are still pending. A later round-2 result will be appended to this artifact after review of the intervening committed follow-up. This round-1 result does not promote T-037 to Done, complete the two-round cycle, approve T-038, or certify a merge.

## Round 2

**Approve T-037's compilation-boundary narrowing and the `69a4109` recording follow-up. No new security finding.** This verdict does not approve the existing register-clobber contract, promote T-037 to Done, or certify merge readiness.

- **Reviewer:** `/root/b21_step1_round2_security`, fresh independent security context.
- **Range:** `960bdef..69a4109e12ad814cec9a1fe9cfef3070155b852b` on `development`.
- **Date:** 2026-10-12, Europe/Istanbul.
- **Separation:** dedicated adversarial security pass; no ordinary code-review pass performed by this reviewer. The [paired code review](../code-reviews/2026-10-12-t037-target-boundary.md) is a separate agent's work.
- **Unsafe audit cross-reference:** [UNSAFE-2026-0033](../../../audits/unsafe-log.md#unsafe-2026-0033--tyrne-user-el0-syscall-svc-0-shims).
- **Procedure:** read AGENTS/CLAUDE, current roadmap, numbered ADRs in numerical order, all standards, both applicable review skills, security master plan/model, round-1 reports and prior T-028 security review. Truncated reads were repaired.
- **Mutation boundary:** the verdict pass made no repository edits, commits, branches or external mutations; verification outputs used temporary directories. Subsequent explicit authorization permits only appending this report, adding its current-state note, and updating this security-review index row. Root owns task/current-roadmap/audit completion recording.

### 1. Capability correctness

| Checklist item | Outcome and adversarial justification |
|---|---|
| Privileged operations require capabilities | **OK for delta.** ARM hosted builds can no longer accidentally compile Tyrne SVC wrappers; bare-metal syscall authority checks remain unchanged. |
| Narrowest sufficient capability | **OK.** The predicate introduces no capability, grant or broader right; console access still requires the caller's `DebugConsole` capability and `CONSOLE_WRITE`. |
| Checks precede side effects; failed checks leak no state | **OK for delta.** `kernel/src/syscall/dispatch.rs:236` checks authority before range validation, copying or console emission, and this change does not bypass it. |
| Move-only capability transfer | **N/A.** No transfer or capability representation changes could introduce copying. |
| Explicit duplication authority | **N/A.** No duplication operation is added or modified. |
| Atomic revocation | **N/A.** Compile-time target selection changes no revocation or concurrency operation. |

`task_exit` continues to affect only the current task under ADR-0031; it gains no authority over other tasks.

### 2. Trust boundaries

| Checklist item | Outcome and adversarial justification |
|---|---|
| Inputs validated before kernel use | **OK for delta.** Runtime syscall inputs are unchanged; independent adversarial build-environment probes confirm that only exact `aarch64`/`none` selects the linker script. |
| User pointers restricted to validated mappings | **OK for delta.** The unchanged console dispatcher retains authority, whole-range and per-page USER checks before emission; no new pointer consumer appears. |
| Buffer lengths range-checked | **OK for delta.** Pointer/length operands and kernel validation are unchanged, so the new predicate does not enlarge the accessible buffer range. |
| Typed message parsing | **N/A.** No new message format, decoder or parsing boundary exists. |
| IPC cannot grant excess authority | **N/A.** No IPC operation or authority-transfer path changes. |

The source and build predicates agree on `aarch64 && none`. This is an ABI compilation boundary, not a defense against a hostile compiler or forged custom target.

### 3. Memory safety

| Checklist item | Outcome and adversarial justification |
|---|---|
| Unsafe policy compliance | **OK for narrowing.** No new unsafe operation is introduced; the target set strictly shrinks, existing comments/references remain, and UNSAFE-2026-0033 records the changed boundary and distinct reviewer. |
| Safety invariants hold for every caller | **Flagged — existing HIGH, T-038.** A caller may rely on input-only `x2` retaining its value, while the kernel overwrites it; this pre-existing invariant is expressly excluded from approval. |
| No uninitialized memory exposed | **OK for delta.** Hosted expansion contains zero SVC sites, and bare-metal assembly/output declarations are unchanged. |
| No use-after-free; raw-pointer lifetimes | **OK for delta.** Hosted stubs neither retain nor dereference their arguments; bare-metal buffer borrowing and pointer lifetime remain unchanged. |
| No aliasing violations | **OK for delta.** No reference construction, raw-pointer mutation or concurrency change is introduced; this does not clear the separate assembly-contract defect. |

**Explicit unsafe approval:** Reviewed the target guards enclosing `userland/tyrne-user/src/lib.rs:101–114` and `:140–147`; I agree with and approve the changed compilation-boundary reasoning restricting those existing unsafe operations to `all(target_arch = "aarch64", target_os = "none")`. I do not affirm the complete register-discipline claim in the existing `console_write` SAFETY comment.

### 4. Kernel-mode discipline

| Checklist item | Outcome and adversarial justification |
|---|---|
| No ISR allocation | **N/A.** No interrupt or allocation path changes. |
| No unbounded kernel loops | **N/A.** Build-time comparisons introduce no kernel loop; this verdict does not reassess existing console-loop behavior. |
| Minimal critical sections | **N/A.** No lock, IRQ mask or critical section changes. |
| No new hot-path kernel panic | **OK.** Hosted stubs panic only in the hosted program; independent execution confirmed both locally unwind without issuing Tyrne SVCs. |
| Typed allocation-exhaustion errors | **N/A.** No kernel allocation or exhaustion-handling path changes. |

### 5. Cryptography

| Checklist item | Outcome and adversarial justification |
|---|---|
| Reviewed primitives | **N/A.** No cryptographic primitive is introduced. |
| Keys excluded from diagnostics | **N/A.** No key handling is introduced or modified. |
| Constant-time comparisons | **N/A.** Target architecture and OS names are public build metadata, not secrets. |
| Acceptable randomness | **N/A.** No random source or use changes. |
| Correct nonce/IV/salt handling | **N/A.** No such operation exists in the delta. |

### 6. Secrets and logging

| Checklist item | Outcome and adversarial justification |
|---|---|
| No secrets in diagnostic output | **OK.** Target values are compared rather than printed; newline-injection probes produced only fixed rerun directives, and no runtime diagnostic is added. |
| Sensitive Debug implementations redact | **N/A.** No type or formatting implementation changes could disclose capability or secret material. |

`CARGO_MANIFEST_DIR` remains the existing trusted build-environment input; this change makes no claim to sanitize a compromised build environment.

### 7. Dependencies

| Checklist item | Outcome and adversarial justification |
|---|---|
| New dependencies follow add-dependency | **N/A.** No dependency, manifest or lockfile change imports additional code. |
| Trust category understood | **N/A.** No dependency changes category or moves from build-time execution into the shipped image. |
| cargo-vet decisions updated | **N/A.** No dependency graph or trust decision changes. |

The fresh image was generated from source with the existing pinned toolchain; no proprietary blob was introduced.

### 8. Threat-model impact

| Checklist item | Outcome and adversarial justification |
|---|---|
| Reconciled with security model | **OK.** The change reduces accidental hosted execution of the wrong syscall ABI while preserving kernel capability and mapping enforcement; P1, P3 and P7 remain unaffected. |
| Model changes documented or tracked | **N/A — no model shift.** The predicate does not authenticate a Tyrne runtime or protect against malicious build configuration; no such expanded protection is claimed. |

### Findings and record verification

**No new finding requiring correction.**

**Existing HIGH retained:** `userland/tyrne-user/src/lib.rs:107` declares `x2` input-only; `bsp-qemu-virt/src/syscall.rs:224` overwrites the saved `x2` register on return. [T-038](../../tasks/phase-b2/T-038-console-write-x2-clobber.md) remains its explicit owner and is Ready at the reviewed commit. Its severity is not reduced by this approval, passing hosted tests, or matching image bytes.

The round-1 recording follow-up is accurate:

- The unsafe log at `960bdef` is an exact byte prefix of the log at `69a4109`; **2,231 bytes** were added overall.
- `f2d577f` added 1,542 bytes. The follow-up finalizes its amendment's introducing SHA and appends the actual reviewer/result; original audit fields remain intact.
- `docs/audits/unsafe-log.md:777` explicitly limits approval to target selection and preserves the T-038 exclusion.
- `69a4109` contains the actual `Refs: ADR-0040`, `Audit: UNSAFE-2026-0033` and `Security-Review: b21_step1_round1_security` trailers.
- No file under `docs/decisions/` changes in the reviewed range; no Accepted ADR body was rewritten.
- The task opening snapshot is labeled historical; current active-task, review and branch pointers identify T-037 as In Review on development. Second-round review remains pending in the reviewed commit, as expected.
- The repository remained clean, and HEAD remained the reviewed commit during the read-only verification pass. Artifact recording occurred only after the subsequent limited authorization.

### Independent verification and limits

Executed on `aarch64-apple-darwin`, pinned Rust `1.94.0-nightly`, commit `86a49fd71`, LLVM 21.1.8:

- **17 build-script environment cases passed:** exact positive pair; ARM macOS/Linux/Windows; x86 Linux/none; missing and empty fields; architecture/OS case mismatch; newline injection; non-Unicode architecture and OS. Only exact `aarch64`/`none` emitted the linker argument.
- **Cfg expansion:** native ARM hosted library contains zero SVC sites; bare-metal ARM library contains two.
- **Native wrapper execution:** both hosted wrappers called with adversarial argument values panic locally and are caught by `catch_unwind`.
- **Fresh isolated-target bare-metal build:** `cargo build --locked -p tyrne-userland-hello --target aarch64-unknown-none`, then pinned `rust-objcopy`: **117 bytes**, SHA-256 `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`.
- **Source comparison:** after removing comments and applying precisely the intended cfg substitution, both changed Rust source bodies match the baseline exactly.

The exact environment matrix was `(arch, OS) = (aarch64, none)`, `(aarch64, macos)`, `(aarch64, linux)`, `(aarch64, windows)`, `(x86_64, none)`, `(x86_64, linux)`, `(missing, none)`, `(aarch64, missing)`, `(missing, missing)`, `(empty, empty)`, `(AARCH64, none)`, `(aarch64, None)`, `(aarch64, none\n)`, `(aarch64\n, none)`, `(aarch64, none\ncargo:rustc-link-arg=-evil)`, `(aarch64, byte 0xff)`, and `(byte 0xff, none)`. Each negative case emitted only the two expected fixed rerun directives; the positive case additionally emitted exactly one linker directive. The native wrapper probe passed `u64::MAX` as capability/exit code and `[1, 2, 3]` as the console buffer, then asserted both caught panics.

I did not repeat workspace Miri/native tests, clippy, QEMU, stable, release, hosted CI or hardware checks. Round-1 execution evidence remains attributed to those reviewers; no new source change or concern justified repeating full Miri. The original baseline binary was not rebuilt here. The independent fresh binary matches the recorded baseline hash; this proves byte preservation for this build, not assembly soundness.

### Round-2 verdict

**Approve the reviewed T-037 delta and recording follow-up, with the existing HIGH T-038 defect expressly excluded.** Both independent security rounds now approve the narrowing. This result carries no Done-promotion or merge certification; root owns the separate lifecycle/audit completion record.
