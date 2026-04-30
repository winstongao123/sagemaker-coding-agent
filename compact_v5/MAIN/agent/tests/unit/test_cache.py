"""Phase 06 unit tests: core/cache.py — cache-break detection.

Locks the contract for ADR-013 (PORT_LOG #013): Runnable's
`promptCacheBreakDetection.ts` adapted to v5. Logs CacheBreakWarning
when ANY section's hash flips, when sections are added/removed, or
when section order changes.
"""
from __future__ import annotations

import logging
import os
import sys

import pytest

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# fingerprint_sections + CacheState
# ============================================================

def test_fingerprint_sections_produces_stable_hashes():
    from core.cache import fingerprint_sections
    sections = [("a", "alpha content"), ("b", "beta content")]
    fp1 = fingerprint_sections(sections)
    fp2 = fingerprint_sections(sections)
    assert [f.sha256 for f in fp1.section_fingerprints] == [f.sha256 for f in fp2.section_fingerprints]
    assert fp1.static_total_tokens == fp2.static_total_tokens


def test_fingerprint_changes_when_content_changes():
    from core.cache import fingerprint_sections
    fp1 = fingerprint_sections([("a", "v1")])
    fp2 = fingerprint_sections([("a", "v2-different")])
    assert fp1.section_fingerprints[0].sha256 != fp2.section_fingerprints[0].sha256


# ============================================================
# detect_cache_break
# ============================================================

def test_detect_cache_break_no_prev_returns_no_break():
    """First turn (no previous state) cannot break the cache."""
    from core.cache import fingerprint_sections, detect_cache_break
    curr = fingerprint_sections([("a", "x"), ("b", "y")])
    report = detect_cache_break(None, curr)
    assert report.broke is False


def test_detect_cache_break_unchanged_does_not_break():
    from core.cache import fingerprint_sections, detect_cache_break
    sections = [("a", "x"), ("b", "y")]
    prev = fingerprint_sections(sections)
    curr = fingerprint_sections(sections)
    report = detect_cache_break(prev, curr)
    assert report.broke is False


def test_detect_cache_break_section_content_change(caplog):
    from core.cache import fingerprint_sections, detect_cache_break
    prev = fingerprint_sections([("a", "x"), ("b", "y")])
    curr = fingerprint_sections([("a", "x"), ("b", "y-CHANGED")])
    with caplog.at_level(logging.WARNING):
        report = detect_cache_break(prev, curr)
    assert report.broke is True
    assert report.changed_sections == ["b"]
    assert "[CacheBreakWarning]" in caplog.text
    assert "changed=[b]" in caplog.text


def test_detect_cache_break_section_added():
    from core.cache import fingerprint_sections, detect_cache_break
    prev = fingerprint_sections([("a", "x")])
    curr = fingerprint_sections([("a", "x"), ("b", "y")])
    report = detect_cache_break(prev, curr)
    assert report.broke is True
    assert report.added_sections == ["b"]


def test_detect_cache_break_section_removed():
    from core.cache import fingerprint_sections, detect_cache_break
    prev = fingerprint_sections([("a", "x"), ("b", "y")])
    curr = fingerprint_sections([("a", "x")])
    report = detect_cache_break(prev, curr)
    assert report.broke is True
    assert report.removed_sections == ["b"]


def test_detect_cache_break_reordered():
    from core.cache import fingerprint_sections, detect_cache_break
    prev = fingerprint_sections([("a", "x"), ("b", "y")])
    curr = fingerprint_sections([("b", "y"), ("a", "x")])
    report = detect_cache_break(prev, curr)
    assert report.broke is True
    assert report.reordered is True


def test_detect_cache_break_token_delta_reported():
    from core.cache import fingerprint_sections, detect_cache_break
    prev = fingerprint_sections([("a", "short")])
    curr = fingerprint_sections([("a", "much much much much longer content x" * 10)])
    report = detect_cache_break(prev, curr)
    assert report.broke is True
    assert report.static_token_delta > 0


# ============================================================
# Integration: detect_cache_break across actual prompt sections
# ============================================================

def test_detect_no_break_when_prompt_unchanged_across_turns():
    """Calling build_system_prompt() twice without any section edit
    must NOT trigger a cache break."""
    from prompt.sections import all_sections, clear_section_cache
    from core.cache import fingerprint_sections, detect_cache_break

    clear_section_cache()
    prev = fingerprint_sections(all_sections())
    curr = fingerprint_sections(all_sections())
    report = detect_cache_break(prev, curr)
    assert report.broke is False
