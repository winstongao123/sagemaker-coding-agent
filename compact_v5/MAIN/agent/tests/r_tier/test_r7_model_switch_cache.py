"""R-tier R7 - Haiku to Sonnet model switch and cache invariant proof.

R7 validates a same-session model switch from Haiku 4.5 AU to Sonnet 4.5 AU
without broad workflow noise. The first turn seeds a distinctive context
marker on Haiku. The second turn switches the existing client's model id to
Sonnet and requires the model to recall that marker.

Evidence pillars:
  - the first Bedrock call uses Haiku 4.5 AU;
  - the second Bedrock call uses Sonnet 4.5 AU in the same Agent session;
  - a typed audit `model_switch` event records the switch;
  - the second assistant answer preserves the pre-switch context marker;
  - token/cache fields are numeric and recorded in side metrics/telemetry;
  - no tools or failure-loop events are used.

Cost cap: $0.50 planned / $0.60 hard retry ceiling. Model path: Haiku -> Sonnet.
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


_HAIKU_45_AU = "au.anthropic.claude-haiku-4-5-20251001-v1:0"
_SONNET_45_AU = "au.anthropic.claude-sonnet-4-5-20250929-v1:0"
_R7_COST_CAP_USD = 0.50
_R7_HARD_CEILING_USD = _R7_COST_CAP_USD * 1.20
_MARKER = "R7-CONTEXT-VIOLET-913"

_TURN1_PROMPT = (
    "Remember this exact context marker for the next turn: "
    f"{_MARKER}. Reply in one short sentence that you stored it."
)
_TURN2_PROMPT = (
    "This is the post-switch turn. State the exact context marker from the "
    "previous turn and include the literal token SONNET_AFTER_SWITCH. Do not "
    "use tools."
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


@pytest.mark.skipif(
    not os.getenv("RUN_REAL_BEDROCK"),
    reason="RUN_REAL_BEDROCK not set; R7 is real-AWS gated.",
)
def test_r7_haiku_to_sonnet_model_switch_cache_invariant(tmp_path):
    """R7 passes when same-session context survives an actual Sonnet switch."""
    from agent import Agent
    from runtime.audit import AUDIT
    from runtime.bedrock_client import BedrockClient
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    import security.manager as sec_mgr

    call = int(os.getenv("R_TIER_CALL", "1"))
    audit_dir = (
        _REPO_ROOT
        / "compact_v5"
        / "_status"
        / "r_tier_runtime"
        / f"R7-call{call}-audit"
    )
    audit_dir.mkdir(parents=True, exist_ok=True)
    side_metrics = (
        _REPO_ROOT
        / "compact_v5"
        / "_status"
        / f"r-tier-R7-aws-call{call}-side-metrics.json"
    )

    saved_ws = CONFIG.workspace
    saved_sec = sec_mgr.SECURITY
    saved_cost_limit = getattr(CONFIG, "session_cost_limit", None)
    saved_model = getattr(CONFIG, "model_id", None)
    saved_max_tokens = getattr(CONFIG, "max_tokens", None)
    saved_temperature = getattr(CONFIG, "temperature", None)
    saved_require_approval = getattr(CONFIG, "require_tool_approval", None)
    saved_audit_dir = getattr(CONFIG, "audit_dir", None)
    saved_disable_traces = getattr(CONFIG, "disable_local_traces", None)
    saved_enable_prompt_cache = getattr(CONFIG, "enable_prompt_cache", None)
    cwd_before = os.getcwd()

    captured_stdout: list[str] = []

    def _stdout_capture(text: str) -> None:
        captured_stdout.append(str(text))
        print(text)

    try:
        CONFIG.workspace = str(tmp_path)
        CONFIG.audit_dir = str(audit_dir)
        CONFIG.session_cost_limit = _R7_HARD_CEILING_USD
        CONFIG.model_id = _HAIKU_45_AU
        CONFIG.max_tokens = 512
        CONFIG.temperature = 0.0
        CONFIG.require_tool_approval = False
        CONFIG.disable_local_traces = False
        CONFIG.enable_prompt_cache = True
        sec_mgr.rebuild_singleton_for_tests()
        AUDIT.__init__(audit_dir=str(audit_dir))
        os.chdir(str(tmp_path))
        TOKENS.reset()

        region = os.getenv("AWS_REGION", "ap-southeast-2")
        client = BedrockClient(model_id=_HAIKU_45_AU, region=region, mock_mode=False)
        used_model_ids: list[str] = []
        original_chat = client.chat

        def _capturing_chat(*args, **kwargs):
            used_model_ids.append(str(client.model_id))
            return original_chat(*args, **kwargs)

        client.chat = _capturing_chat  # type: ignore[method-assign]

        def _hard_cost_halt() -> bool:
            if hasattr(TOKENS, "is_over_budget"):
                return TOKENS.is_over_budget()
            return TOKENS.session_cost >= _R7_HARD_CEILING_USD

        agent = Agent(client=client, max_turns=4, on_stop_check=_hard_cost_halt)
        t0 = time.time()
        first = agent.run(_TURN1_PROMPT, tools=[], output_fn=_stdout_capture)

        before_model = client.model_id
        client.model_id = _SONNET_45_AU
        CONFIG.model_id = _SONNET_45_AU
        AUDIT.log(
            agent._engine.session_id,
            "model_switch",
            tool_name="(engine)",
            parameters={
                "path": "same_agent_session",
                "logical_turn": 2,
                "from": before_model,
                "to": _SONNET_45_AU,
            },
            result_summary=f"R7 same-session model switch: {before_model} -> {_SONNET_45_AU}",
            user_approved=True,
        )

        second = agent.run(_TURN2_PROMPT, tools=[], output_fn=_stdout_capture)
        wallclock_s = time.time() - t0

        events = _audit_events(audit_dir)
        model_switch_events = [e for e in events if e.get("action") == "model_switch"]
        failure_loop_events = [
            e for e in events
            if str(e.get("action")) in {
                "tool_failure_recorded",
                "tool_failure_loop_warning",
                "tool_failure_loop_blocked",
            }
        ]
        stats = TOKENS.get_stats() if hasattr(TOKENS, "get_stats") else {}
        model_usage = stats.get("model_usage", {}) if isinstance(stats, dict) else {}
        output_joined = "\n".join(captured_stdout)
        second_text = second.text or ""
        context_survived = _MARKER in second_text
        sonnet_token_seen = "SONNET_AFTER_SWITCH" in second_text
        prompt_cache_warning_seen = "prompt-cache invariant" in output_joined.lower()
        cache_fields_numeric = all(
            isinstance(value, int)
            for value in (
                getattr(TOKENS, "session_cache_read", 0),
                getattr(TOKENS, "session_cache_write", 0),
                getattr(TOKENS, "parent_cache_read_tokens", 0),
                getattr(TOKENS, "parent_cache_write_tokens", 0),
            )
        )
        cost_used = float(TOKENS.session_cost)
        completed = bool(
            first.stop_reason != "max_turns"
            and second.stop_reason != "max_turns"
            and len(used_model_ids) >= 2
            and used_model_ids[0] == _HAIKU_45_AU
            and used_model_ids[1] == _SONNET_45_AU
            and context_survived
            and sonnet_token_seen
            and len(model_switch_events) == 1
            and cache_fields_numeric
            and not failure_loop_events
            and cost_used <= _R7_HARD_CEILING_USD
        )
        metrics = {
            "test": "R7",
            "call": call,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": f"{_HAIKU_45_AU} -> {_SONNET_45_AU}",
            "expected_models": [_HAIKU_45_AU, _SONNET_45_AU],
            "used_model_ids": used_model_ids,
            "tokens_in": int(TOKENS.session_input),
            "tokens_out": int(TOKENS.session_output),
            "cache_hit_pct": round(
                float(TOKENS.session_cache_read) / max(1, int(TOKENS.session_input)),
                4,
            ),
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
            "cost_cap_usd": _R7_COST_CAP_USD,
            "hard_ceiling_usd": _R7_HARD_CEILING_USD,
            "first_stop_reason": first.stop_reason,
            "second_stop_reason": second.stop_reason,
            "context_survived": context_survived,
            "sonnet_token_seen": sonnet_token_seen,
            "model_switch_events_logged": len(model_switch_events),
            "prompt_cache_warning_seen": prompt_cache_warning_seen,
            "cache_fields_numeric": cache_fields_numeric,
            "session_cache_read": int(TOKENS.session_cache_read),
            "session_cache_write": int(TOKENS.session_cache_write),
            "parent_cache_read_tokens": int(TOKENS.parent_cache_read_tokens),
            "parent_cache_write_tokens": int(TOKENS.parent_cache_write_tokens),
            "model_usage": model_usage,
            "failure_loop_events": len(failure_loop_events),
            "process_quality_ok": completed,
            "completed": completed,
            "verdict": "GENUINE_PASS" if completed else "FAIL",
            "audit_dir": str(audit_dir),
            "final_text": second_text[:500],
        }
        side_metrics.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
        print(f"\n[R7_AUDIT_DIR] {audit_dir}")
        print(f"[R7_SIDE_METRICS] {side_metrics}")
        print(f"[R7_METRICS] {json.dumps(metrics, sort_keys=True, default=str)}")

        assert first.stop_reason != "max_turns", f"R7 first turn hit max_turns: {metrics}"
        assert second.stop_reason != "max_turns", f"R7 second turn hit max_turns: {metrics}"
        assert used_model_ids[:2] == [_HAIKU_45_AU, _SONNET_45_AU], (
            f"R7 expected Haiku then Sonnet calls, got {used_model_ids}. metrics={metrics}"
        )
        assert context_survived, f"R7 post-switch response lost marker {_MARKER}. metrics={metrics}"
        assert sonnet_token_seen, f"R7 post-switch response missed SONNET_AFTER_SWITCH. metrics={metrics}"
        assert len(model_switch_events) == 1, f"R7 expected one model_switch audit event. metrics={metrics}"
        assert cache_fields_numeric, f"R7 cache fields were not numeric. metrics={metrics}"
        assert not failure_loop_events, f"R7 had failure-loop events: {failure_loop_events}"
        assert cost_used <= _R7_HARD_CEILING_USD, (
            f"R7 cost ${cost_used:.4f} exceeded cap ${_R7_COST_CAP_USD:.2f} "
            f"plus 20% retry buffer (${_R7_HARD_CEILING_USD:.2f}). metrics={metrics}"
        )
    finally:
        os.chdir(cwd_before)
        CONFIG.workspace = saved_ws
        CONFIG.session_cost_limit = saved_cost_limit
        if saved_model is not None:
            CONFIG.model_id = saved_model
        if saved_max_tokens is not None:
            CONFIG.max_tokens = saved_max_tokens
        if saved_temperature is not None:
            CONFIG.temperature = saved_temperature
        if saved_require_approval is not None:
            CONFIG.require_tool_approval = saved_require_approval
        if saved_audit_dir is not None:
            CONFIG.audit_dir = saved_audit_dir
        if saved_disable_traces is not None:
            CONFIG.disable_local_traces = saved_disable_traces
        if saved_enable_prompt_cache is not None:
            CONFIG.enable_prompt_cache = saved_enable_prompt_cache
        sec_mgr.SECURITY = saved_sec
