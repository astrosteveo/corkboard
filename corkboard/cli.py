"""The corkboard command: finding the project, shared options, help, errors and warnings.

Each command is a function that takes a Context and its own arguments. The rules every command
follows are in .project/docs/cli.md, under "Rules for every command".
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

from . import project as project_module
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
    run: Callable[[Context, list[str]], None]


@dataclass
class Context:
    cwd: Path
    env: Mapping[str, str]
    out: TextIO
    err: TextIO
    who: str
    _project: Project | None = field(default=None, repr=False)

    def project(self) -> Project:
        """The project for the current folder, loaded once. Warns if any file couldn't be read."""
        if self._project is None:
            root = project_module.find_root(self.cwd)
            if root is None:
                raise CommandError(
                    "no .project/ folder here or above. Run corkboard init to start one."
                )
            self._project = project_module.load(root)
            count = len(self._project.problems)
            if count:
                files = "file" if count == 1 else "files"
                self.warn(f"{count} {files} in .project/ couldn't be read. Run corkboard check.")
        return self._project

    def print(self, text: str = "") -> None:
        self.out.write(text + "\n")

    def warn(self, message: str) -> None:
        self.err.write(f"warning: {message}\n")

    def relative(self, path: Path) -> str:
        """A path relative to the repo, the folder that holds .project/."""
        repo = self.project().root.parent
        try:
            return path.resolve().relative_to(repo.resolve()).as_posix()
        except ValueError:
            return str(path)


def main(
    argv: list[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    out: TextIO | None = None,
    err: TextIO | None = None,
) -> int:
    """Run one corkboard command. Returns the exit code."""
    out = out or _utf8(sys.stdout)
    err = err or _utf8(sys.stderr)
    env = os.environ if env is None else env
    try:
        args, who, wants_help = _global_options(argv, env)
        ctx = Context(cwd or Path.cwd(), env, out, err, who)
        if not args or args[0] in ("help", "--help", "-h"):
            _help(ctx, args[1:2])
            return 0
        command = COMMANDS.get(args[0])
        if command is None:
            raise CommandError(f'"{args[0]}" isn\'t a command. Run corkboard help to see them.')
        if wants_help:
            _command_help(ctx, command)
            return 0
        command.run(ctx, args[1:])
        return 0
    except CommandError as error:
        err.write(f"error: {error}\n")
        return 1


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


def _commands() -> dict[str, Command]:
    from . import show

    commands = [
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
            "help",
            "help [command]",
            "List the commands, or explain one",
            "Lists the commands, or explains the one you name.",
            lambda ctx, args: _help(ctx, args),
        ),
    ]
    return {command.name: command for command in commands}


COMMANDS = _commands()
