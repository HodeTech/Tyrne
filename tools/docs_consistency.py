"""Bounded offline Markdown/navigation checks, governed by ADR-0043.

This is a source checker, not a renderer or a proof of architectural truth.
Offsets remain tied to original text so every diagnostic has a useful line.
"""

from bisect import bisect_right
from dataclasses import dataclass, field
from html.entities import html5 as HTML_ENTITIES
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import stat
import string
from typing import NamedTuple, Optional
import unicodedata
from urllib.parse import unquote

ROOT_FILES = ("README.md", "CLAUDE.md", "AGENTS.md", "SECURITY.md", "CONTRIBUTING.md")
LOCAL_ONLY = ("docs/analysis/private", "docs/analysis/temp", "docs/analysis/technical-analysis")
MAX_DOCUMENT_BYTES = 16 * 1024 * 1024
MAX_NESTING = 64
PHYSICAL_LINE = re.compile(r"[^\r\n]*(?:\r\n|\r|\n|$)")
C0_SPACE = "".join(map(chr, range(33)))
ESCAPE = re.compile(r"\\([" + re.escape(string.punctuation) + r"])")
QUOTE_PREFIX = re.compile(r" {0,3}>[ \t]?")
LIST_PREFIX = re.compile(r" {0,3}(?:[-+*]|[0-9]{1,9}[.)])([ \t]+)")
EMPTY_LINE = re.compile(r"[ \t]*(?:\r?\n)?$")
ENTITY = re.compile(r"&(?:#[xX][0-9a-fA-F]{1,6}|#[0-9]{1,7}|[A-Za-z][A-Za-z0-9]*);")
MARKDOWN_DECODE = re.compile(ESCAPE.pattern + "|" + ENTITY.pattern)
HTML_LINK_START = re.compile(r"<(?:a|img)\s", re.I)
HTML_SPACE = re.compile(r"[ \t\r\n\f]*")
HTML_TAGNAME = re.compile(r"<[A-Za-z][\w:-]*")
HTML_ATTRIBUTE = re.compile(r"[^ \t\r\n\f=/<>\"']+")
HTML_REFERENCE = re.compile(r"&(?:\#(?:[xX][0-9a-fA-F]+|[0-9]+);?|[A-Za-z][A-Za-z0-9]*;?)")
MAX_ENTITY_NAME = max(map(len, HTML_ENTITIES))
# WHATWG numeric-character-reference end state: only HTML has these legacy
# replacements. Other controls and noncharacters remain their actual scalar.
HTML_NUMERIC_REPLACEMENTS = {
    0x80: 0x20AC, 0x82: 0x201A, 0x83: 0x0192, 0x84: 0x201E,
    0x85: 0x2026, 0x86: 0x2020, 0x87: 0x2021, 0x88: 0x02C6,
    0x89: 0x2030, 0x8A: 0x0160, 0x8B: 0x2039, 0x8C: 0x0152,
    0x8E: 0x017D, 0x91: 0x2018, 0x92: 0x2019, 0x93: 0x201C,
    0x94: 0x201D, 0x95: 0x2022, 0x96: 0x2013, 0x97: 0x2014,
    0x98: 0x02DC, 0x99: 0x2122, 0x9A: 0x0161, 0x9B: 0x203A,
    0x9C: 0x0153, 0x9E: 0x017E, 0x9F: 0x0178,
}


class Finding(NamedTuple):
    path: str
    line: int
    code: str
    message: str


class Link(NamedTuple):
    line: int
    destination: str
    kind: str = "markdown"


class TableCell(NamedTuple):
    start: int
    end: int
    source: str


class TableRow(NamedTuple):
    line: int
    cells: list
    header: bool
    table_line: int
    width: int


class Container(NamedTuple):
    kind: str
    width: int


class BlockLine(NamedTuple):
    start: int
    end: int
    body_start: int
    parts: tuple
    boundary: bool
    paragraph: Optional[int] = None
    kind: str = "literal"


@dataclass
class Report:
    findings: list = field(default_factory=list)
    files: int = 0
    local_targets: int = 0
    fragments: int = 0

    def as_dict(self):
        return {"checks": ["links"], "ok": not self.findings, "files": self.files,
                "local_targets": self.local_targets, "fragments": self.fragments,
                "findings": [x._asdict() for x in sorted(set(self.findings))]}


def blank(text):
    """Erase syntax without shifting offsets or line endings."""
    return "".join(c if c in "\r\n" else " " for c in text)


def physical_lines(text, keepends=False):
    """Split only LF, CR and CRLF; Unicode separators remain source content."""
    return [match[0] if keepends else match[0].rstrip("\r\n")
            for match in PHYSICAL_LINE.finditer(text) if match[0]]


def source_offset(line, column):
    """Map structural columns to original text, consuming a partial tab once.

    Classification retains residual virtual spaces in the visual view;
    source consumers retain original text after the structural prefix.
    """
    if "\t" not in line:
        return column
    width = 0
    for index, char in enumerate(line):
        if width >= column:
            return index
        width += 4 - width % 4 if char == "\t" else 1
    return len(line)


def container_parts(line, paragraph=False):
    """Parse ordered quote/list prefixes, retaining excess code indentation."""
    offset = 0
    parts = []
    while True:
        match = QUOTE_PREFIX.match(line, offset)
        if match:
            parts.append(Container("quote", match.end() - offset))
            offset = match.end()
            paragraph = False  # A newly opened quote has a fresh block.
            continue
        match = LIST_PREFIX.match(line, offset)
        if not match:
            break
        marker = match[0].lstrip(" ")
        if paragraph and (not line[match.end():].strip(" \t\r\n") or
                          (marker[0] in string.digits and int(re.match(r"[0-9]+", marker)[0]) != 1)):
            break  # A soft ordered marker remains source text, including its prefix.
        padding = len(match[1])
        width = match.end() - offset if padding <= 4 else match.end() - offset - padding + 1
        parts.append(Container("list", width))
        offset += width
        paragraph = False
    return offset, parts


def continuation(line, parts):
    """Remove a previously opened container; None means it has ended."""
    if "\t" in line:
        visual = line.expandtabs(4)
        body = continuation(visual, parts)
        return None if body is None else line[source_offset(line, len(visual) - len(body)):]
    offset = 0
    for part in parts:
        if part.kind == "quote":
            match = QUOTE_PREFIX.match(line, offset)
            if not match:
                return None
            offset = match.end()
        elif line[offset:offset + part.width] == " " * part.width:
            offset += part.width
        elif EMPTY_LINE.match(line, offset):
            offset = len(line.rstrip("\r\n"))
        else:
            return None
    return line[offset:]


def block_body(line, active, paragraph=False, details=False):
    """Resolve existing containers before interpreting a possible new item.

    Ordered non-1 markers cannot interrupt an open paragraph, but can start
    a sibling after outdent or a new list after the paragraph has ended.
    """
    if "\t" in line:
        visual = line.expandtabs(4)
        body, parts, opened = block_body(visual, active, paragraph, details=True)
        result = line[source_offset(line, len(visual) - len(body)):], parts, opened
        return result if details else result[:2]
    parts = list(active)
    outdented_list = False
    outdented_quote = False
    sibling_parent = False

    def paragraph_only(body):
        sibling = sibling_parent and LIST_PREFIX.match(body)
        return paragraph and not sibling

    while parts:
        body = continuation(line, parts)
        if body is not None:
            offset, extra = container_parts(body, paragraph_only(body))
            if (paragraph and (outdented_list or outdented_quote) and not extra and
                    body.strip(" \t\r\n") and not paragraph_interrupt(body, setext=False)):
                result = body, list(active), False  # Lazy item continuation.
            else:
                result = body[offset:], parts + extra, bool(extra)
            return result if details else result[:2]
        part = parts.pop()
        outdented_list |= part.kind == "list"
        outdented_quote |= part.kind == "quote"
        if part.kind == "list":
            sibling_parent = True
        else:
            # A list inside an unmatched quote is not a sibling parent at
            # the remaining level; its paragraph may continue lazily.
            sibling_parent = False
    offset, parts = container_parts(line, paragraph_only(line))
    if (paragraph and active and not parts and line.strip(" \t\r\n") and
            not paragraph_interrupt(line, setext=False)):
        result = line, list(active), False  # Lazy quote/list continuation.
    else:
        result = line[offset:], parts, bool(parts)
    return result if details else result[:2]


def paragraph_interrupt(body, setext=True):
    """Recognize leaf syntax that ends an existing paragraph's inline block."""
    body = body.rstrip("\r\n")
    if re.match(r" {0,3}(?:#{1,6}(?:[ \t]|$)|>)", body) or opening_fence(body):
        return True
    if setext and re.fullmatch(r" {0,3}(?:=+|-+)[ \t]*", body):
        return True
    if any(re.fullmatch(r" {0,3}(?:" + re.escape(char) + r"[ \t]*){3,}", body) for char in "*-_"):
        return True
    stripped = body.lstrip(" ")
    if len(body) - len(stripped) > 3:
        return False
    if re.match(r"<!--|<\?|<![A-Z]|<!\[CDATA\[", stripped):
        return True
    tag = re.match(r"(</?)([A-Za-z][A-Za-z0-9-]*)(?=[ \t>]|/>|$)", stripped)
    return bool(tag and (tag[2].lower() in HTML_BLOCK_NAMES or
                        (tag[1] == "<" and tag[2].lower() in HTML_RAW_BLOCK_NAMES and
                         (tag.end() == len(stripped) or stripped[tag.end()] in " \t>"))))


class ParagraphState:
    """Classify actual paragraph extents once for every inline consumer.

    Literal blocks clear the state in the block walker. A lazy continuation
    retains its full container identity, but cannot supply a setext underline.
    Masked inline content never becomes a manufactured source blank line.
    """

    def __init__(self):
        self.start = None
        self.parts = ()

    @property
    def active(self):
        """Whether ordinary paragraph text can still continue."""
        return self.start is not None

    def clear(self):
        """End the active paragraph at a real block boundary."""
        self.start = None

    def record(self, begin, end, body_start, parts, opened, body, source, metadata=False):
        """Return one source event, consuming a heading paragraph exactly once."""
        parts = tuple(parts)
        if opened or parts != self.parts:
            self.clear()
        self.parts = parts
        body = body.rstrip("\r\n")
        paragraph = None
        if metadata:
            kind = "paragraph"
        elif not body.strip(" \t"):
            kind = "blank"
        elif re.match(r" {0,3}#{1,6}(?:[ \t]|$)", body):
            kind = "atx"
        elif (self.active and re.fullmatch(r" {0,3}(?:=+|-+)[ \t]*", body) and
              continuation(source.expandtabs(4), parts) is not None):
            kind = "setext"
            paragraph = self.start
        elif paragraph_interrupt(body, setext=False):
            kind = "block"
        else:
            kind = "paragraph"
        boundary = kind != "paragraph" or not self.active
        if kind == "paragraph":
            if not self.active:
                self.start = begin
            paragraph = self.start
        else:
            self.clear()
        return BlockLine(begin, end, body_start, parts, boundary, paragraph, kind)


class BlockLayout:
    """Acyclic physical-line container/paragraph events for inline consumers.

    HTML discovery uses preliminary events. The block walker supplies final
    events after its actual literal/HTML/table decisions; downstream consumers
    retain those source body offsets rather than stripping markers again.
    """

    def __init__(self, text, events=None):
        if events is not None:
            self.lines = events
            return
        self.lines = []
        active = []
        paragraph = ParagraphState()
        start = 0
        for line in physical_lines(text, keepends=True):
            visual = line.expandtabs(4)
            body, parts, opened = block_body(visual, active, paragraph.active, details=True)
            body_start = start + source_offset(line, len(visual) - len(body))
            self.lines.append(paragraph.record(start, start + len(line), body_start,
                                               parts, opened, body, line))
            active = parts
            start += len(line)


def table_cells(body, offset):
    """Keep original cell ranges; only unescaped pipes separate GFM cells."""
    body = body.rstrip("\r\n")
    separators = []
    cursor = 0
    while cursor < len(body):
        if body[cursor] == "\\" and cursor + 1 < len(body) and body[cursor + 1] in string.punctuation:
            cursor += 2
            continue
        if body[cursor] == "|":
            separators.append(cursor)
        cursor += 1
    bounds = [-1] + separators + [len(body)]
    ranges = list(zip(bounds, bounds[1:]))
    if separators and not body[:separators[0]].strip(" \t"):
        ranges.pop(0)
    if separators and ranges and not body[separators[-1] + 1:].strip(" \t"):
        ranges.pop()
    cells = []
    for previous, end in ranges:
        start = previous + 1
        while start < end and body[start] in " \t":
            start += 1
        while end > start and body[end - 1] in " \t":
            end -= 1
        cells.append(TableCell(offset + start, offset + end, body[start:end]))
    return cells, bool(separators)


HTML_BLOCK_NAMES = frozenset((
    "address article aside base basefont blockquote body caption center col colgroup dd details "
    "dialog dir div dl dt fieldset figcaption figure footer form frame frameset h1 h2 h3 h4 h5 h6 "
    "head header hr html iframe legend li link main menu menuitem nav noframes ol optgroup option "
    "p param search section summary table tbody td tfoot th thead title tr track ul"
).split())
HTML_RAW_BLOCK_NAMES = frozenset(("pre", "script", "style", "textarea"))


def opening_fence(body):
    """Return a valid opening run; backticks cannot occur in its info string."""
    match = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", body)
    return match if match and not (match[1][0] == "`" and "`" in match[2]) else None


def table_interrupt(body):
    """A table ends at a blank line or another block's opening syntax."""
    body = body.rstrip("\r\n")
    if not body.strip(" \t"):
        return True
    if re.match(r" {0,3}(?:#{1,6}(?:[ \t]|$)|>|(?:[-+*]|[0-9]{1,9}[.)])[ \t]+)", body) or opening_fence(body):
        return True
    if any(re.fullmatch(r" {0,3}(?:" + re.escape(char) + r"[ \t]*){3,}", body) for char in "*-_"):
        return True
    stripped = body.lstrip(" ")
    if len(body) - len(stripped) > 3:
        return False  # Indentation alone cannot interrupt an existing table.
    if re.match(r"<!--|<\?|<![A-Z]|<!\[CDATA\[", stripped):
        return True
    tag = re.match(r"(</?)([A-Za-z][A-Za-z0-9-]*)(?=[ \t>]|/>|$)", stripped)
    if tag:
        name = tag[2].lower()
        if name in HTML_BLOCK_NAMES:
            return True
        tail = stripped[tag.end():]
        if tag[1] == "<" and name in HTML_RAW_BLOCK_NAMES and (not tail or tail[0] in " \t>"):
            return True
    complete = HTML_TAG.match(stripped) if HTML_START.match(stripped) else None
    if not complete or stripped[complete.end():].strip(" \t"):
        return False
    if stripped.startswith("</"):
        return bool(re.fullmatch(r"</[A-Za-z][A-Za-z0-9-]*[ \t]*>", stripped))
    if not tag or tag[2].lower() in HTML_RAW_BLOCK_NAMES:
        return False
    try:
        return all(re.fullmatch(r"[A-Za-z_:][A-Za-z0-9_.:-]*", name)
                   for name, _, _ in html_attributes(complete[0]))
    except ValueError:
        return False


def blocks(text):
    """Mask fenced/indented code, retaining opening-fence metadata."""
    output = []
    fences = []
    opened = None
    active = []
    comment = False
    comment_parts = []
    paragraph = False
    indented = False
    html = HTMLContexts(text)
    offset = 0
    table = None
    rows = []
    raw_html = []
    events = []
    paragraph_state = ParagraphState()
    lines = physical_lines(text, keepends=True)
    for line_no, line in enumerate(lines, 1):
        begin = offset
        offset += len(line)
        events.append(BlockLine(begin, offset, begin, tuple(active), True))
        visual = line.expandtabs(4)
        if opened:
            char, length, parts = opened
            body = continuation(visual, parts)
            if body is None:
                opened = None
            else:
                closing = re.match(r" {0,3}([`~]+)[ \t]*$", body.rstrip("\r\n"))
                if closing and set(closing[1]) == {char} and len(closing[1]) >= length:
                    opened = None
                output.append(blank(line))
                paragraph = False
                paragraph_state.clear()
                continue
        if comment and continuation(visual, comment_parts) is None:
            # HTML blocks end with their container even without a closing
            # marker. They cannot consume later prose outside a quote/list.
            comment = False
            active = []
            paragraph = False
            paragraph_state.clear()
        if table:
            parts, width, header_line = table
            body = continuation(line, parts)
            visual_body = continuation(visual, parts)
            if body is not None and (line_no == header_line + 1 or not table_interrupt(visual_body)):
                if line_no != header_line + 1:
                    cells, _ = table_cells(body, begin + len(line) - len(body))
                    rows.append(TableRow(line_no, cells, False, header_line, width))
                output.append(blank(line))
                html.cursor = offset
                html.protected.clear()
                paragraph = indented = False
                paragraph_state.clear()
                continue
            table = None
        if html.spans and html.spans[-1][1] > begin:
            # A tag begun in prose owns its complete quoted attributes. Its
            # later physical lines cannot open code blocks or containers.
            output.append(line)
            html.scan(begin, offset)
            events[-1] = paragraph_state.record(begin, offset, begin, active, False, "", line, metadata=True)
            paragraph = paragraph_state.active
            indented = False
            continue
        if not comment and line_no < len(lines):
            raw_body, raw_parts = block_body(line, active, paragraph)
            visual_body, _ = block_body(visual, active, paragraph)
            following = continuation(lines[line_no], raw_parts)
            if following is not None and not table_interrupt(visual_body) and not visual_body.startswith("    "):
                cells, header_pipe = table_cells(raw_body, begin + len(line) - len(raw_body))
                delimiters, delimiter_pipe = table_cells(following, 0)
                if ((header_pipe or delimiter_pipe) and cells and len(cells) == len(delimiters) and
                        all(re.fullmatch(r":?-+:?", cell.source) for cell in delimiters)):
                    table = (raw_parts, len(cells), line_no)
                    rows.append(TableRow(line_no, cells, True, line_no, len(cells)))
                    events[-1] = BlockLine(begin, offset, begin + len(line) - len(raw_body), tuple(raw_parts), True)
                    active = raw_parts
                    output.append(blank(line))
                    html.cursor = offset
                    html.protected.clear()
                    paragraph = indented = False
                    paragraph_state.clear()
                    continue
        if comment:
            body = continuation(visual, comment_parts)
            active = list(comment_parts)
        else:
            raw_body, raw_parts, opened_container = block_body(line, active, paragraph, details=True)
            events[-1] = BlockLine(begin, offset, begin + len(line) - len(raw_body), tuple(raw_parts), True)
            body, active = block_body(visual, active, paragraph)
        body = body.rstrip("\r\n")
        if comment or re.match(r" {0,3}<!--", body):
            comment_start = 0 if comment else line.index("<!--")
            closing = line.find("-->", comment_start)
            if closing < 0:
                output.append(blank(line))
                if not comment:
                    comment_parts = list(active)
                comment = True
                paragraph = False
                paragraph_state.clear()
                continue
            comment = False
            line = line[:comment_start] + blank(line[comment_start:closing + 3]) + line[closing + 3:]
            # The entire closing physical line belongs to the HTML block.
            # Preserve actual raw tags without parsing its literal Markdown
            # or manufacturing code indentation from the erased comment.
            html.scan(begin + closing + 3, offset, raw=True)
            end = max(offset, html.spans[-1][1] if html.spans else offset)
            raw_html.append((begin, end))
            output.append(line)
            paragraph = indented = False
            paragraph_state.clear()
            continue
        spaces = len(body) - len(body.lstrip(" "))
        match = opening_fence(body)
        if match:
            opened = (match[1][0], len(match[1]), list(active))
            fences.append((line_no, match[2].strip()))
            output.append(blank(line))
            paragraph = indented = False
            paragraph_state.clear()
        elif spaces >= 4 and (indented or not paragraph):
            output.append(blank(line))
            indented = True
            paragraph_state.clear()
        elif not body.strip(" \t"):
            output.append(line)
            events[-1] = paragraph_state.record(begin, offset, events[-1].body_start,
                                               raw_parts, opened_container, body, line)
            paragraph = paragraph_state.active
            html.scan(begin, offset)
        else:
            output.append(line)
            indented = False
            events[-1] = paragraph_state.record(begin, offset, events[-1].body_start,
                                               raw_parts, opened_container, body, line)
            paragraph = paragraph_state.active
            html.scan(begin, offset)
    return "".join(output), fences, html.spans, rows, raw_html, BlockLayout(text, events)


BACKTICKS = re.compile(r"`+")
BLANK_LINE = re.compile(r"\n[ \t]*\r?\n")
SPACES = re.compile(r"[ \t]*(?:\r?\n[ \t]*)?")
HTML_START = re.compile(r"</?[A-Za-z][\w:-]*(?:\s|/?>)")
HTML_TAG = re.compile(r"<(?:[^>\"']|\"[^\"]*\"|'[^']*')*>")


class CodeSpans:
    """Index equal delimiter runs and block boundaries once per text mask."""

    def __init__(self, text, layout=None):
        self.text = text
        self.layout = layout if layout is not None else BlockLayout(text)
        self.runs = {}
        for match in BACKTICKS.finditer(text):
            self.runs.setdefault(match.end() - match.start(), []).append(match.start())
        self.boundaries = []
        for line in self.layout.lines:
            if line.boundary:
                self.boundaries.append(line.start)
        self.boundaries.append(len(text))

    def boundary(self, start):
        """Return the next block boundary, excluding one at the opener."""
        return self.boundaries[bisect_right(self.boundaries, start)] if start < len(self.text) else len(self.text)

    def end(self, start):
        match = BACKTICKS.match(self.text, start)
        if not match:
            return None
        length = match.end() - start
        positions = self.runs.get(length, ())
        following = bisect_right(positions, start)
        boundary = self.boundary(start)
        if following < len(positions) and positions[following] < boundary:
            return positions[following] + length
        return None


class CommentSpans:
    """Index inline comment ends once; raw block comments belong to blocks()."""

    def __init__(self, text, index):
        self.text = text
        self.index = index
        self.closings = [match.start() for match in re.finditer("-->", text)]

    def end(self, start):
        # CommonMark also admits these two short inline comment forms.
        for short in ("<!-->", "<!--->"):
            if self.text.startswith(short, start):
                return start + len(short)
        following = bisect_right(self.closings, start + 3)
        if following < len(self.closings):
            end = self.closings[following] + 3
            if end <= self.index.boundary(start):
                return end
        return None  # An incomplete inline opener is ordinary literal text.


def code_end(text, start, index=None):
    return (index if index is not None else CodeSpans(text)).end(start)


def close_label(text, start, index=None):
    index = index if index is not None else CodeSpans(text)
    depth = 1
    cursor = start + 1
    while cursor < len(text):
        char = text[cursor]
        if char == "\\" and ESCAPE.match(text, cursor):
            cursor += 2
            continue
        if char == "`":
            end = code_end(text, cursor, index)
            if end:
                cursor = end
                continue
            cursor = BACKTICKS.match(text, cursor).end()
            continue
        if char == "<" and HTML_START.match(text, cursor):
            tag = HTML_TAG.match(text, cursor)
            if tag:
                cursor = tag.end()
                continue
        if char == "[":
            depth += 1
            if depth > MAX_NESTING:
                raise ValueError("Link-label nesting exceeds supported limit")
        elif char == "]":
            depth -= 1
            if not depth:
                return cursor
        elif char == "\n" and BLANK_LINE.match(text, cursor):
            return None
        cursor += 1
    return None


def spaces(text, start):
    return SPACES.match(text, start).end()


def destination(text, start):
    """Parse one escaped angle or balanced bare destination, without a title."""
    cursor = start
    if cursor < len(text) and text[cursor] == "<":
        cursor += 1
        begin = cursor
        while cursor < len(text):
            if text[cursor] == "\\" and ESCAPE.match(text, cursor):
                cursor += 2
                continue
            if text[cursor] == ">":
                return text[begin:cursor], cursor + 1
            if text[cursor] in "<\r\n":
                raise ValueError("Angle destination has an invalid delimiter or line ending")
            cursor += 1
        raise ValueError("Unclosed angle destination")
    depth = 0
    while cursor < len(text):
        char = text[cursor]
        if char == "\\" and ESCAPE.match(text, cursor):
            cursor += 2
            continue
        if char in " \t\r\n" or (char == ")" and not depth):
            break
        if char == "(":
            depth += 1
            if depth > MAX_NESTING:
                raise ValueError("Destination nesting exceeds supported limit")
        elif char == ")":
            depth -= 1
        elif char == "<" or ord(char) < 32 or ord(char) == 127:
            raise ValueError("Invalid bare destination character")
        cursor += 1
    if depth:
        raise ValueError("Unbalanced destination parentheses")
    return text[start:cursor], cursor


def title_end(text, start):
    delimiter = ")" if text[start] == "(" else text[start]
    cursor = start + 1
    while cursor < len(text):
        if text[cursor] == "\\" and ESCAPE.match(text, cursor):
            cursor += 2
            continue
        if text[cursor] == delimiter:
            return cursor + 1
        if text[cursor] == "\n" and BLANK_LINE.match(text, cursor):
            break
        cursor += 1
    raise ValueError("Unclosed or blank-line-separated link title")


def inline_destination(text, opening):
    start = spaces(text, opening + 1)
    if start > opening + 1 and start < len(text) and text[start] in "\"'":
        value, end = "", title_end(text, start)
    else:
        value, end = destination(text, start)
    tail = spaces(text, end)
    if tail > end and tail < len(text) and text[tail] in "\"'(":
        tail = spaces(text, title_end(text, tail))
    if tail >= len(text) or text[tail] != ")":
        raise ValueError("Malformed or unclosed inline link destination/title")
    return value, tail + 1


def reference_key(label):
    # CommonMark label matching uses raw syntax, not rendered/unescaped inlines.
    return re.sub(r"[ \t\r\n]+", " ", label.strip()).casefold()


def numeric_reference(value, html=False):
    """Decode an already recognized numeric token without deleting scalars.

    Strip leading zeros and bound digit count before integer conversion, even
    for HTML's unbounded spelling. Grammar/semicolon rules belong to callers.
    """
    digits = value[2:].rstrip(";")
    hexadecimal = digits.startswith(("x", "X"))
    digits = (digits[1:] if hexadecimal else digits).lstrip("0")
    if len(digits) > (6 if hexadecimal else 7):
        return "\ufffd"
    number = int(digits or "0", 16 if hexadecimal else 10)
    if number == 0 or number > 0x10FFFF or 0xD800 <= number <= 0xDFFF:
        return "\ufffd"
    if html:
        number = HTML_NUMERIC_REPLACEMENTS.get(number, number)
    return chr(number)


def markdown_entity(value):
    if value.startswith("&#"):
        return numeric_reference(value)
    return HTML_ENTITIES.get(value[1:], value)


def markdown_value(value):
    """Decode complete entities and escapes in one nonrecursive source pass."""
    return MARKDOWN_DECODE.sub(lambda match: match[0][1:] if match[0].startswith("\\")
                               else markdown_entity(match[0]), value)


def navigation_value(link):
    """Preserve Markdown scalars; apply HTML's URL-input cleanup explicitly."""
    if link.kind == "markdown":
        return markdown_value(link.destination)
    value = link.destination.strip(C0_SPACE)
    return value.translate({9: None, 10: None, 13: None})


def without_containers(text, layout=None):
    """Blank physical prefixes for continuation parsing without moving offsets."""
    lines = []
    layout = layout if layout is not None else BlockLayout(text)
    for line in layout.lines:
        lines.append(blank(text[line.start:line.body_start]) + text[line.body_start:line.end])
    return "".join(lines)


def comments(text, layout=None, ignored=None):
    """Mask actual comments; code, HTML attributes and link metadata are literal."""
    output = list(text)
    index = CodeSpans(text, layout)
    comment_index = CommentSpans(text, index)
    metadata = without_containers(text, index.layout)
    protected = {}
    cursor = 0
    while cursor < len(text):
        if cursor in protected:
            cursor = protected.pop(cursor)
            continue
        if text[cursor] == "\\" and ESCAPE.match(text, cursor):
            cursor += 2
            continue
        if text[cursor] == "`":
            end = code_end(text, cursor, index)
            if end:
                cursor = end
                continue
            cursor = BACKTICKS.match(text, cursor).end()
            continue
        if text[cursor] == "<" and HTML_START.match(text, cursor):
            tag = HTML_TAG.match(text, cursor)
            if tag:
                cursor = tag.end()
                continue
        if text[cursor] == "[":
            try:
                closing = close_label(text, cursor, index)
                if closing is not None:
                    after = closing + 1
                    if metadata[after:after + 1] == "(":
                        _, end = inline_destination(metadata, after)
                        protected[after] = end
                    elif metadata[after:after + 1] == ":":
                        begin = spaces(metadata, after + 1)
                        _, end = destination(metadata, begin)
                        following = spaces(metadata, end)
                        if following > end and following < len(metadata) and metadata[following] in "\"'(":
                            end = title_end(metadata, following)
                        protected[after] = end
            except ValueError:
                pass  # The actual inline/definition pass emits the source finding.
        if text.startswith("<!--", cursor):
            end = comment_index.end(cursor)
            if end is not None:
                output[cursor:end] = blank(text[cursor:end])
                if ignored is not None:
                    ignored.append((cursor, end))
            cursor = end if end is not None else cursor + 4
            continue
        cursor += 1
    return "".join(output)


class HTMLContexts:
    """Discover prose tags before their attribute lines reach block parsing.

    The block walker calls this only outside actual code. Inline code,
    comments and link metadata still take precedence over a tag opener.
    """

    def __init__(self, text):
        self.text = text
        self.index = CodeSpans(text)
        self.metadata = without_containers(text, self.index.layout)
        self.comments = CommentSpans(text, self.index)
        self.cursor = 0
        self.protected = {}
        self.spans = []

    def scan(self, begin, end, raw=False):
        text = self.text
        if raw:
            self.protected.clear()
        cursor = begin if raw else max(self.cursor, begin)
        while cursor < end:
            if cursor in self.protected:
                cursor = self.protected.pop(cursor)
                continue
            if not raw and text[cursor] == "\\" and ESCAPE.match(text, cursor):
                cursor += 2
                continue
            if not raw and text[cursor] == "`":
                closing = self.index.end(cursor)
                cursor = closing or BACKTICKS.match(text, cursor).end()
                continue
            if text.startswith("<!--", cursor):
                closing = text.find("-->", cursor + 4) if raw else self.comments.end(cursor)
                if raw:
                    closing = closing + 3 if closing >= 0 else len(text)
                cursor = closing if closing is not None else cursor + 4
                continue
            if text[cursor] == "<" and HTML_START.match(text, cursor):
                tag = HTML_TAG.match(text, cursor)
                if tag:
                    self.spans.append((cursor, tag.end()))
                    cursor = tag.end()
                    continue
            if not raw and text[cursor] == "[":
                try:
                    closing = close_label(text, cursor, self.index)
                    if closing is not None:
                        after = closing + 1
                        if self.metadata[after:after + 1] == "(":
                            _, finish = inline_destination(self.metadata, after)
                            self.protected[after] = finish
                        elif self.metadata[after:after + 1] == ":":
                            start = spaces(self.metadata, after + 1)
                            _, finish = destination(self.metadata, start)
                            following = spaces(self.metadata, finish)
                            if following > finish and following < len(text) and self.metadata[following] in "\"'(":
                                finish = title_end(self.metadata, following)
                            self.protected[after] = finish
                except ValueError:
                    pass  # Actual definition/inline parsing diagnoses it.
            cursor += 1
        self.cursor = cursor


def plain_emphasis(characters, literal):
    """Remove matched underscore emphasis without altering literal tokens."""
    removed = set()
    stack = []
    cursor = 0

    def punctuation(position):
        return (0 <= position < len(characters) and
                (literal[position] or characters[position] in string.punctuation or
                 unicodedata.category(characters[position])[0] in "PS"))

    while cursor < len(characters):
        if characters[cursor] != "_" or literal[cursor]:
            cursor += 1
            continue
        begin = cursor
        while cursor < len(characters) and characters[cursor] == "_" and not literal[cursor]:
            cursor += 1
        end = cursor
        previous_space = begin == 0 or characters[begin - 1].isspace()
        following_space = end == len(characters) or characters[end].isspace()
        left = not following_space and (not punctuation(end) or previous_space or punctuation(begin - 1))
        right = not previous_space and (not punctuation(begin - 1) or following_space or punctuation(end))
        can_open = left and (not right or punctuation(begin - 1))
        can_close = right and (not left or punctuation(end))
        remaining = end - begin
        if can_close:
            while remaining:
                match = None
                for position in range(len(stack) - 1, -1, -1):
                    opener = stack[position]
                    if ((opener[3] or can_open) and (opener[4] + end - begin) % 3 == 0 and
                            (opener[4] % 3 or (end - begin) % 3)):
                        continue
                    match = position
                    break
                if match is None:
                    break
                opener = stack[match]
                count = 2 if opener[2] >= 2 and remaining >= 2 else 1
                removed.update(range(opener[0] + opener[2] - count, opener[0] + opener[2]))
                removed.update(range(end - remaining, end - remaining + count))
                opener[2] -= count
                remaining -= count
                del stack[match + 1:]
                if not opener[2]:
                    stack.pop()
        if can_open and remaining:
            stack.append([end - remaining, end, remaining, can_close, end - begin])
    return "".join(char for position, char in enumerate(characters) if position not in removed)


def inline_text(text):
    """Extract heading text while preserving code, escapes and entity literals."""
    index = CodeSpans(text)
    result = []
    literal = []
    cursor = 0

    def emit(value, protected=False):
        result.extend(value)
        literal.extend([protected] * len(value))

    while cursor < len(text):
        char = text[cursor]
        if char == "\\" and cursor + 1 < len(text) and text[cursor + 1] in string.punctuation:
            emit(text[cursor + 1], True)
            cursor += 2
            continue
        if char == "`":
            end = index.end(cursor)
            if end:
                length = BACKTICKS.match(text, cursor).end() - cursor
                value = text[cursor + length:end - length].replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
                if value.startswith(" ") and value.endswith(" ") and value.strip(" "):
                    value = value[1:-1]
                emit(value, True)
                cursor = end
                continue
            cursor = BACKTICKS.match(text, cursor).end()
            continue
        if char == "<" and HTML_START.match(text, cursor):
            tag = HTML_TAG.match(text, cursor)
            if tag:
                cursor = tag.end()
                continue
        if char == "&":
            entity = ENTITY.match(text, cursor)
            if entity:
                emit(markdown_entity(entity[0]), True)
                cursor = entity.end()
                continue
        if char == "[":
            try:
                end = close_label(text, cursor, index)
            except ValueError:
                end = None
            if end is not None:
                after = end + 1
                following = None
                if after < len(text) and text[after] == "(":
                    try:
                        _, following = inline_destination(text, after)
                    except ValueError:
                        pass
                elif after < len(text) and text[after] == "[":
                    try:
                        closing = close_label(text, after, index)
                        following = closing + 1 if closing is not None else None
                    except ValueError:
                        pass
                if following is not None:
                    emit(inline_text(text[cursor + 1:end]), True)
                    cursor = following
                    continue
        emit(char)
        cursor += 1
    return plain_emphasis(result, literal)


def slug(text):
    text = inline_text(text).lower()
    text = "".join(c for c in text if c in "_- " or unicodedata.category(c)[0] in "LNM")
    return text.replace(" ", "-")


def attribute_value(value):
    """Decode once using HTML attribute, rather than text-node, entity rules."""
    def replace(match):
        raw = match[0]
        if raw.startswith("&#"):
            return numeric_reference(raw, html=True)
        name = raw[1:]
        for length in range(min(len(name), MAX_ENTITY_NAME), 0, -1):
            prefix = name[:length]
            if prefix not in HTML_ENTITIES:
                continue
            following = match.start() + 1 + length
            if (not prefix.endswith(";") and following < len(value) and
                    value[following] in string.ascii_letters + string.digits + "="):
                return raw
            return HTML_ENTITIES[prefix] + name[length:]
        return raw
    return HTML_REFERENCE.sub(replace, value)


def html_attributes(raw):
    """Yield raw attribute names/values/offsets, keeping quoted > and slashes."""
    tag = HTML_TAGNAME.match(raw)
    if tag is None:
        raise ValueError("Unsupported HTML tag syntax")
    cursor = tag.end()
    while cursor < len(raw):
        cursor = HTML_SPACE.match(raw, cursor).end()
        if cursor >= len(raw):
            raise ValueError("Unclosed HTML tag")
        if raw[cursor] == ">" or raw[cursor:cursor + 2] == "/>":
            return
        name = HTML_ATTRIBUTE.match(raw, cursor)
        if name is None:
            raise ValueError("Unsupported HTML attribute syntax")
        start = cursor
        cursor = HTML_SPACE.match(raw, name.end()).end()
        value = None
        if cursor < len(raw) and raw[cursor] == "=":
            cursor = HTML_SPACE.match(raw, cursor + 1).end()
            if cursor < len(raw) and raw[cursor] in "\"'":
                quote = raw[cursor]
                end = raw.find(quote, cursor + 1)
                if end < 0:
                    raise ValueError("Unclosed HTML attribute quote")
                value = raw[cursor + 1:end]
                cursor = end + 1
            else:
                begin = cursor
                while cursor < len(raw) and raw[cursor] not in " \t\r\n\f>":
                    cursor += 1
                value = raw[begin:cursor]
        yield name[0].lower(), value, start


class Anchors(HTMLParser):
    def __init__(self, document):
        super().__init__(convert_charrefs=True)
        self.document = document

    def handle_starttag(self, tag, _attrs):
        # Placeholder-like/non-navigation tags are outside this link contract.
        if not any(name == "id" or (tag == "a" and name in ("name", "href")) or
                   (tag == "img" and name == "src") for name, _ in _attrs):
            return
        raw = self.get_starttag_text() or ""
        # The HTMLParser input has same-length ampersand masking to prevent its
        # unconditional attribute unescape (including unbounded int conversion).
        # Recover the actual spelling through the public tag length/position.
        line, column = self.getpos()
        begin = (self.document.newlines[line - 2] + 1 if line > 1 else 0) + column
        raw = self.document.prose[begin:begin + len(raw)]
        seen = set()
        try:
            attrs = list(html_attributes(raw))
        except ValueError as error:
            self.document.issue(begin, "link-syntax", str(error))
            return
        for name, value, offset in attrs:
            line = self.document.line(begin + offset)
            relevant = name == "id" or (tag == "a" and name in ("name", "href")) or (tag == "img" and name == "src")
            if name in seen:
                if relevant:
                    self.document.findings.append(Finding(self.document.path, line, "link-syntax", "Duplicate relevant HTML attribute: " + name))
                continue
            seen.add(name)
            if value is None:
                continue
            value = attribute_value(value)
            if name == "id" or (tag == "a" and name == "name"):
                self.document.anchors.add(value)
            if (tag == "a" and name == "href") or (tag == "img" and name == "src"):
                self.document.links.append(Link(line, value, "html"))


class Markdown:
    """Parsed bounded syntax, original line offsets and deterministic findings."""

    def __init__(self, path, text, *, inline_only=False, references=None, base_line=0):
        self.path = str(path)
        self.text = text
        self.base_line = base_line
        # HTMLParser counts LF only. A lone CR becomes one LF at the same
        # source offset; CRLF retains both characters and its one LF boundary.
        text = re.sub(r"\r(?!\n)", "\n", text)
        self.newlines = [m.start() for m in re.finditer("\n", text)]
        self.links = []
        self.anchors = set()
        self.findings = []
        if inline_only:
            self.block_text, self.fences, self.html_spans, self.table_rows, raw_spans = text, [], [], [], []
            self.layout = BlockLayout(text)
        else:
            self.block_text, self.fences, self.html_spans, self.table_rows, raw_spans, self.layout = blocks(text)
        # Raw HTML block tails have no Markdown inline semantics. Keep their
        # exact source fragments separately for the HTML navigation pass.
        raw_fragments = [(begin, end, self.block_text[begin:end]) for begin, end in raw_spans]
        block_text = list(self.block_text)
        for begin, end, _ in raw_fragments:
            self.erase(block_text, begin, end, self.block_text)
        self.block_text = "".join(block_text)
        ignored = []
        self.block_text = comments(self.block_text, self.layout, ignored)
        self.references = references if references is not None else {}
        visible = list(self.block_text)
        if not inline_only:
            self._definitions(visible)
        heading_text = list("".join(visible))
        for begin, end in ignored:
            heading_text[begin:end] = [None] * (end - begin)
        self._inlines(visible, heading_text)
        if not inline_only:
            self._headings(heading_text)
        for begin, end, raw in raw_fragments:
            visible[begin:end] = raw
        self.prose = "".join(visible)
        Anchors(self).feed(self.prose.replace("&", "~"))
        for row in self.table_rows:
            for cell in row.cells[:row.width]:
                # GFM unescapes cell pipes before inline parsing, including
                # HTML and reference labels. Original ranges remain above.
                child = Markdown(self.path, cell.source.replace("\\|", "|"), inline_only=True,
                                 references=self.references, base_line=row.line - 1)
                self.links.extend(child.links)
                self.anchors.update(child.anchors)
                self.findings.extend(child.findings)

    def line(self, offset):
        return bisect_right(self.newlines, offset - 1) + 1 + self.base_line

    def issue(self, offset, code, message):
        self.findings.append(Finding(self.path, self.line(offset), code, message))

    def close(self, text, start, index=None):
        try:
            return close_label(text, start, index)
        except ValueError as error:
            self.issue(start, "link-syntax", str(error))
            return None

    @staticmethod
    def erase(output, start, end, original):
        output[start:end] = blank(original[start:end])

    def _definitions(self, visible):
        definition_text = list(self.block_text)
        for begin, end in self.html_spans:
            self.erase(definition_text, begin, end, self.block_text)
        definition_text = "".join(definition_text)
        text = without_containers(definition_text, self.layout)
        index = CodeSpans(text, self.layout)
        lines = {line.start: line for line in self.layout.lines}
        consumed = 0
        paragraph = False
        quote_depth = 0
        for line in re.finditer(r"[^\n]*(?:\n|$)", definition_text):
            if line.start() < consumed or not line[0]:
                continue
            event = lines[line.start()]
            offset = event.body_start - line.start()
            quotes = sum(part.kind == "quote" for part in event.parts)
            list_marker = event.boundary and any(part.kind == "list" for part in event.parts)
            if quotes != quote_depth or list_marker:
                paragraph = False
            quote_depth = quotes
            match = re.match(r" {0,3}\[", line[0][offset:])
            if not match:
                paragraph = event.kind == "paragraph"
                continue
            start = line.start() + offset + match.end() - 1
            closing = self.close(text, start, index)
            if closing is None or text[closing + 1:closing + 2] != ":":
                paragraph = True
                continue
            if paragraph:
                self.issue(start, "link-syntax", "Reference-like definition cannot interrupt prose; add a blank line or quote literal data")
                self.erase(visible, line.start(), line.end(), text)
                continue
            label = text[start + 1:closing]
            if not label.strip() or len(label) > 999 or re.search(r"(?<!\\)[\[\]]", label):
                self.issue(start, "reference", "Unsupported reference-definition label")
                continue
            try:
                begin = spaces(text, closing + 2)
                value, end = destination(text, begin)
                if not value and end == begin:
                    raise ValueError("Reference definition requires a destination")
                following = spaces(text, end)
                if following > end and following < len(text) and text[following] in "\"'(":
                    end = title_end(text, following)
                newline = text.find("\n", end)
                rest = text[end:newline if newline >= 0 else len(text)]
                if rest.strip(" \t\r"):
                    raise ValueError("Unsupported reference-definition continuation/title")
                parts = event.parts
                for continued in physical_lines(self.block_text[line.end():end], keepends=True):
                    if continuation(continued, parts) is None:
                        raise ValueError("Reference continuation leaves its quote/list container")
                consumed = end
                key = reference_key(label)
                if key in self.references:
                    self.issue(start, "reference", "Duplicate reference definition: " + label)
                else:
                    self.references[key] = value
                self.links.append(Link(self.line(start), value))
                self.erase(visible, line.start(), end, text)
                paragraph = False
            except ValueError as error:
                self.issue(start, "link-syntax", str(error))
                self.erase(visible, line.start(), line.end(), text)

    def _inlines(self, visible, heading_text):
        text = "".join(visible)
        index = CodeSpans(text, self.layout)
        comment_index = CommentSpans(text, index)
        cursor = 0
        destinations = {}
        labels = []

        def record(start, closing, after, end, value):
            backslashes = 0
            before = start - 2
            while before >= 0 and text[before] == "\\":
                backslashes += 1
                before -= 1
            image = start > 0 and text[start - 1] == "!" and backslashes % 2 == 0
            if not image and any(begin < start < limit and not outer_image for begin, limit, outer_image in labels):
                self.issue(start, "link-syntax", "Nested links are unsupported; images in link labels are supported")
            self.links.append(Link(self.line(start), value))
            labels.append((start, closing, image))
            if end > after:
                destinations[after] = end
                self.erase(visible, after, end, text)

        while cursor < len(text):
            while labels and cursor > labels[-1][1]:
                labels.pop()
            if cursor in destinations:
                cursor = destinations.pop(cursor)
                continue
            char = text[cursor]
            if char == "\\" and ESCAPE.match(text, cursor):
                if text[cursor + 1] == "<":
                    self.erase(visible, cursor, cursor + 2, text)
                cursor += 2
                continue
            if char == "`":
                end = code_end(text, cursor, index)
                if end:
                    self.erase(visible, cursor, end, text)
                    cursor = end
                    continue
                cursor = BACKTICKS.match(text, cursor).end()
                continue
            if text.startswith("<!--", cursor):
                end = comment_index.end(cursor)
                if end is not None:
                    self.erase(visible, cursor, end, text)
                    heading_text[cursor:end] = [None] * (end - cursor)
                else:
                    # HTMLParser otherwise treats the literal opener as an
                    # unclosed comment and hides subsequent actual HTML.
                    self.erase(visible, cursor, cursor + 1, text)
                cursor = end if end is not None else cursor + 4
                continue
            if char == "<" and HTML_START.match(text, cursor):
                tag = HTML_TAG.match(text, cursor)
                if tag:
                    heading_text[cursor:tag.end()] = [None] * (tag.end() - cursor)
                    cursor = tag.end()
                    continue
                if HTML_LINK_START.match(text, cursor):
                    self.issue(cursor, "link-syntax", "Unclosed relevant HTML link/image tag")
            if char != "[":
                cursor += 1
                continue
            closing = self.close(text, cursor, index)
            if closing is None:
                cursor += 1
                continue
            after = closing + 1
            label = text[cursor + 1:closing]
            if after < len(text) and text[after] == "(":
                try:
                    value, end = inline_destination(text, after)
                    record(cursor, closing, after, end, value)
                    cursor += 1
                    continue
                except ValueError as error:
                    self.issue(cursor, "link-syntax", str(error))
                    cursor = after + 1
                    continue
            explicit = after < len(text) and text[after] == "["
            if explicit:
                end = self.close(text, after, index)
                if end is None:
                    self.issue(cursor, "link-syntax", "Unclosed explicit reference label")
                    cursor = after + 1
                    continue
                key = reference_key(text[after + 1:end] or label)
                if key not in self.references:
                    self.issue(cursor, "reference", "Undefined explicit reference: " + key)
                else:
                    record(cursor, closing, after, end + 1, self.references[key])
                destinations[after] = end + 1
                self.erase(visible, after, end + 1, text)
                cursor += 1
                continue
            key = reference_key(label)
            if key in self.references:
                record(cursor, closing, after, after, self.references[key])
            cursor += 1

    def _headings(self, text):
        """Project visible heading text without turning erased spans into spaces.

        None retains an original source position with zero rendered width,
        including line endings inside actual comments or HTML metadata.
        """
        used = set()
        paragraph = None
        pieces = []
        for line in self.layout.lines:
            start = line.body_start
            end = line.end
            while end > start and self.text[end - 1] in "\r\n":
                end -= 1
            content_end = end
            while end > start and self.text[end - 1] in " \t":
                end -= 1
            while start < end and self.text[start] in " \t":
                start += 1
            body = "".join(char for char in text[start:end] if char is not None)
            if line.kind == "paragraph":
                if line.paragraph != paragraph:
                    pieces = []
                paragraph = line.paragraph
                pieces.append(body)
                if any(char in ("\r", "\n") for char in text[content_end:line.end]):
                    pieces.append(" ")  # Only a visible soft break separates text.
                continue
            raw = self.text[start:end]
            match = re.match(r"#{1,6}(?:[ \t]+|$)(.*)$", raw) if line.kind == "atx" else None
            if match:
                # Closing markers are source syntax, not a hash exposed by
                # removing an inline tag/comment around literal heading text.
                closing = re.search(r"[ \t]+#+[ \t]*$", match[1])
                title_end = start + match.start(1) + (closing.start() if closing else len(match[1]))
                title = "".join(char for char in text[start + match.start(1):title_end] if char is not None)
            elif line.kind == "setext" and line.paragraph == paragraph and pieces:
                title = "".join(pieces)
            else:
                paragraph = None
                pieces = []
                continue
            paragraph = None
            pieces = []
            base = slug(title.strip(" \t\r\n"))
            anchor = base
            number = 0
            while anchor in used:
                number += 1
                anchor = base + "-" + str(number)
            used.add(anchor)
            self.anchors.add(anchor)


def local_only(path):
    return any(path == prefix or path.startswith(prefix + "/") for prefix in LOCAL_ONLY)


def read_utf8(root, path):
    target = root / path
    resolved = target.resolve(strict=True)
    try:
        relative = resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("Input resolves outside repository root") from error
    if local_only(relative.as_posix()):
        raise ValueError("Local-only analysis is unavailable in a clean checkout")
    if not stat.S_ISREG(target.stat().st_mode):
        raise ValueError("Input is not a regular file")
    with target.open("rb") as stream:
        data = stream.read(MAX_DOCUMENT_BYTES + 1)
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("Document exceeds supported 16 MiB input limit")
    return data.decode("utf-8")


def input_symlink(root, path):
    """Identify an unsupported source alias before enumeration or file I/O."""
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Input path is outside the public corpus")
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            return cursor.relative_to(root).as_posix()
    return None


def source_files(root, report):
    result = set()
    for name in ROOT_FILES:
        if (root / name).exists() or (root / name).is_symlink():
            result.add(name)
    for prefix in ("docs", ".agents/skills"):
        start = root / prefix
        alias = input_symlink(root, prefix)
        if alias:
            report.findings.append(Finding(alias, 1, "input", "Symlinked input directory is unsupported"))
            continue
        if not start.exists():
            continue
        if not start.is_dir():
            report.findings.append(Finding(prefix, 1, "input", "Corpus prefix is not a directory"))
            continue

        def walk_error(error):
            path = Path(error.filename).relative_to(root).as_posix()
            report.findings.append(Finding(path, 1, "input", str(error)))

        for directory, dirs, files in os.walk(start, followlinks=False, onerror=walk_error):
            relative = Path(directory).relative_to(root)
            kept = []
            for name in sorted(dirs):
                p = relative / name
                if local_only(p.as_posix()):
                    continue
                if (root / p).is_symlink():
                    report.findings.append(Finding(p.as_posix(), 1, "input", "Symlinked input directory is unsupported"))
                else:
                    kept.append(name)
            dirs[:] = kept
            for name in sorted(files):
                if name.endswith(".md"):
                    result.add((relative / name).as_posix())
    return sorted(result)


def resolve_path(root, source, destination_path):
    path = Path(destination_path.lstrip("/")) if destination_path.startswith("/") else Path(source).parent / destination_path
    parts = []
    for part in path.parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise ValueError("Local link escapes repository root")
            parts.pop()
        else:
            parts.append(part)
    relative = Path(*parts)
    if local_only(relative.as_posix()):
        raise ValueError("Local-only analysis is unavailable in a clean checkout")
    cursor = root
    for part in parts:
        if not cursor.is_dir() or part not in {p.name for p in cursor.iterdir()}:
            raise ValueError("Missing or case-mismatched local target: " + relative.as_posix())
        cursor = cursor / part
    try:
        resolved = cursor.resolve().relative_to(root)
    except ValueError as error:
        raise ValueError("Local link follows a symlink outside repository root") from error
    if local_only(resolved.as_posix()):
        raise ValueError("Local-only analysis is unavailable in a clean checkout")
    return relative


def scan_links(root):
    """Read-only public-corpus check; temporary fixture roots need no Git."""
    report = Report()
    try:
        root = Path(root).resolve()
    except (OSError, RuntimeError) as error:
        report.findings.append(Finding(".", 1, "input", str(error)))
        return report
    if not root.is_dir():
        report.findings.append(Finding(".", 1, "input", "Root is not an existing directory"))
        return report
    documents = {}

    def load(path):
        key = Path(path).as_posix()
        if key in documents:
            return documents[key]
        try:
            alias = input_symlink(root, key)
            if alias:
                report.findings.append(Finding(key, 1, "input", "Symlinked Markdown input is unsupported: " + alias))
                documents[key] = None
                return None
            text = read_utf8(root, key)
            document = Markdown(key, text)
            documents[key] = document
            report.findings.extend(document.findings)
            return document
        except UnicodeDecodeError as error:
            data = error.object
            line = len(re.findall(br"\r\n?|\n", data[:error.start])) + 1
            report.findings.append(Finding(key, line, "read", "Invalid UTF-8 source"))
        except (OSError, ValueError, RuntimeError) as error:
            report.findings.append(Finding(key, 1, "read", str(error)))
        documents[key] = None
        return None

    try:
        paths = source_files(root, report)
    except (OSError, ValueError, RuntimeError) as error:
        report.findings.append(Finding(".", 1, "input", str(error)))
        paths = []
    report.files = len(paths)
    if not paths:
        report.findings.append(Finding(".", 1, "input", "No public Markdown input found"))
    for path in paths:
        load(path)
    for path in paths:
        document = documents[path]
        if document is None:
            continue
        for link in document.links:
            try:
                value = navigation_value(link)
                if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", value) or value.startswith("//"):
                    continue
                report.local_targets += 1
                if re.search(r"%(?![0-9a-fA-F]{2})", value):
                    raise ValueError("Malformed percent encoding in local destination")
                # External schemes were already excluded. Partition local URL
                # delimiters without urlsplit's version-dependent cleanup.
                path_query, _, raw_fragment = value.partition("#")
                raw_path = path_query.partition("?")[0]
                target_text = unquote(raw_path, encoding="utf-8", errors="strict")
                fragment = unquote(raw_fragment, encoding="utf-8", errors="strict")
                target = resolve_path(root, path, target_text) if target_text else Path(path)
                actual = root / target
                if not actual.exists():
                    raise ValueError("Missing local target: " + target.as_posix())
            except (ValueError, OSError, RuntimeError) as error:
                report.findings.append(Finding(path, link.line, "path", str(error)))
                continue
            if not fragment:
                continue
            report.fragments += 1
            try:
                line_reference = re.fullmatch(r"L([0-9]+)(?:-L([0-9]+))?", fragment)
                if actual.is_dir():
                    target = resolve_path(root, target.as_posix() + "/dummy", "README.md")
                    actual = root / target
                if line_reference:
                    size = len(physical_lines(read_utf8(root, target)))
                    begin = int(line_reference[1])
                    end = int(line_reference[2] or begin)
                    if not 1 <= begin <= end <= size:
                        raise ValueError("Source-line fragment outside file bounds: " + fragment)
                elif actual.suffix.lower() == ".md":
                    target_document = load(target)
                    if target_document is None or fragment not in target_document.anchors:
                        raise ValueError("Missing Markdown/HTML anchor: " + fragment)
                else:
                    raise ValueError("Unsupported fragment on non-Markdown source: " + fragment)
            except (ValueError, OSError, RuntimeError) as error:
                report.findings.append(Finding(path, link.line, "fragment", str(error)))
    report.findings = sorted(set(report.findings))
    return report
