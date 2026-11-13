---
id: CB-22
type: task
title: Install docs and marketplace listing
status: done
priority: medium
owner: claude
created: 2026-11-12
parent: CB-3
blocked_by: [CB-21]
---
A README that says what Corkboard is and how to install it, with the one-line permission rule (`Bash(corkboard *)`) and the `~/.local/bin` symlink. Then add Corkboard to the astro-plugins marketplace by its GitHub repo.

Done when the plugin installs from the marketplace into a fresh session, and `corkboard init` and `/corkboard:next` work in a new repo.

## Subtasks
- [x] README
- [x] astro-plugins marketplace entry
- [x] Install it and try it in a new repo

## Log
- 2026-11-12 21:21 claude: created
- 2026-11-12 21:27 claude: The repo is private, so installing from the marketplace only works on a machine where git is logged in to GitHub as the user. Confirm that works, or settle the open question about publishing first.
- 2026-11-12 22:18 claude: moved to in-progress
- 2026-11-12 22:19 claude: done subtask: README
- 2026-11-12 22:23 claude: done subtask: astro-plugins marketplace entry
- 2026-11-12 22:23 claude: done subtask: Install it and try it in a new repo
- 2026-11-12 22:23 claude: Made the repo public (MIT) at the user's choice, and listed it in astro-plugins as an exception to that repo's TypeScript-hook and Python 3.8 rules, recorded in its PROJECT.md. Installed with claude plugin install corkboard@astro-plugins; it cloned from GitHub into the plugin cache. In a brand-new repo with only the installed plugin: corkboard init gave prefix CIT, a fresh session had the summary in its context, and /corkboard:next took the task to done. It closed the item in a separate commit again, so the track skill now says that outright, in 0.1.1.
- 2026-11-12 22:23 claude: moved to done
