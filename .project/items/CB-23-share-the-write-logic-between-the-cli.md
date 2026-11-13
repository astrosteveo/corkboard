---
id: CB-23
type: task
title: Share the write logic between the CLI and the server
status: in-progress
priority: high
owner: claude
created: 2026-11-12
parent: CB-4
---
Move the logic behind `move`, `set`, `sub`, `log`, `new` and `release` out of the CLI commands into functions the web server can call too. Given the project, the item and the change, each one writes the file and returns what the CLI prints today: the result line and any warnings. The CLI commands become thin wrappers around them.

Done when every existing test passes unchanged, and the new functions have tests of their own.

## Subtasks
- [x] Functions for move, set, sub, log, new and release that return their result and warnings
- [x] The CLI commands call them
- [ ] Tests for the functions

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-12 23:05 claude: moved to in-progress
- 2026-11-12 23:11 claude: done subtask: Functions for move, set, sub, log, new and release that return their result and warnings
- 2026-11-12 23:11 claude: done subtask: The CLI commands call them
- 2026-11-12 23:11 claude: Shared functions live in corkboard/edits.py, which never imports cli. They take the Item, not its ID, so the server can answer 404 for a missing item itself. Values come in as typed after field=, so all field rules run in edits.py.
