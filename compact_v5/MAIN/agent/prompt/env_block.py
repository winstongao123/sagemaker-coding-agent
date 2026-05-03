"""Block E+F (ADR-020 0-2/0-4/0-6 remaps) — env-block formatter.

Ports Runnable's env-detail builders so the system prompt's `env_block`
section gets cache-stable date strings + accurate knowledge-cutoff for
the current model + Windows-shell hint when applicable.

Closes ADR-020 §Notes / known scope remaps rows:
  0-2 — getSessionStartDate / getLocalMonthYear (R8 #67) — cache-stable
  0-4 — env block format (R8 #76, #79) — Windows-shell hint, OS, Notes
  0-6 — getKnowledgeCutoff (R8 #39) — model-specific cutoff per Sonnet
        4.6 / Haiku 4.5

Why "month-year not ISO": tool prompts that mention "today's date as
2026-05-03" cause the prompt-cache to bust at midnight. Month-year
("May 2026") changes monthly, not daily, so the cache survives full days.

PORT_LOG: see #071.
"""
from __future__ import annotations

import os
import platform
import sys
from datetime import datetime
from functools import lru_cache
from typing import Optional


# ============================================================
# Date helpers (ADR-020 0-2 remap)
# ============================================================

@lru_cache(maxsize=1)
def get_session_start_date() -> str:
    """Memoized session-start date in `YYYY-MM` form (cache-stable).

    Cached at first call so successive calls within the session return
    the same value even if the wall clock crosses midnight. Prevents
    midnight-boundary cache busts.
    """
    return datetime.now().strftime("%Y-%m")


def get_local_month_year() -> str:
    """Render the current month-year in human-readable form.

    Cache-stable across same-month days (changes monthly, not daily).
    Used in env-block instead of full ISO date so prompt-cache lasts
    longer than 24 hours.
    """
    now = datetime.now()
    return now.strftime("%B %Y")


# ============================================================
# Knowledge cutoff (ADR-020 0-6 remap)
# ============================================================

# Model-specific knowledge cutoffs as of 2026 model lineup. Per Runnable
# constants/prompts.ts:712-730 (R8 #39).
_KNOWLEDGE_CUTOFFS: dict = {
    # Haiku 4.5 (Bedrock + Anthropic-direct)
    "anthropic.claude-haiku-4-5-20251001-v1:0": "October 2025",
    "claude-haiku-4-5-20251001": "October 2025",
    # Sonnet 4.5 (Bedrock direct + AU cross-region inference profile)
    "anthropic.claude-sonnet-4-5-20250929-v1:0": "September 2025",
    "au.anthropic.claude-sonnet-4-5-20250929-v1:0": "September 2025",
    # Sonnet 3.5 baseline
    "anthropic.claude-3-5-sonnet-20241022-v2:0": "October 2024",
}

_KNOWLEDGE_CUTOFF_DEFAULT = "early 2025"


def get_knowledge_cutoff(model_id: str) -> str:
    """Return the human-readable knowledge cutoff for `model_id`.

    Strips Bedrock cross-region prefixes (au./apac./us./eu.) before
    lookup so au.anthropic.claude-haiku-4-5-... matches the canonical
    haiku entry. Falls back to a generic "early 2025" for unknown models.
    """
    if not model_id:
        return _KNOWLEDGE_CUTOFF_DEFAULT
    try:
        from runtime.tokens import canonicalize_model_id
        canonical = canonicalize_model_id(model_id)
    except Exception:
        canonical = model_id
    return _KNOWLEDGE_CUTOFFS.get(canonical, _KNOWLEDGE_CUTOFF_DEFAULT)


# ============================================================
# OS / shell hint (ADR-020 0-4 remap)
# ============================================================

def get_os_string() -> str:
    """Human-readable OS + version + machine."""
    sys_name = platform.system()
    release = platform.release()
    machine = platform.machine()
    return f"{sys_name} {release} ({machine})"


def get_shell_hint() -> str:
    """Best-guess shell name for the platform.

    On Windows, defaults to PowerShell — bash via WSL is also common
    but the agent surface assumes the platform-default shell unless
    the user passes a different `shell` arg to the bash tool.
    """
    if sys.platform == "win32" or os.name == "nt":
        return "PowerShell (use PowerShell syntax — e.g., $null not /dev/null)"
    return f"{os.environ.get('SHELL', 'bash')}"


# ============================================================
# Render the full env block
# ============================================================

def render_env_block(
    *,
    workspace: Optional[str] = None,
    model_id: Optional[str] = None,
) -> str:
    """Render the env-block markdown body.

    Pulls workspace from CONFIG when not passed, model_id from CONFIG
    when not passed. Output is the body that `prompt/sections.py`
    splices into the dynamic tail of the system prompt.

    Notes appendix is included when relevant (Windows-shell warning;
    no-streaming reminder per constraint #10).
    """
    from runtime.config import CONFIG
    workspace = workspace or CONFIG.workspace
    model_id = model_id or CONFIG.model_id

    # Codex Block-E+F iter-1 finding #2 lock: "Session start" must use
    # the memoized YYYY-MM helper so a session that crosses month
    # boundary keeps the same value (the label says "Session START";
    # the start IS the cached first-call value).
    parts = [
        "## Environment",
        "",
        f"- Working directory: `{workspace}`",
        f"- OS: {get_os_string()}",
        f"- Shell: {get_shell_hint()}",
        f"- Session start: {get_session_start_date()}",
        f"- Current month: {get_local_month_year()}",
        f"- Model: `{model_id}`",
        f"- Knowledge cutoff: {get_knowledge_cutoff(model_id)}",
        "",
        "## Notes",
        "",
    ]
    notes: list = []
    if sys.platform == "win32" or os.name == "nt":
        notes.append(
            "- Bash tool runs PowerShell on Windows by default. "
            "Use PowerShell syntax (`$env:VAR`, not `$VAR`)."
        )
    notes.append("- Streaming is NOT supported on this Bedrock SageMaker deployment.")
    notes.append(
        "- Today's month-year shown above is cache-stable; do NOT assume "
        "full ISO date is current — query bash `date` if you need precision."
    )
    parts.extend(notes)
    return "\n".join(parts)


def _reset_caches_for_tests() -> None:
    """Clear lru_cache for date helpers so tests can re-evaluate."""
    get_session_start_date.cache_clear()


__all__ = [
    "get_session_start_date",
    "get_local_month_year",
    "get_knowledge_cutoff",
    "get_os_string",
    "get_shell_hint",
    "render_env_block",
]
