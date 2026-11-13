"""The commands that change things: `new`, `move`, `sub`, `log`, `set` and `release`.

Each one loads the project, makes one change to one file, logs it with who and when (items have
logs; releases don't), and prints one line naming what changed and the file's path.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import header, rules, write
from .cli import CommandError, Context, find_item, usage_error
from .project import (
    LOG_HEADING,
    RELEASE_FIELDS,
    RELEASE_STATUSES,
    STATUSES,
    TYPES,
    Item,
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

_FIELD_ARG = re.compile(r"([a-z_]+)=(.*)", re.DOTALL)
_RELEASE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def new(ctx: Context, args: list[str]) -> None:
    if len(args) < 2 or args[0] not in TYPES:
        raise usage_error("new")
    item_type = args[0]
    title_words = [arg for arg in args[1:] if not _FIELD_ARG.fullmatch(arg)]
    title = " ".join(" ".join(title_words).split())
    if not title:
        raise usage_error("new")
    values = parse_fields([arg for arg in args[1:] if _FIELD_ARG.fullmatch(arg)], NEW_FIELDS)

    project = ctx.project()
    if not project.prefix:
        raise CommandError("config.yml has no prefix. Add a line such as prefix: EX")
    item_id = write.next_id(project)
    now = ctx.now()
    fields: dict[str, header.Value] = {
        "id": item_id,
        "type": item_type,
        "title": title,
        "status": "todo",
        "priority": "medium",
        "owner": "claude",
        "created": f"{now:%Y-%m-%d}",
    }
    for key, value in values.items():
        if value:
            fields[key] = value
    problems = rules.field_problems(project, fields, item_id)
    if problems:
        raise CommandError("; ".join(problems))

    piped = ctx.piped_input() or ""
    if find_section(piped.split("\n"), LOG_HEADING) is not None:
        raise CommandError(
            "piped text can't have a ## Log section. corkboard writes the log itself"
        )
    body = piped.strip("\n") + "\n\n" if piped.strip() else ""
    body = write.add_log_line(body, write.log_line(now, ctx.who, "created"))

    path = write.item_path(project, item_id, title)
    if path.exists():
        raise CommandError(f"{ctx.relative(path)} already exists")
    write.write_file(path, _text(write.ordered_fields(fields), body))
    ctx.print(f"created {item_id} {ctx.relative(path)}")


def move(ctx: Context, args: list[str]) -> None:
    if len(args) < 2:
        raise usage_error("move")
    project = ctx.project()
    item = find_item(project, args[0])
    status = args[1]
    if status not in STATUSES:
        raise CommandError(f'"{status}" isn\'t a status. Use one of: {", ".join(STATUSES)}')
    message = " ".join(" ".join(args[2:]).split())
    if item.status == status:
        ctx.print(f"{item.id} is already {status}")
        return
    if status == "waiting" and not message:
        raise CommandError("moving to waiting needs a message: the question, or what to review")

    if item.is_epic and status == "done":
        open_tasks = [c.id for c in project.children(item) if c.status not in ("done", "cancelled")]
        if open_tasks:
            ctx.warn(f"{item.id} still has open tasks: {', '.join(open_tasks)}")
    if status == "in-progress":
        blockers = project.open_blockers(item)
        if blockers:
            ctx.warn(f"{item.id} is blocked by {', '.join(blockers)}")

    fields = dict(item.fields)
    fields["status"] = status
    text = f"moved to {status}: {message}" if message else f"moved to {status}"
    _save(ctx, item, fields, text)
    ctx.print(f"moved {item.id} to {status} {ctx.relative(item.path)}")


def sub(ctx: Context, args: list[str]) -> None:
    if len(args) < 3 or args[1] not in ("add", "done", "undo"):
        raise usage_error("sub")
    project = ctx.project()
    item = find_item(project, args[0])
    if item.is_epic:
        raise CommandError(f"{item.id} is an epic. Epics have tasks instead of subtasks")
    action = args[1]

    if action == "add":
        text = " ".join(" ".join(args[2:]).split())
        if not text:
            raise usage_error("sub")
        body = _save(
            ctx, item, item.fields, f"added subtask: {text}", write.add_subtask(item.body, text)
        )
    else:
        count = write.subtask_count(item.body)
        if count == 0:
            raise CommandError(
                f'{item.id} has no subtasks yet. Add one with corkboard sub {item.id} add "text"'
            )
        if len(args) != 3 or not args[2].isdigit() or not 1 <= int(args[2]) <= count:
            raise CommandError(f"{item.id} has {count} subtasks. Pick a number from 1 to {count}")
        number = int(args[2])
        subtask = item.subtasks[number - 1]
        done = action == "done"
        if subtask.done == done:
            state = "done" if done else "open"
            ctx.print(f"subtask {number} of {item.id} is already {state}")
            return
        verb = "done subtask" if done else "reopened subtask"
        changed = write.set_subtask(item.body, number, done)
        body = _save(ctx, item, item.fields, f"{verb}: {subtask.text}", changed)

    subtasks = parse_item(item.path, item.fields, body).subtasks
    ticked = sum(subtask.done for subtask in subtasks)
    ctx.print(f"{item.id} subtasks {ticked}/{len(subtasks)} {ctx.relative(item.path)}")


def log(ctx: Context, args: list[str]) -> None:
    if len(args) < 2:
        raise usage_error("log")
    project = ctx.project()
    item = find_item(project, args[0])
    text = " ".join(" ".join(args[1:]).split())
    if not text:
        raise usage_error("log")
    _save(ctx, item, item.fields, text)
    ctx.print(f"logged {item.id} {ctx.relative(item.path)}")


def set_(ctx: Context, args: list[str]) -> None:
    if len(args) < 2:
        raise usage_error("set")
    project = ctx.project()
    item = find_item(project, args[0])
    for arg in args[1:]:
        key = arg.partition("=")[0]
        if key == "status":
            raise CommandError(f"status changes go through corkboard move {item.id} <status>")
        if key in ("id", "created"):
            raise CommandError(f"{key} can't be changed")
    values = parse_fields(args[1:], SET_FIELDS)
    if "title" in values:
        values["title"] = " ".join(str(values["title"]).split())
        if not values["title"]:
            raise CommandError("title can't be empty")
    if "type" in values and values["type"] != item.type and "epic" in (values["type"], item.type):
        raise CommandError("type can only switch between task and bug; an epic stays an epic")

    fields = dict(item.fields)
    changed = []
    for key, value in values.items():
        if value in ("", []):
            if key in fields:
                del fields[key]
                changed.append(f"{key}=")
        elif fields.get(key) != value:
            fields[key] = value
            changed.append(f"{key}={_as_arg(value)}")
    if not changed:
        ctx.print(f"{item.id} already has those values")
        return
    # Report only the problems this change makes, not ones the item already had.
    before = rules.field_problems(project, item.fields, item.id)
    problems = [p for p in rules.field_problems(project, fields, item.id) if p not in before]
    if problems:
        raise CommandError("; ".join(problems))

    path = item.path
    if fields.get("title") != item.title:
        path = write.item_path(project, item.id, str(fields["title"]))
        if path != item.path and path.exists():
            raise CommandError(f"{ctx.relative(path)} already exists")
    _save(ctx, item, write.ordered_fields(fields), "set " + " ".join(changed), path=path)
    ctx.print(f"updated {item.id} {ctx.relative(path)}")


def release(ctx: Context, args: list[str]) -> None:
    if not args:
        raise usage_error("release")
    name = args[0]
    if not _RELEASE_NAME.fullmatch(name):
        raise CommandError(
            f'"{name}" can\'t be a release name. Use letters, digits, dots, dashes and '
            "underscores, such as v0.2"
        )
    values: dict[str, str] = {}
    for arg in args[1:]:
        match = _FIELD_ARG.fullmatch(arg)
        if match is None:
            raise usage_error("release")
        key, raw = match.group(1), match.group(2).strip()
        if key not in ("status", "date"):
            raise CommandError(f"{key} isn't a release field. Fields: status, date")
        if key == "status" and raw not in RELEASE_STATUSES:
            allowed = ", ".join(RELEASE_STATUSES)
            raise CommandError(f'"{raw}" isn\'t a release status. Use one of: {allowed}')
        if key == "date" and raw and not _DATE.fullmatch(raw):
            raise CommandError(f'"{raw}" isn\'t a date like 2026-12-01')
        values[key] = raw

    project = ctx.project()
    active = project.active_release()
    if values.get("status") == "active" and active is not None and active.name != name:
        raise CommandError(
            f"{active.name} is already active. "
            f"Release it first: corkboard release {active.name} status=released"
        )
    piped = ctx.piped_input()
    goal = piped.strip() + "\n" if piped and piped.strip() else None

    existing = project.releases.get(name)
    if existing is None:
        fields: dict[str, header.Value] = {"name": name, "status": values.get("status", "planned")}
        if values.get("date"):
            fields["date"] = values["date"]
        path = project.root / "releases" / f"{name}.md"
        path.parent.mkdir(exist_ok=True)
        write.write_file(path, _text(fields, goal or ""))
        ctx.print(f"created release {name} {ctx.relative(path)}")
        return

    fields = dict(existing.fields)
    for key, value in values.items():
        if value:
            fields[key] = value
        else:
            fields.pop(key, None)
    known = [key for key in RELEASE_FIELDS if key in fields]
    fields = {key: fields[key] for key in known + [k for k in fields if k not in known]}
    body = existing.body if goal is None else goal
    if fields == existing.fields and body == existing.body:
        ctx.print(f"nothing to change in {name}: give status=, date= or pipe in a goal")
        return
    write.write_file(existing.path, _text(fields, body))
    ctx.print(f"updated release {name} {ctx.relative(existing.path)}")


def parse_fields(args: list[str], allowed: tuple[str, ...]) -> dict[str, header.Value]:
    """`field=value` arguments as header values. An empty value means clear the field."""
    values: dict[str, header.Value] = {}
    for arg in args:
        match = _FIELD_ARG.fullmatch(arg)
        if match is None:
            raise CommandError(f'"{arg}" isn\'t field=value')
        key, raw = match.groups()
        if key not in allowed:
            raise CommandError(
                f"{key} isn't a field you can set here. Fields: {', '.join(allowed)}"
            )
        if "\n" in raw:
            raise CommandError(f"{key} can't contain a line break")
        if key in LIST_FIELDS:
            items = [part.strip() for part in raw.split(",") if part.strip()]
            values[key] = [i.upper() for i in items] if key in ID_FIELDS else items
        else:
            value = raw.strip()
            values[key] = value.upper() if key in ID_FIELDS else value
    return values


def _save(
    ctx: Context,
    item: Item,
    fields: dict[str, header.Value],
    text: str,
    body: str | None = None,
    path: Path | None = None,
) -> str:
    """Write the item with these fields, its body (or a changed one) and a new log line.

    With a new `path`, the item moves there: the new file is written first, then the old one is
    removed. Returns the body as written.
    """
    body = item.body if body is None else body
    try:
        line = write.log_line(ctx.now(), ctx.who, text)
    except ValueError as error:
        raise CommandError(str(error)) from None
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
        raise CommandError(str(error)) from None
