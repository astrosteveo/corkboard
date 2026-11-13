---
id: CB-51
type: task
title: Refuse blocking cycles in corkboard set
status: backlog
priority: low
owner: claude
created: 2026-11-13
parent: CB-10
labels: [cli]
---
`corkboard set` and the item panel's + Add link accept a `blocked_by` that makes a chain back to the item itself, such as EX-2 blocked by EX-3 while EX-3 is blocked by EX-2. Only `corkboard check` reports it afterwards. Refuse it when the link is made, with the chain in the message.

## Subtasks
- [ ] Check for a cycle in rules.field_problems, sharing check.py's chain search
- [ ] Tests through the CLI and the API

## Log
- 2026-11-13 17:12 claude: created
