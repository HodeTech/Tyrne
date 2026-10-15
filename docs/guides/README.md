# Guides

Task-oriented walkthroughs for contributors and users of Tyrne. Guides answer “how do I do X?” with prerequisites, steps and verification, linking architecture/ADRs for background.

## Status

Tyrne is pre-alpha. Phase B is complete; Phase B.2 consolidation/hardening is active, and Phase C opens after its exit gate. QEMU boots the cooperative IPC demo and the first EL0 task today. The available-guide inventory below contains all five substantive guide files; this README is their index, not a sixth guide.

## Available guides

| Guide | Audience | Status |
|-------|----------|--------|
| [run-under-qemu.md](run-under-qemu.md) | Build and boot the reference QEMU BSP. | Accepted guide; T-033 refresh merged in PR #48. |
| [ci.md](ci.md) | Understand pipeline jobs and their gates. | Accepted (2026-04-23, R6); Track B.2-1 refresh merged in PR #48. |
| [two-task-demo.md](two-task-demo.md) | Run and interpret the capability-checked IPC demo with EL0 interleaving. | Available; T-050 refresh In Review, both fresh rounds complete; maintainer review pending. |
| [first-userspace.md](first-userspace.md) | Build and inspect hello's EL0 entry, console return and exit. | Available; T-050 refresh In Review, both fresh rounds complete; maintainer review pending. |
| [review-evidence.md](review-evidence.md) | Recover exact archived evidence/original source and verify its integrity. | Available; ADR-0044 maintenance In Progress, both migration rounds pending. |

## Planned topics

The following filenames are ideas, not existing guides or scheduled milestones: `toolchain-setup.md`, `debug-with-gdb.md`, `port-to-new-board.md`, `write-a-driver.md` and `write-an-adr.md`. Use the available guides and [procedure library](../../.agents/skills/README.md) for current workflows.

## Conventions

- Every task guide has Goal, Prerequisites, numbered Steps, Verifying it worked, Troubleshooting and References.
- Commands use fenced `sh` blocks; output uses separate `text` blocks.
- Paths and output are verbatim; placeholders use `<angle-brackets>`.
- Status records distinguish availability, implementation review and maintainer acceptance.
