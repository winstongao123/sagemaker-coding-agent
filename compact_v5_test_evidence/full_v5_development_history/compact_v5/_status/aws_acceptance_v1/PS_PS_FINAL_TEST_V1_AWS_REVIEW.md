# PS_PS_FINAL_TEST_v1 AWS Review

Date: 2026-05-07

## Result

`PS_PS_FINAL_TEST_v1` was run against real Bedrock Claude 4.5 Sonnet in
`ap-southeast-2`.

Final verdict: **PARTIAL PASS, NOT A CLEAN UNATTENDED PASS**.

Explain it like you are 9:

v5 built the little software project, asked helper/reviewer agents, fixed review
problems, and passed the tests. But at the very end it put the project into a
box labeled `.zip` that was not really a zip box. Codex/operator rebuilt that
box correctly so the evidence can be inspected, but that means v1 did not finish
perfectly by itself.

## What Passed

| Check | Result | Evidence |
|---|---|---|
| Real Bedrock run | Used `au.anthropic.claude-sonnet-4-5-20250929-v1:0` in `ap-southeast-2` | `v1-aws-run-20260507-131838.summary.json` |
| Project creation | `mini_issue_tracker` package, docs, tests, reviews, logs, and status were created | `workspace/` |
| Subagents | Planning and review subagents were used and costs were attributed | `v1-aws-run-20260507-131838.summary.json` |
| Review/fix loop | Reviewer found security/quality issues; continuation fixed the important ones | `workspace/docs/REVIEW.md`, `workspace/FINAL_METRICS.md` |
| Tests | Final local rerun: `80 passed` | `v1-operator-final-pytest.log` |
| Evidence zip after operator salvage | Valid zip with all required entries | `v5_final_acceptance_results.zip`, `v1-operator-zip-validation.log` |
| Visual/log summary | Human-readable evidence snapshot created | `v1-aws-visual-summary.png` |

## What Failed

| Finding | Why It Matters | Disposition |
|---|---|---|
| `$2.00` v1 cap was too low | The first run stopped at `$2.0575` before final packaging. A single model turn can overshoot slightly because the cap is checked between calls. | v2 raises the recommended Sonnet cap and documents the overshoot behavior. |
| Packaging failed repeatedly | v5 created a file at the zip path, but Python reported `BadZipFile: File is not a zip file`. | Operator rebuilt the zip for evidence, and v2 now requires `zipfile.ZipFile(...).testzip()` validation before done. |
| Continuation max-turns too small for cleanup | Short packaging continuations stopped while still trying to recover from the zip issue. | v2 tells v5 to package with one simple Python `zipfile` script and validate immediately. |
| `AGENT_STATUS.md` was stale near the end | The generated status still said final packaging/review fields were pending, while later files contained final metrics. | Treat as a process-quality finding for v2: final status must be updated after zip validation. |

## Cost

Observed v1 real Bedrock spend:

| Phase | Cost |
|---|---:|
| Main run | `$2.0575` |
| Continuation | `$1.0163` |
| Zip final attempt | `$0.0837` |
| Zip fix attempt | `$0.1114` |
| **Total observed** | **about `$3.2689`** |

The total is higher than the original `$2.00` v1 target because v1 exposed real
cleanup and packaging gaps. No further Bedrock retry is recommended for v1; v2
should be used for the human final test.

## Operator Salvage

Codex/operator rebuilt the evidence zip with Python `zipfile` after v5 failed to
produce a valid zip. This makes the evidence inspectable, but it is not counted
as a clean unattended v5 pass.

Validation:

```text
bad_member: None
missing_required: []
```

Evidence:

- `v5_final_acceptance_results.zip`
- `v1-operator-zip-validation.log`

## Recommendation For v2

Use `PS_PS_FINAL_TEST_v2.md`, not v1.

v2 has been updated to:

- recommend a `$5.00` Sonnet budget cap for the full supervisor/reviewer/software
  build test;
- explain that the cap can overshoot slightly on the final turn;
- require a real zip created with Python standard-library `zipfile`;
- require `zipfile.ZipFile(...).testzip()` before claiming done;
- require final `AGENT_STATUS.md` to match the true final state.

## Confidence Impact

This v1 run increases confidence in v5's coding/review/test ability, because the
generated package is working and review fixes landed. It reduces confidence in
the final packaging/done discipline until v2 passes cleanly.

Production-readiness statement after v1:

v5 remains strong, but the human final v2 test is still required before saying
the user-facing long-running workflow is fully validated end to end.
