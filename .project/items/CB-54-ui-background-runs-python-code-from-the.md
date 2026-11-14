---
id: CB-54
type: bug
title: ui --background runs Python code from the repo it serves
status: done
priority: high
owner: claude
created: 2026-11-13
parent: CB-53
labels: [server, security]
---
`corkboard ui --background` starts the server with `python -m corkboard` from inside the repo, so the repo's folder comes first on `sys.path`. A `corkboard.py` or `json.py` at the repo root runs in place of the server, which means `/corkboard:ui` in a cloned repo can run that repo's code.

## Subtasks
- [x] Start the child so it can't import from the repo
- [x] Test with a corkboard.py and a json.py in the repo

## Log
- 2026-11-13 20:04 claude: created
- 2026-11-13 20:05 claude: moved to in-progress
- 2026-11-13 20:06 claude: done subtask: Start the child so it can't import from the repo
- 2026-11-13 20:06 claude: done subtask: Test with a corkboard.py and a json.py in the repo
- 2026-11-13 20:06 claude: Fixed with python -P, which keeps the repo's folder off sys.path; PYTHONPATH still finds the package
- 2026-11-13 20:06 claude: moved to done
