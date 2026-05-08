"""Deterministic one-token-word filler for context-window tests."""

from __future__ import annotations

from typing import List


ONE_TOKEN_WORDS: List[str] = [
    "able", "about", "above", "after", "again", "agent", "ahead", "allow",
    "also", "answer", "apply", "area", "around", "array", "basic", "batch",
    "before", "below", "block", "branch", "budget", "build", "cache", "call",
    "case", "change", "check", "clean", "clear", "close", "code", "commit",
    "common", "compact", "copy", "cost", "count", "create", "data", "debug",
    "default", "detail", "diff", "direct", "done", "draft", "early", "edit",
    "empty", "error", "event", "exact", "field", "file", "final", "first",
    "fixed", "flag", "flow", "focus", "format", "found", "gate", "global",
    "group", "guard", "handle", "helper", "history", "honest", "input", "item",
    "json", "keep", "known", "large", "last", "later", "ledger", "level",
    "limit", "line", "local", "lock", "logic", "main", "marker", "matrix",
    "memory", "message", "model", "module", "next", "normal", "note", "open",
    "order", "output", "parent", "parse", "patch", "phase", "plan", "port",
    "prefix", "prompt", "query", "range", "ready", "record", "redo", "reply",
    "report", "reset", "result", "retry", "review", "risk", "row", "rule",
    "safe", "save", "scope", "search", "section", "session", "ship", "slice",
    "small", "source", "state", "status", "strict", "string", "table", "task",
    "test", "text", "thread", "token", "tool", "trace", "turn", "type",
    "unit", "usage", "user", "valid", "value", "view", "warn", "window",
    "worker", "write",
]

MAX_LOREM_TOKENS = 500_000


def generate_lorem_ipsum(token_count: int) -> str:
    """Return exactly ``token_count`` space-separated deterministic words."""
    count = int(token_count)
    if count < 0:
        raise ValueError("token_count must be non-negative")
    if count > MAX_LOREM_TOKENS:
        raise ValueError(f"token_count exceeds cap {MAX_LOREM_TOKENS}")
    if count == 0:
        return ""

    words: List[str] = []
    source_len = len(ONE_TOKEN_WORDS)
    for idx in range(count):
        words.append(ONE_TOKEN_WORDS[idx % source_len])
    return " ".join(words)

