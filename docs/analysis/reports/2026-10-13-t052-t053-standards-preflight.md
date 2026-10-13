# T-052 / T-053 — Step 8 source review and execution plan

- **Date:** 2026-10-13
- **Coordinator:** Codex (AI agent), implementation author; not an independent reviewer
- **Source:** `98378b5add44755f7cbab6e8bc96337accf0574a` on `development`
- **Authority:** maintainer-approved [13-step plan](2026-10-12-phase-b2-track2-preflight-and-plan.md), [T-052](../tasks/phase-b2/T-052-standards-docs-reality-sync.md), [T-053](../tasks/phase-b2/T-053-standards-docs-mechanical-fixes.md), Accepted [ADR-0042](../../decisions/0042-descriptive-test-names.md) and [ADR-0043](../../decisions/0043-documentation-corpus-consistency.md).
- **State:** implementation preflight; no delivery, independent review, new runtime result or maintainer completion claimed.

## Reviewed sources and decisions

The coordinator reread both complete task contracts and the complete owned standards. Full root Cargo/config and all six member lint opt-ins, exact crate attributes/scoped allowances, panic/exception/userland-stub spans, complete hello source, runner scripts and relevant live CI/protection configuration were checked. This is source inspection, not fresh Cargo/QEMU/hosted execution. T-032 is Done and its kernel/HAL/BSP denies exist. ADR-0042 is Accepted and ADR-0041 already Superseded atomically; no unresolved rule choice remains.

| T-052 choice | Classification and implementation |
|---------------|----------------------------------|
| Test names | Rule change authorized by Accepted ADR-0042: descriptive snake_case, no mandatory test_ prefix, concise unambiguous names allowed; three actual IPC identifiers and motivating References link. No rename or naming lint. |
| Panic diagnostics | Approved claim correction: current QEMU BSP emits banner and formatted PanicInfo, then spins. Exception-specific class/ESR diagnostics are separate from a generic register dump. No automatic register-dump follow-up. |
| Incomplete markers | Approved claim correction: workspace Clippy todo deny; no unimplemented deny. Preserve two intentional non-bare-metal user-library stubs and review completeness of reachable runtime paths. |
| Logging | Approved claim correction: structured facade/rings/log service/metrics/configuration are planned; current diagnostics use raw Console/BSP UART. Preserve secret-redaction and nonblocking-context constraints. |
| Deny scope | Approved claim correction: kernel/HAL/QEMU BSP carry panic-family denies with explicit scoped allowances; test-hal/userland inherit workspace lints only. No lint-level change. |

Adjacent TaskFault/supervision/reclamation prose must distinguish intended Phase-E/E3 design from the current non-SVC EL0 whole-kernel panic and retained task/address-space/frame state after explicit exit. Hello's own panic calls task_exit(101); that is not general fault containment.

## Focused commits and review boundary

1. Kick off both tasks and retain source-bound inventory before content edits.
2. T-052 content commit: four named standards plus any demonstrated restatement of the five claims, classifications and downstream dispositions.
3. T-053 content commit: actual panic flags for every aarch64-unknown-none build, live target-aware tooling, current lint table, missing_docs/-D warnings boundary, scope history, printed QEMU log path, fence tags, test-hal and release grammar.
4. Freeze cumulative Step 8 source for two complementary fresh code/security reviewers; verify/fix/commit actual findings. Repeat with two different fresh contexts over the whole corrected step. Actual paired reports are cross-read and retained, with parallel initial passes attributed accurately.
5. Publish canonical reviews/evidence and move both tasks only to In Review, then continue Step 9/T-054 automatically. No date_done or maintainer approval is inferred.

## Additional file scope, recorded before editing

These are bounded corrections of the already-approved adjacent volatile tooling claims, not new standards policy:

- `docs/standards/security-review.md`: its Tooling section falsely calls cargo-audit/cargo-vet live CI gates; current infrastructure/CI makes them planned at the first external dependency. Align that delivery status only.
- `docs/standards/architectural-principles.md`: P11's current-tense cargo-vet claim needs a delivery-status note. Preserve P11's normative Statement, Why and Applies to in full; do not weaken reproducibility or dependency audit requirements.
- `docs/standards/infrastructure.md`: Reproducibility bullets are required properties, not proof of an existing binary-comparison job. Add a factual status note distinguishing pinning/build checks from absent cross-run bit comparison/certification; preserve the required properties.
- Necessary task/current/task-index/approved-plan records, this source-bound report/evidence, canonical review artifacts and their indexes are covered by the tasks' step-scoped evidence allowance. No runtime, lint, CI, runner or branch-protection file is selected for mutation.

## Downstream search and verification

[Retained search](2026-10-13-t052-t053-verification-evidence/downstream-baseline.txt) captures 141 broad matched lines across `.agents/skills/`, architecture and standards; these are search hits, not 141 defects. All hits were read in bounded outputs. The completion evidence must list updated owner documents and explicit unchanged historical/normative/already-accurate dispositions. Accepted/Superseded ADR bodies remain historical.

[Scope inventory](2026-10-13-t052-t053-verification-evidence/scope-baseline.json) binds actual git-log extraction to the source above. Recommend syscalls/architecture/bsp-<board> while preserving prior-use aliases and the existing prior-commit OR review-agreement extension rule; never turn this inventory into an allowlist.

Verify source-backed claims, exact task/index/current state and step-only allowed paths; ensure executable/config/CI bytes unchanged; check all touched relative paths/fragments and every standards opening fence using a stateful parser, and run diff whitespace checks while attributing any inherited raw-log EOF exceptions separately. Prose-only edits do not warrant new runtime tests; no source inspection is reported as test execution. PR #49 remains the publication barrier; no push, remote-policy change or external message is authorized by this step.
