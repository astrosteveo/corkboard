# Corkboard

A lightweight issue tracker and wiki for one person working with Claude Code, kept as Markdown files in the repo.

Corkboard is being built and isn't usable yet. What it's for is in [PROJECT.md](PROJECT.md), the design is in [.project/docs/](.project/docs/), and the work is tracked as Corkboard items in [.project/items/](.project/items/).

## Development

Corkboard runs on Python 3.11 or newer and uses only the standard library, so it needs nothing installed. The formatter and linter run through `uvx`.

```
python3 -m unittest discover -s tests   # run the tests
uvx ruff format                         # format the code
uvx ruff check                          # lint
```

CI runs the same three on every pull request.
