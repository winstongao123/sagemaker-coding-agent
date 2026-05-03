"""Lock test for R-tier R1 PHASE B iter-1 fix: agent loop must survive
UnicodeEncodeError on emoji output (Windows cp1252 default).

Without the fix in core/query_engine.py:_make_unicode_safe_output_fn,
the first call to `print(response.text)` containing an emoji like ✅
crashes the entire agent loop on Windows terminals — even when the
agent's substantive work (file writes) is complete.

Mock-based ($0); no AWS spend.
"""
from __future__ import annotations

import os
import sys

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def test_unicode_safe_output_fn_swallows_encode_error():
    """Wrapped output_fn returns normally when the inner fn raises
    UnicodeEncodeError on the first attempt; falls back to safe encoding.

    Contract: the wrapper MUST NOT propagate UnicodeEncodeError. The
    text reaching the fallback may still contain the emoji if the
    terminal encoding (sys.stdout.encoding) supports it — that's a
    feature, not a bug (utf-8 terminals see full text). The hard
    invariant is: no raise + the human-readable bits are preserved.
    """
    from core.query_engine import _make_unicode_safe_output_fn

    captured: list = []
    call_count = {"n": 0}

    def _strict_fn(text: str) -> None:
        call_count["n"] += 1
        # Simulate a cp1252 stdout: raise on the first call (emoji).
        if call_count["n"] == 1 and any(ord(c) > 0xFF for c in text):
            raise UnicodeEncodeError("charmap", text, 0, 1, "<undefined>")
        captured.append(text)

    safe = _make_unicode_safe_output_fn(_strict_fn)
    # Must not raise.
    safe("Perfect! ✅ Done.")
    assert captured, "fallback path must succeed"
    # Human-readable parts preserved.
    assert "Perfect!" in captured[0]
    assert "Done." in captured[0]
    # Inner fn was called twice: first call raised, second call succeeded.
    assert call_count["n"] == 2


def test_unicode_safe_output_fn_passthrough_on_utf8():
    """When the inner fn doesn't raise (UTF-8 terminal), text passes through unchanged."""
    from core.query_engine import _make_unicode_safe_output_fn

    captured: list = []
    safe = _make_unicode_safe_output_fn(captured.append)
    safe("Perfect! ✅ Done.")
    assert captured == ["Perfect! ✅ Done."]


def test_unicode_safe_output_fn_handles_lookup_error():
    """If sys.stdout.encoding is bogus, the ASCII final fallback kicks in."""
    from core.query_engine import _make_unicode_safe_output_fn

    captured: list = []

    def _double_fail(text: str) -> None:
        # First call raises; second call (with replace-encoded text) raises again.
        if "✅" in text:
            raise UnicodeEncodeError("charmap", text, 0, 1, "<undefined>")
        captured.append(text)

    safe = _make_unicode_safe_output_fn(_double_fail)
    # Must not raise even when the inner fn fails repeatedly on emoji.
    safe("Hi ✅")
    assert captured, "ASCII final fallback must succeed"
    # ASCII fallback replaces non-ASCII chars; "Hi" preserved.
    assert "Hi" in captured[0]
    # The emoji must NOT survive the ASCII-replace path.
    assert "✅" not in captured[0]
