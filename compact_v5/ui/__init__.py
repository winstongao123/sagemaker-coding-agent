"""V5 ui/ — Phase 11 chat UI surface.

- `chat_ui.py` — `create_chat_ui()` factory + `WidgetChatUI` / `ConsoleChatUI`.
- `widgets.py`  — `IterationBudgetWidget` (PS Issue #2) + `ThinkingBudgetWidget` (PS Issue #4).
- `diff_widget.py` — Phase-4 diff renderer for write_file/edit_file/notebook_edit approval.
"""
from __future__ import annotations

from .chat_ui import ConsoleChatUI, WidgetChatUI, create_chat_ui  # noqa: F401
from .widgets import IterationBudgetWidget, ThinkingBudgetWidget  # noqa: F401
