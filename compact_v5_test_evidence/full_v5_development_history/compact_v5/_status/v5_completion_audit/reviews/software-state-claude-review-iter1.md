I have enough context to render the review. I read the canonical context, reconstructed the SOFTWARE-STATE rows from the third-scan docs (DS3-S1/S2/S3/S11 + PS3-1/2/3), inspected each changed file, ran-down each ledger row's evidence, and verified the test logs.

Key findings:
- The 5 rows in `LEDGER.md` map cleanly to the third-scan canonical sources: DS3-S1+PS3-2 → row 1; DS3-S2+PS3-1 → rows 2 and 3; DS3-S3+DS3-S11+PS3-3 → row 4; DS3-S11 → row 5.
- All code citations resolve: `runtime/state.py` provides `DurableStateManager` with atomic writes; `tools/todo.py` mirrors writes/loads via `STATE`; `commands.py` adds `status_memory` + `recovery` to session metadata and gates extraction behind `CONFIG.enable_memory_extraction`; `agent.py` reloads status/memory each top-level run, journals `turn_start`/`turn_finish`, and writes `last_turn.json`.
- Tests in `test_software_state.py` exercise each row; `software-state-tests.log` and `software-state-regression-tests.log` both show `4 passed`. `software-state-py-compile.log` shows `PASS`.
- Memory extraction path uses ctx-injected `extract_fn` and only fires when `CONFIG.enable_memory_extraction=True`; default zero-cost. No AWS/R-tier calls in any test or code path inspected.
- The 03 schema has different columns (PORT_LOG/ADR), but `BLOCK_ORDER_AND_COVERAGE.md` explicitly authorizes a separate ledger pattern for `SOFTWARE-*` blocks; `DECISIONS.md` substitutes for ADR/PORT_LOG.

Specific review-prompt asks:
- Prompt-cache choice: `prompt_cache_now=bool(state_blocks)` is acceptable. The state blocks live after `CACHE_BOUNDARY`, but the engine hashes the full system prompt; without `allow_now=True`, the engine would freeze the first-turn status/memory and silently strip later changes. The decision is documented in `DECISIONS.md` and the test proves status v1 → v2 actually reaches the model. Trade-off is a per-top-level-turn cache-write; that is an acceptable cost for the durable-state goal.
- `last_turn.json` + `turn_journal.jsonl` sufficiency: yes for this block. `last_turn.json` is atomically replaced (tempfile + `os.replace`) with messages/todos/token_stats/status_memory/result; the JSONL journal is appended per `turn_start`/`turn_finish`/`resume`. Named checkpoint indexes are correctly deferred to `SOFTWARE-CHECKPOINT`.

```text
EXPECTED ROW COUNT: 5
LEDGER ROW COUNT: 5
DISPOSITION COUNTS:
- SHIPPED: 5
- PARTIAL: 0
- MISSING: 0
- DEFERRED_USER_APPROVED: 0
- DROPPED_USER_APPROVED: 0
- N/A_CONSTRAINT: 0

REVIEWED ROWS:
- SOFTWARE-STATE-1: APPROVE - DS3-S1/PS3-2 met. Code: runtime/state.py:130-151 (atomic save_todos/load_todos), tools/todo.py:44-66 (_persist_todos / _load_todos_from_disk_if_available), executors call restore_todos(persist=True). Test: test_software_state.py::test_todos_persist_across_memory_reset asserts in-memory reset still rehydrates from .sageagent_state/todos.json. Decision evidence in DECISIONS.md. No AWS.
- SOFTWARE-STATE-2: APPROVE - DS3-S2/PS3-1 met. Code: commands.py:329-357 (cmd_save persists todos, status_memory, tokens_stats, recovery paths) and 364-407 (cmd_resume restores messages, todos, tokens). Test: test_save_resume_round_trip_includes_todos_status_memory verifies the metadata payload, recovery.last_turn_path, and todo round-trip. Decision evidence in DECISIONS.md. Regression: B+ save/resume tests still pass (software-state-regression-tests.log). No AWS.
- SOFTWARE-STATE-3: APPROVE - DS3-S2/PS3-1 crash-safe journaling met. Code: state.py:153-198 (append_journal, atomic save_turn_recovery), agent.py:209-217 turn_start journal, agent.py:237-256 atomic last_turn.json + turn_finish journal. Atomic write via tempfile + os.replace; journal append-flush is crash-safe. Test: test_agent_refreshes_status_and_memory_every_run asserts both .sageagent_state/turn_journal.jsonl and last_turn.json exist after a run. Decision evidence in DECISIONS.md. Auto-restore UI prompt explicitly out-of-scope (handled by SOFTWARE-GATE/UI later); durable data is in place. No AWS.
- SOFTWARE-STATE-4: APPROVE - DS3-S3/DS3-S11/PS3-3 met. Code: agent.py:60-89 (load_agent_status_text, load_agent_memory_text, _load_agent_state_context_blocks reads files at every top-level run() unless system_prompt is overridden); agent.py:166-191 appends fresh blocks after CACHE_BOUNDARY; agent.py:230 forces prompt_cache_now=True so refreshed text actually reaches the model. Test: test_agent_refreshes_status_and_memory_every_run mutates AGENT_STATUS.md/memory.md between runs and asserts run 2's system prompt contains v2 and not v1. Decision evidence in DECISIONS.md. Regression: B+ test_agent_status_auto_load and test_agent_status_auto_load_disabled still pass.
- SOFTWARE-STATE-5: APPROVE - DS3-S11 met as zero-cost opt-in. Code: commands.py:410-434 _maybe_extract_memory_on_save short-circuits unless CONFIG.enable_memory_extraction=True; uses memory.create_memory_extractor + ctx-injected memory_extract_fn (no LLM call inside the test path). Default path stays zero-cost. Test: test_save_can_run_zero_cost_memory_extraction_path injects a fake extract_fn and verifies memory.md is written; default tests do not enable the flag, so no AWS calls. Decision evidence in DECISIONS.md. Real-LLM extraction explicitly deferred to AWS/R-tier per scope.

FINDINGS:
- INFO LEDGER.md schema: SOFTWARE-* ledger columns (gap_id/requirement/implementation/doc_evidence) diverge from 03_LEDGER_SCHEMA.md (port_log/adr/historical_review/git_evidence). BLOCK_ORDER_AND_COVERAGE.md authorizes this for SOFTWARE-* blocks (`scope_audit.py` does not parse them), so this is informational, not ship-blocking. Recommend DECISIONS.md substitutes adequately for ADR/PORT_LOG here.
- INFO agent.py:230 prompt-cache: forcing allow_now=True on every top-level run() with state_blocks invalidates the model_id/tool_names invariant in addition to the system-prompt invariant. In practice tools/model rarely change between runs, but if a future block injects tools per-turn, that change would now also bypass the v5.0.1 deferral policy silently. Not a blocker for SOFTWARE-STATE; flag for SOFTWARE-GATE/SOFTWARE-SUBAGENT to revisit.
- INFO commands.py:329-357 cmd_save: status_memory metadata caps each text at 12000 chars (state.py:110), but session metadata also stores full message buffer; this is consistent with the cap-then-store contract documented in DECISIONS.md.

DISPUTED FINDINGS:
- NONE

REMAINING SHIP-BLOCKING ROWS: 0

VERDICT: APPROVE
SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW
```

Review complete. The 5 SOFTWARE-STATE rows all show concrete code, test, and decision evidence; no AWS/R-tier spend was performed or claimed; the prompt-cache choice and per-turn journal/last-turn recovery files are acceptable for this block's scope.
