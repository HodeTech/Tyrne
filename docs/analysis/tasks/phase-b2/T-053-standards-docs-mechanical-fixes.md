# T-053 — Apply mechanical corrections to the standards docs

- **Phase:** B.2
- **Milestone:** Track B.2-2
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** none
- **ADRs required:** none

---

## User story

As a contributor following the standards documents, I want their factual statements about tooling, lints, paths and conventions to match the repository, so that I am never told to rely on a gate, a path or a rule that does not exist.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). Track B.2-2 of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) lists eight standards-document corrections that need no decision, only a check against the repository: `error-handling.md` misstates where `panic = "abort"` is configured, `code-review.md` still calls CI "(planned)", the `commit-style.md` scope list and the `code-style.md` lint list are stale, `bsp-boot-checklist.md` quotes a fixed QEMU log path, three fences are untagged, `testing.md` has a stale parenthetical, and `release.md` has a grammar slip. Claims that need a **decision** (test-naming convention, register dump, `unimplemented!` lint, uniform deny coverage, logging status) are separate: [T-052](T-052-standards-docs-reality-sync.md).

## Acceptance criteria

- [ ] `docs/standards/error-handling.md` §"Panic strategy" (line 143 at opening): states that `-C panic=abort` is set by `.cargo/config.toml` `[target.aarch64-unknown-none] rustflags`, not by a `Cargo.toml` profile key, scoped to the kernel/BSP build, and that host-side `cargo test` builds of kernel/hal/test-hal keep unwinding for the test harness (verified against `.cargo/config.toml` and the comment above `[profile.release]` in the root `Cargo.toml`).
- [ ] `docs/standards/code-review.md` §Tooling (lines 124-129): CI is described as live and merge-blocking (format, host and kernel clippy, host tests, kernel build, Miri; coverage informational and non-blocking), pointing to `infrastructure.md`; "Branch protection (planned)" is kept only if `infrastructure.md` still lists it as planned.
- [ ] `docs/standards/commit-style.md` scope list (lines 53-56) is refreshed from `git log --format=%s` and includes at least `perf`, `roadmap`, `analysis`, `audits`, `architecture`, `mmu`; spelling variants that coexist in history (`syscall`/`syscalls`, `arch`/`architecture`, `bsp`/`bsp-<board>`) are resolved to one documented form each, with the rule "new scopes must appear in at least one prior commit or be agreed in review" kept.
- [ ] `docs/standards/code-style.md` §Lints (lines 118-130) lists every lint in the root `Cargo.toml` `[workspace.lints.*]` tables — adding `unreachable_pub` (warn), `unused_must_use` (deny) and `clippy::todo` (deny, keeping its rationale visible) — and states that `Cargo.toml` is authoritative.
- [ ] `docs/standards/bsp-boot-checklist.md` §"Enabling QEMU exception logging" (lines 218-224): replaces the fixed `/tmp/qemu_int.log` with the real behaviour — the path `${TMPDIR:-/tmp}/qemu_int.<pid>.log` is printed at startup; grep the printed path (verified against `tools/run-qemu.sh` lines 11-12 and 83).
- [ ] The three untagged fences — `commit-style.md` lines 15 and 25 and `testing.md` line 67 — carry a `text` tag; afterwards no opening fence in `docs/standards/` is untagged (record the check command used, for example an `awk` pass that tracks fence state).
- [ ] `docs/standards/testing.md` (line 82): the parenthetical "(to be added with the workspace)" after `test-hal` is removed (the crate exists).
- [ ] `docs/standards/release.md` (line 16): "an Tyrne-specific" becomes "a Tyrne-specific".

## Out of scope

- Any claim that needs a maintainer decision — [T-052](T-052-standards-docs-reality-sync.md).
- Adding the enforcement-status tagging ("Required / Planned / Advisory") to every standard; apply it only where a line you are already editing is a volatile CI/tooling claim, as `infrastructure.md` does.
- Changing any lint level, CI step or script.

## Approach

Verify each statement against its source of truth first (`.cargo/config.toml`, `ci.yml`, the root `Cargo.toml`, `tools/run-qemu.sh`, `git log`), then edit the sentence. Do not copy the review's wording; copy the repository's facts. For the scope list, run `git log --format=%s | grep -oE '^[a-z]+\(([a-z0-9/_.+, -]+)\)'` and decide which variants to bless. The fence at `testing.md:67` sits inside the test-naming block that T-052 may rewrite; tag it now unless T-052 has already replaced the block.

## Definition of done

- [ ] Every relative link in each touched file resolves.
- [ ] `git diff --stat` is limited to the standards documents named above, this task file and `docs/roadmap/current.md`.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) (scope `standards`).
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Location re-verification (2026-10-11, HEAD `400dec0`):** all eight locations match the tree. Commit-scope counts at that date (from `git log`): `adr` 41, `roadmap` 40, `kernel` 14, `review-round` 13, `reviews` 7, `bsp` 7, `analysis` 7, `task` 6, `mmu` 6, `hal` 6, `syscall` 5, `perf` 5, `audits` 5, `arch` 5, `syscalls` 4 — evidence for the "which variant" decision.
- **Open decisions:** which spelling variant of each scope pair becomes canonical; whether `review-round` and `task` (used as scopes in history) are blessed or discouraged. Record the choice in the review history.
- Sequencing: independent. If T-032 lands first, mention the new `hal`/`bsp` denies in the `code-style.md` list; otherwise leave the "deny in kernel paths" line for T-052.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
