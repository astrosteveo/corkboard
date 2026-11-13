---
id: CB-20
type: task
title: check, check --fix, init
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-2
blocked_by: [CB-14]
---
Every rule in "What corkboard check verifies" in `.project/docs/file-format.md`, the safe repairs `--fix` makes, and `init` with its suggested prefix and name.

Done when `corkboard check` passes on this repo, each rule has a test that breaks it, and `corkboard init` sets up an empty folder.

## Subtasks
- [x] Each check rule, with a test
- [x] `--fix`: file renames and duplicate IDs
- [x] `init`

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 22:09 claude: moved to in-progress
- 2026-11-12 22:12 claude: done subtask: Each check rule, with a test
- 2026-11-12 22:12 claude: done subtask: `--fix`: file renames and duplicate IDs
- 2026-11-12 22:12 claude: done subtask: `init`
- 2026-11-12 22:12 claude: check reads every file itself, so it also sees the second file using an ID, which the loader skips. --fix repairs header formatting, file names and duplicate IDs, all at once per file. The init-then-new test found a real bug: new failed in a fresh project because items/ didn't exist yet. write_file now creates the folder.
- 2026-11-12 22:12 claude: moved to done
