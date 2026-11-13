"""The commands that change things: `new`, `move`, `sub`, `log`, `set` and `release`.

Each one reads its arguments and any piped text, then calls the function of the same name in
edits.py, which the web server calls too, and prints the line and warnings it returns.
"""

from __future__ import annotations

import re

from . import edits
from .cli import CommandError, Context, find_item, usage_error
from .project import TYPES

_FIELD_ARG = re.compile(r"([a-z_]+)=(.*)", re.DOTALL)


def new(ctx: Context, args: list[str]) -> None:
    if len(args) < 2 or args[0] not in TYPES:
        raise usage_error("new")
    title = " ".join(arg for arg in args[1:] if not _FIELD_ARG.fullmatch(arg))
    if not title.split():
        raise usage_error("new")
    values = _field_args([arg for arg in args[1:] if _FIELD_ARG.fullmatch(arg)])
    project = ctx.project()
    body = ctx.piped_input() or ""
    _print(ctx, edits.new(project, args[0], title, values, body, ctx.who, ctx.now()))


def move(ctx: Context, args: list[str]) -> None:
    if len(args) < 2:
        raise usage_error("move")
    project = ctx.project()
    item = find_item(project, args[0])
    message = " ".join(args[2:])
    _print(ctx, edits.move(project, item, args[1], message, ctx.who, ctx.now()))


def sub(ctx: Context, args: list[str]) -> None:
    if len(args) < 3 or args[1] not in edits.SUBTASK_ACTIONS:
        raise usage_error("sub")
    value = " ".join(args[2:])
    if args[1] == "add" and not value.split():
        raise usage_error("sub")
    project = ctx.project()
    item = find_item(project, args[0])
    _print(ctx, edits.sub(project, item, args[1], value, ctx.who, ctx.now()))


def log(ctx: Context, args: list[str]) -> None:
    text = " ".join(args[1:])
    if not text.split():
        raise usage_error("log")
    project = ctx.project()
    item = find_item(project, args[0])
    _print(ctx, edits.log(project, item, text, ctx.who, ctx.now()))


def set_(ctx: Context, args: list[str]) -> None:
    if len(args) < 2:
        raise usage_error("set")
    project = ctx.project()
    item = find_item(project, args[0])
    _print(ctx, edits.set_(project, item, _field_args(args[1:]), ctx.who, ctx.now()))


def release(ctx: Context, args: list[str]) -> None:
    if not args or not all(_FIELD_ARG.fullmatch(arg) for arg in args[1:]):
        raise usage_error("release")
    values = _field_args(args[1:])
    project = ctx.project()
    _print(ctx, edits.release(project, args[0], values, ctx.piped_input()))


def _field_args(args: list[str]) -> dict[str, str]:
    """`field=value` arguments as a dict of each field and its value as typed."""
    values: dict[str, str] = {}
    for arg in args:
        match = _FIELD_ARG.fullmatch(arg)
        if match is None:
            raise CommandError(f'"{arg}" isn\'t field=value')
        values[match.group(1)] = match.group(2)
    return values


def _print(ctx: Context, result: edits.Result) -> None:
    for warning in result.warnings:
        ctx.warn(warning)
    ctx.print(result.line)
