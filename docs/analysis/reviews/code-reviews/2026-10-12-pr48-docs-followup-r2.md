# Code review 2026-10-12 — PR48 follow-up B, fresh round 2

- **Change:** [PR48](https://github.com/HodeTech/Tyrne/pull/48), immutable cumulative `a1eb406576f4984f563bc45ee5650c2aff0d8f2c..646ba33052632d5afda1e206007ed9bc334e8e3a`, `development` only.
- **Reviewer:** fresh independent Codex agent `/root/pr48_docs_r2_code`, acting for @cemililik in all five canonical code-review roles sequentially; distinct from implementation, previous reviewers and paired fresh integration reviewer.
- **Date:** 2026-10-12, Europe/Istanbul.
- **Risk class:** Ordinary documentation, workflow comments and generated report prose. Follow-up A's assurance-tool implementation has distinct historical code/security reviews; no B policy, runtime or assurance algorithm changes.
- **Security-review cross-reference:** N/A for ordinary B. Canonical A security R1/R2 are prerequisite context, not reused B approval. The paired ordinary integration review is `/tmp/tyrne-pr48-docs-r2-integration.md`.
- **Requested model/effort provenance:** `gpt-6.1-sol`, high effort, `fork_turns=none`, as supplied by the coordinator. This records requested orchestration configuration, not an independently attested runtime identity or maintainer signature.
- **Scope:** all 15 changed files: 13 Markdown files, comment-only `ci.yml`, and seven changed report-generator echo lines. Both implementation commits and both R1 findings are reviewed cumulatively. This complete provisional report was written before waiting for the paired review; full cross-read reconciliation follows separately.

## Correctness

**New actionable findings: none. Both R1 Low findings are resolved at the exact reviewed source.**

- **PR48-CR-01 — resolved:** `tools/perf-harness.sh:569–574` now states that nearest-rank p99 at N = 100 selects rank 99, the second-highest sorted observation; from N = 100 onward the selected rank is below N, while ties can still equal the maximum. It expressly says this rank transition establishes no statistical reliability. Direct integer ranks at N = 1/20/99/100/101/1000 are 1/20/99/99/100/990. Four independent synthetic generated reports exercise distinct N = 20/99/100 and tied N = 100; reported p99 and emitted wording agree. This corrects interpretation only. Every other harness byte, including aggregation, sample-validity thresholds, watchdog, source attribution, metadata and overwrite refusal, is identical to base.
- **Historical p99 qualification:** the reconciliation's dated Additional PR feedback section names the inherited unsupported sentence, supersedes its reliability implication, explains rank and ties, and explicitly preserves captured report bytes/digests. The historical 20-sample bands remain correct. It neither retrospectively changes a reviewer verdict nor claims original authors reviewed future source.
- **R1-INT-01 — resolved:** the current reconciliation attributes MP-1 to later review artifacts and MP-33 to earlier artifacts. The security master plan's kernel-mode list contains the common unnumbered typed allocation-exhaustion requirement, not either literal label. Direct source checks find the later label in A R2/T-030 R2 and the earlier label in A R1. The total remains 32 standard items plus one extra; no missing coverage or new governance rule is inferred.
- **Coverage/Miri/ARM:** both coverage examples exclude BSP and both userland crates, matching the actual workflow. Plain repository-local Cargo selects the pinned nightly; explicit stable remains confined to the stable lane. ARM order is check, all-target clippy, isolated rejection probe, native tests, Miri setup, Miri tests. The four gates are check/clippy/test/Miri, with setup/probe as supporting operations. Both userland crates remain included; only BSP is excluded. Fast-lane prose now names all four existing fixture families.
- **Timing/setup/cache:** the Miri estimate is an observed small-suite duration, with the historical budget qualified. Independently parsed service summaries show 92/85 seconds at 5816 and 68/76 seconds at 646. Actual setup is duplicated per job, with no composite action present. Exact cache keys include OS, architecture, toolchain identity and lockfile hash; restore prefixes retain the first three, omitting the hash. Stable is a rolling channel identity, not an immutable compiler version. All cache paths omit cargo-bin while registry/git/target remain trusted build inputs.
- **Protection and workflow trust:** six canonical exact contexts remain app-bound to 15368 with strict checking. Admin enforcement false, zero approval count and disabled code-owner review remain explicit. Producer binding is accurately distinguished from workflow/body/revision attestation. GraphQL review enablement and REST count are independently represented properties. The supplied particular duplicate-job instant-success bypass is not demonstrated; GitHub documents ambiguous duplicate names and possible merge blocking. No policy tightening, ruleset or new acceptance decision is smuggled into prose. [GitHub protection semantics](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
- **Capacity:** per-workflow/ref cancellation and actual smoke/ARM 10/15-minute bounds agree with YAML. Distinct PRs remain outside that cancellation bound. Organization approval/capacity/billing controls are correctly external and unverified here.
- **REST boundaries:** the captured complete protection response and equality/unknown-extension tests support the described observed shape. The unchanged normalizer still refuses unknown enforcement/actor fields instead of dropping them as metadata. Review dismissal/bypass fields carry policy; branch-summary name/protection_url are not evidence of the protection endpoint's schema. The dated fixture is not permanent live-drift attestation. [GitHub protection API](https://docs.github.com/en/rest/branches/branch-protection), [branch API](https://docs.github.com/en/rest/branches/branches).
- **Smoke/history:** T-034 now names the actual Undefined Instruction matcher, matching production and both-profile fixtures; exact SVC counting and adversarial EL0 remain separate. Its opening four-check count is distinguished from the current six-check policy. UTC cadence matches the performance cron. T-033 gains an additive canonical-role map, T-030's index names the actual R1/R2 ranges separately, and the ADR-0040 approval report remains correctly identified as an approval artifact using its dedicated template.

Blocking correctness findings: **none**. Existing HIGH T-038 x2 clobber remains open and excluded, not reclassified or cleared.

## Style

**Findings: none.** ShellCheck 0.11.0, actionlint 1.7.12 against both explicitly named workflows and immutable-range whitespace validation pass. New live prose uses English and ordinary spaces without modifying exact contexts, source SHAs or historical evidence. YAML indentation changes affect comments only. Generated output uses existing Bash echo style and quoting; no executable control structure changes.

UTC-only wording is a routine simplification. The supplied constitutional English-language allegation is correctly refuted by the UN's own English announcement using the official country name; the reconciliation does not encode that allegation as a violation. [UN English-language announcement](https://turkiye.un.org/en/184798-turkeys-name-changed-t%C3%BCrkiye).

No diagram, Rust naming change, unsafe annotation, new dependency, formatter exception or speculative refactor request applies.

## Test coverage

Tests were read before their relevant implementations: the complete seven-method performance suite, actual report output, protection capture/equality/refusal tests, ARM clean-before-mutation flow and smoke token/source. No tests are changed in B. Generated report text changes justify scoped performance execution and direct output assertions; broad local Rust/Miri/QEMU re-execution would not test these documentation corrections and was not repeated.

### Independently executed checks

| Check | Result and evidence meaning |
|---|---|
| `python3 tools/test-perf-harness.py` | Seven methods pass; synthetic measurements, metadata/privacy, dirty/unknown state, valid/failed count, overwrite refusal and failure through Bash/tee |
| `python3 -O tools/test-perf-harness.py` | Seven methods pass; top-level unittest assertions remain active; child shebang processes are not all thereby optimized |
| Four generated-report controls using the existing fixture helper in private temporary directories | Distinct N = 20/99/100 give p99 20,000,000 / 99,000,000 / 99,000,000 ns; tied N = 100 gives 1,000,000 ns. All four emit the exact rank/tie/no-reliability text and omit the obsolete claim |
| `shellcheck tools/*.sh` | Pass at default severity, version 0.11.0 |
| `actionlint .github/workflows/ci.yml .github/workflows/performance.yml` | Pass, version 1.7.12 |
| `git diff --check <immutable-base> <immutable-head>` | Pass |
| Exact source-scope and preservation script | 246 selected existing protected files byte-identical; no runtime Rust/assembly, Cargo/toolchain, ADR, audit, policy/adapter, performance workflow, old performance snapshot or original other-review body change |
| T-033 prefix preservation | Original 46,939 bytes are an exact prefix, followed by seven additive lines |
| Workflow noncomment invariant | Removing only full comment lines yields byte-identical base/head `ci.yml`; no command, scalar, job, trigger, path, permission or run body changes |
| Performance source invariant | Replacing only the report echo paragraph in base yields the exact head script; every other byte is unchanged |
| Changed-Markdown local links/anchors | 393 relative inline-link occurrences and 38 fragments resolve across all 13 changed Markdown files; zero missing targets/anchors |
| Task state inventory | T-030 through T-037 all In Review; T-038 Ready/open, with its HIGH explicitly excluded |
| Targeted current-prose sweep | Obsolete matcher/setup/cache contrast and listed live spacing defects corrected; historical task/report wording intentionally retained |
| Source/worktree checks | Full reviewed HEAD remains 646ba33052632d5afda1e206007ed9bc334e8e3a and shared worktree clean |

The link scanner excludes fenced and inline-code examples, checks local target existence and Markdown heading/explicit anchors, and does not authenticate external links or browser rendering. The selected preservation corpus omits changed files, which were separately inspected; its count is not the entire repository file count. No tests wrote into the repository: performance fixtures copy source into their own temporary directories. No archive, synthetic Git commit, shared Cargo target or guest image was needed for this prose delta.

### Exact-source hosted evidence independently inspected

The coordinator acquired all summaries/downloads below. This reviewer independently parsed the complete local JSONs and inspected downloaded report/metadata. This is not independent API retrieval, guest execution, artifact download or service-archive authentication.

| Source/run | Verified service-summary result |
|---|---|
| Exact 646 [PR CI 38214402250](https://github.com/HodeTech/Tyrne/actions/runs/38214402250) | Full reviewed SHA, pull_request, completed/success; all seven jobs success |
| Exact 646 [push CI 38214395496](https://github.com/HodeTech/Tyrne/actions/runs/38214395496) | Full reviewed SHA, push, completed/success; all seven jobs success |
| Exact 646 [performance 38214395500](https://github.com/HodeTech/Tyrne/actions/runs/38214395500) | Full reviewed SHA, development push, completed/success; informational report job success |
| Prior 5816 [PR CI 38213061361](https://github.com/HodeTech/Tyrne/actions/runs/38213061361) and [push CI 38213057506](https://github.com/HodeTech/Tyrne/actions/runs/38213057506) | Full 5816 SHA, respective events, completed/success and seven successful jobs each; historical R1-source proof, not relabeled 646 evidence |

The 646 performance download identifies clean full reviewed source, 20 requested/valid and zero failed samples, pinned nightly identifier, QEMU 8.2.2, 101-second harness and 139-second enclosing evidence interval. Its actual emitted methodology contains the corrected second-highest/tie/no-reliability paragraph. Independently recomputed all 20 raw values: nearest-rank p10/p50/p90 **8,496,720 / 9,820,080 / 12,571,504 ns**; p99/max **13,788,672 ns**. File SHA-256 **`dab24e41b0bc954f09b29cc942bbf962d552bf7763a92b1d6d1855918546bc87`**. Service metadata names artifact 11731885187, 4,187 bytes; its archive digest remains service-reported, not locally recomputed.

The retained 50ab snapshot independently hashes to **`24c143abb0151de1eb3fb38ff3d74f3e060effd2a6c492cc8389bebca565ae85`**. Its 20 raw samples still give p10/p50/p90 **5,232,672 / 5,473,392 / 7,277,776 ns**, p99/max 7,587,520 ns. The two bands describe different runs; no calibrated regression, cross-host latency or hardware-performance verdict follows. The 646 download is ephemeral evidence at this review, not a falsely claimed existing committed snapshot. First-main/default-branch dispatch remain merge-dependent.

**Missing tests that block B: none.** Existing estimator arithmetic and validity thresholds are unchanged; the correction is precisely verified without inventing a new statistical guarantee or requiring an unrelated runtime test.

## Documentation

**All 17 original supplied dispositions remain accounted for.** The author-maintained reconciliation clearly disclaims being an independent approval, Done promotion or phase closure. Current guide/examples align with source, and historical review reports retain their original source-bound findings/verdicts plus explicit coordinator publication notes. A report's original open finding is not an inconsistency after a later dated correction.

| ID | Independent Round 2 disposition |
|---|---|
| M-1 | Constitutional violation claim refuted; UTC simplification accurate |
| M-2 | Producer/workflow trust boundary, admin bypass/count zero documented; specific bypass unestablished, policy unchanged |
| M-3 | Actual captured endpoint fixture and fail-closed extensions described; no universal schema/live equality guarantee |
| L-1 | Current target spacing restored; historical originals preserved |
| L-2 | Actual setup, coverage exclusions, pinned Miri/observed duration, key/prefix distinction, fixture families and ARM command order/count aligned |
| L-3 | Current T-034 matcher agrees with production and both-profile fixtures |
| L-4 | A's optional metadata fallback accurately described with narrow normal-field minimization |
| L-5 | A's nonempty-diagnostic refusal remains before negative command execution |
| L-6 | Additive T-033 role mapping, dedicated approval-template identity and explicit T-030 ranges valid; R1-INT-01 label-source correction verified |
| L-7 | Historical identifying metadata retained honestly; new normal report fields minimize path/hostname without universal redaction claim |
| L-8 | Same exact clean command precedes six-cfg mutation; exact diagnostic/status boundary retained, not universal compiler classification |
| I-1 | Actor-scoped gate caveat and separately represented review boolean/count accurate |
| I-2 | Five installed-bin cache paths removed in A; remaining cache trust and ordinary PR-ref scope bounded |
| I-3 | Per-ref cancellation and job limits real; external approval/billing/organization controls explicitly unverified |
| I-4 | Requested reviewer configuration/context is not runtime attestation or maintainer signature |
| I-5 | Internal ci-nightly title versus repository filename intentionally preserves captured bytes/digest |
| I-6 | Opening four-check snapshot qualified against current six checks |

PR48-CR-01 is separately resolved by precise future generator prose and an explicit dated historical caveat; it is not silently folded into an unrelated original ID or counted as two defects. R1-INT-01 is corrected without rewriting old MP labels. Both complete R1 artifacts accurately preserve their findings as open at 5816 and record the coordinator's later correction, not reviewer approval of future bytes.

The T-033 role map matches its actual sections 3–7; section 1 is verdict, section 2 read/procedure disclosure and section 8 full checklist. The later WFI/spinning correction remains intact. T-030's security report names R1 `8437158..364b746` and R2 `8437158..5cd9ee8`, agreeing with the clarified index. The approval skill's dedicated template matches the ADR-0040 approval artifact and mandates no separate storage folder. Reading that skill to validate artifact identity does not invoke a new promotion review or its unrelated full gate workflow.

The GitHub cache reference supports ordinary PR merge-ref isolation from base/sibling PRs and same-PR rerun reuse; source inspection establishes actual key/path choices. This is no live-cache inventory or poisoning experiment. [GitHub cache scope](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching).

## Integration

Prerequisites were read directly: AGENTS, full CLAUDE/current roadmap; all 39 actual numbered ADR files in numerical order, 0001–0033 and 0035–0040, with 0034 absent; all 15 standards including README; perform-code-review and conduct-review skills; complete code master plan including its embedded output template. No standalone code-review template file exists; the master-plan template is authoritative. Read the complete supplied Turkish attachment, cached original PR description as older-source intent, all four canonical A R1/R2 code/security reports, and both complete B R1 reports. Relevant approval skill/template, original role/checklist passages, T-030 ranges and unnumbered security-master-plan requirement were directly inspected.

Long outputs were bounded, and truncations were recovered through smaller source ranges, including current roadmap, ADR boundaries, code-style middle, A R1 security trust/memory sections, A R2 security dependency/threat boundary, B R1 heading, complete cumulative diff portions and generator paragraph. Prior review reports are historical context, not substitutes for the independent source checks and own executions above. The old PR description's historical validation-tip/count statements are not treated as exact B proof; later source-bound service summaries establish this review's current integration evidence.

All 15 changed files are covered. No crate/dependency/toolchain/action pin, executable workflow content, permission, runtime symbol/caller, Rust/assembly/unsafe contract, audit body, ADR outcome, administrative adapter or versioned policy change occurs. No new ADR or separate security implementation review is triggered by correcting descriptions of existing boundaries. B adds no runtime overhead; no unrelated refactor is warranted. Tasks remain In Review, and Phase B.2's other tracks, existing HIGH and main/dispatch evidence retain their ownership.

### Complete code-review checklist

| Item | Disposition and evidence |
|---|---|
| Correctness | Pass; full cumulative claims match source, exact percentile rank/ties and label attribution corrected |
| Capability semantics | Runtime N/A; no grants/checks changed; existing administrative/producer boundaries described faithfully |
| Fault containment | Runtime N/A; current matcher prose agrees with unchanged rejection source, no exhaustive-fault or SVC claim |
| Unsafe discipline | N/A to delta; no unsafe/asm/audit change; HIGH T-038 explicitly open/excluded |
| Error handling | No new Result/error path; optional metadata, sample failure and conservative policy refusal accurately retained |
| Tests | Pass for scope; seven methods normal/-O, four generated boundary reports, lints, invariants, links/digests/arithmetic and attributed exact-head service evidence |
| Documentation | Pass; all 17 dispositions plus both R1 corrections and historical preservation verified |
| Architectural principles | All P1–P12 considered individually below |
| Dependencies | N/A; graph, actions and tools unchanged; no new trust decision |
| Naming/style | Pass; English prose, normal spaces, stable exact tokens, valid Bash quoting and comment syntax |
| Commit messages | Pass; conventional scoped docs subjects, explanatory bodies, valid ADR-0013/0040 references; R1 review trailers correctly identify historical reviewed reports, no unsafe Audit/security trailer invented |

### Architectural principles P1–P12

| Principle | Disposition |
|---|---|
| P1 No ambient authority | Preserved; no runtime/admin power added, existing bypass explicitly bounded |
| P2 Smallest defensible TCB | Preserved; generated host prose only, no privileged code growth |
| P3 Drivers/filesystems/network in userspace | N/A; no subsystem placement change |
| P4 Checks at boundaries | Runtime unchanged; administrative actor/enforcement policy remains authority-bearing rather than discarded metadata |
| P5 Rust-only kernel | Preserved; no kernel/assembly/unsafe change and inherited x2 defect not certified |
| P6 HAL separation | Preserved; no HAL/kernel interface or hardware placement change |
| P7 No proprietary blobs | Pass; text-only source/report additions, no firmware/binary |
| P8 Recorded decisions | Pass; Accepted ADR-0040 unchanged, routine implementation alignment without new policy or historical rewrite |
| P9 English repository | Pass; new repository prose/commits English, supplied Turkish review external |
| P10 Mermaid diagrams | N/A; no new diagram/image |
| P11 Reproducibility | Preserved; pins/provenance and exact original snapshots remain; statistical interpretation narrowed and source-bound new output verified |
| P12 Complete declared scope | Pass for ordinary B; no runtime stub, all eight tasks In Review, HIGH/phase/main/dispatch boundaries explicit |

Reviewed digests: ADR-0040 `5b82f632157033d193e64ac554390bacb9944fcd7a79fac9760a666c5f02ff2c`; policy `edd66dad0b4591c937556be55f6c473bf87e23173cde931c53347b6dc88b8a5b`; adapter `747b196e11e21340d0a7d607c7699fd129d58f9df54b96199ff6bad6907a55bd`; corrected perf harness `8a5d2d8042854f9324d424b73edf5de874032889218c39072b4ff52933944d47`.

No repository mutation, checkout, commit, push, live policy operation, API write, PR comment or external-person message was made. Only this temporary report is written; canonical publication/index/trailers belong to the coordinator. Official documentation was read through the web tool to verify cited service semantics; no live repository or organization administration state is inferred from those references.

## Verdict

**Approve for ordinary cumulative follow-up B at immutable 646ba33052632d5afda1e206007ed9bc334e8e3a. Zero new Blocker, High, Medium or Low findings. Blocking list: none. PR48-CR-01 and R1-INT-01 are verified resolved.**

All five roles, the complete checklist and P1–P12 are covered. This complete independent provisional report precedes waiting for the fresh peer. The scoped verdict does not authorize merge, promote tasks, close Phase B.2, certify future source/main/default dispatch or establish runtime safety. Existing HIGH T-038 x2 clobber remains open, excluded and undowngraded by green lint/Miri/smoke.

## Paired-review reconciliation

After writing the complete independent 160-line provisional report, read the full fresh paired integration artifact, first its provisional form and then its complete 155-line version with paired reconciliation. It independently Approves the same immutable cumulative B range with zero new findings and both R1 Low corrections resolved. Its five roles, full checklist, P1–P12, all 17 dispositions, historical preservation and exact-source hosted attribution agree with this review.

The peer independently ran seven performance methods in both modes and the scoped lints/invariants/link/digest/arithmetic checks; those remain peer evidence, not extra executions claimed here. Its 243-file preservation selection and this report's 246-file selection are separately defined subsets, not contradictory whole-repository counts. Original T-033 bytes, 393 links/38 fragments, YAML/harness invariants, task statuses and all cited digests agree. This report's four additional generated boundary reports remain this reviewer's execution. No unresolved finding, verdict, scope or evidence-attribution conflict emerged.

**Final verdict: Approve, zero new findings, PR48-CR-01 and R1-INT-01 resolved at exact 646ba33.** Canonical publication/index/trailers remain the coordinator's work. All eight tasks stay In Review; existing HIGH T-038 and first-main/default-dispatch evidence remain open. No future source or publication bytes are certified.

## Coordinator publication

The complete report above is published with the [paired canonical B Round 2 report](2026-10-12-pr48-docs-integration-r2.md). Private paths identify ephemeral acquisition/execution locations. The coordinator read both complete final reports and reconciled their matching Approve verdicts, zero new findings and verified PR48-CR-01/R1-INT-01 corrections at full `646ba33052632d5afda1e206007ed9bc334e8e3a`. Both fresh B rounds are complete; follow-up A already completed its distinct code/security rounds. This publication does not extend either verdict to later bytes, merge PR48 or promote tasks. Exact final publication-tip CI is checked separately.
