---
id: CB-62
type: bug
title: check passes lowercase link IDs and misreports list values
status: done
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [cli]
---
`check` looks up `parent` and link IDs case-insensitively, but the loader matches them exactly, so a hand-written `blocked_by: [ex-1]` passes check and blocks the item forever. And a single-value field written as a list, such as `status: [todo]`, gets the message `"todo" isn't a status`.

## Subtasks
- [x] check reports an ID that isn't written exactly
- [x] check says a single value is written as a list
- [x] Tests

## Log
- 2026-11-13 20:04 claude: created
- 2026-11-13 20:22 claude: moved to in-progress
- 2026-11-13 20:23 claude: done subtask: check reports an ID that isn't written exactly
- 2026-11-13 20:23 claude: done subtask: check says a single value is written as a list
- 2026-11-13 20:23 claude: done subtask: Tests
- 2026-11-13 20:23 claude: moved to done
