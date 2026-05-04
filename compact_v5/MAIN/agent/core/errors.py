"""V5 core/errors.py — Bedrock error classifier (Phase 8 extraction).

Per ADR-014: extracted verbatim from Phase-1 `runtime/bedrock_client.py`
(which itself is a verbatim port from `compact_v4/MAIN/agent/sagemaker_agent.py`).

PORT_LOG: #017.

Why this lives here in Phase 8 (not Phase 1):
The classifier was bundled with `BedrockClient` in Phase 1 to avoid a
circular Phase-1/Phase-8 dependency. Now that core/ exists, the classifier
gets its own module so:
  - QueryEngine can import without pulling boto3 transitively
  - Tests can exercise classification logic without a Bedrock client
  - Future phases can reuse classifier semantics outside Bedrock invocation

Behavior is byte-equivalent with Phase-1. `runtime/bedrock_client.py`
re-imports these names for backwards compatibility (no chat() change).
"""
from __future__ import annotations

import os
import traceback
from typing import Any


class BedrockErrorCategory:
    """Categories of Bedrock invoke errors. Used by ErrorClassifier + RetryPolicy.

    Block L (PORT_LOG #100) extends to 18 categories per Runnable R4 18-categorization.
    The original 9 (Phase 8) cover the v4 surface; the additional 9 distinguish
    finer-grained cases that benefit from differentiated retry/recovery semantics.
    """
    # Phase 8 (v4) categories — 9
    THROTTLE = "throttle"  # ThrottlingException, rate-limited
    SERVICE_UNAVAILABLE = "service_unavailable"
    MODEL_NOT_READY = "model_not_ready"
    NETWORK = "network"
    VALIDATION_CACHE = "validation_cache"  # cache_control rejected — strip and retry once
    VALIDATION_OTHER = "validation_other"
    CONTEXT_OVERFLOW = "context_overflow"  # prompt-too-long
    ACCESS_DENIED = "access_denied"
    UNKNOWN = "unknown"
    # Block L additions — 9 more (R4 18 categories)
    MAX_TOKENS_OVERFLOW = "max_tokens_overflow"  # output capped at max_tokens — compact + retry
    BEDROCK_5XX_HTML = "bedrock_5xx_html"  # raw HTML 5xx — humanize before user
    REQUEST_TIMEOUT = "request_timeout"  # client-side timeout
    PAYLOAD_TOO_LARGE = "payload_too_large"  # 413 — compact request
    CONFLICT_409 = "conflict_409"  # session/state conflict
    GATEWAY_TIMEOUT = "gateway_timeout"  # 504 — backoff
    MALFORMED_RESPONSE = "malformed_response"  # body parse failure — retry once
    SIGV4_FAILURE = "sigv4_failure"  # auth signature error — no retry, surface
    DEPENDENCY_FAILURE = "dependency_failure"  # downstream service error — backoff


class ShellError(Exception):
    """Structured shell execution error carrying stdout/stderr/code."""

    def __init__(self, message: str, *, stdout: str = "", stderr: str = "", code: int | None = None):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.code = code


class ConfigParseError(Exception):
    """Structured config parse error carrying path/default metadata."""

    def __init__(self, message: str, *, path: str = "", default: Any = None):
        super().__init__(message)
        self.path = path
        self.default = default


class TelemetrySafeError(Exception):
    """Error whose telemetry payload is safe to serialize."""

    def __init__(self, message: str, *, telemetry: dict[str, Any] | None = None):
        super().__init__(message)
        self.telemetry = telemetry or {}


# Block L: which categories are retryable. Used by categorize_retryable().
# Per Runnable R4 categorization.
_RETRYABLE_CATEGORIES = frozenset({
    BedrockErrorCategory.THROTTLE,
    BedrockErrorCategory.SERVICE_UNAVAILABLE,
    BedrockErrorCategory.MODEL_NOT_READY,
    BedrockErrorCategory.NETWORK,
    BedrockErrorCategory.VALIDATION_CACHE,  # retry once after stripping
    BedrockErrorCategory.CONTEXT_OVERFLOW,  # retry after compact
    BedrockErrorCategory.MAX_TOKENS_OVERFLOW,  # retry after compact
    BedrockErrorCategory.BEDROCK_5XX_HTML,  # backoff
    BedrockErrorCategory.REQUEST_TIMEOUT,  # retry once
    BedrockErrorCategory.PAYLOAD_TOO_LARGE,  # retry after compact
    BedrockErrorCategory.GATEWAY_TIMEOUT,  # backoff
    BedrockErrorCategory.MALFORMED_RESPONSE,  # retry once
    BedrockErrorCategory.DEPENDENCY_FAILURE,  # backoff
})


def categorize_retryable(category: str) -> bool:
    """Return True iff `category` is in the retryable set (Block L PORT_LOG #100)."""
    return category in _RETRYABLE_CATEGORIES


def to_error(value: Any) -> Exception:
    """Runnable `toError` analogue: coerce any thrown value to Exception."""
    if isinstance(value, Exception):
        return value
    return Exception(str(value))


def short_error_stack(exc: BaseException, max_frames: int = 5) -> str:
    """Return a short stack string capped to the last N frames."""
    frames = traceback.format_exception(type(exc), exc, exc.__traceback__)
    if len(frames) <= max_frames + 1:
        return "".join(frames).strip()
    return "".join([frames[0], *frames[-max_frames:]]).strip()


def is_fs_inaccessible(exc_or_text: Any) -> bool:
    """True for common filesystem-inaccessible errors."""
    text = str(exc_or_text).lower()
    return any(token in text for token in (
        "enoent", "eacces", "eperm", "enotdir", "eisdir",
        "permission denied", "no such file", "file not found",
    ))


def classify_axios_error(exc_or_text: Any) -> str:
    """Small Axios-style classifier adapted for Bedrock/offline use."""
    text = str(exc_or_text).lower()
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "ssl" in text or "certificate" in text or "zscaler" in text:
        return "ssl"
    if "connection" in text or "econnreset" in text or "network" in text:
        return "network"
    if "status code 5" in text or " 5" in text:
        return "server"
    if "status code 4" in text or " 4" in text:
        return "client"
    return "unknown"


def get_prompt_too_long_token_gap(exc_or_text: Any) -> int:
    """Parse how many tokens a prompt exceeds the accepted context by."""
    import re

    text = str(exc_or_text).lower().replace(",", "")
    patterns = (
        r"(\d+)\s*tokens?\s*(?:>|exceeds|over|above)\s*(\d+)",
        r"context(?:\s+length)?\s*(\d+)\s*(?:>|exceeds|over|above)\s*(\d+)",
        r"prompt is too long.*?(\d+).*?(?:limit|max|context).*?(\d+)",
    )
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            used = int(m.group(1))
            limit = int(m.group(2))
            return max(0, used - limit)
    return 0


def drop_prompt_too_long_message_groups(
    groups: list[Any],
    token_gap: int,
    estimate_tokens,
) -> list[Any]:
    """Drop oldest groups until their estimated tokens cover `token_gap`."""
    remaining = list(groups)
    dropped = 0
    while remaining and dropped < max(0, int(token_gap)):
        first = remaining.pop(0)
        try:
            dropped += max(0, int(estimate_tokens(first)))
        except Exception:
            dropped += 0
    return remaining


def extract_nested_error_message(exc_or_text) -> str:
    """Block L (R4 #9 MUST): humanize Bedrock 5xx errors that contain raw HTML.

    Bedrock occasionally returns HTML error pages on 5xx; the user sees a wall
    of `<html>...<body>The server encountered an error...</body></html>`.
    This helper extracts the readable text from common error shapes:
    - `<title>Error</title>` → use the title.
    - `<body>...text...</body>` → use the body text.
    - `<h1>Error 502</h1>` → use the heading.
    - JSON `{"message": "..."}` → use the message field.

    Falls back to the first 200 chars of the input when no pattern matches.
    """
    import re
    import json as _json

    text = str(exc_or_text)
    if not text.strip():
        return "(empty error)"

    # Try JSON first. Codex iter-1 finding #2: Runnable extracts nested
    # API JSON shapes — `error.error.message` and deeper. Walk up to 3
    # levels deep extracting the deepest "message" / "error" string.
    try:
        data = _json.loads(text)
        if isinstance(data, dict):
            # Walk nested .error.message / .error.error.message paths.
            for path in (
                ("error", "error", "message"),
                ("error", "error", "Message"),
                ("error", "message"),
                ("error", "Message"),
                ("message",),
                ("Message",),
            ):
                cur: Any = data
                for key in path:
                    if isinstance(cur, dict):
                        cur = cur.get(key)
                    else:
                        cur = None
                        break
                if isinstance(cur, str) and cur.strip():
                    return cur.strip()[:200]
            # Fallback: top-level "error" / "Error" if it's a string.
            for key in ("error", "Error"):
                v = data.get(key)
                if isinstance(v, str) and v.strip():
                    return v.strip()[:200]
    except (_json.JSONDecodeError, ValueError):
        pass

    # Try HTML title.
    m = re.search(r"<title[^>]*>([^<]+)</title>", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()[:200]
    # Try h1.
    m = re.search(r"<h1[^>]*>([^<]+)</h1>", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()[:200]
    # Try body text — strip remaining tags.
    m = re.search(r"<body[^>]*>(.*?)</body>", text, re.IGNORECASE | re.DOTALL)
    if m:
        body_text = re.sub(r"<[^>]+>", " ", m.group(1))
        body_text = re.sub(r"\s+", " ", body_text).strip()
        if body_text:
            return body_text[:200]

    # Fallback: strip ALL HTML tags from the full input.
    stripped = re.sub(r"<[^>]+>", " ", text)
    stripped = re.sub(r"\s+", " ", stripped).strip()
    return stripped[:200] or text[:200]


def parse_max_tokens_context_overflow_error(exc) -> bool:
    """Block L (R4 #2 MUST): True iff `exc` is a max-tokens or context-
    overflow error that should trigger compact+retry.

    Distinguishes max_tokens (output cap hit) from prompt-too-long
    (context overflow) — both trigger compact+retry but for different
    reasons. Returns True for either.
    """
    msg = str(exc).lower()
    if "max_tokens" in msg or "max output tokens" in msg or "output token limit" in msg:
        return True
    if "prompt is too long" in msg or "too many tokens" in msg or "input length" in msg:
        return True
    if "context length" in msg or "context_overflow" in msg:
        return True
    return False


def get_retry_after_ms(exc) -> int:
    """Block L (R4 retry-after): parse Retry-After header value from exception.

    Bedrock 429 responses include a Retry-After header (seconds). This helper
    extracts the integer second value and returns milliseconds. Returns 0
    when no Retry-After is found.

    Accepts:
    - integer seconds: "5" → 5000
    - HTTP-date format (RFC 1123): "Wed, 21 Oct 2026 07:28:00 GMT" → ms-until-then
    - error message containing "Retry-After: 5": parses the trailing seconds
    """
    import re
    import time
    from email.utils import parsedate_to_datetime

    s = str(exc)
    # Match "Retry-After: <value>" header pattern.
    m = re.search(r"retry-after\s*:?\s*(\d+)", s, re.IGNORECASE)
    if m:
        try:
            return int(m.group(1)) * 1000
        except (ValueError, TypeError):
            return 0
    # Match HTTP-date. Codex iter-1 finding #1: accept both RFC-1123
    # tail forms — `GMT` and `±0000` — since email.utils.format_datetime
    # produces the latter on Python 3.x. parsedate_to_datetime parses
    # either.
    m = re.search(
        r"retry-after\s*:?\s*([A-Za-z]{3},\s*\d.+\d{4}\s+\d{2}:\d{2}:\d{2}\s+(?:GMT|[+-]\d{4}))",
        s,
        re.IGNORECASE,
    )
    if m:
        try:
            dt = parsedate_to_datetime(m.group(1))
            wait = max(0, int((dt.timestamp() - time.time()) * 1000))
            return wait
        except (ValueError, TypeError):
            return 0
    return 0


def get_rate_limit_reset_delay_ms(exc_or_text: Any) -> int:
    """Parse Anthropic unified-reset Unix seconds into delay milliseconds."""
    import re
    import time

    text = str(exc_or_text)
    m = re.search(
        r"anthropic-ratelimit-unified-reset\s*:?\s*(\d{10}(?:\.\d+)?)",
        text,
        re.IGNORECASE,
    )
    if not m:
        return 0
    reset_at = float(m.group(1))
    return max(0, int((reset_at - time.time()) * 1000))


def is_529_error(exc_or_text: Any) -> bool:
    text = str(exc_or_text).lower()
    return "529" in text or "overloaded" in text or "capacity" in text


def should_retry_529(query_source: str, attempt: int = 0) -> bool:
    """Retry user-facing 529s briefly; drop recursive/internal cascades."""
    if str(query_source or "").lower() in {"compact", "session_memory", "memory"}:
        return False
    return attempt < 3


def fallback_model_for_529(model_id: str, consecutive_529: int) -> str:
    """Return Sonnet fallback model after 3 consecutive Opus 529s."""
    if consecutive_529 < 3:
        return ""
    mid = str(model_id or "")
    if "opus" not in mid.lower():
        return ""
    return mid.replace("opus", "sonnet").replace("Opus", "Sonnet")


def extract_connection_error_details(exc_or_text: Any) -> dict[str, str]:
    """Walk connection/SSL text and return a human hint."""
    text = str(exc_or_text)
    low = text.lower()
    hint = ""
    kind = "connection"
    if "ssl" in low or "certificate" in low or "zscaler" in low:
        kind = "ssl"
        hint = "Check corporate proxy/Zscaler certificate trust or AWS CA bundle."
    elif "timed out" in low or "timeout" in low:
        kind = "timeout"
        hint = "Network timeout while contacting Bedrock; retry or rebuild client."
    elif "econnreset" in low or "connection reset" in low:
        kind = "reset"
        hint = "Connection was reset; rebuild the runtime client before retry."
    return {"kind": kind, "message": text[:500], "hint": hint}


def sanitize_api_error(exc_or_text: Any) -> str:
    """Human-safe Bedrock API error text with HTML/JSON extraction."""
    return extract_nested_error_message(exc_or_text)


def humanize_api_error(exc_or_text: Any, status_code: int | None = None) -> str:
    """Bedrock-only API error humanizer."""
    message = sanitize_api_error(exc_or_text)
    if status_code:
        return f"Bedrock API error {status_code}: {message}"
    return f"Bedrock API error: {message}"


def rollback_to_last_assistant_turn(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return conversation history through the last assistant turn."""
    for idx in range(len(messages) - 1, -1, -1):
        if messages[idx].get("role") == "assistant":
            return list(messages[: idx + 1])
    return []


class ErrorClassifier:
    """Classifies Bedrock exceptions into a (category, recovery, debug_msg) triple.

    Verbatim port of v4's classifier. Recovery values:
      - "strip_cache_retry": cache_control rejected; strip blocks and retry once
      - "compact_retry":     prompt-too-long; caller should compact and retry
      - "backoff":           transient (throttle/503/network); retry with jitter
      - "no_retry":          permanent (validation/access denied); surface to user
    """

    @staticmethod
    def classify(exc: Exception):
        msg_lower = str(exc).lower()
        cls_name = type(exc).__name__.lower()

        # Block L additions — check most-specific first.
        if "max_tokens" in msg_lower or "max output tokens" in msg_lower or "output token limit" in msg_lower:
            return BedrockErrorCategory.MAX_TOKENS_OVERFLOW, "compact_retry", str(exc)[:200]
        if "<html" in msg_lower or "<body" in msg_lower or "<title" in msg_lower:
            # Raw HTML 5xx error — backoff + humanize before user-facing display.
            return BedrockErrorCategory.BEDROCK_5XX_HTML, "backoff", str(exc)[:200]
        if "504" in msg_lower or "gatewaytimeout" in msg_lower:
            return BedrockErrorCategory.GATEWAY_TIMEOUT, "backoff", str(exc)[:200]
        if "413" in msg_lower or "payload too large" in msg_lower or "request entity too large" in msg_lower:
            return BedrockErrorCategory.PAYLOAD_TOO_LARGE, "compact_retry", str(exc)[:200]
        if "409" in msg_lower or "conflictexception" in msg_lower:
            return BedrockErrorCategory.CONFLICT_409, "no_retry", str(exc)[:200]
        # Codex iter-1 finding #3: broaden timeout matching to common shapes
        # ReadTimeout / ConnectTimeout / APIConnectionTimeoutError / "timed out".
        # Note: Phase 8 NETWORK pattern still catches connect/read timeouts
        # as cls_name matches; this REQUEST_TIMEOUT branch must run BEFORE
        # the NETWORK branch to differentiate them. Both are retryable.
        if (
            "request_timeout" in msg_lower
            or "request-timeout" in msg_lower
            or "408" in msg_lower
            or "request timed out" in msg_lower
            or "timed out" in msg_lower
            or "timeout" in cls_name
            or "apiconnectiontimeout" in cls_name
        ):
            return BedrockErrorCategory.REQUEST_TIMEOUT, "backoff", str(exc)[:200]
        if "malformed" in msg_lower or "could not parse response" in msg_lower or "decode" in cls_name:
            return BedrockErrorCategory.MALFORMED_RESPONSE, "backoff", str(exc)[:200]
        if "sigv4" in msg_lower or "signature" in msg_lower or "credentialverify" in cls_name:
            return BedrockErrorCategory.SIGV4_FAILURE, "no_retry", str(exc)[:200]
        if "dependency" in msg_lower or "dependencyfailedexception" in msg_lower:
            return BedrockErrorCategory.DEPENDENCY_FAILURE, "backoff", str(exc)[:200]

        # Phase 8 categories — preserved.
        if "validationexception" in msg_lower and (
            "cache_control" in msg_lower
            or "prompt-caching" in msg_lower
            or "cache" in msg_lower
        ):
            return BedrockErrorCategory.VALIDATION_CACHE, "strip_cache_retry", str(exc)[:200]
        if "validationexception" in msg_lower and (
            "prompt is too long" in msg_lower
            or "too many tokens" in msg_lower
            or "input length" in msg_lower
        ):
            return BedrockErrorCategory.CONTEXT_OVERFLOW, "compact_retry", str(exc)[:200]
        if "validationexception" in msg_lower:
            return BedrockErrorCategory.VALIDATION_OTHER, "no_retry", str(exc)[:200]
        if "throttlingexception" in msg_lower or "rate" in msg_lower:
            return BedrockErrorCategory.THROTTLE, "backoff", str(exc)[:200]
        if "serviceunavailable" in msg_lower or "503" in msg_lower:
            return BedrockErrorCategory.SERVICE_UNAVAILABLE, "backoff", str(exc)[:200]
        if "modelnotready" in msg_lower or "not ready" in msg_lower:
            return BedrockErrorCategory.MODEL_NOT_READY, "backoff", str(exc)[:200]
        if "accessdenied" in msg_lower or "403" in msg_lower or "unauthorized" in msg_lower:
            return BedrockErrorCategory.ACCESS_DENIED, "no_retry", str(exc)[:200]
        if (
            "endpointconnectionerror" in cls_name
            or "connecttimeout" in cls_name
            or "readtimeout" in cls_name
            or "connectionerror" in cls_name
        ):
            return BedrockErrorCategory.NETWORK, "backoff", str(exc)[:200]
        return BedrockErrorCategory.UNKNOWN, "no_retry", str(exc)[:200]
