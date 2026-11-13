---
id: CB-23
type: task
title: Share the write logic between the CLI and the server
status: todo
priority: high
owner: claude
created: 2026-11-12
parent: CB-4
---
Move the logic behind `move`, `set`, `sub`, `log`, `new` and `release` out of the CLI commands into functions the web server can call too. Given the project, the item and the change, each one writes the file and returns what the CLI prints today: the result line and any warnings. The CLI commands become thin wrappers around them.

Done when every existing test passes unchanged, and the new functions have tests of their own.

## Subtasks
- [ ] Functions for move, set, sub, log, new and release that return their result and warnings
- [ ] The CLI commands call them
- [ ] Tests for the functions

## Log
- 2026-11-12 22:45 claude: created
