"""The web app's API, apart from HTTP: the project as one view, and the changes the page makes.

Reading: everything comes from the core library the CLI uses, so the pages show what `corkboard
now`, `next`, `show` and `tree` would: the effective release, open blockers, both sides of each
link, waiting messages, answered items and the order of work. The page only arranges it.

Writing: each change calls the same function in edits.py as its CLI command, so the file ends up
the same either way. Changes from the page are always logged as `me`.

    GET  /api/project                the whole project, as project_view builds it
    GET  /api/items/<ID>             {"id", "mentions", "development"}: docs and items that
                                     mention it, and its branches, pull requests and commits
    GET  /api/pulls                  {"latest", "merged_not_done"}: each item's newest own pull
                                     request, and the items whose one merged while they're open
    GET  /api/docs                   {"docs": [{"name", "title", "changed"}]}: every page
    GET  /api/docs/<name>            {"name", "title", "path", "text", "changed", "mentions"}:
                                     one page, with the IDs of the items it mentions
    GET  /api/search?q=<text>        {"results": [{"kind": "item", "id", "title", "type",
                                     "status", "snippet"} or {"kind": "doc", "name", "title",
                                     "snippet"}]}: the Ctrl-K search, as search.py ranks it

    POST /api/items                  {"type", "title", "fields": {…}, "body"}     corkboard new
    POST /api/items/<ID>/move        {"status", "message"}                       corkboard move
    POST /api/items/<ID>/set         {"fields": {"priority": "high", …}}         corkboard set
    POST /api/items/<ID>/sub         {"action": "add|done|undo", "value"}        corkboard sub
    POST /api/items/<ID>/log         {"text"}                                    corkboard log
    POST /api/items/<ID>/describe    {"description", "base"}    (no command: edits the text)
    POST /api/releases/<name>        {"fields": {"status", "date"}, "goal"}      corkboard release
    POST /api/docs                   {"title", "folder"}        (no command: + New page)
    POST /api/docs/<name>            {"text", "base"}           (no command: edits the page)

Field values are text as typed after field= in the CLI; a list such as labels can also be a JSON
list. The answer is {"line", "warnings"}, plus "id" for a new item and "name" for a new page. A
description or page edit whose "base" no longer matches the file answers 409, with the text on
disk as "current".
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from urllib.parse import unquote

from . import development, docs, edits, search, work
from .development import PullRequest
from .project import TYPES, Item, Project, Release

WHO = "me"


class ApiError(Exception):
    """A request the API can't carry out, with the HTTP status to answer with."""

    def __init__(self, status: int, message: str, extra: dict | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.extra = extra or {}


def project_view(project: Project) -> dict:
    """Releases, items and the order of work, as plain dicts and lists."""
    active = project.active_release()
    return {
        "name": project.name,
        "prefix": project.prefix,
        "root": str(project.root.resolve()),
        "active_release": active.name if active else None,
        "releases": [_release(project, release) for release in project.releases.values()],
        "items": [_item(project, item) for item in project.sorted_items()],
        "next": [item.id for item in work.next_items(project)],
        "problems": [str(problem) for problem in project.problems],
    }


def item_extras(project: Project, item_id: str, prs: list[PullRequest]) -> dict:
    """What the item panel shows beyond the project view: the docs and items that mention it, and
    its development, as `corkboard show` lists it, given the repo's pull requests.

    Kept out of project_view, since finding mentions reads every doc, and development runs git
    and gh."""
    item = _find_item(project, item_id)
    built = development.for_item(project.root, item.id, prs)
    return {
        "id": item.id,
        "mentions": [_mention(project, mention) for mention in project.mentions(item.id)],
        "development": {
            "branches": built.branches,
            "pull_requests": [_pull_request(pr) for pr in built.pull_requests],
            "commits": [
                {"hash": c.hash, "subject": c.subject, "date": c.date} for c in built.commits
            ],
        },
    }


def _mention(project: Project, mention: str) -> dict:
    """An item as {"item": ID}, or a doc as {"doc": name, "title"} for a link to its page."""
    if mention in project.items:
        return {"item": mention}
    name = mention.removeprefix(f"{docs.DOCS_DIR}/").removesuffix(docs.SUFFIX)
    doc = docs.find(project.root, name)
    return {"doc": name, "title": doc.title if doc else name}


def docs_view(project: Project) -> dict:
    """Every page in docs/, for the tree."""
    return {
        "docs": [
            {"name": doc.name, "title": doc.title, "changed": _when(doc.changed)}
            for doc in docs.list_docs(project.root)
        ]
    }


def search_view(project: Project, query: str) -> dict:
    """The Ctrl-K search's results for what was typed."""
    return {"results": search.search(project, query)}


def doc_view(project: Project, name: str) -> dict:
    """One page: its text, the items it mentions, and when it last changed."""
    doc = docs.find(project.root, name)
    if doc is None:
        raise ApiError(404, f"there's no doc {name}")
    return {
        "name": doc.name,
        "title": doc.title,
        "path": project.relative(doc.path),
        "text": doc.text,
        "changed": _when(doc.changed),
        "mentions": docs.mentioned_items(project, doc.text),
    }


def _when(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M")


def pulls_view(project: Project, prs: list[PullRequest]) -> dict:
    """Each item's newest own pull request, for the board's badges, and the open items whose own
    pull request has merged, for Merged, not done. An item's own pull request has its ID in the
    title or branch; one that only names it in the body, as PRs often name their epic, isn't."""
    latest: dict[str, PullRequest] = {}
    for item in project.sorted_items():
        own = next((pr for pr in prs if pr.is_for(item.id)), None)
        if own is not None:
            latest[item.id] = own
    merged = [
        item_id
        for item_id, pr in latest.items()
        if pr.state == "merged" and project.items[item_id].status not in ("done", "cancelled")
    ]
    return {
        "latest": {item_id: _pull_request(pr) for item_id, pr in latest.items()},
        "merged_not_done": merged,
    }


def _pull_request(pr: PullRequest) -> dict:
    return {
        "number": pr.number,
        "title": pr.title,
        "state": pr.state,
        "checks": pr.checks,
        "url": pr.url,
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
        "blocks": [other.id for other in project.blocks(item)],
        "related": item.related,
        "related_to": [other.id for other in project.related_to(item)],
        "duplicate_of": item.duplicate_of,
        "duplicated_by": [other.id for other in project.duplicated_by(item)],
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


def write(project: Project, path: str, data: Mapping, now: datetime) -> dict:
    """Carry out one change from the page. Raises ApiError, or EditError for a refused change."""
    parts = [part for part in path.split("/") if part][1:]  # after "api"
    if parts == ["items"]:
        item_type = _text(data, "type")
        if item_type not in TYPES:
            allowed = ", ".join(TYPES)
            raise ApiError(400, f'"{item_type}" isn\'t an item type. Use one of: {allowed}')
        title, fields, body = _text(data, "title"), _fields(data), _text(data, "body")
        result = edits.new(project, item_type, title, fields, body, WHO, now)
    elif len(parts) == 3 and parts[0] == "items":
        item = _find_item(project, parts[1])
        action = parts[2]
        if action == "move":
            message = _text(data, "message")
            result = edits.move(project, item, _text(data, "status"), message, WHO, now)
        elif action == "set":
            result = edits.set_(project, item, _fields(data), WHO, now)
        elif action == "sub":
            result = edits.sub(project, item, _text(data, "action"), _text(data, "value"), WHO, now)
        elif action == "describe":
            description, base = _text(data, "description"), _text(data, "base")
            try:
                result = edits.describe(project, item, description, base, WHO, now)
            except edits.ConflictError as conflict:
                raise ApiError(409, str(conflict), {"current": conflict.current}) from None
        elif action == "log":
            text = " ".join(_text(data, "text").split())
            if not text:
                raise ApiError(400, "a note needs some text")
            result = edits.log(project, item, text, WHO, now)
        else:
            raise ApiError(404, f"there's no {path}")
    elif len(parts) == 2 and parts[0] == "releases":
        goal = data.get("goal")
        if goal is not None and not isinstance(goal, str):
            raise ApiError(400, "goal must be text")
        result = edits.release(project, parts[1], _fields(data), goal)
    elif parts and parts[0] == "docs":
        return _write_doc(project, parts[1:], data)
    else:
        raise ApiError(404, f"there's no {path}")
    answer: dict = {"line": result.line, "warnings": result.warnings}
    if result.item_id:
        answer["id"] = result.item_id
    return answer


def _write_doc(project: Project, parts: list[str], data: Mapping) -> dict:
    """+ New page (no name), or saving a page's text (its name, still percent-encoded)."""
    if not parts:
        name = docs.new_page(project.root, _text(data, "title"), _text(data, "folder"))
        return {"line": f"created docs/{name}.md", "warnings": [], "name": name}
    name = unquote("/".join(parts))
    doc = docs.find(project.root, name)
    if doc is None:
        raise ApiError(404, f"there's no doc {name}")
    try:
        line = docs.save(doc, _text(data, "text"), _text(data, "base"))
    except edits.ConflictError as conflict:
        raise ApiError(409, str(conflict), {"current": conflict.current}) from None
    return {"line": line, "warnings": []}


def _find_item(project: Project, item_id: str) -> Item:
    item = project.item(item_id)
    if item is None:
        raise ApiError(404, f"there's no item {item_id.upper()}")
    return item


def _text(data: Mapping, key: str) -> str:
    value = data.get(key, "")
    if not isinstance(value, str):
        raise ApiError(400, f"{key} must be text")
    return value


def _fields(data: Mapping) -> dict[str, str | list[str]]:
    """The request's fields: text as the CLI would get it after field=, or a list of text.

    A list goes on as a list, so an item such as the label "a, b" isn't split at its comma.
    """
    fields = data.get("fields", {})
    if not isinstance(fields, dict):
        raise ApiError(400, 'fields must be an object, such as {"priority": "high"}')
    for key, value in fields.items():
        is_list = isinstance(value, list) and all(isinstance(part, str) for part in value)
        if not (is_list or isinstance(value, str)):
            raise ApiError(400, f"{key} must be text or a list of text")
    return fields
