# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@PROJECT.md

# Commands
- Run the tests: `python3 -m unittest discover -s tests`
- Run one test file: `python3 -m unittest discover -s tests -p test_cli.py`
- Format and lint: `uvx ruff format`, then `uvx ruff check`
- Run this checkout's CLI: `bin/corkboard <command>`

# Conventions
- Commits use Conventional Commits with the item's ID, such as `feat(cli): add corkboard tree (CB-19)`

# Gotchas
- The specs in `.project/docs/` are the contract: change a spec in the same pull request as the code. The output tests are built from the examples in `cli.md`.
- Bump the version in `.claude-plugin/plugin.json` and `pyproject.toml` together when a change should reach installed copies; `claude plugin update` only updates on a new version.
- Tests must not depend on this repo's own item state, such as which release is active.
