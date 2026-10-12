# PR48 supplied-review reconciliation — 2026-10-12

This author-maintained disposition records all 17 numbered findings in the maintainer-supplied systematic review of [PR48](https://github.com/HodeTech/Tyrne/pull/48) at `1e281ac89d791dc3c6920a038ec26381a49623f3`.
It separates verified corrections from claims that were narrower, historical or unsupported by the evidence.
It is not a fresh independent review, a maintainer approval, a Done promotion or a Phase B.2 closure record.

## Scope and execution

Follow-up A implements the host-tool corrections in `50ab72bf2c15a4d34be25a1491a357313e50390a` and the shared Low cache-comment correction in `683965b5aa2f5da2e11429aa42803bb3a5fa6f60`.
Its full [code R1](../reviews/code-reviews/2026-10-12-pr48-tools-followup-r1.md) and [separate security R1](../reviews/security-reviews/2026-10-12-pr48-tools-followup-r1.md) preserve the immutable reviewed source, execution details, limits and finding disposition.
Fresh [code R2](../reviews/code-reviews/2026-10-12-pr48-tools-followup-r2.md) and [security R2](../reviews/security-reviews/2026-10-12-pr48-tools-followup-r2.md) approve cumulative source through `683965b`, verify the shared Low correction and report zero new findings; both A rounds are complete.
Follow-up B corrects current prose/examples and adds explicit historical/context mappings below.
Each follow-up step requires two fresh independent rounds; their actual completion is recorded in the task histories and subsequent review artifacts, not inferred from this reconciliation.

The current protection definition and production adapter are unchanged by these follow-ups.
No new CODEOWNERS, approval count, administrator-enforcement setting, environment or ruleset is adopted.
These corrections implement [Accepted ADR-0040](../../decisions/0040-phase-b2-consolidation-bridge.md); its body remains byte-identical.

## Finding dispositions

| ID | Verified disposition | Action / evidence |
|----|----------------------|-------------------|
| M-1 | Claimed English-language violation refuted; optional clarity accepted. | The UN uses the official country name in English. The weekly guide now gives UTC only. |
| M-2 | Producer-app/workflow-integrity boundary verified; specific duplicate-job bypass not demonstrated. | Guide/header explain actual boundary, admin bypass and zero approval count; no new protection policy. |
| M-3 | Current live failure refuted; future response-shape limitation verified. | Full actual REST fixture, equality test and conservative unsupported-field cases; adapter remains unchanged. |
| L-1 | Missing spaces verified in current prose. | Corrected guide, infrastructure, phase and task index; immutable historical reports retained. |
| L-2 | Documentation drift verified; command count needs qualification. | Actual per-job setup, coverage exclusions, observed Miri time, exact key versus prefix, fixture failures and ARM order aligned. |
| L-3 | Instruction-fault token mismatch verified. | Smoke and both-profile fixtures now reject `Undefined Instruction`; current task design note aligned. |
| L-4 | Optional Rust metadata failure verified. | Four metadata commands fall back to unknown while retaining valid samples; failure-output canaries tested. |
| L-5 | Empty-diagnostic latent acceptance verified. | Nonempty guard and regression test reject before the negative command executes. |
| L-6 | Mixed: T-033 role headings noncanonical; approval template and compressed range were valid. | Additive role mapping, clearer index ranges/template identity, checklist-label mapping below; original reports retained. |
| L-7 | Historical identifying metadata verified. | New reports omit the normal override explanation and hostname; old source-bound measurements retained. |
| L-8 | An already-failing source could satisfy the diagnostic class. | Same exact command must pass on clean private source before the six-cfg mutation; baseline failure tests added. |
| I-1 | Unqualified header verified; GraphQL boolean/count combination is valid distinct data. | Header caveat aligned; neither property inferred from the other. |
| I-2 | Unnecessary installed-executable cache surface verified. | Removed five cargo-bin paths; registry/build caches remain trusted build inputs. |
| I-3 | Per-PR runner-capacity boundary acknowledged; billing/organization controls unverified. | Document existing per-ref concurrency and 10/15-minute smoke/ARM limits; no external settings claim. |
| I-4 | No attestation defect established. | Existing honest reviewer provenance retained; agent verdicts are not maintainer signatures or runtime model attestation. |
| I-5 | Intentional exact-byte filename/internal-title difference. | Explicit snapshot provenance below; report bytes unchanged. |
| I-6 | Opening four-check reference lacked nearby qualification. | T-034 criterion labels opening snapshot versus the current six-check policy. |

## Boundaries behind the dispositions

M-1 does not justify replacing one English country name with another as a constitutional repair.
The [UN English-language announcement](https://turkiye.un.org/en/184798-turkeys-name-changed-t%C3%BCrkiye) supports the official name; UTC-only wording is a routine simplification.

For M-2/I-1, app ID 15368 binds a check producer, not a workflow body or trusted source revision.
Workflow/tool changes and the actual run therefore remain subjects of maintainer review.
The existing policy permits administrator bypass, requires zero approvals and disables code-owner review.
Duplicate check names can introduce ambiguity and block merging; the supplied report's particular instant-success duplicate bypass was not reproduced or established.
See [GitHub protection semantics](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

For M-3, enforcement scope and review dismissal/bypass actors carry policy and must not be discarded as harmless metadata.
The [protection endpoint](https://docs.github.com/en/rest/branches/branch-protection#get-branch-protection) and [branch-summary endpoint](https://docs.github.com/en/rest/branches/branches#get-a-branch) have different response shapes.
The dated [actual protection fixture](../../../tools/fixtures/README.md) pins one observed body; it does not promise every future shape is supported or substitute for GraphQL/ruleset reads.
Unknown unrepresentable policy remains refused before writes.
The full read-only live policy check passed separately; a fixture is not live-drift attestation.

For L-8, both exact compiler classes remain necessary because Cargo's parallel all-target build can expose the normal binary or test harness first; an E0152-only assertion already caused a real hosted flake.
The clean same-command control rejects an already-broken baseline before mutation without weakening the diagnostic/exit-101 requirement.
This is a controlled regression assertion under trusted tools, not a proof against nondeterministic external failure or a hostile compiler.

For I-2/I-3, removing installed binaries narrows one cache overwrite route; it does not make registry/git/target caches integrity-attested.
[GitHub cache scope](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching) prevents ordinary PR merge-ref caches from restoring into the base or sibling PRs, while the same PR's reruns can restore them.
Per-ref cancellation does not bound distinct PRs; organization approval/capacity settings were not verified or changed.

## Historical artifact reconciliation

The ADR-0040 approval follow-up correctly uses the dedicated `conduct-approval-review` template.
That skill mandates no separate storage folder; inclusion in the code-review index does not change the artifact's declared type.
The index now makes that distinction explicit without relocation or invented process requirements.

T-033's R1 numbered headings contain all five roles; an [additive role map](../reviews/code-reviews/2026-10-12-t033-qemu-tooling.md#supplied-review-role-heading-reconciliation-2026-10-12) makes them directly discoverable without rewriting the original review.
The T-030 security index previously summarized the cumulative final range, not an incorrect R1 claim; it now names R1 and R2 separately.
`MP-1` in the security master plan and `MP-33` in some historical artifacts denote the same extra allocation-exhaustion item after the 32 standard items, not different or missing checks.
New checklist references use `MP-1`; historical labels and their 33 dispositions remain preserved.

Historical local/hosted performance reports retain their original source identity, metadata and raw measurements.
New metadata minimization does not retroactively certify or redact every auxiliary artifact, arbitrary successful tool output or older report.
The [first hosted snapshot](perf-baseline-2026-10-12-t035-hosted-check.md) keeps its internal `ci-nightly` title because its bytes were copied from the downloaded report.
The [follow-up hosted snapshot](perf-baseline-2026-10-12-t035-pr48-followup-hosted-check.md) follows the same convention and records the changed harness at clean full `50ab72bf2c15a4d34be25a1491a357313e50390a`.
Its SHA-256 is `24c143abb0151de1eb3fb38ff3d74f3e060effd2a6c492cc8389bebca565ae85`; this is the report-file digest, not a locally recomputed artifact-archive digest.
All 20 raw samples independently reproduce p10/p50/p90 `5,232,672 / 5,473,392 / 7,277,776 ns`; no calibrated or cross-host regression verdict follows.

## Remaining review and merge boundary

All eight requested tasks remain **In Review** for the maintainer in PR48; none is promoted to Done by this document.
Existing **HIGH T-038** remains open and excluded; smoke, lint and Miri successes do not certify the x2 assembly contract.
First merged-main runs and the default-branch performance dispatch require the maintainer's merge and remain explicitly pending in [T-035](../tasks/phase-b2/T-035-ci-hygiene-tail.md).
They are merge-dependent evidence, not deferred implementation of this follow-up.
