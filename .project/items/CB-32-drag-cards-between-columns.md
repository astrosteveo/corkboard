---
id: CB-32
type: task
title: Drag cards between columns
status: todo
priority: medium
owner: claude
created: 2026-11-12
parent: CB-6
blocked_by: [CB-25, CB-30]
---
Dragging a card to another column changes its status, the same as `corkboard move`. Dropping on Waiting asks for a message first, and a card goes back where it was if the save fails.

Done when a drag in the browser moves the item on disk, and a failed save puts the card back.

## Subtasks
- [ ] Drag and drop between columns
- [ ] Ask for a message when dropping on Waiting
- [ ] Put the card back if the save fails

## Log
- 2026-11-12 22:45 claude: created
