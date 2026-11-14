---
id: CB-52
type: bug
title: Docs show their heading instead of their file name
status: done
priority: medium
owner: claude
created: 2026-11-13
release: v0.3
labels: [ui, docs]
related: [CB-45]
---
The docs tree lists each page by its first `#` heading, so `ui.md` shows up as "Web app" and `plugin.md` as "Claude Code plugin". The user looked for UI and couldn't find it. A doc should go by its file name everywhere the app names it: the tree, search, the browser tab and Mentioned in.

## Subtasks
- [x] A doc's title is its file name, such as `ui.md`
- [x] Headings of ui.md and plugin.md match their file names
- [x] Spec and tests

## Log
- 2026-11-13 18:48 claude: created
- 2026-11-13 18:48 claude: moved to in-progress
- 2026-11-13 18:48 claude: done subtask: A doc's title is its file name, such as `ui.md`
- 2026-11-13 18:48 claude: done subtask: Headings of ui.md and plugin.md match their file names
- 2026-11-13 18:48 claude: done subtask: Spec and tests
- 2026-11-13 18:49 claude: moved to done
