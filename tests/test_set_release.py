import unittest

from helpers import Fixture


class SetTest(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture(self)
        self.fixture.release("v0.1", "active")
        self.fixture.item("EX-3", type="epic", release="v0.1")
        self.fixture.item("EX-9")
        self.fixture.item("EX-12", title="Drag cards", parent="EX-3")

    def test_changes_fields_and_logs_them(self):
        before = self.fixture.text("EX-12")
        code, out, err = self.fixture.run("set", "EX-12", "priority=high", "labels=ui,board")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "updated EX-12 .project/items/EX-12-drag-cards.md\n")
        expected = before.replace("priority: medium", "priority: high")
        expected = expected.replace("parent: EX-3\n", "parent: EX-3\nlabels: [ui, board]\n")
        expected += "- 2026-11-13 15:30 me: set priority=high labels=ui,board\n"
        self.assertEqual(self.fixture.text("EX-12"), expected)

    def test_a_new_title_renames_the_file(self):
        code, out, _ = self.fixture.run("set", "EX-12", "title=Drag cards between columns")
        self.assertEqual(code, 0)
        self.assertEqual(out, "updated EX-12 .project/items/EX-12-drag-cards-between-columns.md\n")
        self.assertFalse((self.fixture.root / "items" / "EX-12-drag-cards.md").exists())
        item = self.fixture.load().item("EX-12")
        self.assertEqual(item.title, "Drag cards between columns")
        self.assertEqual(item.log[-1].text, 'set title="Drag cards between columns"')

    def test_an_empty_value_clears_and_links_are_uppercased(self):
        self.fixture.run("set", "EX-12", "parent=", "related=ex-9", "release=v0.1")
        item = self.fixture.load().item("EX-12")
        self.assertEqual((item.parent, item.related, item.release), (None, ["EX-9"], "v0.1"))
        self.assertEqual(item.log[-1].text, "set parent= related=EX-9 release=v0.1")

    def test_type_switches_only_between_task_and_bug(self):
        self.assertEqual(self.fixture.run("set", "EX-9", "type=bug")[0], 0)
        self.assertEqual(self.fixture.load().item("EX-9").type, "bug")
        code, _, err = self.fixture.run("set", "EX-9", "type=epic")
        self.assertEqual(code, 1)
        self.assertIn("type can only switch between task and bug", err)

    def test_existing_problems_dont_block_unrelated_changes(self):
        self.fixture.item("EX-20", blocked_by=["EX-98"])
        self.assertEqual(self.fixture.run("set", "EX-20", "priority=low")[0], 0)
        code, _, err = self.fixture.run("set", "EX-20", "related=EX-97")
        self.assertEqual(code, 1)
        self.assertEqual(err, "error: related names EX-97, and there's no such item\n")

    def test_nothing_to_change(self):
        before = self.fixture.text("EX-12")
        self.assertEqual(
            self.fixture.run("set", "EX-12", "priority=medium")[1],
            "EX-12 already has those values\n",
        )
        self.assertEqual(self.fixture.text("EX-12"), before)

    def test_errors(self):
        cases = [
            (("set", "EX-12"), "usage: corkboard set"),
            (("set", "EX-12", "status=done"), "status changes go through corkboard move EX-12"),
            (("set", "EX-12", "id=EX-1"), "id can't be changed"),
            (("set", "EX-12", "title="), "title can't be empty"),
            (("set", "EX-12", "parent=EX-9"), "EX-9 isn't an epic"),
            (("set", "EX-12", "release=v0.1"), "leave release out"),
            (("set", "EX-12", "colour=red"), "colour isn't a field you can set"),
        ]
        for args, message in cases:
            with self.subTest(args=args):
                code, _, err = self.fixture.run(*args)
                self.assertEqual(code, 1)
                self.assertIn(message, err)


class ReleaseTest(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture(self)

    def text(self, name):
        return (self.fixture.root / "releases" / f"{name}.md").read_text(encoding="utf-8")

    def test_creates_a_planned_release_with_a_goal(self):
        code, out, _ = self.fixture.run(
            "release", "v0.2", "date=2026-12-01", stdin="The plugin.\n\n"
        )
        self.assertEqual((code, out), (0, "created release v0.2 .project/releases/v0.2.md\n"))
        self.assertEqual(
            self.text("v0.2"),
            "---\nname: v0.2\nstatus: planned\ndate: 2026-12-01\n---\nThe plugin.\n",
        )

    def test_updates_and_clears(self):
        self.fixture.run("release", "v0.1", "status=active", "date=2026-12-01")
        code, out, _ = self.fixture.run("release", "v0.1", "status=released", "date=")
        self.assertEqual((code, out), (0, "updated release v0.1 .project/releases/v0.1.md\n"))
        self.assertEqual(self.text("v0.1"), "---\nname: v0.1\nstatus: released\n---\n")
        self.fixture.run("release", "v0.1", stdin="Shipped.\n")
        self.assertTrue(self.text("v0.1").endswith("---\nShipped.\n"))
        self.assertEqual(
            self.fixture.run("release", "v0.1")[1],
            "nothing to change in v0.1: give status=, date= or pipe in a goal\n",
        )

    def test_only_one_active_release(self):
        self.fixture.run("release", "v0.1", "status=active")
        code, _, err = self.fixture.run("release", "v0.2", "status=active")
        self.assertEqual(code, 1)
        self.assertEqual(
            err,
            "error: v0.1 is already active. Release it first: corkboard release v0.1 "
            "status=released\n",
        )
        self.assertFalse((self.fixture.root / "releases" / "v0.2.md").exists())
        self.assertEqual(self.fixture.run("release", "v0.1", "status=active")[0], 0)

    def test_never_overwrites_a_file_that_isnt_that_release(self):
        cases = {
            "unreadable": "---\nname: v0.2\nstatus: planned\ndate: 2026-12-01 # moved\n---\nGoal.\n",
            "another name": "---\nname: beta\nstatus: planned\n---\nThe beta's goal.\n",
        }
        for case, text in cases.items():
            with self.subTest(case=case):
                self.fixture.raw("releases", "v0.2.md", text)
                code, _, err = self.fixture.run("release", "v0.2", "status=active")
                self.assertEqual(code, 1)
                self.assertIn("error: .project/releases/v0.2.md already exists", err)
                self.assertEqual(self.text("v0.2"), text)

    def test_errors(self):
        cases = [
            (("release",), "usage: corkboard release"),
            (("release", "../x"), "can't be a release name"),
            (("release", "v1", "status=shipped"), '"shipped" isn\'t a release status'),
            (("release", "v1", "date=soon"), '"soon" isn\'t a date'),
            (("release", "v1", "owner=me"), "owner isn't a release field"),
        ]
        for args, message in cases:
            with self.subTest(args=args):
                code, _, err = self.fixture.run(*args)
                self.assertEqual(code, 1)
                self.assertIn(message, err)


if __name__ == "__main__":
    unittest.main()
