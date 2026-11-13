---
id: CB-36
type: task
title: Move epics between releases, and copy release notes
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-7
blocked_by: [CB-25, CB-35]
---
Dragging an epic, or a task with no epic, onto another release's tab moves it to that release, the same as `corkboard set <ID> release=…`. Copy release notes copies Markdown of the release's done items, grouped by epic, leaving out cancelled ones.

Done when a drag changes the item's release on disk, and the copied notes list exactly the release's done items.

## Subtasks
- [x] Drag onto a release tab
- [x] Release notes as Markdown
- [x] Copy them to the clipboard

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-13 00:05 claude: moved to in-progress
- 2026-11-13 00:05 claude: done subtask: Drag onto a release tab
- 2026-11-13 00:05 claude: done subtask: Release notes as Markdown
- 2026-11-13 00:05 claude: done subtask: Copy them to the clipboard
- 2026-11-13 00:05 claude: Epic headers and loose task rows drag onto the release tabs, which call set release=<name> (or release= for No release); a task under an epic is refused with a pointer to its epic. Release notes are '### Epic' sections of '- Title (EX-4)' lines for done tasks and bugs, then 'Other changes' for done work with no epic; cancelled work is left out. If the clipboard refuses, the notes show in a text box to copy by hand. Checked in Chromium: the copied notes listed exactly corkboard list release=v0.1 status=done, and both drags changed the files.
- 2026-11-13 00:05 claude: moved to done
