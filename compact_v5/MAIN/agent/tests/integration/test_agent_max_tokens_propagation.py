"""Lock test for R-tier R1 PHASE A iter-2 fix: Agent.run must propagate
CONFIG.max_tokens + CONFIG.temperature into the QueryEngine.run call,
which then forwards into BedrockClient.chat.

Without this, R-tier tests overriding CONFIG.max_tokens (to cap per-turn
output cost) would have no effect because QueryEngine.run defaults to
max_tokens=4096.

This is a mock-based lock test ($0); no AWS spend.
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


def test_agent_run_propagates_config_max_tokens():
    """Agent.run reads CONFIG.max_tokens at call time and forwards it
    into the BedrockClient.chat invocation. Verified via spy on a mock
    client that captures every chat() kwargs dict."""
    from runtime.config import CONFIG
    from agent import Agent

    captured: dict = {"max_tokens": None, "temperature": None, "calls": 0}

    class _SpyClient:
        model_id = "spy"

        def chat(self, messages, system, tools=None, max_tokens=4096,
                 temperature=0.0, thinking_enabled=False, thinking_budget=4096):
            captured["max_tokens"] = max_tokens
            captured["temperature"] = temperature
            captured["calls"] += 1
            # Return a minimal end_turn response shape so QueryEngine
            # exits cleanly after one call.
            from runtime.bedrock_client import Response
            return Response(
                text="ok",
                tool_calls=[],
                stop_reason="end_turn",
                usage={"input_tokens": 10, "output_tokens": 5},
            )

    saved_max = getattr(CONFIG, "max_tokens", 4096)
    saved_temp = getattr(CONFIG, "temperature", 0.0)
    try:
        CONFIG.max_tokens = 2048
        CONFIG.temperature = 0.0
        agent = Agent(client=_SpyClient(), max_turns=1)
        agent.run("hi", tools=[])
        assert captured["calls"] >= 1, "spy client never called"
        assert captured["max_tokens"] == 2048, (
            f"Agent.run did not propagate CONFIG.max_tokens=2048 — "
            f"BedrockClient.chat received max_tokens={captured['max_tokens']}"
        )
        assert captured["temperature"] == 0.0
    finally:
        CONFIG.max_tokens = saved_max
        CONFIG.temperature = saved_temp


def test_agent_run_default_when_config_max_tokens_unset():
    """If CONFIG.max_tokens is missing/falsy, fall back to QueryEngine
    default (4096) — keeps the v4 baseline behavior."""
    from runtime.config import CONFIG
    from agent import Agent

    captured: dict = {"max_tokens": None}

    class _SpyClient:
        model_id = "spy"

        def chat(self, messages, system, tools=None, max_tokens=4096, **kw):
            captured["max_tokens"] = max_tokens
            from runtime.bedrock_client import Response
            return Response(text="ok", tool_calls=[], stop_reason="end_turn",
                            usage={"input_tokens": 1, "output_tokens": 1})

    saved_max = getattr(CONFIG, "max_tokens", 4096)
    try:
        # Unset to test fallback path.
        if hasattr(CONFIG, "max_tokens"):
            CONFIG.max_tokens = 4096  # explicit default
        agent = Agent(client=_SpyClient(), max_turns=1)
        agent.run("hi", tools=[])
        assert captured["max_tokens"] == 4096
    finally:
        CONFIG.max_tokens = saved_max
