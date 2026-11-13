---
id: CB-30
type: task
title: The board
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-6
blocked_by: [CB-27]
---
Status columns for one release, the active one by default, with Epic, Label and Owner filters, Group by epic, Backlog and Cancelled hidden until shown, and cards as `.project/docs/ui.md` describes, including the dot for changes since you last looked. PR badges come with v0.3.

Done when this repo's board shows the same items and statuses as `corkboard tree`.

## Subtasks
- [x] Columns and cards
- [x] Release, epic, label and owner filters
- [x] Group by epic
- [x] Show backlog and cancelled
- [x] Check it in a browser

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-12 23:47 claude: moved to in-progress
- 2026-11-12 23:49 claude: done subtask: Columns and cards
- 2026-11-12 23:49 claude: done subtask: Release, epic, label and owner filters
- 2026-11-12 23:49 claude: done subtask: Group by epic
- 2026-11-12 23:49 claude: done subtask: Show backlog and cancelled
- 2026-11-12 23:49 claude: done subtask: Check it in a browser
- 2026-11-12 23:49 claude: Filters, Group by epic, Show backlog and Show more done live in the URL query (?release=v0.1&epic=EX-3&group=1&hidden=1&done=all), so reloads and live updates keep them and a view can be linked. Done shows its first 5 with Show more, as the mockup did. Checked in Chromium: for every release in this repo, the board's items and columns equal corkboard tree's.
- 2026-11-12 23:49 claude: moved to done
