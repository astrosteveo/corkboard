# Claude Project (working title)

A lightweight issue tracker and wiki for one person working with Claude Code, kept as Markdown files in the repo.

## What it is

A Claude Code plugin with a small CLI (`cpm`) and a local web app. Each repo keeps its releases, epics, tasks, subtasks and docs as Markdown files in a `.project/` folder. Claude reads and edits them with its normal tools and uses `cpm` for structured changes. The user works in a browser tab on localhost: a home page showing where things stand, a board, a release view, a list, item pages and docs. Items link to each other and show the commits and pull requests that mention them. It covers what teams use Jira (issues, epics, releases) and Confluence (specs, decisions) for, kept local instead of in a hosted tracker or GitHub Issues.

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
- `cpm` and the web server use only Python 3.11+'s standard library, and the web app has no build step, so the plugin runs right after it installs.

## Decisions

- 2026-11-12: For one user plus Claude only. Why: the user works solo with Claude.
- 2026-11-12: One `.project/` folder per repo, no cross-repo dashboard for now. Why: simplest; a page listing several repos can come later, since it only means reading several folders.
- 2026-11-12: One Markdown file per item with a YAML header, not JSON. Why: most of the content is prose; small files keep Claude's reads and edits small, diff cleanly and render on GitHub.
- 2026-11-12: Claude makes structured changes (IDs, status moves, links, log lines) through the `cpm` CLI and edits descriptions and docs directly. Why: the CLI does the bookkeeping so files stay correct, and it answers project-wide questions in one call.
- 2026-11-12: Turned down SQLite plus an MCP server as the store. Why: a database file doesn't diff or merge in git, Claude can't search the docs with its normal tools, and a server would have to be running.
- 2026-11-12: The UI is a web app in a browser tab on localhost. Why: simplest to build well, and it allows drag-and-drop and richer layouts than a terminal.
- 2026-11-12: Readable sequential IDs like `CP-12`. Why: with one user, collisions are rare, and `cpm check` renumbers duplicates after a merge.
- 2026-11-12: Build our own instead of adopting or forking Backlog.md. Why: to get the release → epic → task → subtask structure and its views exactly the way the user wants, built around Claude Code.
- 2026-11-12: Items nest as release → epic → task or bug → subtask, and any item can have labels. Why: the user wants to see a release as the epics it delivered and the work under each.
- 2026-11-12: No "story" type, only task. Why: for one person and Claude, story and task mean the same thing in practice.
- 2026-11-12: The file format is specified in `.project/docs/file-format.md`. Why: Claude, `cpm` and the web app all read and write the same files.
- 2026-11-12: Subtasks are checklist lines inside their task or bug, not their own files. Why: cheaper for Claude to update and no extra files; a subtask that needs its own owner or log becomes a task.
- 2026-11-12: Statuses are backlog, todo, in-progress, waiting, done and cancelled. Why: `waiting` covers everything Claude needs from the user, questions and reviews alike, and `cancelled` keeps dropped work visible instead of deleted.
- 2026-11-12: Item files are named like `CP-12-drag-cards.md`, and the ID prefix is set per repo in `.project/config.yml`. Why: the names stay readable in diffs and search results, and each repo gets its own key, like a Jira project.
- 2026-11-12: The CLI's commands and output are specified in `.project/docs/cli.md`. Output is plain text with no JSON mode. Why: text is cheaper for Claude to read, and the web app uses the shared core library instead of the CLI.
- 2026-11-12: `cpm now` is the session-start summary, at most 25 lines, and items the user just answered come first in Next up. Why: keeps each session's starting context under 500 tokens, and Claude picks up the user's answers right away.
- 2026-11-12: `cpm` tells Claude and the user apart by the `CLAUDECODE` variable Claude Code sets in Claude's shells. Why: log lines get the right author with nothing to pass in.
- 2026-11-12: The web app's screens are specified in `.project/docs/ui.md`: Now, Board, Releases, List, Item and Docs, plus Ctrl-K search. Why: the fewest screens that cover the goals; List gives the backlog a home, since the board hides it.
- 2026-11-12: Cards can't be reordered by hand; they're sorted by priority, then number. Why: manual order would need a position field on every item and rewrite many files on each drag.
- 2026-11-12: "Since you last looked" clears only when the user clicks Mark seen. Why: glancing at the tab shouldn't lose the list of what Claude did.
- 2026-11-12: Items link as blocked by, related to or duplicate of. Each link is stored on one item and shown on both. Why: adding a link changes one file, and the two sides can't disagree.
- 2026-11-12: Commits and pull requests belong to an item when its ID appears in them, and are never stored in item files. Pull requests are read with `gh` only when shown, and `cpm now` never contacts GitHub. Why: nothing in git goes stale, everything else works offline, and sessions start fast.
- 2026-11-12: Claude puts the item ID in commit messages and PR titles, names branches like `cp-12-drag-cards`, and moves the item to `waiting` when it opens a PR. Why: that's what matches commits and PRs to items, and it puts PRs in the user's Waiting on you list.
- 2026-11-12: A merged PR doesn't close its item automatically; the Now page offers a one-click Mark done. Why: the tool never changes an item unless the user or Claude does it.
- 2026-11-12: The Claude Code plugin is specified in `.project/docs/plugin.md`: `cpm` in its `bin/`, a session-start hook that runs `cpm now`, a `track` skill with the workflow, and `/cp:next`, `/cp:done`, `/cp:plan` and `/cp:ui`. Why: the fewest pieces that keep Claude on track, and every session starts knowing where things stand.
- 2026-11-12: `cpm` ships inside the plugin, so it must run with no install step. This repo is the plugin, listed in the astro-plugins marketplace by its GitHub repo. Why: one install, and the CLI always matches the plugin's version.
- 2026-11-12: Every change Claude commits gets an item, except trivial fixes such as a typo. Why: the board has to match reality, without the upkeep costing more than it saves.
- 2026-11-12: One-line decisions stay in PROJECT.md; a decision that needs more than a line gets a page in `.project/docs/decisions/`, linked from its one-liner. Why: PROJECT.md already loads into every session, and the two would otherwise overlap.
- 2026-11-12: No coordination with the github-tracking plugin. Why: it's being retired, and a repo uses one or the other.
- 2026-11-12: The CLI and web server are Python 3.11+ with only the standard library. The web app is plain HTML, CSS and JavaScript, with Preact, htm and marked committed as single files. Turned down TypeScript (Node isn't installed, and it needs a build) and Go (it needs a committed binary or a release step). Why: the plugin must run right after it installs, with nothing to install and no build output committed, the way the user's other plugins already work.
- 2026-11-12: Item and release headers use a strict subset of YAML, specified in `.project/docs/file-format.md`. Why: the standard library has no YAML parser, and headers must stay valid YAML so GitHub still renders them.
- 2026-11-12: Markdown renders with raw HTML turned off, and the web server only accepts changes from its own page. Why: the app can write files, so a doc in a cloned repo must never be able to run a script in it.

## Open questions

- What's the real name? "Claude Project" is a placeholder, and "Projects" is already a claude.ai feature.
- Will it be published, and under what license?
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
- **`cpm`:** placeholder name for the CLI.

## Status

Design stage, no code yet. The file format, the CLI, the web app's screens and the Claude Code plugin are specified in `.project/docs/`, and the user likes the clickable mockup of the web app so far (https://claude.ai/artifact/7WHHdLRhsnAn4oUeEuBw1k). The stack is chosen: Python standard library for the CLI and server, and a web app with no build step. Next: pick the real name, then plan v0.1 as items in `.project/` and start building.
