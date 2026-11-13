# CLI

`cpm` is how Claude makes structured changes to a repo's project data and asks project-wide questions in one call. The user can use it too. The files it reads and writes are described in [file-format.md](file-format.md).

## Rules for every command

- **Finding the project:** `cpm` walks up from the current folder to the first `.project/config.yml`, the way git finds `.git`. If there's none, it fails with `no .project/ folder here or above. Run cpm init to start one.` The one exception is `cpm now`, which prints nothing and exits 0, so the session-start hook is harmless in other repos.
- **Who:** log lines are written as `claude` when the `CLAUDECODE` environment variable is set (Claude Code sets it in Claude's shells) and as `me` otherwise. Any write command takes `--as me` or `--as claude` to override.
- **Output:** plain text. Color only when output goes to a terminal. No JSON mode.
- **GitHub:** only `cpm show` and `cpm ui` contact GitHub, through `gh`, to read pull requests. Every other command works offline.
- **Fields:** always `field=value`. Lists are comma-separated, such as `labels=ui,board`. An empty value clears a field, such as `parent=`. Quote values with spaces: `title="New title"`.
- **Writes** print one line naming what changed and the file's path, such as `moved CP-12 to done .project/items/CP-12-drag-cards.md`. Files are written whole and swapped in, so the web app never reads half a file.
- **Warnings** start with `warning:` and don't stop the command. **Errors** are one line on stderr starting with `error:`, say how to fix the problem, and exit with code 1. For example: `error: "inprogress" isn't a status. Use one of: backlog, todo, in-progress, waiting, done, cancelled`.
- **Titles** in one-line output are cut to 50 characters with `…`.
- `cpm help` lists the commands, and `cpm <command> --help` explains one.

## Order of work

`cpm next` and the Next up section of `cpm now` use the same order.

Only tasks and bugs with status `todo`, owner `claude`, and nothing open in `blocked_by` count. They're ordered:

1. **Answered by you:** the item was `waiting`, and the user's reply moved it to `todo`. Their reply is the last log line.
2. **In the active release:** its own release or its epic's.
3. **By priority:** high, then medium, then low.
4. **By number:** lowest first.

## Commands

### `cpm init [prefix=XX] [name="…"]`

Creates `.project/config.yml`. Folders are created when first needed.

- The suggested prefix is the first letter of each word in the repo's folder name, such as `claude-project` → `CP`. A one-word name gives its first three letters, such as `astro` → `AST`.
- The suggested name is the folder name in title case, such as `Claude Project`.
- If `.project/` already exists, it fails with `error: already set up: .project/config.yml`.

```
created .project/config.yml (prefix CP)
next: cpm new epic "First epic"
```

### `cpm now`

The session-start summary. It's at most 25 lines, and empty sections are left out.

```
Claude Project · v0.1 active, due 2026-12-01 · 7/15 done

Waiting on you (1)
  CP-14 Cards flicker on drop: "debounce, or rebuild the column?"

In progress (2)
  CP-12 Drag cards between columns · high · 1/3
  CP-21 Write the README (you)

Next up
  CP-16 Column header menu · answered by you
  CP-13 Board column limits · high
  CP-19 Release view

Details: cpm show <ID>
```

- **First line:** the project name, the active release, and done tasks and bugs out of the release's total, leaving out cancelled ones. With no active release it says `no active release`.
- **Waiting on you:** every `waiting` item, with the question from its last log line, cut to 70 characters. At most 5 lines, then `…and 3 more: cpm list status=waiting`.
- **In progress:** every `in-progress` item. Items the user owns are marked `(you)`. Priority is shown only when high, and subtask progress only when there are subtasks. At most 5 lines.
- **Next up:** the first 3 items in the order of work.
- With nothing in any section, it prints the first line and `Nothing in progress or planned. Add work with cpm new.`
- It never contacts GitHub, so it's fast and works offline.

### `cpm next`

The first item in the order of work, printed the way `cpm show` prints it, with one extra line first saying why it's next:

```
next because: answered by you
```

With nothing to do, it prints `nothing to do: no unblocked todo items owned by claude` and exits 0.

### `cpm show <ID>`

One item with its context. Lines with nothing to show are left out.

```
CP-12 task · in-progress · high · claude
Drag cards between columns
path: .project/items/CP-12-drag-cards.md
epic: CP-3 Board view · release: v0.1 · labels: ui, board
blocked by: CP-9 Card component (todo)
blocks: CP-18 Keyboard shortcuts for the board (todo)
related: CP-13 Board column limits (todo)
mentioned in: docs/ui.md, CP-14

What and why, as written in the file.

Subtasks 1/3
  1 [x] Work out which column a card was dropped on
  2 [ ] Save the status change through cpm
  3 [ ] Put the card back if saving fails

Development
  branch: cp-12-drag-cards
  PR #14 Drag cards between columns · open · checks passing
  a1b2c3d feat(board): detect drop column (CP-12)
  9f8e7d6 fix(board): keep card order on drop (CP-12)

Log (last 5 of 9)
  2026-11-12 14:20 claude: moved to in-progress
  …
```

- Subtasks are numbered for `cpm sub`.
- The log shows its last 5 lines. The heading says how many there are in all.
- For an epic, a `Tasks 3/6` list of its tasks and bugs, as `status ID title`, takes the place of Subtasks.
- `mentioned in` lists docs and items whose text mentions the ID.
- Links show both sides: what this item stores (`blocked by`, `related`, `duplicate of`) and what other items store about it (`blocks`, `duplicated by`).
- **Development** lists the branch, the pull requests and the last 5 commits that mention the ID, as described in [file-format.md](file-format.md). Pull requests are read with `gh`, with a 3-second limit. Without `gh`, a GitHub remote or a connection, the PR line is left out and nothing else changes.

### `cpm list [field=value…] [--all]`

One line per item, sorted by number, then a count.

```
CP-12  task  in-progress  high    Drag cards between columns · epic CP-3 · ui, board
CP-13  task  todo         high    Board column limits · epic CP-3 · blocked
2 items
```

- Filters work on any header field. Several filters must all match. Commas inside one filter mean "any of", such as `status=todo,in-progress`.
- `labels=ui` matches items that have that label. `release=v0.1` matches the item's own release or its epic's.
- Done and cancelled items are hidden unless `--all` is given or a `status=` filter names them.

### `cpm tree [RELEASE | none]`

A release, its epics, and each epic's tasks and bugs. With no argument it shows the active release. `none` shows items with no release.

```
v0.1 · active · due 2026-12-01 · 7/15 done
  CP-3 Board view · epic · in-progress · 3/6
    done         CP-10 Board columns
    in-progress  CP-12 Drag cards between columns · 1/3
    waiting      CP-14 Cards flicker on drop
    todo         CP-13 Board column limits
  CP-4 Docs pages · epic · todo · 0/4
    …
  No epic
    todo         CP-22 Fix typo in README
```

- Epics are in number order. Under each, items are sorted by status (done, in-progress, waiting, todo, backlog, cancelled) and then by number.
- Cancelled items are shown so dropped work stays visible.
- With no active release and no argument, it fails and lists the releases: `error: no active release. Name one: cpm tree v0.2 (v0.1 released, v0.2 planned)`.

### `cpm new <epic|task|bug> "Title" [field=value…]`

Creates an item.

- Defaults: `status=todo`, `priority=medium`, `owner=claude`, and `created` set to today.
- Fields that can be set: `status`, `priority`, `owner`, `parent`, `release`, `labels`, `blocked_by`, `related`, `duplicate_of`.
- When input is piped in, it becomes the body, so the description and a `## Subtasks` checklist can go in with one command. `cpm` writes the `## Log` section itself, with a `created` line, so piped input can't contain one.
- It checks the new item the way `cpm check` would and writes nothing if there's a problem.

```
cpm new task "Board column limits" parent=CP-3 priority=high <<'EOF'
Cap how many cards a column shows before it scrolls.

## Subtasks
- [ ] Add a limit per column
- [ ] Show "+N more" at the bottom
EOF
```

```
created CP-18 .project/items/CP-18-board-column-limits.md
```

### `cpm move <ID> <status> ["message"]`

Changes an item's status and logs `moved to <status>`, or `moved to <status>: <message>` with a message.

- Moving to `waiting` needs a message: the question or what to review.
- Moving an epic to `done` while it has open tasks warns and lists them. Moving a blocked item to `in-progress` warns and names the blockers.
- Moving to the status it already has does nothing and prints `CP-12 is already done`.

```
moved CP-12 to done .project/items/CP-12-drag-cards.md
```

### `cpm set <ID> field=value…`

Changes header fields other than `id`, `created` and `status`. Status goes through `cpm move`.

- Fields that can be set: `title`, `type`, `priority`, `owner`, `parent`, `release`, `labels`, `blocked_by`, `related`, `duplicate_of`. `type` can only switch between task and bug.
- Links are set the same way, such as `cpm set CP-18 related=CP-9`.
- It logs one line, such as `set priority=high labels=ui,board`.
- Changing the title renames the file, and the printed path is the new one.

```
updated CP-12 .project/items/CP-12-drag-cards-between-columns.md
```

### `cpm sub <ID> add "text"` · `done <N>` · `undo <N>`

Adds a subtask, checks one off or unchecks one, by its number in `cpm show`. Only tasks and bugs have subtasks. `add` creates the `## Subtasks` section above the log if it's missing.

- Each change is logged: `added subtask: <text>`, `done subtask: <text>` or `reopened subtask: <text>`.
- To reword or remove a subtask, edit the file.

```
CP-12 subtasks 2/3 .project/items/CP-12-drag-cards.md
```

### `cpm log <ID> "text"`

Adds a note to the item's log.

```
logged CP-12 .project/items/CP-12-drag-cards.md
```

### `cpm release <NAME> [status=…] [date=YYYY-MM-DD]`

Creates a release, starting as `planned`, or updates one. Piped input becomes its goal text.

- Only one release can be active. Making a second one active fails: `error: v0.1 is already active. Release it first: cpm release v0.1 status=released`.

```
created release v0.2 .project/releases/v0.2.md
```

### `cpm check [--fix]`

Runs the checks in [file-format.md](file-format.md) and prints one problem per line, then a summary. Exits 1 if any problems are left.

```
CP-12-drag-cards.md: parent CP-99 doesn't exist
CP-7-old-name.md: file name doesn't match the title
42 items, 3 releases: 2 problems
```

`--fix` repairs only what's safe to repair, and lists the rest:

- **File names that don't match the title:** renamed.
- **Duplicate IDs:** the item with the later `created` date gets the next free number. References to the old number can't be told apart, since they could mean either item, so it lists them for review:

```
fixed: CP-12 was used twice. "Ctrl-K search" is now CP-31.
check these references to CP-12, which may have meant CP-31: CP-14 blocked_by, docs/ui.md
```

### `cpm ui`

Starts the web app on localhost, prints its URL, and runs until stopped with Ctrl-C. If the port is taken, it uses the next free one.

```
Claude Project: http://localhost:4747
```
