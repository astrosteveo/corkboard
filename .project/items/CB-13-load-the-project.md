---
id: CB-13
type: task
title: Load the project
status: done
priority: high
owner: claude
created: 2026-11-12
parent: CB-1
blocked_by: [CB-12]
---
Load `config.yml`, releases and items into the core library: each body split into description, subtasks and log, defaults for optional fields, each item's release (its own or its epic's), links seen from both sides, whether an item is blocked, and epic and release progress.

Done when tests load this repo's own `.project/` and get each of those right.

## Subtasks
- [x] Find `.project/` by walking up from the current folder
- [x] Config, releases and items, with defaults
- [x] Description, subtasks and log from the body
- [x] Release, both sides of links, blocked and progress

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 21:38 claude: moved to in-progress
- 2026-11-12 21:41 claude: done subtask: Find `.project/` by walking up from the current folder
- 2026-11-12 21:41 claude: done subtask: Config, releases and items, with defaults
- 2026-11-12 21:41 claude: done subtask: Description, subtasks and log from the body
- 2026-11-12 21:41 claude: done subtask: Release, both sides of links, blocked and progress
- 2026-11-12 21:41 claude: Items keep their header fields and body exactly as the file has them, and the description, subtasks and log are read from the body. That lets CB-15's writes change one line and leave the rest of the file alone. A blocked_by ID with no item counts as open, so a dangling blocker keeps the item blocked until check reports it.
- 2026-11-12 21:41 claude: moved to done
