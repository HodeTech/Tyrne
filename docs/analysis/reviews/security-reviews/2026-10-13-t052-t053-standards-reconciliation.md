# Security review 2026-10-13 — T-052 / T-053 standards reconciliation

- **Change:** development, cumulative 98378b5add44755f7cbab6e8bc96337accf0574a..d553efe90ded0698f220a13b67fd9289864f85d0.
- **Reviewer:** distinct fresh Codex security contexts b22_step8_r1_security and b22_step8_r2_security, coordinator consolidation; no maintainer approval attributed.
- **Date:** 2026-10-13.
- **Separation:** fresh initial contexts in parallel followed by actual primary-report cross-reading, with explicit chronology below.
- **Unsafe audit cross-reference:** no unsafe code or safety-contract delta; unchanged runtime boundaries inspected only to verify prose. HIGH T-038 remains unresolved.
- **Code-review cross-reference:** [paired five-role artifact](../code-reviews/2026-10-13-t052-t053-standards-reconciliation.md).
- **Evidence:** [reconciliation](../../reports/2026-10-13-t052-t053-standards-reconciliation.md), [retained verification](../../reports/2026-10-13-t052-t053-verification-evidence/README.md).

## 1. Capability correctness

OK for descriptions: no new authority path; absent logging/control services remain planned and current capability boundaries are not overstated.

## 2. Trust boundaries

OK: application-specific hello exit is distinguished from arbitrary non-SVC EL0 whole-kernel panic. Supervision and retained-resource reclamation remain future work.

## 3. Memory safety

N/A for implementation changes; no unsafe/source delta. No new soundness proof or completed lifecycle guarantee is inferred.

## 4. Kernel-mode discipline

OK: exact panic-family deny scope/allowances, review-only unimplemented boundary, target-wide panic flags and absent ISR logging transport match source.

## 5. Cryptography

N/A: no primitive, key, protocol or cryptographic certification introduced.

## 6. Secrets and logging

OK: planned status does not waive normative redaction/context rules; current raw Console/UART limitations are explicit.

## 7. Dependencies

OK for factual guidance: zero dependency changes; audit/vet remain planned at first external dependency, while normative trust review is retained. Pinning/build success is not bit-for-bit certification.

## 8. Threat-model impact

OK: descriptions become more precise without claiming new defenses, closing HIGH T-038 or waiving whole-phase gates. Maintainer approval remains separate.

## Verdict

**Approve** — both fresh security passes and actual peer cross-reads complete; zero source/seam findings and zero unresolved delta findings.

## Both-round consolidation

| Round | Fresh context / configured model / effort | Actual disposition |
|-------|------------------------------------------|--------------------|
| 1 code | b22_step8_r1_code / GPT-6.1 Sol / high | Five roles clean; initial Comment solely awaiting actual security report; actual peer cross-read complete, final Approve. |
| 1 security | b22_step8_r1_security / GPT-6 Astra / high | Initial scoped Approve; actual primary cross-read complete, final Approve; zero source/seam findings. |
| 2 code | b22_step8_r2_code_fresh / GPT-6.1 Sol / high | Fresh cumulative assessment and actual security cross-read complete, final Approve; zero new findings. |
| 2 security | b22_step8_r2_security / GPT-6 Astra / high | Fresh cumulative assessment and actual primary cross-read complete, final Approve; zero new findings. |

All four required fresh contexts fully read the required governance corpus before assessment. Both primary reports assess five roles, the 11 literal code-standard checklist items, P1–P12 and every task AC/DoD. Both complementary reports assess eight adversarial axes, all 32 literal security-standard checklist items plus the master plan's allocation-exhaustion item (33 total), P1–P12 and task coverage. Model/effort labels record coordinator configuration, not introspection. Initial passes ran in parallel, then actual reports were cross-read; this is not a claim of sequential code-then-security execution. R2 uses different fresh contexts. Prior-round continuity is attributed after the R2 initial checkpoints.

Before R1 security's initial checkpoint the coordinator relayed the primary's interim no-source-finding status and inventory counts, without its report. The security and primary reports disclose this chronology; their source checks/checklists were performed independently, and actual artifact exchange followed the initial checkpoints. The original R2 primary accidentally read draft future-result assertions from an unexecuted coordinator publication template while locating the navigation diagnostic, after its source checks and before its formal checkpoint. Its supplementary report discloses this exposure and is not counted as the required R2 primary. The coordinator commissioned new empty context b22_step8_r2_code_fresh to repeat that required primary pass; neither the required fresh replacement nor the R2 security initial pass received peer verdicts/reports. The supplementary report remains retained separately below with its procedural Comment verdict. The coordinator read all five complete delivered reports and addenda before consolidation. Their final bytes are retained verbatim below and bound by the evidence manifest. No source correction commit was necessary in either round. The supplementary assessment is preserved as additional evidence, not a substitute for the required fresh pair.

One report-only packaging issue was corrected by its owner: R1 security's S28 infrastructure destination was qualified for this canonical directory. The QA correction and later primary consumption are recorded in their addenda. This is not a Step 8 source finding. Required R2 primary initially printed all 11 checklist names/outcomes; an append-only QA addendum supplies the full literal prompts and records the earlier wording overstatement, preserving the initial checkpoint. That is report completeness, not a source defect or another round. Reviewer diagnostic false positives and failed exploratory commands remain disclosed rather than converted into defects.

The frozen content range contains 24 paths (18 Markdown plus six JSON/text evidence files), all documentation. The initial static snapshot has 19 visible paths before subsequent reports/result/publication; initial navigation has 367 visible Markdown files/6,116 local targets, while the later frozen corpus has 368/6,140. Snapshots and diagnostic domains are separate. All 15 retained source/config/runner digests match baseline and frozen source. Exact after-search output is 73 lines; broad baseline has 141 lines across 29 files, not 141 defects. Git-scope inventory is 470 subjects and 75 captured scope strings. All 15 standards have 20 tagged opening fences and zero untagged/unclosed fences. Runtime/config/CI/Accepted ADR bytes remain unchanged.

No new Cargo/QEMU/Miri/coverage/hosted/reproducibility execution or live remote-protection read-back is claimed for this prose-only step. Existing third-party navigation diagnostics do not certify future T-056 grammar. Step-only diff checking passes; inherited prior raw-log EOF whitespace remains disclosed and unmodified. T-038 remains Ready/HIGH and whole-phase C/D gates remain. Canonical publication/state checks are coordinator bookkeeping, not an additional independent review. T-052/T-053 stop In Review without date_done or maintainer approval. PR49 publication barrier remains.


---

## Retained Round 1 security report

# Security review 2026-10-13 — T-052 / T-053 Step 8, independent round 1

- **Change:** `development`, cumulative `98378b5add44755f7cbab6e8bc96337accf0574a..d553efe90ded0698f220a13b67fd9289864f85d0` (24 changed paths).
- **Reviewer:** Codex independent complementary security agent, `b22_step8_r1_security`; not the implementation author and not maintainer approval.
- **Date:** 2026-10-13.
- **Separation from code review:** independent fresh security context, with an empty checklist and source-first adversarial review. This initial pass ran in parallel with the primary code review. The actual primary report had not been received or read when this verdict was recorded; no sequential-after-code-review claim is made. A later actual-report cross-read will be appended separately. Before the initial completion checkpoint, the coordinator relayed the peer's interim zero-confirmed-finding status and inventory counts; that progress relay did not contain its actual report. The checklist, source verification and initial verdict here are this reviewer's own. This is the approved plan's complementary review arrangement, not a claim that the solo maintainer's several-hour cold-review obligation has occurred.
- **Unsafe audit cross-reference:** no unsafe, executable, audit-log or runtime contract changes. Existing source cites UNSAFE-2026-0002, 0014, 0020 and 0033; targeted audit/history context was inspected, not re-certified.
- **Initial verdict:** **Approve** for the reviewed documentation delta. **Zero confirmed findings.** Completion still requires the paired report seam, the second fresh round, final publication checks and root-owned record updates. No Done promotion, runtime security certification, hosted execution or publication is authorized by this verdict.

## Method, scope and reading record

Applied [perform-security-review](../../../../.agents/skills/perform-security-review/SKILL.md) and [conduct-review](../../../../.agents/skills/conduct-review/SKILL.md), the [security standard](../../../standards/security-review.md), its [master plan](master-plan.md), and the [code review standard](../../../standards/code-review.md) / [master plan](../code-reviews/master-plan.md). The changed fault-containment, panic, logging and verification claims make this a security-relevant documentation review even though no executable surface changes. The adversary considered here is a future contributor or reviewer acting on inaccurate assurance: skipping a check believed automated, treating a planned protection as delivered, relying on a misleading runtime description, or promoting a task based on evidence that never ran.

Fully read AGENTS.md and CLAUDE.md; all 141 lines of current.md including dated historical body; all 42 numbered ADRs in ascending order (0001–0033, 0035–0043; 0034 is reserved); all 15 standards including README; both complete task contracts; the complete approved 13-step plan; the Step 8 preflight and reconciliation reports; both relevant skills and both review master plans. Bounded reads were used and truncations were recovered with narrower reads. All cumulative modified hunks and all newly added evidence contents were inspected, including the 470-subject scope inventory and both downstream hit files. Whole source files read include Cargo.toml, .cargo/config.toml, Cargo.lock, main.json, ci.yml, tools/run-qemu.sh, tools/smoke.sh, hello main, Console and PL011 implementation, plus the complete security-model chapter and historical Phase-B closure security review. Kernel scheduler/BSP exception/vector/syscall and lint source, other architecture/skill downstream contexts, audit entries and Phase E ownership were targeted reads, not whole-runtime or whole-audit-log audits.

The preflight scope reasons for security-review.md, P11 and infrastructure.md were committed at `cbd4cd1`, before T-052 content `7bde23e` and T-053 content/evidence `d553efe`. The naming rule is authorized by Accepted ADR-0042 after ADR-0041's separate recovery Acceptance (`862bfb6`) and atomic supersession (`714c74b`). The four other selected T-052 choices are approved claim corrections. The scope is not expanded into fixing pre-existing runtime debt or implementing planned logging, supervision, reclamation or new enforcement.

## Source-backed security claims

| Surface | Independent inspection and result |
|---|---|
| Panic diagnostics | `bsp-qemu-virt/src/main.rs:1690–1725` reconstructs the low/high UART alias from SP, writes `!! tyrne panic !!`, formats PanicInfo and spins. `exceptions.rs:281–314` carries class/ESR/class-id through the panic message; unexpected IRQ handling carries an IRQ id. Saving registers in a trap frame is not printing them. `error-handling.md:71–76` and logging's panic description accurately distinguish this from a generic register dump/backtrace/reset/shell. |
| EL0 fault versus Rust panic | `vectors.s:218–260` branches every non-SVC synchronous cause to panic_entry. `userland/hello/src/main.rs:56–60` explicitly calls task_exit(101) from its own panic handler. Error-handling §5/§8 does not turn that application convention into arbitrary execution-fault containment. |
| Exit and future lifecycle | `kernel/src/sched/mod.rs:948–992` retains Task/AS/table state and abandons the caller frame through dispatch; the source explicitly describes orphaned Ready metadata. Phase E E3 at `phase-e.md:41–54` owns supervisor Fault endpoints; lifecycle epic at 172 onward supplies reclamation prerequisites. No current TaskFault, supervisor notification or resource teardown is promised. |
| Logging and context safety | Full `hal/src/console.rs` and `bsp-qemu-virt/src/console.rs` show a synchronous byte sink and polling UART, including the TX-full spin. No structured facade/ring/service/control API is in the six-member workspace. Logging's top and section-level Planned notes do not waive current secret-redaction or nonblocking-context constraints. The new ISR wording explicitly rejects treating raw UART as a nonblocking logger. |
| Panic-family and incomplete markers | Kernel lib lines 62–66, HAL lib 35–37 and BSP main 26–28 contain panic/unwrap/expect denies, with scoped allowances in trusted boot/demo, fatal/invariant and test paths. test-hal/userland do not inherit these denies. All six manifests opt into the nine workspace lint entries; Cargo has todo deny and no unimplemented deny. The two host stubs at tyrne-user lib 125–128 and 151–154 remain intentional. No lint level or implementation changed. |
| Panic configuration and lint coverage | .cargo/config.toml's aarch64-unknown-none rustflags carry panic=abort for every build of that target, including userland. Root profile comments explain the host-test distinction. Host alias, bare-metal BSP/userland, release/perf BSP and ARM workspace Clippy use -D warnings in ci.yml. missing_docs/pedantic remain warn in Cargo; emitted warnings are escalated on covered targets, with scoped source allowances and internal-doc review limitations acknowledged. |
| Smoke and CI | tools/smoke.sh runs ordinary matching debug/release images, builds userland first when using its default ELF, checks greeting/exit/completion by profile and rejects listed panic/fault markers. `--int` uses int,unimp, not guest_errors; it does not assert an exact SVC count or prove general page-fault containment. ci.yml contains both real guests, rejection probes, stable/Miri/ARM coverage and informational coverage. This review inspected those commands; it did not execute them. |
| Protection and approval | main.json has six exact app-15368 check bindings, strict checking, linear history, conversation resolution, force/deletion false, approving-review count 0 and enforce_admins false. code-review §Tooling preserves that distinction from the maintainer's cold-review policy. No fresh live GitHub read or approval is inferred from versioned policy. |
| Dependencies and reproducibility | Cargo.lock contains only six in-tree packages. No first external dependency, supply-chain directory, audit/vet CI job or binary-comparison job is introduced. P11 and infrastructure now distinguish required properties from delivered verification. Original principle Statement/Why/Applies and all reproducibility bullets are byte-preserved. SHA-256 evidence checks establish file identity, not boot authenticity, Rust soundness or bit-for-bit build reproducibility. |
| Downstream/provenance | Both retained searches were read. 141 baseline lines are broad hits, not 141 defects. The three search domains are byte-identical from 23391c7 to 98378b5. Exact retained after-search argv reproduces the 73-line file byte-for-byte at d553efe. Standards updates plus unchanged normative/historical/already-correct architecture/skill dispositions are credible; no live restatement of the five false claims was found requiring another change. |

## Eight-axis checklist

The following includes **all 32 literal checklist items from the security standard**, followed by the **one additional allocation-exhaustion item from the master plan**. There are 33 reviewed items in total, not 33 items in the standard. Item text is preserved; relative navigation inside applicable items is adjusted for this report's canonical directory. N/A means the delta introduces no corresponding mechanism, not that the whole kernel has been certified to satisfy that property.

### 1. Capability correctness

**Adversarial question:** Can these edits let a caller or implementer mistake a planned capability or a review convention for currently checked authority?

- **S01. Every privileged operation introduced by this change requires a capability.**
  - N/A — no privileged operation is introduced; planned LogControlCap is explicitly unavailable.
- **S02. The capability required is the **narrowest** one that permits the operation (no privilege escalation by accepting a broad capability where a narrow one would do).**
  - N/A — no operation authority or capability requirement changes.
- **S03. Capabilities are checked **before** observable side effects. A failed check does not leak information that the call was attempted.**
  - N/A — no capability check or side-effect order changes; source behavior is not re-certified.
- **S04. Capability transfer (if any) is move-only; no accidental cloning.**
  - N/A — no IPC transfer or capability value is modified.
- **S05. Capability duplication (if intended) itself requires an explicit `Duplicate`-style authority.**
  - N/A — no duplication operation is introduced; existing normative duplication obligations remain.
- **S06. Capability revocation (if applicable) takes effect atomically; no partial state where the revocation is half-applied.**
  - N/A — no revocation mechanism is touched; deferred cross-table semantics are not claimed delivered.

### 2. Trust boundaries

**Adversarial question:** Can a caller exploit a promise of fault containment, validation or supervision that the implementation does not deliver?

- **S07. Every input crossing from userspace to the kernel is validated before use.**
  - OK for documentation scope — current syscall-input validation is distinguished from arbitrary non-SVC execution faults; no validation code changes.
- **S08. Pointers from userspace are **never** dereferenced in kernel mode without going through a validated mapping.**
  - N/A — no user-pointer dereference is added or modified; the security-model mapping assumptions remain explicit.
- **S09. Buffer lengths provided by userspace are range-checked against the actual mapped region.**
  - N/A — no buffer length or copy implementation changes.
- **S10. Message contents from userspace are parsed into typed structures; no raw bytes are consumed in privileged code.**
  - N/A — no userspace message parser or privileged byte consumer changes.
- **S11. Cross-task IPC does not grant the receiver any authority the sender did not have or did not explicitly transfer.**
  - N/A — no IPC authority transfer changes; no new cross-task service is delivered.

### 3. Memory safety

**Adversarial question:** Can these edits hide a lifetime, initialization or aliasing assumption or present test evidence as a universal safety proof?

- **S12. Any new `unsafe` block meets [unsafe-policy.md](../../../standards/unsafe-policy.md).**
  - N/A — no new unsafe block, unsafe function, assembly or audit-log mutation.
- **S13. Invariants stated in `# Safety` sections hold for every call site, not only "the usual" one.**
  - N/A — no Safety contract or caller changes; targeted source/audit reading is not an audit of every call site.
- **S14. No uninitialized memory is exposed. Where a buffer is declared but only partially filled, the unused portion is zeroed or the buffer is returned as `MaybeUninit`.**
  - N/A — no memory or buffer creation/exposure changes.
- **S15. No use-after-free. Lifetimes on raw pointers are reasoned about explicitly.**
  - OK for documentation scope — retained Task/AS/table/frame state after exit is named accurately; no deallocation or pointer lifetime changes.
- **S16. No aliasing violations. Mutable pointers to the same memory do not coexist.**
  - N/A — no raw-pointer borrowing or context-switch implementation changes.

### 4. Kernel-mode discipline

**Adversarial question:** Can the revised wording lead a contributor to introduce blocking logging, panic or unreclaimed resource growth on a path falsely described as safe?

- **S17. No allocation in interrupt service routines.**
  - OK for documentation scope — ISR no-allocation requirement is preserved; no allocator added.
- **S18. No unbounded loops in kernel mode; every loop has a documented termination.**
  - OK for documentation scope — current panic spin is honestly described and UART is not advertised as a nonblocking ISR transport; no loop is introduced.
- **S19. Critical sections are minimized. Scheduler state is held for as short a time as possible.**
  - N/A — no critical-section duration, lock or scheduler ownership changes; logging context restrictions remain normative.
- **S20. No new kernel panic introduced on a hot path.**
  - OK for documentation scope — no new panic path; crate deny/allow scope and existing non-SVC whole-kernel panic are accurately described.

### 5. Cryptography

**Adversarial question:** Does a checksum or planned audit tool become a fabricated cryptographic guarantee?

- **S21. No roll-your-own primitives. If a primitive is introduced, it is a well-known algorithm from a reviewed crate (or, if truly novel, it comes with a separate ADR and a cited proof or analysis).**
  - N/A — no cryptographic primitive or crate is introduced.
- **S22. Keys are never logged, returned in error messages, or exposed via `Debug`.**
  - N/A — no key material or crypto diagnostic path is introduced; logging prohibition remains.
- **S23. Constant-time comparisons are used where timing leaks matter.**
  - N/A — no secret-dependent comparison or timing policy changes.
- **S24. Randomness comes from an acceptable source — not `rand::thread_rng` with no seeding story.**
  - N/A — no entropy source or random generator changes.
- **S25. Nonces, IVs, and salts are handled correctly per the primitive's contract.**
  - N/A — no nonce, IV, salt or protocol state exists in the delta.

### 6. Secrets and logging

**Adversarial question:** Could the Planned banner be read as permission to log secrets or call blocking UART facilities in restricted contexts?

- **S26. Secrets (keys, tokens, capability bits) are not included in logs, panic messages, debug output, or error types.**
  - OK for documentation scope — secret-redaction requirements explicitly continue to apply to raw current diagnostics. No new runtime output or claim of blanket existing secret-freedom is introduced.
- **S27. `Debug` impls on security-sensitive types redact sensitive fields (or are not implemented at all).**
  - N/A — no Debug implementation changes; conceptual secret-type redaction requirements are preserved.

### 7. Dependencies

**Adversarial question:** Could contributors skip dependency review because absent audit/vet jobs are described as already running?

- **S28. Any new dependency has been evaluated under [infrastructure.md](../../../standards/infrastructure.md) dependency-addition rules.**
  - N/A — no dependency is added or upgraded; Cargo.lock/config bytes are unchanged.
- **S29. The dependency's trust model is understood. A build-time-only crate is very different from a kernel-linked crate.**
  - OK for documentation scope — audit/vet are accurately planned for the first external dependency, without relaxing addition-time trust review.
- **S30. `cargo-vet` trust decisions are updated accordingly.**
  - N/A — no dependency trust decision changes; the normative checklist remains, but absent CI execution is not fabricated.

### 8. Threat model impact

**Adversarial question:** Does this change conflate the trusted embedded demo, future hostile services and governance approval states?

- **S31. The change is reconciled with the documented threat model in [`docs/architecture/security-model.md`](../../../architecture/security-model.md).**
  - OK — reconciled with the fully read current security-model, especially fault containment, bounded resources and supply-chain sections. Current/future protection is more precise.
- **S32. If the change reshapes the threat model, the PR includes the threat-model update or links to a follow-up PR scheduled imminently.**
  - N/A — implemented threat boundaries are unchanged. The clarification names existing Phase E/E3 ownership rather than claiming a new defense or requiring unrelated feature implementation.

### Master-plan additional item

- **M33. Every allocation path returns a typed error, not a panic, on exhaustion.**
  - N/A for implementation — no allocation path changes. Documentation review is OK: current security-model explicitly limits typed errors and retains trusted boot fail-stop/loader leakage/exit-retention caveats. Nothing in Step 8 claims universal recoverable exhaustion or completed reclamation.

## Architectural principles P1–P12

| Principle | Assessment |
|---|---|
| P1 — No ambient authority | OK for delta: no authority introduced; planned logging/control capabilities are not advertised as implemented. |
| P2 — Smallest defensible TCB | OK: no privileged code/dependency addition; raw diagnostic description is not a new subsystem. |
| P3 — Userspace drivers/filesystems/network | OK: current fault-containment limits are candid and future supervision remains Phase E; the principle is not weakened. |
| P4 — Capability checks at trust boundaries | OK for delta: no boundary implementation changes or invented current log-service routing guarantee. |
| P5 — Rust and disciplined assembly | N/A implementation: all 24 paths are documentation/evidence; no unsafe alteration. |
| P6 — HAL separation | OK: raw HAL Console/BSP UART is named correctly; no hardware access moved into generic kernel code. |
| P7 — No proprietary blobs | OK: no executable binary or proprietary dependency added; evidence is text/JSON. |
| P8 — Decisions as ADRs | OK: naming follows Accepted 0042 after 0041 supersession; 0043/approved plan authorizes scoped execution. Four other changes reconcile source claims. |
| P9 — English | OK: newly authored prose/evidence descriptions are English; git subject inventory preserves literal historical data. |
| P10 — Mermaid | OK: no new architectural diagram; existing standards Mermaid remains intact, fences tagged. |
| P11 — Reproducibility | OK: original normative bytes preserved; delivery note makes absence of audit/vet and binary comparison explicit. No reproducibility certification is inferred. |
| P12 — Complete declared scope | OK at review freeze: tasks remain In Progress with unchecked criteria; intentional host stubs are distinguished from incomplete runtime features. Neither this review nor the initial static result promotes work. |

## Task acceptance and definition-of-done coverage

These are review observations, not checked boxes or maintainer completion. Both task contracts remain untouched by this reviewer.

| Task item | Evidence / assessment |
|---|---|
| T-052 AC1 naming | OK: testing.md §Test naming and References, Accepted ADR-0042; actual #[test] functions at ipc/mod.rs 919–970; no source/name/lint change. |
| T-052 AC2 panic | OK: error-handling §5 and BSP/exceptions spans above; no promised automatic dump follow-up. |
| T-052 AC3 unimplemented | OK: error-handling §10, Cargo's todo deny, six manifest opt-ins and two preserved host stubs. |
| T-052 AC4 logging | OK: top banner and per-section Planned boundaries, actual six-member Cargo workspace and Console/UART source. |
| T-052 AC5 denies | OK: error-handling §4/Tooling, code-style §Lints and exact kernel/HAL/BSP attributes/allowances. |
| T-052 AC6 downstream | OK: retained 141/73 line searches, exact after-search reproduction and reconciliation dispositions across required domains. |
| T-052 adjacent fault AC | OK: error-handling §8 accurately separates voluntary exit, whole-kernel panic, retained objects and Phase E/E3 future mechanisms. |
| T-052 DoD links | OK as bounded diagnostic at frozen source: fresh tracked-corpus scan finds zero candidates; scan limitations below. |
| T-052 DoD allowed diff | OK: 24 cumulative paths, named standards plus documented pre-edit downstream/tooling reasons and evidence/state allowance; no executable/config changes. |
| T-052 DoD language/fences | OK: English new prose; 20 tagged opening fences across all 15 standards, no untagged or unclosed fence. |
| T-052 DoD commit | OK: focused English docs(standards) commits with ADR-0040/0042/0043 references; review trailer/publication is root-owned later bookkeeping. |
| T-052 DoD In Review/current | Pending intentionally: In Progress and unchecked at frozen source; requires both complete fresh rounds before root moves state. Current/task index agree. |
| T-053 AC1 panic flags | OK: target-wide config, including userland, and host harness unwinding distinction. |
| T-053 AC2 live tooling | OK: code-review Tooling matches inspected ci.yml/main.json and preserves advisory coverage/zero-approval/admin-bypass limits. |
| T-053 AC3 scopes | OK: independent git-log extraction equals retained 470 subjects and 75 captured scope strings; recommended spellings, historical aliases and review-agreed extension remain. |
| T-053 AC4 lints | OK: all nine actual workspace entries are listed with correct levels; Cargo remains authoritative. |
| T-053 AC5 log path | OK: run-qemu prints TMPDIR-or-/tmp with PID suffix; example reads that printed path; smoke tracing is separately described. |
| T-053 AC6 fences | OK: both commit examples and naming block tagged text; stateful all-standards scan passes. |
| T-053 AC7 test-hal | OK: existing crate described as existing in testing Fixtures. |
| T-053 AC8 grammar | OK: release.md uses “a Tyrne-specific”. |
| T-053 adjacent tooling AC | OK: missing_docs warning escalation, planned audit/vet, live smoke and reproducibility limits are precise; no enforcement level change. |
| T-053 DoD links | OK as bounded frozen-source diagnostic; root must repeat for later appended reports/index links. |
| T-053 DoD scope | OK under documented step evidence allowance and three pre-recorded adjacent-file reasons. |
| T-053 DoD commit | OK: docs(standards) commit and relevant ADR references verified. |
| T-053 DoD In Review/current | Pending intentionally until both paired rounds complete; no date_done or unauthorized Done promotion. |

## Findings and dispositions

**Confirmed findings: none.** No severity is assigned to preferences or pre-existing runtime debt.

The old Phase-B security review contains broader historical assurances, including “denial-of-self” wording and historical memory/logging claims. Those are preserved evidence, not fresh assurance supplied by Step 8; the current security-model and changed standards explicitly state whole-kernel panic, retained resources and limited verification. Likewise, pending T-038, UART polling, incomplete reclamation, future TaskFault delivery and the absence of a structured logger are known current limits, not defects introduced by this documentation-only change. This review does not approve exposing untrusted services before their existing gates.

No loophole was found in the changed wording that waives secrets/context safety merely because logging is planned. P11's delivery note does not remove reproducibility obligations. The scope inventory does not create an allowlist or prohibit old aliases. Versioned branch protection is not described as requiring a positive approval, and no newly executed runtime/hosted gate is claimed.

## Commands, independent results and limits

| Command / inspection | Actual result |
|---|---|
| git status --porcelain; git rev-parse HEAD | Clean at frozen d553efe before and after verification. |
| git diff --name-only/stat 98378b5..d553efe; complete changed-content read | 24 paths, all under docs; 1,161 insertions / 79 deletions. Evidence accounts for most added lines. |
| Independent Python comparison against git show BASE:path and TIP:path | All 15 retained SHA-256 source/config/runner hashes match both source revisions and working files. No runtime, manifest/config, script, workflow, protection, ADR or audit-log delta. |
| git diff 23391c7 98378b5 -- .agents/skills docs/architecture docs/standards | Empty: retained broad baseline applies to the Step 8 baseline domains. |
| git log 98378b5 --format=%s plus anchored scope extraction | Exactly 470 subjects and 75 captured scope strings, identical to retained subjects/counts. Combined scopes remain whole data strings. |
| Exact downstream-search-method.json after_command | Exit 0; output byte-identical to retained 73-line after file. All 141 baseline lines read; the baseline count is independently confirmed, not converted into a defect count. |
| Independent removal/comparison of added delivery-status paragraphs | P11 whole prior file and infrastructure whole prior file otherwise byte-identical to baseline, preserving every original normative principle/property. |
| Independent stateful standards fence scan | 15 files, 20 tagged openings, zero untagged/unclosed fences. |
| Independent task-state extraction | 46 tasks: 8 Done, 21 Ready, 7 In Review, 2 In Progress, 8 Draft. T-032 Done; T-038 Ready. T-052/T-053 unchecked and without date_done. |
| Fresh read-only corpus diagnostic using inspected /tmp/tyrne-b22-readonly-corpus-scan.py, existing Python Markdown parser; output redirected to reviewer-owned /tmp result | 368 tracked Markdown files, 6,140 local targets, 626 fragments, zero candidates at d553efe. No package installed and no repository file written. This is a bounded third-party diagnostic, not the future T-056 parser or full Markdown-grammar certification. |
| git diff --check 98378b5..d553efe | Exit 0. Prior raw-log files have no delta; inherited EOF whitespace was neither normalized nor represented as a new failure. |
| Commit history/source inspection | Preflight is before content commits; 0041/0042 approved transition precedes naming edit. English conventional subjects and ADR references match task contracts. |

Independent check outputs are held at `/tmp/tyrne-b22-step8-r1-security-checks.json` and `/tmp/tyrne-b22-step8-r1-security-navigation.json` for the coordinator. The retained initial static snapshot is explicitly pre-report and has 19 changed paths; it is not the final 24-path freeze inventory. The earlier initial navigation result has 367 visible files/6,116 local targets, while this later tracked-source scan has 368/6,140. These are different recorded snapshots, not conflicting claims about one run.

No Cargo test/build/clippy, QEMU, Miri, coverage, Linux-hosted check, live protection query, reproducibility comparison or external publication was executed by this review. Source inspection is not execution proof. A failed exploratory attempt to read `bsp-qemu-virt/src/uart.rs` found that nonexistent guessed path; `rg --files` located the actual `console.rs`, which was then fully read. No conclusion depends on that failed lookup. Truncated displays were recovered, not silently counted as full reads.

## Verdict and process boundary

**Approve — initial independent complementary security round 1, zero confirmed delta findings.** All applicable documentation-security axes are OK; implementation-only checklist items are explicitly N/A with reasons. This is not a whole-kernel vulnerability audit or a sign-off on existing unsafe/runtime behavior.

The actual primary code report is still pending at this initial checkpoint. Its subsequent cross-read must be an append-only addendum recording actual content and any verified seam/fix result, without rewriting this initial verdict or inventing a prior sequential pass. A second fresh paired round over the cumulative corrected source remains required. Root owns canonical placement/indexing, the Security-Review trailer, final link/state checks and the eventual In Review transition. No external review comment is sent under this read-only assignment. PR #49 remains the recorded publication barrier; no push, merge, remote-setting write or separate PR was attempted, and its live state was not freshly queried here. Human approval and Done remain with the maintainer.

## Subsequent actual primary-report cross-read — 2026-10-13

After the independent initial completion checkpoint, the coordinator supplied the actual primary report `/tmp/tyrne-b22-step8-r1-code.md`. I read all 169 lines of its initial report, including all five roles, the literal code checklist, P1–P12, every AC/DoD row, command outcomes, false-positive dispositions and its initial Comment verdict. The initial primary bytes read have SHA-256 `d02ea54d18d2cd5501364a024376b4e020acd93330860b795b9f8619a9ccdb03`. Its initial Comment means the peer security/cross-read was pending; it is not a code defect or a request to alter Step 8.

**Seam result: no new finding.** The independently reviewed source remains `d553efe90ded0698f220a13b67fd9289864f85d0`, and no source correction was made or required. Both reports agree on all substantive security-sensitive claims: panic banner/PanicInfo/spin, saved exception diagnostics rather than generic dump, hello exit rather than non-SVC containment, retained exit objects, absent logger/ring/supervision, actual lint/config/CI coverage, zero-required-approval policy, dependency/reproducibility limits, original normative-byte preservation and source-bound evidence scope. Both retain In Progress/unchecked tasks, Ready T-038, whole-phase C/D gates and the publication barrier.

The primary's touched-file navigation diagnostic (463 inline targets/44 fragments) and my later full tracked-corpus diagnostic (6,140 local targets/626 fragments) have different stated domains. Its two initial underscore-slug false positives were corrected by direct heading inspection; they are not findings. Its broad-branch inherited raw-log EOF warnings do not contradict clean Step 8 diff checking or justify changing historical captures. These observations do not convert any static check into runtime, hosted or whole-grammar certification.

After my initial report checkpoint, additional read-only searches confirmed that supply-chain/ is absent and workflows contain no cargo-audit/cargo-vet or binary-comparison command. Searches for TaskFault, LogControlCap and structured logging names across runtime crates found no implementation; the single tyrne-log mention in the HAL Console rustdoc is historical explanatory prose, not a delivered crate. BSP syscall termination prints the fixed exit marker then calls task_exit_current. These checks support the existing verdict and introduce no source finding.

**Report-only QA correction:** the coordinator found that the literal S28 checklist quotation retained the standard-local destination `[infrastructure.md](infrastructure.md)`, which would be wrong after canonical publication in security-reviews. I corrected only that destination to `../../../standards/infrastructure.md`, preserving the checklist wording and initial verdict. This is an authoring error in this temporary review report, not a Step 8 source finding. All rendered relative links in the complete report were then checked against the intended canonical security-reviews directory. No repository file was written.

**Final round-1 security verdict: Approve, zero confirmed Step 8 findings and zero newly discovered peer-seam findings.** The initial verdict/history above remains the initial checkpoint. No fix verification is claimed because there was no source fix. The second fresh paired round, root-owned canonical/index/trailer/final-state checks and maintainer approval boundaries still apply. This addendum completes only this reviewer's initial pass and actual primary cross-read; it does not certify the other reviewer's later cross-read or any future round.

---

## Retained Round 2 security report

# Security review 2026-10-13 — T-052/T-053 standards reconciliation, Round 2

- **Change:** cumulative Step 8 on `development`, `98378b5add44755f7cbab6e8bc96337accf0574a..d553efe90ded0698f220a13b67fd9289864f85d0`.
- **Frozen source:** clean HEAD `d553efe90ded0698f220a13b67fd9289864f85d0`; 24 changed paths, all documentation/evidence. Three implementation commits: `cbd4cd15798e0580fe11efff8c4ce2f1a15a3bf3`, `7bde23e33254532af67924cfccf0be3d9d433720`, `d553efe90ded0698f220a13b67fd9289864f85d0`.
- **Reviewer:** Codex independent security agent `b22_step8_r2_security`, acting for @cemililik; not the author and not a maintainer approval.
- **Authority:** [approved execution plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md), [ADR-0042](../../../decisions/0042-descriptive-test-names.md), [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md), [T-052](../../tasks/phase-b2/T-052-standards-docs-reality-sync.md), [T-053](../../tasks/phase-b2/T-053-standards-docs-mechanical-fixes.md).
- **Separation from code review:** fresh security-only context with an empty checklist. Initial security and fresh code passes run in parallel under the explicitly approved paired-agent workflow. No prior Step 8 Round 1 report, peer Round 2 report or verdict was read before this independent initial checkpoint. This is not represented as a sequential cold pass or elapsed-hours self-review; actual peer cross-read is appended only after receipt.
- **Unsafe audit cross-reference:** no new/modified unsafe, assembly, Rust or audit entry. Existing [UNSAFE-2026-0033](../../../audits/unsafe-log.md#unsafe-2026-0033--tyrne-user-el0-syscall-svc-0-shims) and [T-038](../../tasks/phase-b2/T-038-console-write-x2-clobber.md) were inspected only to preserve the known unresolved x2 boundary.
- **Artifact:** temporary reviewer output; intended canonical destination `docs/analysis/reviews/security-reviews/2026-10-13-t052-t053-standards-reconciliation.md`. Relative links are qualified for that destination.

## Independent verdict and findings

**Approve the reviewed documentation delta. Zero new findings; zero delta blockers.** This does not approve the complete kernel security posture, authorize merging, promote tasks to Done, certify runtime tests or clear the known HIGH T-038 defect.

The most consequential improvement is that the standards no longer advertise general EL0 fault containment, automatic reclamation or an ISR-safe structured logger as implemented. Actual source supports the narrower descriptions. The CI, lint, target and supply-chain statements also distinguish required policy from delivered enforcement.

Both task files correctly remain **In Progress with unchecked criteria** at the frozen source. Their final In Review transition, canonical artifact/index/trailer integration and both-round recording are coordinator-owned follow-through after the paired reviews. These are expected pending boundary actions, not defects in the frozen review input. No `date_done` or maintainer completion is inferred. [Current focus](../../../roadmap/current.md) preserves HIGH T-038 Ready, the later correctness checkpoint, whole-B.2 C/D gates and the PR #49 publication barrier.

## Read scope and evidence provenance

**Full reads:** AGENTS.md and CLAUDE.md; all of current.md including dated historical records; all 42 filed numerical ADRs in ascending order 0001–0033 and 0035–0043 (0034 remains reserved); all 15 standards including README; all four skills [perform-security-review](../../../../.agents/skills/perform-security-review/SKILL.md), [conduct-review](../../../../.agents/skills/conduct-review/SKILL.md), [perform-code-review](../../../../.agents/skills/perform-code-review/SKILL.md), [propose-standard-change](../../../../.agents/skills/propose-standard-change/SKILL.md); both review master plans; complete T-052/T-053 task contracts, approved plan, Step 8 preflight/reconciliation and all six retained raw evidence files. Large-output truncations were recovered with bounded rereads, including ADRs 0003/0004/0008/0021/0022/0040, plan contract rows and evidence/diff portions. A truncated result was not accepted as a complete read.

The entire 24-path cumulative change was examined: existing documents through their diff plus full current content, and all newly added report/raw-evidence files in full. No path in the range was excluded as generated evidence. Full authoritative reads also covered root Cargo/config/lock/toolchain and all six member manifests, kernel/HAL crate roots, hello and tyrne-user sources, exceptions.rs, console.rs, both workflows, versioned main protection, run-qemu.sh, smoke.sh, security-model.md and T-038.

**Targeted authoritative reads:** BSP main.rs crate attributes and complete panic handler; vectors.s lower-AArch64 entry and complete synchronous dispatch/non-SVC panic path; scheduler task_exit_current/run_dispatched; BSP syscall Resume and Terminate paths; dispatcher production portion through validate_debug_console_cap; capability/CapObject Debug implementations; actual three IPC test declarations; audit-log header and UNSAFE-2026-0033 with amendments; Phase E supervision/lifecycle sections; repository-wide panic-family attribute/allowance search. These are not claimed as full BSP, scheduler, IPC, capability-table, user-access, allocator or audit-corpus re-audits. Existing unsafe contracts and syscall-input soundness are not newly certified.

The coordinator's [reconciliation](../../reports/2026-10-13-t052-t053-standards-reconciliation.md), [static snapshot](../../reports/2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t052-t053-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t052-t053-verification-evidence/initial-static-verification.json") and [navigation snapshot](../../reports/2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t052-t053-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t052-t053-verification-evidence/initial-navigation-verification.json") are implementation evidence, not independent review conclusions. Their working-tree/base metadata and intentionally pre-publication path inventory are correctly qualified. I independently reproduced the static facts below instead of treating those result files as proof by assertion.

## 1. Capability correctness

**Adversarial question:** could a reader be led to grant ambient authority or bypass an existing capability boundary because planned logging/fault mechanisms appear delivered?

**Assessment:** no changed capability API, transfer, duplication or revoke semantics. Logging's planned capability routing is now explicitly unavailable, while current diagnostics retain secret/context obligations. No new privilege-bearing operation is introduced. The [dispatcher](../../../../kernel/src/syscall/dispatch.rs#L130) continues to decode the release console gate before dispatch, validate console authority before range/page access and output, and bind self-yield/exit to current identity. This review does not reinterpret current trusted kernel mapping APIs as universally capability-safe.

- [x] Every privileged operation introduced by this change requires a capability. — **N/A** — no new privileged operation.
- [x] The capability required is the **narrowest** one that permits the operation (no privilege escalation by accepting a broad capability where a narrow one would do). — **N/A** — no new required capability or changed rights selection.
- [x] Capabilities are checked **before** observable side effects. A failed check does not leak information that the call was attempted. — **N/A** — no capability-check ordering changes; current console source was inspected as context.
- [x] Capability transfer (if any) is move-only; no accidental cloning. — **N/A** — no transfer implementation or contract changes.
- [x] Capability duplication (if intended) itself requires an explicit `Duplicate`-style authority. — **N/A** — no duplication implementation or contract changes.
- [x] Capability revocation (if applicable) takes effect atomically; no partial state where the revocation is half-applied. — **N/A** — no revocation implementation or atomicity claim changes.

## 2. Trust boundaries

**Adversarial question:** could a hostile EL0 fault be mistaken for recoverable typed syscall input, or could smoke success be mistaken for general fault containment?

**Assessment:** [error-handling §5/§8](../../../standards/error-handling.md#5-panic-is-an-assertion-not-error-handling) now separates the hello panic handler's voluntary `task_exit(101)` from arbitrary non-SVC EL0 faults. [vectors.s](../../../../bsp-qemu-virt/src/vectors.s#L195) routes non-SVC ECs to panic_entry; [exceptions.rs](../../../../bsp-qemu-virt/src/exceptions.rs#L308) supplies class/ESR fields to the fatal panic message. [testing](../../../standards/testing.md#3-qemu-boot--smoke-tests) correctly limits normal-image smoke to profile markers and fault rejection, not adversarial-image or general page-fault isolation proof. The unchanged [security model](../../../architecture/security-model.md#fault-containment) agrees.

- [x] Every input crossing from userspace to the kernel is validated before use. — **OK** — changed prose accurately limits current validation to the implemented syscall-input boundary; no validation code changes.
- [x] Pointers from userspace are **never** dereferenced in kernel mode without going through a validated mapping. — **N/A** — no pointer dereference or mapping change; no new guarantee of arbitrary fault recovery.
- [x] Buffer lengths provided by userspace are range-checked against the actual mapped region. — **N/A** — no buffer-length or range-check change.
- [x] Message contents from userspace are parsed into typed structures; no raw bytes are consumed in privileged code. — **N/A** — no message parser or payload contract change.
- [x] Cross-task IPC does not grant the receiver any authority the sender did not have or did not explicitly transfer. — **N/A** — no cross-task transfer or authority change.

## 3. Memory safety

**Adversarial question:** could the changed prose imply that exit frees stale capabilities or mappings, or that test/Clippy success proves every unsafe contract?

**Assessment:** [task_exit_current](../../../../kernel/src/sched/mod.rs#L951) overwrites current through dispatch and never re-enqueues the exiting task; it neither destroys the Task nor reclaims AS/table/frames. The standard states retention explicitly. No source/unsafe/audit bytes change. The known input-only x2 operand remains visible in [tyrne-user](../../../../userland/tyrne-user/src/lib.rs#L108) while [BSP Resume](../../../../bsp-qemu-virt/src/syscall.rs#L224) overwrites its saved slot. [T-038](../../tasks/phase-b2/T-038-console-write-x2-clobber.md) remains HIGH and Ready; neither host stubs nor existing smoke discharge that asm obligation.

- [x] Any new `unsafe` block meets [unsafe-policy.md](../../../standards/unsafe-policy.md). — **N/A** — no new unsafe block.
- [x] Invariants stated in `# Safety` sections hold for every call site, not only "the usual" one. — **N/A** — no Safety contract/call-site change; existing T-038 remains unresolved.
- [x] No uninitialized memory is exposed. Where a buffer is declared but only partially filled, the unused portion is zeroed or the buffer is returned as `MaybeUninit`. — **N/A** — no buffer initialization or memory exposure change.
- [x] No use-after-free. Lifetimes on raw pointers are reasoned about explicitly. — **OK** — changed exit prose correctly says resources are retained, not freed; no lifetime code changes.
- [x] No aliasing violations. Mutable pointers to the same memory do not coexist. — **N/A** — no aliasing or raw-pointer implementation change.

## 4. Kernel-mode discipline

**Adversarial question:** could a contributor rely on nonexistent nonblocking logging, recoverable allocation, panic register dumps, or universal lint enforcement?

**Assessment:** [PL011 write_bytes](../../../../bsp-qemu-virt/src/console.rs#L63) polls TXFF, so the revised ISR guidance correctly forbids assuming raw UART is a nonblocking logger. The current [panic handler](../../../../bsp-qemu-virt/src/main.rs#L1691) selects an address-regime UART alias, prints banner/PanicInfo and spins; there is no saved-frame dump/reset/backtrace/shell. Kernel/HAL/BSP crate roots actually deny panic/unwrap/expect; explicit boot/demo/fatal/test allowances remain, and test-hal/userland inherit workspace lints only. `todo` is workspace-denied, whereas intentional non-bare-metal `unimplemented!` stubs remain and no new deny is introduced. The standard's normal hot-path/error-propagation obligations remain intact.

- [x] No allocation in interrupt service routines. — **N/A** — no ISR allocation path added; no delivered ring is claimed.
- [x] No unbounded loops in kernel mode; every loop has a documented termination. — **N/A** — no loop changed; existing panic spin/UART polling are accurately described rather than certified bounded.
- [x] Critical sections are minimized. Scheduler state is held for as short a time as possible. — **N/A** — no critical-section or scheduler-state change.
- [x] No new kernel panic introduced on a hot path. — **OK** — no new panic path; existing whole-kernel non-SVC fault behavior is now explicit.

- **Master-plan additional item (33rd total, not a 33rd security-standard checkbox):** “Every allocation path returns a typed error, not a panic, on exhaustion.” — **N/A to new paths:** no allocation path changes. The standard does not invent universal recoverable exhaustion: trusted boot remains fail-stop and exit retains resources, consistent with [security-model bounded resources](../../../architecture/security-model.md#bounded-kernel-resources). This is not a fresh audit of existing allocators.

## 5. Cryptography

**Adversarial question:** does the change imply cryptographic authentication, secure boot, entropy or constant-time protections that do not exist?

**Assessment:** no primitive, key, nonce, random source, secure-boot mechanism or side-channel policy changes. SHA-256 values in evidence identify source bytes; they are not boot authentication or a proof of reproducible output.

- [x] No roll-your-own primitives. If a primitive is introduced, it is a well-known algorithm from a reviewed crate (or, if truly novel, it comes with a separate ADR and a cited proof or analysis). — **N/A** — no cryptographic primitive.
- [x] Keys are never logged, returned in error messages, or exposed via `Debug`. — **N/A** — no key or key-output path.
- [x] Constant-time comparisons are used where timing leaks matter. — **N/A** — no secret comparison or timing contract.
- [x] Randomness comes from an acceptable source — not `rand::thread_rng` with no seeding story. — **N/A** — no entropy/randomness source.
- [x] Nonces, IVs, and salts are handled correctly per the primitive's contract. — **N/A** — no nonce, IV or salt handling.

## 6. Secrets and logging

**Adversarial question:** could marking logging “Planned” silently suspend secret-redaction rules for current UART or advertise automatic redaction/rate limiting?

**Assessment:** the top banner and API transition paragraph explicitly preserve secret-redaction and context constraints for current diagnostics. Rings, worker, log service, metrics, controls, rate limiting and structured wire encoding are all planned; future encoding choices still need an ADR. [Capability/CapObject Debug](../../../../kernel/src/cap/mod.rs#L148) redact object identity, but retained rights and other diagnostic types are not falsely certified secret-free. The new text supplies policy rather than a blanket runtime redaction guarantee. No credential or secret is added to the evidence; ordinary repository paths, source hashes and already-public scope subjects are provenance.

- [x] Secrets (keys, tokens, capability bits) are not included in logs, panic messages, debug output, or error types. — **OK** — no secret added; current redaction obligations remain explicit without claiming automatic implementation-wide enforcement.
- [x] `Debug` impls on security-sensitive types redact sensitive fields (or are not implemented at all). — **N/A** — no Debug implementation changes; existing capability redaction inspected, no blanket certification.

## 7. Dependencies

**Adversarial question:** could green CI or a pinned lockfile be misrepresented as earned dependency trust or bit-for-bit reproducibility?

**Assessment:** all six lockfile packages are workspace packages; no external crate or executable dependency is added. Both workflow bodies lack cargo-audit/cargo-vet and cross-run binary comparison. The revised [security tooling](../../../standards/security-review.md#tooling), [code tooling](../../../standards/code-style.md#tooling), [P11 delivery note](../../../standards/architectural-principles.md#p11--reproducibility-from-the-toolchain-up) and [reproducibility status](../../../standards/infrastructure.md#reproducibility) correctly distinguish these absent gates from requirements. Original P11 Statement/Why/Applies and all reproducibility bullets remain unchanged. Existing dependency-addition/certification rules still apply when a dependency lands.

Versioned [main.json](../../../../.github/branch-protection/main.json) has six required contexts bound to app 15368, strict status checks, linear history and conversation resolution, with force/deletion disabled; approval count 0 and enforce_admins false are preserved. Code-review prose explicitly avoids claiming a mechanically required positive PR approval. Workflow source supports host, ARM, kernel/userland, debug/release and smoke descriptions. No live API read-back or new hosted execution was performed in this review; current live-state provenance remains the previously dated project record.

- [x] Any new dependency has been evaluated under [infrastructure.md](../../../standards/infrastructure.md) dependency-addition rules. — **N/A** — no dependency addition.
- [x] The dependency's trust model is understood. A build-time-only crate is very different from a kernel-linked crate. — **N/A** — no dependency/trust-model change; all six current packages are workspace packages.
- [x] `cargo-vet` trust decisions are updated accordingly. — **N/A** — no new trust decision; absent cargo-vet delivery is now stated accurately.

## 8. Threat-model impact

**Adversarial question:** do these corrections normalize unresolved security debt as solved, weaken an accepted rule, or advance the project past its safety gates?

**Assessment:** the delta corrects claims under approved task contracts, with naming as the sole selected rule change authorized by Accepted ADR-0042. The additional three standards files were justified before mutation in [preflight](../../reports/2026-10-13-t052-t053-standards-preflight.md#additional-file-scope-recorded-before-editing). Fault containment and resource lifecycle remain Phase E/E3 work; kernel-section permissions, DMA/SMP and full trap-state protection are not newly claimed. No ADR body/status changes, no new task/decision, no runtime/lint/CI change, no narrowing of the whole-B.2 exit bar and no external publication occur.

- [x] The change is reconciled with the documented threat model in [`docs/architecture/security-model.md`](../../../architecture/security-model.md). — **OK** — standards agree with the current security-model fault/lifecycle/diagnostic limits.
- [x] If the change reshapes the threat model, the PR includes the threat-model update or links to a follow-up PR scheduled imminently. — **OK** — no mechanism or threat-model expansion; source-backed claim corrections need no new threat-model follow-up.

## Architectural-principle coverage

| Principle | Outcome and reason |
|---|---|
| P1 no ambient authority | OK — no new authority or ambient logger API; capability routing remains a future design. |
| P2 minimal TCB | OK — prose/evidence only, no privileged code or dependency. |
| P3 userspace services | OK — log service/supervision remain future userspace responsibilities, not implemented kernel facilities. |
| P4 boundary checks | OK — described syscall input boundary is distinguished from non-SVC fault handling and trusted kernel APIs. |
| P5 Rust/unsafe discipline | OK — executable Rust/assembly and audit bytes unchanged; no fresh unsafe sign-off implied. |
| P6 HAL separation | OK — current Console/BSP UART path accurately attributed; no hardware details moved into kernel code. |
| P7 no proprietary blobs | OK — only text/JSON evidence added; no binary blob. |
| P8 ADR governance | OK — Accepted naming replacement precedes editing; factual corrections match approved contracts; no silent new design. |
| P9 English | OK — repository delta/report prose is English; historical escaped subject data remains provenance. |
| P10 Mermaid | OK — no new non-Mermaid diagram; standards' existing conceptual examples retain tagged fences. |
| P11 reproducibility | OK — requirements preserved byte-for-byte in the relevant original paragraphs/bullets, absent delivered certification stated. |
| P12 scoped completeness | OK — no implementation stub introduced; planned services and intentional host-compilation stubs are explicitly bounded; tasks not prematurely complete. |

## Every task acceptance criterion and definition of done

“Verified” below means the content requirement is satisfied at the frozen source. “Pending boundary” means the expected coordinator recording/state action after both rounds; it is not a human approval or completed DoD checkbox.

| T-052 item | Assessment and evidence |
|---|---|
| AC1 naming/ADR/examples/References/no lint | Verified — [testing naming](../../../standards/testing.md#test-naming), References, Accepted 0042/Superseded 0041, three actual `#[test]` declarations at IPC 919/941/969; no source rename. |
| AC2 panic facts/no dump follow-up | Verified — [error-handling §5](../../../standards/error-handling.md#5-panic-is-an-assertion-not-error-handling), complete BSP handler and exception messages; approved omission of automatic new task retained. |
| AC3 todo/unimplemented/host stubs | Verified — [§10](../../../standards/error-handling.md#10-todo-and-unimplemented-are-transient-markers), full Cargo/member manifests and user library; required target-aware Clippy workflow inspected. |
| AC4 logging banner/facade/current path | Verified — [logging](../../../standards/logging-and-observability.md), complete workspace membership, Console implementation. |
| AC5 exact deny scope/allowances | Verified — [code-style lints](../../../standards/code-style.md#lints), crate roots and allowance search; no uniform userland deny claim. |
| AC6 downstream effects | Verified — [retained 73-hit post-edit search](../../reports/2026-10-16-pr49-evidence-catalog.md#dataset-2026-10-13-t052-t053-verification-evidence "Archived member: docs/analysis/reports/2026-10-13-t052-t053-verification-evidence/downstream-after-content.txt") reproduced byte-for-byte; [dispositions](../../reports/2026-10-13-t052-t053-standards-reconciliation.md#downstream-effects-search-dispositions) distinguish policy/history from false delivery claims. |
| AC7 adjacent task faults/supervision/reclamation | Verified — [§8](../../../standards/error-handling.md#8-userspace-task-faults-are-kernel-visible-errors), vector/exit/hello source and Phase E ownership agree. |
| DoD1 touched links/heading targets | Verified within recorded bounded diagnostic — 18 touched Markdown files, 463 local destinations and 44 fragments, zero candidates; no claim of complete future T-056 grammar. |
| DoD2 diff scope plus allowance | Verified — all 24 paths are named content, recorded downstream corrections or explicit evidence/task/current/track allowance; no executable/config/CI/ADR delta. |
| DoD3 English/tagged fences | Verified — complete content read; all 15 standards have 20 tagged openings, zero untagged/unclosed. |
| DoD4 commit messages/Refs | Verified — all three commits use `docs(standards)` and actual ADR-0040/0042/0043 trailers. |
| DoD5 In Review/current | Pending boundary — both tasks intentionally IP and unchecked until both fresh paired rounds finish; current/index match. |

| T-053 item | Assessment and evidence |
|---|---|
| AC1 target panic flags/userland/host unwind | Verified — [panic strategy](../../../standards/error-handling.md#panic-strategy), full `.cargo/config.toml` and root release comment; no profile panic key. |
| AC2 live CI/coverage/protection | Verified — [code-review tooling](../../../standards/code-review.md#tooling), complete workflows/protection; informational coverage and solo approval/admin limits explicit. |
| AC3 scope vocabulary/history/extension | Verified — [commit scope section](../../../standards/commit-style.md#subject-line), independently reproduced 470 baseline subjects and 75 captured scope strings; historical aliases and prior-use OR review-agreement rule retained. |
| AC4 every workspace lint/authority | Verified — all nine root lint entries represented with levels in [code-style](../../../standards/code-style.md#lints); all six members opt in. |
| AC5 printed QEMU path | Verified — [BSP checklist](../../../standards/bsp-boot-checklist.md#enabling-qemu-exception-logging), full runner uses `${TMPDIR:-/tmp}/qemu_int.$$.log` and prints it. Smoke has separate evidence path/flags. |
| AC6 three tags/all standards fence check | Verified — stateful delimiter-aware scan counts 20 tagged openings across 15 files; commit's two examples and naming fence use `text`. |
| AC7 existing test-hal wording | Verified — [fixtures](../../../standards/testing.md#fixtures-and-doubles) names existing crate; manifest present. |
| AC8 release grammar | Verified — [release versioning](../../../standards/release.md#versioning) now says “a Tyrne-specific”. |
| AC9 adjacent tooling/lint levels/scope rule | Verified — missing_docs warning escalation and review-only internal coverage, planned audit/vet, live normal-image smoke; original configuration unchanged. |
| DoD1 touched links | Verified within bounded diagnostic above; root's larger diagnostic is separately attributed. |
| DoD2 limited diff plus evidence allowance | Verified — same 24-path review and pre-recorded existing-scope additions. |
| DoD3 standards commit messages | Verified — all three commits match required scope and conventional English subjects. |
| DoD4 In Review/current | Pending boundary — root completes only after both paired rounds; no Done/date_done authorization. |

## Commands, independent results and limits

Read commands were `cat`, bounded `sed -n`, `wc -l`, `rg --files`, and `rg -n`/context searches. Full-file and targeted boundaries are listed above rather than overstating search hits as full source audits. Scope/provenance commands actually run include:

```sh
git status --short
git branch --show-current
git rev-parse HEAD
git diff --stat 98378b5add44755f7cbab6e8bc96337accf0574a..d553efe90ded0698f220a13b67fd9289864f85d0
git diff --name-only 98378b5..d553efe
git diff --check 98378b5..d553efe
git diff 98378b5..d553efe -- docs/standards
git diff 98378b5..d553efe -- docs/analysis/tasks/phase-b2 docs/roadmap/current.md docs/analysis/reports/2026-10-12-phase-b2-track2-preflight-and-plan.md
git diff --unified=0 98378b5..d553efe -- docs/analysis/reports/2026-10-12-phase-b2-track2-preflight-and-plan.md docs/analysis/tasks/phase-b2/README.md
git log --format=fuller 98378b5..d553efe
```

Two inline `python3 - <<'PY'` read-only verification programs were actually executed, using only standard-library modules and Git subprocess reads. The first independently checked the full 24-path list, all 15 retained source SHA-256 values against baseline and working tree, exact git-log subject/scope extraction, exact post-edit rg argv/result reproduction, zero baseline-domain diff between `23391c7` and `98378b5`, all standards' stateful matching-delimiter fences, all 46 B.2 task states and unchecked T-052/T-053 criteria. It counted exactly 32 literal security-standard checkboxes. The second checked rendered inline/reference local destinations and heading fragments in all 18 touched Markdown documents with a bounded parser; no candidates. These scratch checks are not installed/shipped T-056 tooling.

Independent results: clean `development` at the frozen SHA; 24 documentation/evidence paths; 15 unchanged source/config digests; 470 actual baseline subjects/75 scope strings; exact 73-line post-edit search reproduction; 15 standards/20 tagged openings; task counts 8 Done, 21 Ready, 7 In Review, 2 In Progress, 8 Draft; clean step `git diff --check`; 463 local destinations/44 fragments without candidates. The broader 141-line pre-edit search is not a defect count; all its hits and dispositions were read. A separate narrower `rg` vocabulary check produced 45 hit lines, not a claim to reproduce the broader expression.

No Cargo, Clippy, Miri, QEMU, coverage, Linux-hosted, external-link, live protection API, binary-comparison or package-install command ran in this review. No repo write, branch switch, push, publication or external message occurred. Runtime re-execution is unnecessary for this prose-only delta and would not turn the reviewed claims into a universal safety proof. The link check deliberately claims only the touched corpus/forms inspected; external URLs were not fetched, and neither it nor the coordinator diagnostic substitutes for ADR-0043's future full grammar/fixture gate.

## Rejected false positives and retained boundaries

- **Logging banner weakens secret policy:** rejected; it explicitly keeps current secret/context obligations and marks only undelivered mechanisms planned.
- **No register dump requires opening a feature task:** rejected; the maintainer-approved T-052 contract expressly removed that obligation. No feature is selected by correcting a false claim.
- **Host `unimplemented!` stubs contradict new completeness wording:** rejected; the new standard explicitly distinguishes intentional non-bare-metal compilation stubs, consistent with unchanged cfg and manifest/CI targets.
- **Known x2 defect makes this documentation change a new exploit or unsafe approval:** rejected; T-038 is an unchanged, source-confirmed HIGH backlog item, not fixed, hidden or newly introduced by Step 8.
- **P11/reproducibility note relaxes mandatory requirements:** rejected; the original requirement text is preserved and the note explicitly denies certification, not the obligation.
- **Protection's zero approval count is an unauthorized weakening:** rejected; code-review wording accurately describes the unchanged versioned policy and retains cold-review obligations.
- **IP/unchecked tasks or snapshot path omissions are premature completion:** rejected; both are explicitly pre-review snapshots with final review/state integration pending.
- **Generic standards examples describe current APIs:** the modified logging examples explicitly say conceptual; unrelated pre-existing general design examples are not promoted to implementation claims or expanded into this step's scope.

## Integration responsibility

The root coordinator owns canonical placement/indexing, cross-linking this report to the paired code review, the applicable `Security-Review:` trailer, the final two-round record and task In Review transition. This temporary independent report makes no claim those writes already occurred. The [security master plan](master-plan.md) and [code master plan](../code-reviews/master-plan.md) remain the artifact contracts; this is an independent security review, not a milestone closure trio or approval-promotion review.

**Independent initial checkpoint recorded (UTC):** 2026-10-13 02:39:36 UTC.

## Post-checkpoint Round 1 continuity

After my independent initial checkpoint (SHA-256 `8d0e605d94ad7267cc369d210eb744b15270a4417e3044307c80b16d69145c44`, 211 lines / 31,402 bytes), the coordinator supplied the actual completed Round 1 code and security artifacts. I fully read `/tmp/tyrne-b22-step8-r1-code.md` (185 lines / 30,648 bytes, SHA-256 `1ac88318d1fb9d77d411669d57d62c810e6b0c04391299829c3b28562281c5d9`) and `/tmp/tyrne-b22-step8-r1-security.md` (242 lines / 33,160 bytes, SHA-256 `df1e3aaf009bcd64a263125add8fceb7e5fb2edd918bffe7c0acc19083bb5dce`) in bounded reads. Their final verdicts Approve the same cumulative frozen source, with zero confirmed source findings and no source correction to verify. This is attributed continuity under conduct-review, not input to my independent verdict.

The earlier reports disclose their own chronology: the first security reviewer received an interim primary status/count relay before its checkpoint, actual artifact exchange happened later, and a report-only S28 infrastructure destination was corrected after initial recording. The code review's navigation helper also initially miscomputed underscore anchors before direct source inspection corrected it. Those are disclosed earlier-review process/report facts, not newly discovered Step 8 defects. Their substantive conclusions match my independent checks; their larger or narrower navigation counts have explicitly different domains and are not runtime or complete-grammar proof. No earlier reviewer result is relabeled as a fresh run by this reviewer.

The coordinator also informed me, after my checkpoint, that the original Round 2 code context had encountered an unexecuted publication template and is supplementary only; a new fresh primary code context `b22_step8_r2_code_fresh` is completing the required paired review. I have not opened that template or supplementary report. The actual fresh primary report remains pending; only its actual delivered artifact will be cross-read. The independent initial security verdict above is preserved.

## Actual fresh Round 2 paired cross-read and final verdict

After both independent initial checkpoints, I fully read the actual fresh primary artifact `/tmp/tyrne-b22-step8-r2-code-fresh.md`, initial 130 lines, SHA-256 `c927cc5266e34fa73f817a6311042ae8e388779036483b895732ce803f077e08`. The delivered initial content is the cross-read evidence; subsequent primary addenda are not presumed read or incorporated. Its five code-review roles independently Approve with zero confirmed findings. Its initial overall Comment is explicitly procedural: the actual separate security report and later cross-read were pending. It identifies no source blocker or requested source correction.

I compared its concrete source and task conclusions with this security report: actual whole-kernel non-SVC panic, voluntary hello exit 101, retained Task/AS/capability/frame resources, raw polling UART, current secret/context obligations despite planned logging mechanisms, all nine inherited workspace lints versus narrower crate denies, target-specific panic configuration, unchanged versioned CI/protection, and preserved P11/dependency-audit requirements all agree. Its task AC/DoD mapping preserves the pending In Review transition; its principle and state checks retain T-038 Ready, the HIGH-correctness checkpoint, whole B.2 C/D gates and PR49 publication barrier. None supplies grounds to change the independently reached security verdict.

The primary's independently reported navigation domain is 368 Markdown files / 6,140 local targets / 626 fragments; mine is the 18 touched Markdown documents / 463 destinations / 44 fragments. These are different scoped checks, both with zero candidates, not interchangeable coverage claims. The primary explicitly qualifies its copied existing diagnostic and performs no new runtime or reproducibility certification. No source fix occurred between rounds; there is consequently no source-fix verification to claim. The coordinator's later report-QA request to reproduce complete literal code-checklist prompts is an append-only artifact-completeness correction, not a source finding or a new independent round; I do not claim to have read that later addendum here.

**Final security verdict: Approve the cumulative documentation change; zero confirmed new security findings, zero security blockers.** The initial security judgment is unchanged after actual peer cross-read and attributed Round 1 continuity. The two reviewers worked independently in parallel before exchanging actual reports; this is not a pretended sequential second pass. This approval is limited to the frozen Step 8 delta and does not close T-038, promote any task to Done, supply human approval, waive whole-track exit gates or authorize publication past the PR49 barrier.

Final artifact QA checks the 32 literal standard checkbox entries (the separately assessed master-plan allocation item makes 33 total review items), qualifies rendered relative links from the intended canonical security-review destination, and rechecks the frozen clean source. Canonical placement, final peer addenda retention, review references/indexes and the authorized In Review transition remain the coordinator's work.

> **Evidence migration (2026-10-16).** Raw evidence links now open the [immutable archive catalog](../../reports/2026-10-16-pr49-evidence-catalog.md). Each link title retains its exact archived member path. Original verdicts, measurements, limitations and execution SHA identities remain historical; the archive bundle restores their original source.
