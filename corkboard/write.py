"""Change .project/ files: whole-file writes, new IDs and file names, log lines and subtasks.

Each change edits an item's text in place. A log line goes at the end of ## Log, a subtask's box
is ticked on its own line, and a status changes in the header. Everything else in the file stays
exactly as it was.
"""

from __future__ import annotations

import contextlib
import os
import re
import tempfile
import unicodedata
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from . import header
from .project import (
    ITEM_FIELDS,
    LOG_HEADING,
    SUBTASK_LINE,
    SUBTASKS_HEADING,
    Project,
    find_section,
    parse_id,
)

SLUG_WIDTH = 40


def write_file(path: Path, text: str) -> None:
    """Write a temporary file beside `path`, then swap it in, so no reader ever sees half a file.

    The temporary file's name doesn't end in .md, so the loader never picks it up.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o666 & ~_umask()
    descriptor, temp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
        os.chmod(temp, mode)
        os.replace(temp, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp)
        raise


def log_line(when: datetime, who: str, text: str) -> str:
    """A log line. Line breaks and runs of spaces in `text` become single spaces."""
    text = " ".join(text.split())
    if not text:
        raise ValueError("a log line needs some text")
    return f"- {when:%Y-%m-%d %H:%M} {who}: {text}"


def add_log_line(body: str, line: str) -> str:
    """The body with `line` added at the end of ## Log, starting the section if there's none."""
    lines = body.split("\n")
    bounds = find_section(lines, LOG_HEADING)
    if bounds is None:
        before = body.rstrip("\n")
        return (before + "\n\n" if before else "") + f"{LOG_HEADING}\n{line}\n"
    at = _last_content(lines, *bounds) + 1
    return "\n".join(lines[:at] + [line] + lines[at:])


def has_log_section(body: str) -> bool:
    return find_section(body.split("\n"), LOG_HEADING) is not None


def subtask_count(body: str) -> int:
    return len(_subtask_indexes(body.split("\n")))


def set_subtask(body: str, number: int, done: bool) -> str:
    """The body with subtask `number` (counting from 1) ticked or unticked."""
    lines = body.split("\n")
    index = _subtask_indexes(lines)[number - 1]
    lines[index] = ("- [x]" if done else "- [ ]") + lines[index][5:]
    return "\n".join(lines)


def add_subtask(body: str, text: str) -> str:
    """The body with a new open subtask at the end of ## Subtasks.

    With no ## Subtasks section, one is started just above ## Log, or at the end of the body.
    """
    text = " ".join(text.split())
    if not text:
        raise ValueError("a subtask needs some text")
    new = f"- [ ] {text}"
    lines = body.split("\n")
    bounds = find_section(lines, SUBTASKS_HEADING)
    if bounds is not None:
        at = _last_content(lines, *bounds) + 1
        return "\n".join(lines[:at] + [new] + lines[at:])
    log = find_section(lines, LOG_HEADING)
    if log is None:
        before = body.rstrip("\n")
        return (before + "\n\n" if before else "") + f"{SUBTASKS_HEADING}\n{new}\n"
    at = log[0]
    section = [SUBTASKS_HEADING, new, ""]
    if at > 0 and lines[at - 1].strip():
        section.insert(0, "")
    return "\n".join(lines[:at] + section + lines[at:])


def ordered_fields(fields: Mapping[str, header.Value]) -> dict[str, header.Value]:
    """Fields in the order corkboard writes them. Keys it doesn't know keep their order, last."""
    known = [key for key in ITEM_FIELDS if key in fields]
    unknown = [key for key in fields if key not in ITEM_FIELDS]
    return {key: fields[key] for key in known + unknown}


def next_id(project: Project) -> str:
    """The next free ID: one more than the highest number in items/, read or not."""
    prefix = project.prefix
    pattern = re.compile(rf"{re.escape(prefix)}-([0-9]+)(?![0-9])")
    numbers = [item.number for item in project.items.values() if item.id.startswith(f"{prefix}-")]
    folder = project.root / "items"
    if folder.is_dir():
        for path in folder.glob("*.md"):
            match = pattern.match(path.name)
            if match:
                numbers.append(int(match.group(1)))
    return f"{prefix}-{max(numbers, default=0) + 1}"


def slug(title: str) -> str:
    """The short title for a file name: lowercase words joined by dashes, cut at a word boundary."""
    plain = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    words = re.findall(r"[a-z0-9]+", plain.lower())
    if not words:
        return "item"
    text = words[0][:SLUG_WIDTH]
    for word in words[1:]:
        if len(text) + 1 + len(word) > SLUG_WIDTH:
            break
        text += "-" + word
    return text


def item_path(project: Project, item_id: str, title: str) -> Path:
    """The file for an item. The ID must be one, such as EX-12, so the path stays in items/."""
    if parse_id(item_id) is None:
        raise ValueError(f"{item_id!r} isn't an item ID")
    return project.root / "items" / f"{item_id}-{slug(title)}.md"


def _subtask_indexes(lines: list[str]) -> list[int]:
    bounds = find_section(lines, SUBTASKS_HEADING)
    if bounds is None:
        return []
    start, end = bounds
    return [i for i in range(start + 1, end) if SUBTASK_LINE.fullmatch(lines[i].rstrip())]


def _last_content(lines: list[str], start: int, end: int) -> int:
    """The last line in [start, end) that isn't blank. The heading at `start` counts."""
    for index in range(end - 1, start, -1):
        if lines[index].strip():
            return index
    return start


def _umask() -> int:
    current = os.umask(0)
    os.umask(current)
    return current
