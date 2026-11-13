---
id: CB-35
type: task
title: The releases view
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-7
blocked_by: [CB-27]
---
A tab for every release plus No release, and the release as a tree: its epics with progress bars, their tasks with status icons, subtasks under tasks, expand and collapse, the goal text, and status and date changed from the header. Cancelled items stay visible.

Done when the view shows the same items and progress as `corkboard tree` for every release in this repo.

## Subtasks
- [x] Release tabs, plus No release
- [x] The tree, with progress and status icons
- [x] Expand and collapse
- [x] Goal, status and date in the header
- [x] Check it in a browser

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-13 00:01 claude: moved to in-progress
- 2026-11-13 00:03 claude: done subtask: Release tabs, plus No release
- 2026-11-13 00:03 claude: done subtask: The tree, with progress and status icons
- 2026-11-13 00:03 claude: done subtask: Expand and collapse
- 2026-11-13 00:03 claude: done subtask: Goal, status and date in the header
- 2026-11-13 00:03 claude: done subtask: Check it in a browser
- 2026-11-13 00:03 claude: The tree uses corkboard tree's order: epics by number, each one's tasks by status (done, in-progress, waiting, todo, backlog, cancelled), then number; cancelled items stay. Epics start open, subtask lists closed. The header's status and date go through POST /api/releases/<name>, so a second active release is refused with the CLI's message. Checked in Chromium: for every release in this repo and the demo, the view's progress, epics, statuses and subtask counts equal corkboard tree's, row for row.
- 2026-11-13 00:03 claude: moved to done
