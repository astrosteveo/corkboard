---
id: CB-25
type: task
title: The write API, with the safety rules
status: done
priority: high
owner: claude
created: 2026-11-12
parent: CB-4
blocked_by: [CB-23, CB-24]
---
Write endpoints for move, set, sub, log, new and release, using the shared functions from CB-23 and logged as `me`. The server listens on 127.0.0.1 only, and refuses any write whose Origin or Host isn't the app's own page, so a page on another site, or a doc in a cloned repo, can't change files.

Done when tests show each write makes the same file change as its CLI command, and that writes from another origin or host are refused.

## Subtasks
- [x] Endpoints for move, set, sub, log, new and release
- [x] Writes logged as me
- [x] Refuse writes from other origins and hosts
- [x] Tests comparing each write with its CLI command

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-12 23:25 claude: CB-24 already refuses any request, read or write, whose Host isn't localhost:<port> or 127.0.0.1:<port>. What's left here is the Origin check on writes.
- 2026-11-12 23:39 claude: moved to in-progress
- 2026-11-12 23:41 claude: done subtask: Endpoints for move, set, sub, log, new and release
- 2026-11-12 23:41 claude: done subtask: Writes logged as me
- 2026-11-12 23:41 claude: done subtask: Refuse writes from other origins and hosts
- 2026-11-12 23:41 claude: done subtask: Tests comparing each write with its CLI command
- 2026-11-12 23:41 claude: POST /api/items, /api/items/<ID>/{move,set,sub,log} and /api/releases/<name> call edits.py under one lock, logged as me. A write needs Origin http://localhost:<port> or http://127.0.0.1:<port> and Content-Type application/json, so a cross-site form or a no-cors fetch can't send one. edits.Result now carries the new item's ID. Checked in Chromium: the page's own fetch writes, and fetches from about:blank or the other host name are blocked.
- 2026-11-12 23:41 claude: moved to done
