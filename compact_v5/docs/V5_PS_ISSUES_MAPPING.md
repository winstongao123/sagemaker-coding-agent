# V5 — Mapping `PS_actual_use_problems.md` Issues to v5 Phases

This file enforces the user's 2026-04-30 requirement: **v5 must address all 7 issues identified in `PS_actual_use_problems.md`**, not just the 2-3 that v4.10.10 fixed in-place. Each issue is mapped to the v5 phase that delivers the structural fix, with acceptance criteria.

If a phase ships without addressing the mapped issue, it FAILS the aggregate audit and blocks progress.

---

## [Actual Use Issue 1] — Noisy `[CSO-CHECK]` warnings on every notebook startup
- **Root cause**: `logging.warning` for advisory-only check (compact_v4 `sagemaker_agent.py:2740`).
- **v4.10.10 in-place fix**: lowered to `logging.debug`. Works.
- **v5 phase**: Phase 10 (skills + auto-trigger porting).
- **v5 acceptance**: every advisory-only audit logs at DEBUG level by default; only true errors at WARNING/ERROR. Unit test: import skill module with `logging.basicConfig(level=logging.WARNING)` produces zero output for skills with non-CSO descriptions.
- **Better than v4**: tests/lint_phase_id.py-style mechanical audit catches accidental WARNING regressions.

---

## [Actual Use Issue 2] — Iteration budget too tight (`max_iteration_budget = 90`)
- **Root cause**: hermes default 90 too conservative for SageMaker dev workloads.
- **v4.10.10 in-place fix**: bumped to 600 + UI slider 90-2000.
- **v5 phase**: Phase 1 (Config) + Phase 8 (QueryEngine wires `IterationBudget`).
- **v5 acceptance**: `runtime/config.py` ships default 600; UI slider in chat.ipynb cell 2; banner displays current value. Status doc mentions remaining iteration budget mid-session.
- **Better than v4**: budget shown live in chat status row (not just at launch banner). Tap user notification when budget < 25% remaining (Hermes-grace pattern, Phase 8).

---

## [Actual Use Issue 3] — Cold cache detected (61min gap) — proactive microcompact
- **Root cause**: Bedrock prompt cache 5-min TTL → cold-cache after long idle. v4 has `microcompact()` triggered after 30-min gap.
- **v4 status**: feature, not bug. Already optimal.
- **v5 phase**: Phase 8 (QueryEngine + context_window) — REUSE v4 microcompact verbatim.
- **v5 acceptance**: behavior identical to v4 (test_v410_cache_boundary.py reused).
- **Better than v4**: in chat status row, show `Cache age: 4m 12s` so user sees they're approaching cold-cache window.

---

## [Actual Use Issue 4] — Thinking mode appears only for the first message
- **Root cause**: model-controlled (Sonnet decides when to engage thinking budget). Not a v4 bug.
- **v4 status**: by design. User saw 💭 emoji only when model returned non-empty `reasoning_content`.
- **v5 phase**: Phase 1 (Bedrock client) + Phase 6 (prompt assembly).
- **v5 acceptance**: thinking config (`thinking: { type: "enabled", budget_tokens: N }`) sent on EVERY Bedrock call when CONFIG.thinking_enabled=True (verified by Phase 1 unit test). UI displays thinking block when present, suppresses gracefully when absent.
- **Better than v4**: chat status indicator (`Thinking budget: 8K, used 2.4K avg`). Per-turn thinking-token chart in `/cost`.
- **Documentation**: explicit note in `prompt/identity.md` and USER_GUIDE: "Thinking is model-controlled — you'll see 💭 on complex turns, not on simple confirmations. This is normal and cost-efficient."

---

## [Actual Use Issue 5] — Session totals not persisted across save/load
- **Root cause**: v4's Agent class didn't persist `session_cost`. v4.10.10 fix wired to TOKENS singleton.
- **v4.10.10 in-place fix**: `metadata["session_cost"] = float(getattr(TOKENS, "session_cost", 0.0))`; restored in on_load.
- **v5 phase**: Phase 1 (`runtime/session.py`).
- **v5 acceptance**: SessionManager.save() persists token_stats + session_cost; SessionManager.load() restores both. Round-trip test: save mid-session at $2.09, load → cost=$2.09.
- **Better than v4**: per-session token-by-tool breakdown saved (not just total cost). Lets user see "this session spent 80% on read_file, 15% on bash, 5% on Bedrock invoke" — useful for cost optimization.

---

## [Actual Use Issue 6] — Codex caught session_cost wiring bug (HIGH severity)
- **Root cause**: my own v4.10.10 round-2 mistake — wrote to non-existent `Agent.session_cost`.
- **v4.10.10 in-place fix**: re-wired to TOKENS singleton.
- **v5 phase**: Phase 0 (this lesson is the foundation of the whole tracking infrastructure).
- **v5 acceptance**: every persistence path has a Codex AXIS-A pass before committing (per V5_BUILD_STATUS.md tag rule: "Tag is FORBIDDEN if any open Codex finding ≥ CHANGES_REQUESTED").
- **Better than v4**: ADR template question 1 explicitly forces "what does this REPLACE? cite v4 file:line" — would have caught the Agent-vs-TOKENS confusion before code landed.

---

## [Actual Use Issue 7] — Real log: agent confused after hitting 40-call exec limit
- **Root cause**: v4's monolithic system prompt buried the tool-availability matrix mid-list. Under cognitive load (40-call limit hit), LLM under-attended to mid-list bullets and concluded "all tools blocked".
- **v4.10.10 in-place fixes**: max_exec_calls 40→200, error message rewritten ("STILL AVAILABLE: read_file, grep, ..."), SYSTEM_PROMPT tool-availability matrix block, read_file repetition tightened.
- **v5 phase**: Phase 6 (sectioned prompt) is the **structural fix**. Phase 4 (diff preview) + Phase 7 (deferred loading) reduce overall cognitive load.
- **v5 acceptance**:
  - `prompt/tool_classes.md` is its own top-level file (not buried).
  - `prompt/sections.py::estimate_tokens(static_prompt) ≤ 2500` (vs v4's 5000).
  - Aggregate audit cognitive-load test simulates blocked-tool recovery: Codex-evaluated PASS required.
  - Phase 8.5 thin-slice parity test specifically includes the "40-call limit hit → continue with read_file" scenario.
- **Better than v4**: structural impossibility of burying the matrix. Each prompt section is a separately-budgeted file with a hard token cap. Adding new content requires creating a new file (mechanically reviewed) instead of appending to a 5000-token monolith.

---

## Cross-cutting v5 improvements (tracked separately)

| v5 improvement | Why | Phase |
|---|---|---|
| Static prompt ≤ 2500 tokens (was ~5000 in v4) | Halves cognitive load on every turn | Phase 6 |
| Per-turn schema overhead −3000 tokens via `tool_search.py` | Defers low-frequency tool schemas | Phase 7 |
| Diff preview UI in approval prompt | Catches misplaced edits before apply | Phase 4 |
| Per-tool inline guidance (Runnable's `BashTool/prompt.ts:280-291` "use read_file not cat" pattern) | Tool description tells LLM what to substitute | Phase 3, 4, 5 |
| Hermes `_skill_should_show()` filter | Bash-dependent skills hidden when bash exhausted | Phase 10 |
| Cognitive-load aggregate audit (Codex-evaluated) | Catches buried-instruction issues before tagging | Phases 3/6/9/12 |

---

## Verification

This mapping is referenced by:
- `compact_v5/_status/CODEX_REVIEW_TEMPLATE.md` AXIS A's test-coverage check (each phase's tests must include a regression for the mapped PS issue)
- `compact_v5/_status/V5_DESIGN_DECISIONS.md` ADR-003 (created next) — "v5 addresses all 7 PS_actual_use_problems issues, not just round-3 in-place fixes"
- Phase 12 parity tests (must include the mapped issue's failure scenario)

If any v5 phase ships without delivering its mapped acceptance criterion, the aggregate audit FAILS and the next phase is blocked.
