---
id: CB-55
type: bug
title: check --fix can write outside .project/items/
status: done
priority: high
owner: claude
created: 2026-11-13
parent: CB-53
labels: [cli, security]
---
`check --fix` builds the rename path from the raw `id`, so an item with `id: ../../EX-1` is moved out of `.project/items/` and `check` then says ok. Renumbering a duplicate also uses the config's prefix after reporting it invalid: with no prefix, the duplicate becomes `-1`.

## Subtasks
- [x] Rename only to a valid ID, inside items/
- [x] Renumber only with a valid prefix
- [x] Tests

## Log
- 2026-11-13 20:04 claude: created
- 2026-11-13 20:09 claude: moved to in-progress
- 2026-11-13 20:10 claude: done subtask: Rename only to a valid ID, inside items/
- 2026-11-13 20:10 claude: done subtask: Renumber only with a valid prefix
- 2026-11-13 20:10 claude: done subtask: Tests
- 2026-11-13 20:10 claude: item_path now refuses anything that isn't an ID, so set can't rename such an item out of items/ either (the web app's title field reached it)
- 2026-11-13 20:10 claude: moved to done
