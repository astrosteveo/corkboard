# Corkboard

A lightweight issue tracker and wiki for one person working with Claude Code, kept as Markdown files in the repo.

## What it is

A Claude Code plugin with a small CLI (`corkboard`) and a local web app. Each repo keeps its releases, epics, tasks, subtasks and docs as Markdown files in a `.project/` folder. Claude reads and edits them with its normal tools and uses `corkboard` for structured changes. The user works in a browser tab on localhost: a home page showing where things stand, a board, a release view, a list, item pages and docs. Items link to each other and show the commits and pull requests that mention them. It covers what teams use Jira (issues, epics, releases) and Confluence (specs, decisions) for, kept local instead of in a hosted tracker or GitHub Issues.

## The problem

Each new Claude session starts without knowing where things stand. Plans, tasks and decisions end up spread across chats, TODO files and GitHub issues, and the user loses track of what's done, what's next and what Claude is waiting on them for.

## Who it's for

One developer working with Claude Code on their own repos. Not for teams.

## Goals

1. Claude knows where the project stands at the start of every session and keeps it up to date as it works, at a low token cost.
2. The user sees at a glance what's in progress, what's next, what Claude did, and what Claude is waiting on them for.
3. Work is organized the way it is in Jira: releases are made of epics, epics of tasks and bugs, tasks of subtasks, with labels across all of them and links between items. The user can open a release and see everything it contains.
4. Issues and docs live together as plain files next to the code, readable without the tool.
5. Each item shows the commits and pull requests that did its work.
6. Stays lightweight: one command to set up, and no server running for Claude to work.

## Non-goals

- Team features: other users, permissions, mentions, notifications, hosting or sync. Why: it's for one person and Claude.
- Syncing items with GitHub Issues or GitHub Projects. Why: it's meant as a local alternative to them, with the data in the repo.

## Success looks like

- At the start of a session, Claude knows what's in progress and what's next from one command, in under 500 tokens.
- The user opens the board and sees what Claude did since they last looked, without asking.
- The user opens a release and sees its epics, each epic's tasks and subtasks, and how far along each one is.
- Setting up a new repo takes one command.
- This project is tracked with itself.

## Failure looks like

- Keeping it up to date costs the user or Claude more time than it saves.
- The board stops matching reality, so the user stops trusting it.
- The user stops opening the UI.

## Priorities

1. Simple and lightweight
2. Cheap and reliable for Claude to use
3. A clear, pleasant UI
4. More features

## Constraints

- Runs on the user's Linux machine. The web app serves on localhost only.
- Project data is plain Markdown in the repo, readable and diffable in git without the tool.
- Claude must be able to work without a server running.
- `corkboard` and the web server use only Python 3.11+'s standard library, and the web app has no build step, so the plugin runs right after it installs.

## Decisions

- 2026-11-12: For one user plus Claude only. Why: the user works solo with Claude.
- 2026-11-12: One `.project/` folder per repo, no cross-repo dashboard for now. Why: simplest; a page listing several repos can come later, since it only means reading several folders.
- 2026-11-12: One Markdown file per item with a YAML header, not JSON. Why: most of the content is prose; small files keep Claude's reads and edits small, diff cleanly and render on GitHub.
- 2026-11-12: Claude makes structured changes (IDs, status moves, links, log lines) through the `corkboard` CLI and edits descriptions and docs directly. Why: the CLI does the bookkeeping so files stay correct, and it answers project-wide questions in one call.
- 2026-11-12: Turned down SQLite plus an MCP server as the store. Why: a database file doesn't diff or merge in git, Claude can't search the docs with its normal tools, and a server would have to be running.
- 2026-11-12: The UI is a web app in a browser tab on localhost. Why: simplest to build well, and it allows drag-and-drop and richer layouts than a terminal.
- 2026-11-12: Readable sequential IDs like `EX-12`. Why: with one user, collisions are rare, and `corkboard check` renumbers duplicates after a merge.
- 2026-11-12: Build our own instead of adopting or forking Backlog.md. Why: to get the release → epic → task → subtask structure and its views exactly the way the user wants, built around Claude Code.
- 2026-11-12: Items nest as release → epic → task or bug → subtask, and any item can have labels. Why: the user wants to see a release as the epics it delivered and the work under each.
- 2026-11-12: No "story" type, only task. Why: for one person and Claude, story and task mean the same thing in practice.
- 2026-11-12: The file format is specified in `.project/docs/file-format.md`. Why: Claude, `corkboard` and the web app all read and write the same files.
- 2026-11-12: Subtasks are checklist lines inside their task or bug, not their own files. Why: cheaper for Claude to update and no extra files; a subtask that needs its own owner or log becomes a task.
- 2026-11-12: Statuses are backlog, todo, in-progress, waiting, done and cancelled. Why: `waiting` covers everything Claude needs from the user, questions and reviews alike, and `cancelled` keeps dropped work visible instead of deleted.
- 2026-11-12: Item files are named like `EX-12-drag-cards.md`, and the ID prefix is set per repo in `.project/config.yml`. Why: the names stay readable in diffs and search results, and each repo gets its own key, like a Jira project.
- 2026-11-12: The CLI's commands and output are specified in `.project/docs/cli.md`. Output is plain text with no JSON mode. Why: text is cheaper for Claude to read, and the web app uses the shared core library instead of the CLI.
- 2026-11-12: `corkboard now` is the session-start summary, at most 25 lines, and items the user just answered come first in Next up. Why: keeps each session's starting context under 500 tokens, and Claude picks up the user's answers right away.
- 2026-11-12: `corkboard` tells Claude and the user apart by the `CLAUDECODE` variable Claude Code sets in Claude's shells. Why: log lines get the right author with nothing to pass in.
- 2026-11-12: The web app's screens are specified in `.project/docs/ui.md`: Now, Board, Releases, List, Item and Docs, plus Ctrl-K search. Why: the fewest screens that cover the goals; List gives the backlog a home, since the board hides it.
- 2026-11-12: Cards can't be reordered by hand; they're sorted by priority, then number. Why: manual order would need a position field on every item and rewrite many files on each drag.
- 2026-11-12: "Since you last looked" clears only when the user clicks Mark seen. Why: glancing at the tab shouldn't lose the list of what Claude did.
- 2026-11-12: Items link as blocked by, related to or duplicate of. Each link is stored on one item and shown on both. Why: adding a link changes one file, and the two sides can't disagree.
- 2026-11-12: Commits and pull requests belong to an item when its ID appears in them, and are never stored in item files. Pull requests are read with `gh` only when shown, and `corkboard now` never contacts GitHub. Why: nothing in git goes stale, everything else works offline, and sessions start fast.
- 2026-11-12: Claude puts the item ID in commit messages and PR titles, names branches like `ex-12-drag-cards`, and moves the item to `waiting` when it opens a PR. Why: that's what matches commits and PRs to items, and it puts PRs in the user's Waiting on you list.
- 2026-11-12: A merged PR doesn't close its item automatically; the Now page offers a one-click Mark done. Why: the tool never changes an item unless the user or Claude does it.
- 2026-11-12: The Claude Code plugin is specified in `.project/docs/plugin.md`: `corkboard` in its `bin/`, a session-start hook that runs `corkboard now`, a `track` skill with the workflow, and `/corkboard:next`, `/corkboard:done`, `/corkboard:plan` and `/corkboard:ui`. Why: the fewest pieces that keep Claude on track, and every session starts knowing where things stand.
- 2026-11-12: `corkboard` ships inside the plugin, so it must run with no install step. This repo is the plugin, listed in the astro-plugins marketplace by its GitHub repo. Why: one install, and the CLI always matches the plugin's version.
- 2026-11-12: Every change Claude commits gets an item, except trivial fixes such as a typo. Why: the board has to match reality, without the upkeep costing more than it saves.
- 2026-11-12: One-line decisions stay in PROJECT.md; a decision that needs more than a line gets a page in `.project/docs/decisions/`, linked from its one-liner. Why: PROJECT.md already loads into every session, and the two would otherwise overlap.
- 2026-11-12: No coordination with the github-tracking plugin. Why: it's being retired, and a repo uses one or the other.
- 2026-11-12: The CLI and web server are Python 3.11+ with only the standard library. The web app is plain HTML, CSS and JavaScript, with Preact, htm and marked committed as single files. Turned down TypeScript (Node isn't installed, and it needs a build) and Go (it needs a committed binary or a release step). Why: the plugin must run right after it installs, with nothing to install and no build output committed, the way the user's other plugins already work.
- 2026-11-12: Item and release headers use a strict subset of YAML, specified in `.project/docs/file-format.md`. Why: the standard library has no YAML parser, and headers must stay valid YAML so GitHub still renders them.
- 2026-11-12: Markdown renders with raw HTML turned off, and the web server only accepts changes from its own page. Why: the app can write files, so a doc in a cloned repo must never be able to run a script in it.
- 2026-11-12: The name is Corkboard. The CLI, the plugin and its slash commands are all `corkboard` (`corkboard now`, `/corkboard:next`), and this repo's ID prefix is `CB`. Turned down Docket and Cairn, which several trackers for AI agents already use. Why: a board you pin cards and notes to covers both the board and the docs, and no tracker in this niche uses the name.
- 2026-11-12: v0.1 is the Claude side (core library, CLI, plugin), v0.2 the web app, and v0.3 docs, the List view, links and GitHub. Why: being cheap and reliable for Claude ranks above the UI, the web app builds on a core that real use has proven, and Corkboard tracks its own build from v0.1.
- 2026-11-12: Until CB-15 adds `new`, `move`, `sub` and `log`, this repo's item files are edited by hand in the strict format; after that, only through `corkboard`. Why: the project tracks itself from the start, and the hand-editing stretch stays short.
- 2026-11-12: The repo is private on GitHub (astrosteveo/corkboard). Each item is built on its own branch and merged through a PR, with CI running the tests and ruff. Why: the user's CI runs on GitHub, and the plugin's own workflow expects PRs.
- 2026-11-12: A release's `date` is optional, and v0.1 to v0.3 have none. Why: it's a hobby project without deadlines.
- 2026-11-12: Examples in specs and docs use the prefix `EX`, such as `EX-12`, never this repo's own `CB`. Why: any item ID in a doc counts as a mention of that item, so an example with a real ID would link to the wrong item.
- 2026-11-12: Claude squash-merges each PR itself once CI passes, and moves on to the next item. Why: the user chose not to review every PR first; they can review any of them afterwards on GitHub.
- 2026-11-12: Work on Corkboard's own repo doesn't load the plugin from this folder (`--plugin-dir .`); it uses `bin/corkboard` directly. Plugin behavior is tried in a separate test repo with the plugin loaded from a copy. Why: Claude Code won't let a session edit the files of a plugin it has loaded, so loading this folder as the plugin blocks every edit to it.
- 2026-11-12: Corkboard is public on GitHub under the MIT license, and installs from the astro-plugins marketplace. Turned down a private marketplace in this repo. Why: the user chose to publish; MIT and astro-plugins match their other plugins.
- 2026-11-12: `corkboard` in your own terminal comes from `uv tool install git+https://github.com/astrosteveo/corkboard`, packaged by `pyproject.toml` with the same version as the plugin. Turned down a symlink into a clone. Why: a new user shouldn't need a clone, and a symlink breaks when the folder moves; the plugin still needs no install step.
- 2026-11-12: The web app's files live in `corkboard/web/`, inside the Python package, not in a top-level `web/`. Why: `uv tool install` only installs the package, so `corkboard ui` from that copy would have no page.
- 2026-11-13: `/corkboard:ui` runs `corkboard ui --background`, which starts the server as its own detached process and exits once it answers. Why: a skill can't keep a foreground server running, and can't count on reading a background shell's output.
- 2026-11-13: Card badges and Merged, not done count only an item's own pull requests, with its ID in the title or branch name. Why: pull request bodies name other items, such as the epic or follow-ups, which marked them merged when they weren't.
- 2026-11-12: `corkboard ui` finds a server already running for the repo by asking each port from 4747 to 4766 which `.project/` it serves, instead of keeping a file with its port. Why: nothing to go stale after a crash, and nothing new in the repo to ignore in git.

## Open questions

- Leave out sprints and time tracking for v1? (Releases replace milestones.)

## Glossary

- **Release:** a named version, such as `v0.2`, that groups the epics shipping in it.
- **Epic:** a large piece of work made of tasks and bugs.
- **Task / Bug:** one piece of work, or one defect to fix. Can have subtasks.
- **Subtask:** a checklist line inside a task or bug.
- **Label:** a free-form tag on any item, such as `ui` or `cli`, used for filtering.
- **Link:** a blocked by, related to or duplicate of connection between two items.
- **Item:** an epic, task or bug, each one file in `.project/items/`.
- **Doc:** a Markdown page in `.project/docs/`. Decisions that need more than a line are docs in `.project/docs/decisions/`.
- **Owner:** `me` or `claude`, whoever does the item.
- **Waiting on you:** items where Claude needs the user's answer or approval before it can go on.
- **Now view:** the web app's home page: what Claude is working on, what's next, and what's waiting on you.
- **`corkboard`:** the CLI. The plugin and its slash commands share the name, as in `/corkboard:next`.

## Status

v0.1 and v0.2 are released, as version 0.2.0. v0.1 is the core library, the `corkboard` command and the Claude Code plugin; the repo is public under MIT, installs from astro-plugins, and Corkboard tracks its own work. v0.2 is the web app (CB-23 to CB-39): `corkboard ui` and `/corkboard:ui` serve the Now page, the board with drag and drop, the releases view, the item panel and the new item form, with live updates and the safety rules from `.project/docs/ui.md`. Its look follows the mockup the user likes (https://claude.ai/artifact/7WHHdLRhsnAn4oUeEuBw1k). v0.3 is active and planned as CB-40 to CB-49: commits, pull requests and links in `corkboard show` and the item panel, PR badges on cards, the docs pages, the List view and Ctrl-K search. Done so far: `corkboard show` lists an item's branch, commits (CB-40) and pull requests with their checks (CB-41), the item panel shows both sides of every link, adds new ones (CB-42) and removes them (CB-50), and its branch, pull requests and commits (CB-43). Board cards show their newest pull request, and the Now page lists items whose pull request merged while they're open (CB-44). Next: CB-51, refusing blocking cycles in `corkboard set`.
