Block 6 review complete.

## Block 6 Review: Cost Controls for Simple S3 Inventory

### 1. v5 architecture preservation: YES
- No changes to Bedrock client, request schema, cache boundary, compactor, security gates, or subagent receipts.
- Thinking is suppressed at the Agent layer per turn by passing `thinking_enabled=_thinking_enabled` to `QueryEngine.run` — no signature/schema surgery.
- New guard hooks into the same pattern as the existing final-claim guard (meta message + `continue`).

### 2. Scope drift: LOW
- One out-of-scope item: the UI **tool-card grouping refactor** in `chat_ui.py` (`_render_tool_card`, `_append_tool_call_card`, `_append_or_update_tool_result_card`, `_tool_card_indices`) is a UX restructure, not a cost control. Justifiable as "verbosity" reduction (cards collapsed by default, thinking `<details>` no longer `open`), but it expands the diff beyond the stated scope. Behaviorally low-risk; clearing `_tool_card_indices` in `_on_clear`/`_on_new`/`_on_compact` is correctly wired (chat_ui.py:1416, 1424, 1433).
- Otherwise the changes match the stated four causes: thinking suppression, blocked-retry one-strike, tool_search-aware `aws_s3_list` visibility, and prompt guidance.

### 3. Regression risks

**LOW**
- **Detector breadth** — `_is_simple_s3_inventory_request` (agent.py:144) trips on "s3" + any of {list, inventory, structure, bucket, prefix, files, objects} with no destructive/coding term. Phrases like "what files does my s3 sync to?" or "describe the prefix structure of our s3 data lake" would silently disable thinking. The user-visible `[cost control] Extended Thinking disabled…` line mitigates surprise; the failure mode is "less reasoning" not "broken." Acceptable, but worth knowing.
- **`bash_aws_s3_cli_blocked` always returned by `_predict_guard_failure_class`** for any `aws s3` bash command (query_engine.py:1753). Harmless because `_should_block_class` requires `_class_count >= 1` (recorded failure), so first call still goes to the security manager. Block message text in security/manager.py:300-305 deliberately contains the matched substring "aws s3 cli is blocked by the bash allowlist" — substring matching is correct.
- **Intent-drift guard signal `compact_v5`** could false-trigger on legitimate answers that mention the workspace, but the short-circuit on S3 answer terms (including `aws_s3_list`) and the one-shot `_intent_drift_guard_sent` flag bound the cost to one extra turn.

**NONE OBSERVED**
- Thinking signatures: thinking config block is only sent when enabled; turning off pre-call doesn't break signature pairing because no thinking blocks exist to pair.
- Cache: prompt/system content unchanged; cache key not invalidated by `thinking_enabled` swap.
- Subagent receipts: turn-level flag only; subagents dispatched via `task` retain their own configuration.
- Final-claim guard: intent-drift guard runs only after final-claim guard returned empty (query_engine.py:1109-1127), no double-fire.
- Cost/cache accounting: UI reads `last_effective_thinking_enabled` (chat_ui.py:991-996, 1066-1071) so the "Thinking ON/OFF" badge reflects what was actually sent.

### 4. Test sufficiency: ADEQUATE for smoke

Tests cover the four assertions: detector narrowness, per-turn thinking flip, `aws_s3_list` visibility under tool_search deferral, and the one-strike retry class. **Gap**: no test directly exercises `_dispatch_single_tool_call` to confirm `_should_block_class` triggers on the second attempt — only the class count and message are asserted. Logic is straightforward enough that this is acceptable for a Block-level smoke test. Also no test for the intent-drift guard message generation — easy to add (`_intent_drift_guard_message` is static enough to unit-test).

### 5. Verdict: APPROVE

Two non-blocking notes for follow-up:
- Consider tightening the detector's "files" keyword or requiring co-occurrence of "s3" near an inventory term (e.g., regex `\bs3\b.{0,40}\b(list|bucket|...)\b`) to reduce false positives on "files" alone.
- Add a unit test for `_intent_drift_guard_message` (positive trip, S3-answer short-circuit, blocker short-circuit) — pure function, cheap to cover.
