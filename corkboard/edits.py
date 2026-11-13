"""Edits to items and releases: the logic behind `new`, `move`, `sub`, `log`, `set` and `release`.

The CLI's commands and the web server both call these, so a change makes the same file edit
whichever one asks for it. Each function takes the project as loaded, the item (or, for `new` and
`release`, what to create), the change, and who makes it and when. It checks the change, writes
the one file it touches, logs it on the item (releases have no log), and returns the line the CLI
prints along with any warnings. A change that can't be made raises EditError and writes nothing.

The project isn't updated in memory. Load it again to see the change.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from . import header, rules, write
from .project import (
    LOG_HEADING,
    RELEASE_FIELDS,
    RELEASE_STATUSES,
    STATUSES,
    SUBTASKS_HEADING,
    Item,
    Project,
    find_section,
    parse_item,
)

NEW_FIELDS = (
    "status",
    "priority",
    "owner",
    "parent",
    "release",
    "labels",
    "blocked_by",
    "related",
    "duplicate_of",
)
SET_FIELDS = ("title", "type", "priority", "owner") + NEW_FIELDS[3:]
LIST_FIELDS = frozenset({"labels", "blocked_by", "related"})
ID_FIELDS = frozenset({"parent", "blocked_by", "related", "duplicate_of"})
SUBTASK_ACTIONS = ("add", "done", "undo")

_RELEASE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class EditError(Exception):
    """A change that can't be made. The message says why, as the CLI prints it after error:."""


class ConflictError(EditError):
    """The description changed on disk since the edit started. `current` is the one on disk now."""

    def __init__(self, message: str, current: str) -> None:
        super().__init__(message)
        self.current = current


@dataclass
class Result:
    """What an edit did: the line the CLI prints, warnings that didn't stop it, and for `new`, the
    ID it gave the item."""

    line: str
    warnings: list[str] = field(default_factory=list)
    item_id: str | None = None


def new(
    project: Project,
    item_type: str,
    title: str,
    values: Mapping[str, str],
    body: str,
    who: str,
    now: datetime,
) -> Result:
    """Create an item. `values` are header fields as typed after field=, `body` its text."""
    title = " ".join(title.split())
    if not title:
        raise EditError("title can't be empty")
    given = parse_fields(values, NEW_FIELDS)
    if not project.prefix:
        raise EditError("config.yml has no prefix. Add a line such as prefix: EX")
    item_id = write.next_id(project)
    fields: dict[str, header.Value] = {
        "id": item_id,
        "type": item_type,
        "title": title,
        "status": "todo",
        "priority": "medium",
        "owner": "claude",
        "created": f"{now:%Y-%m-%d}",
    }
    for key, value in given.items():
        if value:
            fields[key] = value
    problems = rules.field_problems(project, fields, item_id)
    if problems:
        raise EditError("; ".join(problems))

    if find_section(body.split("\n"), LOG_HEADING) is not None:
        raise EditError("piped text can't have a ## Log section. corkboard writes the log itself")
    body = body.strip("\n") + "\n\n" if body.strip() else ""
    body = write.add_log_line(body, write.log_line(now, who, "created"))

    path = write.item_path(project, item_id, title)
    if path.exists():
        raise EditError(f"{project.relative(path)} already exists")
    write.write_file(path, _text(write.ordered_fields(fields), body))
    return Result(f"created {item_id} {project.relative(path)}", item_id=item_id)


def move(
    project: Project, item: Item, status: str, message: str, who: str, now: datetime
) -> Result:
    """Change an item's status. Moving to waiting needs a message."""
    if status not in STATUSES:
        raise EditError(f'"{status}" isn\'t a status. Use one of: {", ".join(STATUSES)}')
    message = " ".join(message.split())
    if item.status == status:
        return Result(f"{item.id} is already {status}")
    if status == "waiting" and not message:
        raise EditError("moving to waiting needs a message: the question, or what to review")

    warnings = []
    if item.is_epic and status == "done":
        open_tasks = [c.id for c in project.children(item) if c.status not in ("done", "cancelled")]
        if open_tasks:
            warnings.append(f"{item.id} still has open tasks: {', '.join(open_tasks)}")
    if status == "in-progress":
        blockers = project.open_blockers(item)
        if blockers:
            warnings.append(f"{item.id} is blocked by {', '.join(blockers)}")

    fields = dict(item.fields)
    fields["status"] = status
    text = f"moved to {status}: {message}" if message else f"moved to {status}"
    _save(item, fields, text, who, now)
    return Result(f"moved {item.id} to {status} {project.relative(item.path)}", warnings)


def sub(project: Project, item: Item, action: str, value: str, who: str, now: datetime) -> Result:
    """Add a subtask (`value` is its text), or tick or untick one (`value` is its number)."""
    if action not in SUBTASK_ACTIONS:
        raise EditError(f'"{action}" isn\'t a subtask action. Use one of: add, done, undo')
    if item.is_epic:
        raise EditError(f"{item.id} is an epic. Epics have tasks instead of subtasks")

    if action == "add":
        text = " ".join(value.split())
        if not text:
            raise EditError("a subtask needs some text")
        added = write.add_subtask(item.body, text)
        body = _save(item, item.fields, f"added subtask: {text}", who, now, added)
    else:
        count = write.subtask_count(item.body)
        if count == 0:
            raise EditError(
                f'{item.id} has no subtasks yet. Add one with corkboard sub {item.id} add "text"'
            )
        if not value.isdecimal() or not 1 <= int(value) <= count:
            raise EditError(f"{item.id} has {count} subtasks. Pick a number from 1 to {count}")
        number = int(value)
        subtask = item.subtasks[number - 1]
        done = action == "done"
        if subtask.done == done:
            state = "done" if done else "open"
            return Result(f"subtask {number} of {item.id} is already {state}")
        verb = "done subtask" if done else "reopened subtask"
        changed = write.set_subtask(item.body, number, done)
        body = _save(item, item.fields, f"{verb}: {subtask.text}", who, now, changed)

    subtasks = parse_item(item.path, item.fields, body).subtasks
    ticked = sum(subtask.done for subtask in subtasks)
    return Result(f"{item.id} subtasks {ticked}/{len(subtasks)} {project.relative(item.path)}")


def log(project: Project, item: Item, text: str, who: str, now: datetime) -> Result:
    """Add a note to an item's log."""
    _save(item, item.fields, text, who, now)
    return Result(f"logged {item.id} {project.relative(item.path)}")


def describe(
    project: Project, item: Item, description: str, base: str, who: str, now: datetime
) -> Result:
    """Replace an item's description: the text before its ## Subtasks or ## Log section.

    `base` is the description the edit started from. If the file's description isn't that any
    more, nothing is written and ConflictError carries the one on disk. Changes elsewhere in the
    file, such as new log lines, don't count, and are kept.
    """
    if item.description != base.strip():
        raise ConflictError(
            f"the description of {item.id} changed while you were editing it", item.description
        )
    text = description.strip()
    if text == item.description:
        return Result(f"{item.id} already has that description")
    if find_section(text.split("\n"), LOG_HEADING) or find_section(
        text.split("\n"), SUBTASKS_HEADING
    ):
        raise EditError("a description can't have a ## Subtasks or ## Log section of its own")
    lines = item.body.split("\n")
    starts = [
        section[0]
        for heading in (SUBTASKS_HEADING, LOG_HEADING)
        if (section := find_section(lines, heading)) is not None
    ]
    rest = "\n".join(lines[min(starts) :]) if starts else ""
    body = f"{text}\n\n{rest}" if text else rest
    _save(item, item.fields, "edited the description", who, now, body)
    return Result(f"updated the description of {item.id} {project.relative(item.path)}")


def set_(
    project: Project, item: Item, values: Mapping[str, str], who: str, now: datetime
) -> Result:
    """Change header fields other than id, created and status. An empty value clears a field."""
    for key in values:
        if key == "status":
            raise EditError(f"status changes go through corkboard move {item.id} <status>")
        if key in ("id", "created"):
            raise EditError(f"{key} can't be changed")
    given = parse_fields(values, SET_FIELDS)
    if "title" in given:
        given["title"] = " ".join(str(given["title"]).split())
        if not given["title"]:
            raise EditError("title can't be empty")
    if "type" in given and given["type"] != item.type and "epic" in (given["type"], item.type):
        raise EditError("type can only switch between task and bug; an epic stays an epic")

    fields = dict(item.fields)
    changed = []
    for key, value in given.items():
        if value in ("", []):
            if key in fields:
                del fields[key]
                changed.append(f"{key}=")
        elif fields.get(key) != value:
            fields[key] = value
            changed.append(f"{key}={_as_arg(value)}")
    if not changed:
        return Result(f"{item.id} already has those values")
    # Report only the problems this change makes, not ones the item already had.
    before = rules.field_problems(project, item.fields, item.id)
    problems = [p for p in rules.field_problems(project, fields, item.id) if p not in before]
    added = [b for b in fields.get("blocked_by") or [] if b not in item.blocked_by]
    chain = rules.blocking_chain(project, item.id, added)
    if chain:
        problems.append(f"{item.id} would be blocked by itself through {' → '.join(chain)}")
    if problems:
        raise EditError("; ".join(problems))

    path = item.path
    if fields.get("title") != item.title:
        path = write.item_path(project, item.id, str(fields["title"]))
        if path != item.path and path.exists():
            raise EditError(f"{project.relative(path)} already exists")
    _save(item, write.ordered_fields(fields), "set " + " ".join(changed), who, now, path=path)
    return Result(f"updated {item.id} {project.relative(path)}")


def release(project: Project, name: str, values: Mapping[str, str], goal: str | None) -> Result:
    """Create a release, or change its status, date or goal. A goal of None keeps the old one."""
    if not _RELEASE_NAME.fullmatch(name):
        raise EditError(
            f'"{name}" can\'t be a release name. Use letters, digits, dots, dashes and '
            "underscores, such as v0.2"
        )
    given: dict[str, str] = {}
    for key, raw in values.items():
        raw = raw.strip()
        if key not in ("status", "date"):
            raise EditError(f"{key} isn't a release field. Fields: status, date")
        if key == "status" and raw not in RELEASE_STATUSES:
            allowed = ", ".join(RELEASE_STATUSES)
            raise EditError(f'"{raw}" isn\'t a release status. Use one of: {allowed}')
        if key == "date" and raw and not _DATE.fullmatch(raw):
            raise EditError(f'"{raw}" isn\'t a date like 2026-12-01')
        given[key] = raw

    active = project.active_release()
    if given.get("status") == "active" and active is not None and active.name != name:
        raise EditError(
            f"{active.name} is already active. "
            f"Release it first: corkboard release {active.name} status=released"
        )
    goal = goal.strip() + "\n" if goal and goal.strip() else None

    existing = project.releases.get(name)
    if existing is None:
        fields: dict[str, header.Value] = {"name": name, "status": given.get("status", "planned")}
        if given.get("date"):
            fields["date"] = given["date"]
        path = project.root / "releases" / f"{name}.md"
        write.write_file(path, _text(fields, goal or ""))
        return Result(f"created release {name} {project.relative(path)}")

    fields = dict(existing.fields)
    for key, value in given.items():
        if value:
            fields[key] = value
        else:
            fields.pop(key, None)
    known = [key for key in RELEASE_FIELDS if key in fields]
    fields = {key: fields[key] for key in known + [k for k in fields if k not in known]}
    body = existing.body if goal is None else goal
    if fields == existing.fields and body == existing.body:
        return Result(f"nothing to change in {name}: give status=, date= or pipe in a goal")
    write.write_file(existing.path, _text(fields, body))
    return Result(f"updated release {name} {project.relative(existing.path)}")


def parse_fields(values: Mapping[str, str], allowed: tuple[str, ...]) -> dict[str, header.Value]:
    """Field values as typed after field=, as header values. An empty value means clear it."""
    parsed: dict[str, header.Value] = {}
    for key, raw in values.items():
        if key not in allowed:
            raise EditError(f"{key} isn't a field you can set here. Fields: {', '.join(allowed)}")
        if "\n" in raw:
            raise EditError(f"{key} can't contain a line break")
        if key in LIST_FIELDS:
            items = [part.strip() for part in raw.split(",") if part.strip()]
            parsed[key] = [i.upper() for i in items] if key in ID_FIELDS else items
        else:
            value = raw.strip()
            parsed[key] = value.upper() if key in ID_FIELDS else value
    return parsed


def _save(
    item: Item,
    fields: dict[str, header.Value],
    text: str,
    who: str,
    now: datetime,
    body: str | None = None,
    path: Path | None = None,
) -> str:
    """Write the item with these fields, its body (or a changed one) and a new log line.

    With a new `path`, the item moves there: the new file is written first, then the old one is
    removed. Returns the body as written.
    """
    body = item.body if body is None else body
    try:
        line = write.log_line(now, who, text)
    except ValueError as error:
        raise EditError(str(error)) from None
    body = write.add_log_line(body, line)
    path = path or item.path
    write.write_file(path, _text(fields, body))
    if path != item.path:
        item.path.unlink()
    return body


def _as_arg(value: header.Value) -> str:
    """A value the way it's typed after field=, for the log."""
    if isinstance(value, list):
        return ",".join(value)
    return f'"{value}"' if " " in value else value


def _text(fields: dict[str, header.Value], body: str) -> str:
    try:
        return header.write(fields, body)
    except ValueError as error:
        raise EditError(str(error)) from None
