import os
import sys
import time
from pathlib import Path


AGENT_DIR = os.path.join(os.path.dirname(__file__), "..", "agent")
sys.path.insert(0, AGENT_DIR)

import sagemaker_agent as sa


def _reset_file_tracking():
    sa.FILE_CACHE.clear_all()
    with sa._FILES_READ_LOCK:
        sa._FILES_READ.clear()
        sa._FILE_READ_TIMES.clear()
        sa._FILE_PARTIAL_READS.clear()


def test_file_unchanged_stub_wins_before_generic_in_context_hint(tmp_path, monkeypatch):
    monkeypatch.setattr(sa.CONFIG, "workspace", str(tmp_path))
    monkeypatch.setattr(sa.SECURITY, "workspace", Path(tmp_path))
    file_path = tmp_path / "sample.py"
    file_path.write_text("print('hello')\n", encoding="utf-8")

    _reset_file_tracking()

    first = sa.tool_read_file({"file_path": str(file_path)})
    second = sa.tool_read_file({"file_path": str(file_path)})

    assert "hello" in first
    assert sa.FILE_UNCHANGED_STUB in second
    assert "File already in context" not in second


class _PromptTooLongClient:
    model_id = "mock-model"

    def __init__(self, max_messages_before_error):
        self.max_messages_before_error = max_messages_before_error
        self.calls = []

    def chat(self, messages, system, tools, max_tokens, temperature):
        self.calls.append(messages)
        if len(messages) > self.max_messages_before_error:
            raise Exception("Prompt too long for summary retry test")
        return sa.Response(
            text="Recovered summary",
            tool_calls=[],
            stop_reason="end_turn",
            usage={},
        )


def test_compactor_retries_prompt_too_long_by_truncating_head():
    messages = []
    for idx in range(18):
        role = "user" if idx % 2 == 0 else "assistant"
        messages.append({"role": role, "content": f"message {idx} " + ("x" * 200)})

    client = _PromptTooLongClient(max_messages_before_error=18)
    summary = sa.Compactor.create_llm_summary(client, messages)

    assert summary == "Recovered summary"
    assert len(client.calls) >= 2
    assert len(client.calls[-1]) < len(client.calls[0])


class _TwoTurnClient:
    model_id = "mock-model"

    def __init__(self):
        self.calls = 0

    def chat(self, messages, system, tools, max_tokens, temperature, thinking_enabled, thinking_budget):
        self.calls += 1
        if self.calls == 1:
            return sa.Response(
                text="Running read-only tools",
                tool_calls=[
                    sa.ToolCall(id="t1", name="read_file", input={"file_path": "a.py"}),
                    sa.ToolCall(id="t2", name="glob", input={"pattern": "*.py", "path": "."}),
                ],
                stop_reason="tool_use",
                usage={},
            )
        return sa.Response(text="Done", tool_calls=[], stop_reason="end_turn", usage={})


def test_parallel_read_only_tools_execute_concurrently(monkeypatch):
    original_read = sa.TOOLS["read_file"]
    original_glob = sa.TOOLS["glob"]

    def slow_read(_args):
        time.sleep(0.25)
        return "read ok"

    def slow_glob(_args):
        time.sleep(0.25)
        return "glob ok"

    monkeypatch.setitem(
        sa.TOOLS,
        "read_file",
        (
            slow_read,
            False,
            "slow read",
            {"type": "object", "properties": {"file_path": {"type": "string"}}, "required": ["file_path"]},
        ),
    )
    monkeypatch.setitem(
        sa.TOOLS,
        "glob",
        (
            slow_glob,
            False,
            "slow glob",
            {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]},
        ),
    )

    agent = sa.Agent(_TwoTurnClient(), session_id="parallel-test", on_approval=lambda *_args, **_kwargs: True)

    started = time.perf_counter()
    result = agent.run("run the tools", output_fn=lambda *_args, **_kwargs: None, system_prompt="test", max_turns_override=3)
    elapsed = time.perf_counter() - started

    assert result == "Done"
    assert elapsed < 0.45
