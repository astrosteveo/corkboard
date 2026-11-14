"""Rules for an item's header values, shared by `corkboard new`, `set` and `check`.

Each problem is one sentence that says what to change. File-level checks (duplicate IDs, file
names, log format and so on) belong to `corkboard check`.
"""

from __future__ import annotations

import re
from collections import deque
from collections.abc import Iterable, Mapping

from . import header
from .project import ITEM_FIELDS, OWNERS, PRIORITIES, STATUSES, TYPES, Project

_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

# The fields that hold a list, written [a, b]. Every other field holds one value.
LIST_FIELDS = ("labels", "blocked_by", "related")


def field_problems(
    project: Project, fields: Mapping[str, header.Value], item_id: str | None = None
) -> list[str]:
    """What's wrong with an item's header values, given the rest of the project."""
    problems: list[str] = []
    # A list where one value belongs gets this problem alone, not a second one that reads it as
    # text, such as "todo" isn't a status.
    lists = [
        key
        for key, value in fields.items()
        if isinstance(value, list) and key in ITEM_FIELDS and key not in LIST_FIELDS
    ]
    for key in lists:
        problems.append(f"{key} is one value, not a list: write it without [ ]")
    fields = {key: value for key, value in fields.items() if key not in lists}

    def exact(key: str, linked: str) -> None:
        """A problem for an ID that isn't written exactly: the loader would never follow it."""
        other = project.item(linked)
        if other is None:
            problems.append(f"{key} names {linked}, and there's no such item")
        else:
            problems.append(f"{key} names {linked}: write it as {other.id}")

    def one_of(key: str, noun: str, allowed: tuple[str, ...]) -> None:
        value = fields.get(key)
        if value is not None and value not in allowed:
            problems.append(f'"{_show(value)}" isn\'t {noun}. Use one of: {", ".join(allowed)}')

    one_of("type", "a type", TYPES)
    one_of("status", "a status", STATUSES)
    one_of("priority", "a priority", PRIORITIES)
    one_of("owner", "an owner", OWNERS)

    created = fields.get("created")
    if created is not None and not (isinstance(created, str) and _DATE.fullmatch(created)):
        problems.append(f'created "{_show(created)}" isn\'t a date like 2026-11-12')

    is_epic = fields.get("type") == "epic"
    parent = fields.get("parent")
    if parent:
        if is_epic:
            problems.append("an epic can't have a parent")
        elif project.item(_show(parent)) is None:
            problems.append(f"there's no item {_show(parent)} to be the parent")
        elif _show(parent) not in project.items:
            exact("parent", _show(parent))
        elif not project.items[_show(parent)].is_epic:
            problems.append(f"{_show(parent)} isn't an epic, so it can't be a parent")

    release = fields.get("release")
    if release:
        if _show(release) not in project.releases:
            names = ", ".join(project.releases) or "none yet"
            problems.append(f"there's no release {_show(release)}. Releases: {names}")
        if parent and not is_epic:
            problems.append("a task with an epic gets its release from the epic; leave release out")

    for key in ("blocked_by", "related", "duplicate_of"):
        value = fields.get(key)
        if value is None:
            continue
        ids = [value] if isinstance(value, str) else value
        for linked in ids:
            if item_id and linked.upper() == item_id:
                problems.append(f"{key} can't name the item itself")
            elif linked not in project.items:
                exact(key, linked)
    return problems


def blocking_chain(project: Project, item_id: str, blockers: Iterable[str]) -> list[str] | None:
    """A chain of blocked_by from one of these blockers back to the item, such as
    [EX-2, EX-3, EX-2] for EX-2 blocked by EX-3 while EX-3 is blocked by EX-2. The shortest one,
    or None when there's none."""
    queue = deque([item_id, blocker] for blocker in blockers if blocker != item_id)
    seen: set[str] = set()
    while queue:
        chain = queue.popleft()
        last = chain[-1]
        if last == item_id:
            return chain
        if last in seen:
            continue
        seen.add(last)
        other = project.item(last)
        if other is not None:
            queue.extend([*chain, next_id] for next_id in other.blocked_by)
    return None


def _show(value: header.Value) -> str:
    return ", ".join(value) if isinstance(value, list) else value
