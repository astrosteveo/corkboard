import unittest

from helpers import LOG, Fixture

from corkboard.search import LIMIT, search


class SearchTest(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture(self)
        self.fixture.item("EX-1", title="Board view", type="epic")
        self.fixture.item("EX-2", title="Drag cards between columns", status="done")
        self.fixture.item("EX-3", title="Drag handles on cards")
        self.fixture.item(
            "EX-4", "Cards jump when you drag them too fast.\n" + LOG, title="Flicker"
        )
        self.fixture.item("EX-12", title="Keyboard shortcuts")
        self.fixture.doc("drag.md", "# Drag\n")
        self.fixture.doc("ui.md", "# UI\n\nThe board.\n\nYou can Drag a card to another column.\n")

    def found(self, query: str) -> list[str]:
        results = search(self.fixture.load(), query)
        return [result.get("id") or result["name"] for result in results]

    def test_a_doc_by_its_file_name_with_md(self):
        # The app shows a doc as ui.md, so that's what people type.
        self.fixture.doc("cli.md", "See [ui.md](ui.md).\n")
        self.assertEqual(self.found("ui.md"), ["ui", "cli"])

    def test_every_word_has_to_match_in_any_case(self):
        self.assertEqual(self.found("DRAG cards"), ["EX-3", "EX-2", "EX-4"])
        self.assertEqual(self.found("drag nothing"), [])
        self.assertEqual(self.found("   "), [])

    def test_the_order_of_the_groups(self):
        # Titles, open first and then newest, then doc names, descriptions and doc text.
        self.assertEqual(self.found("drag"), ["EX-3", "EX-2", "drag", "EX-4", "ui"])

    def test_an_exact_id_comes_first(self):
        self.assertEqual(self.found("ex-1"), ["EX-1", "EX-12"])
        self.assertEqual(self.found("EX-12"), ["EX-12"])

    def test_what_a_result_holds(self):
        results = search(self.fixture.load(), "drag")
        self.assertEqual(
            results[0],
            {
                "kind": "item",
                "id": "EX-3",
                "title": "Drag handles on cards",
                "type": "task",
                "status": "todo",
                "snippet": None,
            },
        )
        self.assertEqual(
            results[2], {"kind": "doc", "name": "drag", "title": "drag.md", "snippet": None}
        )
        self.assertEqual(results[3]["snippet"], "Cards jump when you drag them too fast.")
        self.assertEqual(results[4]["snippet"], "You can Drag a card to another column.")

    def test_a_long_line_is_cut_around_the_word(self):
        line = "x" * 100 + " the needle " + "y" * 100
        self.fixture.doc("long.md", f"{line}\n")
        snippet = search(self.fixture.load(), "needle")[0]["snippet"]
        self.assertIn("the needle", snippet)
        self.assertTrue(snippet.startswith("…") and snippet.endswith("…"))
        self.assertLessEqual(len(snippet), 92)

    def test_at_most_the_limit(self):
        for number in range(20, 20 + LIMIT + 5):
            self.fixture.item(f"EX-{number}", title=f"Card {number}")
        self.assertEqual(len(self.found("card")), LIMIT)


if __name__ == "__main__":
    unittest.main()
