---
id: CB-42
type: task
title: Links in the item panel
status: done
priority: medium
owner: claude
created: 2026-11-13
parent: CB-10
---
The item panel's Links section: both sides of every link (blocked by and blocks, related to, duplicate of and duplicated by), and + Add link, which takes a link type and an item ID and saves it through the existing set API.

Done when: adding "blocked by" on one item shows "Blocks" on the other, and `corkboard show` agrees.

## Subtasks
- [x] Links section showing both sides, with each item's status
- [x] + Add link form, with clear errors for an unknown ID or a link to itself
- [x] Tests for the API writing each link type

## Log
- 2026-11-13 16:32 claude: created
- 2026-11-13 17:12 claude: moved to in-progress
- 2026-11-13 17:12 claude: done subtask: Links section showing both sides, with each item's status
- 2026-11-13 17:12 claude: done subtask: + Add link form, with clear errors for an unknown ID or a link to itself
- 2026-11-13 17:12 claude: done subtask: Tests for the API writing each link type
- 2026-11-13 17:12 claude: Reverse sides (blocks, related_to, duplicated_by) come from the project view, built with the same functions as corkboard show. + Add link offers only the three links an item stores itself, so each add writes one file. Removing links and refusing blocking cycles are CB-50 and CB-51.
- 2026-11-13 17:12 claude: moved to done
