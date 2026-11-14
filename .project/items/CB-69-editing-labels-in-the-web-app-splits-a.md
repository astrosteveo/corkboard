---
id: CB-69
type: bug
title: Editing labels in the web app splits a label with a comma
status: todo
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [server, ui]
---
The API joins a JSON list of labels with commas and `parse_fields` splits them again, so removing `ui` from `labels: ["a, b", ui]` in the web app leaves `labels: [a, b]`.

## Subtasks
- [ ] A JSON list keeps its items as they are
- [ ] Tests

## Log
- 2026-11-13 20:04 claude: created
