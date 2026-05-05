"""SOFTWARE-RESULTS lock tests.

Large tool outputs must remain inspectable after model-visible replacement.
"""
from __future__ import annotations

import os
import re
import sys


_AGENT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _AGENT_ROOT not in sys.path:
    sys.path.insert(0, _AGENT_ROOT)


def _configure_workspace(tmp_path):
    from runtime.config import CONFIG

    old_workspace = CONFIG.workspace
    old_traces = CONFIG.disable_local_traces
    CONFIG.workspace = str(tmp_path)
    CONFIG.disable_local_traces = False
    return old_workspace, old_traces


def _restore_workspace(saved):
    from runtime.config import CONFIG

    old_workspace, old_traces = saved
    CONFIG.workspace = old_workspace
    CONFIG.disable_local_traces = old_traces


def _extract_refs(blocks):
    refs = []
    for block in blocks:
        text = block.get("content", "")
        refs.extend(re.findall(r"sageagent-result://[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", text))
    return list(dict.fromkeys(refs))


def test_per_tool_large_result_persists_and_replays(tmp_path):
    from core.query_engine import QueryEngine
    from runtime.bedrock_client import Response, ToolCall
    from runtime.results import RESULTS
    from tools.registry import build_tool
    from tools.result_replay import _execute as replay_result

    saved = _configure_workspace(tmp_path)
    try:
        payload = "START-" + ("x" * 5000) + "-END"

        class _Client:
            mock_mode = True

            def __init__(self):
                self.turn = 0

            def chat(self, *args, **kwargs):
                self.turn += 1
                if self.turn == 1:
                    return Response(
                        "",
                        [ToolCall("r1", "read_file", {"file_path": "big.txt"})],
                        "tool_use",
                        {},
                    )
                return Response("done", [], "end_turn", {})

        tool = build_tool(
            "read_file",
            "read",
            {},
            lambda args, context=None: payload,
            is_read_only=True,
            is_concurrency_safe=True,
            max_result_size_chars=1000,
        )
        engine = QueryEngine(_Client(), max_turns=3, session_id="soft-results")
        result = engine.run("go", "sys", [tool], output_fn=lambda _: None)

        tool_blocks = result.messages[-2]["content"]
        refs = _extract_refs(tool_blocks)
        assert len(refs) == 1
        assert "tool_result persisted" in tool_blocks[0]["content"]
        assert "result_replay" in tool_blocks[0]["content"]
        assert "START-" in tool_blocks[0]["content"]
        assert "-END" in tool_blocks[0]["content"]

        artifact_path = RESULTS.resolve(refs[0])
        assert artifact_path is not None and artifact_path.is_file()
        assert artifact_path.read_text(encoding="utf-8") == payload
        assert replay_result({"ref": refs[0], "offset": 0, "limit": 20}).startswith("START-")
        assert replay_result({"ref": refs[0], "offset": len(payload) - 4, "limit": 4}) == "-END"
    finally:
        _restore_workspace(saved)


def test_aggregate_tool_result_budget_persists_every_replaced_result(tmp_path):
    from core.query_engine import QueryEngine
    from runtime.bedrock_client import Response, ToolCall
    from runtime.tool_surface import TOOL_RESULT_BUDGET_MARKER
    from tools.registry import build_tool
    from tools.result_replay import _execute as replay_result

    saved = _configure_workspace(tmp_path)
    try:
        payloads = {
            "a.txt": "A" * 150_000,
            "b.txt": "B" * 150_000,
        }

        class _Client:
            mock_mode = True

            def __init__(self):
                self.turn = 0

            def chat(self, *args, **kwargs):
                self.turn += 1
                if self.turn == 1:
                    return Response(
                        "",
                        [
                            ToolCall("a", "read_file", {"file_path": "a.txt"}),
                            ToolCall("b", "read_file", {"file_path": "b.txt"}),
                        ],
                        "tool_use",
                        {},
                    )
                return Response("done", [], "end_turn", {})

        def _read(args, context=None):
            return payloads[args["file_path"]]

        tool = build_tool(
            "read_file",
            "read",
            {},
            _read,
            is_read_only=True,
            is_concurrency_safe=True,
            max_result_size_chars=250_000,
        )
        engine = QueryEngine(_Client(), max_turns=3, session_id="soft-results-aggregate")
        result = engine.run("go", "sys", [tool], output_fn=lambda _: None)

        tool_blocks = result.messages[-2]["content"]
        refs = _extract_refs(tool_blocks)
        assert len(refs) == 2
        assert all("message_budget>200000" in block["content"] for block in tool_blocks)
        assert TOOL_RESULT_BUDGET_MARKER not in "\n".join(block["content"] for block in tool_blocks)
        assert replay_result({"ref": refs[0], "offset": 0, "limit": 3}) in {"AAA", "BBB"}
        assert replay_result({"ref": refs[1], "offset": 0, "limit": 3}) in {"AAA", "BBB"}
        assert replay_result({"ref": refs[0], "offset": 149_997, "limit": 3}) in {"AAA", "BBB"}
    finally:
        _restore_workspace(saved)


def test_result_replay_tool_registered_as_read_only():
    from tools import bootstrap_built_ins
    from tools.registry import all_registered, find_tool_by_name

    bootstrap_built_ins()
    tool = find_tool_by_name(all_registered(), "result_replay")
    assert tool is not None
    assert tool.is_read_only is True
    assert tool.is_concurrency_safe is True


def test_storage_disabled_strips_internal_metadata(tmp_path):
    from runtime.config import CONFIG
    from runtime.results import persist_tool_result_block

    saved = _configure_workspace(tmp_path)
    old_traces = CONFIG.disable_local_traces
    CONFIG.disable_local_traces = True
    try:
        block = {
            "type": "tool_result",
            "tool_use_id": "x",
            "content": "large output",
            "_sageagent_tool_name": "read_file",
            "_sageagent_max_result_chars": 1,
        }
        out = persist_tool_result_block(
            block,
            session_id="disabled-traces",
            reason="test",
        )
        assert out["content"] == "large output"
        assert "_sageagent_tool_name" not in out
        assert "_sageagent_max_result_chars" not in out
    finally:
        CONFIG.disable_local_traces = old_traces
        _restore_workspace(saved)
