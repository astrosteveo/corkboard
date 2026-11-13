"""The corkboard command: finding the project, shared options, help, errors and warnings.

Each command is a function that takes a Context and its own arguments. The rules every command
follows are in .project/docs/cli.md, under "Rules for every command".
"""

from __future__ import annotations

import os
import stat
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TextIO

from . import project as project_module
from .edits import EditError
from .project import Item, Project

TITLE_WIDTH = 50
WHO = ("me", "claude")


class CommandError(Exception):
    """A problem the user can fix. Printed as one `error:` line, and the command exits 1."""


@dataclass
class Command:
    name: str
    usage: str
    summary: str
    details: str
    run: Callable[[Context, list[str]], int | None]


@dataclass
class Context:
    cwd: Path
    env: Mapping[str, str]
    out: TextIO
    err: TextIO
    who: str
    stdin: TextIO | None = None
    clock: Callable[[], datetime] = datetime.now
    _project: Project | None = field(default=None, repr=False)

    def now(self) -> datetime:
        return self.clock()

    def forget_project(self) -> None:
        """Drop the loaded project, so the next call to project() reads the files again."""
        self._project = None

    def piped_input(self) -> str | None:
        """Text piped or redirected in, or None when there's none.

        Reads only from a pipe or a file, such as a heredoc. In Claude Code's shell, stdin with
        nothing piped in is an open socket, and reading it would wait forever.
        """
        if self.stdin is None:
            return None
        try:
            mode = os.fstat(self.stdin.fileno()).st_mode
        except (AttributeError, OSError, ValueError):
            return self.stdin.read()  # an in-memory stream, as in tests
        if stat.S_ISFIFO(mode) or stat.S_ISREG(mode):
            return self.stdin.read()
        return None

    def project(self, warn: bool = True) -> Project:
        """The project for the current folder, loaded once. Warns if any file couldn't be read."""
        if self._project is None:
            root = project_module.find_root(self.cwd)
            if root is None:
                raise CommandError(
                    "no .project/ folder here or above. Run corkboard init to start one."
                )
            self._project = project_module.load(root)
            count = len(self._project.problems)
            if count and warn:
                files = "file" if count == 1 else "files"
                self.warn(f"{count} {files} in .project/ couldn't be read. Run corkboard check.")
        return self._project

    def print(self, text: str = "") -> None:
        self.out.write(text + "\n")

    def warn(self, message: str) -> None:
        self.err.write(f"warning: {message}\n")

    def relative(self, path: Path) -> str:
        """A path relative to the repo, the folder that holds .project/."""
        return self.project().relative(path)


def main(
    argv: list[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    out: TextIO | None = None,
    err: TextIO | None = None,
    stdin: TextIO | None = None,
    clock: Callable[[], datetime] | None = None,
) -> int:
    """Run one corkboard command. Returns the exit code."""
    real_streams = out is None
    out = out or _utf8(sys.stdout)
    err = err or _utf8(sys.stderr)
    if real_streams and stdin is None:
        stdin = sys.stdin
    env = os.environ if env is None else env
    try:
        args, who, wants_help = _global_options(argv, env)
        ctx = Context(cwd or Path.cwd(), env, out, err, who, stdin, clock or datetime.now)
        if not args or args[0] in ("help", "--help", "-h"):
            _help(ctx, args[1:2])
            return 0
        command = COMMANDS.get(args[0])
        if command is None:
            raise CommandError(f'"{args[0]}" isn\'t a command. Run corkboard help to see them.')
        if wants_help:
            _command_help(ctx, command)
            return 0
        return command.run(ctx, args[1:]) or 0
    except (CommandError, EditError) as error:
        err.write(f"error: {error}\n")
        return 1
    except OSError as error:
        err.write(f"error: {error.strerror or error}: {error.filename or ''}".rstrip(": ") + "\n")
        return 1


def run() -> None:
    """The `corkboard` command itself: runs main with the command line and exits with its code."""
    sys.exit(main(sys.argv[1:]))


def find_item(project: Project, text: str) -> Item:
    """The item an argument names, or an error saying what's wrong with it."""
    if project_module.parse_id(text.upper()) is None:
        example = f"{project.prefix or 'EX'}-12"
        raise CommandError(f'"{text}" isn\'t an item ID, such as {example}')
    item = project.item(text)
    if item is None:
        raise CommandError(f"there's no item {text.upper()}")
    return item


def cut(text: str, width: int = TITLE_WIDTH) -> str:
    """Text cut to `width` characters, ending in … when it's cut."""
    return text if len(text) <= width else text[: width - 1] + "…"


def usage_error(command: str) -> CommandError:
    return CommandError(f"usage: corkboard {COMMANDS[command].usage}")


def _global_options(argv: list[str], env: Mapping[str, str]) -> tuple[list[str], str, bool]:
    """Take --as and --help out of the arguments. Returns what's left, who, and --help."""
    who = "claude" if env.get("CLAUDECODE") else "me"
    wants_help = False
    args: list[str] = []
    rest = iter(argv)
    for arg in rest:
        if arg in ("--help", "-h"):
            wants_help = True
        elif arg == "--as" or arg.startswith("--as="):
            value = arg.partition("=")[2] if "=" in arg else next(rest, "")
            if value not in WHO:
                raise CommandError("--as takes me or claude")
            who = value
        else:
            args.append(arg)
    return args, who, wants_help


def _help(ctx: Context, topic: list[str]) -> None:
    if topic:
        command = COMMANDS.get(topic[0])
        if command is None:
            raise CommandError(f'"{topic[0]}" isn\'t a command. Run corkboard help to see them.')
        _command_help(ctx, command)
        return
    width = max(len(command.usage) for command in COMMANDS.values())
    ctx.print("corkboard: a local issue tracker and wiki, kept as Markdown files in .project/")
    ctx.print()
    ctx.print("Commands:")
    for command in COMMANDS.values():
        ctx.print(f"  {command.usage:<{width}}  {command.summary}")
    ctx.print()
    ctx.print("Run corkboard <command> --help for more about one.")


def _command_help(ctx: Context, command: Command) -> None:
    ctx.print(f"usage: corkboard {command.usage}")
    ctx.print()
    ctx.print(command.details)


def _utf8(stream: TextIO) -> TextIO:
    """The stream, switched to UTF-8 if it isn't already, so · and … print anywhere."""
    encoding = (getattr(stream, "encoding", None) or "").lower().replace("-", "")
    if encoding != "utf8" and hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")
    return stream


def _ui(ctx: Context, args: list[str]) -> None:
    from . import server  # imported only here: http.server takes longer to load than all the rest

    server.ui(ctx, args)


def _commands() -> dict[str, Command]:
    from . import changes, check, edits, show, summary, views

    commands = [
        Command(
            "now",
            "now",
            "Where things stand: waiting on you, in progress, next up",
            "The session-start summary: the active release, what's waiting on you, what's in\n"
            "progress and the next 3 items in the order of work. At most 25 lines. Outside a\n"
            "repo with .project/ it prints nothing.",
            summary.now,
        ),
        Command(
            "next",
            "next",
            "The item to do next, in full",
            "The first item in the order of work, shown the way corkboard show shows it, with a\n"
            "line saying why it's next. Only tasks and bugs that are todo, owned by claude and\n"
            "not blocked count: answered items first, then the active release, priority, number.",
            summary.next_,
        ),
        Command(
            "show",
            "show <ID>",
            "One item with its context",
            "One item with its context: its epic, release and labels, its links from both sides,\n"
            "the docs and items that mention it, its description, its numbered subtasks (or an\n"
            "epic's tasks) and the last 5 lines of its log.",
            show.run,
        ),
        Command(
            "list",
            "list [field=value…] [--all]",
            "One line per item, with filters",
            "One line per item, sorted by number, then a count. Filters work on any header field\n"
            "and must all match; commas inside one mean any of, such as status=todo,in-progress.\n"
            "labels=ui matches items with that label, and release=v0.1 also matches items whose\n"
            "epic is in v0.1. Done and cancelled items are hidden unless you pass --all or a\n"
            "status= filter names them.",
            views.list_,
        ),
        Command(
            "tree",
            "tree [release | none]",
            "A release's epics and their tasks, with progress",
            "A release, its epics, and each epic's tasks and bugs with their status and progress.\n"
            "With no argument it shows the active release; none shows items with no release.",
            views.tree,
        ),
        Command(
            "new",
            'new <epic|task|bug> "Title" [field=value…]',
            "Create an item",
            "Creates an item with status=todo, priority=medium and owner=claude unless you set\n"
            "them. Fields: " + ", ".join(edits.NEW_FIELDS) + ".\n"
            "Lists are comma-separated, such as labels=ui,board.\n\n"
            "Text piped in becomes the body, so a description and a ## Subtasks checklist can go\n"
            "in with one command. corkboard writes the ## Log section itself.",
            changes.new,
        ),
        Command(
            "move",
            'move <ID> <status> ["message"]',
            "Change an item's status",
            "Changes an item's status and logs it. Statuses: "
            + ", ".join(project_module.STATUSES)
            + ".\nMoving to waiting needs a message: the question, or what to review.",
            changes.move,
        ),
        Command(
            "sub",
            'sub <ID> add "text" | done <N> | undo <N>',
            "Add, tick or untick a subtask",
            "Adds a subtask, or ticks or unticks one by its number in corkboard show, and logs\n"
            "it. To reword or remove a subtask, edit the file.",
            changes.sub,
        ),
        Command(
            "log",
            'log <ID> "text"',
            "Add a note to an item's log",
            "Adds a note to the item's log: a choice and why, a dead end, a surprise.",
            changes.log,
        ),
        Command(
            "set",
            "set <ID> field=value…",
            "Change an item's other fields",
            "Changes header fields other than id, created and status, and logs the change.\n"
            "Fields: " + ", ".join(edits.SET_FIELDS) + ". An empty value clears a field,\n"
            "such as parent=. type only switches between task and bug. A new title renames\n"
            "the file.",
            changes.set_,
        ),
        Command(
            "release",
            "release <name> [status=…] [date=YYYY-MM-DD]",
            "Create or change a release",
            "Creates a release, starting as planned, or changes one. Statuses: planned, active,\n"
            "released; only one release can be active. Text piped in becomes its goal.",
            changes.release,
        ),
        Command(
            "check",
            "check [--fix]",
            "Find files in .project/ that break the format",
            "Checks every file in .project/ against the rules in file-format.md and prints one\n"
            "problem per line, then a summary. Exits 1 if any problems are left. --fix repairs\n"
            "only what's safe: header formatting, file names that don't match the title, and\n"
            "duplicate IDs, which get a new number, with the references listed for review.",
            check.check,
        ),
        Command(
            "init",
            'init [prefix=XX] [name="…"]',
            "Start a .project/ folder here",
            "Creates .project/config.yml. The prefix defaults to the first letter of each word\n"
            "in the folder's name (claude-project gives CP), or the first three letters of a\n"
            "one-word name; the name defaults to the folder's name in title case.",
            check.init,
        ),
        Command(
            "ui",
            "ui",
            "Start the web app on localhost",
            "Starts the web app on 127.0.0.1, on port 4747 or the next free one up to 4766,\n"
            "prints its URL and runs until Ctrl-C. If it's already running for this repo, it\n"
            "prints that URL and exits.",
            _ui,
        ),
        Command(
            "help",
            "help [command]",
            "List the commands, or explain one",
            "Lists the commands, or explains the one you name.",
            lambda ctx, args: _help(ctx, args),
        ),
    ]
    return {command.name: command for command in commands}


COMMANDS = _commands()
