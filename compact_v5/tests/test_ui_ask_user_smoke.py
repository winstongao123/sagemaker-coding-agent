from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.chat_ui import V4WidgetChatUI


class _Layout:
    display = "none"


class _Widget:
    def __init__(self, value=""):
        self.value = value
        self.placeholder = ""
        self.disabled = False
        self.layout = _Layout()


class _Agent:
    _stop_requested = False


def _ui():
    ui = V4WidgetChatUI.__new__(V4WidgetChatUI)
    ui.agent = _Agent()
    ui._pending_user_input = {"result": None, "event": None, "active": False}
    ui._dark_mode = True
    ui._ask_user_prompt = _Widget()
    ui._ask_user_input = _Widget()
    ui._ask_user_box = _Widget()
    ui._input = _Widget()
    ui._send_btn = _Widget()
    ui._status_html = _Widget()
    ui._messages = []
    ui._append_message = lambda role, content, meta=None, tool_name="": ui._messages.append((role, content))
    return ui


def _wait_until(predicate, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_ask_user_prompt_renders_and_submit_returns_answer():
    ui = _ui()
    result = {}
    thread = threading.Thread(
        target=lambda: result.setdefault("value", ui._request_user_input("Which bucket should I inspect?")),
        daemon=True,
    )
    thread.start()

    assert _wait_until(lambda: ui._pending_user_input["active"])
    assert ui._ask_user_box.layout.display == ""
    assert "Agent Question" in ui._ask_user_prompt.value
    assert "Which bucket should I inspect?" in ui._ask_user_prompt.value

    ui._ask_user_input.value = "data-bucket"
    ui._on_ask_user_submit(None)
    thread.join(timeout=2)

    assert result["value"] == "data-bucket"
    assert ui._ask_user_box.layout.display == "none"
    assert ("system", "User answered: data-bucket") in ui._messages


def test_ask_user_accepts_main_send_as_fallback():
    ui = _ui()
    result = {}
    thread = threading.Thread(
        target=lambda: result.setdefault("value", ui._request_user_input("Confirm path")),
        daemon=True,
    )
    thread.start()

    assert _wait_until(lambda: ui._pending_user_input["active"])
    ui._input.value = "/home/sagemaker-user/project"
    ui._on_send(None)
    thread.join(timeout=2)

    assert result["value"] == "/home/sagemaker-user/project"
    assert ui._pending_user_input["active"] is False


def test_query_engine_dispatch_passes_ask_user_provider_to_tool():
    from types import SimpleNamespace

    from core.query_engine import QueryEngine
    from core.budget import IterationBudget
    from tools.ask_user import _register as register_ask_user
    from tools.registry import all_registered

    register_ask_user()
    engine = QueryEngine(client=object(), budget=IterationBudget())
    # _dispatch_single_tool_call normally runs after QueryEngine.run initializes
    # these per-run counters; set them explicitly for this focused smoke test.
    engine._exec_call_count = 0
    engine._recent_tool_calls = []

    seen = {}

    def provider(prompt: str) -> str:
        seen["prompt"] = prompt
        return "answer from ui"

    result = engine._dispatch_single_tool_call(
        SimpleNamespace(
            id="ask_1",
            name="ask_user",
            input={"question": "Which bucket?", "options": ["all", "one"]},
        ),
        tools=all_registered(),
        plan_mode=False,
        output_fn=lambda _text: None,
        ask_user_response_provider=provider,
    )

    assert seen["prompt"].startswith("Which bucket?")
    assert "Options:" in seen["prompt"]
    assert result["content"] == "answer from ui"
    assert result["tool_use_id"] == "ask_1"


if __name__ == "__main__":
    test_ask_user_prompt_renders_and_submit_returns_answer()
    test_ask_user_accepts_main_send_as_fallback()
    test_query_engine_dispatch_passes_ask_user_provider_to_tool()
    print("ui ask_user smoke: OK")
