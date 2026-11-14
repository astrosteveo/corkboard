---
id: CB-65
type: bug
title: The server drops the connection on a failed write or a non-UTF-8 file name
status: todo
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [server]
---
A write that fails with an OSError (a read-only folder, a full disk) closes the connection without an answer, so the page says "Failed to fetch". And one file name that isn't UTF-8 makes `/api/project` and `/api/docs` answer nothing, so the whole app fails to load.

## Subtasks
- [ ] A failed write answers with the reason
- [ ] JSON answers encode any file name
- [ ] Tests

## Log
- 2026-11-13 20:04 claude: created
