---
id: CB-11
type: task
title: Set up the repo
status: done
priority: high
owner: claude
created: 2026-11-12
release: v0.1
---
The skeleton the rest of v0.1 is built in: the folders from `.project/docs/plugin.md` (`bin/`, `corkboard/`, `tests/`, `.claude-plugin/`), a ruff config, a README stub, and a GitHub Actions workflow that runs the tests and ruff on every push and PR.

Done when `python3 -m unittest discover -s tests`, `uvx ruff format --check` and `uvx ruff check` pass locally and in CI.

## Subtasks
- [x] Folders and an empty `corkboard` package
- [x] ruff config and README stub
- [x] CI workflow for the tests and ruff

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 21:28 claude: moved to in-progress
- 2026-11-12 21:28 claude: done subtask: Folders and an empty `corkboard` package
- 2026-11-12 21:28 claude: done subtask: ruff config and README stub
- 2026-11-12 21:28 claude: done subtask: CI workflow for the tests and ruff
- 2026-11-12 21:28 claude: Only `corkboard/` and `tests/` exist so far. `bin/` comes with CB-14, `.claude-plugin/` with CB-17 and `web/` with v0.2, since git doesn't keep empty folders.
- 2026-11-12 21:28 claude: moved to done
