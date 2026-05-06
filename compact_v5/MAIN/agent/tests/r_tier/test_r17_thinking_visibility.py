"""R-tier R17 - Thinking visibility (PS#4 fix on real Bedrock).

Per PS_V5_TEST_PLAYBOOK.md section 4.5 Gap B:
  Send a hard-reasoning prompt with extended thinking enabled. Verify
  the agent's thinking block is captured in chat history and visible in
  telemetry JSON per_turn[].thinking_text.

Cost cap: $0.30 planned / $0.36 hard retry ceiling. Model: Sonnet 4.5 AU.
R17 intentionally uses Sonnet because the scenario measures extended-thinking
visibility, and Sonnet is the matrix model for this row.

Real-AWS gated: skipped without RUN_REAL_BEDROCK=1.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import pytest


_AGENT_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))


_SONNET_45_AU = "au.anthropic.claude-sonnet-4-5-20250929-v1:0"
_R17_COST_CAP_USD = 0.30
_USER_APPROVED_RETRY_BUFFER_MULTIPLIER = 1.20
_R17_HARD_CEILING_USD = _R17_COST_CAP_USD * _USER_APPROVED_RETRY_BUFFER_MULTIPLIER
_R17_THINKING_BUDGET = 4096

_R17_PROMPT = (
    "Carefully think through this 2-step problem and give the final answer:\n\n"
    "A train leaves Sydney at 09:00 traveling at 80 km/h. A second train "
    "leaves Melbourne (900 km away) at 11:00 traveling at 100 km/h toward "
    "Sydney. At what time and how far from Sydney do they meet? "
    "Show your reasoning concisely; final answer in one line."
)


def _audit_events(audit_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for fp in sorted(audit_dir.glob("*.jsonl")):
        for line in fp.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def _chat_response_thinking(events: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for ev in events:
        if ev.get("action") != "chat_response":
            continue
        params = ev.get("parameters") if isinstance(ev.get("parameters"), dict) else {}
        response = params.get("response") if isinstance(params.get("response"), dict) else {}
        thinking = str(response.get("thinking") or "")
        if thinking:
            chunks.append(thinking)
    return "".join(chunks)


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R17 is real-AWS gated.",
)
def test_r17_thinking_visibility(tmp_path):
    """R17 passes when thinking is present in history and audit telemetry source."""
    from agent import Agent
    from runtime.audit import AUDIT
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr

    call = int(os.getenv("R_TIER_CALL", "1"))
    audit_dir = _REPO_ROOT / "compact_v5" / "_status" / "r_tier_runtime" / f"R17-call{call}-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    side_metrics = _REPO_ROOT / "compact_v5" / "_status" / f"r-tier-R17-aws-call{call}-side-metrics.json"

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_thinking = getattr(CONFIG, "thinking_enabled", None)
    saved_thinking_budget = getattr(CONFIG, "thinking_budget", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_audit_dir = getattr(CONFIG, "audit_dir", None)
    saved_disable_traces = getattr(CONFIG, "disable_local_traces", None)
    cwd_before = os.getcwd()
    try:
        CONFIG.workspace = str(tmp_path)
        CONFIG.audit_dir = str(audit_dir)
        CONFIG.session_cost_limit = _R17_HARD_CEILING_USD
        CONFIG.model_id = _SONNET_45_AU
        # Bedrock requires max_tokens to be greater than thinking.budget_tokens.
        CONFIG.max_tokens = 8192
        CONFIG.thinking_enabled = True
        CONFIG.thinking_budget = _R17_THINKING_BUDGET
        CONFIG.require_tool_approval = False
        CONFIG.disable_local_traces = False
        sec_mgr.rebuild_singleton_for_tests()
        AUDIT.__init__(audit_dir=str(audit_dir))
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_SONNET_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt() -> bool:
            if hasattr(TOKENS, "is_over_budget"):
                return TOKENS.is_over_budget()
            return TOKENS.session_cost >= _R17_HARD_CEILING_USD

        t0 = time.time()
        agent = Agent(
            client=client,
            max_turns=8,
            thinking_enabled=True,
            thinking_budget=_R17_THINKING_BUDGET,
            on_stop_check=_hard_cost_halt,
        )
        result = agent.run(_R17_PROMPT, tools=[])
        wallclock_s = time.time() - t0

        thinking_seen = False
        thinking_chars = 0
        for msg in agent.messages:
            if msg.get("role") != "assistant":
                continue
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "thinking":
                    text = str(block.get("thinking") or "")
                    if text:
                        thinking_seen = True
                        thinking_chars += len(text)

        events = _audit_events(audit_dir)
        audit_thinking_text = _chat_response_thinking(events)
        audit_thinking_seen = bool(audit_thinking_text)
        audit_thinking_chars = len(audit_thinking_text)
        cost_used = float(TOKENS.session_cost)
        completed = bool(
            result.stop_reason != "max_turns"
            and thinking_seen
            and audit_thinking_seen
            and thinking_chars > 50
            and audit_thinking_chars > 50
            and cost_used <= _R17_HARD_CEILING_USD
        )

        metrics = {
            "test": "R17",
            "call": call,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _SONNET_45_AU,
            "tokens_in": int(TOKENS.session_input),
            "tokens_out": int(TOKENS.session_output),
            "cache_hit_pct": 0.0,
            "wallclock_s": round(wallclock_s, 2),
            "tool_calls": 0,
            "api_calls": int(TOKENS.api_calls),
            "subagent_calls": 0,
            "reviewer_calls": 0,
            "subagent_tokens_in": 0,
            "subagent_tokens_out": 0,
            "subagent_cost_usd": 0.0,
            "reviewer_tokens_in": 0,
            "reviewer_tokens_out": 0,
            "reviewer_cost_usd": 0.0,
            "cost_usd": round(cost_used, 4),
            "cost_cap_usd": _R17_COST_CAP_USD,
            "hard_ceiling_usd": _R17_HARD_CEILING_USD,
            "stop_reason": result.stop_reason,
            "thinking_seen": thinking_seen,
            "thinking_chars": thinking_chars,
            "max_tokens": CONFIG.max_tokens,
            "thinking_budget": _R17_THINKING_BUDGET,
            "audit_thinking_seen": audit_thinking_seen,
            "audit_thinking_chars": audit_thinking_chars,
            "thinking_text_in_history": thinking_seen,
            "thinking_text_in_telemetry_source": audit_thinking_seen,
            "process_quality_ok": completed,
            "completed": completed,
            "verdict": "GENUINE_PASS" if completed else "FAIL",
            "audit_dir": str(audit_dir),
            "final_text": (result.text or "")[:500],
        }
        stats = TOKENS.get_stats() if hasattr(TOKENS, "get_stats") else {}
        if isinstance(stats, dict):
            metrics.update({
                "parent_input_tokens": stats.get("parent_input_tokens", 0),
                "parent_output_tokens": stats.get("parent_output_tokens", 0),
                "parent_cache_read_tokens": stats.get("parent_cache_read_tokens", 0),
                "parent_cache_write_tokens": stats.get("parent_cache_write_tokens", 0),
                "parent_cost_usd": stats.get("parent_cost_usd", 0.0),
                "subagent_input_tokens": stats.get("subagent_input_tokens", {}),
                "subagent_output_tokens": stats.get("subagent_output_tokens", {}),
                "subagent_cache_read_tokens": stats.get("subagent_cache_read_tokens", {}),
                "subagent_cache_write_tokens": stats.get("subagent_cache_write_tokens", {}),
                "subagent_cost_usd_by_type": stats.get("subagent_cost_usd", {}),
            })
        side_metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"\n[R17_AUDIT_DIR] {audit_dir}")
        print(f"[R17_SIDE_METRICS] {side_metrics}")
        print(f"[R17_METRICS] {json.dumps(metrics, sort_keys=True)}")

        assert result.stop_reason != "max_turns", (
            f"R17 hit max_turns; thinking did not converge. metrics={metrics}"
        )
        assert thinking_seen, (
            "R17 expected at least one assistant thinking block in history. "
            f"metrics={metrics}"
        )
        assert thinking_chars > 50, (
            f"R17 thinking blocks too short ({thinking_chars} chars). metrics={metrics}"
        )
        assert audit_thinking_seen and audit_thinking_chars > 50, (
            "R17 expected thinking text in chat_response audit evidence. "
            f"metrics={metrics}"
        )
        assert cost_used <= _R17_HARD_CEILING_USD, (
            f"R17 cost ${cost_used:.4f} exceeded cap ${_R17_COST_CAP_USD:.2f} "
            f"plus 20% retry buffer (${_R17_HARD_CEILING_USD:.2f}). metrics={metrics}"
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
        if saved_audit_dir is not None:
            CONFIG.audit_dir = saved_audit_dir
        if saved_disable_traces is not None:
            CONFIG.disable_local_traces = saved_disable_traces
