---
id: CB-31
type: task
title: The item panel
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-6
blocked_by: [CB-25, CB-27]
---
One item in a side panel over the screen you came from, or as a full page at `/items/<ID>`: header fields changed in place, the description rendered as Markdown, subtasks ticked and added, the activity log with Add a note, and Mentioned in. Links and the Development section come with v0.3.

Done when every change made in the panel makes the same file change as its CLI command.

## Subtasks
- [x] The side panel and the full page
- [x] Header fields changed in place
- [x] Subtasks ticked, unticked and added
- [x] Activity and Add a note
- [x] Mentioned in

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-12 23:49 claude: moved to in-progress
- 2026-11-12 23:52 claude: done subtask: The side panel and the full page
- 2026-11-12 23:52 claude: done subtask: Header fields changed in place
- 2026-11-12 23:52 claude: done subtask: Subtasks ticked, unticked and added
- 2026-11-12 23:52 claude: done subtask: Activity and Add a note
- 2026-11-12 23:52 claude: done subtask: Mentioned in
- 2026-11-12 23:52 claude: The panel opens from any screen with ?item=<ID> in the URL, so Back closes it and it can be linked; /items/<ID> stays the full page. Mentioned in comes from GET /api/items/<ID>, so docs are only scanned for the item you open. While a change saves, its select or checkbox keeps the new value instead of flicking back. Checked in Chromium: 11 edits made in the panel (fields, labels, subtasks, a note, status, title, waiting with a question) left .project/ the same as the same corkboard commands run on a copy, apart from log times.
- 2026-11-12 23:52 claude: moved to done
