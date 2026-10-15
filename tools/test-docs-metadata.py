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

    def scan(self, family):
        return metadata.scan_docs(self.root, checks=(family,))

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
