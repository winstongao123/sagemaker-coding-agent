"""V5 core/cache.py — prompt-cache block builder + cache-break detection.

Per ADR-005 (Phase 1 deferred Runnable cache-break detection to Phase 6)
and ADR-012 (Phase 6 sectioned-prompt + cache-boundary contract).

Source: gg-claude-code-runnable/src/services/api/promptCacheBreakDetection.ts.

Phase 6 deliverables:
  1. `build_cache_blocks(prompt, sections)` — turns a prompt + section list
     into the multi-block format Bedrock expects, with `cache_control`
     attached to the cached prefix.
  2. `detect_cache_break(prev, curr)` — given two prompt-block lists,
     identify which section flipped (if any). Logs a `CacheBreakWarning`
     with the section name so the operator can see WHY the cache broke.

Phase 6 keeps the implementation deliberately small — the goal is the
contract + audit log, not the full Runnable hash-tree. Phase 12+ may
extend with per-tool hashes / global cache strategy / betas list when
those concerns arrive.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# Block model
# ============================================================

@dataclass
class CacheBlock:
    """A single content block in Bedrock's multi-block system field.

    Bedrock format:
        {"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}
    """
    text: str
    cache_control: bool = False  # True → attach `cache_control: ephemeral`

    def to_bedrock(self) -> Dict[str, Any]:
        block: Dict[str, Any] = {"type": "text", "text": self.text}
        if self.cache_control:
            block["cache_control"] = {"type": "ephemeral"}
        return block


# ============================================================
# Builder: prompt string → cache blocks
# ============================================================

# Codex Phase-06 review finding 3: import the canonical constant from
# `prompt` instead of duplicating it. Single source of truth eliminates
# the "constants disagree on trailing newline" pitfall Codex flagged.
from prompt import CACHE_BOUNDARY as CACHE_BOUNDARY_MARKER  # noqa: E402


def build_cache_blocks(prompt: str) -> List[CacheBlock]:
    """Split `prompt` on the cache boundary marker and produce the
    list of `CacheBlock`s Bedrock expects.

    Behaviour:
      - If the marker is present and the dynamic part is non-empty:
        return [static-with-cache_control, dynamic-without-cache_control].
      - If the marker is present and the dynamic part is empty/whitespace:
        return [static-with-cache_control] (single block, fully cached).
      - If the marker is absent: return [whole-prompt-with-cache_control].

    This mirrors the Phase-1 `BedrockClient.chat()` cache-block logic
    (see `runtime/bedrock_client.py`), so callers that emit blocks
    directly produce the same on-wire shape.
    """
    if CACHE_BOUNDARY_MARKER in prompt:
        static_part, dynamic_part = prompt.split(CACHE_BOUNDARY_MARKER, 1)
        if dynamic_part.strip():
            # Codex Phase-06 review finding 2: preserve `dynamic_part` exactly
            # (no lstrip) so the direct-block path is byte-equivalent to
            # `runtime/bedrock_client.py:_build_system_field` (which also
            # passes the unmodified `dynamic_part`). Byte-equivalence matters
            # for cache-hashing parity tests.
            return [
                CacheBlock(text=static_part, cache_control=True),
                CacheBlock(text=dynamic_part, cache_control=False),
            ]
        return [CacheBlock(text=static_part, cache_control=True)]
    return [CacheBlock(text=prompt, cache_control=True)]


# ============================================================
# Section-level hashing for cache-break detection
# ============================================================

@dataclass
class SectionFingerprint:
    """A snapshot of one section's content + hash. Used as the unit of
    cache-break detection."""
    name: str
    sha256: str
    length: int


@dataclass
class CacheState:
    """Snapshot of the prompt cache state for one turn."""
    section_fingerprints: List[SectionFingerprint] = field(default_factory=list)
    static_total_tokens: int = 0


def _sha256_short(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def fingerprint_sections(sections: List[Tuple[str, str]]) -> CacheState:
    """Build a CacheState from `[(name, text), ...]` sections.

    Used at the start of a session and after each `clear_section_cache()`
    to snapshot the current state.
    """
    from prompt.sections import estimate_tokens
    fps = [
        SectionFingerprint(
            name=name,
            sha256=_sha256_short(text),
            length=len(text),
        )
        for name, text in sections
    ]
    total = sum(estimate_tokens(text) for _, text in sections)
    return CacheState(section_fingerprints=fps, static_total_tokens=total)


# ============================================================
# detect_cache_break — main public API
# ============================================================

@dataclass
class CacheBreakReport:
    """Result of `detect_cache_break(prev, curr)`."""
    broke: bool
    changed_sections: List[str] = field(default_factory=list)
    added_sections: List[str] = field(default_factory=list)
    removed_sections: List[str] = field(default_factory=list)
    reordered: bool = False
    static_token_delta: int = 0


def detect_cache_break(prev: Optional[CacheState], curr: CacheState) -> CacheBreakReport:
    """Compare two cache states. Identify which section(s) changed.

    Args:
      prev: prior turn's CacheState. None = first turn (no prior to compare).
      curr: current turn's CacheState.

    Returns:
      CacheBreakReport with `broke=True` if ANY of:
        - a previously-present section's hash changed
        - a section was added
        - a section was removed
        - section order changed
      `changed_sections` lists the names of sections whose hash flipped.
      `added_sections` / `removed_sections` are name-set differences.
      `reordered=True` if the same names appear but in a different order.

    Side effect: logs a `CacheBreakWarning` for any break with the
    specific section name(s) so the operator can see WHY the cache
    invalidated. This is the single most-debugged class of cost-spike
    pattern in v4 (a flag flip silently breaks cache → next turn
    re-pays for the entire prompt).
    """
    if prev is None:
        return CacheBreakReport(broke=False)

    prev_by_name = {fp.name: fp for fp in prev.section_fingerprints}
    curr_by_name = {fp.name: fp for fp in curr.section_fingerprints}

    prev_names = [fp.name for fp in prev.section_fingerprints]
    curr_names = [fp.name for fp in curr.section_fingerprints]

    added = [n for n in curr_names if n not in prev_by_name]
    removed = [n for n in prev_names if n not in curr_by_name]
    changed = [
        n for n in curr_names
        if n in prev_by_name and curr_by_name[n].sha256 != prev_by_name[n].sha256
    ]
    reordered = (
        prev_names != curr_names
        and sorted(prev_names) == sorted(curr_names)
        and not added and not removed
    )

    broke = bool(changed or added or removed or reordered)
    delta = curr.static_total_tokens - prev.static_total_tokens

    if broke:
        details: List[str] = []
        if changed:
            details.append(f"changed=[{', '.join(changed)}]")
        if added:
            details.append(f"added=[{', '.join(added)}]")
        if removed:
            details.append(f"removed=[{', '.join(removed)}]")
        if reordered:
            details.append("reordered")
        if delta:
            details.append(f"token_delta={delta:+d}")
        logging.warning(
            "[CacheBreakWarning] prompt cache invalidated. " + "; ".join(details)
        )

    return CacheBreakReport(
        broke=broke,
        changed_sections=changed,
        added_sections=added,
        removed_sections=removed,
        reordered=reordered,
        static_token_delta=delta,
    )
