import http.client
import json
import unittest

from helpers import LOG, NOW, Fixture, run_cli
from test_server import ServerTest

from corkboard import server

WAITING = (
    "\n## Log\n- 2026-11-12 10:00 claude: created\n"
    "- 2026-11-12 11:00 claude: moved to waiting: Debounce, or rebuild?\n"
)


def build(fixture: Fixture) -> Fixture:
    fixture.release("v0.1", "active")
    fixture.item("EX-1", type="epic", title="Board view", release="v0.1")
    fixture.item(
        "EX-2",
        "Drag cards.\n\n## Subtasks\n- [ ] Find the column\n- [x] Save it\n" + LOG,
        parent="EX-1",
    )
    fixture.item("EX-3", WAITING, status="waiting", type="bug", parent="EX-1", related=["EX-2"])
    return fixture


def snapshot(fixture: Fixture) -> dict[str, str]:
    """Every file in .project/, by its path inside it."""
    return {
        path.relative_to(fixture.root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(fixture.root.rglob("*"))
        if path.is_file()
    }


def post(
    port, path, data=None, *, origin="own", host=None, content_type="application/json", raw=None
):
    """POST to the server. Returns the status and the decoded JSON answer."""
    headers = {"Content-Type": content_type}
    if origin == "own":
        origin = f"http://localhost:{port}"
    if origin:
        headers["Origin"] = origin
    if host:
        headers["Host"] = host
    body = raw if raw is not None else json.dumps(data or {}).encode()
    connection = http.client.HTTPConnection(server.HOST, port, timeout=5)
    try:
        connection.request("POST", path, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()


class WriteApiTest(ServerTest):
    def serve_fixture(self) -> tuple[Fixture, server.Server]:
        fixture = build(Fixture(self))
        return fixture, self.serve(fixture, clock=lambda: NOW)

    def assert_same_as_cli(self, cli_args, path, data, stdin=None):
        """From the same start, the API's change leaves .project/ just as the CLI command does."""
        by_cli = build(Fixture(self))
        code, out, err = run_cli(by_cli.repo, *cli_args, "--as", "me", stdin=stdin)
        self.assertEqual(code, 0, err)
        fixture, running = self.serve_fixture()
        status, answer = post(running.port, path, data)
        self.assertEqual(status, 200, answer)
        self.assertEqual(snapshot(fixture), snapshot(by_cli))
        self.assertEqual(answer["line"], out.strip().splitlines()[-1])
        return answer

    def test_new(self):
        body = "Cap columns.\n\n## Subtasks\n- [ ] Add a limit\n"
        answer = self.assert_same_as_cli(
            [
                "new",
                "task",
                "Board column limits",
                "parent=EX-1",
                "priority=high",
                "labels=ui,board",
            ],
            "/api/items",
            {
                "type": "task",
                "title": "Board column limits",
                "fields": {"parent": "EX-1", "priority": "high", "labels": ["ui", "board"]},
                "body": body,
            },
            stdin=body,
        )
        self.assertEqual(answer["id"], "EX-4")

    def test_move_with_a_reply(self):
        self.assert_same_as_cli(
            ["move", "EX-3", "todo", "Debounce it"],
            "/api/items/EX-3/move",
            {"status": "todo", "message": "Debounce it"},
        )

    def test_move_with_a_warning(self):
        answer = self.assert_same_as_cli(
            ["move", "EX-1", "done"], "/api/items/EX-1/move", {"status": "done"}
        )
        self.assertEqual(len(answer["warnings"]), 1)
        self.assertIn("EX-2", answer["warnings"][0])

    def test_set_renames_the_file(self):
        self.assert_same_as_cli(
            ["set", "EX-2", "title=Drag cards between columns", "priority=high", "labels=ui"],
            "/api/items/EX-2/set",
            {"fields": {"title": "Drag cards between columns", "priority": "high", "labels": "ui"}},
        )

    def test_sub(self):
        for args, data in (
            (
                ["add", "Put it back on failure"],
                {"action": "add", "value": "Put it back on failure"},
            ),
            (["done", "1"], {"action": "done", "value": "1"}),
            (["undo", "2"], {"action": "undo", "value": "2"}),
        ):
            with self.subTest(args=args):
                self.assert_same_as_cli(["sub", "EX-2", *args], "/api/items/EX-2/sub", data)

    def test_log(self):
        self.assert_same_as_cli(
            ["log", "EX-2", "Chose", "the", "drop", "event"],
            "/api/items/EX-2/log",
            {"text": "Chose the drop event"},
        )

    def test_release(self):
        goal = "Search and docs.\n"
        self.assert_same_as_cli(
            ["release", "v0.2", "date=2026-12-01"],
            "/api/releases/v0.2",
            {"fields": {"date": "2026-12-01"}, "goal": goal},
            stdin=goal,
        )

    def test_links(self):
        # The page sends the item's whole list: the links it has plus the new one.
        for item_id, arg, fields in (
            ("EX-2", "blocked_by=EX-3", {"blocked_by": ["EX-3"]}),
            ("EX-3", "related=EX-2,EX-1", {"related": ["EX-2", "EX-1"]}),
            ("EX-3", "duplicate_of=EX-2", {"duplicate_of": "EX-2"}),
        ):
            with self.subTest(arg=arg):
                self.assert_same_as_cli(
                    ["set", item_id, arg], f"/api/items/{item_id}/set", {"fields": fields}
                )

    def test_a_link_shows_on_both_items(self):
        fixture, running = self.serve_fixture()
        status, answer = post(
            running.port, "/api/items/EX-2/set", {"fields": {"blocked_by": ["EX-3"]}}
        )
        self.assertEqual(status, 200, answer)
        status, answer = post(
            running.port, "/api/items/EX-3/set", {"fields": {"duplicate_of": "EX-2"}}
        )
        self.assertEqual(status, 200, answer)
        items = {item["id"]: item for item in self.api(running)["items"]}
        two, three = items["EX-2"], items["EX-3"]
        self.assertEqual((two["blocked_by"], three["blocks"]), (["EX-3"], ["EX-2"]))
        # EX-3 stores the related link; both items show it.
        self.assertEqual((three["related"], two["related"]), (["EX-2"], []))
        self.assertEqual((three["related_to"], two["related_to"]), (["EX-2"], ["EX-3"]))
        self.assertEqual((three["duplicate_of"], two["duplicated_by"]), ("EX-2", ["EX-3"]))

        code, out, err = run_cli(fixture.repo, "show", "EX-3")
        self.assertEqual(code, 0, err)
        self.assertIn("blocks: EX-2 Item EX-2 (todo)\n", out)
        code, out, err = run_cli(fixture.repo, "show", "EX-2")
        self.assertIn("blocked by: EX-3 Item EX-3 (waiting)\n", out)
        self.assertIn("duplicated by: EX-3 Item EX-3 (waiting)\n", out)

    def test_describe_conflict_answers_409_with_the_version_on_disk(self):
        fixture, running = self.serve_fixture()
        status, answer = post(
            running.port, "/api/items/EX-2/describe", {"description": "Mine.", "base": "Old text."}
        )
        self.assertEqual(
            (status, answer),
            (
                409,
                {
                    "error": "the description of EX-2 changed while you were editing it",
                    "current": "Drag cards.",
                },
            ),
        )
        status, answer = post(
            running.port,
            "/api/items/EX-2/describe",
            {"description": "Mine.", "base": "Drag cards."},
        )
        self.assertEqual(status, 200)
        self.assertTrue(
            fixture.text("EX-2").split("---\n", 2)[2].startswith("Mine.\n\n## Subtasks")
        )

    def test_writes_are_logged_as_me(self):
        fixture, running = self.serve_fixture()
        post(running.port, "/api/items/EX-2/log", {"text": "A note"})
        self.assertIn("- 2026-11-13 15:30 me: A note\n", fixture.text("EX-2"))

    def test_refused_changes_write_nothing(self):
        fixture, running = self.serve_fixture()
        port = running.port
        before = snapshot(fixture)
        cases = [
            ({"origin": None}, 403, "changes are only accepted from Corkboard's own page"),
            (
                {"origin": "http://evil.example"},
                403,
                "changes are only accepted from Corkboard's own page",
            ),
            ({"origin": "null"}, 403, "changes are only accepted from Corkboard's own page"),
            (
                {"origin": f"http://localhost:{port + 1}"},
                403,
                "changes are only accepted from Corkboard's own page",
            ),
            ({"host": "evil.example"}, 403, "this server only answers to localhost"),
            ({"content_type": "text/plain"}, 415, "send changes as application/json"),
            (
                {"content_type": "application/x-www-form-urlencoded"},
                415,
                "send changes as application/json",
            ),
            ({"raw": b"{not json"}, 400, "the body isn't valid JSON"),
            ({"raw": b"[1]"}, 400, "the body must be a JSON object"),
        ]
        for options, status, error in cases:
            with self.subTest(options=options):
                answer = post(port, "/api/items/EX-2/log", {"text": "Sneaky"}, **options)
                self.assertEqual(answer, (status, {"error": error}))
        self.assertEqual(snapshot(fixture), before)

    def test_errors(self):
        fixture, running = self.serve_fixture()
        port = running.port
        before = snapshot(fixture)
        cases = [
            ("/api/items/EX-99/move", {"status": "done"}, 404, "there's no item EX-99"),
            ("/api/items/EX-2/fly", {}, 404, "there's no /api/items/EX-2/fly"),
            ("/api/nothing", {}, 404, "there's no /api/nothing"),
            (
                "/api/items/EX-2/move",
                {"status": "bogus"},
                400,
                '"bogus" isn\'t a status. Use one of: '
                "backlog, todo, in-progress, waiting, done, cancelled",
            ),
            (
                "/api/items/EX-2/move",
                {"status": "waiting"},
                400,
                "moving to waiting needs a message: the question, or what to review",
            ),
            ("/api/items/EX-2/move", {"status": 3}, 400, "status must be text"),
            ("/api/items/EX-2/log", {"text": "  "}, 400, "a note needs some text"),
            (
                "/api/items/EX-2/set",
                {"fields": {"blocked_by": ["EX-99"]}},
                400,
                "blocked_by names EX-99, and there's no such item",
            ),
            (
                "/api/items/EX-2/set",
                {"fields": {"related": ["EX-3", "EX-2"]}},
                400,
                "related can't name the item itself",
            ),
            (
                "/api/items/EX-2/set",
                {"fields": "priority=high"},
                400,
                'fields must be an object, such as {"priority": "high"}',
            ),
            (
                "/api/items",
                {"type": "story", "title": "X"},
                400,
                '"story" isn\'t an item type. Use one of: epic, task, bug',
            ),
        ]
        for path, data, status, error in cases:
            with self.subTest(path=path, data=data):
                self.assertEqual(post(port, path, data), (status, {"error": error}))
        self.assertEqual(snapshot(fixture), before)

    def test_gets_dont_write(self):
        fixture, running = self.serve_fixture()
        connection = http.client.HTTPConnection(server.HOST, running.port, timeout=5)
        connection.request("GET", "/api/items/EX-2/log")
        response = connection.getresponse()
        response.read()
        connection.close()
        self.assertEqual(response.status, 404)


if __name__ == "__main__":
    unittest.main()
