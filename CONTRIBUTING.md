# Contributing to Tyrne

Thank you for your interest. Tyrne is **pre-alpha** and mid-way through Phase B: the Rust workspace exists, the kernel boots end-to-end on QEMU `virt` aarch64, and it runs a two-task IPC demo. Implementation is active, but the codebase is not yet open for unsolicited code contributions — each subsystem is being grown along the phased roadmap, and changes outside the active milestone's scope force premature rewrites. Issues, references, and ADR review are very welcome (see below).

## What is useful right now

- Reading the [architecture documents](docs/architecture/) and [ADRs](docs/decisions/) and opening issues if something seems unclear, inconsistent with prior art, or contradicted by experience from related systems.
- Suggesting references — academic papers, existing systems (seL4, Hubris, Tock, Redox, Fuchsia/Zircon, Theseus, Drawbridge), talks, books — that would strengthen or refute specific design decisions.
- Reviewing the [standards](docs/standards/) in this repository and proposing improvements via issues.
- Catching typos, broken links, or unclear passages in the documentation; small PRs for those are welcome.

## What is not useful yet

- Pull requests against source code outside the active milestone scope. The Rust workspace exists and the kernel boots end-to-end on QEMU virt (Phase A and milestones B0–B3 closed; B4 active), but each subsystem is being grown along the phased roadmap in [`docs/roadmap/`](docs/roadmap/); changes outside the current milestone's scope force premature rewrites and are usually not merged. Check [`docs/roadmap/current.md`](docs/roadmap/current.md) before opening a non-trivial PR.
- Feature requests for subsystems that have not yet been designed. File those as discussion issues if you want to influence the design, not as feature requests.

## When the project enters the implementation phase

This document will be expanded with:

- Branching strategy and release process.
- PR template and review expectations.
- CI gates (tests, clippy, rustfmt, capability auditing, `unsafe` auditing).
- Coding conventions (see [docs/standards/](docs/standards/)).

## Communication

- Architectural questions or ambiguities → issues in this repository.
- Security-relevant observations → see [SECURITY.md](SECURITY.md).

## Licensing of contributions

All contributions to Tyrne are licensed under the [Apache License, Version 2.0](LICENSE). By submitting a contribution, you agree that it may be redistributed under those terms, and you confirm that you have the right to submit it.
