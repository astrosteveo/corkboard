---
id: CB-54
type: bug
title: ui --background runs Python code from the repo it serves
status: todo
priority: high
owner: claude
created: 2026-11-13
parent: CB-53
labels: [server, security]
---
`corkboard ui --background` starts the server with `python -m corkboard` from inside the repo, so the repo's folder comes first on `sys.path`. A `corkboard.py` or `json.py` at the repo root runs in place of the server, which means `/corkboard:ui` in a cloned repo can run that repo's code.

## Subtasks
- [ ] Start the child so it can't import from the repo
- [ ] Test with a corkboard.py and a json.py in the repo

## Log
- 2026-11-13 20:04 claude: created
