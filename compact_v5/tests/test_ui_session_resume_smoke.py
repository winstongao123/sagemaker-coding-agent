from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.chat_ui import V4WidgetChatUI


class _HTML:
    value = ""


class _Agent:
    def __init__(self, messages):
        self._messages = messages

    @property
    def messages(self):
        return list(self._messages)


def _ui(messages):
    ui = V4WidgetChatUI.__new__(V4WidgetChatUI)
    ui.agent = _Agent(messages)
    ui._messages = []
    ui._dark_mode = True
    ui._chat_height = 500
    ui._chat_display = _HTML()
    ui._tool_card_indices = {}
    return ui


def test_resume_rehydrates_visible_chat_from_saved_engine_messages():
    saved = [
        {"role": "user", "content": "list my s3 buckets"},
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "aws_s3_list",
                    "input": {},
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "toolu_1",
                    "_sageagent_tool_name": "aws_s3_list",
                    "content": "S3 buckets:\n- s3://example/",
                }
            ],
        },
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Here is the bucket structure."},
            ],
        },
    ]
    ui = _ui(saved)

    ui._rehydrate_visible_messages_from_agent()

    roles = [row[0] for row in ui._messages]
    assert roles == ["user", "tool", "assistant"]
    html = ui._chat_display.value
    assert "list my s3 buckets" in html
    assert "aws_s3_list" in html
    assert "S3 buckets:" in html
    assert "Here is the bucket structure." in html
    assert "sageagent-tool-card" in html


if __name__ == "__main__":
    test_resume_rehydrates_visible_chat_from_saved_engine_messages()
    print("ui session resume smoke: OK")
