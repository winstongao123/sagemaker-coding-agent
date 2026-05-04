"""Block C — Hermes-style JSON repair for malformed tool_use args.

When Bedrock streams back a tool_use block with malformed JSON in its
`input` field (truncated string, unbalanced quote, missing closing brace),
v4 / pre-Block-C v5 fail loudly. Hermes adopts a graceful repair pattern
(run_agent.py:547-641): try to fix common malformations; if still
unparseable, fall back to `{}` and let the tool's error path take over.

This module ports that pattern as a stand-alone helper so it can be
called from any tool-arg parsing site (currently only `core/query_engine.py`
when consuming `response.tool_calls[i].input`).

PORT_LOG: see #057.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict


# ============================================================
# JSON repair helpers
# ============================================================

# Pattern: an unbalanced trailing quote followed by close-brace.
# E.g. `{"foo":"bar)` — close paren in place of close quote+brace.
_TRAILING_PAREN_FIX = re.compile(r'([\w])\)\s*$')

# Pattern: truncated value at end of input — assume missing close quote+brace.
_BARE_VALUE_END = re.compile(r':\s*"[^"\\]*(?:\\.[^"\\]*)*$')


def repair_tool_call_arguments(raw: str) -> Dict[str, Any]:
    """Best-effort repair of a malformed tool_use `input` JSON string.

    Returns the parsed dict on success. Falls back to `{}` if no repair
    works — caller (typically the tool dispatch) then surfaces the
    "missing required argument" error to the model so it can retry.

    Per Hermes run_agent.py:547-641 (R7-N) — graceful tool-arg repair.

    Repair attempts (in order):
      1. Parse as-is (covers the happy path; no false-positive cleanup).
      2. Strip trailing whitespace + control chars.
      3. Replace common shape errors:
         - `{"foo":"bar)` → `{"foo":"bar"}`  (paren-for-quote-brace)
         - `{"foo":"bar` → `{"foo":"bar"}`   (truncated value)
         - `{"foo":"bar"`  → `{"foo":"bar"}` (missing brace)
         - `{"foo":"bar",` → `{"foo":"bar"}` (trailing comma + no brace)
      4. Escape lone newlines inside string values (Bedrock occasionally
         emits raw \n inside a JSON string).
      5. Final fallback: `{}`.
    """
    if raw is None:
        return {}
    if isinstance(raw, dict):  # already parsed by the caller
        return raw
    if not isinstance(raw, str):
        return {}

    # Attempt 1: as-is
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        pass

    # Attempt 2: strip whitespace + non-printable (except \n / \t).
    cleaned = raw.strip()
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        pass

    # Attempt 3: shape repairs.
    repaired = cleaned

    # 3a — paren-for-quote-brace at end: `:"bar)` → `:"bar"}`
    if _TRAILING_PAREN_FIX.search(repaired):
        candidate = _TRAILING_PAREN_FIX.sub(r'\1"}', repaired, count=1)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # 3b — truncated value at end: `:"bar` → `:"bar"}`
    if _BARE_VALUE_END.search(repaired):
        candidate = repaired + '"}'
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # 3c — missing closing brace.
    if repaired.endswith(",") or not repaired.endswith("}"):
        candidate = repaired.rstrip(",") + "}"
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # 3d — missing closing quote AND brace at end of last value.
    if repaired.count('"') % 2 == 1:
        candidate = repaired + '"}'
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # Attempt 4: escape invalid raw chars inside string values.
    if any(ch in repaired for ch in ("\n", "\r", "\t")):
        escaped = _escape_invalid_chars_in_json_strings(repaired)
        try:
            parsed = json.loads(escaped)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # Attempt 5 (final fallback): empty dict.
    logging.warning(
        f"json_repair: tool-call arguments unparseable after all repairs; "
        f"returning empty dict. Raw[:100]={raw[:100]!r}"
    )
    return {}


def _escape_invalid_chars_in_json_strings(raw: str) -> str:
    """Escape raw newline, carriage-return, and tab chars inside JSON strings."""
    out: list[str] = []
    in_string = False
    escaped = False
    for ch in raw:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\":
            out.append(ch)
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ch == "\n":
            out.append("\\n")
        elif in_string and ch == "\r":
            out.append("\\r")
        elif in_string and ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    return "".join(out)


__all__ = ["repair_tool_call_arguments", "_escape_invalid_chars_in_json_strings"]
