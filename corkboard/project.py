"""Load a repo's .project/ folder: its config, releases and items, and what follows from them.

This module only reads. An item keeps its header fields and body exactly as the file has them,
and its description, subtasks and log are read from that body, so the code that writes items
can change one line and leave the rest of the file as it was.

A file corkboard can't read is skipped and noted in `Project.problems`, so one bad file never
stops the rest from loading. Checking values against the rules (allowed statuses, links that
point nowhere and so on) is `corkboard check`'s job, not this module's.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import header

PROJECT_DIR = ".project"
CONFIG_FILE = "config.yml"

TYPES = ("epic", "task", "bug")
STATUSES = ("backlog", "todo", "in-progress", "waiting", "done", "cancelled")
PRIORITIES = ("high", "medium", "low")
OWNERS = ("claude", "me")
RELEASE_STATUSES = ("planned", "active", "released")

# Header fields in the order corkboard writes them. The first seven are required.
ITEM_FIELDS = (
    "id",
    "type",
    "title",
    "status",
    "priority",
    "owner",
    "created",
    "parent",
    "release",
    "labels",
    "blocked_by",
    "related",
    "duplicate_of",
)
REQUIRED_FIELDS = ITEM_FIELDS[:7]
RELEASE_FIELDS = ("name", "status", "date")

# What a missing required field reads as, the same defaults `corkboard new` uses.
DEFAULTS = {"type": "task", "status": "todo", "priority": "medium", "owner": "claude"}

SUBTASKS_HEADING = "## Subtasks"
LOG_HEADING = "## Log"

_ID = re.compile(r"([A-Z][A-Z0-9]*)-([0-9]+)")
CODE_FENCE = re.compile(r"\s*(```|~~~)")
HEADING = re.compile(r"#{1,2} \S.*")
SUBTASK_LINE = re.compile(r"- \[([ xX])\] (.+)")
LOG_LINE = re.compile(r"- ([0-9]{4}-[0-9]{2}-[0-9]{2}) ([0-9]{2}:[0-9]{2}) (me|claude): (.+)")


@dataclass(frozen=True)
class Problem:
    """A file corkboard couldn't fully read."""

    path: Path
    message: str

    def __str__(self) -> str:
        return f"{self.path.name}: {self.message}"


@dataclass(frozen=True)
class Subtask:
    text: str
    done: bool


@dataclass(frozen=True)
class LogEntry:
    date: str
    time: str
    who: str
    text: str


@dataclass
class Item:
    """An epic, task or bug: one file in items/."""

    path: Path
    fields: dict[str, header.Value]
    body: str
    description: str = ""
    subtasks: list[Subtask] = field(default_factory=list)
    log: list[LogEntry] = field(default_factory=list)
    has_subtasks_section: bool = False
    # Lines inside ## Subtasks or ## Log that don't follow the format, as (line in body, text).
    unreadable_lines: list[tuple[int, str]] = field(default_factory=list)

    @property
    def id(self) -> str:
        return _text(self.fields.get("id"))

    @property
    def number(self) -> int:
        match = _ID.fullmatch(self.id)
        return int(match.group(2)) if match else 0

    @property
    def type(self) -> str:
        return _text(self.fields.get("type"), DEFAULTS["type"])

    @property
    def title(self) -> str:
        return _text(self.fields.get("title"))

    @property
    def status(self) -> str:
        return _text(self.fields.get("status"), DEFAULTS["status"])

    @property
    def priority(self) -> str:
        return _text(self.fields.get("priority"), DEFAULTS["priority"])

    @property
    def owner(self) -> str:
        return _text(self.fields.get("owner"), DEFAULTS["owner"])

    @property
    def created(self) -> str:
        return _text(self.fields.get("created"))

    @property
    def parent(self) -> str | None:
        return _text(self.fields.get("parent")) or None

    @property
    def release(self) -> str | None:
        """The item's own release field. `Project.release_of` also follows its epic."""
        return _text(self.fields.get("release")) or None

    @property
    def labels(self) -> list[str]:
        return _list(self.fields.get("labels"))

    @property
    def blocked_by(self) -> list[str]:
        return _list(self.fields.get("blocked_by"))

    @property
    def related(self) -> list[str]:
        return _list(self.fields.get("related"))

    @property
    def duplicate_of(self) -> str | None:
        return _text(self.fields.get("duplicate_of")) or None

    @property
    def is_epic(self) -> bool:
        return self.type == "epic"


@dataclass
class Release:
    """One file in releases/."""

    path: Path
    fields: dict[str, header.Value]
    body: str

    @property
    def name(self) -> str:
        return _text(self.fields.get("name")) or self.path.stem

    @property
    def status(self) -> str:
        return _text(self.fields.get("status"), "planned")

    @property
    def date(self) -> str | None:
        return _text(self.fields.get("date")) or None

    @property
    def goal(self) -> str:
        return self.body.strip()


@dataclass
class Project:
    """A loaded .project/ folder."""

    root: Path
    config: dict[str, header.Value]
    releases: dict[str, Release]
    items: dict[str, Item]
    problems: list[Problem] = field(default_factory=list)

    @property
    def name(self) -> str:
        return _text(self.config.get("name")) or self.root.parent.name

    @property
    def prefix(self) -> str:
        return _text(self.config.get("prefix"))

    def item(self, item_id: str) -> Item | None:
        return self.items.get(item_id.upper())

    def sorted_items(self) -> list[Item]:
        return sorted(self.items.values(), key=lambda item: item.number)

    def epic_of(self, item: Item) -> Item | None:
        epic = self.items.get(item.parent or "")
        return epic if epic is not None and epic.is_epic else None

    def release_of(self, item: Item) -> str | None:
        """The item's release: its own, or else its epic's."""
        if item.release:
            return item.release
        epic = self.epic_of(item)
        return epic.release if epic else None

    def children(self, epic: Item) -> list[Item]:
        """The tasks and bugs whose parent is this epic, in number order."""
        return [item for item in self.sorted_items() if item.parent == epic.id]

    def blocks(self, item: Item) -> list[Item]:
        """The items that list this one in their blocked_by."""
        return [other for other in self.sorted_items() if item.id in other.blocked_by]

    def related_to(self, item: Item) -> list[Item]:
        """Related items from both sides: the ones this item lists and the ones that list it."""
        ids = set(item.related)
        ids.update(other.id for other in self.items.values() if item.id in other.related)
        ids.discard(item.id)
        return sorted((self.items[i] for i in ids if i in self.items), key=lambda i: i.number)

    def duplicated_by(self, item: Item) -> list[Item]:
        return [other for other in self.sorted_items() if other.duplicate_of == item.id]

    def open_blockers(self, item: Item) -> list[str]:
        """IDs in blocked_by that aren't done. An ID with no item counts as open."""
        return [
            blocker
            for blocker in item.blocked_by
            if blocker not in self.items or self.items[blocker].status != "done"
        ]

    def is_blocked(self, item: Item) -> bool:
        return bool(self.open_blockers(item))

    def epic_progress(self, epic: Item) -> tuple[int, int]:
        """Done tasks and bugs out of all of them, leaving out cancelled ones."""
        return _progress(self.children(epic))

    def release_progress(self, name: str) -> tuple[int, int]:
        """Done tasks and bugs in the release out of all of them, leaving out cancelled ones."""
        work = [i for i in self.items.values() if not i.is_epic and self.release_of(i) == name]
        return _progress(work)

    def active_release(self) -> Release | None:
        active = [release for release in self.releases.values() if release.status == "active"]
        return active[0] if active else None

    def mentions(self, item_id: str) -> list[str]:
        """Docs (as paths under .project/) and other items whose text mentions this ID.

        A mention is the ID on its own, so EX-12 doesn't count inside EX-120 or XEX-12. Only an
        item's body is searched; its header links are shown separately.
        """
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(item_id)}(?![0-9])")
        found: list[str] = []
        docs = self.root / "docs"
        if docs.is_dir():
            for path in sorted(docs.rglob("*.md"), key=lambda p: natural_key(p.as_posix())):
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                if pattern.search(text):
                    found.append(path.relative_to(self.root).as_posix())
        found += [
            other.id
            for other in self.sorted_items()
            if other.id != item_id and pattern.search(other.body)
        ]
        return found


def find_root(start: Path) -> Path | None:
    """The .project/ folder for `start`: the first one up from it that has a config.yml."""
    start = start.resolve()
    for folder in (start, *start.parents):
        candidate = folder / PROJECT_DIR
        if (candidate / CONFIG_FILE).is_file():
            return candidate
    return None


def load(root: Path) -> Project:
    """Load the .project/ folder at `root`."""
    problems: list[Problem] = []

    config: dict[str, header.Value] = {}
    config_path = root / CONFIG_FILE
    try:
        config = header.read_fields(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, header.HeaderError) as error:
        problems.append(Problem(config_path, str(error)))

    releases: dict[str, Release] = {}
    for path in _markdown_files(root / "releases"):
        parsed = _read(path, problems)
        if parsed is None:
            continue
        release = Release(path, *parsed)
        if release.name in releases:
            other = releases[release.name].path.name
            problems.append(Problem(path, f"release {release.name} is also in {other}"))
            continue
        releases[release.name] = release

    items: dict[str, Item] = {}
    for path in _markdown_files(root / "items"):
        parsed = _read(path, problems)
        if parsed is None:
            continue
        item = parse_item(path, *parsed)
        if not item.id:
            problems.append(Problem(path, "the header has no id"))
            continue
        if item.id in items:
            problems.append(Problem(path, f"{item.id} is also used by {items[item.id].path.name}"))
            continue
        items[item.id] = item

    return Project(root, config, releases, items, problems)


def parse_id(item_id: str) -> tuple[str, int] | None:
    """An ID's prefix and number, such as ("EX", 12) for EX-12."""
    match = _ID.fullmatch(item_id)
    return (match.group(1), int(match.group(2))) if match else None


def natural_key(name: str) -> list[str | int]:
    """Sort key that puts v0.2 before v0.10 and EX-2 before EX-10."""
    return [int(part) if part.isdigit() else part for part in re.split(r"([0-9]+)", name)]


def _markdown_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(folder.glob("*.md"), key=lambda path: natural_key(path.name))


def _read(path: Path, problems: list[Problem]) -> tuple[dict[str, header.Value], str] | None:
    try:
        return header.read(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, header.HeaderError) as error:
        problems.append(Problem(path, str(error)))
        return None


def parse_item(path: Path, fields: dict[str, header.Value], body: str) -> Item:
    """An item from its header fields and body, with its description, subtasks and log read."""
    item = Item(path, fields, body)
    description: list[str] = []
    section = "description"
    in_code = False
    for number, line in enumerate(body.split("\n"), start=1):
        if CODE_FENCE.match(line):
            in_code = not in_code
        if not in_code and HEADING.fullmatch(line):
            if line.strip() == SUBTASKS_HEADING:
                section = "subtasks"
                item.has_subtasks_section = True
                continue
            if line.strip() == LOG_HEADING:
                section = "log"
                continue
            if section != "description":
                section = "other"  # free text after a parsed section: kept in the body only
        if section == "description":
            description.append(line)
        elif section == "subtasks" and line.strip():
            match = SUBTASK_LINE.fullmatch(line.rstrip())
            if match:
                item.subtasks.append(Subtask(match.group(2), match.group(1) != " "))
            else:
                item.unreadable_lines.append((number, line))
        elif section == "log" and line.strip():
            match = LOG_LINE.fullmatch(line.rstrip())
            if match:
                item.log.append(LogEntry(*match.groups()))
            else:
                item.unreadable_lines.append((number, line))
    item.description = "\n".join(description).strip()
    return item


def find_section(lines: list[str], heading: str) -> tuple[int, int] | None:
    """Where a top-level section is in a body's lines: (heading index, index after its end).

    Headings inside code blocks don't count. The section ends at the next # or ## heading, or at
    the end of the body.
    """
    start = None
    in_code = False
    for index, line in enumerate(lines):
        if CODE_FENCE.match(line):
            in_code = not in_code
            continue
        if in_code or not HEADING.fullmatch(line):
            continue
        if start is not None:
            return start, index
        if line.strip() == heading:
            start = index
    return None if start is None else (start, len(lines))


def _progress(items: list[Item]) -> tuple[int, int]:
    counted = [item for item in items if item.status != "cancelled"]
    return sum(item.status == "done" for item in counted), len(counted)


def _text(value: header.Value | None, default: str = "") -> str:
    if value is None:
        return default
    return ", ".join(value) if isinstance(value, list) else value


def _list(value: header.Value | None) -> list[str]:
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value)
