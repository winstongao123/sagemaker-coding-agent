# Full v5 Development History Archive

This index records the mechanical archive of v5 development-history files.

The production runtime is `compact_v5/` and the ship artifact is `compact_v5.zip`.
The development history lives here, outside the production zip:

`compact_v5_test_evidence/full_v5_development_history/`

## Archived Groups

| Group | Files | Why kept |
|---|---:|---|
| MAIN/agent/tests | 89 | v5 design/test/review history and reproducibility evidence. |
| MAIN/changelogs | 15 | v5 design/test/review history and reproducibility evidence. |
| _phase_2 deep scans/plans | 80 | v5 design/test/review history and reproducibility evidence. |
| _status audit/review/log evidence | 1659 | v5 design/test/review history and reproducibility evidence. |
| docs human-facing docs/html | 29 | v5 design/test/review history and reproducibility evidence. |
| root/reference files | 6 | v5 design/test/review history and reproducibility evidence. |

Total archived files: `1878`.

Additional all-history check:

- `DELETED_V5_HISTORY_MANIFEST.txt` lists v5 paths that appeared in earlier
  commits and were later deleted.
- `full_v5_development_history/deleted_history/` restores the deleted-history
  files that were no longer present at `HEAD`.
- The all-history delete scan found only 2 relevant deleted paths:
  `compact_v5/MAIN/agent/mcp/__init__.py` and
  `compact_v5/_status/codex_reviews/block-b-iter2-skipped.md`.

## Important Subfolders

| Path | Meaning |
|---|---|
| `full_v5_development_history/compact_v5/_phase_2/` | Deep scans of v4, Runnable, Hermes, Learning Factory, synthesis maps, and test design. |
| `full_v5_development_history/compact_v5/_status/` | Audit ledgers, Claude reviews, R-tier evidence, PS/PS tests, AWS logs, final readiness docs. |
| `full_v5_development_history/compact_v5/docs/` | Human-readable docs, final test docs, HTML docs, v4-vs-v5 reports. |
| `full_v5_development_history/compact_v5/MAIN/changelogs/` | Phase-by-phase v5 build changelogs. |
| `full_v5_development_history/compact_v5/MAIN/agent/tests/` | Local/unit/integration/R-tier test files used during development. |

## Explain Like Age 9

`compact_v5.zip` is the robot you ship.

`full_v5_development_history/` is the robot factory notebook: plans, tests, reviews, logs, and build history.

They must both be kept, but only the robot goes into the company zip.
