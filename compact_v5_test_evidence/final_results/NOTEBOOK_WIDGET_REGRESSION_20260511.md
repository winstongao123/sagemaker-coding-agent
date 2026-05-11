# compact_v5 Notebook Widget Regression Investigation - 2026-05-11

## Trigger

The user opened/reran `compact_v5/chat.ipynb` and saw:

```text
Error displaying widget: model not found
```

The visible cell also contains:

```python
ui = create_chat_ui()
# v5 follows compact_v4's stable display contract...
```

This investigation began as docs-only. It was later fixed by moving notebook
plumbing into `entry.py` and adding a thin-notebook regression test.

## Findings

### 1. The display regression was introduced before the S3 fixes

The S3 work did not introduce this notebook display contract. The flat
`compact_v5/chat.ipynb` already had the current `ui = create_chat_ui()` shape
when it was added by:

`2cbf9da v5/ui: port v4 launch clear-output behavior`

Evidence from notebook history:

| Commit | Stage | Config cell lines | Launch cell lines | Display contract |
|---|---:|---:|---:|---|
| `9191b2f` | Phase 11 notebook UX | 19 | 6 | `display(ui.render())` |
| `4aa0da1` | robust imports | 54 | 41 | `display(ui.render())` |
| `0512b5f` | restore v4 controls | 181 | 65 | `display(ui.render())` |
| `7cad523` | restore v4 notebook parity | 188 | 69 | `display(ui.render())` |
| `03afb06` | SageMaker-safe widget display | 188 | 76 | `render_parts()` child loop |
| `2cbf9da` | port v4 clear-output behavior | 188 | 60 | `create_chat_ui()` auto-displays one root widget |
| `249dcf7` | pre-fix HEAD | 188 | 59 | `create_chat_ui()` auto-displays one root widget |
| current fix | thin launcher | 12 | 4 | `launch_config_ui()` / `launch_chat_ui(...)` helpers |

The likely regression point for the user's screenshot is therefore `2cbf9da`.
That commit intentionally moved from the previous SageMaker-safe child display
path back to "one root widget" because v4 did that. The mistake was treating
v4's display call as a complete contract, without accounting for v5's larger,
more dynamic widget tree and the user's actual SageMaker/Jupyter environment.

### 2. v5 copied the v4 surface but not v4's notebook simplicity

v4 launch cell:

```python
from sagemaker_agent import CONFIG, create_chat_ui
...
create_chat_ui()
```

v5 launch cell now has 59 lines, and the config cell has 188 lines. The runtime
path-discovery function is duplicated in both config and launch cells.

This is not a good product shape. The v4 lesson should have been:

> Keep the notebook thin; put complexity behind `create_chat_ui()`.

Instead, v5 gradually moved robustness logic and configuration plumbing into
the notebook itself. That makes the UI harder to reason about, harder to test,
and easier to break during packaging/layout changes.

### 3. The visual tests did not prove the target widget runtime

The earlier evidence correctly warned:

`Fixed, but needs user's SageMaker visual re-test after fresh zip + kernel restart.`

That means the prior "fixed" status was too strong for production. The tests
and Claude reviews mostly checked structural properties:

- no cached notebook outputs;
- no `render_parts()` child loop in current Cell 3/4;
- `clear_output(wait=True)` before widget construction;
- zip contains required files.

Those checks do not prove that the target SageMaker/Jupyter widget manager can
display the resulting root widget. The screenshot is therefore a real escaped
gap, not just user error.

### 4. A second regression is currently present in the local working tree

Current local status shows the six tracked S3/UI smoke tests deleted:

```text
D compact_v5/tests/test_aws_s3_list_tool.py
D compact_v5/tests/test_restriction_diagnostics.py
D compact_v5/tests/test_s3_cost_controls.py
D compact_v5/tests/test_s3_intent_drift_guard.py
D compact_v5/tests/test_ui_thinking_smoke.py
D compact_v5/tests/test_ui_tool_cards_smoke.py
```

Those files still exist in git at `HEAD`, but the local `compact_v5/tests/`
directory is missing. The current `compact_v5.zip` intentionally excludes
`tests/`, so the most likely cause is a runtime zip/source overwrite pattern:
using the production zip layout as if it were the editable source tree.

This is the same class of packaging/source drift previously documented in v5:
the runtime artifact is not the development tree. Replacing source with the
runtime zip deletes development-only tests.

## Root Cause Summary

| Problem | Root cause | Stage |
|---|---|---|
| `Error displaying widget: model not found` still happens | v5 root-widget display contract was assumed equivalent to v4, but v5's widget tree and SageMaker runtime differ. | Introduced in flat notebook path at `2cbf9da`; not caused by S3 commits. |
| Notebook code is too long | Robust path/config logic moved into `chat.ipynb` instead of a Python launcher module. | Grew mainly from `4aa0da1` through `7cad523`; carried into current flat tree. |
| Tests disappeared locally | Production zip excludes tests; local source tree appears overwritten or synchronized with runtime zip shape. | Local uncommitted workspace regression after `249dcf7`; not committed to git. |
| Prior review missed it | Review checked source structure and zip integrity, not the real SageMaker widget-manager rendering path. | Process/test gap. |

## Is this hard to fix?

Not conceptually hard, but it must be fixed carefully because the notebook is
the product surface.

The safe fix direction is:

1. Make `chat.ipynb` thin again.
2. Move path discovery and config-widget creation into Python helpers, for
   example `entry.launch_config_ui()` and `entry.launch_chat_ui()`.
3. Preserve the v4 user contract: the launch cell should be a tiny, memorable
   cell, not 59-188 lines of fragile setup.
4. Add a target visual validation gate. A structural smoke test is not enough
   for ipywidgets.
5. Never use the runtime zip as the editable source tree; restore tests from
   git before any new commit.

## Implementation status

Fixed in the follow-up notebook regression patch:

| Fix | Evidence |
|---|---|
| Notebook is thin again | `compact_v5/chat.ipynb` config cell is 12 lines; launch cell is 4 lines. |
| Config/display plumbing moved to Python | `compact_v5/entry.py` now owns `launch_config_ui()` and `launch_chat_ui()`. |
| v4 control surface preserved | Helper exposes model, temperature, thinking, thinking budget, workspace, max turns, iteration budget, mock mode, Bedrock-only, approvals, and cost limit. |
| Regression test added | `compact_v5/tests/test_notebook_thin_launcher.py` locks cell line counts and config propagation. |
| Smoke tests passed | `py -3.10 -m pytest` over S3/UI plus notebook thin tests: 25 passed. |
| Independent review | Claude Round 1 returned `VERDICT: APPROVE` with no HIGH/MEDIUM findings. |

Remaining caveat: a true frontend `Error displaying widget: model not found`
cannot be fully proven by local Python execution. The rebuilt zip still needs a
fresh-kernel SageMaker visual smoke before claiming the notebook UI path is
100% production proven.

## Future Software Lesson

When a reference product works, copy the **user contract**, not blindly the
implementation detail.

For v4, the important contract was:

- the notebook has a simple launch flow;
- `create_chat_ui()` owns display complexity;
- users do not need to understand widget internals;
- the UI either appears or gives one clear fallback.

v5 copied parts of the display mechanism, but let the notebook become a large
integration script. That made the system look more robust in review and less
robust in the user's actual notebook.

Future rule:

> Any notebook app must have a "thin-notebook" budget. If a cell exceeds about
> 20-30 lines, the code belongs in a tested Python module. If a visual widget
> is the main product, it needs a real target-environment render check before
> production readiness.
