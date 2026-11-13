---
id: CB-15
type: task
title: "Write items: new, move, sub, log"
status: in-progress
priority: high
owner: claude
created: 2026-11-12
parent: CB-2
blocked_by: [CB-14]
---
The core library's write path: whole files written and swapped into place, the next free ID, file names from titles, and log lines with who and when. Then the four commands Corkboard needs to track itself: `new` (with a piped body), `move`, `sub` and `log`. `new` checks the new item before writing it.

This is the switch-over. Once it's done, this repo's items change only through `corkboard`.

Done when tests cover each command, and this item is closed with `corkboard move CB-15 done`.

## Subtasks
- [ ] Whole-file writes, next ID and file names
- [ ] Log lines with who and when
- [ ] `new` with a piped body, checked before writing
- [ ] `move`, with the waiting message rule and the warnings
- [ ] `sub add`, `sub done`, `sub undo` and `log`

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 21:47 claude: moved to in-progress
