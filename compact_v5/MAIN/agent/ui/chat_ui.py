"""V5 ui/chat_ui.py — minimal chat UI factory (Phase 11, ADR-017).

Provides `create_chat_ui(...)` which:
1. Builds an `Agent` from `runtime.config.CONFIG`.
2. Constructs `IterationBudgetWidget` + `ThinkingBudgetWidget`.
3. Wires Send / Stop / Clear buttons into the agent.
4. Returns a `ChatUI` handle for the notebook to `display()`.

ADAPT port of v4's `create_chat_ui` (sagemaker_agent.py:9735, ~2000 LOC).
v5 Phase-11 ships the minimal MVP per ADR-017 OUT-OF-SCOPE list:
- No full chat-display HTML rendering (defer to Phase 13 polish).
- No compact / clean buttons (microcompact lands later if at all).
- No model-switcher widget.
- No session auto-restore.

ipywidgets-dependent — falls back to a console mode (`ConsoleChatUI`) when
ipywidgets isn't available so tests + CI can exercise the factory.

PORT_LOG: #030.
"""
from __future__ import annotations

import logging
from typing import Any, Optional


def _invoke_dream(agent: Any) -> str:
    """Block H+ — actually invoke the /dream consolidation engine when
    cmd_dream's side-effect fires.

    Builds a real-LLM consolidator from the parent's BedrockClient,
    dispatches runtime.dream.run_dream(...), and returns a one-line
    status for the chat surface to show the user. Best-effort: errors
    are caught and reported as text.
    """
    try:
        from runtime.config import CONFIG
        from runtime.dream import run_dream, get_dream_prompt
    except Exception as exc:  # noqa: BLE001
        return f"[/dream] could not load consolidation engine: {exc}"

    def _llm_consolidator(existing: str, manifest: str) -> str:
        prompt = get_dream_prompt(existing, manifest)
        try:
            client = getattr(agent, "client", None)
            if client is None:
                return ""
            resp = client.chat(
                messages=[{"role": "user", "content": prompt}],
                system="You are a memory consolidator.",
                tools=[],
                max_tokens=4096,
                temperature=0.0,
                thinking_enabled=False,
                thinking_budget=4096,
            )
            text = getattr(resp, "text", "") or ""
            return text
        except Exception as inner:  # noqa: BLE001
            logging.warning(f"[/dream] consolidator raised: {inner}")
            return ""

    try:
        result = run_dream(
            workspace=CONFIG.workspace,
            consolidator=_llm_consolidator,
        )
    except Exception as exc:  # noqa: BLE001
        return f"[/dream] failed: {type(exc).__name__}: {exc}"

    if result.success:
        if result.new_content:
            return (
                f"[/dream] completed phases: "
                f"{', '.join(result.phases_executed)}. "
                f"Backup at {result.backup_path or '(none)'}."
            )
        # Dry-run / empty consolidator path.
        return (
            f"[/dream] dry-run: phases recorded "
            f"({', '.join(result.phases_executed)}). "
            "No content change."
        )
    return f"[/dream] failed: {result.error}"

from .widgets import IterationBudgetWidget, ThinkingBudgetWidget, _IPYWIDGETS_OK


# ============================================================
# ConsoleChatUI — fallback when ipywidgets is unavailable
# ============================================================

class ConsoleChatUI:
    """Plain-stdout fallback. Sufficient for CI / SageMaker base images
    that strip notebook deps."""

    def __init__(self, agent: Any):
        self.agent = agent
        self.budget_widget = IterationBudgetWidget(budget=agent.budget)
        self.thinking_widget = ThinkingBudgetWidget(agent=agent)

    def send(self, message: str) -> str:
        """Send a user message; return the agent's final text.

        Block D (PORT_LOG #065): if the message starts with `/`, route
        it through the slash-command dispatcher BEFORE invoking the
        agent loop. /auth gates can short-circuit a turn entirely.
        """
        # Block D — slash-command dispatch.
        if message.startswith("/"):
            try:
                from commands import is_command, dispatch_command
                if is_command(message):
                    cr = dispatch_command(message)
                    if cr.consumed:
                        # Block H+ — /dream side-effect: actually invoke
                        # the consolidation engine. Chat UI is the user-
                        # facing trigger surface; the engine lives in
                        # runtime/dream.py.
                        if cr.side_effect == "dream_invoked":
                            return cr.text + "\n" + _invoke_dream(self.agent)
                        return cr.text
            except Exception as _cmd_exc:
                # Best-effort: fall through to agent.run() if dispatch fails.
                import logging as _lg
                _lg.warning(f"slash-command dispatch error: {_cmd_exc}")

        result = self.agent.run(message)
        # Print the budget snapshot so the operator can see consumption.
        try:
            print(self.budget_widget.render_html())
        except Exception:
            pass
        return result.text

    def stop(self) -> None:
        self.agent.stop()

    def clear(self, reset_budget: bool = False) -> None:
        self.agent.clear(reset_budget=reset_budget)

    def render(self) -> Any:
        """Return a renderable handle.

        Codex Phase-11 finding (medium): the prior version returned a raw
        HTML string. `display(<str>)` shows the literal string, not rendered
        HTML — so the notebook's launch cell rendered escaped markup
        instead of a UI. Fix: when `IPython.display.HTML` is available
        (which it is in any Jupyter / SageMaker kernel), wrap the string
        so `display(ui.render())` shows actual HTML. When IPython.display
        isn't available (pure-Python tests), return the raw string for
        the test to still inspect.
        """
        html = (
            "<div style='font-family:sans-serif;'>"
            "<b>v5 Console ChatUI</b> "
            "(ipywidgets not available — using fallback)"
            "<br>" + self.budget_widget.render_html() +
            "<br>" + self.thinking_widget.render_html() +
            "</div>"
        )
        try:
            from IPython.display import HTML
            return HTML(html)
        except Exception:
            return html

    def render_html(self) -> str:
        """Return the raw HTML string (used by tests + by render()'s wrap)."""
        return (
            "<div style='font-family:sans-serif;'>"
            "<b>v5 Console ChatUI</b> "
            "(ipywidgets not available — using fallback)"
            "<br>" + self.budget_widget.render_html() +
            "<br>" + self.thinking_widget.render_html() +
            "</div>"
        )


# ============================================================
# WidgetChatUI — ipywidgets path
# ============================================================

class WidgetChatUI:
    """ipywidgets-backed Chat UI. Wires Send / Stop / Clear buttons into
    the agent, rendering output via ipywidgets.Output."""

    def __init__(self, agent: Any):
        self.agent = agent
        self.budget_widget = IterationBudgetWidget(budget=agent.budget)
        self.thinking_widget = ThinkingBudgetWidget(agent=agent)
        self._build()

    def _build(self) -> None:
        import ipywidgets as widgets  # local import — only on the WidgetChatUI path
        self._input = widgets.Textarea(
            placeholder="Type a message and press Send…",
            layout={"width": "100%", "height": "60px"},
        )
        self._output = widgets.Output(layout={"width": "100%"})
        self._send_btn = widgets.Button(description="Send", button_style="primary")
        self._stop_btn = widgets.Button(description="Stop", button_style="warning")
        self._clear_btn = widgets.Button(description="Clear", button_style="")

        self._send_btn.on_click(self._on_send)
        self._stop_btn.on_click(self._on_stop)
        self._clear_btn.on_click(self._on_clear)

        self._budget_handle = self.budget_widget.render()
        self._thinking_handle = self.thinking_widget.render()

        self._panel = widgets.VBox([
            widgets.HBox([self._budget_handle, self._thinking_handle]),
            self._input,
            widgets.HBox([self._send_btn, self._stop_btn, self._clear_btn]),
            self._output,
        ])

    def _on_send(self, _btn) -> None:
        msg = (self._input.value or "").strip()
        if not msg:
            return
        self._input.value = ""
        with self._output:
            print(f"\n>>> user: {msg}")
            try:
                # Block D — slash-command dispatch BEFORE agent loop.
                if msg.startswith("/"):
                    try:
                        from commands import is_command, dispatch_command
                        if is_command(msg):
                            cr = dispatch_command(msg)
                            if cr.consumed:
                                print(cr.text)
                                # Block H+ — /dream side-effect actually
                                # invokes the consolidation engine.
                                if cr.side_effect == "dream_invoked":
                                    print(_invoke_dream(self.agent))
                                return
                    except Exception as _cmd_exc:
                        logging.warning(
                            f"[chat-ui] slash-command dispatch error: {_cmd_exc}"
                        )
                result = self.agent.run(msg, output_fn=lambda s: print(s))
                print(f"\nstop_reason: {result.stop_reason}")
            except Exception as exc:  # noqa: BLE001 — never crash the UI
                logging.exception("[chat-ui] agent.run() raised")
                print(f"[chat-ui] error: {type(exc).__name__}: {exc}")
            finally:
                # Push the budget update so the bar reflects the latest state.
                self.budget_widget.update()
                self.thinking_widget.refresh()

    def _on_stop(self, _btn) -> None:
        self.agent.stop()
        with self._output:
            print("[stop requested]")

    def _on_clear(self, _btn) -> None:
        self.agent.clear()
        self._output.clear_output()
        self.budget_widget.update()

    def render(self) -> Any:
        """Return the top-level VBox the notebook should `display()`."""
        return self._panel


# ============================================================
# create_chat_ui — public factory
# ============================================================

def create_chat_ui(
    agent: Optional[Any] = None,
    mock_mode: Optional[bool] = None,
    skill_manager: Optional[Any] = None,
) -> Any:
    """Build a chat UI bound to the given (or freshly constructed) Agent.

    Args:
        agent: pre-built Agent. If None, a new one is constructed using
            `CONFIG` + `BedrockClient`. The lazy path also picks up
            `mock_mode` when supplied.
        mock_mode: override CONFIG.mock_mode for the lazy path. Ignored
            when `agent` is supplied.
        skill_manager: optional SkillManager for the lazy path.

    Returns:
        A `WidgetChatUI` when ipywidgets is available, otherwise a
        `ConsoleChatUI`.
    """
    if agent is None:
        from agent import Agent
        from core import IterationBudget
        from runtime.bedrock_client import BedrockClient
        from runtime.config import CONFIG
        if mock_mode is not None:
            CONFIG.mock_mode = bool(mock_mode)
        client = BedrockClient(
            model_id=CONFIG.model_id,
            region=CONFIG.region,
            mock_mode=CONFIG.mock_mode,
        )
        # Codex Phase-11 finding (high): thread CONFIG.max_turns +
        # CONFIG.max_iteration_budget into lazy Agent construction.
        # Without these, the notebook's CONFIG values never reach the
        # runtime turn ceiling / cost-ceiling guards.
        max_turns = int(getattr(CONFIG, "max_turns", 50))
        budget_max = int(getattr(CONFIG, "max_iteration_budget", IterationBudget.DEFAULT_MAX))
        agent = Agent(
            client=client,
            max_turns=max_turns,
            budget=IterationBudget(max_iterations=budget_max),
            skill_manager=skill_manager,
            thinking_enabled=getattr(CONFIG, "thinking_enabled", False),
            thinking_budget=getattr(CONFIG, "thinking_budget", 4096),
        )

    if _IPYWIDGETS_OK:
        return WidgetChatUI(agent)
    return ConsoleChatUI(agent)
