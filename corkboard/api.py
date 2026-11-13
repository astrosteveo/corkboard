"""The web app's read API: the whole project as one JSON-ready view.

Everything here comes from the core library the CLI uses, so the pages show what `corkboard now`,
`next`, `show` and `tree` would: the effective release, open blockers, waiting messages, answered
items and the order of work. The page only arranges it.
"""

from __future__ import annotations

from . import work
from .project import Item, Project, Release


def project_view(project: Project) -> dict:
    """Releases, items and the order of work, as plain dicts and lists."""
    active = project.active_release()
    return {
        "name": project.name,
        "prefix": project.prefix,
        "active_release": active.name if active else None,
        "releases": [_release(project, release) for release in project.releases.values()],
        "items": [_item(project, item) for item in project.sorted_items()],
        "next": [item.id for item in work.next_items(project)],
        "problems": [str(problem) for problem in project.problems],
    }


def _release(project: Project, release: Release) -> dict:
    done, total = project.release_progress(release.name)
    return {
        "name": release.name,
        "status": release.status,
        "date": release.date,
        "goal": release.goal,
        "path": project.relative(release.path),
        "progress": {"done": done, "total": total},
    }


def _item(project: Project, item: Item) -> dict:
    release = project.release_of(item)
    view = {
        "id": item.id,
        "type": item.type,
        "title": item.title,
        "status": item.status,
        "priority": item.priority,
        "owner": item.owner,
        "created": item.created,
        "parent": item.parent,
        "release": release,
        "release_from_epic": release is not None and item.release is None,
        "labels": item.labels,
        "blocked_by": item.blocked_by,
        "open_blockers": project.open_blockers(item),
        "related": item.related,
        "duplicate_of": item.duplicate_of,
        "path": project.relative(item.path),
        "description": item.description,
        "subtasks": [{"text": s.text, "done": s.done} for s in item.subtasks],
        "log": [{"date": e.date, "time": e.time, "who": e.who, "text": e.text} for e in item.log],
        "answered": work.is_answered(item),
        "waiting_message": work.waiting_message(item) if item.status == "waiting" else None,
    }
    if item.is_epic:
        done, total = project.epic_progress(item)
        view["progress"] = {"done": done, "total": total}
    return view
