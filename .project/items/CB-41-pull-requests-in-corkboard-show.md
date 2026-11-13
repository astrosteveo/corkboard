---
id: CB-41
type: task
title: Pull requests in corkboard show
status: todo
priority: medium
owner: claude
created: 2026-11-13
parent: CB-10
blocked_by: [CB-40]
---
The pull requests whose title, body or branch has the item's ID, read with `gh` with a 3-second limit and added to show's Development section.

Done when: show lists each PR with its state and checks, and without `gh`, a GitHub remote or a connection, the PR lines are left out and nothing else changes.

## Subtasks
- [ ] One `gh pr list` call, with a timeout
- [ ] Match the ID in the title, body or branch name
- [ ] PR lines in show
- [ ] Tests with a fake gh on PATH: answers, fails, and hangs

## Log
- 2026-11-13 16:32 claude: created
