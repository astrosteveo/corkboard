---
id: CB-14
type: task
title: Command skeleton and show
status: done
priority: high
owner: claude
created: 2026-11-12
parent: CB-2
blocked_by: [CB-13]
---
`bin/corkboard` finds its package from its own file path and runs commands, with the shared behavior from "Rules for every command" in `.project/docs/cli.md`: errors and warnings, help, `--as`, telling Claude from the user by `CLAUDECODE`, and color only in a terminal. Then `corkboard show`, without the Development section, which comes with CB-10.

Done when `corkboard show CB-12` on this repo matches the layout in `cli.md`.

## Subtasks
- [x] `bin/corkboard` and running commands
- [x] Errors, warnings, help, `--as` and `CLAUDECODE`
- [x] `show`, with links both ways and `mentioned in`

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 21:42 claude: moved to in-progress
- 2026-11-12 21:46 claude: done subtask: `bin/corkboard` and running commands
- 2026-11-12 21:46 claude: done subtask: Errors, warnings, help, `--as` and `CLAUDECODE`
- 2026-11-12 21:46 claude: done subtask: `show`, with links both ways and `mentioned in`
- 2026-11-12 21:46 claude: Wrote a small argument parser instead of argparse, which prints its own usage format and exits 2; the spec wants one `error:` line and exit 1. No color yet: the spec allows it only in a terminal, and plain text was enough. `corkboard show CB-12` on this repo matches the layout in cli.md.
- 2026-11-12 21:46 claude: moved to done
