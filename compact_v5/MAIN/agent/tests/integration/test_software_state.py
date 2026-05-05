"""SOFTWARE-STATE durable state tests."""
from __future__ import annotations

import json
import os
import sys


_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def test_todos_persist_across_memory_reset(tmp_path, monkeypatch):
    from runtime.config import CONFIG
    from tools.todo import (
        _reset_todos_for_tests,
        _todo_read_executor,
        _todo_write_executor,
    )

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "disable_local_traces", False)
    _reset_todos_for_tests(clear_disk=True)

    result = _todo_write_executor(
        {
            "todos": [
                {
                    "content": "write state tests",
                    "status": "in_progress",
                    "activeForm": "Writing state tests",
                }
            ]
        },
        context={},
    )
    assert "1 todos" in result

    _reset_todos_for_tests()
    restored = json.loads(_todo_read_executor({}, context={}))
    assert restored[0]["content"] == "write state tests"
    assert (tmp_path / ".sageagent_state" / "todos.json").is_file()


def test_save_resume_round_trip_includes_todos_status_memory(tmp_path, monkeypatch):
    from commands import dispatch_command
    from runtime.config import CONFIG
    import runtime.session as session_mod
    from tools.todo import (
        _reset_todos_for_tests,
        _todo_read_executor,
        _todo_write_executor,
    )

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "sessions_dir", str(tmp_path / "sessions"))
    monkeypatch.setattr(CONFIG, "status_doc", "AGENT_STATUS.md")
    monkeypatch.setattr(CONFIG, "enable_status_doc", True)
    monkeypatch.setattr(CONFIG, "disable_local_traces", False)
    sm = session_mod.SessionManager(sessions_dir=str(tmp_path / "sessions"))
    monkeypatch.setattr(session_mod, "SESSIONS", sm)

    (tmp_path / "AGENT_STATUS.md").write_text(
        "# Status\n\nCurrent phase: durable state", encoding="utf-8",
    )
    (tmp_path / "memory.md").write_text(
        "- Prefer file-backed state for long runs", encoding="utf-8",
    )
    _reset_todos_for_tests(clear_disk=True)
    _todo_write_executor(
        {"todos": [{"content": "resume todo", "status": "pending"}]},
        context={},
    )
    ctx = {"messages": [{"role": "user", "content": "persist this"}]}

    saved = dispatch_command("/save durable-state", ctx=ctx)
    session_id = saved.side_effect.split(":", 1)[1]
    session = sm.load(session_id)
    assert session is not None
    assert session.todos[0]["content"] == "resume todo"
    assert "durable state" in session.metadata["status_memory"]["status"]["text"]
    assert "file-backed state" in session.metadata["status_memory"]["memory"]["text"]
    assert session.metadata["recovery"]["last_turn_path"].endswith("last_turn.json")

    _reset_todos_for_tests()
    ctx["messages"] = []
    resumed = dispatch_command(f"/resume {session_id}", ctx=ctx)

    assert resumed.side_effect == f"session_resumed:{session_id}"
    assert ctx["messages"] == [{"role": "user", "content": "persist this"}]
    restored = json.loads(_todo_read_executor({}, context={}))
    assert restored[0]["content"] == "resume todo"


def test_agent_refreshes_status_and_memory_every_run(tmp_path, monkeypatch):
    from agent import Agent
    from runtime.bedrock_client import Response
    from runtime.config import CONFIG

    class _SpyClient:
        def __init__(self):
            self.system_prompts = []

        def chat(
            self,
            messages,
            system,
            tools,
            max_tokens,
            temperature,
            thinking_enabled,
            thinking_budget,
        ):
            self.system_prompts.append(system)
            return Response(
                text="ok",
                tool_calls=[],
                stop_reason="end_turn",
                usage={},
            )

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "status_doc", "AGENT_STATUS.md")
    monkeypatch.setattr(CONFIG, "enable_status_doc", True)
    monkeypatch.setattr(CONFIG, "disable_local_traces", False)
    (tmp_path / "AGENT_STATUS.md").write_text("status v1", encoding="utf-8")
    (tmp_path / "memory.md").write_text("memory v1", encoding="utf-8")

    client = _SpyClient()
    agent = Agent(client=client)
    agent.run("first")

    (tmp_path / "AGENT_STATUS.md").write_text("status v2", encoding="utf-8")
    (tmp_path / "memory.md").write_text("memory v2", encoding="utf-8")
    agent.run("second")

    assert "status v1" in client.system_prompts[0]
    assert "memory v1" in client.system_prompts[0]
    assert "status v2" in client.system_prompts[1]
    assert "memory v2" in client.system_prompts[1]
    assert "status v1" not in client.system_prompts[1]
    assert (tmp_path / ".sageagent_state" / "turn_journal.jsonl").is_file()
    assert (tmp_path / ".sageagent_state" / "last_turn.json").is_file()


def test_save_can_run_zero_cost_memory_extraction_path(tmp_path, monkeypatch):
    from commands import dispatch_command
    from runtime.config import CONFIG
    import runtime.session as session_mod

    monkeypatch.setattr(CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(CONFIG, "sessions_dir", str(tmp_path / "sessions"))
    monkeypatch.setattr(CONFIG, "enable_memory_extraction", True)
    monkeypatch.setattr(CONFIG, "disable_local_traces", False)
    sm = session_mod.SessionManager(sessions_dir=str(tmp_path / "sessions"))
    monkeypatch.setattr(session_mod, "SESSIONS", sm)

    def extract_fn(messages, manifest):
        assert messages
        return ["Save command records durable memory extraction path"]

    ctx = {
        "messages": [{"role": "user", "content": "remember this"}],
        "memory_extract_fn": extract_fn,
    }
    saved = dispatch_command("/save memory-path", ctx=ctx)
    assert saved.side_effect.startswith("session_saved:")
    assert "durable memory extraction path" in (
        tmp_path / "memory.md"
    ).read_text(encoding="utf-8")
