"""`corkboard list` and `corkboard tree`: many items at once, as cli.md describes them."""

from __future__ import annotations

import re

from .cli import CommandError, Context, cut, usage_error
from .project import OWNERS, PRIORITIES, STATUSES, TYPES, Item, Project

# The order tree shows a release's work in: what's finished first, then what's moving.
TREE_ORDER = ("done", "in-progress", "waiting", "todo", "backlog", "cancelled")
HIDDEN = ("done", "cancelled")

FILTER_FIELDS = (
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
_CHOICES = {"type": TYPES, "status": STATUSES, "priority": PRIORITIES, "owner": OWNERS}
_FILTER = re.compile(r"([a-z_]+)=(.*)", re.DOTALL)


def list_(ctx: Context, args: list[str]) -> None:
    show_all = "--all" in args
    # Every filter must match, a field filtered twice too, so they're kept as a list.
    filters: list[tuple[str, list[str]]] = []
    for arg in (a for a in args if a != "--all"):
        match = _FILTER.fullmatch(arg)
        if match is None:
            raise usage_error("list")
        key, raw = match.groups()
        if key not in FILTER_FIELDS:
            raise CommandError(f"{key} isn't a field. Filter on: {', '.join(FILTER_FIELDS)}")
        values = [part.strip() for part in raw.split(",") if part.strip()]
        for value in values:
            if key in _CHOICES and value not in _CHOICES[key]:
                allowed = ", ".join(_CHOICES[key])
                raise CommandError(f'"{value}" isn\'t a {key}. Use one of: {allowed}')
        filters.append((key, values))

    project = ctx.project()
    items = [item for item in project.sorted_items() if _matches(project, item, filters)]
    if not show_all and all(key != "status" for key, _ in filters):
        items = [item for item in items if item.status not in HIDDEN]
    width = max((len(item.id) for item in items), default=0)
    for item in items:
        ctx.print(_list_row(project, item, width))
    ctx.print(f"{len(items)} item" + ("" if len(items) == 1 else "s"))


def tree(ctx: Context, args: list[str]) -> None:
    if len(args) > 1:
        raise usage_error("tree")
    project = ctx.project()
    if args and args[0] == "none":
        name = None
    elif args:
        if args[0] not in project.releases:
            raise CommandError(f"there's no release {args[0]}. {_releases(project)}")
        name = args[0]
    else:
        active = project.active_release()
        if active is None:
            if not project.releases:
                raise CommandError("there are no releases yet. Start one with corkboard release")
            example = list(project.releases)[-1]
            listing = ", ".join(f"{r.name} {r.status}" for r in project.releases.values())
            raise CommandError(f"no active release. Name one: corkboard tree {example} ({listing})")
        name = active.name
    ctx.print("\n".join(render_tree(project, name)))


def render_tree(project: Project, name: str | None) -> list[str]:
    """The tree for a release, or for the items with no release when `name` is None."""
    if name is None:
        work = [
            i for i in project.items.values() if not i.is_epic and project.release_of(i) is None
        ]
        done, total = _done(work)
        lines = [f"No release · {done}/{total} done"]
    else:
        release = project.releases[name]
        due = f" · due {release.date}" if release.date else ""
        done, total = project.release_progress(name)
        lines = [f"{name} · {release.status}{due} · {done}/{total} done"]

    epics = [i for i in project.sorted_items() if i.is_epic and i.release == name]
    loose = [
        i
        for i in project.sorted_items()
        if not i.is_epic and project.epic_of(i) is None and project.release_of(i) == name
    ]
    for epic in epics:
        done, total = project.epic_progress(epic)
        lines.append(f"  {epic.id} {cut(epic.title)} · epic · {epic.status} · {done}/{total}")
        lines += [_tree_row(i) for i in _tree_sorted(project.children(epic))]
    if loose:
        lines.append("  No epic")
        lines += [_tree_row(i) for i in _tree_sorted(loose)]
    if not epics and not loose:
        lines.append("  Nothing here yet.")
    return lines


def _matches(project: Project, item: Item, filters: list[tuple[str, list[str]]]) -> bool:
    for key, wanted in filters:
        if key == "release":
            have = [project.release_of(item) or ""]
        elif key in ("labels", "blocked_by", "related"):
            have = getattr(item, key)
        else:
            have = [getattr(item, key) or ""]
        if key in ("id", "parent", "blocked_by", "related", "duplicate_of"):
            wanted = [value.upper() for value in wanted]
        if not set(have) & set(wanted):
            return False
    return True


def _list_row(project: Project, item: Item, width: int) -> str:
    columns = f"{item.id:<{width}}  {item.type:<4}  {item.status:<11}  {item.priority:<6}"
    row = f"{columns}  {cut(item.title)}"
    if item.parent:
        row += f" · epic {item.parent}"
    if item.labels:
        row += " · " + ", ".join(item.labels)
    if project.is_blocked(item):
        row += " · blocked"
    return row


def _tree_row(item: Item) -> str:
    row = f"    {item.status:<11}  {item.id} {cut(item.title)}"
    if item.subtasks:
        done = sum(subtask.done for subtask in item.subtasks)
        row += f" · {done}/{len(item.subtasks)}"
    return row


def _tree_sorted(items: list[Item]) -> list[Item]:
    def key(item: Item) -> tuple[int, int]:
        rank = TREE_ORDER.index(item.status) if item.status in TREE_ORDER else len(TREE_ORDER)
        return rank, item.number

    return sorted(items, key=key)


def _done(items: list[Item]) -> tuple[int, int]:
    counted = [item for item in items if item.status != "cancelled"]
    return sum(item.status == "done" for item in counted), len(counted)


def _releases(project: Project) -> str:
    if not project.releases:
        return "There are no releases yet."
    return "Releases: " + ", ".join(project.releases)
