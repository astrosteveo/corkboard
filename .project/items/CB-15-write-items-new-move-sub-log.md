---
id: CB-15
type: task
title: "Write items: new, move, sub, log"
status: done
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
- [x] Whole-file writes, next ID and file names
- [x] Log lines with who and when
- [x] `new` with a piped body, checked before writing
- [x] `move`, with the waiting message rule and the warnings
- [x] `sub add`, `sub done`, `sub undo` and `log`

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 21:47 claude: moved to in-progress
- 2026-11-12 21:53 claude: done subtask: Whole-file writes, next ID and file names
- 2026-11-12 21:53 claude: done subtask: Log lines with who and when
- 2026-11-12 21:53 claude: done subtask: `new` with a piped body, checked before writing
- 2026-11-12 21:53 claude: done subtask: `move`, with the waiting message rule and the warnings
- 2026-11-12 21:53 claude: done subtask: `sub add`, `sub done`, `sub undo` and `log`
- 2026-11-12 21:53 claude: In Claude Code's shell, stdin with nothing piped in is an open socket, not /dev/null, so a plain read would hang forever. A heredoc arrives as a regular file under zsh and a pipe as a FIFO, so new reads stdin only when it's a FIFO or a regular file. A test runs the real executable with a socket as stdin to keep it that way.
- 2026-11-12 21:53 claude: moved to done
