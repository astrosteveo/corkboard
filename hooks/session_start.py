#!/usr/bin/env python3
"""Session-start hook: puts `corkboard now` in front of Claude in a repo with a .project/ folder.

What this prints becomes part of Claude's context; the user doesn't see it. Outside such a repo,
or if anything at all goes wrong, it prints nothing and exits 0, so it can never get in the way
of a session starting.
"""

import io
import os
import sys
from pathlib import Path

LEAD = (
    "This repo tracks its work in .project/ with corkboard. "
    "Use the corkboard:track skill before you start, finish or plan work."
)


def main() -> int:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from corkboard.cli import main as corkboard

        cwd = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
        out = io.StringIO()
        code = corkboard(["now"], cwd=cwd, out=out, err=io.StringIO(), stdin=None)
        summary = out.getvalue().strip()
        if code == 0 and summary:
            print(f"{LEAD}\n\n{summary}")
    except Exception:  # noqa: BLE001, S110 - a broken summary must never stop a session starting
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
