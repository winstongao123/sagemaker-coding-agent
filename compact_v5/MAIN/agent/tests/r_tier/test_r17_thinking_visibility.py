"""R-tier R17 — Thinking visibility (PS#4 fix on real Bedrock).

Per PS_V5_TEST_PLAYBOOK.md §4.5 Gap B:
  Send a hard-reasoning prompt with extended thinking enabled. Verify
  the agent's thinking block is captured + returned in chat history +
  visible in telemetry.json `per_turn[].thinking_text`.

Cost cap: $0.30. Model: Sonnet 4.5 AU (only Sonnet supports extended
thinking reliably).

Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


_SONNET_45_AU = "au.anthropic.claude-sonnet-4-5-20250929-v1:0"
_R17_COST_CAP_USD = 0.30
_R17_THINKING_BUDGET = 4096


# Hard-reasoning prompt — 2-step math the model is likely to think before
# answering. Designed to be answerable but worth thinking about.
_R17_PROMPT = (
    "Carefully think through this 2-step problem and give the final answer:\n\n"
    "A train leaves Sydney at 09:00 traveling at 80 km/h. A second train "
    "leaves Melbourne (900 km away) at 11:00 traveling at 100 km/h toward "
    "Sydney. At what time and how far from Sydney do they meet? "
    "Show your reasoning concisely; final answer in one line."
)


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R17 is real-AWS gated.",
)
def test_r17_thinking_visibility(tmp_path, monkeypatch):
    """R-tier R17 — extended thinking captured + visible in telemetry.

    PASS criteria:
      - Bedrock returns a thinking block (response.thinking is non-empty
        OR audit_log chat_response carries thinking).
      - Agent run completes (not max_turns).
      - Cost ≤ $0.30 cap.
      - Side-channel _r17_metrics.json records thinking_seen=True.
    """
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr
    from agent import Agent

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_thinking = getattr(CONFIG, "thinking_enabled", None)
    saved_thinking_budget = getattr(CONFIG, "thinking_budget", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    cwd_before = os.getcwd()
    try:
        CONFIG.workspace = str(tmp_path)
        CONFIG.session_cost_limit = _R17_COST_CAP_USD
        CONFIG.model_id = _SONNET_45_AU
        CONFIG.max_tokens = 2048
        CONFIG.thinking_enabled = True
        CONFIG.thinking_budget = _R17_THINKING_BUDGET
        # R-tier tests run un-attended; bypass interactive approvals.
        CONFIG.require_tool_approval = False
        sec_mgr.rebuild_singleton_for_tests()
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_SONNET_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt():
            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R17_COST_CAP_USD
            )

        agent = Agent(
            client=client,
            max_turns=8,
            thinking_enabled=True,
            thinking_budget=_R17_THINKING_BUDGET,
            on_stop_check=_hard_cost_halt,
        )
        # Pre-empt any ask_user (single-turn task; auto-respond if the
        # model invokes it).
        # Note: tools=[] keeps R17 to a pure reasoning loop — no tool use.
        t0 = time.time()
        result = agent.run(_R17_PROMPT, tools=[])
        wallclock_s = time.time() - t0

        # Inspect the chat history for thinking blocks.
        thinking_seen = False
        thinking_chars = 0
        for msg in agent.messages:
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content")
            if isinstance(content, list):
                for blk in content:
                    if isinstance(blk, dict) and blk.get("type") == "thinking":
                        t = blk.get("thinking") or ""
                        if t:
                            thinking_seen = True
                            thinking_chars += len(t)

        cost_used = TOKENS.session_cost
        tokens_in = TOKENS.session_input
        tokens_out = TOKENS.session_output
        api_calls = TOKENS.api_calls

        metrics = {
            "test": "R17",
            "call": 1,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _SONNET_45_AU,
            "tokens_in": int(tokens_in),
            "tokens_out": int(tokens_out),
            "wallclock_s": round(wallclock_s, 2),
            "tool_calls": int(getattr(result, "turns_used", 0)),
            "api_calls": int(api_calls),
            "cost_usd": round(cost_used, 4),
            "stop_reason": result.stop_reason,
            "thinking_seen": thinking_seen,
            "thinking_chars": thinking_chars,
            "final_text": (result.text or "")[:500],
        }
        (tmp_path / "_r17_metrics.json").write_text(
            json.dumps(metrics, indent=2), encoding="utf-8"
        )
        print(f"\n[R17 METRICS] {json.dumps(metrics)}")

        assert result.stop_reason != "max_turns", (
            f"R17 hit max_turns; thinking did not converge. metrics={metrics}"
        )
        assert thinking_seen, (
            "R17 expected at least one assistant thinking block — none captured. "
            f"This is the PS#4 lock failing on real Bedrock. metrics={metrics}"
        )
        assert thinking_chars > 50, (
            f"R17 thinking blocks too short ({thinking_chars} chars) — likely a stub. "
            f"metrics={metrics}"
        )
        assert cost_used <= _R17_COST_CAP_USD, (
            f"R17 cost ${cost_used:.4f} exceeded cap ${_R17_COST_CAP_USD}."
        )
    finally:
        os.chdir(cwd_before)
        CONFIG.workspace = saved_ws
        sec_mgr.SECURITY = saved_sec
        if saved_cost_limit is not None:
            CONFIG.session_cost_limit = saved_cost_limit
        if saved_model is not None:
            CONFIG.model_id = saved_model
        if saved_max_tokens is not None:
            CONFIG.max_tokens = saved_max_tokens
        if saved_thinking is not None:
            CONFIG.thinking_enabled = saved_thinking
        if saved_thinking_budget is not None:
            CONFIG.thinking_budget = saved_thinking_budget
        if saved_require_approval is not None:
            CONFIG.require_tool_approval = saved_require_approval
