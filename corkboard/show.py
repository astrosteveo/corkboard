"""`corkboard show <ID>`: one item with its context, in the layout cli.md describes."""

from __future__ import annotations

from . import development
from .cli import Context, cut, find_item, usage_error
from .project import Item, Project

LOG_LINES = 5


def run(ctx: Context, args: list[str]) -> None:
    if len(args) != 1:
        raise usage_error("show")
    project = ctx.project()
    item = find_item(project, args[0])
    ctx.print(render(ctx, project, item))


def render(ctx: Context, project: Project, item: Item) -> str:
    sections = [_summary(ctx, project, item)]
    if item.description:
        sections.append([item.description])
    work = _tasks(project, item) if item.is_epic else _subtasks(item)
    if work:
        sections.append(work)
    built = _development(project, item)
    if built:
        sections.append(built)
    if item.log:
        sections.append(_log(item))
    return "\n\n".join("\n".join(lines) for lines in sections)


def _summary(ctx: Context, project: Project, item: Item) -> list[str]:
    lines = [
        f"{item.id} {item.type} · {item.status} · {item.priority} · {item.owner}",
        item.title,
        f"path: {ctx.relative(item.path)}",
    ]
    context = []
    if item.parent:
        epic = project.epic_of(item)
        context.append(
            f"epic: {_ref(project, item.parent)}" if epic else f"epic: {item.parent} (no such epic)"
        )
    release = project.release_of(item)
    if release:
        context.append(f"release: {release}")
    if item.labels:
        context.append("labels: " + ", ".join(item.labels))
    if context:
        lines.append(" · ".join(context))

    links = [
        ("blocked by", item.blocked_by),
        ("blocks", [other.id for other in project.blocks(item)]),
        ("related", [other.id for other in project.related_to(item)]),
        ("duplicate of", [item.duplicate_of] if item.duplicate_of else []),
        ("duplicated by", [other.id for other in project.duplicated_by(item)]),
    ]
    for label, ids in links:
        if ids:
            lines.append(f"{label}: " + ", ".join(_ref(project, i, with_status=True) for i in ids))

    mentions = project.mentions(item.id)
    if mentions:
        lines.append("mentioned in: " + ", ".join(mentions))
    return lines


def _ref(project: Project, item_id: str, with_status: bool = False) -> str:
    """Another item as `ID Title`, or `ID Title (status)`."""
    other = project.item(item_id)
    if other is None:
        return f"{item_id} (no such item)"
    text = f"{other.id} {cut(other.title)}"
    return f"{text} ({other.status})" if with_status else text


def _subtasks(item: Item) -> list[str]:
    if not item.subtasks:
        return []
    done = sum(subtask.done for subtask in item.subtasks)
    lines = [f"Subtasks {done}/{len(item.subtasks)}"]
    for number, subtask in enumerate(item.subtasks, start=1):
        lines.append(f"  {number} [{'x' if subtask.done else ' '}] {subtask.text}")
    return lines


def _tasks(project: Project, epic: Item) -> list[str]:
    children = project.children(epic)
    if not children:
        return []
    done, total = project.epic_progress(epic)
    lines = [f"Tasks {done}/{total}"]
    lines += [f"  {child.status:<11}  {child.id} {cut(child.title)}" for child in children]
    return lines


def _development(project: Project, item: Item) -> list[str]:
    """The item's branch and its last commits, from git. Left out when there are none."""
    lines = [f"  branch: {name}" for name in development.branches(project.root, item.id)]
    lines += [f"  {c.hash} {c.subject}" for c in development.commits(project.root, item.id)]
    return ["Development", *lines] if lines else []


def _log(item: Item) -> list[str]:
    count = len(item.log)
    heading = f"Log (last {LOG_LINES} of {count})" if count > LOG_LINES else "Log"
    entries = item.log[-LOG_LINES:]
    return [heading] + [f"  {e.date} {e.time} {e.who}: {e.text}" for e in entries]
