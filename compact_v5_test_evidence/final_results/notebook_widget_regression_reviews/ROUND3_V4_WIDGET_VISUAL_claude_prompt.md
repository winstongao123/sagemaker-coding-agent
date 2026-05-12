You are an independent reviewer for compact_v5, a SageMaker notebook coding
agent. You are not the implementer.

Review the latest notebook widget regression fix in this repository.

Context:
- The user rejected a previous non-widget fallback because v5 must keep a
  v4-style ipywidgets UI as the normal product surface.
- The visible failure was `Error displaying widget: model not found` in
  `compact_v5/chat.ipynb` Cell 2 and Cell 3.
- Local visual testing found that the notebook file had no saved widget outputs,
  and the likely missed cause was a reused Jupyter kernel executing stale
  imported launcher/UI modules while the cell source looked updated.

Changed files to inspect:
- `compact_v5/chat.ipynb`
- `compact_v5/entry.py`
- `compact_v5/tests/test_notebook_thin_launcher.py`
- `compact_v5/chat.md`
- `compact_v5/AGENT_STATUS.md`
- `compact_v5_test_evidence/final_results/NOTEBOOK_WIDGET_REGRESSION_20260511.md`
- `compact_v5_test_evidence/final_results/FUTURE_SOFTWARE_DEVELOPMENT_LESSONS_20260511.md`

Review requirements:
1. Confirm the shipped notebook default is again the v4-style ipywidgets path,
   not the console fallback.
2. Confirm Cell 2 remains reasonably thin and refreshes only the launcher/UI
   modules needed to avoid stale-kernel execution.
3. Confirm `launch_config_ui()` and `launch_chat_ui()` still keep an explicit
   console/headless fallback through `use_widgets=False`.
4. Confirm the fix does not drift into engine, prompt, tool, security, or
   runtime behavior.
5. Confirm docs/status/lessons honestly explain the fallback detour, stale
   kernel/module-cache lesson, and local visual evidence.
6. Confirm tests lock the notebook contract and do not require real Bedrock.
7. Identify any HIGH or MEDIUM regression risk. If none, say APPROVE.

Known local validation evidence:
- `compact_v5_test_evidence/final_results/notebook_widget_regression_reviews/local_visual/06_final_after_cell2_widgets.png`
  shows the real config widgets rendered.
- `compact_v5_test_evidence/final_results/notebook_widget_regression_reviews/local_visual/07_final_after_cell3_chat.png`
  shows the dark v4-style chat surface.
- Browser text check after running Cell 2 and Cell 3:
  - `HAS_WIDGET_ERROR False`
  - `HAS_AGENT_HEADER True`
  - `HAS_CONFIG_HEADING True`
  - `HAS_READY True`
  - `HAS_SEND_BUTTON True`
- `python -m pytest compact_v5/tests -q` passed: 29 passed.

Please return:
- VERDICT: APPROVE or REQUEST_CHANGES
- Findings ordered by severity with file/line references
- Any non-blocking notes
