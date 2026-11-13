---
id: CB-19
type: task
title: tree, list, set, release
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-2
blocked_by: [CB-15]
---
The rest of the reading and writing commands from `.project/docs/cli.md`: `tree`, `list` with its filters, `set` (renaming the file when the title changes), and `release`.

Done when output tests for each command match `cli.md`, and `corkboard tree` on this repo shows v0.1.

## Subtasks
- [x] `tree`
- [x] `list` and its filters
- [x] `set`, with file renames
- [x] `release`, with one active release at a time

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 22:04 claude: moved to in-progress
- 2026-11-12 22:08 claude: done subtask: `tree`
- 2026-11-12 22:08 claude: done subtask: `list` and its filters
- 2026-11-12 22:08 claude: done subtask: `set`, with file renames
- 2026-11-12 22:08 claude: done subtask: `release`, with one active release at a time
- 2026-11-12 22:08 claude: set reports only the problems a change makes, not ones the item already had, so a stale link elsewhere in the header doesn't block an unrelated change. A new title writes the renamed file first, then removes the old one. tree none shows items with no release.
- 2026-11-12 22:08 claude: moved to done
