"""Block E+F — env_block + ADR-020 0-2/0-4/0-6 remap closure.

Phase 6 (sectioned prompt) + Phase 11 (notebook UX) shipped most of
the v4-vs-Runnable Block E+F surface. This test file covers the
remaining ADR-020 remap rows that landed in Block E+F per ADR-020 §
Notes / known scope remaps:

  0-2 — getSessionStartDate / getLocalMonthYear (cache-stable date)
  0-4 — env block format (Windows-shell hint, OS, Notes appendix)
  0-6 — getKnowledgeCutoff (model-specific cutoff)
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


# ============================================================
# ADR-020 0-2 — date helpers (cache-stable)
# ============================================================

def test_session_start_date_memoized():
    """First call caches the date string; subsequent calls return it."""
    from prompt.env_block import get_session_start_date, _reset_caches_for_tests

    _reset_caches_for_tests()
    d1 = get_session_start_date()
    d2 = get_session_start_date()
    assert d1 == d2
    # Format: YYYY-MM
    assert len(d1) == 7
    assert d1[4] == "-"


def test_local_month_year_human_readable():
    from prompt.env_block import get_local_month_year

    s = get_local_month_year()
    # E.g. "May 2026" — should contain a space + 4-digit year.
    parts = s.split()
    assert len(parts) == 2
    assert parts[1].isdigit() and len(parts[1]) == 4


def test_env_block_uses_month_year_not_iso_date():
    """ADR-020 0-2 lock: env_block contains month-year (cache-stable)
    NOT a full ISO date (cache-busts daily)."""
    from prompt.env_block import render_env_block

    body = render_env_block(workspace="/tmp", model_id="x")
    # Should NOT contain a YYYY-MM-DD pattern.
    import re
    iso_dates = re.findall(r"\d{4}-\d{2}-\d{2}", body)
    assert not iso_dates, (
        f"env_block must NOT contain ISO dates (cache-bust risk); "
        f"found: {iso_dates}"
    )
    # Should contain month-year form.
    months = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    assert any(m in body for m in months), (
        "env_block should contain a month-year string"
    )


# ============================================================
# ADR-020 0-6 — knowledge cutoff
# ============================================================

def test_knowledge_cutoff_haiku_4_5():
    from prompt.env_block import get_knowledge_cutoff
    assert get_knowledge_cutoff("anthropic.claude-haiku-4-5-20251001-v1:0") == "October 2025"


def test_knowledge_cutoff_sonnet_4_5():
    from prompt.env_block import get_knowledge_cutoff
    assert get_knowledge_cutoff("anthropic.claude-sonnet-4-5-20250929-v1:0") == "September 2025"


def test_knowledge_cutoff_strips_au_prefix():
    """ADR-020 0-6 lock: cross-region inference prefixes (au./apac./us./eu.)
    must be stripped before cutoff lookup."""
    from prompt.env_block import get_knowledge_cutoff
    assert get_knowledge_cutoff("au.anthropic.claude-haiku-4-5-20251001-v1:0") == "October 2025"
    assert get_knowledge_cutoff("apac.anthropic.claude-sonnet-4-5-20250929-v1:0") == "September 2025"
    assert get_knowledge_cutoff("us.anthropic.claude-3-5-sonnet-20241022-v2:0") == "October 2024"


def test_knowledge_cutoff_unknown_model_default():
    from prompt.env_block import get_knowledge_cutoff
    cutoff = get_knowledge_cutoff("anthropic.claude-future-99-x")
    assert "early" in cutoff.lower() or "20" in cutoff


def test_env_block_emits_model_specific_knowledge_cutoff():
    """ADR-020 0-6 lock: render_env_block uses get_knowledge_cutoff."""
    from prompt.env_block import render_env_block

    haiku_body = render_env_block(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
    sonnet_body = render_env_block(model_id="anthropic.claude-sonnet-4-5-20250929-v1:0")
    assert "October 2025" in haiku_body
    assert "September 2025" in sonnet_body


# ============================================================
# ADR-020 0-4 — env block format (Windows hint, OS, Notes)
# ============================================================

def test_env_block_includes_shell_hint_and_notes():
    """ADR-020 0-4 lock: env_block has OS, shell, and a Notes appendix."""
    from prompt.env_block import render_env_block

    body = render_env_block(workspace="/tmp", model_id="x")
    # OS line
    assert "## Environment" in body
    assert "OS:" in body
    assert "Shell:" in body
    assert "Working directory" in body
    # Notes appendix
    assert "## Notes" in body


def test_env_block_windows_shell_hint(monkeypatch):
    """On Windows, shell hint must mention PowerShell syntax. On
    POSIX, shell hint must be a non-empty string referencing a real
    shell (bash / zsh / sh)."""
    from prompt import env_block as eb_mod

    hint = eb_mod.get_shell_hint()
    assert isinstance(hint, str) and hint, "shell hint must be non-empty"
    if sys.platform == "win32" or os.name == "nt":
        assert "PowerShell" in hint or "powershell" in hint.lower()
    else:
        # POSIX — env $SHELL OR a sane default.
        lower = hint.lower()
        assert any(s in lower for s in ("bash", "zsh", "sh", "fish", "/bin/")), (
            f"POSIX shell hint should reference a real shell; got: {hint!r}"
        )


def test_env_block_no_streaming_note():
    """Constraint #10 enforcement — env_block reminds the model
    streaming is unsupported."""
    from prompt.env_block import render_env_block

    body = render_env_block(workspace="/tmp", model_id="x")
    assert "treaming" in body.lower()  # "Streaming is NOT supported"
    assert ("not supported" in body.lower()
            or "no streaming" in body.lower()
            or "NOT supported" in body)


# ============================================================
# render_env_block defaults
# ============================================================

def test_render_env_block_uses_config_defaults(monkeypatch):
    from runtime.config import CONFIG
    from prompt.env_block import render_env_block

    monkeypatch.setattr(CONFIG, "workspace", "/test/workspace")
    monkeypatch.setattr(CONFIG, "model_id", "anthropic.claude-haiku-4-5-20251001-v1:0")

    body = render_env_block()
    assert "/test/workspace" in body
    assert "claude-haiku-4-5" in body
    assert "October 2025" in body


# ============================================================
# Codex Block-E+F iter-1 finding-lock tests
# ============================================================

def test_render_env_block_session_start_uses_memoized_helper():
    """Codex iter-1 finding #2 lock: render_env_block uses the lru_cached
    `get_session_start_date()` for the "Session start" line, not the
    non-memoized month-year (which would shift on month boundary)."""
    from prompt.env_block import (
        render_env_block,
        get_session_start_date,
        _reset_caches_for_tests,
    )

    _reset_caches_for_tests()
    expected = get_session_start_date()
    body = render_env_block(workspace="/tmp", model_id="x")
    assert f"Session start: {expected}" in body, (
        f"render_env_block must use memoized session-start; "
        f"got body without `Session start: {expected}`"
    )


def test_build_system_prompt_includes_env_block(monkeypatch):
    """Codex iter-1 finding #1 (HIGH) lock: build_system_prompt wires
    render_env_block into the dynamic tail. Without this, env_block
    is helper-only and the ADR-020 remap closure isn't real."""
    from prompt import build_system_prompt

    body = build_system_prompt(ctx={
        "workspace": "/test/ws",
        "model_id": "anthropic.claude-haiku-4-5-20251001-v1:0",
    })
    # The env_block must appear in the assembled system prompt.
    assert "## Environment" in body, (
        "build_system_prompt must splice render_env_block into the dynamic tail"
    )
    assert "/test/ws" in body
    assert "October 2025" in body  # haiku knowledge-cutoff


def test_build_system_prompt_skip_env_block_optout():
    """ctx['skip_env_block']=True opts out so existing tests that pin
    a specific prompt shape are unaffected."""
    from prompt import build_system_prompt

    body = build_system_prompt(ctx={"skip_env_block": True})
    assert "## Environment" not in body
