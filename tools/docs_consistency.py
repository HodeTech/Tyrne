"""Bounded offline Markdown/navigation checks, governed by ADR-0043.

This is a source checker, not a renderer or a proof of architectural truth.
Offsets remain tied to original text so every diagnostic has a useful line.
"""

from bisect import bisect_right
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import string
from typing import NamedTuple
import unicodedata
from urllib.parse import unquote, urlsplit

ROOT_FILES = ("README.md", "CLAUDE.md", "AGENTS.md", "SECURITY.md", "CONTRIBUTING.md")
LOCAL_ONLY = ("docs/analysis/private", "docs/analysis/temp", "docs/analysis/technical-analysis")
MAX_DOCUMENT_BYTES = 16 * 1024 * 1024
MAX_NESTING = 64
ESCAPE = re.compile(r"\\([" + re.escape(string.punctuation) + r"])")


class Finding(NamedTuple):
    path: str
    line: int
    code: str
    message: str


class Link(NamedTuple):
    line: int
    destination: str


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
    return "".join("\n" if c == "\n" else " " for c in text)


def container(line):
    """Return body offset and quote depth; normalize one list marker."""
    offset = 0
    quotes = 0
    while True:
        match = re.match(r" {0,3}>[ \t]?", line[offset:])
        if not match:
            break
        quotes += 1
        offset += match.end()
    match = re.match(r" {0,3}(?:[-+*]|\d{1,9}[.)])[ \t]+", line[offset:])
    list_indent = match.end() if match else 0
    if match:
        offset += match.end()
    return offset, quotes, list_indent


def blocks(text):
    """Mask fenced/indented code, retaining opening-fence metadata."""
    output = []
    fences = []
    opened = None
    comment = False
    paragraph = False
    indented = False
    for line_no, line in enumerate(text.splitlines(keepends=True), 1):
        offset, quotes, list_indent = container(line)
        body = line[offset:].rstrip("\r\n")
        if not opened and (comment or re.match(r" {0,3}<!--", body)):
            begin = 0 if comment else line.index("<!--", offset)
            closing = line.find("-->", begin)
            if closing < 0:
                output.append(blank(line))
                comment = True
                paragraph = False
                continue
            comment = False
            line = line[:begin] + blank(line[begin:closing + 3]) + line[closing + 3:]
            offset, quotes, list_indent = container(line)
            body = line[offset:].rstrip("\r\n")
        spaces = len(body) - len(body.lstrip(" "))
        if opened:
            char, length, quote_depth, list_depth = opened
            raw_spaces = len(line) - len(line.lstrip(" "))
            container_ended = (quotes < quote_depth or
                               (list_depth and line.strip() and not quotes and
                                raw_spaces < list_depth))
            if container_ended:
                opened = None
            else:
                closing = re.match(r" {0,3}([`~]+)[ \t]*$", body)
                if closing and set(closing[1]) == {char} and len(closing[1]) >= length:
                    opened = None
                output.append(blank(line))
                paragraph = False
                continue
        match = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", body)
        if match and not (match[1][0] == "`" and "`" in match[2]):
            opened = (match[1][0], len(match[1]), quotes, list_indent)
            fences.append((line_no, match[2].strip()))
            output.append(blank(line))
            paragraph = indented = False
        elif (spaces >= 4 or body.startswith("\t")) and (indented or not paragraph):
            output.append(blank(line))
            indented = True
        elif not body.strip():
            output.append(line)
            paragraph = False
        else:
            output.append(line)
            indented = False
            paragraph = not bool(re.match(r" {0,3}(?:#{1,6}(?:\s|$)|[-*_]{3,}\s*$)", body))
    return "".join(output), fences


def code_end(text, start):
    """A code span requires a later equal backtick run in this paragraph."""
    match = re.match(r"`+", text[start:])
    if not match:
        return None
    length = len(match[0])
    line_start = text.rfind("\n", 0, start) + 1
    first_line = text[line_start:text.find("\n", start) if "\n" in text[start:] else len(text)]
    body_start, quote_depth, _ = container(first_line)
    heading = bool(re.match(r" {0,3}#{1,6}(?:\s|$)", first_line[body_start:]))
    end = len(text)
    for newline in re.finditer("\n", text[start + length:]):
        boundary = start + length + newline.start()
        following_end = text.find("\n", boundary + 1)
        following = text[boundary + 1:following_end if following_end >= 0 else len(text)]
        offset, quotes, list_marker = container(following)
        body = following[offset:]
        new_block = bool(re.match(r" {0,3}(?:#{1,6}(?:\s|$)|(?:=+|-+|\*{3,}|_{3,})\s*$)", body))
        if heading or not body.strip() or quotes != quote_depth or list_marker or new_block:
            end = boundary
            break
    for closing in re.finditer(r"`+", text[start + length:end]):
        if len(closing[0]) == length:
            return start + length + closing.end()
    return None


def close_label(text, start):
    depth = 1
    cursor = start + 1
    while cursor < len(text):
        char = text[cursor]
        if char == "\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if char == "`":
            end = code_end(text, cursor)
            if end:
                cursor = end
                continue
        if char == "[":
            depth += 1
            if depth > MAX_NESTING:
                raise ValueError("Link-label nesting exceeds supported limit")
        elif char == "]":
            depth -= 1
            if not depth:
                return cursor
        elif char == "\n" and re.match(r"\n[ \t]*\n", text[cursor:]):
            return None
        cursor += 1
    return None


def spaces(text, start):
    match = re.match(r"[ \t]*(?:\n[ \t]*)?", text[start:])
    return start + match.end()


def destination(text, start):
    """Parse one escaped angle or balanced bare destination, without a title."""
    cursor = start
    if cursor < len(text) and text[cursor] == "<":
        cursor += 1
        begin = cursor
        while cursor < len(text):
            if text[cursor] == "\\" and cursor + 1 < len(text):
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
        if char == "\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if char.isspace() or (char == ")" and not depth):
            break
        if char == "(":
            depth += 1
            if depth > MAX_NESTING:
                raise ValueError("Destination nesting exceeds supported limit")
        elif char == ")":
            depth -= 1
        elif char in "<\x00":
            raise ValueError("Invalid bare destination character")
        cursor += 1
    if depth:
        raise ValueError("Unbalanced destination parentheses")
    return text[start:cursor], cursor


def title_end(text, start):
    delimiter = ")" if text[start] == "(" else text[start]
    cursor = start + 1
    while cursor < len(text):
        if text[cursor] == "\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if text[cursor] == delimiter:
            return cursor + 1
        if re.match(r"\n[ \t]*\n", text[cursor:]):
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


def comments(text):
    """Mask inline comments before reference definitions, respecting code."""
    output = list(text)
    cursor = 0
    while cursor < len(text):
        if text[cursor] == "\\" and cursor + 1 < len(text):
            cursor += 2
            continue
        if text[cursor] == "`":
            end = code_end(text, cursor)
            if end:
                cursor = end
                continue
        if text.startswith("<!--", cursor):
            closing = text.find("-->", cursor + 4)
            end = closing + 3 if closing >= 0 else len(text)
            output[cursor:end] = blank(text[cursor:end])
            cursor = end
            continue
        cursor += 1
    return "".join(output)


def inline_text(text):
    """Bounded heading text: retain labels/code content, discard URI/markup."""
    text = re.sub(r"<[^>]*>", "", text)
    result = []
    cursor = 0
    while cursor < len(text):
        if text[cursor] == "[":
            try:
                end = close_label(text, cursor)
            except ValueError:
                end = None
            if end is not None:
                after = end + 1
                if after < len(text) and text[after] == "(":
                    try:
                        _, following = inline_destination(text, after)
                    except ValueError:
                        following = after
                    result.append(text[cursor + 1:end])
                    cursor = following
                    continue
                if after < len(text) and text[after] == "[":
                    try:
                        following = close_label(text, after)
                    except ValueError:
                        following = None
                    if following is not None:
                        result.append(text[cursor + 1:end])
                        cursor = following + 1
                        continue
        result.append(text[cursor])
        cursor += 1
    text = unescape(ESCAPE.sub(r"\1", "".join(result)))
    text = text.replace("`", "").replace("*", "").replace("~", "")
    return re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"\1", text)


def slug(text):
    text = inline_text(text).lower()
    text = "".join(c for c in text if c in "_- " or unicodedata.category(c)[0] in "LNM")
    return text.replace(" ", "-")


class Anchors(HTMLParser):
    def __init__(self, document):
        super().__init__(convert_charrefs=True)
        self.document = document

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if value is None:
                continue
            if name == "id" or (tag == "a" and name == "name"):
                self.document.anchors.add(value)
            if (tag == "a" and name == "href") or (tag == "img" and name == "src"):
                self.document.links.append(Link(self.getpos()[0], value))


class Markdown:
    """Parsed bounded syntax, original line offsets and deterministic findings."""

    def __init__(self, path, text):
        self.path = str(path)
        self.text = text
        self.newlines = [m.start() for m in re.finditer("\n", text)]
        self.links = []
        self.anchors = set()
        self.findings = []
        self.block_text, self.fences = blocks(text)
        self.block_text = comments(self.block_text)
        self.references = {}
        visible = list(self.block_text)
        self._definitions(visible)
        heading_text = list("".join(visible))
        self._inlines(visible, heading_text)
        self.prose = "".join(visible)
        self._headings("".join(heading_text))
        Anchors(self).feed(self.prose)

    def line(self, offset):
        return bisect_right(self.newlines, offset - 1) + 1

    def issue(self, offset, code, message):
        self.findings.append(Finding(self.path, self.line(offset), code, message))

    def close(self, text, start):
        try:
            return close_label(text, start)
        except ValueError as error:
            self.issue(start, "link-syntax", str(error))
            return None

    @staticmethod
    def erase(output, start, end, original):
        output[start:end] = blank(original[start:end])

    def _definitions(self, visible):
        text = self.block_text
        consumed = 0
        paragraph = False
        quote_depth = 0
        for line in re.finditer(r"[^\n]*(?:\n|$)", text):
            if line.start() < consumed or not line[0]:
                continue
            offset, quotes, list_marker = container(line[0])
            body = line[0][offset:]
            if quotes != quote_depth or list_marker:
                paragraph = False
            quote_depth = quotes
            match = re.match(r" {0,3}\[", line[0][offset:])
            if not match:
                paragraph = bool(body.strip()) and not bool(re.match(r" {0,3}(?:#{1,6}(?:\s|$)|(?:=+|-+)\s*$)", body))
                continue
            start = line.start() + offset + match.end() - 1
            closing = self.close(text, start)
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
                if not value:
                    raise ValueError("Reference definition requires a destination")
                following = spaces(text, end)
                if following > end and following < len(text) and text[following] in "\"'(":
                    end = title_end(text, following)
                rest = text[end:text.find("\n", end) if "\n" in text[end:] else len(text)]
                if rest.strip():
                    raise ValueError("Unsupported reference-definition continuation/title")
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
        cursor = 0
        destinations = {}
        labels = []

        def record(start, closing, after, end, value):
            image = start > 0 and text[start - 1] == "!" and not (start > 1 and text[start - 2] == "\\")
            if not image and any(begin < start < limit and not outer_image for begin, limit, outer_image in labels):
                self.issue(start, "link-syntax", "Nested links are unsupported; images in link labels are supported")
            self.links.append(Link(self.line(start), value))
            labels.append((start, closing, image))
            if end > after:
                destinations[after] = end

        while cursor < len(text):
            while labels and cursor > labels[-1][1]:
                labels.pop()
            if cursor in destinations:
                cursor = destinations.pop(cursor)
                continue
            char = text[cursor]
            if char == "\\" and cursor + 1 < len(text):
                cursor += 2
                continue
            if char == "`":
                end = code_end(text, cursor)
                if end:
                    self.erase(visible, cursor, end, text)
                    cursor = end
                    continue
            if text.startswith("<!--", cursor):
                closing = text.find("-->", cursor + 4)
                end = closing + 3 if closing >= 0 else len(text)
                self.erase(visible, cursor, end, text)
                self.erase(heading_text, cursor, end, text)
                cursor = end
                continue
            if char == "<" and re.match(r"</?[A-Za-z][\w:-]*(?:\s|/?>)", text[cursor:]):
                tag = re.match(r"<(?:[^>\"']|\"[^\"]*\"|'[^']*')*>", text[cursor:])
                if tag:
                    cursor += tag.end()
                    continue
                if re.match(r"<(?:a|img)\s", text[cursor:], re.I):
                    self.issue(cursor, "link-syntax", "Unclosed relevant HTML link/image tag")
            if char != "[":
                cursor += 1
                continue
            closing = self.close(text, cursor)
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
                end = self.close(text, after)
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
                cursor += 1
                continue
            key = reference_key(label)
            if key in self.references:
                record(cursor, closing, after, after, self.references[key])
            cursor += 1

    def _headings(self, text):
        used = set()
        bodies = [line[container(line)[0]:].rstrip() for line in text.splitlines()]
        for index, body in enumerate(bodies):
            match = re.match(r" {0,3}#{1,6}(?:[ \t]+|$)(.*)$", body)
            if match:
                title = re.sub(r"[ \t]+#+[ \t]*$", "", match[1])
            elif re.fullmatch(r" {0,3}(?:=+|-+)[ \t]*", body) and index:
                previous = bodies[index - 1]
                if not previous.strip() or previous.lstrip().startswith(("|", "#", "- ", "* ", "+ ")):
                    continue
                begin = index - 1
                while begin and bodies[begin - 1].strip() and not re.match(r" {0,3}[#|]", bodies[begin - 1]):
                    begin -= 1
                title = " ".join(line.strip() for line in bodies[begin:index])
            else:
                continue
            base = slug(title)
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
    with target.open("rb") as stream:
        data = stream.read(MAX_DOCUMENT_BYTES + 1)
    if len(data) > MAX_DOCUMENT_BYTES:
        raise ValueError("Document exceeds supported 16 MiB input limit")
    return data.decode("utf-8")


def source_files(root, report):
    result = set()
    for name in ROOT_FILES:
        if (root / name).exists():
            result.add(name)
    for prefix in ("docs", ".agents/skills"):
        start = root / prefix
        if not start.exists():
            continue
        for directory, dirs, files in os.walk(start, followlinks=False):
            relative = Path(directory).relative_to(root)
            kept = []
            for name in sorted(dirs):
                p = relative / name
                if local_only(p.as_posix()) or name in (".git", ".venv", "__pycache__"):
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
    root = Path(root).resolve()
    report = Report()
    if not root.is_dir():
        report.findings.append(Finding(".", 1, "input", "Root is not an existing directory"))
        return report
    documents = {}

    def load(path):
        key = Path(path).as_posix()
        if key in documents:
            return documents[key]
        try:
            target = root / key
            if target.is_symlink():
                report.findings.append(Finding(key, 1, "input", "Symlinked Markdown input is unsupported"))
                documents[key] = None
                return None
            text = read_utf8(root, key)
            document = Markdown(key, text)
            documents[key] = document
            report.findings.extend(document.findings)
            return document
        except UnicodeDecodeError as error:
            data = (root / key).read_bytes()
            report.findings.append(Finding(key, data[:error.start].count(b"\n") + 1, "read", "Invalid UTF-8 source"))
        except (OSError, ValueError) as error:
            report.findings.append(Finding(key, 1, "read", str(error)))
        documents[key] = None
        return None

    paths = source_files(root, report)
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
                value = unescape(ESCAPE.sub(r"\1", link.destination))
                if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", value) or value.startswith("//"):
                    continue
                report.local_targets += 1
                if re.search(r"%(?![0-9a-fA-F]{2})", value):
                    raise ValueError("Malformed percent encoding in local destination")
                url = urlsplit(value)
                target_text = unquote(url.path, encoding="utf-8", errors="strict")
                fragment = unquote(url.fragment, encoding="utf-8", errors="strict")
                target = resolve_path(root, path, target_text) if target_text else Path(path)
                actual = root / target
                if not actual.exists():
                    raise ValueError("Missing local target: " + target.as_posix())
            except (ValueError, OSError) as error:
                report.findings.append(Finding(path, link.line, "path", str(error)))
                continue
            if not fragment:
                continue
            report.fragments += 1
            try:
                line_reference = re.fullmatch(r"L(\d+)(?:-L(\d+))?", fragment)
                if actual.is_dir():
                    target = resolve_path(root, target.as_posix() + "/dummy", "README.md")
                    actual = root / target
                if line_reference:
                    size = len(read_utf8(root, target).splitlines())
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
            except (ValueError, OSError) as error:
                report.findings.append(Finding(path, link.line, "fragment", str(error)))
    report.findings = sorted(set(report.findings))
    return report
