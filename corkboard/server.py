"""`corkboard ui`: the web app's local server, as cli.md and ui.md describe it.

It listens on 127.0.0.1 only, on the first free port in PORTS, and serves the page in web/ and the
read API. Every API request loads .project/ again, so the page always matches the files. A path
that isn't a file in web/ or under /api/ gets index.html, since the page routes /board,
/releases/v0.1 and /items/EX-12 itself.

A request whose Host isn't this server's own address is refused. Without that, a site could point
its own domain name at 127.0.0.1 (DNS rebinding) and read the project from the browser. A change
(POST) must also come from the app's own page, by its Origin header, and be JSON, which a form on
another site can't send. Changes go through api.write one at a time, logged as `me`.

Live updates: GET /api/events is a stream of server-sent events. Each open stream checks the
modification times and sizes of the files in .project/ every second and sends a `change` event
when any differ, and the page loads the project again. A comment line every 15 seconds notices a
closed tab.

Before starting, it asks each port in PORTS whether a corkboard server for this repo is already
there, and if one is, it prints that server's URL instead of starting another.
"""

from __future__ import annotations

import errno
import http.client
import json
import socketserver
import threading
from collections.abc import Callable, Iterable
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from . import api
from .cli import CommandError, Context, usage_error
from .edits import EditError
from .project import load

HOST = "127.0.0.1"
PORTS = range(4747, 4767)
WEB = Path(__file__).resolve().parent / "web"
PROBE_TIMEOUT = 0.5
MAX_BODY = 1_000_000
POLL_SECONDS = 1.0
HEARTBEAT_SECONDS = 15.0

# Scripts and styles only from the app's own files, nothing inline, and no framing by other pages.
# Markdown already renders with raw HTML off; this stops a script even if something slips through.
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
    "img-src 'self' data: https:; connect-src 'self'; object-src 'none'; base-uri 'none'; "
    "form-action 'self'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".txt": "text/plain; charset=utf-8",
}


def ui(ctx: Context, args: list[str]) -> None:
    if args:
        raise usage_error("ui")
    root = ctx.project().root
    url = find_running(root, PORTS)
    server = None if url else start(root, PORTS)
    ctx.print(f"Corkboard: {url or server.url}")
    ctx.out.flush()  # when output is piped, as with /corkboard:ui, the line would wait otherwise
    if server is None:
        return
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


class Server(ThreadingHTTPServer):
    """One repo's web app and read API, on one port."""

    # SO_REUSEPORT would let a second server bind a port that's taken, instead of moving on.
    allow_reuse_port = False

    def __init__(
        self,
        root: Path,
        port: int,
        web: Path = WEB,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.root = root
        self.web = web.resolve()
        self.clock = clock
        self.write_lock = threading.Lock()
        self.poll_seconds = POLL_SECONDS
        self.stopping = threading.Event()  # set before binding, since a failed bind closes
        super().__init__((HOST, port), Handler)
        self.hosts = {f"localhost:{self.port}", f"{HOST}:{self.port}"}
        self.origins = {f"http://{host}" for host in self.hosts}

    def server_close(self) -> None:
        self.stopping.set()  # ends the event streams
        super().server_close()

    def server_bind(self) -> None:
        # HTTPServer's own version looks up the machine's full domain name, which can stall.
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = HOST, self.port

    @property
    def port(self) -> int:
        return self.server_address[1]

    @property
    def url(self) -> str:
        return f"http://localhost:{self.port}"


def start(
    root: Path,
    ports: Iterable[int],
    web: Path = WEB,
    clock: Callable[[], datetime] = datetime.now,
) -> Server:
    """A server for the repo on the first free port. It answers once serve_forever runs."""
    ports = list(ports)
    for port in ports:
        try:
            return Server(root, port, web, clock)
        except OSError as error:
            if error.errno != errno.EADDRINUSE:
                raise
    raise CommandError(
        f"no free port from {ports[0]} to {ports[-1]}. Stop a server you don't need first."
    )


def find_running(root: Path, ports: Iterable[int]) -> str | None:
    """The URL of a corkboard server already serving this repo on one of the ports, if any."""
    wanted = str(root.resolve())
    for port in ports:
        if _serving(port) == wanted:
            return f"http://localhost:{port}"
    return None


def _serving(port: int) -> str | None:
    """The .project/ folder that a corkboard server on this port serves, or None."""
    connection = http.client.HTTPConnection(HOST, port, timeout=PROBE_TIMEOUT)
    try:
        connection.request("GET", "/api/server")
        response = connection.getresponse()
        data = json.loads(response.read()) if response.status == 200 else None
    except (OSError, http.client.HTTPException, ValueError):
        return None  # nothing there, or something that isn't corkboard
    finally:
        connection.close()
    if isinstance(data, dict) and data.get("app") == "corkboard":
        return data.get("project")
    return None


class Handler(BaseHTTPRequestHandler):
    server: Server
    server_version = "corkboard"

    def do_GET(self) -> None:
        if self.headers.get("Host") not in self.server.hosts:
            self._send(403, CONTENT_TYPES[".txt"], b"This server only answers to localhost.\n")
            return
        path = urlsplit(self.path).path
        if path == "/api/project":
            self._json(200, api.project_view(load(self.server.root)))
        elif path.startswith("/api/items/") and path.count("/") == 3:
            try:
                self._json(200, api.item_extras(load(self.server.root), path.rsplit("/", 1)[1]))
            except api.ApiError as error:
                self._json(error.status, {"error": str(error)})
        elif path == "/api/events":
            self._events()
        elif path == "/api/server":
            self._json(200, {"app": "corkboard", "project": str(self.server.root.resolve())})
        elif path.startswith("/api/"):
            self._json(404, {"error": f"there's no {path}"})
        else:
            self._static(path)

    def do_POST(self) -> None:
        if self.headers.get("Host") not in self.server.hosts:
            self._json(403, {"error": "this server only answers to localhost"})
            return
        if self.headers.get("Origin") not in self.server.origins:
            self._json(403, {"error": "changes are only accepted from Corkboard's own page"})
            return
        if self.headers.get_content_type() != "application/json":
            self._json(415, {"error": "send changes as application/json"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if not 0 <= length <= MAX_BODY:
            self._json(413, {"error": f"a change can be at most {MAX_BODY} bytes"})
            return
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            self._json(400, {"error": "the body isn't valid JSON"})
            return
        if not isinstance(data, dict):
            self._json(400, {"error": "the body must be a JSON object"})
            return
        path = urlsplit(self.path).path
        with self.server.write_lock:
            try:
                answer = api.write(load(self.server.root), path, data, self.server.clock())
            except api.ApiError as error:
                self._json(error.status, {"error": str(error)})
            except EditError as error:
                self._json(400, {"error": str(error)})
            else:
                self._json(200, answer)

    def _events(self) -> None:
        """Send a `change` event whenever a file in .project/ changes, until the page goes away."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        self.end_headers()
        last = files_signature(self.server.root)
        quiet = 0.0
        try:
            self.wfile.write(b"retry: 1000\n\n")
            self.wfile.flush()
            while not self.server.stopping.wait(self.server.poll_seconds):
                current = files_signature(self.server.root)
                quiet += self.server.poll_seconds
                if current != last:
                    last = current
                    self.wfile.write(b"event: change\ndata: {}\n\n")
                elif quiet >= HEARTBEAT_SECONDS:
                    self.wfile.write(b": still here\n\n")
                else:
                    continue
                quiet = 0.0
                self.wfile.flush()
        except OSError:
            pass  # the page closed or reloaded

    def log_message(self, format: str, *args: object) -> None:
        pass  # a line per request would bury the URL in the terminal

    def _static(self, path: str) -> None:
        file = self._web_file(path) or self.server.web / "index.html"
        try:
            body = file.read_bytes()
        except OSError:
            self._send(404, CONTENT_TYPES[".txt"], b"The web app's files are missing.\n")
            return
        content_type = CONTENT_TYPES.get(file.suffix, "application/octet-stream")
        self._send(200, content_type, body)

    def _web_file(self, path: str) -> Path | None:
        """The file in web/ that a URL path names, or None. Never a file outside web/."""
        relative = unquote(path).lstrip("/")
        if not relative:
            return None
        try:
            file = (self.server.web / relative).resolve()
        except (OSError, ValueError):
            return None
        if file.is_relative_to(self.server.web) and file.is_file():
            return file
        return None

    def _json(self, status: int, data: object) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send(status, "application/json", body)

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)


def files_signature(root: Path) -> list[tuple[str, int, int]]:
    """Each file in .project/ with its modification time and size, to tell when any changed."""
    signature = []
    for path in root.rglob("*"):
        try:
            info = path.stat()
        except OSError:
            continue  # removed while we looked
        if path.is_file():
            signature.append((path.relative_to(root).as_posix(), info.st_mtime_ns, info.st_size))
    return sorted(signature)
