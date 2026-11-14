---
id: CB-67
type: bug
title: list ignores repeated filters, and show hides missing related links
status: todo
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [cli]
---
`corkboard list labels=ui labels=board` applies only the last filter, though cli.md says several filters must all match. And `corkboard show` leaves out a `related` link to an item that doesn't exist, while it shows `(no such item)` for `blocked by` and `duplicate of`.

## Subtasks
- [ ] Repeated filters must all match
- [ ] show prints a missing related item as (no such item)
- [ ] Tests

## Log
- 2026-11-13 20:04 claude: created
