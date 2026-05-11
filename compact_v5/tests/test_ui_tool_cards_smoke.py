from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.chat_ui import V4WidgetChatUI


class _HTML:
    value = ""


def _ui():
    ui = V4WidgetChatUI.__new__(V4WidgetChatUI)
    ui._messages = []
    ui._dark_mode = True
    ui._chat_height = 500
    ui._chat_display = _HTML()
    ui._tool_card_indices = {}
    return ui


def test_tool_card_html_is_collapsed_and_grouped():
    ui = _ui()
    call = {
        "type": "tool_generation",
        "tool_use_id": "toolu_1",
        "name": "aws_s3_list",
        "input": {"bucket": "example"},
    }
    result = {
        "type": "tool_result",
        "tool_use_id": "toolu_1",
        "name": "aws_s3_list",
        "content": "Buckets:\n- example",
        "is_error": False,
    }
    ui._append_tool_call_card(call)
    ui._append_or_update_tool_result_card(result)

    assert len(ui._messages) == 1
    html = ui._chat_display.value
    assert "sageagent-tool-card" in html
    assert "<details class='sageagent-tool-card'" in html
    assert "<details open" not in html
    assert "Tool input" in html
    assert "Tool result" in html
    assert "aws_s3_list" in html
    assert "Buckets:" in html


def test_tool_card_error_unknown_and_clear_paths():
    ui = _ui()
    call = {
        "type": "tool_generation",
        "tool_use_id": "old_id",
        "name": "bash",
        "input": {"command": "aws s3 ls"},
    }
    ui._append_tool_call_card(call)
    assert ui._tool_card_indices["old_id"] == 0

    ui._messages.clear()
    ui._tool_card_indices.clear()
    ui._append_message("assistant", "new turn")
    idx = ui._append_or_update_tool_result_card({
        "type": "tool_result",
        "tool_use_id": "old_id",
        "name": "bash",
        "content": "Blocked: AWS S3 CLI is blocked by the bash allowlist",
        "is_error": True,
    })

    assert idx == 1
    assert len(ui._messages) == 2
    html = ui._chat_display.value
    assert ">error</span>" in html
    assert "Blocked: AWS S3 CLI" in html
    assert "new turn" in html

    stale = _ui()
    stale._append_message("assistant", "unrelated assistant")
    stale._tool_card_indices["stale_id"] = 0
    appended = stale._append_or_update_tool_result_card({
        "type": "tool_result",
        "tool_use_id": "stale_id",
        "name": "bash",
        "content": "Blocked: stale result",
        "is_error": True,
    })
    assert appended == 1
    assert len(stale._messages) == 2
    assert stale._messages[0][0] == "assistant"


def test_tool_card_stream_result_and_truncation_render_as_result():
    ui = _ui()
    ui._live_assistant_index = None
    streamed = []
    ui._render_status = lambda: None
    ui._live_output_router("[aws_s3_list result]: bucket-a", streamed)
    assert "Tool result" in ui._chat_display.value
    assert "bucket-a" in ui._chat_display.value
    assert ">done</span>" in ui._chat_display.value
    assert "stream-only; input not captured" in ui._chat_display.value

    long_ui = _ui()
    long_body = "x" * 13000
    long_ui._append_or_update_tool_result_card({
        "type": "tool_result",
        "tool_use_id": "",
        "name": "aws_s3_list",
        "content": long_body,
        "is_error": False,
    })
    assert "tool result truncated in UI" in long_ui._chat_display.value


if __name__ == "__main__":
    test_tool_card_html_is_collapsed_and_grouped()
    test_tool_card_error_unknown_and_clear_paths()
    test_tool_card_stream_result_and_truncation_render_as_result()
    print("ui tool cards smoke: OK")
