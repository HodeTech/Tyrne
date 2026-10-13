# Miri validation — 2026-10-13 / T-049

- **Executed source:** clean `development` at `0ab0ba427ae97d5233afd01dfe7205b1ae8bc0c3`, before the Step-5 archive/report edits. This is the tested source, not a claim that later documentation changes already exist in that commit.
- **Date:** 2026-10-13, Europe/Istanbul. Retained timestamps are UTC (2026-10-12 23:xx), the same local execution date.
- **Actual command exit:** `0`; tracked/untracked tree clean before and after; source HEAD unchanged.
- **Started / finished UTC:** `2026-10-12T23:29:24.354905+00:00` / `2026-10-12T23:29:49.830726+00:00`.
- **Host:** Darwin 27.0.0 / arm64, Rust host `aarch64-apple-darwin`; Python 3.9.6 captured the process.
- **Toolchain:** repository override `nightly-2026-01-15`; rustc `1.94.0-nightly`, commit `86a49fd71fecd25b0fd20247db0ba95eeceaba28` (2026-01-14), rustc LLVM 21.1.8; cargo `1.94.0-nightly (6d1bd93c4 2026-01-10)`.
- **Raw output:** [miri.log](2026-10-13-t049-review-evidence/miri.log), SHA-256 `1ecc45d89c2cdc6caf8f0dd51af791c8fbd56a6a7fe90fc7c5e99c9f99c77d67`; [process/tool/environment metadata](2026-10-13-t049-review-evidence/miri.json).
- **Review state:** [Both fresh primary/complementary rounds](../reviews/code-reviews/2026-10-13-t049-review-corpus-reconciliation.md) complete at `aa37e2c`; C01 corrected and independently verified. T-049 is In Review; no Done, hosted CI or main-merge claim.

## Invocation

```bash
cargo +nightly-2026-01-15 miri test --workspace --exclude tyrne-bsp-qemu-virt
```

Miri version is `0.1.0 (86a49fd71f 2026-01-14)`. Only `tyrne-bsp-qemu-virt` is excluded; both userland crates remain in the workspace invocation and each runs zero host unit tests. `MIRIFLAGS` and the other recorded compile-environment overrides were unset.

## Actual result

| Suite | Passed | Failed | Ignored |
|-------|-------:|-------:|--------:|
| HAL unit tests | 46 | 0 | 0 |
| Kernel unit tests | 259 | 0 | 0 |
| Test-HAL unit tests | 58 | 0 | 0 |
| User / hello host unit tests | 0 | 0 | 0 |
| Test-HAL doc-tests | 3 | 0 | 0 |
| HAL doc-tests | 0 | 0 | 2 |
| Kernel / user doc-tests | 0 | 0 | 0 |
| **Total** | **366** | **0** | **2** |

The command completed with no reported undefined-behavior error on the executed host paths. The raw output retains five notices that Miri ignores optimization levels; the other profile settings still apply. This is not a release optimization/codegen validation.

## Observed limits

Miri reported seven integer-to-pointer-cast warnings, at `kernel/src/mm/pmm.rs:965`, `:409`, `:1028`; `kernel/src/obj/task_loader.rs:1020`, `:1683`, `:2076`; and `kernel/src/mm/mod.rs:145`. The warning explains that exposed-provenance semantics can hide pointer bugs. No permissive flag suppressed the warning, and no strict-provenance run is claimed. These existing physical-address/test-backing conversions were not rewritten in this documentation task. Zero observed UB does not establish absence of all pointer bugs.

The two ignored HAL doc-tests are `FmtWriter` (`console.rs:51`) and `IrqGuard` (`cpu.rs:108`). Their ignored status is explicit; they are not included in the passing total. Pure Rust and fake-HAL paths are exercised; BSP boot assembly, MMIO, hardware page-table walks, real context switching and actual EL0 execution are outside this host run. The zero-test userland host crates do not validate AArch64 `svc` assembly. QEMU evidence remains separately source-bound under T-045/T-046.

## Historical reports

[2026-04-23 Miri validation](2026-04-23-miri-validation.md) and the Miri discussion in [2026-04-27 coverage rerun](2026-04-27-coverage-rerun.md) retain their original source, tool and test-count claims. This new artifact records the actual current invocation and results; it does not overwrite those historical observations or independently reproduce their old runs.
