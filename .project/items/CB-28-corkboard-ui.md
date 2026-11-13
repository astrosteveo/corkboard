---
id: CB-28
type: task
title: /corkboard:ui
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-4
blocked_by: [CB-24]
---
The slash command from `.project/docs/plugin.md`: it starts `corkboard ui` in the background and prints its URL, or only prints the URL if the web app is already running.

Done when `/corkboard:ui`, in a test repo with the plugin loaded from a copy, prints a URL that opens the page, and running it twice starts only one server.

## Subtasks
- [x] skills/ui/SKILL.md
- [x] Try it in a test repo

## Log
- 2026-11-12 22:45 claude: created
- 2026-11-12 23:25 claude: Run in the background from a non-interactive shell, corkboard ui starts with SIGINT ignored, so stop it with kill <pid>, not kill -INT. Ctrl-C in a terminal works.
- 2026-11-13 00:06 claude: moved to in-progress
- 2026-11-13 00:12 claude: done subtask: skills/ui/SKILL.md
- 2026-11-13 00:12 claude: done subtask: Try it in a test repo
- 2026-11-13 00:12 claude: Added corkboard ui --background: it starts python -m corkboard ui as its own session with output on /dev/null, waits until it answers, and prints the URL and process ID; /api/server now reports the pid, so a second call prints the same two lines. The skill is one command. Tried with two claude -p sessions (Haiku) in a test repo, plugin loaded from a copy: both gave http://localhost:4747 and the same pid, one server kept running after both ended, and the page loaded. Also ran it from a pip-installed copy.
- 2026-11-13 00:12 claude: moved to done
