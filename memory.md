# Project Memory

## 2026-05-12 - compact_v5 production-test readiness lesson

compact_v5 source and `compact_v5_ship.zip` are packaged for target SageMaker
validation, but the user's fresh SageMaker retest still shows
`Error displaying widget: model not found`. Treat target widget rendering as an
active validation blocker until a basic ipywidgets smoke test and v5 Cells 2-3
pass in that exact SageMaker runtime.

The source/package confidence is based on parity checks, 31 passing focused
smoke tests, local Jupyter/Playwright visual evidence, rebuilt zip integrity,
and independent Claude CLI review approvals. The missing proof is target
SageMaker widget-manager compatibility.

Reusable lesson:

- Compare against the latest reference product, not an archive. For v4, the
  reference was `compact_v4/MAIN/agent` at v4.10.10.
- Copy the user contract, not only the implementation ritual. v5 must keep the
  v4-style ipywidgets notebook as the normal path.
- A notebook visual test must run current code. Reused kernels can keep stale
  `entry`/UI modules in `sys.modules`, so the source can look fixed while old
  code still executes.
- Runtime fixes are not shipped until the zip is rebuilt and hash/member parity
  is recorded.
- Runnable lessons should be adapted to SageMaker/Bedrock constraints:
  structured tool/progress visibility, reviewer discipline, status tracking,
  cache/cost awareness, and subagent observability matter; terminal UI and
  unrelated delivery-surface features do not need to be copied.

Production-test gate:

- Open the latest `compact_v5_ship.zip` in the target SageMaker environment.
  `compact_v5/` is the complete source tree; `compact_v5_ship.zip` is the
  minimum runtime artifact to upload/extract.
- Restart the kernel.
- Before v5, run `import ipywidgets as widgets; display(widgets.IntSlider(description="Widget test"))`.
  If this simple widget fails, the target SageMaker widget manager is
  mismatched/broken independent of v5.
- Run Cells 1-3.
- Confirm Cell 2 renders widgets, Cell 3 renders the dark v4-style chat UI,
  and no `Error displaying widget: model not found` appears.
- Then run the S3/read-only and notes_cli style acceptance prompts.
