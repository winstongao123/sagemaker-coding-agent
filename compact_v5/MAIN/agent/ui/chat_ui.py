"""V5 ui/chat_ui.py — minimal chat UI factory (Phase 11, ADR-017).

Provides `create_chat_ui(...)` which:
1. Builds an `Agent` from `runtime.config.CONFIG`.
2. Constructs `IterationBudgetWidget` + `ThinkingBudgetWidget`.
3. Wires the v4-style notebook controls into the v5 agent.
4. Returns a `ChatUI` handle for the notebook to `display()`.

ADAPT port of v4's `create_chat_ui` (sagemaker_agent.py:9735, ~2000 LOC).
v5 keeps the v4 notebook surface for operator muscle memory:
- Session save/load/new controls.
- Model selector, sub-agent panel, plan/approval toggles.
- Thinking, budget, auto-compact, dark-mode, and chat-height controls.
- Compact/Clean actions plus token/cost/context status lines.

ipywidgets-dependent — falls back to a console mode (`ConsoleChatUI`) when
ipywidgets isn't available so tests + CI can exercise the factory.

PORT_LOG: #030.
"""
from __future__ import annotations

import logging
from datetime import datetime
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
                    cr = dispatch_command(message, ctx={"agent": self.agent})
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
                            cr = dispatch_command(msg, ctx={"agent": self.agent})
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


class V4WidgetChatUI(WidgetChatUI):
    """v4-compatible notebook surface backed by the v5 Agent."""

    def __init__(self, agent: Any):
        self.agent = agent
        self.budget_widget = IterationBudgetWidget(budget=agent.budget)
        self.thinking_widget = ThinkingBudgetWidget(agent=agent)
        self._messages = []
        self._dark_mode = True
        self._chat_height = 500
        self._build()

    @staticmethod
    def _escape(text: Any) -> str:
        import html
        return html.escape(str(text))

    def _colors(self) -> dict:
        if self._dark_mode:
            return {"bg": "#1e1e1e", "fg": "#e0e0e0", "muted": "#999", "border": "#444"}
        return {"bg": "#ffffff", "fg": "#333", "muted": "#666", "border": "#ccc"}

    def _build(self) -> None:
        import ipywidgets as widgets
        try:
            from entry import BEDROCK_MODELS
            from runtime.config import CONFIG
        except Exception:  # pragma: no cover
            BEDROCK_MODELS = [("Current model", getattr(self.agent.client, "model_id", ""))]
            CONFIG = None

        current_model = getattr(getattr(self.agent, "client", None), "model_id", "")
        values = [m[1] for m in BEDROCK_MODELS]
        default_model = current_model if current_model in values else BEDROCK_MODELS[0][1]

        self._header = widgets.HTML(value="")
        self._chat_display = widgets.HTML(value="")
        self._todo_display = widgets.HTML(value="")
        self._status_html = widgets.HTML(value="")
        self._tokens_html = widgets.HTML(value="")
        self._mode_html = widgets.HTML(value="")

        self._session_name = widgets.Text(placeholder="Session name (optional)", layout=widgets.Layout(width="200px"))
        self._save_btn = widgets.Button(description="Save", button_style="info", icon="save")
        self._session_dropdown = widgets.Dropdown(description="Session:", options=[("New Session", None)], layout=widgets.Layout(width="250px"))
        self._load_btn = widgets.Button(description="Load", button_style="info", icon="folder-open")
        self._new_btn = widgets.Button(description="New", button_style="success", icon="plus")

        self._model_dropdown = widgets.Dropdown(description="", options=BEDROCK_MODELS, value=default_model, layout=widgets.Layout(width="260px"))
        self._subagent_toggle = widgets.ToggleButton(value=False, description="Sub-Agents", icon="cogs", layout=widgets.Layout(width="180px", height="28px"))
        self._plan_mode = widgets.Checkbox(value=False, description="Plan Mode", indent=False, style={"description_width": "initial"}, layout=widgets.Layout(width="auto"))
        self._approval_toggle = widgets.Checkbox(value=bool(getattr(CONFIG, "require_tool_approval", True)), description="Require Approval", indent=False, style={"description_width": "initial"}, layout=widgets.Layout(width="auto"))
        self._explorer_dropdown = widgets.Dropdown(description="Explorer:", options=[("Default", "default"), ("Explorer", "explorer")], value="explorer", layout=widgets.Layout(width="320px"))
        self._worker_dropdown = widgets.Dropdown(description="Worker:", options=[("Default", "default"), ("Worker", "worker")], value="worker", layout=widgets.Layout(width="320px"))
        self._reviewer_dropdown = widgets.Dropdown(description="Reviewer:", options=[("Default", "default"), ("Reviewer", "reviewer")], value="reviewer", layout=widgets.Layout(width="320px"))
        self._subagent_panel = widgets.VBox([
            self._explorer_dropdown,
            self._worker_dropdown,
            self._reviewer_dropdown,
        ])
        self._subagent_panel.layout.display = "none"

        self._thinking_checkbox = widgets.Checkbox(value=bool(getattr(self.agent, "thinking_enabled", False)), description="Extended Thinking", indent=False, style={"description_width": "initial"}, layout=widgets.Layout(width="auto"))
        self._thinking_budget_slider = widgets.IntSlider(value=int(getattr(self.agent, "thinking_budget", 4096)), min=1024, max=16000, step=1024, description="Think Budget:", style={"description_width": "100px"}, layout=widgets.Layout(width="250px"), disabled=not bool(getattr(self.agent, "thinking_enabled", False)))
        self._temperature_slider = widgets.FloatSlider(value=float(getattr(CONFIG, "temperature", 0.0)), min=0.0, max=1.0, step=0.1, description="Temperature:", style={"description_width": "100px"}, layout=widgets.Layout(width="250px"))
        self._budget_input = widgets.BoundedFloatText(value=float(getattr(CONFIG, "session_cost_limit", 0.0) or 10.0), min=0.0, max=999.0, step=0.5, description="Budget $:", style={"description_width": "70px"}, layout=widgets.Layout(width="160px"))
        self._auto_compact = widgets.Checkbox(value=True, description="Auto-Compact", indent=False, layout=widgets.Layout(width="auto"))
        self._dark_toggle = widgets.Checkbox(value=True, description="Dark Mode", indent=False, style={"description_width": "initial"}, layout=widgets.Layout(width="auto"))
        self._chat_height_slider = widgets.IntSlider(value=500, min=200, max=1200, step=50, description="Chat Height:", style={"description_width": "100px"}, layout=widgets.Layout(width="250px"))

        self._input = widgets.Textarea(placeholder="Type your message...", layout=widgets.Layout(width="100%", height="80px"))
        self._send_btn = widgets.Button(description="Send", button_style="primary", icon="paper-plane")
        self._stop_btn = widgets.Button(description="Stop", button_style="danger", icon="stop", layout=widgets.Layout(display="none"))
        self._clear_btn = widgets.Button(description="Clear", button_style="warning", icon="trash")
        self._compact_btn = widgets.Button(description="Compact", button_style="", icon="compress")
        self._clean_btn = widgets.Button(
            description="Clean",
            button_style="",
            icon="eraser",
            tooltip="Remove local traces; saved sessions are kept.",
        )

        self._wire_events()
        self._build_layout(widgets)

    def _wire_events(self) -> None:
        self._send_btn.on_click(self._on_send)
        self._stop_btn.on_click(self._on_stop)
        self._clear_btn.on_click(self._on_clear)
        self._save_btn.on_click(lambda _b: self._dispatch_ui_command("/save " + self._session_name.value.strip() if self._session_name.value.strip() else "/save"))
        self._compact_btn.on_click(self._on_compact)
        self._clean_btn.on_click(self._on_clean)
        self._load_btn.on_click(lambda _b: self._dispatch_ui_command(f"/resume {self._session_dropdown.value}") if self._session_dropdown.value else None)
        self._new_btn.on_click(self._on_new)
        self._model_dropdown.observe(self._on_model_change, names="value")
        self._thinking_checkbox.observe(self._on_thinking_change, names="value")
        self._thinking_budget_slider.observe(self._on_thinking_budget_change, names="value")
        self._temperature_slider.observe(self._on_temperature_change, names="value")
        self._budget_input.observe(self._on_budget_change, names="value")
        self._chat_height_slider.observe(self._on_chat_height_change, names="value")
        self._dark_toggle.observe(self._on_dark_mode_change, names="value")
        self._plan_mode.observe(self._on_plan_mode_change, names="value")
        self._approval_toggle.observe(self._on_approval_change, names="value")
        self._auto_compact.observe(self._on_auto_compact_change, names="value")
        self._subagent_toggle.observe(self._on_subagent_preferences_change, names="value")
        self._explorer_dropdown.observe(self._on_subagent_preferences_change, names="value")
        self._worker_dropdown.observe(self._on_subagent_preferences_change, names="value")
        self._reviewer_dropdown.observe(self._on_subagent_preferences_change, names="value")
        self._on_plan_mode_change({"new": self._plan_mode.value})
        self._on_auto_compact_change({"new": self._auto_compact.value})
        # Seed the Agent with explicit disabled preferences so later toggles are
        # a normal state update, not a special first-use path.
        self._on_subagent_preferences_change({"new": self._subagent_toggle.value})

    def _build_layout(self, widgets: Any) -> None:
        style = widgets.HTML("""
<style>
.sageagent-v4-dark {
  background: #111 !important;
  color: #f5f5f5 !important;
  padding: 10px !important;
  box-sizing: border-box !important;
}
.sageagent-v4-dark .widget-label,
.sageagent-v4-dark .widget-readout,
.sageagent-v4-dark label,
.sageagent-v4-dark .widget-html-content,
.sageagent-v4-dark .jupyter-widgets,
.sageagent-v4-dark .widget-checkbox,
.sageagent-v4-dark .widget-toggle-button {
  color: #f5f5f5 !important;
}
.sageagent-v4-dark input,
.sageagent-v4-dark textarea,
.sageagent-v4-dark select,
.sageagent-v4-dark .widget-text input,
.sageagent-v4-dark .widget-textarea textarea,
.sageagent-v4-dark .widget-dropdown select,
.sageagent-v4-dark .widget-boundedfloat input {
  background: #222 !important;
  color: #f5f5f5 !important;
  border-color: #555 !important;
}
.sageagent-v4-dark textarea::placeholder,
.sageagent-v4-dark input::placeholder {
  color: #999 !important;
}
.sageagent-v4-dark hr {
  border-top-color: #333 !important;
}
</style>
""")
        sep = widgets.HTML("<hr style='margin:4px 0;border:none;border-top:1px solid #333;'/>")
        sep2 = widgets.HTML("<hr style='margin:4px 0;border:none;border-top:1px solid #333;'/>")
        sep3 = widgets.HTML("<hr style='margin:4px 0;border:none;border-top:1px solid #333;'/>")
        sep4 = widgets.HTML("<hr style='margin:2px 0;border:none;border-top:1px solid #333;'/>")
        session_row = widgets.HBox([self._session_name, self._save_btn, self._session_dropdown, self._load_btn, self._new_btn])
        session_row.layout = widgets.Layout(flex_flow="row wrap", align_items="center", grid_gap="4px 8px")
        model_row = widgets.HBox([self._model_dropdown, self._subagent_toggle, self._plan_mode, self._approval_toggle])
        model_row.layout = widgets.Layout(flex_flow="row wrap", align_items="center", grid_gap="4px 8px")
        thinking_row = widgets.HBox([self._thinking_checkbox, self._thinking_budget_slider, self._temperature_slider, self._budget_input, self._auto_compact, self._dark_toggle, self._chat_height_slider])
        thinking_row.layout = widgets.Layout(flex_flow="row wrap", align_items="center", grid_gap="4px 8px")
        action_left = widgets.HBox([self._send_btn, self._stop_btn, self._clear_btn])
        action_left.layout = widgets.Layout(grid_gap="4px")
        action_right = widgets.HBox([self._compact_btn, self._clean_btn, self._status_html])
        action_right.layout = widgets.Layout(grid_gap="4px")
        action_row = widgets.HBox([action_left, action_right])
        action_row.layout = widgets.Layout(justify_content="space-between", width="100%")
        self._refresh_sessions()
        self._render_header()
        self._render_chat()
        self._render_status()
        self._panel = widgets.VBox([style, self._header, session_row, sep, model_row, self._subagent_panel, sep2, thinking_row, sep3, self._todo_display, self._chat_display, self._input, action_row, sep4, self._tokens_html, self._mode_html])
        self._panel.add_class("sageagent-v4-dark")

    def _refresh_sessions(self) -> None:
        try:
            from runtime.session import SESSIONS
            sessions = SESSIONS.list_sessions()
            self._session_dropdown.options = [("New Session", None)] + [(f"{s.get('title') or s.get('id')} ({s.get('updated_at', '')[:10]})", s.get("id")) for s in sessions[:50]]
        except Exception:
            self._session_dropdown.options = [("New Session", None)]

    def _render_header(self) -> None:
        c = self._colors()
        try:
            from tools.registry import all_registered
            tool_count = len(all_registered())
        except Exception:
            tool_count = "v5"
        try:
            saved_count = max(0, len(self._session_dropdown.options) - 1)
        except Exception:
            saved_count = 0
        try:
            from runtime.config import CONFIG
            region = CONFIG.region
        except Exception:
            region = ""
        self._header.value = f"<div style='border-bottom:1px solid {c['border']};padding-bottom:8px;margin-bottom:8px;'><h2 style='margin:0;color:#4a9eff;'>SageMaker Coding Agent</h2><p style='margin:4px 0;color:{c['muted']};font-size:12px;'>{tool_count} tools | {saved_count} saved sessions | {self._escape(region)}</p></div>"

    def _render_chat(self) -> None:
        c = self._colors()
        if not self._messages:
            content = f"<p style='color:{c['fg']};text-align:center;padding:20px;'>Type a message below to start.</p>"
        else:
            rows = []
            for role, text, ts in self._messages:
                color = "#26c6da" if role == "user" else ("#42a5f5" if role == "assistant" else "#ef5350")
                label = "You" if role == "user" else ("Agent" if role == "assistant" else "System")
                body = self._escape(text).replace("\n", "<br>")
                rows.append(f"<div style='margin:8px 0;border-left:3px solid {color};padding-left:10px;'><b style='color:{color};'>[{ts}] {label}:</b><div style='color:{c['fg']};margin-top:4px;line-height:1.5;'>{body}</div></div>")
            content = "".join(rows)
        self._chat_display.value = f"<div style='height:{self._chat_height}px;min-height:200px;max-height:90vh;overflow-y:auto;overflow-x:hidden;border:1px solid {c['border']};background:{c['bg']};display:flex;flex-direction:column-reverse;width:100%;box-sizing:border-box;resize:vertical;'><div style='padding:10px;font-family:system-ui,-apple-system,sans-serif;'>{content}</div></div>"

    def _render_status(self) -> None:
        try:
            from runtime.config import CONFIG
            from runtime.tokens import TOKENS
            from runtime.tokens import get_model_pricing_string
            model = self._escape(getattr(CONFIG, "model_id", ""))
            stats = TOKENS.get_stats()
            pricing = self._escape(get_model_pricing_string(getattr(CONFIG, "model_id", "")))
            session_limit = float(getattr(CONFIG, "session_cost_limit", 0.0) or 0.0)
            context_max = int(getattr(CONFIG, "context_max_tokens", 200000) or 200000)
            mock = bool(getattr(CONFIG, "mock_mode", False))
            auth = bool(getattr(CONFIG, "require_auth", False))
            exec_mode = self._escape(getattr(CONFIG, "execution_mode", "local"))
        except Exception:
            model = ""
            pricing = "unknown"
            session_limit = 0.0
            context_max = 200000
            mock = False
            auth = False
            exec_mode = "local"
            stats = {
                "session_input": 0,
                "session_output": 0,
                "session_total": 0,
                "api_calls": 0,
                "session_cost_usd": 0.0,
                "last_cost_usd": 0.0,
                "context_window_tokens": 0,
            }
        try:
            iter_used = self.agent.budget.used()
            iter_total = self.agent.budget.total()
        except Exception:
            iter_used = 0
            iter_total = 0
        cost = float(stats.get("session_cost_usd", 0.0) or 0.0)
        last_cost = float(stats.get("last_cost_usd", 0.0) or 0.0)
        context_tokens = int(
            stats.get("context_window_tokens", 0)
            or stats.get("session_total", 0)
            or 0
        )
        context_pct = 0.0 if context_max <= 0 else min(100.0, (context_tokens / context_max) * 100.0)
        budget_pct = 0.0 if session_limit <= 0 else min(100.0, (cost / session_limit) * 100.0)
        budget_text = "no limit" if session_limit <= 0 else f"${cost:.4f} / ${session_limit:.2f}"
        status_text = "Connected (Mock mode, no Bedrock call)" if mock else "Connected"
        skills_count = 0
        try:
            skills_count = len(getattr(getattr(self.agent, "skill_manager", None), "skills", {}) or {})
        except Exception:
            skills_count = 0
        thinking_state = "ON" if self._thinking_checkbox.value else "OFF"
        self._status_html.value = "<span style='color:#4caf50'><b>* Ready</b></span>"
        self._tokens_html.value = (
            "<div style='font-size:11px;color:gray;line-height:1.7;'>"
            f"<div>In {int(stats.get('session_input', 0)):,} | Out {int(stats.get('session_output', 0)):,} | Calls {int(stats.get('api_calls', 0)):,}</div>"
            f"<div>Cost: ${cost:.4f} | Last: ${last_cost:.4f} | {pricing}</div>"
            f"<div style='color:#2ca02c;'>Context: {context_pct:.1f}% ({context_tokens:,} / {context_max:,})</div>"
            f"<div style='height:4px;background:#333;width:100%;'><div style='height:4px;background:#2ca02c;width:{context_pct:.1f}%;'></div></div>"
            f"<div style='color:#2ca02c;'>Budget: {budget_pct:.0f}% ({budget_text})</div>"
            f"<div style='height:4px;background:#333;width:100%;'><div style='height:4px;background:#2ca02c;width:{budget_pct:.1f}%;'></div></div>"
            "</div>"
        )
        self._mode_html.value = (
            "<span style='color:#8aa0b8;font-size:11px;'>"
            f"Model: {model} | Status: <b style='color:#2ca02c'>{status_text}</b> "
            f"| Plan: {'ON' if self._plan_mode.value else 'OFF'} "
            f"| Thinking: {thinking_state} (budget {int(self._thinking_budget_slider.value)}) "
            f"| Auth: {'ON' if auth else 'OFF'} "
            f"| Approval: {'ON' if self._approval_toggle.value else 'OFF'} "
            f"| Auto-Compact: {'ON' if self._auto_compact.value else 'OFF'} "
            f"| Sub-Agents: {'ON' if self._subagent_toggle.value else 'OFF'} "
            f"| Skills: {skills_count} | Exec: {exec_mode} "
            f"| Iter: {iter_used}/{iter_total}"
            "</span>"
        )

    def _append_message(self, role: str, content: str) -> None:
        self._messages.append((role, content, datetime.now().strftime("%H:%M:%S")))
        self._render_chat()

    def _dispatch_ui_command(self, command: str) -> None:
        try:
            from commands import dispatch_command
            cr = dispatch_command(command, ctx={"agent": self.agent})
            self._append_message("assistant", cr.text)
        except Exception as exc:  # noqa: BLE001
            self._append_message("system", f"{command} failed: {type(exc).__name__}: {exc}")
        finally:
            self._refresh_sessions()
            self._render_status()

    def _on_send(self, _btn) -> None:
        msg = (self._input.value or "").strip()
        if not msg:
            return
        self._input.value = ""
        self._append_message("user", msg)
        self._stop_btn.layout.display = ""
        self._status_html.value = "<span style='color:#ff9800'><b>* Running</b></span>"
        try:
            if msg.startswith("/"):
                try:
                    from commands import is_command, dispatch_command
                    if is_command(msg):
                        cr = dispatch_command(msg, ctx={"agent": self.agent})
                        if cr.consumed:
                            text = cr.text
                            if cr.side_effect == "dream_invoked":
                                text += "\n" + _invoke_dream(self.agent)
                            self._append_message("assistant", text)
                            return
                except Exception as cmd_exc:
                    logging.warning(f"[chat-ui] slash-command dispatch error: {cmd_exc}")
            streamed = []
            result = self.agent.run(msg, output_fn=lambda s: streamed.append(str(s)))
            self._append_message("assistant", result.text or "\n".join(streamed) or f"stop_reason: {result.stop_reason}")
        except Exception as exc:  # noqa: BLE001
            logging.exception("[chat-ui] agent.run() raised")
            self._append_message("system", f"[chat-ui] error: {type(exc).__name__}: {exc}")
        finally:
            self._stop_btn.layout.display = "none"
            self.budget_widget.update()
            self.thinking_widget.refresh()
            self._render_status()

    def _on_stop(self, _btn) -> None:
        self.agent.stop()
        self._append_message("system", "[stop requested]")
        self._render_status()

    def _on_clear(self, _btn) -> None:
        self.agent.clear()
        self._messages.clear()
        self._render_chat()
        self.budget_widget.update()
        self._render_status()

    def _on_new(self, _btn) -> None:
        self.agent.clear(reset_budget=True)
        self._messages.clear()
        self._render_chat()
        self._render_status()

    def _on_compact(self, _btn) -> None:
        messages = list(getattr(self.agent, "messages", []) or [])
        if not messages:
            self._append_message("system", "No conversation to compact.")
            return
        self._status_html.value = "<span style='color:#ff9800'><b>* Compacting</b></span>"
        try:
            from core.compactor import Compactor
            from runtime.config import CONFIG

            max_context = int(getattr(CONFIG, "context_max_tokens", 200_000) or 200_000)
            before_count = len(messages)
            before_tokens = Compactor.estimate_tokens(messages)
            Compactor.flush_memories_before_compact(messages)
            pruned, saved = Compactor.prune_tool_outputs(messages, max_context)
            summary = Compactor.create_llm_summary(getattr(self.agent, "client", None), pruned)
            if not summary:
                summary = "Conversation compacted manually from the notebook UI. Continue from the preserved recent context."
            compacted = Compactor.compact(pruned, summary)
            post_blocks = []
            post_blocks.extend(Compactor.create_post_compact_file_attachments())
            skill_block = Compactor.create_skill_attachment_if_needed(getattr(self.agent, "skill_manager", None))
            if skill_block is not None:
                post_blocks.append(skill_block)
            if post_blocks:
                compacted.append({"role": "user", "content": post_blocks, "is_meta": True})
            Compactor.reset_retry_counters()
            Compactor.suppress_compact_warning_state()
            Compactor.run_post_compact_cleanup(skill_manager=getattr(self.agent, "skill_manager", None))
            self.agent.replace_messages(compacted)
            after_tokens = Compactor.estimate_tokens(compacted)
            parts = [f"Compacted: {before_count} -> {len(compacted)} messages."]
            if saved:
                parts.append(f"Pruned about {saved:,} tool-output tokens first.")
            parts.append(f"Estimated context: {before_tokens:,} -> {after_tokens:,} tokens.")
            self._append_message("system", " ".join(parts))
        except Exception as exc:  # noqa: BLE001
            logging.exception("[chat-ui] manual compact failed")
            self._append_message("system", f"Compact failed: {type(exc).__name__}: {exc}")
        finally:
            self._render_status()

    def _on_clean(self, _btn) -> None:
        try:
            import os
            import shutil
            from runtime.config import CONFIG

            workspace = getattr(CONFIG, "workspace", os.getcwd())
            targets = [
                ("audit_logs", getattr(CONFIG, "audit_dir", os.path.join(workspace, "audit_logs"))),
                (".snapshots", os.path.join(workspace, ".snapshots")),
                (".code_index", os.path.join(workspace, ".code_index")),
                ("truncated_outputs", os.path.join(workspace, "truncated_outputs")),
                (".sageagent_state", os.path.join(workspace, ".sageagent_state")),
            ]
            cleaned = []
            for name, path in targets:
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                    cleaned.append(name)
            for name, path in [
                (".exec_budget.json", os.path.join(workspace, ".exec_budget.json")),
            ]:
                if os.path.isfile(path):
                    os.unlink(path)
                    cleaned.append(name)
            if cleaned:
                self._append_message("system", f"Cleaned: {', '.join(cleaned)} (sessions kept).")
            else:
                self._append_message("system", "Nothing to clean; sessions kept.")
        except Exception as exc:  # noqa: BLE001
            logging.exception("[chat-ui] clean failed")
            self._append_message("system", f"Clean failed: {type(exc).__name__}: {exc}")
        finally:
            self._refresh_sessions()
            self._render_status()

    def _on_model_change(self, change) -> None:
        try:
            from runtime.config import CONFIG
            CONFIG.model_id = change["new"]
            client = getattr(self.agent, "client", None)
            if client is not None and hasattr(client, "model_id"):
                client.model_id = change["new"]
        except Exception:
            pass
        self._render_status()

    def _on_thinking_change(self, change) -> None:
        self._thinking_budget_slider.disabled = not bool(change["new"])
        try:
            self.agent.set_thinking(bool(change["new"]), int(self._thinking_budget_slider.value))
        except Exception:
            pass
        self.thinking_widget.refresh()
        self._render_status()

    def _on_thinking_budget_change(self, change) -> None:
        try:
            self.agent.set_thinking(bool(self._thinking_checkbox.value), int(change["new"]))
        except Exception:
            pass
        self.thinking_widget.refresh()

    def _on_temperature_change(self, change) -> None:
        try:
            from runtime.config import CONFIG
            CONFIG.temperature = float(change["new"])
        except Exception:
            pass

    def _on_budget_change(self, change) -> None:
        try:
            from runtime.config import CONFIG
            CONFIG.session_cost_limit = float(change["new"])
        except Exception:
            pass
        self._render_status()

    def _on_chat_height_change(self, change) -> None:
        self._chat_height = int(change["new"])
        self._render_chat()

    def _on_dark_mode_change(self, change) -> None:
        self._dark_mode = bool(change["new"])
        try:
            if self._dark_mode:
                self._panel.add_class("sageagent-v4-dark")
            else:
                self._panel.remove_class("sageagent-v4-dark")
        except Exception:
            pass
        self._render_header()
        self._render_chat()

    def _on_approval_change(self, change) -> None:
        try:
            from runtime.config import CONFIG
            CONFIG.require_tool_approval = bool(change["new"])
        except Exception:
            pass
        self._render_status()

    def _on_plan_mode_change(self, change) -> None:
        try:
            self.agent.set_plan_mode(bool(change["new"]))
        except Exception:
            pass
        self._render_status()

    def _on_auto_compact_change(self, change) -> None:
        try:
            self.agent.set_auto_compact(bool(change["new"]))
        except Exception:
            pass
        self._render_status()

    def _on_subagent_preferences_change(self, change) -> None:
        enabled = bool(self._subagent_toggle.value)
        try:
            self._subagent_panel.layout.display = "" if enabled else "none"
        except Exception:
            pass
        try:
            self.agent.set_ui_subagent_preferences(
                enabled=enabled,
                explorer=str(self._explorer_dropdown.value),
                worker=str(self._worker_dropdown.value),
                reviewer=str(self._reviewer_dropdown.value),
            )
        except Exception:
            pass
        self._render_status()

    def render(self) -> Any:
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
        return V4WidgetChatUI(agent)
    return ConsoleChatUI(agent)
