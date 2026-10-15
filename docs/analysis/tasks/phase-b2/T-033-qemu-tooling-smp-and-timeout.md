# T-033 — Add --smp N and a usage-checked --timeout to the QEMU tooling

- **Phase:** B.2
- **Milestone:** Track B.2-1
- **Status:** Done
- **Created:** 2026-10-11
- **date_done:** 2026-10-12
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-034](T-034-ci-qemu-smoke-job.md), [T-074](T-074-phase-c-readiness-sweep.md)
- **ADRs required:** none

---

## User story

As a developer about to bring up a second core, I want `tools/run-qemu.sh` and `tools/smoke.sh` to accept a core count and to reject malformed flags with a usage message, so that Milestone C1's `-smp 4` run needs no tooling retrofit and a typo in `--timeout` does not die with a shell internals error.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). At the opening snapshot, QEMU's core count was hard-coded to 1 in three places: `tools/run-qemu.sh:92`, `tools/smoke.sh:73` and the cargo runner string at `.cargo/config.toml:25`. Milestone C1 ("Secondary core start" in `docs/roadmap/phases/phase-c.md`) has a Tests item "QEMU run with `-smp 4` brings all four cores to a known checkpoint", which could not be attempted through the project's scripts at that snapshot. Separately, `tools/smoke.sh:29` does `TO="$2"; shift 2` under `set -u`; reproduced on HEAD 2026-10-11: `bash tools/smoke.sh --timeout` prints `line 29: $2: unbound variable` and exits 1, whereas every other usage error in the script exits 2.

This task covers three `phase-b2.md` entries (line numbers as of the opening snapshot; locate by headline): Track B.2-1 LOW "QEMU wrapper tooling hardcodes `-smp 1` with no override" (line 57), the Polish item "Parameterize the QEMU core count (`QEMU_SMP` ...)" (line 592), and the Track B.2-3 LOW "`smoke.sh`'s `--timeout` flag crashes with an unbound-variable error" (line 326).

## Acceptance criteria

- [x] `tools/run-qemu.sh` accepts `--smp N` and a `QEMU_SMP` environment default (precedence: flag, then environment, then 1) and passes `-smp N` to QEMU; `N` must match a positive integer or the script prints an error and exits 2. Its argument loop (`for arg in "$@"`, line 32) must be restructured to consume a value.
- [x] `tools/smoke.sh` accepts the same `--smp N` / `QEMU_SMP` with the same validation, replacing the literal in `QEMU_ARGS` (line 73); the default invocation still passes `-smp 1`.
- [x] `tools/smoke.sh --timeout` and `tools/smoke.sh --smp` with no value (and the `run-qemu.sh --smp` equivalent) exit 2 with a one-line message naming the flag (for example "--timeout requires a value") and never print `unbound variable`; both usage headers (the comment blocks the `-h` output is generated from) document the new flags and the precedence.
- [x] `docs/guides/run-under-qemu.md` gains a short "core count" section: `--smp`/`QEMU_SMP`, the cargo-runner override `CARGO_TARGET_AARCH64_UNKNOWN_NONE_RUNNER`, and a warning that N > 1 is unsupported by today's kernel (no secondary-core bring-up; see Design notes); the manual `-smp 1` command (line 76) is annotated and the comment at `.cargo/config.toml:22-25` points at the guide. `.cargo/config.toml`'s runner stays `-smp 1`.
- [x] Tests (scripted invocations recorded in the review history, no new framework): with a stub `qemu-system-aarch64` first on `PATH` that prints its argv, the default run shows `-smp 1`, `QEMU_SMP=3` shows `-smp 3`, `--smp 2` overrides `QEMU_SMP=3`, and `--smp 0`, `--smp abc`, bare `--smp` and bare `--timeout` exit 2; `CARGO_TARGET_AARCH64_UNKNOWN_NONE_RUNNER=echo cargo kernel-run` prints the ELF path, proving the documented override takes effect.
- [x] `shellcheck tools/*.sh` is clean for the two edited scripts if [T-031](T-031-ci-userland-clippy-and-shellcheck.md) has landed (otherwise run it locally and record the result).

## Out of scope

- Making the kernel or BSP SMP-capable, a `_start` park guard, or secondary-core start: Phase C.
- A new flag for `tools/perf-harness.sh` (it inherits `QEMU_SMP` only through `run-qemu.sh`, which is acceptable) and any change to `tools/build-userland.sh`.
- The CI job that runs `tools/smoke.sh`: [T-034](T-034-ci-qemu-smoke-job.md).
- Changing the cargo runner string itself (it is static; the override is documented, not automated).

## Approach

Add `--smp N` and `QEMU_SMP` to both scripts, validate with the same strictly-positive-integer regex `tools/smoke.sh:41` already uses for the timeout, and thread the value into the `-smp` operand. Convert `run-qemu.sh`'s `for arg` loop into the `while [[ $# -gt 0 ]]` / `shift` style of `smoke.sh` (or accept `--smp=N`); fix the `smoke.sh` `$2` trap by checking `[[ $# -ge 2 ]]` before consuming a value. The `-h` text of both scripts is generated from their header comments (`smoke.sh:30`, `run-qemu.sh:26-30`), so update the headers, not a separate usage string. The cargo runner cannot read an environment variable inside its static string, so the plan item's remedy is documentation of Cargo's runner override.

## Definition of done

Beyond the acceptance criteria:

- [x] `cargo fmt --all -- --check` clean.
- [x] `cargo host-clippy` clean with `-D warnings`.
- [x] `cargo kernel-clippy` clean.
- [x] `cargo host-test` passes.
- [x] `tools/smoke.sh --int` PASS with default arguments (the `smoke.sh` change must not alter the default run).
- [x] Every touched markdown file has all `](...)` link targets resolving.
- [x] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with a `Refs: ADR-0040` trailer.
- [x] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **`--timeout` spelling (implementer's choice, record in the review history):** keep `--timeout SECONDS` with a presence check (preserves the documented `--timeout 30` at `smoke.sh:14`), or move to `--timeout=SECONDS` as `tools/perf-harness.sh:113-114` does. The criteria hold for either; if the `=` form is chosen, the bare-word form must be rejected with a clear message and the header updated.
- **N > 1 is a tooling affordance only.** `bsp-qemu-virt/src/boot.s` `_start` (line 45 on) has no `MPIDR_EL1` check, and `phase-c.md` carries an item about the missing secondary-core park guard; behaviour of the current kernel with `-smp` above 1 is therefore not guaranteed, and CI/smoke stay at 1. The guide must say so rather than imply support. Printing a stderr note when N > 1 is optional.
- **Location re-verification (2026-10-11, HEAD `400dec0`):** `run-qemu.sh:92`, `smoke.sh:73`, `smoke.sh:29`, `.cargo/config.toml:25` and `run-under-qemu.md:76` match the plan item. The `phase-b2.md` line numbers cited above (57, 592, 326) are those of the opening snapshot; the live file has since shifted by the kickoff banner, so locate its items by headline.
- Sequencing: lands before [T-034](T-034-ci-qemu-smoke-job.md), which should be written against the final flag spelling; it also feeds the Phase C readiness sweep ([T-074](T-074-phase-c-readiness-sweep.md)).

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
| 2026-10-11 | Codex (AI agent) | Preflight contract review: see [review artifact](../../reviews/code-reviews/2026-10-11-phase-b2-track1-preflight.md); documentation corrected, implementation not started; ADR-0040 remains Proposed. |
| 2026-10-12 | Codex (AI agent) | Started step 2 after T-037's implementation gates and both fresh review rounds. Reproduced the missing timeout value error on `3a7c264`. Keep the space-separated flag syntax; the last repeated flag wins, a valid flag overrides an invalid environment default, and an empty environment value is invalid. Reject extra ELF arguments consistently. Add a dependency-free stub regression script to the existing fast CI lane; it does not claim SMP runtime support or replace T-034. Refresh the existing QEMU guide's stale build prerequisites and completion instructions while adding the required core-count section. |
| 2026-10-12 | Codex (AI agent) | Implementation gates passed: 59 stub argument cases; real default single-core `tools/smoke.sh --int --timeout 5` (greeting, exit, completion, exactly two expected SVCs, no fault); Cargo runner echo printed the ELF path; fmt, host/kernel clippy and 366 host tests passed (two ignored HAL doctests). Local Markdown link targets resolve. ShellCheck on the two runners and harness finds only the pre-existing `smoke.sh` SC2054 comma-token warning; T-031 follows immediately. Actionlint's workflow/schema check passes with its ShellCheck integration disabled; full integration reports existing unquoted `NIGHTLY_PIN` expansions, also to be corrected in T-031. No SMP execution claim. Hosted T-033 verification and both fresh review rounds pending. |
| 2026-10-12 | `b21_step2_round1_code`, `b21_step2_round1_integration` (gpt-6.1-sol/high) | Fresh round 1 on `3a7c264..d5c13a0`: both Approve, no introduced findings. [Full independent reports](../../reviews/code-reviews/2026-10-12-t033-qemu-tooling.md). Code reviewer reproduced the old timeout failure, ran 25 independent Bash 3 cases, rejected nine parser mutants and independently passed real single-core smoke. Integration reviewer passed 31 additional isolated probes, including the Perl fallback and profile/build-order checks. No SMP claim. |
| 2026-10-12 | Codex (AI agent) | [Hosted CI at `d5c13a0`](https://github.com/HodeTech/Tyrne/actions/runs/38176428435) succeeded; inspected the fast-lane log confirming the new 59-case regression step passed. Round 2 and final maintainer PR review remain pending. |
| 2026-10-12 | `b21_step2_round2_code`, `b21_step2_round2_integration` (gpt-6.1-sol/high requested) | Fresh round 2 on `3a7c264..eede01c`: both Approve; code found no new issue, integration found Low R2-INT-01 (new guide's inherited WFI description). Root verified task A actually spins and corrected guide plus matching live smoke/performance descriptions, preserving prior report prose with an explicit superseding note. [Full reports and reconciliation](../../reviews/code-reviews/2026-10-12-t033-qemu-tooling.md). Independent evidence: 47 code and 39 integration probes; code reviewer passed real default smoke with the unchanged 117-byte hash. Wording-fix Bash syntax and the 59-case harness passed. Both rounds complete; final maintainer PR review pending. |
| 2026-10-12 | @cemililik; Codex recorded completion | Maintainer merged [PR #48](https://github.com/HodeTech/Tyrne/pull/48) at full `c16997e003fbd1726d1205734380394781c52002` and explicitly authorized Done promotion. First merged-main [CI 38217531542](https://github.com/HodeTech/Tyrne/actions/runs/38217531542) passes all seven jobs, including native ARM/Miri and both production QEMU profiles; downloaded controls are 23/23. Default-branch [performance dispatch 38217799773](https://github.com/HodeTech/Tyrne/actions/runs/38217799773) passes with 20 valid/0 failed samples. [Post-merge retrospective](../../reviews/business-reviews/2026-10-12-phase-b2-track1-completion.md) records exact-source evidence, remaining scope and next Ready task T-038. Status In Review → Done; date_done 2026-10-12. Phase B.2 remains Active. |
