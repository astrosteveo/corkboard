# File format

How a repo's project data is stored under `.project/`. Claude, `cpm` and the web app all read and write these files, and they stay readable in git and on GitHub without any of them.

## Layout

```
.project/
  config.yml
  releases/v0.1.md            one file per release
  items/CP-12-drag-cards.md   epics, tasks and bugs, all in one flat folder
  docs/                       plain Markdown pages; subfolders make the tree
  docs/decisions/             decision records
```

The folder is committed to git with the code.

## config.yml

```yaml
name: Claude Project
prefix: CP
```

- `name`: the project's display name in the web app.
- `prefix`: the ID prefix for this repo's items, like a Jira project key. Uppercase letters and digits, starting with a letter, such as `CP` or `GAME`. `cpm init` suggests one from the repo name. Changing it later means renaming every item, so pick it at setup.

Nothing else is configurable. Types and statuses are fixed.

## Items

An item is an epic, task or bug. Each one is a Markdown file in `items/` with a YAML header and a free-form body.

### Example

```markdown
---
id: CP-12
type: task
title: Drag cards between columns
status: in-progress
priority: high
owner: claude
created: 2026-11-12
parent: CP-3
labels: [ui, board]
blocked_by: [CP-9]
---
What and why, in a few lines. Free Markdown.

## Subtasks
- [x] Work out which column a card was dropped on
- [ ] Save the status change through cpm
- [ ] Put the card back if saving fails

## Log
- 2026-11-12 14:03 me: created
- 2026-11-12 14:20 claude: moved to in-progress
- 2026-11-12 15:02 claude: moved to waiting: should dropping on Done ask for confirmation?
```

### Header fields

`cpm` writes them in this order. Optional fields are left out when empty.

| Field | Required | Values |
|---|---|---|
| `id` | yes | `PREFIX-N`, such as `CP-12` |
| `type` | yes | `epic`, `task`, `bug` |
| `title` | yes | short text |
| `status` | yes | see Statuses |
| `priority` | yes | `high`, `medium`, `low` |
| `owner` | yes | `claude`, `me` |
| `created` | yes | `YYYY-MM-DD` |
| `parent` | no | ID of an epic. Tasks and bugs only. |
| `release` | no | a release name. Epics, and tasks or bugs with no parent. |
| `labels` | no | list of free-form words, such as `[ui, cli]` |
| `blocked_by` | no | list of item IDs |

There's no `updated` field: the last log line says when the item last changed.

### Statuses

| Status | Meaning |
|---|---|
| `backlog` | An idea, not planned yet. |
| `todo` | Planned and ready to start. |
| `in-progress` | Being worked on. |
| `waiting` | Claude needs the user's answer or review before going on. The last log line says what. |
| `done` | Finished. |
| `cancelled` | Decided not to do it. Kept, not deleted, so the decision stays visible. |

When the user answers a `waiting` item in the web app, it moves to `todo` and the reply is logged as `me: moved to todo: <reply>`. Answered items come first in `cpm next`.

Blocked isn't a status. An item is blocked while any item in its `blocked_by` isn't `done`. The web app shows it, and `cpm next` skips it.

### Hierarchy and releases

- A task or bug belongs to an epic through `parent`. Epics have no parent.
- An item's release is its own `release` field, or else its epic's. A task or bug with a parent doesn't set `release`, so each item's release is decided in one place.
- An epic's progress is its done tasks and bugs out of all of them, leaving out cancelled ones.

### Body

The body is free Markdown. Only two sections are read by the tool, and both are optional.

**`## Subtasks`**: a checklist of small steps, on tasks and bugs only.

```markdown
## Subtasks
- [x] Done step
- [ ] Open step
```

A subtask is only done or not done. It has no owner, labels or log of its own. If it needs those, make it a task. The web app shows progress as done out of total, such as 1/3.

**`## Log`**: the item's history, always the last section, newest line last.

```
- YYYY-MM-DD HH:MM who: text
```

- `who` is `me` or `claude`. Time is local, 24-hour.
- Lines are only ever added, never edited or removed.
- `cpm` adds a line for every change it makes: `created`, `moved to <status>`, `set <field>=<value>`, and subtask changes. A status change with a message is logged as `moved to <status>: <message>`. Moving to `waiting` always needs one.
- Status changes go through `cpm` so they're always logged. Anyone can add other lines, such as notes on what was tried.

## IDs and file names

- IDs are `PREFIX-N`, numbered from 1. A new item gets the highest number in `items/` plus 1. There's no counter file, so there's nothing to conflict on a merge.
- Numbers of deleted items can come back, which is another reason to cancel rather than delete.
- If two branches create the same number, `cpm check` reports it. `cpm check --fix` renumbers the newer item and lists references to the old number for review, since they could mean either item.
- File names are `PREFIX-N-short-title.md`. The ID is what identifies the item; the rest only helps people read the name. The short title is the title in lowercase with dashes, cut at a word boundary to about 40 characters.
- To find an item from its ID, match `items/CP-12-*.md`. The dash after the number keeps it from matching `CP-120`.
- When a title changes, `cpm` renames the file. A short title that's out of date or missing breaks nothing, and `cpm check` fixes it.
- Items refer to each other by ID, never by file path, so renames don't break references.

## Releases

One file per release in `releases/`, named after the release, such as `v0.1.md`.

```markdown
---
name: v0.1
status: active
date: 2026-12-01
---
What this release is for, in a few lines.
```

- `status`: `planned`, `active` or `released`.
- `date`: the target date while planned or active, and the ship date once released.
- The name can be anything that works as a file name, such as `v0.1` or `2026-12`.

## Docs

Plain Markdown pages in `docs/`. Subfolders make the page tree in the web app.

- A page's title is its first `#` heading, or else its file name.
- Writing an item ID such as `CP-12` anywhere in a page links to that item, and the item shows the link back. The same works in item bodies.
- Link to other pages with normal Markdown links.
- Decision records go in `docs/decisions/`, named `0001-short-name.md`, numbered in order.

## What cpm check verifies

- Every header parses, required fields are present, and every value is one of the allowed ones.
- IDs are unique, and every file name starts with its item's ID.
- Every `parent` exists and is an epic. Epics have no parent.
- Tasks and bugs with a parent don't set `release`. Every `release` named has a file in `releases/`.
- Every ID in `blocked_by` exists, and nothing is blocked by itself through a chain.
- Only tasks and bugs have a `## Subtasks` section.
- Log lines match the log format.
