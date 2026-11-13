---
id: CB-16
type: task
title: now and next
status: in-progress
priority: high
owner: claude
created: 2026-11-12
parent: CB-2
blocked_by: [CB-14]
---
The order of work and the two commands built on it, as `.project/docs/cli.md` describes: answered items first, then the active release, priority and number, skipping blocked items and the user's items. `now` is at most 25 lines, leaves out empty sections, and prints nothing outside a repo with `.project/`.

Done when output tests built from the `cli.md` examples pass, `now` never goes over 25 lines, and `corkboard next` on this repo names the next task in build order.

## Subtasks
- [ ] Order of work, including answered items
- [ ] `now`, with its limits and empty sections left out
- [ ] `next`, with its "next because" line
- [ ] Output tests from the `cli.md` examples

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 21:54 claude: moved to in-progress
