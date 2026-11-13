---
id: CB-36
type: task
title: Move epics between releases, and copy release notes
status: todo
priority: medium
owner: claude
created: 2026-11-12
parent: CB-7
blocked_by: [CB-25, CB-35]
---
Dragging an epic, or a task with no epic, onto another release's tab moves it to that release, the same as `corkboard set <ID> release=…`. Copy release notes copies Markdown of the release's done items, grouped by epic, leaving out cancelled ones.

Done when a drag changes the item's release on disk, and the copied notes list exactly the release's done items.

## Subtasks
- [ ] Drag onto a release tab
- [ ] Release notes as Markdown
- [ ] Copy them to the clipboard

## Log
- 2026-11-12 22:45 claude: created
