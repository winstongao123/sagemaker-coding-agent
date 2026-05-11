## Review: BLOCK_4_TOOL_CARDS_COLLAPSE_GROUPING

### 1. v5 architecture preserved?
Yes. Block stays inside the rendering layer of `compact_v5/ui/chat_ui.py` and rides on the already-public `tool_gen_callback` contract (`type`, `tool_use_id`, `name`, `input`/`content`, `is_error`) that `core/query_engine.py:1898-1935` emits. No engine, Bedrock, prompt, compactor, security, or subagent code touched.

### 2. Scope drift?
None visible. New UI-only additions:
- `_tool_card_indices: Dict[str, int]` state field (chat_ui.py:287)
- `_render_tool_card()` (chat_ui.py:573-610)
- `_append_tool_call_card()` / `_append_or_update_tool_result_card()` (chat_ui.py:1093-1156)
- Two call sites swapped in `_on_tool_generation` (chat_ui.py:1276-1286)

The `task`-subagent branch still routes through `_parse_subagent_result` before the result-card path, so subagent receipts remain on their dedicated lane.

### 3. Regression risk
- Bedrock request shape: not touched.
- Thinking signatures: not touched.
- Tool dispatch: only the UI consumer of the callback changed; dispatch path unchanged.
- Compaction / final-claim guard / cost & cache accounting: not touched.
- HTML safety: every model/tool-controlled string (`tool_name`, `phase`, `tool_use_id`, `input_text`, `result_text`) flows through `self._escape(...)`. ✓
- Collapsed-by-default: `<details>` opened without the `open` attribute, confirmed by the smoke test (`assert "<details open" not in html`). ✓
- 12k-byte truncation preserved on result path (chat_ui.py:1120-1121).

### Issues

**MEDIUM — `_tool_card_indices` is not cleared on `_on_clear` / `_on_new`**
`compact_v5/ui/chat_ui.py:1380-1391` clears `self._messages` but leaves `self._tool_card_indices` populated with stale `tool_use_id -> index` entries. After the user clears, those stale indices initially get filtered out by the `idx >= len(self._messages)` guard in `_append_or_update_tool_result_card` (chat_ui.py:1124). But once a new conversation re-grows `_messages` past the stale index, a delayed/spurious `tool_result` event reusing a prior `tool_use_id` would pass the guard and silently overwrite an unrelated message's meta. Low probability with random Bedrock tool ids, but a real correctness footgun and an unbounded dict-growth leak across sessions.

Required fix (one line in each handler):
```python
def _on_clear(self, _btn) -> None:
    self.agent.clear()
    self._messages.clear()
    self._tool_card_indices.clear()
    ...

def _on_new(self, _btn) -> None:
    self.agent.clear(reset_budget=True)
    self._messages.clear()
    self._tool_card_indices.clear()
    ...
```

**LOW — legacy stream-derived tool messages render oddly**
`_live_output_router` (chat_ui.py:1202-1208) still parses `[<tool> result]:` lines and appends a `"tool"` message *without* setting `input_text` / `result_text` in meta. `_render_tool_card` will then show the entire `text` as "Tool input", a "(waiting)" result, and a perpetual "running" status. Not a correctness regression (the data is still visible), but visually inconsistent with the new card model. Either pass `{"input_text": "", "result_text": body, "phase": "result from output stream"}` here or document the gap.

**LOW — test coverage gaps**
The smoke test only covers the happy call-then-result path. Worth adding (still cheap):
- `is_error=True` produces `status="error"` and red status color
- A result event with an unknown `tool_use_id` falls through to an appended message rather than touching another message
- The 12k truncation marker appears when `content` is oversized
- After `_on_clear` (simulated), a result for a previously-seen `tool_use_id` does not mutate any new message (would catch the medium issue above)

### 4. Are tests/checks sufficient?
Marginal. The happy path is covered and `py_compile` runs, but the smoke test does not exercise the error / unknown-id / truncation / post-clear paths. For a UI-only block this is acceptable for shipping, but the clear/new gap above should be closed before claiming "done".

### 5. Verdict
**REQUEST_CHANGES** — required: clear `_tool_card_indices` in `_on_clear` and `_on_new` (chat_ui.py:1380-1391). Recommended: fix legacy stream-path meta in `_live_output_router` and extend the smoke test for `is_error`, oversize truncation, and post-clear behavior. Everything else looks clean and within scope.
