"""`corkboard now` and `corkboard next`, as cli.md describes them.

`now` is what the session-start hook puts in front of Claude, so it stays short: every section
has a cap, and the whole summary is at most 25 lines.
"""

from __future__ import annotations

from . import show, work
from .cli import CommandError, Context, cut, usage_error
from .project import Item, Project

MAX_LINES = 25
SECTION_LINES = 5
NEXT_UP = 3
QUESTION_WIDTH = 70


def now(ctx: Context, args: list[str]) -> None:
    if args:
        raise usage_error("now")
    try:
        project = ctx.project(warn=False)
    except CommandError:
        return  # outside a project: print nothing, so the session-start hook is harmless
    ctx.print("\n".join(render_now(project)))


def next_(ctx: Context, args: list[str]) -> None:
    if args:
        raise usage_error("next")
    project = ctx.project()
    items = work.next_items(project)
    if not items:
        ctx.print("nothing to do: no unblocked todo items owned by claude")
        return
    item = items[0]
    ctx.print(f"next because: {work.reason(project, item)}")
    ctx.print(show.render(ctx, project, item))


def render_now(project: Project) -> list[str]:
    lines = [_first_line(project)]
    if project.problems:
        count = len(project.problems)
        files = "file" if count == 1 else "files"
        lines.append(f"{count} {files} in .project/ couldn't be read. Run corkboard check.")

    work_items = [item for item in project.sorted_items() if not item.is_epic]
    waiting = [item for item in project.sorted_items() if item.status == "waiting"]
    in_progress = [item for item in work_items if item.status == "in-progress"]
    next_up = work.next_items(project)[:NEXT_UP]

    sections = []
    if waiting:
        rows = [f"{item.id} {cut(item.title)}{_question(item)}" for item in waiting]
        sections.append(_section(f"Waiting on you ({len(waiting)})", rows, "waiting"))
    if in_progress:
        rows = [_in_progress_row(project, item) for item in in_progress]
        sections.append(_section(f"In progress ({len(in_progress)})", rows, "in-progress"))
    if next_up:
        sections.append(["Next up"] + [f"  {_next_row(item)}" for item in next_up])

    if not sections:
        lines.append("Nothing in progress or planned. Add work with corkboard new.")
        return lines
    for section in sections:
        lines += [""] + section
    lines += ["", "Details: corkboard show <ID>"]
    return lines[:MAX_LINES]


def _first_line(project: Project) -> str:
    release = project.active_release()
    if release is None:
        return f"{project.name} · no active release"
    due = f", due {release.date}" if release.date else ""
    done, total = project.release_progress(release.name)
    return f"{project.name} · {release.name} active{due} · {done}/{total} done"


def _section(heading: str, rows: list[str], status: str) -> list[str]:
    shown = [f"  {row}" for row in rows[:SECTION_LINES]]
    hidden = len(rows) - SECTION_LINES
    if hidden > 0:
        shown.append(f"  …and {hidden} more: corkboard list status={status}")
    return [heading] + shown


def _question(item: Item) -> str:
    question = work.waiting_message(item)
    return f': "{cut(question, QUESTION_WIDTH)}"' if question else ""


def _in_progress_row(project: Project, item: Item) -> str:
    row = f"{item.id} {cut(item.title)}"
    if item.owner == "me":
        row += " (you)"
    if item.priority == "high":
        row += " · high"
    if item.subtasks:
        done = sum(subtask.done for subtask in item.subtasks)
        row += f" · {done}/{len(item.subtasks)}"
    return row


def _next_row(item: Item) -> str:
    row = f"{item.id} {cut(item.title)}"
    if work.is_answered(item):
        return row + " · answered by you"
    if item.priority == "high":
        return row + " · high"
    return row
