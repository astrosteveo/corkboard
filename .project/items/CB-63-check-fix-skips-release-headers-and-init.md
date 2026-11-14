---
id: CB-63
type: bug
title: check --fix skips release headers, and init fails on an existing .project/
status: todo
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [cli]
---
`check --fix` rewrites item headers that aren't in corkboard's format but not release headers, though its help says it fixes header formatting. And `corkboard init` in a folder whose `.project/` exists without config.yml fails with `error: File exists`, while every other command says to run `init`.

## Subtasks
- [ ] check --fix rewrites release headers
- [ ] init works when .project/ exists without config.yml
- [ ] Tests and cli.md

## Log
- 2026-11-13 20:04 claude: created
