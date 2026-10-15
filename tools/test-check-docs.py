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

    def test_heading_emphasis_keeps_original_markup_neighbors(self):
        for ending in ('\n', '\r', '\r\n'):
            for markup in ('<span></span>', '<!--x-->'):
                for marker in ('_', '__'):
                    for atx in (True, False):
                        with self.subTest(ending=repr(ending), markup=markup, marker=marker, atx=atx):
                            title = marker + 'a' + marker + markup + marker + 'b' + marker
                            body = '# ' + title + '\n' if atx else title + '\n---\n'
                            phantom = 'a' + marker * 2 + 'b'
                            line = len(docs.physical_lines(body * 2)) + 2
                            result = self.check((body * 2 + '\n[real](#ab) [duplicate](#ab-1) [phantom](#' + phantom + ')\n').replace('\n', ending), ['fragment'])
                            self.assertEqual([(line, 'Missing Markdown/HTML anchor: ' + phantom)],
                                             [(item.line, item.message) for item in result.findings])

    def test_heading_emphasis_after_markup_keeps_source_punctuation(self):
        for ending in ('\n', '\r', '\r\n'):
            for markup in ('<!--x-->', '<span></span>', '<!--\nx\n-->'):
                for atx in (True, False):
                    if atx and '\n' in markup:
                        continue
                    with self.subTest(ending=repr(ending), markup=markup, atx=atx):
                        title = 'Alpha' + markup + '_Beta_'
                        body = '# ' + title + '\n' if atx else title + '\n---\n'
                        line = len(docs.physical_lines(body)) + 2
                        result = self.check((body + '\n[real](#alphabeta) [phantom](#alpha_beta_)\n').replace('\n', ending), ['fragment'])
                        self.assertEqual([(line, 'Missing Markdown/HTML anchor: alpha_beta_')],
                                         [(item.line, item.message) for item in result.findings])

    def test_heading_multiline_code_keeps_literal_edge_spaces(self):
        cases = (('Alpha `a  \nb`\n---\n', 'alpha-a---b'),
                 ('Alpha `a\n  b`\n---\n', 'alpha-a-b'),
                 ('Alpha `a  \n  b`\n---\n', 'alpha-a---b'),
                 ('Alpha `` a  \nb ``\n---\n', 'alpha-a---b'),
                 ('> Alpha `a  \n> b`\n> ---\n', 'alpha-a---b'),
                 ('- Alpha `a  \n  b`\n  ---\n', 'alpha-a---b'),
                 ('-\tAlpha `a  \n\tb`\n\t---\n', 'alpha-a---b'))
        for ending in ('\n', '\r', '\r\n'):
            for body, real in cases:
                with self.subTest(ending=repr(ending), body=body):
                    line = len(docs.physical_lines(body)) + 2
                    phantom = 'alpha-a-b' if real != 'alpha-a-b' else 'alpha-a---b'
                    result = self.check((body + '\n[real](#' + real + ') [phantom](#' + phantom + ')\n').replace('\n', ending), ['fragment'])
                    self.assertEqual([(line, 'Missing Markdown/HTML anchor: ' + phantom)],
                                     [(item.line, item.message) for item in result.findings])

    def test_heading_source_context_preserves_literal_tokens(self):
        for ending in ('\n', '\r', '\r\n'):
            for body, anchor in (('# Alpha_Beta_\n', 'alpha_beta_'),
                                  ('# Alpha\\_Beta\\_\n', 'alpha_beta_'),
                                  ('# `_a_`<span></span>`_b_`\n', '_a__b_'),
                                  ('# _a_ _b_\n', 'a-b'),
                                  ('# _&#65;_\n', 'a'),
                                  ('# _a_\\<span>_b_\n', 'aspanb'),
                                  ('Alpha `a\nb`\n---\n', 'alpha-a-b'),
                                  ('# Alpha `a   b`\n', 'alpha-a---b')):
                with self.subTest(ending=repr(ending), body=body):
                    self.check((body + '\n[real](#' + anchor + ')\n').replace('\n', ending))

    def test_heading_emphasis_uses_markdown_whitespace_classes(self):
        for char in ('\v', '\x1c', '\x1d', '\x1e', '\x1f', '\x85', '\u2028', '\u2029'):
            with self.subTest(char=repr(char)):
                result = self.check('# _a_' + char + '_b_\n\n[real](#a__b) [phantom](#ab)\n', ['fragment'])
                self.assertEqual([(3, 'Missing Markdown/HTML anchor: ab')],
                                 [(item.line, item.message) for item in result.findings])

    def heading_pair(self, title, real, phantom, ending, atx, local_targets=2):
        """Check independently specified real/phantom anchors through the CLI."""
        body = '# ' + title + '\n' if atx else title + '\n---\n'
        line = len(docs.physical_lines(body)) + 2
        source = body + '\n[real](#' + real + ') [phantom](#' + phantom + ')\n'
        self.write('docs/source.md', source.replace('\n', ending))
        expected = {'checks': ['links'], 'ok': False, 'files': 3,
                    'local_targets': local_targets, 'fragments': 2,
                    'findings': [{'path': 'docs/source.md', 'line': line, 'code': 'fragment',
                                  'message': 'Missing Markdown/HTML anchor: ' + phantom}]}
        result = self.cli('--root', str(self.root), '--json')
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual('', result.stderr)
        self.assertEqual(expected, json.loads(result.stdout))

    def test_heading_crossing_emphasis_preserves_unmatched_underscores(self):
        for ending in ('\n', '\r', '\r\n'):
            for atx in (True, False):
                for title, real, phantom in (
                        ('*foo _bar* baz_', 'foo-_bar-baz_', 'foo-bar-baz'),
                        ('_foo *bar_ baz*', 'foo-bar-baz', '_foo-bar_-baz'),
                        ('**foo _bar_ baz**', 'foo-bar-baz', 'foo-_bar_-baz'),
                        ('*foo `_bar_` baz*', 'foo-_bar_-baz', 'foo-bar-baz'),
                        (r'*foo \_bar\_ baz*', 'foo-_bar_-baz', 'foo-bar-baz'),
                        ('*[foo _bar_](target.md) baz*', 'foo-bar-baz', 'foo-_bar_-baz')):
                    with self.subTest(ending=repr(ending), atx=atx, title=title):
                        # A real label also contributes its target to the report.
                        self.heading_pair(title, real, phantom, ending, atx,
                                          3 if '(target.md)' in title else 2)

    def test_heading_code_spans_keep_original_token_boundaries(self):
        for ending in ('\n', '\r', '\r\n'):
            for atx in (True, False):
                for title, real, phantom in (
                        ('` a `<!--x-->` b `', 'ab', 'a--b'),
                        ('` a `<span></span>` b `', 'ab', 'a--b'),
                        ('`a`<!--x-->` b `', 'ab', 'a-b-'),
                        ('` a `<!--x-->`` b ``', 'ab', 'a--b'),
                        ('` a ` ` b `', 'a-b', 'ab'),
                        ('` a  b `', 'a--b', 'ab')):
                    with self.subTest(ending=repr(ending), atx=atx, title=title):
                        self.heading_pair(title, real, phantom, ending, atx)

    def test_heading_projection_cannot_create_new_inline_syntax(self):
        for ending in ('\n', '\r', '\r\n'):
            for atx in (True, False):
                for title, real, phantom in (
                        ('Alpha &<!--x-->amp; Beta', 'alpha-amp-beta', 'alpha--beta'),
                        ('Alpha [a]<!--x-->(target.md)', 'alpha-atargetmd', 'alpha-a'),
                        ('Alpha [a]<!--x-->[b]', 'alpha-ab', 'alpha-a'),
                        ('Alpha<sp<!--x-->an>Beta', 'alphaspanbeta', 'alphabeta')):
                    with self.subTest(ending=repr(ending), atx=atx, title=title):
                        self.heading_pair(title, real, phantom, ending, atx)

    def test_comment_mask_cannot_manufacture_html_navigation(self):
        for ending in ('\n', '\r', '\r\n'):
            with self.subTest(ending=repr(ending)):
                result = self.check(('<sp<!--x-->an id="ghost">\n\n'
                                     '[phantom](#ghost)\n<span id="real"></span>\n'
                                     '[real](#real)\n').replace('\n', ending), ['fragment'])
                self.assertEqual([(3, 'Missing Markdown/HTML anchor: ghost')],
                                 [(item.line, item.message) for item in result.findings])

    def test_heading_autolink_text_is_literal_to_emphasis(self):
        for ending in ('\n', '\r', '\r\n'):
            for atx in (True, False):
                with self.subTest(ending=repr(ending), atx=atx):
                    self.heading_pair('__a<https://foo.bar/?q=__>', '__ahttpsfoobarq__',
                                      'ahttpsfoobarq', ending, atx)

    def test_heading_autolink_labels_keep_brackets_literal(self):
        for ending in ('\n', '\r', '\r\n'):
            for title, anchor in (
                    ('<first_last@example.test>', 'first_lastexampletest'),
                    ('<https://example.test/?q=_x_>', 'httpsexampletestq_x_'),
                    ('<https://example.test/?q=&amp;>', 'httpsexampletestqamp'),
                    ('[<https://example.test/a]>](target.md)', 'httpsexampletesta')):
                with self.subTest(ending=repr(ending), title=title):
                    self.check(('# ' + title + '\n\n[x](#' + anchor + ')\n').replace('\n', ending))

    def test_uri_autolinks_exclude_ascii_controls_and_space(self):
        controls = [chr(value) for value in range(33) if value not in (10, 13)] + ['\x7f']
        for char in controls:
            with self.subTest(control=repr(char)):
                parsed = docs.Markdown('README.md', '# <https://a/' + char + '/_x_>\n')
                self.assertEqual({'httpsa-x' if char == ' ' else 'httpsax'}, parsed.anchors)
        for char in ('\x80', '\x85', '\xa0', '\u2028'):
            with self.subTest(non_ascii=repr(char)):
                parsed = docs.Markdown('README.md', '# <https://a/' + char + '/_x_>\n')
                self.assertEqual({'httpsa_x_'}, parsed.anchors)
        for ending in ('\n', '\r', '\r\n'):
            for atx in (True, False):
                with self.subTest(ending=repr(ending), atx=atx):
                    self.heading_pair('<https://a/\x7f/_x_>', 'httpsax', 'httpsa_x_', ending, atx)

    def test_invalid_del_autolink_keeps_real_file_links_active(self):
        for ending in ('\n', '\r', '\r\n'):
            for char in ('\x7f', '%7F', '\x85'):
                with self.subTest(ending=repr(ending), body=repr(char)):
                    self.write('docs/source.md', '<https://a/' + char + '/[bad](missing.md)>' + ending)
                    invalid = char == '\x7f'
                    expected = {'checks': ['links'], 'ok': not invalid, 'files': 3,
                                'local_targets': int(invalid), 'fragments': 0,
                                'findings': ([{'path': 'docs/source.md', 'line': 1, 'code': 'path',
                                              'message': 'Missing or case-mismatched local target: docs/missing.md'}]
                                             if invalid else [])}
                    result = self.cli('--root', str(self.root), '--json')
                    self.assertEqual(int(invalid), result.returncode, result.stdout + result.stderr)
                    self.assertEqual('', result.stderr)
                    self.assertEqual(expected, json.loads(result.stdout))

    def test_failed_emphasis_searches_do_not_rescan_unmatched_prefixes(self):
        self.assertEqual('_a b* c', docs.inline_text('_a b* *c*'))
        self.assertEqual('*a b_ c', docs.inline_text('*a b_ _c_'))
        for opener, closer in (('*', '_'), ('_', '*')):
            with self.subTest(opener=opener, closer=closer):
                source = '# ' + (opener + 'a ') * 32000 + ('b' + closer + ' ') * 32000
                self.write('docs/source.md', source + '\n\n# End\n\n[x](#end)\n')
                result = self.cli('--root', str(self.root), '--json', timeout=5)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertEqual('', result.stderr)
                self.assertEqual({'checks': ['links'], 'ok': True, 'files': 3,
                                  'local_targets': 1, 'fragments': 1, 'findings': []},
                                 json.loads(result.stdout))

    def test_tabbed_list_setext_uses_visual_container_columns(self):
        for ending in ('\n', '\r', '\r\n'):
            for body in ('-\tAlpha\n\t---\n', '-\tAlpha\n    ---\n',
                         '- Alpha\n\t---\n', '-   Alpha\n    ---\n',
                         '- Alpha\n  ---\n', '>\tAlpha\n>\t---\n'):
                with self.subTest(ending=repr(ending), body=body):
                    self.check((body + '\n[real](#alpha)\n').replace('\n', ending))
            with self.subTest(ending=repr(ending), outdented=True):
                result = self.check('-\tAlpha\n  ---\n\n[phantom](#alpha)\n'.replace('\n', ending), ['fragment'])
                self.assertEqual([(4, 'Missing Markdown/HTML anchor: alpha')],
                                 [(item.line, item.message) for item in result.findings])

    def test_tabbed_list_paragraph_keeps_inline_literal_context(self):
        for ending in ('\n', '\r', '\r\n'):
            for body in ('-\tprose <!--\n\t[literal](missing.md) -->\n',
                         '-\tprose `\n\t[literal](missing.md) `\n'):
                with self.subTest(ending=repr(ending), body=body):
                    self.check(body.replace('\n', ending))
            with self.subTest(ending=repr(ending), phantom=True):
                result = self.check('-\tprose <!--\n\t<span id="ghost"></span> -->\n\n[phantom](#ghost)\n'.replace('\n', ending), ['fragment'])
                self.assertEqual([(4, 'Missing Markdown/HTML anchor: ghost')],
                                 [(item.line, item.message) for item in result.findings])

    def test_outer_ordered_sibling_ends_nested_quote_inline_context(self):
        for ending in ('\n', '\r', '\r\n'):
            for body in ('1. > prose <!--\n2. [real](missing.md) -->\n',
                         '1. > prose `\n2. [real](missing.md)`\n',
                         '1) > prose <!--\n2) [real](missing.md) -->\n',
                         '1. > > prose <!--\n2. [real](missing.md) -->\n'):
                with self.subTest(ending=repr(ending), body=body):
                    result = self.check(body.replace('\n', ending), ['path'])
                    self.assertEqual([(2, 'Missing or case-mismatched local target: docs/missing.md')],
                                     [(item.line, item.message) for item in result.findings])
            for body in ('1. > prose <!--\n   2. [literal](missing.md) -->\n',
                         '1. > prose <!--\n   > 2. [literal](missing.md) -->\n'):
                with self.subTest(ending=repr(ending), lazy=body):
                    self.check(body.replace('\n', ending))
            with self.subTest(ending=repr(ending), actual_anchor=True):
                self.check('1. > prose <!--\n2. <span id="real"></span> -->\n\n[x](#real)\n'.replace('\n', ending))

    def test_heading_markup_removal_preserves_adjacent_text(self):
        for ending in ('\n', '\r', '\r\n'):
            for body, phantom in (('# Alpha<!--x-->Beta\n', 'alpha--------beta'),
                                  ('Alpha<!--x-->Beta\n---\n', 'alpha--------beta'),
                                  ('# Alpha<span>Beta</span>\n', 'alpha------beta'),
                                  ('Alpha<span>Beta</span>\n---\n', 'alpha------beta')):
                with self.subTest(ending=repr(ending), body=body):
                    line = len(docs.physical_lines(body)) + 2
                    result = self.check((body + '\n[real](#alphabeta) [phantom](#' + phantom + ')\n').replace('\n', ending), ['fragment'])
                    self.assertEqual([(line, 'Missing Markdown/HTML anchor: ' + phantom)],
                                     [(item.line, item.message) for item in result.findings])

    def test_multiline_heading_comment_preserves_only_actual_spacing(self):
        for ending in ('\n', '\r', '\r\n'):
            for before, after, anchor in (('', '', 'alphabeta'), (' ', '', 'alpha-beta'),
                                          ('', ' ', 'alpha-beta'), (' ', ' ', 'alpha--beta')):
                with self.subTest(ending=repr(ending), before=before, after=after):
                    body = 'Alpha' + before + '<!--\nx\n-->' + after + 'Beta\n---\n'
                    self.check((body + body + '\n[first](#' + anchor + ') [duplicate](#' + anchor + '-1)\n').replace('\n', ending))
            with self.subTest(ending=repr(ending), phantom=True):
                result = self.check('Alpha<!--\nx\n-->Beta\n---\n\n[phantom](#alpha-beta)\n'.replace('\n', ending), ['fragment'])
                self.assertEqual([(6, 'Missing Markdown/HTML anchor: alpha-beta')],
                                 [(item.line, item.message) for item in result.findings])

    def test_heading_html_comment_literals_remain_code_or_escape_text(self):
        for ending in ('\n', '\r', '\r\n'):
            for body, anchor in (('# `Alpha<!--x-->Beta`\n', 'alpha--x--beta'),
                                  ('# `Alpha<span>Beta`\n', 'alphaspanbeta'),
                                  ('# Alpha\\<span>Beta\n', 'alphaspanbeta'),
                                  ('Alpha\nBeta\n---\n', 'alpha-beta'),
                                  ('Alpha  Beta\n---\n', 'alpha--beta')):
                with self.subTest(ending=repr(ending), body=body):
                    self.check((body + '\n[real](#' + anchor + ')\n').replace('\n', ending))

    def test_existing_list_outdent_can_start_a_different_ordered_delimiter(self):
        for ending in ('\n', '\r', '\r\n'):
            for body in ('1. prose <!--\n2) [real](missing.md) -->\n',
                         '1) prose <!--\n2. [real](missing.md) -->\n',
                         '1. > prose <!--\n2) [real](missing.md) -->\n',
                         '1) > prose <!--\n2. [real](missing.md) -->\n'):
                with self.subTest(ending=repr(ending), body=body):
                    result = self.check(body.replace('\n', ending), ['path'])
                    self.assertEqual([(2, 'Missing or case-mismatched local target: docs/missing.md')],
                                     [(item.line, item.message) for item in result.findings])
            for body in ('> 1. prose <!--\n2) [literal](missing.md) -->\n',
                         '> 1) prose <!--\n2. [literal](missing.md) -->\n'):
                with self.subTest(ending=repr(ending), missing_outer_quote=body):
                    self.check(body.replace('\n', ending))

    def test_setext_headings_stop_at_prior_completed_headings(self):
        text = 'First\n---\nSecond\n---\nSecond\n---\n\n[a](#first) [b](#second) [c](#second-1) [phantom](#first-----second)\n'
        result = self.check(text, ['fragment'])
        self.assertEqual([(8, 'Missing Markdown/HTML anchor: first-----second')],
                         [(item.line, item.message) for item in result.findings])

    def test_setext_headings_respect_list_sibling_and_quote_boundaries(self):
        for body in ('1. First\n2. Second\n   ---\n',
                     '- First\n- Second\n  ---\n',
                     'First\n> Second\n> ---\n',
                     '> First\n> > Second\n> > ---\n'):
            with self.subTest(body=body):
                result = self.check(body + '\n[real](#second) [phantom](#first-second)\n', ['fragment'])
                self.assertEqual([(5, 'Missing Markdown/HTML anchor: first-second')],
                                 [(item.line, item.message) for item in result.findings])

    def test_setext_underlines_cannot_be_lazy_container_continuations(self):
        for body, anchors in (('> First\n---\n', ('first',)),
                              ('- First\n---\n', ('first',)),
                              ('> First\nSecond\n===\n', ('first-second', 'second')),
                              ('- First\nSecond\n===\n', ('first-second', 'second'))):
            with self.subTest(body=body):
                first = len(body.splitlines()) + 2
                text = body + '\n' + ''.join('[phantom](#' + name + ')\n' for name in anchors)
                result = self.check(text, ['fragment'] * len(anchors))
                self.assertEqual([(first + index, 'Missing Markdown/HTML anchor: ' + name)
                                  for index, name in enumerate(anchors)],
                                 [(item.line, item.message) for item in result.findings])

    def test_setext_heading_cannot_include_a_prior_thematic_break(self):
        result = self.check('First\n***\nSecond\n---\n\n[real](#second) [phantom](#first--second)\n', ['fragment'])
        self.assertEqual([(6, 'Missing Markdown/HTML anchor: first--second')],
                         [(item.line, item.message) for item in result.findings])

    def test_setext_heading_keeps_actual_soft_paragraph_continuations(self):
        for body, anchor in (('First\nSecond\n---\n', 'first-second'),
                             ('> First\n> Second\n> ---\n', 'first-second'),
                             ('- First\n  Second\n  ---\n', 'first-second'),
                             ('> First\nSecond\n> ---\n', 'first-second'),
                             ('First\n2. Second\n---\n', 'first-2-second')):
            with self.subTest(body=body):
                self.check(body + '\n[real](#' + anchor + ')\n')

    def test_nested_quote_lazy_paragraph_keeps_complete_inline_comment(self):
        for ending in ('\n', '\r', '\r\n'):
            for source in ('- > prose <!--\n  2. [literal](missing.md) -->\n',
                           '- > prose <!--\n  continued [literal](missing.md) -->\n',
                           '- > prose <!--\n  > 2. [literal](missing.md) -->\n',
                           '> prose <!--\n2. [literal](missing.md) -->\n'):
                with self.subTest(ending=repr(ending), source=source):
                    self.check(source.replace('\n', ending))
            for source, line in (('- > prose <!--\n  1. [real](missing.md) -->\n', 2),
                                 ('- > prose <!--\n\n  2. [real](missing.md) -->\n', 3)):
                with self.subTest(ending=repr(ending), source=source):
                    result = self.check(source.replace('\n', ending), ['path'])
                    self.assertEqual([(line, 'Missing or case-mismatched local target: docs/missing.md')],
                                     [(item.line, item.message) for item in result.findings])

    def test_nested_quote_lazy_comment_cannot_create_html_anchor(self):
        for ending in ('\n', '\r', '\r\n'):
            with self.subTest(ending=repr(ending)):
                result = self.check('- > prose <!--\n  2. <span id="ghost"></span> -->\n\n[x](#ghost)\n'.replace('\n', ending), ['fragment'])
                self.assertEqual([(4, 'Missing Markdown/HTML anchor: ghost')],
                                 [(item.line, item.message) for item in result.findings])

    def test_nested_quote_lazy_paragraph_keeps_cross_line_code_span(self):
        for ending in ('\n', '\r', '\r\n'):
            with self.subTest(ending=repr(ending)):
                self.check('- > prose `\n  2. [literal](missing.md) `\n'.replace('\n', ending))

    def test_many_consecutive_setext_headings_keep_bounded_scan(self):
        text = ''.join('Heading ' + str(index) + '\n---\n' for index in range(5000))
        self.write('README.md', text + '\n[last](#heading-4999)\n')
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), '--checks', 'links', '--root', str(self.root), '--json'],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual([], json.loads(result.stdout)['findings'])

    def test_lazy_setext_text_cannot_split_inline_comment_or_code(self):
        for ending in ('\n', '\r', '\r\n'):
            for source in ('> prose <!--\n===\n[literal](missing.md) -->\n',
                           '- prose <!--\n===\n[literal](missing.md) -->\n',
                           '- > prose <!--\n  ===\n  [literal](missing.md) -->\n',
                           '> prose `\n===\n[literal](missing.md) `\n'):
                with self.subTest(ending=repr(ending), source=source):
                    self.check(source.replace('\n', ending))
            for source in ('> prose <!--\n> ===\n> [real](missing.md) -->\n',
                           '> prose <!--\n>\n> [real](missing.md) -->\n'):
                with self.subTest(ending=repr(ending), source=source):
                    result = self.check(source.replace('\n', ending), ['path'])
                    self.assertEqual([(3, 'Missing or case-mismatched local target: docs/missing.md')],
                                     [(item.line, item.message) for item in result.findings])

    def test_setext_heading_keeps_masked_inline_comment_continuation(self):
        for ending in ('\n', '\r', '\r\n'):
            with self.subTest(ending=repr(ending)):
                heading = 'Alpha <!-- first\nhidden\n-->Beta\n---\n'
                self.check((heading + heading + '\n[first](#alpha-beta) [second](#alpha-beta-1)\n').replace('\n', ending))

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

    def test_table_code_spans_cannot_cross_cells_or_rows(self):
        header = "| A | B |\n| --- | --- |\n"
        for row, line in (("| `literal | [bad](missing.md) ` |\n", 3),
                          ("| `literal | text |\n| next | [bad](missing.md) ` |\n", 4)):
            with self.subTest(row=row):
                result = self.check(header + row, ["path"])
                self.assertEqual(line, result.findings[0].line)
                self.assertEqual("Missing or case-mismatched local target: docs/missing.md",
                                 result.findings[0].message)

    def test_table_code_controls_keep_non_table_and_same_cell_literals(self):
        header = "| A | B |\n| --- | --- |\n"
        self.check(header + "| `[literal](missing.md)` | text |\n")
        self.check(header + r"| `[literal](missing.md)\|text` | text |" + "\n")
        self.check("`literal | [literal](missing.md) `\n")
        self.check("| A | B |\n| --- |\n| `literal | [literal](missing.md) ` |\n")

    def test_table_comments_are_confined_to_their_cell(self):
        header = "| A | B |\n| --- | --- |\n"
        result = self.check(header + "| <!-- | [bad](missing.md) --> |\n", ["path"])
        self.assertEqual(3, result.findings[0].line)
        self.check(header + "| <!-- [literal](missing.md) --> | text |\n")
        result = self.check(header + "| <!-- | text |\n\n[bad](missing.md)\n", ["path"])
        self.assertEqual(5, result.findings[0].line)

    def test_table_html_anchors_respect_separators_and_escaped_pipes(self):
        header = "| A | B |\n| --- | --- |\n"
        self.check(header + '<span id="fake|anchor"></span> | text\n\n[x](#fake%7Canchor)\n', ["fragment"])
        self.check(header + r'| <span id="real\|anchor"></span> | text |' + '\n\n[x](#real%7Canchor)\n')
        self.check('<span id="ordinary|anchor"></span>\n[x](#ordinary%7Canchor)\n')
        result = self.check(header + '| <a href="missing.md">x</a> | text |\n', ["path"])
        self.assertEqual(3, result.findings[0].line)

    def test_table_labels_are_cell_local_and_share_document_references(self):
        header = "| A | B |\n| --- | --- |\n"
        self.check(header + "| [bad | label](missing.md) |\n")
        self.check(header + r"| [real\|label](missing.md) | text |" + "\n", ["path"])
        self.check(header + r"| [a\|b] | [x][ref] |" + "\n\n[a|b]: target.md\n[ref]: target.md\n")
        self.check("[ordinary|label](missing.md)\n", ["path"])

    def test_table_cells_cannot_define_block_headings_or_references(self):
        header = "| A | B |\n| --- | --- |\n"
        self.check(header + "| # Ghost | text |\n\n[x](#ghost)\n", ["fragment"])
        self.check(header + "| [ref]: missing.md | text |\n\n[x][ref]\n", ["reference"])

    def test_table_body_column_count_uses_declared_header_width(self):
        header = "| A | B |\n| --- | --- |\n"
        self.check(header + "| text | text | [literal](missing.md) |\n")
        self.check(header + "| [real](missing.md) |\n", ["path"])
        self.check("[header](missing.md) | B\n--- | ---\n", ["path"])

    def test_table_optional_edges_alignment_and_pipe_escape_parity(self):
        self.check("A | B\n:--- | ---:\n`literal | [bad](missing.md) `\n", ["path"])
        self.check("| A | B |\n| --- | --- |\n" +
                   r"| `literal \\| [bad](missing.md) ` |" + "\n", ["path"])
        self.write("docs/a|b.txt", "actual")
        self.check("| A |\n| --- |\n" + r"| [x](a\|b.txt) |" + "\n")

    def test_table_containers_and_block_termination_preserve_physical_lines(self):
        for header, row in (("> | A | B |\n> | --- | --- |\n", "> | `literal | [bad](missing.md) ` |\n"),
                            ("- | A | B |\n  | --- | --- |\n", "  | `literal | [bad](missing.md) ` |\n")):
            with self.subTest(header=header):
                result = self.check(header + row, ["path"])
                self.assertEqual(3, result.findings[0].line)
        self.check("| A | B |\n| --- | --- |\n| text | text |\n# Real\n\n[x](#real)\n")
        self.check("| A | B |\n| --- | --- |\n| text | text |\n- [bad](missing.md)\n", ["path"])

    def test_table_html_and_comments_cannot_leak_into_following_real_code_blocks(self):
        header = "| A | B |\n| --- | --- |\n"
        for row in ('| <span title="literal | text |\n', '| <!-- | text |\n'):
            with self.subTest(row=row):
                result = self.check(header + row + '\n```text\n[literal](also-missing.md)\n```\n'
                                    '[real](missing.md)\n', ["path"])
                self.assertEqual(8, result.findings[0].line)
                self.assertEqual('Missing or case-mismatched local target: docs/missing.md',
                                 result.findings[0].message)

    def test_table_long_backtick_runs_interrupt_only_as_valid_fences(self):
        for source, expected_line in (("```literal``` | `open\n--- | ---\nleft | [bad](missing.md) `\n", 3),
                                      ("| A | B |\n| --- | --- |\n```literal``` | `open\n"
                                       "left | [bad](missing.md) `\n", 4)):
            with self.subTest(source=source):
                result = self.check(source, ["path"])
                self.assertEqual(expected_line, result.findings[0].line)

    def test_table_source_ranges_retain_raw_escaped_and_surplus_cells(self):
        source = '> | A | B |\n> | --- | --- |\n> | [x](target.md) | <span id="a\\|b"></span> | surplus |\n'
        document = docs.Markdown('docs/source.md', source)
        self.assertEqual(3, len(document.table_rows[1].cells))
        self.assertEqual(2, document.table_rows[1].width)
        self.assertEqual(3, document.table_rows[1].line)
        for row in document.table_rows:
            for cell in row.cells:
                self.assertEqual(cell.source, source[cell.start:cell.end])
        self.assertIn('a|b', document.anchors)

    def test_table_html_block_interrupts_follow_declared_start_rules(self):
        header = '| A | B |\n| --- | --- |\n'
        for body, rows in (('<search partial | body |\n', 1),
                           ('<source/> | body |\n', 2),
                           ('<![CDATA[foo | body |\n', 1),
                           ('<div/other | body |\n', 2),
                           ('<pre/> | body |\n', 2),
                           ('</pre partial | body |\n', 2),
                           ('<span>\n', 1), ('<source>\n', 1)):
            with self.subTest(body=body):
                document = docs.Markdown('docs/source.md', header + body)
                self.assertEqual(rows, len(document.table_rows))

    def test_real_line_endings_keep_link_and_reference_continuations(self):
        sources = ('[x](\n target.md)\n', '[x](target.md\n "title")\n',
                   '[x](target.md\n)\n', '[x][r]\n\n[r]:\n target.md\n "title"\n')
        for ending in ('\n', '\r', '\r\n'):
            for source in sources:
                with self.subTest(ending=repr(ending), source=source):
                    self.check(source.replace('\n', ending))

    def test_blank_line_titles_cannot_hide_real_targets_for_any_line_ending(self):
        for ending in ('\n', '\r', '\r\n'):
            for whitespace in ('', ' \t'):
                with self.subTest(ending=repr(ending), whitespace=whitespace):
                    source = '[x](target.md "first\n' + whitespace + '\n[real](missing.md)\nlast")\n'
                    result = self.check(source.replace('\n', ending), ['link-syntax', 'path'])
                    self.assertEqual([(1, 'Unclosed or blank-line-separated link title'),
                                      (3, 'Missing or case-mismatched local target: docs/missing.md')],
                                     [(x.line, x.message) for x in result.findings])

    def test_blank_line_labels_remain_plain_prose_for_any_line_ending(self):
        for ending in ('\n', '\r', '\r\n'):
            with self.subTest(ending=repr(ending)):
                result = self.check('[first\n \t\nlast](missing.md)\n'.replace('\n', ending))
                self.assertEqual(0, result.local_targets)

    def test_parent_inline_comments_cannot_cross_rendered_table_boundaries(self):
        header = '| A | B |\n| --- | --- |\n'
        for ending in ('\n', '\r', '\r\n'):
            for row, expected in (('| text | text |\n', [(7, 'docs/missing.md')]),
                                  ('| [bad](table-missing.md) | text |\n',
                                   [(4, 'docs/table-missing.md'), (7, 'docs/missing.md')])):
                with self.subTest(ending=repr(ending), row=row):
                    source = 'prose <!--\n' + header + row + '-->\n\n[real](missing.md)\n'
                    result = self.check(source.replace('\n', ending), ['path'] * len(expected))
                    self.assertEqual([(line, 'Missing or case-mismatched local target: ' + target)
                                      for line, target in expected],
                                     [(x.line, x.message) for x in result.findings])
        self.check('prose \\<!--\n' + header + '| text | text |\n-->\n\n[real](missing.md)\n', ['path'])
        self.check('<!--\n' + header + '| [literal](missing.md) | text |\n-->\n\n[real](missing.md)\n', ['path'])
        self.check('prose <!--\nordinary literal\n-->\n\n[real](missing.md)\n', ['path'])

    def test_incomplete_inline_comments_do_not_hide_markdown_or_html_links(self):
        for source, line in (('prose <!-- [bad](missing.md)\n', 1),
                             ('| A | B |\n| --- | --- |\n| text <!-- [bad](missing.md) | text |\n', 3),
                             ('prose <!--\n\n<a href="missing.md">real</a>\n', 3)):
            with self.subTest(source=source):
                result = self.check(source, ['path'])
                self.assertEqual((line, 'Missing or case-mismatched local target: docs/missing.md'),
                                 (result.findings[0].line, result.findings[0].message))

    def test_short_inline_comments_end_before_following_navigation(self):
        for comment in ('<!-->', '<!--->', '<!---->'):
            for source, line in (('prose ' + comment + ' [bad](missing.md)\n', 1),
                                 ('| A | B |\n| --- | --- |\n| text ' + comment +
                                  ' [bad](missing.md) | text |\n', 3)):
                with self.subTest(comment=comment, source=source):
                    result = self.check(source, ['path'])
                    self.assertEqual(line, result.findings[0].line)
                    self.assertEqual('Missing or case-mismatched local target: docs/missing.md',
                                     result.findings[0].message)

    def test_complete_inline_comments_keep_soft_break_and_literal_controls(self):
        self.check('prose <!-- [literal](missing.md)\nordinary --> [real](target.md)\n')
        self.check('| A | B |\n| --- | --- |\n| text <!-- [literal](missing.md) --> | text |\n')
        self.check('`<!--` [real](target.md)\n')
        self.check('<span title="<!--">text</span> [real](target.md)\n')
        self.check('[x](target.md "<!--") [real](target.md)\n')
        self.check('# Literal <!--\n[x](#literal---)\n')

    def test_inline_comments_stop_at_new_markdown_blocks(self):
        for prefix in ('# ', '- ', '> ', '```text\n[literal](other-missing.md)\n```\n'):
            with self.subTest(prefix=prefix):
                source = 'prose <!--\n' + prefix + '[real](missing.md)\n\n-->\n'
                result = self.check(source, ['path'])
                self.assertEqual(5 if prefix.startswith('```') else 2, result.findings[0].line)
                self.assertEqual('Missing or case-mismatched local target: docs/missing.md',
                                 result.findings[0].message)

    def test_block_comments_end_when_their_quote_or_list_container_ends(self):
        for source in ('> <!--\n> [literal](other-missing.md)\n\n[real](missing.md)\n',
                       '- <!--\n  [literal](other-missing.md)\n\n[real](missing.md)\n'):
            with self.subTest(source=source):
                result = self.check(source, ['path'])
                self.assertEqual(4, result.findings[0].line)
        self.check('<!--\n\n[literal](missing.md)\n')

    def test_block_comment_contents_cannot_change_their_own_container(self):
        for prefix in ('> ', '  '):
            with self.subTest(prefix=prefix):
                opening = '> <!--\n' if prefix == '> ' else '- <!--\n'
                source = (opening + prefix + '- [literal](other-missing.md)\n' +
                          prefix + 'still [literal](other-missing.md)\n' +
                          prefix + '-->\n\n[real](missing.md)\n')
                result = self.check(source, ['path'])
                self.assertEqual((6, 'Missing or case-mismatched local target: docs/missing.md'),
                                 (result.findings[0].line, result.findings[0].message))

    def test_incomplete_inline_comments_cannot_hide_later_html_metadata(self):
        source = 'prose <!--\n\n<div title="\n# Ghost\n">text</div>\n\n[x](#ghost)\n'
        result = self.check(source, ['fragment'])
        self.assertEqual((7, 'Missing Markdown/HTML anchor: ghost'),
                         (result.findings[0].line, result.findings[0].message))
        self.check(source.replace('[x](#ghost)', '# Real\n\n[x](#real)'))

    def test_many_incomplete_inline_comments_remain_bounded_and_check_real_links(self):
        self.write('docs/source.md', 'text <!-- ' * 100_000 + '[bad](missing.md)\n')
        result = self.cli('--root', str(self.root), '--json', timeout=5)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        findings = json.loads(result.stdout)['findings']
        self.assertEqual([('docs/source.md', 1, 'path',
                           'Missing or case-mismatched local target: docs/missing.md')],
                         [(x['path'], x['line'], x['code'], x['message']) for x in findings])

    def test_escaped_physical_newlines_cannot_bypass_blank_title_boundaries(self):
        for ending in ('\n', '\r', '\r\n'):
            for backslashes in (1, 2):
                with self.subTest(ending=repr(ending), backslashes=backslashes):
                    source = '[x](target.md "first' + '\\' * backslashes + '\n\n[real](missing.md)\nlast")\n'
                    result = self.check(source.replace('\n', ending), ['link-syntax', 'path'])
                    self.assertEqual([(1, 'Unclosed or blank-line-separated link title'),
                                      (3, 'Missing or case-mismatched local target: docs/missing.md')],
                                     [(x.line, x.message) for x in result.findings])
        self.check('[x](target.md "first\\\nlast")\n')
        self.check(r'[x](target.md "escaped \"quote\"")' + '\n')

    def test_escaped_physical_newlines_cannot_join_blank_separated_labels(self):
        for ending in ('\n', '\r', '\r\n'):
            with self.subTest(ending=repr(ending)):
                result = self.check('[first\\\n\nlast](missing.md)\n'.replace('\n', ending))
                self.assertEqual(0, result.local_targets)
        self.check(r'[escaped \] label](target.md)' + '\n')

    def test_destination_backslashes_cannot_escape_physical_line_endings(self):
        for ending in ('\n', '\r', '\r\n'):
            actual = self.write('docs/target\\' + ending + '.txt', 'nonconforming destination decoy')
            for destination in ('<target\\\n.txt>', 'target\\\n.txt'):
                for marker in ('[x]', '![x]'):
                    with self.subTest(ending=repr(ending), destination=destination, marker=marker):
                        result = self.check((marker + '(' + destination + ')\n').replace('\n', ending), ['link-syntax'])
                        self.assertEqual(1, result.findings[0].line)
            actual.unlink()

    def test_bare_destinations_cannot_escape_ascii_space(self):
        actual = self.write('docs/target\\ file.txt', 'nonconforming bare destination decoy')
        for marker in ('[x]', '![x]'):
            with self.subTest(marker=marker):
                result = self.check(marker + '(target\\ file.txt)\n', ['link-syntax'])
                self.assertEqual(1, result.findings[0].line)
        self.check('[x](<target\\ file.txt>)\n')
        actual.unlink()
        actual = self.write('docs/target\\Q.txt', 'literal non-punctuation backslash')
        self.check('[x](target\\Q.txt)\n')
        actual.unlink()

    def test_reference_destinations_cannot_escape_line_endings_or_ascii_space(self):
        for ending in ('\n', '\r', '\r\n'):
            actual = self.write('docs/target\\' + ending + '.txt', 'nonconforming destination decoy')
            for destination in ('<target\\\n.txt>', 'target\\\n.txt'):
                with self.subTest(ending=repr(ending), destination=destination):
                    source = ('[x][r]\n\n[r]: ' + destination + '\n').replace('\n', ending)
                    result = self.check(source, ['reference', 'link-syntax'] if destination.startswith('<') else ['path', 'path'])
                    self.assertEqual([1, 3], [x.line for x in result.findings])
                    if not destination.startswith('<'):
                        self.assertTrue(all(x.message == 'Missing or case-mismatched local target: docs/target\\'
                                            for x in result.findings))
                        selected = self.write('docs/target\\', 'actual first-line reference destination')
                        self.check(source)
                        selected.unlink()
            actual.unlink()
        actual = self.write('docs/target\\ file.txt', 'nonconforming bare destination decoy')
        self.check('[x][r]\n\n[r]: target\\ file.txt\n', ['reference', 'link-syntax'])
        actual.unlink()

    def test_unicode_content_lines_do_not_split_complete_comments_or_code_spans(self):
        for scalar in ('\v', '\f', '\x1c', '\x1d', '\x1e', '\x85', '\u2028', '\u2029', '\u00a0'):
            for ending in ('\n', '\r', '\r\n'):
                for opening, closing in (('prose <!--', '-->'), ('`prose', '`')):
                    with self.subTest(scalar=repr(scalar), ending=repr(ending), opening=opening):
                        source = opening + '\n' + scalar + '\n[literal](missing.md)\n' + closing + '\n[real](target.md)\n'
                        result = self.check(source.replace('\n', ending))
                        self.assertEqual(1, result.local_targets)
        result = self.check('prose <!--\n \t\n[real](missing.md)\n-->\n', ['path'])
        self.assertEqual(3, result.findings[0].line)

    def test_unicode_whitespace_does_not_turn_literal_markers_into_block_boundaries(self):
        for scalar in ('\v', '\f', '\x1c', '\x1d', '\x1e', '\x85', '\u2028', '\u2029', '\u00a0'):
            for marker in ('#', '---', '***', '___'):
                for opening, closing in (('prose <!--', '-->'), ('`prose', '`')):
                    with self.subTest(scalar=repr(scalar), marker=marker, opening=opening):
                        self.check(opening + '\n' + marker + scalar + ('text' if marker == '#' else '') + '\n[literal](missing.md)\n' + closing + '\n')

    def test_unicode_content_is_not_blank_before_reference_like_prose(self):
        for scalar in ('\v', '\f', '\x1c', '\x1d', '\x1e', '\x85', '\u2028', '\u2029', '\u00a0'):
            with self.subTest(scalar=repr(scalar)):
                result = self.check(scalar + '\n[r]: target.md\n\n[x][r]\n', ['link-syntax', 'reference'])
                self.assertEqual([2, 4], [x.line for x in result.findings])

    def test_raw_ascii_control_destinations_are_rejected_before_target_lookup(self):
        for scalar in ('\x01', '\x0b', '\x1b', '\x1f', '\x7f'):
            actual = self.write('docs/a' + scalar + 'b.txt', 'raw control decoy or actual entity target')
            with self.subTest(scalar=repr(scalar)):
                result = self.check('[x](a' + scalar + 'b.txt)\n', ['link-syntax'])
                self.assertEqual(1, result.findings[0].line)
                self.check('[x](a&#' + str(ord(scalar)) + ';b.txt)\n')
            actual.unlink()

    def test_bare_destinations_keep_non_ascii_whitespace_as_filename_content(self):
        for scalar in ('\u00a0', '\u2028', '\u2029'):
            actual = self.write('docs/a' + scalar + 'b.txt', 'actual Unicode filename')
            for source in ('[x](a' + scalar + 'b.txt)\n', '[x][r]\n\n[r]: a' + scalar + 'b.txt\n'):
                with self.subTest(scalar=repr(scalar), source=source):
                    self.check(source)
            actual.unlink()

    def test_block_comment_closing_lines_keep_only_raw_html_navigation(self):
        for ending in ('\n', '\r', '\r\n'):
            cases = [('<!-- c --> <a href="missing.md">real</a>\n', ['path'], [1]),
                     ('<!--\n--> <img src="missing.md">\n', ['path'], [2]),
                     ('<!-- c --> [literal](missing.md) <a href="real-missing.md">real</a>\n', ['path'], [1]),
                     ('<!-- c --> <span id="real"></span>\n\n[x](#real)\n', [], []),
                     ('<!-- c --> [literal](missing.md)\n', [], []),
                     ('<!-- c --> ```text\n[real](missing.md)\n```\n', ['path'], [2]),
                     ('<!-- c -->\n<a href="missing.md">real</a>\n', ['path'], [2]),
                     ('<!-- c --> `<a href="missing.md">real</a>`\n', ['path'], [1]),
                     ('<!-- c --> [literal](target.md "<a href=\'missing.md\'>")\n', ['path'], [1]),
                     ('<!-- c --> <div title="\n# Ghost\n">text</div>\n\n[x](#ghost)\n', ['fragment'], [5])]
            for source, codes, lines in cases:
                with self.subTest(ending=repr(ending), source=source):
                    result = self.check(source.replace('\n', ending), codes)
                    self.assertEqual(lines, [x.line for x in result.findings])
                    for finding in result.findings:
                        expected = ('Missing Markdown/HTML anchor: ghost' if finding.code == 'fragment' else
                                    'Missing or case-mismatched local target: docs/' +
                                    ('real-missing.md' if 'real-missing.md' in source else 'missing.md'))
                        self.assertEqual(expected, finding.message)
        result = self.check('<!-- <a href="missing.md"> --> <a href="target.md">real</a>\n')
        self.assertEqual(1, result.local_targets)

    def test_ordered_soft_continuations_preserve_comments_and_real_list_boundaries(self):
        for ending in ('\n', '\r', '\r\n'):
            cases = [('prose <!--\n2. <span id="ghost"></span> -->\n\n[x](#ghost)\n', ['fragment'], [4]),
                     ('prose <!--\n2. [literal](missing.md) -->\n', [], []),
                     ('prose <!--\n1. [real](missing.md) -->\n', ['path'], [2]),
                     ('1. prose <!--\n2. [real](missing.md) -->\n', ['path'], [2]),
                     ('1. prose <!--\n   2. [literal](missing.md) -->\n', [], []),
                     ('1. prose <!--\n   1. [real](missing.md) -->\n', ['path'], [2]),
                     ('> prose <!--\n> 2. [literal](missing.md) -->\n', [], []),
                     ('> prose <!--\n> 1. [real](missing.md) -->\n', ['path'], [2]),
                     ('prose <!--\n\n2. [real](missing.md) -->\n', ['path'], [3]),
                     ('1. prose <!--\nordinary [literal](missing.md) -->\n', [], []),
                     ('2. prose <!--\n3. [real](missing.md) -->\n', ['path'], [2])]
            for source, codes, lines in cases:
                with self.subTest(ending=repr(ending), source=source):
                    result = self.check(source.replace('\n', ending), codes)
                    self.assertEqual(lines, [x.line for x in result.findings])
                    for finding in result.findings:
                        self.assertEqual('Missing Markdown/HTML anchor: ghost' if finding.code == 'fragment' else
                                         'Missing or case-mismatched local target: docs/missing.md', finding.message)

    def test_noninterrupting_ordered_text_cannot_create_headings_or_definitions(self):
        self.check('prose\n2. # Ghost\n\n[x](#ghost)\n', ['fragment'])
        result = self.check('prose\n2. [r]: target.md\n\n[x][r]\n', ['reference'])
        self.assertEqual(4, result.findings[0].line)
        self.check('prose\n\n2. # Real\n\n[x](#real)\n')
        self.check('1. first\n2. # Real\n\n[x](#real)\n')
        self.check('> prose\n> 2. # Ghost\n\n[x](#ghost)\n', ['fragment'])
        self.check('1. prose\n   2. # Ghost\n\n[x](#ghost)\n', ['fragment'])

    def test_multiline_html_attributes_preserve_quoted_container_boundaries(self):
        source = ('> <div title="\n> 2. # Ghost\n> ~~~\n> " id="real">text</div>\n>\n'
                  '> [real](missing.md)\n[x](#real) [ghost](#ghost)\n')
        result = self.check(source, ['path', 'fragment'])
        self.assertEqual([6, 7], [x.line for x in result.findings])
        self.assertEqual('Missing Markdown/HTML anchor: ghost', result.findings[1].message)
        self.check('- <div title="\n  2. # Ghost\n  ```\n  ">text</div>\n\n[x](#ghost)\n', ['fragment'])

    def test_ordered_item_boundaries_keep_delimiters_nesting_and_long_indentation(self):
        for delimiter in ('.', ')'):
            with self.subTest(delimiter=delimiter):
                self.check('> 1' + delimiter + ' prose <!--\n> 2' + delimiter +
                           ' [real](missing.md) -->\n', ['path'])
                self.check('1' + delimiter + ' prose <!--\n   2' + delimiter +
                           ' [literal](missing.md) -->\n')
        self.check('123456789. ```text\n           [literal](missing.md)\n           ```\n'
                   '           # Real\n\n[x](#real)\n')

    def test_raw_html_tails_ignore_preliminary_markdown_code_and_escape_state(self):
        result = self.check('prose `\n<!-- c --> <a href="missing.md">real</a>\n`\n', ['path'])
        self.assertEqual(2, result.findings[0].line)
        self.check('<!-- c --> \\<a href="missing.md">real</a>\n', ['path'])

    def test_raw_literal_html_blocks_preserve_html_and_exclude_markdown_examples(self):
        for tag in ('pre', 'script', 'style', 'textarea'):
            with self.subTest(tag=tag):
                source = ('<' + tag + '>\n# Ghost\n[literal](missing.md)\n```\n' +
                          '</' + tag.upper() + '>\n\n# Real\n\n[real](#real) [ghost](#ghost)\n')
                self.check(source, ['fragment'])
                document = docs.Markdown('docs/source.md', source)
                self.assertEqual([], document.fences)
                self.assertNotIn('ghost', document.anchors)
        result = self.check('<pre>\n<a href="missing.md">actual HTML</a>\n</pre>\n', ['path'])
        self.assertEqual(2, result.findings[0].line)

    def test_missing_quote_markers_keep_noninterrupting_ordered_lazy_continuations(self):
        for ending in ('\n', '\r', '\r\n'):
            cases = [('> 1. prose <!--\n2. [literal](missing.md) -->\n', []),
                     ('> 1. prose <!--\n1. [real](missing.md) -->\n', ['path']),
                     ('> 1. prose <!--\n> 2. [real](missing.md) -->\n', ['path']),
                     ('> 1. prose <!--\n\n2. [real](missing.md) -->\n', ['path']),
                     ('> > 1. prose <!--\n> 2. [literal](missing.md) -->\n', [])]
            for source, codes in cases:
                with self.subTest(ending=repr(ending), source=source):
                    result = self.check(source.replace('\n', ending), codes)
                    if codes:
                        self.assertEqual(3 if '\n\n' in source else 2, result.findings[0].line)

    def test_ordered_markers_and_source_line_numbers_require_ascii_digits(self):
        for digit in ('١', '１'):
            with self.subTest(digit=digit):
                self.check(digit + '. # Ghost\n\n[x](#ghost)\n', ['fragment'])
                result = self.check('| A | B |\n| --- | --- |\n' + digit +
                                    '. `literal | [real](missing.md) `\n', ['path'])
                self.assertEqual(3, result.findings[0].line)
                self.write('tools/sample.txt', 'one\n')
                self.check('[x](../tools/sample.txt#L' + digit + ')\n', ['fragment'])
        self.check('1. # Real\n\n[x](#real)\n')

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

    def test_multiline_html_attributes_cannot_create_headings_or_consume_suffixes(self):
        for source in ('<div title="\n# Ghost\n">text</div>\n\n[x](#ghost)\n',
                       '<div title="\n# Ghost\n">text</div>\n\n# Ghost\n\n[x](#ghost-1)\n'):
            with self.subTest(source=source):
                self.check(source, ["fragment"])
        self.check('<div title="\n# Ghost\n">text</div>\n\n# Real\n\n[x](#real)\n')

    def test_multiline_html_attributes_do_not_define_references(self):
        self.check('<div title="\n[ref]: missing.md\n">text</div>\n')
        self.check('<div title="\n[ref]: missing.md\n">text</div>\n\n'
                   '[x][ref]\n\n[ref]: target.md\n')

    def test_attribute_fences_cannot_hide_or_substitute_following_real_links(self):
        for marker in ('```', '~~~'):
            for link in ('[x](missing.md)', '<a href="missing.md">x</a>'):
                with self.subTest(marker=marker, link=link):
                    result = self.check('<div title="\n' + marker + '\n">text</div>\n\n' +
                                        link + '\n\n```text\n[literal](also-missing.md)\n```\n', ["path"])
                    self.assertEqual(5, result.findings[0].line)
                    self.assertEqual('Missing or case-mismatched local target: docs/missing.md',
                                     result.findings[0].message)

    def test_multiline_metadata_keeps_real_html_attributes_and_code_escape_controls(self):
        self.check('<span\n title="\n# Ghost\n" id="real"></span>\n\n[x](#real)\n')
        result = self.check('<a\n title="\n~~~\n" href="missing.md">x</a>\n', ["path"])
        self.assertEqual(4, result.findings[0].line)
        self.check('```html\n<div title="\n```\n[real](missing.md)\n', ["path"])
        self.check('`<div title="literal">`\n[x](#literal)\n', ["fragment"])
        self.check('\\<div title="\n# Real\n">text</div>\n\n[x](#real)\n')

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
        return subprocess.run([sys.executable, str(SCRIPT), "--checks", "links", *args], cwd=cwd,
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


class CorpusTests(unittest.TestCase):
    """Shared-reader contracts independent of the selected metadata family."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tyrne corpus ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write("README.md", "# Public\n")

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def test_shared_reader_caches_text_without_selecting_link_findings(self):
        self.write("docs/source.md", "[visible][missing]\n")
        corpus = docs.Corpus(self.root, checks=["tasks"])
        self.assertEqual(["tasks"], corpus.report.as_dict()["checks"])
        view = corpus.report.as_dict()
        view["checks"].append("unselected")
        self.assertEqual(["tasks"], corpus.report.checks)
        self.assertFalse(corpus.report.findings)
        self.assertTrue(corpus.load("docs/source.md").findings)
        with patch.object(docs, "read_utf8", side_effect=AssertionError("cached source reread")):
            self.assertEqual("[visible][missing]\n", corpus.read("docs/source.md"))
            self.assertIs(corpus.load("docs/source.md"), corpus.documents["docs/source.md"])

    def test_direct_metadata_read_rejects_private_and_aliases_before_read(self):
        self.write("outside/canary.rs", "UNSAFE-2099-9999\n")
        self.write("docs/analysis/private/canary.rs", "private fixture\n")
        (self.root / "leaf.rs").symlink_to("outside/canary.rs")
        (self.root / "ancestor").symlink_to("outside", target_is_directory=True)
        (self.root / "dangling.rs").symlink_to("absent")
        (self.root / "loop.rs").symlink_to("loop.rs")
        corpus = docs.Corpus(self.root, checks=["audit"])
        with patch.object(docs, "read_utf8", side_effect=AssertionError("forbidden source opened")):
            for path in ("leaf.rs", "ancestor/canary.rs", "dangling.rs", "loop.rs",
                         "docs/analysis/private/canary.rs", "../outside.rs"):
                with self.subTest(path=path):
                    self.assertIsNone(corpus.read(path))
        self.assertEqual(6, len(corpus.report.findings))

    def test_direct_metadata_read_reports_utf8_size_and_regular_file_errors(self):
        corpus = docs.Corpus(self.root, checks=["audit"])
        (self.root / "invalid.rs").write_bytes(b"one\r\ntwo\r\xff")
        self.write("large.rs", "x" * (docs.MAX_DOCUMENT_BYTES + 1))
        self.assertIsNone(corpus.read("invalid.rs"))
        self.assertIsNone(corpus.read("large.rs"))
        self.assertIsNone(corpus.read("."))
        self.assertEqual([("invalid.rs", 3, "read"), ("large.rs", 1, "read"), (".", 1, "read")],
                         [(x.path, x.line, x.code) for x in corpus.report.findings])

    def test_source_walk_is_sorted_and_rejects_aliases_without_opening(self):
        self.write("crate/src/z.rs", "// source\n")
        self.write("crate/src/a.s", "/* source */\n")
        self.write("crate/target/generated.rs", "// generated fixture\n")
        self.write("outside/canary.rs", "// outside fixture\n")
        (self.root / "crate/alias").symlink_to(self.root / "outside", target_is_directory=True)
        corpus = docs.Corpus(self.root, checks=["audit"])
        with patch.object(docs, "read_utf8", side_effect=AssertionError("walk opened content")):
            paths = corpus.walk("crate", suffixes=(".rs", ".s"), exclude=("target",))
        self.assertEqual(["crate/src/a.s", "crate/src/z.rs"], paths)
        self.assertEqual([("crate/alias", "input")], [(x.path, x.code) for x in corpus.report.findings])

    def test_source_walk_checks_prefix_and_nonregular_ancestors(self):
        self.write("outside/canary.rs", "// outside fixture\n")
        (self.root / "alias").symlink_to("outside", target_is_directory=True)
        self.write("not-directory", "fixture\n")
        corpus = docs.Corpus(self.root, checks=["audit"])
        self.assertEqual([], corpus.walk("alias", suffixes=(".rs",)))
        self.assertEqual([], corpus.walk("not-directory", suffixes=(".rs",)))
        self.assertEqual([], corpus.walk("docs/analysis/private", suffixes=(".rs",)))
        self.assertEqual(3, len(corpus.report.findings))

    def test_explicit_root_alias_is_canonicalized_and_invalid_root_fails(self):
        alias = self.root / "caller-root"
        target = self.root / "selected"
        target.mkdir()
        (target / "README.md").write_text("# Selected\n", encoding="utf-8")
        alias.symlink_to(target, target_is_directory=True)
        corpus = docs.Corpus(alias, checks=["tasks"])
        self.assertEqual(target.resolve(), corpus.root)
        self.assertFalse(corpus.report.findings)
        bad = docs.Corpus(self.root / "absent", checks=["tasks"])
        self.assertTrue(bad.report.findings)
        self.assertEqual([], bad.paths)

    def test_link_labels_preserve_visible_usage_and_image_identity(self):
        text = ("[`ADR-C1-topic`](target.md) [visible][key] [collapsed][] [shortcut]\n"
                "![image][key] <img src='picture.png'>\n\n"
                "[key]: target.md\n[collapsed]: target.md\n[shortcut]: target.md\n\n"
                "| Name |\n|---|\n| [table][key] |\n")
        document = docs.Markdown("docs/source.md", text)
        labels = [(x.label, x.image) for x in document.links if x.label is not None]
        self.assertEqual([("`ADR-C1-topic`", False), ("visible", False), ("collapsed", False),
                          ("shortcut", False), ("image", True), ("table", False)], labels)
        definitions = [x for x in document.links if x.label is None and x.kind == "markdown"]
        self.assertEqual(3, len(definitions))
        self.assertTrue(next(x for x in document.links if x.kind == "html").image)

    def test_shared_links_pass_preserves_report_and_is_not_double_counted(self):
        self.write("docs/source.md", "# Heading\n[x](#heading) [bad][missing]\n")
        corpus = docs.Corpus(self.root)
        result = docs.check_links(corpus)
        self.assertIs(result, corpus.report)
        self.assertEqual(1, result.local_targets)
        self.assertEqual(1, result.fragments)
        self.assertEqual(["reference"], [x.code for x in result.findings])
        before = result.as_dict()
        self.assertEqual(before, docs.check_links(corpus).as_dict())

    def test_metadata_source_alias_created_after_enumeration_is_not_opened(self):
        source = self.write("crate/src/lib.rs", "// original fixture\n")
        self.write("outside/canary.rs", "// canary fixture\n")
        corpus = docs.Corpus(self.root, checks=["audit"])
        self.assertEqual(["crate/src/lib.rs"], corpus.walk("crate", suffixes=(".rs",)))
        source.unlink()
        source.symlink_to(self.root / "outside/canary.rs")
        with patch.object(docs, "read_utf8", side_effect=AssertionError("replacement alias opened")):
            self.assertIsNone(corpus.read("crate/src/lib.rs"))
        self.assertTrue(corpus.report.findings)

    def test_directory_errors_without_filename_are_structured(self):
        self.write("docs/source.md", "# Source\n")
        self.write("crate/src/lib.rs", "// source\n")

        def denied(_start, **options):
            options["onerror"](PermissionError("fixture directory denial"))
            return iter(())

        with patch.object(docs.os, "walk", side_effect=denied):
            corpus = docs.Corpus(self.root, checks=["audit"])
            self.assertEqual([], corpus.walk("crate", suffixes=(".rs",)))
        self.assertEqual([("docs", "input"), ("crate", "input")],
                         [(x.path, x.code) for x in corpus.report.findings])

    def test_generated_exclusion_is_relative_to_member_root(self):
        self.write("crate/target/generated.rs", "// generated fixture\n")
        self.write("crate/src/target/real.rs", "// real source fixture\n")
        corpus = docs.Corpus(self.root, checks=["audit"])
        self.assertEqual(["crate/src/target/real.rs"],
                         corpus.walk("crate", suffixes=(".rs",), exclude=("target",)))
        self.assertFalse(corpus.report.findings)


if __name__ == "__main__":
    unittest.main()
