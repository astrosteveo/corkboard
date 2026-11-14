---
id: CB-57
type: bug
title: set crashes without a title and can delete required fields
status: done
priority: medium
owner: claude
created: 2026-11-13
parent: CB-53
labels: [cli]
---
`corkboard set` on an item whose file has no `title:` line crashes with `KeyError: 'title'`, in the CLI and in the web server. And `set EX-9 priority=` (also `owner=`, `type=`) deletes a required field and exits 0, though `title=` is refused.

## Subtasks
- [x] set works on an item with no title line
- [x] Refuse an empty value for a required field
- [x] Tests

## Log
- 2026-11-13 20:04 claude: created
- 2026-11-13 20:13 claude: moved to in-progress
- 2026-11-13 20:14 claude: done subtask: set works on an item with no title line
- 2026-11-13 20:14 claude: done subtask: Refuse an empty value for a required field
- 2026-11-13 20:14 claude: done subtask: Tests
- 2026-11-13 20:14 claude: moved to done
