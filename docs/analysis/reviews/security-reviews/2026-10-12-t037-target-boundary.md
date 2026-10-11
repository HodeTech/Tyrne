# Security review 2026-10-12 — T-037 target boundary

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
