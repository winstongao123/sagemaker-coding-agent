# chat.ipynb companion (v5 Phase 11)

The notebook itself is the user-facing surface. This file documents cell
purpose, expected output, and troubleshooting — read this when something
in `chat.ipynb` doesn't behave as expected.

## Cell-by-cell

### Cell 0 — Markdown header
Identifies the v5 build. No code.

### Cell 1 — Install dependencies
```python
!pip install -q boto3 ipywidgets Pillow
```
Runs once per kernel. Pillow is for `view_image`; ipywidgets is the chat UI.
SageMaker base images already have boto3; the `-q` flag silences the warning
when boto3 is up to date.

### Cell 2 — Configure
Sets:
- `CONFIG.model_id`     — Bedrock inference profile id (default Haiku 4.5).
- `CONFIG.region`       — AWS region.
- `CONFIG.mock_mode`    — `True` for first-run smoke (no real Bedrock). Flip
                          to `False` to invoke the real model.
- `CONFIG.thinking_enabled` — PS Issue #4. Default OFF. UI exposes a toggle.
- `CONFIG.thinking_budget`  — PS Issue #4. 4096 default; UI exposes a slider.
- `CONFIG.enable_skill_auto_trigger` — v4.9.6 default-OFF. Skills only load
                          via `/skill activate <name>`.

### Cell 3 — Launch
```python
from entry import create_chat_ui
from IPython.display import display
ui = create_chat_ui()
display(ui.render())
```
The factory:
1. Reads CONFIG, builds a `BedrockClient`.
2. Builds an `Agent` (Phase 11 wrapper around QueryEngine).
3. Returns `WidgetChatUI` (when ipywidgets is available) or `ConsoleChatUI`.

The widget panel contains:
- IterationBudget progress bar (PS Issue #2 — visible budget).
- Thinking-budget toggle + slider (PS Issue #4 — visible thinking).
- Send / Stop / Clear buttons.
- Output area for agent text.

### Cell 4 — Quick reference (markdown)
Reminds the user about buttons, PS Issues, skills, console fallback.

## What the smoke test verifies

`tests/integration/test_notebook_smoke.py` exercises:
- `from entry import Agent, create_chat_ui, CONFIG, BEDROCK_MODELS`.
- `Agent(client=mock).run("hello")` returns a `QueryResult` with text.
- `ConsoleChatUI(agent).send("hello world")` returns a non-empty string and
  consumes ≥ 1 iteration from the budget.
- `IterationBudgetWidget.render_html()` reflects post-consume state.
- `ThinkingBudgetWidget.render_html()` shows ON/OFF + budget.
- `chat.ipynb` is valid JSON with required cells.

This is the **Phase 11 acceptance gate** (V5_PLAN.md §Phase 11).

## Troubleshooting

**"ipywidgets not installed"** — Run cell 1 then restart the kernel. The
factory falls back to `ConsoleChatUI` if ipywidgets remains missing; you can
still drive the agent via `ui.send("...")` from a code cell.

**"Bedrock access denied"** — Set `CONFIG.mock_mode = True` in cell 2 to
sanity-check the loop without hitting Bedrock. Then restore `mock_mode =
False` and verify your IAM role has `bedrock-runtime:InvokeModel`.

**"Budget exhausted"** — `Agent.budget` shares the IterationBudget with
sub-agents. Either bump `CONFIG.max_iteration_budget` (Phase 1 config) or
press Clear (which optionally resets the budget if you pass
`reset_budget=True`).

## What's NOT in chat.ipynb (deferred)

- Full v4 chat-display HTML rendering (Phase 13 polish).
- Compact / clean buttons (microcompact wires later if at all).
- Model-switcher mid-session (CONFIG.model_id is static; restart cell 2).
- Session auto-restore (use `runtime.session.SessionManager` from a code
  cell if needed).
- `/skill apply` slash command (Phase 11 wires `skill_propose_patch`'s
  apply path through an explicit user click; not yet shipped).
