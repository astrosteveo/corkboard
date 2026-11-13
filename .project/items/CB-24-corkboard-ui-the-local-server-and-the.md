---
id: CB-24
type: task
title: "corkboard ui: the local server and the read API"
status: done
priority: high
owner: claude
created: 2026-11-12
parent: CB-4
---
`corkboard ui` starts a server, using Python's standard library, on 127.0.0.1:4747 or the next free port, prints `Corkboard: http://localhost:<port>`, and runs until Ctrl-C. It serves `web/` and a read API: one view of the project with everything the pages show (releases, items with their release, blocked state, subtasks and log, the order of work, waiting messages and answered items), computed by the same code as the CLI. If a server for this repo is already running, it prints that URL and exits.

Done when `corkboard ui` on this repo prints the URL, and tests start a real server on a free port and read the API.

## Subtasks
- [x] The ui command, choosing a port, and stopping on Ctrl-C
- [x] Serving web/
- [x] The read API, built from the core library
- [x] Finding a server already running for this repo
- [x] Tests against a real server

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-12 23:16 claude: moved to in-progress
- 2026-11-12 23:25 claude: done subtask: The ui command, choosing a port, and stopping on Ctrl-C
- 2026-11-12 23:25 claude: done subtask: Serving web/
- 2026-11-12 23:25 claude: done subtask: The read API, built from the core library
- 2026-11-12 23:25 claude: done subtask: Finding a server already running for this repo
- 2026-11-12 23:25 claude: done subtask: Tests against a real server
- 2026-11-12 23:25 claude: The web app lives in corkboard/web/, inside the package, so the uv tool install copy has it (package-data in pyproject.toml, checked in CI). plugin.md updated.
- 2026-11-12 23:25 claude: Every request is refused unless its Host is localhost:<port> or 127.0.0.1:<port>, so DNS rebinding can't read the project. A running server is found by probing 4747-4766 at /api/server, with no port file.
- 2026-11-12 23:25 claude: moved to done
