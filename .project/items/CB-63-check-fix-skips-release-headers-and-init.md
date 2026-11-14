---
id: CB-63
type: bug
title: check --fix skips release headers, and init fails on an existing .project/
status: done
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [cli]
---
`check --fix` rewrites item headers that aren't in corkboard's format but not release headers, though its help says it fixes header formatting. And `corkboard init` in a folder whose `.project/` exists without config.yml fails with `error: File exists`, while every other command says to run `init`.

## Subtasks
- [x] check --fix rewrites release headers
- [x] init works when .project/ exists without config.yml
- [x] Tests and cli.md

## Log
- 2026-11-13 20:04 claude: created
- 2026-11-13 20:24 claude: moved to in-progress
- 2026-11-13 20:25 claude: done subtask: check --fix rewrites release headers
- 2026-11-13 20:25 claude: done subtask: init works when .project/ exists without config.yml
- 2026-11-13 20:25 claude: done subtask: Tests and cli.md
- 2026-11-13 20:25 claude: moved to done
