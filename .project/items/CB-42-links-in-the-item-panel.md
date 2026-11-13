---
id: CB-42
type: task
title: Links in the item panel
status: todo
priority: medium
owner: claude
created: 2026-11-13
parent: CB-10
---
The item panel's Links section: both sides of every link (blocked by and blocks, related to, duplicate of and duplicated by), and + Add link, which takes a link type and an item ID and saves it through the existing set API.

Done when: adding "blocked by" on one item shows "Blocks" on the other, and `corkboard show` agrees.

## Subtasks
- [ ] Links section showing both sides, with each item's status
- [ ] + Add link form, with clear errors for an unknown ID or a link to itself
- [ ] Tests for the API writing each link type

## Log
- 2026-11-13 16:32 claude: created
