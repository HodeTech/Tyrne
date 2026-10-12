# Code review 2026-10-12 — PR48 follow-up B, round 1 integration

- **Change:** [PR48](https://github.com/HodeTech/Tyrne/pull/48), immutable `a1eb406576f4984f563bc45ee5650c2aff0d8f2c..5816c934a4d28fa66774b73b46047bd0d652b724`, development only.
- **Reviewer:** fresh independent Codex agent `/root/pr48_docs_r1_integration`, acting for @cemililik; all five canonical roles executed sequentially, with emphasis on documentation integration. This is an agent verdict, not a maintainer signature or runtime model attestation.
- **Date:** 2026-10-12.
- **Risk class:** Ordinary prose and YAML comments. The delta documents existing security boundaries without changing executable behavior or policy.
- **Security-review cross-reference:** no new security implementation pass required for B. The complete A [security R1](../security-reviews/2026-10-12-pr48-tools-followup-r1.md) and [security R2](../security-reviews/2026-10-12-pr48-tools-followup-r2.md) were read as historical scoped context, not reused B approval.
- **Scope:** all 12 changed files, 138 insertions and 26 deletions. No repository mutation, checkout, commit, push, administrative API write, PR comment or external message was performed. Only this temporary review artifact is written; coordinator owns canonical publication/index/trailers.

## Correctness

**B's changed claims are supported.** The guide now matches the actual coverage command's BSP plus two userland exclusions. Plain `cargo miri test` selects the pinned repository toolchain, while explicit stable remains distinguished. ARM order matches the workflow: check, all-target clippy, private rejection probe, native test, Miri setup, Miri test. Calling check/clippy/test/Miri the four gates is accurate despite the two supporting commands. The fixture failure list now includes all four suites actually run in the fast lane.

All exact cache keys include OS/architecture/toolchain identity and lockfile hash; restore prefixes retain OS/architecture/toolchain while omitting that hash. Stable uses the `stable` channel identity, not an exact immutable compiler version. Every actual cache path list omits cargo-bin. The source repeats setup in each job and contains no composite action. UTC cadence agrees with `17 3 * * 1`. Observed Miri timing is explicitly an observation, not a guarantee: coordinator-acquired exact-head PR/push summaries show 92 and 85 seconds respectively.

The 17-item author reconciliation distinguishes corrections from refuted overclaims. It does not certify itself as an independent review. M-1 is correctly refuted as a language violation: the [UN's English announcement](https://turkiye.un.org/en/184798-turkeys-name-changed-t%C3%BCrkiye) uses the official country name; UTC simplification requires no constitutional repair. M-3's actor/enforcement fields carry policy; the source's exact-schema validation and fixture tests continue refusing them. The fixture covers a dated observed endpoint body, not every REST response or permanent live equality. Review enablement and approval count are separately represented; count zero remains explicit. The statement about the prior live check is historical evidence from the A reports, not a live operation performed by this reviewer.

**New finding PR48-CR-01 — Low, nonblocking, independently corroborated from a coordinator-supplied CodeRabbit lead:** the inherited generated methodology at `tools/perf-harness.sh:565–570`, reproduced in `docs/analysis/reports/perf-baseline-2026-10-12-t035-pr48-followup-hosted-check.md:45–50`, says p99 becomes statistically informative at `n >= 100`. At n=100 the formula only selects sorted index 99, the second-highest observation; at n=20 and n=99 it selects the maximum. Crossing that index boundary provides no general sampling reliability guarantee. This is a prose overclaim, not evidence that the nearest-rank calculation or the recorded 20-sample p10/p50/p90 is wrong.

Reproduction: inspect the two generator echo lines at 569–570 and the historical report's corresponding statement; evaluate `ceil(0.99 * n)` for 20, 99 and 100. A search finds the same inherited wording in earlier historical baselines. Correct future generated prose to explain only the rank behavior and caution that tail estimates require substantially more samples and context. Add an explicit dated caveat to the current reconciliation identifying the historical overclaim, while retaining all snapshot bytes/digests. No percentile algorithm, sample-validity threshold, regression policy or ADR change is needed. The generator is unchanged by the present B delta, but the parent explicitly requested disposition as part of B's evidence reconciliation. **Open at immutable 5816c934**; a planned correction is not certified here.

No new Blocker, High or Medium finding was established.

## Style

**Clean for the changed prose/comments.** The conventional commit `docs(ci): reconcile PR48 review claims and current guidance` has valid ADR-0013/0040 references. Actionlint on both explicitly named workflows and immutable-range whitespace checking pass. New text uses ordinary English prose and correct spacing. The old tokens `binding15368`, `count0`, `remains0`, `Monday03`, `Steps1`, `Step8`, `run381`, and `CI381` no longer occur in the four live guide/standard/phase/task-index files targeted by the sweep. Dated task histories and source-bound reports intentionally retain their historical text; broad editorial rewriting would weaken provenance. No new diagram, Rust style, unsafe annotation or dependency issue applies.

## Test coverage

No executable logic changes in B, so a broad Rust/Miri/QEMU rerun is not proportionate. Tests and relevant assurance implementations were read as supporting evidence: protection fixture equality/unknown-policy refusal, ARM clean-before-six-cfg mutation and exit/diagnostic controls, and the complete seven-method performance suite before its relevant generator source. Existing A executions remain attributed to their original reviewers.

### Independently executed checks

| Check | Result and limits |
|---|---|
| `actionlint .github/workflows/ci.yml .github/workflows/performance.yml` | Pass; explicit workflow paths avoid discovery ambiguity |
| `git diff --check a1eb406... 5816c934...` (two immutable arguments) | Pass |
| Workflow comment invariant | Removing only full-line `#` comments leaves identical content byte for byte; every changed YAML line is a full-line comment, no YAML scalar/block body changed |
| Preservation across immutable commits | 239 selected existing files byte-identical: tools, ADRs, audits, reports, policy, runtime source and original non-index review bodies, apart from the separately checked T-033 append |
| T-033 additive preservation | Original 46,939-byte report is an exact prefix of the new file; seven appended lines only |
| Changed-document local links | 383 actual relative-link occurrences, including 38 anchors, resolve. Initial simple scanner also reported three literal `](...)` examples inside inline code; inspection identifies these as syntax examples, not links |
| Historical performance snapshot | SHA-256 equals `24c143abb0151de1eb3fb38ff3d74f3e060effd2a6c492cc8389bebca565ae85`; all 20 raw samples independently reproduce nearest-rank p10/p50/p90 5,232,672 / 5,473,392 / 7,277,776 ns |
| Task state inventory | T-030 through T-037 all remain In Review; T-038 remains Ready, with its HIGH defect open and excluded |
| Read-only worktree checks | Clean; reviewed HEAD exactly 5816c934 |

The local-link checker inspects Markdown links outside fenced code and derives heading anchors; the three inline examples were manually resolved rather than counted as defects. This is local target/anchor validation, not a claim that every historical external URL or runtime log is permanently available. Primary external references newly relied on were read directly through the web tool.

Preserved SHA-256 values independently recomputed: ADR-0040 `5b82f632157033d193e64ac554390bacb9944fcd7a79fac9760a666c5f02ff2c`; main policy `edd66dad0b4591c937556be55f6c473bf87e23173cde931c53347b6dc88b8a5b`; protection adapter `747b196e11e21340d0a7d607c7699fd129d58f9df54b96199ff6bad6907a55bd`.

### Coordinator-acquired hosted evidence inspected

Parsed `/tmp/tyrne-pr48-followup/run-38213061361.json` and `run-38213057506.json`: both name full reviewed `5816c934a4d28fa66774b73b46047bd0d652b724`, completed success, respective pull_request/push events, and seven successful jobs. [PR CI 38213061361](https://github.com/HodeTech/Tyrne/actions/runs/38213061361) and [push CI 38213057506](https://github.com/HodeTech/Tyrne/actions/runs/38213057506) are service-summary evidence fetched by the coordinator, not this reviewer's independent retrieval or runtime execution. No B-head performance run is claimed. The retained 50ab snapshot remains evidence for its original source only; its file digest is not authentication of the service archive.

## Documentation

**Historical reconciliation is substantively sound, with the Low p99 caveat and one label-attribution correction below.** The T-033 mapping matches actual R1 sections 3–7 and distinguishes verdict/procedure/checklist sections 1/2/8. It adds discoverability without replacing the original source-bound verdict or the later WFI/spin correction. The ADR-0040 approval follow-up actually uses the dedicated approval skill's verdict/audit/findings/AC/gates/process shape; the skill mandates no separate storage folder. Index clarification is sufficient; inventing a retroactive code-review format requirement would be wrong.

The T-030 security report itself names R1 `8437158..364b746` and R2 `8437158..5cd9ee8`; the previous index's cumulative summary was not a false R1 range. New explicit ranges are clearer. A R1's MP-33 and A R2's MP-1 both label the additional allocation-exhaustion check after 32 standard items; old reports are not rewritten. The security master plan contains the extra requirement, and the reports supply their labels.

**R1-INT-01 — Low, nonblocking: label attributed to the wrong source.** New reconciliation `docs/analysis/reports/2026-10-12-pr-48-supplied-review-reconciliation.md:74` says “`MP-1` in the security master plan.” The actual master plan has an unnumbered allocation-exhaustion bullet at line 68 and contains no `MP-1` label; that label occurs in later review artifacts, including A R2 and T-030 R2. Reproduce with `rg -n MP-1 docs/analysis/reviews/security-reviews/master-plan.md` (no match) and read its kernel-mode list. The equivalence to historical MP-33 and total of 33 dispositions are correct. Change current prose to attribute MP-1 to later review artifacts and identify both labels as referring to the same unnumbered master-plan addition. Preserve original reports. This is source-attribution precision, not a missing review item or new governance rule. Open at immutable 5816c934.

The fault token in current T-034 notes now matches `tools/smoke.sh` and the BSP standard's `Undefined Instruction`. Its four-check opening snapshot is distinguished from current six-check policy. T-035's new row and current/phase/task-index links identify B as implemented but awaiting both fresh rounds. The historical internal `ci-nightly` title remains appropriate for an exact-byte downloaded snapshot; filename context does not silently rewrite generated evidence. Metadata minimization applies to new ordinary report fields, with arbitrary tool output, auxiliary artifacts and old captures explicitly excluded from any universal sanitization claim.

## Integration

The six exact contexts/app binding 15368, strict checking, admin enforcement false, zero approval count and disabled code-owner requirement match committed JSON. No policy or production adapter bytes change. B correctly separates producer-app identity from workflow content/revision integrity. [GitHub's protected-branch reference](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) supports the admin exception, source-app selection and duplicate-job ambiguity; the supplied specific instant-success duplicate-name bypass was neither reproduced nor established here. The adapter's duplicate evidence refusal must not be confused with GitHub's merge behavior. No new CODEOWNERS, environment, ruleset or acceptance decision is made.

The [official cache reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching) supports PR merge-ref isolation from base/sibling PR caches and reuse by the same PR's reruns. Source inspection separately establishes the actual path/key/prefix choices. Existing registry/git/target build inputs remain a trust boundary. Per-ref cancellation and 10/15-minute smoke/ARM limits are real, but they do not cap separate PRs; organization approval or billing settings are neither claimed nor verified.

The official [protection endpoint](https://docs.github.com/en/rest/branches/branch-protection#get-branch-protection) and [branch endpoint](https://docs.github.com/en/rest/branches/branches#get-a-branch) document different shapes. Dismissal/bypass actor fields confer administrative effects; enforcement scope is not harmless response decoration. The unchanged source remains conservative and the new reconciliation accurately avoids treating its fixture as universal compatibility.

### Complete code-review checklist

| Item | Disposition |
|---|---|
| Correctness | Pass for changed B claims; Low PR48-CR-01 remains open in inherited generated methodology |
| Capability semantics | Runtime N/A; documented administrator/workflow trust boundaries accurately retained |
| Fault containment | Runtime N/A; current token prose aligns with existing matcher, no stronger fault-coverage claim |
| Unsafe discipline | N/A; unsafe/audit source byte-unchanged; HIGH T-038 expressly excluded |
| Error handling | No implementation change; fail-closed policy, optional metadata and negative-probe prose checked against source |
| Tests | Scoped syntax, invariant, digest, links, source and parent-hosted checks above; no invented runtime execution |
| Documentation | All changed files covered, 17 dispositions reconciled; p99 caveat and MP-1 source attribution requested |
| Architectural principles | All P1–P12 considered below |
| Dependencies | None added or changed |
| Naming/style | Pass; ordinary prose, targeted spacing, valid artifact identities |
| Commit message | Pass; Conventional Commits with valid ADR-0013 and ADR-0040 references; coordinator records new review trailers separately |

### Architectural principles P1–P12

| Principle | Disposition |
|---|---|
| P1 No ambient authority | Preserved; no runtime grant or CI administrative credential; existing bypass is honestly described |
| P2 Smallest defensible TCB | Preserved; no executable/kernel growth |
| P3 Userspace services | N/A; no placement change |
| P4 Checks at boundaries | Preserved; no capability boundary change, app/body distinction explicit |
| P5 Rust-only kernel | Preserved; no Rust/assembly/unsafe change |
| P6 HAL separation | Preserved; no source dependency change |
| P7 No proprietary blobs | Pass; text only |
| P8 ADR decisions | Pass; existing Accepted ADR-0040 policy is unchanged, no retroactive acceptance or new governance |
| P9 English repository | Pass; official country-name claim reconciled, new prose English |
| P10 Mermaid diagrams | N/A; no diagrams added |
| P11 Reproducibility | Preserved; pins/logic unchanged, exact-source reports/digests retained, statistical overclaim explicitly identified |
| P12 Complete declared scope | No runtime stubs; B's two rounds pending, tasks In Review, first-main/default dispatch merge-dependent |

### Preread and output-recovery record

Read AGENTS, full CLAUDE and current roadmap before implementation assessment; all 39 actual numbered ADRs in numerical order (0001–0033, 0035–0040; 0034 absent); all 15 standards including README; full perform-code-review, conduct-review and conduct-approval-review skills; full code master plan/template. Read the supplied attachment completely, the actual PR body via read-only `gh pr view 48` before the diff, all four complete canonical A R1/R2 code/security reports, the actual historical approval report and cited T-033/T-030 role/range/checklist locations. PR body describes an older integrated intent/evidence tip and is not substituted for B's immutable scope.

Long output was bounded and all truncations recovered: current roadmap lines 21–40 plus subsequent ranges; ADR 0008; boundary of 0016/0017; 0021 lines 95–170 and 0022 lines 1–83; 0024 lines 50–105; 0027 lines 84–98; 0028 lines 111–205; 0039 in two bounded ranges and 0040 lines 1–75. Other portions remained visible in their original outputs. The combined B diff truncated eight tokens in the unchanged contextual T-035 R2 row; that row was reread in full. The later T-035 supporting-history truncation was recovered with lines 55–78. All four required A reports were read in bounded complete ranges. The original T-033 report was checked at its role/checklist passages and mechanically preserved, rather than falsely claimed as wholly reread.

Own executions, coordinator-acquired service summaries, author dispositions and historical peer executions remain distinguished throughout. No new live-policy export/check/apply, artifact download or archive-digest authentication is claimed.

## Verdict

**Approve for immutable follow-up B round 1, with two Low nonblocking findings, PR48-CR-01 and R1-INT-01; zero new Blocker, High or Medium findings. Blocking list: none.** The inherited p99 prose needs the stated forward correction and explicit historical caveat; the MP-1 reference needs source attribution corrected. No future correction is certified by this report. All eight tasks remain In Review. Existing HIGH T-038 remains open and excluded; green lint/Miri/smoke do not certify the x2 assembly contract. This is not whole-PR merge authorization, Done promotion, phase closure, first-main/default-dispatch proof or approval of future commits.

This complete independent provisional report is written before waiting for the paired B code review. Paired cross-read reconciliation will be appended before final handoff.

## Paired-review reconciliation

After completing this full independent provisional report, first read the complete 151-line provisional `/tmp/tyrne-pr48-docs-r1-code.md`, then read its complete final 162-line version in two bounded ranges before final handoff. The final peer report independently Approves the same immutable range, with inherited Low PR48-CR-01 and corroborated B-introduced Low R1-INT-01, and no blocking/High/Medium issue. Its five roles, full checklist, P1–P12, local checks, 383 links/38 anchors, original-prefix/digest/statistic checks and attribution of exact-B service summaries agree. Its 130-file protected-set inventory and this report's broader 239-file byte comparison use different selection sets; they are not conflicting corpus counts or additional executions attributed to each other.

The peer checked R1-INT-01 directly against reconciliation line 74 and the actual master-plan list and accepted it as a peer-discovered Low. Its complete final report records both findings consistently in the relevant roles, checklist and verdict; the final cross-read is complete. This integration reviewer discovered that source-attribution issue independently, while PR48-CR-01 originated as the coordinator's external-review lead and was independently corroborated by both reviewers. No unresolved finding, verdict or scope conflict remains. Both findings remain open at immutable 5816c934, with no certification of the coordinator's future fix. Final verdict remains **Approve, two Low nonblocking findings, zero Blocker/High/Medium, no blockers**. Coordinator owns canonical recording and fresh cumulative Round 2 after corrections.

## Coordinator publication and correction disposition

The complete reviewer report above is published with its [paired canonical report](2026-10-12-pr48-docs-followup-r1.md). The coordinator read both final full reports and independently verified both Low findings. This publication corrects the future generator p99 prose and adds an explicit dated caveat while preserving all captured report bytes; it also corrects the current MP-1 source attribution. Seven performance methods pass normally and optimized, ShellCheck/actionlint and whitespace/link checks pass. These are coordinator verifications, not reviewer approval of future bytes. Fresh cumulative B Round 2 remains pending; no task promotion or merge occurs.
