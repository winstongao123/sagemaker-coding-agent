"""Phase 08 unit tests: core/retry.py — RetryPolicy.

Locks PORT_LOG #018: jittered exponential backoff with v4 verbatim semantics.
"""
from __future__ import annotations

import os
import random
import sys

_AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def test_max_retries_is_4():
    from core.retry import RetryPolicy
    assert RetryPolicy.MAX_RETRIES == 4


def test_should_retry_for_backoff_recovery():
    from core.retry import RetryPolicy
    assert RetryPolicy.should_retry(0, "backoff") is True
    assert RetryPolicy.should_retry(3, "backoff") is True


def test_should_not_retry_when_attempts_exhausted():
    from core.retry import RetryPolicy
    assert RetryPolicy.should_retry(4, "backoff") is False
    assert RetryPolicy.should_retry(99, "backoff") is False


def test_should_not_retry_for_non_backoff_recovery():
    from core.retry import RetryPolicy
    assert RetryPolicy.should_retry(0, "no_retry") is False
    assert RetryPolicy.should_retry(0, "strip_cache_retry") is False
    assert RetryPolicy.should_retry(0, "compact_retry") is False


def test_backoff_seconds_floor_and_ceiling():
    """Sleep curve: ~1s, 2s, 4s, 8s with up-to-30% jitter. Always >= 0.1s."""
    from core.retry import RetryPolicy
    random.seed(42)
    samples = [RetryPolicy.backoff_seconds(0) for _ in range(50)]
    for s in samples:
        assert s >= 0.1
        # base=1.0, jitter +/- 0.30 → [0.7, 1.3]
        assert 0.7 <= s <= 1.3 + 0.0001


def test_backoff_seconds_doubles_per_attempt():
    from core.retry import RetryPolicy
    random.seed(0)
    base_means = []
    for attempt in range(4):
        random.seed(attempt)
        samples = [RetryPolicy.backoff_seconds(attempt) for _ in range(200)]
        base_means.append(sum(samples) / len(samples))
    # Mean roughly doubles (within jitter): ~1, ~2, ~4, ~8
    for prev, cur in zip(base_means, base_means[1:]):
        assert cur > prev * 1.5, f"expected ~doubling, got {prev:.2f} -> {cur:.2f}"


def test_runtime_bedrock_client_re_exports_match():
    """Byte-equivalence with Phase-1: runtime.bedrock_client re-exports
    the same RetryPolicy class so existing call-sites continue to work."""
    from core.retry import RetryPolicy as CorePolicy
    from runtime.bedrock_client import RetryPolicy as RuntimePolicy
    assert CorePolicy is RuntimePolicy
