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
