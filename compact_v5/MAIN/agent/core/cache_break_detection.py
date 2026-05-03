"""V5 core/cache_break_detection.py — Block L per-tool cache-break detection.

PORT_LOG: #101.

Source: Runnable services/api/cacheBreakDetection.ts.

When a tool's schema changes between turns, the prompt cache is invalidated
for that tool. This module detects per-tool schema changes by hashing each
tool's schema and comparing against a per-engine baseline.

R4 #14 MUST: Haiku-4.5 model_id is in the EXCLUDED_MODELS set — Haiku
doesn't support prompt-cache deletion notifications, so the detector
skips these models entirely. Bedrock returns a 400 error if you call
notify_cache_deletion() on Haiku; the exclusion preserves API validity.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Set


# Block L (R4 #14 MUST): models that don't support prompt-cache
# deletion. Haiku 4.5 in particular: notify_cache_deletion() raises
# ValidationException on these. Cross-region prefixes (au./apac./
# us./eu.) are stripped before lookup.
_EXCLUDED_MODELS_3LOC: frozenset = frozenset({
    "anthropic.claude-haiku-4-5-20251001-v1:0",
    "anthropic.claude-haiku-4-1-20250228-v1:0",  # also exclude prior Haiku
    "anthropic.claude-3-5-haiku-20241022-v1:0",
})


def _strip_region_prefix(model_id: str) -> str:
    """Strip cross-region inference prefixes (au./apac./us./eu./global.)
    so the EXCLUDED_MODELS lookup matches both `au.anthropic...` and
    `anthropic...` forms.
    """
    for prefix in ("au.", "apac.", "us.", "eu.", "global.", "ap.", "in."):
        if model_id.startswith(prefix):
            return model_id[len(prefix):]
    return model_id


def is_cache_break_excluded(model_id: str) -> bool:
    """R4 #14 MUST: True iff model_id is in the cache-break-detection
    EXCLUDED set. Haiku 4.5 in particular.
    """
    if not model_id:
        return False
    return _strip_region_prefix(model_id) in _EXCLUDED_MODELS_3LOC


def hash_tool_schema(tool_schema: Dict[str, Any]) -> str:
    """Stable hash of a tool schema. Two semantically identical schemas
    (different key order) produce the same hash.

    Block L per-tool detection: a tool is cache-broken iff its schema
    hash changed between turns.
    """
    canonical = json.dumps(tool_schema, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class PerToolCacheBreakDetector:
    """Tracks per-tool schema hashes across turns.

    Usage:
        detector = PerToolCacheBreakDetector()
        # Turn 1:
        detector.update_baseline(tools)
        # Turn 2:
        broken = detector.detect_breaks(tools, model_id="anthropic.claude-...")
        # broken is a list of tool names whose schemas changed.

    If model_id is in the EXCLUDED set, detect_breaks() returns [] —
    skips the entire detection path because notify_cache_deletion()
    isn't supported on those models.
    """

    def __init__(self) -> None:
        self._baseline: Dict[str, str] = {}

    def update_baseline(self, tools: List[Dict[str, Any]]) -> None:
        """Snapshot the current schema hashes as the baseline."""
        self._baseline = {
            t.get("name", ""): hash_tool_schema(t)
            for t in tools or []
            if t.get("name")
        }

    def detect_breaks(
        self,
        tools: List[Dict[str, Any]],
        model_id: str = "",
    ) -> List[str]:
        """Return list of tool names whose schemas changed since the last
        update_baseline() call.

        R4 #14: when model_id is in the cache-break EXCLUDED set, skips
        detection entirely (returns []). The notify_cache_deletion()
        call would fail with 400 on those models.
        """
        if is_cache_break_excluded(model_id):
            return []
        if not self._baseline:
            # First call — establish baseline; no breaks reported.
            self.update_baseline(tools)
            return []

        broken: List[str] = []
        current = {
            t.get("name", ""): hash_tool_schema(t)
            for t in tools or []
            if t.get("name")
        }
        for name, h in current.items():
            prev = self._baseline.get(name)
            if prev is not None and prev != h:
                broken.append(name)
        # Update baseline so subsequent calls compare against latest.
        self._baseline = current
        return broken


def notify_cache_deletion(
    model_id: str,
    tool_names: List[str],
) -> bool:
    """Issue a cache-deletion notification for the given tools.

    Block L: when tool schemas change, Bedrock's prompt cache for those
    tool entries is stale; this helper would normally call the Bedrock
    invalidation endpoint. v5's stub: log + return True for non-excluded
    models, return False (skip) for EXCLUDED models.

    The actual Bedrock endpoint integration is wired by core/query_engine
    on the next chat() call's `additionalModelRequestFields`.
    """
    if is_cache_break_excluded(model_id):
        return False  # skip
    # Real wiring would go here; v5 stub just signals "should notify".
    import logging
    logging.info(
        "[cache-break] notify_cache_deletion model=%s tools=%s",
        model_id, tool_names,
    )
    return True
