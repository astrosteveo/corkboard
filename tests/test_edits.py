"""The shared edit functions, called directly the way the web server will call them."""

import unittest

from helpers import LOG, NOW, Fixture

from corkboard import edits
from corkboard.edits import EditError, Result

SUBTASKS = "\n## Subtasks\n- [ ] Draw the column\n- [x] Add the header\n" + LOG


class EditTest(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture(self)
        self.fixture.release("v0.1", "active")
        self.fixture.item("EX-3", type="epic", title="Board view", release="v0.1")
        self.fixture.item("EX-9", title="Card component", parent="EX-3")
        self.fixture.item("EX-12", body=SUBTASKS, title="Board columns", blocked_by=["EX-9"])

    def item(self, item_id):
        project = self.fixture.load()
        return project, project.item(item_id)

    def last_log(self, item_id):
        return self.fixture.load().item(item_id).log[-1]


class NewTest(EditTest):
    def test_creates_an_item_logged_by_who(self):
        result = edits.new(
            self.fixture.load(), "bug", "Cards  overlap", {"labels": "ui, board"}, "", "me", NOW
        )
        self.assertEqual(result, Result("created EX-13 .project/items/EX-13-cards-overlap.md"))
        item = self.fixture.load().item("EX-13")
        self.assertEqual(
            (item.type, item.title, item.labels), ("bug", "Cards overlap", ["ui", "board"])
        )
        self.assertEqual(self.last_log("EX-13").who, "me")

    def test_the_body_becomes_the_description(self):
        edits.new(self.fixture.load(), "task", "Piped", {}, "\nWhat and why.\n\n", "me", NOW)
        self.assertEqual(self.fixture.load().item("EX-13").description, "What and why.")

    def test_refuses_bad_values_and_writes_nothing(self):
        cases = [
            ("story", "X", {}, "", '"story" isn\'t a type'),
            ("task", " ", {}, "", "title can't be empty"),
            ("task", "X", {"colour": "red"}, "", "colour isn't a field you can set here"),
            ("task", "X", {"parent": "EX-12"}, "", "EX-12 isn't an epic"),
            ("task", "X", {"labels": "a\nb"}, "", "labels can't contain a line break"),
            ("task", "X", {}, "## Log\n- x\n", "can't have a ## Log section"),
        ]
        for item_type, title, values, body, message in cases:
            with self.subTest(message=message):
                with self.assertRaises(EditError) as raised:
                    edits.new(self.fixture.load(), item_type, title, values, body, "me", NOW)
                self.assertIn(message, str(raised.exception))
        self.assertIsNone(self.fixture.load().item("EX-13"))


class MoveTest(EditTest):
    def test_moves_and_logs(self):
        project, item = self.item("EX-9")
        result = edits.move(project, item, "waiting", "Which  colour?", "me", NOW)
        self.assertEqual(
            result, Result("moved EX-9 to waiting .project/items/EX-9-card-component.md")
        )
        self.assertEqual(self.fixture.load().item("EX-9").status, "waiting")
        entry = self.last_log("EX-9")
        self.assertEqual((entry.who, entry.text), ("me", "moved to waiting: Which colour?"))

    def test_warnings_are_returned_not_printed(self):
        project, item = self.item("EX-12")
        result = edits.move(project, item, "in-progress", "", "me", NOW)
        self.assertEqual(result.warnings, ["EX-12 is blocked by EX-9"])
        project, epic = self.item("EX-3")
        result = edits.move(project, epic, "done", "", "me", NOW)
        self.assertEqual(result.warnings, ["EX-3 still has open tasks: EX-9"])
        self.assertEqual(self.fixture.load().item("EX-3").status, "done")

    def test_the_same_status_changes_nothing(self):
        before = self.fixture.text("EX-9")
        project, item = self.item("EX-9")
        self.assertEqual(
            edits.move(project, item, "todo", "", "me", NOW).line, "EX-9 is already todo"
        )
        self.assertEqual(self.fixture.text("EX-9"), before)

    def test_errors(self):
        project, item = self.item("EX-9")
        for status, message, words in (
            ("shipped", "", '"shipped" isn\'t a status'),
            ("waiting", " ", "moving to waiting needs a message"),
        ):
            with self.subTest(status=status), self.assertRaises(EditError) as raised:
                edits.move(project, item, status, message, "me", NOW)
            self.assertIn(words, str(raised.exception))


class SubTest(EditTest):
    def test_add_tick_and_untick(self):
        path = ".project/items/EX-12-board-columns.md"
        steps = [
            ("add", "Test  it", f"EX-12 subtasks 1/3 {path}", "added subtask: Test it"),
            ("done", "1", f"EX-12 subtasks 2/3 {path}", "done subtask: Draw the column"),
            ("undo", "2", f"EX-12 subtasks 1/3 {path}", "reopened subtask: Add the header"),
        ]
        for action, value, line, logged in steps:
            with self.subTest(action=action):
                project, item = self.item("EX-12")
                self.assertEqual(edits.sub(project, item, action, value, "me", NOW).line, line)
                entry = self.last_log("EX-12")
                self.assertEqual((entry.who, entry.text), ("me", logged))

    def test_already_in_that_state(self):
        project, item = self.item("EX-12")
        result = edits.sub(project, item, "done", "2", "me", NOW)
        self.assertEqual(result.line, "subtask 2 of EX-12 is already done")

    def test_errors(self):
        cases = [
            ("EX-12", "tick", "1", '"tick" isn\'t a subtask action'),
            ("EX-12", "done", "3", "EX-12 has 2 subtasks. Pick a number from 1 to 2"),
            ("EX-12", "done", "²", "EX-12 has 2 subtasks"),
            ("EX-12", "add", " ", "a subtask needs some text"),
            ("EX-9", "done", "1", "EX-9 has no subtasks yet"),
            ("EX-3", "add", "X", "EX-3 is an epic"),
        ]
        for item_id, action, value, message in cases:
            with self.subTest(message=message):
                project, item = self.item(item_id)
                with self.assertRaises(EditError) as raised:
                    edits.sub(project, item, action, value, "me", NOW)
                self.assertIn(message, str(raised.exception))


class LogTest(EditTest):
    def test_logs_a_note(self):
        project, item = self.item("EX-9")
        result = edits.log(project, item, "Chose  X\nover Y", "me", NOW)
        self.assertEqual(result, Result("logged EX-9 .project/items/EX-9-card-component.md"))
        entry = self.last_log("EX-9")
        self.assertEqual((entry.who, entry.text), ("me", "Chose X over Y"))

    def test_an_empty_note_is_refused(self):
        project, item = self.item("EX-9")
        with self.assertRaises(EditError):
            edits.log(project, item, " \n", "me", NOW)


class SetTest(EditTest):
    def test_sets_fields_and_renames_the_file(self):
        project, item = self.item("EX-9")
        values = {"title": "Card  face", "priority": "high", "parent": ""}
        result = edits.set_(project, item, values, "me", NOW)
        self.assertEqual(result, Result("updated EX-9 .project/items/EX-9-card-face.md"))
        item = self.fixture.load().item("EX-9")
        self.assertEqual((item.title, item.priority, item.parent), ("Card face", "high", None))
        self.assertFalse((self.fixture.root / "items" / "EX-9-card-component.md").exists())
        entry = self.last_log("EX-9")
        self.assertEqual(
            (entry.who, entry.text), ("me", 'set title="Card face" priority=high parent=')
        )

    def test_the_same_values_change_nothing(self):
        project, item = self.item("EX-9")
        result = edits.set_(project, item, {"priority": "medium"}, "me", NOW)
        self.assertEqual(result.line, "EX-9 already has those values")

    def test_errors(self):
        cases = [
            ({"status": "done"}, "status changes go through corkboard move EX-9"),
            ({"created": "2026-01-01"}, "created can't be changed"),
            ({"title": " "}, "title can't be empty"),
            ({"type": "epic"}, "an epic stays an epic"),
            ({"related": "EX-9"}, "related can't name the item itself"),
        ]
        for values, message in cases:
            with self.subTest(message=message):
                project, item = self.item("EX-9")
                with self.assertRaises(EditError) as raised:
                    edits.set_(project, item, values, "me", NOW)
                self.assertIn(message, str(raised.exception))


class ReleaseTest(EditTest):
    def text(self, name):
        return (self.fixture.root / "releases" / f"{name}.md").read_text(encoding="utf-8")

    def test_creates_and_updates(self):
        values = {"date": "2026-12-01"}
        result = edits.release(self.fixture.load(), "v0.2", values, "The app.\n\n")
        self.assertEqual(result, Result("created release v0.2 .project/releases/v0.2.md"))
        self.assertEqual(
            self.text("v0.2"), "---\nname: v0.2\nstatus: planned\ndate: 2026-12-01\n---\nThe app.\n"
        )
        result = edits.release(self.fixture.load(), "v0.2", {"date": ""}, None)
        self.assertEqual(result.line, "updated release v0.2 .project/releases/v0.2.md")
        self.assertEqual(self.text("v0.2"), "---\nname: v0.2\nstatus: planned\n---\nThe app.\n")
        result = edits.release(self.fixture.load(), "v0.2", {}, "  ")
        self.assertEqual(
            result.line, "nothing to change in v0.2: give status=, date= or pipe in a goal"
        )

    def test_errors(self):
        cases = [
            ("../x", {}, "can't be a release name"),
            ("v0.2", {"status": "shipped"}, '"shipped" isn\'t a release status'),
            ("v0.2", {"date": "soon"}, '"soon" isn\'t a date'),
            ("v0.2", {"owner": "me"}, "owner isn't a release field"),
            ("v0.2", {"status": "active"}, "v0.1 is already active"),
        ]
        for name, values, message in cases:
            with self.subTest(message=message):
                with self.assertRaises(EditError) as raised:
                    edits.release(self.fixture.load(), name, values, None)
                self.assertIn(message, str(raised.exception))
        self.assertFalse((self.fixture.root / "releases" / "v0.2.md").exists())


if __name__ == "__main__":
    unittest.main()
