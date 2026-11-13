---
id: CB-37
type: task
title: "Onboarding: clear setup, and corkboard in your own terminal"
status: done
priority: high
owner: claude
created: 2026-11-12
release: v0.2
---
Someone new should get from nothing to working in a few clear steps. Today the README's terminal setup needs a clone and a symlink into it, which breaks when the folder moves. Make the command installable as a normal Python tool, `uv tool install git+https://github.com/astrosteveo/corkboard`, with a `pyproject.toml` and no code changes, and rewrite the README's start into numbered steps. The plugin keeps running `bin/corkboard` with no install step.

Done when a fresh `uvx --from git+https://github.com/astrosteveo/corkboard corkboard help` works, and the README's Get started section goes from installing the plugin to a first planned task.

## Subtasks
- [x] pyproject.toml with a corkboard command
- [x] A test that the plugin and package versions match
- [x] CI checks that the package installs and runs
- [x] README: numbered Get started, terminal install, updating
- [x] plugin.md and PROJECT.md say how the terminal install works

## Log
- 2026-11-12 22:50 claude: created
- 2026-11-12 22:50 claude: moved to in-progress
- 2026-11-12 22:52 claude: done subtask: pyproject.toml with a corkboard command
- 2026-11-12 22:52 claude: done subtask: A test that the plugin and package versions match
- 2026-11-12 22:52 claude: done subtask: CI checks that the package installs and runs
- 2026-11-12 22:52 claude: done subtask: README: numbered Get started, terminal install, updating
- 2026-11-12 22:52 claude: done subtask: plugin.md and PROJECT.md say how the terminal install works
- 2026-11-12 22:52 claude: uv tool install from the repo replaces the clone-and-symlink step. The plugin is unchanged and still runs bin/corkboard with no install. Checked by installing from the pushed branch on GitHub with uvx; it built with setuptools and ran corkboard help. CI now builds and runs the package too. The user's own ~/.local/bin/corkboard symlink to this repo still works for development; the README offers uv tool install --editable . for that.
- 2026-11-12 22:52 claude: moved to done
