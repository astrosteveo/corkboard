---
id: CB-25
type: task
title: The write API, with the safety rules
status: todo
priority: high
owner: claude
created: 2026-11-12
parent: CB-4
blocked_by: [CB-23, CB-24]
---
Write endpoints for move, set, sub, log, new and release, using the shared functions from CB-23 and logged as `me`. The server listens on 127.0.0.1 only, and refuses any write whose Origin or Host isn't the app's own page, so a page on another site, or a doc in a cloned repo, can't change files.

Done when tests show each write makes the same file change as its CLI command, and that writes from another origin or host are refused.

## Subtasks
- [ ] Endpoints for move, set, sub, log, new and release
- [ ] Writes logged as me
- [ ] Refuse writes from other origins and hosts
- [ ] Tests comparing each write with its CLI command

## Log
- 2026-11-12 22:45 claude: created
