"""SOFTWARE-COMPACT-TELEMETRY lock tests."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest


_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


class _ScriptedClient:
    mock_mode = True
    model_id = "anthropic.claude-sonnet-4-5-20250929-v1:0"

    def __init__(self, script):
        self.script = list(script)

    def chat(self, messages, system, tools, max_tokens, temperature,
             thinking_enabled, thinking_budget):
        from runtime.bedrock_client import Response, ToolCall

        if not self.script:
            return Response(text="done", tool_calls=[], stop_reason="end_turn")
        kind, *rest = self.script.pop(0)
        if kind == "text":
            return Response(text=rest[0], tool_calls=[], stop_reason="end_turn", usage={})
        if kind == "tool":
            cid, name, args = rest[:3]
            return Response(
                text="",
                tool_calls=[ToolCall(cid, name, args)],
                stop_reason="tool_use",
                usage={},
            )
        if kind == "tools":
            calls = [
                ToolCall(cid, name, args)
                for cid, name, args in rest[0]
            ]
            return Response(text="", tool_calls=calls, stop_reason="tool_use", usage={})
        raise AssertionError(f"unknown script kind: {kind}")


@pytest.fixture
def audit_logger(tmp_path, monkeypatch):
    from runtime.audit import AuditLogger
    import runtime.audit as audit_mod

    audit = AuditLogger(audit_dir=str(tmp_path / "audit"))
    monkeypatch.setattr(audit_mod, "AUDIT", audit)
    return audit


def _audit_actions(audit, session_id: str) -> List[Dict[str, Any]]:
    return audit.get_session_log(session_id)


def test_microcompact_emits_typed_audit_events(tmp_path, monkeypatch, audit_logger):
    from core import IterationBudget, QueryEngine
    from core.compactor import Compactor
    from runtime.config import CONFIG

    monkeypatch.setattr(CONFIG, "cold_cache_threshold_seconds", 0)
    monkeypatch.setattr(Compactor, "MICROCOMPACT_MIN_SAVINGS", 1)

    engine = QueryEngine(
        client=_ScriptedClient([("text", "ok")]),
        max_turns=2,
        budget=IterationBudget(),
        session_id="microtelemetry",
    )
    old = "x" * 30000
    recent = "y" * 200
    engine.messages = [
        {"role": "assistant", "content": [{"type": "tool_use", "id": "old", "name": "read_file", "input": {}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "old", "content": old}]},
        {"role": "assistant", "content": [{"type": "tool_use", "id": "new", "name": "read_file", "input": {}}]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "new", "content": recent}]},
    ]
    engine._last_api_call_time = time.time() - 10

    result = engine.run("continue", system_prompt="system", tools=[])

    assert result.stop_reason == "end_turn"
    actions = _audit_actions(audit_logger, "microtelemetry")
    names = [a["action"] for a in actions]
    assert "compact_micro_start" in names
    assert "compact_micro_end" in names
    end = [a for a in actions if a["action"] == "compact_micro_end"][-1]
    assert end["parameters"]["applied"] is True
    assert end["parameters"]["saved_count"] >= 1


def test_auto_compact_emits_typed_start_and_end(monkeypatch, audit_logger):
    from core import IterationBudget, QueryEngine
    from core.compactor import AUTO_COMPACT, CompactionResult, Compactor

    AUTO_COMPACT.reset()
    monkeypatch.setattr(Compactor, "should_compact", classmethod(lambda cls, messages, max_tokens=200000: True))
    monkeypatch.setattr(
        Compactor,
        "run",
        classmethod(lambda cls, client, messages, max_tokens=200000, skill_manager=None, **kwargs: CompactionResult(
            success=True,
            summary="summary",
            messages_after=list(messages[-1:]),
            tokens_before=10000,
            tokens_after=1000,
        )),
    )

    engine = QueryEngine(
        client=_ScriptedClient([("text", "ok")]),
        max_turns=2,
        budget=IterationBudget(),
        session_id="autotelemetry",
    )
    result = engine.run("trigger", system_prompt="system", tools=[])

    assert result.stop_reason == "end_turn"
    actions = _audit_actions(audit_logger, "autotelemetry")
    names = [a["action"] for a in actions]
    assert "compact_auto_start" in names
    assert "compact_auto_end" in names
    end = [a for a in actions if a["action"] == "compact_auto_end"][-1]
    assert end["parameters"]["saved_count"] == 9000


def test_repeated_tool_failure_loop_is_audited_and_blocked(audit_logger):
    from core import IterationBudget, QueryEngine
    from tools.registry import build_tool

    calls = []

    def _fail(args, context=None):
        calls.append(dict(args))
        return "Error: fixture failure"

    fail_tool = build_tool(
        name="fail_tool",
        description="fixture failure tool",
        input_schema={"type": "object", "properties": {"x": {"type": "integer"}}},
        execute=_fail,
    )
    client = _ScriptedClient([
        ("tool", "t1", "fail_tool", {"x": 1}), ("text", "after1"),
        ("tool", "t2", "fail_tool", {"x": 1}), ("text", "after2"),
        ("tool", "t3", "fail_tool", {"x": 1}), ("text", "after3"),
    ])
    engine = QueryEngine(
        client=client,
        max_turns=2,
        budget=IterationBudget(max_iterations=10),
        session_id="failuretelemetry",
    )

    engine.run("first", system_prompt="system", tools=[fail_tool])
    engine.run("second", system_prompt="system", tools=[fail_tool])
    engine.run("third", system_prompt="system", tools=[fail_tool])

    assert len(calls) == 2
    actions = _audit_actions(audit_logger, "failuretelemetry")
    names = [a["action"] for a in actions]
    assert names.count("tool_failure_recorded") == 2
    assert "tool_failure_loop_blocked" in names
    blocked = [a for a in actions if a["action"] == "tool_failure_loop_blocked"][-1]
    assert blocked["parameters"]["previous_failures"] == 2


def test_read_file_marks_file_read_for_edit_path(tmp_path, monkeypatch, audit_logger):
    from core import IterationBudget, QueryEngine
    from runtime.config import CONFIG
    from tools import _file_read_tracking, all_registered
    import security.manager as sec_mgr

    target = tmp_path / "app.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    _file_read_tracking.reset_for_tests()
    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    sec_mgr.rebuild_singleton_for_tests()

    engine = QueryEngine(
        client=_ScriptedClient([
            ("tool", "r1", "read_file", {"file_path": str(target)}),
            ("tool", "e1", "edit_file", {
                "file_path": str(target),
                "old_string": "VALUE = 1",
                "new_string": "VALUE = 2",
            }),
            ("text", "done"),
        ]),
        max_turns=4,
        budget=IterationBudget(max_iterations=10),
        session_id="readmarksedit",
    )

    result = engine.run("update", system_prompt="system", tools=list(all_registered()))

    assert result.stop_reason == "end_turn"
    assert target.read_text(encoding="utf-8") == "VALUE = 2\n"
    actions = _audit_actions(audit_logger, "readmarksedit")
    failures = [a for a in actions if a["action"] == "tool_failure_recorded"]
    assert failures == []


def test_guard_class_breaker_blocks_batched_unread_edit_loop(tmp_path, monkeypatch, audit_logger):
    from core import IterationBudget, QueryEngine
    from runtime.config import CONFIG
    from tools import _file_read_tracking, all_registered
    import security.manager as sec_mgr

    targets = []
    for idx in range(3):
        target = tmp_path / f"file{idx}.py"
        target.write_text("VALUE = 1\n", encoding="utf-8")
        targets.append(target)
    _file_read_tracking.reset_for_tests()
    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    sec_mgr.rebuild_singleton_for_tests()

    calls = [
        (f"e{idx}", "edit_file", {
            "file_path": str(target),
            "old_string": "VALUE = 1",
            "new_string": "VALUE = 2",
        })
        for idx, target in enumerate(targets)
    ]
    engine = QueryEngine(
        client=_ScriptedClient([("tools", calls), ("text", "done")]),
        max_turns=3,
        budget=IterationBudget(max_iterations=10),
        session_id="guardbatchedit",
    )

    result = engine.run("bad edits", system_prompt="system", tools=list(all_registered()))

    assert result.stop_reason == "end_turn"
    assert all(target.read_text(encoding="utf-8") == "VALUE = 1\n" for target in targets)
    actions = _audit_actions(audit_logger, "guardbatchedit")
    failures = [a for a in actions if a["action"] == "tool_failure_recorded"]
    blocked = [a for a in actions if a["action"] == "tool_failure_loop_blocked"]
    assert len([a for a in failures if a["tool_name"] == "edit_file"]) == 2
    assert blocked[-1]["parameters"]["failure_class"] == "read_before_edit"


def test_guard_class_breaker_blocks_batched_unread_write_loop(tmp_path, monkeypatch, audit_logger):
    from core import IterationBudget, QueryEngine
    from runtime.config import CONFIG
    from tools import _file_read_tracking, all_registered
    import security.manager as sec_mgr

    targets = []
    for idx in range(3):
        target = tmp_path / f"file{idx}.txt"
        target.write_text("old\n", encoding="utf-8")
        targets.append(target)
    _file_read_tracking.reset_for_tests()
    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    sec_mgr.rebuild_singleton_for_tests()

    calls = [
        (f"w{idx}", "write_file", {"file_path": str(target), "content": "new\n"})
        for idx, target in enumerate(targets)
    ]
    engine = QueryEngine(
        client=_ScriptedClient([("tools", calls), ("text", "done")]),
        max_turns=3,
        budget=IterationBudget(max_iterations=10),
        session_id="guardbatchwrite",
    )

    result = engine.run("bad writes", system_prompt="system", tools=list(all_registered()))

    assert result.stop_reason == "end_turn"
    assert all(target.read_text(encoding="utf-8") == "old\n" for target in targets)
    actions = _audit_actions(audit_logger, "guardbatchwrite")
    failures = [a for a in actions if a["action"] == "tool_failure_recorded"]
    blocked = [a for a in actions if a["action"] == "tool_failure_loop_blocked"]
    assert len([a for a in failures if a["tool_name"] == "write_file"]) == 2
    assert blocked[-1]["parameters"]["failure_class"] == "read_before_write"


def test_guard_class_breaker_blocks_repeated_python_exec_errors(audit_logger):
    from core import IterationBudget, QueryEngine
    from tools import all_registered

    calls = [
        ("p1", "python_exec", {"code": "if True print('bad')"}),
        ("p2", "python_exec", {"code": "for"}),
        ("p3", "python_exec", {"code": "def nope(:\n    pass"}),
    ]
    engine = QueryEngine(
        client=_ScriptedClient([("tools", calls), ("text", "done")]),
        max_turns=3,
        budget=IterationBudget(max_iterations=10),
        session_id="guardpythonexec",
    )

    result = engine.run("bad python", system_prompt="system", tools=list(all_registered()))

    assert result.stop_reason == "end_turn"
    actions = _audit_actions(audit_logger, "guardpythonexec")
    failures = [a for a in actions if a["action"] == "tool_failure_recorded"]
    blocked = [a for a in actions if a["action"] == "tool_failure_loop_blocked"]
    assert len([a for a in failures if a["tool_name"] == "python_exec"]) == 2
    assert blocked[-1]["parameters"]["failure_class"] == "python_exec_error"


def test_python_exec_error_class_allows_later_script_after_success(tmp_path, monkeypatch, audit_logger):
    from core import IterationBudget, QueryEngine
    from runtime.config import CONFIG
    from tools import all_registered
    import security.manager as sec_mgr

    marker = tmp_path / "marker.txt"
    marker.write_text("ok\n", encoding="utf-8")
    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    sec_mgr.rebuild_singleton_for_tests()

    calls = [
        ("p1", "python_exec", {"code": "if True print('bad')"}),
        ("p2", "python_exec", {"code": "for"}),
        ("r1", "read_file", {"file_path": str(marker)}),
        ("p3", "python_exec", {"code": "print('recovered')"}),
    ]
    engine = QueryEngine(
        client=_ScriptedClient([
            ("tool", *calls[0]),
            ("tool", *calls[1]),
            ("tool", *calls[2]),
            ("tool", *calls[3]),
            ("text", "done"),
        ]),
        max_turns=6,
        budget=IterationBudget(max_iterations=10),
        session_id="guardpythonexecrecovery",
    )

    result = engine.run("bad then recovered python", system_prompt="system", tools=list(all_registered()))

    assert result.stop_reason == "end_turn"
    actions = _audit_actions(audit_logger, "guardpythonexecrecovery")
    failures = [a for a in actions if a["action"] == "tool_failure_recorded"]
    blocked = [a for a in actions if a["action"] == "tool_failure_loop_blocked"]
    python_failures = [a for a in failures if a["tool_name"] == "python_exec"]
    assert len(python_failures) == 2
    assert blocked == []
