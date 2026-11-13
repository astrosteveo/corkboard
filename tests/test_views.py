import unittest

from helpers import LOG, Fixture

from corkboard import header


def board(test: unittest.TestCase) -> Fixture:
    fixture = Fixture(test)
    release = header.write({"name": "v0.1", "status": "active", "date": "2026-12-01"}, "Goal.\n")
    fixture.raw("releases", "v0.1.md", release)
    fixture.release("v0.2", "planned")
    fixture.item("EX-3", type="epic", title="Board view", status="in-progress", release="v0.1")
    fixture.item("EX-4", type="epic", title="Docs pages", release="v0.1")
    fixture.item("EX-5", type="epic", title="Later", release="v0.2")
    fixture.item("EX-10", title="Board columns", status="done", parent="EX-3")
    fixture.item(
        "EX-12",
        "## Subtasks\n- [x] One\n- [ ] Two\n- [ ] Three\n" + LOG,
        title="Drag cards between columns",
        status="in-progress",
        priority="high",
        parent="EX-3",
        labels=["ui", "board"],
    )
    fixture.item(
        "EX-13", title="Board column limits", priority="high", parent="EX-3", blocked_by=["EX-12"]
    )
    fixture.item(
        "EX-14",
        title="Cards flicker on drop",
        type="bug",
        status="waiting",
        parent="EX-3",
        labels=["ui"],
    )
    fixture.item("EX-15", title="Card colors", status="cancelled", parent="EX-3")
    fixture.item("EX-17", title="Docs page tree", parent="EX-4")
    fixture.item("EX-22", title="Fix typo in README", release="v0.1")
    fixture.item("EX-30", title="Someday", status="backlog", parent="EX-5")
    fixture.item("EX-31", title="Unplanned idea", status="backlog")
    return fixture


class ListTest(unittest.TestCase):
    def setUp(self):
        self.fixture = board(self)

    def run_list(self, *args):
        code, out, err = self.fixture.run("list", *args)
        self.assertEqual((code, err), (0, ""))
        return out

    def ids(self, *args):
        return [line.split()[0] for line in self.run_list(*args).splitlines()[:-1]]

    def test_matches_the_layout_in_the_spec(self):
        self.assertEqual(
            self.run_list("priority=high"),
            "EX-12  task  in-progress  high    Drag cards between columns · epic EX-3 · ui, board\n"
            "EX-13  task  todo         high    Board column limits · epic EX-3 · blocked\n"
            "2 items\n",
        )

    def test_hides_done_and_cancelled_unless_asked(self):
        self.assertNotIn("EX-10", self.ids())
        self.assertNotIn("EX-15", self.ids())
        self.assertIn("EX-10", self.ids("--all"))
        self.assertEqual(self.ids("status=done"), ["EX-10"])
        self.assertEqual(self.ids("status=done,cancelled"), ["EX-10", "EX-15"])

    def test_filters(self):
        self.assertEqual(
            self.ids("status=todo,in-progress", "type=task"), ["EX-12", "EX-13", "EX-17", "EX-22"]
        )
        self.assertEqual(self.ids("labels=ui"), ["EX-12", "EX-14"])
        self.assertEqual(self.ids("release=v0.2"), ["EX-5", "EX-30"])
        self.assertEqual(self.ids("parent=ex-4"), ["EX-17"])
        self.assertEqual(self.ids("blocked_by=EX-12"), ["EX-13"])
        self.assertEqual(self.ids("type=epic", "--all"), ["EX-3", "EX-4", "EX-5"])
        self.assertEqual(self.run_list("owner=me"), "0 items\n")

    def test_errors(self):
        cases = [
            (("colour=red",), "colour isn't a field. Filter on: id, type"),
            (("status=doing",), '"doing" isn\'t a status. Use one of: backlog'),
            (("loose",), "usage: corkboard list"),
        ]
        for args, message in cases:
            with self.subTest(args=args):
                code, _, err = self.fixture.run("list", *args)
                self.assertEqual(code, 1)
                self.assertIn(message, err)


class TreeTest(unittest.TestCase):
    def setUp(self):
        self.fixture = board(self)

    def test_matches_the_layout_in_the_spec(self):
        code, out, err = self.fixture.run("tree")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(
            out,
            "v0.1 · active · due 2026-12-01 · 1/6 done\n"
            "  EX-3 Board view · epic · in-progress · 1/4\n"
            "    done         EX-10 Board columns\n"
            "    in-progress  EX-12 Drag cards between columns · 1/3\n"
            "    waiting      EX-14 Cards flicker on drop\n"
            "    todo         EX-13 Board column limits\n"
            "    cancelled    EX-15 Card colors\n"
            "  EX-4 Docs pages · epic · todo · 0/1\n"
            "    todo         EX-17 Docs page tree\n"
            "  No epic\n"
            "    todo         EX-22 Fix typo in README\n",
        )

    def test_another_release_and_no_release(self):
        self.assertEqual(
            self.fixture.run("tree", "v0.2")[1],
            "v0.2 · planned · 0/1 done\n"
            "  EX-5 Later · epic · todo · 0/1\n"
            "    backlog      EX-30 Someday\n",
        )
        self.assertEqual(
            self.fixture.run("tree", "none")[1],
            "No release · 0/1 done\n  No epic\n    backlog      EX-31 Unplanned idea\n",
        )

    def test_errors(self):
        self.assertEqual(
            self.fixture.run("tree", "v9"),
            (1, "", "error: there's no release v9. Releases: v0.1, v0.2\n"),
        )
        fixture = Fixture(self)
        fixture.release("v0.1", "released")
        fixture.release("v0.2", "planned")
        self.assertEqual(
            fixture.run("tree")[2],
            "error: no active release. Name one: corkboard tree v0.2 "
            "(v0.1 released, v0.2 planned)\n",
        )


if __name__ == "__main__":
    unittest.main()
