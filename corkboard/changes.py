"""The commands that change items: `new`, `move`, `sub` and `log`, as cli.md describes them.

Each one loads the project, makes one change to one file, logs it with who and when, and prints
one line naming what changed and the file's path.
"""

from __future__ import annotations

import re

from . import header, rules, write
from .cli import CommandError, Context, find_item, usage_error
from .project import LOG_HEADING, STATUSES, TYPES, Item, find_section, parse_item

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
LIST_FIELDS = frozenset({"labels", "blocked_by", "related"})
ID_FIELDS = frozenset({"parent", "blocked_by", "related", "duplicate_of"})

_FIELD_ARG = re.compile(r"([a-z_]+)=(.*)", re.DOTALL)


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
    ctx: Context, item: Item, fields: dict[str, header.Value], text: str, body: str | None = None
) -> str:
    """Write the item with these fields, its body (or a changed one) and a new log line.

    Returns the body as written.
    """
    body = item.body if body is None else body
    try:
        line = write.log_line(ctx.now(), ctx.who, text)
    except ValueError as error:
        raise CommandError(str(error)) from None
    body = write.add_log_line(body, line)
    write.write_file(item.path, _text(fields, body))
    return body


def _text(fields: dict[str, header.Value], body: str) -> str:
    try:
        return header.write(fields, body)
    except ValueError as error:
        raise CommandError(str(error)) from None
