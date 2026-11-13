# CLI

`corkboard` is how Claude makes structured changes to a repo's project data and asks project-wide questions in one call. The user can use it too. The files it reads and writes are described in [file-format.md](file-format.md).

## Rules for every command

- **Finding the project:** `corkboard` walks up from the current folder to the first `.project/config.yml`, the way git finds `.git`. If there's none, it fails with `no .project/ folder here or above. Run corkboard init to start one.` The one exception is `corkboard now`, which prints nothing and exits 0, so the session-start hook is harmless in other repos.
- **Who:** log lines are written as `claude` when the `CLAUDECODE` environment variable is set (Claude Code sets it in Claude's shells) and as `me` otherwise. Any write command takes `--as me` or `--as claude` to override.
- **Output:** plain text. Color only when output goes to a terminal. No JSON mode.
- **GitHub:** only `corkboard show` and `corkboard ui` contact GitHub, through `gh`, to read pull requests. Every other command works offline.
- **Fields:** always `field=value`. Lists are comma-separated, such as `labels=ui,board`. An empty value clears a field, such as `parent=`. Quote values with spaces: `title="New title"`.
- **Writes** print one line naming what changed and the file's path, such as `moved EX-12 to done .project/items/EX-12-drag-cards.md`. Files are written whole and swapped in, so the web app never reads half a file.
- **Warnings** start with `warning:` and don't stop the command. **Errors** are one line on stderr starting with `error:`, say how to fix the problem, and exit with code 1. For example: `error: "inprogress" isn't a status. Use one of: backlog, todo, in-progress, waiting, done, cancelled`.
- **Titles** in one-line output are cut to 50 characters with `…`.
- `corkboard help` lists the commands, and `corkboard <command> --help` explains one.

## Order of work

`corkboard next` and the Next up section of `corkboard now` use the same order.

Only tasks and bugs with status `todo`, owner `claude`, and nothing open in `blocked_by` count. They're ordered:

1. **Answered by you:** the item was `waiting`, and the user's reply moved it to `todo`. Their reply is the last log line.
2. **In the active release:** its own release or its epic's.
3. **By priority:** high, then medium, then low.
4. **By number:** lowest first.

## Commands

### `corkboard init [prefix=XX] [name="…"]`

Creates `.project/config.yml`. Folders are created when first needed.

- The suggested prefix is the first letter of each word in the repo's folder name, such as `claude-project` → `CP`. A one-word name gives its first three letters, such as `astro` → `AST`.
- The suggested name is the folder name in title case, such as `Corkboard`.
- If `.project/` already exists, it fails with `error: already set up: .project/config.yml`.

```
created .project/config.yml (prefix CP)
next: corkboard new epic "First epic"
```

### `corkboard now`

The session-start summary. It's at most 25 lines, and empty sections are left out.

```
Example · v0.1 active, due 2026-12-01 · 7/15 done

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

- **First line:** the project name, the active release, and done tasks and bugs out of the release's total, leaving out cancelled ones. With no active release it says `no active release`. The due date is left out when the release has none.
- **Unreadable files:** if any file in `.project/` couldn't be read, the second line says how many and to run `corkboard check`. Claude only sees what the session-start hook prints, so this can't go to stderr as a warning.
- **Waiting on you:** every `waiting` item, with the message from its last move to `waiting`, cut to 70 characters. At most 5 lines, then `…and 3 more: corkboard list status=waiting`.
- **In progress:** every `in-progress` task and bug. Epics are left out, since an epic is in progress whenever any of its work is. Items the user owns are marked `(you)`. Priority is shown only when high, and subtask progress only when there are subtasks. At most 5 lines, then `…and 2 more: corkboard list status=in-progress`.
- **Next up:** the first 3 items in the order of work.
- With nothing in any section, it prints the first line and `Nothing in progress or planned. Add work with corkboard new.`
- It never contacts GitHub, so it's fast and works offline.

### `corkboard next`

The first item in the order of work, printed the way `corkboard show` prints it, with one extra line first saying why it's next:

```
next because: answered by you
```

With nothing to do, it prints `nothing to do: no unblocked todo items owned by claude` and exits 0.

### `corkboard show <ID>`

One item with its context. Lines with nothing to show are left out.

```
EX-12 task · in-progress · high · claude
Drag cards between columns
path: .project/items/EX-12-drag-cards.md
epic: EX-3 Board view · release: v0.1 · labels: ui, board
blocked by: EX-9 Card component (todo)
blocks: EX-18 Keyboard shortcuts for the board (todo)
related: EX-13 Board column limits (todo)
mentioned in: docs/ui.md, EX-14

What and why, as written in the file.

Subtasks 1/3
  1 [x] Work out which column a card was dropped on
  2 [ ] Save the status change through corkboard
  3 [ ] Put the card back if saving fails

Development
  branch: ex-12-drag-cards
  PR #14 Drag cards between columns · open · checks passing
  a1b2c3d feat(board): detect drop column (EX-12)
  9f8e7d6 fix(board): keep card order on drop (EX-12)

Log (last 5 of 9)
  2026-11-12 14:20 claude: moved to in-progress
  …
```

- Subtasks are numbered for `corkboard sub`.
- The log shows its last 5 lines. The heading says how many there are in all.
- For an epic, a `Tasks 3/6` list of its tasks and bugs, as `status ID title`, takes the place of Subtasks.
- `mentioned in` lists docs and items whose text mentions the ID.
- Links show both sides: what this item stores (`blocked by`, `related`, `duplicate of`) and what other items store about it (`blocks`, `duplicated by`).
- **Development** lists the branch, the pull requests and the last 5 commits that mention the ID, as described in [file-format.md](file-format.md). The branch is any local branch whose name has the ID, and the section is left out when there's nothing to list. Pull requests are read with `gh`, with a 3-second limit. Without `gh`, a GitHub remote or a connection, the PR line is left out and nothing else changes.

### `corkboard list [field=value…] [--all]`

One line per item, sorted by number, then a count.

```
EX-12  task  in-progress  high    Drag cards between columns · epic EX-3 · ui, board
EX-13  task  todo         high    Board column limits · epic EX-3 · blocked
2 items
```

- Filters work on any header field. Several filters must all match. Commas inside one filter mean "any of", such as `status=todo,in-progress`.
- `labels=ui` matches items that have that label. `release=v0.1` matches the item's own release or its epic's.
- Done and cancelled items are hidden unless `--all` is given or a `status=` filter names them.

### `corkboard tree [RELEASE | none]`

A release, its epics, and each epic's tasks and bugs. With no argument it shows the active release. `none` shows items with no release.

```
v0.1 · active · due 2026-12-01 · 7/15 done
  EX-3 Board view · epic · in-progress · 3/6
    done         EX-10 Board columns
    in-progress  EX-12 Drag cards between columns · 1/3
    waiting      EX-14 Cards flicker on drop
    todo         EX-13 Board column limits
  EX-4 Docs pages · epic · todo · 0/4
    …
  No epic
    todo         EX-22 Fix typo in README
```

- Epics are in number order. Under each, items are sorted by status (done, in-progress, waiting, todo, backlog, cancelled) and then by number.
- Cancelled items are shown so dropped work stays visible.
- The due date is left out when the release has none.
- With no active release and no argument, it fails and lists the releases: `error: no active release. Name one: corkboard tree v0.2 (v0.1 released, v0.2 planned)`.

### `corkboard new <epic|task|bug> "Title" [field=value…]`

Creates an item.

- Defaults: `status=todo`, `priority=medium`, `owner=claude`, and `created` set to today.
- Fields that can be set: `status`, `priority`, `owner`, `parent`, `release`, `labels`, `blocked_by`, `related`, `duplicate_of`.
- When input is piped in, it becomes the body, so the description and a `## Subtasks` checklist can go in with one command. `corkboard` writes the `## Log` section itself, with a `created` line, so piped input can't contain one.
- It checks the new item the way `corkboard check` would and writes nothing if there's a problem.

```
corkboard new task "Board column limits" parent=EX-3 priority=high <<'EOF'
Cap how many cards a column shows before it scrolls.

## Subtasks
- [ ] Add a limit per column
- [ ] Show "+N more" at the bottom
EOF
```

```
created EX-18 .project/items/EX-18-board-column-limits.md
```

### `corkboard move <ID> <status> ["message"]`

Changes an item's status and logs `moved to <status>`, or `moved to <status>: <message>` with a message.

- Moving to `waiting` needs a message: the question or what to review.
- Moving an epic to `done` while it has open tasks warns and lists them. Moving a blocked item to `in-progress` warns and names the blockers.
- Moving to the status it already has does nothing and prints `EX-12 is already done`.

```
moved EX-12 to done .project/items/EX-12-drag-cards.md
```

### `corkboard set <ID> field=value…`

Changes header fields other than `id`, `created` and `status`. Status goes through `corkboard move`.

- Fields that can be set: `title`, `type`, `priority`, `owner`, `parent`, `release`, `labels`, `blocked_by`, `related`, `duplicate_of`. `type` can only switch between task and bug.
- Links are set the same way, such as `corkboard set EX-18 related=EX-9`.
- It logs one line, such as `set priority=high labels=ui,board`.
- Changing the title renames the file, and the printed path is the new one.

```
updated EX-12 .project/items/EX-12-drag-cards-between-columns.md
```

### `corkboard sub <ID> add "text"` · `done <N>` · `undo <N>`

Adds a subtask, checks one off or unchecks one, by its number in `corkboard show`. Only tasks and bugs have subtasks. `add` creates the `## Subtasks` section above the log if it's missing.

- Each change is logged: `added subtask: <text>`, `done subtask: <text>` or `reopened subtask: <text>`.
- To reword or remove a subtask, edit the file.

```
EX-12 subtasks 2/3 .project/items/EX-12-drag-cards.md
```

### `corkboard log <ID> "text"`

Adds a note to the item's log.

```
logged EX-12 .project/items/EX-12-drag-cards.md
```

### `corkboard release <NAME> [status=…] [date=YYYY-MM-DD]`

Creates a release, starting as `planned`, or updates one. Piped input becomes its goal text.

- Only one release can be active. Making a second one active fails: `error: v0.1 is already active. Release it first: corkboard release v0.1 status=released`.

```
created release v0.2 .project/releases/v0.2.md
```

### `corkboard check [--fix]`

Runs the checks in [file-format.md](file-format.md) and prints one problem per line, then a summary. Exits 1 if any problems are left.

```
EX-12-drag-cards.md: parent EX-99 doesn't exist
EX-7-old-name.md: file name doesn't match the title
42 items, 3 releases: 2 problems
```

`--fix` repairs only what's safe to repair, and lists the rest:

- **File names that don't match the title:** renamed.
- **Duplicate IDs:** the item with the later `created` date gets the next free number. References to the old number can't be told apart, since they could mean either item, so it lists them for review:

```
fixed: EX-12 was used twice. "Ctrl-K search" is now EX-31.
check these references to EX-12, which may have meant EX-31: EX-14 blocked_by, docs/ui.md
```

### `corkboard ui [--background]`

Starts the web app on localhost, prints its URL, and runs until stopped with Ctrl-C.

- It listens on 127.0.0.1, on port 4747, or the next free one up to 4766.
- If a server for this repo is already running on one of those ports, it prints that server's URL the same way and exits 0, so it's safe to run again.
- `--background` starts the server as its own process, waits until it answers, prints its URL and how to stop it, and exits. If one is already running for this repo, it prints the same two lines for that one. `/corkboard:ui` uses this.

```
Corkboard: http://localhost:4747
```

```
$ corkboard ui --background
Corkboard: http://localhost:4747
Running in the background as process 41873. Stop it with: kill 41873
```
