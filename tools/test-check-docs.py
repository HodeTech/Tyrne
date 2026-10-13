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
from unittest.mock import patch
from urllib.parse import quote

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

    def test_markdown_destinations_preserve_leading_scalars_and_actual_targets(self):
        for spelling, prefix in ((" ", " "), ("&#32;", " "), ("&#1;", "\x01"),
                                 ("&#31;", "\x1f"), ("%20", " ")):
            for form in ("[x](<{}foo.txt>)", "![x](<{}foo.txt>)",
                         "[x][ref]\n\n[ref]: <{}foo.txt>"):
                with self.subTest(spelling=spelling, form=form):
                    source = form.format(spelling) + "\n"
                    decoy = self.write("docs/foo.txt", "decoy")
                    self.check(source, ["path", "path"] if "[ref]:" in source else ["path"])
                    decoy.unlink()
                    actual = self.write("docs/" + prefix + "foo.txt", "actual")
                    self.check(source)
                    actual.unlink()

    def test_markdown_decoded_tabs_and_newlines_are_not_silently_deleted(self):
        for spelling, scalar in (("&#9;", "\t"), ("&#10;", "\n"), ("&#13;", "\r")):
            with self.subTest(spelling=spelling):
                self.write("docs/ab.txt", "decoy")
                self.check("[x](a" + spelling + "b.txt)\n", ["path"])
                actual = self.write("docs/a" + scalar + "b.txt", "actual")
                self.check("[x](a" + spelling + "b.txt)\n")
                actual.unlink()

    def test_html_url_normalization_is_explicit_and_percent_encoding_is_preserved(self):
        self.write("docs/foo.txt", "actual")
        for tag, attr in (("a", "href"), ("img", "src")):
            for spelling in (" foo.txt ", "&#1;foo.txt&#31;", "f&#9;o&#10;o&#13;.txt"):
                with self.subTest(tag=tag, spelling=spelling):
                    self.check('<' + tag + ' ' + attr + '="' + spelling + '">\n')
            self.check('<' + tag + ' ' + attr + '="%20foo.txt">\n', ["path"])
            actual = self.write("docs/ foo.txt", "encoded actual")
            self.check('<' + tag + ' ' + attr + '="%20foo.txt">\n')
            actual.unlink()

    def test_non_line_separators_cannot_manufacture_headings(self):
        for scalar in ("\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"):
            with self.subTest(scalar=repr(scalar)):
                result = self.check("# one" + scalar + "# phantom\n\n[x](#phantom)\n", ["fragment"])
                self.assertEqual(3, result.findings[0].line)

    def test_source_line_fragments_use_only_cr_lf_and_crlf(self):
        for scalar in ("\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"):
            with self.subTest(scalar=repr(scalar)):
                self.write("tools/sample.txt", "a" + scalar + "b")
                self.check("[x](../tools/sample.txt#L1)\n")
                self.check("[x](../tools/sample.txt#L2)\n", ["fragment"])
        for ending in ("\n", "\r", "\r\n"):
            with self.subTest(ending=repr(ending)):
                self.write("tools/sample.txt", "a" + ending + "b" + ending)
                self.check("[x](../tools/sample.txt#L1-L2)\n")
                self.check("[x](../tools/sample.txt#L3)\n", ["fragment"])

    def test_real_line_endings_share_heading_reference_fence_and_diagnostic_offsets(self):
        for ending in ("\n", "\r", "\r\n"):
            with self.subTest(ending=repr(ending)):
                text = "# one\n# real\n\n[x](#real)\n".replace("\n", ending)
                self.check(text)
                text = '```text\n[literal](missing)\n```\n\n[x][ref]\n\n[ref]: target.md\n'.replace("\n", ending)
                self.check(text)

    def test_real_line_endings_keep_markdown_and_html_diagnostic_lines(self):
        for ending in ("\n", "\r", "\r\n"):
            with self.subTest(ending=repr(ending)):
                result = self.check("before" + ending * 2 + "[x](missing)" + ending, ["path"])
                self.assertEqual(3, result.findings[0].line)
                result = self.check('<a' + ending + ' href="missing">x</a>' + ending, ["path"])
                self.assertEqual(2, result.findings[0].line)

    def test_invalid_utf8_uses_the_same_physical_line_model(self):
        for ending in (b"\n", b"\r", b"\r\n"):
            with self.subTest(ending=repr(ending)):
                (self.root / "docs/bad.md").write_bytes(b"before" + ending * 2 + b"\xff")
                result = docs.scan_links(self.root)
                self.assertEqual([(3, "read")], [(x.line, x.code) for x in result.findings])

    def test_traversal_and_symlink_escape_fail(self):
        self.check("[x](../../outside.md)\n", ["path"])
        outside = Path(self.temp.name).parent / (self.root.name + " outside.md")
        outside.write_text("# Outside\n", encoding="utf-8")
        self.addCleanup(outside.unlink)
        (self.root / "docs" / "escape.md").symlink_to(outside)
        result = self.check("[x](escape.md)\n", ["input", "path"])
        self.assertTrue(result.findings)
        (self.root / "docs/escape.md").unlink()
        (self.root / "docs/loop.md").symlink_to("loop.md")
        self.check("[x](loop.md)\n", ["input", "path"])

    def test_existing_local_only_notes_are_not_input_or_navigation(self):
        self.write("docs/analysis/private/notes.md", "[broken](missing.md)\n")
        self.write("docs/analysis/temp/draft.md", "[broken](missing.md)\n")
        self.write("docs/analysis/technical-analysis/notes.md", "[broken](missing.md)\n")
        self.check("[public](target.md)\n")
        self.check("[private](analysis/private/notes.md)\n", ["path"])
        (self.root / "alias").symlink_to(self.root / "docs/analysis/private", target_is_directory=True)
        self.check("[private via alias](../alias/notes.md#anything)\n", ["path"])

    def test_symlinked_input_roots_and_ancestors_are_never_read(self):
        for index, prefix in enumerate(("docs", ".agents", ".agents/skills", "docs/nested")):
            with self.subTest(prefix=prefix):
                root = self.root / ("case-" + str(index))
                root.mkdir()
                (root / "README.md").write_text("# Public\n", encoding="utf-8")
                outside = self.root / ("outside-" + str(index))
                outside.mkdir()
                (outside / "canary.md").write_text("[secret](private-canary.md)\n", encoding="utf-8")
                if prefix == ".agents":
                    (outside / "skills").mkdir()
                    (outside / "skills/canary.md").write_text("[secret](private-canary.md)\n", encoding="utf-8")
                link = root / prefix
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(outside, target_is_directory=True)
                original = docs.read_utf8

                def public_read(selected_root, path):
                    self.assertFalse((selected_root / path).resolve().is_relative_to(outside.resolve()))
                    return original(selected_root, path)

                with patch.object(docs, "read_utf8", side_effect=public_read):
                    result = docs.scan_links(root)
                self.assertTrue(any(x.code == "input" for x in result.findings), result)

    def test_local_only_input_aliases_never_read_canaries(self):
        for index, prefix in enumerate(docs.LOCAL_ONLY):
            with self.subTest(prefix=prefix):
                root = self.root / ("private-alias-" + str(index))
                root.mkdir()
                (root / "README.md").write_text("# Public\n", encoding="utf-8")
                private = root / prefix
                private.mkdir(parents=True)
                (private / "canary.md").write_text("[secret](missing.md)\n", encoding="utf-8")
                link = root / ".agents/skills"
                link.parent.mkdir()
                link.symlink_to(private, target_is_directory=True)
                original = docs.read_utf8

                def public_read(selected_root, path):
                    self.assertEqual("README.md", str(path))
                    return original(selected_root, path)

                with patch.object(docs, "read_utf8", side_effect=public_read):
                    result = docs.scan_links(root)
                self.assertTrue(any(x.code == "input" for x in result.findings), result)

    def test_dangling_loop_and_private_input_aliases_fail_before_read(self):
        for name, target in (("dangling", "absent"), ("loop", "docs"),
                             ("private", "notes")):
            with self.subTest(name=name):
                root = self.root / name
                root.mkdir()
                (root / "README.md").write_text("# Public\n", encoding="utf-8")
                if name == "private":
                    target_dir = root / "notes"
                    target_dir.mkdir()
                    (target_dir / "canary.md").write_text("[secret](missing.md)\n", encoding="utf-8")
                (root / "docs").symlink_to(target, target_is_directory=True)
                original = docs.read_utf8

                def public_read(selected_root, path):
                    self.assertEqual("README.md", str(path))
                    return original(selected_root, path)

                with patch.object(docs, "read_utf8", side_effect=public_read):
                    result = docs.scan_links(root)
                self.assertTrue(any(x.code == "input" for x in result.findings), result)

    def test_archive_and_skills_are_always_checked(self):
        self.write("docs/archive/old.md", "[broken](missing.md)\n")
        self.write(".agents/skills/example/SKILL.md", "[broken](missing.md)\n")
        self.check("[valid](target.md)\n", ["path", "path"])

    def test_public_markdown_is_not_excluded_by_generated_basename(self):
        for name in (".git", ".venv", "__pycache__"):
            with self.subTest(name=name):
                path = self.write("docs/" + name + "/public.md", "[bad](missing.md)\n")
                self.check("[valid](target.md)\n", ["path"])
                path.unlink()

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
        self.check("> ```text\n> [bad](missing.md)\n> ```\n\n- ~~~text\n  [bad](missing.md)\n  ~~~\n\n      [bad](missing.md)\n\n[real](target.md)\n")
        self.check("    [literal](missing.md)\n")

    def test_list_relative_fence_closures_and_mixed_containers(self):
        for indent in range(4):
            with self.subTest(indent=indent):
                self.check("- ```text\n  [literal](missing.md)\n" + " " * (2 + indent) +
                           "```\n  [real](missing.md)\n", ["path"])
        self.check("- > ```text\n  > [literal](missing.md)\n  > ```\n  > [real](missing.md)\n", ["path"])
        self.check("> - ```text\n>   [literal](missing.md)\n>     ```\n>   [real](missing.md)\n", ["path"])

    def test_excess_list_padding_retains_indented_code(self):
        self.check("-     [literal](missing.md)\n")
        self.check("- [real](missing.md)\n", ["path"])
        self.check("- prose\n\n    [real](missing.md)\n", ["path"])
        self.check("- prose\n\n      [literal](missing.md)\n")

    def test_quoted_reference_continuations_keep_original_lines(self):
        self.check('> [x][id]\n>\n> [id]:\n>   target.md\n>   "title"\n')
        result = self.check("> [x][id]\n>\n> [id]:\n>   missing.md\n", ["path", "path"])
        self.assertEqual([1, 3], [x.line for x in result.findings])
        self.check("> [x][id]\n>\n> [id]:\ntarget.md\n", ["reference", "link-syntax"])

    def test_empty_angle_reference_and_missing_destination_are_distinct(self):
        self.check('[x][id]\n\n[id]: <>\n')
        self.check('[x][id]\n\n[id]: <> "title"\n')
        self.check('[x][id]\n\n[id]:\n', ["reference", "link-syntax"])

    def test_image_marker_uses_backslash_parity(self):
        self.check(r"[outer \\![image](target.md)](target.md)")
        self.check(r"[outer \![inner](target.md)](target.md)", ["link-syntax"])

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

    def test_titles_and_attributes_do_not_create_links_anchors_or_comments(self):
        self.check('[x](target.md "<a href=\'missing.md\'>")\n')
        self.check('[x](target.md "<span id=\'fake\'>")\n[y](#fake)\n', ["fragment"])
        self.check('[x](target.md "literal <!--")\n[bad](missing.md)\n', ["path"])
        self.check('<span title="<!--">text</span>\n[bad](missing.md)\n', ["path"])
        self.check('[x][id]\n\n[id]: target.md "literal <!--"\n\n[bad](missing.md)\n', ["path"])
        self.check(r'\<span id="fake"> [x](#fake)', ["fragment"])
        self.check(r'\<a href="missing.md">literal</a>')
        self.check(r'\\<a href="missing.md">real</a>', ["path"])
        self.check('\\<!-- literal\n<a href="missing.md">real</a>\n', ["path"])

    def test_html_attribute_decoding_is_once_and_not_markdown_escaping(self):
        for tag, attr in (("a", "href"), ("img", "src")):
            with self.subTest(tag=tag):
                decoy = self.write("docs/a&b.md", "# Héllo\n")
                text = '<' + tag + ' ' + attr + '="a&amp;amp;b.md#h%C3%A9llo">\n'
                self.check(text, ["path"])
                decoy.unlink()
                actual = self.write("docs/a&amp;b.md", "# Héllo\n")
                self.check(text)
                actual.unlink()
                actual = self.write("docs/a\\!b.md", "# Target\n")
                self.check('<' + tag + ' ' + attr + '="a\\!b.md">\n')
                actual.unlink()

    def test_html_named_references_follow_attribute_context(self):
        for tag, attr in (("a", "href"), ("img", "src")):
            for spelling, actual, decoy in (("a&notit;.md", "a&notit;.md", "a¬it;.md"),
                                            ("a&copyx.md", "a&copyx.md", "a©x.md"),
                                            ("a&copy=.md", "a&copy=.md", "a©=.md")):
                with self.subTest(tag=tag, spelling=spelling):
                    wrong = self.write("docs/" + decoy, "# Decoy\n")
                    text = '<' + tag + ' ' + attr + '="' + spelling + '">\n'
                    self.check(text, ["path"])
                    wrong.unlink()
                    right = self.write("docs/" + actual, "# Actual\n")
                    self.check(text)
                    right.unlink()
        self.write("docs/a©.md", "# Héllo\n")
        self.check('<a href="a&copy.md#h%C3%A9llo">x</a>\n')
        self.check('<a href="a&#169;.md">x</a><img src="a&#xA9;.md">\n')
        self.check('<span id="a&copyx"></span>[x](#a&copyx)\n')

    def test_raw_html_attributes_retain_quotes_case_lines_and_first_value(self):
        self.check('<A HREF=target.md TITLE="a > b">x</A><img src=target.md>\n')
        self.check('<span hidden id=custom></span>[x](#custom)\n')
        result = self.check('<a\n href="missing.md">x</a>\n', ["path"])
        self.assertEqual(2, result.findings[0].line)
        self.check('<span id="real" id="fake"></span>[x](#fake)\n', ["fragment", "link-syntax"])

    def test_markdown_entities_require_complete_names_and_escape_precedence(self):
        for spelling, actual, decoy in (("a&copyx.md", "a&copyx.md", "a©x.md"),
                                        ("a&notit;.md", "a&notit;.md", "a¬it;.md"),
                                        (r"a\&copy;.md", "a&copy;.md", "a©.md")):
            with self.subTest(spelling=spelling):
                wrong = self.write("docs/" + decoy, "# Decoy\n")
                text = "[x](" + spelling + ")\n"
                self.check(text, ["path"])
                wrong.unlink()
                right = self.write("docs/" + actual, "# Actual\n")
                self.check(text)
                right.unlink()
        self.write("docs/a©.md", "# Actual\n")
        self.check("[x](a&copy;.md) [y](a&#169;.md) [z](a&#xA9;.md)\n")
        self.check("# &notit;\n# &#00000169;\n[a](#notit) [b](#00000169)\n")

    def test_template_html_without_navigation_does_not_create_syntax_findings(self):
        self.check('<A / B / C / …>\n<comma-separated tasks, or "none">\n')
        self.check('<A / B / C / …>\n[real](missing.md)\n', ["path"])

    def test_numeric_references_preserve_noncharacter_and_control_anchors(self):
        for spelling, scalar in (("&#xFDD0;", "\ufdd0"), ("&#65535;", "\uffff"),
                                 ("&#x10FFFF;", "\U0010ffff"), ("&#11;", "\x0b"),
                                 ("&#127;", "\x7f"), ("&#x81;", "\x81")):
            for tag, attr in (("span", "id"), ("a", "name")):
                anchor = '<' + tag + ' ' + attr + '="a' + spelling + 'b"></' + tag + '>\n'
                for destination, expected in (("#ab", ["fragment"]),
                                              ("#a" + quote(scalar) + "b", []),
                                              ("#a" + spelling + "b", [])):
                    with self.subTest(spelling=spelling, attr=attr, destination=destination):
                        self.check(anchor + '[x](' + destination + ')\n', expected)

    def test_numeric_noncharacter_destination_cannot_accept_deleted_scalar_decoy(self):
        self.write("docs/ab.md", "# Decoy\n")
        for text in ('<a href="a&#xFDD0;b.md">x</a>\n',
                     '<img src="a&#xFDD0;b.md">\n', '[x](a&#xFDD0;b.md)\n',
                     '[x][ref]\n\n[ref]: a&#xFDD0;b.md\n'):
            with self.subTest(text=text):
                self.check(text, ["path", "path"] if "[ref]:" in text else ["path"])

    def test_numeric_replacement_and_source_specific_legacy_values(self):
        for spelling in ("&#0;", "&#xD800;", "&#xDFFF;", "&#x110000;", "&#9999999;"):
            with self.subTest(spelling=spelling):
                self.check('<span id="a' + spelling + 'b"></span>\n'
                           '[x](#a%EF%BF%BDb) [y](#a' + spelling + 'b)\n')
        # CommonMark numeric values denote their Unicode scalar. HTML alone
        # has legacy C1 remapping; test the boundary with real anchor lookup.
        self.check('<span id="a&#128;b"></span>\n[x](#a%E2%82%ACb)\n')
        self.check('<span id="a&#128;b"></span>\n[x](#a&#128;b)\n', ["fragment"])
        self.check('<span id="a\x80b"></span>\n[x](#a&#128;b)\n')
        self.check('<span id="a\x80b"></span>\n<a href="#a&#128;b">x</a>\n', ["fragment"])
        self.check('<span id="a&#x9F;b"></span>\n[x](#a%C5%B8b)\n')

    def test_long_html_numeric_references_have_bounded_conversion(self):
        for digits, fragment in (("9" * 100_000, "%EF%BF%BD"),
                                 ("0" * 100_000 + "169", "%C2%A9")):
            with self.subTest(fragment=fragment):
                self.write("docs/source.md", '<span id="a&#' + digits + ';b"></span>\n'
                           '[x](#a' + fragment + 'b)\n')
                result = self.cli("--root", str(self.root), "--json", timeout=5)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_heading_code_and_literal_underscores_survive_markup(self):
        self.check('# `<word>`\n# `_secret_`\n# `_secret_`\n# __bold__\n# \\_literal\\_\n'
                   '[a](#word) [b](#_secret_) [c](#_secret_-1) [d](#bold) [e](#_literal_)\n')
        self.check('# `_secret_`\n[x](#secret)\n', ["fragment"])

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

    def cli(self, *args, cwd=None, timeout=20):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd,
                              capture_output=True, text=True, timeout=timeout,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PATH=""))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "Host has no FIFO support")
    def test_special_files_are_rejected_without_blocking(self):
        fifo = self.root / "docs/blocked.md"
        os.mkfifo(fifo)
        result = self.cli("--root", str(self.root), "--json", timeout=2)
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertTrue(json.loads(result.stdout)["findings"])
        fifo.unlink()
        target = self.root / "docs/blocked.txt"
        os.mkfifo(target)
        self.write("README.md", "[source](docs/blocked.txt#L1)\n")
        result = self.cli("--root", str(self.root), "--json", timeout=2)
        self.assertEqual(1, result.returncode, result.stderr)

    def test_large_titles_and_unmatched_runs_terminate_with_correct_results(self):
        self.write("docs/source.md", '[x](target.md "' + "a" * 2_000_000 + '")\n')
        self.assertEqual(0, self.cli("--root", str(self.root)).returncode)
        self.write("docs/source.md", " ".join("`" * i + "x" for i in range(1, 1001)) +
                   "\n[bad](missing.md)\n")
        result = self.cli("--root", str(self.root), "--json")
        self.assertEqual(1, result.returncode)
        self.assertEqual(["path"], [x["code"] for x in json.loads(result.stdout)["findings"]])

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
