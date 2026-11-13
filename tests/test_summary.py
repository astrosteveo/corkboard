import tempfile
import unittest
from pathlib import Path

from helpers import Fixture, run_cli

from corkboard import header, work

CREATED = "- 2026-11-12 10:00 me: created\n"


def log(*lines: str) -> str:
    return (
        "\n## Log\n"
        + CREATED
        + "".join(f"- 2026-11-12 11:0{n} {line}\n" for n, line in enumerate(lines))
    )


def spec_example(test: unittest.TestCase) -> Fixture:
    """The project behind the `corkboard now` example in cli.md."""
    fixture = Fixture(test)
    release = header.write({"name": "v0.1", "status": "active", "date": "2026-12-01"}, "Goal.\n")
    fixture.raw("releases", "v0.1.md", release)
    fixture.release("v0.2", "planned")
    fixture.item("EX-3", type="epic", title="Board view", release="v0.1")
    subtasks = "## Subtasks\n- [x] One\n- [ ] Two\n- [ ] Three\n"
    fixture.item(
        "EX-12",
        subtasks + log(),
        title="Drag cards between columns",
        status="in-progress",
        priority="high",
        parent="EX-3",
    )
    fixture.item("EX-21", title="Write the README", status="in-progress", owner="me", parent="EX-3")
    fixture.item(
        "EX-14",
        log("claude: moved to waiting: debounce, or rebuild the column?"),
        title="Cards flicker on drop",
        type="bug",
        status="waiting",
        parent="EX-3",
    )
    fixture.item(
        "EX-16",
        log("claude: moved to waiting: hide columns?", "me: moved to todo: yes"),
        title="Column header menu",
        parent="EX-3",
    )
    fixture.item("EX-13", title="Board column limits", priority="high", parent="EX-3")
    fixture.item("EX-19", title="Release view", parent="EX-3")
    fixture.item(
        "EX-18", title="Keyboard shortcuts", priority="high", parent="EX-3", blocked_by=["EX-12"]
    )
    fixture.item("EX-22", title="Pick a name", owner="me", parent="EX-3")
    for number in range(30, 37):
        fixture.item(f"EX-{number}", status="done", parent="EX-3")
    fixture.item("EX-40", status="cancelled", parent="EX-3")
    fixture.item("EX-41", title="Later work", priority="high", release="v0.2")
    return fixture


class OrderTest(unittest.TestCase):
    def test_order_of_work(self):
        project = spec_example(self).load()
        order = [item.id for item in work.next_items(project)]
        # Answered first, then the active release by priority and number, then other releases.
        # Blocked items, the user's items, epics and anything not todo are left out.
        self.assertEqual(order, ["EX-16", "EX-13", "EX-19", "EX-41"])
        self.assertEqual(work.reason(project, project.item("EX-16")), "answered by you")
        self.assertEqual(
            work.reason(project, project.item("EX-13")),
            "in v0.1, the active release, high priority",
        )
        self.assertEqual(work.reason(project, project.item("EX-41")), "high priority")

    def test_answered_means_the_users_reply_to_a_wait_is_the_last_line(self):
        cases = [
            (log("claude: moved to waiting: q", "me: moved to todo: yes"), True),
            (log("claude: moved to waiting: q", "me: moved to todo"), True),
            (log("me: moved to todo: no wait before"), False),
            (log("claude: moved to waiting: q", "claude: moved to todo: answered in chat"), False),
            (log("claude: moved to waiting: q", "me: moved to todo: yes", "claude: a note"), False),
            (
                log("claude: moved to waiting: q", "me: moved to in-progress", "me: moved to todo"),
                False,
            ),
        ]
        for body, expected in cases:
            with self.subTest(body=body):
                fixture = Fixture(self)
                fixture.item("EX-1", body)
                self.assertEqual(work.is_answered(fixture.load().item("EX-1")), expected)


class NowTest(unittest.TestCase):
    def test_matches_the_example_in_the_spec(self):
        code, out, err = spec_example(self).run("now")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(
            out,
            "Example · v0.1 active, due 2026-12-01 · 7/15 done\n"
            "\n"
            "Waiting on you (1)\n"
            '  EX-14 Cards flicker on drop: "debounce, or rebuild the column?"\n'
            "\n"
            "In progress (2)\n"
            "  EX-12 Drag cards between columns · high · 1/3\n"
            "  EX-21 Write the README (you)\n"
            "\n"
            "Next up\n"
            "  EX-16 Column header menu · answered by you\n"
            "  EX-13 Board column limits · high\n"
            "  EX-19 Release view\n"
            "\n"
            "Details: corkboard show <ID>\n",
        )

    def test_never_more_than_25_lines(self):
        fixture = Fixture(self)
        fixture.release("v0.1", "active")
        fixture.raw("items", "EX-999-broken.md", "no header\n")
        for number in range(1, 40):
            status = ("waiting", "in-progress", "todo")[number % 3]
            body = log("claude: moved to waiting: " + "why " * 30) if status == "waiting" else log()
            fixture.item(f"EX-{number}", body, title="T" * 80, status=status, release="v0.1")
        code, out, _ = fixture.run("now")
        lines = out.rstrip("\n").split("\n")
        self.assertEqual(code, 0)
        self.assertLessEqual(len(lines), 25)
        self.assertIn("  …and 8 more: corkboard list status=waiting", lines)
        self.assertIn("  …and 8 more: corkboard list status=in-progress", lines)
        self.assertIn("1 file in .project/ couldn't be read. Run corkboard check.", lines)
        self.assertTrue(all(len(line) <= 140 for line in lines))

    def test_an_empty_project_and_no_active_release(self):
        fixture = Fixture(self)
        self.assertEqual(
            fixture.run("now")[1],
            "Example · no active release\n"
            "Nothing in progress or planned. Add work with corkboard new.\n",
        )

    def test_prints_nothing_outside_a_project(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(run_cli(Path(folder), "now"), (0, "", ""))


class NextTest(unittest.TestCase):
    def test_shows_the_next_item_and_why(self):
        code, out, _ = spec_example(self).run("next")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("next because: answered by you\nEX-16 task · todo · "))
        self.assertIn("\nColumn header menu\n", out)

    def test_nothing_to_do(self):
        fixture = Fixture(self)
        fixture.item("EX-1", owner="me")
        self.assertEqual(
            fixture.run("next"), (0, "nothing to do: no unblocked todo items owned by claude\n", "")
        )


if __name__ == "__main__":
    unittest.main()
