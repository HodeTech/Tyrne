"""Bounded offline inventory joins under Accepted ADR-0043 (Python 3.9+).

This implements mechanical metadata agreement, not architecture/governance or
unsafe soundness. The CLI remains links-only until Step12 integration completes.
"""

from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
import re
from urllib.parse import unquote

from docs_consistency import Corpus, Markdown, check_links, inline_text, navigation_value, physical_lines, resolve_path

LIFECYCLE = ("Draft", "Ready", "In Progress", "In Review", "Done", "Blocked", "Superseded")
TASK_NAME = re.compile(r"(T-[0-9]{3,})-[a-z0-9][a-z0-9-]*\.md$")
ADR_NAME = re.compile(r"([0-9]{4})-[a-z0-9][a-z0-9-]*\.md$")
ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

# Reviewed exact baseline destinations under T048/ADR0043. Only a missing
# date_done is exempt; present invalid dates and renamed/new files still fail.
LEGACY_DONE_WITHOUT_DATE = frozenset("docs/analysis/tasks/phase-a/" + name for name in (
    "T-001-capability-table-foundation.md", "T-002-kernel-object-storage.md",
    "T-003-ipc-primitives.md", "T-004-cooperative-scheduler.md", "T-005-two-task-ipc-demo.md",
)) | frozenset("docs/analysis/tasks/phase-b/" + name for name in (
    "T-006-raw-pointer-scheduler-api.md", "T-007-idle-task-typed-deadlock.md",
    "T-008-architecture-docs.md", "T-009-timer-init-cntvct.md", "T-011-missing-tests-bundle.md",
    "T-012-exception-and-irq-infrastructure.md", "T-013-el-drop-to-el1.md",
    "T-014-idle-dispatch-fallback.md", "T-015-endpoint-rollback-cancel-recv.md",
    "T-016-mmu-activation.md", "T-017-physical-memory-manager.md", "T-018-address-space-kernel-object.md",
))


def lifecycle(value):
    """Normalize the adopted state plus an explicit parenthetical qualification."""
    value = inline_text(value).strip()
    for state in LIFECYCLE:
        if value == state or (value.startswith(state + " (") and value.endswith(")")):
            return state
        if state in ("Blocked", "Superseded") and value.startswith(state + " — "):
            return state
        if state == "Superseded" and value.startswith(state + " by "):
            return state
    return None


def calendar(value):
    if not ISO_DATE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def header(corpus, document, code):
    """First H1 and leading Markdown metadata, excluding body examples."""
    lines = physical_lines(document.text)
    first = next((n for n, line in enumerate(lines) if line.strip()), None)
    if first is None or not re.match(r" {0,3}#[ \t]+", lines[first]):
        corpus.issue(document.path, 1, code, "Missing first-level record heading")
        return "", {}
    title = re.sub(r" {0,3}#[ \t]+", "", lines[first], count=1).strip()
    title = re.sub(r"[ \t]+#+[ \t]*$", "", title)
    fields = {}
    for n in range(first + 1, len(lines)):
        line = lines[n]
        if not line.strip():
            continue
        match = re.fullmatch(r"- \*\*([^*]+):\*\*[ \t]*(.*)", line)
        if match:
            key = match[1].casefold()
            if key in fields:
                corpus.issue(document.path, n + 1, code, "Duplicate metadata field: " + match[1])
            else:
                fields[key] = (match[2].strip(), n + 1)
        elif not line.startswith((" ", "\t")):
            break
    return title, fields


def inventory_rows(corpus, document, required, code):
    """One declared inventory table; source rows must match its full width."""
    candidates = []
    for row in document.table_rows:
        if row.header:
            names = [inline_text(cell.source).strip() for cell in row.cells]
            if all(name in names for name in required):
                candidates.append((row, names))
    if len(candidates) != 1:
        corpus.issue(document.path, 1, code, "Missing or ambiguous inventory table: " + ", ".join(required))
        return []
    opening, names = candidates[0]
    if len(set(names)) != len(names) or any(not name for name in names):
        corpus.issue(document.path, opening.line, code, "Duplicate or empty inventory column")
        return []
    result = []
    for row in document.table_rows:
        if row.header or row.table_line != opening.table_line:
            continue
        if len(row.cells) != len(names):
            corpus.issue(document.path, row.line, code, "Inventory row width differs from its header")
            continue
        result.append((row.line, dict(zip(names, row.cells))))
    return result


def cell_links(document, cell):
    child = Markdown(document.path, cell.source.replace("\\|", "|"), inline_only=True,
                     references=document.references)
    return [link for link in child.links if link.kind == "markdown" and not link.image and link.label is not None]


def local_record_target(corpus, document, link):
    value = navigation_value(link)
    if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", value) or value.startswith("//"):
        raise ValueError("Inventory record requires a local Markdown target")
    if re.search(r"%(?![0-9a-fA-F]{2})", value):
        raise ValueError("Malformed percent encoding in inventory target")
    raw_path = value.partition("#")[0].partition("?")[0]
    path = unquote(raw_path, encoding="utf-8", errors="strict")
    return resolve_path(corpus.root, document.path, path).as_posix()


def required_field(corpus, document, fields, name, code):
    value, line = fields.get(name, ("", 1))
    if not value:
        corpus.issue(document.path, line, code, "Missing metadata field: " + name)
    return value, line


def check_tasks(corpus):
    """Exact phase-local membership, global IDs and adopted lifecycle dates."""
    task_paths = [path for path in corpus.paths if path.startswith("docs/analysis/tasks/")
                  and Path(path).name.startswith("T-")]
    records = {}
    identities = defaultdict(list)
    phase_pattern = r"docs/analysis/tasks/phase-[^/]+"
    phases = {Path(path).parent.as_posix() for path in corpus.paths
              if re.fullmatch(phase_pattern, Path(path).parent.as_posix())
              and (Path(path).name == "README.md" or path in task_paths)}
    for path in task_paths:
        document = corpus.load(path)
        if document is None:
            continue
        match = TASK_NAME.fullmatch(Path(path).name)
        if not match or not re.fullmatch(phase_pattern, Path(path).parent.as_posix()):
            corpus.issue(path, 1, "task", "Unsupported task filename or phase placement")
            continue
        identity = match[1]
        identities[identity].append(path)
        title, fields = header(corpus, document, "task")
        if not re.match(re.escape(identity) + r"[ \t]+[—-][ \t]+\S", title):
            corpus.issue(path, 1, "task", "Task heading differs from filename identity: " + identity)
        raw, line = required_field(corpus, document, fields, "status", "task")
        state = lifecycle(raw)
        if state is None:
            corpus.issue(path, line, "task", "Unsupported lifecycle status: " + raw)
        records[path] = (identity, state)
        if "date_done" in fields:
            value, date_line = fields["date_done"]
            if not calendar(inline_text(value).strip()):
                corpus.issue(path, date_line, "task", "date_done requires a real ISO calendar date")
            if state != "Done":
                corpus.issue(path, date_line, "task", "Only Done tasks may carry date_done")
        elif state == "Done" and path not in LEGACY_DONE_WITHOUT_DATE:
            corpus.issue(path, line, "task", "Newly completed task requires date_done; Created is not an exemption")
    for identity, paths in sorted(identities.items()):
        if len(paths) > 1:
            for path in paths:
                corpus.issue(path, 1, "task", "Duplicate project-global task identity: " + identity)
    for phase in sorted(phases):
        index = phase + "/README.md"
        expected = {path for path in task_paths if Path(path).parent.as_posix() == phase}
        if index not in corpus.paths:
            corpus.issue(index, 1, "task-index", "Missing phase task index")
            continue
        document = corpus.load(index)
        if document is None:
            continue
        rows = inventory_rows(corpus, document, ("ID", "Title", "Status"), "task-index")
        counts = Counter()
        for line, cells in rows:
            if cells["ID"].source.strip() == "_(pending)_":
                if expected or len(rows) != 1 or any(inline_text(cell.source).strip() != "—" for name, cell in cells.items() if name != "ID"):
                    corpus.issue(index, line, "task-index", "Pending placeholder requires an otherwise empty task inventory")
                continue
            identity_links = cell_links(document, cells["ID"])
            links = identity_links or cell_links(document, cells["Title"])
            if len(links) != 1:
                corpus.issue(index, line, "task-index", "Expected one task record link in ID or Title")
                continue
            try:
                target = local_record_target(corpus, document, links[0])
            except (OSError, ValueError, RuntimeError) as error:
                corpus.issue(index, line, "task-index", str(error))
                continue
            counts[target] += 1
            if counts[target] > 1:
                corpus.issue(index, line, "task-index", "Duplicate task index record: " + target)
            if target not in expected:
                corpus.issue(index, line, "task-index", "Extra task index record: " + target)
            if target in records:
                identity, state = records[target]
                visible_id = identity_links[0].label if identity_links else cells["ID"].source
                if inline_text(visible_id).strip() != identity:
                    corpus.issue(index, line, "task-index", "Index task identity differs from target: " + identity)
                if lifecycle(cells["Status"].source) != state or state is None:
                    corpus.issue(index, line, "task-index", "Index lifecycle status differs from task: " + identity)
        for path in sorted(expected - counts.keys()):
            corpus.issue(index, 1, "task-index", "Missing task index record: " + path)
        if not expected and not rows:
            corpus.issue(index, 1, "task-index", "Empty task index requires one pending placeholder")


def check_adrs(corpus):
    """Join exact filed-record membership/title/status/full Date metadata."""
    index = "docs/decisions/README.md"
    paths = [path for path in corpus.paths if path.startswith("docs/decisions/")
             and path not in (index, "docs/decisions/template.md")]
    if not paths and index not in corpus.paths:
        return
    records = {}
    identities = defaultdict(list)
    for path in paths:
        document = corpus.load(path)
        if document is None:
            continue
        match = ADR_NAME.fullmatch(Path(path).name)
        if not match or Path(path).parent.as_posix() != "docs/decisions":
            corpus.issue(path, 1, "adr", "Unexpected ADR document or filename")
            continue
        number = match[1]
        identities[number].append(path)
        title, fields = header(corpus, document, "adr")
        heading = re.fullmatch(r"([0-9]{4})[ \t]+[—-][ \t]+(.+)", title)
        if not heading or heading[1] != number:
            corpus.issue(path, 1, "adr", "ADR heading differs from filename identity: " + number)
        raw_status, status_line = required_field(corpus, document, fields, "status", "adr")
        state = inline_text(raw_status).strip()
        if not re.fullmatch(r"(?:Proposed|Accepted|Deprecated|Deferred|Superseded by [0-9]{4}(?: \(.+\))?)", state):
            corpus.issue(path, status_line, "adr", "Unsupported ADR status: " + raw_status)
        raw_date, date_line = required_field(corpus, document, fields, "date", "adr")
        recorded = inline_text(raw_date).strip()
        dates = re.findall(r"(?<!\w)([0-9]{4}-\d+-[\w-]+)", recorded)
        leading_date = re.match(ISO_DATE.pattern + r"(?=$|[ \t(;])", recorded)
        if not leading_date or not dates or not all(calendar(value) for value in dates):
            corpus.issue(path, date_line, "adr", "ADR Date requires real ISO dates, preserving any prose qualification")
        records[path] = (number, heading[2] if heading else "", state, recorded)
    for number, duplicate in sorted(identities.items()):
        if len(duplicate) > 1:
            for path in duplicate:
                corpus.issue(path, 1, "adr", "Duplicate filed ADR identity: " + number)
    if index not in corpus.paths:
        corpus.issue(index, 1, "adr-index", "Missing ADR index")
        return
    document = corpus.load(index)
    if document is None:
        return
    counts = Counter()
    for line, cells in inventory_rows(corpus, document, ("#", "Title", "Status", "Date"), "adr-index"):
        links = cell_links(document, cells["Title"])
        if len(links) != 1:
            corpus.issue(index, line, "adr-index", "Expected one canonical ADR title link")
            continue
        try:
            target = local_record_target(corpus, document, links[0])
        except (OSError, ValueError, RuntimeError) as error:
            corpus.issue(index, line, "adr-index", str(error))
            continue
        counts[target] += 1
        if counts[target] > 1:
            corpus.issue(index, line, "adr-index", "Duplicate ADR index record: " + target)
        if target not in paths:
            corpus.issue(index, line, "adr-index", "Extra ADR index record: " + target)
        if target in records:
            actual = (inline_text(cells["#"].source).strip(), links[0].label,
                      inline_text(cells["Status"].source).strip(), inline_text(cells["Date"].source).strip())
            for name, expected, value in zip(("number", "title", "status", "Date"), records[target], actual):
                if expected != value:
                    corpus.issue(index, line, "adr-index", "ADR " + name + " differs from header: " + target)
    for path in sorted(set(paths) - counts.keys()):
        corpus.issue(index, 1, "adr-index", "Missing ADR index record: " + path)


CHECKS = {"links": check_links, "tasks": check_tasks, "adrs": check_adrs}


def scan_docs(root, *, checks):
    """Run explicitly selected implemented families during Step12 development."""
    selected = list(checks)
    if not selected or len(set(selected)) != len(selected) or any(name not in CHECKS for name in selected):
        raise ValueError("Select distinct implemented check families: " + ", ".join(CHECKS))
    corpus = Corpus(root, checks=selected)
    if corpus.root is not None:
        for name in selected:
            CHECKS[name](corpus)
    corpus.report.findings = sorted(set(corpus.report.findings))
    return corpus.report
