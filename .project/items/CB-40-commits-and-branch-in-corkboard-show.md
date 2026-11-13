---
id: CB-40
type: task
title: Commits and branch in corkboard show
status: todo
priority: medium
owner: claude
created: 2026-11-13
parent: CB-10
---
The commits and the branch that mention an item's ID, read from `git log`, so `corkboard show` lists the work behind an item without going online. The core function is shared with the web app's item panel.

Done when: `corkboard show` prints a Development section with the branch and the last 5 commits, matching the example in cli.md, and the output tests pass.

## Subtasks
- [ ] Core: commits whose message has the exact ID, so EX-12 doesn't match EX-120
- [ ] Core: the branch whose name has the lowercase ID
- [ ] Development section in show, left out when there's nothing
- [ ] Tests in a temporary git repo, and in a folder that isn't a git repo

## Log
- 2026-11-13 16:32 claude: created
