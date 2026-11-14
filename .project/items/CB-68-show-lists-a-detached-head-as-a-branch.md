---
id: CB-68
type: bug
title: show lists a detached HEAD as a branch, and misses commits on an orphan branch
status: todo
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [cli]
---
With HEAD detached at a ref whose name has the ID, `corkboard show` prints `branch: (HEAD detached at origin/ex-12-drag-cards)`. And on an orphan branch, `git log HEAD --branches` fails, so no commits are found, even ones on main.

## Subtasks
- [ ] Branches come from local branches only
- [ ] Commits are found when HEAD has no commits
- [ ] Tests

## Log
- 2026-11-13 20:04 claude: created
