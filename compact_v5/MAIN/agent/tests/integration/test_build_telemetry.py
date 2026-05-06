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
                "cache_efficiency_trend", "agent_attribution",
                "failure_loop_events", "outcome"}:
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


def test_build_telemetry_carries_r16_software_builder_subchecks(tmp_path):
    bt = _load_build_telemetry()
    audit_path = tmp_path / "audit.jsonl"
    _write_audit_jsonl(audit_path, [
        {"timestamp": "2026-05-04T10:00:00.000",
         "session_id": "s1", "action": "tool_dispatch",
         "tool_name": "write_file", "parameters": {"file_path": "app.py"},
         "result_summary": "Written", "user_approved": True, "hash": "h1"},
    ])
    raw_log = tmp_path / "r-tier-R16-aws-call1.log"
    raw_log.write_text("============================= 1 passed =============================\n", encoding="utf-8")
    side = tmp_path / "side.json"
    side.write_text(json.dumps({
        "completed": True,
        "cost_usd": 0.12,
        "tokens_in": 10,
        "tokens_out": 20,
        "software_builder_subchecks": {
            "status_round_trip": True,
            "todo_round_trip": True,
            "named_checkpoint_round_trip": True,
            "verify_done_stale_evidence_blocked": True,
            "compaction_event_emitted": True,
            "cache_evidence_recorded": True,
            "cost_context_reported": True,
            "final_artifact_quality_passed": True,
        },
    }), encoding="utf-8")

    telemetry = bt.build_telemetry(
        test="R16", call=1,
        audit_log_path=audit_path,
        raw_log_path=raw_log,
        side_channel_path=side,
    )

    assert telemetry["software_builder_subchecks"]["status_round_trip"] is True
    assert telemetry["software_builder_subchecks"]["final_artifact_quality_passed"] is True


def test_build_telemetry_reads_all_jsonl_files_in_audit_directory(tmp_path):
    bt = _load_build_telemetry()
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    _write_audit_jsonl(audit_dir / "session.jsonl", [
        {"timestamp": "2026-05-04T10:00:00.000",
         "session_id": "s1", "action": "chat_response",
         "tool_name": "(engine)",
         "parameters": {"response": {
             "usage": {"input_tokens": 10, "output_tokens": 20,
                       "cache_read_input_tokens": 5,
                       "cache_creation_input_tokens": 7},
             "text": "use a tool",
         }},
         "result_summary": "tool_use", "user_approved": False, "hash": "h1"},
        {"timestamp": "2026-05-04T10:00:01.000",
         "session_id": "s1", "action": "tool_dispatch",
         "tool_name": "read_file", "parameters": {"file_path": "tests/test_app.py"},
         "result_summary": "OK", "user_approved": True, "hash": "h2"},
    ])
    _write_audit_jsonl(audit_dir / "forced-local.jsonl", [
        {"timestamp": "2026-05-04T10:00:02.000",
         "session_id": "s1", "action": "compact_auto_end",
         "tool_name": "(compactor)",
         "parameters": {"typed": True, "path": "forced_local"},
         "result_summary": "forced/local", "user_approved": True, "hash": "h3"},
    ])
    raw_log = tmp_path / "raw.log"
    raw_log.write_text("============================= 1 passed =============================\n", encoding="utf-8")

    telemetry = bt.build_telemetry(
        test="R16", call=1,
        audit_log_path=audit_dir,
        raw_log_path=raw_log,
        side_channel_path=None,
    )

    assert len(telemetry["audit_log_paths"]) == 2
    assert telemetry["tool_call_summary"]["TOTAL_calls"] == 1
    assert telemetry["per_turn"][0]["tokens_in"] == 10
    assert telemetry["per_turn"][0]["cache_read_tokens"] == 5
    assert len(telemetry["compaction_events"]) == 1


def test_build_telemetry_extracts_model_switch_events(tmp_path):
    bt = _load_build_telemetry()
    audit_path = tmp_path / "audit.jsonl"
    _write_audit_jsonl(audit_path, [
        {"timestamp": "2026-05-04T10:00:00.000",
         "session_id": "s1", "action": "model_switch",
         "tool_name": "(engine)",
         "parameters": {
             "path": "prebuilt_transcript",
             "logical_turn": 47,
             "from": "Haiku 4.5 AU",
             "to": "Sonnet 4.5 AU",
         },
         "result_summary": "prebuilt switch", "user_approved": True, "hash": "h1"},
    ])
    raw_log = tmp_path / "raw.log"
    raw_log.write_text("============================= 1 passed =============================\n", encoding="utf-8")

    telemetry = bt.build_telemetry(
        test="R19-U10", call=1,
        audit_log_path=audit_path,
        raw_log_path=raw_log,
        side_channel_path=None,
    )

    assert telemetry["model_switch_events"] == [{
        "timestamp": "2026-05-04T10:00:00.000",
        "from": "Haiku 4.5 AU",
        "to": "Sonnet 4.5 AU",
        "logical_turn": 47,
        "path": "prebuilt_transcript",
        "result_summary": "prebuilt switch",
    }]


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
    assert telemetry["cache_efficiency_trend"]["session_avg_hit_pct"] == pytest.approx(0.3333, abs=0.001)


def test_build_telemetry_reads_query_engine_nested_chat_response(tmp_path):
    """R-tier telemetry lock: QueryEngine writes chat_response payloads under
    parameters.response, which must be treated the same as legacy top-level
    response payloads."""
    bt = _load_build_telemetry()
    audit_path = tmp_path / "audit.jsonl"
    _write_audit_jsonl(audit_path, [
        {"timestamp": "2026-05-04T10:00:00.000",
         "session_id": "s1", "action": "chat_response",
         "tool_name": "(engine)",
         "parameters": {
             "turn": 1,
             "response": {
                 "thinking": "Real thinking text",
                 "text": "answer",
                 "usage": {"input_tokens": 200, "output_tokens": 50,
                           "cache_read_input_tokens": 100,
                           "cache_creation_input_tokens": 25},
             },
         },
         "result_summary": "OK", "user_approved": False, "hash": "h1"},
    ])
    raw_log = tmp_path / "raw.log"
    raw_log.write_text("ok\n", encoding="utf-8")

    telemetry = bt.build_telemetry(
        test="R17", call=1,
        audit_log_path=audit_path,
        raw_log_path=raw_log,
        side_channel_path=None,
    )
    pt = telemetry["per_turn"][0]
    assert pt["thinking_text"] == "Real thinking text"
    assert pt["tokens_in"] == 200
    assert pt["tokens_out"] == 50
    assert pt["cache_read_tokens"] == 100
    assert pt["cache_write_tokens"] == 25


def test_build_telemetry_validation_rejects_malformed_output(tmp_path):
    """Validation function catches missing required keys."""
    bt = _load_build_telemetry()
    bad_telemetry = {"test": "X", "call": 1}  # missing per_turn etc.
    errors = bt._validate_telemetry(bad_telemetry)
    assert errors, "validation must reject missing required keys"
    assert any("missing required" in e for e in errors)


def test_build_telemetry_handles_compaction_subagent_and_failure_events(tmp_path):
    """Aggregator filters typed compaction, subagent dispatch, and failure-loop events."""
    bt = _load_build_telemetry()
    audit_path = tmp_path / "audit.jsonl"
    _write_audit_jsonl(audit_path, [
        {"timestamp": "2026-05-04T10:00:00.000",
         "session_id": "s1", "action": "compact_auto_start",
         "tool_name": "(engine)", "parameters": {"trigger": "context_threshold"},
         "result_summary": "started", "hash": "h1"},
        {"timestamp": "2026-05-04T10:00:01.000",
         "session_id": "s1", "action": "compact_invoked",
         "tool_name": "(engine)", "parameters": {"trigger": "legacy"},
         "result_summary": "legacy freed", "hash": "h1b"},
        {"timestamp": "2026-05-04T10:00:05.000",
         "session_id": "s1", "action": "tool_dispatch",
         "tool_name": "task",
         "parameters": {"subagent_type": "explore", "description": "find auth"},
         "result_summary": "ok", "user_approved": True, "hash": "h2"},
        {"timestamp": "2026-05-04T10:00:07.000",
         "session_id": "s1", "action": "tool_failure_loop_blocked",
         "tool_name": "read_file",
         "parameters": {"args_hash": "abc", "previous_failures": 2},
         "result_summary": "blocked", "user_approved": False, "hash": "h3"},
    ])
    raw_log = tmp_path / "raw.log"
    raw_log.write_text("ok", encoding="utf-8")

    telemetry = bt.build_telemetry(
        test="RX", call=1, audit_log_path=audit_path,
        raw_log_path=raw_log, side_channel_path=None,
    )
    assert len(telemetry["compaction_events"]) == 2
    assert telemetry["compaction_events"][0]["typed"] is True
    assert telemetry["compaction_events"][1]["typed"] is False
    assert len(telemetry["subagent_dispatches"]) == 1
    assert telemetry["subagent_dispatches"][0]["agent_type"] == "explore"
    assert len(telemetry["failure_loop_events"]) == 1
    assert telemetry["failure_loop_events"][0]["action"] == "tool_failure_loop_blocked"


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
        "parent_input_tokens": 4000,
        "parent_output_tokens": 1000,
        "parent_cache_read_tokens": 300,
        "parent_cache_write_tokens": 80,
        "parent_cost_usd": 0.02,
        "subagent_input_tokens": {"review": 600, "verify": 700},
        "subagent_output_tokens": {"review": 120, "verify": 150},
        "subagent_cache_read_tokens": {"review": 60, "verify": 70},
        "subagent_cache_write_tokens": {"review": 12, "verify": 15},
        "subagent_cost_usd": {"review": 0.003, "verify": 0.004},
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
    agent_attr = telemetry["agent_attribution"]
    assert agent_attr["parent"]["input_tokens"] == 4000
    assert agent_attr["parent"]["output_tokens"] == 1000
    assert agent_attr["parent"]["cache_read_tokens"] == 300
    assert agent_attr["parent"]["cache_write_tokens"] == 80
    assert agent_attr["parent"]["cost_usd"] == 0.02
    assert agent_attr["subagents"]["review"]["input_tokens"] == 600
    assert agent_attr["subagents"]["review"]["output_tokens"] == 120
    assert agent_attr["subagents"]["review"]["cache_read_tokens"] == 60
    assert agent_attr["subagents"]["review"]["cache_write_tokens"] == 12
    assert agent_attr["subagents"]["review"]["cost_usd"] == 0.003
    assert agent_attr["subagents"]["verify"]["output_tokens"] == 150
    assert agent_attr["subagents"]["verify"]["cache_read_tokens"] == 70
    assert agent_attr["subagents"]["verify"]["cost_usd"] == 0.004
    assert agent_attr["reviewers"]["review"]["cost_usd"] == 0.003
