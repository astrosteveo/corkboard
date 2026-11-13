---
id: CB-14
type: task
title: Command skeleton and show
status: todo
priority: high
owner: claude
created: 2026-11-12
parent: CB-2
blocked_by: [CB-13]
---
`bin/corkboard` finds its package from its own file path and runs commands, with the shared behavior from "Rules for every command" in `.project/docs/cli.md`: errors and warnings, help, `--as`, telling Claude from the user by `CLAUDECODE`, and color only in a terminal. Then `corkboard show`, without the Development section, which comes with CB-10.

Done when `corkboard show CB-12` on this repo matches the layout in `cli.md`.

## Subtasks
- [ ] `bin/corkboard` and running commands
- [ ] Errors, warnings, help, `--as` and `CLAUDECODE`
- [ ] `show`, with links both ways and `mentioned in`

## Log
- 2026-11-12 21:21 claude: created
