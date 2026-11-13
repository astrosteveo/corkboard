---
id: CB-16
type: task
title: now and next
status: done
priority: high
owner: claude
created: 2026-11-12
parent: CB-2
blocked_by: [CB-14]
---
The order of work and the two commands built on it, as `.project/docs/cli.md` describes: answered items first, then the active release, priority and number, skipping blocked items and the user's items. `now` is at most 25 lines, leaves out empty sections, and prints nothing outside a repo with `.project/`.

Done when output tests built from the `cli.md` examples pass, `now` never goes over 25 lines, and `corkboard next` on this repo names the next task in build order.

## Subtasks
- [x] Order of work, including answered items
- [x] `now`, with its limits and empty sections left out
- [x] `next`, with its "next because" line
- [x] Output tests from the `cli.md` examples

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 21:54 claude: moved to in-progress
- 2026-11-12 21:56 claude: done subtask: Order of work, including answered items
- 2026-11-12 21:56 claude: done subtask: `now`, with its limits and empty sections left out
- 2026-11-12 21:56 claude: done subtask: `next`, with its "next because" line
- 2026-11-12 21:56 claude: done subtask: Output tests from the `cli.md` examples
- 2026-11-12 21:56 claude: now on this repo is 10 lines, about 50 tokens. Left epics out of In progress, since an epic is in progress whenever any of its work is. Unreadable files get a line in now itself, because the session-start hook only passes stdout to Claude.
- 2026-11-12 21:56 claude: moved to done
