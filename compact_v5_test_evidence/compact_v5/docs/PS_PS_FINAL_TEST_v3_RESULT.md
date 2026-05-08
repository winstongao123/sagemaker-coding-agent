# PS_PS_FINAL_TEST_v3_RESULT

Date: 2026-05-07

Purpose: record the final v5 Haiku long-running software-engineering acceptance
run after fixing subagent evidence persistence and Bedrock tool-result pairing.

## Final Verdict

`PASS` for the stricter local/AWS v5 acceptance benchmark.

This does not mean future bugs are impossible. It means the specific long-running
coding/research/review workflow now passed with real Bedrock Haiku, saved helper
evidence, validated package output, green tests, cache/cost telemetry, and a clean
`end_turn` stop reason.

## Final v5 Run

| Check | Result |
|---|---|
| Model | `au.anthropic.claude-haiku-4-5-20251001-v1:0` |
| Region | `ap-southeast-2` |
| Budget cap | `$5.00` |
| Final run cost | `$0.714589` |
| API calls | `55` |
| Stop reason | `end_turn` |
| Required live files | `18 / 18` |
| Tests in generated project | `76 passed` |
| Result zip | valid |
| Zip size | `124,043` bytes |
| Zip members | `58` |
| Subagent used | yes, `plan` |
| Subagent cost | `$0.049975` |
| Session cache read/write | `1,967,864 / 159,492` tokens |
| Acceptance gate | `true` |

Evidence:

- `compact_v5/_status/ps_ps_v3_compare/logs/v5-summary.json`
- `compact_v5/_status/ps_ps_v3_compare/logs/v5-agent-output.log`
- `compact_v5/_status/ps_ps_v3_compare/logs/v5-agent-final.txt`
- `compact_v5/_status/ps_ps_v3_compare/logs/v5-pytest.log`
- `compact_v5/_status/ps_ps_v3_compare/PS_PS_V3_COMPARE_REPORT.md`
- `D:/Github/sageagent_psps_v3_compare_workspaces/v5/mini_release_auditor_result.zip`

## What Failed Before The Final Pass

| Problem found | Why it mattered | Fix made | Lock evidence |
|---|---|---|---|
| v5 could use a subagent but fail to leave a review artifact in `docs/reviews/`. | Long work needs helper/reviewer receipts, not only a chat line. | `task` now always persists receipts to `.sageagent_state/subagents/`, `docs/reviews/`, and `docs/logs/subagent_artifacts.log`; prompts require real `task` use when reviewer evidence is requested. | `test_task_tool_persists_review_receipt_in_docs_reviews`; final v5 run has `docs/reviews/20260507T131946Z-plan-028289457dcf.md`. |
| The benchmark could pass even when the agent ended with `fatal_error`. | That would hide a real long-session failure. | `run_agent_compare.py` now requires `stop_reason == "end_turn"` and pytest return code `0`. | Final `v5-summary.json` has `acceptance_pass: true` and `stop_reason: end_turn`. |
| Auto-compact summary could send an assistant `tool_use` without an immediate matching `tool_result`. | Bedrock rejects invalid tool pairing, which breaks long sessions. | Compaction summary input repairs missing tool results before the LLM summary call. | `test_compactor_summary_input_repairs_dangling_tool_use`. |
| Compaction could keep a recent `tool_result` after summarizing away the matching `tool_use`. | Bedrock sees an orphan receipt and rejects the next request. | Orphaned typed `tool_result` blocks are converted to plain text before model calls. | `test_compactor_compact_converts_orphan_tool_result_from_recent_window`. |
| Recovery/compaction could produce duplicate typed results for one tool id. | Bedrock allows exactly one `tool_result` per `tool_use`. | Duplicate typed results are converted to plain text; every chat call gets a final pairing repair. | `test_compactor_repair_converts_duplicate_tool_result_to_text`; `test_engine_repairs_invalid_tool_result_pairs_before_api_call`. |

## Explain It Like You Are 9

v5 had to build a small real software project. At first, it could build the
project but sometimes forgot to put the helper's note into the review folder.
Then it sometimes packed the conversation backpack wrong: a tool receipt was not
next to the tool request, so AWS said "I cannot read this."

We fixed both:

- helper notes are now saved automatically;
- before every model call, v5 checks that tool requests and tool receipts match.

The final run built the project, saved the helper note, passed tests, made a real
zip, showed cache/cost numbers, and ended cleanly.
