# Security review 2026-10-12 — T-035 CI hygiene tail

- **Change:** approved Track B.2-1 step8, `69ac515..e873995`; later T-036 integration correction recorded below.
- **Round1 reviewers:** fresh `b21_step8_round1_code` (`gpt-6.1-sol` / high requested) and distinct `b21_step8_round1_security` (`gpt-6-astra` / high requested), empty inherited context. Configuration provenance, not runtime identity attestation.
- **Paired artifact:** [code review](../code-reviews/2026-10-12-t035-ci-hygiene-tail.md).

> **Current reconciliation:** Both fresh rounds complete. R1 code Request changes for inherited Medium R1-CODE-01; scoped T-035 security Approve. Coordinator verified and fixed the ARM diagnostic race, with permanent exact-class/exit101 refusal controls and an old-code negative control. Fresh R2 code/security both Approve the whole combined delta with zero new finding; full reports read and retained below. Corrected hosted run38187736985 passes all seven jobs and actually exercises the formerly rejected unwind class. Downloaded debug/release guest and23-control evidence passes. First performance artifact at clean e873995 is verified; workflow/harness bytes are unchanged by the later fix. Existing HIGH T-038 remains excluded/undowngraded. Final entry-doc integration, maintainer PR and merge-dependent evidence remain separate; tasks stay In Review.

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

## Round2 — security

# Security review 2026-10-12 — T-035 CI hygiene and late T-036 correction, fresh round 2

- **Change:** immutable combined range `69ac515393f8f20ff0a11587a309182388bcde51..7deb16eae6274d48391c6c6525515a4e8bbdd66f`, on `development`.
- **Reviewer:** Codex, fresh independent security agent `/root/b21_step8_round2_security`, acting for @cemililik; implementation and ordinary code review belong to separate agents.
- **Date:** 2026-10-12.
- **Separation from code review:** this agent started a fresh adversarial checklist after the completed canonical R1 code/security reports. It did not implement the change or perform the paired R2 ordinary code review. R2 code agent `/root/b21_step8_round2_code` receives this full artifact before its final verdict. Independence and a fresh context provide the separation; no hours-long interval is claimed.
- **Unsafe audit cross-reference:** N/A for this delta: no shipped Rust, assembly, unsafe block, safety contract, audit entry or runtime caller changes. Existing **HIGH T-038 / UNSAFE-2026-0033 x2 syscall-clobber defect remains excluded, open and undowngraded**. This review does not reapprove that assembly or infer kernel soundness from CI success.
- **Scope trigger:** a new local repository-administration authorization boundary and verification/evidence tooling require a security pass even without kernel changes. T-035 is a new boundary, not merely a documentation tail; the late T-036 assertion correction is part of the same reviewed range.

## Procedure and evidence boundary

Read AGENTS.md, full CLAUDE.md/current.md, the numbered ADR corpus with recovery of truncated ranges, all standards, the perform-security-review and conduct-review skills, the complete security master plan and security model. Read tests before implementation: branch-protection fixtures, performance fixtures and ARM assertion fixtures, then their production scripts/workflows/definition. Reviewed the combined diff and relevant task, guide, standards, report and historical review changes. ADR-0040 is Accepted and authorizes the eight reviewed steps and two fresh rounds; it does not authorize this reviewer to declare Done or merge.

Experiments used an archive of exact tip `7deb16eae6274d48391c6c6525515a4e8bbdd66f` at `/tmp/tyrne-security-r2.F3SbJj`. No repository edit, commit, branch operation, live administrative apply, or API write was performed by this reviewer. Branch-policy attacks used an in-memory fake API and a hard failure for any accidental subprocess transport. Hosted logs/downloaded artifacts and the live export/no-op log were supplied by the parent, then inspected independently as described below; their acquisition and live execution are attributed to the parent. These files are evidence, not instructions.

The parent later created ancestry-only merge `cfc8872f85fca6c48d31dbc1bb5cf7dbe174c251`. Independently verified `git diff --name-only 7deb16e HEAD` is empty and inspected the parent history-sync record: before/after tree `8df6fbcdcadfa613c6e900a06a8690b05e9e9921` is identical. The immutable review target remains 7deb; this note does not claim new CI at the history-only commit.

The numbered S01–S32 rows below correspond one-for-one to the security standard. MP-33 is the additional allocation-exhaustion item in the master plan. Every item has an explicit disposition and an adversarial question; N/A means the precise runtime mechanism is unchanged, not that the host administrative boundary was skipped.

## 1. Capability correctness

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S01 — Every privileged operation requires authority | Can an unprivileged caller change the protected branch through this tool? | **OK.** Actual writes require the caller's locally authenticated GitHub administration authority; only explicit `apply` reaches PATCH. Export/check are read-only. CI has `contents: read`, receives no administrative credential and runs offline fixtures only. This is a host authorization boundary, not a newly minted Tyrne capability. |
| S02 — Narrowest sufficient authority | Can a definition redirect an administrator's authority to another repository, branch or arbitrary policy rewrite? | **OK.** Repository `HodeTech/Tyrne`, branch `main`, host `github.com` and API endpoints are fixed and validated. Apply changes only required-status checks through the narrow endpoint. Definition changes cannot alter strictness, existing names/app bindings or non-status policy. GitHub administration is the API's required permission; the tool narrows how it is used. |
| S03 — Authorization before observable effects | Can rejected drift or forged green evidence nevertheless cause a policy write? | **OK.** CI marker refusal, schema validation, complete expected-current equality, additive-only checks, exact SHA/app/completed-success proof, and the last full policy read precede PATCH. Refusal paths produced zero fake writes. API reads and local diagnostics are observable, so this is specifically a no-policy-mutation guarantee, not network invisibility. |
| S04 — Move-only capability transfer | Does the change clone a kernel capability or transfer administrative credentials into CI/artifacts? | **N/A** for Tyrne capability transfer: no transfer code changes. Host audit found no credential forwarding into a workflow or artifact; checkout disables persisted credentials in the performance job. |
| S05 — Explicit duplication authority | Can a new duplication path manufacture a capability? | **N/A.** No capability duplication operation, table, handle encoding or rights change exists in the delta. Reusing ordinary local `gh` authentication is an administrator-controlled host operation. |
| S06 — Atomic revocation | Does the change claim atomicity while removing rights in several stages? | **N/A** for capability revocation: no revocation path changes. Administrative reconciliation is explicitly non-atomic and cannot remove existing checks; the separate administrator race is analyzed under axis 8 rather than mislabeled atomic revocation. |

The local tool is a guardrail for a trusted administrator, not a sandbox against a malicious administrator who can edit the script, unset CI variables or call GitHub directly. GitHub documents administration-write permission and the narrow status-check PATCH, including explicit app binding. [GitHub status-check protection API](https://docs.github.com/en/rest/branches/branch-protection#update-status-check-protection).

## 2. Trust boundaries

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S07 — Validate userspace-to-kernel input | Can malformed input reach a changed kernel entry point, or can analogous malformed policy input authorize a write? | **N/A** for the syscall boundary, which is unchanged. **OK** for the host analogue: exact key sets/types, supported values, duplicate-key rejection, full normalized equality and remote evidence validation fail closed before mutation. Null/scalar/error-envelope attacks were rejected without writes. |
| S08 — Validate user pointers before kernel dereference | Can a supplied pointer or path become a kernel dereference or shell command? | **N/A.** No user-pointer code changes. The host API uses an argv list and stdin JSON, not shell evaluation; fixed endpoint construction and full lowercase SHA validation reject shell-shaped SHA input. |
| S09 — Bound user lengths against mapped regions | Can a length overrun a new mapped buffer or allow incomplete remote evidence? | **N/A** for mapped buffers. **OK** for check evidence completeness: exact integer total count, at most 100 entries, and equality to list length reject truncation/pagination rather than trusting a partial successful result. No new byte-copy length exists. |
| S10 — Parse messages into typed structures | Can unknown/missing/duplicate JSON fields, bool-as-int values or a near-match diagnostic be treated as valid evidence? | **OK** for the relevant host boundary. JSON duplicate keys and unsupported policy keys fail; booleans/integers are checked exactly where authority matters; GraphQL baseline comparison preserves type distinctions. The ARM assertion requires exit 101 and a full exact line from one of two observed diagnostics. Independent whitespace/prefix/suffix/ANSI lookalikes fail. No raw userspace message parser changes. |
| S11 — IPC transfers no excess authority | Can a sender obtain additional cross-task rights through this change? | **N/A.** IPC endpoints, send/receive, transfer semantics and kernel call paths are byte-unchanged. The administrative analogue preserves every existing name/app binding and cannot weaken non-status policy. |

The effective classic policy is read through both REST and a fixed read-only GraphQL query. GraphQL covers review enablement, deployments and actor allowances omitted from the supported REST view. Unsupported nonempty extensions and any repository/inherited ruleset stop reconciliation. Empty rulesets are the only supported baseline, so the first page containing any rule is sufficient to refuse; it never accepts a partial nonempty list. GitHub documents inherited rulesets as included by default. [Repository rulesets API](https://docs.github.com/en/rest/repos/rules#get-all-repository-rulesets).

For new check registration, a local fabricated result file cannot supply the green proof: the tool queries check runs at the exact supplied 40-character SHA and requires exactly one matching name with the configured app, completed status and successful conclusion. Duplicates, missing results, failure/neutral/skipped conclusions, app mismatches and incomplete lists fail. This proves the requested check at that SHA; it does not prove the caller selected the current branch head, authenticate arbitrary workflow semantics, or eliminate the need to review the definition and chosen source.

## 3. Memory safety

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S12 — New unsafe meets policy | Is a changed unsafe site missing justification, audit registration or security sign-off? | **N/A.** The 23-file delta has no shipped Rust/assembly or unsafe change. Python and shell host tools require boundary review, but do not receive invented Rust unsafe entries. |
| S13 — Safety invariants hold for every caller | Does a new caller broaden an existing unsafe contract, or does a green gate wrongly clear known UB? | **N/A** for changed callers: none. **Flagged — existing excluded HIGH remains:** T-038 / UNSAFE-2026-0033 x2 syscall-clobber issue is not fixed or downgraded by this tooling review. Successful tests and probe diagnostics do not validate that assembly's contract. |
| S14 — No uninitialized memory exposure | Can a partially initialized kernel buffer become visible? | **N/A.** No buffer initialization or kernel output source changes. Host metadata records explicit dirty/clean/unknown state; a failure to query source state is not relabeled clean. |
| S15 — No use-after-free | Does a changed raw pointer outlive its owner, or can the probe destroy source through cleanup? | **N/A** for raw pointers. Host cleanup is bounded to a newly created private temporary directory, with quoted paths and an EXIT trap; offline cases check source hashes and removal after success, rejection and copy failure. No repository source deletion occurs. |
| S16 — No aliasing violation | Can overlapping mutable references cross a switch or concurrent kernel boundary? | **N/A.** No references, context switches or runtime memory ownership change. Probe mutations and Cargo output are isolated to their own temporary copy/target; source-preservation assertions pass. |

No unsafe audit entry is created, amended or second-signed by this review. The audit applicability determination is based on the complete diff, not an assumption that Python/shell changes can never be security-sensitive.

## 4. Kernel-mode discipline

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S17 — No allocation in ISRs | Does the measurement/reporting path allocate from an interrupt handler? | **N/A.** Reporting runs on the host after unchanged guest output; no ISR code changes. |
| S18 — No unbounded kernel loops | Can a new loop stall privileged guest execution or consume unlimited hosted runtime? | **N/A** for kernel loops. Host exposure is bounded: 20 requested measurement iterations with a five-second per-run watchdog, a ten-minute performance job, existing ARM job bound, finite API work and a 30-second subprocess API timeout. This is not an SLA for GitHub scheduling. |
| S19 — Minimize critical sections | Can external API waits or report formatting hold a kernel lock? | **N/A.** All added administration/reporting work is host-side; kernel locks, IRQ masking and scheduler critical sections are unchanged. |
| S20 — No new hot-path kernel panic | Can malformed host input or the diagnostic fallback introduce a production panic? | **N/A.** The intentional no_std/panic-handler regression exists only in the disposable compiler-probe copy. The shipped six cfg predicates, build script and syscall shim stay unchanged. Expected compiler failure is separate from production failure. |
| MP-33 — Allocation exhaustion returns typed errors, not panics | Can a new kernel allocation exhaust memory and panic? | **N/A.** No kernel allocator, arena capacity or allocation path changes. Host memory/disk/tool failures yield failing commands and cannot bypass the pre-write policy checks. This review makes no general claim that Python allocation is bounded against hostile local files. |

The ARM fix retains the exact `cargo clippy --workspace --exclude tyrne-bsp-qemu-virt --all-targets -- -D warnings` command. It still requires a native aarch64 Rust host, precisely six matching predicates, and only replaces those predicates in the private hello source. Its two accepted full lines correspond to the test harness's duplicate panic handler and the normal no_std binary's unwind rejection. Cargo's all-target compilation may expose either first. Exit 0, tool failures and unrelated compiler errors are not accepted. Printing the actual observed class makes the assertion auditable.

The performance logging pipeline uses explicit Bash, preserving failure through `tee`; the independently executed fixture checks this failure path. GitHub's explicit Bash command includes `-eo pipefail`. [Workflow shell syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_iddefaultsrun).

## 5. Cryptography

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S21 — Reviewed cryptographic primitives | Is a home-grown cipher, hash, signature or protocol introduced? | **N/A.** No cryptographic implementation or protocol is added. Commit/action SHA identifiers and artifact SHA-256 evidence are provenance references, not a new cryptosystem. |
| S22 — Keys absent from logs/errors/Debug | Can a newly handled cryptographic key leak? | **N/A** for cryptographic key management: none is introduced. GitHub credential handling is separately applicable and assessed in S26. |
| S23 — Constant-time sensitive comparisons | Does a new comparison reveal secret-dependent timing? | **N/A.** Equality checks compare public policy, source identifiers and check evidence; no secret equality or cryptographic decision is implemented. |
| S24 — Acceptable randomness | Can predictable randomness compromise a new secret or protocol? | **N/A.** No security nonce/key generator is added. Host temporary directories use existing platform temporary-directory facilities, not invented secret-generation code. |
| S25 — Correct nonce/IV/salt contracts | Can nonce reuse or invalid initialization break encryption/authentication? | **N/A.** No encryption, nonce, IV or salt handling exists in the delta. |

## 6. Secrets and logging

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S26 — No secrets in diagnostic channels | Can gh stderr, a token or repository credential be copied into logs, JSON or artifacts? | **OK.** The tool relies on existing local gh authentication without printing credentials; failed gh stderr is captured and replaced by a generic failure. Transport fixtures pin redaction. Export/check differences contain policy values, not tokens. Performance artifacts collect explicit run/source/toolchain/QEMU/host/output files from a dedicated evidence directory, not the workspace or credential store. |
| S27 — Security-sensitive Debug redacted/absent | Does a new Debug/representation expose capability or credential bytes? | **N/A** for Rust Debug implementations: none change. **OK** for analogous host representations: no credential-bearing type is serialized or printed; diagnostic fixtures exercise transport failure secrecy. |

Hostnames, source SHA, public run identifiers, toolchain paths and guest console output are intentionally diagnostic metadata. Their publication is appropriate to this public repository's CI contract; no general promise of arbitrary-output secret scrubbing is made. Trusted build tools and reviewed guest output remain assumptions. Read-only `contents` permission still permits the platform's artifact/cache mechanisms; those are bounded CI evidence facilities, not branch-administration authority.

## 7. Dependencies

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S28 — Dependency addition policy | Does the change silently introduce an unaudited Rust dependency? | **OK.** No Cargo manifest/lock dependency change; Python uses the standard library and shell tools already used by the project. New workflow references reuse full-SHA-pinned actions. No add-dependency/Cargo trust approval is owed for a nonexistent crate addition. |
| S29 — Trust category understood | Can a build-time service/tool be mistaken for kernel-linked or hermetic trust? | **OK.** GitHub, gh, Python, Bash, pinned Rust/actions, hosted runner packages and QEMU are host/build/evidence trust. No new kernel-linked trust is introduced. ubuntu-latest and apt QEMU can change; actual versions are recorded, and timings are not claimed bit-reproducible across hosts. |
| S30 — cargo-vet updated as needed | Was a changed Rust dependency left without its trust decision? | **N/A.** No external Rust dependency is added/upgraded; the repository's conditional cargo-vet/cargo-audit work remains dormant until an external dependency lands. This does not mean those tools were run here. |

The performance workflow has schedule Monday 03:17 UTC, manual dispatch and only two exact development push paths (`.github/workflows/performance.yml`, `tools/perf-harness.sh`); no pull-request trigger. It has read-only contents permission, disabled checkout credential persistence, dedicated architecture/toolchain cache identity, timeout/concurrency limits and 14-day artifacts. Package installation remains ordinary hosted provisioning; toolchain/QEMU provenance limits performance comparisons rather than silently becoming an unreviewed release guarantee.

## 8. Threat-model impact

| Item | Adversarial question | Disposition and justification |
|---|---|---|
| S31 — Reconciled with security model | Does the new administrative boundary relax runtime capability isolation or conceal a repository-policy weakening? | **OK.** Tyrne's kernel threat model is unchanged. Host supply-chain/administration trust is explicitly added to this review: fixed target, exact supported full policy, no rulesets, no CI admin token, additive-only writes, remote app/SHA proof, final reread and full readback. Existing solo review count 0 and disabled admin enforcement are preserved explicitly, not represented as multi-contributor protection. |
| S32 — Changed threat model documented | Does any new assumption remain hidden or require a missing ADR/update? | **OK.** Accepted ADR-0040 and the CI guide/infrastructure standard document local administration, representability refusal, non-atomic race, coordinated admin changes and no automatic rollback. Performance is informational with no calibrated floor or required check. Runtime security-model.md needs no fictional new kernel boundary; existing deferred runtime risks remain. |

### Administrative race and applicability limits

The final full read narrows the race; it is not compare-and-swap. Another administrator can change required checks after that read and before PATCH, and a concurrently added check could be overwritten without the post-write comparison detecting its brief existence. Non-status drift surviving the narrow PATCH is caught by full readback. The API surface does not offer a documented conditional atomic update here, and the guide explicitly requires coordination. This is an accepted, documented limitation of local trusted administration, not a security finding newly introduced by this review. No automatic rollback is correct: rollback could overwrite a third administrator change. A failed post-write verification requires inspection and does not mean no remote mutation occurred.

Similarly, a sequence of REST/GraphQL/ruleset reads is not one server-side snapshot. API/schema failure or unsupported settings cause refusal. That conservative limitation can make administration unavailable until reviewed adaptation; it cannot silently strip an unmodeled protection field through a broad PUT. The tool does not claim to secure a compromised maintainer account, compromised local executable/PATH, malicious upstream service, or arbitrary edited workflow.

The informational workflow visibly fails on build/measurement/upload failure; no timing threshold or merge floor exists. Best-effort schedule/dispatch behavior and default-branch registration are documented. Cancellation/runner loss can prevent even `always()` artifact collection; this is evidence availability, not privilege escalation. Post-merge schedule/manual-dispatch and first-main evidence remain pending.

### P1–P12 applicability

| Principle | Disposition and reason |
|---|---|
| P1 — No ambient authority | **OK, host analogue.** Explicit local admin authority; no administration token in CI. No Tyrne capability bypass. |
| P2 — Smallest defensible TCB | **OK.** Added code stays in host tooling; kernel TCB is unchanged. The admin tool deliberately supports one repository/branch/policy shape. |
| P3 — Drivers/filesystems/network in userspace | **N/A.** No runtime subsystem placement changes; reporting/admin code is outside the kernel. |
| P4 — Capability checks at every boundary | **OK, host analogue.** Local mode and strict preconditions precede any narrow policy write; kernel capability boundaries unchanged. |
| P5 — Rust-only kernel, justified assembly | **N/A.** No kernel/HAL/service-language or assembly change; Python/Bash are host tools. T-038 remains excluded HIGH. |
| P6 — HAL separation | **N/A.** No HAL, board-specific runtime reference or kernel dependency change. Native host selection is CI orchestration. |
| P7 — No proprietary binary blobs | **OK.** No blob is committed/embedded; the workflow builds userland and kernel from source. Report snapshots are text. |
| P8 — Decisions recorded as ADRs | **OK.** ADR-0040 Accepted before implementation governs schedule/admin choices and the eight-step/two-round procedure. |
| P9 — English repository artifacts | **OK.** Added tooling, documentation, fixture diagnostics and this artifact are English. |
| P10 — Mermaid diagrams | **N/A.** No new diagram; tables and text reports do not introduce an alternate diagram format. |
| P11 — Reproducibility from toolchain up | **OK within scope.** Pinned Rust/actions and unchanged lockfile; full source/tool/host metadata. Timings on rolling hosted infrastructure are explicitly contextual, not reproducible latency guarantees. |
| P12 — No half-finished subsystems on main | **OK for review readiness.** The combined implementation and correction have concrete offline/hosted proof. Work remains In Review on development; final PR/maintainer decision, first merged-main checks and dispatch evidence are not prematurely marked complete. |

### Independent experiments and supplied evidence

| Evidence | Observation and attribution |
|---|---|
| Immutable source | Private `git archive` of exact 7deb tip; combined diff inspected. No shipped Rust/assembly changed. Shared development worktree remained clean at verification. |
| Permanent policy suite | Independently ran 27 tests normally and under `python3 -O`: both pass. Covers narrow mutation/readback/no-op, drift, unsupported policy, exact types, green evidence/app binding, CI refusal, CLI and redacted transport. |
| Permanent performance suite | Independently ran six tests normally and under `python3 -O`: both pass. Covers 20-sample metadata, report preservation, dirty/unknown provenance, empty/partial samples and pipeline failure. |
| Permanent ARM suite | Independently ran nine tests normally and under `python3 -O`: both pass. Fixture stubs check exact command, six predicates, private target, no color, source hashes and cleanup; both observed classes pass and failure controls fail. These are offline contract tests, not nine real compiler runs. |
| Independent administrative attacks | `/tmp/tyrne-security-r2.F3SbJj/security-attacks.py`: 32 attacks passed. Twenty-four malformed response combinations across rulesets/GraphQL/REST/check evidence, four floating-point actor counts, three malicious/malformed SHAs and final-read GraphQL drift all refused with zero fake writes. Real subprocess transport was disabled for this experiment. |
| Independent diagnostic attacks | Five additional leading/trailing whitespace, suffix, note-prefix and ANSI-suffix lookalikes rejected. Fixture source hashes and cleanup checked. These experiments were run normally; no optimized-mode claim is made for the custom assert-based attack script. |
| Old-assertion negative control | In a fixture-owned temporary copy only, substituted the base 69ac script and supplied valid 101/unwind output: old assertion rejected it. Corrected exact-tip assertion accepts that same fixture. This demonstrates the test distinguishes the regression. |
| Historical actual failure | Parent supplied `/tmp/tyrne-b21-step7/registration-tip-failure.log`, hosted run 38186028266 at 69ac: intended mutation failed with the unwind class while the old E0152-only assertion failed. Historical green E0152 runs/R1 remain preserved; they did not prove absence of the race. |
| Corrected actual hosted ARM | Independently inspected parent-downloaded `/tmp/tyrne-b21-step8/fixed-hosted-arm.log`: native `aarch64-unknown-linux-gnu`; exact private probe passes with exit101 and `error: unwinding panics are not supported without std`. Native tests/Miri each report 366 passing with two ignored HAL doctests. [Run 38187736985, ARM job 114613632255](https://github.com/HodeTech/Tyrne/actions/runs/38187736985/job/114613632255). |
| Corrected full CI | Parent-supplied `fixed-hosted-ci.json` reports completed/success and all seven named jobs success. That summary JSON omits head SHA; independently inspected ARM checkout fetch/hash lines identify exact 7deb, corroborated by smoke artifact metadata. Source identity is not invented from the summary field. [Run 38187736985](https://github.com/HodeTech/Tyrne/actions/runs/38187736985). |
| Corrected smoke evidence | Independently inspected parent-downloaded results and metadata: exact 7deb full SHA, clean tracked source, 23 individually passed cases (20 synthetic + three actual private variants), `real_requested` and `completed` true, evidence wall97s. Parent independently checked production traces/profile/fault markers. This reviewer did not rerun real guests for this host-only delta. |
| First actual hosted performance | Parent-downloaded e873 artifact report independently byte-compared with `docs/analysis/reports/perf-baseline-2026-10-12-t035-hosted-check.md`: exact match, report SHA-256 `b0893bf535f2eba2d9daf44dcb7097d8bbb4f58f602cef158ada7a53be1cecaa`. 20 requested/20 valid/zero failed; twenty raw samples independently recounted and p10/p50/p90 recomputed: 8,408,784 / 9,120,416 / 12,621,792 ns. Clean full e873 SHA, pinned Rust, QEMU8.2.2; harness101s, metadata139s; parent reports full job144s. [Run 38186988714, job 114611329672](https://github.com/HodeTech/Tyrne/actions/runs/38186988714/job/114611329672). |
| Performance provenance limit | Independently verified performance workflow/harness unchanged between e873 and 7deb. e873 is the actual measured source; it is not relabeled a new 7deb timing run. The recomputed digest is of the report file, not the service artifact archive; no independent archive-digest claim. |
| Live policy evidence | Parent performed the local live export/check/no-op apply. Independently compared `/tmp/tyrne-b21-step8/live-export.json` with the committed definition: equal. Parent `live-apply.log` says policy matches/no write needed. This reviewer did not invoke live apply or inspect fresh live API state; this is timestamped parent evidence, not a permanent drift guarantee. |

### Finding reconciliation and completeness

No new actionable security finding was identified in the combined range. All eight axes and all 33 dispositions are present. S13 preserves the existing excluded HIGH explicitly; it is not a minor newly waived finding and does not expand this review into a whole-kernel approval.

R1's scoped T-035 security Approve remains a historical and valid scoped judgment. R1 code's inherited Medium T-036 race remains in history with its observed failing run. The 7deb correction resolves the examined assertion defect: exact compiler command and exact isolated mutation remain, accepted status is narrowed to 101, diagnostics are full-line and limited to two actually observed rejection classes, and the previously failing class now passes on a real hosted ARM run. This is not acceptance of any compiler error and not a change to production cfg gates. The paired R2 code review owns its independent final code verdict.

Canonical publication/index/trailer work is intentionally delegated to the parent under the no-repository-edits instruction. This complete temporary artifact supplies that work; it does not claim those later writes have happened. Required final maintainer review and future default-branch dispatch/first-main evidence remain pending, with no Done promotion or merge represented here.

## Verdict

**Approve — the whole combined security-review scope `69ac515393f8f20ff0a11587a309182388bcde51..7deb16eae6274d48391c6c6525515a4e8bbdd66f` is ready for the next authorized review/integration step.**

No new security blocker remains in T-035 or the included late T-036 assertion correction. The exact two-class/exit101 fix and actual corrected hosted rejection close the examined inherited diagnostic-race hold from this security perspective. Approval relies on the documented trusted-local-administrator model, additive-only supported policy and explicitly non-atomic coordinated administration; it is not assurance against concurrent or malicious administrators. Existing HIGH T-038 remains open and undowngraded. Final PR review, maintainer merge/Done decisions and post-merge evidence are separate pending work.
