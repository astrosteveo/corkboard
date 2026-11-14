"""Search for the web app's Ctrl-K box: items by ID, title and description, and docs by file
name and text.

Every word typed has to appear, in any case. Results come in this order: the item whose ID is
exactly what was typed, items whose ID or title match, docs whose file name matches, items whose
description matches, then docs whose text matches. Within each group, open items come before done
and cancelled ones, newest first, and docs go by name. A match in a description or a doc's text
comes with the line it's on as a snippet.
"""

from __future__ import annotations

from . import docs
from .project import Project

LIMIT = 20
SNIPPET = 90  # characters of a snippet line, at most
CLOSED = ("done", "cancelled")


def search(project: Project, query: str) -> list[dict]:
    """The results for `query`, at most LIMIT, as dicts for the page."""
    words = query.lower().split()
    if not words:
        return []
    exact, titles, names, descriptions, texts = [], [], [], [], []
    open_first = sorted(
        project.items.values(), key=lambda item: (item.status in CLOSED, -item.number)
    )
    for item in open_first:
        result = {
            "kind": "item",
            "id": item.id,
            "title": item.title,
            "type": item.type,
            "status": item.status,
            "snippet": None,
        }
        if item.id.lower() == query.strip().lower():
            exact.append(result)
        elif _has_all(words, f"{item.id} {item.title}"):
            titles.append(result)
        elif _has_all(words, f"{item.id} {item.title}\n{item.description}"):
            descriptions.append({**result, "snippet": _snippet(item.description, words)})
    for doc in docs.list_docs(project.root):
        result = {"kind": "doc", "name": doc.name, "title": doc.title, "snippet": None}
        if _has_all(words, doc.name):
            names.append(result)
        elif _has_all(words, f"{doc.name}\n{doc.text}"):
            texts.append({**result, "snippet": _snippet(doc.text, words)})
    return (exact + titles + names + descriptions + texts)[:LIMIT]


def _has_all(words: list[str], text: str) -> bool:
    text = text.lower()
    return all(word in text for word in words)


def _snippet(text: str, words: list[str]) -> str | None:
    """The first line that has one of the words, cut to SNIPPET characters around it."""
    for line in text.splitlines():
        lower = line.lower()
        found = [lower.find(word) for word in words if word in lower]
        if not found:
            continue
        line = line.strip()
        at = min(found) - (len(lower) - len(lower.lstrip()))
        if len(line) <= SNIPPET:
            return line
        start = max(0, min(at - SNIPPET // 3, len(line) - SNIPPET))
        cut = line[start : start + SNIPPET].strip()
        return ("…" if start else "") + cut + ("…" if start + SNIPPET < len(line) else "")
    return None
