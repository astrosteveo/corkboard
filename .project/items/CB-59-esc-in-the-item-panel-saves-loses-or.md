---
id: CB-59
type: bug
title: Esc in the item panel saves, loses or closes the wrong thing
status: done
priority: medium
owner: claude
created: 2026-11-13
parent: CB-53
labels: [ui]
---
Three Esc bugs, each shown in headless Chromium:
- Esc in the title field saves the typed title (renames the file and logs it) instead of putting the old one back.
- Esc while the description editor shows Preview, Save or the conflict view closes the panel and loses the draft.
- Esc in the New item form also closes the item panel under it.

## Subtasks
- [x] Esc in the title puts the old title back and writes nothing
- [x] Esc keeps the panel open while the description has unsaved changes
- [x] Esc in the New item form closes only the form
- [x] Checked in a browser

## Log
- 2026-11-13 20:04 claude: created
- 2026-11-13 20:16 claude: moved to in-progress
- 2026-11-13 20:17 claude: done subtask: Esc in the title puts the old title back and writes nothing
- 2026-11-13 20:17 claude: done subtask: Esc keeps the panel open while the description has unsaved changes
- 2026-11-13 20:17 claude: done subtask: Esc in the New item form closes only the form
- 2026-11-13 20:17 claude: done subtask: Checked in a browser
- 2026-11-13 20:17 claude: Checked in headless Chromium: the three repros pass, and plain Esc still closes the panel, an unchanged editor and the form
- 2026-11-13 20:17 claude: moved to done
