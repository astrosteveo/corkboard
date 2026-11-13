---
id: CB-44
type: task
title: PR badges on cards, and Merged, not done
status: done
priority: medium
owner: claude
created: 2026-11-13
parent: CB-10
blocked_by: [CB-41]
---
Board cards show their latest pull request and its state, such as `#14 merged`. The Now page's Merged, not done section lists items whose PR merged while the item isn't done or cancelled, with a Mark done button. Nothing changes an item on its own.

Done when: a merged PR shows "#14 merged" on its card, and a Mark <ID> done button on the Now page.

## Subtasks
- [x] Server reads the PR list once and keeps it for a short time, instead of calling gh on every refresh
- [x] PR badge on cards
- [x] Merged, not done section with a Mark <ID> done button
- [x] Tests for the matching and for the gh limits

## Log
- 2026-11-13 16:32 claude: created
- 2026-11-13 17:20 claude: moved to in-progress
- 2026-11-13 17:24 claude: done subtask: Server reads the PR list once and keeps it for a short time, instead of calling gh on every refresh
- 2026-11-13 17:24 claude: done subtask: PR badge on cards
- 2026-11-13 17:24 claude: done subtask: Merged, not done section with a Mark <ID> done button
- 2026-11-13 17:24 claude: done subtask: Tests for the matching and for the gh limits
- 2026-11-13 17:24 claude: Badges and Merged, not done use only the item's own PRs (ID in title or branch). With body matches too, this repo flagged its in-progress epic and this very item, both only named in other PRs' bodies. The server keeps the PR list for 60s behind a lock, shared by /api/pulls and /api/items/<ID>; the page asks again on project changes and every 60s, since a merge changes no local file.
- 2026-11-13 17:24 claude: moved to done
