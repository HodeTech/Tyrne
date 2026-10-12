# Code review 2026-10-12 — T-035 CI hygiene tail

- **Change:** approved Track B.2-1 step8, `69ac515..e873995`; later T-036 integration correction recorded below.
- **Round1 reviewers:** fresh `b21_step8_round1_code` (`gpt-6.1-sol` / high requested) and distinct `b21_step8_round1_security` (`gpt-6-astra` / high requested), empty inherited context. Configuration provenance, not runtime identity attestation.
- **Paired artifact:** [security review](../security-reviews/2026-10-12-t035-ci-hygiene-tail.md).

> **Current reconciliation:** Both fresh rounds complete. R1 code Request changes for inherited Medium R1-CODE-01; scoped T-035 security Approve. Coordinator verified and fixed the ARM diagnostic race, with permanent exact-class/exit101 refusal controls and an old-code negative control. Fresh R2 code/security both Approve the whole combined delta with zero new finding; full reports read and retained below. Corrected hosted run38187736985 passes all seven jobs and actually exercises the formerly rejected unwind class. Downloaded debug/release guest and23-control evidence passes. First performance artifact at clean e873995 is verified; workflow/harness bytes are unchanged by the later fix. Existing HIGH T-038 remains excluded/undowngraded. Final entry-doc integration, maintainer PR and merge-dependent evidence remain separate; tasks stay In Review.

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

## Round2 — code

# Code review 2026-10-12 — T-035 Step 8 and late T-036 correction, fresh Round 2

- **Change:** full immutable combined delta `69ac515393f8f20ff0a11587a309182388bcde51..7deb16eae6274d48391c6c6525515a4e8bbdd66f`, `development`; 23 files, 1643 insertions, 54 deletions. Includes the complete T-035 implementation at e873995 and the subsequent diagnostic correction, tests, provenance and documentation at 7deb16e.
- **Reviewer:** independent Codex agent `/root/b21_step8_round2_code`, acting in all five code-review roles sequentially for the maintainer. This is reviewer attribution, not maintainer approval or runtime model attestation.
- **Risk class:** Security-sensitive host administrative authorization boundary. No production Rust, assembly, unsafe contract, Cargo manifest or lockfile change.
- **Security-review cross-reference:** `/tmp/tyrne-b21-t035-round2-security.md`; final full cross-read recorded with the verdict below.
- **Boundary:** no repository edits, commits, branches, live policy export/apply or API writes by this reviewer. Immutable `git archive 7deb16e` under `/tmp/tyrne-b21-round2-code-private`. Only local fake services/temp files were mutated. The only authenticated network commands were read-only `gh run view` calls; official public GitHub documentation was also read.

Read AGENTS first, full CLAUDE and current roadmap, all 39 numbered ADRs in numerical order (0001–0033,0035–0040; no 0034 file), all 15 standards, skill index, `perform-code-review` and `conduct-review` skills and full code master plan. Truncated prerequisite output was recovered in bounded reads. Read both complete canonical T-035 Round 1 reports, T-035/T-036 tasks and the late T-036 reconciliation before reviewing. Description and tests preceded implementation; then definition/schema/normalization, transport/reconciliation, shell/harness and workflow callers were traced in dependency order. All five roles, the entire standard checklist and P1–P12 are disposed below.

## Correctness

**No new confirmed actionable finding in the full combined delta.** The inherited Medium R1-CODE-01 is corrected by the reviewed change and independently verified.

### Administrative definition and tool

- `.github/branch-protection/main.json` preserves the six existing exact context/app pairs (all app15368), strict checking, nine REST toggles, review settings/count, null restrictions, GraphQL-only applied-rule review/deployment/restriction/actor baseline and empty rulesets. It equals the parent-captured `/tmp/tyrne-b21-step8/live-export.json` byte-semantically after JSON parsing.
- `tools/branch-protection.py:57–146` validates exact required fields and types, duplicate object keys/contexts, positive explicit app IDs and supported representation. Unknown fields, bool/int confusion and unsupported actor/deployment/restriction extensions fail closed. Sorting contexts preserves bindings. Known response URL/duplicated contexts metadata is normalized without dropping unknown policy.
- `tools/branch-protection.py:154–176` fixes hostname, repository, branch and API endpoints. `gh` receives argv, explicit methods, timeout and stdin JSON; there is no shell interpolation or token in argv. The GraphQL POST is a constant read-only query. Errors do not echo `gh` stderr or captured timeout stderr.
- `tools/branch-protection.py:179–225` preserves every old context/app pair and all non-status/strict policy. Additions require full lowercase SHA and exactly one completed successful check at that SHA from the explicit app. Truncated/duplicate evidence is refused. Complete REST/GraphQL/ruleset comparison occurs before proof, immediately before the narrow status-check PATCH and after a write. Matching desired policy performs two full reads and zero writes.
- Explicit `apply` refuses CI markers even when their values are `false`. Production guards use exceptions, not optimization-sensitive assertions. No CI job obtains administration credentials or runs live reconciliation.
- The operation has no atomic compare-and-swap. Concurrent administration after the final read can still race; the guide accurately records the limitation, requires coordination and avoids automatic rollback. No atomicity guarantee is inferred from the successful controls.

### Performance reporting

- `.github/workflows/performance.yml` implements Monday03:17UTC, dispatch and development pushes limited to the workflow/harness paths, with no PR trigger. It is separate and informational, has contents-read permissions, nonpersistent checkout credentials, immutable action pins, architecture-separated performance cache and ten-minute outer timeout.
- Matching debug userland precedes debug kernel build. Explicit Bash preserves a fatal harness status through `tee`; one fixed-form report path is required before copying. Always-run wall metadata and artifact upload preserve available diagnostics with 14-day retention. Runner loss/cancellation can still prevent delivery; this is not guaranteed archival.
- `tools/perf-harness.sh` changes only source/tool provenance: full SHA, tracked worktree state, active compiler/toolchain in summary/report. Missing Git status becomes unknown rather than clean. Existing sampling/watchdog/statistics/failure-threshold/append-only behavior remains unchanged.
- A partial set meeting the existing ceil(n/2) threshold is reported with explicit valid/failed counts; it is not a performance-regression threshold. Exact workflow controls demonstrated 20/20 and 19/20 report success, zero-sample failure with retained output and rejection of an unexpected report path.

### R1-CODE-01 resolution

`tools/test-ci-gates.sh:52–74` now requires the ARM command to return compiler exit101 and a full-line match to either observed class: duplicate `panic_impl` or unsupported no_std unwinding. It prints the class actually matched. The exact workspace all-targets clippy command, all six hello cfg mutations, unchanged build script/shim, private Cargo target and host/anchor guards are preserved.

The two failure classes arise from the same isolated cfg regression, with Cargo able to report normal binary or test-target failure first. An unrelated exit101, a near-match diagnostic, wrong status even with a recognized diagnostic, or command success is rejected. Recognition is deliberately narrow rather than any nonzero-exit acceptance.

Independent proof:

1. Nine permanent offline methods pass normally and under Python `-O`, including both classes and refusal/isolation/cleanup contracts.
2. A private control replaces only the copied shell with immutable base69ac515 bytes: the unwind fixture fails the old single-class assertion and passes corrected7deb bytes.
3. An actual native Apple ARM run of immutable7deb shell/source, with only immutable Git file enumeration supplied privately and actual installed rustc/Cargo, returns harness0 after compiler101/E0152. Temporary source was not changed and scratch was empty afterward.
4. Corrected hosted [run38187736985 / ARMjob114613632255](https://github.com/HodeTech/Tyrne/actions/runs/38187736985/job/114613632255) at7deb actually returns the **other** exact class, `error: unwinding panics are not supported without std`, and the assertion passes. This directly covers the previously observed hosted failure class. Positive workspace clippy precedes the private mutation; native tests and Miri follow and pass.

## Style

Clean. English source/comments/docs and conventional commits with ADR-0040 references. Ordinary Python stdlib and portable Bash; no new package dependency, Rust/unsafe or diagram. Independently executed actionlint on both immutable workflows and ShellCheck over all immutable shell scripts pass; repository immutable-range `git diff --check` passes.

This is a large authorized Step8, predominantly the two ADR-0040 interfaces, fixtures, retained reports and review history. The final PR should explain this approved grouping. Size alone is not a new request to split the maintainer-approved step.

## Test coverage

| Reviewer-executed check | Result and purpose |
|---|---|
| `python3 tools/test-branch-protection.py` and `python3 -O ...` | 27/27 each; admin schema, narrow additive write/no-op, proof, drift, CLI, transport and refusal contracts |
| `python3 tools/test-perf-harness.py` and `python3 -O ...` | 6/6 each; metadata,20samples,overwrite preservation,dirty/unknown state,zero/partial samples and pipeline failure |
| `python3 tools/test-arm-host-probe.py` and `python3 -O ...` | 9/9 each; both compiler classes,wrong status,unrelated/green,host/anchor/copy/CLI,isolation,source preservation,cleanup |
| `/tmp/tyrne-b21-round2-code-controls.py`, normal and optimized | 17/17 methods each: nine inherited ARM methods re-executed plus eight new independent methods with many subcases |
| `/tmp/tyrne-b21-round2-workflow-controls.py` | 2/2 methods: exact immutable collection shell across all/partial/zero samples and invalid report path |
| Real immutable Apple ARM compiler probe | PASS, compiler101/E0152 and harness0; Git enumeration shim only |
| Actionlint, ShellCheck, immutable whitespace | Pass |
| Changed Markdown local file targets | 326 resolve, excluding three literal `](...)` examples and code fences; anchors not mechanically asserted |
| Immutable archive preservation | All tracked file bytes remain equal to `git show 7deb16e:<path>`; actual probe scratch empty; shared development clean |

Additional controls cover missing fields at every nested policy level; invalid wrapper/review types; GraphQL boolean/count type confusion; GraphQL/ruleset changes at final prewrite and postwrite reads; exact GET/POST/PATCH transport/payload/timeout; timeout stderr secret canary; captured-definition equality; multiline full-line/near-match compiler diagnostics; and old-code regression failure. Every prewrite rejection asserts zero fake mutations; postwrite divergence asserts one write and no rollback. Private scripts use unittest assertions and explicit exceptions and remain meaningful under `-O`.

No missing blocking test was identified for this delta. No changed guest runtime warrants repeating every kernel test locally; the new host interfaces have direct synthetic/negative tests, the actual ARM command was repeated, and corrected exact-source hosted CI/runtime artifacts were inspected independently. Tests are not evidence that unchanged HIGH T-038 is sound.

### Hosted and captured evidence

- Independent read-only `gh run view` confirms full7deb SHA, completed/success for [CI38187736985](https://github.com/HodeTech/Tyrne/actions/runs/38187736985). Parent-downloaded JSON lists all seven jobs successful, including all six required checks. ARM log independently verifies native `aarch64-unknown-linux-gnu`, pinned rustc1.94.0-nightly, exact second-class rejection, native366passes/2ignored and Miri366passes/2ignored. Job96s, negative probe7s, Miri setup18s/Miri57s from service timestamps; warnings are not a UB finding.
- Corrected CI smoke artifact independently read: full7deb SHA, clean tracked state, current smoke hash, completed23/23 cases (20synthetic plus3 actual private kernels), real_requested=true, wall97s. Production debug/release traces have exit/completion; debug has greeting, release omits it; no panic/CPU-fault class. Deliberately failed rejection traces and the pipeline-mask probe are expected controls, not production failures.
- Independent read-only `gh run view` confirms full e873995 SHA and completed/success for [performance38186988714](https://github.com/HodeTech/Tyrne/actions/runs/38186988714/job/114611329672). Downloaded report/log/metadata/tool versions agree on clean source, pinned Rust, QEMU8.2.2/Linuxx86_64,20requested/20valid/0failed, harness101s/evidence139s. Parent's whole-job144s is a distinct service duration. Recomputed raw nearest-rank p10/p50/p90 =8,408,784/9,120,416/12,621,792ns; mean/stddev also agree.
- Retained `perf-baseline-2026-10-12-t035-hosted-check.md` is exactly equal to downloaded report bytes. The harness and performance workflow are byte-identical at e873995 and7deb; no extra performance trigger is expected for the correction's untouched performance paths. This is source-bound e873995 measurement evidence of unchanged performance code, not a claim that performance ran at7deb.
- The committed local report is correctly labeled dirty tracked base69ac515, QEMU11.1.1/Apple ARM,20valid/0failed,harness100s. Its band4.085/4.210/4.505ms is not compared across hosts as a regression conclusion.
- Parent-captured live export equals the committed definition; `/tmp/tyrne-b21-step8/live-apply.log` says `PASS: live policy matches; no write needed`. This reviewer did not invoke live export/apply or certify a live mutation. Mutating behavior was exercised exclusively against local fakes.
- Artifact service IDs/digests remain attributed service metadata. No extracted-directory comparison is represented as recomputing a downloaded ZIP archive digest.

## Documentation

Clean for the immutable reviewed scope. CI guide, infrastructure/testing standards, workflow comments, tasks/current/index and both retained reports match behavior. Public commands/statuses, app binding, complete supported policy/refusal, full readback, no-op, administrative race, schedule default-branch/best-effort/inactivity semantics, re-enable/dispatch/download and retention are documented. Coverage's old post-T011/neutral-result claims are corrected without inventing an enforcing floor.

Both full canonical Round1 reports preserve their source-bound verdicts and integration finding. Late T036 reconciliation records the failed hosted run and correction instead of rewriting prior green evidence. Current/task text saying corrected hosted proof/R2 pending was accurate at7deb commit time; parent will reconcile completed evidence after this fresh round. No finding is raised for that honest immutable snapshot.

Manual dispatch/default-branch scheduling and first merged-main proof are correctly deferred until maintainer merge. Final PR remains a separate gate. Tasks remain InReview. The explicitly requested later six-entry integrated documentation update and final maintainer review are outside this review artifact's lifecycle actions, not silently completed here.

Official read-only primary references were checked: [status-check protection API](https://docs.github.com/en/rest/branches/branch-protection#update-status-check-protection), [rulesets API](https://docs.github.com/en/rest/repos/rules#get-all-repository-rulesets), and [schedule events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule). The narrow status endpoint supports explicit app bindings; protection reads use applicable administration-read authority, writes administration-write. No live-policy permission was used by this reviewer.

## Integration

No new integration blocker. New offline scripts run in the existing required fast lane; performance remains excluded from required checks; required display names agree with versioned policy. No crate/package dependency, public Rust symbol rename, guest behavior, unsafe audit argument or binary blob change. The old ARM false failure is corrected without weakening the mandatory positive commands or mutation.

Existing **HIGH T-038** x2 clobber mismatch is excluded, unchanged and undowngraded. Passing host/Miri/QEMU or these reviews does not clear it. B.2 whole-phase closure, task Done promotion and final merge are not approved by this scoped review.

### Full code-review checklist

| Item | Disposition |
|---|---|
| Correctness | Clean; R1-CODE-01 corrected, no new actionable issue |
| Capability semantics | No runtime change; explicit authenticated local admin authority, fixed target, narrow effects |
| Fault containment | No guest change; transport/validation/harness failures remain failures, pipefail retained |
| Unsafe discipline | N/A: no changed Rust/assembly/safety argument; HIGH T038 unchanged |
| Error handling | Explicit PolicyError/typed validation and subprocess/IO handling; no credential stderr, permissive fallback or rollback |
| Tests | All new suites normal/-O, independent adversarial controls, old-code failure, actual ARM and hosted evidence pass |
| Documentation | Source-bound history/contracts/limits/evidence stages aligned; post-round reconciliation remains coordinator work |
| Architecture | All P1–P12 disposed below; no new guest architecture |
| Dependencies | Stdlib host tooling, existing GitHub CLI/QEMU/Rust and immutable Actions pins; no dependency addition |
| Naming/style | English/coherent; actionlint/ShellCheck/whitespace pass; no preference findings |
| Commit messages | Both Conventional/English/imperative, subjects within72chars, ADR0040Refs; review trailers preserve prior source-bound verdicts |
| Second security review | Fresh independent full paired pass cross-read before final verdict; recorded below |
| Author post-fix sweep | Current guide/testing/task/tool claims use two-class rule; earlier one-class wording stays in clearly dated immutable reports |
| PR size | Authorized complete Step8 grouping acknowledged; explain in final PR |
| Merge readiness | This review approves its immutable scope only; final maintainer PR/default-branch evidence remain separate |

### P1–P12

| Principle | Disposition |
|---|---|
| P1 no ambient authority | Explicit local GitHub admin operation; no CI admin authority or runtime grant |
| P2 smallest TCB | Host tooling only; kernel TCB unchanged |
| P3 userspace drivers | N/A; no placement change |
| P4 trust-boundary checks | Schema/baseline/app proof/final full read precede narrow write; strict rejection guards |
| P5 Rust kernel | Kernel unchanged; host Python/Bash does not alter language policy |
| P6 HAL isolation | No architecture-dependent kernel code; host QEMU evidence only |
| P7 no proprietary blobs | No opaque guest/firmware binary added; source-built images and text evidence |
| P8 ADR decisions | Accepted ADR0040 governs cadence/classic policy/additive local administration/review sequence |
| P9 English | Source/docs/commits English |
| P10 Mermaid | N/A; no new diagram |
| P11 reproducibility | Pinned Rust/actions,full SHA/tool/dirty-state metadata,arch-scoped caches; rolling host/QEMU recorded |
| P12 complete scope | Both T035 interfaces implemented/tested; inherited flake corrected; tasks InReview, future main/dispatch/PR gates retained |

### Subsequent history-only integration

After this review's source was frozen, the coordinator incorporated the actual remote main ancestry with `cfc8872f85fca6c48d31dbc1bb5cf7dbe174c251`. Independently checked `/tmp/tyrne-b21-step8/history-sync.log`, both commit tree IDs and an empty full-tree diff: 7deb16e and cfc8872 share `8df6fbcdcadfa613c6e900a06a8690b05e9e9921`. The review remains explicitly anchored to 7deb16e. This ancestry-only commit changes no reviewed source bytes; later documentation/evidence and final PR checks retain their own review/validation stages.

## Verdict

**Approve — the complete combined delta `69ac515393f8f20ff0a11587a309182388bcde51..7deb16eae6274d48391c6c6525515a4e8bbdd66f`.**

All five code-review roles are clean. No new actionable code finding or blocker was established. **R1-CODE-01 is resolved**: the exact intended regression is still rejected, both observed compiler classes are narrowly recognized with exit101, unrelated/green/tool failures are refused, the old assertion fails the new fixture, and the corrected second class is proven by actual hosted ARM execution.

Before finalizing this verdict, read the **entire finalized 165-line / 31,414-byte fresh paired security report** `/tmp/tyrne-b21-t035-round2-security.md` in three bounded chunks, including all three evidence-only refinements after the initial cross-read (identical-tree ancestry, explicit performance sample counts and ARM checkout source identity). Final security report SHA-256: `0cc1700baca6b77830cc204b1188ee33da376e33530a3d5bac647f5bbde50e3c`. It approves the same full combined immutable range with no new finding, explicitly covers all eight axes/33 checklist dispositions/P1–P12, records 32 independent administrative attacks and five diagnostic lookalikes, preserves evidence provenance and the documented non-atomic administrator race, and retains HIGH T-038. Its conclusions and limits agree with this independent code pass. No unresolved paired finding remains.

This approves the scoped immutable implementation and correction for the next authorized integration step. It does **not** promote any task to Done, close all of Phase B.2, approve final maintainer PR/merge, or claim future default-branch dispatch/first-main proof. Existing HIGH T-038 remains excluded, open and undowngraded. Coordinator publication, the requested integrated six-entry documentation update and final PR gates remain separate work.
