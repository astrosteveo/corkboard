"""The work behind an item that git knows about: its branch and the commits that mention its ID.

Nothing here is stored in item files; it's read from git each time, so it works offline. Commits
come from HEAD and the local branches. Remote branches are left out, since squash-merged pull
requests leave their branches on the remote and those commits would show up a second time.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .project import mention_pattern

COMMITS = 5
TIMEOUT = 3  # seconds; a git call that takes longer is skipped, not waited on


@dataclass(frozen=True)
class Commit:
    hash: str
    subject: str


def branches(root: Path, item_id: str) -> list[str]:
    """Local branches whose names have the ID, in any case, such as ex-12-drag-cards."""
    pattern = mention_pattern(item_id, ignore_case=True)
    names = _git(root, "branch", "--format=%(refname:short)").splitlines()
    return [name for name in names if pattern.search(name)]


def commits(root: Path, item_id: str, limit: int = COMMITS) -> list[Commit]:
    """The newest commits whose message has the exact ID, so EX-12 doesn't match EX-120."""
    pattern = mention_pattern(item_id)
    out = _git(
        root,
        "log",
        "HEAD",
        "--branches",
        "--no-show-signature",
        "--fixed-strings",
        f"--grep={item_id}",
        "--format=%h%x1f%s%x1f%B%x1e",
    )
    found = []
    for record in out.split("\x1e"):
        parts = record.strip().split("\x1f")
        if len(parts) == 3 and pattern.search(parts[2]):
            found.append(Commit(parts[0], parts[1]))
            if len(found) == limit:
                break
    return found


def _git(root: Path, *args: str) -> str:
    """What git prints, run from `root`, or "" when git is missing, fails or is too slow."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout if result.returncode == 0 else ""
