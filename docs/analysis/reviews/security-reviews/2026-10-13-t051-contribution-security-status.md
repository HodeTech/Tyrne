# Security review 2026-10-13 — T-051 contribution and security status

- **Change:** `development`, `50f21ca7070eb14d2bb52d19972a3978ef666975..4ffda151ca7a1c438b9fa8a855db2584cc476409`.
- **Reviewer:** Codex coordinator for @cemililik, consolidating two fresh independent security contexts. These agent outcomes do not replace maintainer SECURITY wording review.
- **Separation from code review:** Each fresh security context started after its corresponding five-role code pass completed, opened the checklist independently and read no peer temporary report. Round 2 uses different contexts from round 1.
- **Unsafe audit cross-reference:** n/a for changes: no executable, unsafe contract, audit, dependency, CI or live-policy delta. Existing contracts are source context, not globally re-certified.
- **Code-review cross-reference:** [T-051 code/document rounds](../code-reviews/2026-10-13-t051-contribution-security-status.md).
- **Contract:** [T-051](../../tasks/phase-b2/T-051-contributing-and-security-status.md), Step 1 of the [approved plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md). Reporting/disclosure policy is unchanged.

## Review rounds and evidence boundary

| Round | Fresh security context | Model / effort | Source and result |
|-------|------------------------|----------------|-------------------|
| 1 | `b22_t051_r1_security` | GPT-6 Astra / high | `50f21ca..4ffda15`: Approve, zero in-scope findings |
| 2 | `b22_t051_r2_security` | GPT-6 Astra / high | Same cumulative range: Approve, zero verified findings |

Each context worked all eight axes and 33 master-plan checklist items, including allocation exhaustion. No correction commit was needed between rounds. The coordinator read both complete reports and checked their evidence; the detailed merged checklist below uses round 2's explicit source-bound labels and adversarial questions.

Round 1 used N/A-to-executable-change with bounded source verification for transfer, duplication, caller safety, use-after-free and aliasing; round 2 labels those bounded documentation/source checks OK. This difference concerns checklist scope, not a missing protection or a global runtime approval. The rationale below retains that boundary: no new operation or safety contract exists, and unchanged runtime is not globally certified. All other per-item outcomes agree. Both rounds reject old denial-of-self, dormant-loader and gate-order comments where executable paths contradict them.

Every source reference below binds to reviewed tip `4ffda151ca7a1c438b9fa8a855db2584cc476409`; coordinator review/tracking publication is subsequent evidence bookkeeping. No fresh QEMU, Miri, compilation, runtime security test or hosted result is claimed. Existing tests were inspected, not represented as newly passing. A clean verdict concerns the factual documentation delta, not global availability, arbitrary-image, timing, SMP or reclamation guarantees. Both reviewers verified a clean tracked tree at their pass boundaries.

## Claim-to-implementation checks


| Changed claim | Independent evidence and outcome |
|---|---|
| SECURITY:11–19: five numbered v1 calls | `kernel/src/syscall/abi.rs:50–89` defines and decodes only Send=1, Recv=2, TaskYield=3, TaskExit=4 and conditional ConsoleWrite=5; `dispatch.rs:132–171` exhaustively dispatches these. OK. This is ABI reachability, not a claim that the hello demo holds endpoint authority or exercises all five calls. |
| SECURITY:15–16: endpoint SEND/RECV | `kernel/src/ipc/mod.rs:303–365`, `:396–441`, `:589–603` resolve in the supplied caller table, check Endpoint kind and the appropriate right before state mutation. `bsp-qemu-virt/src/syscall.rs:173–217` supplies the running task's own table and fails closed on incomplete context. OK. Bare syscall IPC is not advertised as the scheduler's blocking bridge. |
| SECURITY:17–18: own-task yield/exit | `dispatch.rs:145–169` requires `has_current_task`; no user task identifier is accepted. BSP context uses scheduler accessors (`sched/mod.rs:530–550`) plus generation-checked address-space lookup. BSP Reschedule/Terminate arms call `yield_now`/`task_exit_current`; `sched/mod.rs:979–992` switches away via a diverging path. OK. |
| SECURITY:19–21: debug console and normal release | `abi.rs:80–89` uses `cfg!(debug_assertions)`; `dispatch.rs:132–138` returns BadSyscallNumber on decode failure before handler/cap lookup. Root Cargo release profile leaves debug assertions at its default false. `dispatch.rs:239–331` checks DebugConsole/CONSOLE_WRITE, range, and all pages before copying/output. OK. The explicit cfg wording avoids claiming every customized release profile disables it, and release rejection does not mean all kernel diagnostics are disabled. |
| SECURITY:21: user-buffer validation | `user_access.rs:105–123` rejects overflow/out-of-window nonempty spans; `:145–173` translates every page through task AS and requires USER; `:190–264` copies translated page sub-runs only after probing. `bsp-qemu-virt/src/mmu.rs:331–393` and `hal/src/mmu/vmsav8.rs:397–421` implement read-only translation/permission decode. Zero length copies nothing. OK under current single-core masked-SVC mapping stability and trusted loader. |
| SECURITY:23: kernel APIs exceed EL0 surface | `cap/table.rs` exposes copy/derive/revoke/drop; `ipc/mod.rs:477` exposes notify; `mm/address_space.rs:539,728,775` exposes address-space creation/map/unmap. None has an ABI decode or dispatch arm. OK; the statement does not deny indirect cap transfer by ipc_send/ipc_recv. |
| SECURITY:27: trusted embedded image | `bsp-qemu-virt/src/main.rs:380` uses include_bytes of hello.bin; `:1342–1353` calls load_image with that image and fixed BSP configuration, then `:1485` creates the task and `:1634–1643` publishes it. `task_loader.rs:507–725` validates arguments, budgets, source overlap and uses fresh PMM frames. `userland/hello/src/main.rs:50–56` greets/exits. OK; no arbitrary-untrusted-image service is exposed. |
| SECURITY:28: non-SVC faults panic whole kernel | `vectors.s` lower-EL +0x400 entry branches to the shared sync trampoline; its ESR EC comparison routes anything except SVC64 to panic_entry, which calls panic (`exceptions.rs`). `main.rs:1691–1730` writes panic diagnostics then spins permanently. OK. This contradicts older “denial-of-self” commentary in the correct direction: kernel-wide halt is the executable behavior. |
| SECURITY:29: exit does not reclaim | `sched/mod.rs:850–883` dequeues/falls back to idle and replaces current; `:979–992` calls it without re-enqueueing the exiting task, then abandons the frame through run_dispatched. There is no arena/free-frame/cap-table destruction here. OK. The sentence concerns exit lifecycle; existing lower-level destruction helpers do not constitute integrated exit reclamation. |
| SECURITY:7,31 and CONTRIBUTING:3,14,21–24 | Current phase statements match ADR-0040/0043 and current task selection. Pre-alpha/no-production/no-guarantee terms remain. Contribution instructions point to actual planning, code/security review, CI and release procedures; they add no bypass or assertion that every architectural control is already implemented. OK. |
| Original reporting/disclosure tail | Exact bytes from `## Reporting a security issue` through EOF, including the heading, are identical at base and tip: 1,441 bytes, SHA-256 `9bf184f19b4b7979889e1e13b7cec11f6573860c2fe2c4e8329df63ea81fa22a`. Private advisory channel, repository scope, fix-first/disclose-later policy and AI-agent rule are preserved. OK. |

## 1. Capability correctness

| Item | Outcome and rationale | Malicious-caller question and resolution |
|---|---|---|
| Every introduced privileged operation requires a capability | **OK** — no operation is introduced; the documented object-naming operations match actual endpoint and console checks. | Can I obtain an object effect with a forged handle? Table bounds/generation/occupancy (`cap/table.rs:563–586`) and kind/right checks reject it; BSP never selects a caller-named foreign table. |
| Narrowest sufficient authority | **OK** — SEND, RECV and CONSOLE_WRITE are operation-specific; the two self actions follow ADR-0031's trusted-current-task rule. | Can I use yield/exit to name another task or a broad unrelated capability to access the console? No task target argument exists, and console kind plus right is required. |
| Checks before observable side effects | **OK** — release decode precedes handler access; debug console authority precedes page probing and output; IPC preflights precede mutation. | Can denial still emit user data or expose foreign capability state? Inspected rejection paths emit nothing and resolve only caller-owned handles. Typed own-table error distinctions are deliberate under ADR-0030, not a global timing noninterference proof. |
| Move-only transfer | **OK** — description preserves the existing IPC gate; send checks TRANSFER, cap_take consumes the leaf and bumps its slot generation, and recv installs the moved value. | Can I retain a cloned token merely by encoding a transfer handle? `Capability` has neither Copy nor Clone; stale/unauthorized/has-children transfers fail before endpoint commit. |
| Duplication needs explicit authority | **OK** — cap_copy checks DUPLICATE and rights subset (`cap/table.rs:194–218`), and is absent from v1 EL0 dispatch. | Can I select a hidden syscall or use transfer to manufacture extra authority? Decode has no duplication arm, and transfer moves existing authority. |
| Atomic revocation | **N/A** for changed behavior — revocation is neither changed nor newly exposed or promised as cross-table. Existing bounded local traversal is cooperative; received caps become independent roots. | Can I rely on this text to assume sender revoke reaches a transferred cap or SMP-atomic revocation? No such claim is made; this review does not expand local v1 revocation into either guarantee. |

## 2. Trust boundaries

| Item | Outcome and rationale | Malicious-caller question and resolution |
|---|---|---|
| Userspace inputs validated before use | **OK** — decode, capability lookup/type/right checks, control-plane current-task gate and console range/page validation support the specified boundary. | Can malformed registers select a kernel-only API or a foreign task? Exhaustive dispatch prevents extra services; scheduler bindings supply current identity. |
| User pointers through validated mappings | **OK** — the only pointer-taking v1 call uses current-task translation and USER permission before reading, as the new prose says. | Can an in-window but privileged/unmapped page leak through console_write? Whole-range probe rejects it; USER permission is loader-dependent, which SECURITY:27 explicitly scopes to the trusted image path. |
| Lengths checked against mapped region | **OK** — checked range arithmetic and page probes precede output, followed by bounded 256-byte staging. | Can a wrapping length or a valid first page with an invalid later page produce a partial unauthorized read/output? Both are rejected before first output; zero length accesses no bytes. |
| Typed message contents | **OK** — fixed register words form Message through decode_send_message; recv returns typed outcomes in registers. | Can an IPC payload trick the kernel into following a hidden pointer or parsing extra buffer bytes? The message carries three opaque parameter words and label, not a dereferenced user message buffer. |
| IPC cannot grant unheld authority | **OK** — send validates the transferable cap in caller table; receive moves that cap without widening its rights. | Can sender forge authority, or receiver create authority by demanding delivery into a full table? Lookup/TRANSFER checks and capacity preflight reject those paths; no stronger cross-table revoke guarantee is inferred. |

## 3. Memory safety

| Item | Outcome and rationale | Malicious-caller question and resolution |
|---|---|---|
| New unsafe satisfies policy | **N/A** — no unsafe code, unsafe signature, SAFETY text or audit entry changes. | Can the documentation quietly authorize a new raw-memory bypass? It requires mapping validation and states the trusted-image limitation; no unsafe call surface is expanded. |
| Safety invariants for callers | **OK** within claim scope — inspected BSP dispatcher context and scheduler calls retain single-core/masked-SVC and temporary-reference discipline; no safety contract is broadened. | Can an EL0 register substitute kernel scheduler/table/frame pointers? The BSP constructs these from its trusted statics and scheduler; registers carry data/handles only. This is not a fresh full-tree unsafe audit. |
| No uninitialized data exposed | **OK** within claim scope — console staging starts zeroed, copies only validated initialized page bytes and emits only the filled chunk; error return payloads are zeroed. | Can oversized or partial-page access emit uninitialized staging bytes? Range/probe checks and chunk slices prevent that path; loader frames are fresh and zero-initialized before copying image bytes. |
| No use-after-free | **OK** for changed description — exit is accurately described as retaining resources; it introduces no free/reuse path. | Can the new teardown claim invite access to resources it says were reclaimed? No: absence of reclamation is explicit and source-backed; future destruction semantics are not approved. |
| No mutable alias violation | **OK** for changed description — no reference construction changes; dispatch field borrows finish before scheduler effects. | Can a caller interleave mapping/table mutation during copy or retain a mutable scheduler borrow across a switch through a new API? No new API exists; current cooperative masked context is the inspected scope, without an SMP claim. |

## 4. Kernel-mode discipline

| Item | Outcome and rationale | Malicious-caller question and resolution |
|---|---|---|
| No ISR allocation | **N/A** — no ISR or allocation path changes and the documents make no new ISR claim. | Can this change induce allocation from an interrupt callback? It adds prose only and no executable callback. |
| No unbounded kernel loops | **N/A** for a new loop — no loop changes; existing console polling and panic spin are not certified as bounded. | Can a hostile task halt or monopolize execution despite this review? The non-SVC kernel panic and lack of availability guarantee are explicitly disclosed; console polling and cooperative scheduling are not claimed to provide hostile-workload availability. |
| Minimized critical sections | **N/A** for a critical-section change — no masking, scheduler or locking delta. | Does this text promise protection under preemption/SMP while current context reads are non-atomic? No; this report retains the current cooperative/masked interpretation, and the prose makes no concurrency guarantee. |
| No new hot-path kernel panic | **OK** — no runtime panic is introduced; SECURITY:28 correctly exposes existing non-SVC whole-kernel panic behavior. | Can I panic the kernel with an execution-time fault even though syscall inputs are validated? Yes; the document says so, avoiding the historical denial-of-self understatement. This known limit is not a newly introduced defect. |
| Allocation exhaustion returns typed error | **N/A** for a changed allocation path — none exists; no universal exhaustion-recovery claim is added. | Can readers assume task_exit recovers leaked slots/frames/caps and supports unbounded task churn? SECURITY:29–31 explicitly says it does not reclaim and disclaims hostile resource-isolation guarantees. Existing boot expect/panic choices are not certified as recoverable. |

## 5. Cryptography

| Item | Outcome and rationale | Malicious-caller question and resolution |
|---|---|---|
| No custom cryptographic primitives | **N/A** — no crypto implementation or cryptographic assurance is introduced. | Can an attacker exploit a new primitive chosen by this change? There is none. |
| Keys absent from logs/errors/Debug | **N/A** — no keys, key type or key diagnostic path is added. | Can a caller cause newly added key material to print? There is no such material or path. |
| Constant-time comparisons | **N/A** — no cryptographic comparison changes or constant-time promise. | Does the review imply syscall/capability timing is secret-independent? No; source-based authority checks are not a timing proof. |
| Acceptable randomness | **N/A** — no entropy source or random-based security scheme changes. | Can predictable new randomness grant authority? No randomness is introduced or relied on by this delta. |
| Correct nonces/IVs/salts | **N/A** — no cryptographic protocol, nonce, IV or salt. | Can replay exploit new nonce handling? No such handling exists in scope. |

## 6. Secrets and logging

| Item | Outcome and rationale | Malicious-caller question and resolution |
|---|---|---|
| No secret in diagnostics/errors | **OK** for the delta — no secrets or diagnostic code are added; console wording accurately requires authority and validated user bytes. | Can I point console_write at kernel secrets or use release syscall 5 to emit them? Normal release rejects first; debug requires cap/range/USER checks. This does not certify every pre-existing panic/log statement secret-free, nor prevent an authorized task printing its own bytes. |
| Sensitive Debug redacts or absent | **N/A** for new Debug — none changes; inspected CapObject/Capability implementations (`cap/mod.rs:148,185`) redact object identity while retaining rights. | Can this documentation expose raw capability object identity or claim rights are entirely hidden? It publishes operation names/rights, not live tokens, and makes no blanket Debug secrecy claim. |

## 7. Dependencies

| Item | Outcome and rationale | Malicious-caller question and resolution |
|---|---|---|
| New dependency follows addition policy | **N/A** — exact changed-file list contains only Markdown, no manifest/lockfile/toolchain changes. | Can an unreviewed crate enter through the update? No dependency is added. |
| Trust category understood | **N/A** for a new dependency — no build-time or kernel-linked trust changes. | Does embedded hello mean a newly accepted opaque/proprietary blob? No; it is the existing image built from in-tree Rust, with no artifact or build change here. |
| cargo-vet decisions updated | **N/A** — no dependency graph or trust-policy changes require a new decision. | Can a widened trust exemption hide in this documentation change? No vet/config/settings files change; CONTRIBUTING points to existing gates without inventing new certifications. |

## 8. Threat-model impact

| Item | Outcome and rationale | Malicious-caller question and resolution |
|---|---|---|
| Reconcile documented threat model | **OK** — SECURITY:7 explicitly separates architectural goals from implementation limits; :27–31 states trusted loader, global fault panic and non-reclaiming exit. | Can an operator mistake this update for safe hostile-workload execution or arbitrary-image loading? The explicit limits and no-guarantee statement directly reject that inference. Older security-model TaskFault/supervisor/cleanup claims are not treated as executable truth. |
| Model shift updated or follow-up linked | **OK** — runtime and normative security design are unchanged; this is a factual correction. The approved plan links T-046's imminent Step-3 whole-chapter correction and T-052's standards correction. | Could stale broader chapters silently override this new present-state account? The entry text labels goals versus current limits, and the named follow-up tasks own the known discrepancy; no new protection is promised pending those tasks. |

Architectural principles cross-check: **P1/P4 OK**, specific object caps remain required and self actions follow ADR-0031's trusted current identity; **P2/P3 OK**, no privileged feature/driver moves or unsupported userspace-driver completion claim; **P5/P6 OK**, no Rust/assembly or HAL change; **P7 OK**, no blob/dependency addition; **P8 OK**, the work follows Accepted ADR-0040/0043 and ABI ADR-0030/0031 without deciding a new contract; **P9/P10 OK**, English prose and no new diagram; **P11 OK**, no reproducibility inputs change or fresh reproducibility proof claimed; **P12 OK**, documentation reports partial implementation honestly and task/phase completion is not invented.

## Verdict

**Approve — both distinct fresh security rounds, documentation scope.** Zero verified findings or unresolved blockers in either pass; all applicable changed-claim checks are OK and every N/A is bounded and justified above. The cumulative source accurately states the ABI, release/debug behavior, current-task authority, kernel-only services, trusted embedded image, whole-kernel non-SVC fault impact and absent exit reclamation.

T-038 and existing loader/lifecycle/concurrency limitations remain separately owned and are not certified fixed. T-046 and T-052 own the imminent architecture/standards refresh. No unsafe amendment, advisory, external review message or issue is introduced by this step.

Maintain the explicit maintainer SECURITY wording review before merge. Agent review permits the authorized In Review transition and next local step; it does not promote Done, authorize merge or close Phase B.2. The coordinator statically verifies canonical navigation, task state and trailers when publishing this combined record; that publication is not another independent review of itself.
