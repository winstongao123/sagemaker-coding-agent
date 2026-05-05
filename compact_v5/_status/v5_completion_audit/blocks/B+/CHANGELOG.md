# Block B+ Changelog

Date: 2026-05-05

- Initialized Block B+ completion-audit artifacts from
  `SYNTHESIS_MASTER.md`.
- Added row-level evidence for all 8 canonical B+ rows.
- Added `TokenTracker` per-model usage collapse, four-line cost block,
  local-only OTel-style counters, context-window refresh state, and persisted
  model/context stats.
- Wired `/cost` through the four-line cost summary.
- Added B+ lock tests for canonical per-model collapse, four-line `/cost`,
  local counters, context-window refresh, exit cost flush, and Config row
  coverage.
- Reused the existing Block A advisor-compactor path as the B+5 runtime site
  and reran its targeted tests.
- Closed the Claude iter6 HIGH B+1 finding by adding production `/save` and
  `/resume` command paths. `/save` persists current messages plus
  `TOKENS.get_stats()` metadata; `/resume <id>` restores messages and calls
  `TOKENS.restore()`. Chat UI command dispatch now passes the Agent context so
  console/widget resume paths can restore the live message buffer.

No AWS/R-tier command, tag, nested `codex exec`, or Codex reviewer was run.
