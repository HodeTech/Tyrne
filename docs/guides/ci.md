# CI: what runs, where, and when

This guide describes the GitHub Actions pipeline configured in [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml). It is the first external gate beyond self-review and agent-review. A failing required CI check blocks actors subject to the current branch protection even if local checks passed. The existing solo-phase policy permits administrator bypass and requires no positive approval count; maintainer review remains part of the merge process. Informational reports are excluded from required checks.

## Jobs

| Job | Toolchain | Wall time (expected) | Fails on |
|-----|-----------|----------------------|----------|
| `lint-and-host-test` | pinned nightly + `rustfmt` + `clippy` | ~2 min | `cargo fmt --check` diff, clippy warning, debug/release host test failure, absent release-only syscall tests, tooling ShellCheck finding, expected-failure probe mismatch, stubbed QEMU argument regression, or smoke/protection/performance/ARM fixture failure |
| `kernel-build` | pinned nightly + `aarch64-unknown-none` + `clippy` | ~1 min | Debug/release kernel or debug perf-bench build error, kernel/userland/perf-bench clippy warning or expected-failure probe mismatch |
| `qemu-smoke` | pinned nightly + `llvm-tools-preview` + QEMU | ~2–4 min; 10 min bound | Missing debug/release EL0 markers, release greeting, panic/CPU-fault trace, build failure or expected-failure probe mismatch |
| `arm64-host-check` | pinned nightly + `clippy` + `miri`, `ubuntu-24.04-arm` | 101 s first hosted run; 15 min bound | Native workspace check/clippy/test/Miri failure, wrong host or arch-only regression probe mismatch |
| `host-stable-check` | stable (no extra components) | ~2 min | host crates failing to build or test on stable Rust |
| `miri` | pinned nightly + `miri` component | ~1–2 min observed; historically budgeted ~10–15 min | Any Stacked Borrows violation in `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` |
| `coverage` | pinned nightly + `llvm-tools-preview` + `cargo-llvm-cov` | ~3–5 min | Coverage/tool errors are informational; excluded from required policy |
| `performance-report` (separate workflow) | pinned nightly + LLVM + QEMU | 20 × 5 s watchdogs plus setup; 10 min bound | Visible workflow failure on measurement/build/upload error; no timing threshold and no merge gate |

The ARM job runs on `ubuntu-24.04-arm`; the remaining jobs use `ubuntu-latest` (x86_64). Every exact cache key includes OS, architecture, toolchain and lockfile hash. Restore prefixes retain OS, architecture and toolchain while allowing a different lockfile hash, so ARM cannot restore x86_64 build artifacts. Executable `~/.cargo/bin` paths are excluded; registry and build caches remain inputs executed by the build, not integrity-attested code. [GitHub cache scope](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching) isolates ordinary PR merge-ref caches from base branches and sibling PRs; reruns of the same PR can restore them. Cache scope does not grant a workflow additional trust or make caches suitable for secrets.

### Why do the kernel jobs run on the pinned nightly, not stable?

The kernel needs nightly to build (inline asm intrinsics / lang items — see `rust-toolchain.toml` and ADR-0002). `rust-toolchain.toml` pins `nightly-2026-01-15` at the repo root, and rustup's override precedence means that file selects the pinned nightly for **every** in-repo `cargo` invocation regardless of `rustup default`. So `lint-and-host-test`, `kernel-build`, `qemu-smoke`, `arm64-host-check`, `miri`, and `coverage` all select the pin explicitly (`cargo +$NIGHTLY_PIN …`) — the same toolchain a contributor's local `cargo` uses.

### What does `host-stable-check` give us, then?

A genuine "the host-buildable crates compile and pass tests on **stable** Rust" signal. It runs `cargo +stable build` and `cargo +stable host-test` over the workspace `default-members` (kernel, hal, test-hal) — the bare-metal BSP is excluded because it needs nightly. The `+stable` prefix bypasses the `rust-toolchain.toml` override so this job exercises stable for real. It deliberately does **not** run clippy/fmt with `-D warnings`: `clippy::pedantic` is `warn` workspace-wide and stable is a rolling toolchain, so a future stable pedantic lint could redden the gate with no code change of ours — lint/format enforcement lives only on the pinned-nightly jobs. If a host crate ever grows a `#![feature(...)]` it does not strictly need, this job is the one that goes red on stable.

### Why an ARM64 host job?

An arch-only `target_arch = "aarch64"` cfg accidentally includes bare-metal panic handlers and entry points on an ARM host. Cross-building on x86 cannot expose that host hazard. `arm64-host-check` verifies the machine is `aarch64` and Rust targets `aarch64-unknown-linux-gnu`, then runs the four native gates below with the pinned nightly, with Miri setup and the arch-only rejection probe. Only the BSP is excluded; both userland crates participate. Miri is mandatory alongside native compilation and execution.

```sh
cargo check --workspace --exclude tyrne-bsp-qemu-virt
cargo clippy --workspace --exclude tyrne-bsp-qemu-virt --all-targets -- -D warnings
tools/test-ci-gates.sh --arm-host
cargo test --workspace --exclude tyrne-bsp-qemu-virt
cargo miri setup
cargo miri test --workspace --exclude tyrne-bsp-qemu-virt
```

The ARM-only probe first requires the exact workspace clippy command to pass on the unmodified temporary copy, with a private Cargo target. A failing clean baseline stops before mutation, including when it emits one of the recognized error classes. It then restores hello's six arch-only predicates in that same copy and requires the exact workspace clippy command to exit 101 with either the full duplicate-`panic_impl` diagnostic or `error: unwinding panics are not supported without std`. Cargo's parallel all-targets build can report the test harness or normal `no_std` binary first. The probe prints the diagnostic actually observed; tool failures, unrelated errors and unexpected success are refused. `python3 tools/test-arm-host-probe.py` permanently exercises both observed compiler failures and refusal/cleanup paths with offline fixtures. A successful probe means the compiler rejected the regression, not that Miri failed in production. It refuses non-ARM Rust hosts, uses a private Cargo target and removes the temporary copy on exit. [T-036](../analysis/tasks/phase-b2/T-036-ci-arm64-host-check-job.md) separates Apple Silicon, hosted Linux ARM, final PR and post-merge evidence. Its exact display name is `ARM64 host check + clippy + tests + Miri (nightly)`; live registration completed on 2026-10-12 after hosted green and both fresh review rounds.

### How the action versions are pinned

Every third-party GitHub Action is pinned to a full 40-character commit SHA with the human-readable version in a trailing comment (e.g. `actions/checkout@11bd719… # v4.2.2`). Tags are mutable; SHAs are not. This applies the same anti-silent-drift discipline used for `NIGHTLY_PIN` and `cargo-llvm-cov` to the actions that wrap them — `taiki-e/install-action` in particular downloads and executes a prebuilt binary, so a tag repoint would be arbitrary code execution in CI. See [`docs/standards/infrastructure.md`](../standards/infrastructure.md) §"Supply-chain security" → "GitHub Actions pinning" for the refresh path.

## Triggers

- **Every push** to `main` or `development`.
- **Every PR** targeting `main` or `development`.

Concurrent runs on the same branch cancel each other — only the latest commit's verdict matters.

## Philosophy

The CI matrix mirrors what a contributor should run locally before opening a PR:

| Local command | CI job |
|---|---|
| `cargo fmt --all -- --check` | `lint-and-host-test` |
| `cargo host-clippy` | `lint-and-host-test` |
| `tools/test-ci-gates.sh --hal` (panic-family rejection in a disposable copy) | `lint-and-host-test`, after host clippy |
| `cargo host-test` | `lint-and-host-test` |
| `cargo test --release` | `lint-and-host-test` |
| `tools/check-release-tests.sh` (both named release tests must pass) | `lint-and-host-test` |
| `tools/test-ci-gates.sh --release` (profile-flip rejection in a disposable copy) | `lint-and-host-test` |
| `shellcheck --version` + `shellcheck tools/*.sh` | `lint-and-host-test` |
| `tools/test-ci-gates.sh --shell` (expected failure in a disposable copy) | `lint-and-host-test` |
| `tools/test-qemu-tooling.sh` (stubbed QEMU arguments) | `lint-and-host-test` |
| `cargo kernel-build` | `kernel-build` |
| `cargo kernel-clippy` | `kernel-build` |
| `tools/test-ci-gates.sh --bsp` (panic-family rejection in a disposable copy) | `kernel-build`, after debug kernel clippy |
| `cargo clippy -p tyrne-user -p tyrne-userland-hello --target aarch64-unknown-none -- -D warnings` | `kernel-build`, after debug userland build |
| `tools/test-ci-gates.sh --userland` (expected failure in a disposable copy) | `kernel-build` |
| `tools/build-userland.sh --release` + `cargo kernel-build-release` | `kernel-build`, after debug steps |
| `cargo clippy --release --target aarch64-unknown-none -p tyrne-bsp-qemu-virt -- -D warnings` | `kernel-build`, after release image build |
| `tools/build-userland.sh` + `cargo build --target aarch64-unknown-none -p tyrne-bsp-qemu-virt --features perf-bench` | `kernel-build`, restore debug image immediately before perf build |
| `cargo clippy --target aarch64-unknown-none -p tyrne-bsp-qemu-virt --features perf-bench -- -D warnings` | `kernel-build`, last variant lint |
| `tools/smoke.sh --int` + `tools/smoke.sh --release --int` (matching images) | `qemu-smoke` |
| `tools/test-smoke-gates.sh` (synthetic traces) | `lint-and-host-test` and `qemu-smoke` |
| `tools/test-smoke-gates.sh --real` (also private kernel variants) | `qemu-smoke` |
| Native workspace check/clippy/test/Miri and `tools/test-ci-gates.sh --arm-host` (commands above) | `arm64-host-check` |
| `cargo +stable build` + `cargo +stable host-test` (host crates) | `host-stable-check` |
| `cargo miri test --workspace --exclude tyrne-bsp-qemu-virt` | `miri` |
| `cargo llvm-cov --workspace --exclude tyrne-bsp-qemu-virt --exclude tyrne-user --exclude tyrne-userland-hello --summary-only` | `coverage` |

If you pass these locally, CI should pass too. Your local `cargo` runs the pinned nightly automatically (the `rust-toolchain.toml` override), which is the same toolchain the kernel CI jobs use — so a local/CI divergence on those jobs is rare. If you see one, confirm your pinned nightly is installed (`rustup toolchain list` should show `nightly-2026-01-15`); rustup installs it on first use, but a stale or partial install can drift. For the `host-stable-check` job, reproduce with the explicit prefix: `cargo +stable build` (install stable first with `rustup toolchain install stable` if needed).

### Lint and release regression probes

The real ShellCheck and bare-metal userland clippy steps must pass first. `tools/test-ci-gates.sh` then copies the current tracked worktree into a temporary directory, uses a separate Cargo target directory, injects a shell quoting error or a clone-on-Copy lint, and asserts that the exact matching command fails with its expected diagnostic. A passing probe means the deliberate regression was rejected; it is not a red production workflow. The copy is removed on exit, with no source, branch or shared image change. ShellCheck's installed version is printed in CI; measured local and hosted versions are recorded in [T-031](../analysis/tasks/phase-b2/T-031-ci-userland-clippy-and-shellcheck.md).

The release guard runs `cargo test --release -p tyrne-kernel --lib -- console_write_is_absent_in_release_builds console_write_number_is_bad_syscall_in_release_build` and requires both exact test names to pass plus a two-pass summary. Cargo's success alone is insufficient: setting release `debug-assertions = true` compiles both tests out, returns success with zero tests and exposes `console_write`. The `--release` probe makes that profile change only in its disposable copy and requires the guard to reject it. [T-030](../analysis/tasks/phase-b2/T-030-ci-release-profile-gate.md) records local and hosted evidence separately.

The HAL and BSP deny `clippy::panic`, `clippy::unwrap_used` and `clippy::expect_used` at their crate roots. The `--hal` and `--bsp` probes inject a non-test `None` unwrap outside any allowed function, then require the exact `cargo host-clippy` / `cargo kernel-clippy` command to fail with `clippy::unwrap_used`. The BSP probe first builds its matching debug userland image inside the disposable copy; it never overwrites the checkout's shared image. Existing boot/demo/benchmark invariants and deliberate fatal aborts have narrow function-scoped exceptions with reasons, catalogued in [T-032](../analysis/tasks/phase-b2/T-032-panic-family-denies-hal-bsp.md). These three lints do not prohibit `assert!` or prove a panic-free kernel.

The kernel job builds debug first, then release with its matching userland image, then restores the debug userland immediately before debug perf-bench build/lint. The separate `qemu-smoke` job boots matching debug and release ELFs; compilation alone does not establish guest behavior.

### Guest smoke and diagnostic artifacts

`qemu-smoke` (display name `QEMU debug + release smoke (nightly)`) builds each matching userland/kernel profile explicitly before booting it with `--int`. Debug requires exact serial lines `hello from userspace`, `tyrne: userspace task exited` and `tyrne: all tasks complete`. Release requires exit/completion and forbids any userspace greeting. Both reject panic/CPU-fault patterns. Job-scoped explicit Bash enables pipefail so `tee` cannot turn a failed production smoke into a green step. A separate synthetic completion-only probe deliberately fails the actual smoke entry point through the inherited CI log pipeline; it requires nonzero pipeline status plus the real missing-exit diagnostic, and retains its output artifact. Removing pipefail makes this guard fail. An explicit ELF skips compilation; pass `--release` for release expectations. These are marker checks, not an exact SVC count or proof of exit code zero.

```sh
tools/build-userland.sh
cargo kernel-build
tools/smoke.sh --int target/aarch64-unknown-none/debug/tyrne-bsp-qemu-virt
tools/build-userland.sh --release
cargo kernel-build-release
tools/smoke.sh --release --int target/aarch64-unknown-none/release/tyrne-bsp-qemu-virt
tools/build-userland.sh
```

The 20 synthetic trace fixtures cover both positive profiles, each missing required marker, all six panic/fault patterns in both profiles and the forbidden release greeting. With `--real`, three additional disposable kernels omit EL0 publication, omit completion or add a release greeting. Each actual negative must have the intended marker shape, no unrelated fault and the expected smoke rejection. The host-only harness requires Python 3; actual variants additionally need the same Rust/LLVM/QEMU prerequisites as the production guest. It copies current tracked source, uses private build/image paths and removes the copy on exit; no broken source commit or branch is needed.

```sh
tools/test-smoke-gates.sh
tools/test-smoke-gates.sh --real --artifact-dir /tmp/tyrne-smoke-review-evidence
```

The artifact directory must be new; existing paths are refused. `results.json` binds probes to HEAD, a dirty-tracked-worktree flag and the smoke-script hash, and labels synthetic fixtures separately from actual private kernel traces. CI uploads `qemu-smoke-<sha>-<attempt>` on success and failure, retaining it for 14 days. It contains production PID-suffixed raw traces, combined output, probe traces/results/build logs, source/run identity, QEMU/Rust versions and diagnostic wall time. On early failures it contains the evidence available so far. Artifact upload uses runtime credentials with `contents: read`; no token permission is widened.

## Why is `tyrne-bsp-qemu-virt` excluded from Miri and coverage?

The BSP is a bare-metal `no_std` + `no_main` binary whose panic handler conflicts with `std`'s `panic_impl` lang item when built for the host target (which Miri and llvm-cov both require). The `qemu-smoke` job exercises the BSP under actual single-core QEMU. The completed demo spins, so QEMU is stopped by a watchdog; the smoke verdict comes from the trace, not the expected timeout exit status.

## When does the coverage job start gating?

Coverage remains informational and excluded from the versioned required-check policy. T-011 is already complete; its old future-tense trigger does not establish a calibrated floor. A future enforcing floor needs an explicit reviewed decision, reproducible baseline and workflow change before adding coverage to protection. `continue-on-error: true` permits workflow success despite this job failing; it does not itself define a coverage threshold or reliably describe a particular UI color. See [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idcontinue-on-error).

## Documentation consistency

[T-056](../analysis/tasks/phase-b2/T-056-docs-consistency-automation.md), under Accepted [ADR-0043](../decisions/0043-documentation-corpus-consistency.md), provides the offline [checker](../../tools/check-docs.py) and [isolated fixtures](../../tools/test-check-docs.py). **Step 11 boundary:** local-link parsing is implemented; the other consistency families and required CI wiring belong to Step 12. This section does not claim that the current workflow already runs the new command or that hosted execution has occurred.

Use Python **3.9 or newer**, with standard library only. No package installation, Git executable, network access, credential or repository-setting write is needed. Default root comes from the script's location, so an absolute script path also works from another cwd. `--root` selects an isolated fixture/export root; it does not change the caller's checkout. The command prints sorted `file:line: code: message` findings and exits 0 for a clean selected check, 1 for inconsistent/invalid source, and 2 for invalid CLI arguments. `--json` prints deterministic structured results on stdout. The parser and CLI do not write source, bytecode, reports or settings; redirect stdout explicitly when retaining a capture.

```sh
python3 tools/test-check-docs.py
python3 tools/check-docs.py --checks links
python3 tools/check-docs.py --root /path/to/fixture --json
```

The public corpus is `docs/**/*.md`, the five root entry files README/CLAUDE/AGENTS/SECURITY/CONTRIBUTING and `.agents/skills/**/*.md`. Every public historical archive and review is included; generated-looking directory basenames do not exclude public Markdown. Existing [.gitignore](../../.gitignore) classifies `docs/analysis/technical-analysis/`, `docs/analysis/private/` and `docs/analysis/temp/` as local-only notes/drafts: those exact prefixes are outside repository input, and links into them fail even when a local file or symlink alias exists. There is no configurable archive ignore list or broken-link exception. Source-root, ancestor and leaf symlinks, including dangling/loop aliases, are diagnosed before source opening. Document and source-line reads require regular files, so a FIFO cannot wait for a writer. Links cannot escape the repository root.

Physical source lines use LF, CR or CRLF consistently for parsing, diagnostics and source-line fragments; other Unicode/control separators remain content. Markdown local destinations retain their decoded characters, including leading spaces and numeric-reference tabs/newlines. For HTML href/src, [URL input cleanup](https://url.spec.whatwg.org/#concept-basic-url-parser) trims leading/trailing C0 controls and spaces, then removes ASCII tabs and newlines before selecting the target. Percent-encoded characters are decoded afterward and are not trimmed again. These explicit source-context rules give the same target identity on supported Python versions; they do not claim complete browser URL normalization.

Recognized HTML tags retain multiline quoted attributes as metadata before block, reference-definition and heading processing. Attribute text cannot open a fence, define a reference, create an automatic heading or consume its duplicate suffix. Actual id/name/href/src attributes remain checked, with their original physical diagnostic lines.

[GFM tables](https://github.github.com/gfm/#tables-extension-) require matching header/delimiter cell counts and allow optional edge pipes/alignment colons. Each cell has its own inline-code, comment, HTML and link-label context; those constructs cannot continue into another cell or row. Escaped pipes become cell content before inline parsing, including HTML attributes and reference labels; references resolve through document-wide definitions. Table cells cannot define block headings/references. Body cells beyond the header width are not rendered navigation, while original ranges for every cell remain available to source-inventory checks. Blank lines or new block syntax end a table. Ordinary non-table pipes retain their existing meaning; tables and archives are not excluded from the corpus. Inline comments require a complete closing marker within their current block/cell; the short `<!-->` and `<!--->` forms are recognized. An incomplete inline opener remains literal text and cannot hide later navigation. Real block-start comments can span blank lines through their closing marker or container/document end; comment contents cannot change that container. Parent inline state cannot cross table rows removed from the parent parsing view. The closing physical line of a block-start comment remains raw HTML: actual tags after the closer are checked, while Markdown labels, code/fence text and heading-like text on that line stay literal. Raw tag attributes can continue without creating Markdown blocks. A shared physical-line layout preserves original container body offsets: an ASCII ordered non-1 marker cannot interrupt an open paragraph, but a later sibling of an existing list or a list after a real blank remains a block. Lazy quote/list continuation retains its paragraph context. Blank-line syntax is ASCII space/tab, not arbitrary Unicode whitespace; backslashes escape only ASCII punctuation and cannot skip physical separators. Source-line fragments use ASCII decimal digits. Bare destinations reject raw ASCII controls/spaces while retaining non-ASCII filename content; decoded numeric-reference characters keep their separate source-specific semantics.

The shared layout also records actual paragraph identity and leaf kind. An eligible setext underline consumes its open paragraph once; it cannot include a prior completed heading, thematic break, list sibling or different quote container. Bare `===` on a lazy container continuation remains paragraph text. Missing inner quote markers retain the full lazy paragraph context. Masking an inline comment or HTML metadata cannot manufacture a source blank line. Heading extraction uses a forward pass over those extents, preserving actual multiline titles and duplicate suffixes without repeated backward scans.

Structural indentation uses four-column tab stops, with original source offsets and inline text preserved. A matched existing list parent can open another item or a different-delimiter list before inner-quote lazy fallback; a list beneath an unmatched outer quote retains its noninterrupting lazy continuation. Automatic heading text removes actual HTML/comment spans at zero width, including line endings inside them. Genuine outside spaces and soft breaks, duplicate suffixes, code contents and escaped text retain their meanings. Removed markup cannot fabricate slug hyphens; ATX closing markers are determined from source syntax.

Supported source grammar:

- Inline, full/collapsed reference and defined-shortcut links and images, including images inside link labels and odd/even escape parity; balanced/escaped labels and destinations, angle/empty destinations (including explicit empty-angle reference definitions), optional titles and container-aware reference continuations. Nested links are diagnosed. Reference keys use raw case-folded/whitespace-normalized labels; duplicate definitions and undefined explicit references fail. A definition cannot interrupt prose: separate it with a blank line. An undefined standalone bracket phrase remains ordinary prose. Quoted defect examples must explicitly delimit literal Markdown data.
- Fences match delimiter character and sufficient closing length relative to ordered quote/list containers; excess list-marker padding retains code indentation. Indented code is distinguished from paragraph continuation. Matching backtick spans may cross soft line breaks within a block; run/block indexes avoid repeated suffix scans. Actual comments/code are excluded without shifting source line numbers. Link titles/destinations, HTML attributes and escaped HTML markers cannot create comments, links or anchors; unrelated prose remains checked.
- File/directory, same-file and repository-root-relative paths; source-specific decoding exactly once, followed by UTF-8 URL decoding. Markdown entities require a complete known name/semicolon or bounded numeric spelling, and escaped ampersands remain literal. Numeric references preserve valid noncharacter/control scalars; null, surrogate and out-of-range values become U+FFFD. Only HTML applies its legacy C1 numeric replacements. Raw HTML attributes use the HTML named-reference attribute-context rule, retain quoted/unquoted values and diagnose duplicate relevant attributes; attribute diagnostics preserve their physical source line. Filename case is exact even on a case-insensitive host. A leading slash means repository root. External URI/protocol-relative destinations are never fetched. Query strings do not change the local file target.
- ATX/setext headings, inline label/code text (including HTML-looking code and literal underscores), matched emphasis, Unicode letters/numbers/combining marks, underscore/hyphen retention and collision-aware duplicate suffixes; explicit HTML `id` and `<a name>` anchors. Custom anchors do not consume automatic suffixes. Fragments are case-sensitive. A directory fragment resolves through its `README.md`; source `#L1`/`#L1-L3` fragments must stay within actual line bounds. Actual HTML anchor links/image sources are checked too.

This is a bounded source checker, not a complete CommonMark renderer or proof of architectural correctness. Relevant malformed/unsupported link syntax produces findings rather than being discarded. Inputs are limited to 16 MiB per document, balanced nesting to 64 and reference-definition labels to 999 characters; limits fail visibly. Fixtures define the supported contract, including false-positive controls. [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/), [HTML attribute character references](https://html.spec.whatwg.org/multipage/parsing.html#named-character-reference-state) and [GitHub link/anchor documentation](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax) are syntax references, not a claim of complete rendering parity.

To extend grammar, add an isolated failing contract fixture first, update parsing/resolution and this supported-contract description, then run both fixtures and the whole public corpus. Distinguish parser false positives from real baseline defects; return genuine defects to their named owning tasks and review bounded repairs. Do not add broad exclusions. Adding the task/review/ADR/ledger/fence/audit/live checks and required existing-job enforcement follows the approved Step 12; static commit-scope allowlisting remains deliberately skipped under ADR-0043.

## Adding a new check

1. Add a job to [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).
2. Keep the fast-lane job order stable — `lint-and-host-test` must remain first so red PRs fail quickly.
3. If the check requires a nightly feature, put it in its own job (not folded into `lint-and-host-test`).
4. Update this guide's table.

## Nightly pinning

Miri and cargo-llvm-cov use a **pinned** nightly declared via the `NIGHTLY_PIN` env var in [ci.yml](../../.github/workflows/ci.yml) and [performance.yml](../../.github/workflows/performance.yml). Rolling nightly means that a miri or `llvm-tools` regression on the public nightly channel breaks CI without any commit of ours being the cause; pinning isolates us from that.

cargo-llvm-cov itself is also pinned — installed via [`taiki-e/install-action`](https://github.com/taiki-e/install-action) which downloads a prebuilt binary rather than compiling from source. The version is in the workflow as `tool: cargo-llvm-cov@<x.y.z>` (`0.6.16` at the time of writing). Pinning the tool prevents an upstream release from silently changing what "coverage" reports.

Current pins:
- `NIGHTLY_PIN = nightly-2026-01-15` (set 2026-04-23 when R6 landed; shared by both workflows).
- `cargo-llvm-cov 0.6.16` (set 2026-04-28; see `coverage` job in `ci.yml`).

To bump either pin:

1. Open an issue titled "Bump &lt;pin&gt; to &lt;new-version&gt;" stating the reason (new Miri check we want, a compiler feature we need, a cargo-llvm-cov bug fix, a security advisory, routine refresh).
2. Update `NIGHTLY_PIN` in both workflows, or `tool: cargo-llvm-cov@…` in `ci.yml`, then refresh the "Current pins" list above.
3. Run `cargo +nightly-YYYY-MM-DD miri test --workspace --exclude tyrne-bsp-qemu-virt` and `cargo +nightly-YYYY-MM-DD llvm-cov --workspace --exclude tyrne-bsp-qemu-virt --exclude tyrne-user --exclude tyrne-userland-hello --summary-only` locally; make sure both are green on the new pin.
4. Land the pin bump in its own commit with `Refs:` to the issue. The two pins can be bumped together or independently.

## Weekly performance reports

[performance.yml](../../.github/workflows/performance.yml) runs Monday at **03:17 UTC**, on manual dispatch, and on `development` pushes touching that workflow or `tools/perf-harness.sh`; pushes touching neither path do not trigger it. It has no PR trigger. Each run builds matching debug userland/kernel, runs `tools/perf-harness.sh --iterations=20 --report=ci-nightly` and uploads `performance-<sha>-<attempt>` for 14 days. New reports include full SHA, tracked-worktree state, the Rust toolchain identifier/compiler, QEMU, host OS/release/machine, all valid raw samples, failed count, wall time and the percentile band. The toolchain explanation containing the checkout path and the host name are omitted; failed optional metadata commands produce `(unknown)` without discarding measurements. Earlier baseline reports retain their original captured metadata as historical evidence. The artifact also has run/source identity, full Rust/QEMU versions and harness output; available diagnostics upload even when measurement fails. Reports refuse overwrites and are downloaded artifacts, never committed by CI. Explicit Bash/pipefail propagates harness failures through logging.

A failed measurement/build/upload is a visible failed workflow. There is no calibrated performance threshold; neither this job nor coverage is in the required-check definition. Compare bands only with matching host/profile context; QEMU timings are not hardware latency guarantees.

[GitHub schedule semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) are best effort: runs may be delayed or dropped, execute from the default branch, and public-repository schedules disable after 60 days without repository activity. Schedule/dispatch registration requires the workflow on the default branch; pre-merge `development` push evidence is separate. After maintainer merge, verify the first main CI run and dispatch:

```sh
gh workflow enable performance.yml --repo HodeTech/Tyrne
gh workflow run performance.yml --repo HodeTech/Tyrne --ref main
gh run list --repo HodeTech/Tyrne --workflow performance.yml
gh run download <run-id> --repo HodeTech/Tyrne --dir /tmp/tyrne-performance-download
```

These are maintainer operations; no CI administrative secret is used. Record the actual dispatch/run/artifact evidence in [T-035](../analysis/tasks/phase-b2/T-035-ci-hygiene-tail.md), keeping it pending until default-branch registration exists.

## Versioned classic branch protection

[main.json](../../.github/branch-protection/main.json) captures the complete supported classic `main` policy, including six exact display names with GitHub Actions app binding 15368 and strict checking. It preserves the existing solo-phase review count 0, disabled admin enforcement/signatures/force-push/deletion, required linear history/conversation resolution and all other captured toggles. [T-034](../analysis/tasks/phase-b2/T-034-ci-qemu-smoke-job.md) and [T-036](../analysis/tasks/phase-b2/T-036-ci-arm64-host-check-job.md) record the subsequent smoke/ARM additions and full-policy read-backs. This captures existing protection; it does not enact the standards' future multi-contributor review-count policy.

Required checks are exactly `fmt + clippy + host tests (nightly)`, `aarch64-unknown-none kernel build (nightly)`, `host crates on stable`, `miri (Stacked Borrows)`, `QEMU debug + release smoke (nightly)`, and `ARM64 host check + clippy + tests + Miri (nightly)`. Coverage and performance remain excluded by policy. GitHub can accept successful, skipped or neutral required-check conclusions; the former claim that neutral always blocks was incorrect. [GitHub protected-branch reference](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches#require-status-checks-before-merging).

The source-app binding identifies GitHub Actions as the producer; it does not attest to a particular workflow file, command body or trusted revision. Workflow/tool changes and the actual run remain subjects of maintainer review. A changed workflow can emit the expected context, while duplicate job names can cause ambiguous results and block merging; no duplicate-name bypass has been demonstrated here. The preserved solo policy has `enforce_admins: false`, approving-review count 0 and code-owner review disabled. GraphQL review enablement and the REST approval count are distinct captured properties; the tool does not infer one from the other. These are the current policy's boundaries, not additional security guarantees or a new acceptance decision. [GitHub protection semantics](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

Public PR runs can consume runner capacity. Concurrency cancellation is per workflow/ref; it does not cap distinct PRs. Smoke and ARM jobs have 10/15-minute limits. Fork-run approval and organization capacity settings are external administration, not controls enforced or verified by this repository's policy tool. No billing or approval-setting change is made here.

Use Python 3 and an authenticated `gh` locally. The tool is bound to `github.com`, `HodeTech/Tyrne`, `main`; export/check need read access and apply needs administration permission. Exit 0 means match/success, exit 1 means drift/verification/environment failure, exit 2 means usage error. The [captured REST fixture](../../tools/fixtures/README.md) exercises the actual protection response. Unsupported actor/enforcement policy or unknown endpoint fields remain fail-closed; fields from a branch-summary response are not silently treated as protection metadata. `check` prints a unified diff on drift.

```sh
python3 tools/branch-protection.py export > /tmp/tyrne-main-before.json
python3 tools/branch-protection.py check
# Review the snapshot and definition diff before this explicit local apply:
python3 tools/branch-protection.py apply \
  --expected-current /tmp/tyrne-main-before.json \
  --verified-sha <full-40-character-remotely-green-sha>
python3 tools/branch-protection.py check
python3 tools/test-branch-protection.py
```

Apply refuses a CI environment, unexpected full-policy drift, a new repository/inherited ruleset, unrepresentable settings, unknown fields, missing/duplicate JSON fields, check removal, source-app rebinding or any non-status/strict change. It can only add checks; each addition needs exactly one completed successful remote check at the supplied full SHA with its explicit source app. It refuses incomplete/paginated check evidence. A matching policy is a real no-op. Read-only GraphQL also captures the applied classic rule's PR-review enablement, deployment requirements, push/review restrictions and actor-allowance counts omitted by the REST response; nonempty actor/deployment extensions stop reconciliation. See [GitHub BranchProtectionRule schema](https://docs.github.com/en/graphql/reference/branches#branchprotectionrule). Only known response URLs and duplicated context metadata are normalized; push restrictions or review-policy extensions require a deliberate tooling update, never silent omission.

Immediately before the narrow required-status-checks PATCH, the complete policy is read again; afterward it must match the entire desired definition. The API offers no documented atomic conditional update for this operation: another administrator can still race between read and write. Coordinate administrative changes. Post-write mismatch is an error requiring inspection, without automatic rollback that could overwrite a concurrent change. Unexpected drift must be reconciled and reviewed in the snapshot/definition; do not blindly re-export over the committed definition. CI runs offline safety fixtures only and receives no administrative credentials. [GitHub status-check protection API](https://docs.github.com/en/rest/branches/branch-protection#update-status-check-protection).
