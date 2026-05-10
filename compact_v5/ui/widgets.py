"""V5 ui/widgets.py — IterationBudgetWidget + ThinkingBudgetWidget (Phase 11).

PS Issues addressed:
- **PS Issue #2** (visible IterationBudget): Phase 8 shipped the data model
  (`core.budget.IterationBudget`). Phase 11 wires it to an
  `ipywidgets.IntProgress` so the user sees the budget burning down.
- **PS Issue #4** (visible thinking budget): v4.8.0 added the thinking-mode
  toggle but no in-UI surface for budget consumption. Phase 11 adds a
  small `ipywidgets.HBox` showing the toggle + budget label.

Both widgets are designed so the data model is fully usable WITHOUT
ipywidgets — the `update()` / `render_html()` methods produce text/HTML
output even in environments where ipywidgets isn't installed (CI,
SageMaker base images that strip notebook deps). This is what lets the
Phase 11 smoke test exercise the widget machinery without a real Jupyter.

PORT_LOG: #033 (PS Issue #2) + #034 (PS Issue #4).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ipywidgets is optional — fall back to pure-Python data structures when
# it isn't installed. This matches the v5 ship constraint (chat.ipynb must
# run without `pip install` of a v5 package; ipywidgets is in the install
# cell but won't be present in CI test contexts).
try:
    import ipywidgets as _widgets
    _IPYWIDGETS_OK = True
except Exception:
    _widgets = None
    _IPYWIDGETS_OK = False


# ============================================================
# IterationBudgetWidget — PS Issue #2
# ============================================================

@dataclass
class IterationBudgetWidget:
    """Live display of `IterationBudget` consumption.

    Construction:
        w = IterationBudgetWidget(budget=engine.budget)
        w.render()    # returns ipywidgets widget OR HTML string fallback

    Update:
        w.update()    # call after each agent turn / sub-agent turn

    Resilient to ipywidgets being absent — `render()` returns HTML string
    that callers can `display(HTML(...))` from IPython if available."""

    budget: Any                              # core.budget.IterationBudget
    label_prefix: str = "Iteration budget"
    _ipw: Optional[Any] = field(default=None, init=False, repr=False)

    def render(self) -> Any:
        """Return the renderable handle: ipywidgets.IntProgress when
        available, else an HTML <progress> string the caller can display."""
        if _IPYWIDGETS_OK:
            self._ipw = _widgets.IntProgress(
                value=self.budget.used(),
                min=0,
                max=self.budget.total(),
                description=self.label_prefix,
                orientation="horizontal",
                bar_style="info",
            )
            return self._ipw
        return self.render_html()

    def update(self) -> None:
        """Push current budget state into the widget (ipywidgets path) or
        no-op (HTML path — the caller would re-render the HTML string)."""
        if self._ipw is not None:
            try:
                self._ipw.value = self.budget.used()
                self._ipw.max = self.budget.total()
                # Color cue for cost ceiling — red when ≥ 90% consumed.
                pct = self.budget.used() / max(1, self.budget.total())
                self._ipw.bar_style = (
                    "danger" if pct >= 0.9 else
                    "warning" if pct >= 0.7 else
                    "info"
                )
            except Exception:
                # ipywidgets may have been disposed — silently no-op
                pass

    def render_html(self) -> str:
        """Pure-string fallback. Returns one-line HTML with a progress bar."""
        used = self.budget.used()
        total = self.budget.total()
        pct = (used / max(1, total)) * 100
        return (
            f'<div style="font-family:sans-serif;">'
            f'<b>{self.label_prefix}:</b> '
            f'{used}/{total} ({pct:.0f}%)'
            f'<progress value="{used}" max="{total}" '
            f'style="width:200px;margin-left:8px;"></progress>'
            f'</div>'
        )


# ============================================================
# ThinkingBudgetWidget — PS Issue #4
# ============================================================

@dataclass
class ThinkingBudgetWidget:
    """Live display of thinking-mode toggle + budget label.

    The widget reads from / writes to the bound Agent's thinking-mode
    settings via `agent.set_thinking(enabled, budget)`.

    Construction:
        w = ThinkingBudgetWidget(agent=agent)
        w.render()
    """

    agent: Any
    label_prefix: str = "Thinking budget"
    _toggle: Optional[Any] = field(default=None, init=False, repr=False)
    _slider: Optional[Any] = field(default=None, init=False, repr=False)

    def render(self) -> Any:
        if not _IPYWIDGETS_OK:
            return self.render_html()

        self._toggle = _widgets.Checkbox(
            value=self.agent.thinking_enabled,
            description="thinking",
            indent=False,
        )
        self._slider = _widgets.IntSlider(
            value=self.agent.thinking_budget,
            min=1024,
            max=16000,
            step=512,
            description="budget",
            continuous_update=False,
        )

        def _on_change(change):
            try:
                self.agent.set_thinking(
                    enabled=self._toggle.value,
                    budget=self._slider.value,
                )
            except Exception:
                pass

        self._toggle.observe(_on_change, names="value")
        self._slider.observe(_on_change, names="value")

        return _widgets.HBox([self._toggle, self._slider])

    def render_html(self) -> str:
        return (
            f'<div style="font-family:sans-serif;">'
            f'<b>{self.label_prefix}:</b> '
            f'thinking={"ON" if self.agent.thinking_enabled else "OFF"}, '
            f'budget={self.agent.thinking_budget} tokens'
            f'</div>'
        )

    def refresh(self) -> None:
        """Push current Agent state into the widgets (call after the model
        flips thinking-mode programmatically)."""
        if self._toggle is not None:
            try:
                self._toggle.value = self.agent.thinking_enabled
            except Exception:
                pass
        if self._slider is not None:
            try:
                self._slider.value = self.agent.thinking_budget
            except Exception:
                pass


# ============================================================
# Public re-exports
# ============================================================

__all__ = [
    "IterationBudgetWidget",
    "ThinkingBudgetWidget",
    "_IPYWIDGETS_OK",
]
