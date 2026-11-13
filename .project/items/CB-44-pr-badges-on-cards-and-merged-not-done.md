---
id: CB-44
type: task
title: PR badges on cards, and Merged, not done
status: todo
priority: medium
owner: claude
created: 2026-11-13
parent: CB-10
blocked_by: [CB-41]
---
Board cards show their latest pull request and its state, such as `#14 merged`. The Now page's Merged, not done section lists items whose PR merged while the item isn't done or cancelled, with a Mark done button. Nothing changes an item on its own.

Done when: a merged PR shows "#14 merged" on its card, and a Mark <ID> done button on the Now page.

## Subtasks
- [ ] Server reads the PR list once and keeps it for a short time, instead of calling gh on every refresh
- [ ] PR badge on cards
- [ ] Merged, not done section with a Mark <ID> done button
- [ ] Tests for the matching and for the gh limits

## Log
- 2026-11-13 16:32 claude: created
