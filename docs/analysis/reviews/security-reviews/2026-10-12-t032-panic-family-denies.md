# Security review 2026-10-12 — T-032 panic-family denies

- **Change:** T-032 on `development`, `8591ceb..4f2c38c`.
- **Reviewer:** fresh independent `b21_step5_round1_security`, acting on behalf of @cemililik; `gpt-6-astra` / high requested, fresh context.
- **Separation from code review:** independent agent with an empty security checklist; implementation and paired code context not inherited.
- **Unsafe audit cross-reference:** UNSAFE-2026-0025, the T-032 unused-argument amendment.
- **Paired code review:** [code-review artifact](../code-reviews/2026-10-12-t032-panic-family-denies.md).

> **Current reconciliation:** Round 1 security Approve, no new finding; changed UNSAFE-2026-0025 reasoning explicitly approved. No new BSP unmap runtime or SMP verification is claimed; existing HIGH T-038 remains excluded. Paired Round 1 code review also Approve; second fresh round and final maintainer PR review remain pending. The coordinator records the actual approval append-only and in this follow-up's trailer; no retroactive implementation-commit trailer is claimed.

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
