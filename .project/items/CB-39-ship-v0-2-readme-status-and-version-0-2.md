---
id: CB-39
type: task
title: "Ship v0.2: README, Status and version 0.2.0"
status: done
priority: high
owner: claude
created: 2026-11-13
release: v0.2
---
The web app is built (CB-23 to CB-36). Make it reach installed copies and say so: bump the version to 0.2.0 in both `.claude-plugin/plugin.json` and `pyproject.toml`, describe the web app, `corkboard ui` and `/corkboard:ui` in the README, and bring PROJECT.md's Status up to date. Also fixes the item page having no heading since the title became editable, found in the final browser pass.

## Subtasks
- [x] The item page's heading
- [x] README: the web app, corkboard ui and /corkboard:ui
- [x] PROJECT.md Status
- [x] Version 0.2.0 in plugin.json and pyproject.toml

## Log
- 2026-11-13 00:15 claude: created
- 2026-11-13 00:15 claude: moved to in-progress
- 2026-11-13 00:15 claude: done subtask: The item page's heading
- 2026-11-13 00:15 claude: done subtask: README: the web app, corkboard ui and /corkboard:ui
- 2026-11-13 00:15 claude: done subtask: PROJECT.md Status
- 2026-11-13 00:15 claude: done subtask: Version 0.2.0 in plugin.json and pyproject.toml
- 2026-11-13 00:15 claude: Final browser pass on main, each scenario on a fresh demo: all passed except the item page, which had no heading since the title became an input. The h1 now holds the title as text, with the input labelled Title. Dark theme and 390px width checked on every screen, with no horizontal overflow. v0.2 stays active so the board keeps showing it; the user can release it from the Releases header.
- 2026-11-13 00:15 claude: moved to done
