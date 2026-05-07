"""SOFTWARE-SUBAGENT lock tests."""
from __future__ import annotations

import json
import os
import sys
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
        self.calls: List[Dict[str, Any]] = []

    def chat(self, messages, system, tools, max_tokens, temperature,
             thinking_enabled, thinking_budget):
        from runtime.bedrock_client import Response, ToolCall

        self.calls.append({"messages": list(messages), "system": system})
        if not self.script:
            return Response(text="(end)", tool_calls=[], stop_reason="end_turn")
        kind, *rest = self.script.pop(0)
        if kind == "text":
            text = rest[0]
            usage = rest[1] if len(rest) > 1 else {}
            return Response(text=text, tool_calls=[], stop_reason="end_turn", usage=usage)
        if kind == "tool":
            cid, name, args = rest[:3]
            usage = rest[3] if len(rest) > 3 else {}
            return Response(
                text="",
                tool_calls=[ToolCall(cid, name, args)],
                stop_reason="tool_use",
                usage=usage,
            )
        raise AssertionError(f"unknown script kind: {kind}")


@pytest.fixture(autouse=True)
def fresh_registry():
    from tools.registry import _reset_registry_for_tests
    from tools import bootstrap_built_ins
    _reset_registry_for_tests()
    bootstrap_built_ins()
    yield


def _extract_envelope(text: str) -> Dict[str, Any]:
    marker = "[subagent_result_envelope]"
    assert marker in text
    payload = text.split(marker, 1)[1].strip()
    if "[subagent_artifacts]" in payload:
        payload = payload.split("[subagent_artifacts]", 1)[0].strip()
    return json.loads(payload)


def test_spawn_subagent_result_envelope_has_tokens_files_and_heartbeat(tmp_path, monkeypatch):
    from core import IterationBudget, QueryEngine
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    from subagent.spawn import spawn_subagent

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    TOKENS.reset()

    target = tmp_path / "child.txt"
    client = _ScriptedClient([
        (
            "tool",
            "w1",
            "write_file",
            {"file_path": str(target), "content": "hello"},
            {
                "input_tokens": 100,
                "output_tokens": 10,
                "cache_read_input_tokens": 7,
                "cache_creation_input_tokens": 3,
            },
        ),
        (
            "text",
            "child done",
            {
                "input_tokens": 80,
                "output_tokens": 20,
                "cache_read_input_tokens": 5,
                "cache_creation_input_tokens": 2,
            },
        ),
    ])
    parent = QueryEngine(client=client, max_turns=5, budget=IterationBudget())

    result = spawn_subagent(
        parent_engine=parent,
        prompt="write a small file",
        agent_type="general",
        workspace=str(tmp_path),
    )
    envelope = result.to_envelope()

    assert result.stop_reason == "end_turn"
    assert result.child_session_id
    assert result.duration_ms >= 0
    assert envelope["heartbeat"]["count"] >= 2
    assert envelope["heartbeat"]["timed_out"] is False
    assert str(target) in envelope["files_changed"]
    assert envelope["tokens"]["input_tokens"] == 180
    assert envelope["tokens"]["output_tokens"] == 30
    assert envelope["cache"]["read_tokens"] == 12
    assert envelope["cache"]["write_tokens"] == 5
    assert envelope["cost_usd"] > 0
    assert envelope["recovery_hint"] == "completed"


def test_task_tool_returns_structured_subagent_envelope():
    from core import IterationBudget, QueryEngine
    from runtime.tokens import TOKENS
    from tools import all_registered, find_tool_by_name

    TOKENS.reset()
    client = _ScriptedClient([
        (
            "text",
            "review complete",
            {
                "input_tokens": 60,
                "output_tokens": 15,
                "cache_read_input_tokens": 4,
                "cache_creation_input_tokens": 1,
            },
        ),
    ])
    parent = QueryEngine(client=client, max_turns=3, budget=IterationBudget())
    task_tool = find_tool_by_name(all_registered(), "task")

    out = task_tool.execute(
        {"prompt": "review the current change", "subagent_type": "review"},
        context={"parent_engine": parent, "parent_depth": 0},
    )
    envelope = _extract_envelope(out)

    assert "review complete" in out
    assert envelope["schema"] == "sageagent.subagent_result.v1"
    assert envelope["agent_type"] == "review"
    assert envelope["stop_reason"] == "end_turn"
    assert envelope["tokens"]["input_tokens"] == 60
    assert envelope["tokens"]["output_tokens"] == 15
    assert envelope["cache"]["read_tokens"] == 4
    assert envelope["cache"]["write_tokens"] == 1
    assert envelope["summary"] == "review complete"


def test_task_tool_persists_review_receipt_in_docs_reviews(tmp_path, monkeypatch):
    from core import IterationBudget, QueryEngine
    from runtime.config import CONFIG
    from runtime.tokens import TOKENS
    from tools import all_registered, find_tool_by_name

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    (tmp_path / "docs").mkdir()
    (tmp_path / "AGENT_STATUS.md").write_text("review state", encoding="utf-8")
    TOKENS.reset()
    client = _ScriptedClient([
        (
            "text",
            "review complete",
            {
                "input_tokens": 60,
                "output_tokens": 15,
                "cache_read_input_tokens": 4,
                "cache_creation_input_tokens": 1,
            },
        ),
    ])
    parent = QueryEngine(client=client, max_turns=3, budget=IterationBudget())
    task_tool = find_tool_by_name(all_registered(), "task")

    out = task_tool.execute(
        {"description": "final review", "prompt": "review the current change", "subagent_type": "review"},
        context={"parent_engine": parent, "parent_depth": 0},
    )
    envelope = _extract_envelope(out)

    review_files = list((tmp_path / "docs" / "reviews").glob("*.md"))
    state_files = list((tmp_path / ".sageagent_state" / "subagents").glob("*.md"))
    log_file = tmp_path / "docs" / "logs" / "subagent_artifacts.log"
    assert review_files
    assert state_files
    assert log_file.exists()
    assert "[subagent_artifacts]" in out
    assert str(review_files[0]) in envelope["artifact_paths"]
    receipt = review_files[0].read_text(encoding="utf-8")
    assert "Subagent Receipt: review" in receipt
    assert "review complete" in receipt
    assert "sageagent.subagent_result.v1" in receipt
    assert str(review_files[0]) in log_file.read_text(encoding="utf-8")


def test_prompt_requires_real_task_when_user_requires_reviewer_evidence():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    coord = os.path.join(root, "prompt", "subagent_coord.md")
    verify = os.path.join(root, "prompt", "verification_contract.md")

    coord_text = open(coord, "r", encoding="utf-8").read()
    verify_text = open(verify, "r", encoding="utf-8").read()

    assert "MUST call the `task` tool" in coord_text
    assert "Manually writing a `docs/reviews/*.md` file is not a substitute" in coord_text
    assert "User-required supervisor/reviewer mode" in verify_text
    assert "Do not replace it with a self-written review file" in verify_text


def test_budget_exhausted_task_tool_includes_recovery_envelope():
    from core import IterationBudget, QueryEngine
    from tools import all_registered, find_tool_by_name

    budget = IterationBudget(max_iterations=1)
    budget.consume()
    parent = QueryEngine(
        client=_ScriptedClient([("text", "should not run")]),
        max_turns=3,
        budget=budget,
    )
    task_tool = find_tool_by_name(all_registered(), "task")

    out = task_tool.execute(
        {"prompt": "do a thing", "subagent_type": "general"},
        context={"parent_engine": parent, "parent_depth": 0},
    )
    envelope = _extract_envelope(out)

    assert "Sub-agent stopped: budget_exhausted" in out
    assert envelope["stop_reason"] == "budget_exhausted"
    assert envelope["heartbeat"]["timed_out"] is True
    assert envelope["recovery_hint"] == "parent_should_resume_or_spawn_followup_with_previous_summary"
