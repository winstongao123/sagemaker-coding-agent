# V5 Phase 12 Changelog — Parity tests vs v4 (audit gate before Phase 13)

Date: 2026-04-30
Tag (target): v5-phase-12
ADR: ADR-018
PORT_LOG row: #035

## Goal (V5_PLAN.md §Phase 12)

Run fixed scenarios against v4 and v5; assert behavior parity.
Critical scenario suite 100%, non-critical ≥90%, differences logged in
PORT_LOG.

## What landed

### tests/parity/test_parity_critical.py (15 scenarios — must-pass 100%)
01. SecurityManager denies `rm -rf /`
02. SecurityManager denies banned `import socket`
03. plan-mode dispatch blocks `edit_file`
04. plan-mode dispatch blocks `always_load=True` mutating tool (Codex Phase-08 contract)
05. RetryPolicy.MAX_RETRIES=4, BACKOFF_RECOVERY={"backoff"}
06. ErrorClassifier categorizes Bedrock errors (THROTTLE/SERVICE_UNAVAILABLE/CONTEXT_OVERFLOW/ACCESS_DENIED)
07. static prompt ≤2500 + tool_classes at slot 2 (PS Issue #7)
08. cache boundary marker present in assembled prompt
09. Phase 7 deferred-loading round-trip end-to-end
10. Sub-agent shares parent IterationBudget (Phase 9 contract)
11. SkillManager auto-trigger default-OFF (v4.9.6 contract)
12. 10 v4 production skills load (alias-aware)
13. context-overflow exits cleanly with stop_reason="context_overflow"
14. Tool exception trapped → tool_result is_error=True
15. PS Issues #2 + #4 visible via widgets

### tests/parity/test_parity_non_critical.py (10 scenarios — ≥9/10 must pass)
01. tool_result truncation respects per-tool max_result_size_chars
02. registry duplicate-name registration error wording
03. Skill description CSO format DEBUG advisory
04. skill audit log line format on propose_patch
05. budget widget HTML markup contains `<progress>` element
06. depth-exceeded message wording
07. plan-mode error message contains tool name + plan-mode reference
08. tool_search wire format `<functions>...</functions>`
09. frontmatter parser CSV + YAML list both work
10. env-details ≤6 lines (v4 Haiku-budget contract)

## Test results

- **Critical: 15/15 PASS (100%)** — gate met.
- **Non-critical: 10/10 PASS (100%, exceeds 90% gate)**.
- Full suite: **437 passed + 4 skipped** (was 412+4 in Phase 11; +25 Phase 12 tests).
- Aggregate audit: all 7 metrics PASS.

## Documented v4-vs-v5 divergences (per PORT_LOG #035 appendix)

All divergences are INTENTIONAL improvements caught during Codex reviews:
- Per-tool `max_result_size_chars` cap vs v4's single global cap.
- Strict `PLAN_MODE_ALLOWED_TOOLS` allowlist at dispatch (Codex Phase-08).
- UUID-suffixed proposal filenames (Codex Phase-10).
- `discover_relevant(active_tools=...)` Hermes filter (Phase 10 PS Issue #1).
- Visible `IterationBudget` + `thinking_budget` widgets (Phase 11 PS #2 + #4).

## Codex review

Phase 12 ships ZERO new production code (only test fixtures). The
production-code surface this gate validates was already Codex-reviewed in
Phases 1-11. A self-review note is documented at
`_status/codex_reviews/phase-12.md` (mechanical gate result).

## Next phase

Phase 13 — Cutover + ship zip. Tag v5.0.0. Build `compact_v5.zip` with
flat ship surface. Update README + final docs. v5 ships only if Phase 12
gates met (they are: 15/15 + 10/10).
