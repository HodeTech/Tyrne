# T-049 review-corpus reconciliation — 2026-10-13

- **Task / approved scope:** [T-049](../tasks/phase-b2/T-049-review-indices-sync.md), Step 5 of the [approved plan](2026-10-12-phase-b2-track2-preflight-and-plan.md), under [ADR-0043](../../decisions/0043-documentation-corpus-consistency.md).
- **Comparison / executed source:** clean `development` at `0ab0ba427ae97d5233afd01dfe7205b1ae8bc0c3`, after the kickoff at completed T-048 source `468812b8e765f655edcfcfca161586e609d2478f`. Archive/report changes described here are subsequent implementation edits; they are not claimed to exist at the executed source.
- **State:** [Both fresh primary/complementary rounds](../reviews/code-reviews/2026-10-13-t049-review-corpus-reconciliation.md) complete at `aa37e2c`; the one confirmed Low C01 is corrected and independently verified. T-049 is In Review. No Done, main merge, hosted CI or old-review re-approval is claimed.
- **Evidence:** [retained evidence directory](2026-10-13-t049-review-evidence/README.md), including [navigation/source-object ledger](2026-10-13-t049-review-evidence/navigation.json), [preparation reads](2026-10-13-t049-review-evidence/preflight-read-ledger.json) and [verification results](2026-10-13-t049-review-evidence/verification.json).

## Discovery and structural changes

The missing business Phase B closure, three security closure reports and B6 performance closure now have rows in their own family tables. Their original dates and verdicts were copied from the reports: each security report retains Approve, and B6 retains Re-baseline, no regression. Business/performance tables retain their Date / Scope / File shape; security retains its Verdict column.

The code index identifies the May-6 companion plan separately from canonical verdicts. Existing nested May-6, May-7 and May-8 tracks remain discoverable from their canonical reports. Both analysis/review entry points distinguish the four event-triggered types with master plans from the on-demand whole-tree master-review family. The May-22 consolidated report now links its manifest and all 25 tracks in a dated appendix; its entire prior body remains an exact prefix.

B6 gains dated Hotspot, Proposal, Measurement and Regression check sections before its original Verdict, plus the index acceptance item. They describe the existing re-baseline, same-host control and original micro-measurements; they introduce no optimization target, retrospective run or improved verdict. Host drift, noise floor, TCG limitations, absent full raw smoke trace and the distinction between reused unsafe operations and added call sites are explicit. No unrecorded whole-B6 unsafe-site count is invented.

The business master-plan gains the approved closure-batch discovery sweep alongside the existing T-045 architecture/smoke requirements. Business/security master-plan navigation is corrected.

## Historical navigation and evidence integrity

The preparation baseline at `550500f` found 48 broken navigation occurrences, rather than 48 unique destinations: 41 missing paths and seven fragment issues. All have bounded dispositions. The full preparation read covered 35 existing documents / 6,137 lines / 76 untruncated chunks; it is not either implementation-review round.

Retired skill links use verified full-SHA historical permalinks. Different review periods retain their own skill versions, including the earlier B1 content and the later Simulation amendment. Removed `hal/src/mmu.rs` links open the reviewed May-6 source. Wrong-depth paths, missing heading fragments and malformed source-line destinations are corrected. Original quoted defective/proposed Markdown in master tracks remains exact literal data with adjacent dated functional navigation; the D2b fenced reference definition is unchanged. The optional `.gitattributes` input, absent from both the tree and available path history, is explicit filename data. No fake destination, archive waiver or note-only broken-link exception is introduced.

Within the already-owned May-6/May-7 files, 419 original local line citations now bind to their review-era source: 418 originally rendered citations and one malformed label repaired explicitly. Original labels/fragments remain historical, except the documented unmatched backtick/spacing repair in the May-6 test track. Four original ranges were imprecise or incomplete; dated supplementary ranges clarify the boot entry, IPC queue-full test, F1 blocker and audit tag without erasing the original citations. Two later PR-18 closure links bind to `25854a1949ed9cec0de46d10955a27ddbba774bc`, rather than the older May-7 tip. Nine misleading SHA-labelled directory destinations now open their exact verified commits.

The 419 citation occurrences overlap seven of the 48 baseline repairs; these classes must not be summed as independent findings. The retained ledger contains 58 other navigation disposition records, including grouped SHA occurrences, plus the 419 citations. These ledger records are unrelated to the track's separate 58-disposition acceptance inventory. There are 451 rendered occurrences of 363 distinct delivered immutable blob URLs, covering 82 distinct commit/path pairs; URL ranges and Git objects are different count units. The preparation/mutation stage verified 364 URL keys, including two superseded same-blob aliases; the delivered-target map records the actual current destinations, including D2b's added source link.

Markdown source-line permalinks use `?plain=1#L…`, following [GitHub's Markdown source-link documentation](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-a-permanent-link-to-a-code-snippet#linking-to-markdown). The recorded URLs were checked against local Git objects and ranges. This is not a live HTTP availability check or independent proof of every original code claim or historical run.

## Fresh execution

[Miri validation](2026-10-13-t049-miri-validation.md) executed the pinned workspace command with only the BSP excluded: 366 passed, zero failed, two ignored HAL doc-tests, seven retained integer-to-pointer warnings, no reported UB on exercised host paths. The report distinguishes exposed-provenance limitations, userland's zero host tests and unexercised bare-metal/EL0 behavior.

[Coverage rerun](2026-10-13-t049-coverage-rerun.md) executed the repository command: 363 unit tests passed; 28 files; regions 96.31%, functions 93.13%, lines 95.87%. Branch coverage is unmeasured. Local cargo-llvm-cov 0.9.0 differs from CI's 0.6.16; no identical-denominator or hosted-run claim is made. Raw logs, commands, tools, environment, timestamps, clean-tree checks and SHA-256 are retained. Both commands executed clean `0ab0ba4` before these documentation edits.

## Coordinator verification and boundaries

The one-off comparison checked 25 historical bodies: original non-destination text is exact after the declared navigation/literal/label changes and dated additions are accounted for. B6's prior measurements, verdict and four acceptance items remain unchanged; the consolidated report is append-only, and D2b's original body is exact after removing its dated annotation. All 419 original line citations were checked against their recorded original Markdown and historical source excerpts/objects; original-label precision caveats remain visible.

Discovery membership is complete for 14 business, 21 security, eight performance files, and 27 code canonicals plus one companion plan. All 25 May-22 tracks and its manifest are linked. The one-off rendered-navigation diagnostic found no missing local paths or fragments across the review corpus and new report surfaces; exact snapshot counts and scope are in the verification JSON. It uses Python Markdown for a bounded diagnostic and independently checks heading/line targets. It is not the future T-056 parser, grammar or fixture suite. Raw-log hashes, process exits, 366/363 passing totals and two/zero ignored totals were independently checked.

No Rust, build, toolchain, dependency or CI implementation changed. No new runtime/security behavior is claimed. Both fresh rounds and the verified correction are retained in the canonical review. Its index row is inside the existing code-review table, before Companion plans. The implementation-tip discovery snapshot above remains historical; publication adds one canonical report, yielding 28 code canonicals plus one companion.

## Round-1 correction and verification detail

The primary five-role review requested changes for C01: the May-6 infrastructure track's proposed back-pointer had been rewritten relative to the archive, although its original destination was correct for the proposed `infrastructure.md` sentence. The exact original Markdown is now literal proposal data with adjacent dated archive navigation. The complementary evidence review approved its stated scope with no confirmed findings; neither report is broadened beyond its actual reading/verification scope. Original R1 findings/verdicts and subsequent verification will be retained in the canonical review.

Default `git diff --check` reports the original captured Miri log's blank EOF line (543). Both raw runtime hashes remain unchanged; raw command output is not cosmetically normalized. The check over all non-log changes passes with the two retained raw logs excluded explicitly; the logs are verified byte-for-byte and by SHA-256 instead. This is a narrow raw-evidence formatting observation, not a globally clean default whitespace-check claim.

## Publication verification — 2026-10-13

After both R2 verdicts, coordinator checks over the publication working tree on `aa37e2c` retained all four actual context reports exactly and revalidated the 25 historical comparisons, 419 citation bindings, raw hashes, master-run discovery and lifecycle. Expanded navigation scope: 145 Markdown files, 2,143 local targets and 331 fragments, zero errors; it includes T-045 overview/loader/index and the repaired master-plan. The original verification JSON remains the implementation-stage snapshot. Code discovery now contains 28 canonicals plus one separate companion. New task counts are eight Done / 25 Ready / five In Review / eight Draft, with none In Progress at this boundary. These are coordinator bookkeeping checks, not another independent review or clean-runtime source claim.
