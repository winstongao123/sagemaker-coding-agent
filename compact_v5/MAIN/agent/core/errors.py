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


class BedrockErrorCategory:
    """Categories of Bedrock invoke errors. Used by ErrorClassifier + RetryPolicy."""
    THROTTLE = "throttle"  # ThrottlingException, rate-limited
    SERVICE_UNAVAILABLE = "service_unavailable"
    MODEL_NOT_READY = "model_not_ready"
    NETWORK = "network"
    VALIDATION_CACHE = "validation_cache"  # cache_control rejected — strip and retry once
    VALIDATION_OTHER = "validation_other"
    CONTEXT_OVERFLOW = "context_overflow"  # prompt-too-long
    ACCESS_DENIED = "access_denied"
    UNKNOWN = "unknown"


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
