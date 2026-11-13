"""Read and write item and release headers, the strict YAML subset in file-format.md.

A header sits between two `---` lines at the top of a file. Each line is `key: value`, and a
value is plain text, a double-quoted string, or a `[a, b]` list.

`write` always produces the canonical form: it quotes a value exactly when YAML would otherwise
misread it. So `write(*read(text)) == text` for every file corkboard wrote. `read` is a little
looser: it also accepts quotes a value doesn't need and extra spaces, so `corkboard check` can
report and fix those instead of every command failing on them. What YAML would read differently
from corkboard, such as a comment or a nested value, `read` rejects with the line number.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

Value = str | list[str]

FENCE = "---"

# Fields written as plain YYYY-MM-DD dates. Anywhere else, a date-like value is quoted.
DATE_KEYS = frozenset({"created", "date"})

_KEY = re.compile(r"[a-z][a-z0-9_]*")
_KEY_LINE = re.compile(r"([a-z][a-z0-9_]*):(.*)")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

# A plain value can't start with one of these: YAML gives each a meaning of its own.
_INDICATORS = frozenset("-?:,[]{}#&*!|>'\"%@`")

# YAML parsers are strict about plain text inside [a, b], so a list item goes unquoted only when
# it's letters, digits, spaces and . / - _, starting with a letter or digit. Labels and item IDs
# fit; anything else is quoted.
_LIST_PLAIN = re.compile(r"[^\W_][\w./ -]*")

# Plain values YAML would read as something other than text: null, booleans (YAML 1.1 too, which
# GitHub's renderer follows), the = and << keys, numbers, and dates and times.
_SPECIAL = re.compile(
    r"""
      ~ | null | Null | NULL | = | <<
    | true | True | TRUE | false | False | FALSE
    | yes | Yes | YES | no | No | NO | on | On | ON | off | Off | OFF | y | Y | n | N
    | [-+]? ( [0-9][0-9_]* ( \.[0-9_]* )? | \.[0-9][0-9_]* ) ( [eE][-+]?[0-9]+ )?
    | [-+]? 0[xX][0-9a-fA-F_]+ | [-+]? 0[oO]?[0-7_]+ | [-+]? 0[bB][01_]+
    | [-+]? \.(inf|Inf|INF) | \.(nan|NaN|NAN)
    | [0-9][0-9_]* ( :[0-5]?[0-9] )+ ( \.[0-9_]* )?
    | [0-9]{4}-[0-9]{1,2}-[0-9]{1,2} ( [Tt\ ] .* )?
    """,
    re.VERBOSE,
)


class HeaderError(ValueError):
    """A header corkboard can't read, with the file's line number."""

    def __init__(self, line: int, message: str) -> None:
        super().__init__(f"line {line}: {message}")
        self.line = line
        self.message = message


def read(text: str) -> tuple[dict[str, Value], str]:
    """Split a file into its header fields, in file order, and the body after the header."""
    lines = text.split("\n")
    if lines[0] != FENCE:
        raise HeaderError(1, "the file must start with a --- line")
    for index in range(1, len(lines)):
        if index == len(lines) - 1 and lines[index] == "":
            break  # the end of the file, after its last line break
        if lines[index] == FENCE:
            return _read_lines(lines[1:index], first_line=2), "\n".join(lines[index + 1 :])
    raise HeaderError(len(lines), "the header has no closing --- line")


def read_fields(text: str) -> dict[str, Value]:
    """Read a whole file of `key: value` lines with no --- lines around them, like config.yml."""
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()  # the end of the file, after its last line break
    return _read_lines(lines, first_line=1)


def write_fields(fields: Mapping[str, Value]) -> str:
    """A whole file of `key: value` lines, like config.yml."""
    return write(fields, "").removeprefix(FENCE + "\n").removesuffix(FENCE + "\n")


def write(fields: Mapping[str, Value], body: str) -> str:
    """A file with these header fields, in this order, and this body."""
    lines = [FENCE]
    for key, value in fields.items():
        if not _KEY.fullmatch(key):
            raise ValueError(f"not a valid header key: {key!r}")
        lines.append(f"{key}: {format_value(key, value)}")
    lines.append(FENCE)
    return "\n".join(lines) + "\n" + body


def canonical(text: str) -> str:
    """The file as corkboard would write it. A file that differs from this isn't canonical."""
    return write(*read(text))


def format_value(key: str, value: Value) -> str:
    """A field's value as it appears after `key: `."""
    if isinstance(value, list):
        return "[" + ", ".join(_format_scalar(item, in_list=True) for item in value) + "]"
    if key in DATE_KEYS and _DATE.fullmatch(value):
        return value
    return _format_scalar(value, in_list=False)


def needs_quotes(text: str, in_list: bool = False) -> bool:
    """Whether YAML would misread `text` written without quotes."""
    if text == "" or text != text.strip() or _SPECIAL.fullmatch(text):
        return True
    if in_list:
        return _LIST_PLAIN.fullmatch(text) is None
    if text[0] in _INDICATORS:
        return True
    return ": " in text or " #" in text or text.endswith(":")


def _format_scalar(text: str, in_list: bool) -> str:
    if any(ord(char) < 0x20 or char == "\x7f" for char in text):
        raise ValueError(f"a value can't contain line breaks or control characters: {text!r}")
    if not needs_quotes(text, in_list):
        return text
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _read_lines(lines: list[str], first_line: int) -> dict[str, Value]:
    fields: dict[str, Value] = {}
    for offset, line in enumerate(lines):
        number = first_line + offset
        key, value = _read_line(line, number)
        if key in fields:
            raise HeaderError(number, f"{key} appears twice")
        fields[key] = value
    return fields


def _read_line(line: str, number: int) -> tuple[str, Value]:
    if line.strip() == "":
        raise HeaderError(number, "blank lines aren't allowed in a header")
    if line[0] in " \t":
        raise HeaderError(number, "nested values aren't supported; each line is key: value")
    if line.startswith("#"):
        raise HeaderError(number, "comments aren't allowed in a header")
    if line.startswith("-"):
        raise HeaderError(number, "write a list as [a, b] on its key's line")
    match = _KEY_LINE.fullmatch(line)
    if match is None:
        raise HeaderError(number, "expected key: value, with a lowercase key")
    key, rest = match.groups()
    if rest and rest[0] != " ":
        raise HeaderError(number, "put a space after the colon")
    text = rest.strip()
    if text == "":
        raise HeaderError(number, f"{key} has no value; leave the field out instead")
    if text.startswith("["):
        return key, _read_list(text, number)
    value, end = _read_scalar(text, 0, number, in_list=False)
    if end != len(text):
        raise HeaderError(number, "unexpected text after the closing quote")
    return key, value


def _read_list(text: str, number: int) -> list[str]:
    if not text.endswith("]"):
        raise HeaderError(
            number, "a value starting with [ is a list and must end with ]; wrap text in quotes"
        )
    inner = text[:-1]
    items: list[str] = []
    pos = _skip_spaces(inner, 1)
    if pos == len(inner):
        return items
    while True:
        value, pos = _read_scalar(inner, pos, number, in_list=True)
        items.append(value)
        pos = _skip_spaces(inner, pos)
        if pos == len(inner):
            return items
        if inner[pos] != ",":
            raise HeaderError(number, "separate list items with a comma")
        pos = _skip_spaces(inner, pos + 1)
        if pos == len(inner):
            raise HeaderError(number, "a list can't end with a comma")


def _read_scalar(text: str, pos: int, number: int, in_list: bool) -> tuple[str, int]:
    """Read one value starting at `pos`. Returns the value and the position just after it."""
    if text[pos] == '"':
        chars: list[str] = []
        i = pos + 1
        while i < len(text):
            char = text[i]
            if char == "\\":
                escaped = text[i + 1 : i + 2]
                if escaped not in ('"', "\\"):
                    raise HeaderError(number, 'inside quotes, only \\" and \\\\ are allowed')
                chars.append(escaped)
                i += 2
            elif char == '"':
                return "".join(chars), i + 1
            else:
                chars.append(char)
                i += 1
        raise HeaderError(number, "a quoted value has no closing quote")
    end = pos
    if in_list:
        while end < len(text) and text[end] not in ",]":
            end += 1
    else:
        end = len(text)
    raw = text[pos:end].strip()
    problem = _plain_problem(raw, in_list)
    if problem:
        raise HeaderError(number, f"{problem}; wrap it in double quotes")
    return raw, end


def _skip_spaces(text: str, pos: int) -> int:
    while pos < len(text) and text[pos] == " ":
        pos += 1
    return pos


def _plain_problem(raw: str, in_list: bool) -> str | None:
    """Why YAML would misread this unquoted value, or None if it reads it as written."""
    if raw == "":
        return "an empty list item"
    if raw in ("=", "<<"):
        return f"{raw} on its own means something else in YAML"
    if in_list and not _LIST_PLAIN.fullmatch(raw):
        return "a list item with characters other than letters, digits, spaces and . / - _"
    if raw[0] in _INDICATORS:
        return f"a value starting with {raw[0]} means something else in YAML"
    if ": " in raw or raw.endswith(":"):
        return "a value containing ': ' or ending with ':' means something else in YAML"
    if " #" in raw:
        return "' #' starts a comment in YAML"
    return None
