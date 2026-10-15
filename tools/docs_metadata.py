"""Bounded offline inventory joins under Accepted ADR-0043 (Python 3.9+).

This implements mechanical metadata agreement, not architecture/governance or
unsafe soundness. The CLI remains links-only until Step12 integration completes.
"""

from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
import re
from urllib.parse import unquote

from docs_audit import check_unsafe
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


EVENT_REVIEW_FAMILIES = ("business-reviews", "code-reviews", "security-reviews",
                         "performance-optimization-reviews")
REVIEW_ROOT = "docs/analysis/reviews/"


def review_target(corpus, document, link, line):
    try:
        return local_record_target(corpus, document, link)
    except (OSError, ValueError, RuntimeError) as error:
        corpus.issue(document.path, line, "review-index", str(error))
        return None


def reachable_reviews(corpus, prefix, seeds, paths):
    """Actual local navigation; only strict descendant directories grant scope.

    A family-root/backlink is not blanket ownership of its entire archive.
    This proves discoverability, not the truth or independence of a review.
    """
    available = set(paths)
    reached = set(seeds) & available
    pending = sorted(reached, reverse=True)
    directories = {}
    while pending:
        document = corpus.load(pending.pop())
        if document is None:
            continue
        for link in document.links:
            if link.image:
                continue
            value = navigation_value(link)
            if not value.partition("#")[0].partition("?")[0]:
                continue
            try:
                target = local_record_target(corpus, document, link)
            except (OSError, ValueError, RuntimeError):
                # Navigation diagnostics belong to links; this edge grants no scope.
                continue
            additions = set()
            if target in available:
                additions.add(target)
            elif target.startswith(prefix + "/") and (corpus.root / target).is_dir():
                if target not in directories:
                    directories[target] = {path for path in available if path.startswith(target.rstrip("/") + "/")}
                additions.update(directories[target])
            for path in sorted(additions - reached, reverse=True):
                reached.add(path)
                pending.append(path)
    return reached


def companion_reviews(corpus, document, top):
    """Explicit bullet pairs under Companion plans: plan, owned by canonical."""
    companions = {}
    active = False
    for line, text in enumerate(physical_lines(document.block_text), 1):
        heading = re.match(r" {0,3}(#{1,6})[ \t]+(.+)", text)
        if heading:
            active = heading[1] == "##" and heading[2].strip() == "Companion plans"
            continue
        if not active or not re.match(r" {0,3}[-+*][ \t]+", text):
            continue
        child = Markdown(document.path, text, inline_only=True, references=document.references)
        links = [link for link in child.links if not link.image and link.label is not None]
        if len(links) != 2 or not re.search(r"\bowned by\b", inline_text(text)):
            corpus.issue(document.path, line, "review-index", "Companion plan requires one explicit canonical owner")
            continue
        plan, owner = [review_target(corpus, document, link, line) for link in links]
        if plan not in top or owner not in top or plan == owner or plan in companions:
            corpus.issue(document.path, line, "review-index", "Invalid, duplicate or missing companion/owner record")
            continue
        companions[plan] = (owner, line)
    for plan, (owner, line) in companions.items():
        if owner in companions:
            corpus.issue(document.path, line, "review-index", "Companion owner must be a canonical report")
    return set(companions)


def event_reviews(corpus, prefix, paths):
    index = prefix + "/README.md"
    top = {path for path in paths if Path(path).parent.as_posix() == prefix
           and Path(path).name not in ("README.md", "master-plan.md")}
    if index not in paths:
        corpus.issue(index, 1, "review-index", "Missing review family index")
        return
    document = corpus.load(index)
    if document is None:
        return
    companions = companion_reviews(corpus, document, top)
    canonical = top - companions
    counts = Counter()
    for line, cells in inventory_rows(corpus, document, ("Date", "Scope", "File"), "review-index"):
        links = cell_links(document, cells["File"])
        targets = [review_target(corpus, document, link, line) for link in links]
        # The first File link is the report; later links can expose evidence.
        target = targets[0] if targets else None
        if target not in canonical:
            corpus.issue(index, line, "review-index", "Missing or extra canonical review record: " + str(target))
            continue
        if any(value in top for value in targets[1:]):
            corpus.issue(index, line, "review-index", "File cell contains multiple top-level review records")
        counts[target] += 1
        if counts[target] > 1:
            corpus.issue(index, line, "review-index", "Duplicate canonical review record: " + target)
        day = inline_text(cells["Date"].source).strip()
        if not calendar(day) or not Path(target).name.startswith(day + "-"):
            corpus.issue(index, line, "review-index", "Review Date differs from dated canonical filename")
    for path in sorted(canonical - counts.keys()):
        corpus.issue(index, 1, "review-index", "Missing canonical review record: " + path)
    seeds = top | {index, prefix + "/master-plan.md"}
    reached = reachable_reviews(corpus, prefix, seeds, paths)
    for path in sorted(set(paths) - reached):
        corpus.issue(path, 1, "review-index", "Nested review is not discoverable from its family")


def master_reviews(corpus, prefix, paths):
    index = prefix + "/README.md"
    runs = {Path(path).relative_to(prefix).parts[0] for path in paths if path != index}
    valid = set()
    for run in sorted(runs):
        match = re.fullmatch(r"([0-9]{4}-[0-9]{2}-[0-9]{2})-([0-9]{2})([0-9]{2})([0-9]{2})", run)
        if not match or not calendar(match[1]) or not (int(match[2]) < 24 and int(match[3]) < 60 and int(match[4]) < 60):
            corpus.issue(prefix + "/" + run, 1, "review-index", "Invalid master-review run identity")
            continue
        valid.add(run)
        folder = prefix + "/" + run
        required = {folder + "/consolidated.md", folder + "/00-coverage-manifest.md"}
        for path in sorted(required - set(paths)):
            corpus.issue(path, 1, "review-index", "Missing required master-review artifact")
        if not any(path.startswith(folder + "/tracks/") for path in paths):
            corpus.issue(folder, 1, "review-index", "Master review requires track artifacts")
        run_paths = {path for path in paths if path.startswith(folder + "/")}
        reached = reachable_reviews(corpus, folder, {folder + "/consolidated.md"}, run_paths)
        for path in sorted(run_paths - reached):
            corpus.issue(path, 1, "review-index", "Master-review artifact is not discoverable from consolidated report")
    if index not in paths:
        corpus.issue(index, 1, "review-index", "Missing master-review index")
        return
    document = corpus.load(index)
    if document is None:
        return
    counts = Counter()
    for line, cells in inventory_rows(corpus, document, ("Run", "Commit", "Verdict"), "review-index"):
        links = cell_links(document, cells["Run"])
        if len(links) != 1:
            corpus.issue(index, line, "review-index", "Run cell requires one consolidated report link")
            continue
        run = inline_text(links[0].label).strip()
        target = review_target(corpus, document, links[0], line)
        if run not in valid or target != prefix + "/" + run + "/consolidated.md":
            corpus.issue(index, line, "review-index", "Extra or misdirected master-review run")
            continue
        counts[run] += 1
        if counts[run] > 1:
            corpus.issue(index, line, "review-index", "Duplicate master-review run: " + run)
    for run in sorted(valid - counts.keys()):
        corpus.issue(index, 1, "review-index", "Missing master-review run: " + run)


def check_reviews(corpus):
    paths = [path for path in corpus.paths if path.startswith(REVIEW_ROOT) and path != REVIEW_ROOT + "README.md"]
    families = defaultdict(list)
    for path in paths:
        relative = Path(path).relative_to(REVIEW_ROOT)
        if len(relative.parts) < 2:
            corpus.issue(path, 1, "review-index", "Unexpected review-root document")
        else:
            families[relative.parts[0]].append(path)
    for family, paths in sorted(families.items()):
        prefix = REVIEW_ROOT + family
        if family in EVENT_REVIEW_FAMILIES:
            event_reviews(corpus, prefix, paths)
        elif family == "master-review":
            master_reviews(corpus, prefix, paths)
        else:
            corpus.issue(paths[0], 1, "review-index", "Unsupported review family: " + family)


PURPOSE_ID = re.compile(r"ADR-([A-Z][0-9]+(?:\.[0-9]+)?)-[a-z0-9]+(?:-[a-z0-9]+)*")


def check_planned(corpus):
    """Dynamic ledger definitions and purpose-labelled navigation, not prose counts."""
    definitions = defaultdict(list)
    filed = defaultdict(set)
    phase_paths = [path for path in corpus.paths if re.fullmatch(r"docs/roadmap/phases/phase-[a-z][a-z0-9-]*\.md", path)]
    for path in phase_paths:
        document = corpus.load(path)
        if document is None:
            continue
        headers = [row for row in document.table_rows if row.header]
        has_planned = any("Planned identity" in [inline_text(cell.source).strip() for cell in row.cells] for row in headers)
        if not has_planned:
            if Path(path).stem not in ("phase-a", "phase-b", "phase-b2"):
                for row in headers:
                    names = [inline_text(cell.source).strip() for cell in row.cells]
                    if "ADR" not in names or "Purpose" not in names:
                        continue
                    for entry in document.table_rows:
                        if entry.header or entry.table_line != row.table_line:
                            continue
                        if len(entry.cells) != len(names):
                            corpus.issue(path, entry.line, "planned", "Future ledger row width differs from its header")
                            continue
                        identity = inline_text(entry.cells[names.index("ADR")].source).strip()
                        if identity not in ("(future)", "(none)", "(unallocated)"):
                            corpus.issue(path, entry.line, "planned", "Future ledger requires purpose identity; numeric allocations are retired")
            continue
        for line, cells in inventory_rows(corpus, document, ("Planned identity", "Purpose", "Milestone", "Historical aliases / notes"), "planned"):
            source = cells["Planned identity"].source
            identity = inline_text(source).strip()
            milestone = inline_text(cells["Milestone"].source).strip()
            if not inline_text(cells["Purpose"].source).strip() or not milestone:
                corpus.issue(path, line, "planned", "Planned ledger purpose and milestone must be present")
            if identity in ("(future)", "(none)", "(unallocated)"):
                continue
            match = PURPOSE_ID.fullmatch(identity)
            if not match:
                corpus.issue(path, line, "planned", "Invalid planned purpose identity; numeric allocations are retired: " + identity)
                continue
            definitions[identity].append((path, line))
            if milestone != match[1] or Path(path).stem != "phase-" + milestone[0].lower():
                corpus.issue(path, line, "planned", "Purpose identity differs from phase/milestone: " + identity)
            child = Markdown(path, source.replace("\\|", "|"), inline_only=True, references=document.references)
            if identity.lower() not in child.anchors:
                corpus.issue(path, line, "planned", "Planned definition requires its exact explicit anchor: " + identity.lower())
            for cell in cells.values():
                for link in cell_links(document, cell):
                    try:
                        target = local_record_target(corpus, document, link)
                    except (OSError, ValueError, RuntimeError):
                        continue
                    if Path(target).parent.as_posix() == "docs/decisions" and ADR_NAME.fullmatch(Path(target).name):
                        filed[identity].add(target)
    for identity, records in sorted(definitions.items()):
        if len(records) != 1:
            for path, line in records:
                corpus.issue(path, line, "planned", "Duplicate live purpose definition: " + identity)
        for target in sorted(filed[identity]):
            record = corpus.load(target)
            if record is not None and not re.search(r"(?<![\w-])" + re.escape(identity) + r"(?![\w-])", inline_text(record.block_text)):
                corpus.issue(target, 1, "planned", "Filed decision must preserve historical purpose alias: " + identity)
    by_anchor = {identity.lower(): identity for identity in definitions}
    for path in corpus.paths:
        document = corpus.load(path)
        if document is None:
            continue
        for link in document.links:
            if link.image or link.label is None:
                continue
            label = inline_text(link.label).strip()
            value = navigation_value(link)
            raw_path, separator, raw_fragment = value.partition("#")
            try:
                fragment = unquote(raw_fragment, encoding="utf-8", errors="strict")
            except UnicodeDecodeError:
                fragment = ""
            anchor_match = re.fullmatch(r"adr-([a-z][0-9]+(?:\.[0-9]+)?)-([a-z0-9]+(?:-[a-z0-9]+)*)", fragment)
            anchor_identity = "ADR-" + anchor_match[1].upper() + "-" + anchor_match[2] if anchor_match else None
            identity = label if PURPOSE_ID.fullmatch(label) else by_anchor.get(fragment, anchor_identity)
            if identity is None:
                continue
            if identity not in definitions:
                corpus.issue(path, link.line, "planned", "Unresolved live purpose reference: " + identity)
                continue
            try:
                target = local_record_target(corpus, document, link) if raw_path.partition("?")[0] else path
            except (OSError, ValueError, RuntimeError) as error:
                corpus.issue(path, link.line, "planned", str(error))
                continue
            ledger = any(target == owner and fragment == identity.lower() for owner, _ in definitions[identity])
            if not ledger and not (target in filed[identity] and not separator):
                corpus.issue(path, link.line, "planned", "Purpose reference does not target its ledger definition or filed record: " + identity)


def check_fences(corpus):
    """The shared block parser distinguishes actual openings and closings."""
    for path in corpus.paths:
        if not path.startswith("docs/standards/"):
            continue
        document = corpus.load(path)
        if document is not None:
            for line, info in document.fences:
                if not info:
                    corpus.issue(path, line, "standard-fence", "Standard opening fence requires a language tag")


CHECKS = {"links": check_links, "tasks": check_tasks, "adrs": check_adrs,
          "reviews": check_reviews, "planned": check_planned, "fences": check_fences,
          "unsafe": check_unsafe}


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
