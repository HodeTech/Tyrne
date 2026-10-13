# Host coverage rerun — 2026-10-13 / T-049

- **Executed source:** clean `development` at `0ab0ba427ae97d5233afd01dfe7205b1ae8bc0c3`, before the Step-5 archive/report edits. This is the tested source, not a claim that later documentation changes already exist in that commit.
- **Date:** 2026-10-13, Europe/Istanbul. Retained timestamps are UTC (2026-10-12 23:xx), the same local execution date.
- **Actual command exit:** `0`; tracked/untracked tree clean before and after; source HEAD unchanged.
- **Started / finished UTC:** `2026-10-12T23:29:57.450170+00:00` / `2026-10-12T23:29:59.775303+00:00`.
- **Host:** Darwin 27.0.0 / arm64, Rust host `aarch64-apple-darwin`; Python 3.9.6 captured the process.
- **Toolchain:** repository override `nightly-2026-01-15`; rustc `1.94.0-nightly`, commit `86a49fd71fecd25b0fd20247db0ba95eeceaba28` (2026-01-14), rustc LLVM 21.1.8; cargo `1.94.0-nightly (6d1bd93c4 2026-01-10)`.
- **Raw output:** [coverage.log](2026-10-13-t049-review-evidence/coverage.log), SHA-256 `a22757c1f702bbf7d0b3a376ef1ce7e0785427833c63c2599a9695cb7d657a14`; [process/tool/environment metadata](2026-10-13-t049-review-evidence/coverage.json).
- **Review state:** [Both fresh primary/complementary rounds](../reviews/code-reviews/2026-10-13-t049-review-corpus-reconciliation.md) complete at `aa37e2c`; C01 corrected and independently verified. T-049 is In Review; no Done, hosted CI or main-merge claim.

## Invocation

```bash
cargo llvm-cov --workspace --exclude tyrne-bsp-qemu-virt --exclude tyrne-user --exclude tyrne-userland-hello --summary-only
```

The local runner was `cargo-llvm-cov 0.9.0`, already installed before this task. The repository command uses the repository-pinned default Rust toolchain. CI pins `cargo-llvm-cov@0.6.16`; this local report does not claim that hosted version ran or that the versions produce identical denominators. No CI/tool pin or shipping dependency changed here.

## Actual result

The three included host suites pass **363 unit tests**: HAL 46, kernel 259 and test-HAL 58. This command did not request doc-test coverage; no doc-test execution is inferred from its output. BSP, `tyrne-user` and `tyrne-userland-hello` are explicitly excluded.

| Measure | Total | Missed | Covered / executed | Percent |
|---------|------:|-------:|-------------------:|--------:|
| Regions | 14,039 | 518 | 13,521 | 96.31% |
| Functions | 786 | 54 | 732 | 93.13% |
| Lines | 8,346 | 345 | 8,001 | 95.87% |

The retained table reports 28 source files. Branch columns are zero with percentage `-`: branch coverage was not measured, and this is not a 100% branch-coverage claim. Lower included measurements such as scheduler functions (73.33%) and loader lines (93.74%) remain visible in the full output; the aggregate is not proof that every path is exercised.

## Coverage table

The table below is copied verbatim from this command's output; numerators and percentages above were checked against TOTAL.

```text
Filename                              Regions    Missed Regions     Cover   Functions  Missed Functions  Executed       Lines      Missed Lines     Cover    Branches   Missed Branches     Cover
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
hal/src/console.rs                          6                 0   100.00%           1                 0   100.00%           4                 0   100.00%           0                 0         -
hal/src/cpu.rs                             11                 0   100.00%           2                 0   100.00%           7                 0   100.00%           0                 0         -
hal/src/mmu/mod.rs                         76                16    78.95%          20                 4    80.00%          64                12    81.25%           0                 0         -
hal/src/mmu/vmsav8.rs                     420                 2    99.52%          26                 0   100.00%         279                 0   100.00%           0                 0         -
hal/src/timer.rs                          206                 0   100.00%          28                 0   100.00%         143                 0   100.00%           0                 0         -
kernel/src/cap/mod.rs                      67                 1    98.51%           9                 0   100.00%          54                 1    98.15%           0                 0         -
kernel/src/cap/rights.rs                  120                 0   100.00%          18                 0   100.00%          75                 0   100.00%           0                 0         -
kernel/src/cap/table.rs                  1462                39    97.33%          63                 1    98.41%         632                25    96.04%           0                 0         -
kernel/src/ipc/mod.rs                    1448                21    98.55%          54                 0   100.00%         765                12    98.43%           0                 0         -
kernel/src/mm/address_space.rs           1046                35    96.65%          46                 1    97.83%         561                20    96.43%           0                 0         -
kernel/src/mm/mod.rs                       27                 0   100.00%           6                 0   100.00%          18                 0   100.00%           0                 0         -
kernel/src/mm/pmm.rs                     1068                 7    99.34%          39                 0   100.00%         542                 3    99.45%           0                 0         -
kernel/src/obj/arena.rs                   262                 9    96.56%          20                 1    95.00%         130                 6    95.38%           0                 0         -
kernel/src/obj/endpoint.rs                 64                 0   100.00%           9                 0   100.00%          41                 0   100.00%           0                 0         -
kernel/src/obj/notification.rs            109                 4    96.33%          12                 1    91.67%          65                 3    95.38%           0                 0         -
kernel/src/obj/task.rs                    103                 0   100.00%          13                 0   100.00%          68                 0   100.00%           0                 0         -
kernel/src/obj/task_loader.rs            1819               104    94.28%          66                 4    93.94%        1135                71    93.74%           0                 0         -
kernel/src/sched/mod.rs                  2073               159    92.33%         105                28    73.33%        1430               115    91.96%           0                 0         -
kernel/src/syscall/abi.rs                 243                 0   100.00%          25                 0   100.00%         169                 0   100.00%           0                 0         -
kernel/src/syscall/dispatch.rs           1098                50    95.45%          33                 0   100.00%         723                25    96.54%           0                 0         -
kernel/src/syscall/error.rs               125                 0   100.00%          10                 0   100.00%          89                 0   100.00%           0                 0         -
kernel/src/syscall/user_access.rs         493                11    97.77%          21                 0   100.00%         277                 3    98.92%           0                 0         -
test-hal/src/console.rs                    57                 0   100.00%           8                 0   100.00%          39                 0   100.00%           0                 0         -
test-hal/src/context_switch.rs            182                 2    98.90%          14                 1    92.86%         113                 2    98.23%           0                 0         -
test-hal/src/cpu.rs                       159                 0   100.00%          20                 0   100.00%         102                 0   100.00%           0                 0         -
test-hal/src/irq_controller.rs            195                 3    98.46%          21                 1    95.24%         104                 3    97.12%           0                 0         -
test-hal/src/mmu.rs                       964                55    94.29%          79                12    84.81%         629                44    93.00%           0                 0         -
test-hal/src/timer.rs                     136                 0   100.00%          18                 0   100.00%          88                 0   100.00%           0                 0         -
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
TOTAL                                   14039               518    96.31%         786                54    93.13%        8346               345    95.87%           0                 0         -
```

## Scope and historical comparison

This is host instrumentation, including test-side source regions, not bare-metal/QEMU/assembly, userland, branch or security coverage. The command reports `cfg(coverage)` and `cfg(coverage_nightly)` in the raw output. Local source/tool/profile scope controls the denominator; no architectural correctness or no-regression verdict follows from the percentage alone.

The [2026-04-23 baseline](2026-04-23-coverage-baseline.md) and [2026-04-27 rerun](2026-04-27-coverage-rerun.md) preserve their historical methodology and numbers. They covered an earlier source and used a broader workspace exclusion list. Neither a direct percentage trend nor an improvement/regression is inferred across those different denominators and tool versions. Fresh Miri results are recorded independently in [the companion report](2026-10-13-t049-miri-validation.md).
