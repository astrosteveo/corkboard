---
id: CB-50
type: task
title: Remove a link in the item panel
status: done
priority: low
owner: claude
created: 2026-11-13
parent: CB-10
labels: [ui]
---
The item panel's Links section (CB-42) can add links but not remove them, so a link added by mistake has to be removed with `corkboard set`. Add a × on each link row. A link shown on this item may be stored on the other item (Blocks, Duplicated by, or Related to from the other side), so removing it changes that item's file.

## Subtasks
- [x] × on each link row, writing whichever item stores the link
- [x] Spec in ui.md and a test through the API

## Log
- 2026-11-13 17:12 claude: created
- 2026-11-13 17:25 claude: moved to in-progress
- 2026-11-13 17:26 claude: done subtask: × on each link row, writing whichever item stores the link
- 2026-11-13 17:26 claude: done subtask: Spec in ui.md and a test through the API
- 2026-11-13 17:26 claude: moved to done
