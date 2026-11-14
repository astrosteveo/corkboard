"""The pages in .project/docs/: listing, reading, saving and adding them, and the items a page
mentions.

A page's name is its path under docs/ without `.md`, such as `ui` or `decisions/0001-markdown`,
which is also its URL in the web app: /docs/ui. Only .md files inside docs/ are ever read or
written. A name that leads anywhere else, through `..`, an absolute path or a symlink, finds
nothing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import write
from .edits import ConflictError, EditError
from .project import Project, natural_key

DOCS_DIR = "docs"
SUFFIX = ".md"
DECISIONS = "decisions"

# A folder name in + New page: no `..`, no hidden folders, nothing a shell would trip on.
FOLDER_PART = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
DECISION_NUMBER = re.compile(r"([0-9]{4})-")

# Any item ID on its own, as project.mention_pattern matches one ID.
ANY_ID = re.compile(r"(?<![A-Za-z0-9])[A-Z][A-Z0-9]*-[0-9]+(?![0-9])")


@dataclass(frozen=True)
class Doc:
    name: str  # path under docs/ without .md
    path: Path
    title: str  # its file name, such as ui.md, so the app names a page the way the repo does
    text: str
    changed: datetime  # the file's modification time


def list_docs(root: Path) -> list[Doc]:
    """Every page in docs/, in name order."""
    folder = root / DOCS_DIR
    if not folder.is_dir():
        return []
    # By name, so a symlink to another page in docs/ doesn't list that page twice.
    docs = {doc.name: doc for path in folder.rglob(f"*{SUFFIX}") if (doc := _read(folder, path))}
    return sorted(docs.values(), key=lambda doc: natural_key(doc.name))


def find(root: Path, name: str) -> Doc | None:
    """The page with this name, with or without .md, or None."""
    name = name.removesuffix(SUFFIX)
    if not name:
        return None
    folder = root / DOCS_DIR
    return _read(folder, folder / f"{name}{SUFFIX}")


def save(doc: Doc, text: str, base: str) -> str:
    """Replace the page's text, and return the line to show for it.

    `base` is the text the edit started from. If the file isn't that any more, nothing is written
    and ConflictError carries the text on disk.
    """
    if doc.text != base:
        raise ConflictError(f"docs/{doc.name}.md changed while you were editing it", doc.text)
    text = text.replace("\r\n", "\n")
    if text.strip() and not text.endswith("\n"):
        text += "\n"
    if text == doc.text:
        return f"docs/{doc.name}.md already has that text"
    write.write_file(doc.path, text)
    return f"saved docs/{doc.name}.md"


def new_page(root: Path, title: str, folder: str) -> str:
    """Create a page with this title as its heading, in a folder under docs/ ("" for docs/
    itself), and return its name. The file name is the title's slug. In decisions/, it starts
    with the next number, as in 0002-short-name.md. A name that's taken is refused."""
    title = " ".join(title.split())
    if not title:
        raise EditError("a page needs a title")
    parts = [part for part in folder.strip().strip("/").split("/") if part]
    for part in parts:
        if not FOLDER_PART.fullmatch(part):
            raise EditError(
                f'"{part}" can\'t be a folder name. Use letters, digits, dots, dashes and _'
            )
    base = (root / DOCS_DIR).resolve()
    place = base.joinpath(*parts)
    stem = write.slug(title)
    if parts == [DECISIONS]:
        stem = f"{_next_decision(place):04d}-{stem}"
    path = place / f"{stem}{SUFFIX}"
    if not path.resolve().is_relative_to(base):
        raise EditError(f"{'/'.join(parts)} leads out of docs/")
    name = path.relative_to(base).as_posix().removesuffix(SUFFIX)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            stream.write(f"# {title}\n")
    except FileExistsError:
        raise EditError(f"docs/{name}.md already exists. Choose another title") from None
    except OSError as error:
        raise EditError(f"couldn't create docs/{name}.md: {error.strerror}") from None
    return name


def _next_decision(folder: Path) -> int:
    """One more than the highest number of a decision record in the folder."""
    numbers = [
        int(match.group(1))
        for path in (folder.glob(f"*{SUFFIX}") if folder.is_dir() else [])
        if (match := DECISION_NUMBER.match(path.name))
    ]
    return max(numbers, default=0) + 1


def mentioned_items(project: Project, text: str) -> list[str]:
    """The IDs of the items the text mentions, in number order."""
    found = set(ANY_ID.findall(text))
    return [item.id for item in project.sorted_items() if item.id in found]


def _read(folder: Path, path: Path) -> Doc | None:
    """The page at path, if it's a .md file inside the folder once symlinks and `..` resolve."""
    try:
        base = folder.resolve()
        file = path.resolve()
        if file.suffix != SUFFIX or not file.is_relative_to(base) or not file.is_file():
            return None
        text = file.read_text(encoding="utf-8", errors="replace")
        changed = datetime.fromtimestamp(file.stat().st_mtime)
    except (OSError, ValueError):  # ValueError: a name with a null byte
        return None
    name = file.relative_to(base).as_posix().removesuffix(SUFFIX)
    return Doc(name, file, file.name, text, changed)
