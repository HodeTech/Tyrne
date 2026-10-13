#!/usr/bin/env python3
"""Isolated contract fixtures for offline documentation consistency checks."""

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
import docs_consistency as docs

SCRIPT = Path(__file__).with_name("check-docs.py").resolve()


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tyrne docs with spaces ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write("README.md", "# Start\n")
        self.write("docs/target.md", "# Target\n\n## Hello world\n")

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def check(self, text, expected=()):
        self.write("docs/source.md", text)
        result = docs.scan_links(self.root)
        self.assertEqual(list(expected), [x.code for x in result.findings], result.findings)
        return result

    def test_inline_image_reference_collapsed_and_shortcut(self):
        self.write("docs/picture.png", "fixture image bytes")
        text = """[inline](target.md#hello-world "title") ![image](picture.png)
[full][ Ref ] [collapsed][] [shortcut] [undefined prose]

[ref]: target.md
[collapsed]: target.md#target 'title'
[shortcut]: ../README.md
"""
        result = self.check(text)
        self.assertGreaterEqual(result.local_targets, 6)

    def test_balanced_and_escaped_labels_and_destinations(self):
        self.write("docs/part(one).md", "# Part\n")
        self.check(r"[outer [inner]](part(one).md) [escaped \[label\]](part\(one\).md)")

    def test_images_in_link_labels_remain_checked(self):
        self.check("[outer ![image](absent.png)](target.md)\n", ["path"])
        self.check("[outer ![image][img]][target]\n\n[img]: absent.png\n[target]: target.md\n", ["path", "path"])
        self.check("[outer [inner](target.md)](target.md)\n", ["link-syntax"])

    def test_angle_spaces_title_entities_and_percent_encoding(self):
        self.write("docs/a b&c.md", "# Héllo\n")
        self.check('[x](<a b&amp;c.md> "title") [y](a%20b%26c.md#h%C3%A9llo)')

    def test_empty_destinations_and_title_only_links(self):
        self.check('[one]() [two](<> "title") [three]( "title" )\n')

    def test_reference_normalization_is_raw_casefold_and_whitespace(self):
        self.check("[one][ẞ]\n[two][multi\n line]\n\n[SS]: target.md\n[multi line]: target.md\n")
        self.check("[x][foo\\!]\n\n[foo!]: target.md\n", ["reference"])

    def test_duplicate_and_undefined_explicit_references(self):
        self.check("[x][missing] [y][]\n", ["reference", "reference"])
        self.check("[one]: target.md\n[ONE]: ../README.md\n", ["reference"])

    def test_historical_reference_syntax_is_explicit_literal_data(self):
        self.check('*"historical [ADR][missing] quotation"*\n', ["reference"])
        self.check('*`"historical [ADR][missing] quotation"`*\n')
        self.check('*`"historical [ADR title\ncontinued][missing] quotation"`*\n')

    def test_reference_destination_and_title_continuations(self):
        self.check('[x][id]\n\n[id]:\n  <target.md>\n  "wrapped title"\n')

    def test_reference_definition_cannot_interrupt_prose(self):
        self.check("Paragraph\n[id]: target.md\n", ["link-syntax"])
        self.check("Paragraph\n\n[id]: target.md\n\n[x][id]\n")

    def test_reference_definition_checked_even_when_unused(self):
        self.check("[unused]: absent.md\n", ["path"])

    def test_same_file_unicode_and_duplicate_headings(self):
        self.check("""# Héllo 世界
## Repeat
## Repeat
## Repeat-1
[one](#héllo-世界) [two](#repeat-1) [three](#repeat-1-1)
""")

    def test_heading_markup_and_inline_code_keep_underscores(self):
        self.check("## A `write_bytes` and **bold** [label](target.md)\n[x](#a-write_bytes-and-bold-label)\n")

    def test_setext_heading_and_explicit_html_anchors(self):
        self.check('Setext title\n============\n<a name="custom"></a><span id="Ünicode"></span>\n[x](#setext-title) [y](#custom) [z](#%C3%9Cnicode)\n')

    def test_custom_anchor_does_not_consume_heading_suffix(self):
        self.check('<a id="repeat"></a>\n# Repeat\n# Repeat\n[x](#repeat-1)\n')

    def test_fragment_missing_is_not_file_success(self):
        self.check("[x](target.md#absent)\n", ["fragment"])

    def test_source_line_bounds_and_range_order(self):
        self.write("tools/sample.rs", "first\nsecond\nthird\n")
        self.check("[x](../tools/sample.rs#L1-L3) [y](../tools/sample.rs#L2)\n")
        for fragment in ("L0", "L4", "L3-L2", "L1-L4"):
            with self.subTest(fragment=fragment):
                self.check("[x](../tools/sample.rs#" + fragment + ")\n", ["fragment"])

    def test_files_directories_repository_root_and_queries(self):
        self.write("docs/folder/README.md", "# Folder\n")
        (self.root / "empty").mkdir()
        self.check("[root](/README.md#start) [dir](folder/#folder) [empty](../empty/) [query](target.md?plain=1#target)\n")

    def test_case_sensitive_paths_even_on_case_insensitive_host(self):
        self.write("docs/Case.md", "# Case\n")
        self.check("[x](case.md)\n", ["path"])
        self.check("[x](Case.md)\n")

    def test_external_uris_never_fetched(self):
        self.check("[x](https://invalid.example/absent#bad) [y](mailto:no@example.invalid) [z](//invalid.example/missing)\n")

    def test_traversal_and_symlink_escape_fail(self):
        self.check("[x](../../outside.md)\n", ["path"])
        outside = Path(self.temp.name).parent / (self.root.name + " outside.md")
        outside.write_text("# Outside\n", encoding="utf-8")
        self.addCleanup(outside.unlink)
        (self.root / "docs" / "escape.md").symlink_to(outside)
        result = self.check("[x](escape.md)\n", ["input", "path"])
        self.assertTrue(result.findings)

    def test_existing_local_only_notes_are_not_input_or_navigation(self):
        self.write("docs/analysis/private/notes.md", "[broken](missing.md)\n")
        self.write("docs/analysis/temp/draft.md", "[broken](missing.md)\n")
        self.write("docs/analysis/technical-analysis/notes.md", "[broken](missing.md)\n")
        self.check("[public](target.md)\n")
        self.check("[private](analysis/private/notes.md)\n", ["path"])
        (self.root / "alias").symlink_to(self.root / "docs/analysis/private", target_is_directory=True)
        self.check("[private via alias](../alias/notes.md#anything)\n", ["path"])

    def test_archive_and_skills_are_always_checked(self):
        self.write("docs/archive/old.md", "[broken](missing.md)\n")
        self.write(".agents/skills/example/SKILL.md", "[broken](missing.md)\n")
        self.check("[valid](target.md)\n", ["path", "path"])

    def test_fences_match_character_and_minimum_length(self):
        self.check("""````text
[bad](missing.md)
```
[still bad](missing.md)
````
~~~text
[bad](missing.md)
```
~~~
[real](target.md)
""")
        self.check("````text\n[bad](missing.md)\n````\n[real](missing.md)\n", ["path"])

    def test_quote_and_list_fences_and_indented_code(self):
        self.check("> ```text\n> [bad](missing.md)\n> ```\n\n- ~~~text\n  [bad](missing.md)\n  ~~~\n\n    [bad](missing.md)\n\n[real](target.md)\n")

    def test_indented_paragraph_continuation_is_not_code(self):
        self.check("Paragraph\n    [real](missing.md)\n", ["path"])

    def test_code_spans_match_runs_and_may_cross_soft_break(self):
        self.check("``literal ` [bad](missing.md)``\n`soft\n[bad](missing.md)`\n[real](target.md)\n")
        self.check("Unmatched ` [real](missing.md)\n", ["path"])
        self.check("`unmatched\n\n[real](missing.md)`\n", ["path"])

    def test_comment_and_code_span_precedence(self):
        self.check("`<!-- literal`\n[real](target.md)\n<!-- [bad](missing.md) -->\n")
        self.check("<!-- ignored -->\n[real](missing.md)\n", ["path"])
        self.check("<!--\n[id]: missing.md\n```text\n-->\n[real](target.md)\n")
        self.check("Text <!--\n[id]: missing.md\n-->\n[real](target.md)\n")
        self.check("<!--\n```text\n-->\n[real](missing.md)\n", ["path"])

    def test_code_spans_do_not_cross_markdown_block_boundaries(self):
        for boundary in ("- ", "# ", "> "):
            with self.subTest(boundary=boundary):
                self.check("Unmatched `\n" + boundary + "[real](missing.md)`\n", ["path"])
        # Historical review quotes contain escaped backticks inside code data.
        # A new list item is a new block, even without an intervening blank line.
        text = '- **Doc:** quoted `| \\`field\\` |`\n- **Suggested:** `| [\\`file\\`](missing.md) |`\n'
        self.check(text)

    def test_escaped_markers_are_literal(self):
        self.check(r"\[literal](missing.md) \`unmatched [real](target.md)")

    def test_actual_html_links_and_images(self):
        self.write("docs/img.png", "image")
        self.check('<a href="target.md#target">target</a><img src="img.png">\n')
        self.check('<a href="missing.md">bad</a>\n', ["path"])

    def test_malformed_relevant_forms_do_not_disappear(self):
        for text in ("[x](<target.md)", "[x](target.md bad title)", "[x](target.md", "[x][missing", "[id]: <target.md"):
            with self.subTest(text=text):
                result = docs.Markdown("docs/source.md", text)
                self.assertTrue(result.findings, text)
                self.assertTrue(all(x.code in ("link-syntax", "reference") for x in result.findings))

    def test_supported_nesting_limits_fail_visibly(self):
        self.check("[" * 65 + "label" + "]" * 65 + "(target.md)", ["link-syntax"])
        self.check("[x](" + "(" * 65 + "target.md" + ")" * 65 + ")", ["link-syntax"])

    def test_invalid_utf8_and_malformed_percent_encoding(self):
        self.check("[x](target.md%ZZ)\n", ["path"])
        (self.root / "docs" / "bad.md").write_bytes(b"# Good\n\xff")
        result = docs.scan_links(self.root)
        self.assertTrue(any(x.code == "read" and x.line == 2 for x in result.findings))

    def test_diagnostics_are_source_ordered_and_keep_line_offsets(self):
        result = self.check("~~~text\n[ignored](absent.md)\n~~~\n\n[bad](missing.md)\n[fragment](target.md#no)\n", ["path", "fragment"])
        self.assertEqual([5, 6], [x.line for x in result.findings])

    def test_no_private_or_generated_file_writes(self):
        self.write("docs/source.md", "[x](target.md)\n")
        before = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob("*") if p.is_file()}
        self.assertFalse(docs.scan_links(self.root).findings)
        after = {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def cli(self, *args, cwd=None):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd,
                              capture_output=True, text=True, timeout=20,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PATH=""))

    def test_cli_fixture_root_outside_cwd_without_git(self):
        result = self.cli("--root", str(self.root), "--json", cwd=self.root.parent)
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["ok"])
        self.assertEqual(["links"], report["checks"])
        self.assertFalse((self.root / "__pycache__").exists())

    def test_cli_invalid_root_args_and_inconsistency_are_nonzero(self):
        for args in (("--root", str(self.root / "missing")), ("--checks", "unknown"), ("--unknown",)):
            with self.subTest(args=args):
                self.assertNotEqual(0, self.cli(*args).returncode)
        self.write("README.md", "[x](missing.md)\n")
        result = self.cli("--root", str(self.root))
        self.assertEqual(1, result.returncode)
        self.assertIn("README.md:1:", result.stdout)

    def test_cli_output_is_deterministic(self):
        self.write("docs/z.md", "[bad](absent.md)\n")
        self.write("docs/a.md", "[bad](absent.md)\n")
        a = self.cli("--root", str(self.root), "--json")
        b = self.cli("--root", str(self.root), "--json")
        self.assertEqual(a.stdout, b.stdout)
        paths = [x["path"] for x in json.loads(a.stdout)["findings"]]
        self.assertEqual(sorted(paths), paths)

    def test_python39_syntax_contract(self):
        for path in (SCRIPT, Path(docs.__file__), Path(__file__)):
            with self.subTest(path=path):
                ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 9))


if __name__ == "__main__":
    unittest.main()
