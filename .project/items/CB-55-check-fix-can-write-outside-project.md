---
id: CB-55
type: bug
title: check --fix can write outside .project/items/
status: todo
priority: high
owner: claude
created: 2026-11-13
parent: CB-53
labels: [cli, security]
---
`check --fix` builds the rename path from the raw `id`, so an item with `id: ../../EX-1` is moved out of `.project/items/` and `check` then says ok. Renumbering a duplicate also uses the config's prefix after reporting it invalid: with no prefix, the duplicate becomes `-1`.

## Subtasks
- [ ] Rename only to a valid ID, inside items/
- [ ] Renumber only with a valid prefix
- [ ] Tests

## Log
- 2026-11-13 20:04 claude: created
