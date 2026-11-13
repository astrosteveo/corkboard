---
id: CB-51
type: task
title: Refuse blocking cycles in corkboard set
status: done
priority: low
owner: claude
created: 2026-11-13
parent: CB-10
labels: [cli]
---
`corkboard set` and the item panel's + Add link accept a `blocked_by` that makes a chain back to the item itself, such as EX-2 blocked by EX-3 while EX-3 is blocked by EX-2. Only `corkboard check` reports it afterwards. Refuse it when the link is made, with the chain in the message.

## Subtasks
- [x] Refuse a cycle in corkboard set, searching from the blockers it adds
- [x] Tests through the CLI and the API

## Log
- 2026-11-13 17:12 claude: created
- 2026-11-13 17:27 claude: moved to in-progress
- 2026-11-13 17:28 claude: done subtask: Refuse a cycle in corkboard set, searching from the blockers it adds
- 2026-11-13 17:28 claude: done subtask: Tests through the CLI and the API
- 2026-11-13 17:28 claude: The search runs in set_, not rules.field_problems: check runs field_problems on every item, so a cycle there would be reported once per item on top of check's own cycle finding. It searches only from the blockers the change adds, so a cycle already in the files doesn't block other edits.
- 2026-11-13 17:28 claude: moved to done
