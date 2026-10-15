# Code review 2026-10-13 — T-050 entry-document refresh

- **Change:** development, cumulative 75de2ba90e151bae33e14d2db4a8278837e7775d..946f45f34f7eac90164adccfcd71e4c7f77c1f8e; implementation 74f8e837bd13e10b71f517446ae0d108c5215e42, two corrections recorded below.
- **Reviewer:** four independent Codex contexts listed below; coordinator Codex preserves their actual reports. No human review attributed.
- **Date:** 2026-10-13.
- **Risk class:** Security-sensitive descriptions of capabilities, boot, syscall/EL0, memory and scheduler behavior; documentation-only implementation delta.
- **Security-review cross-reference:** [paired two-round security artifact](../security-reviews/2026-10-13-t050-entry-document-refresh.md).
- **Task / evidence:** [T-050](../../tasks/phase-b2/T-050-entry-docs-and-glossary-sync.md), [source-bound verification](../../reports/2026-10-13-t050-entry-document-verification.md), [raw captures](../../reports/2026-10-13-t050-entry-document-evidence/README.md).

## Correctness

Both primary five-role reports below verify current-versus-target behavior against source. C01 and R2-C01 were confirmed, fixed in separate commits and independently verified. No unresolved correctness finding remains.

## Style

English prose, complete guide structures, stable glossary anchors and exact approved copyright were checked. LICENSE changes only its appendix copyright line; all other bytes are preserved.

## Test coverage

Six fresh matching-profile commands executed clean tracked source 75de2ba, not the later documentation tip; raw metadata/hashes and limits remain retained. Reviewers independently checked the captures and source. Bounded navigation diagnostics and correction checks are attributed in the reports; no new runtime test, hosted CI, general Markdown parser or benchmark certification is claimed.

## Documentation

README, guide inventory/two guides, glossary, BSP/task skills and phase path entry points were reviewed as complete owned surfaces. R1 raw-pointer obligations and R2 bridge gate are now explicit. Historical/executed snapshots remain distinguished from later states.

## Integration

Both fresh primary reports include all five roles, the full code checklist and P1–P12; actual paired security results were read before final primary approvals. No dependency, source/build/CI change or new ADR. Publication adds canonical records/index rows and sets T-050 In Review, without date_done.

## Verdict

**Approve** — both fresh rounds approve the corrected cumulative delta at 946f45f; two confirmed code-origin Low findings resolved, zero open findings. Maintainer review remains pending.

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

## Retained Round 1 primary report

# Code review 2026-10-13 — Track B.2-2 Step 6 / T-050, fresh Round 1

- **Change:** `development`, implementation `75de2ba90e151bae33e14d2db4a8278837e7775d..74f8e837bd13e10b71f517446ae0d108c5215e42`; preceding canonical boundary `054e13e2a368bb6699657ebc5b58e4daf98a23f1`.
- **Reviewed HEAD:** clean `74f8e837bd13e10b71f517446ae0d108c5215e42`, verified at entry and after independent checks.
- **Reviewer:** Codex AI agent `/root/b22_t050_r1_code`, fresh independent primary context; not @cemililik and not maintainer approval.
- **Configuration:** Coordinator-supplied GPT-6.1 Sol / high effort / fresh fork with no inherited turns; paired security reviewer GPT-6 Astra / high effort / fresh fork with no inherited turns. This records coordinator configuration, not runtime self-introspection.
- **Date:** 2026-10-13.
- **Risk class:** Security-sensitive documentation: capability, syscall, memory, scheduler and boot descriptions/procedure. No executable change.
- **Security-review cross-reference:** Separate fresh context `/root/b22_t050_r1_security`, actual report `/tmp/tyrne-b22-t050-r1-security.md` read in full after the independent primary assessment. Initial security Approve / zero independently originated findings; later attributed shared-C01 confirmation. See reconciliation below. Parallel independent passes, not sequential review by this agent.
- **Output authority:** Read-only repository access; this temporary report is the only file written. The coordinator owns canonical review/index integration, corrections and commits. No branch, Git state, source/document/CI file or external service mutated.

## Correctness

**One confirmed Low finding, C01.**

### C01 — A raw capability-table binding is described as a handle

- **Severity:** Low; factual documentation correction required for this task's precise source-backed guide contract. No runtime defect is alleged.
- **Location:** `docs/guides/first-userspace.md:115`: “Enqueues it through `add_user_task`, binding address-space/table handles, the image/stack window and a per-task kernel `SP_EL1` stack.”
- **Source evidence:** `kernel/src/sched/mod.rs:444–452` takes `address_space_handle: AddressSpaceHandle` but `cap_table: *mut CapabilityTable`. The storage at `kernel/src/sched/mod.rs:290` is `Option<*mut CapabilityTable>`, not a capability-table handle. The explicit safety contract at `:428–434` requires that pointer to outlive the task and forbids a live mutable borrow across a context switch. `bsp-qemu-virt/src/syscall.rs:182–186` materializes `&mut *table_ptr` from the running task's binding; the AS is separately resolved through its generation-tagged arena handle.
- **Impact:** The combined “address-space/table handles” wording erases the important distinction between a checked object handle and an externally lifetime-managed raw pointer. A reader following the boot wire-up can infer a typed/generation-checked capability-table binding that the current scheduler does not provide.
- **Remedy:** Name the address-space handle and raw capability-table pointer/binding separately, and retain the pointer's task-lifetime/no-live-mutable-borrow-across-switch obligation. No API or lifecycle implementation change is needed.
- **Disposition at frozen HEAD:** Open. Root independently confirmed the finding and plans a correction after both R1 reports. This report does not pre-approve that unwritten correction.

Other checked correctness areas are clean:

- README separates target userspace drivers/services/init from the present privileged BSP and sole EL0 hello. Six workspace members and three default host members match `Cargo.toml`. Current MMU status matches temporary low bootstrap, kernel TTBR1 and per-task TTBR0; address-space operations are kernel APIs rather than v1 syscalls.
- The current syscall decoder recognizes four release calls and debug-only number 5. Yield/exit use complete current-task context rather than an object capability. Debug console validates the calling table's kind/right before output and copies through range/per-page translation; `copy_to_user` has no dispatcher caller. Per-table revocation and deferred cross-table transitivity are accurately qualified.
- The raw traces and source agree on B waiting → A sending → user console/exit → B receiving/replying → A receiving/completing. Scheduler FIFO, delivery/unblocking, send's conditional yield and B's explicit post-reply yield corroborate that ordering. B's tail and idle never resume; Task A spins without yielding after completion.
- The returning console SVC and non-returning exit are correctly separated. `task_exit_current` is an unsafe module-level free function, abandons its caller frame and leaves task/AS/table resources and terminal-state work unresolved. Exit status is ignored. No source claim is made that the exit SVC ERETs to the exiting user task.
- AP data access, UXN EL0 execution and PXN privileged execution are correctly distinguished. Descriptor constants/encoder and bootstrap flags corroborate high-half RAM AP00/UXN1/PXN0, device AP00/XN both1, user image AP11/UXN0/PXN1 and writable stack AP01/XN both1. Broad privileged executable RAM, deferred section W^X and non-SVC EL0 panic remain explicit limits.
- The BSP template's first instruction is `msr daifset, #0xf`; it is explicitly an already-EL1 stack/FP/BSS skeleton. EL2 entry requires the target's Accepted boot policy, and the text rejects a bare HCR/ERET insertion. Minimal declared-workload completion is distinguished from full reference EL0/IPC smoke.
- Phase paths use `phase-<id>`, lowercase dot-free B.2 → `phase-b2` / `phase-b2.md`; bridge Tracks are distinguished from B0–B6 milestones. No new phase or policy is introduced.

## Style

No confirmed style finding.

- Both rewritten guides use an imperative title, summary, Goal, Prerequisites, numbered imperative Steps, Verifying it worked, Troubleshooting and References, following the full `write-guide` skill.
- Commands use `sh`; output uses `text`; the Rust excerpt is explicitly partial and source-identical in the shown entry body. The existing README diagram is Mermaid and now explicitly target design. Repository tree text is an inventory, not a new architectural diagram.
- Glossary remains a flat bold-headword list. Anchors are invisible inline HTML immediately before each headword, not heading conversions. The four additions have self-contained definitions and decision/source links. Inward related-term links are present; an outward glossary-consumer sweep is explicitly excluded by the task contract.
- No formatter/linter churn, new Rust item, unsafe annotation, dependency, normative standard edit or ADR body edit occurs. The existing guide index's more general CI-description guide is not being retroactively forced into a procedural template.
- `git diff --check 75de2ba..74f8e83` passes. English committed prose and tagged fences were inspected. No preference-only comments are raised.

## Test coverage

No missing behavioral test is introduced by this documentation-only implementation. No new syscall/error/API/unsafe behavior exists to justify fresh unit, regression, Miri or kernel test additions.

I read retained verification inputs before assessing changed implementation prose: `metadata.json`, `verification.json`, `glossary.json` and all 14 stdout/stderr/raw-QEMU logs, including intentional empty stdout files. Subsequently I compared the report claims against those raw inputs and actual source; preparation/report statements were not accepted as review verdicts.

Independently executed read-only diagnostics establish:

| Check | Independent result |
|---|---|
| Tracked `git archive 75de2ba…` digest | Recomputed `68500b9e7a5f05d48b668ca6bd8e1c28ed8e7f5625e6ee4d2fbf5f10a56ebe28`, exact metadata match. |
| All retained stream/raw capture identities | All 14 byte counts and SHA-256 digests match metadata. |
| Runtime command metadata | Six sequential argv/cwd/UTC/exit records; all exits 0. Manual matching userland/kernel builds precede each matching smoke, which repeats its own normal build. |
| Debug raw trace | Two total Taking-exception records, both SVC from EL0 to EL1; one greeting, one exit, one completion; source-consistent order. |
| Release raw trace | Two total Taking-exception records, both SVC from EL0 to EL1; no greeting, one exit, one completion; source-consistent order. |
| Smoke gate | Actual script enforces profile markers and named fault patterns; it does not count SVCs, certify arbitrary hostile EL0 behavior or test timer/idle/preemption. |
| Navigation | 292 rendered plain-inline local targets and 18 fragments in all 13 touched Markdown files resolve. Fenced/code-span data excluded. |
| Guide structures/inventory | All required sections in both rewritten task guides; exactly four substantive guide files match the available table, README excluded. |
| Glossary inventory | Baseline50 → final54 exact headwords; only four approved additions; exactly27 existing definition texts changed, exact manifest match. |
| Glossary anchors/order | Exactly54 unique immediate anchors; full map and full-displayed-headword scheme match the ledger; primary-headword order passes with the approved MMU/mmu_bootstrap/.boot_pt grouping. |
| LICENSE / NOTICE | Same line counts/newlines; LICENSE byte lines differ only at189, NOTICE only at2; exact approved holder including spelling/capitalization/indentation. |
| Lifecycle/index | B.2 has24 Ready,8 historical Done,8 Draft,5 In Review,1 In Progress. T-050/current/task index/plan agree on In Progress and reviews pending; acceptance boxes remain unchecked. |
| Executable/scope preservation | All32 changed files are scoped Markdown/license/notice/evidence. No Rust/assembly/shell/Python/Cargo/lock/toolchain/workflow/branch-protection delta. Final tree clean/frozen. |

Limits: I did not witness the retained command executions, recreate the first-install environment, rerun QEMU/Miri/coverage, automate interactive mon:stdio/Ctrl-A behavior or fetch hosted CI. Archive initial-artifact absence and historical process-exit/tool/ELF identities are retained coordinator provenance, not newly witnessed facts. The recreated source digest and raw log identities support source/evidence consistency; compiled ELFs and the original disposable export are not retained in this evidence directory. Source/retained trace inspection was sufficient for the documentation change and revealed no runtime gap requiring a rerun. Single elapsed values are explicitly anecdotes, not a performance benchmark.

My first general diagnostics deliberately surfaced two false-positive classes and were corrected: sorting full parenthetical expansions instead of primary headwords, and treating the task's backticked `](…)` syntax example as a rendered link. Neither is a repository finding. The final independent navigation scan reports292 targets/18 fragments/zero errors, matching the coordinator snapshot. The scan is bounded plain-inline checking of the actual touched forms, not a general Markdown grammar implementation or the future T-056 gate. I did not read or run `/tmp/tyrne-b22-t050-check.py`.

## Documentation

**Low C01 is the only confirmed documentation gap.** All other literal T-050 acceptance content is implemented at the frozen HEAD; process closure awaits correction, both fresh rounds and maintainer review.

| T-050 contract | Assessment |
|---|---|
| Guide index framing/inventory/status | Four available guides; planned ideas separated; no numeric-phase placeholder status. Existing accepted guides' PR48 refresh is supported by local merge history/task records; new guide refreshes remain pending review. |
| README first-userspace discovery | Present in guide map and workspace tree. |
| README trace/unsafe coverage | Nonexistent image-loaded banner removed; real serial ordering/values elided; illustrative unsafe list includes user copies/audit0030 and unused runtime write-side limitation. |
| Four new glossary terms | Exact AddressSpace, Bridge phase, PMM (Physical Memory Manager), Track additions with relevant ADRs; source semantics checked. |
| Ordering versus corrections | Requested M and Rendezvous/Reply moves separately recorded; existing text not frozen; exact27 correction ledger matches baseline diff. |
| Anchors | All54 immediate unique stable IDs, full displayed headword → lowercase ASCII alphanumeric words/hyphens; task kickoff/history and glossary manifest record the scheme. No changed displayed vocabulary beyond four additions. |
| Phase-path entry points | All three owned surfaces generalized and B.2 mapping/Track distinction documented. |
| BSP trace/boot/diagnostic correction | DAIF-first already-EL1 template, Accepted complete EL2 policy reference, minimal completion versus reference EL0 gates, README link/version caveat and printed PID-scoped log path. |
| Approved copyright | Exact common identity recorded at kickoff before edit; NOTICE2/LICENSE189 only. No other license text or author metadata changed. |
| Clean checkout/profile commands | Explicit userland-before-BSP in README and both guides; debug/release matching/rebuild caution; real six-command clean tracked-export evidence distinguishes tool cache reuse. |
| EL0 exit/permissions/fault limits | Correct free function/no ERET/no reclamation/ignored status, actual AP/UXN/PXN and non-SVC panic. C01 corrects the remaining table-pointer wording in this same wire-up paragraph. |
| Existing glossary factual scope | Rights include CONSOLE_WRITE; badges/reply design deferred; staged transfer/per-table CDT; implemented virtual timer deadlines/GIC without demo IRQ/preemption evidence; actual MMU/six frames/shareability; dynamic Miri limits; no “Tree Borrows stricter successor” claim. |
| Literal DoD and step evidence allowance |32-file implementation range falls within named content and source-bound evidence/task history allowance. Unchanged current/index remain correctly In Progress because no review completion claimed. DoD In Review/boxes must be finalized only after both rounds. |

The complete preflight preparation note was read only after the source/diff/evidence assessment. Its initial bounded ledger, later full-prerequisite completion and later source-boundary notes are explicitly historical and not either implementation round. The verification report separately labels executed clean75de source and subsequent documentation working tree, including static diagnostic limits. It preserves original security verdicts and exposes ongoing limits instead of fabricating retrospective approval. No previous implementation review of this exact scope exists; none was reused.

## Integration

No confirmed integration finding beyond the source/prose distinction C01.

- The implementation is one cohesive T-050 documentation refresh plus inspectable evidence, despite exceeding the ordinary400-line target. Breaking source-bound traces/glossary accounting from the corrections would obscure its acceptance evidence. No executable or CI path is changed.
- `docs(guides): refresh T-050 entry documents` is English, imperative, conventional and uses a scope with prior repository use; actual `Refs: ADR-0040, ADR-0043` exist and govern the change. No new unsafe is introduced requiring an introduction Audit trailer.
- Existing `two-task-demo.md#execution-trace` remains; touched targets/fragments resolve. The first-userspace guide and README cross-link; phase paths preserve old IDs and bridge structure. No downstream code caller changes.
- Build scripts, Cargo aliases, target flags and workspace membership were checked directly. `build.rs` requires hello.bin and watches it; both userland profiles overwrite that ignored path. Smoke builds in order; plain shell runner does not build; Cargo run may build the BSP but does not orchestrate userland. The guides correctly state matching-profile prerequisites.
- T-050 state is correctly In Progress on the frozen pending-review snapshot; no new task was promoted Done and no maintainer/hosted/main merge claim was introduced. ADR-0043's reviewed stacked sequence and later C/D gate remain intact. No source-policy change or new ADR is required by these factual corrections.
- Distinct independent security approval is still required. This primary report will quote the actual paired final outcome, without replacing it or claiming that this agent performed the second pass.

### Full code-review standard checklist

| Required consideration | Result |
|---|---|
| Correctness | Low C01; all other checked source/document/evidence contracts agree. |
| Capability semantics | Current-task control plane versus capability-gated object plane, eight rights, local revocation, staged transfer and caller-table binding checked. C01 preserves the raw-pointer distinction. |
| Fault containment | Existing non-SVC EL0 panic and unreclaimed exit resources are explicit; no new containment implementation promised. |
| Unsafe discipline | No unsafe delta; illustrative README includes audit0030; raw-pointer guide/DAIF template inspected. Not a new audit of every unchanged unsafe region. |
| Error handling | No changed Result/error code; BadSyscallNumber debug gating, typed syscall result and non-returning exit accurately described. |
| Tests | Retained fresh debug/release raw evidence/metadata and meaningful independent static checks; no new behavioral tests needed for doc-only scope; limits explicit. |
| Documentation | Full guide/glossary skills applied; C01 is the only factual gap. No new Rust public item/unsafe fn/errors needing rustdoc. |
| Architectural principles | All P1–P12 explicitly assessed below. |
| Dependencies | No added/upgraded crate/tool/action; no dependency-addition procedure triggered. |
| Naming/style | English, meaningful titles, flat alphabetical glossary, tagged code/output, Mermaid target diagram; no tool-style bikeshedding. |
| Commit message | Conventional docs(guides), prior-use scope, genuine ADR0040/0043 references; source-only review does not claim hosted merge state. |
| Author preparation/run | Task/plan intent and verification inputs read first; source-bound fresh retained builds inspected; no independent behavioral rerun needed. |
| Post-fix sweep | Old owned-file image-loaded, stale order/fixed log path/phase-letter vocabulary replaced; historical opening observations remain deliberate quoted history. C01 correction/sweep remains to be executed and verified. |
| Security gate | Required; separate fresh parallel reviewer assigned, actual delivered outcome to be appended. |

### Architectural principles P1–P12

| Principle | Assessment |
|---|---|
| P1 — No ambient authority | Pass for change: object operations/current-task control-plane distinction and target authority model accurately qualified; no authority introduced. |
| P2 — Small TCB | Pass: privileged BSP versus planned userspace components distinguished, no TCB code expansion. |
| P3 — Userspace drivers/services | Pass for documentation: target design clearly separated from current BSP drivers; no false shipped-isolation promise. |
| P4 — Boundary capability checks | Pass for change: caller table/console kind+right/user translation documented; C01 must distinguish the actual raw table binding. |
| P5 — Rust/audited unsafe | Pass: no executable/unsafe delta; Rust entry excerpt and audit references accurate; no new unsound wrapper. |
| P6 — HAL separation | Pass: actual HAL/BSP split, MMU/Timer/IRQ interfaces reflected; no hardware access added to portable kernel. |
| P7 — No proprietary blobs | Pass: only textual logs/metadata/docs/license change; no binary shipped or new blob dependency. |
| P8 — ADR-first | Pass: approved0040/0043 task scope; source corrections choose no new architectural/EL2/lifecycle/parser policy and preserve ADR bodies. |
| P9 — English | Pass: repository changes English; exact maintainer-approved copyright spelling preserved. |
| P10 — Mermaid | Pass: target diagram remains Mermaid with introductory scope explanation; textual file inventory is not an architectural illustration. |
| P11 — Reproducibility | Pass for change: no pin/dependency/build flag changes; tracked-source archive/log/profile identity checked; cache/first-install/ELF witnessing limits explicit. |
| P12 — Complete declared scope on main | Pending document correction/review only: T-050 remains In Progress, no main merge/Done claimed; both rounds and maintainer authority retained. No subsystem stub added. |

## Verdict

**Request changes** on frozen `74f8e837bd13e10b71f517446ae0d108c5215e42`.

Blocker for a clean T-050 Round1 pass: correct **Low C01**, the capability-table handle/raw-pointer misdescription at `docs/guides/first-userspace.md:115`, then independently verify the precise correction. No other verified finding, dispute or runtime gap was found. Fresh Round2 must review the corrected cumulative step; it cannot reuse this context or preparation. Distinct security review and final maintainer review remain separate requirements. No task promotion/merge approval is conferred by this AI review.

## Actual read ledger and scope limits

Prerequisites were completed literally before task/diff/source assessment, not inherited as proof:

- AGENTS.md23 lines, full CLAUDE.md60, full `docs/roadmap/current.md`141 including dated historical snapshots.
- All42 extant numbered ADRs in numerical order:0001–0033, then0035–0043; reserved0034 has no file. Combined7090 lines, including every rider/revision/supersession/deferred note. Individual line counts:0001:114,0002:110,0003:98,0004:125,0005:83,0006:145,0007:115,0008:169,0009:238,0010:161,0011:145,0012:182,0013:221,0014:267,0015:170,0016:239,0017:227,0018:98,0019:229,0020:334,0021:153,0022:193,0023:92,0024:119,0025:140,0026:181,0027:234,0028:204,0029:159,0030:221,0031:163,0032:154,0033:203,0035:212,0036:207,0037:146,0038:153,0039:115,0040:172,0041:103,0042:99,0043:197.
- All15 standards Markdown files,2240 lines:README48, architectural-principles130, bsp-boot-checklist224, code-review135, code-style155, commit-style146, documentation-style91, error-handling178, infrastructure246, localization100, logging-and-observability149, release155, security-review135, testing155, unsafe-policy193.
- Bounded reads were used. Initial aggregate current.md truncations were recovered by explicit27–34 and72–99 windows in addition to full window coverage1–45/46–85/86–115/116–141. ADR0021/0022 aggregate truncation was recovered with0021:90–103/100–153 and0022:1–100;0026 truncation with1–45;0027 truncation with58–72/70–125. No truncated middle was counted as read. Long later ADRs were split or read individually. Total prerequisite lines9554.

After that gate: full perform-code-review/conduct-review/write-guide/update-glossary skills; full code-review master plan; full approved209-line track plan (truncated findings5–8 recovered in20–70) and literal T-050 task; full edit-target add-bsp/start-task skills; full changed README/glossary/both rewritten guides and complete diffs; analysis/roadmap/index targeted diffs; all new reports/evidence metadata/raw logs. No prior implementation review existed; preflight preparation was read after independent source assessment.

Authoritative actual-source reads: full Cargo.toml, .cargo/config.toml, rust-toolchain.toml, BSP build.rs, build-userland.sh, run-qemu.sh, smoke.sh, reference boot.s, userland hello linker/source, cap rights. Bounded complete units/ranges rather than claimed full files: main.rs task A/B, capability setup and user task registration/start, StaticCell/timing/boot related locations; scheduler FIFO/registration/cap pointer fields, start/exit/dispatch, IPC send/receive bridges; raw IPC send/recv transfer units; AddressSpace struct/cap creation/map/unmap; PMM allocation-zeroing/free validations; descriptor permission encoder/constants/tests; MapperFlush type/discharge; timer resolution/deadline helpers and CPU/GIC wiring searches; BSP syscall current-context/terminate units and vector SVC/panic routes; audit0030 amendments and Miri current-command references. Existing run-under-qemu guide was fully read; ci guide headers/job contract were inspected for inventory claims, not claimed as a whole guide/CI audit.

Limits: no whole unchanged Rust source/test/unsafe/architecture/CI corpus audit, no external source browsing or posting, no hosted result refresh, no behavioral runtime rerun, no parent checker reliance. Source searches are explicitly targeted inspections, not whole-file reads. The separate security report is independently authored and will be linked with its actual outcome.


## Delivered paired-security result and bounded correction verification

This addendum preserves the initial frozen-HEAD **Request changes** verdict and open C01 disposition above. Those are the original assessment of `74f8e837bd13e10b71f517446ae0d108c5215e42`, not the corrected commit's state. Subsequent references above to awaiting delivery/correction describe that initial point in time; the actual subsequent events and final scoped disposition follow here.

I read the separate security report in full, including its initial 129-line result and subsequent reconciliation. Its independent initial verdict is **Approve — zero verified new security findings**, with explicit dispositions across all eight axes. After the coordinator relayed primary C01, that reviewer independently rechecked the pointer/source obligations and confirmed the same **Low C01**, attributed to code-review provenance. Its report also records reading the actual paired 160-line code report. This is one shared finding, not two independent discoveries; there is no dispute or additional security finding. The passes ran independently in parallel, then reconciled their results. This primary agent did not perform the separate security review or inherit its source-reading ledger.

The separate security report preserves existing **HIGH T-038**, Ready and unresolved: input-only x2 in the console shim is overwritten by syscall return (`userland/tyrne-user/src/lib.rs:108`, `bsp-qemu-virt/src/syscall.rs:224`, `vectors.s:237`). Its approval covers this documentation change, not existing shim soundness, production security or human approval. Those limits remain applicable here.

**Correction reviewed:** clean `development` HEAD `523615603f87f6f11f2030db4d6d974c38330f0d`, bounded correction range `74f8e837bd13e10b71f517446ae0d108c5215e42..523615603f87f6f11f2030db4d6d974c38330f0d`. I read the entire three-file delta: guide wording, verification-report correction/provenance section and task history. I reread scheduler field documentation and raw binding at `kernel/src/sched/mod.rs:275–300`, registration Safety contract/signature at `:410–465`, and the actual BSP current-context resolution/dereference at `bsp-qemu-virt/src/syscall.rs:165–195`.

At `docs/guides/first-userspace.md:115`, the correction now names the address-space handle separately from a raw capability-table pointer and explicitly requires the table to outlive the task, no live mutable borrow across a context switch, and caller responsibility. This matches `AddressSpaceHandle` versus `*mut CapabilityTable`, retained-pointer storage and later momentary `&mut` materialization. The original compressed phrase is absent from the guide. **C01 is resolved.** This is a factual guide correction and does not claim new type enforcement, pointer generation checks or runtime safety implementation.

The additional report/history accurately count C01 once, preserve pending reviews, and distinguish later coordinator diagnostics (293 targets) from the earlier retained snapshot (292). The task remains In Progress with unchecked acceptance boxes. The cumulative implementation range still has the same32 paths and no executable/build/CI change. Direct diff of the entire evidence directory between the frozen and corrected commits is empty: no retained raw log, metadata or diagnostic bytes changed. I independently ran cumulative `git diff --check` successfully and confirmed the clean exact HEAD. The coordinator-reported 293-link rerun is attributed to the coordinator; I did not rerun its checker. The guide change adds no new link/anchor, and the added task-history link was inspected as part of the delta. Unaffected original source/evidence checks remain applicable because their inputs are unchanged.

**Final scoped R1 disposition after verified correction: Approve, zero open code-review findings at `523615603f87f6f11f2030db4d6d974c38330f0d`.** The initial Request changes and its provenance remain preserved above. I subsequently read the actual paired security final bounded-verification addendum in full: **Approve on the same corrected HEAD**, zero unresolved findings for this documentation delta, C01 independently verified resolved. Its zero independently originated findings and attributed shared-C01 count remain preserved; this is the security reviewer’s delivered disposition, not an inferred approval. Entirely fresh Round2 code/security reviews and maintainer review remain pending; this bounded verification does not replace them or authorize Done/main merge/hosted publication. No behavioral rerun or repository mutation was performed by this agent.

---

## Retained Round 2 primary report

# Code review 2026-10-13 — Track B.2-2 Step 6 / T-050, fresh Round 2

- **Change:** clean `development`, cumulative `75de2ba90e151bae33e14d2db4a8278837e7775d..523615603f87f6f11f2030db4d6d974c38330f0d`; preceding canonical boundary `054e13e2a368bb6699657ebc5b58e4daf98a23f1`.
- **Reviewed HEAD:** `523615603f87f6f11f2030db4d6d974c38330f0d`, independently verified clean at entry and after diagnostics.
- **Reviewer:** Codex AI agent `/root/b22_t050_r2_code`; not the maintainer, not @cemililik, and not human approval.
- **Configuration:** coordinator-configured GPT-6.1 Sol / high; fresh primary context. Configuration is reported from assignment, not runtime introspection.
- **Risk class:** Security-sensitive documentation describing capabilities, IPC, syscalls, MMU, scheduler and boot. No executable/build/CI change.
- **Security-review cross-reference:** separate fresh `/root/b22_t050_r2_security`, `/tmp/tyrne-b22-t050-r2-security.md`; actual delivered report will be read and appended after this initial independent report is written.
- **Authority:** read-only repository review. Only this temporary report written; root owns corrections, canonical artifacts/indexes/trailers. No builds, branches, commits, external posts, merge or task promotion performed.

## Correctness

### R2-C01 — Bridge-phase definition prohibits work expressly allowed by ADR-0040

- **Severity:** Low. Factual planning-document defect, no runtime regression or new security exploit alleged.
- **Location:** `docs/glossary.md:26`: “Tyrne's B.2 consolidation bridge sits between B and C and must close before C/D work begins.”
- **Authority:** `docs/decisions/0040-phase-b2-consolidation-bridge.md:44`, Decision outcome rule 2, prohibits opening Phase C/D milestones and letting their implementation tasks leave Draft while B.2 is open. The same rule expressly allows and encourages Phase C planning artefacts: scoping drafts, Proposed ADRs and T-074 readiness sweep.
- **Impact:** The new definition's unrestricted “work begins” wording misstates the accepted gate and tells a newcomer that permitted planning/readiness work is prohibited. T-050 specifically requires accurate new Bridge phase/Track vocabulary; this is within the requested factual correction scope.
- **Remedy:** State the actual milestone/implementation gate and the explicit permitted Phase C planning exception. For example: B.2 must close before C/D milestones open or implementation tasks leave Draft; Phase C planning remains permitted. Preserve the general dotted-ID/stable-letter definition and ADR link. No policy change or new ADR is needed.
- **Provenance:** Independently identified in this fresh primary source/decision pass before reading R1 reports or the paired R2 report. Root subsequently independently confirmed the same authority conflict. Distinct identifier R2-C01 prevents collision with R1 C01.
- **Disposition at frozen HEAD:** Open; correction required for the clean source-backed T-050 document contract.

Other assessed correctness areas match source and retained runtime evidence:

- README separates target userspace services/drivers/init from today's privileged BSP drivers and sole EL0 hello. Six workspace members, three default host members, per-table revocation and temporary-low/high-half/per-task translation are appropriately qualified.
- Yield/exit are current-task control-plane calls; send/recv/console validate the calling table's object/right. The eight actual rights include CONSOLE_WRITE. Console checks the complete window and USER leaves before effects. The write-side user-copy primitive is tested but has no current syscall caller.
- CDT revocation is bounded to the same table. IPC transfer stages leaf authority in the endpoint; a full destination table preserves pending transfer for retry. Documentation does not invent global atomic revocation, badges or automatic reply capabilities.
- FIFO source and both raw traces agree: B waiting → A sending → user console/exit → B receives/replies → A receives/completes. B's post-yield tail and idle are unreached; A permanently spins. No timer/preemption execution is inferred from timer-ready output.
- Console resumes EL0; exit calls the unsafe module-level free `task_exit_current`, abandons the frame and dispatches another task. Exit status is ignored; task/AS/table resources and terminal-state lifecycle work remain unresolved.
- AP controls EL0 data access, UXN EL0 execution, PXN privileged execution. Actual RAM AP00/UXN1/PXN0, MMIO AP00/XN both1, user image AP11/UXN0/PXN1 and writable user stack AP01/XN both1 are correctly stated. Existing privileged executable RAM, missing section W^X and non-SVC EL0 panic are explicit.
- The added BSP template is already-EL1 and begins with DAIF masking before stack/FP/BSS. EL2 entry requires Accepted complete target boot policy. Minimal port completion is distinguished from the full reference EL0/IPC trace.
- Timer resolution nearest-integer/minimum1 and absolute-deadline saturating ceiling conversion are distinct source algorithms. No new timer policy is enacted. Six bootstrap frames occupy the reserved .bss range with shared L2 tables; no fictitious standalone output section is promised.

## Style

No confirmed style issue. Both rewritten task guides have the full write-guide structure, imperative commands, tagged fences and verification/troubleshooting/reference sections. The guide inventory distinguishes four substantive guides from its README index. Existing historical accepted-guide status and pending refreshed-guide state are not conflated.

The glossary stays a flat bold-headword list; every invisible anchor immediately precedes its entry. Displayed vocabulary adds exactly four approved terms. The MMU/mmu_bootstrap/.boot_pt grouped exception is retained explicitly. The target diagram remains Mermaid; repository-tree text is inventory. English prose and the exact approved copyright spelling are preserved. No Rust formatting/lint churn or preference-only issue was raised. Cumulative `git diff --check` passes.

## Test coverage

No behavioral source change, new API, Error variant or unsafe operation exists. No fresh QEMU/Miri/coverage or unit-test rerun was needed to establish this documentation delta. I did not fabricate such a run.

Before implementation/source assessment I read meaningful existing tests: dispatcher current-task yield/exit and fail-closed cases; console no-right/no-output and release-number rejection; user-copy success/two-page/non-USER/unmapped-second-page/read-only cases; IPC transfer and full-table pending retry; descriptor kernel/user permission tests. Scheduler FIFO and yield state-transition tests were also read in full. Tests are supporting source contracts, not freshly executed outcomes.

Independently executed read-only diagnostics:

| Check | Result |
|---|---|
| Clean source/step scope | Exact frozen HEAD, empty tracked status;32 changed paths, no Rust/assembly/shell/Python/Cargo/toolchain/lock/CI delta. |
| Runtime source archive | Recomputed `git archive --format=tar 75de2ba…` SHA256 `68500b9e7a5f05d48b668ca6bd8e1c28ed8e7f5625e6ee4d2fbf5f10a56ebe28`, exact retained match. |
| Retained stdout/stderr |12 stream size/hash records match metadata, including empty stdout; all six recorded exits0. |
| Raw QEMU logs | Independently hashed debug1139 bytes / `80a53a565fa95fcf4d509d38668ddc9ad3a73b03bff93d74b16a17797a1c0d8c`; release1113 bytes / `2a09900e123c78f16118db5999f7f8a1aa358ece6e779cf86788915f61ef499a`; exact retained matches. |
| Event/marker counts | Both two total exception records, both SVC/EL0→EL1; two ERETs each. Greetings1debug/0release; exit/completion1each. Full logs read with timeout termination tails preserved. |
| Profile prerequisites | Actual .cargo aliases, build-userland.sh, build.rs and smoke/run scripts substantiate matching userland-before-BSP chains. Six retained real commands cover explicit debug/release build pairs and matching smoke; smoke repeats warm builds. |
| Local navigation | Independent bounded inline-link/path/fragment diagnostic:293 actual targets,18 Markdown fragments, zero errors; task's literal `](…)` template skipped. This is actual-form checking, not a general Markdown grammar or T-056 parser certification. |
| Glossary |50→54 headwords; only AddressSpace/Bridge phase/PMM/Track added;27 changed existing definitions;54 unique immediate anchors. Full ledger/definitions and grouped order inspected. |
| Guide inventory | Files README,ci,first-userspace,run-under-qemu,two-task-demo; four substantive rows match. Both other existing guides fully read for actual status/inventory context. |
| Copyright | Equal old/new line counts; only LICENSE189 and NOTICE2 differ, exact `Copyright 2026 HodeTech, Cemil ILIK and Tyrne Contributors`. All other LICENSE bytes/indentation/newline preserved. |
| Whitespace/messages | Cumulative diff-check passes. Both actual English docs(guides) commit messages contain genuine ADR0040/0043 Refs trailers. |

Diagnostics were inline Python/read-only git/sed/rg/cat; no checker file, parser or repository artifact was created. An initial copyright diagnostic used an incorrect guessed old string and returned False; direct split-line comparison then established the precise approved-only delta above. Two mistyped source paths/one ADR filename and one glob discovery failed harmlessly and were corrected with rg; these failures are not repository findings. One first metadata summary looked for argv/exit_code instead of command/exit; subsequent actual-key read verifies all six commands and exits.

Limits: retained execution is coordinator provenance, not execution witnessed by this reviewer. Original export and compiled ELF binaries are not retained; ELF identities/tools/times are metadata. The archive digest proves reproducible source bytes, not capture authenticity. Installed tools/caches were reused, so no first-install proof exists. No interactive mon:stdio/Ctrl-A automation, hostile EL0 isolation proof, exhaustive ABI/register-leak proof, strict-provenance proof, timer IRQ/idle/preemption exercise, SMP, hardware, hosted CI refresh or benchmark is asserted. Single elapsed debug/release timings are host-dependent observations. Coordinator verification.json is the earlier292-target snapshot, correctly distinguished from the later293-target report. My bounded check is independent; I did not run the coordinator checker or adopt it as grammar coverage.

## Documentation

**R2-C01 is the sole newly confirmed gap.** All other literal acceptance content is implemented; process closure remains pending.

| Literal T-050 criterion | Assessment |
|---|---|
| Guides index current framing, four-file inventory/status, no numeric phase labels | Pass; existing/planned rows separated and refresh review status truthful. |
| README documentation map first-userspace link | Pass. |
| Quick-start actual trace and illustrative unsafe/user-copy0030 | Pass; missing loader banner gone; live75de raw FIFO trace underlies ordered elided output. |
| Four glossary additions/ADR/source accuracy | AddressSpace/PMM/Track pass; Bridge phase requires R2-C01 correction. |
| M and Rendezvous/Reply pure moves separate from factual corrections | Pass;27 existing-definition changes recorded separately. |
|54 immediate unique stable anchors/scheme history | Pass; full displayed-headword lowercase ASCII words/hyphens scheme and grouped exception recorded. |
| Phase path templates across analysis/roadmap/start-task | Pass; phase-id/B.2→phase-b2 and phase-b2.md, Tracks distinct from milestones. |
| add-bsp current minimal trace/end/version/README link | Pass; DAIF-first already-EL1, full policy for EL2, printed PID path and int versus int,unimp accurate. |
| Approved common copyright, LICENSE189 only | Pass, independent exact-line comparison. |
| Clean checkout/userland profiles; exit/free function/permissions/glossary source corrections | Pass including independently rechecked R1 raw-table correction. |
| DoD links/English/tagged fences/commit Refs/scope | Pass for snapshot;32 paths covered by named content plus source-bound evidence allowance. |
| DoD In Review/current/index/checkbox closure | Correctly pending until both fresh rounds/canonical integration. T-050 In Progress/unchecked is not a defect. |

Current phase accounting46=8historicalDone/24Ready/8Draft/5InReview/1InProgress remains consistent; no new task Done or maintainer review is claimed. The preparation note's initial partial ledger, subsequent completed prerequisite ledger and later clean-source boundary are historical stages. It is not either review round. The executed75de source, later document working tree and subsequent R1 correction are labeled separately. No new architectural/EL2/lifecycle policy or ADR is introduced.

## Integration

No integration defect apart from R2-C01's inaccurate accepted-gate description. The cohesive document refresh plus full source-bound evidence is larger than the usual400-line guideline but splitting the evidence from the claims would obscure review. No dependency, crate, action, pin, binary blob or executable caller changed. Existing execution-trace anchor remains; downstream navigation resolves. Tool/profile overwrite behavior and smoke versus interactive runner responsibilities are accurately described. Root retains canonical review/index/trailer work and status promotion responsibility; maintainer approval remains pending.

### Full code-review standard checklist

| Consideration | Disposition |
|---|---|
| Correctness | R2-C01 Low; remaining assessed contracts match source/evidence. |
| Capability semantics | Object rights/current-task control plane, local CDT, staged transfer and raw caller-table binding verified; no new authority. |
| Fault containment | Existing non-SVC panic/unreclaimed exit explicit; no new containment promise. |
| Unsafe discipline | No unsafe delta; source raw-lifetime/DAIF/copy0030 contract checked. Not whole-program recertification. |
| Error handling | No changed Result/unwrap/expect; source bad syscall/release gate/non-returning exit correctly described. |
| Tests | Selected meaningful tests read, fresh retained source/profile traces checked, no behavioral rerun falsely claimed. |
| Documentation | Complete skill structures/anchors/scope; R2-C01 sole new factual gap; no new public Rust item needing rustdoc. |
| Architectural principles | P1–P12 individually below. |
| Dependencies | None; add-dependency not triggered. |
| Naming/style | English/tagged fences/flat glossary/Mermaid pass; no bikeshedding. |
| Commit messages | Both conventional imperative English docs(guides), genuine Refs0040/0043; canonical trailers root-owned. |
| Author preparation/run | Task/approved plan/retained verification inputs assessed; real six-command source-bound evidence internally consistent. |
| Post-fix sweep | Old misleading table-handles phrase absent from live guide. Owned image-loaded/fixed-log mistakes removed; historical quoted opening records deliberately retained. R2-C01 live wording still requires correction. |
| Security gate | Required distinct fresh R2 assessment; actual paired report will be read after initial write. |

### Architectural principles P1–P12

| Principle | Disposition |
|---|---|
| P1 No ambient authority | Pass for delta: actual identity controls versus capability-gated object operations qualified. |
| P2 Smallest TCB | Pass: current privileged BSP/target services distinguished; no expansion. |
| P3 Userspace drivers/filesystems/network | Pass for description: explicit target versus current placement; no shipped isolation claim. |
| P4 Boundary capability checks | Pass: rights/caller table/whole-window validation accurately described; current-task exception explicit. |
| P5 Rust-only/audited unsafe | Pass: no executable delta; illustrative audited copies and manually upheld raw obligations stated. |
| P6 HAL separation | Pass: actual BSP/HAL contracts preserved. |
| P7 No proprietary blobs | Pass: textual evidence only, no binary/dependency addition. |
| P8 ADR-first | Low R2-C01 must accurately summarize Accepted0040; correcting prose requires no policy change/new ADR. |
| P9 English | Pass, exact approved holder preserved. |
| P10 Mermaid | Pass, existing target architecture diagram Mermaid. |
| P11 Reproducibility | Pass within stated source/profile/tool/hash/cache limits; no first-install/authenticity claim. |
| P12 Complete scope on main | Pending correction/reviews/canonical/maintainer; no Done/main merge or subsystem completion claim. |

## Prior-round reconciliation after independent assessment

Only after independently completing current source/diff/evidence assessment and identifying R2-C01, I read actual complete R1 reports: `/tmp/tyrne-b22-t050-r1-code.md`178 lines and `/tmp/tyrne-b22-t050-r1-security.md`151 lines, including initial outcomes and final bounded verification addenda. Their claims were not treated as this fresh review.

R1 code originally requested changes for sole Low C01 at frozen74f8: “address-space/table handles” conflated AddressSpaceHandle with *mut CapabilityTable. R1 security initially independently approved with zero originated security findings; after receiving code C01 it independently corroborated that shared finding, correctly attributed once. Both actual final scoped R1 outcomes approve corrected5236156 with C01 resolved. No other confirmed R1 correction exists.

I independently read the complete74f8..5236156 three-Markdown-file patch and rechecked scheduler428–452 Safety/signature and BSP syscall165–195 actual pointer resolution. Guide115 now names the address-space handle and raw capability-table pointer separately, requires table outlive task/no live mutable borrow across switch, and assigns the obligation to trusted caller. This matches source and does not invent lifetime/type enforcement. Report/task provenance correctly preserves one shared code-origin C01 and pending reviews. Retained evidence bytes and executable source did not change. **R1 C01 independently verified resolved.**

Existing **HIGH T-038** remains Ready/unresolved. The input-only x2 console shim is overwritten by syscall return; no source fix, safe-ABI certification or production-security approval is conferred by this documentation review. This was independently visible in current userlib/trap source and is preserved by both R1 reports. “Safe wrappers” describes the Rust call-site syntax, not proof that T-038 is closed.

## Initial independent verdict

**Request changes** on frozen `523615603f87f6f11f2030db4d6d974c38330f0d`.

One required factual correction: **Low R2-C01**, glossary Bridge phase gate overbreadth. No other verified code/document finding or demonstrated runtime evidence gap. Preserve R1 C01 as resolved and distinct from this finding. Fix R2-C01, then independently verify the bounded correction and actual paired security result. This initial report is written before consuming the R2 security report, preventing circular review or borrowed findings. Fresh R2 does not replace maintainer review, authorize Done/main merge or certify existing runtime security.

## Independent literal read ledger and limits

Mandatory prerequisites completed before task/diff/source assessment: actual AGENTS.md, entire CLAUDE.md, entire current.md141lines including historical tail; all42 extant numbered ADRs0001–0033 then0035–0043, reserved0034 absent, every rider/revision/supersession/deferred note; all15 standards including README. No inherited summary/parent read substituted.

Truncation recovery ledger: current1–75 recovered with1–35/36–75, complete76–141 separately. ADR0009 separately recovered after0007–11 aggregate truncation;0016:215–239 and0017:1–45 recovered boundary;0021:80–100/95–153 and0022:1–100 recovered;0024 fully reread and0025:1–24 recovered;0026:65–82/80–110,0027:78–100/99–133,0028:62–76/75–111,0030:85–98/96–115 recovered. ADR0033/35/36 split into bounded halves;0038 final6lines recovered after0038/39 aggregate truncation;0040 separately and0043 in two windows. Other ADRs fully visible in bounded reads. All15 standards fully visible, not truncated. Every formerly missing window was recovered before marking prerequisites complete.

Then full four skills perform-code-review/conduct-review/write-guide/update-glossary, full code master plan, full T-050 task and approved Track2 plan. Full changed substantive README/glossary/guides/indexes/edit-targetskills/phase-entrydocs; full scoped patches and all new evidence/report files. README diff truncation recovered50–115; glossary diff truncation recovered80–103/100–150. All14 logs, metadata, diagnostic/glossary manifests read completely. Preflight and verification report conclusions read after independent source assessment; actual R1 reports only afterward. All four actual guides read in full, not just table names.

Full or complete bounded-source reads: actual Cargo aliases/config, BSP build.rs, build-userland/smoke scripts, userland hello source/linker and userlib. Targeted complete source functions/units and selected tests, not whole-file audit claims: rights/cap copy/derive/revoke/take; IPC send/receive/staged transfer and retry tests; syscall control/console/release cases; user-access implementation and meaningful permission/copy tests; AS representation; PMM alloc/zero/free; scheduler registration Safety/FIFO/yield/exit/dispatch/send/receive bridges and selected tests; BSP task A/B/registration/cap setup/timing, syscall bindings/termination, vectors SVC/panic; AP/UXN/PXN encoder/constants/tests; bootstrap roots/RAM flags/linker six frames; EL0 entry register scrub; timer deadline/resolution/wiring; DAIF boot head and runner int-log path. Search hits are discovery, never whole-file reads. No claim to full unchanged kernel/tests/architecture/unsafe audit/CI corpus.

No external browsing, posting, hosted evidence retrieval, repository writes, build-mutating commands or child delegation. Commands were read-only git, rg, sed, cat, wc and inline Python diagnostics. Only this requested temporary report is written. Governance/source reading, independent diagnosis, prior-round reconciliation and paired-review reading remain distinct provenance stages.

## Actual paired R2 result — reconciliation

After writing the entire initial independent report above, I read the actual separate `/tmp/tyrne-b22-t050-r2-security.md` in full at its158-line initial delivery. It records a fresh independent eight-axis/P1–P12 assessment on the same clean5236156, **Approve for the independently assessed security delta, zero independently discovered new security findings**, with the code-origin Bridge-phase relay explicitly arriving only after its independent assessment. It preserves R1 C01 as resolved and existing HIGH T-038 as Ready/unresolved. No runtime/ABI/security certification or maintainer approval is inferred.

The separate reviewer then notified me that it had read my actual153-line primary report and independently confirmed **shared Low R2-C01** against glossary26/ADR0040:44. That corroboration is its own source recheck after my finding, not a second independent discovery. It is appending the attributed shared finding and changes-requested recommendation; the final delivered addendum will be read separately before claiming its exact wording. No dispute or additional independently originated security finding was reported.

**Reconciled current primary verdict remains Request changes** for the single Low R2-C01 on frozen5236156. The underlying security assessment is complete; correction/verification and final canonical integration remain pending. This report does not preapprove an unwritten correction.

Additional bounded source confirmation after initial report: audited copy-user0030 body/amendments682–709 reread, recovering the truncated704 amendment with a separate700–704 window. Current `core::ptr::copy`/per-page USER preflight supersedes historical copy_nonoverlapping/identity wording. Userlib input-onlyx2, actual syscall result overwrite and vector reload were reread, corroborating the existing T-038 limitation. No new issue or repository change was found.

Read the actual paired security addendum159–176 in full after delivery. Its exact reconciled verdict is **Changes requested on5236156: address shared Low R2-C01, then verify the bounded correction; zero independently discovered new security findings, one code-origin Low documentation finding independently corroborated and still open**. Its initial standalone approval remains historical and is not misrepresented as a joint approval. It explicitly records its corrected reviewer-report rights enumeration as report QA, with source/glossary already correct; this is not a repository finding. No disagreement or additional issue emerged.

A final byte-oriented LICENSE/NOTICE comparison independently confirmed every byte outside LICENSE189/NOTICE2 is equal to the75de baseline, including LICENSE's three-space indentation and LF. This strengthens the earlier split-line check without changing the finding/verdict. Final primary disposition at the frozen boundary remains **Request changes for R2-C01 only**; root correction and independent verification are outstanding.

## Bounded R2 correction verification — independent primary result

This append preserves the initial **Request changes** on frozen5236156 and the original code-origin R2-C01 provenance above. It is verification of the confirmed correction, not a new review round or retrospective removal of the finding.

Independently checked clean `development` HEAD **`946f45f34f7eac90164adccfcd71e4c7f77c1f8e`** and read the complete5236156..946f45f patch: exactly three Markdown files, six insertions/one deletion (glossary definition, verification-report append, task-history row). Reread Accepted ADR0040 Decision outcome rules1–3, especially rule2 at44, against the complete changed definition. Also reread first-userspace115 and scheduler424–454 Safety/signature for R1 continuity.

**R2-C01 resolved.** Glossary26 now gates C/D milestone opening and implementation tasks leaving Draft, and explicitly permits Phase C planning including Proposed ADRs and readiness sweep. This precisely preserves ADR0040's distinction. The general dotted-ID/stable-letter definition and ADR/Track links remain intact; no new policy, governance decision or ADR is enacted. **R1 C01 remains resolved:** the unchanged guide distinguishes AS handle from raw table pointer and retains caller-managed table lifetime/no live mutable borrow across switch.

The complete patch and independent diagnostics establish: same displayed headword inventory and exact anchor sequence;54 immediate anchors; no runtime source/tool/config/CI delta; no retained evidence-directory byte delta; LICENSE/NOTICE unchanged; same32 cumulative paths. The live overbroad phrase is absent. Cumulative git diff --check passes. T-050 remains In Progress/unchecked pending canonical closure; the new report/history accurately count one code-origin R2 finding corroborated after the distinct security assessment, separately from fixed R1 C01. No false human approval, runtime fix or capture change is introduced.

Root's294-target/18-fragment rerun is attributed to root; I did not rerun that full diagnostic at946f45f. The bounded patch adds one existing verification-report link in task history; it resolves to the already-read existing report. Earlier independent source/evidence checks remain applicable because their bytes are unchanged. No behavioral/build/Miri/QEMU rerun was performed or required by this prose-only correction.

**Independent bounded primary disposition: correction verified, zero open code/document findings at946f45f.** Final primary approval still awaits reading the actual paired security post-fix addendum, which remains a separate delivered outcome; this independent verification is written before that consumption to avoid circular waiting. Canonical integration and maintainer review remain root/maintainer responsibilities. Existing HIGH T-038 remains unresolved and outside this correction.

## Final scoped R2 primary verdict after actual paired verification

Read actual paired security post-fix addendum177–188 in full after my independent bounded result was written. Its delivered final scoped verdict is **Approve on946f45f34f7eac90164adccfcd71e4c7f77c1f8e**, zero independently originated security findings; shared code-origin Low R2-C01 corroborated and now verified fixed; zero unresolved delta findings. Its independently checked correction/source/anchor/evidence/legal-byte preservation agrees with mine. R1 C01 remains fixed; existing HIGH T-038 and all runtime/evidence limits remain unresolved. This is the distinct security agent's actual outcome, not an inferred second pass or inherited read ledger.

**Final scoped R2 code verdict: Approve on clean946f45f34f7eac90164adccfcd71e4c7f77c1f8e — zero open code/document findings.** Sole independently discovered R2 Low R2-C01 is verified resolved, distinct from resolved R1 C01. Original frozen-HEAD Request changes and cross-review provenance remain preserved. This bounded verification closes the correction; it is not a third review round, maintainer approval, Done promotion, main merge, hosted publication or existing runtime security certification. Root owns canonical artifact/index/trailer integration; human review remains pending. Only this temporary report was changed by this reviewer.
