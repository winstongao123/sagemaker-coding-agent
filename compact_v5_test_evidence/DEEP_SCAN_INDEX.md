# Deep Scan And Architecture Evidence Index

This folder preserves the v5 architecture scans and reference comparisons outside
the minimum production zip.

The production zip contains only the runtime. This archive contains the research
that explains why the runtime looks the way it does.

## Easy Location

All restored scan/reference files live under:

```text
compact_v5_test_evidence/deep_scans/
```

## Main Groups

| Group | Path | What it contains |
|---|---|---|
| Phase 2 scan archive | `deep_scans/compact_v5/_phase_2/` | Multi-wave scans of v4, Runnable Claude Code, Hermes, Learning Factory, synthesis plans, risk/completeness matrices, and test design. |
| Wave 5 deep scan | `deep_scans/compact_v5/_phase_2/wave_5_deep/` | The detailed source-backed scan that produced `SYNTHESIS_MASTER.md`, the canonical block/item map. |
| Wave 6 test design | `deep_scans/compact_v5/_phase_2/wave_6/` | Long-session, multi-file, notebook UX, subagent, and tool-failure test design. |
| Third deep scan | `deep_scans/compact_v5/_status/v5_completion_audit/THIRD_DEEP_SCAN_SOFTWARE_BUILDER_GAPS.md` | Later scan focused on making v5 a long-running software engineering agent. |
| Third-scan Claude reviews | `deep_scans/compact_v5/_status/v5_completion_audit/reviews/third-deep-scan-*.md` | Claude review of the third scan and worker-readiness plan. |
| Runnable port log | `deep_scans/compact_v5/_status/V5_RUNNABLE_PORT_LOG.md` | Item-level record of Runnable-derived functionality and v5 dispositions. |
| v5 design decisions | `deep_scans/compact_v5/_status/V5_DESIGN_DECISIONS.md` | Key architecture choices and constraints. |
| v4 UI parity | `deep_scans/compact_v5/_status/PS_UI_V4.md` | Notes from v4 UI inspection used to restore notebook UI parity. |
| Repo learnings docs | `deep_scans/compact_v5/docs/PS_V5_LEARNINGS_FROM_REPOS.md` and `PS_V5_FUNCTIONAL_CHANGES_FROM_V4.md` | Human-readable summary of what v5 learned from v4/Runnable/Hermes/Learning Factory. |
| Runnable HTML references | `deep_scans/compact_v5/docs/htmls/PS_*RUNNABLE*.html` | Visual/reference docs for Runnable comparison. |

## Explain Like Age 9

`compact_v5.zip` is the robot.

`compact_v5_test_evidence/final_test_suites/` is the robot's final exam.

`compact_v5_test_evidence/deep_scans/` is the notebook showing how we studied
older robots before building this one.

Keep this folder in GitHub. Do not put it in the company runtime zip.
