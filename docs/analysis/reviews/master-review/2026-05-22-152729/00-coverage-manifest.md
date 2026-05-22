# Master review — coverage manifest

- **Run id:** `2026-05-22-152729`
- **Commit (HEAD):** `288ddb2be98e4a679cb5a07ba8a70e52b82c21a7`
- **In-scope files:** 251
- **In-scope lines:** 45757
- **Out of scope:** `docs/analysis/reviews/master-review/**` (this review's own output); `docs/analysis/technical-analysis/**` (untracked / gitignored, per maintainer).

Every tracked file below is owned by exactly one Wave-2 track and was read **in full**.
**Status: COMPLETE — all 251 in-scope files reviewed.** Each box below is checked; the
authoritative per-file evidence is the `## Coverage checklist` section inside each
`tracks/<ID>.md`, and the consolidation independently confirmed 251/251 (see
`consolidated.md` → Coverage appendix).

## Track summary

| Track | Files | Lines |
|-------|------:|------:|
| C1-kernel-cap | 3 | 1577 |
| C2-kernel-mm | 3 | 2744 |
| C3-kernel-ipc-obj | 6 | 2278 |
| C4-kernel-task-loader | 2 | 2328 |
| C5-kernel-sched | 1 | 2652 |
| C6-hal | 8 | 1961 |
| C7-bsp | 12 | 3855 |
| C8-test-hal | 7 | 1236 |
| C9-build-infra | 12 | 1111 |
| D1-architecture | 10 | 2220 |
| D2a-adr-early | 20 | 3063 |
| D2b-adr-late | 13 | 2377 |
| D3-standards | 15 | 2178 |
| D4-roadmap-tasks | 43 | 4067 |
| D5a-meta-core | 30 | 2716 |
| D5b-audits-reports | 8 | 1235 |
| D5c-existing-reviews | 58 | 8159 |
| **TOTAL** | **251** | **45757** |

## Files by track


### C1-kernel-cap

- [x] `kernel/src/cap/table.rs` (1188 lines)
- [x] `kernel/src/cap/mod.rs` (192 lines)
- [x] `kernel/src/cap/rights.rs` (197 lines)

### C2-kernel-mm

- [x] `kernel/src/mm/pmm.rs` (1195 lines)
- [x] `kernel/src/mm/address_space.rs` (1380 lines)
- [x] `kernel/src/mm/mod.rs` (169 lines)

### C3-kernel-ipc-obj

- [x] `kernel/src/obj/mod.rs` (102 lines)
- [x] `kernel/src/obj/endpoint.rs` (115 lines)
- [x] `kernel/src/ipc/mod.rs` (1425 lines)
- [x] `kernel/src/obj/notification.rs` (156 lines)
- [x] `kernel/src/obj/task.rs` (188 lines)
- [x] `kernel/src/obj/arena.rs` (292 lines)

### C4-kernel-task-loader

- [x] `kernel/src/obj/task_loader.rs` (2271 lines)
- [x] `kernel/src/lib.rs` (57 lines)

### C5-kernel-sched

- [x] `kernel/src/sched/mod.rs` (2652 lines)

### C6-hal

- [x] `hal/src/cpu.rs` (194 lines)
- [x] `hal/src/mmu/mod.rs` (438 lines)
- [x] `hal/src/timer.rs` (484 lines)
- [x] `hal/src/mmu/vmsav8.rs` (588 lines)
- [x] `hal/src/irq_controller.rs` (59 lines)
- [x] `hal/src/lib.rs` (62 lines)
- [x] `hal/src/console.rs` (66 lines)
- [x] `hal/src/context_switch.rs` (70 lines)

### C7-bsp

- [x] `bsp-qemu-virt/src/main.rs` (1308 lines)
- [x] `bsp-qemu-virt/src/boot.s` (136 lines)
- [x] `bsp-qemu-virt/build.rs` (17 lines)
- [x] `bsp-qemu-virt/Cargo.toml` (20 lines)
- [x] `bsp-qemu-virt/src/vectors.s` (204 lines)
- [x] `bsp-qemu-virt/src/mmu_bootstrap.rs` (256 lines)
- [x] `bsp-qemu-virt/src/exceptions.rs` (272 lines)
- [x] `bsp-qemu-virt/src/gic.rs` (385 lines)
- [x] `bsp-qemu-virt/src/mmu.rs` (521 lines)
- [x] `bsp-qemu-virt/src/cpu.rs` (566 lines)
- [x] `bsp-qemu-virt/src/console.rs` (81 lines)
- [x] `bsp-qemu-virt/linker.ld` (89 lines)

### C8-test-hal

- [x] `test-hal/Cargo.toml` (17 lines)
- [x] `test-hal/src/timer.rs` (175 lines)
- [x] `test-hal/src/irq_controller.rs` (189 lines)
- [x] `test-hal/src/cpu.rs` (190 lines)
- [x] `test-hal/src/lib.rs` (32 lines)
- [x] `test-hal/src/mmu.rs` (539 lines)
- [x] `test-hal/src/console.rs` (94 lines)

### C9-build-infra

- [x] `clippy.toml` (14 lines)
- [x] `hal/Cargo.toml` (14 lines)
- [x] `rustfmt.toml` (15 lines)
- [x] `.github/workflows/ci.yml` (172 lines)
- [x] `kernel/Cargo.toml` (20 lines)
- [x] `rust-toolchain.toml` (21 lines)
- [x] `Cargo.lock` (30 lines)
- [x] `.cargo/config.toml` (45 lines)
- [x] `tools/perf-harness.sh` (585 lines)
- [x] `.gitignore` (63 lines)
- [x] `Cargo.toml` (64 lines)
- [x] `tools/run-qemu.sh` (68 lines)

### D1-architecture

- [x] `docs/architecture/task-loader.md` (170 lines)
- [x] `docs/architecture/ipc.md` (178 lines)
- [x] `docs/architecture/scheduler.md` (178 lines)
- [x] `docs/architecture/boot.md` (209 lines)
- [x] `docs/architecture/overview.md` (249 lines)
- [x] `docs/architecture/exceptions.md` (259 lines)
- [x] `docs/architecture/memory-management.md` (270 lines)
- [x] `docs/architecture/hal.md` (326 lines)
- [x] `docs/architecture/README.md` (33 lines)
- [x] `docs/architecture/security-model.md` (348 lines)

### D2a-adr-early

- [x] `docs/decisions/0002-implementation-language-rust.md` (110 lines)
- [x] `docs/decisions/0001-microkernel-architecture.md` (114 lines)
- [x] `docs/decisions/0007-console-trait.md` (115 lines)
- [x] `docs/decisions/template.md` (121 lines)
- [x] `docs/decisions/0004-target-platforms.md` (123 lines)
- [x] `docs/decisions/0006-workspace-layout.md` (143 lines)
- [x] `docs/decisions/0011-irq-controller-trait.md` (145 lines)
- [x] `docs/decisions/0010-timer-trait.md` (161 lines)
- [x] `docs/decisions/0012-boot-flow-qemu-virt.md` (164 lines)
- [x] `docs/decisions/0008-cpu-trait.md` (165 lines)
- [x] `docs/decisions/0015-ai-integration-stance.md` (170 lines)
- [x] `docs/decisions/0013-roadmap-and-planning.md` (219 lines)
- [x] `docs/decisions/0017-ipc-primitive-set.md` (225 lines)
- [x] `docs/decisions/0009-mmu-trait.md` (237 lines)
- [x] `docs/decisions/0016-kernel-object-storage.md` (239 lines)
- [x] `docs/decisions/0014-capability-representation.md` (263 lines)
- [x] `docs/decisions/README.md` (70 lines)
- [x] `docs/decisions/0005-documentation-language-english.md` (83 lines)
- [x] `docs/decisions/0003-license-apache-2.md` (98 lines)
- [x] `docs/decisions/0018-badge-scheme-and-reply-recv-deferral.md` (98 lines)

### D2b-adr-late

- [x] `docs/decisions/0024-el-drop-policy.md` (119 lines)
- [x] `docs/decisions/0025-adr-governance-amendments.md` (140 lines)
- [x] `docs/decisions/0021-raw-pointer-scheduler-ipc-bridge.md` (153 lines)
- [x] `docs/decisions/0032-endpoint-rollback-and-cancel-recv.md` (154 lines)
- [x] `docs/decisions/0029-initial-userspace-image-format.md` (159 lines)
- [x] `docs/decisions/0026-idle-dispatch-fallback.md` (181 lines)
- [x] `docs/decisions/0022-idle-task-and-typed-scheduler-deadlock.md` (193 lines)
- [x] `docs/decisions/0028-address-space-data-structure.md` (200 lines)
- [x] `docs/decisions/0035-physical-memory-manager.md` (208 lines)
- [x] `docs/decisions/0019-scheduler-shape.md` (222 lines)
- [x] `docs/decisions/0027-kernel-virtual-memory-layout.md` (230 lines)
- [x] `docs/decisions/0020-cpu-trait-v2-context-switch.md` (326 lines)
- [x] `docs/decisions/0023-cross-table-capability-revocation-policy.md` (92 lines)

### D3-standards

- [x] `docs/standards/localization.md` (100 lines)
- [x] `docs/standards/architectural-principles.md` (130 lines)
- [x] `docs/standards/code-review.md` (135 lines)
- [x] `docs/standards/security-review.md` (135 lines)
- [x] `docs/standards/testing.md` (141 lines)
- [x] `docs/standards/commit-style.md` (142 lines)
- [x] `docs/standards/logging-and-observability.md` (149 lines)
- [x] `docs/standards/release.md` (152 lines)
- [x] `docs/standards/code-style.md` (154 lines)
- [x] `docs/standards/error-handling.md` (176 lines)
- [x] `docs/standards/unsafe-policy.md` (191 lines)
- [x] `docs/standards/infrastructure.md` (210 lines)
- [x] `docs/standards/bsp-boot-checklist.md` (224 lines)
- [x] `docs/standards/README.md` (48 lines)
- [x] `docs/standards/documentation-style.md` (91 lines)

### D4-roadmap-tasks

- [x] `docs/analysis/tasks/phase-a/T-002-kernel-object-storage.md` (102 lines)
- [x] `docs/analysis/tasks/phase-a/T-005-two-task-ipc-demo.md` (106 lines)
- [x] `docs/analysis/tasks/phase-a/T-001-capability-table-foundation.md` (109 lines)
- [x] `docs/analysis/tasks/phase-c/README.md` (11 lines)
- [x] `docs/analysis/tasks/phase-d/README.md` (11 lines)
- [x] `docs/analysis/tasks/phase-e/README.md` (11 lines)
- [x] `docs/analysis/tasks/phase-f/README.md` (11 lines)
- [x] `docs/analysis/tasks/phase-g/README.md` (11 lines)
- [x] `docs/analysis/tasks/phase-h/README.md` (11 lines)
- [x] `docs/analysis/tasks/phase-i/README.md` (11 lines)
- [x] `docs/analysis/tasks/phase-b/T-011-missing-tests-bundle.md` (111 lines)
- [x] `docs/analysis/tasks/phase-b/T-009-timer-init-cntvct.md` (112 lines)
- [x] `docs/analysis/tasks/phase-b/T-012-exception-and-irq-infrastructure.md` (113 lines)
- [x] `docs/analysis/tasks/phase-b/T-006-raw-pointer-scheduler-api.md` (114 lines)
- [x] `docs/analysis/tasks/phase-b/T-015-endpoint-rollback-cancel-recv.md` (114 lines)
- [x] `docs/roadmap/phases/phase-j.md` (115 lines)
- [x] `docs/roadmap/phases/phase-e.md` (120 lines)
- [x] `docs/analysis/tasks/phase-b/T-007-idle-task-typed-deadlock.md` (121 lines)
- [x] `docs/analysis/tasks/phase-b/T-008-architecture-docs.md` (121 lines)
- [x] `docs/roadmap/phases/phase-c.md` (128 lines)
- [x] `docs/analysis/tasks/phase-j/README.md` (13 lines)
- [x] `docs/roadmap/phases/phase-g.md` (130 lines)
- [x] `docs/analysis/tasks/phase-b/T-014-idle-dispatch-fallback.md` (134 lines)
- [x] `docs/analysis/tasks/phase-b/T-019-task-loader.md` (138 lines)
- [x] `docs/analysis/tasks/phase-a/README.md` (15 lines)
- [x] `docs/analysis/tasks/phase-b/T-016-mmu-activation.md` (163 lines)
- [x] `docs/analysis/tasks/phase-b/T-017-physical-memory-manager.md` (175 lines)
- [x] `docs/roadmap/phases/phase-d.md` (175 lines)
- [x] `docs/analysis/tasks/phase-b/T-018-address-space-kernel-object.md` (177 lines)
- [x] `docs/roadmap/phases/phase-a.md` (208 lines)
- [x] `docs/analysis/tasks/phase-b/README.md` (21 lines)
- [x] `docs/roadmap/phases/phase-b.md` (312 lines)
- [x] `docs/roadmap/README.md` (46 lines)
- [x] `docs/analysis/tasks/README.md` (51 lines)
- [x] `docs/roadmap/phases/README.md` (55 lines)
- [x] `docs/analysis/tasks/TEMPLATE.md` (65 lines)
- [x] `docs/roadmap/phases/phase-h.md` (75 lines)
- [x] `docs/roadmap/phases/phase-i.md` (77 lines)
- [x] `docs/analysis/tasks/phase-b/T-013-el-drop-to-el1.md` (91 lines)
- [x] `docs/roadmap/phases/phase-f.md` (93 lines)
- [x] `docs/analysis/tasks/phase-a/T-004-cooperative-scheduler.md` (95 lines)
- [x] `docs/analysis/tasks/phase-a/T-003-ipc-primitives.md` (97 lines)
- [x] `docs/roadmap/current.md` (98 lines)

### D5a-meta-core

- [x] `.agents/skills/justify-unsafe/SKILL.md` (102 lines)
- [x] `docs/guides/two-task-demo.md` (102 lines)
- [x] `.agents/skills/add-dependency/SKILL.md` (104 lines)
- [x] `.agents/skills/write-guide/SKILL.md` (111 lines)
- [x] `.agents/skills/write-architecture-doc/SKILL.md` (130 lines)
- [x] `docs/guides/run-under-qemu.md` (142 lines)
- [x] `.agents/skills/conduct-approval-review/SKILL.md` (147 lines)
- [x] `LICENSE` (201 lines)
- [x] `.agents/skills/add-bsp/SKILL.md` (213 lines)
- [x] `AGENTS.md` (23 lines)
- [x] `README.md` (232 lines)
- [x] `docs/guides/README.md` (26 lines)
- [x] `docs/README.md` (28 lines)
- [x] `CONTRIBUTING.md` (33 lines)
- [x] `SECURITY.md` (33 lines)
- [x] `docs/analysis/README.md` (49 lines)
- [x] `CLAUDE.md` (60 lines)
- [x] `.agents/skills/update-glossary/SKILL.md` (66 lines)
- [x] `NOTICE` (7 lines)
- [x] `.agents/skills/supersede-adr/SKILL.md` (74 lines)
- [x] `.agents/skills/propose-standard-change/SKILL.md` (76 lines)
- [x] `docs/guides/ci.md` (77 lines)
- [x] `.agents/skills/perform-security-review/SKILL.md` (79 lines)
- [x] `.agents/skills/sync-adr-index/SKILL.md` (80 lines)
- [x] `.agents/skills/conduct-review/SKILL.md` (81 lines)
- [x] `.agents/skills/perform-code-review/SKILL.md` (82 lines)
- [x] `.agents/skills/README.md` (88 lines)
- [x] `.agents/skills/start-task/SKILL.md` (88 lines)
- [x] `.agents/skills/write-adr/SKILL.md` (91 lines)
- [x] `docs/glossary.md` (91 lines)

### D5b-audits-reports

- [x] `docs/analysis/reports/2026-04-27-coverage-rerun.md` (110 lines)
- [x] `docs/audits/unsafe-log.md` (609 lines)
- [x] `docs/analysis/reports/2026-04-23-miri-validation.md` (62 lines)
- [x] `docs/analysis/reports/2026-04-23-coverage-baseline.md` (76 lines)
- [x] `docs/analysis/reports/perf-baseline-2026-05-08-post-pr-19-pre-adr-0027.md` (89 lines)
- [x] `docs/analysis/reports/perf-baseline-2026-05-09-B2-closure.md` (96 lines)
- [x] `docs/analysis/reports/perf-baseline-2026-05-14-B3-closure.md` (96 lines)
- [x] `docs/analysis/reports/perf-baseline-2026-05-08-post-t-016-mmu-activated.md` (97 lines)

### D5c-existing-reviews

- [x] `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-e-docs.md` (100 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-h-audit.md` (103 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-08-pr-19-20-21-multi-axis-review/track-3-pr-20-governance.md` (103 lines)
- [x] `docs/analysis/reviews/security-reviews/2026-05-14-B3-closure.md` (105 lines)
- [x] `docs/analysis/reviews/performance-optimization-reviews/2026-04-21-A6-baseline.md` (106 lines)
- [x] `docs/analysis/reviews/security-reviews/2026-05-07-B1-closure.md` (113 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-08-pr-19-20-21-multi-axis-review/track-2-pr-20-design.md` (114 lines)
- [x] `docs/analysis/reviews/business-reviews/2026-04-21-A6-completion.md` (115 lines)
- [x] `docs/analysis/reviews/security-reviews/2026-05-09-B2-closure.md` (115 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-a-kernel.md` (116 lines)
- [x] `docs/analysis/reviews/security-reviews/2026-04-27-B0-closure.md` (118 lines)
- [x] `docs/analysis/reviews/business-reviews/2026-05-06-B1-smoke-regression.md` (129 lines)
- [x] `docs/analysis/reviews/business-reviews/master-plan.md` (137 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review.md` (141 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-08-pr-19-20-21-multi-axis-review.md` (144 lines)
- [x] `docs/analysis/reviews/security-reviews/2026-04-28-B1-closure.md` (145 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-g-process.md` (146 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-d-perf.md` (147 lines)
- [x] `docs/analysis/reviews/code-reviews/master-plan.md` (149 lines)
- [x] `docs/analysis/reviews/business-reviews/2026-04-27-T-009-mini-retro.md` (150 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-04-21-tyrne-to-phase-a.md` (155 lines)
- [x] `docs/analysis/reviews/performance-optimization-reviews/2026-05-07-B1-closure.md` (155 lines)
- [x] `docs/analysis/reviews/performance-optimization-reviews/master-plan.md` (155 lines)
- [x] `docs/analysis/reviews/business-reviews/2026-05-07-B1-closure.md` (158 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-j-hygiene.md` (160 lines)
- [x] `docs/analysis/reviews/business-reviews/2026-04-27-B0-closure.md` (165 lines)
- [x] `docs/analysis/reviews/security-reviews/2026-04-21-tyrne-to-phase-a.md` (168 lines)
- [x] `docs/analysis/reviews/business-reviews/2026-04-28-B1-closure.md` (170 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-i-integration.md` (171 lines)
- [x] `docs/analysis/reviews/business-reviews/2026-05-09-B2-closure.md` (178 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-d-performance.md` (179 lines)
- [x] `docs/analysis/reviews/security-reviews/master-plan.md` (184 lines)
- [x] `docs/analysis/reviews/performance-optimization-reviews/2026-05-09-B2-closure.md` (186 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-c-security.md` (187 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-f-tests.md` (190 lines)
- [x] `docs/analysis/reviews/performance-optimization-reviews/2026-05-14-B3-closure.md` (206 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-08-pr-19-20-21-multi-axis-review/track-4-pr-21-perf-harness.md` (208 lines)
- [x] `docs/analysis/reviews/performance-optimization-reviews/2026-04-28-B1-closure.md` (208 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-f-tests.md` (215 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-e-docs.md` (228 lines)
- [x] `docs/analysis/reviews/business-reviews/2026-05-14-B3-closure.md` (231 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-c-security.md` (235 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-06-full-tree-comprehensive.md` (261 lines)
- [x] `docs/analysis/reviews/code-reviews/README.md` (28 lines)
- [x] `docs/analysis/reviews/performance-optimization-reviews/README.md` (31 lines)
- [x] `docs/analysis/reviews/business-reviews/README.md` (36 lines)
- [x] `docs/analysis/reviews/security-reviews/README.md` (39 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-06-full-tree-comprehensive-review-plan.md` (403 lines)
- [x] `docs/analysis/reviews/README.md` (45 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-h-infra.md` (69 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-b-hal.md` (72 lines)
- [x] `docs/analysis/reviews/business-reviews/2026-04-22-T-006-mini-retro.md` (74 lines)
- [x] `docs/analysis/reviews/business-reviews/2026-04-21-A2-completion.md` (77 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-08-pr-19-20-21-multi-axis-review/track-1-pr-19-mechanical.md` (83 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-07-pr-12-to-17-multi-axis-review/track-b-hal-bsp.md` (86 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-g-bsp.md` (87 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/track-a-kernel.md` (89 lines)
- [x] `docs/analysis/reviews/code-reviews/2026-05-06-full-tree/00-preflight.md` (91 lines)
