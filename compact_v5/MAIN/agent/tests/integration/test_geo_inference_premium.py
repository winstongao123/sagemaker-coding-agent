"""Lock test for R-tier R1 PHASE A iter-3 fix: cost tracker applies
+10% geo-inference premium for au./us./eu./apac. profiles.

Without this, AWS Bedrock geo profiles (the only supported invocation
path for Haiku 4.5) would undercount billed cost by 10% locally — letting
R-tier tests "pass cap locally" while exceeding it in real billing.

Mock-based ($0); no AWS spend.
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


def test_get_geo_multiplier_global_is_one():
    from runtime.tokens import get_geo_multiplier
    assert get_geo_multiplier("anthropic.claude-haiku-4-5-20251001-v1:0") == 1.0
    assert get_geo_multiplier("anthropic.claude-sonnet-4-5-20250929-v1:0") == 1.0
    assert get_geo_multiplier("") == 1.0
    assert get_geo_multiplier(None) == 1.0  # type: ignore[arg-type]


def test_get_geo_multiplier_geo_profiles_premium():
    from runtime.tokens import get_geo_multiplier, GEO_INFERENCE_PREMIUM
    assert GEO_INFERENCE_PREMIUM == 1.10
    for prefix in ("au.", "us.", "eu.", "apac."):
        mid = prefix + "anthropic.claude-haiku-4-5-20251001-v1:0"
        assert get_geo_multiplier(mid) == 1.10, (
            f"prefix {prefix} should incur +10% premium"
        )


def test_canonicalize_strips_geo_prefix():
    from runtime.tokens import canonicalize_model_id
    base = "anthropic.claude-haiku-4-5-20251001-v1:0"
    for prefix in ("au.", "us.", "eu.", "apac."):
        assert canonicalize_model_id(prefix + base) == base


def test_token_cost_applies_geo_premium_for_au_profile():
    """Cost charged for au.anthropic.claude-haiku is 1.10x the global rate."""
    from runtime.tokens import TokenTracker
    from runtime.config import CONFIG

    # Same call shape with two model IDs differing only by au. prefix.
    usage = {"input_tokens": 1000, "output_tokens": 1000}
    global_id = "anthropic.claude-haiku-4-5-20251001-v1:0"
    geo_id = "au.anthropic.claude-haiku-4-5-20251001-v1:0"

    saved_model = CONFIG.model_id
    try:
        # Global tracker.
        CONFIG.model_id = global_id
        t_global = TokenTracker(CONFIG)
        t_global.add(usage, model_id=global_id)
        cost_global = t_global.session_cost

        # Geo tracker — same usage; should be 1.10x cost.
        CONFIG.model_id = geo_id
        t_geo = TokenTracker(CONFIG)
        t_geo.add(usage, model_id=geo_id)
        cost_geo = t_geo.session_cost

        assert cost_global > 0, "global cost must be non-zero"
        assert cost_geo > 0, "geo cost must be non-zero"
        # Geo cost must be 1.10x global cost (+/- floating-point tolerance).
        ratio = cost_geo / cost_global
        assert 1.099 <= ratio <= 1.101, (
            f"expected ratio ~1.10; got {ratio:.6f} (global={cost_global}, geo={cost_geo})"
        )
    finally:
        CONFIG.model_id = saved_model


def test_token_cost_no_premium_for_global_profile():
    """Cost charged for plain anthropic.<...> is the base rate (no premium)."""
    from runtime.tokens import TokenTracker, MODEL_COSTS
    from runtime.config import CONFIG

    usage = {"input_tokens": 1000, "output_tokens": 1000}
    global_id = "anthropic.claude-haiku-4-5-20251001-v1:0"
    expected_input_cost = (1000 / 1000) * MODEL_COSTS[global_id]["input"]
    expected_output_cost = (1000 / 1000) * MODEL_COSTS[global_id]["output"]
    expected_total = expected_input_cost + expected_output_cost

    saved_model = CONFIG.model_id
    try:
        CONFIG.model_id = global_id
        t = TokenTracker(CONFIG)
        t.add(usage, model_id=global_id)
        # Allow tiny floating-point tolerance.
        assert abs(t.session_cost - expected_total) < 1e-9, (
            f"global cost expected {expected_total}, got {t.session_cost}"
        )
    finally:
        CONFIG.model_id = saved_model
