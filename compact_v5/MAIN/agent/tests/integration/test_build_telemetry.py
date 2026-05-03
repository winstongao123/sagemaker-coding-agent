"""Lock tests for compact_v5/_status/scripts/build_telemetry.py.

Per PLAYBOOK §1: Codex AXIS A review BEFORE first use; lock test mocks
audit_log + raw_log + side-channel and verifies aggregator output schema.

Mock-based ($0); no AWS spend. Required to PASS before R1 redo.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest


_THIS = Path(__file__).resolve()
# tests/integration/test_build_telemetry.py → integration → tests → agent → MAIN → compact_v5
_V5_ROOT = _THIS.parents[4]  # compact_v5
_SCRIPT_PATH = _V5_ROOT / "_status" / "scripts" / "build_telemetry.py"


def _load_build_telemetry():
    """Import build_telemetry.py as a module from its absolute path."""
    spec = importlib.util.spec_from_file_location("build_telemetry", str(_SCRIPT_PATH))
    assert spec is not None, f"could not load spec for {_SCRIPT_PATH}"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_build_telemetry_script_exists():
    assert _SCRIPT_PATH.is_file(), f"missing {_SCRIPT_PATH}"


def test_build_telemetry_compiles():
    import py_compile
    py_compile.compile(str(_SCRIPT_PATH), doraise=True)


def _write_audit_jsonl(path: Path, events: list) -> None:
    with path.open("w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


def test_build_telemetry_aggregates_tool_dispatch_events(tmp_path):
    """Aggregator groups tool_dispatch events by chronological window
    + summarises per-tool counts + REPEATED detection."""
    bt = _load_build_telemetry()
    audit_path = tmp_path / "audit.jsonl"
    _write_audit_jsonl(audit_path, [
        {"timestamp": "2026-05-04T10:00:00.000",
         "session_id": "s1", "action": "tool_dispatch",
         "tool_name": "read_file", "parameters": {"file_path": "x.txt"},
         "result_summary": "OK", "user_approved": True, "hash": "h1"},
        {"timestamp": "2026-05-04T10:00:05.000",
         "session_id": "s1", "action": "tool_dispatch",
         "tool_name": "read_file", "parameters": {"file_path": "x.txt"},
         "result_summary": "OK", "user_approved": True, "hash": "h2"},
        # Same name+args as above → REPEATED.
        {"timestamp": "2026-05-04T10:00:08.000",
         "session_id": "s1", "action": "tool_dispatch",
         "tool_name": "create_chart", "parameters": {"filepath": "c.png"},
         "result_summary": "Wrote", "user_approved": True, "hash": "h3"},
        # Big gap → next "turn".
        {"timestamp": "2026-05-04T10:01:30.000",
         "session_id": "s1", "action": "tool_dispatch",
         "tool_name": "create_word", "parameters": {"filepath": "r.docx"},
         "result_summary": "Wrote", "user_approved": True, "hash": "h4"},
    ])
    raw_log = tmp_path / "r-tier-RX-aws-call1.log"
    raw_log.write_text("============================= 1 passed =============================\n", encoding="utf-8")
    out = tmp_path / "telemetry.json"

    telemetry = bt.build_telemetry(
        test="RX", call=1,
        audit_log_path=audit_path,
        raw_log_path=raw_log,
        side_channel_path=None,
    )

    # Required schema keys.
    for key in {"test", "call", "per_turn", "tool_call_summary",
                "compaction_events", "subagent_dispatches",
                "cache_efficiency_trend", "outcome"}:
        assert key in telemetry, f"telemetry missing required key {key}"

    # Two turns based on 30s window heuristic.
    assert len(telemetry["per_turn"]) == 2, (
        f"expected 2 turns, got {len(telemetry['per_turn'])}"
    )
    # PLAYBOOK §4.5 Gap A — thinking fields present (null when audit_log
    # has no chat_response events).
    for pt in telemetry["per_turn"]:
        assert "thinking_text" in pt
        assert "thinking_tokens" in pt
        assert pt["thinking_text"] is None
        assert pt["thinking_tokens"] == 0
    # Tool call summary.
    s = telemetry["tool_call_summary"]
    assert s["TOTAL_calls"] == 4
    assert s["per_tool"] == {"read_file": 2, "create_chart": 1, "create_word": 1}
    # REPEATED is the duplicate count beyond first occurrence; 2 read_file
    # calls with identical args = 1 repeat.
    assert s["REPEATED_calls"] == 1, f"expected REPEATED_calls=1, got {s['REPEATED_calls']}"


def test_build_telemetry_captures_thinking_when_audit_emits_chat_response(tmp_path):
    """PLAYBOOK §4.5 Gap A lock — when audit_log carries a chat_response
    event with thinking, telemetry per_turn[].thinking_text is populated."""
    bt = _load_build_telemetry()
    audit_path = tmp_path / "audit.jsonl"
    _write_audit_jsonl(audit_path, [
        {"timestamp": "2026-05-04T10:00:00.000",
         "session_id": "s1", "action": "chat_response",
         "tool_name": "(engine)",
         "response": {
             "thinking": "Step 1: I should think about this. Step 2: ok.",
             "text": "answer",
             "usage": {"input_tokens": 1000, "output_tokens": 200,
                       "cache_read_input_tokens": 500,
                       "cache_creation_input_tokens": 0},
         },
         "result_summary": "OK", "user_approved": True, "hash": "h1"},
        {"timestamp": "2026-05-04T10:00:02.000",
         "session_id": "s1", "action": "tool_dispatch",
         "tool_name": "read_file", "parameters": {"file_path": "x.txt"},
         "result_summary": "OK", "user_approved": True, "hash": "h2"},
    ])
    raw_log = tmp_path / "raw.log"
    raw_log.write_text("ok\n", encoding="utf-8")

    telemetry = bt.build_telemetry(
        test="R17", call=1,
        audit_log_path=audit_path,
        raw_log_path=raw_log,
        side_channel_path=None,
    )
    assert len(telemetry["per_turn"]) == 1
    pt = telemetry["per_turn"][0]
    assert pt["thinking_text"] is not None
    assert "Step 1" in pt["thinking_text"]
    assert pt["thinking_tokens"] > 0
    assert pt["tokens_in"] == 1000
    assert pt["tokens_out"] == 200
    assert pt["cache_read_tokens"] == 500
    # cache_hit_pct = 500 / (500 + 0 + 1000) = 0.3333
    assert abs(pt["cache_hit_pct"] - 0.3333) < 0.001


def test_build_telemetry_validation_rejects_malformed_output(tmp_path):
    """Validation function catches missing required keys."""
    bt = _load_build_telemetry()
    bad_telemetry = {"test": "X", "call": 1}  # missing per_turn etc.
    errors = bt._validate_telemetry(bad_telemetry)
    assert errors, "validation must reject missing required keys"
    assert any("missing required" in e for e in errors)


def test_build_telemetry_handles_compaction_and_subagent_events(tmp_path):
    """Aggregator filters compact + task (subagent dispatch) events
    into their dedicated arrays."""
    bt = _load_build_telemetry()
    audit_path = tmp_path / "audit.jsonl"
    _write_audit_jsonl(audit_path, [
        {"timestamp": "2026-05-04T10:00:00.000",
         "session_id": "s1", "action": "compact_invoked",
         "tool_name": "(engine)", "parameters": {"trigger": "auto"},
         "result_summary": "freed 5000 tokens", "hash": "h1"},
        {"timestamp": "2026-05-04T10:00:05.000",
         "session_id": "s1", "action": "tool_dispatch",
         "tool_name": "task",
         "parameters": {"subagent_type": "explore", "description": "find auth"},
         "result_summary": "ok", "user_approved": True, "hash": "h2"},
    ])
    raw_log = tmp_path / "raw.log"
    raw_log.write_text("ok", encoding="utf-8")

    telemetry = bt.build_telemetry(
        test="RX", call=1, audit_log_path=audit_path,
        raw_log_path=raw_log, side_channel_path=None,
    )
    assert len(telemetry["compaction_events"]) == 1
    assert "freed" in telemetry["compaction_events"][0]["result_summary"]
    assert len(telemetry["subagent_dispatches"]) == 1
    assert telemetry["subagent_dispatches"][0]["agent_type"] == "explore"


def test_build_telemetry_uses_side_channel_for_outcome(tmp_path):
    """Side-channel _<test>_metrics.json populates outcome.cost_usd etc."""
    bt = _load_build_telemetry()
    audit_path = tmp_path / "audit.jsonl"
    _write_audit_jsonl(audit_path, [])
    raw_log = tmp_path / "raw.log"
    raw_log.write_text(
        "[R1 METRICS] " + json.dumps({
            "test": "R1", "tokens_in": 5000, "tokens_out": 2000,
            "cost_usd": 0.04, "wallclock_s": 12.3,
            "stop_reason": "end_turn",
            "chart_exists": True, "report_exists": True,
        }) + "\n"
        "============================= 1 passed =============================\n",
        encoding="utf-8",
    )
    side = tmp_path / "_r1_metrics.json"
    side.write_text(json.dumps({
        "tokens_in": 5000, "tokens_out": 2000, "cost_usd": 0.04,
        "wallclock_s": 12.3, "stop_reason": "end_turn",
        "chart_exists": True, "report_exists": True,
    }), encoding="utf-8")

    telemetry = bt.build_telemetry(
        test="R1", call=1, audit_log_path=audit_path,
        raw_log_path=raw_log, side_channel_path=side,
    )
    out = telemetry["outcome"]
    assert out["cost_usd"] == 0.04
    assert out["tokens_in_total"] == 5000
    assert out["tokens_out_total"] == 2000
    assert out["completed"] is True
    assert out["artifacts_valid"]["chart"] is True
    assert out["artifacts_valid"]["report"] is True
