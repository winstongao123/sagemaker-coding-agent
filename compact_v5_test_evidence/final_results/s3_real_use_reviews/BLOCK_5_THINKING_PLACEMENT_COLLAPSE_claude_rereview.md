Re-review complete. Both smoke tests pass locally.

## Verification of fixes

**1. Defensive index check in `_append_or_update_tool_result_card`** (chat_ui.py:1116-1169) — Verified. Reads the stored message, requires `role == "tool"` AND `tool_use_id` equality before mutating; otherwise appends a fresh card. The stale-pointer test (`test_tool_card_error_unknown_and_clear_paths`, lines 83-95) exercises the path where the index points at an `"assistant"` message and confirms a new card is appended at index 1 without overwriting message 0.

**2. `_on_compact` clears `_tool_card_indices`** (chat_ui.py:1423) — Verified, alongside `_on_clear` (1407) and `_on_new` (1414).

**3. Status.md declares the Block 4 follow-up** — Status drift check item 2 names the defensive map fix as explicitly in scope for Block 5.

**4. Test coverage** — `test_ui_tool_cards_smoke.py` covers: collapsed grouped card, stale index → assistant message fallback, cleared map fallback, error status rendering, stream-only result via `_live_output_router`, and 13000-char truncation. `test_ui_thinking_smoke.py` covers placement-before-metrics + `<details open>` absence in both the turn meta and standalone thinking card.

**5. Stream-only path** — chat_ui.py:1219-1229 now emits `input_text="(stream-only; input not captured)"`, so `_render_tool_card`'s `(waiting)` placeholder is replaced with an explicit explanation. Tool result still surfaces as `done`, no misleading "waiting" pane.

## Answers

1. **v5 architecture / UI-only scope preserved?** Yes. Diff is contained to `compact_v5/ui/chat_ui.py` plus the two test files. No engine, prompt, Bedrock, security, compaction, or registry surface touched. `git status` confirms.
2. **MEDIUM issues resolved?** Yes — all four (defensive map check, compact clears the map, status doc clarifies cumulative Block 4 inclusion, stream-only no longer misleading).
3. **Remaining HIGH/MEDIUM risk to Bedrock request shape / thinking signatures / tool dispatch / compaction / security / final-claim guard / subagent receipts / cost+cache accounting?** None observed. The thinking change is purely the `<details>` default-open flag and DOM ordering inside the turn-meta footer; signed thinking blocks in runtime messages and Bedrock payloads are not affected. Tool dispatch path in `_on_tool_event` (1297-1306) routes through the new helpers which preserve the same `_append_message` semantics. Subagent receipt path for `name == "task"` (1303) is unchanged. Metrics summary still contains `Prompt Cache R/W` (asserted by test).
4. **Verdict: APPROVE.**
