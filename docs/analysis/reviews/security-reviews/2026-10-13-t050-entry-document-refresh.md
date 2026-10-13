# Security review 2026-10-13 — T-050 entry-document refresh

- **Change:** development, cumulative 75de2ba90e151bae33e14d2db4a8278837e7775d..946f45f34f7eac90164adccfcd71e4c7f77c1f8e.
- **Reviewer:** separate fresh Codex security contexts b22_t050_r1_security and b22_t050_r2_security; configuration and actual outcomes below. No human review attributed.
- **Date:** 2026-10-13.
- **Separation from code review:** each security reviewer started with a separate empty context/checklist, independently assessed source and evidence, then consumed actual code reports. Assessments ran in parallel; chronology is preserved below.
- **Unsafe audit cross-reference:** no unsafe code/contract/audit delta; existing UNSAFE-2026-0030 and 0033 inform descriptions, with HIGH T-038 unresolved.
- **Code-review cross-reference:** [paired five-role artifact](../code-reviews/2026-10-13-t050-entry-document-refresh.md).
- **Evidence:** [source-bound verification](../../reports/2026-10-13-t050-entry-document-verification.md), [raw capture inventory](../../reports/2026-10-13-t050-entry-document-evidence/README.md).

## 1. Capability correctness

OK for documentation delta: source-defined rights, per-table revocation, control-plane identity and trusted EL1 demo boundaries are qualified. Both actual eight-axis reports below retain every item and justification.

## 2. Trust boundaries

OK for descriptions: console validation, current EL0 exception path and trusted registration assumptions match source; happy-path smoke is not a hostile-input proof.

## 3. Memory safety

OK for descriptions: R1 C01 corrected the raw table pointer/lifetime/borrow obligations. No unsafe implementation changed; lifecycle, pointer, W^X and ABI limitations remain explicit.

## 4. Kernel-mode discipline

OK for descriptions: cooperative dispatch, completion spin, non-returning exit and panic/fault boundaries are accurately qualified. No runtime availability fix or preemption/idle-IRQ proof is claimed.

## 5. Cryptography

N/A: no cryptographic primitive, key or protocol is introduced or certified.

## 6. Secrets and logging

OK for delta: raw captures contain the reference trusted demo; address/debug diagnostics are qualified and no newly secret-bearing mechanism is introduced.

## 7. Dependencies

N/A for new dependency trust: no dependency/toolchain/CI change. Existing one-off Markdown diagnostics are not the shipping T-056 tool.

## 8. Threat-model impact

OK for documentation delta: current capabilities/fault/teardown limits remain visible, target architecture is distinguished. R2-C01 now accurately preserves the accepted Phase C planning exception. No changed runtime threat model or existing HIGH fix is claimed.

## Verdict

**Approve** — both distinct fresh security contexts approve the corrected documentation scope; zero independently originated security findings, both shared code-origin Low findings corroborated and verified fixed, zero unresolved delta findings. Human review remains pending.

## Both-round consolidation

| Round | Fresh context / configured model / effort | Actual final disposition |
|-------|------------------------------------------|--------------------------|
| 1 code | b22_t050_r1_code / GPT-6.1 Sol / high | Initial Request changes: Low C01; correction independently verified, final Approve at 5236156. |
| 1 security | b22_t050_r1_security / GPT-6 Astra / high | Initial independent zero findings; shared code-origin C01 corroborated, correction verified, final scoped Approve at 5236156. |
| 2 code | b22_t050_r2_code / GPT-6.1 Sol / high | Initial Request changes: Low R2-C01; correction independently verified, final Approve at 946f45f. |
| 2 security | b22_t050_r2_security / GPT-6 Astra / high | Initial independent zero findings; shared code-origin R2-C01 corroborated, correction verified, final scoped Approve at 946f45f. |

Each round used two separate fresh contexts; the second round reused neither first-round reviewer. Code and security assessments ran independently in parallel, followed by actual report cross-reading and source reconciliation. This records the actual chronology, not a sequential code-then-security execution claim. Every reviewer independently completed the literal governance prerequisite read before assessment. Models/effort are coordinator configuration, not reviewer runtime introspection. Full delivered reports below retain exact original verdicts, reading/diagnostic limits, subsequent corrections and reviewer-report QA notes.

R1 C01 is one code-origin Low: first-userspace had called the raw capability-table binding a handle. Commit 523615603f87f6f11f2030db4d6d974c38330f0d distinguishes the address-space handle from the raw table pointer and states caller lifetime/borrow obligations. R2-C01 is a different code-origin Low: Bridge phase had overextended the C/D gate to all work. Commit 946f45f34f7eac90164adccfcd71e4c7f77c1f8e restores ADR-0040's milestone/implementation gate and permitted Phase C planning. Security corroborations do not add duplicate findings. Both rounds end with zero unresolved delta findings.

The coordinator read all four actual reports, including delivered post-fix addenda, and verified their scoped agreement. Canonical publication and lifecycle bookkeeping are not a fifth independent assessment. No executable, build, CI or runtime policy changes occurred. Existing HIGH T-038 remains Ready/unresolved; successful trusted-demo traces do not certify hostile EL0 isolation, general ABI/asm soundness, SMP, strict provenance or real hardware. Maintainer review, Done promotion and publication remain separate.


---

## Retained Round 1 security report

# Security review 2026-10-13 — T-050 Step 6, fresh Round 1

- **Change:** `development`, `75de2ba90e151bae33e14d2db4a8278837e7775d..74f8e837bd13e10b71f517446ae0d108c5215e42`.
- **Reviewed HEAD:** `74f8e837bd13e10b71f517446ae0d108c5215e42`; clean worktree and branch independently checked at entry and completion.
- **Reviewer:** Codex independent agent `/root/b22_t050_r1_security`. No human review is attributed to this agent. Maintainer review remains pending.
- **Separation from code review:** fresh dedicated security context, no implementation or ordinary code-review work by this reviewer; empty security checklist applied independently. Preparation reports and prior verdicts were read only after independent current-source and raw-evidence assessment. This is an implementation security round, not reuse of preparation.
- **Unsafe audit cross-reference:** no executable or unsafe change. Descriptive cross-checks: UNSAFE-2026-0010/0012/0013/0014 (StaticCell and retired/current borrowing), 0017 (boot), 0029 (trap/exit), 0030 (copy-user and amendments), 0032 (entry), 0033 (shim and existing T-038 exclusion). PMM and loader source reference 0026/0027. This does not reapprove every existing unsafe site.
- **Scope constraint:** read-only repository review; only this `/tmp` report written. Root coordinator owns canonical artifact/index/trailer integration. No branches, commits, external posts, hosted operations, build/test/guest reruns or task promotion.

## 1. Capability correctness

Adversarial question: could the revised descriptions cause callers to treat a name, identity or demo behavior as authority they do not possess?

| Checklist item | Outcome and evidence |
|---|---|
| Privileged operations require capabilities | **OK for documentation.** README:44 distinguishes kernel object operations from current-task yield/exit. `dispatch.rs:137–161` uses current identity for controls; IPC/console validate table-local kind/right. No privileged operation is introduced. |
| Narrowest sufficient capability | **OK.** Glossary names the actual eight rights, including CONSOLE_WRITE, without inventing MAP/WAIT/kill rights. `rights.rs:21–73`, `dispatch.rs:321–334`, and `ipc/mod.rs:589–616` match. Trusted `cap_map`/`cap_unmap` remain kernel APIs, not newly exposed syscalls or proof of physical ownership. |
| Checks before observable effects | **OK.** Console checks cap, whole window and all pages before output (`dispatch.rs:228–310`); selected no-cap/non-USER/unmapped-second-page tests assert no output. Text does not promise timing noninterference or universal fault containment. |
| Move-only transfer | **OK.** Glossary describes sender-table removal into endpoint pending state and later receive installation. `ipc/mod.rs:303–449` validates before removal and preserves pending authority when the receiver table is full; the full-table/retry test at :1350 verifies the intended state. No claim of atomic cross-task rendezvous or globally unique authority is introduced. |
| Explicit duplication authority | **OK.** Glossary rights and permitted sharing agree with DUPLICATE and rights-subset checks at `cap/table.rs:194–216`; DERIVE is separately checked at :258–281. Kernel constructors and caller-supplied derive objects remain trusted APIs. |
| Atomic revocation | **OK within current documented boundary.** README explicitly limits traversal to descendants in the same table and points to Deferred ADR-0023. `cap_revoke` at `cap/table.rs:329` performs bounded local traversal; transfer installs a fresh root. No global/SMP/cross-table atomicity assurance follows. |

Badges and automatic reply capabilities are explicitly absent; the demo uses an existing endpoint capability. The new staged Rendezvous definition matches `SendPending`, `RecvWaiting`, and `RecvComplete`; scheduler bridges supply switching separately. Neither document turns caller-controlled message labels into authenticated identity.

## 2. Trust boundaries

Adversarial question: could malformed syscall words, forged handles, lengths or pointers cross an undocumented privilege boundary?

| Checklist item | Outcome and evidence |
|---|---|
| Validate userspace input | **OK.** Source decoder rejects unknown/release-console number; dispatcher routes typed values. Incomplete current table/window/AS binding fails closed as a unit (`bsp-qemu-virt/src/syscall.rs:160–205`). Guides correctly describe the trusted registration boundary without claiming fresh Task-generation or pointer-identity revalidation. |
| Validated mappings before dereference | **OK.** `user_access.rs:101–316` first checks the window, then each USER leaf before copying through the kernel direct map. First-userspace describes the relevant mechanism, not an arbitrary physical-frame ownership proof. |
| User buffer lengths checked | **OK.** Checked end arithmetic and window containment precede the page walk; zero-length requests touch nothing. Selected tests cover wrap/range, absent/non-USER/block leaves, read-only copy-to and second-page failure. The guide does not claim these are all exercised by hello. |
| Typed message parsing | **OK.** `dispatch.rs:172–211` decodes register message/handle fields and calls raw IPC operations. The revised glossary avoids saying both raw calls block until transfer completion. |
| No excess transferred authority | **OK.** IPC enforces TRANSFER and moves a leaf; rights are not widened. Full receiver table preserves pending state. No badge or reply authority is fabricated by the documentation. |

The real trap routes ESR EC 0x15 to syscall entry and other synchronous faults to `panic_entry` (`vectors.s:219–260`). First-userspace:133 and glossary's Syscall entry explicitly retain this system-wide limitation. The returning console call and nonreturning exit are distinguished: `syscall.rs:268–293` ignores the exit code and calls the module-level free function, which abandons the frame (`sched/mod.rs:979–1069`). No resource reclamation or terminal-state claim remains.

## 3. Memory safety

Adversarial question: do new descriptions hide aliasing, stale lifetime, uninitialized data or executable-memory assumptions?

| Checklist item | Outcome and evidence |
|---|---|
| New unsafe meets policy | **N/A — no Rust, assembly or unsafe operation changed.** The added boot snippet is documentation; its first instruction masks DAIF, and it is expressly limited to already-confirmed EL1 entry. |
| Safety invariants hold for callers | **OK as descriptive review; not a whole-program recertification.** StaticCell/scheduler descriptions retain initialized live pointers, single-core cooperative operation and no mutable shared-state borrow across switch. `main.rs:152–212`, `sched/mod.rs:1259–1332`, and audit 0014 agree. |
| No uninitialized-memory exposure | **OK for claims.** PMM source zeroes each returned page; first-entry assembly scrubs GPR/SIMD/control/thread registers (`cpu.rs:477–570`). Guide expressly says smoke does not cover every register-leak or stack-exhaustion scenario. |
| No use-after-free | **OK for claims.** Exit is described as ceasing scheduling, with task/AS/table resources retained and no terminal state. `sched/mod.rs:953–994` supports this; no destructor or slot-reuse guarantee is implied. |
| No aliasing violation | **OK for the documented discipline.** The old 0012 approach is marked removed; current raw-pointer momentary borrows end before switching. StaticCell is not described as immutable after initialization or SMP-safe. Existing unsafe contracts remain manually load-bearing. |

Permission verification: `vmsav8.rs:305–360` encodes high RAM WRITE|EXECUTE|GLOBAL as AP=00, UXN=1, PXN=0; devices have both XN bits. User image USER|EXECUTE at `task_loader.rs:709` yields AP=11, UXN=0, PXN=1; USER|WRITE stack at :764 yields AP=01 with both XN bits. The guide correctly separates data access from EL0/privileged instruction fetch and names current privileged executable RAM and future per-section W^X. Bootstrap shares L2 RAM/device tables with high roots and reserves six frames inside .bss, as the glossary says.

MapperFlush really is `Copy`, carries only VirtAddr, and permits explicit ignore/discard (`hal/src/mmu/mod.rs:390–450`). Its new glossary wording does not advertise linear discharge or AS identity. Miri wording is dynamic, host-path limited; the linked T-049 report explicitly excludes BSP, real EL0/assembly/hardware, has zero userland host tests, two ignored doc tests and exposed-provenance warnings. That report was read after this source pass; no Miri rerun or exhaustive proof is claimed here.

## 4. Kernel-mode discipline

Adversarial question: could onboarding instructions imply protection from stalls, panics, resource exhaustion or unsafe boot states that the implementation lacks?

| Checklist item | Outcome and evidence |
|---|---|
| No ISR allocation | **N/A — no ISR or allocator path changes.** No revised passage asserts that the demo exercises interrupt delivery. |
| No unbounded kernel loops | **OK for documentary truth.** Task A's permanent spin and cooperative nonpreemption are explicit; bounded smoke terminates QEMU after observing completion. This is not an availability guarantee for hostile code. |
| Minimized critical sections | **N/A — no critical-section change.** Documented raw-pointer/DAIF assumptions remain; no preemption/SMP extension is claimed. |
| No new hot-path panic | **OK.** No runtime change. Syscall-input error behavior is distinguished from the existing non-SVC EL0 kernel-panic route, trusted demo invariant panics and boot fail-stop behavior. |
| Typed allocation exhaustion | **N/A — no allocation path introduced.** PMM source returns Option/typed free errors; revised text promises validation and zeroing, not universal recoverable exhaustion or lifecycle cleanup. |

Boot skill: `_start` masks DAIF before SP/FP/BSS, is explicitly an EL1 skeleton, and sends EL2 users to an Accepted target boot policy rather than prescribing one HCR write. Timer access, traps, stack selection and transition context are correctly target-dependent. Minimal port success must follow the selected workload's actual work; it is explicitly weaker than the full reference EL0/IPC smoke. `--int` = `int,unimp`; runner `--int-log` = `int` with printed PID-scoped path. Neither claims `guest_errors` or instruction tracing.

Timer glossary wording is descriptive of source: `resolution_ns_for_freq` rounds nearest/minimum 1 ns; `ns_to_ticks` uses saturating ceiling division, called by the BSP deadline path. These are distinct functions (`hal/src/timer.rs:145–160,207–221`); no new rounding rule is enacted. The preflight records older ADR/rustdoc wording tension rather than editing an Accepted decision.

## 5. Cryptography

Adversarial question: is a new crypto or authenticity guarantee unsupported?

- **N/A — primitive choice:** no cryptographic implementation or protocol changes.
- **N/A — key secrecy:** no keys introduced or manipulated.
- **N/A — constant-time comparison:** no secret comparison introduced; no timing-resistance claim.
- **N/A — randomness:** no entropy/RNG surface introduced.
- **N/A — nonce/IV/salt discipline:** none present.

Retained SHA-256 values are byte-identity checks, not signatures, boot authentication, or evidence that the original capture could not have been edited.

## 6. Secrets and logging

Adversarial question: does new retained material expose credentials or advertise unjustified redaction?

- **OK — new diagnostics:** raw captures contain public demo messages, addresses, tool versions and temporary host paths/host metadata; no credential, key or new capability-token dump was found. No runtime logging change occurs. Public root handle zero in the guide is a caller-local selector, not transferable kernel authority.
- **N/A — security-sensitive Debug implementations:** none changed. The review does not infer global secret-free logging from a passing hello trace or from historical audit prose.

## 7. Dependencies

Adversarial question: does this step add unreviewed executable trust or alter the build chain?

- **N/A — new dependency vetting:** zero dependency/lock/toolchain/build/CI source changes in the reviewed range.
- **OK — trust category clarity:** userland is generated from in-tree source with the pinned toolchain's objcopy; guides describe six workspace members versus three defaults, and matching profiles share one generated hello.bin. No proprietary binary is added.
- **N/A — cargo-vet trust changes:** none needed; no new dependency trust decision.

Independent changed-file examination found only the authorized entry/guide/glossary/skill/path/copyright/task/evidence surfaces (32 paths). LICENSE independently compared byte/line structure: only line 189 changes, matching the approved NOTICE holder spelling. Phase path updates implement existing dotted-ID mapping, not a new phase/dependency authorization rule.

## 8. Threat-model impact

Adversarial question: do onboarding statements confuse an observed successful workload with protection against arbitrary hostile workloads?

- **OK — reconciliation:** full current `docs/architecture/security-model.md` read after source inspection. README/glossary distinguish target userspace drivers/services from current privileged QEMU drivers and the sole trusted embedded EL0 hello. Per-table CDT, control-plane identity, privileged RAM permissions, current fault/exit limitations, no SMP/preemption and evidence limits are compatible.
- **N/A — new threat-model shift:** no feature or boundary changes; the step corrects current-versus-target descriptions under existing ADRs. No new normative policy was found.

**Independent retained-evidence checks:** reconstructed `git archive 75de2ba...` in memory; SHA-256 matches `68500b9e7a5f05d48b668ca6bd8e1c28ed8e7f5625e6ee4d2fbf5f10a56ebe28`, and its member list contains neither target/ nor hello.bin. All 14 retained stdout/stderr/raw streams match metadata size and hash. Six recorded command exits are zero, with explicit debug/release userland builds before matching BSP builds and smoke. Build stderr shows real profile compilations followed by smoke's warm rebuilds. Installed tools/caches were reused, as acknowledged.

Independently counted raw records: debug/release each have two total Taking-exception records, both SVC and both EL0→EL1, with two ERETs (initial entry plus console return). Greeting counts are 1/0, exit and completion counts 1/1 in each. No other exception or listed fault appears. FIFO ordering B→A→EL0/exit→B→A matches registration and switching source, not stale source comments. No runtime rerun was warranted by this doc-only delta.

The checks establish internally consistent retained evidence and unchanged executable source, not original-capture authentication, comprehensive ABI soundness, arbitrary hostile-input coverage, strict provenance, SMP, real hardware, idle or timer IRQ delivery. Fresh R2, maintainer review and publication/merge remain separate. Frozen In Progress/unchecked/pending-review state is truthful.

### Reading and method ledger

Before any task/diff/source assessment, independently completed full AGENTS/CLAUDE, all current.md including historical tail, all 42 extant numbered ADRs in numerical order (0001–0033, 0035–0043; reserved 0034 absent), and all 15 standards including README. Combined output truncations were recovered with bounded re-reads before recording completion.

Then read full perform-security-review/conduct-review/security master plan, write-guide/update-glossary, approved Track B.2-2 plan and full T-050 contract. Read changed substantive guide/glossary/add-bsp content in full and inspect the actual content diffs; inspected path/copyright/index/task deltas. Independently reviewed raw QEMU logs and metadata before coordinator diagnostics/preparation conclusions. Subsequently read full T-050 preflight/verification/evidence README and diagnostic ledgers, full current security model, historical T-028 security review, full T-038 contract and fresh T-049 Miri report for continuity, not as substitute verdicts.

Full source files read: boot.s, cap/rights.rs, userland/tyrne-user/src/lib.rs, userland/hello/src/main.rs, hello.ld, build-userland.sh, smoke.sh, .cargo/config.toml, Cargo.toml and BSP build.rs. Targeted executable/tests/audit ranges, not claimed whole-file audits: syscall dispatcher/control/IPC/console checks and relevant malformed/release tests; user-copy production region and selected adversarial tests; IPC send/receive/transfer/right validation plus full-table retry; cap copy/derive/revoke/take; scheduler exit/dispatch/send bridge, function/test inventory; BSP StaticCell/early boot/task A/registration, syscall entry and vectors; CPU entry/scrub, timer helpers/locations; PMM alloc/free, AS representation/map/unmap; loader permission sites; descriptor encoding and MapperFlush; bootstrap/linker tables; runner logging; named audit entries/amendments. Broad regex searches are discovery, not full source reads. No claim of full kernel, complete test corpus, whole unsafe log, external architecture validation or new CI execution.

Machine checks independently verified frozen clean state, documentation-only executable delta, archive identity/generated-file absence, 14 stream hashes, raw event/marker counts, 54 headwords/54 unique anchors, LICENSE-only-line-189 delta and `git diff --check`. Coordinator navigation/grammar checks were inspected but not independently rerun as a full parser; this pass is the separate security assessment, not T-056 parser certification.

## Verdict

**Approve — zero verified new security findings in this documentation change.** All eight axes completed with explicit item dispositions. No blocking or nonblocking security defect was verified in the reviewed delta; no forced-zero assumption was used.

Existing **HIGH T-038** remains Ready and unresolved: the current console shim declares x2 input-only while syscall return overwrites it (`userland/tyrne-user/src/lib.rs:108`, `bsp-qemu-virt/src/syscall.rs:224`, `vectors.s:237`). The docs' “safe wrappers” wording describes Rust call-site API syntax, not a new proof or claim that T-038 was fixed. This approval covers the source-accurate documentation refresh, not the existing shim's soundness, the old audit assertion, production security, human approval or Done promotion.

Root should retain this distinct security R1 outcome in the canonical review/trailer accounting using the actual agent identity; R2 and maintainer review remain pending. No external comment is authorized or sent by this reviewer.

## Post-independent-result reconciliation — shared C01

The initial independent result above was completed and written before receiving the code-review finding/report. It remains **zero independently discovered security findings**; the following is an attributed cross-review finding, not a retroactive independent discovery. The coordinator then relayed code reviewer C01; its source evidence was independently rechecked against the same frozen HEAD. The actual code report was not yet available at the time of this append.

**Confirmed shared Low C01 — `docs/guides/first-userspace.md:115`: distinguish the capability-table raw pointer from an address-space handle.** The phrase “address-space/table handles” conflates two materially different registration inputs. `kernel/src/sched/mod.rs:448` accepts `AddressSpaceHandle`, but :452 accepts `*mut CapabilityTable`, stored at :290. The unsafe contract at :428–434 requires that the table outlive the task and have no aliased live `&mut` across a context switch; registration records the pointer, and `bsp-qemu-virt/src/syscall.rs:185` later materializes a mutable reference for dispatch. The pointer does not acquire generation validation or lifetime enforcement by being called a handle.

Impact: this is a documentation defect in a safety-sensitive onboarding description. It can cause a contributor to misunderstand the manually enforced pointer binding/lifetime contract. No runtime change, exploitable regression or new authority check failure is demonstrated. **Low** is appropriate. Remedy: identify the address-space handle and capability-table raw-pointer binding separately and state/link the required lifetime and no-live-mutable-borrow discipline. This qualifies the initial “trusted registration boundary”/caller-invariant assessment above: the implementation boundary is intact, but this particular sentence needs correction.

**Reconciled recommendation: address shared Low C01 before R2; no additional independently identified security findings.** Initial standalone verdict was Approve; cumulative review now has one shared Low documentation correction pending. All High runtime limitations discussed above remain outside this documentation delta. Root must preserve attribution/counting so the same C01 is not counted as two independent discoveries.

Coordinator-supplied configuration: this security agent GPT-6 Astra / high; code reviewer GPT-6.1 Sol / high. This records coordinator configuration, not independent runtime introspection. Actual reviewer identity remains the Codex agent named above; human maintainer review remains pending.

Actual paired code report subsequently read in full: `/tmp/tyrne-b22-t050-r1-code.md` (160 lines at read time). Its sole finding and **Request changes** verdict are Low C01 on the same frozen HEAD. This agrees with the attributed source verification above; there is no disputed finding or additional security issue exposed by that report. Its separate navigation/test/source scope is its own evidence, not retroactively added to this security review's read ledger. The two reports preserve independent initial assessments; the combined R1 result requires the C01 correction. A bounded post-correction verification is pending, followed by entirely fresh R2 contexts.

## Bounded R1 correction verification — final scoped verdict

Independently verified clean corrected HEAD **`523615603f87f6f11f2030db4d6d974c38330f0d`**. Read the complete `74f8e837bd13e10b71f517446ae0d108c5215e42..523615603f87f6f11f2030db4d6d974c38330f0d` patch: exactly three Markdown files, eight insertions and one deletion (first-userspace guide, verification-report append, task-history row). Reread `kernel/src/sched/mod.rs:424–453` against the changed guide sentence. `git diff --check 75de2ba90e151bae33e14d2db4a8278837e7775d..523615603f87f6f11f2030db4d6d974c38330f0d` passed. The complete patch confirms no runtime/source/config/CI or retained raw-evidence byte change. Existing independent raw-hash results therefore continue to apply; I did not rerun all hashes or adopt the coordinator's new navigation count as my own executed check.

**C01 resolved.** `docs/guides/first-userspace.md:115` now separately identifies the address-space handle and raw capability-table pointer, explicitly requires the table to outlive the task and forbids a live mutable borrow across a context switch, with responsibility assigned to the trusted registration caller. This faithfully captures the source's manually upheld safety obligations and does not invent generation validation for the table pointer. The appended report/history accurately preserve the finding's code-review origin and subsequent independent security corroboration, unchanged runtime/evidence, and pending review state.

**Final scoped R1 security verdict: Approve on `523615603f87f6f11f2030db4d6d974c38330f0d` — zero independently discovered security findings; one shared Low C01 independently confirmed after the initial result and now verified fixed; zero unresolved findings for this reviewed documentation delta.** The initial standalone assessment and cross-review provenance remain unchanged above. This bounded check closes the specific R1 correction, not a fresh R2 review. R2, canonical integration and human maintainer review remain pending. Existing HIGH T-038 and all stated evidence/security limitations remain unresolved and outside this documentation change.

---

## Retained Round 2 security report

# Security review 2026-10-13 — T-050 Step 6, fresh Round 2

- **Change:** `development`, cumulative `75de2ba90e151bae33e14d2db4a8278837e7775d..523615603f87f6f11f2030db4d6d974c38330f0d`.
- **Reviewed HEAD:** `523615603f87f6f11f2030db4d6d974c38330f0d`; clean repository independently checked. Initial implementation `74f8e837bd13e10b71f517446ae0d108c5215e42`; R1 correction `5236156`.
- **Reviewer:** Codex AI agent `/root/b22_t050_r2_security`, separate fresh context from both R1 agents and the R2 code agent. Coordinator-configured GPT-6 Astra/high; this is configuration attribution, not runtime introspection. No human maintainer review is claimed.
- **Separation:** empty security checklist, full independent prerequisite reads, current source and substantive documentation before coordinator evidence conclusions or actual prior reviews. User-requested separate concurrent contexts supply the separation here; no multi-hour interval or sequential completion after R2 code review is claimed. No implementation/code-review work or repo writes by this reviewer.
- **Unsafe cross-reference:** no executable/unsafe delta. Relevant descriptive checks include UNSAFE-2026-0014 (momentary mutable borrows), 0030 (user copy and amendments), 0031/0032 (AS context/EL0 entry), 0033 (syscall shim and T-038). Related PMM/loader contracts were inspected in source. This does not sign off every historical unsafe entry.
- **Boundary:** only this `/tmp` report is written. Root owns canonical artifacts, indexes and trailers. No builds, guest reruns, commits, hosted posts, main merge, task promotion or external certification performed.

## Independent assessment and chronology

The independent source/evidence assessment completed with **zero independently discovered new security findings** before receiving the R2 code-origin finding relay. Both actual R1 reports were subsequently read in full, including correction addenda, and the full three-file R1 correction patch was verified against current source. They are continuity evidence, not substituted R2 results.

Before this initial report was written, root relayed a new R2 code-origin Low finding about the Bridge phase definition versus ADR-0040. That relay arrived after completion of the independent assessment. The actual R2 code report has not yet been read, and the relayed finding has not yet been independently confirmed in this initial section. A subsequent reconciliation section will preserve its attribution and adjust the combined recommendation as necessary; it will not be portrayed as an independent security discovery.

## 1. Capability correctness

| Item | Adversarial question | Disposition |
|---|---|---|
| Privileged operations require authority | Can identity alone authorize an object operation? | **OK for the changed descriptions.** README distinguishes capability-gated object operations from current-task yield/exit controls. `kernel/src/syscall/dispatch.rs` dispatches controls from current identity while IPC and console resolve table-local capabilities. No new operation exists. |
| Narrowest sufficient capability | Does the prose invent broad authority or a nonexistent right? | **OK.** The eight implemented independent rights are DUPLICATE, DERIVE, REVOKE, TRANSFER, SEND, RECV, NOTIFY and CONSOLE_WRITE (bits 0–7); no READ/WRITE/EXECUTE capability-right bit, MAP/UNMAP bit, badge or reply-capability mechanism is invented. AS map/unmap are trusted kernel APIs; existing kind/live checks are not presented as a physical ownership proof. |
| Checks before side effects | Can a bad cap or later bad page cause output first? | **OK within documented scope.** Console checks its cap and preflights the entire window and all pages before output. Selected negative tests inspect unmapped/non-USER/second-page failures and no partial output. No universal timing noninterference assertion follows. |
| Move-only transfer | Can the same transferred leaf remain at the sender? | **OK.** IPC validates endpoint, TRANSFER and pending availability before taking the sender leaf; receive preserves pending state on a full table. The glossary describes staged removal and subsequent installation, not instantaneous cross-task completion. |
| Authorized duplication | Can a copied/derived capability gain rights? | **OK.** `cap/table.rs` requires DUPLICATE or DERIVE as appropriate and subset rights. Trusted constructors and the caller-chosen object in derive remain privileged assumptions; the docs do not claim full object provenance. |
| Atomic revocation | Does local traversal imply distributed revocation? | **OK for the explicit local boundary.** README/glossary qualify the CDT to a table, matching bounded local descendant traversal. Transfer's fresh receiving root is not claimed to preserve a cross-table CDT; ADR-0023 remains Deferred. No SMP atomicity is claimed. |

## 2. Trust boundaries

| Item | Adversarial question | Disposition |
|---|---|---|
| Validate incoming userspace values | Could malformed numbers or incomplete task binding gain access? | **OK.** Typed decoding rejects unknown/release-console numbers. The BSP builds dispatch context only for the complete table/window/AS binding, with AS generation lookup. It does not independently prove task generation or raw table-pointer identity/lifetime; the corrected guide makes caller obligations explicit. |
| Validate mappings before pointer access | Can a forged VA reach arbitrary kernel memory? | **OK for described mechanism.** User-copy code validates bounds, then USER page leaves, and copies through the direct map. Its trusted address-space/physical-mapping assumptions remain load-bearing, rather than promised arbitrary-frame ownership isolation. |
| Bound user lengths | Can wraparound or a bad later page bypass validation? | **OK.** Checked arithmetic, window containment and whole-range page preflight precede copying; zero-length behavior is explicit in code. Selected negative tests cover non-USER/unmapped/second-page and write-protection cases. These were read, not newly executed. |
| Typed message parsing | Are arbitrary words treated as authenticated messages or blocking calls? | **OK.** Dispatcher decodes register structures and table-local handles; raw IPC is staged, and the scheduler bridge supplies blocking/switching. Glossary does not claim labels authenticate identity or both raw operations synchronously block. |
| No excess receiver authority | Can receiving manufacture rights or lose pending authority on failure? | **OK.** Transfer moves existing permitted authority; full-table receive preserves the pending entry. No unimplemented badge, automatic reply cap or cross-table revocation guarantee appears. |

The lower-EL synchronous vector tests ESR EC 0x15 for SVC; other synchronous exceptions call panic entry. The documentation retains this failure-containment limitation. Exit ignores the supplied status, calls the module-level unsafe free function, selects another runnable context and does not ERET back; it does not reclaim task/table/AS resources or establish a terminal task state. The guide's API spelling and lifecycle limits agree with `bsp-qemu-virt/src/syscall.rs` and `kernel/src/sched/mod.rs`.

## 3. Memory safety

| Item | Adversarial question | Disposition |
|---|---|---|
| New unsafe policy compliance | Does this change add an unaudited unsafe operation? | **N/A.** No Rust, assembly or executable change. The documented bootstrap assembly skeleton is explicitly already-EL1 and masks DAIF first. |
| Safety contracts at callers | Does onboarding conceal pointer lifetime or switch-time borrows? | **OK for the revised descriptions, not a proof of every existing call.** `add_user_task` takes an AS handle and raw capability-table pointer. Guide line 115 now requires table lifetime and no live mutable borrow across switch, assigned to the trusted registration caller. R1 C01 is fixed and attributed below. |
| No uninitialized exposure | Could stale frames/registers be advertised as isolated without cleaning? | **OK for the claims.** PMM allocation actually executes page zeroing; `enter_el0` clears x0–x30, v0–v31, FPCR/FPSR and EL0 thread registers before initial ERET. Initial scrubbing is not ongoing trap/SIMD isolation; hello does not test every register leak or stack condition. |
| No use-after-free | Are generation tags described as lifetime enforcement? | **OK for the claims.** Arena generations reject stale identifiers within their implementation limits; raw pointer validity is separately trusted. Exit retains resources rather than freeing them, and docs do not infer automatic reclamation or universal lifetime safety. |
| No aliasing violation | Could a mutable borrow survive a cooperative switch? | **OK for the documented discipline.** StaticCell and scheduler bridge descriptions retain single-core, initialized live-pointer and short-borrow assumptions. Current scoped raw-pointer borrows end before switches; old removed borrowing approaches are not presented as current code. No general aliasing proof is claimed. |

**Flagged existing limitation, outside this delta:** HIGH T-038 remains Ready: the console wrapper's x2 operand is declared input-only while the syscall return path overwrites x0–x7. This is not fixed by documentation, Miri or a passing smoke. No new runtime defect is reported here and no whole-ABI soundness approval is given.

Descriptor values were checked against `vmsav8` encoding: current high RAM WRITE|EXECUTE|GLOBAL has AP=00, UXN=1, PXN=0; privileged RAM is executable and writable, so per-section W^X remains future work. Device mapping is XN at both levels. User code USER|EXECUTE has AP=11, UXN=0, PXN=1; user stack USER|WRITE has AP=01 and both XN bits. AP data permission and instruction permission are distinct. Bootstrap shares relevant L2 mappings and reserves six table frames in `.bss`; the glossary does not infer finer-grained high-half permissions.

MapperFlush is Copy, contains a VA without an AS identity, and permits explicit ignore/discard: its wording correctly avoids linear completion claims. Miri is limited dynamic checking of exercised host paths. The source-qualified T-049 report's passing selection excludes real BSP/EL0/assembly/hardware, includes zero userland host tests, two ignored doctests and exposed-provenance warnings. It was read after this source assessment and was not rerun or treated as proof of bug absence.

## 4. Kernel-mode discipline

| Item | Adversarial question | Disposition |
|---|---|---|
| No ISR allocation | Does the new workload exercise or alter allocation in interrupts? | **N/A.** No ISR/allocation code changes; the guide explicitly does not establish IRQ/timer-idle execution. |
| No unbounded loops | Could users mistake completion for availability under hostile tasks? | **OK for documentary truth.** Task A permanently spins after the visible exchange; scheduler is cooperative and nonpreemptive. Smoke's bounded timeout follows observed completion, not process exit or adversarial availability proof. |
| Short critical sections | Does the prose permit mutable state across a switch or imply SMP? | **OK for the described discipline.** Short borrow phases and single-core assumptions remain explicit; no new critical section exists. |
| No hot-path panic | Does the text promise fault containment for non-SVC exceptions? | **OK.** Existing lower-EL non-SVC panic, trusted demo invariant panics and boot fail-stop limits are preserved. No runtime panic introduced. |
| Typed allocation failure | Does the text promise lifecycle cleanup or universally recoverable exhaustion? | **N/A to new behavior.** No allocation path changed. PMM Option/typed-free-error behavior was inspected; text does not promise automatic teardown or all-path recovery. |

BSP skill snippets mask DAIF before stack/frame/BSS work, and explicitly assume confirmed EL1. EL2 requires an Accepted target-specific boot policy including trap/timer/context considerations, rather than one generic HCR write. A minimal port's success marker must follow its actual chosen workload; it is not the full reference smoke.

FIFO ordering is supported by registration B, A, user and the ready queue's tail enqueue/front dequeue, not inherited stale comments. Scheduler idle is a fallback, not a queue resident. The retained reference trace does not exercise idle/WFI or timer IRQ delivery. Timer resolution rounds nearest with minimum 1 ns, whereas deadline conversion uses saturating ceiling division; these distinct algorithms are described without rewriting the existing ADR/rustdoc wording tension.

## 5. Cryptography

| Item | Adversarial question | Disposition |
|---|---|---|
| Reviewed primitives | Is this an unreviewed cryptographic construction? | **N/A.** No crypto implementation or protocol. SHA-256 is used only for retained-byte identity. |
| Key confidentiality | Are new keys logged or returned? | **N/A.** No keys introduced or handled. |
| Constant-time comparison | Is secret timing exposed by a new comparison? | **N/A.** No secret comparison or timing-resistance claim. |
| Acceptable randomness | Is an attacker-controlled entropy source introduced? | **N/A.** No entropy/RNG change. |
| Nonce/IV/salt contract | Is reuse or generation newly unsafe? | **N/A.** No nonce, IV or salt handling. |

A matching recorded SHA-256 is not capture authentication, a signature, secure boot or independent proof of the coordinator's execution environment.

## 6. Secrets and logging

| Item | Adversarial question | Disposition |
|---|---|---|
| Diagnostics do not disclose secrets | Do captures contain credentials or new authority-bearing token dumps? | **OK within inspected artifacts.** Public demo text, addresses, paths, versions and host metadata are present; no credential/key was found. A documented hello handle of zero is table-local, not transferable authority by itself. No new logging path exists. |
| Sensitive Debug redaction | Is a new Debug implementation exposing secrets? | **N/A.** No implementation changes. No global secret-free-logging conclusion is drawn. |

The guide accurately distinguishes smoke `--int` (`int,unimp`) from runner `--int-log` (`int` and printed PID-scoped path). Neither option is mislabeled as `guest_errors`, instruction tracing, or proof that arbitrary fault classes were exercised.

## 7. Dependencies

| Item | Adversarial question | Disposition |
|---|---|---|
| New dependency approval | Is new executable trust smuggled into the docs change? | **N/A.** No dependency, lockfile, toolchain, Cargo, config, CI or executable delta in the 32-path range. |
| Trust category understood | Is generated userland mistaken for a proprietary blob or isolated service? | **OK.** In-tree source and pinned-toolchain objcopy produce the shared hello.bin; matching profile build ordering is explicit. The sole embedded trusted EL0 task and privileged current drivers differ from the target userspace-service architecture. |
| cargo-vet decisions | Does a changed trust graph lack vet updates? | **N/A.** No dependency trust graph change. |

NOTICE line 2 and LICENSE line 189 exactly contain `Copyright 2026 HodeTech, Cemil ILIK and Tyrne Contributors`. Independent byte/line comparison found LICENSE changes only at line 189, preserving surrounding content, indentation and newline. No broad license edit or new proprietary artifact was found.

## 8. Threat-model impact

| Item | Adversarial question | Disposition |
|---|---|---|
| Reconcile current threat model | Does observed hello success become a claim of hostile-program isolation? | **OK for security boundaries.** Full current security model reconciles the trusted demo, identity versus object authority, per-table CDT, privileged current drivers, user-copy assumptions, raw registrations, exit retention, non-SVC panic, writable/executable privileged RAM and missing ongoing SIMD containment. No new defense is advertised. |
| Update changed threat model | Is a newly changed security boundary undocumented? | **N/A.** No feature or security-policy shift; the intended change reports existing source and target architecture. The separately relayed governance wording issue awaits reconciliation below. |

## Architectural principles P1–P12

| Principle | Assessment |
|---|---|
| P1 no ambient authority | **OK.** Object authority and current-task controls distinguished; identity alone not advertised as object permission. |
| P2 minimal TCB | **OK.** No runtime TCB addition; actual privileged demo boundary visible. |
| P3 userspace services | **OK.** Target driver/service placement distinguished from current EL1 BSP drivers and trusted embedded hello. |
| P4 boundary checks | **OK for descriptions.** Capability, binding and mapping checks match code with the limitations above. |
| P5 Rust/justified assembly | **N/A to code changes; OK descriptions.** No new executable or unsafe; architecture-required assembly remains source-linked. T-038 is not waived. |
| P6 HAL separation | **OK.** No new board coupling; target-specific boot policy belongs in BSP guidance. |
| P7 no proprietary blobs | **OK.** Source-built hello and raw text evidence only; no firmware/binary addition. |
| P8 ADR decisions | **OK for independent security-policy assessment.** No intentional new decision found; any shared governance wording defect must be corrected to existing ADR-0040, not silently enact a stricter policy. |
| P9 English | **OK.** Changed repository prose and inspected commit messages are English. |
| P10 Mermaid | **N/A.** No new architectural diagram or binary figure. |
| P11 reproducibility | **OK within recorded evidence limits.** Matching profile chain, pinned source/toolchain and hashes are retained. Cache reuse and absence of retained ELFs are explicit; this review does not prove bit-identical rebuilds. |
| P12 scope on main | **OK for current development state.** T-050 stays In Progress with unchecked acceptance; no Done/main merge or maintainer certification is claimed. |

## Independent checks and evidence limits

Executed read-only checks in this review:

1. Exact HEAD/worktree and cumulative file inventory: 32 paths, documentation/legal/JSON/log artifacts only; no kernel/HAL/BSP/userland/tool/Cargo/config/CI runtime delta. `git diff --check` passed.
2. Recomputed all 14 retained raw/stdout/stderr stream sizes and SHA-256 values against metadata; all match, including four empty stdout streams. Read the complete raw output including termination tails.
3. Recreated the base `git archive 75de2ba...` in memory: SHA-256 `68500b9e7a5f05d48b668ca6bd8e1c28ed8e7f5625e6ee4d2fbf5f10a56ebe28` matches. The captured clean export and command execution are coordinator provenance, not witnessed execution by this reviewer.
4. Independently counted debug and release logs: each two SVC Taking-exception records, two EL0-to-EL1 transitions and two ERETs; greeting 1/0; exit/completion once each. Visible FIFO ordering B wait → A send → hello/exit → B receive/reply → A completion matches source. No other exception or inspected fault marker appears.
5. Six recorded command exits are zero; both profiles order userland build before matching BSP build and smoke. Build logs show profile compilation followed by smoke warm rebuilds. Installed tools/caches were reused. Metadata records image/ELF hashes; those binaries are not retained. The interactive path is documented, not automated by this evidence.
6. Independently checked 54 unique headwords and 54 immediate unique explicit anchor IDs against the glossary diagnostic; four guide inventory entries and both procedural guide section orders; LICENSE-only-line-189 delta and matching NOTICE spelling.
7. Read the complete R1 correction patch: exactly first-userspace, verification report and task history; raw evidence and executable source remain unchanged. The pointer distinction/caller obligation matches `add_user_task`.

No compile/test/guest/Miri rerun was performed: this cumulative delta is documentation-only and source inspection found no new runtime gap requiring one. Adversarial tests were inspected, not executed here. The coordinator's 292-target/18-fragment original diagnostic and 293-target correction check were reviewed as attributed evidence; the full navigation parser was not independently rerun. No claim is made of full kernel audit, all-input coverage, real hardware, strict provenance, capture authenticity, SMP, preemption, timer IRQ/idle execution, security bug absence or T-056 parser certification.

## Independent read ledger

**Mandatory gate completed before any task/diff/source assessment:** full AGENTS.md (23 lines), CLAUDE.md (60), current.md (141 including historical tail); every one of 42 extant numbered ADRs in numeric order 0001–0033 and 0035–0043 (reserved 0034 absent), total 7,090 lines; all 15 standards including README, total 2,240 lines. These were literal independent reads, not parent summaries or grep inventories.

ADR lengths, in numeric order: 0001 114; 0002 110; 0003 98; 0004 125; 0005 83; 0006 145; 0007 115; 0008 169; 0009 238; 0010 161; 0011 145; 0012 182; 0013 221; 0014 267; 0015 170; 0016 239; 0017 227; 0018 98; 0019 229; 0020 334; 0021 153; 0022 193; 0023 92; 0024 119; 0025 140; 0026 181; 0027 234; 0028 204; 0029 159; 0030 221; 0031 163; 0032 154; 0033 203; 0035 212; 0036 207; 0037 146; 0038 153; 0039 115; 0040 172; 0041 103; 0042 99; 0043 197.

Standard lengths: README 48; architectural-principles 130; bsp-boot-checklist 224; code-review 135; code-style 155; commit-style 146; documentation-style 91; error-handling 178; infrastructure 246; localization 100; logging-and-observability 149; release 155; security-review 135; testing 155; unsafe-policy 193.

**Gate output recovery:** current.md original truncation recovered with 1–35, 21–27, 36–65, 66–100, 101–141 and separate 52–100 reads; ADR0017 1–30, ADR0021 105–153, ADR0022 1–86, ADR0026 20–45, ADR0027 75–85/85–118, ADR0028 65–76/75–101, ADR0037 123–142, and infrastructure 50–87 recovered respective combined-output gaps. All claimed prerequisites were complete before proceeding.

**After the gate:** full perform-security-review, conduct-review, write-guide, update-glossary, add-bsp and start-task skills; full security master plan; T-050 contract; approved 13-step Track B.2-2 plan; substantive cumulative doc diffs and current README, both procedural guides, glossary, guide inventory, analysis and roadmap entries. Full current security model and T-038 task. Evidence/provenance full preflight, verification, evidence README, metadata, diagnostic JSON and all 14 streams after own source assessment; T-049 Miri report only after source analysis. Preflight 83–110 and glossary diff 105–125/122–215 recovered combined-output truncations.

**Whole source files:** `tools/build-userland.sh`, `tools/smoke.sh`, `tools/run-qemu.sh`, `.cargo/config.toml`, BSP build.rs and boot.s, hello main.rs and linker script, BSP syscall.rs. **Targeted source/test reads, not whole-file audits:** syscall dispatcher production paths and selected malformed/release/binding tests; user-copy production code and selected adversarial tests; IPC send/receive/staged transfer; cap rights/copy/derive/revoke and generation implementation; scheduler registration, FIFO, wakeup, context binding, start/exit and IPC switch bridge; BSP task A/B/registration, CPU scrub entry and lower-EL vector body; PMM allocation/zeroing/free, AS create/map/unmap; descriptor constants/encoding, high-half/bootstrap/linker reservation, loader permission sites; Timer helpers and deadline use; MapperFlush; userland console/exit asm. A late path lookup initially selected nonexistent generic paths; correct discovered `kernel/src/syscall/user_access.rs`, `kernel/src/mm/pmm.rs`, and `bsp-qemu-virt/src/cpu.rs` were then read, including copy-to write and all entry scrubs. Searches were discovery, not claimed full reads.

**Audit reads:** relevant full 0014 body/amendments, 0030/0031/0032/0033 regions; aggregate truncations recovered by separate 0014 192–250 plus 251–256, 0030 682–730 and 0032 731–758 reads. No full unsafe-log audit is claimed. Historical entries are not treated as overriding current code or T-038.

**Prior reviews only after independent assessment:** actual `/tmp/tyrne-b22-t050-r1-code.md` full 178 lines and `/tmp/tyrne-b22-t050-r1-security.md` full 151 lines, including addenda. R1 code discovered Low C01 at initial 74f8e83; R1 security originally approved independently, subsequently corroborated that shared finding, then both verified corrected 5236156. Their original findings and changing verdicts are retained honestly. Current guide states AS handle versus raw table pointer and lifetime/borrow obligations; that correction is confirmed, not rediscovered. Zero unresolved R1 findings does not substitute for this fresh R2 pass.

## Initial independent verdict

**Approve for the independently assessed security delta — zero independently discovered new security findings.** All eight axes and P1–P12 were considered. Existing HIGH T-038 remains Ready, unresolved and outside the documentation delta; the report does not certify runtime soundness. The relayed R2 code-origin Low governance wording issue is not yet independently confirmed in this initial result, so this is not a joint final approval or authorization for Done. Reconciliation follows only after independent confirmation and reading the actual paired report.

## Actual paired R2 report and attributed reconciliation

After the independent assessment and initial report above were complete, read the actual `/tmp/tyrne-b22-t050-r2-code.md` in full (153 lines at read time). Its sole new finding is **Low R2-C01**, independently discovered by the code reviewer; its frozen-HEAD verdict is **Request changes**. Root had relayed this issue between completion of my independent assessment and writing this initial report, as explicitly recorded above. No borrowed finding is counted as an independent security discovery.

**Independently corroborated shared R2-C01 — `docs/glossary.md:26`, Bridge phase.** Reread the current definition and ADR-0040 Decision outcome rule 2 (`docs/decisions/0040-phase-b2-consolidation-bridge.md:44`). The unrestricted “must close before C/D work begins” overstates the accepted gate. The ADR prevents C/D milestones opening and C/D implementation tasks leaving Draft while B.2 remains open, but expressly permits and encourages Phase C scoping drafts, Proposed ADRs and T-074 readiness work. A newcomer following the glossary would unnecessarily block approved planning. **Low** is appropriate: a factual governance/documentation mismatch, with no demonstrated runtime or authority regression.

**Required remedy:** preserve the general dotted-ID/stable-letter definition while stating the actual milestone/implementation gate and the permitted Phase C planning. Correct to the existing Accepted ADR; do not enact a policy change or add a new ADR. This is a shared code-origin finding, counted once as R2-C01 and distinct from resolved R1 C01. It qualifies the initial P8/document-consistency assessment; it does not change the unchanged runtime security boundaries.

The paired report's remaining source/evidence conclusions agree with this independent security pass. Its independently executed full navigation diagnostic is its own evidence and is not retroactively added to my executed checks. Its R1 verification matches the actual prior reports and patch. No second disputed or new security finding emerged from reconciliation.

**Report QA correction:** after the initial write, a fresh literal rights.rs read caught a drafting error in this report's initial narrowest-authority row: it had mistakenly enumerated memory permission names and called CONSOLE_WRITE an alias. The report row was corrected to the actual independent bits DUPLICATE, DERIVE, REVOKE, TRANSFER, SEND, RECV, NOTIFY and CONSOLE_WRITE. Repository glossary/source were already correct; this was a reviewer-report error, not a repository finding. An ADR filename guessed during reconciliation was also corrected by following the actual link before verification. These checks do not alter finding provenance.

## Reconciled R2 verdict at frozen HEAD

**Changes requested on `523615603f87f6f11f2030db4d6d974c38330f0d`: address shared Low R2-C01, then verify the bounded correction.** Zero independently discovered new security findings; one code-origin Low documentation finding independently corroborated and still open. R1 C01 remains verified resolved. All eight security axes are complete; existing HIGH T-038 remains Ready/unresolved, and no runtime, human-review, Done, main-merge or hosted certification is implied.

Final read-only snapshot still has exact frozen HEAD and clean worktree. Root owns the correction and canonical report/index/trailer integration; this reviewer has changed only the authorized temporary report. This is the completed fresh R2 assessment and reconciliation, not yet a post-fix approval.

## Bounded R2 correction verification — final scoped disposition

Independently verified clean `development` HEAD **`946f45f34f7eac90164adccfcd71e4c7f77c1f8e`**. Read the complete `523615603f87f6f11f2030db4d6d974c38330f0d..946f45f34f7eac90164adccfcd71e4c7f77c1f8e` patch: exactly three Markdown files, comprising the Bridge phase sentence correction and provenance additions in the verification report/task history. This is a bounded correction check, not another fresh review round.

**R2-C01 resolved.** The revised glossary requires B.2 closure before C/D milestones open or implementation tasks leave Draft, and explicitly permits Phase C planning, Proposed ADRs and the readiness sweep. Reread ADR-0040 Decision outcome rule 2: the corrected definition accurately preserves its accepted gate and planning exception, while retaining the dotted identifier/stable phase-letter definition and ADR link. No new policy or ADR is introduced. Provenance additions correctly identify the fresh R2 code origin, later independent security corroboration and separate resolved R1 finding; no false original security discovery or completed canonical closure is asserted.

Independent read-only Python checks established exactly the three expected Markdown paths, identical ordered 54 headwords and 54 unique explicit anchor IDs, and no delta to runtime/source/build/config/CI paths, the complete retained evidence directory, the first-userspace guide or NOTICE/LICENSE. Therefore previously verified raw bytes and source evidence are unchanged; I did not rerun the 14 hashes, any guest/build/test/Miri run or navigation parser. The coordinator's later 294-target/18-fragment diagnostic is attributed coordinator evidence, not my executed check. Independently executed cumulative `git diff --check 75de2ba...946f45f` passed.

**R1 C01 remains resolved:** reread the unchanged first-userspace registration sentence and scheduler Safety/signature at lines 424–453. The separate AS handle/raw table pointer, table lifetime and no-live-mutable-borrow-across-switch requirements still match source. Existing HIGH T-038 remains Ready/unresolved and all original security/evidence limits remain in force.

**Final scoped R2 security verdict: Approve on `946f45f34f7eac90164adccfcd71e4c7f77c1f8e` — zero independently discovered new security findings; shared code-origin Low R2-C01 independently corroborated and now verified fixed; zero unresolved findings for this documentation delta.** Initial independent result, subsequent requested correction and reviewer-report QA correction remain preserved above. This bounded result was written without waiting for the paired reviewer's post-fix result. Canonical integration and human maintainer review remain separate; no Done/main merge, runtime soundness or hosted certification is granted. Only the authorized temporary report was written.

After writing the independent bounded approval above, read the actual paired code report's newly delivered reconciliation and bounded-verification sections (lines 154 onward; initial 153 lines were already fully read). The primary reviewer independently verifies both corrections on the same clean `946f45f`, zero open code/document findings, with its final primary approval explicitly awaiting this delivered security addendum. Its source/evidence-preservation findings agree; no dispute or additional finding appeared. My scoped security approval stands without claiming a primary verdict that had not yet been delivered at that read time.
