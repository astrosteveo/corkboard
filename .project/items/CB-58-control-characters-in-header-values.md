---
id: CB-58
type: bug
title: Control characters in header values crash check, and some reach the file
status: done
priority: medium
owner: claude
created: 2026-11-13
parent: CB-53
labels: [cli]
---
`header.read` accepts a tab or other control character inside a value, then `header.write` refuses it, so `corkboard check` crashes with a `ValueError` traceback on the file it should report. And `write` lets through `\x85`, the other C1 controls, U+2028 and U+2029, which YAML reads as line breaks or refuses, so GitHub can't render the header.

## Subtasks
- [x] read reports a control character with its line number
- [x] write refuses C1 controls, U+2028 and U+2029
- [x] Tests

## Log
- 2026-11-13 20:04 claude: created
- 2026-11-13 20:14 claude: moved to in-progress
- 2026-11-13 20:15 claude: done subtask: read reports a control character with its line number
- 2026-11-13 20:15 claude: done subtask: write refuses C1 controls, U+2028 and U+2029
- 2026-11-13 20:15 claude: done subtask: Tests
- 2026-11-13 20:15 claude: moved to done
