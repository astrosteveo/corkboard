---
id: CB-33
type: task
title: Edit descriptions, with a conflict check
status: todo
priority: medium
owner: claude
created: 2026-11-12
parent: CB-6
blocked_by: [CB-31]
---
Edit turns an item's description into a Markdown text box with a preview. If the description changed on disk while you were editing, saving shows both versions and lets you choose instead of overwriting. Changes elsewhere in the file, such as a new log line from Claude, are kept without asking.

Done when a test that changes the description mid-edit gets both versions back, and one that only adds a log line saves cleanly.

## Subtasks
- [ ] A text box with a preview
- [ ] Saving checks whether the description changed on disk
- [ ] Show both versions on a conflict

## Log
- 2026-11-12 22:45 claude: created
