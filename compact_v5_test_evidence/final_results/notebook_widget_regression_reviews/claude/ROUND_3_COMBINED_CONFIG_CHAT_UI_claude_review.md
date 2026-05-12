## VERDICT: REQUEST_CHANGES — one MEDIUM blocker

### Review by question

1. **One displayed surface (Q1).** YES. `chat.ipynb` Cell 2 is a single `launch_ui(use_widgets=True)` call. The visual `20260512_combined_ui_cell2_tall.png` clearly shows model, plan-mode, approval, Bedrock-only, workspace, max turns, iter budget, mock mode, thinking, temperature, budget, chat input, send/stop, and metrics all inside one bordered dark v4-style widget. `HAS_SEPARATE_AGENT_CONFIG_HEADING False` + `HAS_SINGLE_COMBINED_UI True`. v4 UI contract preserved.

2. **Controls actually mutate runtime (Q2).** Mostly yes:
   - workspace, max_turns, iter_budget, temperature, budget, approval, Bedrock-only, thinking, plan, auto-compact: write to CONFIG; max_turns also writes to `agent._engine.max_turns` (matches `core/query_engine.py:641`); iter budget writes to `agent.budget._max` under `_lock` (matches `core/budget.py:39,41`). Good.
   - **MEDIUM (Mock Mode reverse path):** `ui/chat_ui.py:1638-1654 _on_mock_mode_change` only nulls `client.client` when *enabling* mock. When the user toggles Mock Mode OFF after it was ON (or after starting with `CONFIG.mock_mode=True`), `BedrockClient.client` stays `None` and the very next real chat call hits `self.client.invoke_model(...)` on `None` (`runtime/bedrock_client.py:419`). The general retry path may eventually self-heal via `_rebuild_bedrock_client()` in `runtime/bedrock_client.py:464,476`, but only after the AttributeError is reclassified as a transient — that's brittle and depends on `ErrorClassifier`. This is a real new gap because v4 had no runtime mock toggle.

3. **Regressions in existing v5 features (Q3).** None observed. Tool/thinking grouping, line metrics, cost/cache HTML, S3 guards, sandbox diagnostics untouched. `runtime_row` is inserted between `model_row` and `thinking_row`, not on top of metrics/tokens/mode footer. Tests `32 passed`.

4. **Docs/status/memory/zip parity (Q4).** Consistent. `AGENT_STATUS.md`, `chat.md`, `memory.md`, `V5_PRODUCTION_TEST_READINESS_20260512.md`, `FUTURE_SOFTWARE_DEVELOPMENT_LESSONS_20260511.md`, `UI_LIVE_SUPERVISOR_ZIP_VERIFY_20260510.md` all updated to Cells 1–2, 32 tests, combined-UI screenshot. Ship zip SHA `5d06d527...`, 152 members, `testzip None`, `combined_launcher_in_zip True`, `old_widget_ext_in_zip False`, source/zip parity True.

5. **Blockers (Q5).** No HIGH. One MEDIUM (above).

### Required change

**File:** `compact_v5/ui/chat_ui.py` — `_on_mock_mode_change` (around line 1638)

Replace the enable-only client nulling with a symmetric flip that rebuilds the real client when mock is turned OFF:

```python
def _on_mock_mode_change(self, change) -> None:
    enabled = bool(change["new"])
    try:
        from runtime.config import CONFIG
        CONFIG.mock_mode = enabled
        client = getattr(self.agent, "client", None)
        if client is not None and hasattr(client, "mock_mode"):
            client.mock_mode = enabled
            if enabled and hasattr(client, "client"):
                client.client = None
            elif not enabled and getattr(client, "client", None) is None and hasattr(client, "_rebuild_bedrock_client"):
                client._rebuild_bedrock_client()
    except Exception as exc:  # noqa: BLE001
        logging.warning("[chat-ui] Mock Mode update failed: %s", exc)
        self._append_message(
            "system",
            f"Mock Mode update failed: {type(exc).__name__}: {exc}",
        )
    self._render_status()
```

Add a small test in `compact_v5/tests/test_notebook_thin_launcher.py` (or a new ui smoke test) that:
- builds a fake `client` with `mock_mode=False`, `client=<sentinel>`, and a `_rebuild_bedrock_client` that resets `client=<sentinel>`;
- fires `_on_mock_mode_change({"new": True})` → asserts `client.client is None`;
- fires `_on_mock_mode_change({"new": False})` → asserts `_rebuild_bedrock_client` was called and `client.client` is no longer None.

Once that one path is fixed and a regression test pins it, this is APPROVE. Everything else (single-UI requirement, v4-style preservation, runtime wiring for workspace/turns/budget/approval/Bedrock-only/thinking, doc/zip parity) is clean.
