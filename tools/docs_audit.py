"""Bounded Cargo/source comment reference reconciliation; no Rust soundness claim.

Python 3.9 standard library only. Unsupported relevant scope/lexical forms fail
with diagnostics rather than silently narrowing the workspace inventory.
"""

from bisect import bisect_right
import json
from pathlib import Path
import re

from docs_consistency import inline_text, physical_lines, resolve_path

BARE_KEY = re.compile(r"[A-Za-z0-9_-]+")
MANIFEST_SCALAR = re.compile(r"(?:true|false|[+-]?[0-9]+)(?![A-Za-z0-9_.-])")
NEWLINE = re.compile(r"\r\n?|\n")
RAW_STRING = re.compile(r"(?:br|cr|r)(\#*)\"")
SLASH_SUFFIX = re.compile(r"[ \t\r\n`]*/[ \t\r\n`]*([0-9][\w-]*)(?![\w-])")
SHORT_ID = re.compile(r"[0-9]{4}(?![\w-])")


class SyntaxErrorAt(ValueError):
    def __init__(self, line, message):
        super().__init__(message)
        self.line = line


class Manifest:
    """Small documented TOML profile, including quoted/dotted scope keys.

    This is not a general Cargo/TOML evaluator. Unsupported values fail closed.
    Arrays, inline tables and table/array-table declarations cover stored scope.
    """

    def __init__(self, text):
        self.text = text
        self.cursor = 0
        self.newlines = [match.start() for match in re.finditer(r"\r\n?|\n", text)]
        self.depth = 0
        self.root = {}
        self.tables = set()

    def fail(self, message):
        raise SyntaxErrorAt(bisect_right(self.newlines, self.cursor - 1) + 1, message)

    def space(self, multiline=True):
        while self.cursor < len(self.text):
            char = self.text[self.cursor]
            if char in (" \t\r\n" if multiline else " \t"):
                self.cursor += 1
            elif char == "#":
                while self.cursor < len(self.text) and self.text[self.cursor] not in "\r\n":
                    self.cursor += 1
            else:
                break

    def string(self):
        begin = self.cursor
        quote = self.text[begin]
        if self.text.startswith(quote * 3, begin):
            self.fail("Multiline manifest strings are outside the supported scope profile")
        self.cursor += 1
        while self.cursor < len(self.text):
            char = self.text[self.cursor]
            if char in "\r\n":
                self.fail("Unterminated manifest string")
            self.cursor += 1
            if char == quote:
                raw = self.text[begin:self.cursor]
                if quote == "'":
                    return raw[1:-1]
                try:
                    value = json.loads(raw)
                except ValueError:
                    self.fail("Unsupported manifest string escape/control")
                try:
                    value.encode("utf-8", errors="strict")
                except UnicodeError:
                    self.fail("Manifest string requires valid Unicode scalar values")
                return value
            if char == "\\" and quote == '"':
                self.cursor += 1
        self.fail("Unterminated manifest string")

    def key(self):
        parts = []
        while True:
            self.space(False)
            if self.cursor < len(self.text) and self.text[self.cursor] in "\"'":
                parts.append(self.string())
            else:
                match = BARE_KEY.match(self.text, self.cursor)
                if not match:
                    self.fail("Expected manifest key")
                parts.append(match[0])
                self.cursor += len(match[0])
            self.space(False)
            if self.cursor >= len(self.text) or self.text[self.cursor] != ".":
                return parts
            self.cursor += 1

    def descend(self, table, parts):
        for key in parts:
            value = table.setdefault(key, {})
            if isinstance(value, list):
                if not value or not isinstance(value[-1], dict):
                    self.fail("Manifest table conflicts with array value")
                value = value[-1]
            if not isinstance(value, dict):
                self.fail("Manifest key conflicts with a table")
            table = value
        return table

    def assign(self, table, parts, value):
        owner = self.descend(table, parts[:-1])
        if parts[-1] in owner:
            self.fail("Duplicate manifest key")
        owner[parts[-1]] = value

    def value(self):
        self.space()
        self.depth += 1
        if self.depth > 64:
            self.fail("Manifest nesting exceeds supported depth64")
        try:
            if self.cursor >= len(self.text):
                self.fail("Missing manifest value")
            char = self.text[self.cursor]
            if char in "\"'":
                return self.string()
            if char in "[{":
                closing = "]" if char == "[" else "}"
                result = [] if char == "[" else {}
                self.cursor += 1
                self.space()
                while self.cursor < len(self.text) and self.text[self.cursor] != closing:
                    if isinstance(result, dict):
                        parts = self.key()
                        if self.cursor >= len(self.text) or self.text[self.cursor] != "=":
                            self.fail("Expected inline-table assignment")
                        self.cursor += 1
                        self.assign(result, parts, self.value())
                    else:
                        result.append(self.value())
                    self.space()
                    if self.cursor < len(self.text) and self.text[self.cursor] == closing:
                        break
                    if self.cursor >= len(self.text) or self.text[self.cursor] != ",":
                        self.fail("Expected manifest comma or closing delimiter")
                    self.cursor += 1
                    self.space()
                if self.cursor >= len(self.text):
                    self.fail("Unterminated manifest container")
                self.cursor += 1
                return result
            match = MANIFEST_SCALAR.match(self.text, self.cursor)
            if not match:
                self.fail("Unsupported manifest value; use the documented literal scope profile")
            self.cursor += len(match[0])
            if match[0] in ("true", "false"):
                return match[0] == "true"
            if len(match[0]) > 128:
                self.fail("Manifest integer exceeds supported128-digit profile")
            return int(match[0])
        finally:
            self.depth -= 1

    def parse(self):
        table = self.root
        while True:
            self.space()
            if self.cursor >= len(self.text):
                return self.root
            if self.text[self.cursor] == "[":
                array = self.text.startswith("[[", self.cursor)
                self.cursor += 2 if array else 1
                parts = self.key()
                closing = "]]" if array else "]"
                if not self.text.startswith(closing, self.cursor):
                    self.fail("Unsupported or unterminated manifest table header")
                self.cursor += len(closing)
                if array:
                    owner = self.descend(self.root, parts[:-1])
                    rows = owner.setdefault(parts[-1], [])
                    if not isinstance(rows, list):
                        self.fail("Manifest array-table conflicts with a value")
                    table = {}
                    rows.append(table)
                else:
                    table = self.descend(self.root, parts)
                    identity = id(table)
                    if identity in self.tables:
                        self.fail("Duplicate manifest table declaration")
                    self.tables.add(identity)
            else:
                parts = self.key()
                if self.cursor >= len(self.text) or self.text[self.cursor] != "=":
                    self.fail("Expected manifest assignment")
                self.cursor += 1
                self.assign(table, parts, self.value())
            self.space(False)
            if self.cursor < len(self.text) and self.text[self.cursor] not in "\r\n":
                self.fail("Unexpected trailing manifest syntax")


def source_path(corpus, manifest, value):
    if not isinstance(value, str) or not value or any(char in value for char in "*?[]"):
        raise ValueError("Source scope requires a literal non-glob path")
    if Path(value).is_absolute():
        raise ValueError("Source scope requires repository-relative paths")
    return resolve_path(corpus.root, manifest, value).as_posix()


def workspace_sources(corpus):
    """All explicit and in-root path members, never just default-members."""
    manifests = {}

    def load(path):
        text = corpus.read(path)
        if text is None:
            return None
        try:
            parsed = Manifest(text).parse()
            manifests[path] = parsed
            return parsed
        except SyntaxErrorAt as error:
            corpus.issue(path, error.line, "unsafe-scope", str(error))
            return None

    root = load("Cargo.toml")
    if root is None:
        return []
    workspace = root.get("workspace", {})
    if not isinstance(workspace, dict) or not ("workspace" in root or "package" in root):
        corpus.issue("Cargo.toml", 1, "unsafe-scope", "Expected Cargo workspace or root package")
        return []
    members = workspace.get("members", [])
    if not isinstance(members, list) or not all(isinstance(value, str) for value in members):
        corpus.issue("Cargo.toml", 1, "unsafe-scope", "Workspace members must be literal paths")
        return []
    if workspace.get("exclude", []) != []:
        corpus.issue("Cargo.toml", 1, "unsafe-scope", "Nonempty workspace exclusions need supported scope handling")
        return []
    pending = ["Cargo.toml"] if "package" in root else []
    for member in members:
        try:
            pending.append(source_path(corpus, "Cargo.toml", member.rstrip("/") + "/Cargo.toml"))
        except (OSError, ValueError, RuntimeError) as error:
            corpus.issue("Cargo.toml", 1, "unsafe-scope", str(error))
    if len(set(pending)) != len(pending):
        corpus.issue("Cargo.toml", 1, "unsafe-scope", "Duplicate workspace member")
    sources = set()
    seen = set()
    while pending:
        manifest = pending.pop()
        if manifest in seen:
            continue
        seen.add(manifest)
        parsed = manifests.get(manifest) or load(manifest)
        if parsed is None:
            continue
        package = parsed.get("package")
        if not isinstance(package, dict) or not isinstance(package.get("name"), str):
            corpus.issue(manifest, 1, "unsafe-scope", "Workspace member requires package.name")
            continue
        if "workspace" in package:
            corpus.issue(manifest, 1, "unsafe-scope", "Explicit package.workspace redirection is unsupported")
        directory = Path(manifest).parent
        member_sources = set(corpus.walk(directory, suffixes=(".rs", ".s", ".S"), exclude=("target",)))
        sources.update(member_sources)
        explicit = []
        build = package.get("build", False)
        if isinstance(build, str):
            explicit.append(build)
        elif not isinstance(build, bool):
            corpus.issue(manifest, 1, "unsafe-scope", "Unsupported package.build value")
        for kind in ("lib", "bin", "test", "example", "bench"):
            targets = parsed.get(kind, [])
            targets = [targets] if isinstance(targets, dict) else targets
            if not isinstance(targets, list) or not all(isinstance(value, dict) for value in targets):
                corpus.issue(manifest, 1, "unsafe-scope", "Unsupported Cargo target table: " + kind)
                continue
            explicit.extend(target["path"] for target in targets if "path" in target)
        for value in explicit:
            try:
                target = source_path(corpus, manifest, value)
                if target not in member_sources:
                    raise ValueError("Custom source must be stored inside its package and outside generated target output")
            except (OSError, ValueError, RuntimeError) as error:
                corpus.issue(manifest, 1, "unsafe-scope", str(error))
        # Dependency tables may appear at root, workspace or target/cfg scope.
        stack = [parsed]
        while stack:
            table = stack.pop()
            for key, value in table.items():
                if key in ("dependencies", "dev-dependencies", "build-dependencies"):
                    if not isinstance(value, dict):
                        corpus.issue(manifest, 1, "unsafe-scope", "Unsupported dependency table")
                        continue
                    for name, dependency in value.items():
                        dependency_manifest = manifest
                        if isinstance(dependency, dict) and "workspace" in dependency:
                            shared = workspace.get("dependencies", {})
                            if dependency["workspace"] is not True or not isinstance(shared, dict) or name not in shared:
                                corpus.issue(manifest, 1, "unsafe-scope", "Unsupported or missing inherited workspace dependency: " + name)
                                continue
                            dependency = shared[name]
                            dependency_manifest = "Cargo.toml"
                        if isinstance(dependency, dict) and "path" in dependency:
                            try:
                                target = source_path(corpus, dependency_manifest, dependency["path"])
                                if not (corpus.root / target).is_dir():
                                    raise ValueError("Path dependency requires a package directory")
                                pending.append(source_path(corpus, dependency_manifest, dependency["path"].rstrip("/") + "/Cargo.toml"))
                            except (OSError, ValueError, RuntimeError) as error:
                                corpus.issue(manifest, 1, "unsafe-scope", str(error))
                elif isinstance(value, dict) and key != "metadata":
                    stack.append(value)
    return sorted(sources)


def comments_in_source(text, assembly=False):
    """Monotonic bounded lexical pass; comments retain exact source offsets."""
    regions = []
    strings = []
    cursor = 0
    newlines = [match.start() for match in re.finditer(r"\r\n?|\n", text)]

    def fail(begin, message):
        raise SyntaxErrorAt(bisect_right(newlines, begin - 1) + 1, message)

    while cursor < len(text):
        begin = cursor
        if text.startswith("//", cursor):
            match = NEWLINE.search(text, cursor)
            end = match.start() if match else len(text)
            content = re.sub(r"^//[/!]?[ \t]?", lambda item: " " * len(item[0]), text[cursor:end])
            regions.append((begin, content, "line"))
            cursor = end
            continue
        if text.startswith("/*", cursor):
            depth = 1
            cursor += 2
            while cursor < len(text) and depth:
                if not assembly and text.startswith("/*", cursor):
                    depth += 1
                    cursor += 2
                elif text.startswith("*/", cursor):
                    depth -= 1
                    cursor += 2
                else:
                    cursor += 1
            if depth:
                fail(begin, "Unterminated source block comment")
            content = re.sub(r"/\*|\*/|(?m:^[ \t]*\*[ \t]?)", lambda item: " " * len(item[0]), text[begin:cursor])
            regions.append((begin, content, "block"))
            continue
        boundary = cursor == 0 or not (text[cursor - 1].isalnum() or text[cursor - 1] == "_")
        raw = RAW_STRING.match(text, cursor) if boundary and not assembly else None
        if raw:
            end = text.find('"' + raw[1], raw.end())
            if end < 0:
                fail(begin, "Unterminated raw source string")
            cursor = end + 1 + len(raw[1])
            strings.append((begin, cursor, text[begin:cursor]))
            continue
        prefix = 1 if boundary and text.startswith(('b"', 'c"'), cursor) else 0
        if text[cursor + prefix:cursor + prefix + 1] == '"':
            cursor += prefix + 1
            while cursor < len(text) and text[cursor] != '"':
                cursor += 2 if text[cursor] == "\\" else 1
            if cursor >= len(text):
                fail(begin, "Unterminated source string")
            cursor += 1
            strings.append((begin, cursor, text[begin:cursor]))
            continue
        if not assembly and text[cursor] == "'":
            end = cursor + 2
            if cursor + 1 < len(text) and text[cursor + 1] == "\\":
                end = cursor + 3
                if text.startswith("u{", cursor + 2):
                    closing = text.find("}", cursor + 4)
                    if closing < 0:
                        fail(begin, "Unterminated Unicode character escape")
                    end = closing + 1
                elif text.startswith("x", cursor + 2):
                    end = cursor + 5
            if end < len(text) and text[end] == "'":
                cursor = end + 1
                continue
            # A lifetime/label has no closing apostrophe and must not eat comments.
        cursor += 1
    joined = []
    pieces = []
    start = prior_end = 0
    kind = None
    for begin, content, current_kind in regions:
        gap = text[prior_end:begin] if kind == current_kind == "line" else ""
        if pieces and kind == current_kind == "line" and re.fullmatch(r"(?:\r\n?|\n)[ \t]*", gap):
            pieces.extend((gap, content))
        else:
            if pieces:
                joined.append((start, "".join(pieces), kind))
            start, pieces, kind = begin, [content], current_kind
        prior_end = begin + len(content)
    if pieces:
        joined.append((start, "".join(pieces), kind))
    return joined, strings


UNSAFE_ID = re.compile(r"UNSAFE-[0-9]{4}-[0-9]{4}(?![\w-])")
UNSAFE_CANDIDATE = re.compile(r"\bUNSAFE-[\w-]+")
ANNOTATION = re.compile(r"\b(?:Audit:[ \t\r\n]*|audited[ \t\r\n]+under[ \t\r\n]+)", re.IGNORECASE)


def comment_tags(content):
    """All references and explicit list members are separate inventories."""
    closing_parentheses = {}
    opened = []
    for offset, char in enumerate(content):
        if char == "(":
            opened.append(offset)
        elif char == ")" and opened:
            closing_parentheses[opened.pop()] = offset
    references = []
    for match in UNSAFE_CANDIDATE.finditer(content):
        identity = match[0]
        references.append((identity, match.start(), bool(UNSAFE_ID.fullmatch(identity))))
        if not UNSAFE_ID.fullmatch(identity):
            continue
        cursor = match.end()
        while True:
            suffix = SLASH_SUFFIX.match(content, cursor)
            if not suffix:
                break
            references.append((identity[:12] + suffix[1], suffix.start(1), bool(SHORT_ID.fullmatch(suffix[1]))))
            cursor = suffix.end()
    active = set()
    for marker in ANNOTATION.finditer(content):
        cursor = marker.end()
        year = None
        while cursor < len(content):
            while cursor < len(content) and content[cursor] in " \t\r\n`":
                cursor += 1
            identity = UNSAFE_ID.match(content, cursor)
            short = SHORT_ID.match(content, cursor) if year else None
            if identity:
                value = identity[0]
                year = value[:12]
                cursor = identity.end()
            elif short:
                value = year + short[0]
                cursor += len(short[0])
            else:
                break
            active.add(value)
            while cursor < len(content) and content[cursor] in " \t\r\n`":
                cursor += 1
            if cursor < len(content) and content[cursor] == "(":
                cursor = closing_parentheses.get(cursor, len(content) - 1) + 1
                while cursor < len(content) and content[cursor] in " \t\r\n":
                    cursor += 1
            if cursor >= len(content) or content[cursor] not in "+/,":
                break
            separator = content[cursor]
            cursor += 1
            if separator != "/":
                year = None
    return references, active


def check_unsafe(corpus):
    log_path = "docs/audits/unsafe-log.md"
    document = corpus.load(log_path)
    entries = {}
    if document is not None:
        current = None
        statuses = []

        def finish():
            if current is None:
                return
            identity, line = current
            if len(statuses) != 1 or statuses[0] not in ("Active", "Removed"):
                corpus.issue(log_path, line, "unsafe-log", "Unsafe entry requires one Active/Removed status: " + identity)
            elif identity in entries:
                corpus.issue(log_path, line, "unsafe-log", "Duplicate unsafe log identity: " + identity)
            else:
                entries[identity] = (statuses[0], line)

        for line, text in enumerate(physical_lines(document.block_text), 1):
            heading = re.match(r" {0,3}###[ \t]+(UNSAFE-[\w-]+)(?:[ \t]|$)", text)
            if heading:
                finish()
                current = (heading[1], line)
                statuses = []
                if not UNSAFE_ID.fullmatch(heading[1]):
                    corpus.issue(log_path, line, "unsafe-log", "Malformed unsafe log identity: " + heading[1])
            elif re.match(r" {0,3}#{1,3}[ \t]", text):
                finish()
                current = None
                statuses = []
            elif current:
                status = re.fullmatch(r"- \*\*Status:\*\*[ \t]*(.+)", text)
                if status:
                    value = inline_text(status[1]).strip()
                    normalized = re.match(r"(Active|Removed)(?=$|\.(?:[ \t]|$)|[ \t]+—[ \t]+)", value)
                    statuses.append(normalized[1] if normalized else value)
        finish()
    annotations = set()
    sources = set(workspace_sources(corpus))
    for path in sorted(sources):
        text = corpus.read(path)
        if text is None:
            continue
        newlines = [match.start() for match in re.finditer(r"\r\n?|\n", text)]
        try:
            regions, strings = comments_in_source(text, Path(path).suffix in (".s", ".S"))
        except SyntaxErrorAt as error:
            corpus.issue(path, error.line, "unsafe-source", str(error))
            continue
        for begin, content, _ in regions:
            references, active = comment_tags(content)
            annotations.update(active)
            for identity, offset, valid in references:
                line = bisect_right(newlines, begin + offset - 1) + 1
                if not valid or identity not in entries:
                    corpus.issue(path, line, "unsafe-ref", "Malformed or unresolved unsafe reference: " + identity)
                elif identity in active and entries[identity][0] == "Removed":
                    corpus.issue(path, line, "unsafe-ref", "Removed unsafe entry has an active annotation: " + identity)
        # Source redirection must stay within the enumerated workspace inventory.
        visible = list(text)
        for begin, content, _ in regions:
            visible[begin:begin + len(content)] = " " * len(content)
        for begin, end, _ in strings:
            visible[begin:end] = " " * (end - begin)
        code = "".join(visible)
        redirections = list(re.finditer(r"\b(?:include|include_str)!\s*\(|#\s*\[\s*path\s*=|(?m:^[ \t]*\.include[ \t]+)", code))
        for match in redirections:
            literal = next((raw for begin, _, raw in strings if begin >= match.end() and not code[match.end():begin].strip()), None)
            try:
                if literal is None or not literal.startswith('"'):
                    raise ValueError("Dynamic/raw source redirection requires supported scope handling")
                destination = json.loads(literal)
                if not isinstance(destination, str):
                    raise ValueError("Source redirection requires a literal path")
                target = source_path(corpus, path, destination)
                if target not in sources:
                    raise ValueError("Redirected source must be stored .rs/.s/.S inside the enumerated workspace scope")
                if (match[0].lstrip().startswith("include!") or match[0].startswith("#")) and Path(target).suffix != ".rs":
                    raise ValueError("Rust include!/path attributes require stored .rs source in this profile")
            except (OSError, ValueError, RuntimeError) as error:
                corpus.issue(path, bisect_right(newlines, match.start() - 1) + 1, "unsafe-scope", str(error))
    for identity, (status, line) in sorted(entries.items()):
        if status == "Active" and identity not in annotations:
            corpus.issue(log_path, line, "unsafe-log", "Active entry has no active source audit annotation: " + identity)
