# Security review 2026-10-12 — T-035 CI hygiene tail

- **Change:** approved Track B.2-1 step8, `69ac515..e873995`; later T-036 integration correction recorded below.
- **Round1 reviewers:** fresh `b21_step8_round1_code` (`gpt-6.1-sol` / high requested) and distinct `b21_step8_round1_security` (`gpt-6-astra` / high requested), empty inherited context. Configuration provenance, not runtime identity attestation.
- **Paired artifact:** [code review](../code-reviews/2026-10-12-t035-ci-hygiene-tail.md).

> **Current reconciliation:** R1 code Request changes for verified Medium R1-CODE-01, an inherited T-036 compiler-diagnostic race; scoped T-035 security Approve with no new actionable finding. Coordinator read both full reports, verified the finding and corrected it locally with permanent offline controls. Fresh R2 and corrected hosted proof remain pending. Exact-source first performance artifact and all seven CI jobs are green at e873995. Existing HIGH T-038 remains excluded and undowngraded. Final maintainer PR and merge-dependent evidence remain pending; tasks stay In Review.

## Round1 — security

# Security review 2026-10-12 — T-035 CI hygiene tail, Round 1

- **Change:** `development`, immutable base `69ac515393f8f20ff0a11587a309182388bcde51` through tip `e8739957ea0a2ceabb33fa7519cadb1a1d2be57e`.
- **Reviewer:** independent Codex agent `/root/b21_step8_round1_security`, acting for the maintainer; this identifies the actual reviewer and does not represent a maintainer sign-off.
- **Date:** 2026-10-12, Europe/Istanbul.
- **Separation from code review:** fresh security context and checklist, distinct from implementation and the paired `/root/b21_step8_round1_code` pass; no ordinary code review performed by this reviewer. The complete report is delivered to the paired reviewer before its final verdict.
- **Procedure:** `perform-security-review` and `conduct-review`, the complete security master plan, eight axes, all 32 standard items plus allocation exhaustion (33 explicit dispositions), and P1–P12.
- **Unsafe audit cross-reference:** N/A for this delta: no production Rust, assembly, unsafe body, compilation predicate, safety argument or audit-log change. Existing HIGH T-038 remains excluded, unchanged and undowngraded.
- **Security verdict:** **Approve the scoped T-035 security delta.** No new actionable T-035 security finding established. This does not approve overall integration closure: the inherited T-036 diagnostic race reported below remains an independently corroborated integration hold for the paired code review and subsequent fresh Round 2.

### Scope, prerequisites and provenance

The security trigger is the new local branch-protection administrative authorization boundary. Scope includes the fixed repository/branch policy definition, REST/GraphQL reads, local apply restrictions, remote check-run evidence, narrow mutation and read-back, transport diagnostics, offline tests, the informational performance workflow, harness provenance and associated documentation.

Read AGENTS, full CLAUDE, active roadmap, numbered ADR corpus (0001–0033 and 0035–0040; no 0034 file), all 15 substantive standards, both applicable skills, full security master plan and security model. Recovered truncated prerequisite reads in smaller ranges. Reviewed prior T-034 security findings and corrected Round 2 failure-propagation analysis, T-037's target-boundary review and its explicit T-038 exclusion, and current T-035/T-036 scope/evidence records. ADR-0040's Accepted D1–D4 govern this implementation; this is not a re-audit of historical kernel implementations.

No repository writes, branch changes, commits, live policy operations or live administrative apply—including no-op apply—were performed by this reviewer. All executable experiments used a private `git archive` of the immutable tip at `/tmp/tyrne-b21-t035-security-r1`; all additional files are under `/tmp`. The transport failure tests mock subprocess execution. No fixture can reach the actual GitHub API. Official public GitHub documentation was read to verify API/shell semantics. Parent-downloaded hosted artifacts and parent-produced live export/no-op logs were inspected locally and remain attributed to the parent.

## 1. Capability correctness

| Item | Adversarial question | Outcome and justification |
|---|---|---|
| S01 — Every privileged operation requires authority | Can an unprivileged caller change main protection? | **OK for host boundary; N/A to runtime capabilities.** The sole mutation requires explicit `apply` and GitHub repository Administration write authority; export/check contain only policy reads, and no new kernel operation exists. |
| S02 — Narrowest sufficient authority | Can supplied input redirect or widen the administrative operation? | **OK.** Hostname, repository, main branch and endpoint are fixed; only status-check protection is PATCHed, and CI remains `contents: read` with nonpersisted checkout credentials and no admin secret. |
| S03 — Checks precede observable privileged effects | Can malformed policy, stale state or forged proof reach PATCH? | **OK.** Full local validation, expected-current equality, add-only comparison, full-SHA/app-bound green proof and a final full live comparison precede mutation; independent negative cases reached zero fake writes. |
| S04 — Transfer is move-only | Can this change clone a runtime capability during transfer? | **N/A.** No runtime capability representation, transfer or ownership operation changes. |
| S05 — Duplication needs explicit authority | Can the tool mint duplicate capability rights? | **N/A.** No capability duplication operation or right is introduced; GitHub authentication stays with the maintainer's existing local CLI. |
| S06 — Revocation is atomic | Can a capability be half-revoked? | **N/A.** No runtime revocation changes; REST policy reconciliation is deliberately non-atomic and is analyzed separately below. |

The administrative tool is a guard against unsafe reconciliation, not a sandbox against someone already controlling the maintainer's host, CLI executable or admin token. CI environment checks refuse even false-valued `CI`, `GITHUB_ACTIONS`, `GITHUB_RUN_ID` or `RUNNER_ENVIRONMENT` markers before API access. A privileged host operator can use GitHub directly; environment-variable refusal does not claim to remove that authority.

## 2. Trust boundaries

| Item | Adversarial question | Outcome and justification |
|---|---|---|
| S07 — Validate userspace inputs before kernel use | Can malformed syscall input gain a new privileged route? | **N/A to runtime; OK for changed host analog.** No syscall parser changes; JSON definitions and remote policy are validated before administrative mutation. |
| S08 — User pointers require validated mappings | Can supplied addresses be dereferenced by the kernel? | **N/A.** No user pointer, mapping or privileged memory-access path changes. |
| S09 — Range-check user buffer lengths | Can an oversized user length bypass mapping bounds? | **N/A.** No user buffer or length consumer changes; remote check evidence separately rejects incomplete or over-100 result sets. |
| S10 — Typed parsing of messages | Can unstructured input silently replace policy? | **OK for host analog; N/A to IPC.** Duplicate JSON object keys, unknown fields, missing required fields and wrong exact types are rejected; status contexts must agree with unique app-bound checks. |
| S11 — IPC cannot transfer excess authority | Can the sender grant rights it never held? | **N/A.** No IPC operation, sender/receiver authority or transfer behavior changes. |

**Administrative input boundary — OK.** The definition preserves all nine REST booleans, review flags/count, null restrictions, strict checking and every existing context/app pair. Unknown fields fail closed rather than being discarded. URL metadata is the only general response-only metadata removed and must be a string. Omitted REST restrictions normalize to null only within the explicitly supported baseline, while the GraphQL rule separately requires no push restriction or actors. GraphQL-only `requiresApprovingReviews:true`, deployment-off/empty environments and four zero actor counts are captured. Rendering the supported GraphQL rule before equality avoids Python's bool/int equivalence. New/inherited rulesets cause refusal; GitHub documents `includes_parents` defaulting to true for this endpoint. [Repository rules API](https://docs.github.com/en/rest/repos/rules#get-all-repository-rulesets).

**Remote proof boundary — OK.** `--verified-sha` must be a full lowercase 40-character SHA, including on a no-op. Each new check requires exactly one returned name match, the same full head SHA, completed/success and an exactly typed matching app ID. An explicit total/list-length agreement and 100-run ceiling reject truncation rather than guessing across pages; duplicate matches reject even if one succeeds. Existing checks cannot be removed or rebound. The proof is for the maintainer-selected commit; it is not a claim that an arbitrary caller-supplied SHA is the current branch tip or that app identity attests to trusted workflow content.

**Transport boundary — OK.** `gh` receives an argv list, fixed `--hostname github.com`, version header and method, with JSON through stdin; no shell interpolation, input-driven endpoint or token argument is added. Export/check's GraphQL POST executes a constant `query`, not a mutation. The only policy write is PATCH to `/required_status_checks` with strict/checks; no whole-protection replacement, deletion, ruleset change or rollback exists. Official endpoint documentation identifies the narrow PATCH and its Administration-write permission. [Status-check protection API](https://docs.github.com/en/rest/branches/branch-protection#update-status-check-protection).

**Concurrent administrator boundary — documented limitation, not atomicity proof.** The complete REST/GraphQL/ruleset policy is re-read immediately before PATCH and again afterward. A concurrent change after the last read can still be overwritten within the status-check object, and separate REST/GraphQL reads are not an atomic snapshot. Read-back may detect divergence but cannot detect a concurrent check that was added and overwritten in the race window. `docs/guides/ci.md:192` explicitly states the lack of documented atomic conditional update, requires administrative coordination, and forbids automatic rollback. This limitation is accepted within the requested local maintenance model; no CAS guarantee is claimed or inferred.

**Performance result boundary — OK for informational reporting.** Explicit job-level Bash supplies pipefail, so `tee` cannot make a failed harness green. GitHub documents this explicit-shell behavior. [Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_iddefaultsrun). The report path must match the fixed date/context shape before copying. The job has no PR trigger, required-check registration, timing threshold or `continue-on-error`. A failed measurement is a visibly failed informational workflow. The inherited harness accepts its documented minimum-valid fraction and reports requested/valid/failed counts; a partial sample set is not mislabeled 20 successful runs. Guest timing text is diagnostic input from the source-built guest, not cryptographic attestation against hostile source/QEMU/compiler.

## 3. Memory safety

| Item | Adversarial question | Outcome and justification |
|---|---|---|
| S12 — New unsafe meets policy | Can new unsafe escape a SAFETY/audit review? | **N/A.** No production Rust/assembly or unsafe region changes; Python and shell are host tooling. |
| S13 — Safety invariants hold for all callers | Can passing CI be mistaken for proof of the known assembly contract? | **Flagged — existing HIGH T-038, excluded and unchanged.** `console_write` still declares x2 input-only while BSP return handling overwrites saved x2; this security approval does not endorse that invariant. |
| S14 — No uninitialized memory exposed | Can newly exposed buffers disclose uninitialized memory? | **N/A to runtime; OK for delta.** No kernel buffer initialization or memory-dump API changes; new metadata is public host/run provenance. |
| S15 — No use-after-free | Can new raw-pointer lifetime changes create stale access? | **N/A.** No raw pointer, allocation lifetime or runtime ownership change. |
| S16 — No mutable aliasing violations | Can the change create concurrent mutable references? | **N/A.** No Rust references, aliasing operation or synchronization contract changes. |

Read-only source inspection at the immutable tip confirms `userland/tyrne-user/src/lib.rs:107` has `in("x2") buf.len() as u64`, while `bsp-qemu-virt/src/syscall.rs:224` writes `f.x2_x3[0] = r.payload[1]`. T-038 remains HIGH. No unsafe audit entry or new unsafe approval is warranted for T-035, and existing tests do not resolve the mismatch.

## 4. Kernel-mode discipline

| Item | Adversarial question | Outcome and justification |
|---|---|---|
| S17 — No ISR allocation | Can an interrupt force a newly allocating path? | **N/A.** No ISR or runtime allocation path changes. |
| S18 — No unbounded kernel loops | Can an attacker newly stall the kernel? | **N/A to kernel delta.** Kernel loops are unchanged; performance measurement retains the per-run watchdog and the workflow adds a ten-minute outer bound. |
| S19 — Minimize critical sections | Can a caller extend lock/IRQ-disabled time? | **N/A.** No scheduler state, lock or critical-section change. |
| S20 — No new hot-path kernel panic | Can a new input cause a runtime panic? | **OK for delta.** New error paths are host validation/process failures; no shipped kernel hot path changes. |
| MP-1 — Typed allocation-exhaustion errors | Can allocation exhaustion now panic the kernel? | **N/A.** No kernel allocator or exhaustion behavior changes; host resource failures do not imply kernel safety. |

The admin tool bounds each `gh` call to 30 seconds and does not retry writes. It is not a general defense against arbitrarily huge local files or a compromised upstream service exhausting Python's memory. Those are trusted-maintainer-host availability assumptions, not new kernel resource exposure. The performance job runs 20 iterations with five-second guest watchdogs and a ten-minute workflow bound; cancellation/runner loss may prevent artifact delivery despite `always()`.

## 5. Cryptography

| Item | Adversarial question | Outcome and justification |
|---|---|---|
| S21 — Reviewed primitives, no homemade crypto | Can a novel algorithm forge authority? | **N/A.** No cryptographic primitive or protocol is introduced; HTTPS/authentication remains GitHub CLI infrastructure. |
| S22 — Keys absent from logs/errors/Debug | Can API failure expose authentication material? | **OK for credential handling.** `gh` stderr is captured and never echoed; independent failed-process and timeout fixtures kept a secret sentinel out of stdout/stderr. |
| S23 — Constant-time comparisons where relevant | Can comparison timing disclose a secret? | **N/A.** Policy names, booleans, app IDs and source SHAs are public metadata, not secret values. |
| S24 — Acceptable randomness | Can weak random generation mint predictable secrets? | **N/A.** No random token, key or nonce generation changes. |
| S25 — Correct nonce/IV/salt contract | Can a replay misuse newly introduced nonce state? | **N/A.** No encryption, nonce, IV or salt state is introduced. |

Full source SHAs bind evidence to a commit; they are not signatures or a guarantee that the selected runner/toolchain is uncompromised.

## 6. Secrets and logging

| Item | Adversarial question | Outcome and justification |
|---|---|---|
| S26 — No secrets in diagnostics | Can command errors or artifact selection collect credentials? | **OK for reviewed boundary.** Generic nonzero `gh` failures suppress stderr; no token is passed in argv; workflow artifacts select only the dedicated runner-temp evidence directory, with no environment/home/cache dump. |
| S27 — Sensitive Debug redacts or is absent | Can a formatter print key/capability internals? | **N/A.** No Rust Debug implementation or sensitive type is introduced; the script does not format captured credential-bearing stderr. |

The workflow records source SHA, run/attempt, UTC interval, Rust/toolchain, QEMU, host details and harness output. The inspected hosted artifact contains those public diagnostic fields and the generated report. Artifact upload runs on success/failure, errors when evidence is missing and retains 14 days; it does not grant repo write permission. No admin secret is introduced into CI. A malicious checkout/build process could print data already available to its runner; read-only token/no admin secret and checkout credential nonpersistence are the relevant controls, not log filtering of arbitrary hostile programs.

## 7. Dependencies

| Item | Adversarial question | Outcome and justification |
|---|---|---|
| S28 — New dependencies evaluated under policy | Can new third-party code silently enter the kernel? | **OK for host additions; N/A to Cargo additions.** Scripts use Python stdlib and existing shell/Rust/QEMU tooling; actions use full immutable SHAs and no manifest/lockfile dependency is added. |
| S29 — Trust category understood | Can build tooling become runtime TCB code? | **OK.** `gh`, Python, Bash, QEMU and Actions remain maintainer/CI tools; none is linked into the guest kernel. |
| S30 — cargo-vet trust decisions updated | Can a new crate bypass trust review? | **N/A.** Cargo graph/lockfile and cargo-vet decisions are unchanged. |

Checkout `11bd71901bbe5b1630ceea73d27597364c9af683`, cache `5a3ec84eff668545956fd18022155c47e93e2684`, and upload `cf430e030ddbb5b0abf93d22962f4752f3646cd9` match already-reviewed project pins. This pass verifies the immutable configuration, not a fresh full audit of bundled action JavaScript; prior T-034 security review records official upload-tag/source provenance. Rust remains pinned to nightly-2026-01-15. Performance cache keys and restore prefixes include OS, architecture, performance namespace and toolchain, preventing accidental cross-architecture cache sharing. Normal Cargo/source/compiler/cache trust remains; this is not a hermetic cache attestation scheme. Ubuntu and apt QEMU roll, so their observed versions are recorded rather than claimed immutable. Userland and kernel are built in the required order from source; no proprietary blob is added.

## 8. Threat-model impact

| Item | Adversarial question | Outcome and justification |
|---|---|---|
| S31 — Reconciled with security-model.md | Can new authority or misleading assurance weaken a documented boundary? | **OK for T-035 delta.** The new admin surface is local, fixed-target and additive; CI remains unprivileged, and performance output is explicitly informational. The inherited T-036 reliability hold below remains visible. |
| S32 — Model shift documented or tracked | Is a new adversary or security promise silently introduced? | **N/A to runtime model change.** No runtime principal, capability, IPC/MMU/DMA boundary or protection claim changes; ADR-0040 and the CI guide document the host administration/scheduling scope and limits. |

### Findings and integration hold

**No new actionable security finding in the T-035 delta.** The JSON baseline and supplied live export compare equal, including all six checks with app ID 15368, strict true, reviews/REST policy, GraphQL PR-review enabled/deployment disabled/no actors, and empty rulesets. The parent-produced apply log says `PASS: live policy matches; no write needed`; this reviewer did not invoke it or certify a policy mutation.

**Corroborated inherited T-036 integration issue — not cleared by this security verdict.** Parent supplied `/tmp/tyrne-b21-step7/registration-tip-failure.log` from hosted run 38186028266 at the prior registration tip. It shows the deliberately restored arch-only hello build failing with `error: unwinding panics are not supported without std`, followed by the harness's refusal because it expected only `error[E0152]: found duplicate lang item panic_impl`. At the immutable reviewed tip, `tools/test-ci-gates.sh:74` still permits only the latter diagnostic after restoring exactly six hello target predicates. Cargo's all-targets competition can surface either genuine symptom first. This is a verified false-negative/reliability problem in the inherited required gate, not a newly demonstrated privilege bypass or false-green security result. The paired code pass appropriately holds integration until the correction is reviewed. A fix must retain exact mutation preconditions and reject unrelated compiler/tool failures; widening acceptance to any nonzero compiler exit would lose the intended negative control. Subsequent edits are outside this immutable review and require fresh Round 2.

The historical earlier reviews remain scoped to their exact commits and observations. One later green run does not disprove a race observed in another run. Existing HIGH T-038 is separately retained and is not folded into, fixed by, or downgraded by this host diagnostic issue.

### Architectural principles P1–P12

| Principle | Outcome and justification |
|---|---|
| P1 — No ambient authority | **OK for delta.** No runtime grants; admin action requires explicit local command and external GitHub authority, absent from CI. |
| P2 — Smallest defensible TCB | **OK.** Host-only tooling; shipped kernel TCB unchanged. |
| P3 — Drivers in userspace | **N/A.** No driver/service placement change. |
| P4 — Checks at trust boundaries | **OK for changed boundary.** Fail-closed validation and full preconditions precede the sole narrow policy write. |
| P5 — Rust with disciplined assembly | **OK for delta.** Python/shell are host orchestration; no unsafe expansion or assembly soundness claim. |
| P6 — HAL isolation | **N/A.** No architecture-dependent kernel/HAL interface change. |
| P7 — No proprietary blobs | **OK.** Source-built userland/kernel images; no opaque guest binary committed. |
| P8 — Decisions in ADRs | **OK.** Accepted ADR-0040 authorizes schedule and versioned local administration policy. |
| P9 — English repository | **OK.** New source comments, diagnostics and documentation are English. |
| P10 — Mermaid diagrams | **N/A.** No new diagram. |
| P11 — Reproducibility | **OK for delta.** Full action/toolchain pins, architecture-scoped caches and explicit source/dirty-state/tool version metadata; rolling host packages remain disclosed. |
| P12 — No half-finished main | **OK for scoped development, integration held.** T-035 remains In Review; first hosted evidence, two fresh rounds, final maintainer PR and post-merge dispatch are not silently converted into Done. T-036 correction remains required by the paired integration review. |

### Independently executed evidence

All executions used immutable archived bytes, not the evolving shared worktree:

- `python3 tools/test-branch-protection.py`: **27/27 pass**.
- `python3 -O tools/test-branch-protection.py`: **27/27 pass**; production validation uses explicit exceptions rather than assertions.
- `python3 tools/test-perf-harness.py`: **6/6 pass**, including 20 synthetic samples, clean/dirty/unavailable Git-state labels, immutable report refusal, zero/partial sample behavior and failed harness status through explicit Bash/tee.
- Additional independent `/tmp/tyrne-b21-t035-security-attacks.py`: **72 adversarial cases pass normally and with `-O`**, using explicit fixture failures that remain active under optimization. Evidence log `/tmp/tyrne-b21-t035-security-attacks.log`. Cases cover every REST boolean wrapper missing/integer/unknown-field substitution, every supported GraphQL rule value changed, bool/int confusion, wrong/truncated SHA, bad completion/conclusion/source-app data, total/count/truncation/duplicate evidence, all nine final-read boolean drifts, and subprocess nonzero/timeout secret suppression. Every rejected policy/evidence case asserts zero fake writes. These are offline attacks, not real GitHub mutations.

Reviewed-source SHA-256:

| File | SHA-256 |
|---|---|
| `tools/branch-protection.py` | `747b196e11e21340d0a7d607c7699fd129d58f9df54b96199ff6bad6907a55bd` |
| `tools/perf-harness.sh` | `d5f4818f51e46ec805d75b9bd05bbd22ef5abf6470d2e899fbd2abb610aadf8c` |
| `.github/workflows/performance.yml` | `48739689bd1d1a8458a14b4c69e9fab20799c3fde6503f8bd3efa4f65038c753` |

### Supplied evidence inspected and limits

Parent downloaded [performance run 38186988714](https://github.com/HodeTech/Tyrne/actions/runs/38186988714), job 114611329672, into `/tmp/tyrne-b21-step8/hosted-perf-artifact/performance-e8739957ea0a2ceabb33fa7519cadb1a1d2be57e-1/`. Independently read metadata, full report and harness output: full reviewed SHA, clean tracked worktree, attempt 1, pinned Rust 1.94.0-nightly / nightly-2026-01-15, QEMU 8.2.2, **20 requested / 20 valid / 0 failed**, harness wall **101 s**, evidence interval **139 s**. Recomputed nearest-rank p10/p50/p90 from all 20 raw samples: **8,408,784 / 9,120,416 / 12,621,792 ns**, matching the report. Parent reports whole-job 144 s; this is distinct from the two durations directly present in inspected evidence. Parent also reports all seven CI jobs green in run 38186988733; this reviewer did not independently retrieve that run metadata.

The committed local report is transparently pre-commit evidence: base SHA `69ac515...`, dirty tracked worktree, QEMU 11.1.1, 20/20 samples and 100 s harness wall. It is not relabeled as clean-tip/hosted evidence. The new hosted report supplies the clean-tip measurement separately. Performance measurements do not establish a calibrated regression threshold or kernel security proof.

I did not repeat full Rust/Miri/QEMU runtime suites or invoke any live export/check/apply. No changed Rust justifies a fresh unsafe audit for this delta; supplied prior/runtime results retain their original attribution. The active schedule and dispatch depend on default-branch registration after the maintainer's merge, so post-merge dispatch evidence remains pending. `always()` is best-effort under runner loss/cancellation, not guaranteed archival.

## Verdict

**Approve the scoped T-035 security delta at `e8739957ea0a2ceabb33fa7519cadb1a1d2be57e`.** All eight axes, 33 checklist items and P1–P12 are explicitly disposed. No new actionable T-035 security finding was verified. The non-atomic remote-administrator race is accurately documented and operationally constrained; this report makes no compare-and-swap or rollback guarantee.

**Overall integration remains held for the inherited T-036 diagnostic correction and fresh Round 2 review.** Existing HIGH T-038 remains excluded, unchanged and undowngraded. This report is neither Done promotion nor final maintainer PR approval. Parent owns canonical artifact publication, index/trailer recording and lifecycle changes; no maintainer approval or subsequent live operation is fabricated here.
