# C9-build-infra — build, toolchain, CI, tooling (master review, commit 288ddb2)

## Summary

The build infrastructure is unusually well-documented and, for a pre-alpha kernel, mature: the workspace layout matches ADR-0006 exactly, the toolchain is pinned, lints are centralized in `[workspace.lints]`, `Cargo.lock` carries zero external dependencies (so the supply-chain attack surface is currently nil), and the two shell tools (`run-qemu.sh`, `perf-harness.sh`) are genuinely high-quality — `set -euo pipefail`, careful trap-based process cleanup, locale pinning, bash-3.2 portability, and SIGPIPE-aware parsing. The perf harness in particular is the strongest single artifact in this track.

However, the track's headline promise — **reproducibility and gate integrity** (P11) — is undermined by one real correctness defect and several config/docs drifts that all point the same direction: **what CI actually runs is not what its job names, its setup steps, and the guide claim it runs.**

The single most important finding is the **toolchain mismatch (C9-001)**: the `lint-and-host-test` and `kernel-build` jobs run `rustup default stable`, but a `rust-toolchain.toml` pinning `nightly-2026-01-15` sits at the repo root and **overrides `rustup default` for every in-repo `cargo` invocation**. Those two jobs therefore execute on the pinned nightly, not stable — contradicting their own names, their setup commands, and `docs/guides/ci.md`. This is not a cosmetic naming issue: it means the "stable builds clean" guarantee that the job names assert is *not actually tested anywhere*, and a contributor who follows `docs/guides/ci.md` ("run `rustup update stable`") can get a different lint/build result locally than CI produces.

Second tier: the global `RUSTFLAGS: -D warnings` env var in CI **silently discards** the `[target.aarch64-unknown-none] rustflags` from `.cargo/config.toml` (Cargo replaces, does not merge, when the env var is set), so the `kernel-build` CI job builds the kernel **without** `panic=abort` and `force-frame-pointers=yes` (C9-002). And the documented required-gate set in `infrastructure.md` / `release.md` lists `cargo-audit` + `cargo-vet` + QEMU smoke as merge gates, none of which exist in `ci.yml` — the gate-vs-docs delta is acknowledged in places but not fully reconciled (C9-005, C9-006).

Supply-chain hygiene of the CI itself is the other systematic gap: every third-party action is pinned by **mutable tag** (`@v4`, `@v2`) rather than by commit SHA, and there is no top-level `permissions:` block, so the default (often write-capable) `GITHUB_TOKEN` scope applies (C9-004) — directly at odds with `infrastructure.md`'s "Self-hosted runners running code from untrusted PRs" / supply-chain posture and P11's audit-from-the-toolchain-up framing.

No defect here is a kernel-correctness or security-of-the-shipped-artifact issue (the repo ships nothing yet), so nothing rises to Blocker against the *product*. But C9-001 is a Blocker against the *track's own stated purpose* (gate integrity / reproducibility) and is filed as such.

Severity counts: **Blocker 1, Major 5, Minor 7, Nit 5, Praise 6.**

---

## Findings

### Blocker

#### C9-001 — CI "stable" jobs actually run on the pinned nightly; the stable build is never tested
`.github/workflows/ci.yml:43-69` (lint-and-host-test), `:75-100` (kernel-build); `rust-toolchain.toml:11`

Both fast-lane jobs do:

```yaml
rustup update stable --no-self-update
rustup default stable
...
run: cargo fmt --all -- --check     # bare cargo, no +toolchain
run: cargo host-clippy
run: cargo host-test
run: cargo kernel-build
```

But `rust-toolchain.toml` at the repo root pins `channel = "nightly-2026-01-15"`. Rustup's override precedence is: a `rust-toolchain.toml` in the working directory (or any ancestor) **overrides `rustup default`** for any `cargo`/`rustc` invoked inside the repo. The `actions/checkout@v4` step (first in every job) places `rust-toolchain.toml` on disk before any `cargo` call runs. Therefore `cargo fmt`, `cargo host-clippy`, `cargo host-test`, `cargo kernel-build`, and `cargo kernel-clippy` all run under **nightly-2026-01-15**, not stable. The `rustup default stable` line installs a stable toolchain that is then never selected for the actual build steps.

Note the contrast with the `miri` and `coverage` jobs (`:114-115`, `:145-146`), which correctly use `rustup override set $NIGHTLY_PIN` and explicit `cargo +$NIGHTLY_PIN …`. Those two jobs are coherent; the stable jobs are not.

**Why this is a Blocker (against the track's purpose).** This track's mandate is reproducibility and gate integrity. Three concrete failures result:

1. **The job names lie.** `name: fmt + clippy + host tests` on a job titled internally "Fast lane: lint + host tests on stable" does not run on stable. `docs/guides/ci.md:9-12` documents these jobs as "stable + rustfmt + clippy" / "stable + aarch64". That is false.
2. **The "builds on stable" guarantee is untested.** A core implicit claim of having a stable-named job is "Tyrne's host-buildable crates compile and lint clean on stable Rust." Because the override silently redirects to nightly, *nothing in CI ever exercises stable*. If a contributor introduces an accidental nightly-only feature in a host crate, CI stays green; the breakage only surfaces for someone who manages to actually use stable.
3. **Local/CI divergence in the documented direction.** `docs/guides/ci.md:37` tells a contributor whose local result disagrees with CI to `rustup update stable` — which, in-repo, does nothing to change the toolchain cargo selects, so the advice cannot resolve the divergence it is offered for.

This also contradicts `infrastructure.md:19` ("CI runs against the pinned toolchain only") in a confusing way: the statement is *accidentally* true (everything runs on the pin), but the workflow is written as though it were false (it deliberately sets stable). The config and its intent are in direct conflict, which is exactly the "gate integrity" problem this track exists to catch.

**Suggested fix.** Decide the intent and make config + names + docs agree:
- **If the kernel genuinely requires nightly to build** (it does — `rust-toolchain.toml:4-6` and ADR-0002 §Negative both say inline asm / lang items need nightly): delete the `rustup default stable` dance from both jobs, install the pinned nightly the same way the miri/coverage jobs do (`rustup toolchain install $NIGHTLY_PIN …; rustup override set $NIGHTLY_PIN`), rename the jobs to drop "stable," and fix the `docs/guides/ci.md` toolchain column to read "pinned nightly." This is the truthful option and matches `infrastructure.md:19`.
- **If a stable-builds-clean signal is actually wanted**, add `cargo +stable …` explicitly to those steps (so the override is bypassed) — but given the kernel needs nightly, a stable `kernel-build` would not even compile, so this option only makes sense for a host-only subset and should be scoped accordingly.

Route to the contradiction pass as the canonical "CI toolchain ≠ documented toolchain" item, and to gate-reproduction to confirm the override-precedence behavior empirically on a runner.

---

### Major

#### C9-002 — Global `RUSTFLAGS: -D warnings` discards `.cargo/config.toml` per-target rustflags; kernel CI build loses `panic=abort` + frame pointers
`.github/workflows/ci.yml:30`; `.cargo/config.toml:14-21`

CI sets a process-wide `env: RUSTFLAGS: -D warnings`. Cargo's flag-resolution rule is that **if the `RUSTFLAGS` environment variable is set, it takes precedence over and replaces `build.rustflags` and `target.<triple>.rustflags` from config — they are not merged.** Consequently, in the `kernel-build` job, the `[target.aarch64-unknown-none] rustflags = ["-C","panic=abort","-C","force-frame-pointers=yes"]` block in `.cargo/config.toml:15-21` is **silently ignored**, and the kernel ELF is built only with `-D warnings`.

**Why.** Two distinct problems:
- **Reproducibility / fidelity (P11).** The artifact CI compiles is not the artifact a developer compiles locally (where `RUSTFLAGS` is unset and the config rustflags apply). `panic=abort` changes codegen materially — the unwinding tables, the panic path, and (for a `no_std` binary that defines its own `#[panic_handler]`) potentially link behavior. CI is supposed to be the reference build; here it builds a *different* binary than every local build. `force-frame-pointers=yes` (wanted for panic backtraces per `error-handling.md` and the config comment) is likewise dropped.
- **Latent build break.** A bare-metal `no_std`/`no_main` binary that relies on `panic=abort` to avoid pulling in an unwinder / `eh_personality` can fail to link without it. Today it apparently still builds (the panic handler in `bsp-qemu-virt/src/main.rs:1293` is `-> !`), but the project is one refactor away from CI and local diverging on link success. The config comment at `.cargo/config.toml:51-52` even says "panic=abort comes from .cargo/config.toml rustflags so it only applies to the bare-metal target" — an invariant the CI env var quietly breaks.

**Suggested fix.** Do not set `panic`/codegen-affecting flags via a global env var that clobbers config. Options, best first:
1. Drop the `RUSTFLAGS: -D warnings` env entirely and rely on the `-- -D warnings` already passed by the `host-clippy` / `kernel-clippy` aliases (`.cargo/config.toml:34,45`) plus, if a deny-warnings build is wanted, add it to `[target.'cfg(all())'] rustflags` / `build.rustflags` in config so it *merges* with the target block instead of replacing it.
2. Or, if the env var must stay, append the panic/frame-pointer flags into it for the kernel job, or move `-D warnings` into config so all flags live in one mergeable place.
Verify with gate-reproduction: `cargo kernel-build` with and without `RUSTFLAGS` set, diffing the resulting ELF for the presence of unwinding sections.

#### C9-003 — Third-party GitHub Actions pinned by mutable tag, not by commit SHA
`.github/workflows/ci.yml:47,54,79,87,111,117,142,158,162`

Every external action is referenced by a moving tag: `actions/checkout@v4`, `actions/cache@v4`, `taiki-e/install-action@v2`. Tags are mutable — a compromised or malicious maintainer (or a tag-repoint) changes what `@v4` resolves to without any change in this repo.

**Why.** This is the central supply-chain control for a CI pipeline, and it is the one most directly tied to this track's P11 mandate ("reproducibility from the toolchain up") and to `infrastructure.md`'s supply-chain section. The irony is sharp: the workflow goes to real lengths to pin `cargo-llvm-cov@0.6.16` and `NIGHTLY_PIN` (with a documented bump process in `docs/guides/ci.md:54-69`), explicitly *to stop upstream from silently changing what runs* — yet the actions that wrap those pinned tools are themselves unpinned. `taiki-e/install-action@v2` is especially load-bearing: it downloads and executes a prebuilt binary into the build, so a repoint of that tag is arbitrary code execution in CI. `infrastructure.md:202` lists "Self-hosted runners running code from untrusted PRs" as an anti-pattern; SHA-pinning third-party actions is the same class of control for hosted runners.

**Suggested fix.** Pin each action to a full 40-char commit SHA with the human-readable tag in a trailing comment, e.g. `uses: actions/checkout@<sha> # v4.2.2`. Add a short "Action pinning" subsection to `infrastructure.md` §Supply-chain (or §CI platform) codifying SHA-pinning + a Dependabot/`pinact` refresh path, mirroring the existing `cargo-llvm-cov` pin discipline. (Dependabot for GitHub Actions is already foreshadowed at `infrastructure.md:190` as planned — extend it to cover this.)

#### C9-004 — No `permissions:` block; jobs inherit the default `GITHUB_TOKEN` scope
`.github/workflows/ci.yml` (whole file — no `permissions:` key at workflow or job level)

The workflow declares no `permissions:`. Depending on the repository/org default, the auto-provisioned `GITHUB_TOKEN` may carry broad (including write) scopes. This pipeline only reads the repo and runs builds — it needs `contents: read` and nothing else.

**Why.** Least-privilege for the CI token is a baseline supply-chain hardening step and squarely within this track's security dimension. If any action in the graph is compromised (see C9-003), an over-scoped token is the difference between a failed build and a pushed commit / published artifact / leaked token. `infrastructure.md:86` ("Secrets never enter CI") and §Secrets management set the posture; an explicit minimal `permissions:` block operationalizes it.

**Suggested fix.** Add at the top level:

```yaml
permissions:
  contents: read
```

and override per-job only where a future job genuinely needs more (none do today). Document the choice in `infrastructure.md` §CI platform.

#### C9-005 — Documented required-gate set diverges from the actual CI jobs (audit / vet / QEMU-smoke listed as gates that do not exist)
`docs/standards/infrastructure.md:65-73`, `docs/standards/release.md:61`; `.github/workflows/ci.yml` (jobs present: lint-and-host-test, kernel-build, miri, coverage)

`infrastructure.md` §"Required gates (block merge)" lists six gates including `cargo audit`, `cargo vet check`, and a QEMU smoke gate. `release.md:61` repeats "All CI gates green … (format, clippy, tests, build, QEMU smoke, cargo-audit, cargo-vet)" as a process gate. The actual workflow has **no** audit, vet, or qemu-smoke job. The doc *does* annotate audit/vet as "Conditional — currently dormant" (`infrastructure.md:72-73`) and qemu-smoke as "maintainer-launched only … no `qemu-smoke` CI job yet" (`:71`), so the drift is partially disclosed — but `release.md:61` presents the same set as a hard release gate with no such caveat, and the `clippy` line at `infrastructure.md:68` names `cargo clippy --workspace --all-targets` which is not literally what any job runs (CI runs the `host-clippy`/`kernel-clippy` aliases; see C9-008).

**Why.** A reader cross-checking "what blocks merge" against `infrastructure.md` will believe audit/vet/smoke are enforced. They are not. For a security-first project this is exactly the kind of gate-integrity gap the master review must surface: the *documented* assurance exceeds the *enforced* assurance. The dormancy rationale (zero external deps ⇒ audit/vet are no-ops) is sound for *audit/vet*, but it should be stated once, consistently, in both `infrastructure.md` and `release.md`, and the QEMU-smoke gap (a behavioral gate, not a no-op) deserves its own tracked follow-up rather than a parenthetical.

**Suggested fix.** Reconcile the two docs: mark audit/vet/smoke explicitly as "planned, not yet enforced" in `release.md`'s gate list too (it currently reads as enforced); and either (a) add the qemu-smoke job (the `docs/guides/ci.md:39-41` "T-009 follow-up" already scopes it) or (b) demote it from "Required gates" to a clearly-labeled "Planned gates" subsection so the Required list reflects reality. Route the precise wording delta to the contradiction pass.

#### C9-006 — Coverage job is labeled "still required for merge" in the header but is `continue-on-error: true` and is documented as *not* a required check
`.github/workflows/ci.yml:5-7` vs `:137-141`; `docs/guides/ci.md:73-77`

The workflow header comment (`:5-7`) says of the Miri and coverage jobs: "they are still **required for merge** into `main`." But the `coverage` job sets `continue-on-error: true` (`:140`) and is described everywhere else (its own section comment `:132-136`, `docs/guides/ci.md:12,73-77`) as **informational, never gating**. `docs/guides/ci.md:75` even explicitly warns *not* to add `coverage` to required checks while it is `continue-on-error`.

**Why.** The file contradicts itself about whether coverage gates merges. Whoever configures branch protection from the header comment would wrongly add coverage to required checks — the precise mistake `docs/guides/ci.md:75` documents as breaking every push (a neutral result never satisfies `required == passing`). This is an internal contradiction in the single most authoritative file for the gate set.

**Suggested fix.** Fix the header comment at `:5-7` to say only **Miri** is required-but-slow; coverage is informational until the post-T-011 flip. Keep the per-job comments (`:132-136`) as the source of truth.

---

### Minor

#### C9-007 — Doc references to the dependency-onboarding skill point at a path that no longer exists (`.claude/skills/…`)
`docs/standards/infrastructure.md:72,192` (also the brief's own lens text)

`infrastructure.md` links the add-dependency procedure as `../../.claude/skills/add-dependency/SKILL.md` in two places. Per `CLAUDE.md` and project memory, skills migrated to `.agents/skills/<slug>/SKILL.md` on 2026-05-14; the skill now lives at `.agents/skills/add-dependency/SKILL.md` and `.claude/skills/` no longer exists (confirmed: `find` shows only `.agents/skills/add-dependency`). Both links are dead.

**Why.** `infrastructure.md` is *this track's* governing standard; broken self-references in it directly degrade the dependency-onboarding gate's discoverability (the very gate C9-005 is about). It is also a `code-review.md:23` "post-fix sweep" miss — a rename that did not `grep -F` for stale references.

**Suggested fix.** Update both links to `../../.agents/skills/add-dependency/SKILL.md`. Run `rg -F '.claude/skills'` across `docs/` to catch siblings (see C9-009).

#### C9-008 — `host-clippy` alias is `--all-targets` (no `--workspace`); `infrastructure.md` documents the gate as `--workspace --all-targets`
`.cargo/config.toml:45`; `docs/standards/infrastructure.md:68`, `docs/standards/code-style.md:137`

The required-gate text says `cargo clippy --workspace --all-targets -- -D warnings`. The actual alias CI runs is `clippy --all-targets -- -D warnings` — no `--workspace`, so it lints the **default-members** set (kernel, hal, test-hal) rather than the full workspace. Today `default-members` == the host-buildable crates, and the BSP is separately linted by `kernel-clippy`, so coverage is *behaviorally* complete — but the alias does not match the documented command, and the equivalence is incidental (it breaks the moment a host-buildable crate is added to `members` but not `default-members`).

**Why.** Drift between the documented gate command and the executed gate command is a gate-integrity smell even when currently harmless. A future maintainer reading `infrastructure.md:68` and grepping for `--workspace` in CI will not find it and may "fix" CI to add it, subtly changing scope.

**Suggested fix.** Either make the alias `clippy --workspace --all-targets -- -D warnings` (matching the doc; default-members is then irrelevant for clippy) or update `infrastructure.md:68` / `code-style.md:137` to describe the actual two-alias split (`host-clippy` for default-members + `kernel-clippy` for the BSP target). Prefer the former for the least surprise.

#### C9-009 — `.gitignore` comment still describes the tracked-skills tree as `.claude/skills/`
`.gitignore:44-46`

The comment reads: "The .claude/skills/ tree itself IS tracked (project skills are source of truth); only runtime lock files are ignored." After the 2026-05-14 migration, the tracked tree is `.agents/skills/`. The ignore rule itself (`.claude/*.lock`) is still fine, but the explanatory comment names the wrong directory.

**Why.** Stale comment in a config file in this track; same migration sweep miss as C9-007. Minor because the *rule* still works; only the prose is wrong.

**Suggested fix.** Update the comment to reference `.agents/skills/` (and confirm whether any `.claude/*.lock` files are still produced; if Claude Code now writes lock state elsewhere, the rule may itself be obsolete).

#### C9-010 — `run-qemu.sh` silently treats any unrecognized argument (including typo'd flags) as the kernel path
`tools/run-qemu.sh:23-39`

The arg loop's `*)` arm assigns `KERNEL="$arg"`, so `--relese` (typo), `--help`, or a second positional all become the ELF path, and the script then fails later with "kernel image not found at --relese." There is no `--help`, and no rejection of unknown `--flags`.

**Why.** Usability + footgun. `perf-harness.sh` (the sibling tool) does this correctly — it has `-h|--help` and an explicit `*) echo "unknown argument" … usage` arm (`tools/perf-harness.sh:126-133`). `run-qemu.sh` is the more frequently-run tool and the rougher one. A typo'd flag produces a confusing "not found" error pointing at the flag string as if it were a path.

**Suggested fix.** Split the `*)` arm: reject `--*` as "unknown flag" with a usage hint and `exit 2`, treat the first bare token as `KERNEL` and a second bare token as an error. Add a `-h|--help` arm printing the usage header (the file already has a good usage comment block to echo, mirroring `perf-harness.sh:103-106`).

#### C9-011 — `--int-log` writes a fixed `/tmp/qemu_int.log`; concurrent runs collide and it is world-readable
`tools/run-qemu.sh:54-58`, `:67`

The interrupt log path is hard-coded to `/tmp/qemu_int.log`. Two concurrent `run-qemu.sh --int-log` invocations (or two users on a shared host) overwrite each other's logs, and `/tmp` is world-readable.

**Why.** Minor robustness/usability: the perf harness deliberately runs `run-qemu.sh` in a loop and could (in a future `--int-log` mode) trample the file; on a shared dev box the fixed path is a small information-leak and a collision. Low severity because it is a debug-only opt-in flag.

**Suggested fix.** Default to `${TMPDIR:-/tmp}/qemu_int.$$.log` (PID-suffixed) or accept an optional path argument; echo the actual path (already done at `:57`).

#### C9-012 — `perf-harness.sh` 50% threshold uses `(ITERATIONS+1)/2` while the help/doc says "fewer than 50%"
`tools/perf-harness.sh:322-329` vs `:35-36`, `docs/standards/infrastructure.md:109`

`HALF=$(( (ITERATIONS + 1) / 2 ))` and the abort condition is `VALID_COUNT < HALF`. For `ITERATIONS=20`, `HALF=10`, so 10 valid passes (`10 < 10` false). For odd counts, e.g. `ITERATIONS=3`, `HALF=2`, so 1 valid (33%) aborts but 2 valid (67%) passes — fine. The behavior is reasonable, but "fewer than 50%" in the prose (`:35`, `infrastructure.md:109`) does not precisely describe `(n+1)/2` rounding for odd `n` (e.g. n=5 ⇒ HALF=3 ⇒ requires ≥3/5 = 60%, not 50%).

**Why.** Minor doc/impl precision gap in a tool whose whole job is to produce defensible numbers. Not wrong, just imprecise; an analyst computing the exact threshold from the docs would be off for odd `n`.

**Suggested fix.** Either state "at least ⌈n/2⌉ valid runs (rounding up)" in the comment + `infrastructure.md`, or change to `HALF=$(( ITERATIONS / 2 ))` with `VALID_COUNT < HALF` if a true floor-50% is intended. Cosmetic; pick one and make doc + code agree.

#### C9-013 — `coverage` job omits `~/.cargo/bin` from its cache `path:` while every other job includes it
`.github/workflows/ci.yml:164-167` vs `:56-60`, `:89-93`, `:119-123`

The lint, kernel-build, and miri jobs cache `~/.cargo/bin` (among others); the coverage job's cache `path:` lists only `~/.cargo/registry`, `~/.cargo/git`, `target`. Since `cargo-llvm-cov` is installed via `taiki-e/install-action` (not `cargo install` into `~/.cargo/bin`), omitting `~/.cargo/bin` is arguably *correct* for this job — but the inconsistency is undocumented and reads as an oversight.

**Why.** Minor maintainability: a reader cannot tell whether the omission is intentional (it is defensible) or a copy-paste slip. Cache key inconsistency also means the coverage cache can never share with sibling jobs even when it safely could.

**Suggested fix.** Add a one-line comment on the coverage cache block explaining `~/.cargo/bin` is intentionally excluded because the tool is installed by `taiki-e/install-action`, not `cargo install`. (Do not add the path — that would cache nothing useful.)

---

### Nit

#### C9-014 — CI header comment cites a stale host-test count ("111")
`.github/workflows/ci.yml:10-12`
The comment freezes "the local host-test count was 111" as of 2026-04-23 and instructs updating the matrix when crates/targets change, but the count is not used by any job and inevitably rots. (It is already plausibly stale.) Suggest dropping the literal number or replacing it with "see `cargo host-test` output" — a frozen count in a comment is guaranteed drift with no enforcement.

#### C9-015 — `aarch64-unknown-none-softfloat` documented as a target but absent from `rust-toolchain.toml`/CI
`docs/standards/infrastructure.md:22` vs `rust-toolchain.toml:18-20`
The toolchain `targets` array lists only `aarch64-unknown-none`. The softfloat variant is "variants where needed" per the doc, so its absence is fine today — but worth a half-sentence in `rust-toolchain.toml` noting softfloat is added on demand, to preempt a "the standard lists it, why isn't it pinned?" question.

#### C9-016 — `.cargo/config.toml` runner duplicates the QEMU invocation also hard-coded in `run-qemu.sh`
`.cargo/config.toml:25` and `tools/run-qemu.sh:60-68`
The `-M virt -cpu cortex-a72 -m 128M -smp 1 -nographic -serial mon:stdio` string exists verbatim in two places (and a third, `docs/guides/run-under-qemu.md:72-79`). They currently match (confirmed), but three copies drift independently. Not easily DRY-able across a TOML runner and a shell script, so this is a documented-risk nit; a comment in each cross-referencing the others (run-qemu.sh already has none pointing at config.toml) would help. The prior Track-H review (2026-05-06) already verified the match — keep that verification habit.

#### C9-017 — `[profile.release]` sets `overflow-checks = true`, which is unusual and worth a one-line rationale
`Cargo.toml:58`
Enabling overflow checks in release is a deliberate security-over-speed choice (consistent with `code-style.md:126` `arithmetic_side_effects` deny) and a good one for a security-first kernel — but it is surprising enough that the next reader may "optimize" it away. The dev-profile block has it too (`:64`). A one-line comment ("overflow checks kept on in release: a silent wrap in the kernel is a security bug, not a perf win") would lock in the intent. (Filed as Praise too — see C9-P5 — but the missing rationale is the nit.)

#### C9-018 — `Cargo.lock` `version = 4` requires a relatively recent Cargo; no floor documented
`Cargo.lock:3`
The lockfile is format v4 (Cargo 1.78+/recent). Given the toolchain is a pinned nightly this is fine, but nothing records the minimum Cargo that can read the lock. Trivial; mention in `infrastructure.md` §Toolchain only if external contributors with older cargo become a concern.

#### C9-019 — `perf-harness.sh` report path collision is silent (overwrites an existing same-context report)
`tools/perf-harness.sh:455-579`
If two runs use the same `--report=CONTEXT` on the same UTC day, the second silently overwrites the first. `infrastructure.md:115` says baseline reports are "append-only artefacts"; the script does not enforce that (no `-e "$REPORT_PATH"` guard). Low impact (operator-chosen slug), but a `[[ -e "$REPORT_PATH" ]] && { echo "refusing to overwrite"; exit 1; }` guard would make the append-only discipline real rather than conventional.

---

### Praise

#### C9-P1 — `perf-harness.sh` process-cleanup design is genuinely excellent
`tools/perf-harness.sh:51-90`, `:205-244`
The three-trap (EXIT/INT/TERM) model with idempotent `cleanup_in_flight`, the shell-global PID tracking so the trap can reap whichever watchdog/QEMU pair is in flight, the `kill -0` liveness probe before escalation, and the GNU-timeout-matching TERM-then-KILL escalation are all correct and rare to see done right in hand-rolled bash. The inline comments explaining *why* (not what) are exemplary.

#### C9-P2 — Locale and SIGPIPE hardening in `perf-harness.sh`
`tools/perf-harness.sh:41-49` (`export LC_ALL=C` with the tr_TR decimal-comma rationale), `:251-254` (awk `NR==1 … exit` instead of `head -n1` to avoid SIGPIPE under `pipefail`)
Both are subtle, real-world bugs the author anticipated and defused, with comments that teach the reader the failure mode. The LC_ALL fix is directly relevant to this Turkish-locale maintainer.

#### C9-P3 — Centralized `[workspace.lints]` with per-lint rationale and provenance
`Cargo.toml:34-49`
`unsafe_op_in_unsafe_fn = deny`, `undocumented_unsafe_blocks = deny`, `missing_safety_doc = deny`, `todo = deny` (with a comment tracing the kernel-local→workspace promotion to a dated closure-trio) is exactly the lint posture a high-assurance kernel wants, applied uniformly via `[lints] workspace = true` in each member manifest. Matches `code-style.md` and `unsafe-policy.md`.

#### C9-P4 — Pinning discipline for the slow-job toolchain and tools is well-engineered
`.github/workflows/ci.yml:31-37` (NIGHTLY_PIN with bump-process comment), `:147-160` (cargo-llvm-cov pinned to an exact version via prebuilt-binary action, with a clear two-win rationale), and the documented bump procedure in `docs/guides/ci.md:54-69`
The reasoning ("rolling nightly means an upstream regression breaks us with no commit of ours as the cause") is precisely the right justification, and the issue-driven bump process is a model the action-SHA gap (C9-003) should be brought up to.

#### C9-P5 — `overflow-checks = true` in release; `panic=abort` scoped to the bare-metal target only
`Cargo.toml:58`, `.cargo/config.toml:14-21`
Keeping overflow checks on in release trades a little speed for catching silent wraps — the correct call for a kernel. Scoping `panic=abort` to `[target.aarch64-unknown-none]` (so host tests still unwind and report failures normally) is the right separation, well-commented at `.cargo/config.toml:11-13`. (The CI env var undermines it — see C9-002 — but the *config design* is correct.)

#### C9-P6 — Zero external dependencies, and the policy to keep it deliberate
`Cargo.lock` (only the four path crates, no `source`/`checksum` lines), `infrastructure.md:27-59`
For a pre-alpha kernel to have *no* third-party crates in the graph is a strong supply-chain position (it is why audit/vet can be dormant), and the dependency-addition policy (`infrastructure.md` §Dependency policy, trust categories, `cargo-vet` gating on first external dep) is thorough and ready for the moment that changes.

---

## Claims register

| Claim | Source `file:line` | How to verify |
|---|---|---|
| Nightly pinned to `2026-01-15` in toolchain file | `rust-toolchain.toml:11` | Read; `rg channel rust-toolchain.toml` → `nightly-2026-01-15`. **Verified.** |
| Same nightly pinned in CI env | `.github/workflows/ci.yml:37` | `rg NIGHTLY_PIN: .github/workflows/ci.yml` → `nightly-2026-01-15`. **Verified consistent with toolchain file.** |
| CI fast-lane jobs run on **stable** | `.github/workflows/ci.yml:51,83`; `docs/guides/ci.md:9-10` | **FALSE in effect.** `rust-toolchain.toml` override redirects bare `cargo` to nightly; the `rustup default stable` is shadowed for in-repo cargo. Confirm on a runner: `rustup show active-toolchain` from the repo dir after the setup step. (C9-001) |
| CI runs miri as a required gate | `ci.yml:5-7,107-130`; `docs/guides/ci.md:11,76` | Miri job exists, no `continue-on-error`, runs `cargo +$NIGHTLY_PIN miri test --workspace --exclude tyrne-bsp-qemu-virt`. **Required-status enforcement is branch-protection config, not in-repo — unverifiable from the tree; the job itself is correctly gating.** |
| Coverage is informational / never blocks | `ci.yml:137-141`; `docs/guides/ci.md:12,73-77` | `continue-on-error: true` present. **Verified** — but header comment `ci.yml:5-7` contradicts it (C9-006). |
| Required gates include `cargo audit` / `cargo vet` / QEMU smoke | `infrastructure.md:65-73`; `release.md:61` | **No such jobs in `ci.yml`.** Audit/vet annotated "dormant" (zero deps); smoke annotated "no CI job yet." `release.md` lists them ungated. (C9-005) |
| `Cargo.lock` carries zero external dependencies | `infrastructure.md:72`; `Cargo.lock` | `rg "source|checksum" Cargo.lock` → no matches; only 4 path crates. **Verified.** |
| Kernel panic strategy is `panic=abort`, scoped to bare metal | `.cargo/config.toml:18`; `error-handling.md:143`; `Cargo.toml:51-52` | `rg panic .cargo/config.toml`. **Verified in config**; but CI's `RUSTFLAGS` env discards it for the kernel-build job (C9-002) — verify by building with/without `RUSTFLAGS` and inspecting unwinding sections. |
| Frame pointers forced on for the kernel | `.cargo/config.toml:20` | Read. **Verified in config; same RUSTFLAGS-clobber caveat (C9-002).** |
| `panic=abort` NOT applied to host tests | `.cargo/config.toml:11-13` | Flags live under `[target.aarch64-unknown-none]` only; host triple unaffected. **Verified.** |
| Cargo aliases (`kernel-build`, `kernel-clippy`, `kernel-run`, `host-test`, `host-clippy`) work as documented | `.cargo/config.toml:28-45`; `docs/guides/run-under-qemu.md`; `docs/guides/ci.md:27-35` | Alias defs match the documented commands. `host-clippy` lacks `--workspace` vs the doc gate text (C9-008). Functional verification needs a build (not run here, no-build constraint). |
| QEMU runner string in config == `run-qemu.sh` invocation | `.cargo/config.toml:25`; `tools/run-qemu.sh:60-68` | String compare of the two `qemu-system-aarch64 …` invocations — match (also re-confirmed against `run-under-qemu.md:72-79`). **Verified.** |
| Workspace lints applied to every crate | `Cargo.toml:34-49`; `kernel/Cargo.toml:19-20`; `hal/Cargo.toml:13-14` | Each member manifest has `[lints] workspace = true`. **Verified for kernel + hal (this track's manifests); bsp/test-hal owned by their tracks.** |
| Workspace members == ADR-0006 four-crate set | `Cargo.toml:8-13`; `ADR-0006:43-48` | kernel, hal, bsp-qemu-virt, test-hal. **Verified, matches ADR exactly.** |
| `default-members` excludes the bare-metal BSP | `Cargo.toml:18-22` | kernel/hal/test-hal only. **Verified** — rationale (BSP needs explicit target) sound. |
| Skills onboarding doc path `.claude/skills/add-dependency` | `infrastructure.md:72,192` | **Dead path.** Skill is at `.agents/skills/add-dependency/` (per `CLAUDE.md` + memory; `find` confirms). (C9-007) |
| `.gitignore` tracked-skills comment names `.claude/skills/` | `.gitignore:44-46` | **Stale comment** post-2026-05-14 migration. (C9-009) |
| Shell scripts use `set -euo pipefail` | `tools/run-qemu.sh:17`; `tools/perf-harness.sh:41` | Read both. **Verified.** |
| Scripts are executable in git | `tools/*.sh` | `git ls-files -s` → mode `100755` for both. **Verified.** |
| Perf harness is the canonical boot-to-end source | `infrastructure.md:94-96`; `perf-harness.sh:1-10` | Doc + script header agree; harness parses `boot-to-end elapsed = X ns`. **Verified (claim-consistent; runtime behavior not executed here).** |
| Third-party actions pinned by SHA | `ci.yml:47,54,79,87,111,117,142,158,162` | All `@v4`/`@v2` tags, no SHAs. **FALSE.** (C9-003) |
| CI declares least-privilege `permissions:` | `ci.yml` (whole) | No `permissions:` key anywhere. **FALSE.** (C9-004) |
| No release tags / CHANGELOG yet (pre-alpha) | `release.md:3,35`; repo | `git tag -l` empty; `CHANGELOG.md` absent. **Verified consistent with release.md "to be created with the first release."** |

---

## Cross-track notes

- **CI-gate-vs-docs drift → contradiction pass.** Three items belong to the contradiction reviewer with concrete file:line pairs: (1) C9-001 — `ci.yml` "stable" jobs vs `rust-toolchain.toml` nightly pin vs `docs/guides/ci.md:9-10` "stable" vs `infrastructure.md:19` "pinned toolchain only"; (2) C9-005 — `infrastructure.md:65-73` / `release.md:61` required-gate list vs the four jobs that actually exist; (3) C9-006 — `ci.yml:5-7` "coverage required for merge" vs `ci.yml:140` `continue-on-error` vs `ci.md:73-77`.
- **Gate-reproduction coordination.** Two empirical checks need a runner/build (out of scope for this read-only track): (a) confirm `rust-toolchain.toml` override actually selects nightly in the `lint-and-host-test`/`kernel-build` jobs despite `rustup default stable` (C9-001) — `rustup show active-toolchain` from the repo dir is the one-liner; (b) confirm the global `RUSTFLAGS` env clobbers `target.*.rustflags` so the kernel-build CI artifact lacks `panic=abort`/frame-pointers (C9-002) — build with and without `RUSTFLAGS` set and diff the ELF's unwinding sections / `readelf -S`.
- **C5 (commit-style/process) and the post-fix-sweep anti-pattern.** C9-007 and C9-009 are both instances of the `code-review.md:23` "fix produces stale documentation" failure (a skills-dir rename that did not `grep -F` for references). If a track is auditing process discipline, the `.claude/skills/` → `.agents/skills/` migration left at least three stale references (the two doc links + the gitignore comment); a repo-wide `rg -F '.claude/skills'` is the cheap closeout.
- **BSP/test-hal manifests** were deliberately left to their crate tracks per the brief; the only cross-edge I relied on is that `bsp-qemu-virt` is `no_main` and is excluded from default-members/miri/coverage — consistent with ADR-0006:47 and `docs/guides/ci.md:39-41`. The kernel `#[panic_handler]` lives in the BSP (`bsp-qemu-virt/src/main.rs:1293`), which is why C9-002's "missing panic=abort" is a latent-link risk rather than a present failure — flag for the BSP track to confirm the binary still links without `panic=abort`.
- **P7 (no proprietary blobs).** No blobs, vendored binaries, or closed-source toolchain inputs anywhere in this track — clean. `Cargo.lock` has zero external sources; CI installs only rustup-distributed toolchains + one pinned open-source tool (`cargo-llvm-cov`). Nothing to route.

---

## Coverage checklist

All 12 track files read in full:

- [x] `Cargo.toml` (workspace root) — 64 lines
- [x] `Cargo.lock` — 30 lines
- [x] `kernel/Cargo.toml` — 20 lines
- [x] `hal/Cargo.toml` — 14 lines
- [x] `.cargo/config.toml` — 45 lines
- [x] `rust-toolchain.toml` — 21 lines
- [x] `rustfmt.toml` — 15 lines
- [x] `clippy.toml` — 14 lines
- [x] `.github/workflows/ci.yml` — 172 lines
- [x] `tools/run-qemu.sh` — 68 lines
- [x] `tools/perf-harness.sh` — 585 lines
- [x] `.gitignore` — 63 lines

Related context read (read-only): `docs/standards/infrastructure.md`, `docs/guides/ci.md`, `docs/guides/run-under-qemu.md`, `docs/standards/release.md`, `docs/standards/code-review.md`, `docs/standards/architectural-principles.md`, `docs/standards/commit-style.md`, `docs/standards/code-style.md` (grep), `docs/standards/error-handling.md` (grep), `docs/decisions/0006-workspace-layout.md`, `docs/decisions/0002-implementation-language-rust.md`. (Brief cited "ADR-0011 panic policy"; ADR-0011 is actually the IRQ-controller trait — the panic strategy lives in `docs/standards/error-handling.md §Panic strategy`, which was read instead.) Verifications via `rg` and read-only `git log`/`git ls-files`/`find`; no mutating or build commands run.
