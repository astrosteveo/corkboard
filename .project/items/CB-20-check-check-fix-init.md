---
id: CB-20
type: task
title: check, check --fix, init
status: in-progress
priority: medium
owner: claude
created: 2026-11-12
parent: CB-2
blocked_by: [CB-14]
---
Every rule in "What corkboard check verifies" in `.project/docs/file-format.md`, the safe repairs `--fix` makes, and `init` with its suggested prefix and name.

Done when `corkboard check` passes on this repo, each rule has a test that breaks it, and `corkboard init` sets up an empty folder.

## Subtasks
- [ ] Each check rule, with a test
- [ ] `--fix`: file renames and duplicate IDs
- [ ] `init`

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 22:09 claude: moved to in-progress
