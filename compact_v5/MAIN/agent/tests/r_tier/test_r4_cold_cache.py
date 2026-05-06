"""R-tier R4 - cold-cache time-based microcompact.

Validates PS#3 / Block A A-16 on real Bedrock end to end. The production path
is time-based, but the R-tier runner uses CONFIG.cold_cache_threshold_seconds
and QueryEngine._last_api_call_time to avoid a 30-minute wall-clock sleep while
still exercising the real pre-call microcompact code path.

Real-AWS gated: skipped unless RUN_REAL_BEDROCK=1.
Local lock coverage is in tests/integration/test_block_a.py and
tests/integration/test_software_compact_telemetry.py.
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


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_R4_COST_CAP_USD = 0.20
_USER_APPROVED_RETRY_BUFFER_MULTIPLIER = 1.20
_R4_HARD_CEILING_USD = _R4_COST_CAP_USD * _USER_APPROVED_RETRY_BUFFER_MULTIPLIER


def _tool_pair(tool_id: str, content: str) -> list[dict[str, Any]]:
    return [
        {
            "role": "assistant",
            "content": [{
                "type": "tool_use",
                "id": tool_id,
                "name": "read_file",
                "input": {"file_path": f"context_{tool_id}.md"},
            }],
            "is_meta": False,
        },
        {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": content,
            }],
            "is_meta": False,
        },
    ]


def _seed_cold_cache_history() -> list[dict[str, Any]]:
    payload = (
        "R4 cold-cache fixture payload. "
        "This simulates a large historical read_file result that should be "
        "microcompacted before the next API call after an idle cache gap. "
    ) * 350
    messages: list[dict[str, Any]] = [{"role": "user", "content": "Begin R4 seeded history.", "is_meta": False}]
    for idx in range(3):
        messages.extend(_tool_pair(f"r4-{idx}", payload + f"\nSECTION={idx}\n"))
    return messages


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


def _compact_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        ev for ev in events
        if str(ev.get("action", "")).startswith("compact_micro")
    ]


def _microcompact_applied(events: list[dict[str, Any]]) -> bool:
    for ev in _compact_events(events):
        if ev.get("action") != "compact_micro_end":
            continue
        params = ev.get("parameters") if isinstance(ev.get("parameters"), dict) else {}
        if params.get("trigger") == "cold_cache" and params.get("applied") is True:
            return True
    return False


def _microcompact_saved(events: list[dict[str, Any]]) -> int:
    saved = 0
    for ev in _compact_events(events):
        if ev.get("action") != "compact_micro_end":
            continue
        params = ev.get("parameters") if isinstance(ev.get("parameters"), dict) else {}
        try:
            saved = max(saved, int(params.get("saved_count") or 0))
        except (TypeError, ValueError):
            pass
    return saved


def _marker_count(messages: list[dict[str, Any]], marker: str) -> int:
    count = 0
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("content") == marker:
                count += 1
    return count


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R4 is real-AWS gated.",
)
def test_r4_cold_cache_microcompact(monkeypatch):
    """R4: seeded idle gap triggers A-16 cold-cache microcompact before call."""
    from agent import Agent
    from core.compactor import Compactor
    from runtime.audit import AUDIT
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr

    call = int(os.getenv("R_TIER_CALL", "1"))
    audit_dir = _REPO_ROOT / "compact_v5" / "_status" / "r_tier_runtime" / f"R4-call{call}-audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    side_metrics = _REPO_ROOT / "compact_v5" / "_status" / f"r-tier-R4-aws-call{call}-side-metrics.json"

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_audit_dir = getattr(CONFIG, "audit_dir", None)
    saved_disable_traces = getattr(CONFIG, "disable_local_traces", None)
    saved_threshold = getattr(CONFIG, "cold_cache_threshold_seconds", None)
    cwd_before = os.getcwd()
    captured: list[str] = []
    try:
        CONFIG.workspace = str(audit_dir)
        CONFIG.audit_dir = str(audit_dir)
        CONFIG.session_cost_limit = _R4_HARD_CEILING_USD
        CONFIG.model_id = _HAIKU_45_AU
        CONFIG.max_tokens = 128
        CONFIG.require_tool_approval = False
        CONFIG.disable_local_traces = False
        CONFIG.cold_cache_threshold_seconds = 1
        sec_mgr.rebuild_singleton_for_tests()
        AUDIT.__init__(audit_dir=str(audit_dir))
        os.chdir(str(audit_dir))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)

        def _hard_cost_halt() -> bool:
            return TOKENS.is_over_budget() if hasattr(TOKENS, "is_over_budget") else (
                TOKENS.session_cost >= _R4_HARD_CEILING_USD
            )

        def _stdout_capture(text: str) -> None:
            captured.append(text)
            print(text)

        agent = Agent(client=client, max_turns=2, on_stop_check=_hard_cost_halt)
        seeded = _seed_cold_cache_history()
        tokens_before = Compactor.estimate_tokens(seeded)
        agent._engine.messages = seeded
        agent._engine._last_api_call_time = time.time() - 5

        t0 = time.time()
        result = agent.run(
            "The cache has been idle. Reply exactly: R4 cold-cache microcompact ready.",
            tools=[],
            output_fn=_stdout_capture,
        )
        wallclock_s = time.time() - t0

        events = _audit_events(audit_dir)
        applied = _microcompact_applied(events)
        saved_count = _microcompact_saved(events)
        marker_count = _marker_count(agent._engine.messages, Compactor.MICROCOMPACT_MARKER)
        cost_used = float(TOKENS.session_cost)
        stdout_text = "\n".join(captured)
        final_text = (result.text or "").strip()
        artifact_ok = bool(
            result.stop_reason == "end_turn"
            and "R4 cold-cache microcompact ready" in final_text
            and applied
            and saved_count >= Compactor.MICROCOMPACT_MIN_SAVINGS
            and marker_count >= 2
            and cost_used <= _R4_HARD_CEILING_USD
        )
        process_quality_ok = bool(
            "[i] Cold cache detected" in stdout_text
            and len(_compact_events(events)) >= 2
            and not any(ev.get("action") == "compact_micro_failed" for ev in events)
        )

        metrics = {
            "test": "R4",
            "call": call,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": _HAIKU_45_AU,
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
            "tokens_before_seeded_microcompact": int(tokens_before),
            "cold_cache_threshold_seconds": CONFIG.cold_cache_threshold_seconds,
            "seeded_idle_gap_seconds": 5,
            "microcompact_applied": applied,
            "microcompact_saved_tokens": int(saved_count),
            "microcompact_marker_count": int(marker_count),
            "compact_event_actions": [ev.get("action") for ev in _compact_events(events)],
            "artifact_quality_ok": artifact_ok,
            "process_quality_ok": process_quality_ok,
            "completed": bool(artifact_ok and process_quality_ok),
            "cost_usd": round(cost_used, 4),
            "verdict": "GENUINE_PASS" if artifact_ok and process_quality_ok else "FAIL",
            "stop_reason": result.stop_reason,
            "final_text": final_text[:500],
            "audit_dir": str(audit_dir),
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
                "subagent_cost_usd": stats.get("subagent_cost_usd", {}),
            })
        side_metrics.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"\n[R4_AUDIT_DIR] {audit_dir}")
        print(f"[R4_SIDE_METRICS] {side_metrics}")
        print(f"[R4_METRICS] {json.dumps(metrics, sort_keys=True)}")

        assert result.stop_reason == "end_turn", f"R4 ended non-ready. metrics={metrics}"
        assert "R4 cold-cache microcompact ready" in final_text, (
            f"R4 final text did not contain expected anchor. metrics={metrics}"
        )
        assert applied, f"R4 did not apply cold-cache microcompact. metrics={metrics}"
        assert saved_count >= Compactor.MICROCOMPACT_MIN_SAVINGS, (
            f"R4 microcompact saved too little. metrics={metrics}"
        )
        assert marker_count >= 2, f"R4 did not clear old tool results. metrics={metrics}"
        assert process_quality_ok, f"R4 process-quality evidence incomplete. metrics={metrics}"
        assert cost_used <= _R4_HARD_CEILING_USD, (
            f"R4 cost ${cost_used:.4f} exceeded cap ${_R4_COST_CAP_USD:.2f} "
            f"plus 20% retry buffer (${_R4_HARD_CEILING_USD:.2f}). metrics={metrics}"
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
        if saved_require_approval is not None:
            CONFIG.require_tool_approval = saved_require_approval
        if saved_audit_dir is not None:
            CONFIG.audit_dir = saved_audit_dir
        if saved_disable_traces is not None:
            CONFIG.disable_local_traces = saved_disable_traces
        if saved_threshold is None:
            try:
                delattr(CONFIG, "cold_cache_threshold_seconds")
            except AttributeError:
                pass
        else:
            CONFIG.cold_cache_threshold_seconds = saved_threshold
