# Code review 2026-10-12 — PR48 follow-up B, fresh round 2 integration

- **Change:** [PR48](https://github.com/HodeTech/Tyrne/pull/48), immutable cumulative `a1eb406576f4984f563bc45ee5650c2aff0d8f2c..646ba33052632d5afda1e206007ed9bc334e8e3a`, on `development` only.
- **Reviewer:** fresh independent Codex agent `/root/pr48_docs_r2_integration`, acting for @cemililik; all five canonical code-review roles executed sequentially, emphasizing documentation and integration. This is an agent verdict, not maintainer sign-off.
- **Date:** 2026-10-12, Europe/Istanbul.
- **Risk class:** Ordinary documentation, workflow comments and generated report prose. The substantive A assurance changes have distinct historical code/security reviews; this B delta changes no runtime, policy or administrative behavior.
- **Security-review cross-reference:** N/A for a new B security pass. Complete prior A security [R1](../security-reviews/2026-10-12-pr48-tools-followup-r1.md) and [R2](../security-reviews/2026-10-12-pr48-tools-followup-r2.md) are scoped historical context, not reused B approval.
- **Requested model/effort:** `gpt-6-astra`, high effort, fresh `fork_turns=none` was supplied as orchestration configuration metadata; it is not independently attested runtime model identity.
- **Scope:** all 15 changed files, 454 insertions and 28 deletions: 13 Markdown files, full-line YAML comments and five replacement shell echo lines. This complete provisional report is written before waiting for the independent peer; final cross-read follows separately.

## Correctness

**Zero new findings. Both B Round 1 Low findings are resolved at immutable 646ba33.** The entire cumulative scope was inspected afresh, including the original B corrections and the R1 publication/correction commit.

- **PR48-CR-01 resolved:** `tools/perf-harness.sh:569–573` now states the nearest-rank fact: at 100 samples the selected rank is 99; from 100 onward it is below the final rank, while ties may still equal the maximum. It explicitly denies statistical reliability from that transition alone and asks readers to use sample count and measurement context. Integer nearest-rank reasoning supports these statements. The changed shell region replaces two literal `echo` lines with five; all other harness bytes, including calculation, valid-sample threshold, watchdogs, output tables and overwrite refusal, remain identical. This corrects an interpretation claim, not a numeric estimator or performance policy. The dated reconciliation caveat explicitly supersedes the inherited historical sentence while preserving all captured report bytes. The exact-source hosted 646 report visibly contains the corrected paragraph.
- **R1-INT-01 resolved:** reconciliation line 74 now attributes MP-1 to later review artifacts and MP-33 to some earlier artifacts. The security master plan's kernel-discipline list has an unnumbered typed-allocation-exhaustion requirement; its source contains neither literal label. Full A R1/R2 reports and relevant T-030 passages establish their shared meaning after the 32 standard items, for 33 total dispositions. No historical checklist or verdict is rewritten.
- **Guide commands and gate counts:** both coverage examples exclude BSP and both userland crates, matching the real workflow. Plain repository-local Cargo selects `nightly-2026-01-15`; explicit `+stable` remains distinct. ARM order is check, clippy, private arch-only rejection probe, native test, Miri setup, Miri test. Four gates correctly means check/clippy/test/Miri, with two supporting operations. Only BSP is excluded from the ARM commands. The fast-lane table now names all four fixture families actually invoked.
- **Timing, cache and setup claims:** Miri's 1–2 minute duration is explicitly observed, not guaranteed; parent-acquired exact 646 summaries show 68/76 seconds and earlier 5816 summaries show 92/85 seconds. All exact cache keys include OS, architecture, toolchain identity and lockfile hash; restore prefixes omit that hash while retaining OS/architecture/toolchain. The stable lane's identity is the rolling stable channel, not an immutable compiler. Actual path lists omit cargo-bin, while registry/git/target remain trusted build inputs. Each workflow repeats installation/cache setup directly; no shared composite action is present. Monday 03:17 UTC matches the cron expression.
- **Policy and boundary truth:** six required display names, app ID 15368, strict checking, admin enforcement false, approval count 0 and code-owner review false match committed policy. The guide distinguishes producer identity from workflow/source integrity, and GraphQL review enablement from REST approving count. The supplied instant-success duplicate-name bypass is not established. Duplicate names can produce ambiguity; no hosted bypass experiment is claimed. No new CODEOWNERS, environment, ruleset, approval or admin-enforcement policy is adopted.
- **Capacity and response shapes:** per-workflow/ref cancellation does not cap separate PRs. Smoke/ARM have 10/15-minute bounds; organization billing/approval/capacity controls are expressly unverified. The captured REST response is dated observed-shape coverage, not permanent live equality or universal compatibility. Normalizer tests preserve the complete policy and refuse unknown enforcement/actor and branch-summary extensions. Source inspection confirms narrow metadata stripping, strict fields, independent GraphQL/ruleset reads and non-atomic reread/PATCH/readback. B does not change these paths or claim atomicity.
- **Smoke and history:** T-034 uses the actual `Undefined Instruction` token matching source and fixtures, without claiming exhaustive CPU-fault or exact SVC coverage. Its original four-check count is marked as an opening snapshot against current six-check policy. T-033's five-role map matches original numbered headings and is strictly additive. T-030's index names both actual review ranges. The ADR-0040 artifact remains an approval review using its dedicated template; indexing it here does not invent a different review type.

## Style

**Clean.** New prose is English with normal word/number spacing and stable exact tokens. UTC-only wording is an ordinary simplification; the UN's English-language use of the official country name refutes the supplied language-violation allegation. Workflow comments describe present behavior without changing YAML execution. ShellCheck 0.11.0, actionlint 1.7.12 on both explicit workflow paths and immutable-range whitespace validation pass.

Both cumulative commits use Conventional Commits, explain the scope and cite existing ADR-0013/0040. R1 review trailers point to real artifacts and do not pretend to approve subsequent bytes. There is no Rust style, unsafe annotation, diagram or dependency addition needing separate treatment. No unrelated formatting/refactoring is requested.

## Test coverage

Tests were read before supporting implementation: complete seven-method performance suite, relevant policy equality/refusal tests and smoke fixture definition, then source paths/workflow callers and cumulative changes. No test source changes in B. The generated prose change warrants scoped fixtures, source/output inspection and arithmetic; broad Rust/Miri/QEMU reruns would not validate the wording and were not performed.

### Independently executed checks

| Check | Result and limit |
|---|---|
| `python3 tools/test-perf-harness.py` | 7 methods pass, 6.695 s; synthetic samples, report metadata/privacy, overwrite, dirty/unknown source, failure and tee controls |
| `python3 -O tools/test-perf-harness.py` | 7 methods pass, 6.485 s; top-level unittest assertions remain active; child stub interpreters are not all automatically optimized |
| `shellcheck tools/*.sh` | Pass at default severity, version 0.11.0 |
| `actionlint .github/workflows/ci.yml .github/workflows/performance.yml` | Pass, version 1.7.12 |
| `git diff --check <full base> <full head>` | Pass |
| Selected preservation corpus | 243 existing files byte-identical across the immutable range: runtime source, tools except the generator, ADRs, audits, old reports, non-index reviews except T-033, policy, manifests/toolchain and performance workflow |
| T-033 original-body preservation | Original 46,939 bytes are an exact prefix; 7 appended lines only |
| Workflow content invariant | Removing full-line comments yields byte-identical base/head content; no command/job/trigger/permission/cache/run-body change |
| Harness content invariant | Sole replacement is 2 literal echo lines with 5; all other bytes, numeric algorithm and thresholds identical |
| Local Markdown links | Scanner checked 393 relative-link occurrences and 38 fragments across all 13 changed Markdown files: zero missing targets/anchors; fenced/inline code examples excluded. Local validation, not external uptime or browser rendering |
| Original performance digest and raw arithmetic | Preserved 50ab snapshot SHA-256 `24c143abb0151de1eb3fb38ff3d74f3e060effd2a6c492cc8389bebca565ae85`; all 20 raw samples reproduce nearest-rank p10/p50/p90 5,232,672 / 5,473,392 / 7,277,776 ns |
| Task/source inventory | T-030 through T-037 remain In Review; T-038 remains Ready/open. HEAD is full 646ba33 and worktree clean |
| Targeted old-token sweep | Old active-guide spacing, wrong fault token, sibling-cache contrast and unsupported p99 generator sentence absent from live targets; dated historical rows intentionally retain original text |

The exact source was read from the shared clean 646 worktree and cross-checked against immutable Git blobs. The performance suite creates only disposable private fixtures and was not permitted to create a repository report. No checkout, commit, push, shared guest build, live policy operation, API mutation, external comment or message was made. Review output is confined to `/tmp`; the coordinator owns canonical publication/index/trailers.

Preserved SHA-256 values independently recomputed: ADR-0040 `5b82f632157033d193e64ac554390bacb9944fcd7a79fac9760a666c5f02ff2c`; policy `edd66dad0b4591c937556be55f6c473bf87e23173cde931c53347b6dc88b8a5b`; adapter `747b196e11e21340d0a7d607c7699fd129d58f9df54b96199ff6bad6907a55bd`.

### Parent-acquired hosted evidence independently inspected

The coordinator acquired the following JSON summaries and downloaded performance artifact; this reviewer independently parsed/read them and recomputed report arithmetic/digests. These are not this reviewer's API retrieval, hosted execution, artifact download or archive authentication.

| Run | Independently inspected binding and result |
|---|---|
| [PR CI 38214402250](https://github.com/HodeTech/Tyrne/actions/runs/38214402250) | `pull_request`, full `646ba33052632d5afda1e206007ed9bc334e8e3a`, completed/success, all 7 jobs success |
| [Push CI 38214395496](https://github.com/HodeTech/Tyrne/actions/runs/38214395496) | `push`, same full source, completed/success, all 7 jobs success |
| [Performance 38214395500](https://github.com/HodeTech/Tyrne/actions/runs/38214395500) | `push`, same full source, completed/success, informational report job success |
| Prior [PR 38213061361](https://github.com/HodeTech/Tyrne/actions/runs/38213061361) / [push 38213057506](https://github.com/HodeTech/Tyrne/actions/runs/38213057506) | Full historical 5816 source, expected events, completed/success and 7 successful jobs each; not relabeled as 646 proof |

Full downloaded 646 report and metadata identify clean tracked source, pinned compiler/toolchain, QEMU 8.2.2, 20 valid / 0 failed samples, 101 s full harness wall time and 139 s enclosing evidence interval. The corrected rank/ties/no-reliability paragraph is present. Recomputed report-file SHA-256 is `dab24e41b0bc954f09b29cc942bbf962d552bf7763a92b1d6d1855918546bc87`. All 20 raw samples reproduce p10/p50/p90 **8,496,720 / 9,820,080 / 12,571,504 ns**; p99 and max both **13,788,672 ns**, expected for n=20. No cross-host regression or calibrated tail reliability follows.

Service artifact metadata names ID 11731885187, 4,187 bytes and source 646. Its archive digest `0c36949212aff61e495fb0c515aa9bdbb5ced3277efed9331bb945e14742217c` is service-reported, not locally recomputed. The downloaded report is not yet a committed snapshot at the reviewed head; future exact-byte publication belongs to the coordinator and is not pre-certified. Older 50ab report bytes remain unchanged despite their superseded interpretive sentence. First merged-main/default-branch dispatch evidence remains merge-dependent.

**Missing tests blocking this delta: none.** Green hosted runtime checks support integration but do not certify documentation truth, statistical reliability or existing unsafe contracts.

## Documentation

**Clean; both R1 corrections verified.** The new reconciliation is plainly an author disposition, not an independent approval, promotion or phase closure. R1 reports retain both Low findings open at 5816 and append coordinator disposition; R2 assesses actual corrected 646 source. Accepted ADRs and historical reports are byte-preserved. The additive T-033 note maps existing roles without replacing its original verdict. The approval skill was read as evidence for template identity, not invoked to perform a promotion review.

### All 17 supplied dispositions

| ID | Independent assessment |
|---|---|
| M-1 | English-language violation refuted by the UN English reference; UTC simplification valid |
| M-2 | Producer/workflow integrity boundary documented; specific duplicate bypass unproved; no unauthorized policy tightening |
| M-3 | Observed protection-endpoint fixture and conservative limits accurate; current failure was not established by the supplied report; no authority-field stripping |
| L-1 | Current targeted spaces corrected; historical text retained |
| L-2 | Coverage exclusions, pinned Miri, observed duration, keys versus prefixes, setup, fixture table and ARM order/count aligned |
| L-3 | Current task note matches actual Undefined Instruction matcher and both-profile fixture token |
| L-4 | A's four optional metadata fallbacks retained; B accurately limits the claim to valid measurements and optional metadata |
| L-5 | Nonempty diagnostic guard precedes negative command execution in retained A source |
| L-6 | T-033 additive role map and T-030 separate ranges correct; approval template identity valid; corrected MP-label attribution resolves R1-INT-01 |
| L-7 | New normal hostname/override explanation omitted; no universal or retroactive redaction claim |
| L-8 | Same exact clean clippy baseline precedes six-cfg mutation and bounded exit-101/exact-diagnostic test; external nondeterminism/hostile tools excluded |
| I-1 | Header policy boundaries honest; distinct GraphQL review enablement/REST count retained |
| I-2 | A removed five cargo-bin paths; B acknowledges remaining build-cache trust and ordinary PR cache scope |
| I-3 | Per-ref cancellation/job bounds actual; external approval/billing/capacity controls unverified |
| I-4 | Agent provenance is recorded configuration/context, not runtime identity attestation or maintainer signature |
| I-5 | Internal ci-nightly title and repository context filename intentionally differ to preserve exact bytes; digest matches |
| I-6 | Opening four-check reference now qualified against current six-check policy |

The actual PR body was read via `gh pr view 48` before the diff. Its older validation counts and final-tip paragraph describe prior intent/evidence, not this range's exact head. The pinned review assignment and exact-source summaries above establish current scope. No author claim or prior reviewer verdict substitutes for this pass.

Primary references were opened directly to verify external semantic claims: [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) supports admin exceptions, source-app selection, accepted check conclusions and duplicate-name ambiguity; [cache reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching) supports same-PR merge-ref reuse with base/sibling exclusion; [protection API](https://docs.github.com/en/rest/branches/branch-protection) and [branch API](https://docs.github.com/en/rest/branches/branches) identify distinct endpoints; [UN English announcement](https://turkiye.un.org/en/184798-turkeys-name-changed-t%C3%BCrkiye) supports the language disposition. Repository policy facts come from the unchanged definition and adapter, not inference that external pages attest this repository's live state.

## Integration

Full prerequisites were read: supplied and actual AGENTS guidance, complete CLAUDE/current roadmap; all 39 actual numbered ADRs in numerical order (0001–0033, 0035–0040; 0034 absent); all 15 standards including README; skills inventory, full perform-code-review/conduct-review skills and complete code master plan/output template. The supplied 107-line systematic report, actual PR body, all four complete A code/security R1/R2 reports and both complete B R1 reports were read. Relevant original T-033 headings, T-030 range/checklist locations, full ADR-0040 approval artifact and full approval skill establish historical mappings. The security master plan's actual allocation list was checked directly. This is the full ordinary code checklist below, not a claimed new 33-item security review.

Long-output truncations were recovered with bounded reads. During governance preread the current-roadmap overlap at lines 86–95 was reread; numbered ADR reads used bounded full-file groups with no lost tail. The cumulative non-report diff exceeded the tool budget; complete guide and T-035 hunks were subsequently reread separately, recovering the omitted middle. All new report bodies were read in full. No unresolved output gap is accepted as review coverage.

No runtime symbol/caller, unsafe/assembly/audit contract, dependency/toolchain/action pin, workflow executable content, token scope, accepted decision or live protection state changes. The sole executable-file delta emits explanatory prose and has no numeric or timing-policy change. This remains ordinary risk, with no new security-sensitive implementation that would require an invented B security pass. All eight tasks stay In Review; existing HIGH T-038 x2 clobber remains open/excluded. Nothing here treats host tests/Miri/smoke as proof of that assembly contract. Other B.2 tracks and the whole-phase C/D gate remain intact.

### Complete code-review checklist

| Item | Disposition and basis |
|---|---|
| Correctness | Pass; all cumulative descriptions checked against implementation/evidence; both Low R1 issues fixed |
| Capability semantics | Runtime N/A; administrator/workflow/actor-field trust boundaries preserved and accurately qualified |
| Fault containment | Runtime unchanged; configured smoke token honestly described without exhaustive claims |
| Unsafe discipline | N/A to changed source; no unsafe/asm/audit edits; HIGH T-038 remains excluded/open |
| Error handling | No new Result/error path; fail-closed policy/negative controls and optional metadata boundaries accurately represented |
| Tests | Pass; 7-method normal/optimized fixtures, lints, links, exact-byte/arithmetic invariants and attributed hosted evidence |
| Documentation | Pass; all 17 dispositions, dated historical p99 correction and true MP-label source; old captures preserved |
| Architectural principles | All P1–P12 considered individually below |
| Dependencies | N/A; no graph, action, toolchain or trust-policy addition |
| Naming/style | Pass; English, normal spaces, exact tokens, Conventional Commits and lints |
| Commit message | Pass; valid ADR-0013/0040 references and real R1 artifact trailers; coordinator records R2 separately |

### Architectural principles P1–P12

| Principle | Disposition |
|---|---|
| P1 No ambient authority | Preserved; no grant or CI admin credential, existing bypass explicit |
| P2 Smallest defensible TCB | Preserved; no privileged source growth |
| P3 Drivers/services in userspace | N/A; no placement change |
| P4 Capability checks at boundaries | Runtime unchanged; policy-bearing fields remain authority data, app identity distinguished from workflow integrity |
| P5 Rust-only kernel | Preserved; no kernel/assembly/unsafe change; existing T-038 not certified |
| P6 HAL separation | Preserved; no interface/dependency/hardware placement change |
| P7 No proprietary blobs | Pass; text-only delta, no binary/firmware |
| P8 Recorded decisions | Pass; corrections implement Accepted ADR-0040 without a new decision or historical rewrite |
| P9 English repository | Pass; changed prose English, country-name overclaim refuted |
| P10 Mermaid diagrams | N/A; no diagram/image added |
| P11 Reproducibility | Preserved; pins, old report bytes/source IDs retained; numeric calculations unchanged and bands/digests verified |
| P12 Complete declared scope | No runtime stubs; tasks remain In Review, phase/HIGH/first-main/dispatch boundaries explicit |

## Verdict

**Approve for ordinary cumulative follow-up B at immutable 646ba33. Zero new Blocker, High, Medium or Low findings. Blocking list: none.** PR48-CR-01 and R1-INT-01 are resolved at this exact head. All five roles, the complete ordinary checklist and P1–P12 are covered.

This approves the reviewed source and evidence wording, not future publication bytes, whole-kernel safety, maintainer merge, task promotion or Phase B.2 closure. All eight tasks remain In Review. Existing HIGH T-038 and first-main/default-dispatch evidence remain open. The full independent provisional report is complete before peer waiting; full peer cross-read will be appended before final handoff.

## Paired-review reconciliation

After completing the independent provisional report, read the entire 160-line `/tmp/tyrne-pr48-docs-r2-code.md`. The fresh peer independently Approves the same immutable cumulative range with zero new findings and both R1 Low corrections resolved. Its five roles, complete ordinary checklist, P1–P12, all 17 dispositions, historic preservation, task/HIGH/merge boundaries and exact-source evidence attribution agree with this review.

The peer additionally generated four private synthetic reports at distinct N = 20/99/100 and tied N = 100, checking numeric p99 and emitted wording together. Those are peer-executed controls, not this reviewer's tests. The peer's selected preservation corpus contains 246 files; this review's independently defined corpus contains 243. Both explicitly selected subsets rather than whole-repository counts, with the changed files separately inspected; this is not a conflicting source inventory. Both link scanners report 393 relative links and 38 fragments. No unresolved finding, verdict or scope disagreement emerged.

Final verdict remains **Approve, zero new findings, both Low R1 issues resolved at 646ba33**. Canonical recording belongs to the coordinator. The peer's final cross-read addendum will be read before final handoff; no future source is preapproved.

The complete final 164-line peer artifact was subsequently reread in full, including its final paired reconciliation. It confirms matching Approve, zero new findings, both R1 fixes and no unresolved conflict. Final peer cross-read is complete; this report is ready for coordinator publication with the same scoped verdict and limitations.

## Coordinator publication

The complete report above is published with the [paired canonical B Round 2 report](2026-10-12-pr48-docs-followup-r2.md). Private paths identify ephemeral acquisition/execution locations. The coordinator read both complete final reports and reconciled their matching Approve verdicts, zero new findings and verified PR48-CR-01/R1-INT-01 corrections at full `646ba33052632d5afda1e206007ed9bc334e8e3a`. Both fresh B rounds are complete; follow-up A already completed its distinct code/security rounds. This publication does not extend either verdict to later bytes, merge PR48 or promote tasks. Exact final publication-tip CI is checked separately.
