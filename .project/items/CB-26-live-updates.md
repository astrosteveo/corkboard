---
id: CB-26
type: task
title: Live updates
status: todo
priority: high
owner: claude
created: 2026-11-12
parent: CB-4
blocked_by: [CB-24]
---
The server checks `.project/` for changed files every second and pushes an event to the page, with server-sent events, so the screen updates without a reload when Claude changes something.

Done when a test changes an item file and receives the event within 2 seconds.

## Subtasks
- [ ] Check file modification times every second
- [ ] An endpoint for server-sent events
- [ ] A test with a real file change

## Log
- 2026-11-12 22:45 claude: created
