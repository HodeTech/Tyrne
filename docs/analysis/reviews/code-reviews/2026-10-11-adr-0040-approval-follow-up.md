# Approval review 2026-10-11 — ADR-0040 follow-up

- **Reviewer:** `b21_adr0040_approval_followup`, independent agent context; review performed read-only, then explicitly authorised to write this artifact and its index row.
- **Procedure:** [conduct-approval-review](../../../../.agents/skills/conduct-approval-review/SKILL.md).
- **Reviewed range:** `8d6fab5..41679c1`; HEAD `41679c1bc2f21033e1e1b43472043da3c077ff0c`, plus inspected working corrections to ADR-0040, `current.md`, T-049 and T-075. Source remains unchanged.
- **Snapshot:** the initial final-verdict ADR SHA-256 was `e435c874e04a30a060d40f03e979e620b5dbee177e8b4dfe5bead878b198d6e7`. A subsequent inspected lifecycle-wording cleanup, still at **Proposed**, yields `c81802e988fd7789e750324c2ba0c3f82461b002ab7be07ea11d0192954b69f5`.
- **Background:** [Track B.2-1 preflight](2026-10-11-phase-b2-track1-preflight.md), the maintainer-supplied M1/L1–L4/OQ1–OQ2 report, and the settled decision that all of B.2 gates both C and D; C/D may overlap afterward.

## Verdict

**✅ ADR-0040 is ready for Acceptance.** The supplied findings are resolved or corrected against source evidence. Two factual issues identified during this pass were fixed and rechecked. The associated Phase B.2 plan corrections are **✅ ready**. Acceptance remains a separate commit; this artifact does not claim that it has occurred.

The exact workspace Miri and coverage commands still fail on Apple Silicon through the documented T-037 defect. These reproduced baseline failures are neither clean passes nor regressions from this documentation change. No task implementation, Done promotion, hosted verification or phase closure is certified.

## Verification audit

V1–V12 were written and sent to the parent before walking the diff or running gates. File:line citations below refer to the reviewed snapshot; `ADR` means [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md).

| Item | Result and evidence |
|------|---------------------|
| V1 — Scope and unchanged source | ✅ The committed range changes only ADR-0040 and `phase-b2.md`; working corrections are Markdown only. Last source commit remains `3c19278794b177260e9c0715a56bee33b76b7b91`, dated 2026-06-01. ADR:13 now anchors its claim to baseline `8d6fab5`. |
| V2 — M1 plan targets | ✅ `phase-b2.md:84–85,179,268` target B.2 active / C next and gated. ADR:46 explicitly includes those targets. |
| V3 — L1 historical preservation | ✅ ADR:46,114 distinguish live pointers from preserved history; `phase-b.md:299` supersedes its historical closure statement. |
| V4 — L2 ledger facts | ✅ Corrected during review: C currently uses 0040–0044, D 0042–0046, E 0047–0052. ADR:49 distinguishes current collisions from historical “was” references. |
| V5 — L3 historical placeholder | ✅ ADR:11 describes PR #46 historically. `git show 400dec0:docs/roadmap/phases/phase-b2.md` confirms the former unallocated-placeholder wording; merge `400dec0` is dated 2026-07-16. |
| V6 — L4/OQ2 gating | ✅ ADR:44,115 explain D's direct dependency on shared foundations. The entire B.2 exit bar gates C and D; subsequent overlap does not weaken it. |
| V7 — OQ1 kickoff labels | ✅ ADR:17 and task-index instructions distinguish prepared Ready scopes and selected Active focus from implementation authorization. Actual statuses are 36 Ready / 10 Draft; none is In Progress or Done. |
| V8 — Counts and accounting | ✅ All 46 files, T-030–T-075, match index statuses. Plan: 18 HIGH + 43 MEDIUM + 66 LOW + 14 INFO = 141; 71 polish. ADR:45 preserves optional T-036/T-056 and evidenced-deferral rules. |
| V9 — Baseline claims | ✅ Debug 366, release 356 and subset Miri reproduced. Coverage label corrected to 96.31% regions / 95.87% lines. Exact workspace failures are recorded separately below. |
| V10 — Source and CI premises | ✅ Arch-only cfg remains in hello, its build script and syscall wrappers; `console_write` still uses input-only x2. Hello ignores console rejection and exits. CI still lacks smoke/release execution. |
| V11 — Track B.2-1 policy | ✅ ADR:56–63 agrees with T-035/T-036 and the eight-step index sequence. Read-only GitHub inspection confirms four app-15368-bound required checks, strict/linear/conversation enabled, force/delete disabled, and no rulesets. |
| V12 — Structure and references | ✅ MADR sections, alternatives, dependencies, consequences and index exist. All 33 local ADR link occurrences resolve (22 unique targets); plan/index local links and referenced anchors resolve. |

The explicit ARM runner remains a standard public-repository runner in [GitHub's runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), independently checked during this review.

## New findings

### High — resolved

**Coverage metric mislabeling.** ADR:13 and three live references called 96.31% “lines.” The reproduced report identifies that as region coverage; line coverage is 95.87%. Corrected and verified in ADR-0040, `current.md:7`, T-049:34 and T-075:20. High classification follows the approval skill's rule for inaccurate numeric claims; this was documentation error, not coverage regression.

### Medium

None remaining. Supplied M1 is resolved.

### Low — resolved

**The L2 correction incorrectly included a current Phase E collision.** The supplied report mistook historical ledger numbers for current slots. The final ADR correctly identifies the C/D collision and keeps downstream E–I resequencing under T-054. Supplied L1, L3 and L4 are resolved; no additional actionable finding remains.

### Open questions

None. OQ1 is explicitly explained. OQ2 follows the maintainer's settled whole-phase gate for both C and D.

## Per-ADR acceptance audit

| `write-adr` criterion | Result |
|-----------------------|--------|
| Correct numbered file | ✅ ADR-0040 exists at the expected path. |
| Complete MADR content | ✅ Context, drivers, outcome, consequences, references and alternatives contain substantive content. |
| At least two credible options | ✅ Five phase-wide options plus policy alternatives. |
| Simulation | ✅ Governance exemption at ADR:74–76. |
| Simulation-to-verification mapping | ✅ Not applicable to this governance ADR. |
| Grounded dependency chain | ✅ ADR:78–90 references real task slots and distinguishes later realization from Acceptance. |
| Positive and negative consequences | ✅ ADR:94–110 records benefits, costs and mitigations. |
| ADR index entry | ✅ `docs/decisions/README.md:70`, currently Proposed. |
| Prior Accepted ADR consistency | ✅ ADR-0013's additive bridge extension has a dated rider; outcome reversal still requires supersession. |
| Separate Propose and Accept | ✅ ADR remains Proposed; Acceptance will be a separate commit. |

No task is being promoted. Task implementation AC/DoD checkboxes remain unfulfilled and outside this promotion verdict.

## Gates and counts

Executed locally on Apple Silicon with **`nightly-2026-01-15`**:

| Command | Result |
|---------|--------|
| `cargo +nightly-2026-01-15 fmt --all -- --check` | PASS |
| `cargo +nightly-2026-01-15 host-clippy` | PASS |
| `cargo +nightly-2026-01-15 kernel-clippy` | PASS |
| `cargo +nightly-2026-01-15 host-test` | PASS: 46 HAL + 259 kernel + 58 test-HAL + 3 doctests = **366** |
| `cargo +nightly-2026-01-15 kernel-build` | PASS |
| `cargo +nightly-2026-01-15 miri test --workspace --exclude tyrne-bsp-qemu-virt` | **FAIL, exit 1:** hello duplicate `panic_impl`, E0152; documented T-037 baseline |
| `cargo +nightly-2026-01-15 llvm-cov --workspace --exclude tyrne-bsp-qemu-virt --summary-only` | **FAIL, exit 101:** same documented T-037 defect |
| `cargo +nightly-2026-01-15 test --release` | PASS: 46 + 249 + 58 + 3 = **356**; three existing unused-import warnings |
| `cargo +nightly-2026-01-15 miri test -p tyrne-hal -p tyrne-kernel -p tyrne-test-hal` | PASS: **366**, no UB reported; existing provenance/optimization warnings |
| `cargo +nightly-2026-01-15 llvm-cov --workspace --exclude tyrne-bsp-qemu-virt --exclude tyrne-user --exclude tyrne-userland-hello --summary-only` | PASS: **96.31% regions**, **95.87% lines**, **93.13% functions** |
| `tools/smoke.sh --int --timeout 5` | PASS: userspace greeting, task exit/completion, two SVCs, no panic/fault |

Debug/release/subset-Miri totals exclude two existing ignored HAL doctests. Coverage was rechecked against the column header: 14,039 regions / 518 missed; 8,346 lines / 345 missed. The historical stable-toolchain claim was not independently rerun in this pinned-nightly pass.

## Process notes

The reviewer read AGENTS, CLAUDE, the numbered ADR corpus in order, standards, applicable skills, the supplied report and prior preflight. Source, gates and live read-only policy were checked independently. No source change, commit, branch change or external mutation was performed. Unsafe audit amendments and implementation security review are not applicable to this documentation-only diff; future source changes retain their distinct security-review obligations.

The follow-up lifecycle wording was inspected while ADR-0040 remained Proposed: kickoff labels are historical, the policy heading and benefit no longer imply a permanent proposal, and policy activation explicitly requires maintainer Acceptance. These changes do not alter the decision.

The separate Acceptance commit still needs to synchronize ADR/index status, `current.md` pending/next-step text, task-index pending-policy instructions, and T-035/T-036 live decision wording and Ready statuses with their index rows. Preserve dated Proposed-era review histories. These updates record the authorized decision; they do not certify implementation, hosted runs, Done status or B.2 closure.
