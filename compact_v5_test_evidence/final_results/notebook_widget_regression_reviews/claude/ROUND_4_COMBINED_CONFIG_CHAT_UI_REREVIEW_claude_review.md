## Re-review (Round 4)

### 1. Round-3 MEDIUM blocker — FIXED

`compact_v5/ui/chat_ui.py:1638-1660` now correctly handles the OFF path:

- Sets `client.mock_mode = False` **before** calling rebuild (critical — `_rebuild_bedrock_client` at `runtime/bedrock_client.py:256` early-returns if `self.mock_mode` is True).
- Only rebuilds when `client.client is None`, so it doesn't blow away a healthy live client.
- Wraps the whole thing in try/except with a user-visible system message + warning log, which is the right behavior for a notebook toggle that can fail on IAM/region issues.
- `_rebuild_bedrock_client` exists on `BedrockClient` (`runtime/bedrock_client.py:254`) and the normal chat-UI path constructs `BedrockClient(model_id, region, mock_mode)` without an external client (`ui/chat_ui.py:1814-1818`), so `_external_client = False` and the rebuild will actually execute.
- Regression test `test_combined_ui_mock_mode_toggle_rebuilds_real_client_when_disabled` exercises both transitions and asserts `rebuild_count == 1` and `client is not None`. Verified locally: `33 passed`.

### 2. Combined config/chat UI requirement — STILL HOLDS

- `launch_ui()` in `entry.py:420-436` is the single user path; thin-launcher test passes.
- New runtime controls (`Workspace`, `Max Turns`, `Iter Budget`, `Mock Mode`) are added inside `V4WidgetChatUI` and placed on `runtime_row` inserted into the single root `VBox` panel (`ui/chat_ui.py:495-517`). One displayed widget contains config + chat.
- Visual checks confirm: `HAS_SINGLE_COMBINED_UI True`, `HAS_SEPARATE_AGENT_CONFIG_HEADING False`, plus all expected control flags True.

### 3. Remaining HIGH/MEDIUM blockers — none

- Zip integrity: 152 members, `testzip None`, parity True, forbidden 0, old-widget-ext absent.
- Source/zip SHA parity verified for the changed files (`chat_ui.py`, `entry.py`, `chat.ipynb`, etc.).
- Order-of-operations on the mock toggle is correct (mock_mode set before rebuild call).
- Error path on rebuild failure surfaces to the user, doesn't silently brick the agent.

One minor observation, not a blocker: if a future caller constructs `BedrockClient(..., client=external_client)`, `_external_client=True` causes `_rebuild_bedrock_client` to return False without rebuilding, leaving the agent stuck with `client=None`. This doesn't affect the normal chat UI path. No change required for ship.

## VERDICT: APPROVE

Round-3 mock-mode rebuild blocker resolved with a correct fix and a targeted regression test. The single combined config/chat UI requirement is satisfied by `launch_ui()`, the thin-launcher test, the new `runtime_row` placement inside the root `VBox`, and the visual checks. 33 tests pass, zip integrity verified, no remaining HIGH/MEDIUM blockers. Safe to commit and push.
