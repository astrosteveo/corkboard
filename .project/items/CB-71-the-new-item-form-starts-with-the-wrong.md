---
id: CB-71
type: bug
title: The New item form starts with the wrong release
status: todo
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [ui]
---
On `/board?release=v0.2`, the sidebar's New item and Ctrl-K's New task start with the active release, not v0.2. And with no active release, `c` on the board starts with No release instead of the release the board shows; with `?release=v9` it starts with a release that doesn't exist. ui.md: on the board, the form starts with the release and epic it's filtered to.

## Subtasks
- [ ] Every way to open the form on the board starts with the board's release
- [ ] Checked in a browser

## Log
- 2026-11-13 20:04 claude: created
