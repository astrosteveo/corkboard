---
id: CB-24
type: task
title: "corkboard ui: the local server and the read API"
status: todo
priority: high
owner: claude
created: 2026-11-12
parent: CB-4
---
`corkboard ui` starts a server, using Python's standard library, on 127.0.0.1:4747 or the next free port, prints `Corkboard: http://localhost:<port>`, and runs until Ctrl-C. It serves `web/` and a read API: one view of the project with everything the pages show (releases, items with their release, blocked state, subtasks and log, the order of work, waiting messages and answered items), computed by the same code as the CLI. If a server for this repo is already running, it prints that URL and exits.

Done when `corkboard ui` on this repo prints the URL, and tests start a real server on a free port and read the API.

## Subtasks
- [ ] The ui command, choosing a port, and stopping on Ctrl-C
- [ ] Serving web/
- [ ] The read API, built from the core library
- [ ] Finding a server already running for this repo
- [ ] Tests against a real server

## Log
- 2026-11-12 22:45 claude: created
