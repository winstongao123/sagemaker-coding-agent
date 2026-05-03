"""Block L — Error/retry/cache-break + Bedrock guardrails + daemon-thread call.

Source: Runnable services/api/errors.ts + cacheBreakDetection.ts +
withRetry.ts.

Tests per TEST_DESIGN §Block L (8 tests; 2 T2 daemon-thread tests
deferred to Block J real-AWS integration):
- test_categorize_retryable_18_error_types
- test_parse_max_tokens_overflow_recovers
- test_extract_nested_error_message_humanizes_5xx_html
- test_retry_after_header_parsed
- test_per_tool_cache_break_detection
- test_haiku_excluded_from_cache_break_3loc
- test_daemon_thread_bedrock_call_responds_to_ctrl_c (DEFERRED)
- test_30s_heartbeat_during_long_call (DEFERRED)
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
# TEST_DESIGN row 1 — 18 error categories with retryable verdicts
# ============================================================

def test_categorize_retryable_18_error_types():
    """Each of 18 Runnable error categories → correct retryable verdict.

    Retryable (13): throttle, service_unavailable, model_not_ready,
    network, validation_cache, context_overflow, max_tokens_overflow,
    bedrock_5xx_html, request_timeout, payload_too_large,
    gateway_timeout, malformed_response, dependency_failure.

    Non-retryable (5): validation_other, access_denied, conflict_409,
    sigv4_failure, unknown.
    """
    from core import BedrockErrorCategory, categorize_retryable

    # All 18 categories defined.
    all_18 = [
        BedrockErrorCategory.THROTTLE,
        BedrockErrorCategory.SERVICE_UNAVAILABLE,
        BedrockErrorCategory.MODEL_NOT_READY,
        BedrockErrorCategory.NETWORK,
        BedrockErrorCategory.VALIDATION_CACHE,
        BedrockErrorCategory.VALIDATION_OTHER,
        BedrockErrorCategory.CONTEXT_OVERFLOW,
        BedrockErrorCategory.ACCESS_DENIED,
        BedrockErrorCategory.UNKNOWN,
        BedrockErrorCategory.MAX_TOKENS_OVERFLOW,
        BedrockErrorCategory.BEDROCK_5XX_HTML,
        BedrockErrorCategory.REQUEST_TIMEOUT,
        BedrockErrorCategory.PAYLOAD_TOO_LARGE,
        BedrockErrorCategory.CONFLICT_409,
        BedrockErrorCategory.GATEWAY_TIMEOUT,
        BedrockErrorCategory.MALFORMED_RESPONSE,
        BedrockErrorCategory.SIGV4_FAILURE,
        BedrockErrorCategory.DEPENDENCY_FAILURE,
    ]
    assert len(set(all_18)) == 18, f"Expected 18 distinct categories; got {len(set(all_18))}"

    retryable = {
        BedrockErrorCategory.THROTTLE,
        BedrockErrorCategory.SERVICE_UNAVAILABLE,
        BedrockErrorCategory.MODEL_NOT_READY,
        BedrockErrorCategory.NETWORK,
        BedrockErrorCategory.VALIDATION_CACHE,
        BedrockErrorCategory.CONTEXT_OVERFLOW,
        BedrockErrorCategory.MAX_TOKENS_OVERFLOW,
        BedrockErrorCategory.BEDROCK_5XX_HTML,
        BedrockErrorCategory.REQUEST_TIMEOUT,
        BedrockErrorCategory.PAYLOAD_TOO_LARGE,
        BedrockErrorCategory.GATEWAY_TIMEOUT,
        BedrockErrorCategory.MALFORMED_RESPONSE,
        BedrockErrorCategory.DEPENDENCY_FAILURE,
    }
    non_retryable = {
        BedrockErrorCategory.VALIDATION_OTHER,
        BedrockErrorCategory.ACCESS_DENIED,
        BedrockErrorCategory.CONFLICT_409,
        BedrockErrorCategory.SIGV4_FAILURE,
        BedrockErrorCategory.UNKNOWN,
    }

    for cat in retryable:
        assert categorize_retryable(cat) is True, f"{cat} should be retryable"
    for cat in non_retryable:
        assert categorize_retryable(cat) is False, f"{cat} should NOT be retryable"


# ============================================================
# TEST_DESIGN row 2 — max-tokens overflow triggers compact + retry (R4 #2 MUST)
# ============================================================

def test_parse_max_tokens_overflow_recovers():
    """parseMaxTokensContextOverflowError triggers compact + retry."""
    from core import (
        BedrockErrorCategory,
        ErrorClassifier,
        parse_max_tokens_context_overflow_error,
    )

    cases = [
        ValueError("max_tokens 4096 exceeded"),
        RuntimeError("Output token limit reached at 4097"),
        Exception("Prompt is too long: 250000 tokens"),
        Exception("Too many tokens in input length"),
        Exception("context_overflow"),
        Exception("Context length 200001 exceeds 200000"),
    ]
    for exc in cases:
        assert parse_max_tokens_context_overflow_error(exc) is True, (
            f"{exc!r} should be detected as max-tokens/context overflow"
        )

    # Non-cases.
    for exc in [Exception("ThrottlingException"), ValueError("unrelated")]:
        assert parse_max_tokens_context_overflow_error(exc) is False

    # Classifier maps max-tokens overflow to MAX_TOKENS_OVERFLOW with
    # compact_retry recovery.
    cat, recovery, _ = ErrorClassifier.classify(
        Exception("max_tokens 4096 exceeded")
    )
    assert cat == BedrockErrorCategory.MAX_TOKENS_OVERFLOW
    assert recovery == "compact_retry"


# ============================================================
# TEST_DESIGN row 3 — humanize 5xx HTML errors (R4 #9 MUST)
# ============================================================

def test_extract_nested_error_message_humanizes_5xx_html():
    """Bedrock 5xx with raw HTML → user sees clean error message."""
    from core import extract_nested_error_message

    # HTML title.
    html_title = "<html><head><title>503 Service Unavailable</title></head><body>x</body></html>"
    out = extract_nested_error_message(html_title)
    assert out == "503 Service Unavailable"

    # H1.
    html_h1 = "<html><body><h1>Internal Server Error</h1><p>x</p></body></html>"
    out = extract_nested_error_message(html_h1)
    assert "Internal Server Error" in out

    # Body fallback.
    html_body = "<html><body>The server encountered an error.</body></html>"
    out = extract_nested_error_message(html_body)
    assert "The server encountered an error" in out

    # JSON.
    json_err = '{"message": "AccessDenied: principal lacks permission"}'
    out = extract_nested_error_message(json_err)
    assert "AccessDenied" in out

    # Plain string fallback.
    plain = "ThrottlingException: Rate exceeded"
    out = extract_nested_error_message(plain)
    assert "ThrottlingException" in out


# ============================================================
# TEST_DESIGN row 4 — Retry-After header parsed
# ============================================================

def test_retry_after_header_parsed():
    """getRetryAfterMs parses 'Retry-After: 5' → 5000ms."""
    from core import get_retry_after_ms

    assert get_retry_after_ms(Exception("HTTP 429: Retry-After: 5")) == 5000
    assert get_retry_after_ms("Retry-After: 30") == 30000
    assert get_retry_after_ms("retry-after:60") == 60000
    # No header → 0.
    assert get_retry_after_ms("ThrottlingException") == 0
    assert get_retry_after_ms("") == 0


# ============================================================
# TEST_DESIGN row 5 — per-tool cache-break detection
# ============================================================

def test_per_tool_cache_break_detection():
    """Per-tool schema hash change → cache-deletion fires for that tool only."""
    from core import PerToolCacheBreakDetector

    detector = PerToolCacheBreakDetector()

    tools_v1 = [
        {"name": "read_file", "description": "Read", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
        {"name": "write_file", "description": "Write", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
    ]
    # First call: establish baseline; no breaks.
    breaks = detector.detect_breaks(tools_v1, model_id="anthropic.claude-sonnet-4-6")
    assert breaks == []

    # Same tools again → no breaks.
    breaks = detector.detect_breaks(tools_v1, model_id="anthropic.claude-sonnet-4-6")
    assert breaks == []

    # read_file's schema changes; write_file unchanged.
    tools_v2 = [
        {"name": "read_file", "description": "Read v2", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "encoding": {"type": "string"}}}},
        {"name": "write_file", "description": "Write", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
    ]
    breaks = detector.detect_breaks(tools_v2, model_id="anthropic.claude-sonnet-4-6")
    assert breaks == ["read_file"], f"Expected only read_file broken; got {breaks}"


# ============================================================
# TEST_DESIGN row 6 — Haiku excluded from cache-break (R4 #14 MUST 3LOC)
# ============================================================

def test_haiku_excluded_from_cache_break_3loc():
    """Haiku-4.5 model_id in EXCLUDED set → cache-break detector skips."""
    from core import PerToolCacheBreakDetector, is_cache_break_excluded

    # Direct exclusion check.
    assert is_cache_break_excluded("anthropic.claude-haiku-4-5-20251001-v1:0") is True
    assert is_cache_break_excluded("au.anthropic.claude-haiku-4-5-20251001-v1:0") is True
    assert is_cache_break_excluded("apac.anthropic.claude-haiku-4-5-20251001-v1:0") is True
    # Non-Haiku: not excluded.
    assert is_cache_break_excluded("anthropic.claude-sonnet-4-6") is False
    assert is_cache_break_excluded("") is False

    # Detector skip path: even when schemas change, Haiku model returns [].
    detector = PerToolCacheBreakDetector()
    tools_v1 = [{"name": "x", "description": "y", "input_schema": {"v": 1}}]
    detector.detect_breaks(tools_v1, model_id="anthropic.claude-sonnet-4-6")  # establish baseline
    tools_v2 = [{"name": "x", "description": "y", "input_schema": {"v": 2}}]  # schema changed

    # Sonnet sees the break.
    breaks_sonnet = detector.detect_breaks(tools_v2, model_id="anthropic.claude-sonnet-4-6")
    assert "x" in breaks_sonnet

    # Reset baseline + check Haiku gets [] regardless.
    detector2 = PerToolCacheBreakDetector()
    detector2.detect_breaks(tools_v1, model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
    breaks_haiku = detector2.detect_breaks(
        tools_v2, model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
    )
    assert breaks_haiku == [], "Haiku must be excluded from cache-break detection"


# ============================================================
# TEST_DESIGN row 7 + 8 — DEFERRED to Block J real-AWS integration
# ============================================================

@pytest.mark.skip(
    reason="Block L T2 daemon-thread test deferred to Block J real-AWS gate "
    "(timing-sensitive; relies on actual long-running Bedrock call to "
    "interrupt with KeyboardInterrupt). Per ADR-036 §3."
)
def test_daemon_thread_bedrock_call_responds_to_ctrl_c():
    pass


@pytest.mark.skip(
    reason="Block L T2 30s-heartbeat test deferred to Block J real-AWS gate "
    "(timing-sensitive 30s wall-clock test). Per ADR-036 §3."
)
def test_30s_heartbeat_during_long_call():
    pass


# ============================================================
# Behavioral lock tests
# ============================================================

def test_classifier_recognizes_new_categories():
    """Classifier maps each new category to a sensible default recovery."""
    from core import BedrockErrorCategory, ErrorClassifier

    cases = [
        (Exception("<html><body>503 Service Unavailable</body></html>"),
         BedrockErrorCategory.BEDROCK_5XX_HTML, "backoff"),
        (Exception("HTTP 504 GatewayTimeout"),
         BedrockErrorCategory.GATEWAY_TIMEOUT, "backoff"),
        (Exception("HTTP 413 Payload too large"),
         BedrockErrorCategory.PAYLOAD_TOO_LARGE, "compact_retry"),
        (Exception("HTTP 409 ConflictException"),
         BedrockErrorCategory.CONFLICT_409, "no_retry"),
        (Exception("malformed response: could not parse response"),
         BedrockErrorCategory.MALFORMED_RESPONSE, "backoff"),
        (Exception("SigV4 signature failed"),
         BedrockErrorCategory.SIGV4_FAILURE, "no_retry"),
        (Exception("DependencyFailedException: downstream"),
         BedrockErrorCategory.DEPENDENCY_FAILURE, "backoff"),
    ]
    for exc, expected_cat, expected_recovery in cases:
        cat, recovery, _ = ErrorClassifier.classify(exc)
        assert cat == expected_cat, f"{exc!r} → got {cat}, expected {expected_cat}"
        assert recovery == expected_recovery


def test_hash_tool_schema_deterministic():
    """Same schema content → same hash regardless of key order."""
    from core import hash_tool_schema

    a = {"name": "x", "input_schema": {"type": "object", "properties": {"a": {"type": "string"}}}}
    b = {"input_schema": {"properties": {"a": {"type": "string"}}, "type": "object"}, "name": "x"}
    assert hash_tool_schema(a) == hash_tool_schema(b)
    # Different content → different hash.
    c = {"name": "x", "input_schema": {"type": "string"}}
    assert hash_tool_schema(a) != hash_tool_schema(c)


def test_notify_cache_deletion_skips_excluded_models():
    """notify_cache_deletion returns False for Haiku (R4 #14 MUST)."""
    from core import notify_cache_deletion

    assert notify_cache_deletion(
        "anthropic.claude-haiku-4-5-20251001-v1:0", ["read_file"]
    ) is False
    assert notify_cache_deletion(
        "anthropic.claude-sonnet-4-6", ["read_file"]
    ) is True
