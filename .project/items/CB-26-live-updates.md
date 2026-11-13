---
id: CB-26
type: task
title: Live updates
status: done
priority: high
owner: claude
created: 2026-11-12
parent: CB-4
blocked_by: [CB-24]
---
The server checks `.project/` for changed files every second and pushes an event to the page, with server-sent events, so the screen updates without a reload when Claude changes something.

Done when a test changes an item file and receives the event within 2 seconds.

## Subtasks
- [x] Check file modification times every second
- [x] An endpoint for server-sent events
- [x] A test with a real file change

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-12 23:42 claude: moved to in-progress
- 2026-11-12 23:44 claude: done subtask: Check file modification times every second
- 2026-11-12 23:44 claude: done subtask: An endpoint for server-sent events
- 2026-11-12 23:44 claude: done subtask: A test with a real file change
- 2026-11-12 23:44 claude: Each /api/events stream polls file mtimes and sizes in .project/ itself, every second; no shared watcher thread, so nothing runs when no page is open. A comment line every 15 s notices closed tabs, and closing the server ends every stream. The page refetches /api/project on each change and on reconnect. Checked in Chromium: a corkboard log by Claude showed on the open item page in 0.8 s.
- 2026-11-12 23:44 claude: moved to done
