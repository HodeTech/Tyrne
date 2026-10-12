# Contributing to Tyrne

Thank you for your interest. Tyrne is **pre-alpha**. Phase B closed on 2026-06-01: the kernel boots on QEMU `virt` aarch64 and runs its first EL0 userspace task through a capability-gated syscall boundary. Phase B.2 is the active consolidation bridge; Phase C is next and gated on B.2 completion. Implementation is active, but the codebase is not yet open for unsolicited code contributions — each subsystem is being grown along the phased roadmap, and changes outside the active milestone's scope force premature rewrites. Issues, references, and ADR review are very welcome (see below).

## What is useful right now

- Reading the [architecture documents](docs/architecture/) and [ADRs](docs/decisions/) and opening issues if something seems unclear, inconsistent with prior art, or contradicted by experience from related systems.
- Suggesting references — academic papers, existing systems (seL4, Hubris, Tock, Redox, Fuchsia/Zircon, Theseus, Drawbridge), talks, books — that would strengthen or refute specific design decisions.
- Reviewing the [standards](docs/standards/) in this repository and proposing improvements via issues.
- Catching typos, broken links, or unclear passages in the documentation; small PRs for those are welcome.

## What is not useful yet

- Pull requests against source code outside the active roadmap scope. Each subsystem follows the phased [roadmap](docs/roadmap/); check [current focus](docs/roadmap/current.md) before opening a non-trivial PR. Changes outside the active scope force premature rewrites and are usually not merged.
- Feature requests for subsystems that have not yet been designed. File those as discussion issues if you want to influence the design, not as feature requests.

## Implementation workflow

For work within the active scope:

1. Start from [current focus](docs/roadmap/current.md) and the relevant [task](docs/analysis/tasks/). Propose a plan for non-trivial work; record architectural or process decisions as [ADRs](docs/decisions/) before implementation.
2. Follow the [coding and documentation standards](docs/standards/) and [commit style](docs/standards/commit-style.md). Keep changes focused and include verification appropriate to the change.
3. Use the [CI guide](docs/guides/ci.md) for local checks and the required merge gates. Record an ordinary [code review](docs/standards/code-review.md) and a distinct [security review](docs/standards/security-review.md) when the change touches a security-sensitive area.
4. Follow the [release standard](docs/standards/release.md) for releases. Release preparation and review remain separate from routine implementation.

## Communication

- Architectural questions or ambiguities → issues in this repository.
- Security-relevant observations → see [SECURITY.md](SECURITY.md).

## Licensing of contributions

All contributions to Tyrne are licensed under the [Apache License, Version 2.0](LICENSE). By submitting a contribution, you agree that it may be redistributed under those terms, and you confirm that you have the right to submit it.
