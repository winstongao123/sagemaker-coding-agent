# R13 Phase B Iter2 Failure Diagnosis

Date: 2026-05-05

AWS call: R13 call 2

Result: pytest passed, but worker classifies the run as not READY.

Raw log: `compact_v5/_status/codex_reviews/r-tier-R13-aws-call2.log`

Observed behavior:

- The agent created `solutions.py`.
- All five deterministic task tests passed.
- Side metrics recorded `score_passed=5`, `score_total=5`, `cost_usd=0.0471`.
- The agent result still ended with `stop_reason=fatal_error` after a Bedrock
  throttling error: `Too many requests, please wait before trying again`.

Worker classification:

- Not READY. Correct artifacts are necessary but not sufficient; the R-tier
  loop also requires clean process behavior. A final `fatal_error` stop reason
  would be weak Phase C evidence even though the code scored 5/5.

Root cause:

- The R13 runner waited for the model loop to end naturally after the solution
  already passed all local tests.
- That allowed an unnecessary follow-up Bedrock turn after success, which hit a
  transient throttle and changed the final stop reason to `fatal_error`.

Fix applied:

- `compact_v5/MAIN/agent/tests/r_tier/test_r13_coding_accuracy.py` now has
  `_all_solution_tests_pass()`.
- The R13 `on_stop_check` returns true once `solutions.py` exists and the full
  five-test fixture passes.
- Metrics `completed` now requires `stop_reason in {"end_turn", "user_stop"}`.
- The final assertion now rejects non-ready stop reasons, including
  `fatal_error`.

Local gates after fix:

- `py -3.11 -m py_compile compact_v5/MAIN/agent/tests/r_tier/test_r13_coding_accuracy.py compact_v5/MAIN/agent/runtime/bedrock_client.py compact_v5/MAIN/agent/tests/unit/test_bedrock.py` passed.
- `py -3.11 -m pytest compact_v5/MAIN/agent/tests/unit/test_bedrock.py compact_v5/MAIN/agent/tests/r_tier/test_r13_coding_accuracy.py -q` -> `12 passed, 1 skipped`.
- `py -3.11 -m pytest compact_v5/MAIN/agent/tests/integration/test_block_a.py -q` -> `53 passed`.

Retry decision:

- One retry remains under the three-call discipline if call #1 is counted.
- Local R13 spend to account for before retry is `$0.0471`, leaving `$0.4529`
  under the `$0.50` R13 cap.
- Retry requires fresh Claude Phase A approval and a fresh AWS Budget check.
