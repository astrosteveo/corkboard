---
id: CB-72
type: bug
title: plugin.md doesn't match the session-start hook
status: done
priority: low
owner: claude
created: 2026-11-13
parent: CB-53
labels: [docs]
---
plugin.md says the hook runs `${CLAUDE_PLUGIN_ROOT}/bin/corkboard now` and prints "Use the track skill". The hook runs `hooks/session_start.py` and prints "Use the corkboard:track skill".

## Subtasks
- [x] plugin.md describes the hook as it is
- [x] A test keeps the lead line in step

## Log
- 2026-11-13 20:04 claude: created
- 2026-11-13 20:36 claude: moved to in-progress
- 2026-11-13 20:37 claude: done subtask: plugin.md describes the hook as it is
- 2026-11-13 20:37 claude: done subtask: A test keeps the lead line in step
- 2026-11-13 20:37 claude: Also brought plugin.md's quote of the track skill's description up to date, and the test covers it
- 2026-11-13 20:37 claude: moved to done
