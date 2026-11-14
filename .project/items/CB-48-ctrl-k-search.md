---
id: CB-48
type: task
title: Ctrl-K search
status: done
priority: medium
owner: claude
created: 2026-11-13
parent: CB-9
blocked_by: [CB-45]
---
Ctrl-K opens search: jump to any item or doc by ID or title, or run an action such as New task or Go to v0.3. Search covers item titles, descriptions and docs.

Done when: Ctrl-K, typing "drag", then Enter opens the matching item, and the arrow keys and Esc work.

## Subtasks
- [x] Search box and results, with keyboard navigation
- [x] Items by ID, title and description
- [x] Docs by title and text
- [x] Actions: New task, bug or epic, and Go to a release or a screen

## Log
- 2026-11-13 16:32 claude: created
- 2026-11-13 18:56 claude: moved to in-progress
- 2026-11-13 18:58 claude: done subtask: Items by ID, title and description
- 2026-11-13 18:58 claude: done subtask: Docs by title and text
- 2026-11-13 19:02 claude: done subtask: Search box and results, with keyboard navigation
- 2026-11-13 19:02 claude: done subtask: Actions: New task, bug or epic, and Go to a release or a screen
- 2026-11-13 19:02 claude: Search runs on the server (search.py, GET /api/search?q=) so doc text stays off the page and the ranking has unit tests; actions are matched in the page. Docs are matched by file name, per CB-52. Enter pressed before the latest answer arrives waits for it, so typing fast and pressing Enter still opens the first match.
- 2026-11-13 19:02 claude: moved to done
