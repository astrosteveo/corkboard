---
id: CB-64
type: bug
title: A file name with a non-ASCII digit crashes the load
status: done
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [cli]
---
`natural_key` calls `int()` on any part `str.isdigit()` accepts, so a file named `²1.md` in items/ makes `project.load` raise `ValueError`, and every command fails. A doc named `１.md` (a full-width digit) breaks `/api/docs` and search the same way.

## Subtasks
- [x] Sort keys use ASCII digits only
- [x] Tests
- [x] Releases sort by name without .md, so v0.3 comes before v0.3.1

## Log
- 2026-11-13 20:04 claude: created
- 2026-11-13 20:06 claude: moved to in-progress
- 2026-11-13 20:06 claude: added subtask: Releases sort by name without .md, so v0.3 comes before v0.3.1
- 2026-11-13 20:07 claude: done subtask: Sort keys use ASCII digits only
- 2026-11-13 20:07 claude: done subtask: Tests
- 2026-11-13 20:07 claude: done subtask: Releases sort by name without .md, so v0.3 comes before v0.3.1
- 2026-11-13 20:07 claude: Found while fixing CB-54: the new v0.3.1 release sorted before v0.3 and failed ThisRepoTest on main, so this went first
- 2026-11-13 20:07 claude: moved to done
