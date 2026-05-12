# Software Engineering Learnings

This folder is the curated pickup point for broader software-engineering lessons
learned while building v5.

Key themes:
- Verify behavior, not just file existence.
- Use dedicated structured tools when available.
- Avoid speculative abstractions and broad rewrites.
- Keep reviewer prompts concrete and self-contained.
- Diagnose failed checks before switching tactics.
- Report outcomes faithfully, including skipped or failed verification.
- **The fix that sticks is often deletion, not addition** (see 2026-05-13
  widget regression: removing four hidden `clear_output(wait=True)` calls
  across the launch stack — the leaky-abstraction trap).
- **Same anti-pattern at multiple layers compounds** — fix only the visible
  layer and the bug reappears.
- **Cross-codebase comparison is high-ROI** — the 9 deep-scan rounds against
  Runnable produced 14 confirmed v5 wins and 7 actionable backlog items in
  ~6 hours of agent time.

Recommended read order:
1. `FUTURE_SOFTWARE_DEVELOPMENT_LESSONS_20260511.md`
2. `20260513_runnable_additional_deep_scan.md` (now Rounds 4-9; rounds 7-9
   added 2026-05-13 — covers retry/telemetry/cache-observability/permissions/
   sandbox/hooks/file-edit/skills/output-styles axes)
3. `V5_MISSED_ISSUES_ROOT_CAUSE_20260511.md`
4. `final_test_v5_responds_investigation.md`

## Generalisable lessons from rounds 7-9

- **Heartbeats during long waits** — emit periodic status from any retry
  layer that may exceed perceived timeout, not just sit silent. Runnable
  yields every 30s; v5 currently doesn't.
- **Per-source budgets** — distinguish foreground (user-blocking) from
  background (subagent) requests so retry budgets don't compete.
- **Structured per-turn event emission** beats reading log files later — a
  single `summary_event` per assistant turn makes cost/cache regressions
  diagnosable without re-reading transcripts.
- **Document where the fix already lives, not just where the gap is** —
  every backlog row in the scan cites both the Runnable reference and the
  v5 location where the primitive already exists. Backlog work is then
  "add diff generation on top of these hashes" rather than "build cache-break
  detection from scratch."
- **Intentional gaps need to be marked as such** — chat-UI paradigm and
  plugin system are not "v5 lags" but "v5 different by design." Without
  the label, future workers will try to close them and regress v5.

