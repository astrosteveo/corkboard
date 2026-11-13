# Claude Code plugin

What the plugin contains, and how Claude works with a repo's project data through it. The CLI is in [cli.md](cli.md) and the files in [file-format.md](file-format.md).

## Layout

This repo is the plugin. The astro-plugins marketplace lists it by its GitHub repo, so it installs from the same place as the user's other plugins.

```
.claude-plugin/plugin.json
bin/corkboard            the CLI, on Claude's PATH while the plugin is enabled
corkboard/               the Python code: core library, CLI commands and web server
corkboard/web/           the web app: HTML, CSS, JavaScript, and Preact, htm and marked as single files
tests/                   unittest tests
hooks/hooks.json         the session-start hook
skills/track/SKILL.md    the workflow, loaded by Claude
skills/next/SKILL.md     /corkboard:next
skills/done/SKILL.md     /corkboard:done
skills/plan/SKILL.md     /corkboard:plan
skills/ui/SKILL.md       /corkboard:ui
```

- The plugin is named `corkboard`, so its slash commands are `/corkboard:next`, `/corkboard:done` and so on.
- `bin/corkboard` has to run right after the plugin installs, with no install step. It's a Python 3.11+ script that uses only the standard library. It finds the rest of its code from its own file path, since `${CLAUDE_PLUGIN_ROOT}` isn't set in Claude's shells.
- Tests run with `python3 -m unittest discover -s tests`. Formatting and linting use `uvx ruff format` and `uvx ruff check`.
- Each skill holds everything it needs in its own text. Claude Code asks before reading files outside the project, and an installed plugin always is outside it.
- Plugins can't ship permission rules. Each skill pre-approves `corkboard` with `allowed-tools: Bash(corkboard *)` while it's active. For other turns, the README tells the user to add `Bash(corkboard *)` to their settings once.
- To run `corkboard` in their own terminal, outside Claude Code, the user installs it as a Python tool: `uv tool install git+https://github.com/astrosteveo/corkboard`, built from `pyproject.toml`. The plugin itself never uses that package. The web app is inside the `corkboard/` package so that installed copy has it too.

## Session-start hook

Runs `${CLAUDE_PLUGIN_ROOT}/bin/corkboard now`, by full path, when a session starts, resumes, is cleared or compacts, and prints:

```
This repo tracks its work in .project/ with corkboard. Use the track skill before you start, finish or plan work.

Example · v0.1 active, due 2026-12-01 · 7/15 done

Waiting on you (1)
  EX-14 Cards flicker on drop: "debounce, or rebuild the column?"
…
```

- What it prints goes into Claude's context. The user doesn't see it.
- It prints nothing in a repo without `.project/`, and nothing if `corkboard` fails, and it always exits 0, so it can't break a session start.
- `corkboard now` is at most 25 lines, well under the 10,000 characters Claude Code accepts from a hook.

## The track skill

Loaded by Claude, not run by the user (`user-invocable: false`), with `allowed-tools: Bash(corkboard *)`. Its description says when to load it:

> Use in a repo with a .project/ folder before you start, finish or plan any work, and before you say where the project stands. Keeps the repo's items, releases and docs true as you work, through corkboard.

What it tells Claude to do:

### Starting work

1. Find the item the work belongs to (`corkboard list`, `corkboard show`), or create one with `corkboard new`, piping in a short description and subtasks.
2. Every change Claude commits gets an item, except trivial fixes such as a typo or a one-line fix.
3. `corkboard move <ID> in-progress`. Claude keeps one item in progress at a time, and finishes or parks one (back to `todo`) before starting another. If the item's epic is still `todo`, move the epic to `in-progress` too.
4. On the default branch, switch to a branch named after the item's file name: `EX-12-drag-cards.md` → `ex-12-drag-cards`.

### While working

- Tick subtasks off as they're done: `corkboard sub <ID> done <N>`.
- `corkboard log` what a later session would need: a choice and why, a dead end, a surprise. Not every step.
- New work that turns up becomes a new item (`corkboard new`, with `parent` and `blocked_by` as they apply). Work found along the way stays out of the current change unless it's trivial.
- A question that blocks the item: ask the user in chat, and `corkboard move <ID> waiting "<question>"`. When the user answers in chat, `corkboard log` the answer and move the item back to `in-progress`.

### Commits and pull requests

- Every commit for an item has its ID in the message, such as `feat(board): drag cards between columns (EX-12)`. Everything else about commits follows the user's own rules.
- A pull request has the ID in its title. After opening one: `corkboard move <ID> waiting "PR #14 ready for review"`.

### Finishing

- An item is done when its subtasks are all ticked and the project's formatter, linter and tests pass.
- Work that goes through a PR moves to `done` once the PR merges. Work committed without a PR moves to `done` before its last commit, so the item's file goes into that commit with the work.
- When an epic's last open task or bug is done, move the epic to `done` too.

### Saying where things stand

Answer from `corkboard now`, `corkboard tree` and `corkboard list`, never by reading item files one by one.

### Docs and decisions

- Specs and longer notes go in `.project/docs/` as Markdown, mentioning item IDs where they apply.
- One-line decisions go in PROJECT.md's Decisions section, which loads into every session. A decision that needs more than a line gets a page in `.project/docs/decisions/`, and its one-liner links to it.

### Rules

- Header fields change only through `corkboard`. Open an item's file only to edit its description, or to reword or remove a subtask.
- Never delete an item. Cancel it with a message saying why.
- Don't change items the user owns unless they ask.
- Prefer `corkboard` output to reading files: it costs fewer tokens and is always current.

## Slash commands

Each is a skill the user runs (`disable-model-invocation: true`), with `allowed-tools: Bash(corkboard *)`.

### /corkboard:next [ID]

1. Takes the named item, or the one `corkboard next` gives.
2. If Claude already has an item in progress, says so and asks whether to finish it first or park it.
3. Moves the item to `in-progress`, branches if on the default branch, and shows it with `corkboard show`.
4. States a short plan from its description and subtasks, then starts.

With nothing to do, it says so and suggests `/corkboard:plan`.

### /corkboard:done [ID]

1. Takes the named item, or Claude's one item in progress. With none, it asks which.
2. Checks that every subtask is ticked. If some aren't, it asks whether to finish them or move them into a new item.
3. Runs the project's formatter, linter and tests, and fixes what fails.
4. Commits what's left, with the ID in the message.
5. In a repo with a GitHub remote, it pushes the branch, opens a PR with the ID in its title, and moves the item to `waiting` with "PR #N ready for review". Otherwise it moves the item to `done`.
6. Reports what it did and what `corkboard next` gives.

### /corkboard:plan <goal>

1. Reads PROJECT.md, if there is one, and what already exists (`corkboard tree`, `corkboard list`).
2. Drafts the plan as a tree: the release (an existing one or a new one), its epics, their tasks and bugs with a line of description each, subtasks, priorities and blockers.
3. Waits for the user's approval or changes, then creates it with `corkboard release` and `corkboard new`, and prints `corkboard tree`.

It plans only. It writes no code.

### /corkboard:ui

Runs `corkboard ui --background`, which starts the web app as its own process, or finds the one already running for this repo, and prints its URL and process ID. Claude replies with the URL and that `kill <pid>` stops it. The web app keeps running after the session ends.

## Left out for now

- A status line showing the current item and how many are waiting on the user.
- A hook that checks commit messages for an item ID. The skill's habit should be enough to start with.
