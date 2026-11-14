---
id: CB-47
type: task
title: The List view
status: in-progress
priority: medium
owner: claude
created: 2026-11-13
parent: CB-9
---
The List screen at `/list`: every item in a table, filtered the way `corkboard list` filters, starting with backlog and todo, for sorting through the backlog.

Done when: the filters and sort order are kept in the URL, status and priority can be changed in the row, and clicking a row opens the item panel.

## Subtasks
- [x] Route and sidebar entry
- [x] Filters: status, type, label, release
- [x] Sort by clicking a column header
- [x] Change status and priority in the row

## Log
- 2026-11-13 16:32 claude: created
- 2026-11-13 18:30 claude: moved to in-progress
- 2026-11-13 18:35 claude: done subtask: Route and sidebar entry
- 2026-11-13 18:35 claude: done subtask: Filters: status, type, label, release
- 2026-11-13 18:35 claude: done subtask: Sort by clicking a column header
- 2026-11-13 18:35 claude: done subtask: Change status and priority in the row
- 2026-11-13 18:35 claude: Status filter is six toggle buttons with counts, not a dropdown: one click per status and no popover to close. Sort is sort=<column> in the URL, or sort=-<column> for the other way; no sort= means by number. Reused the board's AskDialog for Waiting.
