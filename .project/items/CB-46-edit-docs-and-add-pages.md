---
id: CB-46
type: task
title: Edit docs and add pages
status: done
priority: medium
owner: claude
created: 2026-11-13
parent: CB-8
blocked_by: [CB-45]
---
Edit a doc in a Markdown text box with a preview, with the same conflict check as item descriptions. + New page asks for a title and a folder and creates the file.

Done when: saving a page Claude changed while you were editing shows both versions, and a new page opens once it's created.

## Subtasks
- [x] Save API with a conflict check
- [x] Edit with a preview
- [x] + New page: title and folder to a file, refusing a name that's already taken
- [x] Tests

## Log
- 2026-11-13 16:32 claude: created
- 2026-11-13 18:09 claude: moved to in-progress
- 2026-11-13 18:11 claude: done subtask: Save API with a conflict check
- 2026-11-13 18:16 claude: done subtask: Edit with a preview
- 2026-11-13 18:16 claude: done subtask: + New page: title and folder to a file, refusing a name that's already taken
- 2026-11-13 18:16 claude: done subtask: Tests
- 2026-11-13 18:16 claude: The description's editor moved to editor.js (MarkdownEditor), shared by docs and descriptions. A new page opens in the editor, since it's only a heading. In decisions/ a new page gets the next number, as file-format.md names decision records. Closing the editor waits for the page to load again, so Use the one on disk never shows the old text.
- 2026-11-13 18:16 claude: moved to done
