import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import LOG, REPO, Fixture, run_cli

BIN = REPO / "bin" / "corkboard"


class CommandsTest(unittest.TestCase):
    def test_help_lists_the_commands(self):
        code, out, _ = run_cli(REPO, "help")
        self.assertEqual(code, 0)
        self.assertIn("show <ID>", out)
        self.assertEqual(run_cli(REPO)[1], out)  # no arguments shows help too

    def test_command_help(self):
        code, out, _ = run_cli(REPO, "show", "--help")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("usage: corkboard show <ID>\n"))
        self.assertEqual(run_cli(REPO, "help", "show")[1], out)

    def test_unknown_command(self):
        code, out, err = run_cli(REPO, "frobnicate")
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(
            err, 'error: "frobnicate" isn\'t a command. Run corkboard help to see them.\n'
        )

    def test_outside_a_project(self):
        with tempfile.TemporaryDirectory() as folder:
            code, _, err = run_cli(Path(folder), "show", "EX-1")
        self.assertEqual(code, 1)
        self.assertEqual(
            err, "error: no .project/ folder here or above. Run corkboard init to start one.\n"
        )

    def test_bad_as_value(self):
        code, _, err = run_cli(REPO, "show", "CB-1", "--as", "someone")
        self.assertEqual((code, err), (1, "error: --as takes me or claude\n"))

    def test_unreadable_files_warn_but_the_command_runs(self):
        fixture = Fixture(self)
        fixture.item("EX-1")
        fixture.raw("items", "EX-2-broken.md", "no header\n")
        code, out, err = fixture.run("show", "EX-1")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("EX-1 task"))
        self.assertEqual(
            err, "warning: 1 file in .project/ couldn't be read. Run corkboard check.\n"
        )


class ShowTest(unittest.TestCase):
    def setUp(self):
        fixture = Fixture(self)
        fixture.release("v0.1", "active")
        fixture.item("EX-3", type="epic", title="Board view", status="in-progress", release="v0.1")
        fixture.item("EX-9", title="Card component")
        fixture.item("EX-13", parent="EX-3", title="Board column limits", related=["EX-12"])
        fixture.item(
            "EX-12",
            "What and why, as written in the file.\n\n## Subtasks\n"
            "- [x] Work out which column a card was dropped on\n"
            "- [ ] Save the status change through corkboard\n"
            "- [ ] Put the card back if saving fails\n\n## Log\n"
            + "".join(f"- 2026-11-12 14:0{n} claude: step {n}\n" for n in range(9)),
            title="Drag cards between columns",
            status="in-progress",
            priority="high",
            parent="EX-3",
            labels=["ui", "board"],
            blocked_by=["EX-9"],
        )
        fixture.item("EX-14", "Flickers right after EX-12 drops a card.\n" + LOG, type="bug")
        fixture.item("EX-18", title="Keyboard shortcuts for the board", blocked_by=["EX-12"])
        fixture.item("EX-20", status="cancelled", duplicate_of="EX-12", title="Dragging")
        fixture.doc("ui.md", "# Web app\n\nThe board (EX-12) and not EX-120.\n")
        fixture.doc("other.md", "Nothing about XEX-12 here.\n")
        self.fixture = fixture

    def test_matches_the_layout_in_the_spec(self):
        code, out, err = self.fixture.run("show", "EX-12")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(
            out,
            "EX-12 task · in-progress · high · claude\n"
            "Drag cards between columns\n"
            "path: .project/items/EX-12-drag-cards-between-columns.md\n"
            "epic: EX-3 Board view · release: v0.1 · labels: ui, board\n"
            "blocked by: EX-9 Card component (todo)\n"
            "blocks: EX-18 Keyboard shortcuts for the board (todo)\n"
            "related: EX-13 Board column limits (todo)\n"
            "duplicated by: EX-20 Dragging (cancelled)\n"
            "mentioned in: docs/ui.md, EX-14\n"
            "\n"
            "What and why, as written in the file.\n"
            "\n"
            "Subtasks 1/3\n"
            "  1 [x] Work out which column a card was dropped on\n"
            "  2 [ ] Save the status change through corkboard\n"
            "  3 [ ] Put the card back if saving fails\n"
            "\n"
            "Log (last 5 of 9)\n"
            "  2026-11-12 14:04 claude: step 4\n"
            "  2026-11-12 14:05 claude: step 5\n"
            "  2026-11-12 14:06 claude: step 6\n"
            "  2026-11-12 14:07 claude: step 7\n"
            "  2026-11-12 14:08 claude: step 8\n",
        )

    def test_an_epic_lists_its_tasks(self):
        _, out, _ = self.fixture.run("show", "ex-3")
        self.assertEqual(
            out,
            "EX-3 epic · in-progress · medium · claude\n"
            "Board view\n"
            "path: .project/items/EX-3-board-view.md\n"
            "release: v0.1\n"
            "\n"
            "Tasks 0/2\n"
            "  in-progress  EX-12 Drag cards between columns\n"
            "  todo         EX-13 Board column limits\n"
            "\n"
            "Log\n"
            "  2026-11-12 10:00 me: created\n",
        )

    def test_lines_with_nothing_to_show_are_left_out(self):
        _, out, _ = self.fixture.run("show", "EX-9")
        self.assertEqual(
            out,
            "EX-9 task · todo · medium · claude\n"
            "Card component\n"
            "path: .project/items/EX-9-card-component.md\n"
            "blocks: EX-12 Drag cards between columns (in-progress)\n"
            "\n"
            "Log\n"
            "  2026-11-12 10:00 me: created\n",
        )

    def test_missing_links_say_so(self):
        self.fixture.item("EX-30", parent="EX-99", blocked_by=["EX-98"])
        _, out, _ = self.fixture.run("show", "EX-30")
        self.assertIn("epic: EX-99 (no such epic)\n", out)
        self.assertIn("blocked by: EX-98 (no such item)\n", out)

    def test_long_titles_of_other_items_are_cut(self):
        self.fixture.item("EX-31", title="A" * 60)
        self.fixture.item("EX-32", blocked_by=["EX-31"])
        _, out, _ = self.fixture.run("show", "EX-32")
        self.assertIn(f"blocked by: EX-31 {'A' * 49}… (todo)\n", out)

    def test_errors(self):
        cases = [
            ((), "error: usage: corkboard show <ID>\n"),
            (("EX-1", "EX-2"), "error: usage: corkboard show <ID>\n"),
            (("twelve",), 'error: "twelve" isn\'t an item ID, such as EX-12\n'),
            (("EX-404",), "error: there's no item EX-404\n"),
        ]
        for args, message in cases:
            with self.subTest(args=args):
                code, out, err = self.fixture.run("show", *args)
                self.assertEqual((code, out, err), (1, "", message))


class BinTest(unittest.TestCase):
    """The real executable, run the way Claude runs it."""

    def run_bin(self, executable: Path, cwd: Path) -> subprocess.CompletedProcess:
        env = {**os.environ, "CLAUDECODE": "1"}
        return subprocess.run(
            [sys.executable, str(executable), "show", "CB-12"],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_runs_from_a_subfolder_of_the_repo(self):
        result = self.run_bin(BIN, REPO / "tests")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("CB-12 task · "))
        self.assertIn("path: .project/items/CB-12-header-format-read-and-write.md\n", result.stdout)

    def test_runs_through_a_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            link = Path(folder) / "corkboard"
            link.symlink_to(BIN)
            result = self.run_bin(link, REPO)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("CB-12 task · "))

    def test_is_executable(self):
        self.assertTrue(os.access(BIN, os.X_OK))


if __name__ == "__main__":
    unittest.main()
