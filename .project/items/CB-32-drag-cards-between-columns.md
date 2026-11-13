---
id: CB-32
type: task
title: Drag cards between columns
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-6
blocked_by: [CB-25, CB-30]
---
Dragging a card to another column changes its status, the same as `corkboard move`. Dropping on Waiting asks for a message first, and a card goes back where it was if the save fails.

Done when a drag in the browser moves the item on disk, and a failed save puts the card back.

## Subtasks
- [x] Drag and drop between columns
- [x] Ask for a message when dropping on Waiting
- [x] Put the card back if the save fails

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-12 23:53 claude: moved to in-progress
- 2026-11-12 23:54 claude: done subtask: Drag and drop between columns
- 2026-11-12 23:54 claude: done subtask: Ask for a message when dropping on Waiting
- 2026-11-12 23:54 claude: done subtask: Put the card back if the save fails
- 2026-11-12 23:54 claude: HTML5 drag and drop with a private data type, so only Corkboard cards drop on columns. A dropped card shows in its new column at once and goes back, with the server's error, if the save fails. A drop on Waiting opens a native <dialog> for the message; Esc cancels. Checked in Chromium: drags saved to disk, Esc on the dialog changed nothing, and a forced 500 put the card back in Todo with the file unchanged.
- 2026-11-12 23:54 claude: moved to done
