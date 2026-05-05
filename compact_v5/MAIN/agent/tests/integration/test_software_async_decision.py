"""SOFTWARE-ASYNC-DECISION lock tests.

The third deep scan decides that v5.0.1 should not claim true background
subagents. The `task` tool remains synchronous and one-shot; strengthened
supervision lands in SOFTWARE-SUBAGENT.
"""
from __future__ import annotations


def test_task_tool_declares_sync_one_shot_no_background_contract():
    from tools import all_registered, bootstrap_built_ins, find_tool_by_name
    from tools.registry import _reset_registry_for_tests

    _reset_registry_for_tests()
    bootstrap_built_ins()

    task_tool = find_tool_by_name(all_registered(), "task")
    assert task_tool is not None
    assert task_tool.is_concurrency_safe is False

    props = set(task_tool.input_schema.get("properties", {}).keys())
    forbidden_async_fields = {
        "async",
        "background",
        "job_id",
        "poll",
        "wait",
        "kill",
    }
    assert props.isdisjoint(forbidden_async_fields)

    description = task_tool.description.lower()
    assert "runs to completion" in description
    assert "one-shot" in description
    assert "final answer" in description


def test_coordinator_docs_state_async_channel_is_not_in_v5():
    import coordinator

    doc = (coordinator.__doc__ or "").lower()
    assert "no async sub-agent" in doc
    assert "run sync to completion" in doc
