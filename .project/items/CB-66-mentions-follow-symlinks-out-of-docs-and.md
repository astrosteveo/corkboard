---
id: CB-66
type: bug
title: Mentions follow symlinks out of docs/, and search misses doc file names
status: done
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [server, docs]
---
"Mentioned in" lists a doc that is a symlink out of `docs/`, whose page then gives a 404, and lists a page twice when another doc is a symlink to it. And Ctrl-K search for `cli.md` doesn't find `cli.md`, because it matches the name without `.md`.

## Subtasks
- [x] Mentions list only pages inside docs/, once each
- [x] Search finds a doc by its file name with .md
- [x] Tests

## Log
- 2026-11-13 20:04 claude: created
- 2026-11-13 20:27 claude: moved to in-progress
- 2026-11-13 20:28 claude: done subtask: Mentions list only pages inside docs/, once each
- 2026-11-13 20:28 claude: done subtask: Search finds a doc by its file name with .md
- 2026-11-13 20:28 claude: done subtask: Tests
- 2026-11-13 20:28 claude: moved to done
