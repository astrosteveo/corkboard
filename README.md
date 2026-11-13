# Corkboard

A lightweight issue tracker and wiki for one person working with Claude Code, kept as Markdown files in the repo.

Corkboard keeps a repo's releases, epics, tasks, bugs and docs as Markdown files in a `.project/` folder, next to the code. Claude reads and changes them through the `corkboard` command, which does the bookkeeping: IDs, file names, and log lines with who and when. Every session starts with a short summary of where things stand, so Claude knows what's in progress, what's next and what's waiting on you without being told.

The files are plain Markdown with a small header, so they read fine on GitHub, diff cleanly, and need nothing running. A web app with a board, a release view and the docs is planned for v0.2.

## Get started

You need Claude Code and Python 3.11 or newer. Nothing else gets installed.

1. **Install the plugin.** In Claude Code, run:

   ```
   /plugin install corkboard --marketplace astrosteveo/astro-plugins
   ```

   Then start a new session, so the plugin loads.

2. **Let Claude run `corkboard` without asking each time.** A plugin can't add permission rules for you, so add this to `~/.claude/settings.json`:

   ```json
   {
     "permissions": {
       "allow": ["Bash(corkboard *)"]
     }
   }
   ```

3. **Set up a repo.** In the repo's folder, ask Claude to set up Corkboard. It runs `corkboard init`, which creates `.project/config.yml` with a prefix for the repo's IDs, taken from the folder's name: `claude-project` gives `CP-1`, `CP-2` and so on. Commit `.project/` along with your code.

4. **Plan some work.** For example:

   ```
   /corkboard:plan Add a dark mode to the settings page
   ```

   Claude drafts a release, epics and tasks with subtasks, and creates them once you approve.

5. **Work through it.** `/corkboard:next` starts the next task and `/corkboard:done` finishes it. From then on, every session starts with a summary of what's in progress, what's next and what's waiting on you.

### Run corkboard in your own terminal

This is optional. The plugin gives `corkboard` to Claude, not to your shell. To run it yourself, install it as a tool:

```
uv tool install git+https://github.com/astrosteveo/corkboard
```

`pipx install git+https://github.com/astrosteveo/corkboard` works too. Then `corkboard now`, `corkboard tree` and the rest work in any repo with a `.project/` folder.

### Update

```
claude plugin update corkboard@astro-plugins   # the plugin Claude uses
uv tool upgrade corkboard                       # the terminal command, if you installed it
```

The plugin's update takes effect in new sessions.

## Use

| Command | What it does |
| --- | --- |
| `/corkboard:plan <goal>` | Drafts a release, epics, tasks and subtasks for a goal, and creates them once you approve |
| `/corkboard:next [ID]` | Starts the next item, or the one you name: moves it to in progress, makes a branch, and gets going |
| `/corkboard:done [ID]` | Finishes the current item: checks its subtasks, runs the tests, commits, and opens a PR or closes the item |

You don't have to use the commands. Claude loads the `corkboard:track` skill on its own when it starts, finishes or plans work. It makes an item for every change it commits (trivial fixes aside), puts the item's ID in commit messages and branch names, ticks subtasks as it goes, and logs choices worth keeping. When Claude needs your answer, it asks in chat and moves the item to `waiting`, so the question is still on the board if you step away.

## What Claude sees when a session starts

```
Example · v0.1 active · 7/15 done

Waiting on you (1)
  EX-14 Cards flicker on drop: "debounce, or rebuild the column?"

In progress (2)
  EX-12 Drag cards between columns · high · 1/3
  EX-21 Write the README (you)

Next up
  EX-16 Column header menu · answered by you
  EX-13 Board column limits · high
  EX-19 Release view

Details: corkboard show <ID>
```

It's at most 25 lines, about a few hundred tokens, and nothing is added in a repo without `.project/`.

## The corkboard command

| Command | What it does |
| --- | --- |
| `corkboard now` | The summary above |
| `corkboard next` | The item to do next, in full |
| `corkboard show <ID>` | One item: its epic, release, links, subtasks and recent log |
| `corkboard list [field=value…]` | One line per item, with filters such as `status=todo labels=ui` |
| `corkboard tree [release]` | A release's epics and their tasks, with progress |
| `corkboard new <epic\|task\|bug> "Title" [field=value…]` | Creates an item; text piped in becomes its description and subtasks |
| `corkboard move <ID> <status> ["message"]` | Changes its status: backlog, todo, in-progress, waiting, done or cancelled |
| `corkboard sub <ID> add "text"` / `done <N>` / `undo <N>` | Adds, ticks or unticks a subtask |
| `corkboard log <ID> "text"` | Adds a note to its log |
| `corkboard set <ID> field=value…` | Changes its title, priority, owner, epic, release, labels or links |
| `corkboard release <name> [status=…] [date=…]` | Creates or changes a release |
| `corkboard check [--fix]` | Finds files that break the format, and repairs the safe ones |
| `corkboard init` | Starts `.project/` in this folder |

`corkboard help` lists them, and `corkboard <command> --help` explains one.

## The files

```
.project/
  config.yml                  the project's name and ID prefix
  releases/v0.1.md            one file per release
  items/EX-12-drag-cards.md   one file per epic, task or bug
  docs/                       specs and notes, as plain Markdown
```

An item looks like this:

```markdown
---
id: EX-12
type: task
title: Drag cards between columns
status: in-progress
priority: high
owner: claude
created: 2026-11-12
parent: EX-3
labels: [ui, board]
---
What and why, in a few lines.

## Subtasks
- [x] Work out which column a card was dropped on
- [ ] Save the status change

## Log
- 2026-11-12 14:03 me: created
- 2026-11-12 14:20 claude: moved to in-progress
```

The full format is in [.project/docs/file-format.md](.project/docs/file-format.md). The command's behavior is in [cli.md](.project/docs/cli.md), the plugin's in [plugin.md](.project/docs/plugin.md), and the planned web app's in [ui.md](.project/docs/ui.md). What the project is for, and the decisions behind it, are in [PROJECT.md](PROJECT.md). Corkboard tracks its own work: its items are in [.project/items/](.project/items/).

## Development

Corkboard runs on Python 3.11 or newer and uses only the standard library, so it needs nothing installed. The formatter and linter run through `uvx`.

```
python3 -m unittest discover -s tests                   # run the tests
python3 -m unittest discover -s tests -p test_cli.py    # run one test file
uvx ruff format                                         # format the code
uvx ruff check                                          # lint
```

CI runs the tests and both ruff checks on every pull request, and also builds the package and runs `corkboard help`.

To run your working copy as `corkboard` from anywhere, install it in editable mode: `uv tool install --editable .`

Things that aren't obvious from the code:

- **Don't load the plugin from the folder you're editing** (`claude --plugin-dir .`). Claude Code won't let a session edit a plugin it has loaded. Work on this repo with `bin/corkboard`, and try plugin changes in a separate test repo with the plugin loaded from a copy.
- **The specs in `.project/docs/` are the contract.** Change a spec in the same pull request as the code. The output tests are built from the examples in `cli.md`.
- **Examples in docs use the prefix `EX-`,** never this repo's `CB-`. Any ID in a doc counts as a mention of that item.
- **Bump the version in `.claude-plugin/plugin.json` and `pyproject.toml` together** when a change should reach installed copies. `claude plugin update` only updates when the version changes, and a test checks the two match.
- **Corkboard tracks its own work.** Each change gets an item in `.project/items/`, created and changed with `corkboard`, with its ID in the branch name and commit messages.
- **Tests mustn't depend on this repo's own item state,** such as which release is active, since that changes as the work moves.

## License

MIT
