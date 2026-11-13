---
id: CB-17
type: task
title: Manifest and session-start hook
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-3
blocked_by: [CB-16]
---
`.claude-plugin/plugin.json` and the session-start hook from `.project/docs/plugin.md`. The hook runs `${CLAUDE_PLUGIN_ROOT}/bin/corkboard now` on startup, resume, clear and compact, adds the lead line, and stays silent without `.project/` or when the command fails.

Done when a session started with `claude --plugin-dir .` has the `corkboard now` output in its context, and a session in another repo gets nothing added. From here on, work on this repo happens in sessions started that way.

## Subtasks
- [x] Plugin manifest
- [x] Session-start hook with the lead line
- [x] Silent outside `.project/` and on failure

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 21:56 claude: moved to in-progress
- 2026-11-12 21:58 claude: done subtask: Plugin manifest
- 2026-11-12 21:58 claude: done subtask: Session-start hook with the lead line
- 2026-11-12 21:58 claude: done subtask: Silent outside `.project/` and on failure
- 2026-11-12 21:58 claude: The hook is a small Python script, not a shell line in hooks.json: it runs now, adds the lead line, and catches every failure so it always exits 0. Checked with two one-shot claude -p --plugin-dir sessions on Haiku: in this repo the context had the Corkboard line, in an empty folder it had nothing. claude plugin validate passes; it notes a missing LICENSE, which only the public plugin directory needs (the open question about publishing).
- 2026-11-12 21:58 claude: moved to done
- 2026-11-12 22:04 claude: Correction: don't work on this repo in a session started with --plugin-dir . after all. Claude Code won't let a session edit files of a plugin it has loaded, so every edit here gets blocked. See PROJECT.md's decisions; CB-18's trial found it.
