---
name: track
description: Use in a repo with a .project/ folder before you start, finish or plan any work, and before you say where the project stands. Keeps the repo's Corkboard items, releases and docs true as you work, through the corkboard command.
user-invocable: false
allowed-tools: Bash(corkboard *)
---

# Track work with Corkboard

This repo keeps its work in `.project/` as Markdown files: releases, epics, tasks and bugs (together called items), and docs. The user follows the project through these files, the web app and the summary at the start of each session, so keep them true as you work. An item still marked in progress a day after its PR merged misleads the user, and so does work that has no item at all.

`corkboard` is on your PATH, and it does the bookkeeping: IDs, file names, and log lines with who and when. Change an item's header fields, status, subtasks and log only through it. Open an item's file only to edit its description.

## Commands

```
corkboard now                           # where things stand: the session-start summary
corkboard next                          # the item to do next, in full
corkboard show EX-12                    # one item: links, subtasks, last log lines, path
corkboard list status=todo labels=ui    # one line per item
corkboard tree v0.1                     # a release's epics and tasks, with progress
corkboard new task "Title" parent=EX-3 priority=high <<'EOF'
What and why, in a few lines.

## Subtasks
- [ ] First step
EOF
corkboard move EX-12 in-progress        # backlog, todo, in-progress, waiting, done, cancelled
corkboard move EX-12 waiting "Debounce the drop, or rebuild the column?"
corkboard sub EX-12 done 2              # by its number in show; also: add "text", undo 2
corkboard log EX-12 "Chose X over Y because Z"
corkboard set EX-12 priority=high labels=ui,board
corkboard check                         # files in .project/ that break the format
```

`corkboard help` lists every command, and `corkboard <command> --help` explains one.

## Before starting work

1. Find the item the work belongs to with `corkboard list` or `corkboard show`, or create one with `corkboard new`, piping in a few lines of what and why and a `## Subtasks` checklist. Every change you commit gets an item, except a trivial fix such as a typo or a one-line change.
2. `corkboard move <ID> in-progress`. Keep one item in progress at a time: finish it, or park it back in `todo`, before starting another. If its epic is still `todo`, move the epic to `in-progress` too.
3. On the default branch, switch to a branch named after the item's file name, which `corkboard show` prints as `path:`. For example, `EX-12-drag-cards.md` becomes `ex-12-drag-cards`.

## While working

- Tick subtasks off as you finish them: `corkboard sub <ID> done <N>`.
- Use `corkboard log <ID> "..."` for what a later session would need: a choice and why, a dead end, a surprise. Not every step.
- Work that turns up along the way becomes a new item (`corkboard new`, with `parent=` and `blocked_by=` where they apply) instead of growing the current change, unless it's trivial.
- When a question blocks the item, ask the user in chat and run `corkboard move <ID> waiting "<the question>"`. When they answer in chat, log their answer with `corkboard log` and move the item back to `in-progress`.

## Commits and pull requests

- Put the item's ID in every commit message for it, such as `feat(board): drag cards between columns (EX-12)`. Everything else about commits follows the user's own rules.
- Put the ID in a pull request's title. After opening one, run `corkboard move <ID> waiting "PR #14 ready for review"`, unless the user has said you merge your own PRs.

## Finishing

- An item is done when its subtasks are all ticked and the project's formatter, linter and tests pass.
- Work that goes through a PR moves to `done` once the PR merges. Work committed without a PR moves to `done` right away.
- When an epic's last open task or bug is done, move the epic to `done` too.

## Saying where things stand

Answer from `corkboard now`, `corkboard tree` and `corkboard list`. Don't read item files one by one: the commands cost fewer tokens and are always current.

## Docs and decisions

- Specs and longer notes go in `.project/docs/` as Markdown. Mention item IDs where they apply, and Corkboard links them both ways.
- In examples inside docs, use a made-up prefix such as `EX-12`, never the repo's own, or the example links to a real item.
- One-line decisions go in PROJECT.md's Decisions section if the repo has one. A decision that needs more than a line gets a page in `.project/docs/decisions/`, and its one-liner links to it.

## Rules

- Never delete an item. Cancel it with a message saying why: `corkboard move <ID> cancelled "No longer needed: …"`.
- Don't change items the user owns (`owner: me`) unless they ask.
- If `corkboard` reports files it couldn't read, run `corkboard check` and fix them before going on.
