---
id: CB-34
type: task
title: The new item form
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-6
blocked_by: [CB-31]
---
Opened with + New or the c key: type, title, epic, priority, owner, labels and an optional description. It creates the item the way `corkboard new` does, then opens it in the side panel.

Done when an item made in the form matches one made with `corkboard new` from the same values.

## Subtasks
- [x] The form and the c key
- [x] Create through the write API
- [x] Open the new item in the panel

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-12 23:58 claude: moved to in-progress
- 2026-11-13 00:01 claude: done subtask: The form and the c key
- 2026-11-13 00:01 claude: done subtask: Create through the write API
- 2026-11-13 00:01 claude: done subtask: Open the new item in the panel
- 2026-11-13 00:01 claude: A native <dialog>, opened by + New item on the board, the sidebar's New item button, or c anywhere outside a text field. Added a Release field when there's no epic, so a task made from the board lands on it; ui.md says so. Labels and selects use <label for> pairs, since a label wrapped around a select also takes the options' text into its name. Checked in Chromium: a bug with epic, labels and a subtask, and a task with only a release, came out byte for byte like corkboard new, and each opened in the panel.
- 2026-11-13 00:01 claude: moved to done
