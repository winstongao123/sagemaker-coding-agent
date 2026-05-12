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
    return ui


def test_turn_meta_does_not_duplicate_thinking_after_answer():
    ui = _ui()
    html = ui._render_turn_meta(
        {
            "input_tokens": 100,
            "output_tokens": 20,
            "cache_read": 10,
            "cache_write": 5,
            "api_calls": 1,
            "cost_usd": 0.01,
            "cache_saved_usd": 0.02,
            "thinking": "private reasoning trace",
            "reasoning_state": "Thinking ON (budget 1024)",
        },
        ui._colors(),
    )
    assert "private reasoning trace" not in html
    assert "Reasoning / thinking captured for this turn" not in html
    assert "Prompt Cache R/W 10/5" in html


def test_live_thinking_renders_before_assistant_and_metrics():
    ui = _ui()
    streamed = []
    ui._render_status = lambda: None
    ui._live_output_router("[thinking]\nchoose next safe tool", streamed)
    ui._append_message("assistant", "Answer", {"input_tokens": 1, "output_tokens": 2})
    html = ui._chat_display.value
    assert "Reasoning / thinking" in html
    assert "choose next safe tool" in html
    assert html.index("Reasoning / thinking") < html.index("Answer")
    assert html.index("Reasoning / thinking") < html.index("sageagent-turn-metrics")
    assert "<details open" not in html


def test_standalone_thinking_card_is_collapsed():
    ui = _ui()
    ui._messages.append(("thinking", "expanded text should stay hidden", "12:00:00", {}))
    ui._render_chat()
    assert "Reasoning / thinking" in ui._chat_display.value
    assert "<details open" not in ui._chat_display.value


if __name__ == "__main__":
    test_turn_meta_does_not_duplicate_thinking_after_answer()
    test_live_thinking_renders_before_assistant_and_metrics()
    test_standalone_thinking_card_is_collapsed()
    print("ui thinking smoke: OK")
