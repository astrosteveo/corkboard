---
id: CB-61
type: bug
title: new and describe write bodies whose log or subtasks can't be read
status: todo
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [cli]
---
`new` accepts bodies that `check` then reports (an epic with `## Subtasks`, a subtask line with no box), though cli.md says it checks the way `check` does. A code fence left open in a new body or a description hides `## Subtasks` and `## Log`. And a line that starts with inline triple backticks is taken for a fence, which hides the log too.

## Subtasks
- [ ] new checks the body the way check does
- [ ] new and describe refuse a code fence left open
- [ ] Code fences follow CommonMark: an info string has no backticks, and a fence closes only with its own kind
- [ ] Tests

## Log
- 2026-11-13 20:04 claude: created
