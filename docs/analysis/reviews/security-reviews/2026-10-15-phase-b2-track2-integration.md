# Security review 2026-10-15 — Track B.2-2 integrated Step 13

- **Change:** development, cumulative ab847eee..7d1eca0;18 documentation/evidence paths.
- **Reviewer:** independent dedicated R1 SECURITY and different fresh R2 SECURITY; coordinator consolidation, no human approval attributed.
- **Separation from code review:** distinct contexts/empty checklists; same-round peer reports withheld before freeze. Root reads and reconciles all frozen originals. No invented hours-long gap or extra peer-review round.
- **Scope:** explicitly requested documentary authority/evidence assurance; no new runtime security-standard trigger or unsafe delta.
- **Unsafe audit cross-reference:** N/A; no runtime/unsafe/audit-entry modification or new soundness proof.
- **Code-review cross-reference:** [five-role record](../code-reviews/2026-10-15-phase-b2-track2-integration.md).
- **Evidence:** [complete original reports](../../reports/2026-10-15-phase-b2-track2-final-evidence/complete-review-reports.json) and [immutable identities/archives](../../reports/2026-10-15-phase-b2-track2-final-evidence/review-publication-manifest.json).

The following eight axes retain explicit dispositions for all32 literal standard prompts plus the master's additional allocation prompt. Original pre-repair flags and each reviewer's actual commands, readings, helper QA and limits remain in the full originals; current supplemental navigation disposition reflects the verified repair.

## 1. Capability correctness

- **S01: N/A — no privileged runtime operation is introduced.** Every privileged operation introduced by this change requires a capability.
- **S02: N/A — no capability requirement changes.** The capability required is the **narrowest** one that permits the operation (no privilege escalation by accepting a broad capability where a narrow one would do).
- **S03: N/A — no capability-check path or side effect changes.** Capabilities are checked **before** observable side effects. A failed check does not leak information that the call was attempted.
- **S04: N/A — no transfer implementation changes.** Capability transfer (if any) is move-only; no accidental cloning.
- **S05: N/A — no duplication implementation changes.** Capability duplication (if intended) itself requires an explicit `Duplicate`-style authority.
- **S06: N/A — no revocation implementation changes; deferred cross-table limits are retained.** Capability revocation (if applicable) takes effect atomically; no partial state where the revocation is half-applied.

## 2. Trust boundaries

- **S07: N/A — no kernel input-validation path changes.** Every input crossing from userspace to the kernel is validated before use.
- **S08: N/A — no userspace pointer operation changes.** Pointers from userspace are **never** dereferenced in kernel mode without going through a validated mapping.
- **S09: N/A — no kernel buffer or mapped-region operation changes.** Buffer lengths provided by userspace are range-checked against the actual mapped region.
- **S10: N/A — no IPC parser or message representation changes.** Message contents from userspace are parsed into typed structures; no raw bytes are consumed in privileged code.
- **S11: N/A — no IPC authority transfer changes.** Cross-task IPC does not grant the receiver any authority the sender did not have or did not explicitly transfer.
- **Supplemental evidence trust: OK after repair.** SECURITY-R1-01 was one Low affecting two README targets; root fixed7d1eca0, original SECURITY verified the committed repair and different fresh R2 independently verifies all 58 targets. Original flag remains in the immutable report.

## 3. Memory safety

- **S12: N/A — no unsafe block introduced or modified.** Any new `unsafe` block meets [unsafe-policy.md](../../../standards/unsafe-policy.md).
- **S13: N/A — no Safety contract or call site changes in this delta; the older HAL doc-comment equivalence is independently bounded above.** Invariants stated in `# Safety` sections hold for every call site, not only "the usual" one.
- **S14: N/A — no memory initialization or exposure path changes.** No uninitialized memory is exposed. Where a buffer is declared but only partially filled, the unused portion is zeroed or the buffer is returned as `MaybeUninit`.
- **S15: N/A — no object lifetime or raw-pointer operation changes.** No use-after-free. Lifetimes on raw pointers are reasoned about explicitly.
- **S16: N/A — no mutable-pointer operation changes.** No aliasing violations. Mutable pointers to the same memory do not coexist.

## 4. Kernel-mode discipline

- **S17: N/A — no ISR implementation changes.** No allocation in interrupt service routines.
- **S18: N/A — no kernel loop changes; no universal termination guarantee is claimed.** No unbounded loops in kernel mode; every loop has a documented termination.
- **S19: N/A — no critical-section or scheduler implementation changes.** Critical sections are minimized. Scheduler state is held for as short a time as possible.
- **S20: N/A — no kernel panic path changes; existing fault limits remain stated.** No new kernel panic introduced on a hot path.
- **M33 — N/A.** “Every allocation path returns a typed error, not a panic, on exhaustion.” No allocation path changes; the full security model explicitly rejects a universal recoverable-exhaustion guarantee for the existing kernel.

## 5. Cryptography (when present)

- **S21: N/A — no cryptographic primitive introduced; SHA-256 identifies evidence bytes and is not a boot/authenticity claim.** No roll-your-own primitives. If a primitive is introduced, it is a well-known algorithm from a reviewed crate (or, if truly novel, it comes with a separate ADR and a cited proof or analysis).
- **S22: N/A — no key-handling implementation introduced.** Keys are never logged, returned in error messages, or exposed via `Debug`.
- **S23: N/A — no secret comparison or timing-sensitive algorithm introduced.** Constant-time comparisons are used where timing leaks matter.
- **S24: N/A — no randomness source introduced.** Randomness comes from an acceptable source — not `rand::thread_rng` with no seeding story.
- **S25: N/A — no nonce, IV or salt processing introduced.** Nonces, IVs, and salts are handled correctly per the primitive's contract.

## 6. Secrets and logging

- **S26: OK — retained public demo/CI evidence and source excerpts introduce no observed secret material; addresses and timings remain explicitly public diagnostic evidence, not a blanket redaction proof.** Secrets (keys, tokens, capability bits) are not included in logs, panic messages, debug output, or error types.
- **S27: N/A — no Debug implementation changed; retained capability redaction prose does not generalize to every handle/diagnostic.** `Debug` impls on security-sensitive types redact sensitive fields (or are not implemented at all).

## 7. Dependencies

- **S28: N/A — no package/toolchain dependency added or changed.** Any new dependency has been evaluated under [infrastructure.md](../../../standards/infrastructure.md) dependency-addition rules.
- **S29: N/A — no new build-time or kernel-linked dependency.** The dependency's trust model is understood. A build-time-only crate is very different from a kernel-linked crate.
- **S30: N/A — no cargo-vet trust change; reports do not claim dormant audit/vet ran.** `cargo-vet` trust decisions are updated accordingly.

## 8. Threat model impact

- **S31: OK — full security-model and SECURITY boundary read; integration preserves trusted-image, lifecycle, DMA, fault and whole-phase limits.** The change is reconciled with the documented threat model in [`docs/architecture/security-model.md`](../../../architecture/security-model.md).
- **S32: N/A — no threat-model shift or new runtime service exposure introduced.** If the change reshapes the threat model, the PR includes the threat-model update or links to a follow-up PR scheduled imminently.


## Evidence, procedure and remaining authority

Both fresh rounds independently compare58 original blocks/owners/hashes/target links,156 literal criterion tuples, nine markers/exact comment-only source patches,62 original smoke-file bindings and23 structured probe outcomes, phase census and unchanged protected domains. Each SECURITY reviewer reads both complete production traces and executes the existing checker on both local Python runtimes:397/7163/925/zero. Historical0033 execution and404 hosted source records remain attributed to their original runners; raw probe traces/full hosted log are not falsely claimed manually reread. Policy verification is offline against the root's recorded read-only snapshot; reviewers do not claim fresh live settings queries.

R1's prerequisite truncation/order limitation and initial scratch mkdir TMPDIR omission remain disclosed; final all-text completion does not backdate compliance. R2 completes its separately recorded full mandatory prerequisite stage before any scope inspection. Root reads all complete final reports and actual R1 fix verification, validates the Low and reconciles outcomes. Complete reports and bounded source/scripts/streams are retained losslessly; archived paths are provenance, not executable navigation.

Exact7d1eca0 hosted PR/push each pass seven jobs/six required app15368 contexts,161/124 methods and397/7163/925/zero; the root checkpoint is distinct from the reviewers' historical404 inspection and later final filing tip. No exact hosted Python version, first-main execution, universal parser/resource/sandbox/kernel guarantee or human approval is inferred.

## Verdict

**Approve — both independent security rounds complete at7d1eca0.** SECURITY-R1-01 is one Low, fixed in7d1eca0 and actually verified by the original finder and different fresh R2. No new R2 or unresolved issue remains. All eight axes, literal32+M33 and P1–P12 are explicitly assessed in the original reports; no runtime security certification follows from documentation review.

T-045–T-056 remain In Review/no date_done. Final filing-tip CI is recorded in PR #49 before handoff; maintainer PR/SECURITY wording review and authorized merge remain. HIGH T-038 and the whole-phase C/D gates retain their own future work.
