# compact_v5 Production-Test Readiness - 2026-05-12

## Verdict

compact_v5 source and `compact_v5_ship.zip` are ready for target SageMaker
validation. After the user's fresh SageMaker screenshot still showed
`Error displaying widget: model not found`, v5 was aligned more literally with
latest v4.10.10: Cell 1 no longer installs `jupyterlab_widgets` or
`widgetsnbextension` from inside the notebook.

Confidence: **98% for source/package readiness; target SageMaker retest
required after the v4-dependency alignment fix**.

This is not a claim of zero production risk. It means the source, package,
S3 real-use blockers, tests, review evidence, and zip verification are strong,
but the target SageMaker widget manager still must pass a real smoke test.

## Evidence Table

| Area | v4 / Runnable reference | v5 current state | Evidence |
|---|---|---|---|
| Latest v4 baseline | Latest tracked v4 is v4.10.10 at `3ba3425`. | Compared against `compact_v4/MAIN/agent`, not an old archive. | `compact_v4/MAIN/agent/chat.ipynb`; `compact_v4/MAIN/agent/sagemaker_agent.py`. |
| Notebook user contract | v4 uses SageMaker/Jupyter ipywidgets as the normal UI. | v5 default is one v4-style combined ipywidgets UI: config controls and chat live in the same displayed widget. Console fallback is explicit only with `use_widgets=False`. | `compact_v5/chat.ipynb`; `compact_v5/entry.py`; `compact_v5/ui/chat_ui.py`. |
| Thin launch cells | v4 was familiar but carried long config/launch cells. | v5 Cell 2 is a thin combined launcher; logic lives in `entry.py` and `ui/chat_ui.py`. | `compact_v5/tests/test_notebook_thin_launcher.py`. |
| Widget regression | v4 rendered widgets; v5 temporarily showed `model not found`, then still had config separated from chat. | v5 refreshes launcher/UI modules in Cell 2, matches v4's dependency posture by not installing frontend widget extension packages, and launches one combined config/chat UI. | Local Jupyter/Playwright from rebuilt ship zip: `HAS_MODEL_NOT_FOUND False`, `HAS_SEPARATE_AGENT_CONFIG_HEADING False`, `HAS_SINGLE_COMBINED_UI True`, `HAS_CHAT_INPUT True`, `HAS_LINE_METRICS True`, `HAS_OLD_WIDGET_INSTALL False`. |
| Tool visibility | Runnable has strong tool/progress affordances; v4 had better visible flow than early v5. | v5 has live output routing and collapsed/grouped tool cards. | UI smoke tests and Claude UI reviews. |
| Model asks user for input | v4 `ask_user` shows an inline Agent Question box with Submit/Skip and Send fallback. | v5 now routes `ask_user` through the combined notebook UI instead of console input: inline prompt, Submit, Skip, Send fallback, Stop unblocks. | `test_ui_ask_user_smoke.py`; `ask_user_ui_reviews/ask_user_prompt_fixture.png`; `ROUND_2_ASK_USER_UI_claude_review.md` -> `APPROVE`. |
| Thinking display/cost | Earlier v5 thinking placement/cost was confusing. | Thinking is collapsed and placed before metrics; simple S3 inventory disables thinking for that turn. | `test_ui_thinking_smoke.py`; `test_s3_cost_controls.py`. |
| S3 real use | User asked for S3 inventory and early v5 drifted to local source inventory. | v5 has `aws_s3_list`, accurate sandbox diagnostics, S3 intent guard, and one-strike blocked retry. | S3 real-use review blocks and tests. |
| Runnable lessons | Runnable patterns matter, but terminal UI does not map directly to SageMaker notebooks. | v5 adapted relevant patterns: progress visibility, review discipline, status tracking, cache/cost awareness, subagent observability. | `V5_DEEP_SCAN_RUNNABLE_COMPARE_20260511.md`; `V5_DESIGN_OVERVIEW.html`. |
| Tests | v4 was stable; v5 is more modular and testable. | Focused suite passes. | `python -m pytest compact_v5/tests -q` -> 36 passed. |
| Independent review | User required Claude CLI review with subscription auth. | Final Claude CLI review loop approved; no HIGH/MEDIUM findings; the v4-dependency alignment and combined config/chat UI patches both received `APPROVE`. | `notebook_widget_regression_reviews/ROUND3_*`; `notebook_widget_regression_reviews/claude/ROUND_1_WIDGET_DEPENDENCY_FIX_claude_review.md`; `notebook_widget_regression_reviews/claude/ROUND_4_COMBINED_CONFIG_CHAT_UI_REREVIEW_claude_review.md`. |
| Package | Source fixes must be in the runtime ship zip. | Minimum ship zip rebuilt and verified. | `compact_v5_ship.zip`; SHA recorded in zip verify doc. |

## Remaining Risk

The current target retest focus is widget rendering:

- v5 previously installed `jupyterlab_widgets` and `widgetsnbextension` in Cell
  1; latest v4 did not. This has been removed.
- SageMaker/Jupyter widget manager behavior can still differ from local
  Jupyter;
- if the target still produces `Error displaying widget: model not found`, run
  a basic `ipywidgets.IntSlider` smoke test in the same target kernel/browser;
- IAM permissions and AWS credentials can differ;
- installed package versions can differ;
- production-like user prompts can still expose P2 polish needs.

The widget-manager item remains the first thing to validate in the user's
target SageMaker runtime after uploading the new ship zip.

## Production-Test Gate

1. Upload/extract latest `compact_v5_ship.zip` in target SageMaker.
2. Restart the kernel.
3. Run Cells 1-2.
4. Confirm:
   - Cell 2 renders the single combined dark v4-style config/chat UI;
   - no `Error displaying widget: model not found`;
   - footer shows ready/status/metrics.
5. If the error remains, run this basic widget smoke in the target kernel:
   `import ipywidgets as widgets; display(widgets.IntSlider(description="Widget test"))`.
6. Run:
   - S3 inventory prompt;
   - notes_cli style build/test/review prompt;
   - an ambiguous prompt that makes the model call `ask_user`, confirming the
     inline Agent Question box displays and resumes after Submit/Skip;
   - one long-running task with subagent/reviewer visibility.

## Lesson

Production confidence should be evidence-labeled, not absolute.

For future software work, use this language:

- **100% ready for target validation** means all known P0/P1 source/package
  blockers are closed and the artifact is rebuilt.
- **98% source/package ready** means source, tests, docs, and ship zip are
  aligned, but target runtime validation can still fail.
- Do not say **production flawless** until target-environment validation passes.
