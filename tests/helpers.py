"""Shared test helpers: temporary .project/ folders and running the CLI in one."""

import io
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from corkboard import header, write
from corkboard.cli import main
from corkboard.project import ITEM_FIELDS, load

REPO = Path(__file__).resolve().parents[1]

# Every command run through run_cli sees this as the time.
NOW = datetime(2026, 11, 13, 15, 30)

LOG = "\n## Log\n- 2026-11-12 10:00 me: created\n"


def item_file(item_id: str, body: str = LOG, **fields: str | list[str]) -> str:
    values = {"id": item_id, "type": "task", "title": f"Item {item_id}", "status": "todo"}
    values.update({"priority": "medium", "owner": "claude", "created": "2026-11-12"})
    values.update(fields)
    ordered = {key: values[key] for key in ITEM_FIELDS if key in values}
    return header.write(ordered, body)


class Fixture:
    """A temporary repo with a .project/ folder built from file texts."""

    def __init__(self, test: unittest.TestCase) -> None:
        folder = tempfile.TemporaryDirectory()
        test.addCleanup(folder.cleanup)
        self.repo = Path(folder.name)
        self.root = self.repo / ".project"
        (self.root / "items").mkdir(parents=True)
        (self.root / "releases").mkdir()
        (self.root / "config.yml").write_text("name: Example\nprefix: EX\n", encoding="utf-8")

    def item(self, item_id: str, body: str = LOG, **fields: str | list[str]) -> Path:
        title = str(fields.get("title", f"Item {item_id}"))
        path = self.root / "items" / f"{item_id}-{write.slug(title)}.md"
        path.write_text(item_file(item_id, body, **fields), encoding="utf-8")
        return path

    def release(self, name: str, status: str, goal: str = "Goal.\n") -> None:
        text = header.write({"name": name, "status": status}, goal)
        (self.root / "releases" / f"{name}.md").write_text(text, encoding="utf-8")

    def doc(self, name: str, text: str) -> None:
        path = self.root / "docs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def raw(self, folder: str, name: str, text: str) -> None:
        (self.root / folder / name).write_text(text, encoding="utf-8")

    def load(self):
        return load(self.root)

    def run(
        self, *argv: str, env: dict[str, str] | None = None, stdin: str | None = None
    ) -> tuple[int, str, str]:
        return run_cli(self.repo, *argv, env=env, stdin=stdin)

    def text(self, item_id: str) -> str:
        """The current text of an item's file."""
        (path,) = (self.root / "items").glob(f"{item_id}-*.md")
        return path.read_text(encoding="utf-8")


def run_cli(
    cwd: Path, *argv: str, env: dict[str, str] | None = None, stdin: str | None = None
) -> tuple[int, str, str]:
    """Run corkboard in `cwd`. Returns the exit code, stdout and stderr.

    `stdin` is text piped in; None means nothing is piped.
    """
    out, err = io.StringIO(), io.StringIO()
    code = main(
        list(argv),
        cwd=cwd,
        env=env or {},
        out=out,
        err=err,
        stdin=None if stdin is None else io.StringIO(stdin),
        clock=lambda: NOW,
    )
    return code, out.getvalue(), err.getvalue()
