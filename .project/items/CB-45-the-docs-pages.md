---
id: CB-45
type: task
title: The docs pages
status: in-progress
priority: medium
owner: claude
created: 2026-11-13
parent: CB-8
---
The Docs screen at `/docs` and `/docs/<path>`: the tree of the `docs/` folder, each page rendered as Markdown with raw HTML off, item IDs as chips with the item's current title and status, and a footer with the items the page mentions and when it last changed.

Done when: `/docs/ui` shows ui.md with chips, a doc containing a `<script>` runs nothing, and the item panel's Mentioned in links to the doc.

## Subtasks
- [x] Docs API: the list (path, title, last changed) and one page, serving only .md files inside docs/
- [ ] Docs in the sidebar, the routes, and the tree
- [ ] ID chips with the current title and status, in docs and item descriptions
- [ ] Footer, and Mentioned in linking to the doc
- [ ] Tests, including paths that try to leave docs/

## Log
- 2026-11-13 16:32 claude: created
- 2026-11-13 17:39 claude: moved to in-progress
- 2026-11-13 17:45 claude: done subtask: Docs API: the list (path, title, last changed) and one page, serving only .md files inside docs/
