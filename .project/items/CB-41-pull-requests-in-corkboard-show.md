---
id: CB-41
type: task
title: Pull requests in corkboard show
status: done
priority: medium
owner: claude
created: 2026-11-13
parent: CB-10
blocked_by: [CB-40]
---
The pull requests whose title, body or branch has the item's ID, read with `gh` with a 3-second limit and added to show's Development section.

Done when: show lists each PR with its state and checks, and without `gh`, a GitHub remote or a connection, the PR lines are left out and nothing else changes.

## Subtasks
- [x] One `gh api graphql` call, with a timeout
- [x] Match the ID in the title, body or branch name
- [x] PR lines in show
- [x] Tests with a fake gh on PATH: answers, fails, and hangs

## Log
- 2026-11-13 16:32 claude: created
- 2026-11-13 16:48 claude: moved to in-progress
- 2026-11-13 16:56 claude: Reads PRs with one gh api graphql call for the 100 newest, asking only for the checks' overall state. gh pr list --json statusCheckRollup fetches every check run: 1.5s for this repo's 32 PRs and 9-18s for 100 on cli/cli, so the 3s limit would soon drop the PR lines. The GraphQL query took 0.7-0.9s here. Matching is local (exact ID in title or body, any case in the branch) so CB-44 can cache the same list for the board.
- 2026-11-13 16:56 claude: done subtask: One `gh api graphql` call, with a timeout
- 2026-11-13 16:56 claude: done subtask: Match the ID in the title, body or branch name
- 2026-11-13 16:56 claude: done subtask: PR lines in show
- 2026-11-13 16:56 claude: done subtask: Tests with a fake gh on PATH: answers, fails, and hangs
- 2026-11-13 16:56 claude: moved to done
