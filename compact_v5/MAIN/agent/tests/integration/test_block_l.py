"""Block L â€” Error/retry/cache-break + Bedrock guardrails + daemon-thread call.

Source: Runnable services/api/errors.ts + cacheBreakDetection.ts +
withRetry.ts.

Tests per TEST_DESIGN Â§Block L (8 tests; 2 T2 daemon-thread tests
deferred to Block J real-AWS integration):
- test_categorize_retryable_18_error_types
- test_parse_max_tokens_overflow_recovers
- test_extract_nested_error_message_humanizes_5xx_html
- test_retry_after_header_parsed
- test_per_tool_cache_break_detection
- test_haiku_excluded_from_cache_break_3loc
- test_daemon_thread_bedrock_call_responds_to_ctrl_c
- test_30s_heartbeat_during_long_call
"""
from __future__ import annotations

import os
import sys
import time

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


# ============================================================
# TEST_DESIGN row 1 â€” 18 error categories with retryable verdicts
# ============================================================

def test_categorize_retryable_18_error_types():
    """Each of 18 Runnable error categories â†’ correct retryable verdict.

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
# TEST_DESIGN row 2 â€” max-tokens overflow triggers compact + retry (R4 #2 MUST)
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
# TEST_DESIGN row 3 â€” humanize 5xx HTML errors (R4 #9 MUST)
# ============================================================

def test_extract_nested_error_message_humanizes_5xx_html():
    """Bedrock 5xx with raw HTML â†’ user sees clean error message."""
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
# TEST_DESIGN row 4 â€” Retry-After header parsed
# ============================================================

def test_retry_after_header_parsed():
    """getRetryAfterMs parses 'Retry-After: 5' â†’ 5000ms."""
    from core import get_retry_after_ms

    assert get_retry_after_ms(Exception("HTTP 429: Retry-After: 5")) == 5000
    assert get_retry_after_ms("Retry-After: 30") == 30000
    assert get_retry_after_ms("retry-after:60") == 60000
    # No header â†’ 0.
    assert get_retry_after_ms("ThrottlingException") == 0
    assert get_retry_after_ms("") == 0


# ============================================================
# TEST_DESIGN row 5 â€” per-tool cache-break detection
# ============================================================

def test_per_tool_cache_break_detection():
    """Per-tool schema hash change â†’ cache-deletion fires for that tool only."""
    from core import PerToolCacheBreakDetector

    detector = PerToolCacheBreakDetector()

    tools_v1 = [
        {"name": "read_file", "description": "Read", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
        {"name": "write_file", "description": "Write", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
    ]
    # First call: establish baseline; no breaks.
    breaks = detector.detect_breaks(tools_v1, model_id="anthropic.claude-sonnet-4-5")
    assert breaks == []

    # Same tools again â†’ no breaks.
    breaks = detector.detect_breaks(tools_v1, model_id="anthropic.claude-sonnet-4-5")
    assert breaks == []

    # read_file's schema changes; write_file unchanged.
    tools_v2 = [
        {"name": "read_file", "description": "Read v2", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "encoding": {"type": "string"}}}},
        {"name": "write_file", "description": "Write", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}},
    ]
    breaks = detector.detect_breaks(tools_v2, model_id="anthropic.claude-sonnet-4-5")
    assert breaks == ["read_file"], f"Expected only read_file broken; got {breaks}"


# ============================================================
# TEST_DESIGN row 6 â€” Haiku excluded from cache-break (R4 #14 MUST 3LOC)
# ============================================================

def test_haiku_excluded_from_cache_break_3loc():
    """Haiku-4.5 model_id in EXCLUDED set â†’ cache-break detector skips."""
    from core import PerToolCacheBreakDetector, is_cache_break_excluded

    # Direct exclusion check.
    assert is_cache_break_excluded("anthropic.claude-haiku-4-5-20251001-v1:0") is True
    assert is_cache_break_excluded("au.anthropic.claude-haiku-4-5-20251001-v1:0") is True
    assert is_cache_break_excluded("apac.anthropic.claude-haiku-4-5-20251001-v1:0") is True
    # Non-Haiku: not excluded.
    assert is_cache_break_excluded("anthropic.claude-sonnet-4-5") is False
    assert is_cache_break_excluded("") is False

    # Detector skip path: even when schemas change, Haiku model returns [].
    detector = PerToolCacheBreakDetector()
    tools_v1 = [{"name": "x", "description": "y", "input_schema": {"v": 1}}]
    detector.detect_breaks(tools_v1, model_id="anthropic.claude-sonnet-4-5")  # establish baseline
    tools_v2 = [{"name": "x", "description": "y", "input_schema": {"v": 2}}]  # schema changed

    # Sonnet sees the break.
    breaks_sonnet = detector.detect_breaks(tools_v2, model_id="anthropic.claude-sonnet-4-5")
    assert "x" in breaks_sonnet

    # Reset baseline + check Haiku gets [] regardless.
    detector2 = PerToolCacheBreakDetector()
    detector2.detect_breaks(tools_v1, model_id="anthropic.claude-haiku-4-5-20251001-v1:0")
    breaks_haiku = detector2.detect_breaks(
        tools_v2, model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
    )
    assert breaks_haiku == [], "Haiku must be excluded from cache-break detection"


# ============================================================
# TEST_DESIGN row 7 + 8 - daemon-call and heartbeat local locks
# ============================================================

def test_daemon_thread_bedrock_call_responds_to_ctrl_c():
    """Daemon helper returns promptly on stale local call; no AWS required."""
    from runtime.bedrock_client import run_bedrock_call_daemon

    start = time.monotonic()
    with pytest.raises(TimeoutError):
        run_bedrock_call_daemon(lambda: time.sleep(1), stale_deadline_s=0.05)
    assert time.monotonic() - start < 0.5


def test_30s_heartbeat_during_long_call():
    """Heartbeat path is tested with a short interval instead of 30s wall time."""
    from runtime.bedrock_client import run_bedrock_call_daemon

    beats = []
    assert run_bedrock_call_daemon(
        lambda: (time.sleep(0.05), "done")[1],
        stale_deadline_s=1.0,
        heartbeat_callback=lambda: beats.append(True),
        heartbeat_interval_s=0.01,
    ) == "done"
    assert beats


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
        assert cat == expected_cat, f"{exc!r} â†’ got {cat}, expected {expected_cat}"
        assert recovery == expected_recovery


def test_hash_tool_schema_deterministic():
    """Same schema content â†’ same hash regardless of key order."""
    from core import hash_tool_schema

    a = {"name": "x", "input_schema": {"type": "object", "properties": {"a": {"type": "string"}}}}
    b = {"input_schema": {"properties": {"a": {"type": "string"}}, "type": "object"}, "name": "x"}
    assert hash_tool_schema(a) == hash_tool_schema(b)
    # Different content â†’ different hash.
    c = {"name": "x", "input_schema": {"type": "string"}}
    assert hash_tool_schema(a) != hash_tool_schema(c)


# ============================================================
# Codex iter-1 finding-lock tests
# ============================================================

def test_get_retry_after_ms_parses_http_date():
    """Codex iter-1 finding #1 lock: get_retry_after_ms must parse the
    HTTP-date format used in Retry-After headers (case-insensitive
    header matching).
    """
    import time
    from email.utils import format_datetime
    from datetime import datetime, timezone, timedelta
    from core import get_retry_after_ms

    # Future date: ~10 seconds from now.
    future = datetime.now(timezone.utc) + timedelta(seconds=10)
    http_date = format_datetime(future)  # produces "Wed, ... GMT"

    out = get_retry_after_ms(f"HTTP 429: Retry-After: {http_date}")
    # Should return ~10000ms (allow some slack).
    assert 5000 <= out <= 15000, (
        f"HTTP-date Retry-After parsing failed; got {out}ms, "
        f"expected ~10000ms (Codex iter-1 #1)"
    )

    # Lower-case header name still works (RFC says case-insensitive).
    out_lower = get_retry_after_ms(f"retry-after: {http_date}")
    assert 5000 <= out_lower <= 15000


def test_extract_nested_error_message_extracts_nested_api_json():
    """Codex iter-1 finding #2 lock: extract_nested_error_message must
    walk nested .error.message and .error.error.message JSON paths
    (the shape Bedrock + Anthropic API actually return).
    """
    import json as _json
    from core import extract_nested_error_message

    # Single-nested .error.message.
    body1 = _json.dumps(
        {"error": {"message": "AccessDenied: principal lacks permission"}}
    )
    out1 = extract_nested_error_message(body1)
    assert "AccessDenied" in out1, (
        f"single-nested .error.message must be extracted; got {out1!r}"
    )

    # Double-nested .error.error.message.
    body2 = _json.dumps(
        {"error": {"error": {"message": "ThrottlingException: rate exceeded"}}}
    )
    out2 = extract_nested_error_message(body2)
    assert "ThrottlingException" in out2, (
        f"double-nested .error.error.message must be extracted; got {out2!r}"
    )


def test_classifier_recognizes_common_timeout_shapes():
    """Codex iter-1 finding #3 lock: classifier must catch common
    timeout exception shapes (ReadTimeout, ConnectTimeout,
    APIConnectionTimeoutError, "request timed out").
    """
    from core import BedrockErrorCategory, ErrorClassifier

    # Class-name shapes (cls_name match).
    class ReadTimeout(Exception):
        pass

    class ConnectTimeout(Exception):
        pass

    class APIConnectionTimeoutError(Exception):
        pass

    cases = [
        ReadTimeout("read timed out"),
        ConnectTimeout("connect timed out"),
        APIConnectionTimeoutError("connection timeout"),
        Exception("Request timed out after 30s"),
    ]
    for exc in cases:
        cat, recovery, _ = ErrorClassifier.classify(exc)
        assert cat == BedrockErrorCategory.REQUEST_TIMEOUT, (
            f"{type(exc).__name__}({exc!r}) â†’ got {cat}, "
            f"expected REQUEST_TIMEOUT (Codex iter-1 #3)"
        )
        assert recovery == "backoff"


def test_notify_cache_deletion_skips_excluded_models():
    """notify_cache_deletion returns False for Haiku (R4 #14 MUST)."""
    from core import notify_cache_deletion

    assert notify_cache_deletion(
        "anthropic.claude-haiku-4-5-20251001-v1:0", ["read_file"]
    ) is False
    assert notify_cache_deletion(
        "anthropic.claude-sonnet-4-5", ["read_file"]
    ) is True


def test_l1_prompt_too_long_gap_drops_multiple_groups():
    from core import drop_prompt_too_long_message_groups, get_prompt_too_long_token_gap

    gap = get_prompt_too_long_token_gap("ValidationException: 205000 tokens exceeds 200000")
    assert gap == 5000

    groups = [{"id": 1, "tokens": 2000}, {"id": 2, "tokens": 3500}, {"id": 3, "tokens": 1000}]
    remaining = drop_prompt_too_long_message_groups(
        groups,
        gap,
        estimate_tokens=lambda g: g["tokens"],
    )
    assert [g["id"] for g in remaining] == [3]


def test_l3_rate_limit_unified_reset_unix_seconds():
    from core import get_rate_limit_reset_delay_ms

    future = time.time() + 10
    out = get_rate_limit_reset_delay_ms(
        f"anthropic-ratelimit-unified-reset: {future:.3f}"
    )
    assert 5_000 <= out <= 15_000


def test_l4_529_query_source_retry_vs_drop():
    from core import is_529_error, should_retry_529

    assert is_529_error("HTTP 529 overloaded") is True
    assert should_retry_529("user", attempt=0) is True
    assert should_retry_529("user", attempt=3) is False
    assert should_retry_529("compact", attempt=0) is False


def test_l5_opus_529_fallback_to_sonnet_after_three():
    from core import fallback_model_for_529

    opus = "au.anthropic.claude-opus-4-1-20250805-v1:0"
    assert fallback_model_for_529(opus, 2) == ""
    assert fallback_model_for_529(opus, 3) == "au.anthropic.claude-sonnet-4-1-20250805-v1:0"
    assert fallback_model_for_529("anthropic.claude-sonnet-4-5", 3) == ""


def test_l6_keepalive_disabled_on_rebuild_marker():
    from runtime.bedrock_client import BedrockClient, _bedrock_client_config

    cfg = _bedrock_client_config(disable_keepalive=True)
    assert cfg.retries["max_attempts"] == 1
    # botocore exposes tcp_keepalive through the config object's kwargs-backed
    # attribute on current runtimes. Older runtimes fall back without failing.
    if hasattr(cfg, "tcp_keepalive"):
        assert cfg.tcp_keepalive is False

    client = BedrockClient("x", "us-east-1", mock_mode=True)
    assert client._rebuild_bedrock_client(disable_keepalive=True) is False
    assert client._last_rebuild_disable_keepalive is True


def test_l7_persistent_retry_mode_env_gated(monkeypatch):
    from core import RetryPolicy

    monkeypatch.delenv("SAGEMAKER_UNATTENDED_RETRY", raising=False)
    assert RetryPolicy.persistent_retry_enabled() is False
    assert RetryPolicy.max_retries() == RetryPolicy.MAX_RETRIES
    monkeypatch.setenv("SAGEMAKER_UNATTENDED_RETRY", "1")
    assert RetryPolicy.persistent_retry_enabled() is True
    assert RetryPolicy.max_retries() == RetryPolicy.PERSISTENT_MAX_RETRIES


def test_l8_connection_error_details_ssl_hint():
    from core import extract_connection_error_details

    out = extract_connection_error_details("SSL certificate verify failed behind Zscaler")
    assert out["kind"] == "ssl"
    assert "Zscaler" in out["hint"]


def test_l9_sanitize_api_error_nested_json_and_html():
    from core import sanitize_api_error

    assert sanitize_api_error('{"error":{"error":{"message":"nested message"}}}') == "nested message"
    assert "Service Unavailable" in sanitize_api_error("<html><title>Service Unavailable</title></html>")


def test_l10_prompt_state_snapshot_has_eight_bedrock_fields():
    from dataclasses import fields
    from core import PromptStateSnapshot

    names = [f.name for f in fields(PromptStateSnapshot)]
    assert names == [
        "system_hash",
        "tools_hash",
        "per_tool_hashes",
        "cache_control_hash",
        "model_id",
        "thinking_enabled",
        "thinking_budget",
        "cache_ttl",
    ]


def test_l11_lru_tracks_max_ten_sources():
    from core import MAX_TRACKED_SOURCES, PerToolCacheBreakDetector, PromptStateSnapshot

    detector = PerToolCacheBreakDetector()
    snap = PromptStateSnapshot(system_hash="s", tools_hash="t")
    for idx in range(MAX_TRACKED_SOURCES + 2):
        detector.record_source_snapshot(f"src-{idx}", snap)
    assert len(detector.tracked_sources()) == MAX_TRACKED_SOURCES
    assert detector.tracked_sources()[0] == "src-2"


def test_l12_min_cache_miss_tokens_constant():
    from core import MIN_CACHE_MISS_TOKENS

    assert MIN_CACHE_MISS_TOKENS == 2_000


def test_l13_ttl_expiry_classification():
    from core import PromptStateSnapshot, classify_ttl_expiry

    snap = PromptStateSnapshot(system_hash="s", tools_hash="t", cache_ttl="5m")
    assert classify_ttl_expiry(snap, age_ms=301_000) == "ttl_expired"
    assert classify_ttl_expiry(snap, age_ms=60_000) == "not_ttl_expired"
    assert classify_ttl_expiry(PromptStateSnapshot("s", "t", cache_ttl="server"), None) == "server_side_or_unknown"


def test_l15_write_cache_break_diff(tmp_path):
    import json
    from core import PromptStateSnapshot, write_cache_break_diff

    before = PromptStateSnapshot(system_hash="s1", tools_hash="t")
    after = PromptStateSnapshot(system_hash="s2", tools_hash="t")
    path = tmp_path / "cache_diff.json"
    write_cache_break_diff(str(path), before, after)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["changed"]["system_hash"] == {"before": "s1", "after": "s2"}


def test_l16_strip_cache_control_and_cache_control_hash():
    from core import cache_control_hash, strip_cache_control

    value = [{"type": "text", "text": "x", "cache_control": {"type": "ephemeral", "ttl": "5m"}}]
    stripped = strip_cache_control(value)
    assert "cache_control" not in stripped[0]
    assert cache_control_hash(value) != cache_control_hash(stripped)


def test_l17_bedrock_api_error_humanizer():
    from core import humanize_api_error

    out = humanize_api_error('{"message":"denied"}', status_code=403)
    assert out == "Bedrock API error 403: denied"


def test_l18_rollback_to_last_assistant_turn():
    from core import rollback_to_last_assistant_turn

    messages = [
        {"role": "user", "content": "a"},
        {"role": "assistant", "content": "b"},
        {"role": "user", "content": "c"},
    ]
    assert rollback_to_last_assistant_turn(messages) == messages[:2]


def test_l19_one_extra_primary_recovery_after_max(monkeypatch):
    from core import RetryPolicy

    monkeypatch.delenv("SAGEMAKER_UNATTENDED_RETRY", raising=False)
    assert RetryPolicy.allow_primary_recovery_after_max(RetryPolicy.MAX_RETRIES, "backoff") is True
    assert RetryPolicy.allow_primary_recovery_after_max(RetryPolicy.MAX_RETRIES + 1, "backoff") is False


def test_l20_three_tier_recovery_ladder():
    from core import BedrockErrorCategory, RetryPolicy

    assert RetryPolicy.three_tier_recovery_ladder(BedrockErrorCategory.NETWORK) == [
        "retry_with_backoff",
        "refresh_iam_token_or_client",
        "surface_user_error",
    ]
    assert RetryPolicy.three_tier_recovery_ladder(BedrockErrorCategory.ACCESS_DENIED) == [
        "surface_user_error"
    ]


def test_l21_daemon_thread_call_times_out_without_blocking():
    from runtime.bedrock_client import run_bedrock_call_daemon

    start = time.monotonic()
    with pytest.raises(TimeoutError):
        run_bedrock_call_daemon(
            lambda: time.sleep(1),
            stale_deadline_s=0.05,
            heartbeat_interval_s=0.01,
        )
    assert time.monotonic() - start < 0.5


def test_l22_context_scaled_deadline():
    from runtime.bedrock_client import context_scaled_deadline_seconds

    assert context_scaled_deadline_seconds(0, base_seconds=120) == 120
    assert context_scaled_deadline_seconds(200_000, base_seconds=120) > 120


def test_l23_heartbeat_callback_during_long_call():
    from runtime.bedrock_client import run_bedrock_call_daemon

    beats = []
    result = run_bedrock_call_daemon(
        lambda: (time.sleep(0.08), "ok")[1],
        stale_deadline_s=1.0,
        heartbeat_callback=lambda: beats.append(time.monotonic()),
        heartbeat_interval_s=0.01,
    )
    assert result == "ok"
    assert beats


def test_l24_bedrock_client_rebuild_branch_for_injected_client():
    from runtime.bedrock_client import BedrockClient

    fake = object()
    client = BedrockClient("x", "us-east-1", mock_mode=False, client=fake)
    assert client._rebuild_bedrock_client(disable_keepalive=True) is False
    assert client.client is fake
    assert client._last_rebuild_disable_keepalive is True


def test_l25_invalidate_runtime_client_region():
    import runtime.bedrock_client as bc

    bc._RUNTIME_CLIENT_CACHE["us-east-1|keepalive=on"] = object()
    assert bc.invalidate_runtime_client("us-east-1") is True
    assert bc.invalidate_runtime_client("missing") is False


def test_l26_error_utility_helpers():
    from core import classify_axios_error, is_fs_inaccessible, short_error_stack, to_error

    assert isinstance(to_error("boom"), Exception)
    assert is_fs_inaccessible("ENOENT: no such file or directory") is True
    assert classify_axios_error("SSL certificate verify failed") == "ssl"
    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        assert "RuntimeError: boom" in short_error_stack(exc, max_frames=2)


def test_l27_structured_error_classes():
    from core import ConfigParseError, ShellError, TelemetrySafeError

    shell = ShellError("failed", stdout="out", stderr="err", code=2)
    assert shell.stdout == "out"
    assert shell.stderr == "err"
    assert shell.code == 2
    cfg = ConfigParseError("bad", path="agent_config.json", default={"x": 1})
    assert cfg.path == "agent_config.json"
    assert cfg.default == {"x": 1}
    telemetry = TelemetrySafeError("safe", telemetry={"kind": "timeout"})
    assert telemetry.telemetry == {"kind": "timeout"}


def test_l28_bedrock_guardrails_config_wired(monkeypatch):
    import runtime.config as runtime_config
    from runtime.bedrock_client import BedrockClient

    class FakeBody:
        def read(self):
            return b'{"content":[{"type":"text","text":"ok"}],"stop_reason":"end_turn","usage":{}}'

    class FakeClient:
        def __init__(self):
            self.kwargs = None

        def invoke_model(self, **kwargs):
            self.kwargs = kwargs
            return {"body": FakeBody()}

    fake = FakeClient()
    monkeypatch.setattr(runtime_config.CONFIG, "enable_prompt_cache", False)
    monkeypatch.setattr(runtime_config.CONFIG, "bedrock_guardrail_identifier", "gr-123")
    monkeypatch.setattr(runtime_config.CONFIG, "bedrock_guardrail_version", "1")
    monkeypatch.setattr(runtime_config.CONFIG, "bedrock_guardrail_trace", "ENABLED")

    client = BedrockClient("model", "us-east-1", mock_mode=False, client=fake)
    response = client.chat([{"role": "user", "content": "hi"}], system="sys")
    assert response.text == "ok"
    assert fake.kwargs["guardrailIdentifier"] == "gr-123"
    assert fake.kwargs["guardrailVersion"] == "1"
    assert fake.kwargs["trace"] == "ENABLED"
