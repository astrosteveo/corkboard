---
id: CB-13
type: task
title: Load the project
status: todo
priority: high
owner: claude
created: 2026-11-12
parent: CB-1
blocked_by: [CB-12]
---
Load `config.yml`, releases and items into the core library: each body split into description, subtasks and log, defaults for optional fields, each item's release (its own or its epic's), links seen from both sides, whether an item is blocked, and epic and release progress.

Done when tests load this repo's own `.project/` and get each of those right.

## Subtasks
- [ ] Find `.project/` by walking up from the current folder
- [ ] Config, releases and items, with defaults
- [ ] Description, subtasks and log from the body
- [ ] Release, both sides of links, blocked and progress

## Log
- 2026-11-12 21:21 claude: created
