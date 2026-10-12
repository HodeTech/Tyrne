# Code review 2026-10-12 — PR48 follow-up B, fresh round 1

- **Change:** [PR48](https://github.com/HodeTech/Tyrne/pull/48), immutable `a1eb406576f4984f563bc45ee5650c2aff0d8f2c..5816c934a4d28fa66774b73b46047bd0d652b724`, `development` only.
- **Reviewer:** fresh independent Codex agent `/root/pr48_docs_r1_code`, acting for @cemililik in all five canonical code-review roles sequentially; separate from implementation, prior A reviewers and the paired B integration reviewer.
- **Date:** 2026-10-12, Europe/Istanbul.
- **Risk class:** Ordinary documentation and workflow comments. The substantive assurance-tool changes were follow-up A and have separate code/security records. B changes no runtime source, administrative adapter, policy or executable workflow content.
- **Security-review cross-reference:** N/A for this ordinary delta. Prior A security R1/R2 are context, not a new B security verdict. The independent paired ordinary integration review is `/tmp/tyrne-pr48-docs-r1-integration.md`.
- **Requested model/effort provenance:** parent confirms `gpt-6.1-sol`, high effort, `fork_turns=none`. This is orchestration metadata, not an independent runtime model-identity attestation.
- **Scope:** all 12 changed files, 138 additions and 26 deletions; 11 Markdown documents and comment-only `ci.yml`. This full provisional report was written before waiting for the independent peer; final cross-read disposition is appended afterward.

## Correctness

**One B-introduced Low source-attribution finding, R1-INT-01, was discovered by the independent integration reviewer and independently confirmed during the full peer cross-read.** One inherited generated-documentation claim was independently confirmed during this round and is recorded as Low PR48-CR-01 under Documentation. No runtime or policy defect is established by either.

- **Commands and gate descriptions:** both coverage examples now exclude BSP, `tyrne-user` and `tyrne-userland-hello`, matching `ci.yml:455`. Miri examples use repository-selected pinned nightly rather than rolling `+nightly`. The six-line ARM block now matches check → clippy → isolated rejection probe → native tests → Miri setup → Miri tests. Its four gates are check/clippy/test/Miri; the probe and setup are correctly additional operations. Both userland crates remain included, only BSP excluded. The fast-lane failure table now includes all four existing fixture families.
- **Observed timing and caches:** the ~1–2 minute Miri statement is explicitly observed, with the older 10–15 minute budget retained as history. Parent-acquired exact-B summaries independently parsed here show Miri jobs of 92 and 85 seconds. Every workflow cache key contains OS/architecture, toolchain identity (literal stable for that lane) and lockfile hash; restore prefixes omit the hash while retaining OS/architecture/toolchain. All paths omit cargo-bin. This accurately narrows one installed-executable surface without describing registry/git/target artifacts as integrity-attested.
- **Actual setup:** workflows install/cache directly per job. No shared composite action exists in the tree. Correcting the infrastructure description documents current implementation; it does not adopt a new architectural or process policy.
- **Current policy and trust:** guide/header correctly qualify branch protection by the actors it governs, preserve `enforce_admins: false`, count 0 and disabled code-owner review, and distinguish Actions producer app 15368 from workflow/source integrity. Required display names match all six canonical JSON entries. The GraphQL review-enabled boolean and REST approval count remain separately captured properties. Neither this review nor B demonstrates the supplied duplicate-name bypass. GitHub documents duplicate-name ambiguity and possible merge blocking, rather than the supplied report's specific instant-success bypass. [GitHub protection semantics](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
- **Capacity and external controls:** per-workflow/ref concurrency and smoke/ARM 10/15-minute bounds match the YAML. They do not bound distinct PRs. Fork approval, organization capacity and billing settings are explicitly unverified external administration, without a fictional repository-enforced limit.
- **REST schema boundaries:** the guide/reconciliation link the actual complete protection response fixture and distinguish it from branch-summary responses. The fixture equality and unknown-extension tests preserve conservative refusal; dismissal/bypass actors and enforcement scope carry policy. They must not be discarded as URL metadata. Production adapter and policy are unchanged. The reference's actor restrictions corroborate that distinction. [GitHub protected-branch API](https://docs.github.com/en/rest/branches/branch-protection).
- **Smoke and historical counts:** T-034 now names the actual `Undefined Instruction` matcher in both production smoke and fixture tuples; it retains that exact SVC counting is outside the gate. Its opening four-check reference is explicitly historical, while current protection has six checks. No stronger guest-safety claim is introduced.
- **Review/evidence mapping:** T-033's original source-bound report is retained as an exact prefix, with an additive mapping to the five canonical roles. T-030's index accurately names R1 `8437158..364b746` and R2 `8437158..5cd9ee8`; its prior cumulative compression was not an incorrect original R1 range. The ADR-0040 approval artifact is explicitly an approval review using its dedicated template; the approval skill mandates no separate storage folder. MP-1/MP-33 refer to the same allocation-exhaustion item, without another checklist item or original-disposition rewrite. The new sentence incorrectly attributes literal MP-1 to the master plan; R1-INT-01 records the source-precision correction.

The cache paragraph is consistent with GitHub's ordinary PR merge-ref scope: the same PR's reruns may restore that cache, while base/sibling PR runs cannot. This is documented service scope, not a live cache inventory or poisoning experiment. [GitHub dependency caching reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching).

## Style

**Findings: none.** Actionlint 1.7.12 on both explicit workflows and immutable-range whitespace validation pass. Changed live prose restores normal word/number spaces without altering exact tokens, SHAs, job names or historic evidence. Comments now align consistently with their surrounding YAML. Repository text is English; UTC-only schedule wording is a routine simplification. The supplied allegation that the official country name itself violated English-only policy is refuted by the English-language UN announcement, and B does not encode that allegation as truth. [UN English-language announcement](https://turkiye.un.org/en/184798-turkeys-name-changed-t%C3%BCrkiye).

No diagram, new public Rust item, unsafe contract, dependency, naming refactor or lint exception is introduced. No speculative style/refactor request is warranted for the small prose delta.

## Test coverage

### Independently executed verification

| Check | Outcome and evidence meaning |
|---|---|
| `actionlint .github/workflows/ci.yml .github/workflows/performance.yml` | Pass; version 1.7.12, installed Homebrew darwin/arm64 binary |
| `git diff --check a1eb406..5816c93` | Pass; exact immutable delta whitespace |
| Full changed-Markdown repository-link check | 383 inline repository-link occurrences and 38 Markdown fragments checked across all 11 changed Markdown files; zero missing targets/anchors. Heading slugs and explicit anchors were checked locally, not a browser-render claim or external-link uptime scan |
| Protected-file/tree scope | 130 tracked protected files are absent from the changed-file set: tools, runtime Rust/assembly, ADRs, audits, policy/adapter, Cargo/toolchain, performance workflow and existing baseline reports; complete changed-file inventory contains only the stated 12 files |
| YAML content invariant | Removing only full comment lines from base/head `ci.yml` yields byte-identical remaining lines; no command, job, trigger, cache, permission or run body changes |
| Historical review invariant | Head T-033 report starts with exact complete base bytes; seven appended lines only |
| Performance snapshot digest | Independently recomputed unchanged `24c143abb0151de1eb3fb38ff3d74f3e060effd2a6c492cc8389bebca565ae85` |
| Raw performance arithmetic | Parsed all 20 original samples; nearest-rank p10/p50/p90 reproduce `5,232,672 / 5,473,392 / 7,277,776 ns` |
| Task/status consistency | All T-030…T-037 status fields remain In Review; T-038 remains Ready/open, with the HIGH explicitly excluded; no Done promotion |
| Targeted stale-token sweep | No current target occurrence of the obsolete fault token, sibling-cache contrast, composite-setup claim or listed spacing defects; historical records deliberately retained |
| Worktree/source checks | HEAD remained full 5816c93 and shared worktree stayed clean; no repo mutation by reviewer |

No tests are added or changed in B. Relevant existing performance, protection and smoke fixture contracts were inspected before their corresponding unchanged production paths; existing ARM flow and workflow commands were checked against the guide. New Rust public APIs, new errors, behavioral changes and before/after runtime regression tests are N/A to this prose-only range. Broad Cargo/Miri/QEMU re-execution would not validate these text corrections and was not performed. A future correction to generated performance wording should run its seven synthetic performance methods and ShellCheck; it does not need a percentile-algorithm change or broad guest retest.

### Parent-acquired exact-B hosted evidence independently inspected

The coordinator fetched `/tmp/tyrne-pr48-followup/run-38213061361.json` and `run-38213057506.json`. This reviewer parsed the complete JSONs, asserted full source SHA, expected event, completed/success and exactly seven successful job conclusions:

| Run | Source and result |
|---|---|
| [PR CI 38213061361](https://github.com/HodeTech/Tyrne/actions/runs/38213061361) | `pull_request`, exact `5816c934a4d28fa66774b73b46047bd0d652b724`, all seven jobs success |
| [Push CI 38213057506](https://github.com/HodeTech/Tyrne/actions/runs/38213057506) | `push`, same full source, all seven jobs success |

These are independent inspections of parent-acquired service summaries, not this reviewer's independent API retrieval, guest execution, artifact download or archive authentication. Earlier exact-683 A runs and their code/security records remain correctly source-bound prior evidence; they were not relabeled as B runs. No new performance run is required or claimed for this B commit, which changes neither relevant performance trigger path nor harness/workflow bytes. No new live policy export/check/apply was performed here. First merged-main CI and default-branch dispatch remain merge-dependent.

**Missing B tests that block approval: none.** CI success supports integration, but does not prove documentation truth, estimator reliability or runtime soundness.

## Documentation

The new author-maintained reconciliation explicitly disclaims independent-review/maintainer-approval/Done/closure status. It accounts for every supplied finding, with links from current roadmap, phase and task index and an appended T-035 history entry. Original review verdicts, original performance bytes and older identifying metadata remain historical. The new-normal-field minimization claim is carefully limited; it does not certify every auxiliary artifact or arbitrary successful tool output.

### All 17 supplied dispositions

| ID | Independently assessed disposition |
|---|---|
| M-1 | Language-violation claim refuted; UTC simplification valid |
| M-2 | Producer-versus-workflow trust gap documented; claimed specific duplicate bypass unestablished; no unauthorized policy change |
| M-3 | Observed response fixture and conservative extension limits accurate; no current live failure inferred and no actor/enforcement stripping |
| L-1 | Current live spacing corrections present; historic originals preserved |
| L-2 | Setup, exclusions, Miri observation, cache key/prefix, fixture table and ARM order/count aligned |
| L-3 | Current task matches production/fixtures' Undefined Instruction token |
| L-4 | Optional metadata fallback implementation and synthetic controls were A; B accurately describes the narrow behavior |
| L-5 | Nonempty-diagnostic guard is present before command execution, preserved from A |
| L-6 | Additive T-033 role map valid; dedicated approval template and cumulative range were already valid; MP item equivalence correct, but literal-label attribution needs R1-INT-01 correction |
| L-7 | Normal new-report field minimization accurate; no retroactive rewrite/privacy certification of older captures |
| L-8 | Successful identical clean baseline precedes six-cfg mutation; both exact observed compiler classes remain justified, not a universal classifier |
| I-1 | Header policy limits and separately captured review properties accurately described |
| I-2 | Five bin paths removed in A; remaining cache trust and PR scope accurately bounded |
| I-3 | Per-ref capacity boundary stated; external organization/approval/billing controls explicitly unverified |
| I-4 | Reviewer provenance retained as recorded configuration/context, not runtime identity attestation or maintainer signature |
| I-5 | Filename/internal-title distinction intentionally preserves exact downloaded bytes; digest independently matches |
| I-6 | Opening four-check snapshot qualified against current six-check policy |

### PR48-CR-01 — Low, nonblocking: sample-rank transition is presented as statistical reliability

- **Location at immutable 5816c93:** `tools/perf-harness.sh:565–570`, particularly the generated final sentence; reproduced in the preserved follow-up hosted snapshot `docs/analysis/reports/perf-baseline-2026-10-12-t035-pr48-followup-hosted-check.md:49–50`. The new reconciliation's Historical artifact section currently preserves/links that snapshot without a dated p99 qualification.
- **Source/provenance:** root reported a new read-only CodeRabbit Minor thread on exact 683 and requested independent assessment. This reviewer did not retrieve that thread or run its embedded suggested command. The finding follows direct immutable source/snapshot inspection and integer-rank arithmetic; it is inherited PR48 generated prose, not a regression introduced by B.
- **Evidence:** nearest rank is `ceil(0.99*n)`. Direct integer evaluation gives rank 20 at n=20, 99 at n=99, and 99 at n=100. At 100 the selected order statistic is merely second-highest rather than maximum. That rank transition supplies no confidence bound, precision target, independence/stationarity assumption or tail-estimator reliability result. The unconditional claim of becoming statistically informative at 100 samples is unsupported. The current 20-sample p99/max equality and reported raw p10/p50/p90 values are correct.
- **Impact:** readers may treat an arbitrary count as sufficient assurance of tail reliability. Performance is informational with no calibrated merge threshold, so this is a narrow Low prose-quality defect, not a statistics algorithm defect or merge-safety finding.
- **Action:** revise future generated methodology to state the exact rank fact and that no universal sample count establishes p99 reliability. Preserve the existing captured baselines byte-for-byte and add an explicit dated reconciliation caveat for the inherited sentence. Keep percentile calculation, measurement thresholds and Accepted ADR unchanged. Verify generator wording with the seven scoped performance fixtures/ShellCheck and fresh cumulative Round 2.
- **Status:** open at immutable 5816c93. Root's planned correction is not certified by this report. One shared finding, not an additional duplicate count if the peer corroborates it.

### R1-INT-01 — Low, nonblocking: literal checklist label attributed to the master plan

- **Location:** `docs/analysis/reports/2026-10-12-pr-48-supplied-review-reconciliation.md:74` at immutable 5816c93.
- **Discovery/provenance:** the independent integration reviewer discovered this after its initial provisional report; this reviewer independently verified it during full peer cross-read, after writing the complete independent provisional code report.
- **Evidence:** the new sentence attributes `MP-1` literally to the security master plan. That file's kernel-mode discipline list at line 68 contains an unnumbered typed-allocation-exhaustion requirement, and a direct search finds neither `MP-1` nor `MP-33`. Later A R2/T-030 R2 artifacts use MP-1; earlier artifacts use MP-33 for that same extra item after the 32 standard checks.
- **Impact:** imprecise source attribution in the new reconciliation. The actual requirement, equivalence and total of 33 dispositions are correct; no missing review coverage or governance defect follows.
- **Action:** attribute MP-1 and MP-33 to later/earlier review artifacts respectively and identify the unnumbered master-plan requirement as their common source. Preserve all original review text.
- **Status:** open at immutable 5816c93; coordinator's future correction requires fresh cumulative review. One peer-discovered finding corroborated here, not a second independent count.

No further actionable documentation defect was established. The PR body's older-source validation counts and “final tip” paragraphs remain dated historical intent/evidence; neither the B document nor this verdict treats those as exact-B source proof. Later parent-fetched exact-B runs above supply the current binding.

## Integration

Prerequisites read directly with bounded reads and recovery of truncated output: AGENTS, full CLAUDE/current roadmap, all 39 actual numbered ADRs in numerical order (0001–0033, 0035–0040; 0034 absent), all 15 standards including README, skills index, `perform-code-review`, `conduct-review` and full code master plan/output template. Read actual read-only `gh pr view 48` description as older source intent, complete supplied Turkish attachment, and all four complete canonical A code/security R1/R2 reports. The dedicated approval skill and relevant original approval/T-030 headings were checked to assess the reconciliation's template/range claims; no approval-promotion review was performed. All 12 B changed files and the complete new reconciliation were inspected.

Risk classification is ordinary: correcting descriptions of existing assurance/security boundaries does not modify those boundaries. No new mandatory security review, ADR, policy, approval rule or ruleset is justified by B. No runtime symbol/caller, dependency graph, toolchain/action pin, permission, unsafe contract or binary changes. Existing HIGH T-038 is expressly open/excluded and no gate/Miri success is used to clear it. Performance/coverage remain informational; merge-dependent proof is not confused with deferred implementation. B adds no runtime overhead and no behavioral refactor is warranted.

### Complete code-review checklist

| Item | Disposition and basis |
|---|---|
| Correctness | Current commands/operational claims pass; one Low B source-attribution defect and one inherited Low p99 claim explicitly recorded |
| Capability semantics | Runtime N/A; no grants or checks changed. Existing admin, producer and actor/enforcement-policy boundaries documented faithfully |
| Fault containment | Runtime N/A; smoke token description matches preserved matcher; no new exhaustive-fault or SVC claim |
| Unsafe discipline | N/A to delta; no unsafe/assembly/audit change. Existing HIGH T-038 remains excluded/open |
| Error handling | No changed Result/error path; fail-closed policy and optional metadata boundaries accurately documented |
| Tests | Pass for scope; actionlint, links/anchors, source/historical/digest/arithmetic invariants and exact-B hosted summaries; broad guest retest intentionally N/A |
| Documentation | All 17 dispositions covered; Low generated p99 claim and literal MP-1 source attribution open, with precise preservation-safe corrections |
| Architectural principles | All P1–P12 considered individually below |
| Dependencies | N/A; no new crate/action/tool/dependency or trust decision |
| Naming/style | Pass; English live prose, spacing, stable exact tokens, comment lint and whitespace checks |
| Commit message | Pass: `docs(ci): reconcile PR48 review claims and current guidance`, explanatory body, valid ADR-0013/0040 references. No unsafe Audit/security trailer needed for ordinary B |

### Architectural principles P1–P12

| Principle | Disposition |
|---|---|
| P1 No ambient authority | Preserved; no new runtime/admin power and explicit existing bypass boundary |
| P2 Smallest defensible TCB | Preserved; no privileged source or runtime growth |
| P3 Drivers/filesystems/network in userspace | N/A; no subsystem placement change |
| P4 Capability checks at boundaries | Runtime unchanged; authority-bearing administrative fields are not reclassified as metadata |
| P5 Rust-only kernel | Preserved; no kernel/assembly/unsafe change; inherited T-038 not certified |
| P6 HAL separation | Preserved; no HAL/kernel interface or hardware placement change |
| P7 No proprietary blobs | Preserved; text-only additions, no binary/firmware |
| P8 Recorded decisions | Pass; routine alignment implements Accepted ADR-0040 without new policy or ADR rewrite |
| P9 English repository | Pass; official English country-name allegation correctly refuted; new repository text English |
| P10 Mermaid diagrams | N/A; no diagram or image added |
| P11 Reproducibility | Preserved; pins/source attribution and original capture bytes retained; raw statistics/digest independently checked |
| P12 Complete declared scope | Pass for ordinary B; eight tasks stay In Review, no phase/main/dispatch/Done completion claimed |

Publication, canonical index/cross-reference/trailer work belongs to the coordinator under the explicit no-repository-edit instruction. This reviewer wrote only the temporary report, performed read-only repository/service-reference operations, and made no checkout, commit, push, policy/API write, PR comment or external-person message.

## Verdict

**Approve for ordinary follow-up B at immutable 5816c93, with two Low nonblocking documentation findings: inherited PR48-CR-01 and B-introduced R1-INT-01.** New Blocker/High/Medium findings: **zero**. Blocking list: **none**.

All five roles, the complete code-review checklist and P1–P12 are covered. This scoped verdict does not approve a future p99 correction, complete the second fresh B round, authorize merge, promote any task or close Phase B.2. Under the requested review/fix workflow, the confirmed Low findings should be corrected and reviewed in fresh cumulative Round 2. Existing HIGH T-038 and first-main/default-dispatch evidence remain open.

## Paired-review reconciliation

After writing the complete independent 151-line provisional report, read the entire paired `/tmp/tyrne-pr48-docs-r1-integration.md`, including its added R1-INT-01, before finalizing. The peer independently Approves the same immutable range with the same inherited Low PR48-CR-01 and the newly discovered Low R1-INT-01. The complete five roles, checklist, P1–P12, task/HIGH/merge boundaries, exact-source hosted attribution and source-preservation conclusions agree. Its 239-file broader preservation check is peer-executed evidence; this reviewer performed the independently described 130-file scope/YAML/T-033/digest checks and does not reattribute the peer's execution.

The source-attribution finding was independently reproduced after peer discovery and is now reflected throughout this final report. No unresolved verdict conflict or additional blocker emerged. Both findings are open at immutable B head; neither planned correction nor fresh Round 2 is preapproved. Coordinator publication/index/trailers remain separate authorized work.

## Coordinator publication and correction disposition

The complete reviewer report above is published with its [paired canonical report](2026-10-12-pr48-docs-integration-r1.md). The coordinator read both final full reports and independently verified both Low findings. This publication corrects the future generator p99 prose and adds an explicit dated caveat while preserving all captured report bytes; it also corrects the current MP-1 source attribution. Seven performance methods pass normally and optimized, ShellCheck/actionlint and whitespace/link checks pass. These are coordinator verifications, not reviewer approval of future bytes. Fresh cumulative B Round 2 remains pending; no task promotion or merge occurs.
