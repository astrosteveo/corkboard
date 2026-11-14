---
id: CB-56
type: bug
title: corkboard release overwrites a release file it couldn't read
status: todo
priority: high
owner: claude
created: 2026-11-13
parent: CB-53
labels: [cli]
---
When `releases/v0.2.md` can't be read (such as a `# comment` in its header) or its header has another `name`, `corkboard release v0.2 status=active` replaces the file with a bare header and exits 0. The release's goal is lost. `new` refuses a path that exists; `release` should too.

## Subtasks
- [ ] Refuse when the file exists but isn't that release
- [ ] Tests

## Log
- 2026-11-13 20:04 claude: created
