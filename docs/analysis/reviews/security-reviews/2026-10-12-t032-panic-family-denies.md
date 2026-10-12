# Security review 2026-10-12 — T-032 panic-family denies

- **Change:** T-032 on `development`, `8591ceb..4f2c38c`.
- **Reviewer:** fresh independent `b21_step5_round1_security`, acting on behalf of @cemililik; `gpt-6-astra` / high requested, fresh context.
- **Separation from code review:** independent agent with an empty security checklist; implementation and paired code context not inherited.
- **Unsafe audit cross-reference:** UNSAFE-2026-0025, the T-032 unused-argument amendment.
- **Paired code review:** [code-review artifact](../code-reviews/2026-10-12-t032-panic-family-denies.md).

> **Current reconciliation:** Both fresh code/security rounds Approve with no new actionable finding. Changed UNSAFE-2026-0025 reasoning is explicitly approved in both rounds, with actual approval recorded append-only. Independent compiler mutations verify sibling and callee exception boundaries; historical audit bytes are preserved. Local/hosted implementation gates passed. Runtime BSP unmap, SMP and unchanged HIGH T-038 remain outside this scoped approval. Final maintainer PR review remains pending; T-032 stays In Review.

## Round 1 security review

**Approve the T-032 delta in `8591ceb..4f2c38c`. No new security finding.** I explicitly approve the changed UNSAFE-2026-0025 argument reasoning below. This is a scoped first-round security verdict, not whole-kernel soundness, Done promotion or final merge approval.

- **Change:** approved Track B.2-1 step 5 on `development`; implementation `c3f32c8`, actual-SHA audit reconciliation `b6572cc`, hosted-evidence documentation `4f2c38c6a8fdf221e00a0f0cb461303ed0b74b55`.
- **Reviewer:** independent Codex security agent `/root/b21_step5_round1_security`, acting for the maintainer.
- **Requested configuration:** `gpt-6-astra`, high reasoning, fresh context (`fork_turns=none`). This records requested configuration, not independently attested runtime identity.
- **Date:** 2026-10-12, Europe/Istanbul.
- **Separation from code review:** fresh independent agent/context and empty security checklist; no implementation or ordinary code-review pass performed by this reviewer. Paired code review is separately owned.
- **Unsafe audit cross-reference:** UNSAFE-2026-0025, `docs/audits/unsafe-log.md:530`, T-032 amendment at :560.
- **Procedure:** `perform-security-review` and `conduct-review`; all eight axes, 32 standard checklist items and the master-plan allocation item (33 total), plus P1–P12.
- **Mutation boundary:** no repository/GitHub edit, commit, branch mutation or external communication. Tests wrote only disposable private source/target trees and temporary evidence. Shared hello.bin and kernel ELF were not rebuilt. Coordinator owns publication/index/cross-reference/trailer and append-only audit approval recording.

### Reading and scope

Read AGENTS/CLAUDE, current roadmap, numbered ADR corpus in numerical traversal (0001–0033 and 0035–0040; 0034 reserved), all standards, skill index and both review skills, full security master plan and security model. Bounded reads recovered truncated policy portions. Read T-032 and the negative-probe harness before examining the source diff; then all executable changes, complete MMU implementation/helper, the ten exception functions and callers, Cargo aliases/toolchain, relevant CI changes, audit entry/history, capability unmap and its FakeMmu regression. Consulted the preflight review and prior T-037/T-030 security results and exclusions. This context reading is not a fresh whole-tree security certification.

The only runtime expression change replaces the infallible zero-frame construction/unwrap in `QemuVirtMmu::unmap` with an existing typed root value as the helper's ignored third argument. Other Rust changes are lint attributes/comments. No syscall body, userland shim, capability policy, fatal exception policy, assembly, dependency, toolchain or architecture decision changes. Git-object comparison confirms both syscall/shim files, Cargo.lock and toolchain pin are byte-preserved.

### 1. Capability correctness

| Item | Disposition, adversarial question and justification |
|---|---|
| S01 — Every introduced privileged operation requires a capability | **OK for delta.** Can a caller unmap without authority because the root is passed twice? No operation or entry point is introduced; `cap_unmap` still resolves the capability and live arena object before MMU mutation. |
| S02 — Narrowest sufficient capability | **OK for delta.** Does the replacement root grant a broader right? It is a copied physical-frame address, not a capability or new grant; the existing address-space authorization model is unchanged. |
| S03 — Checks precede effects; failures leak no state | **OK for delta.** Can the new argument cause a descriptor write before authorization? The unchanged capability/arena checks precede MMU entry, and no new write exists. |
| S04 — Move-only capability transfer | **N/A.** Could this copy transferable authority? No capability representation or transfer changes; PhysFrame is an address value, not an authority token. |
| S05 — Explicit duplication authority | **N/A.** Could a new duplicate bypass authority? No capability duplication path is added or changed. |
| S06 — Atomic revocation | **N/A.** Could revocation become partially applied? No revocation or concurrency operation changes. |

The pre-existing v1 address-space capability model is kind-based; this review does not invent per-operation MAP/UNMAP rights or expand the five-syscall set. Demo endpoint caps stay in trusted kernel task tables; the default EL0 task receives its console cap, not those endpoint caps. The benchmark EL0 table remains empty.

### 2. Trust boundaries

| Item | Disposition, adversarial question and justification |
|---|---|
| S07 — Validate userspace input before use | **OK for delta.** Can hostile syscall arguments enter an newly exempted function? Syscall code has no panic-family allow; the new exceptions attach to existing boot/demo/benchmark or fatal functions, with unchanged routing. |
| S08 — Userspace pointers only through validated mappings | **OK for delta.** Can the dummy root become a user-pointer dereference? The ignored parameter is never dereferenced on unmap; existing mapping/copy-user consumers are unchanged. |
| S09 — Range-check user lengths | **OK for delta.** Can a longer buffer become accepted? No buffer length, user window or translation validation changes. |
| S10 — Typed userspace message parsing | **N/A.** Could malformed bytes exploit a new parser? No wire format/parser is added or modified. |
| S11 — IPC grants only held/explicitly transferred authority | **OK for delta.** Can allowed demo panics hide an authority-transfer change? The demo and benchmark bodies/cap grants are unchanged; their IPC calls retain `None` transfers and statically provisioned rights. |

The changed verification boundary is source-to-Clippy evidence. Both new modes append a non-test root function outside exception scopes. `black_box(None::<u64>).unwrap()` prevents the test from depending merely on a trivially known-None warning. The actual exact aliases are `cargo host-clippy` and `cargo kernel-clippy`; private copied Cargo configuration and toolchain preserve their target and `-D warnings` behavior.

The harness requires both nonzero status and `clippy::unwrap_used`, rejecting unrelated failures or unexpected success. It copies tracked current files via NUL-delimited names, preserves script modes, uses mktemp isolation and a separate CARGO_TARGET_DIR, and deletes its quoted private root on normal exit/error. BSP builds source-derived userland only inside that copy before linting, preventing a missing shared image from masquerading as the intended lint rejection. Independent execution observed cleanup for both real modes. The supplied controlled fixtures additionally cover unrelated failure, unexpected green, exact argv, private target/image and CLI errors. This is a regression guard over trusted source/build tools; it does not authenticate deliberately forged compiler output or a malicious contributor who edits the gate and code together.

Workflow additions are fixed command strings inside existing jobs. No trigger, action pin, permission, secret, credential persistence or cache change appears. Normal build/lint gates precede the negative probes; negative failure is evidence of rejection, not red production CI. Private targets avoid contaminating ordinary cached outputs.

### 3. Memory safety

| Item | Disposition, adversarial question and justification |
|---|---|
| S12 — Unsafe policy compliance | **OK for changed reasoning.** Does the new operand broaden unsafe or lack a record? Adjacent SAFETY explains why pa is unused and why an allow was rejected; the dated 0025 amendment names actual implementation SHA c3f32c8. Explicit approval follows. |
| S13 — Safety invariants hold for every caller | **OK for MMU delta; flagged existing HIGH T-038, excluded.** Can unmap consume pa on an error or success path? All three intermediate calls receive literal true; all exits and the entire true leaf arm ignore pa. Existing unrelated x2 input-only/write-back mismatch remains HIGH and is not approved. |
| S14 — No uninitialized memory exposed | **OK for delta.** Can the substituted frame introduce garbage into a descriptor or return? No: pa is unused; the returned frame still comes from the existing L3 descriptor. No initialization changes. |
| S15 — No use-after-free; raw-pointer lifetimes justified | **OK for delta.** Can reusing root free or extend a frame lifetime? PhysFrame is copied by value; no allocation/free, owner, pointer computation or lifetime changes. Existing exclusive valid-table lifetime obligations remain. |
| S16 — No aliasing violations | **OK for delta.** Does passing root twice create two mutable references? Both arguments are value copies, not references; descriptor access, caller's mutable address-space borrow and table ownership are unchanged. |

**Explicit unsafe approval:** Reviewed `unsafe` in `bsp-qemu-virt/src/mmu.rs:307–333`, including the changed SAFETY comment and `walk_and_install_leaf` call at :319–328; I agree with and approve the changed SAFETY reasoning under UNSAFE-2026-0025. The call passes literal `true` for unmap. The helper reaches L3 through the unchanged root and VA, returns typed errors for missing/intermediate block mappings, reads the existing leaf, masks its PA, clears its slot and returns that leaf frame. Its `pa` parameter is used only in the false/map arm. Reusing already-valid `as_.root` as this ignored argument is sound and behavior-preserving under the existing table-validity/ownership/lifetime contracts. It introduces no new raw pointer or dereference and is preferable to weakening this non-init path with an unwrap allowance.

The root argument, flags, null frame provider, descriptor accesses and caller flush obligation are identical. `cap_unmap` still flushes the returned token before returning the frame. Alignment and index bounds remain unchanged; a copied PhysFrame does not itself create ownership or authorize mapping. The change does not fix or worsen pre-existing caller-contract debt.

Independent byte comparison removed the one new 1,502-byte amendment from the reviewed unsafe log and recovered the baseline log exactly: original entry and all historical amendments are preserved. The amendment accurately leaves actual review recording pending; coordinator should append this real verdict without rewriting that history.

**Limits:** default smoke exercises boot/map, not this BSP unmap branch. FakeMmu unmap/rollback tests verify kernel-layer behavior and TLB-token discharge, not physical BSP table walking. No new runtime unmap coverage is claimed. Original 0025 SMP-forward-compatibility language is expressly not endorsed; T-069 retains that work. No full table-walker/SMP/architecture recertification follows from this narrow equivalence proof.

**Existing HIGH retained:** `userland/tyrne-user/src/lib.rs:107` declares x2 input-only while `bsp-qemu-virt/src/syscall.rs:224` overwrites it on return. Both files are unchanged. T-038 remains its owner; host Miri, clean builds and successful boot neither downgrade it nor establish assembly soundness.

### 4. Kernel-mode discipline

| Item | Disposition, adversarial question and justification |
|---|---|
| S17 — No ISR allocation | **OK for delta.** Can the IRQ allowance enable a new allocation? IRQ body is unchanged; the annotation permits only existing panic behavior, with no new allocation path. |
| S18 — Bounded loops | **OK for delta.** Can attacker input create a new unbounded loop? No loop changes; pre-existing idle/demo/perf parking semantics are preserved and not newly certified as bounded. |
| S19 — Minimal critical sections | **OK for delta.** Does lint repair hold scheduler state longer? No lock, IRQ mask, borrow scope or context-switch sequence changes. |
| S20 — No new hot-path panic | **OK.** Can the guard conceal a new hostile-input panic? No panic/expect is added to runtime; the sole unwrap is removed. Exactly ten reasoned function exceptions, no HAL/syscall/MMU family allow. Assertions remain outside these lints. |
| MP-1 — Allocation exhaustion returns a typed error | **OK for delta.** Can malicious allocation exhaustion reach a new expect? No new allocation/error conversion occurs. Existing one-shot trusted setup expects remain scoped; MMU missing/allocation failures preserve typed errors. |

#### Exception inventory

| Function | Allowed lints | Classification and boundary |
|---|---|---|
| main::kernel_main_high (:996) | expect, panic | One-shot trusted boot; static image, fixed capacities and object setup precede scheduler start. |
| main::idle_entry (:522) | expect | Trusted scheduler invariant; yield runs only after start and its NoCurrentTask would indicate broken BSP state. |
| main::task_a (:674) | expect, panic | Trusted single-round demo; static endpoint/capability setup and fixed reply protocol. |
| main::task_b (:568) | expect, panic | Trusted single-round demo; matching static receive/reply protocol. |
| perf_bench::run (:147) | expect, panic | One-shot measurement-build object/image setup before start. |
| perf_bench::driver_yield (:439) | expect | Trusted benchmark scheduler invariant after start. |
| perf_bench::driver_send (:460) | expect | Trusted statically provisioned SEND cap and fixed ping-pong protocol. |
| perf_bench::partner_recv (:493) | expect | Trusted statically provisioned RECV cap and matching protocol. |
| exceptions::irq_entry (:187) | panic | Existing deliberate fatal unhandled-IRQ abort after EOI. |
| exceptions::panic_entry (:308) | panic | Existing fatal handling of unhandled exception classes. |

All ten attributes have `reason =`; none permits unwrap. Multiline enumeration and attached-function inspection agree. Function allowances do not exempt callees. Boot/demo/benchmark reasons do not relabel live syscall input as initialization. Fatal handlers are genuinely hostile-event reachable in the existing policy: accepting these annotations preserves that policy; it does not claim full task-fault containment is implemented or authorize a new fatal policy. Future additions inside allowed functions still require review. This task is three-lint enforcement, not proof of a panic-free kernel.

### 5. Cryptography

| Item | Disposition, adversarial question and justification |
|---|---|
| S21 — Reviewed primitives | **N/A.** Can a new weak algorithm be exploited? No cryptography is introduced. |
| S22 — Keys absent from diagnostics | **N/A.** Can new key handling expose material? No key material/handling changes. |
| S23 — Constant-time comparisons | **N/A.** Can secret-dependent comparison timing leak? Only public lint diagnostic matching is added; no secret comparison changes. |
| S24 — Acceptable randomness | **N/A.** Can predictable randomness weaken authority? No security RNG changes; mktemp serves exclusive host temporary-directory creation. |
| S25 — Nonce/IV/salt correctness | **N/A.** Can nonce reuse violate a contract? No such operation exists in the delta. |

### 6. Secrets and logging

| Item | Disposition, adversarial question and justification |
|---|---|
| S26 — No secrets in diagnostics | **OK for delta.** Can new output expose cap bits or credentials? Runtime panic strings/output are unchanged; new diagnostics are fixed harness text and normal compiler/build output without secret arguments. |
| S27 — Redacted sensitive Debug | **N/A.** Can a new formatter expose a sensitive field? No Debug/Display/type changes. |

### 7. Dependencies

| Item | Disposition, adversarial question and justification |
|---|---|
| S28 — Dependencies evaluated under policy | **N/A.** Can unreviewed code enter through a new package? No dependency/action/binary addition or upgrade. |
| S29 — Trust category understood | **OK for delta.** Does host probing enlarge privileged runtime code? Shell orchestration remains host-only; the runtime change removes a redundant expression. |
| S30 — cargo-vet decisions updated | **N/A.** Can a new trust decision escape audit? Manifest/lock/dependency graph and vet decisions are unchanged. |

### 8. Threat-model impact

| Item | Disposition, adversarial question and justification |
|---|---|
| S31 — Reconciled with security model | **OK.** Can developer error newly permit a hostile-input panic? The crate-root denies strengthen detection while keeping intentional existing exceptions visible. Capability, memory, boot, fault and DMA boundaries are unchanged. |
| S32 — Model shifts documented or tracked | **N/A — no shift.** Does this introduce a new adversary/principal/defense claim? No. Assertions, historical unmap/SMP limits and existing fatal policy remain explicit rather than silently certified. |

Accepted ADR-0040 governs this consolidation step; ADR-0009/0027/0028/0033 explain MMU frame/flush/direct-map contracts and ADR-0039 the source image build. No ADR is added or rewritten and no architecture choice is being made through lint attributes.

### Architectural principles P1–P12

| Principle | Disposition |
|---|---|
| P1 — No ambient authority | **OK:** no operation/grant bypass; value reuse does not mint a capability. |
| P2 — Smallest defensible TCB | **OK:** no subsystem/dependency growth; guards execute on the host. |
| P3 — Drivers in userspace | **N/A:** no driver placement change. |
| P4 — Capability checks at boundaries | **OK for delta:** existing authorization is unchanged; syscall paths receive no family allowance. |
| P5 — Rust and audited unsafe | **OK for changed reasoning:** explicit 0025 approval above; unrelated HIGH T-038 excluded. |
| P6 — HAL separation | **OK:** deny attributes preserve architecture-neutral HAL and BSP separation. |
| P7 — No proprietary blobs | **OK:** no binary addition; private userland image built from source. |
| P8 — ADR decisions | **OK:** follows Accepted ADR-0040 and existing MMU contracts; no new decision needed. |
| P9 — English artifacts | **OK:** changed prose/code/diagnostics are English. |
| P10 — Mermaid | **N/A:** no diagram change. |
| P11 — Reproducibility | **OK for delta:** pin/lockfile unchanged; private clean target/image probes. Not a reproducibility certification. |
| P12 — Complete declared scope | **OK for first-round review:** concrete source/gates present; fresh second round and final human PR remain pending, tasks In Review. |

### Independent verification

Executed on the repository's pinned `nightly-2026-01-15`, using `/bin/bash` and Python TemporaryDirectory roots with spaces. Logs: `/tmp/tyrne-b21-t032-round1-security-checks/`.

| Check | Observed result |
|---|---|
| Actual `tools/test-ci-gates.sh --hal` | Harness 0; exact host-clippy rejected with exit 101 and clippy::unwrap_used; cleanup observed. |
| Actual `tools/test-ci-gates.sh --bsp` | Harness 0; private 117-byte image; exact kernel-clippy rejected exit 101 with clippy::unwrap_used; cleanup observed. |
| Private root expect mutation, HAL | host-clippy 101, clippy::expect_used. |
| Private root panic mutation, HAL | host-clippy 101, clippy::panic. |
| Private root expect mutation, BSP | kernel-clippy 101, clippy::expect_used. |
| Private root panic mutation, BSP | kernel-clippy 101, clippy::panic. |
| Audit byte comparison | Removing exactly the new 1,502-byte amendment reproduces baseline log byte-for-byte. |
| Exception enumeration | Exactly ten function groups with reasons; zero HAL/syscall/MMU family allowances. |
| Source comparison | Shim, BSP syscall, Cargo.lock, toolchain unchanged; no executable delta after c3f32c8. |
| Working-tree check | HEAD 4f2c38c, tracked working tree clean after verification. |

The four extra mutations used a copied tracked tree with its own CARGO_TARGET_DIR; each file was restored between lint families. The userland build ran only inside that tree. All six negative compiler checks reached the intended lint. These checks establish enforcement in the pinned compiler; the static helper analysis supplies the MMU equivalence argument. Neither alone claims complete absence of panic or UB.

### Supplied evidence inspected and limits

Inspected coordinator logs in `/tmp/tyrne-b21-step5/`: host-test and Miri summaries show 46 HAL + 259 kernel + 58 test-HAL + 3 doctests = **366 passes**, two existing HAL doctests ignored. Miri records existing optimization/provenance warnings, with no UB failure. The debug smoke trace shows the real userspace greeting, userspace exit and completion, two actual EL0 SVC events (the log later repeats them in a summary) and no unexpected fault class. This is inspected supplied execution, not a QEMU/Miri run by this reviewer.

Inspected `hosted-run.json`, `hosted-fastlane.log` and `hosted-kernel.log`: [run 38181326486](https://github.com/HodeTech/Tyrne/actions/runs/38181326486) binds b6572cc to success in all five jobs. HAL and BSP negative steps each record exit 101 with clippy::unwrap_used. Kernel log records the private 117-byte probe image and production 117 → 69 → restored 117-byte sequence. The coordinator also reports exact evidence-only HEAD 4f2c38c all five green at [run 38181458269](https://github.com/HodeTech/Tyrne/actions/runs/38181458269), verified by its read-only metadata query; this reviewer did not independently fetch that later run.

Other broad checks remain coordinator/task-record evidence: fmt, ShellCheck/actionlint; host/default/release/perf Clippy and builds; 11 controlled probe/CLI/isolation cases; 59 QEMU-argv cases; unchanged 117-byte debug image SHA-256 `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`. The controlled fixture's earlier escaped-NUL setup failure was corrected before recorded success; no failed fixture is treated as evidence. I inspected its final JSON outcomes without independently recreating that matrix.

No independent whole-suite positive build/test/Miri, hosted fetch, QEMU, BSP unmap runtime, hardware/SMP, hostile termination cleanup, live protection, whole-tree unsafe or full architecture audit is claimed. Existing assembly/SMP issues are outside this scoped approval. Historical body preservation is evidence of audit discipline, not endorsement of every old claim.

### Verdict and recording follow-up

**Approve Round 1 for `8591ceb..4f2c38c`. No new finding requiring correction. Explicitly approve the changed UNSAFE-2026-0025 unmap argument/SAFETY reasoning as stated above.** All changed-surface checklist items are OK; the unchanged HIGH T-038 invariant remains flagged and excluded without downgrade. The original SMP claim is not endorsed; runtime BSP unmap remains unverified.

Coordinator should publish the full report and index/cross-reference, record the truthful Security-Review trailer and append this actual unsafe approval to 0025 while preserving the historical pending statement. Fresh independent Round 2 and final maintainer PR review remain required. This verdict neither promotes any task to Done nor authorizes merge.

## Round 2 security review

**Approve the scoped T-032 delta at `6e191e2`. No new actionable security finding. Explicit approval of the changed UNSAFE-2026-0025 reasoning is recorded below.**

- **Change:** approved Track B.2-1 step 5 on `development`, `8591ceb..6e191e229d932ea7a3e330cfa55e9e0dc981f4e8`; source `c3f32c8`, actual-SHA reconciliation `b6572cc`, hosted evidence `4f2c38c`, Round 1 reports/approval recording `6e191e2`.
- **Reviewer:** independent Codex security agent `/root/b21_step5_round2_security`, acting on behalf of the maintainer, not impersonating a human approval.
- **Configuration provenance:** parent requested `gpt-6-astra`, high reasoning, fresh context (`fork_turns=none`); these are requested orchestration settings, not independently attested runtime model identity.
- **Separation from code review:** separate agent/context from the paired Round 2 code pass; began an independent security checklist and did not implement this change.
- **Unsafe audit cross-reference:** `docs/audits/unsafe-log.md`, UNSAFE-2026-0025, T-032 amendment and Round 1 recording.
- **Procedure:** `perform-security-review`, `conduct-review`, security master plan and standard; consulted `justify-unsafe`. All eight axes, 32 standard items plus the master-plan allocation item (33 total), and P1–P12.
- **Mutation boundary:** report and evidence only under `/tmp`; no repository/GitHub mutation, commit, branch change or external communication. Coordinator owns canonical report publication, index, cross-reference, trailer and append-only recording. No Done or merge action.

### Scope and reading

Read AGENTS and full CLAUDE; current roadmap including historical banners; numbered ADR corpus in numerical order (0001–0033, 0035–0040; no 0034 file); standards corpus and skill index; full security model/master plan and applicable skills. Bounded follow-up reads recovered truncated passages. Read T-032 and actual negative-probe harness before inspecting the implementation; also read T-037 and the full Track B.2-1 preflight for evidence limits. Read both full Round 1 reports, changed executable files, complete attached exception bodies and relevant callers, actual MMU walker/contracts, cap_unmap/FakeMmu contract, Cargo aliases, image build helper, BSP build script, workflow delta, unsafe entry/history, guide and lifecycle changes, and range commit messages.

The runtime delta is one ignored-argument substitution inside `QemuVirtMmu::unmap`. Remaining Rust changes are lint attributes and comments; the host test harness gains two modes and CI invokes them after positive lints. No syscall body, assembly, capability policy, fatal-fault policy, dependency, toolchain, or public API changes. Git-object comparisons confirm BSP syscall, userspace shim, lockfile and toolchain pin are byte-identical to the baseline; no non-documentation change follows `c3f32c8`.

### 1. Capability correctness

| Item | Disposition and adversarial rationale |
|---|---|
| S01 — Privileged operations require capabilities | **OK for delta.** Can passing the root twice bypass authorization? No operation or entry point is added; unchanged `cap_unmap` resolves the capability and live arena object before MMU entry. |
| S02 — Narrowest sufficient capability | **OK for delta.** Does the reused frame broaden authority? `PhysFrame` is a copied aligned address, not a capability grant. Existing kind-based address-space authorization is unchanged. |
| S03 — Checks precede effects; failures leak no state | **OK for delta.** Can the new operand mutate before checks? No: capability/arena checks and VA alignment still precede the same walker mutation. |
| S04 — Move-only transfer | **N/A.** Could frame copying duplicate transferable authority? No capability representation or transfer changes. |
| S05 — Explicit duplication authority | **N/A.** No new capability-copy path exists to evade its authority requirement. |
| S06 — Atomic revocation | **N/A.** No revocation, CDT or concurrency operation changes that could leave partial revocation. |

Demo task tables retain SEND/RECV for the fixed endpoint; benchmark driver/partner retain their separate SEND/RECV grants. Their IPC calls pass no transferred capability. The default EL0 table receives its console capability, not demo endpoint rights; the benchmark EL0 table is empty. This review does not invent MAP/UNMAP rights that v1 does not have, or certify unrelated existing lifecycle/revocation debt.

### 2. Trust boundaries

| Item | Disposition and adversarial rationale |
|---|---|
| S07 — Validate userspace input | **OK for delta.** Can arbitrary syscall input enter a newly broadly exempt scope? No family allowance exists in syscall; function exceptions retain their original routing and bodies. Independent syscall-module unwrap injection is rejected. |
| S08 — Validate user pointers through mappings | **OK for delta.** Can the placeholder root become a user dereference? The argument is unused on unmap; actual root/pointer computations and copy-user paths are unchanged. |
| S09 — Range-check buffer lengths | **OK for delta.** No buffer/window/length arithmetic or acceptance check changes. |
| S10 — Typed message parsing | **N/A.** No new wire parser or byte reinterpretation could admit malformed input. |
| S11 — IPC transfers only held authority | **OK for delta.** Trusted demo/benchmark bodies and grants are unchanged; none of the lint exceptions adds a transfer or grants foreign rights. |

The new evidence boundary is source-to-Clippy: non-test root functions outside all allowed functions use `black_box(None::<u64>).unwrap()`. Exact `cargo host-clippy` and `cargo kernel-clippy` aliases preserve package/target/warning selection. The harness requires both nonzero exit and `clippy::unwrap_used`; unrelated failure alone and unexpected success cannot pass. It enumerates tracked current files using NUL separators, copies with modes preserved, assigns a private target directory, and uses quoted EXIT cleanup. BSP userland is built only in its private source copy, so an absent shared image cannot mask the intended diagnostic.

Independent executions reached the intended compiler error and removed both disposable roots. The temporary fixture used paths containing spaces and `/bin/bash`. This is a regression guard over trusted source and build tools, not authentication of maliciously forged compiler output or protection against an authorized contributor rewriting both gate and code. Existing cleanup under forced termination is not newly certified.

CI adds fixed commands within the existing required jobs, following positive lints. Trigger, permissions, action pins, secrets and cache policy are unchanged. A successful negative-probe step means the deliberate regression was rejected; it is not a red production workflow.

### 3. Memory safety

| Item | Disposition and adversarial rationale |
|---|---|
| S12 — Unsafe policy | **OK for changed reasoning.** Does the operand change lack justification? Adjacent SAFETY plus append-only amendment explain ignored `pa`, retained contracts and rejected allowance. Actual source SHA and real first approval are recorded. |
| S13 — Invariants hold for callers | **OK for delta; existing HIGH T-038 flagged and excluded.** Can any true-branch success/error path consume the placeholder? All intermediate calls propagate true and do not receive `pa`; the whole true leaf arm ignores it. Unchanged unrelated x2 asm contract remains defective. |
| S14 — No uninitialized exposure | **OK for delta.** The return frame remains masked from the existing L3 descriptor; placeholder contents never enter a descriptor or result. |
| S15 — No use-after-free; justified lifetimes | **OK for delta.** Copying `PhysFrame` neither frees nor acquires ownership nor extends lifetime. Root/table validity and exclusive ownership remain caller obligations. |
| S16 — Aliasing discipline | **OK for delta.** Two value copies create no mutable references; address-space borrow and descriptor access scopes are unchanged. |

**Explicit unsafe approval:** Reviewed the changed `unsafe` call and adjacent SAFETY reasoning in `bsp-qemu-virt/src/mmu.rs:307–333`, particularly `walk_and_install_leaf` at :319–328; I agree with and approve the changed SAFETY reasoning under **UNSAFE-2026-0025**. With literal `unmap = true`, `pa` is unused. Replacing the infallible dummy-zero frame construction/unwrap with already-valid `as_.root` preserves the operation under the existing root/table validity, ownership and lifetime contracts.

The actual helper computes indices from VA, traverses the same L0/L1/L2 tables, returns unchanged typed errors for missing/block mappings, reads the existing L3 descriptor, masks its output PA, clears that leaf slot and returns the descriptor-derived frame. `pa` appears operationally only in the false/map arm, where it is encoded and returned. The new value affects no pointer, descriptor access, allocation, return value or error. Root argument, VA, flags, null provider and true selector are identical. `PhysFrame` is Copy, has no ownership/destructor effect, and the removed constructor always accepts aligned zero. The caller still receives `MapperFlush`; unchanged `cap_unmap` flushes before returning the frame.

Independent historical-byte verification removes exactly the new T-032 amendment plus Round 1 recording (2,571 bytes) and reconstructs the complete baseline audit log byte-for-byte. Thus original fields and prior amendments are preserved. The new amendment accurately identifies `c3f32c8`; it does not silently rewrite the old SMP claim.

**Round 1 recording verified:** Read both complete canonical reports. The security report explicitly Approves the changed call/reasoning for `8591ceb..4f2c38c`, limits its approval to the ignored-argument equivalence, excludes runtime BSP unmap/SMP/T-038, and asks for append-only actual approval recording. The code report explicitly agrees and records the distinct security result. The appended recording at `6e191e2` states those same facts and preserves the earlier pending sentence as history. Its real commit message contains `Audit: UNSAFE-2026-0025` and `Security-Review: b21_step5_round1_security (docs/analysis/reviews/security-reviews/2026-10-12-t032-panic-family-denies.md)`. No fabricated or retroactive implementation-commit approval is present.

**Limits retained:** ordinary smoke exercises boot/map, not this BSP unmap branch. The FakeMmu test asserts returned PA and both flushes; rollback tests concern kernel-layer cleanup, not physical BSP table walking. No runtime BSP unmap test was newly executed. The original SMP-forward claim is expressly not endorsed; T-069 retains ownership. This narrow proof does not certify the whole walker or historical caller-contract debt.

**Existing HIGH T-038 retained:** the userspace shim declares x2 input-only while the unchanged BSP return path writes x2. Both files are byte-preserved. Clean Clippy, host Miri and successful guest boot cannot certify that assembly; this review neither fixes nor downgrades it.

### 4. Kernel-mode discipline

| Item | Disposition and adversarial rationale |
|---|---|
| S17 — No ISR allocation | **OK for delta.** IRQ annotation adds no allocation; its unchanged timer/spurious paths return and unhandled path EOIs before fatal abort. |
| S18 — Bounded loops | **OK for delta.** No attacker-dependent loop is introduced. Existing idle/parking/cooperative loops remain unchanged; no new blanket termination claim. |
| S19 — Minimal critical sections | **OK for delta.** No lock, IRQ mask, borrow lifetime or context-switch sequencing changes. |
| S20 — No new hot-path panic | **OK.** One redundant unwrap is removed; no new runtime panic/expect appears. Exactly ten reasoned function exceptions, with no HAL/syscall/MMU family allow. |
| MP-1 — Allocation exhaustion returns typed errors | **OK for delta.** No new allocation or conversion of attacker-driven failure to expect. Existing trusted setup exceptions stay scoped; MMU error paths are unchanged. |

#### Full exception inventory

| Function | Allowed family members | Classification and boundary |
|---|---|---|
| `main::kernel_main_high` | expect, panic | One-shot trusted static image/capacity/object setup before scheduler start. |
| `main::idle_entry` | expect | Post-start trusted current-task invariant; accurately not described as initialization. |
| `main::task_a` | expect, panic | Trusted one-round kernel demo and fixed IPC protocol. |
| `main::task_b` | expect, panic | Trusted matching receiver/reply demo protocol. |
| `perf_bench::run` | expect, panic | One-shot trusted measurement-build setup and publish-before-start sequence. |
| `perf_bench::driver_yield` | expect | Trusted current-task invariant after scheduler start. |
| `perf_bench::driver_send` | expect | Static SEND capability and fixed ping-pong protocol. |
| `perf_bench::partner_recv` | expect | Static RECV capability and fixed matching protocol. |
| `exceptions::irq_entry` | panic | Existing deliberate fatal unhandled-IRQ abort after EOI. |
| `exceptions::panic_entry` | panic | Existing fatal unhandled-exception policy. |

All ten groups have reasons and attach to functions; none permits unwrap. Full bodies, multiline attributes and variant selection were inspected. Fatal exception handling is hostile-event reachable under the existing policy; approval of its annotation is not a claim of full task-fault containment and does not allocate that unchanged debt to a future phase. Future changes inside these allowed functions remain review-sensitive. Assertions are outside these three lints; no panic-free-kernel claim follows.

### 5. Cryptography

| Item | Disposition and adversarial rationale |
|---|---|
| S21 — Reviewed primitives | **N/A.** No cryptographic primitive is introduced or changed. |
| S22 — Keys absent from diagnostics | **N/A.** No key handling or key-bearing diagnostic is added. |
| S23 — Constant-time comparison | **N/A.** Public diagnostic matching is not a secret comparison; no cryptographic timing path changes. |
| S24 — Acceptable randomness | **N/A.** No security RNG change. Host mktemp creates an exclusive disposable directory, not a cryptographic token. |
| S25 — Nonce/IV/salt discipline | **N/A.** No such state or operation changes. |

### 6. Secrets and logging

| Item | Disposition and adversarial rationale |
|---|---|
| S26 — No sensitive diagnostic leakage | **OK for delta.** Runtime diagnostics are unchanged; new output is fixed test status and compiler/build output, with no new secret argument. |
| S27 — Redacted sensitive Debug | **N/A.** No new type/formatter could reveal capability identity or key fields. |

### 7. Dependencies

| Item | Disposition and adversarial rationale |
|---|---|
| S28 — Dependencies evaluated under policy | **N/A.** No crate, action or binary dependency is added/upgraded. |
| S29 — Trust category understood | **OK for delta.** Additional probing is host-only; no unreviewed runtime component enters the TCB. |
| S30 — cargo-vet decisions recorded | **N/A.** No dependency graph/trust decision changes; lockfile preserved. |

### 8. Threat-model impact

| Item | Disposition and adversarial rationale |
|---|---|
| S31 — Reconciled with security model | **OK.** The change improves detection of developer error on hostile-input paths while keeping intentional exceptions explicit; runtime authority, user-memory and hardware boundaries remain unchanged. |
| S32 — Model changes recorded/tracked | **N/A — no model shift.** No new adversary/principal or defense claim is introduced. Existing fatal handling, SMP and assembly limitations remain explicit. |

Accepted ADR-0040 governs the consolidation workflow; existing MMU/direct-map/image ADRs govern the preserved implementation contracts. No architecture or standard policy is changed through attributes, and no new ADR is required for the ignored-value substitution.

### Architectural principles P1–P12

| Principle | Disposition |
|---|---|
| P1 — No ambient authority | **OK:** no authority surface added or bypassed. |
| P2 — Small defensible TCB | **OK:** host probes add no privileged runtime subsystem. |
| P3 — Userspace drivers | **N/A:** placement unchanged. |
| P4 — Capability boundaries | **OK for delta:** checks unchanged; syscall module retains lint enforcement. |
| P5 — Rust/audited unsafe | **OK for changed reasoning:** explicit 0025 approval; existing T-038 excluded. |
| P6 — HAL separation | **OK:** crate-root enforcement preserves the abstraction boundary. |
| P7 — No proprietary blobs | **OK:** no committed binary; private image built from source. |
| P8 — ADR governance | **OK:** existing Accepted policy implemented, history preserved. |
| P9 — English | **OK:** changed repository prose/code/diagnostics English. |
| P10 — Mermaid | **N/A:** no diagram needed or changed. |
| P11 — Reproducibility | **OK for delta:** pin/lock preserved and independent private image matches recorded hash; no whole-kernel reproducibility certification. |
| P12 — Complete scoped work | **OK for this review:** concrete implementation/evidence exists; coordinator must record Round 2 and retain final human PR/Done boundaries. |

### Independent execution and evidence

Independent execution used the pinned nightly, `/bin/bash`, Python `TemporaryDirectory` paths with spaces, private source copies and private CARGO_TARGET_DIR. Script `/tmp/tyrne-b21-r2-security-check.py`; logs and results `/tmp/tyrne-b21-t032-round2-security-checks/`.

| Check | Observed outcome |
|---|---|
| Actual production `tools/test-ci-gates.sh --hal` | Harness 0; real host Clippy 101, intended `clippy::unwrap_used`; private cleanup confirmed. |
| Actual production `tools/test-ci-gates.sh --bsp` | Harness 0; real kernel Clippy 101, intended `clippy::unwrap_used`; private image build and cleanup confirmed. |
| Fresh private debug userland build | Exit 0; 117 bytes, SHA-256 `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88`. |
| Private positive `cargo host-clippy` / `cargo kernel-clippy` | Both exit 0. |
| Inject sibling non-test unwrap in BSP syscall module | Kernel Clippy 101, `clippy::unwrap_used`. |
| Inject sibling non-test unwrap in MMU module | Kernel Clippy 101, `clippy::unwrap_used`. |
| Inject sibling non-test expect in exceptions module | Kernel Clippy 101, `clippy::expect_used`; fatal function exceptions do not exempt module siblings. |
| Inject sibling non-test panic in perf module with feature enabled | Feature-selected Clippy 101, `clippy::panic`; benchmark allowances do not exempt module siblings. |
| Mutation isolation | Each private file restored between cases; outer TemporaryDirectory removed. Watched shared HAL/BSP/MMU/syscall sources, hello.bin and debug kernel ELF SHA-256 unchanged. |
| Historical audit and source comparison | Two new blocks removed reproduce baseline log exactly; syscall/shim/pin/lock unchanged, no non-doc delta after source commit. |
| Final repository check | Exact reviewed HEAD and clean tracked working tree. |

The private lint mutations directly challenge exception scope instead of merely restating the implementation. No failed fixture is counted as success. No broad suite was rerun after these targeted checks because the source delta and uncertainty did not warrant it.

#### Supplied evidence inspected versus reported

Inspected coordinator-downloaded `hosted-run.json`, `hosted-fastlane.log`, `hosted-kernel.log` under `/tmp/tyrne-b21-step5/`. Metadata binds completed success to exact `b6572cc65857b99f3ac3661b99cea809a7b12e88`, with all five jobs successful in [run 38181326486](https://github.com/HodeTech/Tyrne/actions/runs/38181326486). Supplied fast-lane line 202 and kernel line 214 show the intended HAL/BSP unwrap rejection at exit 101; kernel line 213 shows its private 117-byte image. Production image sequence is 117 → 69 → restored 117 bytes (lines 173/244/276). Fast-lane summaries establish 366 debug and 356 release passes plus two ignored HAL doctests. This is inspection of supplied metadata/logs, not independent GitHub retrieval.

Coordinator reports additional all-five-green docs-only `4f2c38c` [run 38181458269](https://github.com/HodeTech/Tyrne/actions/runs/38181458269). During report finalization the coordinator also reported a read-only `gh run list` metadata result binding exact reviewed `6e191e2` to all five successful jobs in [run 38181945962](https://github.com/HodeTech/Tyrne/actions/runs/38181945962). These two later runs are coordinator-retrieved metadata attribution, not independent retrieval by this reviewer. All non-documentation files are unchanged after the detailed hosted source/evidence tip.

Other broad validation remains coordinator/task/first-review attribution: fmt/ShellCheck/actionlint; default/release/perf builds and Clippy; 366 host and Miri passes, existing Miri warnings and two ignored doctests; real debug greeting/exit/completion/two SVCs/no unexpected fault; eleven controlled probe/CLI cases and 59 QEMU argv cases. The full R1 reports document independent unwrap-deny-removal controls and root expect/panic checks in both crates. This reviewer read those reports but did not independently repeat those particular controls or the broad host/Miri/QEMU suite. Parent's corrected escaped-NUL fixture failure is not accepted as passing evidence.

No new guest smoke, BSP unmap runtime, hardware/SMP, forced-termination cleanup, live protection, whole-tree unsafe, or assembly correctness certification is claimed. Successful ordinary boot, host FakeMmu and Miri evidence cannot establish those properties.

### Verdict

**Approve Round 2 SECURITY for `8591ceb..6e191e2`, with no new actionable finding. Explicitly approve the changed UNSAFE-2026-0025 unmap argument and adjacent SAFETY reasoning as scoped above. The actual Round 1 approval recording and trailer accurately match the full first-round report.**

All 33 checklist items and P1–P12 are dispositioned. Unchanged HIGH T-038 stays flagged/excluded without downgrade; the original SMP-forward claim is not endorsed and runtime BSP unmap remains unverified. Coordinator should publish this full review and record its actual approval append-only. T-032 remains In Review for the final maintainer PR; this verdict does not promote Done or authorize merge.
