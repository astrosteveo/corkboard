---
name: plan
description: Break a goal into a Corkboard release, epics, tasks and subtasks, and create them once the user approves the plan.
disable-model-invocation: true
argument-hint: "<goal>"
allowed-tools: Bash(corkboard *)
---

# Plan work

The user ran `/corkboard:plan` with this goal: `$ARGUMENTS`. If that's empty, ask what to plan.

Plan only. Write no code, and create nothing until the user approves.

1. Read what exists: PROJECT.md if the repo has one, `corkboard tree` for the active release, `corkboard tree none` for work with no release, and `corkboard list --all` if you need the rest.
2. Draft the plan and show it as a tree:
   - **The release:** an existing one, or a new one with a line saying what it's for.
   - **Epics**, each with a line saying what it covers.
   - **Under each epic, its tasks and bugs.** Give each one a line of what and why, a "Done when …" check, and a few subtasks.
   - **Priority:** use `high` only for what has to come first. Leave the rest at `medium`.
   - **Blockers:** add `blocked_by` only for real dependencies.
   - **Order:** list the tasks in the order you'd build them. Corkboard numbers items as they're created, so the numbers and `corkboard next` will follow that order.
3. Ask the user to approve the plan or change it, and wait.
4. Create what they approved:
   - `corkboard release <name>` for a new release, with its goal piped in.
   - `corkboard new epic "…" release=<name>` for each epic.
   - `corkboard new task "…" parent=<epic ID>` for each task, in build order, with its body piped in: the description, the "Done when" line, and a `## Subtasks` checklist. Add `blocked_by=` using the IDs `corkboard` printed for the items created earlier.
5. Show `corkboard tree <release>`, and say what `corkboard next` gives.
