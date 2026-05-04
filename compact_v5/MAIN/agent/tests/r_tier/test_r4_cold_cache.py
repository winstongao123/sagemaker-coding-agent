"""R-tier R4 - 30-minute idle cold-cache microcompact.

Validates PS#3 / Block A A-16 on real Bedrock end to end:
send a first turn, wait long enough for the prompt cache to be cold, then
send the next turn and verify the pre-call microcompact fires.

Real-AWS gated: skipped unless RUN_REAL_BEDROCK=1 and RUN_R4_IDLE_WAIT=1.
The local Block A proof is tests/integration/test_block_a.py:
test_cold_cache_30min_idle_triggers_microcompact.
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


@pytest.mark.skipif(
    not (os.getenv("RUN_REAL_BEDROCK") and os.getenv("RUN_R4_IDLE_WAIT")),
    reason="R4 is real-AWS and wall-clock gated; requires explicit user approval.",
)
def test_r4_cold_cache_30min_idle_microcompact(monkeypatch):
    """R4: real idle gap triggers A-16 cold-cache microcompact before turn 2."""
    from agent import Agent
    from core.compactor import AUTO_COMPACT, Compactor
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS

    saved_model = CONFIG.model_id
    saved_mock = CONFIG.mock_mode
    saved_threshold = getattr(CONFIG, "cold_cache_threshold_seconds", None)
    captured: list[str] = []
    try:
        CONFIG.mock_mode = False
        CONFIG.model_id = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
        CONFIG.cold_cache_threshold_seconds = Compactor.COLD_CACHE_THRESHOLD_SECONDS
        AUTO_COMPACT.reset()
        TOKENS.reset()
        agent = Agent(mock_mode=False)

        agent.run(
            "Read enough local context to make the next prompt non-trivial, then say ready.",
            output_fn=captured.append,
        )
        time.sleep(Compactor.COLD_CACHE_THRESHOLD_SECONDS + 5)
        agent.run("Continue with a one-sentence status.", output_fn=captured.append)

        assert any("[i] Cold cache detected" in line for line in captured)
        assert TOKENS.session_cost <= 0.20
    finally:
        CONFIG.model_id = saved_model
        CONFIG.mock_mode = saved_mock
        if saved_threshold is None:
            try:
                delattr(CONFIG, "cold_cache_threshold_seconds")
            except AttributeError:
                pass
        else:
            CONFIG.cold_cache_threshold_seconds = saved_threshold
