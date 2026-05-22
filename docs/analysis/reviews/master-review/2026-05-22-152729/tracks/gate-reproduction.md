# Gate reproduction (master review, commit 288ddb2)

Anchor commit: `288ddb2be98e4a679cb5a07ba8a70e52b82c21a7`
Run date: 2026-05-21
Agent: GATE-REPRODUCTION (claude-sonnet-4-6)

---

## Environment

| Component | Version |
|---|---|
| OS | macOS 15.7.3 (Darwin 24.6.0, arm64 host) |
| rustc | `1.94.0-nightly (86a49fd71 2026-01-14)` — matches `rust-toolchain.toml` pin `nightly-2026-01-15` |
| cargo | `1.94.0-nightly (6d1bd93c4 2026-01-10)` |
| qemu-system-aarch64 | `10.2.2` |
| cargo-llvm-cov | installed at current version (not pinned locally; CI pin is 0.6.16 via taiki-e/install-action) |

Toolchain note: the active toolchain is `nightly-2026-01-15` as pinned by `rust-toolchain.toml`. The CI workflow uses `stable` for `lint-and-host-test` and `kernel-build`, and `nightly-2026-01-15` for `miri` and `coverage`. Local runs here used the pinned nightly for all gates (the workspace `rust-toolchain.toml` governs); this matches behavior for miri and coverage exactly. For fmt/clippy/host-test/kernel-build the nightly toolchain was used rather than stable — no divergence was observed.

---

## Results table

| # | Gate | Command | Status | Key numbers |
|---|---|---|---|---|
| 1 | fmt | `cargo fmt --all -- --check` | **PASS** | exit 0, no diff |
| 2a | host clippy | `cargo host-clippy` | **PASS** | exit 0, 0 warnings |
| 2b | kernel clippy | `cargo kernel-clippy` | **PASS** | exit 0, 0 warnings |
| 3 | host tests | `cargo host-test` | **PASS** | **260 passed** (42 hal + 175 kernel + 43 test-hal), 0 failed |
| 4 | kernel build | `cargo kernel-build` | **PASS** | exit 0, aarch64-unknown-none ELF produced |
| 5 | miri | `cargo +nightly miri test --workspace --exclude tyrne-bsp-qemu-virt` | **PASS** | 260 passed (42+175+43), 0 failed; integer-to-pointer cast warnings only (advisory, not errors) |
| 6 | coverage | `cargo llvm-cov --workspace --exclude tyrne-bsp-qemu-virt --summary-only` | **PASS** | Regions **96.26%** / Lines 95.76% / Functions 93.09% |
| 7 | QEMU smoke | `qemu-system-aarch64 -M virt ... -kernel tyrne-bsp-qemu-virt` | **PASS** | Full trace through `tyrne: all tasks complete`; elapsed ~27–33 ms; 629 guest_error events (all pre-existing PL011 disabled-UART noise) |

All seven gates PASS.

---

## Per-gate detail

### Gate 1 — `cargo fmt --all -- --check`

```
EXIT_STATUS:0
```

No output (clean diff means no formatting violations). Exit status 0.

---

### Gate 2a — `cargo host-clippy`

```
Checking tyrne-hal v0.0.1
Checking tyrne-test-hal v0.0.1
Checking tyrne-kernel v0.0.1
Finished `dev` profile [optimized + debuginfo] target(s) in 27.09s
EXIT_STATUS:0
```

Zero warnings. Clippy ran with `-D warnings` (from workspace `RUSTFLAGS` / alias definition).

---

### Gate 2b — `cargo kernel-clippy`

```
Checking tyrne-hal v0.0.1
Checking tyrne-kernel v0.0.1
Checking tyrne-bsp-qemu-virt v0.0.1
Finished `dev` profile [optimized + debuginfo] target(s) in 10.01s
EXIT_STATUS:0
```

Zero warnings on the `aarch64-unknown-none` target.

---

### Gate 3 — `cargo host-test` (actual test count)

**Total: 260 passing tests, 0 failures.**

Breakdown by crate:

| Crate | Binary | Passed |
|---|---|---|
| `tyrne-hal` | `tyrne_hal` | 42 |
| `tyrne-kernel` | `tyrne_kernel` | 175 |
| `tyrne-test-hal` | `tyrne_test_hal` | 43 |
| doc-tests (hal) | — | 0 (2 ignored) |
| doc-tests (kernel) | — | 0 (1 ignored) |
| doc-tests (test-hal) | — | 0 |
| **TOTAL** | | **260** |

The `tyrne-bsp-qemu-virt` crate is excluded from workspace default-members and does not appear in `cargo host-test` output (as designed).

Key result lines from each crate:
```
test result: ok. 42 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s   [tyrne_hal]
test result: ok. 175 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.01s  [tyrne_kernel]
test result: ok. 43 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s   [tyrne_test_hal]
```

---

### Gate 4 — `cargo kernel-build`

```
Compiling tyrne-hal v0.0.1
Compiling tyrne-kernel v0.0.1
Compiling tyrne-bsp-qemu-virt v0.0.1
Finished `dev` profile [optimized + debuginfo] target(s) in 9.33s
EXIT_STATUS:0
```

ELF produced at `target/aarch64-unknown-none/debug/tyrne-bsp-qemu-virt`.

---

### Gate 5 — `cargo +nightly miri test --workspace --exclude tyrne-bsp-qemu-virt`

**Total: 260 passing tests, 0 failures.** Exit status 0.

Results per crate:
```
test result: ok. 42 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 5.37s   [tyrne_hal under miri]
test result: ok. 175 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 25.89s [tyrne_kernel under miri]
test result: ok. 43 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 5.54s   [tyrne_test_hal under miri]
```

Miri emitted **integer-to-pointer cast warnings** (advisory) in the following contexts:

- `kernel/src/mm/pmm.rs:874` — `aligned_backing` test helper (integer → `*mut u8` for aligned allocation in tests)
- `kernel/src/mm/pmm.rs:378` — `Pmm::alloc_frame` identity-map `pa_usize as *mut u8`
- `kernel/src/obj/task_loader.rs:871` — `aligned_backing` test helper (same pattern)
- `kernel/src/mm/mod.rs:168` — `phys_frame_kernel_ptr` (`frame.as_usize() as *mut u8`)

All warnings carry the standard Miri advisory text: `this program is using integer-to-pointer casts... which means that Miri might miss pointer bugs`. These are **not errors** — they reflect the identity-mapping assumption that is explicitly documented in UNSAFE-2026-0025 and UNSAFE-2026-0026 audit entries. No Stacked Borrows violations, no undefined behavior detected. The warnings suggest a future strict-provenance migration path (noted for the carry-forward section).

---

### Gate 6 — `cargo llvm-cov --workspace --exclude tyrne-bsp-qemu-virt --summary-only`

**Coverage summary (workspace, excluding BSP):**

| Metric | Covered | Missed | % |
|---|---|---|---|
| **Regions** | 9580 / 9952 | 372 | **96.26%** |
| **Functions** | 539 / 579 | 40 | **93.09%** |
| **Lines** | 5489 / 5732 | 243 | **95.76%** |

Per-file breakdown (weakest to strongest by region coverage):

| File | Regions % | Functions % | Lines % | Notes |
|---|---|---|---|---|
| `hal/src/mmu/mod.rs` | 67.74% | 66.67% | 66.67% | Trait declaration surface; MMU page-table walk live but some error paths not exercised |
| `kernel/src/sched/mod.rs` | 92.41% | 72.41% | 92.65% | Post-switch spin-loop tail + raw-pointer error paths; functions% low due to unreachable-from-host context-switch impls |
| `kernel/src/obj/task_loader.rs` | 93.83% | 94.34% | 93.55% | New in T-019; some deep rollback paths and error arms not covered |
| `kernel/src/cap/mod.rs` | 95.00% | 100.00% | 94.74% | — |
| `kernel/src/obj/arena.rs` | 96.56% | 95.00% | 95.38% | — |
| `kernel/src/mm/address_space.rs` | 96.37% | 97.67% | 96.30% | — |
| `kernel/src/obj/notification.rs` | 96.33% | 91.67% | 95.38% | — |
| `kernel/src/cap/table.rs` | 97.54% | 98.31% | 96.25% | — |
| `kernel/src/ipc/mod.rs` | 97.84% | 100.00% | 98.05% | — |
| `kernel/src/mm/pmm.rs` | 98.91% | 100.00% | 98.42% | — |
| `test-hal/src/cpu.rs` | 97.83% | 94.74% | 96.70% | — |
| `test-hal/src/irq_controller.rs` | 98.31% | 94.74% | 96.74% | — |
| `test-hal/src/mmu.rs` | 99.40% | 97.37% | 99.04% | — |
| `hal/src/mmu/vmsav8.rs` | 98.36% | 100.00% | 100.00% | — |
| `hal/src/timer.rs` | 100.00% | 100.00% | 100.00% | — |
| `kernel/src/cap/rights.rs` | 100.00% | 100.00% | 100.00% | — |
| `kernel/src/mm/mod.rs` | 100.00% | 100.00% | 100.00% | — |
| `kernel/src/obj/endpoint.rs` | 100.00% | 100.00% | 100.00% | — |
| `kernel/src/obj/task.rs` | 100.00% | 100.00% | 100.00% | — |
| `hal/src/console.rs` | 100.00% | 100.00% | 100.00% | — |
| `hal/src/cpu.rs` | 100.00% | 100.00% | 100.00% | — |
| `test-hal/src/console.rs` | 100.00% | 100.00% | 100.00% | — |
| `test-hal/src/timer.rs` | 100.00% | 100.00% | 100.00% | — |

Exit status 0.

---

### Gate 7 — QEMU smoke test

**Boot trace (full, verbatim):**

```
tyrne: hello from kernel_main
tyrne: mmu activated
tyrne: pmm initialized (32599 frames available; 169 reserved)
tyrne: address-space-arena ready (1 / 8 slots used; bootstrap AS root = 0x40095000)
tyrne: image loaded (entry = 0x800000; sp = 0x802000; image bytes 8; stack bytes 4096; AS cap = idx 1)
tyrne: timer ready (62500000 Hz, resolution 16 ns)
tyrne: starting cooperative scheduler
tyrne: task B — waiting for IPC
tyrne: task A -- sending IPC
tyrne: task B — received IPC (label=0xaaaa); replying
tyrne: task A — received reply (label=0xbbbb); done
tyrne: all tasks complete
tyrne: boot-to-end elapsed = 26824000 ns
```

Kernel then enters `spin_loop` idle (halts output). Terminated externally with SIGTERM after success marker.

Second run (with `-d int,unimp,guest_errors`) produced byte-identical trace and elapsed ~32,570,000 ns.

**Success marker reached:** `tyrne: all tasks complete` — YES.

**`-d int,unimp,guest_errors` event count:** **629 lines**, all `PL011 data written to disabled UART`.
No `Taking exception` events, no `unimp` events, no new fault classes.

**Boot-to-end elapsed:** 26,824,000 ns (run 1) / 32,570,000 ns (run 2). Both within the expected QEMU-TCG debug-build range of ~27–33 ms on this host (Apple Silicon under Rosetta/TCG).

**QEMU invocation used:**
```sh
qemu-system-aarch64 -M virt -cpu cortex-a72 -m 128M -smp 1 -nographic \
    -serial mon:stdio -kernel target/aarch64-unknown-none/debug/tyrne-bsp-qemu-virt
```

---

## Drift from documented claims

Claims compared against: `docs/roadmap/current.md` (the primary source of headline numbers at commit `288ddb2`), `docs/analysis/reports/2026-04-27-coverage-rerun.md`, and `.github/workflows/ci.yml` comment block.

### Host-test count

| Source | Claimed | Actual | Δ | Severity |
|---|---|---|---|---|
| `current.md` (T-019 banner, round-4 tip) | **259/259** | **260** | +1 | **Minor** |
| `current.md` (B3 closure banner) | 226 | (B3 state, not HEAD) | n/a — historical | Nit |
| `ci.yml` comment (`was 111` at pipeline birth) | 111 | (historical) | n/a — historical | Nit |

**Minor drift — 259 vs 260.** The `current.md` T-019 banner records `259/259` at round-4's commit (`95efd62`). HEAD (`288ddb2`) shows 260. The delta is +1 test. The banner note states "the misaligned-VA test rather than adding new ones; the distinctness assertion gained 2 sub-cases but those land inside an existing test" — however the actual executable test binary count is 260 at HEAD, not 259. This discrepancy is consistent with a post-round-4 commit (the `docs(readme)` commit `288ddb2`) either adding a test or the banner being written before a test was finalized. The difference is one test; it is not a regression (all pass). Severity: **Minor** — the claim is off by one in the positive direction.

### Coverage — workspace regions

| Source | Claimed | Actual | Δ | Severity |
|---|---|---|---|---|
| `current.md` (T-019 banner, implicit ≥96%) | ≥96% (T-011 gate) | **96.26%** | +0 pp net | Nit — consistent |
| `2026-04-27-coverage-rerun.md` post-fix observed | 96.37% workspace regions | 96.26% | −0.11 pp | **Minor** |

**Minor drift — 96.37% vs 96.26%.** The 2026-04-27 report's follow-up note recorded a post-fix tip of 96.37% workspace regions. HEAD shows 96.26%. The −0.11 pp delta is consistent with T-019's `task_loader.rs` landing at 93.83% regions (new code with some rollback paths uncovered) pulling the workspace total slightly below the post-T-011 high-water mark. Both T-011 acceptance criteria remain met (≥96% workspace regions: 96.26% ≥ 96.00%; sched ≥90%: 92.41% ≥ 90.00%). Severity: **Minor** — the workspace floor is still above the T-011 gate; the drop reflects expected code growth, not regression.

### Coverage — `hal/src/mmu/mod.rs`

| Source | Claimed | Actual | Δ | Severity |
|---|---|---|---|---|
| `2026-04-27-coverage-rerun.md` | 40.82% (`hal/src/mmu.rs`) | **67.74%** (`hal/src/mmu/mod.rs`) | +26.92 pp | Nit — improvement |

The file was previously a flat `hal/src/mmu.rs`; it was restructured into `hal/src/mmu/mod.rs` + `hal/src/mmu/vmsav8.rs` during the T-016 VMSAv8 encoder work. The net coverage improved substantially (40.82% → 67.74% on `mod.rs`; `vmsav8.rs` is a new file at 98.36%). The 2026-04-27 report's "Remaining gaps" note routing this to B2 is now partially resolved. No negative drift here; the old report is a historical baseline.

### QEMU smoke — serial trace

| Source | Claimed | Actual | Match? | Severity |
|---|---|---|---|---|
| `current.md` (T-019 banner) | `tyrne: image loaded (entry = 0x800000; sp = 0x802000; image bytes 8; stack bytes 4096; AS cap = idx 1)` | Byte-identical | YES | — |
| `current.md` (T-016 banner) | `tyrne: mmu activated` (inserted after hello, before timer) | Present in correct position | YES | — |
| `current.md` (T-018 banner) | `tyrne: address-space-arena ready (1 / 8 slots used; bootstrap AS root = 0x40095000)` | Byte-identical | YES | — |
| All banners | `tyrne: all tasks complete` | Present | YES | — |

**No drift** on the serial trace. All claimed banner lines appear, in the claimed order, at HEAD.

### QEMU smoke — `-d int,unimp,guest_errors` event count

| Source | Claimed | Actual | Δ | Severity |
|---|---|---|---|---|
| `current.md` (T-019 banner) | **629** PL011-disabled-UART warnings | **629** | 0 | — |
| `current.md` (T-016 banner, B2 baseline) | 379 warnings | 629 (HEAD) | +250 | Nit — expected growth |

The 629 count at HEAD matches the T-019 banner claim exactly. The +250 delta from the T-016 baseline (379) is expected: subsequent tasks (T-017 PMM print, T-018 AS-arena print, T-019 image-loaded print) added new UART output lines, each of which generates one `LOG_GUEST_ERROR` per byte written to the PL011 with `UARTCR.UARTEN=0`. This is a pre-existing QEMU quirk tracked in the project (not a kernel defect). Severity: **Nit** — the count matches the most recent claim (T-019 banner); the delta from the T-016 baseline is intended.

### Miri — integer-to-pointer cast warnings

| Source | Claimed | Actual | Severity |
|---|---|---|---|
| `current.md` (no mention of miri warnings) | Clean miri pass implied | 260/260 pass with advisory warnings | **Minor** |

The miri run passes (zero test failures, zero UB detected) but emits **advisory integer-to-pointer cast warnings** in `pmm.rs` (test helpers and `alloc_frame`), `task_loader.rs` (test helper), and `mm/mod.rs` (`phys_frame_kernel_ptr`). These warnings are not errors under the default `MIRIFLAGS` configuration. They reflect the identity-mapped `PhysAddr as *mut u8` pattern that is documented in UNSAFE-2026-0025 and UNSAFE-2026-0026. The `current.md` and existing miri report (`2026-04-23-miri-validation.md`) do not mention these warnings, implying they appeared with T-017 (PMM) or T-019 (task loader) code that was added after the baseline miri report. Severity: **Minor** — the warnings are advisory and the underlying patterns are already under audit control; however they are unmentioned in any existing report and warrant explicit acknowledgement. Strict-provenance migration is a forward-looking cleanup item.

### Summary of drift

| # | Finding | Severity |
|---|---|---|
| D1 | Claimed test count 259/259 (current.md T-019 banner) vs actual 260/260 | Minor |
| D2 | Workspace region coverage 96.37% (2026-04-27 follow-up) vs actual 96.26% — T-019 code growth | Minor |
| D3 | Miri integer-to-pointer cast warnings in pmm + task_loader + phys_frame_kernel_ptr not mentioned in any prior report | Minor |
| D4 | `hal/src/mmu/mod.rs` coverage 40.82% baseline — now 67.74% (positive drift, file restructured) | Nit |
| D5 | Guest-error count 629 vs T-016 baseline 379 (expected growth, matches T-019 claim exactly) | Nit |

No Blocker-severity drift found. All three hard CI gates (lint-and-host-test, kernel-build, miri) and the informational coverage gate pass cleanly. QEMU smoke reaches the success marker with the expected serial trace.
