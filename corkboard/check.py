"""`corkboard check [--fix]` and `corkboard init`, as cli.md describes them.

check reads every file in .project/ itself, so it also sees what the loader skips: unreadable
headers and the second file that uses an ID. --fix repairs only what can't lose anything: header
formatting, file names, and duplicate IDs (renumbered, with the references listed for review).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import header, rules, write
from .cli import CommandError, Context, usage_error
from .project import (
    CONFIG_FILE,
    ITEM_FIELDS,
    PROJECT_DIR,
    RELEASE_FIELDS,
    RELEASE_STATUSES,
    REQUIRED_FIELDS,
    Project,
    find_root,
    natural_key,
    parse_id,
    parse_item,
)

_PREFIX = re.compile(r"[A-Z][A-Z0-9]*")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


@dataclass
class Finding:
    """One problem in one file. `fixes` names what --fix would do about it, if anything."""

    path: Path
    message: str
    fixes: set[str] = field(default_factory=set)


@dataclass
class ItemFile:
    path: Path
    text: str
    fields: dict[str, header.Value]
    body: str


def check(ctx: Context, args: list[str]) -> int:
    if any(arg != "--fix" for arg in args):
        raise usage_error("check")
    project = ctx.project(warn=False)
    findings = find_problems(project)
    if "--fix" in args and any(finding.fixes for finding in findings):
        for line in apply_fixes(ctx, project, findings):
            ctx.print(line)
        ctx.forget_project()
        project = ctx.project(warn=False)
        findings = find_problems(project)
    for finding in findings:
        ctx.print(f"{finding.path.name}: {finding.message}")
    items = len(_markdown(project.root / "items"))
    releases = len(_markdown(project.root / "releases"))
    summary = f"{items} item{'' if items == 1 else 's'}, {releases} release" + (
        "" if releases == 1 else "s"
    )
    count = len(findings)
    ctx.print(f"{summary}: " + ("ok" if not count else f"{count} problem" + ("s" * (count != 1))))
    return 1 if findings else 0


def init(ctx: Context, args: list[str]) -> None:
    values: dict[str, str] = {}
    for arg in args:
        key, sep, value = arg.partition("=")
        if not sep or key not in ("prefix", "name"):
            raise usage_error("init")
        values[key] = " ".join(value.split())
    existing = find_root(ctx.cwd)
    if existing is not None:
        where = os.path.relpath(existing / CONFIG_FILE, ctx.cwd.resolve())
        raise CommandError(f"already set up: {where}")
    folder = ctx.cwd.resolve()
    prefix = (values.get("prefix") or suggest_prefix(folder.name)).upper()
    if not _PREFIX.fullmatch(prefix):
        raise CommandError(
            f'"{prefix}" can\'t be a prefix. Use capital letters and digits, such as EX'
        )
    name = values.get("name") or suggest_name(folder.name)
    root = folder / PROJECT_DIR  # it may exist already, without config.yml; write_file makes it
    write.write_file(root / CONFIG_FILE, header.write_fields({"name": name, "prefix": prefix}))
    ctx.print(f"created {PROJECT_DIR}/{CONFIG_FILE} (prefix {prefix})")
    ctx.print('next: corkboard new epic "First epic"')


def suggest_prefix(folder: str) -> str:
    """The first letter of each word, or the first three letters of a one-word name."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9]*", folder)
    if not words:
        return "EX"
    prefix = "".join(word[0] for word in words) if len(words) > 1 else words[0][:3]
    return prefix.upper()


def suggest_name(folder: str) -> str:
    words = [word for word in re.split(r"[-_.\s]+", folder) if word]
    return " ".join(word[0].upper() + word[1:] for word in words) or folder


def find_problems(project: Project) -> list[Finding]:
    findings: list[Finding] = []
    root = project.root
    _config_problems(project, findings)
    for path in _markdown(root / "releases"):
        _release_problems(project, path, findings)

    files: list[ItemFile] = []
    for path in _markdown(root / "items"):
        try:
            text = path.read_text(encoding="utf-8")
            fields, body = header.read(text)
        except (OSError, UnicodeDecodeError, header.HeaderError) as error:
            findings.append(Finding(path, str(error)))
            continue
        files.append(ItemFile(path, text, fields, body))

    first_use: dict[str, ItemFile] = {}
    for item_file in sorted(files, key=lambda f: (_text(f.fields.get("created")), f.path.name)):
        item_id = _text(item_file.fields.get("id"))
        if item_id and item_id not in first_use:
            first_use[item_id] = item_file

    for item_file in files:
        _item_problems(project, item_file, first_use, findings)
    _cycle_problems(project, findings)
    return findings


def apply_fixes(ctx: Context, project: Project, findings: list[Finding]) -> list[str]:
    """Repair what --fix may, one file at a time. Returns a line for each repair."""
    lines: list[str] = []
    fixable: dict[Path, set[str]] = {}
    for finding in findings:
        if finding.fixes:
            fixable.setdefault(finding.path, set()).update(finding.fixes)
    next_number = int(write.next_id(project).rpartition("-")[2])

    for path in sorted(fixable, key=lambda p: natural_key(p.name)):
        fixes = fixable[path]
        fields, body = header.read(path.read_text(encoding="utf-8"))
        if path.parent == project.root / "releases":
            write.write_file(path, header.write(_release_order(fields), body))
            lines.append(f"fixed: rewrote the header of {path.name} in corkboard's format")
            continue
        fields = write.ordered_fields(fields)
        old_id = _text(fields.get("id"))
        if "renumber" in fixes:
            new_id = f"{project.prefix}-{next_number}"
            next_number += 1
            fields["id"] = new_id
            line = write.log_line(
                ctx.now(), ctx.who, f"renumbered from {old_id}, which another item also used"
            )
            body = write.add_log_line(body, line)
            title = _text(fields.get("title"))
            lines.append(f'fixed: {old_id} was used twice. "{title}" is now {new_id}.')
            refs = _references(project, old_id, exclude=path)
            if refs:
                lines.append(
                    f"check these references to {old_id}, which may have meant {new_id}: "
                    + ", ".join(refs)
                )
        new_path = path
        if fixes & {"rename", "renumber"} and fields.get("title"):
            new_path = write.item_path(project, _text(fields["id"]), _text(fields["title"]))
        if new_path != path and new_path.exists():
            lines.append(f"not fixed: {path.name} can't be renamed, {new_path.name} exists")
            new_path = path
        write.write_file(new_path, header.write(fields, body))
        if new_path != path:
            path.unlink()
            if "renumber" not in fixes:
                lines.append(f"fixed: renamed {path.name} to {new_path.name}")
        elif "canonical" in fixes:
            lines.append(f"fixed: rewrote the header of {path.name} in corkboard's format")
    return lines


def _config_problems(project: Project, findings: list[Finding]) -> None:
    config = project.root / CONFIG_FILE
    for problem in project.problems:
        if problem.path == config:
            findings.append(Finding(config, problem.message))
            return
    if not project.prefix:
        findings.append(Finding(config, "there's no prefix, such as prefix: EX"))
    elif not _PREFIX.fullmatch(project.prefix):
        findings.append(
            Finding(config, "the prefix must be capital letters and digits, such as EX")
        )


def _release_problems(project: Project, path: Path, findings: list[Finding]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
        fields, body = header.read(text)
    except (OSError, UnicodeDecodeError, header.HeaderError) as error:
        findings.append(Finding(path, str(error)))
        return
    name, status, date = (_text(fields.get(key)) for key in RELEASE_FIELDS)
    if name != path.stem:
        findings.append(Finding(path, f'name is "{name}", but the file is named {path.name}'))
    if status not in RELEASE_STATUSES:
        allowed = ", ".join(RELEASE_STATUSES)
        findings.append(Finding(path, f'"{status}" isn\'t a release status. Use one of: {allowed}'))
    if date and not _DATE.fullmatch(date):
        findings.append(Finding(path, f'date "{date}" isn\'t a date like 2026-12-01'))
    for key in fields:
        if key not in RELEASE_FIELDS:
            findings.append(Finding(path, f"{key} isn't a release field"))
    if header.write(_release_order(fields), body) != text:
        findings.append(
            Finding(path, "the header isn't written the way corkboard writes it", {"canonical"})
        )


def _release_order(fields: dict[str, header.Value]) -> dict[str, header.Value]:
    """A release's fields in corkboard's order. Keys it doesn't know keep their order, last."""
    ordered = {key: fields[key] for key in RELEASE_FIELDS if key in fields}
    ordered.update((key, value) for key, value in fields.items() if key not in ordered)
    return ordered


def _item_problems(
    project: Project, item_file: ItemFile, first_use: dict[str, ItemFile], findings: list[Finding]
) -> None:
    path, fields = item_file.path, item_file.fields
    item = parse_item(path, fields, item_file.body)
    item_id = item.id
    if not item_id:
        findings.append(Finding(path, "the header has no id"))
        return

    def add(message: str, *fixes: str) -> None:
        findings.append(Finding(path, message, set(fixes)))

    parsed = parse_id(item_id)
    if parsed is None or (project.prefix and parsed[0] != project.prefix):
        add(f"{item_id} isn't an ID with this project's prefix, such as {project.prefix}-12")
    if first_use.get(item_id) is not item_file:
        # Renumbering needs a prefix that makes valid IDs; config.yml's problem is reported too.
        fixes = ["renumber"] if _PREFIX.fullmatch(project.prefix) else []
        add(f"{item_id} is also used by {first_use[item_id].path.name}", *fixes)

    missing = [key for key in REQUIRED_FIELDS if key not in fields]
    if missing:
        add("missing " + ", ".join(missing))
    for key in fields:
        if key not in ITEM_FIELDS:
            add(f"{key} isn't a field corkboard knows")
    for problem in rules.field_problems(project, fields, item_id):
        add(problem)
    if item.is_epic and item.has_subtasks_section:
        add("an epic has tasks, not a ## Subtasks section")

    # Only a real ID can name a file: renaming to ../../EX-1 would write outside items/.
    if item.title and parsed is not None:
        expected = write.item_path(project, item_id, item.title).name
        if not path.name.startswith(f"{item_id}-"):
            add(f"the file name doesn't start with {item_id}", "rename")
        elif path.name != expected:
            add("the file name doesn't match the title", "rename")

    canonical = header.write(write.ordered_fields(fields), item_file.body)
    if canonical != item_file.text:
        add("the header isn't written the way corkboard writes it", "canonical")

    offset = item_file.text[: len(item_file.text) - len(item_file.body)].count("\n")
    for number, line in item.unreadable_lines:
        add(f"line {offset + number}: {line.strip()!r} isn't a subtask or log line")


def _cycle_problems(project: Project, findings: list[Finding]) -> None:
    """Items that block themselves through a chain of blocked_by."""
    seen: set[tuple[str, ...]] = set()
    graph = {item.id: item.blocked_by for item in project.items.values()}

    def visit(node: str, trail: list[str]) -> None:
        if node in trail:
            loop = trail[trail.index(node) :]
            start = loop.index(min(loop, key=lambda i: (len(i), i)))
            key = tuple(loop[start:] + loop[:start])
            if key not in seen and len(key) > 1:
                seen.add(key)
                item = project.items[key[0]]
                chain = " → ".join([*key, key[0]])
                findings.append(Finding(item.path, f"blocked by itself through {chain}"))
            return
        for blocker in graph.get(node, []):
            if blocker in graph:
                visit(blocker, [*trail, node])

    for item_id in sorted(graph):
        visit(item_id, [])


def _references(project: Project, item_id: str, exclude: Path) -> list[str]:
    refs = []
    for item in project.sorted_items():
        if item.path == exclude:
            continue
        for key in ("parent", "blocked_by", "related", "duplicate_of"):
            value = item.fields.get(key)
            values = value if isinstance(value, list) else [value]
            if item_id in values:
                refs.append(f"{item.id} {key}")
    for mention in project.mentions(item_id):
        refs.append(mention if "/" in mention else f"{mention} text")
    return refs


def _markdown(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(folder.glob("*.md"), key=lambda path: natural_key(path.name))


def _text(value: header.Value | None) -> str:
    if value is None:
        return ""
    return ", ".join(value) if isinstance(value, list) else value
