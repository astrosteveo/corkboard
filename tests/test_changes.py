import os
import socket
import subprocess
import sys
import unittest

from helpers import LOG, REPO, Fixture

CLAUDE = {"CLAUDECODE": "1"}


class StdinTest(unittest.TestCase):
    """The real executable, with stdin as each kind of file it meets."""

    def run_new(self, fixture: Fixture, title: str, **stdin) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(REPO / "bin" / "corkboard"), "new", "task", title],
            cwd=fixture.repo,
            env={**os.environ, "CLAUDECODE": "1"},
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            **stdin,
        )

    def test_a_pipe_becomes_the_body(self):
        fixture = Fixture(self)
        result = self.run_new(fixture, "Piped", input="From a pipe.\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(fixture.load().item("EX-1").description, "From a pipe.")

    def test_dev_null_and_an_open_socket_are_not_read(self):
        # In Claude Code's shell, stdin with nothing piped in is an open socket. Reading it would
        # wait forever, so corkboard must not read it.
        fixture = Fixture(self)
        result = self.run_new(fixture, "Null", stdin=subprocess.DEVNULL)
        self.assertEqual(result.returncode, 0, result.stderr)
        mine, theirs = socket.socketpair()
        self.addCleanup(mine.close)
        self.addCleanup(theirs.close)
        result = self.run_new(fixture, "Socket", stdin=theirs.fileno())
        self.assertEqual(result.returncode, 0, result.stderr)
        project = fixture.load()
        self.assertEqual([project.item(i).description for i in ("EX-1", "EX-2")], ["", ""])


class NewTest(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture(self)
        self.fixture.release("v0.1", "active")
        self.fixture.item("EX-3", type="epic", title="Board view", release="v0.1")
        self.fixture.item("EX-9", title="Card component")

    def test_creates_an_item_with_defaults(self):
        code, out, err = self.fixture.run("new", "task", "Board column limits", env=CLAUDE)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "created EX-10 .project/items/EX-10-board-column-limits.md\n")
        self.assertEqual(
            self.fixture.text("EX-10"),
            "---\nid: EX-10\ntype: task\ntitle: Board column limits\nstatus: todo\n"
            "priority: medium\nowner: claude\ncreated: 2026-11-13\n---\n"
            "## Log\n- 2026-11-13 15:30 claude: created\n",
        )

    def test_fields_and_a_piped_body(self):
        body = (
            "Cap how many cards a column shows before it scrolls.\n\n"
            '## Subtasks\n- [ ] Add a limit per column\n- [ ] Show "+N more" at the bottom\n'
        )
        code, out, _ = self.fixture.run(
            "new",
            "task",
            "Fix: column limits",
            "parent=ex-3",
            "priority=high",
            "labels=ui, board,",
            "blocked_by=EX-9",
            stdin=body,
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, "created EX-10 .project/items/EX-10-fix-column-limits.md\n")
        self.assertEqual(
            self.fixture.text("EX-10"),
            '---\nid: EX-10\ntype: task\ntitle: "Fix: column limits"\nstatus: todo\n'
            "priority: high\nowner: claude\ncreated: 2026-11-13\nparent: EX-3\n"
            "labels: [ui, board]\nblocked_by: [EX-9]\n---\n"
            + body
            + "\n## Log\n- 2026-11-13 15:30 me: created\n",
        )
        item = self.fixture.load().item("EX-10")
        self.assertEqual(
            [s.text for s in item.subtasks],
            ["Add a limit per column", 'Show "+N more" at the bottom'],
        )

    def test_an_unquoted_title_of_several_words(self):
        code, out, _ = self.fixture.run("new", "bug", "Cards", "flicker", "status=backlog")
        self.assertEqual(code, 0)
        self.assertIn("EX-10-cards-flicker.md", out)
        item = self.fixture.load().item("EX-10")
        self.assertEqual((item.title, item.type, item.status), ("Cards flicker", "bug", "backlog"))

    def test_problems_write_nothing(self):
        cases = [
            (("new", "task"), "usage: corkboard new"),
            (("new", "story", "X"), "usage: corkboard new"),
            (("new", "task", "X", "status=doing"), '"doing" isn\'t a status'),
            (("new", "task", "X", "colour=red"), "colour isn't a field you can set"),
            (("new", "task", "X", "parent=EX-9"), "EX-9 isn't an epic"),
            (("new", "task", "X", "parent=EX-40"), "there's no item EX-40"),
            (("new", "epic", "X", "parent=EX-3"), "an epic can't have a parent"),
            (("new", "task", "X", "release=v9"), "there's no release v9. Releases: v0.1"),
            (("new", "task", "X", "parent=EX-3", "release=v0.1"), "leave release out"),
            (("new", "task", "X", "blocked_by=EX-50"), "blocked_by names EX-50"),
        ]
        for args, message in cases:
            with self.subTest(args=args):
                code, out, err = self.fixture.run(*args)
                self.assertEqual((code, out), (1, ""))
                self.assertIn(message, err)
        code, _, err = self.fixture.run("new", "task", "X", stdin="Text.\n\n## Log\n- fake\n")
        self.assertEqual(code, 1)
        self.assertIn("can't have a ## Log section", err)
        self.assertEqual(len(self.fixture.load().items), 2)

    def test_a_log_heading_inside_code_is_fine(self):
        code, _, _ = self.fixture.run("new", "task", "X", stdin="```\n## Log\n```\n")
        self.assertEqual(code, 0)
        self.assertEqual(len(self.fixture.load().item("EX-10").log), 1)


class MoveTest(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture(self)
        self.fixture.item("EX-1", type="epic")
        self.fixture.item("EX-2", parent="EX-1", status="done")
        self.fixture.item("EX-3", parent="EX-1", blocked_by=["EX-9"])
        self.fixture.item("EX-9")

    def test_moves_and_logs(self):
        before = self.fixture.text("EX-9")
        code, out, err = self.fixture.run("move", "ex-9", "in-progress", env=CLAUDE)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "moved EX-9 to in-progress .project/items/EX-9-item.md\n")
        expected = before.replace("status: todo", "status: in-progress")
        expected += "- 2026-11-13 15:30 claude: moved to in-progress\n"
        self.assertEqual(self.fixture.text("EX-9"), expected)

    def test_a_message_is_logged_and_required_for_waiting(self):
        code, _, err = self.fixture.run("move", "EX-9", "waiting")
        self.assertEqual(
            (code, err),
            (1, "error: moving to waiting needs a message: the question, or what to review\n"),
        )
        code, _, _ = self.fixture.run("move", "EX-9", "waiting", "Debounce,", "or rebuild?")
        self.assertEqual(code, 0)
        self.assertEqual(
            self.fixture.load().item("EX-9").log[-1].text, "moved to waiting: Debounce, or rebuild?"
        )

    def test_same_status_changes_nothing(self):
        before = self.fixture.text("EX-9")
        self.assertEqual(self.fixture.run("move", "EX-9", "todo")[1], "EX-9 is already todo\n")
        self.assertEqual(self.fixture.text("EX-9"), before)

    def test_bad_status(self):
        code, _, err = self.fixture.run("move", "EX-9", "inprogress")
        self.assertEqual(code, 1)
        self.assertEqual(
            err,
            'error: "inprogress" isn\'t a status. Use one of: backlog, todo, '
            "in-progress, waiting, done, cancelled\n",
        )

    def test_warnings_dont_stop_the_move(self):
        code, _, err = self.fixture.run("move", "EX-1", "done")
        self.assertEqual((code, err), (0, "warning: EX-1 still has open tasks: EX-3\n"))
        code, _, err = self.fixture.run("move", "EX-3", "in-progress")
        self.assertEqual((code, err), (0, "warning: EX-3 is blocked by EX-9\n"))
        self.assertEqual(self.fixture.load().item("EX-3").status, "in-progress")


class SubTest(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture(self)
        self.fixture.item("EX-1", "Text.\n\n## Subtasks\n- [ ] One\n- [ ] Two\n" + LOG)
        self.fixture.item("EX-2")
        self.fixture.item("EX-5", type="epic")

    def test_done_and_undo(self):
        code, out, _ = self.fixture.run("sub", "EX-1", "done", "2")
        self.assertEqual((code, out), (0, "EX-1 subtasks 1/2 .project/items/EX-1-item.md\n"))
        item = self.fixture.load().item("EX-1")
        self.assertEqual([s.done for s in item.subtasks], [False, True])
        self.assertEqual(item.log[-1].text, "done subtask: Two")
        self.fixture.run("sub", "EX-1", "undo", "2")
        item = self.fixture.load().item("EX-1")
        self.assertEqual([s.done for s in item.subtasks], [False, False])
        self.assertEqual(item.log[-1].text, "reopened subtask: Two")

    def test_add_starts_the_section_above_the_log(self):
        code, out, _ = self.fixture.run("sub", "EX-2", "add", "Write", "tests")
        self.assertEqual((code, out), (0, "EX-2 subtasks 0/1 .project/items/EX-2-item.md\n"))
        text = self.fixture.text("EX-2")
        self.assertIn("\n## Subtasks\n- [ ] Write tests\n\n## Log\n", text)
        self.assertTrue(text.endswith("me: added subtask: Write tests\n"))

    def test_already_done_changes_nothing(self):
        self.fixture.run("sub", "EX-1", "done", "1")
        before = self.fixture.text("EX-1")
        self.assertEqual(
            self.fixture.run("sub", "EX-1", "done", "1")[1], "subtask 1 of EX-1 is already done\n"
        )
        self.assertEqual(self.fixture.text("EX-1"), before)

    def test_errors(self):
        cases = [
            (("sub", "EX-1", "tick", "1"), "usage: corkboard sub"),
            (("sub", "EX-1", "done", "3"), "EX-1 has 2 subtasks. Pick a number from 1 to 2"),
            (("sub", "EX-1", "done", "x"), "Pick a number from 1 to 2"),
            (("sub", "EX-2", "done", "1"), "EX-2 has no subtasks yet"),
            (("sub", "EX-5", "add", "x"), "EX-5 is an epic"),
            (("sub", "EX-1", "add", " "), "usage: corkboard sub"),
        ]
        for args, message in cases:
            with self.subTest(args=args):
                code, _, err = self.fixture.run(*args)
                self.assertEqual(code, 1)
                self.assertIn(message, err)


class LogTest(unittest.TestCase):
    def test_adds_a_note_as_who_ran_it(self):
        fixture = Fixture(self)
        fixture.item("EX-1")
        code, out, _ = fixture.run("log", "EX-1", "Tried", "X;", "too slow.", "--as", "claude")
        self.assertEqual((code, out), (0, "logged EX-1 .project/items/EX-1-item.md\n"))
        entry = fixture.load().item("EX-1").log[-1]
        self.assertEqual(
            (entry.who, entry.text, entry.date, entry.time),
            ("claude", "Tried X; too slow.", "2026-11-13", "15:30"),
        )
        self.assertEqual(fixture.run("log", "EX-1")[0], 1)


if __name__ == "__main__":
    unittest.main()
