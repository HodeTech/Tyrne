# Master reviews

A **master review** is a whole-tree, end-to-end audit of the entire Tyrne
repository — every tracked source file and every in-scope document read in full,
then reviewed across all dimensions at once. It is heavier and broader than the
four event-triggered review types in the sibling directories
([business](../business-reviews/), [code](../code-reviews/),
[security](../security-reviews/),
[performance](../performance-optimization-reviews/)), which are each scoped to a
single milestone, PR, or concern. A master review is run **on demand** when the
maintainer wants a full, independent sweep of the project's current state.

## What it covers

Across all code and docs, in one pass:

- **Code** — correctness, optimization/performance, security surface,
  maintainability, refactor opportunities, API usability/ergonomics, test adequacy.
- **Documentation** — accuracy, appropriateness, clarity, level of detail,
  understandability, completeness, convention compliance (English-only,
  Mermaid-only, MADR for ADRs), and valid cross-references.
- **Contradictions** — code↔doc, doc↔doc, and code↔code, each verified on both
  sides with `file:line` citations.
- **Gates** — the quality gates and the QEMU smoke test are actually re-run and
  their output is attached as evidence, so documentation claims (test counts,
  coverage, boot success) are checked against reality.

It reuses the project's existing conventions: the severity scale
**Blocker > Major > Minor > Nit** (plus **Praise**), the
[code-review](../../../standards/code-review.md) and
[security-review](../../../standards/security-review.md) checklists, the
[unsafe policy](../../../standards/unsafe-policy.md), and the architectural
principles P1–P12.

## How it is run

The review is executed by many parallel agents in dependency-ordered waves:

1. **Wave 0 — coverage manifest.** Build a `file → owning-track` map from
   `git ls-files` so every in-scope file is accounted for (the no-exceptions
   guarantee).
2. **Wave 1 — gate reproduction.** Run `fmt`/`clippy`/`host-test`/`kernel-build`/
   `miri`/`coverage` + QEMU smoke; capture real output.
3. **Wave 2 — deep per-track read.** One agent per code/doc track reads its files
   in full and produces severity-tagged findings, a claims register, and a
   per-file coverage checklist.
4. **Wave 3 — cross-cutting synthesis.** Whole-tree security (8 axes), performance,
   unsafe-audit reconciliation, the three contradiction passes, and
   business-logic alignment.
5. **Wave 4 — consolidation.** All track outputs are de-duplicated into one
   canonical, severity-sorted report.

## Run layout

Each run lives in a timestamped directory `YYYY-MM-DD-HHMMSS/`:

```
master-review/
  README.md                  # this file
  <run-id>/
    consolidated.md          # headline deliverable: de-duplicated findings + follow-ups
    00-coverage-manifest.md  # every in-scope file, owning track, read-status
    tracks/                  # raw per-track outputs (Cn, Dn, Xn, gate-reproduction)
```

Start at `consolidated.md`; drill into `tracks/<ID>.md` for the full per-area
detail behind any finding. A master review is read-only with respect to the
codebase — it produces findings and prioritized follow-up proposals, and applies
no changes.

## Runs

| Run | Commit | Verdict |
|-----|--------|---------|
| [2026-05-22-152729](2026-05-22-152729/consolidated.md) | `288ddb2` | Shipped kernel APPROVE; doc/CI integrity and one latent context-switch contract gap need attention (4 Blocker / 18 Major, all in CI-infra, doc/ADR drift, and the `d8`–`d15` contract — 0 kernel-code or security Blockers). |
