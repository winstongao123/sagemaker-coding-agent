## VERDICT: APPROVE

No HIGH or MEDIUM regressions found. The fix restores the v4-style ipywidgets UI as the default, keeps the console path as an explicit opt-in, and addresses the actual root cause (stale kernel modules) without drifting into engine/prompt/tool/security/runtime code.

### Findings (ordered by severity)

#### HIGH — none

#### MEDIUM — none

#### LOW / Non-blocking notes

1. **Cell 2 line budget is tight against the test contract.** `chat.ipynb` Cell 2 is currently 18 lines; `tests/test_notebook_thin_launcher.py:25` allows `<= 20`. Adding a single comment or path entry could push it over. Consider tightening the test (`<= 25`) or trimming a comment to give a small buffer.

2. **Selective `sys.modules` pop only covers `ui.chat_ui`, `ui.widgets`, `entry`** (chat.ipynb Cell 2, entry.py:1-396 path discovery). This is the right minimal scope for the documented widget-staleness symptom, but if `agent`, `runtime.config`, or `ui.*` submodules change between zip refreshes, those would still be served from kernel cache. The chat.md troubleshooting row already tells users to restart the kernel for repeated widget errors, so the user-visible escape hatch is present. Non-blocking.

3. **`_apply_notebook_config` looks up `_TEMPERATURE_OPTIONS` / `_THINKING_BUDGET_OPTIONS` by raw widget value** (`entry.py:262-264`). If a future caller passes overrides as raw floats/ints rather than label strings, this would `KeyError`. Current call sites all stay in label-space (controls or `_apply_control_overrides` mapping), so this is latent, not active.

4. **`agent` module is referenced as `entry.create_chat_ui` in tests** (test_notebook_thin_launcher.py:62, 88, 126). The monkey-patching pattern is fine, but note that `launch_chat_ui` reads `create_chat_ui` from the `entry` module namespace, so test patches must happen on `entry`, not at the source — which is what the tests already do.

### Spec confirmations

| Requirement | Status | Evidence |
|---|---|---|
| Default is v4-style ipywidgets (not console fallback) | ✓ | `entry.py:308` `launch_config_ui(use_widgets: bool = True, ...)`; `entry.py:393-395` defaults `use_widgets=True`; chat.ipynb Cell 2/3 call with `use_widgets=True` |
| Cell 2 stays thin and refreshes launcher/UI modules | ✓ | chat.ipynb Cell 2 is 18 lines; pops `ui.chat_ui`, `ui.widgets`, `entry` before importing |
| Console fallback preserved via `use_widgets=False` | ✓ | `entry.py:316-324` console branch; `chat_ui.py:1721-1730` `force_console` branch |
| No drift into engine/prompt/tool/security/runtime | ✓ | Changes confined to `entry.py` launcher helpers, `chat.ipynb`, `chat.md` (S3/UI text unchanged), tests, and docs. `create_chat_ui` signature only gained `force_console`, which is widget-routing only |
| Docs explain detour, stale-kernel lesson, and visual evidence | ✓ | NOTEBOOK_WIDGET_REGRESSION_20260511.md §"Visual validation failure after first fix" + §"Final follow-up"; FUTURE_SOFTWARE_DEVELOPMENT_LESSONS Example D + Lesson 13; AGENT_STATUS 2026-05-12 entry |
| Tests lock the notebook contract; no Bedrock required | ✓ | test_notebook_thin_launcher.py uses `SimpleNamespace`, mocks `entry.create_chat_ui`, asserts cell line counts, default widget path, explicit console opt-in, control defaults |

### Honesty check

The docs accurately admit the fallback detour was a wrong product call ("That avoided the error but broke the product contract"), name the missed cause (reused kernel + stale `sys.modules`), and the lesson layer correctly generalizes to "validate against the actual widget runtime, not just structural checks." No overclaiming.

