# BLOCK_5_THINKING_PLACEMENT_COLLAPSE — Review

## Q1. v5 architecture preserved?
Yes. Engine (`core/query_engine.py`), prompts, Bedrock request shape, signed-thinking blocks, runtime message tuples passed to the model — none are touched. All changes live in `compact_v5/ui/chat_ui.py` (display layer, `_messages` is the UI shadow list, not the runtime conversation) and a new test file.

## Q2. Scope drift?
**Yes — material drift.** The block name and goal are "thinking placement/collapse only", but the diff bundles a sizeable **tool-card rendering refactor** that is unrelated to thinking:

- New state `self._tool_card_indices: Dict[str, int]` (chat_ui.py:287)
- New method `_render_tool_card` (chat_ui.py:573–610) replaces the inline tool pre-block
- New methods `_append_tool_card` / `_append_or_update_tool_result_card` (chat_ui.py:1093–1156) coalesce tool call + result into one card keyed by `tool_use_id`
- Tool-event dispatcher rewired (chat_ui.py:1284–1293 area) and stream-router tool branch given new meta keys (chat_ui.py:1206–1216)
- `_on_clear` / `_on_new` extended to clear the new index dict (chat_ui.py:1392, 1400)

This is still UI-only, but it is **beyond the stated block scope**. Per the DONE-Definition rule, this should either be (a) split into its own block, or (b) explicitly noted in the status.md as an in-scope expansion with rationale. The status.md only says "UI placement/collapse for thinking visibility" — the tool-card refactor is undeclared.

## Q3. Regression risk to listed surfaces?
- Bedrock request shape: **no change** (UI shadow list only).
- Thinking signatures: **no change** — `_render_turn_meta` only reorders `thinking_html` above the summary div and removes the unconditional `<details open>` on the standalone thinking role card. Signed thinking blocks for the model are produced elsewhere (engine/query_engine) and untouched.
- Tool dispatch: **no change** to dispatch path; only the UI representation of `tool_generation` / `tool_result` events changes.
- Compaction, security, final-claim guard, subagent receipts, cost/cache accounting: **untouched**.

**One structural hazard, MEDIUM:** `_append_or_update_tool_result_card` (chat_ui.py:1116–1156) trusts the stored index without verifying it still points at a tool message with the matching `tool_use_id`:
```python
idx = self._tool_card_indices.get(tool_use_id) if tool_use_id else None
if idx is None or idx < 0 or idx >= len(self._messages):
    # fall through to append
...
self._messages[idx] = (role, text, ts, meta)
```
- `_tool_card_indices` is **not** cleared by `_on_compact` (chat_ui.py:1405) or anywhere `agent.replace_messages(...)` runs. The UI shadow `_messages` is not rebuilt by compact today, so this is latent — but the moment any future path (e.g. resume/restore via `/resume` dispatch) reassigns `_messages`, a stale `tool_use_id → index` mapping can overwrite the wrong message (potentially an assistant message), silently corrupting render state.

**Required fix:** before `self._messages[idx] = ...`, verify `role == "tool"` and `old_meta.get("tool_use_id") == tool_use_id`; otherwise fall through to the append branch. Also clear `_tool_card_indices` in `_on_compact` for parity with `_on_clear` / `_on_new`.

## Q4. Tests sufficient?
**No — they only cover the declared scope.** `test_ui_thinking_smoke.py` exercises:
- collapsed `<details>` (no `open`) on turn-meta thinking
- thinking placed before `sageagent-turn-metrics`
- Prompt Cache R/W still in metrics
- standalone thinking role card collapsed

Missing for the actual diff scope:
- No test that a `tool_generation` followed by `tool_result` with the same `tool_use_id` produces **one** card (the call+result coalescing).
- No test for the `is_error=True` path (red status pill).
- No test for the staleness scenario above (mismatched index after `_messages` rebuild).
- No test for the missing-`tool_use_id` fallback.

## Q5. Verdict: REQUEST_CHANGES

### Required (MEDIUM)
1. **Defensive index check** in `_append_or_update_tool_result_card` (chat_ui.py:1138–1154): verify `role == "tool"` and stored `tool_use_id` matches before mutating; else append.
2. **Clear `_tool_card_indices` in `_on_compact`** (chat_ui.py:1405) for parity with clear/new, so future rebuilds of `_messages` cannot leave stale pointers.
3. **Scope honesty:** either move the tool-card refactor to its own block, or update `BLOCK_5_..._status.md` to declare it explicitly with rationale (and rename to e.g. `THINKING_PLACEMENT_AND_TOOL_CARDS`). Per DONE-Definition rule, silent scope expansion is what we're guarding against.
4. **Add tests** for the tool-card coalescing (call+result merge, error state, missing tool_use_id fallback). Without them, the bundled refactor is untested.

### Nice-to-have (LOW)
- `_live_output_router` tool branch (chat_ui.py:1206–1216) appends a tool card with `input_text=""`, which renders as a permanent `(waiting)` in the Tool input pane. Consider either omitting the input pane when no input is known, or labeling it "(stream-only; input not captured)" so users don't think the call is hung.
