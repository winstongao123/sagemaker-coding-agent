# PS_PS_FINAL_TEST_v2 Result Summary

Date: 2026-05-07

Purpose: explain what v2 tested, what evidence exists, and why v3 was created.

## Plain Result

`PS_PS_FINAL_TEST_v2.md` is the corrected human acceptance-test protocol that
replaced the weaker v1 instructions. It was not recorded as one single clean
unattended Bedrock run. Instead, the evidence chain is:

1. v1 real AWS/Sonnet run proved v5 could build, test, review, and fix a real
   package, but exposed packaging/status gaps.
2. v2 updated the acceptance instructions to close those gaps.
3. local final acceptance verified the UI/status/subagent/verify/done surfaces.
4. v3 added a stricter Haiku comparison against v4 and made saved subagent review
   artifacts a hard gate.

Explain it like you are 9:

v1 showed the robot can build the toy but put it in a bad box. v2 says exactly
how the robot must use a real box and write the checklist. v3 then made v5 and
v4 do the same homework side by side.

## Side-By-Side Evidence

| Check | v1 AWS evidence | v2 protocol change | Local/UI evidence | v3 Haiku comparison evidence | Conclusion |
|---|---|---|---|---|---|
| Real long coding | Built `mini_issue_tracker`; final operator rerun had `80 passed`. | Keeps same long software-building goal. | Not a full software build; local gate smoke only. | v5 built `mini_release_auditor`; `62 passed`. | v5 can do real package work, not just snippets. |
| Cost cap | v1 spent about `$3.2689`; `$2` was too tight. | Raises recommended cap to `$5`; explains turn-boundary overshoot. | `/cost` output visible in local gate. | v5 Haiku spent `$0.9378 / $5`; v4 spent `$0.3934 / $5`. | Budget behavior is visible and bounded. |
| Subagent/reviewer | Planning/review subagents used and costed. | Requires worker/reviewer notes under `docs/reviews/`. | Subagent lifecycle, envelope, `/verify`, `/done` passed. | v5 verify subagent cost/cache recorded; `docs/reviews/` missing. | v3 makes saved review artifacts a hard not-done condition. |
| Zip packaging | v1 generated an invalid zip; operator rebuilt it. | Requires Python `zipfile` and `testzip()` before done. | Ship zip verifier passes for v5 package. | v5 made a valid zip with 27 members; v4 made no zip in intended workspace. | Packaging gap is now explicitly tested. |
| Final status | v1 `AGENT_STATUS.md` became stale near the end. | Requires final status to have no pending packaging/review/cost/context/verify/done. | `/done full` gate passed locally. | v5 had status; v4 had no required files in intended workspace. | v2/v3 focus on no stale final claim. |
| Workspace discipline | v1 used the requested workspace. | Keeps explicit workspace requirement. | Local smoke does not prove workspace drift. | v5 wrote in intended workspace; v4 polluted repo root. | v5 is much safer than v4 for supervisor-style work. |
| UI observability | v1 surfaced cost/subagent logs during run. | Tells user what UI metrics to watch. | Cache line, cache savings, parent/subagent attribution, todos visible. | v3 asks user to visually confirm cache/reasoning/subagent status before running. | v5 UI is usable, but v3 keeps a human visual check. |

## Files

| Evidence | Path |
|---|---|
| v1 AWS review | `compact_v5/_status/aws_acceptance_v1/PS_PS_FINAL_TEST_V1_AWS_REVIEW.md` |
| v2 test protocol | `compact_v5/docs/PS_PS_FINAL_TEST_v2.md` |
| local final acceptance summary | `compact_v5/_status/final_local_acceptance/local-final-acceptance-summary.md` |
| v3 comparison report | `compact_v5/_status/ps_ps_v3_compare/PS_PS_V3_COMPARE_REPORT.md` |
| v3 human test | `compact_v5/docs/PS_PS_FINAL_TEST_v3.md` |

## Final Interpretation

v2 is valid as the corrected acceptance protocol, but it should not be described
as a standalone clean pass. The cleanest current human test is v3 because it
adds the stricter checks learned from v1/v2 and the direct v4-vs-v5 comparison.

