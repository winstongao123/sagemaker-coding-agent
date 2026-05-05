"""Slash-command parsing and argument substitution helpers for Block D.

These helpers are intentionally independent of the command dispatcher so custom
commands and skills can use the same parsing/substitution contract.
"""
from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional


@dataclass(frozen=True)
class ParsedSlashCommand:
    raw: str
    command: str
    args: str = ""
    namespace: Optional[str] = None


_COMMAND_RE = re.compile(
    r"^\s*(?P<command>/[^\s(]+)(?:\((?P<namespace>[^)]+)\))?(?:\s+(?P<args>.*))?\s*$"
)
_INDEXED_ARGUMENTS_RE = re.compile(r"\$ARGUMENTS\[(\d+)\]")
_SHORT_INDEX_RE = re.compile(r"\$(\d+)")
_BRACED_NAME_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_PLAIN_NAME_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


def parse_slash_command(message: str) -> Optional[ParsedSlashCommand]:
    """Parse `/name(args) rest` style slash-command input.

    Runnable keeps an MCP suffix parser even when MCP is disabled so command
    expansion can distinguish `/foo` from `/foo(MCP)`. v5 mirrors that parser
    but does not enable MCP execution.
    """
    match = _COMMAND_RE.match(message or "")
    if not match:
        return None
    command = match.group("command")
    if not command.startswith("/"):
        return None
    namespace = match.group("namespace")
    if namespace is not None:
        namespace = namespace.strip() or None
    return ParsedSlashCommand(
        raw=message,
        command=command,
        args=(match.group("args") or "").strip(),
        namespace=namespace,
    )


def _positional_values(arguments: Any) -> tuple[str, List[str], Dict[str, str]]:
    if arguments is None:
        return "", [], {}
    if isinstance(arguments, Mapping):
        named = {str(k): str(v) for k, v in arguments.items()}
        whole = named.get("ARGUMENTS", "")
        return whole, [], named
    if isinstance(arguments, (list, tuple)):
        values = [str(v) for v in arguments]
        return " ".join(values), values, {}
    whole = str(arguments)
    try:
        values = shlex.split(whole)
    except ValueError:
        values = whole.split()
    return whole, values, {}


def substitute_arguments(template: str, arguments: Any) -> str:
    """Substitute custom-command argument placeholders.

    Supported forms:
    - `$ARGUMENTS` for the full raw argument string.
    - `$ARGUMENTS[0]` and `$0` for indexed positional arguments.
    - `${name}` and `$name` for named mapping values.
    """
    if not template:
        return template
    whole, positional, named = _positional_values(arguments)

    def indexed(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        return positional[idx] if idx < len(positional) else ""

    def short_index(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        return positional[idx] if idx < len(positional) else ""

    def braced_name(match: re.Match[str]) -> str:
        key = match.group(1)
        return named.get(key, "")

    def plain_name(match: re.Match[str]) -> str:
        key = match.group(1)
        if key == "ARGUMENTS":
            return whole
        return named.get(key, match.group(0))

    out = _INDEXED_ARGUMENTS_RE.sub(indexed, template)
    out = _SHORT_INDEX_RE.sub(short_index, out)
    out = _BRACED_NAME_RE.sub(braced_name, out)
    return _PLAIN_NAME_RE.sub(plain_name, out)


__all__ = [
    "ParsedSlashCommand",
    "parse_slash_command",
    "substitute_arguments",
]
