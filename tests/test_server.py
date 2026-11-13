import http.client
import json
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from helpers import LOG, REPO, Fixture, run_cli

from corkboard import server
from corkboard.cli import CommandError

BIN = REPO / "bin" / "corkboard"


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind((server.HOST, 0))
        return probe.getsockname()[1]


def get(port: int, path: str, host: str | None = None) -> tuple[int, str, bytes]:
    """GET a path from 127.0.0.1. Returns the status, content type and body."""
    connection = http.client.HTTPConnection(server.HOST, port, timeout=5)
    try:
        headers = {"Host": host} if host else {}
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        return response.status, response.getheader("Content-Type"), response.read()
    finally:
        connection.close()


class ServerTest(unittest.TestCase):
    """A real server on a free port, serving a Fixture repo."""

    def serve(
        self, fixture: Fixture, ports=(0,), web=server.WEB, clock=datetime.now
    ) -> server.Server:
        running = server.start(fixture.root, ports, web, clock)
        # A short poll interval, so shutdown doesn't wait the default half second.
        thread = threading.Thread(target=running.serve_forever, args=(0.01,), daemon=True)
        thread.start()
        self.addCleanup(running.server_close)
        self.addCleanup(running.shutdown)
        return running

    def api(self, running: server.Server) -> dict:
        status, content_type, body = get(running.port, "/api/project")
        self.assertEqual((status, content_type), (200, "application/json"))
        return json.loads(body)


class StaticTest(ServerTest):
    def setUp(self):
        self.fixture = Fixture(self)
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.web = Path(folder.name) / "web"
        (self.web / "vendor").mkdir(parents=True)
        (self.web / "index.html").write_text("<p>index</p>", encoding="utf-8")
        (self.web / "vendor" / "app.js").write_text("export {};", encoding="utf-8")
        (Path(folder.name) / "secret.txt").write_text("secret", encoding="utf-8")
        self.running = self.serve(self.fixture, web=self.web)

    def test_files_in_web(self):
        status, content_type, body = get(self.running.port, "/vendor/app.js")
        self.assertEqual(
            (status, content_type, body), (200, "text/javascript; charset=utf-8", b"export {};")
        )

    def test_app_routes_get_index_html(self):
        for path in ("/", "/board", "/releases/v0.1", "/items/EX-12", "/docs/a/b?x=1"):
            with self.subTest(path=path):
                status, content_type, body = get(self.running.port, path)
                self.assertEqual((status, body), (200, b"<p>index</p>"))
                self.assertEqual(content_type, "text/html; charset=utf-8")

    def test_never_serves_files_outside_web(self):
        for path in ("/../secret.txt", "/%2e%2e/secret.txt", "/vendor/../../secret.txt", "/%00"):
            with self.subTest(path=path):
                self.assertEqual(get(self.running.port, path)[2], b"<p>index</p>")

    def test_unknown_api_path(self):
        status, _, body = get(self.running.port, "/api/nothing")
        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body), {"error": "there's no /api/nothing"})

    def test_refuses_other_hosts(self):
        port = self.running.port
        for host in ("evil.example", f"evil.example:{port}", "localhost:1"):
            with self.subTest(host=host):
                self.assertEqual(get(port, "/api/project", host=host)[0], 403)
        for host in (f"localhost:{port}", f"127.0.0.1:{port}"):
            with self.subTest(host=host):
                self.assertEqual(get(port, "/api/project", host=host)[0], 200)

    def test_security_headers_on_every_response(self):
        for path in ("/", "/vendor/app.js", "/api/project", "/api/nothing"):
            with self.subTest(path=path):
                connection = http.client.HTTPConnection(server.HOST, self.running.port, timeout=5)
                connection.request("GET", path)
                response = connection.getresponse()
                response.read()
                connection.close()
                policy = response.getheader("Content-Security-Policy")
                self.assertIn("script-src 'self';", policy)
                self.assertIn("frame-ancestors 'none'", policy)
                self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")


class WebAppFilesTest(unittest.TestCase):
    """The page's own files: everything it loads is committed, with no build step."""

    IMPORT = re.compile(r"""(?:from|import)\s*["']([^"']+)["']""")

    def test_the_page_loads_its_script_and_styles(self):
        page = (server.WEB / "index.html").read_text(encoding="utf-8")
        for path in re.findall(r'(?:src|href)="/([^"]+)"', page):
            with self.subTest(path=path):
                self.assertTrue((server.WEB / path).is_file())

    def test_every_import_is_a_committed_file(self):
        scripts = sorted((server.WEB / "app").glob("*.js")) + [
            server.WEB / "vendor" / "hooks.module.js"
        ]
        for script in scripts:
            for target in self.IMPORT.findall(script.read_text(encoding="utf-8")):
                with self.subTest(script=script.name, target=target):
                    self.assertTrue(target.startswith("."), "imports must be relative paths")
                    self.assertTrue((script.parent / target).resolve().is_file())

    def test_vendored_libraries_have_their_licenses(self):
        for name in ("preact", "htm", "marked"):
            self.assertTrue((server.WEB / "vendor" / f"{name}.LICENSE").is_file())


class ReadApiTest(ServerTest):
    def setUp(self):
        fixture = Fixture(self)
        fixture.release("v0.1", "active", "Ship the board.\n")
        fixture.release("v0.2", "planned")
        fixture.item("EX-1", type="epic", title="Board view", release="v0.1")
        fixture.item(
            "EX-2",
            "Drag cards.\n\n## Subtasks\n- [x] Find the column\n- [ ] Save it\n" + LOG,
            parent="EX-1",
            status="in-progress",
            priority="high",
            labels=["ui", "board"],
        )
        fixture.item(
            "EX-3",
            body="\n## Log\n- 2026-11-12 10:00 me: created\n"
            "- 2026-11-12 11:00 claude: moved to waiting: Debounce, or rebuild?\n",
            parent="EX-1",
            status="waiting",
            type="bug",
        )
        fixture.item(
            "EX-4",
            body="\n## Log\n- 2026-11-12 10:00 me: created\n"
            "- 2026-11-12 11:00 claude: moved to waiting: Which one?\n"
            "- 2026-11-12 12:00 me: moved to todo: The first\n",
        )
        fixture.item("EX-5", parent="EX-1", blocked_by=["EX-2"])
        fixture.item("EX-6", status="done")
        fixture.item("EX-7", release="v0.1")
        fixture.raw("items", "EX-8-broken.md", "no header\n")
        self.fixture = fixture
        self.running = self.serve(fixture)

    def test_the_project(self):
        data = self.api(self.running)
        self.assertEqual(
            (data["name"], data["prefix"], data["active_release"]), ("Example", "EX", "v0.1")
        )
        self.assertEqual([item["id"] for item in data["items"]], [f"EX-{n}" for n in range(1, 8)])
        self.assertEqual(data["root"], str(self.fixture.root.resolve()))
        self.assertEqual(
            data["problems"], ["EX-8-broken.md: line 1: the file must start with a --- line"]
        )

    def test_releases_with_progress(self):
        v01, v02 = self.api(self.running)["releases"]
        self.assertEqual(
            v01,
            {
                "name": "v0.1",
                "status": "active",
                "date": None,
                "goal": "Ship the board.",
                "path": ".project/releases/v0.1.md",
                "progress": {"done": 0, "total": 4},
            },
        )
        self.assertEqual((v02["name"], v02["progress"]), ("v0.2", {"done": 0, "total": 0}))

    def test_an_item(self):
        items = {item["id"]: item for item in self.api(self.running)["items"]}
        self.assertEqual(
            items["EX-2"],
            {
                "id": "EX-2",
                "type": "task",
                "title": "Item EX-2",
                "status": "in-progress",
                "priority": "high",
                "owner": "claude",
                "created": "2026-11-12",
                "parent": "EX-1",
                "release": "v0.1",
                "release_from_epic": True,
                "labels": ["ui", "board"],
                "blocked_by": [],
                "open_blockers": [],
                "related": [],
                "duplicate_of": None,
                "path": ".project/items/EX-2-item-ex-2.md",
                "description": "Drag cards.",
                "subtasks": [
                    {"text": "Find the column", "done": True},
                    {"text": "Save it", "done": False},
                ],
                "log": [{"date": "2026-11-12", "time": "10:00", "who": "me", "text": "created"}],
                "answered": False,
                "waiting_message": None,
            },
        )

    def test_what_the_cli_works_out(self):
        data = self.api(self.running)
        items = {item["id"]: item for item in data["items"]}
        self.assertEqual(items["EX-1"]["progress"], {"done": 0, "total": 3})
        self.assertNotIn("progress", items["EX-2"])
        self.assertEqual(items["EX-3"]["waiting_message"], "Debounce, or rebuild?")
        self.assertTrue(items["EX-4"]["answered"])
        self.assertEqual(items["EX-5"]["open_blockers"], ["EX-2"])
        self.assertEqual(
            (items["EX-7"]["release"], items["EX-7"]["release_from_epic"]), ("v0.1", False)
        )
        self.assertEqual(
            (items["EX-6"]["release"], items["EX-6"]["release_from_epic"]), (None, False)
        )
        # The order of work: answered first, then the active release; EX-5 is blocked.
        self.assertEqual(data["next"], ["EX-4", "EX-7"])

    def test_an_items_mentions(self):
        self.fixture.doc("plan.md", "EX-2 comes first.\n")
        self.fixture.item("EX-9", "See EX-2.\n" + LOG)
        status, _, body = get(self.running.port, "/api/items/ex-2")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"id": "EX-2", "mentions": ["docs/plan.md", "EX-9"]})
        status, _, body = get(self.running.port, "/api/items/EX-99")
        self.assertEqual((status, json.loads(body)), (404, {"error": "there's no item EX-99"}))

    def test_reads_the_files_again_on_each_request(self):
        self.api(self.running)
        self.fixture.item("EX-9", title="Added later")
        titles = [item["title"] for item in self.api(self.running)["items"]]
        self.assertIn("Added later", titles)


class PortsTest(ServerTest):
    def test_moves_on_from_a_taken_port(self):
        with socket.socket() as taken:
            taken.bind((server.HOST, 0))
            taken.listen()
            port = taken.getsockname()[1]
            running = self.serve(Fixture(self), ports=[port, 0])
            self.assertNotEqual(running.port, port)
            self.assertEqual(get(running.port, "/api/server")[0], 200)

    def test_no_free_port(self):
        with socket.socket() as first, socket.socket() as second:
            for taken in (first, second):
                taken.bind((server.HOST, 0))
                taken.listen()
            ports = [first.getsockname()[1], second.getsockname()[1]]
            with self.assertRaises(CommandError) as raised:
                server.start(Fixture(self).root, ports)
        self.assertIn("no free port", str(raised.exception))

    def test_finds_a_server_already_running_for_the_repo(self):
        fixture = Fixture(self)
        running = self.serve(fixture)
        ports = [free_port(), running.port]
        self.assertEqual(
            server.find_running(fixture.root, ports), f"http://localhost:{running.port}"
        )
        self.assertIsNone(server.find_running(Fixture(self).root, ports))

    def test_ignores_a_port_that_isnt_corkboard(self):
        with socket.socket() as other:
            other.bind((server.HOST, 0))
            other.listen()
            # It accepts the connection and never answers, so the probe has to time out.
            self.assertIsNone(server.find_running(Fixture(self).root, [other.getsockname()[1]]))


class EventsTest(ServerTest):
    """GET /api/events: a server-sent event whenever a file in .project/ changes."""

    def setUp(self):
        self.fixture = Fixture(self)
        self.fixture.item("EX-1")

    def stream(self, running: server.Server):
        connection = http.client.HTTPConnection(server.HOST, running.port, timeout=5)
        self.addCleanup(connection.close)
        connection.request("GET", "/api/events")
        response = connection.getresponse()
        self.assertEqual(response.getheader("Content-Type"), "text/event-stream")
        self.assertEqual(next_event(response), "retry: 1000\n")
        return response

    def test_a_changed_file_sends_an_event_within_2_seconds(self):
        response = self.stream(self.serve(self.fixture))
        started = time.monotonic()
        run_cli(self.fixture.repo, "move", "EX-1", "in-progress")
        self.assertEqual(next_event(response), "event: change\ndata: {}\n")
        self.assertLess(time.monotonic() - started, 2)

    def test_new_and_removed_files_count_as_changes(self):
        running = self.serve(self.fixture)
        running.poll_seconds = 0.02
        response = self.stream(running)
        path = self.fixture.item("EX-2")
        self.assertEqual(next_event(response), "event: change\ndata: {}\n")
        path.unlink()
        self.assertEqual(next_event(response), "event: change\ndata: {}\n")

    def test_a_quiet_stream_still_sends_a_line_now_and_then(self):
        running = self.serve(self.fixture)
        running.poll_seconds = 0.02
        with mock.patch.object(server, "HEARTBEAT_SECONDS", 0.1):
            response = self.stream(running)
            self.assertEqual(next_event(response), ": still here\n")

    def test_closing_the_server_ends_the_stream(self):
        running = self.serve(self.fixture)
        running.poll_seconds = 0.02
        response = self.stream(running)
        running.shutdown()
        running.server_close()
        self.assertEqual(next_event(response), "")


def next_event(response) -> str:
    """The next event's lines, up to the blank line after it, or "" when the stream ends."""
    lines = []
    while True:
        line = response.readline().decode("utf-8")
        if not line:
            return "".join(lines)
        if line == "\n" and lines:
            return "".join(lines)
        if line != "\n":
            lines.append(line)


class UiCommandTest(unittest.TestCase):
    """bin/corkboard ui as a real process, stopped the way Ctrl-C stops it."""

    def start_ui(self, fixture: Fixture) -> subprocess.Popen:
        process = subprocess.Popen(
            [sys.executable, str(BIN), "ui"],
            cwd=fixture.repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={key: value for key, value in os.environ.items() if key != "CLAUDECODE"},
            # A test run started in the background ignores SIGINT, and the child would inherit it.
            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_DFL),
        )
        self.addCleanup(process.kill)
        self.addCleanup(process.stdout.close)
        self.addCleanup(process.stderr.close)
        return process

    def test_prints_the_url_serves_and_stops_on_ctrl_c(self):
        fixture = Fixture(self)
        fixture.item("EX-1")
        process = self.start_ui(fixture)
        line = process.stdout.readline()
        self.assertRegex(line, r"^Corkboard: http://localhost:47[4-6][0-9]\n$")
        port = int(line.rsplit(":", 1)[1])
        self.assertEqual(json.loads(get(port, "/api/project")[2])["items"][0]["id"], "EX-1")

        again = subprocess.run(
            [sys.executable, str(BIN), "ui"],
            cwd=fixture.repo,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual((again.returncode, again.stdout, again.stderr), (0, line, ""))

        process.send_signal(signal.SIGINT)
        self.assertEqual(process.wait(timeout=10), 0)
        self.assertEqual(process.stderr.read(), "")

    def test_takes_no_arguments(self):
        code, _, err = run_cli(Fixture(self).repo, "ui", "extra")
        self.assertEqual((code, err), (1, "error: usage: corkboard ui\n"))


if __name__ == "__main__":
    unittest.main()
