from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent import Agent, _is_simple_s3_inventory_request
from core.query_engine import QueryEngine, QueryResult
from runtime.config import CONFIG
from tools.registry import apply_tool_search_deferral
from tools.aws_s3_list import _register as register_aws_s3_list
from tools.tool_search import _register as register_tool_search


def test_simple_s3_inventory_turn_disables_thinking_only_for_that_turn():
    captured = {}
    outputs = []
    agent = Agent(client=object(), thinking_enabled=True)

    def fake_run(**kwargs):
        captured["thinking_enabled"] = kwargs["thinking_enabled"]
        return QueryResult(text="ok", stop_reason="end_turn")

    original_flag = CONFIG.disable_thinking_for_simple_s3_inventory
    try:
        CONFIG.disable_thinking_for_simple_s3_inventory = True
        agent._engine.run = fake_run
        agent.run(
            "list file and bucket structure of my s3",
            tools=[],
            output_fn=outputs.append,
        )
        assert captured["thinking_enabled"] is False
        assert agent.last_effective_thinking_enabled is False
        assert agent.last_prompt_metrics.get("thinking_enabled") is False
        assert any("Extended Thinking disabled" in line for line in outputs)

        outputs.clear()
        agent.run("explain compact_v5 architecture", tools=[], output_fn=outputs.append)
        assert captured["thinking_enabled"] is True
        assert agent.last_effective_thinking_enabled is True
    finally:
        CONFIG.disable_thinking_for_simple_s3_inventory = original_flag


def test_simple_s3_inventory_detector_is_narrow():
    assert _is_simple_s3_inventory_request("list file and bucket structure of my s3")
    assert not _is_simple_s3_inventory_request("delete objects from my s3 bucket")
    assert not _is_simple_s3_inventory_request("fix code that reads from s3")


def test_aws_s3_list_is_visible_without_tool_search():
    aws_s3_list = register_aws_s3_list()
    tool_search = register_tool_search()
    visible, deferred = apply_tool_search_deferral([aws_s3_list, tool_search], enabled=True)
    visible_names = {tool.name for tool in visible}
    assert "aws_s3_list" in visible_names
    assert "tool_search" in visible_names
    assert "aws_s3_list" not in deferred


def test_bash_s3_cli_retry_is_one_strike_blocked():
    engine = QueryEngine(client=object())
    command_args = {"command": "aws s3 ls"}
    failure_key = engine._tool_failure_key("bash", command_args)
    engine._record_tool_failure(
        "bash",
        failure_key,
        "Blocked: AWS S3 CLI is blocked by the bash allowlist. Use the `aws_s3_list` tool.",
    )

    failure_class = engine._predict_guard_failure_class("bash", command_args)
    assert failure_class == "bash_aws_s3_cli_blocked"
    assert engine._tool_failure_class_counts[("bash", failure_class)] == 1
    message = engine._failure_class_block_message("bash", failure_class, 1)
    assert "aws_s3_list" in message
    assert "Stop retrying" in message


if __name__ == "__main__":
    test_simple_s3_inventory_turn_disables_thinking_only_for_that_turn()
    test_simple_s3_inventory_detector_is_narrow()
    test_aws_s3_list_is_visible_without_tool_search()
    test_bash_s3_cli_retry_is_one_strike_blocked()
    print("s3 cost controls smoke: OK")
