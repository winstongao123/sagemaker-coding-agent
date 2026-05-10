"""V5 memory/compact.py — Block H session-memory compaction helpers.

PORT_LOG: #097 (H-11 + H-12 + H-14).

Source: Runnable services/sessionMemoryCompact.ts.

H-11 adjustIndexToPreserveAPIInvariants is the **MUST** correctness fix:
without it, sessionMemoryCompact picks a startIndex that lands mid-pair
(tool_use without its tool_result, or vice versa) → Bedrock 400 reject
on the very next API call. This module is small but critical.

Public functions:
- adjust_index_to_preserve_api_invariants(messages, candidate_index)
  → returns an index that keeps tool_use/tool_result paired.
- calculate_messages_to_keep_index(messages, max_keep_count)
  → choose a starting cut-point that satisfies H-11.
- has_text_blocks(content) — H-14 helper.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_SESSION_MEMORY_TEMPLATE = "# Session Memory\n\n"


@dataclass(frozen=True)
class SessionMemoryCompactConfig:
    """H-13: file-backed defaults for session-memory compaction."""

    enabled: bool = True
    max_messages_to_keep: int = 40
    max_section_chars: int = 4000
    max_total_chars: int = 12000

    @classmethod
    def from_workspace(cls, workspace: str) -> "SessionMemoryCompactConfig":
        data = _load_config_dict(workspace)
        raw = data.get("session_memory_compaction", data.get("sessionMemoryCompaction", {}))
        if not isinstance(raw, dict):
            raw = {}
        return cls(
            enabled=_bool_value(raw.get("enabled"), cls.enabled),
            max_messages_to_keep=_positive_int(
                raw.get("max_messages_to_keep", raw.get("maxMessagesToKeep")),
                cls.max_messages_to_keep,
            ),
            max_section_chars=_positive_int(
                raw.get("max_section_chars", raw.get("maxSectionChars")),
                cls.max_section_chars,
            ),
            max_total_chars=_positive_int(
                raw.get("max_total_chars", raw.get("maxTotalChars")),
                cls.max_total_chars,
            ),
        )


def _strip_jsonc_comments(text: str) -> str:
    out: List[str] = []
    i = 0
    in_string = False
    while i < len(text):
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
        elif ch == "/" and i + 1 < len(text) and text[i + 1] == "/":
            while i < len(text) and text[i] != "\n":
                i += 1
        elif ch == "/" and i + 1 < len(text) and text[i + 1] == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2 if i + 1 < len(text) else 0
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _load_config_dict(workspace: str) -> Dict[str, Any]:
    for name in ("agent_config.json", "agent_config.jsonc"):
        path = Path(workspace) / name
        if not path.is_file():
            continue
        try:
            return json.loads(_strip_jsonc_comments(path.read_text(encoding="utf-8")))
        except Exception:
            return {}
    return {}


def _positive_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _bool_value(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def has_text_blocks(content: Any) -> bool:
    """H-14: True iff `content` is a list with at least one text block.

    Used by H-12: a candidate cut-point with no text content above is
    not a useful boundary (the resulting buffer would have no human-
    readable summary anchor).
    """
    if not isinstance(content, list):
        return isinstance(content, str) and bool(content.strip())
    for b in content:
        if isinstance(b, dict) and b.get("type") == "text":
            text = b.get("text", "")
            if isinstance(text, str) and text.strip():
                return True
    return False


def _collect_pair_indices(messages: List[Dict[str, Any]]) -> Dict[str, int]:
    """Return a dict mapping tool_use_id → index-of-message-containing-it
    AND tool_result_id → index-of-message-containing-it.

    Used by adjust_index_to_preserve_api_invariants.
    """
    use_to_index: Dict[str, int] = {}
    result_to_index: Dict[str, int] = {}
    for i, m in enumerate(messages or []):
        content = m.get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                tid = b.get("id")
                if tid:
                    use_to_index[tid] = i
            elif b.get("type") == "tool_result":
                tid = b.get("tool_use_id")
                if tid:
                    result_to_index[tid] = i
    return {"uses": use_to_index, "results": result_to_index}


def adjust_index_to_preserve_api_invariants(
    messages: List[Dict[str, Any]],
    candidate_index: int,
) -> int:
    """H-11 — the **MUST** correctness fix.

    Given a `candidate_index` (where compaction wants to start dropping
    older messages), return an adjusted index that:
    1. Never lands in the middle of a tool_use/tool_result pair (would
       cause Bedrock 400 on the next API call).
    2. Floors at 0 if the candidate would split a pair.
    3. Returns `candidate_index` unchanged when it's already pair-safe.

    The adjustment direction is "earlier" — if the cut would split a
    pair, we move the cut earlier so BOTH sides of the pair are kept
    in the post-compact buffer (or both are dropped). This may sacrifice
    some compaction savings to preserve API validity.
    """
    msgs = messages or []
    if not msgs:
        return 0
    if candidate_index <= 0:
        return 0
    if candidate_index >= len(msgs):
        return len(msgs)

    # Build pair index.
    indices = _collect_pair_indices(msgs)
    use_to_index = indices["uses"]
    result_to_index = indices["results"]

    # Codex iter-1 finding #1 BLOCKER fix: fixed-point loop.
    # A single pass through use_to_index can leave earlier pairs split.
    # Example: candidate=7 splits pair (5,8) → adjusted=5. But 5 splits
    # an earlier pair (2,6) which we already visited. Iterate until no
    # further pulls happen.
    adjusted = candidate_index
    while True:
        next_adjusted = adjusted
        for tid, use_idx in use_to_index.items():
            result_idx = result_to_index.get(tid)
            if result_idx is None:
                # Dangling tool_use (no result yet); the cut must NOT split
                # it from any preceding tool_result-bearing context.
                continue
            lo = min(use_idx, result_idx)
            hi = max(use_idx, result_idx)
            # If the cut lands between lo and hi, the pair is split.
            # Pull adjusted to lo so the whole pair lands AFTER the cut.
            if lo < next_adjusted <= hi:
                next_adjusted = min(next_adjusted, lo)
        if next_adjusted == adjusted:
            break
        adjusted = next_adjusted
    return max(0, min(adjusted, len(msgs)))


def calculate_messages_to_keep_index(
    messages: List[Dict[str, Any]],
    max_keep_count: int,
) -> int:
    """H-12: pick a starting index for the keep-set.

    Strategy:
    1. Start with `len(messages) - max_keep_count` as the naive candidate.
    2. Floor at 0 (keep everything if buffer is shorter).
    3. Pass through adjust_index_to_preserve_api_invariants to shift
       earlier if the naive cut splits a pair.
    """
    msgs = messages or []
    if not msgs or max_keep_count <= 0:
        return 0
    if max_keep_count >= len(msgs):
        return 0
    candidate = len(msgs) - max_keep_count
    return adjust_index_to_preserve_api_invariants(msgs, candidate)


def truncate_session_memory_for_compact(
    session_memory: Any,
    config: Optional[SessionMemoryCompactConfig] = None,
) -> str:
    """H-15: cap session memory by per-section and total character limits.

    Accepts either a string or a mapping of section name to body. The return
    value is prompt-ready text.
    """
    cfg = config or SessionMemoryCompactConfig()
    if isinstance(session_memory, dict):
        sections = [
            f"## {name}\n{str(value).strip()}"
            for name, value in session_memory.items()
            if str(value).strip()
        ]
    else:
        text = str(session_memory or "")
        sections = _split_markdown_sections(text)

    truncated_sections = [
        _truncate_text(section.strip(), cfg.max_section_chars)
        for section in sections
        if section.strip()
    ]
    return _truncate_text("\n\n".join(truncated_sections), cfg.max_total_chars)


def _split_markdown_sections(text: str) -> List[str]:
    current: List[str] = []
    sections: List[str] = []
    for line in (text or "").splitlines():
        if line.startswith("## ") and current:
            sections.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current))
    return sections


def _truncate_text(text: str, limit: int) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    marker = "\n...[truncated]"
    keep = max(0, limit - len(marker))
    return text[:keep].rstrip() + marker


def is_session_memory_empty(
    session_memory: str,
    template: str = DEFAULT_SESSION_MEMORY_TEMPLATE,
) -> bool:
    """H-16: true for empty memory or the untouched template."""
    normalized = (session_memory or "").strip()
    return not normalized or normalized == (template or "").strip()


def should_use_session_memory_compaction(
    config: Optional[SessionMemoryCompactConfig] = None,
    env: Optional[Dict[str, str]] = None,
) -> bool:
    """H-17: session-memory compaction switch with env override."""
    env_map = env if env is not None else os.environ
    override = env_map.get("SAGEMAKER_SM_COMPACT_ENABLE")
    if override is not None:
        return _bool_value(override, default=False)
    cfg = config or SessionMemoryCompactConfig()
    return bool(cfg.enabled)
