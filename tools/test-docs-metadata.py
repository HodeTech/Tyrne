#!/usr/bin/env python3
"""Isolated metadata contracts for the offline consistency command."""

from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
import docs_metadata as metadata


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tyrne metadata ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write("README.md", "# Fixture\n")
        self.tasks = {}
        self.adrs = {}
        self.reviews = {}

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def task(self, identity="T-080", status="Ready", date_done=None, phase="phase-x", path=None):
        path = path or "docs/analysis/tasks/" + phase + "/" + identity + "-work.md"
        text = ("# " + identity + " — Fixture task\n\n- **Status:** " + status +
                "\n- **Created:** 1999-01-01\n")
        if date_done is not None:
            text += "- **date_done:** " + date_done + "\n"
        self.write(path, text + "\n---\n\n## User story\n\nFixture.\n")
        self.tasks[path] = (identity, status)
        parent = Path(path).parent
        rows = ["| ID | Title | Milestone | Status |", "|---|---|---|---|"]
        for name, (key, state) in sorted(self.tasks.items()):
            if Path(name).parent == parent:
                rows.append("| [" + key + "](" + Path(name).name + ") | Fixture | X1 | " + state + " |")
        self.write((parent / "README.md").as_posix(), "# Tasks\n\n" + "\n".join(rows) + "\n")
        return path

    def adr(self, number="0001", title="Fixture `Cpu` decision", status="Accepted", date="2026-10-15"):
        path = "docs/decisions/" + number + "-immutable-slug.md"
        self.write(path, "# " + number + " — " + title + "\n\n- **Status:** " + status +
                   "\n- **Date:** " + date + "\n- **Deciders:** @fixture\n\n## Context\n\nFixture.\n")
        self.adrs[path] = (number, title, status, date)
        rows = ["| # | Title | Status | Date |", "|---|---|---|---|"]
        for name, (key, heading, state, recorded) in sorted(self.adrs.items()):
            rows.append("| " + key + " | [" + heading + "](" + Path(name).name + ") | " + state + " | " + recorded + " |")
        self.write("docs/decisions/README.md", "# ADRs\n\n" + "\n".join(rows) + "\n\n0034 is reserved; no file required.\n")
        return path

    def test_task_lifecycle_normalization_and_valid_completion_dates(self):
        for state in ("Draft", "Ready", "In Progress", "In Review", "Blocked", "Superseded", "Done (2026-10-15)"):
            with self.subTest(state=state):
                self.task(status=state, date_done="2026-10-15" if state.startswith("Done") else None)
                self.clean("tasks")

    def test_new_completion_date_cannot_be_bypassed_by_created_backdating(self):
        path = self.task(status="Done")
        report = self.rejects("tasks", "task", path)
        self.assertTrue(any("date_done" in x.message for x in report.findings))
        self.task(status="Done", date_done="2024-02-29")
        self.clean("tasks")

    def test_present_completion_dates_require_real_calendar_dates(self):
        for date in ("2026-02-29", "2026-13-01", "20261015", "2026-2-9", ""):
            with self.subTest(date=date):
                path = self.task(status="Done", date_done=date)
                self.rejects("tasks", "task", path)

    def test_open_task_cannot_have_a_completion_date(self):
        path = self.task(status="In Review", date_done="2026-10-15")
        self.rejects("tasks", "task", path)

    def test_exact_legacy_paths_only_exempt_missing_completion_date(self):
        for path in metadata.LEGACY_DONE_WITHOUT_DATE:
            identity = Path(path).name.split("-")[0] + "-" + Path(path).name.split("-")[1]
            self.task(identity=identity, status="Done (2026-05-07)", path=path)
        self.assertEqual(17, len(self.tasks))
        self.clean("tasks")
        legacy = "docs/analysis/tasks/phase-a/T-001-capability-table-foundation.md"
        self.task(identity="T-001", status="Done", date_done="invalid", path=legacy)
        self.rejects("tasks", "task", legacy)

    def test_renamed_legacy_file_does_not_inherit_date_exception(self):
        path = self.task(identity="T-001", status="Done", phase="phase-a")
        self.rejects("tasks", "task", path)

    def test_task_index_missing_extra_and_duplicate_rows(self):
        path = self.task()
        index = self.root / Path(path).with_name("README.md")
        original = index.read_text()
        row = original.splitlines()[-1]
        for changed in (original.replace(row, ""), original + row + "\n",
                        original + "| [T-081](T-081-absent.md) | Extra | X1 | Ready |\n"):
            with self.subTest(index=changed):
                index.write_text(changed, encoding="utf-8")
                self.rejects("tasks", "task-index", str(index.relative_to(self.root)))

    def test_project_global_task_ids_cannot_repeat_in_another_phase(self):
        self.task(phase="phase-x")
        self.task(phase="phase-y")
        report = self.rejects("tasks", "task")
        self.assertTrue(any("Duplicate" in x.message for x in report.findings))

    def test_task_index_status_and_header_identity_must_agree(self):
        path = self.task()
        index = self.root / Path(path).with_name("README.md")
        original = index.read_text()
        index.write_text(original.replace("| Ready |", "| In Review |"), encoding="utf-8")
        self.rejects("tasks", "task-index")
        index.write_text(original, encoding="utf-8")
        source = self.root / path
        source.write_text(source.read_text().replace("# T-080", "# T-081"), encoding="utf-8")
        self.rejects("tasks", "task", path)

    def test_inventory_tables_reject_wrong_width_and_duplicate_metadata(self):
        path = self.task()
        index = self.root / Path(path).with_name("README.md")
        original = index.read_text()
        row = original.splitlines()[-1]
        index.write_text(original.replace(row, row + " surplus |"), encoding="utf-8")
        self.rejects("tasks", "task-index")
        index.write_text(original, encoding="utf-8")
        source = self.root / path
        source.write_text(source.read_text().replace("- **Status:** Ready", "- **Status:** Ready\n- **Status:** Done"), encoding="utf-8")
        self.rejects("tasks", "task", path)

    def test_empty_future_task_index_allows_only_declared_pending_row(self):
        self.write("docs/analysis/tasks/phase-c/README.md",
                   "# Tasks\n\n| ID | Title | Milestone | Status |\n|---|---|---|---|\n| _(pending)_ | — | — | — |\n")
        self.clean("tasks")
        self.task(phase="phase-c")
        index = self.root / "docs/analysis/tasks/phase-c/README.md"
        index.write_text(index.read_text() + "| _(pending)_ | — | — | — |\n", encoding="utf-8")
        self.rejects("tasks", "task-index")

    def test_adr_index_uses_actual_heading_including_code_not_filename_slug(self):
        self.adr()
        self.clean("adrs")
        index = self.root / "docs/decisions/README.md"
        index.write_text(index.read_text().replace("[Fixture `Cpu` decision]", "[Immutable slug]"), encoding="utf-8")
        self.rejects("adrs", "adr-index")

    def test_adr_membership_rejects_missing_extra_and_duplicate_rows(self):
        self.adr()
        index = self.root / "docs/decisions/README.md"
        original = index.read_text()
        row = next(x for x in original.splitlines() if x.startswith("| 0001 |"))
        for changed in (original.replace(row, ""), original.replace(row, row + "\n" + row),
                        original.replace(row, row + "\n| 0002 | [Absent](0002-absent.md) | Proposed | 2026-10-15 |")):
            with self.subTest(index=changed):
                index.write_text(changed, encoding="utf-8")
                self.rejects("adrs", "adr-index")

    def test_adr_status_and_complete_date_match_authoritative_header(self):
        self.adr()
        index = self.root / "docs/decisions/README.md"
        original = index.read_text()
        for changed in (original.replace("| Accepted |", "| Proposed |"),
                        original.replace("| 2026-10-15 |", "| 2026-10-14 |")):
            with self.subTest(index=changed):
                index.write_text(changed, encoding="utf-8")
                self.rejects("adrs", "adr-index")

    def test_deferred_prose_date_and_partial_supersession_are_preserved(self):
        self.adr("0022", status="Superseded by 0026 (idle axis only; typed-error axis stands)")
        self.adr("0023", status="Deferred", date="2026-04-27 (deferred at closure); placeholder body landed 2026-05-07")
        self.adr("0026", title="Replacement decision")
        self.clean("adrs")
        index = self.root / "docs/decisions/README.md"
        index.write_text(index.read_text().replace("placeholder body landed 2026-05-07", "placeholder body landed 2026-05-08"), encoding="utf-8")
        self.rejects("adrs", "adr-index")

    def test_reserved_slot_is_not_an_expected_file_or_index_row(self):
        self.adr()
        self.clean("adrs")
        index = self.root / "docs/decisions/README.md"
        index.write_text(index.read_text().replace("| 0001 |", "| 0034 |"), encoding="utf-8")
        self.rejects("adrs", "adr-index")

    def test_adr_header_identity_metadata_and_calendar_errors_are_visible(self):
        path = self.adr()
        source = self.root / path
        original = source.read_text()
        for changed in (original.replace("# 0001", "# 0002"),
                        original.replace("- **Date:** 2026-10-15", "- **Date:** 2026-02-29"),
                        original.replace("- **Status:** Accepted", "- **Status:** Accepted\n- **Status:** Proposed"),
                        original.replace("- **Status:** Accepted\n", "")):
            with self.subTest(source=changed):
                source.write_text(changed, encoding="utf-8")
                self.rejects("adrs", "adr", path)

    def test_unexpected_adr_document_is_not_silently_ignored(self):
        self.adr()
        self.write("docs/decisions/unallocated-draft.md", "# Unallocated\n")
        self.rejects("adrs", "adr", "docs/decisions/unallocated-draft.md")

    def test_metadata_read_safety_does_not_depend_on_selecting_links(self):
        path = self.task()
        target = self.root / path
        target.unlink()
        self.write("outside/canary.md", "# T-080 — Canary\n\n- **Status:** Ready\n")
        target.symlink_to(self.root / "outside/canary.md")
        self.rejects("tasks", "input", path)

    def test_task_index_reference_shortcut_and_title_links_are_supported(self):
        path = self.task()
        index = self.root / Path(path).with_name("README.md")
        original = index.read_text()
        direct = "[T-080](T-080-work.md)"
        forms = (
            original.replace(direct, "[T-080][task]") + "\n[task]: T-080-work.md\n",
            original.replace(direct, "[T-080]") + "\n[T-080]: T-080-work.md\n",
            original.replace(direct, "T-080").replace("| Fixture |", "| [Fixture](T-080-work.md) |"),
        )
        for text in forms:
            with self.subTest(index=text):
                index.write_text(text, encoding="utf-8")
                self.clean("tasks")

    def test_adr_date_token_cannot_hide_extra_digits_or_letters(self):
        for value in ("2026-10-150", "2026-10-15oops", "not-a-date",
                      "2026-10-15 (amended 2026-02-29)",
                      "2026-10-15 (amended 2026-04-270)",
                      "2026-10-15 (amended 2026-04-27oops)",
                      "2026-10-15 (amended 2026-04-27α)",
                      "2026-10-15 (amended 2026-٠٤-27)"):
            with self.subTest(date=value):
                path = self.adr(date=value)
                self.rejects("adrs", "adr", path)

    def test_adr_title_keeps_literal_escapes_inside_inline_code(self):
        self.adr(title=r"Literal `\#` heading")
        self.clean("adrs")
        index = self.root / "docs/decisions/README.md"
        index.write_text(index.read_text().replace(r"[Literal `\#` heading]", "[Literal `#` heading]"), encoding="utf-8")
        self.rejects("adrs", "adr-index")

    def review(self, name="2026-10-15-scope.md", family="code-reviews", body="Fixture.\n", evidence=""):
        folder = "docs/analysis/reviews/" + family
        path = folder + "/" + name
        self.write(path, "# Review\n\n" + body)
        self.reviews[path] = (name[:10], evidence)
        rows = ["| Date | Scope | File |", "|---|---|---|"]
        for target, (day, extra) in sorted(self.reviews.items()):
            if Path(target).parent.as_posix() == folder:
                rows.append("| " + day + " | Fixture | [Report](" + Path(target).name + ")" + extra + " |")
        self.write(folder + "/README.md", "# Reviews\n\n" + "\n".join(rows) + "\n")
        self.write(folder + "/master-plan.md", "# Procedure\n")
        return path

    def master_run(self, identity="2026-10-15-120000"):
        folder = "docs/analysis/reviews/master-review"
        self.write(folder + "/" + identity + "/consolidated.md",
                   "# Consolidated\n\n[Coverage](00-coverage-manifest.md) [Tracks](tracks/)\n")
        self.write(folder + "/" + identity + "/00-coverage-manifest.md", "# Coverage\n")
        self.write(folder + "/" + identity + "/tracks/c1.md", "# Track\n")
        self.write(folder + "/README.md", "# Runs\n\n| Run | Commit | Verdict |\n|---|---|---|\n| [" +
                   identity + "](" + identity + "/consolidated.md) | `fixture` | Fixture |\n")
        return folder + "/" + identity

    def test_all_event_review_families_reconcile_canonical_files(self):
        for family in ("business-reviews", "code-reviews", "security-reviews", "performance-optimization-reviews"):
            self.review(family=family)
        self.clean("reviews")

    def test_review_missing_duplicate_and_extra_index_rows_fail(self):
        path = self.review()
        index = self.root / Path(path).with_name("README.md")
        original = index.read_text()
        row = original.splitlines()[-1]
        for text in (original.replace(row, ""), original + row + "\n",
                     original + "| 2026-10-15 | Extra | [Missing](2026-10-15-missing.md) |\n"):
            with self.subTest(index=text):
                index.write_text(text, encoding="utf-8")
                self.rejects("reviews", "review-index")

    def test_nondated_unindexed_top_level_report_is_not_ignored(self):
        self.review()
        self.write("docs/analysis/reviews/code-reviews/unindexed.md", "# Undiscovered\n")
        self.rejects("reviews", "review-index")

    def test_companion_plan_requires_explicit_existing_canonical_owner(self):
        path = self.review()
        folder = Path(path).parent
        plan = "2026-10-15-scope-review-plan.md"
        self.write((folder / plan).as_posix(), "# Plan\n")
        self.rejects("reviews", "review-index")
        index = self.root / folder / "README.md"
        index.write_text(index.read_text() + "\n## Companion plans\n\n- [Plan](" + plan +
                         "), owned by the [canonical review](" + Path(path).name + ").\n", encoding="utf-8")
        self.clean("reviews")
        index.write_text(index.read_text().replace("owned by the [canonical review](" + Path(path).name,
                                                  "owned by the [canonical review](2026-10-15-absent.md"), encoding="utf-8")
        self.rejects("reviews", "review-index")

    def test_file_cell_supporting_links_are_not_extra_canonical_entries(self):
        self.write("docs/analysis/reviews/code-reviews/nested/c1.md", "# Track\n")
        self.review(evidence=" (with [tracks](nested/))")
        self.clean("reviews")

    def test_nested_reports_must_be_discoverable_from_the_family(self):
        self.review(body="[Preflight](nested/preflight.md)\n")
        self.write("docs/analysis/reviews/code-reviews/nested/preflight.md", "# Preparation\n\n[Track](c1.md)\n")
        self.write("docs/analysis/reviews/code-reviews/nested/c1.md", "# Track\n")
        self.clean("reviews")
        self.write("docs/analysis/reviews/code-reviews/nested/orphan.md", "# Undiscovered\n")
        self.rejects("reviews", "review-index")

    def test_root_directory_link_does_not_blanket_own_nested_reports(self):
        self.review(body="[Family](./)\n")
        self.write("docs/analysis/reviews/code-reviews/nested/orphan.md", "# Undiscovered\n")
        self.rejects("reviews", "review-index")

    def test_review_index_date_and_source_width_are_checked(self):
        path = self.review()
        index = self.root / Path(path).with_name("README.md")
        original = index.read_text()
        for text in (original.replace("| 2026-10-15 |", "| 2026-10-14 |"),
                     original.replace("[Report](2026-10-15-scope.md) |", "[Report](2026-10-15-scope.md) | extra |")):
            with self.subTest(index=text):
                index.write_text(text, encoding="utf-8")
                self.rejects("reviews", "review-index")

    def test_master_run_has_exact_index_and_required_supporting_files(self):
        folder = self.master_run()
        self.clean("reviews")
        (self.root / folder / "00-coverage-manifest.md").unlink()
        self.rejects("reviews", "review-index")

    def test_master_index_duplicate_missing_and_wrong_target_fail(self):
        self.master_run()
        index = self.root / "docs/analysis/reviews/master-review/README.md"
        original = index.read_text()
        row = original.splitlines()[-1]
        for text in (original.replace(row, ""), original + row + "\n",
                     original.replace("/consolidated.md", "/00-coverage-manifest.md")):
            with self.subTest(index=text):
                index.write_text(text, encoding="utf-8")
                self.rejects("reviews", "review-index")

    def test_master_run_folder_and_visible_identity_must_agree(self):
        self.master_run()
        index = self.root / "docs/analysis/reviews/master-review/README.md"
        index.write_text(index.read_text().replace("[2026-10-15-120000]", "[2026-10-15-130000]"), encoding="utf-8")
        self.rejects("reviews", "review-index")

    def test_unknown_review_family_is_not_silently_skipped(self):
        self.write("docs/analysis/reviews/unknown-reviews/2026-10-15-scope.md", "# Unknown family\n")
        self.rejects("reviews", "review-index")

    def test_review_file_reference_label_and_scope_citations_are_distinct(self):
        path = self.review()
        index = self.root / Path(path).with_name("README.md")
        text = index.read_text().replace("| Fixture |", "| [Previous](2026-10-15-scope.md) |")
        text = text.replace("[Report](2026-10-15-scope.md)", "[Report][canonical]")
        index.write_text(text + "\n[canonical]: 2026-10-15-scope.md\n", encoding="utf-8")
        self.clean("reviews")

    def test_two_canonical_reports_in_one_file_cell_fail(self):
        first = self.review()
        second = self.review(name="2026-10-15-other.md")
        index = self.root / Path(first).with_name("README.md")
        text = index.read_text().replace("[Report](2026-10-15-scope.md)",
                                        "[Report](2026-10-15-scope.md) [Other](" + Path(second).name + ")")
        index.write_text(text, encoding="utf-8")
        self.rejects("reviews", "review-index")

    def test_companion_literal_examples_do_not_exempt_real_reports(self):
        path = self.review()
        folder = Path(path).parent
        plan = "2026-10-15-plan.md"
        self.write((folder / plan).as_posix(), "# Plan\n")
        index = self.root / folder / "README.md"
        index.write_text(index.read_text() + "\n## Companion plans\n\n```markdown\n- [Plan](" + plan +
                         "), owned by the [canonical review](" + Path(path).name + ").\n```\n", encoding="utf-8")
        self.rejects("reviews", "review-index")

    def test_companion_cycle_and_duplicate_declarations_fail(self):
        path = self.review()
        folder = Path(path).parent
        plan = "2026-10-15-plan.md"
        self.write((folder / plan).as_posix(), "# Plan\n")
        index = self.root / folder / "README.md"
        original = index.read_text()
        declaration = "- [Plan](" + plan + "), owned by the [review](" + Path(path).name + ").\n"
        for extra in (declaration, "- [Review](" + Path(path).name + "), owned by the [plan](" + plan + ").\n"):
            with self.subTest(extra=extra):
                index.write_text(original + "\n## Companion plans\n\n" + declaration + extra, encoding="utf-8")
                self.rejects("reviews", "review-index")

    def test_master_run_calendar_time_and_missing_tracks_fail(self):
        for identity in ("2026-02-29-120000", "2026-10-15-240000", "2026-10-15-126000", "not-a-run"):
            with self.subTest(identity=identity):
                self.master_run(identity)
                self.rejects("reviews", "review-index")
        import shutil
        shutil.rmtree(self.root / "docs/analysis/reviews/master-review")
        folder = self.master_run()
        (self.root / folder / "tracks/c1.md").unlink()
        self.rejects("reviews", "review-index")

    def test_master_track_orphan_is_not_owned_by_presence_alone(self):
        folder = self.master_run()
        source = self.root / folder / "consolidated.md"
        source.write_text(source.read_text().replace(" [Tracks](tracks/)", ""), encoding="utf-8")
        self.rejects("reviews", "review-index", folder + "/tracks/c1.md")

    def test_review_alias_rejected_without_selecting_links(self):
        path = self.review()
        target = self.root / path
        target.unlink()
        other = self.write("outside/report.md", "# Canary\n")
        target.symlink_to(other)
        self.rejects("reviews", "input", path)

    def test_review_discovery_requires_visible_reference_uses(self):
        path = self.review()
        orphan = "docs/analysis/reviews/code-reviews/nested/orphan.md"
        self.write(orphan, "# Orphan\n")
        for body in ("[hidden]: nested/orphan.md\n", "[hidden]: nested/\n",
                     "![hidden]\n\n[hidden]: nested/orphan.md\n"):
            with self.subTest(body=body):
                self.write(path, "# Review\n\n" + body)
                self.rejects("reviews", "review-index", orphan)
                self.clean("links")
        for body in ("[Visible][hidden]\n\n[hidden]: nested/orphan.md\n",
                     "[hidden][]\n\n[hidden]: nested/orphan.md\n",
                     "[hidden]\n\n[hidden]: nested/orphan.md\n",
                     '<a href="nested/orphan.md">Visible</a>\n'):
            with self.subTest(body=body):
                self.write(path, "# Review\n\n" + body)
                self.clean("reviews")
        self.write(path, "# Review\n\n[hidden]: missing.md\n")
        self.rejects("links", "path")

    def test_master_discovery_ignores_unused_reference_definitions(self):
        folder = self.master_run()
        self.write(folder + "/consolidated.md", "# Consolidated\n\n[Coverage](00-coverage-manifest.md)\n\n[unused]: tracks/\n")
        self.rejects("reviews", "review-index", folder + "/tracks/c1.md")
        self.write(folder + "/consolidated.md", "# Consolidated\n\n[Coverage](00-coverage-manifest.md) [tracks]\n\n[tracks]: tracks/\n")
        self.clean("reviews")

    def scan(self, family):
        return metadata.scan_docs(self.root, checks=(family,))

    def planned(self, identity="ADR-C1-secondary-core-start", phase="c", milestone="C1"):
        path = "docs/roadmap/phases/phase-" + phase + ".md"
        anchor = identity.lower()
        self.write(path, '# Phase\n\n## ADR ledger\n\n| Planned identity | Purpose | Milestone | Historical aliases / notes |\n'
                   '|---|---|---|---|\n| <a id="' + anchor + '"></a>' + identity +
                   ' | Fixture purpose | ' + milestone + ' | Historical aliases: ADR-0040 |\n')
        return path

    def test_planned_definition_and_repeated_code_formatted_link_labels(self):
        path = self.planned()
        self.write("docs/current.md", "# Current\n\n[ADR-C1-secondary-core-start](roadmap/phases/phase-c.md#adr-c1-secondary-core-start)\n\n"
                   "[`ADR-C1-secondary-core-start`][decision]\n\n[decision]: roadmap/phases/phase-c.md#adr-c1-secondary-core-start\n")
        self.clean("planned")

    def test_planned_definition_uniqueness_is_separate_from_references(self):
        path = self.planned()
        source = self.root / path
        source.write_text(source.read_text() + source.read_text().splitlines()[-1] + "\n", encoding="utf-8")
        self.rejects("planned", "planned", path)

    def test_same_milestone_distinct_purposes_are_valid(self):
        path = self.planned("ADR-F2-i2c-service", "f", "F2")
        source = self.root / path
        source.write_text(source.read_text() + source.read_text().splitlines()[-1].replace("i2c", "spi") + "\n", encoding="utf-8")
        self.clean("planned")

    def test_planned_identity_requires_matching_milestone_phase_and_anchor(self):
        path = self.planned()
        source = self.root / path
        original = source.read_text()
        for text in (original.replace("| C1 |", "| C2 |"),
                     original.replace('id="adr-c1-secondary-core-start"', 'id="wrong"'),
                     original.replace("ADR-C1-secondary-core-start", "ADR-D1-secondary-core-start")):
            with self.subTest(text=text):
                source.write_text(text, encoding="utf-8")
                self.rejects("planned", "planned", path)

    def test_unknown_or_misdirected_live_purpose_references_fail(self):
        self.planned()
        for label, destination in (("ADR-C1-missing", "roadmap/phases/phase-c.md#adr-c1-missing"),
                                   ("ADR-C1-secondary-core-start", "wrong.md#adr-c1-secondary-core-start"),
                                   ("ADR-C1-secondary-core-start", "roadmap/phases/phase-c.md")):
            with self.subTest(label=label, destination=destination):
                self.write("docs/wrong.md", "# Wrong\n")
                self.write("docs/current.md", "# Current\n\n[" + label + "](" + destination + ")\n")
                self.rejects("planned", "planned", "docs/current.md")

    def test_numeric_live_planned_definitions_fail_even_when_filed(self):
        self.adr("0040")
        path = self.planned()
        source = self.root / path
        original = source.read_text()
        for text in (original.replace("ADR-C1-secondary-core-start", "ADR-0040"),
                     "# Phase C\n\n## ADR ledger\n\n| ADR | Purpose | Expected state |\n|---|---|---|\n| ADR-0040 | Future decision | C1 |\n"):
            with self.subTest(text=text):
                source.write_text(text, encoding="utf-8")
                self.rejects("planned", "planned", path)

    def test_historical_filed_ledgers_and_future_unallocated_rows_are_valid(self):
        self.write("docs/roadmap/phases/phase-a.md", "# Phase A\n\n| ADR | Purpose | Expected state |\n|---|---|---|\n| ADR-0014 | Historical | Accepted |\n")
        self.write("docs/roadmap/phases/phase-j.md", "# Phase J\n\n## ADR ledger\n\n| ADR | Purpose | Expected state |\n|---|---|---|\n| _(future)_ | Runtime choice | J1 |\n")
        path = self.planned()
        source = self.root / path
        source.write_text(source.read_text() + "| _(none)_ | Implementation only | C2 | No new ADR |\n", encoding="utf-8")
        self.clean("planned")

    def test_purpose_examples_in_fences_are_not_definitions_or_references(self):
        self.planned()
        self.write("docs/example.md", "# Example\n\n```markdown\n[ADR-Z9-missing](absent.md)\n| Planned identity | Purpose | Milestone |\n|---|---|---|\n| ADR-0001 | Example | Z9 |\n```\n")
        self.clean("planned")

    def test_unknown_purpose_anchor_cannot_hide_behind_a_human_label(self):
        self.planned()
        self.write("docs/current.md", "# Current\n\n[Unknown decision](roadmap/phases/phase-c.md#adr-c9-missing)\n")
        self.rejects("planned", "planned", "docs/current.md")

    def test_filed_purpose_keeps_one_ledger_definition_and_record_alias(self):
        path = self.planned()
        record = self.adr("0044", title="Secondary core start")
        source = self.root / path
        original = source.read_text()
        source.write_text(original.replace("Fixture purpose", "[Filed decision](../../decisions/0044-immutable-slug.md)"), encoding="utf-8")
        target = self.root / record
        target.write_text(target.read_text() + "\nHistorical alias: `ADR-C1-secondary-core-start`.\n", encoding="utf-8")
        self.write("docs/current.md", "# Current\n\n[ADR-C1-secondary-core-start](decisions/0044-immutable-slug.md)\n")
        self.clean("planned")
        target.write_text(target.read_text().replace("Historical alias: `ADR-C1-secondary-core-start`.", "Historical alias omitted."), encoding="utf-8")
        self.rejects("planned", "planned")

    def test_standard_fence_openings_preserve_length_and_container_rules(self):
        self.write("docs/standards/fixture.md", "# Standard\n\n````markdown\n```\n````\n\n> ~~~rust\n> code\n> ~~~\n\n- List\n\n  ```text\n  sample\n  ```\n")
        self.clean("fences")

    def test_untagged_standard_opening_reports_original_line_only(self):
        self.write("docs/standards/fixture.md", "# Standard\n\n> ~~~~\n> code\n> ~~~~\n")
        report = self.rejects("fences", "standard-fence", "docs/standards/fixture.md")
        self.assertEqual([(3, "standard-fence")], [(x.line, x.code) for x in report.findings])

    def test_archived_untagged_fences_are_outside_standard_tag_policy(self):
        self.write("docs/analysis/reports/history.md", "# History\n\n```\nhistorical\n```\n")
        self.clean("fences")

    def audit_fixture(self, source="// Audit: UNSAFE-2026-0001\n", entries=None):
        self.write("Cargo.toml", '[workspace]\nmembers = ["kernel"]\n')
        self.write("kernel/Cargo.toml", '[package]\nname = "fixture"\n')
        self.write("kernel/src/lib.rs", source)
        entries = entries if entries is not None else {"UNSAFE-2026-0001": "Active"}
        self.write("docs/audits/unsafe-log.md", "# Unsafe log\n\n" + "\n".join(
            "### " + key + " — Fixture\n\n- **Status:** " + state + ".\n" for key, state in entries.items()))

    def test_unsafe_active_reference_and_original_physical_line(self):
        self.audit_fixture("// Audit: UNSAFE-2026-0001\r\n\r\n// Historical UNSAFE-2026-0099\r")
        report = self.rejects("unsafe", "unsafe-ref", "kernel/src/lib.rs")
        self.assertEqual([3], [x.line for x in report.findings if x.code == "unsafe-ref"])

    def test_unsafe_wrapped_lists_shorthand_and_safe_audited_under(self):
        self.audit_fixture("// Audit:\n// `UNSAFE-2026-0001` (page tables) +\n// UNSAFE-2026-0002 / 0003, UNSAFE-2026-0004.\n\n"
                           "/// The assertion itself is audited\n/// under UNSAFE-2026-0005 (safe invariant).\n",
                           {"UNSAFE-2026-%04d" % n: "Active" for n in range(1, 6)})
        self.clean("unsafe")

    def test_unsafe_removed_history_does_not_become_an_active_annotation(self):
        self.audit_fixture("// Reject the old UNSAFE-2026-0012 pattern.\n// Audit: UNSAFE-2026-0001 (see UNSAFE-2026-0012 history).\n",
                           {"UNSAFE-2026-0001": "Active", "UNSAFE-2026-0012": "Removed"})
        self.clean("unsafe")

    def test_unsafe_removed_active_annotation_and_unknown_shorthand_fail(self):
        self.audit_fixture("// Audit: UNSAFE-2026-0001 / 0012 / 0099\n",
                           {"UNSAFE-2026-0001": "Active", "UNSAFE-2026-0012": "Removed"})
        self.rejects("unsafe", "unsafe-ref")

    def test_unsafe_active_entry_requires_annotation_not_ordinary_mentions(self):
        self.audit_fixture("// Historical reference UNSAFE-2026-0001.\n")
        self.rejects("unsafe", "unsafe-log", "docs/audits/unsafe-log.md")

    def test_unsafe_lists_stop_at_prose_and_source_gaps(self):
        self.audit_fixture("// Audit: UNSAFE-2026-0001. Previously UNSAFE-2026-0002.\n\n// UNSAFE-2026-0003\n",
                           {"UNSAFE-2026-%04d" % n: "Active" for n in range(1, 4)})
        report = self.rejects("unsafe", "unsafe-log")
        self.assertEqual(2, len([x for x in report.findings if x.code == "unsafe-log"]))

    def test_unsafe_strings_raw_strings_characters_and_lifetimes(self):
        self.audit_fixture('const S: &str = "// Audit: UNSAFE-2026-0099";\n'
                           'const R: &str = r###"quote"# // Audit: UNSAFE-2026-0098"###;\n'
                           'const B: &[u8] = br##"/* Audit: UNSAFE-2026-0097 */"##;\n'
                           'const C: char = \'/\';\nfn f<\'a>(x: &\'a str) {\n'
                           ' // Audit: UNSAFE-2026-0001\n}\n')
        self.clean("unsafe")

    def test_unsafe_nested_rust_and_assembly_comments(self):
        self.audit_fixture("/* outer /* nested */ Audit: UNSAFE-2026-0001 */\n")
        self.write("kernel/src/vectors.S", '/* Audit:\n * UNSAFE-2026-0002 */\nmov x0, #1\n.asciz "// UNSAFE-2026-0099"\n')
        self.write("docs/audits/unsafe-log.md", "# Log\n\n### UNSAFE-2026-0001 — Rust\n\n- **Status:** Active.\n\n### UNSAFE-2026-0002 — Assembly\n\n- **Status:** Active.\n")
        self.clean("unsafe")

    def test_unsafe_malformed_id_and_unterminated_lexical_input_fail(self):
        for source in ("// Audit: UNSAFE-2026-00010\n", "// UNSAFE-2026-00x1\n", 'const S: &str = "unterminated', "/* unterminated"):
            with self.subTest(source=source):
                self.audit_fixture(source)
                report = self.scan("unsafe")
                self.assertTrue(any(x.code in ("unsafe-ref", "unsafe-source") for x in report.findings), report.as_dict())

    def test_unsafe_log_duplicate_status_id_and_fenced_examples(self):
        self.audit_fixture()
        log = self.root / "docs/audits/unsafe-log.md"
        original = log.read_text()
        for changed in (original + original[original.index("###"):],
                        original.replace("- **Status:** Active.", "- **Status:** Active.\n- **Status:** Removed."),
                        original.replace("Active.", "Unknown."), original.replace("- **Status:** Active.", "")):
            with self.subTest(log=changed):
                log.write_text(changed, encoding="utf-8")
                self.rejects("unsafe", "unsafe-log")
        log.write_text(original + "\n```markdown\n### UNSAFE-2026-0099 — Example\n- **Status:** Active.\n```\n", encoding="utf-8")
        self.clean("unsafe")

    def test_unsafe_all_workspace_members_independent_of_defaults(self):
        self.audit_fixture()
        self.write("Cargo.toml", '[workspace]\nmembers = ["kernel", "bsp"]\ndefault-members = ["kernel"]\n')
        self.write("bsp/Cargo.toml", '[package]\nname = "bsp"\n')
        self.write("bsp/tests/check.rs", "// Unknown UNSAFE-2026-0099\n")
        self.rejects("unsafe", "unsafe-ref", "bsp/tests/check.rs")

    def test_unsafe_build_examples_benches_custom_sources_and_generated_boundary(self):
        self.audit_fixture()
        self.write("kernel/Cargo.toml", '[package]\nname = "fixture"\nbuild = "custom/build.rs"\n[[bin]]\nname = "custom"\npath = "custom/main.rs"\n')
        for path in ("custom/build.rs", "custom/main.rs", "examples/demo.rs", "benches/bench.rs", "src/target/module.rs"):
            self.write("kernel/" + path, "// Audit: UNSAFE-2026-0001\n")
        self.write("kernel/target/generated.rs", "// UNSAFE-2026-0099\n")
        self.clean("unsafe")

    def test_unsafe_in_root_path_dependency_cannot_disappear(self):
        self.audit_fixture()
        self.write("kernel/Cargo.toml", '[package]\nname = "fixture"\n[dependencies]\nother = { path = "../other" }\n')
        self.write("other/Cargo.toml", '[package]\nname = "other"\n')
        self.write("other/src/lib.rs", "// Unknown UNSAFE-2026-0099\n")
        report = self.scan("unsafe")
        self.assertTrue(any(x.code == "unsafe-scope" or (x.code == "unsafe-ref" and x.path == "other/src/lib.rs") for x in report.findings), report.as_dict())

    def test_unsafe_unsupported_scope_and_duplicate_manifest_keys_fail(self):
        for manifest in ('[workspace]\nmembers = ["*"]\n',
                         '[workspace]\nmembers = ["kernel"]\nexclude = ["other"]\n',
                         '[workspace]\nmembers = ["kernel"]\nmembers = []\n',
                         'workspace = { members = ["missing"] }\n',
                         '[workspace]\nmembers = "kernel"\n'):
            with self.subTest(manifest=manifest):
                self.audit_fixture()
                self.write("Cargo.toml", manifest)
                self.rejects("unsafe", "unsafe-scope")

    def test_unsafe_custom_source_missing_or_outside_package_fails(self):
        for path in ("missing.rs", "../outside.rs"):
            with self.subTest(path=path):
                self.audit_fixture()
                self.write("outside.rs", "// Audit: UNSAFE-2026-0001\n")
                self.write("kernel/Cargo.toml", '[package]\nname = "fixture"\nbuild = "' + path + '"\n')
                self.rejects("unsafe", "unsafe-scope")

    def test_unsafe_manifest_strings_comments_and_metadata_do_not_change_scope(self):
        self.audit_fixture()
        self.write("Cargo.toml", '[workspace]\nmembers = [\n "kernel", # actual member\n]\n[workspace.metadata]\nnote = "# members = []"\n')
        self.clean("unsafe")

    def test_unsafe_dotted_and_quoted_manifest_scope_is_resolved_or_rejected(self):
        self.audit_fixture()
        self.write("Cargo.toml", 'workspace."members" = ["kernel", "missing"]\n')
        self.rejects("unsafe", "unsafe-scope")

    def test_unsafe_source_redirection_literal_and_dynamic_forms(self):
        self.audit_fixture('#[path = "other.rs"]\nmod other;\ninclude_str!("vectors.s");\n// Audit: UNSAFE-2026-0001\n')
        self.write("kernel/src/other.rs", "// Audit: UNSAFE-2026-0001\n")
        self.write("kernel/src/vectors.s", "/* Audit: UNSAFE-2026-0001 */\n")
        self.clean("unsafe")
        self.write("kernel/src/lib.rs", 'include!(concat!(env!("OUT_DIR"), "/generated.rs"));\n// Audit: UNSAFE-2026-0001\n')
        self.rejects("unsafe", "unsafe-scope", "kernel/src/lib.rs")

    def test_unsafe_only_selection_guards_source_and_manifest_aliases(self):
        self.audit_fixture()
        source = self.root / "kernel/src/lib.rs"
        source.unlink()
        other = self.write("outside.rs", "// Audit: UNSAFE-2026-0001\n")
        source.symlink_to(other)
        self.rejects("unsafe", "input", "kernel/src/lib.rs")
        source.unlink();source.write_text("// Audit: UNSAFE-2026-0001\n", encoding="utf-8")
        manifest = self.root / "kernel/Cargo.toml"
        manifest.unlink();manifest.symlink_to(self.write("outside.toml", '[package]\nname = "outside"\n'))
        self.rejects("unsafe", "input", "kernel/Cargo.toml")

    def test_unsafe_requires_manifest_log_and_public_regular_utf8_sources(self):
        self.audit_fixture()
        (self.root / "Cargo.toml").unlink()
        self.rejects("unsafe", "read", "Cargo.toml")
        self.audit_fixture()
        (self.root / "docs/audits/unsafe-log.md").unlink()
        self.rejects("unsafe", "read", "docs/audits/unsafe-log.md")
        self.audit_fixture()
        (self.root / "kernel/src/lib.rs").write_bytes(b"\xff")
        self.rejects("unsafe", "read", "kernel/src/lib.rs")

    def test_unsafe_log_adopted_status_qualifications_are_preserved(self):
        self.audit_fixture("// Audit: UNSAFE-2026-0001\n// Historical UNSAFE-2026-0012\n",
                           {"UNSAFE-2026-0001": "Active. Pending smoke verification", "UNSAFE-2026-0012": "Removed — dated retirement"})
        self.clean("unsafe")

    def test_unsafe_workspace_path_dependencies_are_not_lost(self):
        self.audit_fixture()
        self.write("Cargo.toml", '[workspace]\nmembers = ["kernel"]\n[workspace.dependencies]\nother = { path = "other" }\n')
        self.write("kernel/Cargo.toml", '[package]\nname = "fixture"\n[dependencies]\nother.workspace = true\n')
        self.write("other/Cargo.toml", '[package]\nname = "other"\n')
        self.write("other/src/lib.rs", "// Unknown UNSAFE-2026-0099\n")
        self.rejects("unsafe", "unsafe-ref", "other/src/lib.rs")

    def test_unsafe_malformed_slash_suffix_is_not_silently_dropped(self):
        for suffix in ("00010", "00x1"):
            with self.subTest(suffix=suffix):
                self.audit_fixture("// Audit: UNSAFE-2026-0001 / " + suffix + "\n")
                self.rejects("unsafe", "unsafe-ref")

    def test_unsafe_lexical_scan_has_bounded_repeated_line_work(self):
        import subprocess
        import sys
        command = ('import sys; sys.path.insert(0, "tools"); from docs_audit import comments_in_source; '
                   'text = \'let value = r#"// Audit: UNSAFE-2026-0099"#; // ordinary comment\\n\' * 30000; '
                   'regions, strings = comments_in_source(text); '
                   'assert len(regions) == 30000 and len(strings) == 30000')
        result = subprocess.run([sys.executable, "-B", "-c", command], cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, timeout=10)
        self.assertEqual(0, result.returncode, result.stderr.decode())

    def test_unsafe_backtick_slash_shorthand_still_resolves_unknown_tail(self):
        self.audit_fixture("// Audit: `UNSAFE-2026-0001` / `0099`\n")
        self.rejects("unsafe", "unsafe-ref", "kernel/src/lib.rs")

    def test_unsafe_redirected_rust_extension_and_assembly_include_are_bounded(self):
        self.audit_fixture('#[path = "extra.inc"]\nmod extra;\n// Audit: UNSAFE-2026-0001\n')
        self.write("kernel/src/extra.inc", "// Unknown UNSAFE-2026-0099\n")
        self.rejects("unsafe", "unsafe-scope", "kernel/src/lib.rs")
        self.audit_fixture()
        self.write("kernel/src/extra.s", '.include "extra.inc"\n')
        self.rejects("unsafe", "unsafe-scope", "kernel/src/extra.s")

    def test_unsafe_annotation_list_work_is_bounded_with_nested_explanations(self):
        import subprocess
        import sys
        command = ('import sys; sys.path.insert(0, "tools"); from docs_audit import comment_tags; '
                   'text = "Audit: UNSAFE-2026-0001 (" * 15000 + ")" * 15000; '
                   'references, active = comment_tags(text); '
                   'assert len(references) == 15000 and active == {"UNSAFE-2026-0001"}')
        result = subprocess.run([sys.executable, "-B", "-c", command], cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, timeout=10)
        self.assertEqual(0, result.returncode, result.stderr.decode())

    def test_unsafe_explanatory_markers_do_not_activate_history(self):
        for explanation in ("previous Audit: UNSAFE-2026-0002",
                            "nested (previous Audit: UNSAFE-2026-0002)",
                            "previous audited\n// under UNSAFE-2026-0002"):
            for status in ("Active", "Removed"):
                with self.subTest(explanation=explanation, status=status):
                    self.audit_fixture("// Audit: UNSAFE-2026-0001 (" + explanation + ")\n",
                                       {"UNSAFE-2026-0001": "Active", "UNSAFE-2026-0002": status})
                    if status == "Removed":
                        self.clean("unsafe")
                    else:
                        report = self.rejects("unsafe", "unsafe-log")
                        self.assertTrue(any("0002" in x.message for x in report.findings))

    def test_unsafe_explanations_keep_resolution_and_later_real_annotations(self):
        self.audit_fixture("// Audit: UNSAFE-2026-0001 (previous Audit: UNSAFE-2026-0099)\n")
        self.rejects("unsafe", "unsafe-ref", "kernel/src/lib.rs")
        self.audit_fixture("// Audit: UNSAFE-2026-0001 (previous Audit: UNSAFE-2026-0012), UNSAFE-2026-0002.\n"
                           "// This safe assertion (audited under UNSAFE-2026-0003) is current.\n",
                           {"UNSAFE-2026-0001": "Active", "UNSAFE-2026-0002": "Active",
                            "UNSAFE-2026-0003": "Active", "UNSAFE-2026-0012": "Removed"})
        self.clean("unsafe")

    def test_unsafe_macro_redirections_accept_tokens_and_guard_all_delimiters(self):
        self.audit_fixture()
        self.write("kernel/src/extra.rs", "// Audit: UNSAFE-2026-0001\n")
        for name in ("include", "include_str"):
            for opening, closing in (("(", ")"), ("[", "]"), ("{", "}")):
                for gap in (" ", "/* gap */\n"):
                    with self.subTest(name=name, delimiter=opening, gap=gap):
                        prefix = name + gap + "!" + gap + opening
                        self.write("kernel/src/lib.rs", prefix + '"extra.rs"' + closing + ";\n")
                        self.clean("unsafe")
                        self.write("kernel/src/lib.rs", prefix + '"../../outside.rs"' + closing + ";\n")
                        self.rejects("unsafe", "unsafe-scope", "kernel/src/lib.rs")
                        self.write("kernel/src/lib.rs", prefix + 'concat!("extra", ".rs")' + closing + ";\n")
                        self.rejects("unsafe", "unsafe-scope", "kernel/src/lib.rs")

    def test_unsafe_conditional_path_attributes_preserve_predicate_context(self):
        self.audit_fixture()
        self.write("kernel/src/extra.rs", "// Audit: UNSAFE-2026-0001\n")
        for form in ('#[path = "%s"]', '#[cfg_attr(feature = "x", path = "%s")]',
                     '#[cfg_attr(all(unix, feature = "x"), allow(dead_code), cfg_attr(test, path = "%s"))]'):
            with self.subTest(form=form):
                self.write("kernel/src/lib.rs", form % "extra.rs" + "\nmod extra;\n")
                self.clean("unsafe")
                self.write("kernel/src/lib.rs", form % "../../outside.rs" + "\nmod extra;\n")
                self.rejects("unsafe", "unsafe-scope", "kernel/src/lib.rs")
        self.audit_fixture('#[cfg_attr(path = "production", allow(dead_code))]\n'
                           '// #[cfg_attr(test, path = "../../outside.rs")]\n'
                           'const TEXT: &str = "include ! {\\\"../../outside.rs\\\"}";\n'
                           'const BYTES: &[u8] = include_bytes ! {"data.bin"};\n'
                           '// Audit: UNSAFE-2026-0001\n')
        self.clean("unsafe")

    def test_unsafe_raw_attribute_identifiers_keep_source_scope(self):
        self.audit_fixture()
        self.write("kernel/src/extra.rs", "// Audit: UNSAFE-2026-0001\n")
        for form in ('#[r#path = "%s"]', '#[r#cfg_attr(all(), path = "%s")]',
                     '#[cfg_attr(all(), r#path = "%s")]',
                     '#[r#cfg_attr(all(), r#cfg_attr(test, r#path = "%s"))]'):
            with self.subTest(form=form):
                self.write("kernel/src/lib.rs", form % "extra.rs" + "\nmod extra;\n")
                self.clean("unsafe")
                self.write("kernel/src/lib.rs", form % "hidden.inc" + "\nmod extra;\n")
                self.rejects("unsafe", "unsafe-scope")
        self.audit_fixture('#[r#cfg_attr(r#path = "production", allow(dead_code))]\n'
                           '// Audit: UNSAFE-2026-0001\n')
        self.clean("unsafe")

    def test_unsafe_root_patch_and_replace_paths_are_inventoried_transitively(self):
        for table in ('[patch.crates-io]\nother', '[patch."https://example.invalid/index"]\nother',
                      '[replace]\n"other:0.1.0"'):
            for root_package in (False, True):
                with self.subTest(table=table, root_package=root_package):
                    self.audit_fixture()
                    package = '[package]\nname = "root"\n' if root_package else ""
                    self.write("Cargo.toml", package + '[workspace]\nmembers = ["kernel"]\ndefault-members = ["kernel"]\n' +
                               table + ' = { path = "other" }\n')
                    self.write("other/Cargo.toml", '[package]\nname = "other"\n[dependencies]\nthird = { path = "../third" }\n')
                    self.write("other/src/lib.rs", "// Ordinary source\n")
                    self.write("third/Cargo.toml", '[package]\nname = "third"\n')
                    self.write("third/src/lib.rs", "// Unknown UNSAFE-2026-0099\n")
                    self.rejects("unsafe", "unsafe-ref", "third/src/lib.rs")

    def test_unsafe_root_override_paths_cannot_escape_guarded_input(self):
        for value in ('"missing"', '"../outside"', '"docs/analysis/private/hidden"', '4', '"*"'):
            with self.subTest(value=value):
                self.audit_fixture()
                self.write("Cargo.toml", '[workspace]\nmembers = ["kernel"]\n[patch.crates-io]\nother = { path = ' + value + ' }\n')
                self.rejects("unsafe", "unsafe-scope")
        self.audit_fixture()
        self.write("Cargo.toml", '[workspace]\nmembers = ["kernel"]\n[replace]\n"other:0.1.0" = { path = "other" }\n')
        self.write("outside/Cargo.toml", '[package]\nname = "outside"\n')
        (self.root / "other").symlink_to(self.root / "outside", target_is_directory=True)
        self.rejects("unsafe", "input", "other/Cargo.toml")

    def test_unsafe_many_supported_redirections_have_bounded_lookup_work(self):
        import subprocess
        self.audit_fixture('// Audit: UNSAFE-2026-0001\n' + ''.join(
            'const S%d: &str = include_str!("extra.rs");\n' % n for n in range(24000)))
        self.write("kernel/src/extra.rs", "// Audit: UNSAFE-2026-0001\n")
        result = subprocess.run([sys.executable, "-B", str(Path(__file__).with_name("check-docs.py")),
                                 "--root", str(self.root), "--checks", "unsafe", "--json"],
                                capture_output=True, timeout=10)
        self.assertEqual(0, result.returncode, result.stderr.decode())

    def live(self, active=True):
        for identity, state in (("T-080", "In Progress" if active else "In Review"), ("T-081", "Ready")):
            path = self.task(identity=identity, status=state)
            source = self.root / path
            source.write_text(source.read_text().replace("- **Created:**", "- **Phase:** X\n- **Milestone:** Track X-1\n- **Created:**"), encoding="utf-8")
        self.write("docs/roadmap/phases/phase-x.md", "# Phase X\n")
        pointer = "[T-080 — Fixture](../analysis/tasks/phase-x/T-080-work.md), In Progress under this plan." if active else "None; waiting for review."
        return self.write("docs/roadmap/current.md", "# Current\n\n<!-- current-state:start -->\n## Live state — 2026-10-15\n\n"
                          "- **Active phase:** [X — Fixture](phases/phase-x.md).\n- **Selected track:** X-1, approved plan.\n"
                          "- **Active task:** " + pointer + "\n- **Phase inventory:** 2 tasks — 1 " +
                          ("In Progress" if active else "In Review") + ", 1 Ready; phase inventory.\n\n"
                          "| Task | Status |\n|---|---|\n| [T-080](../analysis/tasks/phase-x/T-080-work.md) | " +
                          ("In Progress" if active else "In Review") + " |\n| [T-081](../analysis/tasks/phase-x/T-081-work.md) | Ready |\n"
                          "\n<!-- current-state:end -->\n\nHistorical T-080 Done, intentionally outside live scope.\n")

    def test_live_selected_membership_active_pointer_and_phase_census(self):
        self.live()
        self.clean("live")

    def test_live_no_active_pointer_is_valid_only_without_selected_progress(self):
        source = self.live(active=False)
        self.clean("live")
        path = self.root / "docs/analysis/tasks/phase-x/T-080-work.md"
        path.write_text(path.read_text().replace("In Review", "In Progress"), encoding="utf-8")
        self.rejects("live", "live-state", "docs/roadmap/current.md")

    def test_live_delimiters_must_be_unique_complete_and_ordered(self):
        source = self.live()
        original = source.read_text()
        for text in (original.replace("<!-- current-state:start -->", ""),
                     original.replace("<!-- current-state:end -->", ""),
                     original + "\n<!-- current-state:start -->\n",
                     original.replace("current-state:start", "current-state:TMP").replace("current-state:end", "current-state:start").replace("current-state:TMP", "current-state:end")):
            with self.subTest(text=text):
                source.write_text(text, encoding="utf-8")
                self.rejects("live", "live-state")

    def test_live_stale_status_missing_extra_and_duplicate_selected_rows(self):
        source = self.live()
        original = source.read_text()
        row = "| [T-081](../analysis/tasks/phase-x/T-081-work.md) | Ready |\n"
        for text in (original.replace(row, row.replace("Ready", "Done")), original.replace(row, ""),
                     original.replace(row, row + row),
                     original.replace(row, row + "| [T-082](../analysis/tasks/phase-x/T-081-work.md) | Ready |\n")):
            with self.subTest(text=text):
                source.write_text(text, encoding="utf-8")
                self.rejects("live", "live-state")

    def test_live_census_counts_normalized_states_and_rejects_duplicate_claims(self):
        source = self.live()
        original = source.read_text()
        for text in (original.replace("2 tasks", "3 tasks"), original.replace("1 Ready;", "2 Ready;"),
                     original.replace("1 Ready;", "1 Ready, 0 Ready;")):
            with self.subTest(text=text):
                source.write_text(text, encoding="utf-8")
                self.rejects("live", "live-state")

    def test_live_active_task_cannot_be_ready_or_wrong_visible_identity(self):
        source = self.live()
        original = source.read_text()
        for text in (original.replace("[T-080 — Fixture]", "[T-099 — Fixture]"),
                     original.replace("), In Progress under", "), Ready under"),
                     original.replace("T-080-work.md), In Progress under", "T-081-work.md), In Progress under")):
            with self.subTest(text=text):
                source.write_text(text, encoding="utf-8")
                self.rejects("live", "live-state")

    def test_live_fenced_table_and_history_do_not_supply_current_state(self):
        source = self.live()
        source.write_text(source.read_text().replace("| Task | Status |", "```markdown\n| Task | Status |").replace("<!-- current-state:end -->", "```\n<!-- current-state:end -->"), encoding="utf-8")
        self.rejects("live", "live-state")

    def test_live_heading_calendar_and_duplicate_metadata_fail(self):
        source = self.live()
        original = source.read_text()
        for text in (original.replace("2026-10-15", "2026-02-29"),
                     original.replace("- **Selected track:** X-1, approved plan.", "- **Selected track:** X-1, approved plan.\n- **Selected track:** X-2, ambiguous.")):
            with self.subTest(text=text):
                source.write_text(text, encoding="utf-8")
                self.rejects("live", "live-state")

    def test_live_phase_census_includes_tasks_outside_selected_track(self):
        source = self.live()
        path = self.task(identity="T-082", status="Draft")
        task = self.root / path
        task.write_text(task.read_text().replace("- **Created:**", "- **Phase:** X\n- **Milestone:** Track X-2\n- **Created:**"), encoding="utf-8")
        self.rejects("live", "live-state")
        source.write_text(source.read_text().replace("2 tasks", "3 tasks").replace("1 Ready;", "1 Ready, 1 Draft;"), encoding="utf-8")
        self.clean("live")

    def test_live_zero_count_states_are_portable_across_supported_python(self):
        source = self.live()
        source.write_text(source.read_text().replace("1 Ready;", "1 Ready, 0 Done;"), encoding="utf-8")
        self.clean("live")

    def test_live_overlong_count_is_a_diagnostic_not_an_integer_exception(self):
        source = self.live()
        source.write_text(source.read_text().replace("2 tasks", "9" * 5000 + " tasks"), encoding="utf-8")
        self.rejects("live", "live-state")

    def test_live_delimiters_cannot_gain_authority_from_literal_contexts(self):
        source = self.live()
        original = source.read_text()
        for text in ("```markdown\n" + original + "\n```\n",
                     "<!-- outer comment\n" + original + "\n-->\n",
                     original.replace("<!-- current-state:start -->", "```markdown\n<!-- current-state:start -->\n```"),
                     original.replace("<!-- current-state:end -->", "```markdown\n<!-- current-state:end -->\n```"),
                     '<a title="\n' + original + '\n">Example</a>\n'):
            with self.subTest(text=text):
                source.write_text(text, encoding="utf-8")
                self.rejects("live", "live-state", "docs/roadmap/current.md")

    def test_live_keeps_full_document_references_and_inner_example_context(self):
        source = self.live()
        original = source.read_text().replace('[X — Fixture](phases/phase-x.md)', '[X — Fixture][phase]')
        original += "\n[phase]: phases/phase-x.md\n"
        original = original.replace("<!-- current-state:end -->", "```markdown\n| Task | Status |\n|---|---|\n| bogus | Done |\n```\n<!-- current-state:end -->")
        for newline in ("\n", "\r\n", "\r"):
            with self.subTest(newline=newline):
                source.write_bytes(original.replace("\n", newline).encode("utf-8"))
                self.clean("live")

    def test_live_raw_html_examples_do_not_authorize_delimiters(self):
        source = self.live()
        original = source.read_text()
        for tag in ("pre", "script", "style", "textarea"):
            with self.subTest(tag=tag):
                source.write_text("<" + tag + ">\n" + original + "\n</" + tag + ">\n", encoding="utf-8")
                self.rejects("live", "live-state")
                source.write_text("<" + tag + ">\n```markdown\n<!-- current-state:example -->\n</" + tag + ">\n\n" + original,
                                  encoding="utf-8")
                self.clean("live")

    def test_live_cdata_processing_and_declaration_contexts_remain_literal(self):
        source = self.live()
        original = source.read_text()
        for opening, closing in (("<![CDATA[", "]]>"), ("<?example", "?>"), ("<!EXAMPLE", ">")):
            with self.subTest(opening=opening):
                source.write_text(opening + "\n" + original + "\n" + closing + "\n", encoding="utf-8")
                self.rejects("live", "live-state")
                source.write_text(opening + "\n```markdown\n" + closing + "\n\n" + original, encoding="utf-8")
                self.clean("live")

    def test_live_blank_ended_html_blocks_and_cross_name_endings(self):
        source = self.live()
        original = source.read_text()
        region = original[original.index("<!-- current-state:start -->"):]
        for opening in ("<div>", "<custom>", "</custom>", "<div partial", "<!example"):
            with self.subTest(opening=opening):
                source.write_text(opening + "\n" + region, encoding="utf-8")
                self.rejects("live", "live-state")
                source.write_text(opening + "\n<!-- example -->\n\n" + original, encoding="utf-8")
                self.clean("live")
        source.write_text("<pre>\n```markdown\n</style>\n\n" + original, encoding="utf-8")
        self.clean("live")

    def test_malformed_custom_tags_cannot_hide_real_links(self):
        for tag in ('<custom a=>', '<custom a=bad`value>', '<custom a="1"b="2">', '<custom a=x=y>'):
            with self.subTest(tag=tag):
                self.write("docs/probe.md", tag + "\n[Real](missing.md)\n")
                report = self.rejects("links", "path", "docs/probe.md")
                self.assertEqual([2], [x.line for x in report.findings if x.path == "docs/probe.md"])

    def test_malformed_custom_tags_cannot_hide_standard_fences(self):
        for tag in ('<custom a=>', '<custom a=bad`value>', '<custom a="1"b="2">', '<custom a=x=y>'):
            with self.subTest(tag=tag):
                self.write("docs/standards/probe.md", tag + "\n```\nliteral\n```\n")
                report = self.rejects("fences", "standard-fence", "docs/standards/probe.md")
                self.assertEqual([2], [x.line for x in report.findings if x.code == "standard-fence"])

    def test_type_seven_complete_tags_keep_strict_and_prefix_rules_distinct(self):
        source = self.live()
        original = source.read_text()
        region = original[original.index("<!-- current-state:start -->"):]
        for tag in ('<custom a=word>', '<custom a="" b="2">', '<custom disabled>', '<div a=>'):
            with self.subTest(tag=tag):
                source.write_text(tag + "\n" + region, encoding="utf-8")
                self.rejects("live", "live-state")
                source.write_text(tag + "\n\n" + original, encoding="utf-8")
                self.clean("live")
        for tag in ('<custom a=>', '<custom a=bad`value>', '<custom a="1"b="2">', '<custom a=x=y>'):
            with self.subTest(tag=tag):
                source.write_text(tag + "\n" + region, encoding="utf-8")
                self.clean("live")

    def test_unsafe_unsupported_redirections_do_not_copy_distant_suffixes(self):
        import subprocess
        self.audit_fixture('// Audit: UNSAFE-2026-0001\nfn f() {\n' +
                           'include!(file!());\n' * 384000 + '}\nconst LAST: &str = "extra.rs";\n')
        self.write("kernel/src/extra.rs", "// Audit: UNSAFE-2026-0001\n")
        command = ('import sys; sys.path.insert(0, "tools"); from docs_consistency import Corpus; '
                   'from docs_audit import check_unsafe; '
                   'c = Corpus(sys.argv[1], checks=["unsafe"]); '
                   'check_unsafe(c); '
                   'assert len(c.report.findings) == 384000; '
                   'assert all(x.code == "unsafe-scope" for x in c.report.findings)')
        result = subprocess.run([sys.executable, "-B", "-c", command, str(self.root)],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, timeout=10)
        self.assertEqual(0, result.returncode, result.stderr.decode())

    def cli(self, *args):
        import os
        import subprocess
        result = subprocess.run([sys.executable, str(Path(__file__).with_name("check-docs.py")),
                                 "--root", str(self.root), *args], cwd=self.root.parent,
                                env={**os.environ, "PATH": "", "PYTHONDONTWRITEBYTECODE": "1"},
                                capture_output=True, text=True, timeout=20)
        return result

    def test_cli_default_all_and_explicit_all_share_the_complete_contract(self):
        import json
        self.live()
        self.audit_fixture()
        expected = ["links", "tasks", "adrs", "reviews", "planned", "fences", "unsafe", "live"]
        first = self.cli("--json")
        second = self.cli("--checks", "all", "--json")
        self.assertEqual(0, first.returncode, first.stderr + first.stdout)
        self.assertEqual(0, second.returncode, second.stderr + second.stdout)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(expected, json.loads(first.stdout)["checks"])
        self.assertEqual(expected, metadata.scan_docs(self.root).as_dict()["checks"])

    def test_cli_default_cannot_succeed_by_silently_deselecting_metadata(self):
        import json
        self.live()
        self.audit_fixture()
        source = self.root / "docs/analysis/tasks/phase-x/T-081-work.md"
        source.write_text(source.read_text().replace("- **Status:** Ready", "- **Status:** In Review"), encoding="utf-8")
        self.assertEqual(0, self.cli("--checks", "links").returncode)
        result = self.cli("--json")
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertTrue(any(x["code"] == "task-index" for x in json.loads(result.stdout)["findings"]))

    def test_cli_comma_subsets_enforce_only_selected_families(self):
        import json
        self.task()
        for selection, expected in (("tasks,links", ["tasks", "links"]), ("links, tasks", ["links", "tasks"])):
            with self.subTest(selection=selection):
                result = self.cli("--checks", selection, "--json")
                self.assertEqual(0, result.returncode, result.stderr + result.stdout)
                self.assertEqual(expected, json.loads(result.stdout)["checks"])

    def test_cli_empty_duplicate_unknown_and_mixed_all_are_argument_errors(self):
        for selection in ("", ",", "links,,tasks", "links,links", "all,links", "ALL", "unknown", "links,"):
            with self.subTest(selection=selection):
                result = self.cli("--checks", selection, "--json")
                self.assertEqual(2, result.returncode, result.stdout + result.stderr)
                self.assertFalse(result.stdout)

    def test_cli_all_is_deterministic_and_does_not_write_fixture_files(self):
        import hashlib
        self.live()
        self.audit_fixture()
        before = {str(path.relative_to(self.root)): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in self.root.rglob("*") if path.is_file()}
        first = self.cli("--json")
        second = self.cli("--json")
        self.assertEqual(0, first.returncode, first.stderr + first.stdout)
        self.assertEqual(first.stdout, second.stdout)
        after = {str(path.relative_to(self.root)): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        self.assertFalse(list(self.root.rglob("__pycache__")))

    def test_api_rejects_empty_duplicate_unknown_explicit_selections(self):
        for selection in ((), ("links", "links"), ("unknown",)):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                metadata.scan_docs(self.root, checks=selection)

    def test_cli_invalid_manifest_unicode_scalar_retains_structured_diagnostics(self):
        import json
        self.audit_fixture()
        self.write("Cargo.toml", '[workspace]\nmembers = ["\\ud800"]\n')
        result = self.cli("--checks", "unsafe", "--json")
        self.assertEqual(1, result.returncode)
        self.assertFalse(result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(any(x["path"] == "Cargo.toml" and x["code"] == "unsafe-scope" for x in report["findings"]))

    def test_record_header_literal_fields_do_not_supply_task_or_adr_metadata(self):
        for family, create, code, boundary in (("tasks", self.task, "task", "\n\n---"),
                                                ("adrs", self.adr, "adr", "\n\n## Context")):
            path = create()
            source = self.root / path
            original = source.read_text()
            begin = original.index("- **Status:")
            end = original.index(boundary)
            fields = original[begin:end]
            for opening, closing in ((" ```markdown\n", "\n ```"),
                                     ("   ~~~markdown\n", "\n   ~~~"),
                                     (' <div title="\n', '\n">Example</div>'),
                                     ('- **Note:** <a title="\n', '\n">Example</a>')):
                with self.subTest(family=family, opening=opening):
                    source.write_text(original[:begin] + opening + fields + closing + original[end:], encoding="utf-8")
                    report = self.rejects(family, code, path)
                    self.assertTrue(any("Missing metadata field: status" in finding.message for finding in report.findings))
            source.write_text(original, encoding="utf-8")

    def test_record_header_literal_duplicates_do_not_override_visible_fields(self):
        for family, create, boundary in (("tasks", self.task, "\n\n---"),
                                         ("adrs", self.adr, "\n\n## Context")):
            path = create()
            source = self.root / path
            original = source.read_text()
            for opening, closing in (("\n ```markdown\n", "\n ```"),
                                     ('\n- **Note:** <a title="\n', '\n">Example</a>')):
                with self.subTest(family=family, opening=opening):
                    duplicate = opening + "- **Status:** Invalid hidden state" + closing
                    source.write_text(original.replace(boundary, duplicate + boundary, 1), encoding="utf-8")
                    self.clean(family)
            source.write_text(original, encoding="utf-8")

    def test_live_html_attributes_do_not_supply_heading_or_metadata(self):
        source = self.live()
        original = source.read_text()
        heading = "## Live state — 2026-10-15"
        begin = original.index("- **Active phase:")
        end = original.index("\n\n| Task |")
        fields = original[begin:end]
        for tag in ("a", "span"):
            opening, closing = '<' + tag + ' title="\n', '\n">Example</' + tag + '>'
            variants = (original.replace(heading, opening + heading + closing),
                        original[:begin] + opening + fields + closing + original[end:])
            for text in variants:
                for newline in ("\n", "\r\n", "\r"):
                    with self.subTest(tag=tag, text=text, newline=newline):
                        source.write_bytes(text.replace("\n", newline).encode("utf-8"))
                        self.rejects("live", "live-state", "docs/roadmap/current.md")

    def test_live_html_attribute_duplicates_do_not_conflict_with_real_fields(self):
        source = self.live()
        original = source.read_text()
        for tag in ("a", "span"):
            hidden = '<' + tag + ' title="\n- **Selected track:** X-2, hidden.\n">Example</' + tag + '>\n\n'
            text = original.replace("## Live state", hidden + "## Live state", 1)
            for newline in ("\n", "\r\n", "\r"):
                with self.subTest(tag=tag, newline=newline):
                    source.write_bytes(text.replace("\n", newline).encode("utf-8"))
                    self.clean("live")

    def test_companion_html_attributes_cannot_exempt_unindexed_reports(self):
        path = self.review()
        folder = Path(path).parent
        plan = "2026-10-15-plan.md"
        self.write((folder / plan).as_posix(), "# Plan\n")
        index = self.root / folder / "README.md"
        original = index.read_text()
        heading = "## Companion plans"
        declaration = "- [Plan](" + plan + "), owned by the [review](" + Path(path).name + ")."
        for tag in ("a", "span"):
            opening, closing = '<' + tag + ' title="\n', '\n">Example</' + tag + '>'
            for text in (opening + heading + "\n\n" + declaration + closing,
                         opening + heading + closing + "\n\n" + declaration,
                         heading + "\n\n" + opening + declaration + closing):
                with self.subTest(tag=tag, text=text):
                    index.write_text(original + "\n" + text + "\n", encoding="utf-8")
                    self.rejects("reviews", "review-index")

    def test_companion_hidden_heading_does_not_disable_real_owner_declaration(self):
        path = self.review()
        folder = Path(path).parent
        plan = "2026-10-15-plan.md"
        self.write((folder / plan).as_posix(), "# Plan\n")
        index = self.root / folder / "README.md"
        original = index.read_text()
        for tag in ("a", "span"):
            text = ('\n## Companion plans\n\n<' + tag + ' title="\n## Hidden unrelated section\n">Example</' + tag + '>\n\n'
                    '- [Plan](' + plan + '), owned by the [review](' + Path(path).name + ').\n')
            with self.subTest(tag=tag):
                index.write_text(original + text, encoding="utf-8")
                self.clean("reviews")

    def clean(self, family):
        report = self.scan(family)
        self.assertFalse(report.findings, report.as_dict())
        self.assertEqual([family], report.as_dict()["checks"])
        return report

    def rejects(self, family, code, path=None):
        report = self.scan(family)
        found = [x for x in report.findings if x.code == code and (path is None or x.path == path)]
        self.assertTrue(found, report.as_dict())
        self.assertTrue(all(x.line >= 1 for x in report.findings))
        return report


if __name__ == "__main__":
    unittest.main()
