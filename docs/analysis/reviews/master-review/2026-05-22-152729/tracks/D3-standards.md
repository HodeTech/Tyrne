# D3-standards — standards docs (master review, commit 288ddb2)

## Summary

The Tyrne standards library is in remarkably good shape for a pre-alpha project.
The documents are well-written, internally coherent, and clearly aimed at a serious kernel-development audience.
The majority of findings are standard↔reality drift items — the standards describe aspirational or planned infrastructure (QEMU-smoke CI gate, cargo-audit/cargo-vet CI gates, `tyrne-log` crate, `docs/architecture/security-model.md`) that does not yet exist, without always flagging the gap honestly.
The most load-bearing defects are: (1) two stale `.claude/skills/` paths in `infrastructure.md` that silently break the "wired in once the first external dependency lands" contract; (2) the CI header claims both Miri and coverage "are still required for merge" while `coverage` runs with `continue-on-error: true` — a factual lie in the CI file that every contributor reads; (3) `release.md` lists QEMU-smoke, `cargo-audit`, and `cargo-vet` as required release gates that do not yet exist in CI; (4) `infrastructure.md` says "CI runs against the pinned toolchain only" but the `lint-and-host-test` and `kernel-build` jobs use `stable`, not the pinned nightly; (5) a recurring pattern of non-Conventional-Commits subjects on `main` that `commit-style.md` prohibits and no CI gate catches.

Severity breakdown: **3 Blockers, 5 Major, 8 Minor, 5 Nits, 4 Praise**.

---

## Findings (by severity)

### Blocker

---

#### D3-001 — Stale `.claude/skills/` paths in `infrastructure.md` (two instances)

**File:** `docs/standards/infrastructure.md:72` and `infrastructure.md:192`

**Description.**
Both occurrences link to `../../.claude/skills/add-dependency/SKILL.md`.
The `.claude/skills/` directory was removed on 2026-05-14 (commit `77d3e7e`) as part of the `.claude/skills/ → .agents/skills/` migration; the skill now lives at `.agents/skills/add-dependency/SKILL.md`.
The links are broken on disk: `ls .claude/skills/` returns "No such file."
`infrastructure.md` is load-bearing: its "conditional — see add-dependency skill" note is the **trigger** that tells maintainers when and how to wire up cargo-audit and cargo-vet.
If a contributor follows the link they reach a 404, which breaks the cargo-vet onboarding path entirely.

Line 72: *(Conditional — currently dormant … wired in once the first external dependency lands per [add-dependency](../../.claude/skills/add-dependency/SKILL.md).)*
Line 192: *The `supply-chain/` directory does not exist at HEAD — see [add-dependency](../../.claude/skills/add-dependency/SKILL.md) for the trigger that creates it.*

**Suggested fix.**
Replace both occurrences:
`../../.claude/skills/add-dependency/SKILL.md` → `../../.agents/skills/add-dependency/SKILL.md`

---

#### D3-002 — CI header claims coverage "required for merge" but job is `continue-on-error: true`

**File:** `.github/workflows/ci.yml:6` (header comment) vs `ci.yml:140` (`continue-on-error: true`)

**Description.**
The CI file's header says: *"The Miri and coverage jobs are slower and run conditionally to keep median PR feedback tight; they are still required for merge into `main`."*
The `coverage` job at line 140 carries `continue-on-error: true`, which means GitHub treats a coverage failure as a passing check — the job will never block a merge.
No other branch-protection configuration enforces it independently.
This is a direct factual contradiction between the comment (a standard in effect for all CI contributors) and the actual YAML behavior.
`testing.md` and `infrastructure.md` both characterize the CI gates as merge-blocking; this contradiction undermines both.

**Suggested fix.**
Either: (a) remove `continue-on-error: true` from the `coverage` job once a floor is agreed and the job is reliable; or (b) update the header comment to say *"Miri is required for merge; coverage is currently informational and does not block merge"* to accurately reflect today's state.
Preferred: (b) now, with a TODO comment naming the milestone at which `continue-on-error` is removed.

---

#### D3-003 — `release.md` process gate lists CI jobs that do not exist (QEMU smoke, cargo-audit, cargo-vet)

**File:** `docs/standards/release.md:61`

**Description.**
The process gate checklist reads: *"All CI gates green on the commit being released (format, clippy, tests, build, QEMU smoke, `cargo-audit`, `cargo-vet`)."*
None of these three jobs exist in `.github/workflows/ci.yml`:
- `qemu-smoke` — explicitly noted in `infrastructure.md:71` as "maintainer-launched only; no CI job yet."
- `cargo-audit` — explicitly noted as "currently dormant."
- `cargo-vet` — same conditional dormant note.

A gate checklist item that cannot be ticked off because the required CI job does not exist gives contributors a false picture of the release standard, or (worse) tempts them to skip the gate reasoning because "CI is red and there's nothing to be done."

**Suggested fix.**
Annotate the checklist items that reference missing CI jobs with the same honest parenthetical `infrastructure.md` uses:

```
- [ ] All CI gates green on the commit being released (format, clippy, tests, build,
  QEMU smoke *(maintainer-launched; no CI job yet — see infrastructure.md)*, 
  `cargo-audit` *(dormant until first external dep lands)*, 
  `cargo-vet` *(same conditional)*.
```

Or, if the gates are aspirational, move them to a separate "aspirational gates — not yet enforced" sub-list.

---

### Major

---

#### D3-004 — `infrastructure.md` claims "CI runs against the pinned toolchain only" but `lint-and-host-test` and `kernel-build` use `stable`

**File:** `docs/standards/infrastructure.md:19`

**Description.**
The standard says: *"CI runs against the pinned toolchain only. Multiple-toolchain matrices are not currently useful for a `no_std` kernel."*
In reality, `.github/workflows/ci.yml` has two jobs (`lint-and-host-test`, `kernel-build`) that install `rustup default stable` — not the pinned nightly — and only Miri and coverage use `NIGHTLY_PIN`.
`rust-toolchain.toml` pins `nightly-2026-01-15`, which means contributor machines use that nightly, but CI's two main jobs run on `stable`.
This is a real divergence: a `#[feature(...)]` flag that works on nightly might not compile on stable, and a stable build that passes CI could fail for a contributor on nightly (or vice-versa).
The standard claim is factually wrong.

**Suggested fix.**
Either: (a) update the standard to say *"CI's fast lane (lint + host tests + kernel-build) runs on stable; Miri and coverage run on the pinned nightly"* (which describes reality accurately); or (b) switch all CI jobs to the pinned nightly and make the standard claim true.
Preferred: (b), since the kernel's `rust-toolchain.toml` is nightly, and the standard's intent (determinism, no silent breakage) is best served by having CI use the same toolchain as local builds.

---

#### D3-005 — `commit-style.md` type/scope list not enforced in CI; non-compliant commits on `main`

**File:** `docs/standards/commit-style.md:38–53`

**Description.**
`commit-style.md` requires Conventional Commits format (`<type>(<scope>): <subject>`), defines a fixed type list, and lists allowed scopes.
`git log --format="%s"` on `main` shows multiple non-compliant commits that have merged:

- `docs,kernel,bsp: T-019 review-round 6 follow-up (5 valid findings)` — no parentheses around scope; comma-separated types in the subject position.
- `hal,kernel,docs: T-019 review-round 5 follow-up (P1 + P2 + P3)` — same pattern.
- `docs+tools: integration-PR review-round wrap-up …` — `+` separator, not standard.
- `test+refactor(kernel): T-011 missing tests bundle` — two types joined with `+`.
- `fix+docs: apply post-A6 code-review feedback` — same.
- `feat(kernel/ipc, kernel/sched): …` — slash-separated sub-scope, space in scope list.
- `feat(a5): …` — scope `a5` is not on the allowed list.
- `audit: R1 …`, `audit: R2 …`, `audit: R3 …` — `audit` is not a type in the list.
- `style(sched): …` — `style` is not a listed type (closest is `chore` or `refactor`).

The standard defines this as the project's commit history contract, yet the tooling section admits `.gitmessage` is "to be added" and commitlint CI validation is "planned."
Without enforcement, the standard documents an aspiration that is drifting from reality on every PR.

**Suggested fix.**
Short term: add the undocumented types (`audit`, `style`) to the allowed list if they are intentional, or flag them as violations to fix retroactively in a `chore` commit.
Medium term: add a `commitlint` or equivalent GitHub Actions step that validates the PR merge-commit subject against the type/scope list before merge.
Also: `style` is a well-known Conventional Commits type used by the `aarch64-cpu` and other Oxide/embedded crates; consider adding it to the type list.

---

#### D3-006 — `code-style.md` states `missing_docs` is `deny` on public kernel crates; workspace Cargo.toml sets it to `warn`

**File:** `docs/standards/code-style.md:58`, `Cargo.toml:36`

**Description.**
`code-style.md:58` states: *"CI runs `#![deny(missing_docs)]` on public kernel crates."*
The workspace `Cargo.toml` at line 36 sets `missing_docs = "warn"`, not `"deny"`.
The kernel crate opts into `[lints] workspace = true` and has no per-crate override to `deny`.
`clippy::missing_safety_doc` is correctly `"deny"` in the workspace.
`missing_docs = "warn"` means undocumented public items produce warnings, not errors — CI does not fail on them.

**Suggested fix.**
Either: (a) change `Cargo.toml:36` from `"warn"` to `"deny"` to match the standard; or (b) update `code-style.md` to say `warn` and explain that the lint is informational until the public API surface stabilizes.
The standard should accurately describe the enforced level so reviewers know whether to reject undocumented public items.

---

#### D3-007 — `security-review.md:88` references `docs/architecture/security-model.md` as "Phase 3, does not yet exist" — it now exists

**File:** `docs/standards/security-review.md:88`

**Description.**
The checklist item reads: *"The change is reconciled with the documented threat model (once `docs/architecture/security-model.md` exists — Phase 3)."*
`docs/architecture/security-model.md` exists at HEAD (confirmed: `ls docs/architecture/` lists it, and it has substantial content including a full threat model section).
The checklist item is conditional on a file that has already been written.
Any reviewer following the checklist will treat this item as "not yet actionable" and skip it — even though the threat model is now available and should be consulted.

**Suggested fix.**
Remove the conditional and make the checklist item unconditional:
> - [ ] The change is reconciled with the documented threat model in [`docs/architecture/security-model.md`](../architecture/security-model.md).

---

#### D3-008 — `testing.md:105` says QEMU smoke tests "must pass" in CI; no QEMU-smoke CI job exists

**File:** `docs/standards/testing.md:105`

**Description.**
The CI gates section states: *"QEMU smoke tests — must pass on the primary target."*
No QEMU-smoke CI job exists in `.github/workflows/ci.yml`.
`infrastructure.md:71` is honest about this: it notes the job is "maintainer-launched only."
`testing.md` is not aligned — it presents the gate as an already-present CI requirement.
A contributor reading `testing.md` believes their PR will be blocked if a QEMU-smoke test fails, which is false.

**Suggested fix.**
Align `testing.md` with `infrastructure.md`'s honest parenthetical:
> QEMU smoke tests — run by the maintainer before merge; no CI job yet (tracked as B2-or-later follow-up per `infrastructure.md`).

---

### Minor

---

#### D3-009 — `logging-and-observability.md:68` Phase-3 label around a hal.md section reference; `security-review.md:88` is the Phase-3 pattern generally

**File:** `docs/standards/logging-and-observability.md:68`; also `infrastructure.md:63`, `infrastructure.md:142`

**Description.**
Several standards reference phase numbers (Phase 3, Phase 4, Phase 5) as future checkpoints.
At commit 288ddb2 the project is well into Phase B (B4 implementation half, T-019 task loader live on `main`), and Phases 1–4c are complete per the memory file.
`infrastructure.md:63` says *"CI is expected to be set up early in Phase 4 (Rust toolchain + workspace skeleton)"* — Phase 4 is complete; CI exists.
`infrastructure.md:142` says *"SBOM is generated per release (planned, Phase 5)"* — still fine as a future marker.
`logging-and-observability.md:68` says *"see architecture/hal.md, Phase 3"* — the section is a cross-link to `hal.md`, not a Phase-3-specific reference; the "(Phase 3)" parenthetical confuses rather than clarifies.
Phase-number labels that were meaningful when written become noise as phases complete.

**Suggested fix.**
In `infrastructure.md:63`, update the sentence: *"CI is expected to be set up early in Phase 4"* → *"CI was set up in Phase 4 (completed 2026-04-23); the gates below define the bar."*
In `logging-and-observability.md:68`, remove the dangling "(Phase 3)" cross-reference note; the link to `hal.md` is sufficient.
For Phase 5 references, add a note like *(planned — not yet implemented)* rather than relying on phase numbers alone.

---

#### D3-010 — `release.md:16` has a grammatical article error: "with an Tyrne-specific convention"

**File:** `docs/standards/release.md:16`

**Description.**
The sentence reads: *"Tyrne uses **semantic versioning** with an Tyrne-specific convention during the pre-1.0 period."*
"an Tyrne-specific" is a grammatical error — "Tyrne" begins with a consonant sound; the correct article is "a".
Should read: *"with a Tyrne-specific convention."*

**Suggested fix.**
Change "an Tyrne-specific" to "a Tyrne-specific".
(Trivial; included because the standard documents appear on any public repo landing page.)

---

#### D3-011 — `error-handling.md` states `clippy::result_large_err` and `clippy::missing_errors_doc` are "warn" — neither appears in Cargo.toml or kernel/src/lib.rs

**File:** `docs/standards/error-handling.md:169–170`

**Description.**
The Tooling section says:
- `clippy::result_large_err` is `warn` — error types larger than ~128 bytes bloat the `Result` return value.
- `clippy::missing_errors_doc` is `warn` — every public `fn -> Result` should document its errors.

Neither lint appears in `Cargo.toml` workspace lints, `clippy.toml`, or `kernel/src/lib.rs` `#![warn(...)]` / `#![deny(...)]` declarations (confirmed by `grep`).
The standard claims these lints are active; they are not.

**Suggested fix.**
Either add `result_large_err = "warn"` and `missing_errors_doc = "warn"` to the workspace lint set in `Cargo.toml`, or remove the "is warn" claim and rephrase as *"are recommended to be added when the API surface stabilizes."*

---

#### D3-012 — `code-style.md:97` references "ADR-0006 when written" — ADR-0006 exists and covers workspace layout, not the allocator

**File:** `docs/standards/code-style.md:97`

**Description.**
The `no_std` discipline section says: *"When the allocator is added (see ADR-0006 when written), it will be a distinct crate."*
ADR-0006 exists (`docs/decisions/0006-workspace-layout.md`) but it covers crate layout and workspace structure, not the allocator design.
The phrase "when written" is no longer accurate (ADR-0006 is Accepted), and the implied subject (an allocator ADR) does not match the actual ADR-0006 content.
There is no allocator ADR at all — no ADR in the 0001–0035 range covers the heap allocator decision.

**Suggested fix.**
Update the parenthetical: *"(see the allocator ADR, to be written when the allocator is introduced)"* — removing the stale ADR-0006 reference and making the forward reference honest.

---

#### D3-013 — `infrastructure.md:19` combined with CI reality creates a contributor confusion point re: toolchain

Covered in D3-004. Listed here separately because even if D3-004 is resolved by updating the standard to describe reality, a contributor's `rust-toolchain.toml` pins nightly but CI uses stable for the two fastest jobs — this should be explicitly explained in the standard so contributors understand why `cargo test` on their machine (nightly) may have subtly different behavior from CI (stable).

**File:** `docs/standards/infrastructure.md:17–19`

**Suggested fix.**
Add a note: *"Note: the fast-lane jobs (`lint-and-host-test`, `kernel-build`) use stable Rust to keep compilation fast and to validate stable compatibility. The pinned nightly is used for Miri and coverage. Contributors running `cargo test` locally will use the pinned nightly per `rust-toolchain.toml`."*

---

#### D3-014 — `bsp-boot-checklist.md:218` references `tools/run-qemu.sh --debug`; that flag does not exist in the script

**File:** `docs/standards/bsp-boot-checklist.md:218`

**Description.**
The diagnostic cheat sheet says: *"Add `--debug` to `tools/run-qemu.sh` or pass flags directly."*
`tools/run-qemu.sh` exists at HEAD.
Checking the script: there is no `--debug` argument processing — the script passes flags directly to `qemu-system-aarch64`.
A contributor following this instruction would get an error from the script, not from QEMU.

**Suggested fix.**
Replace the misleading instruction with the direct QEMU flag form that the cheat sheet already shows (the `qemu-system-aarch64 ... -d int -D /tmp/qemu_int.log` line below it), and remove the `--debug` reference, or add the `--debug` parsing to `run-qemu.sh`.

---

#### D3-015 — `code-style.md` mentions `clippy.toml` will hold the "full list" but the actual `clippy.toml` only has numeric thresholds (no lint levels)

**File:** `docs/standards/code-style.md:130`

**Description.**
The standard says: *"The full list is codified in `clippy.toml` once the workspace is created."*
The workspace exists and `clippy.toml` exists, but it contains only `avoid-breaking-exported-api = false` — numeric thresholds, no lint levels.
Lint levels are in `Cargo.toml` `[workspace.lints.clippy]` and in `kernel/src/lib.rs` `#![deny(...)]` attributes.
A contributor reading this sentence will look in `clippy.toml` for the authoritative lint list and find it empty of lint levels.

**Suggested fix.**
Update the sentence: *"Lint levels are configured in `Cargo.toml` `[workspace.lints.clippy]` and per-crate `#![deny(...)]` attributes in `lib.rs`. `clippy.toml` holds only numeric thresholds."*

---

#### D3-016 — `logging-and-observability.md` references `tyrne-log` crate as "planned"; no crate of that name exists in workspace; actual kernel uses no logging facade at all

**File:** `docs/standards/logging-and-observability.md:52`

**Description.**
The standard says: *"The project provides a logging facade (planned crate `tyrne-log`) with macros mirroring the `log` crate's shape."*
`Cargo.toml` workspace `members` lists: `kernel`, `hal`, `bsp-qemu-virt`, `test-hal` — no `tyrne-log`.
`grep log! info! warn! error! trace! debug!` across `kernel/src/` finds zero matches.
The kernel currently uses `Console::write_bytes` directly (serial output only, no structured logging).
The standard describes a fully designed logging architecture that does not exist yet.
This is acceptable for a forward-looking standard, but the prose does not clearly distinguish "this is planned and does not exist" from "this is how it works now."
In particular the anti-patterns section says *"never use `log::info!`, `tracing::info!`, or `std::println!` directly"* — which is already true (nobody uses them) but for the wrong reason (no logging at all, not because of the facade discipline).

**Suggested fix.**
Add an explicit status note at the top of `logging-and-observability.md`: *"**Status: forward-looking.** The `tyrne-log` crate and the log service architecture described here are not yet implemented. The kernel currently emits diagnostic output exclusively via the BSP console trait. This document records the intended design for when logging infrastructure lands."*

---

### Nit

---

#### D3-017 — `infrastructure.md:22` mentions `aarch64-unknown-none-softfloat` target but it does not appear in `rust-toolchain.toml` or CI

**File:** `docs/standards/infrastructure.md:22`

**Description.**
The toolchain section lists `aarch64-unknown-none-softfloat` as a cross-compile target installed "as needed."
`rust-toolchain.toml:targets` only lists `aarch64-unknown-none`.
CI installs only `aarch64-unknown-none` (`rustup target add aarch64-unknown-none`).
The softfloat target is not used anywhere in the current build; its inclusion creates a false impression of a multi-target setup.

**Suggested fix.**
Remove the softfloat line, or add a parenthetical: *(not currently used; retained as documentation of the alternative target available if FP-trap behavior changes).*

---

#### D3-018 — `release.md:113` references `docs/release-signing.md` which does not yet exist (without stating it does not exist)

**File:** `docs/standards/release.md:113`

**Description.**
The signing section says: *"The public key is published in `docs/release-signing.md` (to be added with the first release)."*
The phrase "to be added" is the honest forward-reference disclosure — this is a nit rather than a major finding.
However, the link syntax in the sentence does not use markdown linking, so a reader who tries to navigate to the file gets no helpful indication.

**Suggested fix.**
This is correctly marked "to be added." No change required beyond noting the status is accurate.
Optionally improve with: *"The public key will be published in `docs/release-signing.md` when the first release is cut."* (present tense → future tense for clarity).

---

#### D3-019 — `documentation-style.md:65` calls one-sentence-per-line a "useful convention" but does not apply it uniformly in the standards corpus itself

**File:** `docs/standards/documentation-style.md:65`

**Description.**
The standard says: *"A useful convention: one sentence per line in prose paragraphs."*
The word "convention" correctly avoids claiming it is a rule.
Several standards files do not follow it (e.g., `bsp-boot-checklist.md` has multi-sentence lines in its opening paragraph, `error-handling.md` has multi-sentence paragraphs in §Rules).
Since the standard explicitly calls it a "convention" (not "must"), this is a nit rather than a violation.

**Suggested fix.**
Either: (a) no change required — the standard is deliberately soft here; or (b) if the intent is to upgrade this to a rule, replace "A useful convention" with "Prose paragraphs must use one sentence per line."

---

#### D3-020 — `commit-style.md` does not mention `style` as an allowed type, but `style(sched)` commit exists on `main`

**File:** `docs/standards/commit-style.md:38`

**Description.**
The type list in `commit-style.md` does not include `style`.
Commit `style(sched): apply cargo fmt — ADR-0022 test-module reflow` is on `main`.
`style` is a standard Conventional Commits type used across the Rust ecosystem.
Its omission from the list creates a scenario where a perfectly reasonable commit type is technically non-compliant with the standard.

**Suggested fix.**
Add `style` — code style changes (non-behavioral, non-refactor) — to the type list in `commit-style.md`, positioned after `refactor`.

---

#### D3-021 — `unsafe-policy.md:78` uses Turkish text in the Mechanical-edit exemption example

**File:** `docs/standards/unsafe-policy.md:78`

**Description.**
The mechanical-edit exemption says: *"localisation passes (`Yüksek` → `High`)"* as an example.
`Yüksek` is a Turkish word, and it appears in a committed documentation file.
`architectural-principles.md:P9` and `localization.md:Rule 6` both state that committed artifacts are English; Turkish appears only in chat.
The Turkish word is used as a data example (demonstrating a past localisation sweep) rather than as prose, which puts it in a grey zone per `documentation-style.md:9` (*"show it as data, e.g. in a code block, and describe its meaning in English prose"*).
The example does not appear in a code block, however — it is inline prose.

**Suggested fix.**
Either wrap the example in a code span that signals it is data: `` `Yüksek` (Turkish: "High") → `High` `` or replace with a language-neutral example such as `("TyrneOS" → "Tyrne")`.

---

### Praise

---

#### D3-P01 — `bsp-boot-checklist.md` is an outstanding example of learned-lesson documentation

The checklist documents *why* each step matters with "what goes wrong if skipped" sections backed by real QEMU failure modes and ESR codes.
The diagnostic cheat sheet at the end is immediately actionable.
This is precisely the kind of institutional memory that saves hours on future BSP ports.

---

#### D3-P02 — `unsafe-policy.md` amendment discipline is sophisticated and well-designed

The append-only rule, the explicit Amendment format, the Mechanical-edit exemption, and the real canonical example (UNSAFE-2026-0011) show mature handling of an inherently tricky auditability problem.
The `unsafe-log.md` at HEAD actually follows the policy: 27 entries, all with the required fields, amendments attached correctly.

---

#### D3-P03 — `error-handling.md` Rule 6 ("return errors, do not log-and-return") is a rare and valuable kernel-specific rule

Most error-handling guides stop at "use Result."
Explicitly forbidding the log-and-return anti-pattern — and naming why (the caller controls logging policy) — is a non-obvious rule that prevents subtle observability bugs.
The bad/good code example reinforces the point clearly.

---

#### D3-P04 — `commit-style.md §PR-number references` is a well-codified recurring-failure lesson

Documenting the off-by-one and reopen/drift failure modes, with concrete recurrence examples from PR #18 and PR #20, and then providing three concrete mitigation strategies (defer, branch-slug, SHA) turns an annoying recurring mistake into a solved problem.
This is exactly how standards should capture operational experience.

---

## Claims register

The following table captures each standard's key claims, where to verify them against reality, and the current verification result (as of commit 288ddb2).

| Claim / rule | File:line | How to verify against reality | Verified? |
|---|---|---|---|
| "CI runs against the pinned toolchain only" | `infrastructure.md:19` | `grep "rustup default\|rustup update" .github/workflows/ci.yml` | **No** — `lint-and-host-test` and `kernel-build` use `stable` |
| "QEMU smoke — required gate for CI merge" | `infrastructure.md:71` | `cat .github/workflows/ci.yml` — look for qemu-smoke job | **No** — maintainer-launched only; no CI job |
| "cargo-audit — fails on known advisories (CI gate)" | `infrastructure.md:72` | `cat .github/workflows/ci.yml` | **No** — explicitly dormant |
| "cargo-vet check — CI gate" | `infrastructure.md:73` | `cat .github/workflows/ci.yml` | **No** — explicitly dormant |
| "Miri and coverage are still required for merge" | `ci.yml:6` (header) | `grep "continue-on-error" .github/workflows/ci.yml` | **No** — coverage has `continue-on-error: true` |
| "All CI gates green on commit being released (QEMU smoke, cargo-audit, cargo-vet)" | `release.md:61` | `cat .github/workflows/ci.yml` | **No** — those CI jobs do not exist |
| "`.claude/skills/add-dependency` skill" | `infrastructure.md:72,192` | `ls .agents/skills/add-dependency/` vs `ls .claude/skills/` | **No** — `.claude/skills/` deleted; path broken |
| "`#![deny(missing_docs)]` on public kernel crates" | `code-style.md:58` | `grep missing_docs Cargo.toml kernel/src/lib.rs` | **No** — workspace sets `warn`, not `deny` |
| "`clippy::result_large_err` is `warn`" | `error-handling.md:169` | `grep result_large_err Cargo.toml kernel/src/lib.rs` | **No** — lint not set anywhere |
| "`clippy::missing_errors_doc` is `warn`" | `error-handling.md:170` | same grep | **No** — lint not set anywhere |
| "Threat model: `docs/architecture/security-model.md` does not yet exist — Phase 3" | `security-review.md:88` | `ls docs/architecture/security-model.md` | **No** — file exists and has content |
| "QEMU smoke tests — must pass (CI gate)" | `testing.md:105` | `cat .github/workflows/ci.yml` | **No** — no CI job |
| "`tools/run-qemu.sh --debug`" | `bsp-boot-checklist.md:218` | inspect `tools/run-qemu.sh` for `--debug` flag | **No** — flag does not exist in script |
| "ADR-0006 when written — allocator" | `code-style.md:97` | `cat docs/decisions/0006-workspace-layout.md` | **No** — ADR-0006 exists but covers workspace layout, not allocator |
| "Conventional Commits format enforced on `main`" | `commit-style.md:11` | `git log --format="%s"` | **No** — multiple non-compliant commits on `main` |
| "Full lint list in `clippy.toml`" | `code-style.md:130` | `cat clippy.toml` | **No** — only numeric thresholds; lint levels are in `Cargo.toml` and per-crate |
| "Unsafe policy append-only enforced" | `unsafe-policy.md:63–76` | `cat docs/audits/unsafe-log.md` — check for in-place edits | **Yes** — audit log correctly amended, not rewritten |
| "Every `unsafe` block has `// SAFETY:` comment" | `unsafe-policy.md:§1` | `grep -rn "unsafe {" src/ + SAFETY: proximity check` | **Yes** — 183 SAFETY comments, 165 unsafe blocks (ratio >1 including fn/impl) |
| "Kernel lints: `clippy::panic`, `unwrap_used`, etc. are deny" | `code-style.md:128` | `grep deny.*clippy::panic kernel/src/lib.rs` | **Yes** — verified at lib.rs:47-51 |
| "English only in committed files" | `documentation-style.md:9`, `architectural-principles.md:P9` | `grep -rn Turkish/Turkish-words docs/standards/` | **Partial** — `unsafe-policy.md:78` has inline `Yüksek` (see D3-021) |
| "`rust-toolchain.toml` pins toolchain + components" | `infrastructure.md:17` | `cat rust-toolchain.toml` | **Yes** — nightly-2026-01-15, required components listed |
| "No `supply-chain/` directory at HEAD — wired in when first dep lands" | `infrastructure.md:192` | `ls supply-chain/` | **Yes** — directory does not exist (correctly acknowledged) |
| "Mermaid-only diagrams" | `architectural-principles.md:P10`, `documentation-style.md:§Diagrams` | `find docs/ -name "*.png" -o -name "*.svg"` | **Yes** — no binary image files found |
| "CHANGELOG.md to be created with first release" | `release.md:35` | `ls CHANGELOG.md` | **Yes** — accurately described as future; does not yet exist |
| "Tags are signed" | `release.md:91` | N/A (no releases yet; forward-looking) | **N/A** |

---

## Cross-track notes

1. **C9-build-infra** will likely independently find the CI toolchain discrepancy (D3-004) and the stale `.claude/skills/` paths (D3-001). If C9 finds additional details, D3-001 and D3-004 should be promoted to cross-track findings with the C9 reference.

2. **D2a-adr-early / D2b-adr-late**: The ADR-0006 mislabeling in `code-style.md:97` (D3-012) is a cross-cutting accuracy issue — the ADR reviewer tracks should note that ADR-0006's actual scope (workspace layout) is narrow enough that an allocator ADR has never been written, which is itself a potential gap if heap allocation is ever needed in the kernel.

3. **D5b-audits-reports** / **D5a-meta-core**: The `unsafe-policy.md` Mechanical-edit exemption at line 78 (D3-021) cites the 2026-05-07 PR #14 multi-axis review's Track-H. If the audit reviewer flagged this differently, the cross-reference should be reconciled.

4. **Gate-reproduction**: Several blocker findings here (D3-001 broken links, D3-002 continue-on-error lie, D3-003 missing CI gates) directly affect the gate-reproduction checklist's ability to accurately verify what "CI green" means for a release candidate. The gate-reproduction reviewer should note dependency on these findings.

5. **D1-architecture**: `security-review.md:88`'s stale "Phase 3 — security-model.md does not yet exist" note (D3-007) has a counterpart in D1's domain — the security model document now exists and its cross-references back into the standards should be checked by D1.

6. **D5c-existing-reviews**: The historical review snapshots under `docs/analysis/reviews/code-reviews/2026-05-0{6,7}*` intentionally retain `.claude/skills/...` links as point-in-time records (noted in `current.md`). Those stale links are *by design* in historical documents and are not findings there. The findings D3-001 applies specifically to `docs/standards/infrastructure.md` — a live, normative document.

---

## Coverage checklist

All 15 files were read in full. Line counts are from `wc -l docs/standards/*.md`.

| File | Lines | Read in full | Notes |
|---|---|---|---|
| [x] `docs/standards/README.md` | 48 | Yes | |
| [x] `docs/standards/architectural-principles.md` | 130 | Yes | |
| [x] `docs/standards/bsp-boot-checklist.md` | 224 | Yes | |
| [x] `docs/standards/code-review.md` | 135 | Yes | |
| [x] `docs/standards/code-style.md` | 154 | Yes | |
| [x] `docs/standards/commit-style.md` | 142 | Yes | |
| [x] `docs/standards/documentation-style.md` | 91 | Yes | |
| [x] `docs/standards/error-handling.md` | 176 | Yes | |
| [x] `docs/standards/infrastructure.md` | 210 | Yes | Stale .claude/skills/ paths; CI claims; toolchain divergence |
| [x] `docs/standards/localization.md` | 100 | Yes | |
| [x] `docs/standards/logging-and-observability.md` | 149 | Yes | tyrne-log crate is planned/non-existent |
| [x] `docs/standards/release.md` | 152 | Yes | Missing CI gates in process-gate list |
| [x] `docs/standards/security-review.md` | 135 | Yes | Stale Phase-3 conditional for security-model.md |
| [x] `docs/standards/testing.md` | 141 | Yes | QEMU smoke "must pass" claim vs. missing CI job |
| [x] `docs/standards/unsafe-policy.md` | 191 | Yes | Turkish inline example (nit) |
| **Total** | **2,178** | | |

Cross-checked against: `git ls-files docs/standards` (confirmed 15 files exactly matching the above list).
