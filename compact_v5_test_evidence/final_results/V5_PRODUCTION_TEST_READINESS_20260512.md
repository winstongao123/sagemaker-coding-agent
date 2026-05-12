# compact_v5 Production-Test Readiness - 2026-05-12

## Verdict

compact_v5 source and `compact_v5_ship.zip` are ready for target SageMaker
validation. After the user's fresh SageMaker screenshot still showed
`Error displaying widget: model not found`, v5 was aligned more literally with
the stable widget contract the target needs: unlike v4's unpinned Cell 1
`ipywidgets` install, v5 no longer installs or upgrades `ipywidgets`,
`jupyterlab_widgets`, or `widgetsnbextension` from inside the notebook.

Confidence: **100% ready for validation after the refreshed ship zip is used;
98% source/package confidence for production testing; target SageMaker retest
still required after upload/extract**.

This is not a claim of zero production risk. It means the source, package,
S3 real-use blockers, tests, review evidence, and zip verification are strong,
but the target SageMaker widget manager still must pass a real smoke test.

## Evidence Table

| Area | v4 / Runnable reference | v5 current state | Evidence |
|---|---|---|---|
| Latest v4 baseline | Latest tracked v4 is v4.10.10 at `3ba3425`. | Compared against `compact_v4/MAIN/agent`, not an old archive. | `compact_v4/MAIN/agent/chat.ipynb`; `compact_v4/MAIN/agent/sagemaker_agent.py`. |
| Notebook user contract | v4 uses SageMaker/Jupyter ipywidgets as the normal UI. | v5 default is one v4-style combined ipywidgets UI: config controls and chat live in the same displayed widget. Console fallback is explicit only with `use_widgets=False`. | `compact_v5/chat.ipynb`; `compact_v5/entry.py`; `compact_v5/ui/chat_ui.py`. |
| Thin launch cells | v4 was familiar but carried long config/launch cells. | v5 Cell 2 is a thin combined launcher; logic lives in `entry.py` and `ui/chat_ui.py`. | `compact_v5/tests/test_notebook_thin_launcher.py`. |
| Widget regression | v4 rendered widgets; v5 temporarily showed `model not found`, then still had config separated from chat. | v5 refreshes launcher/UI modules in Cell 2, goes beyond v4's unpinned widget install by not installing/upgrading `ipywidgets` or frontend widget extension packages, and launches one combined config/chat UI. | Local Jupyter/Playwright from rebuilt ship zip: `20260512_widget_contract_chat_live_final.png` with `CHAT_HAS_MODEL_NOT_FOUND False`, `CHAT_HAS_SEND True`, `CHAT_HAS_STOP True`, `CHAT_HAS_READY True`, `CHAT_HAS_IPYWIDGETS_VERSION_PRINT True`, `CHAT_HAS_OLD_WIDGET_INSTALL False`; simple `IntSlider` smoke: `SIMPLE_HAS_MODEL_NOT_FOUND False`. |
| Tool visibility | Runnable has strong tool/progress affordances; v4 had better visible flow than early v5. | v5 has live output routing and collapsed/grouped tool cards. | UI smoke tests and Claude UI reviews. |
| Model asks user for input | v4 `ask_user` shows an inline Agent Question box with Submit/Skip and Send fallback. | v5 now routes `ask_user` through the combined notebook UI instead of console input: inline prompt, Submit, Skip, Send fallback, Stop unblocks. | `test_ui_ask_user_smoke.py`; `ask_user_ui_reviews/ask_user_prompt_fixture.png`; `ROUND_2_ASK_USER_UI_claude_review.md` -> `APPROVE`. |
| Session resume display | v4 reloads the visible chat after loading a saved session. | v5 now rehydrates visible chat rows from restored saved messages after `/resume`, including collapsed tool cards grouped by `tool_use_id`. | `test_ui_session_resume_smoke.py`. |
| Thinking display/cost | Earlier v5 thinking placement/cost was confusing. | Thinking is collapsed and placed before metrics; simple S3 inventory disables thinking for that turn. | `test_ui_thinking_smoke.py`; `test_s3_cost_controls.py`. |
| S3 real use | User asked for S3 inventory and early v5 drifted to local source inventory. | v5 has `aws_s3_list`, accurate sandbox diagnostics, S3 intent guard, and one-strike blocked retry. | S3 real-use review blocks and tests. |
| S3 follow-up discipline | User asked "pick two files to investigate" after S3 inventory. | Fixed. v5 reuses recent S3 object paths, caps follow-up `aws_s3_list` calls, adds `aws_s3_preview`, guards truncated "complete" claims, records artifact paths, rebases user deliverables outside runtime package folders, enforces ASCII writes when requested, blocks status-doc spam for small S3 tasks, hides raw tool ids in summaries, and disables thinking for simple S3 follow-ups. | `S3_FOLLOWUP_TOOL_DISCIPLINE_ISSUES_20260512.md`; `S3_FOLLOWUP_TOOL_DISCIPLINE_CLAUDE_REVIEW.md` -> `APPROVE`; `S3_FOLLOWUP_TOOL_DISCIPLINE_CLAUDE_REREVIEW.md` -> `APPROVE`; `py -3.10 -m pytest compact_v5/tests -q` -> 48 passed. |
| Runnable lessons | Runnable patterns matter, but terminal UI does not map directly to SageMaker notebooks. | v5 adapted relevant patterns: progress visibility, review discipline, status tracking, cache/cost awareness, subagent observability. | `V5_DEEP_SCAN_RUNNABLE_COMPARE_20260511.md`; `V5_DESIGN_OVERVIEW.html`. |
| Tests | v4 was stable; v5 is more modular and testable. | Focused suite passes. | `py -3.10 -m pytest compact_v5/tests -q` -> 48 passed. |
| Independent review | User required Claude CLI review with subscription auth. | Final Claude CLI review loop approved; no HIGH/MEDIUM findings; the combined config/chat UI and final widget-stack no-mutation patches received `APPROVE`. | `notebook_widget_regression_reviews/ROUND3_*`; `notebook_widget_regression_reviews/claude/ROUND_4_COMBINED_CONFIG_CHAT_UI_REREVIEW_claude_review.md`; `notebook_widget_regression_reviews/claude/ROUND_5_WIDGET_STACK_NO_MUTATION_REREVIEW_claude_review.md`. |
| Package | Source fixes must be in the runtime ship zip. | Minimum ship zip rebuilt and verified: 154 members, `testzip() None`, required hash parity true. | `compact_v5_ship.zip`; current SHA is recorded in `UI_LIVE_SUPERVISOR_ZIP_VERIFY_20260510.md`. |

## Remaining Risk

The current target retest focus is widget rendering:

- v5 previously installed/upgraded the widget stack in Cell 1. v4 also
  installed `ipywidgets`, but that unpinned install is a latent mismatch risk;
  v5 now avoids that risk by not installing or upgrading `ipywidgets`,
  `jupyterlab_widgets`, or `widgetsnbextension` from the notebook.
- SageMaker/Jupyter widget manager behavior can still differ from local
  Jupyter;
- if the target still produces `Error displaying widget: model not found`, run
  a basic `ipywidgets.IntSlider` smoke test in the same target kernel/browser;
- IAM permissions and AWS credentials can differ;
- installed package versions can differ;
- production-like user prompts can still expose P2 polish needs.
- S3 follow-up tool discipline is fixed in source and independently approved;
  production validation should still include the exact transcript that exposed
  the issue.

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
  - the S3 follow-up prompt `pick two files to investigate and tell me what
    you found`, confirming v5 does not rescan every bucket;
  - one long-running task with subagent/reviewer visibility.

## Lesson

Production confidence should be evidence-labeled, not absolute.

For future software work, use this language:

- **100% ready for target validation** means all known P0/P1 source/package
  blockers are closed and the artifact is rebuilt.
- **98% source/package ready** means source, tests, docs, and ship zip are
  aligned, but target runtime validation can still fail.
- Do not say **production flawless** until target-environment validation passes.
