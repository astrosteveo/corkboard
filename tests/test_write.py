import difflib
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from helpers import REPO, Fixture

from corkboard import header, write
from corkboard.project import load, parse_item

WHEN = datetime(2026, 11, 13, 9, 5)


class LogTest(unittest.TestCase):
    def test_log_line(self):
        self.assertEqual(write.log_line(WHEN, "me", "  a\nnote  "), "- 2026-11-13 09:05 me: a note")
        with self.assertRaises(ValueError):
            write.log_line(WHEN, "me", " \n ")

    def test_adds_after_the_last_log_line(self):
        body = "Text.\n\n## Log\n- 2026-11-12 10:00 me: created\n"
        self.assertEqual(
            write.add_log_line(body, "- new"),
            "Text.\n\n## Log\n- 2026-11-12 10:00 me: created\n- new\n",
        )

    def test_keeps_a_section_after_the_log(self):
        body = "## Log\n- one\n\n## Later\nKept.\n"
        self.assertEqual(
            write.add_log_line(body, "- two"), "## Log\n- one\n- two\n\n## Later\nKept.\n"
        )

    def test_starts_the_log_when_there_is_none(self):
        self.assertEqual(write.add_log_line("Text.\n", "- one"), "Text.\n\n## Log\n- one\n")
        self.assertEqual(write.add_log_line("", "- one"), "## Log\n- one\n")

    def test_ignores_a_log_heading_inside_code(self):
        body = "```\n## Log\n```\n"
        self.assertEqual(write.add_log_line(body, "- one"), "```\n## Log\n```\n\n## Log\n- one\n")


class SubtaskTest(unittest.TestCase):
    BODY = "Text.\n\n## Subtasks\n- [ ] One\n- [x] Two\n\n## Log\n- created\n"

    def test_ticks_and_unticks_one_line(self):
        self.assertEqual(write.subtask_count(self.BODY), 2)
        ticked = write.set_subtask(self.BODY, 1, True)
        self.assertEqual(ticked, self.BODY.replace("- [ ] One", "- [x] One"))
        self.assertEqual(
            write.set_subtask(ticked, 2, False), ticked.replace("- [x] Two", "- [ ] Two")
        )

    def test_adds_at_the_end_of_the_section(self):
        self.assertEqual(
            write.add_subtask(self.BODY, "Three"),
            self.BODY.replace("- [x] Two\n", "- [x] Two\n- [ ] Three\n"),
        )

    def test_starts_the_section_above_the_log(self):
        self.assertEqual(
            write.add_subtask("Text.\n\n## Log\n- created\n", "One"),
            "Text.\n\n## Subtasks\n- [ ] One\n\n## Log\n- created\n",
        )
        self.assertEqual(
            write.add_subtask("Text.\n## Log\n- created\n", "One"),
            "Text.\n\n## Subtasks\n- [ ] One\n\n## Log\n- created\n",
        )
        self.assertEqual(write.add_subtask("Text.\n", "One"), "Text.\n\n## Subtasks\n- [ ] One\n")


class FilesTest(unittest.TestCase):
    def test_write_file_swaps_in_the_whole_file_and_keeps_its_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "EX-1-x.md"
            path.write_text("old\n", encoding="utf-8")
            os.chmod(path, 0o640)
            write.write_file(path, "new\n")
            self.assertEqual(path.read_text(encoding="utf-8"), "new\n")
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)
            self.assertEqual(os.listdir(folder), ["EX-1-x.md"])

    def test_slug(self):
        cases = [
            ("Drag cards between columns", "drag-cards-between-columns"),
            ("Fix: crash on drop!", "fix-crash-on-drop"),
            ("Ünïcode café", "unicode-cafe"),
            (
                "Install docs and marketplace listing extra words",
                "install-docs-and-marketplace-listing",
            ),
            ("x" * 50, "x" * 40),
            ("!!!", "item"),
        ]
        for title, expected in cases:
            with self.subTest(title):
                self.assertEqual(write.slug(title), expected)

    def test_next_id_counts_files_that_could_not_be_read(self):
        fixture = Fixture(self)
        fixture.item("EX-1")
        fixture.item("EX-7")
        fixture.raw("items", "EX-30-broken.md", "not a header\n")
        self.assertEqual(write.next_id(fixture.load()), "EX-31")

    def test_next_id_starts_at_one(self):
        self.assertEqual(write.next_id(Fixture(self).load()), "EX-1")


class RealFilesTest(unittest.TestCase):
    """Each change to a real item, written by hand, changes exactly one line and nothing else."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name) / ".project"
        shutil.copytree(REPO / ".project", self.root)
        self.project = load(self.root)

    def assert_one_line_changed(self, old: str, new: str, kind: str) -> None:
        old_lines, new_lines = old.split("\n"), new.split("\n")
        changes = [
            op
            for op in difflib.SequenceMatcher(None, old_lines, new_lines).get_opcodes()
            if op[0] != "equal"
        ]
        self.assertEqual(len(changes), 1, changes)
        tag, i1, i2, j1, j2 = changes[0]
        self.assertEqual((tag, i2 - i1, j2 - j1), (kind, 1 if kind == "replace" else 0, 1))

    def assert_still_clean(self, path: Path, text: str) -> None:
        self.assertEqual(header.canonical(text), text)
        fields, body = header.read(text)
        self.assertEqual(parse_item(path, fields, body).unreadable_lines, [])

    def test_every_item(self):
        for item in self.project.sorted_items():
            with self.subTest(item.id):
                old = item.path.read_text(encoding="utf-8")

                logged = header.write(
                    item.fields, write.add_log_line(item.body, "- 2026-11-13 09:05 me: a note")
                )
                self.assert_one_line_changed(old, logged, "insert")
                self.assert_still_clean(item.path, logged)

                fields = dict(item.fields)
                fields["status"] = "waiting" if item.status != "waiting" else "todo"
                moved = header.write(fields, item.body)
                self.assert_one_line_changed(old, moved, "replace")
                self.assert_still_clean(item.path, moved)

                if item.subtasks:
                    toggled = write.set_subtask(item.body, 1, not item.subtasks[0].done)
                    self.assert_one_line_changed(old, header.write(item.fields, toggled), "replace")
                    self.assert_still_clean(item.path, header.write(item.fields, toggled))


if __name__ == "__main__":
    unittest.main()
