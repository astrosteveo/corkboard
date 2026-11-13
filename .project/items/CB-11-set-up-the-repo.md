---
id: CB-11
type: task
title: Set up the repo
status: in-progress
priority: high
owner: claude
created: 2026-11-12
release: v0.1
---
The skeleton the rest of v0.1 is built in: the folders from `.project/docs/plugin.md` (`bin/`, `corkboard/`, `tests/`, `.claude-plugin/`), a ruff config, a README stub, and a GitHub Actions workflow that runs the tests and ruff on every push and PR.

Done when `python3 -m unittest discover -s tests`, `uvx ruff format --check` and `uvx ruff check` pass locally and in CI.

## Subtasks
- [ ] Folders and an empty `corkboard` package
- [ ] ruff config and README stub
- [ ] CI workflow for the tests and ruff

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 21:28 claude: moved to in-progress
