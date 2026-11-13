---
id: CB-29
type: task
title: The Now page
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-5
blocked_by: [CB-25, CB-26, CB-27]
---
The home page from `.project/docs/ui.md`: the release line with progress, Waiting on you with Send and Mark done, In progress, Next up, and Since you last looked with Mark seen. The time of the last Mark seen is kept in the browser. Merged, not done waits for GitHub support in v0.3.

Done when, for a project like the example in cli.md, the page shows what `corkboard now` shows, and a reply sent from the page puts the item first in `corkboard next`, marked answered.

## Subtasks
- [x] The release line and its progress
- [x] Waiting on you, with Send and Mark done
- [x] In progress and Next up
- [x] Since you last looked, with Mark seen
- [x] Check it in a browser

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-12 23:45 claude: moved to in-progress
- 2026-11-12 23:46 claude: done subtask: The release line and its progress
- 2026-11-12 23:46 claude: done subtask: Waiting on you, with Send and Mark done
- 2026-11-12 23:46 claude: done subtask: In progress and Next up
- 2026-11-12 23:46 claude: done subtask: Since you last looked, with Mark seen
- 2026-11-12 23:46 claude: done subtask: Check it in a browser
- 2026-11-12 23:46 claude: The Mark seen time is in localStorage, keyed by the .project/ folder's path (now in /api/project as root), since several repos can use the same port over time. Log stamps are minute-precise, so a line Claude writes in the same minute you click Mark seen counts as seen. Checked in Chromium on a demo like cli.md's example: the sections match corkboard now, a reply sent from the page made corkboard next pick that item, answered by you, and Mark seen survives a reload.
- 2026-11-12 23:46 claude: moved to done
