# compact_v5 Production-Test Readiness - 2026-05-12

## Verdict

compact_v5 source and `compact_v5_ship.zip` are ready for target SageMaker
validation, but the user's fresh SageMaker screenshot still shows
`Error displaying widget: model not found`.

Confidence: **98% for source/package readiness; target widget validation is
currently blocked**.

This is not a claim of zero production risk. It means the source, package,
S3 real-use blockers, tests, review evidence, and zip verification are strong,
but the target SageMaker widget manager still must pass a real smoke test.

## Evidence Table

| Area | v4 / Runnable reference | v5 current state | Evidence |
|---|---|---|---|
| Latest v4 baseline | Latest tracked v4 is v4.10.10 at `3ba3425`. | Compared against `compact_v4/MAIN/agent`, not an old archive. | `compact_v4/MAIN/agent/chat.ipynb`; `compact_v4/MAIN/agent/sagemaker_agent.py`. |
| Notebook user contract | v4 uses SageMaker/Jupyter ipywidgets as the normal UI. | v5 default is v4-style ipywidgets. Console fallback is explicit only with `use_widgets=False`. | `compact_v5/chat.ipynb`; `compact_v5/entry.py`. |
| Thin launch cells | v4 was familiar but carried long config/launch cells. | v5 Cell 2 is 16 lines; Cell 3 is 4 lines; logic lives in `entry.py`. | `compact_v5/tests/test_notebook_thin_launcher.py`. |
| Widget regression | v4 rendered widgets; v5 temporarily showed `model not found`. | v5 refreshes launcher/UI modules in Cell 2 so reused kernels run current files, but target SageMaker still fails in the user's retest. | Local Jupyter/Playwright: `HAS_WIDGET_ERROR False`; user SageMaker screenshot: still failing. |
| Tool visibility | Runnable has strong tool/progress affordances; v4 had better visible flow than early v5. | v5 has live output routing and collapsed/grouped tool cards. | UI smoke tests and Claude UI reviews. |
| Thinking display/cost | Earlier v5 thinking placement/cost was confusing. | Thinking is collapsed and placed before metrics; simple S3 inventory disables thinking for that turn. | `test_ui_thinking_smoke.py`; `test_s3_cost_controls.py`. |
| S3 real use | User asked for S3 inventory and early v5 drifted to local source inventory. | v5 has `aws_s3_list`, accurate sandbox diagnostics, S3 intent guard, and one-strike blocked retry. | S3 real-use review blocks and tests. |
| Runnable lessons | Runnable patterns matter, but terminal UI does not map directly to SageMaker notebooks. | v5 adapted relevant patterns: progress visibility, review discipline, status tracking, cache/cost awareness, subagent observability. | `V5_DEEP_SCAN_RUNNABLE_COMPARE_20260511.md`; `V5_DESIGN_OVERVIEW.html`. |
| Tests | v4 was stable; v5 is more modular and testable. | Focused suite passes. | `python -m pytest compact_v5/tests -q` -> 31 passed. |
| Independent review | User required Claude CLI review with subscription auth. | Final Claude CLI review loop approved; no HIGH/MEDIUM findings. | `notebook_widget_regression_reviews/ROUND3_*`. |
| Package | Source fixes must be in the runtime ship zip. | Minimum ship zip rebuilt and verified. | `compact_v5_ship.zip`; SHA recorded in zip verify doc. |

## Remaining Risk

The current blocker is target-environment widget rendering:

- SageMaker/Jupyter widget manager behavior differs from local Jupyter and is
  currently producing `Error displaying widget: model not found`;
- Cell 1 may install/upgrade Python widget packages without updating the
  browser-side SageMaker widget manager;
- a basic `ipywidgets.IntSlider` smoke test must be run in the same target
  kernel/browser before blaming v5's widget tree;
- IAM permissions and AWS credentials can differ;
- installed package versions can differ;
- production-like user prompts can still expose P2 polish needs.

The widget-manager item is now an active validation blocker in the user's
target SageMaker runtime.

## Production-Test Gate

1. Upload/extract latest `compact_v5_ship.zip` in target SageMaker.
2. Restart the kernel.
3. Run Cells 1-3.
4. Before v5, run this basic widget smoke in the target kernel:
   `import ipywidgets as widgets; display(widgets.IntSlider(description="Widget test"))`.
5. Confirm:
   - Cell 2 renders ipywidgets controls;
   - Cell 3 renders the dark v4-style chat UI;
   - no `Error displaying widget: model not found`;
   - footer shows ready/status/metrics.
6. Run:
   - S3 inventory prompt;
   - notes_cli style build/test/review prompt;
   - one long-running task with subagent/reviewer visibility.

## Lesson

Production confidence should be evidence-labeled, not absolute.

For future software work, use this language:

- **100% ready for target validation** means all known P0/P1 source/package
  blockers are closed and the artifact is rebuilt.
- **98% source/package ready** means source, tests, docs, and ship zip are
  aligned, but target runtime validation can still fail.
- Do not say **production flawless** until target-environment validation passes.
