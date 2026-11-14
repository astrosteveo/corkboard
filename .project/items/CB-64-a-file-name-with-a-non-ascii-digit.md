---
id: CB-64
type: bug
title: A file name with a non-ASCII digit crashes the load
status: todo
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [cli]
---
`natural_key` calls `int()` on any part `str.isdigit()` accepts, so a file named `²1.md` in items/ makes `project.load` raise `ValueError`, and every command fails. A doc named `１.md` (a full-width digit) breaks `/api/docs` and search the same way.

## Subtasks
- [ ] Sort keys use ASCII digits only
- [ ] Tests

## Log
- 2026-11-13 20:04 claude: created
