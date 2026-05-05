I have enough canonical context. Reconstructing scope independently, then writing the review.

---

```text
EXPECTED ROW COUNT: 3
LEDGER ROW COUNT: 3
DISPOSITION COUNTS:
- SHIPPED: 3
- PARTIAL: 0
- MISSING: 0
- DEFERRED_USER_APPROVED: 0
- DROPPED_USER_APPROVED: 0
- N/A_CONSTRAINT: 0

REVIEWED ROWS:
- SOFTWARE-ASYNC-DECISION-1: APPROVE - DS3-S6 decision row. Code evidence verified: `tools/task.py:158` declares `is_concurrency_safe=False`; `_DESCRIPTION` (lines 33-57) explicitly states "sub-agent runs to completion before returning" and "sub-agents are one-shot". Lock test `test_task_tool_declares_sync_one_shot_no_background_contract` asserts is_concurrency_safe is False AND description contains "runs to completion", "one-shot", "final answer". Test passes per `software-async-decision-tests.log` (2 passed). DECISIONS.md SAD-001 states the deferral with rationale tied to SageMaker notebook constraints — matches third-scan recommendation in `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md:111` and `:148-149`.
- SOFTWARE-ASYNC-DECISION-2: APPROVE - Future-block handoff row. Code evidence verified: `coordinator/__init__.py:19-23` docstring contains both "no async sub-agent channel" and "run sync to completion"; `coordinator/system_prompt.py:85-86` reinforces "every `task` call spawns a worker that runs synchronously to completion". Lock test `test_coordinator_docs_state_async_channel_is_not_in_v5` asserts both phrases are present. Doc evidence (`BLOCK_ORDER_AND_COVERAGE.md:56`, `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md:164-166`) confirms `SOFTWARE-SUBAGENT` and `SOFTWARE-GATE` remain in the redo queue and own structured envelopes / `/done` consumption respectively. No future obligation silently dropped.
- SOFTWARE-ASYNC-DECISION-3: APPROVE - No-false-async-UX row. Code evidence verified: `tools/task.py:60-79` input schema only exposes `description`, `prompt`, `subagent_type` properties; required is only `["prompt"]`. Repo-wide grep for `job_id|background_job|poll_subagent|background_subagent|async_task_tool` returns only the lock test itself — no production exposure of async/job/poll/wait/kill APIs. Lock test asserts `props.isdisjoint({"async","background","job_id","poll","wait","kill"})`. The `search_hint` string includes "background" but is an internal tool-discovery field, not a contract surface, and the `_DESCRIPTION` and schema explicitly contradict any background semantics — acceptable.

FINDINGS:
- MINOR `blocks/SOFTWARE-ASYNC-DECISION/LEDGER.md`: Ledger lacks the standard summary footer required by `03_LEDGER_SCHEMA.md` (`EXPECTED_ROWS`, `LEDGER_ROWS`, `SHIPPED`, `PARTIAL`, `MISSING`, `SHIP_BLOCKING_ROWS`). `STATUS.md` does carry the row counts (3 expected / 3 ledger / 0 ship-blocking), and `BLOCK_ORDER_AND_COVERAGE.md` documents that software-builder blocks use a manual ledger format outside `scope_audit.py`, so this is a docs-completeness issue, not a substantive scope gap. Recommend adding the footer for consistency with canonical blocks.
- MINOR `blocks/SOFTWARE-ASYNC-DECISION/LEDGER.md`: Manual ledger uses a custom column layout (`gap_id`, `requirement`, `decision`, `doc_evidence`) instead of the canonical schema's (`capability`, `source`, `priority`, `fit`, `expected_target`, `port_log`, `adr`, `historical_review`, `git_evidence`). `BLOCK_ORDER_AND_COVERAGE.md:23-25` explicitly authorizes this for software-builder blocks because they are not parsed by `scope_audit.py`. Acceptable, flagged for transparency.
- INFO `tools/task.py:162`: `search_hint` includes the word "background" in its tool-discovery string. This is not a model-facing contract field and the lock test does not flag it. Mentioned only because the worker's "no false async UX" claim is otherwise tight; a future cleanup could remove "background" from the hint.

DISPUTED FINDINGS:
- NONE: Worker did not dispute any prior finding (this is iteration 1 review).

REMAINING SHIP-BLOCKING ROWS: 0

VERDICT: APPROVE
SHIP DECISION: READY_FOR_BLOCK_CLOSE_REVIEW
```

---

Review complete. The block honestly ships the async/background scope decision as a documented deferral without exposing any false pollable/background API. DS3-S6 scope from `THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` and `PS_CODEX_3RD_SCAN_SOFTWARE_BUILDER_REQUIREMENTS.md` is faithfully reconstructed across the 3 manual ledger rows; future `SOFTWARE-SUBAGENT` and `SOFTWARE-GATE` obligations remain explicitly in scope per `BLOCK_ORDER_AND_COVERAGE.md` and `DECISIONS.md` SAD-001. Two minor ledger-format observations are noted but not ship-blocking for a decision-only block.
