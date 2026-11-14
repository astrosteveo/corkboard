---
id: CB-72
type: bug
title: plugin.md doesn't match the session-start hook
status: todo
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [docs]
---
plugin.md says the hook runs `${CLAUDE_PLUGIN_ROOT}/bin/corkboard now` and prints "Use the track skill". The hook runs `hooks/session_start.py` and prints "Use the corkboard:track skill".

## Subtasks
- [ ] plugin.md describes the hook as it is
- [ ] A test keeps the lead line in step

## Log
- 2026-11-13 20:04 claude: created
