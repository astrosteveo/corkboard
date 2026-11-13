---
id: CB-40
type: task
title: Commits and branch in corkboard show
status: done
priority: medium
owner: claude
created: 2026-11-13
parent: CB-10
---
The commits and the branch that mention an item's ID, read from `git log`, so `corkboard show` lists the work behind an item without going online. The core function is shared with the web app's item panel.

Done when: `corkboard show` prints a Development section with the branch and the last 5 commits, matching the example in cli.md, and the output tests pass.

## Subtasks
- [x] Core: commits whose message has the exact ID, so EX-12 doesn't match EX-120
- [x] Core: the branch whose name has the lowercase ID
- [x] Development section in show, left out when there's nothing
- [x] Tests in a temporary git repo, and in a folder that isn't a git repo

## Log
- 2026-11-13 16:32 claude: created
- 2026-11-13 16:35 claude: moved to in-progress
- 2026-11-13 16:39 claude: done subtask: Core: commits whose message has the exact ID, so EX-12 doesn't match EX-120
- 2026-11-13 16:39 claude: done subtask: Core: the branch whose name has the lowercase ID
- 2026-11-13 16:39 claude: done subtask: Development section in show, left out when there's nothing
- 2026-11-13 16:39 claude: done subtask: Tests in a temporary git repo, and in a folder that isn't a git repo
- 2026-11-13 16:39 claude: Commits come from git log HEAD --branches, not --all or remotes: squash-merged PRs leave their branches on origin, so remote refs would list each item's work twice. Matching reuses the mention rule (new project.mention_pattern), case-insensitive for branch names. Git is run from the .project/ folder with a 3-second limit and stderr dropped, so CB-43's server can call the same corkboard/development.py.
- 2026-11-13 16:39 claude: moved to done
