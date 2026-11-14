import re
import unittest
from pathlib import Path

from corkboard.header import HeaderError, canonical, format_value, read, write

REPO = Path(__file__).resolve().parents[1]


def header_file(*lines: str, body: str = "Body.\n") -> str:
    return "\n".join(["---", *lines, "---"]) + "\n" + body


class ReadTest(unittest.TestCase):
    def test_reads_fields_in_order_and_the_body(self):
        fields, body = read(
            header_file(
                "id: EX-12",
                'title: "Fix: crash on drop"',
                "labels: [ui, board]",
                "created: 2026-11-12",
                body="Text.\n\n## Log\n",
            )
        )
        self.assertEqual(
            fields,
            {
                "id": "EX-12",
                "title": "Fix: crash on drop",
                "labels": ["ui", "board"],
                "created": "2026-11-12",
            },
        )
        self.assertEqual(list(fields), ["id", "title", "labels", "created"])
        self.assertEqual(body, "Text.\n\n## Log\n")

    def test_reads_escapes_inside_quotes(self):
        fields, _ = read(header_file(r'title: "say \"hi\" to C:\\temp"'))
        self.assertEqual(fields["title"], 'say "hi" to C:\\temp')

    def test_reads_quoted_list_items(self):
        fields, _ = read(header_file('labels: ["a, b", c, "yes"]'))
        self.assertEqual(fields["labels"], ["a, b", "c", "yes"])

    def test_accepts_loose_spacing_and_needless_quotes(self):
        fields, _ = read(header_file('title:   "plain"  ', "labels: [ ui ,board ]"))
        self.assertEqual(fields, {"title": "plain", "labels": ["ui", "board"]})

    def test_reads_an_empty_list(self):
        fields, _ = read(header_file("labels: []"))
        self.assertEqual(fields["labels"], [])

    def test_body_can_be_empty(self):
        self.assertEqual(read("---\nid: EX-1\n---\n"), ({"id": "EX-1"}, ""))


class ReadErrorTest(unittest.TestCase):
    CASES = [
        ("no opening fence", "id: EX-1\n---\n", 1, "must start with a --- line"),
        ("no closing fence", "---\nid: EX-1\n", 3, "no closing --- line"),
        ("blank line", header_file("id: EX-1", "", "type: task"), 3, "blank lines"),
        ("comment", header_file("# note", "id: EX-1"), 2, "comments"),
        ("nested value", header_file("id: EX-1", "  sub: x"), 3, "nested"),
        ("block list", header_file("labels:", "- ui"), 2, "has no value"),
        ("dash line", header_file("id: EX-1", "- ui"), 3, "[a, b]"),
        ("uppercase key", header_file("Title: x"), 2, "lowercase key"),
        ("no space", header_file("title:x"), 2, "space after the colon"),
        ("empty value", header_file("title:"), 2, "leave the field out"),
        ("duplicate", header_file("id: EX-1", "id: EX-2"), 3, "appears twice"),
        ("comment in value", header_file("title: Fix #12 now"), 2, "comment"),
        ("colon in value", header_file("title: Fix: crash"), 2, "': '"),
        ("indicator start", header_file("title: *bold*"), 2, "starting with *"),
        ("bad escape", header_file(r'title: "tab\t"'), 2, "only"),
        ("unclosed quote", header_file('title: "open'), 2, "no closing quote"),
        ("text after quote", header_file('title: "a" b'), 2, "after the closing quote"),
        ("unclosed list", header_file("title: [draft] Board"), 2, "wrap text in quotes"),
        ("trailing comma", header_file("labels: [ui, ]"), 2, "end with a comma"),
        ("nested list", header_file("labels: [[ui]]"), 2, "other than letters"),
        ("odd list item", header_file("labels: [c?1]"), 2, "other than letters"),
        ("bare equals", header_file("title: ="), 2, "on its own"),
        ("missing comma", header_file('labels: ["a" "b"]'), 2, "comma"),
        ("tab in value", header_file("title: Fix\tcrash"), 2, "control character"),
        ("tab in quotes", header_file('title: "Fix\tcrash"'), 2, "control character"),
        ("NUL in list", header_file('labels: ["a\x00b"]'), 2, "control character"),
        ("C1 control", header_file("title: a\x9bb"), 2, "control character"),
        ("line separator", header_file("title: a\u2028b"), 2, "control character"),
    ]

    def test_rejects_what_yaml_would_read_differently(self):
        for name, text, line, message in self.CASES:
            with self.subTest(name):
                with self.assertRaises(HeaderError) as caught:
                    read(text)
                self.assertEqual(caught.exception.line, line)
                self.assertIn(message, caught.exception.message)


class WriteTest(unittest.TestCase):
    SCALARS = [
        ("title", "Drag cards between columns", "Drag cards between columns"),
        ("title", "Ünïcode — dashes and accents", "Ünïcode — dashes and accents"),
        ("title", "C:\\temp and a:b", "C:\\temp and a:b"),
        ("release", "v0.1", "v0.1"),
        ("title", "Fix: crash on drop", '"Fix: crash on drop"'),
        ("title", "Ticket #12 crash", '"Ticket #12 crash"'),
        ("title", "Ends with:", '"Ends with:"'),
        ("title", "[draft] Board", '"[draft] Board"'),
        ("title", '"Quoted" "title"', '"\\"Quoted\\" \\"title\\""'),
        ("title", "`corkboard` CLI", '"`corkboard` CLI"'),
        ("title", "*bold*", '"*bold*"'),
        ("title", "- dash first", '"- dash first"'),
        ("title", "#12 first", '"#12 first"'),
        ("title", " leading space", '" leading space"'),
        ("title", "trailing space ", '"trailing space "'),
        ("title", "", '""'),
        ("title", "yes", '"yes"'),
        ("title", "Off", '"Off"'),
        ("title", "null", '"null"'),
        ("title", "~", '"~"'),
        ("title", "12", '"12"'),
        ("title", "1.0", '"1.0"'),
        ("title", "0x1F", '"0x1F"'),
        ("title", "1e3", '"1e3"'),
        ("title", ".inf", '".inf"'),
        ("title", "=", '"="'),
        ("title", "<<", '"<<"'),
        ("title", "1:30", '"1:30"'),
        ("title", "2026-11-12", '"2026-11-12"'),
        ("created", "2026-11-12", "2026-11-12"),
        ("date", "2026-12-01", "2026-12-01"),
        ("created", "soon", "soon"),
        ("title", 'back\\slash "q" inside', 'back\\slash "q" inside'),
        ("title", '"q" back\\slash', '"\\"q\\" back\\\\slash"'),
    ]

    LISTS = [
        (["ui", "board"], "[ui, board]"),
        (["EX-9", "EX-10"], "[EX-9, EX-10]"),
        (["a, b", "c"], '["a, b", c]'),
        (["x]y", "{z}"], '["x]y", "{z}"]'),
        (["yes"], '["yes"]'),
        (
            ["good first issue", "é-ui", "docs/api", "v0.1"],
            "[good first issue, é-ui, docs/api, v0.1]",
        ),
        (["c?1", "a:b", "_x", "#tag"], '["c?1", "a:b", "_x", "#tag"]'),
        ([], "[]"),
    ]

    def test_quotes_exactly_when_yaml_would_misread(self):
        for key, value, expected in self.SCALARS:
            with self.subTest(value=value):
                self.assertEqual(format_value(key, value), expected)
                fields, _ = read(header_file(f"{key}: {expected}"))
                self.assertEqual(fields[key], value)

    def test_writes_lists(self):
        for value, expected in self.LISTS:
            with self.subTest(value=value):
                self.assertEqual(format_value("labels", value), expected)
                fields, _ = read(header_file(f"labels: {expected}"))
                self.assertEqual(fields["labels"], value)

    def test_writes_a_whole_file(self):
        text = write({"id": "EX-1", "title": "Fix: it", "labels": ["ui"]}, "Body.\n")
        self.assertEqual(text, '---\nid: EX-1\ntitle: "Fix: it"\nlabels: [ui]\n---\nBody.\n')

    def test_refuses_line_breaks_and_bad_keys(self):
        # YAML reads \x85, U+2028 and U+2029 as line breaks, and refuses the other C1 controls.
        for text in ("two\nlines", "a\tb", "a\x85b", "a\u2028b", "a\u2029b", "a\x9bb"):
            with self.subTest(text=repr(text)), self.assertRaises(ValueError):
                format_value("title", text)
        with self.assertRaises(ValueError):
            write({"Title": "x"}, "")

    def test_canonical_drops_needless_quotes_and_spaces(self):
        loose = header_file('title:   "plain"', "labels: [ ui ,board ]")
        self.assertEqual(canonical(loose), header_file("title: plain", "labels: [ui, board]"))


class RoundTripTest(unittest.TestCase):
    def assert_round_trip(self, path_name: str, text: str) -> None:
        with self.subTest(path_name):
            self.assertEqual(canonical(text), text)

    def test_this_repos_items_and_releases_are_canonical(self):
        paths = sorted((REPO / ".project").glob("items/*.md"))
        paths += sorted((REPO / ".project").glob("releases/*.md"))
        self.assertGreater(len(paths), 10)
        for path in paths:
            self.assert_round_trip(path.name, path.read_text(encoding="utf-8"))

    def test_header_examples_in_the_spec_are_canonical(self):
        examples = []
        for path in sorted((REPO / ".project" / "docs").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for block in re.findall(r"```markdown\n(---\n.*?\n---\n)", text, re.DOTALL):
                examples.append((path.name, block))
        self.assertGreaterEqual(len(examples), 2)
        for name, block in examples:
            self.assert_round_trip(name, block)


if __name__ == "__main__":
    unittest.main()
