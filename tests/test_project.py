import tempfile
import unittest
from pathlib import Path

from corkboard import header
from corkboard.project import ITEM_FIELDS, find_root, load, natural_key, parse_id

REPO = Path(__file__).resolve().parents[1]

LOG = "\n## Log\n- 2026-11-12 10:00 me: created\n"


def item_file(item_id: str, body: str = LOG, **fields: str | list[str]) -> str:
    values = {"id": item_id, "type": "task", "title": f"Item {item_id}", "status": "todo"}
    values.update({"priority": "medium", "owner": "claude", "created": "2026-11-12"})
    values.update(fields)
    ordered = {key: values[key] for key in ITEM_FIELDS if key in values}
    return header.write(ordered, body)


class Fixture:
    """A temporary .project/ folder built from file texts."""

    def __init__(self, test: unittest.TestCase) -> None:
        folder = tempfile.TemporaryDirectory()
        test.addCleanup(folder.cleanup)
        self.repo = Path(folder.name)
        self.root = self.repo / ".project"
        (self.root / "items").mkdir(parents=True)
        (self.root / "releases").mkdir()
        (self.root / "config.yml").write_text("name: Example\nprefix: EX\n", encoding="utf-8")

    def item(self, item_id: str, body: str = LOG, **fields: str | list[str]) -> None:
        path = self.root / "items" / f"{item_id}-item.md"
        path.write_text(item_file(item_id, body, **fields), encoding="utf-8")

    def release(self, name: str, status: str, goal: str = "Goal.\n") -> None:
        text = header.write({"name": name, "status": status}, goal)
        (self.root / "releases" / f"{name}.md").write_text(text, encoding="utf-8")

    def raw(self, folder: str, name: str, text: str) -> None:
        (self.root / folder / name).write_text(text, encoding="utf-8")

    def load(self):
        return load(self.root)


class ThisRepoTest(unittest.TestCase):
    """Facts about this repo's own plan that don't change as its items move."""

    def setUp(self):
        self.project = load(REPO / ".project")

    def test_loads_without_problems(self):
        self.assertEqual(self.project.problems, [])
        self.assertEqual((self.project.name, self.project.prefix), ("Corkboard", "CB"))
        self.assertGreaterEqual(len(self.project.items), 22)

    def test_releases(self):
        self.assertEqual(list(self.project.releases)[:3], ["v0.1", "v0.2", "v0.3"])
        self.assertEqual(self.project.active_release().name, "v0.1")

    def test_structure(self):
        project = self.project
        task = project.item("CB-13")
        self.assertEqual(task.parent, "CB-1")
        self.assertEqual(project.epic_of(task).title, "Core library")
        self.assertIsNone(task.release)
        self.assertEqual(project.release_of(task), "v0.1")
        self.assertEqual(project.release_of(project.item("CB-11")), "v0.1")
        children = [i.id for i in project.children(project.item("CB-1"))]
        self.assertEqual(children[:2], ["CB-12", "CB-13"])
        blocked = [i.id for i in project.blocks(project.item("CB-15"))]
        self.assertIn("CB-18", blocked)
        self.assertIn("CB-19", blocked)

    def test_every_item_has_a_log_and_reads_cleanly(self):
        for item in self.project.items.values():
            with self.subTest(item.id):
                self.assertTrue(item.log)
                self.assertEqual(item.unreadable_lines, [])
                self.assertEqual(item.log[0].text, "created")


class BodyTest(unittest.TestCase):
    def test_splits_description_subtasks_and_log(self):
        fixture = Fixture(self)
        fixture.item(
            "EX-1",
            "What and why.\n\nMore detail.\n\n## Subtasks\n- [x] First\n- [X] Second\n"
            "- [ ] Third\n\n## Log\n- 2026-11-12 14:03 me: created\n"
            "- 2026-11-12 14:20 claude: moved to in-progress\n",
        )
        item = fixture.load().item("EX-1")
        self.assertEqual(item.description, "What and why.\n\nMore detail.")
        self.assertTrue(item.has_subtasks_section)
        self.assertEqual(
            [(s.text, s.done) for s in item.subtasks],
            [("First", True), ("Second", True), ("Third", False)],
        )
        self.assertEqual(
            [(e.date, e.time, e.who, e.text) for e in item.log],
            [
                ("2026-11-12", "14:03", "me", "created"),
                ("2026-11-12", "14:20", "claude", "moved to in-progress"),
            ],
        )

    def test_headings_inside_code_blocks_and_other_sections(self):
        fixture = Fixture(self)
        fixture.item(
            "EX-1",
            "Intro.\n\n## Background\nKept in the description.\n\n```markdown\n## Log\n"
            "- not a log line\n```\n\n## Log\n- 2026-11-12 10:00 me: created\n",
        )
        item = fixture.load().item("EX-1")
        self.assertIn("## Background", item.description)
        self.assertIn("- not a log line", item.description)
        self.assertEqual(len(item.log), 1)
        self.assertFalse(item.has_subtasks_section)

    def test_notes_lines_that_break_the_format(self):
        fixture = Fixture(self)
        fixture.item("EX-1", "## Subtasks\n- [ ] Ok\n- [] broken\n\n## Log\nfree text\n")
        item = fixture.load().item("EX-1")
        self.assertEqual([text for _, text in item.unreadable_lines], ["- [] broken", "free text"])


class FieldsTest(unittest.TestCase):
    def test_optional_fields_default_to_empty(self):
        fixture = Fixture(self)
        fixture.item("EX-1")
        item = fixture.load().item("EX-1")
        self.assertIsNone(item.parent)
        self.assertIsNone(item.release)
        self.assertIsNone(item.duplicate_of)
        self.assertEqual((item.labels, item.blocked_by, item.related), ([], [], []))

    def test_missing_required_fields_read_as_the_new_item_defaults(self):
        fixture = Fixture(self)
        fixture.raw("items", "EX-1-bare.md", "---\nid: EX-1\n---\n")
        item = fixture.load().item("EX-1")
        self.assertEqual(
            (item.type, item.status, item.priority, item.owner),
            ("task", "todo", "medium", "claude"),
        )
        self.assertEqual(item.title, "")

    def test_lookup_ignores_case_and_sorting_is_by_number(self):
        fixture = Fixture(self)
        for item_id in ("EX-10", "EX-2", "EX-1"):
            fixture.item(item_id)
        project = fixture.load()
        self.assertEqual(project.item("ex-2").id, "EX-2")
        self.assertEqual([i.id for i in project.sorted_items()], ["EX-1", "EX-2", "EX-10"])


class StructureTest(unittest.TestCase):
    def setUp(self):
        fixture = Fixture(self)
        fixture.release("v0.1", "active")
        fixture.release("v0.2", "planned")
        fixture.item("EX-1", type="epic", release="v0.1")
        fixture.item("EX-2", parent="EX-1", status="done")
        fixture.item("EX-3", parent="EX-1", blocked_by=["EX-2"], related=["EX-4"])
        fixture.item("EX-4", parent="EX-1", blocked_by=["EX-3"], related=["EX-3"])
        fixture.item("EX-5", parent="EX-1", status="cancelled", duplicate_of="EX-4")
        fixture.item("EX-6", type="bug", release="v0.1", status="done", blocked_by=["EX-99"])
        fixture.item("EX-7", release="v0.2")
        fixture.item("EX-8")
        self.project = fixture.load()

    def get(self, item_id):
        return self.project.item(item_id)

    def test_release_of_follows_the_epic(self):
        release_of = self.project.release_of
        self.assertEqual(release_of(self.get("EX-3")), "v0.1")
        self.assertEqual(release_of(self.get("EX-6")), "v0.1")
        self.assertEqual(release_of(self.get("EX-7")), "v0.2")
        self.assertIsNone(release_of(self.get("EX-8")))

    def test_links_show_from_both_sides(self):
        ids = lambda items: [i.id for i in items]  # noqa: E731
        self.assertEqual(ids(self.project.blocks(self.get("EX-3"))), ["EX-4"])
        self.assertEqual(ids(self.project.related_to(self.get("EX-3"))), ["EX-4"])
        self.assertEqual(ids(self.project.related_to(self.get("EX-4"))), ["EX-3"])
        self.assertEqual(ids(self.project.duplicated_by(self.get("EX-4"))), ["EX-5"])

    def test_blocked_until_every_blocker_is_done(self):
        self.assertFalse(self.project.is_blocked(self.get("EX-3")))  # EX-2 is done
        self.assertTrue(self.project.is_blocked(self.get("EX-4")))  # EX-3 is todo
        self.assertEqual(self.project.open_blockers(self.get("EX-6")), ["EX-99"])  # no such item

    def test_progress_leaves_out_cancelled_and_epics(self):
        self.assertEqual(self.project.epic_progress(self.get("EX-1")), (1, 3))
        self.assertEqual(self.project.release_progress("v0.1"), (2, 4))
        self.assertEqual(self.project.release_progress("v0.2"), (0, 1))
        self.assertEqual(self.project.active_release().name, "v0.1")


class ProblemsTest(unittest.TestCase):
    def test_bad_files_are_skipped_and_noted(self):
        fixture = Fixture(self)
        fixture.item("EX-1")
        fixture.raw("items", "EX-2-broken.md", "---\nid: EX-2\ntitle: Fix: it\n---\n")
        fixture.raw("items", "EX-1-again.md", item_file("EX-1"))
        fixture.raw("items", "no-id.md", "---\ntitle: x\n---\n")
        project = fixture.load()
        self.assertEqual(list(project.items), ["EX-1"])
        messages = sorted(str(problem) for problem in project.problems)
        self.assertEqual(len(messages), 3)
        self.assertIn("EX-1-item.md: EX-1 is also used by EX-1-again.md", messages)
        self.assertIn("EX-2-broken.md: line 3: a value containing ': '", messages[1])
        self.assertIn("no-id.md: the header has no id", messages)

    def test_a_missing_config_is_a_problem_not_a_crash(self):
        fixture = Fixture(self)
        (fixture.root / "config.yml").unlink()
        project = fixture.load()
        self.assertEqual(len(project.problems), 1)
        self.assertEqual(project.name, fixture.repo.name)


class FindRootTest(unittest.TestCase):
    def test_walks_up_to_the_first_project_folder(self):
        fixture = Fixture(self)
        nested = fixture.repo / "src" / "deep"
        nested.mkdir(parents=True)
        self.assertEqual(find_root(nested), fixture.root.resolve())

    def test_none_outside_a_project(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertIsNone(find_root(Path(folder)))


class HelpersTest(unittest.TestCase):
    def test_parse_id_and_natural_order(self):
        self.assertEqual(parse_id("EX-12"), ("EX", 12))
        self.assertIsNone(parse_id("ex-12"))
        self.assertEqual(
            sorted(["v0.10", "v0.2", "v0.1"], key=natural_key), ["v0.1", "v0.2", "v0.10"]
        )

    def test_config_round_trips(self):
        text = "name: Example\nprefix: EX\n"
        self.assertEqual(header.write_fields(header.read_fields(text)), text)


if __name__ == "__main__":
    unittest.main()
