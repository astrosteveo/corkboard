---
id: CB-18
type: task
title: The track skill
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-3
blocked_by: [CB-15, CB-17]
---
`skills/track/SKILL.md` from `.project/docs/plugin.md`: when it loads, starting work, while working, questions, commits and PRs, finishing, saying where things stand, docs and decisions, and the rules. It pre-approves `Bash(corkboard *)`.

Done when a session with the plugin loaded takes a real item through the workflow: moves it, logs a decision, and commits with its ID.

## Subtasks
- [x] A description that loads it at the right times
- [x] The workflow sections
- [x] Try it on a real item

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 21:59 claude: moved to in-progress
- 2026-11-12 22:00 claude: done subtask: A description that loads it at the right times
- 2026-11-12 22:00 claude: done subtask: The workflow sections
- 2026-11-12 22:04 claude: done subtask: Try it on a real item
- 2026-11-12 22:04 claude: Trial: a fresh Sonnet session, plugin loaded from a copy, working in a separate small test repo. Before editing, it created an item with subtasks, moved it to in-progress and branched (tr-2-add-shout-option-to-greet-py). Then it made the change, ran the tests, committed with the ID in the message, ticked both subtasks and moved the item to done, with the item file in the same commit. It logged no decision, which is fine for a change that small. The first try had it editing before making the item, so the skill now says to set up the item before any edit. Earlier tries inside a clone of this repo were blocked, because the clone was the loaded plugin.
- 2026-11-12 22:04 claude: moved to done
