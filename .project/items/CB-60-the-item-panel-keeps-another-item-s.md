---
id: CB-60
type: bug
title: The item panel keeps another item's unsent text and steals focus
status: todo
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [ui]
---
When the panel switches to another item, an unsent note, label, subtask or waiting message stays in its box, and Enter sends it to the new item. And while the waiting prompt is open, every re-render (a live update, the pulls poll) moves focus back into it.

## Subtasks
- [ ] Reset the panel's unsent text when the item changes
- [ ] Focus the waiting message once, not on every render
- [ ] Checked in a browser

## Log
- 2026-11-13 20:04 claude: created
