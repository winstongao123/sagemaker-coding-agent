# Widget Robustness Visual Report - 2026-05-13

Purpose: verify the recurring notebook error does not appear after the UI launch
hardening.

## Root Cause Found

The user's screenshot showed a stale Cell 2 that still used:

- `clear_output(wait=True)`
- `sys.modules.pop(...)`
- `from entry import refresh_ui`

The active source notebook had already moved to direct `launch_ui`, but the
compatibility helper `entry.refresh_ui()` still cleared output internally, and
`create_chat_ui()` also cleared output before widget construction. Those hidden
clear paths kept the old risky behavior alive.

## Fix

- `chat.ipynb` Cell 2 now uses only direct `launch_ui(use_widgets=True)`.
- Follow-up hardening changed Cell 2 to the even simpler v4-style
  `create_chat_ui()` call after setting only production defaults.
- `entry.refresh_ui()` no longer clears notebook output; it is now a safe
  compatibility alias for `launch_ui`.
- `ui.chat_ui.create_chat_ui()` no longer calls `IPython.display.clear_output`
  around root widget display.
- `V4WidgetChatUI.refresh()` no longer clears output before display.
- Regression test locks that the launch paths do not import/call
  `clear_output(wait=True)`.

## Verification

Commands:

- `py -3.10 -m pytest tests -q` -> 66 passed.
- `py -3.10 -m pytest compact_v5\tests -q` from repo root -> 66 passed.
- `py -3.10 -m py_compile entry.py ui\chat_ui.py` -> passed.
- Executed `chat.ipynb` with nbconvert from a fresh kernel.
- Executed a compatibility notebook using the old stale `refresh_ui` cell shape.
- Captured both rendered HTML files with Playwright screenshots.
- Claude CLI subscription review: `APPROVE`, ship-ready for target SageMaker
  validation. Two LOW notes were handled: stale duplicate zip-evidence row
  removed and workspace text `continuous_update=False` added.

Visual artifacts:

- `v5_widget_cold_kernel.html`
- `cold_screenshot.png`
- `v5_widget_old_refresh_compat.html`
- `old_refresh_compat_screenshot.png`

Playwright checks:

| Scenario | model-not-found text | loading widget text | Send | Stop | Bedrock-only | Ready |
|---|---:|---:|---:|---:|---:|---:|
| Fresh/cold notebook | False | False | True | True | True | True |
| Old refresh cell compatibility | False | False | True | True | True | True |

Conclusion: the current source and compatibility path render the v5 UI visually
without the persistent widget model error in local notebook execution.

## 2026-05-13 Follow-Up From Claude Suggestion

Claude correctly pointed out that v4 is stable because the launcher is
dumb-simple. Cell 2 was therefore stripped further:

- no `launch_ui` wrapper in production Cell 2;
- no `refresh_ui`;
- no `sys.modules.pop`;
- no `clear_output`;
- direct `from entry import CONFIG, create_chat_ui`;
- production defaults are assigned explicitly, then `ui = create_chat_ui()`.

Verification for the v4-simple Cell 2:

- `py -3.10 -m pytest tests -q` -> 66 passed.
- `py -3.10 -m pytest compact_v5\tests -q` from repo root -> 66 passed.
- Executed `chat.ipynb` with nbconvert from a fresh kernel.
- Captured `v4_simple_cold_kernel_screenshot.png` with Playwright.
- Checks: `HAS_MODEL_NOT_FOUND False`, `HAS_LOADING_WIDGET False`,
  `HAS_SEND True`, `HAS_STOP True`, `HAS_BEDROCK_ONLY True`,
  `HAS_READY True`, `HAS_CREATE_CHAT_UI_CELL True`.
