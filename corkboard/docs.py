"""The pages in .project/docs/: listing them, reading one, and the items a page mentions.

A page's name is its path under docs/ without `.md`, such as `ui` or `decisions/0001-markdown`,
which is also its URL in the web app: /docs/ui. Only .md files inside docs/ are ever read. A name
that leads anywhere else, through `..`, an absolute path or a symlink, finds nothing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .project import CODE_FENCE, Project, natural_key

DOCS_DIR = "docs"
SUFFIX = ".md"

# Any item ID on its own, as project.mention_pattern matches one ID.
ANY_ID = re.compile(r"(?<![A-Za-z0-9])[A-Z][A-Z0-9]*-[0-9]+(?![0-9])")
# A level-one heading: "# Title", with optional closing #s.
TITLE = re.compile(r" {0,3}# +(.*?)(?: +#+)? *")


@dataclass(frozen=True)
class Doc:
    name: str  # path under docs/ without .md
    path: Path
    title: str
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


def mentioned_items(project: Project, text: str) -> list[str]:
    """The IDs of the items the text mentions, in number order."""
    found = set(ANY_ID.findall(text))
    return [item.id for item in project.sorted_items() if item.id in found]


def title_of(text: str, fallback: str) -> str:
    """The first level-one heading outside a code block, or else the fallback."""
    in_code = False
    for line in text.splitlines():
        if CODE_FENCE.match(line):
            in_code = not in_code
            continue
        match = None if in_code else TITLE.fullmatch(line)
        if match and match.group(1).strip():
            return match.group(1).strip()
    return fallback


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
    return Doc(name, file, title_of(text, file.stem), text, changed)
