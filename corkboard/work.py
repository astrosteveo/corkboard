"""The order of work: which items Claude should pick up, and in what order.

`corkboard next`, the Next up section of `corkboard now`, and later the web app all use this.
Only tasks and bugs with status todo, owner claude and nothing open in blocked_by count. They're
ordered: answered by the user first, then the active release, then priority, then number.
"""

from __future__ import annotations

import re

from .project import Item, LogEntry, Project

RANK = {"high": 0, "medium": 1, "low": 2}

_MOVED = re.compile(r"moved to ([a-z-]+)(?::|$)")


def moved_to(entry: LogEntry) -> str | None:
    """The status a `moved to <status>` log line moved to, or None for any other line."""
    match = _MOVED.match(entry.text)
    return match.group(1) if match else None


def is_answered(item: Item) -> bool:
    """The item was waiting, and the user's reply moved it to todo: their reply is the last line."""
    if item.status != "todo" or not item.log:
        return False
    last = item.log[-1]
    if last.who != "me" or moved_to(last) != "todo":
        return False
    earlier = [moved_to(entry) for entry in item.log[:-1] if moved_to(entry)]
    return bool(earlier) and earlier[-1] == "waiting"


def waiting_message(item: Item) -> str:
    """What a waiting item is waiting for: the message on its last move to waiting."""
    for entry in reversed(item.log):
        if moved_to(entry) == "waiting":
            return entry.text.partition(": ")[2] if ": " in entry.text else ""
    return ""


def next_items(project: Project) -> list[Item]:
    """Every item Claude could start now, in the order of work."""
    active = project.active_release()
    active_name = active.name if active else None

    def key(item: Item) -> tuple[bool, bool, int, int]:
        in_active = active_name is not None and project.release_of(item) == active_name
        return (not is_answered(item), not in_active, RANK.get(item.priority, 1), item.number)

    candidates = [
        item
        for item in project.items.values()
        if not item.is_epic
        and item.status == "todo"
        and item.owner == "claude"
        and not project.is_blocked(item)
    ]
    return sorted(candidates, key=key)


def reason(project: Project, item: Item) -> str:
    """Why an item is where it is in the order of work, in a few words."""
    if is_answered(item):
        return "answered by you"
    parts = []
    active = project.active_release()
    if active and project.release_of(item) == active.name:
        parts.append(f"in {active.name}, the active release")
    parts.append(f"{item.priority} priority")
    return ", ".join(parts)
