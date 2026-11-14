---
id: CB-60
type: bug
title: The item panel keeps another item's unsent text and steals focus
status: done
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [ui]
---
When the panel switches to another item, an unsent note, label, subtask or waiting message stays in its box, and Enter sends it to the new item. And while the waiting prompt is open, every re-render (a live update, the pulls poll) moves focus back into it.

## Subtasks
- [x] Reset the panel's unsent text when the item changes
- [x] Focus the waiting message once, not on every render
- [x] Checked in a browser

## Log
- 2026-11-13 20:04 claude: created
- 2026-11-13 20:18 claude: moved to in-progress
- 2026-11-13 20:19 claude: done subtask: Reset the panel's unsent text when the item changes
- 2026-11-13 20:19 claude: done subtask: Focus the waiting message once, not on every render
- 2026-11-13 20:19 claude: done subtask: Checked in a browser
- 2026-11-13 20:19 claude: Keyed ItemView by item ID instead of resetting each box; dropped the three per-item resets that made redundant
- 2026-11-13 20:19 claude: moved to done
