# Code review 2026-10-12 — T-035 CI hygiene tail

- **Change:** approved Track B.2-1 step8, `69ac515..e873995`; later T-036 integration correction recorded below.
- **Round1 reviewers:** fresh `b21_step8_round1_code` (`gpt-6.1-sol` / high requested) and distinct `b21_step8_round1_security` (`gpt-6-astra` / high requested), empty inherited context. Configuration provenance, not runtime identity attestation.
- **Paired artifact:** [security review](../security-reviews/2026-10-12-t035-ci-hygiene-tail.md).

> **Current reconciliation:** R1 code Request changes for verified Medium R1-CODE-01, an inherited T-036 compiler-diagnostic race; scoped T-035 security Approve with no new actionable finding. Coordinator read both full reports, verified the finding and corrected it locally with permanent offline controls. Fresh R2 and corrected hosted proof remain pending. Exact-source first performance artifact and all seven CI jobs are green at e873995. Existing HIGH T-038 remains excluded and undowngraded. Final maintainer PR and merge-dependent evidence remain pending; tasks stay In Review.

## Round1 — code

# Code review 2026-10-12 — T-035 STEP 8, fresh round 1

- **Change:** `69ac515393f8f20ff0a11587a309182388bcde51..e8739957ea0a2ceabb33fa7519cadb1a1d2be57e`, on `development`; 15 files, 1041 insertions, 49 deletions. Immutable commit subject: `ci: add weekly performance reports and versioned merge policy`.
- **Reviewer:** Codex independent agent `b21_step8_round1_code`, all five code-review roles sequentially, on behalf of @cemililik.
- **Risk class:** Security-sensitive administrative authorization boundary. No kernel/Rust/unsafe change.
- **Security-review cross-reference:** `/tmp/tyrne-b21-t035-round1-security.md`, fresh independent Astra pass; final cross-read recorded below before this report is delivered.
- **Review boundary:** Read-only repository and captured live evidence. Private immutable `git archive e873995` snapshot and experiments at `/tmp/tyrne-b21-t035-round1-code-private/`. No live API mutation, repository edit, branch, commit, task promotion, or PR/merge action by this reviewer.

## Correctness

**No new confirmed T-035 correctness finding.** One inherited integration blocker is recorded under Integration and in the verdict; it is not attributed to the STEP 8 diff.

Description → tests → definition/normalization → reconciliation/transport → CLI/workflow callers → tests were reviewed in dependency order. Background included full AGENTS/CLAUDE, `current.md` with historical banners, all numbered ADR files in numerical order (39 files, including Accepted ADR-0040), all 15 standards, skill index plus `perform-code-review` and `conduct-review`, the full code-review master plan, T-035/T-036, and the earlier Track B.2-1 preflight review. Large tool reads that truncated were followed by smaller reads of the omitted sections.

Administrative behavior:

- Committed JSON is equal to `/tmp/tyrne-b21-step8/live-export.json`: six exact check contexts, every binding app 15368, strict checking, all captured REST toggles/review settings, GraphQL-only review enablement/deployment/restriction/actor counts, and empty rulesets.
- `validate` rejects missing/unknown fields, invalid types including bool-as-int, duplicate contexts, non-positive/unbound source apps, unsupported classic policy and restrictions. Canonical check ordering does not erase a binding or alter semantics. Duplicate JSON keys are rejected rather than taking the last value.
- `live` examines repository/inherited rulesets, the applied classic rule and full REST protection. Unsupported GraphQL actor/deployment policies are rejected by exact supported-baseline comparison. Unknown REST policy is not silently omitted. Known URL/context metadata is the only normalized response metadata.
- `apply` has explicit local invocation, CI-environment refusal, expected full-baseline equality, additive-only context preservation including strict/app bindings, full lowercase SHA proof, exactly one completed successful app-bound remote check per addition, a second full read immediately before the narrow status-checks PATCH and a full post-write read-back. No-op performs two full reads and zero mutation calls. Errors stop reconciliation; no automatic rollback overwrites another administrator's concurrent policy.
- The real subprocess boundary was independently exercised with a private `gh` shim: explicit fixed `github.com`, REST GET with no body, GraphQL POST with only the read-only query, narrow PATCH with JSON on stdin, and canary stderr suppression. No shell interpolation or credentials in argv are introduced.
- The API has no implemented atomic compare-and-swap. A concurrent administrator can race after the last read; this limitation is stated in the guide and is not presented as atomic enforcement.

Performance behavior:

- Separate informational workflow: Monday `17 3 * * 1`, dispatch, and only `development` pushes changing its own file or `tools/perf-harness.sh`; no PR trigger. Contents-read permissions, checkout credentials disabled, SHA-pinned actions, architecture-separated performance cache, pinned nightly, userland build before kernel, matching debug images, bounded job and 14-day evidence artifacts.
- Harness delta is metadata only: full SHA, tracked dirty/clean/unknown state, Rust compiler and active toolchain. Timing extraction, aggregation, watchdogs, failure threshold and append-only report behavior are unchanged.
- Explicit Bash gives the measurement pipeline `-e -o pipefail`; report extraction accepts one expected relative Markdown path and quotes the copy. Fatal measurement failures stay failures through `tee`. Always-run wall metadata and upload preserve available failure diagnostics.
- The existing canonical harness deliberately accepts at least half the requested samples and reports failed samples. A 19-valid/1-failed run remains a successful report; this is established infrastructure policy and is exercised by the tests, not a new performance regression gate. No calibrated timing threshold is added.

## Style

Clean for this scope. English repository prose and commit, ordinary stdlib Python and portable Bash, no unnecessary dependencies or architectural diagrams, no new unsafe/assembly. `actionlint` on both immutable workflows and ShellCheck on all immutable `tools/*.sh` return 0; `git diff --check 69ac515 e873995` returns 0. Rust formatting/lint evidence is supplied by the parent and exact-source hosted CI; no Rust source changed.

This is a very large step by the code-review standard. Its size is predominantly two complete administrative/reporting interfaces, their safety tests and task/guide/standard synchronization. ADR-0040 and the maintainer's requested eight-step sequence explicitly bundle both T-035 outputs into STEP 8. The final PR description should explain this approved grouping rather than conceal its size; it is not a request to split the authorized reviewed step now.

## Test coverage

Reviewer-executed checks:

| Check | Result | What it establishes |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 tools/test-branch-protection.py` | 27 passed | Additive/no-op/drift/proof/CLI/CI/policy/transport contracts |
| Same unit suite under `python3 -O` | 27 passed | Production guards and unittest assertions survive Python optimization |
| `PYTHONDONTWRITEBYTECODE=1 python3 tools/test-perf-harness.py` | 6 passed | 20 samples/provenance, overwrite preservation, dirty/unknown status, zero/partial sample behavior, pipeline failure |
| Private `review-controls.py`, normal Python | 87 explicit control cases passed | Actual subprocess argv/stdin methods, credential canary, exhaustive missing policy fields/boolean types, missing GraphQL fields, final-read GraphQL/ruleset drift, captured definition equality |
| Private `review-workflow-controls.py` | 3 passed | Exact immutable workflow collection block: all 20 samples copies report; zero samples fails and retains log; partial report follows canonical threshold |
| `actionlint` both workflows | passed | Workflow syntax/context and embedded shell validation |
| `shellcheck tools/*.sh` | passed | Shell lint at default severity |
| Immutable whitespace diff check | passed | No diff whitespace errors |
| Changed-document relative Markdown file targets | 280 passed | File existence, excluding code examples; anchor contents not asserted |

The independent 87-case script uses ordinary Python assertions and is credited only for its normal-Python execution; the repository's optimization proof above uses unittest and remains meaningful under `-O`. Private scripts never call a real GitHub API. No mutating live T-035 apply was exercised: the captured real apply is a no-op, and writes are proved against private stateful fakes/shims.

The metadata-only harness change does not require a new guest mutation. The parent's real local 20-run report was inspected: 20 valid/0 failed, 100 s, debug, QEMU 11.1.1, pinned Rust, **dirty tracked worktree at base 69ac515**, p10/p50/p90 4.085/4.210/4.505 ms. It is accurately identified as pre-commit local evidence, not clean exact-tip hosted certification.

Exact-tip hosted evidence was independently read from the downloaded files:

- [Performance run 38186988714/job 114611329672](https://github.com/HodeTech/Tyrne/actions/runs/38186988714/job/114611329672): success. Download directory `/tmp/tyrne-b21-step8/hosted-perf-artifact/performance-e8739957ea0a2ceabb33fa7519cadb1a1d2be57e-1/` contains report, full harness output, metadata, Rust/compiler/toolchain and QEMU version files, start timestamp. Report/log/metadata agree on full **e873995**, `development`, **clean**, pinned nightly, Linux x86_64, QEMU 8.2.2, debug, **20 valid/0 failed**, **101 s harness / 139 s evidence / 144 s job**, and p10/p50/p90 **8.409/9.120/12.622 ms**. The 20 raw samples and the printed band agree. Different host bands are not a regression conclusion.
- Service artifact metadata `/tmp/tyrne-b21-step8/perf-artifacts.json`: artifact 11719932471, matching name/full SHA/run, 4180 bytes, creation 2026-10-12T00:12:40Z, expiry 2026-10-26T00:12:40Z. Service-reported digest is `sha256:c6d1d5a59141638093ec9ddcb9af0531022ad77830a904625fddf7f1c2f75f86`; this reviewer does **not** claim to have recomputed the archive digest from the extracted directory.
- [CI run 38186988733](https://github.com/HodeTech/Tyrne/actions/runs/38186988733) is completed/success; captured `/tmp/tyrne-b21-step8/hosted-ci.json` shows all seven jobs green, including all six required gates. A final read-only `gh run view 38186988733 --repo HodeTech/Tyrne --json headSha,conclusion,status,url` independently confirms full e873995 SHA and completed/success. This successful run does not disprove the separately captured intermittent ARM probe failure.

## Documentation

Clean for T-035's declared scope. Guide, infrastructure/testing standards, CI header, task/index/current pointers and local generated report match the implemented mechanism and Accepted ADR-0040. Public administrative commands, exit statuses, app binding, unsupported-policy refusal, no-op behavior, live race limitation, no automatic rollback, schedule best effort/default branch/inactivity behavior, enable/dispatch/download steps, artifact retention and informational status are explained. Old neutral-always-blocks and future-post-T-011 coverage enforcement claims are corrected without inventing a new threshold.

The immutable task's first hosted artifact checkbox was pending when committed; subsequent exact-tip downloaded evidence now discharges that criterion and should be recorded in the correction/evidence commit. Manual dispatch and first merged `main` run remain legitimately pending until the maintainer merge. No task is `Done`, and this review does not authorize a final merge or claim full Phase B.2 completion.

Relevant primary references were checked read-only: [protected-branch REST API](https://docs.github.com/en/rest/branches/branch-protection), [repository rulesets API](https://docs.github.com/en/rest/repos/rules), and [schedule event reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule). Export/check requires the API's applicable read permission; apply requires administration write permission. The narrow update path and source-app identity requirement agree with the API contract.

## Integration

### R1-CODE-01 — Medium, blocking: inherited ARM negative probe accepts only one legitimate diagnostic

- **Location:** `tools/test-ci-gates.sh:61–74`, especially line 74, as present at immutable e873995. This file is inherited from T-036 and is **outside the 15-file T-035 diff**.
- **Observed evidence:** `/tmp/tyrne-b21-step7/registration-tip-failure.log`, hosted run **38186028266**, source **69ac515**. The isolated hello arch-only mutation invokes exact workspace clippy `--all-targets`, and Cargo reports `error: unwinding panics are not supported without std`, then `could not compile tyrne-userland-hello (bin "hello")`. The rejection harness nevertheless fails because it requires only `error[E0152]: found duplicate lang item panic_impl`.
- **Why it is a defect:** The mutation makes both the normal hello binary and its test variant ill-formed on the ARM host. Parallel target compilation can expose the normal no_std/unwind failure before the duplicate panic_impl test failure. The negative assertion therefore turns a legitimate rejection of the intended regression into an intermittent red **required** check. Earlier and exact-tip green runs demonstrate intermittence, not safety of the single-diagnostic assumption.
- **Required correction:** Keep the exact mandatory workspace gate and isolated mutation. Deterministically prove the intended regression, or narrowly recognize both legitimate diagnostic classes with target/source context and controls that reject unrelated errors and unexpected success. Preserve the historical failed run and distinguish a failed command inside an expected-failure probe from an actual red workflow. Re-run local/hosted controls and both fresh round-2 reviewers on the entire correction/cross-step delta.
- **Status:** Parent independently found and verified this issue before receiving this report and is correcting it. This review independently read the failure evidence and source. It is not a new T-035 security vulnerability or reason to downgrade/exclude the existing separate HIGH T-038 asm issue.

No new Cargo/Python package dependency, API rename, syscall/kernel behavior, binary blob or CI administrative credential is introduced. New offline fixtures are included in the existing required fast lane. The performance job remains deliberately outside required checks. Actual policy application is confined to a local narrow endpoint; real T-035 application was a no-op because the six reviewed checks were registered in preceding steps.

### Full code-review checklist

| Standard item | Disposition |
|---|---|
| Correctness | T-035 clean; inherited required-check flake R1-CODE-01 blocks integrated readiness |
| Capability semantics | No OS capability change. Administrative authority remains the local authenticated `gh` principal; fixed target, explicit apply, refusal guards and narrow payload precede effects |
| Fault containment | No userspace/kernel path change. API/measurement/parse failures stay tool/workflow failures; fatal pipeline status preserved |
| Unsafe discipline | N/A: no Rust unsafe, asm or safety contract change |
| Error handling | Typed `PolicyError` plus caught IO/JSON/subprocess failures; no stderr credential echo; no drift fallback; no automatic rollback; API race disclosed |
| Tests | 27 normal/optimized unit cases, 6 synthetic perf, 87 independent normal-Python controls, 3 exact-shell workflow controls, real downloaded guest report; inherited flake requires correction |
| Documentation | Commands/contracts/limitations and evidence stages synchronized; new hosted evidence needs its follow-up task-history recording |
| Architectural principles | P1–P12 explicitly reconciled below |
| Dependencies | N/A: stdlib-only Python, existing platform tools and pinned actions; no crate/package addition |
| Naming/style | English, coherent tool/CLI names, actionlint/ShellCheck/whitespace clean; no style preference finding |
| Commit message | Conventional `ci:` subject within limit, motivation/body and `Refs: ADR-0040`; final PR/review trailers are parent/maintainer work, not fabricated by this read-only reviewer |
| Second security reviewer | Independent paired full pass required and cross-read before report delivery; recorded below |
| Author post-fix sweep | Historical coverage/neutral/protection claims checked in touched source/docs; R1 correction must sweep the old diagnostic-only claim in T-036/guide/tool fixtures |
| PR size | Large approved STEP 8 grouping acknowledged under Style; final PR needs explicit size rationale |
| Merge readiness | No Done/merge approval while R1-CODE-01 remains and required fresh correction reviews have not completed |

### P1–P12 reconciliation

| Principle | Disposition |
|---|---|
| P1 — No ambient authority | OS capability system untouched; local admin operation explicit and GitHub-authenticated; no CI admin token |
| P2 — Small TCB | Host tooling only, no kernel surface growth |
| P3 — Userspace services/drivers | N/A: no subsystem placement change |
| P4 — Trust boundary checks | Admin schema/baseline/proof/final-read checks before PATCH; kernel trust boundaries untouched |
| P5 — Rust kernel | Kernel unchanged; host Python/Bash does not violate kernel-language rule |
| P6 — HAL separation | No architecture details added to kernel; QEMU measurement stays in host tooling |
| P7 — No proprietary blobs | No new binary in source or firmware dependency; generated human-readable local report only |
| P8 — ADRs | Accepted ADR-0040 directly specifies cadence, JSON/classic additive administration and review sequence; no material new policy/threshold |
| P9 — English | Committed source/docs/commit English |
| P10 — Mermaid | N/A: no new diagram |
| P11 — Reproducibility | Pinned Rust/actions, full source/tool metadata, arch-separated cache; timestamps/host paths appear in evidence reports, not kernel binary inputs |
| P12 — Complete scope | Both T-035 interfaces implemented with tests; hosted artifact proved; post-merge-only evidence pending honestly; inherited required-check flake must be fixed before integrated approval |

## Verdict

**Request changes.**

Exactly one blocking integration issue is retained: **R1-CODE-01**, the inherited T-036 nondeterministic negative-probe diagnostic assumption. There is **no additional confirmed finding in the new T-035 code**. The exact-tip hosted performance artifact and seven green CI jobs are verified; they do not erase the separately observed flaky required check. Parent must apply the localized correction, record hosted evidence and submit the full corrected delta to the two fresh round-2 reviewers. Default-branch dispatch/main and final maintainer review remain future evidence; no task is promoted to Done and no final merge is approved here.

### Paired-security cross-read

Read the entire final `/tmp/tyrne-b21-t035-round1-security.md` before issuing this code verdict. The independent security pass approves only the scoped T-035 security delta at the same exact e873995 SHA, with no new actionable security finding; it explicitly corroborates and retains the inherited T-036 integration hold. Its eight axes, 33 checklist dispositions, P1–P12, 72 additional explicit normal/optimized adversarial controls, secret-failure/timeout controls and hosted artifact analysis were read and assessed. The security result agrees with this code review: no new T-035 defect, non-atomic admin races honestly limited, existing HIGH T-038 unchanged/excluded/undowngraded, and correction plus fresh round 2 still required. The security approval is not an overall integration or maintainer approval.
