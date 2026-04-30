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

import random


class RetryPolicy:
    """Jittered exponential backoff (v4 verbatim)."""
    MAX_RETRIES = 4
    BASE_SECONDS = 1.0
    JITTER_FRACTION = 0.30
    BACKOFF_RECOVERY = {"backoff"}

    @staticmethod
    def should_retry(attempt: int, recovery: str) -> bool:
        if attempt >= RetryPolicy.MAX_RETRIES:
            return False
        return recovery in RetryPolicy.BACKOFF_RECOVERY

    @staticmethod
    def backoff_seconds(attempt: int) -> float:
        base = RetryPolicy.BASE_SECONDS * (2 ** attempt)
        jitter = base * RetryPolicy.JITTER_FRACTION * (2 * random.random() - 1)
        return max(0.1, base + jitter)
