# Claude Project (working title)

A lightweight issue tracker and wiki for one person working with Claude Code, kept as Markdown files in the repo.

## What it is

A Claude Code plugin with a small CLI (`cpm`) and a local web app. Each repo keeps its releases, epics, tasks, subtasks and docs as Markdown files in a `.project/` folder. Claude reads and edits them with its normal tools and uses `cpm` for structured changes. The user works in a browser tab on localhost: a board, a release view, issue pages and docs. It covers what teams use Jira (issues, epics, releases) and Confluence (specs, decisions) for.

## The problem

Each new Claude session starts without knowing where things stand. Plans, tasks and decisions end up spread across chats, TODO files and GitHub issues, and the user loses track of what's done, what's next and what Claude is waiting on them for.

## Who it's for

One developer working with Claude Code on their own repos. Not for teams.

## Goals

1. Claude knows where the project stands at the start of every session and keeps it up to date as it works, at a low token cost.
2. The user sees at a glance what's in progress, what's next, what Claude did, and what Claude is waiting on them for.
3. Work is organized the way it is in Jira: releases are made of epics, epics of tasks and bugs, tasks of subtasks, with labels across all of them. The user can open a release and see everything it contains.
4. Issues and docs live together as plain files next to the code, readable without the tool.
5. Stays lightweight: one command to set up, and no server running for Claude to work.

## Non-goals

- Team features: other users, permissions, mentions, notifications, hosting or sync. Why: it's for one person and Claude.

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

## Open questions

- What's the real name? "Claude Project" is a placeholder, and "Projects" is already a claude.ai feature.
- Will it be published, and under what license?
- Stack: TypeScript with pnpm for both the CLI and the web app, sharing one core library?
- Which fields go in an item's YAML header, and which statuses exist?
- Are subtasks their own files, or checklist lines inside their task?
- What exactly do `cpm board`, `cpm next` and the session-start summary print?
- Leave out sprints and time tracking for v1? (Releases replace milestones.)
- Which web app views are in v1 besides Now, Board, Release, Issue and Docs?

## Glossary

- **Release:** a named version, such as `v0.2`, that groups the epics shipping in it.
- **Epic:** a large piece of work made of tasks and bugs.
- **Task / Bug:** one piece of work, or one defect to fix. Can have subtasks.
- **Subtask:** a small step inside a task or bug.
- **Label:** a free-form tag on any item, such as `ui` or `cli`, used for filtering.
- **Item:** any epic, task, bug or subtask.
- **Doc:** a Markdown page in `.project/docs/`. Decisions are docs in `.project/docs/decisions/`.
- **Owner:** `me` or `claude`, whoever does the item.
- **Waiting on you:** items where Claude needs the user's answer or approval before it can go on.
- **Now view:** the web app's home page: what Claude is working on, what's next, and what's waiting on you.
- **`cpm`:** placeholder name for the CLI.

## Status

Design stage, no code yet. Next: spec the file format and the CLI's output, then sketch the web app screens.
