# Project Memory

## 2026-05-12 - compact_v5 production-test readiness lesson

compact_v5 source and `compact_v5_ship.zip` are packaged for target SageMaker
validation. The user's fresh SageMaker retest still showed
`Error displaying widget: model not found`; the concrete v5-side difference
from latest v4.10.10 was Cell 1 mutating the widget stack from inside the
notebook. v4 also installed `ipywidgets`, but that unpinned install was a
latent browser/kernel mismatch risk. The first v5 repair removed
`jupyterlab_widgets` and `widgetsnbextension` but still installed/upgraded
`ipywidgets`, which can also mismatch SageMaker's browser widget manager. v5 is
now deliberately more conservative than v4: Cell 1 does not install or upgrade
`ipywidgets`, `jupyterlab_widgets`, or `widgetsnbextension`.

The source/package confidence is based on parity checks, 48 passing focused
smoke tests, local Jupyter/Playwright visual evidence from the rebuilt ship
zip, rebuilt zip integrity, and independent Claude CLI review approvals. The
remaining proof is target SageMaker retest with the new ship zip.

2026-05-12 follow-up: the accepted notebook workflow is one combined UI, not a
separate Agent Configuration panel plus a chat panel. Cell 2 now launches the
single v4-style config/chat surface.

2026-05-12 follow-up: model-initiated `ask_user` prompts now match the v4
notebook contract. v5 displays an inline `Agent Question` card inside the
combined UI, supports Submit/Skip, accepts the main Send button as fallback,
and Stop unblocks the wait. Claude CLI Round 1 caught a provider propagation
bug in the engine dispatch path; Round 2 approved after the end-to-end test
was added.

2026-05-12 follow-up: `/resume` previously restored engine messages but not
the visible notebook transcript. v5 now rehydrates the visible chat after
session load, including user/assistant turns and collapsed tool cards grouped
by tool id.

2026-05-12 follow-up: S3 access is not the same as S3 workflow discipline.
After a successful S3 inventory, the prompt "pick two files to investigate"
caused v5 to run multiple new `aws_s3_list` calls instead of reusing the
previously listed objects. Treat this as an open follow-up tool-discipline
block: add reuse-first behavior, S3 fanout limits, a safe S3 preview tool,
truncation truth checks, ASCII-contract tests, artifact tracking, workspace
defaults outside the v5 runtime folder, and a guard against editing
`AGENT_STATUS.md` for simple non-project tasks. Claude CLI subscription review
approved the worker plan after tightening three specifics: cap
`aws_s3_list` at 2 calls per user turn, use a separate allowed
`user_artifacts_root` for generated deliverables, and apply concrete
status-update thresholds.

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
- UI callbacks need two tests: one proving the visible widget/card renders, and
  one proving the engine/tool dispatch path can actually reach that callback.
- Session persistence has two truths: model-visible context and user-visible
  transcript. Test both when claiming v4 session parity.
- Follow-up prompts have a continuity contract. When the user says "pick two"
  after a list, the agent should choose from the known list first, not re-run a
  broad discovery scan.
- Runnable lessons should be adapted to SageMaker/Bedrock constraints:
  structured tool/progress visibility, reviewer discipline, status tracking,
  cache/cost awareness, and subagent observability matter; terminal UI and
  unrelated delivery-surface features do not need to be copied.

Production-test gate:

- Open the latest `compact_v5_ship.zip` in the target SageMaker environment.
  `compact_v5/` is the complete source tree; `compact_v5_ship.zip` is the
  minimum runtime artifact to upload/extract.
- Restart the kernel.
- Run Cells 1-2.
- Confirm Cell 2 renders the single combined dark v4-style config/chat UI,
  and no `Error displaying widget: model not found` appears.
- If the error remains, run `import ipywidgets as widgets; display(widgets.IntSlider(description="Widget test"))`.
  If this simple widget fails, the target SageMaker widget manager is
  mismatched/broken independent of v5.
- Then run the S3/read-only and notes_cli style acceptance prompts.
- Also run one ambiguous prompt that triggers `ask_user` and verify the inline
  `Agent Question` prompt resumes the agent after Submit/Skip.
