---
name: sync-adr-index
description: Rebuild the ADR index table in `docs/decisions/README.md` from the actual ADR files on disk.
when-to-use: After adding, superseding, or deprecating ADRs in a way that the index may have fallen out of sync. Also as a periodic maintenance task.
---

# Sync ADR index

## Inputs

None. This skill scans the filesystem and reconciles.

## Procedure

1. **Enumerate ADR files.**
   - List every file in `docs/decisions/` matching the pattern `NNNN-*.md`, where `NNNN` is a zero-padded four-digit number.
   - Exclude `README.md` and `template.md`.
   - Sort numerically by `NNNN`.

2. **Read metadata from each ADR.**
   - Open the file.
   - Extract:
     - **Number** — from the filename.
     - **Title** — from the first `#` heading, with the "NNNN — " prefix stripped.
     - **Status** — from the `- **Status:** ...` line in the header block. Ordinary values: `Proposed`, `Accepted`, `Deprecated`, `Superseded by NNNN`. Preserve the existing evidence-backed `Deferred` placeholder in ADR-0023 and ADR-0022's full qualified partial-supersession status; report these forms explicitly. An unfamiliar status is an anomaly, not permission to infer acceptance.
     - **Date** — the entire `- **Date:** ...` value. New records use ISO-8601; preserve ADR-0023's existing prose-extended Date, reporting its historical form instead of truncating it or guessing a filing date.
   - Preserve the heading's title exactly after stripping the number prefix, including inline code; a historical descriptive index alias is a mismatch to report, not the source of the title.
   - If any field is missing or malformed, record the anomaly and continue. Anomalies are reported at the end, not silently ignored.

3. **Cross-check supersession.**
   - For every ADR whose status starts with `Superseded by MMMM`, confirm that ADR `MMMM` exists and is `Accepted`; retain any explicit partial-axis qualification.
   - Check the older callout and newer Context/References for consistent forward/backward supersession pointers and scope. ADR-0022/0026 supersede only the idle-location axis; the typed-error decision still stands. ADR-0041/0042 record whole-decision supersession.
   - Distinguish explicit supersession from ordinary correction, implementation, or cross-reference riders. A forward link alone does not require a status flip. Report an actual conflicting decision or missing supersession pointer; do not relabel every Accepted record that links to a later ADR.
   - Record inconsistencies as anomalies.

4. **Rebuild the index table.** In [`docs/decisions/README.md`](../../../docs/decisions/README.md), replace the contents of the `## Index` section's table with freshly generated rows:

   ```markdown
   | # | Title | Status | Date |
   |---|-------|--------|------|
   | 0001 | [<Title>](0001-slug.md) | Accepted | 2026-04-20 |
   | 0002 | [<Title>](0002-slug.md) | Accepted | 2026-04-20 |
   ...
   ```

   - Rows are in numeric order.
   - Each title is a relative link to its ADR file and matches the exact header title.
   - Status column reflects exactly what the ADR header says.
   - Date column is the ADR's authoritative `Date:` field.

5. **Do not touch the rest of `README.md` during an ordinary index rebuild.** The surrounding sections (Why ADRs, Format, Creating a new ADR) are not this skill's responsibility. Separately authorized procedure/metadata reconciliation, such as [T-055](../../../docs/analysis/tasks/phase-b2/T-055-adr-append-only-corrections.md) under [ADR-0043](../../../docs/decisions/0043-documentation-corpus-consistency.md), records its own scope and evidence; an index sync alone does not authorize it.

6. **Report anomalies** to the maintainer, if any:
   - ADRs missing a Status or Date.
   - ADRs with status `Superseded by MMMM` where MMMM does not exist or is not Accepted.
   - Missing, extra or duplicate index members and title/status/full-Date mismatches against source headers, with before/after values and disposition.
   - ADRs whose title does not match their filename slug, separately from index/header mismatches. Normalize a full title by lowercasing ASCII alphanumerics and joining other runs with hyphens for this literal comparison; report fuller historical titles without renaming filed records or claiming a synchronized index removes those differences.
   - Evidence-backed noncanonical metadata forms (Deferred, prose-extended Date, qualified partial supersession), explicitly distinguished from missing/malformed/unknown values. Preserve the supported historical value; do not make it a blanket exception for new records.
   - Gaps in numbering with their actual evidence and disposition. Slot 0034 is intentionally reserved by ADR-0027 and documented in the index; do not invent a record or renumber later ADRs to close it. Report any other gap without fabricating its cause.

7. **Commit** per [commit-style.md](../../../docs/standards/commit-style.md):
   - Message: `docs(adr): sync index`.
   - Body: optional; if the sync resolves any anomalies, note them.

## Acceptance criteria

- [ ] Index table rows match the set of `NNNN-*.md` files on disk.
- [ ] Each row's title, status, and date match the corresponding ADR's header.
- [ ] Supersession back-pointers consistent in both directions.
- [ ] Anomalies (if any) reported explicitly, not silently patched.
- [ ] Historical title/slug differences and metadata forms are reported separately from repaired index/header mismatches; no blanket "no anomalies" claim hides them.

## Anti-patterns

- **Editing ADR bodies during a sync.** This skill only touches `docs/decisions/README.md`.
- **Silently fixing anomalies.** If an ADR lacks a Date, the sync reports the missing field; it does not guess.
- **Reformatting the surrounding `README.md` prose.** The table is all this skill rebuilds.
- **Renumbering ADRs to close gaps.** ADR numbers are stable history; gaps are acceptable, renumbering breaks citations.
- **Collapsing a rider into supersession.** A correction pointer is not a whole-decision override; preserve explicit partial-axis scope.

## References

- [docs/decisions/README.md](../../../docs/decisions/README.md) — the index this skill maintains.
- [write-adr](../write-adr/SKILL.md) — used when adding an ADR.
- [supersede-adr](../supersede-adr/SKILL.md) — used when overriding an ADR.
- [commit-style.md](../../../docs/standards/commit-style.md) — commit format.
