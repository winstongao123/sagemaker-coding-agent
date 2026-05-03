"""Block B — TokenTracker + per-agent attribution + tokenEstimation helpers.

Verbatim port of v4's `TokenTracker` (compact_v4/MAIN/agent/sagemaker_agent.py
lines 3565-3753) plus:
- per-agent input/output/cost attribution (B-11 + Plan v3 §Block B)
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
# B-13 — ToolResult dataclass (V1 gap #1, MUST)
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
# B-10 — MODEL_COSTS (R8 #34, #68; Bedrock-only subset)
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
        au.   — Australia (Sydney; ap-southeast-2 default)
        apac. — Asia-Pacific
        us.   — United States (legacy us-east-1 / us-west-2)
        eu.   — Europe (legacy eu-west-1 / eu-central-1)

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
# R4 #14 — EXCLUDED_MODELS_FOR_CACHE_BREAK (MUST)
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
# B-5 — IMAGE_MAX_TOKEN_SIZE (R4 #38)
# ============================================================
#
# Per Anthropic billing: each image consumed by Bedrock counts for at
# most 2000 tokens regardless of resolution. Used by the rough estimator
# below.

IMAGE_MAX_TOKEN_SIZE: int = 2000


# ============================================================
# B-3 — bytesPerTokenForFileType (R4 #40)
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
# B-6 — estimateMessageTokens with 4/3 padding (R4 #39)
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
# B-7 — hasThinkingBlocks (R4 #43)
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
# B-4 — roughTokenCountEstimationForBlock (R4 #44)
# ============================================================

def rough_token_count_for_block(block: Any) -> int:
    """Per-block-type token estimator.

    text/tool_use/tool_result/image — each has different size math.
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
# TokenTracker — verbatim port of v4 + per-agent attribution
# ============================================================

# Sentinel for distinguishing "not yet recorded" from "recorded as 0".
_NO_USAGE_RECORD: Optional[Dict[str, int]] = None


class TokenTracker:
    """Thread-safe tracker for API token usage, cost, and cache hits per session.

    v5 extension over v4: per-agent attribution dict so parent and
    sub-agent token costs can be reported separately while still rolling
    up to the same `session_cost` total. Per Plan v3 §Block B + B-11.

    The agent_kind argument to `add()` is the attribution bucket key
    (default "parent"; sub-agents pass "build", "explore", "verify",
    etc. — the type-string from `subagent.spawn`).
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
        from runtime.config import CONFIG as _CFG  # noqa: F401 — late import
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
        # Per-agent attribution (Plan v3 §Block B). Parent always tracked
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
            # B-8 — record last usage so estimators can walk back.
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
                        f"TokenTracker: no pricing for model '{mid}' — cost will show as $0. "
                        f"Add to MODEL_COSTS dict in runtime/tokens.py."
                    )
                self.last_cost = 0.0

            # Per-agent attribution (additive — same singleton, separate buckets).
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
    # B-8 / B-9 — context-token math derived from last response
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


try:  # pragma: no cover — registration-time best-effort
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
