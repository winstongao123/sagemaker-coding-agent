"""V5 core/retry.py — jittered exponential backoff (Phase 8 extraction).

Per ADR-014: extracted verbatim from Phase-1 `runtime/bedrock_client.py`
(which itself is a verbatim port from `compact_v4/MAIN/agent/sagemaker_agent.py`).

PORT_LOG: #018.

Sleep curve:
  attempt 0 -> ~1.0s   (0.7-1.3s with jitter)
  attempt 1 -> ~2.0s   (1.4-2.6s)
  attempt 2 -> ~4.0s   (2.8-5.2s)
  attempt 3 -> ~8.0s   (5.6-10.4s)
  attempt 4 -> stops   (MAX_RETRIES reached)

MAX_RETRIES=4 means up to 5 total attempts (initial + 4 retries).
Behavior is byte-equivalent with Phase-1. `runtime/bedrock_client.py`
re-imports these names for backwards compatibility.
"""
from __future__ import annotations

import os
import random


class RetryPolicy:
    """Jittered exponential backoff (v4 verbatim)."""
    MAX_RETRIES = 4
    BASE_SECONDS = 1.0
    JITTER_FRACTION = 0.30
    BACKOFF_RECOVERY = {"backoff"}
    PERSISTENT_MAX_RETRIES = 12

    @staticmethod
    def persistent_retry_enabled() -> bool:
        """Block L: opt-in unattended retry mode for SageMaker idle sessions."""
        return os.environ.get("SAGEMAKER_UNATTENDED_RETRY", "").strip() == "1"

    @staticmethod
    def max_retries() -> int:
        """Return the active retry ceiling, honoring the env-gated persistent mode."""
        if RetryPolicy.persistent_retry_enabled():
            return RetryPolicy.PERSISTENT_MAX_RETRIES
        return RetryPolicy.MAX_RETRIES

    @staticmethod
    def should_retry(attempt: int, recovery: str, max_retries: int | None = None) -> bool:
        ceiling = RetryPolicy.max_retries() if max_retries is None else max_retries
        if attempt >= ceiling:
            return False
        return recovery in RetryPolicy.BACKOFF_RECOVERY

    @staticmethod
    def allow_primary_recovery_after_max(attempt: int, recovery: str) -> bool:
        """Allow one final primary-channel recovery after the nominal retry cap."""
        return attempt == RetryPolicy.max_retries() and recovery in {
            "backoff",
            "compact_retry",
            "strip_cache_retry",
        }

    @staticmethod
    def three_tier_recovery_ladder(category: str) -> list[str]:
        """Bedrock-adapted recovery ladder: retry, refresh auth/client, user error."""
        from core.errors import BedrockErrorCategory

        if category in {
            BedrockErrorCategory.THROTTLE,
            BedrockErrorCategory.SERVICE_UNAVAILABLE,
            BedrockErrorCategory.MODEL_NOT_READY,
            BedrockErrorCategory.NETWORK,
            BedrockErrorCategory.REQUEST_TIMEOUT,
            BedrockErrorCategory.GATEWAY_TIMEOUT,
            BedrockErrorCategory.DEPENDENCY_FAILURE,
        }:
            return ["retry_with_backoff", "refresh_iam_token_or_client", "surface_user_error"]
        if category in {
            BedrockErrorCategory.CONTEXT_OVERFLOW,
            BedrockErrorCategory.MAX_TOKENS_OVERFLOW,
            BedrockErrorCategory.PAYLOAD_TOO_LARGE,
        }:
            return ["compact_and_retry", "primary_recovery_once", "surface_user_error"]
        if category == BedrockErrorCategory.VALIDATION_CACHE:
            return ["strip_cache_control", "retry_without_cache", "surface_user_error"]
        return ["surface_user_error"]

    @staticmethod
    def backoff_seconds(attempt: int) -> float:
        base = RetryPolicy.BASE_SECONDS * (2 ** attempt)
        jitter = base * RetryPolicy.JITTER_FRACTION * (2 * random.random() - 1)
        return max(0.1, base + jitter)
