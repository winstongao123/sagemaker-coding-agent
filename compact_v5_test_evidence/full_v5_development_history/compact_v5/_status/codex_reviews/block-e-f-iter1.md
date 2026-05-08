OpenAI Codex v0.125.0 (research preview)
--------
workdir: D:\Github\sagemaker-coding-agent
model: gpt-5.3-codex
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, C:\Users\winst\.codex\memories]
reasoning effort: high
reasoning summaries: none
session id: 019debf6-05fc-7852-bd62-5d11326d009f
--------
user
Review Block E+F of v5.0.1: env_block + ADR-020 0-2/0-4/0-6 remap closure.

Phase 6 + Phase 11 already shipped most of the v4-vs-Runnable Block E+F surface. This Block adds the 3 remaining ADR-020 remap rows for env-block content:
- 0-2: cache-stable date helpers (get_session_start_date lru_cached + get_local_month_year)
- 0-4: env block format with Windows shell hint, OS, Notes appendix
- 0-6: get_knowledge_cutoff with 5-model lookup + cross-region prefix strip

Read these 2 files:
- compact_v5/MAIN/agent/prompt/env_block.py (~125 LOC)
- compact_v5/MAIN/agent/tests/integration/test_block_e_f.py (12 lock tests)

3-axis review:
AXIS A: errors / regressions / security (lru_cache correctness; cross-region prefix logic; OS detection portability). Verdict: PASS / CHANGES_REQUESTED / BLOCKER.
AXIS B: v5 fit (closes ADR-020 0-2/0-4/0-6 with cache-stability rule preserved). Verdict: FAITHFUL / FAITHFUL-WITH-JUSTIFIED-ADAPTATION / DRIFTED.
AXIS C: covers ADR-020 0-2 + 0-4 + 0-6? Anything UNDECLARED_PATTERN?

Tests: 587 pass + 5 skip (was 575; +12 net new).

FINAL: APPROVE | APPROVE_WITH_FIXES | REJECT.

codex
Reviewing those two files now against ADR-020 rows `0-2/0-4/0-6`, with focus on cache behavior, region-prefix stripping, and portability. I’ll inspect implementation and the 12 lock tests first, then give axis verdicts plus final disposition.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path "compact_v5/MAIN/agent/prompt/env_block.py"' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path "compact_v5/MAIN/agent/tests/integration/test_block_e_f.py"' in D:\Github\sagemaker-coding-agent
 succeeded in 489ms:
"""Block E+F â€” env_block + ADR-020 0-2/0-4/0-6 remap closure.

Phase 6 (sectioned prompt) + Phase 11 (notebook UX) shipped most of
the v4-vs-Runnable Block E+F surface. This test file covers the
remaining ADR-020 remap rows that landed in Block E+F per ADR-020 Â§
Notes / known scope remaps:

  0-2 â€” getSessionStartDate / getLocalMonthYear (cache-stable date)
  0-4 â€” env block format (Windows-shell hint, OS, Notes appendix)
  0-6 â€” getKnowledgeCutoff (model-specific cutoff)
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
# ADR-020 0-2 â€” date helpers (cache-stable)
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
    # E.g. "May 2026" â€” should contain a space + 4-digit year.
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
# ADR-020 0-6 â€” knowledge cutoff
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
# ADR-020 0-4 â€” env block format (Windows hint, OS, Notes)
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
    """On Windows, shell hint must mention PowerShell syntax."""
    from prompt import env_block as eb_mod

    if sys.platform == "win32" or os.name == "nt":
        # Native Windows â€” verify the hint actually mentions PowerShell.
        hint = eb_mod.get_shell_hint()
        assert "PowerShell" in hint or "powershell" in hint.lower()


def test_env_block_no_streaming_note():
    """Constraint #10 enforcement â€” env_block reminds the model
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

 succeeded in 515ms:
"""Block E+F (ADR-020 0-2/0-4/0-6 remaps) â€” env-block formatter.

Ports Runnable's env-detail builders so the system prompt's `env_block`
section gets cache-stable date strings + accurate knowledge-cutoff for
the current model + Windows-shell hint when applicable.

Closes ADR-020 Â§Notes / known scope remaps rows:
  0-2 â€” getSessionStartDate / getLocalMonthYear (R8 #67) â€” cache-stable
  0-4 â€” env block format (R8 #76, #79) â€” Windows-shell hint, OS, Notes
  0-6 â€” getKnowledgeCutoff (R8 #39) â€” model-specific cutoff per Sonnet
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
    # Sonnet 4.5
    "anthropic.claude-sonnet-4-5-20250929-v1:0": "September 2025",
    # Sonnet 4.6 (newest)
    "anthropic.claude-sonnet-4-6-20260101-v1:0": "January 2026",
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

    On Windows, defaults to PowerShell â€” bash via WSL is also common
    but the agent surface assumes the platform-default shell unless
    the user passes a different `shell` arg to the bash tool.
    """
    if sys.platform == "win32" or os.name == "nt":
        return "PowerShell (use PowerShell syntax â€” e.g., $null not /dev/null)"
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

    parts = [
        "## Environment",
        "",
        f"- Working directory: `{workspace}`",
        f"- OS: {get_os_string()}",
        f"- Shell: {get_shell_hint()}",
        f"- Session start: {get_local_month_year()}",
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
        "full ISO date is current â€” query bash `date` if you need precision."
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

codex
I’ve read both target files; next I’m checking `runtime.tokens.canonicalize_model_id` and running the new integration test file to validate the cross-region behavior end-to-end.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path "compact_v5/MAIN/agent/runtime/tokens.py"' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'python -m pytest -q "compact_v5/MAIN/agent/tests/integration/test_block_e_f.py"' in D:\Github\sagemaker-coding-agent
 succeeded in 516ms:
"""Block B â€” TokenTracker + per-agent attribution + tokenEstimation helpers.

Verbatim port of v4's `TokenTracker` (compact_v4/MAIN/agent/sagemaker_agent.py
lines 3565-3753) plus:
- per-agent input/output/cost attribution (B-11 + Plan v3 Â§Block B)
- MODEL_COSTS for Haiku 4.5 + Sonnet 4.6 (B-10, R8 #34/#68)
- EXCLUDED_MODELS_FOR_CACHE_BREAK Haiku set (R4 #14 MUST)
- IMAGE_MAX_TOKEN_SIZE = 2000 (B-5, R4 #38)
- bytesPerTokenForFileType (B-3, R4 #40)
- estimateMessageTokens 4/3 padding (B-6, R4 #39)
- hasThinkingBlocks helper (B-7, R4 #43)
- roughTokenCountEstimationForBlock (B-4, R4 #44)
- finalContextTokensFromLastResponse (B-9, R8 #16)
- tokenCountWithEstimation walks back to last usage record (B-8, R8 #15)
- ToolResult dataclass (B-13, V1 gap #1)

PORT_LOG: see #039 (TokenTracker), #040 (MODEL_COSTS+per-agent),
#041 (Runnable tokenEstimation helpers), #042 (ToolResult).
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ============================================================
# B-13 â€” ToolResult dataclass (V1 gap #1, MUST)
# ============================================================

@dataclass
class ToolResult:
    """Result envelope for a single tool execution.

    Verbatim port of v4 `compact_v4/MAIN/agent/sagemaker_agent.py:867-886`
    metadata fields. v5 tools return either a plain string OR a ToolResult
    so callers can introspect truncation + size for token-accounting.
    """
    output: str
    tool_name: str = ""
    truncated: bool = False
    total_size: int = 0          # bytes/chars before truncation
    shown_size: int = 0          # bytes/chars after truncation
    error: bool = False
    error_message: str = ""


# ============================================================
# B-10 â€” MODEL_COSTS (R8 #34, #68; Bedrock-only subset)
# ============================================================
#
# 2-row Bedrock pricing table per the user's deployment (Haiku 4.5 +
# Sonnet 4.6). Cache pricing math: cache_read = 10% of base input,
# cache_write = 125% of base input. Output = full price. All values are
# USD per 1K tokens, current as of 2026-04 Bedrock list pricing.
#
# Cross-region inference profile prefixes (`apac.`, `us.`, `eu.`) collapse
# to canonical model id via `canonicalize_model_id()`.

MODEL_COSTS: Dict[str, Dict[str, float]] = {
    "anthropic.claude-haiku-4-5-20251001-v1:0": {"input": 0.001, "output": 0.005},
    "anthropic.claude-sonnet-4-5-20250929-v1:0": {"input": 0.003, "output": 0.015},
    # Phase-1 baseline kept for parity tests
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {"input": 0.003, "output": 0.015},
}

# Backwards-compat alias (v4 internal name used inside TokenTracker.add).
_MODEL_PRICING = MODEL_COSTS


def canonicalize_model_id(model_id: str) -> str:
    """Strip Bedrock cross-region inference prefixes.

    Per Runnable cost-tracker.ts:181-226 (R11 N9). v5 collapses
    `apac.anthropic.claude-haiku-4-5-...` and
    `anthropic.claude-haiku-4-5-...` to the same canonical key for
    pricing lookup. Bedrock inference-profile prefixes covered:
        au.   â€” Australia (Sydney; ap-southeast-2 default)
        apac. â€” Asia-Pacific
        us.   â€” United States (legacy us-east-1 / us-west-2)
        eu.   â€” Europe (legacy eu-west-1 / eu-central-1)

    Codex Block-B finding #1 (HIGH) lock: `au.` was missing originally,
    causing CONFIG.model_id="au.anthropic.claude-sonnet-4-5-..." to
    miss MODEL_COSTS entirely and TOKENS to record $0.
    """
    if not model_id:
        return model_id
    for prefix in ("au.", "apac.", "us.", "eu."):
        if model_id.startswith(prefix):
            return model_id[len(prefix):]
    return model_id


# ============================================================
# R4 #14 â€” EXCLUDED_MODELS_FOR_CACHE_BREAK (MUST)
# ============================================================
#
# Haiku-4.5 cache hashing in Bedrock is non-deterministic in a way that
# the prompt-cache-break detector misreads as a "section flipped". Add
# Haiku to the exclusion set so cache-break warnings don't fire on Haiku
# sessions. This is a MUST per Wave-5-DEEP R4 #14.

EXCLUDED_MODELS_FOR_CACHE_BREAK: set = {
    "anthropic.claude-haiku-4-5-20251001-v1:0",
}


# ============================================================
# B-5 â€” IMAGE_MAX_TOKEN_SIZE (R4 #38)
# ============================================================
#
# Per Anthropic billing: each image consumed by Bedrock counts for at
# most 2000 tokens regardless of resolution. Used by the rough estimator
# below.

IMAGE_MAX_TOKEN_SIZE: int = 2000


# ============================================================
# B-3 â€” bytesPerTokenForFileType (R4 #40)
# ============================================================
#
# Different file types compress to tokens differently. JSON is dense
# (~2 bytes/token); plain text is sparse (~4 bytes/token). Used by the
# rough estimator to avoid underestimating big JSON tool returns.

_BYTES_PER_TOKEN_BY_EXT: Dict[str, float] = {
    ".json": 2.0,
    ".jsonl": 2.0,
    ".csv": 3.0,
    ".tsv": 3.0,
    ".xml": 2.5,
    ".html": 2.5,
    ".yaml": 3.0,
    ".yml": 3.0,
    ".py": 3.5,
    ".js": 3.5,
    ".ts": 3.5,
    ".md": 4.0,
    ".txt": 4.0,
}


def bytes_per_token_for_file_type(filename: str) -> float:
    """Return the bytes-per-token ratio for a filename's extension.

    Falls back to 4.0 (plain-text) for unknown extensions. Used by the
    rough estimator to budget tool output sizes.
    """
    if not filename:
        return 4.0
    lower = filename.lower()
    for ext, ratio in _BYTES_PER_TOKEN_BY_EXT.items():
        if lower.endswith(ext):
            return ratio
    return 4.0


# ============================================================
# B-6 â€” estimateMessageTokens with 4/3 padding (R4 #39)
# ============================================================

def estimate_message_tokens(text: str, padding_factor: float = 4.0 / 3.0) -> int:
    """Rough token estimator with 4/3 padding (Bedrock-side overhead).

    v4 used `len(text) // 3`. Runnable's microCompact.ts:164-205 adds a
    4/3 multiplier so the estimate accounts for Bedrock framing tokens
    (turn boundaries, role markers). Returns ceil(len/3 * 4/3) = len*4/9
    rounded up.
    """
    if not text:
        return 0
    base = len(text) / 3.0
    return int(base * padding_factor + 0.5)


# ============================================================
# B-7 â€” hasThinkingBlocks (R4 #43)
# ============================================================

def has_thinking_blocks(message: Dict[str, Any]) -> bool:
    """True if a message contains an Anthropic-format `thinking` block.

    Used to gate `count_tokens` requests so we send the same content
    shape the assistant turn would produce. Per R4 #43.
    """
    if not isinstance(message, dict):
        return False
    content = message.get("content")
    if not isinstance(content, list):
        return False
    for block in content:
        if isinstance(block, dict) and block.get("type") in {"thinking", "redacted_thinking"}:
            return True
    return False


# ============================================================
# B-4 â€” roughTokenCountEstimationForBlock (R4 #44)
# ============================================================

def rough_token_count_for_block(block: Any) -> int:
    """Per-block-type token estimator.

    text/tool_use/tool_result/image â€” each has different size math.
    Images are capped at IMAGE_MAX_TOKEN_SIZE per Anthropic billing.
    """
    if isinstance(block, str):
        return estimate_message_tokens(block)
    if not isinstance(block, dict):
        return 0
    btype = block.get("type")
    if btype == "text":
        return estimate_message_tokens(block.get("text", ""))
    if btype == "tool_use":
        # Tool name + input as JSON (dense, 2 bytes/token).
        name_tokens = estimate_message_tokens(block.get("name", ""))
        import json as _json
        input_tokens = int(len(_json.dumps(block.get("input", {}))) / 2.0 + 0.5)
        return name_tokens + input_tokens
    if btype == "tool_result":
        content = block.get("content", "")
        if isinstance(content, list):
            return sum(rough_token_count_for_block(c) for c in content)
        return estimate_message_tokens(str(content))
    if btype in {"image", "input_image"}:
        return IMAGE_MAX_TOKEN_SIZE
    if btype in {"thinking", "redacted_thinking"}:
        return estimate_message_tokens(block.get("thinking", "") or block.get("data", ""))
    return 0


def rough_token_count_for_message(msg: Dict[str, Any]) -> int:
    """Sum of `rough_token_count_for_block` for each block in a message."""
    if not isinstance(msg, dict):
        return 0
    content = msg.get("content")
    if isinstance(content, str):
        return estimate_message_tokens(content)
    if isinstance(content, list):
        return sum(rough_token_count_for_block(b) for b in content)
    return 0


# ============================================================
# TokenTracker â€” verbatim port of v4 + per-agent attribution
# ============================================================

# Sentinel for distinguishing "not yet recorded" from "recorded as 0".
_NO_USAGE_RECORD: Optional[Dict[str, int]] = None


class TokenTracker:
    """Thread-safe tracker for API token usage, cost, and cache hits per session.

    v5 extension over v4: per-agent attribution dict so parent and
    sub-agent token costs can be reported separately while still rolling
    up to the same `session_cost` total. Per Plan v3 Â§Block B + B-11.

    The agent_kind argument to `add()` is the attribution bucket key
    (default "parent"; sub-agents pass "build", "explore", "verify",
    etc. â€” the type-string from `subagent.spawn`).
    """

    def __init__(self, config=None):
        # `config` is injected so tests can build a TokenTracker without
        # importing the runtime CONFIG singleton at module-import time.
        # When None, we resolve CONFIG dynamically on every read so a
        # test that `importlib.reload(runtime.config)` doesn't strand the
        # tracker on a stale instance.
        self._config_override = config
        self._fixed_overhead: Optional[int] = None
        self._lock = threading.Lock()
        self.reset()

    @property
    def _config(self):
        """Resolve CONFIG lazily so reloads in tests don't strand us."""
        if self._config_override is not None:
            return self._config_override
        from runtime.config import CONFIG as _CFG  # noqa: F401 â€” late import
        return _CFG

    # --------------------------------------------------------
    # Reset / state
    # --------------------------------------------------------

    def reset(self):
        """Reset all counters."""
        with self._lock:
            self._reset_unlocked()

    def _reset_unlocked(self):
        self.session_input = 0
        self.session_output = 0
        self.session_total = 0
        self.session_cache_read = 0
        self.session_cache_write = 0
        self.last_input = 0
        self.last_output = 0
        self.api_calls = 0
        self.session_cost = 0.0
        self.last_cost = 0.0
        self._model_id = self._config.model_id
        self._budget_warned = False
        self._budget_stopped = False
        # Per-agent attribution (Plan v3 Â§Block B). Parent always tracked
        # by default; sub-agents accumulate under their type-string key.
        self.parent_input_tokens = 0
        self.parent_output_tokens = 0
        self.parent_cost = 0.0
        self.subagent_input_tokens: Dict[str, int] = {}
        self.subagent_output_tokens: Dict[str, int] = {}
        self.subagent_cost: Dict[str, float] = {}
        # Last-usage record for tokenCountWithEstimation walks (B-8).
        self._last_usage_record: Optional[Dict[str, int]] = None

    # --------------------------------------------------------
    # Add usage (the singleton write path)
    # --------------------------------------------------------

    def add(
        self,
        usage: Dict[str, int],
        model_id: Optional[str] = None,
        agent_kind: str = "parent",
    ):
        """Add usage from API response (thread-safe).

        agent_kind: attribution bucket. "parent" (default) for the main
        agent loop; sub-agent type-strings ("build", "explore", "verify",
        "plan", "review", "general") for spawned children. The session
        rollup totals always include both.
        """
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        cache_read = int(usage.get("cache_read_input_tokens", 0) or 0)
        cache_write = int(usage.get("cache_creation_input_tokens", 0) or 0)

        with self._lock:
            self.last_input = input_tokens
            self.last_output = output_tokens
            self.session_input += input_tokens
            self.session_output += output_tokens
            self.session_total = self.session_input + self.session_output
            self.session_cache_read += cache_read
            self.session_cache_write += cache_write
            self.api_calls += 1
            # B-8 â€” record last usage so estimators can walk back.
            self._last_usage_record = dict(usage)

            mid = canonicalize_model_id(model_id or self._config.model_id)
            if model_id:
                self._model_id = model_id
            pricing = MODEL_COSTS.get(mid)
            cost = 0.0
            if pricing:
                base_input = pricing["input"]
                regular_input = max(0, input_tokens - cache_read - cache_write)
                cost = (
                    (regular_input / 1000) * base_input
                    + (cache_read / 1000) * base_input * 0.1
                    + (cache_write / 1000) * base_input * 1.25
                    + (output_tokens / 1000) * pricing["output"]
                )
                self.session_cost += cost
                self.last_cost = cost
            else:
                if not hasattr(self, "_warned_models"):
                    self._warned_models = set()
                if mid not in self._warned_models:
                    self._warned_models.add(mid)
                    logging.warning(
                        f"TokenTracker: no pricing for model '{mid}' â€” cost will show as $0. "
                        f"Add to MODEL_COSTS dict in runtime/tokens.py."
                    )
                self.last_cost = 0.0

            # Per-agent attribution (additive â€” same singleton, separate buckets).
            if agent_kind == "parent":
                self.parent_input_tokens += input_tokens
                self.parent_output_tokens += output_tokens
                self.parent_cost += cost
            else:
                self.subagent_input_tokens[agent_kind] = (
                    self.subagent_input_tokens.get(agent_kind, 0) + input_tokens
                )
                self.subagent_output_tokens[agent_kind] = (
                    self.subagent_output_tokens.get(agent_kind, 0) + output_tokens
                )
                self.subagent_cost[agent_kind] = (
                    self.subagent_cost.get(agent_kind, 0.0) + cost
                )

            # Budget gate (verbatim from v4).
            limit = self._config.session_cost_limit
            if limit > 0 and self.session_cost > 0:
                pct = self.session_cost / limit
                if pct >= 1.0 and not self._budget_stopped:
                    self._budget_stopped = True
                    logging.warning(
                        f"Session cost ${self.session_cost:.4f} reached limit ${limit:.2f}."
                    )
                elif pct >= 0.8 and not self._budget_warned:
                    self._budget_warned = True
                    logging.warning(
                        f"Session cost ${self.session_cost:.4f} is {pct:.0%} of ${limit:.2f} limit."
                    )

    # --------------------------------------------------------
    # Read-only views (v4 verbatim)
    # --------------------------------------------------------

    def is_over_budget(self) -> bool:
        limit = self._config.session_cost_limit
        return limit > 0 and self.session_cost >= limit

    def get_last(self) -> str:
        return f"In:{self.last_input:,} Out:{self.last_output:,}"

    def get_session(self) -> str:
        return (
            f"In:{self.session_input:,} Out:{self.session_output:,} "
            f"Total:{self.session_total:,}"
        )

    def get_cache_savings_usd(self) -> float:
        mid = canonicalize_model_id(self._model_id or self._config.model_id)
        pricing = MODEL_COSTS.get(mid)
        if not pricing or self.session_cache_read == 0:
            return 0.0
        full_price_per_1k = pricing["input"]
        return (self.session_cache_read / 1000) * full_price_per_1k * 0.90

    def get_cost(self) -> str:
        cost_str = (
            f"${self.session_cost:.4f}"
            if self.session_cost < 0.01
            else f"${self.session_cost:.2f}"
        )
        if self.session_cache_read > 0 and self.session_input > 0:
            cache_pct = min(100, (self.session_cache_read / self.session_input) * 100)
            savings = self.get_cache_savings_usd()
            cost_str += f" (cache {cache_pct:.0f}% | saved ~${savings:.4f})"
        return cost_str

    def get_stats(self) -> Dict[str, Any]:
        return {
            "session_input": self.session_input,
            "session_output": self.session_output,
            "session_total": self.session_total,
            "session_cache_read": self.session_cache_read,
            "session_cache_write": self.session_cache_write,
            "last_input": self.last_input,
            "last_output": self.last_output,
            "api_calls": self.api_calls,
            "session_cost_usd": round(self.session_cost, 6),
            "last_cost_usd": round(self.last_cost, 6),
            "parent_input_tokens": self.parent_input_tokens,
            "parent_output_tokens": self.parent_output_tokens,
            "parent_cost_usd": round(self.parent_cost, 6),
            "subagent_input_tokens": dict(self.subagent_input_tokens),
            "subagent_output_tokens": dict(self.subagent_output_tokens),
            "subagent_cost_usd": {k: round(v, 6) for k, v in self.subagent_cost.items()},
        }

    def restore(self, stats: Dict[str, Any]):
        """Restore counters from saved session metadata.

        Used by Block B+ SessionManager `/resume` to rehydrate cost
        across sessions (Runnable cost-tracker.ts:87-175 / R11 N8).
        """
        with self._lock:
            self.session_input = int(stats.get("session_input", 0))
            self.session_output = int(stats.get("session_output", 0))
            self.session_total = self.session_input + self.session_output
            self.session_cache_read = int(stats.get("session_cache_read", 0))
            self.session_cache_write = int(stats.get("session_cache_write", 0))
            self.last_input = int(stats.get("last_input", 0))
            self.last_output = int(stats.get("last_output", 0))
            self.api_calls = int(stats.get("api_calls", 0))
            self.session_cost = float(stats.get("session_cost_usd", 0.0))
            self.last_cost = float(stats.get("last_cost_usd", 0.0))
            self.parent_input_tokens = int(stats.get("parent_input_tokens", 0))
            self.parent_output_tokens = int(stats.get("parent_output_tokens", 0))
            self.parent_cost = float(stats.get("parent_cost_usd", 0.0))
            self.subagent_input_tokens = dict(stats.get("subagent_input_tokens", {}))
            self.subagent_output_tokens = dict(stats.get("subagent_output_tokens", {}))
            self.subagent_cost = {
                k: float(v) for k, v in stats.get("subagent_cost_usd", {}).items()
            }

    # --------------------------------------------------------
    # B-8 / B-9 â€” context-token math derived from last response
    # --------------------------------------------------------

    def final_context_tokens_from_last_response(self) -> int:
        """Best-available estimate of the current context window size.

        Per R8 #16: Bedrock returns top-level `usage` only (no per-block
        `cache_creation_input_tokens` breakdown). We use:
          context = last_input + cache_read + cache_write
        as a conservative upper bound for the next turn's prompt.
        """
        rec = self._last_usage_record
        if not rec:
            return self.session_input  # cold start fallback
        return (
            int(rec.get("input_tokens", 0))
            + int(rec.get("cache_read_input_tokens", 0))
            + int(rec.get("cache_creation_input_tokens", 0))
        )

    def token_count_with_estimation(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate token count for a message list.

        Per R8 #15. Walks back to the last usage record; if it covers
        the same prefix-length as `messages`, reuse the recorded value
        (correct under prompt caching). Otherwise fall back to the
        block-level rough estimator.
        """
        if not messages:
            return 0
        if self._last_usage_record is not None:
            recorded = self._last_usage_record.get("input_tokens", 0)
            if recorded > 0:
                return int(recorded)
        return sum(rough_token_count_for_message(m) for m in messages)


# Module-level singleton (parity with v4 `TOKENS = TokenTracker()`).
TOKENS = TokenTracker()


# Block B+ (PORT_LOG #054): atexit cost-flush via cleanup_registry.
# Per Runnable costHook.ts:6-22 (R11 N14). On normal exit / SIGINT /
# SIGTERM, log the final session cost so operators can audit
# post-hoc even if the user closes the notebook abruptly.
def _flush_cost_on_exit() -> None:
    if TOKENS.session_cost > 0:
        logging.warning(
            f"session-final cost: {TOKENS.get_cost()} "
            f"({TOKENS.api_calls} API calls, "
            f"in={TOKENS.session_input:,} out={TOKENS.session_output:,})"
        )


try:  # pragma: no cover â€” registration-time best-effort
    from runtime.cleanup_registry import register as _register_cleanup
    _register_cleanup(_flush_cost_on_exit)
except Exception:
    pass


__all__ = [
    "ToolResult",
    "MODEL_COSTS",
    "EXCLUDED_MODELS_FOR_CACHE_BREAK",
    "IMAGE_MAX_TOKEN_SIZE",
    "TokenTracker",
    "TOKENS",
    "bytes_per_token_for_file_type",
    "estimate_message_tokens",
    "has_thinking_blocks",
    "rough_token_count_for_block",
    "rough_token_count_for_message",
    "canonicalize_model_id",
]

2026-05-03T03:51:45.093751Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 18.9 seconds
Output:
Program 'python.exe' failed to run: The file cannot be accessed by the systemAt line:2 char:1
+ python -m pytest -q "compact_v5/MAIN/agent/tests/integration/test_blo ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.
At line:2 char:1
+ python -m pytest -q "compact_v5/MAIN/agent/tests/integration/test_blo ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ResourceUnavailable: (:) [], ApplicationFailedException
    + FullyQualifiedErrorId : NativeCommandFailed
 

 exited 1 in 18867ms:
Program 'python.exe' failed to run: The file cannot be accessed by the systemAt line:2 char:1
+ python -m pytest -q "compact_v5/MAIN/agent/tests/integration/test_blo ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.
At line:2 char:1
+ python -m pytest -q "compact_v5/MAIN/agent/tests/integration/test_blo ...
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ResourceUnavailable: (:) [], ApplicationFailedException
    + FullyQualifiedErrorId : NativeCommandFailed
 

codex
I confirmed cross-region stripping is centralized in `runtime.tokens.canonicalize_model_id` and matches `au/apac/us/eu`. I’ll pull exact line references now and retry test execution with an alternate interpreter entrypoint (`py`) since `python` was not runnable in this environment.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=0; Get-Content "compact_v5/MAIN/agent/prompt/env_block.py" | ForEach-Object { $i++; "{0,4}: {1}" -f $i, $_ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=0; Get-Content "compact_v5/MAIN/agent/tests/integration/test_block_e_f.py" | ForEach-Object { $i++; "{0,4}: {1}" -f $i, $_ }' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Command python, py | Format-Table -AutoSize' in D:\Github\sagemaker-coding-agent
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'py -3 -m pytest -q "compact_v5/MAIN/agent/tests/integration/test_block_e_f.py"' in D:\Github\sagemaker-coding-agent
2026-05-03T03:51:56.158382Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.6 seconds
Output:
py : The term 'py' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the 
spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:1
+ py -3 -m pytest -q "compact_v5/MAIN/agent/tests/integration/test_bloc ...
+ ~~
    + CategoryInfo          : ObjectNotFound: (py:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

 exited 1 in 557ms:
py : The term 'py' is not recognized as the name of a cmdlet, function, script file, or operable program. Check the 
spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:1
+ py -3 -m pytest -q "compact_v5/MAIN/agent/tests/integration/test_bloc ...
+ ~~
    + CategoryInfo          : ObjectNotFound: (py:String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
 

 succeeded in 582ms:
   1: """Block E+F â€” env_block + ADR-020 0-2/0-4/0-6 remap closure.
   2: 
   3: Phase 6 (sectioned prompt) + Phase 11 (notebook UX) shipped most of
   4: the v4-vs-Runnable Block E+F surface. This test file covers the
   5: remaining ADR-020 remap rows that landed in Block E+F per ADR-020 Â§
   6: Notes / known scope remaps:
   7: 
   8:   0-2 â€” getSessionStartDate / getLocalMonthYear (cache-stable date)
   9:   0-4 â€” env block format (Windows-shell hint, OS, Notes appendix)
  10:   0-6 â€” getKnowledgeCutoff (model-specific cutoff)
  11: """
  12: from __future__ import annotations
  13: 
  14: import os
  15: import sys
  16: 
  17: import pytest
  18: 
  19: _AGENT_ROOT = os.path.dirname(
  20:     os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  21: )
  22: if _AGENT_ROOT not in sys.path:
  23:     sys.path.insert(0, _AGENT_ROOT)
  24: 
  25: 
  26: # ============================================================
  27: # ADR-020 0-2 â€” date helpers (cache-stable)
  28: # ============================================================
  29: 
  30: def test_session_start_date_memoized():
  31:     """First call caches the date string; subsequent calls return it."""
  32:     from prompt.env_block import get_session_start_date, _reset_caches_for_tests
  33: 
  34:     _reset_caches_for_tests()
  35:     d1 = get_session_start_date()
  36:     d2 = get_session_start_date()
  37:     assert d1 == d2
  38:     # Format: YYYY-MM
  39:     assert len(d1) == 7
  40:     assert d1[4] == "-"
  41: 
  42: 
  43: def test_local_month_year_human_readable():
  44:     from prompt.env_block import get_local_month_year
  45: 
  46:     s = get_local_month_year()
  47:     # E.g. "May 2026" â€” should contain a space + 4-digit year.
  48:     parts = s.split()
  49:     assert len(parts) == 2
  50:     assert parts[1].isdigit() and len(parts[1]) == 4
  51: 
  52: 
  53: def test_env_block_uses_month_year_not_iso_date():
  54:     """ADR-020 0-2 lock: env_block contains month-year (cache-stable)
  55:     NOT a full ISO date (cache-busts daily)."""
  56:     from prompt.env_block import render_env_block
  57: 
  58:     body = render_env_block(workspace="/tmp", model_id="x")
  59:     # Should NOT contain a YYYY-MM-DD pattern.
  60:     import re
  61:     iso_dates = re.findall(r"\d{4}-\d{2}-\d{2}", body)
  62:     assert not iso_dates, (
  63:         f"env_block must NOT contain ISO dates (cache-bust risk); "
  64:         f"found: {iso_dates}"
  65:     )
  66:     # Should contain month-year form.
  67:     months = ["January", "February", "March", "April", "May", "June",
  68:               "July", "August", "September", "October", "November", "December"]
  69:     assert any(m in body for m in months), (
  70:         "env_block should contain a month-year string"
  71:     )
  72: 
  73: 
  74: # ============================================================
  75: # ADR-020 0-6 â€” knowledge cutoff
  76: # ============================================================
  77: 
  78: def test_knowledge_cutoff_haiku_4_5():
  79:     from prompt.env_block import get_knowledge_cutoff
  80:     assert get_knowledge_cutoff("anthropic.claude-haiku-4-5-20251001-v1:0") == "October 2025"
  81: 
  82: 
  83: def test_knowledge_cutoff_sonnet_4_5():
  84:     from prompt.env_block import get_knowledge_cutoff
  85:     assert get_knowledge_cutoff("anthropic.claude-sonnet-4-5-20250929-v1:0") == "September 2025"
  86: 
  87: 
  88: def test_knowledge_cutoff_strips_au_prefix():
  89:     """ADR-020 0-6 lock: cross-region inference prefixes (au./apac./us./eu.)
  90:     must be stripped before cutoff lookup."""
  91:     from prompt.env_block import get_knowledge_cutoff
  92:     assert get_knowledge_cutoff("au.anthropic.claude-haiku-4-5-20251001-v1:0") == "October 2025"
  93:     assert get_knowledge_cutoff("apac.anthropic.claude-sonnet-4-5-20250929-v1:0") == "September 2025"
  94:     assert get_knowledge_cutoff("us.anthropic.claude-3-5-sonnet-20241022-v2:0") == "October 2024"
  95: 
  96: 
  97: def test_knowledge_cutoff_unknown_model_default():
  98:     from prompt.env_block import get_knowledge_cutoff
  99:     cutoff = get_knowledge_cutoff("anthropic.claude-future-99-x")
 100:     assert "early" in cutoff.lower() or "20" in cutoff
 101: 
 102: 
 103: def test_env_block_emits_model_specific_knowledge_cutoff():
 104:     """ADR-020 0-6 lock: render_env_block uses get_knowledge_cutoff."""
 105:     from prompt.env_block import render_env_block
 106: 
 107:     haiku_body = render_env_block(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
 108:     sonnet_body = render_env_block(model_id="anthropic.claude-sonnet-4-5-20250929-v1:0")
 109:     assert "October 2025" in haiku_body
 110:     assert "September 2025" in sonnet_body
 111: 
 112: 
 113: # ============================================================
 114: # ADR-020 0-4 â€” env block format (Windows hint, OS, Notes)
 115: # ============================================================
 116: 
 117: def test_env_block_includes_shell_hint_and_notes():
 118:     """ADR-020 0-4 lock: env_block has OS, shell, and a Notes appendix."""
 119:     from prompt.env_block import render_env_block
 120: 
 121:     body = render_env_block(workspace="/tmp", model_id="x")
 122:     # OS line
 123:     assert "## Environment" in body
 124:     assert "OS:" in body
 125:     assert "Shell:" in body
 126:     assert "Working directory" in body
 127:     # Notes appendix
 128:     assert "## Notes" in body
 129: 
 130: 
 131: def test_env_block_windows_shell_hint(monkeypatch):
 132:     """On Windows, shell hint must mention PowerShell syntax."""
 133:     from prompt import env_block as eb_mod
 134: 
 135:     if sys.platform == "win32" or os.name == "nt":
 136:         # Native Windows â€” verify the hint actually mentions PowerShell.
 137:         hint = eb_mod.get_shell_hint()
 138:         assert "PowerShell" in hint or "powershell" in hint.lower()
 139: 
 140: 
 141: def test_env_block_no_streaming_note():
 142:     """Constraint #10 enforcement â€” env_block reminds the model
 143:     streaming is unsupported."""
 144:     from prompt.env_block import render_env_block
 145: 
 146:     body = render_env_block(workspace="/tmp", model_id="x")
 147:     assert "treaming" in body.lower()  # "Streaming is NOT supported"
 148:     assert ("not supported" in body.lower()
 149:             or "no streaming" in body.lower()
 150:             or "NOT supported" in body)
 151: 
 152: 
 153: # ============================================================
 154: # render_env_block defaults
 155: # ============================================================
 156: 
 157: def test_render_env_block_uses_config_defaults(monkeypatch):
 158:     from runtime.config import CONFIG
 159:     from prompt.env_block import render_env_block
 160: 
 161:     monkeypatch.setattr(CONFIG, "workspace", "/test/workspace")
 162:     monkeypatch.setattr(CONFIG, "model_id", "anthropic.claude-haiku-4-5-20251001-v1:0")
 163: 
 164:     body = render_env_block()
 165:     assert "/test/workspace" in body
 166:     assert "claude-haiku-4-5" in body
 167:     assert "October 2025" in body

 succeeded in 611ms:
   1: """Block E+F (ADR-020 0-2/0-4/0-6 remaps) â€” env-block formatter.
   2: 
   3: Ports Runnable's env-detail builders so the system prompt's `env_block`
   4: section gets cache-stable date strings + accurate knowledge-cutoff for
   5: the current model + Windows-shell hint when applicable.
   6: 
   7: Closes ADR-020 Â§Notes / known scope remaps rows:
   8:   0-2 â€” getSessionStartDate / getLocalMonthYear (R8 #67) â€” cache-stable
   9:   0-4 â€” env block format (R8 #76, #79) â€” Windows-shell hint, OS, Notes
  10:   0-6 â€” getKnowledgeCutoff (R8 #39) â€” model-specific cutoff per Sonnet
  11:         4.6 / Haiku 4.5
  12: 
  13: Why "month-year not ISO": tool prompts that mention "today's date as
  14: 2026-05-03" cause the prompt-cache to bust at midnight. Month-year
  15: ("May 2026") changes monthly, not daily, so the cache survives full days.
  16: 
  17: PORT_LOG: see #071.
  18: """
  19: from __future__ import annotations
  20: 
  21: import os
  22: import platform
  23: import sys
  24: from datetime import datetime
  25: from functools import lru_cache
  26: from typing import Optional
  27: 
  28: 
  29: # ============================================================
  30: # Date helpers (ADR-020 0-2 remap)
  31: # ============================================================
  32: 
  33: @lru_cache(maxsize=1)
  34: def get_session_start_date() -> str:
  35:     """Memoized session-start date in `YYYY-MM` form (cache-stable).
  36: 
  37:     Cached at first call so successive calls within the session return
  38:     the same value even if the wall clock crosses midnight. Prevents
  39:     midnight-boundary cache busts.
  40:     """
  41:     return datetime.now().strftime("%Y-%m")
  42: 
  43: 
  44: def get_local_month_year() -> str:
  45:     """Render the current month-year in human-readable form.
  46: 
  47:     Cache-stable across same-month days (changes monthly, not daily).
  48:     Used in env-block instead of full ISO date so prompt-cache lasts
  49:     longer than 24 hours.
  50:     """
  51:     now = datetime.now()
  52:     return now.strftime("%B %Y")
  53: 
  54: 
  55: # ============================================================
  56: # Knowledge cutoff (ADR-020 0-6 remap)
  57: # ============================================================
  58: 
  59: # Model-specific knowledge cutoffs as of 2026 model lineup. Per Runnable
  60: # constants/prompts.ts:712-730 (R8 #39).
  61: _KNOWLEDGE_CUTOFFS: dict = {
  62:     # Haiku 4.5 (Bedrock + Anthropic-direct)
  63:     "anthropic.claude-haiku-4-5-20251001-v1:0": "October 2025",
  64:     "claude-haiku-4-5-20251001": "October 2025",
  65:     # Sonnet 4.5
  66:     "anthropic.claude-sonnet-4-5-20250929-v1:0": "September 2025",
  67:     # Sonnet 4.6 (newest)
  68:     "anthropic.claude-sonnet-4-6-20260101-v1:0": "January 2026",
  69:     # Sonnet 3.5 baseline
  70:     "anthropic.claude-3-5-sonnet-20241022-v2:0": "October 2024",
  71: }
  72: 
  73: _KNOWLEDGE_CUTOFF_DEFAULT = "early 2025"
  74: 
  75: 
  76: def get_knowledge_cutoff(model_id: str) -> str:
  77:     """Return the human-readable knowledge cutoff for `model_id`.
  78: 
  79:     Strips Bedrock cross-region prefixes (au./apac./us./eu.) before
  80:     lookup so au.anthropic.claude-haiku-4-5-... matches the canonical
  81:     haiku entry. Falls back to a generic "early 2025" for unknown models.
  82:     """
  83:     if not model_id:
  84:         return _KNOWLEDGE_CUTOFF_DEFAULT
  85:     try:
  86:         from runtime.tokens import canonicalize_model_id
  87:         canonical = canonicalize_model_id(model_id)
  88:     except Exception:
  89:         canonical = model_id
  90:     return _KNOWLEDGE_CUTOFFS.get(canonical, _KNOWLEDGE_CUTOFF_DEFAULT)
  91: 
  92: 
  93: # ============================================================
  94: # OS / shell hint (ADR-020 0-4 remap)
  95: # ============================================================
  96: 
  97: def get_os_string() -> str:
  98:     """Human-readable OS + version + machine."""
  99:     sys_name = platform.system()
 100:     release = platform.release()
 101:     machine = platform.machine()
 102:     return f"{sys_name} {release} ({machine})"
 103: 
 104: 
 105: def get_shell_hint() -> str:
 106:     """Best-guess shell name for the platform.
 107: 
 108:     On Windows, defaults to PowerShell â€” bash via WSL is also common
 109:     but the agent surface assumes the platform-default shell unless
 110:     the user passes a different `shell` arg to the bash tool.
 111:     """
 112:     if sys.platform == "win32" or os.name == "nt":
 113:         return "PowerShell (use PowerShell syntax â€” e.g., $null not /dev/null)"
 114:     return f"{os.environ.get('SHELL', 'bash')}"
 115: 
 116: 
 117: # ============================================================
 118: # Render the full env block
 119: # ============================================================
 120: 
 121: def render_env_block(
 122:     *,
 123:     workspace: Optional[str] = None,
 124:     model_id: Optional[str] = None,
 125: ) -> str:
 126:     """Render the env-block markdown body.
 127: 
 128:     Pulls workspace from CONFIG when not passed, model_id from CONFIG
 129:     when not passed. Output is the body that `prompt/sections.py`
 130:     splices into the dynamic tail of the system prompt.
 131: 
 132:     Notes appendix is included when relevant (Windows-shell warning;
 133:     no-streaming reminder per constraint #10).
 134:     """
 135:     from runtime.config import CONFIG
 136:     workspace = workspace or CONFIG.workspace
 137:     model_id = model_id or CONFIG.model_id
 138: 
 139:     parts = [
 140:         "## Environment",
 141:         "",
 142:         f"- Working directory: `{workspace}`",
 143:         f"- OS: {get_os_string()}",
 144:         f"- Shell: {get_shell_hint()}",
 145:         f"- Session start: {get_local_month_year()}",
 146:         f"- Model: `{model_id}`",
 147:         f"- Knowledge cutoff: {get_knowledge_cutoff(model_id)}",
 148:         "",
 149:         "## Notes",
 150:         "",
 151:     ]
 152:     notes: list = []
 153:     if sys.platform == "win32" or os.name == "nt":
 154:         notes.append(
 155:             "- Bash tool runs PowerShell on Windows by default. "
 156:             "Use PowerShell syntax (`$env:VAR`, not `$VAR`)."
 157:         )
 158:     notes.append("- Streaming is NOT supported on this Bedrock SageMaker deployment.")
 159:     notes.append(
 160:         "- Today's month-year shown above is cache-stable; do NOT assume "
 161:         "full ISO date is current â€” query bash `date` if you need precision."
 162:     )
 163:     parts.extend(notes)
 164:     return "\n".join(parts)
 165: 
 166: 
 167: def _reset_caches_for_tests() -> None:
 168:     """Clear lru_cache for date helpers so tests can re-evaluate."""
 169:     get_session_start_date.cache_clear()
 170: 
 171: 
 172: __all__ = [
 173:     "get_session_start_date",
 174:     "get_local_month_year",
 175:     "get_knowledge_cutoff",
 176:     "get_os_string",
 177:     "get_shell_hint",
 178:     "render_env_block",
 179: ]

2026-05-03T03:51:56.310246Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 0.7 seconds
Output:

CommandType Name       Version Source                                                       
----------- ----       ------- ------                                                       
Application python.exe 0.0.0.0 C:\Users\winst\AppData\Local\Microsoft\WindowsApps\python.exe


Get-Command : The term 'py' is not recognized as the name of a cmdlet, function, script file, or operable program. 
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:1
+ Get-Command python, py | Format-Table -AutoSize
+ ~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (py:String) [Get-Command], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException,Microsoft.PowerShell.Commands.GetCommandCommand
 

 exited 1 in 710ms:

CommandType Name       Version Source                                                       
----------- ----       ------- ------                                                       
Application python.exe 0.0.0.0 C:\Users\winst\AppData\Local\Microsoft\WindowsApps\python.exe


Get-Command : The term 'py' is not recognized as the name of a cmdlet, function, script file, or operable program. 
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:2 char:1
+ Get-Command python, py | Format-Table -AutoSize
+ ~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (py:String) [Get-Command], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException,Microsoft.PowerShell.Commands.GetCommandCommand
 

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "get_session_start_date|get_local_month_year|get_knowledge_cutoff|render_env_block" compact_v5/MAIN/agent' in D:\Github\sagemaker-coding-agent
 succeeded in 799ms:
compact_v5/MAIN/agent\prompt\env_block.py:34:def get_session_start_date() -> str:
compact_v5/MAIN/agent\prompt\env_block.py:44:def get_local_month_year() -> str:
compact_v5/MAIN/agent\prompt\env_block.py:76:def get_knowledge_cutoff(model_id: str) -> str:
compact_v5/MAIN/agent\prompt\env_block.py:121:def render_env_block(
compact_v5/MAIN/agent\prompt\env_block.py:145:        f"- Session start: {get_local_month_year()}",
compact_v5/MAIN/agent\prompt\env_block.py:147:        f"- Knowledge cutoff: {get_knowledge_cutoff(model_id)}",
compact_v5/MAIN/agent\prompt\env_block.py:169:    get_session_start_date.cache_clear()
compact_v5/MAIN/agent\prompt\env_block.py:173:    "get_session_start_date",
compact_v5/MAIN/agent\prompt\env_block.py:174:    "get_local_month_year",
compact_v5/MAIN/agent\prompt\env_block.py:175:    "get_knowledge_cutoff",
compact_v5/MAIN/agent\prompt\env_block.py:178:    "render_env_block",
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:32:    from prompt.env_block import get_session_start_date, _reset_caches_for_tests
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:35:    d1 = get_session_start_date()
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:36:    d2 = get_session_start_date()
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:44:    from prompt.env_block import get_local_month_year
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:46:    s = get_local_month_year()
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:56:    from prompt.env_block import render_env_block
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:58:    body = render_env_block(workspace="/tmp", model_id="x")
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:79:    from prompt.env_block import get_knowledge_cutoff
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:80:    assert get_knowledge_cutoff("anthropic.claude-haiku-4-5-20251001-v1:0") == "October 2025"
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:84:    from prompt.env_block import get_knowledge_cutoff
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:85:    assert get_knowledge_cutoff("anthropic.claude-sonnet-4-5-20250929-v1:0") == "September 2025"
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:91:    from prompt.env_block import get_knowledge_cutoff
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:92:    assert get_knowledge_cutoff("au.anthropic.claude-haiku-4-5-20251001-v1:0") == "October 2025"
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:93:    assert get_knowledge_cutoff("apac.anthropic.claude-sonnet-4-5-20250929-v1:0") == "September 2025"
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:94:    assert get_knowledge_cutoff("us.anthropic.claude-3-5-sonnet-20241022-v2:0") == "October 2024"
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:98:    from prompt.env_block import get_knowledge_cutoff
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:99:    cutoff = get_knowledge_cutoff("anthropic.claude-future-99-x")
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:104:    """ADR-020 0-6 lock: render_env_block uses get_knowledge_cutoff."""
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:105:    from prompt.env_block import render_env_block
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:107:    haiku_body = render_env_block(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:108:    sonnet_body = render_env_block(model_id="anthropic.claude-sonnet-4-5-20250929-v1:0")
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:119:    from prompt.env_block import render_env_block
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:121:    body = render_env_block(workspace="/tmp", model_id="x")
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:144:    from prompt.env_block import render_env_block
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:146:    body = render_env_block(workspace="/tmp", model_id="x")
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:154:# render_env_block defaults
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:157:def test_render_env_block_uses_config_defaults(monkeypatch):
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:159:    from prompt.env_block import render_env_block
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:164:    body = render_env_block()

web search: 
web search: 
codex
I found one substantive mismatch in the implementation (session-start cache helper isn’t actually used in the rendered env block). I’m validating whether that should be treated as drift vs. bug, then I’ll give you axis verdicts and final recommendation.
exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Command uv | Format-Table -AutoSize' in D:\Github\sagemaker-coding-agent
 succeeded in 1297ms:

CommandType Name   Version Source                          
----------- ----   ------- ------                          
Application uv.exe 0.0.0.0 C:\Users\winst\.local\bin\uv.exe



exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'uv run pytest -q "compact_v5/MAIN/agent/tests/integration/test_block_e_f.py"' in D:\Github\sagemaker-coding-agent
2026-05-03T03:52:29.086658Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 1.1 seconds
Output:
error: Failed to initialize cache at `C:\Users\winst\AppData\Local\uv\cache`
  Caused by: failed to open file `C:\Users\winst\AppData\Local\uv\cache\sdists-v9\.git`: Access is denied. (os error 5)

 exited 1 in 1125ms:
error: Failed to initialize cache at `C:\Users\winst\AppData\Local\uv\cache`
  Caused by: failed to open file `C:\Users\winst\AppData\Local\uv\cache\sdists-v9\.git`: Access is denied. (os error 5)

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$env:UV_CACHE_DIR='"'D:\\Github\\sagemaker-coding-agent\\.uv-cache'; uv run pytest -q \"compact_v5/MAIN/agent/tests/integration/test_block_e_f.py\"" in D:\Github\sagemaker-coding-agent
2026-05-03T03:53:07.818292Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 31 seconds
Output:
error: failed to create directory `C:\Users\winst\AppData\Roaming\uv\python`: Access is denied. (os error 5)

 exited 1 in 30983ms:
error: failed to create directory `C:\Users\winst\AppData\Roaming\uv\python`: Access is denied. (os error 5)

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$env:UV_CACHE_DIR='"'D:\\Github\\sagemaker-coding-agent\\.uv-cache'; "'$env:UV_PYTHON_INSTALL_DIR='"'D:\\Github\\sagemaker-coding-agent\\.uv-python'; uv run pytest -q \"compact_v5/MAIN/agent/tests/integration/test_block_e_f.py\"" in D:\Github\sagemaker-coding-agent
2026-05-03T03:53:48.972129Z ERROR codex_core::tools::router: error=Exit code: 1
Wall time: 36.8 seconds
Output:
error: Request failed after 3 retries in 5.8s
  Caused by: Failed to download https://github.com/astral-sh/python-build-standalone/releases/download/20260325/cpython-3.14.3%2B20260325-x86_64-pc-windows-msvc-install_only_stripped.tar.gz
  Caused by: error sending request for url (https://github.com/astral-sh/python-build-standalone/releases/download/20260325/cpython-3.14.3%2B20260325-x86_64-pc-windows-msvc-install_only_stripped.tar.gz)
  Caused by: client error (Connect)
  Caused by: tcp connect error
  Caused by: An attempt was made to access a socket in a way forbidden by its access permissions. (os error 10013)

 exited 1 in 36826ms:
error: Request failed after 3 retries in 5.8s
  Caused by: Failed to download https://github.com/astral-sh/python-build-standalone/releases/download/20260325/cpython-3.14.3%2B20260325-x86_64-pc-windows-msvc-install_only_stripped.tar.gz
  Caused by: error sending request for url (https://github.com/astral-sh/python-build-standalone/releases/download/20260325/cpython-3.14.3%2B20260325-x86_64-pc-windows-msvc-install_only_stripped.tar.gz)
  Caused by: client error (Connect)
  Caused by: tcp connect error
  Caused by: An attempt was made to access a socket in a way forbidden by its access permissions. (os error 10013)

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command '$i=0; Get-Content "compact_v5/MAIN/agent/runtime/tokens.py" | ForEach-Object { $i++; if($i -ge 76 -and $i -le 110){ "{0,4}: {1}" -f $i, $_ }}' in D:\Github\sagemaker-coding-agent
 succeeded in 445ms:
  76:     `apac.anthropic.claude-haiku-4-5-...` and
  77:     `anthropic.claude-haiku-4-5-...` to the same canonical key for
  78:     pricing lookup. Bedrock inference-profile prefixes covered:
  79:         au.   â€” Australia (Sydney; ap-southeast-2 default)
  80:         apac. â€” Asia-Pacific
  81:         us.   â€” United States (legacy us-east-1 / us-west-2)
  82:         eu.   â€” Europe (legacy eu-west-1 / eu-central-1)
  83: 
  84:     Codex Block-B finding #1 (HIGH) lock: `au.` was missing originally,
  85:     causing CONFIG.model_id="au.anthropic.claude-sonnet-4-5-..." to
  86:     miss MODEL_COSTS entirely and TOKENS to record $0.
  87:     """
  88:     if not model_id:
  89:         return model_id
  90:     for prefix in ("au.", "apac.", "us.", "eu."):
  91:         if model_id.startswith(prefix):
  92:             return model_id[len(prefix):]
  93:     return model_id
  94: 
  95: 
  96: # ============================================================
  97: # R4 #14 â€” EXCLUDED_MODELS_FOR_CACHE_BREAK (MUST)
  98: # ============================================================
  99: #
 100: # Haiku-4.5 cache hashing in Bedrock is non-deterministic in a way that
 101: # the prompt-cache-break detector misreads as a "section flipped". Add
 102: # Haiku to the exclusion set so cache-break warnings don't fire on Haiku
 103: # sessions. This is a MUST per Wave-5-DEEP R4 #14.
 104: 
 105: EXCLUDED_MODELS_FOR_CACHE_BREAK: set = {
 106:     "anthropic.claude-haiku-4-5-20251001-v1:0",
 107: }
 108: 
 109: 
 110: # ============================================================

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "env_block|render_env_block|Session start" compact_v5/MAIN/agent/prompt' in D:\Github\sagemaker-coding-agent
 succeeded in 424ms:
compact_v5/MAIN/agent/prompt\env_block.py:3:Ports Runnable's env-detail builders so the system prompt's `env_block`
compact_v5/MAIN/agent/prompt\env_block.py:121:def render_env_block(
compact_v5/MAIN/agent/prompt\env_block.py:145:        f"- Session start: {get_local_month_year()}",
compact_v5/MAIN/agent/prompt\env_block.py:178:    "render_env_block",

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command "rg -n \"prompt\\.env_block|from prompt import env_block|render_env_block\\(\" compact_v5/MAIN/agent" in D:\Github\sagemaker-coding-agent
 succeeded in 468ms:
compact_v5/MAIN/agent\prompt\env_block.py:121:def render_env_block(
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:32:    from prompt.env_block import get_session_start_date, _reset_caches_for_tests
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:44:    from prompt.env_block import get_local_month_year
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:56:    from prompt.env_block import render_env_block
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:58:    body = render_env_block(workspace="/tmp", model_id="x")
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:79:    from prompt.env_block import get_knowledge_cutoff
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:84:    from prompt.env_block import get_knowledge_cutoff
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:91:    from prompt.env_block import get_knowledge_cutoff
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:98:    from prompt.env_block import get_knowledge_cutoff
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:105:    from prompt.env_block import render_env_block
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:107:    haiku_body = render_env_block(model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:108:    sonnet_body = render_env_block(model_id="anthropic.claude-sonnet-4-5-20250929-v1:0")
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:119:    from prompt.env_block import render_env_block
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:121:    body = render_env_block(workspace="/tmp", model_id="x")
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:133:    from prompt import env_block as eb_mod
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:144:    from prompt.env_block import render_env_block
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:146:    body = render_env_block(workspace="/tmp", model_id="x")
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:159:    from prompt.env_block import render_env_block
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:164:    body = render_env_block()

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'rg -n "## Environment|Knowledge cutoff|Streaming is NOT supported|Working directory:" compact_v5/MAIN/agent' in D:\Github\sagemaker-coding-agent
 succeeded in 451ms:
compact_v5/MAIN/agent\prompt\env_block.py:56:# Knowledge cutoff (ADR-020 0-6 remap)
compact_v5/MAIN/agent\prompt\env_block.py:140:        "## Environment",
compact_v5/MAIN/agent\prompt\env_block.py:142:        f"- Working directory: `{workspace}`",
compact_v5/MAIN/agent\prompt\env_block.py:147:        f"- Knowledge cutoff: {get_knowledge_cutoff(model_id)}",
compact_v5/MAIN/agent\prompt\env_block.py:158:    notes.append("- Streaming is NOT supported on this Bedrock SageMaker deployment.")
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:123:    assert "## Environment" in body
compact_v5/MAIN/agent\tests\integration\test_block_e_f.py:147:    assert "treaming" in body.lower()  # "Streaming is NOT supported"

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-ChildItem -Path "compact_v5/MAIN/agent/prompt" -File | Select-Object -ExpandProperty Name' in D:\Github\sagemaker-coding-agent
 succeeded in 640ms:
answer_preference.md
commands.md
critique_handling.md
data_validation.md
documents.md
doing_tasks.md
env_block.py
executing_actions.md
identity.md
mcp.md
memory_protocol.md
output_style.md
sections.py
security.md
skill_patching.md
status_doc.md
subagent_coord.md
system.md
tool_classes.md
tool_efficiency.md
verification_contract.md
_CACHE_BOUNDARY.md
__init__.py

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path "compact_v5/MAIN/agent/prompt/sections.py"' in D:\Github\sagemaker-coding-agent
 succeeded in 440ms:
"""V5 prompt section registry â€” one section per .md file, token-budgeted.

Per ADR-002 (file-per-section system prompt) + ADR-012 (Phase 6 final
section list + token caps).

Source pattern: `gg-claude-code-runnable/src/constants/systemPromptSections.ts`.
Adaptation: v5 sections are STATIC `.md` files instead of TS function
returns. The registry stores one entry per section with its name, file
path, and hard token cap. `build_static_prompt()` reads each file at
prompt-build time, validates token caps, and concatenates with explicit
`\\n\\n` separators so cache hashing is byte-stable.

Phase 8 may extend the registry with `cache_break=True` sections (the
Runnable `DANGEROUS_uncachedSystemPromptSection` analogue) for any
future runtime-computed sections. Phase 6 ships only static sections.

The order of sections in `SECTION_ORDER` is significant â€” it locks the
display order in the cached prefix. Reordering would invalidate the
prompt cache for every downstream user. Codex-reviewed; section moves
require a new ADR.

PS Issue #7 fix: `tool_classes.md` is at slot 2 (right after identity).
Under cognitive load the LLM attends to early sections more than the
middle of a flat list â€” promoting the tool-capability matrix prevents
the v4.10.10 "all tools blocked" failure mode.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


# ============================================================
# Section descriptor
# ============================================================

@dataclass(frozen=True)
class Section:
    """One system-prompt section.

    Attributes:
        name:        stable identifier (used as cache key + audit log entry)
        file:        relative path inside `prompt/` (e.g. "identity.md")
        token_cap:   hard maximum estimated tokens for this section's content
        cache_break: if True, recomputing this section invalidates the prompt
                     cache (Runnable parity: DANGEROUS_uncachedSystemPromptSection).
                     Phase 6 ships ALL sections with cache_break=False.
    """
    name: str
    file: str
    token_cap: int
    cache_break: bool = False


# ============================================================
# Section registry â€” per ADR-012 (locked order + caps)
# ============================================================

# Order matters. PS Issue #7 fix: `tool_classes` at slot 2 (right after
# identity, before `system`). Reordering invalidates the prompt cache.
#
# Cap rationale: each cap is set to the current section's actual token
# count plus ~5-10% headroom for minor edits. Caps are MAXIMUMS, not
# targets â€” sections that grow past their cap fail the audit gate.
# Adding new content requires either compressing an existing section
# below its cap OR creating a new section + updating SECTION_ORDER + its
# own cap (which lifts STATIC_TOKEN_BUDGET if needed).
#
# Total budget: the V5_PLAN.md acceptance target was â‰¤2500 tokens. The
# actual Phase-6 implementation lands at ~2740 tokens â€” a 45% reduction
# from v4's ~5000-token f-string but with realistic content for each of
# the 19 sections. The budget is set to 2900 (Phase-6 actual + 6%
# headroom) to allow minor edits without re-budgeting; if v5 is not
# tracking close to budget by Phase 12, Phase 13 polish will tighten.
SECTION_ORDER: List[Section] = [
    Section("identity",                "identity.md",                 75),
    Section("tool_classes",            "tool_classes.md",            410),  # PROMOTED â€” PS Issue #7
    Section("system",                  "system.md",                  150),
    Section("tool_efficiency",         "tool_efficiency.md",         190),
    Section("doing_tasks",             "doing_tasks.md",             300),
    Section("critique_handling",       "critique_handling.md",       190),
    Section("answer_preference",       "answer_preference.md",       120),
    Section("data_validation",         "data_validation.md",         120),
    Section("executing_actions",       "executing_actions.md",       170),
    Section("output_style",            "output_style.md",             85),
    Section("subagent_coord",          "subagent_coord.md",          135),
    Section("status_doc",              "status_doc.md",              105),
    Section("verification_contract",   "verification_contract.md",   170),
    Section("memory_protocol",         "memory_protocol.md",         130),
    Section("documents",               "documents.md",               110),
    Section("security",                "security.md",                 85),
    Section("mcp",                     "mcp.md",                      40),
    Section("commands",                "commands.md",                 70),
    Section("skill_patching",          "skill_patching.md",          225),
]

# Total cap for the static prefix. Phase-6 actual â‰ˆ 2740, cap 2900 gives
# 6% headroom for minor edits. v4's ~5000-token monolith â†’ 2740 is a 45%
# reduction. Phase 13 polish target is to tighten to â‰¤2500.
STATIC_TOKEN_BUDGET = 2900


# ============================================================
# Token estimation
# ============================================================

def estimate_tokens(text: str) -> int:
    """Approximate token count for `text` using the 4-chars-per-token heuristic.

    Phase 6 uses this for the audit gate. Phase 12+ may swap in a real
    tokenizer (anthropic-tokenizer or tiktoken cl100k) â€” the function
    signature stays the same.

    Aggregate audit (`tests/aggregate_audit.py`) compares this estimate
    against sampled live Bedrock prompt accounting on fixed fixtures and
    fails the gate if the divergence exceeds Â±5%.
    """
    if not text:
        return 0
    # Bedrock + Anthropic Claude tokenize at roughly 1 token per 3.5-4 chars
    # for English code-mixed content. We use 4.0 as a slight under-estimate
    # so the audit gate fails fast if a section grows past its cap.
    return max(1, len(text) // 4)


# ============================================================
# Section file IO + cap enforcement
# ============================================================

_PROMPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _read_section_file(file_name: str) -> str:
    """Read a section file relative to the `prompt/` package directory."""
    path = os.path.join(_PROMPT_DIR, file_name)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"prompt section file missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def section_text(section_name: str) -> str:
    """Read one section's `.md` file and return the trimmed text.

    Raises:
        FileNotFoundError if the section file is missing.
        KeyError if `section_name` is not in SECTION_ORDER.
    """
    for s in SECTION_ORDER:
        if s.name == section_name:
            return _read_section_file(s.file)
    raise KeyError(f"unknown section: {section_name!r}")


def section_token_estimate(section_name: str) -> int:
    """Token estimate for one section."""
    return estimate_tokens(section_text(section_name))


def all_sections() -> List[Tuple[str, str]]:
    """Return [(name, text), ...] in SECTION_ORDER. Reads all .md files."""
    return [(s.name, _read_section_file(s.file)) for s in SECTION_ORDER]


# ============================================================
# Cap-enforcement (used by tests + audit gate)
# ============================================================

def check_section_caps(strict: bool = True) -> List[str]:
    """Validate every section is under its token_cap.

    Returns a list of violation messages. Empty list = all clean.
    If `strict=True` (default), missing files are also reported.
    """
    violations: List[str] = []
    total = 0
    for s in SECTION_ORDER:
        try:
            text = _read_section_file(s.file)
        except FileNotFoundError as e:
            if strict:
                violations.append(f"[missing] {s.name} â†’ {s.file}: {e}")
            continue
        tokens = estimate_tokens(text)
        total += tokens
        if tokens > s.token_cap:
            violations.append(
                f"[over-cap] {s.name} ({s.file}): {tokens} tokens, "
                f"cap {s.token_cap} (over by {tokens - s.token_cap})"
            )
    if total > STATIC_TOKEN_BUDGET:
        violations.append(
            f"[over-budget] static prompt total: {total} tokens, "
            f"budget {STATIC_TOKEN_BUDGET} (over by {total - STATIC_TOKEN_BUDGET})"
        )
    return violations


def total_static_tokens() -> int:
    """Return the estimated total tokens for the static prefix."""
    return sum(estimate_tokens(_read_section_file(s.file)) for s in SECTION_ORDER)


# ============================================================
# Memoization (Runnable parity: cache section results across turns)
# ============================================================

# Phase 6 sections are pure-static reads, so the memo is just an LRU-1
# avoiding repeated disk IO. Phase 8+ may add cache_break=True sections
# whose compute() is expensive; the memo will then cache results per
# session and be cleared by `clear_section_cache()` on /clear or /compact.
_SECTION_CACHE: Dict[str, str] = {}


def get_cached_section(name: str) -> Optional[str]:
    return _SECTION_CACHE.get(name)


def set_cached_section(name: str, text: str) -> None:
    _SECTION_CACHE[name] = text


def clear_section_cache() -> None:
    """Runnable parity: `clearSystemPromptSections()` invoked on /clear or /compact.

    Phase 8 will wire this into the QueryEngine's compaction handler.
    """
    _SECTION_CACHE.clear()


# ============================================================
# Compose the static prefix
# ============================================================

def build_static_prefix() -> str:
    """Concatenate all sections in SECTION_ORDER, separated by `\\n\\n`.

    This is the byte-stable cached prefix that `build_system_prompt()`
    in `prompt/__init__.py` returns to the caller. Bedrock applies
    `cache_control={'type':'ephemeral'}` to this prefix.
    """
    parts: List[str] = []
    for s in SECTION_ORDER:
        cached = get_cached_section(s.name)
        if cached is not None and not s.cache_break:
            parts.append(cached)
            continue
        text = _read_section_file(s.file)
        set_cached_section(s.name, text)
        parts.append(text)
    return "\n\n".join(parts)

exec
"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content -Path "compact_v5/MAIN/agent/prompt/__init__.py"' in D:\Github\sagemaker-coding-agent
 succeeded in 433ms:
"""V5 prompt package â€” assembles the system prompt from sections.

Per ADR-002 + ADR-012:
  - 19 file-per-section `.md` files (`identity.md`, `tool_classes.md`, ...)
  - `sections.py` â€” section registry + token-cap enforcement
  - `_CACHE_BOUNDARY.md` â€” explicit marker matching v4's `# === DYNAMIC ===`
                          line so Phase-1's BedrockClient still splits
                          correctly.

`build_system_prompt(ctx)` returns the assembled prompt as a single
string with the cache-boundary marker between static and dynamic
content. Phase 1's `BedrockClient.chat()` already applies
`cache_control={"type":"ephemeral"}` to the static prefix when the
string contains the marker â€” Phase 6 just locks the structure.

Phase 6 ships ZERO dynamic sections. The dynamic group is reserved for:
  - todo_restoration (Phase 8 â€” after auto-compact)
  - file_restoration (Phase 8 â€” after auto-compact)
  - skill_active (Phase 10 â€” per-skill auto-trigger content)
  - iteration_budget_status (Phase 8 â€” current budget)

When the dynamic list is empty (Phase 6 default), the assembled prompt
is just the static prefix + the cache-boundary marker. BedrockClient
then caches the entire static prefix as one block.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from .sections import (  # noqa: F401  (public re-exports)
    SECTION_ORDER,
    STATIC_TOKEN_BUDGET,
    Section,
    all_sections,
    build_static_prefix,
    check_section_caps,
    clear_section_cache,
    estimate_tokens,
    section_text,
    section_token_estimate,
    total_static_tokens,
)


# ============================================================
# Cache-boundary marker â€” SINGLE SOURCE OF TRUTH
# ============================================================
#
# Codex Phase-06 review finding 3 fix: this is the ONLY canonical
# definition of the boundary string. `core/cache.py` imports it.
# `runtime/bedrock_client.py` (Phase 1) keeps a local string literal
# that MUST be byte-equal to this constant; the equality is locked by
# `test_boundary_constants_match_across_modules`.
#
# Format: leading `\n\n` separates the boundary from the preceding
# section's content; the trailing line is intentionally NOT terminated
# with a newline so `prompt.split(CACHE_BOUNDARY, 1)` produces a
# `dynamic_part` that starts EXACTLY where the dynamic content begins
# (a leading `\n` in dynamic_part is preserved verbatim).
CACHE_BOUNDARY = "\n\n# === DYNAMIC ==="

# Backwards-compat alias used by some early Phase-6 callers â€” keep as
# a simple alias of the canonical name. (The single-source-of-truth
# constant is `CACHE_BOUNDARY`; `CACHE_BOUNDARY_MARKER` was the original
# Phase-6 name. Both refer to the same value.)
CACHE_BOUNDARY_MARKER = CACHE_BOUNDARY


def _read_boundary_file() -> str:
    """Read the boundary file. The marker line `# === DYNAMIC ===` must
    be present somewhere in the body (BedrockClient splits on it)."""
    boundary_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_CACHE_BOUNDARY.md")
    if not os.path.isfile(boundary_path):
        raise FileNotFoundError(f"_CACHE_BOUNDARY.md missing at {boundary_path}")
    with open(boundary_path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# Public builder
# ============================================================

def build_system_prompt(ctx: Optional[Dict[str, Any]] = None) -> str:
    """Assemble the full system prompt = static prefix + boundary + dynamic.

    Args:
      ctx: optional context dict for dynamic sections. Keys recognised
           Phase 6 (all optional, all empty by default):
             - dynamic_blocks: List[str] of additional dynamic content
                               (e.g., todo_restoration, file_restoration).
                               Phase 8+ will populate these.

    Returns:
      Single string with the static prefix, the cache-boundary marker,
      and any dynamic blocks joined with `\\n\\n`. BedrockClient splits
      on the marker for cache_control placement.
    """
    ctx = ctx or {}
    static = build_static_prefix()
    dynamic_blocks: List[str] = list(ctx.get("dynamic_blocks") or [])

    # Always include the boundary marker even if dynamic_blocks is empty.
    # BedrockClient handles "boundary present, no dynamic content" by caching
    # the full static prefix as one block.
    # CACHE_BOUNDARY already starts with `\n\n` so we concatenate directly
    # rather than join with `"\n\n"` (which would double the leading newlines).
    body = static + CACHE_BOUNDARY
    if dynamic_blocks:
        body += "\n" + "\n\n".join(dynamic_blocks)
    return body


def assert_static_prompt_under_budget() -> None:
    """Raise if the static prefix exceeds STATIC_TOKEN_BUDGET or any
    section exceeds its individual cap. Used by the audit gate
    (`tests/aggregate_audit.py`) before Phase 7."""
    violations = check_section_caps(strict=True)
    if violations:
        raise AssertionError(
            "Phase 6 token-cap audit failed:\n  " + "\n  ".join(violations)
        )

web search: 
web search: 
codex
**Findings (by severity)**

1. **High: `env_block` is not wired into prompt assembly; behavior is test-only right now.**  
   `render_env_block()` is defined, but I found no production call sites outside the test file. So ADR-020 closure claims for env-block output are not effective in runtime prompt construction.  
   - [env_block.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/prompt/env_block.py:121)  
   - [test_block_e_f.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_e_f.py:56)  
   - [__init__.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/prompt/__init__.py:89)

2. **Medium: cache-stable “session start” helper exists but is not used in rendered env output.**  
   `get_session_start_date()` is memoized, but `render_env_block()` uses non-memoized `get_local_month_year()` for the “Session start” line. That means month-boundary sessions can shift value and the label is semantically inaccurate.  
   - [env_block.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/prompt/env_block.py:33)  
   - [env_block.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/prompt/env_block.py:145)

3. **Low: platform-specific test is weak on non-Windows.**  
   `test_env_block_windows_shell_hint` does no assertion unless running on Windows, so portability regressions can slip through on Linux/macOS CI.  
   - [test_block_e_f.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_e_f.py:131)

**Axis verdicts**

- **AXIS A (errors/regressions/security):** **CHANGES_REQUESTED**  
  Core logic is reasonable (prefix stripping via canonicalizer and OS/shell hints), but the integration gap and session-start mismatch are real regressions vs. claimed closure.

- **AXIS B (v5 fit vs ADR-020 0-2/0-4/0-6):** **DRIFTED**  
  0-4 and 0-6 are implemented in module/tests, but not effectively shipped if not wired. 0-2 cache-stability intent is only partially realized in rendered output.

- **AXIS C (coverage + undeclared patterns):**  
  - `0-2`: partial (helper exists/tests exist; rendered field does not use memoized helper).  
  - `0-4`: implemented in formatter/tests.  
  - `0-6`: implemented with 5-entry map + cross-region normalization hook.  
  - **UNDECLARED_PATTERN:** env-block renderer currently appears orphaned from runtime prompt assembly.

**FINAL: REJECT**

Couldn’t execute tests locally in this environment due unavailable runnable Python/tooling access (Windows Store shim + blocked `uv` Python download), so this is static review plus code-path tracing.
2026-05-03T03:54:55.656697Z ERROR codex_core::session: failed to record rollout items: thread 019debf6-05fc-7852-bd62-5d11326d009f not found
tokens used
34,386
**Findings (by severity)**

1. **High: `env_block` is not wired into prompt assembly; behavior is test-only right now.**  
   `render_env_block()` is defined, but I found no production call sites outside the test file. So ADR-020 closure claims for env-block output are not effective in runtime prompt construction.  
   - [env_block.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/prompt/env_block.py:121)  
   - [test_block_e_f.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_e_f.py:56)  
   - [__init__.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/prompt/__init__.py:89)

2. **Medium: cache-stable “session start” helper exists but is not used in rendered env output.**  
   `get_session_start_date()` is memoized, but `render_env_block()` uses non-memoized `get_local_month_year()` for the “Session start” line. That means month-boundary sessions can shift value and the label is semantically inaccurate.  
   - [env_block.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/prompt/env_block.py:33)  
   - [env_block.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/prompt/env_block.py:145)

3. **Low: platform-specific test is weak on non-Windows.**  
   `test_env_block_windows_shell_hint` does no assertion unless running on Windows, so portability regressions can slip through on Linux/macOS CI.  
   - [test_block_e_f.py](/D:/Github/sagemaker-coding-agent/compact_v5/MAIN/agent/tests/integration/test_block_e_f.py:131)

**Axis verdicts**

- **AXIS A (errors/regressions/security):** **CHANGES_REQUESTED**  
  Core logic is reasonable (prefix stripping via canonicalizer and OS/shell hints), but the integration gap and session-start mismatch are real regressions vs. claimed closure.

- **AXIS B (v5 fit vs ADR-020 0-2/0-4/0-6):** **DRIFTED**  
  0-4 and 0-6 are implemented in module/tests, but not effectively shipped if not wired. 0-2 cache-stability intent is only partially realized in rendered output.

- **AXIS C (coverage + undeclared patterns):**  
  - `0-2`: partial (helper exists/tests exist; rendered field does not use memoized helper).  
  - `0-4`: implemented in formatter/tests.  
  - `0-6`: implemented with 5-entry map + cross-region normalization hook.  
  - **UNDECLARED_PATTERN:** env-block renderer currently appears orphaned from runtime prompt assembly.

**FINAL: REJECT**

Couldn’t execute tests locally in this environment due unavailable runnable Python/tooling access (Windows Store shim + blocked `uv` Python download), so this is static review plus code-path tracing.
