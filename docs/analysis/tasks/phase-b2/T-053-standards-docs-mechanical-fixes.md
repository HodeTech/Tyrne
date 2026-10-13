# T-053 — Apply mechanical corrections to the standards docs

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** In Progress
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-056](T-056-docs-consistency-automation.md)
- **ADRs required:** [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md) (Accepted 2026-10-12; reviewed execution and corpus policy)

---

> **Approved contract reconciliation (2026-10-12).** The maintainer approved the [preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and ADR package. The criteria below are the executable contract; dated opening observations remain historical. This preparation records no task delivery. Each implementation step includes verification and two fresh independent review rounds under [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); new task states stop at `In Review`.

## User story

As a contributor following the standards documents, I want their factual statements about tooling, lints, paths and conventions to match the repository, so that I am never told to rely on a gate, a path or a rule that does not exist.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). Track B.2-2 of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) lists eight standards-document corrections that need no decision, only a check against the repository: `error-handling.md` misstates where `panic = "abort"` is configured, `code-review.md` still calls CI "(planned)", the `commit-style.md` scope list and the `code-style.md` lint list are stale, `bsp-boot-checklist.md` quotes a fixed QEMU log path, three fences are untagged, `testing.md` has a stale parenthetical, and `release.md` has a grammar slip. Claims that need a **decision** (test-naming convention, register dump, `unimplemented!` lint, uniform deny coverage, logging status) are separate: [T-052](T-052-standards-docs-reality-sync.md).

## Acceptance criteria

- [ ] `docs/standards/error-handling.md` §"Panic strategy" (line 143 at opening): states that `-C panic=abort` is set by `.cargo/config.toml` `[target.aarch64-unknown-none] rustflags`, not by a `Cargo.toml` profile key, scoped to every build for that bare-metal target, including kernel/BSP and userland, and that host-side `cargo test` builds of kernel/hal/test-hal keep unwinding for the test harness (verified against `.cargo/config.toml` and the comment above `[profile.release]` in the root `Cargo.toml`).
- [ ] `docs/standards/code-review.md` §Tooling (lines 124-129): CI is described as live and merge-blocking (format, host and kernel clippy, host tests, kernel build, Miri; coverage informational and non-blocking), pointing to `infrastructure.md`; "Branch protection (planned)" is kept only if `infrastructure.md` still lists it as planned.
- [ ] `docs/standards/commit-style.md` scope list (lines 53-56) is refreshed from `git log --format=%s` and includes at least `perf`, `roadmap`, `analysis`, `audits`, `architecture`, `mmu`; recommend `syscalls`, `architecture` and `bsp-<board>` for new examples while documenting historical aliases/prior-use scopes without prohibiting them, with the rule "new scopes must appear in at least one prior commit or be agreed in review" kept.
- [ ] `docs/standards/code-style.md` §Lints (lines 118-130) lists every lint in the root `Cargo.toml` `[workspace.lints.*]` tables — adding `unreachable_pub` (warn), `unused_must_use` (deny) and `clippy::todo` (deny, keeping its rationale visible) — and states that `Cargo.toml` is authoritative.
- [ ] `docs/standards/bsp-boot-checklist.md` §"Enabling QEMU exception logging" (lines 218-224): replaces the fixed `/tmp/qemu_int.log` with the real behaviour — the path `${TMPDIR:-/tmp}/qemu_int.<pid>.log` is printed at startup; grep the printed path (verified against `tools/run-qemu.sh` lines 11-12 and 83).
- [ ] The three untagged fences — `commit-style.md` lines 15 and 25 and `testing.md` line 67 — carry a `text` tag; afterwards no opening fence in `docs/standards/` is untagged (record the check command used, for example an `awk` pass that tracks fence state).
- [ ] `docs/standards/testing.md` (line 82): the parenthetical "(to be added with the workspace)" after `test-hal` is removed (the crate exists).
- [ ] `docs/standards/release.md` (line 16): "an Tyrne-specific" becomes "a Tyrne-specific".

- [ ] Correct adjacent volatile tooling claims: missing_docs is warn but required Clippy -D warnings escalates it; cargo-audit/cargo-vet remain planned unless source shows delivery; smoke execution is live in CI and test guidance. Preserve all lint levels and the existing review-agreed scope-extension rule.

## Out of scope

- Any claim that needs a maintainer decision — [T-052](T-052-standards-docs-reality-sync.md).
- Adding the enforcement-status tagging ("Required / Planned / Advisory") to every standard; apply it only where a line you are already editing is a volatile CI/tooling claim, as `infrastructure.md` does.
- Changing any lint level, CI step or script.

## Approach

Verify each statement against its source of truth first (`.cargo/config.toml`, `ci.yml`, the root `Cargo.toml`, `tools/run-qemu.sh`, `git log`), then edit the sentence. Do not copy the review's wording; copy the repository's facts. For the scope list, run `git log --format=%s | grep -oE '^[a-z]+\(([a-z0-9/_.+, -]+)\)'` and document recommended examples separately from valid prior-use aliases; do not introduce a static allowlist or new prohibition. The fence at `testing.md:67` sits inside the test-naming block that T-052 may rewrite; tag it now unless T-052 has already replaced the block.

## Definition of done

- [ ] Every relative link in each touched file resolves.
- [ ] `git diff --stat` is limited to the standards documents named above, this task file and `docs/roadmap/current.md`.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) (scope `standards`).
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

**Step-scoped evidence allowance.** In addition to the named content files, the step may update this task, `docs/roadmap/current.md`, the B.2 task/track indexes, governing decision references, source-bound reports/raw evidence, canonical review artifacts and their indexes where necessary. Verify this allowance against the step commit range, not the full stacked branch. Record a demonstrated existing-scope reason for any further file.

## Design notes

- **Location re-verification (2026-10-11, HEAD `400dec0`):** all eight locations match the tree. Commit-scope counts at that date (from `git log`): `adr` 41, `roadmap` 40, `kernel` 14, `review-round` 13, `reviews` 7, `bsp` 7, `analysis` 7, `task` 6, `mmu` 6, `hal` 6, `syscall` 5, `perf` 5, `audits` 5, `arch` 5, `syscalls` 4 — evidence for the "which variant" decision.
- **Resolved 2026-10-12:** recommend syscalls/architecture/bsp-<board> for new examples; retain prior-use aliases, review-round/task and the existing review-agreement extension rule. No static scope ban is introduced.
- Sequencing: independent. If T-032 lands first, mention the new `hal`/`bsp` denies in the `code-style.md` list; otherwise leave the "deny in kernel paths" line for T-052.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-12 | Codex (AI agent), maintainer-approved reconciliation | Old: panic=abort kernel/BSP-only, alias canonicalization and eight narrow corrections. Approved replacement: target-wide flags including userland, recommended spellings with valid historical aliases/extensions, adjacent missing_docs/audit-vet/smoke truth and no lint-level change. See [approved preflight plan](../../reports/2026-10-12-phase-b2-track2-preflight-and-plan.md) and [ADR-0043](../../../decisions/0043-documentation-corpus-consistency.md); preparation only, status unchanged. |
| 2026-10-12 | Codex (AI agent), coordinator cross-reference check | ROOT-01: added the T-056 Informs backlink to match its newly explicit prerequisite/surface reference, following start-task step 9; no dependency scope or task state changed. |
| 2026-10-13 | Codex (AI agent), implementation author | Step 8 kickoff after T-055's completed two-round boundary at `98378b5`; verified prerequisites and approved choices. See [source-bound preflight](../../reports/2026-10-13-t052-t053-standards-preflight.md), including additional existing-scope tooling-file reasons recorded before edits. Status In Progress; no delivery or review claim. |
| 2026-10-13 | Codex (AI agent), implementation author | T-053 content: target-wide panic flags, live target-aware CI/smoke, actual lint entries and warning escalation, history-derived valid scopes, printed QEMU log path, all three fence tags and grammar/test-hal fixes. Pre-recorded security-review/P11/infrastructure additions correct adjacent tooling delivery claims while preserving required properties. No source/configuration/CI/lint-level change. Verification and both fresh paired rounds remain pending. |
