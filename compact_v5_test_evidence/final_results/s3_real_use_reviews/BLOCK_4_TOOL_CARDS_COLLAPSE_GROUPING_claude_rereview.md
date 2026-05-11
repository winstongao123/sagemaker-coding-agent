## Re-review: BLOCK_4_TOOL_CARDS_COLLAPSE_GROUPING

### 1. v5 architecture & UI-only scope — PRESERVED
Diff touches only `compact_v5/ui/chat_ui.py` (rendering + grouping helpers) and `compact_v5/tests/test_ui_tool_cards_smoke.py` (new). No engine, prompt, security, Bedrock, or tool-dispatch code modified — confirmed both in the patch and in `status.md` drift check.

### 2. Previously identified MEDIUM/LOW findings — RESOLVED

| Prior finding | Resolution | Evidence |
|---|---|---|
| MEDIUM: stale `_tool_card_indices` after Clear/New could mutate the wrong message | Fixed | Diff lines 1390-1404: `self._tool_card_indices.clear()` added in both `_on_clear` and `_on_new`. Also initialized to `{}` in `__init__` (line 287). |
| LOW: legacy output-stream tool result meta inconsistent with new card schema | Fixed | `_live_output_router` now emits `input_text=""`, `result_text=body`, `is_error=False`, so `_render_tool_card` renders it as a normal "done" card. |
| LOW: smoke checks too narrow | Fixed | `test_ui_tool_cards_smoke.py` now covers: grouped happy path, error result phase, stale/unknown id after clear, stream-result rendering, and 12k truncation marker. |

Defensive details that are correct:
- `_append_or_update_tool_result_card` falls back to `_append_message` when the index is missing, out of range, or absent — avoids mutating an unrelated row.
- Meta merge preserves prior `input_text` (`if "input_text" not in meta`) so the input pane isn't blanked when result arrives.
- All user-supplied strings (`tool_name`, `phase`, `tool_use_id`, input/result bodies) flow through `self._escape` before HTML insertion — no new XSS surface.
- `<details>` rendered without `open`, matching the v4 collapsed default; test asserts `<details open` is absent.

### 3. Regression risk on out-of-scope surfaces — NONE OBSERVED
- **Bedrock request shape / thinking signatures / compaction / security / final-claim guard / cost/cache accounting**: untouched.
- **Tool dispatch**: untouched; only the *display* of tool call/result events changed.
- **Subagent receipts**: `task` tool result still routed to `_parse_task_payload` → `_append_message("subagent", ...)` before the card-update branch, so the subagent rendering path is preserved.
- **Truncation behavior**: 12000-char cap retained in `_append_or_update_tool_result_card`, matching prior runtime/audit boundary.

Minor non-blocking note: `_render_tool_card` shows `status="running"` whenever `result_text` is empty. For the stream-result fallback, the result text is populated so it renders as `done` — but in any hypothetical path where only a call card is appended and no result ever arrives, the card stays at `running` indefinitely. Acceptable for now; could be revisited if real-use surfaces orphan calls.

### 4. Verdict
**APPROVE**
