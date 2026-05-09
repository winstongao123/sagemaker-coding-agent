You are Claude Opus acting as an independent final pre-user-test reviewer.

Repo: D:\Github\sagemaker-coding-agent
Production artifact: D:\Github\sagemaker-coding-agent\compact_v5.zip

Important local-state note:
- The working tree may contain a local accidental extraction at `compact_v5/compact_v5`.
- Review the production ZIP and the evidence files below. Do not fail the artifact
  because of unrelated local working-tree noise unless the ZIP itself is wrong.

Review targets:

1. Inspect `compact_v5.zip` using Python/zipfile or equivalent. Confirm:
   - zip integrity passes,
   - it includes `compact_v5/chat.ipynb`, `compact_v5/entry.py`,
     `compact_v5/ui/chat_ui.py`, `compact_v5/core/query_engine.py`,
     `compact_v5/runtime/bedrock_client.py`, and
     `compact_v5/docs/htmls/V5_DESIGN_OVERVIEW.html`,
   - it excludes `_status`, `_phase_2`, `MAIN`, PowerBI skill, and PS_PS final-test prompts.

2. Inspect these evidence files:
   - `compact_v5_test_evidence/final_results/CRITICAL_BEDROCK_THINKING_SIGNATURE_REGRESSION.md`
   - `compact_v5_test_evidence/final_results/CRITICAL_UI_PER_TURN_METRICS_GAP.md`
   - `compact_v5_test_evidence/final_results/PS_TEST_REVIEW_FINAL.md`

3. Inspect the ZIP's extracted source or the corresponding current source files for:
   - `runtime/bedrock_client.py` signed-thinking handling,
   - `core/query_engine.py` assistant-history replay,
   - `ui/chat_ui.py` per-assistant-turn cache/cost/reasoning display,
   - `chat.ipynb` normal UI setup path.

Questions:

1. Is the Bedrock thinking-signature bug fixed without reintroducing invalid unsigned thinking replay?
2. Does the UI now expose per-assistant-turn cache/cost/reasoning evidence in addition to footer metrics?
3. Is the production zip valid and minimal enough for SageMaker install?
4. Are the current docs/evidence sufficient for the user to understand what changed and why prior tests missed it?
5. Is it ready for the user to run the next SageMaker acceptance test, assuming they install the latest zip and restart the kernel?

Output exactly:

VERDICT: APPROVE_FOR_USER_TEST or REQUEST_CHANGES
DRIFT DECISION: NO_DRIFT or DRIFT_FOUND
ZIP DECISION: VALID or INVALID

Then list concise findings with file/path evidence. If requesting changes, give exact fixes.
