import tempfile
import unittest
from pathlib import Path

from helpers import LOG, Fixture, item_file, run_cli

from corkboard.check import suggest_name, suggest_prefix


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture(self)
        self.fixture.release("v0.1", "active")
        self.fixture.item("EX-1", type="epic", title="Board", release="v0.1")

    def problems(self):
        code, out, err = self.fixture.run("check")
        self.assertEqual(err, "")
        lines = out.rstrip("\n").split("\n")
        return code, lines[:-1], lines[-1]

    def assert_problem(self, line):
        code, problems, summary = self.problems()
        self.assertEqual(code, 1)
        self.assertIn(line, problems)
        self.assertTrue(summary.endswith("problem" if len(problems) == 1 else "problems"))

    def test_a_clean_project(self):
        self.fixture.raw("items", "EX-2-item-ex-2.md", item_file("EX-2", parent="EX-1"))
        self.assertEqual(self.problems(), (0, [], "2 items, 1 release: ok"))

    def test_each_rule(self):
        cases = [
            ("EX-2-x.md", "---\nid: EX-2\ntitle: Fix: it\n---\n", "line 3: a value containing"),
            (
                "EX-3-item-ex-3.md",
                "---\nid: EX-3\n---\n" + LOG,
                "missing type, title, status, priority, owner, created",
            ),
            ("EX-4-item-ex-4.md", item_file("EX-4", status="doing"), '"doing" isn\'t a status'),
            ("EX-5-item-ex-5.md", item_file("EX-5", parent="EX-9"), "there's no item EX-9"),
            (
                "EX-6-item-ex-6.md",
                item_file("EX-6", parent="EX-1", release="v0.1"),
                "leave release out",
            ),
            ("EX-7-item-ex-7.md", item_file("EX-7", release="v9"), "there's no release v9"),
            (
                "EX-8-item-ex-8.md",
                item_file("EX-8", blocked_by=["EX-8"]),
                "blocked_by can't name the item itself",
            ),
            (
                "EX-9-item-ex-9.md",
                item_file("EX-9", related=["EX-99"]),
                "related names EX-99, and there's no such item",
            ),
            (
                "EX-10-item-ex-10.md",
                item_file("EX-10", "## Subtasks\n- [ ] x\n" + LOG, type="epic"),
                "an epic has tasks, not a ## Subtasks section",
            ),
            (
                "EX-11-item-ex-11.md",
                item_file("EX-11", "## Log\n- yesterday: did stuff\n"),
                "isn't a subtask or log line",
            ),
            ("EX-12-old-name.md", item_file("EX-12"), "the file name doesn't match the title"),
            ("twelve.md", item_file("EX-13"), "the file name doesn't start with EX-13"),
            (
                "EX-14-item-ex-14.md",
                item_file("EX-14").replace("type: task", 'type: "task"'),
                "the header isn't written the way corkboard writes it",
            ),
            (
                "EX-15-item-ex-15.md",
                item_file("EX-15").replace(
                    "created: 2026-11-12\n", "created: 2026-11-12\ncolour: red\n"
                ),
                "colour isn't a field corkboard knows",
            ),
            (
                "ZZ-16-item-zz-16.md",
                item_file("ZZ-16"),
                "ZZ-16 isn't an ID with this project's prefix, such as EX-12",
            ),
        ]
        for name, text, message in cases:
            with self.subTest(name):
                fixture = Fixture(self)
                fixture.release("v0.1", "active")
                fixture.item("EX-1", type="epic", title="Board", release="v0.1")
                fixture.raw("items", name, text)
                self.fixture = fixture
                code, problems, _ = self.problems()
                self.assertEqual(code, 1)
                self.assertTrue(any(name + ": " in p and message in p for p in problems), problems)

    def test_the_exact_lines_from_the_spec(self):
        self.fixture.raw("items", "EX-12-item-ex-12.md", item_file("EX-12", parent="EX-99"))
        self.fixture.raw("items", "EX-7-old-name.md", item_file("EX-7"))
        code, problems, summary = self.problems()
        self.assertEqual(code, 1)
        self.assertEqual(
            problems,
            [
                "EX-7-old-name.md: the file name doesn't match the title",
                "EX-12-item-ex-12.md: there's no item EX-99 to be the parent",
            ],
        )
        self.assertEqual(summary, "3 items, 1 release: 2 problems")

    def test_a_control_character_in_a_header_is_reported(self):
        text = item_file("EX-2").replace("title: Item EX-2", "title: Fix\tcrash")
        self.fixture.raw("items", "EX-2-fix-crash.md", text)
        code, out, err = self.fixture.run("check")
        self.assertEqual((code, err), (1, ""))
        self.assertIn("EX-2-fix-crash.md: line 4: a value can't contain a tab", out)

    def test_duplicates_and_loops(self):
        self.fixture.raw("items", "EX-2-item-ex-2.md", item_file("EX-2", blocked_by=["EX-3"]))
        self.fixture.raw("items", "EX-3-item-ex-3.md", item_file("EX-3", blocked_by=["EX-2"]))
        later = item_file("EX-2", created="2026-11-20").replace("Item EX-2", "Other")
        self.fixture.raw("items", "EX-2-other.md", later)
        _, problems, _ = self.problems()
        self.assertIn("EX-2-other.md: EX-2 is also used by EX-2-item-ex-2.md", problems)
        self.assertIn("EX-2-item-ex-2.md: blocked by itself through EX-2 → EX-3 → EX-2", problems)

    def test_config_and_releases(self):
        (self.fixture.root / "config.yml").write_text("name: Example\n", encoding="utf-8")
        self.fixture.raw("releases", "v0.2.md", "---\nname: v2\nstatus: shipped\ndate: soon\n---\n")
        _, problems, _ = self.problems()
        self.assertIn("config.yml: there's no prefix, such as prefix: EX", problems)
        self.assertIn('v0.2.md: name is "v2", but the file is named v0.2.md', problems)
        self.assertIn(
            'v0.2.md: "shipped" isn\'t a release status. Use one of: planned, active, released',
            problems,
        )
        self.assertIn('v0.2.md: date "soon" isn\'t a date like 2026-12-01', problems)


class FixTest(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture(self)
        self.fixture.item("EX-1", type="epic", title="Board")

    def test_renames_and_rewrites_headers(self):
        self.fixture.raw("items", "EX-7-old-name.md", item_file("EX-7"))
        text = item_file("EX-8").replace("type: task", 'type: "task"')
        self.fixture.raw("items", "EX-8-item-ex-8.md", text)
        code, out, _ = self.fixture.run("check", "--fix")
        self.assertEqual(code, 0)
        self.assertEqual(
            out,
            "fixed: renamed EX-7-old-name.md to EX-7-item-ex-7.md\n"
            "fixed: rewrote the header of EX-8-item-ex-8.md in corkboard's format\n"
            "3 items, 0 releases: ok\n",
        )
        self.assertIn("type: task\n", self.fixture.text("EX-8"))

    def test_renumbers_the_later_duplicate_and_lists_references(self):
        self.fixture.raw("items", "EX-12-item-ex-12.md", item_file("EX-12"))
        later = item_file("EX-12", created="2026-11-20", title="Ctrl-K search")
        self.fixture.raw("items", "EX-12-ctrl-k-search.md", later)
        self.fixture.raw("items", "EX-14-item-ex-14.md", item_file("EX-14", blocked_by=["EX-12"]))
        self.fixture.doc("ui.md", "Search is EX-12.\n")
        code, out, _ = self.fixture.run("check", "--fix")
        self.assertEqual(code, 0, out)
        self.assertEqual(
            out.split("\n")[:2],
            [
                'fixed: EX-12 was used twice. "Ctrl-K search" is now EX-15.',
                "check these references to EX-12, which may have meant EX-15: "
                "EX-14 blocked_by, docs/ui.md",
            ],
        )
        project = self.fixture.load()
        self.assertEqual(project.item("EX-15").title, "Ctrl-K search")
        self.assertEqual(
            project.item("EX-15").log[-1].text,
            "renumbered from EX-12, which another item also used",
        )
        self.assertTrue(project.item("EX-15").path.name.startswith("EX-15-"))
        self.assertEqual(project.item("EX-12").title, "Item EX-12")

    def test_never_moves_an_item_out_of_items(self):
        # An ID that isn't one can't name a file: ../../EX-6 would write outside items/.
        text = item_file("EX-6", title="x").replace("id: EX-6\n", "id: ../../EX-6\n")
        self.fixture.raw("items", "EX-6-x.md", text)
        code, out, _ = self.fixture.run("check", "--fix")
        self.assertEqual(code, 1, out)
        self.assertFalse((self.fixture.repo / "EX-6-x.md").exists(), out)
        self.assertTrue((self.fixture.root / "items" / "EX-6-x.md").exists(), out)
        self.assertNotIn("fixed:", out)

    def test_doesnt_renumber_without_a_valid_prefix(self):
        for config in ("name: Example\n", "name: Example\nprefix: ../x\n"):
            with self.subTest(config=config):
                fixture = Fixture(self)
                (fixture.root / "config.yml").write_text(config, encoding="utf-8")
                fixture.raw("items", "EX-1-item-ex-1.md", item_file("EX-1"))
                fixture.raw(
                    "items", "EX-1-other.md", item_file("EX-1", created="2026-11-20", title="Other")
                )
                code, out, _ = fixture.run("check", "--fix")
                self.assertEqual(code, 1, out)
                self.assertNotIn("fixed:", out)
                names = sorted(path.name for path in fixture.root.rglob("*.md"))
                self.assertEqual(names, ["EX-1-item-ex-1.md", "EX-1-other.md"])

    def test_lists_what_it_cant_fix(self):
        self.fixture.raw("items", "EX-5-item-ex-5.md", item_file("EX-5", parent="EX-9"))
        code, out, _ = self.fixture.run("check", "--fix")
        self.assertEqual(code, 1)
        self.assertEqual(
            out,
            "EX-5-item-ex-5.md: there's no item EX-9 to be the parent\n"
            "2 items, 0 releases: 1 problem\n",
        )


class InitTest(unittest.TestCase):
    def folder(self, name: str) -> Path:
        parent = tempfile.TemporaryDirectory()
        self.addCleanup(parent.cleanup)
        path = Path(parent.name) / name
        path.mkdir()
        return path

    def test_suggestions(self):
        self.assertEqual(suggest_prefix("claude-project"), "CP")
        self.assertEqual(suggest_prefix("astro"), "AST")
        self.assertEqual(suggest_prefix("my_cool.app2"), "MCA")
        self.assertEqual(suggest_prefix("2024"), "EX")
        self.assertEqual(suggest_name("claude-project"), "Claude Project")
        self.assertEqual(suggest_name("corkboard"), "Corkboard")

    def test_sets_up_a_folder_that_new_then_works_in(self):
        folder = self.folder("claude-project")
        code, out, _ = run_cli(folder, "init")
        self.assertEqual(
            (code, out),
            (0, 'created .project/config.yml (prefix CP)\nnext: corkboard new epic "First epic"\n'),
        )
        config = (folder / ".project" / "config.yml").read_text(encoding="utf-8")
        self.assertEqual(config, "name: Claude Project\nprefix: CP\n")
        self.assertEqual(
            run_cli(folder, "new", "epic", "First epic")[1],
            "created CP-1 .project/items/CP-1-first-epic.md\n",
        )
        self.assertEqual(run_cli(folder, "check")[1], "1 item, 0 releases: ok\n")

    def test_options_and_errors(self):
        folder = self.folder("whatever")
        self.assertEqual(run_cli(folder, "init", "prefix=gm", "name=Game")[0], 0)
        config = (folder / ".project" / "config.yml").read_text(encoding="utf-8")
        self.assertEqual(config, "name: Game\nprefix: GM\n")
        self.assertEqual(
            run_cli(folder, "init"), (1, "", "error: already set up: .project/config.yml\n")
        )
        self.assertEqual(
            run_cli(folder / ".project", "init")[2], "error: already set up: config.yml\n"
        )
        other = self.folder("other")
        self.assertIn("can't be a prefix", run_cli(other, "init", "prefix=1x")[2])
        self.assertIn("usage: corkboard init", run_cli(other, "init", "colour=red")[2])


if __name__ == "__main__":
    unittest.main()
