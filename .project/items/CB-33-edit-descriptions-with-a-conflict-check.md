---
id: CB-33
type: task
title: Edit descriptions, with a conflict check
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-6
blocked_by: [CB-31]
---
Edit turns an item's description into a Markdown text box with a preview. If the description changed on disk while you were editing, saving shows both versions and lets you choose instead of overwriting. Changes elsewhere in the file, such as a new log line from Claude, are kept without asking.

Done when a test that changes the description mid-edit gets both versions back, and one that only adds a log line saves cleanly.

## Subtasks
- [x] A text box with a preview
- [x] Saving checks whether the description changed on disk
- [x] Show both versions on a conflict

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-12 23:55 claude: moved to in-progress
- 2026-11-12 23:57 claude: done subtask: A text box with a preview
- 2026-11-12 23:57 claude: done subtask: Saving checks whether the description changed on disk
- 2026-11-12 23:57 claude: done subtask: Show both versions on a conflict
- 2026-11-12 23:57 claude: edits.describe replaces only the text before ## Subtasks or ## Log, given the description the edit started from; a mismatch raises ConflictError and the API answers 409 with the one on disk. It logs 'edited the description' as me, added to file-format.md. Conflicts offer Keep mine, Use the one on disk, or Edit mine (your text, with the disk version as the new base). Checked in Chromium: preview, save, a conflict from a direct file edit, Keep mine, and a mid-edit log line that saved cleanly and was kept.
- 2026-11-12 23:57 claude: moved to done
