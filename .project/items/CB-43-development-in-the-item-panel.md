---
id: CB-43
type: task
title: Development in the item panel
status: done
priority: medium
owner: claude
created: 2026-11-13
parent: CB-10
blocked_by: [CB-41]
---
The branch, pull requests and commits for an item in the item panel, from `/api/items/<ID>`, using the same core code as `corkboard show`. Hidden when there are none.

Done when: an item with commits shows them in the panel, matching `corkboard show`.

## Subtasks
- [x] Add the development data to the item API
- [x] Development section in the panel
- [x] Tests for the API

## Log
- 2026-11-13 16:32 claude: created
- 2026-11-13 17:17 claude: moved to in-progress
- 2026-11-13 17:19 claude: done subtask: Add the development data to the item API
- 2026-11-13 17:19 claude: done subtask: Development section in the panel
- 2026-11-13 17:19 claude: done subtask: Tests for the API
- 2026-11-13 17:19 claude: development.for_item gathers branches, matching PRs and commits for both corkboard show and /api/items/<ID>, so they can't drift. Commits now carry their author date and PRs their GitHub URL, which the panel shows and links; show's output is unchanged.
- 2026-11-13 17:19 claude: moved to done
