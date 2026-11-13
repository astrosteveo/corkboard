---
id: CB-17
type: task
title: Manifest and session-start hook
status: todo
priority: medium
owner: claude
created: 2026-11-12
parent: CB-3
blocked_by: [CB-16]
---
`.claude-plugin/plugin.json` and the session-start hook from `.project/docs/plugin.md`. The hook runs `${CLAUDE_PLUGIN_ROOT}/bin/corkboard now` on startup, resume, clear and compact, adds the lead line, and stays silent without `.project/` or when the command fails.

Done when a session started with `claude --plugin-dir .` has the `corkboard now` output in its context, and a session in another repo gets nothing added. From here on, work on this repo happens in sessions started that way.

## Subtasks
- [ ] Plugin manifest
- [ ] Session-start hook with the lead line
- [ ] Silent outside `.project/` and on failure

## Log
- 2026-11-12 21:21 claude: created
