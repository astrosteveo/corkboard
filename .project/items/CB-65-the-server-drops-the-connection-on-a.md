---
id: CB-65
type: bug
title: The server drops the connection on a failed write or a non-UTF-8 file name
status: done
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [server]
---
A write that fails with an OSError (a read-only folder, a full disk) closes the connection without an answer, so the page says "Failed to fetch". And one file name that isn't UTF-8 makes `/api/project` and `/api/docs` answer nothing, so the whole app fails to load.

## Subtasks
- [x] A failed write answers with the reason
- [x] JSON answers encode any file name
- [x] Tests

## Log
- 2026-11-13 20:04 claude: created
- 2026-11-13 20:26 claude: moved to in-progress
- 2026-11-13 20:26 claude: done subtask: A failed write answers with the reason
- 2026-11-13 20:26 claude: done subtask: JSON answers encode any file name
- 2026-11-13 20:26 claude: done subtask: Tests
- 2026-11-13 20:26 claude: A non-UTF-8 name goes out with ? in place of the bad byte: the app loads, and that doc's page says it isn't there until it's renamed
- 2026-11-13 20:26 claude: moved to done
